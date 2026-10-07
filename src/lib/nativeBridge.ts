/**
 * JONY STUDENT ANDROID ILOVASI BILAN KO'PRIK (2026-10-07).
 *
 * Ilovaning 2-versiyasi saytni Chrome emas, o'zining WebView'ida
 * ochadi — shunda butun ilovada skrinshot yopiladi (Jahongir: "butun
 * app bo'yicha screenshot mumkin bo'lmasin"). Lekin Android WebView
 * brauzerning ikki imkoniyatini bermaydi:
 *   - speechSynthesis (listening'da so'zni ovoz chiqarib o'qish);
 *   - SpeechRecognition (speaking'da nutqni matnga aylantirish).
 * Ilova ularni telefonning o'z TTS va nutq tanish xizmati orqali
 * beradi (window.JonyApp), bu fayl esa saytdagi mavjud kod hech
 * o'zgarmasdan ishlashi uchun brauzer API'sining o'xshashini
 * (polyfill) qo'yadi. Oddiy brauzerda JonyApp yo'q — hech narsa
 * qilinmaydi.
 */

type Any = any; // eslint-disable-line @typescript-eslint/no-explicit-any

interface NativeApp {
  isNative?: () => boolean;
  speak?: (id: string, text: string, lang: string, rate: number, pitch: number) => void;
  stopSpeaking?: () => void;
  startListening?: (id: string, lang: string, interim: boolean) => void;
  stopListening?: (id: string) => void;
}

function nativeApp(): NativeApp | null {
  const a = (window as Any).JonyApp as NativeApp | undefined;
  try {
    return a && typeof a.isNative === "function" && a.isNative() ? a : null;
  } catch {
    return null;
  }
}

export function isNativeApp(): boolean {
  return nativeApp() !== null;
}

let seq = 0;
const nextId = (p: string) => `${p}${Date.now().toString(36)}${(seq++).toString(36)}`;

function installTts(app: NativeApp) {
  if (!app.speak) return;
  const live = new Map<string, Any>();

  class Utterance {
    text: string;
    lang = "en-US";
    rate = 1;
    pitch = 1;
    volume = 1;
    voice: Any = null;
    onstart: ((e: Any) => void) | null = null;
    onend: ((e: Any) => void) | null = null;
    onerror: ((e: Any) => void) | null = null;
    onboundary: ((e: Any) => void) | null = null;
    private listeners: Record<string, ((e: Any) => void)[]> = {};
    constructor(text = "") {
      this.text = text;
    }
    addEventListener(t: string, fn: (e: Any) => void) {
      (this.listeners[t] ||= []).push(fn);
    }
    removeEventListener(t: string, fn: (e: Any) => void) {
      this.listeners[t] = (this.listeners[t] || []).filter((f) => f !== fn);
    }
    _emit(t: string) {
      const ev = { type: t, target: this, utterance: this };
      const h = (this as Any)["on" + t];
      try { if (typeof h === "function") h(ev); } catch { /* sahifa xatosi */ }
      for (const fn of this.listeners[t] || []) {
        try { fn(ev); } catch { /* sahifa xatosi */ }
      }
    }
  }

  const queue: { id: string; u: Utterance }[] = [];
  let current: string | null = null;

  const synth: Any = {
    speaking: false,
    pending: false,
    paused: false,
    onvoiceschanged: null,
    getVoices: () => [],
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    pause: () => undefined,
    resume: () => undefined,
    speak(u: Utterance) {
      const id = nextId("t");
      live.set(id, u);
      queue.push({ id, u });
      synth.pending = queue.length > 1 || current !== null;
      if (current === null) playNext();
    },
    cancel() {
      queue.length = 0;
      const was = current;
      current = null;
      synth.speaking = false;
      synth.pending = false;
      try { app.stopSpeaking?.(); } catch { /* */ }
      if (was) {
        const u = live.get(was);
        live.delete(was);
        u?._emit("end");
      }
    },
  };

  function playNext() {
    const item = queue.shift();
    if (!item) {
      current = null;
      synth.speaking = false;
      synth.pending = false;
      return;
    }
    current = item.id;
    synth.speaking = true;
    synth.pending = queue.length > 0;
    const u = item.u;
    try {
      app.speak!(item.id, String(u.text || ""), String(u.lang || "en-US"),
                 Number(u.rate) || 1, Number(u.pitch) || 1);
    } catch {
      live.delete(item.id);
      u._emit("error");
      playNext();
    }
  }

  // Ilova shu funksiyani chaqiradi: (id, "start" | "end" | "error")
  (window as Any).__jonyTts = (id: string, type: string) => {
    const u = live.get(id);
    if (!u) return;
    if (type === "start") {
      u._emit("start");
      return;
    }
    live.delete(id);
    u._emit(type === "error" ? "error" : "end");
    if (current === id) playNext();
  };

  try {
    Object.defineProperty(window, "speechSynthesis", { value: synth, configurable: true });
  } catch {
    (window as Any).speechSynthesis = synth;
  }
  (window as Any).SpeechSynthesisUtterance = Utterance;
}

