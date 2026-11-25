"use strict";
/* ============ ISLA LETRAS: DATOS EDITABLES ============
   Todo el contenido de la isla vive acá (la lógica está en js/islas/letras.js y no lleva textos ni listas).
   1) TEXTOS: todo lo que se LEE o se DICE en pantalla, agrupado (para traducir / revisar tono). Los {nombres} entre
      llaves se reemplazan al usarse. Una lista de frases = se elige una al azar.
   2) HABILIDADES: la escalera por edades (id, nivel, edad típica, eje curricular, umbral de "rápido").
   3) CONTENIDO: palabras con dibujo, rimas, frases, comprensión, ortografía.

   ALINEACIÓN CURRICULAR (comentarios orientativos; NO son citas textuales y están "a revisar" por una persona docente):
   - NAP de Lengua, Primer Ciclo (Argentina, educ.ar). Ejes: "Comprensión y producción oral", "Lectura",
     "Escritura" y "Reflexión sobre la lengua (sistema, norma y uso) y los textos". Verificado: que esos ejes existen
     con esos nombres. A REVISAR: qué saber puntual de cada eje cubre cada habilidad (la columna `eje` es una
     aproximación nuestra).
   - Progresiones de los aprendizajes, Prácticas del Lenguaje, Primer ciclo (GCBA, 2018). Verificado: el documento
     existe y trabaja el pasaje de la escritura silábica a la alfabética. A REVISAR: el mapeo fino a cada
     progresión (columna `prog`); aquí solo se anota el ámbito general.
   - La app NO enseña "método": practica y verifica destrezas (reconocer letras, conciencia fonológica, lectura de
     palabras/frases, ortografía de uso común) como complemento de la escuela.

   REGLA DE CONTENIDO: vocabulario cotidiano argentino, sin marcas ni personajes. Los ejercicios "de oído" evitan
   pares que se confunden en el habla rioplatense (b/v, s/z/c, ll/y, g/j, k/q/c, h muda): esas letras se enseñan
   por nombre, por forma y por palabras escritas con dibujo, no por "el sonido inicial".
   IDEA FUTURA (no implementada): leer en voz alta con micrófono y reconocimiento de voz. Esta entrega es solo toque. */

