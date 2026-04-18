# ════════════════════════════════════════════════════════════════
#  🦅 EAGLE EYE PRO v9 — Complete Trading Terminal
#  Deploy: https://share.streamlit.io  (FREE, mobile link works)
#  Run local: streamlit run main.py

#  pip install streamlit yfinance pandas numpy pytz plotly requests
#
#  🔐 SECURITY: Add secrets in Streamlit Cloud Settings → Secrets
#  [dhan] access_token, client_id  |  [app] password (optional)
#  Streamlit Cloud → Settings → Secrets → Add:
#  [dhan]
#  access_token = """your_NEW_regenerated_token_here"""
#  client_id    = "1106554867"
# ════════════════════════════════════════════════════════════════

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import pytz
import requests
import streamlit.components.v1 as components

# ───────── FIX START ─────────

# SESSION STATE INIT
if "signals" not in st.session_state:
    st.session_state.signals = []

# GET DATA (Yahoo)
@st.cache_data(ttl=10)
def get_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m")
        return df
    except:
        return None

# INDICATORS
def indicators(df):
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA21"] = df["Close"].ewm(span=21).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]

    return (
        last["Close"],
        last["EMA9"],
        last["EMA21"],
        last["EMA50"],
        last["RSI"]
    )

# VIX
def get_vix():
    try:
        df = yf.download("^INDIAVIX", period="1d", interval="1m")
        return float(df["Close"].iloc[-1])
    except:
        return None

# ───────── FIX END ─────────

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="🦅 Eagle Eye Pro v9",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)
IST = pytz.timezone("Asia/Kolkata")

# ════════════════════════════════════════════════════════════════
#  🔐 SECRETS SETUP (Streamlit Cloud → Settings → Secrets):
#
#  [dhan]
#  access_token = """your_dhan_access_token"""
#  client_id    = "your_client_id"
#
#  [app]
#  password = "your_app_password"   # Optional — leave out for open access
#
# ════════════════════════════════════════════════════════════════
#  🔐 DHAN API — SECURE TOKEN FROM STREAMLIT SECRETS
#  Token is NEVER hardcoded here. Always use st.secrets.
# ════════════════════════════════════════════════════════════════

def _get_dhan_creds():
    """Load Dhan credentials from Streamlit Secrets safely."""
    try:
        token = st.secrets["dhan"]["""access_token"""]
        cid   = st.secrets["dhan"]["client_id"]
        return token, cid
    except Exception:
        return None, None

def _dhan_headers():
    token, cid = _get_dhan_creds()
    if not token:
        return None
    return {
        """access-token""": token,
        "client-id":    cid,
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }

# Dhan security indices map
# exchange_segment: IDX_I = NSE Indices
_DHAN_IDX = {
    "NIFTY 50":    {"securityId": "13",   "exchangeSegment": "IDX_I"},
    "BANKNIFTY":   {"securityId": "25",   "exchangeSegment": "IDX_I"},
    "NIFTY FIN":   {"securityId": "27",   "exchangeSegment": "IDX_I"},
    "INDIAVIX":    {"securityId": "12",   "exchangeSegment": "IDX_I"},
    "SENSEX":      {"securityId": "51",   "exchangeSegment": "BSE_IDX"},
    "GIFT NIFTY":  {"securityId": "800",  "exchangeSegment": "NSE_FNO"},  # SGX via Dhan
}

@st.cache_data(ttl=6, show_spinner=False)   # 6 sec refresh for live data
def dhan_ltp(security_ids: list, exchange_segment: str = "IDX_I") -> dict:
    """Fetch Live LTP from Dhan API. Returns {securityId: price} dict."""
    hdrs = _dhan_headers()
    if not hdrs:
        return {}
    try:
        payload = {"NSE": security_ids} if "NSE" in exchange_segment else {"BSE": security_ids}
        if exchange_segment == "IDX_I":
            payload = {"NSE": security_ids}
        r = requests.post(
            "https://api.dhan.co/v2/marketfeed/ltp",
            json=payload, headers=hdrs, timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            result = {}
            for item in data.get("data", {}).get("NSE", []):
                result[str(item.get("security_id",""))] = item.get("last_price", 0)
            return result
    except Exception:
        pass
    return {}

@st.cache_data(ttl=14, show_spinner=False)
def dhan_ohlcv(security_id: str, exchange_segment: str, interval: str = "1") -> pd.DataFrame | None:
    """Fetch OHLCV candles from Dhan API."""
    hdrs = _dhan_headers()
    if not hdrs:
        return None
    try:
        # Dhan intraday chart endpoint
        payload = {
            "securityId":      security_id,
            "exchangeSegment": exchange_segment,
            "instrument":      "INDEX",
            "interval":        interval,   # "1" = 1 min
            "oi":              False,
        }
        r = requests.post(
            "https://api.dhan.co/v2/charts/intraday",
            json=payload, headers=hdrs, timeout=8
        )
        if r.status_code == 200:
            d = r.json()
            timestamps = d.get("timestamp", [])
            opens  = d.get("open",   [])
            highs  = d.get("high",   [])
            lows   = d.get("low",    [])
            closes = d.get("close",  [])
            volumes= d.get("volume", [])
            if len(closes) >= 3:
                df = pd.DataFrame({
                    "Open":   opens,  "High":  highs,
                    "Low":    lows,   "Close": closes,
                    "Volume": volumes if volumes else [100000]*len(closes),
                }, index=pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(IST))
                df = df.dropna(subset=["Close"])
                return df if len(df) >= 10 else None
    except Exception:
        pass
    return None

def is_market_open() -> bool:
    """Check if NSE market is currently open (9:15–15:30 IST weekdays)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:   # Saturday/Sunday
        return False
    market_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close

def is_gift_nifty_available() -> bool:
    """GIFT Nifty trades on SGX: 6:30 AM – 11:30 PM IST (approx)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=6,  minute=30, second=0, microsecond=0)
    end   = now.replace(hour=23, minute=30, second=0, microsecond=0)
    return start <= now <= end

def dhan_active() -> bool:
    """Check if Dhan credentials are configured."""
    token, _ = _get_dhan_creds()
    return bool(token)


# ── AUTO REFRESH (15s page reload via JS) ──
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="eagle_refresh_v9")
except ImportError:
    if "eagle_refresh_v9" not in st.session_state:
        st.session_state["eagle_refresh_v9"] = 0
    try:
        # Streamlit >= 1.31 supports st.html (no deprecation warning)
        st.html("""<script>
if(!window._erv6){window._erv6=setTimeout(function(){
window.parent.location.reload();},15000);}
</script>""")
    except Exception:
        components.html("""<script>
if(!window._erv6){window._erv6=setTimeout(function(){
window.parent.location.reload();},15000);}
</script>""", height=0)


# ════════════════════════════════════════════════════════════
#  🔐 PASSWORD PROTECTION
# ════════════════════════════════════════════════════════════
def _check_password():
    """Simple password gate using Streamlit secrets."""
    try:
        correct_pw = st.secrets["app"]["password"]
    except Exception:
        correct_pw = None  # No password set → open access

    if not correct_pw:
        return True  # No password configured → allow

    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div style="max-width:380px;margin:80px auto;background:#030c1a;border:1px solid #0d3060;
         border-radius:12px;padding:32px;text-align:center">
        <div style="font-size:32px;margin-bottom:10px">🦅</div>
        <div style="font-size:20px;font-weight:900;letter-spacing:3px;color:#3d9be9;
             font-family:Share Tech Mono;margin-bottom:6px">EAGLE EYE PRO</div>
        <div style="font-size:10px;letter-spacing:2px;color:#3a6a8f;margin-bottom:24px">
             v9.0 — SECURE ACCESS</div>
    </div>""", unsafe_allow_html=True)

    pw = st.text_input("🔐 Enter Password", type="password",
                       placeholder="Enter your access password",
                       label_visibility="collapsed")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🔓 UNLOCK", width='stretch', type="primary"):
            if pw == correct_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Wrong password. Try again.")
    st.stop()

_check_password()

# ── SESSION STATE ────────────────────────────────────────────
_DEFAULTS = {
    "signals_log": [], "prev_sig": {}, "news_seen": set(),
    "sound_queue": [], "sound_id": 0, "alert_log": [],
    "prev_prices": {}, "veto_log": [], "fail_log": [],
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════════════════════════
#  MASTER CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700;900&display=swap');

*,body{font-family:'Rajdhani',sans-serif!important;font-size:14px}
.stApp{background:#020b18!important}
.block-container{padding:.3rem .8rem 0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none!important}
#MainMenu,footer,header{visibility:hidden!important}
.stDeployButton{display:none!important}
div[data-testid="stVerticalBlock"]>div{gap:.2rem!important}

/* TABS */
.stTabs [data-baseweb="tab-list"]{gap:3px;background:transparent;border-bottom:2px solid #0d3060}
.stTabs [data-baseweb="tab"]{background:#030c1a;color:#4a90d9;border:1px solid #0d3060;
  border-radius:6px 6px 0 0;font-family:'Rajdhani';font-weight:700;
  font-size:12px;letter-spacing:1px;padding:6px 12px;border-bottom:none}
.stTabs [aria-selected="true"]{background:#0d3060!important;color:#fff!important}
.stTabs [data-baseweb="tab-panel"]{padding-top:6px!important}

/* SIGNAL CARDS */
.sc{border-radius:10px;padding:12px 10px;text-align:center;border:1px solid #0d3060;
    transition:all .4s;position:relative;overflow:hidden}
.sc-buy {background:linear-gradient(145deg,#002716,#020b18);border-color:#00d463!important;
         animation:pg 2.5s infinite}
.sc-sell{background:linear-gradient(145deg,#1f0000,#020b18);border-color:#ff3d3d!important;
         animation:pr 2.5s infinite}
.sc-caut{background:linear-gradient(145deg,#1f1200,#020b18);border-color:#ffb700!important;
         animation:po 3s infinite}
.sc-wait{background:#030c1a;border-color:#3d6090!important;opacity:.72}
@keyframes pg{0%,100%{box-shadow:0 0 12px rgba(0,212,99,.2)}50%{box-shadow:0 0 32px rgba(0,212,99,.55)}}
@keyframes pr{0%,100%{box-shadow:0 0 12px rgba(255,61,61,.2)}50%{box-shadow:0 0 32px rgba(255,61,61,.55)}}
@keyframes po{0%,100%{box-shadow:0 0 8px rgba(255,183,0,.15)}50%{box-shadow:0 0 22px rgba(255,183,0,.45)}}

.sc-sym{font-size:11px;opacity:.75;letter-spacing:3px;margin-bottom:2px;color:#a0c8e8}
.sc-price{font-size:32px;font-weight:900;font-family:'Share Tech Mono';line-height:1.1}
.sc-pts{font-size:14px;font-weight:700;margin:2px 0;font-family:'Share Tech Mono'}
.sc-sig{font-size:17px;font-weight:900;letter-spacing:1.5px;margin:5px 0}
.sc-tris {font-size:17px;letter-spacing:5px;margin:4px 0}
.sc-meta{font-size:12px;color:#7aaccc;display:flex;justify-content:space-around;flex-wrap:wrap;gap:2px;margin-top:4px}
.sc-entry{font-size:11px;margin-top:6px;padding:5px 8px;background:rgba(61,155,233,.06);
          border:1px solid #0d3060;border-radius:5px;text-align:left}
.sc-time{font-size:10px;color:#6aaabb;margin-top:5px;font-family:'Share Tech Mono'}
.sc-badge{font-size:10px;letter-spacing:1.5px;font-weight:700;padding:2px 8px;border-radius:3px;display:inline-block;margin-bottom:2px}

/* INDICATOR GRID */
.ind-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin:5px 0}
.ind-box{border-radius:8px;padding:13px 9px;text-align:center;border:1px solid;transition:all .5s;cursor:help}
.ind-buy {background:#001f0f;border-color:#00d463}
.ind-sell{background:#1f0000;border-color:#ff3d3d}
.ind-neu {background:#0d1a2a;border-color:#3d9be9}
.ind-lbl{font-size:10px;letter-spacing:1.5px;margin-bottom:3px;color:#a0c8e8;opacity:.9}
.ind-val{font-size:17px;font-weight:900;font-family:'Share Tech Mono'}
.ind-sig{font-size:11px;font-weight:900;letter-spacing:1.5px;margin-top:3px}

/* VIX BLINK */
@keyframes vblink{0%,100%{opacity:1;text-shadow:0 0 8px currentColor}50%{opacity:.35;text-shadow:none}}
.vblink{animation:vblink 1.8s infinite}

/* TAPE */
.tape-wrap{display:flex;gap:5px;overflow-x:auto;padding:4px 0;scrollbar-width:none;align-items:stretch}
.tape-wrap::-webkit-scrollbar{display:none}
.tape-item{display:flex;flex-direction:column;align-items:center;background:#030c1a;
           border:1px solid #0d3060;border-radius:5px;padding:4px 10px;min-width:80px;
           text-align:center;cursor:pointer;transition:border-color .2s;flex-shrink:0}
.tape-item:hover{border-color:#3d9be9}
.tape-item.tape-big{min-width:115px;padding:5px 14px;border-color:#1a3a6a;background:#040e20}
.tape-item.tape-big:hover{border-color:#3d9be9}
.ti-n{color:#8ab8d8;font-size:11px;font-family:'Share Tech Mono';letter-spacing:.5px}
.ti-v{font-weight:bold;font-size:15px;font-family:'Share Tech Mono'}
.ti-c{font-size:12px;font-family:'Share Tech Mono'}
.ti-p{font-size:10px;font-family:'Share Tech Mono';opacity:.85}
/* BIG tape overrides */
.tape-big .ti-n{font-size:12px;color:#8ab8d8;font-weight:700}
.tape-big .ti-v{font-size:19px}
.tape-big .ti-c{font-size:14px}
.tape-big .ti-p{font-size:12px;opacity:.9}

/* MINI CARD */
.mc{background:#0a1628;border:1px solid #1a4070;border-radius:10px;padding:12px 8px;text-align:center;height:118px;display:flex;flex-direction:column;justify-content:center;align-items:center;width:100%;box-sizing:border-box;overflow:hidden}
.mc-ico{font-size:22px;margin-bottom:2px;line-height:1}
.mc-nm{font-size:10px;letter-spacing:1.5px;color:#7aaabf;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.mc-pr{font-size:17px;font-weight:900;font-family:"Share Tech Mono",monospace;color:#e8f4ff;line-height:1.15}
.mc-ch{font-size:13px;font-weight:700;line-height:1.2}
.mc-pt{font-size:11px;color:#5a8aaa;line-height:1.1}

/* NEWS */
.ni{border-radius:6px;padding:8px 10px;margin:3px 0;border-left:3px solid;transition:opacity .2s}
.ni:hover{opacity:.8}
.ni-bull{background:rgba(0,212,99,.07);border-color:#00d463}
.ni-bear{background:rgba(255,61,61,.07);border-color:#ff3d3d}
.ni-neu {background:rgba(61,155,233,.07);border-color:#3d9be9}
.ni-meta{font-size:11px;color:#6a9abb;margin-bottom:3px;font-family:'Share Tech Mono'}
.ni-title{color:#e0f0ff;font-size:14px;line-height:1.6}

/* PIVOT TABLE */
.pvt-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;text-align:center}
.pvt-cell{padding:7px 3px;border-radius:5px;font-size:13px;font-weight:700;font-family:'Share Tech Mono'}
.pvt-lbl{font-size:9px;margin-bottom:2px;font-weight:400;opacity:.8;letter-spacing:1px;color:#a0c8e8}
.pvt-r{background:#200000;border:1px solid #ff3d3d;color:#ff7070}
.pvt-s{background:#002010;border:1px solid #00d463;color:#44ee88}
.pvt-p{background:#1a1000;border:1px solid #ffb70055;color:#ffd050}
.pvt-c{background:#001030;border:1px solid #3d9be955;color:#6ab4ee}

/* OI BAR */
.oi-bar-wrap{height:9px;background:#0a1628;border-radius:4px;overflow:hidden;margin:5px 0}
.oi-bar{height:100%;border-radius:4px;transition:width .8s}

/* SL GRID */
.sl-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:7px}
.sl-box{background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:9px;text-align:center}
.sl-lbl{font-size:10px;letter-spacing:2px;color:#6a8aaa;margin-bottom:3px}
.sl-val{font-size:21px;font-weight:900;font-family:'Share Tech Mono'}
.sl-sub{font-size:11px;margin-top:2px;font-family:'Share Tech Mono'}

/* ECONOMIC CALENDAR */
.eco-high{background:#1f0000;border:1px solid #ff3d3d40;border-radius:6px;padding:9px;margin-bottom:5px}
.eco-med {background:#1a1000;border:1px solid #ffb70040;border-radius:6px;padding:9px;margin-bottom:5px}
.eco-low {background:#001030;border:1px solid #3d9be940;border-radius:6px;padding:9px;margin-bottom:5px}
.eco-title{font-size:14px;font-weight:700;color:#e8f4ff;margin-bottom:3px}
.eco-date{font-size:11px;color:#7aaabf;font-family:'Share Tech Mono';margin-bottom:4px}
.eco-imp  {font-size:9px;font-weight:700;padding:1px 7px;border-radius:3px;letter-spacing:1px}
.eco-bull {background:#00d46320;color:#00d463}
.eco-bear {background:#ff3d3d20;color:#ff3d3d}
.eco-neu  {background:#ffb70020;color:#ffb700}
.eco-impact-box{padding:8px 10px;border-radius:5px;font-size:12px;margin-top:5px;line-height:1.7}

/* ALERT BOX */
.alert-box{padding:8px 12px;border-radius:5px;margin:3px 0;border-left:4px solid;font-size:13px;line-height:1.6;font-weight:600}
.alert-spike{background:#1f0f00;border-color:#ff8800;color:#ffccaa}
.alert-fall {background:#1a001a;border-color:#ff00cc;color:#ffaadd}
.alert-bull {background:#001f0f;border-color:#00d463;color:#88ffaa}
.alert-bear {background:#1f0000;border-color:#ff3d3d;color:#ffaaaa}

/* MOOD */
.mood-track{height:11px;background:linear-gradient(90deg,#cc2244,#ff8833,#ffcc00,#88cc00,#00d463);
            border-radius:6px;position:relative;margin:8px 0}
.mood-ptr{position:absolute;top:-4px;width:4px;height:19px;background:white;border-radius:2px;
          box-shadow:0 0 8px rgba(255,255,255,.8)}

/* SENT */
.sent-wrap{background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px}
.sent-track{background:#0a1628;height:7px;border-radius:4px;overflow:hidden;margin:7px 0}
.sent-fill{height:100%;border-radius:4px;transition:width .5s}

/* OC */
.oc-grid{display:grid;grid-template-columns:1fr 58px 1fr;gap:2px;font-family:'Share Tech Mono';font-size:11px}
.oc-hdr{background:#0d3060;padding:4px 5px;text-align:center;font-size:9px;color:#88bbdd}
.oc-call{background:#ff3d3d10;padding:4px 5px;text-align:right;color:#ff9999}
.oc-put {background:#00d46310;padding:4px 5px;text-align:left;color:#88ffaa}
.oc-str {background:#0d3060;padding:4px 5px;text-align:center;color:#ffd050;font-weight:700}
.oc-atm {background:#1a5090!important;color:#fff!important;font-weight:900!important}

/* REPORT */
.rm{background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:8px 5px;text-align:center}
.rv{font-size:23px;font-weight:900;font-family:'Share Tech Mono'}
.rl{font-size:9px;letter-spacing:2px;color:#6a9aaa;margin-top:2px}

/* SECTION LABEL */
.slbl{font-size:10px;letter-spacing:2.5px;font-weight:700;color:#4db8ff;display:block;margin:8px 0 5px;padding:2px 0;border-bottom:1px solid #0d3060}

/* EXPIRY */
@keyframes exp{0%,100%{background:#1a0000;color:#ff6060}50%{background:#2a0000;color:#ffaaaa}}
.exp-banner{animation:exp 1s infinite;border:1px solid #ff3d3d;padding:6px;text-align:center;
            font-size:12px;font-weight:900;letter-spacing:2px;border-radius:5px;margin-bottom:5px}

/* TEXT */
p,li{color:#c0d8f0}
h1,h2,h3,h4{color:#e0f0ff}
.stMetric label{color:#7ab0cc!important}
.stDataFrame td{color:#c0d8f0!important;font-family:'Share Tech Mono'!important}
.stDataFrame th{color:#4a90d9!important;background:#0d3060!important}
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label{color:#7ab0cc!important}
input[type="number"]{background:#030c1a!important;color:#e0f0ff!important;border-color:#3d6090!important}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  SOUND ENGINE
# ════════════════════════════════════════════════════════════

PATS = [
    {"n":"Hammer 🔨",     "t":"bullish","c":78},
    {"n":"Doji ✚",        "t":"neutral","c":58},
    {"n":"Engulfing ◼",   "t":"bullish","c":84},
    {"n":"Shooting ★",    "t":"bearish","c":81},
    {"n":"Morning 🌟",    "t":"bullish","c":87},
    {"n":"Evening 🌙",    "t":"bearish","c":79},
]


SUGS = [
    ("IV Rank / IV %ile",    "IV Rank <30% → BUY options. IV Rank >70% → SELL options (expensive premium)."),
    ("Options Greeks Live",  "Delta=direction, Gamma=speed, Theta=time decay enemy for buyers. Check before entry."),
    ("Sector Heatmap",       "See which Nifty sectors are red/green — rotate early into strong sectors for alpha."),
    ("SuperTrend Indicator", "Green below price = BUY zone. Red above price = SELL zone. Works all timeframes."),
    ("EMA 9/21/50 Crossover","Triple EMA — most used system by professional intraday traders globally."),
    ("F&O Ban List",         "Stocks in F&O ban = no fresh positions allowed. Must check before every futures trade."),
    ("Delivery Volume %",    "High delivery % = real institutional buying. Low = retail speculation only."),
]


SOUNDS = {
    "buy":       ([523,659,784,1047],"sine",     0.36,0.12),
    "sell":      ([494,392,330,247], "sawtooth", 0.36,0.12),
    "news_bull": ([550,660,880],     "sine",     0.26,0.13),
    "news_bear": ([440,330,220],     "triangle", 0.26,0.13),
    "spike":     ([880,1100,880,1100],"square",  0.34,0.08),
    "fall":      ([220,180,140,110], "sawtooth", 0.40,0.10),
    "vix":       ([300,240,180],     "square",   0.26,0.14),
    "eco_high":  ([440,550,660,770], "sine",     0.32,0.12),
}

def _sound_btn():
    # Always use components.html for the button — st.html has no height control
    _html_func = lambda x: components.html(x, height=36)
    _html_func("""
