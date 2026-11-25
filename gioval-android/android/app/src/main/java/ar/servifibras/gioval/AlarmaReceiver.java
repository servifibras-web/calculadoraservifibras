package ar.servifibras.gioval;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import androidx.core.content.ContextCompat;

/** Llega la hora de la alarma (la despierta AlarmManager aunque la app esté cerrada y la pantalla apagada). */
public class AlarmaReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !AlarmaProgramador.ACCION_ALARMA.equals(intent.getAction())) return;
        int id = intent.getIntExtra(AlarmaProgramador.EXTRA_ID, 7001);
        String titulo = intent.getStringExtra(AlarmaProgramador.EXTRA_TITULO);
        String texto = intent.getStringExtra(AlarmaProgramador.EXTRA_TEXTO);
        AlarmaProgramador.olvidar(context, id);

        // App a la vista: la alarma web (alarma.js) ya la maneja con sonido propio. Acá no se duplica.
        if (Estado.primerPlano) return;

        Context app = context.getApplicationContext();
        try {
            AlarmaServicio.iniciar(app, id, titulo, texto);
        } catch (Exception e) {
            // Android no dejó iniciar el servicio de sonido: al menos un aviso con sonido de alarma
            Notificaciones.aviso(app, id, titulo, texto, true);
        }
    }
}
