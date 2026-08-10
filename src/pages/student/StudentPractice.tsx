import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft, Check, Ear, Mic, PenLine, RotateCcw, Sparkles, Volume2, X,
} from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — 4 KO'NIKMA MASHG'ULOTI (2026-08-10).
 *
 * Bitta sahifa to'rt xil mashqni yuritadi:
 *   listening — brauzer TTS o'qiydi: diktant / tanlov;
 *   reading   — matn + tushunish savollari;
 *   writing   — o'zbekcha ma'noni inglizcha YOZIB tarjima qilish;
 *   speaking  — jumlani MIKROFONGA o'qish (brauzer nutqni matnga
 *               aylantiradi, server solishtiradi).
 *
 * Tekshiruv har doim serverda. TTS/mikrofon qurilmada bo'lmasa,
 * tushunarli ogohlantirish chiqadi.
 */

const META: Record<string, { label: string; grad: string; icon: Any }> = {
  listening: { label: "Listening", grad: "from-amber-600 to-amber-500", icon: Ear },
  reading: { label: "Reading", grad: "from-sky-700 to-sky-500", icon: PenLine },
  writing: { label: "Writing", grad: "from-rose-600 to-rose-500", icon: PenLine },
  speaking: { label: "Speaking", grad: "from-teal-600 to-teal-500", icon: Mic },
};

function speak(text: string, rate = 0.95) {
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = rate;
    window.speechSynthesis.speak(u);
  } catch {
    /* TTS yo'q */
  }
}

