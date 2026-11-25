"use strict";
/* ============ ISLA RITMO ============
   Ritmo antes que solfeo y guitarra: sentir el pulso, copiar ritmos (eco), silencios, leer tarjetas (ta / ti-ti / shh),
   canciones tradicionales (solo el patrón), llamada y respuesta y composición de 4 pulsos.
   Entrada: eventos "golpe" (js/core/entrada/golpes.js): por micrófono (palmas, cajón, bongó, tambor…) o por el tambor de la pantalla.
   Honestidad: la app mide CUÁNDO suena cada golpe y qué tan parejo es. No juzga técnica, sonido ni afinación (docs/RITMO.md).
   Contenido y textos: js/datos/ritmo.js. Se registra en Gioval.islas; el motor no conoce nada de esta isla. */
(function () {
const D = Gioval.datos.ritmo, TX = D.TEXTOS, AJ = D.AJUSTES, G = Gioval.entrada.proveedores.golpes;
/* ESC acelera TODO el reloj de la isla (solo para pruebas automáticas: window.__RITMO_ESCALA=5). En la app real es 1. */
const ESC = (typeof window.__RITMO_ESCALA === "number" && window.__RITMO_ESCALA > 0) ? window.__RITMO_ESCALA : 1;
const ms = x => x / ESC;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
function tx(path, v) {
  let o = TX; String(path).split(".").forEach(k => { o = o && o[k]; });
  if (Array.isArray(o)) o = rnd(o);
  if (typeof o !== "string") return "[" + path + "]";
  return o.replace(/\{(\w+)\}/g, (m, k) => (v && v[k] != null ? v[k] : m));
}
const ord = i => TX.ui.ordinales[Math.min(i, TX.ui.ordinales.length - 1)];

/* ============ PATRONES ============ T = ta (1 pulso), TT = ti-ti (2 golpes en 1 pulso), H = ta-a (1 golpe, dura 2), S = shh (silencio de 1) */
const DUR = { T: 1, TT: 1, S: 1, H: 2 };
function parse(str) {
  const toks = []; let b = 0;
  String(str).trim().split(/\s+/).forEach(k => { toks.push({ k, b, ons: k === "TT" ? [b, b + 0.5] : (k === "S" ? [] : [b]) }); b += DUR[k]; });
  const ons = [], tokDe = []; toks.forEach((t, i) => t.ons.forEach(o => { ons.push(o); tokDe.push(i); }));
  return { str: String(str).trim(), toks, L: b, ons, tokDe };
}
let ultimaLectura = "";
function genLectura(g) {
  for (let t = 0; t < 40; t++) {
    const toks = [];
    for (let c = 0; c < g.compases; c++) for (let i = 0; i < 4; i++) { const r = Math.random(); toks.push(g.tt && r < .3 ? "TT" : (g.s && r < (g.tt ? .55 : .3) ? "S" : "T")); }
    const golpes = toks.filter(k => k !== "S").length;
    if (golpes >= 2 + g.compases && (!g.s || toks.includes("S")) && (!g.tt || toks.includes("TT")) && toks.join() !== ultimaLectura) { ultimaLectura = toks.join(); return toks.join(" "); }
  }
  return g.tt ? "T TT S T" : "T T S T";
}

/* ============ EVALUACIÓN (funciones puras: se pueden probar sin pantalla) ============ */
const mediana = a => { if (!a.length) return 0; const b = a.slice().sort((x, y) => x - y), m = b.length >> 1; return b.length % 2 ? b[m] : (b[m - 1] + b[m]) / 2; };
const media = a => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
/* tolerancia (ms) según el nivel de ayuda (0 = más ayuda → ventana más ancha … 2 = sin ayuda) y el largo del pulso */
function ventana(lvl, beatMs) { const a = AJ.ventana; return clamp(a.frac[clamp(lvl | 0, 0, 2)] * beatMs, ms(a.minMs), ms(a.maxMs)); }
function veredicto(n, nOk, extras) { return n >= 6 ? (nOk / n >= AJ.aciertoMin && extras <= 1) : (nOk === n && extras === 0); }

/* ECO: se copia un ritmo. rel = instantes esperados relativos (ms, rel[0]=0); golpes = instantes del niño (ms). El primer golpe es el
   ancla (no se juzga cuándo empieza). Cada golpe se compara con el anterior (intervalo) o con el primero (posición): vale el más cercano. */
function evalIOI(rel, golpes, W) {
  const n = rel.length, h = golpes.slice().sort((a, b) => a - b), usado = new Set([0]), et = [], dc = [];
  const R_ = { n, etiquetas: et, extra: [], ok: false, desvio: 0, sesgo: 0, nOk: 0, golpes: h.length };
  if (!h.length) { for (let i = 0; i < n; i++) et.push({ i, estado: "falta" }); return R_; }
  et.push({ i: 0, estado: "ok", dev: 0 }); let prev = h[0]; const h0 = h[0];
  for (let i = 1; i < n; i++) {
    const gap = rel[i] - rel[i - 1], pc = prev + gap, pp = h0 + rel[i], Wm = Math.max(1.5 * W, 0.5 * gap);
    let mj = -1, md = 1e12;
    for (let j = 1; j < h.length; j++) { if (usado.has(j) || h[j] <= prev) continue; const d = Math.min(Math.abs(h[j] - pc), Math.abs(h[j] - pp)); if (d < md) { md = d; mj = j; } }
    if (mj < 0 || md > Wm) { et.push({ i, estado: "falta" }); prev = pc; continue; }
    usado.add(mj); const x = h[mj], a = x - pc, b = x - pp, d = Math.abs(a) <= Math.abs(b) ? a : b;
    et.push({ i, estado: Math.abs(d) <= W ? "ok" : (d < 0 ? "adelantado" : "atrasado"), dev: a }); dc.push(a); prev = x;
  }
  h.forEach((x, j) => { if (!usado.has(j)) R_.extra.push(x); });
  R_.nOk = et.filter(e => e.estado === "ok").length; R_.desvio = media(dc.map(Math.abs)); R_.sesgo = media(dc);
  R_.ok = veredicto(n, R_.nOk, R_.extra.length); return R_;
}
/* GRILLA: se toca sobre un pulso compartido. exp = instantes ABSOLUTOS esperados; se descuenta la demora fija (mediana) de la
   pantalla/micrófono/parlante, así que se mide la regularidad, no la latencia del aparato. */
function evalGrid(exp, golpes, W, beatMs, o) {
  o = o || {}; const n = exp.length;
  const lo = o.desde != null ? o.desde : exp[0] - 0.6 * beatMs, hi = o.hasta != null ? o.hasta : exp[n - 1] + 0.6 * beatMs;
  const h = golpes.filter(t => t >= lo && t <= hi).sort((a, b) => a - b);
  let minGap = beatMs; for (let i = 1; i < n; i++) minGap = Math.min(minGap, exp[i] - exp[i - 1]);
  const We = Math.min(W, 0.45 * minGap), et = [], R_ = { n, etiquetas: et, extra: [], extraSilencio: false, ok: false, desvio: 0, sesgo: 0, nOk: 0, golpes: h.length, We };
  const res = h.map(x => { let m = 1e12; exp.forEach(e => { if (Math.abs(x - e) < Math.abs(m)) m = x - e; }); return m; }).filter(r => Math.abs(r) <= 0.45 * minGap);
  const c = res.length >= 2 ? clamp(mediana(res), -0.45 * minGap, 0.45 * minGap) : 0; R_.sesgo = c;
  const hs = h.map(x => x - c), usado = new Set(), devs = [];
  for (let i = 0; i < n; i++) {
    let mj = -1, md = 1e12; for (let j = 0; j < hs.length; j++) { if (usado.has(j)) continue; const d = Math.abs(hs[j] - exp[i]); if (d < md) { md = d; mj = j; } }
    if (mj < 0 || md > Math.max(We * 1.4, 0.45 * minGap)) { et.push({ i, estado: "falta" }); continue; }
    usado.add(mj); const d = hs[mj] - exp[i]; devs.push(Math.abs(d));
    et.push({ i, estado: Math.abs(d) <= We ? "ok" : (d < 0 ? "adelantado" : "atrasado"), dev: d });
  }
  h.forEach((x, j) => { if (!usado.has(j)) R_.extra.push(x); });
  R_.nOk = et.filter(e => e.estado === "ok").length; R_.desvio = media(devs); R_.ok = veredicto(n, R_.nOk, R_.extra.length);
  if (o.silencios) R_.extraSilencio = R_.extra.some(x => o.silencios.some(s => Math.abs(x - c - s) < 0.5 * beatMs));
  return R_;
}
/* LIBRE (llamada y respuesta): cualquier ritmo, pero sobre la grilla de corcheas del pulso. */
function evalLibre(golpes, t0, beatMs, W, hasta) {
  const sub = beatMs / 2, h = golpes.filter(t => t >= t0 - 0.5 * beatMs && t <= (hasta != null ? hasta : t0 + 4.5 * beatMs)).sort((a, b) => a - b);
  const R_ = { n: h.length, ok: false, desvio: 0, sesgo: 0, motivo: null, golpes: h.length };
  if (!h.length) { R_.motivo = "vacio"; return R_; }
  let sx = 0, sy = 0; h.forEach(t => { const f = 2 * Math.PI * ((((t - t0) % sub) + sub) % sub) / sub; sx += Math.cos(f); sy += Math.sin(f); });
  const c = Math.atan2(sy, sx) / (2 * Math.PI) * sub, res = h.map(t => { let r = ((t - t0 - c) % sub + sub) % sub; if (r > sub / 2) r -= sub; return r; });
  R_.sesgo = c; R_.desvio = media(res.map(Math.abs)); const We = Math.min(W, 0.4 * sub);
  if (h.length < 2) R_.motivo = "pocos"; else if (h.length > 8) R_.motivo = "muchos"; else if (Math.max(...res.map(Math.abs)) > We) R_.motivo = "desparejo";
  R_.ok = !R_.motivo; return R_;
}

/* ============ SONIDO: percusión de juguete (osciladores y ruido; sin archivos) ============ */
let ruido = null;
function bufRuido(c) {
  if (ruido && ruido.sampleRate === c.sampleRate) return ruido;
  const n = Math.round(c.sampleRate * 0.3), b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); let s = 12345;
  for (let i = 0; i < n; i++) { s = (s * 1664525 + 1013904223) >>> 0; d[i] = s / 2147483648 - 1; }
  return (ruido = b);
}
function voz(nombre, vol, cuando) {
  const c = ensureCtx(), t = cuando != null ? cuando : c.currentTime, g = c.createGain(); g.connect(c.destination);
  const tono = (tipo, f0, f1, dur) => { const o = c.createOscillator(); o.type = tipo; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur * .6); o.connect(g); o.start(t); o.stop(t + dur + .05); };
  const sopla = (filtro, f, dur) => { const s = c.createBufferSource(); s.buffer = bufRuido(c); const fl = c.createBiquadFilter(); fl.type = filtro; fl.frequency.value = f; s.connect(fl); fl.connect(g); s.start(t); s.stop(t + dur); };
  if (nombre === "tambor") { g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(.001, t + .26); tono("sine", 200, 70, .26); sopla("lowpass", 900, .04); }
  else if (nombre === "madera") { g.gain.setValueAtTime(vol * .9, t); g.gain.exponentialRampToValueAtTime(.001, t + .11); tono("triangle", 950, 640, .11); }
  else if (nombre === "tic2") { g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(.001, t + .05); sopla("highpass", 4500, .05); tono("sine", 1500, 1400, .05); }
  else { g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(.001, t + .03); sopla("highpass", 5500, .03); }
}
Gioval.sonido.registrarInstrumento("percusion", { nombre: "Percusión de juguete", tocar(midi, dur, vol, c) { voz(midi >= 76 ? "madera" : "tambor", vol, c.currentTime); }, programar: voz });
const ctxDe = tp => ensureCtx().currentTime + Math.max(0, tp - performance.now()) / 1000;
const sonar = (nombre, vol, tp) => { try { voz(nombre, vol, ctxDe(tp)); } catch (e) {} };

