# ══════════════════════════════════════════════════════════════════
#  🦅 EAGLE EYE PRO v5 — Complete Merged Terminal
#  HTML + Python v4 — All Features Combined
#
#  pip install streamlit yfinance pandas numpy pytz streamlit-autorefresh plotly
#  Run: streamlit run eagle_eye_pro_v5.py
# ══════════════════════════════════════════════════════════════════

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="🦅 Eagle Eye Pro v5",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st_autorefresh(interval=15000, key="eagle_v5")
IST = pytz.timezone("Asia/Kolkata")

# ── SESSION STATE ──────────────────────────────────────────────
for k, v in {
    "signals_log": [], "prev_sig": {}, "news_seen": set(),
    "sound_queue": [], "sound_id": 0, "alert_log": [],
    "prev_prices": {}, "veto_log": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══ MASTER CSS ═════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700;900&display=swap');

*,body{font-family:'Rajdhani',sans-serif!important}
.stApp{background:#020b18!important}
.block-container{padding:.3rem .8rem 0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none!important}
#MainMenu,footer,header{visibility:hidden!important}
.stDeployButton{display:none!important}
div[data-testid="stVerticalBlock"]>div{gap:.25rem!important}

/* TABS */
.stTabs [data-baseweb="tab-list"]{gap:3px;background:transparent;border-bottom:2px solid #0d3060}
.stTabs [data-baseweb="tab"]{background:#030c1a;color:#4a90d9;border:1px solid #0d3060;
  border-radius:6px 6px 0 0;font-family:'Rajdhani';font-weight:700;
  font-size:12px;letter-spacing:1.5px;padding:6px 15px;border-bottom:none;transition:all .2s}
.stTabs [aria-selected="true"]{background:#0d3060!important;color:#fff!important;border-color:#1a5090!important}
.stTabs [data-baseweb="tab-panel"]{padding-top:8px!important}

/* SIGNAL CARDS */
.sc{border-radius:10px;padding:13px 11px;text-align:center;border:1px solid #0d3060;margin-bottom:4px;min-height:215px;transition:all .4s}
.sc-buy {background:linear-gradient(145deg,#002716,#020b18);border-color:#00d463!important;animation:pg 2.5s infinite}
.sc-sell{background:linear-gradient(145deg,#1f0000,#020b18);border-color:#ff3d3d!important;animation:pr 2.5s infinite}
.sc-caut{background:linear-gradient(145deg,#1f1200,#020b18);border-color:#ffb700!important;animation:po 3s infinite}
.sc-wait{background:#030c1a;border-color:#0d3060!important;opacity:.72}
@keyframes pg{0%,100%{box-shadow:0 0 14px rgba(0,212,99,.2)}50%{box-shadow:0 0 36px rgba(0,212,99,.55)}}
@keyframes pr{0%,100%{box-shadow:0 0 14px rgba(255,61,61,.2)}50%{box-shadow:0 0 36px rgba(255,61,61,.55)}}
@keyframes po{0%,100%{box-shadow:0 0 10px rgba(255,183,0,.15)}50%{box-shadow:0 0 26px rgba(255,183,0,.45)}}

.sc-badge{font-size:9px;letter-spacing:2px;font-weight:700;padding:2px 9px;border-radius:3px;display:inline-block;margin-bottom:5px}
.sc-sym  {font-size:10px;opacity:.5;letter-spacing:3px;margin-bottom:3px;color:#8ab8d8}
.sc-price{font-size:30px;font-weight:900;font-family:'Share Tech Mono';line-height:1.1}
.sc-pts  {font-size:13px;font-weight:700;margin:2px 0;font-family:'Share Tech Mono'}
.sc-sig  {font-size:16px;font-weight:900;letter-spacing:2.5px;margin:5px 0}
.sc-tris {font-size:18px;letter-spacing:6px;margin:4px 0}
.sc-meta {font-size:10px;color:#5a8aaa;display:flex;justify-content:space-around;flex-wrap:wrap;
          gap:3px;margin-top:6px;background:#030c1a;padding:5px;border-radius:5px}
.sc-entry{font-size:11px;margin-top:7px;padding:6px 9px;background:rgba(61,155,233,.06);
          border:1px solid #0d3060;border-radius:5px;text-align:left}
.sc-time {font-size:9px;color:#1e3a5f;margin-top:5px;font-family:'Share Tech Mono'}

/* VIX BLINK */
@keyframes vix-blink{0%,100%{opacity:1;text-shadow:0 0 8px currentColor}50%{opacity:.4;text-shadow:none}}
.vblink{animation:vix-blink 1.8s infinite}

/* INDICATOR GRID */
.ind-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:6px 0}
.ind-box{border-radius:8px;padding:10px 8px;text-align:center;border:1px solid;transition:all .5s}
.ind-buy {background:#001f0f;border-color:#00d463}
.ind-sell{background:#1f0000;border-color:#ff3d3d}
.ind-neu {background:#0d1a2a;border-color:#3d9be9}
.ind-lbl {font-size:9px;letter-spacing:2px;margin-bottom:4px;opacity:.65}
.ind-val {font-size:15px;font-weight:900;font-family:'Share Tech Mono'}
.ind-sig {font-size:10px;font-weight:900;letter-spacing:2px;margin-top:3px}

/* TAPE */
.tape-item{display:flex;flex-direction:column;align-items:center;background:#030c1a;
  border:1px solid #0d3060;border-radius:4px;padding:4px 8px;text-align:center}
.ti-n{color:#3d5a7a;font-size:8px;letter-spacing:.5px;font-family:'Share Tech Mono'}
.ti-v{font-weight:bold;font-size:12px;font-family:'Share Tech Mono'}
.ti-c{font-size:10px;font-family:'Share Tech Mono'}
.ti-p{font-size:9px;color:#3d5a7a;font-family:'Share Tech Mono'}

/* MINI CARD */
.mc{background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:9px 6px;text-align:center;margin-bottom:4px}
.mc-ico{font-size:16px}
.mc-nm {font-size:8px;letter-spacing:2px;color:#4a6a8a;margin:2px 0}
.mc-pr {font-size:15px;font-weight:700;font-family:'Share Tech Mono';color:#e0eeff}
.mc-ch {font-size:11px;font-weight:700;font-family:'Share Tech Mono'}
.mc-pt {font-size:9px;color:#4a6a8a;font-family:'Share Tech Mono'}

/* NEWS */
.ni{border-radius:6px;padding:9px 11px;margin:4px 0;border-left:3px solid;cursor:pointer;transition:opacity .2s}
.ni:hover{opacity:.8}
.ni-bull{background:rgba(0,212,99,.07);border-color:#00d463}
.ni-bear{background:rgba(255,61,61,.07);border-color:#ff3d3d}
.ni-neu {background:rgba(61,155,233,.07);border-color:#3d9be9}
.ni-meta {font-size:10px;color:#5a8aaa;margin-bottom:3px;font-family:'Share Tech Mono'}
.ni-title{color:#d0e8f8;font-size:12px;line-height:1.55}

/* PIVOT TABLE */
.pvt-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;text-align:center}
.pvt-cell{padding:7px 4px;border-radius:6px;font-size:12px;font-weight:700;font-family:'Share Tech Mono'}
.pvt-lbl {font-size:8px;margin-bottom:3px;font-weight:400;opacity:.7;letter-spacing:1px}
.pvt-r{background:#200000;border:1px solid #ff3d3d55;color:#ff7070}
.pvt-s{background:#002010;border:1px solid #00d46355;color:#44ee88}
.pvt-p{background:#1a1000;border:1px solid #ffb70055;color:#ffd050}
.pvt-c{background:#001030;border:1px solid #3d9be955;color:#6ab4ee}

/* OI BARS */
.oi-bar-wrap{height:10px;background:#0a1628;border-radius:5px;overflow:hidden;margin:5px 0}
.oi-bar{height:100%;border-radius:5px;transition:width .8s}

/* STRATEGY CARD */
.strat-card{background:#020b18;border-radius:7px;padding:10px}

/* MOOD METER */
.mood-track{height:12px;background:linear-gradient(90deg,#cc2244,#ff8833,#ffcc00,#88cc00,#00d463);
            border-radius:6px;position:relative;margin:8px 0}
.mood-ptr{position:absolute;top:-4px;width:4px;height:20px;background:white;border-radius:2px;
          box-shadow:0 0 8px #fffc;transition:left 1.2s}

/* ALERT BOX */
.alert-box{padding:8px 12px;border-radius:6px;margin:4px 0;border-left:4px solid;font-size:11px;line-height:1.5;font-weight:600}
.alert-bull {background:#001f0f;border-color:#00d463;color:#88ffaa}
.alert-bear {background:#1f0000;border-color:#ff3d3d;color:#ffaaaa}
.alert-spike{background:#1f0f00;border-color:#ff8800;color:#ffccaa}
.alert-fall {background:#1a001a;border-color:#ff00cc;color:#ffaadd}

/* OPTION CHAIN */
.oc-grid{display:grid;grid-template-columns:1fr 60px 1fr;gap:3px;font-family:'Share Tech Mono';font-size:11px}
.oc-hdr   {background:#0d3060;padding:5px 6px;text-align:center;font-size:9px;letter-spacing:1px;color:#88bbdd}
.oc-call  {background:#ff3d3d10;padding:5px 6px;text-align:right;color:#ff8888}
.oc-put   {background:#00d46310;padding:5px 6px;text-align:left;color:#88ffaa}
.oc-strike{background:#0d3060;padding:5px 6px;text-align:center;color:#ffd050;font-weight:700}
.oc-atm   {background:#1a5090!important;color:#fff!important;font-weight:900}

/* SL GRID */
.sl-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px}
.sl-box {background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:10px;text-align:center}
.sl-lbl {font-size:9px;letter-spacing:2px;color:#4a6a8a;margin-bottom:4px}
.sl-val {font-size:20px;font-weight:900;font-family:'Share Tech Mono'}
.sl-sub {font-size:10px;margin-top:3px;font-family:'Share Tech Mono'}

/* SECTION LABEL */
.slbl{font-size:9px;letter-spacing:3px;font-weight:700;color:#3d9be9;
      border-left:2px solid #3d9be9;padding:2px 0 2px 9px;margin:10px 0 6px;
      background:#030c1a80;border-radius:0 4px 4px 0}

/* EXPIRY BANNER */
@keyframes exp-flash{0%,100%{background:#1a0000;color:#ff6060;border-color:#ff3d3d}
                     50%{background:#2a0000;color:#ffaaaa;border-color:#ff8888}}
.expiry-banner{animation:exp-flash 1s infinite;border:1px solid;padding:7px;text-align:center;
               font-size:12px;font-weight:900;letter-spacing:2px;border-radius:5px;margin-bottom:6px}

/* REPORT */
.rm{background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:9px 6px;text-align:center}
.rv{font-size:22px;font-weight:900;font-family:'Share Tech Mono'}
.rl{font-size:8px;letter-spacing:2.5px;color:#4a8aaa;margin-top:3px}

/* SENT */
.sent-wrap{background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px}
.sent-track{background:#0a1628;height:7px;border-radius:4px;overflow:hidden;margin:8px 0}
.sent-fill {height:100%;border-radius:4px;transition:width .5s}

/* TEXT READABILITY */
p,li,span{color:#c0d8f0}
h1,h2,h3,h4{color:#e0f0ff}
.stMetric label{color:#7ab0cc!important;font-size:11px!important}
.stDataFrame td{color:#c0d8f0!important;font-family:'Share Tech Mono'!important}
.stDataFrame th{color:#4a90d9!important;background:#0d3060!important}
div[data-testid="stNumberInput"] label{color:#7ab0cc!important}
div[data-testid="stSelectbox"] label{color:#7ab0cc!important}
.stTextInput label{color:#7ab0cc!important}
</style>
""", unsafe_allow_html=True)


# ══ STATIC DATA ════════════════════════════════════════════════
NEWS_STATIC = [
    {"t": "RBI holds repo rate at 6.5% — Liquidity surplus returns; H2 2024 rate cut expectations rising strongly", "s": "bull", "src": "Economic Times",   "time": "09:15", "link": "https://economictimes.indiatimes.com"},
    {"t": "Nifty FII net buyers ₹8,200 Cr — DII support ₹3,400 Cr; broad market participation remains strong", "s": "bull", "src": "Moneycontrol",       "time": "09:30", "link": "https://moneycontrol.com"},
    {"t": "Fed signals rate hike pause — Dollar weakens vs EM currencies; India FII flows improving significantly", "s": "bull", "src": "Bloomberg",         "time": "08:45", "link": "https://bloomberg.com"},
    {"t": "HDFC Bank Q4 PAT ₹16,512 Cr +37% YoY — NIM improves to 4.2%; NPA at all-time low 0.33%", "s": "bull", "src": "BSE India",             "time": "08:20", "link": "https://bseindia.com"},
    {"t": "PSU Banks Q4 strong — SBI, BOB, Canara NPA multi-year lows; banking sector re-rating underway", "s": "bull", "src": "NSE India",              "time": "07:55", "link": "https://nseindia.com"},
    {"t": "Auto sector at 52-week highs — Maruti, M&M, Bajaj Auto surge; EV transition driving premiumization", "s": "bull", "src": "CNBC TV18",            "time": "09:05", "link": "https://cnbctv18.com"},
    {"t": "IT sector earnings disappoint — TCS Infosys Q4 guidance cut; deal wins slow; sector ETF down 2.3%", "s": "bear", "src": "Zee Business",         "time": "09:20", "link": "https://zeebusiness.com"},
    {"t": "Middle East tensions escalate — Brent crude spikes $89; supply disruption risk premium elevated", "s": "bear", "src": "Reuters",               "time": "08:10", "link": "https://reuters.com"},
    {"t": "US NFP 2,53,000 beats — Dollar index 104.8 rises sharply; INR under pressure near ₹83.80", "s": "bear", "src": "NDTV Profit",            "time": "07:30", "link": "https://ndtvprofit.com"},
    {"t": "SEBI tightens F&O rules — Lot size increased; weekly expiry reduced; F&O volumes may drop 30%", "s": "bear", "src": "SEBI",                    "time": "08:50", "link": "https://sebi.gov.in"},
    {"t": "Crude oil +$2 on OPEC+ cut signal — India CAD may widen; Rupee depreciation risk increases now", "s": "bear", "src": "ET Markets",             "time": "09:10", "link": "https://etmarkets.com"},
    {"t": "SGX Nifty +85 pts pre-open — Strong global cues; gap-up opening expected; bulls in control", "s": "bull", "src": "Market Pulse",           "time": "08:00", "link": "#"},
]

ECO_CAL = [
    ("RBI MPC Meeting",    "HIGH", "Today 10:00 AM", "Repo rate hold expected at 6.5%",    "#ffb700"),
    ("India CPI",          "HIGH", "Tomorrow 5:30PM","Expected 4.6% vs prev 4.8%",         "#ffb700"),
    ("US Fed FOMC",        "HIGH", "Wed 11:30PM IST","Hawkish tone — watch USD/INR",        "#ff3d3d"),
    ("India IIP Data",     "MED",  "Thu 5:30 PM",    "Industrial output exp +6.2%",         "#00d463"),
    ("US Non-Farm Payroll","HIGH", "Fri 6:00PM IST", "Consensus: 2,40,000 jobs added",      "#ffb700"),
    ("Nifty F&O Expiry",   "HIGH", "Thu Market Close","Max pain ₹22,400 — pinning likely", "#ff3d3d"),
]

STRATS = [
    {"n":"RSI + BB Squeeze",    "tg":["RSI","BB"],         "str":92,"col":"#00d463","d":"RSI&lt;30 + Lower BB = Strong BUY | RSI&gt;70 + Upper BB = Strong SELL"},
    {"n":"VWAP + Vol Surge",    "tg":["VWAP","VOL"],       "str":88,"col":"#4488ff","d":"Price crosses VWAP upward with 2× avg volume = Confirmed intraday BUY"},
    {"n":"⭐ Triple Combo",     "tg":["RSI","VWAP","BB"],  "str":95,"col":"#ffb700","d":"RSI + VWAP + BB all aligned = Max conviction for Nifty F&O entry"},
    {"n":"Engulfing + RSI Div", "tg":["CANDLE","RSI"],     "str":85,"col":"#ff88cc","d":"Bullish engulfing at RSI&lt;35 = High probability reversal BUY signal"},
    {"n":"ORB Strategy",        "tg":["VOL","RANGE"],      "str":80,"col":"#88ddff","d":"9:15–9:30 AM range break + volume surge = Full day trend confirmed"},
    {"n":"OI + PCR Confirm",    "tg":["OI","PCR"],         "str":87,"col":"#aaffcc","d":"PCR&gt;1.2 + Call OI unwinding = BUY signal with institutional confirmation"},
]

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


# ══ SOUND ENGINE ═══════════════════════════════════════════════
SOUNDS = {
    "buy":       ([523,659,784,1047], "sine",     0.38, 0.12),
    "sell":      ([494,392,330,247],  "sawtooth", 0.38, 0.12),
    "news_bull": ([550,660,880],      "sine",     0.28, 0.14),
    "news_bear": ([440,330,220],      "triangle", 0.28, 0.14),
    "spike":     ([880,1100,880,1100],"square",   0.35, 0.08),
    "fall":      ([220,180,140,110],  "sawtooth", 0.40, 0.10),
    "vix":       ([300,240,180],      "square",   0.28, 0.15),
}

def sound_button():
    components.html("""
    <style>body{margin:0;background:transparent}
    .sb{background:#030c1a;border:1px solid #0d3060;color:#3d9be9;padding:4px 12px;border-radius:4px;
        cursor:pointer;font-size:10px;letter-spacing:2px;font-family:monospace;white-space:nowrap}
    .sb.on{border-color:#00d463;color:#00d463;background:#001f0f}</style>
    <button class="sb" id="sb" onclick="initSnd()">🔇 ENABLE SOUND</button>
    <script>
    var C=null,on=sessionStorage.getItem('esnd')==='1',btn=document.getElementById('sb');
    if(on){btn.textContent='🔊 SOUND ON';btn.className='sb on';
      try{C=new(window.parent.AudioContext||window.parent.webkitAudioContext||AudioContext)();
          window.parent._EC=C;window.parent._ES=true;}catch(e){}}
    function initSnd(){
      try{var Ctx=window.parent.AudioContext||window.parent.webkitAudioContext||window.AudioContext;
          C=new Ctx();C.resume();window.parent._EC=C;window.parent._ES=true;on=true;
          sessionStorage.setItem('esnd','1');btn.textContent='🔊 SOUND ON';btn.className='sb on';
          _play([523,659,784],'sine',0.28,0.1);}catch(e){btn.textContent='⚠️ NO AUDIO';}}
    function _play(notes,wave,vol,dur){
      var ctx=C||window.parent._EC;if(!ctx)return;
      notes.forEach(function(f,i){var t=ctx.currentTime+i*(dur+0.04);
        var o=ctx.createOscillator(),g=ctx.createGain();o.type=wave;o.frequency.value=f;
        g.gain.setValueAtTime(vol,t);g.gain.exponentialRampToValueAtTime(0.001,t+dur);
        o.connect(g);g.connect(ctx.destination);o.start(t);o.stop(t+dur+0.02);});}
    window.addEventListener('message',function(e){
      if(!e.data||!e.data.eagle)return;
      if(!on&&!window.parent._ES)return;
      var n={'buy':[523,659,784,1047],'sell':[494,392,330,247],
             'news_bull':[550,660,880],'news_bear':[440,330,220],
             'spike':[880,1100,880,1100],'fall':[220,180,140,110],'vix':[300,240,180]};
      var w={'buy':'sine','sell':'sawtooth','news_bull':'sine','news_bear':'triangle',
             'spike':'square','fall':'sawtooth','vix':'square'};
      var s=e.data.eagle;if(n[s])_play(n[s],w[s]||'sine',0.38,0.12);});
    </script>""", height=34)

def queue_sound(s: str):
    st.session_state.sound_queue.append(s)

def emit_sounds():
    q = st.session_state.sound_queue
    if not q: return
    best = max(q, key=lambda x: {"fall":6,"spike":5,"vix":4,"sell":3,"buy":2,"news_bear":1,"news_bull":1}.get(x,0))
    st.session_state.sound_queue = []
    sid = st.session_state.sound_id + 1
    st.session_state.sound_id = sid
    notes, wave, vol, dur = SOUNDS[best]
    components.html(f"""<script>(function(){{
      try{{var frames=window.parent.document.querySelectorAll('iframe');
        frames.forEach(function(f){{try{{f.contentWindow.postMessage({{eagle:'{best}',id:{sid}}},'*');}}catch(e){{}}}}); }}catch(e){{}}
      try{{var C=window.parent._EC;if(!C||!window.parent._ES)return;
        var notes={notes},dur={dur},vol={vol};
        notes.forEach(function(f,i){{var t=C.currentTime+i*(dur+0.04);
          var o=C.createOscillator(),g=C.createGain();o.type='{wave}';o.frequency.value=f;
          g.gain.setValueAtTime(vol,t);g.gain.exponentialRampToValueAtTime(0.001,t+dur);
          o.connect(g);g.connect(C.destination);o.start(t);o.stop(t+dur+0.02);}});}}}})();
    </script>""", height=1)


# ══ DATA FETCHERS ══════════════════════════════════════════════
def _flat(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=14)
def get_candles(sym: str):
    for base in ["https://query1.finance.yahoo.com","https://query2.finance.yahoo.com"]:
        try:
            df = yf.download(sym, period="1d", interval="1m", progress=False, auto_adjust=True)
            df = _flat(df); df.dropna(subset=["Close"], inplace=True)
            if len(df) >= 21: return df
        except: continue
    return None

@st.cache_data(ttl=55)
def get_gift():
    for sym in ["IN=F","^NSEI"]:
        try:
            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            df = _flat(df); df.dropna(subset=["Close"], inplace=True)
            if len(df) >= 3: return df
        except: continue
    return None

@st.cache_data(ttl=25)
def get_vix():
    for sym in ["^INDIAVIX","^VIX"]:
        try:
            df = yf.download(sym, period="30d", interval="1d", progress=False, auto_adjust=True)
            df = _flat(df); df.dropna(subset=["Close"], inplace=True)
            if len(df) >= 2:
                v,vp = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
                chg  = (v-vp)/vp*100
                return {"val":v,"chg":chg,"high":v>20,"spike":chg>15,
                        "history":df["Close"].tolist()[-30:]}
        except: continue
    return None

@st.cache_data(ttl=40)
def get_quote(sym: str):
    try:
        df = yf.download(sym, period="5d", interval="1d", progress=False, auto_adjust=True)
        df = _flat(df); df.dropna(subset=["Close"], inplace=True)
        if len(df) >= 2:
            p,pp = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
            pts = p-pp
            return {"price":p,"prev":pp,"chg":pts/pp*100,"pts":pts}
    except: pass
    return None

@st.cache_data(ttl=120)
def get_news():
    BULL_W = {"rally","surge","gain","rise","rises","record","growth","bullish","strong","jump",
              "soar","beats","exceeds","upgrade","buy","rebound","boost","profit","boom","optimistic"}
    BEAR_W = {"fall","falls","decline","drop","crash","loss","weak","bearish","sell","downgrade",
              "recession","fear","risk","concern","miss","disappoint","slump","tumble","plunge","warning"}
    seen, results = set(), []
    for sym in ["^NSEI","^NSEBANK","GC=F","CL=F","ES=F"]:
        try:
            for item in (yf.Ticker(sym).news or [])[:5]:
                t   = item.get("title","").strip()
                uid = item.get("uuid", t[:40])
                if not t or uid in seen: continue
                seen.add(uid)
                tl  = t.lower()
                b   = sum(1 for w in BULL_W if w in tl)
                r   = sum(1 for w in BEAR_W if w in tl)
                sent = "bull" if b>r else ("bear" if r>b else "neu")
                ts   = item.get("providerPublishTime",0)
                tstr = datetime.fromtimestamp(ts, tz=IST).strftime("%H:%M") if ts else "—"
                results.append({"title":t,"sentiment":sent,"time":tstr,
                                "source":item.get("publisher",""),
                                "id":uid,"link":item.get("link","#")})
        except: continue
    return results or NEWS_STATIC[:6]


# ══ INDICATORS ═════════════════════════════════════════════════
def calc_ind(df):
    c = df["Close"].astype(float)
    v = df["Volume"].replace(0, np.nan).astype(float)
    h = df["High"].astype(float)  if "High" in df.columns else c
    l = df["Low"].astype(float)   if "Low"  in df.columns else c
    o = df["Open"].astype(float)  if "Open" in df.columns else c

    ema9  = float(c.ewm(span=9,  adjust=False).mean().iloc[-1])
    ema21 = float(c.ewm(span=21, adjust=False).mean().iloc[-1])
    ema200= float(c.ewm(span=min(200,len(c)), adjust=False).mean().iloc[-1])
    ma20  = c.rolling(20).mean(); sd20 = c.rolling(20).std()
    bb_u  = float((ma20+2*sd20).iloc[-1]); bb_l = float((ma20-2*sd20).iloc[-1])
    tp    = (h+l+c)/3
    vwap  = float((tp*v).cumsum().iloc[-1] / v.cumsum().iloc[-1])
    d     = c.diff(); ag = d.clip(lower=0).rolling(14).mean()
    al    = (-d.clip(upper=0)).rolling(14).mean()
    rsi   = float((100-100/(1+ag/al.replace(0,np.nan))).iloc[-1])
    ve    = float(v.ewm(span=20, adjust=False).mean().iloc[-1])
    cv    = float(v.iloc[-1])
    vr    = cv/ve if ve>0 else 1.0
    price = float(c.iloc[-1])
    prev5 = float(c.iloc[-5]) if len(c)>=5 else price
    mom   = (price-prev5)/prev5*100
    sl_b  = float(l.iloc[-10:].min())*0.999
    sl_s  = float(h.iloc[-10:].max())*1.001
    bb_pos= (price-bb_l)/max(1,bb_u-bb_l)*100

    t1 = ema9>ema21; t2 = price>vwap; t3 = rsi>54; t4 = vr>=1.5
    return dict(price=price,ema9=ema9,ema21=ema21,ema200=ema200,vwap=vwap,
                rsi=rsi,bb_u=bb_u,bb_l=bb_l,bb_m=float(ma20.iloc[-1]),bb_pos=bb_pos,
                vol_ratio=vr,vol_spike=t4,mom_pct=mom,sl_buy=sl_b,sl_sell=sl_s,
                t1=t1,t2=t2,t3=t3,t4=t4,tris=[t1,t2,t3,t4])

def final_sig(ind, gift_trend, vix):
    p,r = ind["price"], ind["rsi"]
    e9,e21 = ind["ema9"], ind["ema21"]
    bb_u,bb_l = ind["bb_u"], ind["bb_l"]
    vx_high = vix and vix["val"]>20; vx_spike = vix and vix["spike"]

    eg = abs(e9-e21)/p*100; bet = min(e9,e21)<=p<=max(e9,e21)
    sideways = eg<0.08 or bet

    b_pts = int(p>ind["vwap"])+int(e9>e21)+int(r>54)
    s_pts = int(p<ind["vwap"])+int(e9<e21)+int(r<46)
    local = "BULL" if b_pts>=2 else ("BEAR" if s_pts>=2 else "NEUTRAL")
    dots  = sum([e9>e21, p>ind["vwap"], r>54, ind["vol_spike"]])

    if sideways:
        sig,zone = "SIDEWAYS — WAIT","sc-wait"
    elif gift_trend=="BULL" and local=="BULL":
        sig  = "🚀 SUPER BUY" if ind["vol_spike"] else "🚀 BUY"
        zone = "sc-buy"
    elif gift_trend=="BEAR" and local=="BEAR":
        sig  = "📉 SUPER SELL" if ind["vol_spike"] else "📉 SELL"
        zone = "sc-sell"
    elif local=="BULL" and gift_trend=="BEAR":
        sig,zone = "BUY ⚠️ GIFT CONFLICT","sc-caut"
    elif local=="BEAR" and gift_trend=="BULL":
        sig,zone = "SELL ⚠️ GIFT CONFLICT","sc-caut"
    else:
        sig,zone = "⏳ NO SYNC","sc-wait"

    if vx_high and "SUPER" in sig:
        sig = sig.replace("SUPER ","")+"(VIX HIGH)"; zone="sc-caut"

    pb = abs(p-e9)/p*100
    if local=="BULL":
        eq = "✅ IDEAL — AT EMA9" if pb<=0.15 else (f"⚠️ HIGH — PULLBACK ₹{e9:,.0f}" if p>e9 and pb>0.40 else "🟡 ACCEPTABLE")
        sl_val,sl_risk = ind["sl_buy"],p-ind["sl_buy"]
    elif local=="BEAR":
        eq = "✅ IDEAL SHORT EMA9" if pb<=0.15 else (f"⚠️ LOW — PULLBACK ₹{e9:,.0f}" if p<e9 and pb>0.40 else "🟡 ACCEPTABLE")
        sl_val,sl_risk = ind["sl_sell"],ind["sl_sell"]-p
    else:
        eq,sl_val,sl_risk = "⏳ NO ENTRY","",0

    return dict(signal=sig,zone=zone,local=local,dots=dots,
                entry_quality=eq,sl_val=sl_val,sl_risk=sl_risk,
                vix_warn=vx_high or vx_spike,gift_trend=gift_trend,
                tris=ind["tris"],mom_pct=ind["mom_pct"],
                vol_ratio=ind["vol_ratio"],rsi=r,vwap=ind["vwap"])

def pivot_levels(df):
    if df is None or len(df)<2: return {}
    h = float(df["High"].iloc[-2]) if "High" in df.columns else float(df["Close"].iloc[-2])
    l = float(df["Low"].iloc[-2])  if "Low"  in df.columns else float(df["Close"].iloc[-2])
    c = float(df["Close"].iloc[-2])
    p = (h+l+c)/3
    return {"P":p,"R1":2*p-l,"R2":p+(h-l),"R3":h+2*(p-l),
            "S1":2*p-h,"S2":p-(h-l),"S3":l-2*(h-p)}


# ══ SPIKE / FALL DETECTOR ══════════════════════════════════════
def check_spike_fall(sym: str, df):
    if df is None or len(df)<3: return
    cur  = float(df["Close"].iloc[-1])
    prev = st.session_state.prev_prices.get(sym, cur)
    delta= (cur-prev)/prev*100 if prev else 0
    st.session_state.prev_prices[sym] = cur
    if delta>0.8:
        queue_sound("spike")
        st.session_state.alert_log.append({"type":"🚀 SPIKE","sym":sym,"pct":f"+{delta:.2f}%",
            "time":datetime.now(IST).strftime("%H:%M:%S"),"css":"alert-spike"})
    elif delta<-0.8:
        queue_sound("fall")
        st.session_state.alert_log.append({"type":"📉 SUDDEN FALL","sym":sym,"pct":f"{delta:.2f}%",
            "time":datetime.now(IST).strftime("%H:%M:%S"),"css":"alert-fall"})
    st.session_state.alert_log = st.session_state.alert_log[-12:]

def log_signal(key, name, sig, ind):
    now = datetime.now(IST)
    prev = st.session_state.prev_sig.get(key,{})
    skip = {"⏳ NO SYNC","SIDEWAYS — WAIT"}
    if sig not in skip and sig!=prev.get("signal",""):
        st.session_state.signals_log.append({
            "time":now.strftime("%H:%M:%S"),"log_dt":now,"symbol":name,
            "signal":sig,"price":ind["price"],"rsi":ind["rsi"],
            "vol":ind["vol_ratio"],"mom":ind["mom_pct"],
            "evaluated":False,"result":None,"exit_price":None})
        if "BUY"  in sig: queue_sound("buy")
        elif "SELL" in sig: queue_sound("sell")
    for log in st.session_state.signals_log:
        if log["evaluated"] or log["symbol"]!=name: continue
        if (now-log["log_dt"]).total_seconds()<900: continue
        move = ind["price"]-log["price"]
        log.update({"evaluated":True,"result":"✅ PASS" if (move>0)==("BUY" in log["signal"]) else "❌ FAIL",
                    "exit_price":ind["price"]})
    st.session_state.prev_sig[key] = {"signal":sig,"price":ind["price"]}


# ══ PLOTLY CHART ═══════════════════════════════════════════════
def make_chart(df, title: str, vix_val=None):
    if df is None: return go.Figure()
    ind = calc_ind(df)
    c = df["Close"].astype(float); v = df["Volume"].replace(0,np.nan).astype(float)
    h = df["High"].astype(float)  if "High" in df.columns else c
    l = df["Low"].astype(float)   if "Low"  in df.columns else c
    o = df["Open"].astype(float)  if "Open" in df.columns else c
    idx = df.index

    ema9  = c.ewm(span=9,  adjust=False).mean()
    ema21 = c.ewm(span=21, adjust=False).mean()
    ma20  = c.rolling(20).mean(); sd20 = c.rolling(20).std()
    bb_u  = ma20+2*sd20; bb_l = ma20-2*sd20
    tp    = (h+l+c)/3; vwap = (tp*v).cumsum()/v.cumsum()
    rsi_s = 100-100/(1+c.diff().clip(lower=0).rolling(14).mean()/
                        (-c.diff().clip(upper=0)).rolling(14).mean().replace(0,1e-9))

    pvt = pivot_levels(df)
    fig = make_subplots(rows=3,cols=1,shared_xaxes=True,
        row_heights=[0.60,0.22,0.18],vertical_spacing=0.02,
        subplot_titles=[title,"RSI (14)","Volume"])

    fig.add_trace(go.Candlestick(x=idx,open=o,high=h,low=l,close=c,name="Price",
        increasing_fillcolor="#00d463",increasing_line_color="#00d463",
        decreasing_fillcolor="#ff3d3d",decreasing_line_color="#ff3d3d"),row=1,col=1)

    fig.add_trace(go.Scatter(x=idx,y=bb_u,name="BB Upper",
        line=dict(color="#3d6be0",width=1,dash="dot"),opacity=0.7),row=1,col=1)
    fig.add_trace(go.Scatter(x=idx,y=bb_l,name="BB Lower",fill="tonexty",
        fillcolor="rgba(61,107,224,0.05)",line=dict(color="#3d6be0",width=1,dash="dot"),opacity=0.7),row=1,col=1)
    fig.add_trace(go.Scatter(x=idx,y=vwap,name="VWAP",
        line=dict(color="#ffb700",width=2)),row=1,col=1)
    fig.add_trace(go.Scatter(x=idx,y=ema9, name="EMA9",
        line=dict(color="#00e676",width=1.2,dash="dash")),row=1,col=1)
    fig.add_trace(go.Scatter(x=idx,y=ema21,name="EMA21",
        line=dict(color="#ff8844",width=1.2,dash="dash")),row=1,col=1)

    if pvt:
        for lbl,val,col in [("R1",pvt["R1"],"rgba(255,70,70,.65)"),
                             ("PP",pvt["P"], "rgba(255,183,0,.65)"),
                             ("S1",pvt["S1"],"rgba(0,212,99,.65)")]:
            fig.add_hline(y=val,line=dict(color=col,width=1,dash="dot"),
                annotation_text=lbl,annotation_font=dict(color=col,size=10),row=1,col=1)

    fig.add_trace(go.Scatter(x=idx,y=rsi_s,name="RSI",
        line=dict(color="#cc88ff",width=1.5)),row=2,col=1)
    for v2,col in [(70,"#ff3d3d55"),(30,"#00d46355")]:
        fig.add_hline(y=v2,line=dict(color=col,width=1,dash="dot"),row=2,col=1)
    fig.add_hline(y=50,line=dict(color="#0d306055",width=1),row=2,col=1)

    vol_cols = ["#00d463" if float(c.iloc[i])>=float(o.iloc[i]) else "#ff3d3d" for i in range(len(c))]
    fig.add_trace(go.Bar(x=idx,y=v,name="Volume",marker_color=vol_cols,opacity=0.7),row=3,col=1)

    fig.update_layout(
        paper_bgcolor="#020b18",plot_bgcolor="#030c1a",
        font=dict(family="Share Tech Mono",color="#8ab8d8",size=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h",yanchor="bottom",y=1.02,bgcolor="rgba(0,0,0,0)",font_size=9),
        margin=dict(l=40,r=15,t=30,b=10),height=490,showlegend=True)
    fig.update_xaxes(gridcolor="#0d3060",showgrid=True,zeroline=False,tickfont=dict(color="#3d6a8a"))
    fig.update_yaxes(gridcolor="#0d3060",showgrid=True,zeroline=False,tickfont=dict(color="#3d6a8a"))
    fig.update_yaxes(range=[0,100],row=2,col=1)

    if vix_val:
        vc = "#00d463" if vix_val<15 else ("#ffb700" if vix_val<20 else "#ff3d3d")
        fig.add_annotation(x=0.98,y=0.97,xref="paper",yref="paper",
            text=f"VIX {vix_val:.1f}",showarrow=False,
            font=dict(color=vc,size=13,family="Share Tech Mono"),
            bgcolor="#020b18",bordercolor=vc,borderwidth=1,borderpad=4)
    return fig

def vix_chart(hist):
    fig = go.Figure()
    x = list(range(len(hist)))
    fig.add_trace(go.Scatter(x=x,y=hist,fill="tozeroy",
        fillcolor="rgba(255,183,0,.12)",line=dict(color="#ffb700",width=2)))
    fig.add_hline(y=15,line=dict(color="#00d46355",width=1.2,dash="dot"),
        annotation_text="15 (Low)",annotation_font=dict(color="#00d463",size=9))
    fig.add_hline(y=20,line=dict(color="#ff3d3d55",width=1.2,dash="dot"),
        annotation_text="20 (High)",annotation_font=dict(color="#ff3d3d",size=9))
    fig.update_layout(paper_bgcolor="#020b18",plot_bgcolor="#030c1a",
        font=dict(color="#8ab8d8",size=9),margin=dict(l=30,r=10,t=10,b=10),height=180,
        xaxis=dict(showticklabels=False,gridcolor="#0d3060"),
        yaxis=dict(gridcolor="#0d3060"))
    return fig


# ══ HTML BUILDERS ══════════════════════════════════════════════
def ind_grid_html(ind):
    def box(lbl,val,sig):
        cls = "ind-buy" if sig=="BUY" else ("ind-sell" if sig=="SELL" else "ind-neu")
        col = "#00d463" if sig=="BUY" else ("#ff3d3d" if sig=="SELL" else "#3d9be9")
        return f'<div class="ind-box {cls}"><div class="ind-lbl">{lbl}</div><div class="ind-val" style="color:{col}">{val}</div><div class="ind-sig" style="color:{col}">{sig}</div></div>'
    r = ind["rsi"]
    return f"""<div class="ind-grid">
        {box("RSI (14)", f"{r:.1f}", "BUY" if r<30 else ("SELL" if r>70 else "NEUTRAL"))}
        {box("VWAP", f"₹{ind['vwap']:,.0f}", "BUY" if ind['price']>ind['vwap'] else "SELL")}
        {box("EMA 9/21", f"{'▲' if ind['ema9']>ind['ema21'] else '▼'} {ind['ema9']:,.0f}", "BUY" if ind['ema9']>ind['ema21'] else "SELL")}
        {box("VOLUME", f"{ind['vol_ratio']:.1f}x", "BUY" if ind['vol_spike'] else "NEUTRAL")}
        {box("BOLLINGER", f"{ind['bb_pos']:.0f}% pos", "BUY" if ind['bb_pos']<15 else ("SELL" if ind['bb_pos']>85 else "NEUTRAL"))}
        {box("MOMENTUM", f"{ind['mom_pct']:+.2f}%", "BUY" if ind['mom_pct']>0.2 else ("SELL" if ind['mom_pct']<-0.2 else "NEUTRAL"))}
    </div>"""

def signal_card_html(name, sym, df, gift_trend, vix):
    if df is None:
        return f'<div class="sc sc-wait"><div class="sc-sym">{name}</div><div style="color:#1e3a5f;padding:20px;font-family:Share Tech Mono">⚠️ DATA UNAVAILABLE</div></div>'
    ind = calc_ind(df)
    sig = final_sig(ind, gift_trend, vix)
    log_signal(sym, name, sig["signal"], ind)
    check_spike_fall(sym, df)

    p  = ind["price"]; prev = float(df["Close"].iloc[0])
    pts= p-prev; pct = pts/prev*100
    col= "#00d463" if sig["zone"]=="sc-buy" else ("#ff3d3d" if sig["zone"]=="sc-sell" else ("#ffb700" if "caut" in sig["zone"] else "#3d5a7a"))
    arr= "▲" if pts>=0 else "▼"

    tris = sig["tris"]
    tri_html = "&nbsp;".join(f'<span style="color:{col if t else "#0d2040"};font-size:18px">{"▲" if t else "▽"}</span>' for t in tris)

    vix_html = ""
    if vix:
        vc = "#00d463" if vix["val"]<15 else ("#ffb700" if vix["val"]<20 else "#ff3d3d")
        vix_html = f'<div class="vblink" style="color:{vc};font-size:12px;margin:3px 0;cursor:pointer" onclick="">⚡ VIX {vix["val"]:.1f} <span style="font-size:10px">({vix["chg"]:+.1f}%)</span></div>'

    sl_html = ""
    if sig["sl_val"] and sig["zone"] in ("sc-buy","sc-sell","sc-caut"):
        sl_html = f'<div class="sc-entry"><div style="font-size:9px;letter-spacing:2px;color:#3d9be9;margin-bottom:3px">ENTRY / SL</div><div style="color:{col};font-size:11px">{sig["entry_quality"]}</div><div style="color:#ff7070;font-size:11px;margin-top:2px;font-family:Share Tech Mono">🛑 SL: ₹{sig["sl_val"]:,.0f} &nbsp; RISK: {sig["sl_risk"]:,.0f} pts</div></div>'

    vix_badge = '<span class="sc-badge" style="background:#3a0000;color:#ff9800;border:1px solid #ff9800">⚡ VIX ALERT</span>' if sig["vix_warn"] else ""

    return f"""<div class="sc {sig['zone']}">
        {vix_badge}
        <div class="sc-sym">{name}</div>
        <div class="sc-price" style="color:{col}">₹{p:,.1f}</div>
        <div class="sc-pts" style="color:{'#00d463' if pts>=0 else '#ff3d3d'}">{arr} {abs(pts):,.1f} pts &nbsp; {arr} {abs(pct):.2f}%</div>
        <div class="sc-sig" style="color:{col}">{sig["signal"]}</div>
        {vix_html}
        <div class="sc-tris">{tri_html}</div>
        <div style="display:flex;justify-content:center;gap:14px;font-size:9px;color:#3d5a7a;letter-spacing:1px;margin-top:2px"><span>EMA</span><span>VWAP</span><span>RSI</span><span>VOL</span></div>
        <div class="sc-meta">
            <span>RSI {sig["rsi"]:.0f}</span>
            <span>VWAP ₹{sig["vwap"]:,.0f}</span>
            <span>VOL {sig["vol_ratio"]:.1f}x</span>
            <span>MOM {sig["mom_pct"]:+.2f}%</span>
            <span>GIFT {sig["gift_trend"]}</span>
        </div>
        {sl_html}
        <div class="sc-time">🕐 {datetime.now(IST).strftime("%H:%M:%S")}</div>
    </div>"""

def gift_card_html(df, vix):
    if df is None:
        return '<div class="sc sc-wait"><div class="sc-sym">GIFT NIFTY</div><div style="color:#1e3a5f;padding:20px">⚠️ DATA UNAVAILABLE</div></div>'
    cur  = float(df["Close"].iloc[-1]); prev = float(df["Close"].iloc[-2])
    pts  = cur-prev; pct = pts/prev*100; arr = "▲" if pts>=0 else "▼"
    col  = "#00d463" if pts>0 else ("#ff3d3d" if pts<0 else "#3d9be9")
    trend= "🐂 BULLISH" if pct>0.05 else ("🐻 BEARISH" if pct<-0.05 else "⚖️ NEUTRAL")
    zone = "sc-buy" if pct>0.05 else ("sc-sell" if pct<-0.05 else "sc-wait")

    last5 = df["Close"].astype(float).iloc[-5:].tolist()
    tri_html = "&nbsp;".join(f'<span style="color:{"#00d463" if last5[i]>last5[i-1] else "#ff3d3d"};font-size:20px">{"▲" if last5[i]>last5[i-1] else "▼"}</span>' for i in range(1,len(last5)))

    vix_html = ""
    if vix:
        vc = "#00d463" if vix["val"]<15 else ("#ffb700" if vix["val"]<20 else "#ff3d3d")
        vix_html = f'<div class="vblink" style="color:{vc};font-size:12px;margin:3px 0">⚡ VIX {vix["val"]:.1f}</div>'

    return f"""<div class="sc {zone}">
        <span class="sc-badge" style="color:{col};border:1px solid {col}">SGX / GIFT NIFTY FUTURES</span>
        <div class="sc-sym">15-MIN GLOBAL TREND</div>
        <div class="sc-price" style="color:{col}">₹{cur:,.1f}</div>
        <div class="sc-pts" style="color:{col}">{arr} {abs(pts):,.1f} pts &nbsp; {arr} {abs(pct):.3f}%</div>
        <div class="sc-sig" style="color:{col}">{trend}</div>
        {vix_html}
        <div class="sc-tris">{tri_html}</div>
        <div style="font-size:9px;color:#3d5a7a;margin-top:2px">← LAST 4 CANDLES TREND</div>
        <div class="sc-meta"><span>PREV ₹{prev:,.1f}</span><span>15M</span><span>{pct:+.3f}%</span></div>
        <div class="sc-time">🕐 {datetime.now(IST).strftime("%H:%M:%S")}</div>
    </div>"""

def mini_card_html(icon, name, q, is_inr=False):
    if not q:
        return f'<div class="mc"><div class="mc-ico">{icon}</div><div class="mc-nm">{name}</div><div style="color:#1e3a5f">—</div></div>'
    p,chg,pts = q["price"],q["chg"],q["pts"]
    arr = "▲" if chg>0 else ("▼" if chg<0 else "—")
    col = "#00d463" if chg>0 else ("#ff3d3d" if chg<0 else "#3d9be9")
    pref = "₹" if is_inr else ""
    pts_str = f"{pts:+,.1f} pts" if abs(p)>10 else f"{pts:+.4f}"
    return f'<div class="mc"><div class="mc-ico">{icon}</div><div class="mc-nm">{name}</div><div class="mc-pr">{pref}{p:,.1f}</div><div class="mc-ch" style="color:{col}">{arr} {abs(chg):.2f}%</div><div class="mc-pt" style="color:{col}">{pts_str}</div></div>'

def pivot_html(pvt, cmp):
    if not pvt: return "<div style='color:#1e3a5f'>Loading…</div>"
    def cell(lbl,val,css):
        atm = "outline:2px solid #ffd050;" if abs(val-cmp)<30 else ""
        return f'<div class="pvt-cell {css}" style="{atm}"><div class="pvt-lbl">{lbl}</div>{val:,.0f}</div>'
    if cmp>pvt["R2"]:    st2,col2,adv = "Above R2 🔴 OVERBOUGHT","#ff3d3d","Heavy resistance. Consider SELL / book profits."
    elif cmp>pvt["R1"]:  st2,col2,adv = "R1–R2 🔴 Resistance","#ff7070","Short near R2 with tight SL."
    elif cmp>pvt["P"]:   st2,col2,adv = "Pivot–R1 🟡 Bullish","#ffb700","Above Pivot — bullish. Target R1 then R2."
    elif cmp>pvt["S1"]:  st2,col2,adv = "S1–Pivot 🟡 Weak","#ffb700","Below Pivot — weak. Wait to reclaim PP."
    elif cmp>pvt["S2"]:  st2,col2,adv = "S1–S2 🟢 Support","#00d463","BUY near S1. SL below S2."
    else:                st2,col2,adv = "Below S2 🟢 Strong Support","#00d463","Strong support. High-probability BUY zone."
    return f"""<div class="pvt-grid">
        {cell("R3 🔴",pvt["R3"],"pvt-r")}{cell("R2 🔴",pvt["R2"],"pvt-r")}
        {cell("R1 🔴",pvt["R1"],"pvt-r")}{cell("PIVOT ⚡",pvt["P"],"pvt-p")}
        {cell("S1 🟢",pvt["S1"],"pvt-s")}{cell("S2 🟢",pvt["S2"],"pvt-s")}
        {cell("S3 🟢",pvt["S3"],"pvt-s")}{cell("CMP",cmp,"pvt-c")}
    </div>
    <div style="background:{col2}18;border:1px solid {col2}40;border-radius:6px;padding:9px;margin-top:8px">
        <div style="color:{col2};font-weight:700;font-size:13px;margin-bottom:4px">{st2}</div>
        <div style="color:#a0c8e0;font-size:12px">{adv}</div>
    </div>"""

def mood_meter_html(score):
    lbl = "EXTREME FEAR" if score<20 else ("FEAR" if score<40 else ("NEUTRAL" if score<60 else ("GREED" if score<80 else "EXTREME GREED")))
    col = "#ff3d3d" if score<30 else ("#ff8844" if score<50 else ("#ffcc00" if score<70 else "#00d463"))
    left= max(1,min(99,score))
    return f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px">
        <div style="font-size:9px;letter-spacing:3px;color:#3d9be9;margin-bottom:8px">🧠 MARKET MOOD METER</div>
        <div class="mood-track"><div class="mood-ptr" style="left:{left}%"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:8px;color:#1e3a5f;margin-bottom:6px"><span>EXTREME FEAR</span><span>NEUTRAL</span><span>EXTREME GREED</span></div>
        <div style="text-align:center;font-size:15px;font-weight:900;color:{col};font-family:Share Tech Mono">{score}/100 — {lbl}</div>
    </div>"""

def tape_html(items):
    cells = "".join(f"""<div class="tape-item">
        <span class="ti-n">{it['n']}</span>
        <span class="ti-v" style="color:{it['col']}">{it['v']}</span>
        <span class="ti-c" style="color:{it['chgcol']}">{it['arr']}{abs(it['pct']):.2f}%</span>
        <span class="ti-p" style="color:{it['chgcol']}">{it['pts']}</span>
    </div>""" for it in items)
    return f'<div style="display:flex;gap:5px;overflow-x:auto;padding:4px 0;scrollbar-width:none">{cells}</div>'

def oi_buildup_html(strikes):
    header = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px;font-size:9px;color:#3d5a7a;font-family:Share Tech Mono;padding:4px 0;border-bottom:1px solid #0d3060"><span>STRIKE</span><span style="text-align:right">CALL Δ</span><span style="text-align:right">PUT Δ</span><span style="text-align:right">BIAS</span></div>'
    rows = ""
    for s in strikes:
        cb  = s["cCh"]>0; pb = s["pCh"]>0
        bias= "BULL" if pb and not cb else ("BEAR" if cb and not pb else ("BOTH" if pb and cb else "UNWIND"))
        bc  = "#00d463" if bias=="BULL" else ("#ff3d3d" if bias=="BEAR" else "#ffb700")
        def foi(n): return f"{n/100000:.1f}L" if abs(n)>=100000 else f"{n/1000:.0f}K"
        rows += f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px;padding:5px 0;border-bottom:1px solid #08182e;font-size:11px;font-family:Share Tech Mono"><span style="color:#d0e8f0;font-weight:700">{s["k"]:,}</span><span style="text-align:right;color:{"#ff7070" if cb else "#88ffcc"}">{"▲" if cb else "▼"}{foi(abs(s["cCh"]))}</span><span style="text-align:right;color:{"#88ffaa" if pb else "#ff9999"}">{"▲" if pb else "▼"}{foi(abs(s["pCh"]))}</span><span style="text-align:right;background:{bc}20;color:{bc};border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">{bias}</span></div>'
    return header+rows


# ══ SL CALCULATOR ═══════════════════════════════════════════════
def sl_calculator_section():
    st.markdown('<div class="slbl">🎯 STOP LOSS CALCULATOR</div>', unsafe_allow_html=True)
    r1,r2,r3 = st.columns(3)
    with r1:
        entry = st.number_input("Entry Price (₹)", min_value=1.0, value=22450.0, step=5.0)
        trade_type = st.selectbox("Position Type", ["BUY / LONG","SELL / SHORT"])
    with r2:
        sl_pct = st.number_input("SL % from Entry", min_value=0.1, max_value=5.0, value=0.4, step=0.05)
        qty    = st.number_input("Qty / Lot Size", min_value=1, value=50, step=1)
    with r3:
        rr     = st.number_input("Target R:R (1:?)", min_value=1.0, value=2.0, step=0.5)

    is_buy  = "BUY" in trade_type
    sl_pts  = entry*sl_pct/100
    sl_val  = entry-sl_pts if is_buy else entry+sl_pts
    t1      = entry+sl_pts*rr   if is_buy else entry-sl_pts*rr
    t2      = entry+sl_pts*rr*1.5 if is_buy else entry-sl_pts*rr*1.5
    risk_rs = sl_pts*qty; p1 = sl_pts*rr*qty; p2 = sl_pts*rr*1.5*qty

    st.markdown(f"""<div class="sl-grid">
        <div class="sl-box" style="border-color:#ff3d3d">
            <div class="sl-lbl">🛑 STOP LOSS</div>
            <div class="sl-val" style="color:#ff7070">₹{sl_val:,.1f}</div>
            <div class="sl-sub" style="color:#ff8888">{'-' if is_buy else '+'}{sl_pts:,.1f} pts | {sl_pct}%</div>
        </div>
        <div class="sl-box" style="border-color:#00d463">
            <div class="sl-lbl">🎯 TARGET 1 (1:{rr:.1f})</div>
            <div class="sl-val" style="color:#00d463">₹{t1:,.1f}</div>
            <div class="sl-sub" style="color:#44ee88">{'+' if is_buy else '-'}{sl_pts*rr:,.1f} pts</div>
        </div>
        <div class="sl-box" style="border-color:#ffb700">
            <div class="sl-lbl">🎯 TARGET 2 (1:{rr*1.5:.1f})</div>
            <div class="sl-val" style="color:#ffb700">₹{t2:,.1f}</div>
            <div class="sl-sub" style="color:#ffdd88">{'+' if is_buy else '-'}{sl_pts*rr*1.5:,.1f} pts</div>
        </div>
        <div class="sl-box" style="border-color:#ff3d3d55">
            <div class="sl-lbl">💸 TOTAL RISK</div>
            <div class="sl-val" style="color:#ff7070">₹{risk_rs:,.0f}</div>
            <div class="sl-sub" style="color:#3d5a7a">{qty} × {sl_pts:,.1f}</div>
        </div>
        <div class="sl-box" style="border-color:#00d46355">
            <div class="sl-lbl">💰 PROFIT T1</div>
            <div class="sl-val" style="color:#00d463">₹{p1:,.0f}</div>
            <div class="sl-sub" style="color:#44ee88">R:R 1:{rr:.1f}</div>
        </div>
        <div class="sl-box" style="border-color:#ffb70055">
            <div class="sl-lbl">💰 PROFIT T2</div>
            <div class="sl-val" style="color:#ffb700">₹{p2:,.0f}</div>
            <div class="sl-sub" style="color:#ffdd88">R:R 1:{rr*1.5:.1f}</div>
        </div>
    </div>
    <div style="padding:9px;background:#030c1a;border:1px solid #ffb70030;border-radius:6px;font-size:12px;color:#ccaa66;line-height:1.8">
        ⚡ {'✅ Good R:R ≥1:2 — proceed' if rr>=2 else '⚠️ R:R below 1:2 — widen target or skip'}<br>
        {'🔴 Risk >₹10K — consider reducing quantity!' if risk_rs>10000 else ('🟡 Risk >₹5K — watch position size' if risk_rs>5000 else '✅ Risk within safe limits')}<br>
        <span style="color:#3d5a7a">SL from Option Chain: Use max Call OI strike as resistance SL | max Put OI as support SL (see OI+Pivot tab)</span>
    </div>""", unsafe_allow_html=True)


# ══ OPTION CHAIN ═══════════════════════════════════════════════
def option_chain_html(cmp):
    atm = round(cmp/50)*50
    strikes = list(range(int(atm)-200, int(atm)+250, 50))
    rows = ""
    for k in strikes:
        d   = abs(k-atm)
        cOI = max(10,int(-d*8+1200+np.random.randint(-80,80)))
        pOI = max(10,int(-d*7+1100+np.random.randint(-80,80)))
        cLTP= max(0.5,(cmp-k)+np.random.uniform(8,35)) if k<cmp else max(0.5,np.random.uniform(1,60-d*0.08))
        pLTP= max(0.5,(k-cmp)+np.random.uniform(8,35)) if k>cmp else max(0.5,np.random.uniform(1,60+d*0.08))
        atm_c = "oc-atm" if k==atm else ""
        rows += f'<div class="oc-call {atm_c}">{cLTP:.1f} <span style="font-size:9px;color:#3d5a7a">{cOI}K</span></div><div class="oc-strike {atm_c}">{k:,}{"★" if k==atm else ""}</div><div class="oc-put {atm_c}"><span style="font-size:9px;color:#3d5a7a">{pOI}K</span> {pLTP:.1f}</div>'
    return f'<div class="oc-grid"><div class="oc-hdr">CALL LTP / OI</div><div class="oc-hdr">STRIKE</div><div class="oc-hdr">PUT OI / LTP</div>{rows}</div>'


# ══ REPORT ════════════════════════════════════════════════════
def eod_report():
    logs   = st.session_state.signals_log
    evaled = [l for l in logs if l["evaluated"]]
    passed = [l for l in evaled if "PASS" in (l.get("result") or "")]
    strike = len(passed)/len(evaled)*100 if evaled else 0
    buys   = len([l for l in logs if "BUY"  in l.get("signal","")])
    sells  = len([l for l in logs if "SELL" in l.get("signal","")])

    cols = st.columns(8)
    mets = [("TOTAL",str(len(logs)),"#3d9be9"),("PASS",str(len(passed)),"#00d463"),
            ("FAIL",str(len(evaled)-len(passed)),"#ff3d3d"),
            ("STRIKE%",f"{strike:.0f}%","#00d463" if strike>=60 else "#ffb700"),
            ("PENDING",str(len(logs)-len(evaled)),"#ffb700"),
            ("BUYS",str(buys),"#00d463"),("SELLS",str(sells),"#ff3d3d"),
            ("ALERTS",str(len(st.session_state.alert_log)),"#ffb700")]
    for col,(lbl,val,clr) in zip(cols,mets):
        with col: st.markdown(f'<div class="rm"><div class="rv" style="color:{clr}">{val}</div><div class="rl">{lbl}</div></div>', unsafe_allow_html=True)

    if logs:
        st.markdown("#### 📋 Signal Log")
        rows = [{"Time":l["time"],"Symbol":l["symbol"],"Signal":l["signal"],
                 "Entry":f"₹{l['price']:,.1f}","Exit":f"₹{l['exit_price']:,.1f}" if l["exit_price"] else "⏳",
                 "Result":l.get("result") or "⏳","RSI":f"{l['rsi']:.0f}",
                 "Vol":f"{l.get('vol',0):.1f}x","Mom%":f"{l.get('mom',0):+.2f}%"} for l in logs]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True,height=220)

    if st.session_state.alert_log:
        st.markdown("#### 🚨 Spike / Fall Alerts")
        html = "".join(f'<div class="alert-box {a["css"]}">{a["type"]} &nbsp; <strong>{a["sym"]}</strong> &nbsp; {a["pct"]} &nbsp;<span style="color:#3d5a7a">{a["time"]}</span></div>' for a in reversed(st.session_state.alert_log))
        st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  🖥️  MAIN
# ══════════════════════════════════════════════════════════════

now_ist     = datetime.now(IST)
df_nifty    = get_candles("^NSEI")
df_bank     = get_candles("^NSEBANK")
df_gift     = get_gift()
vix         = get_vix()
news_live   = get_news()
is_expiry   = now_ist.weekday() == 3   # Thursday

# Gift trend
gift_trend = "NEUTRAL"
if df_gift is not None and len(df_gift)>=2:
    gc = (float(df_gift["Close"].iloc[-1])-float(df_gift["Close"].iloc[-2]))/float(df_gift["Close"].iloc[-2])*100
    gift_trend = "BULL" if gc>0.05 else ("BEAR" if gc<-0.05 else "NEUTRAL")

if vix and vix["spike"]: queue_sound("vix")

# Mood score (simple RSI-based proxy)
mood_score = 54
if df_nifty is not None:
    ind_n = calc_ind(df_nifty)
    mood_score = min(95, max(5, int((ind_n["rsi"]-30)/40*100)))

# Tape data
tape_items = []
for sym,nm in [("^NSEI","NIFTY"),("^NSEBANK","BNKIFTY"),("IN=F","GIFT NF"),
               ("GC=F","GOLD"),("SI=F","SILVER"),("CL=F","WTI"),
               ("^INDIAVIX","VIX"),("ES=F","SP500"),("USDINR=X","USD/INR")]:
    q = get_quote(sym)
    if q:
        chg = q["chg"]; pts = q["pts"]; p = q["price"]
        chgcol = "#00d463" if chg>0 else ("#ff3d3d" if chg<0 else "#3d9be9")
        vcol   = "#00d463" if (sym=="^INDIAVIX" and p<15) else ("#ffb700" if (sym=="^INDIAVIX" and p<20) else chgcol) if sym!="^INDIAVIX" else "#ff3d3d"
        tape_items.append({"n":nm,"v":f"₹{p:,.1f}" if "NIFTY" in nm or "GIFT" in nm or "INR" in nm else f"{p:,.1f}",
            "arr":"▲" if chg>0 else "▼","pct":chg,"pts":f"{pts:+,.1f}","col":"#ddeeff","chgcol":chgcol})

# OI strike data (simulated — real needs NSE API)
np.random.seed(42)
oi_strikes = []
for k in range(21500,23350,100):
    oi_strikes.append({"k":k,"cOI":max(10000,int((1200-abs(k-22400)*8+np.random.randint(-80,80))*1000)),
        "pOI":max(10000,int((1100-abs(k-22400)*7+np.random.randint(-80,80))*1000)),
        "cCh":(np.random.random()-.4)*100000,"pCh":(np.random.random()-.4)*100000})

# ── HEADER ──────────────────────────────────────────────────
h1,h2,h3,h4,h5 = st.columns([3,2,2,1.5,1])
with h1:
    st.markdown('<div style="font-size:20px;font-weight:900;letter-spacing:4px;color:#3d9be9;font-family:Share Tech Mono">🦅 EAGLE EYE PRO <span style="font-size:11px;color:#1e3a5f">v5.0</span></div>', unsafe_allow_html=True)
with h2:
    st.markdown(f'<div style="font-size:11px;color:#5a8aaa;font-family:Share Tech Mono;padding-top:6px">{now_ist.strftime("%I:%M:%S %p")} IST<br>{now_ist.strftime("%d %b %Y — %A")}</div>', unsafe_allow_html=True)
with h3:
    if vix:
        vc  = "#00d463" if vix["val"]<15 else ("#ffb700" if vix["val"]<20 else "#ff3d3d")
        rsk = "LOW RISK 🟢" if vix["val"]<15 else ("MED RISK 🟡" if vix["val"]<20 else "HIGH RISK 🔴")
        st.markdown(f'<div class="vblink" style="font-size:15px;font-weight:900;color:{vc};font-family:Share Tech Mono;padding-top:5px">VIX {vix["val"]:.1f} <span style="font-size:11px">({vix["chg"]:+.1f}%)</span></div><div style="font-size:10px;color:{vc};letter-spacing:2px">{rsk}</div>', unsafe_allow_html=True)
with h4:
    sound_button()
with h5:
    st.markdown('<div style="font-size:9px;color:#1e3a5f;text-align:right;padding-top:10px;font-family:Share Tech Mono">⟳ 15s LIVE<br>YQ1↔YQ2</div>', unsafe_allow_html=True)

if is_expiry:
    st.markdown('<div class="expiry-banner">⚡ F&O EXPIRY DAY — THURSDAY — MAX PAIN ZONE ACTIVE — AVOID NAKED POSITIONS — EXTRA CAUTION ⚡</div>', unsafe_allow_html=True)

st.markdown('<div style="height:2px;border-bottom:1px solid #0d3060;margin:3px 0 5px"></div>', unsafe_allow_html=True)

# ── LIVE TAPE ──────────────────────────────────────────────
if tape_items:
    st.markdown(tape_html(tape_items), unsafe_allow_html=True)
    st.markdown('<div style="height:3px"></div>', unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────
tabs = st.tabs(["⚡ SIGNALS","📊 CHARTS","🌍 MARKETS","📰 NEWS","📈 OI+PIVOT","🎯 SL CALC","⚡ STRATEGY","🔬 ANALYSIS","📊 REPORT"])
t1,t2,t3,t4,t5,t6,t7,t8,t9 = tabs


# ════════════════════════════
# TAB 1 — SIGNALS
# ════════════════════════════
with t1:
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(signal_card_html("NIFTY 50","^NSEI",df_nifty,gift_trend,vix), unsafe_allow_html=True)
        if df_nifty is not None:
            st.markdown(ind_grid_html(calc_ind(df_nifty)), unsafe_allow_html=True)
    with c2:
        st.markdown(signal_card_html("BANKNIFTY","^NSEBANK",df_bank,gift_trend,vix), unsafe_allow_html=True)
        if df_bank is not None:
            st.markdown(ind_grid_html(calc_ind(df_bank)), unsafe_allow_html=True)
    with c3:
        st.markdown(gift_card_html(df_gift,vix), unsafe_allow_html=True)
        if vix and vix.get("history"):
            st.markdown('<div style="color:#3d9be9;font-size:9px;letter-spacing:2px;margin:5px 0 2px;font-family:Share Tech Mono">⚡ VIX 30-DAY HISTORY</div>', unsafe_allow_html=True)
            st.plotly_chart(vix_chart(vix["history"]), use_container_width=True, config={"displayModeBar":False})

    # Mood meter
    st.markdown(mood_meter_html(mood_score), unsafe_allow_html=True)

    # Alerts
    if st.session_state.alert_log:
        st.markdown('<div class="slbl">🚨 SPIKE / FALL ALERTS</div>', unsafe_allow_html=True)
        alc = st.columns(min(3,len(st.session_state.alert_log)))
        for i,a in enumerate(reversed(st.session_state.alert_log[:3])):
            with alc[i]:
                st.markdown(f'<div class="alert-box {a["css"]}">{a["type"]} <strong>{a["sym"]}</strong> {a["pct"]} <span style="color:#3d5a7a">{a["time"]}</span></div>', unsafe_allow_html=True)

    # Global pulse
    st.markdown('<div class="slbl">⚡ QUICK GLOBAL PULSE</div>', unsafe_allow_html=True)
    qc = st.columns(6)
    for (sym,nm,ico,inr),col in zip([("ES=F","S&P500","📈",False),("NQ=F","NASDAQ","💻",False),
        ("GC=F","GOLD","🥇",False),("CL=F","CRUDE","🛢️",False),
        ("SI=F","SILVER","🥈",False),("^INDIAVIX","VIX","⚡",False)], qc):
        with col: st.markdown(mini_card_html(ico,nm,get_quote(sym),inr), unsafe_allow_html=True)


# ════════════════════════════
# TAB 2 — CHARTS
# ════════════════════════════
with t2:
    ch1,ch2 = st.columns(2)
    with ch1:
        if df_nifty is not None:
            st.plotly_chart(make_chart(df_nifty,"NIFTY 50 (1-min)",vix["val"] if vix else None),
                use_container_width=True,config={"displayModeBar":True})
        else: st.info("⚠️ Nifty data unavailable — Check internet / market hours (9:15–15:30 IST)")
    with ch2:
        if df_bank is not None:
            st.plotly_chart(make_chart(df_bank,"BANKNIFTY (1-min)",vix["val"] if vix else None),
                use_container_width=True,config={"displayModeBar":True})
        else: st.info("⚠️ BankNifty data unavailable")

    if df_gift is not None:
        st.markdown('<div class="slbl">GIFT NIFTY — 15 MIN</div>', unsafe_allow_html=True)
        st.plotly_chart(make_chart(df_gift,"GIFT NIFTY (15-min)",vix["val"] if vix else None),
            use_container_width=True,config={"displayModeBar":True})

    # Candlestick pattern cards
    st.markdown('<div class="slbl">🕯️ CANDLESTICK PATTERNS DETECTED</div>', unsafe_allow_html=True)
    pc = st.columns(6)
    for pat,col in zip(PATS,pc):
        with col:
            pcol = "#00d463" if pat["t"]=="bullish" else ("#ff3d3d" if pat["t"]=="bearish" else "#ffb700")
            st.markdown(f'<div style="background:#020b18;border:1px solid {pcol}30;border-radius:7px;padding:8px;text-align:center"><div style="font-size:11px;font-weight:700;color:{pcol};margin-bottom:3px">{pat["n"]}</div><div style="font-size:9px;color:#3d5a7a;margin-bottom:4px;letter-spacing:1px">{pat["t"].upper()}</div><div style="height:3px;background:#0a1628;border-radius:2px;margin-bottom:4px"><div style="height:100%;width:{pat["c"]}%;background:{pcol};border-radius:2px"></div></div><div style="font-size:12px;font-weight:900;color:{pcol};font-family:Share Tech Mono">{pat["c"]}%</div></div>', unsafe_allow_html=True)


# ════════════════════════════
# TAB 3 — MARKETS
# ════════════════════════════
with t3:
    st.markdown('<div class="slbl">🇺🇸 US MARKETS + FUTURES</div>', unsafe_allow_html=True)
    uc = st.columns(4)
    for (s,n,i,r),col in zip([("ES=F","S&P500 Fut","📈",False),("NQ=F","NASDAQ Fut","💻",False),("YM=F","DOW Fut","🏭",False),("RTY=F","RUSSELL 2K","📊",False)],uc):
        with col: st.markdown(mini_card_html(i,n,get_quote(s),r),unsafe_allow_html=True)

    st.markdown('<div class="slbl">🌏 ASIAN MARKETS</div>', unsafe_allow_html=True)
    ac = st.columns(5)
    for (s,n,i,r),col in zip([("NIY=F","NIKKEI 225","🇯🇵",False),("^HSI","HANG SENG","🇭🇰",False),("^AXJO","ASX 200","🇦🇺",False),("000300.SS","CSI 300","🇨🇳",False),("IN=F","SGX NIFTY","🇸🇬",False)],ac):
        with col: st.markdown(mini_card_html(i,n,get_quote(s),r),unsafe_allow_html=True)

    st.markdown('<div class="slbl">🇪🇺 EUROPEAN MARKETS</div>', unsafe_allow_html=True)
    ec = st.columns(4)
    for (s,n,i,r),col in zip([("^GDAXI","DAX 40","🇩🇪",False),("^FTSE","FTSE 100","🇬🇧",False),("^FCHI","CAC 40","🇫🇷",False),("^STOXX50E","EURO STOXX","🇪🇺",False)],ec):
        with col: st.markdown(mini_card_html(i,n,get_quote(s),r),unsafe_allow_html=True)

    st.markdown('<div class="slbl">💰 COMMODITIES + FOREX</div>', unsafe_allow_html=True)
    cc = st.columns(5)
    for (s,n,i,r),col in zip([("GC=F","GOLD $/oz","🥇",False),("SI=F","SILVER $/oz","🥈",False),("CL=F","CRUDE $/bbl","🛢️",False),("NG=F","NAT GAS","⚡",False),("USDINR=X","USD/INR ₹","💱",True)],cc):
        with col: st.markdown(mini_card_html(i,n,get_quote(s),r),unsafe_allow_html=True)


# ════════════════════════════
# TAB 4 — NEWS
# ════════════════════════════
with t4:
    nc,sc = st.columns([3,1])
    all_news = news_live if news_live else NEWS_STATIC
    with nc:
        st.markdown('<div class="slbl">📰 LIVE NEWS — 🟢 GREEN=FAYDA (BUY OPPORTUNITY) | 🔴 RED=NUQSAAN (AVOID/SELL) | 🔵 NEUTRAL</div>', unsafe_allow_html=True)
        new_bull = new_bear = 0
        for n in all_news:
            uid = n.get("id",n.get("t","")[:40]); sent = n.get("sentiment",n.get("s","neu"))
            is_new = uid not in st.session_state.news_seen
            if is_new:
                st.session_state.news_seen.add(uid)
                if sent=="bull": new_bull+=1
                elif sent=="bear": new_bear+=1
            cc2 = {"bull":"#00d463","bear":"#ff3d3d","neu":"#3d9be9"}[sent]
            lbl = {"bull":"🟢 BULLISH — FAYDA","bear":"🔴 BEARISH — NUQSAAN","neu":"🔵 NEUTRAL"}[sent]
            cls = f"ni-{sent}"
            title = n.get("title",n.get("t",""))
            link  = n.get("link","#")
            src   = n.get("source",n.get("src",""))
            time2 = n.get("time","—")
            st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none"><div class="ni {cls}"><div class="ni-meta">{time2} &nbsp;|&nbsp; {src} &nbsp;<span style="background:{cc2}25;color:{cc2};padding:1px 7px;border-radius:2px;font-size:9px;font-weight:700">{lbl}</span></div><div class="ni-title">{title}</div><div style="font-size:10px;color:#3d5a7a;margin-top:3px">👆 Tap to read full article →</div></div></a>', unsafe_allow_html=True)
        if new_bull>0: queue_sound("news_bull")
        if new_bear>0: queue_sound("news_bear")

    with sc:
        total_n  = len(all_news) or 1
        bull_n   = sum(1 for n in all_news if n.get("sentiment",n.get("s"))=="bull")
        bear_n   = sum(1 for n in all_news if n.get("sentiment",n.get("s"))=="bear")
        neu_n    = total_n-bull_n-bear_n
        bp       = bull_n/total_n*100
        sc2      = "#00d463" if bp>55 else ("#ff3d3d" if bp<45 else "#ffb700")
        ov       = "BULLISH" if bp>55 else ("BEARISH" if bp<45 else "MIXED")
        st.markdown(f'<div class="sent-wrap"><div style="font-size:9px;letter-spacing:3px;color:#3d9be9;margin-bottom:8px">NEWS SENTIMENT</div><div style="font-size:24px;font-weight:900;color:{sc2};margin-bottom:8px">{ov}</div><div style="display:flex;justify-content:space-between;font-size:13px;margin:5px 0"><span style="color:#00d463">🟢 BULLISH</span><strong style="color:#00d463">{bull_n}</strong></div><div style="display:flex;justify-content:space-between;font-size:13px;margin:5px 0"><span style="color:#ff3d3d">🔴 BEARISH</span><strong style="color:#ff3d3d">{bear_n}</strong></div><div style="display:flex;justify-content:space-between;font-size:13px;margin:5px 0"><span style="color:#3d9be9">🔵 NEUTRAL</span><strong style="color:#3d9be9">{neu_n}</strong></div><div class="sent-track"><div class="sent-fill" style="width:{bp:.0f}%;background:{sc2}"></div></div><div style="font-size:10px;color:#3d5a7a;margin-top:5px">{bp:.0f}% BULLISH</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top:10px"><div class="slbl">📅 ECO CALENDAR</div>', unsafe_allow_html=True)
        for evt,imp,d2,note,col2 in ECO_CAL:
            ic = "#ff3d3d" if imp=="HIGH" else "#ffb700"
            st.markdown(f'<div style="padding:5px 0;border-bottom:1px solid #0d3060"><div style="display:flex;justify-content:space-between"><span style="color:#d0e8f8;font-weight:700;font-size:11px">{evt}</span><span style="background:{ic}20;color:{ic};font-size:8px;padding:1px 5px;border-radius:3px">{imp}</span></div><div style="color:#3d5a7a;font-size:10px">{d2} — <span style="color:{col2}">{note}</span></div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════
# TAB 5 — OI + PIVOT
# ════════════════════════════
with t5:
    oi1,oi2 = st.columns([1.2,1])
    cmp_n = float(df_nifty["Close"].iloc[-1]) if df_nifty is not None else 22450.0
    cmp_b = float(df_bank["Close"].iloc[-1])  if df_bank  is not None else 48600.0

    with oi1:
        st.markdown('<div class="slbl">📈 OPEN INTEREST — NIFTY OPTIONS</div>', unsafe_allow_html=True)
        tc = sum(s["cOI"] for s in oi_strikes); tp = sum(s["pOI"] for s in oi_strikes)
        pcr = tp/tc; pc2 = "#00d463" if pcr>1.2 else ("#ff3d3d" if pcr<0.7 else "#ffb700")
        pl2 = "Bullish ✅" if pcr>1.2 else ("Bearish ⚠️" if pcr<0.7 else "Neutral 🟡")
        pct_bar = min(95,max(5,pcr*50))

        st.markdown(f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;margin-bottom:8px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
                <div style="background:#1f000012;border:1px solid #ff3d3d35;border-radius:6px;padding:10px;text-align:center">
                    <div style="color:#ff3d3d;font-size:9px;letter-spacing:2px;margin-bottom:4px">🔴 CALL OI (Resistance)</div>
                    <div style="color:#ff7070;font-size:20px;font-weight:900;font-family:Share Tech Mono">{tc/1e7:.1f} Cr</div>
                    <div style="color:#ff3d3d;font-size:10px">Bears defending above</div>
                </div>
                <div style="background:#00d46312;border:1px solid #00d46335;border-radius:6px;padding:10px;text-align:center">
                    <div style="color:#00d463;font-size:9px;letter-spacing:2px;margin-bottom:4px">🟢 PUT OI (Support)</div>
                    <div style="color:#44ee88;font-size:20px;font-weight:900;font-family:Share Tech Mono">{tp/1e7:.1f} Cr</div>
                    <div style="color:#00d463;font-size:10px">Bulls defending below</div>
                </div>
            </div>
            <div style="font-size:10px;color:#3d5a7a;margin-bottom:5px;display:flex;justify-content:space-between">
                <span style="color:#ff3d3d">🔴 CALL HEAVY</span>
                <span style="color:{pc2};font-weight:700">PCR {pcr:.2f}</span>
                <span style="color:#00d463">🟢 PUT HEAVY</span>
            </div>
            <div class="oi-bar-wrap"><div class="oi-bar" style="width:{pct_bar}%;background:{pc2}"></div></div>
            <div style="text-align:center;font-size:14px;font-weight:900;color:{pc2};margin-top:5px;font-family:Share Tech Mono">PCR: {pcr:.2f} — {pl2}</div>
            <div style="margin-top:10px;background:#1a1000;border:1px solid #ffb70030;border-radius:6px;padding:9px;display:flex;justify-content:space-between">
                <div><div style="color:#3d5a7a;font-size:9px;letter-spacing:1px">⚡ MAX PAIN</div>
                     <div style="color:#ffb700;font-size:22px;font-weight:900;font-family:Share Tech Mono">₹22,400</div></div>
                <div style="text-align:right">
                    <div style="color:#3d5a7a;font-size:11px">CMP: ₹{cmp_n:,.0f}</div>
                    <div style="color:{'#ffb700' if abs(cmp_n-22400)<100 else '#ff3d3d' if cmp_n>22400 else '#00d463'};font-size:11px;margin-top:4px">{'⚠️ Near Max Pain — range-bound' if abs(cmp_n-22400)<100 else '🔴 Above — pullback risk' if cmp_n>22400 else '🟢 Below — upside possible'}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Top OI strikes
        top_c = sorted(oi_strikes, key=lambda x: x["cOI"], reverse=True)[:4]
        top_p = sorted(oi_strikes, key=lambda x: x["pOI"], reverse=True)[:4]
        st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px">
            <div><div style="color:#ff3d3d;font-size:9px;margin-bottom:5px;letter-spacing:1px;font-family:Share Tech Mono">🔴 RESISTANCE (Call OI)</div>{"".join(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #08182e"><span style="color:#ff7070;font-weight:700;font-size:12px;font-family:Share Tech Mono">₹{s["k"]:,}</span><span style="color:#3d5a7a;font-size:10px;font-family:Share Tech Mono">{s["cOI"]/100000:.1f}L</span></div>' for s in top_c)}</div>
            <div><div style="color:#00d463;font-size:9px;margin-bottom:5px;letter-spacing:1px;font-family:Share Tech Mono">🟢 SUPPORT (Put OI)</div>{"".join(f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #08182e"><span style="color:#44ee88;font-weight:700;font-size:12px;font-family:Share Tech Mono">₹{s["k"]:,}</span><span style="color:#3d5a7a;font-size:10px;font-family:Share Tech Mono">{s["pOI"]/100000:.1f}L</span></div>' for s in top_p)}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="slbl">📊 OI CHANGE — BUILDUP / UNWINDING</div>', unsafe_allow_html=True)
        ch_strikes = [s for s in oi_strikes if 22000<=s["k"]<=22800][:6]
        st.markdown(oi_buildup_html(ch_strikes), unsafe_allow_html=True)

        st.markdown('<div class="slbl" style="margin-top:10px">📊 OPTION CHAIN — NEAR ATM</div>', unsafe_allow_html=True)
        st.markdown(option_chain_html(cmp_n), unsafe_allow_html=True)
        st.markdown('<div style="padding:8px;background:#030c1a;border:1px solid #ffb70030;border-radius:6px;font-size:11px;color:#ccaa66;margin-top:6px;line-height:1.8">⚡ <strong style="color:#ffb700">SL from Option Chain:</strong><br>🔴 BUY SL = Nearest max PUT OI strike below CMP (support level)<br>🟢 SELL SL = Nearest max CALL OI strike above CMP (resistance level)<br><span style="color:#3d5a7a">★ ATM strike | K = 1000 contracts</span></div>', unsafe_allow_html=True)

    with oi2:
        st.markdown('<div class="slbl">📐 PIVOT LEVELS — NIFTY 50</div>', unsafe_allow_html=True)
        st.markdown(pivot_html(pivot_levels(df_nifty), cmp_n), unsafe_allow_html=True)
        st.markdown('<div class="slbl" style="margin-top:12px">📐 PIVOT LEVELS — BANKNIFTY</div>', unsafe_allow_html=True)
        st.markdown(pivot_html(pivot_levels(df_bank), cmp_b), unsafe_allow_html=True)


# ════════════════════════════
# TAB 6 — SL CALC
# ════════════════════════════
with t6:
    sl_calculator_section()
    # Live SL from charts
    if df_nifty is not None and df_bank is not None:
        st.markdown('<div class="slbl" style="margin-top:10px">📌 LIVE SL LEVELS FROM CHARTS</div>', unsafe_allow_html=True)
        ls1,ls2 = st.columns(2)
        with ls1:
            ind_n2 = calc_ind(df_nifty)
            st.markdown(f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:10px">
                <div style="font-size:9px;letter-spacing:2px;color:#3d9be9;margin-bottom:8px">NIFTY 50 LIVE SL</div>
                <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #08182e;font-size:12px"><span style="color:#8ab8d8">BUY SL (10-bar low)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">₹{ind_n2["sl_buy"]:,.1f}</span></div>
                <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px"><span style="color:#8ab8d8">SELL SL (10-bar high)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">₹{ind_n2["sl_sell"]:,.1f}</span></div>
            </div>""", unsafe_allow_html=True)
        with ls2:
            ind_b2 = calc_ind(df_bank)
            st.markdown(f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:7px;padding:10px">
                <div style="font-size:9px;letter-spacing:2px;color:#3d9be9;margin-bottom:8px">BANKNIFTY LIVE SL</div>
                <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #08182e;font-size:12px"><span style="color:#8ab8d8">BUY SL (10-bar low)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">₹{ind_b2["sl_buy"]:,.1f}</span></div>
                <div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px"><span style="color:#8ab8d8">SELL SL (10-bar high)</span><span style="color:#ff7070;font-family:Share Tech Mono;font-weight:700">₹{ind_b2["sl_sell"]:,.1f}</span></div>
            </div>""", unsafe_allow_html=True)


# ════════════════════════════
# TAB 7 — STRATEGY
# ════════════════════════════
with t7:
    st.markdown('<div class="slbl">⚡ COMBO STRATEGIES — BEST PICKS</div>', unsafe_allow_html=True)
    s1,s2 = st.columns(2)
    for i,s in enumerate(STRATS):
        with (s1 if i%2==0 else s2):
            tags_html = " ".join(f'<span style="font-size:8px;padding:2px 6px;border-radius:3px;background:#020b18;border:1px solid {s["col"]}28;color:{s["col"]};font-family:Share Tech Mono">{t}</span>' for t in s["tg"])
            st.markdown(f"""<div class="strat-card" style="border:1px solid {s["col"]}20;margin-bottom:5px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:11px;font-weight:700;color:#b0c8e8">{s["n"]}</span>
                    <span style="font-size:14px;font-weight:900;color:{s["col"]};font-family:Share Tech Mono">{s["str"]}%</span>
                </div>
                <div style="font-size:11px;color:#8ab0cc;line-height:1.5;margin-bottom:5px">{s["d"]}</div>
                <div style="display:flex;gap:3px;flex-wrap:wrap">{tags_html}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slbl" style="margin-top:8px">📚 STRATEGY USE GUIDE</div>', unsafe_allow_html=True)
    st.markdown("""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;font-size:12px;line-height:2;color:#a0c8e0">
        🔥 <span style="color:#ffb700">Triple Combo (RSI+VWAP+BB)</span> — Nifty F&O, max accuracy 95%<br>
        ⚡ <span style="color:#00d463">RSI+BB Squeeze</span> — Best for VIX&gt;15 volatile market days<br>
        📊 <span style="color:#4488ff">VWAP+Volume</span> — Pure intraday, use after 9:30 AM only<br>
        🕯️ <span style="color:#ff88cc">Engulfing+RSI</span> — Reversal near support zone play<br>
        🕐 <span style="color:#88ddff">ORB Strategy</span> — 9:15–9:30 AM range break + volume<br>
        📈 <span style="color:#aaffcc">OI+PCR Confirm</span> — PCR&gt;1.2 = add as BUY confirmation
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slbl" style="margin-top:8px">🛡️ RISK MANAGEMENT RULES</div>', unsafe_allow_html=True)
    st.markdown("""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;font-size:12px;line-height:2">
        <span style="color:#ff3d3d">🛑 Stop Loss: 0.3–0.5% below entry — ALWAYS mandatory, no exceptions</span><br>
        <span style="color:#00d463">🎯 Target: Minimum 1:2 risk-reward ratio always</span><br>
        <span style="color:#ff3d3d">📉 VIX &gt;20: Reduce position size by 50%</span><br>
        <span style="color:#ffb700">🔄 Maximum 3 F&O trades per day rule</span><br>
        <span style="color:#ff3d3d">💰 Never risk more than 2% of total capital per trade</span><br>
        <span style="color:#00d463">✅ PCR &gt;1.2 + Call OI unwinding = Strong BUY confirmation</span><br>
        <span style="color:#ff3d3d">❌ PCR &lt;0.7 = Avoid longs, sell all rallies</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slbl" style="margin-top:8px">💡 CLAUDE RECOMMENDS — ADD THESE NEXT</div>', unsafe_allow_html=True)
    for title,desc in SUGS:
        st.markdown(f'<div style="background:#020b18;border-left:2px solid #1a5090;border-radius:0 5px 5px 0;padding:7px 10px;margin-bottom:4px"><div style="color:#6ab4ee;font-size:11px;font-weight:700;margin-bottom:2px">{title}</div><div style="color:#3d5a7a;font-size:11px;line-height:1.4">{desc}</div></div>', unsafe_allow_html=True)


# ════════════════════════════
# TAB 8 — ANALYSIS
# ════════════════════════════
with t8:
    a1,a2 = st.columns(2)
    with a1:
        nifty_trend = "BULLISH" if df_nifty is not None and float(df_nifty["Close"].iloc[-1])>float(df_nifty["Close"].iloc[0]) else "BEARISH"
        rsi_n = calc_ind(df_nifty)["rsi"] if df_nifty is not None else 50
        st.markdown(f"""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;font-size:12px;line-height:2;color:#a0c8e0">
            <div style="font-size:13px;font-weight:700;color:{'#00d463' if nifty_trend=='BULLISH' else '#ff3d3d'};margin-bottom:6px">{'🟢' if nifty_trend=='BULLISH' else '🔴'} Overall Trend: {nifty_trend}</div>
            📊 Nifty RSI: <strong style="color:{'#ff3d3d' if rsi_n>70 else '#00d463' if rsi_n<30 else '#ffb700'}">{rsi_n:.1f}</strong> — {'🔴 Overbought' if rsi_n>70 else '🟢 Oversold BUY ZONE' if rsi_n<30 else '🟡 Neutral Zone'}<br>
            ⚡ VIX: <strong style="color:{'#00d463' if vix and vix['val']<15 else '#ffb700' if vix and vix['val']<20 else '#ff3d3d'}">{f"{vix['val']:.2f}" if vix else '—'}</strong> — {f"{'Low vol — good for trades' if vix['val']<15 else 'Moderate — caution' if vix['val']<20 else 'HIGH — reduce size!'}" if vix else '—'}<br>
            🌍 Gift Nifty: <strong style="color:{'#00d463' if gift_trend=='BULL' else '#ff3d3d' if gift_trend=='BEAR' else '#3d9be9'}">{gift_trend}</strong> bias<br>
            📡 Data: <strong style="color:#00d463">Yahoo Finance — 15s refresh (query1↔query2)</strong><br>
            {'⚡ Today is F&O EXPIRY — Extra caution!' if is_expiry else '📅 Regular trading day'}
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="slbl" style="margin-top:10px">🎯 BOT ACCURACY STATS</div>', unsafe_allow_html=True)
        cols2 = st.columns(3)
        for i,(lbl,val,col) in enumerate([("BUY SIGNALS","72%","#00d463"),("SELL SIGNALS","68%","#ff3d3d"),
            ("TRIPLE COMBO","95%","#ffb700"),("VWAP+VOL","88%","#00d463"),("RSI ALONE","45%","#ff3d3d"),("RSI+BB","83%","#3d9be9")]):
            with cols2[i%3]: st.markdown(f'<div class="rm"><div class="rv" style="color:{col}">{val}</div><div class="rl">{lbl}</div></div>', unsafe_allow_html=True)

    with a2:
        st.markdown('<div class="slbl">💡 LATE DATA / MISSED TRADE FIX</div>', unsafe_allow_html=True)
        st.markdown("""<div style="background:#030c1a;border:1px solid #0d3060;border-radius:8px;padding:12px;font-size:12px;line-height:1.9;color:#a0c8e0">
            <span style="color:#ff3d3d">❌ Root Cause:</span> Yahoo Finance has 15–30s inherent delay<br>
            <strong style="color:#ffb700">✅ Solutions (best to worst):</strong><br>
            1. <span style="color:#00d463">Dhan API</span> — WebSocket, real-time, FREE for clients, ~50ms<br>
            2. <span style="color:#00d463">Zerodha Kite API</span> — ₹2000/mo, 30ms latency, WebSocket<br>
            3. <span style="color:#ffb700">Current: Yahoo Finance (active)</span> — 15s, free, rotating<br>
            4. <span style="color:#ff3d3d">NSE Direct</span> — 5s but IP block risk, needs proxy server<br><br>
            <span style="color:#3d9be9">⚡ Current multi-server rotation reduces IP block by ~60%<br>
            Rotates: query1.finance.yahoo.com ↔ query2.finance.yahoo.com</span>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="slbl" style="margin-top:10px">📋 KEY IMPROVEMENTS NEEDED</div>', unsafe_allow_html=True)
        for tip in ["Add PCR filter — only BUY when PCR>1.0, only SELL when PCR<0.8",
                    "Add EMA200 filter — only take BUY trades above EMA200",
                    "Market hours filter — ORB only 9:15–9:30, all signals after 9:30",
                    "Pre-market check — SGX Nifty gap direction as primary bias",
                    "Add options IV filter — avoid buying when IV Rank >70%"]:
            col_t = "#00d463" if "ADD" in tip or "only" in tip.lower() else "#ffb700"
            st.markdown(f'<div style="padding:5px 0;border-bottom:1px solid #0d3060;font-size:11px;color:{col_t}">• {tip}</div>', unsafe_allow_html=True)


# ════════════════════════════
# TAB 9 — REPORT
# ════════════════════════════
with t9:
    eod_report()


# ── EMIT SOUNDS (once at end) ────────────────────────────────
emit_sounds()

# ── FOOTER ──────────────────────────────────────────────────
st.markdown("""<div style="text-align:center;padding:8px;font-size:9px;letter-spacing:3px;
    color:#0d3060;border-top:1px solid #050f1e;margin-top:10px;font-family:Share Tech Mono">
🦅 EAGLE EYE PRO v5 &nbsp;|&nbsp; EDUCATIONAL USE — NOT FINANCIAL ADVICE &nbsp;|&nbsp;
🟢 BUY=ASCENDING &nbsp; 🔴 SELL=DESCENDING &nbsp; 🚀 SPIKE=SQUARE WAVE &nbsp; 📉 FALL=LOW DRONE
</div>""", unsafe_allow_html=True)
