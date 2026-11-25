# Mundo Gioval como app de Android (con alarma de verdad)

Esta guía es para vos, Marcos: cómo conseguir la app, instalarla en los celulares y tablets de los chicos, y dejarla lista para que la alarma suene **aunque la pantalla esté apagada o la app cerrada**. Al final hay una parte técnica, corta, para quien programe.

## Qué es y para qué sirve

Es la misma Mundo Gioval de siempre, pero empaquetada como una app de Android que se instala con un archivo `.apk`. La ventaja: la **alarma del sistema**. En la versión web (la que se abre desde el navegador), si el teléfono se bloquea, el navegador "congela" la página y la alarma puede no sonar. En la app de Android, la alarma la programa el propio sistema operativo: suena con la pantalla apagada, enciende la pantalla, vibra y muestra un botón grande para cortarla.

Lo que **no** cambia: los juegos, el progreso y todo lo demás son exactamente los de la versión web. Si más adelante publicamos una versión nueva de la web, hay que armar un APK nuevo (ver "Cómo se actualiza").

> **Ojo con los datos.** El progreso de los chicos se guarda *dentro de cada app*. La app de Android empieza vacía: no ve lo que hay en la versión web del navegador. Para pasar el progreso: en la versión web, panel de adultos (la ruedita ⚙️) → **Exportar respaldo**; en la app, panel de adultos → **Restaurar**.

## Qué se probó y qué no (leer antes de confiar)

- **Probado automáticamente:** que en el navegador nada cambia, que la app habla bien con el plugin nativo (con uno simulado), el botón "atrás", y que la receta de GitHub Actions es válida.
- **NO se pudo probar sin un aparato Android:** que el sonido suene de verdad con la pantalla apagada, la vibración, la pantalla sobre el bloqueo y la reprogramación tras reiniciar. El código está hecho con las herramientas oficiales de Android, pero **hay que probarlo en un aparato real** antes de depender de él (ver "Probar que la alarma funciona", más abajo). Cada marca de celular tiene sus ahorros de batería, y ahí es donde suelen fallar las alarmas.

## 1. Conseguir el APK (GitHub Actions)

El APK lo arma GitHub solo, en sus servidores. No hace falta instalar nada en tu computadora.

1. Entrá al repositorio en GitHub y abrí la pestaña **Actions**.
2. En la lista de la izquierda, elegí **APK Android**.
3. Dos maneras de que se arme:
   - **Automática:** cada vez que se actualiza la rama `android-envoltorio` se arma un APK solo. Abrí la corrida más reciente (la de arriba de todo).
   - **A mano:** botón **Run workflow** → elegí la rama → en "Qué app armar" elegí **normal** (la de todos los días) o **beta** (copia de prueba) → **Run workflow**. *(Este botón aparece cuando el archivo `.github/workflows/apk.yml` está en la rama principal del repositorio.)*
4. Esperá unos 5 a 10 minutos hasta que aparezca una tilde verde. Si aparece una cruz roja, algo falló: avisale a quien programa y pasale el link de la corrida.
5. Entrá a la corrida y bajá hasta **Artifacts** (al final de la página). Descargá **mundo-gioval-debug** (o **mundo-gioval-beta-debug** si armaste la beta). Baja un `.zip`: descomprimilo y adentro está el `.apk`.

> Para descargar hay que estar con tu usuario de GitHub. Lo más cómodo es bajarlo desde la computadora y pasarlo al celular por WhatsApp (a vos mismo), Google Drive, mail o cable USB.

**Normal vs beta.** La **normal** es "Mundo Gioval". La **beta** se instala como **otra app aparte** ("Mundo Gioval BETA", con la cinta roja en el ícono y en la pantalla): tiene sus propios datos y no toca los de los chicos. Sirve para probar cosas nuevas sin riesgo.

## 2. Instalarla en el celular o la tablet

