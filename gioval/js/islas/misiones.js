"use strict";
/* ============ ISLA MISIONES (reales) + ÁLBUM DE LOGROS REALES ============
   Actividades fuera de la pantalla (Construir, Experimentos, Cocina, Huerta, Arte, Hogar) que el niño hace con un adulto
   y después registra acá. Los textos (tablas de idioma, por clave misiones.*) y las misiones viven en js/datos/misiones.js (editables).
   - No es una isla de "tocar opciones": no tiene habilidades ni sesión diaria ni chequeo. Declara menuPropio() (ver ui.js)
     y sus propias pantallas. Ninguna pantalla lleva la clase "juego", así que su tiempo NO cuenta como pantalla.
   - Cada misión: ¿listo? (aviso de seguridad + nivel de supervisión) → materiales → (predicción) → hacer (temporizador
     opcional del módulo Alarma) → (¿qué pasó? → ¿por qué creés?) → registrar (frase + salió como pensaba/distinto + foto opcional).
   - Álbum: store.misiones.album[perfil] = [{ id, m, nombre, emoji, cat, fecha, t, pred, obs, porque, frase, res, foto }].
     Las fotos son Blob en IndexedDB (Gioval.almacen.fotos), SOLO en el aparato, achicadas a 1024 px y re-codificadas (se pierden
     los metadatos de la cámara, incluida la ubicación). Entran en el respaldo (exportar/restaurar).
   - store.misiones se crea al usarse (sin migración): { album:{}, pend:{}, semana:{}, edad:{} }.
   - Privacidad: la foto y el dictado por voz necesitan que un adulto los active (candado de multiplicación). */
