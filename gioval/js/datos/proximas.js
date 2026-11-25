"use strict";
/* Islas que todavía no existen: aparecen en el mapa con candado. Cuando una isla nueva se registra
   (js/islas/*.js) hay que sacarla de esta lista. Los textos salen de js/i18n/<idioma>.js (proximas.*). */
Gioval.datos.proximas = [
  { emoji: "🐘", get name() { return t("proximas.animales"); }, get sub() { return t("proximas.pronto"); } },
];