const TEXTOS = {
  isla: {
    nombre: "Isla Letras", sub: "¡A jugar con las letras!",
    bienvenida: "¡Isla Letras! Empezamos con la sesión de hoy, o elegí otra cosa.",
    outro: "Ahora, ¡buscá letras en carteles, envases y libros!",
    capTail: "Ahora, a mirar libros y carteles de verdad. ¡Mañana seguimos con las letras!",
    notaInforme: "En Letras, \"saltada\" significa que se marcó como sabida sin practicarla (por dominio rápido, por las preguntas iniciales o por el juego de ubicación) y se vuelve a comprobar sin ayuda en el chequeo semanal; si no sale, vuelve a práctica. Los tiempos son de respuesta al primer intento, sin contar lo que tarda la voz."
  },
  letras: { A: "a", B: "be larga", C: "ce", D: "de", E: "e", F: "efe", G: "ge", H: "hache", I: "i", J: "jota", K: "ka", L: "ele", M: "eme", N: "ene", Ñ: "eñe", O: "o", P: "pe", Q: "cu", R: "erre", S: "ese", T: "te", U: "u", V: "ve corta", W: "doble ve", X: "equis", Y: "i griega", Z: "zeta" },
  habilidades: {
    let_v: "Las vocales", let_cs1: "Contar los pedacitos de las palabras", let_c1: "M, P, S, L y T", let_s1: "¿Con qué letra empieza?",
    let_ri1: "Rimas con dibujos", let_c2: "N, D, C, B, R, F y G", let_p1: "De la letra al dibujo", let_sil: "Armar con sílabas",
    let_f1: "¿Qué vocal falta?", let_s2: "Primer sonido: más letras", let_c3: "J, V, Z, H e Y", let_ms: "Mayúsculas y minúsculas",
    let_arm: "Armar palabras con letras", let_sp: "Separar en sílabas", let_f2: "¿Qué letra falta?", let_c4: "Ñ, Q, K, X y W",
    let_nom: "Escribir mi nombre", let_rs: "Leer sílabas", let_rp1: "Leer palabras cortas", let_abc1: "El abecedario: antes y después",
    let_rf1: "Leer frases cortas", let_rp2: "Leer palabras largas", let_comp1: "Entender una frase", let_ora: "Ordenar oraciones",
    let_dig: "Letras que van juntas: LL, RR, CH, QU, GU", let_tr: "Sílabas trabadas: BR, FL, TR…", let_may: "Mayúsculas y puntos",
    let_ort: "Ortografía de todos los días", let_abc2: "Orden alfabético", let_comp2: "Entender un textito"
  },
  /* los 8 "tramos" de la escalera (cada habilidad pertenece a uno) */
  tramos: [
    "Vocales y contar pedacitos", "Primeras letras y sonidos", "Más letras y armar con sílabas", "Armar palabras y todas las letras",
    "Leer sílabas y palabras", "Leer frases y entender", "Oraciones, trabadas y letras juntas", "Ortografía, abecedario y textos"
  ],
  menu: {
    preguntas: { t: "Preguntas para adultos", s: "Dos minutos, una sola vez" },
    ubicacion: { t: "Juego de ubicación", s: "Unos 5 minutos, sin apuro" },
    resultado: { t: "Resultado de ubicación", s: "Para adultos: revisar y aceptar" },
    informe: { t: "Informe para adultos", s: "Aciertos, tiempos y saltos" }
  },
  bienvenida: {
    titulo: "¡Bienvenidos a la Isla Letras!",
    texto: "Para que {nombre} empiece en el lugar justo, necesitamos que una persona adulta responda unas preguntas (dos minutos, una sola vez). Después se puede hacer un juego de ubicación para ajustar.",
    adulto: "Soy una persona adulta", despues: "Más tarde"
  },
  intake: {
    titulo: "Preguntas para adultos: Letras de {nombre}",
    intro: "Respondé lo que veas en casa. No hay respuestas buenas ni malas: sirven para empezar en un lugar cómodo. Después se puede cambiar.",
    pEdad: "¿Cuántos años tiene?", pLetras: "¿Cuántas letras reconoce?", pLee: "¿Qué lee?", pNombre: "¿Escribe su nombre?",
    edad: [{ v: 4, t: "4 años" }, { v: 5, t: "5 años" }, { v: 6, t: "6 años" }, { v: 7, t: "7 años" }, { v: 8, t: "8 o más" }],
    letras: [{ v: 0, t: "Ninguna todavía" }, { v: 1, t: "Algunas (las vocales o las de su nombre)" }, { v: 2, t: "Casi todas las mayúsculas" }, { v: 3, t: "Todas, mayúsculas y minúsculas" }],
    lee: [{ v: "no", t: "Todavía no lee" }, { v: "silabas", t: "Lee sílabas sueltas (MA, PA, SO)" }, { v: "palabras", t: "Lee palabras cortas (MESA, GATO)" }, { v: "frases", t: "Lee frases cortas (EL GATO COME)" }, { v: "textos", t: "Lee textos cortos y entiende" }],
    nombre: [{ v: "no", t: "Todavía no" }, { v: "copia", t: "Lo copia de un modelo" }, { v: "solo", t: "Lo escribe solo" }],
    guardar: "Guardar", cancelar: "Cancelar", falta: "Faltan respuestas: tocá una opción en cada pregunta.",
    sugerido: "Con esas respuestas, {nombre} empezaría en: «{habilidad}» (tramo {tramo} de 8: {nombreTramo}).",
    sugeridoCero: "Con esas respuestas, {nombre} empezaría desde el principio: «{habilidad}».",
    usar: "Usar este punto de partida", jugar: "Hacer el juego de ubicación (≈5 min)", masTarde: "Decidir más tarde",
    aviso: "Lo que se marque como sabido se vuelve a comprobar sin ayuda en el chequeo semanal; si no sale, vuelve a práctica."
  },
  ubicacion: {
    titulo: "Juego de ubicación",
    intro: "¡Hola, {nombre}! Vamos a jugar con las letras. No es un examen y no hay apuro. Si no sabés alguna, tocá «No sé» y seguimos.",
    nose: "No sé", nose2: "🤷 No sé",
    gracias: ["¡Gracias! Seguimos.", "¡Anotado! Vamos a la próxima.", "¡Listo! Sigamos jugando.", "¡Bien! Probemos otra."],
    fin: "¡Terminamos el juego, {nombre}! Probaste un montón de cosas. Ahora le toca a un adulto ver cómo te fue.",
    titResumen: "Resultado del juego de ubicación", fila: "Tramo {n}: {nombre}",
    ok: "✅ lo hace bien ({a}/{b})", dudoso: "🟡 a veces ({a}/{b})", no: "❌ todavía no ({a}/{b})", sinPreguntar: "— no se preguntó",
    propuesta: "Propongo empezar en el tramo {tramo}: «{habilidad}». Se marcarán como ya sabidas {n} habilidades de los tramos anteriores.",
    propuestaCero: "Propongo empezar desde el principio. No se marca nada como sabido.",
    antes: "◀ Empezar antes", despues: "Empezar después ▶", aceptar: "Aceptar", descartar: "No cambiar nada",
    resumenTiempo: "Respondió {n} preguntas en {min} min.", aceptada: "¡Listo! Ya está guardado el punto de partida.",
    pendiente: "Resultado sin revisar"
  },
  informe: {
    titulo: "INFORME DE LETRAS — {nombre}", fecha: "Fecha: {fecha}",
    datos: "Respuestas de los adultos ({fecha}): {edad} · letras: {letras} · lectura: {lee} · nombre: {nombreEscribe}",
    sinDatos: "Todavía no se respondieron las preguntas para adultos.",
    inicio: "Punto de partida: tramo {tramo} («{habilidad}»), definido por {origen}.",
    origenPreguntas: "las preguntas para adultos", origenUbicacion: "el juego de ubicación", origenAdulto: "el juego de ubicación, ajustado por un adulto",
    ubic: "Juego de ubicación ({fecha}): {n} preguntas.", ubicTramo: "   Tramo {n}: {txt}",
    habilidades: "HABILIDADES", copiar: "Copiar", whatsapp: "WhatsApp", cerrar: "Cerrar", cambiar: "Cambiar respuestas",
    resumenSaltos: "SALTOS: {n} habilidad(es) saltada(s): {c} confirmada(s) sin ayuda, {r} volvieron a práctica, {p} pendientes de comprobar.",
    hab: "• {name}: {estado} (edad típica: {edad} años · tramo {tramo})", dom: "dominada", prac: "en práctica", saltada: "saltada",
    acc: "   Aciertos al primer intento: primeros {a} → últimos {b}", ret: "   Retención (acierto ≥1 día después de practicar): {r}",
    chequeos: "CHEQUEOS SIN AYUDA (Letras)", sinChequeos: "   (todavía no hizo ninguno)", sinDatosHab: "   (todavía sin práctica)",
    comoLeerlo: "Cómo leerlo: los aciertos son al PRIMER intento, sin contar ayudas. La retención mide si lo recuerda tras dormir y pasar días. El chequeo semanal se hace sin pistas. Las edades son orientativas y nunca limitan: cada chico avanza a su ritmo.",
    etiquetas: { si: "sí", no: "no" }
  },
  dominio: {
    porPreguntas: "según las preguntas para adultos del {fecha}",
    porUbic: "juego de ubicación del {fecha} ({n} preguntas)"
  },
  actividades: {
    lname: {
      ok: ["¡Te fijaste bien en la letra!", "¡Escuchar y mirar funcionó!", "¡Eso es! Fijarse en cada letra ayuda."],
      pedir: ["Tocá la letra {nombre}.", "¿Dónde está la {nombre}?", "Buscá la {nombre}."], pedirAyuda: "Tocá la letra {nombre}, la de {palabra}.",
      tip: "Mirá bien cada letra. Saqué una opción.", reveal: "Mirá, es la {nombre}, la de {palabra}."
    },
    lsound: {
      ok: ["¡Escuchaste el primer sonido!", "¡Decir la palabra despacito ayuda!", "¡Eso es! Prestaste atención al sonido."],
      pedirAyuda: "Mirá: {palabra}. ¿Con qué letra empieza?", pedir: "Escuchá: {palabra}. ¿Con qué letra empieza?",
      tip: "Decí la palabra despacito: {palabra}. Saqué una opción.", reveal: "Mirá, {palabra} empieza con la {nombre}."
    },
    lpic: {
      ok: ["¡Relacionaste la letra con el dibujo!", "¡Pensaste en el sonido y salió!", "¡Eso es! Escuchar el principio ayuda."],
      pedirAyuda: "Buscá lo que empieza con la {nombre}. ¿Es {a}, {b} o {c}?", pedirAyuda2: "Buscá lo que empieza con la {nombre}. ¿Es {a} o {b}?",
      pedir: "¿Qué dibujo empieza con la {nombre}?",
      tip: "Decí cada nombre despacito. Saqué una opción.", reveal: "Mirá, {palabra} empieza con la {nombre}."
    },
    lcount: {
      ok: ["¡Contaste los pedacitos!", "¡Aplaudir las sílabas ayuda!", "¡Eso es! Escuchar cada pedacito funciona."],
      pedirAyuda: "Aplaudimos: {silabas}. ¿Cuántos pedacitos tiene {palabra}?", pedir: "Decí despacito: {palabra}. ¿Cuántos pedacitos tiene?",
      tip: "Aplaudí cada pedacito: {silabas}. Saqué una opción.", reveal: "{palabra} tiene {n}: {silabas}."
    },
    lrhyme: {
      ok: ["¡Escuchaste cómo terminan!", "¡Fijarse en el final ayuda!", "¡Eso es! Encontraste la rima."],
      pedirAyuda: "{palabra} rima con… ¡{rima}! Buscá el dibujo que termina igual que {palabra}.", pedir: "¿Cuál rima con {palabra}? Fijate cómo terminan.",
      tip: "Fijate en el final de cada palabra. Saqué una opción.", reveal: "Mirá, {palabra} y {rima} terminan igual: {fin}."
    },
    lsyl: {
      ok: ["¡Juntaste las sílabas!", "¡Armaste la palabra sílaba por sílaba!", "¡Eso es! Decirla en voz alta ayuda."],
      pedir: "¿Qué es esto? Armala con sílabas.", pedirAyuda: "Armá la palabra {palabra} con sílabas.",
      tip: "Decí la palabra despacito y escuchá cada pedacito.", reveal: "Ahora va {silaba}."
    },
    lbuild: {
      ok: ["¡Armaste la palabra letra por letra!", "¡Ordenaste las letras con cuidado!", "¡Eso es! Ir de a una letra funciona."],
      pedir: "¿Qué es esto? Armá la palabra con las letras.", pedirAyuda: "Armá la palabra {palabra}.",
      tip: "Una letra por vez, de izquierda a derecha.", reveal: "Ahora va la {nombre}."
    },
    lmissing: {
      ok: ["¡Miraste la palabra con cuidado!", "¡Leíste y completaste!", "¡Eso es! Fijarse en el dibujo ayuda."],
      pedir: "Mirá el dibujo y completá la palabra. ¿Qué letra falta?", pedirAyuda: "Falta una letra en {palabra}. ¿Cuál es?",
      tip: "Leé la palabra despacito. Saqué una opción.", reveal: "Mirá, falta la {nombre}: {palabra}."
    },
    lcase: {
      ok: ["¡Encontraste la pareja!", "¡Miraste bien la forma!", "¡Eso es! Cada letra tiene sus dos versiones."],
      pedirMin: "Tocá la letra chiquita que es pareja de esta.", pedirMay: "Tocá la letra grande que es pareja de esta.",
      pedirAyudaMin: "Tocá la letra chiquita de la {nombre}.", pedirAyudaMay: "Tocá la letra grande de la {nombre}.",
      tip: "Fijate bien en la forma. Saqué una opción.", reveal: "Mirá, esta es la pareja de la {nombre}."
    },
    lsplit: {
      ok: ["¡Separaste los pedacitos!", "¡Aplaudir las sílabas ayuda!", "¡Eso es! Cortaste la palabra en su lugar."],
      pedir: "¿Cómo se separa {palabra} en sílabas?", pedirAyuda: "Aplaudimos: {silabas}. ¿Cuál está bien separada?",
      tip: "Aplaudí cada pedacito. Saqué una opción.", reveal: "Mirá, se separa así: {silabas}."
    },
    lnombre: {
      ok: ["¡Escribiste tu nombre letra por letra!", "¡Ordenaste las letras de tu nombre!", "¡Eso es! Tu nombre es tuyo."],
      pedir: "Armá tu nombre, {nombre}.", pedirAyuda: "Armá tu nombre, {nombre}: {deletreo}.",
      tip: "Una letra por vez, de izquierda a derecha.", reveal: "Ahora va la {letra}."
    },
    lrsyl: {
      ok: ["¡Leíste la sílaba!", "¡Fijarte en las dos letras funcionó!", "¡Eso es! Leer de a pedacitos ayuda."],
      pedirAyuda: "Esta sílaba dice {silaba}. Buscá el dibujo que empieza con {silaba}.", pedir: "Leé la sílaba y tocá el dibujo que empieza con ella.",
      pedirInv: "Mirá el dibujo y tocá con qué sílaba empieza.", pedirInvAyuda: "{palabra} empieza con {silaba}. Tocá esa sílaba.",
      tip: "Leé las dos letras juntas, despacito. Saqué una opción.", reveal: "Mirá, {palabra} empieza con {silaba}."
    },
    lrword: {
      ok: ["¡Leíste la palabra!", "¡Leer despacito funcionó!", "¡Eso es! Fijarse en todas las letras ayuda."],
      pedirAyuda: "Esta palabra dice {palabra}. Tocá el dibujo.", pedir: "Leé la palabra y tocá el dibujo.",
      tip: "Leé sílaba por sílaba. Saqué una opción.", reveal: "Mirá, dice {palabra}."
    },
    lrphrase: {
      ok: ["¡Leíste la frase entera!", "¡Leer palabra por palabra funcionó!", "¡Eso es! Fijarse en cada palabra ayuda."],
      pedirAyuda: "Dice: {frase}. Tocá el dibujo que cuenta eso.", pedir: "Leé la frase y tocá el dibujo que la cuenta.",
      tip: "Leé cada palabra con calma. Saqué una opción.", reveal: "Mirá, dice: {frase}."
    },
    labc: {
      ok: ["¡Pensaste en el abecedario!", "¡Recitar el abecedario ayuda!", "¡Eso es! Fijarte en el orden funcionó."],
      despues: "¿Qué letra va después de la {nombre}?", antes: "¿Qué letra va antes de la {nombre}?",
      tip: "Decí el abecedario despacito. Saqué una opción.", reveal: "Mirá, la {nombre2} va {donde} de la {nombre}.", dDespues: "después", dAntes: "antes"
    },
    lcomp: {
      ok: ["¡Leíste y entendiste!", "¡Volver al texto ayuda!", "¡Eso es! Pensar en lo que dice funciona."],
      pedirAyuda: "{texto} {pregunta}", pedir: "Leé con calma y respondé.",
      tip: "Volvé a leer el textito despacio. Saqué una opción.", reveal: "Mirá, el texto dice: {texto}"
    },
    lorden: {
      ok: ["¡Ordenaste la oración!", "¡Leer cada palabra ayudó!", "¡Eso es! Una oración tiene su orden."],
      pedir: "Ordená las palabras para armar la oración.", pedirAyuda: "Armá la oración: {frase}.",
      tip: "Pensá cuál palabra va primero. Saqué una pista.", reveal: "Ahora va «{palabra}»."
    },
    lcluster: {
      ok: ["¡Elegiste las letras que van juntas!", "¡Leer la palabra entera ayudó!", "¡Eso es! Fijarse en el dibujo ayuda."],
      pedir: "Mirá el dibujo. ¿Qué letras faltan?", pedirAyuda: "Falta un pedacito en {palabra}. ¿Cuál es?",
      tip: "Leé la palabra completa con cada opción. Saqué una opción.", reveal: "Mirá, va {grupo}: {palabra}."
    },
    lbien: {
      ok: ["¡Miraste bien cómo se escribe!", "¡Leíste con atención!", "¡Eso es! Fijarse en los detalles ayuda."],
      pedir: "¿Cuál está bien escrita?", pedirDib: "Mirá el dibujo. ¿Cuál está bien escrita?", pedirAyuda: "Es {palabra}. ¿Cuál está bien escrita?",
      tip: "Leé cada una despacito. Saqué una opción.", reveal: "Mirá, está bien escrita así: {correcta}. {regla}"
    },
    lalfa: {
      ok: ["¡Ordenaste con el abecedario!", "¡Mirar la primera letra funcionó!", "¡Eso es! El abecedario tiene su orden."],
      pedir: "Tocá las palabras en orden del abecedario, empezando por la que va primero.", pedirAyuda: "Fijate en la primera letra de cada palabra. ¿Cuál va primero en el abecedario?",
      tip: "Mirá la primera letra de cada una. Saqué una pista.", reveal: "Ahora va «{palabra}»."
    }
  }
};

