import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────
#  PAGE SETUP
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Eagle Eye Global Sync",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st_autorefresh(interval=30000, key="live_update")  # ✅ 30 sec (3 sec too aggressive → rate limit)

IST = pytz.timezone('Asia/Kolkata')
live_time = datetime.now(IST).strftime("%I:%M:%S %p")

# ─────────────────────────────────────────
#  STYLES
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@700;900&display=swap');

* { font-family: 'Share Tech Mono', monospace; }
.stApp { background: #020409; color: #e0e0e0; }

.header-box {
    text-align: center; padding: 22px 10px 16px;
    border-bottom: 1px solid #1a2a1a; margin-bottom: 28px;
    background: linear-gradient(180deg, #050e05 0%, transparent 100%);
}
.header-box h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 28px; font-weight: 900; letter-spacing: 4px;
    color: #00ff88; margin: 0; text-shadow: 0 0 20px rgba(0,255,136,0.5);
}
.header-box p { font-size: 11px; color: #444; letter-spacing: 3px; margin: 8px 0 0; }

/* CARDS */
.sync-card {
    padding: 30px 20px 24px; border-radius: 16px;
    text-align: center; border: 1px solid #333;
    transition: all 0.4s ease; position: relative; overflow: hidden;
    margin-bottom: 10px;
}
.super-buy  { background: linear-gradient(160deg,#001a0a,#000); border-color:#00ff88; box-shadow:0 0 50px rgba(0,255,136,0.2); }
.super-sell { background: linear-gradient(160deg,#1a0000,#000); border-color:#ff3355; box-shadow:0 0 50px rgba(255,51,85,0.2); }
.no-sync    { background: #080808; border-color:#222; }
.error-card { background: #0a0808; border-color:#ff4400; border-style: dashed; }

.name-tag   { font-size:10px; color:#555; letter-spacing:3px; margin-bottom:6px; }
.price-big  { font-size:40px; font-weight:800; letter-spacing:1px; margin:8px 0; }
.buy-price  { color:#00ff88; }
.sell-price { color:#ff3355; }
.wait-price { color:#888; }

.status-pill {
    display:inline-block; padding:8px 22px; border-radius:30px;
    font-family:'Orbitron',sans-serif; font-size:15px; font-weight:900;
    letter-spacing:2px; margin:10px 0;
}
.pill-buy  { background:#00ff8822; color:#00ff88; border:1px solid #00ff8866; }
.pill-sell { background:#ff335522; color:#ff3355; border:1px solid #ff335566; }
.pill-wait { background:#22222200; color:#555;    border:1px solid #333; }

/* SCORE BAR */
.score-row { display:flex; justify-content:center; gap:8px; margin:14px 0 10px; }
.score-dot {
    width:12px; height:12px; border-radius:50%;
    display:inline-block;
}
.dot-on-buy  { background:#00ff88; box-shadow:0 0 8px #00ff88; }
.dot-on-sell { background:#ff3355; box-shadow:0 0 8px #ff3355; }
.dot-off     { background:#1a1a1a; border:1px solid #333; }

/* INDICATOR ROW */
.ind-row { display:flex; justify-content:space-around; flex-wrap:wrap; gap:6px; margin-top:14px; }
.ind-chip {
    font-size:10px; padding:4px 10px; border-radius:6px;
    letter-spacing:1px; white-space:nowrap;
}
.chip-bull { background:#00ff8815; color:#00ff88; border:1px solid #00ff8830; }
.chip-bear { background:#ff335515; color:#ff3355; border:1px solid #ff335530; }
.chip-neut { background:#22222230; color:#666;    border:1px solid #333; }

.footer-note {
    text-align:center; font-size:11px; color:#333; letter-spacing:1px;
    margin-top:20px; padding: 14px; border-top:1px solid #111;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────
def flatten(df):
    """yfinance naye versions mein MultiIndex columns deta hai — flatten karo."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def calc_rsi(series, period=14):
    """RSI (Relative Strength Index) calculate karo."""
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = -delta.clip(upper=0).rolling(period).mean()
    rs    = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


# ─────────────────────────────────────────
#  DATA FETCH  (cached — rate limit safe)
# ─────────────────────────────────────────
@st.cache_data(ttl=30)
def get_gift_data():
    """
    GIFT Nifty Futures Yahoo Finance par directly available nahi hain.
    Best proxy = ^NSEI (15m), jo global overnight sentiment reflect karta hai.
    Agar International broker API ho (e.g. Zerodha WebSocket) to wahan se lo.
    """
    try:
        df = yf.download("^NSEI", period="3d", interval="15m", progress=False)
        df = flatten(df)
        if df.empty:
            return None
        return df
    except Exception as e:
        st.warning(f"GIFT data error: {e}")
        return None


@st.cache_data(ttl=30)
def get_local_data(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1m", progress=False)
        df = flatten(df)
        if df.empty:
            return None
        return df
    except Exception as e:
        st.warning(f"Local data error ({symbol}): {e}")
        return None


# ─────────────────────────────────────────
#  CORE ANALYSIS ENGINE
# ─────────────────────────────────────────
def analyze(symbol):
    """
    Multi-factor signal engine:
    ┌─ Factor 1: GIFT Nifty 15m trend      (1 pt)
    ├─ Factor 2: Price vs VWAP             (1 pt)
    ├─ Factor 3: EMA9 vs EMA21 crossover   (1 pt)
    └─ Factor 4: Volume surge              (1 pt)

    RSI filter (veto):
    • BUY  signal lekin RSI > 72 → WAIT (overbought)
    • SELL signal lekin RSI < 28 → WAIT (oversold)

    Final signal:
    • Score 4/4 → ⚡ STRONG SUPER BUY/SELL
    • Score 3/4 → 🚀 SUPER BUY / 📉 SUPER SELL
    • Score < 3  → ⏳ NO SYNC
    """
    try:
        gift  = get_gift_data()
        local = get_local_data(symbol)

        if gift is None or local is None:
            return None

        # ── GIFT TREND (15m) ──────────────────────────────
        gift_close = gift['Close'].dropna()
        if len(gift_close) < 4:
            return None
        
        gift_now  = float(gift_close.iloc[-1])
        gift_prev = float(gift_close.iloc[-2])
        gift_chg  = (gift_now - gift_prev) / gift_prev * 100  # % change

        # Threshold 0.05% se kam = noise, NEUTRAL treat karo
        if gift_chg > 0.05:
            gift_trend = "BULL"
        elif gift_chg < -0.05:
            gift_trend = "BEAR"
        else:
            gift_trend = "NEUTRAL"

        # ── LOCAL INDICATORS (1m) ─────────────────────────
        price = float(local['Close'].iloc[-1])

        # VWAP
        cum_vol = local['Volume'].cumsum().replace(0, np.nan)
        vwap    = (local['Close'] * local['Volume']).cumsum() / cum_vol
        vwap_val = float(vwap.iloc[-1])

        # EMA Crossover
        ema9  = float(local['Close'].ewm(span=9,  adjust=False).mean().iloc[-1])
        ema21 = float(local['Close'].ewm(span=21, adjust=False).mean().iloc[-1])

        # RSI
        rsi = float(calc_rsi(local['Close']).iloc[-1])

        # Volume Surge (current vol vs 20-bar average)
        avg_vol  = float(local['Volume'].rolling(20).mean().iloc[-1])
        curr_vol = float(local['Volume'].iloc[-1])
        vol_surge = (curr_vol > avg_vol * 1.5) and (avg_vol > 0)

        # ── SCORING ──────────────────────────────────────
        indicators = {}

        # Factor 1: GIFT
        indicators['gift'] = gift_trend  # BULL / BEAR / NEUTRAL

        # Factor 2: VWAP
        indicators['vwap'] = "BULL" if price > vwap_val else "BEAR"

        # Factor 3: EMA Crossover
        indicators['ema']  = "BULL" if ema9 > ema21 else "BEAR"

        # Factor 4: Volume
        indicators['vol']  = "BULL" if vol_surge else "NEUT"

        def score(direction):
            pts = 0
            if indicators['gift'] == direction: pts += 1
            if indicators['vwap'] == direction: pts += 1
            if indicators['ema']  == direction: pts += 1
            if indicators['vol']  == "BULL":    pts += 1  # vol surge = confirmation
            return pts

        bull_pts = score("BULL")
        bear_pts = score("BEAR")

        # ── SIGNAL DETERMINATION ─────────────────────────
        strong = False
        if bull_pts >= 3 and gift_trend == "BULL":
            # RSI veto: overbought mein BUY mat lo
            if rsi > 72:
                signal = "NO SYNC"
            else:
                signal = "SUPER BUY"
                strong = (bull_pts == 4)
        elif bear_pts >= 3 and gift_trend == "BEAR":
            # RSI veto: oversold mein SELL mat lo
            if rsi < 28:
                signal = "NO SYNC"
            else:
                signal = "SUPER SELL"
                strong = (bear_pts == 4)
        else:
            signal = "NO SYNC"

        return {
            "price":      price,
            "vwap":       vwap_val,
            "ema9":       ema9,
            "ema21":      ema21,
            "rsi":        rsi,
            "gift_trend": gift_trend,
            "gift_price": gift_now,
            "gift_chg":   gift_chg,
            "vol_surge":  vol_surge,
            "bull_pts":   bull_pts,
            "bear_pts":   bear_pts,
            "indicators": indicators,
            "signal":     signal,
            "strong":     strong,
        }

    except Exception as e:
        st.error(f"Analysis error ({symbol}): {e}")
        return None


# ─────────────────────────────────────────
#  RENDER CARD
# ─────────────────────────────────────────
def render_card(name, res):
    if res is None:
        st.markdown(f"""
        <div class="sync-card error-card">
            <div class="name-tag">{name} FUTURE</div>
            <div class="price-big wait-price">- - -</div>
            <div class="status-pill pill-wait">⚠ DATA ERROR</div>
            <div class="ind-row"><span class="ind-chip chip-neut">Check API / Internet</span></div>
        </div>""", unsafe_allow_html=True)
        return

    sig    = res["signal"]
    strong = res["strong"]

    # Card class + colors
    if sig == "SUPER BUY":
        card_cls   = "super-buy"
        price_cls  = "buy-price"
        pill_cls   = "pill-buy"
        icon       = "⚡" if strong else "🚀"
        label      = f"{icon} {'STRONG ' if strong else ''}SUPER BUY"
        score_pts  = res["bull_pts"]
        dot_on_cls = "dot-on-buy"
    elif sig == "SUPER SELL":
        card_cls   = "super-sell"
        price_cls  = "sell-price"
        pill_cls   = "pill-sell"
        icon       = "⚡" if strong else "📉"
        label      = f"{icon} {'STRONG ' if strong else ''}SUPER SELL"
        score_pts  = res["bear_pts"]
        dot_on_cls = "dot-on-sell"
    else:
        card_cls   = "no-sync"
        price_cls  = "wait-price"
        pill_cls   = "pill-wait"
        label      = "⏳ WAITING SYNC"
        score_pts  = max(res["bull_pts"], res["bear_pts"])
        dot_on_cls = "dot-off"

    # Score dots (4 max)
    dots = ""
    for i in range(4):
        cls = dot_on_cls if i < score_pts else "dot-off"
        dots += f'<span class="score-dot {cls}"></span>'

    # Indicator chips
    ind = res["indicators"]
    def chip(label_text, val):
        cls = "chip-bull" if val == "BULL" else ("chip-bear" if val == "BEAR" else "chip-neut")
        return f'<span class="ind-chip {cls}">{label_text}: {val}</span>'

    chips = (
        chip("GIFT 15m", ind["gift"]) +
        chip("VWAP", ind["vwap"]) +
        chip("EMA", ind["ema"]) +
        chip("VOL", "SURGE" if res["vol_surge"] else "NORMAL") +
        chip(f"RSI {res['rsi']:.0f}", "NEUT" if 35 < res["rsi"] < 65 else ("BEAR" if res["rsi"] >= 65 else "BULL"))
    )

    st.markdown(f"""
    <div class="sync-card {card_cls}">
        <div class="name-tag">{name} FUTURE</div>
        <div class="price-big {price_cls}">₹{res['price']:,.1f}</div>
        <div><span class="status-pill {pill_cls}">{label}</span></div>
        <div class="score-row">{dots}</div>
        <div style="font-size:9px;color:#333;letter-spacing:2px;margin-bottom:4px;">SIGNAL STRENGTH ({score_pts}/4)</div>
        <div class="ind-row">{chips}</div>
        <div style="font-size:10px;color:#333;margin-top:12px;letter-spacing:1px;">
            GIFT ₹{res['gift_price']:,.0f} ({res['gift_chg']:+.2f}%) &nbsp;|&nbsp; 
            VWAP ₹{res['vwap']:,.1f} &nbsp;|&nbsp; 
            EMA9/21: {res['ema9']:,.0f}/{res['ema21']:,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────
st.markdown(f"""
<div class="header-box">
    <h1>🦅 EAGLE EYE GLOBAL SYNC</h1>
    <p>GIFT NIFTY (15M) ⚡ LOCAL (1M) | EMA · VWAP · RSI · VOLUME | {live_time} IST</p>
</div>
""", unsafe_allow_html=True)

indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY")]
c1, c2 = st.columns(2)

for i, (sym, name) in enumerate(indices):
    with [c1, c2][i]:
        res = analyze(sym)
        render_card(name, res)

# ─────────────────────────────────────────
#  STRATEGY LEGEND
# ─────────────────────────────────────────
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("**📡 Factor 1 — GIFT 15m**\nGlobal trend proxy. Change > 0.05% tabhi count hoga, nahi to NEUTRAL.")
with col2:
    st.markdown("**📊 Factor 2 — VWAP**\nPrice > VWAP = institutional buying zone. Price < VWAP = selling pressure.")
with col3:
    st.markdown("**📈 Factor 3 — EMA 9/21**\nFast EMA > Slow EMA = momentum bullish. Crossover = trend shift signal.")
with col4:
    st.markdown("**🔊 Factor 4 — Volume Surge**\nVolume > 1.5x average = smart money entering. Confirmation filter.")

st.markdown("""
<div class="footer-note">
⚡ STRONG signal = 4/4 factors align &nbsp;|&nbsp; 
🚀 SUPER signal = 3/4 factors &nbsp;|&nbsp; 
RSI > 72 → BUY veto &nbsp;|&nbsp; RSI < 28 → SELL veto &nbsp;|&nbsp;
Auto-refresh: 30 sec
</div>
""", unsafe_allow_html=True)
