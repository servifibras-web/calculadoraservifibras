"use strict";
/* ============ ZONA DE ADULTOS: candado, panel, informe, tiempo diario, respaldo ============ */
/* ---- Informe verificable (para papá y la profesora) ---- */
function reportText(){
  const lines=[], ds=store.days[KID]||[], log=store.log[KID]||[];
  const mins=Math.round(Object.entries(store.time).filter(([k])=>k.startsWith(KID+"|")).reduce((a,[,v])=>a+v,0)/60);
  lines.push("INFORME DE "+KID.toUpperCase()+" — Mundo Gioval", new Date().toLocaleDateString("es-AR"),
    "Días practicados: "+ds.length+" · Minutos en la app: "+mins, "");
  const pc=a=>a.length?Math.round(100*a.filter(Boolean).length/a.length)+"% (n="+a.length+")":"–";
  let lastPk=null;
  Gioval.islas.habilidades().forEach(s=>{
    const ev=log.filter(e=>e.s===s.id&&e.k!=="check"), st=SK(s.id); if(!ev.length&&!st.mast) return;
    const pk=PACKS.find(p=>p.skills.includes(s)); if(pk&&pk!==lastPk){ lines.push(pk.emoji+" "+pk.name.toUpperCase()); lastPk=pk; }
    const first=ev.map(e=>e.f), ret=ev.filter(e=>e.g>=1).map(e=>e.o);
    lines.push("• "+s.name+": "+(st.mast?"dominado":"en práctica"));
    lines.push("   Aciertos al primer intento: primeros "+pc(first.slice(0,5))+" → últimos "+pc(first.slice(-5)));
    lines.push("   Retención (acierto ≥1 día después de practicar): "+pc(ret));
  });
  const ck=store.checks[KID]||[];
  lines.push("", "CHEQUEOS SIN AYUDA (1 por semana y por isla)");
  if(!ck.length) lines.push("   (todavía no hizo ninguno)");
  ck.slice(-12).forEach(c=>{ const pk=PACKS.find(x=>x.id===c.p); lines.push("   "+c.d+" · "+(pk?pk.name:"")+": "+c.ok+"/"+c.n+" ("+Math.round(100*c.ok/c.n)+"%)"); });
  lines.push("", "Cómo leerlo: la retención mide si recuerda tras dormir y pasar días; el chequeo semanal se hace sin pistas ni ayuda. "+Gioval.islas.notasInforme());
  return lines.join("\n");
}
function renderParent(){
  const ds=store.days[KID]||[];
  const used=Math.round((store.time[KID+"|"+today()]||0)/60);
  let t=KID?`<b>${KID}</b>: ${ds.length} día(s) jugados · hoy ${used} de ${store.limit[KID]||15} min.<br>`:"";
  Gioval.islas.habilidades().forEach(s=>{ if(!KID) return; const st=SK(s.id); if(st.att||st.mast) t+=`• ${(PACKS.find(p=>p.skills.includes(s))||{}).emoji||""} ${s.name}: ${st.mast?"dominado":"en práctica"} (${Math.round(st.score*100)}% de aciertos, ${st.att} intentos, ayuda nivel ${st.lvl})<br>`; });
  $("parentSum").innerHTML=t||"";
  if(KID) $("limSel").value=String(store.limit[KID]||15);
  renderRespaldo();
  $("skipSel").innerHTML=PACKS.flatMap(p=>p.skills.map(s=>`<option value="${s.id}">${p.emoji} ${s.name}</option>`)).join("");
  Gioval.emit("panel"); /* gancho genérico: módulos opcionales redibujan su sección del panel */
}
function markKnown(id){
  const mark=sid=>{ const s=Gioval.islas.habilidades().find(x=>x.id===sid); s.req.forEach(mark); const st=SK(sid); st.mast=true; st.att=Math.max(st.att,6); st.score=Math.max(st.score,.9); st.box=Math.max(st.box,1); st.due=Date.now()+DAY; };
  mark(id); save(); renderParent();
}
$("skipBtn").onclick=()=>{ if(!KID) return; markKnown($("skipSel").value); setBubble("¡Listo! Marqué eso como ya sabido."); };
/* candado para adultos */
function gate(cb){
  const a=3+Math.floor(Math.random()*6), b=3+Math.floor(Math.random()*6);
  S.gateAns=a*b; S.gateCb=cb; $("gateQ").textContent="Pregunta para adultos: ¿cuánto es "+a+" × "+b+"?";
  $("gateIn").value=""; $("gateBox").classList.add("show"); setTimeout(()=>$("gateIn").focus(),50);
}
$("gateOk").onclick=()=>{ if(+$("gateIn").value===S.gateAns){ $("gateBox").classList.remove("show"); const cb=S.gateCb; S.gateCb=null; if(cb) cb(); } else { $("gateIn").value=""; $("gateQ").textContent="Probá de nuevo 🙂 (solo para adultos)"; } };
$("gateNo").onclick=()=>$("gateBox").classList.remove("show");
$("gateIn").addEventListener("keydown",e=>{ if(e.key==="Enter") $("gateOk").click(); });
$("btnGear").onclick=()=>{
  if($("panel").classList.contains("show")){ $("panel").classList.remove("show"); return; }
  gate(()=>{ renderParent(); $("panel").classList.add("show"); });
};
$("limSel").onchange=()=>{ if(!KID) return; store.limit[KID]=+$("limSel").value; save(); renderParent(); setBubble("Listo: "+$("limSel").value+" minutos por día."); if($("menuIsla").classList.contains("active")) renderMenuIsla(); };
$("btnExtra").onclick=()=>{ if(!KID) return; const k=KID+"|"+today(); store.extra[k]=(store.extra[k]||0)+900; save(); renderParent(); setBubble("¡Sumé 15 minutos más para hoy!"); if($("menuIsla").classList.contains("active")) renderMenuIsla(); };
$("btnReport").onclick=()=>{ if(!KID) return; $("reportTxt").textContent=reportText(); $("reportBox").classList.add("show"); };
$("repClose").onclick=()=>$("reportBox").classList.remove("show");
$("repCopy").onclick=async()=>{ try{ await navigator.clipboard.writeText(reportText()); $("repCopy").textContent="¡Copiado!"; setTimeout(()=>$("repCopy").textContent="Copiar",1500); }catch(e){ $("repCopy").textContent="Seleccioná y copiá"; } };
$("repWa").onclick=()=>{ window.open("https://wa.me/?text="+encodeURIComponent(reportText()),"_blank"); };

