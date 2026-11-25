# Isla Números por edades (Fase 1)

Esta isla pasa de 9 a **31 habilidades** ordenadas desde los 4 años, con un **punto de partida** que carga un adulto, un
**test de ubicación** jugable y **salto por dominio rápido**. Todo lo que se puede editar está en datos (no en la lógica).

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Habilidades, ejes, preguntas al adulto, umbrales de tiempo, textos (`TEXTOS`) | `gioval/js/datos/numeros.js` (`Gioval.datos.numeros`) |
| Actividades de toque nuevas (15 tipos) y registro de la isla | `gioval/js/islas/numeros.js` (las 9 de la v1 no se tocaron) |
| Punto de partida, escalera del test, pantallas del adulto, informe de la isla | `gioval/js/islas/numeros_ubicacion.js` (`Gioval.numeros`) |
| Dominio rápido, saltos, reevaluación, sesiones guiadas (**genérico, no nombra ninguna isla**) | `gioval/js/core/dominio.js` (`Gioval.dominio`) |
| Migración v1 → v2 (`store.intake`) | `gioval/js/core/almacen.js` |

## La escalera

`ESCALA` en `datos/numeros.js`. Cada habilidad lleva `eje`, `edad` (orientativa), `nap` (de dónde sale) y
`rapido:{rt,salta}`. Los ejes (`EJES`) son: **A** serie y conteo, **B** comparar y ordenar, **C** sumas y restas,
**D** valor posicional, **E** dobles, grupos y repartos. Los ids `num_c10 … num_r20` de la v1 no cambian (el progreso de los
chicos se conserva). Los comentarios dicen qué se verificó con NAP Primer Ciclo y Progresiones de los aprendizajes (CABA)
y qué está marcado **"a revisar"**. Lo de Nivel Inicial **no se verificó contra el documento original**.

Para sumar o mover una habilidad: agregala a `ESCALA` (después de sus requisitos), a la `cadena` de su eje y, si hace falta, a
alguna respuesta de `INTAKE`. La prueba "Números (datos)" valida requisitos, ejes, actividades, textos y que no se use
lenguaje prohibido (elogio a la inteligencia, rachas, tuteo).

## Preguntas iniciales (`store.intake[niño]`)

Panel de adultos ⚙️ → **Punto de partida (Números)**. Son 6 listas: edad, hasta dónde cuenta, hasta dónde reconoce, suma,
resta, multiplicar. Cada opción trae `domina`: las habilidades que afirma. Con **"No sé"** se usa el `defecto` de la edad
(conservador). Se guarda `{v:1, edad, resp, ubicacion?, inicio?, pendiente?}`. Nada cambia en el progreso hasta que el adulto
toca **Aceptar** en el resumen, donde puede ajustar habilidad por habilidad.

### Regla del punto de partida (estados)
- **saltada**: se marca dominada (para destrabar lo siguiente) pero con `skip` y sin práctica propia.
- **en curso**: la "punta" de cada rama (lo último que el adulto dice que sabe): no se salta; se practica con menos ayuda
  (`lvl` 1). También lo es todo lo que el test aprobó **despacio**.
- **no**: abierta si sus requisitos están saltados; si no, cerrada hasta que lo anterior se domine.
- Una habilidad solo puede estar saltada o en curso si **todos sus requisitos están saltados** (el plan lo garantiza al
  cerrar por requisitos; el resumen suelta las dependientes al desmarcar una base).

## Test de ubicación

Desde el resumen → **Hacer el test de ubicación**. Es una sesión guiada (`Gioval.dominio.iniciarGuiada`): usa los mismos
ítems de toque, con voz, no toca habilidades, registro ni días. Escalera por eje, empezando donde dijo el adulto:
2 aciertos aprueban, 2 errores fallan, si hay 1 y 1 va un 3.er ítem; sube un nivel al aprobar, baja con pasos crecientes al
fallar. Topes en `UBICACION`: 10 ítems por eje, 30 en total, 5 minutos (cierra al terminar el ítem en curso). **Seguir ➜**
cuenta como "no sé". Una aprobación con tiempo de respuesta lento queda **en curso**, no saltada. Al terminar, el niño
escucha que sigue un adulto; el adulto ve el resumen (lo que dijo vs. lo que se vio), lo ajusta y acepta.

## Salto por dominio rápido (genérico)

Ver la cabecera de `js/core/dominio.js`. Resumen: en los últimos 10 intentos, ≥6 intentos, ≥90 % al primer intento y mediana
del tiempo de respuesta (`rt`, medido desde que termina la voz hasta el acierto, solo ítems sin errores) bajo `rapido.rt`.
Entonces se saltean las `rapido.salta` (poco practicadas, requisitos dominados). En el **chequeo semanal sin ayuda** las
saltadas reciben 3 ítems: ≥2/3 las confirma (y confirma sus bases por implicación); si no, **vuelven atrás** junto con las
que dependen de ellas. Una isla lo activa solo con datos (`rapido`), sin código.

## Informe de adultos

Sección "PUNTO DE PARTIDA — ISLA NÚMEROS" (edad, respuestas, test, qué se saltó), por habilidad: aciertos al primer
intento, retención (≥1 día), mediana del tiempo, y "HABILIDADES SALTADAS (sin práctica propia) Y POR QUÉ" con la evidencia y
el estado (pendiente / confirmada / volvió a práctica).

## Ganchos genéricos que se agregaron (para otras islas)

- `skill.rapido = {rt, salta[]}` y `skill.skip` en el progreso (`SK`).
- `PACK.informeInicio(kid)` → líneas extra al principio del informe.
- `Gioval.emit("panel", kid)` al abrir el panel, y `panelPie` para agregar contenido.
- `Gioval.dominio.iniciarGuiada({titulo, saludo, guia:{siguiente, respuesta}})` para sesiones propias de la isla.
- El motor de toques entrega `rt` y `aid` a `S.onDone` y se guardan en el registro (`log[].rt`, `log[].a`).
- Almacén v2: `store.intake`.

## Parámetros a revisar con datos reales

`Gioval.dominio.params` (ventana, mínimo de intentos/aciertos, ítems de chequeo por saltada, tope por chequeo), cada
`rapido.rt` por habilidad, `UBICACION` y los `defecto` por edad en `INTAKE`. Los umbrales de tiempo son estimaciones para
chicos de 4 a 8 años: ajustalos mirando el informe después de unas semanas de uso.