/* ---------- Escalera de habilidades ----------
   id          no renombrar nunca una vez publicado (es parte del progreso guardado).
   nivel       tramo 0..7 de la escalera (ver TEXTOS.tramos). Las preguntas iniciales y el juego de ubicación
               marcan como sabidas las habilidades de tramos anteriores al punto de partida.
   edad        edad típica en que suele aparecer (4..7): solo informativa, nunca limita.
   eje         eje de los NAP de Lengua (a revisar): oral | lectura | escritura | reflexion
   rtRapido    mediana de tiempo de respuesta (ms, después de que termina la voz) a partir de la cual se considera "rápido"
               para el salto por dominio. Valores iniciales razonables; AJUSTAR con datos reales.
   sonda       true = sirve para el juego de ubicación (respuesta de un solo toque)
   saltable    false = nunca se salta por dominio rápido */
const HABILIDADES = [
  { id: "let_v", type: "lname", icon: "🅰️", nivel: 0, edad: 4, eje: "lectura", rtRapido: 2800, sonda: true, letters: "AEIOU".split(""), prior: [], req: [] },
  { id: "let_cs1", type: "lcount", icon: "👏", nivel: 0, edad: 4, eje: "oral", rtRapido: 3500, sonda: true, max: 3, req: [] },
  { id: "let_c1", type: "lname", icon: "🔤", nivel: 1, edad: 4, eje: "lectura", rtRapido: 2800, sonda: true, letters: "MPSLT".split(""), prior: "AEIOU".split(""), req: ["let_v"] },
  { id: "let_s1", type: "lsound", icon: "🐒➡️M", nivel: 1, edad: 4, eje: "oral", rtRapido: 3200, sonda: true, letters: "AEIOUMPSLT".split(""), req: ["let_c1"] },
  { id: "let_ri1", type: "lrhyme", icon: "🎶", nivel: 1, edad: 4, eje: "oral", rtRapido: 4200, sonda: true, req: ["let_cs1"] },
  { id: "let_c2", type: "lname", icon: "🔡", nivel: 2, edad: 5, eje: "lectura", rtRapido: 3000, sonda: true, letters: "NDCBRFG".split(""), prior: "AEIOUMPSLT".split(""), req: ["let_c1"] },
  { id: "let_p1", type: "lpic", icon: "🅼➡️🐒", nivel: 2, edad: 5, eje: "lectura", rtRapido: 3800, sonda: true, letters: "AEIOUMPSLT".split(""), req: ["let_s1"] },
  { id: "let_sil", type: "lsyl", icon: "🧱", nivel: 2, edad: 5, eje: "escritura", rtRapido: 9000, req: ["let_s1", "let_cs1"] },
  { id: "let_f1", type: "lmissing", icon: "🧩", nivel: 2, edad: 5, eje: "escritura", rtRapido: 4000, sonda: true, modo: "vocal", len: [3, 5], req: ["let_s1"] },
  { id: "let_s2", type: "lsound", icon: "🎧", nivel: 3, edad: 5, eje: "oral", rtRapido: 3400, sonda: true, letters: "AEIOUMPSLTNDFRBCGJ".split(""), req: ["let_s1", "let_c2"] },
  { id: "let_c3", type: "lname", icon: "🔠", nivel: 3, edad: 5, eje: "lectura", rtRapido: 3200, sonda: true, letters: "JVZHY".split(""), prior: "NDCBRFG".split(""), req: ["let_c2"] },
  { id: "let_ms", type: "lcase", icon: "Aa", nivel: 3, edad: 5, eje: "lectura", rtRapido: 3000, sonda: true, letters: "AEIOUMPSLTNDCBRFGJVZHY".split(""), req: ["let_c2"] },
  { id: "let_arm", type: "lbuild", icon: "✏️", nivel: 3, edad: 5, eje: "escritura", rtRapido: 12000, len: [3, 6], req: ["let_sil", "let_f1"] },
  { id: "let_sp", type: "lsplit", icon: "✂️", nivel: 3, edad: 6, eje: "reflexion", rtRapido: 5200, sonda: true, req: ["let_sil"] },
  { id: "let_f2", type: "lmissing", icon: "🧩🔤", nivel: 3, edad: 6, eje: "escritura", rtRapido: 4500, sonda: true, modo: "letra", len: [4, 8], req: ["let_f1", "let_s2"] },
  { id: "let_c4", type: "lname", icon: "🔠", nivel: 4, edad: 6, eje: "lectura", rtRapido: 3500, sonda: true, letters: "ÑQKXW".split(""), prior: "JVZHY".split(""), req: ["let_c3"] },
  { id: "let_nom", type: "lnombre", icon: "🦊", nivel: 4, edad: 5, eje: "escritura", rtRapido: 16000, saltable: false, req: ["let_arm"] },
  { id: "let_rs", type: "lrsyl", icon: "MA", nivel: 4, edad: 6, eje: "lectura", rtRapido: 3600, sonda: true, cons: "MPSLT", req: ["let_p1", "let_c2"] },
  { id: "let_rp1", type: "lrword", icon: "📖", nivel: 4, edad: 6, eje: "lectura", rtRapido: 4200, sonda: true, banco: "cvcv", req: ["let_rs"] },
  { id: "let_abc1", type: "labc", icon: "🔤➡️", nivel: 4, edad: 6, eje: "reflexion", rtRapido: 5000, sonda: true, req: ["let_c3"] },
  { id: "let_rf1", type: "lrphrase", icon: "💬", nivel: 5, edad: 6, eje: "lectura", rtRapido: 8000, sonda: true, req: ["let_rp1"] },
  { id: "let_rp2", type: "lrword", icon: "📚", nivel: 5, edad: 6, eje: "lectura", rtRapido: 5200, sonda: true, banco: "largas", req: ["let_rp1", "let_c3"] },
  { id: "let_comp1", type: "lcomp", icon: "🤔", nivel: 5, edad: 6, eje: "lectura", rtRapido: 9000, sonda: true, banco: "comp1", req: ["let_rf1"] },
  { id: "let_ora", type: "lorden", icon: "🧩📝", nivel: 6, edad: 7, eje: "escritura", rtRapido: 20000, req: ["let_rf1"] },
  { id: "let_dig", type: "lcluster", icon: "🔗", nivel: 6, edad: 7, eje: "reflexion", rtRapido: 5200, sonda: true, banco: "dig", req: ["let_rp2"] },
  { id: "let_tr", type: "lcluster", icon: "🔗🔤", nivel: 6, edad: 7, eje: "reflexion", rtRapido: 5200, sonda: true, banco: "tr", req: ["let_rp2"] },
  { id: "let_may", type: "lbien", icon: "Aa.", nivel: 6, edad: 7, eje: "reflexion", rtRapido: 6000, sonda: true, banco: "may", req: ["let_rf1"] },
  { id: "let_ort", type: "lbien", icon: "✅", nivel: 7, edad: 7, eje: "reflexion", rtRapido: 6000, sonda: true, banco: "orto", req: ["let_dig", "let_may"] },
  { id: "let_abc2", type: "lalfa", icon: "🔤📚", nivel: 7, edad: 7, eje: "reflexion", rtRapido: 12000, req: ["let_abc1", "let_rp2"] },
  { id: "let_comp2", type: "lcomp", icon: "📰", nivel: 7, edad: 7, eje: "lectura", rtRapido: 14000, sonda: true, banco: "comp2", req: ["let_comp1", "let_ora"] },
];

