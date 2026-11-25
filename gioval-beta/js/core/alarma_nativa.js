"use strict";
/* ============ ALARMA NATIVA (puente con el envoltorio Android) ============
   alarma.js NO se toca y sigue siendo la alarma de la app (la que ve y usa el resto del código). Este archivo solo se activa
   si la app corre dentro del envoltorio Android (Capacitor) y ese envoltorio trae el plugin propio "GiovalAlarma"
   (gioval-android/android/.../GiovalAlarmaPlugin.java). En un navegador o en la PWA no hace NADA: ni siquiera cambia una función.

   Cuando está activo:
   - Alarma.programar(...) además programa una alarma EXACTA del sistema (AlarmManager) que suena con la pantalla apagada y la app
     cerrada (servicio en primer plano + tono de alarma + pantalla sobre el bloqueo). Alarma.cancelar() la cancela.
     Si la app está a la vista cuando llega la hora, la alarma nativa se calla y suena la web (no se duplican).
   - Alarma.pedirPermiso() pide el permiso de avisos de Android (13+) y window.Notification pasa a reflejar ese permiso.
   - La pantalla se mantiene encendida mientras se juega una actividad o corre una alarma.
   - El panel de adultos suma una sección "Alarma del teléfono" (permisos, batería, probar).
   Gioval.alarmaNativa = { activa, estado, refrescar, probar }.  activa=false fuera del envoltorio. Ver docs/ANDROID.md. */