/* ============ ESTADO ============ */
const R = { escala: ESC, tid: 0, fase: "idle", turno: null, cur: null, cap: null, repetir: false, compose: null, evaluar: { ioi: evalIOI, grid: evalGrid, libre: evalLibre }, ventana, parse, tx };
Gioval.ritmo = R;
const sleepT = t => new Promise(r => setTimeout(r, Math.max(0, t)));
const luz = (tp, run, fn) => setTimeout(() => { if (run === S.run) fn(); }, Math.max(0, tp - performance.now()));
const modoMic = () => !!(G.activo && G.fuente === "mic");

/* ============ PANTALLA ============ */
const CSS = `
#rit .rtBody{flex:1;display:flex;flex-direction:column;gap:8px;min-height:0}
#rit .rtScene>*{flex:none}
#rit.comp .rtPad,#rit.comp .rtMic{height:min(16vh,110px)}
#rit .rtScene{flex:1 1 0;min-height:0;background:rgba(255,255,255,.55);border-radius:26px;padding:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;overflow:hidden;text-align:center}
#rit .rtMsg{font-weight:900;font-size:clamp(20px,4.2vh,32px);color:#7c4dff;line-height:1.1;min-height:1.1em}
#rit .rtMsg b{font-size:1.6em;display:block;font-weight:400}
#rit .rtCards{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;width:100%;max-width:520px}
#rit .rc{display:flex;flex-direction:column;align-items:center;gap:1px;transition:transform .08s}
#rit .rc.h{grid-column:span 2}
#rit .rc span{font-weight:900;font-size:clamp(13px,2.4vw,18px);color:#2b2350}
#rit .rcd{width:100%;min-height:clamp(34px,6.5vh,64px);border-radius:16px;display:flex;align-items:center;justify-content:center;gap:2px;background:#4d96ff;color:#fff;font-size:clamp(20px,4.4vh,34px);box-shadow:0 4px 0 rgba(0,0,0,.15)}
#rit .rcd b{font-weight:400;line-height:1}
#rit .rc.tt .rcd{background:#ff9f1c;font-size:clamp(15px,3.2vh,26px)}
#rit .rc.s .rcd{background:#d9d4ec;border:3px dashed #8d84b3}
#rit .rc.q .rcd{background:#fff;border:3px dashed #b9a6ff;color:#7c4dff;font-weight:900}
#rit .rc.on{transform:scale(1.12)}
#rit .rc.on .rcd{box-shadow:0 0 0 5px #ffd23f,0 4px 0 rgba(0,0,0,.15)}
#rit .rc.ok .rcd{box-shadow:0 0 0 4px #4cc86a}
#rit .rc.ko .rcd{box-shadow:0 0 0 4px #ff5a5f}
#rit .rtBeats{display:flex;gap:12px;justify-content:center;min-height:30px}
#rit .rtBeats i{width:clamp(22px,4vh,30px);height:clamp(22px,4vh,30px);border-radius:50%;background:#fff;border:3px solid #7c4dff;display:flex;align-items:center;justify-content:center;font-style:normal;font-weight:900;font-size:13px;color:#7c4dff}
#rit .rtBeats i.on{background:#7c4dff;color:#fff;transform:scale(1.25)}
#rit .rtBeats.off{visibility:hidden}
#rit .rtInput{flex:none;display:flex;flex-direction:column;gap:8px;align-items:stretch}
#rit .rtPad{border:0;border-radius:32px;background:radial-gradient(circle at 50% 30%,#ffe88a,#ff9f1c);box-shadow:0 8px 0 rgba(0,0,0,.2);height:min(30vh,230px);font-size:clamp(46px,9vh,76px);display:flex;flex-direction:column;align-items:center;justify-content:center;touch-action:manipulation;color:#2b2350;font-family:inherit;font-weight:900;line-height:1.1}
#rit .rtPad small{font-size:clamp(14px,2.6vh,20px)}
#rit .rtPad.hit{transform:translateY(6px);box-shadow:0 2px 0 rgba(0,0,0,.2);filter:brightness(1.12)}
#rit .rtMic{display:none;height:min(30vh,230px);border-radius:32px;background:#fff;box-shadow:0 6px 0 rgba(0,0,0,.14);flex-direction:column;align-items:center;justify-content:center;gap:8px;font-weight:900;font-size:clamp(18px,3.4vh,26px);padding:8px}
#rit .rtMic .big1{font-size:clamp(44px,8vh,66px);line-height:1}
#rit .rtMic .meter{width:80%;flex:none}
#rit .rtMic.hit .big1{transform:scale(1.25)}
#rit.micOn .rtPad{display:none}
#rit.micOn .rtMic{display:flex}
#rit .rtPal{display:none;gap:8px;justify-content:center}
#rit.comp .rtPal{display:flex}
#rit .rtPal button{flex:1;max-width:150px;border:0;border-radius:18px;font-family:inherit;font-weight:900;color:#fff;font-size:clamp(16px,3vh,22px);padding:6px 4px;box-shadow:0 4px 0 rgba(0,0,0,.2);display:flex;flex-direction:column;align-items:center}
#rit .rtPal button b{font-weight:400;font-size:1.5em}
#rit .rtCards .slot{min-height:clamp(34px,6.5vh,64px);border-radius:16px;border:3px dashed #b9a6ff;background:#fff;display:flex;align-items:center;justify-content:center;color:#b9a6ff;font-weight:900}
#rtCal .box{background:#fff;color:#2b2350;border-radius:26px;padding:18px 22px;max-width:min(90vw,440px);display:flex;flex-direction:column;gap:10px;align-items:center}
#rtCal .box h1{font-size:clamp(22px,4.4vw,34px);color:#7c4dff}
#rtCal .box .em{font-size:60px;line-height:1}
@media (max-width:640px){ #rtTitle{display:none} }
@media (max-height:480px) and (orientation:landscape){
  #rit .rtBody{flex-direction:row}
  #rit .rtScene{flex:1.35 1 0;padding:4px}
  #rit .rtInput{flex:1 1 0;justify-content:center}
  #rit .rtPad,#rit .rtMic{height:100%;min-height:90px}
  #rit .rtCards{max-width:none}
  #rit .rcd{min-height:34px;font-size:22px}
  #rit .rtMsg b{font-size:1.2em}
  #rit .rtBeats i{width:22px;height:22px}
}
`;
const DOM = {
  pantallas: `
  <style>${CSS}</style>
  <div class="screen juego" id="rit">
    <div class="bar">
      <button class="btn alt" id="rtBack">⬅<span class="lbl">${TX.ui.volver}</span></button>
      <div style="font-weight:800;font-size:clamp(18px,2.8vw,26px)" id="rtTitle"></div>
      <div style="display:flex;gap:8px"><button class="btn alt" id="rtHear">🔊<span class="lbl">${TX.ui.escuchar}</span></button><button class="btn" id="rtSkip">${TX.ui.seguir}</button></div>
    </div>
    <div class="prog" id="prog3"></div>
    <div class="rtBody">
      <div class="rtScene" id="rtScene">
        <div class="rtMsg" id="rtMsg"></div>
        <div class="rtCards" id="rtCards"></div>
        <div class="rtBeats off" id="rtBeats"><i>1</i><i>2</i><i>3</i><i>4</i></div>
        <div class="rtPal" id="rtPal"></div>
      </div>
      <div class="rtInput">
        <button class="rtPad" id="rtPad" aria-label="${TX.ui.padAlt}">🥁<small>${TX.ui.pad}</small></button>
        <div class="rtMic" id="rtMic"><div class="big1">🎤</div><div>${TX.ui.micEscucho}</div><div class="meter"><i id="rtMicNivel"></i></div><button class="btn alt" id="rtMicOff" style="padding:6px 14px;font-size:16px">${TX.ui.micPantalla}</button></div>
      </div>
    </div>
  </div>
  <div class="big" id="rtCal"><div class="box"><div class="em" id="rtCalEm">🤫</div><h1 id="rtCalT"></h1><div id="rtCalS" style="font-size:18px;font-weight:700"></div><div class="meter" style="width:100%"><i id="rtCalBar"></i></div><div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center"><button class="btn" id="rtCalOk">${TX.ui.cerrar}</button><button class="btn alt" id="rtCalPant">${TX.ui.usarPantalla}</button></div></div></div>`,
  panelArriba: `<div id="rtPanel" style="display:none"><label>${TX.panel.estado} <b id="rtPanelEstado"></b></label>
    <label>${TX.panel.nivel} <div class="meter"><i id="rtLevel"></i></div></label>
    <label>${TX.panel.sens} <input type="range" id="rtSens" min="25" max="400" value="100" style="flex:1"> <span id="rtSensVal">1.0×</span></label>
    <div style="display:flex;gap:8px;margin-top:6px"><button class="btn alt" id="rtRecal" style="padding:6px 14px;font-size:16px">${TX.panel.recalibrar}</button></div>
    <div class="note-hint">${TX.panel.pie}</div></div>`,
};