/* ---------- Ubicación inicial a partir de las preguntas para adultos ----------
   Cada respuesta sugiere un tramo desde donde practicar (los tramos anteriores se marcan como sabidos y se
   re-comprueban sin ayuda). Se toma el MAYOR de los tramos sugeridos. Se resta uno en lectura a propósito
   (los adultos suelen ser generosos al decir "lee"). La EDAD no salta nada (no es evidencia): solo decide dónde
   arranca el juego de ubicación cuando las respuestas no dicen nada. */
const INICIO = {
  letras: { 0: 0, 1: 0, 2: 2, 3: 3 },
  lee: { no: 0, silabas: 3, palabras: 4, frases: 5, textos: 6 },
  nombre: { no: 0, copia: 0, solo: 1 },
  edadParaUbicacion: { 4: 0, 5: 1, 6: 2, 7: 3, 8: 4 }
};

/* ---------- Contenido: palabras con dibujo ----------
   "SÍ-LA-BAS" con guiones y mayúsculas; el dibujo es un emoji (sin marcas ni personajes). Vocabulario cotidiano argentino.
   Agregá palabras acá: la lógica deduce sola si sirven para cada ejercicio. NO repetir el mismo dibujo en dos palabras
   (las opciones se confundirían). Las rimas, comprensión y demás referencian palabras de esta lista. */
