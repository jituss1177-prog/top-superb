import streamlit as st
import yfinance as yf
import pandas as pd
import os
import concurrent.futures

# Page Setup
st.set_page_config(page_title="Fast RSI Scanner", layout="wide")
st.title("⚡ Superfast 30-Min RSI Scanner")

file_path = "Trading_Symbols_Chartink.txt"

# RSI Formula
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

# Har stock ko check karne ka logic
def check_stock(symbol):
    try:
        yf_symbol = symbol + ".NS"
        df = yf.download(yf_symbol, interval='30m', period='7d', progress=False)
        
        if len(df) > 22:
            rsi_series = calculate_rsi(df['Close'], window=22).dropna()
            
            if len(rsi_series) >= 2:
                curr_rsi = rsi_series.iloc[-1]
                prev_rsi = rsi_series.iloc[-2]
                
                # Setup: RSI 22 Crossed Below 35
                if prev_rsi >= 35 and curr_rsi < 35:
                    return {
                        "Stock Symbol": symbol,
                        "Current RSI": round(curr_rsi, 2),
                        "TradingView Chart": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                    }
    except:
        pass
    return None

# Scan Button
if st.button("Start Fast Scan 🚀", type="primary"):
    symbols = get_symbols()
    
    if symbols:
        st.write(f"Scanning {len(symbols)} stocks at rocket speed... Kripya wait karein.")
        progress_bar = st.progress(0)
        
        matched_stocks = []
        completed = 0
        
        # Superfast Multi-threading (Ek sath 20 stocks check honge)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(check_stock, sym): sym for sym in symbols}
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    matched_stocks.append(result)
                
                completed += 1
                progress_bar.progress(completed / len(symbols))
        
        # Result Dikhana
        if matched_stocks:
            st.success("✅ Scan Complete! Ye rahe aapke setup wale stocks:")
            st.data_editor(
                pd.DataFrame(matched_stocks),
                column_config={"TradingView Chart": st.column_config.LinkColumn("Open in TradingView")},
                hide_index=True
            )
        else:
            st.info("Abhi kisi bhi stock me RSI 35 ke niche cross nahi hua hai.")
