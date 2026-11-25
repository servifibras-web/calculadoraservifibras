"use strict";
/* ============ ISLA LETRAS ============
   Lógica de la isla. TODO el contenido (textos, palabras, rimas, frases, escalera de habilidades) está en
   js/datos/letras.js; acá no hay textos ni listas, solo cómo se juega.
   Qué trae:
   - 20 tipos de actividad por toque (lname, lsound, lpic, lcount, lrhyme, lsyl, lbuild, lmissing, lcase, lsplit, lnombre,
     lrsyl, lrword, lrphrase, labc, lcomp, lorden, lcluster, lbien, lalfa) sobre el motor genérico de toques.
   - Preguntas iniciales para adultos (una vez por niño) -> store.intake[KID].letras.
   - Juego de ubicación adaptativo (~5 min) con resumen que el adulto puede ajustar antes de aceptar.
   - Informe para adultos con evidencia (aciertos, tiempo, retención) y qué se saltó y por qué.
   El salto por dominio rápido vive en js/core/dominio.js (genérico, sin nombrar la isla). */
(function () {
const D = Gioval.datos.letras, I18 = Gioval.i18n;
/* Los textos viven en la tabla es-AR (js/datos/letras.js, claves "letras.*"). Acá se leen SIEMPRE al momento de usarlos
   (así cambian con el idioma). tx(clave_completa, {huecos}) devuelve la frase armada (si es una lista de variantes, una al azar);
   TX.grupo.clave y TA.<tipo>.<clave> son atajos de lectura. Las claves en el código van en camelCase y se convierten a snake_case. */
const sn = s => String(s).replace(/([A-Z])/g, m => "_" + m.toLowerCase());
const claveDe = k => k.split(".").map(sn).join(".");   /* siempre claves completas (prefijo letras) */
const lista = r => Array.isArray(r) && r.every(x => typeof x === "string");
const tx = (k, v) => { const c = claveDe(k), raw = I18.dato(c); return lista(raw) ? rnd(tl(c, v)) : t(c, v); };
const hayGrupo = c => Object.keys(I18.tablas["es-AR"].textos).some(x => x.startsWith(c + "."));
const grupoTx = pre => new Proxy({}, { get(_, p) {
  if (typeof p !== "string") return undefined;
  const c = pre + "." + sn(p), raw = I18.dato(c);
  if (raw === undefined) return hayGrupo(c) ? grupoTx(c) : undefined;
  return typeof raw === "string" ? t(c) : (lista(raw) ? tl(c) : raw);
} });
const TX = grupoTx("letras"), TA = TX.actividades;
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const LN = l => (I18.dato("letras.nombres_letras") || {})[l] || l.toLowerCase();
const ABC = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ".split("");

/* ---------- palabras: se deduce todo de js/datos/letras.js ---------- */
const sinAc = s => s.replace(/Á/g, "A").replace(/É/g, "E").replace(/Í/g, "I").replace(/Ó/g, "O").replace(/Ú/g, "U");
const WORDS = D.PALABRAS.map(([sy, e]) => {
  const sl = sy.split("-"), w = sl.join(""), base = sinAc(w), ini = base[0];
  return { w, sy: sl, e, lo: w.toLowerCase(), base, ini,
    dip: sl.some(x => /[AEIOUÁÉÍÓÚ]{2}/.test(x)),                                   /* diptongo o hiato dentro de una sílaba: no sirve para contar/separar */
    simple: !/[ÁÉÍÓÚ]|LL|RR|GU|QU|CH|H/.test(w) && w.length >= 3 && w.length <= 8,   /* letra por letra sin trampas */
    cvcv: sl.length === 2 && sl.every(x => /^[BCDFGJLMNÑPRSTVZ][AEIOU]$/.test(x)),    /* dos sílabas directas: MANO, PATO */
    fon: "AEIOUMPSLTNDFRBCGJ".includes(ini) && !/^(CH|LL)/.test(w) && !/^[CG][EI]/.test(base) /* la inicial se oye sin ambigüedad */ };
});
const byW = Object.fromEntries(WORDS.map(w => [w.w, w]));
const WORDSET = new Set(WORDS.map(w => w.w));
/* letras que se confunden de oído en el habla rioplatense (b/v, s/z/c, g/j, h muda...): nunca juntas en un ejercicio de sonido */
const chocan = (a, b) => a !== b && ((D.CONFUNDEN[a] || "").includes(b) || (D.CONFUNDEN[b] || "").includes(a));
const esVocal = c => "AEIOU".includes(c);
const pic = e => `<div class="pic">${e}</div>`;
const slots = (a, cont) => `<div class="slots${cont ? " " + cont : ""}">${a.map(x => `<span class="sl${x.c ? " " + x.c : ""}">${x.t || "&nbsp;"}</span>`).join("")}</div>`;
const cap = (e, t) => `${e}<small class="cap">${t}</small>`;
const lay = ops => { const n = ops.length; return { oc: n === 3 ? 3 : (n >= 5 ? 3 : 2), ocl: n === 3 ? 3 : (n >= 5 ? 3 : n) }; };
const tileOc = n => Math.min(4, Math.ceil(n / 2));
const mk = (v, h, extra) => Object.assign({ val: v, html: h == null ? v : h }, extra);
const tiles = (vals, extra, cls) => shuffle(vals.map((v, i) => ({ val: v, html: v, id: i, cls, extra: !!extra && i >= vals.length - extra })));
const sufijo = (a, b) => { let i = 0; while (i < a.length && i < b.length && a[a.length - 1 - i] === b[b.length - 1 - i]) i++; return a.slice(a.length - i); };
const letrasDe = w => w.split("");
const sil = w => w.sy.map(x => x.toLowerCase()).join(", ");

const ACT = {};   /* tipos de actividad de la isla */

/* ---------- 1) lname: tocar la letra por su nombre ---------- */
ACT.lname = {
  okMsgs: TA.lname.ok, noVoiceAid: 0,
  make(s) {
    const pool = (s.prior && s.prior.length && Math.random() < .3) ? s.prior : s.letters, t = pick(pool, "ln" + s.id);
    const rest = shuffle([...new Set([...s.letters, ...(s.prior || [])])].filter(x => x !== t));
    const vals = shuffle([t, ...rest.slice(0, 3)]), cases = {}; vals.forEach(v => cases[v] = Math.random() < .5);
    return { skill: s, t, seq: [t], cases, far: vals.find(v => v !== t), opts: vals.map(v => mk(v)) };
  },
  view(it, aid) {
    const w = byW[D.ANCLAS[it.t]], nom = LN(it.t); let ops = it.opts;
    if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    if (aid >= 2) ops = ops.map(o => mk(o.val, it.cases[o.val] ? o.val : o.val.toLowerCase()));
    const say = aid === 0 ? tx("letras.actividades.lname.pedirAyuda", { nombre: nom, palabra: w.lo }) : tx("letras.actividades.lname.pedir", { nombre: nom });
    return Object.assign({ say, stage: aid === 0 ? pic(w.e) : "", opts: ops }, lay(ops));
  },
  tip: it => TA.lname.tip, reveal: it => tx("letras.actividades.lname.reveal", { nombre: LN(it.t), palabra: byW[D.ANCLAS[it.t]].lo })
};

/* ---------- 2) lsound: ¿con qué letra empieza? (dibujo -> letra) ---------- */
ACT.lsound = {
  okMsgs: TA.lsound.ok, noVoiceAid: 1,
  make(s) {
    const pool = WORDS.filter(w => w.fon && s.letters.includes(w.ini)), L = pick([...new Set(pool.map(w => w.ini))], "lsL" + s.id);
    const w = pick(pool.filter(x => x.ini === L), "ls" + s.id + L);
    const rest = shuffle(s.letters.filter(x => x !== w.ini && !chocan(w.ini, x))), vals = shuffle([w.ini, ...rest.slice(0, 3)]);
    return { skill: s, wd: w, seq: [w.ini], far: vals.find(v => v !== w.ini), opts: vals.map(v => mk(v)) };
  },
  view(it, aid, T) {
    const w = it.wd; let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    let stage = aid >= 2 ? pic("🎧") : pic(w.e);
    if (T.reveal) stage = pic(w.e) + slots(letrasDe(w.w).map((c, i) => ({ t: c, c: i === 0 ? "hl" : "" })));
    return Object.assign({ say: tx(aid >= 2 ? "letras.actividades.lsound.pedir" : "letras.actividades.lsound.pedirAyuda", { palabra: w.lo }), stage, opts: ops }, lay(ops));
  },
  tip: it => tx("letras.actividades.lsound.tip", { palabra: it.wd.lo }), reveal: it => tx("letras.actividades.lsound.reveal", { palabra: it.wd.lo, nombre: LN(it.wd.ini) })
};

/* ---------- 3) lpic: de la letra al dibujo (letra -> dibujo) ---------- */
ACT.lpic = {
  okMsgs: TA.lpic.ok, noVoiceAid: 1,
  make(s) {
    const pool = WORDS.filter(w => w.fon && s.letters.includes(w.ini)), L = pick([...new Set(pool.map(w => w.ini))], "lpL" + s.id);
    const tw = pick(pool.filter(x => x.ini === L), "lp" + s.id + L), dist = [];
    shuffle(pool).forEach(w => { if (dist.length < 2 && w.ini !== L && !chocan(L, w.ini) && !dist.some(d => d.ini === w.ini)) dist.push(w); });
    return { skill: s, L, wd: tw, seq: [tw.w], far: dist[0].w, opts: shuffle([tw, ...dist]).map(w => mk(w.w, pic(w.e))) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    let say; const nom = LN(it.L);
    if (aid === 0) { const n = ops.map(o => byW[o.val].lo); say = tx(n.length === 3 ? "letras.actividades.lpic.pedirAyuda" : "letras.actividades.lpic.pedirAyuda2", { nombre: nom, a: n[0], b: n[1], c: n[2] }); }
    else say = tx("letras.actividades.lpic.pedir", { nombre: nom });
    return Object.assign({ say, stage: `<div class="lmodel">${it.L}</div>`, opts: ops }, lay(ops));
  },
  tip: it => TA.lpic.tip, reveal: it => tx("letras.actividades.lpic.reveal", { palabra: it.wd.lo, nombre: LN(it.L) })
};

/* ---------- 4) lcount: ¿cuántos pedacitos (sílabas) tiene? ---------- */
ACT.lcount = {
  okMsgs: TA.lcount.ok, noVoiceAid: 0,
  make(s) {
    const c = pick(range(1, s.max), "lc" + s.id), w = pick(WORDS.filter(x => !x.dip && x.sy.length === c), "lcw" + s.id + c);
    const cand = shuffle(range(1, Math.max(s.max, c + 1)).filter(v => v !== c)).slice(0, 2);
    return { skill: s, wd: w, n: c, seq: [c], far: cand[0], opts: shuffle([c, ...cand]).map(v => mk(v)) };
  },
  view(it, aid) {
    const w = it.wd; let ops = it.opts; if (aid === 0 && ops.length > 2) ops = ops.filter(o => o.val !== it.far);
    const stage = pic(w.e) + (aid === 0 ? slots(w.sy.map(x => ({ t: x })), "pal") : "");
    return Object.assign({ say: tx(aid === 0 ? "letras.actividades.lcount.pedirAyuda" : "letras.actividades.lcount.pedir", { palabra: w.lo, silabas: sil(w) }), stage, opts: ops }, lay(ops));
  },
  tip: it => tx("letras.actividades.lcount.tip", { silabas: sil(it.wd) }), reveal: it => tx("letras.actividades.lcount.reveal", { palabra: it.wd.lo, n: I18.numeroEnPalabras(it.n), silabas: sil(it.wd) })
};

/* ---------- 5) lrhyme: ¿cuál rima? (se ve la palabra escrita: sirve aunque haya seseo) ---------- */
const GRUPOS_RIMA = D.RIMAS.map(g => g.map(x => byW[x]).filter(Boolean));
ACT.lrhyme = {
  okMsgs: TA.lrhyme.ok, noVoiceAid: 0,
  make(s) {
    const g = pick(GRUPOS_RIMA.filter(x => x.length >= 2), "rm"), [a, b] = shuffle(g).slice(0, 2), dist = [];
    shuffle(GRUPOS_RIMA.filter(x => x !== g)).forEach(x => { const w = rnd(x); if (dist.length < 2 && sufijo(w.lo, a.lo).length < 2 && !dist.some(d => d.e === w.e || sufijo(d.lo, w.lo).length >= 2)) dist.push(w); });
    return { skill: s, a, b, seq: [b.w], far: dist[0].w, opts: shuffle([b, ...dist]).map(w => mk(w.w, cap(w.e, w.w))) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    return Object.assign({ say: tx(aid === 0 ? "letras.actividades.lrhyme.pedirAyuda" : "letras.actividades.lrhyme.pedir", { palabra: it.a.lo, rima: it.b.lo }), stage: pic(it.a.e) + `<div class="lpal">${it.a.w}</div>`, opts: ops }, lay(ops));
  },
  tip: it => TA.lrhyme.tip, reveal: it => tx("letras.actividades.lrhyme.reveal", { palabra: it.a.lo, rima: it.b.lo, fin: sufijo(it.a.lo, it.b.lo) })
};

/* ---------- 6) lsyl: armar la palabra con sílabas ---------- */
ACT.lsyl = {
  okMsgs: TA.lsyl.ok, noVoiceAid: 0,
  make(s) {
    const w = pick(WORDS.filter(x => !x.dip && x.sy.length >= 2 && x.sy.length <= 3), "ly" + s.id);
    const ex = shuffle([...new Set(WORDS.flatMap(x => x.sy).filter(y => !w.sy.includes(y)))]).slice(0, 2);
    let t; for (let g = 0; g < 10; g++) { t = tiles([...w.sy, ...ex], 2, "syl"); if (t.filter(x => !x.extra).map(x => x.val).join("-") !== w.sy.join("-")) break; }
    return { skill: s, wd: w, seq: w.sy, consume: true, tiles: t, opts: t };
  },
  view(it, aid, T) {
    const w = it.wd, sl = it.seq.map((c, i) => ({ t: i < T.pos ? c : (aid === 0 && i === T.pos ? c : ""), c: aid === 0 && i === T.pos ? "syl ghost" : "syl" }));
    const ops = it.tiles.filter(t => aid >= 2 || !t.extra);
    return { say: aid >= 2 ? TA.lsyl.pedir : tx("letras.actividades.lsyl.pedirAyuda", { palabra: w.lo }), stage: pic(w.e) + slots(sl), opts: ops, oc: ops.length > 4 ? 3 : 2, ocl: ops.length > 4 ? 3 : 2 };
  },
  tip: it => TA.lsyl.tip, reveal: (it, T) => tx("letras.actividades.lsyl.reveal", { silaba: it.seq[T.pos].toLowerCase() })
};

/* ---------- 7) lbuild: armar la palabra con letras ---------- */
ACT.lbuild = {
  okMsgs: TA.lbuild.ok, noVoiceAid: 0,
  make(s) {
    const w = pick(WORDS.filter(x => x.simple && x.w.length >= s.len[0] && x.w.length <= s.len[1]), "lb" + s.id);
    const letters = letrasDe(w.w), ex = shuffle("AEIOUMPSLTNDCBRFG".split("").filter(c => !letters.includes(c))).slice(0, 2);
    let t; for (let g = 0; g < 10; g++) { t = tiles([...letters, ...ex], 2); if (t.filter(x => !x.extra).map(x => x.val).join("") !== w.w) break; }
    return { skill: s, wd: w, seq: letters, consume: true, tiles: t, opts: t };
  },
  view(it, aid, T) {
    const w = it.wd, sl = it.seq.map((c, i) => ({ t: i < T.pos ? c : (aid === 0 && i === T.pos ? c : ""), c: aid === 0 && i === T.pos ? "ghost" : "" }));
    const ops = it.tiles.filter(t => aid >= 2 || !t.extra);
    return { say: aid >= 2 ? TA.lbuild.pedir : tx("letras.actividades.lbuild.pedirAyuda", { palabra: w.lo }), stage: pic(w.e) + slots(sl), opts: ops, oc: tileOc(ops.length), ocl: Math.min(3, tileOc(ops.length)) };
  },
  tip: it => TA.lbuild.tip, reveal: (it, T) => tx("letras.actividades.lbuild.reveal", { nombre: LN(it.seq[T.pos]) })
};

/* ---------- 8) lmissing: ¿qué letra falta? (modo "vocal" o "letra") ---------- */
ACT.lmissing = {
  okMsgs: TA.lmissing.ok, noVoiceAid: 0,
  make(s) {
    const vocal = s.modo === "vocal", cand = WORDS.filter(x => x.simple && x.w.length >= s.len[0] && x.w.length <= s.len[1]);
    for (let tries = 0; tries < 60; tries++) {
      const w = pick(cand, "lm" + s.id), pos = letrasDe(w.w).map((c, i) => i).filter(i => vocal ? esVocal(w.w[i]) : true);
      if (!pos.length) continue; const i = rnd(pos), ans = w.w[i];
      const pool = (vocal ? "AEIOU".split("") : "AEIOUMPSLTNDCBRFGJVZ".split("")).filter(c => c !== ans && !chocan(ans, c) && !WORDSET.has(w.w.slice(0, i) + c + w.w.slice(i + 1)));
      const same = shuffle(pool.filter(c => esVocal(c) === esVocal(ans))), oth = shuffle(pool.filter(c => esVocal(c) !== esVocal(ans)));
      const need = vocal ? 2 : 3, ds = [...same, ...oth].slice(0, need); if (ds.length < need) continue;
      return { skill: s, wd: w, i, seq: [ans], far: ds[0], opts: shuffle([ans, ...ds]).map(v => mk(v)) };
    }
    const w = byW.PATO; return { skill: s, wd: w, i: 1, seq: ["A"], far: "E", opts: ["A", "E", "U"].map(v => mk(v)) };
  },
  view(it, aid, T) {
    const w = it.wd, done = T.pos >= 1 || T.reveal;
    const sl = letrasDe(w.w).map((c, i) => i === it.i ? (done ? { t: c, c: "blank" } : { t: "?", c: "blank" }) : { t: c });
    let ops = it.opts; if (aid === 0 && ops.length > 3) ops = ops.filter(o => o.val !== it.far);
    return Object.assign({ say: aid === 0 ? tx("letras.actividades.lmissing.pedirAyuda", { palabra: w.lo }) : TA.lmissing.pedir, stage: pic(w.e) + slots(sl), opts: ops }, lay(ops));
  },
  tip: it => TA.lmissing.tip, reveal: it => tx("letras.actividades.lmissing.reveal", { nombre: LN(it.seq[0]), palabra: it.wd.lo })
};

/* ---------- 9) lcase: mayúscula <-> minúscula (pareja de la letra) ---------- */
ACT.lcase = {
  okMsgs: TA.lcase.ok, noVoiceAid: 0,
  make(s) {
    const L = pick(s.letters, "lcs" + s.id), aMin = Math.random() < .5, grupo = D.FORMAS_PARECIDAS.find(g => g.includes(L.toLowerCase())) || "";
    const ds = shuffle(s.letters.filter(x => x !== L && !grupo.includes(x.toLowerCase()))).slice(0, 2), cv = c => aMin ? c.toLowerCase() : c;
    return { skill: s, L, aMin, seq: [cv(L)], far: cv(ds[0]), opts: shuffle([L, ...ds]).map(c => mk(cv(c))) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    const mod = it.aMin ? it.L : it.L.toLowerCase();
    const say = aid === 0 ? tx(it.aMin ? "letras.actividades.lcase.pedirAyudaMin" : "letras.actividades.lcase.pedirAyudaMay", { nombre: LN(it.L) }) : (it.aMin ? TA.lcase.pedirMin : TA.lcase.pedirMay);
    return Object.assign({ say, stage: `<div class="lmodel">${mod}</div>`, opts: ops }, lay(ops));
  },
  tip: it => TA.lcase.tip, reveal: it => tx("letras.actividades.lcase.reveal", { nombre: LN(it.L) })
};

/* ---------- 10) lsplit: ¿cómo se separa en sílabas? ---------- */
function particiones(w) {
  const cortes = []; let c = 0; w.sy.forEach((x, i) => { c += x.length; if (i < w.sy.length - 1) cortes.push(c); });
  const txt = cs => { const out = []; let a = 0; [...cs, w.w.length].forEach(b => { out.push(w.w.slice(a, b)); a = b; }); return out.join("-"); };
  const valido = cs => cs.every((x, i) => x >= 1 && x <= w.w.length - 1 && (i === 0 || x > cs[i - 1]));
  const alts = new Set();
  cortes.forEach((x, i) => [-1, 1].forEach(d => { const n = cortes.slice(); n[i] = x + d; if (valido(n)) alts.add(txt(n)); }));
  for (let p = 1; p < w.w.length && alts.size < 4; p++) if (!cortes.includes(p)) { const n = [...cortes, p].sort((a, b) => a - b); if (valido(n)) alts.add(txt(n)); }
  alts.delete(txt(cortes));
  return { ok: txt(cortes), alts: [...alts] };
}
ACT.lsplit = {
  okMsgs: TA.lsplit.ok, noVoiceAid: 0,
  make(s) {
    const w = pick(WORDS.filter(x => !x.dip && x.sy.length >= 2 && x.sy.length <= 4), "lsp" + s.id), p = particiones(w), ds = shuffle(p.alts).slice(0, 2);
    return { skill: s, wd: w, ok: p.ok, seq: [p.ok], far: ds[0], opts: shuffle([p.ok, ...ds]).map(v => mk(v, v, { cls: "syl" })) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0 && ops.length > 2) ops = ops.filter(o => o.val !== it.far);
    return { say: tx(aid === 0 ? "letras.actividades.lsplit.pedirAyuda" : "letras.actividades.lsplit.pedir", { palabra: it.wd.lo, silabas: sil(it.wd) }), stage: pic(it.wd.e), opts: ops, oc: 1, ocl: ops.length, wide: true };
  },
  tip: it => TA.lsplit.tip, reveal: it => tx("letras.actividades.lsplit.reveal", { silabas: it.ok })
};

/* ---------- 11) lnombre: armar mi nombre ---------- */
const letrasNombre = () => { const l = String(KID || "").toUpperCase().replace(/Ñ/g, "\u0001").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/\u0001/g, "Ñ").replace(/[^A-ZÑ]/g, ""); return l.length >= 2 ? l : "SOL"; };
ACT.lnombre = {
  okMsgs: TA.lnombre.ok, noVoiceAid: 0,
  make(s) {
    const letters = letrasNombre().split("").slice(0, 12), ex = letters.length >= 8 ? 0 : 2;
    const extras = shuffle("AEIOUMPSLTNDCBRFG".split("").filter(c => !letters.includes(c))).slice(0, ex);
    let t; for (let g = 0; g < 10; g++) { t = tiles([...letters, ...extras], ex); if (t.filter(x => !x.extra).map(x => x.val).join("") !== letters.join("")) break; }
    return { skill: s, letters, seq: letters, consume: true, tiles: t, opts: t };
  },
  view(it, aid, T) {
    const sl = it.seq.map((c, i) => ({ t: i < T.pos ? c : (aid === 0 && i === T.pos ? c : ""), c: aid === 0 && i === T.pos ? "ghost" : "" }));
    const ops = it.tiles.filter(t => aid >= 2 || !t.extra);
    return { say: aid >= 2 ? tx("letras.actividades.lnombre.pedir", { nombre: esc(KID) }) : tx("letras.actividades.lnombre.pedirAyuda", { nombre: KID, deletreo: it.letters.map(LN).join(", ") }), stage: pic("🦊") + slots(sl), opts: ops, oc: tileOc(ops.length), ocl: Math.min(4, tileOc(ops.length)) };
  },
  tip: it => TA.lnombre.tip, reveal: (it, T) => tx("letras.actividades.lnombre.reveal", { letra: LN(it.seq[T.pos]) })
};

/* ---------- 12) lrsyl: leer sílabas (sílaba -> dibujo, o dibujo -> sílaba) ---------- */
const VOC5 = "AEIOU".split("");
ACT.lrsyl = {
  okMsgs: TA.lrsyl.ok, noVoiceAid: 0,
  make(s) {
    const pool = WORDS.filter(w => w.sy[0].length === 2 && s.cons.includes(w.sy[0][0]) && VOC5.includes(w.sy[0][1]) && !w.dip);
    const sils = [...new Set(pool.map(w => w.sy[0]))], sy = pick(sils, "lrs" + s.id), tw = pick(pool.filter(w => w.sy[0] === sy), "lrw" + s.id + sy);
    if (Math.random() < .4) {   /* dibujo -> sílaba */
      const c = sy[0], v = sy[1], parecidas = shuffle(s.cons.split("").filter(x => x !== c).map(x => x + v)).slice(0, 1).concat(shuffle(VOC5.filter(x => x !== v).map(x => c + x)).slice(0, 1));
      return { skill: s, modo: "inv", sy, wd: tw, seq: [sy], far: parecidas[0], opts: shuffle([sy, ...parecidas]).map(x => mk(x, x, { cls: "syl" })) };
    }
    const dist = []; shuffle(pool.filter(w => w.sy[0] !== sy)).sort((a, b) => ((b.sy[0][0] === sy[0]) + (b.sy[0][1] === sy[1])) - ((a.sy[0][0] === sy[0]) + (a.sy[0][1] === sy[1]))).forEach(w => { if (dist.length < 2 && !dist.some(d => d.sy[0] === w.sy[0] || d.e === w.e)) dist.push(w); });
    return { skill: s, modo: "dir", sy, wd: tw, seq: [tw.w], far: dist[0].w, opts: shuffle([tw, ...dist]).map(w => mk(w.w, pic(w.e))) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    if (it.modo === "inv") return Object.assign({ say: aid === 0 ? tx("letras.actividades.lrsyl.pedirInvAyuda", { palabra: it.wd.lo, silaba: it.sy.toLowerCase() }) : TA.lrsyl.pedirInv, stage: pic(it.wd.e), opts: ops }, lay(ops));
    return Object.assign({ say: aid === 0 ? tx("letras.actividades.lrsyl.pedirAyuda", { silaba: it.sy.toLowerCase() }) : TA.lrsyl.pedir, stage: `<div class="lmodel">${it.sy}</div>`, opts: ops }, lay(ops));
  },
  tip: it => TA.lrsyl.tip, reveal: it => tx("letras.actividades.lrsyl.reveal", { palabra: it.wd.lo, silaba: it.sy.toLowerCase() })
};

/* ---------- 13) lrword: leer una palabra y elegir el dibujo ---------- */
const sim = (a, b) => (a.base[0] === b.base[0] ? 2 : 0) + (a.base.slice(-1) === b.base.slice(-1) ? 1 : 0) + (a.sy.length === b.sy.length ? 1 : 0);
ACT.lrword = {
  okMsgs: TA.lrword.ok, noVoiceAid: 0,
  make(s) {
    const pool = WORDS.filter(w => s.banco === "cvcv" ? w.cvcv : (!w.cvcv && w.base.length >= 4)), tw = pick(pool, "lw" + s.id), dist = [];
    shuffle(pool.filter(w => w !== tw)).sort((a, b) => sim(b, tw) - sim(a, tw)).slice(0, 8).forEach(w => { if (dist.length < 2 && !dist.some(d => d.e === w.e) && w.e !== tw.e) dist.push(w); });
    return { skill: s, wd: tw, seq: [tw.w], far: dist[0].w, opts: shuffle([tw, ...dist]).map(w => mk(w.w, pic(w.e))) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    return Object.assign({ say: aid === 0 ? tx("letras.actividades.lrword.pedirAyuda", { palabra: it.wd.lo }) : TA.lrword.pedir, stage: `<div class="lpal">${it.wd.w}</div>`, opts: ops }, lay(ops));
  },
  tip: it => TA.lrword.tip, reveal: it => tx("letras.actividades.lrword.reveal", { palabra: it.wd.lo })
};

/* ---------- 14) lrphrase: leer una frase y elegir el dibujo ---------- */
ACT.lrphrase = {
  okMsgs: TA.lrphrase.ok, noVoiceAid: 0,
  make(s) {
    const f = pick(D.FRASES, "lf" + s.id);
    return { skill: s, fr: f[0], seq: [f[1]], far: f[2], opts: shuffle([f[1], f[2], f[3]]).map(v => mk(v)) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    return { say: aid === 0 ? tx("letras.actividades.lrphrase.pedirAyuda", { frase: it.fr.toLowerCase() }) : TA.lrphrase.pedir, stage: `<div class="lpal fr">${it.fr}</div>`, opts: ops, oc: 1, ocl: ops.length, wide: true };
  },
  tip: it => TA.lrphrase.tip, reveal: it => tx("letras.actividades.lrphrase.reveal", { frase: it.fr.toLowerCase() })
};

/* ---------- 15) labc: ¿qué letra va antes / después? ---------- */
ACT.labc = {
  okMsgs: TA.labc.ok, noVoiceAid: 0,
  make(s) {
    const desp = Math.random() < .6, i = desp ? R(0, ABC.length - 2) : R(1, ABC.length - 1), ref = ABC[i], ai = desp ? i + 1 : i - 1, ans = ABC[ai];
    const cer = shuffle(ABC.filter((x, j) => x !== ans && x !== ref && Math.abs(j - ai) <= 3)).slice(0, 2);
    return { skill: s, desp, i, ref, ans, seq: [ans], far: cer[0], opts: shuffle([ans, ...cer]).map(v => mk(v)) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    const q = tx(it.desp ? "letras.actividades.labc.despues" : "letras.actividades.labc.antes", { nombre: LN(it.ref) });
    const vecinos = it.desp ? [ABC[it.i - 2], ABC[it.i - 1], it.ref, "?"] : ["?", it.ref, ABC[it.i + 1], ABC[it.i + 2]];
    const stage = aid === 0 ? slots(vecinos.filter(Boolean).map(c => ({ t: c, c: c === "?" ? "blank" : (c === it.ref ? "hl" : "") }))) : slots([it.desp ? { t: it.ref, c: "hl" } : { t: "?", c: "blank" }, it.desp ? { t: "?", c: "blank" } : { t: it.ref, c: "hl" }]);
    return Object.assign({ say: q, stage, opts: ops }, lay(ops));
  },
  tip: it => TA.labc.tip, reveal: it => tx(it.desp ? "letras.actividades.labc.revealDespues" : "letras.actividades.labc.revealAntes", { nombre: LN(it.ref), nombre2: LN(it.ans) })
};

/* ---------- 16) lcomp: entender un texto corto ---------- */
ACT.lcomp = {
  okMsgs: TA.lcomp.ok, noVoiceAid: 0,
  make(s) {
    const c = pick(D.COMP[s.banco], "lcp" + s.id), [t, q, ok, d1, d2] = c;
    return { skill: s, texto: t, preg: q, seq: [ok], far: d1, opts: shuffle([ok, d1, d2]).map(v => { const txt = /^[\wáéíóúñ]/.test(v); return mk(v, txt && v.length <= 2 ? v : (txt ? v : pic(v)), { cls: txt && v.length > 2 ? "syl" : "" }); }) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0) ops = ops.filter(o => o.val !== it.far);
    const largo = it.texto.length > 70;
    const texto = `<div class="letTexto${largo ? " lg" : ""}">${esc(it.texto)}</div><div class="letPreg">${esc(it.preg)}</div>`;
    const emoji = !ops.some(o => o.cls === "syl");
    return { say: aid === 0 ? tx("letras.actividades.lcomp.pedirAyuda", { texto: it.texto, pregunta: it.preg }) : TA.lcomp.pedir, stage: texto, opts: ops, oc: emoji ? ops.length : 1, ocl: ops.length, wide: !emoji };
  },
  tip: it => TA.lcomp.tip, reveal: it => tx("letras.actividades.lcomp.reveal", { texto: it.texto })
};

/* ---------- 17) lorden: ordenar las palabras de una oración ---------- */
ACT.lorden = {
  okMsgs: TA.lorden.ok, noVoiceAid: 0,
  make(s) {
    const o = pick(D.ORACIONES, "lo" + s.id), pal = o[0].split(" ");
    let t; for (let g = 0; g < 12; g++) { t = tiles(pal, 0, "syl pal2"); if (t.map(x => x.val).join(" ") !== o[0]) break; }
    return { skill: s, fr: o[0], e: o[1], seq: pal, consume: true, tiles: t, opts: t };
  },
  view(it, aid, T) {
    const sl = it.seq.map((c, i) => ({ t: i < T.pos ? c : (aid === 0 && i === T.pos ? c : ""), c: "syl" + (aid === 0 && i === T.pos ? " ghost" : "") }));
    return { say: aid === 0 ? tx("letras.actividades.lorden.pedirAyuda", { frase: it.fr.toLowerCase() }) : TA.lorden.pedir, stage: pic(it.e) + slots(sl, "pal"), opts: it.tiles, oc: it.tiles.length > 4 ? 3 : 2, ocl: it.tiles.length > 4 ? 3 : it.tiles.length };
  },
  tip: it => TA.lorden.tip, reveal: (it, T) => tx("letras.actividades.lorden.reveal", { palabra: it.seq[T.pos].toLowerCase() })
};

/* ---------- 18) lcluster: letras que van juntas (trabadas y dígrafos) ---------- */
ACT.lcluster = {
  okMsgs: TA.lcluster.ok, noVoiceAid: 0,
  make(s) {
    const G = D.GRUPOS[s.banco], [sy, g] = pick(G.items, "lcl" + s.id), sl = sy.split("-"), w = sl.join(""), i = w.indexOf(g);
    const ds = shuffle(G.opciones.filter(x => x !== g && !WORDSET.has(w.slice(0, i) + x + w.slice(i + g.length)) && !chocan(g[0], x[0]))).slice(0, 2);
    const ws = byW[w];
    return { skill: s, w, ws, i, g, seq: [g], far: ds[0], opts: shuffle([g, ...ds]).map(v => mk(v, v, { cls: "syl" })) };
  },
  view(it, aid, T) {
    const done = T.pos >= 1 || T.reveal, L = letrasDe(it.w), sl = [];
    L.forEach((c, k) => { if (k === it.i) sl.push(done ? { t: it.g, c: "blank" } : { t: "?", c: "blank" }); else if (k < it.i || k >= it.i + it.g.length) sl.push({ t: c }); });
    let ops = it.opts; if (aid === 0 && ops.length > 2) ops = ops.filter(o => o.val !== it.far);
    return Object.assign({ say: aid === 0 ? tx("letras.actividades.lcluster.pedirAyuda", { palabra: it.w.toLowerCase() }) : TA.lcluster.pedir, stage: pic(it.ws ? it.ws.e : "") + slots(sl), opts: ops }, lay(ops));
  },
  tip: it => TA.lcluster.tip, reveal: it => tx("letras.actividades.lcluster.reveal", { grupo: it.g, palabra: it.w.toLowerCase() })
};

/* ---------- 19) lbien: ¿cuál está bien escrita? (ortografía de uso común, mayúsculas y puntos) ---------- */
ACT.lbien = {
  okMsgs: TA.lbien.ok, noVoiceAid: 0,
  make(s) {
    if (s.banco === "orto") { const [e, ok, ...resto] = pick(D.ORTO, "lbo" + s.id), regla = resto.pop(); return { skill: s, e, ok, regla, seq: [ok], far: resto[0], opts: shuffle([ok, ...resto]).map(v => mk(v, v, { cls: "syl" })) }; }
    const [ok, mal, regla] = pick(D.MAYUS, "lbm" + s.id); return { skill: s, e: "", ok, regla, seq: [ok], far: mal, opts: shuffle([ok, mal]).map(v => mk(v, v, { cls: "syl" })) };
  },
  view(it, aid) {
    let ops = it.opts; if (aid === 0 && ops.length > 2) ops = ops.filter(o => o.val !== it.far);
    return { say: aid === 0 && it.e ? tx("letras.actividades.lbien.pedirAyuda", { palabra: it.ok.toLowerCase() }) : (it.e ? TA.lbien.pedirDib : TA.lbien.pedir), stage: it.e ? pic(it.e) : "", opts: ops, oc: 1, ocl: ops.length, wide: true };
  },
  tip: it => TA.lbien.tip, reveal: it => tx("letras.actividades.lbien.reveal", { correcta: it.ok, regla: it.regla })
};

/* ---------- 20) lalfa: ordenar palabras según el abecedario ---------- */
ACT.lalfa = {
  okMsgs: TA.lalfa.ok, noVoiceAid: 0,
  make(s) {
    const usadas = new Set(), tri = []; shuffle(WORDS.filter(w => !w.dip)).forEach(w => { if (tri.length < 3 && !usadas.has(w.ini)) { usadas.add(w.ini); tri.push(w); } });
    const orden = tri.slice().sort((a, b) => ABC.indexOf(a.ini) - ABC.indexOf(b.ini));
    return { skill: s, orden, seq: orden.map(w => w.w), consume: true, opts: shuffle(tri).map((w, i) => ({ val: w.w, id: i, html: `<span class="em2">${w.e}</span><small class="cap">${w.w}</small>` })) };
  },
  view(it, aid, T) {
    const n = T.pos, stage = aid === 0 ? slots(it.orden.map((w, i) => ({ t: i < n ? w.ini : (i === n ? "?" : ""), c: i === n ? "blank" : "" }))) : "";
    return { say: aid === 0 ? TA.lalfa.pedirAyuda : TA.lalfa.pedir, stage: stage || `<div class="lpal">A → Z</div>`, opts: it.opts, oc: 3, ocl: 3 };
  },
  tip: it => TA.lalfa.tip, reveal: (it, T) => tx("letras.actividades.lalfa.reveal", { palabra: it.seq[T.pos].toLowerCase() })
};
Object.values(ACT).forEach(a => { a.tip = a.tip || (() => ""); });
/* las frases de proceso se leen al usarse (cambian con el idioma) */
Object.keys(ACT).forEach(k => Object.defineProperty(ACT[k], "okMsgs", { get: () => tl("letras.actividades." + k + ".ok"), enumerable: true, configurable: true }));

/* ---------- Habilidades ---------- */
const SKILLS = D.HABILIDADES.map(h => Object.defineProperty(Object.assign({}, h), "name", { get: () => t("letras.hab." + h.id), enumerable: true }));
const bySkill = Object.fromEntries(SKILLS.map(s => [s.id, s]));
const tramoDe = n => SKILLS.filter(s => s.nivel === n);
const primeraDe = n => SKILLS.find(s => s.nivel === n) || SKILLS[SKILLS.length - 1];

/* ---------- Versión de ubicación: cada tipo de un solo toque suma "No sé" y no da ayudas ---------- */
const ACTS_UBIC = {};
SKILLS.filter(s => s.sonda).forEach(s => {
  const k = s.type, A = ACT[k]; if (ACTS_UBIC["u_" + k]) return;
  ACTS_UBIC["u_" + k] = Object.assign({}, A, {
    make(sk) { const it = A.make(sk); it.skill = Object.assign({}, sk, { type: "u_" + k }); return it; },
    view(it, aid, T) {
      const v = A.view(it, 2, T), ops = v.opts.concat([mk("__nose", `🤷<small class="cap">${TX.ubicacion.nose}</small>`, { cls: "nose" })]);
      return Object.assign({}, v, { opts: ops }, v.wide ? { oc: 1, ocl: ops.length } : { oc: ops.length >= 5 ? 3 : 2, ocl: ops.length >= 5 ? 3 : ops.length });
    }
  });
});

/* ============ PREGUNTAS PARA ADULTOS (intake) ============ */
const intakeDe = k => { const i = store.intake && store.intake[k]; return (i && i.letras) || null; };
function guardarIntake(k, obj) { store.intake = store.intake || {}; (store.intake[k] = store.intake[k] || {}).letras = obj; save(); }
const nivelDe = r => Math.max(D.INICIO.letras[r.letras] || 0, D.INICIO.lee[r.lee] || 0, D.INICIO.nombre[r.nombre] || 0);
/* tramo desde donde arranca el JUEGO de ubicación: lo que dicen las respuestas; si no dicen nada, la edad */
const arranqueUbic = r => { const n = nivelDe(r); return n > 0 ? n : (D.INICIO.edadParaUbicacion[r.edad] || 0); };
const fechaCorta = ts => I18.fecha(new Date(ts));
const etiqueta = (lista, v) => { const o = lista.find(x => String(x.v) === String(v)); return o ? o.t : String(v); };

/* marca como sabidas (sin práctica) todas las habilidades de tramos < ini; las marcas anteriores de este tipo que ya no corresponden se anulan */
function aplicarInicio(ini, por, datos) {
  let n = 0;
  SKILLS.forEach(s => {
    const st = SK(s.id);
    if (s.nivel < ini) { if (Gioval.dominio.marcarSaltada(s, por, datos)) n++; }
    else if (st.mast && st.skip && st.skip.estado === "pendiente" && (st.skip.por === "ubicacion" || st.skip.por === "preguntas")) Gioval.dominio.revertir(s, "anulada");
  });
  save(); return n;
}

/* ============ JUEGO DE UBICACIÓN ============
   Escalera por tramos (0..7). En cada tramo se hacen 2 o 3 preguntas de un solo toque, SIN ayudas (con botón "No sé"):
     2 de 2 y una tercera correcta -> "ok" (3/3) | 3ª incorrecta o 2/3 -> "dudoso" (2/3) | 0/2 o 1/3 -> "no".
   "ok" sube un tramo, "no" baja uno, "dudoso" frena. Termina cuando el límite entre lo que sabe y no sabe está claro, a las 16
   preguntas o a los ~5,5 minutos. Punto de partida propuesto = último tramo "ok" (se practica ese; lo anterior se marca como sabido). */
const UB = { MAX_ITEMS: 16, MAX_MS: 330000 };
function evaluarTramo(R) {
  if (R.n < 2) return null;
  if (R.n === 2) return R.a === 0 ? "no" : null;
  return R.a === 3 ? "ok" : (R.a === 2 ? "dudoso" : "no");
}
function resultadoUbic(E) {
  let lim = null; for (let t = 0; t <= 7; t++) { const r = E.r[t]; if (r && r.estado !== "ok") { lim = t; break; } }
  let ini; if (lim === null) { const ts = Object.keys(E.r).map(Number); ini = ts.length ? Math.max(...ts) : 0; } else ini = Math.max(0, lim - 1);
  return Math.min(7, ini);
}
function siguienteTramo(E) {
  const R = E.r[E.cur], est = R.estado;
  if (est === "ok" && E.cur < 7 && !E.r[E.cur + 1]) return E.cur + 1;
  if (est === "no" && E.cur > 0 && !E.r[E.cur - 1]) return E.cur - 1;
  return null;
}
async function jugarUbicacion() {
  if (capLeft() <= 0) return showCap();
  const r = intakeDe(KID) || { edad: 5 };
  ensureCtx(); S.run++; const run = S.run; ocultarOv();
  S.check = true; S.session = null; S.finMode = "session"; S.capShown = false; S.hint = 2; S.mode = "demo";
  $("btnActSkip").style.display = "none"; entrarToques(TX.ubicacion.titulo); renderProg();
  const E = { cur: Math.min(7, arranqueUbic(r)), r: {}, n: 0, t0: Date.now() };
  await speak(tx("letras.ubicacion.intro", { nombre: KID })); if (run !== S.run) return;
  while (true) {
    const R = E.r[E.cur] || (E.r[E.cur] = { a: 0, n: 0, estado: null, k: R_start(E.cur) });
    const prob = tramoDe(E.cur).filter(s => s.sonda), s = prob[(R.k + R.n) % prob.length];
    const it = ACTS_UBIC["u_" + s.type].make(s);
    const res = await new Promise(ok => { S.onDone = ok; ACTS_UBIC["u_" + s.type].jugar(run, it, null); });
    if (run !== S.run) return;
    E.n++; R.n++; if (res.miss === 0) R.a++;
    R.estado = evaluarTramo(R);
    const pasaTiempo = E.n >= UB.MAX_ITEMS || Date.now() - E.t0 > UB.MAX_MS;
    setBubble(tx("letras.ubicacion.gracias")); await sleep(450); if (run !== S.run) return;
    if (!R.estado) { if (!pasaTiempo) continue; R.estado = R.a / R.n >= .66 ? "dudoso" : "no"; }
    const sig = pasaTiempo ? null : siguienteTramo(E);
    if (sig === null) break; E.cur = sig;
  }
  if (run !== S.run) return;
  S.mode = "done"; S.tap = null; S.check = false; S.onDone = null; $("btnActSkip").style.display = "";
  const ini = resultadoUbic(E), pend = { fecha: Date.now(), n: E.n, seg: Math.round((Date.now() - E.t0) / 1000), r: E.r, iniPropuesto: ini };
  const i = intakeDe(KID) || {}; i.ubicacionPend = pend; guardarIntake(KID, i);
  await speak(tx("letras.ubicacion.fin", { nombre: KID }));
  if (run !== S.run) return;
  resetFlow(); goMenuIsla();
  gate(() => vistaResumen());
}
const R_start = t => Math.floor(Math.random() * 7) + t;   /* para no preguntar siempre la misma habilidad del tramo */

/* ============ PANTALLAS PARA ADULTOS (una sola capa, #letOv) ============ */
const LS = { form: {}, ini: 0 };
const ov = () => $("letOv");
function mostrarOv(html) { ov().querySelector(".letCard").innerHTML = html; ov().classList.add("show"); ov().querySelector(".letCard").scrollTop = 0; }
function ocultarOv() { ov().classList.remove("show"); }
const btn = (a, t, extra = "") => `<button class="btn${extra}" data-a="${a}">${t}</button>`;

function vistaBienvenida() {
  mostrarOv(`<h2>${esc(TX.bienvenida.titulo)}</h2><p>${esc(tx("letras.bienvenida.texto", { nombre: KID }))}</p>
    <div class="letRow">${btn("bienvenidaSi", esc(TX.bienvenida.adulto))}${btn("cerrar", esc(TX.bienvenida.despues), " alt")}</div>`);
}
function vistaIntake() {
  const I = TX.intake, prev = intakeDe(KID); LS.form = prev ? { edad: prev.edad, letras: prev.letras, lee: prev.lee, nombre: prev.nombre } : {};
  const grupo = (k, q, ops) => `<div class="letQ"><b>${esc(q)}</b><div class="letOpts" data-k="${k}">${ops.map(o => `<button class="letBtn${String(LS.form[k]) === String(o.v) ? " sel" : ""}" data-a="resp" data-k="${k}" data-v="${o.v}">${esc(o.t)}</button>`).join("")}</div></div>`;
  mostrarOv(`<h2>${esc(tx("letras.intake.titulo", { nombre: KID }))}</h2><p>${esc(I.intro)}</p>
    ${grupo("edad", I.pEdad, I.edad)}${grupo("letras", I.pLetras, I.letras)}${grupo("lee", I.pLee, I.lee)}${grupo("nombre", I.pNombre, I.nombre)}
    <p class="letAviso" id="letFalta"></p><div class="letRow">${btn("guardarIntake", esc(I.guardar))}${btn("cerrar", esc(I.cancelar), " alt")}</div>`);
}
function vistaSugerido() {
  const r = intakeDe(KID), n = nivelDe(r), h = primeraDe(n), I = TX.intake;
  const frase = n === 0 ? tx("letras.intake.sugeridoCero", { nombre: KID, habilidad: h.name }) : tx("letras.intake.sugerido", { nombre: KID, habilidad: h.name, tramo: n + 1, nombreTramo: TX.tramos[n] });
  mostrarOv(`<h2>${esc(TX.menu.preguntas.t)}</h2><p>${esc(frase)}</p><p class="letAviso">${esc(I.aviso)}</p>
    <div class="letRow col">${btn("jugarUbic", esc(I.jugar))}${btn("usarPunto", esc(I.usar), " alt")}${btn("cerrar", esc(I.masTarde), " alt")}</div>`);
}
function vistaResumen() {
  const r = intakeDe(KID), p = r && r.ubicacionPend; if (!p) return;
  if (LS.pendId !== p.fecha) { LS.pendId = p.fecha; LS.ini = p.iniPropuesto; }
  const U = TX.ubicacion, ini = LS.ini, h = primeraDe(ini), nSab = SKILLS.filter(s => s.nivel < ini).length;
  const fila = t => { const x = p.r[t]; return `<li><b>${esc(tx("letras.ubicacion.fila", { n: t + 1, nombre: TX.tramos[t] }))}</b><br>${esc(x ? tx("letras.ubicacion." + x.estado, { a: x.a, b: x.n }) : U.sinPreguntar)}</li>`; };
  mostrarOv(`<h2>${esc(U.titResumen)}</h2><p>${esc(tx("letras.ubicacion.resumenTiempo", { n: p.n, min: Math.max(1, Math.round(p.seg / 60)) }))}</p>
    <ul class="letLista">${range(0, 7).map(fila).join("")}</ul>
    <p class="letProp">${esc(ini === 0 ? U.propuestaCero : tx("letras.ubicacion.propuesta", { tramo: ini + 1, habilidad: h.name, n: nSab }))}</p>
    <div class="letRow">${ini > 0 ? btn("antes", esc(U.antes), " alt") : ""}${ini < 7 ? btn("despues", esc(U.despues), " alt") : ""}</div>
    <p class="letAviso">${esc(TX.intake.aviso)}</p>
    <div class="letRow">${btn("aceptarUbic", esc(U.aceptar))}${btn("descartarUbic", esc(U.descartar), " alt")}</div>`);
}
function informeTexto() {
  const I = TX.informe, L = [], r = intakeDe(KID), hoy = fechaCorta(Date.now()), log = store.log[KID] || [];
  L.push(tx("letras.informe.titulo", { nombre: String(KID).toUpperCase() }), tx("letras.informe.fecha", { fecha: hoy }), "");
  if (r && r.edad) {
    L.push(tx("letras.informe.datos", { fecha: fechaCorta(r.fecha || Date.now()), edad: etiqueta(TX.intake.edad, r.edad), letras: etiqueta(TX.intake.letras, r.letras), lee: etiqueta(TX.intake.lee, r.lee), nombreEscribe: etiqueta(TX.intake.nombre, r.nombre) }));
    if (r.inicio) L.push(tx("letras.informe.inicio", { tramo: r.inicio.tramo + 1, habilidad: primeraDe(r.inicio.tramo).name, origen: r.inicio.origen }));
    if (r.ubicacion) { L.push(tx("letras.informe.ubic", { fecha: fechaCorta(r.ubicacion.fecha), n: r.ubicacion.n })); range(0, 7).forEach(t => { const x = r.ubicacion.r[t]; if (x) L.push(tx("letras.informe.ubicTramo", { n: t + 1, nombre: TX.tramos[t], estado: tx("letras.ubicacion." + x.estado, { a: x.a, b: x.n }) })); }); }
  } else L.push(I.sinDatos);
  L.push("", I.habilidades);
  const pc = a => a.length ? Math.round(100 * a.filter(Boolean).length / a.length) + "% (n=" + a.length + ")" : "–";
  SKILLS.forEach(s => {
    const ev = log.filter(e => e.s === s.id && e.k !== "check"), st = SK(s.id); if (!ev.length && !st.mast && !st.skip) return;
    L.push(tx("letras.informe.hab", { name: s.name, estado: st.skip && st.skip.estado === "pendiente" && !ev.length ? "saltada" : (st.mast ? "dom" : "prac"), edad: s.edad, tramo: s.nivel + 1 }));
    if (ev.length) { const first = ev.map(e => e.f); L.push(tx("letras.informe.acc", { a: pc(first.slice(0, 5)), b: pc(first.slice(-5)) }), tx("letras.informe.ret", { r: pc(ev.filter(e => e.g >= 1).map(e => e.o)) })); } else L.push(I.sinDatosHab);
    Gioval.dominio.lineasInforme(s, st, ev).forEach(l => L.push(l));
  });
  const m = Gioval.dominio.resumenSaltos(LETRAS_PACK());
  if (m.n) L.push("", tx("letras.informe.resumenSaltos", { n: m.n, c: m.confirmadas, r: m.revertidas, p: m.pendientes }));
  L.push("", I.chequeos); const ck = (store.checks[KID] || []).filter(c => c.p === "letras");
  if (!ck.length) L.push(I.sinChequeos); ck.slice(-12).forEach(c => L.push("   " + c.d + ": " + c.ok + "/" + c.n + " (" + Math.round(100 * c.ok / c.n) + "%)"));
  L.push("", I.comoLeerlo); return L.join("\n");
}
const LETRAS_PACK = () => Gioval.islas.lista.find(p => p.id === "letras");
function vistaInforme() {
  const I = TX.informe;
  mostrarOv(`<pre class="letPre" id="letPre">${esc(informeTexto())}</pre><div class="letRow">${btn("copiar", esc(I.copiar))}${btn("wa", esc(I.whatsapp))}${btn("cambiar", esc(I.cambiar), " alt")}${btn("cerrar", esc(I.cerrar), " alt")}</div>`);
}

const ACC = {
  cerrar() { ocultarOv(); },
  bienvenidaSi() { gate(() => vistaIntake()); },
  resp(b) { LS.form[b.dataset.k] = isNaN(+b.dataset.v) ? b.dataset.v : +b.dataset.v; b.parentElement.querySelectorAll(".letBtn").forEach(x => x.classList.toggle("sel", x === b)); const f = $("letFalta"); if (f) f.textContent = ""; },
  guardarIntake() {
    const F = LS.form; if (["edad", "letras", "lee", "nombre"].some(k => F[k] == null)) { $("letFalta").textContent = TX.intake.falta; return; }
    const prev = intakeDe(KID) || {}; guardarIntake(KID, Object.assign({}, prev, { fecha: Date.now(), edad: F.edad, letras: F.letras, lee: F.lee, nombre: F.nombre }));
    vistaSugerido(); renderMenuIsla();
  },
  jugarUbic() { jugarUbicacion(); },
  usarPunto() {
    const r = intakeDe(KID), n = nivelDe(r);
    aplicarInicio(n, "preguntas", { ts: Date.now() }); r.inicio = { tramo: n, origen: "preguntas", fecha: Date.now() }; guardarIntake(KID, r); ocultarOv(); renderMenuIsla();
  },
  antes() { LS.ini = Math.max(0, LS.ini - 1); vistaResumen(); },
  despues() { LS.ini = Math.min(7, LS.ini + 1); vistaResumen(); },
  aceptarUbic() {
    const r = intakeDe(KID), p = r.ubicacionPend, ajustado = LS.ini !== p.iniPropuesto;
    aplicarInicio(LS.ini, "ubicacion", { ts: p.fecha, n: p.n });
    r.ubicacion = { fecha: p.fecha, n: p.n, seg: p.seg, r: p.r, iniPropuesto: p.iniPropuesto }; delete r.ubicacionPend;
    r.inicio = { tramo: LS.ini, origen: ajustado ? "ajustado" : "ubicacion", fecha: Date.now() }; guardarIntake(KID, r);
    ocultarOv(); renderMenuIsla(); setBubble(TX.ubicacion.aceptada);
  },
  descartarUbic() { const r = intakeDe(KID); if (r) { delete r.ubicacionPend; guardarIntake(KID, r); } ocultarOv(); renderMenuIsla(); },
  copiar() { try { navigator.clipboard.writeText(informeTexto()); } catch (e) {} },
  wa() { window.open("https://wa.me/?text=" + encodeURIComponent(informeTexto()), "_blank"); },
  cambiar() { vistaIntake(); }
};

const DOM = {
  pantallas: `<div class="big letOv" id="letOv"><div class="letCard"></div></div>`
};
const VISTO = {};
function iniciar() {
  ov().addEventListener("click", e => { const b = e.target.closest("[data-a]"); if (b && ACC[b.dataset.a]) ACC[b.dataset.a](b); });
  Gioval.on("menu", p => {
    $("btnActSkip").style.display = ""; ocultarOv();
    if (!p || p.id !== "letras") return;
    if (!intakeDe(KID) && !VISTO[KID]) { VISTO[KID] = true; vistaBienvenida(); }
  });
}
function tarjetas(done) {
  const r = intakeDe(KID), M = TX.menu, out = [];
  if (!r || !r.edad) out.push({ em: "📝", t: M.preguntas.t, s: M.preguntas.s, on: true, go: () => gate(() => vistaIntake()) });
  else if (r.ubicacionPend) out.push({ em: "📋", t: M.resultado.t, s: M.resultado.s, on: true, go: () => gate(() => vistaResumen()) });
  else out.push({ em: "🎯", t: M.ubicacion.t, s: done ? "Mañana seguimos 🌙" : M.ubicacion.s, on: !done, go: () => jugarUbicacion() });
  out.push({ em: "📄", t: M.informe.t, s: M.informe.s, on: true, go: () => gate(() => vistaInforme()) });
  return out;
}

Gioval.islas.registrar({
  id: "letras", get name() { return TX.isla.nombre; }, emoji: "🔤", get sub() { return TX.isla.sub; }, skills: SKILLS, tap: true, plain: true,
  instrumento: null, entradas: ["toque"], actividades: Object.assign({}, ACT, ACTS_UBIC),
  dom: DOM, iniciar, tarjetas,
  get outro() { return TX.isla.outro; }, get capTail() { return TX.isla.capTail; }, get notaInforme() { return t("dominio.nota"); }
});
/* para las pruebas y las herramientas de depuración */
Gioval.letras = { WORDS, SKILLS, intakeDe, nivelDe, arranqueUbic, aplicarInicio, evaluarTramo, resultadoUbic, informeTexto, particiones };
})();
