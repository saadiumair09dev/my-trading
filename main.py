# Part 1: HTML, CSS aur Basic Structure
full_code = """<!DOCTYPE html>
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
@keyframes pulse{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}
@keyframes slideUp{from{transform:translateY(10px);opacity:0}to{transform:translateY(0);opacity:1}}
@keyframes glow{0%{box-shadow:0 0 5px var(--blue)}50%{box-shadow:0 0 15px var(--blue)}100%{box-shadow:0 0 5px var(--blue)}}
.blink{animation:pulse 1s infinite}.up{color:var(--green)}.dn{color:var(--red)}
header{display:flex;justify-content:space-between;align-items:center;padding:10px 15px;background:var(--card);border-bottom:1px solid var(--border);flex-shrink:0}
.logo{font-family:var(--font);font-weight:700;font-size:1.2rem;color:var(--gold);display:flex;align-items:center;gap:8px}
.logo span{font-size:0.7rem;background:var(--dim2);padding:2px 6px;border-radius:4px;color:var(--blue);border:1px solid var(--border)}
.top-meta{display:flex;gap:15px;font-family:var(--font);font-size:0.85rem}#clock{color:var(--blue)}
#ticker-wrap{background:var(--dim2);border-bottom:1px solid var(--border);height:30px;overflow:hidden;white-space:nowrap;display:flex;align-items:center;flex-shrink:0}
#ticker{display:inline-flex;gap:25px;padding-left:100%;animation:scroll 40s linear infinite}
@keyframes scroll{0%{transform:translateX(0)}100%{transform:translateX(-100%)}}
.t-item{display:flex;gap:6px;font-family:var(--font);font-size:0.85rem}
nav{display:flex;background:var(--card);overflow-x:auto;border-bottom:1px solid var(--border);scrollbar-width:none;flex-shrink:0}
nav::-webkit-scrollbar{display:none}
.tab{padding:12px 18px;white-space:nowrap;cursor:pointer;color:var(--dim);font-weight:600;border-bottom:2px solid transparent;transition:all .2s;text-transform:uppercase;font-size:0.8rem;letter-spacing:0.5px}
.tab.on{color:var(--blue);border-bottom-color:var(--blue);background:rgba(61,155,233,0.05)}
main{flex:1;overflow-y:auto;position:relative;background:radial-gradient(circle at top right, #05162d, var(--bg))}
.panel{display:none;padding:15px;animation:slideUp 0.3s ease-out}.panel.on{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px}
.card{background:rgba(5,15,30,0.7);border:1px solid var(--border);border-radius:8px;padding:15px;position:relative;overflow:hidden;backdrop-filter:blur(5px)}
.card-h{display:flex;justify-content:space-between;margin-bottom:12px;border-bottom:1px solid var(--dim2);padding-bottom:8px}
.card-t{font-weight:700;color:var(--gold);font-size:0.9rem;display:flex;align-items:center;gap:6px}
.sig-row{display:flex;justify-content:space-between;align-items:center;padding:10px;border-bottom:1px solid var(--dim2);font-family:var(--font)}
.sig-row:last-child{border:0}.sig-main{display:flex;flex-direction:column;gap:2px}.sig-sym{font-weight:700;font-size:1.1rem}
.sig-type{font-size:0.75rem;text-transform:uppercase;padding:2px 6px;border-radius:3px;width:fit-content}
.bg-buy{background:rgba(0,212,99,0.15);color:var(--green)}.bg-sell{background:rgba(255,61,61,0.15);color:var(--red)}
.sig-price{text-align:right}.sig-val{font-size:1.1rem;font-weight:700}.sig-time{font-size:0.7rem;color:var(--dim)}
.chart-box{height:320px;width:100%;background:var(--dim2);border-radius:4px;margin-bottom:15px;position:relative;border:1px solid var(--border)}
.m-stat{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--dim2)}
.m-label{color:var(--dim)}.m-val{font-family:var(--font);font-weight:600}
.an-bar-wrap{height:12px;background:#0d2040;border-radius:6px;margin:10px 0;display:flex;overflow:hidden;border:1px solid var(--border)}
.an-bar-buy{background:var(--green);height:100%;transition:width 0.5s}.an-bar-sell{background:var(--red);height:100%;transition:width 0.5s}
.bottom-nav{display:flex;background:var(--card);border-top:1px solid var(--border);flex-shrink:0}
.bb{flex:1;padding:12px;text-align:center;font-size:0.7rem;color:var(--dim);cursor:pointer;display:flex;flex-direction:column;gap:4px;align-items:center}
.bb.on{color:var(--blue);background:rgba(61,155,233,0.05)}
#overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(2,11,24,0.95);z-index:999;display:none;align-items:center;justify-content:center;padding:20px;text-align:center}
#overlay.on{display:flex}.modal{background:var(--card);border:1px solid var(--gold);padding:30px;border-radius:12px;max-width:400px}
</style>
</head>
<body>
<div id="overlay"><div class="modal"><h2>⚠️ ACCESS EXPIRED</h2><p>Your Pro License has expired.</p></div></div>
<div id="app">
  <header><div class="logo">🦅 EAGLE EYE <span>PRO V3</span></div><div class="top-meta"><div id="clock">00:00:00</div></div></header>
  <div id="ticker-wrap"><div id="ticker"></div></div>
  <nav>
    <div class="tab on" onclick="T('signals')">🎯 SIGNALS</div>
    <div class="tab" onclick="T('market')">📊 MARKET</div>
    <div class="tab" onclick="T('charts')">📉 CHARTS</div>
    <div class="tab" onclick="T('analysis')">🔍 ANALYSIS</div>
  </nav>
  <main>
    <div id="p-signals" class="panel on"><div id="sig-list"></div></div>
    <div id="p-market" class="panel"><div id="m-indices"></div></div>
    <div id="p-charts" class="panel"><div class="chart-box"><canvas id="cNifty"></canvas></div></div>
    <div id="p-analysis" class="panel"><div class="an-bar-wrap"><div id="sent-buy" class="an-bar-buy"></div><div id="sent-sell" class="an-bar-sell"></div></div></div>
  </main>
  <div class="bottom-nav"><div class="bb on" onclick="T('signals')">🎯<br>Sigs</div><div class="bb" onclick="T('market')">📊<br>Mkt</div></div>
</div>
"""# Part 2: JavaScript Logic aur File Saving
script_part = """
<script>
let l=null;const symbols=["NIFTY 50","BANK NIFTY","RELIANCE","GOLD"];const data={};
symbols.forEach(s=>{data[s]={p:0,ch:0,h:[]};});
const fNum=(n)=>Number(n).toLocaleString('en-IN',{minimumFractionDigits:2});
const uClock=()=>{document.getElementById('clock').textContent=new Date().toLocaleTimeString();};
function simTick(){
  symbols.forEach(s=>{
    if(data[s].p===0)data[s].p=s.includes("NIFTY")?22000:70000;
    const chg=(Math.random()-0.5)*10;data[s].p+=chg;data[s].ch+=chg;data[s].h.push(data[s].p);
    if(data[s].h.length>50)data[s].h.shift();
  });
}
function render(){
  const t=document.getElementById('ticker');t.innerHTML='';
  symbols.forEach(s=>{t.innerHTML+=`<div class="t-item">${s} <span class="${data[s].ch>=0?'up':'dn'}">${fNum(data[s].p)}</span></div>`;});
  const sl=document.getElementById('sig-list');sl.innerHTML='';
  symbols.forEach(s=>{
    sl.innerHTML+=`<div class="sig-row"><div class="sig-main"><span class="sig-sym">${s}</span></div><div class="sig-val">${fNum(data[s].p)}</div></div>`;
  });
}
function T(name){
  document.querySelectorAll(".panel").forEach(p=>p.classList.remove("on"));
  const p=document.getElementById("p-"+name);if(p)p.classList.add("on");
}
setInterval(()=>{uClock();simTick();render();},1000);
</script>
</body>
</html>"""

# Dono parts ko jod kar save karna
with open("eagle_eye_pro_v3.html", "w", encoding="utf-8") as f:
    f.write(full_code + script_part)

print("Kaam ho gaya! File save ho chuki hai.")
