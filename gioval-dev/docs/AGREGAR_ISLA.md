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
| Opcionales | `dom` (pantallas/botones propios), `iniciar`, `entrar(title)`, `antesDeSesion`, `fin`, `tarjetas(done)`, `notaInforme`. Música los usa porque tiene piano propio. |

### Una actividad por toque (`tap: true`)

- `make(s)`: resuelve **todo lo aleatorio una sola vez** y devuelve el ítem `{ skill:s, seq:[respuestas correctas en orden], opts:[{val, html}] }`.
  Usar `pick(lista, clave)` (no repite el último), `shuffle`, `R(a,b)`, `range(a,b)` (disponibles globalmente).
- `view(it, aid, T)`: cómo se ve y qué se dice. `aid` es el nivel de ayuda (0 más ayuda … 2 sin ayuda). Devuelve
  `{ say, stage, opts, oc, ocl, wide }`.
- `okMsgs`, `tip(it)`, `reveal(it)`: textos de **proceso** ("¡Probaste distinto y salió!"). **Nunca elogio de la persona**
  ("¡qué inteligente!") ni rachas. Tras un error el motor da pistas: 1.er error mensaje, 2.º saca una opción y muestra `tip`,
  3.º muestra la respuesta (`reveal`). En el chequeo semanal no hay ayuda y termina el ítem al primer error.
- Voz: todo lo que se dice sale por `speak()` en es-AR. Escribir frases completas, con signos de apertura (¿ ¡).

### Si la isla no es por toque

Puede traer su propia pantalla y juego (como Música): declarar `dom`, `iniciar`, `entrar`, y en cada actividad
una función `jugar(run, it, ss)` que devuelve una promesa con el resultado. Mirar `js/islas/musica.js`.

## Ejemplo completo: Isla Colores

```js
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
y juega sesiones completas, dominio, desbloqueo, chequeo semanal e informe de la isla nueva. Si el motor empezara a
depender de una isla en particular, esa prueba falla.

Para probar la isla real: sumar al `correr.py` una prueba parecida a la de Números (ver `t_numeros`).

## Cuidado con los datos de los chicos

- Los ids de habilidad (`skills[].id`) son parte del progreso guardado: **no renombrarlos** una vez publicados; si hace
  falta, escribir una migración (ver `almacen.js`, `migraciones`).
- Las habilidades de una isla se guardan en `store.sk["Perfil|id"]`; el registro de práctica en `store.log`; los chequeos
  en `store.checks` con `p: "<id de la isla>"`. No hace falta tocar el esquema para una isla nueva.
