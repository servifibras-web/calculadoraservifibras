"use strict";
/* ============ DATOS DE MISIONES REALES (editable) ============
   Actividades FUERA de la pantalla que el niño hace con un adulto y después registra en la app.

   TEXTOS: TODO lo que se lee o se escucha está acá arriba, en las tablas de idioma (Gioval.i18n.agregar), una clave por texto:
     misiones.ui.*            la interfaz de la isla (frases completas; plurales y género con ICU: {n, plural, one{…} other{…}})
     misiones.cat.<categoría> el nombre de cada categoría
     misiones.m.<id>.*        los textos de cada misión: nombre, resumen, aviso, materiales (lista), pasos (lista),
                              prediccion.pregunta, prediccion.opciones (lista), observacion (lista), guia, explicacion, imaginar
   es-AR es el idioma base (obligatorio); "en" tiene las mismas claves (lo exige la prueba de completitud). es-419 y es-ES caen a es-AR
   (voseo) mientras nadie escriba su variante. Cualquier otro idioma que traiga textos de misiones necesita además SU lista de palabras
   prohibidas (ver PROHIBIDAS_EN): si falta, validar() oculta la misión.
   Debajo de los textos está la estructura de cada misión (id, categoría, edad mínima, nivel de supervisión, tipo).

   CÓMO EDITAR / AGREGAR UNA MISIÓN (ver gioval-dev/docs/MISIONES.md):
     1. Agregá sus textos (misiones.m.<id>.*) en es-AR y en en, y su estructura en MISIONES.
     2. La app NO muestra una misión que no pase validar(): le exige materiales, pasos, nivel de supervisión,
        aviso de seguridad y que ningún texto, en NINGÚN idioma, nombre algo de la lista de palabras prohibidas
        (fuego, filo, químicos, resina, etc.).
     3. Si no estás 100% seguro de un dato científico, ponele a la misión  revisar:"A REVISAR: <qué falta confirmar>".
        La app NO muestra esa explicación al niño ni al adulto hasta que se saque la marca.
   Reglas de la casa: sin elogio a la persona ("sos un genio"); se elogia el proceso (qué probó, qué observó);
   sin rachas ni puntos. Voz rioplatense ("vos") en es-AR. Las traducciones las tiene que revisar una persona que hable el idioma
   (sobre todo los avisos de seguridad). */

