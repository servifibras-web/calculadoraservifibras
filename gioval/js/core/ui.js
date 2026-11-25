"use strict";
/* ============ INTERFAZ GENERAL: pantallas, mapa de islas, menú de isla, logros, arranque ============ */
const MENUS=["who","map","menuIsla"]; /* pantallas donde puede aparecer el aviso de versión nueva (nunca en sesión ni actividad) */
function show(id){ document.querySelectorAll(".screen").forEach(s=>s.classList.toggle("active",s.id===id)); if(Gioval.actualizacion) Gioval.actualizacion.revisar(); }
$("btnLogrosBack").onclick=()=>goMenuIsla();
$("btnMenuBack").onclick=()=>goMap();
$("btnWho").onclick=()=>{ renderWho(); show("who"); setBubble("¿Quién juega?"); };
function renderMap(){
  $("mapTitle").textContent="Mundo Gioval · ¡A jugar, "+KID+"!";
  const box=$("islands"); box.innerHTML="";
  const islas=[
    ...PACKS.map(p=>({name:p.name,emoji:p.emoji,sub:p.sub,on:true,go:()=>{ PACK=p; goMenuIsla(); speak("¡"+p.name+"! Empezamos con la sesión de hoy, o elegí otra cosa."); }})),
    ...(Gioval.datos.proximas||[]).map(p=>({name:p.name,emoji:p.emoji,sub:p.sub,on:false})),
  ];
  islas.forEach(is=>{
    const b=document.createElement("button"); b.className="island"+(is.on?"":" off");
    b.innerHTML=`<div class="em">${is.on?is.emoji:"🔒"}</div>${is.name}<small>${is.sub}</small>`;
    if(is.on) b.onclick=()=>{ ensureCtx(); is.go(); }
    box.appendChild(b);
  });
}
function goMap(){ S.run++; S.tap=null; Gioval.emit("mapa"); show("map"); renderMap(); setBubble("¡Hola "+KID+"! ¿A qué isla vamos?"); }
function renderWho(){
  const box=$("profiles"); box.innerHTML="";
  store.profiles.forEach(n=>{
    const b=document.createElement("button"); b.className="song"; b.innerHTML=`<div style="font-size:48px">🦊</div>${n}`;
    b.onclick=()=>{ ensureCtx(); KID=n; goMap(); speak("¡Hola "+KID+"! Mundo Gioval, ¡a jugar! ¿A qué isla vamos?"); }; box.appendChild(b);
  });
  const nb=document.createElement("button"); nb.className="song"; nb.innerHTML=`<div style="font-size:48px">➕</div>Nuevo jugador`;
  nb.onclick=()=>{ $("nameBox").classList.add("show"); $("nameIn").value=""; setTimeout(()=>$("nameIn").focus(),50); }; box.appendChild(nb);
}
$("nameOk").onclick=()=>{
  const n=$("nameIn").value.trim().slice(0,14); if(!n) return;
  if(!store.profiles.includes(n)){ store.profiles.push(n); save(); }
  $("nameBox").classList.remove("show"); ensureCtx(); KID=n; goMap(); speak("¡Hola "+KID+"! Mundo Gioval, ¡a jugar!");
};
$("nameIn").addEventListener("keydown",e=>{ if(e.key==="Enter") $("nameOk").click(); });
$("btnVoice").onclick=()=>{ voiceOn=!voiceOn; $("btnVoice").textContent=voiceOn?"🔊":"🔇"; if(!voiceOn){try{speechSynthesis.cancel();}catch(e){}} };
$("btnFinOk").onclick=()=>{ $("finish").classList.remove("show");
  if(S.finMode==="session"){ resetFlow(); (PACK.fin&&PACK.fin.okFn||goMenuIsla)(); return; }
  if(S.finOk) S.finOk(); };
$("btnFinHome").onclick=()=>{ $("finish").classList.remove("show");
  if(S.finMode==="session"){ resetFlow(); (PACK.fin&&PACK.fin.homeFn||goMap)(); return; }
  if(S.finHome) S.finHome(); };
