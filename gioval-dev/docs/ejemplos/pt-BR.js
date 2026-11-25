"use strict";
/* EJEMPLO de un idioma nuevo, PARCIAL (portugués de Brasil): traduce la interfaz principal y deja el resto en es-AR
   (la cadena de respaldo es pt-BR → es-AR → en). Ver docs/AGREGAR_IDIOMA.md. No se publica: está en gioval-dev/docs/ejemplos. */
Gioval.i18n.registrar("pt-BR", {
  meta: { nombre: "Portuguese (Brazil)", nombreNativo: "Português (Brasil)", dir: "ltr", locale: "pt-BR", moneda: "BRL",
    voz: ["pt-BR", "pt-PT", "pt"], notas: ["Dó","Dó#","Ré","Ré#","Mi","Fá","Fá#","Sol","Sol#","Lá","Lá#","Si"], fallback: ["es-AR"] },
  textos: {
    "app.titulo": "Mundo Gioval - Vamos brincar",
    "app.nombre": "Mundo Gioval",
    "app.a_jugar": "Vamos brincar!",
    "app.quien_juega": "Quem vai brincar?",
    "app.nuevo_jugador": "Novo jogador",
    "app.mapa_titulo": "Mundo Gioval · Vamos brincar, {nombre}!",
    "app.hola_mapa": "Oi {nombre}! Para qual ilha vamos?",
    "menu.sesion": "Sessão de hoje",
    "menu.logros": "Minhas conquistas",
    "menu.chequeo": "Revisão semanal",
    "menu.chequeo_dias": "Disponível em {n, plural, one{# dia} other{# dias}}",
    "musica.nombre": "Ilha da Música",
    "musica.sub": "Vamos tocar piano!",
    "numeros.nombre": "Ilha dos Números",
    "numeros.sub": "Vamos contar e somar!",
  }
});
