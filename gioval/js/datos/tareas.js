"use strict";
/* ============ AYUDANTES DE LA CASA: textos y lista editable de tareas ============
   Este archivo es SOLO datos (no hay lógica). La pantalla y el cronómetro están en js/islas/ayudantes.js.
   Se edita a mano: agregar, sacar o cambiar una tarea no requiere tocar nada más.

   ---------------------------------------------------------------------------------------------------------
   LISTA PARA QUE MARCOS LA APRUEBE  (revisar antes de publicar)
   ---------------------------------------------------------------------------------------------------------
   Criterio de exclusión (ninguna tarea de la lista lo incluye; la prueba automática lo vigila en los PASOS):
     - FUEGO y CALOR: hornallas, horno, estufa, plancha, agua o comida caliente, hervir, freír.
     - FILO: cuchillos, tijeras, abrelatas, latas, vidrio roto, rallador.
     - PRODUCTOS QUÍMICOS: lavandina, detergente, desinfectantes, jabones fuertes, abonos, venenos.
     - ESCALERAS y ALTURAS: nada de subirse a sillas, banquitos ni escaleras; solo lo que se alcanza desde el piso.
     - ELECTRICIDAD: enchufes, electrodomésticos, cables.
   Cuando una tarea toca algo cercano a esos riesgos (cubiertos, platos, plantas, residuos, mascotas, cocina), el
   riesgo se evita en los PASOS (se usa lo que no se rompe, ni corta, ni quema) y además lleva un AVISO de seguridad
   que se lee en voz alta y se ve antes de empezar.

   Nivel de supervisión (obligatorio en cada tarea):
     "solo"   = puede hacerla por su cuenta (igual se le avisa a un adulto cuando termina).
     "cerca"  = con un adulto cerca, que mira y ayuda si hace falta.
     "adulto" = SOLO con un adulto al lado: para empezarla la app pide la pregunta de adultos (como el panel).
   Regla de la prueba automática: toda tarea "cerca" o "adulto" TIENE que traer un aviso de seguridad no vacío.

   Tareas (edad mínima en años · minutos sugeridos · supervisión):
     mesa_poner        Poner la mesa                          4 · 5  · cerca   (cuchillos y vidrio: los pone un adulto)
     mesa_levantar     Levantar la mesa                       5 · 5  · cerca   (vidrio y lo que quema: lo levanta un adulto)
     juguetes          Guardar los juguetes                   4 · 10 · solo    (sin subirse a nada)
     plantas           Regar las plantas                      4 · 5  · cerca   (solo agua; el piso mojado resbala)
     zapatos           Ordenar los zapatos                    4 · 3  · solo
     ropa              Acomodar la ropa limpia                5 · 10 · solo    (dedos en los cajones)
     mascota           Dar de comer a la mascota              5 · 5  · adulto  (con adulto; no molestar al animal que come)
     reciclaje         Separar papel, cartón y plástico       5 · 10 · cerca   (vidrio y latas: los separa un adulto)
     secar             Secar cubiertos de plástico            5 · 5  · cerca   (ya lavados y fríos; nada que corte)
     cocinar_verduras  Ayudar a cocinar: lavar verduras       5 · 10 · adulto  (agua fría, sobre la mesa, adulto al lado)
     cama              Hacer la cama                          5 · 5  · solo    (la cucheta de arriba la hace un adulto)
     mochila           Preparar la mochila                    4 · 5  · solo    (lo que corta lo guarda un adulto)

   Cambios respecto de la lista anterior (que tenía cama, dientes, juguetes, mochila):
     - Se conservaron los ids "cama", "juguetes" y "mochila".
     - SE SACÓ "Lavarse los dientes" (id "dientes"): es higiene personal, no ayuda para la casa. Si querés
       conservarla, agregá la línea de nuevo con supervision "solo".
   ---------------------------------------------------------------------------------------------------------
   IMPORTANTE: los ids son parte de lo que se guarda (tareas asignadas, registro de "ayudó N veces").
   No los renombres una vez publicados; si hace falta sacar una tarea, es más seguro deshabilitarla desde el panel.
   Los textos van en TEXTOS (el trabajo de traducción lo encuentra todo acá). {n}, {min}, {nombre}... son huecos.
   ============================================================================================================ */