const PALABRAS = [
  ["A-BE-JA", "🐝"], ["AU-TO", "🚗"], ["A-VIÓN", "✈️"], ["A-RA-ÑA", "🕷️"], ["ÁR-BOL", "🌳"], ["A-VE", "🐦"],
  ["E-LE-FAN-TE", "🐘"], ["ES-TRE-LLA", "⭐"], ["IS-LA", "🏝️"], ["I-MÁN", "🧲"],
  ["O-SO", "🐻"], ["O-VE-JA", "🐑"], ["O-RE-JA", "👂"], ["O-JO", "👁️"], ["U-VA", "🍇"], ["U-NI-COR-NIO", "🦄"], ["U-ÑA", "💅"],
  ["MA-NO", "✋"], ["MO-NO", "🐒"], ["MA-RI-PO-SA", "🦋"], ["MO-TO", "🏍️"], ["MAN-ZA-NA", "🍎"], ["MA-PA", "🗺️"], ["MA-TE", "🧉"],
  ["ME-DIA-LU-NA", "🥐"], ["MO-CHI-LA", "🎒"], ["MO-ÑO", "🎀"], ["MA-MÁ", "👩"],
  ["PA-TO", "🦆"], ["PAN", "🍞"], ["PE-LO-TA", "⚽"], ["PE-RRO", "🐶"], ["PEZ", "🐟"], ["PI-ÑA", "🍍"], ["PA-PA", "🥔"], ["PE-RA", "🍐"],
  ["PUER-TA", "🚪"], ["PI-LE-TA", "🏊"], ["PLA-TO", "🍽️"], ["PLA-NE-TA", "🪐"], ["PA-QUE-TE", "📦"], ["PRIN-CE-SA", "👸"], ["PIN-TU-RA", "🎨"], ["PUL-PO", "🐙"], ["PAL-TA", "🥑"],
  ["SOL", "☀️"], ["SO-PA", "🥣"], ["SI-LLA", "🪑"], ["SO-FÁ", "🛋️"], ["SAN-DÍA", "🍉"], ["SER-PIEN-TE", "🐍"], ["SO-BRE", "✉️"], ["SE-MÁ-FO-RO", "🚦"],
  ["LU-NA", "🌙"], ["LE-ÓN", "🦁"], ["LI-BRO", "📖"], ["LO-RO", "🦜"], ["LÁ-PIZ", "✏️"], ["LI-MÓN", "🍋"], ["LLA-VE", "🔑"], ["LE-CHE", "🥛"],
  ["LO-BO", "🐺"], ["LLA-MA", "🦙"], ["LA-DRI-LLO", "🧱"], ["LÁM-PA-RA", "💡"],
  ["TOR-TU-GA", "🐢"], ["TO-MA-TE", "🍅"], ["TREN", "🚆"], ["TI-JE-RA", "✂️"], ["TE-LÉ-FO-NO", "📞"], ["TI-GRE", "🐯"], ["TO-RO", "🐂"], ["TRI-GO", "🌾"],
  ["TAM-BOR", "🥁"], ["TO-RRE", "🗼"], ["TIE-RRA", "🌎"], ["TA-XI", "🚕"],
  ["NU-BE", "☁️"], ["NA-RAN-JA", "🍊"], ["NA-RIZ", "👃"], ["NA-VE", "🚀"], ["NI-ÑO", "🧒"], ["NO-TA", "🎵"], ["ÑO-QUIS", "🍝"],
  ["DA-DO", "🎲"], ["DE-DO", "☝️"], ["DI-NO-SAU-RIO", "🦖"], ["DEL-FÍN", "🐬"], ["DUL-CE", "🍬"], ["DRA-GÓN", "🐉"], ["DI-A-MAN-TE", "💎"], ["DU-RAZ-NO", "🍑"],
  ["CA-SA", "🏠"], ["CA-MA", "🛏️"], ["CA-BA-LLO", "🐴"], ["CO-CO", "🥥"], ["CO-NE-JO", "🐰"], ["CA-MIÓN", "🚚"], ["CUA-DER-NO", "📓"], ["CA-FÉ", "☕"],
  ["CA-RA-COL", "🐌"], ["CAM-PA-NA", "🔔"], ["CAM-PO", "🏞️"], ["CE-BRA", "🦓"], ["CO-LEC-TI-VO", "🚌"], ["CHO-CLO", "🌽"], ["CRO-CO-DI-LO", "🐊"], ["CU-CHA-RA", "🥄"],
  ["BA-NA-NA", "🍌"], ["BO-TA", "🥾"], ["BAR-CO", "⛵"], ["BA-LLE-NA", "🐋"], ["BE-BÉ", "👶"], ["BI-CI-CLE-TA", "🚲"], ["BU-FAN-DA", "🧣"], ["BRU-JA", "🧙"],
  ["BLU-SA", "👚"], ["BOM-BE-RO", "🚒"], ["BE-SO", "😘"],
  ["RA-NA", "🐸"], ["RA-TÓN", "🐭"], ["RE-GA-LO", "🎁"], ["RE-LOJ", "⏰"], ["RO-SA", "🌹"], ["RA-DIO", "📻"], ["RE-ME-RA", "👕"], ["RA-MA", "🌿"],
  ["FLOR", "🌸"], ["FRU-TI-LLA", "🍓"], ["FUE-GO", "🔥"], ["FAN-TAS-MA", "👻"], ["FO-TO", "📷"], ["FLE-CHA", "🏹"],
  ["GA-TO", "🐱"], ["GLO-BO", "🎈"], ["GUI-TA-RRA", "🎸"], ["GA-LLI-NA", "🐔"], ["GU-SA-NO", "🐛"], ["GI-RA-SOL", "🌻"], ["GO-TA", "💧"], ["GRI-LLO", "🦗"],
  ["GUI-SO", "🍲"], ["GA-LLE-TI-TA", "🍪"], ["GUAN-TE", "🧤"],
  ["HE-LA-DO", "🍦"], ["HO-JA", "🍃"], ["HUE-VO", "🥚"], ["HOR-MI-GA", "🐜"], ["HA-DA", "🧚"],
  ["VA-CA", "🐄"], ["VE-LA", "🕯️"],
  ["ZA-PA-TO", "👟"], ["ZO-RRO", "🦊"], ["ZA-NA-HO-RIA", "🥕"],
  ["JI-RA-FA", "🦒"], ["JA-BÓN", "🧼"], ["JU-GO", "🧃"],
  ["KO-A-LA", "🐨"], ["KI-WI", "🥝"], ["QUE-SO", "🧀"], ["YA-TE", "🛥️"], ["WA-FLE", "🧇"],
  ["HUE-SO", "🦴"]
];

