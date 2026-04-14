import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz  
from streamlit_autorefresh import st_autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="Eagle Eye Terminal", layout="wide", initial_sidebar_state="collapsed")

# REFRESH RATE SET TO 3 SECONDS (3000ms)
st_autorefresh(interval=3000, key="live_update")

# --- IST TIME ---
IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

# --- CSS (Premium Dark Mode) ---
st.markdown("""
    <style>
    .stApp { background: #050505; color: #ffffff; }
    .header-container { background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
    .trade-card { padding: 30px; border-radius: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    .call-card { background: linear-gradient(145deg, rgba(0, 200, 83, 0.2), rgba(0, 50, 0, 0.5)); border: 1.5px solid #00c853; box-shadow: 0 0 15px rgba(0,200,83,0.2); }
    .put-card { background: linear-gradient(145deg, rgba(255, 75, 75, 0.2), rgba(80, 0, 0, 0.5)); border: 1.5px solid #ff4b4b; box-shadow: 0 0 15px rgba(255,75,75,0.2); }
    .wait-card { background: rgba(255, 255, 255, 0.05); border: 1.5px solid #555; }
    .price-val { font-size: 45px !important; font-weight: 800; margin: 5px 0; font-family: 'Courier New', monospace; }
    .live-dot { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; margin-right: 5px; animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f'<div class="header-container"><div><span class="live-dot"></span> 🦅 EAGLE EYE LIVE</div><div>IST: {live_time}</div></div>', unsafe_allow_html=True)

# --- SAFE DATA FETCHING ---
def get_data(symbol):
    try:
        # 2-day period to ensure data availability during off-market hours
        df = yf.download(symbol, period="2d", interval="1m", progress=False)
        if df is None or df.empty or len(df) < 5:
            return None
        
        # VWAP Calculation
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        
        # RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        return df
    except:
        return None

# --- UI LAYOUT ---
col1, col2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [col1, col2][i]:
        df = get_data(sym)
        
        if df is not None:
            try:
                price = float(df['Close'].iloc[-1])
                vwap = float(df['VWAP'].iloc[-1])
                rsi = float(df['RSI'].fillna(50).iloc[-1])
                
                # Logic for Signals
                if price > vwap and rsi > 52:
                    cls, action = "call-card", "🚀 BUY CALL"
                elif price < vwap and rsi < 48:
                    cls, action = "put-card", "📉 BUY PUT"
                else:
                    cls, action = "wait-card", "⏳ NEUTRAL"

                st.markdown(f"""
                    <div class="trade-card {cls}">
                        <div style="opacity:0.7; letter-spacing: 2px;">{name}</div>
                        <div class="price-val">₹{price:,.2f}</div>
                        <div style="font-weight:bold; font-size:20px;">{action}</div>
                        <div style="font-size:12px; margin-top:10px; color:#aaa;">VWAP: {vwap:,.1f} | RSI: {rsi:.1f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            except:
                st.warning(f"{name}: Updating...")
        else:
            st.error(f"{name}: Connection Slow")

st.divider()
st.caption("Auto-refreshing every 3 seconds. Scalping rules apply.")
