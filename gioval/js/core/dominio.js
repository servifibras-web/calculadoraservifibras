"use strict";
/* ============ DOMINIO RÁPIDO, SALTOS Y SESIONES GUIADAS (genérico) ============
   Este archivo no nombra ninguna isla. Una isla activa estas funciones solo con datos en sus habilidades:

     { id:"x", ..., rapido:{ rt:4000, salta:["y","z"] } }

   - rt: umbral en milisegundos. El tiempo de respuesta (rt) lo mide el motor de toques (js/core/actividades.js) desde que la
     app termina de hablar hasta el acierto, y solo existe para ítems resueltos SIN errores (sin pistas ni ayudas tras fallar).
   - salta: habilidades que se pueden saltear si ésta se domina con fluidez.

   REGLA DE SALTO POR DOMINIO RÁPIDO (parámetros en Gioval.dominio.params, todos a revisar con datos reales):
     en los últimos `ventana` (10) intentos de aprender/repasar la habilidad:
       · hay al menos `minIntentos` (6) intentos,
       · al menos `minAciertos` (90 %) fueron al primer intento (sin pistas), y
       · la mediana del tiempo de respuesta de esos aciertos es menor que `rapido.rt`.
     Si se cumple y la habilidad ya está dominada, se saltean las habilidades de `salta` cuyos requisitos estén todos
     dominados y que casi no se hayan practicado (menos de 3 intentos). Una habilidad saltada queda dominada para destrabar
     lo que sigue, pero guarda `skip:{por,de,t,estado:"pendiente",motivo,ev}`: no tiene práctica propia.

   REEVALUACIÓN: en el próximo chequeo semanal (sin ayuda) cada habilidad saltada pendiente recibe `itemsChequeoSalto` (3) ítems
   (hasta `maxSaltadasPorChequeo` (4) habilidades por chequeo; van primero las "puntas": las que no son base de otra saltada, y entre ellas las más viejas). Se confirma con al menos 2/3 de aciertos;
   si no, VUELVE ATRÁS (deja de estar dominada) junto con las saltadas pendientes que dependan de ella. Si una saltada se
   confirma, las saltadas pendientes que son base suya (sus requisitos) quedan confirmadas por implicación.

   SESIONES GUIADAS: una isla puede jugar una secuencia propia (por ejemplo un test de ubicación) con
   Gioval.dominio.iniciarGuiada({titulo,saludo,guia}) donde guia={siguiente(run), respuesta(run,it,res)}. El motor solo muestra
   los ítems; los resultados no tocan el progreso (SK) ni el registro: los maneja la isla. */
