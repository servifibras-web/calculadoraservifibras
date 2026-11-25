"use strict";
/* ============ ZONA DE ADULTOS: candado, panel, informe, tiempo diario, respaldo ============ */
/* ---- Informe verificable (para papá y la profesora) ---- */
function reportText(){
  const lines=[], ds=store.days[KID]||[], log=store.log[KID]||[];
  const mins=Math.round(Object.entries(store.time).filter(([k])=>k.startsWith(KID+"|")).reduce((a,[,v])=>a+v,0)/60);
  const loc=Gioval.i18n.meta().locale;
  lines.push(t("informe.titulo",{nombre:KID.toLocaleUpperCase(loc)}), Gioval.i18n.fecha(new Date()),
    t("informe.dias",{dias:ds.length,min:mins}), "");
  const pc=a=>a.length?Math.round(100*a.filter(Boolean).length/a.length)+"% (n="+a.length+")":"–";
  let lastPk=null;
  Gioval.islas.habilidades().forEach(s=>{
    const ev=log.filter(e=>e.s===s.id&&e.k!=="check"), st=SK(s.id); if(!ev.length&&!st.mast) return;
    const pk=PACKS.find(p=>p.skills.includes(s)); if(pk&&pk!==lastPk){ lines.push(pk.emoji+" "+pk.name.toLocaleUpperCase(loc)); lastPk=pk; }
    const first=ev.map(e=>e.f), ret=ev.filter(e=>e.g>=1).map(e=>e.o);
    lines.push(t("informe.hab",{nombre:s.name,estado:st.mast?"dominado":"practica"}));
    lines.push(t("informe.primeros",{a:pc(first.slice(0,5)),b:pc(first.slice(-5))}));
    lines.push(t("informe.retencion",{r:pc(ret)}));
  });
  PACKS.forEach(p=>{ if(!p.informe) return; const l=p.informe(KID); if(l&&l.length) lines.push("", ...l); });   /* gancho opcional: cada isla puede sumar sus propias líneas */
  const ck=store.checks[KID]||[];
  lines.push("", t("informe.chequeos"));
  if(!ck.length) lines.push(t("informe.sin_chequeos"));
  ck.slice(-12).forEach(c=>{ const pk=PACKS.find(x=>x.id===c.p); lines.push(t("informe.chequeo_linea",{fecha:c.d,isla:pk?pk.name:"",ok:c.ok,n:c.n,pct:Math.round(100*c.ok/c.n)})); });
  lines.push("", t("informe.pie",{notas:Gioval.islas.notasInforme()}));
  return lines.join("\n");
}
function renderParent(){
  const ds=store.days[KID]||[];
  const used=Math.round((store.time[KID+"|"+today()]||0)/60);
  let h=KID?t("adultos.resumen",{nombre:KID,dias:ds.length,usados:used,limite:store.limit[KID]||15})+"<br>":"";
  Gioval.islas.habilidades().forEach(s=>{ if(!KID) return; const st=SK(s.id); if(st.att||st.mast) h+=t("adultos.hab_linea",{emoji:(PACKS.find(p=>p.skills.includes(s))||{}).emoji||"",nombre:s.name,estado:st.mast?"dominado":"practica",pct:Math.round(st.score*100),n:st.att,nivel:st.lvl})+"<br>"; });
  $("parentSum").innerHTML=h||"";
  if(KID) $("limSel").value=String(store.limit[KID]||15);
  renderRespaldo(); renderIdioma();
  $("skipSel").innerHTML=PACKS.flatMap(p=>p.skills.map(s=>`<option value="${s.id}">${p.emoji} ${s.name}</option>`)).join("");
  Gioval.emit("panel"); /* gancho genérico: módulos opcionales redibujan su sección del panel */
}
function markKnown(id){
  const mark=sid=>{ const s=Gioval.islas.habilidades().find(x=>x.id===sid); s.req.forEach(mark); const st=SK(sid); st.mast=true; st.att=Math.max(st.att,6); st.score=Math.max(st.score,.9); st.box=Math.max(st.box,1); st.due=Date.now()+DAY; };
  mark(id); save(); renderParent();
}
$("skipBtn").onclick=()=>{ if(!KID) return; markKnown($("skipSel").value); setBubble(t("adultos.marcado")); };
/* candado para adultos */
function gate(cb){
  const a=3+Math.floor(Math.random()*6), b=3+Math.floor(Math.random()*6);
  S.gateAns=a*b; S.gateCb=cb; $("gateQ").textContent=t("adultos.pregunta_mult",{a,b});
  $("gateIn").value=""; $("gateBox").classList.add("show"); setTimeout(()=>$("gateIn").focus(),50);
}
$("gateOk").onclick=()=>{ if(+$("gateIn").value===S.gateAns){ $("gateBox").classList.remove("show"); const cb=S.gateCb; S.gateCb=null; if(cb) cb(); } else { $("gateIn").value=""; $("gateQ").textContent=t("adultos.pregunta_otra"); } };
$("gateNo").onclick=()=>$("gateBox").classList.remove("show");
$("gateIn").addEventListener("keydown",e=>{ if(e.key==="Enter") $("gateOk").click(); });
$("btnGear").onclick=()=>{
  if($("panel").classList.contains("show")){ $("panel").classList.remove("show"); return; }
  gate(()=>{ renderParent(); $("panel").classList.add("show"); });
};
$("limSel").onchange=()=>{ if(!KID) return; store.limit[KID]=+$("limSel").value; save(); renderParent(); setBubble(t("adultos.limite_ok",{n:$("limSel").value})); if($("menuIsla").classList.contains("active")) renderMenuIsla(); };
$("btnExtra").onclick=()=>{ if(!KID) return; const k=KID+"|"+today(); store.extra[k]=(store.extra[k]||0)+900; save(); renderParent(); setBubble(t("adultos.extra_ok")); if($("menuIsla").classList.contains("active")) renderMenuIsla(); };
$("btnReport").onclick=()=>{ if(!KID) return; $("reportTxt").textContent=reportText(); $("reportBox").classList.add("show"); };
$("repClose").onclick=()=>$("reportBox").classList.remove("show");
$("repCopy").onclick=async()=>{ try{ await navigator.clipboard.writeText(reportText()); $("repCopy").textContent=t("adultos.copiado"); setTimeout(()=>$("repCopy").textContent=t("adultos.copiar"),1500); }catch(e){ $("repCopy").textContent=t("adultos.copiar_manual"); } };
$("repWa").onclick=()=>{ window.open("https://wa.me/?text="+encodeURIComponent(reportText()),"_blank"); };

