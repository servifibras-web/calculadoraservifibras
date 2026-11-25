"use strict";
/* Proveedor "toque": lo que se toca en la pantalla (teclas del piano, botones). Siempre disponible. */
Gioval.entrada.registrarProveedor({
  id: "toque", tipos: ["toque"], activo: true,
  disponible() { return true; }, iniciar() { return Promise.resolve(); }, detener() {},
  /* la interfaz llama a pulsar({midi, tecla, x, y}) y se emite un evento "toque" */
  pulsar(datos) { Gioval.entrada.emitir(Object.assign({ tipo: "toque", fuerza: 1 }, datos || {})); },
});
