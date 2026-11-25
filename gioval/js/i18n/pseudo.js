"use strict";
/* Idiomas de PRUEBA generados automáticamente a partir de es-AR (no son idiomas reales; no se ofrecen a los chicos).
   - qps-ploc : pseudo-localización. Cambia las letras por parecidas con acento y alarga cada texto un 40 % ("[…]"),
                para descubrir textos cortados, botones que no entran o frases armadas pegando pedazos.
   - qps-plocm: lo mismo pero de derecha a izquierda (dir="rtl"), para probar el espejado de la interfaz.
   Sin voz a propósito (meta.sinVoz): prueba el último escalón de la cadena de voz, "solo texto". */
(function () {
  const MAPA = { a: "á", e: "é", i: "í", o: "ó", u: "ú", A: "Á", E: "É", I: "Í", O: "Ó", U: "Ú", c: "ç", n: "ñ", C: "Ç", N: "Ñ", y: "ý", s: "š", S: "Š", z: "ž" };
  function pseudo(s) {
    if (!s || s.length < 2 || /^[\d\s.,:;%×+\-–—→·/()]+$/.test(s)) return s;
    /* no tocar las etiquetas HTML (<b>, <br>) */
    const partes = s.split(/(<[^>]+>)/), extra = Math.ceil(s.replace(/<[^>]+>/g, "").length * 0.4);
    let fill = ""; while (fill.length < extra) fill += "ẍẍẍẍ ";
    const trans = partes.map(p => p[0] === "<" ? p : p.replace(/[A-Za-z]/g, c => MAPA[c] || c)).join("");
    return "⟦" + trans + " " + fill.trim() + "⟧";
  }
  const meta = { prueba: true, sinVoz: true, locale: "es-AR", moneda: "ARS", voz: [], fallback: [] };
  Gioval.i18n.registrarDerivado("qps-ploc", "es-AR", Object.assign({ nombre: "Pseudo-language (test)", nombreNativo: "Pseudo (prueba)", dir: "ltr" }, meta), pseudo);
  /* en RTL la flecha de "Seguir" mira hacia el otro lado (un idioma RTL real la traduciría ya con ⬅) */
  Gioval.i18n.registrarDerivado("qps-plocm", "es-AR", Object.assign({ nombre: "Pseudo-language RTL (test)", nombreNativo: "Pseudo RTL (prueba)", dir: "rtl" }, meta), s => pseudo(s).replace(/➜/g, "⬅"));
})();