function installRecognition(app: NativeApp) {
  if (!app.startListening) return;
  const live = new Map<string, Any>();

  class Recognition {
    lang = "en-US";
    continuous = false;
    interimResults = false;
    maxAlternatives = 1;
    onresult: ((e: Any) => void) | null = null;
    onerror: ((e: Any) => void) | null = null;
    onend: ((e: Any) => void) | null = null;
    onstart: ((e: Any) => void) | null = null;
    onspeechend: ((e: Any) => void) | null = null;
    private id: string | null = null;
    private finals: string[] = [];
    start() {
      if (this.id) return;
      this.id = nextId("r");
      this.finals = [];
      live.set(this.id, this);
      try {
        app.startListening!(this.id, String(this.lang || "en-US"), !!this.interimResults);
      } catch {
        this._error("not-allowed");
      }
    }
    stop() {
      if (this.id) {
        try { app.stopListening?.(this.id); } catch { /* */ }
      }
    }
    abort() {
      this.stop();
    }
    addEventListener() { /* sahifalar on... ishlatadi */ }
    removeEventListener() { /* */ }
    _call(name: string, ev: Any) {
      const h = (this as Any)["on" + name];
      try { if (typeof h === "function") h(ev); } catch { /* sahifa xatosi */ }
    }
    _result(text: string, isFinal: boolean) {
      const mk = (t: string, fin: boolean) => {
        const alt = { transcript: t, confidence: 0.9 };
        const r: Any = [alt];
        r.isFinal = fin;
        r.length = 1;
        r.item = () => alt;
        return r;
      };
      const results: Any[] = this.finals.map((t) => mk(t, true));
      let resultIndex = results.length;
      if (isFinal) {
        this.finals.push(text);
        results.push(mk(text, true));
        resultIndex = results.length - 1;
      } else {
        results.push(mk(text, false));
        resultIndex = results.length - 1;
      }
      (results as Any).item = (i: number) => results[i];
      this._call("result", { resultIndex, results });
    }
    _error(code: string) {
      this._call("error", { error: code, message: code });
    }
    _end() {
      if (this.id) live.delete(this.id);
      this.id = null;
      this._call("end", {});
    }
  }

  // Ilova chaqiradi: (id, "start"|"partial"|"final"|"error"|"end", matn)
  (window as Any).__jonySr = (id: string, type: string, text?: string) => {
    const r = live.get(id) as Recognition | undefined;
    if (!r) return;
    if (type === "start") r._call("start", {});
    else if (type === "partial") r._result(String(text || ""), false);
    else if (type === "final") r._result(String(text || ""), true);
    else if (type === "error") r._error(String(text || "network"));
    else if (type === "end") r._end();
  };

  (window as Any).SpeechRecognition = Recognition;
  (window as Any).webkitSpeechRecognition = Recognition;
}

/** main.tsx dan bir marta chaqiriladi. */
export function installNativeBridge() {
  if (typeof window === "undefined") return;
  const app = nativeApp();
  if (!app) return;
  installTts(app);
  installRecognition(app);
  document.documentElement.classList.add("jony-native");
}