/* tarjetas de ritmo (colores y dibujos) */
const carta = (t, i, oculta) => {
  const k = t.k, em = k === "S" ? "🤫" : "🥁";
  if (oculta) return `<div class="rc q${k === "H" ? " h" : ""}" data-i="${i}"><div class="rcd"><b>?</b></div></div>`;
  return `<div class="rc ${k.toLowerCase()}" data-i="${i}"><div class="rcd">${k === "TT" ? `<b>${em}</b><b>${em}</b>` : `<b>${em}</b>`}</div><span>${TX.tarjeta[k]}</span></div>`;
};
const UI = {
  msg(em, t) { $("rtMsg").innerHTML = (em ? `<b>${em}</b>` : "") + (t || ""); },
  cartas(P, oculta) { $("rtCards").innerHTML = P ? P.toks.map((t, i) => carta(t, i, oculta)).join("") : ""; $("rtCards").style.display = P ? "" : "none"; },
  marca(i, cls, quitar) { const e = $("rtCards").querySelector(`.rc[data-i="${i}"]`); if (!e) return; if (quitar) e.classList.remove(cls); else e.classList.add(cls); },
  limpiaMarcas(cls) { $("rtCards").querySelectorAll(".rc").forEach(e => e.classList.remove(cls)); },
  latidos(visible) { $("rtBeats").classList.toggle("off", !visible); $("rtBeats").querySelectorAll("i").forEach(e => e.classList.remove("on")); },
  latido(i) { $("rtBeats").querySelectorAll("i").forEach((e, k) => e.classList.toggle("on", k === i)); },
  pad(fuerza) { const p = $("rtPad"), m = $("rtMic"); p.classList.add("hit"); m.classList.add("hit"); setTimeout(() => { p.classList.remove("hit"); m.classList.remove("hit"); }, 110); },
  modo() { $("rit").classList.toggle("micOn", modoMic()); },
};