(function () {
const D = Gioval.datos.misiones, I18N = Gioval.i18n;
/* Todo texto sale de la tabla del idioma (js/datos/misiones.js): u("lista.titulo") = clave misiones.ui.lista.titulo. Nada de español en el código. */
const u = (k, p) => t("misiones.ui." + k, p);
const ul = (k, p) => tl("misiones.ui." + k, p);
const nombreCat = c => t("misiones.cat." + c);
const burbujaDe = paso => I18N.tiene("misiones.ui.burbuja." + paso) ? u("burbuja." + paso) : "";
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fAlm = () => Gioval.almacen.fotos;

/* ---------------- datos guardados ---------------- */
function M() {
  const m = store.misiones && typeof store.misiones === "object" && !Array.isArray(store.misiones) ? store.misiones : (store.misiones = {});
  ["album", "pend", "semana", "edad"].forEach(k => { if (!m[k] || typeof m[k] !== "object" || Array.isArray(m[k])) m[k] = {}; });
  return m;
}
const verAlbum = () => M().album[KID] || [];
const verPend = () => M().pend[KID] || [];
const edadDe = () => M().edad[KID] || 6;

/* ---------------- lista de misiones válidas ---------------- */
let LISTA = null;
function lista() {
  if (!LISTA) LISTA = D.MISIONES.filter(m => {
    const p = D.validar(m); if (p.length) { console.warn("[misiones] oculta " + (m && m.id) + ": " + p.join("; ")); return false; }
    return true;
  });
  return LISTA;
}
const textosDe = m => D.textos(m);
const hechas = id => verAlbum().filter(e => e.m === id).length;

/* ---------------- misión de la semana ---------------- */
function semanaKey() {
  const d = new Date(Date.now()), t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const dia = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - dia);
  const y = t.getUTCFullYear(), w = Math.ceil(((t - Date.UTC(y, 0, 1)) / DAY + 1) / 7);
  return y + "-W" + String(w).padStart(2, "0");
}
/* la que eligió el adulto para esta semana; si no, una automática según la edad (prefiere las que todavía no hizo) */
function misionSemana() {
  const m = M(), k = semanaKey(), L = lista(), s = m.semana[KID];
  if (s && s.w === k) { const x = L.find(y => y.id === s.id); if (x) return x; }
  const ok = L.filter(x => x.minEdad <= edadDe()); if (!ok.length) return null;
  const vistas = new Set(verAlbum().map(e => e.m)), nuevas = ok.filter(x => !vistas.has(x.id)), pool = nuevas.length ? nuevas : ok;
  const n = +k.split("-W")[1], h = Array.from(KID).reduce((a, c) => a + c.charCodeAt(0), 0);
  const x = pool[(n + h) % pool.length];
  m.semana[KID] = { w: k, id: x.id, auto: true }; save(); return x;
}

/* ---------------- estado de la misión en curso ---------------- */
let Mi = null;
function secuencia(m, reanuda) {
  const s = [];
  if (!reanuda) { s.push("listo", "materiales"); if (m.tipo !== "hacer" || textosDe(m).imaginar) s.push("antes"); s.push("hacer"); if (m.espera) { s.push("espera"); return s; } }
  if (m.tipo !== "hacer") s.push("quepaso", "porque");
  s.push("registro"); return s;
}
function abrirMision(id, pend) {
  const m = lista().find(x => x.id === id); if (!m) return;
  const t = textosDe(m);
  Mi = { m, t, seq: secuencia(m, !!pend), paso: pend ? "quepaso" : "listo", i: 0, mats: t.materiales.map(() => false), predSel: null, pred: "", obsSel: null, obs: "", porque: "", frase: "", res: "", foto: null, consent: false, dictado: false,
    adOpen: false, verExp: false, timer: false, guardado: false, pend: pend || null };
  if (pend) { Mi.pred = pend.pred || ""; Mi.predSel = pend.predSel == null ? null : pend.predSel; }
  show("misJuego"); pintar();
}
/* dice el texto en voz alta pero deja en el globito una frase corta (el texto largo ya se lee en pantalla) */
function hablar(texto, burbuja) { const p = speak(texto); setBubble(burbuja || ""); return p; }
const SR = () => window.SpeechRecognition || window.webkitSpeechRecognition;

/* ---------------- temporizador (módulo Alarma) ---------------- */
const mmss = s => Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
function bajaTimer() { if (Mi && Mi.baja) { Mi.baja(); Mi.baja = null; } }
function ponerTimer(seg) {
  try { Gioval.alarma.pedirPermiso().catch(() => {}); } catch (e) {}
  bajaTimer(); const ini = Date.now(), tit = u("timer.titulo"); /* el título se fija ahora: si cambia el idioma mientras corre, igual se reconoce */
  /* se escucha SOLO mientras hay un temporizador nuestro corriendo: si no, se "robaría" el aviso de una alarma vencida con la app cerrada */
  Mi.baja = Gioval.alarma.onFin(info => {
    if (info.titulo !== tit || info.fin < ini || !Mi || !Mi.timer) return;
    bajaTimer(); Mi.timer = false; pintarTimer(); hablar(u("timer.fin"), u("timer.fin"));
  });
  Gioval.alarma.programar(seg, { titulo: tit, texto: u("timer.texto") }); Mi.timer = true; pintarTimer();
}
function cancelarTimer() { if (Mi && Mi.timer) { Gioval.alarma.cancelar(); Mi.timer = false; } bajaTimer(); pintarTimer(); }
function pintarTimer() {
  const el = $("misTimerEstado"); if (!el) return;
  const r = Mi && Mi.timer ? Gioval.alarma.restante() : 0;
  el.innerHTML = r > 0 ? esc(u("timer.corre", { tiempo: "@@T@@" })).replace("@@T@@", "<b>" + mmss(r) + "</b>") + " <button class=\"mis-mini\" data-act=\"timerCancel\">" + esc(u("timer.cancelar")) + "</button>" : "";
}
setInterval(() => { if (Mi && $("misJuego").classList.contains("active")) pintarTimer(); }, 500);

/* ---------------- pantalla de la misión ---------------- */
function chips(opts, sel, extra) {
  return '<div class="mis-chips">' + opts.map((o, k) => `<button class="mis-chip${sel === k ? " on" : ""}" data-chip="${k}">${esc(o)}</button>`).join("") +
    (extra || []).map(([k, txt]) => `<button class="mis-chip${sel === k ? " on" : ""}" data-chip="${k}">${esc(txt)}</button>`).join("") + "</div>";
}
function adultoOpciones() {
  const dic = SR() ? `<button class="mis-tg${Mi.dictado ? " on" : ""}" data-act="tgDictado" aria-pressed="${Mi.dictado}"><span>${Mi.dictado ? "☑" : "☐"}</span> ${esc(u("adulto.dictado"))}</button>` : "";
  return `<details class="mis-ad" data-ad${Mi.adOpen ? " open" : ""}><summary>${esc(u("adulto.resumen"))}</summary>
    <button class="mis-tg${Mi.consent ? " on" : ""}" data-act="tgFoto" aria-pressed="${Mi.consent}"><span>${Mi.consent ? "☑" : "☐"}</span> ${esc(u("adulto.foto"))}</button>${dic}</details>`;
}
function areaTexto(clave, placeholder) {
  const dic = Mi.dictado && SR() ? `<button class="mis-mini" data-dictar="${clave}">${esc(u("registro.dictar"))}</button>` : "";
  return `<textarea class="mis-in" data-in="${clave}" rows="2" placeholder="${esc(placeholder)}">${esc(Mi[clave])}</textarea>${dic}`;
}
function boton(t, cls, fn, off) { const b = document.createElement("button"); b.className = "btn" + (cls ? " " + cls : ""); b.textContent = t; if (off) b.disabled = true; b.onclick = fn; $("misAcc").appendChild(b); return b; }
function ir(paso) { Mi.paso = paso; if (paso === "hacer") Mi.i = Mi.i || 0; pintar(); }
function siguiente() { const k = Mi.seq.indexOf(Mi.paso); ir(Mi.seq[k + 1]); }
function predTexto() {
  const t = Mi.t.prediccion;
  if (Mi.predSel === "nose") return u("antes.nose_texto");
  if (Mi.predSel === "otra") return Mi.pred.trim() || u("antes.otra_puesta");
  if (typeof Mi.predSel === "number" && t) return t.opciones[Mi.predSel];
  return Mi.pred.trim();
}
function obsTexto() {
  if (Mi.obsSel === "otra") return Mi.obs.trim() || u("que_paso.otra");
  if (typeof Mi.obsSel === "number") return Mi.t.observacion[Mi.obsSel];
  return "";
}
function pintar(opc) {
  opc = opc || {};
  const m = Mi.m, t = Mi.t, cont = $("misCont"), top = cont.scrollTop;
  $("misAcc").innerHTML = ""; $("misTitulo").textContent = m.emoji + " " + t.nombre;
  const pr = $("misProg"), idx = Mi.seq.indexOf(Mi.paso); pr.style.display = "flex"; pr.innerHTML = "";
  Mi.seq.forEach((_, k) => { const d = document.createElement("i"); d.className = k < idx ? "ok" : (k === idx ? "now" : ""); pr.appendChild(d); });
  let html = "", habla = "", burb = burbujaDe(Mi.paso);
  switch (Mi.paso) {
    case "listo":
      html = `<div class="mis-aviso" id="misAviso"><b>${esc(u("listo.aviso"))}</b><p>${esc(t.aviso)}</p></div>
        <div class="mis-sup mis-sup-${m.sup}">${esc(u("supervision." + m.sup + ".corto"))}</div>
        <p class="mis-det">${esc(u("supervision." + m.sup + ".detalle"))} <small>(${esc(u("lista.desde", { n: m.minEdad }))})</small></p>
        <p>${esc(t.resumen)}</p>${adultoOpciones()}`;
      habla = u("listo.habla", { nombre: t.nombre.replace(/[.!?¡¿]+$/, ""), resumen: t.resumen, aviso: t.aviso });
      boton(u("listo.volver"), "alt", () => salir());
      boton(u("listo.adulto"), "", () => { if (m.sup === "junto") gate(() => siguiente()); else siguiente(); });
      break;
    case "materiales": {
      html = `<p>${esc(u("materiales.ayuda"))}</p><div class="mis-mats">` + t.materiales.map((x, k) => `<button class="mis-mat${Mi.mats[k] ? " on" : ""}" data-mat="${k}"><span class="chk">${Mi.mats[k] ? "☑" : "☐"}</span> ${esc(x)}</button>`).join("") + "</div>";
      habla = u("materiales.habla");
      boton(u("materiales.falta"), "alt", () => { salir(); hablar(u("materiales.falta_habla"), u("materiales.falta_habla")); });
      const b = boton(u("materiales.todo"), "", () => siguiente(), !Mi.mats.every(Boolean)); b.id = "misTodo";
      break; }
    case "antes": {
      const P = t.prediccion;
      if (P) {
        html = `<p class="mis-preg">${esc(P.pregunta)}</p>` + chips(P.opciones, Mi.predSel, [["otra", u("antes.otra")], ["nose", u("antes.nose")]]) +
          (Mi.predSel === "otra" ? areaTexto("pred", u("antes.escribir")) : "") + adultoOpciones();
        habla = P.pregunta;
      } else {
        html = `<p class="mis-preg">${esc(t.imaginar)}</p>` + areaTexto("pred", u("antes.escribir")) + adultoOpciones();
        habla = t.imaginar;
      }
      boton(u("antes.seguir"), "", () => { Mi.pred = predTexto(); siguiente(); }, !!P && Mi.predSel == null);
      break; }
    case "hacer": {
      const k = Mi.i, n = t.pasos.length, tp = m.temporizador;
      const bt = tp && tp.paso === k ? `<p><button class="btn" data-act="timer">${esc(u("timer.poner", { min: Math.round(tp.seg / 60) }))}</button></p>` : "";
      html = `<div class="mis-pasoN">${esc(u("hacer.paso", { i: k + 1, n }))}</div><p class="mis-paso">${esc(t.pasos[k])}</p>${bt}<div class="mis-timer" id="misTimerEstado"></div>`;
      habla = t.pasos[k]; burb = u("burbuja.hacer", { i: k + 1, n });
      if (k > 0) boton(u("hacer.anterior"), "alt", () => { Mi.i--; pintar(); });
      boton(k < n - 1 ? u("hacer.siguiente") : u("hacer.ultimo"), "", () => { if (k < n - 1) { Mi.i++; pintar(); } else siguiente(); });
      break; }
    case "espera": {
      const d = m.espera.dias;
      html = `<div class="mis-fin"><div class="em">⏳</div><h3>${esc(u("espera.titulo"))}</h3><p>${esc(u("espera.texto", { dias: d }))}</p></div>`;
      habla = u("espera.habla", { dias: d });
      boton(u("espera.guardar"), "", () => guardarPend());
      break; }
    case "quepaso": {
      const rec = Mi.pred ? `<p class="mis-recuerda">${esc(u("que_paso.pensabas"))} <b>${esc(Mi.pred)}</b></p>` : "";
      html = `<h3 class="mis-h">${esc(u("que_paso.titulo"))}</h3>${rec}` + chips(t.observacion, Mi.obsSel, [["otra", u("que_paso.otra")]]) + (Mi.obsSel === "otra" ? areaTexto("obs", u("registro.frase_ph")) : "");
      habla = u("que_paso.habla");
      boton(u("que_paso.seguir"), "", () => { Mi.obs = obsTexto(); siguiente(); }, Mi.obsSel == null);
      break; }
    case "porque": {
      const ver = Mi.verExp && t.explicacion && !m.revisar;
      html = `<h3 class="mis-h">${esc(u("porque.titulo"))}</h3>` + areaTexto("porque", u("porque.escribir")) +
        `<p class="mis-guia"><b>${esc(u("porque.guia"))}</b> ${esc(t.guia)}</p>` +
        (ver ? `<div class="mis-exp"><b>${esc(u("porque.para_adulto"))}</b><p>${esc(t.explicacion)}</p></div>` : "") + adultoOpciones();
      habla = u("porque.habla");
      if (t.explicacion && !m.revisar) boton(Mi.verExp ? u("porque.ocultar") : u("porque.ver"), "alt", () => { Mi.verExp = !Mi.verExp; pintar({ silencio: true }); });
      boton(u("porque.seguir"), "", () => siguiente());
      break; }
    case "registro": {
      const dis = !Mi.res;
      let foto = "";
      if (Mi.consent) {
        foto = Mi.foto ? `<div class="mis-fotoprev"><img src="${Mi.foto.url}" alt=""><div><button class="mis-mini" data-act="sacar">${esc(u("adulto.otra"))}</button> <button class="mis-mini" data-act="quitar">${esc(u("adulto.quitar"))}</button></div></div>`
          : `<button class="btn" data-act="sacar" id="misSacar">${esc(u("adulto.sacar"))}</button>`;
        if (!Gioval.almacen.idbOk) foto = `<p class="mis-guia">${esc(u("adulto.sin_almacen"))}</p>`;
      } else foto = `<p class="mis-guia">${esc(u("adulto.foto_off"))}</p>`;
      html = `<h3 class="mis-h">${esc(u("registro.titulo"))}</h3>
        <label class="mis-lbl">${esc(u("registro.frase"))}</label>${areaTexto("frase", u("registro.frase_ph"))}
        <div class="mis-chips"><button class="mis-chip${Mi.res === "pensaba" ? " on" : ""}" data-res="pensaba">${esc(u("registro.pensaba"))}</button><button class="mis-chip${Mi.res === "distinto" ? " on" : ""}" data-res="distinto">${esc(u("registro.distinto"))}</button></div>
        ${adultoOpciones()}<div class="mis-foto-zona">${foto}</div>`;
      habla = u("registro.habla");
      const b = boton(u("registro.guardar"), "", () => guardar(), dis); b.id = "misGuardar";
      break; }
    case "fin": {
      html = `<div class="mis-fin"><div class="em">📖</div><h3>${esc(u("fin.titulo"))}</h3><p id="misFinTxt">${esc(Mi.mensaje)}</p></div>`;
      habla = Mi.mensaje;
      boton(u("fin.isla"), "alt", () => salir());
      boton(u("fin.mas"), "alt", () => { Mi = null; abrirLista(); });
      boton(u("fin.album"), "", () => { Mi = null; abrirAlbum(false); });
      break; }
  }
  cont.innerHTML = html; cont.scrollTop = opc.silencio ? top : 0;
  if (opc.silencio && Mi.paso === "registro" && Mi.consent) { const z = cont.querySelector(".mis-foto-zona"); if (z) z.scrollIntoView({ block: "nearest" }); } /* que se vea la foto recién sacada aunque la pantalla sea baja */
  Mi.habla = habla; Mi.burb = burb; if (Mi.paso === "hacer") pintarTimer();
  if (opc.silencio) setBubble(burb); else if (habla) hablar(habla, burb); else setBubble(burb);
}
function salir() {
  try { speechSynthesis.cancel(); } catch (e) {}
  cancelarTimer(); if (Mi && Mi.foto) URL.revokeObjectURL(Mi.foto.url);
  Mi = null; goMenuIsla();
}

/* eventos de la zona de contenido (se arma una sola vez) */
function conectar() {
  const cont = $("misCont");
  cont.addEventListener("click", ev => {
    if (!Mi) return;
    const b = ev.target.closest("button"); if (!b || !cont.contains(b)) return;
    if (b.dataset.mat != null) { const k = +b.dataset.mat; Mi.mats[k] = !Mi.mats[k]; b.classList.toggle("on", Mi.mats[k]); b.querySelector(".chk").textContent = Mi.mats[k] ? "☑" : "☐"; const t = $("misTodo"); if (t) t.disabled = !Mi.mats.every(Boolean); return; }
    if (b.dataset.chip != null) {
      const v = b.dataset.chip, val = /^\d+$/.test(v) ? +v : v;
      if (Mi.paso === "antes") { Mi.predSel = val; if (val !== "otra" && val !== "nose") Mi.pred = ""; pintar({ silencio: true }); }
      else if (Mi.paso === "quepaso") { Mi.obsSel = val; pintar({ silencio: true }); }
      return;
    }
    if (b.dataset.res) { Mi.res = b.dataset.res; pintar({ silencio: true }); return; }
    if (b.dataset.dictar) { dictar(b.dataset.dictar, b); return; }
    const a = b.dataset.act; if (!a) return;
    if (a === "timer") ponerTimer(Mi.m.temporizador.seg);
    else if (a === "timerCancel") cancelarTimer();
    else if (a === "tgFoto") { if (Mi.consent) { Mi.consent = false; quitarFoto(); pintar({ silencio: true }); } else gate(() => { Mi.consent = true; Mi.adOpen = true; pintar({ silencio: true }); }); }
    else if (a === "tgDictado") { if (Mi.dictado) { Mi.dictado = false; pintar({ silencio: true }); } else gate(() => { Mi.dictado = true; Mi.adOpen = true; pintar({ silencio: true }); }); }
    else if (a === "sacar") $("misFile").click();
    else if (a === "quitar") { quitarFoto(); pintar({ silencio: true }); }
  });
  cont.addEventListener("input", ev => { const k = ev.target.dataset && ev.target.dataset.in; if (k && Mi) Mi[k] = ev.target.value; });
  cont.addEventListener("toggle", ev => { if (Mi && ev.target.matches && ev.target.matches("details[data-ad]")) Mi.adOpen = ev.target.open; }, true);
  $("misFile").onchange = async e => {
    const f = e.target.files[0]; e.target.value = ""; if (!f || !Mi || !Mi.consent) return;
    try { const blob = await reducir(f); quitarFoto(); Mi.foto = { blob, url: URL.createObjectURL(blob) }; pintar({ silencio: true }); }
    catch (err) { setBubble(u("adulto.lectura_error")); }
  };
}
function quitarFoto() { if (Mi && Mi.foto) { URL.revokeObjectURL(Mi.foto.url); Mi.foto = null; } }
/* achica a 1024 px y re-codifica en JPEG: pesa poco y se pierden los metadatos de la cámara (incluida la ubicación) */
async function reducir(file) {
  let bmp = null;
  try { bmp = await createImageBitmap(file, { imageOrientation: "from-image" }); } catch (e) {}
  if (!bmp) bmp = await new Promise((ok, mal) => { const im = new Image(), u = URL.createObjectURL(file); im.onload = () => { URL.revokeObjectURL(u); ok(im); }; im.onerror = () => mal(new Error("imagen")); im.src = u; });
  const w0 = bmp.width, h0 = bmp.height, k = Math.min(1, 1024 / Math.max(w0, h0));
  const c = document.createElement("canvas"); c.width = Math.max(1, Math.round(w0 * k)); c.height = Math.max(1, Math.round(h0 * k));
  c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height); if (bmp.close) bmp.close();
  const blob = await new Promise(r => c.toBlob(r, "image/jpeg", .8)); if (!blob) throw new Error("jpeg");
  return blob;
}
function dictar(clave, boton) {
  const R = SR(); if (!R) return;
  try { speechSynthesis.cancel(); } catch (e) {}
  const r = new R(); r.lang = I18N.meta().locale; r.interimResults = false; r.maxAlternatives = 1; r.continuous = false;
  const fin = () => { boton.textContent = u("registro.dictar"); };
  boton.textContent = u("registro.escuchando");
  r.onresult = ev => { const txt = ev.results[0][0].transcript; Mi[clave] = (Mi[clave] ? Mi[clave] + " " : "") + txt; const ta = document.querySelector('#misCont [data-in="' + clave + '"]'); if (ta) ta.value = Mi[clave]; };
  r.onend = fin; r.onerror = fin;
  try { r.start(); } catch (e) { fin(); }
}

