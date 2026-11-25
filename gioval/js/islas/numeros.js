"use strict";
/* ============ ISLA NÚMEROS ============
   Lógica universal (contar, comparar, sumar, restar, series, valor posicional, dobles, grupos iguales…) + textos en español (es-AR).
   Habilidades encadenadas con req (datos en js/datos/numeros.js); las actividades por toque están abajo. Se registra en Gioval.islas.
   Las preguntas iniciales, el test de ubicación y el punto de partida están en js/islas/numeros_ubicacion.js. */
(function(){
/* La escalera de habilidades (31) vive en js/datos/numeros.js; acá solo está cómo se juega cada tipo de actividad. */
const DN=Gioval.datos.numeros, SKILLS_NUMEROS=DN.ESCALA;

/* ---- actividades por toque de esta isla ---- (el motor de toques es genérico: js/core/actividades.js)
   Una actividad "tap" define:
     make(s)            -> ítem con todo lo aleatorio ya resuelto: {skill, seq:[respuestas en orden], opts:[{val,html}], ...}
     view(it,aid,T)     -> {say, stage, opts, oc, ocl, wide, cls} según el nivel de ayuda aid (0 más ayuda … 2 sin ayuda)
     okMsgs/tip/reveal  -> textos de proceso (nunca elogio de la persona)
     stageTap(it,T,i)   -> (opcional) toque sobre el dibujo del escenario
   El motor (tapItem/tapPick) se ocupa de errores, ayudas progresivas, chequeo sin ayuda y registro. */
const NW=["cero","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez","once","doce","trece","catorce","quince","dieciséis","diecisiete","dieciocho","diecinueve","veinte"];
const OBJS=[
  {e:"🍎",s:"manzana",p:"manzanas",f:1},{e:"⭐",s:"estrella",p:"estrellas",f:1},{e:"🚗",s:"auto",p:"autos"},
  {e:"🐟",s:"pez",p:"peces"},{e:"🌸",s:"flor",p:"flores",f:1},{e:"🎈",s:"globo",p:"globos"},
  {e:"🐶",s:"perro",p:"perros"},{e:"🍓",s:"frutilla",p:"frutillas",f:1},{e:"⚽",s:"pelota",p:"pelotas",f:1},
  {e:"🦋",s:"mariposa",p:"mariposas",f:1},{e:"🍪",s:"galletita",p:"galletitas",f:1},{e:"🐢",s:"tortuga",p:"tortugas",f:1},
];
const nm=(o,n)=>n===1?o.s:o.p;
const nw=(n,o)=>(n===1&&o)?(o.f?"una":"un"):NW[n];
const uno=o=>o.f?"una":"uno";
const cuantos=o=>o.f?"Cuántas":"Cuántos";
function numOpts(ans,min,max,k){
  const c=[]; for(let d=-3;d<=3;d++){ const v=ans+d; if(d&&v>=min&&v<=max) c.push(v); }
  const pool=shuffle(c).slice(0,k-1);
  for(let v=min;v<=max&&pool.length<k-1;v++){ if(v!==ans&&!pool.includes(v)) pool.push(v); }
  return shuffle([ans,...pool]);
}
const chunks5=n=>{ const a=[]; for(let l=n;l>0;l-=5) a.push(Math.min(5,l)); return a; };
const chunksRnd=n=>{ const a=[]; let l=n; while(l>0){ const c=Math.min(l,R(2,6)); a.push(c); l-=c; } if(a.length>1&&a[a.length-1]===1){ a[a.length-2]++; a.pop(); } return shuffle(a); };
/* dibujo de n objetos en filas; o.x = cuántos tachados al final; o.cnt = índices ya contados; o.nofit = sin tamaño propio */
function objs(e,plan,o={}){
  const total=plan.reduce((a,b)=>a+b,0); let i=0;
  const rows=plan.map(c=>{ let r=""; for(let k=0;k<c;k++,i++){
    const cr=o.x&&i>=total-o.x, ci=o.cnt?o.cnt.indexOf(i):-1;
    r+=`<span class="ob${cr?" x":""}" data-i="${i}">${e}${ci>=0?`<b>${ci+1}</b>`:""}</span>`; } return `<div class="or">${r}</div>`; }).join("");
  return `<div class="og"${o.nofit?"":` data-fit="${Math.max(...plan)},${plan.length+(o.extra||0)}"`}>${rows}${o.cap?`<div class="ocap">${o.cap}</div>`:""}</div>`;
}
const numOpt=v=>({val:v,html:String(v)});
const OKGEN=["¡Eso es! Te fijaste bien.","¡Salió! Pensarlo paso a paso funciona.","¡Bien pensado! Seguimos 🚀"];
const TAP_ACTS={
  count:{
    okMsgs:["¡Contaste con cuidado!","¡Contar de a uno funciona!","¡Prestaste atención y salió!"],
    make(s){ const n=pick(range(s.min,s.max),"cn"+s.id), o=pick(OBJS,"obj");
      const vals=numOpts(n,1,Math.max(s.max,n+1),4); const far=vals.slice().sort((a,b)=>Math.abs(b-n)-Math.abs(a-n))[0];
      return {skill:s,n,o,seq:[n],opts:vals.map(numOpt),far,plan0:chunks5(n),plan2:chunksRnd(n)}; },
    view(it,aid,T){
      const tapOn=(aid===0||T.help)&&!S.check, plan=aid>=2?it.plan2:it.plan0;
      let ops=it.opts; if(aid===0&&ops.length>3) ops=ops.filter(o=>o.val!==it.far);
      return {say:"¿"+cuantos(it.o)+" "+it.o.p+" hay? "+(tapOn?"Tocá cada dibujo mientras contás.":"Contá y tocá el número."),
        stage:objs(it.o.e,plan,{cnt:tapOn?T.cnt:null}), opts:ops, oc:ops.length===3?3:2, ocl:ops.length===3?3:2}; },
    stageTap(it,T,i){ if(S.check||!(T.aid===0||T.help)||T.cnt.includes(i)) return; T.cnt.push(i); speak(NW[T.cnt.length]); tapRender(); },
    tip:it=>"Contá de a uno, tocando cada dibujo. Y saqué una opción.",
    reveal:it=>"Contemos juntos: hay "+NW[it.n]+". Mirá cuál es."
  },
  numrec:{
    okMsgs:["¡Te fijaste bien en el número!","¡Escuchaste con atención y salió!","¡Eso es! Buscar con calma ayuda."],
    noVoiceAid:0,
    make(s){ const n=pick(range(s.min,s.max),"nr"+s.id), o=pick(OBJS,"obj");
      const grp=s.max<=10&&Math.random()<.4;
      const vals=numOpts(n,1,s.max,grp?3:4);
      return {skill:s,n,o,grp,seq:[n],opts:vals.map(v=>({val:v,html:grp?objs(o.e,chunks5(v),{extra:0}):String(v)})),far:vals.slice().sort((a,b)=>Math.abs(b-n)-Math.abs(a-n))[0],plan:chunks5(n)}; },
    view(it,aid,T){
      if(it.grp) return {say:"Este es el "+NW[it.n]+". Tocá el grupo que tiene "+NW[it.n]+".",stage:`<div class="bignum">${it.n}</div>`,sm:true,opts:it.opts,wide:true,oc:1,ocl:3};
      let ops=it.opts; if(aid===0&&ops.length>3) ops=ops.filter(o=>o.val!==it.far);
      return {say:rnd(["Tocá el número "+NW[it.n]+".","¿Dónde está el "+NW[it.n]+"?","Buscá el "+NW[it.n]+"."]),
        stage:aid===0?objs("🔵",it.plan):"", opts:ops, oc:ops.length===3?3:2, ocl:ops.length===3?3:2}; },
    tip:it=>"Fijate bien en cada número. Saqué una opción.",
    reveal:it=>"Mirá, es el "+NW[it.n]+"."
  },
  cmp:{
    okMsgs:["¡Comparaste con cuidado!","¡Miraste bien y decidiste!","¡Eso es! Fijarse ayuda."],
    make(s){ let a=R(1,s.max),b=R(1,s.max),g=0; while(a===b&&g++<20) b=R(1,s.max); if(a===b) b=a===s.max?a-1:a+1;
      const o=pick(OBJS,"obj"), ask=Math.random()<.4?"menos":"mas";
      return {skill:s,a,b,o,ask,seq:[ask==="mas"?Math.max(a,b):Math.min(a,b)],opts:shuffle([a,b]).map(numOpt)}; },
    view(it,aid,T){
      const ops=it.opts.map(op=>({val:op.val,html:aid>=2?`<div class="bignum" style="font-size:clamp(50px,min(22vw,26vh),120px)">${op.val}</div>`:objs(it.o.e,chunks5(op.val),{cap:aid===0?op.val:"",extra:aid===0?1:0})}));
      const say=aid>=2?(it.ask==="mas"?"Tocá el número más grande.":"Tocá el número más chico."):("¿Dónde hay "+(it.ask==="mas"?"más ":"menos ")+it.o.p+"?");
      return {say,stage:"",opts:ops,wide:true,oc:1,ocl:2}; },
    tip:it=>"Fijate bien cuál tiene "+(it.ask==="mas"?"más":"menos")+". Saqué una opción.",
    reveal:it=>"Mirá, este es el que tiene "+(it.ask==="mas"?"más":"menos")+": "+NW[it.seq[0]]+"."
  },
  add:{
    okMsgs:["¡Juntaste y contaste!","¡Pensaste la suma paso a paso!","¡Eso es! Contar todo junto ayuda."],
    make(s){ const c=pick(range(s.min,s.max),"ad"+s.id), a=R(1,c-1), b=c-a, o=pick(OBJS,"obj");
      return {skill:s,a,b,c,o,seq:[c],opts:numOpts(c,1,s.max,4).map(numOpt)}; },
    view(it,aid,T){
      const {a,b,o}=it, g=(n,k)=>`<div class="grp ${k}">${objs(o.e,chunks5(n),{nofit:1})}</div>`;
      const stage=aid>=2?`<div class="eqt" style="font-size:clamp(46px,14vmin,110px)">${a} + ${b} = ?</div>`
        :`<div class="eq" data-fit="0,0" data-area="${a+b+2}"><div class="eqrow">${g(a,"g1")}<span class="eqop">+</span>${g(b,"g2")}<span class="eqop" style="white-space:nowrap">= ?</span></div>${aid===0?`<div class="eqt">${a} + ${b} = ?</div>`:""}</div>`;
      const say=aid>=2?"¿Cuánto es "+NW[a]+" más "+NW[b]+"?":"Hay "+nw(a,o)+" "+nm(o,a)+". "+(b===1?"Llega "+uno(o):"Llegan "+NW[b])+" más. ¿"+cuantos(o)+" hay en total?";
      return {say,stage,opts:it.opts,oc:2,ocl:2}; },
    tip:it=>"Contá todos juntos. Saqué una opción.",
    reveal:it=>NW[it.a]+" más "+NW[it.b]+" son "+NW[it.c]+". Mirá."
  },
  sub:{
    okMsgs:["¡Sacaste y contaste lo que queda!","¡Pensaste la resta paso a paso!","¡Eso es! Mirar lo que queda ayuda."],
    make(s){ const a=pick(range(s.min,s.max),"sb"+s.id), b=R(1,a-1), c=a-b, o=pick(OBJS,"obj");
      return {skill:s,a,b,c,o,seq:[c],opts:numOpts(c,1,s.max,4).map(numOpt)}; },
    view(it,aid,T){
      const {a,b,o}=it;
      const stage=aid>=2?`<div class="eqt" style="font-size:clamp(46px,14vmin,110px)">${a} − ${b} = ?</div>`
        :`<div class="eq" data-fit="0,0" data-area="${a+2}"><div class="eqrow"><div class="grp">${objs(o.e,chunks5(a),{nofit:1,x:b})}</div></div>${aid===0?`<div class="eqt">${a} − ${b} = ?</div>`:""}</div>`;
      const say=aid>=2?"¿Cuánto es "+NW[a]+" menos "+NW[b]+"?":"Había "+nw(a,o)+" "+nm(o,a)+". "+(b===1?"Se va "+uno(o):"Se van "+NW[b])+". ¿"+cuantos(o)+" quedan?";
      return {say,stage,opts:it.opts,oc:2,ocl:2}; },
    tip:it=>"Mirá las que quedan sin tachar. Saqué una opción.",
    reveal:it=>NW[it.a]+" menos "+NW[it.b]+" son "+NW[it.c]+". Mirá."
  },
};

/* ============ ACTIVIDADES NUEVAS (escalera por edades) ============
   Mismos contratos que arriba. Textos en Gioval.datos.numeros.TEXTOS.act. Convención de ayuda visual (aid):
   0 = dibujo contable + escritura, 1 = solo dibujo, 2 = solo símbolos y voz. */
const TX=DN.TEXTOS, AX=TX.act;
const fmt=(t,v)=>t.replace(/\{(\w+)\}/g,(m,k)=>(v&&v[k]!=null)?v[k]:m);
const decs=n=>n===0?"ninguna decena":n===1?"una decena":n+" decenas";
const unis=n=>n===0?"ninguna unidad":n===1?"una unidad":n+" unidades";
const cents=n=>n===0?"ninguna centena":n===1?"una centena":n+" centenas";
const cap1=t=>t.charAt(0).toUpperCase()+t.slice(1);
const farOf=(vals,n)=>vals.slice().sort((a,b)=>Math.abs(b-n)-Math.abs(a-n))[0];
const trimOpts=(it,aid)=>{ let ops=it.opts; if(aid===0&&ops.length>3) ops=ops.filter(o=>o.val!==it.far); return ops; };
const ocN=ops=>ops.length===3?3:2;
/* opciones de números grandes: vecinos, ±10 y los que se pasan como "must" (por ejemplo, las cifras invertidas) */
function numOptsG(ans,min,max,k,must){
  const ok=v=>v!==ans&&v>=min&&v<=max, pool=[];
  (must||[]).forEach(v=>{ if(ok(v)&&!pool.includes(v)) pool.push(v); });
  shuffle([ans+1,ans-1,ans+10,ans-10,ans+2,ans-2]).forEach(v=>{ if(pool.length<k-1&&ok(v)&&!pool.includes(v)) pool.push(v); });
  for(let v=min;v<=max&&pool.length<k-1;v++){ if(ok(v)&&!pool.includes(v)) pool.push(v); }
  return shuffle([ans,...pool.slice(0,k-1)]);
}
/* bloques de base 10: centena = cuadrado, decena = barra, unidad = cuadradito. xd/xu: cuántas decenas/unidades se tachan (las últimas) */
function bq(c,d,u,o={}){
  const g=(n,cls,x,extra)=>{ let h=""; for(let i=0;i<n;i++) h+=`<span class="${cls}${x&&i>=n-x?" x":""}"></span>`; return `<span class="bg${extra||""}">${h}</span>`; };
  const parts=[]; if(c) parts.push(g(c,"b100")); if(d) parts.push(g(d,"b10",o.xd)); if(u) parts.push(g(u,"b1",o.xu,u>5?" bu":""));
  const w=c*1.45+d*.42+(u>5?5:u)*.34+Math.max(0,parts.length-1)*.5+.4;
  return `<div class="bq"${o.nofit?"":` data-fit="${(w/1.3).toFixed(1)},${((c?1.4:1.4)/1.35).toFixed(1)}"`}>${parts.join("")||"0"}</div>`;
}
const digs=n=>({c:Math.floor(n/100),d:Math.floor(n%100/10),u:n%10});
const eqtBig=t=>`<div class="eqt" style="font-size:clamp(40px,12vmin,96px)">${t}</div>`;
const grupo=(inner,k,icon)=>`<div class="grp ${k||""}">${icon?`<div class="ocap" style="font-size:calc(var(--es,24px)*.8)">${icon}</div>`:""}${inner}</div>`;
const eqWrap=(rows,area,extra)=>`<div class="eq" data-fit="0,0" data-area="${area}"><div class="eqrow">${rows}</div>${extra||""}</div>`;

const NUEVAS={
  /* ---- el que sigue y el que va antes ---- */
  vecino:{
    okMsgs:AX.vecino.ok,
    make(s){ const dir=Math.random()<.5?"sig":"ant";
      const n=dir==="sig"?pick(range(s.min,s.max-1),"vc"+s.id):pick(range(s.min+1,s.max),"vc"+s.id), r=dir==="sig"?n+1:n-1;
      const vals=numOpts(r,s.min,s.max,4); return {skill:s,n,dir,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {n,dir,r}=it, c=(x,b)=>`<span class="sl${b?" blank":""}">${b?"?":x}</span>`;
      let stage;
      if(aid===0){ const izq=dir==="sig"?(n>1?c(n-1):""):c(r,1), cen=c(n), der=dir==="sig"?c(r,1):c(n+1); stage=`<div class="slots">${izq}${cen}${der}</div>`; }
      else if(aid===1) stage=`<div class="slots">${dir==="sig"?c(n)+c(r,1):c(r,1)+c(n)}</div>`;
      else stage=`<div class="bignum">${n}</div>`;
      const ops=trimOpts(it,aid);
      return {say:fmt(AX.vecino[dir],{n}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>fmt(it.dir==="sig"?AX.vecino.tipSig:AX.vecino.tipAnt,{n:it.n}),
    reveal:it=>fmt(it.dir==="sig"?AX.vecino.revSig:AX.vecino.revAnt,{n:it.n,r:it.r})
  },
  /* ---- completar series ---- */
  serie:{
    okMsgs:AX.serie.ok,
    make(s){ const len=5, step=pick(s.steps,"sp"+s.id), desc=!!s.desc&&Math.random()<.35, span=step*(len-1), lo=s.min, hi=s.max-span;
      let start; if(s.alinear||step>1){ const a=Math.ceil(lo/step), b=Math.floor(hi/step); start=step*R(a,Math.max(a,b)); } else start=R(lo,Math.max(lo,hi));
      let t=range(0,len-1).map(i=>start+step*i); if(desc) t=t.reverse();
      const bi=R(1,len-1), r=t[bi];
      const cand=[r+step,r-step,r+1,r-1,r+2*step,r-2*step].filter((v,i,a)=>v>=0&&v!==r&&!t.includes(v)&&a.indexOf(v)===i);
      const vals=shuffle([r,...shuffle(cand).slice(0,3)]);
      return {skill:s,t,bi,r,step,desc,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const stage=`<div class="slots">${it.t.map((x,i)=>`<span class="sl${i===it.bi?" blank":""}">${i===it.bi?"?":x}</span>`).join("")}</div>`;
      const ops=trimOpts(it,aid);
      return {say:AX.serie.say+(it.step>1&&aid<2?fmt(AX.serie.dea,{paso:it.step}):""),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.serie.tip,
    reveal:it=>fmt(AX.serie.rev,{r:it.r})
  },
  /* ---- los números hasta 100 ---- */
  num100:{
    okMsgs:AX.num100.ok, noVoiceAid:0,
    make(s){ const n=pick(range(s.min,s.max),"n100"+s.id), sw=n<100?(n%10)*10+Math.floor(n/10):0;
      const vals=numOptsG(n,s.min,s.max,4,sw&&sw!==n?[sw]:[]);
      return {skill:s,n,seq:[n],opts:vals.map(numOpt),far:farOf(vals,n)}; },
    view(it,aid,T){
      const g=digs(it.n), ops=trimOpts(it,aid);
      return {say:rnd(AX.num100.say).replace("{n}",it.n),stage:aid===0?bq(g.c,g.d,g.u):"",opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.num100.tip,
    reveal:it=>{ const g=digs(it.n); return fmt(AX.num100.rev,{n:it.n,dd:decs(g.c*10+g.d),uu:unis(g.u)}); }
  },
  /* ---- comparar números de dos cifras ---- */
  cmpg:{
    okMsgs:AX.cmpg.ok,
    make(s){ const modo=pick(["dec","uni","azar"],"cg"+s.id); let a,b;
      if(modo==="dec"){ const t=R(Math.ceil(s.min/10),Math.floor(s.max/10)); a=t*10+R(0,9); b=t*10+R(0,9); }
      else if(modo==="uni"){ const u=R(0,9); a=R(1,9)*10+u; b=R(1,9)*10+u; }
      else { a=R(s.min,s.max); b=R(s.min,s.max); }
      let g=0; while(a===b&&g++<30) b=R(s.min,s.max); if(a===b) b=a===s.max?a-1:a+1;
      const ask=Math.random()<.4?"menos":"mas";
      return {skill:s,a,b,ask,seq:[ask==="mas"?Math.max(a,b):Math.min(a,b)],opts:shuffle([a,b]).map(numOpt)}; },
    view(it,aid,T){
      const ops=it.opts.map(op=>{ const g=digs(op.val);
        return {val:op.val,html:aid>=2?`<div class="bignum" style="font-size:clamp(46px,min(20vw,24vh),110px)">${op.val}</div>`:bq(g.c,g.d,g.u)+(aid===0?`<div class="ocap" style="font-size:clamp(22px,6vmin,44px)">${op.val}</div>`:"")}; });
      const say=aid>=2?AX.cmpg[it.ask]:AX.cmpg[it.ask+"B"];
      return {say,stage:"",opts:ops,wide:true,oc:1,ocl:2}; },
    tip:it=>AX.cmpg.tip,
    reveal:it=>fmt(AX.cmpg.rev,{r:it.seq[0]})
  },
  /* ---- ordenar números (varios toques seguidos) ---- */
  ord:{
    okMsgs:AX.ord.ok,
    make(s){ const dir=Math.random()<.3?"desc":"asc", nums=shuffle(range(s.min,s.max)).slice(0,s.cnt);
      const sorted=nums.slice().sort((x,y)=>dir==="asc"?x-y:y-x);
      return {skill:s,dir,seq:sorted,consume:true,opts:nums.map(v=>({val:v,html:String(v),id:v}))}; },
    view(it,aid,T){
      const stage=`<div class="slots">${it.seq.map((x,i)=>`<span class="sl${i<T.pos?"":" blank"}">${i<T.pos?x:"?"}</span>`).join("")}</div>`;
      return {say:AX.ord[it.dir==="asc"?"asc":"desc"],stage,opts:it.opts,oc:it.opts.length>3?2:3,ocl:it.opts.length}; },
    tip:it=>it.dir==="asc"?AX.ord.tipAsc:AX.ord.tipDesc,
    reveal:it=>fmt(AX.ord.revAsc,{l:it.seq.join(", ")})
  },
  /* ---- decenas y unidades ---- */
  dyu:{
    okMsgs:AX.dyu.ok,
    make(s){ const modo=pick(["num","num","dec","uni"],"dy"+s.id), d=R(1,9), u=Math.random()<.2?0:R(0,9), n=d*10+u;
      let r,vals;
      if(modo==="num"){ r=n; const sw=u*10+d; vals=numOptsG(n,10,99,4,sw!==n&&sw>=10?[sw]:[]); }
      else if(modo==="dec"){ r=d; vals=numOpts(d,1,9,4); }
      else { r=u; vals=numOpts(u,0,9,4); }
      return {skill:s,modo,d,u,n,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {modo,d,u,n}=it, ops=trimOpts(it,aid);
      let stage,say;
      if(modo==="num"){ say=fmt(AX.dyu.num,{dd:decs(d),uu:unis(u)});
        stage=aid<=1?bq(0,d,u):eqtBig(decs(d)+" y "+unis(u)); }
      else { say=fmt(AX.dyu[modo],{n}); stage=`<div class="bignum">${n}</div>`+(aid===0?bq(0,d,u):""); }
      return {say,stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.dyu.tip,
    reveal:it=>fmt(AX.dyu.rev,{n:it.n,dd:decs(it.d),uu:unis(it.u)})
  },
  /* ---- centenas ---- */
  cen:{
    okMsgs:AX.cen.ok,
    make(s){ const modo=pick(["num","cen"],"ce"+s.id), c=R(1,Math.floor(s.max/100)), d=R(0,9), u=R(0,9), n=c*100+d*10+u;
      let r,vals;
      if(modo==="num"){ r=n; const sw=[d*100+c*10+u,u*100+d*10+c].filter(v=>v!==n&&v>=100); vals=numOptsG(n,100,s.max+100,4,sw.slice(0,1).concat([n+100,n-100])); }
      else { r=c; vals=numOpts(c,1,Math.max(5,c+1),4); }
      return {skill:s,modo,c,d,u,n,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {modo,c,d,u,n}=it, ops=trimOpts(it,aid);
      let stage,say;
      if(modo==="num"){ say=fmt(AX.cen.num,{cc:cents(c),dd:decs(d),uu:unis(u)}); stage=aid<=1?bq(c,d,u):eqtBig(cents(c)+", "+decs(d)+" y "+unis(u)); }
      else { say=fmt(AX.cen.cen,{n}); stage=`<div class="bignum">${n}</div>`+(aid===0?bq(c,d,u):""); }
      return {say,stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.cen.tip,
    reveal:it=>fmt(AX.cen.rev,{n:it.n,cc:cents(it.c),dd:decs(it.d),uu:unis(it.u)})
  },
  /* ---- dobles ---- */
  dob:{
    okMsgs:AX.dob.ok,
    make(s){ const n=pick(range(1,s.max),"db"+s.id), r=2*n, o=pick(OBJS,"obj"), vals=numOpts(r,2,2*s.max,4);
      return {skill:s,n,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {n,o}=it, g=(k)=>grupo(objs(o.e,chunks5(n),{nofit:1}),k), ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(fmt(AX.dob.eq,{n})):eqWrap(g("g1")+`<span class="eqop">+</span>`+g("g2")+`<span class="eqop" style="white-space:nowrap">= ?</span>`,2*n+2,aid===0?`<div class="eqt">${n} + ${n} = ?</div>`:"");
      return {say:fmt(aid>=2?AX.dob.say:AX.dob.sayB,{n}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.dob.tip,
    reveal:it=>fmt(AX.dob.rev,{n:it.n,r:it.r})
  },
  /* ---- mitades ---- */
  mit:{
    okMsgs:AX.mit.ok,
    make(s){ const r=pick(range(1,s.max/2),"mt"+s.id), n=2*r, o=pick(OBJS,"obj"), vals=numOpts(r,1,s.max/2,4);
      return {skill:s,n,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {n,r,o}=it, ops=trimOpts(it,aid);
      let stage;
      if(aid===0) stage=eqWrap(grupo(objs(o.e,chunks5(r),{nofit:1}),"g1","🍽️")+grupo(objs(o.e,chunks5(r),{nofit:1}),"g2","🍽️")+`<span class="eqop" style="white-space:nowrap">${n} → ?</span>`,n+4);
      else if(aid===1) stage=eqWrap(grupo(objs(o.e,chunks5(n),{nofit:1}),"g1"),n+2);
      else stage=eqtBig(fmt(AX.mit.eq,{n}));
      return {say:fmt(aid>=2?AX.mit.say:AX.mit.sayB,{n}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.mit.tip,
    reveal:it=>fmt(AX.mit.rev,{n:it.n,r:it.r})
  },
  /* ---- grupos iguales (multiplicar como grupos) ---- */
  grp:{
    okMsgs:AX.grp.ok,
    make(s){ let g,p,x=0; do{ g=R(2,5); p=R(2,5); }while(g*p>s.max&&x++<40); const r=g*p, o=pick(OBJS,"obj"), vals=numOptsG(r,2,s.max+5,4,[r+p,r-p]);
      return {skill:s,g,p,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {g,p,o}=it, ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(fmt(AX.grp.sayT,{g,p}).replace(/\. .*/,"")+" = ?"):eqWrap(range(1,g).map(i=>grupo(objs(o.e,chunks5(p),{nofit:1}),i%2?"g1":"g2","🧺")).join(""),g*p+g*2,aid===0?`<div class="eqt">${range(1,g).map(()=>p).join(" + ")} = ?</div>`:"");
      return {say:aid>=2?fmt(AX.grp.sayT,{g,p}):fmt(AX.grp.say,{g,p,obj:o.p,Cuantos:cuantos(o)}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>fmt(AX.grp.tip,{suma:range(1,it.g).map(()=>it.p).join(" + ")}),
    reveal:it=>fmt(AX.grp.rev,{g:it.g,p:it.p,r:it.r})
  },
  /* ---- repartir en partes iguales ---- */
  rep:{
    okMsgs:AX.rep.ok,
    make(s){ let a,q,x=0; do{ a=R(2,5); q=R(1,4); }while(a*q>s.max&&x++<40); const n=a*q, o=pick(OBJS,"obj"), vals=numOptsG(q,1,5,4,[q+1,q-1]);
      return {skill:s,a,q,n,o,seq:[q],opts:vals.map(numOpt),far:farOf(vals,q)}; },
    view(it,aid,T){
      const {a,q,n,o}=it, ops=trimOpts(it,aid);
      let stage;
      if(aid===0) stage=eqWrap(range(1,a).map(i=>grupo(objs(o.e,chunks5(q),{nofit:1}),i%2?"g1":"g2","🧒")).join(""),n+a*2);
      else if(aid===1) stage=eqWrap(grupo(objs(o.e,chunks5(n),{nofit:1}),"g1")+`<span class="eqop" style="white-space:nowrap">${"🧒".repeat(a)}</span>`,n+a+3);
      else stage=eqtBig(fmt(TX.act.rep.sayT,{n,a}).split(".")[0]);
      return {say:aid>=2?fmt(AX.rep.sayT,{n,a}):fmt(AX.rep.say,{n,a,obj:o.p,Los:o.f?"Las":"Los",Cuantos:cuantos(o)}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.rep.tip,
    reveal:it=>fmt(AX.rep.rev,{n:it.n,a:it.a,r:it.q})
  },
  /* ---- multiplicar: tablas del 2, 5 y 10 ---- */
  mul:{
    okMsgs:AX.mul.ok,
    make(s){ const t=pick(s.tablas,"ml"+s.id), f=R(2,s.fmax), r=t*f, o=pick(OBJS,"obj"), vals=numOptsG(r,t,t*(s.fmax+1),4,[r+t,r-t]);
      return {skill:s,t,f,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {t,f,o}=it, ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(`${f} × ${t} = ?`):eqWrap(range(1,f).map(i=>grupo(objs(o.e,chunks5(t),{nofit:1}),i%2?"g1":"g2")).join(""),f*t+f*2,aid===0?`<div class="eqt">${f} × ${t} = ?</div>`:"");
      return {say:aid>=2?fmt(AX.mul.sayT,{f,t}):fmt(AX.mul.say,{f,t}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>fmt(AX.mul.tip,{t:it.t,f:it.f,suma:range(1,it.f).map(()=>it.t).join(" + ")}),
    reveal:it=>fmt(AX.mul.rev,{f:it.f,t:it.t,r:it.r})
  },
  /* ---- dividir ---- */
  div:{
    okMsgs:AX.div.ok,
    make(s){ const d=pick(s.divisores,"dv"+s.id), q=R(1,s.qmax), n=d*q, o=pick(OBJS,"obj"), vals=numOptsG(q,1,s.qmax+1,4,[q+1,q-1]);
      return {skill:s,d,q,n,o,seq:[q],opts:vals.map(numOpt),far:farOf(vals,q)}; },
    view(it,aid,T){
      const {d,q,n,o}=it, ops=trimOpts(it,aid);
      let stage;
      if(aid===0) stage=eqWrap(range(1,d).map(i=>grupo(objs(o.e,chunks5(q),{nofit:1}),i%2?"g1":"g2")).join(""),n+d*2,`<div class="eqt">${n} ÷ ${d} = ?</div>`);
      else if(aid===1) stage=eqWrap(grupo(objs(o.e,chunks5(n),{nofit:1}),"g1")+`<span class="eqop" style="white-space:nowrap">÷ ${d}</span>`,n+4);
      else stage=eqtBig(`${n} ÷ ${d} = ?`);
      return {say:aid>=2?fmt(AX.div.sayT,{n,d}):fmt(AX.div.say,{n,d,obj:o.p,Los:o.f?"Las":"Los",Cuantos:cuantos(o)}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.div.tip,
    reveal:it=>fmt(AX.div.rev,{n:it.n,d:it.d,r:it.q})
  },
  /* ---- sumas de dos cifras sin llevar ---- */
  sumg:{
    okMsgs:AX.sumg.ok,
    make(s){ const modo=pick([0,1,2],"sg"+s.id); let a,b;
      if(modo===0){ const ta=R(1,8), tb=R(1,Math.min(9,10-ta)); a=ta*10; b=tb*10; }
      else if(modo===1){ const ua=R(0,8); a=R(1,8)*10+ua; b=R(1,9-ua); }
      else { const ua=R(0,8), ub=R(0,9-ua), ta=R(1,7), tb=R(1,Math.min(8,9-ta)); a=ta*10+ua; b=tb*10+ub; if(!ub&&!ua) b+=1; }
      const r=a+b, vals=numOptsG(r,10,s.max,4,[r+10,r-10]);
      return {skill:s,a,b,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {a,b}=it, ga=digs(a), gb=digs(b), ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(`${a} + ${b} = ?`):eqWrap(grupo(bq(0,ga.d,ga.u,{nofit:1}),"g1")+`<span class="eqop">+</span>`+grupo(bq(0,gb.d,gb.u,{nofit:1}),"g2")+`<span class="eqop" style="white-space:nowrap">= ?</span>`,Math.round(((ga.d+gb.d)*.5+(ga.u+gb.u)*.4+4)*1.3),aid===0?`<div class="eqt">${a} + ${b} = ?</div>`:"");
      return {say:aid>=2?fmt(AX.sumg.sayT,{a,b}):fmt(AX.sumg.say,{a,b}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.sumg.tip,
    reveal:it=>fmt(AX.sumg.rev,{a:it.a,b:it.b,r:it.r})
  },
  /* ---- restas de dos cifras sin llevar ---- */
  restag:{
    okMsgs:AX.restag.ok,
    make(s){ let a,b,x=0; do{ const ta=R(1,9), ua=R(0,9), tb=R(0,ta), ub=R(0,ua); a=ta*10+ua; b=tb*10+ub; }while((b<=0||b>=a)&&x++<60); if(b<=0||b>=a){ a=57; b=24; }
      const r=a-b, vals=numOptsG(r,1,s.max,4,[r+10,r-10]);
      return {skill:s,a,b,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {a,b}=it, ga=digs(a), gb=digs(b), ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(`${a} − ${b} = ?`):eqWrap(grupo(bq(0,ga.d,ga.u,{nofit:1,xd:gb.d,xu:gb.u}),"g1"),Math.round((ga.d*.5+ga.u*.4+3)*1.3),aid===0?`<div class="eqt">${a} − ${b} = ?</div>`:"");
      return {say:aid>=2?fmt(AX.restag.sayT,{a,b}):fmt(AX.restag.say,{a,b}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AX.restag.tip,
    reveal:it=>fmt(AX.restag.rev,{a:it.a,b:it.b,r:it.r})
  },
};
Object.assign(TAP_ACTS,NUEVAS);

/* ---- registro de la isla ---- */
const ISLA={id:"numeros",name:"Isla Números",emoji:"🔢",sub:"¡A contar y sumar!",skills:SKILLS_NUMEROS,tap:true,plain:true,
  instrumento:null,entradas:["toque"],
  actividades:TAP_ACTS,
  dom:Gioval.numeros.dom,                              /* botón del panel de adultos y pantallas de preguntas/resumen */
  iniciar(){ Gioval.numeros.iniciar(); },
  informeInicio(kid){ return Gioval.numeros.informeInicio(kid); },
  outro:"Ahora, ¡buscá cosas para contar a tu alrededor!",
  capTail:"Ahora, a jugar con cosas de verdad: ¡contá lo que encuentres! ¡Mañana seguimos!"};
Gioval.islas.registrar(ISLA);
})();