function goMenuIsla(){ S.run++; S.tap=null; Gioval.emit("menu",PACK); show("menuIsla"); renderMenuIsla(); setBubble("¡"+PACK.name+"! ¿Qué hacemos?"); }
function renderMenuIsla(){
  $("menuIslaTitle").textContent=PACK.emoji+" "+PACK.name;
  const left=capLeft(); $("streak").textContent="⏱ "+(left>0?Math.ceil(left/60)+" min":"listo por hoy");
  const box=$("menuIslaItems"); box.innerHTML="";
  const done=left<=0, ci=checkInfo();
  const cards=[
    {em:"▶️",t:"Sesión de hoy",s:done?"Mañana seguimos 🌙":sessionPreview(),on:!done,go:()=>startSession()},
    ...(PACK.tarjetas?PACK.tarjetas(done):[]),
    ...(Gioval.tarjetasMenu||[]).flatMap(f=>f(done)||[]), /* gancho genérico: módulos opcionales suman tarjetas a todos los menús */
    {em:"🌟",t:"Mis logros",s:"Mirá todo lo que aprendiste",on:true,go:()=>{ show("logros"); renderLogros(); }},
    {em:"🧪",t:"Chequeo semanal",s:done&&ci.ok?"Mañana seguimos 🌙":ci.sub,on:ci.ok&&!done,go:()=>startCheck()},
  ];
  cards.forEach(c=>{ const b=document.createElement("button"); b.className="island"+(c.on?"":" off"); b.innerHTML=`<div class="em">${c.on?c.em:(c.em==="🌟"?c.em:"🔒")}</div>${c.t}<small>${c.s}</small>`; if(c.on) b.onclick=()=>{ ensureCtx(); c.go(); }; box.appendChild(b); });
}
function renderLogros(){
  const box=$("skillList"); box.innerHTML="";
  PACK.skills.forEach(s=>{
    const st=SK(s.id), open=s.req.every(mastered);
    const pct=st.mast?100:Math.round(Math.min(1,st.att/6)*st.score*100);
    const d=document.createElement("div"); d.className="skill"+(open?"":" lock");
    d.innerHTML=`<div class="em">${open?s.icon:"🔒"}</div><div style="flex:1">${s.name}<small>${st.mast?"⭐ ¡Dominado!":(open?"Practicando…":"Se abre al dominar lo anterior")}</small><div class="bar2"><i style="width:${open?pct:0}%"></i></div></div>`;
    box.appendChild(d);
  });
}

/* ---- aviso de versión nueva: solo en los menús ---- */
Gioval.actualizacion = {
  pendiente: false, reg: null, aplicando: false,
  revisar(){
    const a=document.querySelector(".screen.active"), el=$("avisoVersion"); if(!el) return;
    el.classList.toggle("show", !!(this.pendiente && a && MENUS.includes(a.id) && !document.querySelector(".big.show")));
  },
  aplicar(){ const w=this.reg&&this.reg.waiting; this.aplicando=true; if(w) w.postMessage({tipo:"saltar"}); else location.reload(); },
};
$("btnActualizar").onclick=()=>Gioval.actualizacion.aplicar();
setInterval(()=>Gioval.actualizacion.revisar(),1500);
function registrarSW(){
  if(!("serviceWorker" in navigator)) return;
  const A=Gioval.actualizacion;
  navigator.serviceWorker.register("sw.js").then(reg=>{
    A.reg=reg;
    const marca=()=>{ if(reg.waiting&&navigator.serviceWorker.controller){ A.pendiente=true; A.revisar(); } };
    marca();
    reg.addEventListener("updatefound",()=>{ const n=reg.installing; if(n) n.addEventListener("statechange",()=>{ if(n.state==="installed") marca(); }); });
    setInterval(()=>reg.update().catch(()=>{}),30*60*1000);
    document.addEventListener("visibilitychange",()=>{ if(!document.hidden) reg.update().catch(()=>{}); });
  }).catch(()=>{});
  let recargando=false;
  navigator.serviceWorker.addEventListener("controllerchange",()=>{ if(recargando||!A.aplicando) return; recargando=true; location.reload(); });
}
/* ============ ARRANQUE ============ */
Gioval.arrancar = async function(){
  await Gioval.almacen.cargar();
  Gioval.islas.montar();
  PACK=PACKS[0];
  renderWho(); show("who");
  if(!store.profiles.length) $("nameBox").classList.add("show");
  registrarSW();
  Gioval.listo=true;
};
