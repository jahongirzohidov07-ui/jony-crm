import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Check, Volume2, X } from "lucide-react";
import { api } from "../../lib/api";
import { autoNextDelay, useAutoNext } from "../../lib/useAutoNext";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * IELTS LISTENING — SPELLING VA RAQAMLAR (2026-08-24).
 *
 * Jahongir: "Listening bo'limda birinchi spelling names bo'lsin...
 * keyin 50ta number practice... 3-mashq spelling mixed koproq
 * postcodelar... hammasi sekinidan boshlab qiyinlashib borsin va
 * tezlashib borsin asta sekinlik bilan".
 *
 * ISHLASH TARTIBI. Server elementlarni OSONDAN QIYINGA saralab
 * beradi va har biriga o'z tezligini (rate) qo'shadi - 0.55x dan
 * 1.0x gacha. Bola eshitadi, yozadi, server tekshiradi.
 *
 * NEGA "yana eshitish" bor. IELTS'da audio BIR MARTA beriladi,
 * lekin bu MASHQ - o'rganish bosqichida takror eshitish foydali.
 * Nechchi marta eshitgani ekranda ko'rinib turadi, ya'ni bola
 * o'zini o'zi nazorat qiladi.
 */

const RATE_LABEL = (r: number) =>
  r <= 0.6 ? "juda sekin" : r <= 0.7 ? "sekin"
    : r <= 0.8 ? "o'rtacha" : r <= 0.9 ? "tezroq" : "imtihon tezligi";

/* 2026-08-26, Jahongir: "2 marta aytiladi CEFRdagi barcha
   listeninglar". Yuborgan audiosi o'lchandi: har gap ikki marta
   o'qiladi, orasida jimlik bor. Shuning uchun speak() endi necha
   marta o'qishni va oradagi jimlikni ham oladi. Kutayotgan taymer
   alohida saqlanadi, aks holda "yana eshitish" bosilganda eski
   takror yangisining ustiga chiqib ketardi. */
let replayTimer: number | undefined;

function stopSpeaking() {
  if (replayTimer) window.clearTimeout(replayTimer);
  replayTimer = undefined;
  try {
    stopSpeaking();
  } catch {
    /* brauzer qo'llamasa — jim o'tamiz */
  }
}

function speak(text: string, rate: number, times = 1, gapMs = 1500) {
  try {
    stopSpeaking();
    let left = Math.max(1, times);
    const say = () => {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "en-GB";
      u.rate = rate;
      u.volume = 1;
      u.onend = () => {
        left -= 1;
        if (left > 0) replayTimer = window.setTimeout(say, gapMs);
      };
      window.speechSynthesis.speak(u);
    };
    say();
    return;
  } catch {
    /* pastdagi eski yo'l ishlaydi */
  }
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-GB";
    u.rate = rate;
    window.speechSynthesis.speak(u);
  } catch {
    /* TTS yo'q */
  }
}

