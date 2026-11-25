"use strict";
/* ============ DOMINIO RÁPIDO Y SALTOS (genérico: no nombra ninguna isla) ============
   Qué hace:
   1) SALTO POR DOMINIO RÁPIDO. Cuando una habilidad se domina (evento "dominada" del motor) y la evidencia dice que fue
      fácil, se SALTA la siguiente habilidad que se destraba (se marca como sabida sin practicarla). "Fácil" =
        - al menos 6 intentos de aprendizaje, y
        - 90 % o más acertados AL PRIMER INTENTO (entre los últimos 10), y
        - al menos 5 tiempos de respuesta (rt) y su MEDIANA <= skill.rtRapido (ms, lo declara la isla en cada habilidad;
          sin rtRapido nunca hay salto).
      El tiempo rt lo mide el motor de toques desde que termina la voz hasta la respuesta correcta al primer intento.
   2) UNA HABILIDAD SALTADA (o marcada como sabida por una isla: ubicación, preguntas iniciales) tiene
      st.skip = { t, por, datos, estado:"pendiente"|"confirmada"|"revertida" }. Se RE-EVALÚA en el chequeo semanal sin ayuda
      (evento "chequeo"): si no acierta ni un ítem, vuelve a práctica (revertida); si acierta alguno, queda confirmada.
      El chequeo semanal da prioridad a las pendientes.
   3) Aporta al informe para adultos: mediana de rt por habilidad y qué se saltó y por qué.
   Ganchos del motor que usa: Gioval.emit("dominada"), Gioval.emit("chequeo"), elegirChequeo() y lineasInforme(). */
