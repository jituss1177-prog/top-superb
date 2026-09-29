import streamlit as st
import yfinance as yf
import pandas as pd
import os

st.set_page_config(page_title="Accurate RSI Scanner", layout="wide")
st.title("🎯 Accurate 30-Min RSI Scanner")

file_path = "Trading_Symbols_Chartink.txt"

# RSI Exact Formula
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

if st.button("Start Accurate Scan 🚀", type="primary"):
    symbols = get_symbols()
    
    if symbols:
        # User ko message dikhana
        st.write(f"Total {len(symbols)} stocks ka 1 mahine ka data fetch ho raha hai (Taaki accuracy Chartink jaisi aaye). Kripya wait karein...")
        
        # Yahoo Finance ke liye ".NS" lagana
        yf_symbols = [sym + ".NS" for sym in symbols]
        
        # BULK DOWNLOAD: Ek hi baar me saara data lana (Bina block hue)
        try:
            data = yf.download(yf_symbols, interval='30m', period='1mo', progress=False)
            matched_stocks = []
            
            if not data.empty and 'Close' in data:
                closes = data['Close']
                
                for symbol in symbols:
                    yf_sym = symbol + ".NS"
                    
                    try:
                        # Har stock ka close price nikalna
                        if isinstance(closes, pd.Series):
                            stock_close = closes.dropna()
                        else:
                            if yf_sym in closes.columns:
                                stock_close = closes[yf_sym].dropna()
                            else:
                                continue
                                
                        if len(stock_close) > 22:
                            rsi_series = calculate_rsi(stock_close, window=22).dropna()
                            
                            if len(rsi_series) >= 2:
                                curr_rsi = rsi_series.iloc[-1]
                                prev_rsi = rsi_series.iloc[-2]
                                
                                # Setup: RSI 22 Crossed Below 35
                                if prev_rsi >= 35 and curr_rsi < 35:
                                    matched_stocks.append({
                                        "Stock Symbol": symbol,
                                        "Current RSI": round(curr_rsi, 2),
                                        "TradingView Chart": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                    })
                    except Exception:
                        pass # Agar kisi 1 stock me dikkat aaye toh skip kardo
                        
            # Result dikhana
            if matched_stocks:
                st.success(f"✅ Scan Complete! {len(matched_stocks)} stocks aapke setup me aaye hain:")
                st.data_editor(
                    pd.DataFrame(matched_stocks),
                    column_config={"TradingView Chart": st.column_config.LinkColumn("Open in TradingView")},
                    hide_index=True
                )
            else:
                st.info("Abhi kisi bhi stock me RSI 35 ke niche cross nahi hua hai.")
                
        except Exception as e:
            st.error("Data laane me error aayi. Thodi der baad try karein.")
