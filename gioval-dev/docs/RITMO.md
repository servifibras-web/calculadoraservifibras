# Isla Ritmo y percusión

Ritmo antes que solfeo y guitarra: sentir el pulso, copiar ritmos, silencios, leer tarjetas, ritmos de canciones tradicionales,
llamada y respuesta y armar un ritmo propio. Se juega con el **tambor de la pantalla** o con **un instrumento de verdad**
(tambor, cajón, bongó, pandereta, palmas, cucharas, la caja de la guitarra) escuchado por el micrófono.

Archivos: `gioval/js/islas/ritmo.js` (isla), `gioval/js/datos/ritmo.js` (habilidades, canciones, parámetros y textos por idioma),
`gioval/js/core/entrada/golpes.js` (detector de golpes, genérico), `gioval/js/core/entrada/microfono.js` (micrófono compartido).

## Qué mide la app y qué NO

**Qué detecta (y se puede confiar):**

- **Cuándo empieza** cada golpe (sonido corto y fuerte), con error de pocos milisegundos en pruebas con audio sintético.
- **Aproximadamente qué tan fuerte** fue (de 0 a 1; sirve para distinguir un golpe suave de uno fuerte, no para medir decibeles).
- Con eso evalúa **solo el tiempo**: si copiaste el ritmo, si seguiste el pulso, si te adelantaste, atrasaste, faltó un golpe,
  sobró uno o tocaste donde había un silencio. Y calcula qué tan **parejo** sos (desvío medio en milisegundos).

**Qué NO detecta (y la app no lo finge):**

- No sabe **qué instrumento** suena ni si el golpe está "bien dado" (técnica, postura, mano, sonido, calidad).
- No juzga **afinación** ni **notas** (eso es de la isla Música).
- No distingue **quién** golpea: si hay otra persona o un televisor haciendo ruidos cortos y fuertes, los cuenta.
- Un golpe **muy suave** (por debajo del umbral) no se oye: sube la sensibilidad o acercá el micrófono.
- Un golpe que cae **justo encima del clic de la base** de la propia app puede perderse con el micrófono (la app silencia ese
  instante para no escucharse a sí misma). Por eso en esos ejercicios la base suena bajito y los golpes del niño siguen contando.
- Rasgueos de guitarra: las 6 cuerdas cuentan como **un** golpe (el del inicio). No se distinguen los golpes de abajo y de arriba.
- La **demora fija** del aparato (la pantalla, el micrófono, el Bluetooth) no se mide: en los ejercicios con base se descuenta
  (se ve como "tendencia" en el informe), pero es un número orientativo.

El informe para adultos lo dice con todas las letras: la app mide **cuándo** suenan los golpes y **qué tan parejos** son; la técnica
y el sonido los ve un adulto o un profe.

## Cómo funciona el detector (por micrófono)

1. Comparte el flujo del micrófono con la isla Música (un solo permiso).
2. Mide la energía del sonido cada ~3 ms. Hay golpe cuando la energía **supera el umbral** y además **sube de golpe** respecto de
   los ~45 ms anteriores. Después hay un **período refractario** de 110 ms (un rebote o un rasgueo cuentan como un solo golpe).
3. **Calibración de 3 s** al encender ("Shhh, estoy escuchando el ruido de la sala"): mide el ruido de fondo y arma el umbral
   (ruido de fondo x 3,5, con un mínimo). Después el ruido de fondo se adapta despacio (un ventilador que arranca no dispara golpes).
4. **Silencio mientras la app suena**: no escucha mientras habla ni durante los clics de la base (así no se oye a sí misma).
5. Si no hay micrófono o se niega el permiso, se usa el **tambor de la pantalla** (el mismo evento `golpe` con `fuente:"toque"`).

Si el micrófono falla o el aparato está muy ruidoso, la app lo avisa y sigue con la pantalla; nunca se queda trabada.

## Cómo se evalúa (tolerancias que se adaptan)

- La **ventana de tolerancia** es una fracción del largo del pulso, según el nivel de ayuda del niño:
  nivel 0 (más ayuda) 32 %, nivel 1 24 %, nivel 2 (sin ayuda) 18 %; con topes de 90 ms y 210 ms.
  Ejemplo, pulso de 500 ms (120 por minuto): 160 / 120 / 90 ms.
- **Eco** (copiar un ritmo): el primer golpe es el ancla (no importa cuándo empieces); cada golpe se compara con el anterior
  (intervalo) o con el primero (posición); vale el más cercano.
