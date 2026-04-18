# 🦅 Eagle Eye Pro v12 — INSTITUTIONAL PRO TERMINAL
# 🔥 Options Chain + Smart Entry/Exit + AI Signals + Pro UI

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="🦅 Eagle Eye Pro v12", layout="wide")
IST = pytz.timezone("Asia/Kolkata")

st_autorefresh(interval=8000)

# SESSION
if "signals" not in st.session_state:
    st.session_state.signals = []

# SAFE CHECK
def safe_df(df):
    return df is not None and hasattr(df, "__len__") and len(df) > 0

# DATA
@st.cache_data(ttl=8)
def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="5d", interval="5m")
        return df if safe_df(df) else None
    except:
        return None

# VIX
@st.cache_data(ttl=20)
def get_vix():
    try:
        df = yf.Ticker("^INDIAVIX").history(period="5d")
        if safe_df(df):
            return float(df["Close"].iloc[-1])
        return None
    except:
        return None

# INDICATORS
def indicators(df):
    try:
        c = df["Close"]
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()

        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))

        return (
            float(c.iloc[-1]),
            float(ema9.iloc[-1]),
            float(ema21.iloc[-1]),
            float(ema50.iloc[-1]),
            float(rsi.iloc[-1])
        )
    except:
        return 0,0,0,0,50

# AI SIGNAL
def ai_signal(price, ema9, ema21, ema50, rsi, vix):
    score = 0

    if price > ema9: score += 1
    if ema9 > ema21: score += 1
    if ema21 > ema50: score += 1
    if rsi > 55: score += 1

    if vix is not None and vix > 20:
        score -= 1

    if score >= 3:
        return "BUY", score
    elif score <= 1:
        return "SELL", score
    return "WAIT", score

# ENTRY EXIT SYSTEM
def trade_levels(price, sig):
    try:
        if sig == "BUY":
            sl = price * 0.995
            tgt = price * 1.01
        elif sig == "SELL":
            sl = price * 1.005
            tgt = price * 0.99
        else:
            return None, None
        return round(sl,2), round(tgt,2)
    except:
        return None, None

# OPTIONS CHAIN (SIMPLIFIED)
def options_chain(symbol="^NSEI"):
    try:
        opt = yf.Ticker(symbol).options
        return opt[:3] if opt else []
    except:
        return []

# UI
st.markdown("""
<style>
.big {font-size:22px !important; font-weight:bold;}
.glow {color:#00ffcc;}
</style>
""", unsafe_allow_html=True)

st.title("🦅 Eagle Eye Pro v12 — INSTITUTIONAL MODE")

symbols = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "^CNXFIN"
}

vix = get_vix()
st.subheader(f"VIX: {vix:.2f}" if vix is not None else "VIX unavailable")

cols = st.columns(3)

for i,(name,sym) in enumerate(symbols.items()):
    df = get_data(sym)

    with cols[i]:
        if not safe_df(df):
            st.error("Data error")
            continue

        price, ema9, ema21, ema50, rsi = indicators(df)
        sig, score = ai_signal(price, ema9, ema21, ema50, rsi, vix)

        st.metric(name, f"{price:.2f}")
        st.progress(min(score/4,1.0))

        sl, tgt = trade_levels(price, sig)

        if sig == "BUY":
            st.success(f"BUY | SL: {sl} | TGT: {tgt}")
        elif sig == "SELL":
            st.error(f"SELL | SL: {sl} | TGT: {tgt}")
        else:
            st.warning("WAIT")

        # SAFE SIGNAL LOG
        st.session_state.signals.append({
            "time": datetime.now(IST).strftime("%H:%M:%S"),
            "symbol": name,
            "signal": sig,
            "price": price
        })
        st.session_state.signals = st.session_state.signals[-30:]

# CHART
st.subheader("📈 Chart")
sym = st.selectbox("Select", list(symbols.values()))
df = get_data(sym)

if safe_df(df):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Chart data unavailable")

# OPTIONS
st.subheader("📊 Options Chain (Expiries)")
exp = options_chain()
st.write(exp if exp else "No data")

# LOG
st.subheader("📜 Trade Log")
if st.session_state.signals:
    st.dataframe(pd.DataFrame(st.session_state.signals))
else:
    st.info("No trades yet")

st.caption("⚡ v12 Institutional Build — Smart Money Ready")
