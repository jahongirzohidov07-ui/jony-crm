package uz.jonyacademy.examiner;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.app.KeyguardManager;
import android.content.pm.ServiceInfo;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * IMTIHON NAVBATINI KUZATUVCHI XIZMAT (2026-09-25).
 *
 * Jahongir: "examinerlar uchun ... yangi exam haqida bildirishnoma
 * kelsa o'tkazib yubormasin, suzuvchi oynadan push bildirishnoma
 * keladigan app bo'lsin".
 *
 * QANDAY ISHLAYDI. Xizmat ilova yopilgandan keyin ham ishlab turadi
 * (foreground service) va har 90 soniyada JonyOS dagi imtihon
 * navbatini so'raydi. Yangi so'rov paydo bo'lsa:
 *   1) "boshqa ilovalar ustidan" ruxsati bo'lsa — suzuvchi oyna
 *      darrov ochiladi va bulbul kuyi chaladi (AlertActivity);
 *   2) ruxsat bo'lmasa — bulbul kuyili baland bildirishnoma, telefon
 *      qulflangan bo'lsa ekran yonadi (full-screen intent).
 *
 * NEGA SHUNDAY. Haqiqiy "push" (Firebase) uchun alohida Firebase
 * hisobi va kalit kerak — u Jahongirning hisobidan ochiladi. Shu
 * sababli birinchi bosqichda ilova o'zi so'rab turadi: natija bir
 * xil, faqat batareya biroz ko'proq ketadi va xabar 90 soniyagacha
 * kechikishi mumkin.
 */
public class WatchService extends Service {