Gioval.i18n.agregar("es-AR", {

  "misiones.ui.isla.nombre": "Isla Misiones",
  "misiones.ui.isla.sub": "¡Cosas de verdad!",
  "misiones.ui.isla.etiqueta_tiempo": "🌿 Sin tope de pantalla",
  "misiones.ui.isla.habla_menu": "¡Misiones! Son cosas de verdad, afuera de la pantalla, con un adulto. ¿Qué hacemos?",

  "misiones.ui.tarjetas.semana": "Misión de la semana",
  "misiones.ui.tarjetas.semana_sub": "Elegida para esta semana",
  "misiones.ui.tarjetas.elegir": "Elegir una misión",
  "misiones.ui.tarjetas.elegir_sub": "Construir, experimentos, cocina…",
  "misiones.ui.tarjetas.album": "Mi álbum",
  "misiones.ui.tarjetas.album_sub0": "Acá van a quedar tus recuerdos",
  "misiones.ui.tarjetas.album_sub": "{n, plural, one{# recuerdo} other{# recuerdos}}",
  "misiones.ui.tarjetas.pendiente": "Mirar: {nombre}",
  "misiones.ui.tarjetas.pendiente_sub": "{dias, plural, =0{Empezaste hoy} =1{Empezaste ayer} other{Empezaste hace # días}}",

  "misiones.ui.lista.titulo": "🧭 Elegir una misión",
  "misiones.ui.lista.todas": "Todas",
  "misiones.ui.lista.volver": "Volver",
  "misiones.ui.lista.desde": "Desde los {n} años",
  "misiones.ui.lista.hecha": "{n, plural, one{Hecha # vez} other{Hecha # veces}}",
  "misiones.ui.lista.semana_tag": "⭐ De la semana",
  "misiones.ui.lista.bloqueada": "🔒 Un poco más grande",

  "misiones.ui.supervision.cerca.corto": "👀 Con un adulto cerca",
  "misiones.ui.supervision.cerca.detalle": "Un adulto tiene que estar cerca, mirando, por si necesitás ayuda.",
  "misiones.ui.supervision.junto.corto": "🤝 Solo con un adulto al lado",
  "misiones.ui.supervision.junto.detalle": "Esta misión se hace únicamente con un adulto al lado, paso a paso.",

  "misiones.ui.burbuja.listo": "Primero, el aviso: lo lee un adulto.",
  "misiones.ui.burbuja.materiales": "Juntemos los materiales.",
  "misiones.ui.burbuja.antes": "Pensá antes de empezar.",
  "misiones.ui.burbuja.hacer": "Paso {i} de {n}.",
  "misiones.ui.burbuja.espera": "¡Quedó armado!",
  "misiones.ui.burbuja.quepaso": "¿Qué pasó?",
  "misiones.ui.burbuja.porque": "¿Por qué creés?",
  "misiones.ui.burbuja.registro": "Guardemos el recuerdo.",
  "misiones.ui.burbuja.fin": "¡Misión registrada!",

  "misiones.ui.listo.aviso": "⚠️ Antes de empezar",
  "misiones.ui.listo.adulto": "✅ Un adulto está conmigo. ¡Listo!",
  "misiones.ui.listo.volver": "Volver",
  "misiones.ui.listo.habla": "{nombre}. {resumen} Antes de empezar, un adulto tiene que escuchar esto. {aviso}",

  "misiones.ui.materiales.titulo": "🧺 Juntemos los materiales",
  "misiones.ui.materiales.ayuda": "Tocá cada cosa cuando la tengas.",
  "misiones.ui.materiales.todo": "Tengo todo ➜",
  "misiones.ui.materiales.falta": "Me falta algo",
  "misiones.ui.materiales.falta_habla": "No pasa nada. Cuando tengas todo, hacemos la misión.",
  "misiones.ui.materiales.habla": "Juntemos los materiales. Tocá cada cosa cuando la tengas.",

  "misiones.ui.antes.titulo": "🤔 Antes de empezar",
  "misiones.ui.antes.otra": "💬 Otra idea (la digo en voz alta)",
  "misiones.ui.antes.nose": "🤷 No sé",
  "misiones.ui.antes.otra_puesta": "Otra idea (dicha en voz alta)",
  "misiones.ui.antes.nose_texto": "No sabía",
  "misiones.ui.antes.escribir": "Escribí o dictá tu idea (opcional)",
  "misiones.ui.antes.seguir": "Seguir ➜",

  "misiones.ui.hacer.paso": "Paso {i} de {n}",
  "misiones.ui.hacer.anterior": "⬅ Antes",
  "misiones.ui.hacer.siguiente": "Siguiente ➜",
  "misiones.ui.hacer.ultimo": "✅ ¡Ya lo hice!",

  "misiones.ui.timer.poner": "⏱ Poner temporizador ({min} min)",
  "misiones.ui.timer.cancelar": "Cancelar temporizador",
  "misiones.ui.timer.corre": "⏱ Falta {tiempo}",
  "misiones.ui.timer.fin": "¡Pasó el tiempo! Fijate qué pasó.",
  "misiones.ui.timer.titulo": "Mundo Gioval · Misión",
  "misiones.ui.timer.texto": "¡Pasó el tiempo de tu misión!",

  "misiones.ui.espera.titulo": "🌱 ¡Quedó armado!",
  "misiones.ui.espera.texto": "Ahora hay que esperar. Volvé a mirar en {dias, plural, one{# día} other{unos # días}} y contá qué pasó. Lo vas a encontrar en la Isla Misiones.",
  "misiones.ui.espera.guardar": "Guardar y mirar más tarde",
  "misiones.ui.espera.habla": "¡Quedó armado! Ahora hay que esperar. Volvé a mirar en {dias, plural, one{# día} other{unos # días}}.",
  "misiones.ui.espera.despedida": "Guardado. ¡Volvé a mirarlo en unos días!",

  "misiones.ui.que_paso.titulo": "👀 ¿Qué pasó?",
  "misiones.ui.que_paso.habla": "¿Qué pasó? Mirá bien y elegí lo que viste.",
  "misiones.ui.que_paso.otra": "Pasó otra cosa",
  "misiones.ui.que_paso.pensabas": "Habías pensado:",
  "misiones.ui.que_paso.seguir": "Seguir ➜",

  "misiones.ui.porque.titulo": "💡 ¿Por qué creés que pasó?",
  "misiones.ui.porque.habla": "¿Por qué creés que pasó? Pensalo y contáselo al adulto. No hay una sola respuesta: lo importante es pensar.",
  "misiones.ui.porque.escribir": "Escribí o dictá tu idea (opcional)",
  "misiones.ui.porque.ver": "👨‍👩‍👦 Ver la explicación",
  "misiones.ui.porque.ocultar": "Ocultar la explicación",
  "misiones.ui.porque.para_adulto": "Para el adulto: leela y contásela con tus palabras",
  "misiones.ui.porque.guia": "Para preguntar:",
  "misiones.ui.porque.seguir": "Seguir ➜",

  "misiones.ui.registro.titulo": "📖 Guardemos el recuerdo",
  "misiones.ui.registro.habla": "Guardemos el recuerdo. Contá con tus palabras qué hiciste, y elegí si salió como pensabas o distinto.",
  "misiones.ui.registro.frase": "Mi frase",
  "misiones.ui.registro.frase_ph": "Escribí o dictá lo que querés recordar",
  "misiones.ui.registro.pensaba": "✅ Salió como pensaba",
  "misiones.ui.registro.distinto": "🔄 Salió distinto",
  "misiones.ui.registro.elegi": "Elegí una de las dos",
  "misiones.ui.registro.guardar": "📖 Guardar en mi álbum",
  "misiones.ui.registro.dictar": "🎤 Dictar",
  "misiones.ui.registro.escuchando": "🎤 Escuchando…",
  "misiones.ui.registro.sin_frase": "(sin frase)",

  "misiones.ui.adulto.resumen": "👨‍👩‍👦 Para el adulto",
  "misiones.ui.adulto.foto": "Guardar una foto en este aparato (no se sube a ningún lado, ni a internet ni a la nube)",
  "misiones.ui.adulto.foto_off": "Para sacar una foto, el adulto tiene que activar el permiso.",
  "misiones.ui.adulto.dictado": "Dictado por voz (el navegador puede usar un servicio de internet para entender lo que se dice)",
  "misiones.ui.adulto.sacar": "📷 Sacar una foto",
  "misiones.ui.adulto.otra": "📷 Sacar otra",
  "misiones.ui.adulto.quitar": "✖ Quitar la foto",
  "misiones.ui.adulto.sin_almacen": "Este aparato no permite guardar fotos. Se guarda el recuerdo sin foto.",
  "misiones.ui.adulto.foto_error": "No pude guardar la foto. El recuerdo se guardó sin foto.",
  "misiones.ui.adulto.lectura_error": "No pude leer esa foto. Probá con otra.",

  "misiones.ui.fin.titulo": "¡Misión registrada!",
  "misiones.ui.fin.mas": "🧭 Más misiones",
  "misiones.ui.fin.album": "📖 Ver mi álbum",
  "misiones.ui.fin.isla": "🏝️ A la isla",
  "misiones.ui.fin.predijo": ["Dijiste lo que pensabas antes de probar.","Pensaste una idea antes de empezar."],
  "misiones.ui.fin.miro": ["Miraste con atención qué pasaba.","Observaste con cuidado."],
  "misiones.ui.fin.conto": ["Lo contaste con tus palabras.","Pusiste en palabras lo que viste."],
  "misiones.ui.fin.foto": ["Guardaste una foto de tu trabajo."],
  "misiones.ui.fin.pensaba": ["Lo que pensabas se parecía a lo que pasó."],
  "misiones.ui.fin.distinto": ["Salió distinto de lo que pensabas, y eso también sirve: ahora sabés algo nuevo."],
  "misiones.ui.fin.hacer": ["Lo hiciste paso a paso.","Seguiste los pasos con paciencia."],
  "misiones.ui.fin.cierre": ["¡Quedó guardado en tu álbum!"],

  "misiones.ui.album.titulo": "📖 Mi álbum",
  "misiones.ui.album.vacio": "Todavía no hay recuerdos. Cuando termines una misión, va a aparecer acá.",
  "misiones.ui.album.volver": "Volver",
  "misiones.ui.album.adultos": "🔒 Para adultos",
  "misiones.ui.album.nino": "👦 Volver a la vista del niño",
  "misiones.ui.album.info_adulto": "Vista de adultos. Todo queda solo en este aparato y entra en el respaldo (⚙️ → Exportar respaldo).",
  "misiones.ui.album.pensaba": "✅ Salió como pensaba",
  "misiones.ui.album.distinto": "🔄 Salió distinto",
  "misiones.ui.album.predijo": "Pensé:",
  "misiones.ui.album.paso": "Pasó:",
  "misiones.ui.album.porque": "Por qué:",
  "misiones.ui.album.sin_foto": "📷 La foto no está en este aparato",
  "misiones.ui.album.borrar": "🗑 Borrar el recuerdo",
  "misiones.ui.album.borrar_foto": "🗑 Borrar solo la foto",
  "misiones.ui.album.confirma_recuerdo": "¿Borrar este recuerdo y su foto? No se puede deshacer.",
  "misiones.ui.album.confirma_foto": "¿Borrar solo la foto? El recuerdo queda sin foto. No se puede deshacer.",
  "misiones.ui.album.si": "Sí, borrar",
  "misiones.ui.album.no": "No",

  "misiones.ui.panel.titulo": "🧭 Misiones",
  "misiones.ui.panel.edad": "Edad de {nombre}:",
  "misiones.ui.panel.anos": "{n, plural, one{# año} other{# años}}",
  "misiones.ui.panel.semana": "Misión de la semana:",
  "misiones.ui.panel.auto": "Automática (según la edad)",
  "misiones.ui.panel.album": "📖 Álbum (adultos)",
  "misiones.ui.panel.sin_perfil": "Primero elegí quién juega.",

  "misiones.cat.construir": "Construir",

  "misiones.cat.experimentos": "Experimentos",

  "misiones.cat.cocina": "Cocina",

  "misiones.cat.huerta": "Huerta",

  "misiones.cat.arte": "Arte",

  "misiones.cat.hogar": "Hogar",

  "misiones.m.construir_puente.nombre": "Puente de papel",
  "misiones.m.construir_puente.resumen": "Armá un puente con una hoja y fijate cuánto peso aguanta.",
  "misiones.m.construir_puente.aviso": "Hacelo en el piso o en una mesa baja y usá libros chicos: si se cae uno, puede lastimar un pie. Las monedas y las cositas chicas no se llevan a la boca.",
  "misiones.m.construir_puente.materiales": ["2 libros o cajas del mismo alto","2 hojas de papel iguales","Autitos o bloques de juguete livianos para poner arriba (o monedas, si ya sabés que no se llevan a la boca)","Un lugar plano, mejor en el piso"],
  "misiones.m.construir_puente.pasos": ["Poné los dos libros parados, con un espacio en el medio de más o menos un palmo.","Apoyá una hoja lisa sobre los dos libros, como si fuera un puente.","Poné los autitos de a uno sobre el puente. Contá cuántos aguanta antes de doblarse mucho.","Ahora doblá la otra hoja como un acordeón, con pliegues del ancho de un dedo.","Apoyala como puente y poné los autitos de a uno. ¿Cuántos aguanta ahora?"],
  "misiones.m.construir_puente.prediccion.pregunta": "¿Qué creés que va a pasar? ¿Qué puente va a aguantar más autitos?",
  "misiones.m.construir_puente.prediccion.opciones": ["El liso","El de pliegues","Los dos igual"],
  "misiones.m.construir_puente.observacion": ["El liso aguantó más","El de pliegues aguantó más","Aguantaron igual"],
  "misiones.m.construir_puente.guia": "Preguntale: ¿qué cambió entre una hoja y la otra? ¿Dónde se doblaba el puente liso?",
  "misiones.m.construir_puente.explicacion": "Con pliegues, la misma hoja se vuelve mucho más dura: un papel doblado en acordeón se dobla menos que uno liso, y por eso aguanta más peso con el mismo papel. Esa idea se usa en los techos de chapa acanalada y en el cartón corrugado de las cajas.",

  "misiones.m.construir_casita.nombre": "Casita de cajas",
  "misiones.m.construir_casita.resumen": "Armá una casita o un garaje para un muñeco con cajas de cartón.",
  "misiones.m.construir_casita.aviso": "Pasale la mano a las cajas para ver si tienen bordes que raspan o puntas de grapas; si hay, que el adulto las tape con cinta o las cambie. No uses cajas que hayan tenido productos de limpieza.",
  "misiones.m.construir_casita.materiales": ["3 o 4 cajas de cartón chicas y limpias (de cereales, galletitas o zapatos)","Cinta de enmascarar, en tiritas que arranca el adulto","Un muñeco o un autito para que viva o se estacione","Marcadores para decorar"],
  "misiones.m.construir_casita.pasos": ["Mirá las cajas y pensá: ¿cuál va abajo? ¿Cuál va arriba?","Apilá las cajas para armar la casita. Probá de distintas formas hasta que quede firme.","Unilas con las tiritas de cinta que te dio el adulto.","Decorala con marcadores: puertas, ventanas, techo.","Poné al muñeco adentro. ¿Entra? Si no entra, ¿qué cambiarías?"],
  "misiones.m.construir_casita.imaginar": "Antes de empezar, imaginá: ¿cómo va a ser tu casita?",

  "misiones.m.exp_flota.nombre": "¿Flota o se hunde?",
  "misiones.m.exp_flota.resumen": "Adiviná qué cosas flotan en el agua y cuáles se hunden, y después probalo.",
  "misiones.m.exp_flota.aviso": "Usá una palangana o un balde con poca agua, sobre el piso con una toalla. Si se derrama, secalo enseguida para que nadie se resbale. El agua no es para tomar. Las cosas chiquitas no se llevan a la boca.",
  "misiones.m.exp_flota.materiales": ["Una palangana o un balde con agua hasta la mitad","Una toalla","4 cosas para probar: por ejemplo un corcho, una hoja de árbol, una piedra chica y una moneda"],
  "misiones.m.exp_flota.pasos": ["Poné las cosas en fila sobre la toalla.","Antes de probar, señalá cuáles creés que flotan y cuáles se hunden.","Poné una cosa por vez en el agua, despacito.","Mirá bien qué pasa. ¿Flota? ¿Se hunde? ¿Se hunde rápido o despacio?","Sacá todo del agua con las manos y secá lo que se mojó."],
  "misiones.m.exp_flota.prediccion.pregunta": "¿Qué creés que va a pasar? ¿Qué va a pasar con tus cosas?",
  "misiones.m.exp_flota.prediccion.opciones": ["Todas flotan","Algunas flotan y otras se hunden","Todas se hunden"],
  "misiones.m.exp_flota.observacion": ["Todas flotaron","Algunas flotaron y otras se hundieron","Todas se hundieron"],
  "misiones.m.exp_flota.guia": "Preguntale: ¿qué tienen en común las que flotaron? ¿Y las que se hundieron?",
  "misiones.m.exp_flota.explicacion": "Una cosa flota cuando pesa poco para su tamaño; por ejemplo, el corcho tiene muchos huequitos con aire adentro. Se hunde cuando pesa mucho para su tamaño, como una piedra o una moneda de metal. No depende solo de lo pesada que sea: un barco enorme de metal flota porque tiene mucho espacio con aire adentro.",

  "misiones.m.exp_hielo.nombre": "Hielo al sol o a la sombra",
  "misiones.m.exp_hielo.resumen": "Poné dos cubitos de hielo, uno al sol y otro a la sombra, y mirá cuál se derrite más rápido.",
  "misiones.m.exp_hielo.aviso": "Nunca mires directo al sol y usá gorrita. El hielo está muy frío: no te lo pongas en la boca (puede atragantar) y no lo agarres mucho rato. Secá el agua que se derrame.",
  "misiones.m.exp_hielo.materiales": ["2 cubitos de hielo del mismo tamaño (los saca el adulto del freezer)","2 platitos iguales","Un lugar con sol y un lugar con sombra, cerca uno del otro","Un temporizador (la app te lo prepara)"],
  "misiones.m.exp_hielo.pasos": ["Pedile al adulto que saque dos cubitos de hielo y los ponga en los platitos.","Poné un platito al sol y el otro a la sombra. Los dos al mismo tiempo.","Tocá el botón del temporizador y esperá. Mientras tanto, mirá cómo cambian los cubitos.","Cuando suene, mirá cuál se derritió más. ¿Cuánta agua hay en cada platito?","Llevá los platitos adentro y volcá el agua en la pileta."],
  "misiones.m.exp_hielo.prediccion.pregunta": "¿Qué creés que va a pasar? ¿Qué cubito se va a derretir más rápido?",
  "misiones.m.exp_hielo.prediccion.opciones": ["El del sol","El de la sombra","Los dos igual"],
  "misiones.m.exp_hielo.observacion": ["Se derritió más el del sol","Se derritió más el de la sombra","Se derritieron igual"],
  "misiones.m.exp_hielo.guia": "Preguntale: ¿qué le da el sol al hielo? ¿Qué pasaría si lo ponemos adentro del freezer?",
  "misiones.m.exp_hielo.explicacion": "El hielo se derrite cuando recibe calor. Al sol le llega mucho más calor que a la sombra, porque la luz del sol le da energía a todo lo que toca; por eso el cubito del sol se derrite más rápido. A la sombra también se derrite, porque el aire que lo rodea está más tibio que el hielo, pero más despacio. En un día muy frío, los dos tardarían mucho más.",

  "misiones.m.cocina_plastilina.nombre": "Plastilina casera",
  "misiones.m.cocina_plastilina.resumen": "Prepará masa para modelar con harina, sal y agua fría.",
  "misiones.m.cocina_plastilina.aviso": "Solo con un adulto al lado. Esta masa no es para comer: tiene mucha sal. Tiene harina de trigo: si alguien tiene alergia o es celíaco, preguntale al adulto antes. El colorante mancha: poné delantal y mantel. Lavate las manos antes y después, y no te las lleves a la boca.",
  "misiones.m.cocina_plastilina.materiales": ["2 tazas de harina común","1 taza de sal fina","1 taza de agua fría de la canilla (se agrega de a poquito)","2 cucharadas de aceite","Colorante comestible (unas gotitas)","Un bol grande y una cuchara","Una bandeja o un mantel de plástico"],
  "misiones.m.cocina_plastilina.pasos": ["Poné la harina y la sal en el bol y mezclalas con la cuchara.","Agregá el aceite y unas gotitas de colorante.","Poné el agua de a poquito, un chorrito por vez, y seguí mezclando. Fijate cómo va cambiando la masa.","Cuando se junta todo, amasá con las manos sobre la bandeja. Si queda pegajosa, agregá un puñadito de harina; si queda dura, unas gotas de agua.","¡Modelá lo que quieras! Un bichito, una letra, tu nombre.","Cuando termines, guardá la masa en un frasco o una bolsa bien cerrada y lavate las manos."],
  "misiones.m.cocina_plastilina.imaginar": "Antes de empezar, pensá: ¿cómo creés que se va a sentir la masa cuando esté lista?",

  "misiones.m.cocina_vasitos.nombre": "Vasitos de yogur con frutas",
  "misiones.m.cocina_vasitos.resumen": "Armá un vasito con capas de yogur y frutas.",
  "misiones.m.cocina_vasitos.aviso": "Solo con un adulto al lado. Antes, el adulto tiene que fijarse si alguien es alérgico a alguna de estas comidas. Lavate las manos con agua y jabón. La fruta tiene que estar en trocitos chiquitos, que prepara el adulto, para que nadie se atragante. No se come nada hasta terminar de armar el vasito.",
  "misiones.m.cocina_vasitos.materiales": ["Yogur","2 o 3 frutas lavadas, en trocitos chiquitos que prepara el adulto (banana, frutilla, durazno)","Cereales de desayuno (si querés)","Vasos transparentes","Cucharas"],
  "misiones.m.cocina_vasitos.pasos": ["Lavate las manos con agua y jabón.","Poné una capa de yogur en el fondo del vaso, con la cuchara.","Agregá una capa de fruta. Después otra de yogur. Fijate cómo se ven las capas a través del vaso.","Terminá con cereales o una frutilla arriba.","¡A comerlo despacito, sentado y con el adulto cerca!"],
  "misiones.m.cocina_vasitos.imaginar": "Antes de empezar, imaginá: ¿cuántas capas va a tener tu vasito?",

  "misiones.m.huerta_poroto.nombre": "Un poroto que despierta",
  "misiones.m.huerta_poroto.resumen": "Poné un poroto en un vaso con algodón húmedo y mirá qué le pasa en unos días.",
  "misiones.m.huerta_poroto.aviso": "El poroto seco no se come crudo (hace mal) ni se mete en la boca, la nariz ni los oídos. El algodón tampoco se come. Usá un vaso de plástico, no de vidrio. Lavate las manos después. Si aparece pelusa blanca o verde (moho), no la toques: avisale al adulto para que tire todo.",
  "misiones.m.huerta_poroto.materiales": ["1 o 2 porotos secos, de los de cocina","Un vaso de plástico transparente","Algodón","Un poco de agua","Un lugar con luz, cerca de una ventana"],
  "misiones.m.huerta_poroto.pasos": ["Mojá el algodón con un poquito de agua y apretalo: tiene que quedar húmedo, no chorreando.","Poné el algodón en el vaso, apretadito contra las paredes.","Metele el poroto entre el algodón y el vaso, para poder verlo desde afuera.","Poné el vaso cerca de una ventana. Cada día, fijate si el algodón sigue húmedo y agregale una cucharadita de agua si hace falta.","Mirá el poroto todos los días y dibujá lo que ves. Cuando aparezca algo nuevo, volvé a la app a contarlo."],
  "misiones.m.huerta_poroto.prediccion.pregunta": "¿Qué creés que va a pasar? ¿Qué va a salir primero del poroto?",
  "misiones.m.huerta_poroto.prediccion.opciones": ["Una hojita","Una raicita","No va a salir nada"],
  "misiones.m.huerta_poroto.observacion": ["Salió primero una raicita","Salió primero una hojita","Todavía no pasó nada"],
  "misiones.m.huerta_poroto.guia": "Preguntale: ¿hacia dónde crece la raicita? ¿Qué creés que necesita el poroto para despertar?",
  "misiones.m.huerta_poroto.explicacion": "Adentro de la semilla ya hay una plantita chiquita y su comida. Con agua y una temperatura agradable, la semilla se hincha y se despierta; eso se llama germinar. Lo primero que sale es la raíz, que sirve para agarrarse y tomar agua; después sale el tallito con las hojas. Para despertar, el poroto no necesita luz; cuando ya tiene hojitas, sí la necesita para crecer.",

  "misiones.m.huerta_bichitos.nombre": "Safari de bichitos",
  "misiones.m.huerta_bichitos.resumen": "Salí a buscar bichitos al jardín y mirá cómo son, sin tocarlos.",
  "misiones.m.huerta_bichitos.aviso": "Mirá con los ojos, sin tocar. No toques bichos, nidos ni telarañas, y no levantes piedras ni macetas sin un adulto: abajo puede haber bichos que pican. Si algo te pica, avisale al adulto enseguida. Usá gorrita y zapatos cerrados, y lavate las manos al volver.",
  "misiones.m.huerta_bichitos.materiales": ["Un patio, una plaza o un jardín","Un cuaderno y un lápiz (o el adulto anota)","Una gorrita y zapatos cerrados","Un adulto que camine con vos"],
  "misiones.m.huerta_bichitos.pasos": ["Caminá despacito por el jardín con el adulto.","Mirá las hojas, la tierra, las flores y las paredes. Los bichitos se esconden.","Cuando veas uno, quedate quieto y mirá: ¿cuántas patas tiene? ¿De qué color es? ¿Qué está haciendo?","Dibujalo en el cuaderno o contáselo al adulto.","Contá cuántos bichitos distintos encontraste."],
  "misiones.m.huerta_bichitos.prediccion.pregunta": "¿Qué creés que va a pasar? ¿Cuántos bichitos vas a encontrar?",
  "misiones.m.huerta_bichitos.prediccion.opciones": ["Muchos","Pocos","Casi ninguno"],
  "misiones.m.huerta_bichitos.observacion": ["Encontré muchos","Encontré pocos","No encontré casi ninguno"],
  "misiones.m.huerta_bichitos.guia": "Preguntale: ¿en qué lugares había más bichitos? ¿Qué creés que hacían ahí?",
  "misiones.m.huerta_bichitos.explicacion": "Los bichitos viven donde encuentran comida, humedad y un lugar para esconderse; por eso es más fácil verlos entre las hojas, en la tierra húmeda y sobre las plantas. Cada tipo de bichito elige su lugar, y en distintos momentos del día o del año se ven bichitos distintos.",

  "misiones.m.arte_colores.nombre": "Mezclar colores con agua",
  "misiones.m.arte_colores.resumen": "Mezclá agua de colores y descubrí qué colores nuevos salen.",
  "misiones.m.arte_colores.aviso": "El colorante mancha la ropa y las manos: poné delantal y mantel de plástico. El agua de colores no es para tomar, aunque parezca jugo. Usá vasos de plástico y lavate las manos al terminar.",
  "misiones.m.arte_colores.materiales": ["3 vasos de plástico transparentes con agua","Colorante comestible rojo, azul y amarillo","3 vasos de plástico vacíos para mezclar","Una cuchara","Un mantel de plástico y un delantal"],
  "misiones.m.arte_colores.pasos": ["Poné agua en tres vasos y unas gotitas de colorante en cada uno: rojo, azul y amarillo. Pedile ayuda al adulto con las gotitas.","Mirá los tres colores. Pensá: ¿qué va a salir si juntamos amarillo con azul?","Volcá un poquito de amarillo y un poquito de azul en un vaso vacío. Mezclá con la cuchara.","Probá otras mezclas en vasos nuevos: rojo con amarillo, y rojo con azul. Fijate qué sale.","Probá poner más de un color que del otro. ¿Cambia el resultado?"],
  "misiones.m.arte_colores.prediccion.pregunta": "¿Qué creés que va a pasar? ¿Qué color sale si juntamos amarillo con azul?",
  "misiones.m.arte_colores.prediccion.opciones": ["Verde","Naranja","Violeta","Marrón"],
  "misiones.m.arte_colores.observacion": ["Salió verde","Salió naranja","Salió violeta","Salió marrón","Salió otro color"],
  "misiones.m.arte_colores.guia": "Preguntale: ¿qué pasó cuando pusiste más de un color? ¿Qué otros colores te gustaría inventar?",
  "misiones.m.arte_colores.explicacion": "Cada colorante deja pasar su propio color de luz y frena los demás. Al juntar dos, solo pasa el color que los dos dejan pasar: amarillo con azul da verde, rojo con amarillo da naranja y rojo con azul da violeta. Si ponés más cantidad de un color, el resultado se parece más a ese. Si juntás los tres, queda un color oscuro.",

  "misiones.m.arte_dibujo_secreto.nombre": "Dibujo secreto",
  "misiones.m.arte_dibujo_secreto.resumen": "Dibujá con crayón blanco y descubrí tu dibujo con pintura.",
  "misiones.m.arte_dibujo_secreto.aviso": "La pintura no se come ni se prueba. Usá témperas o acuarelas que digan “no tóxico”. Poné delantal y mantel, y lavate las manos al terminar.",
  "misiones.m.arte_dibujo_secreto.materiales": ["Una hoja blanca","Un crayón de cera blanco (o de un color muy clarito)","Acuarelas o témpera aguada","Un pincel o una esponjita","Un vaso con agua","Un mantel y un delantal"],
  "misiones.m.arte_dibujo_secreto.pasos": ["Con el crayón blanco, dibujá algo bien fuerte sobre la hoja blanca: una estrella, tu nombre, un animal. Apretá bien.","Mojá el pincel y pintá toda la hoja con un color, de lado a lado.","Mirá qué pasa con tu dibujo secreto."],
  "misiones.m.arte_dibujo_secreto.prediccion.pregunta": "Vas a dibujar con crayón blanco y después pintar toda la hoja. ¿Qué creés que va a pasar?",
  "misiones.m.arte_dibujo_secreto.prediccion.opciones": ["Se va a ver mi dibujo","No se va a ver nada","Se va a mezclar con la pintura"],
  "misiones.m.arte_dibujo_secreto.observacion": ["Apareció mi dibujo","No apareció nada","Pasó otra cosa"],
  "misiones.m.arte_dibujo_secreto.guia": "Preguntale: ¿dónde se pegó la pintura y dónde no? ¿Qué otras cosas creés que no se mojan?",
  "misiones.m.arte_dibujo_secreto.explicacion": "El crayón está hecho de cera, y la cera rechaza el agua: la pintura con agua resbala donde hay cera y se pega en el papel limpio. Por eso el dibujo aparece, como un mensaje secreto.",

  "misiones.m.hogar_medias.nombre": "Pares de medias",
  "misiones.m.hogar_medias.resumen": "Buscá las parejas de un montón de medias y contá los pares.",
  "misiones.m.hogar_medias.aviso": "Usá solo ropa limpia y seca. Si encontrás algo que no es ropa (monedas, cositas chiquitas), no lo agarres: avisale al adulto. Fijate que no haya nada en el piso donde caminás.",
  "misiones.m.hogar_medias.materiales": ["Un montón de medias limpias y mezcladas (unas 10 o 12)","Un lugar plano, como la cama o el piso","Una canasta o un cajón para guardar los pares"],
  "misiones.m.hogar_medias.pasos": ["Desparramá las medias sobre la cama o el piso.","Agarrá una media y buscá su pareja: tiene que ser igual.","Juntá cada par y doblalos juntos.","Contá cuántos pares armaste. ¿Sobró alguna media sin pareja?","Guardá los pares en su lugar."],
  "misiones.m.hogar_medias.imaginar": "Antes de empezar, pensá: ¿cuántos pares de medias creés que hay?",

  "misiones.m.hogar_mesa.nombre": "Poner la mesa",
  "misiones.m.hogar_mesa.resumen": "Poné la mesa para toda la familia: un plato, un vaso y cubiertos para cada uno.",
  "misiones.m.hogar_mesa.aviso": "Llevá las cosas de a una o dos, caminando despacio. Usá platos y vasos de plástico o irrompibles. Si algo se cae o se rompe, no lo toques: llamá al adulto. Si algo se derrama, secalo para que nadie se resbale.",
  "misiones.m.hogar_mesa.materiales": ["Un plato, un vaso, una cuchara y un tenedor por cada persona que come","Servilletas","Una mesa libre"],
  "misiones.m.hogar_mesa.pasos": ["Contá cuántas personas van a comer. Eso te dice cuántos platos necesitás.","Poné un plato adelante de cada silla.","Poné la cuchara, el tenedor y un vaso en cada lugar.","Poné una servilleta en cada lugar.","Fijate: ¿hay un plato, un vaso y cubiertos para cada uno? Contá de nuevo para comprobar."],
  "misiones.m.hogar_mesa.imaginar": "Antes de empezar, pensá: ¿cuántos platos vas a necesitar?",
});

