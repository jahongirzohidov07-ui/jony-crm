package uz.jonyacademy.examiner;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * JonyOS bilan aloqa (2026-09-25).
 *
 * Tashqi kutubxona ishlatilmaydi — ikkita so'rovga HttpURLConnection
 * yetadi: kirish va imtihon navbatini o'qish. Ilova qanchalik yengil
 * bo'lsa, shunchalik tez ochiladi va kam batareya yeydi.
 */
final class Api {

    static final String BASE = "https://jonyos.uz";
    private static final String PREF = "jony_examiner";

    private Api() {
    }

    /** Token eskirgan yoki bekor qilingan — qayta kirish kerak. */
    static final class AuthExpired extends IllegalStateException {
        AuthExpired(String m) {
            super(m);
        }
    }

    static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    static String token(Context c) {
        return prefs(c).getString("token", null);
    }

    static void saveToken(Context c, String token, String name) {
        prefs(c).edit().putString("token", token)
                .putString("name", name).apply();
    }

    static void clear(Context c) {
        prefs(c).edit().remove("token").remove("name").remove("user")
                .remove("push_web").apply();
    }

    /** Sayt o'z tokenini yangilasa (login almashtirildi) — o'shani olamiz. */
    static void adoptToken(Context c, String token) {
        prefs(c).edit().putString("token", token).apply();
    }

    /** Kirish. Muvaffaqiyatli bo'lsa token saqlanadi. */
    static String login(Context c, String username, String password)
            throws Exception {
        JSONObject body = new JSONObject();
        body.put("username", username);
        body.put("password", password);
        // "Eslab qolish" — token 60 kun yashaydi. Oddiy token 12 soatda
        // eskiradi va kuzatuv tunda jimgina to'xtab qolardi.
        body.put("remember", true);
        String out = post("/api/auth/login", body.toString(), null);
        JSONObject j = new JSONObject(out);
        String role = j.optString("role", "");
        if (!role.startsWith("examiner") && !role.equals("head_examiner")
                && !role.equals("founder")) {
            throw new IllegalStateException(
                    "Bu ilova examinerlar uchun. Sizning lavozimingiz: "
                            + role);
        }
        saveToken(c, j.getString("access_token"),
                j.optString("full_name", username));
        // Sayt (AuthContext) ochilishi bilan foydalanuvchini ham shu
        // yerdan o'qiydi — faqat token berilsa, bir lahza login
        // sahifasiga otib yuborishi mumkin edi.
        JSONObject u = new JSONObject();
        u.put("full_name", j.optString("full_name", username));
        u.put("role", role);
        u.put("branch_id", j.isNull("branch_id") ? JSONObject.NULL
                : j.opt("branch_id"));
        prefs(c).edit().putString("user", u.toString())
                .putBoolean("push_web", true).apply();
        return j.optString("full_name", username);
    }

    /** Imtihon navbati: tasdiqlanmagan so'rovlar. */
    static JSONArray orders(Context c) throws Exception {
        String t = token(c);
        if (t == null) {
            return new JSONArray();
        }
        String out;
        try {
            out = get("/api/exam-orders?status=new", t);
        } catch (IllegalStateException e) {
            if (e.getMessage() != null && e.getMessage().startsWith("401")) {
                throw new AuthExpired("Sessiya tugadi");
            }
            throw e;
        }
        Object v = new org.json.JSONTokener(out).nextValue();
        if (v instanceof JSONArray) {
            return (JSONArray) v;
        }
        JSONObject o = (JSONObject) v;
        return o.optJSONArray("rows") != null
                ? o.optJSONArray("rows") : new JSONArray();
    }

    // ----------------------------------------------------- quyi qism
    private static String get(String path, String token) throws Exception {
        HttpURLConnection c = open(path, "GET", token);
        return read(c, token);
    }

    private static String post(String path, String body, String token)
            throws Exception {
        HttpURLConnection c = open(path, "POST", token);
        c.setDoOutput(true);
        c.setRequestProperty("Content-Type", "application/json");
        try (OutputStream os = c.getOutputStream()) {
            os.write(body.getBytes(StandardCharsets.UTF_8));
        }
        return read(c, token);
    }

    private static HttpURLConnection open(String path, String method,
                                          String token) throws Exception {
        HttpURLConnection c = (HttpURLConnection)
                new URL(BASE + path).openConnection();
        c.setRequestMethod(method);
        c.setConnectTimeout(12000);
        c.setReadTimeout(15000);
        if (token != null) {
            c.setRequestProperty("Authorization", "Bearer " + token);
        }
        return c;
    }

    private static String read(HttpURLConnection c, String token)
            throws Exception {
        int code = c.getResponseCode();
        InputStream in = code >= 400 ? c.getErrorStream() : c.getInputStream();
        StringBuilder sb = new StringBuilder();
        if (in != null) {
            try (BufferedReader r = new BufferedReader(
                    new InputStreamReader(in, StandardCharsets.UTF_8))) {
                String line;
                while ((line = r.readLine()) != null) {
                    sb.append(line);
                }
            }
        }
        String out = sb.toString();
        if (code >= 400) {
            String msg = out;
            try {
                msg = new JSONObject(out).optString("detail", out);
            } catch (Exception ignored) {
            }
            if (code == 401) {
                // Kirish oynasida — parol xato; navbatda — token eskirgan
                msg = token == null ? "Login yoki parol noto'g'ri"
                        : "401 " + msg;
            }
            throw new IllegalStateException(msg);
        }
        return out;
    }
}
