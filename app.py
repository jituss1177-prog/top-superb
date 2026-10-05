import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Brahmaastra Scanner", layout="wide")

# UI text ko generic kar diya gaya hai
st.title("🏹 Brahmaastra Scanner")
st.write("**System Status:** Active & Scanning Premium Setups...")

file_path = "Trading_Symbols_Chartink.txt"

def calculate_rsi(series, window=22):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_symbols():
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

ist = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(ist)
is_weekday = now.weekday() < 5
market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
is_market_live = is_weekday and market_open <= now <= market_close

if is_market_live:
    st.success("🟢 **Market Live:** System Running.")
else:
    st.error("🔴 **Market Band:** Showing last closing data.")

col1, col2 = st.columns([1, 2])
with col1:
    auto_run = st.toggle("🤖 Auto-Scan ON (Har 15 Min)", disabled=not is_market_live)
with col2:
    manual_run = st.button("Scan Now 🚀")

if auto_run or manual_run:
    symbols = get_symbols()
    
    if symbols:
        st.write(f"⏳ Processing {len(symbols)} items... Last Checked: **{now.strftime('%I:%M:%S %p')}**")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        matched_stocks = []
        chunk_size = 50
        total_chunks = (len(symbols) // chunk_size) + (1 if len(symbols) % chunk_size != 0 else 0)
        
        for i in range(0, len(symbols), chunk_size):
            chunk_syms = symbols[i:i+chunk_size]
            yf_symbols = [sym + ".NS" for sym in chunk_syms]
            current_chunk = (i // chunk_size) + 1
            
            status_text.markdown(f"**Fetching Data: Batch {current_chunk} out of {total_chunks}...**")
            
            try:
                data_30m = yf.download(yf_symbols, interval='30m', period='1mo', progress=False, threads=False)
                data_daily = yf.download(yf_symbols, interval='1d', period='3mo', progress=False, threads=False)
                
                if not data_30m.empty and not data_daily.empty:
                    closes_30m = data_30m['Close']
                    lows_daily = data_daily['Low']
                    
                    for symbol in chunk_syms:
                        yf_sym = symbol + ".NS"
                        try:
                            if isinstance(closes_30m, pd.Series):
                                stock_close = closes_30m.dropna()
                            else:
                                stock_close = closes_30m[yf_sym].dropna() if yf_sym in closes_30m.columns else None
                                
                            if isinstance(lows_daily, pd.Series):
                                stock_low = lows_daily.dropna()
                            else:
                                stock_low = lows_daily[yf_sym].dropna() if yf_sym in lows_daily.columns else None
                                    
                            if stock_close is not None and stock_low is not None and len(stock_close) > 22 and len(stock_low) > 10:
                                
                                support_90d = stock_low[:-1].min()
                                rsi_series = calculate_rsi(stock_close, window=22).dropna()
                                
                                if len(rsi_series) >= 2 and support_90d > 0:
                                    curr_rsi = rsi_series.iloc[-1]
                                    curr_close = stock_close.iloc[-1]
                                    
                                    dist_pct = ((curr_close - support_90d) / support_90d) * 100
                                    
                                    # Setup logic secret hai, kisi ko show nahi hoga
                                    if curr_rsi < 35 and (0 <= dist_pct <= 3.5):
                                        matched_stocks.append({
                                            "Stock": symbol,
                                            "Metric A": round(curr_rsi, 2),        # RSI ka naam chupa diya
                                            "Current Price": round(curr_close, 2),
                                            "Key Level": round(support_90d, 2),    # Support ka naam chupa diya
                                            "Zone %": f"{round(dist_pct, 2)}%",    # Distance ka naam chupa diya
                                            "TradingView": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                        })
                        except Exception:
                            pass
            except Exception as e:
                pass
            
            current_progress = min((i + chunk_size) / len(symbols), 1.0)
            progress_bar.progress(current_progress)
        
        status_text.markdown("**✅ Scan Complete!**")
        
        if matched_stocks:
            # Success message bhi secret kar diya gaya hai
            st.success(f"🔥 ALERT: {len(matched_stocks)} stocks me aapka setup active hai!")
            st.data_editor(
                pd.DataFrame(matched_stocks),
                column_config={"TradingView": st.column_config.LinkColumn("Open in TradingView")},
                hide_index=True
            )
        else:
            # Info message generic banaya
            st.info("Abhi koi bhi stock aapke criteria se match nahi kar raha hai.")
            
        if auto_run and is_market_live:
            st.write("🔄 *Next scan 15 minute me hoga...*")
            time.sleep(900) 
            st.rerun()
