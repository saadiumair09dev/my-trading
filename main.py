import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz

# --- PAGE CONFIG ---
st.set_page_config(page_title="Eagle Eye Pro Stable", layout="wide")

# --- 1. SAFE DATA FETCHING (Delisted symbols ko handle karega) ---
@st.cache_data(ttl=60)
def get_safe_data(symbol):
    try:
        # Delisted futures symbols ko bypass karein
        if "$" in symbol:
            return pd.DataFrame()
            
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="15m")
        return df if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 2. SAFE CHART RENDERER (Unique ID ke sath) ---
def render_chart(fig, symbol):
    # Colors fix karein
    if fig and hasattr(fig, 'layout') and fig.layout.shapes:
        for shape in fig.layout.shapes:
            if isinstance(shape.line.color, str) and len(shape.line.color) > 7:
                shape.line.color = shape.line.color[:7]
                
    st.plotly_chart(
        fig, 
        use_container_width=True, 
        key=f"chart_{symbol}_{datetime.now().microsecond}"
    )

# --- APP UI ---
st.title("🦅 Eagle Eye Pro - Stable Version")

# Symbols List
symbols = ["^NSEI", "^NSEBANK"] 

for sym in symbols:
    st.subheader(f"Analysis for {sym}")
    df = get_safe_data(sym)
    
    if not df.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index, 
            open=df['Open'], 
            high=df['High'], 
            low=df['Low'], 
            close=df['Close']
        )])
        render_chart(fig, sym)
    else:
        st.error(f"{sym} ka data filhal available nahi hai.")

# Footer note
st.markdown("---")
st.write("System Status: Stable")
