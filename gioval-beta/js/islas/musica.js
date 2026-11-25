"use strict";
/* ============ ISLA MÚSICA ============
   Datos (habilidades, canciones, textos) + juego del piano (teclado en pantalla, demostración, escucha por micrófono).
   Se registra en Gioval.islas; el motor no conoce nada de esta isla. */
(function(){
const COLORS = {C:"#ff5a5f",D:"#ff9f1c",E:"#ffd23f",F:"#4cc86a",G:"#2ec4b6",A:"#4d96ff",B:"#9b5de5"};
const BASE = {C:0,D:2,E:4,F:5,G:7,A:9,B:11};
/* nombre de la nota según el idioma: Do Re Mi (español), C D E (inglés)... */
const noteName = L => Gioval.i18n.nombreNota(BASE[L]);
const WHITE = [60,62,64,65,67,69,71,72,74,76]; // Do4 .. Mi5
const PCLET = {0:"C",2:"D",4:"E",5:"F",7:"G",9:"A",11:"B"};
function parseNote(tok){
  const m = /^([A-G])(\d)(?::([\d.]+))?$/.exec(tok);
  const midi = 12*(+m[2]+1)+BASE[m[1]];
  return {midi, beats: m[3]?parseFloat(m[3]):1};
}
function parsePhrase(s){ return s.trim().split(/\s+/).map(parseNote); }
// Agregá acá las canciones favoritas de Valentino (melodía de una mano, notas Do4–Mi5)
const SONGS = [
  {id:"Estrellita", clave:"estrellita", emoji:"⭐",
   phrases:["C4 C4 G4 G4 A4 A4 G4:2","F4 F4 E4 E4 D4 D4 C4:2","G4 G4 F4 F4 E4 E4 D4:2"],
   order:[0,1,2,2,0,1]},
  {id:"Himno a la Alegría", clave:"himno", emoji:"🎶",
   phrases:["E4 E4 F4 G4 G4 F4 E4 D4","C4 C4 D4 E4 E4:1.5 D4:.5 D4:2","C4 C4 D4 E4 D4:1.5 C4:.5 C4:2"],
   order:[0,1,0,2]},
  {id:"Cumpleaños feliz", clave:"cumple", emoji:"🎂",
   phrases:["G4 G4 A4 G4 C5 B4:2","G4 G4 A4 G4 D5 C5:2"],
   order:[0,1,0,1]},
].map(s=>({id:s.id, emoji:s.emoji, order:s.order, chunks:s.phrases.map(parsePhrase),
  /* id = título original en español: es la clave del progreso guardado (store.stars), NO se traduce */
  get title(){ return t("musica.cancion."+s.clave+".titulo"); }, get sub(){ return t("musica.cancion."+s.clave+".sub"); }}));


/* ---- estado propio de la isla (el motor solo conoce lo genérico de S) ---- */
const mic=Gioval.entrada.proveedores.microfono;
const panelAbierto=()=>{ const p=$("panel"); return !!(p&&p.classList.contains("show")); };
const MIC_OPTS={
  umbral:()=>(+$("sens").value)/1000,
  nivel:r=>{ $("dbgLevel").style.width=Math.min(100,r*600)+"%"; },
  alDetectar:(b,d)=>{ $("dbgNote").textContent=midiName(b)+" ("+b+")"; },
  alEncender:()=>{ $("btnMic").classList.add("on"); setBubble(t("musica.mic.encendido")); },
  alError:()=>{ $("btnMic").classList.remove("on"); setBubble(t("musica.mic.error")); },
  alApagar:()=>{ $("btnMic").classList.remove("on"); mostrarCue(false); pintarVivo(); },
  /* lo que el micrófono "ve" en cada cuadro: alimenta la lectura en vivo del panel de adultos y la señal "te escucho" de los chicos */
  envivo:()=>panelAbierto(),
  diagnostico:v=>{ mostrarCue(!v.silenciado&&S.mode==="play"&&!!document.querySelector("#play.active")); if(panelAbierto()) pintarVivo(); },
  alAfinar:()=>{ pintarAfinacion(); },
};
/* nombre con octava: Do 4 = Do central (midi 60) */
const oct=m=>Math.floor(m/12)-1;
const nombreConOctava=m=>midiName(m)+" "+oct(m);
function mostrarCue(on){
  const c=$("micCue"); if(!c) return;
  if(c.classList.contains("on")!==!!on){ c.classList.toggle("on",!!on); $("btnMic").classList.toggle("oyendo",!!on); if(on) c.textContent=t("musica.cue.escucho"); }
}
const num=(x,d=0)=>x==null?"–":x.toLocaleString(Gioval.i18n.meta().locale,{maximumFractionDigits:d,minimumFractionDigits:d});
function textoDesvio(c){ return Math.abs(c)<5?t("musica.vivo.afinada"):t(c>0?"musica.vivo.aguda":"musica.vivo.grave",{c:Math.abs(c)}); }
/* lectura en vivo del panel: nota, Hz, desvío, octava, volumen contra el mínimo, y el motivo si se ignoró un sonido */
function pintarVivo(){
  const el=$("micVivoNota"); if(!el) return;
  const V=mic.vivo, ahora=performance.now();
  let nota="–", det="", est;
  if(!mic.activo) est=t("musica.vivo.estado.apagado");
  else if(V.silenciado) est=t("musica.vivo.estado.silenciado");
  else est=t("musica.vivo.estado.escuchando");
  if(mic.activo&&V.midi!=null){ nota=nombreConOctava(V.midi); det=t("musica.vivo.detalle",{hz:num(V.hz,1),desvio:textoDesvio(V.cents),oct:oct(V.midi)}); }
  else if(V.ultimaNota&&ahora-V.ultimaNota.t<4000){ const u=V.ultimaNota; nota=nombreConOctava(u.midi); det=t("musica.vivo.ultima",{hz:num(u.hz,1),desvio:textoDesvio(u.cents)}); }
  el.textContent=nota; $("micVivoDet").textContent=det||t("musica.vivo.nada");
  $("micVivoEstado").textContent=est;
  const thr=V.umbral||MIC_OPTS.umbral();
  $("dbgThr").style.left=Math.min(100,thr*600)+"%";
  $("dbgLevelTxt").textContent=t("musica.vivo.volumen",{v:num(V.rms*1000,0),m:num(thr*1000,0)});
  const mo=$("micVivoMotivo"); let txt="";
  if(V.motivo&&ahora-V.motivoT<5000) txt=t("musica.motivo."+V.motivo,{hz:num(V.fueraHz,0)});
  mo.textContent=txt; mo.style.display=txt?"block":"none";
}
const textoAfinacion=()=>{
  const c=mic.afinacion(); let h=Math.abs(c)<1?t("musica.afin.valor0"):t("musica.afin.valor",{c:num(Math.abs(c),0),dir:t(c<0?"musica.afin.grave":"musica.afin.aguda")});
  h+=" "+t(mic.afinacionManual()?"musica.afin.manual":(mic.afinacionAuto()?"musica.afin.auto_si":"musica.afin.auto_no")); return h;
};
function pintarAfinacion(){ const e=$("afinInfo"); if(e){ e.textContent=textoAfinacion(); $("afinAuto").checked=mic.afinacionAuto(); } }
async function calibrarLa(){
  const msg=$("afinMsg"); msg.style.display="block"; msg.textContent=t("musica.afin.esperando"); ensureCtx();
  if(!mic.activo) await mic.iniciar(MIC_OPTS);
  if(!mic.activo){ msg.textContent=t("musica.mic.error"); return; }
  const r=await mic.calibrarLa();
  if(r.ok) msg.textContent=t(Math.abs(r.afinacion)<1?"musica.afin.listo_cero":"musica.afin.listo",{c:num(Math.abs(r.afinacion),0),dir:t(r.afinacion<0?"musica.afin.grave":"musica.afin.aguda")})+(r.limitada?" "+t("musica.afin.limitada"):"");
  else if(r.motivo==="no_es_la") msg.textContent=t("musica.afin.no_es_la",{nota:nombreConOctava(r.escuche)});
  else if(r.motivo==="tiempo") msg.textContent=t("musica.afin.tiempo");
  else if(r.motivo==="sin_nota") msg.textContent=t("musica.afin.sin_nota");
  pintarAfinacion();
}
function midiName(m){ return Gioval.i18n.nombreNota(m); }
Object.assign(S,{song:null,chunks:[],ci:0,ni:0,missPhrase:0,missNote:0,learnIdx:0});
const starsOf=id=>store.stars[KID+"|"+id]||0;

/* ============ TECLADO ============ */
function buildKeyboard(){
  const kb=$("kb"); kb.innerHTML="";
  WHITE.forEach((m,i)=>{
    const L=PCLET[m%12]; const k=document.createElement("div");
    k.className="key"; k.dataset.m=m; k.style.setProperty("--c",COLORS[L]);
    k.innerHTML=`<span>${noteName(L)}</span>`;
    k.addEventListener("pointerdown",e=>{ e.preventDefault(); pressKey(m); });
    kb.appendChild(k);
  });
  // teclas negras decorativas
  [0,1,3,4,5,7,8].forEach(i=>{
    const b=document.createElement("div"); b.className="black";
    const innerW=100-1.6; b.style.left=`calc(8px + (100% - 16px) * ${(i+1)/WHITE.length} - 2.5%)`;
    kb.appendChild(b);
  });
}
function keyEl(midi){ return document.querySelector(`.key[data-m="${midi}"]`) || document.querySelector(`.key[data-m="${midi%12+60}"]`); }
function flash(midi, cls, ms=350){
  const el = (function(){ const exact=document.querySelector(`.key[data-m="${midi}"]`); if(exact) return exact; return [...document.querySelectorAll(".key")].find(k=>(+k.dataset.m)%12===midi%12); })();
  if(!el) return; el.classList.add(cls); setTimeout(()=>el.classList.remove(cls),ms);
}
function pressKey(midi){ Gioval.entrada.proveedores.toque.pulsar({midi}); }


function renderHome(){
  const box=$("songs"); box.innerHTML="";
  SONGS.forEach((s,i)=>{
    const st=starsOf(s.id);
    const b=document.createElement("button"); b.className="song";
    b.innerHTML=`<div style="font-size:44px">${s.emoji}</div>${s.title}<small>${s.sub}</small><div class="st">${"⭐".repeat(st)}${"☆".repeat(3-st)}</div>`;
    b.onclick=()=>startSong(i); box.appendChild(b);
  });
}
function chunk(){ return S.chunks[S.ci]; }
function renderDots(){
  const box=$("dots"); box.innerHTML="";
  const ch=chunk(); if(!ch) return;
  const hide=(S.kind==="ear"||S.kind==="echo")&&!S.reveal;
  ch.forEach((n,i)=>{
    const L=PCLET[n.midi%12]; const d=document.createElement("div");
    const pending=i>=S.ni;
    d.className="dot"+(i<S.ni?" done":"")+(i===S.ni&&S.mode==="play"?" cur":"");
    if(pending&&hide){ d.className+=" q"; d.innerHTML="<span>?</span>"; }
    else if(pending&&S.kind==="find"&&S.hint>=2&&!S.reveal){ d.className+=" neutral"; d.innerHTML=`<span>${noteName(L)}</span>`; }
    else { d.style.background=COLORS[L]; d.innerHTML=`<span>${noteName(L)}</span>`; }
    if(i<S.ni) d.style.background=COLORS[L];
    box.appendChild(d);
  });
  document.querySelectorAll(".key").forEach(k=>k.classList.remove("target"));
  const guide=(!S.kind)||S.reveal||(S.kind==="find"&&S.hint===0);
  if(S.mode==="play"&&guide){ const t=ch[S.ni]; if(t) markTarget(t.midi); }
}
function markTarget(midi){
  const el=[...document.querySelectorAll(".key")].find(k=>+k.dataset.m===midi) || [...document.querySelectorAll(".key")].find(k=>(+k.dataset.m)%12===midi%12);
  if(el) el.classList.add("target");
}
async function demo(notes, run, showKeys=true){
  S.mode="demo";
  const beat=.5;
  for(const n of notes){
    if(run!==S.run) return false;
    muteUntil=performance.now()+n.beats*beat*1000+500;
    if(showKeys) flash(n.midi,"demo",n.beats*beat*1000-40); tone(n.midi,n.beats*beat+.1);
    await sleep(n.beats*beat*1000);
  }
  muteUntil=performance.now()+400;
  return run===S.run;
}
async function startSong(i){
  if(capLeft()<=0) return showCap();
  ensureCtx(); S.check=false; S.capShown=false; S.tap=null;
  S.song=SONGS[i]; S.run++; S.learnIdx=0; S.session=null; S.onDone=null; S.kind=null; S.hint=0; S.reveal=false; $("songTitle").textContent=S.song.emoji+" "+S.song.title;
  show("play"); buildKeyboard(); renderProg();
  await learnPhrase(0, t("musica.cancion.intro",{cancion:S.song.title}));
}
async function learnPhrase(idx, intro){
  const run=S.run; S.learnIdx=idx; S.mode="demo"; S.chunks=[S.song.chunks[idx]]; S.ci=0; S.ni=0; S.missPhrase=0; S.missNote=0; renderDots();
  await speak(intro|| (idx===0?t("musica.frase.primera"):t("musica.frase.siguiente")));
  if(run!==S.run) return;
  if(!(await demo(S.chunks[0],run))) return;
  await speak(t("musica.te_toca")); if(run!==S.run) return;
  S.mode="play"; renderDots(); armMic();
}
async function startFull(){
  const run=S.run; S.mode="demo";
  S.chunks=S.song.order.map(i=>S.song.chunks[i]); S.ci=0; S.ni=0; S.missPhrase=0; S.missNote=0; S.full=true;
  renderDots();
  await speak(t("musica.completa"));
  if(run!==S.run) return; S.mode="play"; renderDots();
}
function stars3(m){ return m===0?3:(m<=3?2:1); }
async function handleInput(midi,src,ev){
  if(S.mode!=="play"||S.tap) return;
  const now=performance.now(); if(now-S.lastWrong<300) return;
  const nt=chunk()[S.ni]; if(!nt) return;
  const anyOct=$("anyOctave").checked;
  let ok = anyOct ? (midi%12===nt.midi%12) : (midi===nt.midi);
  /* micrófono: un piano de casa casi nunca está a 440 exactos. Si la altura medida (con la afinación ya aplicada) cae a menos de
     ~12 cents del borde de la nota que se pidió, cuenta como esa nota: no se castiga al chico por la afinación del piano. */
  if(!ok&&src==="mic"&&ev&&typeof ev.midiFloat==="number"){
    const aj=ev.midiFloat-(ev.afinacion||0)/100;
    let d=Math.abs(aj-nt.midi); if(anyOct){ d=Math.abs(((aj-nt.midi)%12+18)%12-6); }
    if(d<=.62) ok=true;
  }
  /* con "cualquier octava" apagado: la nota correcta en otra octava no es un error, solo se avisa (y no resta estrellas) */
  if(!ok&&src==="mic"&&!anyOct&&midi%12===nt.midi%12){
    S.lastWrong=now; setBubble(t("musica.otra_octava",{nota:noteName(PCLET[nt.midi%12])})); return;
  }
  const run=S.run;
  if(ok){
    S.missNote=0; if(!S.check) flash(nt.midi,"ok",300); S.ni++; renderDots();
    if(S.ni>=chunk().length){
      S.mode="between";
      if(S.onDone){ const cb=S.onDone; cb({miss:S.missPhrase}); return; }
      if(!S.full){
        const st=stars3(S.missPhrase);
        await speak(rnd(tl("musica.elogio",{nombre:KID}))+" "+"⭐".repeat(st)); if(run!==S.run) return;
        if(S.learnIdx+1<S.song.chunks.length) await learnPhrase(S.learnIdx+1);
        else await startFull();
      } else {
        S.ci++; S.ni=0;
        if(S.ci>=S.chunks.length) return finishSong(run);
        S.mode="play"; renderDots();
      }
    }
  } else {
    S.lastWrong=now; S.missPhrase++; S.missNote++;
    if(S.check){ S.mode="between"; const cb=S.onDone; cb({miss:S.missPhrase}); return; }
    flash(midi,"near",450);
    const tn=noteName(PCLET[nt.midi%12]);
    if(S.kind==="ear"||S.kind==="echo"){
      if(S.missNote===2){ S.mode="demo"; await speak(t("musica.escucha_otra")); if(await demo(chunk(),run,false)){ S.mode="play"; renderDots(); } }
      else if(S.missNote>=4){ S.reveal=true; S.missNote=0; renderDots(); setBubble(t("musica.mira_es",{nota:tn})); }
      else setBubble(t("musica.casi_otra"));
    }
    else if(S.missNote===2){ S.reveal=true; renderDots(); setBubble(t("musica.casi_busca",{nota:tn})); await speak(t("musica.casi_proba",{nota:tn})); }
    else if(S.missNote>=4){ S.missNote=0; S.mode="demo"; await speak(t("musica.te_ayudo",{nota:tn})); tone(nt.midi,.8); flash(nt.midi,"demo",700); await sleep(900); if(run===S.run){ S.mode="play"; renderDots(); } }
    else setBubble(t("musica.casi_otra"));
  }
}
async function finishSong(run){
  S.finMode="song";
  S.finOk=()=>{ const i=SONGS.indexOf(S.song); S.full=false; startSong(i); };
  S.finHome=()=>{ S.full=false; $("btnBack").onclick(); };
  $("btnFinOk").textContent=t("motor.fin.otra_vez"); $("btnFinHome").textContent=t("motor.fin.elegir");
  S.mode="done"; const st=stars3(Math.floor(S.missPhrase/2)); // en la canción completa se tolera más
  const prev=starsOf(S.song.id); if(st>prev){ store.stars[KID+"|"+S.song.id]=st; save(); }
  $("finStars").textContent="⭐".repeat(st)+"☆".repeat(3-st);
  $("finTitle").textContent=t("musica.tocaste",{cancion:S.song.title});
  $("finish").classList.add("show");
  await speak(t("musica.bravo",{nombre:KID}));
}

/* ---- habilidades (cadena con req) ---- */
const SK_ALL=[60,62,64,65,67,69,71,72];
/* el nombre de cada habilidad sale de la tabla de idiomas (musica.hab.<id>); el id NO cambia nunca (es la clave del progreso) */
const sk=(id,o)=>Object.defineProperty({id,...o},"name",{get:()=>t("musica.hab."+id),enumerable:true});
const SKILLS_MUSICA=[
  sk("n1",{icon:"🔴🟠🟡",type:"find",notes:[60,62,64],prior:[],req:[]}),
  sk("e1",{icon:"👂",type:"ear",notes:[60,62,64],req:["n1"]}),
  sk("n2",{icon:"🟢🔵",type:"find",notes:[65,67],prior:[60,62,64],req:["n1"]}),
  sk("eco3",{icon:"🔁",type:"echo",len:3,notes:[60,62,64,65,67],req:["e1","n2"]}),
  sk("n3",{icon:"🟣⭐",type:"find",notes:[69,71,72],prior:[60,62,64,65,67],req:["n2"]}),
  sk("e2",{icon:"🎧",type:"ear",notes:SK_ALL,req:["e1","n3"]}),
  sk("eco5",{icon:"🎶",type:"echo",len:5,notes:SK_ALL,req:["eco3","n3"]}),
];
let lastTarget=null;
function pickDistinct(arr){ let x,g=0; do{ x=rnd(arr); g++; }while(arr.length>1&&x===lastTarget&&g<10); lastTarget=x; return x; }

/* tipos de actividad de la isla */
const ACTIVIDADES={
  find:{
    make(s){ const pool=(Math.random()<.35&&s.prior&&s.prior.length)?s.prior:s.notes; return {skill:s,notes:[pickDistinct(pool)]}; },
    async present(it,run,ss){ const nm=noteName(PCLET[it.notes[0]%12]); await speak(rnd(tl("musica.find",{nota:nm}))); return run===S.run; }
  },
  ear:{
    make(s){ return {skill:s,notes:[pickDistinct(s.notes)]}; },
    async present(it,run,ss){ await speak(ss.seen.ear?t("musica.ear_otra"):t("musica.ear_primera")); ss.seen.ear=true;
      if(!(await demo(S.chunks[0],run,false))) return false; setBubble(t("musica.ear_cual")); return true; }
  },
  echo:{
    tolerancia:1, chequeoItems:1,
    make(s){ const seq=[]; let cur=rnd(s.notes); seq.push(cur);
      while(seq.length<s.len){ const i=s.notes.indexOf(cur); const j=Math.max(0,Math.min(s.notes.length-1,i+rnd([-2,-1,1,2]))); cur=s.notes[j]; seq.push(cur); }
      return {skill:s,notes:seq}; },
    async present(it,run,ss){ await speak(ss.seen.echo?t("musica.echo_otra"):t("musica.echo_primera")); ss.seen.echo=true;
      if(!(await demo(S.chunks[0],run,false))) return false; setBubble(t("musica.echo_vos")); return true; }
  }
};


/* cómo se juega un ítem de esta isla: demostración + teclado (el motor llama a jugar) */
async function jugarPiano(run,it,ss){
  const sk=it.skill;
  S.chunks=[it.notes.map(m=>({midi:m,beats:1}))]; S.ci=0; S.ni=0; S.missPhrase=0; S.missNote=0; S.full=false;
  renderProg(); renderDots();
  if(!(await ACTIVIDADES[sk.type].present(it,run,ss))) return;
  if(run!==S.run) return; S.mode="play"; renderDots(); armMic();
}
Object.values(ACTIVIDADES).forEach(a=>{ a.jugar=jugarPiano; });
function armMic(){ /* el micrófono sigue activo si ya se encendió */ }

/* ---- pantallas e interfaz propias (se inyectan en la cáscara al arrancar) ---- */
const DOM={
  pantallas:`
  <div class="screen" id="home">
    <div class="bar"><button class="btn alt" id="btnHomeBack"><span class="arr">⬅</span><span class="lbl" data-i18n="app.isla"> Isla</span></button><h2 style="margin:0" data-i18n="musica.canciones_titulo">🎵 Mis canciones</h2><span style="width:90px"></span></div>
    <div class="songs" id="songs"></div>
  </div>

  <div class="screen juego" id="play">
    <div class="bar">
      <button class="btn alt" id="btnBack"><span class="arr">⬅</span><span class="lbl" data-i18n="app.volver"> Volver</span></button>
      <div style="font-weight:800;font-size:clamp(18px,2.8vw,26px)" id="songTitle"></div>
      <div style="display:flex;gap:8px">
        <button class="btn alt" id="btnHear">🔊<span class="lbl" data-i18n="app.escuchar"> Escuchar</span></button>
        <button class="btn" id="btnSkip" data-i18n="app.seguir">Seguir ➜</button>
      </div>
    </div>
    <div class="prog" id="prog"></div>
    <div class="dots" id="dots"></div>
    <div class="stage">
      <div class="micCue" id="micCue" aria-live="polite"></div>
      <div class="kb" id="kb"></div>
    </div>
  </div>
`,
  herramientas:`<button class="iconbtn" id="btnMic" title="Escuchar mi piano" data-i18n-title="musica.mic_titulo">🎤</button>`,
  panelTexto:`<span data-i18n="musica.panel.texto"> — el 🎤 hace que la app escuche el piano. Tocar el teclado de la pantalla también funciona.</span>`,
  panelArriba:`<div class="micVivo"><b data-i18n="musica.panel.vivo_titulo">Lo que escucha el micrófono</b>
      <div class="micVivoFila"><span class="micNota" id="micVivoNota">–</span><span id="micVivoDet"></span></div>
      <div id="micVivoEstado"></div><div class="micMotivo" id="micVivoMotivo" style="display:none"></div></div>
    <label><span data-i18n="musica.panel.nota">Nota que escucho:</span> <b id="dbgNote">–</b></label>
    <label><span data-i18n="musica.panel.volumen">Volumen</span> <div class="meter"><i id="dbgLevel"></i><u id="dbgThr"></u></div> <span id="dbgLevelTxt"></span></label>
    <label><span data-i18n="musica.panel.sensibilidad">Sensibilidad</span> <input type="range" id="sens" min="1" max="30" value="8" style="flex:1"> <span id="sensVal"></span></label>
    <label><span data-i18n="musica.panel.octava">Aceptar la nota en cualquier octava</span> <input type="checkbox" id="anyOctave" checked></label>
    <div class="afin"><b data-i18n="musica.afin.titulo">Afinación del piano</b>
      <div id="afinInfo"></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px"><button class="btn" id="afinLa" style="padding:6px 14px;font-size:16px" data-i18n="musica.afin.btn_la">🎵 Tocá un La</button><button class="btn alt" id="afinCero" style="padding:6px 14px;font-size:16px" data-i18n="musica.afin.btn_reset">↺ Volver a cero</button></div>
      <div class="psum" id="afinMsg" style="display:none"></div>
      <label><span data-i18n="musica.afin.auto">Ajustar sola mientras se toca</span> <input type="checkbox" id="afinAuto" checked></label></div>`,
  panelPie:`<div class="note-hint" data-i18n="musica.panel.tip">Tip: poné la tablet sobre el atril, cerca del teclado. Si el teclado digital tiene volumen alto y la sala es silenciosa, funciona mejor.</div>`,
};
function iniciar(){
  $("btnBack").onclick=()=>{ const was=S.session; S.run++; S.mode="idle"; try{speechSynthesis.cancel();}catch(e){} resetFlow();
  if(was){ goMenuIsla(); } else { show("home"); renderHome(); setBubble(t("musica.que_cancion")); } };
  $("btnHomeBack").onclick=()=>goMenuIsla();
  $("btnHear").onclick=async()=>{ if(!S.song&&!S.session) return; const run=++S.run; const ch=chunk(); await demo(ch, run, !S.session); if(run===S.run){ S.mode="play"; renderDots(); } };
  $("btnSkip").onclick=()=>{
    if(S.session){ const run=++S.run; S.session.i++; renderProg(); nextItem(run); return; }
    if(!S.song) return; S.run++; if(S.full||S.learnIdx+1>=S.song.chunks.length) startFull(); else learnPhrase(S.learnIdx+1); };
  $("sens").oninput=e=>{ $("sensVal").textContent=e.target.value; };
  $("sensVal").textContent=$("sens").value;
  $("afinLa").onclick=()=>calibrarLa();
  $("afinCero").onclick=()=>{ mic.reiniciarAfinacion(); const m=$("afinMsg"); m.style.display="block"; m.textContent=t("musica.afin.reiniciada"); pintarAfinacion(); };
  $("afinAuto").onchange=e=>{ mic.afinacionAuto(e.target.checked); pintarAfinacion(); };
  Gioval.on("panel",()=>{ pintarAfinacion(); pintarVivo(); });
  pintarAfinacion(); pintarVivo();
  $("btnMic").onclick=async()=>{ ensureCtx(); if(mic.activo){ mic.detener(); } else { await mic.iniciar(MIC_OPTS); } };
  Gioval.entrada.suscribir("toque",ev=>{ ensureCtx(); Gioval.sonido.tocar(ev.midi,.6); handleInput(ev.midi,"touch"); });
  Gioval.entrada.suscribir("nota",ev=>{ handleInput(ev.midi,"mic",ev); });
  buildKeyboard();
  Gioval.on("idioma",d=>{ if(!d||!d.cambio) return; pintarAfinacion(); pintarVivo(); buildKeyboard(); if(S.chunks&&S.chunks.length&&document.querySelector("#play.active")) renderDots(); });
  Gioval.on("mapa",()=>{ $("btnMic").style.display=""; });
  Gioval.on("menu",p=>{ if(p!==ISLA){ if(mic.activo) mic.detener(); $("btnMic").style.display="none"; } else $("btnMic").style.display=""; });
}
const ISLA={id:"musica",hasSongs:true,emoji:"🎹",skills:SKILLS_MUSICA,
  get name(){ return t("musica.nombre"); }, get sub(){ return t("musica.sub"); },
  instrumento:"piano",entradas:["nota","toque"],
  actividades:ACTIVIDADES,dom:DOM,iniciar,
  entrar(title){ $("songTitle").textContent=title; show("play"); buildKeyboard(); },
  antesDeSesion(){ S.song=null; S.full=false; },
  fin:{ get ok(){ return t("musica.tocar_cancion"); }, get home(){ return t("musica.terminar_hoy"); },
    okFn(){ if(capLeft()<=0){ goMenuIsla(); return; } show("home"); renderHome(); },
    homeFn(){ goMenuIsla(); } },
  tarjetas(done){ return [{em:"🎵",t:t("musica.tarjeta_canciones"),s:done?t("menu.manana"):t("musica.tarjeta_sub"),on:!done,go:()=>{ show("home"); renderHome(); }}]; },
  get outro(){ return t("musica.outro"); },
  get capTail(){ return t("musica.cola_tope"); },
  get notaInforme(){ return t("musica.nota_informe"); },
};
Gioval.islas.registrar(ISLA);
})();
