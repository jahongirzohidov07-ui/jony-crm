package uz.jonyos.jonystudent;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;

import java.util.ArrayList;


/**
 * NUTQNI TANISH (2026-10-07).
 *
 * <p>Android WebView brauzerning SpeechRecognition'ini bermaydi, shuning
 * uchun speaking mashqidagi "gapirganingiz matnga aylansin" qismi
 * telefonning o'z nutq tanish xizmati orqali ishlaydi. Natija sahifaga
 * window.__jonySr(id, tur, matn) bilan qaytadi (lib/nativeBridge.ts).
 * Bir vaqtda bitta tinglash â€” yangisi boshlansa eskisi to'xtaydi.
 */
final class SpeechBridge {

    private final Context ctx;
    /** Sahifaga JS yuboruvchi (API 23 da java.util.function yo'q). */
    interface Js {
        void accept(String code);
    }

    private final Js js;
    private SpeechRecognizer rec;
    private String currentId;

    SpeechBridge(Context ctx, Js js) {
        this.ctx = ctx;
        this.js = js;
    }

    private void emit(String id, String type, String text) {
        js.accept("window.__jonySr&&window.__jonySr(" + MainActivity.q(id) + ","
                + MainActivity.q(type) + "," + MainActivity.q(text) + ")");
    }

    void start(String id, String lang, boolean interim) {
        if (!SpeechRecognizer.isRecognitionAvailable(ctx)) {
            emit(id, "error", "service-not-allowed");
            emit(id, "end", "");
            return;
        }
        if (currentId != null) {
            String old = currentId;
            stopInternal();
            emit(old, "end", "");
        }
        currentId = id;
        try {
            rec = SpeechRecognizer.createSpeechRecognizer(ctx);
        } catch (Exception e) {
            currentId = null;
            emit(id, "error", "service-not-allowed");
            emit(id, "end", "");
            return;
        }
        rec.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                emit(id, "start", "");
            }

            @Override
            public void onBeginningOfSpeech() {
            }

            @Override
            public void onRmsChanged(float rmsdB) {
            }

            @Override
            public void onBufferReceived(byte[] buffer) {
            }

            @Override
            public void onEndOfSpeech() {
            }

            @Override
            public void onError(int error) {
                String code;
                switch (error) {
                    case SpeechRecognizer.ERROR_NO_MATCH:
                    case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:
                        code = "no-speech";
                        break;
                    case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:
                        code = "not-allowed";
                        break;
                    case SpeechRecognizer.ERROR_AUDIO:
                        code = "audio-capture";
                        break;
                    default:
                        code = "network";
                }
                emit(id, "error", code);
                finish(id);
            }

            @Override
            public void onResults(Bundle results) {
                String t = first(results);
                if (t != null) {
                    emit(id, "final", t);
                }
                finish(id);
            }

            @Override
            public void onPartialResults(Bundle partial) {
                String t = first(partial);
                if (interim && t != null && !t.isEmpty()) {
                    emit(id, "partial", t);
                }
            }

            @Override
            public void onEvent(int eventType, Bundle params) {
            }
        });
        Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        i.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang == null || lang.isEmpty() ? "en-US" : lang);
        i.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, interim);
        i.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
        i.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, ctx.getPackageName());
        try {
            rec.startListening(i);
        } catch (Exception e) {
            emit(id, "error", "audio-capture");
            finish(id);
        }
    }

    private static String first(Bundle b) {
        if (b == null) {
            return null;
        }
        ArrayList<String> list = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        return list == null || list.isEmpty() ? null : list.get(0);
    }

    private void finish(String id) {
        if (id.equals(currentId)) {
            stopInternal();
        }
        emit(id, "end", "");
    }

    void stop(String id) {
        if (rec != null && id != null && id.equals(currentId)) {
            try {
                rec.stopListening(); // natija onResults orqali keladi
            } catch (Exception ignored) {
                finish(id);
            }
        }
    }

    private void stopInternal() {
        currentId = null;
        if (rec != null) {
            try {
                rec.destroy();
            } catch (Exception ignored) {
                // allaqachon yopilgan
            }
            rec = null;
        }
    }

    void destroy() {
        stopInternal();
    }
}
