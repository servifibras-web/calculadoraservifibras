"use strict";
/* ============ ISLA NÚMEROS ============
   Lógica universal (contar, comparar, sumar, restar) + textos en español (es-AR).
   Habilidades encadenadas con req; las actividades por toque están abajo. Se registra en Gioval.islas. */
(function(){
const SKILLS_NUMEROS=[
  {id:"num_c10",name:"Contar hasta 10",icon:"🍎🍎🍎",type:"count",min:1,max:10,req:[]},
  {id:"num_r10",name:"Reconocer los números",icon:"7️⃣",type:"numrec",min:1,max:10,req:["num_c10"]},
  {id:"num_may",name:"Más y menos",icon:"⚖️",type:"cmp",max:10,req:["num_r10"]},
  {id:"num_add5",name:"Sumas hasta 5",icon:"➕",type:"add",min:2,max:5,req:["num_r10"]},
  {id:"num_sub5",name:"Restas hasta 5",icon:"➖",type:"sub",min:2,max:5,req:["num_add5"]},
  {id:"num_c20",name:"Contar hasta 20",icon:"🔢",type:"count",min:6,max:20,req:["num_c10","num_may"]},
  {id:"num_add10",name:"Sumas hasta 10",icon:"➕🔟",type:"add",min:6,max:10,req:["num_add5","num_may"]},
  {id:"num_sub10",name:"Restas hasta 10",icon:"➖🔟",type:"sub",min:6,max:10,req:["num_sub5","num_add10"]},
  {id:"num_r20",name:"Los números hasta 20",icon:"2️⃣0️⃣",type:"numrec",min:8,max:20,req:["num_c20"]},
];

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

const ISLA={id:"numeros",name:"Isla Números",emoji:"🔢",sub:"¡A contar y sumar!",skills:SKILLS_NUMEROS,tap:true,plain:true,
  instrumento:null,entradas:["toque"],
  actividades:TAP_ACTS,
  outro:"Ahora, ¡buscá cosas para contar a tu alrededor!",
  capTail:"Ahora, a jugar con cosas de verdad: ¡contá lo que encuentres! ¡Mañana seguimos!"};
Gioval.islas.registrar(ISLA);
})();
