"use strict";
/* ============ DATOS DE MISIONES REALES (editable) ============
   Actividades FUERA de la pantalla que el niño hace con un adulto y después registra en la app.
   TODO lo que se lee o se escucha está en TEXTOS (acá arriba): así se puede traducir o corregir sin tocar el código.
   Debajo de TEXTOS está la estructura de cada misión (id, categoría, edad mínima, nivel de supervisión, tipo).

   CÓMO EDITAR / AGREGAR UNA MISIÓN (ver gioval-dev/docs/MISIONES.md):
     1. Agregá sus textos en TEXTOS.misiones.<id>  y su estructura en MISIONES.
     2. La app NO muestra una misión que no pase validar(): le exige materiales, pasos, nivel de supervisión,
        aviso de seguridad y que no nombre nada de la lista PROHIBIDAS (fuego, filo, químicos, resina, etc.).
     3. Si no estás 100% seguro de un dato científico, ponele a la misión  revisar:"A REVISAR: <qué falta confirmar>".
        La app NO muestra esa explicación al niño ni al adulto hasta que se saque la marca.
   Reglas de la casa: sin elogio a la persona ("sos un genio"); se elogia el proceso (qué probó, qué observó);
   sin rachas ni puntos. Voz rioplatense ("vos"). */

const TEXTOS = {
  ui: {
    isla: { nombre: "Isla Misiones", sub: "¡Cosas de verdad!", etiquetaTiempo: "🌿 Sin tope de pantalla" },
    hablaMenu: "¡Misiones! Son cosas de verdad, afuera de la pantalla, con un adulto. ¿Qué hacemos?",
    tarjetas: {
      semana: "Misión de la semana", semanaSub: "Elegida para esta semana",
      elegir: "Elegir una misión", elegirSub: "Construir, experimentos, cocina…",
      album: "Mi álbum", albumSub0: "Acá van a quedar tus recuerdos", albumSub: n => n === 1 ? "1 recuerdo" : n + " recuerdos",
      pendiente: "Mirar:", pendienteSub: dias => dias < 1 ? "Empezaste hoy" : (dias === 1 ? "Empezaste ayer" : "Empezaste hace " + dias + " días"),
    },
    lista: { titulo: "🧭 Elegir una misión", todas: "Todas", volver: "Volver", desde: n => "Desde los " + n + " años", hecha: n => n === 1 ? "Hecha 1 vez" : "Hecha " + n + " veces", semanaTag: "⭐ De la semana", bloqueada: "🔒 Un poco más grande" },
    supervision: {
      cerca: { corto: "👀 Con un adulto cerca", detalle: "Un adulto tiene que estar cerca, mirando, por si necesitás ayuda." },
      junto: { corto: "🤝 Solo con un adulto al lado", detalle: "Esta misión se hace únicamente con un adulto al lado, paso a paso." },
    },
    /* lo que se ve en el globito de la mascota (corto); lo largo se dice en voz alta y se lee en pantalla */
    burbuja: { listo: "Primero, el aviso: lo lee un adulto.", materiales: "Juntemos los materiales.", antes: "Pensá antes de empezar.", hacer: (i, n) => "Paso " + i + " de " + n + ".", espera: "¡Quedó armado!", quepaso: "¿Qué pasó?", porque: "¿Por qué creés?", registro: "Guardemos el recuerdo.", fin: "¡Misión registrada!" },
    listo: { aviso: "⚠️ Antes de empezar", adulto: "✅ Un adulto está conmigo. ¡Listo!", volver: "Volver", habla: (nombre, resumen, aviso) => nombre.replace(/[.!?¡¿]+$/, "") + ". " + resumen + " Antes de empezar, un adulto tiene que escuchar esto. " + aviso },
    materiales: { titulo: "🧺 Juntemos los materiales", ayuda: "Tocá cada cosa cuando la tengas.", todo: "Tengo todo ➜", falta: "Me falta algo", faltaHabla: "No pasa nada. Cuando tengas todo, hacemos la misión.", habla: "Juntemos los materiales. Tocá cada cosa cuando la tengas." },
    antes: { titulo: "🤔 Antes de empezar", otra: "💬 Otra idea (la digo en voz alta)", nose: "🤷 No sé", otraPuesta: "Otra idea (dicha en voz alta)", noseTexto: "No sabía", escribir: "Escribí o dictá tu idea (opcional)", seguir: "Seguir ➜" },
    hacer: { paso: (i, n) => "Paso " + i + " de " + n, anterior: "⬅ Antes", siguiente: "Siguiente ➜", ultimo: "✅ ¡Ya lo hice!" },
    timer: { poner: seg => "⏱ Poner temporizador (" + Math.round(seg / 60) + " min)", cancelar: "Cancelar temporizador", corre: "⏱ Falta ", fin: "¡Pasó el tiempo! Fijate qué pasó.", titulo: "Mundo Gioval · Misión", texto: "¡Pasó el tiempo de tu misión!" },
    espera: { titulo: "🌱 ¡Quedó armado!", texto: dias => "Ahora hay que esperar. Volvé a mirar en unos " + dias + " días y contá qué pasó. Lo vas a encontrar en la Isla Misiones.", guardar: "Guardar y mirar más tarde", habla: dias => "¡Quedó armado! Ahora hay que esperar. Volvé a mirar en unos " + dias + " días.", despedida: "Guardado. ¡Volvé a mirarlo en unos días!" },
    quePaso: { titulo: "👀 ¿Qué pasó?", habla: "¿Qué pasó? Mirá bien y elegí lo que viste.", otra: "Pasó otra cosa", pensabas: "Habías pensado:", seguir: "Seguir ➜" },
    porque: { titulo: "💡 ¿Por qué creés que pasó?", habla: "¿Por qué creés que pasó? Pensalo y contáselo al adulto. No hay una sola respuesta: lo importante es pensar.", escribir: "Escribí o dictá tu idea (opcional)", ver: "👨‍👩‍👦 Ver la explicación", ocultar: "Ocultar la explicación", paraAdulto: "Para el adulto: leela y contásela con tus palabras", guia: "Para preguntar:", seguir: "Seguir ➜" },
    registro: {
      titulo: "📖 Guardemos el recuerdo", habla: "Guardemos el recuerdo. Contá con tus palabras qué hiciste, y elegí si salió como pensabas o distinto.",
      frase: "Mi frase", frasePH: "Escribí o dictá lo que querés recordar", pensaba: "✅ Salió como pensaba", distinto: "🔄 Salió distinto", elegi: "Elegí una de las dos",
      guardar: "📖 Guardar en mi álbum", dictar: "🎤 Dictar", escuchando: "🎤 Escuchando…", sinFrase: "(sin frase)",
    },
    adulto: {
      resumen: "👨‍👩‍👦 Para el adulto",
      foto: "Guardar una foto en este aparato (no se sube a ningún lado, ni a internet ni a la nube)", fotoOff: "Para sacar una foto, el adulto tiene que activar el permiso.",
      dictado: "Dictado por voz (el navegador puede usar un servicio de internet para entender lo que se dice)",
      sacar: "📷 Sacar una foto", otra: "📷 Sacar otra", quitar: "✖ Quitar la foto", sinAlmacen: "Este aparato no permite guardar fotos. Se guarda el recuerdo sin foto.", fotoError: "No pude guardar la foto. El recuerdo se guardó sin foto.",
      lecturaError: "No pude leer esa foto. Probá con otra.",
    },
    fin: {
      titulo: "¡Misión registrada!", mas: "🧭 Más misiones", album: "📖 Ver mi álbum", isla: "🏝️ A la isla",
      /* Elogio al PROCESO (qué hizo), nunca a la persona. */
      predijo: ["Dijiste lo que pensabas antes de probar.", "Pensaste una idea antes de empezar."],
      miro: ["Miraste con atención qué pasaba.", "Observaste con cuidado."],
      conto: ["Lo contaste con tus palabras.", "Pusiste en palabras lo que viste."],
      foto: ["Guardaste una foto de tu trabajo."],
      pensaba: ["Lo que pensabas se parecía a lo que pasó."],
      distinto: ["Salió distinto de lo que pensabas, y eso también sirve: ahora sabés algo nuevo."],
      hacer: ["Lo hiciste paso a paso.", "Seguiste los pasos con paciencia."],
      cierre: ["¡Quedó guardado en tu álbum!"],
    },
    album: {
      titulo: "📖 Mi álbum", vacio: "Todavía no hay recuerdos. Cuando termines una misión, va a aparecer acá.", volver: "Volver",
      adultos: "🔒 Para adultos", niño: "👦 Volver a la vista del niño", infoAdulto: "Vista de adultos. Todo queda solo en este aparato y entra en el respaldo (⚙️ → Exportar respaldo).",
      pensaba: "✅ Salió como pensaba", distinto: "🔄 Salió distinto", predijo: "Pensé:", paso: "Pasó:", porque: "Por qué:",
      sinFoto: "📷 La foto no está en este aparato", borrar: "🗑 Borrar el recuerdo", borrarFoto: "🗑 Borrar solo la foto",
      confirmaRecuerdo: "¿Borrar este recuerdo y su foto? No se puede deshacer.", confirmaFoto: "¿Borrar solo la foto? El recuerdo queda sin foto. No se puede deshacer.", si: "Sí, borrar", no: "No",
      semanaSemLabel: "Semana", pendienteDe: "Esperando",
    },
    panel: { titulo: "🧭 Misiones", edad: "Edad de ", años: n => n + " años", semana: "Misión de la semana: ", auto: "Automática (según la edad)", album: "📖 Álbum (adultos)", sinPerfil: "Primero elegí quién juega." },
  },
  categorias: {
    construir: "Construir", experimentos: "Experimentos", cocina: "Cocina", huerta: "Huerta", arte: "Arte", hogar: "Hogar",
  },
  misiones: {
    construir_puente: {
      nombre: "Puente de papel",
      resumen: "Armá un puente con una hoja y fijate cuánto peso aguanta.",
      aviso: "Hacelo en el piso o en una mesa baja y usá libros chicos: si se cae uno, puede lastimar un pie. Las monedas y las cositas chicas no se llevan a la boca.",
      materiales: ["2 libros o cajas del mismo alto", "2 hojas de papel iguales", "Autitos o bloques de juguete livianos para poner arriba (o monedas, si ya sabés que no se llevan a la boca)", "Un lugar plano, mejor en el piso"],
      pasos: [
        "Poné los dos libros parados, con un espacio en el medio de más o menos un palmo.",
        "Apoyá una hoja lisa sobre los dos libros, como si fuera un puente.",
        "Poné los autitos de a uno sobre el puente. Contá cuántos aguanta antes de doblarse mucho.",
        "Ahora doblá la otra hoja como un acordeón, con pliegues del ancho de un dedo.",
        "Apoyala como puente y poné los autitos de a uno. ¿Cuántos aguanta ahora?",
      ],
      prediccion: { pregunta: "¿Qué creés que va a pasar? ¿Qué puente va a aguantar más autitos?", opciones: ["El liso", "El de pliegues", "Los dos igual"] },
      observacion: ["El liso aguantó más", "El de pliegues aguantó más", "Aguantaron igual"],
      guia: "Preguntale: ¿qué cambió entre una hoja y la otra? ¿Dónde se doblaba el puente liso?",
      explicacion: "Con pliegues, la misma hoja se vuelve mucho más dura: un papel doblado en acordeón se dobla menos que uno liso, y por eso aguanta más peso con el mismo papel. Esa idea se usa en los techos de chapa acanalada y en el cartón corrugado de las cajas.",
    },
    construir_casita: {
      nombre: "Casita de cajas",
      resumen: "Armá una casita o un garaje para un muñeco con cajas de cartón.",
      aviso: "Pasale la mano a las cajas para ver si tienen bordes que raspan o puntas de grapas; si hay, que el adulto las tape con cinta o las cambie. No uses cajas que hayan tenido productos de limpieza.",
      materiales: ["3 o 4 cajas de cartón chicas y limpias (de cereales, galletitas o zapatos)", "Cinta de enmascarar, en tiritas que arranca el adulto", "Un muñeco o un autito para que viva o se estacione", "Marcadores para decorar"],
      pasos: [
        "Mirá las cajas y pensá: ¿cuál va abajo? ¿Cuál va arriba?",
        "Apilá las cajas para armar la casita. Probá de distintas formas hasta que quede firme.",
        "Unilas con las tiritas de cinta que te dio el adulto.",
        "Decorala con marcadores: puertas, ventanas, techo.",
        "Poné al muñeco adentro. ¿Entra? Si no entra, ¿qué cambiarías?",
      ],
      imaginar: "Antes de empezar, imaginá: ¿cómo va a ser tu casita?",
    },
    exp_flota: {
      nombre: "¿Flota o se hunde?",
      resumen: "Adiviná qué cosas flotan en el agua y cuáles se hunden, y después probalo.",
      aviso: "Usá una palangana o un balde con poca agua, sobre el piso con una toalla. Si se derrama, secalo enseguida para que nadie se resbale. El agua no es para tomar. Las cosas chiquitas no se llevan a la boca.",
      materiales: ["Una palangana o un balde con agua hasta la mitad", "Una toalla", "4 cosas para probar: por ejemplo un corcho, una hoja de árbol, una piedra chica y una moneda"],
      pasos: [
        "Poné las cosas en fila sobre la toalla.",
        "Antes de probar, señalá cuáles creés que flotan y cuáles se hunden.",
        "Poné una cosa por vez en el agua, despacito.",
        "Mirá bien qué pasa. ¿Flota? ¿Se hunde? ¿Se hunde rápido o despacio?",
        "Sacá todo del agua con las manos y secá lo que se mojó.",
      ],
      prediccion: { pregunta: "¿Qué creés que va a pasar? ¿Qué va a pasar con tus cosas?", opciones: ["Todas flotan", "Algunas flotan y otras se hunden", "Todas se hunden"] },
      observacion: ["Todas flotaron", "Algunas flotaron y otras se hundieron", "Todas se hundieron"],
      guia: "Preguntale: ¿qué tienen en común las que flotaron? ¿Y las que se hundieron?",
      explicacion: "Una cosa flota cuando pesa poco para su tamaño; por ejemplo, el corcho tiene muchos huequitos con aire adentro. Se hunde cuando pesa mucho para su tamaño, como una piedra o una moneda de metal. No depende solo de lo pesada que sea: un barco enorme de metal flota porque tiene mucho espacio con aire adentro.",
    },
    exp_hielo: {
      nombre: "Hielo al sol o a la sombra",
      resumen: "Poné dos cubitos de hielo, uno al sol y otro a la sombra, y mirá cuál se derrite más rápido.",
      aviso: "Nunca mires directo al sol y usá gorrita. El hielo está muy frío: no te lo pongas en la boca (puede atragantar) y no lo agarres mucho rato. Secá el agua que se derrame.",
      materiales: ["2 cubitos de hielo del mismo tamaño (los saca el adulto del freezer)", "2 platitos iguales", "Un lugar con sol y un lugar con sombra, cerca uno del otro", "Un temporizador (la app te lo prepara)"],
      pasos: [
        "Pedile al adulto que saque dos cubitos de hielo y los ponga en los platitos.",
        "Poné un platito al sol y el otro a la sombra. Los dos al mismo tiempo.",
        "Tocá el botón del temporizador y esperá. Mientras tanto, mirá cómo cambian los cubitos.",
        "Cuando suene, mirá cuál se derritió más. ¿Cuánta agua hay en cada platito?",
        "Llevá los platitos adentro y volcá el agua en la pileta.",
      ],
      prediccion: { pregunta: "¿Qué creés que va a pasar? ¿Qué cubito se va a derretir más rápido?", opciones: ["El del sol", "El de la sombra", "Los dos igual"] },
      observacion: ["Se derritió más el del sol", "Se derritió más el de la sombra", "Se derritieron igual"],
      guia: "Preguntale: ¿qué le da el sol al hielo? ¿Qué pasaría si lo ponemos adentro del freezer?",
      explicacion: "El hielo se derrite cuando recibe calor. Al sol le llega mucho más calor que a la sombra, porque la luz del sol le da energía a todo lo que toca; por eso el cubito del sol se derrite más rápido. A la sombra también se derrite, porque el aire que lo rodea está más tibio que el hielo, pero más despacio. En un día muy frío, los dos tardarían mucho más.",
    },
    cocina_plastilina: {
      nombre: "Plastilina casera",
      resumen: "Prepará masa para modelar con harina, sal y agua fría.",
      aviso: "Solo con un adulto al lado. Esta masa no es para comer: tiene mucha sal. Tiene harina de trigo: si alguien tiene alergia o es celíaco, preguntale al adulto antes. El colorante mancha: poné delantal y mantel. Lavate las manos antes y después, y no te las lleves a la boca.",
      materiales: ["2 tazas de harina común", "1 taza de sal fina", "1 taza de agua fría de la canilla (se agrega de a poquito)", "2 cucharadas de aceite", "Colorante comestible (unas gotitas)", "Un bol grande y una cuchara", "Una bandeja o un mantel de plástico"],
      pasos: [
        "Poné la harina y la sal en el bol y mezclalas con la cuchara.",
        "Agregá el aceite y unas gotitas de colorante.",
        "Poné el agua de a poquito, un chorrito por vez, y seguí mezclando. Fijate cómo va cambiando la masa.",
        "Cuando se junta todo, amasá con las manos sobre la bandeja. Si queda pegajosa, agregá un puñadito de harina; si queda dura, unas gotas de agua.",
        "¡Modelá lo que quieras! Un bichito, una letra, tu nombre.",
        "Cuando termines, guardá la masa en un frasco o una bolsa bien cerrada y lavate las manos.",
      ],
      imaginar: "Antes de empezar, pensá: ¿cómo creés que se va a sentir la masa cuando esté lista?",
    },
    cocina_vasitos: {
      nombre: "Vasitos de yogur con frutas",
      resumen: "Armá un vasito con capas de yogur y frutas.",
      aviso: "Solo con un adulto al lado. Antes, el adulto tiene que fijarse si alguien es alérgico a alguna de estas comidas. Lavate las manos con agua y jabón. La fruta tiene que estar en trocitos chiquitos, que prepara el adulto, para que nadie se atragante. No se come nada hasta terminar de armar el vasito.",
      materiales: ["Yogur", "2 o 3 frutas lavadas, en trocitos chiquitos que prepara el adulto (banana, frutilla, durazno)", "Cereales de desayuno (si querés)", "Vasos transparentes", "Cucharas"],
      pasos: [
        "Lavate las manos con agua y jabón.",
        "Poné una capa de yogur en el fondo del vaso, con la cuchara.",
        "Agregá una capa de fruta. Después otra de yogur. Fijate cómo se ven las capas a través del vaso.",
        "Terminá con cereales o una frutilla arriba.",
        "¡A comerlo despacito, sentado y con el adulto cerca!",
      ],
      imaginar: "Antes de empezar, imaginá: ¿cuántas capas va a tener tu vasito?",
    },
    huerta_poroto: {
      nombre: "Un poroto que despierta",
      resumen: "Poné un poroto en un vaso con algodón húmedo y mirá qué le pasa en unos días.",
      aviso: "El poroto seco no se come crudo (hace mal) ni se mete en la boca, la nariz ni los oídos. El algodón tampoco se come. Usá un vaso de plástico, no de vidrio. Lavate las manos después. Si aparece pelusa blanca o verde (moho), no la toques: avisale al adulto para que tire todo.",
      materiales: ["1 o 2 porotos secos, de los de cocina", "Un vaso de plástico transparente", "Algodón", "Un poco de agua", "Un lugar con luz, cerca de una ventana"],
      pasos: [
        "Mojá el algodón con un poquito de agua y apretalo: tiene que quedar húmedo, no chorreando.",
        "Poné el algodón en el vaso, apretadito contra las paredes.",
        "Metele el poroto entre el algodón y el vaso, para poder verlo desde afuera.",
        "Poné el vaso cerca de una ventana. Cada día, fijate si el algodón sigue húmedo y agregale una cucharadita de agua si hace falta.",
        "Mirá el poroto todos los días y dibujá lo que ves. Cuando aparezca algo nuevo, volvé a la app a contarlo.",
      ],
      espera: { dias: 3 },
      prediccion: { pregunta: "¿Qué creés que va a pasar? ¿Qué va a salir primero del poroto?", opciones: ["Una hojita", "Una raicita", "No va a salir nada"] },
      observacion: ["Salió primero una raicita", "Salió primero una hojita", "Todavía no pasó nada"],
      guia: "Preguntale: ¿hacia dónde crece la raicita? ¿Qué creés que necesita el poroto para despertar?",
      explicacion: "Adentro de la semilla ya hay una plantita chiquita y su comida. Con agua y una temperatura agradable, la semilla se hincha y se despierta; eso se llama germinar. Lo primero que sale es la raíz, que sirve para agarrarse y tomar agua; después sale el tallito con las hojas. Para despertar, el poroto no necesita luz; cuando ya tiene hojitas, sí la necesita para crecer.",
    },
    huerta_bichitos: {
      nombre: "Safari de bichitos",
      resumen: "Salí a buscar bichitos al jardín y mirá cómo son, sin tocarlos.",
      aviso: "Mirá con los ojos, sin tocar. No toques bichos, nidos ni telarañas, y no levantes piedras ni macetas sin un adulto: abajo puede haber bichos que pican. Si algo te pica, avisale al adulto enseguida. Usá gorrita y zapatos cerrados, y lavate las manos al volver.",
      materiales: ["Un patio, una plaza o un jardín", "Un cuaderno y un lápiz (o el adulto anota)", "Una gorrita y zapatos cerrados", "Un adulto que camine con vos"],
      pasos: [
        "Caminá despacito por el jardín con el adulto.",
        "Mirá las hojas, la tierra, las flores y las paredes. Los bichitos se esconden.",
        "Cuando veas uno, quedate quieto y mirá: ¿cuántas patas tiene? ¿De qué color es? ¿Qué está haciendo?",
        "Dibujalo en el cuaderno o contáselo al adulto.",
        "Contá cuántos bichitos distintos encontraste.",
      ],
      temporizador: { paso: 0, seg: 600 },
      prediccion: { pregunta: "¿Qué creés que va a pasar? ¿Cuántos bichitos vas a encontrar?", opciones: ["Muchos", "Pocos", "Casi ninguno"] },
      observacion: ["Encontré muchos", "Encontré pocos", "No encontré casi ninguno"],
      guia: "Preguntale: ¿en qué lugares había más bichitos? ¿Qué creés que hacían ahí?",
      explicacion: "Los bichitos viven donde encuentran comida, humedad y un lugar para esconderse; por eso es más fácil verlos entre las hojas, en la tierra húmeda y sobre las plantas. Cada tipo de bichito elige su lugar, y en distintos momentos del día o del año se ven bichitos distintos.",
    },
    arte_colores: {
      nombre: "Mezclar colores con agua",
      resumen: "Mezclá agua de colores y descubrí qué colores nuevos salen.",
      aviso: "El colorante mancha la ropa y las manos: poné delantal y mantel de plástico. El agua de colores no es para tomar, aunque parezca jugo. Usá vasos de plástico y lavate las manos al terminar.",
      materiales: ["3 vasos de plástico transparentes con agua", "Colorante comestible rojo, azul y amarillo", "3 vasos de plástico vacíos para mezclar", "Una cuchara", "Un mantel de plástico y un delantal"],
      pasos: [
        "Poné agua en tres vasos y unas gotitas de colorante en cada uno: rojo, azul y amarillo. Pedile ayuda al adulto con las gotitas.",
        "Mirá los tres colores. Pensá: ¿qué va a salir si juntamos amarillo con azul?",
        "Volcá un poquito de amarillo y un poquito de azul en un vaso vacío. Mezclá con la cuchara.",
        "Probá otras mezclas en vasos nuevos: rojo con amarillo, y rojo con azul. Fijate qué sale.",
        "Probá poner más de un color que del otro. ¿Cambia el resultado?",
      ],
      prediccion: { pregunta: "¿Qué creés que va a pasar? ¿Qué color sale si juntamos amarillo con azul?", opciones: ["Verde", "Naranja", "Violeta", "Marrón"] },
      observacion: ["Salió verde", "Salió naranja", "Salió violeta", "Salió marrón", "Salió otro color"],
      guia: "Preguntale: ¿qué pasó cuando pusiste más de un color? ¿Qué otros colores te gustaría inventar?",
      explicacion: "Cada colorante deja pasar su propio color de luz y frena los demás. Al juntar dos, solo pasa el color que los dos dejan pasar: amarillo con azul da verde, rojo con amarillo da naranja y rojo con azul da violeta. Si ponés más cantidad de un color, el resultado se parece más a ese. Si juntás los tres, queda un color oscuro.",
    },
    arte_dibujo_secreto: {
      nombre: "Dibujo secreto",
      resumen: "Dibujá con crayón blanco y descubrí tu dibujo con pintura.",
      aviso: "La pintura no se come ni se prueba. Usá témperas o acuarelas que digan “no tóxico”. Poné delantal y mantel, y lavate las manos al terminar.",
      materiales: ["Una hoja blanca", "Un crayón de cera blanco (o de un color muy clarito)", "Acuarelas o témpera aguada", "Un pincel o una esponjita", "Un vaso con agua", "Un mantel y un delantal"],
      pasos: [
        "Con el crayón blanco, dibujá algo bien fuerte sobre la hoja blanca: una estrella, tu nombre, un animal. Apretá bien.",
        "Mojá el pincel y pintá toda la hoja con un color, de lado a lado.",
        "Mirá qué pasa con tu dibujo secreto.",
      ],
      prediccion: { pregunta: "Vas a dibujar con crayón blanco y después pintar toda la hoja. ¿Qué creés que va a pasar?", opciones: ["Se va a ver mi dibujo", "No se va a ver nada", "Se va a mezclar con la pintura"] },
      observacion: ["Apareció mi dibujo", "No apareció nada", "Pasó otra cosa"],
      guia: "Preguntale: ¿dónde se pegó la pintura y dónde no? ¿Qué otras cosas creés que no se mojan?",
      explicacion: "El crayón está hecho de cera, y la cera rechaza el agua: la pintura con agua resbala donde hay cera y se pega en el papel limpio. Por eso el dibujo aparece, como un mensaje secreto.",
    },
    hogar_medias: {
      nombre: "Pares de medias",
      resumen: "Buscá las parejas de un montón de medias y contá los pares.",
      aviso: "Usá solo ropa limpia y seca. Si encontrás algo que no es ropa (monedas, cositas chiquitas), no lo agarres: avisale al adulto. Fijate que no haya nada en el piso donde caminás.",
      materiales: ["Un montón de medias limpias y mezcladas (unas 10 o 12)", "Un lugar plano, como la cama o el piso", "Una canasta o un cajón para guardar los pares"],
      pasos: [
        "Desparramá las medias sobre la cama o el piso.",
        "Agarrá una media y buscá su pareja: tiene que ser igual.",
        "Juntá cada par y doblalos juntos.",
        "Contá cuántos pares armaste. ¿Sobró alguna media sin pareja?",
        "Guardá los pares en su lugar.",
      ],
      imaginar: "Antes de empezar, pensá: ¿cuántos pares de medias creés que hay?",
    },
    hogar_mesa: {
      nombre: "Poner la mesa",
      resumen: "Poné la mesa para toda la familia: un plato, un vaso y cubiertos para cada uno.",
      aviso: "Llevá las cosas de a una o dos, caminando despacio. Usá platos y vasos de plástico o irrompibles. Si algo se cae o se rompe, no lo toques: llamá al adulto. Si algo se derrama, secalo para que nadie se resbale.",
      materiales: ["Un plato, un vaso, una cuchara y un tenedor por cada persona que come", "Servilletas", "Una mesa libre"],
      pasos: [
        "Contá cuántas personas van a comer. Eso te dice cuántos platos necesitás.",
        "Poné un plato adelante de cada silla.",
        "Poné la cuchara, el tenedor y un vaso en cada lugar.",
        "Poné una servilleta en cada lugar.",
        "Fijate: ¿hay un plato, un vaso y cubiertos para cada uno? Contá de nuevo para comprobar.",
      ],
      imaginar: "Antes de empezar, pensá: ¿cuántos platos vas a necesitar?",
    },
  },
};

