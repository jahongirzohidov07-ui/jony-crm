package uz.jonyacademy.examiner;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import android.window.OnBackInvokedDispatcher;

import androidx.core.app.ActivityCompat;

import org.json.JSONObject;

import android.app.Activity;

/**
 * JONY EXAMINER (2026-09-25).
 *
 * Jahongir: "examinerlar uchun bir programma yasa, ularga
 * bildirishnoma tepadan kelsin, yangi exam haqida bildirishnoma
 * kelsa o'tkazib yubormasin".
 *
 * Ilova ikki ishni qiladi:
 *   1) JonyOS ni ochadi — examiner odatdagidek ishlaydi;
 *   2) orqa fonda imtihon navbatini kuzatadi va yangi so'rov
 *      kelganda ovoz bilan, ekranga chiqadigan oyna bilan xabar
 *      beradi (WatchService).
 *
 * Kirish ilovaning o'zida bo'ladi: token saqlanadi va sahifaga
 * uzatiladi — shunda examiner har safar qayta login qilmaydi va
 * kuzatuv xizmati ham o'sha token bilan ishlaydi.
 */
public class MainActivity extends Activity {

    private WebView web;
    private View login;
    private EditText userIn, passIn;
    private TextView note;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        setContentView(R.layout.activity_main);
        web = findViewById(R.id.web);
        login = findViewById(R.id.login);
        userIn = findViewById(R.id.user);
        passIn = findViewById(R.id.pass);
        note = findViewById(R.id.note);
        Button enter = findViewById(R.id.enter);

        WatchService.channels(this);
        askNotifications();
        setupWeb();
        setupBack();

        enter.setOnClickListener(v -> doLogin());

