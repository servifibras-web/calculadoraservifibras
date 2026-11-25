"use strict";
/* ============ AYUDANTES DE LA CASA ("Hora de ayudantes") ============
   Cuando termina el tiempo diario de pantalla, la app ofrece tareas reales para la casa que un niño puede hacer,
   con cronómetro, para que se sienta útil. NO es una isla de aprendizaje: no se registra en Gioval.islas (no tiene
   habilidades, ni aparece en el mapa, ni entra en el informe). Se engancha al motor por tres ganchos genéricos:
     - Gioval.on("tope", d)       -> el motor avisa que se llegó al tope diario; acá se suma la frase y el botón
     - Gioval.tarjetasMenu        -> tarjeta "Hora de ayudantes" en el menú de la isla, solo cuando ya se llegó al tope
     - Gioval.on("panel")         -> redibuja la sección de la zona de adultos
   El TIEMPO DE AYUDANTES NO CUENTA COMO TIEMPO DE PANTALLA: el motor solo suma segundos en pantallas ".juego"
   (actividades de aprendizaje) y la pantalla #ayudantes no lo es.
   Textos y tareas: js/datos/tareas.js (TEXTOS arriba de todo; lista anotada para aprobación). Alarma: js/core/alarma.js
   (hora absoluta; ver docs/ALARMA.md y docs/AYUDANTES.md). Sin rachas, sin puntos, sin castigo.
   Lo que se guarda (lazy, dentro de store, viaja en el respaldo):
     store.ayud.cfg[perfil] = { on, edad, dur, off:[ids], asig:[ids], foto }     (configuración de adultos)
     store.ayud.reg[perfil] = [ { t, id, s, f? } ]                                (registro: cuándo, qué tarea, segundos, id de foto) */
