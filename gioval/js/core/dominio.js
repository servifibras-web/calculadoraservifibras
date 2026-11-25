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
      st.skip = { t, por, why, estado:"pendiente"|"confirmada"|"revertida" }. Se RE-EVALÚA en el chequeo semanal sin ayuda
      (evento "chequeo"): si no acierta ni un ítem, vuelve a práctica (revertida); si acierta alguno, queda confirmada.
      El chequeo semanal da prioridad a las pendientes.
   3) Aporta al informe para adultos: mediana de rt por habilidad y qué se saltó y por qué.
   Ganchos del motor que usa: Gioval.emit("dominada"), Gioval.emit("chequeo"), elegirChequeo() y lineasInforme(). */
Gioval.dominio = (function () {
  /* Textos del informe para adultos (agrupados para traducir) */
  const TXT = {
    tiempo: "   Tiempo de respuesta típico: {seg} s (mediana de {n} aciertos al primer intento)",
    saltoRapido: "domino rápido: {n} intentos, {ac}% al primer intento, mediana {seg} s en «{hab}»",
    saltoLinea: "   Saltada el {fecha} ({por}): {why}.",
    estado: { pendiente: "Todavía no se comprobó sin ayuda.", confirmada: "Comprobada sin ayuda el {fecha}: ¡se mantiene!", revertida: "Se comprobó el {fecha} y no salió: volvió a práctica.", anulada: "Se anuló el {fecha} al cambiar el punto de partida." },
    por: { rapido: "dominio rápido", ubicacion: "juego de ubicación", preguntas: "preguntas iniciales" }
  };
  const f = (s, v) => s.replace(/\{(\w+)\}/g, (m, k) => v[k] != null ? v[k] : m);
  const fecha = t => new Date(t).toLocaleDateString("es-AR");
  const mediana = a => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const seg = ms => (Math.round(ms / 100) / 10).toString().replace(".", ",");
  const eventos = id => (store.log[KID] || []).filter(e => e.s === id);
  const packDe = sk => Gioval.islas.lista.find(p => p.skills.includes(sk));
  const D = {
    TXT, mediana, seg,
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
    marcarSaltada(sk, por, why, desde) {
      const st = SK(sk.id); if (st.mast) return false;
      st.mast = true; st.box = 1; st.due = Date.now() + DAY; st.score = Math.max(st.score, .9);
      st.skip = { t: Date.now(), por, why, estado: "pendiente" }; if (desde) st.skip.desde = desde;
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
      D.marcarSaltada(sig, "rapido", f(TXT.saltoRapido, { n: d.n, ac: Math.round(d.ac * 100), seg: seg(d.med), hab: sk.name }), sk.id);
      return sig;
    },
    /* gancho del chequeo semanal: arma los ítems (máx. 10) dando prioridad a las habilidades saltadas pendientes */
    elegirChequeo(items) {
      const pack = PACK, pend = new Set(D.pendientes(pack).map(s => s.id));
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
      if (rts.length >= 3) out.push(f(TXT.tiempo, { seg: seg(mediana(rts)), n: rts.length }));
      if (st.skip) {
        const k = st.skip;
        out.push(f(TXT.saltoLinea, { fecha: fecha(k.t), por: TXT.por[k.por] || k.por, why: k.why }));
        out.push("   " + f(TXT.estado[k.estado] || "", { fecha: k.tCheq ? fecha(k.tCheq) : "" }));
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
