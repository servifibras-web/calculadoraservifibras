"use strict";
/* ============ VOZ ============
   Cadena de voz (de mejor a peor; cada escalón cae al siguiente si falla o no existe):
     1. AUDIO GRABADO o pregenerado:  audio/<código>/manifest.json  { textos:{ "frase exacta":"archivo.mp3" }, claves:{ "clave.i18n":"archivo.mp3" } }
        Se usa si la frase (o la clave de la que salió) está en el manifiesto. Sin conexión, el service worker lo tiene en caché
        SOLO para el idioma elegido.
     2. VOZ DEL APARATO (speechSynthesis): se elige la mejor voz según los códigos BCP-47 que declara el idioma
        (meta.voz, en orden de preferencia: "es-AR", "es-419", ... ), prefiriendo las que funcionan sin conexión (localService).
        El adulto puede fijar una voz concreta en "Probar voz" (se guarda en este aparato).
     3. SOLO TEXTO: si el aparato no tiene ninguna voz para el idioma (o el idioma no tiene voz a propósito), la app sigue
        funcionando: se ve el globito con el texto. En la zona de adultos aparece un aviso discreto (Gioval.voz.sinVoz).
   speak(texto) devuelve una promesa que se resuelve cuando termina de "hablar" (o de mostrarse, en solo texto). */
let voiceOn=true, muteUntil=0; /* muteUntil: la escucha del micrófono (si la isla la usa) se silencia mientras habla la app */
const V = Gioval.voz = { nivel:"tts", sinVoz:false, voz:null, manifest:null, codigoManifest:null, elegida:null, audio:null };
function voiceReady(){ return voiceOn&&!!window.speechSynthesis&&V.nivel!=="texto"; }

const CLAVE_VOZ=codigo=>Gioval.clave("gioval_voz_"+codigo);
const norm=l=>String(l||"").replace("_","-").toLowerCase();
function vocesDelAparato(){ try{ return (window.speechSynthesis&&speechSynthesis.getVoices())||[]; }catch(e){ return []; } }
/* voces candidatas del idioma actual, en orden de preferencia */
function candidatas(){
  const vs=vocesDelAparato(), pref=(Gioval.i18n.meta().voz||[]).map(norm), out=[];
  const poner=v=>{ if(!out.includes(v)) out.push(v); };
  pref.forEach(l=>{
    const exactas=vs.filter(v=>norm(v.lang)===l).sort((a,b)=>(b.localService?1:0)-(a.localService?1:0));
    exactas.forEach(poner);
    if(!l.includes("-")){ vs.filter(v=>norm(v.lang).split("-")[0]===l).sort((a,b)=>(b.localService?1:0)-(a.localService?1:0)).forEach(poner); }
  });
  /* mismo idioma base aunque la región no esté en la lista (p. ej. es-CL cuando se pidió es-AR) */
  pref.forEach(l=>{ const b=l.split("-")[0]; vs.filter(v=>norm(v.lang).split("-")[0]===b).sort((a,b2)=>(b2.localService?1:0)-(a.localService?1:0)).forEach(poner); });
  return out;
}
/* elige la voz y calcula el nivel de la cadena para el idioma actual */
V.configurar=function(){
  const meta=Gioval.i18n.meta(), codigo=Gioval.i18n.actual;
  const cand=candidatas(), vs=vocesDelAparato();
  let guardada=null; try{ guardada=localStorage.getItem(CLAVE_VOZ(codigo)); }catch(e){}
  V.elegida=guardada;
  V.voz=(guardada&&vs.find(v=>v.voiceURI===guardada))||cand[0]||null;
  const hayGrabado=!!(V.manifest&&V.codigoManifest===codigo&&V.cantidadAudios()>0);
  if(hayGrabado) V.nivel="grabado";
  else if(meta.sinVoz||!window.speechSynthesis) V.nivel="texto";
  else if(!vs.length) V.nivel="tts";                 /* el aparato todavía no cargó la lista: se intenta igual */
  else V.nivel=V.voz?"tts":"texto";
  V.sinVoz=V.nivel==="texto";
  V.avisarSW(codigo);
  Gioval.emit("voz",V);
  V.cargarManifest(codigo);                            /* asíncrono: si aparece audio, se vuelve a configurar */
};
V.cantidadAudios=()=>V.manifest?Object.keys(V.manifest.textos||{}).length+Object.keys(V.manifest.claves||{}).length:0;
V._pedido=null;
V.cargarManifest=function(codigo){
  if(V.codigoManifest===codigo||V._pedido===codigo) return;
  V.manifest=null; V.codigoManifest=null;
  if(!Gioval.i18n.meta(codigo).audio){ V.codigoManifest=codigo; return; }   /* solo los idiomas con meta.audio:true tienen carpeta audio/<código>/ */
  V._pedido=codigo;
  fetch("audio/"+codigo+"/manifest.json",{cache:"no-cache"}).then(r=>r.ok?r.json():null).catch(()=>null).then(m=>{
    V._pedido=null; if(Gioval.i18n.actual!==codigo) return;
    if(m&&(m.textos||m.claves)){ V.manifest=m; V.codigoManifest=codigo; V.configurar(); }
    else V.codigoManifest=codigo;                         /* se sabe que no hay: no se vuelve a pedir */
  });
};
/* el service worker guarda en caché el audio de ESTE idioma y borra el de los demás */
V.avisarSW=function(codigo){
  try{
    const urls=V.manifest&&V.codigoManifest===codigo?[...new Set(Object.values(V.manifest.textos||{}).concat(Object.values(V.manifest.claves||{})))].map(f=>"audio/"+codigo+"/"+f).concat(["audio/"+codigo+"/manifest.json"]):[];
    if(navigator.serviceWorker&&navigator.serviceWorker.controller) navigator.serviceWorker.controller.postMessage({tipo:"audio",codigo,urls});
  }catch(e){}
};
function archivoGrabado(text){
  const m=V.manifest; if(!m||V.codigoManifest!==Gioval.i18n.actual) return null;
  const f=(m.textos&&m.textos[text])||(m.claves&&m.claves[Gioval.i18n.claveDe(text)]);
  return f?"audio/"+Gioval.i18n.actual+"/"+f:null;
}
if(window.speechSynthesis){ speechSynthesis.onvoiceschanged = ()=>{ V.configurar(); }; }
function setBubble(t){ $("bubble").textContent = t; }

