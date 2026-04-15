import { useState, useEffect, useRef, useCallback } from "react";

const COINS = [
  { id:"bitcoin",     symbol:"BTC",  binance:"BTCUSDT",  cc:"BTC"  },
  { id:"ethereum",    symbol:"ETH",  binance:"ETHUSDT",  cc:"ETH"  },
  { id:"solana",      symbol:"SOL",  binance:"SOLUSDT",  cc:"SOL"  },
  { id:"binancecoin", symbol:"BNB",  binance:"BNBUSDT",  cc:"BNB"  },
  { id:"ripple",      symbol:"XRP",  binance:"XRPUSDT",  cc:"XRP"  },
  { id:"dogecoin",    symbol:"DOGE", binance:"DOGEUSDT", cc:"DOGE" },
];
const SOURCES   = ["CoinGecko","Binance","CryptoCompare"];
const INTERVALS = [5,10,30];

// FIX: Backticks correctly used for template literals
async function fetchCoinGecko() {
  const ids = COINS.map(c=>c.id).join(",");
  const r = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true`);
  if(!r.ok) throw new Error("CG fail");
  const d = await r.json();
  return COINS.map(c=>({ symbol:c.symbol, price:d[c.id]?.usd??null, change24h:d[c.id]?.usd_24h_change??null, volume:d[c.id]?.usd_24h_vol??null }));
}

async function fetchBinance() {
  return Promise.all(COINS.map(c=>
    fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${c.binance}`)
      .then(r=>r.json())
      .then(d=>({ symbol:c.symbol, price:parseFloat(d.lastPrice), change24h:parseFloat(d.priceChangePercent), volume:parseFloat(d.quoteVolume) }))
  ));
}

async function fetchCryptoCompare() {
  const fsyms = COINS.map(c=>c.cc).join(",");
  const r = await fetch(`https://min-api.cryptocompare.com/data/pricemultifull?fsyms=${fsyms}&tsyms=USD`);
  if(!r.ok) throw new Error("CC fail");
  const d = await r.json();
  return COINS.map(c=>{ const x=d.RAW?.[c.cc]?.USD; return { symbol:c.symbol, price:x?.PRICE??null, change24h:x?.CHANGEPCT24HOUR??null, volume:x?.VOLUME24HOURTO??null }; });
}

const FETCHERS=[fetchCoinGecko,fetchBinance,fetchCryptoCompare];

async function fetchNifty() {
  const toTry = [
    ["nifty","https://query2.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=2d"],
    ["gift", "https://query2.finance.yahoo.com/v8/finance/chart/%5ENIFTYSGX?interval=1d&range=2d"],
  ];
  const out={nifty:null,gift:null};
  await Promise.all(toTry.map(async([key,url])=>{
    try {
      const r=await fetch(url);
      if(!r.ok) return;
      const d=await r.json();
      const meta=d?.chart?.result?.[0]?.meta;
      if(meta){ out[key]={ price:meta.regularMarketPrice, prev:meta.previousClose||meta.chartPreviousClose }; }
    } catch{}
  }));
  return out;
}

const fmtP=(n,dec=2)=>{
  if(n===null||n===undefined||isNaN(n)) return "—";
  if(Math.abs(n)>=1e9) return `$${(n/1e9).toFixed(1)}B`;
  if(Math.abs(n)>=1e6) return `$${(n/1e6).toFixed(1)}M`;
  return `$${Number(n).toLocaleString("en-US",{maximumFractionDigits:dec})}`;
};
const fmtC=n=>(!n&&n!==0)?"—":`${n>=0?"+":""}${Number(n).toFixed(2)}%`;

function DotsIndicator({change,size=8}){
  const active = change!==null&&change!==undefined;
  const isUp   = active && change>=0;
  const strength = active ? Math.min(5,Math.round(Math.abs(change)/0.4)) : 0;
  const onC  = isUp?"#22c55e":"#ef4444";
  const glow = isUp?"rgba(34,197,94,0.7)":"rgba(239,68,68,0.7)";
  return (
    <div style={{display:"flex",gap:3,alignItems:"center"}}>
      {[1,2,3,4,5].map(i=>{
        const lit=active&&i<=strength;
        return (
          <div key={i} style={{
            width:size,height:size,borderRadius:"50%",
            background:lit?onC:"#0f2030",
            border:`1px solid ${lit?onC:"#1a3040"}`,
            boxShadow:lit?`0 0 5px ${glow}`:"none",
            transition:"all 0.35s ease",
          }}/>
        );
      })}
    </div>
  );
}

function Spark({data,up}){
  if(!data||data.length<2) return null;
  const min=Math.min(...data),max=Math.max(...data),range=max-min||1;
  const W=56,H=18;
  const pts=data.map((v,i)=>`${(i/(data.length-1))*W},${H-((v-min)/range)*(H-2)-1}`).join(" ");
  return <svg width={W} height={H} style={{opacity:0.18,display:"block"}}><polyline points={pts} fill="none" stroke={up?"#22c55e":"#ef4444"} strokeWidth="1.5"/></svg>;
}