1. Pasá el archivo `.apk` al aparato y abrilo desde la app **Archivos** (o **Descargas**), o tocalo en WhatsApp / Drive.
2. Android va a decir que **no puede instalar apps de esta fuente**. Tocá **Ajustes** y activá **Permitir de esta fuente** (o "Instalar apps desconocidas") para la app desde la que abriste el archivo (Archivos, Chrome, WhatsApp, Drive…). Volvé atrás.
3. Tocá **Instalar**.
4. Si aparece un cartel de **Play Protect** ("app no verificada" / "bloqueada por Play Protect"): tocá **Más detalles** → **Instalar de todos modos**. Es normal: la app no está en Google Play.
5. Abrila. La primera vez Android puede pedir permiso para el **micrófono** (lo usan los juegos de notas y de golpes) y para **enviar notificaciones**: aceptá los dos.

## 3. Dejar la alarma lista (hacerlo una vez en cada aparato)

Entrá al **panel de adultos** de la app (ruedita ⚙️ arriba a la derecha → respondé la multiplicación). Abajo vas a ver la sección **"⏰ Alarma del teléfono (app Android)"**, que te dice qué falta con ✅ y ⚠️ y tiene un botón para cada cosa:

| Qué | Para qué | Cómo |
|---|---|---|
| **Avisos permitidos** | Que la alarma pueda mostrar el cartel en pantalla. | Botón **Permitir** → **Permitir**. |
| **Alarmas exactas** | Que suene a la hora justa y no unos minutos tarde (Android 12 o más nuevo). | Botón **Permitir** → activá **Permitir alarmas y recordatorios** para Mundo Gioval. En Android 13 o más nuevo ya viene dado. |
| **Pantalla sobre el bloqueo** | Que la alarma encienda la pantalla y muestre el botón grande (Android 14 o más nuevo). Solo aparece si falta. | Botón **Abrir ajustes** → activá **Notificaciones a pantalla completa**. |
| **Sin restricción de batería** | Que el ahorro de batería no duerma la app. **Es lo que más suele fallar.** | Botón **Abrir ajustes** y seguí el paso de tu marca (abajo). |

También conviene saber:

- La alarma suena con el volumen de **"Alarmas"** del teléfono, que es distinto del volumen de música y del de timbre. Revisalo en **Ajustes → Sonido → Volumen**. Si está en cero, suena en silencio (solo vibra).
- Con **No molestar** activado, normalmente las alarmas igual suenan, pero algunas marcas lo cambian. Revisalo en la prueba.

### Batería, marca por marca

Los nombres de los menús cambian según el modelo y la versión de Android. La idea es siempre la misma: ponerle a Mundo Gioval **"Sin restricciones"** / **"Sin optimizar"** / **"No ahorrar batería"**.

- **Samsung:** Ajustes → Aplicaciones → **Mundo Gioval** → Batería → **Sin restricciones**. Además: Ajustes → Cuidado del dispositivo (o Batería) → Batería → **Límites de uso en segundo plano** → sacá a Mundo Gioval de "Apps en suspensión" y "Apps en suspensión profunda".
- **Motorola:** Ajustes → Aplicaciones → **Mundo Gioval** → Batería → **Sin restricciones** (a veces dice "Sin optimizar").
- **Xiaomi / Redmi / POCO:** Ajustes → Aplicaciones → Administrar aplicaciones → **Mundo Gioval** → Ahorro de batería → **Sin restricciones**. Y en la misma pantalla activá **Inicio automático** y, en Otros permisos, **Mostrar en la pantalla de bloqueo** y **Mostrar ventanas emergentes mientras se ejecuta en segundo plano**.
- **Huawei / Honor:** Ajustes → Batería → **Inicio de aplicaciones** → **Mundo Gioval** → pasá a **Administrar manualmente** y activá las tres opciones (inicio automático, inicio secundario y ejecución en segundo plano).
- **OPPO / Realme / OnePlus:** Ajustes → Batería → (Más ajustes) → **Mundo Gioval** → permitir **actividad en segundo plano** y **inicio automático**. En Ajustes → Aplicaciones → Mundo Gioval → Uso de batería → **Permitir**.
- **Pixel / Android "puro" / tablets en general:** Ajustes → Aplicaciones → **Mundo Gioval** → Batería (Uso de batería de la app) → **Sin restricciones**.
- **Otra marca:** buscá en Ajustes "batería" o "optimización" y fijate que Mundo Gioval no esté restringida. Un buen sitio con instrucciones por marca es *dontkillmyapp.com*.

