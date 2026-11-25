"use strict";
/* Utilidades chicas y espacio de nombres compartido (Gioval).
   Scripts clásicos (sin módulos, sin build): lo que se declara con let/const/function al nivel superior
   queda visible para los demás archivos; lo "público" cuelga de window.Gioval. */
window.Gioval = window.Gioval || { datos: {} };
Gioval.espacio = (self.GIOVAL_ESPACIO || "");                   /* "" en producción; ver js/version.js */
Gioval.clave = n => Gioval.espacio ? n + "_" + Gioval.espacio : n;   /* nombre de una clave de localStorage dentro del espacio */
/* bus de eventos mínimo: Gioval.on("menu", fn) / Gioval.emit("menu", datos) */
Gioval._ev = {};
Gioval.on = (n, f) => { (Gioval._ev[n] = Gioval._ev[n] || []).push(f); };
Gioval.emit = (n, d) => { (Gioval._ev[n] || []).forEach(f => { try { f(d); } catch (e) { console.error(e); } }); };

const $ = id => document.getElementById(id);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = a => a[Math.floor(Math.random() * a.length)];
const shuffle = a => a.map(x => [Math.random(), x]).sort((p, q) => p[0] - q[0]).map(p => p[1]);
const R = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
const range = (a, b) => { const r = []; for (let i = a; i <= b; i++) r.push(i); return r; };
const LASTP = {};
/* elige un elemento distinto del último que se eligió con la misma clave */
function pick(arr, key) { let x, g = 0; do { x = rnd(arr); g++; } while (arr.length > 1 && x === LASTP[key] && g < 12); LASTP[key] = x; return x; }
const today = () => new Date().toLocaleDateString("en-CA");
const DAY = 864e5;
