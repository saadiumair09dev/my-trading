import { useState, useEffect, useRef, useCallback } from "react";

// \u2500\u2500 COINS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
const COINS = [
  { id: "bitcoin",      symbol: "BTC",  binance: "BTCUSDT",  cc: "BTC"  },
  { id: "ethereum",     symbol: "ETH",  binance: "ETHUSDT",  cc: "ETH"  },
  { id: "solana",       symbol: "SOL",  binance: "SOLUSDT",  cc: "SOL"  },
  { id: "binancecoin",  symbol: "BNB",  binance: "BNBUSDT",  cc: "BNB"  },
  { id: "ripple",       symbol: "XRP",  binance: "XRPUSDT",  cc: "XRP"  },
  { id: "dogecoin",     symbol: "DOGE", binance: "DOGEUSDT", cc: "DOGE" },
];

const SOURCES   = ["CoinGecko", "Binance", "CryptoCompare"];
const INTERVALS = [5, 10, 30];

// \u2500\u2500 FETCHERS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
async function fetchCoinGecko() {
  const ids = COINS.map(c => c.id).join(",");
  const r = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true`);
  if (!r.ok) throw new Error("CoinGecko fail");
  const d = await r.json();
  return COINS.map(c => ({
    symbol: c.symbol,
    price: d[c.id]?.usd ?? null,
    change24h: d[c.id]?.usd_24h_change ?? null,
    volume: d[c.id]?.usd_24h_vol ?? null,
  }));
}

async function fetchBinance() {
  const results = await Promise.all(
    COINS.map(c =>
      fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${c.binance}`)
        .then(r => r.json())
        .then(d => ({
          symbol: c.symbol,
          price: parseFloat(d.lastPrice),
          change24h: parseFloat(d.priceChangePercent),
          volume: parseFloat(d.quoteVolume),
        }))
    )
  );
  return results;
}

async function fetchCryptoCompare() {
  const fsyms = COINS.map(c => c.cc).join(",");
  const r = await fetch(`https://min-api.cryptocompare.com/data/pricemultifull?fsyms=${fsyms}&tsyms=USD`);
  if (!r.ok) throw new Error("CC fail");
  const d = await r.json();
  return COINS.map(c => {
    const x = d.RAW?.[c.cc]?.USD;
    return {
      symbol: c.symbol,
      price: x?.PRICE ?? null,
      change24h: x?.CHANGEPCT24HOUR ?? null,
      volume: x?.VOLUME24HOURTO ?? null,
    };
  });
}

const FETCHERS = [fetchCoinGecko, fetchBinance, fetchCryptoCompare];

// Nifty via Yahoo Finance (no-cors proxy attempt)
async function fetchNifty() {
  try {
    const [niftyR, giftR] = await Promise.allSettled([
      fetch("https://query2.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=2d"),
      fetch("https://query2.finance.yahoo.com/v8/finance/chart/%5ENIFTYSGX?interval=1d&range=2d"),
    ]);
    const parseYahoo = async (res) => {
      if (res.status !== "fulfilled" || !res.value.ok) return null;
      const d = await res.value.json();
      const meta = d?.chart?.result?.[0]?.meta;
      if (!meta) return null;
      return {
        price: meta.regularMarketPrice,
        prev:  meta.previousClose || meta.chartPreviousClose,
      };
    };
    const nifty = await parseYahoo(niftyR);
    const gift  = await parseYahoo(giftR);
    return { nifty, gift };
  } catch {
    return { nifty: null, gift: null };
  }
}

