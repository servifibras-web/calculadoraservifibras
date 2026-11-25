"use strict";
/* Estado general del juego. Lo propio de cada isla (canciones, teclado, etc.) lo agrega la isla. */
let KID = "";
let S = {mode:"idle", run:0, lastWrong:0, session:null, tap:null, check:false, onDone:null, kind:null, reveal:false, hint:0, finMode:"", capShown:false};

/* ============ REGISTRO DE ISLAS ============
   Cada isla: { id, name, emoji, sub, skills:[{id,name,icon,type,req,...}], actividades:{tipo:{make,...}},
     tap?:true (se juega tocando opciones: motor de js/core/actividades.js), plain?:true (sin estrellas ni rachas),
     instrumento?, entradas?:["nota","toque"], dom?:{pantallas,herramientas,panelTexto,panelArriba,panelPie}, iniciar?(),
     entrar?(titulo), antesDeSesion?(), fin?:{ok,home,okFn,homeFn}, tarjetas?(done), outro?, capTail?, notaInforme? } */
Gioval.islas = {
  lista: [], actividades: {},
  registrar(def){
    this.lista.push(def); Object.assign(this.actividades, def.actividades||{});
    if(def.tap) Object.values(def.actividades||{}).forEach(a=>{ a.tap=true; a.jugar=(run,it,ss)=>tapItem(run,it,a,ss); });
    return def;
  },
  habilidades(){ return this.lista.flatMap(p=>p.skills); },
  notasInforme(){ return this.lista.map(p=>p.notaInforme).filter(Boolean).join(" "); },
  montar(){
    this.lista.forEach(p=>{ const d=p.dom||{};
      if(d.pantallas) $("app").insertAdjacentHTML("beforeend",d.pantallas);
      if(d.herramientas) $("btnVoice").insertAdjacentHTML("beforebegin",d.herramientas);
      if(d.panelTexto) $("panelTexto").insertAdjacentHTML("beforeend",d.panelTexto);
      if(d.panelArriba) $("panelArriba").insertAdjacentHTML("beforeend",d.panelArriba);
      if(d.panelPie) $("panelPie").insertAdjacentHTML("beforeend",d.panelPie);
    });
    this.lista.forEach(p=>{ if(p.iniciar) p.iniciar(); });
  },
};
const PACKS=Gioval.islas.lista, ACTIVITIES=Gioval.islas.actividades;
let PACK=null;

/* ============ MOTOR DE APRENDIZAJE ============
   Ideas con respaldo en la ciencia del aprendizaje:
   - Sesiones cortas + repaso espaciado (la práctica distribuida rinde más que la masiva)
   - Recuperar de memoria (sin mostrar la respuesta) y mezclar habilidades (intercalado)
   - Dificultad adaptativa: apuntar a ~85% de aciertos
   - Pistas que se retiran de a poco
   - Oído primero (método Kodály)
   - Elogio al esfuerzo, no a "ser inteligente"
   - Tope diario de tiempo y chequeo semanal SIN ayuda para comprobar lo que realmente quedó
   CÓMO SUMAR OTRA ISLA: ver docs/AGREGAR_ISLA.md. Es un archivo nuevo en js/islas/ que llama a
   Gioval.islas.registrar({...}); este motor no nombra ninguna isla. El resto (sesión diaria, repaso espaciado,
   dificultad adaptativa, chequeo semanal, logros, informe y tope de tiempo) funciona igual para todas. */
