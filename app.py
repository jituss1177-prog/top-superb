import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Live RSI Scanner", layout="wide")
st.title("⚡ Turant Live RSI Scanner (30-Min)")
st.write("Condition: RSI(22) Crossed Below 35 in Current Candle")

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

col1, col2 = st.columns([1, 2])
with col1:
    auto_run = st.toggle("🟢 Auto-Scan ON (Har 1 Min)")
with col2:
    manual_run = st.button("Turant Manual Scan 🚀")

if auto_run or manual_run:
    symbols = get_symbols()
    
    if symbols:
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        st.write(f"⏳ Live checking {len(symbols)} stocks... Last Checked: **{now.strftime('%I:%M:%S %p')}**")
        
        try:
            yf_symbols = [sym + ".NS" for sym in symbols]
            # Live latest candle data lane ke liye
            data = yf.download(yf_symbols, interval='30m', period='1mo', progress=False)
            matched_stocks = []
            
            if not data.empty and 'Close' in data:
                closes = data['Close']
                for symbol in symbols:
                    yf_sym = symbol + ".NS"
                    try:
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
                                # curr_rsi = Abhi jo candle chal rahi hai (Live)
                                # prev_rsi = Pichli candle jo close ho chuki hai
                                curr_rsi = rsi_series.iloc[-1]
                                prev_rsi = rsi_series.iloc[-2]
                                
                                # Setup: Exact Cross Below 35 in Current Live Candle
                                if prev_rsi >= 35 and curr_rsi < 35:
                                    matched_stocks.append({
                                        "Stock Symbol": symbol,
                                        "Live RSI (22)": round(curr_rsi, 2),
                                        "TradingView Chart": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                    })
                    except Exception:
                        pass
                        
            if matched_stocks:
                st.success(f"🚨 ALERT: In {len(matched_stocks)} stocks ne turant RSI 35 cross kiya hai!")
                st.data_editor(
                    pd.DataFrame(matched_stocks),
                    column_config={"TradingView Chart": st.column_config.LinkColumn("Open in TradingView")},
                    hide_index=True
                )
            else:
                st.info("Abhi current candle me kisi stock ne RSI 35 ko niche cross nahi kiya hai.")
                
        except Exception as e:
            st.error("Data fetch error. Retrying in next cycle...")

        # AUTO-REFRESH LOGIC (Har 1 Minute)
        if auto_run:
            is_weekday = now.weekday() < 5
            market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            if is_weekday and market_open <= now <= market_close:
                st.write("🔄 *Tracking Live Data... Next check 60 seconds me.*")
                time.sleep(60) # Har 1 minute me refresh hoga
                st.rerun()
            else:
                st.warning("⏸️ Market band hai. Auto-scan ruke ga taaki data block na ho.")
