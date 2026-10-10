import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Brahmaastra Terminal", layout="wide")

file_path = "Trading_Symbols_Chartink.txt"

# Engine (Hidden Logic for Support Scanner)
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

# --- TABS CREATION ---
tab1, tab2, tab3 = st.tabs(["📊 5-Min VCP Scanner", "🏹 90D Support Scanner", "💰 Dividend Tracker"])

# ==========================================
# TAB 1: 5-MIN VCP INTRADAY SCANNER
# ==========================================
with tab1:
    st.title("📊 5-Min Volume Contraction")
    st.caption("Best trading time: 9:30 AM to 11:00 AM IST. Din me sirf ek trade valid hoga.")
    
    col_bull, col_bear = st.columns(2)
    with col_bull:
        st.subheader("🟢 Top Bullish Setups")
    with col_bear:
        st.subheader("🔴 Top Bearish Setups")
        
    if st.button("Start 5-Min Scan 🚀"):
        symbols = get_symbols()
        if symbols:
            status = st.empty()
            status.info("Scanning 5-Min Data... (Isme thoda time lag sakta hai)")
            prog_bar_vcp = st.progress(0)
            
            bullish_list = []
            bearish_list = []
            
            chunk_size = 40
            for i in range(0, len(symbols), chunk_size):
                chunk_syms = symbols[i:i+chunk_size]
                yf_symbols = [sym + ".NS" for sym in chunk_syms]
                
                try:
                    data_5m = yf.download(yf_symbols, interval='5m', period='1d', progress=False, threads=False)
                    
                    if not data_5m.empty:
                        closes = data_5m['Close']
                        opens = data_5m['Open']
                        volumes = data_5m['Volume']
                        highs = data_5m['High']
                        lows = data_5m['Low']
                        
                        for symbol in chunk_syms:
                            yf_sym = symbol + ".NS"
                            try:
                                if isinstance(closes, pd.Series):
                                    stk_c, stk_o, stk_v = closes.dropna(), opens.dropna(), volumes.dropna()
                                    stk_h, stk_l = highs.dropna(), lows.dropna()
                                else:
                                    if yf_sym in closes.columns:
                                        stk_c = closes[yf_sym].dropna()
                                        stk_o = opens[yf_sym].dropna()
                                        stk_v = volumes[yf_sym].dropna()
                                        stk_h = highs[yf_sym].dropna()
                                        stk_l = lows[yf_sym].dropna()
                                    else:
                                        continue
                                        
                                if len(stk_c) >= 3:
                                    day_open = stk_o.iloc[0] 
                                    c1, o1, v1 = stk_c.iloc[-1], stk_o.iloc[-1], stk_v.iloc[-1]
                                    c2, o2, v2 = stk_c.iloc[-2], stk_o.iloc[-2], stk_v.iloc[-2]
                                    h1, l1 = stk_h.iloc[-1], stk_l.iloc[-1]
                                    
                                    # Bullish Setup
                                    if c1 > day_open:
                                        if (c2 < o2) and (c1 < o1) and (v1 < v2):
                                            bullish_list.append({
                                                "Stock": symbol,
                                                "Buy >": round(h1, 2),
                                                "Link": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                            })
                                            
                                    # Bearish Setup
                                    if c1 < day_open:
                                        if (c2 > o2) and (c1 > o1) and (v1 < v2):
                                            bearish_list.append({
                                                "Stock": symbol,
                                                "Sell <": round(l1, 2),
                                                "Link": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                            })
                            except Exception:
                                pass
                except Exception:
                    pass
                    
                prog_bar_vcp.progress(min((i + chunk_size) / len(symbols), 1.0))
            
            status.empty()
            prog_bar_vcp.empty()
            
            with col_bull:
                if bullish_list:
                    st.dataframe(pd.DataFrame(bullish_list).head(5), column_config={"Link": st.column_config.LinkColumn("View")}, hide_index=True)
                else:
                    st.write("No Bullish setups.")
                    
            with col_bear:
                if bearish_list:
                    st.dataframe(pd.DataFrame(bearish_list).head(5), column_config={"Link": st.column_config.LinkColumn("View")}, hide_index=True)
                else:
                    st.write("No Bearish setups.")

# ==========================================
# TAB 2: MAIN SECRET SCANNER (90D Support)
# ==========================================
with tab2:
    st.title("🏹 90D Support Scanner")
    col1, col2 = st.columns([1, 2])
    with col1:
        auto_run = st.toggle("Auto-Scan", disabled=not is_market_live)
    with col2:
        manual_run = st.button("Scan Now 🎯")

    if auto_run or manual_run:
        symbols = get_symbols()
        
        if symbols:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            matched_stocks = []
            chunk_size = 50
            
            for i in range(0, len(symbols), chunk_size):
                chunk_syms = symbols[i:i+chunk_size]
                yf_symbols = [sym + ".NS" for sym in chunk_syms]
                
                status_text.markdown("Loading...")
                
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
                                        
                                        if curr_rsi < 35 and (0 <= dist_pct <= 3.5):
                                            matched_stocks.append({
                                                "Stock": symbol,
                                                "Current Price": round(curr_close, 2),
                                                "TradingView": f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
                                            })
                            except Exception:
                                pass
                except Exception as e:
                    pass
                
                current_progress = min((i + chunk_size) / len(symbols), 1.0)
                progress_bar.progress(current_progress)
            
            status_text.empty()
            progress_bar.empty()
            
            if matched_stocks:
                st.data_editor(
                    pd.DataFrame(matched_stocks),
                    column_config={"TradingView": st.column_config.LinkColumn("Open in TradingView")},
                    hide_index=True
                )
            else:
                st.write("No results.")
                
            if auto_run and is_market_live:
                time.sleep(900) 
                st.rerun()

# ==========================================
# TAB 3: SEPARATE DIVIDEND SCANNER
# ==========================================
with tab3:
    st.title("💰 Dividend Tracker")
    
    if st.button("Check Dividends"):
        symbols = get_symbols()
        if symbols:
            status_text_div = st.empty()
            status_text_div.markdown("Processing...")
            prog_bar_div = st.progress(0)
            
            div_matched = []
            today_date = now.date()
            
            for i, symbol in enumerate(symbols):
                try:
                    yf_sym = symbol + ".NS"
                    ticker = yf.Ticker(yf_sym)
                    ex_div_unix = ticker.info.get('exDividendDate')
                    
                    if ex_div_unix:
                        ex_date = datetime.fromtimestamp(ex_div_unix).date()
                        
                        if today_date <= ex_date <= (today_date + timedelta(days=30)):
                            days_left = (ex_date - today_date).days
                            div_matched.append({
                                "Stock": symbol,
                                "Dividend Date": ex_date.strftime("%d %b %Y"),
                                "Timeline": f"{days_left} Days Left"
                            })
                except:
                    pass
                
                prog_bar_div.progress((i + 1) / len(symbols))
                
            prog_bar_div.empty()
            status_text_div.empty()
            
            if div_matched:
                st.dataframe(pd.DataFrame(div_matched), hide_index=True)
            else:
                st.write("No upcoming dividends found.")