(function () {
  const TEXTOS = {
    nombre: "Ayudantes de la casa",
    horaTitulo: "Hora de ayudantes",

    /* ---- cuando se termina el tiempo de pantalla ---- */
    topeExtra: "Si querés, ¡es la hora de ayudantes!",
    topeBoton: "🧹 Hora de ayudantes",
    tarjetaTitulo: "Hora de ayudantes",
    tarjetaSub: "¡Ayudá en casa un ratito!",

    /* ---- pantalla del niño ---- */
    volver: "⬅",
    volverLbl: " Volver",
    elegi: "¿Qué tarea querés hacer?",
    elegiVoz: "¡Hora de ayudantes! Elegí una tarea para ayudar en casa.",
    pedida: "📌 Te la pidió un adulto",
    vacio: "Todavía no hay tareas para hoy. ¡Gracias igual!",
    min: "{n} min",
    supervision: {
      solo: { icono: "🙂", corto: "Por tu cuenta", largo: "Podés hacerla por tu cuenta.", voz: "Podés hacerla por tu cuenta." },
      cerca: { icono: "👀", corto: "Con un adulto cerca", largo: "Con un adulto cerca.", voz: "Pedile a un adulto que esté cerca." },
      adulto: { icono: "🧑‍🤝‍🧑", corto: "Solo con un adulto", largo: "Solo con un adulto al lado.", voz: "Esta tarea es solo con un adulto al lado." },
    },
    pasoN: "Paso {n}.",
    ojo: "Ojo:",
    escuchar: "🔊 Escuchar",
    empezar: "▶ ¡Empezar! ({n} min)",
    empezarAdulto: "🔒 Empezar con un adulto",
    avisoAdulto: "Un adulto tiene que estar al lado. Pedile que te ayude a empezar.",
    otraTarea: "⬅ Otra tarea",
    leyendoPasos: "{nombre}.",

    /* ---- cronómetro ---- */
    vamos: "¡Vamos! Tenés {n} minutos para {nombre}.",
    vamos1: "¡Vamos! Tenés un minuto para {nombre}.",
    terminePronto: "✅ ¡Ya terminé!",
    cancelar: "Dejarla por ahora",
    cancelado: "Está bien, la dejamos por ahora. ¡Otro día la hacés!",
    tiempoSeTermino: "⏰ ¡Se terminó el tiempo!",
    tiempoVoz: "¡Se terminó el tiempo! ¿Pudiste terminar?",
    tiempoTarde: "Volviste a la app y ya había pasado el tiempo. Está bien: ¿pudiste terminar?",
    termine: "✅ ¡Terminé!",
    masTiempo: "⏳ Un ratito más",
    masTiempoVoz: "¡Dale! Un ratito más.",
    masMinutos: 2,
    alarmaTitulo: "Mundo Gioval · Ayudantes",
    alarmaTexto: "¡Se terminó el tiempo de «{nombre}»!",
    tareaEnCurso: "Tenías una tarea en curso: {nombre}.",

    /* ---- al terminar (siempre elogio del esfuerzo, nunca de la persona; sin rachas ni puntos) ---- */
    elogios: [
      "¡Gracias por ayudar! Le pusiste ganas.",
      "¡Terminaste lo que empezaste! Eso lleva esfuerzo.",
      "¡Ayudaste y se nota! Gracias por el esfuerzo.",
      "¡Qué bien que te animaste a ayudar!",
      "¡Tu ayuda sirve un montón en casa!",
    ],
    finTitulo: "¡Gracias por ayudar!",
    semana1: "Esta semana ayudaste 1 vez.",
    semanaN: "Esta semana ayudaste {n} veces.",
    foto: "📷 Sacar una foto",
    fotoOk: "📷 ¡Foto guardada!",
    fotoVoz: "¡Qué lindo! Guardé la foto.",
    otraMas: "Elegir otra tarea",
    listo: "Listo, a descansar",

    /* ---- zona de adultos ---- */
    panel: {
      titulo: "🧹 Ayudantes de la casa",
      elegirJugador: "Elegí quién juega para configurar los ayudantes.",
      activar: "Ofrecer “Hora de ayudantes” cuando se termina el tiempo de pantalla",
      aclaracion: "El tiempo de ayudantes NO cuenta como tiempo de pantalla.",
      edad: "Edad:",
      anios: "{n} años",
      duracion: "Duración:",
      duracionTarea: "La que sugiere cada tarea",
      duracionMin: "{n} min",
      tareas: "Tareas habilitadas (☑) y asignadas (📌, se quitan solas cuando las hace):",
      edadDesde: "desde {n} años",
      foto: "Permitir sacar una foto al terminar (queda solo en este aparato)",
      abrirAhora: "▶ Abrir Hora de ayudantes ahora",
      semana: "Esta semana ayudó: {n}.",
      semanaNada: "Esta semana todavía no hay tareas anotadas.",
      vez: "vez",
      veces: "veces",
      fotos: "Fotos guardadas: {n}.",
      alarmaTitulo: "⚠️ Alarma con pantalla apagada: no garantizada en navegador; se resuelve con la app Android nativa.",
      alarmaDetalle: "Si el teléfono se bloquea o la app se cierra, el aviso puede no sonar a la hora. Al volver a abrir la app se recalcula con la hora real y suena enseguida (diciendo que ya pasó el tiempo). Mientras el niño usa la tarea con la pantalla encendida, suena sin problemas.",
      wakeSi: "Pantalla encendida mientras corre: sí (si el navegador lo permite).",
      wakeNo: "Pantalla encendida mientras corre: este navegador no lo permite.",
      notifGranted: "Avisos del sistema: permitidos (igual no se garantiza con la pantalla apagada).",
      notifDenied: "Avisos del sistema: bloqueados en este navegador.",
      notifDefault: "Avisos del sistema: sin permitir.",
      notifNo: "Avisos del sistema: este navegador no los ofrece.",
      permitir: "Permitir avisos",
      nativaSi: "App nativa: se detectó Capacitor; la alarma también se programa en el sistema. Todavía hay que probarla en el aparato.",
      nativaNo: "App nativa: no disponible (se usa el navegador).",
    },
  };

  const TAREAS = [
    { id: "mesa_poner", emoji: "🍽️", nombre: "Poner la mesa", minutos: 5, edadMin: 4, supervision: "cerca",
      pasos: ["Contá cuántas personas van a comer.", "Poné un plato y un vaso que no se rompan en cada lugar.", "Poné una cuchara o un tenedor al lado de cada plato."],
      aviso: "Los cuchillos los pone un adulto. Si algo es de vidrio o se puede romper, lo lleva un adulto." },
    { id: "mesa_levantar", emoji: "🧺", nombre: "Levantar la mesa", minutos: 5, edadMin: 5, supervision: "cerca",
      pasos: ["Llevá a la cocina tus platos y vasos que no se rompen, de a uno o de a dos.", "Llevá también los cubiertos de plástico.", "Pasá un repasador seco por la mesa para sacar las migas."],
      aviso: "Lo que es de vidrio, lo que tiene filo y lo que está caliente lo levanta un adulto." },
    { id: "juguetes", emoji: "🧸", nombre: "Guardar los juguetes", minutos: 10, edadMin: 4, supervision: "solo",
      pasos: ["Juntá los juguetes que están en el piso.", "Poné cada uno en su caja o en su lugar.", "Los que están muy arriba, dejalos: los guarda un adulto."],
      aviso: "Sin subirte a nada: solo guardás lo que alcanzás con los pies en el piso. Mirá dónde pisás: las piezas chiquitas lastiman." },
    { id: "plantas", emoji: "🪴", nombre: "Regar las plantas", minutos: 5, edadMin: 4, supervision: "cerca",
      pasos: ["Un adulto te deja la regadera chiquita con agua.", "Echá un poquito de agua en la tierra de cada planta.", "Pará cuando la tierra se ve mojada."],
      aviso: "Solo agua, nada de abonos ni productos. No pruebes hojas ni flores. Si cae agua al piso, avisá para secarla: resbala." },
    { id: "zapatos", emoji: "👟", nombre: "Ordenar los zapatos", minutos: 3, edadMin: 4, supervision: "solo",
      pasos: ["Juntá los zapatos que están desparramados.", "Buscá el par de cada uno: izquierdo y derecho.", "Ponelos en fila en el zapatero o junto a la puerta."],
      aviso: "" },
    { id: "ropa", emoji: "👕", nombre: "Acomodar la ropa limpia", minutos: 10, edadMin: 5, supervision: "solo",
      pasos: ["Separá la ropa en pilas: remeras, pantalones, medias.", "Doblá lo que puedas, una prenda por vez.", "Poné cada pila en su cajón, o llevala a su pieza."],
      aviso: "Cuidado con los dedos al cerrar los cajones." },
    { id: "mascota", emoji: "🐶", nombre: "Dar de comer a la mascota", minutos: 5, edadMin: 5, supervision: "adulto",
      pasos: ["Pedile a un adulto la medida de comida que le toca.", "Poné la comida en el plato de tu mascota.", "Con un adulto, cambiale el agua del bebedero.", "Lavate las manos al terminar."],
      aviso: "Siempre con un adulto al lado. No molestes a un animal mientras come. La comida de la mascota no se prueba." },
    { id: "reciclaje", emoji: "♻️", nombre: "Separar papel, cartón y plástico", minutos: 10, edadMin: 5, supervision: "cerca",
      pasos: ["Mirá cada cosa: ¿es de papel, de cartón o de plástico?", "Poné el papel y el cartón en su bolsa.", "Poné los envases de plástico limpios en la otra bolsa.", "Lavate las manos al terminar."],
      aviso: "El vidrio, las latas y todo lo que lastima lo separa un adulto. Si algo está sucio o no sabés qué es, preguntá." },
    { id: "secar", emoji: "🥄", nombre: "Secar cubiertos de plástico", minutos: 5, edadMin: 5, supervision: "cerca",
      pasos: ["Un adulto te pasa los cubiertos de plástico ya lavados y fríos.", "Agarrá un repasador limpio y secá cada uno.", "Ponelos en el escurridor o en su cajón."],
      aviso: "Solo cosas de plástico y siempre ya lavadas. El vidrio, las ollas y todo lo que corta lo seca un adulto." },
    { id: "cocinar_verduras", emoji: "🥕", nombre: "Ayudar a cocinar: lavar verduras", minutos: 10, edadMin: 5, supervision: "adulto",
      pasos: ["Un adulto te trae las verduras y un bol con agua fría, sobre la mesa.", "Frotá cada verdura despacito con las manos, bajo el agua.", "Pasalas a un colador o a un plato limpio.", "Lavate las manos al terminar."],
      aviso: "Siempre con un adulto al lado. Solo agua fría y a la altura de la mesa. El adulto corta y cocina; no se prueba nada hasta que él o ella lo indique." },
    { id: "cama", emoji: "🛏️", nombre: "Hacer la cama", minutos: 5, edadMin: 5, supervision: "solo",
      pasos: ["Estirá la sábana para que no queden arrugas.", "Acomodá la almohada.", "Estirá la colcha o el acolchado por arriba."],
      aviso: "Si dormís en una cucheta de arriba, esa cama la hace un adulto." },
    { id: "mochila", emoji: "🎒", nombre: "Preparar la mochila", minutos: 5, edadMin: 4, supervision: "solo",
      pasos: ["Mirá la lista de lo que necesitás mañana.", "Poné adentro tu cuaderno, tu estuche y tu botella.", "Cerrá el cierre y dejala junto a la puerta."],
      aviso: "Si en el estuche hay algo que corta, como una tijera, lo guarda un adulto." },
  ];

  Gioval.datos.ayudantes = { TEXTOS, tareas: TAREAS };
  Gioval.datos.tareas = TAREAS; /* nombre anterior, por compatibilidad */
})();