        if (Api.token(this) != null) {
            open(getIntent());
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Sessiya orqa fonda tugagan bo'lsa (WatchService tokenni
        // o'chiradi) — eski sahifa emas, kirish oynasi ko'rinsin.
        if (Api.token(this) == null && web.getVisibility() == View.VISIBLE) {
            web.setVisibility(View.GONE);
            login.setVisibility(View.VISIBLE);
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (Api.token(this) != null) {
            open(intent);
        }
    }

    private void askNotifications() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                    this, new String[]{Manifest.permission.POST_NOTIFICATIONS},
                    7);
        }
    }

    private void doLogin() {
        String u = userIn.getText().toString().trim();
        String p = passIn.getText().toString();
        if (u.isEmpty() || p.isEmpty()) {
            note.setText("Login va parolni kiriting");
            note.setVisibility(View.VISIBLE);
            return;
        }
        note.setVisibility(View.GONE);
        new Thread(() -> {
            try {
                Api.login(this, u, p);
                new Handler(Looper.getMainLooper()).post(() -> open(null));
            } catch (Exception e) {
                String m = e.getMessage() == null ? "Kirib bo'lmadi"
                        : e.getMessage();
                new Handler(Looper.getMainLooper()).post(() -> {
                    note.setText(m);
                    note.setVisibility(View.VISIBLE);
                });
            }
        }).start();
    }

    /** Sahifani ochadi va kuzatuvni yoqadi. */
    private void open(Intent from) {
        login.setVisibility(View.GONE);
        web.setVisibility(View.VISIBLE);
        String go = from != null ? from.getStringExtra("go") : null;
        web.loadUrl(Api.BASE + (go == null ? "/" : go));
        WatchService.start(this);
        askBackground();
    }

    /**
     * Xabar o'tkazib yuborilmasligi uchun uch sozlama kerak:
     *   0) "boshqa ilovalar ustidan" — oyna telefon qaysi ekranda
     *      bo'lmasin ochiladi (eng muhimi: TECNO bildirishnomani jim
     *      qilib qo'yadi, oyna esa baribir chiqadi);
     *   1) batareya tejash kuzatuvni uxlatib qo'ymasin;
     *   2) Android 14+ da ekranga chiqadigan oyna ruxsati.
     * Har ochilishda faqat bittasi so'raladi — ikkala oyna bir
     * vaqtda chiqib, biri ikkinchisini yopib qo'ymasin.
     */
    private void askBackground() {
        try {
            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Jony Examiner ga ruxsat bering — "
                        + "yangi imtihon oynasi shunda chiqadi",
                        Toast.LENGTH_LONG).show();
                startActivity(new Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:" + getPackageName())));
                return;
            }
            PowerManager pm = getSystemService(PowerManager.class);
            if (!pm.isIgnoringBatteryOptimizations(getPackageName())) {
                startActivity(new Intent(
                        Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + getPackageName())));
                return;
            }
            if (Build.VERSION.SDK_INT >= 34) {
                NotificationManager nm =
                        getSystemService(NotificationManager.class);
                if (!nm.canUseFullScreenIntent()) {
                    startActivity(new Intent(
                            Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                            Uri.parse("package:" + getPackageName())));
                }
            }
        } catch (Exception ignored) {
            // Ba'zi telefonlarda bu oynalar yo'q — ilova baribir ishlaydi
        }
    }

    private void setupWeb() {
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setSupportMultipleWindows(false);
        web.addJavascriptInterface(new Bridge(), "JonyApp");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v,
                                                    WebResourceRequest r) {
                Uri u = r.getUrl();
                return u.getHost() == null
                        || !u.getHost().endsWith("jonyos.uz");
            }

            @Override
            public void onPageFinished(WebView v, String url) {
                sync(v);
            }
        });
    }

    /**
     * ILOVA VA SAYT BITTA SESSIYADA (2026-09-25).
     *
     * 1) Ilovada kirilgandan keyin birinchi sahifada token va
     *    foydalanuvchi saytga yoziladi — examiner qayta login qilmaydi.
     * 2) Keyin sayt kuzatiladi: saytda "Chiqish" bosilsa ilova ham
     *    chiqadi va kuzatuv to'xtaydi (aks holda chiqqan odamga
     *    bildirishnoma kelaverardi); sayt yangi token olsa (login
     *    almashtirildi) kuzatuv o'sha token bilan davom etadi.
     */
    private void sync(WebView v) {
        String t = Api.token(this);
        if (t == null) {
            return;
        }
        if (Api.prefs(this).getBoolean("push_web", false)) {
            Api.prefs(this).edit().putBoolean("push_web", false).apply();
            String user = Api.prefs(this).getString("user", "{}");
            v.evaluateJavascript("(function(){try{"
                    + "sessionStorage.removeItem('jony_crm_token');"
                    + "sessionStorage.removeItem('jony_crm_user');"
                    + "localStorage.setItem('jony_crm_token',"
                    + JSONObject.quote(t) + ");"
                    + "localStorage.setItem('jony_crm_user',"
                    + JSONObject.quote(user) + ");"
                    + "location.reload();}catch(e){}})()", null);
            return;
        }
        v.evaluateJavascript("(function(){if(window.__jx)return;"
                + "window.__jx=1;var last=null;function cur(){"
                + "return localStorage.getItem('jony_crm_token')"
                + "||sessionStorage.getItem('jony_crm_token')||'';}"
                // Token bor-u, foydalanuvchi yo'q — sayt login sahifasida
                // qotib qoladi. Foydalanuvchi serverdan olinib yoziladi.
                + "var t=cur();if(t&&!localStorage.getItem('jony_crm_user')"
                + "&&!sessionStorage.getItem('jony_crm_user')){"
                + "fetch('/api/auth/me',{headers:{Authorization:'Bearer '+t}})"
                + ".then(function(r){return r.ok?r.json():null;})"
                + ".then(function(u){if(!u)return;"
                + "localStorage.setItem('jony_crm_user',JSON.stringify({"
                + "full_name:u.full_name,role:u.role,branch_id:u.branch_id}));"
                + "location.replace('/');}).catch(function(){});}"
                + "function tick(){var w=cur();if(w!==last){last=w;"
                + "JonyApp.webToken(w);}}tick();setInterval(tick,1500);"
                + "})()", null);
    }

    /** Saytdan keladigan xabar (faqat jonyos.uz sahifalari ochiladi). */
    private final class Bridge {
        @JavascriptInterface
        public void webToken(String w) {
            new Handler(Looper.getMainLooper()).post(() -> {
                if (Api.token(MainActivity.this) == null) {
                    return;
                }
                if (w == null || w.isEmpty()) {
                    Api.clear(MainActivity.this);
                    WatchService.stop(MainActivity.this);
                    web.setVisibility(View.GONE);
                    login.setVisibility(View.VISIBLE);
                } else if (!w.equals(Api.token(MainActivity.this))) {
                    Api.adoptToken(MainActivity.this, w);
                }
            });
        }
    }

    /** Orqaga: avval sahifada orqaga, keyin ilovadan chiqish. */
    private void goBack() {
        if (web.getVisibility() == View.VISIBLE && web.canGoBack()) {
            web.goBack();
        } else {
            // Yopilmaydi — orqa fonga o'tadi, kuzatuv baribir ishlaydi
            moveTaskToBack(true);
        }
    }

    // Android 13+ (ayniqsa 16): orqaga SURISH onBackPressed ni
    // chaqirmaydi — shu sababli tizim chaqiruvi alohida ro'yxatdan
    // o'tkaziladi. Aks holda surish sahifada orqaga qaytmay, ilovani
    // yopib yuborardi.
    private void setupBack() {
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::goBack);
        }
    }

    @SuppressLint("GestureBackNavigation") // 33+ da setupBack ishlaydi
    @Override
    public void onBackPressed() {
        goBack();
    }
}