/* ---------------- guardar ---------------- */
function mensajeFin() {
  const F = k => ul("fin." + k), p = [], m = Mi.m;
  if (m.tipo === "hacer") p.push(pick(F("hacer"), "mf-h"));
  else { if (Mi.predSel != null && Mi.predSel !== "nose") p.push(pick(F("predijo"), "mf-p")); p.push(pick(F("miro"), "mf-m")); }
  if (Mi.frase.trim()) p.push(pick(F("conto"), "mf-c"));
  if (Mi.fotoGuardada) p.push(pick(F("foto"), "mf-f"));
  p.push(Mi.res === "pensaba" ? F("pensaba")[0] : F("distinto")[0], F("cierre")[0]);
  return p.join(" ");
}
async function guardar() {
  if (!Mi || Mi.guardado || !Mi.res) return; Mi.guardado = true;
  const m = Mi.m, t = Mi.t, A = Gioval.almacen;
  const e = { id: "a" + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36), m: m.id, nombre: t.nombre, emoji: m.emoji, cat: m.cat, fecha: today(), t: Date.now(),
    pred: Mi.pred || predTexto(), obs: Mi.obs || obsTexto(), porque: Mi.porque.trim(), frase: Mi.frase.trim(), res: Mi.res, foto: null };
  let aviso = "";
  if (Mi.foto && Mi.consent) {
    try {
      if (!A.idbOk) throw new Error("sin IndexedDB");
      const fid = await fAlm().guardar(Mi.foto.blob, { perfil: KID, entrada: e.id, mision: m.id });
      if (await fAlm().obtener(fid)) e.foto = fid; else throw new Error("photo not stored");
    } catch (err) { aviso = u("adulto.foto_error"); }
  }
  Mi.fotoGuardada = !!e.foto;
  const M_ = M(); (M_.album[KID] = M_.album[KID] || []).push(e);
  if (M_.pend[KID]) M_.pend[KID] = M_.pend[KID].filter(p => p.m !== m.id);
  save(); await A.guardarYa();
  quitarFoto(); cancelarTimer();
  Mi.mensaje = mensajeFin() + (aviso ? " " + aviso : ""); Mi.paso = "fin"; Mi.seq = ["fin"];
  pintar();
}
function guardarPend() {
  const m = Mi.m, M_ = M(), arr = M_.pend[KID] = (M_.pend[KID] || []).filter(p => p.m !== m.id);
  arr.push({ m: m.id, desde: Date.now(), fecha: today(), pred: Mi.pred, predSel: typeof Mi.predSel === "number" ? Mi.predSel : (Mi.predSel || null) });
  save(); Gioval.almacen.guardarYa(); const msg = u("espera.despedida"); cancelarTimer(); Mi = null; goMenuIsla(); hablar(msg, msg);
}

