import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz  
from streamlit_autorefresh import st_autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="Eagle Eye Pro Terminal", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, key="live_update")

# --- IST TIME ---
IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

# --- CSS (Advanced UI with Dynamic Colors) ---
st.markdown("""
    <style>
    .stApp { background: #050505; color: #ffffff; }
    .header-container { background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
    
    .trade-card { padding: 30px; border-radius: 20px; text-align: center; border: 1.5px solid rgba(255,255,255,0.1); margin-bottom: 20px; transition: 0.5s; }
    
    /* STRONG SIGNALS */
    .strong-call { background: linear-gradient(145deg, rgba(0, 255, 100, 0.2), rgba(0, 80, 0, 0.6)); border: 2px solid #00ff64; box-shadow: 0 0 25px rgba(0,255,100,0.3); }
    .strong-put { background: linear-gradient(145deg, rgba(255, 30, 30, 0.2), rgba(100, 0, 0, 0.6)); border: 2px solid #ff1e1e; box-shadow: 0 0 25px rgba(255,30,30,0.3); }
    
    /* WEAK/NEUTRAL SIGNALS */
    .wait-card { background: rgba(255, 255, 255, 0.03); border: 1.5px solid #444; }
    
    .price-val { font-size: 50px !important; font-weight: 800; margin: 5px 0; font-family: 'Courier New', monospace; }
    .pdc-val { font-size: 13px; color: #ff9800; font-weight: bold; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f'<div class="header-container"><div>🦅 <b>EAGLE EYE PRO</b></div><div>IST: {live_time}</div></div>', unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=2)
def get_pro_data(symbol):
    try:
        # Fetch 5 days to ensure we get Previous Day Close correctly
        df = yf.download(symbol, period="5d", interval="1m", progress=False)
        if df.empty: return None
        
        # 1. Previous Day Close (PDC)
        # पिछले दिन का आखिरी Close ढूंढना
        day_groups = df.groupby(df.index.date)
        if len(day_groups) >= 2:
            prev_day_date = list(day_groups.groups.keys())[-2]
            pdc = df.loc[str(prev_day_date)]['Close'].iloc[-1]
        else:
            pdc = df['Close'].iloc[0]

        # 2. Indicators
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        return df, pdc
    except:
        return None, None

# --- UI LAYOUT ---
col1, col2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [col1, col2][i]:
        df, pdc = get_pro_data(sym)
        
        if df is not None:
            price = float(df['Close'].iloc[-1])
            vwap = float(df['VWAP'].iloc[-1])
            rsi = float(df['RSI'].fillna(50).iloc[-1])
            ema200 = float(df['EMA200'].iloc[-1])
            
            # --- ADVANCED SIGNAL LOGIC ---
            is_above_pdc = price > pdc
            is_above_ema = price > ema200
            
            # Strong BUY: Price > VWAP AND RSI > 52 AND Trend is UP
            if price > vwap and rsi > 52 and is_above_ema:
                cls, action = "strong-call", "🚀 STRONG BUY (CE)"
            # Strong SELL: Price < VWAP AND RSI < 48 AND Trend is DOWN
            elif price < vwap and rsi < 48 and not is_above_ema:
                cls, action = "strong-put", "📉 STRONG BUY (PE)"
            else:
                cls, action = "wait-card", "⏳ NEUTRAL / WAIT"

            # Color for PDC comparison
            pdc_color = "#00ff00" if is_above_pdc else "#ff4b4b"

            st.markdown(f"""
                <div class="trade-card {cls}">
                    <div class="pdc-val" style="color: {pdc_color};">
                        PDC: ₹{pdc:,.2f} ({"▲ ABOVE" if is_above_pdc else "▼ BELOW"})
                    </div>
                    <div style="opacity:0.8; font-size: 14px; letter-spacing:1px;">{name}</div>
                    <div class="price-val">₹{price:,.2f}</div>
                    <div style="font-weight:bold; font-size:22px; margin: 15px 0;">{action}</div>
                    <div style="font-size:12px; color:#aaa; border-top: 1px solid #333; padding-top: 10px;">
                        VWAP: {vwap:,.1f} | RSI: {rsi:.1f} | EMA200: {ema200:,.1f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error(f"{name}: Fetching...")

st.divider()
st.caption("PDC = Previous Day Close | Indicators: VWAP, RSI (14), EMA (200)")
