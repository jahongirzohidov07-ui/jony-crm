package uz.jonyos.jonystudent;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.content.FileProvider;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import org.json.JSONObject;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/**
 * JONY STUDENT — 2-versiya (2026-10-07).
 *
 * <p>Sayt (jonyos.uz/student) ilovaning O'Z WebView'ida ochiladi.
 * Ilova qo'shadigani:
 * <ul>
 *   <li>FLAG_SECURE — butun ilovada skrinshot, ekran yozish va ekranni
 *       uzatish bloklanadi;</li>
 *   <li>JonyApp ko'prigi — ovoz chiqarib o'qish (TTS), nutqni tanish
 *       (SpeechBridge), imtihonda ekranni qulflash;</li>
 *   <li>fon bildirishnomalari (NotifyWorker, har 15 daqiqada);</li>
 *   <li>offline: saytning servis workeri qobiqni saqlaydi, birinchi
 *       ochilish internetsiz bo'lsa — tushuntirish ekrani.</li>
 * </ul>
 */
public class MainActivity extends Activity {

    static final String HOME = "https://jonyos.uz/student?pwa=1";
    static final List<String> HOSTS = Arrays.asList(
            "jonyos.uz", "www.jonyos.uz", "jony-crm.vercel.app");

    private static final int REQ_FILE = 41;
    private static final int REQ_AUDIO = 42;
    private static final int REQ_NOTIFY = 43;

    private WebView web;
    private View offlineView;
    private SharedPreferences prefs;

    private ValueCallback<Uri[]> fileCallback;
    private Uri photoUri;
    private PermissionRequest pendingWebPermission;
    private Runnable pendingAudioAction;

    private TextToSpeech tts;
    private boolean ttsReady = false;
    private String[] pendingSpeak;
    private SpeechBridge speech;