/* ---------------- elegir una misión ---------------- */
let filtro = "todas";
function abrirLista() { show("misLista"); pintarLista(); setBubble(u("lista.titulo").replace(/^\S+\s/, "")); }
function pintarLista() {
  const f = $("misFiltros"); f.innerHTML = "";
  [["todas", u("lista.todas")]].concat(D.CATEGORIAS.map(k => [k, nombreCat(k)])).forEach(([k, n]) => {
    const b = document.createElement("button"); b.className = "mis-chip" + (filtro === k ? " on" : ""); b.textContent = n; b.dataset.cat = k;
    b.onclick = () => { filtro = k; pintarLista(); }; f.appendChild(b);
  });
  const g = $("misGrid"); g.innerHTML = ""; const sem = misionSemana(), edad = edadDe();
  lista().filter(m => filtro === "todas" || m.cat === filtro).forEach(m => {
    const t = textosDe(m), bloq = m.minEdad > edad, n = hechas(m.id), b = document.createElement("button");
    b.className = "mis-card" + (bloq ? " off" : ""); b.dataset.id = m.id;
    b.innerHTML = `<span class="em">${bloq ? "🔒" : m.emoji}</span><b>${esc(t.nombre)}</b><small>${esc(nombreCat(m.cat))} · ${esc(u("supervision." + m.sup + ".corto"))}</small>` +
      `<small>${bloq ? esc(u("lista.bloqueada")) + " · " : ""}${esc(u("lista.desde", { n: m.minEdad }))}${n ? " · " + esc(u("lista.hecha", { n })) : ""}</small>` + (sem && sem.id === m.id ? `<span class="mis-tagsem">${esc(u("lista.semana_tag"))}</span>` : "");
    if (!bloq) b.onclick = () => { ensureCtx(); abrirMision(m.id); };
    g.appendChild(b);
  });
}

