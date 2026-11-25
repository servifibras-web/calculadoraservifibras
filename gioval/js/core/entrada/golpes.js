"use strict";
/* Proveedor "golpes": detecta CUÁNDO suena un golpe (palmas, cajón, bongó, pandereta, tambor, objetos de cocina) y emite
     { tipo:"golpe", t, fuerza, fuente:"mic"|"toque" }      t = performance.now() del INICIO del golpe (ms), fuerza 0..1
   Qué hace y qué NO hace (importante, ver docs/RITMO.md):
     - SÍ mide el instante en que empieza un sonido corto y fuerte, y aproximadamente qué tan fuerte fue.
     - NO reconoce qué instrumento es, ni si el golpe está "bien dado", ni la afinación. No juzga técnica.
   Cómo funciona (por micrófono):
     1. Comparte el permiso/flujo del micrófono con microfono.js (M.flujo()/M.soltar()); no abre otro.
     2. Un AnalyserNode entrega las últimas muestras; se alinean EXACTAMENTE con lo ya procesado (así no se pierde ni se
        repite ninguna muestra) y el tiempo de cada golpe sale del reloj de audio, no del temporizador (error de pocos ms).
     3. Energía (RMS) cada ~3 ms. Hay golpe cuando la energía supera el umbral (ruido de fondo medido x factor) Y sube de golpe
        respecto de los ~45 ms anteriores. Período refractario 110 ms (un rasgueo o un rebote cuentan como UN golpe).
     4. Calibración de 3 s al encender: mide el ruido de fondo (percentil 95) y arma el umbral. Después el piso se adapta
        despacio si el ruido de la sala cambia.
     5. Silencia la escucha mientras la app suena (muteUntil, de voz.js) y en las ventanas que la isla marque con
        enmascarar(desde,hasta) (por ejemplo, el clic de la base): así no se escucha a sí misma.
   Fallback sin instrumento: pulsar({t,fuerza}) emite el mismo evento "golpe" con fuente:"toque" (la isla dibuja el pad).
   NOTA: no emite eventos "toque": la isla de Música escucha "toque" con notas de piano y se rompería.
   Parámetros ajustables: Gioval.entrada.proveedores.golpes.PARAMS (ver docs/RITMO.md). */