/* ============ ENTRADA DE GOLPES ============ */
function captura(run, cfg) {
  return new Promise(res => {
    const hits = [], ini = performance.now(); let hecho = false, iv = null;
    const baja = Gioval.entrada.suscribir("golpe", ev => {
      if (ev.t < cfg.desde) return; const u = hits[hits.length - 1]; if (u && ev.t - u.t < ms(40)) return;
      const h = { t: ev.t, fuerza: ev.fuerza, fuente: ev.fuente || "toque" }; hits.push(h); cfg.alGolpe && cfg.alGolpe(h, hits);
    });
    const fin = m => { if (hecho) return; hecho = true; baja(); clearInterval(iv); R.cap = null; res({ hits, motivo: m }); };
    iv = setInterval(() => {
      if (run !== S.run) return fin("cancelado");
      if (R.repetir) { R.repetir = false; return fin("repetir"); }
      const r = cfg.fin(hits, performance.now(), ini); if (r) fin(r === true ? "fin" : r);
    }, 25);
    R.cap = { fin };
  });
}
function panelEstado() {
  const st = G.estado(), e = $("rtPanelEstado"); if (!e) return;
  e.textContent = (G.activo && G.fuente === "mic") ? tx("panel.estadoOk", { piso: st.piso.toFixed(4), umbral: st.umbral.toFixed(4) }) : TX.panel.estadoApagado;
}
const MIC_OPTS = {
  nivel: r => { const w = Math.min(100, r * 600) + "%"; $("rtMicNivel").style.width = w; $("rtLevel").style.width = w; },
  alGolpe: () => UI.pad(),
  alCalibrando: f => { $("rtCalBar").style.width = Math.round(f * 100) + "%"; $("rtCalS").textContent = tx("ui.calibrandoSub", { s: Math.max(0, Math.ceil((1 - f) * G.PARAMS.calibracionMs / 1000)) }); },
  alApagar: () => { UI.modo(); panelEstado(); },
};
async function encenderMic() {
  ensureCtx(); $("rtCal").classList.add("show"); $("rtCalEm").textContent = "🤫"; $("rtCalT").textContent = TX.ui.calibrando; $("rtCalBar").style.width = "0%"; $("rtCalS").textContent = "";
  await speak(tx("voz.micPedir"));
  let fallo = false;
  const fuente = await G.iniciar(Object.assign({}, MIC_OPTS, { fuente: "mic", alError: () => { fallo = true; } }));
  if (fuente !== "mic") { $("rtCal").classList.remove("show"); UI.modo(); panelEstado(); await speak(TX.voz.micError); renderMenuIsla(); return; }
  UI.modo();
  const info = await G.calibrar();
  if (!info) { $("rtCal").classList.remove("show"); return; }
  const nivel = info.umbral > 0.06 ? "alto" : (info.umbral > 0.025 ? "medio" : "bajo");
  $("rtCalEm").textContent = nivel === "alto" ? "🔊" : "🎤"; $("rtCalT").textContent = TX.ui.calibrado; $("rtCalS").textContent = TX.ui.ruido[nivel]; $("rtCalBar").style.width = "100%";
  panelEstado();
  const baja = Gioval.entrada.suscribir("golpe", ev => { if (ev.fuente !== "mic") return; baja(); $("rtCalEm").textContent = "👏"; $("rtCalT").textContent = TX.ui.oi; speak(tx("voz.micOyo")); setTimeout(() => $("rtCal").classList.remove("show"), 1100); renderMenuIsla(); });
  R.calBaja = baja;
  speak(nivel === "alto" ? tx("voz.micMucho") : tx("voz.micListo"));
  renderMenuIsla();
}
function apagarMic() { if (R.calBaja) { R.calBaja(); R.calBaja = null; } if (G.activo) G.detener(); $("rtCal").classList.remove("show"); UI.modo(); panelEstado(); }

/* ============ REGISTRO (para el informe de adultos) ============ */
function registrar(it, r, mt, nivel) {
  if (!r || r.vacio) return;
  const L = ((store.ritmo = store.ritmo || {})[KID] = store.ritmo[KID] || []);
  const fuente = (r.fuentes && r.fuentes.includes("mic")) ? "m" : "t";
  L.push({ t: Date.now(), s: it.skill.id, d: Math.round(r.desvio || 0), b: Math.round(r.sesgo || 0), n: r.n || 0, o: r.nOk != null ? r.nOk : 0, x: (r.extra || []).length, f: fuente, bpm: Math.round(mt.bpmReal / ESC), l: nivel, c: S.check ? 1 : 0, ok: r.ok ? 1 : 0 });
  if (L.length > 600) L.splice(0, L.length - 600);
  save();
}