// \u2500\u2500 HELPERS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
const fmtP = (n, d = 2) => {
  if (!n && n !== 0) return "\u2014";
  if (Math.abs(n) >= 1e9) return `$${(n/1e9).toFixed(1)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n/1e6).toFixed(1)}M`;
  return `$${Number(n).toLocaleString("en-US", { maximumFractionDigits: d })}`;
};
const fmtC = n => (!n && n !== 0) ? "\u2014" : `${n >= 0 ? "+" : ""}${Number(n).toFixed(2)}%`;
const fmtINR = n => (!n && n !== 0) ? "\u2014" : `\u20b9${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

// \u2500\u2500 DOTS INDICATOR \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
// 5 dots: strength = |change| / 0.4, capped at 5
function DotsIndicator({ change, size = 9 }) {
  if (change === null || change === undefined) {
    return (
      <div style={{ display: "flex", gap: 3 }}>
        {[1,2,3,4,5].map(i => (
          <div key={i} style={{ width: size, height: size, borderRadius: "50%", background: "#1e3a4a" }} />
        ))}
      </div>
    );
  }
  const isUp     = change >= 0;
  const strength = Math.min(5, Math.round(Math.abs(change) / 0.4));
  const activeC  = isUp ? "#22c55e" : "#ef4444";
  const glowC    = isUp ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)";
  return (
    <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
      {[1,2,3,4,5].map(i => {
        const active = i <= strength;
        return (
          <div key={i} style={{
            width: size, height: size, borderRadius: "50%",
            background: active ? activeC : "#1a2e3a",
            border: `1px solid ${active ? activeC : "#253d4a"}`,
            boxShadow: active ? `0 0 5px ${glowC}` : "none",
            transition: "all 0.4s ease",
          }} />
        );
      })}
    </div>
  );
}

// \u2500\u2500 MINI SPARK \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function Spark({ data, up }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const W = 60, H = 20;
  const pts = data.map((v, i) =>
    `${(i / (data.length - 1)) * W},${H - ((v - min) / range) * (H - 2) - 1}`
  ).join(" ");
  return (
    <svg width={W} height={H} style={{ opacity: 0.6 }}>
      <polyline points={pts} fill="none" stroke={up ? "#22c55e" : "#ef4444"} strokeWidth="1.2" />
    </svg>
  );
}

// \u2500\u2500 MAIN \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
export default function Dashboard() {
  const [prices,    setPrices]    = useState([]);
  const [niftyData, setNiftyData] = useState({ nifty: null, gift: null });
  const [srcIdx,    setSrcIdx]    = useState(0);
  const [interval_, setInterval_] = useState(10);
  const [countdown, setCountdown] = useState(10);
  const [loading,   setLoading]   = useState(false);
  const [errors,    setErrors]    = useState({});
  const [alerts,    setAlerts]    = useState([]);
  const [history,   setHistory]   = useState({});
  const [lastFetch, setLastFetch] = useState(null);
  const [fetchCnt,  setFetchCnt]  = useState({ CoinGecko:0, Binance:0, CryptoCompare:0 });
  const prevRef = useRef({});
  const timerRef = useRef(null);
  const cdRef    = useRef(null);

  const doFetch = useCallback(async (idx) => {
    setLoading(true);
    const src = SOURCES[idx];
    try {
      const [cryptoData, nifty] = await Promise.all([
        FETCHERS[idx](),
        fetchNifty(),
      ]);
      setPrices(cryptoData);
      setNiftyData(nifty);
      setLastFetch(new Date());
      setErrors(e => ({ ...e, [src]: null }));
      setFetchCnt(c => ({ ...c, [src]: (c[src]||0) + 1 }));

      // Opportunity alerts
      const newAlerts = [];
      cryptoData.forEach(d => {
        if (d.change24h !== null && Math.abs(d.change24h) >= 2) {
          if (prevRef.current[d.symbol] !== d.price) {
            newAlerts.push({ id: `${Date.now()}-${d.symbol}`, symbol: d.symbol, change: d.change24h, price: d.price, src, time: new Date() });
          }
        }
        prevRef.current[d.symbol] = d.price;
      });
      if (newAlerts.length) setAlerts(a => [...newAlerts, ...a].slice(0, 6));

      setHistory(h => {
        const u = { ...h };
        cryptoData.forEach(d => {
          if (d.price) {
            u[d.symbol] = [...(u[d.symbol] || []), d.price].slice(-20);
          }
        });
        return u;
      });
    } catch(e) {
      setErrors(prev => ({ ...prev, [src]: true }));
    } finally {
      setLoading(false);
    }
  }, []);

  const rotate = useCallback(() => {
    setSrcIdx(prev => {
      const next = (prev + 1) % SOURCES.length;
      doFetch(next);
      return next;
    });
    setCountdown(interval_);
  }, [interval_, doFetch]);

  useEffect(() => { doFetch(0); }, []);

  useEffect(() => {
    clearInterval(timerRef.current);
    clearInterval(cdRef.current);
    setCountdown(interval_);
    timerRef.current = setInterval(rotate, interval_ * 1000);
    cdRef.current    = setInterval(() => setCountdown(c => c <= 1 ? interval_ : c - 1), 1000);
    return () => { clearInterval(timerRef.current); clearInterval(cdRef.current); };
  }, [interval_, rotate]);

  const src = SOURCES[srcIdx];
  const niftyChange = niftyData.nifty
    ? ((niftyData.nifty.price - niftyData.nifty.prev) / niftyData.nifty.prev) * 100
    : null;
  const giftChange = niftyData.gift
    ? ((niftyData.gift.price - niftyData.gift.prev) / niftyData.gift.prev) * 100
    : null;

  return (
    <div style={{
      height: "100vh", background: "#030b10", color: "#cbd5e1",
      fontFamily: "'Courier New', monospace",
      display: "flex", flexDirection: "column", overflow: "hidden",
      fontSize: 12,
    }}>
      <style>{`
        @keyframes glow { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes ping  { 75%,100%{transform:scale(2);opacity:0} }
        @keyframes fadein{ from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
        .card:hover { background:#0a2030 !important; }
        button:hover { opacity:0.75; }
        ::-webkit-scrollbar{ display:none; }
      `}</style>

      {/* \u2500\u2500 TOP BAR \u2500\u2500 */}
      <div style={{
        background: "#040e16",
        borderBottom: "1px solid #0f2d3d",
        padding: "6px 14px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 14, fontWeight: 700, letterSpacing: 3, color: "#f59e0b" }}>\u25c8 TRADE RADAR</span>
          <span style={{ fontSize: 9, color: "#334155", letterSpacing: 2 }}>MULTI-SOURCE</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Source pills */}
          {SOURCES.map((s, i) => (
            <div key={s} style={{
              display: "flex", alignItems: "center", gap: 4,
              padding: "2px 7px", borderRadius: 3,
              background: i === srcIdx ? "#0c2a1a" : "transparent",
              border: `1px solid ${i === srcIdx ? "#16a34a" : "#0f2d3d"}`,
              fontSize: 9, color: i === srcIdx ? "#4ade80" : "#334155",
            }}>
              <span style={{ width: 5, height: 5, borderRadius: "50%", background: errors[s] ? "#ef4444" : i === srcIdx ? "#4ade80" : "#1e3a4a", display: "inline-block", animation: i === srcIdx ? "glow 1.5s infinite" : "none" }} />
              {s.slice(0,4).toUpperCase()}
            </div>
          ))}

          <div style={{ width: 1, height: 16, background: "#0f2d3d" }} />

          {/* Interval buttons */}
          {INTERVALS.map(s => (
            <button key={s} onClick={() => setInterval_(s)} style={{
              padding: "2px 7px", fontSize: 9, borderRadius: 3,
              border: `1px solid ${interval_===s ? "#f59e0b" : "#0f2d3d"}`,
              background: interval_===s ? "#2a1a00" : "transparent",
              color: interval_===s ? "#f59e0b" : "#334155",
              cursor: "pointer",
            }}>{s}s</button>
          ))}

          <div style={{ width: 1, height: 16, background: "#0f2d3d" }} />

          {/* Countdown */}
          <div style={{ display:"flex", alignItems:"center", gap: 5 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: countdown <= 3 ? "#ef4444" : "#f59e0b", fontVariantNumeric: "tabular-nums", minWidth: 22, textAlign:"right" }}>
              {String(countdown).padStart(2,"0")}
            </div>
            <div style={{ width: 36, height: 3, background: "#0f2d3d", borderRadius: 2 }}>
              <div style={{ height:"100%", borderRadius:2, background:"#f59e0b", width:`${((interval_-countdown)/interval_)*100}%`, transition:"width 1s linear" }} />
            </div>
          </div>

          <button onClick={rotate} disabled={loading} style={{
            padding: "3px 9px", fontSize: 9, letterSpacing: 1,
            border: "1px solid #f59e0b", background: "transparent",
            color: "#f59e0b", borderRadius: 3, cursor: "pointer",
            opacity: loading ? 0.4 : 1,
          }}>
            {loading ? "..." : "\u21bb NOW"}
          </button>
        </div>
      </div>

      {/* \u2500\u2500 NIFTY BANNER \u2500\u2500 */}
      <div style={{
        background: "#040e16",
        borderBottom: "1px solid #0f2d3d",
        padding: "8px 14px",
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 8,
        flexShrink: 0,
      }}>
        {/* GIFT Nifty */}
        <NiftyBox
          label="GIFT NIFTY"
          price={niftyData.gift?.price}
          change={giftChange}
          badge="SGX"
          color="#f59e0b"
        />

        {/* Nifty 50 */}
        <NiftyBox
          label="NIFTY 50"
          price={niftyData.nifty?.price}
          change={niftyChange}
          badge="NSE"
          color="#38bdf8"
        />

        {/* Last update + alert strip */}
        <div style={{ display:"flex", flexDirection:"column", justifyContent:"center", gap:4, paddingLeft: 8, borderLeft: "1px solid #0f2d3d" }}>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:9, color:"#334155" }}>
            <span>LAST UPDATE</span>
            <span style={{ color:"#94a3b8" }}>{lastFetch ? lastFetch.toLocaleTimeString() : "\u2014"}</span>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:9, color:"#334155" }}>
            <span>ACTIVE SRC</span>
            <span style={{ color:"#f59e0b" }}>{src.toUpperCase()}</span>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:9, color:"#334155" }}>
            <span>NEXT SRC</span>
            <span style={{ color:"#475569" }}>{SOURCES[(srcIdx+1)%3].toUpperCase()}</span>
          </div>
          <div style={{ display:"flex", gap:2, marginTop:2 }}>
            {SOURCES.map((_,i)=>(
              <div key={i} style={{ flex:1, height:2, background: i===srcIdx?"#f59e0b": i<srcIdx?"#1a4a2a":"#0f2d3d", borderRadius:1 }} />
            ))}
          </div>
        </div>
      </div>

      {/* \u2500\u2500 CRYPTO GRID \u2500\u2500 */}
      <div style={{
        flex: 1,
        display: "grid",
        gridTemplateColumns: "repeat(3,1fr)",
        gridTemplateRows: "repeat(2,1fr)",
        gap: 6,
        padding: "6px 10px",
        overflow: "hidden",
      }}>
        {(prices.length ? prices : COINS.map(c=>({symbol:c.symbol,price:null,change24h:null,volume:null}))).map((coin, idx) => {
          const isUp   = (coin.change24h??0) >= 0;
          const isBig  = coin.change24h !== null && Math.abs(coin.change24h) >= 2;
          const hist   = history[coin.symbol] || [];
          const accentC = isUp ? "#22c55e" : "#ef4444";
          return (
            <div key={coin.symbol} className="card" style={{
              background: "#050f18",
              border: `1px solid ${isBig ? accentC+"55" : "#0f2d3d"}`,
              borderRadius: 6,
              padding: "8px 10px",
              display: "flex", flexDirection: "column", justifyContent: "space-between",
              boxShadow: isBig ? `0 0 12px ${accentC}22` : "none",
              transition: "all 0.3s",
              position: "relative", overflow: "hidden",
              cursor: "default",
              animation: `fadein 0.3s ease ${idx*0.05}s both`,
            }}>
              {/* Spark background */}
              <div style={{ position:"absolute", bottom:0, right:0, opacity:0.12 }}>
                <Spark data={hist} up={isUp} />
              </div>

              {/* Signal badge */}
              {isBig && (
                <div style={{
                  position:"absolute", top:6, right:7,
                  fontSize:8, padding:"1px 5px", borderRadius:2,
                  background: isUp?"#14532d":"#7f1d1d",
                  color: isUp?"#4ade80":"#fca5a5",
                  letterSpacing:1,
                }}>\u2605 SIGNAL</div>
              )}

              {/* Row 1: symbol + change */}
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
                <span style={{ fontSize:11, color:"#475569", letterSpacing:3 }}>{coin.symbol}</span>
                <span style={{ fontSize:12, fontWeight:700, color: coin.change24h===null?"#1e3a4a":accentC }}>
                  {fmtC(coin.change24h)}
                </span>
              </div>

              {/* Row 2: Price big */}
              <div style={{ fontSize:18, fontWeight:700, color: coin.price?"#f1f5f9":"#1e3a4a", letterSpacing:-0.5, fontVariantNumeric:"tabular-nums" }}>
                {coin.price ? fmtP(coin.price, coin.price < 1 ? 4 : 2) : "\u2014"}
              </div>

              {/* Row 3: Dots + volume */}
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                <DotsIndicator change={coin.change24h} size={7} />
                <span style={{ fontSize:9, color:"#253d4a" }}>
                  {coin.volume ? fmtP(coin.volume) : ""}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* \u2500\u2500 BOTTOM ALERT BAR \u2500\u2500 */}
      <div style={{
        borderTop:"1px solid #0f2d3d",
        background:"#040e16",
        padding:"4px 12px",
        display:"flex", alignItems:"center", gap:8,
        flexShrink:0, minHeight:28, overflowX:"auto",
      }}>
        <span style={{ fontSize:9, color:"#f59e0b", letterSpacing:2, flexShrink:0 }}>\u2605 SIGNALS</span>
        {alerts.length === 0 ? (
          <span style={{ fontSize:9, color:"#1e3a4a" }}>Waiting for \u00b12% moves...</span>
        ) : (
          alerts.map(a => (
            <div key={a.id} style={{
              display:"flex", gap:5, alignItems:"center",
              padding:"2px 8px", borderRadius:3,
              background: a.change>=0?"#052010":"#150505",
              border:`1px solid ${a.change>=0?"#16a34a":"#7f1d1d"}`,
              fontSize:9, flexShrink:0,
              animation:"fadein 0.3s ease",
            }}>
              <span style={{ color:"#94a3b8", fontWeight:700 }}>{a.symbol}</span>
              <span style={{ color: a.change>=0?"#4ade80":"#f87171", fontWeight:700 }}>{fmtC(a.change)}</span>
              <span style={{ color:"#334155" }}>{a.time.toLocaleTimeString("en",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}</span>
            </div>
          ))
        )}
        <div style={{ marginLeft:"auto", display:"flex", gap:10, fontSize:9, color:"#1e3a4a", flexShrink:0 }}>
          <span>CYCLE: CoinGecko\u2192Binance\u2192CryptoCompare\u2192\u2026</span>
        </div>
      </div>
    </div>
  );
}

// \u2500\u2500 NIFTY BOX \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function NiftyBox({ label, price, change, badge, color }) {
  const isUp     = (change??0) >= 0;
  const changeC  = change === null ? "#334155" : isUp ? "#22c55e" : "#ef4444";
  return (
    <div style={{
      background:"#050f18",
      border:`1px solid ${color}33`,
      borderRadius:5, padding:"6px 10px",
      display:"flex", justifyContent:"space-between", alignItems:"center",
    }}>
      {/* Left */}
      <div>
        <div style={{ display:"flex", gap:5, alignItems:"center", marginBottom:3 }}>
          <span style={{ fontSize:9, color:"#475569", letterSpacing:2 }}>{label}</span>
          <span style={{ fontSize:7, padding:"1px 4px", borderRadius:2, background:`
