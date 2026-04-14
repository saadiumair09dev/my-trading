import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="Alpha Pro Live", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, key="live_update")

# --- CUSTOM CSS (Clean & Big UI) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .live-indicator { color: #00ff00; font-size: 14px; font-weight: bold; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .card { padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 20px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .call-card { background: linear-gradient(135deg, #00c853 0%, #007e33 100%); border: 3px solid #ffffff; }
    .put-card { background: linear-gradient(135deg, #ff4b4b 0%, #8b0000 100%); border: 3px solid #ffffff; }
    .wait-card { background: linear-gradient(135deg, #2c3e50 0%, #000000 100%); border: 1px solid #555; }
    .price-text { font-size: 60px !important; font-weight: 900; margin: 10px 0; }
    .signal-text { font-size: 30px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; }
    .momentum-badge { background: rgba(0,0,0,0.3); padding: 8px 15px; border-radius: 10px; font-size: 16px; display: inline-block; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_live_data(symbol):
    try:
        data = yf.download(symbol, period="1d", interval="1m")
        if data.empty: return None
        # Logic
        data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        data['RSI'] = 100 - (100 / (1 + (gain/loss)))
        data['Momentum'] = data['Close'].diff(5) # 5 min change
        return data
    except: return None

# --- HEADER ---
now = datetime.now().strftime("%H:%M:%S")
st.markdown(f"<div style='text-align:right;'><span class='live-indicator'>●</span> LIVE UPDATING: {now}</div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: white;'>🦅 ALPHA DIRECTIONAL PRO</h1>", unsafe_allow_html=True)

# --- DASHBOARD ---
col1, col2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [col1, col2][i]:
        df = get_live_data(sym)
        if df is not None:
            price = df['Close'].iloc[-1]
            vwap = df['VWAP'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            mom = df['Momentum'].iloc[-1]
            
            # --- DIRECTION LOGIC ---
            if price > vwap and rsi > 55:
                card_style, action, trend = "call-card", "🚀 BUY CALL (CE)", "STRONG BULLISH"
            elif price < vwap and rsi < 45:
                card_style, action, trend = "put-card", "📉 BUY PUT (PE)", "STRONG BEARISH"
            else:
                card_style, action, trend = "wait-card", "⏳ WAIT / NO TRADE", "SIDEWAYS"

            # --- RENDER UI ---
            mom_icon = "🔥" if abs(mom) > 15 else "⚖️"
            st.markdown(f"""
                <div class="card {card_style}">
                    <div style="font-size: 24px;">{name}</div>
                    <div class="price-text">₹{price:,.2f}</div>
                    <div class="signal-text">{action}</div>
                    <div class="momentum-badge">{mom_icon} Momentum: {mom:.2f}</div>
                    <div style="margin-top:10px; font-size:14px; opacity:0.8;">Trend: {trend} | RSI: {rsi:.1f}</div>
                </div>
                """, unsafe_allow_html=True)

# --- FOOTER RULES ---
st.divider()
st.markdown("### 🛡️ TRADING DISCIPLINE")
c1, c2, c3 = st.columns(3)
c1.success("1. Card Green + PCR > 1 = BUY CALL")
c2.error("2. Card Red + PCR < 1 = BUY PUT")
c3.warning("3. Target Hit? System Band!")
