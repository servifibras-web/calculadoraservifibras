package ar.servifibras.gioval;

import android.app.Notification;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.media.RingtoneManager;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.os.VibrationEffect;
import android.os.Vibrator;

import androidx.core.app.ServiceCompat;
import androidx.core.content.ContextCompat;

/**
 * Servicio en primer plano que hace sonar la alarma: tono de alarma del sistema en bucle (volumen de ALARMA),
 * vibración y un aviso con pantalla completa sobre el bloqueo. Se corta solo al minuto, o al tocar Parar / abrir la app.
 */
public class AlarmaServicio extends Service {
    static final String ACCION_PARAR = "ar.servifibras.gioval.PARAR";
    private static final long DURACION_MS = 60_000L;

    private MediaPlayer player;
    private Vibrator vibrador;
    private PowerManager.WakeLock wakeLock;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable porTiempo = new Runnable() {
        @Override
        public void run() {
            // sonó un minuto y nadie la paró: se deja un aviso en la barra para que se vea que sonó
            Notificaciones.aviso(AlarmaServicio.this, 0, tituloGuardado, textoGuardado, false);
            stopSelf();
        }
    };
    private String tituloGuardado;
    private String textoGuardado;

    static void iniciar(Context c, int id, String titulo, String texto) {
        Intent i = new Intent(c, AlarmaServicio.class);
        i.putExtra(AlarmaProgramador.EXTRA_ID, id);
        i.putExtra(AlarmaProgramador.EXTRA_TITULO, titulo);
        i.putExtra(AlarmaProgramador.EXTRA_TEXTO, texto);
        ContextCompat.startForegroundService(c, i);
    }

    static void detener(Context c) {
        c.stopService(new Intent(c, AlarmaServicio.class));
        Notificaciones.quitar(c);
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACCION_PARAR.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        int id = intent != null ? intent.getIntExtra(AlarmaProgramador.EXTRA_ID, 7001) : 7001;
        tituloGuardado = intent != null ? intent.getStringExtra(AlarmaProgramador.EXTRA_TITULO) : null;
        textoGuardado = intent != null ? intent.getStringExtra(AlarmaProgramador.EXTRA_TEXTO) : null;

        Notification n = Notificaciones.sonando(this, id, tituloGuardado, textoGuardado);
        try {
            int tipo = Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q ? ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK : 0;
            ServiceCompat.startForeground(this, Notificaciones.NOTIF_ID, n, tipo);
        } catch (Exception e) {
            // Android no dejó pasar a primer plano: aviso con sonido de alarma del sistema y listo
            Notificaciones.aviso(this, id, tituloGuardado, textoGuardado, true);
            stopSelf();
            return START_NOT_STICKY;
        }

        try {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (pm != null) {
                wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "gioval:alarma");
                wakeLock.acquire(DURACION_MS + 5_000L);
            }
        } catch (Exception e) {
            wakeLock = null;
        }
        empezarSonido();
        empezarVibracion();
        handler.removeCallbacks(porTiempo);
        handler.postDelayed(porTiempo, DURACION_MS);
        return START_NOT_STICKY;
    }

    private Uri tono() {
        Uri uri = RingtoneManager.getActualDefaultRingtoneUri(this, RingtoneManager.TYPE_ALARM);
        if (uri == null) uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
        if (uri == null) uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
        if (uri == null) uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE);
        return uri;
    }

    private void empezarSonido() {
        try {
            Uri uri = tono();
            if (uri == null) return;
            player = new MediaPlayer();
            player.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build());
            player.setDataSource(this, uri);
            player.setLooping(true);
            player.prepare();
            player.start();
        } catch (Exception e) {
            // sin sonido (queda la vibración y el aviso en pantalla)
            liberarPlayer();
        }
    }

    @SuppressWarnings("deprecation")
    private void empezarVibracion() {
        try {
            vibrador = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
            if (vibrador == null || !vibrador.hasVibrator()) return;
            long[] patron = { 0, 600, 400 };
            AudioAttributes aa = new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build();
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrador.vibrate(VibrationEffect.createWaveform(patron, 0), aa);
            } else {
                vibrador.vibrate(patron, 0, aa);
            }
        } catch (Exception e) {
            vibrador = null;
        }
    }

    private void liberarPlayer() {
        try {
            if (player != null) {
                try { player.stop(); } catch (Exception e) { /* ya parado */ }
                player.release();
            }
        } catch (Exception e) {
            // nada
        }
        player = null;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacks(porTiempo);
        liberarPlayer();
        try { if (vibrador != null) vibrador.cancel(); } catch (Exception e) { /* nada */ }
        try { if (wakeLock != null && wakeLock.isHeld()) wakeLock.release(); } catch (Exception e) { /* nada */ }
        super.onDestroy();
    }
}