    private boolean locked = false;
    private boolean mainFrameFailed = false;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        // SKRINSHOT BLOKI — butun oynaga, ilova ochilgan zahoti.
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE,
                WindowManager.LayoutParams.FLAG_SECURE);
        prefs = getSharedPreferences("jony", MODE_PRIVATE);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);
        web = new WebView(this);
        root.addView(web, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        offlineView = buildOfflineView();
        offlineView.setVisibility(View.GONE);
        root.addView(offlineView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);

        // Android 15+ ekran chetigacha chizadi — sahifa status bar
        // ostida qolmasin.
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        new WindowInsetsControllerCompat(getWindow(), root).setAppearanceLightStatusBars(true);
        ViewCompat.setOnApplyWindowInsetsListener(root, (v, insets) -> {
            Insets b = insets.getInsets(WindowInsetsCompat.Type.systemBars()
                    | WindowInsetsCompat.Type.ime());
            v.setPadding(b.left, b.top, b.right, b.bottom);
            return WindowInsetsCompat.CONSUMED;
        });

        setupWeb();
        // Android 13+ (va 16 dagi "predictive back") — orqaga tugmasi
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                    this::handleBack);
        }
        speech = new SpeechBridge(this, this::js);
        Notifier.ensureChannel(this);
        NotifyWorker.schedule(this);
        askNotificationPermissionOnce();

        String start = urlFromIntent(getIntent());
        web.loadUrl(start != null ? start : HOME);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        String u = urlFromIntent(intent);
        if (u != null) {
            web.loadUrl(u);
        }
    }

    /** Havoladan (yoki bildirishnomadan) kelgan manzil — faqat o'z saytimiz. */
    private String urlFromIntent(Intent intent) {
        if (intent == null) {
            return null;
        }
        String extra = intent.getStringExtra("url");
        Uri u = extra != null ? Uri.parse(extra) : intent.getData();
        if (u == null || !"https".equals(u.getScheme()) || u.getHost() == null
                || !HOSTS.contains(u.getHost())) {
            return null;
        }
        String s = u.toString();
        if (s.contains("/student") && !s.contains("pwa=1")) {
            s += (s.contains("?") ? "&" : "?") + "pwa=1";
        }
        return s;
    }

    // ------------------------------------------------------ WebView

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    private void setupWeb() {
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportMultipleWindows(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setUserAgentString(s.getUserAgentString() + " JonyStudentApp/2");
        CookieManager.getInstance().setAcceptCookie(true);
        web.addJavascriptInterface(new Bridge(), "JonyApp");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                String scheme = u.getScheme();
                if ("https".equals(scheme) && u.getHost() != null && HOSTS.contains(u.getHost())) {
                    return false; // o'z saytimiz — ilova ichida
                }
                if (locked) {
                    return true; // imtihon paytida tashqariga chiqilmaydi
                }
                openExternal(u, r.getUrl().toString());
                return true;
            }

            @Override
            public void onPageStarted(WebView v, String url, android.graphics.Bitmap f) {
                mainFrameFailed = false;
            }

            @Override
            public void onPageFinished(WebView v, String url) {
                if (!mainFrameFailed) {
                    offlineView.setVisibility(View.GONE);
                }
                saveToken();
            }

            @Override
            public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                if (r.isForMainFrame()) {
                    // Servis worker keshida ham yo'q — birinchi ochilish
                    // internetsiz bo'ldi.
                    mainFrameFailed = true;
                    offlineView.setVisibility(View.VISIBLE);
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb,
                                             FileChooserParams params) {
                return chooseFile(cb, params);
            }

            @Override
            public void onPermissionRequest(PermissionRequest request) {
                runOnUiThread(() -> handleWebPermission(request));
            }
        });
    }

    private void openExternal(Uri u, String raw) {
        try {
            Intent i;
            if ("intent".equals(u.getScheme())) {
                i = Intent.parseUri(raw, Intent.URI_INTENT_SCHEME);
                if (getPackageName().equals(i.getPackage())) {
                    String data = i.getDataString();
                    if (data != null) {
                        web.loadUrl(data);
                    }
                    return;
                }
                i.addCategory(Intent.CATEGORY_BROWSABLE);
                i.setComponent(null);
            } else {
                i = new Intent(Intent.ACTION_VIEW, u);
            }
            startActivity(i);
        } catch (Exception ignored) {
            Toast.makeText(this, "Havolani ochib bo'lmadi", Toast.LENGTH_SHORT).show();
        }
    }

    /** Sahifadagi login tokenini fon bildirishnomalari uchun saqlaymiz. */
    private void saveToken() {
        web.evaluateJavascript(
                "(function(){try{return localStorage.getItem('jony_crm_token')"
                        + "||sessionStorage.getItem('jony_crm_token')||'';}catch(e){return '';}})()",
                value -> {
                    String t = "";
                    try {
                        // evaluateJavascript JSON-satr qaytaradi
                        t = new JSONObject("{\"v\":" + value + "}").optString("v", "");
                    } catch (Exception ignored) {
                        // bo'sh qoladi
                    }
                    String old = prefs.getString("token", "");
                    if (!t.equals(old)) {
                        prefs.edit().putString("token", t).apply();
                        if (!t.isEmpty()) {
                            NotifyWorker.kick(this);
                        }
                    }
                });
    }

    // ------------------------------------------------- fayl / kamera

    private boolean chooseFile(ValueCallback<Uri[]> cb, WebChromeClient.FileChooserParams params) {
        if (fileCallback != null) {
            fileCallback.onReceiveValue(null);
        }
        fileCallback = cb;
        photoUri = null;
        try {
            Intent camera = null;
            File dir = new File(getCacheDir(), "photos");
            if (dir.exists() || dir.mkdirs()) {
                File f = new File(dir, "img_" + System.currentTimeMillis() + ".jpg");
                photoUri = FileProvider.getUriForFile(this, getPackageName() + ".files", f);
                camera = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                camera.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
                camera.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            }
            Intent pick;
            if (params != null && params.isCaptureEnabled() && camera != null) {
                // Imtihondagi yuz surati: faqat kamera (old kamera)
                camera.putExtra("android.intent.extras.CAMERA_FACING", 1);
                camera.putExtra("android.intent.extra.USE_FRONT_CAMERA", true);
                pick = camera;
            } else {
                Intent content = new Intent(Intent.ACTION_GET_CONTENT);
                content.addCategory(Intent.CATEGORY_OPENABLE);
                content.setType("image/*");
                pick = Intent.createChooser(content, "Rasm tanlang");
                if (camera != null) {
                    pick.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{camera});
                }
            }
            startActivityForResult(pick, REQ_FILE);
            return true;
        } catch (ActivityNotFoundException e) {
            fileCallback = null;
            Toast.makeText(this, "Kamera ochilmadi", Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != REQ_FILE || fileCallback == null) {
            return;
        }
        Uri[] result = null;
        if (res == RESULT_OK) {
            if (data != null && data.getData() != null) {
                result = new Uri[]{data.getData()};
            } else if (photoUri != null) {
                result = new Uri[]{photoUri};
            }
        }
        fileCallback.onReceiveValue(result);
        fileCallback = null;
    }

    // ------------------------------------------------- ruxsatlar

    private void handleWebPermission(PermissionRequest request) {
        boolean wantsAudio = false;
        for (String r : request.getResources()) {
            if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r)) {
                wantsAudio = true;
            }
        }
        if (!wantsAudio) {
            request.deny();
            return;
        }
        if (hasAudio()) {
            request.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
        } else {
            pendingWebPermission = request;
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_AUDIO);
        }
    }

    boolean hasAudio() {
        return checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED;
    }

    /** Mikrofon kerak bo'lgan amal — ruxsat bo'lmasa avval so'raladi. */
    void withAudio(Runnable action, Runnable denied) {
        if (hasAudio()) {
            action.run();
            return;
        }
        pendingAudioAction = () -> {
            if (hasAudio()) {
                action.run();
            } else {
                denied.run();
            }
        };
        requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_AUDIO);
    }

    private void askNotificationPermissionOnce() {
        if (Build.VERSION.SDK_INT < 33 || prefs.getBoolean("asked_notify", false)) {
            return;
        }
        prefs.edit().putBoolean("asked_notify", true).apply();
        if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIFY);
        }
    }

    @Override
    public void onRequestPermissionsResult(int req, String[] perms, int[] results) {
        super.onRequestPermissionsResult(req, perms, results);
        if (req != REQ_AUDIO) {
            return;
        }
        boolean ok = hasAudio();
        if (pendingWebPermission != null) {
            if (ok) {
                pendingWebPermission.grant(
                        new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
            } else {
                pendingWebPermission.deny();
                Toast.makeText(this, "Mikrofonga ruxsat berilmadi", Toast.LENGTH_SHORT).show();
            }
            pendingWebPermission = null;
        }
        if (pendingAudioAction != null) {
            Runnable a = pendingAudioAction;
            pendingAudioAction = null;
            a.run();
        }
    }

    // ------------------------------------------------- JS yordamchi

    /** Sahifadagi funksiyani UI oqimida chaqiradi. */
    void js(String code) {
        runOnUiThread(() -> web.evaluateJavascript(code, null));
    }

    static String q(String s) {
        return JSONObject.quote(s == null ? "" : s);
    }

    // ------------------------------------------------- TTS

    private void ensureTts() {
        if (tts != null) {
            return;
        }
        tts = new TextToSpeech(this, status -> {
            ttsReady = status == TextToSpeech.SUCCESS;
            if (ttsReady && pendingSpeak != null) {
                String[] p = pendingSpeak;
                pendingSpeak = null;
                speakNow(p[0], p[1], p[2], Float.parseFloat(p[3]), Float.parseFloat(p[4]));
            } else if (!ttsReady && pendingSpeak != null) {
                js("window.__jonyTts&&window.__jonyTts(" + q(pendingSpeak[0]) + ",'error')");
                pendingSpeak = null;
            }
        });
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override
            public void onStart(String id) {
                js("window.__jonyTts&&window.__jonyTts(" + q(id) + ",'start')");
            }

            @Override
            public void onDone(String id) {
                js("window.__jonyTts&&window.__jonyTts(" + q(id) + ",'end')");
            }

            @Override
            public void onError(String id) {
                js("window.__jonyTts&&window.__jonyTts(" + q(id) + ",'error')");
            }

            @Override
            public void onStop(String id, boolean interrupted) {
                js("window.__jonyTts&&window.__jonyTts(" + q(id) + ",'end')");
            }
        });
    }

    private void speakNow(String id, String text, String lang, float rate, float pitch) {
        try {
            Locale loc = Locale.forLanguageTag(lang == null || lang.isEmpty() ? "en-US" : lang);
            int r = tts.setLanguage(loc);
            if (r == TextToSpeech.LANG_MISSING_DATA || r == TextToSpeech.LANG_NOT_SUPPORTED) {
                tts.setLanguage(Locale.US);
            }
            tts.setSpeechRate(Math.max(0.3f, Math.min(rate, 2.5f)));
            tts.setPitch(Math.max(0.5f, Math.min(pitch, 2f)));
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, id);
        } catch (Exception e) {
            js("window.__jonyTts&&window.__jonyTts(" + q(id) + ",'error')");
        }
    }

    // ------------------------------------------------- ko'prik

    /** Sahifa shu orqali ilovaga gapiradi (lib/nativeBridge.ts, ExamTake). */
    private class Bridge {

        @JavascriptInterface
        public boolean isNative() {
            return true;
        }

        @JavascriptInterface
        public boolean isApp() {
            return true;
        }

        @JavascriptInterface
        public String version() {
            return "2";
        }

        @JavascriptInterface
        public void speak(String id, String text, String lang, double rate, double pitch) {
            runOnUiThread(() -> {
                ensureTts();
                if (ttsReady) {
                    speakNow(id, text, lang, (float) rate, (float) pitch);
                } else {
                    pendingSpeak = new String[]{id, text, lang,
                            String.valueOf((float) rate), String.valueOf((float) pitch)};
                }
            });
        }

        @JavascriptInterface
        public void stopSpeaking() {
            runOnUiThread(() -> {
                pendingSpeak = null;
                if (tts != null) {
                    tts.stop();
                }
            });
        }

        @JavascriptInterface
        public void startListening(String id, String lang, boolean interim) {
            runOnUiThread(() -> withAudio(
                    () -> speech.start(id, lang, interim),
                    () -> {
                        js("window.__jonySr&&window.__jonySr(" + q(id) + ",'error','not-allowed')");
                        js("window.__jonySr&&window.__jonySr(" + q(id) + ",'end')");
                    }));
        }

        @JavascriptInterface
        public void stopListening(String id) {
            runOnUiThread(() -> speech.stop(id));
        }

        @JavascriptInterface
        public void examStarted() {
            runOnUiThread(() -> {
                String bad = DeviceCheck.problem();
                if (bad != null) {
                    Toast.makeText(MainActivity.this, bad, Toast.LENGTH_LONG).show();
                    web.loadUrl(HOME);
                    return;
                }
                setLocked(true);
            });
        }

        @JavascriptInterface
        public void examFinished() {
            runOnUiThread(() -> setLocked(false));
        }
    }

    private void setLocked(boolean on) {
        if (locked == on) {
            return;
        }
        locked = on;
        try {
            if (on) {
                startLockTask();
            } else {
                stopLockTask();
            }
        } catch (Exception ignored) {
            // Ba'zi telefonlarda qulflash yo'q — chiqishni sahifa qayd qiladi
        }
    }

    // ------------------------------------------------- offline ekran

    private View buildOfflineView() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setBackgroundColor(Color.WHITE);
        int pad = (int) (32 * getResources().getDisplayMetrics().density);
        box.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText(R.string.offline_title);
        title.setTextSize(22);
        title.setTextColor(Color.parseColor("#0F172A"));
        title.setGravity(Gravity.CENTER);
        box.addView(title);

        TextView body = new TextView(this);
        body.setText(R.string.offline_body);
        body.setTextSize(15);
        body.setTextColor(Color.parseColor("#475569"));
        body.setGravity(Gravity.CENTER);
        body.setPadding(0, pad / 2, 0, pad / 2);
        box.addView(body);

        Button retry = new Button(this);
        retry.setText(R.string.retry);
        retry.setOnClickListener(v -> {
            offlineView.setVisibility(View.GONE);
            String cur = web.getUrl();
            web.loadUrl(cur != null && !cur.startsWith("data:") ? cur : HOME);
        });
        box.addView(retry);
        return box;
    }

    // ------------------------------------------------- hayot davri

    @Override
    protected void onPause() {
        super.onPause();
        web.onPause();
        CookieManager.getInstance().flush();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.shutdown();
        }
        speech.destroy();
        super.onDestroy();
    }

    /** Orqaga: imtihonda yopiq, aks holda sahifada orqaga, so'ng chiqish. */
    private void handleBack() {
        if (locked) {
            Toast.makeText(this, "Imtihon tugamaguncha chiqib bo'lmaydi",
                    Toast.LENGTH_SHORT).show();
            return;
        }
        if (web.canGoBack()) {
            web.goBack();
            return;
        }
        finish();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        handleBack();
    }
}
