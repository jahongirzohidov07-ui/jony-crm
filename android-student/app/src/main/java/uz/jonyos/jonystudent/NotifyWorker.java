package uz.jonyos.jonystudent;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.annotation.NonNull;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * FON BILDIRISHNOMALARI (2026-10-07, Jahongir: "bildirishnomalar ham
 * keladigan bo'lsin").
 *
 * <p>Ilova yopiq bo'lsa ham Android har ~15 daqiqada shu ishni bajaradi:
 * saytdagi /api/student/notifications ro'yxatini (o'sha qo'ng'iroqcha)
 * so'raydi va hali ko'rsatilmagan yangi xabarlarni — ochilgan imtihon,
 * yangi topshiriq, imtihon natijasi, sovg'a, to'lov vaqti — telefon
 * bildirishnomasi qilib chiqaradi. Birinchi tekshiruvda eski xabarlar
 * faqat "ko'rilgan" deb belgilanadi (o'quvchiga bir yo'la 10 ta xabar
 * yog'ilmasin).
 */
public class NotifyWorker extends Worker {

    private static final String API = "https://jonyos.uz/api/student/notifications";
    private static final String UNIQUE = "jony_notify";
    private static final int MAX_PER_RUN = 4;

    public NotifyWorker(@NonNull Context ctx, @NonNull WorkerParameters params) {
        super(ctx, params);
    }

    static void schedule(Context ctx) {
        Constraints c = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED).build();
        PeriodicWorkRequest req = new PeriodicWorkRequest.Builder(
                NotifyWorker.class, 15, TimeUnit.MINUTES).setConstraints(c).build();
        WorkManager.getInstance(ctx).enqueueUniquePeriodicWork(
                UNIQUE, ExistingPeriodicWorkPolicy.KEEP, req);
    }

    /** Login bo'lgan zahoti bir marta tekshirib, "ko'rilganlar"ni belgilab qo'yadi. */
    static void kick(Context ctx) {
        Constraints c = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED).build();
        OneTimeWorkRequest req = new OneTimeWorkRequest.Builder(NotifyWorker.class)
                .setConstraints(c).build();
        WorkManager.getInstance(ctx).enqueueUniqueWork(
                UNIQUE + "_now", ExistingWorkPolicy.REPLACE, req);
    }

    @NonNull
    @Override
    public Result doWork() {
        Context ctx = getApplicationContext();
        SharedPreferences p = ctx.getSharedPreferences("jony", Context.MODE_PRIVATE);
        String token = p.getString("token", "");
        if (token.isEmpty()) {
            return Result.success();
        }
        HttpURLConnection con = null;
        try {
            con = (HttpURLConnection) new URL(API).openConnection();
            con.setConnectTimeout(15000);
            con.setReadTimeout(20000);
            con.setRequestProperty("Authorization", "Bearer " + token);
            con.setRequestProperty("Accept", "application/json");
            int code = con.getResponseCode();
            if (code == 401 || code == 403) {
                // Token eskirgan yoki o'quvchi muzlatilgan — jim to'xtaymiz.
                // Keyingi safar ilova ochilganda yangi token saqlanadi.
                p.edit().putString("token", "").apply();
                return Result.success();
            }
            if (code != 200) {
                return Result.retry();
            }
            StringBuilder sb = new StringBuilder();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(
                    con.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = r.readLine()) != null) {
                    sb.append(line);
                }
            }
            JSONObject data = new JSONObject(sb.toString());
            JSONArray items = data.optJSONArray("items");
            if (items == null) {
                return Result.success();
            }
            // Ko'rilganlar ro'yxati O'QUVCHIGA bog'langan: telefonda boshqa
            // o'quvchi kirsa, unga ham birinchi safar eski xabarlar yog'ilmaydi.
            String owner = String.valueOf(data.optInt("student_id", 0));
            boolean seeded = owner.equals(p.getString("seen_owner", ""));
            Set<String> seen = seeded
                    ? new HashSet<>(p.getStringSet("seen", new HashSet<>()))
                    : new HashSet<>();
            int shown = 0;
            for (int i = 0; i < items.length(); i++) {
                JSONObject it = items.optJSONObject(i);
                if (it == null) {
                    continue;
                }
                String id = it.optString("id", "");
                if (id.isEmpty() || seen.contains(id)) {
                    continue;
                }
                seen.add(id);
                if (!seeded || shown >= MAX_PER_RUN) {
                    continue;
                }
                String href = it.optString("href", "");
                String url = "https://jonyos.uz"
                        + (href.startsWith("/") ? href : "/student/notifications");
                Notifier.show(ctx, id.hashCode(), it.optString("title", "Jony Student"),
                        it.optString("body", ""), url);
                shown++;
            }
            // Ro'yxat cheksiz o'smasin
            if (seen.size() > 500) {
                seen.clear();
                for (int i = 0; i < items.length(); i++) {
                    JSONObject it = items.optJSONObject(i);
                    if (it != null) {
                        seen.add(it.optString("id", ""));
                    }
                }
            }
            p.edit().putStringSet("seen", seen).putString("seen_owner", owner).apply();
            return Result.success();
        } catch (Exception e) {
            return Result.retry();
        } finally {
            if (con != null) {
                con.disconnect();
            }
        }
    }
}
