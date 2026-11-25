package ar.servifibras.gioval;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

/**
 * Pantalla principal: Capacitor muestra gioval/ (la app web) dentro de un WebView.
 * Lo único propio: registrar el plugin de la alarma nativa y avisar si la app está a la vista
 * (si está a la vista, la alarma la hace la app web; si no, suena la nativa).
 */
public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        // los plugins propios se registran ANTES de super.onCreate (ahí Capacitor arma el puente)
        registerPlugin(GiovalAlarmaPlugin.class);
        super.onCreate(savedInstanceState);
    }

    @Override
    public void onResume() {
        super.onResume();
        Estado.primerPlano = true;
        // si la app se abrió mientras la alarma sonaba (tocando el aviso), el sonido se corta:
        // la app web se entera sola de que la hora ya pasó (alarma.js recalcula con la hora absoluta)
        AlarmaServicio.detener(this);
    }

    @Override
    public void onPause() {
        Estado.primerPlano = false;
        super.onPause();
    }
}