/* ---------------- álbum ---------------- */
const Alb = { adulto: false, urls: [], token: 0, confirmar: null };
function abrirAlbum(adulto) { Alb.adulto = !!adulto; show("misAlbum"); pintarAlbum(); setBubble(u("album.titulo").replace(/^\S+\s/, "")); }
function soltarUrls() { Alb.urls.forEach(u => URL.revokeObjectURL(u)); Alb.urls = []; }
async function pintarAlbum() {
  const tk = ++Alb.token, box = $("misAlbLista"); soltarUrls();
  $("misAlbModo").innerHTML = Alb.adulto ? `👦<span class="lbl"> ${esc(u("album.nino").replace(/^\S+\s/, ""))}</span>` : `🔒<span class="lbl"> ${esc(u("album.adultos").replace(/^\S+\s/, ""))}</span>`;
  $("misAlbModo").title = Alb.adulto ? u("album.nino") : u("album.adultos");
  $("misAlbInfo").textContent = Alb.adulto ? u("album.info_adulto") : ""; $("misAlbInfo").style.display = Alb.adulto ? "" : "none";
  const arr = verAlbum().slice().sort((a, b) => b.t - a.t);
  if (!arr.length) { box.innerHTML = `<div class="mis-vacio">${esc(u("album.vacio"))}</div>`; return; }
  box.innerHTML = arr.map(e => {
    const fecha = I18N.fecha(new Date(e.t), { day: "numeric", month: "long", year: "numeric" });
    const det = [e.pred ? esc(u("album.predijo")) + " " + esc(e.pred) : "", e.obs ? esc(u("album.paso")) + " " + esc(e.obs) : "", e.porque ? esc(u("album.porque")) + " " + esc(e.porque) : ""].filter(Boolean).map(x => `<small>${x}</small>`).join("");
    const adm = Alb.adulto ? `<div class="mis-adm"><button class="mis-mini" data-del="${esc(e.id)}">${esc(u("album.borrar"))}</button>${e.foto ? ` <button class="mis-mini" data-delfoto="${esc(e.id)}">${esc(u("album.borrar_foto"))}</button>` : ""}</div>` : "";
    return `<div class="mis-ent" data-id="${esc(e.id)}"><div class="mis-foto" data-foto="${esc(e.foto || "")}"><span class="em">${esc(e.emoji)}</span></div>
      <div class="mis-txt"><b>${esc(e.emoji)} ${esc(e.nombre)}</b><small>${esc(fecha)}</small>${e.frase ? `<p class="mis-frase">“${esc(e.frase)}”</p>` : ""}
      <span class="mis-tag t-${e.res}">${esc(e.res === "pensaba" ? u("album.pensaba") : u("album.distinto"))}</span>${det}${adm}</div></div>`;
  }).join("");
  for (const e of arr) {
    if (!e.foto) continue;
    let rec = null; try { rec = await fAlm().obtener(e.foto); } catch (x) {}
    if (tk !== Alb.token) return;
    const z = box.querySelector('.mis-ent[data-id="' + e.id + '"] .mis-foto'); if (!z) continue;
    if (rec && rec.blob) { const u = URL.createObjectURL(rec.blob); Alb.urls.push(u); z.innerHTML = `<img src="${u}" alt="">`; }
    else z.innerHTML = `<span class="mis-sinfoto">${esc(u("album.sin_foto"))}</span>`;
  }
}
async function borrarEntrada(id, soloFoto) {
  const m = M(), arr = m.album[KID] || [], e = arr.find(x => x.id === id); if (!e) return;
  if (e.foto) { try { await fAlm().borrar(e.foto); } catch (x) {} e.foto = null; }
  if (!soloFoto) m.album[KID] = arr.filter(x => x.id !== id);
  save(); await Gioval.almacen.guardarYa(); pintarAlbum();
}
function conectarAlbum() {
  $("misAlbBack").onclick = () => { Alb.token++; soltarUrls(); Alb.adulto = false; goMenuIsla(); };
  $("misAlbModo").onclick = () => { if (Alb.adulto) { Alb.adulto = false; pintarAlbum(); } else gate(() => { Alb.adulto = true; pintarAlbum(); }); };
  $("misAlbLista").addEventListener("click", ev => {
    const b = ev.target.closest("button"); if (!b || !Alb.adulto) return;
    const id = b.dataset.del || b.dataset.delfoto; if (!id) return;
    const solo = !!b.dataset.delfoto; Alb.confirmar = { id, solo };
    $("misConfirmTxt").textContent = solo ? u("album.confirma_foto") : u("album.confirma_recuerdo"); $("misConfirm").classList.add("show");
  });
  $("misConfirmSi").onclick = async () => { const c = Alb.confirmar; Alb.confirmar = null; $("misConfirm").classList.remove("show"); if (c) await borrarEntrada(c.id, c.solo); };
  $("misConfirmNo").onclick = () => { Alb.confirmar = null; $("misConfirm").classList.remove("show"); };
}

