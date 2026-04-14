import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz  
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(page_title="Eagle Eye Terminal", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=5000, key="live_update")

# --- TIMEZONE SETUP ---
IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background: #050505; color: #ffffff; }
    .header-container { background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
    .trade-card { padding: 35px; border-radius: 25px; text-align: center; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px); margin-bottom: 20px; }
    .call-card { background: linear-gradient(145deg, rgba(0,200,83,0.2), rgba(0,100,0,0.4)); border: 1px solid #00c853; }
    .put-card { background: linear-gradient(145deg, rgba(255,75,75,0.2), rgba(139,0,0,0.4)); border: 1px solid #ff4b4b; }
    .wait-card { background: rgba(40, 44, 52, 0.5); border: 1px solid #555; }
    .price-val { font-size: 50px !important; font-weight: 800; margin: 10px 0; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f'<div class="header-container"><div>🦅 EAGLE EYE TERMINAL</div><div>IST: {live_time}</div></div>', unsafe_allow_html=True)

# --- DATA FETCHING WITH SAFETY ---
def get_market_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False)
        if df is None or len(df) < 2: return None
        
        # Latest data points
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    except:
        return None

# --- UI ---
col1, col2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [col1, col2][i]:
        df = get_market_data(sym)
        
        # Yahan Error Check hai
        if df is not None and not df.empty and not pd.isna(df['Close'].iloc[-1]):
            price = float(df['Close'].iloc[-1])
            vwap = float(df['VWAP'].iloc[-1])
            rsi = float(df['RSI'].fillna(50).iloc[-1])
            
            if price > vwap and rsi > 52:
                card_class, action = "call-card", "🚀 BUY CALL (CE)"
            elif price < vwap and rsi < 48:
                card_class, action = "put-card", "📉 BUY PUT (PE)"
            else:
                card_class, action = "wait-card", "⏳ NEUTRAL / WAIT"

            st.markdown(f"""
                <div class="trade-card {card_class}">
                    <div style="opacity: 0.7;">{name}</div>
                    <div class="price-val">₹{price:,.2f}</div>
                    <div style="font-weight:bold;">{action}</div>
                    <div style="font-size:12px; margin-top:10px; color:#aaa;">VWAP: {vwap:,.1f} | RSI: {rsi:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Waiting for {name} data... (Market is Closed)")

# --- RULES ---
st.markdown("### 🛡️ OPERATIONAL DISCIPLINE")
st.info("1. Enter only when NIFTY & BANK NIFTY match. | 2. Target hit? Close terminal. | 3. Always use Stop Loss.")
