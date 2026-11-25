"use strict";
/* ============ DATOS DE LA ISLA RITMO ============
   Todo el contenido (textos, habilidades, patrones, canciones, parámetros de tolerancia) vive acá; el código de la isla
   (js/islas/ritmo.js) y el de entrada de golpes (js/core/entrada/golpes.js) no llevan texto ni contenido pedagógico.
   TEXTOS está al tope para facilitar la traducción: los valores con {algo} se completan con datos; los arreglos son
   variantes (se elige una al azar). Tono: español rioplatense ("vos"), elogio al ESFUERZO y al proceso, nunca a "ser bueno".
   Vocabulario de ritmo (método Kodály, de dominio público): "ta" = negra, "ti-ti" = dos corcheas, "ta-a" = blanca, "shh" = silencio de negra. */
(function () {
const TEXTOS = {
  isla: { nombre: "Isla Ritmo", sub: "¡A marcar el ritmo!", emoji: "🥁" },
  /* nombres de las habilidades (aparecen en Mis logros, en el informe y en "Mañana seguimos con…") */
  hab: {
    pulso: "Sentir el pulso", eco2: "Eco de 2 golpes", tempo: "Lento, medio y rápido", base: "Pulso con la base",
    eco3: "Eco de 3 golpes", eco4: "Eco de 4 golpes", silencio: "Golpe y silencio", solo: "Pulso solito",
    lee1: "Leer: ta y shh", lee2: "Leer: ti-ti", llamada: "Llamada y respuesta", cancion: "Ritmos de canciones",
    leemix: "Leer ritmos largos", compone: "Mi propio ritmo",
  },
  /* sílabas y dibujos de las tarjetas de ritmo */
  tarjeta: { T: "ta", TT: "ti-ti", H: "ta-a", S: "shh", mudoAyuda: "Escuchá y mirá", oculta: "¡Escuchá con atención!" },
  /* lo que se dice en voz alta */
  voz: {
    escucha: ["Escuchá…", "Escuchá bien…", "Atención, escuchá…"],
    turno: ["¡Ahora vos!", "¡Te toca a vos!", "¡Ahora te toca!"],
    cuenta: ["Contamos hasta cuatro y empezás.", "Preparate: cuento cuatro y arrancás.", "Yo cuento cuatro y entrás."],
    tiempoLento: "Ahora va lento, como una tortuga.",
    tiempoMedio: "Ahora va a paso normal, como un conejo.",
    tiempoRapido: "Ahora va rápido, como un guepardo.",
    intro: {
      eco: "Escuchá el ritmo y repetilo igualito. Podés tocar el tambor de la pantalla o tu instrumento.",
      pulso: "Un pulso es como el latido del corazón: siempre parejito. Escuchá y repetí los golpes parejos.",
      tempo: "Mirá qué rápido o qué lento va el ritmo, y copialo a la misma velocidad.",
      base: "Voy a tocar una base. Escuchala y golpeá con cada clic, siempre parejito.",
      solo: "Primero te ayudo con la base. Después sigo en silencio y vos mantenés el pulso solito.",
      silencio: "Atención: a veces hay un silencio. Ahí no se golpea: ¡shh! Seguí el pulso y esperá.",
      lectura: "Leé las tarjetas de izquierda a derecha. Ta es un golpe, shh es un silencio. Contamos y empezás.",
      lecturaTT: "Ahora hay tarjetas ti-ti: son dos golpes rápidos en un solo pulso. Contamos y empezás.",
      cancion: "Este es el ritmo de una canción que conocés. Cantala en tu cabeza y tocá su ritmo.",
      llamada: "Yo toco un ritmo y vos me contestás con el tuyo, siguiendo el pulso. ¡Inventá lo que quieras!",
      compone: "Armá tu propio ritmo de cuatro pulsos eligiendo tarjetas. Después lo tocamos juntos.",
    },
    ok: ["¡Lo hiciste parejito!", "¡Escuchaste con atención y salió!", "¡Seguiste el pulso muy bien!", "¡Cuidaste el ritmo y salió!"],
    okTrasError: ["¡Lo lograste! Seguiste intentando.", "¡Eso! Escuchaste mejor la segunda vez.", "¡Insistir funciona!"],
    casi: ["¡Casi! Probemos otra vez.", "¡Ya casi! Escuchemos de nuevo.", "¡Buen intento! Vamos otra vez."],
    faltan: "Faltó algún golpe. Escuchemos de nuevo.",
    sobra: "Hubo un golpe de más. ¡Escuchemos otra vez!",
    sobraSilencio: "Ahí había un silencio. ¡Shh! Probemos otra vez.",
    adelantado: "Fuiste un poquito rápido en el {ord} golpe. Esperá un poquito más.",
    atrasado: "El {ord} golpe llegó un poquito tarde. ¡Ya casi!",
    sinGolpes: "No te escuché. Probá de nuevo; también podés tocar el tambor de la pantalla.",
    pregunta: "¿Seguimos con el próximo?",
    ayuda1: "Mirá las tarjetas mientras escuchás.",
    ayuda2: "Vamos más despacito.",
    revela: "¡Esta era difícil! Mirá y escuchá cómo va. La repasamos en un ratito.",
    libreOk: "¡Contestaste siguiendo el pulso! ¡Qué buen ritmo inventaste!",
    libreMuyPoco: "Probá con más golpes: dos o más, siguiendo el pulso.",
    libreMuchos: "Fueron muchos golpes. Probá con menos y bien parejitos.",
    libreDesparejo: "Tus golpes se corrieron un poco del pulso. ¡Probemos otra vez!",
    componeElegi: "Elegí una tarjeta para cada pulso.",
    componeEscucha: "Escuchá cómo suena tu ritmo.",
    componeAlMenos: "Poné al menos un golpe, ¡no todo silencio!",
    modoPantalla: "Ahora tocamos con el tambor de la pantalla.",
    micPedir: "Voy a escuchar el ruido de la sala. Quedate en silencio unos segundos.",
    micListo: "¡Listo! Hacé un golpe para probar.",
    micOyo: "¡Te escuché! Ya podemos jugar.",
    micMucho: "Hay bastante ruido en la sala. Probá en un lugar más tranquilo, o usá el tambor de la pantalla.",
    micError: "No pude usar el micrófono. Usamos el tambor de la pantalla.",
  },
  /* globitos que el motor muestra tras cada ítem */
  okMsgs: ["¡Escuchaste y seguiste el pulso!", "¡Prestaste atención al ritmo!", "¡Cuidaste el pulso, muy bien!"],
  /* pantalla de juego */
  ui: {
    titulo: "Sesión de hoy", volver: " Volver", escuchar: " Escuchar", seguir: "Seguir ➜",
    pad: "Tocá acá", padAlt: "Tambor",
    micEscucho: "Te escucho", micPantalla: "🥁 Usar la pantalla", micTitulo: "Escuchar mi instrumento",
    tarjetaMicOn: { t: "Usar la pantalla", s: "Ahora te escucho: tocá tu instrumento" },
    tarjetaMicOff: { t: "Tocar con mi instrumento", s: "Tambor, cajón, palmas… ¡te escucho!" },
    calibrando: "Shhh… estoy escuchando el ruido de la sala", calibrandoSub: "Quedate en silencio {s} segundos",
    calibrado: "¡Listo! Hacé un golpe para probar", oi: "¡Te escuché!", cerrar: "Listo", usarPantalla: "Usar la pantalla",
    ruido: { bajo: "Sala tranquila", medio: "Algo de ruido", alto: "Mucho ruido" },
    componer: { T: "ta", TT: "ti-ti", S: "shh", borrar: "↺ Borrar", listo: "¡Listo!" },
    ordinales: ["primer", "segundo", "tercer", "cuarto", "quinto", "sexto", "séptimo", "octavo", "noveno", "décimo", "11.º", "12.º", "13.º", "14.º", "15.º", "16.º"],
    golpe: "golpe", cuenta: "1 · 2 · 3 · 4",
  },
  /* para papá (panel de adultos) */
  panel: {
    texto: " — Isla Ritmo: el 🎤 se enciende desde la isla (“Tocar con mi instrumento”).",
    sens: "Sensibilidad de golpes", nivel: "Volumen", recalibrar: "Recalibrar ruido", estado: "Micrófono de golpes:",
    estadoApagado: "apagado (se usa la pantalla)", estadoOk: "escuchando · ruido de fondo {piso} · umbral {umbral}",
    pie: "Ritmo: la app mide CUÁNDO suena cada golpe y qué tan parejo es; no juzga cómo suena el instrumento ni la técnica. Probá primero con 10 golpes parejos.",
  },
  /* informe para adultos */
  informe: {
    titulo: "REGULARIDAD DEL RITMO (Isla Ritmo)",
    como: "   Desvío medio = cuántos milisegundos se aparta cada golpe del momento esperado (menos es más parejo). Se mide solo en el PRIMER intento de cada ejercicio.",
    sinDatos: "   (todavía no hay ejercicios medidos)",
    general: "   Desvío medio general: {d} ms (n={n} ejercicios) · {mic} con instrumento, {tq} en pantalla",
    mejora: "   Evolución: primeros {k} ejercicios {a} ms → últimos {k} {b} ms ({delta})",
    mejoraMenos: "mejora de {x} ms", mejoraMas: "{x} ms más desparejo", mejoraIgual: "sin cambios claros",
    pocos: "   Evolución: se muestra cuando haya al menos {n} ejercicios medidos.",
    porDia: "   Por día practicado: {lista}",
    sesgo: "   Tendencia: suele golpear {dir} (unos {x} ms; incluye la demora propia de la pantalla o del micrófono).",
    sesgoAdelante: "un poco antes del pulso", sesgoAtras: "un poco después del pulso", sesgoNada: "justo sobre el pulso",
    porHab: "   Por habilidad (desvío medio): {lista}",
    aclaracion: "   Importante: la app solo mide cuándo suenan los golpes y qué tan parejos son. No juzga la técnica, el sonido, la afinación ni si el instrumento está bien tocado; eso lo ve un adulto o un profe.",
  },
};

/* ---- parámetros ajustables (docs/RITMO.md) ---- */
const AJUSTES = {
  ventana: { frac: [0.32, 0.24, 0.18], minMs: 90, maxMs: 210 }, // tolerancia = fracción del pulso, según el nivel (0 = más ayuda … 2 = sin ayuda)
  aciertoMin: 0.75,        // en ejercicios largos (6 o más golpes esperados) alcanza con acertar esta proporción
  pulsosCuenta: 4,         // clics de cuenta antes de empezar
  esperaPrimerGolpeMs: 10000,
  graciaMs: 350,           // espera tras el último golpe esperado para detectar golpes de más
  intentosMax: 3,
  minEvaluaciones: 8,      // para mostrar "evolución" en el informe
  bajaTempoAyuda: 0.85,    // el 2.º intento fallado baja el tempo a este factor
  volumen: { modelo: 0.5, base: 0.22, pad: 0.45 },
};

/* ---- patrones: T = ta (negra), TT = ti-ti (dos corcheas), H = ta-a (blanca, 2 pulsos), S = shh (silencio de negra) ---- */
const HABILIDADES = [
  { id: "rit_pulso", icon: "💓", type: "eco", req: [], pats: ["T T T T"], bpms: [66, 76], intro: "pulso" },
  { id: "rit_eco2", icon: "✌️", type: "eco", req: ["rit_pulso"], pats: ["T T", "H T", "TT"], bpms: [70, 80, 90] },
  { id: "rit_tempo", icon: "🐢", type: "tempo", req: ["rit_pulso"], pats: ["T T T T", "T T T T T T"],
    tempos: [{ n: "lento", bpm: 54, e: "🐢", voz: "tiempoLento" }, { n: "medio", bpm: 84, e: "🐇", voz: "tiempoMedio" }, { n: "rapido", bpm: 124, e: "🐆", voz: "tiempoRapido" }] },
  { id: "rit_base", icon: "🥁", type: "base", req: ["rit_pulso"], pulsos: 8, bpms: [70, 80, 90] },
  { id: "rit_eco3", icon: "3️⃣", type: "eco", req: ["rit_eco2"], pats: ["T T H", "H T T", "T H T", "T TT", "TT T", "T T T"], bpms: [76, 88] },
  { id: "rit_eco4", icon: "4️⃣", type: "eco", req: ["rit_eco3"], pats: ["T T TT", "TT TT", "T TT T", "TT T T", "T T T H", "T H T T"], bpms: [76, 88] },
  { id: "rit_silencio", icon: "🤫", type: "silencio", req: ["rit_eco3", "rit_base"], pats: ["T T S T", "T S T T", "T T T S", "T S T S", "S T T T"], bpms: [70, 80] },
  { id: "rit_solo", icon: "🧘", type: "solo", req: ["rit_base", "rit_tempo"], pulsos: 12, apoyo: [6, 4, 2], bpms: [70, 80] },
  { id: "rit_lee1", icon: "🔵", type: "lectura", req: ["rit_silencio"], gen: { tt: false, s: true, compases: 1 }, bpms: [70, 80], intro: "lectura" },
  { id: "rit_lee2", icon: "🟠", type: "lectura", req: ["rit_lee1"], gen: { tt: true, s: true, compases: 1 }, bpms: [70, 80], intro: "lecturaTT" },
  { id: "rit_llamada", icon: "📣", type: "llamada", req: ["rit_eco4", "rit_base"], pats: ["T T T T", "T TT T T", "T T TT T", "TT T T T", "T T H"], bpms: [76, 86] },
  { id: "rit_cancion", icon: "🎵", type: "cancion", req: ["rit_lee2"], bpms: [76, 86] },
  { id: "rit_leemix", icon: "📖", type: "lectura", req: ["rit_lee2", "rit_solo"], gen: { tt: true, s: true, compases: 2 }, bpms: [70, 80], intro: "lecturaTT" },
  { id: "rit_compone", icon: "🎨", type: "compone", req: ["rit_lee2", "rit_llamada"], bpms: [72, 80] },
];

/* ---- ritmos de canciones tradicionales de dominio público. SOLO el patrón rítmico de una frase (sin letra), simplificado. ---- */
const CANCIONES = [
  { id: "estrellita", nombre: "Estrellita", emoji: "⭐", pat: "T T T T T T H" },
  { id: "martinillo", nombre: "Martinillo (Fray Santiago)", emoji: "🔔", pat: "T T T T T T T T" },
  { id: "martinillo2", nombre: "Martinillo, segunda parte", emoji: "🔔", pat: "T T H T T H" },
  { id: "martinillo3", nombre: "Martinillo, la campana", emoji: "🔔", pat: "TT TT T T" },
  { id: "panCaliente", nombre: "Hot cross buns", emoji: "🥐", pat: "T T H T T H" },
  { id: "corderito", nombre: "Mary tenía un corderito", emoji: "🐑", pat: "T T T T T T H" },
];

/* ---- paletas de la composición ---- */
const COMPONER = { pulsos: 4, fichas: ["T", "TT", "S"] };

Gioval.datos.ritmo = { TEXTOS, AJUSTES, HABILIDADES, CANCIONES, COMPONER };
})();
