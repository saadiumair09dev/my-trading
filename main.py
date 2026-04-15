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
  },[ivl,doFetch]);

  useEffect(()=>{ doFetch(0); },[]);
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
    <div style={{height:"100vh",background:"#03090f",color:"#cbd5e1",fontFamily:"'Courier New',monospace",display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <style>{`
        @keyframes glow{0%,100%{opacity:1}50%{opacity:0.4}}
        @keyframes fadein{from{opacity:0;transform:translateY(-5px)}to{opacity:1;transform:translateY(0)}}
        .hov:hover{background:#071828!important;} button{font-family:inherit;}
        ::-webkit-scrollbar{display:none;}
      `}</style>

      {/* ═══ TOPBAR ═══ */}
      <div style={{background:"#040c14",borderBottom:"1px solid #0e2535",padding:"5px 12px",display:"flex",alignItems:"center",justifyContent:"space-between",flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:13,fontWeight:700,letterSpacing:3,color:"#f59e0b"}}>◈ TRADE RADAR</span>
          <span style={{fontSize:8,color:"#1e3a4a",letterSpacing:2}}>MULTI-SRC ENGINE</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          {/* source chips */}
          {SOURCES.map((s,i)=>(
            <div key={s} style={{display:"flex",alignItems:"center",gap:3,padding:"2px 6px",borderRadius:3,background:i===srcIdx?"#0c2218":"transparent",border:`1px solid ${i===srcIdx?"#22c55e":"#0e2535"}`,fontSize:8,color:i===srcIdx?"#4ade80":"#1e3a4a"}}>
              <span style={{width:4,height:4,borderRadius:"50%",background:errors[s]?"#ef4444":i===srcIdx?"#4ade80":"#1e3a4a",display:"inline-block",animation:i===srcIdx?"glow 1.5s infinite":"none"}}/>
              {s.slice(0,4).toUpperCase()}
              <span style={{color:"#1e3a4a"}}>×{cnt[s]}</span>
            </div>
          ))}
          <div style={{width:1,height:14,background:"#0e2535"}}/>
          {INTERVALS.map(s=>(
            <button key={s} onClick={()=>setIvl(s)} style={{padding:"2px 6px",fontSize:8,borderRadius:3,border:`1px solid ${ivl===s?"#f59e0b":"#0e2535"}`,background:ivl===s?"#1e1000":"transparent",color:ivl===s?"#f59e0b":"#1e3a4a",cursor:"pointer"}}>
              {s}s
            </button>
          ))}
          <div style={{display:"flex",alignItems:"center",gap:4}}>
            <span style={{fontSize:14,fontWeight:700,color:cd<=3?"#ef4444":"#f59e0b",fontVariantNumeric:"tabular-nums",minWidth:20,textAlign:"right"}}>{String(cd).padStart(2,"0")}</span>
            <div style={{width:30,height:3,background:"#0e2535",borderRadius:2}}>
              <div style={{height:"100%",borderRadius:2,background:"#f59e0b",width:`${((ivl-cd)/ivl)*100}%`,transition:"width 1s linear"}}/>
            </div>
          </div>
          <button onClick={rotate} disabled={loading} style={{padding:"2px 8px",fontSize:8,letterSpacing:1,border:"1px solid #f59e0b",background:"transparent",color:"#f59e0b",borderRadius:3,cursor:"pointer",opacity:loading?0.4:1}}>
            {loading?"…":"↻ NOW"}
          </button>
        </div>
      </div>

      {/* ═══ NIFTY ROW ═══ */}
      <div style={{background:"#040c14",borderBottom:"1px solid #0e2535",padding:"6px 10px",display:"grid",gridTemplateColumns:"1fr 1fr auto",gap:8,flexShrink:0}}>
        <NiftyBox label="GIFT NIFTY" sub="SGX·FUTURES" price={nifty.gift?.price} change={giftChg} accent="#f59e0b"/>
        <NiftyBox label="NIFTY 50"   sub="NSE·CASH"    price={nifty.nifty?.price} change={niftyChg} accent="#38bdf8"/>
        {/* Meta panel */}
        <div style={{display:"flex",flexDirection:"column",justifyContent:"center",gap:4,paddingLeft:10,borderLeft:"1px solid #0e2535",minWidth:140}}>
          <Row label="UPDATED"   val={lastFetch?lastFetch.toLocaleTimeString():"—"} vc="#94a3b8"/>
          <Row label="SOURCE"    val={src.toUpperCase()} vc="#f59e0b"/>
          <Row label="NEXT"      val={SOURCES[(srcIdx+1)%3].toUpperCase()} vc="#475569"/>
          <div style={{display:"flex",gap:2,marginTop:1}}>
            {SOURCES.map((_,i)=>(
              <div key={i} style={{flex:1,height:2,borderRadius:1,background:i===srcIdx?"#f59e0b":i<srcIdx?"#1a3a22":"#0e2535"}}/>
            ))}
          </div>
        </div>
      </div>

      {/* ═══ CRYPTO GRID ═══ */}
      <div style={{flex:1,display:"grid",gridTemplateColumns:"repeat(3,1fr)",gridTemplateRows:"repeat(2,1fr)",gap:6,padding:"6px 10px",overflow:"hidden"}}>
        {(prices.length?prices:COINS.map(c=>({symbol:c.symbol,price:null,change24h:null,volume:null}))).map((coin,idx)=>{
          const isUp  = (coin.change24h??0)>=0;
          const isBig = coin.change24h!==null&&Math.abs(coin.change24h)>=2;
          const hist  = history[coin.symbol]||[];
          const ac    = isUp?"#22c55e":"#ef4444";
          return (
            <div key={coin.symbol} className="hov" style={{
              background:"#040e18",
              border:`1px solid ${isBig?ac+"44":"#0e2535"}`,
              borderRadius:6,padding:"8px 10px",
              display:"flex",flexDirection:"column",justifyContent:"space-between",
              boxShadow:isBig?`0 0 14px ${ac}18`:"none",
              transition:"all 0.3s",position:"relative",overflow:"hidden",
              animation:`fadein 0.3s ease ${idx*0.05}s both`,
            }}>
              {/* bg sparkline */}
              <div style={{position:"absolute",bottom:0,right:0,opacity:1}}>
                <Spark data={hist} up={isUp}/>
              </div>

              {/* signal badge */}
              {isBig&&<div style={{position:"absolute",top:6,right:7,fontSize:7,padding:"1px 5px",borderRadius:2,background:isUp?"#14532d":"#7f1d1d",color:isUp?"#4ade80":"#fca5a5",letterSpacing:1}}>★ SIGNAL</div>}

              {/* symbol + % */}
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <span style={{fontSize:10,color:"#475569",letterSpacing:3}}>{coin.symbol}</span>
                <span style={{fontSize:11,fontWeight:700,color:coin.change24h===null?"#1e3a4a":ac}}>
                  {fmtC(coin.change24h)}
                </span>
              </div>

              {/* price */}
              <div style={{fontSize:19,fontWeight:700,color:coin.price?"#f1f5f9":"#1e3a4a",fontVariantNumeric:"tabular-nums",letterSpacing:-0.5}}>
                {coin.price?fmtP(coin.price,coin.price<1?4:2):"—"}
              </div>

              {/* dots + vol */}
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <DotsIndicator change={coin.change24h} size={7}/>
                <span style={{fontSize:8,color:"#1e3a4a"}}>{coin.volume?fmtP(coin.volume):""}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ═══ ALERT TICKER ═══ */}
      <div style={{background:"#040c14",borderTop:"1px solid #0e2535",padding:"3px 10px",display:"flex",alignItems:"center",gap:8,flexShrink:0,minHeight:26,overflowX:"auto"}}>
        <span style={{fontSize:8,color:"#f59e0b",letterSpacing:2,flexShrink:0}}>★ SIGNALS</span>
        {alerts.length===0
          ? <span style={{fontSize:8,color:"#1e3a4a"}}>Monitoring... ±2% move pe alert ayega</span>
          : alerts.map(a=>(
            <div key={a.id} style={{display:"flex",gap:5,alignItems:"center",padding:"2px 7px",borderRadius:3,background:a.change>=0?"#052010":"#150505",border:`1px solid ${a.change>=0?"#16a34a":"#7f1d1d"}`,fontSize:8,flexShrink:0,animation:"fadein 0.3s ease"}}>
              <span style={{color:"#94a3b8",fontWeight:700}}>{a.symbol}</span>
              <span style={{color:a.change>=0?"#4ade80":"#f87171",fontWeight:700}}>{fmtC(a.change)}</span>
              <span style={{color:"#334155"}}>{a.time.toLocaleTimeString("en",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}</span>
              <span style={{color:"#1e3a4a"}}>{a.src.slice(0,2).toUpperCase()}</span>
            </div>
          ))
        }
        <span style={{marginLeft:"auto",fontSize:8,color:"#0e2535",flexShrink:0}}>
          {SOURCES.join(" → ")} → loop
        </span>
      </div>
    </div>
  );
}

function NiftyBox({label,sub,price,change,accent}){
  const isUp=!change||change>=0;
  const cc=change===null?"#1e3a4a":isUp?"#22c55e":"#ef4444";
  return (
    <div style={{background:"#040e18",border:`1px solid ${accent}22`,borderRadius:5,padding:"6px 10px",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
      <div>
        <div style={{display:"flex",gap:5,alignItems:"baseline",marginBottom:2}}>
          <span style={{fontSize:10,color:"#475569",letterSpacing:2}}>{label}</span>
          <span style={{fontSize:7,color:accent,letterSpacing:1}}>{sub}</span>
        </div>
        <div style={{fontSize:20,fontWeight:700,color:price?"#f1f5f9":"#1e3a4a",fontVariantNumeric:"tabular-nums"}}>
          {price?`₹${Number(price).toLocaleString("en-IN",{maximumFractionDigits:0})}`:"—"}
        </div>
      </div>
      <div style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:5}}>
        <span style={{fontSize:13,fontWeight:700,color:cc}}>
          {change!==null?`${isUp?"+":""}${change.toFixed(2)}%`:"—"}
        </span>
        <DotsIndicator change={change} size={9}/>
      </div>
    </div>
  );
}

function Row({label,val,vc}){
  return (
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",fontSize:8}}>
      <span style={{color:"#1e3a4a",letterSpacing:1}}>{label}</span>
      <span style={{color:vc||"#94a3b8"}}>{val}</span>
    </div>
  );
}
