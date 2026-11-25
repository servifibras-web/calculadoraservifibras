"use strict";
/* ============ i18n: textos por idioma (solo la maquinaria; los textos viven en js/i18n/<código>.js) ============
   Reglas de la casa:
   - Los textos son FRASES COMPLETAS con huecos con nombre ({nombre}). Nunca se arma una frase pegando pedazos:
     el orden de las palabras, el género y los plurales cambian de un idioma a otro.
   - Formato de cada texto (subconjunto de ICU MessageFormat):
       {nombre}                                  -> valor
       {g, select, f{una} other{un}}             -> elige según el valor (género, tipo...). "other" es obligatorio.
       {n, plural, =0{ninguno} one{# gato} other{# gatos}}   -> plural según el idioma ("#" = el número)
     Se pueden anidar.
   - Un texto puede ser una LISTA de variantes (para elegir una al azar con rnd(tl(clave))).
   - Un texto puede ser un OBJETO de datos (sustantivos con género y formas de plural): dato(clave).
   - Cadena de respaldo: idioma pedido -> sus "fallback" -> es-AR -> en. Si una clave no existe en ninguno, se muestra la clave
     y queda anotada en Gioval.i18n.faltantes.
   Cada idioma se registra con Gioval.i18n.registrar(código, { meta, textos }). Ver docs/AGREGAR_IDIOMA.md. */
