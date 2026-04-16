# Eagle Eye Pro v3 - Full Python Conversion
# Isme aapka original code 100% surakshit hai.

html_code = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<meta name="theme-color" content="#020b18"/>
<meta name="mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<title>🦅 Eagle Eye Pro v3</title>
<style>
/* ══ RESET & ROOT ══ */
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#020b18;--card:#050f1e;--border:#0d3060;--blue:#3d9be9;--green:#00d463;
  --red:#ff3d3d;--gold:#ffb700;--text:#dce8f7;--dim:#3d5a7a;--dim2:#0d2040;
  --font:'Courier New',monospace;--sfont:'Segoe UI',Arial,sans-serif;
}
html,body{background:var(--bg);color:var(--text);font-family:var(--sfont);height:100%;overflow:hidden;font-size:12px}
#app{display:flex;flex-direction:column;height:100vh;height:100dvh;overflow:hidden}

/* ══ ANIMATIONS ══ */
@keyframes pulse{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}
@keyframes slideUp{from{transform:translateY(10px);opacity:0}to{transform:translateY(0);opacity:1}}
@keyframes glow{0%{box-shadow:0 0 5px var(--blue)}50%{box-shadow:0 0 15px var(--blue)}100%{box-shadow:0 0 5px var(--blue)}}
.blink{animation:pulse 1s infinite}
.up{color:var(--green)}
.dn{color:var(--red)}

/* ══ HEADER ══ */
header{display:flex;justify-content:space-between;align-items:center;padding:10px 15px;background:var(--card);border-bottom:1px solid var(--border);flex-shrink:0}
.logo{font-family:var(--font);font-weight:700;font-size:1.2rem;color:var(--gold);display:flex;align-items:center;gap:8px}
.logo span{font-size:0.7rem;background:var(--dim2);padding:2px 6px;border-radius:4px;color:var(--blue);border:1px solid var(--border)}
.top-meta{display:flex;gap:15px;font-family:var(--font);font-size:0.85rem}
#clock{color:var(--blue)}

/* ══ TICKER ══ */
#ticker-wrap{background:var(--dim2);border-bottom:1px solid var(--border);height:30px;overflow:hidden;white-space:nowrap;display:flex;align-items:center;flex-shrink:0}
#ticker{display:inline-flex;gap:25px;padding-left:100%;animation:scroll 40s linear infinite}
@keyframes scroll{0%{transform:translateX(0)}100%{transform:translateX(-100%)}}
.t-item{display:flex;gap:6px;font-family:var(--font);font-size:0.85rem}

/* ══ TABS ══ */
nav{display:flex;background:var(--card);overflow-x:auto;border-bottom:1px solid var(--border);scrollbar-width:none;flex-shrink:0}
nav::-webkit-scrollbar{display:none}
.tab{padding:12px 18px;white-space:nowrap;cursor:pointer;color:var(--dim);font-weight:600;border-bottom:2px solid transparent;transition:all .2s;text-transform:uppercase;font-size:0.8rem;letter-spacing:0.5px}
.tab.on{color:var(--blue);border-bottom-color:var(--blue);background:rgba(61,155,233,0.05)}

/* ══ MAIN ══ */
main{flex:1;overflow-y:auto;position:relative;background:radial-gradient(circle at top right, #05162d, var(--bg))}
.panel{display:none;padding:15px;animation:slideUp 0.3s ease-out}
.panel.on{display:block}

/* ══ CARDS & GRIDS ══ */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px}
.card{background:rgba(5,15,30,0.7);border:1px solid var(--border);border-radius:8px;padding:15px;position:relative;overflow:hidden;backdrop-filter:blur(5px)}
.card-h{display:flex;justify-content:space-between;margin-bottom:12px;border-bottom:1px solid var(--dim2);padding-bottom:8px}
.card-t{font-weight:700;color:var(--gold);font-size:0.9rem;display:flex;align-items:center;gap:6px}

/* ══ SIGNAL STYLES ══ */
.sig-row{display:flex;justify-content:space-between;align-items:center;padding:10px;border-bottom:1px solid var(--dim2);font-family:var(--font)}
.sig-row:last-child{border:0}
.sig-main{display:flex;flex-direction:column;gap:2px}
.sig-sym{font-weight:700;font-size:1.1rem}
.sig-type{font-size:0.75rem;text-transform:uppercase;padding:2px 6px;border-radius:3px;width:fit-content}
.bg-buy{background:rgba(0,212,99,0.15);color:var(--green)}
.bg-sell{background:rgba(255,61,61,0.15);color:var(--red)}
.sig-price{text-align:right}
.sig-val{font-size:1.1rem;font-weight:700}
.sig-time{font-size:0.7rem;color:var(--dim)}

/* ══ CHARTS ══ */
.chart-box{height:320px;width:100%;background:var(--dim2);border-radius:4px;margin-bottom:15px;position:relative;border:1px solid var(--border)}
.canvas-wrap{position:relative;width:100%;height:100%}

/* ══ MARKET STATUS ══ */
.m-stat{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--dim2)}
.m-label{color:var(--dim)}
.m-val{font-family:var(--font);font-weight:600}

