"use strict";
/* ============ DATOS DE LA ISLA RITMO ============
   Contenido de la isla: habilidades, patrones, canciones, parámetros de tolerancia y textos por idioma (es-AR base + en, con
   Gioval.i18n.agregar). El código de la isla (js/islas/ritmo.js) y el de entrada de golpes (js/core/entrada/golpes.js) no llevan texto
   ni contenido pedagógico. Tono: voseo rioplatense, elogio al ESFUERZO y al proceso, nunca a "ser bueno".
   Vocabulario de ritmo (método Kodály, de dominio público): "ta" = negra, "ti-ti" = dos corcheas, "ta-a" = blanca, "shh" = silencio de negra. */
(function () {
/* ---- textos por idioma (Gioval.i18n). es-AR es el idioma base; "en" es obligatorio (la prueba de completitud pide las mismas claves).
   Las frases son COMPLETAS con huecos con nombre ({ord}, {x}…); las listas son variantes (se elige una al azar).
   Tono: voseo rioplatense, elogio al ESFUERZO y al proceso, nunca a "ser bueno". Sílabas de ritmo (método Kodály, de dominio público):
   "ta" = negra, "ti-ti" = dos corcheas, "ta-a" = blanca, "shh" = silencio de negra. ---- */
Gioval.i18n.agregar("es-AR", {
  "ritmo.nombre": "Isla Ritmo", "ritmo.sub": "¡A marcar el ritmo!",
  "ritmo.outro": "Ahora, ¡a tocar un tambor, una caja o las palmas de verdad!",
  "ritmo.cola_tope": "Ahora, a hacer ritmo con tus palmas o tu tambor. ¡Mañana seguimos!",
  "ritmo.nota_informe": "En Ritmo la app mide cuándo suenan los golpes y qué tan parejos son; la técnica y el sonido los ve un adulto.",
  /* nombres de las habilidades (Mis logros, informe, "Mañana seguimos con…") */
  "ritmo.hab.rit_pulso": "Sentir el pulso", "ritmo.hab.rit_eco2": "Eco de 2 golpes", "ritmo.hab.rit_tempo": "Lento, medio y rápido",
  "ritmo.hab.rit_base": "Pulso con la base", "ritmo.hab.rit_eco3": "Eco de 3 golpes", "ritmo.hab.rit_eco4": "Eco de 4 golpes",
  "ritmo.hab.rit_silencio": "Golpe y silencio", "ritmo.hab.rit_solo": "Pulso solito", "ritmo.hab.rit_lee1": "Leer: ta y shh",
  "ritmo.hab.rit_lee2": "Leer: ti-ti", "ritmo.hab.rit_llamada": "Llamada y respuesta", "ritmo.hab.rit_cancion": "Ritmos de canciones",
  "ritmo.hab.rit_leemix": "Leer ritmos largos", "ritmo.hab.rit_compone": "Mi propio ritmo",
  /* canciones tradicionales (solo se dice el nombre; el patrón es del dominio público) */
  "ritmo.cancion.estrellita": "Estrellita", "ritmo.cancion.martinillo": "Martinillo (Fray Santiago)", "ritmo.cancion.martinillo2": "Martinillo, segunda parte",
  "ritmo.cancion.martinillo3": "Martinillo, la campana", "ritmo.cancion.panCaliente": "Hot cross buns", "ritmo.cancion.corderito": "Mary tenía un corderito",
  /* sílabas de las tarjetas */
  "ritmo.tarjeta.ta": "ta", "ritmo.tarjeta.ti_ti": "ti-ti", "ritmo.tarjeta.ta_a": "ta-a", "ritmo.tarjeta.shh": "shh",
  "ritmo.tarjeta.mudo_ayuda": "Escuchá y mirá",
  /* lo que se dice en voz alta */
  "ritmo.voz.escucha": ["Escuchá…", "Escuchá bien…", "Atención, escuchá…"],
  "ritmo.voz.turno": ["¡Ahora vos!", "¡Te toca a vos!", "¡Ahora te toca!"],
  "ritmo.voz.cuenta": ["Contamos hasta cuatro y empezás.", "Preparate: cuento cuatro y arrancás.", "Yo cuento cuatro y entrás."],
  "ritmo.voz.tiempo_lento": "Ahora va lento, como una tortuga.",
  "ritmo.voz.tiempo_medio": "Ahora va a paso normal, como un conejo.",
  "ritmo.voz.tiempo_rapido": "Ahora va rápido, como un guepardo.",
  "ritmo.voz.intro.eco": "Escuchá el ritmo y repetilo igualito. Podés tocar el tambor de la pantalla o tu instrumento.",
  "ritmo.voz.intro.pulso": "Un pulso es como el latido del corazón: siempre parejito. Escuchá y repetí los golpes parejos.",
  "ritmo.voz.intro.tempo": "Mirá qué rápido o qué lento va el ritmo, y copialo a la misma velocidad.",
  "ritmo.voz.intro.base": "Voy a tocar una base. Escuchala y golpeá con cada clic, siempre parejito.",
  "ritmo.voz.intro.solo": "Primero te ayudo con la base. Después sigo en silencio y vos mantenés el pulso solito.",
  "ritmo.voz.intro.silencio": "Atención: a veces hay un silencio. Ahí no se golpea: ¡shh! Seguí el pulso y esperá.",
  "ritmo.voz.intro.lectura": "Leé las tarjetas de izquierda a derecha. Ta es un golpe, shh es un silencio. Contamos y empezás.",
  "ritmo.voz.intro.lectura_ti_ti": "Ahora hay tarjetas ti-ti: son dos golpes rápidos en un solo pulso. Contamos y empezás.",
  "ritmo.voz.intro.cancion": "Este es el ritmo de una canción que conocés. Cantala en tu cabeza y tocá su ritmo.",
  "ritmo.voz.intro.llamada": "Yo toco un ritmo y vos me contestás con el tuyo, siguiendo el pulso. ¡Inventá lo que quieras!",
  "ritmo.voz.intro.compone": "Armá tu propio ritmo de cuatro pulsos eligiendo tarjetas. Después lo tocamos juntos.",
  "ritmo.voz.casi": ["¡Casi! Probemos otra vez.", "¡Ya casi! Escuchemos de nuevo.", "¡Buen intento! Vamos otra vez."],
  "ritmo.voz.faltan": "Faltó algún golpe. Escuchemos de nuevo.",
  "ritmo.voz.sobra": "Hubo un golpe de más. ¡Escuchemos otra vez!",
  "ritmo.voz.sobra_silencio": "Ahí había un silencio. ¡Shh! Probemos otra vez.",
  "ritmo.voz.adelantado": "Fuiste un poquito rápido en el {ord} golpe. Esperá un poquito más.",
  "ritmo.voz.atrasado": "El {ord} golpe llegó un poquito tarde. ¡Ya casi!",
  "ritmo.voz.sin_golpes": "No te escuché. Probá de nuevo; también podés tocar el tambor de la pantalla.",
  "ritmo.voz.pregunta": "¿Seguimos con el próximo?",
  "ritmo.voz.revela": "¡Esta era difícil! Mirá y escuchá cómo va. La repasamos en un ratito.",
  "ritmo.voz.libre_ok": "¡Contestaste siguiendo el pulso! ¡Qué buen ritmo inventaste!",
  "ritmo.voz.libre_muy_poco": "Probá con más golpes: dos o más, siguiendo el pulso.",
  "ritmo.voz.libre_muchos": "Fueron muchos golpes. Probá con menos y bien parejitos.",
  "ritmo.voz.libre_desparejo": "Tus golpes se corrieron un poco del pulso. ¡Probemos otra vez!",
  "ritmo.voz.compone_escucha": "Escuchá cómo suena tu ritmo.",
  "ritmo.voz.compone_al_menos": "Poné al menos un golpe, ¡no todo silencio!",
  "ritmo.voz.modo_pantalla": "Ahora tocamos con el tambor de la pantalla.",
  "ritmo.voz.mic_pedir": "Voy a escuchar el ruido de la sala. Quedate en silencio unos segundos.",
  "ritmo.voz.mic_listo": "¡Listo! Hacé un golpe para probar.",
  "ritmo.voz.mic_oyo": "¡Te escuché! Ya podemos jugar.",
  "ritmo.voz.mic_mucho": "Hay bastante ruido en la sala. Probá en un lugar más tranquilo, o usá el tambor de la pantalla.",
  "ritmo.voz.mic_error": "No pude usar el micrófono. Usamos el tambor de la pantalla.",
  /* globitos que el motor muestra tras cada ítem */
  "ritmo.ok_msgs": ["¡Escuchaste y seguiste el pulso!", "¡Prestaste atención al ritmo!", "¡Cuidaste el pulso, muy bien!"],
  /* pantalla de juego */
  "ritmo.ui.volver": " Volver", "ritmo.ui.escuchar": " Escuchar", "ritmo.ui.seguir": "Seguir ➜",
  "ritmo.ui.pad": "Tocá acá", "ritmo.ui.pad_alt": "Tambor",
  "ritmo.ui.mic_escucho": "Te escucho", "ritmo.ui.mic_pantalla": "🥁 Usar la pantalla",
  "ritmo.ui.tarjeta_mic_on_t": "Usar la pantalla", "ritmo.ui.tarjeta_mic_on_s": "Ahora te escucho: tocá tu instrumento",
  "ritmo.ui.tarjeta_mic_off_t": "Tocar con mi instrumento", "ritmo.ui.tarjeta_mic_off_s": "Tambor, cajón, palmas… ¡te escucho!",
  "ritmo.ui.calibrando": "Shhh… estoy escuchando el ruido de la sala", "ritmo.ui.calibrando_sub": "Quedate en silencio {s} segundos",
  "ritmo.ui.calibrado": "¡Listo! Hacé un golpe para probar", "ritmo.ui.oi": "¡Te escuché!", "ritmo.ui.cerrar": "Listo", "ritmo.ui.usar_pantalla": "Usar la pantalla",
  "ritmo.ui.ruido_bajo": "Sala tranquila", "ritmo.ui.ruido_medio": "Algo de ruido", "ritmo.ui.ruido_alto": "Mucho ruido",
  "ritmo.ui.componer_ta": "ta", "ritmo.ui.componer_ti_ti": "ti-ti", "ritmo.ui.componer_shh": "shh", "ritmo.ui.componer_borrar": "Borrar",
  "ritmo.ui.ordinales": ["primer", "segundo", "tercer", "cuarto", "quinto", "sexto", "séptimo", "octavo", "noveno", "décimo", "11.º", "12.º", "13.º", "14.º", "15.º", "16.º"],
  "ritmo.ui.cuenta": "1 · 2 · 3 · 4",
  /* para papá (panel de adultos) */
  "ritmo.panel.texto": " — Isla Ritmo: el 🎤 se enciende desde la isla (“Tocar con mi instrumento”).",
  "ritmo.panel.sens": "Sensibilidad de golpes", "ritmo.panel.nivel": "Volumen", "ritmo.panel.recalibrar": "Recalibrar ruido", "ritmo.panel.estado": "Micrófono de golpes:",
  "ritmo.panel.estado_apagado": "apagado (se usa la pantalla)", "ritmo.panel.estado_ok": "escuchando · ruido de fondo {piso} · umbral {umbral}",
  "ritmo.panel.pie": "Ritmo: la app mide CUÁNDO suena cada golpe y qué tan parejo es; no juzga cómo suena el instrumento ni la técnica. Probá primero con 10 golpes parejos.",
  /* informe para adultos */
  "ritmo.informe.titulo": "REGULARIDAD DEL RITMO (Isla Ritmo)",
  "ritmo.informe.como": "   Desvío medio = cuántos milisegundos se aparta cada golpe del momento esperado (menos es más parejo). Se mide solo en el PRIMER intento de cada ejercicio.",
  "ritmo.informe.general": "   Desvío medio general: {d} ms (n={n} ejercicios) · {mic} con instrumento, {tq} en pantalla",
  "ritmo.informe.mejora": "   Evolución: primeros {k} ejercicios {a} ms → últimos {k} {b} ms ({delta})",
  "ritmo.informe.mejora_menos": "mejora de {x} ms", "ritmo.informe.mejora_mas": "{x} ms más desparejo", "ritmo.informe.mejora_igual": "sin cambios claros",
  "ritmo.informe.pocos": "   Evolución: se muestra cuando haya al menos {n} ejercicios medidos.",
  "ritmo.informe.por_dia": "   Por día practicado: {lista}",
  "ritmo.informe.sesgo": "   Tendencia: suele golpear {dir} (unos {x} ms; incluye la demora propia de la pantalla o del micrófono).",
  "ritmo.informe.sesgo_adelante": "un poco antes del pulso", "ritmo.informe.sesgo_atras": "un poco después del pulso", "ritmo.informe.sesgo_nada": "justo sobre el pulso",
  "ritmo.informe.por_hab": "   Por habilidad (desvío medio): {lista}",
  "ritmo.informe.aclaracion": "   Importante: la app solo mide cuándo suenan los golpes y qué tan parejos son. No juzga la técnica, el sonido, la afinación ni si el instrumento está bien tocado; eso lo ve un adulto o un profe.",
});
Gioval.i18n.agregar("en", {
  "ritmo.nombre": "Rhythm Island", "ritmo.sub": "Let's keep the beat!",
  "ritmo.outro": "Now go play a real drum, a box or just clap your hands!",
  "ritmo.cola_tope": "Now go make rhythm with your hands or your drum. See you tomorrow!",
  "ritmo.nota_informe": "In Rhythm the app measures when the hits sound and how even they are; technique and sound quality are for an adult to judge.",
  "ritmo.hab.rit_pulso": "Feel the beat", "ritmo.hab.rit_eco2": "Echo of 2 hits", "ritmo.hab.rit_tempo": "Slow, medium and fast",
  "ritmo.hab.rit_base": "Beat with the backing", "ritmo.hab.rit_eco3": "Echo of 3 hits", "ritmo.hab.rit_eco4": "Echo of 4 hits",
  "ritmo.hab.rit_silencio": "Hits and rests", "ritmo.hab.rit_solo": "Keeping the beat alone", "ritmo.hab.rit_lee1": "Read: ta and shh",
  "ritmo.hab.rit_lee2": "Read: ti-ti", "ritmo.hab.rit_llamada": "Call and response", "ritmo.hab.rit_cancion": "Song rhythms",
  "ritmo.hab.rit_leemix": "Read longer rhythms", "ritmo.hab.rit_compone": "My own rhythm",
  "ritmo.cancion.estrellita": "Twinkle, Twinkle, Little Star", "ritmo.cancion.martinillo": "Martinillo (Brother John)", "ritmo.cancion.martinillo2": "Martinillo, second part",
  "ritmo.cancion.martinillo3": "Martinillo, the bell", "ritmo.cancion.panCaliente": "Hot cross buns", "ritmo.cancion.corderito": "Mary Had a Little Lamb",
  "ritmo.tarjeta.ta": "ta", "ritmo.tarjeta.ti_ti": "ti-ti", "ritmo.tarjeta.ta_a": "ta-a", "ritmo.tarjeta.shh": "shh",
  "ritmo.tarjeta.mudo_ayuda": "Listen and look",
  "ritmo.voz.escucha": ["Listen…", "Listen closely…", "Get ready, listen…"],
  "ritmo.voz.turno": ["Now you!", "Your turn!", "Now it's your turn!"],
  "ritmo.voz.cuenta": ["We count to four and you start.", "Get ready: I count four and you go.", "I count four and you come in."],
  "ritmo.voz.tiempo_lento": "Now it goes slowly, like a turtle.",
  "ritmo.voz.tiempo_medio": "Now it goes at a normal pace, like a rabbit.",
  "ritmo.voz.tiempo_rapido": "Now it goes fast, like a cheetah.",
  "ritmo.voz.intro.eco": "Listen to the rhythm and copy it exactly. You can tap the drum on the screen or play your instrument.",
  "ritmo.voz.intro.pulso": "A beat is like a heartbeat: always steady. Listen and repeat the steady hits.",
  "ritmo.voz.intro.tempo": "Notice how fast or how slow the rhythm goes, and copy it at the same speed.",
  "ritmo.voz.intro.base": "I'm going to play a backing beat. Listen and hit with every click, nice and steady.",
  "ritmo.voz.intro.solo": "First I help you with the backing beat. Then I go quiet and you keep the beat by yourself.",
  "ritmo.voz.intro.silencio": "Careful: sometimes there is a rest. You don't hit there: shh! Keep the beat and wait.",
  "ritmo.voz.intro.lectura": "Read the cards from left to right. Ta is a hit, shh is a rest. We count and you start.",
  "ritmo.voz.intro.lectura_ti_ti": "Now there are ti-ti cards: two quick hits in a single beat. We count and you start.",
  "ritmo.voz.intro.cancion": "This is the rhythm of a song you know. Sing it in your head and play its rhythm.",
  "ritmo.voz.intro.llamada": "I play a rhythm and you answer with yours, following the beat. Make up anything you like!",
  "ritmo.voz.intro.compone": "Make your own four-beat rhythm by choosing cards. Then we play it together.",
  "ritmo.voz.casi": ["Almost! Let's try again.", "So close! Let's listen again.", "Good try! Let's go again."],
  "ritmo.voz.faltan": "A hit was missing. Let's listen again.",
  "ritmo.voz.sobra": "There was one hit too many. Let's listen again!",
  "ritmo.voz.sobra_silencio": "There was a rest there. Shh! Let's try again.",
  "ritmo.voz.adelantado": "You were a little quick on the {ord} hit. Wait a little longer.",
  "ritmo.voz.atrasado": "The {ord} hit came a little late. Almost there!",
  "ritmo.voz.sin_golpes": "I didn't hear you. Try again; you can also tap the drum on the screen.",
  "ritmo.voz.pregunta": "Shall we go on to the next one?",
  "ritmo.voz.revela": "This one was hard! Look and listen to how it goes. We'll practice it again in a little while.",
  "ritmo.voz.libre_ok": "You answered following the beat! What a nice rhythm you made up!",
  "ritmo.voz.libre_muy_poco": "Try with more hits: two or more, following the beat.",
  "ritmo.voz.libre_muchos": "That was a lot of hits. Try fewer, nice and steady.",
  "ritmo.voz.libre_desparejo": "Your hits drifted a little from the beat. Let's try again!",
  "ritmo.voz.compone_escucha": "Listen to how your rhythm sounds.",
  "ritmo.voz.compone_al_menos": "Put in at least one hit, not all rests!",
  "ritmo.voz.modo_pantalla": "Now we play with the drum on the screen.",
  "ritmo.voz.mic_pedir": "I'm going to listen to the noise in the room. Stay quiet for a few seconds.",
  "ritmo.voz.mic_listo": "Ready! Make a hit to try it out.",
  "ritmo.voz.mic_oyo": "I heard you! We can play now.",
  "ritmo.voz.mic_mucho": "It's quite noisy in the room. Try a quieter place, or use the drum on the screen.",
  "ritmo.voz.mic_error": "I couldn't use the microphone. We'll use the drum on the screen.",
  "ritmo.ok_msgs": ["You listened and followed the beat!", "You paid attention to the rhythm!", "You took care of the beat, nice!"],
  "ritmo.ui.volver": " Back", "ritmo.ui.escuchar": " Listen", "ritmo.ui.seguir": "Next ➜",
  "ritmo.ui.pad": "Tap here", "ritmo.ui.pad_alt": "Drum",
  "ritmo.ui.mic_escucho": "I'm listening", "ritmo.ui.mic_pantalla": "🥁 Use the screen",
  "ritmo.ui.tarjeta_mic_on_t": "Use the screen", "ritmo.ui.tarjeta_mic_on_s": "I'm listening now: play your instrument",
  "ritmo.ui.tarjeta_mic_off_t": "Play with my instrument", "ritmo.ui.tarjeta_mic_off_s": "Drum, cajon, claps… I'm listening!",
  "ritmo.ui.calibrando": "Shhh… I'm listening to the noise in the room", "ritmo.ui.calibrando_sub": "Stay quiet for {s} seconds",
  "ritmo.ui.calibrado": "Ready! Make a hit to try it out", "ritmo.ui.oi": "I heard you!", "ritmo.ui.cerrar": "Done", "ritmo.ui.usar_pantalla": "Use the screen",
  "ritmo.ui.ruido_bajo": "Quiet room", "ritmo.ui.ruido_medio": "Some noise", "ritmo.ui.ruido_alto": "Very noisy",
  "ritmo.ui.componer_ta": "ta", "ritmo.ui.componer_ti_ti": "ti-ti", "ritmo.ui.componer_shh": "shh", "ritmo.ui.componer_borrar": "Clear",
  "ritmo.ui.ordinales": ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "11th", "12th", "13th", "14th", "15th", "16th"],
  "ritmo.ui.cuenta": "1 · 2 · 3 · 4",
  "ritmo.panel.texto": " — Rhythm Island: the 🎤 is turned on from the island (“Play with my instrument”).",
  "ritmo.panel.sens": "Hit sensitivity", "ritmo.panel.nivel": "Level", "ritmo.panel.recalibrar": "Recalibrate noise", "ritmo.panel.estado": "Hit microphone:",
  "ritmo.panel.estado_apagado": "off (the screen is used)", "ritmo.panel.estado_ok": "listening · background noise {piso} · threshold {umbral}",
  "ritmo.panel.pie": "Rhythm: the app measures WHEN each hit sounds and how even it is; it does not judge how the instrument sounds or the technique. Try first with 10 even hits.",
  "ritmo.informe.titulo": "RHYTHM STEADINESS (Rhythm Island)",
  "ritmo.informe.como": "   Mean deviation = how many milliseconds each hit is off from the expected moment (less is steadier). It is measured only on the FIRST try of each exercise.",
  "ritmo.informe.general": "   Overall mean deviation: {d} ms (n={n} exercises) · {mic} with an instrument, {tq} on screen",
  "ritmo.informe.mejora": "   Progress: first {k} exercises {a} ms → last {k} {b} ms ({delta})",
  "ritmo.informe.mejora_menos": "improved by {x} ms", "ritmo.informe.mejora_mas": "{x} ms less steady", "ritmo.informe.mejora_igual": "no clear change",
  "ritmo.informe.pocos": "   Progress: shown once there are at least {n} measured exercises.",
  "ritmo.informe.por_dia": "   By day practiced: {lista}",
  "ritmo.informe.sesgo": "   Tendency: usually hits {dir} (about {x} ms; includes the screen's or microphone's own delay).",
  "ritmo.informe.sesgo_adelante": "a little before the beat", "ritmo.informe.sesgo_atras": "a little after the beat", "ritmo.informe.sesgo_nada": "right on the beat",
  "ritmo.informe.por_hab": "   By skill (mean deviation): {lista}",
  "ritmo.informe.aclaracion": "   Important: the app only measures when the hits sound and how even they are. It does not judge technique, sound, tuning or whether the instrument is played well; an adult or a teacher can see that.",
});

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
    tempos: [{ n: "lento", bpm: 54, e: "🐢", voz: "tiempo_lento" }, { n: "medio", bpm: 84, e: "🐇", voz: "tiempo_medio" }, { n: "rapido", bpm: 124, e: "🐆", voz: "tiempo_rapido" }] },
  { id: "rit_base", icon: "🥁", type: "base", req: ["rit_pulso"], pulsos: 8, bpms: [70, 80, 90] },
  { id: "rit_eco3", icon: "3️⃣", type: "eco", req: ["rit_eco2"], pats: ["T T H", "H T T", "T H T", "T TT", "TT T", "T T T"], bpms: [76, 88] },
  { id: "rit_eco4", icon: "4️⃣", type: "eco", req: ["rit_eco3"], pats: ["T T TT", "TT TT", "T TT T", "TT T T", "T T T H", "T H T T"], bpms: [76, 88] },
  { id: "rit_silencio", icon: "🤫", type: "silencio", req: ["rit_eco3", "rit_base"], pats: ["T T S T", "T S T T", "T T T S", "T S T S", "S T T T"], bpms: [70, 80] },
  { id: "rit_solo", icon: "🧘", type: "solo", req: ["rit_base", "rit_tempo"], pulsos: 12, apoyo: [6, 4, 2], bpms: [70, 80] },
  { id: "rit_lee1", icon: "🔵", type: "lectura", req: ["rit_silencio"], gen: { tt: false, s: true, compases: 1 }, bpms: [70, 80], intro: "lectura" },
  { id: "rit_lee2", icon: "🟠", type: "lectura", req: ["rit_lee1"], gen: { tt: true, s: true, compases: 1 }, bpms: [70, 80], intro: "lectura_ti_ti" },
  { id: "rit_llamada", icon: "📣", type: "llamada", req: ["rit_eco4", "rit_base"], pats: ["T T T T", "T TT T T", "T T TT T", "TT T T T", "T T H"], bpms: [76, 86] },
  { id: "rit_cancion", icon: "🎵", type: "cancion", req: ["rit_lee2"], bpms: [76, 86] },
  { id: "rit_leemix", icon: "📖", type: "lectura", req: ["rit_lee2", "rit_solo"], gen: { tt: true, s: true, compases: 2 }, bpms: [70, 80], intro: "lectura_ti_ti" },
  { id: "rit_compone", icon: "🎨", type: "compone", req: ["rit_lee2", "rit_llamada"], bpms: [72, 80] },
];

/* ---- ritmos de canciones tradicionales de dominio público. SOLO el patrón rítmico de una frase (sin letra), simplificado. ---- */
const CANCIONES = [
  { id: "estrellita", emoji: "⭐", pat: "T T T T T T H" },
  { id: "martinillo", emoji: "🔔", pat: "T T T T T T T T" },
  { id: "martinillo2", emoji: "🔔", pat: "T T H T T H" },
  { id: "martinillo3", emoji: "🔔", pat: "TT TT T T" },
  { id: "panCaliente", emoji: "🥐", pat: "T T H T T H" },
  { id: "corderito", emoji: "🐑", pat: "T T T T T T H" },
];

/* ---- paletas de la composición ---- */
const COMPONER = { pulsos: 4, fichas: ["T", "TT", "S"] };

Gioval.datos.ritmo = { AJUSTES, HABILIDADES, CANCIONES, COMPONER };
})();