/* ---- respaldo: exportar / restaurar ---- */
function renderRespaldo(){
  const A=Gioval.almacen, u=A.ultimoRespaldo();
  let h=t("respaldo.info",{fecha:u?Gioval.i18n.fecha(new Date(u)):t("respaldo.nunca"),version:self.GIOVAL_VERSION,almacenamiento:A.persistente?t("respaldo.protegido"):t("respaldo.normal")});
  if(A.debeRecordar()) h+=t("respaldo.recordar");
  if(A.errorMigracion) h+=t("respaldo.error_migracion");
  $("respaldoInfo").innerHTML=h;
}
let restauracionPendiente=null;
$("btnExport").onclick=()=>{ Gioval.almacen.exportar(); renderRespaldo(); setBubble(t("respaldo.descargado")); };
$("btnRestore").onclick=()=>$("fileRestore").click();
$("fileRestore").onchange=async e=>{
  const f=e.target.files[0]; e.target.value=""; if(!f) return;
  const r=await Gioval.almacen.leerRespaldo(f); restauracionPendiente=r.ok?r.datos:null;
  const box=$("restoreTxt");
  if(!r.ok){ box.textContent=r.error; $("restoreOk").style.display="none"; }
  else {
    const R=r.resumen; $("restoreOk").style.display="";
    box.innerHTML=t("respaldo.vista",{fecha:R.exportado?Gioval.i18n.fechaHora(R.exportado):t("respaldo.sin_fecha"),
      perfiles:R.perfiles.length?R.perfiles.map(p=>t("respaldo.perfil_linea",{nombre:p,dias:R.dias[p],dominadas:R.dominadas[p]})).join("<br>"):t("respaldo.sin_perfiles")});
  }
  $("restoreBox").classList.add("show");
};
$("restoreNo").onclick=()=>{ restauracionPendiente=null; $("restoreBox").classList.remove("show"); };
$("restoreOk").onclick=async()=>{ if(!restauracionPendiente) return; await Gioval.almacen.restaurar(restauracionPendiente); location.reload(); };

