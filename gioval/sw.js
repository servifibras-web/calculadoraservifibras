importScripts("js/version.js");
/* La versión sale de js/version.js (una sola constante). Para sumar un archivo de la app: agregalo a F. */
const C="gioval-"+self.GIOVAL_VERSION;
const F=["./","index.html","manifest.json","apple-touch-icon.png","icon-192.png","icon-512.png","icon-maskable.png","css/app.css",
  "js/version.js",
  "js/core/util.js",
  "js/core/voz.js",
  "js/core/audio.js",
  "js/core/sonido.js",
  "js/core/almacen.js",
  "js/core/alarma.js",
  "js/core/entrada/entrada.js",
  "js/core/entrada/toque.js",
  "js/core/entrada/microfono.js",
  "js/core/entrada/golpes.js",
  "js/core/entrada/acordes.js",
  "js/core/entrada/midi.js",
  "js/core/actividades.js",
  "js/core/motor.js",
  "js/core/ui.js",
  "js/core/adultos.js",
  "js/datos/proximas.js",
  "js/datos/tareas.js",
  "js/islas/musica.js",
  "js/islas/numeros.js",
  "js/islas/ayudantes.js"];
/* instalar: precargar todo SIN activarse solo; la página avisa "hay una versión nueva" y al tocar Actualizar manda {tipo:"saltar"} */
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener("message",e=>{if(e.data&&e.data.tipo==="saltar")self.skipWaiting()});
/* red primero (siempre la versión más nueva) y la caché como respaldo sin conexión */
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET")return;
  e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request,{ignoreSearch:true})))});
self.addEventListener("notificationclick",e=>{e.notification.close();e.waitUntil(self.clients.matchAll({type:"window"}).then(l=>l.length?l[0].focus():self.clients.openWindow("./")))});
