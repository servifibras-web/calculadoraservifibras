package ar.servifibras.gioval;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

/** Canales y avisos de la alarma. */
final class Notificaciones {
    /** Canal del aviso mientras suena (silencioso: el sonido lo hace AlarmaServicio con el volumen de ALARMA). */
    static final String CANAL_SONANDO = "gioval_alarma_sonando";
    /** Canal de avisos sueltos (alarma vencida con el aparato apagado, o si no se pudo iniciar el sonido). */
    static final String CANAL_AVISO = "gioval_alarma_aviso";
    /** Número del aviso del servicio mientras suena (desaparece cuando el servicio se detiene). */
    static final int NOTIF_ID = 7101;
    /** Número del aviso suelto (queda en la barra aunque el servicio se detenga). */
    static final int NOTIF_AVISO_ID = 7102;

    private Notificaciones() {}

    static void crearCanales(Context c) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null) return;

        NotificationChannel sonando = new NotificationChannel(CANAL_SONANDO, c.getString(R.string.alarma_canal_sonando), NotificationManager.IMPORTANCE_HIGH);
        sonando.setSound(null, null);
        sonando.enableVibration(false);
        sonando.setBypassDnd(true);
        sonando.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(sonando);

        NotificationChannel aviso = new NotificationChannel(CANAL_AVISO, c.getString(R.string.alarma_canal_aviso), NotificationManager.IMPORTANCE_HIGH);
        Uri uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
        aviso.setSound(uri, new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
        aviso.enableVibration(true);
        aviso.setVibrationPattern(new long[] { 0, 500, 300, 500 });
        aviso.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(aviso);
    }

    private static PendingIntent abrirApp(Context c) {
        Intent i = new Intent(c, MainActivity.class);
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        return PendingIntent.getActivity(c, 11, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private static String tituloOk(Context c, String titulo) {
        return (titulo == null || titulo.isEmpty()) ? c.getString(R.string.alarma_titulo_defecto) : titulo;
    }

    /** Aviso del servicio mientras suena: pantalla completa sobre el bloqueo + botón Parar. */
    static Notification sonando(Context c, int id, String titulo, String texto) {
        crearCanales(c);
        Intent pant = new Intent(c, AlarmaActivity.class);
        pant.putExtra(AlarmaProgramador.EXTRA_ID, id);
        pant.putExtra(AlarmaProgramador.EXTRA_TITULO, tituloOk(c, titulo));
        pant.putExtra(AlarmaProgramador.EXTRA_TEXTO, texto);
        pant.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_USER_ACTION);
        PendingIntent pPantalla = PendingIntent.getActivity(c, 12, pant, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Intent parar = new Intent(c, AlarmaServicio.class).setAction(AlarmaServicio.ACCION_PARAR);
        PendingIntent pParar = PendingIntent.getService(c, 13, parar, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        return new NotificationCompat.Builder(c, CANAL_SONANDO)
                .setSmallIcon(R.drawable.ic_stat_alarma)
                .setColor(0xFF7C4DFF)
                .setContentTitle(tituloOk(c, titulo))
                .setContentText(texto)
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setContentIntent(abrirApp(c))
                .setFullScreenIntent(pPantalla, true)
                .addAction(0, c.getString(R.string.alarma_parar), pParar)
                .build();
    }

    /** Aviso suelto (queda en la barra hasta que se toca). conSonido = sonido de alarma del sistema. */
    static void aviso(Context c, int id, String titulo, String texto, boolean conSonido) {
        try {
            crearCanales(c);
            NotificationCompat.Builder b = new NotificationCompat.Builder(c, conSonido ? CANAL_AVISO : CANAL_SONANDO)
                    .setSmallIcon(R.drawable.ic_stat_alarma)
                    .setColor(0xFF7C4DFF)
                    .setContentTitle(tituloOk(c, titulo))
                    .setContentText(texto == null || texto.isEmpty() ? c.getString(R.string.alarma_perdida) : texto)
                    .setCategory(NotificationCompat.CATEGORY_ALARM)
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setAutoCancel(true)
                    .setContentIntent(abrirApp(c));
            NotificationManagerCompat.from(c).notify(NOTIF_AVISO_ID, b.build());
        } catch (SecurityException e) {
            // sin permiso de avisos (Android 13+): no hay nada más que hacer acá
        }
    }

    static void quitar(Context c) {
        try {
            NotificationManagerCompat.from(c).cancel(NOTIF_AVISO_ID);
        } catch (Exception e) {
            // nada
        }
    }
}