Gioval.i18n = (function () {
  const I = { tablas: {}, actual: "es-AR", faltantes: new Set(), _origen: new Map(), _nodos: new Map() };
  const BASE = "es-AR";

  /* ---- registro ---- */
  I.registrar = function (codigo, def) {
    const meta = Object.assign({ nombre: codigo, nombreNativo: codigo, dir: "ltr", voz: [codigo], locale: codigo, moneda: "USD", fallback: [], notas: null }, def.meta || {});
    I.tablas[codigo] = { codigo, meta, textos: def.textos || {} };
    return I.tablas[codigo];
  };
  /* idioma derivado de otro por una transformación (para pseudo-idiomas de prueba) */
  I.registrarDerivado = function (codigo, de, meta, transformar) {
    I.registrar(codigo, { meta: Object.assign({ derivadoDe: de }, meta), textos: {} });
    I.tablas[codigo].transformar = transformar;
  };
  /* una isla (o cualquier archivo) suma sus textos a un idioma ya registrado: Gioval.i18n.agregar("es-AR", { "colores.nombre": "…" }) */
  I.agregar = function (codigo, textos) { if (!I.tablas[codigo]) return false; Object.assign(I.tablas[codigo].textos, textos); return true; };
  I.idiomas = () => Object.values(I.tablas).map(t => ({ codigo: t.codigo, nombre: t.meta.nombre, nombreNativo: t.meta.nombreNativo, dir: t.meta.dir, prueba: !!t.meta.prueba }));
  I.meta = codigo => (I.tablas[codigo || I.actual] || I.tablas[BASE]).meta;
  I.cadena = function (codigo) {
    const out = [], ag = c => { if (c && I.tablas[c] && !out.includes(c)) out.push(c); };
    const t = I.tablas[codigo]; ag(codigo);
    if (t && t.meta.derivadoDe) ag(t.meta.derivadoDe);
    ((t && t.meta.fallback) || []).forEach(ag);
    ag(BASE); ag("en");
    return out;
  };

  /* ---- búsqueda de una clave siguiendo la cadena ---- */
  function buscar(clave) {
    for (const c of I.cadena(I.actual)) {
      const t = I.tablas[c];
      if (Object.prototype.hasOwnProperty.call(t.textos, clave)) return { v: t.textos[clave], tabla: t };
      if (t.meta.derivadoDe) { const b = I.tablas[t.meta.derivadoDe]; if (b && Object.prototype.hasOwnProperty.call(b.textos, clave)) return { v: b.textos[clave], tabla: t }; }
    }
    return null;
  }
  I.tiene = clave => !!buscar(clave);

  /* ---- formato ---- */
  function parsear(s) {
    if (I._nodos.has(s)) return I._nodos.get(s);
    let i = 0;
    const ws = () => { while (i < s.length && /\s/.test(s[i])) i++; };
    function texto(dentro) {
      const out = []; let buf = "";
      while (i < s.length) {
        const c = s[i];
        if (c === "{") { if (buf) { out.push(buf); buf = ""; } i++; out.push(arg()); }
        else if (c === "}" && dentro) break;
        else { buf += c; i++; }
      }
      if (buf) out.push(buf); return out;
    }
    function arg() {
      let nombre = ""; while (i < s.length && s[i] !== "," && s[i] !== "}") nombre += s[i++];
      nombre = nombre.trim();
      if (s[i] === "}") { i++; return { v: nombre }; }
      i++; let tipo = ""; while (i < s.length && s[i] !== "," && s[i] !== "}") tipo += s[i++];
      tipo = tipo.trim(); if (s[i] === ",") i++;
      const ops = {};
      ws();
      while (i < s.length && s[i] !== "}") {
        let k = ""; while (i < s.length && !/[\s{]/.test(s[i])) k += s[i++];
        ws(); if (s[i] !== "{") throw new Error("texto mal formado: " + s);
        i++; ops[k] = texto(true); i++; ws();
      }
      i++; return { v: nombre, tipo, ops };
    }
    const nodos = texto(false); I._nodos.set(s, nodos); return nodos;
  }
  let _pr = null, _prCodigo = null;
  function reglaPlural(n) {
    const loc = I.meta().locale;
    if (_prCodigo !== loc) { try { _pr = new Intl.PluralRules(loc); } catch (e) { _pr = new Intl.PluralRules("en"); } _prCodigo = loc; }
    return _pr.select(n);
  }
  I.categoriaPlural = reglaPlural;
  function render(nodos, p, num) {
    let out = "";
    for (const n of nodos) {
      if (typeof n === "string") { out += num == null ? n : n.replace(/#/g, I.num(num)); continue; }
      const val = p[n.v];
      if (!n.tipo) { out += val === undefined ? "{" + n.v + "}" : String(val); continue; }
      if (n.tipo === "select") { const r = n.ops[String(val)] || n.ops.other; out += r ? render(r, p, num) : ""; continue; }
      if (n.tipo === "plural") {
        const v = +val, r = n.ops["=" + v] || n.ops[reglaPlural(v)] || n.ops.other;
        out += r ? render(r, p, v) : ""; continue;
      }
    }
    return out;
  }
  I.formatear = (s, p) => render(parsear(s), p || {}, null);

  /* ---- API de uso ---- */
  I.t = function (clave, p) {
    const r = buscar(clave);
    if (!r) { I.faltantes.add(clave); return clave; }
    let v = r.v; if (Array.isArray(v)) v = v[0];
    if (typeof v !== "string") { I.faltantes.add(clave); return clave; }
    let s = I.formatear(v, p);
    if (r.tabla.transformar) s = r.tabla.transformar(s);
    if (I._origen.size > 800) I._origen.clear();
    I._origen.set(s, clave);
    return s;
  };
  I.tl = function (clave, p) {
    const r = buscar(clave);
    if (!r) { I.faltantes.add(clave); return [clave]; }
    const arr = Array.isArray(r.v) ? r.v : [r.v];
    return arr.map(v => { let s = I.formatear(v, p); if (r.tabla.transformar) s = r.tabla.transformar(s); I._origen.set(s, clave); return s; });
  };
  I.dato = function (clave) { const r = buscar(clave); return r ? r.v : undefined; };
  /* clave de la que salió un texto ya formateado (la usa la voz para buscar audio grabado) */
  I.claveDe = texto => I._origen.get(texto) || null;

  /* ---- formatos por idioma: números, dinero, fechas ---- */
  const loc = () => I.meta().locale;
  I.num = n => { try { return new Intl.NumberFormat(loc()).format(n); } catch (e) { return String(n); } };
  I.dinero = n => { const m = I.meta(); try { return new Intl.NumberFormat(m.locale, { style: "currency", currency: m.moneda }).format(n); } catch (e) { return String(n); } };
  I.fecha = (d, opc) => { try { return new Intl.DateTimeFormat(loc(), opc).format(d); } catch (e) { return String(d); } };
  I.fechaHora = d => { try { return new Date(d).toLocaleString(loc()); } catch (e) { return String(d); } };
  /* nombres de las notas musicales según el idioma/región (Do Re Mi en español, C D E en inglés) */
  I.nombreNota = pc => { for (const c of I.cadena(I.actual)) { const n = I.tablas[c].meta.notas; if (n) return n[((pc % 12) + 12) % 12]; } return String(pc); };
  /* número en palabras: cada idioma aporta meta.numeroEnPalabras(n, opciones) */
  I.numeroEnPalabras = (n, o) => { for (const c of I.cadena(I.actual)) { const f = I.tablas[c].meta.numeroEnPalabras; if (f) return f(n, o || {}); } return String(n); };

  /* ---- DOM: data-i18n, data-i18n-html, data-i18n-title, data-i18n-placeholder (+ data-i18n-n para {n}) ---- */
  I.aplicar = function (raiz) {
    const r = raiz || document, q = (a, f) => r.querySelectorAll("[" + a + "]").forEach(f);
    const par = el => (el.dataset.i18nN != null ? { n: +el.dataset.i18nN } : {});
    q("data-i18n", el => { el.textContent = I.t(el.dataset.i18n, par(el)); });
    q("data-i18n-html", el => { el.innerHTML = I.t(el.dataset.i18nHtml, par(el)); });
    q("data-i18n-title", el => { el.title = I.t(el.dataset.i18nTitle); });
    q("data-i18n-placeholder", el => { el.placeholder = I.t(el.dataset.i18nPlaceholder); });
  };

  /* ---- idioma del aparato y de cada jugador ---- */
  const CLAVE_DISP = "gioval_idioma" + (Gioval.espacio ? "_" + Gioval.espacio : "");
  I.delAparato = function () { try { const c = localStorage.getItem(CLAVE_DISP); if (c && I.tablas[c]) return c; } catch (e) {} return BASE; };
  I.guardarDelAparato = function (c) { try { localStorage.setItem(CLAVE_DISP, c); } catch (e) {} };
  /* cambia el idioma de la interfaz: lang/dir del documento, textos estáticos y aviso a quien tenga que redibujar */
  I.usar = function (codigo) {
    if (!I.tablas[codigo]) codigo = BASE;
    const cambio = codigo !== I.actual;
    I.actual = codigo; _prCodigo = null;
    const m = I.meta(), h = document.documentElement;
    h.lang = codigo; h.dir = m.dir || "ltr";
    document.title = I.t("app.titulo");
    I.aplicar(document);
    Gioval.emit("idioma", { codigo, cambio });
    return codigo;
  };
  return I;
})();
const t = (clave, p) => Gioval.i18n.t(clave, p);
const tl = (clave, p) => Gioval.i18n.tl(clave, p);