/* ---------------- panel de adultos ---------------- */
function refrescarPanel() {
  const ed = $("misPEdad"), se = $("misPSem"); if (!ed) return;
  $("misPEdadL").textContent = u("panel.edad", { nombre: KID || "…" });
  ed.disabled = se.disabled = !KID; $("misPAlbum").disabled = !KID;
  ed.innerHTML = ""; for (let a = 4; a <= 12; a++) { const o = document.createElement("option"); o.value = a; o.textContent = u("panel.anos", { n: a }); ed.appendChild(o); }
  if (!KID) return;
  ed.value = String(edadDe());
  const sem = misionSemana(), s = M().semana[KID], auto = !s || s.auto !== false;
  se.innerHTML = `<option value="">${esc(u("panel.auto"))}</option>` + lista().map(m => `<option value="${m.id}">${m.emoji} ${esc(textosDe(m).nombre)}</option>`).join("");
  se.value = auto ? "" : (sem ? sem.id : "");
}
function conectarPanel() {
  Gioval.on("panel", refrescarPanel);
  $("misPEdad").onchange = e => { if (!KID) return; M().edad[KID] = +e.target.value; const s = M().semana[KID]; if (s && s.auto) delete M().semana[KID]; save(); refrescarPanel(); };
  $("misPSem").onchange = e => { if (!KID) return; const v = e.target.value; if (v) M().semana[KID] = { w: semanaKey(), id: v, auto: false }; else delete M().semana[KID]; save(); refrescarPanel(); };
  $("misPAlbum").onclick = () => { if (!KID) return; $("panel").classList.remove("show"); S.run++; resetFlow(); PACK = ISLA; abrirAlbum(true); };
}

/* ---------------- menú de la isla ---------------- */
function menuPropio() {
  const cards = [], sem = misionSemana();
  if (sem) cards.push({ em: sem.emoji, t: u("tarjetas.semana"), s: textosDe(sem).nombre, on: true, go: () => abrirMision(sem.id) });
  verPend().forEach(p => {
    const m = lista().find(x => x.id === p.m); if (!m) return;
    cards.push({ em: m.emoji, t: u("tarjetas.pendiente", { nombre: textosDe(m).nombre }), s: u("tarjetas.pendiente_sub", { dias: Math.floor((Date.now() - p.desde) / DAY) }), on: true, go: () => abrirMision(m.id, p) });
  });
  cards.push({ em: "🧭", t: u("tarjetas.elegir"), s: u("tarjetas.elegir_sub"), on: true, go: () => abrirLista() });
  const n = verAlbum().length;
  cards.push({ em: "📖", t: u("tarjetas.album"), s: n ? u("tarjetas.album_sub", { n }) : u("tarjetas.album_sub0"), on: true, go: () => abrirAlbum(false) });
  return cards;
}