- **Con base o con pulso** (la app marca el pulso): se descuenta la demora fija típica y se compara cada golpe con el momento esperado.
- **Llamada y respuesta**: no hay "respuesta correcta": se cuenta que haya al menos 2 golpes, no demasiados, y que caigan sobre la
  grilla de corcheas (parejos).
- En ejercicios largos (6 golpes o más) alcanza con acertar el 75 % y un golpe de más.
- **Ayudas que se retiran** (a medida que el niño avanza): nivel 0 con tarjetas, latidos visibles y modelo; nivel 1 con menos ayuda
  visual; nivel 2 solo sonido; y en el **chequeo semanal** sin ninguna ayuda y con un solo intento.
- Un error **no castiga**: se dice qué pasó ("fuiste un poquito rápido en el segundo golpe"), se repite, y al segundo intento fallado
  baja un poco el tempo. A la tercera, la app muestra cómo va y la deja para repasar después.

## Parámetros ajustables

En `gioval/js/datos/ritmo.js` (`AJUSTES`):

| Parámetro | Valor | Qué hace |
|---|---|---|
| `ventana.frac` | `[0.32, 0.24, 0.18]` | tolerancia como fracción del pulso, por nivel (0 más ayuda … 2 sin ayuda) |
| `ventana.minMs` / `maxMs` | 90 / 210 | topes de la tolerancia |
| `aciertoMin` | 0.75 | proporción de aciertos que alcanza en ejercicios largos |
| `pulsosCuenta` | 4 | clics de cuenta antes de empezar |
| `esperaPrimerGolpeMs` | 10000 | cuánto espera el primer golpe antes de decir "no te escuché" |
| `graciaMs` | 350 | espera tras el último golpe esperado para detectar golpes de más |
| `intentosMax` | 3 | intentos por ejercicio |
| `bajaTempoAyuda` | 0.85 | tras un fallo repetido baja el tempo a este factor |
| `minEvaluaciones` | 8 | mediciones mínimas para mostrar la evolución en el informe |
| `volumen` | modelo .5 · base .22 · pad .45 | volúmenes de los sonidos de la app |

En `gioval/js/core/entrada/golpes.js` (`Gioval.entrada.proveedores.golpes.PARAMS`, se puede cambiar desde la consola para probar):

| Parámetro | Valor | Qué hace |
|---|---|---|
| `factor` | 3.5 | umbral = ruido de fondo (percentil 95) x este factor. Más alto = menos sensible |
| `rmsMin` | 0.010 | umbral mínimo absoluto aunque la sala sea muy silenciosa |
| `salto` | 1.9 | cuánto debe subir la energía respecto de los ~45 ms anteriores |
| `refractarioMs` | 110 | mínimo entre dos golpes (por debajo de esto cuentan como uno) |
| `calibracionMs` | 3000 | duración de la calibración |
| `tauPisoMs` | 4000 | qué tan rápido se adapta el ruido de fondo |
| `hopMs`, `contextoMs`, `picoMs` | 3, 45, 40 | resolución del análisis |

En el **panel de adultos** (candado) hay, con la isla abierta, un deslizador de **Sensibilidad de golpes** (0,25x a 4x), un medidor de
volumen, el estado del micrófono (ruido de fondo y umbral) y un botón **Recalibrar ruido**.

## Cómo probar con instrumentos de verdad (guía para Marcos)

Las pruebas automáticas usan audio sintético: demuestran que el programa mide bien, **no** cómo suena tu sala, tu celular ni tu
instrumento. Esta prueba de 15 minutos sirve para ajustar la sensibilidad. Anotá lo que veas.

Preparación: el celular apoyado sobre una mesa a 1 o 2 metros, sala sin música ni televisor, volumen del celular medio.
Abrí la isla Ritmo, tocá **"Tocar con mi instrumento"**, y quedate en silencio los 3 segundos que dice la pantalla.
Si dice "Mucho ruido", buscá un lugar más tranquilo y repetí.

1. **10 golpes parejos con tu tambor o caja** (uno por segundo, contá "1, 2, 3…" en voz baja, sin acelerar). Abrí el panel de
   adultos: ahí aparece el estado del micrófono. Esperado: la pantalla destella 10 veces, ni 9 ni 11.
   - Si faltan golpes: subí **Sensibilidad** (por ejemplo 1,5x) o acercá el celular.
   - Si sobran golpes (un golpe cuenta doble): bajá la sensibilidad o apoyá el celular en un lugar que no vibre con el tambor.