/* ---- idioma (por aparato y por jugador) y prueba de voz ---- */
function nombreIdioma(c){ const l=Gioval.i18n.idiomas().find(x=>x.codigo===c); return l?l.nombreNativo:c; }
function renderIdioma(){
  const I=Gioval.i18n, lista=I.idiomas();
  const op=l=>`<option value="${l.codigo}">${l.nombreNativo}${l.prueba?t("idioma.prueba"):""}</option>`;
  $("langDev").innerHTML=lista.map(op).join(""); $("langDev").value=I.delAparato();
  $("langKidLbl").textContent=KID?t("idioma.jugador",{nombre:KID}):"";
  $("langKid").parentElement.style.display=KID?"":"none";
  $("langKid").innerHTML=`<option value="">${t("idioma.igual_aparato")}</option>`+lista.map(op).join(""); $("langKid").value=KID?((store.idioma||{})[KID]||""):"";
  const av=$("vozAviso"); av.style.display=Gioval.voz.sinVoz?"":"none"; av.textContent=Gioval.voz.sinVoz?t("voz.aviso_texto"):"";
}
function idiomaEfectivo(){ const a=document.querySelector(".screen.active"); return (KID&&a&&a.id!=="who"&&(store.idioma||{})[KID])||Gioval.i18n.delAparato(); }
$("langDev").onchange=()=>{ Gioval.i18n.guardarDelAparato($("langDev").value); Gioval.i18n.usar(idiomaEfectivo()); renderIdioma(); setBubble(t("idioma.cambiado",{idioma:nombreIdioma(Gioval.i18n.actual)})); };
$("langKid").onchange=()=>{ if(!KID) return; store.idioma=store.idioma||{}; const v=$("langKid").value; if(v) store.idioma[KID]=v; else delete store.idioma[KID]; save();
  Gioval.i18n.usar(idiomaEfectivo()); renderIdioma(); setBubble(t("idioma.cambiado",{idioma:nombreIdioma(Gioval.i18n.actual)})); };
Gioval.on("voz",()=>{ if($("panel").classList.contains("show")) renderIdioma(); if($("vozBox").classList.contains("show")) renderVozBox(); });

function renderVozBox(){
  const V=Gioval.voz, I=Gioval.i18n, vs=(window.speechSynthesis&&speechSynthesis.getVoices())||[];
  $("vozIdioma").innerHTML=t("voz.idioma",{idioma:nombreIdioma(I.actual)});
  let n;
  if(V.nivel==="grabado") n=t("voz.nivel_grabado",{n:V.cantidadAudios()});
  else if(V.nivel==="texto") n=t("voz.nivel_texto");
  else if(V.voz) n=t("voz.nivel_tts",{voz:V.voz.name,lang:V.voz.lang,local:V.voz.localService?"si":"no"});
  else n=t("voz.nivel_tts_sin_confirmar");
  $("vozNivel").innerHTML=n;
  const sel=$("vozSel"), meta=I.meta(), pref=(meta.voz||[]).map(x=>x.toLowerCase().split("-")[0]);
  const lista=vs.filter(v=>pref.includes(String(v.lang).toLowerCase().replace("_","-").split("-")[0]));
  sel.innerHTML=""; const a=document.createElement("option"); a.value=""; a.textContent=t("voz.automatica"); sel.appendChild(a);
  lista.forEach(v=>{ const o=document.createElement("option"); o.value=v.voiceURI; o.textContent=v.name+" ("+v.lang+(v.localService?"":" · online")+")"; sel.appendChild(o); });
  sel.value=V.elegida&&lista.some(v=>v.voiceURI===V.elegida)?V.elegida:"";
  $("vozNota").textContent=lista.length?"":t("voz.sin_voces");
}
$("btnVozProbar").onclick=()=>{ renderVozBox(); $("vozBox").classList.add("show"); };
$("vozCerrar").onclick=()=>$("vozBox").classList.remove("show");
$("vozSel").onchange=()=>{ const c=Gioval.i18n.actual; try{ if($("vozSel").value) localStorage.setItem(Gioval.clave("gioval_voz_"+c),$("vozSel").value); else localStorage.removeItem(Gioval.clave("gioval_voz_"+c)); }catch(e){} Gioval.voz.configurar(); };
$("vozSonar").onclick=()=>{ ensureCtx(); speak(t("voz.frase_prueba")); };
