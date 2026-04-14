# ══════════════════════════════════════════════════════════════════
#  🦅 EAGLE EYE PRO — Advanced Global Sync Trading Dashboard
#  Strategies: GIFT Nifty + VWAP + EMA + RSI + Global Futures
# ══════════════════════════════════════════════════════════════════
#  pip install streamlit yfinance pandas numpy pytz streamlit-autorefresh

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import json
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="🦅 Eagle Eye Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st_autorefresh(interval=30000, key="eagle_refresh")   # 30-sec refresh
IST = pytz.timezone('Asia/Kolkata')

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
_defaults = {
    "signals_log":      [],      # EOD signal history
    "prev_signals":     {},      # last known signal per symbol (beep guard)
    "news_seen":        set(),   # prevent duplicate news beeps
    "veto_log":         [],      # NO-SYNC veto tracking
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# CSS / GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700;900&display=swap');

*, body { font-family: 'Rajdhani', sans-serif !important; }
.stApp { background: #020b18; color: #dce8f7; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }
div[data-testid="stHorizontalBlock"] { gap: 10px; }

/* ── HEADER ── */
.eagle-hdr {
    text-align: center; padding: 16px 20px;
    background: linear-gradient(90deg, #010913 0%, #071e3d 50%, #010913 100%);
    border-bottom: 1px solid #0d3060; margin-bottom: 18px;
}
.eagle-title { font-size: 30px; font-weight: 900; letter-spacing: 8px; color: #3d9be9; }
.eagle-sub   { font-size: 11px; letter-spacing: 4px; color: #3d9be9; opacity: 0.65; margin-top: 4px; }

/* ── SECTION LABEL ── */
.sec-lbl {
    font-size: 10px; letter-spacing: 4px; font-weight: 700; color: #3d9be9;
    border-left: 3px solid #3d9be9; padding: 3px 0 3px 10px; margin: 20px 0 10px;
}

/* ── SIGNAL CARDS ── */
.sig-card {
    border-radius: 14px; padding: 20px 16px; text-align: center;
    border: 1px solid #0d3060; position: relative; overflow: hidden;
    transition: all 0.4s ease; margin-bottom: 10px; min-height: 220px;
}
.sig-buy  { background: linear-gradient(145deg, #002716 0%, #020b18 100%);
            border-color: #00d463; box-shadow: 0 0 30px rgba(0,212,99,0.22);
            animation: pulse-g 2.5s infinite; }
.sig-sell { background: linear-gradient(145deg, #200000 0%, #020b18 100%);
            border-color: #ff1a1a; box-shadow: 0 0 30px rgba(255,26,26,0.22);
            animation: pulse-r 2.5s infinite; }
.sig-wait { background: #050f1e; border-color: #0d3060; opacity: 0.75; }

@keyframes pulse-g { 0%,100%{box-shadow:0 0 25px rgba(0,212,99,0.18)} 50%{box-shadow:0 0 50px rgba(0,212,99,0.45)} }
@keyframes pulse-r { 0%,100%{box-shadow:0 0 25px rgba(255,26,26,0.18)} 50%{box-shadow:0 0 50px rgba(255,26,26,0.45)} }

.sig-badge  { font-size: 9px; letter-spacing: 3px; font-weight: 700; margin-bottom: 6px; }
.sig-name   { font-size: 13px; opacity: 0.55; }
.sig-price  { font-size: 40px; font-weight: 700; font-family: 'Share Tech Mono' !important; margin: 6px 0; }
.sig-status { font-size: 20px; font-weight: 900; letter-spacing: 3px; margin: 6px 0; }
.sig-bar    { font-size: 11px; color: #3d5a7a; display: flex; justify-content: space-around; margin-top: 10px; flex-wrap: wrap; gap: 4px; }
.sig-time   { font-size: 10px; color: #1e3a5f; margin-top: 8px; font-family: 'Share Tech Mono'; }

/* ── MINI CARDS (futures / commodities) ── */
.mini-card {
    background: #050f1e; border: 1px solid #0d3060;
    border-radius: 10px; padding: 14px; text-align: center; margin-bottom: 8px;
}
.mini-icon  { font-size: 20px; }
.mini-name  { font-size: 9px; letter-spacing: 2px; color: #3d5a7a; margin: 4px 0; }
.mini-price { font-size: 18px; font-weight: 700; font-family: 'Share Tech Mono'; }
.mini-chg   { font-size: 12px; font-weight: 700; margin-top: 2px; }
.chg-pos    { color: #00d463; }
.chg-neg    { color: #ff1a1a; }
.chg-neu    { color: #3d9be9; }

/* ── NEWS FEED ── */
.news-item {
    border-radius: 8px; padding: 10px 13px; margin: 5px 0;
    border-left: 3px solid; font-size: 13px; line-height: 1.5;
    cursor: pointer; transition: opacity 0.2s;
}
.n-bull { background: rgba(0,212,99,0.07);  border-color: #00d463; }
.n-bear { background: rgba(255,26,26,0.07); border-color: #ff1a1a; }
.n-neu  { background: rgba(61,155,233,0.07);border-color: #3d9be9; }
.news-meta { font-size: 10px; color: #3d5a7a; margin-bottom: 3px; }

/* ── REPORT CARD ── */
.rpt-metric {
    background: #050f1e; border: 1px solid #0d3060;
    border-radius: 10px; padding: 14px 10px; text-align: center;
}
.rpt-val { font-size: 28px; font-weight: 700; font-family: 'Share Tech Mono'; }
.rpt-lbl { font-size: 9px; letter-spacing: 2px; color: #3d9be9; margin-top: 4px; }

/* ── SENTIMENT GAUGE ── */
.sent-box {
    background: #050f1e; border: 1px solid #0d3060;
    border-radius: 12px; padding: 18px; text-align: center;
}
.sent-val { font-size: 28px; font-weight: 900; letter-spacing: 2px; margin-bottom: 14px; }
.prog-bar { background: #0d3060; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 10px; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #020b18; }
::-webkit-scrollbar-thumb { background: #0d3060; border-radius: 2px; }

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 🔊 SOUND ENGINE  (Web Audio API via JS)
# ─────────────────────────────────────────────
def inject_sound(beep_type: str):
    """
    beep_type: 'buy' | 'sell' | 'news'
    Uses Web Audio API — works on desktop Chrome/Edge/Firefox.
    Mobile: works after first user gesture (tap) unlocks AudioContext.
    """
    profiles = {
        "buy":  {"notes": [523, 659, 784, 1047], "wave": "sine",    "vol": 0.45, "dur": 0.12},
        "sell": {"notes": [494, 392, 330, 247],  "wave": "sawtooth","vol": 0.45, "dur": 0.12},
        "news": {"notes": [440, 550, 440],        "wave": "triangle","vol": 0.30, "dur": 0.18},
    }
    p = profiles.get(beep_type, profiles["news"])
    js_code = f"""
    <script>
    (function(){{
      try {{
        var Ctx = window.AudioContext || window.webkitAudioContext;
        if(!Ctx) return;
        var ctx = new Ctx();
        var notes = {json.dumps(p['notes'])};
        var gap   = {p['dur'] + 0.05};
        notes.forEach(function(freq, i) {{
          var t   = ctx.currentTime + i * gap;
          var osc = ctx.createOscillator();
          var gain= ctx.createGain();
          osc.type = '{p['wave']}';
          osc.frequency.setValueAtTime(freq, t);
          gain.gain.setValueAtTime({p['vol']}, t);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + {p['dur']});
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start(t);
          osc.stop(t + {p['dur']} + 0.02);
        }});
      }} catch(e) {{ console.warn('Eagle Eye sound error:', e); }}
    }})();
    </script>"""
    components.html(js_code, height=0, scrolling=False)


# ─────────────────────────────────────────────
# 📦 DATA FETCHING  (cached)
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_ohlcv(symbol: str, period: str = "1d", interval: str = "1m") -> pd.DataFrame | None:
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(subset=['Close', 'Volume'], inplace=True)
        return df if len(df) >= 5 else None
    except Exception:
        return None


@st.cache_data(ttl=60)
def fetch_gift_data() -> pd.DataFrame | None:
    """GIFT Nifty 15m — try IN=F first, fallback to ^NSEI 15m"""
    for sym in ["IN=F", "^NSEI"]:
        try:
            df = yf.download(sym, period="2d", interval="15m", progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.dropna(subset=['Close'], inplace=True)
            if len(df) >= 3:
                return df
        except Exception:
            continue
    return None


@st.cache_data(ttl=45)
def fetch_quote(symbol: str) -> dict | None:
    """Latest price + % change for a single symbol"""
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(subset=['Close'], inplace=True)
        if len(df) >= 2:
            p = float(df['Close'].iloc[-1])
            pc = float(df['Close'].iloc[-2])
            return {"price": p, "chg": (p - pc) / pc * 100, "prev": pc}
    except Exception:
        pass
    return None


@st.cache_data(ttl=120)
def fetch_news() -> list[dict]:
    """
    Pull news via yfinance; classify sentiment by keyword scoring.
    Returns list of dicts: {title, sentiment, time, source, id}
    """
    BULL = {'rally','surge','gain','rise','rises','record','growth','positive','bullish',
            'strong','jump','soar','beats','exceeds','upgrade','buy','rebound','recovery',
            'boost','profit','boom','optimistic','high','support','up'}
    BEAR = {'fall','falls','decline','drop','crash','loss','weak','bearish','sell',
            'downgrade','recession','fear','risk','concern','miss','disappoint','slump',
            'tumble','plunge','low','warning','cut','below','slowdown','tension'}

    tickers = ["^NSEI", "^NSEBANK", "GC=F", "CL=F", "ES=F", "^DJI"]
    seen, results = set(), []

    for sym in tickers:
        try:
            items = yf.Ticker(sym).news or []
            for item in items[:6]:
                title = item.get('title', '').strip()
                uid   = item.get('uuid', title[:40])
                if not title or uid in seen:
                    continue
                seen.add(uid)
                t_lo = title.lower()
                b_score = sum(1 for w in BULL if w in t_lo)
                r_score = sum(1 for w in BEAR if w in t_lo)
                if b_score > r_score:
                    sent = "bull"
                elif r_score > b_score:
                    sent = "bear"
                else:
                    sent = "neu"
                ts = item.get('providerPublishTime', 0)
                t_str = datetime.fromtimestamp(ts, tz=IST).strftime("%H:%M") if ts else "—"
                results.append({
                    "title": title,
                    "sentiment": sent,
                    "time": t_str,
                    "source": item.get('publisher', ''),
                    "id": uid,
                    "link": item.get('link', '#'),
                })
        except Exception:
            continue

    return results


# ─────────────────────────────────────────────
# 📊 SIGNAL ENGINE  (EMA + VWAP + RSI + GIFT)
# ─────────────────────────────────────────────
def compute_signal(symbol: str, gift_df: pd.DataFrame | None) -> dict | None:
    local = fetch_ohlcv(symbol, period="1d", interval="1m")
    if local is None or len(local) < 21 or gift_df is None or len(gift_df) < 3:
        return None

    price = float(local['Close'].iloc[-1])
    vol   = local['Volume'].replace(0, np.nan)

    # ── VWAP (intraday cumulative) ──
    vwap = float((local['Close'] * vol).cumsum().iloc[-1] / vol.cumsum().iloc[-1])

    # ── EMA 9 / EMA 21 ──
    ema9  = float(local['Close'].ewm(span=9,  adjust=False).mean().iloc[-1])
    ema21 = float(local['Close'].ewm(span=21, adjust=False).mean().iloc[-1])

    # ── RSI 14 ──
    delta = local['Close'].diff()
    avg_g = delta.clip(lower=0).rolling(14).mean()
    avg_l = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = avg_g / avg_l.replace(0, np.nan)
    rsi   = float((100 - 100 / (1 + rs)).iloc[-1])

    # ── Momentum (5-bar price delta) ──
    momentum = float(local['Close'].iloc[-1] - local['Close'].iloc[-5]) if len(local) >= 5 else 0.0
    mom_pct  = momentum / float(local['Close'].iloc[-5]) * 100 if len(local) >= 5 else 0.0

    # ── GIFT Nifty (15m trend) ──
    g_now  = float(gift_df['Close'].iloc[-1])
    g_prev = float(gift_df['Close'].iloc[-2])
    g_chg  = (g_now - g_prev) / g_prev * 100
    if g_chg > 0.05:
        gift_trend = "BULL"
    elif g_chg < -0.05:
        gift_trend = "BEAR"
    else:
        gift_trend = "NEUTRAL"

    # ── Local Confirmation (2 of 3 required) ──
    bull_pts = int(price > vwap) + int(ema9 > ema21) + int(rsi > 55)
    bear_pts = int(price < vwap) + int(ema9 < ema21) + int(rsi < 45)

    if bull_pts >= 2:
        local_trend = "BULL"
    elif bear_pts >= 2:
        local_trend = "BEAR"
    else:
        local_trend = "NEUTRAL"

    # ── FINAL SIGNAL ──
    strength = 0
    if gift_trend == "BULL" and local_trend == "BULL":
        signal = "SUPER BUY"
        strength = bull_pts
    elif gift_trend == "BEAR" and local_trend == "BEAR":
        signal = "SUPER SELL"
        strength = bear_pts
    else:
        signal = "NO SYNC"

    return {
        "signal": signal, "strength": strength,
        "price": price, "vwap": vwap,
        "ema9": ema9, "ema21": ema21, "rsi": rsi,
        "gift_trend": gift_trend, "gift_price": g_now, "gift_chg": g_chg,
        "local_trend": local_trend,
        "momentum": momentum, "mom_pct": mom_pct,
        "bull_pts": bull_pts, "bear_pts": bear_pts,
        "time": datetime.now(IST).strftime("%H:%M:%S"),
        "timestamp": datetime.now(IST),
    }


# ─────────────────────────────────────────────
# 📝 LOG & EVALUATE SIGNALS
# ─────────────────────────────────────────────
def log_signal(symbol_key: str, name: str, result: dict):
    """
    • Logs new signals when they change.
    • Evaluates past signals after 15 min.
    • Tracks veto events (NO SYNC blocking a potential trade).
    """
    if result is None:
        return

    now    = datetime.now(IST)
    sig    = result['signal']
    price  = result['price']
    prev_s = st.session_state.prev_signals.get(symbol_key, {})

    # ── Log if signal changed (not from NO SYNC → NO SYNC) ──
    if sig != prev_s.get("signal") and sig != "NO SYNC":
        st.session_state.signals_log.append({
            "entry_time":  now.strftime("%H:%M:%S"),
            "log_dt":      now,
            "symbol":      name,
            "signal":      sig,
            "entry_price": price,
            "vwap":        result['vwap'],
            "rsi":         result['rsi'],
            "ema9":        result['ema9'],
            "ema21":       result['ema21'],
            "gift_trend":  result['gift_trend'],
            "mom_pct":     result['mom_pct'],
            "strength":    result['strength'],
            "evaluated":   False,
            "result":      None,
            "exit_price":  None,
            "momentum_captured": None,
            "veto_result": None,
        })

    # ── Track NO-SYNC veto events ──
    if sig == "NO SYNC" and prev_s.get("signal") not in ("NO SYNC", None, ""):
        # One side was signalling previously; now blocked
        st.session_state.veto_log.append({
            "time":        now.strftime("%H:%M:%S"),
            "log_dt":      now,
            "symbol":      name,
            "blocked_sig": prev_s.get("signal", ""),
            "price_at_veto": price,
            "evaluated":   False,
            "veto_success": None,
        })

    # ── Evaluate past signals (15-min window) ──
    for log in st.session_state.signals_log:
        if log["evaluated"] or log["symbol"] != name:
            continue
        age_min = (now - log["log_dt"]).total_seconds() / 60
        if age_min < 15:
            continue
        move = price - log["entry_price"]
        is_buy = "BUY" in log["signal"]
        passed = (move > 0) if is_buy else (move < 0)
        mom_ok = abs(move) > 15   # ≥15 point move = momentum captured
        log.update({
            "evaluated": True,
            "result":    "✅ PASS" if passed else "❌ FAIL",
            "exit_price": price,
            "momentum_captured": "✅ YES" if mom_ok else ("⚠️ PARTIAL" if abs(move) > 5 else "❌ MISSED"),
        })

    # ── Evaluate veto outcomes (15-min) ──
    for veto in st.session_state.veto_log:
        if veto["evaluated"] or veto["symbol"] != name:
            continue
        age_min = (now - veto["log_dt"]).total_seconds() / 60
        if age_min < 15:
            continue
        move = price - veto["price_at_veto"]
        # If blocked signal was BUY, veto success = price didn't go up significantly
        blocked_bull = "BUY" in veto["blocked_sig"]
        move_bad = (move > 10) if blocked_bull else (move < -10)
        veto["evaluated"]   = True
        veto["veto_success"] = "❌ MISSED MOVE" if move_bad else "✅ SAVED"

    st.session_state.prev_signals[symbol_key] = {"signal": sig, "price": price}


# ─────────────────────────────────────────────
# 🃏 RENDER SIGNAL CARD
# ─────────────────────────────────────────────
def render_signal_card(symbol: str, name: str, gift_df, col):
    with col:
        result = compute_signal(symbol, gift_df)
        log_signal(symbol, name, result)

        if result is None:
            st.markdown(f"""
            <div class="sig-card sig-wait">
                <div class="sig-name">{name}</div>
                <div class="sig-status" style="color:#1e3a5f;">⚠️ DATA UNAVAILABLE</div>
            </div>""", unsafe_allow_html=True)
            return

        sig   = result['signal']
        price = result['price']

        if "BUY" in sig:
            zone = "sig-buy"; color = "#00d463"; icon = "🚀"
            msg  = "GLOBAL × LOCAL ✓ ALIGNED"
        elif "SELL" in sig:
            zone = "sig-sell"; color = "#ff1a1a"; icon = "📉"
            msg  = "GLOBAL × LOCAL ✓ ALIGNED"
        else:
            zone = "sig-wait"; color = "#3d5a7a"; icon = "⏳"
            msg  = "WAITING FOR GLOBAL ALIGNMENT"

        # ── Fire beep on new signal ──
        prev_rendered = st.session_state.prev_signals.get(f"_render_{symbol}", "")
        if sig != prev_rendered and sig != "NO SYNC":
            inject_sound("buy" if "BUY" in sig else "sell")
        st.session_state.prev_signals[f"_render_{symbol}"] = sig

        # Strength dots
        dots = "●" * result['strength'] + "○" * (3 - result['strength'])

        st.markdown(f"""
        <div class="sig-card {zone}">
            <div class="sig-badge" style="color:{color};">{msg}</div>
            <div class="sig-name">{name} FUTURE</div>
            <div class="sig-price" style="color:{color};">₹{price:,.1f}</div>
            <div class="sig-status" style="color:{color};">{icon} {sig}</div>
            <div style="font-size:14px;color:{color};letter-spacing:3px;">{dots}</div>
            <div class="sig-bar">
                <span>RSI&nbsp;{result['rsi']:.0f}</span>
                <span>VWAP&nbsp;{result['vwap']:,.0f}</span>
                <span>EMA9&nbsp;{result['ema9']:,.0f}</span>
                <span>MOM&nbsp;{result['mom_pct']:+.2f}%</span>
                <span>GIFT&nbsp;{result['gift_trend']}</span>
            </div>
            <div class="sig-time">🕐 {result['time']}</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 📈 MINI QUOTE CARD (Futures / Commodities)
# ─────────────────────────────────────────────
def mini_card(symbol: str, name: str, icon: str, col):
    with col:
        q = fetch_quote(symbol)
        if q:
            chg   = q['chg']
            arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "—")
            cls   = "chg-pos" if chg > 0 else ("chg-neg" if chg < 0 else "chg-neu")
            st.markdown(f"""
            <div class="mini-card">
                <div class="mini-icon">{icon}</div>
                <div class="mini-name">{name}</div>
                <div class="mini-price">{q['price']:,.1f}</div>
                <div class="mini-chg {cls}">{arrow} {chg:+.2f}%</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="mini-card">
                <div class="mini-icon">{icon}</div>
                <div class="mini-name">{name}</div>
                <div style="color:#1e3a5f;font-size:12px;">NO DATA</div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 📊 EOD REPORT CARD
# ─────────────────────────────────────────────
def render_eod_report():
    logs  = st.session_state.signals_log
    vetos = st.session_state.veto_log
    now   = datetime.now(IST)

    total      = len(logs)
    evaluated  = [l for l in logs if l['evaluated']]
    passed     = [l for l in evaluated if "PASS"  in (l.get('result') or "")]
    failed     = [l for l in evaluated if "FAIL"  in (l.get('result') or "")]
    pending    = total - len(evaluated)
    buy_sigs   = [l for l in logs if "BUY"  in l['signal']]
    sell_sigs  = [l for l in logs if "SELL" in l['signal']]

    strike     = len(passed) / len(evaluated) * 100 if evaluated else 0
    mom_ok     = [l for l in evaluated if "YES" in (l.get('momentum_captured') or "")]
    mom_rate   = len(mom_ok) / len(evaluated) * 100 if evaluated else 0

    ev_vetos   = [v for v in vetos if v['evaluated']]
    saved_v    = [v for v in ev_vetos if "SAVED" in (v.get('veto_success') or "")]
    veto_rate  = len(saved_v) / len(ev_vetos) * 100 if ev_vetos else 0

    st.markdown('<div class="sec-lbl">📊 EOD REPORT CARD</div>', unsafe_allow_html=True)

    cols = st.columns(8)
    metrics = [
        ("TOTAL",       str(total),          "#3d9be9"),
        ("PASS",        str(len(passed)),     "#00d463"),
        ("FAIL",        str(len(failed)),     "#ff1a1a"),
        ("PENDING",     str(pending),         "#ff9800"),
        ("STRIKE %",    f"{strike:.0f}%",     "#00d463" if strike >= 60 else "#ff9800"),
        ("MOMENTUM %",  f"{mom_rate:.0f}%",   "#00d463" if mom_rate >= 60 else "#ff9800"),
        ("VETO SAVE %", f"{veto_rate:.0f}%",  "#00d463" if veto_rate >= 60 else "#ff9800"),
        ("BUY/SELL",    f"{len(buy_sigs)}/{len(sell_sigs)}", "#3d9be9"),
    ]
    for col, (lbl, val, clr) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="rpt-metric">
                <div class="rpt-val" style="color:{clr};">{val}</div>
                <div class="rpt-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    if logs:
        st.markdown("#### Signal Log")
        rows = []
        for l in logs:
            rows.append({
                "Time":      l['entry_time'],
                "Index":     l['symbol'],
                "Signal":    l['signal'],
                "Entry ₹":   f"{l['entry_price']:,.1f}",
                "Exit ₹":    f"{l['exit_price']:,.1f}" if l['exit_price'] else "⏳",
                "Result":    l.get('result') or "⏳ Pending",
                "Momentum":  l.get('momentum_captured') or "⏳",
                "RSI":       f"{l['rsi']:.0f}",
                "MOM%":      f"{l['mom_pct']:+.2f}%",
                "Strength":  "●" * l['strength'] + "○" * (3 - l['strength']),
                "GIFT":      l['gift_trend'],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if ev_vetos:
        st.markdown("#### Veto Log")
        vrows = [{
            "Time":      v['time'],
            "Index":     v['symbol'],
            "Blocked":   v['blocked_sig'],
            "Price":     f"₹{v['price_at_veto']:,.1f}",
            "Outcome":   v.get('veto_success') or "⏳",
        } for v in ev_vetos]
        st.dataframe(pd.DataFrame(vrows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
#  🖥️  MAIN LAYOUT
# ══════════════════════════════════════════════
live_time = datetime.now(IST).strftime("%I:%M:%S %p  |  %d %b %Y")
st.markdown(f"""
<div class="eagle-hdr">
    <div class="eagle-title">🦅 EAGLE EYE PRO</div>
    <div class="eagle-sub">GIFT NIFTY + EMA + VWAP + RSI + GLOBAL SYNC  |  {live_time} IST</div>
</div>""", unsafe_allow_html=True)

# ─── FETCH GIFT DATA ONCE ───────────────────
gift_df = fetch_gift_data()

# ══ SECTION 1: PRIMARY SIGNAL CARDS ══
st.markdown('<div class="sec-lbl">⚡ PRIMARY SIGNALS</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

render_signal_card("^NSEI",    "NIFTY 50",    gift_df, c1)
render_signal_card("^NSEBANK", "BANK NIFTY",  gift_df, c2)

# GIFT Nifty standalone card
with c3:
    if gift_df is not None and len(gift_df) >= 2:
        gp  = float(gift_df['Close'].iloc[-1])
        gpp = float(gift_df['Close'].iloc[-2])
        gc  = (gp - gpp) / gpp * 100
        g_color = "#00d463" if gc > 0.05 else ("#ff1a1a" if gc < -0.05 else "#3d9be9")
        g_label = ("🐂 BULLISH" if gc > 0.05 else ("🐻 BEARISH" if gc < -0.05 else "⚖️ NEUTRAL"))
        g_zone  = ("sig-buy"  if gc > 0.05 else ("sig-sell" if gc < -0.05 else "sig-wait"))
        arrow   = "▲" if gc > 0 else "▼"
        st.markdown(f"""
        <div class="sig-card {g_zone}">
            <div class="sig-badge" style="color:{g_color};">GIFT NIFTY — 15M GLOBAL TREND</div>
            <div class="sig-name">SGX / GIFT NIFTY</div>
            <div class="sig-price" style="color:{g_color};">₹{gp:,.1f}</div>
            <div class="sig-status" style="color:{g_color};">{arrow} {gc:+.3f}%  {g_label}</div>
            <div class="sig-bar">
                <span>PREV CANDLE: {gpp:,.1f}</span>
                <span>INTERVAL: 15M</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="sig-card sig-wait">
            <div class="sig-name">GIFT NIFTY</div>
            <div class="sig-status" style="color:#1e3a5f;">⚠️ DATA UNAVAILABLE</div>
        </div>""", unsafe_allow_html=True)

# ══ SECTION 2: US FUTURES ══
st.markdown('<div class="sec-lbl">🇺🇸 US FUTURES</div>', unsafe_allow_html=True)
uc = st.columns(4)
us_futures = [("ES=F","S&P 500 FUT","📈"), ("NQ=F","NASDAQ FUT","💻"),
              ("YM=F","DOW FUT","🏭"),     ("RTY=F","RUSSELL 2K","📊")]
for (sym, name, icon), col in zip(us_futures, uc):
    mini_card(sym, name, icon, col)

# ══ SECTION 3: ASIA FUTURES ══
st.markdown('<div class="sec-lbl">🌏 ASIA FUTURES</div>', unsafe_allow_html=True)
ac = st.columns(4)
asia_futures = [("NIY=F","NIKKEI 225","🇯🇵"), ("^HSI","HANG SENG","🇭🇰"),
                ("^AXJO","ASX 200","🇦🇺"),    ("000300.SS","CSI 300","🇨🇳")]
for (sym, name, icon), col in zip(asia_futures, ac):
    mini_card(sym, name, icon, col)

# ══ SECTION 4: EUROPE FUTURES ══
st.markdown('<div class="sec-lbl">🌍 EUROPE FUTURES</div>', unsafe_allow_html=True)
ec = st.columns(4)
eu_futures = [("^GDAXI","DAX","🇩🇪"), ("^FTSE","FTSE 100","🇬🇧"),
              ("^FCHI","CAC 40","🇫🇷"), ("^STOXX50E","EURO STOXX 50","🇪🇺")]
for (sym, name, icon), col in zip(eu_futures, ec):
    mini_card(sym, name, icon, col)

# ══ SECTION 5: COMMODITIES ══
st.markdown('<div class="sec-lbl">💰 COMMODITIES</div>', unsafe_allow_html=True)
cc = st.columns(4)
commodities = [("GC=F","GOLD","🥇"), ("SI=F","SILVER","🥈"),
               ("CL=F","CRUDE OIL WTI","🛢️"), ("NG=F","NATURAL GAS","⚡")]
for (sym, name, icon), col in zip(commodities, cc):
    mini_card(sym, name, icon, col)

# ══ SECTION 6: NEWS FEED ══
st.markdown('<div class="sec-lbl">📰 MARKET INTELLIGENCE</div>', unsafe_allow_html=True)
news_col, sent_col = st.columns([3, 1])

news_items = fetch_news()
new_bull, new_bear = 0, 0

with news_col:
    if news_items:
        for n in news_items:
            nid = n['id']
            is_new = nid not in st.session_state.news_seen
            if is_new:
                st.session_state.news_seen.add(nid)
                if n['sentiment'] == 'bull': new_bull += 1
                if n['sentiment'] == 'bear': new_bear += 1

            icon = "🟢" if n['sentiment'] == "bull" else ("🔴" if n['sentiment'] == "bear" else "🔵")
            css  = "n-bull" if n['sentiment'] == "bull" else ("n-bear" if n['sentiment'] == "bear" else "n-neu")
            st.markdown(f"""
            <div class="news-item {css}">
                <div class="news-meta">{n['time']}  |  {n['source']}</div>
                {icon} {n['title']}
            </div>""", unsafe_allow_html=True)

        # Beep on new news
        if new_bull > 0 or new_bear > 0:
            inject_sound("news")
    else:
        st.info("Fetching market news…")

with sent_col:
    total_n  = len(news_items) or 1
    bull_n   = sum(1 for n in news_items if n['sentiment'] == 'bull')
    bear_n   = sum(1 for n in news_items if n['sentiment'] == 'bear')
    bull_pct = bull_n / total_n * 100
    s_color  = "#00d463" if bull_pct > 55 else ("#ff1a1a" if bull_pct < 45 else "#ff8f00")
    overall  = "BULLISH" if bull_pct > 55 else ("BEARISH" if bull_pct < 45 else "MIXED")

    st.markdown(f"""
    <div class="sent-box">
        <div style="font-size:9px;letter-spacing:3px;color:#3d9be9;margin-bottom:10px;">NEWS SENTIMENT</div>
        <div class="sent-val" style="color:{s_color};">{overall}</div>
        <div style="display:flex;justify-content:space-between;font-size:13px;margin:8px 0;">
            <span style="color:#00d463;">🟢 BULL</span><span style="color:#00d463;font-weight:700;">{bull_n}</span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:13px;margin:8px 0;">
            <span style="color:#ff1a1a;">🔴 BEAR</span><span style="color:#ff1a1a;font-weight:700;">{bear_n}</span>
        </div>
        <div class="prog-bar">
            <div style="background:{s_color};height:6px;width:{bull_pct:.0f}%;transition:width 0.5s;"></div>
        </div>
        <div style="font-size:9px;color:#3d5a7a;margin-top:6px;">{bull_pct:.0f}% BULLISH</div>
    </div>""", unsafe_allow_html=True)

# ══ SECTION 7: EOD REPORT ══
st.divider()
render_eod_report()

# ── FOOTER ──────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:18px;font-size:9px;letter-spacing:3px;
            color:#0d3060;border-top:1px solid #050f1e;margin-top:16px;">
  🦅 EAGLE EYE PRO  |  EDUCATIONAL USE ONLY  |  NOT FINANCIAL ADVICE
  <br>🔊 BUY BEEP: ASCENDING TONE  |  SELL BEEP: DESCENDING TONE  |  NEWS BEEP: DOUBLE TONE
</div>""", unsafe_allow_html=True)