Gioval.dominio = (function () {
  /* Textos del informe: frases completas en la tabla del idioma (es-AR obligatorio; en incluido). Lo que se guarda en el
     progreso son DATOS (st.skip.datos), no frases: el informe se escribe en el idioma de quien lo lee. */
  Gioval.i18n.agregar("es-AR", {
    "dominio.tiempo": "   Tiempo de respuesta típico: {seg} s (mediana de {n} aciertos al primer intento)",
    "dominio.salto_linea": "   Saltada el {fecha} ({por}): {motivo}.",
    "dominio.por_rapido": "dominio rápido", "dominio.por_ubicacion": "juego de ubicación", "dominio.por_preguntas": "preguntas iniciales",
    "dominio.motivo_rapido": "domino rápido: {n} intentos, {ac}% al primer intento, mediana {seg} s en «{hab}»",
    "dominio.motivo_ubicacion": "juego de ubicación del {fecha} ({n} preguntas)",
    "dominio.motivo_preguntas": "según las preguntas para adultos del {fecha}",
    "dominio.estado_pendiente": "Todavía no se comprobó sin ayuda.",
    "dominio.estado_confirmada": "Comprobada sin ayuda el {fecha}: ¡se mantiene!",
    "dominio.estado_revertida": "Se comprobó el {fecha} y no salió: volvió a práctica.",
    "dominio.estado_anulada": "Se anuló el {fecha} al cambiar el punto de partida.",
    "dominio.ya_sabias": "⭐ Ya lo sabías (se repasa pronto)",
    "dominio.nota": "\"Saltada\" significa que se marcó como sabida sin practicarla (por dominio rápido, por las preguntas iniciales o por el juego de ubicación) y se vuelve a comprobar sin ayuda en el chequeo semanal; si no sale, vuelve a práctica. Los tiempos son de respuesta al primer intento, sin contar lo que tarda la voz."
  });
  Gioval.i18n.agregar("en", {
    "dominio.tiempo": "   Typical response time: {seg} s (median of {n} first-try correct answers)",
    "dominio.salto_linea": "   Skipped on {fecha} ({por}): {motivo}.",
    "dominio.por_rapido": "quick mastery", "dominio.por_ubicacion": "placement game", "dominio.por_preguntas": "initial questions",
    "dominio.motivo_rapido": "mastered quickly: {n} attempts, {ac}% right on the first try, median {seg} s in \u201c{hab}\u201d",
    "dominio.motivo_ubicacion": "placement game on {fecha} ({n} questions)",
    "dominio.motivo_preguntas": "from the adult questions on {fecha}",
    "dominio.estado_pendiente": "Not yet checked without help.",
    "dominio.estado_confirmada": "Checked without help on {fecha}: it holds!",
    "dominio.estado_revertida": "Checked on {fecha} and it did not come out: back to practice.",
    "dominio.estado_anulada": "Cancelled on {fecha} when the starting point was changed.",
    "dominio.ya_sabias": "⭐ Already knew it (will be reviewed soon)",
    "dominio.nota": "\"Skipped\" means it was marked as known without practicing it (by quick mastery, the initial questions or the placement game) and it is checked again without help in the weekly check; if it does not come out, it goes back to practice. Times are first-try response times, not counting how long the voice takes."
  });
  const fechaDe = ts => Gioval.i18n.fecha(new Date(ts));
  const mediana = a => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const seg = ms => Gioval.i18n.num(Math.round(ms / 100) / 10);
  const eventos = id => (store.log[KID] || []).filter(e => e.s === id);
  const packDe = sk => Gioval.islas.lista.find(p => p.skills.includes(sk));
  const D = {
    mediana, seg,
    /* evidencia de rapidez de una habilidad (con los últimos 10 intentos de aprendizaje) */
    evidencia(sk) {
      const ev = eventos(sk.id).filter(e => e.k === "learn").slice(-10), n = ev.length;
      const rts = ev.filter(e => e.f && e.r != null).map(e => e.r);
      return { n, ac: n ? ev.filter(e => e.f).length / n : 0, nrt: rts.length, med: mediana(rts) };
    },
    esRapida(sk) {
      if (!sk.rtRapido) return false;
      const d = D.evidencia(sk);
      return d.n >= 6 && d.ac >= .9 && d.nrt >= 5 && d.med != null && d.med <= sk.rtRapido;
    },
    /* marca una habilidad como sabida SIN práctica. Devuelve true si la marcó. */
    marcarSaltada(sk, por, datos, desde) {   /* datos: lo que hace falta para explicar el motivo en el informe (ver dominio.motivo_<por>) */
      const st = SK(sk.id); if (st.mast) return false;
      st.mast = true; st.box = 1; st.due = Date.now() + DAY; st.score = Math.max(st.score, .9);
      st.skip = { t: Date.now(), por, datos: datos || {}, estado: "pendiente" }; if (desde) st.skip.desde = desde;
      return true;
    },
    /* vuelve a práctica una habilidad saltada (conserva el registro de por qué) */
    revertir(sk, estado) {   /* estado: "revertida" (no salió en el chequeo) o "anulada" (el adulto cambió el punto de partida) */
      const st = SK(sk.id); if (!st.skip) return;
      st.mast = false; st.att = 0; st.score = .5; st.box = 0; st.due = 0; st.lvl = 0; st.rec = [];
      st.skip.estado = estado || "revertida"; st.skip.tCheq = Date.now();
    },
    pendientes(pack) { return pack.skills.filter(s => { const st = SK(s.id); return st.mast && st.skip && st.skip.estado === "pendiente"; }); },
    /* gancho "dominada": ¿fue fácil? entonces saltar la siguiente */
    alDominar(sk) {
      if (!D.esRapida(sk)) return null;
      const pack = packDe(sk); if (!pack) return null;
      const sig = pack.skills.find(s => !SK(s.id).mast && s.saltable !== false && s.req.includes(sk.id) && s.req.every(r => SK(r).mast));
      if (!sig) return null;
      const d = D.evidencia(sk);
      D.marcarSaltada(sig, "rapido", { n: d.n, ac: Math.round(d.ac * 100), ms: d.med, hab: sk.id }, sk.id);
      return sig;
    },
    /* gancho del chequeo semanal: arma los ítems (máx. 10) dando prioridad a las habilidades saltadas pendientes */
    elegirChequeo(items) {
      const pack = PACK, pend = new Set(D.pendientes(pack).map(s => s.id));
      if (!pend.size) return shuffle(items).slice(0, 10);   /* sin saltadas: exactamente el chequeo de siempre (mismo sorteo) */
      const por = pend.size <= 5 ? 2 : 1, tomados = {}, prio = [], resto = [];
      shuffle(items).forEach(it => {
        const id = it.skill.id;
        if (pend.has(id) && (tomados[id] || 0) < por && prio.length < 10) { tomados[id] = (tomados[id] || 0) + 1; prio.push(it); } else resto.push(it);
      });
      return shuffle(prio.concat(resto.slice(0, Math.max(0, 10 - prio.length))));
    },
    /* gancho "chequeo": re-evalúa las saltadas pendientes según los resultados */
    alTerminarChequeo(d) {
      const por = {}; (d.res || []).forEach(r => { (por[r.s] = por[r.s] || []).push(r.o); });
      let cambio = false;
      d.pack.skills.forEach(s => {
        const st = SK(s.id), r = por[s.id]; if (!r || !st.skip || st.skip.estado !== "pendiente") return;
        if (r.some(x => x)) { st.skip.estado = "confirmada"; st.skip.tCheq = Date.now(); } else D.revertir(s);
        cambio = true;
      });
      if (cambio) save();
    },
    /* líneas para el informe para adultos (de una habilidad) */
    lineasInforme(s, st, ev) {
      const out = [], rts = ev.filter(e => e.f && e.r != null).map(e => e.r);
      if (rts.length >= 3) out.push(t("dominio.tiempo", { seg: seg(mediana(rts)), n: rts.length }));
      if (st.skip) {
        const k = st.skip, d = k.datos || {}, h = Gioval.islas.habilidades().find(x => x.id === d.hab);
        const motivo = t("dominio.motivo_" + k.por, { n: d.n, ac: d.ac, seg: d.ms != null ? seg(d.ms) : "", hab: h ? h.name : (d.hab || ""), fecha: d.ts ? fechaDe(d.ts) : fechaDe(k.t) });
        out.push(t("dominio.salto_linea", { fecha: fechaDe(k.t), por: t("dominio.por_" + k.por), motivo }));
        out.push("   " + t("dominio.estado_" + k.estado, { fecha: k.tCheq ? fechaDe(k.tCheq) : "" }));
      }
      return out;
    },
    /* resumen de saltos de una isla */
    resumenSaltos(pack) {
      const sk = pack.skills.filter(s => SK(s.id).skip);
      return { n: sk.length, confirmadas: sk.filter(s => SK(s.id).skip.estado === "confirmada").length, revertidas: sk.filter(s => SK(s.id).skip.estado === "revertida").length, pendientes: sk.filter(s => SK(s.id).skip.estado === "pendiente").length };
    }
  };
  Gioval.on("dominada", e => { if (e && e.skill) D.alDominar(e.skill); });
  Gioval.on("chequeo", e => D.alTerminarChequeo(e));
  return D;
})();