2. **10 palmas** (una por segundo). Esperado: 10 destellos. Las palmas suaves pueden perderse: probá palmas más firmes y comparalas.
3. **Rasgueo de guitarra** (un rasgueo de abajo hacia arriba cada 2 segundos, 5 veces). Esperado: 5 destellos (un rasgueo = un golpe).
4. **Ruido de fondo**: hacé un golpe, y después encendé un ventilador o la tele bajita y hacé otros 5. Anotá si empieza a perderse alguno.
5. **Jugar en serio**: una sesión completa de "Eco" con tu instrumento. Mirá en el informe de adultos el **desvío medio**. No tenemos todavía valores de referencia medidos con niños de 6 años: anotá los de
   tus hijos como punto de partida y comparalos con los de dentro de unas semanas (lo que importa es la evolución, no el número).

Qué anotar para ajustar los números: cuántos golpes de cada 10 detectó (por instrumento), la sensibilidad que usaste, y si había ruido.
Con eso se puede cambiar `factor`, `rmsMin` o `ventana.frac` (ver tablas de arriba).

## Cómo se prueba automáticamente

`python3 gioval-dev/tests/correr.py ritmo` y `... golpes` (la suite completa los incluye):

- **Detector con señales sintéticas** (clic, palma, tambor, cajón, pandereta; 60/100/150 por minuto): error de tiempo de pocos ms,
  0 falsos positivos con ruido, zumbido, crescendo lento y un ventilador que arranca; refractario; rasgueo = un golpe; fuerza creciente;
  sala ruidosa; silencio de la app.
- **Micrófono falso de Chrome** (`--use-file-for-fake-audio-capture` con archivos WAV): palmas a 100 por minuto, un ritmo de cajón,
  silencio con zumbido y palmas mientras "habla" la app.
- **Evaluación del eco**: acierto, adelantado, atrasado, golpe de más, golpe que falta, ventanas por nivel.
- **Sesiones completas por toque** con un jugador sintético (dominio, desbloqueo, errores sin castigo, informe), las 14 habilidades,
  chequeo semanal, capturas en 360x700 y 740x330.
- `window.__RITMO_ESCALA` (solo pruebas): acelera el reloj de la isla (por ejemplo 5 veces) para que una sesión dure segundos. En la
  app real vale 1.

Límite de las pruebas: el jugador sintético golpea con tiempos exactos; no reemplaza probar con manos de un niño ni con un instrumento real.

## Habilidades (14, desde los 4 años)

Sentir el pulso · eco de 2 golpes · lento, medio y rápido · pulso con la base · eco de 3 · eco de 4 · golpe y silencio ·
pulso solito (la base se apaga) · leer ta y shh · leer ti-ti · llamada y respuesta · ritmos de canciones · leer ritmos largos ·
mi propio ritmo (4 pulsos). Cada una se desbloquea al dominar las anteriores (`req`).

Vocabulario de las tarjetas (método Kodály, de dominio público): **ta** = un golpe, **ti-ti** = dos golpes rápidos en un pulso,
**ta-a** = un golpe largo (dos pulsos), **shh** = silencio.

Canciones: solo se usa el **patrón rítmico simplificado** de una frase de canciones tradicionales de dominio público
(Estrellita, Martinillo, Hot cross buns, Mary tenía un corderito); no se usa ninguna letra. Los patrones están simplificados: si
querés ajustar alguno, está en `CANCIONES` de `gioval/js/datos/ritmo.js`.

## Informe para adultos

En la zona de adultos, el informe incluye "REGULARIDAD DEL RITMO": desvío medio general (en milisegundos), cuántos ejercicios se
midieron con instrumento y cuántos en pantalla, la evolución (primeros vs. últimos ejercicios), el promedio por día practicado, la
tendencia a golpear antes o después del pulso y el desvío por habilidad. Solo se mide el **primer intento** de cada ejercicio (así
el número no se mejora repitiendo). Los datos están en `store.ritmo[<jugador>]` (últimas 600 mediciones; viajan en el respaldo).

## Idiomas

Los textos están en `gioval/js/datos/ritmo.js` como tablas `es-AR` (base) y `en` (`Gioval.i18n.agregar`), con claves `ritmo.*` y
frases completas. La traducción al inglés la hizo la IA y conviene que la revise una persona que hable inglés.
