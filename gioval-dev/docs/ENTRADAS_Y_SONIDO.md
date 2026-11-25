# Entradas y sonido

Las actividades no hablan directamente con el micrófono ni con la pantalla, ni saben cómo suena el piano. Piden
"qué entrada necesito" a un registro y escuchan eventos con un formato común. Así se pueden sumar un teclado MIDI,
detector de palmas o instrumentos con muestras sin tocar las islas ni el motor.

## Entradas (`js/core/entrada/`)

### Eventos

| Evento | Campos | Quién lo emite |
|---|---|---|
| `{ tipo:"nota" }` | `midi`, `t`, `fuerza` | micrófono (YIN, una nota por vez); MIDI (reservado) |
| `{ tipo:"golpe" }` | `t`, `fuerza` | detector de golpes/palmas (reservado) |
| `{ tipo:"acorde" }` | `notas:[midi…]`, `t` | cromagrama o MIDI (reservado) |
| `{ tipo:"toque" }` | `midi?`, `tecla?`, `x?`, `y?`, `t` | toque en pantalla |

`t` es `performance.now()` en ms; `fuerza` va de 0 a 1.

### API (`Gioval.entrada`)

```js
Gioval.entrada.registrarProveedor({ id, tipos:["nota"], disponible(), activo, iniciar(opts), detener() });
Gioval.entrada.suscribir("nota", ev => {...});     // devuelve una función para darse de baja; "*" escucha todo
Gioval.entrada.emitir({ tipo:"nota", midi:60, fuerza:.7 });
Gioval.entrada.necesito(["nota","golpe"]);          // -> { disponibles:["nota"], faltan:["golpe"] }
Gioval.entrada.quien("nota");                       // proveedores que pueden dar ese tipo
```

Una isla declara lo que usa al registrarse: `{ instrumento:"piano", entradas:["nota","toque"] }`. Con
`necesito(isla.entradas)` el motor/UI puede avisar a un adulto cuando falta algo (por ejemplo, sin micrófono).

### Proveedores hoy

| Archivo | Estado |
|---|---|
| `toque.js` | Implementado. Siempre disponible. La interfaz llama `pulsar({midi,...})`. |
| `microfono.js` | Implementado. Es el detector YIN de siempre, **con los mismos umbrales y tiempos** (hay una prueba que compara las frecuencias con la versión anterior). Opciones de `iniciar`: `umbral()`, `nivel(rms)`, `alDetectar(midi)`, `alEncender()`, `alApagar()`, `alError(e)`. |
| `golpes.js` | Reservado, vacío y documentado (energía/onsets de volumen para ritmo y palmas; debe compartir el permiso del micrófono). |
| `acordes.js` | Reservado (varias notas a la vez; cromagrama). |
| `midi.js` | Reservado (Web MIDI por USB/OTG en Chrome para Android). |

### Cómo agregar un proveedor

1. Crear `js/core/entrada/<nombre>.js` que llame a `registrarProveedor`.
2. Agregarlo en `index.html` (después de `entrada.js`) y en la lista de `sw.js`.
3. Una actividad que lo necesite escucha `Gioval.entrada.suscribir("<tipo>", ...)`; no se importa nada de la isla.

## Sonido (`js/core/sonido.js`)

Los instrumentos son "voces" intercambiables.

```js
Gioval.sonido.registrarInstrumento("guitarra", {
  nombre: "Guitarra",
  muestras: { "60": "audio/inst/guitarra/c4.mp3", "67": "audio/inst/guitarra/g4.mp3" }, // opcional
  tocar(midi, dur, vol, ctx) { /* alternativa con osciladores */ }
});
Gioval.sonido.usar("guitarra");                 // instrumento activo
Gioval.sonido.tocar(64, .5, .35, "piano");      // suena una nota (el último parámetro es opcional)
await Gioval.sonido.cargarMuestras("guitarra"); // baja y decodifica las muestras SOLO cuando se necesitan
```

- Hoy hay un instrumento: `"piano"`, el piano de juguete con osciladores, **idéntico al sonido de siempre**
  (`tone(midi, dur, vol)` sigue existiendo y usa el instrumento activo).
- Un instrumento con `muestras` suena con la muestra más cercana, ajustando la velocidad de reproducción.
  Las muestras se descargan por demanda (no se precargan en `sw.js` hasta que existan; en ese caso se las agrega a la
  caché de forma explícita para uso sin conexión).

## Pruebas

`python3 gioval-dev/tests/correr.py` cubre: registro de proveedores, `emitir`/`suscribir`/dar de baja,
`necesito`, que Música responda a eventos sintéticos `nota` y `toque` (sin tocar el micrófono real), YIN idéntico a
la versión anterior (7 frecuencias), un micrófono real simulado con el dispositivo falso de Chrome (arranca, queda
encendido, se detiene), e instrumentos/muestras intercambiables.

**No se prueba en emulación:** la detección de un piano real por el micrófono de un teléfono real (ruido, distancia,
umbral). Eso se verifica a mano.
