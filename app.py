import streamlit as st
import yfinance as yf
import pandas as pd
import os

# Website ka title aur layout
st.set_page_config(page_title="Live RSI Scanner", layout="wide")
st.title("Live 30-Min RSI Scanner (RSI 22 Crossed Below 35)")

# Aapki text file ka exact naam
file_path = "Trading_Symbols_Chartink.txt"

def get_symbols():
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            # File se list nikalna
            symbols = [line.strip() for line in f.readlines() if line.strip()]
        return symbols
    else:
        st.error(f"Error: '{file_path}' file nahi mili. Kripya dhyan dein ki file ka naam ekdum sahi ho.")
        return []

# Scan button
if st.button("Start Live Scan", type="primary"):
    symbols = get_symbols()
    
    if symbols:
        st.write(f"Total {len(symbols)} stocks scan ho rahe hain. Kripya thoda wait karein...")
        progress_bar = st.progress(0)
        matched_stocks = []
        
        for i, symbol in enumerate(symbols):
            try:
                # Indian stocks ke liye .NS lagana zaroori hai
                yf_symbol = symbol + ".NS"
                
                # 30 minute ka pichle 7 din ka data
                df = yf.download(yf_symbol, interval='30m', period='7d', progress=False)
                
                # RSI 22 calculate karne ke liye kam se kam 23 candle chahiye
                if len(df) > 22:
                    df.ta.rsi(length=22, append=True)
                    df = df.dropna()
                    
                    if len(df) >= 2:
                        curr_rsi = df["RSI_22"].iloc[-1]  # Sabse latest candle
                        prev_rsi = df["RSI_22"].iloc[-2]  # Usse pichli candle
                        
                        # Strategy: Crossed Below 35
                        if prev_rsi >= 35 and curr_rsi < 35:
                            tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                            matched_stocks.append({
                                "Stock Symbol": symbol,
                                "Current RSI (22)": round(curr_rsi, 2),
                                "TradingView Chart": tv_url
                            })
            except Exception:
                # Agar kisi stock ka data na mile toh agle stock par chale jao
                pass 
            
            # Progress bar ko update karna
            progress_bar.progress((i + 1) / len(symbols))
        
        # Scan complete hone par result dikhana
        if matched_stocks:
            st.success("Scan Complete! Niche diye gaye stocks aapke setup me aa gaye hain:")
            result_df = pd.DataFrame(matched_stocks)
            
            # TradingView ka clickable link banana
            st.data_editor(
                result_df,
                column_config={
                    "TradingView Chart": st.column_config.LinkColumn("Open in TradingView")
                },
                hide_index=True
            )
        else:
            st.info("Abhi kisi bhi stock me RSI 35 ke niche cross nahi hua hai. Thodi der baad dubara try karein.")
