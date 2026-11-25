# Copia de prueba (por ejemplo /gioval-beta/)

Una copia de `gioval/` servida desde el mismo sitio comparte el almacenamiento del navegador con la versión real (mismo origen):
`localStorage`, `IndexedDB` y cachés se llaman igual. Para que la copia **no vea ni pise los datos de los chicos**, hay un
interruptor en `js/version.js`:

```js
self.GIOVAL_ESPACIO = "beta";   // en producción va vacío: ""
```

Con un espacio, la copia usa sus propias claves: `localStorage` `gioval_beta` (y `gioval_alarma_beta`, `gioval_idioma_beta`, `gioval_voz_<idioma>_beta`),
la base `gioval-db-beta` y las cachés `gioval@beta-<versión>`; su service worker no borra las cachés de la versión real y viceversa.
La copia arranca vacía; para probar con datos reales, exportar un respaldo en la real y **Restaurar** en la copia.
Hay una prueba automática ("espacio de datos").