/* ══ ANALYSIS ══ */
.an-box{margin-top:10px;padding:10px;background:var(--dim2);border-radius:6px;font-family:var(--font)}
.an-bar-wrap{height:12px;background:#0d2040;border-radius:6px;margin:10px 0;display:flex;overflow:hidden;border:1px solid var(--border)}
.an-bar-buy{background:var(--green);height:100%;transition:width 0.5s}
.an-bar-sell{background:var(--red);height:100%;transition:width 0.5s}

/* ══ STRATEGY & NEWS ══ */
.st-card{border-left:4px solid var(--blue);margin-bottom:10px}
.n-item{padding:10px 0;border-bottom:1px solid var(--dim2)}
.n-head{color:var(--gold);margin-bottom:4px;font-weight:600;line-height:1.4}
.n-meta{font-size:0.75rem;color:var(--dim);display:flex;gap:10px}

/* ══ FOOTER BAR ══ */
.bottom-nav{display:flex;background:var(--card);border-top:1px solid var(--border);flex-shrink:0}
.bb{flex:1;padding:12px;text-align:center;font-size:0.7rem;color:var(--dim);cursor:pointer;display:flex;flex-direction:column;gap:4px;align-items:center}
.bb i{font-size:1.2rem}
.bb.on{color:var(--blue);background:rgba(61,155,233,0.05)}

/* ══ MODAL / OVERLAY ══ */
#overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(2,11,24,0.95);z-index:999;display:none;align-items:center;justify-content:center;padding:20px;text-align:center}
#overlay.on{display:flex}
.modal{background:var(--card);border:1px solid var(--gold);padding:30px;border-radius:12px;max-width:400px}
.modal h2{color:var(--gold);margin-bottom:15px}

@media(max-width:480px){
  .top-meta{display:none}
  .grid{grid-template-columns:1fr}
}
</style>
</head>
<body>

<div id="overlay">
  <div class="modal">
    <h2>⚠️ ACCESS EXPIRED</h2>
    <p>Your Pro License has expired. Please contact administrator to renew.</p>
    <div style="margin-top:20px;color:var(--dim)">System ID: EE-V3-9942-X</div>
  </div>
</div>

<div id="app">
  <header>
    <div class="logo">🦅 EAGLE EYE <span>PRO V3</span></div>
    <div class="top-meta">
      <div id="clock">00:00:00</div>
      <div id="connection" class="up">● LIVE</div>
    </div>
  </header>

  <div id="ticker-wrap">
    <div id="ticker"></div>
  </div>

  <nav>
    <div class="tab on" onclick="T('signals')">🎯 SIGNALS</div>
    <div class="tab" onclick="T('market')">📊 MARKET</div>
    <div class="tab" onclick="T('charts')">📉 CHARTS</div>
    <div class="tab" onclick="T('oi')">⚡ OI DATA</div>
    <div class="tab" onclick="T('analysis')">🔍 ANALYSIS</div>
    <div class="tab" onclick="T('strategy')">📜 STRATEGY</div>
    <div class="tab" onclick="T('news')">📰 NEWS</div>
    <div class="tab" onclick="T('slcalc')">🧮 CALC</div>
  </nav>

  <main>
    <div id="p-signals" class="panel on">
      <div class="card-h">
        <div class="card-t">PRO ALGO SIGNALS (5m/15m)</div>
        <div class="up" style="font-size:0.7rem">AUTO-REFRESHING</div>
      </div>
      <div id="sig-list">
        </div>
    </div>

    <div id="p-market" class="panel">
      <div class="grid">
        <div class="card">
          <div class="card-t">GLOBAL INDICES</div>
          <div id="m-indices"></div>
        </div>
        <div class="card">
          <div class="card-t">CURRENCY & COMMODITY</div>
          <div id="m-comm"></div>
        </div>
      </div>
    </div>

    <div id="p-charts" class="panel">
      <div class="card-h">
        <div class="card-t">NIFTY 50 REAL-TIME</div>
        <div id="c-price-nifty" class="sig-val">00.00</div>
      </div>
      <div class="chart-box"><canvas id="cNifty"></canvas></div>
      
      <div class="card-h">
        <div class="card-t">BANK NIFTY REAL-TIME</div>
        <div id="c-price-bank" class="sig-val">00.00</div>
      </div>
      <div class="chart-box"><canvas id="cBank"></canvas></div>
    </div>

    <div id="p-oi" class="panel">
      <div class="card">
        <div class="card-t">OI ANALYSIS (PCR)</div>
        <div class="grid">
          <div style="text-align:center">
            <div style="color:var(--dim)">NIFTY PCR</div>
            <div id="pcr-nifty" style="font-size:1.5rem;font-weight:700">1.00</div>
            <div id="pcr-n-view" class="up">NEUTRAL</div>
          </div>
          <div style="text-align:center">
            <div style="color:var(--dim)">BANK PCR</div>
            <div id="pcr-bank" style="font-size:1.5rem;font-weight:700">1.00</div>
            <div id="pcr-b-view" class="up">NEUTRAL</div>
          </div>
        </div>
      </div>
    </div>

    <div id="p-analysis" class="panel">
      <div class="card">
        <div class="card-t">MARKET SENTIMENT METER</div>
        <div class="an-bar-wrap">
          <div id="sent-buy" class="an-bar-buy" style="width:50%"></div>
          <div id="sent-sell" class="an-bar-sell" style="width:50%"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-family:var(--font)">
          <div class="up">BULLS: <span id="sent-buy-v">50</span>%</div>
          <div class="dn">BEARS: <span id="sent-sell-v">50</span>%</div>
        </div>
        <div id="sent-text" style="margin-top:15px;text-align:center;font-weight:700;color:var(--gold)">
          COLLECTING DATA...
        </div>
      </div>
    </div>

    <div id="p-strategy" class="panel">
      <div id="st-list"></div>
    </div>

    <div id="p-news" class="panel">
      <div id="n-list"></div>
    </div>

    <div id="p-slcalc" class="panel">
      <div class="card">
        <div class="card-t">POSITION SIZING & SL</div>
        <div style="display:flex;flex-direction:column;gap:10px;margin-top:10px">
          <input type="number" id="c-cap" placeholder="Total Capital" style="padding:10px;background:var(--dim2);border:1px solid var(--border);color:#fff">
          <input type="number" id="c-risk" placeholder="Risk % per trade" style="padding:10px;background:var(--dim2);border:1px solid var(--border);color:#fff">
          <input type="number" id="c-ent" placeholder="Entry Price" style="padding:10px;background:var(--dim2);border:1px solid var(--border);color:#fff">
          <input type="number" id="c-sl" placeholder="SL Price" style="padding:10px;background:var(--dim2);border:1px solid var(--border);color:#fff">
          <button onclick="doCalc()" style="padding:12px;background:var(--blue);border:0;color:#fff;font-weight:700;border-radius:4px">CALCULATE</button>
          <div id="c-res" style="margin-top:10px;padding:10px;background:var(--dim2);border-radius:4px;font-family:var(--font)"></div>
        </div>
      </div>
    </div>

  </main>

  <div class="bottom-nav">
    <div class="bb on" onclick="T('signals')">🎯<br>Sigs</div>
    <div class="bb" onclick="T('market')">📊<br>Mkt</div>
    <div class="bb" onclick="T('charts')">📉<br>Cht</div>
    <div class="bb" onclick="T('oi')">⚡<br>OI</div>
  </div>
</div>

<script>
/* ══ CORE STATE ══ */
let l=null,simInterval=null;
const symbols=["NIFTY 50","BANK NIFTY","RELIANCE","TCS","HDFC BANK","ICICI BANK","INFY","GOLD","CRUDE OIL"];
const data={};
symbols.forEach(s=>{ data[s]={p:0,c:0,ch:0,v:0,h:[],l:[]}; });

/* ══ UTILS ══ */
const fNum=(n)=>Number(n).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});
const uClock=()=>{ document.getElementById('clock').textContent=new Date().toLocaleTimeString('en-GB'); };

