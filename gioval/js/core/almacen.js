"use strict";
/* ============ ALMACÉN DE DATOS ============
   `store` vive en memoria con el MISMO formato de siempre (profiles, stars, sk, days, time, log, checks, extra, limit)
   para que el resto del código no cambie. Se persiste en dos lugares:
     - IndexedDB "gioval-db": store "estado" (el JSON completo), "fotos" (Blob, para el futuro álbum),
       "respaldo" (copias de seguridad automáticas: antes de migrar y antes de restaurar).
     - localStorage clave "gioval": espejo en JSON (respaldo de emergencia y compatibilidad con versiones viejas).
   Al arrancar se usa la copia más reciente (meta.guardado). Las migraciones están numeradas: v0 = formato
   antiguo de localStorage (sin campo version). NUNCA se borra nada si una migración falla: se guarda copia
   previa y se sigue con los datos originales. */
const ALMACEN_VERSION = 1;
const store = { version: ALMACEN_VERSION, profiles: [], stars: {}, sk: {}, days: {}, time: {}, log: {}, checks: {}, extra: {}, limit: {}, meta: { ultimoRespaldo: 0, guardado: 0, desde: 0 } };

Gioval.almacen = (function () {
  const DB = "gioval-db", DB_V = 1, LS = "gioval", LS_PRE = "gioval_pre_migracion";
  const A = { listo: null, persistente: null, errorMigracion: null, idbOk: false, versionFutura: false, VERSION: ALMACEN_VERSION };
  let db = null, tmr = null, escribiendo = Promise.resolve();
  const esObj = x => x && typeof x === "object" && !Array.isArray(x);
  const obj = x => esObj(x) ? x : {};

  /* ---- migraciones numeradas: cada una lleva el formato (n-1) al formato n ---- */
  const MIGRACIONES = [
    { a: 1, nombre: "v0 → v1: formato de localStorage antiguo → campos normalizados + version + meta",
      fn(s) {
        s.profiles = Array.isArray(s.profiles) ? s.profiles.filter(x => typeof x === "string") : [];
        ["stars", "sk", "days", "time", "log", "checks", "extra", "limit"].forEach(k => { s[k] = obj(s[k]); });
        s.meta = Object.assign({ ultimoRespaldo: 0, guardado: 0, desde: 0 }, obj(s.meta));
        /* los chequeos viejos (antes de existir varias islas) eran todos de música */
        Object.keys(s.checks).forEach(k => { if (Array.isArray(s.checks[k])) s.checks[k].forEach(c => { if (c && !c.p) c.p = "musica"; }); });
        return s;
      } },
    /* v2 (Fase 1, ejemplo): { a: 2, nombre:"…", fn(s){ s.intake = obj(s.intake); return s; } } */
  ];
  A.migraciones = MIGRACIONES;
  function migrar(s) {
    let v = Number.isInteger(s.version) ? s.version : 0;
    if (v > ALMACEN_VERSION) { A.versionFutura = true; return s; }
    for (const m of MIGRACIONES) { if (m.a > v) { if (window.__GIOVAL_FALLAR_MIGRACION) throw new Error("migración forzada a fallar (prueba)"); s = m.fn(s); v = m.a; s.version = v; } }
    return s;
  }

  /* ---- IndexedDB ---- */
  function abrir() {
    return new Promise(res => {
      if (!window.indexedDB) return res(null);
      let rq; try { rq = indexedDB.open(DB, DB_V); } catch (e) { return res(null); }
      rq.onupgradeneeded = () => { const d = rq.result; ["estado", "fotos", "respaldo"].forEach(n => { if (!d.objectStoreNames.contains(n)) d.createObjectStore(n, { keyPath: "id" }); }); };
      rq.onsuccess = () => res(rq.result); rq.onerror = () => res(null); rq.onblocked = () => res(null);
    });
  }
  function tx(nombre, modo, fn) {
    return new Promise((res, rej) => {
      if (!db) return res(null);
      try { const t = db.transaction(nombre, modo), st = t.objectStore(nombre), r = fn(st); t.oncomplete = () => res(r && "result" in r ? r.result : null); t.onerror = t.onabort = () => rej(t.error); } catch (e) { rej(e); }
    });
  }
  const idbGet = (n, k) => tx(n, "readonly", st => st.get(k)).catch(() => null);
  const idbPut = (n, v) => tx(n, "readwrite", st => st.put(v)).catch(() => null);
  const idbAll = n => tx(n, "readonly", st => st.getAll()).catch(() => []);
  const idbDel = (n, k) => tx(n, "readwrite", st => st.delete(k)).catch(() => null);

  /* ---- carga ---- */
  function parse(txt) { try { const o = JSON.parse(txt); return esObj(o) ? o : null; } catch (e) { return null; } }
  function reemplazar(o) { Object.keys(store).forEach(k => delete store[k]); Object.assign(store, o); }
  A.cargar = function () {
    return A.listo = (async () => {
      const rawLS = (() => { try { return localStorage.getItem(LS); } catch (e) { return null; } })();
      const dLS = rawLS ? parse(rawLS) : null;
      db = await abrir(); A.idbOk = !!db;
      const rec = db ? await idbGet("estado", "store") : null;
      const dIDB = rec && rec.json ? parse(rec.json) : null;
      const ts = d => d ? ((d.meta && +d.meta.guardado) || 0) : -1;
      let elegido = ts(dIDB) > ts(dLS) ? dIDB : (dLS || dIDB);
      let origenTxt = elegido === dIDB && dIDB ? rec.json : rawLS;
      if (!elegido) { reemplazar(JSON.parse(JSON.stringify(store))); await escribirAhora(); return; }
      let hechoMigracion = false;
      const versionAntes = Number.isInteger(elegido.version) ? elegido.version : 0;
      if (versionAntes < ALMACEN_VERSION) {
        /* copia previa ANTES de tocar nada */
        try { localStorage.getItem(LS_PRE) || localStorage.setItem(LS_PRE, origenTxt); } catch (e) {}
        await idbPut("respaldo", { id: "pre-migracion-v" + versionAntes + "-" + Date.now(), motivo: "antes de migrar de v" + versionAntes, ts: Date.now(), json: origenTxt });
        try { elegido = migrar(JSON.parse(origenTxt)); hechoMigracion = true; }
        catch (e) { A.errorMigracion = String(e && e.message || e); elegido = Object.assign({ profiles: [], stars: {}, sk: {}, days: {}, time: {}, log: {}, checks: {}, extra: {}, limit: {} }, JSON.parse(origenTxt)); }
      } else { elegido = migrar(elegido); }
      const base = JSON.parse(JSON.stringify(store)); /* defaults */
      reemplazar(Object.assign(base, elegido));
      if (!A.errorMigracion) {
        store.meta = Object.assign({ ultimoRespaldo: 0, guardado: 0, desde: 0 }, obj(store.meta));
        if (hayProgreso() && !store.meta.desde) { store.meta.desde = Date.now(); hechoMigracion = true; } /* desde cuándo hay progreso: base del recordatorio de respaldo */
        if (hechoMigracion) await escribirAhora();
      }
      else await escribirAhora();
    })();
  };

  /* ---- guardado ---- */
  function hayProgreso() { return Object.keys(store.sk).length > 0 || Object.keys(store.days).some(k => (store.days[k] || []).length); }
  function espejo() { try { localStorage.setItem(LS, JSON.stringify(store)); } catch (e) {} }
  async function escribirAhora() {
    espejo();
    if (db) await idbPut("estado", { id: "store", json: JSON.stringify(store), t: Date.now() });
  }
  A.guardarYa = function () { clearTimeout(tmr); tmr = null; store.meta.guardado = Date.now(); if (hayProgreso() && !store.meta.desde) store.meta.desde = Date.now(); escribiendo = escribiendo.then(() => escribirAhora()); return escribiendo; };
  window.save = function save() {
    store.meta.guardado = Date.now(); if (hayProgreso() && !store.meta.desde) store.meta.desde = Date.now();
    espejo(); /* espejo inmediato y síncrono */
    clearTimeout(tmr); tmr = setTimeout(() => { escribiendo = escribiendo.then(() => escribirAhora()); }, 400);
  };
  document.addEventListener("visibilitychange", () => { if (document.hidden && tmr) A.guardarYa(); });
  window.addEventListener("pagehide", () => { if (tmr) A.guardarYa(); });

  /* ---- persistencia protegida: se pide tras el primer toque ---- */
  A.pedirPersistencia = function () {
    if (!(navigator.storage && navigator.storage.persist)) return Promise.resolve(false);
    return navigator.storage.persist().then(ok => (A.persistente = ok), () => (A.persistente = false));
  };
  document.addEventListener("pointerdown", () => { A.pedirPersistencia(); }, { once: true, capture: true });

  /* ---- exportar / restaurar ---- */
  A.exportar = function () {
    const d = { app: "gioval", formato: 1, version: store.version, exportado: new Date().toISOString(), store };
    const txt = JSON.stringify(d, null, 1), nombre = "gioval-respaldo-" + today() + ".json";
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([txt], { type: "application/json" })); a.download = nombre;
    document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
    store.meta.ultimoRespaldo = Date.now(); window.save(); A.guardarYa();
    return nombre;
  };
  /* lee un archivo de respaldo, lo valida y devuelve { ok, error, datos, resumen } sin tocar nada */
  A.leerRespaldo = async function (file) {
    let o; try { o = JSON.parse(await file.text()); } catch (e) { return { ok: false, error: "El archivo no es un respaldo válido (no se pudo leer)." }; }
    if (!esObj(o) || o.app !== "gioval" || !esObj(o.store) || !Array.isArray(o.store.profiles)) return { ok: false, error: "Ese archivo no es un respaldo de Mundo Gioval." };
    const v = Number.isInteger(o.store.version) ? o.store.version : 0;
    if (v > ALMACEN_VERSION) return { ok: false, error: "Ese respaldo es de una versión más nueva de la app. Actualizá la app y probá de nuevo." };
    let s; try { s = migrar(JSON.parse(JSON.stringify(o.store))); } catch (e) { return { ok: false, error: "No se pudo convertir el respaldo viejo: " + e.message }; }
    const resumen = {
      exportado: o.exportado || "", perfiles: s.profiles.slice(),
      dias: Object.fromEntries(s.profiles.map(p => [p, (s.days[p] || []).length])),
      dominadas: Object.fromEntries(s.profiles.map(p => [p, Object.entries(s.sk).filter(([k, x]) => k.startsWith(p + "|") && x && x.mast).length])),
    };
    return { ok: true, datos: s, resumen };
  };
  A.restaurar = async function (datos) {
    await idbPut("respaldo", { id: "pre-restauracion-" + Date.now(), motivo: "antes de restaurar un respaldo", ts: Date.now(), json: JSON.stringify(store) });
    const base = { version: ALMACEN_VERSION, profiles: [], stars: {}, sk: {}, days: {}, time: {}, log: {}, checks: {}, extra: {}, limit: {}, meta: { ultimoRespaldo: 0, guardado: 0, desde: 0 } };
    reemplazar(Object.assign(base, datos)); store.meta = Object.assign(base.meta, obj(store.meta));
    store.meta.guardado = Date.now(); await A.guardarYa(); return true;
  };
  A.ultimoRespaldo = () => store.meta.ultimoRespaldo || 0;
  A.debeRecordar = function () {
    if (!hayProgreso()) return false;
    const base = store.meta.ultimoRespaldo || store.meta.desde || Date.now();
    return Date.now() - base > 14 * DAY;
  };
  A.respaldos = () => idbAll("respaldo");

  /* ---- fotos (Blob) para el futuro álbum ---- */
  A.fotos = {
    guardar: async (blob, meta) => { const id = "f" + Date.now() + "-" + Math.floor(Math.random() * 1e6); await idbPut("fotos", { id, blob, meta: meta || {}, ts: Date.now() }); return id; },
    obtener: id => idbGet("fotos", id),
    listar: async () => (await idbAll("fotos")).map(f => ({ id: f.id, meta: f.meta, ts: f.ts })),
    borrar: id => idbDel("fotos", id),
  };
  return A;
})();