const INTERVALS=[.2,1,3,7];
const capBase=()=>(store.limit[KID]||15)*60; /* minutos por día; lo cambian los adultos desde el panel */
const capLeft=()=>capBase()+(store.extra[KID+"|"+today()]||0)-(store.time[KID+"|"+today()]||0);
function SK(id){ const k=KID+"|"+id; return store.sk[k]||(store.sk[k]={score:.5,att:0,box:0,due:0,lvl:0,rec:[],mast:false,last:0}); }
const mastered=id=>SK(id).mast;
const unlockedList=()=>PACK.skills.filter(s=>s.req.every(mastered));
const makeItem=s=>ACTIVITIES[s.type].make(s);
function planSession(){
  const now=Date.now(), un=unlockedList();
  const due=un.filter(s=>SK(s.id).mast&&SK(s.id).due<=now).slice(0,2);
  const learn=un.find(s=>!SK(s.id).mast);
  const learn2=un.find(s=>!SK(s.id).mast&&s!==learn);
  let items=[];
  due.forEach(s=>{ for(let i=0;i<3;i++) items.push(makeItem(s)); });
  items=shuffle(items);
  if(learn){
    const L=[]; for(let i=0;i<7;i++) L.push(makeItem(learn));
    if(learn2){ [2,5,8].forEach(pos=>L.splice(pos,0,makeItem(learn2))); }
    items=items.concat(L);
  } else if(!due.length){
    let mix=[]; un.slice(-3).forEach(s=>{ for(let i=0;i<3;i++) mix.push(makeItem(s)); }); items=shuffle(mix);
  }
  return {items,due,learn};
}
function sessionPreview(){
  const un=unlockedList(), learn=un.find(s=>!SK(s.id).mast);
  const due=un.filter(s=>SK(s.id).mast&&SK(s.id).due<=Date.now());
  if(learn) return (due.length?"Repaso + ":"")+"Nuevo: "+learn.name;
  return due.length?"Repaso de lo aprendido":"¡Todo dominado! Repaso libre";
}
function checkInfo(){
  const ms=PACK.skills.filter(s=>SK(s.id).mast);
  if(!ms.length) return {ok:false,sub:"Se abre cuando domines algo"};
  const ck=(store.checks[KID]||[]).filter(c=>c.p===PACK.id); if(!ck.length) return {ok:true,sub:"Sin ayuda: ¡mostrá lo que sabés!"};
  const days=Math.floor((Date.now()-new Date(ck[ck.length-1].d+"T12:00:00").getTime())/DAY);
  return days>=7?{ok:true,sub:"Sin ayuda: ¡mostrá lo que sabés!"}:{ok:false,sub:"Disponible en "+(7-days)+" día(s)"};
}
function renderProg(){
  ["prog","prog2"].forEach(id=>{
    const box=$(id); box.innerHTML="";
    if(!S.session){ box.style.display="none"; return; }
    box.style.display="flex";
    S.session.items.forEach((_,i)=>{ const d=document.createElement("i"); const r=S.session.log[i];
      d.className=r===1?"ok":(r===2?"soft":(r===4?"dn":(i===S.session.i?"now":""))); box.appendChild(d); });
  });
}
/* entra a la pantalla de juego que corresponde a la isla (piano o toques) */
function enterPlay(title){
  S.tap=null;
  (PACK.entrar||entrarToques)(title);
  renderProg();
}
function resetFlow(){ S.tap=null; S.onDone=null; S.kind=null; S.check=false; S.session=null; S.reveal=false; renderProg(); }
async function startSession(){
  if(capLeft()<=0) return showCap();
  ensureCtx(); S.run++; const run=S.run;
  const plan=planSession();
  if(PACK.antesDeSesion) PACK.antesDeSesion(); S.finMode="session"; S.check=false; S.capShown=false;
  S.session={items:plan.items,i:0,log:[],t0:Date.now(),streak:0,newly:[],seen:{}};
  enterPlay("Sesión de hoy");
  await speak("¡Vamos con la sesión de hoy, "+KID+"! Son jueguitos cortos.");
  nextItem(run);
}
async function startCheck(){
  if(capLeft()<=0) return showCap();
  ensureCtx(); S.run++; const run=S.run;
  let items=[]; PACK.skills.filter(s=>SK(s.id).mast).forEach(s=>{ const n=ACTIVITIES[s.type].chequeoItems||2; for(let i=0;i<n;i++) items.push(makeItem(s)); });
  items=Gioval.dominio?Gioval.dominio.elegirChequeo(items):shuffle(items).slice(0,10); /* las saltadas se re-evalúan primero */
  if(PACK.antesDeSesion) PACK.antesDeSesion(); S.finMode="session"; S.check=true; S.capShown=false;
  S.session={items,i:0,log:[],t0:Date.now(),streak:0,newly:[],seen:{},checkRes:[]};
  enterPlay("Chequeo semanal");
  await speak("Hoy es el chequeo. No te ayudo: ¡mostrá lo que sabés! Si no estás seguro, probá igual.");
  nextItem(run);
}
async function nextItem(run){
  const ss=S.session; if(!ss||run!==S.run) return;
  if(ss.i>=ss.items.length || capLeft()<=0 || (Date.now()-ss.t0>10*60e3 && ss.i>=4)) return endSession(run);
  const it=ss.items[ss.i], sk=it.skill, st=SK(sk.id);
  S.reveal=false; S.kind=sk.type; S.hint=S.check?2:st.lvl; S.mode="demo";
  S.onDone=res=>itemDone(run,it,res);
  return ACTIVITIES[sk.type].jugar(run,it,ss);
}
function logEvent(sk,ok,first,kind,rt){
  const st=SK(sk.id), now=Date.now(); const g=st.last?+((now-st.last)/DAY).toFixed(2):0; st.last=now;
  const e={t:now,s:sk.id,o:ok?1:0,f:first?1:0,g,k:kind}; if(rt!=null) e.r=rt; /* r = tiempo de respuesta en ms (solo primer intento correcto) */
  const l=store.log[KID]||(store.log[KID]=[]); l.push(e); if(l.length>800) l.splice(0,l.length-800);
}
async function itemDone(run,it,res){
  if(run!==S.run) return;
  const sk=it.skill, st=SK(sk.id), ss=S.session, AT=ACTIVITIES[sk.type];
  const first=res.miss===0, ok=first||(AT.tolerancia&&res.miss<=AT.tolerancia&&!S.check);
  if(S.check){
    logEvent(sk,first,first,"check"); ss.checkRes.push({s:sk.id,o:first?1:0}); save();
    ss.log[ss.i]=4; ss.i++; renderProg();
    setBubble(rnd(["¡Anotado! ✍️","¡Seguimos!","¡Gracias! Vamos a la próxima."])); await sleep(600);
    if(run!==S.run) return; return nextItem(run);
  }
  const wasMast=st.mast; logEvent(sk,ok,first,wasMast?"review":"learn",res.rt);
  st.att++; st.score=st.score*.7+(ok?1:0)*.3; st.rec=st.rec.concat(ok?1:0).slice(-5);
  const rc=st.rec;
  if(rc.length>=3&&rc.slice(-3).every(x=>x)&&st.lvl<2){ st.lvl++; st.rec=[]; }
  else if(rc.length>=2&&rc.slice(-2).every(x=>!x)&&st.lvl>0){ st.lvl--; st.rec=[]; }
  let achievement=null;
  if(!st.mast){ if(st.att>=6&&st.score>=.8){ st.mast=true; st.box=1; st.due=Date.now()+INTERVALS[1]*DAY; achievement=sk.name; ss.newly.push(sk.name); } }
  else { st.box=ok?Math.min(3,st.box+1):Math.max(0,st.box-1); st.due=Date.now()+INTERVALS[st.box]*DAY; }
  if(achievement) Gioval.emit("dominada",{skill:sk}); /* gancho: salto por dominio rápido (js/core/dominio.js) */
  save();
  ss.log[ss.i]=first?1:2; ss.i++; ss.streak=first?ss.streak+1:0;
  if(!ok&&!it.retry){ ss.items.splice(Math.min(ss.i+2,ss.items.length),0,{...makeItem(sk),retry:true}); }
  renderProg();
  let msg=null;
  if(achievement) msg="¡Nuevo logro! Dominaste "+achievement+". ⭐";
  else if(!PACK.plain&&(ss.streak===3||ss.streak===6)) msg="¡"+ss.streak+" seguidas sin errores! Estás concentrado.";
  else if(!first&&ok) msg=rnd(["¡Lo lograste! Seguiste intentando.","¡Eso! Escuchaste mejor la segunda vez.","¡Insistir funciona!"]);
  else if(!ok) msg=(AT.tap&&!res.revealed&&res.miss<3)?"¡Probaste distinto y salió! La repasamos en un ratito.":"¡Esta era difícil! Volvemos a probarla en un ratito.";
  if(msg){ await speak(msg); } else { setBubble(rnd(AT.okMsgs||["¡Bien! ✨","¡Eso es!","¡Muy bien!","¡Sigamos! 🚀"])); await sleep(550); }
  if(run!==S.run) return; nextItem(run);
}
async function endSession(run){
  const ss=S.session; S.mode="done"; S.onDone=null;
  const day=today(); const ds=store.days[KID]||(store.days[KID]=[]); if(!ds.includes(day)){ ds.push(day); store.days[KID]=ds.slice(-90); }
  S.finMode="session";
  const fin=PACK.fin||{}; $("btnFinOk").textContent=fin.ok||"↩ Volver a la isla"; $("btnFinHome").textContent=fin.home||"🗺️ Al mapa";
  let speech;
  if(S.check){
    const n=ss.checkRes.length, okc=ss.checkRes.filter(x=>x.o).length;
    if(n){ const l=store.checks[KID]||(store.checks[KID]=[]); l.push({d:day,n,ok:okc,p:PACK.id}); store.checks[KID]=l.slice(-60); }
    Gioval.emit("chequeo",{res:ss.checkRes,pack:PACK}); /* gancho: re-evaluar habilidades saltadas */
    $("finStars").textContent="✅ "+okc+" de "+n; $("finTitle").textContent="¡Chequeo listo!";
    speech="¡Terminamos el chequeo, "+KID+"! Lo anoté para papá. ¡Gracias por mostrar lo que sabés!";
  } else {
    const okc=ss.log.filter(x=>x===1).length, tot=Math.max(1,ss.log.length), ratio=okc/tot;
    const stars=ratio>=.85?3:(ratio>=.6?2:1);
    $("finStars").textContent=PACK.plain?"🌱":"⭐".repeat(stars)+"☆".repeat(3-stars);
    $("finTitle").textContent=ss.newly.length?"¡Nuevo logro: "+ss.newly[0]+"!":"¡Terminaste la sesión de hoy!";
    const nxt=unlockedList().find(s=>!SK(s.id).mast);
    speech="¡Terminamos por hoy, "+KID+"! Practicaste mucho. "+(nxt?"Mañana seguimos con "+nxt.name+(/[?!.]$/.test(nxt.name)?"":"."):"Mañana repasamos lo que aprendiste.")+" "+(PACK.outro||"¡Hasta mañana!");
  }
  save(); $("finish").classList.add("show"); await speak(speech);
}
function showCap(){
  S.run++; S.capShown=true; S.mode="idle"; S.onDone=null; try{speechSynthesis.cancel();}catch(e){}
  $("capBox").classList.add("show");
  $("capMin").textContent=(store.limit[KID]||15); const tail=PACK.capTail||"¡Mañana seguimos!"; $("capTail").textContent=tail;
  speak("¡Llegamos a los "+(store.limit[KID]||15)+" minutos de hoy, "+KID+"! "+tail);
}
$("capOk").onclick=()=>{ $("capBox").classList.remove("show"); S.capShown=false; resetFlow(); goMenuIsla(); };
/* contador de tiempo: solo cuenta mientras se juega (pantalla de actividad abierta) */
setInterval(()=>{
  if(!KID||document.hidden) return;
  const act=document.querySelector(".screen.active"); if(!act||!act.classList.contains("juego")) return;
  const k=KID+"|"+today(); store.time[k]=(store.time[k]||0)+1; if(store.time[k]%10===0) save();
  if(capLeft()<=0&&!S.capShown) showCap();
},1000);
