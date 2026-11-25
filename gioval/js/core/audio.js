"use strict";
/* ============ AUDIO (Web Audio: sonidos generados, sin archivos) ============ */
let ctx=null;
function ensureCtx(){
  if(!ctx){ const AC=window.AudioContext||window.webkitAudioContext; ctx=new AC(); }
  if(ctx.state==="suspended") ctx.resume();
  return ctx;
}
/* tone() y los instrumentos están en js/core/sonido.js */
