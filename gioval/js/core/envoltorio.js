"use strict";
/* ============ ENVOLTORIO ANDROID: botón "atrás" y sin service worker ============
   Solo actúa dentro del envoltorio Android (Capacitor con su plugin "App" o el plugin "GiovalAlarma"). En un navegador no hace nada.
   1) Sin service worker: en la app Android todos los archivos ya viajan dentro del APK (funciona sin conexión y se actualiza
      instalando un APK nuevo), así que el service worker solo sumaría una capa de caché que complica las actualizaciones.
      Se quita antes de que la app lo registre (ui.js lo registra solo si "serviceWorker" existe en navigator).
   2) Botón "atrás". Sin esto el botón del teléfono no haría nada (la app no usa el historial del navegador).
   Comportamiento del "atrás": cierra lo que esté abierto de arriba hacia abajo (cartel, panel de adultos), después usa el botón
   "⬅ Volver" de la pantalla actual y, en la pantalla de inicio, manda la app a segundo plano (no la cierra: así una
   alarma en curso no se pierde). */
(function () {
  const plug = n => { try { return window.Capacitor && Capacitor.Plugins && Capacitor.Plugins[n] || null; } catch (e) { return null; } };
  const App = plug("App");
  Gioval.envoltorio = { activo: !!((App && App.addListener) || plug("GiovalAlarma")), atras: null };
  if (!Gioval.envoltorio.activo) return;
  try { delete Navigator.prototype.serviceWorker; } catch (e) {}
  if (!(App && App.addListener)) return;
  const clic = el => { if (el) el.click(); return !!el; };
  /* botones que cierran cada cartel (si el cartel no tiene salida, el "atrás" no hace nada para no dejarlo a medias) */
  const SALIDAS = { gateBox: "gateNo", reportBox: "repClose", restoreBox: "restoreNo", vozBox: "vozCerrar", capBox: "capOk", finish: "btnFinHome" };
  function atras() {
    const carteles = [...document.querySelectorAll(".big.show")];
    if (carteles.length) { const c = carteles[carteles.length - 1]; return clic(document.getElementById(SALIDAS[c.id])), "cartel"; }
    const panel = document.getElementById("panel");
    if (panel && panel.classList.contains("show")) { panel.classList.remove("show"); return "panel"; }
    const pant = document.querySelector(".screen.active"); if (!pant) return "nada";
    if (pant.id === "map") return clic(document.getElementById("btnWho")), "mapa";
    const volver = pant.querySelector(".bar .btn .arr");
    if (volver) return clic(volver.closest("button")), "volver";
    return "minimizar";
  }
  Gioval.envoltorio.atras = atras;
  App.addListener("backButton", () => { const r = atras(); if (r === "minimizar" || r === "nada") { try { App.minimizeApp(); } catch (e) {} } });
})();