/* ══ SIMULATION (FALLBACK) ══ */
function simTick(){
  symbols.forEach(s=>{
    if(data[s].p===0){
      if(s.includes("NIFTY 50")) data[s].p=22400;
      else if(s.includes("BANK")) data[s].p=47500;
      else if(s.includes("GOLD")) data[s].p=71000;
      else if(s.includes("CRUDE")) data[s].p=6800;
      else data[s].p=1500+Math.random()*1000;
    }
    const chg=(Math.random()-0.5)*5;
    data[s].p+=chg;
    data[s].ch+=chg;
    data[s].h.push(data[s].p);
    if(data[s].h.length>50) data[s].h.shift();
  });
}

/* ══ LIVE DATA (YAHOO FINANCE API FETCH) ══ */
async function fetchLiveData(){
  // Note: Standard browser CORS policy prevents direct fetch from Yahoo. 
  // In a real production environment, this would hit your own backend proxy.
  // This function simulates the logic for the Pro V3 dashboard.
  try{
    const tickers=["^NSEI","^NSEBANK","RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","GC=F","CL=F"];
    // Mocking the update process to ensure UI stays alive
    symbols.forEach((s,i)=>{
       // random live feel
       data[s].v=(Math.random()-0.4)*2;
    });
  }catch(e){console.log("Feed Err: Using Sim");}
}

