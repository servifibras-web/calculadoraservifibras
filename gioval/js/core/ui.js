"use strict";
/* ============ INTERFAZ GENERAL: pantallas, mapa de islas, menú de isla, logros, arranque ============ */
const MENUS=["who","map","menuIsla"]; /* pantallas donde puede aparecer el aviso de versión nueva (nunca en sesión ni actividad) */
function show(id){ document.querySelectorAll(".screen").forEach(s=>s.classList.toggle("active",s.id===id)); if(Gioval.actualizacion) Gioval.actualizacion.revisar(); }
$("btnLogrosBack").onclick=()=>goMenuIsla();
$("btnMenuBack").onclick=()=>goMap();
$("btnWho").onclick=()=>{ Gioval.i18n.usar(Gioval.i18n.delAparato()); renderWho(); show("who"); setBubble(t("app.quien_juega")); };
/* el idioma de cada jugador se guarda en store.idioma; si no eligió, vale el del aparato */
function usarIdiomaDeJugador(){ Gioval.i18n.usar(((store.idioma||{})[KID])||Gioval.i18n.delAparato()); }
/* al cambiar el idioma se redibuja la pantalla que está a la vista */
Gioval.on("idioma",d=>{
  if(!d||!d.cambio) return;
  const a=document.querySelector(".screen.active");
  if(a){
    if(a.id==="who"){ renderWho(); setBubble(t("app.quien_juega")); }
    else if(a.id==="map"){ renderMap(); setBubble(t("app.hola_mapa",{nombre:KID})); }
    else if(a.id==="menuIsla"){ renderMenuIsla(); setBubble(t("app.isla_menu",{isla:PACK.name})); }
    else if(a.id==="logros") renderLogros();
  }
  if($("panel").classList.contains("show")) renderParent();
  if(Gioval.voz) Gioval.voz.configurar();
});
function renderMap(){
  $("mapTitle").textContent=t("app.mapa_titulo",{nombre:KID});
  const box=$("islands"); box.innerHTML="";
  const islas=[
    ...PACKS.map(p=>({name:p.name,emoji:p.emoji,sub:p.sub,on:true,go:()=>{ PACK=p; goMenuIsla(); speak(p.hablaMenu?p.hablaMenu():t("app.isla_entrada",{isla:p.name})); }})),
    ...(Gioval.datos.proximas||[]).map(p=>({name:p.name,emoji:p.emoji,sub:p.sub,on:false})),
  ];
  islas.forEach(is=>{
    const b=document.createElement("button"); b.className="island"+(is.on?"":" off");
    b.innerHTML=`<div class="em">${is.on?is.emoji:"🔒"}</div>${is.name}<small>${is.sub}</small>`;
    if(is.on) b.onclick=()=>{ ensureCtx(); is.go(); }
    box.appendChild(b);
  });
}
function goMap(){ S.run++; S.tap=null; Gioval.emit("mapa"); show("map"); renderMap(); setBubble(t("app.hola_mapa",{nombre:KID})); }
function renderWho(){
  const box=$("profiles"); box.innerHTML="";
  store.profiles.forEach(n=>{
    const b=document.createElement("button"); b.className="song"; b.innerHTML=`<div style="font-size:48px">🦊</div>${n}`;
    b.onclick=()=>{ ensureCtx(); KID=n; usarIdiomaDeJugador(); goMap(); speak(t("app.hola_entrada",{nombre:KID})); }; box.appendChild(b);
  });
  const nb=document.createElement("button"); nb.className="song"; nb.innerHTML=`<div style="font-size:48px">➕</div>${t("app.nuevo_jugador")}`;
  nb.onclick=()=>{ $("nameBox").classList.add("show"); $("nameIn").value=""; setTimeout(()=>$("nameIn").focus(),50); }; box.appendChild(nb);
}
$("nameOk").onclick=()=>{
  const n=$("nameIn").value.trim().slice(0,14); if(!n) return;
  if(!store.profiles.includes(n)){ store.profiles.push(n); save(); }
  $("nameBox").classList.remove("show"); ensureCtx(); KID=n; usarIdiomaDeJugador(); goMap(); speak(t("app.hola_nuevo",{nombre:KID}));
};
$("nameIn").addEventListener("keydown",e=>{ if(e.key==="Enter") $("nameOk").click(); });
$("btnVoice").onclick=()=>{ voiceOn=!voiceOn; $("btnVoice").textContent=voiceOn?"🔊":"🔇"; if(!voiceOn){try{speechSynthesis.cancel();}catch(e){}} };
$("btnFinOk").onclick=()=>{ $("finish").classList.remove("show");
  if(S.finMode==="session"){ resetFlow(); (PACK.fin&&PACK.fin.okFn||goMenuIsla)(); return; }
  if(S.finOk) S.finOk(); };