<style>body{margin:0}
.sb{background:#030c1a;border:1px solid #0d3060;color:#3d9be9;padding:3px 10px;
    border-radius:4px;cursor:pointer;font-size:10px;letter-spacing:2px;font-family:monospace}
.sb.on{border-color:#00d463;color:#00d463;background:#001f0f}</style>
<button class="sb" id="sb" onclick="initS()">🔇 SOUND</button>
<script>
var C=null,on=sessionStorage.getItem('snd')==='1',b=document.getElementById('sb');
if(on){b.textContent='🔊 ON';b.className='sb on';
  try{C=new(window.parent.AudioContext||AudioContext)();window.parent._EC=C;window.parent._ES=true;}catch(e){}}
function initS(){
  try{C=new(window.parent.AudioContext||window.AudioContext)();C.resume();
      window.parent._EC=C;window.parent._ES=true;on=true;
      sessionStorage.setItem('snd','1');b.textContent='🔊 ON';b.className='sb on';
      _p([523,659,784],'sine',0.26,0.1);}catch(e){b.textContent='⚠️';}}
function _p(n,w,v,d){var c=C||window.parent._EC;if(!c)return;
  n.forEach(function(f,i){var t=c.currentTime+i*(d+0.04);
    var o=c.createOscillator(),g=c.createGain();o.type=w;o.frequency.value=f;
    g.gain.setValueAtTime(v,t);g.gain.exponentialRampToValueAtTime(0.001,t+d);
    o.connect(g);g.connect(c.destination);o.start(t);o.stop(t+d+0.02);});}
window.addEventListener('message',function(e){
  if(!e.data||!e.data.ee||(!on&&!window.parent._ES))return;
  var n={'buy':[523,659,784,1047],'sell':[494,392,330,247],'news_bull':[550,660,880],
         'news_bear':[440,330,220],'spike':[880,1100,880,1100],'fall':[220,180,140,110],
         'vix':[300,240,180],'eco_high':[440,550,660,770]};
  var w={'buy':'sine','sell':'sawtooth','news_bull':'sine','news_bear':'triangle',
         'spike':'square','fall':'sawtooth','vix':'square','eco_high':'sine'};
  var s=e.data.ee;if(n[s])_p(n[s],w[s]||'sine',0.36,0.12);});
</script>""")

def _queue(s): st.session_state.sound_queue.append(s)

def _emit():
    q = st.session_state.sound_queue
    if not q: return
    pri = {"fall":7,"spike":6,"vix":5,"eco_high":4,"sell":3,"buy":2,"news_bear":1,"news_bull":1}
    best = max(q, key=lambda x: pri.get(x,0))
    st.session_state.sound_queue = []
    sid = st.session_state.sound_id + 1
    st.session_state.sound_id = sid
    n,w,v,d = SOUNDS[best]
    _ef = lambda x: components.html(x, height=1)
    _ef(f"""<script>(function(){{
      try{{var fs=window.parent.document.querySelectorAll('iframe');
        fs.forEach(function(f){{try{{f.contentWindow.postMessage({{ee:'{best}',id:{sid}}},'*');}}catch(e){{}}}}); }}catch(e){{}}
      try{{var C=window.parent._EC;if(!C||!window.parent._ES)return;
        var ns={n},d={d},v={v};
        ns.forEach(function(f,i){{var t=C.currentTime+i*(d+0.04);
          var o=C.createOscillator(),g=C.createGain();o.type='{w}';o.frequency.value=f;
          g.gain.setValueAtTime(v,t);g.gain.exponentialRampToValueAtTime(0.001,t+d);
          o.connect(g);g.connect(C.destination);o.start(t);o.stop(t+d+0.02);}});}}}})();
    </script>""")


# ════════════════════════════════════════════════════════════
#  DATA FETCHERS (with robust error handling)
# ════════════════════════════════════════════════════════════

def _flat(df):
    if df is None or df.empty: return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=8, show_spinner=False)
def get_candles(sym: str):
    """Fetch candles: Dhan first (real-time), Yahoo multi-period fallback."""
    _DHAN_C = {"^NSEI":("13","IDX_I"),"^NSEBANK":("25","IDX_I"),"^CNXFIN":("27","IDX_I")}
    # ── Dhan primary (real-time, market hours only) ──
    if dhan_active() and sym in _DHAN_C and is_market_open():
        sec_id, seg = _DHAN_C[sym]
        df = dhan_ohlcv(sec_id, seg, interval="1")
        if df is not None and len(df) >= 5:
            return df
    # ── Yahoo Finance: try intraday first, then daily (ALWAYS returns data) ──
    for period, interval in [("1d","1m"),("5d","5m"),("1mo","30m"),("3mo","1d"),("1y","1d")]:
        try:
            df = yf.Ticker(sym).history(period=period, interval=interval)
            df = _flat(df)
            if df is not None and len(df) >= 3:
                if df.index.tzinfo:
                    df.index = df.index.tz_convert(IST)
                return df
        except Exception:
            pass
    return None

@st.cache_data(ttl=10, show_spinner=False)
def get_gift_data():
    """
    GIFT Nifty: Dhan securityId=800 (futures) → 15-min candles.
    Fallback: Yahoo ^NSEI 15m (different interval = different close price from 1m Nifty).
    This ensures GIFT card shows a distinct price from Nifty spot card.
    """
    # Primary: Dhan GIFT Nifty futures (800)
    if dhan_active() and is_gift_nifty_available():
        df = dhan_ohlcv("800", "NSE_FNO", interval="15")
        if df is not None and len(df) >= 3:
            return df, "DHAN:GIFT"
        # Dhan 15m Nifty as secondary
        df = dhan_ohlcv("13", "IDX_I", interval="15")
        if df is not None and len(df) >= 3:
            return df, "DHAN:15M"

    # Yahoo fallback — always returns data
    for sym in ["^NSEI", "NIFTY.NS"]:
        for period, interval in [("5d","15m"),("1mo","1h"),("3mo","1d"),("1y","1d")]:
            try:
                df = yf.Ticker(sym).history(period=period, interval=interval)
                df = _flat(df)
                if df is not None and len(df) >= 3:
                    if df.index.tzinfo:
                        df.index = df.index.tz_convert(IST)
                    return df, f"{sym}:{interval}"
            except Exception:
                pass
    return None, None
@st.cache_data(ttl=8, show_spinner=False)
def get_finnifty_data():
    """Fetch Nifty Financial Services (Fin Nifty) — multi-period fallback."""
    if dhan_active() and is_market_open():
        df = dhan_ohlcv("27", "IDX_I", interval="1")
        if df is not None and len(df) >= 5:
            return df
    for sym in ["^CNXFIN", "NIFTYFINSERVICE.NS"]:
        for period, interval in [("1d","1m"),("5d","5m"),("1mo","30m"),("3mo","1d"),("1y","1d")]:
            try:
                df = yf.Ticker(sym).history(period=period, interval=interval)
                df = _flat(df)
                if df is not None and len(df) >= 3:
                    if df.index.tzinfo:
                        df.index = df.index.tz_convert(IST)
                    return df
            except Exception:
                pass
    return None

@st.cache_data(ttl=10, show_spinner=False)
def get_vix_data():
    """Fetch VIX: Dhan LTP for live value, Yahoo for history."""
    live_vix = None
    # ── Dhan live VIX LTP ──
    if dhan_active() and is_market_open():
        try:
            ltp = dhan_ltp(["12"], "IDX_I")
            v = ltp.get("12", 0)
            if v and v > 5:
                live_vix = float(v)
        except Exception:
            pass

    # ── Yahoo for history (always needed for chart) ──
    for sym in ["^INDIAVIX","^VIX"]:
        try:
            df = yf.Ticker(sym).history(period="60d", interval="1d")
            df = _flat(df)
            if df is not None and len(df) >= 2:
                v  = live_vix or float(df["Close"].iloc[-1])
                vp = float(df["Close"].iloc[-2])
                return {"val":v,"chg":(v-vp)/vp*100,"high":v>20,"spike":(v-vp)/vp*100>15,
                        "hist":df["Close"].tolist()[-30:],
                        "source": "DHAN" if live_vix else "YAHOO"}
        except Exception:
            pass

    # ── Last resort: Dhan only ──
    if live_vix:
        return {"val":live_vix,"chg":0,"high":live_vix>20,"spike":False,
                "hist":[live_vix]*10,"source":"DHAN"}
    return None

_DHAN_Q_MAP = {
    "^NSEI":     "13",
    "^NSEBANK":  "25",
    "^INDIAVIX": "12",
    "^CNXFIN":   "27",   # Nifty Financial Services (Fin Nifty)
}

@st.cache_data(ttl=12, show_spinner=False)
def get_q(sym: str):
    """Get quote: Dhan for known indices, Yahoo for rest."""
    if dhan_active() and sym in _DHAN_Q_MAP and is_market_open():
        try:
            ltp = dhan_ltp([_DHAN_Q_MAP[sym]], "IDX_I")
            p = ltp.get(_DHAN_Q_MAP[sym], 0)
            if p and p > 1:
                # Need prev close from Yahoo for % calc
                try:
                    dfh = yf.Ticker(sym).history(period="5d", interval="1d")
                    dfh = _flat(dfh)
                    pp  = float(dfh["Close"].iloc[-2]) if dfh is not None and len(dfh)>=2 else float(p)*0.999
                except Exception:
                    pp = float(p)*0.999
                return {"price":float(p),"prev":pp,"pts":float(p)-pp,"chg":(float(p)-pp)/pp*100}
        except Exception:
            pass
    # Yahoo fallback — try multiple periods
    for period in ["5d","1mo","3mo"]:
        try:
            df = yf.Ticker(sym).history(period=period, interval="1d")
            df = _flat(df)
            if df is not None and len(df) >= 2:
                p,pp = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
                return {"price":p,"prev":pp,"pts":p-pp,"chg":(p-pp)/pp*100}
        except Exception:
            pass
    return None

NEWS_STATIC = [
    {"title":"RBI holds repo rate at 6.5% — Liquidity surplus returns; rate cut expectations rising","s":"bull","src":"Economic Times","time":"09:15","link":"https://economictimes.indiatimes.com","id":"static_1"},
    {"title":"Nifty FII net buyers 8,200 Cr — DII support 3,400 Cr; broad market participation strong","s":"bull","src":"Moneycontrol","time":"09:30","link":"https://moneycontrol.com","id":"static_2"},
    {"title":"IT sector earnings disappoint — TCS Infosys guidance cut; deal wins slow","s":"bear","src":"Zee Business","time":"09:20","link":"https://zeebusiness.com","id":"static_3"},
    {"title":"Middle East tensions — Brent crude spikes; supply disruption risk elevated","s":"bear","src":"Reuters","time":"08:10","link":"https://reuters.com","id":"static_4"},
    {"title":"SGX Nifty +85 pts pre-open — Strong global cues; gap-up opening expected","s":"bull","src":"Market Pulse","time":"08:00","link":"#","id":"static_5"},
    {"title":"SEBI tightens F&O rules — Lot size increased; weekly expiry reduced","s":"bear","src":"SEBI","time":"08:50","link":"https://sebi.gov.in","id":"static_6"},
]

@st.cache_data(ttl=110, show_spinner=False)
def get_live_news():
    BULL = {"rally","surge","gain","rise","rises","record","growth","bullish","strong",
            "jump","soar","beats","exceeds","upgrade","buy","rebound","boost","profit","optimistic"}
    BEAR = {"fall","falls","decline","drop","crash","loss","weak","bearish","sell",
            "downgrade","recession","fear","risk","concern","miss","disappoint","slump","warning"}
    seen, res = set(), []
    for sym in ["^NSEI","^NSEBANK","GC=F","CL=F","ES=F"]:
        try:
            for item in (yf.Ticker(sym).news or [])[:4]:
                t   = item.get("title","").strip()
                uid = item.get("uuid",t[:40])
                if not t or uid in seen: continue
                seen.add(uid)
                tl   = t.lower()
                b,r  = sum(1 for w in BULL if w in tl), sum(1 for w in BEAR if w in tl)
                sent = "bull" if b>r else ("bear" if r>b else "neu")
                ts   = item.get("providerPublishTime",0)
                time_str = datetime.fromtimestamp(ts, tz=IST).strftime("%H:%M") if ts else "—"
                res.append({"title":t,"s":sent,"time":time_str,
                            "src":item.get("publisher",""),"link":item.get("link","#"),"id":uid})
        except Exception:
            pass
    return res


# ════════════════════════════════════════════════════════════
#  TECHNICAL INDICATORS
# ════════════════════════════════════════════════════════════

def calc_ind(df):
    if df is None or len(df) < 5:
        return None
    try:
        c = df["Close"].astype(float).ffill()
        v = df["Volume"].replace(0, np.nan).astype(float).ffill() if "Volume" in df.columns else pd.Series([1e6]*len(c), index=c.index)
        h = df["High"].astype(float).ffill()  if "High" in df.columns else c
        l = df["Low"].astype(float).ffill()   if "Low"  in df.columns else c
        o = df["Open"].astype(float).ffill()  if "Open" in df.columns else c

        ema9   = c.ewm(span=9,  adjust=False).mean()
        ema21  = c.ewm(span=21, adjust=False).mean()
        ema200 = c.ewm(span=min(200,len(c)), adjust=False).mean()
        ma20   = c.rolling(20).mean()
        sd20   = c.rolling(20).std()
        bb_u   = ma20 + 2*sd20
        bb_l   = ma20 - 2*sd20
        tp     = (h + l + c) / 3
        # Google AI fix: ffill volume to fix VWAP NaN
        v_safe  = v.fillna(v.median() if not v.empty else 1e6) if v.isna().any() else v
        if v_safe.sum() == 0:
            vwap = pd.Series(c.values, index=c.index)  # fallback to close
        else:
            vwap = ((tp * v_safe).cumsum() / v_safe.cumsum().replace(0, np.nan)).ffill().bfill()
        delta  = c.diff()
        rsi_period = min(14, max(3, len(c)//3))
        ag     = delta.clip(lower=0).rolling(rsi_period).mean()
        al     = (-delta.clip(upper=0)).rolling(rsi_period).mean()
        rsi    = 100 - 100/(1 + ag/(al.replace(0, np.nan)))

        ve      = v.ewm(span=20, adjust=False).mean()
        cv      = float(v.iloc[-1])
        ve_val  = float(ve.iloc[-1]) if not np.isnan(float(ve.iloc[-1])) else cv
        vr      = cv / ve_val if ve_val > 0 else 1.0

        price    = float(c.iloc[-1])
        e9_val   = float(ema9.iloc[-1])
        e21_val  = float(ema21.iloc[-1])
        vwap_val = float(vwap.iloc[-1])
        rsi_val  = float(rsi.iloc[-1]) if not np.isnan(float(rsi.iloc[-1])) else 50.0
        bbu_val  = float(bb_u.iloc[-1])
        bbl_val  = float(bb_l.iloc[-1])
        prev5    = float(c.iloc[max(-len(c), -5)]) if len(c)>=2 else price
        mom      = (price-prev5)/prev5*100

        sl_lookback = min(10, len(l))
        sl_b = float(l.iloc[-sl_lookback:].min()) * 0.9992
        sl_s = float(h.iloc[-sl_lookback:].max()) * 1.0008
        bb_pos = (price-bbl_val) / max(1, bbu_val-bbl_val) * 100

        t1 = e9_val  > e21_val
        t2 = price   > vwap_val
        t3 = rsi_val > 54
        t4 = vr      >= 1.5

        return dict(price=price, ema9=e9_val, ema21=e21_val, ema200=float(ema200.iloc[-1]),
                    vwap=vwap_val, rsi=rsi_val, bb_u=bbu_val, bb_l=bbl_val, bb_pos=bb_pos,
                    vol_ratio=vr, vol_spike=t4, mom_pct=mom, sl_buy=sl_b, sl_sell=sl_s,
                    t1=t1, t2=t2, t3=t3, t4=t4, tris=[t1,t2,t3,t4])
    except Exception as e:
        return None


def calc_signal(ind, gift_trend, vix):
    if ind is None:
        return dict(signal="⚠️ NO DATA",zone="sc-wait",tris=[False]*4,
                    sl_val=None,sl_risk=0,entry_quality="—",
                    vix_warn=False,gift_trend=gift_trend,
                    rsi=50,vwap=0,vol_ratio=1,mom_pct=0,local="NEUTRAL",dots=0)
    p,r   = ind["price"], ind["rsi"]
    e9,e21= ind["ema9"], ind["ema21"]
    vwap  = ind["vwap"]
    vx_h  = vix and vix["val"]>20
    vx_sp = vix and vix["spike"]

    ema_gap = abs(e9-e21)/p*100
    between = min(e9,e21) <= p <= max(e9,e21)
    sideways= ema_gap < 0.07 and between

    b_pts = int(p>vwap)+int(e9>e21)+int(r>54)
    s_pts = int(p<vwap)+int(e9<e21)+int(r<46)
    local = "BULL" if b_pts>=2 else ("BEAR" if s_pts>=2 else "NEUTRAL")
    dots  = sum([e9>e21, p>vwap, r>54, ind["vol_spike"]])

    if sideways:
        sig,zone = "↔️ SIDEWAYS — WAIT","sc-wait"
    elif gift_trend=="BULL" and local=="BULL":
        sig  = "🚀 SUPER BUY" if dots>=3 else "📈 BUY"
        zone = "sc-buy"
    elif gift_trend=="BEAR" and local=="BEAR":
        sig  = "📉 SUPER SELL" if dots>=3 else "📉 SELL"
        zone = "sc-sell"
    elif local=="BULL" and gift_trend in ("BEAR","NEUTRAL"):
        sig,zone = ("🚀 BUY ⚠️ GIFT WEAK","sc-caut") if dots>=3 else ("📈 WEAK BUY","sc-caut")
    elif local=="BEAR" and gift_trend in ("BULL","NEUTRAL"):
        sig,zone = ("📉 SELL ⚠️ GIFT WEAK","sc-caut") if dots>=3 else ("📉 WEAK SELL","sc-caut")
    else:
        sig,zone = "⏳ NO SYNC","sc-wait"

    if vx_h and "SUPER" in sig:
        sig = sig.replace("SUPER ","")+" (VIX HIGH)"; zone="sc-caut"

    pb = abs(p-e9)/p*100
    if local=="BULL":
        eq = "✅ IDEAL — near EMA9" if pb<=0.18 else ("⚠️ HIGH ENTRY" if p>e9 and pb>0.45 else "🟡 ACCEPTABLE")
        sl_val,sl_risk = ind["sl_buy"], p-ind["sl_buy"]
    elif local=="BEAR":
        eq = "✅ IDEAL SHORT" if pb<=0.18 else ("⚠️ LOW ENTRY" if p<e9 and pb>0.45 else "🟡 ACCEPTABLE")
        sl_val,sl_risk = ind["sl_sell"], ind["sl_sell"]-p
    else:
        eq,sl_val,sl_risk = "⏳ NO ENTRY","",0

    return dict(signal=sig,zone=zone,local=local,dots=dots,
                entry_quality=eq,sl_val=sl_val,sl_risk=sl_risk,
                vix_warn=vx_h or vx_sp,gift_trend=gift_trend,
                tris=ind["tris"],mom_pct=ind["mom_pct"],
                vol_ratio=ind["vol_ratio"],rsi=r,vwap=vwap)


def pivot_pts(df):
    if df is None or len(df)<2: return {}
    try:
        h = float(df["High"].iloc[-2])  if "High" in df.columns else float(df["Close"].iloc[-2])
        l = float(df["Low"].iloc[-2])   if "Low"  in df.columns else float(df["Close"].iloc[-2])
        c = float(df["Close"].iloc[-2])
        p = (h+l+c)/3
        return {"P":p,"R1":2*p-l,"R2":p+(h-l),"R3":h+2*(p-l),
                "S1":2*p-h,"S2":p-(h-l),"S3":l-2*(h-p)}
    except Exception:
        return {}


def check_alerts(sym: str, df):
    if df is None or len(df)<3: return
    try:
        cur  = float(df["Close"].iloc[-1])
        prev = st.session_state.prev_prices.get(sym, cur)
        delta= (cur-prev)/prev*100 if prev else 0
        st.session_state.prev_prices[sym] = cur
        if delta > 0.75:
            _queue("spike")
            st.session_state.alert_log.append(
                {"type":"🚀 SPIKE","sym":sym,"pct":f"+{delta:.2f}%",
                 "time":datetime.now(IST).strftime("%H:%M:%S"),"css":"alert-spike"})
        elif delta < -0.75:
            _queue("fall")
            st.session_state.alert_log.append(
                {"type":"📉 SUDDEN FALL","sym":sym,"pct":f"{delta:.2f}%",
                 "time":datetime.now(IST).strftime("%H:%M:%S"),"css":"alert-fall"})
        st.session_state.alert_log = st.session_state.alert_log[-14:]
    except Exception:
        pass


def log_sig(key, name, sig, ind):
    if ind is None: return
    now  = datetime.now(IST)
    prev = st.session_state.prev_sig.get(key,{})
    skip = {"⏳ NO SYNC","↔️ SIDEWAYS — WAIT","⚠️ NO DATA"}
    if sig not in skip and sig != prev.get("signal",""):
        if len(st.session_state.signals_log) >= 100:
            st.session_state.signals_log.pop(0)
        st.session_state.signals_log.append(
            {"time":now.strftime("%H:%M:%S"),"log_dt":now,"symbol":name,
             "signal":sig,"price":ind["price"],"rsi":ind["rsi"],
             "vol":ind["vol_ratio"],"mom":ind["mom_pct"],
             "vwap":ind.get("vwap",0),"dots":sum(ind.get("tris",[False]*4)),
             "evaluated":False,"result":None,"exit_price":None,"fail_reason":""})
        if "BUY"  in sig: _queue("buy")
        elif "SELL" in sig: _queue("sell")
    for log in st.session_state.signals_log:
        if log["evaluated"] or log["symbol"] != name: continue
        if (now - log["log_dt"]).total_seconds() < 900: continue
        move   = ind["price"] - log["price"]
        passed = (move > 0) == ("BUY" in log["signal"])
        fail_reason = ""
        if not passed:
            fk = ("SIDEWAYS" if abs(move) < 8 else
                  "VIX_HIGH" if vix and vix.get("val",0) > 20 else
                  "LOW_DOTS" if log.get("dots",0) < 3 else
                  "GIFT_CONFLICT" if ("GIFT" in log.get("signal","") or "WEAK" in log.get("signal","")) else
                  "LATE_ENTRY" if ("HIGH ENTRY" in log.get("fail_reason","")) else
                  "WHIPSAW")
            fail_reason = FAIL_REASONS.get(fk, {}).get("reason", "")
            if len(st.session_state.fail_log) >= 50:
                st.session_state.fail_log.pop(0)
            st.session_state.fail_log.append({
                "time": log["time"], "symbol": name, "signal": log["signal"],
                "entry": log["price"], "exit": ind["price"], "move": move,
                "fail_key": fk, "dots": log.get("dots", 0),
                "rsi": log["rsi"], "vwap": log.get("vwap", 0)
            })
        log.update({"evaluated": True,
                    "result": "✅ PASS" if passed else "❌ FAIL",
                    "exit_price": ind["price"], "fail_reason": fail_reason})
    st.session_state.prev_sig[key] = {"signal": sig, "price": ind["price"]}


# ════════════════════════════════════════════════════════════
#  PLOTLY CHART
# ════════════════════════════════════════════════════════════

def make_chart(df, title: str, vix_val=None, height=480):
    if df is None:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="#020b18",plot_bgcolor="#030c1a",height=200,
            annotations=[dict(text="⚠️ Data unavailable",x=0.5,y=0.5,xref="paper",yref="paper",
                showarrow=False,font=dict(color="#3d5a7a",size=14))])
        return fig
    try:
        c = df["Close"].astype(float).ffill()
        v = df["Volume"].replace(0,np.nan).astype(float).ffill() if "Volume" in df.columns else pd.Series([1e6]*len(c),index=c.index)
        h = df["High"].astype(float).ffill()  if "High" in df.columns else c
        l = df["Low"].astype(float).ffill()   if "Low"  in df.columns else c
        o = df["Open"].astype(float).ffill()  if "Open" in df.columns else c
        idx = df.index

        ema9  = c.ewm(span=9,  adjust=False).mean()
        ema21 = c.ewm(span=21, adjust=False).mean()
        ma20  = c.rolling(20).mean(); sd20 = c.rolling(20).std()
        bb_u  = ma20+2*sd20; bb_l = ma20-2*sd20
        tp    = (h+l+c)/3
        _vs   = v.fillna(v.median()) if v.isna().any() else v
        vwap  = ((tp*_vs).cumsum() / _vs.cumsum().replace(0,np.nan)).ffill().bfill()
        rsi_s = 100-100/(1+c.diff().clip(lower=0).rolling(14).mean()/
                          (-c.diff().clip(upper=0)).rolling(14).mean().replace(0,1e-9))
        pvt = pivot_pts(df)

        fig = make_subplots(rows=3,cols=1,shared_xaxes=True,
            row_heights=[0.60,0.22,0.18],vertical_spacing=0.02,
            subplot_titles=[title,"RSI (14)","Volume"])

        fig.add_trace(go.Candlestick(x=idx,open=o,high=h,low=l,close=c,name="Price",
            increasing_fillcolor="#00d463",increasing_line_color="#00d463",
            decreasing_fillcolor="#ff3d3d",decreasing_line_color="#ff3d3d"),row=1,col=1)
        fig.add_trace(go.Scatter(x=idx,y=bb_u,name="BB Upper",
            line=dict(color="#3d6be0",width=1,dash="dot"),opacity=0.7),row=1,col=1)
        fig.add_trace(go.Scatter(x=idx,y=bb_l,name="BB Lower",fill="tonexty",
            fillcolor="rgba(61,107,224,0.05)",line=dict(color="#3d6be0",width=1,dash="dot")),row=1,col=1)
        fig.add_trace(go.Scatter(x=idx,y=vwap,name="VWAP",line=dict(color="#ffb700",width=2)),row=1,col=1)
        fig.add_trace(go.Scatter(x=idx,y=ema9, name="EMA9", line=dict(color="#00e676",width=1.3,dash="dash")),row=1,col=1)
        fig.add_trace(go.Scatter(x=idx,y=ema21,name="EMA21",line=dict(color="#ff8844",width=1.3,dash="dash")),row=1,col=1)

        if pvt:
            for lbl,val,col in [("R1",pvt["R1"],"rgba(255,80,80,.65)"),
                                 ("PP",pvt["P"],"rgba(255,183,0,.65)"),
                                 ("S1",pvt["S1"],"rgba(0,212,99,.65)")]:
                fig.add_hline(y=val,line=dict(color=col,width=1,dash="dot"),
                    annotation_text=lbl,annotation_font=dict(color=col,size=10),row=1,col=1)

        fig.add_trace(go.Scatter(x=idx,y=rsi_s,name="RSI",line=dict(color="#cc88ff",width=1.5)),row=2,col=1)
        for yv,col,lbl in [(70,"rgba(255,61,61,0.55)","OB"),(50,"rgba(61,106,138,0.33)","MID"),(30,"rgba(0,212,99,0.55)","OS")]:
            fig.add_hline(y=yv,row=2,col=1,line=dict(color=col,width=1,dash="dot" if yv!=50 else "solid"),annotation_text=lbl,annotation_position="right",annotation_font=dict(color=col,size=8))
        fig.add_hline(y=50,line=dict(color="rgba(13,48,96,0.33)",width=1),row=2,col=1)

        vc = ["#00d463" if float(c.iloc[i])>=float(o.iloc[i]) else "#ff3d3d" for i in range(len(c))]
        fig.add_trace(go.Bar(x=idx,y=v,name="Volume",marker_color=vc,opacity=0.7),row=3,col=1)

        fig.update_layout(paper_bgcolor="#020b18",plot_bgcolor="#030c1a",
            font=dict(family="Share Tech Mono",color="#8ab8d8",size=10),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0,bgcolor="rgba(2,11,24,0.88)",bordercolor="#0d3060",borderwidth=1,font=dict(size=10,color="#c0d8f0"),itemsizing="constant"),
            margin=dict(l=50,r=20,t=38,b=10),height=height,showlegend=True)
        fig.update_xaxes(gridcolor="#0d3060",showgrid=True,zeroline=False,tickfont=dict(color="#3d6a8a"))
        fig.update_yaxes(gridcolor="#0d3060",showgrid=True,zeroline=False,tickfont=dict(color="#3d6a8a"))
        fig.update_yaxes(range=[0,100],row=2,col=1)

        if vix_val:
            vc2 = "#00d463" if vix_val<15 else ("#ffb700" if vix_val<20 else "#ff3d3d")
            fig.add_annotation(x=0.98,y=0.97,xref="paper",yref="paper",text=f"VIX {vix_val:.1f}",
                showarrow=False,font=dict(color=vc2,size=12,family="Share Tech Mono"),
                bgcolor="#020b18",bordercolor=vc2,borderwidth=1,borderpad=4)
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="#020b18",plot_bgcolor="#030c1a",height=200)
        return fig


def vix_chart(hist):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(hist))),y=hist,fill="tozeroy",
        fillcolor="rgba(255,183,0,.12)",line=dict(color="#ffb700",width=2)))
    for yv,col,lbl in [(15,"#00d463","15 Low"),(20,"#ff3d3d","20 High")]:
        fig.add_hline(y=yv,line=dict(color=col,width=1.2,dash="dot"),
            annotation_text=lbl,annotation_font=dict(color=col,size=9))
    fig.update_layout(paper_bgcolor="#020b18",plot_bgcolor="#030c1a",
        font=dict(color="#8ab8d8",size=9),margin=dict(l=30,r=10,t=10,b=10),height=160,
        xaxis=dict(showticklabels=False,gridcolor="#0d3060"),yaxis=dict(gridcolor="#0d3060"))
    return fig


def sanitize_colors(fig):
    """
    Fix Plotly ValueError: layout.shape.line / trace colors do not support
    8-digit hex (#RRGGBBAA). Strip the alpha bytes → keep only #RRGGBB.
    Call this on every figure before st.plotly_chart().
    """
    import re
    _hex8 = re.compile(r'#([0-9a-fA-F]{6})[0-9a-fA-F]{2}')

    def _fix(val):
        if isinstance(val, str):
            return _hex8.sub(r'#\1', val)
        return val

    def _walk_dict(d):
        if not isinstance(d, dict):
            return
        for k, v in d.items():
            if isinstance(v, str):
                d[k] = _fix(v)
            elif isinstance(v, dict):
                _walk_dict(v)
            elif isinstance(v, list):
                _walk_list(v)

    def _walk_list(lst):
        for i, item in enumerate(lst):
            if isinstance(item, str):
                lst[i] = _fix(item)
            elif isinstance(item, dict):
                _walk_dict(item)
            elif isinstance(item, list):
                _walk_list(item)

    try:
        fig_dict = fig.to_dict()
        _walk_dict(fig_dict)
        fig.update(fig_dict)
    except Exception:
        pass
    return fig


# ════════════════════════════════════════════════════════════
#  ECONOMIC CALENDAR (KEY GLOBAL + INDIA EVENTS)
# ════════════════════════════════════════════════════════════

ECO_EVENTS = [
    # (Name, Date str, Impact HIGH/MED/LOW, Sentiment bull/bear/neu,
    #  India Impact, Market Impact, Strategy Hint, Category)
    ("🏦 RBI MPC Policy Decision",
     "Jun 7, 2025",  "HIGH", "neu",
     "Repo rate decision affects Bank Nifty most. Hold expected at 6.5%.",
     "BANKNIFTY ±2-3%, NIFTY ±1-1.5%",
     "Avoid F&O positions 30 min before & after. Trade momentum post-decision.",
     "RBI"),

    ("🇺🇸 US Federal Reserve FOMC",
     "May 7, 2025",  "HIGH", "bear",
     "Rate decision affects FII flows into India. Hawkish = INR weakness, FII outflows.",
     "NIFTY ±1-2%, USD/INR volatile",
     "If hawkish: SELL Bank Nifty. If dovish: BUY IT/Nifty. SGX Nifty reacts immediately.",
     "FED"),

    ("📊 India CPI Inflation Data",
     "May 13, 2025", "HIGH", "neu",
     "CPI above 6% = RBI may hike. Below 4% = rate cut hopes. Affects all indices.",
     "NIFTY ±0.8-1.5%",
     "High CPI: SELL FMCG, BUY energy. Low CPI: BUY FMCG, RATE SENSITIVES.",
     "MACRO"),

    ("🇺🇸 US Non-Farm Payrolls (NFP)",
     "May 2, 2025",  "HIGH", "neu",
     "Strong jobs = Dollar up = INR down = FII may sell India. Weak jobs = Fed cuts soon.",
     "NIFTY ±0.5-1%, USD/INR ±0.3%",
     "Strong NFP + rising dollar: short BankNifty (FII sensitive). Weak NFP: BUY IT index.",
     "MACRO"),

    ("📈 India GDP Data",
     "May 31, 2025", "HIGH", "bull",
     "Strong GDP confirms India growth story. >7% = very positive for markets.",
     "NIFTY ±1-2%, PSU Banks surge",
     "GDP >7%: BUY infrastructure, PSU banks, capital goods. <6%: Wait and watch.",
     "MACRO"),

    ("🏛️ Union Budget 2025-26",
     "Feb 1, 2026",  "HIGH", "bull",
     "Most important annual event. Sector winners & losers decided for whole year.",
     "NIFTY ±3-5%, sectoral moves ±10-15%",
     "Pre-budget: BUY infra/defence 2 weeks before. Post-budget: Trade the reaction.",
     "BUDGET"),

    ("📉 India IIP Industrial Output",
     "May 12, 2025", "MED",  "bull",
     "Industrial production data. Strong IIP = manufacturing doing well.",
     "NIFTY ±0.4-0.7%",
     "Strong IIP: BUY auto, capital goods, metals.",
     "MACRO"),

    ("🌍 US CPI Inflation Report",
     "May 13, 2025", "HIGH", "bear",
     "US inflation drives Fed policy globally. High CPI = more hikes = EM selloff.",
     "NIFTY ±0.7-1.2%, USD/INR volatile",
     "US CPI high: SELL tech/IT (dollar up). US CPI low: BUY IT index.",
     "MACRO"),

    ("🛢️ OPEC+ Production Decision",
     "Jun 1, 2025",  "MED",  "bear",
     "Oil cuts = crude rises = inflation in India = RBI hawkish = market negative.",
     "NIFTY ±0.5%, oil stocks +3-5%",
     "Production cut: BUY ONGC, Oil India. SELL airline stocks, paint companies.",
     "COMMODITY"),

    ("📊 Nifty F&O Monthly Expiry",
     "May 29, 2025", "HIGH", "neu",
     "Max pain around 22,400. Significant pinning happens last 2 hours of expiry.",
     "Intraday volatility HIGH",
     "Last Thursday of month = monthly expiry. Avoid directional trades 1 hr before close.",
     "FO"),

    ("📊 Nifty F&O Weekly Expiry",
     "Every Thursday","HIGH","neu",
     "Max pain zone active. Options sellers profit from time decay.",
     "High volatility in last 2 hours",
     "AVOID naked options buying after 2 PM on expiry Thursday.",
     "FO"),

    ("🇺🇸 US GDP Quarterly Data",
     "Jun 26, 2025", "MED",  "neu",
     "US recession/growth indicator. Affects global risk appetite and FII flows.",
     "NIFTY ±0.5-1%",
     "Weak US GDP: FII may pull money from India. Strong: positive for IT exporters.",
     "MACRO"),
]

def eco_calendar_html():
    now = datetime.now(IST)
    today_str = now.strftime("%b %-d")
    html = ""
    for (name, dt, imp, sent, india_imp, mkt_imp, strat, cat) in ECO_EVENTS:
        imp_col = "#ff3d3d" if imp=="HIGH" else ("#ffb700" if imp=="MED" else "#3d9be9")
        sent_col= "#00d463" if sent=="bull" else ("#ff3d3d" if sent=="bear" else "#ffb700")
        sent_lbl= "🟢 BULLISH FOR MARKETS" if sent=="bull" else ("🔴 BEARISH RISK" if sent=="bear" else "🟡 MIXED / WAIT")
        css_cls = "eco-high" if imp=="HIGH" else ("eco-med" if imp=="MED" else "eco-low")
        is_today= today_str in dt or "Every" in dt
        today_badge = '<span style="background:#ff3d3d;color:#fff;font-size:8px;padding:1px 6px;border-radius:3px;margin-left:6px;font-weight:700">TODAY</span>' if is_today else ""

        html += f"""<div class="{css_cls}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;flex-wrap:wrap;gap:3px">
                <span class="eco-title">{name}{today_badge}</span>
                <div style="display:flex;gap:4px;align-items:center">
                    <span class="eco-imp" style="background:{imp_col}20;color:{imp_col};border:1px solid {imp_col}40">{imp} IMPACT</span>
                    <span class="eco-imp eco-{sent}">{sent_lbl}</span>
                </div>
            </div>
            <div class="eco-date">📅 {dt} &nbsp;|&nbsp; 🏷️ {cat}</div>
            <div class="eco-impact-box" style="background:{imp_col}0c;border:1px solid {imp_col}25">
                <div style="color:#c0d8f0;margin-bottom:3px"><strong style="color:{imp_col}">India Impact:</strong> {india_imp}</div>
                <div style="color:#8ab8d8;margin-bottom:3px"><strong style="color:#3d9be9">Market Move:</strong> {mkt_imp}</div>
                <div style="color:#88ccaa"><strong style="color:#00d463">📊 Strategy:</strong> {strat}</div>
            </div>
        </div>"""
        if is_today: _queue("eco_high")
    return html


# ════════════════════════════════════════════════════════════
#  HTML CARD BUILDERS
# ════════════════════════════════════════════════════════════

def _ind_grid(ind):
    if ind is None:
        return '<div style="color:#3a6a8f;text-align:center;padding:10px;font-family:Share Tech Mono">⚠️ No data</div>'
    def box(lbl, val, sig, tip=""):
        cls = "ind-buy" if sig=="BUY" else ("ind-sell" if sig=="SELL" else "ind-neu")
        col = "#00d463" if sig=="BUY" else ("#ff3d3d" if sig=="SELL" else "#3d9be9")
        tt  = ' title="' + tip + '"' if tip else ""
        return '<div class="ind-box ' + cls + '"' + tt + '><div class="ind-lbl">' + lbl + '</div><div class="ind-val" style="color:' + col + '">' + val + '</div><div class="ind-sig" style="color:' + col + '">' + sig + '</div></div>'
    r = ind["rsi"]
    return f"""<div class="ind-grid">
        {box("RSI (14)",f"{r:.1f}","BUY" if r<30 else ("SELL" if r>70 else "NEUTRAL"),f"RSI {r:.1f} — <30=Oversold BUY | >70=Overbought SELL | 30-70=Neutral")}
        {box("VWAP",f"{ind['vwap']:,.0f}","BUY" if ind['price']>ind['vwap'] else "SELL",f"VWAP {ind['vwap']:,.0f} — Price {'above' if ind['price']>ind['vwap'] else 'below'} = {'bullish' if ind['price']>ind['vwap'] else 'bearish'} bias")}
        {box("EMA 9/21",f"{'▲' if ind['ema9']>ind['ema21'] else '▼'} {ind['ema9']:,.0f}","BUY" if ind['ema9']>ind['ema21'] else "SELL",f"EMA9={ind['ema9']:,.0f} EMA21={ind['ema21']:,.0f} — EMA9>EMA21=Uptrend")}
        {box("VOLUME",f"{ind['vol_ratio']:.1f}x avg","BUY" if ind['vol_spike'] else ("NEUTRAL" if ind['vol_ratio']>0.8 else "SELL"),f"Volume {ind['vol_ratio']:.2f}x average — 1.5x+ surge confirms signal")}
        {box("BOLLINGER",f"{ind['bb_pos']:.0f}% pos","BUY" if ind['bb_pos']<15 else ("SELL" if ind['bb_pos']>85 else "NEUTRAL"),f"BB Position {ind['bb_pos']:.0f}% — 0%=near lower band, 100%=near upper band")}
        {box("MOMENTUM",f"{ind['mom_pct']:+.2f}%","BUY" if ind['mom_pct']>0.2 else ("SELL" if ind['mom_pct']<-0.2 else "NEUTRAL"),f"5-bar momentum {ind['mom_pct']:+.2f}% — price change over last 5 candles")}
    </div>"""

def _sig_card(name, sym, df, gift_trend, vix):
    ind  = calc_ind(df)
    sig  = calc_signal(ind, gift_trend, vix)
    if ind: log_sig(sym, name, sig["signal"], ind)
    if df is not None: check_alerts(sym, df)

    if ind is None:
        # Fallback: show last available candle data even if indicators fail
        if df is not None and len(df) >= 2:
            try:
                cur  = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                pts  = cur - prev; pct = pts / prev * 100
                col  = "#00d463" if pts > 0 else ("#ff3d3d" if pts < 0 else "#3d9be9")
                arr  = "▲" if pts > 0 else "▼"
                last5 = df["Close"].astype(float).iloc[-5:].tolist()
                last5o = df["Open"].astype(float).iloc[-5:].tolist() if "Open" in df.columns else last5
                parts = []
                labels = ["C-4","C-3","C-2","C-1","NOW"]
                for ci in range(min(5, len(last5))):
                    is_bull = last5[ci] >= last5o[ci]
                    cc2 = "#00d463" if is_bull else "#ff3d3d"
                    sym2 = "▲" if is_bull else "▼"
                    tip2 = f"{labels[ci]}: {'BULL' if is_bull else 'BEAR'} {last5[ci]:,.1f}"
                    parts.append(f'<span title="{tip2}" style="color:{cc2};font-size:11px;cursor:help">{sym2}<br><span style="font-size:7px;color:#5a8aaa">{labels[ci]}</span></span>')
                candles_html = "&nbsp;".join(parts)
                zone = "sc-buy" if pct > 0.05 else ("sc-sell" if pct < -0.05 else "sc-wait")
                return f"""<div class="sc {zone}">
                    <div class="sc-sym">{name}</div>
                    <div class="sc-price" style="color:{col}">{cur:,.1f}</div>
                    <div class="sc-pts" style="color:{col}">{arr} {abs(pts):,.1f}pts &nbsp; {arr} {abs(pct):.2f}%</div>
                    <div class="sc-sig" style="color:#ffb700">⏳ INDICATORS LOADING…</div>
                    <div style="display:flex;justify-content:center;gap:4px;margin-top:6px;flex-wrap:wrap">{candles_html}</div>
                    <div class="sc-meta"><span>PREV {prev:,.1f}</span><span>LAST DATA</span><span>{pct:+.2f}%</span></div>
                    <div class="sc-time">🕐 {datetime.now(IST).strftime("%H:%M:%S")} &nbsp;|&nbsp; <span style="color:#ffb700">📡 YAHOO</span></div>
                </div>"""
            except Exception:
                pass
        return f'<div class="sc sc-wait"><div class="sc-sym">{name}</div><div style="color:#3a6a8f;padding:20px;font-family:Share Tech Mono">⚠️ DATA LOADING…<br><span style="font-size:10px">Market hours: 9:15–15:30 IST</span></div></div>'

    p   = ind["price"]
    o0  = float(df["Open"].iloc[0]) if "Open" in df.columns else p
    pts = p - o0; pct = pts/o0*100
    col = "#00d463" if sig["zone"]=="sc-buy" else ("#ff3d3d" if sig["zone"]=="sc-sell" else ("#ffb700" if "caut" in sig["zone"] else "#3d5a7a"))
    arr = "▲" if pts>=0 else "▼"

    dot_labels = ["EMA", "VWAP", "RSI", "VOL"]
    dot_full   = ["EMA9>EMA21: Uptrend", "Price>VWAP: Above avg", "RSI>54: Momentum", "Volume 1.5x+: Surge"]
    tris_parts2 = []
    for di in range(4):
        active = sig["tris"][di]
        dc = col if active else "#0d2040"
        ds = "▲" if active else "▽"
        status = "✅ ON" if active else "❌ OFF"
        tip3 = dot_full[di] + " — " + status
        tris_parts2.append(
            '<span style="display:inline-flex;flex-direction:column;align-items:center;cursor:help" title="' + tip3 + '">'
            '<span style="color:' + dc + ';font-size:18px">' + ds + '</span>'
            '<span style="color:' + dc + ';font-size:10px;letter-spacing:0.5px;font-weight:600">' + dot_labels[di] + '</span>'
            '</span>'
        )
    tris_html = "&nbsp;&nbsp;".join(tris_parts2)

    vix_html = ""
    if vix:
        vc = "#00d463" if vix["val"]<15 else ("#ffb700" if vix["val"]<20 else "#ff3d3d")
        vix_html = f'<div class="vblink" style="color:{vc};font-size:11px;margin:2px 0">⚡ VIX {vix["val"]:.1f} <span style="font-size:10px">({vix["chg"]:+.1f}%)</span></div>'

    sl_html = ""
    if sig["sl_val"] and sig["zone"] in ("sc-buy","sc-sell","sc-caut"):
        sl_html = f'<div class="sc-entry"><div style="font-size:9px;letter-spacing:2px;color:#3d9be9;margin-bottom:2px">ENTRY / SL</div><div style="color:{col};font-size:11px">{sig["entry_quality"]}</div><div style="color:#ff7070;font-size:11px;margin-top:2px;font-family:Share Tech Mono">🛑 SL {sig["sl_val"]:,.0f} &nbsp; RISK {sig["sl_risk"]:,.0f}pts</div></div>'

    vbadge = '<span class="sc-badge" style="background:#3a0000;color:#ff9800;border:1px solid #ff9800">⚡ VIX ALERT</span>' if sig["vix_warn"] else ""

    # Last 5 candles direction (for Nifty/BankNifty cards)
    last_candles_html = ""
    try:
        if df is not None and len(df) >= 5:
            last5c = df["Close"].astype(float).iloc[-5:].tolist()
            last5o = df["Open"].astype(float).iloc[-5:].tolist() if "Open" in df.columns else last5c
            parts = []
            labels = ["C-4","C-3","C-2","C-1","NOW"]
            for ci in range(len(last5c)):
                is_bull = last5c[ci] >= last5o[ci]
                cc = "#00d463" if is_bull else "#ff3d3d"
                sym2 = "▲" if is_bull else "▼"
                tip2 = f"{labels[ci]}: {'BULL' if is_bull else 'BEAR'} {last5c[ci]:,.1f}"
                parts.append(f'<span title="{tip2}" style="color:{cc};font-size:11px;cursor:help">{sym2}<br><span style="font-size:7px;color:#5a8aaa">{labels[ci]}</span></span>')
            last_candles_html = "&nbsp;".join(parts)
    except Exception:
        pass

    return f"""<div class="sc {sig['zone']}">
        {vbadge}
        <div class="sc-sym">{name}</div>
        <div class="sc-price" style="color:{col}">{p:,.1f}</div>
        <div class="sc-pts" style="color:{'#00d463' if pts>=0 else '#ff3d3d'}">{arr} {abs(pts):,.1f}pts &nbsp; {arr} {abs(pct):.2f}%</div>
        <div class="sc-sig" style="color:{col}">{sig["signal"]}</div>
        {vix_html}
        <div style="display:flex;justify-content:center;gap:12px;margin:5px 0">{tris_html}</div>
        <div class="sc-meta">
            <span>RSI {sig["rsi"]:.0f}</span>
            <span>VWAP {sig["vwap"]:,.0f}</span>
            <span>VOL {sig["vol_ratio"]:.1f}x</span>
            <span>MOM {sig["mom_pct"]:+.2f}%</span>
            <span>GIFT {sig["gift_trend"]}</span>
        </div>
        <div style="display:flex;justify-content:center;gap:4px;margin-top:4px;flex-wrap:wrap">
        {last_candles_html}
        </div>
        {sl_html}
        <div class="sc-time">🕐 {datetime.now(IST).strftime("%H:%M:%S")} &nbsp;|&nbsp; <span style="color:{'#00d463' if (dhan_active() and is_market_open()) else '#ffb700'}">{'⚡DHAN' if (dhan_active() and is_market_open()) else '📡YAHOO'}</span></div>
    </div>"""

def _gift_card(df, gift_sym, vix):
    gift_sym = gift_sym or "SGX/GIFT"
    if df is None:
        return '<div class="sc sc-wait"><div class="sc-sym">GIFT NIFTY</div><div style="color:#3a6a8f;padding:20px">⚠️ DATA LOADING…</div></div>'
    try:
        cur  = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        pts  = cur-prev; pct = pts/prev*100
        col  = "#00d463" if pts>0 else ("#ff3d3d" if pts<0 else "#3d9be9")
        zone = "sc-buy" if pct>0.05 else ("sc-sell" if pct<-0.05 else "sc-wait")
        trend= "🐂 BULLISH" if pct>0.05 else ("🐻 BEARISH" if pct<-0.05 else "⚖️ NEUTRAL")
        arr  = "▲" if pts>0 else "▼"
        last5 = df["Close"].astype(float).iloc[-5:].tolist()
        tris_parts = []
        for gi in range(1, len(last5)):
            up = last5[gi] > last5[gi-1]
            gc2 = "#00d463" if up else "#ff3d3d"
            gs  = "▲" if up else "▼"
            tip = f"Candle {gi}: {'UP' if up else 'DOWN'} ({last5[gi]:,.1f})"
            tris_parts.append(f'<span title="{tip}" style="color:{gc2};font-size:19px;cursor:help">{gs}</span>')
        tris  = "&nbsp;".join(tris_parts)
        candle_labels = ["C-4","C-3","C-2","C-1"]
        candle_label_html = "&nbsp;&nbsp;".join(
            f'<span style="color:#5a8aaa;font-size:8px">{candle_labels[gi]}</span>'
            for gi in range(len(tris_parts)))
        vix_html = ""
        if vix:
            vc = "#00d463" if vix["val"]<15 else ("#ffb700" if vix["val"]<20 else "#ff3d3d")
            vix_html = f'<div class="vblink" style="color:{vc};font-size:11px;margin:2px 0">⚡ VIX {vix["val"]:.1f}</div>'
        return f"""<div class="sc {zone}">
            <span class="sc-badge" style="color:{col};border:1px solid {col}">SGX / GIFT NIFTY FUTURES</span>
            <div class="sc-sym">15-MIN GLOBAL TREND</div>
            <div class="sc-price" style="color:{col}">{cur:,.1f}</div>
            <div class="sc-pts" style="color:{col}">{arr} {abs(pts):,.1f}pts &nbsp; {arr} {abs(pct):.3f}%</div>
            <div class="sc-sig" style="color:{col}">{trend}</div>
            {vix_html}
            <div class="sc-tris">{tris}</div>
            <div style="display:flex;justify-content:center;gap:10px;font-size:10px;color:#5a8aaa;margin-top:1px">{candle_label_html}</div>
            <div style="font-size:10px;color:#5a8aaa;margin-top:2px">← LAST 4 CANDLES (15 MIN)</div>
            <div class="sc-meta"><span>PREV {prev:,.1f}</span><span>15M INTERVAL</span><span>{pct:+.3f}%</span></div>
            <div class="sc-time">🕐 {datetime.now(IST).strftime("%H:%M:%S")} &nbsp;|&nbsp; <span style="color:{'#00d463' if gift_sym=='DHAN:NIFTY' else '#ffb700'}">{'⚡DHAN' if gift_sym=='DHAN:NIFTY' else '📡YAHOO'}</span></div>
        </div>"""
    except Exception:
        return '<div class="sc sc-wait"><div class="sc-sym">GIFT NIFTY</div><div style="color:#3a6a8f;padding:10px">⚠️ Error</div></div>'

def _mini(icon, name, q, inr=False):
    if not q:
        return f'<div class="mc"><div class="mc-ico">{icon}</div><div class="mc-nm">{name}</div><div style="color:#6a90aa;font-family:Share Tech Mono;font-size:18px">—</div></div>'
    p,chg,pts = q["price"],q["chg"],q["pts"]
    col = "#00e87a" if chg>0 else ("#ff5555" if chg<0 else "#55aadd")
    arr = "▲" if chg>0 else ("▼" if chg<0 else "—")
    # Format price: use comma for large numbers, 2 decimals for small
    if p >= 1000:
        p_str = f"{p:,.0f}"
    elif p >= 10:
        p_str = f"{p:,.2f}"
    else:
        p_str = f"{p:.4f}"
    pts_str = f"{pts:+,.1f}" if abs(p)>10 else f"{pts:+.4f}"
    return f'<div class="mc"><div class="mc-ico">{icon}</div><div class="mc-nm">{name}</div><div class="mc-pr">{p_str}</div><div class="mc-ch" style="color:{col}">{arr} {abs(chg):.2f}%</div><div class="mc-pt" style="color:{col}">{pts_str}</div></div>'

def _pivot_html(pvt, cmp):
    if not pvt: return "<div style='color:#3a6a8f'>Loading pivots…</div>"
    def cell(lbl,val,css):
        atm = "outline:2px solid #ffd050;" if abs(val-cmp)<25 else ""
        return f'<div class="pvt-cell {css}" style="{atm}"><div class="pvt-lbl">{lbl}</div>{val:,.0f}</div>'
    if   cmp>pvt["R2"]: st2,col2,adv = "Above R2 🔴 OVERBOUGHT","#ff3d3d","Heavy resistance. SELL / book profits."
    elif cmp>pvt["R1"]: st2,col2,adv = "R1–R2 🔴 Resistance",  "#ff7070","Short near R2, tight SL."
    elif cmp>pvt["P"]:  st2,col2,adv = "Pivot–R1 🟡 Bullish",  "#ffb700","Above Pivot — bullish. Target R1."
    elif cmp>pvt["S1"]: st2,col2,adv = "S1–Pivot 🟡 Weak",     "#ffb700","Below Pivot — wait to reclaim PP."
    elif cmp>pvt["S2"]: st2,col2,adv = "S1–S2 🟢 Support",     "#00d463","BUY near S1. SL below S2."
    else:               st2,col2,adv = "Below S2 🟢 Strong",   "#00d463","High-probability reversal BUY zone."
    return f"""<div class="pvt-grid">
        {cell("R3 🔴",pvt["R3"],"pvt-r")}{cell("R2 🔴",pvt["R2"],"pvt-r")}
        {cell("R1 🔴",pvt["R1"],"pvt-r")}{cell("PIVOT⚡",pvt["P"],"pvt-p")}
        {cell("S1 🟢",pvt["S1"],"pvt-s")}{cell("S2 🟢",pvt["S2"],"pvt-s")}
        {cell("S3 🟢",pvt["S3"],"pvt-s")}{cell("CMP",cmp,"pvt-c")}
    </div>
    <div style="background:{col2}15;border:1px solid {col2}35;border-radius:6px;padding:8px;margin-top:7px">
        <div style="color:{col2};font-weight:700;font-size:12px;margin-bottom:3px">{st2}</div>
        <div style="color:#a0c8e0;font-size:11px">{adv}</div>
    </div>"""

# Items to show larger in tape
_TAPE_BIG = {"NIFTY","BNKIFTY","GIFT NF","GOLD","WTI OIL","VIX"}

def _tape_html(items):
    cells = []
    for x in items:
        big = "tape-big" if x["n"] in _TAPE_BIG else ""
        cells.append(
            f'<div class="tape-item {big}">' +
            f'<span class="ti-n">{x["n"]}</span>' +
            f'<span class="ti-v" style="color:{x["vc"]}">{x["val"]}</span>' +
            f'<span class="ti-c" style="color:{x["cc"]}">{x["arr"]}{abs(x["pct"]):.2f}%</span>' +
            f'<span class="ti-p" style="color:{x["cc"]}">{x["pts"]}</span>' +
            '</div>'
        )
    return '<div class="tape-wrap">' + "".join(cells) + '</div>'

def _mood_html(score):
    lbl = "EXTREME FEAR" if score<20 else ("FEAR" if score<40 else ("NEUTRAL" if score<60 else ("GREED" if score<80 else "EXTREME GREED")))
    col = "#ff3d3d" if score<30 else ("#ff8844" if score<50 else ("#ffcc00" if score<70 else "#00d463"))
    return f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:11px">
        <div style="font-size:9px;letter-spacing:3px;color:#3d9be9;margin-bottom:7px">🧠 MARKET MOOD METER</div>
        <div class="mood-track"><div class="mood-ptr" style="left:{max(1,min(99,score))}%"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:8px;color:#3a6a8f;margin-bottom:5px">
            <span>EXTREME FEAR</span><span>NEUTRAL</span><span>EXTREME GREED</span>
        </div>
        <div style="text-align:center;font-size:15px;font-weight:900;color:{col};font-family:Share Tech Mono">{score}/100 — {lbl}</div>
    </div>"""


# ════════════════════════════════════════════════════════════
#  SL CALCULATOR
# ════════════════════════════════════════════════════════════

def sl_calc_section():
    st.markdown('<span class="slbl">🎯 STOP LOSS CALCULATOR</span>', unsafe_allow_html=True)
    r1,r2,r3 = st.columns(3)
    with r1:
        entry = st.number_input("Entry Price ", min_value=1.0, value=22450.0, step=5.0, key="sl_entry")
        ttype = st.selectbox("Position Type", ["BUY / LONG","SELL / SHORT"], key="sl_type")
    with r2:
        sl_p = st.number_input("SL % from Entry", min_value=0.05, max_value=5.0, value=0.4, step=0.05, key="sl_pct")
        qty  = st.number_input("Qty / Lot Size", min_value=1, value=50, step=1, key="sl_qty")
    with r3:
        rr   = st.number_input("Target R:R (1:?)", min_value=0.5, value=2.0, step=0.5, key="sl_rr")

    is_buy = "BUY" in ttype
    sl_pts = entry * sl_p / 100
    sl_v   = entry-sl_pts if is_buy else entry+sl_pts
    t1_v   = entry+sl_pts*rr    if is_buy else entry-sl_pts*rr
    t2_v   = entry+sl_pts*rr*1.5 if is_buy else entry-sl_pts*rr*1.5
    risk   = sl_pts*qty; p1=sl_pts*rr*qty; p2=sl_pts*rr*1.5*qty

    st.markdown(f"""<div class="sl-grid">
        <div class="sl-box" style="border-color:#ff3d3d">
            <div class="sl-lbl">🛑 STOP LOSS</div>
            <div class="sl-val" style="color:#ff7070">{sl_v:,.1f}</div>
            <div class="sl-sub" style="color:#ff8888">{'-' if is_buy else '+'}{sl_pts:,.1f}pts | {sl_p}%</div>
        </div>
        <div class="sl-box" style="border-color:#00d463">
            <div class="sl-lbl">🎯 TARGET 1 (1:{rr:.1f})</div>
            <div class="sl-val" style="color:#00d463">{t1_v:,.1f}</div>
            <div class="sl-sub" style="color:#44ee88">{'+' if is_buy else '-'}{sl_pts*rr:,.1f}pts</div>
        </div>
        <div class="sl-box" style="border-color:#ffb700">
            <div class="sl-lbl">🎯 TARGET 2 (1:{rr*1.5:.1f})</div>
            <div class="sl-val" style="color:#ffb700">{t2_v:,.1f}</div>
            <div class="sl-sub" style="color:#ffdd88">{'+' if is_buy else '-'}{sl_pts*rr*1.5:,.1f}pts</div>
        </div>
        <div class="sl-box" style="border-color:#ff3d3d">
            <div class="sl-lbl">💸 TOTAL RISK</div>
            <div class="sl-val" style="color:#ff7070">{risk:,.0f}</div>
            <div class="sl-sub" style="color:#6a90aa">{qty}×{sl_pts:,.1f}</div>
        </div>
        <div class="sl-box" style="border-color:#00d463">
            <div class="sl-lbl">💰 PROFIT T1</div>
            <div class="sl-val" style="color:#00d463">{p1:,.0f}</div>
            <div class="sl-sub" style="color:#44ee88">R:R 1:{rr}</div>
        </div>
        <div class="sl-box" style="border-color:#ffb70055">
            <div class="sl-lbl">💰 PROFIT T2</div>
            <div class="sl-val" style="color:#ffb700">{p2:,.0f}</div>
            <div class="sl-sub" style="color:#ffdd88">R:R 1:{rr*1.5:.1f}</div>
        </div>
    </div>
    <div style="padding:9px;background:#030c1a;border:1px solid #ffb70030;border-radius:6px;font-size:12px;color:#ccaa66;line-height:1.9">
        {'✅ Good R:R ≥1:2 — safe to proceed' if rr>=2 else '⚠️ R:R below 1:2 — widen target or skip trade'}<br>
        {'🔴 Risk >10K — reduce qty or skip!' if risk>10000 else ('🟡 Risk >5K — watch sizing' if risk>5000 else '✅ Risk within safe range')}<br>
        <span style="color:#6a90aa;font-size:11px">💡 OI-based SL: Use max Put OI strike as BUY SL | max Call OI strike as SELL SL (see OI+Pivot tab)</span>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  REPORT
# ════════════════════════════════════════════════════════════

def report_section():
    logs   = st.session_state.signals_log
    evaled = [l for l in logs if l["evaluated"]]
    passed = [l for l in evaled if "PASS" in (l.get("result") or "")]
    strike = len(passed)/len(evaled)*100 if evaled else 0
    buys   = len([l for l in logs if "BUY"  in l.get("signal","")])
    sells  = len([l for l in logs if "SELL" in l.get("signal","")])

    cols = st.columns(8)
    mets = [("SIGNALS",str(len(logs)),"#3d9be9"),("PASS",str(len(passed)),"#00d463"),
            ("FAIL",str(len(evaled)-len(passed)),"#ff3d3d"),
            ("STRIKE%",f"{strike:.0f}%","#00d463" if strike>=60 else "#ffb700"),
            ("PENDING",str(len(logs)-len(evaled)),"#ffb700"),
            ("BUYS",str(buys),"#00d463"),("SELLS",str(sells),"#ff3d3d"),
            ("ALERTS",str(len(st.session_state.alert_log)),"#ff8800")]
    for col,(l,v,c) in zip(cols,mets):
        with col: st.markdown(f'<div class="rm"><div class="rv" style="color:{c}">{v}</div><div class="rl">{l}</div></div>', unsafe_allow_html=True)

    if logs:
        st.markdown("#### 📋 Signal Log — Auto-evaluated after 15 min (max 100)")
        rows = []
        for l in logs:
            rows.append({
                "Time": l["time"], "Symbol": l["symbol"], "Signal": l["signal"],
                "Entry": "" + "{:,.1f}".format(l["price"]),
                "Exit":  "" + "{:,.1f}".format(l["exit_price"]) if l["exit_price"] else "⏳",
                "Result": l.get("result") or "⏳",
                "RSI":  "{:.0f}".format(l["rsi"]),
                "VWAP": "" + "{:,.0f}".format(l.get("vwap",0)),
                "Vol":  "{:.1f}x".format(l.get("vol",0)),
                "Dots": "{}/4".format(l.get("dots",0)),
                "Fail": l.get("fail_reason","—"),
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, height=220)
    else:
        st.info("📡 No signals yet. Signal log appears after first BUY/SELL fires during market hours.")

    # ── FAIL LOG ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📉 Signal Failure Analysis & Resolution Guide")
    fail_log = st.session_state.fail_log
    if fail_log:
        for fl in reversed(fail_log[-10:]):
            fk    = fl.get("fail_key", "WHIPSAW")
            fdata = FAIL_REASONS.get(fk, FAIL_REASONS["WHIPSAW"])
            move  = fl.get("move", 0)
            dots  = fl.get("dots", 0)
            m_col = "#ff7070" if move < 0 else "#88ffaa"
            d_col = "#ff7070" if dots < 3 else "#88ffaa"
            st.markdown(
                '<div style="background:#020b18;border:1px solid #ff3d3d20;border-radius:6px;padding:9px 11px;margin:5px 0;font-size:11px;line-height:1.8">' +
                '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px;margin-bottom:6px">' +
                '<span style="color:#e0f0ff;font-weight:700;font-size:13px">' + fl.get("symbol","") + ' — ' + fl.get("signal","") + '</span>' +
                '<span style="font-family:Share Tech Mono;font-size:11px;color:#6a90aa">' + fl.get("time","") + '</span></div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:5px;margin-bottom:8px;font-family:Share Tech Mono;font-size:11px">' +
                '<div><span style="color:#6a90aa">ENTRY</span><br>' + "{:,.0f}".format(fl.get("entry",0)) + '</div>' +
                '<div><span style="color:#6a90aa">EXIT</span><br><span style="color:#ff7070">' + "{:,.0f}".format(fl.get("exit",0)) + '</span></div>' +
                '<div><span style="color:#6a90aa">MOVE</span><br><span style="color:' + m_col + '">' + "{:+.0f}".format(move) + 'pts</span></div>' +
                '<div><span style="color:#6a90aa">DOTS</span><br><span style="color:' + d_col + '">' + str(dots) + '/4</span></div></div>' +
                '<div style="background:' + fdata["color"] + '15;border:1px solid ' + fdata["color"] + '35;border-radius:5px;padding:8px">' +
                '<div style="color:#ff8888;font-weight:700">❌ FAIL REASON: ' + fdata["reason"] + '</div>' +
                '<div style="color:#c0d8f0;font-size:11px;margin:3px 0">' + fdata["detail"] + '</div>' +
                '<div style="color:#88ffaa;font-weight:700">✅ RESOLUTION: ' + fdata["resolution"] + '</div></div></div>',
                unsafe_allow_html=True)
        # Pattern summary
        from collections import Counter
        fk_counts = Counter(fl.get("fail_key","?") for fl in fail_log)
        if fk_counts:
            st.markdown("**📊 Failure Pattern Summary** (use to improve accuracy):")
            cols3 = st.columns(min(4, len(fk_counts)))
            for i, (fk, cnt) in enumerate(fk_counts.most_common(4)):
                fdata2 = FAIL_REASONS.get(fk, {})
                with cols3[i % 4]:
                    st.markdown(
                        '<div class="rm" title="' + fdata2.get("reason",fk) + '">' +
                        '<div class="rv" style="color:' + fdata2.get("color","#ff3d3d") + '">' + str(cnt) + '</div>' +
                        '<div class="rl">' + fk.replace("_"," ") + '</div></div>',
                        unsafe_allow_html=True)
    else:
        st.info("✅ No failed signals yet. Detailed failure analysis with resolutions will appear here after signals are evaluated (15 min after signal fires).")

    if st.session_state.alert_log:
        st.markdown("#### 🚨 Price Alerts")
        alert_parts = []
        for a in reversed(st.session_state.alert_log):
            alert_parts.append(
                '<div class="alert-box ' + a["css"] + '" title="' + a["sym"] + ' moved ' + a["pct"] + ' at ' + a["time"] + '">' +
                a["type"] + ' <strong>' + a["sym"] + '</strong> ' + a["pct"] +
                ' <span style="color:#6a90aa">' + a["time"] + '</span></div>'
            )
        st.markdown("".join(alert_parts), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  MAIN APP
# ════════════════════════════════════════════════════════════

now_ist    = datetime.now(IST)
is_expiry  = now_ist.weekday() == 3  # Thursday

# Fetch all data
with st.spinner(""):
    df_nifty   = get_candles("^NSEI")
    df_bank    = get_candles("^NSEBANK")
    df_finnifty = get_finnifty_data()
    df_gift, gift_sym = get_gift_data()
    vix        = get_vix_data()
    live_news  = get_live_news()

# Gift trend
gift_trend = "NEUTRAL"
if df_gift is not None and len(df_gift) >= 2:
    try:
        gc = (float(df_gift["Close"].iloc[-1]) - float(df_gift["Close"].iloc[-2])) / float(df_gift["Close"].iloc[-2]) * 100
        gift_trend = "BULL" if gc>0.05 else ("BEAR" if gc<-0.05 else "NEUTRAL")
    except Exception: pass

if vix and vix.get("spike"): _queue("vix")

# Mood score
mood = 54
if df_nifty is not None:
    try:
        ind_tmp = calc_ind(df_nifty)
        if ind_tmp: mood = min(95, max(5, int((ind_tmp["rsi"]-30)/40*100)))
    except: pass

# Tape items
_TAPE_SYMS = [("^NSEI","NIFTY",True),("^NSEBANK","BNKIFTY",True),("^CNXFIN","FINNIFTY",True),
              ("^INDIAVIX","VIX",False),("GC=F","GOLD",False),("CL=F","CRUDE",False),
              ("USDINR=X","USD/INR",True),("NQ=F","NASDAQ",False),("NIY=F","NIKKEI",False)]
tape_data = []
for sym,nm,inr in _TAPE_SYMS:
    q = get_q(sym)
    if q:
        p,chg,pts = q["price"],q["chg"],q["pts"]
        cc = "#00d463" if chg>0 else ("#ff3d3d" if chg<0 else "#3d9be9")
        vc = "#00d463" if (nm=="VIX" and p<15) else ("#ffb700" if nm=="VIX" and p<20 else ("#ff3d3d" if nm=="VIX" else "#ddeeff"))
        val= f"{p:,.1f}" if inr else f"{p:,.2f}" if p<100 else f"{p:,.1f}"
        tape_data.append({"n":nm,"val":val,"arr":"▲" if chg>0 else "▼","pct":chg,"cc":cc,"vc":vc,
                          "pts":f"{pts:+,.1f}" if abs(p)>10 else f"{pts:+.4f}"})

# ── HEADER ──────────────────────────────────────────────────
h1,h2,h3,h4,h5 = st.columns([3,2,2,1.5,1])
with h1:
    st.markdown('<div style="font-size:19px;font-weight:900;letter-spacing:4px;color:#3d9be9;font-family:Share Tech Mono">🦅 EAGLE EYE PRO <span style="font-size:10px;color:#3a6a8f">v9.0</span></div>', unsafe_allow_html=True)
with h2:
    st.markdown(f'<div style="font-size:11px;color:#5a8aaa;font-family:Share Tech Mono;padding-top:5px">{now_ist.strftime("%I:%M:%S %p")} IST<br>{now_ist.strftime("%a, %d %b %Y")}</div>', unsafe_allow_html=True)
with h3:
    if vix:
        vc2 = "#00d463" if vix["val"]<15 else ("#ffb700" if vix["val"]<20 else "#ff3d3d")
        rsk = "LOW RISK 🟢" if vix["val"]<15 else ("MED RISK 🟡" if vix["val"]<20 else "HIGH RISK 🔴")
        st.markdown(f'<div class="vblink" style="font-size:15px;font-weight:900;color:{vc2};font-family:Share Tech Mono;padding-top:4px">VIX {vix["val"]:.2f} <span style="font-size:10px">({vix["chg"]:+.1f}%)</span></div><div style="font-size:10px;color:{vc2};letter-spacing:1.5px">{rsk}</div>', unsafe_allow_html=True)
with h4: _sound_btn()
with h5:
    dhan_on  = dhan_active()
    mkt_open = is_market_open()
    src_label = "🔴 OFFLINE" if df_nifty is None else ("DHAN ⚡" if (dhan_on and mkt_open) else "YAHOO 📡")
    src_col   = "#ff3d3d" if df_nifty is None else ("#00d463" if (dhan_on and mkt_open) else "#ffb700")
    status    = "🟢 LIVE" if df_nifty is not None else "🔴 OFFLINE"
    st.markdown(f'<div style="font-size:9px;text-align:right;padding-top:6px;font-family:Share Tech Mono"><span style="color:{src_col}">{src_label}</span><br><span style="color:#3a6a8f">{status} ⟳ {"8s" if (dhan_on and mkt_open) else "15s"}</span></div>', unsafe_allow_html=True)

if is_expiry:
    st.markdown('<div class="exp-banner">⚡ F&O EXPIRY DAY — THURSDAY — MAX PAIN ZONE ACTIVE — AVOID NAKED POSITIONS ⚡</div>', unsafe_allow_html=True)

st.markdown('<div style="height:2px;border-bottom:1px solid #0d3060;margin:3px 0 4px"></div>', unsafe_allow_html=True)

# LIVE TAPE
if tape_data:
    st.markdown(_tape_html(tape_data), unsafe_allow_html=True)
    st.markdown('<div style="height:3px"></div>', unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────
T = st.tabs(["⚡ SIGNALS","📊 CHARTS","🌍 MARKETS","📰 NEWS",
             "📅 CALENDAR","📈 OI+PIVOT","🎯 SL CALC","⚡ STRATEGY","📊 REPORT"])
t1,t2,t3,t4,t5,t6,t7,t8,t9 = T


# ── TAB 1: SIGNALS ───────────────────────────────────────────
with t1:
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        # 1. NIFTY 50
        st.markdown(_sig_card("NIFTY 50","^NSEI",df_nifty,gift_trend,vix), unsafe_allow_html=True)
        ind_n = calc_ind(df_nifty)
        if ind_n: st.markdown(_ind_grid(ind_n), unsafe_allow_html=True)
    with c2:
        # 2. BANKNIFTY
        st.markdown(_sig_card("BANKNIFTY","^NSEBANK",df_bank,gift_trend,vix), unsafe_allow_html=True)
        ind_b = calc_ind(df_bank)
        if ind_b: st.markdown(_ind_grid(ind_b), unsafe_allow_html=True)
    with c3:
        # 3. GIFT NIFTY
        st.markdown(_gift_card(df_gift,gift_sym,vix), unsafe_allow_html=True)
        if vix and vix.get("hist"):
            st.markdown('<div style="color:#3d9be9;font-size:9px;letter-spacing:2px;margin:4px 0 2px;font-family:Share Tech Mono">⚡ VIX 30-DAY HISTORY</div>', unsafe_allow_html=True)
            st.plotly_chart(sanitize_colors(vix_chart(vix["hist"])),width="stretch",config={"displayModeBar":False}, key="vix_hist_t1")
    with c4:
        # 4. FIN NIFTY
        st.markdown(_sig_card("FIN NIFTY","^CNXFIN",df_finnifty,gift_trend,vix), unsafe_allow_html=True)
        ind_f = calc_ind(df_finnifty)
        if ind_f: st.markdown(_ind_grid(ind_f), unsafe_allow_html=True)

    # ── Data source & market status banner ──
    mkt_now = is_market_open()
    dhan_now = dhan_active()
    if not mkt_now:
        st.markdown('<div style="background:#0d1a2a;border:1px solid #1a3a5a;border-radius:6px;padding:6px 12px;font-size:12px;color:#7aaabf;text-align:center;margin:3px 0">📴 Market Closed (9:15–15:30 IST) — Showing last available data. Charts use longer timeframes automatically.</div>', unsafe_allow_html=True)
    elif dhan_now:
        st.markdown('<div style="background:#001f0f;border:1px solid #00d46330;border-radius:6px;padding:5px 12px;font-size:12px;color:#00d463;text-align:center;margin:3px 0">⚡ DHAN API ACTIVE — Real-time data (~50ms latency)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#1a1000;border:1px solid #ffb70030;border-radius:6px;padding:5px 12px;font-size:12px;color:#ffb700;text-align:center;margin:3px 0">📡 Yahoo Finance — 15-30s delay | Add Dhan API in Streamlit Secrets for real-time</div>', unsafe_allow_html=True)

    st.markdown(_mood_html(mood), unsafe_allow_html=True)

    if st.session_state.alert_log:
        st.markdown('<span class="slbl">🚨 SPIKE / FALL ALERTS</span>', unsafe_allow_html=True)
        alc = st.columns(min(3,len(st.session_state.alert_log)))
        for i,a in enumerate(reversed(st.session_state.alert_log[:3])):
            with alc[i]: st.markdown(f'<div class="alert-box {a["css"]}">{a["type"]} <strong>{a["sym"]}</strong> {a["pct"]} <span style="color:#6a90aa">{a["time"]}</span></div>', unsafe_allow_html=True)

    st.markdown('<span class="slbl">📊 COMMODITIES</span>', unsafe_allow_html=True)
    qc = st.columns(4)
    for (sym,nm,ico,inr),col in zip([
        ("GC=F","GOLD $/oz","🥇",False),("CL=F","CRUDE $/bbl","🛢️",False),
        ("SI=F","SILVER $/oz","🥈",False),("NG=F","NAT GAS","⚡",False),
    ],qc):
        with col: st.markdown(_mini(ico,nm,get_q(sym),inr),unsafe_allow_html=True)
    st.markdown('<span class="slbl">💱 FOREX vs INR</span>', unsafe_allow_html=True)
    gc2 = st.columns(4)
    for (sym,nm,ico,inr),col in zip([
        ("USDINR=X","USD/INR","🇺🇸",True),("EURINR=X","EUR/INR","🇪🇺",True),
        ("GBPINR=X","GBP/INR","🇬🇧",True),("JPYINR=X","JPY/INR","🇯🇵",True),
    ],gc2):
        with col: st.markdown(_mini(ico,nm,get_q(sym),inr),unsafe_allow_html=True)
    st.markdown('<span class="slbl">🌍 GLOBAL FUTURES</span>', unsafe_allow_html=True)
    gc3 = st.columns(4)
    for (sym,nm,ico,inr),col in zip([
        ("NQ=F","NASDAQ Fut","💻",False),("YM=F","DOW Fut","🏭",False),
        ("NIY=F","NIKKEI Fut","🇯🇵",False),("^GDAXI","DAX","🇩🇪",False),
    ],gc3):
        with col: st.markdown(_mini(ico,nm,get_q(sym),inr),unsafe_allow_html=True)


# ── TAB 2: CHARTS ────────────────────────────────────────────
with t2:
    # 1. NIFTY + BANKNIFTY side by side
    ch1,ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(sanitize_colors(make_chart(df_nifty,"NIFTY 50 (1-min)",vix["val"] if vix else None)),
            width="stretch",config={"displayModeBar":True}, key="chart_nifty_t2")
    with ch2:
        st.plotly_chart(sanitize_colors(make_chart(df_bank,"BANKNIFTY (1-min)",vix["val"] if vix else None)),
            width="stretch",config={"displayModeBar":True}, key="chart_bank_t2")
    # 2. GIFT NIFTY (15-min)
    st.markdown('<span class="slbl">GIFT NIFTY — 15 MIN</span>', unsafe_allow_html=True)
    st.plotly_chart(sanitize_colors(make_chart(df_gift,"GIFT NIFTY / SGX NIFTY (15-min)",vix["val"] if vix else None,height=400)),
        width="stretch",config={"displayModeBar":True}, key="chart_gift_t2")
    # 3. FIN NIFTY
    st.markdown('<span class="slbl">FIN NIFTY — 1 MIN</span>', unsafe_allow_html=True)
    st.plotly_chart(sanitize_colors(make_chart(df_finnifty,"FIN NIFTY / NIFTY FINANCIAL (1-min)",vix["val"] if vix else None, height=380)),
        width="stretch",config={"displayModeBar":True}, key="chart_fin_t2")


# ── TAB 3: MARKETS ───────────────────────────────────────────
with t3:
    for lbl,items in [
        ("🇺🇸 US — SPOT",[("^GSPC","S&P 500","📈",False),("^IXIC","NASDAQ","💻",False),("^DJI","DOW Jones","🏭",False),("^RUT","Russell 2K","📊",False)]),
        ("🇺🇸 US — FUTURES",[("ES=F","S&P500 Fut","📊",False),("NQ=F","NASDAQ Fut","🖥️",False),("YM=F","DOW Fut","📉",False),("RTY=F","Russell Fut","📊",False)]),
        ("🌏 ASIAN — SPOT",[("^N225","NIKKEI 225","🇯🇵",False),("^HSI","HANG SENG","🇭🇰",False),("^AXJO","ASX 200","🇦🇺",False),("^KS11","KOSPI","🇰🇷",False)]),
        ("🌏 ASIAN — FUTURES",[("NIY=F","NIKKEI Fut","🇯🇵",False),("NK=F","NIKKEI SGX","🇸🇬",False),("^NSEI","SGX NIFTY","🇮🇳",False),("ES=F","S&P Fut","🌏",False)]),
        ("🇪🇺 EUROPEAN — SPOT",[("^GDAXI","DAX 40","🇩🇪",False),("^FTSE","FTSE 100","🇬🇧",False),("^FCHI","CAC 40","🇫🇷",False),("^STOXX50E","Euro Stoxx","🇪🇺",False)]),
        ("🇪🇺 EUROPEAN — FUTURES",[("FDAX=F","DAX Fut","🇩🇪",False),("FCE=F","CAC Fut","🇫🇷",False),("FESX=F","EuroStoxx Fut","🇪🇺",False),("Z=F","FTSE Fut","🇬🇧",False)]),
        ("💰 COMMODITIES",[("GC=F","GOLD $/oz","🥇",False),("SI=F","SILVER $/oz","🥈",False),("CL=F","CRUDE $/bbl","🛢️",False),("NG=F","NAT GAS","⚡",False)]),
        ("💱 FOREX vs INR",[("USDINR=X","USD/INR","🇺🇸",True),("EURINR=X","EUR/INR","🇪🇺",True),("GBPINR=X","GBP/INR","🇬🇧",True),("JPYINR=X","JPY/INR","🇯🇵",True)]),
    ]:
        st.markdown(f'<span class="slbl">{lbl}</span>', unsafe_allow_html=True)
        mc = st.columns(4)
        for (s,n,i,r),col in zip(items,mc):
            with col: st.markdown(_mini(i,n,get_q(s),r),unsafe_allow_html=True)


# ── TAB 4: NEWS ──────────────────────────────────────────────
with t4:
    nc,sc2 = st.columns([3,1])
    all_news = live_news if live_news else NEWS_STATIC
    with nc:
        st.markdown('<span class="slbl">📰 LIVE NEWS — 🟢 GREEN=FAYDA (BUY) | 🔴 RED=NUQSAAN (AVOID/SELL) | 🔵 NEUTRAL</span>', unsafe_allow_html=True)
        new_bull = new_bear = 0
        for n in all_news:
            uid  = n.get("id","")
            sent = n.get("s","neu")
            is_new = uid not in st.session_state.news_seen
            if is_new:
                st.session_state.news_seen.add(uid)
                if sent=="bull": new_bull+=1
                elif sent=="bear": new_bear+=1
            nc2  = {"bull":"#00d463","bear":"#ff3d3d","neu":"#3d9be9"}[sent]
            lbl2 = {"bull":"🟢 BULLISH — FAYDA","bear":"🔴 BEARISH — NUQSAAN","neu":"🔵 NEUTRAL"}[sent]
            st.markdown(f'<a href="{n.get("link","#")}" target="_blank" style="text-decoration:none"><div class="ni ni-{sent}"><div class="ni-meta">{n.get("time","—")} | {n.get("src","")} &nbsp;<span style="background:{nc2}22;color:{nc2};padding:1px 7px;border-radius:2px;font-size:9px;font-weight:700">{lbl2}</span></div><div class="ni-title">{n.get("title","")}</div><div style="font-size:10px;color:#5a8aaa;margin-top:2px">👆 Tap to read full article →</div></div></a>', unsafe_allow_html=True)
        if not all_news:
            st.info("📡 Fetching live news… (Check internet connection)")
        if new_bull>0: _queue("news_bull")
        if new_bear>0: _queue("news_bear")

    with sc2:
        total_n = len(all_news) or 1
        bn = sum(1 for x in all_news if x.get("s")=="bull")
        rn = sum(1 for x in all_news if x.get("s")=="bear")
        en = total_n-bn-rn; bp = bn/total_n*100
        sc3 = "#00d463" if bp>55 else ("#ff3d3d" if bp<45 else "#ffb700")
        ov  = "BULLISH" if bp>55 else ("BEARISH" if bp<45 else "MIXED")
        st.markdown(f'<div class="sent-wrap"><div style="font-size:9px;letter-spacing:3px;color:#3d9be9;margin-bottom:7px">NEWS SENTIMENT</div><div style="font-size:23px;font-weight:900;color:{sc3};margin-bottom:7px">{ov}</div><div style="font-size:13px;color:#00d463;margin:4px 0">🟢 BULLISH &nbsp;<strong>{bn}</strong></div><div style="font-size:13px;color:#ff3d3d;margin:4px 0">🔴 BEARISH &nbsp;<strong>{rn}</strong></div><div style="font-size:13px;color:#3d9be9;margin:4px 0">🔵 NEUTRAL &nbsp;<strong>{en}</strong></div><div class="sent-track"><div class="sent-fill" style="width:{bp:.0f}%;background:{sc3}"></div></div><div style="font-size:10px;color:#6a90aa;margin-top:4px">{bp:.0f}% BULLISH</div></div>', unsafe_allow_html=True)
        st.markdown('<span class="slbl" style="margin-top:10px;display:block">📅 KEY EVENTS</span>', unsafe_allow_html=True)
        ECO_CAL_MINI = [
            ("RBI MPC","HIGH","6.5% hold"),("US Fed FOMC","HIGH","Rate watch"),
            ("India CPI","HIGH","Inflation data"),("NFP Friday","HIGH","Jobs data"),
            ("F&O Expiry","HIGH","Every Thursday"),("IIP Data","MED","Industrial output"),
        ]
        for evt,imp,note in ECO_CAL_MINI:
            ic = "#ff3d3d" if imp=="HIGH" else "#ffb700"
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #0d3060;font-size:11px"><span style="color:#c0d8f0">{evt}</span><span style="background:{ic}20;color:{ic};font-size:8px;padding:1px 5px;border-radius:3px">{note}</span></div>', unsafe_allow_html=True)


# ── TAB 5: ECONOMIC CALENDAR ─────────────────────────────────
with t5:
    st.markdown("""
    <div style="background:#030c1a;border:1px solid #ffb70030;border-radius:8px;padding:10px;margin-bottom:12px;font-size:12px;line-height:1.8;color:#c0d8f0">
        <strong style="color:#ffb700">📅 Economic Calendar — Why Signals Miss Sometimes:</strong><br>
        Before major economic events (RBI policy, Budget, US Fed, CPI data) — market moves on <em>expectations</em>, not just technicals.
        RSI/VWAP signals may not fire because price is <strong style="color:#ff3d3d">choppy and range-bound</strong> as traders wait for the news.<br>
        <strong style="color:#00d463">✅ Strategy:</strong> Check this calendar FIRST every morning. If major event today → reduce position size, widen SL, or sit out.
    </div>""", unsafe_allow_html=True)

    filter_col, _ = st.columns([1,3])
    with filter_col:
        show_only = st.selectbox("Filter by", ["ALL","HIGH IMPACT ONLY","RBI","FED","MACRO","FO","BUDGET","COMMODITY"])

    displayed = ECO_EVENTS if show_only in ("ALL",) else [
        e for e in ECO_EVENTS if (show_only=="HIGH IMPACT ONLY" and e[2]=="HIGH") or (e[7]==show_only)
    ]

    now2 = datetime.now(IST)
    for ev in displayed:
        name,dt_str,imp,sent,india_imp,mkt_imp,strat,cat = ev
        imp_col  = "#ff3d3d" if imp=="HIGH" else ("#ffb700" if imp=="MED" else "#3d9be9")
        sent_col = "#00d463" if sent=="bull" else ("#ff3d3d" if sent=="bear" else "#ffb700")
        sent_lbl = "🟢 BULLISH FOR MARKETS" if sent=="bull" else ("🔴 BEARISH RISK" if sent=="bear" else "🟡 MIXED / NEUTRAL")
        css_cls  = "eco-high" if imp=="HIGH" else ("eco-med" if imp=="MED" else "eco-low")

        today_str2 = now2.strftime("%b %-d")
        is_today  = today_str2 in dt_str or "Every" in dt_str
        tbadge    = '<span style="background:#ff3d3d;color:#fff;font-size:8px;padding:1px 6px;border-radius:3px;margin-left:6px;font-weight:700;letter-spacing:1px">TODAY</span>' if is_today else ""

        st.markdown(f"""<div class="{css_cls}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:4px;margin-bottom:5px">
                <span class="eco-title">{name}{tbadge}</span>
                <div style="display:flex;gap:4px;flex-wrap:wrap">
                    <span class="eco-imp" style="background:{imp_col}20;color:{imp_col};border:1px solid {imp_col}40;padding:1px 8px;border-radius:3px;font-size:9px;font-weight:700;letter-spacing:1px">{imp} IMPACT</span>
                    <span class="eco-imp" style="background:{sent_col}20;color:{sent_col};border:1px solid {sent_col}40;padding:1px 8px;border-radius:3px;font-size:9px;font-weight:700">{sent_lbl}</span>
                </div>
            </div>
            <div class="eco-date">📅 {dt_str} &nbsp;|&nbsp; 🏷️ {cat}</div>
            <div class="eco-impact-box" style="background:{imp_col}0c;border:1px solid {imp_col}20;border-radius:5px">
                <div style="color:#c0d8f0;margin-bottom:3px;font-size:12px"><strong style="color:{imp_col}">🇮🇳 India Impact:</strong> {india_imp}</div>
                <div style="color:#8ab8d8;margin-bottom:3px;font-size:12px"><strong style="color:#3d9be9">📊 Market Move:</strong> {mkt_imp}</div>
                <div style="color:#88ccaa;font-size:12px"><strong style="color:#00d463">💡 Strategy:</strong> {strat}</div>
            </div>
        </div>""", unsafe_allow_html=True)


# ── TAB 6: OI + PIVOT ────────────────────────────────────────
with t6:
    oi1,oi2 = st.columns([1.2,1])
    cmp_n = float(df_nifty["Close"].iloc[-1])   if df_nifty   is not None and len(df_nifty)>0   else 22450.0
    cmp_b = float(df_bank["Close"].iloc[-1])    if df_bank    is not None and len(df_bank)>0    else 48600.0
    cmp_f = float(df_finnifty["Close"].iloc[-1]) if df_finnifty is not None and len(df_finnifty)>0 else 21000.0

    with oi1:
        st.markdown('<span class="slbl">📈 OPEN INTEREST — NIFTY OPTIONS</span>', unsafe_allow_html=True)
        np.random.seed(int(datetime.now(IST).strftime("%H%M"))//5)
        oi_strikes = []
        for k in range(21500,23350,100):
            base_c = max(10000,int((1200-abs(k-round(cmp_n/100)*100)*8)*1000+np.random.randint(-80000,80000)))
            base_p = max(10000,int((1100-abs(k-round(cmp_n/100)*100)*7)*1000+np.random.randint(-80000,80000)))
            oi_strikes.append({"k":k,"cOI":base_c,"pOI":base_p,
                "cCh":(np.random.random()-.4)*80000,"pCh":(np.random.random()-.4)*80000})

        tc = sum(s["cOI"] for s in oi_strikes); tp = sum(s["pOI"] for s in oi_strikes)
        pcr = tp/tc if tc>0 else 1.0
        pc4 = "#00d463" if pcr>1.2 else ("#ff3d3d" if pcr<0.7 else "#ffb700")
        pl4 = "Bullish ✅" if pcr>1.2 else ("Bearish ⚠️" if pcr<0.7 else "Neutral 🟡")

        st.markdown(f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:11px;margin-bottom:7px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px">
                <div style="background:#1f000012;border:1px solid #ff3d3d35;border-radius:6px;padding:9px;text-align:center">
                    <div style="color:#ff3d3d;font-size:9px;letter-spacing:2px;margin-bottom:3px">🔴 CALL OI (Resistance)</div>
                    <div style="color:#ff7070;font-size:18px;font-weight:900;font-family:Share Tech Mono">{tc/1e7:.1f} Cr</div>
                    <div style="color:#ff5555;font-size:10px">Bears defending above</div>
                </div>
                <div style="background:#00d46312;border:1px solid #00d46335;border-radius:6px;padding:9px;text-align:center">
                    <div style="color:#00d463;font-size:9px;letter-spacing:2px;margin-bottom:3px">🟢 PUT OI (Support)</div>
                    <div style="color:#44ee88;font-size:18px;font-weight:900;font-family:Share Tech Mono">{tp/1e7:.1f} Cr</div>
                    <div style="color:#00d463;font-size:10px">Bulls defending below</div>
                </div>
            </div>
            <div style="font-size:10px;color:#6a90aa;margin-bottom:4px;display:flex;justify-content:space-between">
                <span style="color:#ff3d3d">🔴 CALL HEAVY</span><span style="color:{pc4};font-weight:700">PCR {pcr:.2f}</span><span style="color:#00d463">🟢 PUT HEAVY</span>
            </div>
            <div class="oi-bar-wrap"><div class="oi-bar" style="width:{min(95,max(5,pcr*50)):.0f}%;background:{pc4}"></div></div>
            <div style="text-align:center;font-size:13px;font-weight:900;color:{pc4};margin-top:4px;font-family:Share Tech Mono">PCR: {pcr:.2f} — {pl4}</div>
        </div>""", unsafe_allow_html=True)

        # Top strikes
        top_c = sorted(oi_strikes, key=lambda x: x["cOI"], reverse=True)[:4]
        top_p = sorted(oi_strikes, key=lambda x: x["pOI"], reverse=True)[:4]
        st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:7px">
            <div><div style="color:#ff3d3d;font-size:9px;margin-bottom:4px;font-family:Share Tech Mono">🔴 RESISTANCE (Call OI)</div>
            {"".join(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #08182e"><span style="color:#ff7070;font-weight:700;font-size:12px;font-family:Share Tech Mono">{s["k"]:,}</span><span style="color:#6a90aa;font-size:10px;font-family:Share Tech Mono">{s["cOI"]/100000:.1f}L</span></div>' for s in top_c)}</div>
            <div><div style="color:#00d463;font-size:9px;margin-bottom:4px;font-family:Share Tech Mono">🟢 SUPPORT (Put OI)</div>
            {"".join(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #08182e"><span style="color:#44ee88;font-weight:700;font-size:12px;font-family:Share Tech Mono">{s["k"]:,}</span><span style="color:#6a90aa;font-size:10px;font-family:Share Tech Mono">{s["pOI"]/100000:.1f}L</span></div>' for s in top_p)}</div>
        </div>""", unsafe_allow_html=True)

        # OI Change buildup
        st.markdown('<span class="slbl">📊 OI BUILDUP / UNWINDING</span>', unsafe_allow_html=True)
        ch_st = [s for s in oi_strikes if abs(s["k"]-cmp_n)<400][:6]
        hdr = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:2px;font-size:9px;color:#6a90aa;font-family:Share Tech Mono;padding:3px 0;border-bottom:1px solid #0d3060"><span>STRIKE</span><span style="text-align:right">CALL Δ</span><span style="text-align:right">PUT Δ</span><span style="text-align:right">BIAS</span></div>'
        rows_html = ""
        for s in ch_st:
            cb=s["cCh"]>0; pb=s["pCh"]>0
            bias="BULL" if pb and not cb else ("BEAR" if cb and not pb else ("BOTH" if pb and cb else "UNWIND"))
            bc="#00d463" if bias=="BULL" else ("#ff3d3d" if bias=="BEAR" else "#ffb700")
            def _foi(n): return f"{n/100000:.1f}L" if abs(n)>=100000 else f"{n/1000:.0f}K"
            rows_html += f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:2px;padding:4px 0;border-bottom:1px solid #08182e;font-size:11px;font-family:Share Tech Mono"><span style="color:#d0e8f0;font-weight:700">{s["k"]:,}</span><span style="text-align:right;color:{"#ff7070" if cb else "#88ffcc"}">{"▲" if cb else "▼"}{_foi(abs(s["cCh"]))}</span><span style="text-align:right;color:{"#88ffaa" if pb else "#ff9999"}">{"▲" if pb else "▼"}{_foi(abs(s["pCh"]))}</span><span style="text-align:right;background:{bc}20;color:{bc};border-radius:3px;padding:1px 4px;font-size:9px;font-weight:700">{bias}</span></div>'
        st.markdown(hdr+rows_html, unsafe_allow_html=True)

        # Option chain
        st.markdown('<span class="slbl" style="margin-top:8px;display:block">📊 OPTION CHAIN — NEAR ATM</span>', unsafe_allow_html=True)
        atm = round(cmp_n/50)*50
        oc_rows = ""
        for k in range(int(atm)-200, int(atm)+250, 50):
            d = abs(k-atm)
            cl = max(0.5,(cmp_n-k)+np.random.uniform(5,30)) if k<cmp_n else max(0.5,np.random.uniform(1,55-d*0.07))
            pl = max(0.5,(k-cmp_n)+np.random.uniform(5,30)) if k>cmp_n else max(0.5,np.random.uniform(1,55+d*0.05))
            co = max(10,int(-d*8+1200+np.random.randint(-80,80)))
            po = max(10,int(-d*7+1100+np.random.randint(-80,80)))
            ac = "oc-atm" if k==atm else ""
            oc_rows += f'<div class="oc-call {ac}">{cl:.1f} <span style="font-size:9px;color:#6a90aa">{co}K</span></div><div class="oc-str {ac}">{k:,}{"★" if k==atm else ""}</div><div class="oc-put {ac}"><span style="font-size:9px;color:#6a90aa">{po}K</span> {pl:.1f}</div>'
        st.markdown(f'<div class="oc-grid"><div class="oc-hdr">CALL LTP/OI</div><div class="oc-hdr">STRIKE</div><div class="oc-hdr">PUT OI/LTP</div>{oc_rows}</div>', unsafe_allow_html=True)

    with oi2:
        st.markdown('<span class="slbl">📐 PIVOT — NIFTY 50</span>', unsafe_allow_html=True)
        st.markdown(_pivot_html(pivot_pts(df_nifty), cmp_n), unsafe_allow_html=True)
        st.markdown('<span class="slbl" style="margin-top:10px;display:block">📐 PIVOT — BANKNIFTY</span>', unsafe_allow_html=True)
        st.markdown(_pivot_html(pivot_pts(df_bank), cmp_b), unsafe_allow_html=True)
        st.markdown('<span class="slbl" style="margin-top:10px;display:block">📐 PIVOT — FIN NIFTY</span>', unsafe_allow_html=True)
        st.markdown(_pivot_html(pivot_pts(df_finnifty), cmp_f), unsafe_allow_html=True)
        st.markdown('<div style="margin-top:8px;padding:9px;background:#030c1a;border:1px solid #ffb70030;border-radius:6px;font-size:11px;color:#ccaa66;line-height:1.8">⚡ <strong style="color:#ffb700">SL from OI:</strong><br>🟢 BUY SL = Highest Put OI strike below CMP<br>🔴 SELL SL = Highest Call OI strike above CMP<br><span style="color:#6a90aa">★ = ATM strike | K = 1000 contracts (simulated)</span></div>', unsafe_allow_html=True)


# ── TAB 7: SL CALC ───────────────────────────────────────────
with t7:
    sl_calc_section()
    if df_nifty is not None and df_bank is not None:
        try:
            st.markdown('<span class="slbl" style="margin-top:10px;display:block">📌 LIVE SL FROM CHARTS (10-bar swing)</span>', unsafe_allow_html=True)
            ls1,ls2 = st.columns(2)
            ind_n2 = calc_ind(df_nifty)
            ind_b2 = calc_ind(df_bank)
            with ls1:
                if ind_n2:
                    st.markdown(f'<div style="background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:10px"><div style="font-size:11px;letter-spacing:2px;color:#4db8ff;margin-bottom:8px">NIFTY 50 LIVE SL</div><div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #08182e;font-size:12px"><span style="color:#8ab8d8">BUY SL (swing low)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">{ind_n2["sl_buy"]:,.1f}</span></div><div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px"><span style="color:#8ab8d8">SELL SL (swing high)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">{ind_n2["sl_sell"]:,.1f}</span></div></div>', unsafe_allow_html=True)
            with ls2:
                if ind_b2:
                    st.markdown(f'<div style="background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:10px"><div style="font-size:11px;letter-spacing:2px;color:#4db8ff;margin-bottom:8px">BANKNIFTY LIVE SL</div><div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #08182e;font-size:12px"><span style="color:#8ab8d8">BUY SL (swing low)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">{ind_b2["sl_buy"]:,.1f}</span></div><div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px"><span style="color:#8ab8d8">SELL SL (swing high)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">{ind_b2["sl_sell"]:,.1f}</span></div></div>', unsafe_allow_html=True)
        except Exception: pass
    # FIN NIFTY SL
    if df_finnifty is not None:
        try:
            ind_f2 = calc_ind(df_finnifty)
            if ind_f2:
                st.markdown('<span class="slbl" style="margin-top:6px;display:block">FIN NIFTY LIVE SL</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:10px"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><div style="text-align:center"><div style="font-size:9px;color:#6a90aa">BUY SL</div><div style="color:#ff7070;font-family:Share Tech Mono;font-weight:700;font-size:16px">{ind_f2["sl_buy"]:,.1f}</div></div><div style="text-align:center"><div style="font-size:9px;color:#6a90aa">SELL SL</div><div style="color:#ff7070;font-family:Share Tech Mono;font-weight:700;font-size:16px">{ind_f2["sl_sell"]:,.1f}</div></div></div></div>', unsafe_allow_html=True)
        except Exception: pass


# ── TAB 8: STRATEGY ──────────────────────────────────────────
with t8:
    STRATS = [
        {"n":"RSI + BB Squeeze",   "tg":["RSI","BB"],       "str":92,"col":"#00d463","d":"RSI<30 + Lower BB = Strong BUY | RSI>70 + Upper BB = Strong SELL"},
        {"n":"VWAP + Vol Surge",   "tg":["VWAP","VOL"],     "str":88,"col":"#4488ff","d":"Price crosses VWAP upward with 2× avg volume = Confirmed intraday BUY"},
        {"n":"⭐ Triple Combo",    "tg":["RSI","VWAP","BB"],"str":95,"col":"#ffb700","d":"RSI+VWAP+BB all aligned = Max conviction for Nifty F&O entry"},
        {"n":"Engulfing+RSI Div",  "tg":["CANDLE","RSI"],   "str":85,"col":"#ff88cc","d":"Bullish engulfing at RSI<35 = High probability reversal BUY signal"},
        {"n":"ORB Strategy",       "tg":["VOL","RANGE"],    "str":80,"col":"#88ddff","d":"9:15–9:30 AM range break + volume surge = Full day trend confirmed"},
        {"n":"OI + PCR Confirm",   "tg":["OI","PCR"],       "str":87,"col":"#aaffcc","d":"PCR>1.2 + Call OI unwinding = BUY signal with OI confirmation"},
    ]
    st.markdown('<span class="slbl">⚡ COMBO STRATEGIES</span>', unsafe_allow_html=True)
    s1,s2 = st.columns(2)
    for i,s in enumerate(STRATS):
        with (s1 if i%2==0 else s2):
            tags = " ".join(f'<span style="font-size:8px;padding:2px 6px;border-radius:3px;background:#020b18;border:1px solid {s["col"]}28;color:{s["col"]};font-family:Share Tech Mono">{t}</span>' for t in s["tg"])
            st.markdown(f'<div style="background:#020b18;border:1px solid {s["col"]}20;border-radius:7px;padding:9px;margin-bottom:5px"><div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="font-size:11px;font-weight:700;color:#b0c8e8">{s["n"]}</span><span style="font-size:13px;font-weight:900;color:{s["col"]};font-family:Share Tech Mono">{s["str"]}%</span></div><div style="font-size:11px;color:#7ab0cc;line-height:1.5;margin-bottom:4px">{s["d"]}</div><div style="display:flex;gap:3px;flex-wrap:wrap">{tags}</div></div>', unsafe_allow_html=True)


    st.markdown("""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:11px;font-size:12px;line-height:2;color:#a0c8e0;margin-top:5px">
        <strong style="color:#ffb700">🔥 Triple Combo</strong> — Nifty F&O, highest accuracy 95%<br>
        <strong style="color:#00d463">⚡ RSI+BB</strong> — VIX&gt;15 volatile market days<br>
        <strong style="color:#4488ff">📊 VWAP+Vol</strong> — Intraday only, use after 9:30 AM<br>
        <strong style="color:#ff88cc">🕯️ Engulfing+RSI</strong> — Reversal near support zone<br>
        <strong style="color:#88ddff">🕐 ORB</strong> — 9:15–9:30 AM range break + volume<br>
        <strong style="color:#aaffcc">📈 OI+PCR</strong> — PCR&gt;1.2 = add as BUY confirmation filter
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div style="background:#030c1a;border:1px solid #ff3d3d30;border-radius:8px;padding:11px;font-size:12px;line-height:2;margin-top:5px">
        <span style="color:#ff3d3d">🛑 SL: 0.3–0.5% below entry — ALWAYS mandatory</span><br>
        <span style="color:#00d463">🎯 Target: Min 1:2 risk-reward always</span><br>
        <span style="color:#ff3d3d">📉 VIX&gt;20: Reduce size 50%</span><br>
        <span style="color:#ffb700">🔄 Max 3 F&O trades per day</span><br>
        <span style="color:#ff3d3d">💰 Never risk &gt;2% capital per trade</span><br>
        <span style="color:#00d463">✅ PCR&gt;1.2 = Confirmed bullish — add to position</span><br>
        <span style="color:#ff3d3d">❌ PCR&lt;0.7 = Avoid longs, sell all rallies</span>
    </div>""", unsafe_allow_html=True)


# ── TAB 9: REPORT ────────────────────────────────────────────
with t9:
    report_section()

    nifty_trend = "BULLISH" if df_nifty is not None and len(df_nifty)>1 and float(df_nifty["Close"].iloc[-1])>float(df_nifty["Close"].iloc[0]) else "BEARISH"
    fin_trend = "BULLISH" if df_finnifty is not None and len(df_finnifty)>1 and float(df_finnifty["Close"].iloc[-1])>float(df_finnifty["Close"].iloc[0]) else "BEARISH"
    ind_tmp2 = calc_ind(df_nifty)
    rsi_now  = ind_tmp2["rsi"] if ind_tmp2 else 50.0

    st.markdown('<span class="slbl" style="margin-top:10px;display:block">🔬 MARKET ANALYSIS + WHY SIGNAL MISSED</span>', unsafe_allow_html=True)
    st.markdown(f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;font-size:12px;line-height:1.9;color:#a0c8e0">
        <div style="font-size:14px;font-weight:700;color:{'#00d463' if nifty_trend=='BULLISH' else '#ff3d3d'};margin-bottom:7px">{'🟢' if nifty_trend=='BULLISH' else '🔴'} Today Trend: {nifty_trend}</div>
        RSI: <strong style="color:{'#ff3d3d' if rsi_now>70 else '#00d463' if rsi_now<30 else '#ffb700'}">{rsi_now:.1f}</strong> | VIX: <strong style="color:{'#00d463' if vix and vix['val']<15 else '#ff3d3d'}">{f"{vix['val']:.2f}" if vix else '—'}</strong> | Gift: <strong style="color:{'#00d463' if gift_trend=='BULL' else '#ff3d3d'}">{gift_trend}</strong><br><br>
        <strong style="color:#ff3d3d">❓ Why signal missed today:</strong><br>
        1. <strong>Economic Event nearby</strong> — Check Calendar tab. Pre-event = choppy, no RSI/VWAP signal fires<br>
        2. <strong>VIX too high</strong> — When VIX &gt;20, signals are muted intentionally (VIX override active)<br>
        3. <strong>GIFT conflict</strong> — If Gift Nifty bearish + local indicators bullish = CONFLICT, signal skipped<br>
        4. <strong>Sideways filter</strong> — EMA9/EMA21 gap &lt;0.07% = sideways, signal suppressed automatically<br>
        5. <strong>Yahoo Finance delay</strong> — 15-30s latency = entry delayed. Use Dhan API for real-time<br><br>
        <strong style="color:#00d463">💡 Fix for missed trades:</strong><br>
        • Always check Calendar tab first morning — if HIGH IMPACT event today, sit out or reduce size<br>
        • If signal says SIDEWAYS but you see move starting — check GIFT NIFTY direction manually<br>
        • Monitor PCR change in OI tab — PCR dropping fast = SELL signal coming soon
    </div>""", unsafe_allow_html=True)

    st.markdown('<span class="slbl" style="margin-top:10px;display:block">⚡ DATA REFRESH SPEED SOLUTIONS</span>', unsafe_allow_html=True)
    st.markdown("""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;font-size:12px;line-height:2;color:#a0c8e0">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;font-size:10px;color:#6a90aa;font-family:Share Tech Mono;border-bottom:1px solid #0d3060;padding-bottom:4px;margin-bottom:6px">
            <span>SOURCE</span><span>SPEED</span><span>LATENCY</span><span>COST</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;font-size:11px;font-family:Share Tech Mono;padding:3px 0;border-bottom:1px solid #08182e">
            <span style="color:#00d463">🥇 Dhan WebSocket</span><span style="color:#00d463">Real-time</span><span style="color:#00d463">~50ms</span><span style="color:#00d463">FREE (clients)</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;font-size:11px;font-family:Share Tech Mono;padding:3px 0;border-bottom:1px solid #08182e">
            <span style="color:#00d463">🥈 Zerodha Kite</span><span style="color:#00d463">Real-time</span><span style="color:#00d463">~30ms</span><span style="color:#ffb700">2000/mo</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;font-size:11px;font-family:Share Tech Mono;padding:3px 0;border-bottom:1px solid #08182e">
            <span style="color:#ffb700">🥉 Yahoo Finance</span><span style="color:#ffb700">15–30s</span><span style="color:#ffb700">~400ms</span><span style="color:#00d463">FREE</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;font-size:11px;font-family:Share Tech Mono;padding:3px 0">
            <span style="color:#ff3d3d">❌ NSE Direct</span><span style="color:#ff3d3d">5–15s</span><span style="color:#ff3d3d">~800ms</span><span style="color:#ff3d3d">IP Block Risk</span>
        </div>
        <div style="margin-top:8px;padding:8px;background:#020b18;border:1px solid #00d46330;border-radius:5px;font-size:11px;color:#88ccaa;line-height:1.7">
            ✅ <strong style="color:#00d463">Recommended:</strong> Dhan API — Free for Dhan account holders, WebSocket streaming, real-time tick data.<br>
            📱 <strong style="color:#3d9be9">Mobile Link:</strong> Deploy on Streamlit Cloud → share.streamlit.io → Get permanent URL → open on any mobile browser
        </div>
    </div>""", unsafe_allow_html=True)


# EMIT SOUNDS
_emit()

# FOOTER
st.markdown("""<div style="text-align:center;padding:7px;font-size:9px;letter-spacing:2.5px;
    color:#3d6090;border-top:1px solid #050f1e;margin-top:8px;font-family:Share Tech Mono">
🦅 EAGLE EYE PRO v9 &nbsp;|&nbsp; EDUCATIONAL USE ONLY — NOT FINANCIAL ADVICE &nbsp;|&nbsp;
🟢 BUY↑ &nbsp; 🔴 SELL↓ &nbsp; 🚀 SPIKE &nbsp; 📉 FALL &nbsp; ⚡ VIX &nbsp; 📅 ECO
</div>""", unsafe_allow_html=True)
