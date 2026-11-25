# Cómo agregar una isla

Una isla nueva es **un archivo** en `gioval/js/islas/`, **una línea** en `gioval/index.html` y **una línea** en la lista
de precarga de `gioval/sw.js`. El motor (`js/core/`) no nombra ninguna isla y no se toca: sesión diaria, repaso
espaciado, dificultad adaptativa, chequeo semanal, logros, informe para adultos, tope de tiempo, mapa y respaldo
funcionan solos con lo que la isla declara.

El contenido (habilidades, textos, listas de palabras) vive en el archivo de la isla; el código genérico no lleva
contenido pedagógico. No hay paso de compilación.

## Los 4 pasos

1. Crear `gioval/js/islas/<nombre>.js` (ver el ejemplo completo abajo; también está en `gioval-dev/docs/ejemplos/colores.js`).
2. En `gioval/index.html`, después de la última isla:
   `<script src="js/islas/<nombre>.js"></script>`
3. En `gioval/sw.js`, en la lista `F`, agregar `"js/islas/<nombre>.js"` (si falta, la app no funciona sin conexión y
   la prueba automática "sw: precarga TODOS los archivos" falla).
4. Si la isla figuraba como "Pronto" en `gioval/js/datos/proximas.js`, sacarla de esa lista.
   Subir `gioval/js/version.js` (un número) para que los teléfonos reciban el aviso "Hay una versión nueva".

## Qué declara una isla (`Gioval.islas.registrar({...})`)

| Campo | Para qué |
|---|---|
| `id`, `name`, `emoji`, `sub` | Identidad y tarjeta del mapa. `id` también marca los chequeos semanales (`checks[...].p`). |
| `skills` | Lista de habilidades `{ id, name, icon, type, req:[ids previos], ...parámetros }`. `req` arma la cadena de desbloqueo; `type` elige la actividad. |
| `actividades` | `{ <type>: {...} }`, una por tipo de habilidad (ver abajo). |
| `tap: true` | Usa el motor de toques genérico (`js/core/actividades.js`): ayudas progresivas, chequeo sin ayuda, registro. |
| `plain: true` | Sin rachas ni puntos adictivos (el criterio de la casa). |
| `instrumento`, `entradas` | `instrumento:"piano"` o `null`; `entradas:["toque"]`, `["nota","toque"]`, etc. Ver `ENTRADAS_Y_SONIDO.md`. |
| `outro`, `capTail` | Frase de cierre de la sesión y del tope diario. |
| Opcionales | `dom` (pantallas/botones propios), `iniciar`, `entrar(title)`, `antesDeSesion`, `fin`, `tarjetas(done)`, `informe(kid)`, `notaInforme`. Si la isla trae su propia pantalla de juego, la barra de progreso lleva la clase `prog` (el motor redibuja todas). Música los usa porque tiene piano propio. |

### Una actividad por toque (`tap: true`)

- `make(s)`: resuelve **todo lo aleatorio una sola vez** y devuelve el ítem `{ skill:s, seq:[respuestas correctas en orden], opts:[{val, html}] }`.
  Usar `pick(lista, clave)` (no repite el último), `shuffle`, `R(a,b)`, `range(a,b)` (disponibles globalmente).
- `view(it, aid, T)`: cómo se ve y qué se dice. `aid` es el nivel de ayuda (0 más ayuda … 2 sin ayuda). Devuelve
  `{ say, stage, opts, oc, ocl, wide }`.
- `okMsgs`, `tip(it)`, `reveal(it)`: textos de **proceso** ("¡Probaste distinto y salió!"). **Nunca elogio de la persona**
  ("¡qué inteligente!") ni rachas. Tras un error el motor da pistas: 1.er error mensaje, 2.º saca una opción y muestra `tip`,
  3.º muestra la respuesta (`reveal`). En el chequeo semanal no hay ayuda y termina el ítem al primer error.
- **Textos e idiomas:** nada de español escrito en el código. Cada frase es una clave de la tabla del idioma
  (`t("colores.say", { color })`, o `rnd(tl("colores.ok"))` para una lista de variantes). La isla suma sus textos con
  `Gioval.i18n.agregar("es-AR", {...})` (idioma base, obligatorio) y, si quiere, `agregar("en", {...})`; lo que falte en otro idioma
  cae a es-AR. Las frases son COMPLETAS con huecos con nombre, nunca pedazos pegados (el orden, el género y los plurales cambian
  de un idioma a otro): ver `docs/AGREGAR_IDIOMA.md`. El nombre de cada habilidad sale de la tabla con un getter; su `id` no se traduce.
- Voz: todo lo que se dice sale por `speak()` (audio grabado → voz del aparato en el idioma elegido → solo texto).

### Informe propio de la isla (opcional)

Una isla puede declarar `informe(kid)`: devuelve una lista de líneas de texto que el informe para adultos agrega antes de
"CHEQUEOS SIN AYUDA" (Ritmo lo usa para la regularidad en milisegundos). El motor no sabe nada de lo que contiene. Los textos de ese
bloque también van en la tabla del idioma.

### Si la isla no es por toque

Puede traer su propia pantalla y juego (como Música): declarar `dom`, `iniciar`, `entrar`, y en cada actividad
una función `jugar(run, it, ss)` que devuelve una promesa con el resultado. Mirar `js/islas/musica.js`.

## Ejemplo completo: Isla Colores

```js
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
```

En `index.html`:

```html
<script src="js/islas/numeros.js"></script>
<script src="js/islas/colores.js"></script>   <!-- línea nueva -->
```

En `sw.js`:

```js
  "js/islas/numeros.js",
  "js/islas/colores.js"];   // línea nueva
```

## Cómo se comprueba

`python3 gioval-dev/tests/correr.py` incluye la prueba **"agregar una isla"**: copia la app a una carpeta temporal,
agrega `docs/ejemplos/colores.js` con esas dos líneas (sin tocar `js/core/`, y verifica que sea byte a byte idéntico),
y juega sesiones completas, dominio, desbloqueo, chequeo semanal e informe de la isla nueva, también en inglés. Si el motor empezara a
depender de una isla en particular, esa prueba falla.

El mismo ejemplo se prueba en inglés. Para probar la isla real: sumar al `correr.py` una prueba parecida a la de Números (ver `t_numeros`).

## Cuidado con los datos de los chicos

- Los ids de habilidad (`skills[].id`) son parte del progreso guardado: **no renombrarlos** una vez publicados; si hace
  falta, escribir una migración (ver `almacen.js`, `migraciones`).
- Las habilidades de una isla se guardan en `store.sk["Perfil|id"]`; el registro de práctica en `store.log`; los chequeos
  en `store.checks` con `p: "<id de la isla>"`. No hace falta tocar el esquema para una isla nueva.