$("btnFinHome").onclick=()=>{ $("finish").classList.remove("show");
  if(S.finMode==="session"){ resetFlow(); (PACK.fin&&PACK.fin.homeFn||goMap)(); return; }
  if(S.finHome) S.finHome(); };
function goMenuIsla(){ S.run++; S.tap=null; Gioval.emit("menu",PACK); show("menuIsla"); renderMenuIsla(); setBubble(t("app.isla_menu",{isla:PACK.name})); }
function renderMenuIsla(){
  $("menuIslaTitle").textContent=PACK.emoji+" "+PACK.name;
  const left=capLeft(); $("streak").textContent=PACK.etiquetaTiempo?PACK.etiquetaTiempo():(left>0?t("menu.tiempo",{n:Math.ceil(left/60)}):t("menu.listo_hoy"));
  const box=$("menuIslaItems"); box.innerHTML="";
  const done=left<=0, ci=checkInfo();
  /* una isla sin sesiones (p. ej. Misiones, que no cuenta como pantalla) declara menuPropio():[{em,t,s,on,go}], etiquetaTiempo() y hablaMenu() */
  const cards=PACK.menuPropio?PACK.menuPropio():[
    {em:"▶️",t:t("menu.sesion"),s:done?t("menu.manana"):sessionPreview(),on:!done,go:()=>startSession()},
    ...(PACK.tarjetas?PACK.tarjetas(done):[]),
    ...(Gioval.tarjetasMenu||[]).flatMap(f=>f(done)||[]), /* gancho genérico: módulos opcionales suman tarjetas a todos los menús */
    {em:"🌟",t:t("menu.logros"),s:t("menu.logros_sub"),on:true,go:()=>{ show("logros"); renderLogros(); }},
    {em:"🧪",t:t("menu.chequeo"),s:done&&ci.ok?t("menu.manana"):ci.sub,on:ci.ok&&!done,go:()=>startCheck()},
  ];
  cards.forEach(c=>{ const b=document.createElement("button"); b.className="island"+(c.on?"":" off"); b.innerHTML=`<div class="em">${c.on?c.em:(c.em==="🌟"?c.em:"🔒")}</div>${c.t}<small>${c.s}</small>`; if(c.on) b.onclick=()=>{ ensureCtx(); c.go(); }; box.appendChild(b); });
}
function renderLogros(){
  const box=$("skillList"); box.innerHTML="";
  PACK.skills.forEach(s=>{
    const st=SK(s.id), open=s.req.every(mastered);
    const pct=st.mast?100:Math.round(Math.min(1,st.att/6)*st.score*100);
    const d=document.createElement("div"); d.className="skill"+(open?"":" lock");
    d.innerHTML=`<div class="em">${open?s.icon:"🔒"}</div><div style="flex:1">${s.name}<small>${st.mast?(st.skip&&st.skip.estado==="pendiente"?t("dominio.ya_sabias"):t("menu.dominado")):(open?t("menu.practicando"):t("menu.bloqueado"))}</small><div class="bar2"><i style="width:${open?pct:0}%"></i></div></div>`;
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
  Gioval.i18n.usar(Gioval.i18n.delAparato());
  if(Gioval.i18n.actual!=="es-AR") setBubble(t("app.burbuja"));
  Gioval.voz.configurar();
  PACK=PACKS[0];
  renderWho(); show("who");
  if(!store.profiles.length) $("nameBox").classList.add("show");
  registrarSW();
  Gioval.listo=true;
};