(function () {
  const G = Gioval, NID = 7001;   /* mismo número de alarma que usa alarma.js para su notificación */
  const N = G.alarmaNativa = { activa: false, estado: null, permiso: "default", refrescar: async () => null, probar: () => 0 };
  const plug = () => { try { return window.Capacitor && Capacitor.Plugins && Capacitor.Plugins.GiovalAlarma || null; } catch (e) { return null; } };
  const P = plug();
  if (!P || !G.alarma) return;   /* navegador / PWA: no cambia nada */
  const A = G.alarma;
  N.activa = true;

  /* ---------- textos (es-AR es el idioma base; en el resto cae a es-AR) ---------- */
  G.i18n.agregar("es-AR", {
    "nativa.panel.titulo": "⏰ Alarma del teléfono (app Android)",
    "nativa.panel.detalle": "Esta app instalada hace sonar la alarma aunque la pantalla esté apagada. Para que no falle, revisá esto:",
    "nativa.panel.avisos_si": "✅ Avisos permitidos.",
    "nativa.panel.avisos_no": "⚠️ Avisos NO permitidos: la alarma puede sonar sin mostrar nada en pantalla.",
    "nativa.panel.exacta_si": "✅ Alarmas exactas permitidas (suena a la hora justa).",
    "nativa.panel.exacta_no": "⚠️ Alarmas exactas NO permitidas: puede atrasarse unos minutos.",
    "nativa.panel.pantalla_no": "⚠️ No puede aparecer sobre la pantalla bloqueada (solo sonará y mostrará el aviso).",
    "nativa.panel.bateria_si": "✅ Sin restricción de batería.",
    "nativa.panel.bateria_no": "⚠️ El ahorro de batería puede dormir la app. En algunas marcas (Xiaomi, Samsung, Huawei, Motorola…) conviene quitarle la restricción.",
    "nativa.panel.permitir": "Permitir",
    "nativa.panel.ajustar": "Abrir ajustes",
    "nativa.panel.probar": "🔔 Probar alarma (10 segundos)",
    "nativa.panel.probar_ayuda": "Tocá Probar, bloqueá el teléfono y esperá: tiene que sonar y encender la pantalla.",
    "nativa.panel.prueba_titulo": "Prueba de alarma",
    "nativa.panel.prueba_texto": "¡Funciona! Así va a sonar cuando se termine el tiempo.",
  });
  G.i18n.agregar("en", {
    "nativa.panel.titulo": "⏰ Phone alarm (Android app)",
    "nativa.panel.detalle": "This installed app rings the alarm even with the screen off. To make sure it works, check this:",
    "nativa.panel.avisos_si": "✅ Notifications allowed.",
    "nativa.panel.avisos_no": "⚠️ Notifications NOT allowed: the alarm may ring without showing anything on screen.",
    "nativa.panel.exacta_si": "✅ Exact alarms allowed (rings at the exact time).",
    "nativa.panel.exacta_no": "⚠️ Exact alarms NOT allowed: it may be a few minutes late.",
    "nativa.panel.pantalla_no": "⚠️ It cannot appear over the lock screen (it will only ring and show the notification).",
    "nativa.panel.bateria_si": "✅ No battery restriction.",
    "nativa.panel.bateria_no": "⚠️ Battery saving may put the app to sleep. On some brands (Xiaomi, Samsung, Huawei, Motorola…) it is best to remove the restriction.",
    "nativa.panel.permitir": "Allow",
    "nativa.panel.ajustar": "Open settings",
    "nativa.panel.probar": "🔔 Test the alarm (10 seconds)",
    "nativa.panel.probar_ayuda": "Tap Test, lock the phone and wait: it should ring and turn the screen on.",
    "nativa.panel.prueba_titulo": "Alarm test",
    "nativa.panel.prueba_texto": "It works! This is how it will sound when time is up.",
  });

  /* ---------- estado y permisos ---------- */
  const aPermiso = s => s === "granted" ? "granted" : s === "denied" ? "denied" : "default";
  async function refrescar() {
    try { N.estado = await P.estado(); N.permiso = aPermiso(N.estado.permisoNotificaciones); } catch (e) {}
    pintar(); return N.estado;
  }
  N.refrescar = refrescar;

  /* ---------- Alarma.programar / cancelar / pedirPermiso: se suma lo nativo, lo web queda igual ---------- */
  const orig = { programar: A.programar, cancelar: A.cancelar, pedirPermiso: A.pedirPermiso };
  A.programar = function (seg, o) {
    const fin = orig.programar.call(A, seg, o); o = o || {};
    try { Promise.resolve(P.programar({ id: NID, fin: Math.round(fin), titulo: o.titulo || "Mundo Gioval", texto: o.texto || "" })).then(r => { if (N.estado && r) N.estado.exacta = !!r.exacta; }, () => {}); } catch (e) {}
    pantalla(); return fin;
  };
  A.cancelar = function () {
    orig.cancelar.call(A);
    try { Promise.resolve(P.cancelar({ id: NID })).catch(() => {}); } catch (e) {}
    pantalla();
  };
  A.pedirPermiso = function () {
    return Promise.resolve(P.pedirNotificaciones()).then(r => { if (r) { N.estado = r; N.permiso = aPermiso(r.permisoNotificaciones); } pintar(); return N.permiso; }, () => N.permiso);
  };

  /* window.Notification refleja el permiso nativo (el panel de Ayudantes y alarma.js lo leen). La notificación en sí la hace el sistema. */
  const Notif = function () {};
  Object.defineProperty(Notif, "permission", { get: () => N.permiso });
  Notif.requestPermission = () => A.pedirPermiso();
  try { window.Notification = Notif; } catch (e) {}

  /* ---------- pantalla encendida mientras se juega o corre una alarma ---------- */
  let encendida = null;
  function pantalla() {
    const act = !!document.querySelector(".screen.juego.active") || A.activa();
    if (act === encendida) return; encendida = act;
    try { Promise.resolve(P.mantenerPantalla({ activo: act })).catch(() => {}); } catch (e) {}
  }
  try { new MutationObserver(pantalla).observe(document.getElementById("app"), { subtree: true, attributes: true, attributeFilter: ["class"] }); } catch (e) {}
  setInterval(pantalla, 2000);   /* cubre el momento en que la alarma vence */
  document.addEventListener("visibilitychange", () => { if (!document.hidden) { encendida = null; pantalla(); refrescar(); } });

  /* ---------- sección del panel de adultos ---------- */
  const pie = document.getElementById("panelPie");
  let caja = null;
  if (pie) { pie.insertAdjacentHTML("beforeend", '<div class="psum" id="nativaPanel"></div>'); caja = document.getElementById("nativaPanel"); }
  function pintar() {
    if (!caja) return; const e = N.estado || {};
    const fila = (ok, si, no, tipo, boton) => `<li>${ok ? t(si) : t(no)}${ok ? "" : ` <button class="btn alt" data-nativa="${tipo}" style="padding:3px 10px;font-size:15px">${t(boton)}</button>`}</li>`;
    caja.innerHTML = `<b>${t("nativa.panel.titulo")}</b><div>${t("nativa.panel.detalle")}</div><ul>`
      + fila(e.notificaciones !== false, "nativa.panel.avisos_si", "nativa.panel.avisos_no", "avisos", "nativa.panel.permitir")
      + fila(e.exacta !== false, "nativa.panel.exacta_si", "nativa.panel.exacta_no", "exacta", "nativa.panel.permitir")
      + (e.pantallaCompleta === false ? fila(false, "", "nativa.panel.pantalla_no", "pantallaCompleta", "nativa.panel.ajustar") : "")
      + fila(e.sinRestriccionBateria === true, "nativa.panel.bateria_si", "nativa.panel.bateria_no", "bateria", "nativa.panel.ajustar")
      + `</ul><button class="btn" data-nativa="probar" style="padding:6px 14px;font-size:16px">${t("nativa.panel.probar")}</button><div class="note-hint">${t("nativa.panel.probar_ayuda")}</div>`;
  }
  N.probar = (seg) => A.programar(seg || 10, { titulo: t("nativa.panel.prueba_titulo"), texto: t("nativa.panel.prueba_texto") });
  if (caja) caja.addEventListener("click", ev => {
    const b = ev.target.closest("button"); if (!b || !b.dataset.nativa) return; const k = b.dataset.nativa;
    if (k === "probar") N.probar(10);
    else if (k === "avisos") {
      /* si Android ya no vuelve a preguntar (se negó dos veces), se abren los ajustes de avisos de la app */
      A.pedirPermiso().then(p => { if (p !== "granted") P.abrirAjustes({ tipo: "notificaciones" }); });
    } else P.abrirAjustes({ tipo: k === "exacta" ? "exacta" : k === "pantallaCompleta" ? "pantallaCompleta" : "bateria" });
  });
  G.on("panel", refrescar); G.on("idioma", pintar);
  pintar(); refrescar(); pantalla();
})();
