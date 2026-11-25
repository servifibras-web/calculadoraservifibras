"use strict";
/* ISLA COLORES (ejemplo mínimo). Un archivo = una isla. */
(function(){
const COL=[{n:"rojo",e:"🔴"},{n:"azul",e:"🔵"},{n:"verde",e:"🟢"},{n:"amarillo",e:"🟡"},{n:"violeta",e:"🟣"},{n:"naranja",e:"🟠"}];

const SKILLS=[
  {id:"col_nom",name:"Nombrar colores",icon:"🔴",type:"color",max:3,req:[]},
  {id:"col_mas",name:"Más colores",icon:"🌈",type:"color",max:6,req:["col_nom"]},
];

const ACTIVIDADES={
  color:{
    /* mensajes de PROCESO (nunca elogio de la persona) */
    okMsgs:["¡Miraste con atención!","¡Probaste y salió!","¡Fijarse bien ayuda!"],
    /* make: resuelve TODO lo aleatorio una sola vez. seq = respuestas correctas en orden. */
    make(s){
      const c=pick(COL.slice(0,s.max),"col");                 /* pick evita repetir el último */
      const otros=shuffle(COL.slice(0,s.max).filter(x=>x!==c)).slice(0,2);
      const opts=shuffle([c].concat(otros)).map(x=>({val:x.n,html:x.e}));
      return {skill:s,c,seq:[c.n],opts};
    },
    /* view: cómo se ve y qué se dice según la ayuda (aid 0 = más ayuda … 2 = sin ayuda) */
    view(it,aid,T){
      return {say:"Tocá el color "+it.c.n+".",stage:"",opts:it.opts,oc:1,ocl:3};
    },
    tip:it=>"Fijate bien en el nombre. Saqué una opción.",
    reveal:it=>"Mirá, este es el "+it.c.n+"."
  },
};

Gioval.islas.registrar({
  id:"colores",name:"Isla Colores",emoji:"🎨",sub:"¡A mirar colores!",
  skills:SKILLS,
  tap:true,                 /* usa el motor de toques genérico */
  plain:true,               /* sin rachas ni puntos */
  instrumento:null,
  entradas:["toque"],
  actividades:ACTIVIDADES,
  outro:"Ahora, ¡buscá colores a tu alrededor!",
  capTail:"¡Mañana seguimos con los colores!"
});
})();
