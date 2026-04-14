import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz  
from streamlit_autorefresh import st_autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="Eagle Eye Pro", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, key="live_update")

# --- TIME & CSS ---
IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

st.markdown("""
    <style>
    .stApp { background: #050505; color: #ffffff; }
    .header-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
    .status-bar { font-size: 12px; padding: 5px 15px; border-radius: 50px; background: rgba(255,255,255,0.1); }
    .trade-card { padding: 30px; border-radius: 25px; text-align: center; border: 1.5px solid rgba(255,255,255,0.1); transition: 0.3s; }
    .call-zone { background: linear-gradient(145deg, rgba(0, 200, 83, 0.15), rgba(0, 50, 0, 0.4)); border-color: #00c853; box-shadow: 0 0 20px rgba(0,200,83,0.1); }
    .put-zone { background: linear-gradient(145deg, rgba(255, 75, 75, 0.15), rgba(80, 0, 0, 0.4)); border-color: #ff4b4b; box-shadow: 0 0 20px rgba(255,75,75,0.1); }
    .trend-badge { font-size: 10px; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; margin-bottom: 10px; display: inline-block; }
    .price-val { font-size: 48px !important; font-weight: 800; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- ADVANCED DATA LOGIC ---
def get_pro_data(symbol):
    try:
        # Fetching 1m and 15m data
        df_1m = yf.download(symbol, period="2d", interval="1m", progress=False)
        df_15m = yf.download(symbol, period="5d", interval="15m", progress=False)
        
        if df_1m.empty or df_15m.empty: return None
        
        # 1m Indicators
        df_1m['VWAP'] = (df_1m['Close'] * df_1m['Volume']).cumsum() / df_1m['Volume'].cumsum()
        delta = df_1m['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df_1m['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        # 15m Trend (EMA 20)
        ema_15m = df_15m['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        current_15m = df_15m['Close'].iloc[-1]
        trend_15m = "BULLISH" if current_15m > ema_15m else "BEARISH"
        
        return df_1m, trend_15m
    except: return None

# --- VIX CHECK ---
def get_vix():
    try:
        vix = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False)
        return float(vix['Close'].iloc[-1])
    except: return 0

# --- UI HEADER ---
vix_val = get_vix()
vix_status = "⚠️ High Volatility" if vix_val > 20 else "✅ Normal"
st.markdown(f'''
    <div class="header-container">
        <div style="font-weight:bold; letter-spacing:1px;">🦅 EAGLE EYE PRO</div>
        <div class="status-bar">VIX: {vix_val:.2f} ({vix_status})</div>
        <div style="font-family:monospace;">{live_time}</div>
    </div>
''', unsafe_allow_html=True)

# --- MAIN DASHBOARD ---
c1, c2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [c1, c2][i]:
        data = get_pro_data(sym)
        if data:
            df, trend_15m = data
            price = float(df['Close'].iloc[-1])
            vwap = float(df['VWAP'].iloc[-1])
            rsi = float(df['RSI'].fillna(50).iloc[-1])
            
            # MULTI-TIMEFRAME LOGIC (1m + 15m)
            signal = "⏳ WAITING"
            card_style = ""
            trend_col = "#00c853" if trend_15m == "BULLISH" else "#ff4b4b"
            
            if price > vwap and rsi > 52 and trend_15m == "BULLISH":
                signal, card_style = "🚀 STRONG BUY (CE)", "call-zone"
            elif price < vwap and rsi < 48 and trend_15m == "BEARISH":
                signal, card_style = "📉 STRONG SELL (PE)", "put-zone"
            elif (price > vwap and trend_15m == "BEARISH") or (price < vwap and trend_15m == "BULLISH"):
                signal = "⚠️ TREND MISMATCH"
            
            st.markdown(f'''
                <div class="trade-card {card_style}">
                    <span class="trend-badge" style="background:{trend_col}22; color:{trend_col}; border:1px solid {trend_col}">15M Trend: {trend_15m}</span>
                    <div style="opacity:0.6; font-size:14px; margin-top:5px;">{name}</div>
                    <div class="price-val">₹{price:,.2f}</div>
                    <div style="font-size:22px; font-weight:bold; margin:15px 0;">{signal}</div>
                    <div style="font-size:12px; color:#888;">VWAP: {vwap:,.1f} | RSI: {rsi:.1f}</div>
                </div>
            ''', unsafe_allow_html=True)

st.divider()
st.caption("Strategy: Multi-Timeframe EMA Filter + VWAP + RSI. Refreshing every 3s.")
