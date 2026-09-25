package uz.jonyacademy.examiner;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;

/**
 * EKRANGA CHIQADIGAN OYNA (2026-09-25).
 *
 * Yangi imtihon so'rovi kelganda telefon qulflangan bo'lsa ham
 * ekran yonadi va shu oyna chiqadi — examiner xabarni o'tkazib
 * yubormaydi. "Ko'rish" bosilsa ilova imtihon navbatida ochiladi.
 *
 * OVOZNI OYNANING O'ZI CHALADI (2026-09-25, Jahongir: "bildirishnoma
 * kelmadi"). TECNO/HiOS yangi ilova bildirishnomasini "past" darajaga
 * tushirib qo'yadi — u jimgina ro'yxatga tushadi, tepadan chiqmaydi.
 * Shuning uchun xizmat bu oynani "boshqa ilovalar ustidan" ruxsati
 * bilan to'g'ridan-to'g'ri ochadi, ovoz va tebranish esa shu yerda:
 * tugma bosilguncha yoki 30 soniya davomida.
 */
public class AlertActivity extends Activity {

    private static final long RING_MS = 30_000L;
    private MediaPlayer ring;
    private Vibrator vib;
    private final Handler handler = new Handler(Looper.getMainLooper());

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
        ringStart();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        // Oyna ochiq turganda yana so'rov keldi — matn yangilanadi
        super.onNewIntent(intent);
        setIntent(intent);
        recreate();
    }

    private void ringStart() {
        // O'ziga xos hakam hushtagi (res/raw/whistle.wav) — telefonning
        // boshqa hech bir ovoziga o'xshamaydi, darrov tanib olinadi.
        try {
            ring = MediaPlayer.create(this, R.raw.whistle,
                    new AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                            .setContentType(
                                    AudioAttributes.CONTENT_TYPE_SONIFICATION)
                            .build(),
                    AudioManager.AUDIO_SESSION_ID_GENERATE);
            if (ring != null) {
                ring.setLooping(true);
                ring.start();
            }
        } catch (Exception ignored) {
        }
        try {
            vib = getSystemService(Vibrator.class);
            if (vib != null && vib.hasVibrator()) {
                vib.vibrate(VibrationEffect.createWaveform(
                        new long[]{0, 500, 400, 500, 1600}, 0));
            }
        } catch (Exception ignored) {
        }
        handler.postDelayed(this::ringStop, RING_MS);
    }

    private void ringStop() {
        handler.removeCallbacksAndMessages(null);
        try {
            if (ring != null) {
                ring.stop();
                ring.release();
                ring = null;
            }
        } catch (Exception ignored) {
        }
        try {
            if (vib != null) {
                vib.cancel();
            }
        } catch (Exception ignored) {
        }
    }

    @Override
    protected void onDestroy() {
        ringStop();
        super.onDestroy();
    }
}
