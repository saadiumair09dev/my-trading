import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz  
from streamlit_autorefresh import st_autorefresh

# --- PAGE SETUP ---
st.set_page_config(page_title="Eagle Eye Global Sync", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=3000, key="live_update")

# --- TIME & STYLE ---
IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

st.markdown("""
    <style>
    .stApp { background: #000000; color: #ffffff; }
    .header-box { text-align: center; padding: 20px; border-bottom: 2px solid #222; margin-bottom: 25px; }
    .sync-card { padding: 40px 20px; border-radius: 30px; text-align: center; border: 2px solid #333; transition: 0.4s; position: relative; overflow: hidden; }
    .super-buy { background: linear-gradient(145deg, #004d1a, #000000); border-color: #00ff00; box-shadow: 0 0 40px rgba(0,255,0,0.3); }
    .super-sell { background: linear-gradient(145deg, #4d0000, #000000); border-color: #ff0000; box-shadow: 0 0 40px rgba(255,0,0,0.3); }
    .no-sync { background: #0a0a0a; border-color: #444; opacity: 0.8; }
    .status-text { font-size: 35px !important; font-weight: 900; margin: 20px 0; text-transform: uppercase; }
    .label-tag { font-size: 11px; color: #00ff00; letter-spacing: 2px; font-weight: bold; }
    .mini-data { font-size: 12px; color: #888; display: flex; justify-content: space-around; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ADVANCED SYNC LOGIC ---
def get_global_signals(symbol):
    try:
        # 1. GIFT Nifty (Global Trend - 15m)
        gift = yf.download("IN=F", period="2d", interval="15m", progress=False)
        # 2. Local Index (Execution - 1m)
        local = yf.download(symbol, period="1d", interval="1m", progress=False)
        
        if gift.empty or local.empty: return None

        # GIFT Trend Analysis (Current 15m candle vs previous)
        gift_now = gift['Close'].iloc[-1]
        gift_prev = gift['Close'].iloc[-2]
        gift_trend = "BULL" if gift_now > gift_prev else "BEAR"

        # Local Analysis (Price vs VWAP)
        price = local['Close'].iloc[-1]
        vwap = (local['Close'] * local['Volume']).cumsum() / local['Volume'].cumsum()
        vwap_val = vwap.iloc[-1]
        
        # Local Trend
        local_trend = "BULL" if price > vwap_val else "BEAR"
        
        return price, vwap_val, gift_trend, gift_now, local_trend
    except: return None

# --- UI RENDER ---
st.markdown(f'<div class="header-box"><h1>🦅 EAGLE EYE GLOBAL SYNC</h1><p>GIFT NIFTY (15M) ⚡ LOCAL NIFTY (1M) | {live_time}</p></div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]

for i, (sym, name) in enumerate(indices):
    with [c1, c2][i]:
        res = get_global_signals(sym)
        if res:
            price, vwap, gift_trend, gift_p, local_trend = res
            
            # THE ULTIMATE SYNC RULE
            if gift_trend == "BULL" and local_trend == "BULL":
                status, zone, msg = "🚀 SUPER BUY", "super-buy", "GLOBAL & LOCAL MATCHING"
            elif gift_trend == "BEAR" and local_trend == "BEAR":
                status, zone, msg = "📉 SUPER SELL", "super-sell", "GLOBAL & LOCAL MATCHING"
            else:
                status, zone, msg = "⏳ NO SYNC", "no-sync", "WAITING FOR GLOBAL ALIGNMENT"

            st.markdown(f'''
                <div class="sync-card {zone}">
                    <div class="label-tag">{msg}</div>
                    <div style="font-size: 16px; opacity: 0.6; margin-top:10px;">{name} FUTURE</div>
                    <div style="font-size: 45px; font-weight: 800; margin: 10px 0;">₹{price:,.2f}</div>
                    <div class="status-text">{status}</div>
                    <div class="mini-data">
                        <span>GIFT NIFTY: {gift_p:,.1f} ({gift_trend})</span>
                        <span>VWAP: {vwap:,.1f}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

st.divider()
st.info("🎯 **Strategy Rule:** Sirf 'SUPER' signals par dhyan dein. Jab GIFT Nifty (15M) aur Local Nifty (1M) ek saath move karte hain, tabhi bada breakout aata hai.")
