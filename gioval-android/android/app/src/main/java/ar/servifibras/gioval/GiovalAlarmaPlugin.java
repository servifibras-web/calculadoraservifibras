package ar.servifibras.gioval;

import android.Manifest;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.provider.Settings;
import android.view.WindowManager;

import androidx.core.app.NotificationManagerCompat;

import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

/**
 * Puente entre la app web (js/core/alarma_nativa.js) y la alarma del sistema.
 * En JavaScript se usa como Capacitor.Plugins.GiovalAlarma.
 *
 *   programar({ id, fin, titulo, texto })  fin = hora absoluta en milisegundos (Date.now() + duración)
 *   cancelar({ id })
 *   detener()                              corta el sonido si está sonando (no cancela alarmas pendientes)
 *   estado()                               permisos y ajustes que importan para que suene bien
 *   pedirNotificaciones()                  Android 13+: pide el permiso de avisos
 *   abrirAjustes({ tipo })                 "exacta" | "bateria" | "notificaciones" | "pantallaCompleta" | "app"
 *   mantenerPantalla({ activo })           pantalla encendida mientras se juega
 */
@CapacitorPlugin(
        name = "GiovalAlarma",
        permissions = {
                @Permission(strings = { Manifest.permission.POST_NOTIFICATIONS }, alias = "notificaciones")
        }
)
public class GiovalAlarmaPlugin extends Plugin {

    @PluginMethod
    public void programar(PluginCall call) {
        // org.json entiende número entero, decimal o texto; PluginCall.getLong solo entiende Long
        long fin = call.getData().optLong("fin", 0L);
        if (fin <= 0L) {
            call.reject("Falta fin (hora absoluta en milisegundos)");
            return;
        }
        int id = call.getData().optInt("id", 7001);
        String titulo = call.getString("titulo", "");
        String texto = call.getString("texto", "");
        boolean exacta = AlarmaProgramador.programar(getContext(), id, fin, titulo, texto);
        JSObject r = new JSObject();
        r.put("exacta", exacta);
        call.resolve(r);
    }

    @PluginMethod
    public void cancelar(PluginCall call) {
        int id = call.getData().optInt("id", 7001);
        AlarmaProgramador.cancelar(getContext(), id);
        AlarmaServicio.detener(getContext());
        call.resolve();
    }

    @PluginMethod
    public void detener(PluginCall call) {
        AlarmaServicio.detener(getContext());
        call.resolve();
    }

    @PluginMethod
    public void estado(PluginCall call) {
        call.resolve(estadoActual());
    }

    private JSObject estadoActual() {
        Context c = getContext();
        JSObject r = new JSObject();
        r.put("sdk", Build.VERSION.SDK_INT);
        r.put("exacta", AlarmaProgramador.puedeExacta(c));
        boolean avisos = NotificationManagerCompat.from(c).areNotificationsEnabled();
        r.put("notificaciones", avisos);
        // "granted" | "denied" | "prompt" (todavía no se le preguntó al usuario)
        String permiso = avisos ? "granted" : "denied";
        if (Build.VERSION.SDK_INT >= 33 && !avisos) {
            PermissionState ps = getPermissionState("notificaciones");
            if (ps == PermissionState.PROMPT || ps == PermissionState.PROMPT_WITH_RATIONALE) permiso = "prompt";
        }
        r.put("permisoNotificaciones", permiso);
        boolean pantalla = true;
        if (Build.VERSION.SDK_INT >= 34) {
            NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
            pantalla = nm != null && nm.canUseFullScreenIntent();
        }
        r.put("pantallaCompleta", pantalla);
        PowerManager pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
        r.put("sinRestriccionBateria", pm != null && pm.isIgnoringBatteryOptimizations(c.getPackageName()));
        return r;
    }

    @PluginMethod
    public void pedirNotificaciones(PluginCall call) {
        if (Build.VERSION.SDK_INT < 33 || getPermissionState("notificaciones") == PermissionState.GRANTED) {
            call.resolve(estadoActual());
            return;
        }
        requestPermissionForAlias("notificaciones", call, "tras_pedir_notificaciones");
    }

    @PermissionCallback
    private void tras_pedir_notificaciones(PluginCall call) {
        call.resolve(estadoActual());
    }

    @PluginMethod
    public void abrirAjustes(PluginCall call) {
        String tipo = call.getString("tipo", "app");
        Context c = getContext();
        String paquete = c.getPackageName();
        Intent i;
        try {
            if ("exacta".equals(tipo) && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                i = new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:" + paquete));
            } else if ("bateria".equals(tipo)) {
                // lista de apps con "optimización de batería": ahí se elige Gioval > No optimizar
                i = new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS);
            } else if ("notificaciones".equals(tipo)) {
                i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, paquete);
            } else if ("pantallaCompleta".equals(tipo) && Build.VERSION.SDK_INT >= 34) {
                i = new Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT, Uri.parse("package:" + paquete));
            } else {
                i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + paquete));
            }
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
            call.resolve();
        } catch (Exception e) {
            // algunos fabricantes no tienen esa pantalla: se abre la ficha general de la app
            try {
                Intent g = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + paquete));
                g.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                c.startActivity(g);
                call.resolve();
            } catch (Exception e2) {
                call.reject("No se pudo abrir los ajustes");
            }
        }
    }

    @PluginMethod
    public void mantenerPantalla(final PluginCall call) {
        final boolean activo = Boolean.TRUE.equals(call.getBoolean("activo", false));
        if (getActivity() == null) {
            call.resolve();
            return;
        }
        getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (activo) getActivity().getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                else getActivity().getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                call.resolve();
            }
        });
    }
}
