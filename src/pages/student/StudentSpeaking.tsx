import { StudentSymbol, type StudentSymbolName } from "../../components/StudentSymbol";
import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, GraduationCap, Mic, Volume2, VolumeX,
} from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY TEACHER — AI SPEAKING PARTNER (2026-08-18).
 *
 * Jahongir: "practice uchun AI speaking partner qoshish kerak savollar
 * bersa, savol berib koproq oquvchini gapirtiradigan Jony Teacher
 * nomi bilan".
 *
 * Ishlashi: bola mavzu tanlaydi -> Jony Teacher salomlashib birinchi
 * savolni beradi -> bola MIKROFONGA gapiradi (yoki yozadi) -> Teacher
 * qisqa javob berib YANA savol beradi. Har javob ovoz bilan o'qib
 * beriladi (o'chirsa bo'ladi). Har mazmunli javob +1 XP (kuniga 10).
 */

const TOPICS: { key: string; label: string; icon: StudentSymbolName }[] = [
  { key: "My day", icon: "day", label: "Mening kunim" },
  { key: "My family", icon: "family", label: "Oilam" },
  { key: "School", icon: "school", label: "Maktab" },
  { key: "Hobbies", icon: "hobbies", label: "Sevimli mashg'ulot" },
  { key: "Food", icon: "food", label: "Ovqatlar" },
  { key: "Travel", icon: "travel", label: "Sayohat" },
  { key: "Animals", icon: "animals", label: "Hayvonlar" },
  { key: "Free talk", icon: "chat", label: "Erkin suhbat" },
];

type Msg = { role: "teacher" | "student"; text: string };

