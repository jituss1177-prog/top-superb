import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Brahmaastra Scanner", layout="wide")
st.title("🏹 Brahmaastra: RSI 35 + 90D Support Bounce")
st.write("**Strategy:** 30-Min RSI < 35 **AUR** Price 90-Day Base Support ke paas (0-3% range me) ho.")

file_path = "Trading_Symbols_Chartink.txt"

# Exact RSI Formula
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

# Market Status Check
ist = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(ist)
is_weekday = now.weekday() < 5
market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
is_market_live = is_weekday and market_open <= now <= market_close

if is_market_live:
    st.success("🟢 **Market Live:** Current forming candle par entry setup dhoondh raha hai.")
else:
    st.error("🔴 **Market Band:** Aakhri closing (3:30 PM) ka setup dikha raha hai.")

col1, col2 = st.columns([1, 2])
with col1:
    auto_run = st.toggle("🤖 Auto-Scan ON (Har 1 Min)", disabled=not is_market_live)
with col2:
    manual_run = st.button("Scan Now 🚀")

if auto_run or manual_run:
    symbols = get_symbols()
    
    if symbols:
        st.write(f"⏳ Double-Filtering {len(symbols)} stocks (Support + RSI)... Last Checked: **{now.strftime('%I:%M:%S %p')}**")
        
        try:
            yf_symbols = [sym + ".NS" for sym in symbols]
            
            # 1. RSI ke liye 30-min data (1 Mahina)
            data_30m = yf.download(yf_symbols, interval='30m', period='1mo', progress=False)
            # 2. Base Support ke liye Daily data (Pichle 3 Mahine / 90 Days)
            data_daily = yf.download(yf_symbols, interval='1d', period='3mo', progress=False)
            
            matched_stocks = []
            
            if not data_30m.empty and not data_daily.empty:
                closes_30m = data_30m['Close']
                lows_daily = data_daily['Low']
                
                for symbol in symbols:
                    yf_sym = symbol + ".NS"
                    try:
                        # 30-min Close price fetch karna
                        if isinstance(closes_30m, pd.Series):
                            stock_close = closes_30m.dropna()
                        else:
                            stock_close = closes_30m[yf_sym].dropna() if yf_sym in closes_30m.columns else None
                            
                        # Daily Low price fetch karna
                        if isinstance(lows_daily, pd.Series):
                            stock_low = lows_daily.dropna()
                        else:
                            stock_low = lows_daily[yf_sym].dropna() if yf_sym in lows_daily.columns else None
                                
                        if stock_close is not None and stock_low is not None and len(stock_close) > 22 and len(stock_low) > 10:
                            
                            # Hanuman 90D Support (Aakhri din ki incomplete candle chhod kar pichle 90 din ka lowest low)
                            support_90d = stock_low[:-1].min()
                            
                            rsi_series = calculate_rsi(stock_close, window=22).dropna()
                            
                            if len(rsi_series) >= 2 and support_90d > 0:
                                curr_rsi = rsi_series.iloc[-1]
                                curr_close = stock_close.iloc[-1]
                                
                                # Distance calculation: Support se kitna upar khada hai price?
                                dist_pct = ((curr_close - support_90d) / support_90d) * 100
                                
                                # 🎯 THE BRAHMAASTRA SETUP: RSI < 35 AUR Price Support ke 0% se 3.5% ki range me ho
                                if curr_rsi < 35 and (0 <= dist_pct <= 3.5):
                                    matched_stocks.append({
                                        "Stock": symbol,
                                        "RSI (22)": round(curr_rsi, 2),
                                        "Current Price": round(curr_close, 2),
                                        "90D Support": round(support_90d, 2),
                                        "Support Distance": f"{round(dist_pct, 2)}% uper",
                                        "TradingView": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                    })
                    except Exception:
                        pass
                        
            if matched_stocks:
                st.success(f"🔥 LIMIT ORDER READY: {len(matched_stocks)} stocks bilkul aapke Support zone par aa chuke hain!")
                st.data_editor(
                    pd.DataFrame(matched_stocks),
                    column_config={"TradingView": st.column_config.LinkColumn("Open in TradingView")},
                    hide_index=True
                )
            else:
                st.info("Abhi koi bhi stock RSI 35 + Support Bounce wale perfect setup me nahi hai.")
                
        except Exception as e:
            st.error("Data processing me error aayi. Kripya thodi der baad try karein.")

        # AUTO-REFRESH (Har 1 Minute)
        if auto_run and is_market_live:
            st.write("🔄 *Next scan 60 seconds me hoga...*")
            time.sleep(60) 
            st.rerun()