/* ---------- Palabra "ancla" de cada letra (para "la A de abeja") ---------- */
const ANCLAS = { A: "ABEJA", E: "ELEFANTE", I: "ISLA", O: "OSO", U: "UVA", M: "MONO", P: "PATO", S: "SOL", L: "LUNA", T: "TOMATE", N: "NUBE", D: "DADO", C: "CASA", B: "BANANA", R: "RANA", F: "FLOR", G: "GATO", J: "JIRAFA", V: "VACA", Z: "ZAPATO", H: "HORMIGA", Y: "YATE", Ñ: "ÑOQUIS", K: "KOALA", Q: "QUESO", X: "TAXI", W: "WAFLE" };

/* ---------- Rimas: grupos de palabras que terminan igual (misma ortografía del final) ---------- */
const RIMAS = [
  ["GATO", "PATO", "PLATO", "ZAPATO"], ["BANANA", "MANZANA", "RANA", "CAMPANA"],
  ["RATÓN", "CAMIÓN", "AVIÓN", "LIMÓN", "DRAGÓN", "LEÓN", "JABÓN"], ["CARACOL", "GIRASOL", "SOL"],
  ["PELOTA", "BOTA", "GOTA", "NOTA"], ["MOTO", "FOTO"], ["REMERA", "TIJERA"], ["MARIPOSA", "ROSA"], ["FRUTILLA", "SILLA"],
  ["QUESO", "HUESO", "BESO"], ["LLAVE", "NAVE", "AVE"], ["ABEJA", "OVEJA", "OREJA"], ["CAMA", "RAMA", "LLAMA"], ["LORO", "TORO"], ["DADO", "HELADO"]
];

