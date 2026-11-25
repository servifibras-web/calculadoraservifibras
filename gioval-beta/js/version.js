/* Versión de Mundo Gioval. Es la ÚNICA constante de versión:
   la usan sw.js (nombre de la caché, vía importScripts) y la página (aviso de versión nueva, panel de adultos).
   Subila cada vez que publiques cambios; así los celulares detectan que hay algo nuevo. */
self.GIOVAL_VERSION = "8";
/* Espacio de datos. En producción va vacío. Una COPIA DE PRUEBA de la app que se sirva desde el mismo sitio (por ejemplo
   /gioval-beta/) debe poner acá otro nombre ("beta"): así usa su propio localStorage, su propia base IndexedDB, su propia
   alarma y su propia caché, y no mezcla ni pisa los datos de los chicos de la versión real. */
self.GIOVAL_ESPACIO = "beta";
