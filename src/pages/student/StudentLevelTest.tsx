import { StudentImage } from "../../components/StudentIcon";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Volume2, X } from "lucide-react";
import { api } from "../../lib/api";
import { JSA, JsaLogo } from "../../components/Jsa";
import { autoNextDelay } from "../../lib/useAutoNext";

/**
 * ADAPTIV DARAJA TESTI (2026-08-21).
 *
 * Jahongir: "darajasini aniqlaydigan chuqur bir test qoshaylik level
 * test... togri topsa ozgina qiyinlashtiradi, topsa qiyinlashib
 * ketaveradi darajasi yuqorilab, topolmasa osha darajadan berib
 * koradi yana topolmasa pastroq darajadan berib koradi... Grammar,
 * Vocabular, Reading, Listeningdan aniqlashi kerak".
 *
 * Adaptiv mantiq TO'LIQ serverda (to'g'ri javob mijozga oldindan
 * yuborilmaydi) — bu ekran faqat savolni ko'rsatadi va javob yuboradi.
 */
type Any = any; // eslint-disable-line @typescript-eslint/no-explicit-any

const SEC_ICONS: Record<string, string> = {
  grammar: "/jsicons/learn-grammar.png",
  vocabulary: "/jsicons/learn-vocabulary.png",
  reading: "/jsicons/learn-reading.png",
  listening: "/jsicons/learn-listening.png",
};
const LEVEL_COLORS: Record<string, string> = {
  A1: "#94A3B8", A2: "#38BDF8", B1: "#34D399", B2: "#A78BFA",
};

function speak(text: string) {
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  } catch {
    /* TTS yo'q */
  }
}

