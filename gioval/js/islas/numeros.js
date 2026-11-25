"use strict";
/* ============ ISLA NÚMEROS ============
   Lógica universal (contar, comparar, sumar, restar, series, valor posicional, dobles, grupos iguales…); los textos van en las tablas de idiomas.
   Habilidades encadenadas con req; las actividades por toque están abajo. Se registra en Gioval.islas. */
(function(){
/* La escalera de habilidades (31) vive en js/datos/numeros.js: allí el nombre de cada una sale de la tabla de idiomas (numeros.hab.<id>)
   y el id NO cambia nunca (es la clave del progreso). Acá solo está cómo se juega cada tipo de actividad. */
const DN=Gioval.datos.numeros, SKILLS_NUMEROS=DN.ESCALA;

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

/* ============ ACTIVIDADES NUEVAS (escalera por edades) ============
   Mismos contratos que arriba. Los textos están en las tablas de idiomas (numeros.ed.act.<tipo>.* en js/datos/numeros.js): cada frase es
   una clave completa con huecos con nombre; acá no hay español escrito. Convención de ayuda visual (aid):
   0 = dibujo contable + escritura, 1 = solo dibujo, 2 = solo símbolos y voz. */
const AK=(tipo,campo,p)=>t("numeros.ed.act."+tipo+"."+campo,p);
const okDe=tipo=>tl("numeros.ed.act."+tipo+".ok");
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
const eqtBig=x=>`<div class="eqt" style="font-size:clamp(40px,12vmin,96px)">${x}</div>`;
const grupo=(inner,k,icon)=>`<div class="grp ${k||""}">${icon?`<div class="ocap" style="font-size:calc(var(--es,24px)*.8)">${icon}</div>`:""}${inner}</div>`;
const eqWrap=(rows,area,extra)=>`<div class="eq" data-fit="0,0" data-area="${area}"><div class="eqrow">${rows}</div>${extra||""}</div>`;
const sumaDe=(n,k)=>range(1,k).map(()=>n).join(" + ");

const NUEVAS={
  /* ---- el que sigue y el que va antes ---- */
  vecino:{
    get okMsgs(){ return okDe("vecino"); },
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
      return {say:AK("vecino",dir,{n}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("vecino",it.dir==="sig"?"tip_sig":"tip_ant",{n:it.n}),
    reveal:it=>AK("vecino",it.dir==="sig"?"rev_sig":"rev_ant",{n:it.n,r:it.r})
  },
  /* ---- completar series ---- */
  serie:{
    get okMsgs(){ return okDe("serie"); },
    make(s){ const len=5, step=pick(s.steps,"sp"+s.id), desc=!!s.desc&&Math.random()<.35, span=step*(len-1), lo=s.min, hi=s.max-span;
      let start; if(s.alinear||step>1){ const a=Math.ceil(lo/step), b=Math.floor(hi/step); start=step*R(a,Math.max(a,b)); } else start=R(lo,Math.max(lo,hi));
      let fila=range(0,len-1).map(i=>start+step*i); if(desc) fila=fila.reverse();
      const bi=R(1,len-1), r=fila[bi];
      const cand=[r+step,r-step,r+1,r-1,r+2*step,r-2*step].filter((v,i,a)=>v>=0&&v!==r&&!fila.includes(v)&&a.indexOf(v)===i);
      const vals=shuffle([r,...shuffle(cand).slice(0,3)]);
      return {skill:s,t:fila,bi,r,step,desc,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const stage=`<div class="slots">${it.t.map((x,i)=>`<span class="sl${i===it.bi?" blank":""}">${i===it.bi?"?":x}</span>`).join("")}</div>`;
      const ops=trimOpts(it,aid);
      return {say:it.step>1&&aid<2?AK("serie","say_paso",{paso:it.step}):AK("serie","say"),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("serie","tip"),
    reveal:it=>AK("serie","rev",{r:it.r})
  },
  /* ---- los números hasta 100 ---- */
  num100:{
    get okMsgs(){ return okDe("num100"); }, noVoiceAid:0,
    make(s){ const n=pick(range(s.min,s.max),"n100"+s.id), sw=n<100?(n%10)*10+Math.floor(n/10):0;
      const vals=numOptsG(n,s.min,s.max,4,sw&&sw!==n?[sw]:[]);
      return {skill:s,n,seq:[n],opts:vals.map(numOpt),far:farOf(vals,n)}; },
    view(it,aid,T){
      const g=digs(it.n), ops=trimOpts(it,aid);
      return {say:rnd(tl("numeros.ed.act.num100.say",{n:it.n})),stage:aid===0?bq(g.c,g.d,g.u):"",opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("num100","tip"),
    reveal:it=>{ const g=digs(it.n); return AK("num100","rev",{n:it.n,d:g.c*10+g.d,u:g.u}); }
  },
  /* ---- comparar números de dos cifras ---- */
  cmpg:{
    get okMsgs(){ return okDe("cmpg"); },
    make(s){ const modo=pick(["dec","uni","azar"],"cg"+s.id); let a,b;
      if(modo==="dec"){ const t10=R(Math.ceil(s.min/10),Math.floor(s.max/10)); a=t10*10+R(0,9); b=t10*10+R(0,9); }
      else if(modo==="uni"){ const u=R(0,9); a=R(1,9)*10+u; b=R(1,9)*10+u; }
      else { a=R(s.min,s.max); b=R(s.min,s.max); }
      let g=0; while(a===b&&g++<30) b=R(s.min,s.max); if(a===b) b=a===s.max?a-1:a+1;
      const ask=Math.random()<.4?"menos":"mas";
      return {skill:s,a,b,ask,seq:[ask==="mas"?Math.max(a,b):Math.min(a,b)],opts:shuffle([a,b]).map(numOpt)}; },
    view(it,aid,T){
      const ops=it.opts.map(op=>{ const g=digs(op.val);
        return {val:op.val,html:aid>=2?`<div class="bignum" style="font-size:clamp(46px,min(20vw,24vh),110px)">${op.val}</div>`:bq(g.c,g.d,g.u)+(aid===0?`<div class="ocap" style="font-size:clamp(22px,6vmin,44px)">${op.val}</div>`:"")}; });
      const say=AK("cmpg",aid>=2?it.ask:it.ask+"_b");
      return {say,stage:"",opts:ops,wide:true,oc:1,ocl:2}; },
    tip:it=>AK("cmpg","tip"),
    reveal:it=>AK("cmpg","rev",{r:it.seq[0]})
  },
  /* ---- ordenar números (varios toques seguidos) ---- */
  ord:{
    get okMsgs(){ return okDe("ord"); },
    make(s){ const dir=Math.random()<.3?"desc":"asc", nums=shuffle(range(s.min,s.max)).slice(0,s.cnt);
      const sorted=nums.slice().sort((x,y)=>dir==="asc"?x-y:y-x);
      return {skill:s,dir,seq:sorted,consume:true,opts:nums.map(v=>({val:v,html:String(v),id:v}))}; },
    view(it,aid,T){
      const stage=`<div class="slots">${it.seq.map((x,i)=>`<span class="sl${i<T.pos?"":" blank"}">${i<T.pos?x:"?"}</span>`).join("")}</div>`;
      return {say:AK("ord",it.dir),stage,opts:it.opts,oc:it.opts.length>3?2:3,ocl:it.opts.length}; },
    tip:it=>AK("ord",it.dir==="asc"?"tip_asc":"tip_desc"),
    reveal:it=>AK("ord","rev_"+it.dir,{l:it.seq.join(", ")})
  },
  /* ---- decenas y unidades ---- */
  dyu:{
    get okMsgs(){ return okDe("dyu"); },
    make(s){ const modo=pick(["num","num","dec","uni"],"dy"+s.id), d=R(1,9), u=Math.random()<.2?0:R(0,9), n=d*10+u;
      let r,vals;
      if(modo==="num"){ r=n; const sw=u*10+d; vals=numOptsG(n,10,99,4,sw!==n&&sw>=10?[sw]:[]); }
      else if(modo==="dec"){ r=d; vals=numOpts(d,1,9,4); }
      else { r=u; vals=numOpts(u,0,9,4); }
      return {skill:s,modo,d,u,n,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {modo,d,u,n}=it, ops=trimOpts(it,aid);
      let stage,say;
      if(modo==="num"){ say=AK("dyu","num",{d,u}); stage=aid<=1?bq(0,d,u):eqtBig(AK("dyu","eq",{d,u})); }
      else { say=AK("dyu",modo,{n}); stage=`<div class="bignum">${n}</div>`+(aid===0?bq(0,d,u):""); }
      return {say,stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("dyu","tip"),
    reveal:it=>AK("dyu","rev",{n:it.n,d:it.d,u:it.u})
  },
  /* ---- centenas ---- */
  cen:{
    get okMsgs(){ return okDe("cen"); },
    make(s){ const modo=pick(["num","cen"],"ce"+s.id), c=R(1,Math.floor(s.max/100)), d=R(0,9), u=R(0,9), n=c*100+d*10+u;
      let r,vals;
      if(modo==="num"){ r=n; const sw=[d*100+c*10+u,u*100+d*10+c].filter(v=>v!==n&&v>=100); vals=numOptsG(n,100,s.max+100,4,sw.slice(0,1).concat([n+100,n-100])); }
      else { r=c; vals=numOpts(c,1,Math.max(5,c+1),4); }
      return {skill:s,modo,c,d,u,n,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {modo,c,d,u,n}=it, ops=trimOpts(it,aid);
      let stage,say;
      if(modo==="num"){ say=AK("cen","num",{c,d,u}); stage=aid<=1?bq(c,d,u):eqtBig(AK("cen","eq",{c,d,u})); }
      else { say=AK("cen","cen",{n}); stage=`<div class="bignum">${n}</div>`+(aid===0?bq(c,d,u):""); }
      return {say,stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("cen","tip"),
    reveal:it=>AK("cen","rev",{n:it.n,c:it.c,d:it.d,u:it.u})
  },
  /* ---- dobles ---- */
  dob:{
    get okMsgs(){ return okDe("dob"); },
    make(s){ const n=pick(range(1,s.max),"db"+s.id), r=2*n, o=pick(OBJS,"obj"), vals=numOpts(r,2,2*s.max,4);
      return {skill:s,n,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {n,o}=it, g=(k)=>grupo(objs(o.e,chunks5(n),{nofit:1}),k), ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(AK("dob","eq",{n})):eqWrap(g("g1")+`<span class="eqop">+</span>`+g("g2")+`<span class="eqop" style="white-space:nowrap">= ?</span>`,2*n+2,aid===0?`<div class="eqt">${n} + ${n} = ?</div>`:"");
      return {say:aid>=2?AK("dob","say",{n}):AK("dob","say_b",pr(o,{n})),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("dob","tip"),
    reveal:it=>AK("dob","rev",{n:it.n,r:it.r})
  },
  /* ---- mitades ---- */
  mit:{
    get okMsgs(){ return okDe("mit"); },
    make(s){ const r=pick(range(1,s.max/2),"mt"+s.id), n=2*r, o=pick(OBJS,"obj"), vals=numOpts(r,1,s.max/2,4);
      return {skill:s,n,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {n,r,o}=it, ops=trimOpts(it,aid);
      let stage;
      if(aid===0) stage=eqWrap(grupo(objs(o.e,chunks5(r),{nofit:1}),"g1","🍽️")+grupo(objs(o.e,chunks5(r),{nofit:1}),"g2","🍽️")+`<span class="eqop" style="white-space:nowrap">${n} → ?</span>`,n+4);
      else if(aid===1) stage=eqWrap(grupo(objs(o.e,chunks5(n),{nofit:1}),"g1"),n+2);
      else stage=eqtBig(AK("mit","eq",{n}));
      return {say:aid>=2?AK("mit","say",{n}):AK("mit","say_b",pr(o,{n})),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("mit","tip"),
    reveal:it=>AK("mit","rev",{n:it.n,r:it.r})
  },
  /* ---- grupos iguales (multiplicar como grupos) ---- */
  grp:{
    get okMsgs(){ return okDe("grp"); },
    make(s){ let g,p,x=0; do{ g=R(2,5); p=R(2,5); }while(g*p>s.max&&x++<40); const r=g*p, o=pick(OBJS,"obj"), vals=numOptsG(r,2,s.max+5,4,[r+p,r-p]);
      return {skill:s,g,p,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {g,p,o}=it, ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(AK("grp","eq",{grupos:g,p})):eqWrap(range(1,g).map(i=>grupo(objs(o.e,chunks5(p),{nofit:1}),i%2?"g1":"g2","🧺")).join(""),g*p+g*2,aid===0?`<div class="eqt">${sumaDe(p,g)} = ?</div>`:"");
      return {say:aid>=2?AK("grp","say_t",{grupos:g,p}):AK("grp","say",pr(o,{grupos:g,p})),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("grp","tip",{suma:sumaDe(it.p,it.g)}),
    reveal:it=>AK("grp","rev",{grupos:it.g,p:it.p,r:it.r})
  },
  /* ---- repartir en partes iguales ---- */
  rep:{
    get okMsgs(){ return okDe("rep"); },
    make(s){ let a,q,x=0; do{ a=R(2,5); q=R(1,4); }while(a*q>s.max&&x++<40); const n=a*q, o=pick(OBJS,"obj"), vals=numOptsG(q,1,5,4,[q+1,q-1]);
      return {skill:s,a,q,n,o,seq:[q],opts:vals.map(numOpt),far:farOf(vals,q)}; },
    view(it,aid,T){
      const {a,q,n,o}=it, ops=trimOpts(it,aid);
      let stage;
      if(aid===0) stage=eqWrap(range(1,a).map(i=>grupo(objs(o.e,chunks5(q),{nofit:1}),i%2?"g1":"g2","🧒")).join(""),n+a*2);
      else if(aid===1) stage=eqWrap(grupo(objs(o.e,chunks5(n),{nofit:1}),"g1")+`<span class="eqop" style="white-space:nowrap">${"🧒".repeat(a)}</span>`,n+a+3);
      else stage=eqtBig(AK("rep","eq",{n,a}));
      return {say:aid>=2?AK("rep","say_t",{n,a}):AK("rep","say",pr(o,{n,a})),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("rep","tip"),
    reveal:it=>AK("rep","rev",{n:it.n,a:it.a,r:it.q})
  },
  /* ---- multiplicar: tablas del 2, 5 y 10 ---- */
  mul:{
    get okMsgs(){ return okDe("mul"); },
    make(s){ const tb=pick(s.tablas,"ml"+s.id), f=R(2,s.fmax), r=tb*f, o=pick(OBJS,"obj"), vals=numOptsG(r,tb,tb*(s.fmax+1),4,[r+tb,r-tb]);
      return {skill:s,tb,f,r,o,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {tb,f,o}=it, ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(AK("mul","eq",{f,t:tb})):eqWrap(range(1,f).map(i=>grupo(objs(o.e,chunks5(tb),{nofit:1}),i%2?"g1":"g2")).join(""),f*tb+f*2,aid===0?`<div class="eqt">${AK("mul","eq",{f,t:tb})}</div>`:"");
      return {say:aid>=2?AK("mul","say_t",{f,t:tb}):AK("mul","say",{f,t:tb}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("mul","tip",{t:it.tb,f:it.f,suma:sumaDe(it.tb,it.f)}),
    reveal:it=>AK("mul","rev",{f:it.f,t:it.tb,r:it.r})
  },
  /* ---- dividir ---- */
  div:{
    get okMsgs(){ return okDe("div"); },
    make(s){ const d=pick(s.divisores,"dv"+s.id), q=R(1,s.qmax), n=d*q, o=pick(OBJS,"obj"), vals=numOptsG(q,1,s.qmax+1,4,[q+1,q-1]);
      return {skill:s,d,q,n,o,seq:[q],opts:vals.map(numOpt),far:farOf(vals,q)}; },
    view(it,aid,T){
      const {d,q,n,o}=it, ops=trimOpts(it,aid);
      let stage;
      if(aid===0) stage=eqWrap(range(1,d).map(i=>grupo(objs(o.e,chunks5(q),{nofit:1}),i%2?"g1":"g2")).join(""),n+d*2,`<div class="eqt">${n} ÷ ${d} = ?</div>`);
      else if(aid===1) stage=eqWrap(grupo(objs(o.e,chunks5(n),{nofit:1}),"g1")+`<span class="eqop" style="white-space:nowrap">÷ ${d}</span>`,n+4);
      else stage=eqtBig(`${n} ÷ ${d} = ?`);
      return {say:aid>=2?AK("div","say_t",{n,d}):AK("div","say",pr(o,{n,d})),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("div","tip"),
    reveal:it=>AK("div","rev",{n:it.n,d:it.d,r:it.q})
  },
  /* ---- sumas de dos cifras sin llevar ---- */
  sumg:{
    get okMsgs(){ return okDe("sumg"); },
    make(s){ const modo=pick([0,1,2],"sg"+s.id); let a,b;
      if(modo===0){ const ta=R(1,8), tb=R(1,Math.min(9,10-ta)); a=ta*10; b=tb*10; }
      else if(modo===1){ const ua=R(0,8); a=R(1,8)*10+ua; b=R(1,9-ua); }
      else { const ua=R(0,8), ub=R(0,9-ua), ta=R(1,7), tb=R(1,Math.min(8,9-ta)); a=ta*10+ua; b=tb*10+ub; if(!ub&&!ua) b+=1; }
      const r=a+b, vals=numOptsG(r,10,s.max,4,[r+10,r-10]);
      return {skill:s,a,b,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {a,b}=it, ga=digs(a), gb=digs(b), ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(`${a} + ${b} = ?`):eqWrap(grupo(bq(0,ga.d,ga.u,{nofit:1}),"g1")+`<span class="eqop">+</span>`+grupo(bq(0,gb.d,gb.u,{nofit:1}),"g2")+`<span class="eqop" style="white-space:nowrap">= ?</span>`,Math.round(((ga.d+gb.d)*.5+(ga.u+gb.u)*.4+4)*1.3),aid===0?`<div class="eqt">${a} + ${b} = ?</div>`:"");
      return {say:AK("sumg",aid>=2?"say_t":"say",{a,b}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("sumg","tip"),
    reveal:it=>AK("sumg","rev",{a:it.a,b:it.b,r:it.r})
  },
  /* ---- restas de dos cifras sin llevar ---- */
  restag:{
    get okMsgs(){ return okDe("restag"); },
    make(s){ let a,b,x=0; do{ const ta=R(1,9), ua=R(0,9), tb=R(0,ta), ub=R(0,ua); a=ta*10+ua; b=tb*10+ub; }while((b<=0||b>=a)&&x++<60); if(b<=0||b>=a){ a=57; b=24; }
      const r=a-b, vals=numOptsG(r,1,s.max,4,[r+10,r-10]);
      return {skill:s,a,b,r,seq:[r],opts:vals.map(numOpt),far:farOf(vals,r)}; },
    view(it,aid,T){
      const {a,b}=it, ga=digs(a), gb=digs(b), ops=trimOpts(it,aid);
      const stage=aid>=2?eqtBig(`${a} − ${b} = ?`):eqWrap(grupo(bq(0,ga.d,ga.u,{nofit:1,xd:gb.d,xu:gb.u}),"g1"),Math.round((ga.d*.5+ga.u*.4+3)*1.3),aid===0?`<div class="eqt">${a} − ${b} = ?</div>`:"");
      return {say:AK("restag",aid>=2?"say_t":"say",{a,b}),stage,opts:ops,oc:ocN(ops),ocl:ocN(ops)}; },
    tip:it=>AK("restag","tip"),
    reveal:it=>AK("restag","rev",{a:it.a,b:it.b,r:it.r})
  },
};
Object.assign(TAP_ACTS,NUEVAS);

const ISLA={id:"numeros",emoji:"🔢",skills:SKILLS_NUMEROS,tap:true,plain:true,
  get name(){ return t("numeros.nombre"); }, get sub(){ return t("numeros.sub"); },
  instrumento:null,entradas:["toque"],
  actividades:TAP_ACTS,
  dom:Gioval.numeros.dom,                              /* botón del panel de adultos y pantallas de preguntas/resumen */
  iniciar(){ Gioval.numeros.iniciar(); },
  informeInicio(kid){ return Gioval.numeros.informeInicio(kid); },
  get outro(){ return t("numeros.outro"); },
  get capTail(){ return t("numeros.cola_tope"); }};
Gioval.islas.registrar(ISLA);
})();
