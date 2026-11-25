"use strict";
/* RESERVADO — detector de golpes / ritmo (palmas, percusión).
   Todavía no hay implementación. Cuando se haga: registrar un proveedor
     Gioval.entrada.registrarProveedor({ id:"golpes", tipos:["golpe"], disponible(), activo, iniciar(opts), detener() })
   que escuche el micrófono por ENERGÍA (onsets de volumen, no de altura) y emita
     Gioval.entrada.emitir({ tipo:"golpe", t, fuerza })
   Debe compartir el permiso/stream del micrófono con js/core/entrada/microfono.js en vez de abrir otro.
   Pensado para: ritmo, palmas, tambor, percusión. Ver docs/ENTRADAS_Y_SONIDO.md. */
