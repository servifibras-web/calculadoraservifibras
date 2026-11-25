package ar.servifibras.gioval;

/** Estado compartido muy simple entre la pantalla principal y el receptor de la alarma. */
final class Estado {
    /** true mientras la app está a la vista y con la pantalla encendida (entre onResume y onPause). */
    static volatile boolean primerPlano = false;

    private Estado() {}
}
