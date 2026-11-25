# De a dos (Giovanni y Valentino juegan por turnos en el mismo aparato)

Un modo nuevo para que los dos jueguen juntos, uno a la vez, en el mismo celular o tableta. **No es una isla**: no tiene
habilidades propias. Juega las habilidades de una isla que ya existe (hoy Números o Letras), pero cada uno con **su propio plan**.

## Qué ve el chico

1. En **¿Quién juega?** (y también en el mapa) aparece la tarjeta **👫 De a dos**. Solo aparece si hay al menos dos jugadores creados.
2. **Armado**: tocan a los dos jugadores (el orden en que se tocan es el orden de los turnos; si solo hay dos, ya vienen elegidos) y, si hay
   más de una isla por toque, eligen la isla. Un chico que ya jugó sus minutos de hoy no se puede elegir.
3. **Entrega de turno**: pantalla grande con el avatar y el nombre ("Ahora le toca a Valentino"). La voz lo anuncia. **No hay apuro**: el
   turno empieza cuando tocan **¡Vamos!**. Esperar acá **no gasta tiempo** de nadie.
4. **El turno**: 4 respuestas del plan de **ese** chico (más los reintentos de siempre si se equivoca). Arriba se ve de quién es el turno y el
   **dibujo del equipo**. Después, otra vez la entrega para el que sigue.
5. **El dibujo del equipo**: 8 casilleros (Huerta, Ciudad, Mar, Espacio, uno después del otro). Se llena una pieza cada vez que **cualquiera** de los dos
   resuelve una pregunta sin que la app le muestre la respuesta. **Los errores no restan nada.** Cuando se completa, hay una pantalla de festejo
   y arranca un dibujo nuevo. El dibujo es de la pareja y se guarda.
6. **Explicar**: a veces, antes de su turno, la app le dice a uno: "Valentino está practicando «Contar hasta 10» y vos ya lo sabés. ¿Le explicás cómo
   se hace?", con un consejito simple ("Contale qué mirás primero."). Si toca **¡Ya le expliqué!**, el equipo suma 2 piezas. Si toca **Ahora no**, no pasa nada.
7. **Tope diario**: si uno llega a su tope de minutos, **se deja terminar la pregunta que tiene en pantalla** (sin apuro; si no la resuelve, a los 45 segundos el turno se
   cierra solo) y aparece un mensaje amable: "Giovanni ya jugó por hoy. ¡Gracias por jugar! Mañana seguimos." con dos botones: **Seguir con Valentino**
   (juega él solo hasta su tope) o **Terminar por hoy**. Si los dos llegan al tope, la sesión termina con "¡Buen trabajo, equipo!".
8. El botón **⬅ Volver** durante un turno pregunta "¿Terminamos por hoy?". Lo hecho hasta ahí ya está guardado.

## Qué NO cambia (y por qué importa)

- **Cada uno conserva lo suyo**: habilidades dominadas, nivel de ayuda, repaso espaciado (Leitner), estrellas y tiempo diario. Un turno de Valentino
  se juega "como si fuera Valentino solo": nunca baja ni sube de nivel por el otro, y a Giovanni no le toca lo de Valentino ni al revés (hay pruebas que lo comprueban).
- **Las reglas de dominio y de ayudas son las de siempre**: las respuestas pasan por el mismo código que una sesión suelta.
- **Explicar no cuenta como aprender**: no suma nada al dominio de nadie (ni práctica, ni registro, ni días). Solo suma piezas al dibujo.
- **El tiempo de cada turno gasta el tope de ese chico**, y el tiempo de espera entre turnos no gasta nada.

## Informe para adultos

En **⚙️ → 📄 Informe**, cada chico ve **sus** sesiones de a dos (hasta las últimas 8): fecha, con quién, cuántas respuestas, cuántas al primer intento, minutos,
turnos, piezas del equipo, y cuántas veces explicó o escuchó una explicación. Si nunca jugó de a dos, no aparece la sección. Las respuestas también están,
como siempre, en las líneas de cada habilidad. En el registro de práctica quedan marcadas con `d:1` por si más adelante querés separar "solo" de "de a dos".

## Qué es una estimación y no se validó con los chicos

Todo esto está elegido con criterio pero **sin probarlo todavía con Giovanni y Valentino**. Se ajusta en `AJ` (arriba de todo en `gioval/js/islas/dedos.js`):

