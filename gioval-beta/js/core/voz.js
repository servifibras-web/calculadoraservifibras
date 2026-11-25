"use strict";
/* ============ VOZ ============ */
let voiceOn=true, muteUntil=0; /* muteUntil: la escucha del micrófono (si la isla la usa) se silencia mientras habla la app */
function voiceReady(){ return voiceOn&&!!window.speechSynthesis; }
let esVoice=null;
function pickVoice(){
  const vs = (window.speechSynthesis && speechSynthesis.getVoices())||[];
  const es = vs.filter(v=>/^es/i.test(v.lang));
  esVoice = es.find(v=>/AR/i.test(v.lang)) || es.find(v=>/MX|US|419/i.test(v.lang)) || es[0] || null;
}
if(window.speechSynthesis){ pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; }
function setBubble(t){ $("bubble").textContent = t; }
function speak(text){
  setBubble(text);
  const est = 500 + text.length*85;
  muteUntil = performance.now() + est + 400;
  if(!voiceOn || !window.speechSynthesis) return sleep(Math.min(est,1400));
  return new Promise(res=>{
    let done=false; const fin=()=>{ if(!done){done=true; muteUntil=performance.now()+350; res();} };
    try{
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = esVoice?esVoice.lang:"es-AR"; if(esVoice) u.voice=esVoice;
      u.rate=.92; u.pitch=1.25;
      u.onend=fin; u.onerror=fin;
      speechSynthesis.speak(u);
    }catch(e){ fin(); }
    setTimeout(fin, est+1500);
  });
}
