package ar.servifibras.gioval;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Reinicio del aparato, app actualizada, cambio de hora o permiso de alarmas exactas modificado: se reprograman las alarmas. */
public class ArranqueReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) return;
        switch (intent.getAction()) {
            case Intent.ACTION_BOOT_COMPLETED:
            case Intent.ACTION_MY_PACKAGE_REPLACED:
            case Intent.ACTION_TIME_CHANGED:
            case Intent.ACTION_TIMEZONE_CHANGED:
            case "android.app.action.SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED":
                AlarmaProgramador.reprogramarTodas(context.getApplicationContext());
                break;
            default:
                break;
        }
    }
}
