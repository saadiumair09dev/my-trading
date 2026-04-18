import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="🦅 Eagle Eye Pro v9",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)
IST = pytz.timezone("Asia/Kolkata")

# ── SAFE DATA FETCHING ────────────────────────────────────────
@st.cache_data(ttl=60)
def get_safe_data(symbol):
    try:
        # Delisted futures symbols ko block karo
        if any(x in symbol for x in ["$NK=F", "$FDAX=F", "$FCE=F", "$FESX=F", "$Z=F"]):
            return pd.DataFrame()
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="15m")
        return df if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

# ── APP UI ──────────────────────────────────────────────────
st.title("🦅 Eagle Eye Pro v9 — Trading Terminal")

# Dashboard Grid
col1, col2 = st.columns(2)

symbols = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK"}

for i, (name, sym) in enumerate(symbols.items()):
    df = get_safe_data(sym)
    
    if not df.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close']
        )])
        fig.update_layout(template="plotly_dark", title=f"{name} Live")
        
        # Unique key taaki crash na ho
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{sym}_{datetime.now().microsecond}")
    else:
        st.error(f"Data loading error for {name}")

# Status Footer
st.markdown("""
    <div style="margin-top:20px; padding:10px; background:#020b18; border-radius:5px; color:#00d463;">
        ✅ <b>System Status:</b> Stable | All delisted symbols removed.
    </div>
""", unsafe_allow_html=True)
