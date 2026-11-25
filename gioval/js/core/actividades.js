"use strict";
/* ============ ACTIVIDADES POR TOQUE: motor genérico ============
   Las islas que se juegan tocando opciones (Números, y las que vengan) definen sus tipos de actividad con
   make/view/okMsgs/tip/reveal (ver js/islas/numeros.js) y se registran con tap:true. Este archivo dibuja la pantalla
   (#act), recibe los toques, da ayudas progresivas tras errores y reporta el resultado al motor (S.onDone). */
function entrarToques(title){ $("actTitle").textContent=title; show("act"); }
function fitAll(){
  document.querySelectorAll("#act [data-fit]").forEach(el=>{
    const p=el.parentElement; el.style.setProperty("--es","12px");
    const w=p.clientWidth-16,h=p.clientHeight-16; if(w<=0||h<=0) return;
    const [c,r]=el.dataset.fit.split(",").map(Number); let es;
    if(el.dataset.area) es=Math.sqrt(w*h/((+el.dataset.area+3)*2.2)); else es=Math.min(w/(c*1.3),h/(r*1.35));
    es=Math.max(14,Math.min(es,76)); el.style.setProperty("--es",es+"px");
    for(let g=0;g<14&&es>14&&(el.offsetHeight>p.clientHeight-8||el.offsetWidth>p.clientWidth-8);g++){ es*=.9; el.style.setProperty("--es",es+"px"); }
  });
}
window.addEventListener("resize",()=>{ if($("act").classList.contains("active")) fitAll(); });
function tapRender(){
  const T=S.tap; if(!T) return; const it=T.it, A=ACTIVITIES[it.skill.type];
  const v=A.view(it,T.aid,T); T.v=v;
  $("actStage").innerHTML=v.stage||""; $("actStage").className="actStage"+(v.sm?" sm":"");
  const ob=$("actOpts"); ob.className="actOpts"+(v.wide?" wide":"");
  ob.style.setProperty("--oc",v.oc||2); ob.style.setProperty("--ocl",v.ocl||v.oc||2); ob.style.setProperty("--n",v.opts.length);
  ob.innerHTML="";
  const want=it.seq[T.pos];
  v.opts.forEach((o,i)=>{
    const b=document.createElement("button"); b.className="opt"+(o.cls?" "+o.cls:"")+(v.cls?" "+v.cls:"");
    b.innerHTML=o.html; b.dataset.i=i;
    if(T.used.has(o.id!=null?o.id:i)) b.classList.add("used");
    if(T.dead.has(o.val)&&it.seq.length===1) b.classList.add("dead");
    if(T.reveal&&o.val===want&&!T.used.has(o.id!=null?o.id:i)&&!b.classList.contains("target")&&!ob.querySelector(".target")) b.classList.add("target");
    b.onclick=()=>tapPick(i); ob.appendChild(b);
  });
  fitAll();
}
$("actStage").onclick=e=>{ const T=S.tap; if(!T||S.mode!=="play") return; const A=ACTIVITIES[T.it.skill.type]; const ob=e.target.closest(".ob"); if(ob&&A.stageTap) A.stageTap(T.it,T,+ob.dataset.i); };
async function tapItem(run,it,A,ss){
  let aid=S.hint; if(A.noVoiceAid!=null&&!voiceReady()) aid=Math.min(aid,A.noVoiceAid);
  const T=S.tap={it,run,aid,pos:it.start||0,miss:0,used:new Set(),dead:new Set(),help:false,reveal:false,revealed:false,cnt:[],v:null,t0:0,tVoz:null};
  renderProg(); tapRender();
  S.mode="play"; T.t0=performance.now();   /* t0: el ítem ya se ve; tVoz: cuándo terminó de hablar la app (el tiempo de respuesta se mide desde ahí) */
  await speak(S.tap.v.say);
  if(S.tap===T) T.tVoz=performance.now();
}
/* tiempo de respuesta (ms) de un ítem resuelto sin errores: desde que terminó de hablar la app (o desde que se ve, si tocó antes) */
function tapRt(T,tFin){ const base=(T.tVoz!=null&&T.tVoz<=tFin)?T.tVoz:T.t0; return Math.max(200,Math.round(tFin-base)); }
async function tapPick(i){
  const T=S.tap; if(!T||S.mode!=="play") return;
  const v=T.v, o=v.opts[i], it=T.it, A=ACTIVITIES[it.skill.type], id=o.id!=null?o.id:i;
  if(T.used.has(id)||T.dead.has(o.val)) return;
  const now=performance.now(); if(now-S.lastWrong<250) return;
  const run=T.run, want=it.seq[T.pos], btn=$("actOpts").children[i];
  if(o.val===want){
    T.pos++; if(it.consume) T.used.add(id);
    try{ tone(76,.3,.16); }catch(e){}
    const fin=T.pos>=it.seq.length;
    if(fin) S.mode="between";
    T.reveal=false; tapRender();
    if(fin){ const rt=T.miss===0?tapRt(T,now):null; const b2=$("actOpts").children[i]; if(b2) b2.classList.add("ok"); await sleep(520); if(run!==S.run) return; S.onDone({miss:T.miss,revealed:T.revealed,rt,aid:T.aid}); }
    return;
  }
  S.lastWrong=now; T.miss++;
  if(S.check){ S.mode="between"; btn.classList.add("near"); await sleep(380); if(run!==S.run) return; S.onDone({miss:1,rt:null,aid:T.aid}); return; }
  btn.classList.add("near"); setTimeout(()=>btn.classList.remove("near"),450);
  if(T.miss===1){ setBubble(rnd(tl("tap.fallo1"))); }
  else if(T.miss===2){
    T.help=true;
    if(it.seq.length===1){ const wr=v.opts.filter(x=>x.val!==want&&!T.dead.has(x.val)); if(wr.length>1) T.dead.add(rnd(wr).val); }
    tapRender(); await speak(A.tip?A.tip(it):t("tap.tip"));
  } else if(T.miss>=3&&!T.reveal){
    T.reveal=true; T.revealed=true; tapRender(); await speak(A.reveal?A.reveal(it,T):t("tap.reveal"));
  }
}
$("btnActHear").onclick=()=>{ if(S.tap&&S.tap.v) speak(S.tap.v.say); };
$("btnActSkip").onclick=()=>{ if(!S.session) return; const run=++S.run; S.session.i++; renderProg(); nextItem(run); };
$("btnActBack").onclick=()=>{ S.run++; S.mode="idle"; try{speechSynthesis.cancel();}catch(e){} resetFlow(); goMenuIsla(); };

