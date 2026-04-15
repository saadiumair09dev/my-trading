# ══════════════════════════════════════════════════════════════════
#  🦅 EAGLE EYE PRO v2 — Full Rewrite
#  pip install streamlit yfinance pandas numpy pytz streamlit-autorefresh
# ══════════════════════════════════════════════════════════════════

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# ── PAGE CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title="🦅 Eagle Eye Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st_autorefresh(interval=30000, key="eagle_v2")
IST = pytz.timezone('Asia/Kolkata')

# ── SESSION STATE ─────────────────────────────────────────────────
for k, v in {
    "signals_log": [],
    "prev_sig":    {},
    "news_seen":   set(),
    "veto_log":    [],
    "sound_id":    0,
    "sound_queue": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══ CSS ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700;900&display=swap');

*, body { font-family: 'Rajdhani', sans-serif !important; }
.stApp { background: #020b18; color: #dce8f7; }
.block-container { padding: 0.3rem 0.8rem 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 3px; background: transparent;
    border-bottom: 1px solid #0d3060; padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    background: #050f1e; color: #3d9be9;
    border: 1px solid #0d3060; border-radius: 6px 6px 0 0;
    font-family: 'Rajdhani'; font-weight: 700;
    font-size: 11px; letter-spacing: 2px; padding: 5px 14px; border-bottom: none;
}
.stTabs [aria-selected="true"] { background: #0d3060 !important; color: #fff !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 6px !important; }

/* ── SIGNAL CARDS ── */
.sc {
    border-radius: 10px; padding: 12px 10px; text-align: center;
    border: 1px solid #0d3060; margin-bottom: 6px; min-height: 198px;
}
.sc-buy  { background: linear-gradient(145deg,#002716,#020b18); border-color:#00d463;
           box-shadow:0 0 22px rgba(0,212,99,0.2); animation: pg 2.5s infinite; }
.sc-sell { background: linear-gradient(145deg,#200000,#020b18); border-color:#ff1a1a;
           box-shadow:0 0 22px rgba(255,26,26,0.2); animation: pr 2.5s infinite; }
.sc-caut { background: linear-gradient(145deg,#2a1a00,#020b18); border-color:#ff9800;
           box-shadow:0 0 18px rgba(255,152,0,0.18); }
.sc-side { background: #050f1e; border-color:#ff9800; }
.sc-wait { background: #050f1e; border-color:#0d3060; opacity:0.7; }
@keyframes pg { 0%,100%{box-shadow:0 0 18px rgba(0,212,99,0.15)} 50%{box-shadow:0 0 38px rgba(0,212,99,0.4)} }
@keyframes pr { 0%,100%{box-shadow:0 0 18px rgba(255,26,26,0.15)} 50%{box-shadow:0 0 38px rgba(255,26,26,0.4)} }

.sc-name  { font-size:10px; opacity:0.5; letter-spacing:2px; margin-bottom:2px; }
.sc-price { font-size:30px; font-weight:700; font-family:'Share Tech Mono'; line-height:1.1; }
.sc-sig   { font-size:15px; font-weight:900; letter-spacing:3px; margin:3px 0; }
.sc-dots  { font-size:13px; letter-spacing:5px; margin:3px 0; }
.sc-bar   { font-size:9px; color:#3d5a7a; display:flex; justify-content:space-around;
            flex-wrap:wrap; gap:2px; margin-top:5px; }
.sc-entry { font-size:10px; margin-top:5px; padding:4px 7px;
            background:rgba(61,155,233,0.07); border:1px solid #0d3060; border-radius:4px; }
.sc-bge   { font-size:8px; letter-spacing:2px; font-weight:700;
            padding:1px 7px; border-radius:2px; display:inline-block; margin-bottom:3px; }
.sc-time  { font-size:8px; color:#1e3a5f; margin-top:4px; font-family:'Share Tech Mono'; }

/* ── MINI CARDS ── */
.mc { background:#050f1e; border:1px solid #0d3060; border-radius:7px;
      padding:8px 4px; text-align:center; margin-bottom:5px; }
.mc-ico { font-size:14px; }
.mc-nm  { font-size:7px; letter-spacing:2px; color:#3d5a7a; margin:2px 0; }
.mc-pr  { font-size:14px; font-weight:700; font-family:'Share Tech Mono'; }
.mc-ch  { font-size:10px; font-weight:700; }
.pos { color:#00d463; } .neg { color:#ff1a1a; } .neu { color:#3d9be9; }

/* ── NEWS ── */
.ni { border-radius:5px; padding:7px 9px; margin:3px 0; border-left:3px solid;
      font-size:11px; line-height:1.4; display:block; color:inherit !important;
      text-decoration:none !important; transition: opacity 0.2s; }
.ni:hover { opacity:0.75; }
.ni-bull { background:rgba(0,212,99,0.05);  border-color:#00d463; }
.ni-bear { background:rgba(255,26,26,0.05); border-color:#ff1a1a; }
.ni-neu  { background:rgba(61,155,233,0.05);border-color:#3d9be9; }
.ni-m { font-size:8px; color:#3d5a7a; margin-bottom:2px; }

/* ── REPORT ── */
.rm { background:#050f1e; border:1px solid #0d3060; border-radius:7px;
      padding:8px 6px; text-align:center; }
.rv { font-size:20px; font-weight:700; font-family:'Share Tech Mono'; }
.rl { font-size:7px; letter-spacing:2px; color:#3d9be9; margin-top:2px; }

/* ── SENTIMENT ── */
.sentb { background:#050f1e; border:1px solid #0d3060; border-radius:8px; padding:12px 10px; text-align:center; }
.pb { background:#0d3060; height:5px; border-radius:3px; overflow:hidden; margin-top:8px; }

/* ── LABELS ── */
.slbl { font-size:8px; letter-spacing:3px; font-weight:700; color:#3d9be9;
        border-left:2px solid #3d9be9; padding:1px 0 1px 7px; margin:8px 0 5px; }
</style>
""", unsafe_allow_html=True)

# ══ SOUND ENGINE ══════════════════════════════════════════════════
# Approach: store AudioContext in window.parent from the enable-button iframe.
# play_sound iframes access window.parent._EC directly.
# Both postMessage (to sound_mgr) and direct play are attempted.

SOUND_NOTES = {
    "buy":  ([523, 659, 784, 1047], "sine",     0.40, 0.12),
    "sell": ([494, 392, 330, 247],  "sawtooth", 0.40, 0.12),
    "news": ([440, 550, 440],       "triangle", 0.30, 0.15),
    "vix":  ([350, 280, 220],       "square",   0.28, 0.15),
}

def sound_enable_btn():
    """Renders a small enable-sound button that also acts as sound receiver."""
    components.html("""
    <style>
    body { margin:0; background:transparent; }
    .sb { background:#050f1e; border:1px solid #0d3060; color:#3d9be9;
          padding:3px 10px; border-radius:4px; cursor:pointer;
          font-size:9px; letter-spacing:2px; font-family:monospace;
          white-space:nowrap; }
    .sb.on { border-color:#00d463; color:#00d463; background:#002710; }
    </style>
    <button class="sb" id="sb" onclick="initSnd()">🔇 ENABLE SOUND</button>
    <script>
    var C = null;
    var on = sessionStorage.getItem('esnd') === '1';
    var btn = document.getElementById('sb');

    if (on) {
        btn.textContent = '🔊 SOUND ON';
        btn.className = 'sb on';
        try {
            C = new (window.parent.AudioContext || window.parent.webkitAudioContext || AudioContext)();
            window.parent._EC = C;
            window.parent._ES = true;
        } catch(e) {}
    }

    function initSnd() {
        try {
            var Ctx = window.parent.AudioContext || window.parent.webkitAudioContext
                   || window.AudioContext || window.webkitAudioContext;
            C = new Ctx();
            C.resume();
            window.parent._EC = C;
            window.parent._ES = true;
            on = true;
            sessionStorage.setItem('esnd', '1');
            btn.textContent = '🔊 SOUND ON';
            btn.className = 'sb on';
            _play([523, 659, 784], 'sine', 0.3, 0.1);
        } catch(e) { btn.textContent = '⚠️ NO AUDIO'; }
    }

    function _play(notes, wave, vol, dur) {
        var ctx = C || window.parent._EC;
        if (!ctx) return;
        notes.forEach(function(f, i) {
            var t = ctx.currentTime + i * (dur + 0.04);
            var o = ctx.createOscillator(), g = ctx.createGain();
            o.type = wave; o.frequency.value = f;
            g.gain.setValueAtTime(vol, t);
            g.gain.exponentialRampToValueAtTime(0.001, t + dur);
            o.connect(g); g.connect(ctx.destination);
            o.start(t); o.stop(t + dur + 0.02);
        });
    }

    // Listen for sound trigger messages from sibling iframes
    window.addEventListener('message', function(e) {
        if (!e.data || !e.data.eagle) return;
        var s = e.data.eagle;
        if (!on && !window.parent._ES) return;
        var n = {'buy':[523,659,784,1047],'sell':[494,392,330,247],'news':[440,550,440],'vix':[350,280,220]};
        var w = {'buy':'sine','sell':'sawtooth','news':'triangle','vix':'square'};
        if (n[s]) _play(n[s], w[s] || 'sine', 0.4, 0.12);
    });
    </script>
    """, height=30)


def queue_sound(snd: str):
    st.session_state.sound_queue.append(snd)


def emit_queued_sounds():
    """Call ONCE at end of main render to emit the highest-priority sound."""
    q = st.session_state.sound_queue
    if not q:
        return
    priority = {"vix": 4, "sell": 3, "buy": 2, "news": 1}
    best = max(q, key=lambda s: priority.get(s, 0))
    st.session_state.sound_queue = []

    sid = st.session_state.sound_id + 1
    st.session_state.sound_id = sid
    notes, wave, vol, dur = SOUND_NOTES[best]

    components.html(f"""
    <script>
    (function() {{
        // 1. Send postMessage to all iframes (catches sound_mgr)
        try {{
            var frames = window.parent.document.querySelectorAll('iframe');
            frames.forEach(function(f) {{
                try {{ f.contentWindow.postMessage({{eagle:'{best}', id:{sid}}}, '*'); }} catch(e) {{}}
            }});
        }} catch(e) {{}}

        // 2. Direct play via parent AudioContext (most reliable)
        try {{
            var C = window.parent._EC;
            if (!C || !window.parent._ES) return;
            var notes = {notes};
            var dur = {dur}, vol = {vol};
            notes.forEach(function(f, i) {{
                var t = C.currentTime + i * (dur + 0.04);
                var o = C.createOscillator(), g = C.createGain();
                o.type = '{wave}'; o.frequency.value = f;
                g.gain.setValueAtTime(vol, t);
                g.gain.exponentialRampToValueAtTime(0.001, t + dur);
                o.connect(g); g.connect(C.destination);
                o.start(t); o.stop(t + dur + 0.02);
            }});
        }} catch(e) {{}}
    }})();
    </script>
    """, height=1)


# ══ DATA FUNCTIONS (cached) ═══════════════════════════════════════

def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(ttl=25)
def get_local_data(symbol: str) -> pd.DataFrame | None:
    try:
        df = yf.download(symbol, period="1d", interval="1m", progress=False, auto_adjust=True)
        df = _flatten(df)
        df.dropna(subset=['Close', 'Volume'], inplace=True)
        return df if len(df) >= 21 else None
    except Exception:
        return None


@st.cache_data(ttl=55)
def get_gift_data() -> pd.DataFrame | None:
    """GIFT Nifty 15m — IN=F first, fallback to ^NSEI"""
    for sym in ["IN=F", "^NSEI"]:
        try:
            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            df = _flatten(df)
            df.dropna(subset=['Close'], inplace=True)
            if len(df) >= 3:
                return df
        except Exception:
            continue
    return None


@st.cache_data(ttl=55)
def get_vix() -> dict | None:
    for sym in ["^INDIAVIX", "^VIX"]:
        try:
            df = yf.download(sym, period="5d", interval="1d", progress=False, auto_adjust=True)
            df = _flatten(df)
            df.dropna(subset=['Close'], inplace=True)
            if len(df) >= 2:
                v  = float(df['Close'].iloc[-1])
                vp = float(df['Close'].iloc[-2])
                chg = (v - vp) / vp * 100
                return {"val": v, "chg": chg, "high": v > 20, "spike": chg > 15}
        except Exception:
            continue
    return None


@st.cache_data(ttl=45)
def get_quote(symbol: str) -> dict | None:
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
        df = _flatten(df)
        df.dropna(subset=['Close'], inplace=True)
        if len(df) >= 2:
            p  = float(df['Close'].iloc[-1])
            pp = float(df['Close'].iloc[-2])
            return {"price": p, "chg": (p - pp) / pp * 100}
    except Exception:
        pass
    return None


@st.cache_data(ttl=120)
def get_news() -> list:
    BULL = {'rally','surge','gain','rise','rises','record','growth','positive','bullish',
            'strong','jump','soar','beats','exceeds','upgrade','buy','rebound','recovery',
            'boost','profit','boom','optimistic','support','up','upbeat','robust'}
    BEAR = {'fall','falls','decline','drop','crash','loss','weak','bearish','sell',
            'downgrade','recession','fear','risk','concern','miss','disappoint','slump',
            'tumble','plunge','low','warning','cut','below','slowdown','tension','turmoil'}
    seen, results = set(), []
    for sym in ["^NSEI", "^NSEBANK", "GC=F", "CL=F", "ES=F"]:
        try:
            items = yf.Ticker(sym).news or []
            for item in items[:5]:
                t   = item.get('title', '').strip()
                uid = item.get('uuid', t[:40])
                if not t or uid in seen: continue
                seen.add(uid)
                tl    = t.lower()
                b     = sum(1 for w in BULL if w in tl)
                r     = sum(1 for w in BEAR if w in tl)
                sent  = "bull" if b > r else ("bear" if r > b else "neu")
                ts    = item.get('providerPublishTime', 0)
                tstr  = datetime.fromtimestamp(ts, tz=IST).strftime("%H:%M") if ts else "—"
                results.append({
                    "title": t, "sentiment": sent, "time": tstr,
                    "source": item.get('publisher', ''),
                    "id": uid, "link": item.get('link', '#'),
                })
        except Exception:
            continue
    return results


# ══ SIGNAL ENGINE ════════════════════════════════════════════════

def compute_signal(symbol: str, gift_df: pd.DataFrame | None, vix: dict | None) -> dict | None:
    df = get_local_data(symbol)
    if df is None or gift_df is None:
        return None

    price = float(df['Close'].iloc[-1])
    vol   = df['Volume'].replace(0, np.nan)

    # VWAP (cumulative intraday)
    vwap = float((df['Close'] * vol).cumsum().iloc[-1] / vol.cumsum().iloc[-1])

    # EMA 9 / 21
    ema9  = float(df['Close'].ewm(span=9,  adjust=False).mean().iloc[-1])
    ema21 = float(df['Close'].ewm(span=21, adjust=False).mean().iloc[-1])

    # RSI 14
    delta = df['Close'].diff()
    ag    = delta.clip(lower=0).rolling(14).mean()
    al    = (-delta.clip(upper=0)).rolling(14).mean()
    rsi   = float((100 - 100 / (1 + ag / al.replace(0, np.nan))).iloc[-1])

    # Volume: current vs 20-bar EMA
    vol_ema   = float(vol.ewm(span=20, adjust=False).mean().iloc[-1])
    cur_vol   = float(vol.iloc[-1])
    vol_ratio = cur_vol / vol_ema if vol_ema > 0 else 1.0
    vol_spike = vol_ratio >= 1.5

    # 5-bar momentum
    mom_pct = float((price - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100) if len(df) >= 5 else 0.0

    # GIFT Nifty (15m trend)
    g_now  = float(gift_df['Close'].iloc[-1])
    g_prev = float(gift_df['Close'].iloc[-2])
    g_chg  = (g_now - g_prev) / g_prev * 100
    if g_chg > 0.05:
        gift_trend = "BULL"
    elif g_chg < -0.05:
        gift_trend = "BEAR"
    else:
        gift_trend = "NEUTRAL"

    # ── SIDEWAYS FILTER ──
    ema_gap_pct  = abs(ema9 - ema21) / price * 100
    between_emas = min(ema9, ema21) <= price <= max(ema9, ema21)
    sideways     = ema_gap_pct < 0.08 or between_emas

    # ── LOCAL TREND SCORE ──
    bull_pts = int(price > vwap) + int(ema9 > ema21) + int(rsi > 54)
    bear_pts = int(price < vwap) + int(ema9 < ema21) + int(rsi < 46)
    local_trend = "BULL" if bull_pts >= 2 else ("BEAR" if bear_pts >= 2 else "NEUTRAL")

    # ── 4-DOT SYSTEM ──
    # Dot 1: EMA cross  | Dot 2: VWAP  | Dot 3: RSI  | Dot 4: Volume
    is_bull_context = local_trend == "BULL"
    is_bear_context = local_trend == "BEAR"
    dot1 = (ema9 > ema21) if is_bull_context else (ema9 < ema21)
    dot2 = (price > vwap) if is_bull_context else (price < vwap)
    dot3 = (rsi > 54)     if is_bull_context else (rsi < 46)
    dot4 = vol_spike
    dots = sum([dot1, dot2, dot3, dot4])

    # ── SL CALCULATION ──
    recent_low  = float(df['Low'].iloc[-10:].min())  if 'Low'  in df.columns else price * 0.997
    recent_high = float(df['High'].iloc[-10:].max()) if 'High' in df.columns else price * 1.003
    sl_buy  = recent_low  - price * 0.001   # tiny buffer below swing low
    sl_sell = recent_high + price * 0.001   # tiny buffer above swing high

    # ── PULLBACK ENTRY QUALITY ──
    pb_dist = abs(price - ema9) / price * 100
    if local_trend == "BULL":
        if pb_dist <= 0.15:
            eq = "✅ IDEAL — AT EMA9 PULLBACK"
        elif price > ema9 and pb_dist > 0.40:
            eq = f"⚠️ HIGH ENTRY  |  PULLBACK TARGET ₹{ema9:,.0f}"
        else:
            eq = "🟡 ACCEPTABLE ENTRY"
    elif local_trend == "BEAR":
        if pb_dist <= 0.15:
            eq = "✅ IDEAL — AT EMA9 PULLBACK SHORT"
        elif price < ema9 and pb_dist > 0.40:
            eq = f"⚠️ LOW ENTRY  |  PULLBACK TARGET ₹{ema9:,.0f}"
        else:
            eq = "🟡 ACCEPTABLE SHORT"
    else:
        eq = "⏳ NO ENTRY"

    # ── FINAL SIGNAL ──
    if sideways:
        signal, zone = "SIDEWAYS — WAIT", "sc-side"
        caution = False

    elif gift_trend == "BULL" and local_trend == "BULL":
        if dots >= 3:
            signal = "🚀 SUPER BUY" if vol_spike else "🚀 BUY (LOW VOL)"
            zone   = "sc-buy"
        else:
            signal, zone = "⚠️ WEAK BUY", "sc-caut"
        caution = not vol_spike

    elif gift_trend == "BEAR" and local_trend == "BEAR":
        if dots >= 3:
            signal = "📉 SUPER SELL" if vol_spike else "📉 SELL (LOW VOL)"
            zone   = "sc-sell"
        else:
            signal, zone = "⚠️ WEAK SELL", "sc-caut"
        caution = not vol_spike

    elif local_trend == "BULL" and gift_trend == "BEAR":
        signal, zone, caution = "BUY ⚠️ GIFT BEARISH", "sc-caut", True

    elif local_trend == "BEAR" and gift_trend == "BULL":
        signal, zone, caution = "SELL ⚠️ GIFT BULLISH", "sc-caut", True

    else:
        signal, zone, caution = "⏳ NO SYNC", "sc-wait", False

    # ── VIX OVERRIDE ──
    vix_warn = False
    if vix and (vix['high'] or vix['spike']):
        vix_warn = True
        if "SUPER" in signal:
            signal = signal.replace("SUPER ", "")
            signal = signal + " (VIX HIGH)"
            zone   = "sc-caut"

    return {
        "signal": signal, "zone": zone, "caution": caution, "vix_warn": vix_warn,
        "sideways": sideways,
        "price": price, "vwap": vwap, "ema9": ema9, "ema21": ema21,
        "rsi": rsi, "vol_ratio": vol_ratio, "vol_spike": vol_spike,
        "dot1": dot1, "dot2": dot2, "dot3": dot3, "dot4": dot4, "dots": dots,
        "gift_trend": gift_trend, "gift_price": g_now, "gift_chg": g_chg,
        "local_trend": local_trend, "mom_pct": mom_pct,
        "sl_buy": sl_buy, "sl_sell": sl_sell,
        "entry_quality": eq, "pullback_target": ema9,
        "bull_pts": bull_pts, "bear_pts": bear_pts,
        "time": datetime.now(IST).strftime("%H:%M:%S"),
        "timestamp": datetime.now(IST),
    }


# ══ SIGNAL LOGGING ═══════════════════════════════════════════════

def log_signal(symbol_key: str, name: str, r: dict | None):
    if r is None:
        return
    now  = datetime.now(IST)
    sig  = r['signal']
    prev = st.session_state.prev_sig.get(symbol_key, {})

    # Log new meaningful signals
    skip = {"⏳ NO SYNC", "SIDEWAYS — WAIT"}
    if sig not in skip and sig != prev.get("signal", ""):
        st.session_state.signals_log.append({
            "entry_time":  now.strftime("%H:%M:%S"),
            "log_dt":      now,
            "symbol":      name,
            "signal":      sig,
            "entry_price": r['price'],
            "vwap":        r['vwap'],
            "rsi":         r['rsi'],
            "mom_pct":     r['mom_pct'],
            "dots":        r['dots'],
            "vol_ratio":   r['vol_ratio'],
            "gift_trend":  r['gift_trend'],
            "evaluated":   False,
            "result":      None,
            "exit_price":  None,
            "momentum_captured": None,
        })

    # Veto log (signal was active, now blocked)
    if sig in skip and prev.get("signal", "") not in (list(skip) + [""]):
        st.session_state.veto_log.append({
            "time":        now.strftime("%H:%M:%S"),
            "log_dt":      now,
            "symbol":      name,
            "blocked_sig": prev.get("signal", ""),
            "price":       r['price'],
            "evaluated":   False,
            "veto_success": None,
        })

    # Evaluate past signals after 15 min
    for log in st.session_state.signals_log:
        if log["evaluated"] or log["symbol"] != name:
            continue
        if (now - log["log_dt"]).total_seconds() < 900:
            continue
        move   = r['price'] - log["entry_price"]
        is_buy = "BUY" in log["signal"]
        passed = (move > 0) if is_buy else (move < 0)
        log.update({
            "evaluated":          True,
            "result":             "✅ PASS" if passed else "❌ FAIL",
            "exit_price":         r['price'],
            "momentum_captured":  "✅ YES" if abs(move) > 15 else (
                                  "⚠️ PARTIAL" if abs(move) > 5 else "❌ MISSED"),
        })

    for veto in st.session_state.veto_log:
        if veto["evaluated"] or veto["symbol"] != name:
            continue
        if (now - veto["log_dt"]).total_seconds() < 900:
            continue
        move       = r['price'] - veto["price"]
        bull_block = "BUY" in veto["blocked_sig"]
        bad_move   = (move > 10) if bull_block else (move < -10)
        veto["evaluated"]    = True
        veto["veto_success"] = "❌ MISSED MOVE" if bad_move else "✅ SAVED"

    st.session_state.prev_sig[symbol_key] = {"signal": sig, "price": r['price']}


# ══ SIGNAL CARD RENDERER ═════════════════════════════════════════

def render_card(symbol: str, name: str, gift_df, vix, col):
    with col:
        r = compute_signal(symbol, gift_df, vix)
        log_signal(symbol, name, r)

        if r is None:
            st.markdown(
                f'<div class="sc sc-wait"><div class="sc-name">{name}</div>'
                f'<div class="sc-sig" style="color:#1e3a5f;">⚠️ NO DATA</div></div>',
                unsafe_allow_html=True)
            return

        sig   = r['signal']
        price = r['price']
        zone  = r['zone']

        # Color
        if "SUPER BUY" in sig or (zone == "sc-buy"):
            color = "#00d463"
        elif "SUPER SELL" in sig or (zone == "sc-sell"):
            color = "#ff1a1a"
        elif zone == "sc-caut" or "SIDEWAYS" in sig:
            color = "#ff9800"
        else:
            color = "#3d5a7a"

        # 4 dots with labels
        dc = color  # active color
        ic = "#1e3a5f"  # inactive
        dot_html = (
            f'<span style="color:{dc if r["dot1"] else ic};" title="EMA Cross">{"●" if r["dot1"] else "○"}</span>'
            f'&nbsp;<span style="color:{dc if r["dot2"] else ic};" title="VWAP">{"●" if r["dot2"] else "○"}</span>'
            f'&nbsp;<span style="color:{dc if r["dot3"] else ic};" title="RSI">{"●" if r["dot3"] else "○"}</span>'
            f'&nbsp;<span style="color:{dc if r["dot4"] else ic};" title="Volume">{"●" if r["dot4"] else "○"}</span>'
        )
        dot_lbl = '<span style="font-size:7px;color:#1e3a5f;letter-spacing:1px;">EMA&nbsp;&nbsp;VWAP&nbsp;&nbsp;RSI&nbsp;&nbsp;VOL</span>'

        # Badge
        if r['vix_warn']:
            badge = f'<span class="sc-bge" style="background:#400;color:#ff9800;border:1px solid #ff9800;">⚡ VIX ALERT</span>'
        elif "SIDEWAYS" in sig:
            badge = f'<span class="sc-bge" style="background:#2a1500;color:#ff9800;border:1px solid #ff9800;">↔️ SIDEWAYS — WAIT</span>'
        elif "GIFT BEARISH" in sig or "GIFT BULLISH" in sig:
            badge = f'<span class="sc-bge" style="background:#2a1500;color:#ff9800;border:1px solid #ff9800;">⚠️ GIFT CONFLICT</span>'
        elif "LOW VOL" in sig:
            badge = f'<span class="sc-bge" style="background:#1a1000;color:#ff9800;border:1px solid #ff9800;">📊 LOW VOLUME</span>'
        elif zone in ("sc-buy", "sc-sell"):
            badge = f'<span class="sc-bge" style="color:{color};border:1px solid {color};">GIFT × LOCAL ✓  VOL ✓</span>'
        else:
            badge = ""

        # Entry + SL
        if "BUY" in sig and zone in ("sc-buy", "sc-caut"):
            sl_val  = r['sl_buy']
            risk_pt = price - sl_val
            entry_block = (
                f'<div class="sc-entry">'
                f'<div style="font-size:9px;letter-spacing:2px;color:#3d9be9;">ENTRY / SL</div>'
                f'<div style="color:{color};font-size:10px;">{r["entry_quality"]}</div>'
                f'<div style="color:#ff6666;font-size:9px;margin-top:2px;">'
                f'SL ₹{sl_val:,.0f} &nbsp; RISK {risk_pt:,.0f} pts</div>'
                f'</div>'
            )
        elif "SELL" in sig and zone in ("sc-sell", "sc-caut"):
            sl_val  = r['sl_sell']
            risk_pt = sl_val - price
            entry_block = (
                f'<div class="sc-entry">'
                f'<div style="font-size:9px;letter-spacing:2px;color:#3d9be9;">ENTRY / SL</div>'
                f'<div style="color:{color};font-size:10px;">{r["entry_quality"]}</div>'
                f'<div style="color:#ff6666;font-size:9px;margin-top:2px;">'
                f'SL ₹{sl_val:,.0f} &nbsp; RISK {risk_pt:,.0f} pts</div>'
                f'</div>'
            )
        else:
            entry_block = ""

        # Queue sound on signal change
        prev_sig = st.session_state.prev_sig.get(f"_r_{symbol}", "")
        if sig != prev_sig and zone in ("sc-buy", "sc-sell"):
            queue_sound("buy" if zone == "sc-buy" else "sell")
        st.session_state.prev_sig[f"_r_{symbol}"] = sig

        st.markdown(f"""
        <div class="sc {zone}">
            {badge}
            <div class="sc-name">{name}</div>
            <div class="sc-price" style="color:{color};">₹{price:,.1f}</div>
            <div class="sc-sig" style="color:{color};">{sig}</div>
            <div class="sc-dots">{dot_html}</div>
            {dot_lbl}
            <div class="sc-bar">
                <span>RSI {r['rsi']:.0f}</span>
                <span>VWAP {r['vwap']:,.0f}</span>
                <span>VOL {r['vol_ratio']:.1f}x</span>
                <span>MOM {r['mom_pct']:+.2f}%</span>
                <span>GIFT {r['gift_trend']}</span>
            </div>
            {entry_block}
            <div class="sc-time">🕐 {r['time']}</div>
        </div>""", unsafe_allow_html=True)


# ══ MINI CARD ════════════════════════════════════════════════════

def mini_card(symbol: str, name: str, icon: str, col):
    with col:
        q = get_quote(symbol)
        if q:
            chg   = q['chg']
            arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "—")
            cls   = "pos" if chg > 0 else ("neg" if chg < 0 else "neu")
            st.markdown(f"""
            <div class="mc">
                <div class="mc-ico">{icon}</div>
                <div class="mc-nm">{name}</div>
                <div class="mc-pr">{q['price']:,.1f}</div>
                <div class="mc-ch {cls}">{arrow} {chg:+.2f}%</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="mc">
                <div class="mc-ico">{icon}</div>
                <div class="mc-nm">{name}</div>
                <div style="color:#1e3a5f;font-size:11px;">—</div>
            </div>""", unsafe_allow_html=True)


# ══ EOD REPORT ═══════════════════════════════════════════════════

def eod_report():
    logs   = st.session_state.signals_log
    vetos  = st.session_state.veto_log
    evaled = [l for l in logs if l["evaluated"]]
    passed = [l for l in evaled if "PASS" in (l.get("result") or "")]
    failed = [l for l in evaled if "FAIL" in (l.get("result") or "")]
    pending = len(logs) - len(evaled)
    strike  = len(passed) / len(evaled) * 100 if evaled else 0
    mom_ok  = [l for l in evaled if "YES" in (l.get("momentum_captured") or "")]
    mom_rt  = len(mom_ok) / len(evaled) * 100 if evaled else 0
    ev_vt   = [v for v in vetos if v["evaluated"]]
    saved   = [v for v in ev_vt if "SAVED" in (v.get("veto_success") or "")]
    vrate   = len(saved) / len(ev_vt) * 100 if ev_vt else 0
    buys    = len([l for l in logs if "BUY"  in l["signal"]])
    sells   = len([l for l in logs if "SELL" in l["signal"]])
    vol_pass = len([l for l in passed if l.get("vol_ratio", 0) >= 1.5])
    avg_dots = np.mean([l["dots"] for l in logs]) if logs else 0

    cols = st.columns(9)
    metrics = [
        ("SIGNALS",  str(len(logs)),        "#3d9be9"),
        ("PASS",     str(len(passed)),       "#00d463"),
        ("FAIL",     str(len(failed)),       "#ff1a1a"),
        ("PENDING",  str(pending),           "#ff9800"),
        ("STRIKE %", f"{strike:.0f}%",      "#00d463" if strike >= 60 else "#ff9800"),
        ("MOM %",    f"{mom_rt:.0f}%",      "#00d463" if mom_rt >= 60 else "#ff9800"),
        ("VETO %",   f"{vrate:.0f}%",       "#00d463" if vrate >= 60 else "#ff9800"),
        ("BUY/SELL", f"{buys}/{sells}",      "#3d9be9"),
        ("AVG DOTS", f"{avg_dots:.1f}/4",   "#00d463" if avg_dots >= 3 else "#ff9800"),
    ]
    for col, (lbl, val, clr) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="rm">
                <div class="rv" style="color:{clr};">{val}</div>
                <div class="rl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    if logs:
        st.markdown("##### 📋 Signal Log (Auto-evaluated after 15 min)")
        df_rows = []
        for l in logs:
            df_rows.append({
                "Time":    l["entry_time"],
                "Index":   l["symbol"],
                "Signal":  l["signal"],
                "Entry ₹": f"₹{l['entry_price']:,.1f}",
                "Exit ₹":  f"₹{l['exit_price']:,.1f}" if l["exit_price"] else "⏳",
                "Result":  l.get("result") or "⏳ Pending",
                "Mom":     l.get("momentum_captured") or "⏳",
                "RSI":     f"{l['rsi']:.0f}",
                "Vol":     f"{l.get('vol_ratio',0):.1f}x",
                "Dots":    f"{l['dots']}/4",
                "MOM%":    f"{l['mom_pct']:+.2f}%",
                "GIFT":    l["gift_trend"],
            })
        st.dataframe(pd.DataFrame(df_rows), use_container_width=True, hide_index=True, height=200)

    if ev_vt:
        st.markdown("##### 🛡️ Veto / NO-SYNC Log")
        vrows = [{
            "Time":    v["time"], "Index": v["symbol"],
            "Blocked Signal": v["blocked_sig"],
            "Price at Veto":  f"₹{v['price']:,.1f}",
            "Outcome":        v.get("veto_success") or "⏳",
        } for v in ev_vt]
        st.dataframe(pd.DataFrame(vrows), use_container_width=True, hide_index=True)

    if not logs and not vetos:
        st.info("📊 Signals appear here as they generate during the session. Evaluation is automatic after 15 minutes.")


# ══════════════════════════════════════════════════════════════════
#  🖥️  MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════

# ── Fetch shared data ONCE ────────────────────────────────────────
gift_df  = get_gift_data()
vix      = get_vix()
news     = get_news()
now_ist  = datetime.now(IST)

# VIX display
if vix:
    vix_clr  = "#ff1a1a" if vix["high"] or vix["spike"] else "#00d463"
    vix_txt  = f"VIX {vix['val']:.1f} ({vix['chg']:+.1f}%)"
    if vix["spike"]: vix_txt += " ⚡"
    if vix["high"]:  vix_txt += " 🔴"
    if vix["spike"]: queue_sound("vix")
else:
    vix_clr, vix_txt = "#3d5a7a", "VIX —"

# ── HEADER ───────────────────────────────────────────────────────
hc1, hc2, hc3, hc4 = st.columns([3, 3, 2, 1])
with hc1:
    st.markdown(
        f'<div style="font-size:18px;font-weight:900;letter-spacing:4px;color:#3d9be9;padding-top:5px;">'
        f'🦅 EAGLE EYE PRO</div>',
        unsafe_allow_html=True)
with hc2:
    st.markdown(
        f'<div style="font-size:10px;color:#3d5a7a;font-family:monospace;padding-top:8px;">'
        f'{now_ist.strftime("%I:%M:%S %p  |  %d %b %Y")} IST</div>',
        unsafe_allow_html=True)
with hc3:
    st.markdown(
        f'<div style="font-size:11px;letter-spacing:2px;color:{vix_clr};padding-top:8px;font-weight:700;">'
        f'{vix_txt}</div>',
        unsafe_allow_html=True)
with hc4:
    sound_enable_btn()

st.markdown('<div style="height:2px;border-bottom:1px solid #0d3060;margin-bottom:6px;"></div>',
            unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["⚡ SIGNALS", "🌍 MARKETS", "📰 NEWS", "📊 REPORT"])

# ─── TAB 1: SIGNALS ──────────────────────────────────────────────
with tab1:
    c1, c2, c3 = st.columns(3)

    # NIFTY 50
    render_card("^NSEI",    "NIFTY 50",   gift_df, vix, c1)
    # BANK NIFTY
    render_card("^NSEBANK", "BANK NIFTY", gift_df, vix, c2)

    # GIFT NIFTY — standalone indicator card
    with c3:
        if gift_df is not None and len(gift_df) >= 2:
            gp    = float(gift_df['Close'].iloc[-1])
            gpp   = float(gift_df['Close'].iloc[-2])
            gc    = (gp - gpp) / gpp * 100
            g_col = "#00d463" if gc > 0.05 else ("#ff1a1a" if gc < -0.05 else "#3d9be9")
            g_zon = "sc-buy" if gc > 0.05 else ("sc-sell" if gc < -0.05 else "sc-wait")
            g_lbl = "🐂 BULLISH" if gc > 0.05 else ("🐻 BEARISH" if gc < -0.05 else "⚖️ NEUTRAL")
            arrow = "▲" if gc > 0.05 else ("▼" if gc < -0.05 else "—")
            # Last 5 candles mini trend
            last5  = [float(gift_df['Close'].iloc[-i]) for i in range(1, min(6, len(gift_df)+1))]
            ticons = ["▲" if last5[i] > last5[i+1] else "▼" for i in range(min(4, len(last5)-1))]
            tstr   = " ".join(ticons) if ticons else "—"

            st.markdown(f"""
            <div class="sc {g_zon}">
                <span class="sc-bge" style="color:{g_col};border:1px solid {g_col};">SGX / GIFT NIFTY FUTURES</span>
                <div class="sc-name">15-MINUTE GLOBAL TREND</div>
                <div class="sc-price" style="color:{g_col};">₹{gp:,.1f}</div>
                <div class="sc-sig" style="color:{g_col};">{arrow} {gc:+.3f}% &nbsp; {g_lbl}</div>
                <div class="sc-bar">
                    <span>PREV: {gpp:,.1f}</span>
                    <span>INTERVAL: 15M</span>
                </div>
                <div style="font-size:11px;color:{g_col};margin-top:8px;letter-spacing:4px;">{tstr}</div>
                <div style="font-size:8px;color:#3d5a7a;margin-top:2px;">← RECENT 4 CANDLES</div>
                <div class="sc-time">🕐 {now_ist.strftime("%H:%M:%S")}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="sc sc-wait"><div class="sc-name">GIFT NIFTY</div>'
                '<div class="sc-sig" style="color:#1e3a5f;">⚠️ NO DATA</div></div>',
                unsafe_allow_html=True)

    # Quick global pulse strip
    st.markdown('<div class="slbl">⚡ QUICK GLOBAL PULSE</div>', unsafe_allow_html=True)
    qc = st.columns(6)
    for (sym, nm, ic), col in zip([
        ("ES=F", "S&P 500", "📈"), ("NQ=F", "NASDAQ", "💻"),
        ("GC=F", "GOLD",    "🥇"), ("CL=F", "CRUDE",  "🛢️"),
        ("SI=F", "SILVER",  "🥈"), ("^INDIAVIX", "INDIA VIX", "⚡"),
    ], qc):
        mini_card(sym, nm, ic, col)

# ─── TAB 2: MARKETS ──────────────────────────────────────────────
with tab2:
    st.markdown('<div class="slbl">🇺🇸 US FUTURES</div>', unsafe_allow_html=True)
    uc = st.columns(4)
    for (sym, nm, ic), col in zip([
        ("ES=F", "S&P 500 FUT", "📈"), ("NQ=F", "NASDAQ FUT", "💻"),
        ("YM=F", "DOW FUT",     "🏭"), ("RTY=F", "RUSSELL 2K", "📊"),
    ], uc):
        mini_card(sym, nm, ic, col)

    st.markdown('<div class="slbl">🌏 ASIA FUTURES</div>', unsafe_allow_html=True)
    ac = st.columns(4)
    for (sym, nm, ic), col in zip([
        ("NIY=F", "NIKKEI 225", "🇯🇵"), ("^HSI",      "HANG SENG", "🇭🇰"),
        ("^AXJO", "ASX 200",    "🇦🇺"), ("000300.SS", "CSI 300",   "🇨🇳"),
    ], ac):
        mini_card(sym, nm, ic, col)

    st.markdown('<div class="slbl">🌍 EUROPE FUTURES</div>', unsafe_allow_html=True)
    ec = st.columns(4)
    for (sym, nm, ic), col in zip([
        ("^GDAXI",   "DAX",        "🇩🇪"), ("^FTSE",    "FTSE 100",    "🇬🇧"),
        ("^FCHI",    "CAC 40",     "🇫🇷"), ("^STOXX50E","EURO STOXX 50","🇪🇺"),
    ], ec):
        mini_card(sym, nm, ic, col)

    st.markdown('<div class="slbl">💰 COMMODITIES</div>', unsafe_allow_html=True)
    cc = st.columns(4)
    for (sym, nm, ic), col in zip([
        ("GC=F", "GOLD",        "🥇"), ("SI=F", "SILVER",      "🥈"),
        ("CL=F", "CRUDE WTI",   "🛢️"), ("NG=F", "NATURAL GAS", "⚡"),
    ], cc):
        mini_card(sym, nm, ic, col)

# ─── TAB 3: NEWS ─────────────────────────────────────────────────
with tab3:
    nc, sc = st.columns([3, 1])

    with nc:
        new_bull = new_bear = 0
        if news:
            for n in news:
                is_new = n["id"] not in st.session_state.news_seen
                if is_new:
                    st.session_state.news_seen.add(n["id"])
                    if n["sentiment"] == "bull": new_bull += 1
                    if n["sentiment"] == "bear": new_bear += 1

                icon = "🟢" if n["sentiment"] == "bull" else ("🔴" if n["sentiment"] == "bear" else "🔵")
                css  = f"ni-{n['sentiment']}"
                link = n.get("link", "#")

                # Clickable news item (opens in new tab)
                st.markdown(
                    f'<a href="{link}" target="_blank" class="ni {css}">'
                    f'<div class="ni-m">{n["time"]} &nbsp;|&nbsp; {n["source"]}</div>'
                    f'{icon} {n["title"]}'
                    f'</a>',
                    unsafe_allow_html=True)

            if new_bull > 0 or new_bear > 0:
                queue_sound("news")
        else:
            st.info("Fetching market news…")

    with sc:
        total_n  = len(news) or 1
        bull_n   = sum(1 for n in news if n["sentiment"] == "bull")
        bear_n   = sum(1 for n in news if n["sentiment"] == "bear")
        neu_n    = total_n - bull_n - bear_n
        bull_pct = bull_n / total_n * 100
        s_clr    = "#00d463" if bull_pct > 55 else ("#ff1a1a" if bull_pct < 45 else "#ff9800")
        overall  = "BULLISH" if bull_pct > 55 else ("BEARISH" if bull_pct < 45 else "MIXED")

        st.markdown(f"""
        <div class="sentb">
            <div style="font-size:8px;letter-spacing:3px;color:#3d9be9;margin-bottom:8px;">NEWS SENTIMENT</div>
            <div style="font-size:22px;font-weight:900;color:{s_clr};margin-bottom:8px;">{overall}</div>
            <div style="display:flex;justify-content:space-between;font-size:12px;margin:5px 0;">
                <span style="color:#00d463;">🟢 BULL</span>
                <span style="color:#00d463;font-weight:700;">{bull_n}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:12px;margin:5px 0;">
                <span style="color:#ff1a1a;">🔴 BEAR</span>
                <span style="color:#ff1a1a;font-weight:700;">{bear_n}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:12px;margin:5px 0;">
                <span style="color:#3d9be9;">🔵 NEU</span>
                <span style="color:#3d9be9;font-weight:700;">{neu_n}</span>
            </div>
            <div class="pb">
                <div style="background:{s_clr};height:5px;width:{bull_pct:.0f}%;transition:width 0.5s;"></div>
            </div>
            <div style="font-size:8px;color:#3d5a7a;margin-top:5px;">{bull_pct:.0f}% BULLISH</div>
        </div>""", unsafe_allow_html=True)

# ─── TAB 4: REPORT ───────────────────────────────────────────────
with tab4:
    eod_report()

# ── EMIT QUEUED SOUNDS (once, end of render) ──────────────────────
emit_queued_sounds()

# ── FOOTER ───────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:6px;font-size:8px;letter-spacing:3px;
            color:#0d3060;border-top:1px solid #050f1e;margin-top:8px;">
🦅 EAGLE EYE PRO v2 &nbsp;|&nbsp; EDUCATIONAL USE ONLY — NOT FINANCIAL ADVICE
&nbsp;|&nbsp; 🔊 BUY=ASCENDING &nbsp; SELL=DESCENDING &nbsp; NEWS=DOUBLE TONE &nbsp; VIX=LOW DRONE
</div>""", unsafe_allow_html=True)