### Probar que la alarma funciona

En el panel de adultos, sección "Alarma del teléfono", tocá **🔔 Probar alarma (10 segundos)**. Después **bloqueá el teléfono** (botón de encendido) y esperá. A los 10 segundos tiene que:

1. Sonar la alarma (aunque tengas la app cerrada: probalo también cerrándola desde "Recientes"),
2. Encender la pantalla con "¡Prueba de alarma!" y un botón grande **¡Listo!**,
3. Dejar de sonar al tocar **¡Listo!** (o **Parar** en el aviso). Si nadie la toca, se corta sola al minuto y deja un aviso en la barra.

Si no suena: revisá la tabla de arriba (sobre todo batería y volumen de alarmas) y repetí la prueba. Si en un modelo no hay caso, anotá marca y modelo y avisá.

**Qué pasa si la app está abierta y a la vista cuando se cumple la hora:** suena la alarma de la propia app (como siempre) y la del sistema se calla para que no suenen dos a la vez.

## 4. Cómo se actualiza

1. Cuando haya una versión nueva de la app, armá un APK nuevo (paso 1). Cada APK nuevo lleva un número de compilación más alto.
2. Instalalo **encima** del anterior (mismos pasos que la instalación). **No hace falta desinstalar y no se pierde el progreso**, porque todos los APK se firman con la misma clave (`gioval-debug.keystore`, que está en el repositorio).
3. Solo si Android dice **"La app no se instaló" / "conflicto con un paquete existente"**: es porque la app que está instalada se armó con otra clave. Antes de desinstalarla, **Exportar respaldo** desde el panel de adultos; después instalá el APK nuevo y **Restaurar**.

La app instalada no se actualiza sola ni avisa "hay una versión nueva": la actualización es instalar el APK nuevo.

## Problemas comunes

| Síntoma | Qué probar |
|---|---|
| "No puedo instalar: bloqueada" | Permitir "instalar apps desconocidas" para la app desde la que abrís el archivo (paso 2). |
| "Play Protect bloqueó la app" | Más detalles → Instalar de todos modos. |
| La alarma suena tarde | Falta **Alarmas exactas** (ver tabla) o el ahorro de batería la durmió. |
| Suena pero no enciende la pantalla | Falta el permiso de **pantalla sobre el bloqueo** o **avisos**. |
| No suena nada pero vibra | Volumen de **Alarmas** en cero. |
| El micrófono no anda | Ajustes → Aplicaciones → Mundo Gioval → Permisos → **Micrófono: Permitir**. |
| El botón "atrás" | Va volviendo pantalla por pantalla; en la primera pantalla manda la app a segundo plano (no la cierra). |

---

# Parte técnica

## Estructura

```
gioval/                       la app web (no se compila nada). Sumó dos archivos: js/core/alarma_nativa.js y js/core/envoltorio.js
gioval-android/
  package.json                Capacitor 8 (core, android, app) — Node 22 y Java 21
  capacitor.config.json       appId ar.servifibras.gioval, webDir "www", androidScheme https
  preparar_web.py             copia gioval/ a www/ (con --espacio beta: GIOVAL_ESPACIO="beta", título y cartel BETA; falla fuerte si falta el texto esperado)
  generar_iconos.py           íconos adaptables y splash desde gioval/icon-512.png e icon-maskable.png (--beta pone la cinta roja)
  android/                    proyecto generado con `npx cap add android` y personalizado
    app/gioval-debug.keystore firma de depuración FIJA (clave pública "android"): permite actualizar encima sin perder datos
    app/src/main/java/ar/servifibras/gioval/   código nativo propio (ver abajo)
.github/workflows/apk.yml     arma el APK y lo sube como artefacto
```