    static final String CH_WATCH = "watch";
    // Kanal ovozi yaratilgandan keyin o'zgarmaydi — yangi ovoz uchun
    // yangi kanal ochiladi, eskilari o'chiriladi.
    static final String CH_ALERT = "exam_bulbul";
    /** Oyna o'zi chalganda — bildirishnoma faqat iz, jim. */
    static final String CH_LOG = "exam_log";
    private static final long PERIOD = 90_000L;
    static final String TAG = "JonyExaminer";

    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean running = false;

    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            check();
            handler.postDelayed(this, PERIOD);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        channels(this);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Android 14+ turini aniq aytish shart. "specialUse": dataSync
        // Android 15 da sutkasiga 6 soatdan keyin o'chirib qo'yiladi.
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(1, watching(),
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        } else {
            startForeground(1, watching());
        }
        if (!running) {
            running = true;
            handler.post(tick);
        }
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacks(tick);
        running = false;
        super.onDestroy();
    }

    /** Doimiy (jimgina) bildirishnoma — xizmat ishlayotganini bildiradi. */
    private Notification watching() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
                this, 0, open,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this, CH_WATCH)
                .setContentTitle("Jony Examiner")
                .setContentText("Yangi imtihon so'rovlari kuzatilmoqda")
                .setSmallIcon(android.R.drawable.ic_popup_reminder)
                .setContentIntent(pi)
                .setOngoing(true)
                .build();
    }

    private void check() {
        new Thread(() -> {
            try {
                JSONArray rows = Api.orders(this);
                Log.i(TAG, "navbat: " + rows.length() + " ta yangi so'rov");
                int maxId = 0;
                JSONObject newest = null;
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject o = rows.getJSONObject(i);
                    int id = o.optInt("id");
                    if (id > maxId) {
                        maxId = id;
                        newest = o;
                    }
                }
                // -1 = hali bir marta ham tekshirilmagan. Birinchi
                // tekshiruvda eski so'rovlar uchun bong urilmaydi, faqat
                // belgilab qo'yiladi. (0 ni "birinchi marta" deb olish
                // xato edi: navbat bo'sh bo'lsa, keyingi birinchi yangi
                // so'rov ham jimgina o'tib ketardi.)
                int seen = Api.prefs(this).getInt("last_order", -1);
                if (seen < 0) {
                    Api.prefs(this).edit()
                            .putInt("last_order", maxId).apply();
                } else if (maxId > seen) {
                    if (newest != null) {
                        alert(this, newest, rows.length());
                    }
                    Api.prefs(this).edit()
                            .putInt("last_order", maxId).apply();
                }
            } catch (Api.AuthExpired e) {
                // Token eskirdi — jim turib qolmasin, examiner bilsin.
                Api.clear(this);
                relogin(this);
                handler.post(this::stopSelf);
            } catch (Exception e) {
                // Internet yo'q — keyingi urinishda. Log qoladi: telefon
                // qulfida tarmoq yopilsa shu yerdan ko'rinadi.
                Log.w(TAG, "tekshiruv o'tmadi: " + e);
            }
        }).start();
    }

    /** Sessiya tugadi: kuzatuv to'xtadi, qayta kirish kerak. */
    static void relogin(Context c) {
        PendingIntent pi = PendingIntent.getActivity(
                c, 3, new Intent(c, MainActivity.class),
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification n = new Notification.Builder(c, CH_ALERT)
                .setContentTitle("Jony Examiner: qayta kiring")
                .setContentText("Sessiya tugadi — yangi imtihonlar "
                        + "kuzatilmayapti")
                .setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentIntent(pi)
                .setAutoCancel(true)
                .build();
        c.getSystemService(NotificationManager.class).notify(3, n);
    }

    // ------------------------------------------------------ kanallar
    static void channels(Context c) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        NotificationChannel watch = new NotificationChannel(
                CH_WATCH, "Kuzatuv", NotificationManager.IMPORTANCE_MIN);
        watch.setDescription("Ilova orqa fonda ishlayotganini bildiradi");
        nm.createNotificationChannel(watch);

        nm.deleteNotificationChannel("exam_alert");
        nm.deleteNotificationChannel("exam_whistle");
        NotificationChannel alert = new NotificationChannel(
                CH_ALERT, "Yangi imtihon",
                NotificationManager.IMPORTANCE_HIGH);
        alert.setDescription("Yangi imtihon so'rovi kelganda — bulbul kuyi");
        alert.enableVibration(true);
        alert.setVibrationPattern(new long[]{0, 500, 400, 500});
        alert.setSound(
                Uri.parse("android.resource://" + c.getPackageName()
                        + "/" + R.raw.bulbul),
                new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                        .build());
        alert.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(alert);

        NotificationChannel log = new NotificationChannel(
                CH_LOG, "Imtihon so'rovlari (jim)",
                NotificationManager.IMPORTANCE_LOW);
        log.setDescription("Oyna ochilgandan keyin ro'yxatda qoladigan iz");
        nm.createNotificationChannel(log);
    }

    /** Yangi so'rov: suzuvchi oyna + bulbul kuyi (yoki baland bildirishnoma). */
    static void alert(Context c, JSONObject order, int total) {
        // Maydonlar serverdagi _exam_order_out bilan bir xil
        // (api/common.py). Bo'sh qiymat JSON da null bo'lib keladi.
        String group = str(order, "group");
        String kind = str(order, "kind_label");
        if (kind.isEmpty()) {
            kind = "Imtihon";
        }
        String date = str(order, "date_text");
        if (date.isEmpty()) {
            date = str(order, "date");
        }
        String time = str(order, "time");
        String teacher = str(order, "teacher");
        String branch = str(order, "branch");
        int students = order.optInt("students_count", 0);
        String title = "Yangi imtihon: " + kind;
        StringBuilder sb = new StringBuilder();
        if (!group.isEmpty()) {
            sb.append(group);
            if (students > 0) {
                sb.append(" (").append(students).append(" o'quvchi)");
            }
        }
        if (!date.isEmpty()) {
            sb.append(sb.length() > 0 ? "\n" : "").append(date);
            if (!time.isEmpty()) {
                sb.append(", ").append(time);
            }
        }
        if (!teacher.isEmpty()) {
            sb.append(sb.length() > 0 ? "\n" : "").append("Ustoz: ")
                    .append(teacher);
        }
        if (!branch.isEmpty()) {
            sb.append(sb.length() > 0 ? "\n" : "").append(branch);
        }
        String text = sb.toString();

        Intent full = new Intent(c, AlertActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("title", title)
                .putExtra("text", text)
                .putExtra("total", total);
        PendingIntent fullPi = PendingIntent.getActivity(
                c, 1, full,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);

        Intent open = new Intent(c, MainActivity.class)
                .putExtra("go", "/exam?tab=orders");
        PendingIntent openPi = PendingIntent.getActivity(
                c, 2, open,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);

        // "Boshqa ilovalar ustidan" ruxsati bor bo'lsa oyna to'g'ridan-
        // to'g'ri ochiladi va bulbul kuyini o'zi chaladi; bildirishnoma esa
        // ro'yxatda iz bo'lib qoladi (jim — ovoz ikki marta chalmasin).
        // Ruxsat yo'q bo'lsa — bulbul kuyili baland bildirishnoma.
        //
        // NEGA (2026-09-25, Jahongir: "bildirishnoma kelmadi"): TECNO
        // HiOS yangi ilova bildirishnomasini "past" darajaga tushiradi
        // (so'ralgan 4, berilgan 2) — u tepadan chiqmay, jimgina
        // ro'yxatga tushib qolgan edi.
        boolean overlay = Settings.canDrawOverlays(c);
        Notification.Builder nb = new Notification.Builder(c,
                overlay ? CH_LOG : CH_ALERT)
                .setContentTitle(title)
                .setContentText(text.replace('\n', ' '))
                .setStyle(new Notification.BigTextStyle().bigText(
                        text + (total > 1
                                ? "\n\nNavbatda jami " + total + " ta so'rov"
                                : "")))
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(openPi)
                .setCategory(Notification.CATEGORY_REMINDER)
                .setAutoCancel(true);
        if (!overlay) {
            nb.setFullScreenIntent(fullPi, true);
        }
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        if (overlay) {
            Ringer.start(c);
            KeyguardManager km = c.getSystemService(KeyguardManager.class);
            PowerManager pm = c.getSystemService(PowerManager.class);
            boolean locked = (km != null && km.isKeyguardLocked())
                    || (pm != null && !pm.isInteractive());
            if (locked) {
                // Qulf ekrani: ekranni yoqib, qulf ustidan chiqadigan oyna
                try {
                    c.startActivity(full);
                } catch (Exception e) {
                    // Oyna ochilmasa — bildirishnoma baribir chiqadi
                }
            } else {
                // Telefon ishlatilmoqda: tepada suzuvchi oyna
                FloatingAlert.show(c, title, text, total);
            }
        }
        nm.notify(2, nb.build());
    }

    /** optString null ni "null" matniga aylantiradi — shuni chetlaydi. */
    private static String str(JSONObject o, String key) {
        return o.isNull(key) ? "" : o.optString(key, "").trim();
    }

    static void start(Context c) {
        c.startForegroundService(new Intent(c, WatchService.class));
    }

    static void stop(Context c) {
        c.stopService(new Intent(c, WatchService.class));
    }
}