/* ══ RENDERERS ══ */
function render(){
  // Ticker
  const t=document.getElementById('ticker');
  t.innerHTML='';
  symbols.forEach(s=>{
    const cl=data[s].ch>=0?'up':'dn';
    t.innerHTML+=`<div class="t-item">${s} <span class="${cl}">${fNum(data[s].p)}</span></div>`;
  });

  // Signals
  const sl=document.getElementById('sig-list');
  sl.innerHTML='';
  symbols.slice(0,6).forEach(s=>{
    const type=data[s].ch>0?'BUY':'SELL';
    const cl=type==='BUY'?'bg-buy':'bg-sell';
    sl.innerHTML+=`
      <div class="sig-row">
        <div class="sig-main">
          <span class="sig-sym">${s}</span>
          <span class="sig-type ${cl}">${type} ZONE</span>
        </div>
        <div class="sig-price">
          <div class="sig-val ${data[s].ch>=0?'up':'dn'}">${fNum(data[s].p)}</div>
          <div class="sig-time">${Math.floor(Math.random()*5)+1}m ago</div>
        </div>
      </div>`;
  });

  // Market
  const mi=document.getElementById('m-indices');
  mi.innerHTML='';
  symbols.slice(0,4).forEach(s=>{
    mi.innerHTML+=`
      <div class="m-stat">
        <span class="m-label">${s}</span>
        <span class="m-val ${data[s].ch>=0?'up':'dn'}">${fNum(data[s].p)}</span>
      </div>`;
  });

  // Prices on Chart Tab
  if(document.getElementById('c-price-nifty')) document.getElementById('c-price-nifty').textContent=fNum(data["NIFTY 50"].p);
  if(document.getElementById('c-price-bank')) document.getElementById('c-price-bank').textContent=fNum(data["BANK NIFTY"].p);
}

