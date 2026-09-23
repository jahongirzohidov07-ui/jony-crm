package uz.jonyacademy.exam;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import java.io.File;
import java.util.Arrays;
import java.util.List;

/**
 * JONY IMTIHON.
 *
 * <p>Ilova ichida CRM'dagi o'sha test sahifasi ochiladi — savollar,
 * taymer, rasm, chiqishlarni sanash hammasi o'sha yerda. Ilova
 * qo'shadigani brauzerda umuman mumkin bo'lmagan uch narsa:
 *
 * <ul>
 *   <li>FLAG_SECURE — skrinshot ham, ekran yozish ham, ekranni
 *       televizorga uzatish ham bloklanadi;</li>
 *   <li>ekran qulfi (lock task) — test ketayotganda boshqa ilovaga
 *       o'tib bo'lmaydi;</li>
 *   <li>root/emulyator tekshiruvi — bu himoyani aylanib o'tish
 *       mumkin bo'lgan qurilmalarda test ochilmaydi.</li>
 * </ul>
 */
public class MainActivity extends Activity {

    /** Test havolasi faqat shu manzillardan bo'lishi mumkin. */
    private static final List<String> HOSTS = Arrays.asList(
            "jonyos.uz", "www.jonyos.uz", "jony-crm.vercel.app",
            "jonyacademy.uz", "www.jonyacademy.uz");

    private static final int REQ_PHOTO = 41;

    private WebView web;
    private View intro;
    private EditText linkInput;
    private TextView note;

    private ValueCallback<Uri[]> fileCallback;
    private Uri photoUri;
    /** Test ketyaptimi — shunda ekran qulflanadi va orqaga chiqilmaydi. */
    private boolean locked = false;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        // SKRINSHOT BLOKI. Butun oynaga qo'yiladi: test sahifasi ham,
        // havola kiritish ekrani ham suratga tushmaydi.
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE,
                WindowManager.LayoutParams.FLAG_SECURE);
        setContentView(R.layout.activity_main);

        web = findViewById(R.id.web);
        intro = findViewById(R.id.intro);
        linkInput = findViewById(R.id.link);
        note = findViewById(R.id.note);
        Button open = findViewById(R.id.open);

        String bad = DeviceCheck.problem();
        if (bad != null) {
            linkInput.setVisibility(View.GONE);
            open.setVisibility(View.GONE);
            note.setText(bad);
            note.setVisibility(View.VISIBLE);
            return;
        }

        setupWeb();
        open.setOnClickListener(v -> openLink(linkInput.getText().toString()));

        Uri data = getIntent() != null ? getIntent().getData() : null;
        if (data != null) {
            openLink(data.toString());
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (intent != null && intent.getData() != null) {
            openLink(intent.getData().toString());
        }
    }

    // ------------------------------------------------------ havola

    private void openLink(String raw) {
        String url = raw == null ? "" : raw.trim();
        if (!url.startsWith("http")) {
            url = "https://" + url;
        }
        Uri u = Uri.parse(url);
        if (!"https".equals(u.getScheme()) || u.getHost() == null
                || !HOSTS.contains(u.getHost())) {
            note.setText("Havola noto'g'ri. Examiner bergan havolani "
                    + "to'liq nusxalab qo'ying.");
            note.setVisibility(View.VISIBLE);
            return;
        }
        note.setVisibility(View.GONE);
        intro.setVisibility(View.GONE);
        web.setVisibility(View.VISIBLE);
        web.loadUrl(u.toString());
    }

    // ------------------------------------------------------ WebView

    private void setupWeb() {
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportMultipleWindows(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        web.addJavascriptInterface(new Bridge(), "JonyApp");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v,
                                                    WebResourceRequest r) {
                // Test paytida hech qanday tashqi havolaga chiqilmaydi
                Uri u = r.getUrl();
                return u.getHost() == null || !HOSTS.contains(u.getHost());
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView v,
                                             ValueCallback<Uri[]> cb,
                                             FileChooserParams params) {
                return takePhoto(cb);
            }
        });
    }

    /** Sahifa rasm so'raganda telefonning kamerasi ochiladi. */
    private boolean takePhoto(ValueCallback<Uri[]> cb) {
        if (fileCallback != null) {
            fileCallback.onReceiveValue(null);
        }
        fileCallback = cb;
        try {
            File dir = new File(getCacheDir(), "photos");
            if (!dir.exists() && !dir.mkdirs()) {
                throw new IllegalStateException("papka yaratilmadi");
            }
            File f = new File(dir, "exam_" + System.currentTimeMillis() + ".jpg");
            photoUri = FileProvider.getUriForFile(
                    this, getPackageName() + ".files", f);
            Intent i = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            i.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
            // Old kamera (sahifada capture="user" deb so'ralgan)
            i.putExtra("android.intent.extras.CAMERA_FACING", 1);
            i.putExtra("android.intent.extra.USE_FRONT_CAMERA", true);
            i.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            startActivityForResult(i, REQ_PHOTO);
            return true;
        } catch (Exception e) {
            fileCallback = null;
            photoUri = null;
            Toast.makeText(this, "Kamera ochilmadi", Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != REQ_PHOTO) {
            return;
        }
        if (fileCallback == null) {
            return;
        }
        if (res == RESULT_OK && photoUri != null) {
            fileCallback.onReceiveValue(new Uri[]{photoUri});
        } else {
            fileCallback.onReceiveValue(null);
        }
        fileCallback = null;
    }

    // ------------------------------------------- sahifa bilan aloqa

    /**
     * Test sahifasi shu orqali ilovaga gapiradi: test boshlandi —
     * ekranni qulfla, tugadi — qo'yib yubor.
     */
    private class Bridge {

        @JavascriptInterface
        public boolean isApp() {
            return true;
        }

        @JavascriptInterface
        public void examStarted() {
            runOnUiThread(() -> setLocked(true));
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
            // Ba'zi telefonlarda qulflash o'chirib qo'yilgan — test
            // baribir davom etadi, chiqib ketish esa sahifada
            // qayd qilinadi.
        }
    }

    // ------------------------------------------------- hayot davri

    @Override
    protected void onPause() {
        super.onPause();
        web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    public void onBackPressed() {
        if (locked) {
            Toast.makeText(this, "Test tugamaguncha chiqib bo'lmaydi",
                    Toast.LENGTH_SHORT).show();
            return;
        }
        if (web.getVisibility() == View.VISIBLE && web.canGoBack()) {
            web.goBack();
            return;
        }
        super.onBackPressed();
    }
}
