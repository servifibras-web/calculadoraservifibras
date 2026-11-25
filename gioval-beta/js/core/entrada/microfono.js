"use strict";
/* Proveedor "microfono": detecta UNA nota por vez (YIN) y emite
     { tipo:"nota", midi, midiFloat, cents, hz, afinacion, fuerza }
   midi       = la nota (número entero) YA corregida por la afinación del piano
   midiFloat  = la altura medida, con decimales y SIN corregir (60 = Do central, 60.5 = Do medio tono arriba)
   cents      = cuánto se aparta la nota detectada de `midi` (−50…+50; 100 cents = un semitono = una tecla)
   hz         = frecuencia medida;  afinacion = corrección (en cents) que se aplicó antes de redondear.
   Qué cambió respecto de la primera versión (ver docs/ENTRADAS_Y_SONIDO.md, "Si el piano no se escucha bien"):
   · rango de 80 a 1200 Hz (antes 170–1200: el Mi grave y todo lo de abajo no se oía);
   · la altura se afina entre muestras (antes error de hasta ±38 cents, y un piano de casa casi nunca está a 440 exactos);
   · si ningún valle llega al umbral de siempre (.15) se acepta un valle claro (< .3), y hace falta que al menos 2 de los
     "votos" coincidan en la misma altura;
   · AFINACIÓN DEL PIANO: corrección en cents que se aplica antes de redondear. Se estima sola con las notas naturales que se
     tocan (mediana, lenta, con tope de ±50) y se puede calibrar a mano con "Tocá un La"; se guarda en este aparato.
   La isla que lo usa pasa opciones a iniciar(opts):
     umbral()            -> sensibilidad (RMS mínimo, 0.001–0.03)
     nivel(rms)          -> para mostrar el volumen en el panel (opcional)
     alDetectar(midi, d) -> para mostrar la nota detectada; d = { hz, cents, midiFloat } (opcional)
     diagnostico(d)      -> en cada cuadro (cada ~30 ms): { rms, umbral, silenciado, hz, midi, cents, motivo } (opcional)
     envivo()            -> si devuelve false no se mide la nota "en vivo" (ahorra batería con el panel cerrado)
     alEncender()/alApagar()/alError(e) -> avisos a la interfaz (opcional)
   motivo = por qué se ignoró un sonido: "silenciado" (la app hablaba/tocaba), "bajo" (muy suave), "suena_anterior"
   (todavía sonaba la nota anterior), "sin_nota" (no se pudo saber qué nota era), "fuera_rango" (muy grave o muy aguda).
   El permiso y el flujo del micrófono se comparten con otros proveedores (golpes.js): M.flujo() abre el flujo una sola vez
   (cuenta cuántos lo usan) y M.soltar() lo cierra cuando ya no lo usa nadie. */
