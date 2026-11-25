# Cómo agregar un idioma (y cómo funcionan los idiomas)

Mundo Gioval trae la **maquinaria** de idiomas. Los textos de cada idioma viven en tablas (`gioval/js/i18n/<código>.js`).
Agregar un idioma es **un archivo** + **una línea en `index.html`** + **una línea en la lista de `sw.js`**. El motor no se toca.

Idiomas que hay hoy:

| Código | Qué es |
|---|---|
| `es-AR` | Idioma **base**. Tiene todas las claves (voseo: "Tocá", "frutilla"). Todo lo que falte en otro idioma cae acá. |
| `es-419`, `es-ES` | Variantes: solo traen lo que **cambia** (tuteo, "fresa", "galleta", "coche"…); el resto cae a es-AR. |
| `en` | Inglés completo (interfaz, actividades de Música y Números, informe). Nombres de notas C D E. |
| `qps-ploc`, `qps-plocm` | Pseudo-idiomas **de prueba** (generados de es-AR, +40 % de largo, acentos; el segundo va de derecha a izquierda). No son idiomas reales; en el selector aparecen marcados "(solo para pruebas)". |

Qué NO hay todavía: traducción real a otros idiomas más allá de `en`, un idioma RTL real (árabe/hebreo; el espejado se probó con el pseudo-idioma), ni audio grabado.
Letras e idiomas del contenido de cada isla (por ejemplo, las palabras y sílabas de Letras) se agregan cuando exista esa isla.

## Los 3 pasos

1. Crear `gioval/js/i18n/<código>.js` (ejemplo parcial completo: `gioval-dev/docs/ejemplos/pt-BR.js`).
2. En `gioval/index.html`, después de `en.js`: `<script src="js/i18n/<código>.js"></script>`.
3. En `gioval/sw.js`, en la lista `F`: `"js/i18n/<código>.js"`. Después subir `js/version.js`.

El código es una etiqueta BCP-47 (`pt-BR`, `fr`, `ar`...). Aparece solo en el selector de idioma de la zona de adultos.

## El archivo de un idioma

```js
Gioval.i18n.registrar("pt-BR", {
  meta: {
    nombre: "Portuguese (Brazil)", nombreNativo: "Português (Brasil)",
    dir: "ltr",                       // "rtl" para árabe, hebreo, persa...
    locale: "pt-BR",                  // para formatos de número, dinero y fecha (Intl)
    moneda: "BRL",
    voz: ["pt-BR", "pt-PT", "pt"],    // voces del aparato, en orden de preferencia (BCP-47)
    notas: ["Dó","Dó#","Ré","Ré#","Mi","Fá","Fá#","Sol","Sol#","Lá","Lá#","Si"],  // nombre de las 12 notas
    numeroEnPalabras(n, o) { /* "tres", "veintiuna" … (o.g = género) */ },        // opcional; si falta cae al del idioma de respaldo
    fallback: ["es-AR"],              // a dónde caer si falta una clave (siempre termina en es-AR y luego en)
    audio: false,                     // true si existe la carpeta audio/<código>/ (ver "Voz")
    sinVoz: false,                    // true si NO debe intentar hablar (solo texto)
  },
  textos: { "app.quien_juega": "Quem vai brincar?", /* ... */ }
});
```

Cadena de respaldo: **idioma pedido → su `fallback` → es-AR → en**. Una clave que no existe en ningún idioma se ve como la clave
(`menu.sesion`) y queda anotada en `Gioval.i18n.faltantes`; la prueba automática lo detecta.

### Reglas para escribir los textos

- **Frases completas con huecos con nombre. Nunca se arma una frase pegando pedazos.** El orden de las palabras, el
  género y los plurales cambian de un idioma a otro. Mal: `"Hay " + n + " " + objeto`. Bien: `"Hay {n} {objetos}."`.
- Formato (subconjunto de ICU MessageFormat), anidable:
  - `{nombre}` → valor.
  - `{g, select, f{una} other{un}}` → género o cualquier variante. `other` es obligatorio.
  - `{n, plural, =0{ninguno} one{# gato} other{# gatos}}` → plural según el idioma (`#` es el número formateado).
    Los idiomas con más formas (`few`, `many`, `two`...) las escriben todas.