Gioval.i18n.agregar("en", {

  "misiones.ui.isla.nombre": "Missions Island",
  "misiones.ui.isla.sub": "Real things!",
  "misiones.ui.isla.etiqueta_tiempo": "🌿 No screen limit",
  "misiones.ui.isla.habla_menu": "Missions! These are real things to do away from the screen, with a grown-up. What shall we do?",

  "misiones.ui.tarjetas.semana": "Mission of the week",
  "misiones.ui.tarjetas.semana_sub": "Picked for this week",
  "misiones.ui.tarjetas.elegir": "Pick a mission",
  "misiones.ui.tarjetas.elegir_sub": "Building, experiments, cooking…",
  "misiones.ui.tarjetas.album": "My album",
  "misiones.ui.tarjetas.album_sub0": "Your memories will go here",
  "misiones.ui.tarjetas.album_sub": "{n, plural, one{# memory} other{# memories}}",
  "misiones.ui.tarjetas.pendiente": "Take a look: {nombre}",
  "misiones.ui.tarjetas.pendiente_sub": "{dias, plural, =0{You started today} =1{You started yesterday} other{You started # days ago}}",

  "misiones.ui.lista.titulo": "🧭 Pick a mission",
  "misiones.ui.lista.todas": "All",
  "misiones.ui.lista.volver": "Back",
  "misiones.ui.lista.desde": "From age {n}",
  "misiones.ui.lista.hecha": "{n, plural, one{Done # time} other{Done # times}}",
  "misiones.ui.lista.semana_tag": "⭐ Of the week",
  "misiones.ui.lista.bloqueada": "🔒 A little older",

  "misiones.ui.supervision.cerca.corto": "👀 With a grown-up nearby",
  "misiones.ui.supervision.cerca.detalle": "A grown-up has to be nearby, watching, in case you need help.",
  "misiones.ui.supervision.junto.corto": "🤝 Only with a grown-up beside you",
  "misiones.ui.supervision.junto.detalle": "This mission is only done with a grown-up beside you, step by step.",

  "misiones.ui.burbuja.listo": "First, the warning: a grown-up reads it.",
  "misiones.ui.burbuja.materiales": "Let's gather the materials.",
  "misiones.ui.burbuja.antes": "Think before you start.",
  "misiones.ui.burbuja.hacer": "Step {i} of {n}.",
  "misiones.ui.burbuja.espera": "All set up!",
  "misiones.ui.burbuja.quepaso": "What happened?",
  "misiones.ui.burbuja.porque": "Why do you think?",
  "misiones.ui.burbuja.registro": "Let's save the memory.",
  "misiones.ui.burbuja.fin": "Mission saved!",

  "misiones.ui.listo.aviso": "⚠️ Before we start",
  "misiones.ui.listo.adulto": "✅ A grown-up is with me. Ready!",
  "misiones.ui.listo.volver": "Back",
  "misiones.ui.listo.habla": "{nombre}. {resumen} Before we start, a grown-up needs to hear this. {aviso}",

  "misiones.ui.materiales.titulo": "🧺 Let's gather the materials",
  "misiones.ui.materiales.ayuda": "Tap each thing when you have it.",
  "misiones.ui.materiales.todo": "I have everything ➜",
  "misiones.ui.materiales.falta": "I'm missing something",
  "misiones.ui.materiales.falta_habla": "That's okay. When you have everything, we'll do the mission.",
  "misiones.ui.materiales.habla": "Let's gather the materials. Tap each thing when you have it.",

  "misiones.ui.antes.titulo": "🤔 Before we start",
  "misiones.ui.antes.otra": "💬 Another idea (I say it out loud)",
  "misiones.ui.antes.nose": "🤷 I don't know",
  "misiones.ui.antes.otra_puesta": "Another idea (said out loud)",
  "misiones.ui.antes.nose_texto": "I didn't know",
  "misiones.ui.antes.escribir": "Write or dictate your idea (optional)",
  "misiones.ui.antes.seguir": "Next ➜",

  "misiones.ui.hacer.paso": "Step {i} of {n}",
  "misiones.ui.hacer.anterior": "⬅ Back",
  "misiones.ui.hacer.siguiente": "Next ➜",
  "misiones.ui.hacer.ultimo": "✅ I did it!",

  "misiones.ui.timer.poner": "⏱ Set the timer ({min} min)",
  "misiones.ui.timer.cancelar": "Cancel the timer",
  "misiones.ui.timer.corre": "⏱ Time left: {tiempo}",
  "misiones.ui.timer.fin": "Time's up! Look at what happened.",
  "misiones.ui.timer.titulo": "Mundo Gioval · Mission",
  "misiones.ui.timer.texto": "Your mission's time is up!",

  "misiones.ui.espera.titulo": "🌱 All set up!",
  "misiones.ui.espera.texto": "Now we have to wait. Come back and look in {dias, plural, one{# day} other{about # days}} and tell what happened. You'll find it on Missions Island.",
  "misiones.ui.espera.guardar": "Save and look later",
  "misiones.ui.espera.habla": "All set up! Now we have to wait. Come back and look in {dias, plural, one{# day} other{about # days}}.",
  "misiones.ui.espera.despedida": "Saved. Come back and look in a few days!",

  "misiones.ui.que_paso.titulo": "👀 What happened?",
  "misiones.ui.que_paso.habla": "What happened? Look closely and pick what you saw.",
  "misiones.ui.que_paso.otra": "Something else happened",
  "misiones.ui.que_paso.pensabas": "You had thought:",
  "misiones.ui.que_paso.seguir": "Next ➜",

  "misiones.ui.porque.titulo": "💡 Why do you think it happened?",
  "misiones.ui.porque.habla": "Why do you think it happened? Think about it and tell the grown-up. There is no single answer: what matters is thinking.",
  "misiones.ui.porque.escribir": "Write or dictate your idea (optional)",
  "misiones.ui.porque.ver": "👨‍👩‍👦 See the explanation",
  "misiones.ui.porque.ocultar": "Hide the explanation",
  "misiones.ui.porque.para_adulto": "For the grown-up: read it and explain it in your own words",
  "misiones.ui.porque.guia": "Questions to ask:",
  "misiones.ui.porque.seguir": "Next ➜",

  "misiones.ui.registro.titulo": "📖 Let's save the memory",
  "misiones.ui.registro.habla": "Let's save the memory. Tell in your own words what you did, and pick whether it turned out as you thought or different.",
  "misiones.ui.registro.frase": "My sentence",
  "misiones.ui.registro.frase_ph": "Write or dictate what you want to remember",
  "misiones.ui.registro.pensaba": "✅ It turned out as I thought",
  "misiones.ui.registro.distinto": "🔄 It turned out different",
  "misiones.ui.registro.elegi": "Pick one of the two",
  "misiones.ui.registro.guardar": "📖 Save in my album",
  "misiones.ui.registro.dictar": "🎤 Dictate",
  "misiones.ui.registro.escuchando": "🎤 Listening…",
  "misiones.ui.registro.sin_frase": "(no sentence)",

  "misiones.ui.adulto.resumen": "👨‍👩‍👦 For the grown-up",
  "misiones.ui.adulto.foto": "Save a photo on this device (it is not uploaded anywhere, not to the internet or the cloud)",
  "misiones.ui.adulto.foto_off": "To take a photo, a grown-up has to turn on the permission.",
  "misiones.ui.adulto.dictado": "Voice dictation (the browser may use an internet service to understand what is said)",
  "misiones.ui.adulto.sacar": "📷 Take a photo",
  "misiones.ui.adulto.otra": "📷 Take another",
  "misiones.ui.adulto.quitar": "✖ Remove the photo",
  "misiones.ui.adulto.sin_almacen": "This device cannot save photos. The memory is saved without a photo.",
  "misiones.ui.adulto.foto_error": "I could not save the photo. The memory was saved without a photo.",
  "misiones.ui.adulto.lectura_error": "I could not read that photo. Try another one.",

  "misiones.ui.fin.titulo": "Mission saved!",
  "misiones.ui.fin.mas": "🧭 More missions",
  "misiones.ui.fin.album": "📖 See my album",
  "misiones.ui.fin.isla": "🏝️ To the island",
  "misiones.ui.fin.predijo": ["You said what you thought before trying.","You came up with an idea before starting."],
  "misiones.ui.fin.miro": ["You looked closely at what was happening.","You observed carefully."],
  "misiones.ui.fin.conto": ["You told it in your own words.","You put into words what you saw."],
  "misiones.ui.fin.foto": ["You saved a photo of your work."],
  "misiones.ui.fin.pensaba": ["What you thought was close to what happened."],
  "misiones.ui.fin.distinto": ["It turned out different from what you thought, and that is useful too: now you know something new."],
  "misiones.ui.fin.hacer": ["You did it step by step.","You followed the steps with patience."],
  "misiones.ui.fin.cierre": ["It's saved in your album!"],

  "misiones.ui.album.titulo": "📖 My album",
  "misiones.ui.album.vacio": "There are no memories yet. When you finish a mission, it will show up here.",
  "misiones.ui.album.volver": "Back",
  "misiones.ui.album.adultos": "🔒 For grown-ups",
  "misiones.ui.album.nino": "👦 Back to the child's view",
  "misiones.ui.album.info_adulto": "Grown-up view. Everything stays only on this device and goes into the backup (⚙️ → Export backup).",
  "misiones.ui.album.pensaba": "✅ It turned out as I thought",
  "misiones.ui.album.distinto": "🔄 It turned out different",
  "misiones.ui.album.predijo": "I thought:",
  "misiones.ui.album.paso": "What happened:",
  "misiones.ui.album.porque": "Why:",
  "misiones.ui.album.sin_foto": "📷 The photo is not on this device",
  "misiones.ui.album.borrar": "🗑 Delete the memory",
  "misiones.ui.album.borrar_foto": "🗑 Delete only the photo",
  "misiones.ui.album.confirma_recuerdo": "Delete this memory and its photo? This cannot be undone.",
  "misiones.ui.album.confirma_foto": "Delete only the photo? The memory stays without a photo. This cannot be undone.",
  "misiones.ui.album.si": "Yes, delete",
  "misiones.ui.album.no": "No",

  "misiones.ui.panel.titulo": "🧭 Missions",
  "misiones.ui.panel.edad": "Age of {nombre}:",
  "misiones.ui.panel.anos": "{n, plural, one{# year old} other{# years old}}",
  "misiones.ui.panel.semana": "Mission of the week:",
  "misiones.ui.panel.auto": "Automatic (by age)",
  "misiones.ui.panel.album": "📖 Album (grown-ups)",
  "misiones.ui.panel.sin_perfil": "First pick who is playing.",

  "misiones.cat.construir": "Building",

  "misiones.cat.experimentos": "Experiments",

  "misiones.cat.cocina": "Cooking",

  "misiones.cat.huerta": "Garden",

  "misiones.cat.arte": "Art",

  "misiones.cat.hogar": "Home",

  "misiones.m.construir_puente.nombre": "Paper bridge",
  "misiones.m.construir_puente.resumen": "Build a bridge from a sheet of paper and see how much weight it holds.",
  "misiones.m.construir_puente.aviso": "Do it on the floor or a low table and use small books: if one falls, it can hurt a foot. Coins and tiny things do not go in the mouth.",
  "misiones.m.construir_puente.materiales": ["2 books or boxes of the same height","2 identical sheets of paper","Light toy cars or blocks to put on top (or coins, if you already know they do not go in the mouth)","A flat place, the floor is best"],
  "misiones.m.construir_puente.pasos": ["Stand the two books up, with a gap in the middle about one hand wide.","Lay a flat sheet across the two books, like a bridge.","Put the little cars on the bridge one at a time. Count how many it holds before it sags a lot.","Now fold the other sheet like an accordion, with folds as wide as a finger.","Lay it down as a bridge and put the little cars on one at a time. How many does it hold now?"],
  "misiones.m.construir_puente.prediccion.pregunta": "What do you think will happen? Which bridge will hold more cars?",
  "misiones.m.construir_puente.prediccion.opciones": ["The flat one","The folded one","Both the same"],
  "misiones.m.construir_puente.observacion": ["The flat one held more","The folded one held more","They held the same"],
  "misiones.m.construir_puente.guia": "Ask: what changed between one sheet and the other? Where did the flat bridge bend?",
  "misiones.m.construir_puente.explicacion": "With folds, the same sheet becomes much stiffer: paper folded like an accordion bends less than flat paper, so it holds more weight with the same paper. This idea is used in corrugated metal roofs and in the corrugated cardboard of boxes.",

  "misiones.m.construir_casita.nombre": "Cardboard house",
  "misiones.m.construir_casita.resumen": "Build a little house or a garage for a toy figure with cardboard boxes.",
  "misiones.m.construir_casita.aviso": "Run your hand over the boxes to check for edges that scratch or staple points; if there are any, the grown-up covers them with tape or swaps the box. Do not use boxes that held cleaning products.",
  "misiones.m.construir_casita.materiales": ["3 or 4 small, clean cardboard boxes (cereal, cookie or shoe boxes)","Masking tape, in strips that the grown-up tears off","A toy figure or a little car to live or park inside","Markers to decorate"],
  "misiones.m.construir_casita.pasos": ["Look at the boxes and think: which one goes at the bottom? Which one goes on top?","Stack the boxes to build the little house. Try different ways until it stands firm.","Join them with the strips of tape the grown-up gave you.","Decorate it with markers: doors, windows, a roof.","Put the toy figure inside. Does it fit? If not, what would you change?"],
  "misiones.m.construir_casita.imaginar": "Before you start, imagine: what will your little house be like?",

  "misiones.m.exp_flota.nombre": "Does it float or sink?",
  "misiones.m.exp_flota.resumen": "Guess which things float in water and which sink, and then try it.",
  "misiones.m.exp_flota.aviso": "Use a basin or a bucket with a little water, on the floor with a towel. If it spills, dry it right away so nobody slips. The water is not for drinking. Tiny things do not go in the mouth.",
  "misiones.m.exp_flota.materiales": ["A basin or a bucket with water up to halfway","A towel","4 things to try: for example a cork, a tree leaf, a small stone and a coin"],
  "misiones.m.exp_flota.pasos": ["Line the things up on the towel.","Before trying, point to which ones you think float and which ones sink.","Put one thing at a time in the water, slowly.","Look closely at what happens. Does it float? Does it sink? Does it sink fast or slowly?","Take everything out of the water with your hands and dry what got wet."],
  "misiones.m.exp_flota.prediccion.pregunta": "What do you think will happen? What will happen with your things?",
  "misiones.m.exp_flota.prediccion.opciones": ["All of them float","Some float and some sink","All of them sink"],
  "misiones.m.exp_flota.observacion": ["All of them floated","Some floated and some sank","All of them sank"],
  "misiones.m.exp_flota.guia": "Ask: what do the ones that floated have in common? And the ones that sank?",
  "misiones.m.exp_flota.explicacion": "Something floats when it is light for its size; for example, a cork has lots of tiny pockets of air inside. It sinks when it is heavy for its size, like a stone or a metal coin. It does not depend only on how heavy it is: a huge metal ship floats because it has a lot of space with air inside.",

  "misiones.m.exp_hielo.nombre": "Ice in the sun or in the shade",
  "misiones.m.exp_hielo.resumen": "Put two ice cubes out, one in the sun and one in the shade, and see which one melts faster.",
  "misiones.m.exp_hielo.aviso": "Never look straight at the sun and wear a hat. Ice is very cold: do not put it in your mouth (it can make you choke) and do not hold it for long. Dry up any water that spills.",
  "misiones.m.exp_hielo.materiales": ["2 ice cubes of the same size (the grown-up takes them out of the freezer)","2 identical small plates","A sunny spot and a shady spot, close to each other","A timer (the app sets it up for you)"],
  "misiones.m.exp_hielo.pasos": ["Ask the grown-up to take out two ice cubes and put them on the small plates.","Put one plate in the sun and the other in the shade. Both at the same time.","Tap the timer button and wait. Meanwhile, watch how the cubes change.","When it rings, look at which one melted more. How much water is on each plate?","Take the plates inside and pour the water down the sink."],
  "misiones.m.exp_hielo.prediccion.pregunta": "What do you think will happen? Which cube will melt faster?",
  "misiones.m.exp_hielo.prediccion.opciones": ["The one in the sun","The one in the shade","Both the same"],
  "misiones.m.exp_hielo.observacion": ["The one in the sun melted more","The one in the shade melted more","They melted the same"],
  "misiones.m.exp_hielo.guia": "Ask: what does the sun give to the ice? What would happen if we left it inside the freezer?",
  "misiones.m.exp_hielo.explicacion": "Ice melts when it gets heat. Much more heat reaches the sun than the shade, because sunlight gives energy to everything it touches; that is why the cube in the sun melts faster. In the shade it melts too, because the air around it is warmer than the ice, but more slowly. On a very cold day, both would take much longer.",

  "misiones.m.cocina_plastilina.nombre": "Homemade play dough",
  "misiones.m.cocina_plastilina.resumen": "Make modeling dough with flour, salt and cold water.",
  "misiones.m.cocina_plastilina.aviso": "Only with a grown-up beside you. This dough is not for eating: it has lots of salt. It has wheat flour: if anyone has an allergy or celiac disease, ask the grown-up first. Food coloring stains: wear an apron and use a tablecloth. Wash your hands before and after, and do not put them in your mouth.",
  "misiones.m.cocina_plastilina.materiales": ["2 cups of plain flour","1 cup of fine salt","1 cup of cold tap water (add it little by little)","2 spoonfuls of oil","Food coloring (a few drops)","A big bowl and a spoon","A tray or a plastic tablecloth"],
  "misiones.m.cocina_plastilina.pasos": ["Put the flour and the salt in the bowl and mix them with the spoon.","Add the oil and a few drops of coloring.","Pour in the water little by little, a small splash at a time, and keep mixing. Notice how the dough changes.","When it all comes together, knead it with your hands on the tray. If it is sticky, add a pinch of flour; if it is hard, a few drops of water.","Model whatever you like! A little bug, a letter, your name.","When you finish, keep the dough in a jar or a tightly closed bag and wash your hands."],
  "misiones.m.cocina_plastilina.imaginar": "Before you start, think: how do you think the dough will feel when it is ready?",

  "misiones.m.cocina_vasitos.nombre": "Yogurt and fruit cups",
  "misiones.m.cocina_vasitos.resumen": "Make a cup with layers of yogurt and fruit.",
  "misiones.m.cocina_vasitos.aviso": "Only with a grown-up beside you. First, the grown-up has to check whether anyone is allergic to any of these foods. Wash your hands with soap and water. The fruit has to be in tiny pieces, prepared by the grown-up, so nobody chokes. Nothing is eaten until the cup is finished.",
  "misiones.m.cocina_vasitos.materiales": ["Yogurt","2 or 3 washed fruits, in tiny pieces prepared by the grown-up (banana, strawberry, peach)","Breakfast cereal (if you like)","Clear cups","Spoons"],
  "misiones.m.cocina_vasitos.pasos": ["Wash your hands with soap and water.","Put a layer of yogurt at the bottom of the cup, with the spoon.","Add a layer of fruit. Then another of yogurt. Notice how the layers look through the cup.","Finish with cereal or a strawberry on top.","Eat it slowly, sitting down and with the grown-up nearby!"],
  "misiones.m.cocina_vasitos.imaginar": "Before you start, imagine: how many layers will your cup have?",

  "misiones.m.huerta_poroto.nombre": "A bean that wakes up",
  "misiones.m.huerta_poroto.resumen": "Put a bean in a cup with damp cotton and watch what happens to it over a few days.",
  "misiones.m.huerta_poroto.aviso": "A dry bean is not eaten raw (it makes you sick) and does not go in the mouth, nose or ears. The cotton is not eaten either. Use a plastic cup, not a glass one. Wash your hands afterwards. If white or green fuzz appears (mold), do not touch it: tell the grown-up so they throw everything away.",
  "misiones.m.huerta_poroto.materiales": ["1 or 2 dry beans, the kind used for cooking","A clear plastic cup","Cotton","A little water","A spot with light, near a window"],
  "misiones.m.huerta_poroto.pasos": ["Wet the cotton with a little water and squeeze it: it should be damp, not dripping.","Put the cotton in the cup, packed snugly against the walls.","Slip the bean between the cotton and the cup, so you can see it from outside.","Put the cup near a window. Every day, check whether the cotton is still damp and add a teaspoon of water if needed.","Look at the bean every day and draw what you see. When something new appears, come back to the app to tell about it."],
  "misiones.m.huerta_poroto.prediccion.pregunta": "What do you think will happen? What will come out of the bean first?",
  "misiones.m.huerta_poroto.prediccion.opciones": ["A little leaf","A little root","Nothing will come out"],
  "misiones.m.huerta_poroto.observacion": ["A little root came out first","A little leaf came out first","Nothing has happened yet"],
  "misiones.m.huerta_poroto.guia": "Ask: which way is the little root growing? What do you think the bean needs to wake up?",
  "misiones.m.huerta_poroto.explicacion": "Inside the seed there is already a tiny plant and its food. With water and a pleasant temperature, the seed swells and wakes up; this is called germinating. The root comes out first, to hold on and take in water; then the little stem with leaves comes out. To wake up, the bean does not need light; once it has little leaves, it does need light to grow.",

  "misiones.m.huerta_bichitos.nombre": "Bug safari",
  "misiones.m.huerta_bichitos.resumen": "Go out to look for little bugs in the garden and see what they are like, without touching them.",
  "misiones.m.huerta_bichitos.aviso": "Look with your eyes, without touching. Do not touch bugs, nests or spiderwebs, and do not lift stones or flowerpots without a grown-up: underneath there may be bugs that sting. If something stings you, tell the grown-up right away. Wear a hat and closed shoes, and wash your hands when you come back.",
  "misiones.m.huerta_bichitos.materiales": ["A yard, a park or a garden","A notebook and a pencil (or the grown-up writes)","A hat and closed shoes","A grown-up who walks with you"],
  "misiones.m.huerta_bichitos.pasos": ["Walk slowly through the garden with the grown-up.","Look at the leaves, the soil, the flowers and the walls. Little bugs hide.","When you see one, stay still and look: how many legs does it have? What color is it? What is it doing?","Draw it in the notebook or tell the grown-up about it.","Count how many different bugs you found."],
  "misiones.m.huerta_bichitos.prediccion.pregunta": "What do you think will happen? How many little bugs will you find?",
  "misiones.m.huerta_bichitos.prediccion.opciones": ["Lots","A few","Almost none"],
  "misiones.m.huerta_bichitos.observacion": ["I found lots","I found a few","I found almost none"],
  "misiones.m.huerta_bichitos.guia": "Ask: in which places were there more little bugs? What do you think they were doing there?",
  "misiones.m.huerta_bichitos.explicacion": "Little bugs live where they find food, moisture and a place to hide; that is why it is easier to see them among leaves, in damp soil and on plants. Each kind of bug picks its own place, and at different times of day or year you see different bugs.",

  "misiones.m.arte_colores.nombre": "Mixing colored water",
  "misiones.m.arte_colores.resumen": "Mix colored water and discover which new colors come out.",
  "misiones.m.arte_colores.aviso": "Food coloring stains clothes and hands: wear an apron and a plastic tablecloth. The colored water is not for drinking, even if it looks like juice. Use plastic cups and wash your hands when you finish.",
  "misiones.m.arte_colores.materiales": ["3 clear plastic cups with water","Red, blue and yellow food coloring","3 empty plastic cups for mixing","A spoon","A plastic tablecloth and an apron"],
  "misiones.m.arte_colores.pasos": ["Put water in three cups and a few drops of coloring in each one: red, blue and yellow. Ask the grown-up to help with the drops.","Look at the three colors. Think: what will come out if we mix yellow with blue?","Pour a little yellow and a little blue into an empty cup. Stir with the spoon.","Try other mixes in new cups: red with yellow, and red with blue. Notice what comes out.","Try putting more of one color than the other. Does the result change?"],
  "misiones.m.arte_colores.prediccion.pregunta": "What do you think will happen? What color comes out if we mix yellow with blue?",
  "misiones.m.arte_colores.prediccion.opciones": ["Green","Orange","Purple","Brown"],
  "misiones.m.arte_colores.observacion": ["Green came out","Orange came out","Purple came out","Brown came out","Another color came out"],
  "misiones.m.arte_colores.guia": "Ask: what happened when you put more of one color? Which other colors would you like to invent?",
  "misiones.m.arte_colores.explicacion": "Each coloring lets its own color of light through and blocks the others. When you mix two, only the color that both let through gets by: yellow with blue makes green, red with yellow makes orange and red with blue makes purple. If you add more of one color, the result looks more like that one. If you mix all three, you get a dark color.",

  "misiones.m.arte_dibujo_secreto.nombre": "Secret drawing",
  "misiones.m.arte_dibujo_secreto.resumen": "Draw with a white crayon and reveal your drawing with paint.",
  "misiones.m.arte_dibujo_secreto.aviso": "Paint is not for eating or tasting. Use paints that say “non-toxic”. Wear an apron and a tablecloth, and wash your hands when you finish.",
  "misiones.m.arte_dibujo_secreto.materiales": ["A white sheet of paper","A white wax crayon (or a very light color)","Watercolors or watered-down poster paint","A brush or a little sponge","A cup of water","A tablecloth and an apron"],
  "misiones.m.arte_dibujo_secreto.pasos": ["With the white crayon, draw something nice and strong on the white sheet: a star, your name, an animal. Press hard.","Wet the brush and paint the whole sheet with one color, from side to side.","Look at what happens to your secret drawing."],
  "misiones.m.arte_dibujo_secreto.prediccion.pregunta": "You will draw with a white crayon and then paint the whole sheet. What do you think will happen?",
  "misiones.m.arte_dibujo_secreto.prediccion.opciones": ["My drawing will show","Nothing will show","It will mix with the paint"],
  "misiones.m.arte_dibujo_secreto.observacion": ["My drawing appeared","Nothing appeared","Something else happened"],
  "misiones.m.arte_dibujo_secreto.guia": "Ask: where did the paint stick and where did it not? What other things do you think do not get wet?",
  "misiones.m.arte_dibujo_secreto.explicacion": "The crayon is made of wax, and wax pushes water away: the watery paint slides off where there is wax and sticks to the clean paper. That is why the drawing appears, like a secret message.",

  "misiones.m.hogar_medias.nombre": "Pairs of socks",
  "misiones.m.hogar_medias.resumen": "Find the matching pairs in a pile of socks and count the pairs.",
  "misiones.m.hogar_medias.aviso": "Use only clean, dry clothes. If you find something that is not clothing (coins, tiny things), do not pick it up: tell the grown-up. Make sure nothing is on the floor where you walk.",
  "misiones.m.hogar_medias.materiales": ["A pile of clean, mixed-up socks (about 10 or 12)","A flat place, like the bed or the floor","A basket or a drawer to keep the pairs"],
  "misiones.m.hogar_medias.pasos": ["Spread the socks out on the bed or the floor.","Pick up a sock and look for its partner: it has to be the same.","Put each pair together and fold them together.","Count how many pairs you made. Is there a sock left over without a partner?","Put the pairs away in their place."],
  "misiones.m.hogar_medias.imaginar": "Before you start, think: how many pairs of socks do you think there are?",

  "misiones.m.hogar_mesa.nombre": "Setting the table",
  "misiones.m.hogar_mesa.resumen": "Set the table for the whole family: a plate, a cup and cutlery for each person.",
  "misiones.m.hogar_mesa.aviso": "Carry things one or two at a time, walking slowly. Use plastic or unbreakable plates and cups. If something falls or breaks, do not touch it: call the grown-up. If something spills, dry it so nobody slips.",
  "misiones.m.hogar_mesa.materiales": ["A plate, a cup, a spoon and a fork for each person who eats","Napkins","A free table"],
  "misiones.m.hogar_mesa.pasos": ["Count how many people will eat. That tells you how many plates you need.","Put a plate in front of each chair.","Put the spoon, the fork and a cup at each place.","Put a napkin at each place.","Check: is there a plate, a cup and cutlery for everyone? Count again to be sure."],
  "misiones.m.hogar_mesa.imaginar": "Before you start, think: how many plates will you need?",
});

