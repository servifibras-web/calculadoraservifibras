# Entradas y sonido

Las actividades no hablan directamente con el micrófono ni con la pantalla, ni saben cómo suena el piano. Piden
"qué entrada necesito" a un registro y escuchan eventos con un formato común. Así se pueden sumar un teclado MIDI,
detector de palmas o instrumentos con muestras sin tocar las islas ni el motor.

## Entradas (`js/core/entrada/`)

### Eventos

| Evento | Campos | Quién lo emite |
|---|---|---|
| `{ tipo:"nota" }` | `midi`, `t`, `fuerza` | micrófono (YIN, una nota por vez); MIDI (reservado) |
| `{ tipo:"golpe" }` | `t`, `fuerza`, `fuente` (`"mic"` o `"toque"`) | detector de golpes/palmas (`golpes.js`); el tambor de la pantalla emite lo mismo con `fuente:"toque"` |
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
| `microfono.js` | Implementado. Detector de notas con YIN (rango 80–1200 Hz, valle afinado entre muestras, valle suave como alternativa, votos que tienen que coincidir) y **afinación del piano** (corrección en cents, automática o calibrada a mano). Emite `{ tipo:"nota", midi, midiFloat, cents, hz, afinacion, fuerza }`. Opciones de `iniciar`: `umbral()`, `nivel(rms)`, `alDetectar(midi, {hz,cents,midiFloat})`, `diagnostico(v)`, `envivo()`, `alAfinar(c)`, `alEncender()`, `alApagar()`, `alError(e)`. `M.vivo` guarda lo último que oyó y por qué se ignoró un sonido. |
| `golpes.js` | Implementado (lo usa la isla Ritmo). Detecta CUÁNDO empieza un golpe (energía con umbral adaptativo, período refractario, calibración de 3 s del ruido de fondo, silencio mientras la app suena, máscaras para el clic de la propia isla) y cuánto de fuerte fue. Comparte el micrófono con `microfono.js`: Música y Ritmo pueden estar encendidos a la vez con un solo permiso. Alternativa sin micrófono: `pulsar({t,fuerza})`. No emite `"toque"`. Detalle, parámetros y límites: `RITMO.md`. |
| `acordes.js` | Reservado (varias notas a la vez; cromagrama). |
| `midi.js` | Reservado (Web MIDI por USB/OTG en Chrome para Android). |

### Micrófono compartido

`microfono.js` expone `flujo()` y `soltar()` (cuenta de usos): el primero que pide abre el micrófono, los demás reutilizan el mismo
flujo (un solo permiso), y el micrófono se apaga cuando nadie lo usa. `golpes.js` lo usa así; `iniciar`/`detener` de `microfono.js`
siguen funcionando igual para Música.

### Cómo agregar un proveedor

1. Crear `js/core/entrada/<nombre>.js` que llame a `registrarProveedor`.
2. Agregarlo en `index.html` (después de `entrada.js`) y en la lista de `sw.js`.
3. Una actividad que lo necesite escucha `Gioval.entrada.suscribir("<tipo>", ...)`; no se importa nada de la isla.

## Si el piano no se escucha bien

Esto es para cuando la app "no reacciona" o marca mal una tecla que tocaste bien. Se prueba en la **zona de adultos (⚙️)**:
ahí hay un cuadro "Lo que escucha el micrófono" que se actualiza en vivo. Encendé el 🎤, abrí el panel y tocá **una tecla sola**.

**Qué muestra el cuadro**

- **La nota grande** (por ejemplo "Mi 4"): lo que la app cree que tocaste. El número es la octava (Do 4 es el Do del medio del piano).
- **Hz y "cents"**: la frecuencia del sonido y cuánto se aparta de la nota justa. *100 cents = una tecla (un semitono).* "Bien afinada"
  es menos de 5 cents; "20 cents más grave" quiere decir que el piano suena un poquito bajo.
- **Volumen contra el mínimo**: "Volumen 30 · mínimo 8". Si tu volumen no pasa el mínimo, la app no oye la tecla: subí la sensibilidad
  (el control "Sensibilidad") o acercá el celular al piano. La rayita roja de la barra marca el mínimo.