/* ---- respaldo: exportar / restaurar ---- */
function renderRespaldo(){
  const A=Gioval.almacen, u=A.ultimoRespaldo();
  let t="Último respaldo: <b>"+(u?new Date(u).toLocaleDateString("es-AR"):"nunca")+"</b> · versión "+self.GIOVAL_VERSION+" · almacenamiento "+(A.persistente?"protegido":"normal");
  if(A.debeRecordar()) t+="<br><b>⚠️ Hace más de 14 días que no hacés un respaldo.</b> Tocá “Exportar respaldo” y guardá el archivo.";
  if(A.errorMigracion) t+="<br><b>⚠️ No se pudo actualizar el formato de los datos.</b> Tus datos originales están a salvo; exportá un respaldo y avisá.";
  $("respaldoInfo").innerHTML=t;
}
let restauracionPendiente=null;
$("btnExport").onclick=()=>{ Gioval.almacen.exportar(); renderRespaldo(); setBubble("¡Respaldo descargado!"); };
$("btnRestore").onclick=()=>$("fileRestore").click();
$("fileRestore").onchange=async e=>{
  const f=e.target.files[0]; e.target.value=""; if(!f) return;
  const r=await Gioval.almacen.leerRespaldo(f); restauracionPendiente=r.ok?r.datos:null;
  const box=$("restoreTxt");
  if(!r.ok){ box.textContent=r.error; $("restoreOk").style.display="none"; }
  else {
    const R=r.resumen; $("restoreOk").style.display="";
    box.innerHTML="<b>Vista previa del respaldo</b><br>Guardado: "+(R.exportado?new Date(R.exportado).toLocaleString("es-AR"):"(sin fecha)")+"<br>"+
      (R.perfiles.length?R.perfiles.map(p=>"• "+p+": "+R.dias[p]+" día(s), "+R.dominadas[p]+" habilidad(es) dominada(s)").join("<br>"):"(sin perfiles)")+
      "<br><br>Esto <b>reemplaza</b> lo que hay hoy en este aparato (se guarda una copia de seguridad antes). ¿Restaurar?";
  }
  $("restoreBox").classList.add("show");
};
$("restoreNo").onclick=()=>{ restauracionPendiente=null; $("restoreBox").classList.remove("show"); };
$("restoreOk").onclick=async()=>{ if(!restauracionPendiente) return; await Gioval.almacen.restaurar(restauracionPendiente); location.reload(); };
