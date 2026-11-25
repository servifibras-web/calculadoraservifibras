# Alarma (js/core/alarma.js)

Módulo aislado para "avisame cuando pasen N segundos" (por ejemplo, un temporizador de práctica o de descanso).
Ninguna isla ni el motor dependen de cómo se implementa: usan solo esta API.

```js
Alarma.programar(segundos, { titulo: "Mundo Gioval", texto: "¡Se terminó el tiempo!" }); // reemplaza la anterior
Alarma.cancelar();
Alarma.restante();            // segundos que faltan (0 si no hay alarma)
Alarma.activa();              // true/false
const baja = Alarma.onFin(info => { /* info = { titulo, texto, fin, tarde } */ });  // baja() deja de escuchar
Alarma.pedirPermiso();        // pedir permiso de notificaciones; llamarlo desde un toque del usuario
```

`window.Alarma` es un alias de `Gioval.alarma`.

## Limitación honesta (leer antes de prometerle algo a nadie)

**En la web instalada (PWA), una alarma con la pantalla apagada, el teléfono bloqueado o la app cerrada NO está
garantizada.** El navegador congela o descarta la página y no hay forma confiable de despertarla a una hora exacta.
Lo que sí hace la versión web, y lo que no:

| Situación | Alarma web |
|---|---|
| App abierta y pantalla encendida | Suena a la hora (sonido Web Audio, vibración, notificación si hay permiso). |
| Pantalla encendida y la app en segundo plano un rato | Suele sonar, pero depende del navegador. |
| Pantalla apagada / teléfono bloqueado | **No garantizado.** Al volver a abrir la app se recalcula con la hora absoluta y, si ya venció, suena en ese momento ("tarde" indica cuánto pasó). |
| App cerrada o descartada por el sistema | **No garantizado.** Al reabrir, la alarma vencida se avisa igual. |

La solución real es el envoltorio nativo, **Android primero**: ver `ANDROID.md` (APK armado con GitHub Actions). Dentro del
envoltorio, `js/core/alarma_nativa.js` (que se activa solo si existe el plugin propio `Capacitor.Plugins.GiovalAlarma`) suma
a la alarma web una alarma EXACTA del sistema (AlarmManager + servicio de sonido + pantalla sobre el bloqueo), y `cancelar()` la
cancela. `alarma.js` no cambia: la app **no depende** del envoltorio y, sin él, funciona como PWA con la limitación de arriba.
Además, si existe `window.Capacitor.Plugins.LocalNotifications`, `alarma.js` sigue programando una notificación local exacta
(camino alternativo; el envoltorio de Android no lo usa). Falta probar la alarma nativa en un aparato real.

## Cómo funciona la versión web

- **Hora absoluta.** Se guarda `fin = Date.now() + duración`. Nunca se confía en un contador que se pueda congelar.
- **Revisión al volver.** Cada 500 ms mientras la página corre, y también en `visibilitychange`, `pageshow` y `focus`,
  se compara `Date.now()` con `fin`. Si la pantalla estuvo apagada y los timers se congelaron, al volver dispara enseguida.
- **Persistencia.** La alarma se guarda en `localStorage` (`gioval_alarma`). Si la página se recarga o el navegador la
  descarta, al abrirla se restaura. Una alarma que venció mientras la app estaba cerrada se entrega al primer
  `onFin` que se registre (así no se pierde por llegar antes que el oyente).
- **Wake Lock (opcional).** Mientras corre pide `navigator.wakeLock.request("screen")` para que la pantalla no se apague
  sola. Si el navegador no lo soporta, sigue igual.
- **Al vencer:** 4 pitidos con Web Audio, vibración, y notificación vía service worker
  (`registration.showNotification`) si el permiso está concedido. El service worker (`sw.js`) enfoca la app al tocar
  la notificación.
- **Una sola vez.** Una alarma dispara una única vez; no se duplica por los eventos de revisión.

## Qué se prueba automáticamente (y qué no)

`python3 gioval-dev/tests/correr.py` cubre, con reloj simulado y timers congelados:

- reloj adelantado + pantalla "oculta": no dispara antes de tiempo, dispara al volver a primer plano, una sola vez;
- cancelar, dar de baja un oyente, reprogramar, sobrevivir a una recarga, alarma vencida con la app cerrada;
- wake lock pedido, notificación local nativa (Capacitor simulado) y notificación del service worker (simulada).

**No se puede probar en emulación:** que el teléfono real suene con la pantalla apagada o con la app cerrada. Eso hay
que verificarlo a mano en el aparato (PWA) y, más adelante, en el envoltorio nativo.

## Quién la usa

- **Ayudantes de la casa** (`js/islas/ayudantes.js`): cronómetro de cada tarea. Qué ve el niño al volver a primer plano y cómo
  se retoma una tarea tras cerrar la app: ver `AYUDANTES.md`. Pruebas: `correr.py ayudantes`.
