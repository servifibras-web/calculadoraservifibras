# Ayudantes de la casa ("Hora de ayudantes")

Cuando se termina el tiempo diario de pantalla, la app ofrece tareas **reales y seguras** para la casa, con cronómetro,
para que el niño se sienta útil. No es una isla de aprendizaje: no está en el mapa, no tiene habilidades y no entra en
el informe. Código: `gioval/js/islas/ayudantes.js`. Textos y tareas: `gioval/js/datos/tareas.js`.

## Qué ve el niño

1. Al llegar al tope diario, el cartel "¡Terminamos por hoy!" suma la frase "Si querés, ¡es la hora de ayudantes!" y el
   botón **🧹 Hora de ayudantes** (junto al "¡Chau, zorro!" de siempre). Si lo cierra, la tarjeta sigue en el menú de la isla
   mientras no haya más tiempo.
2. **Lista** de tareas (por edad, habilitadas por los adultos; las que pidió un adulto van primero y marcadas 📌).
3. **Detalle**: ícono, 2 a 4 pasos cortos que la app **lee en voz** de a uno, tiempo sugerido, nivel de supervisión y,
   si corresponde, el **aviso de seguridad** (también leído). Las tareas **"solo con adulto"** piden la pregunta de adultos
   (la misma del panel) para empezar.
4. **Cronómetro**: cuenta regresiva grande (mm:ss) y barra. Usa la **hora absoluta** del módulo Alarma.
5. Al vencer: alarma suave (4 pitidos), vibración, aviso en voz y pantalla "⏰ ¡Se terminó el tiempo!" con
   **✅ ¡Terminé!** o **⏳ Un ratito más** (+2 minutos). Sin castigo: también puede **"Dejarla por ahora"** y no se anota nada.
6. **Terminé**: elogio al **esfuerzo** ("Terminaste lo que empezaste, eso lleva esfuerzo"), nunca a la persona. Se anota y
   dice "Esta semana ayudaste N veces". **No hay rachas, puntos ni comparaciones**; la semana siguiente empieza de cero.
7. Opcional (solo si un adulto lo activa): **📷 foto** al terminar, guardada en el almacén de fotos de IndexedDB
   (`Gioval.almacen.fotos`, con `meta = {tipo:"ayudantes", kid, tarea}`), reducida a 1280 px. Queda **solo en el aparato** y
   **no viaja en el respaldo** (el respaldo exporta solo el JSON del `store`). Todavía no hay pantalla de álbum.

## Zona de adultos (panel ⚙️ → "🧹 Ayudantes de la casa", por perfil)

Activar/desactivar · edad del niño (4 a 12) · duración (la sugerida por tarea o 3/5/10/15/20 min) · tareas habilitadas ·
tareas asignadas 📌 (se quitan solas cuando el niño la hace) · permitir foto · "▶ Abrir Hora de ayudantes ahora" ·
"Esta semana ayudó: N veces (detalle)" · cantidad de fotos · **estado honesto de la alarma** (ver abajo).

Por defecto: activado, 6 años, duración sugerida, todas las tareas habilitadas, sin foto.

## El tiempo de ayudantes NO cuenta como tiempo de pantalla

Decisión tomada: pantalla = solo tiempo dentro de la app en actividades de aprendizaje. El motor solo suma segundos cuando
la pantalla activa tiene la clase `juego` (`motor.js`, contador de tiempo) y `#ayudantes` no la tiene. Una prueba lo comprueba
(el contador sigue quieto durante el cronómetro y el cartel de tope no vuelve a saltar).

## Alarma con la pantalla apagada: NO garantizada en navegador

Se usa `js/core/alarma.js` sin cambios (Ayudantes se registra con `onFin` solo mientras hay una tarea en curso, para no llevarse el aviso de una alarma vencida que sea de otro módulo). Comportamiento verificado automáticamente (reloj simulado + `document.hidden` +
timers congelados), con la tarea en curso:

| Situación | Qué pasa |
|---|---|
| App abierta, pantalla encendida | Suena a la hora y muestra "¡Se terminó el tiempo!". |
| Pantalla oculta/bloqueada y los timers congelados | **No suena mientras sigue congelada.** Al volver a primer plano (`visibilitychange`) se recalcula con la hora real, suena en ese momento (una sola vez) y se muestra "Volviste a la app y ya había pasado el tiempo. Está bien: ¿pudiste terminar?". |
| App cerrada o descartada por el sistema | La tarea en curso se guarda (`localStorage.gioval_ayudando`). Al reabrir y elegir de nuevo al niño, se retoma: en hora con la cuenta regresiva, o vencida con el mismo mensaje. Una tarea de más de 3 horas se descarta. |

**Lo que no se puede probar en emulación** y hay que verificar a mano en el aparato: que el teléfono real suene con la
pantalla apagada. En navegador no está garantizado; se resuelve con la app Android nativa (Capacitor `LocalNotifications`,
ya preparado en `alarma.js`, aparato por confirmar). El panel de adultos lo dice con esas palabras y muestra si el
navegador permite mantener la pantalla encendida, el estado del permiso de avisos y si se detectó Capacitor.

## Ganchos en `js/core/` (mínimos y genéricos; no nombran a Ayudantes)

| Archivo | Cambio |
|---|---|
| `motor.js` `showCap()` | `Gioval.emit("tope", {kid, pack, extra})`; si un módulo deja `d.extra`, se suma a la frase del cartel y se dice en voz. |
| `ui.js` `renderMenuIsla()` | `Gioval.tarjetasMenu`: lista de funciones `done => [tarjetas]` que se suman al menú de cualquier isla. |
| `adultos.js` `renderParent()` | `Gioval.emit("panel")` al final, para que los módulos redibujen su sección. |
| `index.html` | El botón del cartel de tope quedó dentro de `#capAcc` (fila de botones) para poder sumar otros. |

Sin módulos que los usen, no hacen nada: el cartel, los menús y el panel se ven igual (lo comprueba la regresión visual).

## Lo que se guarda

Dentro de `store` (viaja en el respaldo; se crea al primer uso, sin migración): `store.ayud.cfg[perfil]` =
`{on, edad, dur, off:[ids], asig:[ids], foto}` y `store.ayud.reg[perfil]` = `[{t, id, s, f?}]` (cuándo, tarea, segundos, id de foto).
Los ids de tarea son parte de lo guardado: no renombrarlos.

## Cómo editar las tareas

Todo está en `gioval/js/datos/tareas.js`: agregar una tarea es agregar un objeto
`{id, emoji, nombre, minutos, edadMin, supervision, pasos:[2 a 4 frases], aviso}`. La prueba automática exige:
supervisión válida, aviso no vacío si es "cerca" o "adulto", 2 a 4 pasos cortos, y que los **pasos** no nombren fuego, calor,
filo, químicos, escaleras ni electricidad. Los textos de pantalla están en `TEXTOS` (arriba del archivo).

## Pruebas (`python3 gioval-dev/tests/correr.py ayudantes`)

Datos y reglas de seguridad · aparece al llegar al tope · elegir tarea y pregunta de adultos · cronómetro con reloj
simulado y pantalla oculta · terminar y registro semanal · no cuenta como tiempo de pantalla · configuración de adultos
(y estado honesto de la alarma) · foto opcional · retomar tras cerrar la app · Música y Números no cambian · capturas
(360x700 y 740x330 en `gioval-dev/tests/salida/`).
