import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Trade Radar", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Dark Radar Theme
st.markdown("""
    <style>
    .main { background-color: #03090f; color: #cbd5e1; }
    .stApp { background-color: #03090f; }
    .metric-card {
        background-color: #040e18;
        border: 1px solid #1e3a4a;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .price-text { font-size: 24px; font-weight: bold; color: #f1f5f9; }
    .symbol-text { font-size: 14px; color: #475569; letter-spacing: 2px; }
    </style>
    """, unsafe_allow_html=True)

# 1. Fetch Functions (Python style using requests)
def fetch_crypto_data():
    # Fetching from Binance for accuracy
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
    results = []
    try:
        for s in symbols:
            r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}")
            d = r.json()
            results.append({
                "symbol": s.replace("USDT", ""),
                "price": float(d['lastPrice']),
                "change": float(d['priceChangePercent']),
                "volume": float(d['quoteVolume'])
            })
        return results
    except:
        return []

def fetch_nifty_data():
    # Simplified data fetch
    return {
        "nifty": {"price": 22450, "change": 0.45},
        "gift": {"price": 22510, "change": -0.12}
    }

# --- HEADER ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("<h3 style='color:#f59e0b; margin:0;'>◈ TRADE RADAR</h3>", unsafe_allow_html=True)
    st.caption("MULTI-SOURCE ENGINE • LIVE")

# --- NIFTY SECTION ---
nifty_data = fetch_nifty_data()
n_col1, n_col2 = st.columns(2)

with n_col1:
    val = nifty_data['gift']
    color = "#22c55e" if val['change'] >= 0 else "#ef4444"
    st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid #f59e0b;">
            <div class="symbol-text">GIFT NIFTY</div>
            <div class="price-text">₹{val['price']:,}</div>
            <div style="color:{color}">{val['change']}%</div>
        </div>
    """, unsafe_allow_html=True)

with n_col2:
    val = nifty_data['nifty']
    color = "#22c55e" if val['change'] >= 0 else "#ef4444"
    st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid #38bdf8;">
            <div class="symbol-text">NIFTY 50</div>
            <div class="price-text">₹{val['price']:,}</div>
            <div style="color:{color}">{val['change']}%</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- CRYPTO GRID ---
crypto_prices = fetch_crypto_data()

if crypto_prices:
    cols = st.columns(3)
    for i, coin in enumerate(crypto_prices):
        with cols[i % 3]:
            change_color = "#22c55e" if coin['change'] >= 0 else "#ef4444"
            st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="symbol-text">{coin['symbol']}</span>
                        <span style="color:{change_color}; font-weight:bold;">{coin['change']}%</span>
                    </div>
                    <div class="price-text" style="margin:10px 0;">${coin['price']:,.2f}</div>
                    <div style="font-size:10px; color:#1e3a4a;">VOL: ${coin['volume']/1e6:.1f}M</div>
                </div>
            """, unsafe_allow_html=True)
            st.write("") # Spacer

# --- AUTO REFRESH ---
st.empty()
time.sleep(10)
st.rerun()
