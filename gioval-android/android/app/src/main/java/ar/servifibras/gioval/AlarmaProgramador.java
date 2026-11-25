package ar.servifibras.gioval;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import org.json.JSONObject;

import java.util.Map;

/**
 * Programa y guarda las alarmas del sistema.
 * - Se usa setExactAndAllowWhileIdle: hora exacta, y suena aunque el aparato esté en reposo (Doze).
 * - Si en Android 12+ el permiso "Alarmas y recordatorios" no está dado, se usa una alarma NO exacta
 *   (puede atrasarse unos minutos) y la app web lo informa en el panel de adultos.
 * - Cada alarma pendiente se guarda también en SharedPreferences para poder reprogramarla tras un reinicio.
 */
final class AlarmaProgramador {
    static final String ACCION_ALARMA = "ar.servifibras.gioval.ALARMA";
    static final String EXTRA_ID = "id";
    static final String EXTRA_FIN = "fin";
    static final String EXTRA_TITULO = "titulo";
    static final String EXTRA_TEXTO = "texto";

    private static final String PREFS = "gioval_alarmas";
    /** Si el aparato estuvo apagado y la alarma venció hace menos que esto, se avisa igual al arrancar. */
    private static final long GRACIA_ARRANQUE_MS = 30L * 60L * 1000L;

    private AlarmaProgramador() {}

    static boolean puedeExacta(Context c) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true;
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        return am != null && am.canScheduleExactAlarms();
    }

    private static PendingIntent pendiente(Context c, int id, long fin, String titulo, String texto) {
        Intent i = new Intent(c, AlarmaReceiver.class).setAction(ACCION_ALARMA);
        i.putExtra(EXTRA_ID, id);
        i.putExtra(EXTRA_FIN, fin);
        i.putExtra(EXTRA_TITULO, titulo);
        i.putExtra(EXTRA_TEXTO, texto);
        return PendingIntent.getBroadcast(c, id, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** Programa (reemplazando la anterior con el mismo id) y la guarda. Devuelve true si la alarma es exacta. */
    static boolean programar(Context c, int id, long fin, String titulo, String texto) {
        guardar(c, id, fin, titulo, texto);
        return armar(c, id, fin, titulo, texto);
    }

    private static boolean armar(Context c, int id, long fin, String titulo, String texto) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return false;
        PendingIntent pi = pendiente(c, id, fin, titulo, texto);
        boolean exacta = puedeExacta(c);
        try {
            if (exacta) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, fin, pi);
            else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, fin, pi);
        } catch (SecurityException e) {
            // el permiso se revocó justo ahora: se cae a la alarma no exacta
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, fin, pi);
            exacta = false;
        }
        return exacta;
    }

    static void cancelar(Context c, int id) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am != null) am.cancel(pendiente(c, id, 0L, "", ""));
        olvidar(c, id);
    }

    /** Se llama cuando la alarma ya sonó: se borra del registro. */
    static void olvidar(Context c, int id) {
        prefs(c).edit().remove("a" + id).apply();
    }

    private static SharedPreferences prefs(Context c) {
        return c.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static void guardar(Context c, int id, long fin, String titulo, String texto) {
        try {
            JSONObject o = new JSONObject();
            o.put("fin", fin);
            o.put("titulo", titulo);
            o.put("texto", texto);
            prefs(c).edit().putString("a" + id, o.toString()).apply();
        } catch (Exception e) {
            // si no se pudo guardar, la alarma igual queda programada (solo se pierde la reprogramación tras reiniciar)
        }
    }

    static boolean hayPendientes(Context c) {
        return !prefs(c).getAll().isEmpty();
    }

    /** Tras reiniciar el aparato / actualizar la app / cambiar la hora: vuelve a programar lo pendiente. */
    static void reprogramarTodas(Context c) {
        long ahora = System.currentTimeMillis();
        Map<String, ?> todo = prefs(c).getAll();
        for (Map.Entry<String, ?> e : todo.entrySet()) {
            String k = e.getKey();
            if (k == null || !k.startsWith("a") || !(e.getValue() instanceof String)) continue;
            try {
                int id = Integer.parseInt(k.substring(1));
                JSONObject o = new JSONObject((String) e.getValue());
                long fin = o.getLong("fin");
                String titulo = o.optString("titulo", "");
                String texto = o.optString("texto", "");
                if (fin > ahora) {
                    armar(c, id, fin, titulo, texto);
                } else if (ahora - fin < GRACIA_ARRANQUE_MS) {
                    // venció mientras el aparato estaba apagado: se avisa ahora (sin sonido continuo: desde el arranque
                    // Android no deja iniciar el servicio de sonido)
                    Notificaciones.aviso(c, id, titulo, texto, true);
                    olvidar(c, id);
                } else {
                    olvidar(c, id);
                }
            } catch (Exception ex) {
                prefs(c).edit().remove(k).apply();
            }
        }
    }
}
