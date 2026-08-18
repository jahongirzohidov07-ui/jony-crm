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

const TOPICS = [
  { key: "My day", label: "🌞 Mening kunim" },
  { key: "My family", label: "👨‍👩‍👧 Oilam" },
  { key: "School", label: "🏫 Maktab" },
  { key: "Hobbies", label: "⚽ Sevimli mashg'ulot" },
  { key: "Food", label: "🍕 Ovqatlar" },
  { key: "Travel", label: "✈️ Sayohat" },
  { key: "Animals", label: "🐱 Hayvonlar" },
  { key: "Free talk", label: "💬 Erkin suhbat" },
];

type Msg = { role: "teacher" | "student"; text: string };

export default function StudentSpeaking() {
  const [topic, setTopic] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
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
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<Any>("/student/speaking", {
        topic: chosenTopic,
        messages: history,
      });
      const reply = String(r.reply || "");
      setMsgs([...history, { role: "teacher", text: reply }]);
      setXpToday(r.xp_today ?? null);
      if (r.xp_cap) setXpCap(r.xp_cap);
      speak(reply);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setMsgs(history);
    } finally {
      setBusy(false);
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
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    rec.start();
  }

  /* ═══════════════ MAVZU TANLASH ═══════════════ */
  if (!topic) {
    return (
      <>
        <div className="bg-gradient-to-br from-indigo-700 to-violet-500 text-white px-4 pt-6 pb-12">
          <div className="max-w-md mx-auto">
            <Link to="/student/games"
              className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3">
              <ArrowLeft size={16} /> Mashqlar
            </Link>
            <div className="flex items-center gap-3">
              <span className="w-12 h-12 rounded-2xl bg-white/15 flex items-center justify-center text-2xl">
                🧑‍🏫
              </span>
              <div>
                <h1 className="text-xl font-bold">Jony Teacher</h1>
                <p className="text-[13px] text-white/80">
                  AI speaking partner — ingliz tilida suhbat
                </p>
              </div>
            </div>
          </div>
        </div>
        <div className="max-w-md mx-auto px-4 -mt-6 pb-24">
          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <p className="text-sm font-bold text-slate-900 mb-1">
              Qaysi mavzuda gaplashamiz?
            </p>
            <p className="text-xs text-slate-500 mb-3">
              Jony Teacher savollar beradi — siz ingliz tilida javob
              berasiz. Har javob uchun +1 XP (kuniga {xpCap} tagacha).
            </p>
            <div className="grid grid-cols-2 gap-2">
              {TOPICS.map((t) => (
                <button key={t.key} onClick={() => start(t.key)}
                  className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-[13.5px] font-semibold text-slate-800 text-left active:scale-[0.98]">
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </>
    );
  }

  /* ═══════════════ SUHBAT ═══════════════ */
  return (
    <div className="flex flex-col h-[100dvh]">
      <div className="bg-gradient-to-br from-indigo-700 to-violet-500 text-white px-4 pt-4 pb-3 shrink-0">
        <div className="max-w-md mx-auto flex items-center gap-2.5">
          <button onClick={() => { setTopic(null); setMsgs([]); }}
            className="p-1 -ml-1 text-white/85">
            <ArrowLeft size={19} />
          </button>
          <span className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center text-lg">
            🧑‍🏫
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold leading-tight">Jony Teacher</p>
            <p className="text-[11px] text-white/75 truncate">
              {TOPICS.find((t) => t.key === topic)?.label || topic}
              {xpToday !== null && ` · bugun +${xpToday}/${xpCap} XP`}
            </p>
          </div>
          <button onClick={() => setVoiceOn(!voiceOn)}
            className="p-2 rounded-lg bg-white/10">
            {voiceOn ? <Volume2 size={17} /> : <VolumeX size={17} />}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-slate-50 px-4 py-3">
        <div className="max-w-md mx-auto space-y-2.5">
          {msgs.map((m, i) => (
            <div key={i}
              className={`flex ${m.role === "student" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[14px] leading-relaxed whitespace-pre-wrap ${
                m.role === "student"
                  ? "bg-brand-600 text-white rounded-br-md"
                  : "bg-white border border-slate-200 text-slate-800 rounded-bl-md"
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
              <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3">
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
          <div ref={endRef} />
        </div>
      </div>

      {/* FAQAT MIKROFON — yozish yo'q (Jahongir: "faqat gapirish
          kerak yozish mumkin bo'lmasin"). Speaking mashqi yozish
          bilan aldab bo'lmaydigan bo'ldi. */}
      <div className="shrink-0 bg-white border-t border-slate-200 px-3 pt-3 pb-[max(0.875rem,env(safe-area-inset-bottom))]">
        <div className="max-w-md mx-auto flex flex-col items-center gap-1.5">
          <button onClick={startMic} disabled={busy}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition shadow-lg ${
              listening
                ? "bg-red-500 text-white animate-pulse"
                : "bg-brand-600 text-white active:bg-brand-700"
            } disabled:opacity-40`}>
            <Mic size={26} />
          </button>
          <p className="text-[11.5px] font-semibold text-slate-400">
            {busy ? "Jony Teacher o'ylayapti..."
              : listening ? "Gapiring... to'xtatish uchun bosing"
                : "Mikrofonni bosib, inglizcha javob bering"}
          </p>
        </div>
      </div>
      <span className="hidden"><GraduationCap size={1} /></span>
    </div>
  );
}