const CATEGORIAS = ["construir", "experimentos", "cocina", "huerta", "arte", "hogar"];

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

/* Lista equivalente para inglés (se compara en minúsculas, palabra entera). "heat" (calor) se permite, "heating/heated/heater" no. */
const PROHIBIDAS_EN = [
  "fire\\w*", "flame\\w*", "bonfire\\w*", "matchbox\\w*", "matchstick\\w*", "lighter\\w*", "candle\\w*", "stove\\w*", "oven\\w*", "microwave\\w*", "iron", "burn\\w*", "boil\\w*", "hot", "heater\\w*", "heated", "heating", "torch\\w*", "magnifying",
  "knife", "knives", "scissors", "sharp\\w*", "blade\\w*", "razor\\w*", "cutter\\w*", "cut", "cuts", "cutting", "sawing", "hacksaw\\w*", "chainsaw\\w*", "axe", "machete", "hammer\\w*", "drill\\w*", "nail", "nails", "gun", "pistol",
  "bleach", "chlorine", "ammonia", "solvent\\w*", "thinner", "turpentine", "gasoline", "petrol", "kerosene", "acetone", "alcohol", "peroxide", "vinegar", "baking soda", "bicarbonate",
  "disinfectant\\w*", "cleaner\\w*", "degreaser\\w*", "acid\\w*", "caustic", "poison\\w*", "insecticide\\w*", "pesticide\\w*", "herbicide\\w*", "fertilizer\\w*",
  "resin\\w*", "epoxy", "polyester", "fiberglass", "fibreglass", "catalyst\\w*", "superglue", "contact cement",
  "outlet\\w*", "socket\\w*", "electric\\w*", "plug", "plugs", "extension cord\\w*", "charger\\w*", "cable\\w*", "voltage", "mains",
];
const _rx = lista => lista.map(p => new RegExp("(^|[^a-z])(" + p + ")($|[^a-z])"));
const _REGEX_PROHIBIDAS = { es: _rx(PROHIBIDAS), en: _rx(PROHIBIDAS_EN) };
function _norm(s) { return String(s).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }
function _textos(x, out) { if (typeof x === "string") out.push(x); else if (Array.isArray(x)) x.forEach(y => _textos(y, out)); else if (x && typeof x === "object") Object.keys(x).forEach(k => _textos(x[k], out)); return out; }
const _base = codigo => String(codigo).split("-")[0].toLowerCase();
/* palabras prohibidas que aparecen en un texto (lista vacía = limpio). "idioma": "es" (por defecto), "en"… ; si no hay lista para ese idioma devuelve ["(sin lista)"] */
function palabrasProhibidas(texto, idioma) {
  const rs = _REGEX_PROHIBIDAS[_base(idioma || "es")]; if (!rs) return ["(sin lista para " + idioma + ")"];
  const t = _norm(texto), hit = []; rs.forEach(r => { const m = r.exec(t); if (m) hit.push(m[2]); }); return hit;
}

