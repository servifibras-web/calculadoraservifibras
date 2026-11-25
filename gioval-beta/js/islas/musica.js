"use strict";
/* ============ ISLA MÚSICA ============
   Datos (habilidades, canciones, textos) + juego del piano (teclado en pantalla, demostración, escucha por micrófono).
   Se registra en Gioval.islas; el motor no conoce nada de esta isla. */
(function(){
const NAMES = {C:"Do",D:"Re",E:"Mi",F:"Fa",G:"Sol",A:"La",B:"Si"};
const COLORS = {C:"#ff5a5f",D:"#ff9f1c",E:"#ffd23f",F:"#4cc86a",G:"#2ec4b6",A:"#4d96ff",B:"#9b5de5"};
const BASE = {C:0,D:2,E:4,F:5,G:7,A:9,B:11};
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
  {title:"Estrellita", sub:"Estrellita, ¿dónde estás?", emoji:"⭐",
   phrases:["C4 C4 G4 G4 A4 A4 G4:2","F4 F4 E4 E4 D4 D4 C4:2","G4 G4 F4 F4 E4 E4 D4:2"],
   order:[0,1,2,2,0,1]},
  {title:"Himno a la Alegría", sub:"Beethoven", emoji:"🎶",
   phrases:["E4 E4 F4 G4 G4 F4 E4 D4","C4 C4 D4 E4 E4:1.5 D4:.5 D4:2","C4 C4 D4 E4 D4:1.5 C4:.5 C4:2"],
   order:[0,1,0,2]},
  {title:"Cumpleaños feliz", sub:"¡A festejar!", emoji:"🎂",
   phrases:["G4 G4 A4 G4 C5 B4:2","G4 G4 A4 G4 D5 C5:2"],
   order:[0,1,0,1]},
].map(s=>({...s, chunks:s.phrases.map(parsePhrase)}));


/* ---- estado propio de la isla (el motor solo conoce lo genérico de S) ---- */
const mic=Gioval.entrada.proveedores.microfono;
const MIC_OPTS={
  umbral:()=>(+$("sens").value)/1000,
  nivel:r=>{ $("dbgLevel").style.width=Math.min(100,r*600)+"%"; },
  alDetectar:b=>{ $("dbgNote").textContent=midiName(b)+" ("+b+")"; },
  alEncender:()=>{ $("btnMic").classList.add("on"); setBubble("¡Te escucho! Tocá tu piano 🎹"); },
  alError:()=>{ $("btnMic").classList.remove("on"); setBubble("No pude usar el micrófono. Podés tocar el teclado de la pantalla."); },
  alApagar:()=>{ $("btnMic").classList.remove("on"); },
};
function midiName(m){ const n=["Do","Do#","Re","Re#","Mi","Fa","Fa#","Sol","Sol#","La","La#","Si"]; return n[((m%12)+12)%12]; }
Object.assign(S,{song:null,chunks:[],ci:0,ni:0,missPhrase:0,missNote:0,learnIdx:0});
const starsOf=t=>store.stars[KID+"|"+t]||0;
const PRAISE = ()=>["¡Muy bien, "+KID+"!","¡Qué bien que lo intentaste!","¡Lo practicaste y te salió!","¡Eso es! Escuchaste con atención.","¡Seguiste hasta lograrlo!","¡Esa melodía está quedando genial!"];

/* ============ TECLADO ============ */
function buildKeyboard(){
  const kb=$("kb"); kb.innerHTML="";
  WHITE.forEach((m,i)=>{
    const L=PCLET[m%12]; const k=document.createElement("div");
    k.className="key"; k.dataset.m=m; k.style.setProperty("--c",COLORS[L]);
    k.innerHTML=`<span>${NAMES[L]}</span>`;
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
    const st=starsOf(s.title);
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
    else if(pending&&S.kind==="find"&&S.hint>=2&&!S.reveal){ d.className+=" neutral"; d.innerHTML=`<span>${NAMES[L]}</span>`; }
    else { d.style.background=COLORS[L]; d.innerHTML=`<span>${NAMES[L]}</span>`; }
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
  await learnPhrase(0, "Vamos a tocar "+S.song.title+". Primero escuchá.");
}
async function learnPhrase(idx, intro){
  const run=S.run; S.learnIdx=idx; S.mode="demo"; S.chunks=[S.song.chunks[idx]]; S.ci=0; S.ni=0; S.missPhrase=0; S.missNote=0; renderDots();
  await speak(intro|| (idx===0?"Escuchá cómo suena.":"Ahora, la siguiente parte. Escuchá."));
  if(run!==S.run) return;
  if(!(await demo(S.chunks[0],run))) return;
  await speak("¡Ahora te toca a vos!"); if(run!==S.run) return;
  S.mode="play"; renderDots(); armMic();
}
async function startFull(){
  const run=S.run; S.mode="demo";
  S.chunks=S.song.order.map(i=>S.song.chunks[i]); S.ci=0; S.ni=0; S.missPhrase=0; S.missNote=0; S.full=true;
  renderDots();
  await speak("¡Ya sabés todas las partes! Ahora tocá la canción completa. ¡Yo te espero!");
  if(run!==S.run) return; S.mode="play"; renderDots();
}
function stars3(m){ return m===0?3:(m<=3?2:1); }
async function handleInput(midi){
  if(S.mode!=="play"||S.tap) return;
  const now=performance.now(); if(now-S.lastWrong<300) return;
  const t=chunk()[S.ni]; if(!t) return;
  const anyOct=$("anyOctave").checked;
  const ok = anyOct ? (midi%12===t.midi%12) : (midi===t.midi);
  const run=S.run;
  if(ok){
    S.missNote=0; if(!S.check) flash(t.midi,"ok",300); S.ni++; renderDots();
    if(S.ni>=chunk().length){
      S.mode="between";
      if(S.onDone){ const cb=S.onDone; cb({miss:S.missPhrase}); return; }
      if(!S.full){
        const st=stars3(S.missPhrase);
        await speak(rnd(PRAISE())+" "+"⭐".repeat(st)); if(run!==S.run) return;
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
    const tn=NAMES[PCLET[t.midi%12]];
    if(S.kind==="ear"||S.kind==="echo"){
      if(S.missNote===2){ S.mode="demo"; await speak("Escuchá otra vez."); if(await demo(chunk(),run,false)){ S.mode="play"; renderDots(); } }
      else if(S.missNote>=4){ S.reveal=true; S.missNote=0; renderDots(); setBubble("Mirá, es el "+tn+" 👀"); }
      else setBubble("¡Casi! Probá otra vez 😊");
    }
    else if(S.missNote===2){ S.reveal=true; renderDots(); setBubble("¡Casi! Buscá el "+tn); await speak("¡Casi! Probá con el "+tn+"."); }
    else if(S.missNote>=4){ S.missNote=0; S.mode="demo"; await speak("Mirá, te ayudo. Este es el "+tn+"."); tone(t.midi,.8); flash(t.midi,"demo",700); await sleep(900); if(run===S.run){ S.mode="play"; renderDots(); } }
    else setBubble("¡Casi! Probá otra vez 😊");
  }
}
async function finishSong(run){
  S.finMode="song";
  S.finOk=()=>{ const i=SONGS.indexOf(S.song); S.full=false; startSong(i); };
  S.finHome=()=>{ S.full=false; $("btnBack").onclick(); };
  $("btnFinOk").textContent="¡Otra vez!"; $("btnFinHome").textContent="Elegir otra canción";
  S.mode="done"; const st=stars3(Math.floor(S.missPhrase/2)); // en la canción completa se tolera más
  const prev=starsOf(S.song.title); if(st>prev){ store.stars[KID+"|"+S.song.title]=st; save(); }
  $("finStars").textContent="⭐".repeat(st)+"☆".repeat(3-st);
  $("finTitle").textContent="¡Tocaste "+S.song.title+"!";
  $("finish").classList.add("show");
  await speak("¡Bravo "+KID+"! ¡Tocaste toda la canción!");
}

/* ---- habilidades (cadena con req) ---- */
const SK_ALL=[60,62,64,65,67,69,71,72];
const SKILLS_MUSICA=[
  {id:"n1",name:"Do, Re y Mi",icon:"🔴🟠🟡",type:"find",notes:[60,62,64],prior:[],req:[]},
  {id:"e1",name:"Oído: ¿cuál suena?",icon:"👂",type:"ear",notes:[60,62,64],req:["n1"]},
  {id:"n2",name:"Fa y Sol",icon:"🟢🔵",type:"find",notes:[65,67],prior:[60,62,64],req:["n1"]},
  {id:"eco3",name:"Eco de 3 notas",icon:"🔁",type:"echo",len:3,notes:[60,62,64,65,67],req:["e1","n2"]},
  {id:"n3",name:"La, Si y Do alto",icon:"🟣⭐",type:"find",notes:[69,71,72],prior:[60,62,64,65,67],req:["n2"]},
  {id:"e2",name:"Oído con todas las notas",icon:"🎧",type:"ear",notes:SK_ALL,req:["e1","n3"]},
  {id:"eco5",name:"Eco de 5 notas",icon:"🎶",type:"echo",len:5,notes:SK_ALL,req:["eco3","n3"]},
];
let lastTarget=null;
function pickDistinct(arr){ let x,g=0; do{ x=rnd(arr); g++; }while(arr.length>1&&x===lastTarget&&g<10); lastTarget=x; return x; }

/* tipos de actividad de la isla */
const ACTIVIDADES={
  find:{
    make(s){ const pool=(Math.random()<.35&&s.prior&&s.prior.length)?s.prior:s.notes; return {skill:s,notes:[pickDistinct(pool)]}; },
    async present(it,run,ss){ const nm=NAMES[PCLET[it.notes[0]%12]]; await speak(rnd(["Tocá el "+nm,"Buscá el "+nm,"¿Dónde está el "+nm+"?"])); return run===S.run; }
  },
  ear:{
    make(s){ return {skill:s,notes:[pickDistinct(s.notes)]}; },
    async present(it,run,ss){ await speak(ss.seen.ear?"Escuchá…":"Escuchá bien y tocá la nota que suena."); ss.seen.ear=true;
      if(!(await demo(S.chunks[0],run,false))) return false; setBubble("¿Cuál era? 🎧"); return true; }
  },
  echo:{
    tolerancia:1, chequeoItems:1,
    make(s){ const seq=[]; let cur=rnd(s.notes); seq.push(cur);
      while(seq.length<s.len){ const i=s.notes.indexOf(cur); const j=Math.max(0,Math.min(s.notes.length-1,i+rnd([-2,-1,1,2]))); cur=s.notes[j]; seq.push(cur); }
      return {skill:s,notes:seq}; },
    async present(it,run,ss){ await speak(ss.seen.echo?"Escuchá…":"Escuchá y repetí igualito."); ss.seen.echo=true;
      if(!(await demo(S.chunks[0],run,false))) return false; setBubble("¡Ahora vos! 🎹"); return true; }
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
    <div class="bar"><button class="btn alt" id="btnHomeBack">⬅<span class="lbl"> Isla</span></button><h2 style="margin:0">🎵 Mis canciones</h2><span style="width:90px"></span></div>
    <div class="songs" id="songs"></div>
  </div>

  <div class="screen juego" id="play">
    <div class="bar">
      <button class="btn alt" id="btnBack">⬅<span class="lbl"> Volver</span></button>
      <div style="font-weight:800;font-size:clamp(18px,2.8vw,26px)" id="songTitle"></div>
      <div style="display:flex;gap:8px">
        <button class="btn alt" id="btnHear">🔊<span class="lbl"> Escuchar</span></button>
        <button class="btn" id="btnSkip">Seguir ➜</button>
      </div>
    </div>
    <div class="prog" id="prog"></div>
    <div class="dots" id="dots"></div>
    <div class="stage">
      <div class="kb" id="kb"></div>
    </div>
  </div>
`,
  herramientas:`<button class="iconbtn" id="btnMic" title="Escuchar mi piano">🎤</button>`,
  panelTexto:` — el 🎤 hace que la app escuche el piano. Tocar el teclado de la pantalla también funciona.`,
  panelArriba:`<label>Nota que escucho: <b id="dbgNote">–</b></label>
    <label>Volumen <div class="meter"><i id="dbgLevel"></i></div></label>
    <label>Sensibilidad <input type="range" id="sens" min="1" max="30" value="8" style="flex:1"> <span id="sensVal"></span></label>
    <label>Aceptar la nota en cualquier octava <input type="checkbox" id="anyOctave" checked></label>`,
  panelPie:`<div class="note-hint">Tip: poné la tablet sobre el atril, cerca del teclado. Si el teclado digital tiene volumen alto y la sala es silenciosa, funciona mejor.</div>`,
};
function iniciar(){
  $("btnBack").onclick=()=>{ const was=S.session; S.run++; S.mode="idle"; try{speechSynthesis.cancel();}catch(e){} resetFlow();
  if(was){ goMenuIsla(); } else { show("home"); renderHome(); setBubble("¿Qué canción tocamos?"); } };
  $("btnHomeBack").onclick=()=>goMenuIsla();
  $("btnHear").onclick=async()=>{ if(!S.song&&!S.session) return; const run=++S.run; const ch=chunk(); await demo(ch, run, !S.session); if(run===S.run){ S.mode="play"; renderDots(); } };
  $("btnSkip").onclick=()=>{
    if(S.session){ const run=++S.run; S.session.i++; renderProg(); nextItem(run); return; }
    if(!S.song) return; S.run++; if(S.full||S.learnIdx+1>=S.song.chunks.length) startFull(); else learnPhrase(S.learnIdx+1); };
  $("sens").oninput=e=>{ $("sensVal").textContent=e.target.value; };
  $("sensVal").textContent=$("sens").value;
  $("btnMic").onclick=async()=>{ ensureCtx(); if(mic.activo){ mic.detener(); } else { await mic.iniciar(MIC_OPTS); } };
  Gioval.entrada.suscribir("toque",ev=>{ ensureCtx(); Gioval.sonido.tocar(ev.midi,.6); handleInput(ev.midi,"touch"); });
  Gioval.entrada.suscribir("nota",ev=>{ handleInput(ev.midi,"mic"); });
  buildKeyboard();
  Gioval.on("mapa",()=>{ $("btnMic").style.display=""; });
  Gioval.on("menu",p=>{ if(p!==ISLA){ if(mic.activo) mic.detener(); $("btnMic").style.display="none"; } else $("btnMic").style.display=""; });
}
const ISLA={id:"musica",name:"Isla Música",emoji:"🎹",sub:"¡A tocar el piano!",skills:SKILLS_MUSICA,hasSongs:true,
  instrumento:"piano",entradas:["nota","toque"],
  actividades:ACTIVIDADES,dom:DOM,iniciar,
  entrar(title){ $("songTitle").textContent=title; show("play"); buildKeyboard(); },
  antesDeSesion(){ S.song=null; S.full=false; },
  fin:{ ok:"🎵 Tocar una canción", home:"Terminar por hoy",
    okFn(){ if(capLeft()<=0){ goMenuIsla(); return; } show("home"); renderHome(); },
    homeFn(){ goMenuIsla(); } },
  tarjetas(done){ return [{em:"🎵",t:"Mis canciones",s:done?"Mañana seguimos 🌙":"Tocá tus favoritas",on:!done,go:()=>{ show("home"); renderHome(); }}]; },
  outro:"Ahora, ¡a tocar el piano de verdad!",
  capTail:"Ahora, a tocar tu piano de verdad. ¡Mañana seguimos!",
  notaInforme:"Lo más importante es que lo aprendido se vea también en su piano de verdad.",
};
Gioval.islas.registrar(ISLA);
})();
