"use strict";
/* RESERVADO — Web MIDI (teclado digital por USB; funciona en Chrome para Android con cable OTG).
   Todavía no hay implementación. Cuando se haga: registrar un proveedor
     Gioval.entrada.registrarProveedor({ id:"midi", tipos:["nota","acorde"], disponible(){ return !!navigator.requestMIDIAccess; }, … })
   que use navigator.requestMIDIAccess() y emita "nota" por cada noteOn ({ tipo:"nota", midi, t, fuerza: velocity/127 }),
   y "acorde" si llegan varias notas casi juntas. Ver docs/ENTRADAS_Y_SONIDO.md. */
