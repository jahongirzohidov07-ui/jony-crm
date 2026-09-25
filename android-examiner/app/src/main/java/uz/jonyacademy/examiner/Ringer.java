package uz.jonyacademy.examiner;

import android.content.Context;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;

/**
 * BULBUL KUYI VA TEBRANISH (2026-09-25, Jahongir: "kuchli ovoz,
 * bulbul sayragandek aniq notalar bo'lsin").
 *
 * res/raw/bulbul.wav budilnik oqimida chalinadi — bildirishnoma ovozi
 * odatda past turadi, budilniknikiga esa hamma e'tibor beradi. Telefon
 * ovozsiz/tebranish rejimida bo'lsa faqat tebranadi: imtihon payti
 * xonada baqirib qolmasin. Examiner tugmani bosguncha yoki 30 soniya
 * davomida takrorlanadi.
 *
 * Suzuvchi oyna ham, qulf ekranidagi oyna ham shu bitta chalg'ichni
 * ishlatadi — ikkalasi bir vaqtda ochilsa ovoz ikki marta chalmaydi.
 */
final class Ringer {

    private static final long RING_MS = 30_000L;
    private static MediaPlayer player;
    private static Vibrator vib;
    private static final Handler handler = new Handler(Looper.getMainLooper());

    private Ringer() {
    }

    static synchronized void start(Context c) {
        stop();
        Context app = c.getApplicationContext();
        try {
            AudioManager am = app.getSystemService(AudioManager.class);
            if (am == null
                    || am.getRingerMode() == AudioManager.RINGER_MODE_NORMAL) {
                player = MediaPlayer.create(app, R.raw.bulbul,
                        new AudioAttributes.Builder()
                                .setUsage(AudioAttributes.USAGE_ALARM)
                                .setContentType(
                                        AudioAttributes.CONTENT_TYPE_SONIFICATION)
                                .build(),
                        AudioManager.AUDIO_SESSION_ID_GENERATE);
                if (player != null) {
                    player.setLooping(true);
                    player.start();
                }
            }
        } catch (Exception ignored) {
        }
        try {
            vib = app.getSystemService(Vibrator.class);
            if (vib != null && vib.hasVibrator()) {
                vib.vibrate(VibrationEffect.createWaveform(
                        new long[]{0, 500, 400, 500, 1600}, 0));
            }
        } catch (Exception ignored) {
        }
        handler.postDelayed(Ringer::stop, RING_MS);
    }

    static synchronized void stop() {
        handler.removeCallbacksAndMessages(null);
        try {
            if (player != null) {
                player.stop();
                player.release();
            }
        } catch (Exception ignored) {
        }
        player = null;
        try {
            if (vib != null) {
                vib.cancel();
            }
        } catch (Exception ignored) {
        }
        vib = null;
    }
}
