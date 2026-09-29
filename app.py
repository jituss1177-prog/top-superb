import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Smart RSI Scanner", layout="wide")
st.title("🎯 Smart 30-Min RSI Scanner (Live + Post-Market)")
st.write("**Condition:** 30-Min RSI(22) Crossed Below 35")

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

# Market Status Check (Live ya Band)
ist = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(ist)
is_weekday = now.weekday() < 5
market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
is_market_live = is_weekday and market_open <= now <= market_close

if is_market_live:
    st.success("🟢 **Market Live Hai.** App current forming candle ko track kar rahi hai.")
else:
    st.error(f"🔴 **Market Band Hai.** App aakhri closing time (3:30 PM) ka final data dikha rahi hai.")

col1, col2 = st.columns([1, 2])
with col1:
    auto_run = st.toggle("🤖 Auto-Scan ON (Har 1 Min)", disabled=not is_market_live, help="Market band hone par Auto-Scan kaam nahi karega.")
with col2:
    manual_run = st.button("Scan Now 🚀")

if auto_run or manual_run:
    symbols = get_symbols()
    
    if symbols:
        st.write(f"⏳ Fetching data for {len(symbols)} stocks... Last Checked: **{now.strftime('%I:%M:%S %p')}**")
        
        try:
            yf_symbols = [sym + ".NS" for sym in symbols]
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
                                # curr_rsi aakhri candle hai (Live me latest, Market band me 3:30 PM wali)
                                curr_rsi = rsi_series.iloc[-1]
                                prev_rsi = rsi_series.iloc[-2]
                                
                                # Setup: Exact Cross Below 35
                                if prev_rsi >= 35 and curr_rsi < 35:
                                    matched_stocks.append({
                                        "Stock Symbol": symbol,
                                        "RSI (22)": round(curr_rsi, 2),
                                        "TradingView Chart": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                    })
                    except Exception:
                        pass
                        
            if matched_stocks:
                st.success(f"✅ ALERT: {len(matched_stocks)} stocks me aapka setup ban chuka hai!")
                st.data_editor(
                    pd.DataFrame(matched_stocks),
                    column_config={"TradingView Chart": st.column_config.LinkColumn("Open in TradingView")},
                    hide_index=True
                )
            else:
                st.info("Abhi kisi stock me RSI 35 ko niche cross nahi kiya hai.")
                
        except Exception as e:
            st.error("Data fetch error. Kripya thodi der baad try karein.")

        # AUTO-REFRESH LOGIC (Sirf Live Market me chalega)
        if auto_run and is_market_live:
            st.write("🔄 *Tracking Live Data... Next check 60 seconds me.*")
            time.sleep(60) 
            st.rerun()