/* Estructura de cada misión. sup: "cerca" | "junto". tipo: "experimento" (predicción → hacer → qué pasó → por qué),
   "observar" (igual, salida a mirar) o "hacer" (se imagina antes y se registra al final).
   espera:{dias} = hay que esperar días para ver el resultado (queda "empezada" hasta que el niño vuelve a mirarla).
   temporizador:{paso,seg} = ofrece el temporizador (módulo Alarma) en ese paso (0 = primero).
   revisar:"A REVISAR: …" = no se muestra la explicación científica hasta confirmarla. */
const MISIONES = [
  { id: "construir_puente",    cat: "construir",    emoji: "🌉", minEdad: 5, sup: "cerca", tipo: "experimento" },
  { id: "construir_casita",    cat: "construir",    emoji: "🏠", minEdad: 4, sup: "cerca", tipo: "hacer" },
  { id: "exp_flota",           cat: "experimentos", emoji: "💧", minEdad: 4, sup: "cerca", tipo: "experimento" },
  { id: "exp_hielo",           cat: "experimentos", emoji: "🧊", minEdad: 4, sup: "cerca", tipo: "experimento", temporizador: { paso: 2, seg: 600 } },
  { id: "cocina_plastilina",   cat: "cocina",       emoji: "🥣", minEdad: 4, sup: "junto", tipo: "hacer" },
  { id: "cocina_vasitos",      cat: "cocina",       emoji: "🍓", minEdad: 4, sup: "junto", tipo: "hacer" },
  { id: "huerta_poroto",       cat: "huerta",       emoji: "🌱", minEdad: 4, sup: "cerca", tipo: "experimento", espera: { dias: 3 } },
  { id: "huerta_bichitos",     cat: "huerta",       emoji: "🐛", minEdad: 4, sup: "cerca", tipo: "observar", temporizador: { paso: 0, seg: 600 } },
  { id: "arte_colores",        cat: "arte",         emoji: "🌈", minEdad: 4, sup: "cerca", tipo: "experimento" },
  { id: "arte_dibujo_secreto", cat: "arte",         emoji: "🖍️", minEdad: 4, sup: "cerca", tipo: "experimento" },
  { id: "hogar_medias",        cat: "hogar",        emoji: "🧦", minEdad: 4, sup: "cerca", tipo: "hacer" },
  { id: "hogar_mesa",          cat: "hogar",        emoji: "🍽️", minEdad: 4, sup: "cerca", tipo: "hacer" },
];

