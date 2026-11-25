# Isla Letras por edades (diseño, umbrales y qué falta revisar)

Isla para chicos que empiezan con las letras (desde los 4 años) y siguen hasta ortografía de uso común. Solo toque. Es la isla de
**lectura y escritura en español**; los textos de la isla están solo en es-AR (ver "Idiomas").

## Dónde está cada cosa

| Archivo | Qué tiene |
|---|---|
| `gioval/js/datos/letras.js` | Textos (tabla es-AR, arriba de todo), las 30 habilidades (`HABILIDADES`), las listas de contenido (palabras con dibujo, rimas, frases, comprensión, oraciones, grupos, ortografía), el mapeo de las preguntas para adultos (`INICIO`) y la tabla de letras que se confunden de oído (`CONFUNDEN`). **Editable sin tocar la lógica.** |
| `gioval/js/islas/letras.js` | Los 20 tipos de actividad, las preguntas para adultos, el juego de ubicación, el resumen y el informe. |
| `gioval/js/core/dominio.js` | Genérico (compartido con Números): salto por dominio rápido y re-evaluación semanal (ver `AGREGAR_ISLA.md`, "dominio rápido"). Letras solo declara `rapido:{rt, salta}` en cada habilidad y marca lo sabido con `Gioval.dominio.saltar`. |
| `gioval/css/letras.css` | Estilos propios (letras grandes, pantallas para adultos). |

## La escalera (8 tramos, 30 habilidades)

Cada habilidad lleva `nivel` (tramo 0 a 7), `edad` típica (orientativa, **nunca limita**: cada chico avanza a su ritmo), `eje` y `rtRapido`.

| Tramo | Edad típica | Contenido |
|---|---|---|
| 1 | 4 | vocales, contar pedacitos (sílabas) |
| 2 | 4 | M P S L T, primer sonido, rimas |
| 3 | 5 | N D C B R F G, de la letra al dibujo, armar con sílabas, vocal que falta |
| 4 | 5 a 6 | primer sonido con más letras, J V Z H Y, mayúsculas/minúsculas, armar palabras, separar en sílabas, letra que falta |
| 5 | 5 a 6 | Ñ Q K X W, escribir el nombre, leer sílabas y palabras cortas, abecedario antes/después |
| 6 | 6 | leer frases, palabras largas, entender una frase |
| 7 | 7 | ordenar oraciones, LL RR CH QU GU, trabadas, mayúsculas y puntos |
| 8 | 7 | ortografía de todos los días, orden alfabético, entender un textito |

## Criterios de diseño

- Se elogia el **esfuerzo y el proceso** ("¡Escuchaste el primer sonido!"), nunca a la persona; sin rachas ni puntos; sesiones cortas; ningún castigo por errores (ayudas progresivas).
- Los ejercicios "de oído" **no ponen juntas** letras que en el habla rioplatense suenan igual o parecido (B/V, C/K/Q/S/Z, G/J, H muda): esas se enseñan por nombre, forma y palabras con dibujo. Una prueba lo comprueba (`CONFUNDEN`).
- Dibujos: solo emoji, vocabulario cotidiano argentino, sin marcas. Cada dibujo se usa en una sola palabra (para que las opciones no se confundan).
- Las rimas siempre muestran la palabra escrita (no dependen del oído).

## Preguntas para adultos (una sola vez, 2 minutos)

Edad, cuántas letras reconoce, qué lee y si escribe su nombre. Se guardan en `store.intake["letras|<Jugador>"]` (Números guarda las suyas en `store.intake[<Jugador>]` y reemplaza ese objeto entero, por eso no se comparte). El tramo de arranque es el **mayor** de:

- letras: ninguna/algunas -> 1; casi todas mayúsculas -> 3; todas -> 4
- lee: no -> 1; sílabas -> 4; palabras -> 5; frases -> 6; textos -> 7
- nombre: no/copia -> 1; solo -> 2

(los números son tramos de 1 a 8; en el código, de 0 a 7). **Se resta uno a propósito** en lectura porque los adultos suelen ser generosos al decir "lee". **La edad sola no salta nada**: no es evidencia; solo decide por dónde arranca el juego de ubicación. Lo que se marca como sabido queda "pendiente de comprobar" y se re-evalúa sin ayuda en el chequeo semanal.

## Juego de ubicación (~5 minutos, sin presión)

Adaptativo y sin ayudas, con botón "No sé" (que cuenta como no saber, sin castigo). En cada tramo: 2 o 3 preguntas de un toque.

- 3 de 3 -> "lo hace bien" (sube un tramo); 2 de 3 -> "a veces" (frena); 0 de 2 o 1 de 3 -> "todavía no" (baja un tramo).
- Corta cuando el límite está claro, a las **16 preguntas** o a los **5,5 minutos**.
- Resultado: **último tramo que hace bien**. Con 3 preguntas por tramo, adivinar al azar entre 3 opciones pasa un tramo el 26 % de las veces; por eso hay "No sé" y por eso lo marcado se re-evalúa en el chequeo semanal.
- El **adulto ve un resumen** (por tramo) y puede "Empezar antes" / "Empezar después" o "No cambiar nada" **antes de aceptar**. Nada se marca hasta que acepta. Queda registrado si se ajustó.

## Salto por dominio rápido

Lo hace el núcleo (`dominio.js`, el mismo de Números). Umbrales (a revisar con datos reales): en los últimos 10 intentos, al menos 6 intentos, al menos 90 % al primer intento y mediana del tiempo de respuesta **menor** que el `rt` de esa habilidad (en milisegundos; en Letras sale de `rtRapido` en `HABILIDADES`). Si se cumple al dominar una habilidad, se salta **solo la primera** que se destraba (Letras declara una sola en `salta`, a propósito conservador). En el chequeo semanal sin ayuda cada saltada recibe 3 ítems: con al menos 2 de 3 queda confirmada; si no, vuelve a práctica. **Los `rtRapido` son estimaciones hechas sin chicos reales: hay que calibrarlos** mirando el "Tiempo de respuesta" del informe de varios chicos (A REVISAR por Marcos).

## Informe para adultos

Desde el menú de la isla ("Informe para adultos"): respuestas de los adultos, punto de partida y de dónde salió, resultado del ubicador, y por habilidad aciertos al primer intento (primeros 5 -> últimos 5), **retención** (aciertos >= 1 día después), tiempo de respuesta típico y qué se saltó, por qué y si se confirmó o volvió a práctica. El informe general de la zona de adultos suma lo mismo.

## Alineación curricular (a revisar por una persona docente)

Orientativa; **no son citas textuales**. Se verificó que existen: los NAP de Lengua del Primer Ciclo (educ.ar) con los ejes "Comprensión y producción oral", "Lectura", "Escritura" y "Reflexión sobre la lengua (sistema, norma y uso) y los textos"; y las "Progresiones de los aprendizajes: Prácticas del Lenguaje, Primer ciclo" (GCBA, 2018). **A revisar**: qué saber puntual de cada eje cubre cada habilidad (la columna `eje` es una aproximación nuestra) y el mapeo fino a cada progresión. La app complementa a la escuela: practica y verifica destrezas, no es un "método".

## Idiomas

Los textos van como frases completas en la tabla es-AR (`letras.*`). Letras enseña a leer en español: las letras, sílabas y palabras son del español, así que **no hay tabla en inglés** (la prueba de completitud exceptúa las claves `letras.*`). Para otro idioma hace falta una isla de letras propia de ese idioma (otro contenido), no una traducción.

## Idea futura (no implementada)

Leer en voz alta con micrófono y reconocimiento de voz. Esta entrega es solo toque.