export default function StudentIeltsListening() {
  const { kind } = useParams();
  const [d, setD] = useState<Any>(null);
  const [idx, setIdx] = useState(0);
  const [typed, setTyped] = useState("");
  const [result, setResult] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [plays, setPlays] = useState(0);
  const [slow, setSlow] = useState(false);
  const [score, setScore] = useState({ ok: 0, xp: 0 });
  const [finished, setFinished] = useState(false);
  const [cnt, setCnt] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const load = useCallback(() => {
    if (cnt === null) return;
    setErr("");
    setD(null);
    setIdx(0);
    setTyped("");
    setResult(null);
    setPlays(0);
    setScore({ ok: 0, xp: 0 });
    setFinished(false);
    api
      .get<Any>(`/student/ielts/listening/round?kind=${kind}&count=${cnt}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [kind, cnt]);

  useEffect(load, [load]);
  useEffect(() => () => stopSpeaking(), []);

  const items: Any[] = d?.items || [];
  const q = items[idx];
  const autoNext = useAutoNext(() => next());

  // Yangi element — o'zi bir marta o'qib beradi va kursor maydonda
  useEffect(() => {
    if (!q || result) return;
    setPlays(1);
    setSlow(false);
    speak(q.say, q.rate, q.plays || 1, q.gap_ms || 1500);
    if (q.options) return;   // tanlovli turda klaviatura kerak emas
    const t = setTimeout(() => inputRef.current?.focus(), 300);
    return () => clearTimeout(t);
  }, [q, result]);

  async function submit(picked?: string) {
    const answer = picked ?? typed;
    if (!q || busy || result || !answer.trim()) return;
    setBusy(true);
    try {
      const r = await api.post<Any>("/student/ielts/listening/answer", {
        ref: q.ref,
        answer,
      });
      if (picked) setTyped(picked);
      setResult(r);
      if (r.correct)
        setScore((s) => ({ ok: s.ok + 1, xp: s.xp + (r.xp || 0) }));
      // Xato bo'lsa uzoqroq turadi — harflarni solishtirish kerak
      autoNext.schedule(
        autoNextDelay({ correct: !!r.correct, hasAnswer: true,
                        hasExtra: true }) * (r.correct ? 1 : 1.6),
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  function next() {
    autoNext.cancel();
    stopSpeaking();
    if (idx + 1 >= items.length) {
      setFinished(true);
      return;
    }
    setIdx(idx + 1);
    setTyped("");
    setResult(null);
  }

  const card = { background: "#111C4B", borderColor: "#223070" };

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* -------------------------------------------- sarlavha */}
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/ielts"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <X size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          IELTS LISTENING
        </p>
        {!finished && items.length > 0 && (
          <span
            className="rounded-xl px-2.5 py-1.5 border text-[12px] font-bold shrink-0"
            style={card}
          >
            {Math.min(idx + 1, items.length)} / {items.length}
          </span>
        )}
      </div>

      <h1 className="text-[26px] font-extrabold text-white leading-tight mt-3">
        {d?.title || "Mashq"}
      </h1>

      {err && (
        <div className="bg-white rounded-xl border border-red-200 p-4 mt-4">
          <p className="text-sm text-red-600">{err}</p>
        </div>
      )}

      {/* -------------------------------------- nechta mashq */}
      {cnt === null && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mt-4">
          <p className="text-sm font-semibold text-slate-800 mb-1">
            Nechta mashq qilamiz?
          </p>
          <p className="text-[11px] text-slate-400 mb-3">
            Mashq oson va sekindan boshlanadi, keyin asta-sekin
            qiyinlashib va tezlashib boradi.
          </p>
          <div className="space-y-1.5">
            {[
              [8, "8 ta", "Bitta CEFR mashg'uloti"],
              [16, "16 ta", "Ikki mashg'ulot — 7-8 daqiqa"],
              [50, "50 ta", "To'liq blok — imtihon tezligigacha"],
            ].map(([n, lbl, hint]) => (
              <button
                key={String(n)}
                onClick={() => setCnt(n as number)}
                className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 text-left active:scale-[0.99]"
              >
                <div className="w-11 h-9 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center shrink-0 text-sm font-extrabold">
                  {n}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800">{lbl}</p>
                  <p className="text-[11px] text-slate-400">{hint}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------- mashq */}
      {!finished && q && (
        <>
          <div className="bg-white rounded-xl border border-slate-200 p-4 mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-500">
                {q.hint}
              </span>
              <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                {q.step}-bosqich · {RATE_LABEL(q.rate)}
              </span>
            </div>

            <button
              onClick={() => {
                setPlays((p) => p + 1);
                speak(q.say, slow ? Math.max(0.5, q.rate - 0.25) : q.rate,
                      q.plays || 1, q.gap_ms || 1500);
              }}
              className="w-full py-6 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center gap-2 text-amber-700 font-semibold text-sm active:scale-[0.99]"
            >
              <Volume2 size={22} />
              {plays === 0 ? "Eshitish" : "Yana eshitish"}
              {(q.plays || 1) > 1 && (
                <span className="text-[11px] font-normal opacity-70">
                  ({q.plays} marta aytiladi)
                </span>
              )}
            </button>
            <div className="flex items-center justify-between mt-2">
              <p className="text-[11px] text-slate-400">
                {plays} marta eshitildi
                {!q.prompt && ` · ${q.length} belgi`}
              </p>
              <button
                onClick={() => {
                  setSlow((v) => !v);
                  setPlays((p) => p + 1);
                  speak(q.say, !slow ? Math.max(0.5, q.rate - 0.25) : q.rate,
                    q.plays || 1, q.gap_ms || 1500);
                }}
                className={`text-[11px] font-medium rounded-full px-2.5 py-1 border ${
                  slow
                    ? "bg-slate-800 text-white border-transparent"
                    : "text-slate-500 border-slate-200"
                }`}
              >
                sekinroq
              </button>
            </div>

            {/* SAVOL (2026-08-24). Ma'lumot ilib olish va
                chalg'ituvchi javoblar mashqlarida audio — oddiy
                dialog, savol esa ALOHIDA. Savolni ko'rsatmasak,
                bola nimani yozishini bilmaydi. */}
            {q.prompt && (
              <div className="mt-3 rounded-lg bg-slate-900/5 border border-slate-200 px-3 py-2.5">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                  Savol
                </p>
                {/* 2026-08-26: CEFR 2- va 6-qismda savol o'rniga
                    BUTUN qaydnoma turadi va u ko'p qatorli. Shuning
                    uchun qator ko'chishi saqlanadi. */}
                <p className="text-sm font-medium text-slate-800 mt-0.5 whitespace-pre-line leading-relaxed">
                  {q.prompt}
                </p>
              </div>
            )}

            {/* A/B/C VARIANTLARI (2026-08-24 — exact word trap).
                Bu turda javob yozilmaydi, tanlanadi. To'g'ri javob
                serverdan faqat tanlovdan KEYIN keladi. */}
            {q.options ? (
              <div className="space-y-1.5 mt-3">
                {q.options.map((o: string, i: number) => {
                  const isMine = result && o === typed;
                  const isAns = result && o === result.expected;
                  return (
                    <button
                      key={o}
                      disabled={!!result || busy}
                      onClick={() => submit(o)}
                      className={`w-full flex items-start gap-2.5 py-2.5 px-3 rounded-lg border text-sm text-left ${
                        isAns
                          ? "bg-emerald-600 text-white border-transparent"
                          : isMine
                            ? "bg-red-600 text-white border-transparent"
                            : "bg-white text-slate-700 border-slate-200"
                      }`}
                    >
                      <span className="font-bold shrink-0">
                        {"ABC"[i]}
                      </span>
                      <span className="flex-1">{o}</span>
                    </button>
                  );
                })}
              </div>
            ) : (
              <input
                ref={inputRef}
                value={typed}
                disabled={!!result}
                onChange={(e) => setTyped(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
                placeholder={
                  q.prompt ? "Javobingizni yozing" : "Eshitganingizni yozing"
                }
                autoCapitalize={q.prompt ? "off" : "characters"}
                autoCorrect="off"
                spellCheck={false}
                className={`w-full mt-3 px-3 py-3 rounded-lg border border-slate-200 text-base ${
                  q.prompt ? "" : "tracking-widest uppercase"
                }`}
              />
            )}

            {!result ? (
              !q.options && (
                <button
                  onClick={() => submit()}
                  disabled={busy || !typed.trim()}
                  className="w-full mt-2 py-3 rounded-lg bg-brand-600 text-white text-sm font-semibold disabled:opacity-40"
                >
                  Tekshirish
                </button>
              )
            ) : (
              <div
                className={`mt-3 rounded-lg p-3 ${
                  result.correct ? "bg-emerald-50" : "bg-red-50"
                }`}
              >
                <p
                  className={`text-sm font-bold ${
                    result.correct ? "text-emerald-700" : "text-red-700"
                  }`}
                >
                  {result.correct ? "To'g'ri!" : "Xato"}
                </p>
                {!result.correct && (
                  <p className="text-sm text-slate-700 mt-1">
                    To'g'ri javob:{" "}
                    <b className={q.options ? "" : "tracking-widest"}>
                      {result.expected}
                    </b>
                  </p>
                )}
                {result.explain && (
                  <p className="text-[11px] text-slate-500 mt-1.5 leading-relaxed">
                    {result.explain}
                  </p>
                )}
                <button
                  onClick={next}
                  className="mt-2.5 text-sm font-semibold text-brand-700"
                >
                  {idx + 1 >= items.length ? "Yakunlash" : "Keyingisi"}
                  {autoNext.secsLeft > 0 ? ` (${autoNext.secsLeft})` : ""}
                </button>
              </div>
            )}
          </div>

          <div className="h-2 rounded-full overflow-hidden mt-3"
               style={{ background: "#26326B" }}>
            <div
              className="h-full bg-amber-500 rounded-full transition-all"
              style={{
                width: `${((idx + (result ? 1 : 0)) / items.length) * 100}%`,
              }}
            />
          </div>
        </>
      )}

      {/* ------------------------------------------ yakun */}
      {finished && (
        <div className="rounded-2xl border p-6 mt-4 text-center" style={card}>
          <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-500/15 flex items-center justify-center">
            <Check size={26} className="text-emerald-400" />
          </div>
          <p className="text-white font-extrabold text-[20px] mt-3">
            {score.ok} / {items.length}
          </p>
          <p className="text-[13px] text-slate-400 mt-1">
            +{score.xp} XP · keyingi safar tezroq bo'ladi
          </p>
          <div className="flex gap-2 mt-4">
            <button
              onClick={load}
              className="flex-1 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white"
            >
              Yana mashq
            </button>
            <Link
              to="/student/ielts"
              className="flex-1 rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-300"
              style={card}
            >
              Bo'limga qaytish
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
