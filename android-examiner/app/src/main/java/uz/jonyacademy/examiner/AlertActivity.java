package uz.jonyacademy.examiner;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;

/**
 * EKRANGA CHIQADIGAN OYNA (2026-09-25).
 *
 * Yangi imtihon so'rovi kelganda telefon qulflangan bo'lsa ham
 * ekran yonadi va shu oyna chiqadi — examiner xabarni o'tkazib
 * yubormaydi. "Ko'rish" bosilsa ilova imtihon navbatida ochiladi.
 */
public class AlertActivity extends Activity {

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true);
            setTurnScreenOn(true);
        } else {
            getWindow().addFlags(
                    WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                            | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON);
        }
        setContentView(R.layout.activity_alert);

        Intent i = getIntent();
        ((TextView) findViewById(R.id.title)).setText(
                i.getStringExtra("title"));
        ((TextView) findViewById(R.id.text)).setText(
                i.getStringExtra("text"));
        int total = i.getIntExtra("total", 0);
        TextView more = findViewById(R.id.more);
        if (total > 1) {
            more.setText("Navbatda jami " + total + " ta so'rov");
        } else {
            more.setVisibility(android.view.View.GONE);
        }

        ((Button) findViewById(R.id.open)).setOnClickListener(v -> {
            startActivity(new Intent(this, MainActivity.class)
                    .putExtra("go", "/audit")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            finish();
        });
        ((Button) findViewById(R.id.later)).setOnClickListener(v -> finish());
    }
}
