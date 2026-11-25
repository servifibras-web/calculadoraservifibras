"use strict";
/* ============ SONIDO (salida) ============
   Los instrumentos son "voces de sonido" intercambiables. Hoy hay uno: "piano" (el piano de juguete hecho con
   osciladores, igual que siempre). Más adelante se registran instrumentos con muestras livianas (guitarra, batería…).
     Gioval.sonido.registrarInstrumento(id, { nombre, tocar(midi, dur, vol, ctx), muestras?:{ "60":"audio/inst/guitarra/c4.mp3", … } })
     Gioval.sonido.usar(id)                  instrumento activo
     Gioval.sonido.tocar(midi, dur, vol, id) suena una nota (id opcional)
     Gioval.sonido.cargarMuestras(id)        baja y decodifica las muestras SOLO cuando se necesitan (por demanda)
   Un instrumento con "muestras" suena con la muestra más cercana, ajustando la velocidad de reproducción.
   Ver docs/ENTRADAS_Y_SONIDO.md. */
Gioval.sonido = (function () {
  const S_ = { instrumentos: {}, activo: "piano", _buffers: {} };
  S_.registrarInstrumento = (id, def) => { S_.instrumentos[id] = Object.assign({ id, nombre: id }, def); return S_.instrumentos[id]; };
  S_.usar = id => { if (S_.instrumentos[id]) S_.activo = id; return S_.activo; };
  S_.cargarMuestras = async function (id) {
    const ins = S_.instrumentos[id]; if (!ins || !ins.muestras) return false;
    const c = ensureCtx(), bufs = S_._buffers[id] = S_._buffers[id] || {};
    await Promise.all(Object.entries(ins.muestras).map(async ([midi, url]) => {
      if (bufs[midi]) return;
      if (url && url.constructor && url.constructor.name === "AudioBuffer") { bufs[midi] = url; return; }
      const r = await fetch(url); bufs[midi] = await c.decodeAudioData(await r.arrayBuffer());
    }));
    return true;
  };
  function conMuestras(ins, midi, dur, vol) {
    const bufs = S_._buffers[ins.id]; if (!bufs) return false;
    const claves = Object.keys(bufs).map(Number); if (!claves.length) return false;
    const base = claves.reduce((a, b) => Math.abs(b - midi) < Math.abs(a - midi) ? b : a);
    const c = ensureCtx(), src = c.createBufferSource(), g = c.createGain();
    src.buffer = bufs[base]; src.playbackRate.value = Math.pow(2, (midi - base) / 12); g.gain.value = vol;
    src.connect(g); g.connect(c.destination); src.start(); src.stop(c.currentTime + Math.max(.3, dur) + .2);
    return true;
  }
  S_.tocar = function (midi, dur = .5, vol = .35, id) {
    const ins = S_.instrumentos[id || S_.activo] || S_.instrumentos.piano;
    if (ins.muestras && conMuestras(ins, midi, dur, vol)) return;
    (ins.tocar || S_.instrumentos.piano.tocar)(midi, dur, vol, ensureCtx());
  };
  /* piano de juguete: osciladores (idéntico al sonido de siempre) */
  S_.registrarInstrumento("piano", {
    nombre: "Piano de juguete",
    tocar(midi, dur, vol, c) {
      const f = 440 * Math.pow(2, (midi - 69) / 12); const t = c.currentTime;
      const g = c.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + .01);
      g.gain.exponentialRampToValueAtTime(.001, t + Math.max(.25, dur)); g.connect(c.destination);
      [[1, "triangle", 1], [2, "sine", .3], [3, "sine", .1]].forEach(([m, type, a]) => {
        const o = c.createOscillator(); o.type = type; o.frequency.value = f * m;
        const gg = c.createGain(); gg.gain.value = a; o.connect(gg); gg.connect(g); o.start(t); o.stop(t + Math.max(.3, dur) + .05);
      });
    },
  });
  return S_;
})();
/* atajo histórico: tone(midi, dur, vol) suena con el instrumento activo */
function tone(midi, dur = .5, vol = .35) { Gioval.sonido.tocar(midi, dur, vol); }