export default function Dashboard(){
  const [prices,   setPrices]   = useState([]);
  const [nifty,    setNifty]    = useState({nifty:null,gift:null});
  const [srcIdx,   setSrcIdx]   = useState(0);
  const [ivl,      setIvl]      = useState(10);
  const [cd,       setCd]       = useState(10);
  const [loading,  setLoading]  = useState(false);
  const [errors,   setErrors]   = useState({});
  const [alerts,   setAlerts]   = useState([]);
  const [history,  setHistory]  = useState({});
  const [lastFetch,setLastFetch]= useState(null);
  const [cnt,      setCnt]      = useState({CoinGecko:0,Binance:0,CryptoCompare:0});
  const prevRef  = useRef({});
  const timerRef = useRef(null);
  const cdRef    = useRef(null);

  const doFetch=useCallback(async(idx)=>{
    setLoading(true);
    const src=SOURCES[idx];
    try {
      const [crypto,niftyD]=await Promise.all([FETCHERS[idx](),fetchNifty()]);
      setPrices(crypto);
      setNifty(niftyD);
      setLastFetch(new Date());
      setErrors(e=>({...e,[src]:false}));
      setCnt(c=>({...c,[src]:(c[src]||0)+1}));
      const newA=[];
      crypto.forEach(d=>{
        if(d.change24h!==null&&Math.abs(d.change24h)>=2&&prevRef.current[d.symbol]!==d.price)
          newA.push({id:`${Date.now()}-${d.symbol}`,symbol:d.symbol,change:d.change24h,price:d.price,src,time:new Date()});
        prevRef.current[d.symbol]=d.price;
      });
      if(newA.length) setAlerts(a=>[...newA,...a].slice(0,8));
      setHistory(h=>{
        const u={...h};
        crypto.forEach(d=>{ if(d.price) u[d.symbol]=[...(u[d.symbol]||[]),d.price].slice(-20); });
        return u;
      });
    } catch{ setErrors(e=>({...e,[src]:true})); }
    finally{ setLoading(false); }
  },[]);

  const rotate=useCallback(()=>{
    setSrcIdx(p=>{ const n=(p+1)%3; doFetch(n); return n; });
    setCd(ivl);
  }, [ivl, doFetch]);

  useEffect(()=>{ doFetch(0); }, [doFetch]);
  useEffect(()=>{
    clearInterval(timerRef.current); clearInterval(cdRef.current);
    setCd(ivl);
    timerRef.current=setInterval(rotate,ivl*1000);
    cdRef.current=setInterval(()=>setCd(c=>c<=1?ivl:c-1),1000);
    return()=>{ clearInterval(timerRef.current); clearInterval(cdRef.current); };
  },[ivl,rotate]);

  const src=SOURCES[srcIdx];
  const niftyChg = nifty.nifty ? ((nifty.nifty.price-nifty.nifty.prev)/nifty.nifty.prev)*100 : null;
  const giftChg  = nifty.gift  ? ((nifty.gift.price -nifty.gift.prev) /nifty.gift.prev) *100 : null;

  return (
    <div style={{height:"100vh",background:"#03090f",color:"#cbd5e1",fontFamily:"monospace",display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <style>{`
        @keyframes glow{0%,100%{opacity:1}50%{opacity:0.4}}
        @keyframes fadein{from{opacity:0;transform:translateY(-5px)}to{opacity:1;transform:translateY(0)}}
        .hov:hover{background:#071828!important;} button{font-family:inherit;}
      `}</style>

      {/* TOPBAR */}
      <div style={{background:"#040c14",borderBottom:"1px solid #0e2535",padding:"5px 12px",display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:13,fontWeight:700,color:"#f59e0b"}}>◈ TRADE RADAR</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          {SOURCES.map((s,i)=>(
            <div key={s} style={{fontSize:8, color: i===srcIdx ? "#4ade80" : "#1e3a4a"}}>
              {s.toUpperCase()}
            </div>
          ))}
          <span style={{fontSize:14,fontWeight:700,color:cd<=3?"#ef4444":"#f59e0b"}}>{cd}s</span>
          <button onClick={rotate} disabled={loading} style={{fontSize:8,border:"1px solid #f59e0b",background:"transparent",color:"#f59e0b",cursor:"pointer"}}>
            {loading?"…":"↻ NOW"}
          </button>
        </div>
      </div>

      {/* NIFTY ROW */}
      <div style={{background:"#040c14",borderBottom:"1px solid #0e2535",padding:"6px 10px",display:"grid",gridTemplateColumns:"1fr 1fr auto",gap:8}}>
        <NiftyBox label="GIFT NIFTY" sub="SGX" price={nifty.gift?.price} change={giftChg} accent="#f59e0b"/>
        <NiftyBox label="NIFTY 50"   sub="NSE" price={nifty.nifty?.price} change={niftyChg} accent="#38bdf8"/>
      </div>

      {/* CRYPTO GRID */}
      <div style={{flex:1,display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:6,padding:"6px 10px"}}>
        {prices.map((coin,idx)=>(
          <div key={coin.symbol} style={{background:"#040e18", border:"1px solid #0e2535", padding:10, borderRadius:6}}>
            <div style={{display:"flex", justifyContent:"space-between"}}>
              <span style={{fontSize:10, color:"#475569"}}>{coin.symbol}</span>
              <span style={{color: (coin.change24h||0) >=0 ? "#22c55e" : "#ef4444"}}>{fmtC(coin.change24h)}</span>
            </div>
            <div style={{fontSize:18, fontWeight:700}}>{fmtP(coin.price)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NiftyBox({label,sub,price,change,accent}){
  const isUp=!change||change>=0;
  return (
    <div style={{background:"#040e18",border:`1px solid ${accent}22`,borderRadius:5,padding:"6px 10px",display:"flex",justifyContent:"space-between"}}>
      <div>
        <span style={{fontSize:10,color:"#475569"}}>{label}</span>
        <div style={{fontSize:18,fontWeight:700}}>{price?`₹${price.toLocaleString()}`:"—"}</div>
      </div>
      <span style={{color:isUp?"#22c55e":"#ef4444",fontWeight:700}}>{fmtC(change)}</span>
    </div>
  );
}