/* ============ SECUENCIAS ============ */
/* suena un patrón (instrumento "tambor") a partir de t0 (performance.now()) con luces en las tarjetas; devuelve el instante final */
function sonarPatron(run, P, t0, beatMs, luces, vol) {
  P.toks.forEach((t, i) => {
    t.ons.forEach(o => sonar("tambor", vol != null ? vol : AJ.volumen.modelo, t0 + o * beatMs));
    if (luces) { luz(t0 + t.b * beatMs, run, () => { UI.limpiaMarcas("on"); UI.marca(i, "on"); }); luz(t0 + (t.b + Math.min(DUR[t.k], 1)) * beatMs - 30, run, () => UI.marca(i, "on", true)); }
  });
  return t0 + P.L * beatMs;
}
const tipoFamilia = t => ({ eco: "eco", tempo: "eco", base: "grid", solo: "grid", silencio: "grid", lectura: "grid", cancion: "grid", llamada: "libre", compone: "compone" })[t];

function mensajeFalla(r, P) {
  const e = (r.etiquetas || []).find(x => x.estado === "adelantado" || x.estado === "atrasado");
  if (r.extraSilencio) return tx("voz.sobraSilencio");
  if ((r.etiquetas || []).some(x => x.estado === "falta")) return tx("voz.faltan");
  if ((r.extra || []).length) return tx("voz.sobra");
  if (e) return tx(e.estado === "adelantado" ? "voz.adelantado" : "voz.atrasado", { ord: ord(e.i) });
  return tx("voz.casi");
}
function pintaResultado(P, r) {
  if (!P || !r.etiquetas) return;
  r.etiquetas.forEach(e => { const i = P.tokDe[e.i]; if (i == null) return; UI.marca(i, e.estado === "ok" ? "ok" : "ko"); });
}

/* ---- intento de ECO: se escucha el ritmo y se repite ---- */
async function intentoEco(run, it, ss, ctxI) {
  const P = it.P, aid = ctxI.aid, fallos = ctxI.fallos;
  const bpmReal = it.bpm * ESC * (fallos >= 2 ? AJ.bajaTempoAyuda : 1), beatMs = 60000 / bpmReal, W = ventana(ctxI.lvl, beatMs);
  const ver = aid === 0 || fallos >= 1;
  UI.limpiaMarcas("ok"); UI.limpiaMarcas("ko"); UI.latidos(false); UI.cartas(ver ? P : null); UI.msg("👂", TX.tarjeta.mudoAyuda);
  R.fase = "modelo"; R.turno = null;
  await speak(ctxI.primera ? (TX.voz.intro[it.intro || it.skill.type] || TX.voz.intro.eco) : tx("voz.escucha")); if (run !== S.run) return { cancelado: true };
  if (it.tempoVoz && ctxI.primera) { await speak(tx("voz." + it.tempoVoz)); if (run !== S.run) return { cancelado: true }; }
  const t0 = performance.now() + 150, fin = sonarPatron(run, P, t0, beatMs, ver);
  muteUntil = Math.max(muteUntil, fin + beatMs + 250); G.limpiarMascaras();
  await sleepT(fin + beatMs * 0.6 - performance.now()); if (run !== S.run) return { cancelado: true };
  UI.limpiaMarcas("on"); UI.msg("🥁", tx("voz.turno"));
  await speak(tx("voz.turno")); if (run !== S.run) return { cancelado: true };
  const rel = P.ons.map(b => b * beatMs), n = rel.length, maxGap = Math.max(beatMs, ...rel.slice(1).map((x, i) => x - rel[i]));
  const desde = performance.now(); R.fase = "turno";
  R.turno = { id: ++R.tid, modo: "ioi", rel, n, beatMs, W, desde, aid, intento: ctxI.intento, skill: it.skill.id };
  const cap = await captura(run, {
    desde,
    alGolpe: (h, hs) => { const j = hs.length - 1; if (ver && j < n) UI.marca(P.tokDe[j], "ok"); UI.pad(); },
    fin: (h, now, ini) => {
      if (!h.length) return now - ini > ms(AJ.esperaPrimerGolpeMs) ? "vacio" : false;
      const ultimo = h[h.length - 1].t;
      if (h.length >= n) return now - ultimo > Math.max(beatMs * 0.9, ms(AJ.graciaMs));
      return now - ultimo > maxGap * 1.6 + ms(700);
    },
  });
  R.turno = null; R.fase = "feedback";
  if (cap.motivo === "cancelado") return { cancelado: true };
  if (cap.motivo === "repetir") return { repetir: true };
  if (cap.motivo === "vacio") return { vacio: true };
  const r = evalIOI(rel, cap.hits.map(h => h.t), W); r.fuentes = cap.hits.map(h => h.fuente);
  UI.limpiaMarcas("ok"); if (ver) pintaResultado(P, r);
  return Object.assign(r, { bpmReal, W, msg: r.ok ? null : mensajeFalla(r, P) });
}

