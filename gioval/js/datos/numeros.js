"use strict";
/* ============ DATOS DE LA ISLA NÚMEROS (contenido editable, sin lógica) ============
   Todo lo que se puede cambiar sin tocar código: textos visibles, la escalera de habilidades, las preguntas para el adulto y los
   umbrales de velocidad. La lógica está en js/islas/numeros.js (actividades) y js/islas/numeros_ubicacion.js (preguntas
   iniciales, test de ubicación y punto de partida). La explicación completa está en gioval-dev/docs/NUMEROS_EDADES.md.

   TEXTOS: todos los textos NUEVOS de la isla (es-AR, voseo) viven acá, agrupados, para pasarlos a claves de i18n de forma
   mecánica. Se escriben como frases con marcadores {nombre}. Los textos de las actividades v1 (contar, reconocer, más/menos,
   sumar, restar) siguen dentro de js/islas/numeros.js tal cual estaban, para no cambiar lo que ya se probó con los chicos.
   Reglas de redacción: elogio al esfuerzo y al proceso ("¡Probaste y salió!"), nunca a la persona ("¡qué inteligente!");
   sin rachas ni puntos; sin castigo por los errores. */
Gioval.datos.numeros = (function () {

  const TEXTOS = {
    /* ---- zona de adultos: botón del panel ---- */
    panel: {
      boton: "🔢 Números: punto de partida",
      sin: "Todavía no se cargó el punto de partida de {nombre} (empieza desde el principio).",
      respuestas: "Respuestas del adulto guardadas; falta aceptar el punto de partida.",
      pendiente: "El test de ubicación terminó: falta que un adulto acepte el resultado.",
      aceptado: "Empieza en «{inicio}» · {saltadas} habilidad(es) saltada(s) · {encurso} en curso.",
      completo: "Recorrió toda la escalera: no hay nada para practicar por ahora.",
    },
    /* ---- preguntas iniciales para el adulto ---- */
    intake: {
      titulo: "Punto de partida de {nombre}",
      intro: "Son 6 preguntas, una sola vez por niño. Sirven para empezar en el lugar justo (sin aburrir ni frustrar). Si no sabés una respuesta, elegí “No sé”: se usa la edad.",
      noSe: "No sé",
      edad: "¿Cuántos años tiene?",
      edades: { 4: "4 años", 5: "5 años", 6: "6 años", 7: "7 años", 8: "8 años o más" },
      ver: "Ver el punto de partida",
      cancelar: "Cancelar",
      aviso: "Lo que respondas no se aplica hasta que lo confirmes en la pantalla siguiente.",
    },
    /* ---- resumen que acepta o ajusta el adulto ---- */
    resumen: {
      tituloIntake: "Así empezaría {nombre}",
      tituloTest: "Resultado del test de ubicación de {nombre}",
      empieza: "Empieza en: <b>{inicio}</b>",
      empiezaTodo: "Ya recorrió toda la escalera.",
      saltadas: "{n} habilidad(es) marcada(s) como ya dominada(s)",
      encurso: "{n} en curso (se practican con menos ayuda para confirmar)",
      explica: "“Saltada” quiere decir que no se practica ahora, pero se vuelve a comprobar sin ayuda en el próximo chequeo semanal: si falla, vuelve atrás. Podés ajustar cada habilidad antes de aceptar.",
      aceptar: "Aceptar este punto de partida",
      hacerTest: "Hacer el test de ubicación (unos 5 min, con {nombre})",
      volver: "Volver",
      cambiarResp: "✏️ Cambiar las respuestas",
      aceptado: "¡Listo! Guardé el punto de partida de {nombre}.",
      etiqueta: { abierta: "para aprender ahora", cerrada: "se abre después" },
      estados: { saltada: "Ya la domina (se saltea)", encurso: "En curso (confirmar)", no: "Todavía no" },
      origen: { adulto: "según el adulto", ubicacion: "test de ubicación", implicita: "base de otra que domina", manual: "marcada a mano" },
      test: "Test: {ok} de {n} al primer intento · tiempo de respuesta mediano {mediana}.",
      testCorto: "El test terminó antes de tiempo ({motivo}); lo no probado se decide con las respuestas del adulto.",
      motivoTiempo: "se acabó el tiempo", motivoItems: "se llegó al máximo de ítems",
    },
    /* ---- motivos que quedan guardados en cada habilidad saltada ---- */
    motivos: {
      adulto: "según lo que contó el adulto en las preguntas iniciales",
      ubicacion: "en el test de ubicación ({ok} de {n} al primer intento, mediana {mediana})",
      implicita: "es base de «{de}», que ya domina",
      manual: "marcada a mano por un adulto al aceptar el punto de partida",
    },
    /* ---- test de ubicación (lo escucha y lo juega el niño) ---- */
    ubic: {
      titulo: "Jugamos con números",
      saludo: "¡Hola, {nombre}! Vamos a jugar un ratito con números. Algunos son fáciles y otros más difíciles. Si no sabés alguno, no pasa nada: probá igual.",
      siguientes: ["¡Seguimos!", "¡Gracias! Vamos al próximo.", "¡Probar así está muy bien!", "¡Pensaste con calma! Sigamos."],
      finTitulo: "¡Terminamos de jugar!",
      finVoz: "¡Terminamos, {nombre}! Jugaste con mucha atención. Ahora un adulto tiene que mirar algo en el celu.",
      botonAdulto: "👤 Para un adulto",
      botonMapa: "🗺️ Al mapa",
    },
    /* ---- informe para adultos ---- */
    informe: {
      titulo: "PUNTO DE PARTIDA — ISLA NÚMEROS",
      edad: "Edad: {edad} años.",
      edadNoSe: "Edad: sin dato.",
      resp: "Respuestas del adulto: {lista}.",
      respItem: "{corto}: {t}",
      noSe: "no sabe (se usó la edad)",
      test: "Test de ubicación ({fecha}): {n} ítems, {ok} al primer intento ({pct}), tiempo de respuesta mediano {mediana}.",
      testEjes: "Hasta dónde llegó, por eje: {lista}.",
      testEje: "{eje}: «{skill}»",
      testEjeNada: "{eje}: todavía no pasó el primer nivel",
      testEjeOmitido: "{eje}: no se probó",
      inicio: "Punto de partida aceptado el {fecha}: empieza en «{inicio}». {saltadas} saltada(s) · {encurso} en curso.",
      ajustes: "Ajustes manuales del adulto: {n}.",
      sin: "Sin preguntas iniciales: empezó desde el principio de la escalera.",
    },
    /* ---- nombres de los ejes ---- */
    ejes: { A: "Conteo y números", B: "Comparar y ordenar", C: "Sumas y restas", D: "Valor posicional", E: "Dobles, grupos y repartos" },

    /* ---- actividades nuevas (lo que dice la app al jugar). {n}, {a}, … los completa el código ---- */
    act: {
      vecino: {
        ok: ["¡Te fijaste en el orden!", "¡Contar en tu cabeza ayudó!", "¡Eso es! Pensar en la fila de números sirve."],
        sig: "¿Qué número viene justo después del {n}?", ant: "¿Qué número viene justo antes del {n}?",
        tipSig: "Contá desde el {n} y fijate cuál sigue. Saqué una opción.", tipAnt: "Contá para atrás desde el {n}. Saqué una opción.",
        revSig: "Después del {n} viene el {r}. Mirá.", revAnt: "Antes del {n} viene el {r}. Mirá.",
      },
      serie: {
        ok: ["¡Descubriste la regla!", "¡Te fijaste cómo sigue la serie!", "¡Eso es! Mirar los vecinos ayuda."],
        say: "Mirá la serie y completá: ¿qué número falta?", dea: " Va de a {paso}.",
        tip: "Fijate cuánto cambia de un número al siguiente. Saqué una opción.", rev: "En esta serie falta el {r}. Mirá cómo sigue.",
      },
      num100: {
        ok: ["¡Te fijaste bien en cada cifra!", "¡Escuchaste con atención y salió!", "¡Eso es! Mirar los dos números ayuda."],
        say: ["Tocá el número {n}.", "¿Dónde está el {n}?", "Buscá el {n}."],
        tip: "Fijate bien en el primer número y en el segundo. Saqué una opción.", rev: "Mirá, es el {n}: {dd} y {uu}.",
      },
      cmpg: {
        ok: ["¡Comparaste con cuidado!", "¡Miraste las decenas primero!", "¡Eso es! Fijarse en las decenas ayuda."],
        mas: "¿Cuál es el número más grande?", menos: "¿Cuál es el número más chico?", masB: "¿Dónde hay más?", menosB: "¿Dónde hay menos?",
        tip: "Mirá primero las decenas: las barras. Saqué una opción.", rev: "Mirá, es el {r}.",
      },
      ord: {
        ok: ["¡Ordenaste con paciencia!", "¡Buscaste uno por uno y salió!", "¡Eso es! Ir de a uno ayuda."],
        asc: "Tocá los números de menor a mayor: primero el más chico.", desc: "Tocá los números de mayor a menor: primero el más grande.",
        tipAsc: "Buscá el más chico de los que quedan. Saqué una opción.", tipDesc: "Buscá el más grande de los que quedan. Saqué una opción.",
        revAsc: "El orden es {l}. Mirá.", revDesc: "El orden es {l}. Mirá.",
      },
      dyu: {
        ok: ["¡Contaste las decenas y las unidades!", "¡Separaste decenas y unidades!", "¡Eso es! Mirar cada grupo ayuda."],
        num: "Hay {dd} y {uu}. ¿Qué número es?",
        dec: "¿Cuántas decenas tiene el {n}?", uni: "¿Cuántas unidades sueltas tiene el {n}?",
        tip: "Las barras son decenas y los cuadraditos sueltos son unidades. Saqué una opción.", rev: "El {n} tiene {dd} y {uu}. Mirá.",
      },
      cen: {
        ok: ["¡Armaste el número por partes!", "¡Contaste centenas, decenas y unidades!", "¡Eso es! Ir por partes ayuda."],
        num: "Hay {cc}, {dd} y {uu}. ¿Qué número es?", cen: "¿Cuántas centenas tiene el {n}?",
        tip: "El cuadrado grande es una centena, la barra una decena y el cuadradito una unidad. Saqué una opción.", rev: "El {n} tiene {cc}, {dd} y {uu}. Mirá.",
      },
      dob: {
        ok: ["¡Juntaste dos grupos iguales!", "¡Pensaste en dos veces lo mismo!", "¡Eso es! Duplicar es juntar dos iguales."],
        say: "¿Cuál es el doble de {n}? Es juntar dos grupos de {n}.", sayB: "Hay dos grupos de {n}. ¿Cuántas hay en total?", eq: "El doble de {n} = ?",
        tip: "Doble es lo mismo dos veces. Contá los dos grupos. Saqué una opción.", rev: "El doble de {n} es {r}. Mirá los dos grupos.",
      },
      mit: {
        ok: ["¡Repartiste en dos partes iguales!", "¡Pensaste en dos mitades!", "¡Eso es! Repartir parejo ayuda."],
        say: "¿Cuál es la mitad de {n}? Es repartir en dos partes iguales.", sayB: "Hay {n}. Las repartimos en dos grupos iguales. ¿Cuántas hay en cada grupo?", eq: "La mitad de {n} = ?",
        tip: "Repartí de a una en cada grupo hasta que no queden. Saqué una opción.", rev: "La mitad de {n} es {r}. Mirá los dos grupos.",
      },
      grp: {
        ok: ["¡Contaste los grupos iguales!", "¡Juntaste grupo por grupo!", "¡Eso es! Sumar de a grupos ayuda."],
        say: "Hay {g} bolsas con {p} {obj} en cada una. ¿{Cuantos} {obj} hay en total?",
        sayT: "{g} grupos de {p}. ¿Cuánto es en total?",
        tip: "Sumá grupo por grupo: {suma}. Saqué una opción.", rev: "{g} grupos de {p} son {r}. Mirá.",
      },
      rep: {
        ok: ["¡Repartiste parejo!", "¡Repartiste de a uno y salió!", "¡Eso es! Repartir de a uno ayuda."],
        say: "Hay {n} {obj}. {Los} repartimos en partes iguales entre {a} amigos. ¿{Cuantos} le tocan a cada uno?",
        sayT: "{n} entre {a}. ¿Cuánto le toca a cada uno?",
        tip: "Repartí de a uno a cada amigo hasta que no queden. Saqué una opción.", rev: "{n} entre {a} toca {r} para cada uno. Mirá.",
      },
      mul: {
        ok: ["¡Juntaste los grupos iguales!", "¡Contaste de a grupos y salió!", "¡Eso es! Sumar de a grupos ayuda."],
        say: "Hay {f} grupos de {t}. ¿Cuánto es {f} por {t}?", sayT: "¿Cuánto es {f} por {t}?",
        tip: "Sumá {t} cada vez, {f} veces: {suma}. Saqué una opción.", rev: "{f} por {t} es {r}. Mirá los grupos.",
      },
      div: {
        ok: ["¡Repartiste en grupos iguales!", "¡Pensaste en cuántos entran!", "¡Eso es! Repartir de a uno ayuda."],
        say: "Hay {n} {obj}. {Los} repartimos en {d} grupos iguales. ¿{Cuantos} hay en cada grupo?", sayT: "¿Cuánto es {n} dividido por {d}?",
        tip: "Repartí de a una en cada grupo hasta que no queden. Saqué una opción.", rev: "{n} dividido por {d} es {r}. Mirá.",
      },
      sumg: {
        ok: ["¡Sumaste decenas con decenas!", "¡Juntaste por partes!", "¡Eso es! Sumar por partes ayuda."],
        say: "Hay {a} y llegan {b} más. ¿Cuánto hay en total?", sayT: "¿Cuánto es {a} más {b}?",
        tip: "Juntá las decenas por un lado y las unidades por otro. Saqué una opción.", rev: "{a} más {b} son {r}. Mirá.",
      },
      restag: {
        ok: ["¡Sacaste por partes!", "¡Restaste decenas y unidades!", "¡Eso es! Restar por partes ayuda."],
        say: "Había {a} y se van {b}. ¿Cuántos quedan?", sayT: "¿Cuánto es {a} menos {b}?",
        tip: "Sacá las decenas por un lado y las unidades por otro. Saqué una opción.", rev: "{a} menos {b} son {r}. Mirá.",
      },
    },
  };

  /* ---- ejes: cada uno es una cadena de habilidades de menor a mayor, usada por el test de ubicación ---- */
  const EJES = [
    { id: "A", cadena: ["num_c10", "num_r10", "num_c20", "num_r20", "num_sig", "num_ser20", "num_r100", "num_ser100", "num_dec", "num_sal"], necesita: null },
    { id: "C", cadena: ["num_add5", "num_sub5", "num_add10", "num_sub10", "num_add20", "num_sub20", "num_add100", "num_sub100"], necesita: "num_r10" },
    { id: "B", cadena: ["num_may", "num_may20", "num_ord20", "num_may100", "num_ord100"], necesita: "num_r10" },
    { id: "D", cadena: ["num_dyu", "num_cen"], necesita: "num_r100" },
    { id: "E", cadena: ["num_dob", "num_mit", "num_grp", "num_rep", "num_mul", "num_div"], necesita: "num_add10" },
  ];

  /* ---- la escalera: 31 habilidades ----
     Campos propios de cada habilidad (los demás son parámetros de su actividad):
       eje      A..E (ver EJES)            edad   edad típica de arranque (años), orientativa
       nap      de dónde sale (ver abajo)  rapido {rt: ms bajo el cual se considera "rápido", salta: [ids que se pueden saltear]}
     Los 9 primeros ids son los de la versión 1 de la isla y NO se pueden renombrar (son parte del progreso guardado).

     ALINEACIÓN CURRICULAR (resumen propio, sin citas textuales). Se leyeron los documentos oficiales y se anotó qué eje cubre
     cada habilidad; lo que no se pudo verificar está marcado "a revisar".
       · NAP Matemática, Primer Ciclo EGB / Nivel Primario (Ministerio de Educación de la Nación; en educ.ar), eje "En relación
         con el número y las operaciones". 1.º año: leer, escribir y comparar números; regularidades de la serie; sumas y restas
         pasando del conteo al cálculo, con una y dos cifras; cálculos memorizados como dobles. 2.º año: números de tres cifras y
         valor posicional; multiplicación y división con distintos significados; sumas y restas de hasta tres cifras.
       · Progresiones de los aprendizajes, Matemática Primer Ciclo (GCBA, 2018), "Sistema de numeración": Niveles I y II ≈ serie
         oral, contar colecciones, leer/ordenar hasta ~100; Nivel III ≈ hasta ~1000 y escalas de 10 en 10; Nivel IV ≈ hasta ~10.000.
       · Para 4 y 5 años (Nivel Inicial: conteo, reconocimiento de números hasta 10 o 20) las habilidades quedan anotadas
         "NAP Nivel Inicial: a revisar": no se verificó ese documento.
       · Las edades son una aproximación para ordenar la escalera, NO una norma: los NAP se organizan por año/grado, no por edad.
     Marcas: "nap1"/"nap2" = año del NAP; "prog I-II/III" = nivel de las Progresiones; "a revisar" = no verificado. */
  const ESCALA = [
    /* ---- las 9 de la versión 1 (no cambiar ids, nombres ni parámetros) ---- */
    { id: "num_c10", name: "Contar hasta 10", icon: "🍎🍎🍎", type: "count", min: 1, max: 10, req: [], eje: "A", edad: 4,
      nap: "serie oral y conteo de colecciones pequeñas: Progresiones prog I-II; NAP Nivel Inicial: a revisar", rapido: { rt: 6000, salta: ["num_r10"] } },
    { id: "num_r10", name: "Reconocer los números", icon: "7️⃣", type: "numrec", min: 1, max: 10, req: ["num_c10"], eje: "A", edad: 4,
      nap: "leer números de una cifra: NAP 1.º (leer y escribir números); prog I-II", rapido: { rt: 2500, salta: ["num_may"] } },
    { id: "num_may", name: "Más y menos", icon: "⚖️", type: "cmp", max: 10, req: ["num_r10"], eje: "B", edad: 4,
      nap: "comparar cantidades y números: NAP 1.º (comparar); prog I-II", rapido: { rt: 3500, salta: [] } },
    { id: "num_add5", name: "Sumas hasta 5", icon: "➕", type: "add", min: 2, max: 5, req: ["num_r10"], eje: "C", edad: 5,
      nap: "agregar/juntar, pasando del conteo al cálculo: NAP 1.º (suma y resta)", rapido: { rt: 4000, salta: [] } },
    { id: "num_sub5", name: "Restas hasta 5", icon: "➖", type: "sub", min: 2, max: 5, req: ["num_add5"], eje: "C", edad: 5,
      nap: "quitar/separar, del conteo al cálculo: NAP 1.º (suma y resta)", rapido: { rt: 4500, salta: [] } },
    { id: "num_c20", name: "Contar hasta 20", icon: "🔢", type: "count", min: 6, max: 20, req: ["num_c10", "num_may"], eje: "A", edad: 5,
      nap: "conteo de colecciones y serie hasta ~20: prog I-II; NAP Nivel Inicial: a revisar", rapido: { rt: 7000, salta: ["num_r20"] } },
    { id: "num_add10", name: "Sumas hasta 10", icon: "➕🔟", type: "add", min: 6, max: 10, req: ["num_add5", "num_may"], eje: "C", edad: 5,
      nap: "sumas con resultados hasta 10, cálculo memorizado: NAP 1.º", rapido: { rt: 5000, salta: ["num_dob"] } },
    { id: "num_sub10", name: "Restas hasta 10", icon: "➖🔟", type: "sub", min: 6, max: 10, req: ["num_sub5", "num_add10"], eje: "C", edad: 6,
      nap: "restas con números hasta 10: NAP 1.º", rapido: { rt: 5500, salta: [] } },
    { id: "num_r20", name: "Los números hasta 20", icon: "2️⃣0️⃣", type: "numrec", min: 8, max: 20, req: ["num_c20"], eje: "A", edad: 5,
      nap: "leer números de dos cifras (hasta 20): NAP 1.º; prog I-II", rapido: { rt: 3000, salta: ["num_sig"] } },

    /* ---- nuevas: eje A (conteo y números) ---- */
    { id: "num_sig", name: "El que sigue y el que va antes", icon: "👉", type: "vecino", min: 1, max: 20, req: ["num_r20"], eje: "A", edad: 5,
      nap: "regularidades de la serie numérica: NAP 1.º; prog I-II (a revisar el ajuste de edad)", rapido: { rt: 3000, salta: ["num_ser20"] } },
    { id: "num_ser20", name: "Completar series hasta 20", icon: "🧩", type: "serie", min: 1, max: 20, steps: [1], desc: true, req: ["num_sig"], eje: "A", edad: 6,
      nap: "regularidades de la serie numérica (ascendente y descendente): NAP 1.º; prog I-II", rapido: { rt: 4000, salta: [] } },
    { id: "num_r100", name: "Los números hasta 100", icon: "💯", type: "num100", min: 21, max: 100, req: ["num_r20"], eje: "A", edad: 6,
      nap: "leer números de dos cifras: NAP 1.º; Progresiones Niveles I-II (hasta ~100)", rapido: { rt: 3500, salta: ["num_ser100"] } },
    { id: "num_ser100", name: "Completar series hasta 100", icon: "🧮", type: "serie", min: 1, max: 100, steps: [1], desc: true, req: ["num_ser20", "num_r100"], eje: "A", edad: 6,
      nap: "regularidades en la serie numérica hasta ~100: NAP 1.º; prog I-II", rapido: { rt: 4500, salta: ["num_dec"] } },
    { id: "num_dec", name: "Contar de 10 en 10", icon: "🔟", type: "serie", min: 10, max: 100, steps: [10], alinear: true, req: ["num_r100"], eje: "A", edad: 6,
      nap: "escalas de 10 en 10: las Progresiones lo ubican en el Nivel III; acá se adelanta como paso previo (a revisar)", rapido: { rt: 4000, salta: [] } },
    { id: "num_sal", name: "Contar de 2 en 2 y de 5 en 5", icon: "🦘", type: "serie", min: 2, max: 50, steps: [2, 5], alinear: true, req: ["num_dec", "num_ser20"], eje: "A", edad: 7,
      nap: "series proporcionales / regularidades, base de la multiplicación: NAP 2.º (a revisar)", rapido: { rt: 5000, salta: [] } },

    /* ---- nuevas: eje B (comparar y ordenar) ---- */
    { id: "num_may20", name: "Más y menos hasta 20", icon: "⚖️2️⃣0️⃣", type: "cmp", max: 20, req: ["num_may", "num_r20"], eje: "B", edad: 5,
      nap: "comparar números hasta 20: NAP 1.º (comparar)", rapido: { rt: 3500, salta: ["num_ord20"] } },
    { id: "num_ord20", name: "Ordenar números hasta 20", icon: "↗️", type: "ord", min: 1, max: 20, cnt: 3, req: ["num_may20"], eje: "B", edad: 6,
      nap: "ordenar números (Progresiones prog I-II); NAP 1.º (comparar)", rapido: { rt: 9000, salta: [] } },
    { id: "num_may100", name: "Comparar números hasta 100", icon: "⚖️💯", type: "cmpg", min: 10, max: 99, req: ["num_r100", "num_may20"], eje: "B", edad: 6,
      nap: "comparar números de dos cifras mirando decenas y unidades: NAP 1.º; prog I-II", rapido: { rt: 4000, salta: ["num_ord100"] } },
    { id: "num_ord100", name: "Ordenar números hasta 100", icon: "📶", type: "ord", min: 10, max: 99, cnt: 3, req: ["num_may100", "num_ord20"], eje: "B", edad: 7,
      nap: "ordenar números de dos cifras: NAP 1.º; prog I-II", rapido: { rt: 11000, salta: [] } },

    /* ---- nuevas: eje C (sumas y restas, hasta 100) ---- */
    { id: "num_add20", name: "Sumas hasta 20", icon: "➕2️⃣0️⃣", type: "add", min: 11, max: 20, req: ["num_add10", "num_r20"], eje: "C", edad: 6,
      nap: "sumas hasta 20 (pasar la decena), cálculo mental: NAP 1.º", rapido: { rt: 6000, salta: [] } },
    { id: "num_sub20", name: "Restas hasta 20", icon: "➖2️⃣0️⃣", type: "sub", min: 11, max: 20, req: ["num_sub10", "num_add20"], eje: "C", edad: 6,
      nap: "restas hasta 20: NAP 1.º", rapido: { rt: 6500, salta: [] } },
    { id: "num_add100", name: "Sumas hasta 100 (sin llevar)", icon: "➕💯", type: "sumg", max: 100, req: ["num_add20", "num_dyu"], eje: "C", edad: 7,
      nap: "sumas con decenas enteras y números de dos cifras: NAP 1.º-2.º (decenas enteras, cálculo mental)", rapido: { rt: 9000, salta: [] } },
    { id: "num_sub100", name: "Restas hasta 100 (sin llevar)", icon: "➖💯", type: "restag", max: 99, req: ["num_sub20", "num_add100"], eje: "C", edad: 7,
      nap: "restas con decenas enteras y números de dos cifras: NAP 1.º-2.º", rapido: { rt: 9500, salta: [] } },

    /* ---- nuevas: eje D (valor posicional) ---- */
    { id: "num_dyu", name: "Decenas y unidades", icon: "🧱", type: "dyu", min: 11, max: 99, req: ["num_r100"], eje: "D", edad: 6,
      nap: "valor posicional (decenas y unidades): NAP 1.º; Progresiones Nivel II-III", rapido: { rt: 5000, salta: [] } },
    { id: "num_cen", name: "Las centenas", icon: "🟦", type: "cen", min: 100, max: 599, req: ["num_dyu", "num_may100"], eje: "D", edad: 7,
      nap: "números de tres cifras y valor posicional: NAP 2.º; Progresiones Nivel III (hasta ~1000)", rapido: { rt: 6000, salta: [] } },

    /* ---- nuevas: eje E (dobles, grupos y repartos) — la parte de multiplicar y dividir es nivel avanzado ---- */
    { id: "num_dob", name: "Los dobles", icon: "👯", type: "dob", max: 10, req: ["num_add10"], eje: "E", edad: 5,
      nap: "cálculos memorizados: dobles: NAP 1.º", rapido: { rt: 4000, salta: ["num_mit"] } },
    { id: "num_mit", name: "Las mitades", icon: "✂️", type: "mit", max: 20, req: ["num_dob", "num_sub10"], eje: "E", edad: 6,
      nap: "reparto en partes iguales (mitad): NAP 2.º reparto; a revisar su ubicación", rapido: { rt: 4500, salta: [] } },
    { id: "num_grp", name: "Grupos iguales", icon: "🧺", type: "grp", max: 20, req: ["num_add20", "num_dob"], eje: "E", edad: 6,
      nap: "multiplicar como grupos iguales / sumas repetidas: NAP 2.º (multiplicación con distintos significados)", rapido: { rt: 6000, salta: [] } },
    { id: "num_rep", name: "Repartir en partes iguales", icon: "🍪", type: "rep", max: 20, req: ["num_grp", "num_mit"], eje: "E", edad: 7,
      nap: "dividir como repartir en partes iguales: NAP 2.º (división con distintos significados)", rapido: { rt: 6500, salta: [] } },
    { id: "num_mul", name: "Multiplicar: tablas del 2, 5 y 10", icon: "✖️", type: "mul", tablas: [2, 5, 10], fmax: 5, req: ["num_grp", "num_sal"], eje: "E", edad: 7,
      nap: "multiplicación y primeros productos memorizados: NAP 2.º-3.º (a revisar el alcance de las tablas)", rapido: { rt: 6000, salta: [] } },
    { id: "num_div", name: "Dividir en partes iguales", icon: "➗", type: "div", divisores: [2, 3, 5], qmax: 5, req: ["num_rep", "num_mul"], eje: "E", edad: 7,
      nap: "división como reparto y partición: NAP 2.º-3.º (a revisar)", rapido: { rt: 7000, salta: [] } },
  ];

  /* ---- preguntas iniciales para el adulto ----
     Cada opción lista las habilidades que "dominaría" quien responde eso. Después se agregan sus requisitos (ver NUMEROS_EDADES.md).
     defecto: lo que se asume por edad si el adulto contesta "No sé". Es CONSERVADOR a propósito (apunta por debajo de lo típico). */
  const A = (...ids) => ids;
  const INTAKE = {
    version: 1,
    edades: [4, 5, 6, 7, 8],
    preguntas: [
      { id: "cuenta", corto: "Cuenta de memoria", texto: "¿Hasta cuánto cuenta de memoria, sin ayuda?",
        opciones: [
          { v: 0, t: "Todavía no cuenta (o llega hasta 3)", domina: A() },
          { v: 5, t: "Hasta 5", domina: A() },
          { v: 10, t: "Hasta 10", domina: A("num_c10") },
          { v: 20, t: "Hasta 20", domina: A("num_c10", "num_c20") },
          { v: 50, t: "Hasta 50", domina: A("num_c10", "num_c20", "num_sig", "num_ser20") },
          { v: 100, t: "Hasta 100 o más", domina: A("num_c10", "num_c20", "num_sig", "num_ser20", "num_dec") },
        ] },
      { id: "reconoce", corto: "Reconoce escrito", texto: "¿Hasta qué número reconoce cuando lo ve escrito?",
        opciones: [
          { v: 0, t: "Todavía no reconoce números", domina: A() },
          { v: 5, t: "Hasta 5", domina: A() },
          { v: 10, t: "Hasta 10", domina: A("num_r10") },
          { v: 20, t: "Hasta 20", domina: A("num_r10", "num_r20") },
          { v: 100, t: "Hasta 100", domina: A("num_r10", "num_r20", "num_r100") },
          { v: 1000, t: "Hasta 1000 o más", domina: A("num_r10", "num_r20", "num_r100", "num_may100") },
        ] },
      { id: "suma", corto: "Suma", texto: "¿Sabe sumar?",
        opciones: [
          { v: 0, t: "Todavía no", domina: A() },
          { v: 5, t: "Sí, con resultados hasta 5", domina: A("num_add5") },
          { v: 10, t: "Sí, hasta 10", domina: A("num_add5", "num_add10") },
          { v: 20, t: "Sí, hasta 20", domina: A("num_add5", "num_add10", "num_add20") },
          { v: 100, t: "Sí, hasta 100 o más", domina: A("num_add5", "num_add10", "num_add20", "num_dyu", "num_add100") },
        ] },
      { id: "resta", corto: "Resta", texto: "¿Sabe restar?",
        opciones: [
          { v: 0, t: "Todavía no", domina: A() },
          { v: 5, t: "Sí, con números hasta 5", domina: A("num_sub5") },
          { v: 10, t: "Sí, hasta 10", domina: A("num_sub5", "num_sub10") },
          { v: 20, t: "Sí, hasta 20", domina: A("num_sub5", "num_sub10", "num_sub20") },
          { v: 100, t: "Sí, hasta 100 o más", domina: A("num_sub5", "num_sub10", "num_sub20", "num_dyu", "num_sub100") },
        ] },
      { id: "mult", corto: "Multiplicación", texto: "¿Ya conoce la multiplicación?",
        opciones: [
          { v: 0, t: "No", domina: A() },
          { v: 1, t: "Todavía no, pero sabe los dobles", domina: A("num_dob") },
          { v: 2, t: "Arma grupos iguales y reparte en partes iguales", domina: A("num_dob", "num_mit", "num_grp", "num_rep") },
          { v: 3, t: "Sabe las tablas del 2, 5 y 10", domina: A("num_dob", "num_mit", "num_grp", "num_rep", "num_sal", "num_mul", "num_div") },
        ] },
    ],
    defecto: {
      4: { cuenta: 5, reconoce: 5, suma: 0, resta: 0, mult: 0 },
      5: { cuenta: 10, reconoce: 10, suma: 0, resta: 0, mult: 0 },
      6: { cuenta: 20, reconoce: 20, suma: 5, resta: 5, mult: 0 },
      7: { cuenta: 50, reconoce: 100, suma: 10, resta: 10, mult: 0 },
      8: { cuenta: 100, reconoce: 100, suma: 20, resta: 20, mult: 0 },
    },
  };

  /* ---- test de ubicación (escalera adaptativa) ---- */
  const UBICACION = {
    ayuda: 1,              // nivel de ayuda visual con que se muestran los ítems (0 más ayuda … 2 sin ayuda)
    itemsPorNivel: 2,      // un nivel se aprueba con 2 aciertos al primer intento (si hay 1 y 1, se agrega un 3.er ítem)
    maxItemsPorEje: 8,
    maxItems: 30,
    maxMs: 5 * 60e3,       // ~5 minutos de juego
  };

  return { TEXTOS, EJES, ESCALA, INTAKE, UBICACION };
})();