/* ---------------- pantallas ---------------- */
const di = k => ["data-i18n", JSON.stringify("misiones.ui." + k)].join("=");  /* atributo para que i18n.aplicar() retraduzca el texto al cambiar de idioma */
const DOM = {
  pantallas: `
<style>
.mis-body{flex:1;min-height:0;display:flex;flex-direction:column;gap:8px}
.mis-cont{flex:1 1 0;min-height:0;overflow:auto;background:rgba(255,255,255,.8);border-radius:22px;padding:12px 14px;font-size:clamp(17px,2.5vw,22px);line-height:1.35;font-weight:600;-webkit-overflow-scrolling:touch;user-select:text;-webkit-user-select:text}
.mis-cont p{margin:6px 0}
.mis-acc{flex:none;display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
.mis-acc .btn{flex:1 1 150px;max-width:340px}
.mis-acc .btn:disabled,.mis-cont .btn:disabled{opacity:.4;pointer-events:none}
.mis-aviso{background:#fff3c4;border:3px solid #ff9f1c;border-radius:16px;padding:8px 12px;font-weight:700}
.mis-aviso p{margin:4px 0 0}
.mis-sup{display:inline-block;margin:8px 0 0;padding:4px 12px;border-radius:14px;font-weight:900;background:#d8f5de}
.mis-sup-junto{background:#ffd9d9}
.mis-det{margin:4px 0}
.mis-det small{opacity:.7}
.mis-h{margin:2px 0 6px;font-size:1.15em}
.mis-preg{font-size:1.1em;font-weight:800}
.mis-pasoN{font-weight:900;color:#7c4dff}
.mis-paso{font-size:1.25em;font-weight:800}
.mis-recuerda{background:#ece6ff;border-radius:12px;padding:6px 10px}
.mis-chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.mis-chip{border:0;border-radius:18px;padding:10px 14px;background:#fff;font:inherit;font-weight:800;color:#2b2350;box-shadow:0 3px 0 rgba(0,0,0,.16);min-height:48px;touch-action:manipulation}
.mis-chip.on{background:#7c4dff;color:#fff}
.mis-mats{display:flex;flex-direction:column;gap:8px}
.mis-mat{border:0;border-radius:16px;padding:10px 12px;background:#fff;font:inherit;font-weight:700;text-align:left;color:#2b2350;box-shadow:0 3px 0 rgba(0,0,0,.14);min-height:48px;display:flex;gap:10px;align-items:center}
.mis-mat.on{background:#d8f5de}
.mis-mat .chk{font-size:1.3em}
.mis-in{width:100%;min-height:60px;border-radius:14px;border:2px solid #cfc3ff;padding:8px 10px;font:inherit;font-weight:600;color:#2b2350;user-select:text;-webkit-user-select:text;resize:vertical}
.mis-mini{border:0;border-radius:12px;padding:6px 12px;background:#fff;font:inherit;font-size:.85em;font-weight:800;color:#2b2350;box-shadow:0 2px 0 rgba(0,0,0,.18);margin:4px 4px 0 0;min-height:36px}
.mis-guia{font-size:.9em;opacity:.85}
.mis-exp{background:#e6f7ff;border:2px solid #7cc4ee;border-radius:14px;padding:6px 12px;margin-top:8px}
.mis-lbl{font-weight:900;display:block;margin-top:6px}
.mis-ad{margin-top:10px;background:#f3f0ff;border-radius:14px;padding:6px 10px}
.mis-ad summary{font-weight:800;min-height:36px;display:flex;align-items:center}
.mis-tg{display:flex;gap:8px;align-items:flex-start;width:100%;border:0;background:#fff;border-radius:12px;padding:8px 10px;margin:6px 0;font:inherit;font-size:.85em;font-weight:700;text-align:left;color:#2b2350;min-height:44px}
.mis-tg.on{background:#d8f5de}
.mis-foto-zona{margin-top:8px}
.mis-fotoprev{display:flex;gap:10px;align-items:center}
.mis-fotoprev img{width:96px;height:96px;object-fit:cover;border-radius:14px;background:#eee}
.mis-timer{margin-top:6px;font-weight:800;color:#7c4dff}
.mis-fin{text-align:center}
.mis-fin .em{font-size:64px;line-height:1}
.mis-fin h3{margin:6px 0}
.mis-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;overflow:auto;padding:4px 2px 10px}
.mis-card{border:0;border-radius:24px;padding:14px 14px;background:linear-gradient(160deg,#fff,#eefaf0);box-shadow:0 5px 0 rgba(0,0,0,.14);display:flex;flex-direction:column;align-items:flex-start;gap:4px;font:inherit;font-size:clamp(18px,2.5vw,22px);font-weight:900;color:#2b2350;text-align:left;position:relative}
.mis-card .em{font-size:44px;line-height:1}
.mis-card small{font-size:14px;font-weight:700;opacity:.7}
.mis-card.off{filter:grayscale(.85);opacity:.6}
.mis-card:not(.off):active{transform:translateY(3px)}
.mis-tagsem{position:absolute;right:10px;top:10px;background:#ffd23f;border-radius:10px;padding:2px 8px;font-size:13px}
.mis-filtros{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 6px}
.mis-filtros .mis-chip{min-height:38px;padding:6px 12px;font-size:15px}
.mis-alb{flex:1;min-height:0;overflow:auto;display:flex;flex-direction:column;gap:10px;padding:2px 2px 10px}
.mis-ent{display:flex;gap:12px;background:#fff;border-radius:22px;padding:10px;box-shadow:0 4px 0 rgba(0,0,0,.12)}
.mis-foto{flex:none;width:96px;height:96px;border-radius:16px;background:#eef;display:flex;align-items:center;justify-content:center;overflow:hidden;text-align:center}
.mis-foto img{width:100%;height:100%;object-fit:cover}
.mis-foto .em{font-size:44px}
.mis-sinfoto{font-size:12px;font-weight:700;padding:4px}
.mis-txt{display:flex;flex-direction:column;gap:3px;min-width:0;font-weight:700}
.mis-txt small{font-weight:600;opacity:.75}
.mis-frase{margin:2px 0;font-style:italic;font-weight:700}
.mis-tag{align-self:flex-start;border-radius:10px;padding:2px 8px;font-size:14px;font-weight:800;background:#d8f5de}
.mis-tag.t-distinto{background:#ffe9b8}
.mis-vacio{background:rgba(255,255,255,.8);border-radius:20px;padding:20px;font-weight:700;text-align:center}
.mis-info{background:#fff3c4;border-radius:14px;padding:6px 12px;margin-bottom:6px;font-size:15px;font-weight:700}
.mis-adm{margin-top:4px}
.mis-panel label{display:flex;gap:10px;align-items:center;margin-top:8px}
.mis-panel select{font-size:16px;padding:6px;border-radius:10px}
@media (max-height:480px) and (orientation:landscape){
  .mis-body{flex-direction:row}
  .mis-acc{flex-direction:column;justify-content:center;width:200px}
  .mis-acc .btn{flex:0 0 auto;max-width:none}
  .mis-foto{width:72px;height:72px}
}
</style>
<div class="screen" id="misLista">
  <div class="bar"><button class="btn alt" id="misListaBack"><span class="arr">⬅</span><span class="lbl" data-i18n="app.isla">${esc(t("app.isla"))}</span></button><h2 style="margin:0" ${di("lista.titulo")}>${esc(u("lista.titulo"))}</h2><span style="width:90px"></span></div>
  <div class="mis-filtros" id="misFiltros"></div>
  <div class="mis-grid" id="misGrid"></div>
</div>
<div class="screen" id="misJuego">
  <div class="bar">
    <button class="btn alt" id="misBack"><span class="arr">⬅</span><span class="lbl" data-i18n="app.volver">${esc(t("app.volver"))}</span></button>
    <div style="font-weight:800;font-size:clamp(16px,2.6vw,24px);flex:1;text-align:center;min-width:0" id="misTitulo"></div>
    <button class="btn alt" id="misHear">🔊<span class="lbl" data-i18n="app.escuchar">${esc(t("app.escuchar"))}</span></button>
  </div>
  <div class="prog" id="misProg"></div>
  <div class="mis-body"><div class="mis-cont" id="misCont"></div><div class="mis-acc" id="misAcc"></div></div>
  <input type="file" id="misFile" accept="image/*" capture="environment" style="display:none">
</div>
<div class="screen" id="misAlbum">
  <div class="bar"><button class="btn alt" id="misAlbBack"><span class="arr">⬅</span><span class="lbl" data-i18n="app.isla">${esc(t("app.isla"))}</span></button><h2 style="margin:0" ${di("album.titulo")}>${esc(u("album.titulo"))}</h2><button class="btn alt" id="misAlbModo"></button></div>
  <div class="mis-info" id="misAlbInfo" style="display:none"></div>
  <div class="mis-alb" id="misAlbLista"></div>
</div>
<div class="big" id="misConfirm">
  <div style="background:#fff;color:#2b2350;padding:14px 18px;border-radius:18px;max-width:92vw;font-size:18px;font-weight:700" id="misConfirmTxt"></div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center"><button class="btn" id="misConfirmSi" ${di("album.si")}>${esc(u("album.si"))}</button><button class="btn alt" id="misConfirmNo" ${di("album.no")}>${esc(u("album.no"))}</button></div>
</div>`,
  panelPie: `<div class="psum mis-panel"><b ${di("panel.titulo")}>${esc(u("panel.titulo"))}</b>
    <label><span id="misPEdadL">${esc(u("panel.edad", { nombre: "…" }))}</span> <select id="misPEdad"></select></label>
    <label><span ${di("panel.semana")}>${esc(u("panel.semana"))}</span> <select id="misPSem"></select></label>
    <div style="margin-top:8px"><button class="btn" id="misPAlbum" style="padding:6px 14px;font-size:16px" ${di("panel.album")}>${esc(u("panel.album"))}</button></div></div>`,
};

