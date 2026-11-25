"use strict";
/* ============ ISLA NÚMEROS: preguntas iniciales, test de ubicación y punto de partida ============
   Se carga ANTES de js/islas/numeros.js (que registra la isla y le pasa a Gioval.islas los ganchos de acá).
   Los datos y los textos (tablas de idiomas, claves numeros.ed.*) están en js/datos/numeros.js; la regla completa, explicada para personas, en
   gioval-dev/docs/NUMEROS_EDADES.md. Todo esto lo maneja un ADULTO desde el panel ⚙️ (detrás del candado),
   salvo el test de ubicación, que juega el niño con voz y sin presión.

   MODELO
   · store.intake[niño] = { v:1, creado, edad, resp:{cuenta,reconoce,suma,resta,mult} (null = "No sé"),
                             ubicacion?: resultado del test, pendiente?: true, inicio?: punto de partida aceptado }
   · Estado de cada habilidad en el punto de partida:  "saltada" (ya la domina: queda dominada, con skip.por/motivo, y se vuelve a
     comprobar en el próximo chequeo semanal sin ayuda) · "encurso" (se practica ya, con menos ayuda, para confirmar)
     · "no" (todavía no: es "abierta" si todos sus requisitos están saltados —se puede aprender ahora— o "cerrada").
   REGLA (sin test):  1) cada respuesta del adulto nombra habilidades que "domina"; "No sé" usa lo típico por edad (conservador).
     2) se suman los requisitos de cada una (si domina la de arriba, domina las bases).
     3) las que son la punta de su rama (ninguna otra habilidad dominada depende de ellas) quedan EN CURSO; las demás, SALTADAS.
   REGLA (con test): las probadas y aprobadas quedan saltadas (y sus bases); las probadas y falladas (y lo que depende de ellas)
     dejan de contar aunque el adulto las haya dicho: quedan en curso si tuvieron algún acierto, y si no, "todavía no";
     la más alta aprobada de cada rama, si se respondió con lentitud (mediana sobre el umbral `rapido.rt`), queda en curso y no saltada;
     lo que no se probó sigue la regla anterior. */