- **El estado**: "Escuchando", o "La app está hablando o tocando: ahora no escucho". Mientras la app habla, o toca la demostración, **no oye
  nada** (si no, se escucharía a sí misma). Si tocás una tecla en ese momento, se pierde. Los chicos ven un cartelito verde
  "👂 Te escucho" arriba del teclado cuando sí los está escuchando: si no está, hay que esperar.
- **El motivo**, si la app ignoró un sonido (queda 5 segundos): *la app estaba hablando* · *muy suave* · *todavía sonaba la nota anterior* ·
  *no pude saber qué nota era* (varias teclas juntas o mucho ruido) · *demasiado grave o aguda* (fuera de 80 a 1200 Hz).

**Qué hacer según lo que se vea**

1. *Tocás Mi y aparece "Re#" o "Fa" (u otra tecla vecina)*: el piano está desafinado. Probá la **afinación** (abajo). Las teclas
   negras no se ven en la pantalla de los chicos, por eso un Mi leído como Re# parece "no hacer nada".
2. *No aparece nada y el volumen no llega al mínimo*: subí la sensibilidad o acercá el celular.
3. *Aparece "La app está hablando"*: esperá a que termine y que aparezca el cartelito "Te escucho".
4. *Aparece la nota correcta pero con otra octava y el juego la marca mal*: tenés apagado "Aceptar la nota en cualquier octava".
   Con eso apagado, la nota correcta en otra octava ya no resta estrellas: solo se avisa.

**Afinación del piano.** Un piano de casa casi nunca está justo a La = 440 Hz; muchos están 20 o 40 cents bajos. La app compensa:

- *Sola*: mientras se tocan notas naturales (blancas), va midiendo el desvío promedio y se corrige de a poco (nunca más de 8 cents por vez,
  hasta 50 cents, y solo con al menos 6 notas parecidas de 3 teclas distintas; las teclas negras no cuentan).
- *A mano*: botón **"🎵 Tocá un La"**; tocá un La (una sola tecla, clara) y la app fija la corrección. **"↺ Volver a cero"** la borra.
- Queda guardada **en este aparato** (no en el progreso de los chicos ni en el respaldo).
- Límite: no distingue un piano 50 cents **alto** de uno 50 cents bajo (suenan igual de "a medio camino"). Si está tan lejos, hay que afinarlo.

**Rango y cómo decide.** Oye de 80 a 1200 Hz (del Mi2 al Re6; antes empezaba en 170 Hz, el Fa3, y el Mi3 se leía como Fa3). Mide tres veces
en los primeros ~0,2 s de la nota y hacen falta al menos dos medidas que coincidan.

**Límites conocidos.** Con 3 o 4 notas por segundo de la misma tecla puede perderse alguna. Un piano con las cuerdas muy desparejas
(sonido "de bar") puede hacer que una nota larga cuente dos veces. Un teclado con timbre de órgano o coro que mezcla notas puede dar
octavas equivocadas. Nada de esto se pudo probar con un piano real: ver "Pruebas".

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
la versión anterior (mismas notas, más cerca de la frecuencia real), un micrófono real simulado con el dispositivo falso de Chrome (arranca, queda
encendido, se detiene), e instrumentos/muestras intercambiables.

Para el micrófono de Música hay pruebas con audio sintético de teclado tocado por el micrófono falso de Chrome (`senal_notas` en `tests/lib.py`):
los 7 naturales Do4–Do5 más Mi3/Mi4/Mi5 en 3 timbres y con el piano afinado, −30 y +30 cents; piano −50 cents con "pedido Mi → tocar Mi = acierto, tocar Do = error";
dos frecuencias de muestreo; rango 80–1200 Hz y ruido; afinación automática y calibración con un La; notas repetidas y sostenidas; lectura en vivo y motivos.

**No se prueba en emulación:** la detección de un piano real por el micrófono de un teléfono real (ruido, distancia,
umbral). Eso se verifica a mano.
