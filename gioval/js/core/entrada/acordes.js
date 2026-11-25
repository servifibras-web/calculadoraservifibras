"use strict";
/* RESERVADO — detector de acordes (cromagrama).
   Todavía no hay implementación. Cuando se haga: registrar un proveedor
     Gioval.entrada.registrarProveedor({ id:"acordes", tipos:["acorde"], disponible(), activo, iniciar(opts), detener() })
   que calcule un cromagrama (12 clases de nota) con FFT sobre el micrófono y emita
     Gioval.entrada.emitir({ tipo:"acorde", notas:[midi…], t })
   Pensado para: guitarra, ukelele, teclado con varias notas. Ver docs/ENTRADAS_Y_SONIDO.md. */