- Una **lista** (`["Bien!", "Muy bien!"]`) es un conjunto de variantes; el código elige una al azar con `rnd(tl("clave"))`.
- Un **objeto** guarda datos (por ejemplo, los sustantivos de Números: `{ "manzana": { one:"manzana", other:"manzanas", g:"f" } }`).
  El género `g` es del idioma: en inglés no existe y la frase no lo usa.
- Los números en palabras salen de `meta.numeroEnPalabras` (hoy es y en, hasta 999).
- El texto del HTML (`data-i18n="clave"`) tiene que coincidir con la tabla es-AR: una prueba lo comprueba.
- Cada idioma pide **los mismos huecos** que es-AR para esa clave (una prueba lo comprueba).

### Qué es de cada idioma y qué no

- Cambia con el idioma: textos, nombres de las notas (Do Re Mi / C D E), números en palabras, sustantivos, formato de números,
  dinero y fechas, la voz.
- **No cambia con el idioma** (para no perder el progreso de los chicos): los ids de habilidad (`n1`, `num_c10`), la clave
  de las canciones (`store.stars`), y las melodías.
- Una isla suma sus textos con `Gioval.i18n.agregar("es-AR", {...})` desde su propio archivo (ver `AGREGAR_ISLA.md`).

## Idioma del aparato y del jugador

En la zona de adultos hay dos selectores: **Idioma del aparato** (se guarda en este aparato) e **Idioma de <jugador>**
(se guarda en `store.idioma` y viaja en el respaldo). Si el jugador no eligió, vale el del aparato. La pantalla de "¿Quién juega?" usa el del aparato.

## Voz por idioma (`js/core/voz.js`)

Cadena, de mejor a peor (cada escalón cae al siguiente):

1. **Audio grabado o pregenerado**: `audio/<código>/manifest.json` con `{ "textos": { "frase exacta": "archivo.mp3" }, "claves": { "clave.i18n": "archivo.mp3" } }` y los archivos al lado. Poner `audio: true` en `meta`.
   El service worker guarda en caché **solo el audio del idioma elegido** y borra el de los demás (los archivos de `audio/` no están en la precarga).
2. **Voz del aparato** (`speechSynthesis`): se elige la mejor según `meta.voz` (en ese orden; prefiere las que funcionan sin
   conexión; si no hay región exacta usa otra variante del mismo idioma). El adulto puede fijar una voz en **Probar voz**.
3. **Solo texto**: si el aparato no tiene voz para el idioma, la app sigue funcionando (se ve el globito) y la zona de adultos muestra un aviso discreto.

**Probar voz** (zona de adultos): muestra qué voz se está usando, la lista de voces del aparato para el idioma, y un botón para escucharla.
Todo se resuelve en el aparato; no se envía nada a ningún servidor.

## Derecha a izquierda (RTL)

Con `dir: "rtl"` se espeja la interfaz: `lang` y `dir` del documento, mascota, botones, flechas ("volver"), paneles. El CSS usa
propiedades lógicas (`inicio/fin`) y la fuente del sistema. **No se espejan** el teclado del piano y la fila de notas, las cuentas
ni los dibujos de objetos. Probalo con el pseudo-idioma `qps-plocm`.

## Cómo se prueba

`python3 gioval-dev/tests/correr.py` incluye:

- formato de textos, plurales, género, números en palabras, cadena de respaldo, formatos por idioma;
- completitud (todas las claves usadas existen; `en` = es-AR; mismos huecos; textos bien formados) y HTML = tabla es-AR;
- **es-AR idéntico a antes** (las pruebas de regresión: mismas frases, mismo progreso, 0 píxeles de diferencia);
- inglés completo (sesiones de Música y Números sin una palabra en español);
- idioma por aparato y por jugador, que se guarda, se recuerda al recargar y viaja en el respaldo;
- pseudo-idioma (+40 %) y RTL, con capturas en 360x700 y 740x330, sin desbordes nuevos respecto de es-AR;
- cadena de voz con voces simuladas, audio grabado y caché del service worker por idioma;
- agregar un idioma (ejemplo `pt-BR`) con 1 archivo + 1 línea + 1 línea y sin tocar `js/core`.

**No se puede probar en emulación:** cómo suena una voz real en un aparato real, ni la calidad de las traducciones (las revisa una persona que hable el idioma).