export default function StudentSpeaking() {
  const [topic, setTopic] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [retryTurn, setRetryTurn] = useState<{ history: Msg[]; topic: string } | null>(null);
  const turnId = useRef(0);
  const [err, setErr] = useState("");
  const [listening, setListening] = useState(false);
  const [voiceOn, setVoiceOn] = useState(true);
  const [xpToday, setXpToday] = useState<number | null>(null);
  const [xpCap, setXpCap] = useState(10);
  const recRef = useRef<Any>(null);
  const voiceOnRef = useRef(true);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    voiceOnRef.current = voiceOn;
    if (!voiceOn) window.speechSynthesis?.cancel();
  }, [voiceOn]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  useEffect(() => () => {
    turnId.current += 1;
    window.speechSynthesis?.cancel();
    try { recRef.current?.abort(); } catch { /* bo'sh */ }
  }, []);

  function speak(text: string) {
    if (!voiceOnRef.current || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    // Qavsdagi tuzatishlar o'qilmasin — bola asosiy gapni eshitsin
    const clean = text.replace(/\([^)]*\)/g, "");
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = "en-US";
    u.rate = 0.92;
    const vs = window.speechSynthesis.getVoices();
    // Jony Teacher ERKAK ovozda gapiradi (2026-08-18, Jahongir:
    // "ovozi qizlarniki men o'gil bolaman jony teacher"). Qurilmada
    // qaysi erkak ovoz bo'lsa o'sha tanlanadi; topilmasa - past
    // tembr bilan har qanday inglizcha ovoz.
    const male = vs.find((x) => x.lang?.startsWith("en") &&
      /male|david|daniel|george|guy|james|ryan|alex|fred|uk english male|us english male/i
        .test(x.name) && !/female/i.test(x.name));
    const v = male || vs.find((x) => x.lang?.startsWith("en"));
    if (v) u.voice = v;
    if (!male) u.pitch = 0.75; // erkak ovoz topilmasa pastroq tembr
    window.speechSynthesis.speak(u);
  }

  async function turn(history: Msg[], chosenTopic: string) {
    const id = ++turnId.current;
    setBusy(true);
    setErr("");
    setRetryTurn(null);
    try {
      const r = await api.post<Any>("/student/speaking", {
        topic: chosenTopic,
        messages: history,
      });
      if (id !== turnId.current) return;
      const reply = String(r.reply || "").trim();
      if (!reply) throw new Error("Jony Teacher javobi bo‘sh keldi. Qayta urinib ko‘ring.");
      setMsgs([...history, { role: "teacher", text: reply }]);
      setXpToday(r.xp_today ?? null);
      if (r.xp_cap) setXpCap(r.xp_cap);
      speak(reply);
    } catch (e) {
      if (id !== turnId.current) return;
      setErr(e instanceof Error ? e.message : "Xatolik");
      setRetryTurn({ history, topic: chosenTopic });
      setMsgs(history);
    } finally {
      if (id === turnId.current) setBusy(false);
    }
  }

  function start(t: string) {
    setTopic(t);
    setMsgs([]);
    turn([], t);
  }

  // FAQAT GAPIRISH (2026-08-18, Jahongir: "Bu jony teacherga faqat
  // gapirish kerak yozish mumkin bo'lmasin") — matn maydoni yo'q,
  // bu funksiya faqat mikrofondan kelgan matn bilan chaqiriladi.
  function sendSpoken(text: string) {
    const clean = text.trim();
    if (!clean || busy || !topic) return;
    const next: Msg[] = [...msgs, { role: "student", text: clean }];
    setMsgs(next);
    turn(next, topic);
  }

  function startMic() {
    const SR =
      (window as Any).SpeechRecognition ||
      (window as Any).webkitSpeechRecognition;
    if (!SR) {
      setErr("Bu qurilma ovozni matnga aylantirishni qo'llamaydi. " +
             "Android Chrome yoki iPhone Safari'da ochib ko'ring.");
      return;
    }
    if (listening) {
      try { recRef.current?.stop(); } catch { /* bo'sh */ }
      return;
    }
    window.speechSynthesis?.cancel();
    setErr("");
    const rec = new SR();
    recRef.current = rec;
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    setListening(true);
    rec.onresult = (e: Any) => {
      const t = e.results[0][0].transcript;
      setListening(false);
      sendSpoken(t);
    };
    rec.onerror = (e: Any) => {
      setListening(false);
      const errors: Record<string, string> = { "not-allowed": "Mikrofonga ruxsat berilmagan. Brauzer sozlamalaridan ruxsat bering.", "audio-capture": "Mikrofon topilmadi. Qurilmani tekshiring.", "no-speech": "Ovoz eshitilmadi. Mikrofonni bosib yana gapiring.", "network": "Ovozni aniqlash xizmati javob bermadi. Internetni tekshirib qayta urinib ko‘ring." };
      if (e.error !== "aborted") setErr(errors[e.error] || "Ovozni aniqlab bo‘lmadi. Qayta urinib ko‘ring.");
    };
    rec.onend = () => setListening(false);
    try { rec.start(); } catch { setListening(false); setErr("Mikrofonni ishga tushirib bo‘lmadi. Qayta urinib ko‘ring."); }
  }

  /* ═══════════════ MAVZU TANLASH (speaking.png, 2026-08-21:
     Jahongir "hammasini 1ga 1 qilib ber") ═══════════════ */
  if (!topic) {
    const card = { background: "#0c2258", borderColor: "#35538c" };
    return (
      <div className="max-w-md mx-auto px-4 pt-5 pb-8">
        <div className="flex items-center gap-2.5">
          <Link to="/student/games"
            className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
            style={card}>
            <ArrowLeft size={18} />
          </Link>
          <span className="text-[15px] font-semibold text-slate-300 flex-1">
            O'rganish
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 border shrink-0"
                style={card}>
            <span className="text-brand-300 text-sm font-bold">
              Har javob +1 XP
            </span>
          </span>
        </div>

        <div className="flex items-start gap-2 mt-4">
          <div className="flex-1 min-w-0">
            <h1 className="text-[40px] font-extrabold text-white leading-none">
              Jony Teacher
            </h1>
            <p className="text-[16px] text-slate-400 mt-2">
              AI speaking partner
            </p>
            <span className="inline-block mt-2 px-2.5 py-1 rounded-lg bg-amber-400 text-slate-900 text-[11px] font-extrabold tracking-wide">
              YANGI
            </span>
          </div>
          <StudentImage src="/jsicons/learn-jony-teacher.png" alt=""
               className="w-[88px] h-[88px] shrink-0" />
        </div>

        <div className="student-panel bg-white rounded-3xl p-4 mt-4">
          <div className="flex items-center gap-3">
            <span className="w-11 h-11 rounded-full bg-violet-100 flex items-center justify-center text-[20px] shrink-0">
              <StudentSymbol name="chat" tone="violet" />
            </span>
            <p className="text-[19px] font-extrabold text-slate-900">
              Qaysi mavzuda gaplashamiz?
            </p>
          </div>
          <p className="text-sm text-slate-500 mt-2">
            Jony Teacher savol beradi, siz ingliz tilida javob berasiz.
          </p>
          <p className="mt-3 rounded-xl bg-slate-50 px-3 py-2.5 text-[13px] text-slate-600 flex items-center gap-2 flex-wrap">
            <span className="font-bold text-violet-600">
              ⬡ Har javob +1 XP
            </span>
            <span className="text-slate-300">·</span>
            <span>Kunlik limit <b>{xpCap} XP</b></span>
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-3">
          {TOPICS.map((t, i) => (
            <button key={t.key} onClick={() => start(t.key)}
              className={`student-panel student-topic-card bg-white rounded-3xl p-4 text-left active:scale-[0.98] transition ${
                i === 0 ? "ring-2 ring-violet-500 shadow-[0_0_22px_rgba(124,92,240,0.45)]" : ""}`}>
              <StudentSymbol name={t.icon} tone={(["blue", "violet", "amber", "green"] as const)[i % 4]} />
              <p className="text-[15px] font-extrabold text-slate-900 leading-snug">
                {t.label}
              </p>
              {i === 0 && (
                <span className="inline-block mt-2 px-2.5 py-1 rounded-lg bg-violet-600 text-white text-[11px] font-bold">
                  Tavsiya
                </span>
              )}
            </button>
          ))}
        </div>

        <button onClick={() => start(TOPICS[0].key)}
          className="mt-4 w-full py-4 rounded-2xl bg-brand-600 text-white text-[17px] font-bold">
          Suhbatni boshlash
        </button>
      </div>
    );
  }

  /* ═══════════════ SUHBAT ═══════════════ */
  return (
    <div className="flex flex-col h-[100dvh]" style={{ background: "#0A1233" }}>
      <div className="px-4 pt-4 pb-3 shrink-0 text-white border-b"
           style={{ borderColor: "#1D2A63" }}>
        <div className="max-w-md mx-auto flex items-center gap-2.5">
          <button onClick={() => { turnId.current += 1; window.speechSynthesis?.cancel(); recRef.current?.abort(); setListening(false); setBusy(false); setRetryTurn(null); setErr(""); setTopic(null); setMsgs([]); }} aria-label="Mavzularga qaytish"
            className="p-1 -ml-1 text-white/85">
            <ArrowLeft size={19} />
          </button>
          <StudentImage src="/jsicons/learn-jony-teacher.png" alt=""
               className="w-10 h-10 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold leading-tight">Jony Teacher</p>
            <p className="text-[11px] truncate">
              <span className={err ? "text-amber-300" : "text-emerald-400"}>{err ? "● Ulanish xatosi" : busy ? "● Javob tayyorlanmoqda" : "● Suhbat"}</span>{"  "}
              <span className="text-white/60">
              {TOPICS.find((t) => t.key === topic)?.label || topic}
              {xpToday !== null && ` · Bugun +${xpToday}/${xpCap} XP`}
              </span>
            </p>
          </div>
          <button aria-label={voiceOn ? "Ovozni o‘chirish" : "Ovozni yoqish"} onClick={() => setVoiceOn(!voiceOn)}
            className="p-2 rounded-lg bg-white/10">
            {voiceOn ? <Volume2 size={17} /> : <VolumeX size={17} />}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="max-w-md mx-auto space-y-2.5">
          {msgs.map((m, i) => (
            <div key={i}
              className={`flex ${m.role === "student" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap ${
                m.role === "student"
                  ? "bg-brand-600 text-white rounded-br-md"
                  : "bg-white text-slate-900 rounded-bl-md text-[16px] font-semibold"
              }`}>
                {m.role === "teacher" && (
                  <button onClick={() => speak(m.text)}
                    className="float-right ml-2 mt-0.5 text-slate-400">
                    <Volume2 size={14} />
                  </button>
                )}
                {m.text}
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex justify-start">
              <div className="student-panel bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:120ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:240ms]" />
                </span>
              </div>
            </div>
          )}
          {err && (
            <p className="text-center text-xs font-semibold text-red-600 bg-red-50 rounded-xl px-3 py-2">
              {err}
            </p>
          )}
          {retryTurn && !busy && <button onClick={() => turn(retryTurn.history, retryTurn.topic)} className="min-h-11 px-5 py-3 rounded-xl bg-brand-600 text-white font-bold">Qayta urinish</button>}
          <div ref={endRef} />
        </div>
      </div>

      {/* FAQAT MIKROFON — yozish yo'q (Jahongir: "faqat gapirish
          kerak yozish mumkin bo'lmasin"). Speaking mashqi yozish
          bilan aldab bo'lmaydigan bo'ldi. */}
      <div className="shrink-0 px-3 pt-3 pb-[max(0.875rem,env(safe-area-inset-bottom))] border-t"
           style={{ borderColor: "#1D2A63" }}>
        <div className="max-w-md mx-auto flex flex-col items-center gap-2">
          <button onClick={startMic} disabled={busy || !!retryTurn} aria-label={listening ? "Yozishni to‘xtatish" : "Mikrofonni yoqish"}
            className={`w-24 h-24 rounded-full flex items-center justify-center transition ${
              listening
                ? "bg-red-500 text-white animate-pulse"
                : "bg-brand-600 text-white active:bg-brand-700"
            } disabled:opacity-40`}
            style={{ boxShadow: listening
              ? "0 0 40px rgba(239,68,68,0.6)"
              : "0 0 44px rgba(63,131,248,0.65)" }}>
            <Mic size={38} />
          </button>
          <p className="text-[14px] font-bold text-white text-center leading-snug">
            {busy ? "Jony Teacher o'ylayapti..."
              : listening ? "Gapiring... to'xtatish uchun bosing"
                : "Mikrofonni bosib, inglizcha javob bering"}
          </p>
          <div className="w-full grid grid-cols-3 gap-1 rounded-2xl border px-2 py-2.5 mt-1"
               style={{ background: "#0c2258", borderColor: "#35538c" }}>
            <p className="text-center">
              <span className={`text-[12px] font-bold ${
                listening ? "text-emerald-400" : "text-slate-300"}`}>
                ● Tinglayapti
              </span>
              <span className="block text-[10px] text-slate-500">
                Mikrofon yoqilganda
              </span>
            </p>
            <p className="text-center border-x" style={{ borderColor: "#35538c" }}>
              <span className="text-[12px] font-bold text-violet-300">
                ıılı Gap tahlili
              </span>
              <span className="block text-[10px] text-slate-500">
                Javobingiz tahlil qilinadi
              </span>
            </p>
            <p className="text-center">
              <span className="text-[12px] font-bold text-amber-400">
                ⭐ +1 XP
              </span>
              <span className="block text-[10px] text-slate-500">
                javob uchun
              </span>
            </p>
          </div>
        </div>
      </div>
      <span className="hidden"><GraduationCap size={1} /></span>
    </div>
  );
}
