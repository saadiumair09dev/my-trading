import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz  
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG ---
st.set_page_config(page_title="Eagle Eye Terminal", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, key="live_update")

# --- TIMEZONE SETUP ---
IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

# --- ADVANCED PREMIUM UI (CSS) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background: #050505; color: #ffffff; }
    
    /* Header Style */
    .header-container { background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
    .live-dot { height: 10px; width: 10px; background-color: #00ff00; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 10px #00ff00; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }

    /* Glass Cards */
    .trade-card { padding: 35px; border-radius: 25px; text-align: center; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px); margin-bottom: 20px; transition: transform 0.3s; }
    .trade-card:hover { transform: translateY(-5px); }
    
    /* Dynamic Colors */
    .call-card { background: linear-gradient(145deg, rgba(0,200,83,0.2), rgba(0,100,0,0.4)); border: 1px solid #00c853; }
    .put-card { background: linear-gradient(145deg, rgba(255,75,75,0.2), rgba(139,0,0,0.4)); border: 1px solid #ff4b4b; }
    .wait-card { background: rgba(40, 44, 52, 0.5); border: 1px solid #555; }
    
    /* Text Styles */
    .price-val { font-size: 55px !important; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin: 10px 0; color: #ffffff; }
    .signal-badge { font-size: 20px; font-weight: bold; padding: 8px 20px; border-radius: 50px; background: rgba(0,0,0,0.3); letter-spacing: 1px; }
    .metrics { font-size: 14px; color: #aaa; margin-top: 15px; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown(f"""
    <div class="header-container">
        <div style="font-family: sans-serif; font-weight: bold; font-size: 18px;">🦅 EAGLE EYE TERMINAL</div>
        <div style="font-family: monospace; font-size: 16px;"><span class="live-dot"></span>IST: {live_time}</div>
    </div>
    """, unsafe_allow_html=True)

# --- LOGIC ---
def get_market_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m")
        if df.empty: return None
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        # RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        return df
    except: return None

# --- UI LAYOUT ---
col1, col2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [col1, col2][i]:
        df = get_market_data(sym)
        if df is not None:
            price = df['Close'].iloc[-1]
            vwap = df['VWAP'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            
            # Logic for Signal
            if price > vwap and rsi > 52:
                card_class, action, badge_col = "call-card", "🚀 BUY CALL (CE)", "#00ff00"
            elif price < vwap and rsi < 48:
                card_class, action, badge_col = "put-card", "📉 BUY PUT (PE)", "#ff4b4b"
            else:
                card_class, action, badge_col = "wait-card", "⏳ NEUTRAL / WAIT", "#ffffff"

            st.markdown(f"""
                <div class="trade-card {card_class}">
                    <div style="font-size: 16px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.7;">{name}</div>
                    <div class="price-val">₹{price:,.2f}</div>
                    <span class="signal-badge" style="color: {badge_col};">{action}</span>
                    <div class="metrics">VWAP: {vwap:,.1f} | RSI: {rsi:.1f}</div>
                </div>
                """, unsafe_allow_html=True)

# --- DISCIPLINE RULES (CLEAN CARDS) ---
st.markdown("### 🛡️ OPERATIONAL DISCIPLINE")
r1, r2, r3 = st.columns(3)

rule_box = "background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); height: 120px;"

r1.markdown(f"<div style='{rule_box}'><b>1. SYNC RULE</b><br><small style='color:#bbb;'>Only enter if NIFTY and BANK NIFTY signals match in direction.</small></div>", unsafe_allow_html=True)
r2.markdown(f"<div style='{rule_box}'><b>2. TAKE PROFIT</b><br><small style='color:#bbb;'>Close terminal once daily target is met. Do not overtrade.</small></div>", unsafe_allow_html=True)
r3.markdown(f"<div style='{rule_box}'><b>3. STOP LOSS</b><br><small style='color:#bbb;'>Never trade without a hard SL. Capital protection is #1.</small></div>", unsafe_allow_html=True)
