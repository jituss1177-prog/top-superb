import os
import pandas as pd
import streamlit as st
import yfinance as yf


# Custom RSI formula
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# Website ki Setting (Poori tarah se Stealth)
st.set_page_config(page_title="Smart Money", page_icon="🎯", layout="wide")
st.title("🎯 Smart Money")

# 2 Tabs create kiye
tab1, tab2 = st.tabs(["List Scan", "Manual Check"])

# ---------------- TAB 1: AUTO SCANNER (Last 5 Days) ----------------
with tab1:
    if st.button("Run Scan 🚀"):
        file_path = "Trading_Symbols_Chartink.txt"
        stocks = []

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                stocks = [
                    line.strip() + ".NS" for line in f.readlines() if line.strip()
                ]
        else:
            st.error("Trading_Symbols_Chartink.txt file nahi mili.")

        if stocks:
            with st.spinner("Processing list... please wait."):
                results = []
                progress_bar = st.progress(0)

                for i, stock in enumerate(stocks):
                    progress_bar.progress((i + 1) / len(stocks))

                    try:
                        data = yf.download(stock, period="120d", progress=False)
                        if isinstance(data.columns, pd.MultiIndex):
                            data.columns = data.columns.get_level_values(0)

                        if len(data) >= 90:
                            data["RSI"] = compute_rsi(data["Close"], 14)

                            # CHANGE: RSI Crossed Below 35 Logic
                            latest_rsi = float(data["RSI"].iloc[-1])
                            prev_rsi = float(data["RSI"].iloc[-2])

                            # Filter 1: Kal RSI 35 ke upar tha, aur aaj 35 ya usse niche aaya hai (Fresh Cross)
                            if prev_rsi > 35 and latest_rsi <= 35:
                                data["Avg_Vol_20"] = (
                                    data["Volume"].rolling(window=20).mean()
                                )

                                last_5_days = data.tail(5)
                                accumulation_found = False
                                entry_date = ""

                                # Filter 2: Stealth Accumulation (Absorption) in Last 5 Days
                                for date, row in last_5_days.iterrows():
                                    open_p = float(row["Open"])
                                    close_p = float(row["Close"])
                                    high_p = float(row["High"])
                                    low_p = float(row["Low"])

                                    body = abs(open_p - close_p)
                                    lower_wick = min(open_p, close_p) - low_p
                                    total_range = high_p - low_p

                                    # Absorption Logic
                                    if (
                                        total_range > 0
                                        and lower_wick > body
                                        and (lower_wick / total_range) >= 0.4
                                    ):
                                        accumulation_found = True
                                        entry_date = date.strftime("%d %b %Y")
                                        break

                                if accumulation_found:
                                    symbol_clean = stock.replace(".NS", "")
                                    tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol_clean}"
                                    current_close = float(data["Close"].iloc[-1])

                                    results.append(
                                        {
                                            "Stock": symbol_clean,
                                            "Entry Date": entry_date,
                                            "Current Price": round(
                                                current_close, 2
                                            ),
                                            "RSI": round(latest_rsi, 2),
                                            "Open in TradingView": tv_link,
                                        }
                                    )
                    except Exception as e:
                        pass

                progress_bar.empty()

                if len(results) > 0:
                    df = pd.DataFrame(results)
                    st.dataframe(
                        df,
                        column_config={
                            "Open in TradingView": st.column_config.LinkColumn(
                                "Open in TradingView",
                                display_text="View Chart 📈",
                            )
                        },
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "Koi fresh RSI < 35 breakdown aur recent accumulation nahi mili."
                    )

# ---------------- TAB 2: MANUAL CHECK (Last 5 Days) ----------------
with tab2:
    user_input = st.text_input("Stock Name (e.g. INFY, HDFCBANK)", "")

    if st.button("Check Stock 🕵️‍♂️"):
        if user_input.strip() == "":
            st.warning("Pehle kisi stock ka naam likhein.")
        else:
            with st.spinner("Analyzing recent activity..."):
                try:
                    stock_name = user_input.strip().upper()
                    if not stock_name.endswith(".NS"):
                        stock_name += ".NS"

                    data = yf.download(stock_name, period="30d", progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)

                    if len(data) >= 20:
                        data["Avg_Vol_20"] = (
                            data["Volume"].rolling(window=20).mean()
                        )

                        last_5_days = data.tail(5)
                        activity = []

                        for date, row in last_5_days.iterrows():
                            open_p = float(row["Open"])
                            close_p = float(row["Close"])
                            high_p = float(row["High"])
                            low_p = float(row["Low"])
                            vol = float(row["Volume"])
                            avg_vol = float(row["Avg_Vol_20"])

                            body = abs(open_p - close_p)
                            lower_wick = min(open_p, close_p) - low_p
                            total_range = high_p - low_p
                            vol_spike = vol / avg_vol if avg_vol > 0 else 0
                            is_green = close_p > open_p

                            setup = ""

                            if (
                                total_range > 0
                                and lower_wick > body
                                and (lower_wick / total_range) >= 0.4
                            ):
                                setup = "Absorption (Stealth) 🟢"
                            elif is_green and vol_spike >= 1.5:
                                setup = "Aggressive Buy 🚀"

                            if setup != "":
                                activity.append(
                                    {
                                        "Date": date.strftime("%d %b %Y"),
                                        "Setup Type": setup,
                                        "Closing Price": round(close_p, 2),
                                        "Volume Spike": f"{round(vol_spike, 1)}x",
                                    }
                                )

                        if len(activity) > 0:
                            st.success(
                                f"Activity Found for {stock_name.replace('.NS', '')}"
                            )
                            st.dataframe(
                                pd.DataFrame(activity),
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.info(
                                f"Pichle 5 dino mein koi special activity nahi mili."
                            )
                    else:
                        st.error("Data nahi mila. Sahi naam type karein.")
                except Exception as e:
                    st.error("Kuch technical error aaya. Sahi naam check karein.")
