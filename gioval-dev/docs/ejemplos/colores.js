"use strict";
/* ISLA COLORES (ejemplo mínimo). Un archivo = una isla. Los textos van en tablas por idioma (Gioval.i18n.agregar);
   el código solo pide frases completas con t("clave", {huecos}). */
(function(){
/* --- textos por idioma: es-AR es el idioma base (obligatorio); los demás son opcionales y caen a es-AR --- */
Gioval.i18n.agregar("es-AR",{
  "colores.nombre":"Isla Colores","colores.sub":"¡A mirar colores!",
  "colores.hab.col_nom":"Nombrar colores","colores.hab.col_mas":"Más colores",
  "colores.nombres":{rojo:"rojo",azul:"azul",verde:"verde",amarillo:"amarillo",violeta:"violeta",naranja:"naranja"},
  "colores.ok":["¡Miraste con atención!","¡Probaste y salió!","¡Fijarse bien ayuda!"],
  "colores.say":"Tocá el color {color}.",
  "colores.tip":"Fijate bien en el nombre. Saqué una opción.",
  "colores.reveal":"Mirá, este es el {color}.",
  "colores.outro":"Ahora, ¡buscá colores a tu alrededor!",
  "colores.cola_tope":"¡Mañana seguimos con los colores!",
});
Gioval.i18n.agregar("en",{
  "colores.nombre":"Colors Island","colores.sub":"Let's look at colors!",
  "colores.hab.col_nom":"Name the colors","colores.hab.col_mas":"More colors",
  "colores.nombres":{rojo:"red",azul:"blue",verde:"green",amarillo:"yellow",violeta:"purple",naranja:"orange"},
  "colores.ok":["You looked carefully!","You tried and it worked!","Looking closely helps!"],
  "colores.say":"Tap the color {color}.",
  "colores.tip":"Look carefully at the name. I removed one option.",
  "colores.reveal":"Look, this is {color}.",
  "colores.outro":"Now, go look for colors around you!",
  "colores.cola_tope":"See you tomorrow with more colors!",
});

const COL=[{id:"rojo",e:"🔴"},{id:"azul",e:"🔵"},{id:"verde",e:"🟢"},{id:"amarillo",e:"🟡"},{id:"violeta",e:"🟣"},{id:"naranja",e:"🟠"}];
const nombre=c=>Gioval.i18n.dato("colores.nombres")[c.id];

/* el id de la habilidad NO se traduce ni se cambia (es la clave del progreso); el nombre sale de la tabla */
const sk=(id,o)=>Object.defineProperty({id,...o},"name",{get:()=>t("colores.hab."+id),enumerable:true});
const SKILLS=[
  sk("col_nom",{icon:"🔴",type:"color",max:3,req:[]}),
  sk("col_mas",{icon:"🌈",type:"color",max:6,req:["col_nom"]}),
];

const ACTIVIDADES={
  color:{
    /* mensajes de PROCESO (nunca elogio de la persona) */
    get okMsgs(){ return tl("colores.ok"); },
    /* make: resuelve TODO lo aleatorio una sola vez. seq = respuestas correctas en orden. */
    make(s){
      const c=pick(COL.slice(0,s.max),"col");                 /* pick evita repetir el último */
      const otros=shuffle(COL.slice(0,s.max).filter(x=>x!==c)).slice(0,2);
      const opts=shuffle([c].concat(otros)).map(x=>({val:x.id,html:x.e}));
      return {skill:s,c,seq:[c.id],opts};
    },
    /* view: cómo se ve y qué se dice según la ayuda (aid 0 = más ayuda … 2 = sin ayuda) */
    view(it,aid,T){
      return {say:t("colores.say",{color:nombre(it.c)}),stage:"",opts:it.opts,oc:1,ocl:3};
    },
    tip:it=>t("colores.tip"),
    reveal:it=>t("colores.reveal",{color:nombre(it.c)})
  },
};

Gioval.islas.registrar({
  id:"colores",emoji:"🎨",
  get name(){ return t("colores.nombre"); }, get sub(){ return t("colores.sub"); },
  skills:SKILLS,
  tap:true,                 /* usa el motor de toques genérico */
  plain:true,               /* sin rachas ni puntos */
  instrumento:null,
  entradas:["toque"],
  actividades:ACTIVIDADES,
  get outro(){ return t("colores.outro"); },
  get capTail(){ return t("colores.cola_tope"); }
});
})();
