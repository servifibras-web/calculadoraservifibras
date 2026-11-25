# Misiones reales y Álbum de logros reales

Actividades **fuera de la pantalla** (Construir, Experimentos, Cocina, Huerta, Arte, Hogar) que el niño hace con un
adulto y después registra en la app. Isla `Misiones` (`gioval/js/islas/misiones.js`) + contenido editable en
`gioval/js/datos/misiones.js`.

## Qué ve el niño
Tarjetas del menú: **Misión de la semana**, **Elegir una misión**, **Mi álbum** (y "Mirar: …" si dejó una misión empezada).
Cada misión: aviso de seguridad y nivel de supervisión → checklist de materiales → predicción → pasos (con voz y
temporizador opcional del módulo Alarma) → ¿qué pasó? → ¿por qué creés? (con explicación para el adulto) →
registro (frase + "salió como pensaba / distinto" + foto opcional).
El elogio es al proceso ("Miraste con atención…"), sin rachas ni puntos. **No cuenta como tiempo de pantalla** y no
tiene tope diario.

## Editar o agregar una misión (`js/datos/misiones.js`)
1. Textos en las tablas de idioma, una clave por texto, en `es-AR` (base) **y** en `en` (la prueba de completitud exige las mismas
   claves): `misiones.m.<id>.nombre`, `.resumen`, `.aviso`, `.materiales` (lista), `.pasos` (lista) y, si es experimento,
   `.prediccion.pregunta`, `.prediccion.opciones` (lista), `.observacion` (lista), `.guia`, `.explicacion`; si no, `.imaginar`.
   Se escriben con `Gioval.i18n.agregar("es-AR", {...})` al principio de `js/datos/misiones.js`. La interfaz de la isla es
   `misiones.ui.*` (frases completas; plurales con ICU, por ejemplo `{n, plural, one{# recuerdo} other{# recuerdos}}`; el código
   no tiene funciones de texto ni español escrito: `u("lista.titulo")` = `t("misiones.ui.lista.titulo")`).
   es-419 y es-ES no tienen variante propia todavía: caen a es-AR (voseo). **Las traducciones (hoy el inglés) las tiene que
   revisar una persona que hable el idioma, sobre todo los avisos de seguridad.**
2. Estructura en `MISIONES`: `id, cat, emoji, minEdad (4 o más), sup ("cerca" | "junto"), tipo ("experimento" | "observar" | "hacer")`,
   opcionales `espera:{dias}` (queda empezada hasta que el niño vuelve a mirar), `temporizador:{paso,seg}`, `revisar`.
3. `validar()` oculta cualquier misión sin materiales, supervisión o aviso, con edad menor a 4, o que nombre algo de la lista
   `PROHIBIDAS` (español) o `PROHIBIDAS_EN` (inglés) (fuego y calor, filo y corte, químicos del hogar, electricidad de red,
   resina/epoxi/solventes), **ni siquiera como "no lo hagas"**. Se revisa el texto de CADA idioma que tenga claves de esa misión.
   Un idioma nuevo con textos de misiones necesita además su lista de palabras prohibidas: si no hay, la misión se oculta
   (falla cerrado). Escribí lo seguro en positivo ("agua fría de la canilla").
4. Dato científico dudoso: `revisar:"A REVISAR: …"` en la misión. La explicación no se muestra a nadie hasta sacar la marca.
5. Correr `python3 gioval-dev/tests/correr.py misiones`.

## Datos y privacidad
- Álbum: `store.misiones.album[perfil]`; pendientes `store.misiones.pend`, semana `store.misiones.semana`, edad `store.misiones.edad`
  (se crean al usarse, sin migración). **No se agregó ningún otro campo al almacén**: `store.misiones` es lo único nuevo y no
  necesita migración (el almacén v2 de cimientos, con `idioma:{}`, no cambia). El idioma de cada niño ya lo guarda `store.idioma`.
- Fotos: Blob en IndexedDB (`Gioval.almacen.fotos`), **solo en el aparato**. Se achican a 1024 px y se re-codifican en JPEG
  (se pierden los metadatos de la cámara, incluida la ubicación). La foto solo se puede sacar si un adulto activa el permiso
  (candado de multiplicación) en cada misión. Nada se sube.
- Dictado por voz: solo si el adulto lo activa. **Ojo:** en Chrome/Android el reconocimiento de voz del navegador puede mandar el
  audio a un servicio de internet; por eso queda apagado por defecto.
- Respaldo: `Exportar respaldo` incluye las fotos (data URL en la clave `fotos` del JSON). `Restaurar` recupera álbum y fotos; antes
  guarda una copia de las fotos actuales en la tabla `respaldo`. Un respaldo viejo sin la clave `fotos` no toca las fotos de hoy.
- Adultos: ⚙️ → "Misiones" (edad del niño, misión de la semana) y "Álbum (adultos)" para borrar recuerdos o solo la foto.

## Cambios en `js/core` (mínimos y genéricos)
- `almacen.js`: `exportar()` es async e incluye fotos; `leerRespaldo()` devuelve `fotos`; `restaurar(datos, fotos)`;
  `fotos.todas/exportarTodas/reemplazarTodas`; `idbAll` devuelve `[]` sin IndexedDB.
- `adultos.js`: pasa las fotos al restaurar, muestra "Fotos: N" en la vista previa (clave `respaldo.fotos`, hueco `{fotos}` en
  `respaldo.vista`, en todos los idiomas) y emite `Gioval.emit("panel")`.
- `ui.js`: `PACK.menuPropio()`, `PACK.etiquetaTiempo()` y `PACK.hablaMenu()` opcionales; **son funciones** (devuelven el texto en el
  idioma actual), no textos fijos.
- `i18n/es-AR.js` y `en.js`: `almacen.err.foto_danada`, `almacen.err.foto_leer`, `respaldo.fotos` y `{fotos}` en `respaldo.vista`.
