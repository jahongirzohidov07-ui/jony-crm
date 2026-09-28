package uz.jonyacademy.examiner;

import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;

/**
 * SUZUVCHI OYNA (2026-09-25, Jahongir: "suzuvchi oynadan push
 * bildirishnoma keladigan app bo'lsin").
 *
 * Ekran tepasida, qaysi ilova ochiq bo'lsa o'shaning ustida chiqadi
 * ("boshqa ilovalar ustidan" ruxsati bilan). Oddiy oyna (Activity)
 * TECNO HiOS da ilovaning o'zini oldinga tortib chiqarardi —
 * "Keyinroq" bosilganda examiner o'z ishiga emas, Jony Examiner ga
 * tushib qolardi. Bu oyna esa hech qanday ilovani almashtirmaydi:
 * yopilganda examiner qayerda bo'lsa o'sha yerda qoladi.
 *
 * Tugma bosilmaguncha ekranda turadi — ovoz 30 soniyada to'xtasa ham,
 * xabar o'tkazib yuborilmaydi.
 */
final class FloatingAlert {

    private static View shown;

    private FloatingAlert() {
    }

    static void show(Context c, String title, String text, int total) {
        new Handler(Looper.getMainLooper()).post(
                () -> showOnMain(c.getApplicationContext(), title, text, total));
    }

    private static void showOnMain(Context c, String title, String text,
                                   int total) {
        WindowManager wm = c.getSystemService(WindowManager.class);
        hide(c);

        View v = LayoutInflater.from(c).inflate(R.layout.activity_alert, null);
        float dp = c.getResources().getDisplayMetrics().density;
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(0xFFFFFFFF);
        bg.setCornerRadius(18 * dp);
        bg.setStroke((int) (2 * dp), 0xFF0F4593);
        v.setBackground(bg);
        v.setElevation(12 * dp);

        ((TextView) v.findViewById(R.id.title)).setText(title);
        ((TextView) v.findViewById(R.id.text)).setText(text);
        TextView more = v.findViewById(R.id.more);
        if (total > 1) {
            more.setText(c.getString(R.string.queue_total, total));
        } else {
            more.setVisibility(View.GONE);
        }
        ((Button) v.findViewById(R.id.later)).setOnClickListener(x -> {
            Ringer.stop();
            hide(c);
        });
        ((Button) v.findViewById(R.id.open)).setOnClickListener(x -> {
            Ringer.stop();
            hide(c);
            c.startActivity(new Intent(c, MainActivity.class)
                    .putExtra("go", "/exam?tab=orders")
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        });

        WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                // Fokus olmaydi — examiner ostidagi ilovada yozishda
                // davom eta oladi, faqat oynadagi tugmalar bosiladi.
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                        | WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP;
        lp.y = (int) (36 * dp);
        lp.horizontalMargin = 0.03f;
        try {
            wm.addView(v, lp);
            shown = v;
        } catch (Exception e) {
            // Ruxsat olib qo'yilgan — bildirishnoma baribir chiqadi
            shown = null;
        }
    }

    static void hide(Context c) {
        if (shown == null) {
            return;
        }
        try {
            c.getSystemService(WindowManager.class).removeView(shown);
        } catch (Exception ignored) {
        }
        shown = null;
    }
}