/* ---------- Frases cortas para leer: la frase y 3 dibujos (el primero es el correcto; se mezclan solos) ---------- */
const FRASES = [
  ["EL GATO COME PEZ", "🐱🐟", "🐶🐟", "🐱🥛"], ["EL PERRO TIENE UNA PELOTA", "🐶⚽", "🐱⚽", "🐶🦴"],
  ["MAMÁ TOMA LECHE", "👩🥛", "👩☕", "👦🥛"], ["LA NENA TIENE UN GLOBO", "👧🎈", "👦🎈", "👧⚽"],
  ["EL NENE COME UNA MANZANA", "👦🍎", "👧🍎", "👦🍌"], ["EL PATO NADA EN EL AGUA", "🦆🌊", "🐔🌊", "🦆🏠"],
  ["LA VACA TOMA AGUA", "🐄💧", "🐴💧", "🐄🥕"], ["PAPÁ MANEJA UN AUTO", "👨🚗", "👩🚗", "👨🚲"],
  ["EL BEBÉ DUERME", "👶💤", "👶🍼", "🧒💤"], ["LA ABEJA ESTÁ EN LA FLOR", "🐝🌸", "🦋🌸", "🐝🌳"],
  ["EL MONO COME BANANA", "🐒🍌", "🐘🍌", "🐒🍎"], ["EL NENE TIENE UN PERRO", "👦🐶", "👦🐱", "👧🐶"],
  ["EL CABALLO COME PASTO", "🐴🌿", "🐄🌿", "🐴🥕"], ["LA NENA USA UN SOMBRERO", "👧👒", "👦👒", "👧🧣"],
  ["EL SOL BRILLA EN EL CIELO", "☀️🌤️", "🌙🌤️", "☀️🌧️"], ["LA RANA ESTÁ EN LA HOJA", "🐸🍃", "🐢🍃", "🐸🌸"]
];

/* ---------- Comprensión: texto, pregunta, opciones (la primera es la correcta) ---------- */
const COMP = {
  comp1: [
    ["Ana tiene un perro.", "¿Qué tiene Ana?", "🐶", "🐱", "🐟"], ["Tomás come una banana.", "¿Qué come Tomás?", "🍌", "🍎", "🍞"],
    ["El gato duerme en la cama.", "¿Dónde duerme el gato?", "🛏️", "🚗", "🌳"], ["Hoy llueve. Mateo lleva un paraguas.", "¿Cómo está el día?", "🌧️", "☀️", "❄️"],
    ["El pez vive en el agua.", "¿Dónde vive el pez?", "💧", "🌳", "🏠"], ["Juan tiene dos globos.", "¿Cuántos globos tiene Juan?", "2", "3", "1"],
    ["La abeja hace miel.", "¿Qué hace la abeja?", "🍯", "🥛", "🍞"], ["Sofi toma leche con galletitas.", "¿Qué toma Sofi?", "🥛", "🧃", "☕"],
    ["Lola tiene una pelota roja.", "¿De qué color es la pelota?", "🔴", "🔵", "🟢"], ["Papá lleva a Lucas a la escuela en bicicleta.", "¿En qué lleva papá a Lucas?", "🚲", "🚌", "🚗"]
  ],
  comp2: [
    ["Vale tiene un gatito. El gatito es negro y juega con una pelota.", "¿De qué color es el gatito?", "negro", "blanco", "gris"],
    ["Es sábado. Papá hace un asado y toda la familia come en el patio.", "¿Qué hace papá?", "un asado", "una torta", "una sopa"],
    ["Lola va a la plaza en bicicleta. Se sube al tobogán y juega con sus amigos.", "¿Cómo va Lola a la plaza?", "en bicicleta", "en colectivo", "caminando"],
    ["El domingo llovió todo el día. Tomás se quedó en casa y armó un rompecabezas.", "¿Por qué se quedó Tomás en casa?", "porque llovía", "porque hacía calor", "porque estaba cansado"],
    ["Mi abuela hace tortas fritas cuando llueve. Las comemos con mate cocido.", "¿Cuándo hace tortas fritas la abuela?", "cuando llueve", "cuando hace calor", "de noche"],
    ["En la escuela, la seño nos leyó un cuento de un dragón. El dragón era amigo de un nene.", "¿Qué leyó la seño?", "un cuento", "una carta", "un mapa"],
    ["El zorro es rápido y astuto. Vive en el campo y duerme de día.", "¿Cuándo duerme el zorro?", "de día", "de noche", "nunca"],
    ["Julia guarda sus juguetes. Después se lava los dientes y se va a dormir.", "¿Qué hace Julia después de guardar los juguetes?", "se lava los dientes", "va a la pileta", "toma el colectivo"]
  ]
};

/* ---------- Oraciones para ordenar: la oración y un dibujo ---------- */
const ORACIONES = [
  ["EL GATO DUERME", "🐱💤"], ["LA NENA SALTA", "👧"], ["MAMÁ COCINA UNA SOPA", "👩🥣"], ["EL PERRO CORRE EN EL PARQUE", "🐶🏞️"],
  ["PAPÁ LEE UN LIBRO", "👨📖"], ["LA LUNA SALE DE NOCHE", "🌙"], ["EL NENE JUEGA CON LA PELOTA", "👦⚽"], ["LOS PÁJAROS CANTAN", "🐦🎶"],
  ["HOY VAMOS A LA PILETA", "🏊"], ["ME GUSTA EL HELADO DE FRUTILLA", "🍦🍓"], ["LA ABUELA TOMA MATE", "👵🧉"], ["EL SOL ES AMARILLO", "☀️"]
];

/* ---------- Letras que van juntas ----------
   dig: dígrafos y letras dobles.  tr: sílabas trabadas.  Cada ítem: [palabra con guiones, grupo que falta]. */
