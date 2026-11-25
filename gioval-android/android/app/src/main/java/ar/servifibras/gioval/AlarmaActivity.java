package ar.servifibras.gioval;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Pantalla que aparece sobre el bloqueo cuando suena la alarma: título, texto y un botón grande.
 * Sin XML a propósito: es una sola pantalla simple.
 */
public class AlarmaActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true);
            setTurnScreenOn(true);
        } else {
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON);
        }
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON | WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD);

        String titulo = getIntent().getStringExtra(AlarmaProgramador.EXTRA_TITULO);
        String texto = getIntent().getStringExtra(AlarmaProgramador.EXTRA_TEXTO);
        if (titulo == null || titulo.isEmpty()) titulo = getString(R.string.alarma_titulo_defecto);
        if (texto == null) texto = "";

        int p = (int) (24 * getResources().getDisplayMetrics().density);
        LinearLayout raiz = new LinearLayout(this);
        raiz.setOrientation(LinearLayout.VERTICAL);
        raiz.setGravity(Gravity.CENTER);
        raiz.setBackgroundColor(Color.parseColor("#7C4DFF"));
        raiz.setPadding(p, p, p, p);

        TextView emoji = new TextView(this);
        emoji.setText("⏰");
        emoji.setTextSize(72);
        emoji.setGravity(Gravity.CENTER);
        raiz.addView(emoji);

        TextView t = new TextView(this);
        t.setText(titulo);
        t.setTextColor(Color.WHITE);
        t.setTextSize(30);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setGravity(Gravity.CENTER);
        raiz.addView(t);

        TextView x = new TextView(this);
        x.setText(texto);
        x.setTextColor(Color.WHITE);
        x.setTextSize(22);
        x.setGravity(Gravity.CENTER);
        x.setPadding(0, p / 2, 0, p);
        raiz.addView(x);

        Button listo = new Button(this);
        listo.setText(R.string.alarma_listo);
        listo.setTextSize(26);
        listo.setPadding(p * 2, p / 2, p * 2, p / 2);
        listo.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                AlarmaServicio.detener(AlarmaActivity.this);
                Intent i = new Intent(AlarmaActivity.this, MainActivity.class);
                i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                startActivity(i);
                finish();
            }
        });
        raiz.addView(listo);
        setContentView(raiz);
    }
}
