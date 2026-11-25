importScripts("js/version.js");
/* La versión sale de js/version.js (una sola constante). Para sumar un archivo de la app: agregalo a F. */
/* P = prefijo de TODAS las cachés de esta copia de la app. En producción "gioval-"; una copia de prueba con otro
   GIOVAL_ESPACIO usa "gioval@<espacio>-" y no toca (ni borra) las cachés de la versión real. */
const P=self.GIOVAL_ESPACIO?"gioval@"+self.GIOVAL_ESPACIO+"-":"gioval-";
const C=P+self.GIOVAL_VERSION;
const CA=P+"audio-";   /* audio de voz por idioma: una caché por idioma, fuera de la precarga (se guarda solo el del idioma elegido) */
const F=["./","index.html","manifest.json","apple-touch-icon.png","icon-192.png","icon-512.png","icon-maskable.png","css/app.css","css/letras.css",
  "js/version.js",
  "js/core/util.js",
  "js/i18n/i18n.js",
  "js/i18n/es-AR.js",
  "js/i18n/es-419.js",
  "js/i18n/es-ES.js",
  "js/i18n/en.js",
  "js/i18n/pseudo.js",
  "js/core/voz.js",
  "js/core/audio.js",
  "js/core/sonido.js",
  "js/core/almacen.js",
  "js/core/alarma.js",
  "js/core/alarma_nativa.js",
  "js/core/envoltorio.js",
  "js/core/entrada/entrada.js",
  "js/core/entrada/toque.js",
  "js/core/entrada/microfono.js",
  "js/core/entrada/golpes.js",
  "js/core/entrada/acordes.js",
  "js/core/entrada/midi.js",
  "js/core/actividades.js",
  "js/core/motor.js",
  "js/core/dominio.js",
  "js/core/ui.js",
  "js/core/adultos.js",
  "js/datos/proximas.js",
  "js/datos/tareas.js",
  "js/datos/letras.js",
  "js/datos/numeros.js",
  "js/datos/misiones.js",
  "js/datos/ritmo.js",
  "js/islas/musica.js",
  "js/islas/numeros_ubicacion.js",
  "js/islas/numeros.js",
  "js/islas/letras.js",
  "js/islas/ayudantes.js",
  "js/islas/misiones.js",
  "js/islas/ritmo.js",
  "js/islas/dedos.js"];
/* instalar: precargar todo SIN activarse solo; la página avisa "hay una versión nueva" y al tocar Actualizar manda {tipo:"saltar"} */
self.addEventListener("install",e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x.startsWith(P)&&x!==C&&!x.startsWith(CA)).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener("message",e=>{
  const d=e.data||{};
  if(d.tipo==="saltar")self.skipWaiting();
  /* la página avisa qué idioma eligió: se guarda en caché el audio de ESE idioma y se borra el de los demás */
  if(d.tipo==="audio"&&d.codigo)e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(x=>x.startsWith(CA)&&x!==CA+d.codigo).map(x=>caches.delete(x))))
    .then(()=>d.urls&&d.urls.length?caches.open(CA+d.codigo).then(c=>Promise.all(d.urls.map(u=>c.add(u).catch(()=>{})))):null));
});
/* red primero (siempre la versión más nueva) y la caché como respaldo sin conexión */
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET")return;
  const m=/\/audio\/([^/]+)\//.exec(new URL(e.request.url).pathname);
  const destino=m?CA+decodeURIComponent(m[1]):C;   /* el audio va a la caché de su idioma */
  e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(destino).then(c=>c.put(e.request,cp))}return r}).catch(()=>caches.match(e.request,{ignoreSearch:true})))});
self.addEventListener("notificationclick",e=>{e.notification.close();e.waitUntil(self.clients.matchAll({type:"window"}).then(l=>l.length?l[0].focus():self.clients.openWindow("./")))});