`www/` y los assets copiados dentro de `android/` se generan en cada compilación y no se commitean.

## Alarma: cómo funciona

**Web (sin cambios).** `js/core/alarma.js` guarda la hora absoluta de fin y la revisa al volver a primer plano, como siempre. En un navegador o en la PWA `alarma_nativa.js` no hace nada (ni cambia funciones): lo comprueba la prueba "el puente NO cambia nada".

**Puente (`alarma_nativa.js`).** Si existe `Capacitor.Plugins.GiovalAlarma`, envuelve `Alarma.programar`, `cancelar` y `pedirPermiso`: después de la lógica web llama al plugin con la hora absoluta (`fin` en milisegundos). Además:
`window.Notification` pasa a reflejar el permiso nativo (así el panel de Ayudantes muestra el estado real); mantiene la pantalla encendida mientras hay una actividad (`.screen.juego.active`) o una alarma corriendo; y suma la sección del panel de adultos. No se registra ningún `onFin` propio a propósito: `alarma.js` entrega una alarma vencida *al primer oyente que se registre*, y ese tiene que ser el de la isla.

**Plugin (`GiovalAlarmaPlugin.java`, nombre JS `GiovalAlarma`).**

| Método | Qué hace |
|---|---|
| `programar({id, fin, titulo, texto})` | `AlarmManager.setExactAndAllowWhileIdle` (o `setAndAllowWhileIdle`, no exacta, si falta el permiso). Devuelve `{exacta}`. Guarda la alarma en `SharedPreferences` para reprogramar. |
| `cancelar({id})` | Cancela la alarma del sistema, la borra del registro y corta el sonido. |
| `detener()` | Corta el sonido sin tocar las alarmas pendientes. |
| `estado()` | `sdk`, `exacta`, `notificaciones`, `permisoNotificaciones`, `pantallaCompleta`, `sinRestriccionBateria`. |
| `pedirNotificaciones()` | Pide `POST_NOTIFICATIONS` (Android 13+). |
| `abrirAjustes({tipo})` | `exacta`, `bateria`, `notificaciones`, `pantallaCompleta` o `app`; si el fabricante no tiene esa pantalla, abre la ficha de la app. |
| `mantenerPantalla({activo})` | `FLAG_KEEP_SCREEN_ON` de la ventana. |

**Cuando llega la hora:** `AlarmaReceiver` → si la app está a la vista (`Estado.primerPlano`, entre `onResume` y `onPause` de `MainActivity`) no hace nada (suena la web). Si no: `AlarmaServicio` (servicio en primer plano, tipo `mediaPlayback`) toca el tono de alarma del sistema en bucle con `USAGE_ALARM`, vibra, toma un `WakeLock` parcial y muestra un aviso con `fullScreenIntent` a `AlarmaActivity` (sobre el bloqueo, botón **¡Listo!**) y acción **Parar**. Se corta al minuto (deja un aviso), al tocar Parar / Listo, o al abrir la app (`MainActivity.onResume`).
Si no se puede iniciar el servicio, cae a un aviso con sonido de alarma del sistema (canal `gioval_alarma_aviso`).

**Reinicio y cambios de hora.** `ArranqueReceiver` (`BOOT_COMPLETED`, `MY_PACKAGE_REPLACED`, `TIME_SET`, `TIMEZONE_CHANGED`, cambio del permiso de alarmas exactas) reprograma lo pendiente. Lo que venció hace menos de 30 minutos se avisa con una notificación (desde el arranque Android no deja iniciar un servicio `mediaPlayback`); lo más viejo se descarta. Además `alarma.js` recalcula al abrir la app.

**Por qué `setExactAndAllowWhileIdle` y no `setAlarmClock`.** `setAlarmClock` es más inmune al ahorro de energía, pero el sistema muestra el ícono y el "próximo despertador" como si fuera una alarma de despertarse, y un temporizador de tarea de un chico no lo es. Si en las pruebas reales se ve que Doze la atrasa, cambiar a `setAlarmClock` en `AlarmaProgramador.armar` es un cambio de una línea.