/* ---- textos de una misión en el idioma actual (con la cadena de respaldo), o crudos de una tabla de idioma ---- */
const _I = () => Gioval.i18n;
const _k = id => "misiones.m." + id + ".";
function textos(m) {
  const I = _I(), k = _k(m.id), tiene = s => I.tiene(k + s), T = s => tiene(s) ? I.t(k + s) : "", L = s => tiene(s) ? I.tl(k + s) : [];
  return {
    nombre: T("nombre"), resumen: T("resumen"), aviso: T("aviso"), materiales: L("materiales"), pasos: L("pasos"),
    prediccion: tiene("prediccion.pregunta") ? { pregunta: T("prediccion.pregunta"), opciones: L("prediccion.opciones") } : null,
    observacion: tiene("observacion") ? L("observacion") : null,
    guia: T("guia"), explicacion: T("explicacion"), imaginar: T("imaginar"),
  };
}
/* los valores sin formatear que una tabla de idioma tiene para esa misión: { "nombre": "...", "pasos": [...] } */
function crudos(id, codigo) {
  const tb = _I().tablas[codigo], k = _k(id), out = {}; if (!tb) return out;
  Object.keys(tb.textos).forEach(c => { if (c.startsWith(k)) out[c.slice(k.length)] = tb.textos[c]; });
  return out;
}