Gioval.numeros = (function () {
  const DN = Gioval.datos.numeros, ESCALA = DN.ESCALA, EJES = DN.EJES, IN = DN.INTAKE, UB = DN.UBICACION;
  const POR = new Map(ESCALA.map(s => [s.id, s]));
  const ORDEN = new Map(ESCALA.map((s, i) => [s.id, i]));
  const esc = t => String(t).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const sk = id => POR.get(id);

  /* ---------- grafo de requisitos ---------- */
  const _anc = new Map();
  function ancestros(id) {
    if (_anc.has(id)) return _anc.get(id);
    const out = new Set(); (function rec(x) { sk(x).req.forEach(r => { if (!out.has(r)) { out.add(r); rec(r); } }); })(id);
    _anc.set(id, out); return out;
  }
  const depende = (z, id) => ancestros(z).has(id);
  function cerrar(ids) { const out = new Set(); ids.forEach(id => { if (POR.has(id)) { out.add(id); ancestros(id).forEach(a => out.add(a)); } }); return out; }
  const mediana = a => Gioval.dominio.mediana(a);

  /* ---------- 1) preguntas iniciales → habilidades que "domina" ---------- */
  function respuestaEfectiva(resp, edad) {
    const def = IN.defecto[edad] || null, valores = {}, deEdad = {};
    IN.preguntas.forEach(p => { const v = resp ? resp[p.id] : null; if (v == null) { valores[p.id] = def ? def[p.id] : 0; deEdad[p.id] = true; } else valores[p.id] = v; });
    return { valores, deEdad };
  }
  function reclamos(resp, edad) {
    const ef = respuestaEfectiva(resp, edad), ids = [];
    IN.preguntas.forEach(p => { const o = p.opciones.find(x => x.v === ef.valores[p.id]); if (o) ids.push(...o.domina); });
    return new Set(ids);
  }

  /* ---------- 2) plan: estado de cada habilidad ---------- */
  function resumenItems(registros, id) {
    const r = (registros || []).filter(x => x.s === id), ok = r.filter(x => x.ok);
    return { n: r.length, ok: ok.length, med: mediana(ok.filter(x => typeof x.rt === "number").map(x => x.rt)) };
  }
  function calcularPlan(reclamados, test) {
    test = test || { pasados: [], fallados: [], parcial: {}, registros: [] };
    const D = cerrar(reclamados), pass = new Set(), por = {}, de = {}, ev = {};
    test.pasados.forEach(id => { pass.add(id); por[id] = "ubicacion"; ev[id] = resumenItems(test.registros, id); });
    test.pasados.forEach(id => ancestros(id).forEach(a => { if (!pass.has(a)) { pass.add(a); por[a] = "implicita"; de[a] = id; } }));
    /* aprobó la más alta de su rama pero LENTO (mediana sobre el umbral de la habilidad): la conoce pero no con fluidez → en curso, no saltada */
    const puntas = test.pasados.filter(id => !test.pasados.some(o => o !== id && depende(o, id)));
    const lentas = new Set(puntas.filter(id => { const m = ev[id] && ev[id].med; return m != null && sk(id).rapido && m > sk(id).rapido.rt; }));
    const bloq = id => test.fallados.some(f => f === id || depende(id, f));
    const Dp = [...D].filter(id => !pass.has(id) && !bloq(id));
    const U = new Set([...pass, ...Dp]), estados = {};
    ESCALA.forEach(s => {
      const id = s.id;
      if (pass.has(id)) estados[id] = lentas.has(id) ? "encurso" : "saltada";
      else if (Dp.includes(id)) {
        const sobre = ESCALA.some(z => z.id !== id && U.has(z.id) && z.req.includes(id));
        if (sobre) { estados[id] = "saltada"; if (reclamados.has(id)) por[id] = "adulto"; else { por[id] = "implicita"; de[id] = ESCALA.find(z => U.has(z.id) && z.id !== id && depende(z.id, id)).id; } }
        else { estados[id] = "encurso"; por[id] = "adulto"; }
      } else if (test.fallados.includes(id) && (test.parcial || {})[id] >= 1) { estados[id] = "encurso"; por[id] = "ubicacion"; }
      else estados[id] = "no";
    });
    return { estados, por, de, ev };
  }
  const practicables = estados => ESCALA.filter(s => estados[s.id] !== "saltada" && s.req.every(r => estados[r] === "saltada"));
  const empiezaEn = estados => { const p = practicables(estados); return p.length ? p[0] : null; };
  const etiquetaNo = (estados, id) => sk(id).req.every(r => estados[r] === "saltada") ? "abierta" : "cerrada";
  const contar = (estados, e) => ESCALA.filter(s => estados[s.id] === e).length;
  /* cambio manual de un adulto: arrastra requisitos o dependientes para que el plan siga siendo coherente */
  function cambiar(estados, id, nuevo) {
    estados[id] = nuevo;
    if (nuevo === "saltada") ancestros(id).forEach(a => { estados[a] = "saltada"; });
    else ESCALA.forEach(z => { if (z.id !== id && estados[z.id] === "saltada" && depende(z.id, id)) estados[z.id] = "no"; });
    return estados;
  }

  /* ---------- 3) test de ubicación: escalera adaptativa (lógica pura, sin pantalla) ---------- */
  function crearEscalera(reclamados) {
    const D = cerrar(reclamados);
    const ejes = EJES.map(e => { let top = -1; e.cadena.forEach((id, i) => { if (D.has(id)) top = i; });
      return { id: e.id, cadena: e.cadena, necesita: e.necesita, idx: Math.max(0, top), tally: {}, mejor: -1, techo: Infinity, fallosSeguidos: 0, items: 0, fin: false, omitido: false }; });
    return { D, ejes, nItems: 0, registros: [], pasados: new Set(), fallados: new Set(), t0: Date.now() };
  }
  /* ¿se puede dar por sabida esta habilidad para habilitar un eje? (aprobada o ancestro de una aprobada, o dicha por el adulto y no refutada) */
  function superado(U, id) {
    const cierre = new Set(); U.pasados.forEach(p => { cierre.add(p); ancestros(p).forEach(a => cierre.add(a)); });
    if (cierre.has(id)) return true;
    if (!U.D.has(id)) return false;
    for (const f of U.fallados) if (f === id || depende(id, f)) return false;
    return true;
  }
  function proximo(U) {
    if (U.nItems >= UB.maxItems) return null;
    for (const e of U.ejes) {
      if (e.fin) continue;
      if (e.necesita && !superado(U, e.necesita)) { e.fin = true; e.omitido = true; continue; }
      return { eje: e, id: e.cadena[e.idx] };
    }
    return null;
  }
  /* un nivel se aprueba con 2 aciertos al primer intento; con 2 errores se falla; con 1 y 1 se pide un 3.er ítem.
     Si aprueba: sube un nivel (hasta el primer nivel fallado). Si falla: baja, y cada fallo seguido baja un nivel más
     (1, 2, 3…) para encontrar rápido dónde sí puede, hasta un nivel aprobado o el piso; los niveles de en medio se prueban después. */
  function registrar(U, e, id, ok, rt) {
    U.registros.push({ s: id, ok: !!ok, rt: typeof rt === "number" ? rt : null });
    U.nItems++; e.items++;
    const L = e.tally[e.idx] || (e.tally[e.idx] = []); L.push(!!ok);
    const bien = L.filter(Boolean).length, mal = L.length - bien;
    if (bien >= UB.itemsPorNivel) {
      e.mejor = Math.max(e.mejor, e.idx); U.pasados.add(id); e.fallosSeguidos = 0;
      const nx = e.idx + 1;
      if (nx >= e.cadena.length || nx >= e.techo || e.items >= UB.maxItemsPorEje) e.fin = true; else e.idx = nx;
    } else if (mal >= UB.itemsPorNivel) {
      e.techo = Math.min(e.techo, e.idx); U.fallados.add(id); e.fallosSeguidos++;
      let nx = Math.max(0, e.idx - e.fallosSeguidos);
      while (nx < e.idx && e.tally[nx]) nx++;
      if (nx >= e.idx || nx <= e.mejor || e.items >= UB.maxItemsPorEje) e.fin = true; else e.idx = nx;
    } else if (e.items >= UB.maxItemsPorEje) e.fin = true;
  }
  function resultado(U, fin) {
    const parcial = {}; U.fallados.forEach(id => { parcial[id] = U.registros.filter(r => r.s === id && r.ok).length; });
    const ejes = {}; U.ejes.forEach(e => { ejes[e.id] = { mejor: e.mejor >= 0 ? e.cadena[e.mejor] : null, techo: e.techo < Infinity ? e.cadena[e.techo] : null, omitido: e.omitido, items: e.items }; });
    return { t: Date.now(), fin, durMs: Date.now() - U.t0, registros: U.registros.slice(), pasados: [...U.pasados], fallados: [...U.fallados], parcial, ejes };
  }
  /* simulación sin pantalla: responder(id, k) → {ok, rt}. La usan las pruebas automáticas. */
  function simular(reclamados, responder) {
    const U = crearEscalera(reclamados), cuenta = {};
    for (let g = 0; g < 500; g++) { const x = proximo(U); if (!x) break; const k = cuenta[x.id] = (cuenta[x.id] || 0) + 1; const r = responder(x.id, k); registrar(U, x.eje, x.id, r.ok, r.rt); }
    return resultado(U, U.nItems >= UB.maxItems ? "items" : "completo");
  }

  /* ---------- 4) aplicar el punto de partida al progreso ---------- */
  function limpiarSalto(id) {
    const st = SK(id); if (st.skip && st.skip.estado === "pendiente") { st.mast = false; st.box = 0; st.due = 0; delete st.skip; }
  }
  /* el motivo se guarda como { k: clave, p: datos } y se escribe en el idioma de quien lee el informe (ver Gioval.dominio.motivo) */
  function motivoTexto(id, por, de, ev) {
    if (por === "ubicacion") { const e = ev || {}; return { k: "numeros.ed.motivos.ubicacion", p: { ok: e.ok != null ? e.ok : "?", n: e.n != null ? e.n : "?", mediana: e.med != null ? e.med : null } }; }
    if (por === "implicita") return { k: "numeros.ed.motivos.implicita", p: { de: de || "?" } };
    return { k: "numeros.ed.motivos." + por, p: {} };
  }
  function aplicar(estados, por, de, ev) {
    ESCALA.forEach(s => {
      const id = s.id, st = SK(id), e = estados[id];
      if (e === "saltada") { if (!st.mast) Gioval.dominio.saltar(id, por[id] || "adulto", { motivo: motivoTexto(id, por[id] || "adulto", de[id], ev[id]), de: de[id] || null, ev: ev[id] || null }); }
      else { limpiarSalto(id); if (e === "encurso" && !st.mast && st.att === 0) st.lvl = Math.max(st.lvl, 1); }
    });
  }

  /* ---------- 5) pantallas para el adulto ---------- */
  const O = (id) => document.getElementById(id);
  const cerrarOverlay = id => O(id).classList.remove("show");
  const guardado = () => store.intake[KID];
  function nombreHab(id) { return sk(id).name; }

  function intakeHTML(I) {
    const edad = I ? I.edad : null, resp = I ? I.resp : {};
    const sel = (id, opts, val) => `<select id="${id}">${opts.map(o => `<option value="${o.v == null ? "" : o.v}"${(o.v == null ? val == null : o.v === val) ? " selected" : ""}>${esc(o.t)}</option>`).join("")}</select>`;
    const T = (c, p) => esc(t("numeros.ed.intake." + c, p)), noSe = { v: null, t: t("numeros.ed.intake.no_se") };
    let h = `<h3>${T("titulo", { nombre: KID })}</h3><p>${T("intro")}</p>`;
    h += `<div class="nfila"><label for="ni_edad"><b>${T("edad")}</b></label>${sel("ni_edad", [noSe].concat(IN.edades.map(e => ({ v: e, t: t("numeros.ed.intake.edades." + e) }))), edad)}</div>`;
    IN.preguntas.forEach(p => { h += `<div class="nfila"><label for="ni_${p.id}"><b>${T(p.id + ".texto")}</b></label>${sel("ni_" + p.id, [noSe].concat(p.opciones.map(o => ({ v: o.v, t: t("numeros.ed.intake." + p.id + ".o" + o.v) }))), resp ? resp[p.id] : null)}</div>`; });
    h += `<p class="note-hint">${T("aviso")}</p><div class="nbtns"><button class="btn" id="niVer">${T("ver")}</button><button class="btn alt" id="niCancelar">${T("cancelar")}</button></div>`;
    return h;
  }
  function abrirIntake() {
    if (!KID) return;
    $("panel").classList.remove("show");
    O("numIntakeCard").innerHTML = intakeHTML(guardado() || null);
    O("numIntake").classList.add("show");
    O("niCancelar").onclick = () => cerrarOverlay("numIntake");
    O("niVer").onclick = () => {
      const num = id => { const v = O(id).value; return v === "" ? null : +v; };
      const resp = {}; IN.preguntas.forEach(p => { resp[p.id] = num("ni_" + p.id); });
      const prev = guardado() || {};
      store.intake[KID] = { v: IN.version, creado: prev.creado || Date.now(), edad: num("ni_edad"), resp, inicio: prev.inicio || undefined };
      if (!store.intake[KID].inicio) delete store.intake[KID].inicio;
      save(); cerrarOverlay("numIntake"); mostrarResumen("intake");
    };
  }

  let VISTA = null;   // { origen, estados, por, de, ev, base (estados calculados), test }
  function mostrarResumen(origen) {
    const I = guardado(); if (!I) return abrirIntake();
    const test = (origen === "test" || (origen === "ver" && I.pendiente)) ? (I.ubicacion || null) : null;
    let estados, por, de, ev;
    if (origen === "ver" && I.inicio && !I.pendiente) { estados = Object.assign({}, I.inicio.estados); por = Object.assign({}, I.inicio.por); de = Object.assign({}, I.inicio.de || {}); ev = {}; }
    else { const pl = calcularPlan(reclamos(I.resp, I.edad), test); estados = pl.estados; por = pl.por; de = pl.de; ev = pl.ev; }
    VISTA = { origen: test ? "test" : origen, estados, por, de, ev, base: Object.assign({}, estados), test };
    dibujarResumen();
    O("numResumen").classList.add("show");
  }
  function dibujarResumen() {
    const V = VISTA, E = V.estados, I = guardado();
    const ini = empiezaEn(E), nS = contar(E, "saltada"), nC = contar(E, "encurso");
    const R = (c, p) => t("numeros.ed.resumen." + c, p), Re = (c, p) => esc(R(c, p));
    let h = `<h3>${Re(V.origen === "test" ? "titulo_test" : "titulo_intake", { nombre: KID })}</h3>`;
    h += `<p class="nbig">${ini ? R("empieza", { inicio: esc(ini.name) }) : Re("empieza_todo")}<br>${Re("saltadas", { n: nS })}<br>${Re("encurso", { n: nC })}</p>`;
    if (V.test) {
      const reg = V.test.registros, ok = reg.filter(x => x.ok), med = mediana(ok.filter(x => typeof x.rt === "number").map(x => x.rt));
      h += `<p>${Re("test", { ok: ok.length, n: reg.length, mediana: med != null ? Gioval.dominio.seg(med) : "–" })}` + (V.test.fin !== "completo" ? " " + Re("test_corto", { motivo: R(V.test.fin === "tiempo" ? "motivo_tiempo" : "motivo_items") }) : "") + `</p>`;
    }
    h += `<p class="note-hint">${Re("explica")}</p>`;
    EJES.forEach(eje => {
      h += `<div class="neje">${esc(t("numeros.ed.ejes." + eje.id.toLowerCase()))}</div>`;
      ESCALA.filter(s => s.eje === eje.id).forEach(s => {
        const e = E[s.id], extra = e === "no" ? R("etiqueta." + etiquetaNo(E, s.id)) : (V.por[s.id] ? R("origen." + V.por[s.id]) : "");
        h += `<div class="nrow"><div class="nn"><span class="ni">${s.icon}</span> ${esc(s.name)}<small>${esc(extra || "")}</small></div><select data-id="${s.id}" class="nsel e-${e}">${["saltada", "encurso", "no"].map(o => `<option value="${o}"${o === e ? " selected" : ""}>${Re("estados." + o)}</option>`).join("")}</select></div>`;
      });
    });
    h += `<div class="nbtns"><button class="btn" id="nrAceptar">${Re("aceptar")}</button></div><div class="nbtns2">`;   /* solo "Aceptar" queda fijo abajo: en 360x700 los otros botones taparían la lista */
    if (V.origen === "intake" || V.origen === "ver") h += `<button class="btn alt" id="nrTest">${Re("hacer_test", { nombre: KID })}</button><button class="btn alt" id="nrResp">${Re("cambiar_resp")}</button>`;
    h += `<button class="btn alt" id="nrVolver">${Re("volver")}</button></div>`;
    O("numResumenCard").innerHTML = h;
    O("numResumenCard").querySelectorAll("select.nsel").forEach(sel => { sel.onchange = () => { cambiar(V.estados, sel.dataset.id, sel.value); V.por[sel.dataset.id] = "manual"; dibujarResumen(); }; });
    O("nrVolver").onclick = () => cerrarOverlay("numResumen");
    O("nrAceptar").onclick = aceptar;
    if (O("nrTest")) O("nrTest").onclick = () => { cerrarOverlay("numResumen"); iniciarTest(); };
    if (O("nrResp")) O("nrResp").onclick = () => { cerrarOverlay("numResumen"); abrirIntake(); };
  }
  function aceptar() {
    const V = VISTA, I = guardado(); if (!I) return;
    const ajustes = ESCALA.filter(s => V.estados[s.id] !== V.base[s.id]).map(s => s.id);
    aplicar(V.estados, V.por, V.de, V.ev);
    const ini = empiezaEn(V.estados);
    I.inicio = { t: Date.now(), estados: Object.assign({}, V.estados), por: Object.assign({}, V.por), de: Object.assign({}, V.de), ajustes, empiezaEn: ini ? ini.id : null,
      saltadas: contar(V.estados, "saltada"), encurso: contar(V.estados, "encurso"), origen: V.origen };
    delete I.pendiente; save();
    cerrarOverlay("numResumen"); actualizarPanel();
    setBubble(t("numeros.ed.resumen.aceptado", { nombre: KID }));
  }

  /* ---------- 6) el test de ubicación que juega el niño ---------- */
  function iniciarTest() {
    if (!KID || !guardado()) return;
    const pack = PACKS.find(p => p.id === "numeros"); PACK = pack;
    $("panel").classList.remove("show");
    const kid = KID, I = guardado(), U = crearEscalera(reclamos(I.resp, I.edad));
    let pend = null;
    const guia = {
      siguiente(run) {
        if (pend) { registrar(U, pend.eje, pend.id, false, null); pend = null; }   /* "Seguir ➜" sin responder cuenta como "no sé" */
        const x = proximo(U), tiempo = Date.now() - U.t0 > UB.maxMs;
        if (!x || tiempo) return terminar(run, U, kid, tiempo ? "tiempo" : (U.nItems >= UB.maxItems ? "items" : "completo"));
        const s = sk(x.id), it = ACTIVITIES[s.type].make(s); pend = { eje: x.eje, id: x.id };
        return Gioval.dominio.jugarItem(run, it, UB.ayuda);
      },
      async respuesta(run, it, res) {
        const p = pend; pend = null; if (!p) return;
        const ok = res.miss === 0; registrar(U, p.eje, p.id, ok, res.rt); Gioval.dominio.marcar(ok);
        setBubble(rnd(tl("numeros.ed.ubic.siguientes"))); await sleep(450); if (run !== S.run) return; guia.siguiente(run);
      },
    };
    Gioval.dominio.iniciarGuiada({ titulo: t("numeros.ed.ubic.titulo"), saludo: t("numeros.ed.ubic.saludo", { nombre: kid }), guia });
  }
  async function terminar(run, U, kid, motivo) {
    S.mode = "done"; S.onDone = null;
    const test = resultado(U, motivo), I = store.intake[kid]; I.ubicacion = test; I.pendiente = true; save();
    S.finMode = "ubic"; $("finStars").textContent = "🌱"; $("finTitle").textContent = t("numeros.ed.ubic.fin_titulo");
    $("btnFinOk").textContent = t("numeros.ed.ubic.boton_adulto"); $("btnFinHome").textContent = t("numeros.ed.ubic.boton_mapa");
    S.finOk = () => { resetFlow(); goMenuIsla(); gate(() => mostrarResumen("test")); };
    S.finHome = () => { resetFlow(); goMap(); };
    $("finish").classList.add("show"); actualizarPanel();
    await speak(t("numeros.ed.ubic.fin_voz", { nombre: kid }));
  }

  /* ---------- 7) panel de adultos e informe ---------- */
  function estadoPanel(kid) {
    const I = kid ? store.intake[kid] : null, P = (c, p) => t("numeros.ed.panel." + c, p);
    if (!I) return P("sin", { nombre: kid || "…" });
    if (I.pendiente) return P("pendiente");
    if (!I.inicio) return P("respuestas");
    const ini = I.inicio.empiezaEn ? sk(I.inicio.empiezaEn) : null;
    return ini ? P("aceptado", { inicio: ini.name, saltadas: I.inicio.saltadas, encurso: I.inicio.encurso }) : P("completo");
  }
  function actualizarPanel() { const el = O("numInicioEstado"); if (el) el.textContent = estadoPanel(KID); }
  function informeInicio(kid) {
    const I = store.intake[kid], N = (c, p) => t("numeros.ed.informe." + c, p), out = [];
    const tieneProgreso = ESCALA.some(s => { const x = store.sk[kid + "|" + s.id]; return x && (x.att || x.mast); });
    if (!I) return tieneProgreso ? [N("titulo"), N("sin")] : [];
    const loc = Gioval.i18n.meta().locale, minus = x => x.charAt(0).toLocaleLowerCase(loc) + x.slice(1);
    out.push(N("titulo"), I.edad ? N("edad", { edad: I.edad }) : N("edad_no_se"));
    const lista = IN.preguntas.map(p => { const v = (I.resp || {})[p.id], o = p.opciones.find(x => x.v === v); return N("resp_item", { corto: t("numeros.ed.intake." + p.id + ".corto"), t: o ? minus(t("numeros.ed.intake." + p.id + ".o" + o.v)) : N("no_se") }); });
    out.push(N("resp", { lista: lista.join("; ") }));
    if (I.ubicacion) {
      const u = I.ubicacion, ok = u.registros.filter(x => x.ok), med = mediana(ok.filter(x => typeof x.rt === "number").map(x => x.rt));
      out.push(N("test", { fecha: Gioval.dominio.fecha(u.t), n: u.registros.length, ok: ok.length, pct: Gioval.dominio.pct(ok.length, u.registros.length), mediana: med != null ? Gioval.dominio.seg(med) : "–" }));
      const ejes = EJES.map(e => { const x = u.ejes[e.id], nombre = t("numeros.ed.ejes." + e.id.toLowerCase()); return !x || x.omitido ? N("test_eje_omitido", { eje: nombre }) : x.mejor ? N("test_eje", { eje: nombre, skill: nombreHab(x.mejor) }) : N("test_eje_nada", { eje: nombre }); });
      out.push(N("test_ejes", { lista: ejes.join("; ") }));
    }
    if (I.inicio) {
      const ini = I.inicio.empiezaEn ? nombreHab(I.inicio.empiezaEn) : "—";
      out.push(N("inicio", { fecha: Gioval.dominio.fecha(I.inicio.t), inicio: ini, saltadas: I.inicio.saltadas, encurso: I.inicio.encurso }));
      if (I.inicio.ajustes && I.inicio.ajustes.length) out.push(N("ajustes", { n: I.inicio.ajustes.length }));
    }
    return out;
  }

  /* ---------- 8) piezas que se enchufan en la isla ---------- */
  const dom = {
    pantallas: `<div class="big" id="numIntake"><div class="ncard" id="numIntakeCard"></div></div><div class="big" id="numResumen"><div class="ncard" id="numResumenCard"></div></div>`,
    panelPie: `<div style="margin-top:8px"><button class="btn alt" id="btnNumInicio" style="padding:6px 14px;font-size:16px" data-i18n="numeros.ed.panel.boton">🔢 Números: punto de partida</button><div class="psum" id="numInicioEstado"></div></div>`,
  };
  function iniciar() {
    O("btnNumInicio").onclick = () => { if (!KID) return; const I = guardado(); if (!I) abrirIntake(); else mostrarResumen(I.pendiente ? "test" : (I.inicio ? "ver" : "intake")); $("panel").classList.remove("show"); };
    Gioval.on("panel", actualizarPanel);
  }

  return { dom, iniciar, informeInicio, estadoPanel,
    /* API pura (la usan las pruebas) */
    api: { ancestros, cerrar, reclamos, respuestaEfectiva, calcularPlan, practicables, empiezaEn, cambiar, crearEscalera, proximo, registrar, resultado, simular, aplicar, etiquetaNo, contar },
    abrirIntake, mostrarResumen, iniciarTest };
})();