## Permisos del manifiesto

`INTERNET`; `RECORD_AUDIO` y `MODIFY_AUDIO_SETTINGS` (micrófono; el WebView de Capacitor pide el permiso en tiempo de ejecución la primera vez); `POST_NOTIFICATIONS` (13+); `SCHEDULE_EXACT_ALARM` (solo hasta Android 12L, `maxSdkVersion=32`) y `USE_EXACT_ALARM` (13+, se concede al instalar); `USE_FULL_SCREEN_INTENT`; `RECEIVE_BOOT_COMPLETED`; `FOREGROUND_SERVICE` y `FOREGROUND_SERVICE_MEDIA_PLAYBACK`; `WAKE_LOCK`; `VIBRATE`. El micrófono y la pantalla táctil figuran como `required=false`.

## Android: otros detalles

- `screenOrientation="fullSensor"`: gira con el aparato (celular y tablet). `targetSdk` 36, `minSdk` 24 (Android 7).
- **Atrás** (`envoltorio.js`, plugin `@capacitor/app`): cierra el cartel abierto, después el panel de adultos, después usa el botón **⬅ Volver** de la pantalla actual (en el mapa, "Cambiar"), y en la primera pantalla llama a `minimizeApp()`. Sin un listener de `backButton`, Capacitor no haría nada al apretar atrás.
- **Sin service worker dentro del envoltorio:** `envoltorio.js` quita `navigator.serviceWorker` antes de que la app lo registre. Los archivos ya viajan en el APK y se actualizan instalando un APK nuevo; el service worker solo sumaría una capa de caché.
- Íconos: ícono adaptable (fondo `#7C4DFF` + capa de adelante con `icon-maskable.png`), ícono clásico y redondo con `icon-512.png`. Pantalla de arranque morada.
- `allowBackup="false"`: el progreso no se restaura solo por las copias de Google; se usa **Exportar / Restaurar respaldo**.

## Variante beta

`apk.yml` con `espacio = beta`: `preparar_web.py --espacio beta` pone `GIOVAL_ESPACIO = "beta"` en `js/version.js` (falla si el texto esperado no está exactamente una vez, igual que `hacer_beta.py`), título y cartel BETA; `generar_iconos.py --beta` pone la cinta roja; Gradle recibe `-PgiovalAppId=ar.servifibras.gioval.beta -PgiovalNombre="Mundo Gioval BETA"`. Al final el flujo lee el APK con `aapt2 dump badging` y falla si el id o los permisos no son los esperados.

## Compilar a mano (opcional)

Hace falta Node 22, Java 21 y el SDK de Android (plataforma 36). Desde `gioval-android/`:

```
python3 preparar_web.py            # o: --espacio beta
npm ci
npx cap sync android
cd android && ./gradlew assembleDebug -PgiovalVersionCode=1
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

Propiedades de Gradle opcionales: `giovalAppId`, `giovalNombre`, `giovalVersionCode` (tiene que crecer en cada APK; el flujo usa el número de corrida), `giovalVersionName` (el flujo usa `GIOVAL_VERSION`).

## Límites y cosas a tener en cuenta

- Una sola alarma por vez (id 7001), igual que `alarma.js`.
- El APK es de **depuración** firmado con una clave pública: sirve para instalar a mano. **No sirve para Google Play** (haría falta una clave de lanzamiento secreta, y Play tiene políticas propias para `USE_EXACT_ALARM` y `USE_FULL_SCREEN_INTENT`).
- Mientras la app está a la vista la alarma es la web; la nativa solo entra cuando la app no está a la vista.
- Si se agrega un archivo a `gioval/`, `preparar_web.py` lo copia solo; no hay lista aparte. Si se agrega un plugin de Capacitor, hay que sumarlo en `package.json` y correr `npx cap sync android`.
- Pruebas automáticas: `python3 gioval-dev/tests/correr.py "alarma nativa"` y `... "envoltorio"` (el plugin nativo se simula en JavaScript; lo que corre en Android no se prueba ahí).
