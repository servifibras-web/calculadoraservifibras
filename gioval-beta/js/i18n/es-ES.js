"use strict";
/* Spanish (Spain): variante del español. Solo trae lo que CAMBIA respecto de es-AR (tuteo en lugar de voseo; "fresa", "galleta", "coche"); el resto cae a es-AR. */
Gioval.i18n.registrar("es-ES", {
  meta: { nombre: "Spanish (Spain)", nombreNativo: "Español (España)", dir: "ltr", locale: "es-ES", moneda: "EUR", voz: ["es-ES", "es-419", "es"], fallback: ["es-AR"] },
  textos: {
    "app.isla_entrada": "¡{isla}! Empezamos con la sesión de hoy, o elige otra cosa.",
    "app.pregunta_nombre": "¿Cómo te llamas?",
    "menu.logros_sub": "Mira todo lo que aprendiste",
    "menu.chequeo_abierto": "Sin ayuda: ¡muestra lo que sabes!",
    "motor.sesion.inicio": "¡Vamos con la sesión de hoy, {nombre}! Son juegos cortos.",
    "motor.chequeo.inicio": "Hoy es el chequeo. No te ayudo: ¡muestra lo que sabes! Si no estás seguro, prueba igual.",
    "motor.fin.chequeo_voz": "¡Terminamos el chequeo, {nombre}! Lo anoté para papá. ¡Gracias por mostrar lo que sabes!",
    "tap.fallo1": ["Mmm, prueba distinto 🤔", "Fíjate de nuevo, despacito.", "¡Casi! Prueba de otra manera."],
    "tap.tip": "Fíjate bien. Te saqué una opción.",
    "tap.reveal": "Mira, es este.",
    "adultos.pregunta_otra": "Prueba de nuevo 🙂 (solo para adultos)",
    "adultos.copiar_manual": "Selecciona y copia",
    "respaldo.recordar": "<br><b>⚠️ Hace más de 14 días que no haces un respaldo.</b> Toca “Exportar respaldo” y guarda el archivo.",
    "respaldo.error_migracion": "<br><b>⚠️ No se pudo actualizar el formato de los datos.</b> Tus datos originales están a salvo; exporta un respaldo y avisa.",
    "almacen.err.futura": "Ese respaldo es de una versión más nueva de la app. Actualiza la app y prueba de nuevo.",
    "voz.nivel_tts_sin_confirmar": "Voz del aparato: todavía no se pudo confirmar cuál se usa. Prueba con el botón.",
    "musica.mic.encendido": "¡Te escucho! Toca tu piano 🎹",
    "musica.mic.error": "No pude usar el micrófono. Puedes tocar el teclado de la pantalla.",
    "musica.frase.primera": "Escucha cómo suena.",
    "musica.frase.siguiente": "Ahora, la siguiente parte. Escucha.",
    "musica.te_toca": "¡Ahora te toca a ti!",
    "musica.completa": "¡Ya sabes todas las partes! Ahora toca la canción completa. ¡Yo te espero!",
    "musica.escucha_otra": "Escucha otra vez.",
    "musica.mira_es": "Mira, es el {nota} 👀",
    "musica.casi_otra": "¡Casi! Prueba otra vez 😊",
    "musica.casi_busca": "¡Casi! Busca el {nota}",
    "musica.casi_proba": "¡Casi! Prueba con el {nota}.",
    "musica.te_ayudo": "Mira, te ayudo. Este es el {nota}.",
    "musica.find": ["Toca el {nota}", "Busca el {nota}", "¿Dónde está el {nota}?"],
    "musica.ear_primera": "Escucha bien y toca la nota que suena.",
    "musica.ear_otra": "Escucha…",
    "musica.echo_primera": "Escucha y repite igualito.",
    "musica.echo_otra": "Escucha…",
    "musica.echo_vos": "¡Ahora tú! 🎹",
    "musica.tarjeta_sub": "Toca tus favoritas",
    "musica.panel.tip": "Tip: pon la tablet sobre el atril, cerca del teclado. Si el teclado digital tiene volumen alto y la sala es silenciosa, funciona mejor.",
    "musica.otra_octava": "¡Es el {nota}, pero de otra octava! Prueba con el {nota} que está cerca del medio 😊",
    "musica.motivo.silenciado": "Ignoré un sonido porque la app estaba hablando o tocando. Espera a que termine y toca de nuevo.",
    "musica.motivo.bajo": "Ignoré un sonido porque es muy suave. Toca más fuerte o sube la sensibilidad.",
    "musica.motivo.suena_anterior": "Ignoré un sonido porque todavía sonaba la nota anterior. Espera a que se apague o toca un poco más fuerte.",
    "musica.motivo.sin_nota": "Escuché un sonido pero no pude saber qué nota era (¿varias teclas juntas o mucho ruido?). Prueba con una sola tecla.",
    "musica.vivo.estado.apagado": "🎤 El micrófono está apagado: toca el 🎤 de arriba.",
    "musica.afin.btn_la": "🎵 Toca un La",
    "musica.afin.esperando": "Toca un La ahora (una sola tecla, bien clara)… te escucho.",
    "musica.afin.no_es_la": "Eso no sonó como un La (escuché {nota}). Prueba de nuevo con el La.",
    "musica.afin.sin_nota": "No pude medir la nota. Toca un La solo, bien fuerte, y deja que suene.",
    "musica.afin.tiempo": "No escuché ningún La. Aprieta el botón y toca de nuevo.",
    "numeros.objetos": {
      "manzana": {
        "one": "manzana",
        "other": "manzanas",
        "g": "f"
      },
      "estrella": {
        "one": "estrella",
        "other": "estrellas",
        "g": "f"
      },
      "auto": {
        "one": "coche",
        "other": "coches",
        "g": "m"
      },
      "pez": {
        "one": "pez",
        "other": "peces",
        "g": "m"
      },
      "flor": {
        "one": "flor",
        "other": "flores",
        "g": "f"
      },
      "globo": {
        "one": "globo",
        "other": "globos",
        "g": "m"
      },
      "perro": {
        "one": "perro",
        "other": "perros",
        "g": "m"
      },
      "frutilla": {
        "one": "fresa",
        "other": "fresas",
        "g": "f"
      },
      "pelota": {
        "one": "pelota",
        "other": "pelotas",
        "g": "f"
      },
      "mariposa": {
        "one": "mariposa",
        "other": "mariposas",
        "g": "f"
      },
      "galletita": {
        "one": "galleta",
        "other": "galletas",
        "g": "f"
      },
      "tortuga": {
        "one": "tortuga",
        "other": "tortugas",
        "g": "f"
      }
    },
    "numeros.count.say_toca": "¿{g, select, f{Cuántas} other{Cuántos}} {objetos} hay? Toca cada dibujo mientras cuentas.",
    "numeros.count.say": "¿{g, select, f{Cuántas} other{Cuántos}} {objetos} hay? Cuenta y toca el número.",
    "numeros.count.tip": "Cuenta de a uno, tocando cada dibujo. Y saqué una opción.",
    "numeros.count.reveal": "Contemos juntos: hay {n_palabras}. Mira cuál es.",
    "numeros.rec.say_grupo": "Este es el {n_palabras}. Toca el grupo que tiene {n_palabras}.",
    "numeros.rec.say": ["Toca el número {n_palabras}.", "¿Dónde está el {n_palabras}?", "Busca el {n_palabras}."],
    "numeros.rec.tip": "Fíjate bien en cada número. Saqué una opción.",
    "numeros.rec.reveal": "Mira, es el {n_palabras}.",
    "numeros.cmp.say_mas": "Toca el número más grande.",
    "numeros.cmp.say_menos": "Toca el número más chico.",
    "numeros.cmp.tip_mas": "Fíjate bien cuál tiene más. Saqué una opción.",
    "numeros.cmp.tip_menos": "Fíjate bien cuál tiene menos. Saqué una opción.",
    "numeros.cmp.reveal_mas": "Mira, este es el que tiene más: {n_palabras}.",
    "numeros.cmp.reveal_menos": "Mira, este es el que tiene menos: {n_palabras}.",
    "numeros.add.tip": "Cuenta todos juntos. Saqué una opción.",
    "numeros.add.reveal": "{a_palabras} más {b_palabras} son {c_palabras}. Mira.",
    "numeros.sub.tip": "Mira las que quedan sin tachar. Saqué una opción.",
    "numeros.sub.reveal": "{a_palabras} menos {b_palabras} son {c_palabras}. Mira.",
    "numeros.outro": "Ahora, ¡busca cosas para contar a tu alrededor!"
  }
});