/* ---- intento sobre GRILLA: cuenta de 4 clics y se toca sobre el pulso ---- */
async function intentoGrid(run, it, ss, ctxI) {
  const P = it.P, aid = ctxI.aid, fallos = ctxI.fallos, tipo = it.skill.type;
  const bpmReal = it.bpm * ESC * (fallos >= 2 ? AJ.bajaTempoAyuda : 1), beatMs = 60000 / bpmReal, W = ventana(ctxI.lvl, beatMs);
  const lee = tipo !== "base" && tipo !== "solo";
  const cartasVis = lee && (tipo === "lectura" || tipo === "compone" || aid <= 1 || fallos >= 1);   // canciones y silencios: sin ayuda no hay tarjetas
  const conModelo = (tipo === "lectura" || tipo === "cancion" || tipo === "silencio") && (aid === 0 || fallos >= 1 || (tipo === "silencio" && aid === 2));
  UI.limpiaMarcas("ok"); UI.limpiaMarcas("ko"); R.fase = "modelo"; R.turno = null; G.limpiarMascaras();
  UI.cartas(cartasVis ? P : null); UI.latidos(aid === 0); UI.msg(lee ? "👀" : "💓", lee ? TX.tarjeta.mudoAyuda : "");
  if (ctxI.primera || conModelo) { await speak(ctxI.primera ? (TX.voz.intro[it.intro || tipo] || TX.voz.intro.lectura) : tx("voz.escucha")); if (run !== S.run) return { cancelado: true }; }
  if (it.cancion && ctxI.primera) { await speak(it.cancion.nombre + "."); if (run !== S.run) return { cancelado: true }; }
  if (conModelo) {
    UI.msg("👂", TX.tarjeta.mudoAyuda);
    const t0m = performance.now() + 150, fm = sonarPatron(run, P, t0m, beatMs, true); muteUntil = Math.max(muteUntil, fm + 250);
    await sleepT(fm + beatMs * 0.4 - performance.now()); if (run !== S.run) return { cancelado: true };
    UI.limpiaMarcas("on");
  }
  await speak(tx("voz.cuenta")); if (run !== S.run) return { cancelado: true };
  /* cuenta y pulso */
  const nC = AJ.pulsosCuenta, tS = performance.now() + 200, t0 = tS + nC * beatMs, L = P.L;
  const apoyoN = tipo === "solo" ? it.skill.apoyo[clamp(aid, 0, 2)] : (aid <= 1 ? L : 0), clics = [];
  for (let i = 0; i < nC + L; i++) {
    const tp = tS + i * beatMs, enCuenta = i < nC;
    if (enCuenta || i - nC < apoyoN) { sonar(i % 4 === 0 ? "tic2" : "tic", AJ.volumen.base, tp); clics.push(tp); }
    if (enCuenta || (aid === 0 && i - nC < apoyoN)) luz(tp, run, () => UI.latido(i % 4));
    if (!enCuenta && cartasVis && lee) { const k = P.toks.findIndex(t => t.b <= i - nC && i - nC < t.b + DUR[t.k]); if (k >= 0 && aid === 0) luz(tp, run, () => { UI.limpiaMarcas("on"); UI.marca(k, "on"); }); }
  }
  luz(tS, run, () => UI.msg("", TX.ui.cuenta)); luz(t0 - 20, run, () => UI.msg("🥁", tx("voz.turno")));
  const exp = P.ons.map(b => t0 + b * beatMs), desde = t0 - 0.5 * beatMs, hasta = t0 + L * beatMs + 0.6 * beatMs;
  const silencios = P.toks.filter(t => t.k === "S").map(t => t0 + t.b * beatMs);
  R.fase = "turno"; R.turno = { id: ++R.tid, modo: "grid", esperados: exp, n: exp.length, beatMs, W, t0, desde, hasta, tS, aid, intento: ctxI.intento, skill: it.skill.id, silencios };
  /* el clic de la base puede colarse por el micrófono: se mide su demora en la cuenta y se lo enmascara después */
  let mascaraPuesta = false;
  const poneMascara = () => {
    mascaraPuesta = true; if (!modoMic()) return;
    const dem = []; cuenta.forEach(h => { const c = clics.filter(c => h.t - c >= -ms(20) && h.t - c <= ms(400)).pop(); if (c != null) dem.push(h.t - c); });
    if (dem.length < 2) return; const Ld = mediana(dem); R.eco = Ld;
    clics.filter(c => c >= t0 - 5).forEach(c => G.enmascarar(c + Ld - ms(14), c + Ld + ms(26)));
  };
  const cuenta = []; luz(t0 - 0.2 * beatMs, run, poneMascara);
  const cap = await captura(run, {
    desde: tS - 50,
    alGolpe: (h, hs) => { if (h.t < t0 - 0.5 * beatMs) { cuenta.push(h); return; } UI.pad(); const j = hs.filter(x => x.t >= t0 - 0.5 * beatMs).length - 1; if (cartasVis && j < exp.length) UI.marca(P.tokDe[j], "ok"); },
    fin: (h, now) => now > hasta + ms(80),
  });
  R.turno = null; R.fase = "feedback"; UI.latido(-1);
  if (cap.motivo === "cancelado") return { cancelado: true };
  if (cap.motivo === "repetir") return { repetir: true };
  const juz = cap.hits.filter(h => h.t >= desde && h.t <= hasta);
  if (!juz.length) return { vacio: true };
  const r = evalGrid(exp, juz.map(h => h.t), W, beatMs, { desde, hasta, silencios }); r.fuentes = juz.map(h => h.fuente);
  UI.limpiaMarcas("ok"); UI.limpiaMarcas("on"); if (cartasVis && lee) pintaResultado(P, r);
  return Object.assign(r, { bpmReal, W, msg: r.ok ? null : mensajeFalla(r, P) });
}

/* ---- intento de LLAMADA Y RESPUESTA: yo toco 4 pulsos, vos contestás lo que quieras sobre el pulso ---- */
async function intentoLibre(run, it, ss, ctxI) {
  const P = it.P, aid = ctxI.aid, fallos = ctxI.fallos;
  const bpmReal = it.bpm * ESC * (fallos >= 2 ? AJ.bajaTempoAyuda : 1), beatMs = 60000 / bpmReal, W = ventana(ctxI.lvl, beatMs);
  UI.limpiaMarcas("ok"); UI.limpiaMarcas("ko"); R.fase = "modelo"; R.turno = null; G.limpiarMascaras();
  UI.cartas(aid === 0 || fallos >= 1 ? P : null); UI.latidos(aid === 0); UI.msg("📣", TX.tarjeta.mudoAyuda);
  await speak(ctxI.primera ? TX.voz.intro.llamada : tx("voz.escucha")); if (run !== S.run) return { cancelado: true };
  const tL = performance.now() + 200, tR = tL + 4 * beatMs, fin = sonarPatron(run, P, tL, beatMs, aid === 0 || fallos >= 1); muteUntil = Math.max(muteUntil, tL + 4 * beatMs - 50);
  const clics = [];
  for (let i = 0; i < 8; i++) {
    const tp = tL + i * beatMs; if (i >= 4 && aid <= 1) { sonar(i % 4 === 0 ? "tic2" : "tic", AJ.volumen.base, tp); clics.push(tp); }
    if (aid === 0) luz(tp, run, () => UI.latido(i % 4));
  }
  UI.msg("🥁", tx("voz.turno")); luz(tR - 20, run, () => UI.msg("🥁", tx("voz.turno")));
  const hasta = tR + 4 * beatMs + 0.6 * beatMs;
  R.fase = "turno"; R.turno = { id: ++R.tid, modo: "libre", t0: tR, beatMs, W, desde: tR - 0.5 * beatMs, hasta, aid, intento: ctxI.intento, skill: it.skill.id, esperados: [] };
  if (modoMic() && R.eco != null) clics.forEach(c => G.enmascarar(c + R.eco - ms(14), c + R.eco + ms(26)));
  const cap = await captura(run, { desde: tR - 0.5 * beatMs, alGolpe: () => UI.pad(), fin: (h, now) => now > hasta + ms(80) });
  R.turno = null; R.fase = "feedback"; UI.latidos(false);
  if (cap.motivo === "cancelado") return { cancelado: true };
  if (cap.motivo === "repetir") return { repetir: true };
  const r = evalLibre(cap.hits.map(h => h.t), tR, beatMs, W, hasta); r.fuentes = cap.hits.map(h => h.fuente);
  if (r.motivo === "vacio") return { vacio: true };
  return Object.assign(r, { bpmReal, W, msg: r.ok ? tx("voz.libreOk") : tx(r.motivo === "pocos" ? "voz.libreMuyPoco" : (r.motivo === "muchos" ? "voz.libreMuchos" : "voz.libreDesparejo")) });
}

