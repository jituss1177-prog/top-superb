import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="VCP Intraday Scanner", layout="wide")

st.title("🚀 VCP Intraday Strategy Scanner")
st.markdown("Filtering stocks based on momentum, 3-minute VCP setups, and strict price rules (>= ₹200).")

# Sample function or placeholder for fetching stock data
@st.cache_data
def get_market_data():
    # Yahan aap apni list ya API data load karte hain
    # Example placeholder structure:
    data = {
        'Symbol': ['RELAXO', 'ROSSARI', 'CAPILLARY', 'WELSPUNLIV', 'SBI CARD', 'TTKPRESTIG', 'SSWL', 'GANDHAR'],
        'Close': [291.60, 427.80, 558.30, 210.74, 555.65, 511.00, 458.75, 294.10],
        'Change_Pct': [1.8, 3.2, 0.5, 1.5, 2.1, 0.8, -1.2, -0.3]
    }
    return pd.DataFrame(data)

if st.button("Start 5-Min Scan (9:25 AM)"):
    df = get_market_data()
    
    # 1. CRITICAL FILTER: Remove stocks below ₹200
    df = df[df['Close'] >= 200]
    
    # 2. Categorization Columns
    top_bullish = df[df['Change_Pct'] > 2.5]
    sweet_spot = df[(df['Change_Pct'] >= 1.0) & (df['Change_Pct'] <= 2.5)]
    top_bearish = df[df['Change_Pct'] < -1.0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔥 Top Bullish (> 2.5%)")
        st.dataframe(top_bullish[['Symbol', 'Close', 'Change_Pct']])
        
    with col2:
        st.subheader("🎯 Sweet Spot (1% - 2.5%)")
        st.dataframe(sweet_spot[['Symbol', 'Close', 'Change_Pct']])
        
    with col3:
        st.subheader("📉 Top Bearish")
        st.dataframe(top_bearish[['Symbol', 'Close', 'Change_Pct']])

st.markdown("---")
st.markdown("**Rules Reminder:** Max 4 Trades | 50 Quantity | 3-4 Points SL | 10 Points Target | Cover Order")
