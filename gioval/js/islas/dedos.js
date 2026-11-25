"use strict";
/* ============ DE A DOS (jugar por turnos con un hermano o hermana, en el mismo aparato) ============
   NO es una isla de aprendizaje: no se registra en Gioval.islas (no tiene habilidades propias). Es un MODO que juega las
   habilidades de una isla que ya existe (hoy Números o Letras: las islas por toque), de a un turno por vez:
     - Cada chico juega SU plan: cada turno llama a planSession() con KID = el chico del turno, así que el nivel, el repaso espaciado
       (Leitner), las ayudas que se retiran, el dominio, las estrellas y el tiempo diario son los de SIEMPRE y de cada uno.
       Las respuestas pasan por el mismo itemDone() del motor: no hay otra forma de sumar progreso. Nadie baja ni sube de nivel por el otro.
     - Capa cooperativa: un dibujo del equipo (8 piezas) que crece cuando CUALQUIERA de los dos resuelve un ítem sin que la app
       le muestre la respuesta. Los errores no restan nada. El dibujo no toca el dominio de nadie.
     - Momento de enseñar (regla fija, sin azar): si al que le toca ya dominó (de verdad, no saltada sin comprobar) la habilidad que
       el otro está practicando, la app le propone explicarle. NO suma nada al dominio de nadie; solo piezas para el dibujo del equipo.
     - Tiempo: el tiempo de cada turno cuenta contra el tope diario de ESE chico (store.time / store.limit / store.extra), porque
       el turno se juega con KID = ese chico. Las pantallas de entrega de turno no son ".juego", así que esperar no gasta tiempo.
   Se engancha al motor con ganchos genéricos que no nombran este archivo:
     Gioval.modos (ui.js: tarjeta en "¿Quién juega?" y en el mapa; adultos.js: sección del informe),
     S.session.alFin / alResponder / alTope / alVolver (motor.js y actividades.js: ver docs/DE_A_DOS.md).
   Lo que se guarda (store.dedos, migración v4):
     eq  = { "A|B": { piezas, cuadros, total } }                      el dibujo de cada pareja (A y B en orden alfabético)
     reg = { niño: [ { t, c, n, ok, s, tr, e, r, p } ] }               una entrada por sesión y por niño (hasta 90):
           cuándo, con quién, respuestas, al primer intento, segundos jugados, turnos, veces que explicó, veces que escuchó, piezas del equipo
   Cada evento de práctica de de-a-dos queda además en store.log[niño] con la marca d:1 (para separar después, si hace falta). */
