"use strict";
/* ============ ENTRADAS (proveedores enchufables) ============
   Las actividades NO hablan con el micrófono ni con la pantalla: piden "qué tipo de entrada necesito" a este registro
   y escuchan eventos con formato común:
     { tipo:"nota",   midi, t, fuerza }          una nota detectada (micrófono, MIDI)
     { tipo:"golpe",  t, fuerza }                un golpe/palmada/percusión (ritmo)
     { tipo:"acorde", notas:[midi…], t }         varias notas a la vez (cromagrama, MIDI)
     { tipo:"toque",  midi?, tecla?, x?, y?, t } un toque en pantalla (el que traiga datos de la isla)
   t = performance.now() (ms). fuerza va de 0 a 1.
   Un PROVEEDOR es un objeto { id, tipos:["nota"], disponible():bool, activo:bool, iniciar(opts):Promise, detener() }
   y se registra con Gioval.entrada.registrarProveedor(p). Los proveedores emiten con Gioval.entrada.emitir(ev).
   Una isla declara { instrumento:"piano", entradas:["nota","toque"] } al registrarse.
   Ver docs/ENTRADAS_Y_SONIDO.md. */
Gioval.entrada = (function () {
  const E = { proveedores: {}, _subs: {} };
  E.registrarProveedor = p => { E.proveedores[p.id] = p; return p; };
  E.suscribir = (tipo, cb) => { (E._subs[tipo] = E._subs[tipo] || []).push(cb); return () => { E._subs[tipo] = (E._subs[tipo] || []).filter(f => f !== cb); }; };
  E.emitir = ev => { if (ev.t == null) ev.t = performance.now(); (E._subs[ev.tipo] || []).slice().forEach(f => { try { f(ev); } catch (e) { console.error(e); } }); (E._subs["*"] || []).slice().forEach(f => { try { f(ev); } catch (e) { console.error(e); } }); };
  /* qué proveedores pueden dar un tipo de evento */
  E.quien = tipo => Object.values(E.proveedores).filter(p => p.tipos.includes(tipo));
  /* "qué tipo de entrada necesito": devuelve { disponibles:[tipos con proveedor utilizable], faltan:[tipos sin proveedor] } */
  E.necesito = tipos => {
    const d = [], f = [];
    (tipos || []).forEach(t => (E.quien(t).some(p => p.disponible()) ? d : f).push(t));
    return { disponibles: d, faltan: f };
  };
  return E;
})();