Gioval.entrada.registrarProveedor((function () {
  const mic = Gioval.entrada.proveedores.microfono;
  const G = { id: "golpes", tipos: ["golpe"], activo: false, fuente: null, opts: {}, sens: 1, huecos: 0 };
  G.PARAMS = {
    hopMs: 3,              // cada cuántos ms se mide la energía
    calibracionMs: 3000,   // duración de la calibración del ruido de fondo (tiempo "útil", sin contar la voz de la app)
    maxCalibracionMs: 12000, // tope de espera si la app habla casi todo el tiempo
    factor: 3.5,           // umbral = ruido de fondo (p95) x factor
    rmsMin: 0.010,         // umbral mínimo absoluto (RMS, 0..1) aunque la sala sea muy silenciosa
    salto: 1.9,            // el golpe debe subir esto respecto de los ~45 ms anteriores
    contextoMs: 45,        // ventana "de antes" para medir la subida
    refractarioMs: 110,    // mínimo entre golpes
    picoMs: 40,            // se espera esto para medir la fuerza (el instante t es el del inicio)
    tauPisoMs: 4000,       // qué tan rápido se adapta el piso a cambios del ruido de fondo
    gananciaFuerza: 30,    // dB por encima del umbral que equivalen a fuerza 1
    ventanaMax: 4,         // el piso adaptado nunca sube más de esto x lo calibrado
  };
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

  /* ============ DETECTOR PURO (sin audio ni DOM: se puede probar con señales sintéticas) ============ */
  G.crearDetector = function (sr, params) {
    const P = Object.assign({}, G.PARAMS, params || {});
    const hop = Math.max(16, Math.round(sr * P.hopMs / 1000)), hopMs = hop * 1000 / sr;
    const nCtx = Math.max(3, Math.round(P.contextoMs / hopMs));
    const hist = new Float32Array(nCtx); let hn = 0, hi = 0;
    const D = { sr, hop, P, sens: 1, calibrado: false, piso: 0, pisoCal: 0, muCal: 1e-5, mu: 0, umbral: Math.max(P.rmsMin, 0.02), cal: null, alCalibrado: null };
    let resto = new Float32Array(0), ultimo = -1e9, pend = null;
    const umbralDe = () => Math.max(P.rmsMin, D.piso * P.factor) / D.sens;
    D.calibrar = function (ms) { D.cal = { vals: [], util: 0, total: 0, ms: ms || P.calibracionMs }; D.calibrado = false; return D; };
    function cerrarCalibracion() {
      const v = D.cal.vals.slice().sort((a, b) => a - b); let mean = 0; v.forEach(x => (mean += x)); mean = v.length ? mean / v.length : 0;
      const p95 = v.length ? v[Math.min(v.length - 1, Math.floor(v.length * 0.95))] : 0;
      D.pisoCal = Math.max(p95, mean); D.piso = D.pisoCal; D.muCal = Math.max(mean, 1e-5); D.mu = D.muCal; D.calibrado = true;
      D.umbral = umbralDe();
      const info = { piso: D.pisoCal, media: mean, umbral: D.umbral, muestras: v.length, utilMs: D.cal.util };
      D.cal = null; D.info = info; if (D.alCalibrado) D.alCalibrado(info);
    }
    /* feed(bloque, tFinMs, mudo?) -> eventos {t,fuerza,rms} listos.  bloque = muestras NUEVAS y contiguas con las anteriores;
       tFinMs = instante de la ÚLTIMA muestra; mudo(t) = true si ese instante está silenciado (voz de la app, ventanas) */
    D.feed = function (bloque, tFin, mudo) {
      const out = [], total = resto.length + bloque.length;
      let x = bloque;
      if (resto.length) { x = new Float32Array(total); x.set(resto, 0); x.set(bloque, resto.length); }
      const msPorMuestra = 1000 / sr; let k = 0;
      for (; k + hop <= total; k += hop) {
        const t0 = tFin - (total - 1 - k) * msPorMuestra;     // instante de la primera muestra del hop
        let s = 0, mx = 0, imx = 0; for (let i = k; i < k + hop; i++) { const v = x[i]; s += v * v; const a = v < 0 ? -v : v; if (a > mx) { mx = a; } }
        const e = Math.sqrt(s / hop), tc = t0 + hopMs / 2, silen = !!(mudo && mudo(tc));
        if (D.cal) {                                            // calibrando: solo cuenta el tiempo no silenciado
          D.cal.total += hopMs;
          if (!silen) { D.cal.vals.push(e); D.cal.util += hopMs; }
          if (D.cal.util >= D.cal.ms || (D.cal.total >= P.maxCalibracionMs && D.cal.util >= 800)) cerrarCalibracion();
          hist[hi] = e; hi = (hi + 1) % nCtx; hn = Math.min(nCtx, hn + 1); continue;
        }
        const um = D.umbral = umbralDe();
        let prev = 0; for (let i = 0; i < hn; i++) prev += hist[i]; prev = hn ? prev / hn : 0;
        if (pend) {                                             // midiendo el pico para la fuerza
          if (e > pend.pico) pend.pico = e;
          if (tc >= pend.t + P.picoMs) { out.push({ t: pend.t, rms: pend.pico, fuerza: clamp(20 * Math.log10(pend.pico / pend.um) / P.gananciaFuerza, 0, 1) }); pend = null; }
        } else if (D.calibrado && !silen && e >= um && e >= P.salto * Math.max(prev, D.piso) && tc - ultimo >= P.refractarioMs) {
          let ti = 0; for (let i = 0; i < hop; i++) { const v = x[k + i]; if ((v < 0 ? -v : v) >= 0.35 * mx) { ti = i; break; } }
          const tOn = t0 + ti * msPorMuestra; ultimo = tOn; pend = { t: tOn, pico: e, um };
        } else if (D.calibrado && !silen && e < um) {           // adaptar el piso al ruido de la sala (despacio)
          D.mu += (e - D.mu) * (1 - Math.exp(-hopMs / P.tauPisoMs));
          D.piso = D.pisoCal * clamp(D.mu / D.muCal, 0.5, P.ventanaMax);
        }
        hist[hi] = e; hi = (hi + 1) % nCtx; hn = Math.min(nCtx, hn + 1);
      }
      resto = x.slice(k);
      return out;
    };
    D.sensibilidad = v => { D.sens = clamp(v || 1, 0.25, 4); return D; };
    return D;
  };

  /* Prueba sin navegador de audio: procesa una señal entera (como llegaría por bloques) y devuelve los golpes con t en ms
     desde la muestra 0. La calibración usa los primeros calMs. */
  G.simular = function (muestras, sr, o) {
    o = o || {}; const det = G.crearDetector(sr, o.params); det.calibrar(o.calMs || G.PARAMS.calibracionMs); if (o.sens) det.sensibilidad(o.sens);
    const B = o.bloque || 512, ev = [], mudo = o.mudo || null;
    for (let i = 0; i < muestras.length; i += B) {
      const b = muestras.subarray ? muestras.subarray(i, Math.min(muestras.length, i + B)) : Float32Array.from(muestras.slice(i, i + B));
      det.feed(b, (i + b.length - 1) * 1000 / sr, mudo).forEach(e => ev.push(e));
    }
    return { eventos: ev, info: det.info || null, detector: det };
  };

  /* ============ PROVEEDOR (micrófono real) ============ */
  let perdidas = 0, analyser = null, timer = null, tieneFlujo = false, det = null, buf = null, prev = null, lastCt = 0, nAbs = 0, off = null, tFrame = 0, mascaras = [], calProm = null, calRes = null;
  G.detector = () => det;                                   // para pruebas y diagnóstico
  G.disponible = () => true;                                // siempre: si no hay micrófono queda el pad en pantalla
  G.micDisponible = () => mic.disponible();
  G.estado = () => ({ activo: G.activo, fuente: G.fuente, calibrado: !!(det && det.calibrado), piso: det ? det.piso : 0, umbral: det ? det.umbral : 0, huecos: G.huecos, sens: G.sens });
  G.sensibilidad = v => { G.sens = clamp(v || 1, 0.25, 4); if (det) det.sensibilidad(G.sens); return G.sens; };
  G.enmascarar = (desde, hasta) => { mascaras.push([desde, hasta]); if (mascaras.length > 200) mascaras.splice(0, mascaras.length - 200); };
  G.limpiarMascaras = () => { mascaras = []; };
  const silenciado = t => { if (typeof muteUntil !== "undefined" && t < muteUntil) return true; for (let i = mascaras.length - 1; i >= 0; i--) if (t >= mascaras[i][0] && t <= mascaras[i][1]) return true; return false; };
  G.silenciado = silenciado;

  G.iniciar = async function (opts) {
    G.opts = opts || {}; if (G.activo) G.detener();
    if ((G.opts.fuente === "toque") || !G.micDisponible()) { G.fuente = "toque"; G.activo = true; G.opts.alEncender && G.opts.alEncender("toque"); return "toque"; }
    try {
      ensureCtx();
      const flujo = await mic.flujo(); tieneFlujo = true;
      const src = ctx.createMediaStreamSource(flujo);
      analyser = ctx.createAnalyser(); analyser.fftSize = 8192; analyser.smoothingTimeConstant = 0; src.connect(analyser);
      buf = new Float32Array(analyser.fftSize); prev = null; off = null; tFrame = 0; nAbs = 0; perdidas = 0; mascaras = []; lastCt = ctx.currentTime;
      det = G.crearDetector(ctx.sampleRate); det.sensibilidad(G.sens);
      G.fuente = "mic"; G.activo = true; G.opts.alEncender && G.opts.alEncender("mic");
      timer = setInterval(frame, 12);
      G.calibrar();
      return "mic";
    } catch (e) {
      G.fuente = "toque"; G.activo = true; if (tieneFlujo) { tieneFlujo = false; mic.soltar(); }
      G.opts.alError && G.opts.alError(e); G.opts.alEncender && G.opts.alEncender("toque"); return "toque";
    }
  };
  G.detener = function () {
    const estaba = G.activo; G.activo = false; G.fuente = null; clearInterval(timer); timer = null;
    if (analyser) { try { analyser.disconnect(); } catch (e) {} analyser = null; }
    if (tieneFlujo) { tieneFlujo = false; mic.soltar(); }
    det = null; if (calRes) { calRes(null); calRes = null; calProm = null; }
    if (estaba) G.opts.alApagar && G.opts.alApagar();
  };
  /* calibración del ruido de fondo (por defecto 3 s). Devuelve una promesa con { piso, umbral, … } o null si no hay micrófono. */
  G.calibrar = function (ms) {
    if (G.fuente !== "mic" || !det) return Promise.resolve(null);
    if (calProm) return calProm;
    calProm = new Promise(res => { calRes = res; });
    det.calibrar(ms || G.PARAMS.calibracionMs);
    det.alCalibrado = info => { const r = calRes; calRes = null; calProm = null; G.opts.alCalibrado && G.opts.alCalibrado(info); r && r(info); };
    G.opts.alCalibrando && G.opts.alCalibrando(0);
    return calProm;
  };
  /* alinea el buffer nuevo del analizador con el anterior: cuántas muestras son realmente nuevas (exacto: las muestras viejas
     reaparecen idénticas, desplazadas) */
  function nuevas() {
    const N = buf.length;
    if (!prev) { prev = new Float32Array(N); prev.set(buf); lastCt = ctx.currentTime; return Math.min(N, Math.round(ctx.sampleRate * 0.02)); }
    const est = Math.round((ctx.currentTime - lastCt) * ctx.sampleRate); let n = -1;
    if (est >= N - 8) { G.huecos++; n = N; perdidas = Math.max(0, est - N); }   // el aparato se atrasó más que el buffer: se cuentan las muestras perdidas para no correr los tiempos
    else {
      for (let d = 0; d <= 400 && n < 0; d++) {
        for (const c of d ? [est + d, est - d] : [est]) {
          if (c < 0 || c > N - 8) continue;
          const M = Math.min(96, N - c); let ok = true;
          for (let j = 0; j < M; j++) if (buf[j] !== prev[j + c]) { ok = false; break; }
          if (ok) { n = c; break; }
        }
      }
      if (n < 0) n = clamp(est, 0, N);
    }
    prev.set(buf); lastCt = ctx.currentTime; return n;
  }
  function frame() {
    if (!analyser || !det) return;
    analyser.getFloatTimeDomainData(buf);
    const ahora = performance.now(), n = nuevas();
    if (G.opts.nivel) { let s = 0; for (let i = buf.length - 1024; i < buf.length; i++) s += buf[i] * buf[i]; G.opts.nivel(Math.sqrt(s / 1024)); }
    if (n <= 0) return;
    nAbs += n + perdidas; perdidas = 0; const tMuestras = nAbs * 1000 / ctx.sampleRate, d = ahora - tMuestras;
    /* reloj de audio -> performance.now(): manda la muestra "más cercana" (la menos demorada), pero la corrección hacia abajo se limita a
       4 ms por segundo: así un bache de carga del teléfono al arrancar no deforma los intervalos entre golpes cuando después se corrige */
    if (off === null) off = d; else if (d < off) off = Math.max(d, off - 0.004 * Math.max(0, ahora - tFrame)); else off += (d - off) * 0.0002;
    tFrame = ahora;
    const cal0 = !!det.cal;
    const evs = det.feed(buf.subarray(buf.length - n), off + tMuestras, silenciado);
    if (cal0 && det.cal && G.opts.alCalibrando) G.opts.alCalibrando(Math.min(1, det.cal.util / det.cal.ms));
    evs.forEach(e => { if (silenciado(e.t)) return; Gioval.entrada.emitir({ tipo: "golpe", t: e.t, fuerza: e.fuerza, fuente: "mic" }); G.opts.alGolpe && G.opts.alGolpe(e); });
  }

  /* ============ FALLBACK POR TOQUE ============ */
  G.pulsar = function (datos) {
    const d = datos || {};
    Gioval.entrada.emitir({ tipo: "golpe", t: d.t != null ? d.t : performance.now(), fuerza: d.fuerza != null ? d.fuerza : 1, fuente: "toque" });
  };
  return G;
})());
