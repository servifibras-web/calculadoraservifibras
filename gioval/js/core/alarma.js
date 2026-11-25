"use strict";
/* ============ ALARMA ============
   Interfaz única (la app no debe usar temporizadores sueltos):
     Alarma.programar(segundos, { titulo, texto })   -> programa (reemplaza la anterior)
     Alarma.cancelar()
     Alarma.restante()                                -> segundos que faltan (0 si no hay alarma)
     Alarma.onFin(cb)                                 -> avisa cuando vence; devuelve una función para desuscribirse
     Alarma.pedirPermiso()                            -> pide permiso de notificaciones (llamar desde un toque)
   Implementación WEB: se guarda la hora ABSOLUTA de fin (Date.now() + duración). Nunca se cuenta con un
   contador que se pierda si la pantalla se apaga: cada vez que la página vuelve a primer plano
   (visibilitychange / pageshow / focus) se recalcula y, si ya venció, se dispara. Mientras corre se pide un
   Screen Wake Lock (opcional) para que la pantalla no se apague sola. Al vencer: sonido (Web Audio),
   vibración y, si hay permiso, notificación vía service worker. La alarma se guarda en localStorage
   ("gioval_alarma") para sobrevivir a un reinicio de la página.
   Implementación NATIVA: si existe window.Capacitor con el plugin LocalNotifications, además se programa una
   notificación local exacta (sirve con la pantalla apagada). El código está listo pero la app NO depende de él.
   LIMITACIÓN HONESTA: en la web instalada (PWA) la alarma con la pantalla apagada o la app cerrada NO está
   garantizada: el navegador congela la página y no hay forma confiable de despertarla. Eso se resuelve con el
   envoltorio nativo (Android primero; aparato todavía por confirmar). Ver docs/ALARMA.md. */
Gioval.alarma = (function () {
  const KEY = Gioval.clave("gioval_alarma"), NID = 7001;
  const A = { fin: 0, titulo: "", texto: "", cbs: [], tick: null, wake: null, disparada: false, perdida: null };
  const nativa = () => { try { return window.Capacitor && Capacitor.Plugins && Capacitor.Plugins.LocalNotifications || null; } catch (e) { return null; } };
  const persist = () => { try { A.fin ? localStorage.setItem(KEY, JSON.stringify({ fin: A.fin, titulo: A.titulo, texto: A.texto })) : localStorage.removeItem(KEY); } catch (e) {} };

  async function tomarWake() {
    try { if (navigator.wakeLock && !document.hidden && A.fin && !A.wake) { A.wake = await navigator.wakeLock.request("screen"); A.wake.addEventListener("release", () => { A.wake = null; }); } } catch (e) { A.wake = null; }
  }
  function soltarWake() { try { A.wake && A.wake.release(); } catch (e) {} A.wake = null; }
  function sonido() {
    try {
      const c = (typeof ensureCtx === "function") ? ensureCtx() : new (window.AudioContext || window.webkitAudioContext)();
      [0, .35, .7, 1.05].forEach(d => { const o = c.createOscillator(), g = c.createGain(), t = c.currentTime + d; o.type = "sine"; o.frequency.value = 880; g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.4, t + .02); g.gain.exponentialRampToValueAtTime(.001, t + .3); o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + .32); });
    } catch (e) {}
  }
  async function notificar(titulo, texto) {
    try {
      if (!("Notification" in window) || Notification.permission !== "granted") return;
      const reg = navigator.serviceWorker && await navigator.serviceWorker.getRegistration();
      if (reg && reg.showNotification) await reg.showNotification(titulo || "Mundo Gioval", { body: texto || "", tag: "gioval-alarma", renotify: true, vibrate: [200, 100, 200] });
      else new Notification(titulo || "Mundo Gioval", { body: texto || "" });
    } catch (e) {}
  }
  function disparar() {
    if (!A.fin || A.disparada) return;
    const info = { titulo: A.titulo, texto: A.texto, fin: A.fin, tarde: Math.max(0, Date.now() - A.fin) };
    A.disparada = true; clearInterval(A.tick); A.tick = null; A.fin = 0; persist(); soltarWake();
    try { navigator.vibrate && navigator.vibrate([200, 100, 200]); } catch (e) {}
    sonido(); notificar(info.titulo, info.texto);
    if (!A.cbs.length) A.perdida = info; /* venció sin nadie escuchando (p. ej. al reabrir la app): se entrega al primer onFin */
    A.cbs.slice().forEach(f => { try { f(info); } catch (e) { console.error(e); } });
  }
  function revisar() { if (A.fin && Date.now() >= A.fin) disparar(); }

  const API = {
    programar(seg, o) {
      o = o || {}; clearInterval(A.tick);
      A.fin = Date.now() + Math.max(0, +seg || 0) * 1000; A.titulo = o.titulo || "Mundo Gioval"; A.texto = o.texto || ""; A.disparada = false;
      persist(); A.tick = setInterval(revisar, 500); tomarWake();
      const n = nativa();
      if (n) { try { n.schedule({ notifications: [{ id: NID, title: A.titulo, body: A.texto, schedule: { at: new Date(A.fin), allowWhileIdle: true } }] }); } catch (e) {} }
      return A.fin;
    },
    cancelar() {
      clearInterval(A.tick); A.tick = null; A.fin = 0; A.disparada = false; persist(); soltarWake();
      const n = nativa(); if (n) { try { n.cancel({ notifications: [{ id: NID }] }); } catch (e) {} }
    },
    restante() { return A.fin ? Math.max(0, Math.ceil((A.fin - Date.now()) / 1000)) : 0; },
    activa() { return !!A.fin; },
    onFin(cb) { A.cbs.push(cb); if (A.perdida) { const i = A.perdida; A.perdida = null; setTimeout(() => cb(i), 0); } return () => { A.cbs = A.cbs.filter(f => f !== cb); }; },
    pedirPermiso() { return ("Notification" in window) ? Notification.requestPermission() : Promise.resolve("denied"); },
    _revisar: revisar,
  };
  /* al volver a primer plano se recalcula con la hora absoluta */
  document.addEventListener("visibilitychange", () => { revisar(); if (!document.hidden) tomarWake(); });
  window.addEventListener("pageshow", revisar); window.addEventListener("focus", revisar);
  /* restaurar una alarma guardada (la página se recargó o el navegador la descartó) */
  try {
    const g = JSON.parse(localStorage.getItem(KEY) || "null");
    if (g && g.fin) { A.fin = g.fin; A.titulo = g.titulo || ""; A.texto = g.texto || ""; A.tick = setInterval(revisar, 500); setTimeout(revisar, 0); }
  } catch (e) {}
  return API;
})();
window.Alarma = Gioval.alarma;