Gioval.entrada.registrarProveedor((function () {
  const M = { id: "microfono", tipos: ["nota"], activo: false, opts: {}, yin: null, yinDetalle: null, freqToMidi: null, midiFloat: null };
  const FMIN = 80, FMAX = 1200, W = 1024, UMBRAL_YIN = .15, UMBRAL_SUAVE = .3;
  const NATURALES = [0, 2, 4, 5, 7, 9, 11];
  let lastFrameT = 0, analyser = null, micStream = null, refs = 0, propio = false, timer = null, slow = 0, prevRms = 0, pending = false, votes = [], pendStart = 0, lastOnset = 0, onsetRms = 0, lastIgn = 0;
  M.vivo = { rms: 0, umbral: 0, silenciado: false, hz: null, midi: null, cents: null, motivo: null, motivoT: 0, ultimaNota: null, ultimaT: 0 };
  M.disponible = () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  /* flujo compartido: lo abre la primera vez y cuenta quién lo usa (así golpes.js no pide el permiso dos veces) */
  M.flujo = async function () {
    ensureCtx();
    if (!micStream) micStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
    refs++; return micStream;
  };
  M.soltar = function () {
    refs = Math.max(0, refs - 1);
    if (!refs && micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  };
  M.iniciar = async function (opts) {
    M.opts = opts || {};
    try {
      ensureCtx();
      const flujo = await M.flujo(); propio = true;
      const src = ctx.createMediaStreamSource(flujo);
      analyser = ctx.createAnalyser(); analyser.fftSize = 4096; analyser.smoothingTimeConstant = 0;
      src.connect(analyser);
      slow = prevRms = 0; pending = false; lastFrameT = 0;
      M.activo = true; M.opts.alEncender && M.opts.alEncender();
      timer = setInterval(frame, 30);
    } catch (e) {
      M.activo = false; M.opts.alError && M.opts.alError(e);
    }
  };
  M.detener = function () {
    M.activo = false; clearInterval(timer); cancelarCalibracion("apagado"); M.opts.alApagar && M.opts.alApagar();
    if (propio) { propio = false; M.soltar(); }
  };

  /* ---------------- YIN ----------------
     Devuelve { f, c, claro, tau } (f = null si no hay una nota clara).
     W = 1024 muestras como siempre; el rango baja a 80 Hz (maxTau = sr/80); el valle se afina entre muestras. */
  function yinDetalle(buf, sr, o) {
    const fmin = (o && o.fmin) || FMIN, fmax = (o && o.fmax) || FMAX, w = (o && o.W) || W;
    const maxTau = Math.floor(sr / fmin), minTau = Math.max(2, Math.floor(sr / fmax));
    const start = buf.length - w - maxTau - 4; if (start < 0) return { f: null, motivo: "corto" };
    const d = new Float32Array(maxTau + 2);
    for (let tau = 1; tau <= maxTau + 1; tau++) { let s = 0; for (let i = 0; i < w; i++) { const x = buf[start + i] - buf[start + i + tau]; s += x * x; } d[tau] = s; }
    const c = new Float32Array(maxTau + 2); c[0] = 1; let run = 0;
    for (let tau = 1; tau <= maxTau + 1; tau++) { run += d[tau]; c[tau] = d[tau] * tau / (run || 1); }
    if (run < 1e-9) return { f: null, motivo: "silencio" };   /* señal sin energía: no hay nota (antes daba 1200 Hz) */
    let tau = -1, claro = true;
    for (let t = minTau; t < maxTau; t++) { if (c[t] < UMBRAL_YIN) { while (t + 1 < maxTau && c[t + 1] < c[t]) t++; tau = t; break; } }
    if (tau < 0) {
      /* ningún valle llegó a .15 (timbres con fundamental débil, notas muy suaves, cuerdas desafinadas entre sí):
         se acepta el PRIMER valle claro (< .3) que sea casi tan profundo como el mejor (así no se salta a una octava más grave) */
      let mn = 1e9; const valles = [];
      for (let t = Math.max(minTau, 2); t < maxTau - 1; t++) if (c[t] <= c[t - 1] && c[t] <= c[t + 1]) { valles.push(t); if (c[t] < mn) mn = c[t]; }
      if (mn >= UMBRAL_SUAVE) return { f: null, motivo: "nada", c: mn };
      tau = valles.find(t => c[t] <= mn + .05); claro = false;
    }
    /* afinado entre muestras: se busca el mínimo de la diferencia con la copia desplazada una fracción de muestra
       (interpolación lineal) y se ajusta una parábola; el método de siempre (parábola sobre c) se equivoca hasta 38 cents */
    const Df = tf => { const ti = Math.floor(tf), fr = tf - ti; let s = 0; for (let i = 0; i < w; i++) { const y = fr ? buf[start + i + ti] * (1 - fr) + buf[start + i + ti + 1] * fr : buf[start + i + ti]; const x = buf[start + i] - y; s += x * x; } return s; };
    let best = Infinity, bt = tau; const paso = .25;
    for (let tf = tau - 1; tf <= tau + 1.0001; tf += paso) { const v = Df(tf); if (v < best) { best = v; bt = tf; } }
    const a = Df(bt - paso), b = best, g = Df(bt + paso); const den = a - 2 * b + g;
    const fino = den > 0 ? bt + paso * (a - g) / (2 * den) : bt;
    return { f: sr / fino, c: c[tau], claro, tau };
  }
  M.yinDetalle = yinDetalle;
  M.yin = (buf, sr) => yinDetalle(buf, sr).f;
  const midiFloat = f => 69 + 12 * Math.log2(f / 440);
  const hzDeMidi = m => 440 * Math.pow(2, (m - 69) / 12);
  /* nota entera para una frecuencia, con la afinación del piano ya aplicada (o la que se pase en cents) */
  function freqToMidi(f, afin) { return Math.round(midiFloat(f) - (afin == null ? M.afinacion() : afin) / 100); }
  M.freqToMidi = freqToMidi; M.midiFloat = midiFloat; M.hzDeMidi = hzDeMidi;

  /* ---------------- afinación del piano ----------------
     afinacion = cuántos cents SUENA el piano por encima (+) o por debajo (−) de lo normal (La = 440 Hz).
     Se resta de la altura medida antes de redondear a la nota. Queda guardada en este aparato (localStorage, no en el progreso
     de los chicos). */
  const CLAVE = () => Gioval.clave("gioval_afinacion");
  const A = { c: 0, auto: true, manual: false, muestras: [], cargada: false, ultimoCambio: 0 };
  const acotar = (x, a, b) => Math.max(a, Math.min(b, x));
  function cargarAfinacion() {
    if (A.cargada) return; A.cargada = true;
    try { const o = JSON.parse(localStorage.getItem(CLAVE()) || "null"); if (o && typeof o === "object") { if (isFinite(o.c)) A.c = acotar(+o.c, -50, 50); if (typeof o.auto === "boolean") A.auto = o.auto; A.manual = !!o.manual; } } catch (e) {}
  }
  function guardarAfinacion() { try { localStorage.setItem(CLAVE(), JSON.stringify({ c: Math.round(A.c * 10) / 10, auto: A.auto, manual: A.manual })); } catch (e) {} }
  M.afinacion = () => { cargarAfinacion(); return A.c; };
  M.afinacionAuto = v => { cargarAfinacion(); if (v === undefined) return A.auto; A.auto = !!v; if (!A.auto) A.muestras = []; guardarAfinacion(); return A.auto; };
  M.afinacionManual = () => { cargarAfinacion(); return A.manual; };
  M.fijarAfinacion = (c, manual) => { cargarAfinacion(); A.c = acotar(Math.round(+c * 10) / 10, -50, 50); A.manual = !!manual; A.muestras = []; A.ultimoCambio = performance.now(); guardarAfinacion(); M.opts.alAfinar && M.opts.alAfinar(A.c); };
  M.reiniciarAfinacion = () => { cargarAfinacion(); A.c = 0; A.manual = false; A.muestras = []; A.auto = true; A.ultimoCambio = performance.now(); guardarAfinacion(); M.opts.alAfinar && M.opts.alAfinar(0); };
  M.muestrasAfinacion = () => A.muestras.map(x => x.dev);
  /* la nota natural (Do Re Mi Fa Sol La Si, de cualquier octava) más cercana a una altura con decimales */
  function naturalCercana(m) { let mejor = null; for (let k = Math.floor(m) - 1; k <= Math.ceil(m) + 1; k++) if (NATURALES.includes(((k % 12) + 12) % 12) && (mejor === null || Math.abs(m - k) < Math.abs(m - mejor))) mejor = k; return mejor; }
  const mediana = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
  /* Estimación automática. Los ejercicios de los chicos usan solo notas naturales: la desviación de cada nota detectada respecto
     de la natural más cercana es, en promedio, la desafinación del piano.
     Guardas: solo detecciones claras · solo desvíos de hasta ±50 cents (así una tecla negra no cuenta) · hacen falta 6 muestras de
     al menos 3 notas distintas (un piano muy alto o muy bajo confunde a Mi/Fa y Si/Do: con 2 notas no se decide) · que se parezcan
     entre sí (MAD ≤ 15 cents) · no se mueve si la diferencia es menor a 8 cents · cada paso es la MITAD de la diferencia y como
     mucho 8 cents · tope total ±50. */
  M.aportarAfinacion = function (mf) {
    cargarAfinacion(); if (!A.auto) return false;
    const aj = mf - A.c / 100, N = naturalCercana(aj); if (Math.abs(aj - N) > .5) return false;
    A.muestras.push({ dev: (mf - N) * 100, pc: ((N % 12) + 12) % 12 }); if (A.muestras.length > 12) A.muestras.shift();
    if (A.muestras.length < 6 || new Set(A.muestras.map(x => x.pc)).size < 3) return false;
    const devs = A.muestras.map(x => x.dev), med = mediana(devs), mad = mediana(devs.map(x => Math.abs(x - med)));
    if (mad > 15 || Math.abs(med - A.c) < 8) return false;
    A.c = acotar(Math.round((A.c + acotar((med - A.c) * .5, -8, 8)) * 10) / 10, -50, 50); A.manual = false; A.ultimoCambio = performance.now(); guardarAfinacion();
    M.opts.alAfinar && M.opts.alAfinar(A.c); return true;
  };
  /* Calibración a mano: "Tocá un La". Mide la próxima nota (la que sea La, de cualquier octava), fija la corrección y NO la manda al juego.
     Devuelve una promesa con { ok, afinacion?, motivo?, escuche? }. */
  let calib = null;
  function cancelarCalibracion(motivo) { if (calib) { const c = calib; calib = null; clearTimeout(c.timer); c.res({ ok: false, motivo }); } }
  M.calibrarLa = function () {
    cancelarCalibracion("otra");
    return new Promise(res => { calib = { res, timer: setTimeout(() => cancelarCalibracion("tiempo"), 20000) }; });
  };
  M.calibrando = () => !!calib;
  function resolverCalibracion(r) {
    const c = calib; calib = null; clearTimeout(c.timer);
    if (!r) { c.res({ ok: false, motivo: "sin_nota" }); return; }
    const k = Math.round((r.mf - 9) / 12) * 12 + 9, dev = (r.mf - k) * 100;   /* La más cercano, de cualquier octava */
    if (Math.abs(dev) > 100) { c.res({ ok: false, motivo: "no_es_la", escuche: Math.round(r.mf) }); return; }
    M.fijarAfinacion(dev, true); c.res({ ok: true, afinacion: A.c, medido: dev, limitada: Math.abs(dev) > 50 });
  }

  /* ---------------- detección ---------------- */
  /* ¿de los votos, cuántos coinciden en una misma altura (±0,6 semitonos)? Devuelve el grupo más grande */
  function consenso(v) {
    if (v.length < 2) return null; let mejor = null;
    v.forEach(a => { const g = v.filter(b => Math.abs(b.mf - a.mf) <= .6); if (!mejor || g.length > mejor.length) mejor = g; });
    if (mejor.length < 2) return null;
    const mfs = mejor.map(x => x.mf);
    return { mf: mediana(mfs), n: mejor.length, spread: Math.max(...mfs) - Math.min(...mfs), claros: mejor.filter(x => x.claro).length };
  }
  M.consenso = consenso;
  function ignorar(motivo, now) {
    if (now - lastIgn < 500) return; lastIgn = now;
    M.vivo.motivo = motivo; M.vivo.motivoT = now;
  }
  function terminar(buf, now) {
    pending = false;
    const r = consenso(votes);
    if (!r) {
      /* ¿será que la nota está fuera del rango de 80–1200 Hz? se mira con un rango más amplio, solo cuando falla */
      let fuera = false;
      try { const x = yinDetalle(buf, ctx.sampleRate, { fmin: 40, fmax: 3000, W: 2048 }); if (x.f && (x.f < FMIN * .95 || x.f > FMAX * 1.05)) { fuera = true; M.vivo.fueraHz = x.f; } } catch (e) {}
      if (calib) resolverCalibracion(null);
      lastIgn = 0; ignorar(fuera ? "fuera_rango" : "sin_nota", now); return;
    }
    const aj = r.mf - M.afinacion() / 100, midi = Math.round(aj), cents = Math.round((aj - midi) * 100), hz = hzDeMidi(r.mf);
    if (calib) { resolverCalibracion(r); M.vivo.ultimaNota = null; return; }
    if (r.spread <= .35 && onsetRms >= (M.opts.umbral ? M.opts.umbral() : .008) * 1.5) M.aportarAfinacion(r.mf);
    M.vivo.ultimaNota = { midi, cents, hz, midiFloat: r.mf, t: now }; M.vivo.motivo = null;
    M.opts.alDetectar && M.opts.alDetectar(midi, { hz, cents, midiFloat: r.mf });
    Gioval.entrada.emitir({ tipo: "nota", midi, midiFloat: r.mf, cents, hz, afinacion: M.afinacion(), fuerza: Math.min(1, onsetRms * 8) });
  }
  /* ¿EMPEZÓ una nota ahora, o solo es una nota que ya sonaba y "late" (batido entre cuerdas, pedal, eco de la sala)?
     Se compara la energía máxima de bloques de 256 muestras (~6 ms) del tramo nuevo contra la de los bloques anteriores: un golpe de
     tecla sube de golpe (relación ≥ 3); un batido sube despacio (≈ 1,1 a 2,2). Sin esto, una nota larga se contaba dos veces. */
  M.cfg = { ataque: 3, ataqueFuerte: 3.5 };
  function ataque(buf, spanMs) {
    const B = 256, n = buf.length, sr = ctx.sampleRate, nb = Math.min(11, Math.ceil(spanMs * sr / 1000 / B) + 1);
    const e = k => { let s = 0; const a = n - (k + 1) * B; for (let i = a; i < a + B; i++) s += buf[i] * buf[i]; return s / B; };
    let mx = 0; for (let k = 0; k < nb; k++) mx = Math.max(mx, e(k));
    let old = 0; for (let k = nb; k < nb + 4; k++) old += e(k); old /= 4;
    return mx / (old || 1e-12);
  }
  function frame() {
    if (!analyser) return;
    const buf = new Float32Array(analyser.fftSize); analyser.getFloatTimeDomainData(buf);
    let s = 0; for (let i = buf.length - 1024; i < buf.length; i++) s += buf[i] * buf[i]; const rms = Math.sqrt(s / 1024);
    M.opts.nivel && M.opts.nivel(rms);
    const now = performance.now(), thr = M.opts.umbral ? M.opts.umbral() : .008; // 0.001 – 0.03
    const mudo = typeof muteUntil !== "undefined" && now < muteUntil;
    const V = M.vivo; V.rms = rms; V.umbral = thr; V.silenciado = mudo; V.hz = V.midi = V.cents = null;
    /* nota "en vivo" para el panel de adultos (solo si lo piden y hay un sonido apreciable) */
    if (M.opts.diagnostico && (!M.opts.envivo || M.opts.envivo()) && !mudo && rms > thr * .6) {
      const x = yinDetalle(buf, ctx.sampleRate);
      if (x.f) { const mf = midiFloat(x.f), aj = mf - M.afinacion() / 100; V.hz = x.f; V.midi = Math.round(aj); V.cents = Math.round((aj - V.midi) * 100); }
    }
    if (mudo) {
      if (rms > thr && rms > prevRms * 1.4) ignorar("silenciado", now);
      slow = rms; prevRms = rms; pending = false;
      M.opts.diagnostico && M.opts.diagnostico(V); return;
    }
    const span = lastFrameT ? now - lastFrameT : 30; lastFrameT = now;
    /* inicio de nota: subió el volumen (más de 1,4 veces el nivel de fondo) y de golpe (≥ 3); o, si el nivel de fondo todavía es alto
       (eco de la nota anterior), un golpe un poco más marcado (≥ 3,5) */
    const sube = rms > thr && (() => { const a = V.ataque = ataque(buf, span); return a >= (rms > slow * 1.4 ? M.cfg.ataque : M.cfg.ataqueFuerte); })();
    if (!pending && sube && now - lastOnset > 140) { pending = true; votes = []; pendStart = now; lastOnset = now; onsetRms = rms; }
    else if (!pending && now - lastOnset > 140) {
      if (rms > thr && rms > prevRms * 1.25 && rms > slow * 1.1) ignorar("suena_anterior", now);
      else if (rms > thr * .4 && rms <= thr && rms > prevRms * 1.4 && rms > slow * 1.4) ignorar("bajo", now);
    }
    if (pending) {
      if (now - pendStart > 70) { const x = yinDetalle(buf, ctx.sampleRate); if (x.f) votes.push({ mf: midiFloat(x.f), c: x.c, claro: x.claro }); }
      const c = votes.length >= 3 ? consenso(votes) : null;
      if ((c && votes.length >= 3) || votes.length >= 5 || now - pendStart > 380) terminar(buf, now);
    }
    /* nivel de fondo: sube despacio (.15) pero BAJA rápido (.6): tras soltar una tecla, la nota siguiente no queda tapada por el eco del nivel */
    slow = rms < slow ? slow * .4 + rms * .6 : slow * .85 + rms * .15; prevRms = rms;
    M.opts.diagnostico && M.opts.diagnostico(V);
  }
  return M;
})());