/* Lo que NUNCA puede aparecer en una misión (ni siquiera como "no lo hagas"). Se compara sin tildes y en minúsculas.
   Fuego y calor, filo y herramientas de corte, químicos del hogar, electricidad de red, resinas/epoxi/solventes. */
const PROHIBIDAS = [
  "fuego", "fogata", "fogon", "llamarada", "encend\\w*", "fosforo\\w*", "velas?", "hornalla\\w*", "horno\\w*", "estufa\\w*", "microondas", "plancha\\w*",
  "hervi\\w*", "hirvi\\w*", "calent\\w*", "calient\\w*", "quem\\w*", "ardi\\w*", "soplete\\w*", "lupa\\w*",
  "cuchill\\w*", "tijera\\w*", "filos?", "afilad\\w*", "navaja\\w*", "trincheta\\w*", "cutter", "cuter", "serrucho\\w*", "sierra\\w*", "hacha", "machete", "cortar", "cortad\\w*", "corta", "cortan", "corte", "cortes", "martillo\\w*", "taladro\\w*", "clavo\\w*", "pistola",
  "lavandina", "cloro", "lejia", "amoniaco", "solvente\\w*", "thinner", "aguarras", "diluyente\\w*", "nafta", "kerosene", "querosene", "acetona", "alcohol", "oxigenada", "vinagre", "bicarbonato",
  "desinfectante\\w*", "limpiador\\w*", "desengras\\w*", "destapa\\w*", "acido\\w*", "caustic\\w*", "veneno\\w*", "insecticida\\w*", "pesticida\\w*", "herbicida\\w*", "fertilizante\\w*",
  "resina\\w*", "epoxi\\w*", "poliester", "fibra de vidrio", "catalizador\\w*", "pegamento instantaneo", "gotita", "pegamento de contacto",
  "enchufe\\w*", "electric\\w*", "tomacorriente\\w*", "alargue\\w*", "cargador\\w*", "cable\\w*", "voltaje",
];
const _REGEX_PROHIBIDAS = PROHIBIDAS.map(p => new RegExp("(^|[^a-z])(" + p + ")($|[^a-z])"));
function _norm(s) { return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
function _textos(x, out) { if (typeof x === "string") out.push(x); else if (Array.isArray(x)) x.forEach(y => _textos(y, out)); else if (x && typeof x === "object") Object.keys(x).forEach(k => _textos(x[k], out)); return out; }
/* palabras prohibidas que aparecen en un texto (lista vacía = limpio) */
function palabrasProhibidas(texto) { const t = _norm(texto), hit = []; _REGEX_PROHIBIDAS.forEach((re, i) => { if (re.test(t)) hit.push(PROHIBIDAS[i].replace("\\w*", "")); }); return hit; }
/* Devuelve la lista de problemas de una misión (vacía = se puede mostrar). textos = TEXTOS.misiones por defecto (los tests pueden pasar otros). */
function validar(m, textos) {
  const p = [], t = (textos || TEXTOS.misiones)[m && m.id];
  if (!m || !m.id) return ["falta el id"];
  if (!t) return ["no tiene textos en TEXTOS.misiones"];
  if (!TEXTOS.categorias[m.cat]) p.push("categoría desconocida");
  if (!(m.minEdad >= 4)) p.push("la edad mínima tiene que ser 4 o más");
  if (!TEXTOS.ui.supervision[m.sup]) p.push("falta el nivel de supervisión (cerca o junto)");
  if (!["experimento", "observar", "hacer"].includes(m.tipo)) p.push("tipo desconocido");
  if (!t.nombre) p.push("falta el nombre");
  if (!t.resumen) p.push("falta el resumen");
  if (!t.aviso || String(t.aviso).trim().length < 20) p.push("falta el aviso de seguridad");
  if (!Array.isArray(t.materiales) || !t.materiales.length) p.push("faltan los materiales");
  if (!Array.isArray(t.pasos) || t.pasos.length < 2) p.push("faltan los pasos (mínimo 2)");
  if (m.tipo === "hacer") { if (!t.imaginar) p.push("falta la frase de “imaginá”"); }
  else {
    if (!t.prediccion || !t.prediccion.pregunta || !Array.isArray(t.prediccion.opciones) || t.prediccion.opciones.length < 2) p.push("falta la predicción (pregunta y 2 opciones)");
    if (!Array.isArray(t.observacion) || t.observacion.length < 2) p.push("faltan las opciones de “¿qué pasó?”");
    if (!t.guia) p.push("falta la guía para el adulto");
    if (!t.explicacion && !m.revisar) p.push("falta la explicación (o marcá revisar)");
  }
  if (m.espera && !(m.espera.dias >= 1)) p.push("espera.dias inválido");
  if (m.temporizador && !(m.temporizador.seg > 0 && t.pasos && m.temporizador.paso >= 0 && m.temporizador.paso < t.pasos.length)) p.push("temporizador inválido");
  _textos(t, []).forEach(s => { const h = palabrasProhibidas(s); if (h.length) p.push("palabra prohibida «" + h[0] + "» en: " + s.slice(0, 50)); });
  return p;
}

Gioval.datos.misiones = { TEXTOS, MISIONES, PROHIBIDAS, validar, palabrasProhibidas };