/* ---- COMPOSICIÓN: se eligen 4 tarjetas, se escucha y se toca ---- */
async function componer(run, it) {
  const N = D.COMPONER.pulsos; R.fase = "componer"; R.turno = null;
  const slots = []; R.compose = { slots, n: N, id: ++R.tid };
  $("rit").classList.add("comp"); UI.latidos(false); UI.msg("🎨", "");
  const pal = $("rtPal"); pal.innerHTML = D.COMPONER.fichas.map(k => `<button class="rtPal${k}" data-k="${k}" style="background:${k === "T" ? "#4d96ff" : k === "TT" ? "#ff9f1c" : "#8d84b3"}"><b>${k === "S" ? "🤫" : "🥁"}</b>${TX.ui.componer[k]}</button>`).join("") + `<button class="rtPalB" data-k="borrar" style="background:#fff;color:#2b2350"><b>↺</b>${TX.ui.componer.borrar.replace("↺ ", "")}</button>`;
  const dibuja = () => { $("rtCards").style.display = ""; $("rtCards").innerHTML = Array.from({ length: N }, (_, i) => slots[i] ? carta({ k: slots[i] }, i, false) : `<div class="slot">${i + 1}</div>`).join(""); };
  dibuja(); await speak(TX.voz.intro.compone); if (run !== S.run) return null;
  const str = await new Promise(res => {
    pal.onclick = e => {
      const b = e.target.closest("button"); if (!b || run !== S.run) return; const k = b.dataset.k;
      if (k === "borrar") { slots.length = 0; dibuja(); return; }
      if (slots.length >= N) return; slots.push(k); dibuja(); R.compose.slots = slots;
      if (slots.length === N) {
        if (slots.every(x => x === "S")) { slots.length = 0; setTimeout(() => { dibuja(); speak(TX.voz.componeAlMenos); }, 250); return; }
        setTimeout(() => res(slots.join(" ")), 350);
      }
    };
    const iv = setInterval(() => { if (run !== S.run) { clearInterval(iv); res(null); } }, 100); R.compose.iv = iv;
  });
  clearInterval(R.compose && R.compose.iv); pal.onclick = null; $("rit").classList.remove("comp"); R.compose = null; pal.innerHTML = "";
  return str;
}

/* ---- bucle de intentos común a todas las actividades ---- */
async function jugarItem(run, it, ss) {
  const sk = it.skill, fam = tipoFamilia(sk.type), st = SK(sk.id);
  S.mode = "play"; R.cur = it; UI.modo(); $("rit").classList.remove("comp");
  ss.seen = ss.seen || {};
  const check = !!S.check, max = check ? 1 : AJ.intentosMax;
  if (sk.type === "compone") {
    if (check) { it.str = genLectura({ tt: true, s: true, compases: 1 }); }
    else { const s = await componer(run, it); if (run !== S.run || s == null) return; it.str = s; it.P = parse(s);
      UI.cartas(it.P, false); UI.msg("👂", TX.voz.componeEscucha); await speak(TX.voz.componeEscucha); if (run !== S.run) return;
      const bm = 60000 / (it.bpm * ESC), t0 = performance.now() + 200, fin = sonarPatron(run, it.P, t0, bm, true); muteUntil = Math.max(muteUntil, fin + 250);
      await sleepT(fin + bm * .5 - performance.now()); if (run !== S.run) return; UI.limpiaMarcas("on"); }
    it.P = parse(it.str);
  }
  let fallos = 0, vacios = 0, intento = 0, primeraMedida = null, mt = { bpmReal: it.bpm * ESC };
  for (;;) {
    const ctxI = { aid: S.hint, lvl: st.lvl, fallos, intento: intento + 1, primera: !ss.seen[sk.type + (it.intro || "")] };
    ss.seen[sk.type + (it.intro || "")] = true;
    const r = await (fam === "eco" ? intentoEco : fam === "libre" ? intentoLibre : intentoGrid)(run, it, ss, ctxI);
    if (run !== S.run || r.cancelado) return;
    if (r.repetir) continue;
    if (r.vacio) { vacios++; if (vacios < 2 && !check) { await speak(tx("voz.sinGolpes")); if (run !== S.run) return; continue; } r.msg = tx("voz.pregunta"); }
    intento++;
    if (!r.vacio) { mt = r; if (!primeraMedida) { primeraMedida = r; registrar(it, r, r, st.lvl); } }
    if (r.ok) {
      S.mode = "between"; try { tone(76, .3, .16); } catch (e) {}
      if (!check) { UI.msg("🌟", ""); await sleepT(ms(500)); if (run !== S.run) return; }
      S.onDone({ miss: fallos, revealed: false }); return;
    }
    fallos++;
    if (check) { S.mode = "between"; S.onDone({ miss: 1 }); return; }
    if (fallos >= max) {
      S.mode = "between"; UI.msg("🤝", ""); await speak(TX.voz.revela); if (run !== S.run) return;
      if (it.P) { UI.cartas(it.P, false); const bm = 60000 / (it.bpm * ESC * AJ.bajaTempoAyuda), t0 = performance.now() + 200, fin = sonarPatron(run, it.P, t0, bm, true); muteUntil = Math.max(muteUntil, fin + 250); await sleepT(fin + bm * .5 - performance.now()); if (run !== S.run) return; UI.limpiaMarcas("on"); }
      S.onDone({ miss: fallos, revealed: true }); return;
    }
    S.mode = "between"; await speak(r.msg || tx("voz.casi")); if (run !== S.run) return; S.mode = "play";
  }
}

/* ============ HABILIDADES Y ACTIVIDADES ============ */
const SKILLS = D.HABILIDADES.map(h => Object.assign({}, h, { name: TX.hab[h.id.replace("rit_", "")] }));
const mkEco = s => { const str = pick(s.pats, "rp" + s.id); return { skill: s, str, P: parse(str), bpm: pick(s.bpms, "rb" + s.id), intro: s.intro }; };
const ACTIVIDADES = {
  eco: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 2, make: mkEco, jugar: jugarItem },
  tempo: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 2, jugar: jugarItem,
    make(s) { const t = pick(s.tempos, "rt" + s.id), str = pick(s.pats, "rp" + s.id); return { skill: s, str, P: parse(str), bpm: t.bpm, tempoVoz: t.voz }; } },
  base: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 1, jugar: jugarItem,
    make(s) { const str = Array(s.pulsos).fill("T").join(" "); return { skill: s, str, P: parse(str), bpm: pick(s.bpms, "rb" + s.id) }; } },
  solo: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 1, jugar: jugarItem,
    make(s) { const str = Array(s.pulsos).fill("T").join(" "); return { skill: s, str, P: parse(str), bpm: pick(s.bpms, "rb" + s.id) }; } },
  silencio: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 2, make: mkEco, jugar: jugarItem },
  lectura: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 2, jugar: jugarItem,
    make(s) { const str = genLectura(s.gen); return { skill: s, str, P: parse(str), bpm: pick(s.bpms, "rb" + s.id), intro: s.intro }; } },
  cancion: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 1, jugar: jugarItem,
    make(s) { const c = pick(D.CANCIONES, "rc"); return { skill: s, str: c.pat, P: parse(c.pat), bpm: pick(s.bpms, "rb" + s.id), cancion: c }; } },
  llamada: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 1, make: mkEco, jugar: jugarItem },
  compone: { okMsgs: TX.okMsgs, tolerancia: 1, chequeoItems: 1, jugar: jugarItem,
    make(s) { return { skill: s, str: "T T T T", P: parse("T T T T"), bpm: pick(s.bpms, "rb" + s.id) }; } },
};

