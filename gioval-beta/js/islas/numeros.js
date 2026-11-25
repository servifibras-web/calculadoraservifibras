"use strict";
/* ============ ISLA NÚMEROS ============
   Lógica universal (contar, comparar, sumar, restar) + textos en español (es-AR).
   Habilidades encadenadas con req; las actividades por toque están abajo. Se registra en Gioval.islas. */
(function(){
/* el nombre de cada habilidad sale de la tabla de idiomas (numeros.hab.<id>); el id NO cambia nunca (es la clave del progreso) */
const sk=(id,o)=>Object.defineProperty({id,...o},"name",{get:()=>t("numeros.hab."+id),enumerable:true});
const SKILLS_NUMEROS=[
  sk("num_c10",{icon:"🍎🍎🍎",type:"count",min:1,max:10,req:[]}),
  sk("num_r10",{icon:"7️⃣",type:"numrec",min:1,max:10,req:["num_c10"]}),
  sk("num_may",{icon:"⚖️",type:"cmp",max:10,req:["num_r10"]}),
  sk("num_add5",{icon:"➕",type:"add",min:2,max:5,req:["num_r10"]}),
  sk("num_sub5",{icon:"➖",type:"sub",min:2,max:5,req:["num_add5"]}),
  sk("num_c20",{icon:"🔢",type:"count",min:6,max:20,req:["num_c10","num_may"]}),
  sk("num_add10",{icon:"➕🔟",type:"add",min:6,max:10,req:["num_add5","num_may"]}),
  sk("num_sub10",{icon:"➖🔟",type:"sub",min:6,max:10,req:["num_sub5","num_add10"]}),
  sk("num_r20",{icon:"2️⃣0️⃣",type:"numrec",min:8,max:20,req:["num_c20"]}),
];

/* ---- actividades por toque de esta isla ---- (el motor de toques es genérico: js/core/actividades.js)
   Una actividad "tap" define:
     make(s)            -> ítem con todo lo aleatorio ya resuelto: {skill, seq:[respuestas en orden], opts:[{val,html}], ...}
     view(it,aid,T)     -> {say, stage, opts, oc, ocl, wide, cls} según el nivel de ayuda aid (0 más ayuda … 2 sin ayuda)
     okMsgs/tip/reveal  -> textos de proceso (nunca elogio de la persona)
     stageTap(it,T,i)   -> (opcional) toque sobre el dibujo del escenario
   El motor (tapItem/tapPick) se ocupa de errores, ayudas progresivas, chequeo sin ayuda y registro. */
/* Todo lo que depende del idioma (palabras de los números, sustantivos con género y plural) sale de js/i18n/<idioma>.js.
   Cada frase es una clave COMPLETA con huecos ({g}, {objetos}, {a_palabras}...): no se arman frases pegando pedazos. */
const NW=(n,g)=>Gioval.i18n.numeroEnPalabras(n,{g});             /* número en palabras; con g "m"/"f" el uno sale un/una */
const OBJS=[
  {id:"manzana",e:"🍎"},{id:"estrella",e:"⭐"},{id:"auto",e:"🚗"},
  {id:"pez",e:"🐟"},{id:"flor",e:"🌸"},{id:"globo",e:"🎈"},
  {id:"perro",e:"🐶"},{id:"frutilla",e:"🍓"},{id:"pelota",e:"⚽"},
  {id:"mariposa",e:"🦋"},{id:"galletita",e:"🍪"},{id:"tortuga",e:"🐢"},
];
const sust=o=>Gioval.i18n.dato("numeros.objetos")[o.id];          /* { one, other, g } del idioma actual */
const forma=(o,n)=>{ const d=sust(o); return d[Gioval.i18n.categoriaPlural(n)]||d.other; };
const pr=(o,x)=>Object.assign({g:sust(o).g,objetos:forma(o,2)},x);
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
const TAP_ACTS={
  count:{
    get okMsgs(){ return tl("numeros.count.ok"); },
    make(s){ const n=pick(range(s.min,s.max),"cn"+s.id), o=pick(OBJS,"obj");
      const vals=numOpts(n,1,Math.max(s.max,n+1),4); const far=vals.slice().sort((a,b)=>Math.abs(b-n)-Math.abs(a-n))[0];
      return {skill:s,n,o,seq:[n],opts:vals.map(numOpt),far,plan0:chunks5(n),plan2:chunksRnd(n)}; },
    view(it,aid,T){
      const tapOn=(aid===0||T.help)&&!S.check, plan=aid>=2?it.plan2:it.plan0;
      let ops=it.opts; if(aid===0&&ops.length>3) ops=ops.filter(o=>o.val!==it.far);
      return {say:t(tapOn?"numeros.count.say_toca":"numeros.count.say",pr(it.o)),
        stage:objs(it.o.e,plan,{cnt:tapOn?T.cnt:null}), opts:ops, oc:ops.length===3?3:2, ocl:ops.length===3?3:2}; },
    stageTap(it,T,i){ if(S.check||!(T.aid===0||T.help)||T.cnt.includes(i)) return; T.cnt.push(i); speak(NW(T.cnt.length)); tapRender(); },
    tip:it=>t("numeros.count.tip"),
    reveal:it=>t("numeros.count.reveal",{n_palabras:NW(it.n)})
  },
  numrec:{
    get okMsgs(){ return tl("numeros.rec.ok"); },
    noVoiceAid:0,
    make(s){ const n=pick(range(s.min,s.max),"nr"+s.id), o=pick(OBJS,"obj");
      const grp=s.max<=10&&Math.random()<.4;
      const vals=numOpts(n,1,s.max,grp?3:4);
      return {skill:s,n,o,grp,seq:[n],opts:vals.map(v=>({val:v,html:grp?objs(o.e,chunks5(v),{extra:0}):String(v)})),far:vals.slice().sort((a,b)=>Math.abs(b-n)-Math.abs(a-n))[0],plan:chunks5(n)}; },
    view(it,aid,T){
      if(it.grp) return {say:t("numeros.rec.say_grupo",{n_palabras:NW(it.n)}),stage:`<div class="bignum">${it.n}</div>`,sm:true,opts:it.opts,wide:true,oc:1,ocl:3};
      let ops=it.opts; if(aid===0&&ops.length>3) ops=ops.filter(o=>o.val!==it.far);
      return {say:rnd(tl("numeros.rec.say",{n_palabras:NW(it.n)})),
        stage:aid===0?objs("🔵",it.plan):"", opts:ops, oc:ops.length===3?3:2, ocl:ops.length===3?3:2}; },
    tip:it=>t("numeros.rec.tip"),
    reveal:it=>t("numeros.rec.reveal",{n_palabras:NW(it.n)})
  },
  cmp:{
    get okMsgs(){ return tl("numeros.cmp.ok"); },
    make(s){ let a=R(1,s.max),b=R(1,s.max),g=0; while(a===b&&g++<20) b=R(1,s.max); if(a===b) b=a===s.max?a-1:a+1;
      const o=pick(OBJS,"obj"), ask=Math.random()<.4?"menos":"mas";
      return {skill:s,a,b,o,ask,seq:[ask==="mas"?Math.max(a,b):Math.min(a,b)],opts:shuffle([a,b]).map(numOpt)}; },
    view(it,aid,T){
      const ops=it.opts.map(op=>({val:op.val,html:aid>=2?`<div class="bignum" style="font-size:clamp(50px,min(22vw,26vh),120px)">${op.val}</div>`:objs(it.o.e,chunks5(op.val),{cap:aid===0?op.val:"",extra:aid===0?1:0})}));
      const mas=it.ask==="mas", say=aid>=2?t(mas?"numeros.cmp.say_mas":"numeros.cmp.say_menos"):t(mas?"numeros.cmp.say_objs_mas":"numeros.cmp.say_objs_menos",pr(it.o));
      return {say,stage:"",opts:ops,wide:true,oc:1,ocl:2}; },
    tip:it=>t(it.ask==="mas"?"numeros.cmp.tip_mas":"numeros.cmp.tip_menos"),
    reveal:it=>t(it.ask==="mas"?"numeros.cmp.reveal_mas":"numeros.cmp.reveal_menos",{n_palabras:NW(it.seq[0])})
  },
  add:{
    get okMsgs(){ return tl("numeros.add.ok"); },
    make(s){ const c=pick(range(s.min,s.max),"ad"+s.id), a=R(1,c-1), b=c-a, o=pick(OBJS,"obj");
      return {skill:s,a,b,c,o,seq:[c],opts:numOpts(c,1,s.max,4).map(numOpt)}; },
    view(it,aid,T){
      const {a,b,o}=it, g=(n,k)=>`<div class="grp ${k}">${objs(o.e,chunks5(n),{nofit:1})}</div>`;
      const stage=aid>=2?`<div class="eqt" style="font-size:clamp(46px,14vmin,110px)">${a} + ${b} = ?</div>`
        :`<div class="eq" data-fit="0,0" data-area="${a+b+2}"><div class="eqrow">${g(a,"g1")}<span class="eqop">+</span>${g(b,"g2")}<span class="eqop" style="white-space:nowrap">= ?</span></div>${aid===0?`<div class="eqt">${a} + ${b} = ?</div>`:""}</div>`;
      const say=aid>=2?t("numeros.add.say_sin_ayuda",{a_palabras:NW(a),b_palabras:NW(b)}):t(b===1?"numeros.add.say_uno":"numeros.add.say",pr(o,{a,a_g:NW(a,sust(o).g),a_palabras:NW(a),b_palabras:NW(b),objetos_a:forma(o,a)}));
      return {say,stage,opts:it.opts,oc:2,ocl:2}; },
    tip:it=>t("numeros.add.tip"),
    reveal:it=>t("numeros.add.reveal",{a_palabras:NW(it.a),b_palabras:NW(it.b),c_palabras:NW(it.c)})
  },
  sub:{
    get okMsgs(){ return tl("numeros.sub.ok"); },
    make(s){ const a=pick(range(s.min,s.max),"sb"+s.id), b=R(1,a-1), c=a-b, o=pick(OBJS,"obj");
      return {skill:s,a,b,c,o,seq:[c],opts:numOpts(c,1,s.max,4).map(numOpt)}; },
    view(it,aid,T){
      const {a,b,o}=it;
      const stage=aid>=2?`<div class="eqt" style="font-size:clamp(46px,14vmin,110px)">${a} − ${b} = ?</div>`
        :`<div class="eq" data-fit="0,0" data-area="${a+2}"><div class="eqrow"><div class="grp">${objs(o.e,chunks5(a),{nofit:1,x:b})}</div></div>${aid===0?`<div class="eqt">${a} − ${b} = ?</div>`:""}</div>`;
      const say=aid>=2?t("numeros.sub.say_sin_ayuda",{a_palabras:NW(a),b_palabras:NW(b)}):t(b===1?"numeros.sub.say_uno":"numeros.sub.say",pr(o,{a,a_g:NW(a,sust(o).g),a_palabras:NW(a),b_palabras:NW(b),objetos_a:forma(o,a)}));
      return {say,stage,opts:it.opts,oc:2,ocl:2}; },
    tip:it=>t("numeros.sub.tip"),
    reveal:it=>t("numeros.sub.reveal",{a_palabras:NW(it.a),b_palabras:NW(it.b),c_palabras:NW(it.c)})
  },
};

const ISLA={id:"numeros",emoji:"🔢",skills:SKILLS_NUMEROS,tap:true,plain:true,
  get name(){ return t("numeros.nombre"); }, get sub(){ return t("numeros.sub"); },
  instrumento:null,entradas:["toque"],
  actividades:TAP_ACTS,
  get outro(){ return t("numeros.outro"); },
  get capTail(){ return t("numeros.cola_tope"); }};
Gioval.islas.registrar(ISLA);
})();