(function () {
const L = (k, p) => Gioval.i18n.t(k, p), LL = (k, p) => Gioval.i18n.tl(k, p);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---------------- textos (frases completas; es-AR base y en completo) ---------------- */
Gioval.i18n.agregar("es-AR", {
  "dedos.nombre": "De a dos", "dedos.sub": "¡Jugamos por turnos, juntos!",
  "dedos.voz.entrada": "¡Vamos a jugar de a dos! Elijan quiénes juegan.",
  "dedos.ui.titulo": "👫 De a dos",
  "dedos.ui.quienes": "¿Quiénes juegan? Toquen a los dos, en el orden en que van a jugar.",
  "dedos.ui.falta": "Falta elegir a alguien más.",
  "dedos.ui.pocos": "Para jugar de a dos hacen falta dos jugadores con tiempo para hoy.",
  "dedos.ui.isla": "¿A qué isla vamos?",
  "dedos.ui.ir": "¡A jugar!",
  "dedos.ui.ya_jugo": "Ya jugó hoy",
  "dedos.turno.ahora": "Ahora le toca a {nombre}",
  "dedos.turno.voz": "Ahora le toca a {nombre}. Cuando quieras, tocá el botón grande.",
  "dedos.turno.vamos": "¡Vamos!",
  "dedos.turno.terminar": "Terminar por hoy",
  "dedos.act.turno": "Turno de {nombre}",
  "dedos.equipo.linea": "Nuestro dibujo: {cuadro} ({n} de {total})",
  "dedos.cuadro.huerta": "Huerta", "dedos.cuadro.ciudad": "Ciudad", "dedos.cuadro.mar": "Mar", "dedos.cuadro.espacio": "Espacio",
  "dedos.equipo.completo": "¡Armaron el dibujo «{cuadro}» entre los dos!",
  "dedos.equipo.completo_voz": "¡Lo lograron! Entre los dos armaron el dibujo «{cuadro}».",
  "dedos.equipo.seguir": "¡Seguimos!",
  "dedos.explica.titulo": "{nombre}, ¡te toca explicar!",
  "dedos.explica.texto": "{oyente} está practicando «{habilidad}» y vos ya lo sabés. ¿Le explicás cómo se hace?",
  "dedos.explica.consejos": ["Contale qué mirás primero.", "Mostrale un ejemplo.", "Decile qué hacés cuando te trabás."],
  "dedos.explica.hecho": "¡Ya le expliqué!", "dedos.explica.ahora_no": "Ahora no",
  "dedos.explica.gracias": "¡Gracias por explicar! Explicar también es aprender. Sumaron {n, plural, one{# pieza} other{# piezas}} al dibujo del equipo.",
  "dedos.pausa.titulo": "¿Terminamos por hoy?", "dedos.pausa.texto": "Lo que hicieron hasta ahora quedó guardado.", "dedos.pausa.seguir": "Seguir jugando",
  "dedos.tope.titulo": "{nombre} ya jugó por hoy",
  "dedos.tope.texto": "{nombre} completó los {n} minutos de hoy. ¡Gracias por jugar! Mañana seguimos.",
  "dedos.tope.voz": "{nombre}, completaste tus {n} minutos de hoy. ¡Gracias por jugar! Mañana seguimos.",
  "dedos.tope.sigue": "Seguir con {otro}",
  "dedos.fin.titulo": "¡Buen trabajo, equipo!",
  "dedos.fin.texto": "{piezas, plural, =0{Hoy todavía no sumaron piezas al dibujo.} one{Hoy sumaron # pieza al dibujo entre los dos.} other{Hoy sumaron # piezas al dibujo entre los dos.}}",
  "dedos.fin.kid": "{nombre}: {n, plural, =0{ninguna respuesta} one{# respuesta} other{# respuestas}}",
  "dedos.fin.voz": "Gracias por jugar de a dos, {a} y {b}. ¡Mañana seguimos!",
  "dedos.fin.ok": "Listo",
  "dedos.informe.titulo": "👫 DE A DOS (por turnos, en el mismo aparato)",
  "dedos.informe.resumen": "{n, plural, one{# sesión} other{# sesiones}} de a dos. Cada chico sigue su propio plan: lo que responde acá cuenta en SU progreso, igual que siempre. Explicarle a otro no suma nada al dominio.",
  "dedos.informe.fila": "• {fecha} con {compa}: {n, plural, =0{sin respuestas} one{# respuesta} other{# respuestas}} ({ok} al primer intento), {min} min, {tr, plural, one{# turno} other{# turnos}}, {p, plural, =0{sin piezas} one{# pieza} other{# piezas}} para el dibujo del equipo.",
  "dedos.informe.explico": "   Le explicó a {compa} ({n, plural, one{# vez} other{# veces}}). No cuenta para el dominio.",
  "dedos.informe.escucho": "   Escuchó la explicación de {compa} ({n, plural, one{# vez} other{# veces}}).",
});
Gioval.i18n.agregar("en", {
  "dedos.nombre": "Together", "dedos.sub": "Let's play in turns, together!",
  "dedos.voz.entrada": "Let's play together! Choose who is playing.",
  "dedos.ui.titulo": "👫 Together",
  "dedos.ui.quienes": "Who is playing? Tap both of you, in the order you will play.",
  "dedos.ui.falta": "One more player to choose.",
  "dedos.ui.pocos": "To play together we need two players who still have time today.",
  "dedos.ui.isla": "Which island shall we go to?",
  "dedos.ui.ir": "Let's play!",
  "dedos.ui.ya_jugo": "Already played today",
  "dedos.turno.ahora": "It's {nombre}'s turn",
  "dedos.turno.voz": "It's {nombre}'s turn. Whenever you like, tap the big button.",
  "dedos.turno.vamos": "Let's go!",
  "dedos.turno.terminar": "Stop for today",
  "dedos.act.turno": "{nombre}'s turn",
  "dedos.equipo.linea": "Our picture: {cuadro} ({n} of {total})",
  "dedos.cuadro.huerta": "Garden", "dedos.cuadro.ciudad": "City", "dedos.cuadro.mar": "Sea", "dedos.cuadro.espacio": "Space",
  "dedos.equipo.completo": "You built the “{cuadro}” picture together!",
  "dedos.equipo.completo_voz": "You did it! Together you built the “{cuadro}” picture.",
  "dedos.equipo.seguir": "Let's keep going!",
  "dedos.explica.titulo": "{nombre}, it's your turn to explain!",
  "dedos.explica.texto": "{oyente} is practicing “{habilidad}” and you already know it. Can you explain how to do it?",
  "dedos.explica.consejos": ["Tell what you look at first.", "Show an example.", "Say what you do when you get stuck."],
  "dedos.explica.hecho": "I explained it!", "dedos.explica.ahora_no": "Not now",
  "dedos.explica.gracias": "Thank you for explaining! Explaining is learning too. You added {n, plural, one{# piece} other{# pieces}} to the team picture.",
  "dedos.pausa.titulo": "Stop for today?", "dedos.pausa.texto": "What you did so far is saved.", "dedos.pausa.seguir": "Keep playing",
  "dedos.tope.titulo": "{nombre} is done for today",
  "dedos.tope.texto": "{nombre} played the {n} minutes for today. Thanks for playing! See you tomorrow.",
  "dedos.tope.voz": "{nombre}, you played your {n} minutes for today. Thanks for playing! See you tomorrow.",
  "dedos.tope.sigue": "Keep going with {otro}",
  "dedos.fin.titulo": "Great work, team!",
  "dedos.fin.texto": "{piezas, plural, =0{You haven't added pieces to the picture yet today.} one{Today you added # piece to the picture together.} other{Today you added # pieces to the picture together.}}",
  "dedos.fin.kid": "{nombre}: {n, plural, =0{no answers} one{# answer} other{# answers}}",
  "dedos.fin.voz": "Thanks for playing together, {a} and {b}. See you tomorrow!",
  "dedos.fin.ok": "Done",
  "dedos.informe.titulo": "👫 TOGETHER (in turns, on the same device)",
  "dedos.informe.resumen": "{n, plural, one{# session} other{# sessions}} together. Each child follows their own plan: what they answer here counts in THEIR progress, as always. Explaining to someone else adds nothing to mastery.",
  "dedos.informe.fila": "• {fecha} with {compa}: {n, plural, =0{no answers} one{# answer} other{# answers}} ({ok} on the first try), {min} min, {tr, plural, one{# turn} other{# turns}}, {p, plural, =0{no pieces} one{# piece} other{# pieces}} for the team picture.",
  "dedos.informe.explico": "   Explained to {compa} ({n, plural, one{# time} other{# times}}). It doesn't count toward mastery.",
  "dedos.informe.escucho": "   Heard the explanation from {compa} ({n, plural, one{# time} other{# times}}).",
});

/* ---------------- datos editables ---------------- */
const AJ = {
  itemsPorTurno: 4,            /* respuestas por turno antes de pasar el aparato (estimación: a validar con los chicos) */
  piezasExplicar: 2,           /* piezas del equipo por explicarle al otro */
  maxExplicaciones: 2,         /* por sesión */
  turnosEntreExplicaciones: 3, /* mínimo de turnos entre una propuesta y la siguiente */
  minIntentosOyente: 2,        /* el otro tiene que haber practicado esa habilidad al menos esto para que cuente como "la está practicando" */
  graciaTopeMs: 45000,         /* al llegar al tope en pleno ítem, se deja terminar ese ítem; pasado este tiempo se cierra el turno igual */
};
const CUADROS = [
  { id: "huerta", p: ["🌱", "🌿", "🌷", "🌻", "🍅", "🥕", "🐝", "🦋"] },
  { id: "ciudad", p: ["🏠", "🌳", "🚗", "🚲", "⛲", "🐕", "☀️", "🌈"] },
  { id: "mar", p: ["🌊", "🐚", "🐟", "🐙", "⛵", "🐢", "🦀", "🌅"] },
  { id: "espacio", p: ["🌙", "⭐", "🚀", "🪐", "🛰️", "☄️", "👽", "🌍"] },
];
const AVATARES = [{ e: "🦊", c: "#ffd9a8" }, { e: "🐻", c: "#cfe8ff" }, { e: "🐯", c: "#d8f5de" }, { e: "🐸", c: "#ffd0e0" }, { e: "🦉", c: "#e5dcff" }, { e: "🐙", c: "#fff3b0" }];
const avatarDe = k => AVATARES[Math.max(0, store.profiles.indexOf(k)) % AVATARES.length];
const avatarHtml = k => { const a = avatarDe(k); return `<span class="dd-av" style="--c:${a.c}">${a.e}</span>`; };

/* ---------------- datos guardados ---------------- */
function dd() { const s = store.dedos = (store.dedos && typeof store.dedos === "object" && !Array.isArray(store.dedos)) ? store.dedos : {}; s.eq = s.eq || {}; s.reg = s.reg || {}; return s; }
const claveEq = (a, b) => [a, b].sort().join("|");
function equipo(a, b) { const o = dd().eq, k = claveEq(a, b); return o[k] || (o[k] = { piezas: 0, cuadros: 0, total: 0 }); }
const cuadroDe = e => CUADROS[e.cuadros % CUADROS.length];
const restante = k => (store.limit[k] || 15) * 60 + (store.extra[k + "|" + today()] || 0) - (store.time[k + "|" + today()] || 0);   /* igual a capLeft() del motor, pero de cualquier chico */
const islasElegibles = () => PACKS.filter(p => p.tap && p.skills && p.skills.length && !p.entrar && !p.antesDeSesion && !p.menuPropio);

/* ---------------- estado de la sesión de a dos ---------------- */
let D = null;                       /* sesión en curso (null = no hay) */
let SEL = { orden: [], isla: null }; /* selección en la pantalla de armado */
let ORIGEN = "who";
let PASO = null;                    /* función que arma la pantalla de paso actual (se vuelve a llamar al cambiar el idioma) */
const otroDe = k => D.kids[0] === k ? D.kids[1] : D.kids[0];
const segundos = k => Math.max(0, (store.time[k + "|" + today()] || 0) - D.porKid[k].t0);
function marcarDia(k) { const ds = store.days[k] || (store.days[k] = []), d = today(); if (!ds.includes(d)) { ds.push(d); store.days[k] = ds.slice(-90); } }

/* ---------------- pantallas ---------------- */
const DOM = `
<style>
/* De a dos: todo con prefijo dd- / #dd para no tocar las demás pantallas */
.dd-body{flex:1;min-height:0;overflow:auto;display:flex;flex-direction:column;gap:10px;padding-bottom:6px}
.dd-hint{margin:0;font-size:clamp(17px,3.2vw,24px);font-weight:800;text-align:center}
.dd-chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.dd-chip{position:relative;border:0;border-radius:22px;background:#fff;color:#2b2350;padding:8px 14px;min-width:132px;max-width:100%;font-family:inherit;font-weight:900;font-size:clamp(18px,3.4vw,26px);box-shadow:0 5px 0 rgba(0,0,0,.14);display:flex;flex-direction:column;align-items:center;gap:2px;touch-action:manipulation}
.dd-chip b{max-width:100%;overflow-wrap:anywhere}
.dd-chip small{font-size:14px;font-weight:700;opacity:.7}
.dd-chip.sel{outline:5px solid #7c4dff}
.dd-chip:disabled{opacity:.45}
.dd-ord{position:absolute;inset-block-start:-8px;inset-inline-end:-8px;width:30px;height:30px;border-radius:50%;background:#7c4dff;color:#fff;font-style:normal;font-size:18px;display:flex;align-items:center;justify-content:center}
.dd-av{display:inline-flex;align-items:center;justify-content:center;width:1.5em;height:1.5em;border-radius:50%;background:var(--c,#fff);font-size:1.5em;line-height:1}
.dd-ir{align-self:center}
.dd-ir:disabled{opacity:.4}
#ddPaso{align-items:center}
.dd-paso{flex:1;min-height:0;width:100%;overflow:auto;display:flex;flex-direction:column;align-items:center;justify-content:safe center;gap:10px;text-align:center;padding:4px 6px}
#ddAv{font-size:clamp(40px,12vw,72px);line-height:1}
#ddAv .dd-em{font-size:1.4em}
#ddTit{margin:0;font-size:clamp(26px,6vw,46px);line-height:1.15;max-width:94vw;overflow-wrap:anywhere}
.dd-txt{max-width:94vw;font-size:clamp(17px,3.4vw,26px);font-weight:700;line-height:1.3}
.dd-txt div{margin:2px 0}
.dd-cu{display:none;flex-direction:column;align-items:center;gap:4px}
.dd-cu.on{display:flex}
.dd-cuadro{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;direction:ltr}
.dd-cell{width:clamp(28px,9vw,44px);height:clamp(28px,9vw,44px);border-radius:12px;border:3px dashed #b9a6ff;background:rgba(255,255,255,.5);display:flex;align-items:center;justify-content:center;font-size:clamp(16px,5vw,26px);line-height:1}
.dd-cell.on{border:3px solid #fff;background:#fff}
.dd-cell.nueva{animation:ddPop .5s ease-out}
@keyframes ddPop{0%{transform:scale(.3)}70%{transform:scale(1.25)}100%{transform:scale(1)}}
.dd-cu small{font-size:clamp(14px,2.6vw,18px);font-weight:700;opacity:.75}
.dd-acc{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;position:sticky;inset-block-end:0;padding:6px 10px 4px;z-index:1;border-radius:22px;background:rgba(255,236,246,.9)}   /* los botones siempre quedan a la vista aunque el texto sea largo (otros idiomas) */
.dd-acc .btn{max-width:94vw}
.dd-acc .btn:disabled{opacity:.5}
.dd-acc .btn.grande{font-size:clamp(24px,5vw,36px);padding:16px 34px}
.dd-eq{display:none;align-items:center;justify-content:center;flex-wrap:wrap;gap:4px 10px;padding:2px 0}
.dd-eq.on{display:flex}
.dd-eq .dd-av{font-size:22px}
.dd-eq .dd-quien{display:flex;align-items:center;gap:6px;font-weight:900;font-size:clamp(15px,3vw,20px);background:#fff;border-radius:16px;padding:2px 10px 2px 4px;max-width:60vw}
.dd-eq .dd-quien span:last-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dd-eq .dd-cuadro{gap:3px}
.dd-eq .dd-cell{width:clamp(22px,6.4vw,30px);height:clamp(22px,6.4vw,30px);border-width:2px;border-radius:8px;font-size:clamp(13px,3.6vw,18px)}
@media (min-width:700px) and (min-height:900px){
  .dd-cell{width:56px;height:56px;font-size:32px}
  .dd-eq .dd-cell{width:34px;height:34px;font-size:20px}
  #ddAv{font-size:96px}
}
@media (max-height:480px) and (orientation:landscape){
  .dd-paso{flex-direction:row;flex-wrap:wrap;gap:6px 16px;align-content:center}
  #ddAv{font-size:46px}
  #ddTit{font-size:clamp(20px,5vh,28px)}
  .dd-txt{font-size:15px}
  .dd-cell{width:26px;height:26px;font-size:15px;border-width:2px;border-radius:8px}
  .dd-acc .btn.grande{font-size:20px;padding:8px 22px}
  .dd-eq{padding:0}
  .dd-eq .dd-av{font-size:16px}
  .dd-eq .dd-cell{width:20px;height:20px;font-size:12px}
}
</style>
<div class="screen" id="ddSetup">
  <div class="bar"><button class="btn alt" id="ddSetupBack"><span class="arr">⬅</span><span class="lbl" data-i18n="app.volver"> Volver</span></button><h2 style="margin:0" data-i18n="dedos.ui.titulo">👫 De a dos</h2><span style="width:90px"></span></div>
  <div class="dd-body" id="ddSetupBody"></div>
</div>
<div class="screen" id="ddPaso">
  <div class="dd-paso">
    <div id="ddAv"></div>
    <h1 id="ddTit"></h1>
    <div class="dd-txt" id="ddTxt"></div>
    <div class="dd-cu" id="ddCu"><div class="dd-cuadro" id="ddCuadro"></div><small id="ddCuTxt"></small></div>
    <div class="dd-acc" id="ddAcc"></div>
  </div>
</div>`;

function cuadroHtml(e, nueva) {
  const c = cuadroDe(e);
  return c.p.map((x, i) => `<span class="dd-cell${i < e.piezas ? " on" : ""}${nueva && i === e.piezas - 1 ? " nueva" : ""}">${i < e.piezas ? x : ""}</span>`).join("");
}
const lineaEquipo = e => L("dedos.equipo.linea", { cuadro: L("dedos.cuadro." + cuadroDe(e).id), n: e.piezas, total: cuadroDe(e).p.length });

/* ---- armado: quiénes juegan y en qué isla ---- */
function abrirSetup() {
  const a = document.querySelector(".screen.active"); ORIGEN = a && a.id === "map" && KID ? "map" : "who";
  const libres = store.profiles.filter(n => restante(n) > 0);
  SEL = { orden: libres.length === 2 ? (ORIGEN === "map" && libres[1] === KID ? libres.slice().reverse() : libres.slice()) : (ORIGEN === "map" && libres.includes(KID) ? [KID] : []), isla: (islasElegibles()[0] || {}).id || null };
  show("ddSetup"); pintarSetup(); speak(L("dedos.voz.entrada"));
}
function pintarSetup() {
  const b = $("ddSetupBody"), el = islasElegibles(), libres = store.profiles.filter(n => restante(n) > 0);
  let h = `<p class="dd-hint">${esc(libres.length < 2 ? L("dedos.ui.pocos") : L("dedos.ui.quienes"))}</p><div class="dd-chips">`;
  store.profiles.forEach((n, i) => {
    const fuera = restante(n) <= 0, pos = SEL.orden.indexOf(n);
    h += `<button class="dd-chip${pos >= 0 ? " sel" : ""}" data-k="${i}"${fuera ? " disabled" : ""}>${avatarHtml(n)}<b>${esc(n)}</b>${fuera ? `<small>${esc(L("dedos.ui.ya_jugo"))}</small>` : ""}${pos >= 0 ? `<i class="dd-ord">${pos + 1}</i>` : ""}</button>`;
  });
  h += `</div>`;
  if (el.length > 1) {
    h += `<p class="dd-hint">${esc(L("dedos.ui.isla"))}</p><div class="dd-chips">`;
    el.forEach(p => { h += `<button class="dd-chip${SEL.isla === p.id ? " sel" : ""}" data-isla="${esc(p.id)}"><span style="font-size:1.5em;line-height:1">${p.emoji}</span><b>${esc(p.name)}</b></button>`; });
    h += `</div>`;
  }
  const listo = SEL.orden.length === 2;
  if (!listo && libres.length >= 2) h += `<p class="dd-hint" style="opacity:.75">${esc(L("dedos.ui.falta"))}</p>`;
  h += `<button class="btn dd-ir" id="ddIr"${listo ? "" : " disabled"}>${esc(L("dedos.ui.ir"))}</button>`;
  b.innerHTML = h;
}
$("app").insertAdjacentHTML("beforeend", DOM);
$("act").querySelector(".bar").insertAdjacentHTML("afterend", `<div class="dd-eq" id="ddEquipo"></div>`);   /* franja del turno y del dibujo, solo visible durante un turno de a dos */
$("ddSetupBack").onclick = () => { if (ORIGEN === "map" && KID) goMap(); else $("btnWho").onclick(); };
$("ddSetupBody").onclick = e => {
  const k = e.target.closest("[data-k]"), i = e.target.closest("[data-isla]"), ir = e.target.closest("#ddIr");
  if (k && !k.disabled) { const n = store.profiles[+k.dataset.k], p = SEL.orden.indexOf(n); if (p >= 0) SEL.orden.splice(p, 1); else if (SEL.orden.length < 2) SEL.orden.push(n); pintarSetup(); }
  else if (i) { SEL.isla = i.dataset.isla; pintarSetup(); }
  else if (ir && !ir.disabled) { ensureCtx(); empezar(); }
};

/* ---- pantalla de paso (entrega de turno, explicar, tope, pausa, fin): un solo diseño para todas ---- */
function paso(build, hablar) {
  PASO = build; pintarPaso(); show("ddPaso");
  if (hablar !== false) { const d = build(); if (d.voz) speak(d.voz); else setBubble(d.titulo); }
}
function pintarPaso() {
  if (!PASO) return;
  const d = PASO();
  $("ddAv").innerHTML = d.kid ? avatarHtml(d.kid) : `<span class="dd-em">${d.em || "👫"}</span>`;
  $("ddTit").textContent = d.titulo;
  const tx = $("ddTxt"); tx.innerHTML = ""; (d.lineas || []).forEach(l => { const x = document.createElement("div"); x.textContent = l; tx.appendChild(x); });
  tx.style.display = (d.lineas || []).length ? "" : "none";
  const cu = $("ddCu"), e = d.cuadro && D ? equipo(D.kids[0], D.kids[1]) : null;
  cu.classList.toggle("on", !!e);
  if (e) { $("ddCuadro").innerHTML = cuadroHtml(e); $("ddCuTxt").textContent = lineaEquipo(e); }
  const acc = $("ddAcc"); acc.innerHTML = "";
  d.botones.forEach(b => { const x = document.createElement("button"); x.className = "btn" + (b.cls ? " " + b.cls : ""); x.textContent = b.t; x.onclick = () => { if (x.disabled) return; x.disabled = true; ensureCtx(); b.go(); }; acc.appendChild(x); });
}

/* ---- franja dentro de la pantalla de actividad: de quién es el turno y el dibujo del equipo ---- */
function mostrarEquipo(on) { $("ddEquipo").classList.toggle("on", !!on); if (on) pintarEquipo(); }
function pintarEquipo(nueva) {
  if (!D || !$("ddEquipo").classList.contains("on")) return;
  const e = equipo(D.kids[0], D.kids[1]);
  $("ddEquipo").innerHTML = `<span class="dd-quien">${avatarHtml(KID)}<span>${esc(KID)}</span></span><span class="dd-cuadro" role="img" aria-label="${esc(lineaEquipo(e))}">${cuadroHtml(e, nueva)}</span>`;
}

/* ---------------- flujo ---------------- */
function empezar() {
  const [a, b] = SEL.orden, isla = islasElegibles().find(p => p.id === SEL.isla) || islasElegibles()[0];
  if (!a || !b || !isla) return;
  const nuevo = k => ({ n: 0, ok: 0, turnos: 0, e: 0, r: 0, t0: store.time[k + "|" + today()] || 0, ref: null });
  D = { kids: [a, b], isla, idx: 0, turnos: 0, porKid: { [a]: nuevo(a), [b]: nuevo(b) }, piezas: 0, avisado: {}, actual: a, celebrar: [], expl: { n: 0, ult: -99, hechas: {} } };
  siguiente();
}
const sin = k => restante(k) <= 0;
function siguiente() {
  if (!D) return;
  const [a, b] = D.kids;
  if (sin(a) && sin(b)) return final();
  for (const k of D.kids) if (sin(k) && !D.avisado[k]) { D.avisado[k] = 1; return pantallaTope(k, otroDe(k)); }   /* quien se quedó sin tiempo recibe un mensaje amable ya mismo */
  if (D.celebrar.length) return pantallaCelebracion();
  let quien = D.kids[D.idx % 2]; if (sin(quien)) { D.idx++; quien = D.kids[D.idx % 2]; }
  pantallaTurno(quien);
}
function usarIdioma(k) { KID = k; usarIdiomaDeJugador(); }
function pantallaTurno(quien) {
  D.actual = quien; usarIdioma(quien);
  paso(() => ({ kid: quien, titulo: L("dedos.turno.ahora", { nombre: quien }), voz: L("dedos.turno.voz", { nombre: quien }), cuadro: true,
    botones: [{ t: L("dedos.turno.vamos"), cls: "grande", go: () => iniciarTurno(quien) }, { t: L("dedos.turno.terminar"), cls: "alt", go: () => final() }] }));
}
function pantallaTope(k, otro) {
  usarIdioma(k); const n = store.limit[k] || 15;
  paso(() => ({ kid: k, titulo: L("dedos.tope.titulo", { nombre: k }), lineas: [L("dedos.tope.texto", { nombre: k, n })], voz: L("dedos.tope.voz", { nombre: k, n }),
    botones: [{ t: L("dedos.tope.sigue", { otro }), go: () => siguiente() }, { t: L("dedos.turno.terminar"), cls: "alt", go: () => final() }] }));
}
function pantallaCelebracion() {
  const c = D.celebrar.shift();
  paso(() => ({ em: "🎉", titulo: L("dedos.equipo.completo", { cuadro: L("dedos.cuadro." + c) }), voz: L("dedos.equipo.completo_voz", { cuadro: L("dedos.cuadro." + c) }), cuadro: true,
    botones: [{ t: L("dedos.equipo.seguir"), cls: "grande", go: () => siguiente() }] }));
}
function iniciarTurno(quien) {
  if (!D) return; usarIdioma(quien); PACK = D.isla;
  const p = proponerExplicacion(quien); if (p) return pantallaExplica(p);
  jugarTurno(quien);
}

/* ---- momento de enseñar: regla fija, sin azar ---- */
function proponerExplicacion(quien) {
  const X = D.expl, otro = otroDe(quien);
  if (X.n >= AJ.maxExplicaciones || D.turnos - X.ult < AJ.turnosEntreExplicaciones || sin(otro)) return null;
  const mast = (k, id) => { const s = store.sk[k + "|" + id]; return !!(s && s.mast); };
  const real = (k, id) => { const s = store.sk[k + "|" + id]; return !!(s && s.mast && !(s.skip && s.skip.estado === "pendiente")); };   /* una saltada sin comprobar no es saber */
  const aprende = D.isla.skills.find(s => s.req.every(r => mast(otro, r)) && !mast(otro, s.id));   /* lo que el otro está practicando (la misma habilidad "nueva" que usa su plan) */
  if (!aprende) return null;
  const st = store.sk[otro + "|" + aprende.id];
  if (!st || (st.att || 0) < AJ.minIntentosOyente || !real(quien, aprende.id) || X.hechas[aprende.id + "|" + quien]) return null;
  return { skill: aprende, id: aprende.id, explica: quien, oyente: otro, consejo: rnd(LL("dedos.explica.consejos")) };
}
function pantallaExplica(p) {
  const hab = () => p.skill.name;
  paso(() => ({ kid: p.explica, titulo: L("dedos.explica.titulo", { nombre: p.explica }), lineas: [L("dedos.explica.texto", { oyente: p.oyente, habilidad: hab() }), p.consejo],
    voz: L("dedos.explica.texto", { oyente: p.oyente, habilidad: hab() }) + " " + p.consejo,
    botones: [{ t: L("dedos.explica.hecho"), cls: "grande", go: async () => {
        const X = D.expl; X.n++; X.ult = D.turnos; X.hechas[p.id + "|" + p.explica] = 1;
        D.porKid[p.explica].e++; D.porKid[p.oyente].r++; sumar(AJ.piezasExplicar); actualizarReg(p.explica); actualizarReg(p.oyente); save();   /* nada del dominio: ni store.sk ni store.log */
        await speak(L("dedos.explica.gracias", { n: AJ.piezasExplicar })); if (D) jugarTurno(p.explica); } },
      { t: L("dedos.explica.ahora_no"), cls: "alt", go: () => { const X = D.expl; X.ult = D.turnos; X.hechas[p.id + "|" + p.explica] = 1; jugarTurno(p.explica); } }] }));
}

/* ---- un turno: unas pocas respuestas del plan de ESE chico, con el motor de siempre ---- */
async function jugarTurno(quien) {
  if (!D) return; usarIdioma(quien); PACK = D.isla; D.actual = quien;
  const plan = planSession(), items = plan.items.slice(0, AJ.itemsPorTurno);
  if (!items.length) { D.idx++; return siguiente(); }
  S.run++; const run = S.run; S.finMode = "session"; S.check = false; S.capShown = false; S.mode = "idle";
  S.session = { items, i: 0, log: [], t0: Date.now(), streak: 0, newly: [], seen: {},
    alFin: () => cerrarTurno(S.session), alResponder: (it, res, r) => alResponder(it, res, r), alTope: () => alTope(S.session), alVolver: () => pausa() };
  D.turnos++; D.porKid[quien].turnos++;
  enterPlay(L("dedos.act.turno", { nombre: quien })); mostrarEquipo(true);
  nextItem(run);
}
function alResponder(it, res, r) {
  if (!D) return; const k = KID, P = D.porKid[k];
  P.n++; if (r.first) P.ok++;
  const l = store.log[k]; if (l && l.length) l[l.length - 1].d = 1;
  marcarDia(k);
  if (!res.revealed) { sumar(1); pintarEquipo(true); }   /* una pieza si resolvió sin que la app le mostrara la respuesta (un error no resta nada) */
  actualizarReg(k); save();
}
/* se llegó al tope diario de quien está jugando: se deja terminar el ítem en curso (sin apuro) y el turno se cierra al terminarlo */
function alTope(ss) {
  if (!D || !ss || ss.cerrado) return false;
  ss.capDesde = ss.capDesde || Date.now();
  if (Date.now() - ss.capDesde > AJ.graciaTopeMs) { S.capShown = true; S.run++; try { speechSynthesis.cancel(); } catch (e) {} cerrarTurno(ss); }
  return true;
}
function cerrarTurno(ss) {
  if (!D || !ss || ss.cerrado) return; ss.cerrado = true;
  S.mode = "idle"; S.onDone = null; try { speechSynthesis.cancel(); } catch (e) {}
  for (const k of D.kids) actualizarReg(k);
  resetFlow(); mostrarEquipo(false); S.capShown = false;
  D.idx++; save(); siguiente();
}
function pausa() {   /* botón ⬅ durante un turno: lo hecho ya está guardado (cada ítem se guarda al terminar) */
  const ss = S.session; if (ss) ss.cerrado = true;
  S.run++; S.mode = "idle"; S.onDone = null; try { speechSynthesis.cancel(); } catch (e) {}
  for (const k of D.kids) actualizarReg(k);
  resetFlow(); mostrarEquipo(false); S.capShown = false; save();
  const quien = D.actual;
  paso(() => ({ kid: quien, titulo: L("dedos.pausa.titulo"), lineas: [L("dedos.pausa.texto")], cuadro: true,
    botones: [{ t: L("dedos.pausa.seguir"), cls: "grande", go: () => jugarTurno(quien) }, { t: L("dedos.turno.terminar"), cls: "alt", go: () => final() }] }));
}
function final() {
  if (!D) return;
  const ss = S.session; if (ss) ss.cerrado = true;
  S.run++; S.mode = "idle"; S.onDone = null; try { speechSynthesis.cancel(); } catch (e) {}
  for (const k of D.kids) actualizarReg(k);
  resetFlow(); mostrarEquipo(false); S.capShown = false; save();
  const [a, b] = D.kids, piezas = D.piezas, P = D.porKid; D.fin = true;
  paso(() => ({ em: "🌟", titulo: L("dedos.fin.titulo"),
    lineas: [L("dedos.fin.texto", { piezas }), L("dedos.fin.kid", { nombre: a, n: P[a].n }), L("dedos.fin.kid", { nombre: b, n: P[b].n })],
    voz: L("dedos.fin.voz", { a, b }), cuadro: true,
    botones: [{ t: L("dedos.fin.ok"), cls: "grande", go: () => salir() }] }));
}
function salir() { D = null; PASO = null; $("btnWho").onclick(); }

/* ---- el dibujo del equipo ---- */
function sumar(n) {
  const e = equipo(D.kids[0], D.kids[1]);
  for (let i = 0; i < n; i++) {
    e.piezas++; e.total++; D.piezas++;
    if (e.piezas >= cuadroDe(e).p.length) { D.celebrar.push(cuadroDe(e).id); e.piezas = 0; e.cuadros++; }
  }
}
/* una entrada de registro por sesión y por chico: se crea con la primera respuesta (o explicación) y se actualiza sola, así no se pierde si se cierra la app */
function actualizarReg(k) {
  const P = D.porKid[k];
  if (!P.ref) {
    if (!P.n && !P.e && !P.r) return;
    P.ref = { t: Date.now(), c: otroDe(k), n: 0, ok: 0, s: 0, tr: 0, e: 0, r: 0, p: 0 };
    const l = (dd().reg[k] = dd().reg[k] || []); l.push(P.ref); if (l.length > 90) l.splice(0, l.length - 90);
  }
  Object.assign(P.ref, { n: P.n, ok: P.ok, s: segundos(k), tr: P.turnos, e: P.e, r: P.r, p: D.piezas });
}

/* ---- informe para adultos (cada chico ve SUS sesiones de a dos) ---- */
function informe(kid) {
  const l = (dd().reg[kid] || []); if (!l.length) return [];
  const out = [L("dedos.informe.titulo"), L("dedos.informe.resumen", { n: l.length })];
  l.slice(-8).forEach(e => {
    out.push(L("dedos.informe.fila", { fecha: Gioval.i18n.fecha(new Date(e.t)), compa: e.c, n: e.n, ok: e.ok, min: Math.round(e.s / 60), tr: e.tr, p: e.p }));
    if (e.e) out.push(L("dedos.informe.explico", { compa: e.c, n: e.e }));
    if (e.r) out.push(L("dedos.informe.escucho", { compa: e.c, n: e.r }));
  });
  return out;
}

/* ---- si cambia el idioma con una pantalla de este modo a la vista, se vuelve a dibujar (sin volver a hablar) ---- */
Gioval.on("idioma", d => {
  if (!d || !d.cambio) return;
  const a = document.querySelector(".screen.active"); if (!a) return;
  if (a.id === "ddSetup") pintarSetup(); else if (a.id === "ddPaso") pintarPaso(); else if (a.id === "act") pintarEquipo();
});

Gioval.modos = Gioval.modos || [];
Gioval.modos.push({ id: "dedos", em: "👫", get nombre() { return L("dedos.nombre"); }, get sub() { return L("dedos.sub"); },
  visible: () => store.profiles.length >= 2 && islasElegibles().length > 0, go: () => abrirSetup(), informe });
/* para las pruebas y las herramientas de depuración */
Gioval.dedos = { AJ, CUADROS, estado: () => D, equipo, informe, restante, islasElegibles, proponerExplicacion: k => D && proponerExplicacion(k), datos: dd };
})();
