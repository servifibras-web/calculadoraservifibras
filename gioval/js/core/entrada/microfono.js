"use strict";
/* Proveedor "microfono": detecta UNA nota por vez (YIN) y emite { tipo:"nota", midi, t, fuerza }.
   El algoritmo, los umbrales y los tiempos son los mismos de siempre (no cambiar sin probar con el piano real).
   La isla que lo usa pasa opciones a iniciar(opts):
     umbral()            -> sensibilidad (RMS mínimo, 0.001–0.03)
     nivel(rms)          -> para mostrar el volumen en el panel (opcional)
     alDetectar(midi)    -> para mostrar la nota detectada (opcional)
     alEncender()/alApagar()/alError(e) -> avisos a la interfaz (opcional) */
Gioval.entrada.registrarProveedor((function () {
  const M = { id: "microfono", tipos: ["nota"], activo: false, opts: {}, yin: null, freqToMidi: null };
  let analyser = null, micStream = null, timer = null, slow = 0, pending = false, votes = [], pendStart = 0, lastOnset = 0, onsetRms = 0;
  M.disponible = () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  M.iniciar = async function (opts) {
    M.opts = opts || {};
    try {
      ensureCtx();
      micStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      const src = ctx.createMediaStreamSource(micStream);
      analyser = ctx.createAnalyser(); analyser.fftSize = 4096; analyser.smoothingTimeConstant = 0;
      src.connect(analyser);
      M.activo = true; M.opts.alEncender && M.opts.alEncender();
      timer = setInterval(frame, 30);
    } catch (e) {
      M.activo = false; M.opts.alError && M.opts.alError(e);
    }
  };
  M.detener = function () {
    M.activo = false; clearInterval(timer); M.opts.alApagar && M.opts.alApagar();
    if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  };
  // YIN: detecta la frecuencia fundamental de una nota suelta
  function yin(buf, sr) {
    const W = 1024, maxTau = Math.floor(sr / 170), minTau = Math.floor(sr / 1200);
    const start = buf.length - W - maxTau - 2; if (start < 0) return null;
    const d = new Float32Array(maxTau + 1);
    for (let tau = 1; tau <= maxTau; tau++) { let s = 0; for (let i = 0; i < W; i++) { const x = buf[start + i] - buf[start + i + tau]; s += x * x; } d[tau] = s; }
    const c = new Float32Array(maxTau + 1); c[0] = 1; let run = 0;
    for (let tau = 1; tau <= maxTau; tau++) { run += d[tau]; c[tau] = d[tau] * tau / (run || 1); }
    let tau = -1;
    for (let t = minTau; t < maxTau; t++) { if (c[t] < .15) { while (t + 1 < maxTau && c[t + 1] < c[t]) t++; tau = t; break; } }
    if (tau < 0) return null;
    const a = c[tau - 1] || c[tau], b = c[tau], g = c[tau + 1] || c[tau];
    const den = 2 * (2 * b - a - g); const shift = den ? (a - g) / den : 0;
    return sr / (tau + shift);
  }
  function freqToMidi(f) { return Math.round(69 + 12 * Math.log2(f / 440)); }
  M.yin = yin; M.freqToMidi = freqToMidi;
  function frame() {
    if (!analyser) return;
    const buf = new Float32Array(analyser.fftSize); analyser.getFloatTimeDomainData(buf);
    let s = 0; for (let i = buf.length - 1024; i < buf.length; i++) s += buf[i] * buf[i]; const rms = Math.sqrt(s / 1024);
    M.opts.nivel && M.opts.nivel(rms);
    const now = performance.now();
    if (now < muteUntil) { slow = rms; pending = false; return; }
    const thr = M.opts.umbral ? M.opts.umbral() : .008; // 0.001 – 0.03
    if (!pending && rms > thr && rms > slow * 1.4 && now - lastOnset > 140) { pending = true; votes = []; pendStart = now; lastOnset = now; onsetRms = rms; }
    if (pending) {
      if (now - pendStart > 70) { const f = yin(buf, ctx.sampleRate); if (f) votes.push(freqToMidi(f)); }
      if (votes.length >= 3 || now - pendStart > 380) {
        pending = false;
        if (votes.length >= 2) {
          const cnt = {}; votes.forEach(v => cnt[v] = (cnt[v] || 0) + 1);
          const best = +Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0];
          M.opts.alDetectar && M.opts.alDetectar(best);
          Gioval.entrada.emitir({ tipo: "nota", midi: best, fuerza: Math.min(1, onsetRms * 8) });
        }
      }
    }
    slow = slow * .85 + rms * .15;
  }
  return M;
})());