| Qué | Valor | Para qué |
|---|---|---|
| `itemsPorTurno` | 4 | Respuestas antes de pasar el aparato. Si se aburren esperando, bajalo; si el cambio es muy seguido, subilo. |
| `CUADROS` | 4 dibujos de 8 piezas | Los dibujos (emoji) están en la lista `CUADROS`; cada uno tiene 8 piezas y al llenarlo hay festejo. |
| `piezasExplicar` | 2 | Piezas por explicar. |
| `maxExplicaciones`, `turnosEntreExplicaciones` | 2 y 3 | Cuántas veces por sesión y cada cuántos turnos se propone explicar. |
| `minIntentosOyente` | 2 | El otro tiene que haber practicado esa habilidad al menos 2 veces para que cuente como "la está practicando". |
| `graciaTopeMs` | 45 s | Cuánto se espera a que termine la pregunta en pantalla cuando se llega al tope. |

Dudas pedagógicas para mirar con ellos: si "explicar" les sirve de verdad o lo toman como trámite (por eso solo da piezas), si el dibujo motiva sin competir,
y si a Valentino (6 años) le resulta largo esperar durante el turno de Giovanni.

## Qué no se pudo probar acá

Todo se probó con Chrome emulando un Pixel 7, un celular de 360x700, uno horizontal de 740x330 y una tableta de 820x1180. **No se probó**: en un aparato Android real
con dedos reales, cómo suena la voz anunciando los turnos, ni con los chicos de verdad.

## Parte técnica (para quien programe)

- Archivo nuevo: `gioval/js/islas/dedos.js` (`Gioval.dedos` para pruebas). Registrado en `index.html` (después de `ritmo.js`) y en la lista de `sw.js`. **Se subió `GIOVAL_VERSION` de 8 a 9**.
- **No se registra con `Gioval.islas.registrar`** (igual que Ayudantes): no es una isla de aprendizaje y así no cambia la lista de islas ni sus pruebas. Se anota en `Gioval.modos`.
- **Ganchos genéricos nuevos** (no nombran este archivo; sin módulos que los usen no hacen nada):
  - `ui.js`: `Gioval.modos = [{id, visible(), em, nombre, sub, go(), informe?(kid)}]` → tarjeta en "¿Quién juega?" y en el mapa (`data-modo`).
  - `adultos.js`: `reportText()` suma `m.informe(KID)` de cada modo.
  - `motor.js`: `S.session.alFin(run)` (en `endSession`), `S.session.alResponder(it,res,{ok,first})` (en `itemDone`, después de guardar el progreso) y `S.session.alTope()` (en `showCap`, para que un modo maneje el tope a su manera).
  - `actividades.js`: `S.session.alVolver()` (botón ⬅).
- **Cómo funciona un turno**: `KID = chico del turno`, `PACK = isla elegida`, `planSession()` y se toman los primeros `itemsPorTurno` ítems; se arma una `S.session` con los ganchos y se llama a `nextItem()`. Todo el progreso lo escribe `itemDone()` del motor.
- **Tiempo**: el contador del motor suma segundos a `store.time[KID|hoy]` solo en pantallas `.juego`. La pantalla de actividad lo es; las de este modo (`#ddSetup`, `#ddPaso`) no.
- **Datos** (almacén **v4**, migración numerada nueva, con copia previa antes de migrar como siempre): `store.dedos = { eq: { "A|B": {piezas, cuadros, total} }, reg: { chico: [{t, c, n, ok, s, tr, e, r, p}] } }`.
  Las pruebas existentes que comprobaban la versión 3 pasaron a comprobar la 4.
- **Pruebas** (`python3 gioval-dev/tests/correr.py "de a dos"`): entrada y armado, turnos que alternan y progreso por chico, dibujo del equipo, explicar, tope diario, informe, vistas
  (Pixel 7, 360x700, 740x330 y tableta 820x1180), pseudo-idioma y RTL, inglés, migración, y que sin usarlo nada cambia.
- **Idiomas**: claves `dedos.*` en es-AR (base) y `en` (completo). Las variantes es-419 / es-ES caen a es-AR (con voseo): pendiente de traducir.
- El CSS está dentro de `dedos.js` (clases `dd-` e ids `#dd…`) para no tocar `css/app.css`.
