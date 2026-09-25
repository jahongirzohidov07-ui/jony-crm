package uz.jonyacademy.examiner;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;

/**
 * QULF EKRANIDAGI OYNA (2026-09-25).
 *
 * Telefon qulflangan yoki ekran o'chiq bo'lsa ishlatiladi: ekran yonadi
 * va oyna qulf ustidan chiqadi — examiner xabarni o'tkazib yubormaydi.
 * Telefon ochiq bo'lsa buning o'rniga FloatingAlert (suzuvchi oyna)
 * chiqadi. Ovoz va tebranish Ringer'da — xizmat uni yoqadi, bu oyna
 * tugma bosilganda o'chiradi.
 */
public class AlertActivity extends Activity {

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (Build.VERSION.SDK_INT >= 27) {
            setShowWhenLocked(true);
            setTurnScreenOn(true);
        } else {
            getWindow().addFlags(
                    WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                            | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON);
        }
        setContentView(R.layout.activity_alert);
        fill(getIntent());

        ((Button) findViewById(R.id.open)).setOnClickListener(v -> {
            Ringer.stop();
            startActivity(new Intent(this, MainActivity.class)
                    .putExtra("go", "/audit")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            finish();
        });
        ((Button) findViewById(R.id.later)).setOnClickListener(v -> {
            Ringer.stop();
            finishAndRemoveTask();
        });
    }

    @Override
    protected void onNewIntent(Intent intent) {
        // Oyna ochiq turganda yana so'rov keldi — matn yangilanadi
        super.onNewIntent(intent);
        setIntent(intent);
        fill(intent);
    }

    private void fill(Intent i) {
        ((TextView) findViewById(R.id.title)).setText(
                i.getStringExtra("title"));
        ((TextView) findViewById(R.id.text)).setText(
                i.getStringExtra("text"));
        int total = i.getIntExtra("total", 0);
        TextView more = findViewById(R.id.more);
        if (total > 1) {
            more.setText(getString(R.string.queue_total, total));
            more.setVisibility(View.VISIBLE);
        } else {
            more.setVisibility(View.GONE);
        }
    }
}