Gioval.dominio = (function () {
  const P = { minIntentos: 6, minAciertos: 0.9, ventana: 10, itemsChequeoSalto: 3, maxSaltadasPorChequeo: 4, topeChequeo: 12, minChequeo: 2 };
  const habilidad = id => (PACK ? PACK.skills : Gioval.islas.habilidades()).find(s => s.id === id) || Gioval.islas.habilidades().find(s => s.id === id);
  const mediana = a => { if (!a.length) return null; const b = a.slice().sort((x, y) => x - y), m = b.length >> 1; return b.length % 2 ? b[m] : Math.round((b[m - 1] + b[m]) / 2); };
  const seg = ms => (ms / 1000).toFixed(1).replace(".", ",") + " s";
  const fecha = t => new Date(t).toLocaleDateString("es-AR");
  const pct = (a, n) => n ? Math.round(100 * a / n) + "%" : "–";

  /* últimos intentos de aprender/repasar (no del chequeo) de una habilidad */
  function datos(id) {
    const ev = (store.log[KID] || []).filter(e => e.s === id && e.k !== "check").slice(-P.ventana);
    const bien = ev.filter(e => e.f === 1);
    const rts = bien.filter(e => typeof e.rt === "number").map(e => e.rt);
    return { n: ev.length, aciertos: bien.length, rts, med: mediana(rts) };
  }
  function evaluar(sk) {
    const r = sk.rapido; if (!r) return { cumple: false };
    const d = datos(sk.id), tasa = d.n ? d.aciertos / d.n : 0;
    const cumple = d.n >= P.minIntentos && tasa >= P.minAciertos && d.rts.length >= P.minIntentos && d.med != null && d.med < r.rt;
    return { cumple, n: d.n, aciertos: d.aciertos, tasa, med: d.med, umbral: r.rt, nrt: d.rts.length };
  }

  function saltar(id, por, extra) {
    const st = SK(id); if (st.mast) return false;
    st.mast = true; st.box = 1; st.due = Date.now() + DAY; st.lvl = Math.max(st.lvl, 1);
    st.skip = Object.assign({ por, t: Date.now(), estado: "pendiente" }, extra || {});
    return true;
  }
  function revertir(id, chequeo) {
    const st = SK(id); if (!st.skip) return;
    st.mast = false; st.box = 0; st.due = 0; st.rec = [];
    st.skip.estado = "revertida"; st.skip.chequeo = chequeo || null;
  }
  const pendiente = st => !!(st && st.mast && st.skip && st.skip.estado === "pendiente");
  /* ¿z depende (transitivamente) de id? */
  function depende(z, id, skills) {
    const por = new Map(skills.map(s => [s.id, s])); const vistos = new Set();
    (function rec(x) { x.req.forEach(r => { if (!vistos.has(r)) { vistos.add(r); const y = por.get(r); if (y) rec(y); } }); })(z);
    return vistos.has(id);
  }

  /* gancho de motor.js (itemDone): devuelve las habilidades que se saltearon con este intento */
  function alResponder(sk, st) {
    const out = [];
    if (!sk.rapido || !st.mast || st.fast) return out;
    const ev = evaluar(sk); if (!ev.cumple) return out;
    st.fast = { t: Date.now(), n: ev.n, aciertos: ev.aciertos, med: ev.med, umbral: ev.umbral };
    (sk.rapido.salta || []).forEach(id => {
      const y = habilidad(id); if (!y) return;
      const sy = SK(id); if (sy.mast || sy.att >= 3) return;
      if (!y.req.every(r => SK(r).mast)) return;
      if (saltar(id, "rapido", { de: sk.id, ev: { n: ev.n, aciertos: ev.aciertos, med: ev.med, umbral: ev.umbral } })) out.push(y);
    });
    return out;
  }
  function mensajeSaltos(arr) {
    return "¡Respondiste con mucha seguridad! Por eso nos saltamos " + arr.map(s => "«" + s.name + "»").join(" y ") + " y vamos a lo que sigue.";
  }

  /* chequeo semanal: las saltadas pendientes van primero (con más ítems) */
  function armarChequeo(pack, items, makeItem) {
    const todas = pack.skills.filter(s => pendiente(SK(s.id)));
    const puntas = todas.filter(s => !todas.some(z => z !== s && depende(z, s.id, pack.skills)));   /* si pasa la de arriba, las bases quedan confirmadas */
    const pend = puntas.sort((a, b) => SK(a.id).skip.t - SK(b.id).skip.t).slice(0, P.maxSaltadasPorChequeo);
    if (!pend.length) return items;
    const ids = new Set(pend.map(s => s.id));
    const propios = []; pend.forEach(s => { for (let i = 0; i < P.itemsChequeoSalto; i++) propios.push(makeItem(s)); });
    const resto = items.filter(it => !ids.has(it.skill.id)).slice(0, Math.max(0, P.topeChequeo - propios.length));
    return shuffle(propios.concat(resto));
  }
  /* res = [{s, o}] del chequeo que terminó. Confirma o devuelve las saltadas pendientes que se evaluaron. */
  function alTerminarChequeo(pack, res) {
    const out = { confirmadas: [], volvieron: [] };
    pack.skills.forEach(s => {
      const st = SK(s.id); if (!pendiente(st)) return;
      const r = res.filter(x => x.s === s.id); if (r.length < P.minChequeo) return;
      const ok = r.filter(x => x.o).length, necesita = Math.ceil(r.length * 2 / 3), c = { d: today(), t: Date.now(), ok, n: r.length };
      if (ok >= necesita) {
        st.skip.estado = "confirmada"; st.skip.chequeo = c; out.confirmadas.push(s);
        pack.skills.forEach(a => { const sa = SK(a.id); if (a !== s && pendiente(sa) && depende(s, a.id, pack.skills)) { sa.skip.estado = "confirmada"; sa.skip.chequeo = { d: c.d, t: c.t, ok: 0, n: 0, porImplicacion: s.id }; out.confirmadas.push(a); } });
      }
      else { revertir(s.id, c); out.volvieron.push(s); }
    });
    /* si una vuelve atrás, las saltadas pendientes que dependen de ella (y no se evaluaron ahora) también */
    out.volvieron.slice().forEach(v => {
      pack.skills.forEach(z => { const sz = SK(z.id); if (pendiente(sz) && depende(z, v.id, pack.skills)) { revertir(z.id, { d: today(), t: Date.now(), ok: 0, n: 0, porDependencia: v.id }); out.volvieron.push(z); } });
    });
    return out;
  }
  function mensajeChequeo(rev) {
    if (rev.volvieron.length) return "Algunas cosas que nos habíamos saltado las vamos a practicar un poquito: ¡es parte de aprender!";
    return "Lo que nos habíamos saltado salió bien: ¡queda confirmado!";
  }

  /* ---- informe para adultos ---- */
  function motivo(s, st) {
    const k = st.skip; if (!k) return "";
    if (k.por === "rapido") {
      const de = habilidad(k.de), e = k.ev || {};
      return "por dominio rápido de «" + (de ? de.name : k.de) + "» (" + e.aciertos + " de " + e.n + " al primer intento, mediana " + (e.med != null ? seg(e.med) : "–") + ", umbral " + seg(e.umbral) + ")";
    }
    return k.motivo || ("origen: " + k.por);
  }
  function estadoSalto(st) {
    const k = st.skip, c = k.chequeo;
    if (k.estado === "pendiente") return "se reevalúa en el próximo chequeo semanal sin ayuda";
    if (k.estado === "confirmada") return "CONFIRMADA en el chequeo del " + fecha(c.t) + (c.porImplicacion ? " (porque aprobó otra más avanzada que la necesita)" : " (" + c.ok + "/" + c.n + ")");
    if (k.estado === "revertida") return "VOLVIÓ A PRÁCTICA" + (c && c.porDependencia ? " (depende de otra que falló)" : c ? " tras el chequeo del " + fecha(c.t) + " (" + c.ok + "/" + c.n + ")" : "");
    return k.estado;
  }
  /* líneas extra de una habilidad dentro del informe (tiempos y saltos) */
  function lineasInforme(s, st, ev) {
    const out = [];
    const rts = ev.filter(e => e.f === 1 && typeof e.rt === "number").map(e => e.rt);
    if (rts.length >= 3) out.push("   Tiempo de respuesta (mediana, aciertos sin pistas): " + seg(mediana(rts)) + " (n=" + rts.length + ")");
    if (st.skip) out.push("   Saltada " + motivo(s, st) + " → " + estadoSalto(st));
    return out;
  }
  /* sección "qué se saltó y por qué" */
  function lineasSaltos(packs) {
    const filas = [];
    packs.forEach(p => p.skills.forEach(s => { const st = SK(s.id); if (st.skip) filas.push({ s, st }); }));
    if (!filas.length) return [];
    const out = ["HABILIDADES SALTADAS (sin práctica propia) Y POR QUÉ"];
    filas.sort((a, b) => a.st.skip.t - b.st.skip.t).forEach(({ s, st }) => out.push("• " + s.name + " — " + motivo(s, st) + " (" + fecha(st.skip.t) + "). " + estadoSalto(st) + "."));
    return out;
  }

  /* ---- sesiones guiadas por la isla ---- */
  async function iniciarGuiada(o) {
    if (capLeft() <= 0) return showCap();
    ensureCtx(); S.run++; const run = S.run;
    if (PACK.antesDeSesion) PACK.antesDeSesion(); S.finMode = "session"; S.check = false; S.capShown = false;
    S.session = { items: [], i: 0, log: [], t0: Date.now(), streak: 0, newly: [], seen: {}, guia: o.guia };
    enterPlay(o.titulo);
    await speak(o.saludo);
    if (run === S.run) o.guia.siguiente(run);
  }
  /* muestra un ítem con el nivel de ayuda indicado; el resultado vuelve a guia.respuesta */
  function jugarItem(run, it, aid) {
    const ss = S.session; if (!ss || run !== S.run) return;
    S.reveal = false; S.kind = it.skill.type; S.hint = aid; S.mode = "demo";
    S.onDone = res => itemDone(run, it, res);
    ss.items[ss.i] = it; renderProg();
    return ACTIVITIES[it.skill.type].jugar(run, it, ss);
  }
  function marcar(ok) { const ss = S.session; if (!ss) return; ss.log[ss.i] = ok ? 1 : 2; ss.i++; renderProg(); }

  return { params: P, datos, evaluar, saltar, revertir, pendiente, depende, alResponder, mensajeSaltos, armarChequeo, alTerminarChequeo, mensajeChequeo,
    motivo, estadoSalto, lineasInforme, lineasSaltos, iniciarGuiada, jugarItem, marcar, mediana, seg, fecha, pct };
})();