export default function StudentPractice() {
  const { skill } = useParams();
  const m = META[skill || ""] || META.listening;
  const [d, setD] = useState<Any>(null);
  const [idx, setIdx] = useState(0);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [typed, setTyped] = useState("");
  const [result, setResult] = useState<Any>(null);
  const [score, setScore] = useState({ ok: 0, xp: 0 });
  const [finished, setFinished] = useState(false);
  const [listening, setListening] = useState(false);
  const [heard, setHeard] = useState("");
  const recRef = useRef<Any>(null);
  // LISTENING TEZLIGI (2026-08-11, Jahongir): 0.75x sekin / 1x normal
  const [rate, setRate] = useState(1.0);
  // READING POP-UP LUG'ATI: bosilgan so'z tarjimasi
  const [dict, setDict] = useState<Any>(null);
  const dictCache = useRef<Record<string, Any>>({});

  const load = useCallback(() => {
    setErr("");
    setD(null);
    setIdx(0);
    setResult(null);
    setTyped("");
    setHeard("");
    setScore({ ok: 0, xp: 0 });
    setFinished(false);
    api
      .get<Any>(`/student/practice/${skill}/round`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [skill]);

  useEffect(load, [load]);
  useEffect(() => () => window.speechSynthesis?.cancel(), []);

  const items: Any[] = d?.items || [];
  const q = items[idx];

  async function submit(answer: string) {
    if (!q || busy || result) return;
    setBusy(true);
    try {
      const r = await api.post<Any>("/student/practice/answer", {
        skill,
        ref: q.ref,
        answer,
      });
      setResult({ ...r, _mine: answer });
      if (r.correct)
        setScore((s) => ({ ok: s.ok + 1, xp: s.xp + (r.xp || 0) }));
    } catch {
      /* toast */
    } finally {
      setBusy(false);
    }
  }

  function next() {
    window.speechSynthesis?.cancel();
    if (idx + 1 >= items.length) {
      setFinished(true);
      return;
    }
    setIdx(idx + 1);
    setResult(null);
    setTyped("");
    setHeard("");
  }

  // ---- READING: so'z bosilganda tarjima (2026-08-11) ----
  async function lookupWord(raw: string) {
    const w = raw.replace(/[^A-Za-z'-]/g, "").toLowerCase();
    if (!w) return;
    if (dictCache.current[w]) {
      setDict(dictCache.current[w]);
      return;
    }
    setDict({ word: raw, loading: true });
    try {
      const r = await api.get<Any>(
        `/student/word-lookup?w=${encodeURIComponent(w)}`,
      );
      dictCache.current[w] = r;
      setDict(r);
    } catch {
      setDict(null);
    }
  }

  // ---- SPEAKING: mikrofon ----
  function startMic() {
    const SR =
      (window as Any).SpeechRecognition ||
      (window as Any).webkitSpeechRecognition;
    if (!SR) {
      setErr(
        "Bu qurilma ovozni matnga aylantirishni qo'llamaydi. " +
          "Android Chrome'da urinib ko'ring.",
      );
      return;
    }
    setErr("");
    const rec = new SR();
    recRef.current = rec;
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    setListening(true);
    rec.onresult = (e: Any) => {
      const t = e.results[0][0].transcript;
      setHeard(t);
      setListening(false);
      submit(t);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    rec.start();
  }

  const Icon = m.icon;

  return (
    <>
      <div className={`bg-gradient-to-br ${m.grad} text-white px-4 pt-6 pb-10`}>
        <div className="max-w-md mx-auto">
          <Link
            to="/student/games"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Mashqlar
          </Link>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Icon size={20} />
            {m.label}
          </h1>
          {!finished && items.length > 0 && (
            <div className="flex items-center gap-2 mt-2">
              <div className="flex-1 h-1.5 bg-white/25 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white rounded-full transition-all"
                  style={{
                    width: `${((idx + (result ? 1 : 0)) / items.length) * 100}%`,
                  }}
                />
              </div>
              <span className="text-xs opacity-90">
                {Math.min(idx + 1, items.length)}/{items.length}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-3 pb-8">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4">
            <p className="text-sm text-red-600">{err}</p>
            <button onClick={load} className="mt-2 text-sm font-medium text-slate-700 underline">
              Qayta urinish
            </button>
          </div>
        )}

        {/* Reading matni doim tepada turadi */}
        {!finished && skill === "reading" && d?.text && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-baseline justify-between mb-1.5">
              <p className="text-sm font-semibold text-slate-800">
                {d.text.title}
              </p>
              <span className="text-[10px] font-bold text-sky-600 bg-sky-50 px-1.5 py-0.5 rounded">
                {d.text.level}
              </span>
            </div>
            {/* Har so'z bosiladi - tarjimasi chiqadi (pop-up
                lug'at); tepada matnni eshitish tugmasi. */}
            <p className="text-sm text-slate-700 leading-relaxed">
              {String(d.text.body)
                .split(/(\s+)/)
                .map((tok: string, i: number) =>
                  /\s+/.test(tok) ? (
                    tok
                  ) : (
                    <span
                      key={i}
                      onClick={() => lookupWord(tok)}
                      className="cursor-pointer active:bg-amber-100 rounded"
                    >
                      {tok}
                    </span>
                  ),
                )}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <button
                onClick={() => speak(d.text.body, 0.95)}
                className="flex items-center gap-1.5 text-xs font-medium text-sky-600 bg-sky-50 px-3 py-1.5 rounded-lg"
              >
                <Volume2 size={13} />
                Matnni eshitish
              </button>
              <p className="text-[10px] text-slate-400">
                So'z ustiga bossangiz — tarjimasi chiqadi
              </p>
            </div>
          </div>
        )}

        {/* ---- SO'Z TARJIMASI (pop-up) ---- */}
        {dict && (
          <div
            className="fixed inset-x-0 bottom-20 z-40 flex justify-center px-6"
            onClick={() => setDict(null)}
          >
            <div className="bg-slate-900 text-white rounded-xl px-4 py-3 shadow-xl max-w-xs w-full flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold">{dict.word}</p>
                <p className="text-xs text-slate-300">
                  {dict.loading
                    ? "Qidirilmoqda..."
                    : dict.found
                      ? dict.translation
                      : "Lug'atda topilmadi"}
                </p>
              </div>
              {!dict.loading && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    speak(dict.word);
                  }}
                  className="text-slate-300"
                  aria-label="Talaffuz"
                >
                  <Volume2 size={16} />
                </button>
              )}
            </div>
          </div>
        )}

        {finished && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
            <Sparkles size={36} className="mx-auto text-amber-500 mb-2" />
            <p className="text-2xl font-bold text-slate-900">
              {score.ok}/{items.length}
            </p>
            <p className="text-sm text-slate-500 mt-1">
              to'g'ri javob{score.xp > 0 && ` · +${score.xp} XP`}
            </p>
            <div className="flex gap-2 mt-5">
              <button
                onClick={load}
                className="flex-1 py-3 rounded-xl bg-slate-900 text-white text-sm font-semibold flex items-center justify-center gap-2"
              >
                <RotateCcw size={15} />
                Yana mashq
              </button>
              <Link
                to="/student/games"
                className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold flex items-center justify-center"
              >
                Mashqlar
              </Link>
            </div>
          </div>
        )}

        {!finished && q && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            {/* ---- LISTENING ---- */}
            {q.kind?.startsWith("listen") && (
              <>
                <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wide mb-3">
                  {q.kind === "listen_choice"
                    ? "Eshiting va tarjimasini tanlang"
                    : "Eshiting va yozing"}
                </p>
                <button
                  onClick={() => speak(q.say, rate)}
                  className="w-full py-5 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center gap-2 text-amber-700 font-semibold text-sm mb-2 active:scale-[0.99]"
                >
                  <Volume2 size={20} />
                  Eshitish
                </button>
                {/* TEZLIK (2026-08-11): 0.75x sekin / 1x normal */}
                <div className="flex gap-1.5 mb-3">
                  {[
                    [0.75, "0.75x sekin"],
                    [1.0, "1x normal"],
                  ].map(([v, lbl]) => (
                    <button
                      key={String(v)}
                      onClick={() => {
                        setRate(v as number);
                        speak(q.say, v as number);
                      }}
                      className={`flex-1 py-1.5 rounded-lg border text-xs font-medium ${
                        rate === v
                          ? "bg-amber-600 text-white border-transparent"
                          : "bg-white text-slate-500 border-slate-200"
                      }`}
                    >
                      {lbl}
                    </button>
                  ))}
                </div>
                {q.kind === "listen_choice" ? (
                  <div className="space-y-1.5">
                    {(q.options || []).map((o: string) => {
                      const isMine = result && o === result._mine;
                      const good = result?.correct && isMine;
                      return (
                        <button
                          key={o}
                          disabled={!!result || busy}
                          onClick={() => submit(o)}
                          className={`w-full py-2.5 px-3 rounded-lg border text-sm font-medium text-left ${
                            good
                              ? "bg-emerald-600 text-white border-transparent"
                              : isMine
                                ? "bg-red-600 text-white border-transparent"
                                : "bg-white text-slate-700 border-slate-200"
                          }`}
                        >
                          {o}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  !result && (
                    <div className="flex gap-2">
                      <input
                        value={typed}
                        onChange={(e) => setTyped(e.target.value)}
                        placeholder="Eshitganingizni yozing..."
                        className="flex-1 rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                        autoCapitalize="off"
                      />
                      <button
                        disabled={!typed.trim() || busy}
                        onClick={() => submit(typed)}
                        className="px-4 rounded-lg bg-amber-600 text-white text-sm font-semibold disabled:opacity-40"
                      >
                        OK
                      </button>
                    </div>
                  )
                )}
              </>
            )}

            {/* ---- READING savoli ---- */}
            {q.kind === "read_mcq" && (
              <>
                <p className="text-[11px] font-semibold text-sky-600 uppercase tracking-wide mb-2">
                  Savol {idx + 1}
                </p>
                <p className="text-base font-medium text-slate-900 mb-3">
                  {q.prompt}
                </p>
                <div className="space-y-1.5">
                  {(q.options || []).map((o: string) => {
                    const isMine = result && o === result._mine;
                    const isAns = result && o === result.expected;
                    return (
                      <button
                        key={o}
                        disabled={!!result || busy}
                        onClick={() => submit(o)}
                        className={`w-full py-2.5 px-3 rounded-lg border text-sm font-medium text-left ${
                          isAns
                            ? "bg-emerald-600 text-white border-transparent"
                            : isMine
                              ? "bg-red-600 text-white border-transparent"
                              : "bg-white text-slate-700 border-slate-200"
                        }`}
                      >
                        {o}
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* ---- WRITING ---- */}
            {q.kind === "write_translate" && (
              <>
                <p className="text-[11px] font-semibold text-rose-600 uppercase tracking-wide mb-2">
                  Inglizchaga tarjima qilib yozing
                </p>
                <p className="text-base font-medium text-slate-900 mb-1">
                  {q.prompt}
                </p>
                <p className="text-[11px] text-slate-400 mb-3">
                  {q.words} ta so'zdan iborat jumla
                </p>
                {!result && (
                  <div className="space-y-2">
                    <input
                      value={typed}
                      onChange={(e) => setTyped(e.target.value)}
                      placeholder="Write in English..."
                      className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                      autoCapitalize="off"
                    />
                    <button
                      disabled={!typed.trim() || busy}
                      onClick={() => submit(typed)}
                      className="w-full py-3 rounded-xl bg-rose-600 text-white text-sm font-semibold disabled:opacity-40"
                    >
                      Tekshirish
                    </button>
                  </div>
                )}
              </>
            )}

            {/* ---- SPEAKING ---- */}
            {q.kind === "speak_read" && (
              <>
                <p className="text-[11px] font-semibold text-teal-600 uppercase tracking-wide mb-2">
                  Jumlani ovoz chiqarib o'qing
                </p>
                <p className="text-lg font-semibold text-slate-900 leading-relaxed mb-1">
                  {q.text}
                </p>
                <button
                  onClick={() => speak(q.text)}
                  className="text-xs text-teal-600 font-medium flex items-center gap-1 mb-4"
                >
                  <Volume2 size={13} />
                  Namunani eshitish
                </button>
                {!result && (
                  <button
                    onClick={startMic}
                    disabled={busy || listening}
                    className={`w-full py-5 rounded-xl flex items-center justify-center gap-2 text-sm font-semibold transition ${
                      listening
                        ? "bg-red-600 text-white animate-pulse"
                        : "bg-teal-600 text-white"
                    }`}
                  >
                    <Mic size={20} />
                    {listening ? "Eshitilmoqda... gapiring" : "Gapirish"}
                  </button>
                )}
                {heard && (
                  <p className="text-xs text-slate-500 mt-2">
                    Siz aytdingiz: "{heard}"
                  </p>
                )}
              </>
            )}

            {/* ---- Natija ---- */}
            {result && (
              <div
                className={`mt-3 rounded-xl p-3 ${
                  result.correct ? "bg-emerald-50" : "bg-red-50"
                }`}
              >
                <p
                  className={`text-sm font-semibold flex items-center gap-1.5 ${
                    result.correct ? "text-emerald-700" : "text-red-700"
                  }`}
                >
                  {result.correct ? <Check size={15} /> : <X size={15} />}
                  {result.correct
                    ? result.first_time
                      ? "To'g'ri! +1 XP"
                      : "To'g'ri!"
                    : "Xato"}
                </p>
                {!result.correct && result.expected && (
                  <p className="text-sm text-slate-700 mt-1">
                    To'g'ri javob: <b>{result.expected}</b>
                  </p>
                )}
                {result.explain && (
                  <p className="text-xs text-slate-500 mt-1">
                    {result.explain}
                  </p>
                )}
                {/* SKRIPT (2026-08-11): topshiriq bajarilgach audio
                    matni ko'rinadi */}
                {q.kind?.startsWith("listen") && q.say && (
                  <p className="text-xs text-slate-600 mt-1.5 bg-white/60 rounded-lg px-2 py-1.5">
                    📜 Skript: <i>{q.say}</i>
                  </p>
                )}
                <button
                  onClick={next}
                  className="w-full mt-2.5 py-2.5 rounded-lg bg-slate-900 text-white text-sm font-semibold"
                >
                  {idx + 1 >= items.length ? "Yakunlash" : "Keyingisi"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