function iniciar() {
  conectar(); conectarAlbum(); conectarPanel();
  $("misListaBack").onclick = () => goMenuIsla();
  $("misBack").onclick = () => salir();
  $("misHear").onclick = () => { if (Mi && Mi.habla) hablar(Mi.habla, Mi.burb); };
  /* si cambia el idioma con una pantalla de la isla a la vista, se vuelve a dibujar (sin volver a hablar) */
  Gioval.on("idioma", d => {
    if (!d || !d.cambio) return;
    const a = document.querySelector(".screen.active"); if (!a) return;
    if (a.id === "misLista") pintarLista();
    else if (a.id === "misAlbum") pintarAlbum();
    else if (a.id === "misJuego" && Mi) { Mi.t = textosDe(Mi.m); pintar({ silencio: true }); }
  });
}

const ISLA = { id: "misiones", emoji: "🧭", get name() { return u("isla.nombre"); }, get sub() { return u("isla.sub"); }, skills: [], actividades: {}, plain: true, instrumento: null, entradas: [],
  dom: DOM, iniciar, menuPropio, etiquetaTiempo: () => u("isla.etiqueta_tiempo"), hablaMenu: () => u("isla.habla_menu"),
  outro: "", capTail: "" };
Gioval.islas.registrar(ISLA);
/* interfaz para pruebas y para otras islas */
Gioval.misiones = { lista, recargar() { LISTA = null; return lista(); }, semana: misionSemana, semanaKey, estado: () => Mi, abrirMision, abrirAlbum, pintarAlbum, mensajeFin, datos: M };
})();