const GRUPOS = {
  dig: { opciones: ["LL", "RR", "CH", "QU", "GU"], items: [
    ["LLA-VE", "LL"], ["CA-BA-LLO", "LL"], ["GA-LLI-NA", "LL"], ["SI-LLA", "LL"], ["BA-LLE-NA", "LL"],
    ["PE-RRO", "RR"], ["GUI-TA-RRA", "RR"], ["TIE-RRA", "RR"], ["ZO-RRO", "RR"], ["TO-RRE", "RR"],
    ["LE-CHE", "CH"], ["MO-CHI-LA", "CH"], ["CHO-CLO", "CH"], ["CU-CHA-RA", "CH"],
    ["QUE-SO", "QU"], ["PA-QUE-TE", "QU"],
    ["GUI-TA-RRA", "GU"], ["GUI-SO", "GU"], ["GUAN-TE", "GU"]
  ] },
  tr: { opciones: ["BR", "BL", "CR", "DR", "FL", "FR", "GL", "GR", "PL", "PR", "TR"], items: [
    ["BRU-JA", "BR"], ["LI-BRO", "BR"], ["SO-BRE", "BR"], ["CE-BRA", "BR"], ["BLU-SA", "BL"], ["CRO-CO-DI-LO", "CR"],
    ["DRA-GÓN", "DR"], ["LA-DRI-LLO", "DR"], ["FLOR", "FL"], ["FLE-CHA", "FL"], ["FRU-TI-LLA", "FR"], ["GLO-BO", "GL"],
    ["TI-GRE", "GR"], ["GRI-LLO", "GR"], ["PLA-TO", "PL"], ["PLA-NE-TA", "PL"], ["PRIN-CE-SA", "PR"], ["TREN", "TR"], ["TRI-GO", "TR"], ["ES-TRE-LLA", "TR"]
  ] }
};

/* ---------- Ortografía y puntuación: "¿cuál está bien escrita?" ----------
   [dibujo o "", correcta, equivocadas…, regla]. La regla se dice al mostrar la respuesta. */
const ORTO = [
  ["🏞️", "CAMPO", "CANPO", "Antes de P y de B se escribe M."], ["💡", "LÁMPARA", "LÁNPARA", "Antes de P y de B se escribe M."],
  ["🎺", "TROMPETA", "TRONPETA", "Antes de P y de B se escribe M."], ["🥁", "TAMBOR", "TANBOR", "Antes de P y de B se escribe M."],
  ["🔔", "CAMPANA", "CANPANA", "Antes de P y de B se escribe M."], ["🚒", "BOMBERO", "BONBERO", "Antes de P y de B se escribe M."],
  ["🐶", "PERRO", "PERO", "Entre vocales, la erre fuerte se escribe con rr."], ["🗼", "TORRE", "TORE", "Entre vocales, la erre fuerte se escribe con rr."],
  ["🎸", "GUITARRA", "GUITARA", "Entre vocales, la erre fuerte se escribe con rr."], ["🌎", "TIERRA", "TIERA", "Entre vocales, la erre fuerte se escribe con rr."],
  ["🦊", "ZORRO", "ZORO", "Entre vocales, la erre fuerte se escribe con rr."],
  ["🦒", "JIRAFA", "GIRAFA", "Jirafa se escribe con J."], ["🌻", "GIRASOL", "JIRASOL", "Girasol se escribe con G."],
  ["🥚", "HUEVO", "UEVO", "Huevo empieza con H, aunque la H no suena."], ["🍦", "HELADO", "ELADO", "Helado empieza con H, aunque la H no suena."],
  ["🐜", "HORMIGA", "ORMIGA", "Hormiga empieza con H, aunque la H no suena."], ["🍃", "HOJA", "OJA", "Hoja empieza con H, aunque la H no suena."],
  ["🧀", "QUESO", "KESO", "Que y qui se escriben con QU."], ["📦", "PAQUETE", "PAKETE", "Que y qui se escriben con QU."],
  ["🍲", "GUISO", "GISO", "Para que suene /gui/ se escribe GU."], ["🔑", "LLAVE", "YAVE", "Llave se escribe con LL."],
  ["🐔", "GALLINA", "GAYINA", "Gallina se escribe con LL."], ["🐴", "CABALLO", "CABAYO", "Caballo se escribe con LL."],
  ["🐋", "BALLENA", "BAYENA", "Ballena se escribe con LL."], ["🐄", "VACA", "BACA", "Vaca se escribe con V."], ["⛵", "BARCO", "VARCO", "Barco se escribe con B."]
];
const MAYUS = [
  ["Ana", "ana", "Los nombres de personas empiezan con mayúscula."], ["Lucas", "lucas", "Los nombres de personas empiezan con mayúscula."],
  ["Sofía", "sofía", "Los nombres de personas empiezan con mayúscula."], ["Tomás", "tomás", "Los nombres de personas empiezan con mayúscula."],
  ["Buenos Aires", "buenos aires", "Los nombres de lugares empiezan con mayúscula."], ["Rosario", "rosario", "Los nombres de lugares empiezan con mayúscula."],
  ["Mendoza", "mendoza", "Los nombres de lugares empiezan con mayúscula."], ["Argentina", "argentina", "Los nombres de lugares empiezan con mayúscula."],
  ["Mi perro se llama Lola.", "mi perro se llama Lola.", "Las oraciones empiezan con mayúscula."],
  ["Hoy es sábado.", "hoy es sábado.", "Las oraciones empiezan con mayúscula."],
  ["El gato duerme.", "El gato duerme", "Las oraciones terminan con punto."], ["Mamá hace una torta.", "Mamá hace una torta", "Las oraciones terminan con punto."],
  ["¿Cómo te llamás?", "Cómo te llamás?", "Las preguntas llevan signos de pregunta al principio y al final: ¿ ?"],
  ["¿Dónde está mi pelota?", "¿Dónde está mi pelota", "Las preguntas llevan signos de pregunta al principio y al final: ¿ ?"],
  ["¡Qué lindo día!", "Qué lindo día!", "Cuando algo se dice con emoción, va entre signos de exclamación: ¡ !"],
  ["¡Feliz cumpleaños!", "¡Feliz cumpleaños", "Cuando algo se dice con emoción, va entre signos de exclamación: ¡ !"]
];

/* ---------- Pares para "mayúsculas y minúsculas": letras que se confunden por la forma no van juntas ---------- */
const FORMAS_PARECIDAS = ["bdpq", "nu", "mw", "il", "ceo"];

/* ---------- Letras que se confunden de oído en el habla rioplatense: nunca juntas como opción de un ejercicio de sonido ---------- */
const CONFUNDEN = { B: "V", V: "B", C: "KQSZ", K: "CQ", Q: "CK", S: "CZ", Z: "CS", G: "J", J: "G", H: "AEIOU", A: "H", E: "H", I: "H", O: "H", U: "H" };

Gioval.datos.letras = { TEXTOS, ANCLAS, HABILIDADES, INICIO, PALABRAS, RIMAS, FRASES, COMP, ORACIONES, GRUPOS, ORTO, MAYUS, FORMAS_PARECIDAS, CONFUNDEN };