function hablarTTS(text,est){
  return new Promise(res=>{
    let done=false; const fin=()=>{ if(!done){done=true; muteUntil=performance.now()+350; res();} };
    try{
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = V.voz?V.voz.lang:((Gioval.i18n.meta().voz||["es-AR"])[0]||"es-AR"); if(V.voz) u.voice=V.voz;
      u.rate=.92; u.pitch=1.25;
      u.onend=fin; u.onerror=fin;
      speechSynthesis.speak(u);
    }catch(e){ fin(); }
    setTimeout(fin, est+1500);
  });
}
function reproducir(url,text,est){
  return new Promise(res=>{
    let done=false; const fin=ok=>{ if(!done){done=true; muteUntil=performance.now()+350; res(ok);} };
    try{
      try{ speechSynthesis&&speechSynthesis.cancel(); }catch(e){}
      if(V.audio){ try{ V.audio.pause(); }catch(e){} }
      const a=V.audio=new Audio(url); a.onended=()=>fin(true); a.onerror=()=>fin(false);
      const p=a.play(); if(p&&p.catch) p.catch(()=>fin(false));
    }catch(e){ fin(false); }
    setTimeout(()=>fin(true), est+4000);
  }).then(ok=>ok?undefined:(window.speechSynthesis&&V.nivel!=="texto"?hablarTTS(text,est):undefined));
}
function speak(text){
  setBubble(text);
  const est = 500 + text.length*85;
  muteUntil = performance.now() + est + 400;
  if(!voiceOn) return sleep(Math.min(est,1400));
  const grabado=archivoGrabado(text);
  if(grabado) return reproducir(grabado,text,est);
  if(!window.speechSynthesis||V.nivel==="texto") return sleep(Math.min(est,1400));
  return hablarTTS(text,est);
}