/* Una misión solo se muestra si pasa esta revisión (devuelve la lista de problemas; vacía = válida). Revisa es-AR (estructura) y
   las palabras prohibidas en TODOS los idiomas que traigan textos de esa misión. */
function validar(m) {
  const p = [], I = _I();
  if (!m || !m.id) return ["falta el id"];
  const t = crudos(m.id, "es-AR");
  if (!Object.keys(t).length) return ["no tiene textos en es-AR (misiones.m." + m.id + ".*)"];
  const es = I.tablas["es-AR"].textos;
  if (!es["misiones.cat." + m.cat]) p.push("categoría desconocida");
  if (!(m.minEdad >= 4)) p.push("la edad mínima tiene que ser 4 o más");
  if (!es["misiones.ui.supervision." + m.sup + ".corto"]) p.push("falta el nivel de supervisión (cerca o junto)");
  if (!["experimento", "observar", "hacer"].includes(m.tipo)) p.push("tipo desconocido");
  if (!t.nombre) p.push("falta el nombre");
  if (!t.resumen) p.push("falta el resumen");
  if (!t.aviso || String(t.aviso).trim().length < 20) p.push("falta el aviso de seguridad");
  if (!Array.isArray(t.materiales) || !t.materiales.length) p.push("faltan los materiales");
  if (!Array.isArray(t.pasos) || t.pasos.length < 2) p.push("faltan los pasos (mínimo 2)");
  if (m.tipo === "hacer") { if (!t.imaginar) p.push("falta la frase de “imaginá”"); }
  else {
    if (!t["prediccion.pregunta"] || !Array.isArray(t["prediccion.opciones"]) || t["prediccion.opciones"].length < 2) p.push("falta la predicción (pregunta y 2 opciones)");
    if (!Array.isArray(t.observacion) || t.observacion.length < 2) p.push("faltan las opciones de “¿qué pasó?”");
    if (!t.guia) p.push("falta la guía para el adulto");
    if (!t.explicacion && !m.revisar) p.push("falta la explicación (o marcá revisar)");
  }
  if (m.espera && !(m.espera.dias >= 1)) p.push("espera.dias inválido");
  if (m.temporizador && !(m.temporizador.seg > 0 && Array.isArray(t.pasos) && m.temporizador.paso >= 0 && m.temporizador.paso < t.pasos.length)) p.push("temporizador inválido");
  Object.keys(I.tablas).forEach(c => {
    const cr = crudos(m.id, c); if (!Object.keys(cr).length) return;
    _textos(cr, []).forEach(s => { const h = palabrasProhibidas(s, c); if (h.length) p.push("[" + c + "] palabra prohibida «" + h[0] + "» en: " + s.slice(0, 50)); });
  });
  return p;
}

Gioval.datos.misiones = { MISIONES, CATEGORIAS, PROHIBIDAS, PROHIBIDAS_EN, textos, crudos, validar, palabrasProhibidas };
