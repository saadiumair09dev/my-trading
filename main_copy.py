# main.py
# Eagle Eye Pro v7 · Streamlit
# Full replacement implementing:
# - Streamlit password protection (st.secrets)
# - Dhan -> yfinance fallback for OHLC
# - short TTL caching for live data
# - safe_run wrapper to surface exceptions
# - sound enable toggle + in-memory beep
# - news clickable links and "Show details"
# - triangle annotations and last-candle highlight on Plotly charts
# - debug panel visible after auth
#
# NOTE: Replace placeholder functions (dhan_fetch_*) with your existing Dhan integration.
# Put your secrets (app_password_hash, dhan_api_key, etc.) into .streamlit/secrets.toml

import streamlit as st
import hashlib
import logging
import traceback
import pandas as pd
import numpy as np
import datetime as dt
import io
import wave
import plotly.graph_objects as go

# -------------------------
# Basic logging
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eagle_eye_pro")

# -------------------------
# Password protection
# -------------------------
def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def check_password():
    """
    Simple password gate. Put SHA256 hash in st.secrets['app_password_hash'].
    If no hash present, app will continue (useful for dev). For production, set a hash.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    stored_hash = st.secrets.get("app_password_hash", "")
    if not stored_hash:
        # No password configured; allow access but warn
        st.warning("No app password configured in secrets. Set app_password_hash in .streamlit/secrets.toml")
        st.session_state.authenticated = True
        return True
    if not st.session_state.authenticated:
        pw = st.text_input("App password", type="password")
        if pw:
            if _sha256(pw) == stored_hash:
                st.session_state.authenticated = True
                st.success("Authenticated")
            else:
                st.error("Incorrect password")
    return st.session_state.authenticated

if not check_password():
    st.stop()

# -------------------------
# Debug panel toggle (visible only after auth)
# -------------------------
if "show_debug" not in st.session_state:
    st.session_state.show_debug = False

st.sidebar.title("Eagle Eye Pro · Controls")
if st.sidebar.checkbox("Show debug panel", value=False):
    st.session_state.show_debug = True
else:
    st.session_state.show_debug = False

# -------------------------
# Sound enable toggle + beep generator
# -------------------------
if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = False

if st.sidebar.button("Enable sound"):
    st.session_state.sound_enabled = True
    st.success("Sound enabled for this session")

def generate_beep_wav_bytes(freq=440.0, duration_s=0.18, volume=0.3, fs=44100):
    """
    Generate a short beep WAV in memory and return bytes.
    Uses numpy and wave to avoid external dependencies beyond numpy.
    """
    t = np.linspace(0, duration_s, int(fs * duration_s), False)
    tone = np.sin(freq * 2 * np.pi * t) * volume
    # convert to 16-bit PCM
    audio = (tone * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()

def beep():
    if not st.session_state.sound_enabled:
        return
    wav_bytes = generate_beep_wav_bytes()
    st.audio(wav_bytes, format="audio/wav")

# -------------------------
# Safe-run wrapper to surface exceptions
# -------------------------
def safe_run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        st.error(f"Error in {fn.__name__}: {e}")
        st.text(traceback.format_exc())
        logger.exception("Exception in %s", fn.__name__)
        return None

# -------------------------
# Dhan integration placeholders
# -------------------------
# Replace these placeholders with your existing Dhan functions.
# The wrapper below will call dhan_fetch_ohlc and fallback to yfinance if needed.

def dhan_fetch_ohlc(symbol: str, start: dt.datetime, end: dt.datetime, interval: str = "5m"):
    """
    Placeholder for your Dhan OHLC fetch.
    Should return a pandas DataFrame with columns: ['Open','High','Low','Close','Volume'] and a datetime index.
    If Dhan fails or returns empty, raise an Exception or return None.
    """
    # Replace this with your Dhan API call and parsing logic.
    raise NotImplementedError("Replace dhan_fetch_ohlc with your Dhan implementation")

# -------------------------
# yfinance fallback
# -------------------------
def map_symbol_to_yf(symbol: str) -> str:
    """
    Map your internal symbol names to yfinance tickers.
    Update mappings as required for correct tickers.
    """
    mapping = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "GIFTNIFTY": "^NIFTY",   # adjust if you have a specific ticker
        "FINNIFTY": "^NSEI",    # adjust mapping to correct FINNIFTY ticker if available
    }
    return mapping.get(symbol.upper(), symbol)

@st.cache_data(ttl=30)
def yf_fetch_ohlc(symbol: str, start: dt.datetime, end: dt.datetime, interval: str = "5m"):
    import yfinance as yf
    yf_ticker = map_symbol_to_yf(symbol)
    df = yf.download(yf_ticker, start=start, end=end, interval=interval, progress=False)
    if df is None or df.empty:
        return None
    df = df.rename(columns=lambda c: c.capitalize())
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            return None
    return df[["Open", "High", "Low", "Close", "Volume"]]

def get_ohlc_with_fallback(symbol: str, start: dt.datetime, end: dt.datetime, interval: str = "5m"):
    """
    Try Dhan first, then fallback to yfinance. Returns pandas DataFrame or raises.
    """
    try:
        df = dhan_fetch_ohlc(symbol, start, end, interval)
        if df is None or len(df) == 0:
            raise ValueError("Dhan returned no data")
        return df
    except Exception as e:
        logger.warning("Dhan fetch failed for %s: %s. Falling back to yfinance", symbol, e)
        df = yf_fetch_ohlc(symbol, start, end, interval)
        if df is None or df.empty:
            raise RuntimeError(f"No data available for {symbol} from Dhan or yfinance")
        return df

# -------------------------
# Charting helpers (Plotly)
# -------------------------
def plot_candles_with_annotations(df: pd.DataFrame, triangles: list = None, title: str = "Chart"):
    """
    df: DataFrame with datetime index and Open/High/Low/Close columns
    triangles: list of dicts [{'x': datetime, 'y': float, 'type': 'ascending'/'descending'/'symmetrical'}]
    """
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name=title
    )])
    # Add triangle annotations
    if triangles:
        for tri in triangles:
            x = tri.get("x")
            y = tri.get("y")
            ttype = tri.get("type", "triangle")
            label = f"Triangle: {ttype}"
            fig.add_annotation(x=x, y=y, text=label, showarrow=True, arrowhead=2, ax=0, ay=-40)
    # Highlight last candle
    try:
        last_idx = df.index[-1]
        last_high = float(df["High"].iloc[-1])
        last_low = float(df["Low"].iloc[-1])
        x0 = last_idx - pd.Timedelta(minutes=1)
        x1 = last_idx + pd.Timedelta(minutes=1)
        fig.add_shape(type="rect",
                      x0=x0, x1=x1,
                      y0=last_low, y1=last_high,
                      line=dict(color="RoyalBlue"), fillcolor="LightSkyBlue", opacity=0.25)
    except Exception:
        pass
    fig.update_layout(title=title, xaxis_rangeslider_visible=False, height=600)
    return fig

# -------------------------
# News rendering helper
# -------------------------
def render_news_list(news_list: list):
    """
    news_list: list of dicts with keys: 'id','title','url','summary'
    Renders clickable links and a Show details button for each item.
    """
    if not news_list:
        st.info("No news available")
        return
    for i, item in enumerate(news_list):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        summary = item.get("summary", "")
        st.markdown(f"**{title}**")
        if url:
            st.markdown(f"[Open source]({url})")
        if st.button("Show details", key=f"news_{i}"):
            st.write(summary or "No summary available")
        st.markdown("---")

# -------------------------
# Small test utilities
# -------------------------
def test_fetch_last_candles(symbol: str, minutes=60):
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(minutes=minutes)
    try:
        df = get_ohlc_with_fallback(symbol, start, end, interval="5m")
        st.write(f"Fetched {len(df)} rows for {symbol}")
        st.dataframe(df.tail(5))
        return df
    except Exception as e:
        st.error(f"Failed to fetch {symbol}: {e}")
        return None

# -------------------------
# Main UI layout
# -------------------------
st.title("🦅 Eagle Eye Pro v7")

# Top controls
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    symbol = st.selectbox("Symbol", options=["NIFTY", "BANKNIFTY", "GIFTNIFTY", "FINNIFTY"], index=0)
with col2:
    interval = st.selectbox("Interval", options=["1m", "5m", "15m", "30m", "60m"], index=1)
with col3:
    refresh = st.button("Refresh")

# Time range
now = dt.datetime.utcnow()
start = now - dt.timedelta(hours=6)
end = now

# Fetch data (safe)
df = safe_run(get_ohlc_with_fallback, symbol, start, end, interval)

if df is None:
    st.warning("No OHLC data to display. Use debug panel to inspect errors.")
else:
    # Example triangle detection placeholder
    # Replace with your actual triangle detection logic and ensure it returns list of dicts
    triangles = []
    # If you have a function compute_triangles(df) that returns triangles, call it here safely
    # triangles = safe_run(compute_triangles, df) or leave empty
    fig = safe_run(plot_candles_with_annotations, df, triangles, f"{symbol} {interval}")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# News section
st.header("Market News")
# Placeholder news list. Replace with your news fetch logic.
sample_news = [
    {"id": "1", "title": "Macro data lifts markets", "url": "https://example.com/news1", "summary": "Macro data beat expectations and pushed indices higher."},
    {"id": "2", "title": "Company X posts results", "url": "https://example.com/news2", "summary": "Company X reported better-than-expected earnings."}
]
render_news_list(sample_news)

# Signals / Strategy / Calculator / Report placeholders
st.header("Signals & Strategy")
st.info("Signals, SL calculator, strategy engine and reports will render here. If they are failing, enable debug panel to see traces.")

# Example: trigger beep when a new signal arrives (placeholder)
# Replace with your actual signal detection logic
if st.button("Simulate new buy signal"):
    st.success("Buy signal detected for " + symbol)
    beep()

# Last candle overlay for NIFTY and BANKNIFTY (apply same as above)
st.header("Last Candle Snapshot")
for s in ["NIFTY", "BANKNIFTY"]:
    try:
        df_snap = safe_run(get_ohlc_with_fallback, s, now - dt.timedelta(minutes=60), now, "5m")
        if df_snap is not None and not df_snap.empty:
            last = df_snap.iloc[-1]
            st.write(f"**{s}** last candle: Open {last['Open']}, High {last['High']}, Low {last['Low']}, Close {last['Close']}")
    except Exception as e:
        st.warning(f"Could not fetch last candle for {s}: {e}")

# Debug panel
if st.session_state.show_debug:
    st.header("Debug Panel")
    st.subheader("Environment")
    st.write({"now_utc": now.isoformat(), "symbol": symbol, "interval": interval})
    st.subheader("Secrets (masked)")
    secrets_preview = {}
    for k in st.secrets:
        if any(x in k.lower() for x in ("key", "secret", "password", "token")):
            secrets_preview[k] = "***"
        else:
            try:
                secrets_preview[k] = st.secrets.get(k)
            except Exception:
                secrets_preview[k] = "*****"
    st.json(secrets_preview)
    st.subheader("Last exception trace")
    st.text("Check Streamlit logs for full tracebacks")

# -------------------------
# Small test buttons for FINNIFTY and GIFTNIFTY
# -------------------------
st.header("Quick tests")
if st.button("Test FINNIFTY fetch"):
    safe_run(test_fetch_last_candles, "FINNIFTY", 120)
if st.button("Test GIFTNIFTY fetch"):
    safe_run(test_fetch_last_candles, "GIFTNIFTY", 120)

# -------------------------
# End of file
# -------------------------