export default function StudentLevelTest() {
  const [phase, setPhase] = useState<"intro" | "quiz" | "result">("intro");
  const [prev, setPrev] = useState<Any>(null); // oxirgi natija (intro'da)
  const [q, setQ] = useState<Any>(null);       // joriy savol bloki
  const [result, setResult] = useState<Any>(null);
  const [picked, setPicked] = useState<string | number | null>(null);
  const [fb, setFb] = useState<Any>(null);     // {correct, expected}
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/level-test/status")
      .then((r) => {
        if (r.active) {
          setQ(r);
          setPhase("quiz");
        } else if (r.done) setPrev(r);
      })
      .catch(() => undefined);
  }, []);
  useEffect(() => () => window.speechSynthesis?.cancel(), []);

  const start = useCallback(() => {
    setErr("");
    setBusy(true);
    api
      .post<Any>("/student/level-test/start", {})
      .then((r) => {
        setQ(r);
        setResult(null);
        setFb(null);
        setPicked(null);
        setPhase("quiz");
        if (r.question?.say) setTimeout(() => speak(r.question.say), 400);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setBusy(false));
  }, []);

  async function submit(answer: string | number) {
    if (busy || fb) return;
    setBusy(true);
    setPicked(answer);
    try {
      const r = await api.post<Any>("/student/level-test/answer", {
        answer,
      });
      setFb(r);
      if (r.done) {
        setTimeout(() => {
          setResult(r);
          setPhase("result");
          setFb(null);
        }, r.correct ? 700 : 1600);
      } else {
        setTimeout(() => {
          setQ(r);
          setFb(null);
          setPicked(null);
          if (r.question?.say) setTimeout(() => speak(r.question.say), 300);
        }, autoNextDelay({
          correct: !!r.correct,
          hasAnswer: !!r.expected,
          hasExtra: false,
        }));
      }
    } catch (e) {
      // 2026-09-08, Jahongir: "tanlab bo'lmayabdi ekan xatolik bor
      // ekan". Ilgari xato JIMGINA yutilardi: o'quvchi javobni bosardi,
      // ekranda hech narsa o'zgarmasdi va u "tugma ishlamayapti" deb
      // o'ylardi. Endi sabab yoziladi va qayta urinish mumkin.
      setFb(null);
      setPicked(null);
      setErr(
        e instanceof Error && e.message
          ? e.message
          : "Javob yuborilmadi — internetni tekshirib, qaytadan bosing",
      );
    } finally {
      setBusy(false);
    }
  }

  const qq = q?.question;

  return (
    <div className="min-h-screen" style={{ background: JSA.bg }}>
      <div className="max-w-md mx-auto px-4 pt-4">
        <div className="flex items-center justify-between">
          <Link
            to="/student/games"
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}
            aria-label="Yopish"
          >
            <X size={18} className="text-slate-300" />
          </Link>
          <JsaLogo small />
          <div className="w-10" />
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 mt-4 space-y-3 pb-10">
        {err && (
          <div className="student-panel bg-white rounded-xl border border-red-200 p-4">
            <p className="text-sm text-red-600">{err}</p>
          </div>
        )}

        {/* ================= INTRO ================= */}
        {phase === "intro" && (
          <>
            <div
              className="rounded-2xl p-5 text-white"
              style={{
                background:
                  "linear-gradient(120deg,#2B50E0,#4A56EC 55%,#7B5CF0)",
              }}
            >
              <StudentImage
                src="/jsicons/learn-exam.png"
                alt=""
                className="w-14 h-14 mb-3"
              />
              <p className="text-[22px] font-extrabold leading-tight">
                Daraja testi
              </p>
              <p className="text-[13px] text-white/85 mt-1.5 leading-snug">
                Darajangizni chuqur aniqlaymiz: to'g'ri topsangiz savollar
                qiyinlashib boradi, adashsangiz o'sha darajadan yana bir
                imkon, keyin pastroqdan — shu tarzda aniq darajangiz
                topiladi.
              </p>
            </div>

            <div
              className="rounded-2xl p-4"
              style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}
            >
              <p className="text-[13px] font-bold text-white mb-2.5">
                4 bo'lim ketma-ket tekshiriladi
              </p>
              {(["grammar", "vocabulary", "reading", "listening"] as const).map(
                (k) => (
                  <div key={k} className="flex items-center gap-3 py-2">
                    <StudentImage src={SEC_ICONS[k]} alt="" className="w-9 h-9" />
                    <div className="flex-1">
                      <p className="text-[13px] font-semibold text-white capitalize">
                        {k}
                      </p>
                      <p className="text-[11px] text-slate-400">
                        Har darajada bir nechta savol — chuqur tekshiruv
                      </p>
                    </div>
                  </div>
                ),
              )}
              <p className="text-[11px] text-slate-400 mt-2">
                Har darajani yutish uchun 3 ta to'g'ri javob kerak —
                shunda natija aniq bo'ladi. Natija: har ko'nikma
                bo'yicha CEFR daraja (A1–B2) va umumiy daraja.
              </p>
            </div>

            {prev && (
              <div
                className="rounded-2xl p-4"
                style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}
              >
                <p className="text-[12px] text-slate-400">
                  Oxirgi natijangiz
                </p>
                <p className="text-[20px] font-extrabold text-white mt-0.5">
                  {prev.overall}{" "}
                  <span className="text-[13px] font-semibold text-slate-300">
                    · {prev.overall_label}
                  </span>
                </p>
              </div>
            )}

            <button
              onClick={start}
              disabled={busy}
              className="w-full py-3.5 rounded-xl bg-brand-600 text-white text-sm font-bold disabled:opacity-60"
            >
              {busy ? "Tayyorlanmoqda…" : "Testni boshlash"}
            </button>
          </>
        )}

        {/* ================= SAVOL ================= */}
        {phase === "quiz" && qq && (
          <>
            <div className="flex items-center gap-2.5">
              <StudentImage
                src={SEC_ICONS[q.section] || SEC_ICONS.grammar}
                alt=""
                className="w-9 h-9"
              />
              <div className="flex-1">
                <p className="text-[14px] font-bold text-white">
                  {q.section_label}
                </p>
                <p className="text-[11px] text-slate-400">
                  Bo'lim {q.section_no}/{q.sections_total} · savol{" "}
                  {q.question_no}
                </p>
              </div>
            </div>
            <div
              className="h-1.5 rounded-full overflow-hidden"
              style={{ background: "#26326B" }}
            >
              <div
                className="h-full rounded-full transition-all bg-gradient-to-r from-sky-500 to-violet-500"
                style={{
                  width: `${((q.section_no - 1) * 100 +
                    Math.min(100, (q.question_no / 36) * 100)) /
                    q.sections_total}%`,
                }}
              />
            </div>

            <div className="student-panel bg-white rounded-2xl shadow-sm p-4">
              {qq.kind === "read" && (
                <div className="mb-3 border border-slate-200 rounded-xl p-3 max-h-52 overflow-y-auto">
                  <p className="text-[12px] font-bold text-slate-800 mb-1">
                    {qq.title}
                  </p>
                  <p className="text-[12.5px] text-slate-600 whitespace-pre-line leading-relaxed">
                    {qq.text}
                  </p>
                </div>
              )}

              {qq.kind === "listen" ? (
                <button
                  onClick={() => speak(qq.say)}
                  className="mx-auto my-3 w-16 h-16 rounded-full bg-brand-600 text-white flex items-center justify-center active:scale-95 transition"
                  aria-label="Eshitish"
                >
                  <Volume2 size={26} />
                </button>
              ) : (
                <p className="text-[15px] font-semibold text-slate-900 leading-snug">
                  {qq.prompt}
                </p>
              )}
              <p className="text-[11px] text-slate-400 mt-1 mb-3">
                {qq.hint}
              </p>

              <div className="space-y-1.5">
                {[...(qq.options || []).map((o: string) => ({label: o, value: o})), {label: "Bilmayman", value: -1}].map(({label: o, value}: {label: string; value: string | number}) => {
                  const isPick = picked === value;
                  const good = fb && fb.correct && isPick;
                  const bad = fb && !fb.correct && isPick;
                  const showRight =
                    value !== -1 && fb && !fb.correct && fb.expected === value;
                  return (
                    <button
                      key={value}
                      aria-pressed={isPick}
                      onClick={() => submit(value)}
                      disabled={busy || !!fb}
                      className={`w-full text-left px-3.5 py-3 rounded-xl border text-[13.5px] font-medium transition ${
                        good || showRight
                          ? "border-emerald-400 bg-emerald-50 text-emerald-700"
                          : bad
                            ? "border-red-300 bg-red-50 text-red-600"
                            : isPick
                              ? "border-brand-600 bg-blue-50 text-slate-700"
                              : "border-slate-200 text-slate-700 active:scale-[0.99]"
                      }`}
                    >
                      <span className="flex items-center justify-between">
                        {o}
                        {(good || showRight) && (
                          <Check size={15} className="text-emerald-500" />
                        )}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* ================= NATIJA ================= */}
        {phase === "result" && result && (
          <>
            <div
              className="rounded-2xl p-6 text-center text-white"
              style={{
                background:
                  "linear-gradient(120deg,#2B50E0,#4A56EC 55%,#7B5CF0)",
              }}
            >
              <p className="text-[12px] uppercase tracking-wide text-white/75">
                Sizning darajangiz
              </p>
              <p className="text-[44px] font-extrabold leading-none mt-1.5">
                {result.overall}
              </p>
              <p className="text-[13px] font-semibold mt-1">
                {result.overall_label}
              </p>
              {result.ielts && (
                <p className="text-[11.5px] text-white/75 mt-1.5">
                  Taxminiy IELTS: {result.ielts}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {(
                [
                  ["grammar", result.grammar],
                  ["vocabulary", result.vocabulary],
                  ["reading", result.reading],
                  ["listening", result.listening],
                ] as [string, string][]
              ).map(([k, lvl]) => (
                <div
                  key={k}
                  className="rounded-2xl p-3.5"
                  style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}
                >
                  <StudentImage src={SEC_ICONS[k]} alt="" className="w-8 h-8 mb-2" />
                  <p className="text-[12px] text-slate-400 capitalize">{k}</p>
                  <p
                    className="text-[20px] font-extrabold"
                    style={{ color: LEVEL_COLORS[lvl] || "#fff" }}
                  >
                    {lvl || "—"}
                  </p>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <button
                onClick={start}
                className="flex-1 py-3 rounded-xl text-slate-200 text-sm font-semibold"
                style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}
              >
                Qayta topshirish
              </button>
              <Link
                to="/student/games"
                className="flex-1 py-3 rounded-xl bg-brand-600 text-white text-sm font-bold flex items-center justify-center"
              >
                O'rganishga qaytish
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