(function () {
  const D = Gioval.datos.ayudantes, TAREAS = D.tareas, SUPS = D.supervision;
  const L = (k, p) => Gioval.i18n.t(k, p), LL = (k, p) => Gioval.i18n.tl(k, p); /* "t" y "tl" globales quedan libres para las variables locales */
  const KEY = Gioval.clave("gioval_ayudando");
    const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const porId = id => TAREAS.find(t => t.id === id);
  const sup = t => SUPS[t.supervision] || SUPS.adulto; /* si falta la supervisión se trata como la más estricta */

  /* ---------- configuración y registro (por perfil) ---------- */
  const DEF = { on: true, edad: 6, dur: 0, off: [], asig: [], foto: false };
  function cfg(kid) {
    const c = (store.ayud && store.ayud.cfg && store.ayud.cfg[kid]) || {};
    return Object.assign({}, DEF, c, { off: (c.off || []).slice(), asig: (c.asig || []).slice() });
  }
  function ponerCfg(kid, parche) {
    const a = store.ayud || (store.ayud = { cfg: {}, reg: {} }); a.cfg = a.cfg || {}; a.reg = a.reg || {};
    a.cfg[kid] = Object.assign(cfg(kid), parche); save();
  }
  function disponibles(kid) {
    const c = cfg(kid);
    const l = TAREAS.filter(t => c.asig.includes(t.id) || (!c.off.includes(t.id) && t.edadMin <= c.edad));
    return l.filter(t => c.asig.includes(t.id)).concat(l.filter(t => !c.asig.includes(t.id)));
  }
  const ofrece = kid => !!kid && cfg(kid).on && disponibles(kid).length > 0;
  const regDe = kid => (store.ayud && store.ayud.reg && store.ayud.reg[kid]) || [];
  function inicioSemana() { const d = new Date(Date.now()); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.getTime(); } /* lunes 00:00 */
  const vecesSemana = kid => regDe(kid).filter(e => e.t >= inicioSemana()).length;
  function registrar(kid, id, s) {
    const a = store.ayud || (store.ayud = { cfg: {}, reg: {} }); a.cfg = a.cfg || {}; a.reg = a.reg || {};
    const l = a.reg[kid] || (a.reg[kid] = []), e = { t: Date.now(), id, s };
    l.push(e); if (l.length > 300) l.splice(0, l.length - 300); save(); return e;
  }

  /* ---------- estado de la tarea en curso (sobrevive a una recarga) ---------- */
  let V = "lista", SEL = null, E = null, ULT = null; /* vista, tarea mirada, tarea en curso, última terminada */
  const persistir = () => { try { E && (E.estado === "corre" || E.estado === "tiempo") ? localStorage.setItem(KEY, JSON.stringify(E)) : localStorage.removeItem(KEY); } catch (e) {} };
  try {
    const g = JSON.parse(localStorage.getItem(KEY) || "null");
    if (g && porId(g.id) && Date.now() - g.tIni < 3 * 3600e3) E = g; else if (g) localStorage.removeItem(KEY);
  } catch (e) {}

  /* ---------- pantalla ---------- */
  $("app").insertAdjacentHTML("beforeend",
    `<div class="screen" id="ayudantes"><div class="bar"><button class="btn alt" id="ayBack"></button><h2 id="ayTitulo" style="margin:0"></h2><span id="ayEspacio" style="width:90px"></span></div><div id="ayBody"></div></div>`);
  const mmss = s => String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
  const minTxt = n => L("ayudantes.min", { n });
  const pasosHtml = (t, cls) => `<ol class="aySteps ${cls || ""}">${t.pasos.map(p => `<li>${esc(p)}</li>`).join("")}</ol>`;
  const avisoHtml = t => (t.aviso ? `<div class="ayAviso">⚠️ ${esc(t.aviso)}</div>` : "") + (t.supervision === "adulto" ? `<div class="ayAviso adulto">🧑‍🤝‍🧑 ${esc(L("ayudantes.aviso_adulto"))}</div>` : "");
  /* la tarea se lee en voz por partes (nombre y supervisión, cada paso, el aviso): el globito muestra la frase que suena */
  let LEE = 0;
  function partesLeidas(t) {
    return [L("ayudantes.leer_intro", { nombre: t.nombre, supervision: sup(t).voz })].concat(t.pasos.map((p, i) => L("ayudantes.leer_paso", { n: i + 1, paso: p })), t.aviso ? [L("ayudantes.leer_aviso", { aviso: t.aviso })] : []);
  }
  async function leer(t) {
    const mi = ++LEE;
    for (const p of partesLeidas(t)) { if (mi !== LEE) return; await speak(p); }
  }
  const dur = t => (cfg(KID).dur || t.minutos) * 60;

  function ir(v, id, hablar) { LEE++; V = v; if (id !== undefined) SEL = id; show("ayudantes"); render(); if (hablar) hablarVista(); }
  function hablarVista() {
    if (V === "lista") speak(L("ayudantes.elegi_voz"));
    else if (V === "detalle") leer(porId(SEL));
  }
  function render() {
    const b = $("ayBody"), t = porId(SEL || (E && E.id));
    $("ayTitulo").textContent = "🧹 " + L("ayudantes.hora_titulo");
    const back = $("ayBack"); back.innerHTML = `<span class="arr">⬅</span><span class="lbl">${L("app.volver")}</span>`;
    back.style.visibility = (V === "lista" || V === "detalle") ? "visible" : "hidden";
    b.className = "ay-" + V; $("ayudantes").dataset.v = V;
    if (V === "lista") {
      const ts = disponibles(KID), c = cfg(KID);
      b.innerHTML = ts.length ? `<div class="ayHint">${L("ayudantes.elegi")}</div><div class="ayGrid">${ts.map(x => {
        const asig = c.asig.includes(x.id), s = sup(x);
        return `<button class="ayCard${asig ? " asig" : ""}" data-id="${x.id}"><span class="em">${x.emoji}</span><span class="nm">${esc(x.nombre)}</span><small>⏱ ${minTxt(c.dur || x.minutos)} · ${s.icono} ${s.corto}</small>${asig ? `<small class="pin">${L("ayudantes.pedida")}</small>` : ""}</button>`;
      }).join("")}</div>` : `<div class="ayVacio">${L("ayudantes.vacio")}</div>`;
    } else if (V === "detalle") {
      const s = sup(t);
      b.innerHTML = `<div class="ayDet"><div class="ayDetHead"><span class="em">${t.emoji}</span><div><b>${esc(t.nombre)}</b><div class="ayChips"><span>⏱ ${minTxt(cfg(KID).dur || t.minutos)}</span><span>${s.icono} ${s.largo}</span></div></div></div>
        ${pasosHtml(t)}${avisoHtml(t)}
        <div class="ayAcc"><button class="btn alt" data-a="oir">${L("ayudantes.escuchar")}</button><button class="btn" data-a="empezar">${t.supervision === "adulto" ? L("ayudantes.empezar_adulto") : L("ayudantes.empezar", { n: cfg(KID).dur || t.minutos })}</button><button class="btn alt" data-a="lista"><span class="arr">⬅</span> ${L("ayudantes.otra_tarea")}</button></div></div>`;
    } else if (V === "corre") {
      b.innerHTML = `<div class="ayRun"><div class="ayRunMain"><div class="ayRunTarea"><span class="em">${t.emoji}</span> ${esc(t.nombre)}</div><div class="ayTime" id="ayTime" role="timer">${mmss(Alarma.restante())}</div><div class="ayBar"><i id="ayBarI"></i></div></div>
        <div class="ayRunSide">${pasosHtml(t, "sm")}<div class="ayAcc"><button class="btn" data-a="terminar">${L("ayudantes.terminar_pronto")}</button><button class="btn alt" data-a="oir">${L("ayudantes.escuchar")}</button><button class="btn alt" data-a="cancelar">${L("ayudantes.cancelar")}</button></div></div></div>`;
      pintarTiempo();
    } else if (V === "tiempo") {
      b.innerHTML = `<div class="ayRun"><div class="ayRunMain"><div class="ayTiempo">${L("ayudantes.tiempo_se_termino")}</div><div class="ayRunTarea"><span class="em">${t.emoji}</span> ${esc(t.nombre)}</div>${E && E.tarde > 5000 ? `<p class="ayTarde">${L("ayudantes.tiempo_tarde")}</p>` : ""}</div>
        <div class="ayRunSide"><div class="ayAcc col"><button class="btn" data-a="terminar">${L("ayudantes.termine")}</button><button class="btn alt" data-a="mas">${L("ayudantes.mas_tiempo")}</button></div></div></div>`;
    } else if (V === "fin") {
      const n = vecesSemana(KID), c = cfg(KID);
      b.innerHTML = `<div class="ayFin"><div class="ayStar">🌱</div><h1>${L("ayudantes.fin_titulo")}</h1><p id="ayElogio">${esc(ULT.elogio)}</p><p class="ayWeek">${L("ayudantes.semana", { n })}</p>
        ${c.foto ? `<button class="btn alt" data-a="foto" id="ayFotoBtn">${ULT.reg && ULT.reg.f ? L("ayudantes.foto_ok") : L("ayudantes.foto")}</button><input type="file" id="ayFotoIn" accept="image/*" capture="environment" style="display:none">` : ""}
        <div class="ayAcc"><button class="btn" data-a="lista">${L("ayudantes.otra_mas")}</button><button class="btn alt" data-a="salir">${L("ayudantes.listo")}</button></div></div>`;
    }
  }
  function pintarTiempo() {
    const el = $("ayTime"); if (!el || !E) return;
    const r = Alarma.restante(); el.textContent = mmss(r);
    const i = $("ayBarI"); if (i) i.style.width = Math.max(0, Math.min(100, 100 * (1 - r / E.total))) + "%";
  }

  /* ---------- flujo ---------- */
  function abrir() {
    if (!KID) return;
    $("capBox").classList.remove("show"); S.capShown = false; S.mode = "idle"; $("panel").classList.remove("show");
    resetFlow();
    if (E && E.kid === KID && (E.estado === "corre" || E.estado === "tiempo")) { ir(estadoVista(), undefined, false); return; }
    ir("lista", null, true);
  }
  function estadoVista() {
    if (E.estado === "corre" && !Alarma.activa()) { E.estado = "tiempo"; E.tarde = E.tarde || 0; persistir(); }
    return E.estado === "tiempo" ? "tiempo" : "corre";
  }
  function elegir(id) { ir("detalle", id, true); }
  function empezar(id) {
    const t = porId(id); if (!t) return;
    ensureCtx(); const seg = dur(t);
    escuchar(); Alarma.programar(seg, { titulo: L("ayudantes.alarma_titulo"), texto: L("ayudantes.alarma_texto", { nombre: t.nombre }) });
    E = { kid: KID, id, estado: "corre", tIni: Date.now(), total: seg, tarde: 0 }; persistir();
    ir("corre");
    const m = Math.round(seg / 60); speak(L("ayudantes.vamos", { n: m, nombre: t.nombre }));
  }
  function pedirEmpezar(id) {
    const t = porId(id); if (!t) return;
    if (t.supervision === "adulto") gate(() => empezar(id)); /* solo con un adulto: se pide la pregunta de adultos */
    else empezar(id);
  }
  function tiempoCumplido(tarde) {
    if (!E || E.estado !== "corre") return;
    E.estado = "tiempo"; E.tarde = tarde || 0; persistir();
    if ($("ayudantes").classList.contains("active")) { ir("tiempo"); speak(L("ayudantes.tiempo_voz")); }
  }
  function masTiempo() {
    if (!E) return; const t = porId(E.id), seg = D.masMinutos * 60;
    escuchar(); Alarma.programar(seg, { titulo: L("ayudantes.alarma_titulo"), texto: L("ayudantes.alarma_texto", { nombre: t.nombre }) });
    E.estado = "corre"; E.total = seg; E.tarde = 0; persistir(); ir("corre"); speak(L("ayudantes.mas_tiempo_voz"));
  }
  function terminar() {
    if (!E || E.estado === "fin") return;
    const e = E, kid = e.kid; Alarma.cancelar(); dejarDeEscuchar();
    const reg = registrar(kid, e.id, Math.round((Date.now() - e.tIni) / 1000));
    const c = cfg(kid); if (c.asig.includes(e.id)) ponerCfg(kid, { asig: c.asig.filter(x => x !== e.id) }); /* una tarea asignada se cumple una vez */
    ULT = { id: e.id, reg, elogio: rnd(LL("ayudantes.elogios")) }; E = null; persistir();
    ir("fin"); speak(L("ayudantes.fin_voz", { elogio: ULT.elogio, semana: L("ayudantes.semana", { n: vecesSemana(kid) }) }));
  }
  function cancelar() {
    Alarma.cancelar(); dejarDeEscuchar(); E = null; persistir(); ir("lista"); speak(L("ayudantes.cancelado"));
  }
  async function reducir(file) {
    const bm = await createImageBitmap(file), k = Math.min(1, 1280 / Math.max(bm.width, bm.height));
    const cv = document.createElement("canvas"); cv.width = Math.round(bm.width * k); cv.height = Math.round(bm.height * k);
    cv.getContext("2d").drawImage(bm, 0, 0, cv.width, cv.height);
    return await new Promise((ok, no) => cv.toBlob(b => b ? ok(b) : no(new Error("sin imagen")), "image/jpeg", .8));
  }
  async function guardarFoto(file) {
    if (!file || !ULT) return;
    let blob = file; try { blob = await reducir(file); } catch (e) {}
    const id = await Gioval.almacen.fotos.guardar(blob, { tipo: "ayudantes", kid: KID, tarea: ULT.id, t: Date.now() });
    if (ULT.reg) { ULT.reg.f = id; save(); }
    const b = $("ayFotoBtn"); if (b) b.textContent = L("ayudantes.foto_ok"); speak(L("ayudantes.foto_voz"));
  }

  $("ayBack").onclick = () => { if (V === "detalle") ir("lista", null, true); else goMenuIsla(); };
  $("ayBody").addEventListener("click", ev => {
    const card = ev.target.closest(".ayCard"); if (card) return elegir(card.dataset.id);
    const b = ev.target.closest("[data-a]"); if (!b) return;
    const a = b.dataset.a;
    if (a === "oir") { const t = porId(SEL || (E && E.id)); if (t) leer(t); }
    else if (a === "empezar") pedirEmpezar(SEL);
    else if (a === "lista") ir("lista", null, true);
    else if (a === "terminar") terminar();
    else if (a === "mas") masTiempo();
    else if (a === "cancelar") cancelar();
    else if (a === "salir") goMenuIsla();
    else if (a === "foto") $("ayFotoIn").click();
  });
  $("ayBody").addEventListener("change", ev => { if (ev.target.id === "ayFotoIn") guardarFoto(ev.target.files[0]); });

  /* ---------- alarma: hora absoluta, se revisa al volver a primer plano ---------- */
  /* Se escucha SOLO mientras hay una tarea en curso: un oyente permanente se llevaría el aviso de una alarma vencida que
     le corresponde a otro (Alarma entrega lo vencido al primer oyente que se registre). */
  let baja = null;
  const escuchar = () => { if (!baja) baja = Alarma.onFin(info => tiempoCumplido(info && info.tarde)); };
  const dejarDeEscuchar = () => { if (baja) { baja(); baja = null; } };
  if (E) escuchar();
  setInterval(() => { if (E && E.estado === "corre" && $("ayudantes").classList.contains("active")) { if (!Alarma.activa()) tiempoCumplido(0); else pintarTiempo(); } }, 250);
  document.addEventListener("visibilitychange", () => { if (!document.hidden && E && E.estado === "corre") { if (!Alarma.activa()) tiempoCumplido(0); else pintarTiempo(); } });
  /* si la app se cerró con una tarea en curso, al elegir de nuevo a ese niño se retoma */
  Gioval.on("mapa", () => { if (E && E.kid === KID) setTimeout(() => { if (E && E.kid === KID) { $("capBox").classList.remove("show"); estadoVista(); ir(E.estado === "tiempo" ? "tiempo" : "corre"); if (E.estado === "tiempo") speak(L("ayudantes.tiempo_voz")); else speak(L("ayudantes.en_curso", { nombre: porId(E.id).nombre })); } }, 0); });

  /* ---------- ganchos con el motor ---------- */
  Gioval.on("tope", d => {
    const acc = $("capAcc"); let b = $("capAyud");
    if (!b && acc) { b = document.createElement("button"); b.className = "btn"; b.id = "capAyud"; b.onclick = () => abrir(); acc.insertBefore(b, $("capOk")); }
    if (!b) return; const on = ofrece(d.kid);
    b.textContent = L("ayudantes.tope_boton"); b.style.display = on ? "" : "none"; if (on) d.extra = L("ayudantes.tope_extra");
  });
  Gioval.tarjetasMenu = Gioval.tarjetasMenu || [];
  Gioval.tarjetasMenu.push(done => (done && ofrece(KID)) ? [{ em: "🧹", t: L("ayudantes.hora_titulo"), s: L("ayudantes.tarjeta_sub"), on: true, go: () => abrir() }] : []);

  /* ---------- zona de adultos ---------- */
  $("panelPie").insertAdjacentHTML("beforeend", `<details id="ayPanel" class="ayPanel"><summary data-i18n="ayudantes.panel.titulo">${L("ayudantes.panel.titulo")}</summary><div id="ayPanelBody"></div></details>`);
  const refrescarMenu = () => { if ($("menuIsla").classList.contains("active")) renderMenuIsla(); };
  function estadoAlarma() {
    const wake = ("wakeLock" in navigator) ? L("ayudantes.panel.wake_si") : L("ayudantes.panel.wake_no");
    const perm = ("Notification" in window) ? Notification.permission : "no";
    const notif = perm === "granted" ? L("ayudantes.panel.notif_granted") : perm === "denied" ? L("ayudantes.panel.notif_denied") : perm === "default" ? L("ayudantes.panel.notif_default") : L("ayudantes.panel.notif_no");
    const nat = ((window.Capacitor && Capacitor.Plugins && Capacitor.Plugins.LocalNotifications) || (Gioval.alarmaNativa && Gioval.alarmaNativa.activa)) ? L("ayudantes.panel.nativa_si") : L("ayudantes.panel.nativa_no");
    return `<div class="ayAlarma"><b>${L("ayudantes.panel.alarma_titulo")}</b><div>${L("ayudantes.panel.alarma_detalle")}</div><ul><li>${wake}</li><li>${notif}${perm === "default" ? ` <button class="btn alt" data-p="permiso" style="padding:3px 10px;font-size:15px">${L("ayudantes.panel.permitir")}</button>` : ""}</li><li>${nat}</li></ul></div>`;
  }
  function renderPanel() {
    const box = $("ayPanelBody"); if (!box) return;
    if (!KID) { box.innerHTML = `<div class="note-hint">${L("ayudantes.panel.elegir_jugador")}</div>`; return; }
    const c = cfg(KID), reg = regDe(KID), desde = inicioSemana(), sem = reg.filter(e => e.t >= desde);
    const por = {}; sem.forEach(e => { por[e.id] = (por[e.id] || 0) + 1; });
    const detalle = Object.keys(por).map(id => (porId(id) ? porId(id).nombre : id) + " ×" + por[id]).join(", ");
    box.innerHTML = `
      <label class="ayChk"><input type="checkbox" id="ayOn" ${c.on ? "checked" : ""}> ${L("ayudantes.panel.activar")}</label>
      <div class="note-hint">${L("ayudantes.panel.aclaracion")}</div>
      <label>${L("ayudantes.panel.edad")} <select id="ayEdad" style="font-size:16px;padding:4px;border-radius:10px">${[4, 5, 6, 7, 8, 9, 10, 11, 12].map(n => `<option value="${n}" ${c.edad === n ? "selected" : ""}>${L("ayudantes.panel.anios", { n })}</option>`).join("")}</select></label>
      <label>${L("ayudantes.panel.duracion")} <select id="ayDur" style="font-size:16px;padding:4px;border-radius:10px"><option value="0" ${c.dur === 0 ? "selected" : ""}>${L("ayudantes.panel.duracion_tarea")}</option>${[3, 5, 10, 15, 20].map(n => `<option value="${n}" ${c.dur === n ? "selected" : ""}>${L("ayudantes.panel.duracion_min", { n })}</option>`).join("")}</select></label>
      <div class="note-hint">${L("ayudantes.panel.tareas")}</div>
      <div class="ayTareas">${TAREAS.map(t => `<div class="ayFila"><label><input type="checkbox" data-h="${t.id}" ${c.off.includes(t.id) && !c.asig.includes(t.id) ? "" : "checked"}> ${t.emoji} ${esc(t.nombre)} <small>(${L("ayudantes.panel.edad_desde", { n: t.edadMin })} · ${sup(t).icono} ${sup(t).corto})</small></label> <label class="pin" title="${esc(L("ayudantes.pedida"))}"><input type="checkbox" data-asig="${t.id}" ${c.asig.includes(t.id) ? "checked" : ""}>📌</label></div>`).join("")}</div>
      <label class="ayChk"><input type="checkbox" id="ayFoto" ${c.foto ? "checked" : ""}> ${L("ayudantes.panel.foto")}</label>
      <div style="margin-top:6px"><button class="btn" id="ayAbrir" style="padding:6px 14px;font-size:16px">${L("ayudantes.panel.abrir_ahora")}</button></div>
      <div class="psum" id="ayResumen">${sem.length ? (detalle ? L("ayudantes.panel.semana_detalle", { n: sem.length, detalle }) : L("ayudantes.panel.semana", { n: sem.length })) : L("ayudantes.panel.semana_nada")} <span id="ayFotos"></span></div>
      ${estadoAlarma()}`;
    Gioval.almacen.fotos.listar().then(l => { const n = l.filter(f => f.meta && f.meta.tipo === "ayudantes" && f.meta.kid === KID).length; const el = $("ayFotos"); if (el && n) el.textContent = L("ayudantes.panel.fotos", { n }); }).catch(() => {});
  }
  Gioval.on("panel", renderPanel);
  /* al cambiar el idioma se redibuja lo que esté a la vista (la pantalla, el panel y el botón del cartel de tope) */
  Gioval.on("idioma", d => {
    if (!d || !d.cambio) return;
    renderPanel(); const b = $("capAyud"); if (b) b.textContent = L("ayudantes.tope_boton");
    if ($("ayudantes").classList.contains("active")) render();
  });
  $("ayPanelBody").addEventListener("change", ev => {
    if (!KID) return; const el = ev.target, c = cfg(KID);
    if (el.id === "ayOn") ponerCfg(KID, { on: el.checked });
    else if (el.id === "ayEdad") ponerCfg(KID, { edad: +el.value });
    else if (el.id === "ayDur") ponerCfg(KID, { dur: +el.value });
    else if (el.id === "ayFoto") ponerCfg(KID, { foto: el.checked });
    else if (el.dataset.h) { const off = c.off.filter(x => x !== el.dataset.h); if (!el.checked) off.push(el.dataset.h); ponerCfg(KID, { off, asig: el.checked ? c.asig : c.asig.filter(x => x !== el.dataset.h) }); }
    else if (el.dataset.asig) { const id = el.dataset.asig, asig = c.asig.filter(x => x !== id); if (el.checked) asig.push(id); ponerCfg(KID, { asig, off: el.checked ? c.off.filter(x => x !== id) : c.off }); }
    renderPanel(); refrescarMenu();
  });
  $("ayPanelBody").addEventListener("click", ev => {
    const b = ev.target.closest("button"); if (!b) return;
    if (b.id === "ayAbrir") abrir();
    else if (b.dataset.p === "permiso") Alarma.pedirPermiso().then(renderPanel, renderPanel);
  });

  /* API pública mínima (la usan las pruebas y el futuro envoltorio nativo) */
  Gioval.ayudantes = { abrir, cfg, ponerCfg, disponibles, ofrece, vecesSemana, registro: regDe, tareas: TAREAS,
    enCurso: () => E && { id: E.id, estado: E.estado, kid: E.kid }, vista: () => V };
})();