/* ============ INFORME PARA ADULTOS ============ */
function informe(kid) {
  const L = (store.ritmo || {})[kid] || []; if (!L.length) return [];
  const I = TX.informe, out = [I.titulo, I.como], n = L.length, dm = Math.round(media(L.map(e => e.d)));
  const mic = L.filter(e => e.f === "m").length;
  out.push(tx("informe.general", { d: dm, n, mic, tq: n - mic }));
  const k = Math.min(10, Math.floor(n / 2));
  if (n >= AJ.minEvaluaciones) {
    const a = Math.round(media(L.slice(0, k).map(e => e.d))), b = Math.round(media(L.slice(-k).map(e => e.d))), dl = a - b;
    out.push(tx("informe.mejora", { k, a, b, delta: Math.abs(dl) < 8 ? I.mejoraIgual : (dl > 0 ? tx("informe.mejoraMenos", { x: dl }) : tx("informe.mejoraMas", { x: -dl })) }));
  } else out.push(tx("informe.pocos", { n: AJ.minEvaluaciones }));
  const dias = {}; L.forEach(e => { const d = new Date(e.t).toLocaleDateString("en-CA"); (dias[d] = dias[d] || []).push(e.d); });
  const lista = Object.keys(dias).sort().slice(-7).map(d => d.slice(8) + "/" + d.slice(5, 7) + " " + Math.round(media(dias[d])) + " ms").join(" · ");
  out.push(tx("informe.porDia", { lista }));
  const sg = Math.round(media(L.map(e => e.b)));
  out.push(tx("informe.sesgo", { dir: Math.abs(sg) < 15 ? I.sesgoNada : (sg < 0 ? I.sesgoAdelante : I.sesgoAtras), x: Math.abs(sg) }));
  const ph = {}; L.forEach(e => (ph[e.s] = ph[e.s] || []).push(e.d));
  out.push(tx("informe.porHab", { lista: SKILLS.filter(s => ph[s.id]).map(s => s.name + " " + Math.round(media(ph[s.id])) + " ms").join(" · ") }));
  out.push(I.aclaracion);
  return out;
}

/* ============ CÁSCARA DE LA ISLA ============ */
function iniciar() {
  const pad = $("rtPad");
  pad.addEventListener("pointerdown", e => { e.preventDefault(); ensureCtx(); G.pulsar({ t: e.timeStamp > 0 ? e.timeStamp : performance.now(), fuerza: 1 }); });
  /* todo golpe (pantalla, micrófono o prueba): destello; si es de la pantalla, suena el tambor del niño */
  Gioval.entrada.suscribir("golpe", ev => { if (!$("rit").classList.contains("active")) return; if (ev.fuente !== "mic") { UI.pad(); try { sonar("madera", AJ.volumen.pad * (0.6 + 0.4 * (ev.fuerza == null ? 1 : ev.fuerza)), performance.now()); } catch (e) {} } });
  $("rtBack").onclick = () => { S.run++; S.mode = "idle"; R.fase = "idle"; R.turno = null; try { speechSynthesis.cancel(); } catch (e) {} resetFlow(); goMenuIsla(); };
  $("rtSkip").onclick = () => { if (!S.session) return; const run = ++S.run; S.session.i++; renderProg(); nextItem(run); };
  $("rtHear").onclick = () => { if (R.cap && R.fase === "turno" && R.cur && tipoFamilia(R.cur.skill.type) === "eco") R.repetir = true; else if (R.cur) speak(TX.voz.intro[R.cur.skill.type] || TX.voz.escucha[0]); };
  $("rtMicOff").onclick = () => { apagarMic(); setBubble(TX.voz.modoPantalla); };
  $("rtCalOk").onclick = () => { if (R.calBaja) { R.calBaja(); R.calBaja = null; } $("rtCal").classList.remove("show"); };
  $("rtCalPant").onclick = () => { apagarMic(); renderMenuIsla(); };
  $("rtSens").oninput = e => { const v = +e.target.value / 100; $("rtSensVal").textContent = v.toFixed(1) + "×"; G.sensibilidad(v); };
  $("rtRecal").onclick = () => { if (modoMic()) { $("rtCal").classList.add("show"); $("rtCalT").textContent = TX.ui.calibrando; G.calibrar().then(info => { if (info) { $("rtCalT").textContent = TX.ui.calibrado; panelEstado(); } }); } };
  const mostrarPanel = on => { $("rtPanel").style.display = on ? "" : "none"; panelEstado(); };
  Gioval.on("menu", p => { if (p !== ISLA) apagarMic(); mostrarPanel(p === ISLA); });
  Gioval.on("mapa", () => { apagarMic(); mostrarPanel(false); });
  document.addEventListener("visibilitychange", () => { if (document.hidden && modoMic()) { apagarMic(); $("menuIsla").classList.contains("active") && renderMenuIsla(); } });
}
const ISLA = { id: "ritmo", name: TX.isla.nombre, emoji: TX.isla.emoji, sub: TX.isla.sub, skills: SKILLS, plain: true,
  instrumento: "percusion", entradas: ["golpe"], actividades: ACTIVIDADES, dom: DOM, iniciar,
  entrar(title) { $("rtTitle").textContent = title; $("rtMsg").innerHTML = ""; UI.cartas(null); UI.latidos(false); UI.modo(); show("rit"); },
  antesDeSesion() { R.cur = null; G.limpiarMascaras(); },
  tarjetas() { const m = modoMic(), c = m ? TX.ui.tarjetaMicOn : TX.ui.tarjetaMicOff; return [{ em: m ? "🥁" : "🎤", t: c.t, s: c.s, on: true, go: () => { if (m) { apagarMic(); setBubble(TX.voz.modoPantalla); renderMenuIsla(); } else encenderMic(); } }]; },
  informe,
  outro: "Ahora, ¡a tocar un tambor, una caja o las palmas de verdad!",
  capTail: "Ahora, a hacer ritmo con tus palmas o tu tambor. ¡Mañana seguimos!",
  notaInforme: "En Ritmo la app mide cuándo suenan los golpes y qué tan parejos son; la técnica y el sonido los ve un adulto.",
};
Gioval.islas.registrar(ISLA);
})();