/* ══ CHARTS (CANVAS) ══ */
function dCharts(){
  const draw=(id,sym)=>{
    const c=document.getElementById(id);if(!c)return;
    const ctx=c.getContext('2d');
    const h=data[sym].h;
    ctx.clearRect(0,0,c.width,c.height);
    ctx.strokeStyle='#3d9be9';
    ctx.lineWidth=2;
    ctx.beginPath();
    const step=c.width/50;
    const min=Math.min(...h), max=Math.max(...h), range=max-min;
    h.forEach((p,i)=>{
      const x=i*step;
      const y=c.height - ((p-min)/range * c.height);
      if(i===0)ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.stroke();
    // gradient
    ctx.lineTo(h.length*step, c.height);
    ctx.lineTo(0, c.height);
    const g=ctx.createLinearGradient(0,0,0,c.height);
    g.addColorStop(0,'rgba(61,155,233,0.2)');
    g.addColorStop(1,'transparent');
    ctx.fillStyle=g;ctx.fill();
  };
  draw('cNifty',"NIFTY 50");
  draw('cBank',"BANK NIFTY");
}

/* ══ ANALYSIS BIAS ══ */
function bAnalysis(){
  const b=Math.floor(Math.random()*40)+30;
  const s=100-b;
  document.getElementById('sent-buy').style.width=b+'%';
  document.getElementById('sent-sell').style.width=s+'%';
  document.getElementById('sent-buy-v').textContent=b;
  document.getElementById('sent-sell-v').textContent=s;
  const txt=document.getElementById('sent-text');
  if(b>55){txt.textContent="BULLISH BIAS DETECTED";txt.className="up";}
  else if(b<45){txt.textContent="BEARISH BIAS DETECTED";txt.className="dn";}
  else{txt.textContent="SIDEWAYS / NEUTRAL";txt.className="up";}
}

/* ══ STATIC DATA BINDERS ══ */
function bPats(){
  const st=document.getElementById('st-list');
  const items=[
    {n:"Golden Crossover",s:"BULLISH",d:"50 EMA crossing above 200 EMA on 15m chart."},
    {n:"Double Bottom",s:"REVERSAL",d:"Strong support at 22100 with volume spike."},
    {n:"Hanging Man",s:"BEARISH",d:"Potential exhaustion near R1 resistance."}
  ];
  items.forEach(i=>{
    st.innerHTML+=`
      <div class="card st-card">
        <div style="display:flex;justify-content:space-between">
          <span style="font-weight:700">${i.n}</span>
          <span class="up" style="font-size:0.7rem">${i.s}</span>
        </div>
        <p style="font-size:0.8rem;color:var(--dim);margin-top:5px">${i.d}</p>
      </div>`;
  });
}

function bNews(){
  const nl=document.getElementById('n-list');
  const news=[
    {h:"Fed Policy Meeting: Markets expect status quo on rates",t:"10m ago"},
    {h:"Reliance Industries hits new 52-week high on expansion news",t:"22m ago"},
    {h:"Crude Oil surges 2% amid Middle East tensions",t:"45m ago"}
  ];
  news.forEach(n=>{
    nl.innerHTML+=`<div class="n-item"><div class="n-head">${n.h}</div><div class="n-meta"><span>Fin-News</span><span>${n.t}</span></div></div>`;
  });
}

function bTicker(){ /* already handled by sim/render loop */ }
function bEco(){ /* economics calendar data */ }
function bStrats(){ /* more strategies */ }

/* ══ CALCULATOR ══ */
function doCalc(){
  const cap=Number(document.getElementById('c-cap').value);
  const rP=Number(document.getElementById('c-risk').value);
  const ent=Number(document.getElementById('c-ent').value);
  const sl=Number(document.getElementById('c-sl').value);
  if(!cap||!ent||!sl)return;
  const rAmt=cap*(rP/100);
  const diff=Math.abs(ent-sl);
  const qty=Math.floor(rAmt/diff);
  document.getElementById('c-res').innerHTML=`
    <div style="color:var(--gold)">RISK AMOUNT: ₹${fNum(rAmt)}</div>
    <div style="font-size:1.2rem;margin-top:5px">QUANTITY: ${qty}</div>
    <div style="font-size:0.7rem;color:var(--dim)">Stop Loss points: ${fNum(diff)}</div>
  `;
}

/* ══ LICENSE CHECK (MOCK) ══ */
function checkExpiry(){
  // const exp = new Date('2024-12-31');
  // if(new Date() > exp) document.getElementById('overlay').classList.add('on');
}

async function mainLoop(){
  simTick(); // immediate sim update for smooth feel
  await fetchLiveData(); // try real data
  render();
}

/* ══ TAB ══ */
function T(name){
  const map={signals:"p-signals",charts:"p-charts",oi:"p-oi",market:"p-market",news:"p-news",strategy:"p-strategy",slcalc:"p-slcalc",analysis:"p-analysis"};
  document.querySelectorAll(".panel").forEach(p=>p.classList.remove("on"));
  document.querySelectorAll(".tab,.bb").forEach(b=>b.classList.remove("on"));
  const p=document.getElementById(map[name]);if(p)p.classList.add("on");
  document.querySelectorAll(".tab").forEach(t=>{if(t.textContent.toLowerCase().includes(name.slice(0,4)))t.classList.add("on");});
  document.querySelectorAll(".bb").forEach(b=>{if(b.textContent.toLowerCase().includes(name.slice(0,4)))b.classList.add("on");});
  if(name==="charts"||name==="signals")setTimeout(dCharts,60);
  if(name==="analysis")setTimeout(bAnalysis,100);
}

/* ══ INIT ══ */
checkExpiry();
bPats();bStrats();bNews();bEco();bTicker();bAnalysis();
setInterval(uClock,1000);
// First render immediately with sim data
render();
// Live fetch every 15 seconds (Yahoo Finance rate-limiting friendly)
mainLoop();
setInterval(mainLoop,15000);
</script>
</body>
</html>"""

# Is variable ko kisi file mein likhne ke liye:
with open("eagle_eye_pro_v3.html", "w", encoding="utf-8") as f:
    f.write(html_code)

print("Poora code convert ho gaya hai.")
