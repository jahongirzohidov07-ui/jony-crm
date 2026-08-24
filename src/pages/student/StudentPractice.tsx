import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Check, Ear, Mic, PenLine, RotateCcw, Sparkles, Volume2, X,
} from "lucide-react";
import { api } from "../../lib/api";
import { autoNextDelay, useAutoNext } from "../../lib/useAutoNext";
import { getLang } from "../../lib/lang";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — 4 KO'NIKMA MASHG'ULOTI (2026-08-11, Jahongir
 * spetsifikatsiyasi bo'yicha kengaytirildi).
 *
 * Har ko'nikmada TUR TANLANADI:
 *  reading:  savol-javob / True-False-Not Given / bo'sh joy /
 *            sarlavha moslash;
 *  listening: diktant / rasmga (emoji) moslash / dialog savol-javob /
 *            tartiblash — 0.75x/1x tezlik va skript bilan;
 *  writing:  tarjima / qayta tuzish-kengaytirish;
 *  speaking: o'qib berish / eshitib takrorlash / savolga javob —
 *            natijada so'zlar rangda (yashil aytilgan, qizil xato).
 * Tekshiruv har doim serverda.
 */

const META: Record<string, { label: string; grad: string; icon: Any }> = {
  listening: { label: "Listening", grad: "from-amber-600 to-amber-500", icon: Ear },
  reading: { label: "Reading", grad: "from-sky-700 to-sky-500", icon: PenLine },
  writing: { label: "Writing", grad: "from-rose-600 to-rose-500", icon: PenLine },
  speaking: { label: "Speaking", grad: "from-teal-600 to-teal-500", icon: Mic },
};

const KINDS: Record<string, [string, string, string][]> = {
  reading: [
    ["read_mcq", "Savol-javob", "Matn o'qib, savollarga javob"],
    ["read_tfng", "True / False / Not Given", "Fikr matnga mosmi?"],
    ["read_gap", "Bo'sh joylarni to'ldirish", "Matn ichidagi tushib qolgan so'zlar"],
    ["read_match", "Sarlavhalarni moslash", "Har abzasga to'g'ri sarlavha"],
  ],
  listening: [
    ["dictation", "Diktant va tanlov", "Eshitib yozish yoki tanlash"],
    ["listen_img", "Rasmga moslash", "Eshitib mos rasmni tanlang"],
    ["listen_qa", "Dialog: savol-javob", "Suhbatni eshitib javob toping"],
    ["listen_order", "Tartiblash", "Voqealarni eshitib tartibga soling"],
  ],
  writing: [
    ["write_translate", "Tarjima qilish", "O'zbekchadan inglizchaga yozing"],
    ["write_transform", "Qayta tuzish", "Gapni birlashtiring yoki o'zgartiring"],
  ],
  speaking: [
    ["speak_read", "O'qib berish", "Jumlani mikrofonga o'qing"],
    ["speak_repeat", "Eshitib takrorlash", "Eshitganingizni aynan takrorlang"],
    ["speak_answer", "Savolga javob", "Savolga og'zaki javob bering"],
  ],
};

// Tanlangan tilga mos TTS ovozi (2026-08-21, Jahongir: listening
// aralashmasin). Komponent renderda yangilab turadi.
const TTS_LANGS: Record<string, string> = {
  en: "en-US", ru: "ru-RU", de: "de-DE", ko: "ko-KR",
};
let ttsLang = "en-US";

function speak(text: string, rate = 0.95) {
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = ttsLang;
    u.rate = rate;
    window.speechSynthesis.speak(u);
  } catch {
    /* TTS yo'q */
  }
}

/** Natijada so'zlarni bo'yash: aytilganlari yashil, qolgani qizil. */
function ColoredWords({ target, heard }: { target: string; heard: string }) {
  const said = new Set(
    heard.toLowerCase().replace(/[^a-z' ]/g, " ").split(/\s+/),
  );
  return (
    <p className="text-sm leading-relaxed mt-1">
      {target.split(/\s+/).map((w, i) => {
        const clean = w.toLowerCase().replace(/[^a-z']/g, "");
        return (
          <span
            key={i}
            className={
              said.has(clean)
                ? "text-emerald-700 font-medium"
                : "text-red-600 font-medium"
            }
          >
            {w}{" "}
          </span>
        );
      })}
    </p>
  );
}

export default function StudentPractice() {
  const { skill } = useParams();
  const m = META[skill || ""] || META.listening;
  // O'rganilayotgan til — listening shu til so'zlaridan tuziladi
  const lang = getLang();
  ttsLang = skill === "listening" ? TTS_LANGS[lang] || "en-US" : "en-US";
  const [kind, setKind] = useState<string | null>(null);
  // DARAJA BO'LIMLARI (2026-08-24, Jahongir: "reading listening
  // qismini a1 dan boshlab c2 darajagacha... bo'lim chiqib").
  // Boshqa tillar listeningida daraja yo'q — u faqat so'z diktanti.
  // 2026-08-24 (Jahongir: "Writingni ham darajalanmagan u ham")
  const needLevel =
    skill === "reading" || skill === "writing" ||
    (skill === "listening" && lang === "en");
  const [level, setLevel] = useState<string | null>(null);
  const [levels, setLevels] = useState<Any[]>([]);
  const [cnt, setCnt] = useState(10);
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
  const [rate, setRate] = useState(1.0);
  const [dict, setDict] = useState<Any>(null);
  const dictCache = useRef<Record<string, Any>>({});
  // Ko'p qismli javoblar: gap/match tanlovlari va tartiblash
  const [sel, setSel] = useState<Record<number, string>>({});
  const [seq, setSeq] = useState<string[]>([]);

  useEffect(() => {
    if (!needLevel) return;
    api
      .get<Any>(`/student/practice/${skill}/levels`)
      .then((r) => setLevels(r.levels || []))
      .catch(() => setLevels([]));
  }, [skill, needLevel]);

  const load = useCallback(() => {
    if (kind === null) return;
    if (needLevel && level === null) return;
    setErr("");
    setD(null);
    setIdx(0);
    setResult(null);
    setTyped("");
    setHeard("");
    setSel({});
    setSeq([]);
    setScore({ ok: 0, xp: 0 });
    setFinished(false);
    const oldKinds = ["read_mcq", "dictation", "write_translate", "speak_read"];
    const parts: string[] = [];
    if (!oldKinds.includes(kind)) parts.push(`kind=${kind}`);
    if (skill === "listening") parts.push(`language=${lang}`);
    if (needLevel && level) parts.push(`level=${level}`);
    // Mashqlar soni (2026-08-24: "mashqlarni ham kopaytir")
    if (cnt && kind !== "read_mcq") parts.push(`count=${cnt}`);
    const q = parts.length ? `?${parts.join("&")}` : "";
    api
      .get<Any>(`/student/practice/${skill}/round${q}`)
      .then((r) => setD(r))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [skill, kind, lang, level, cnt, needLevel]);

  useEffect(load, [load]);
  useEffect(() => () => window.speechSynthesis?.cancel(), []);
  useEffect(() => {
    setKind(null);
    setLevel(null);
  }, [skill]);

  const items: Any[] = d?.items || [];
  const q = items[idx];

  // Javobdan keyin o'zi keyingi savolga o'tadi (2026-08-18, Jahongir:
  // "shu narsa avtomat otsin keyingisiga"). Tugma qoladi — sanoq bilan.
  const autoNext = useAutoNext(() => next());

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
      // Skript (listening/speaking) va izoh — o'qishga vaqt kerak
      const hasExtra = !!r.explain || !!q.say;
      // Reading — matnli mashq (2026-08-21, Jahongir: "Readingda
      // berilgan vaqt kam kopaytirish kerak"): vaqt 3 barobar.
      // Listening XATO javobda (2026-08-24, Jahongir: "5 sekund
      // kamlik qilyabdi xatosini tushunish uchun"): vaqt 2.5x —
      // skript va to'g'ri javobni o'qishga ulguradi.
      const mult = skill === "reading" ? 3
        : skill === "listening" && !r.correct ? 2.5 : 1;
      autoNext.schedule(
        mult *
          autoNextDelay({
            correct: !!r.correct,
            hasAnswer: !!r.expected,
            hasExtra,
          }),
      );
    } catch {
      /* toast */
    } finally {
      setBusy(false);
    }
  }

  function next() {
    autoNext.cancel();
    window.speechSynthesis?.cancel();
    if (idx + 1 >= items.length) {
      setFinished(true);
      return;
    }
    setIdx(idx + 1);
    setResult(null);
    setTyped("");
    setHeard("");
    setSel({});
    setSeq([]);
  }

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
  const tappable = (body: string) =>
    String(body)
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
      );

  const OptButtons = ({ opts }: { opts: string[] }) => (
    <div className="space-y-1.5">
      {opts.map((o) => {
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
  );

  const SpeedButtons = ({ text }: { text: string }) => (
    <div className="flex gap-1.5 mb-3">
      {[
        [0.75, "0.75x sekin"],
        [1.0, "1x normal"],
      ].map(([v, lbl]) => (
        <button
          key={String(v)}
          onClick={() => {
            setRate(v as number);
            speak(text, v as number);
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
  );

  const AudioButton = ({ text, tone = "amber" }: Any) => (
    <button
      onClick={() => speak(text, rate)}
      className={`w-full py-5 rounded-xl bg-${tone}-50 border border-${tone}-200 flex items-center justify-center gap-2 text-${tone}-700 font-semibold text-sm mb-2 active:scale-[0.99]`}
    >
      <Volume2 size={20} />
      Eshitish
    </button>
  );

  const groupsDone = (n: number) => Object.keys(sel).length >= n;
  void Icon; // sarlavha dizayni o'zgardi, ikonka hozircha kerak emas

  // 2026-08-21: mashq sarlavhasi dizayn to'plamidagi kabi
  // (listening.png / reading.png / writing.png): X tugma, JONY
  // STUDENT APP, +XP/+Coin pilllari, N/M progress. Mashqning ichki
  // mantig'iga tegilmadi.
  return (
    <>
      <div className="max-w-md mx-auto px-4 pt-5 text-white">
        <div className="flex items-center gap-2.5">
          <Link to="/student/games"
            className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
            style={{ background: "#111C4B", borderColor: "#223070" }}>
            <X size={18} />
          </Link>
          <p className="text-[15px] font-extrabold tracking-wide flex-1">
            JONY STUDENT APP
          </p>
          <span className="inline-flex items-center gap-1 rounded-xl px-2.5 py-1.5 border text-[12px] font-bold shrink-0"
                style={{ background: "#111C4B", borderColor: "#223070" }}>
            ⬡ +10 XP
          </span>
          <span className="inline-flex items-center gap-1 rounded-xl px-2.5 py-1.5 border text-[12px] font-bold text-amber-300 shrink-0"
                style={{ background: "#111C4B", borderColor: "#5c4a15" }}>
            🪙 +3 Coin
          </span>
        </div>
        <div className="flex items-center gap-2 mt-3 mb-1">
          <p className="text-[22px] font-extrabold shrink-0">
            {!finished && kind && items.length > 0
              ? <>{Math.min(idx + 1, items.length)}
                 <span className="text-slate-400"> / {items.length}</span></>
              : m.label}
          </p>
          {!finished && kind && items.length > 0 && (
            <div className="flex-1 h-2 rounded-full overflow-hidden"
                 style={{ background: "#26326B" }}>
              <div className="h-full bg-brand-500 rounded-full transition-all"
                   style={{ width: `${((idx + (result ? 1 : 0)) / items.length) * 100}%` }} />
            </div>
          )}
          {kind && (
            <button onClick={() => setKind(null)}
              className="text-[11px] font-medium rounded-full px-2.5 py-1 border text-slate-300 shrink-0"
              style={{ background: "#111C4B", borderColor: "#223070" }}>
              turni almashtirish
            </button>
          )}
          {needLevel && level && (
            <button onClick={() => { setKind(null); setLevel(null); }}
              className="text-[11px] font-bold rounded-full px-2.5 py-1 border text-brand-300 shrink-0"
              style={{ background: "#111C4B", borderColor: "#223070" }}
              title="Darajani almashtirish">
              {level}
            </button>
          )}
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 mt-3 space-y-3 pb-8">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4">
            <p className="text-sm text-red-600">{err}</p>
            <button
              onClick={() => (kind === null ? setErr("") : load())}
              className="mt-2 text-sm font-medium text-slate-700 underline"
            >
              Qayta urinish
            </button>
          </div>
        )}

        {/* ---- DARAJA TANLASH (2026-08-24) ---- */}
        {needLevel && level === null && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-1">
              Darajangizni tanlang
            </p>
            <p className="text-[11px] text-slate-400 mb-3">
              Beginner (A1) dan Native (C2) gacha — har bo'limda o'z
              darajangizga mos mashqlar.
            </p>
            <div className="space-y-1.5">
              {levels.map((lv: Any) => {
                const empty = !lv.total;
                return (
                  <button
                    key={lv.level}
                    disabled={empty}
                    onClick={() => setLevel(lv.level)}
                    className={`w-full flex items-center gap-3 border rounded-xl p-3.5 text-left transition ${
                      empty
                        ? "border-slate-100 opacity-50"
                        : "border-slate-200 active:scale-[0.99]"
                    }`}
                  >
                    <div className="w-11 h-9 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center shrink-0 text-sm font-extrabold">
                      {lv.level}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800">
                        {lv.label}
                      </p>
                      <p className="text-[11px] text-slate-400">
                        {empty
                          ? "Mashqlar tez orada qo'shiladi"
                          : `${lv.solved}/${lv.total} bajarildi`}
                      </p>
                    </div>
                    {!empty && (
                      <div className="w-16 shrink-0">
                        <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                          <div className="h-full bg-sky-500 rounded-full"
                               style={{ width: `${lv.percent}%` }} />
                        </div>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ---- TUR TANLASH ---- */}
        {kind === null && (!needLevel || level !== null) && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Qaysi turdagi mashqni xohlaysiz?
            </p>
            <div className="flex items-center gap-1.5 mb-3">
              <span className="text-[11px] text-slate-400 mr-1">Soni:</span>
              {[10, 20, 30].map((n) => (
                <button
                  key={n}
                  onClick={() => setCnt(n)}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                    cnt === n
                      ? "bg-slate-800 text-white border-transparent"
                      : "bg-white text-slate-500 border-slate-200"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <div className="space-y-1.5">
              {(KINDS[skill || ""] || [])
                .filter(
                  ([k]) =>
                    !(skill === "listening" && lang !== "en" &&
                      k !== "dictation"),
                )
                .map(([k, lbl, hint]) => (
                <button
                  key={k}
                  onClick={() => setKind(k)}
                  className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                >
                  <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center shrink-0 text-sm font-bold">
                    {lbl.charAt(0)}
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

        {/* Reading matni (read_mcq va read_tfng) */}
        {!finished && kind && d?.text && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-baseline justify-between mb-1.5">
              <p className="text-sm font-semibold text-slate-800">
                {d.text.title}
              </p>
              <span className="text-[10px] font-bold text-sky-600 bg-sky-50 px-1.5 py-0.5 rounded">
                {d.text.level}
              </span>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">
              {tappable(d.text.body)}
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
                So'z ustiga bossangiz — tarjimasi
              </p>
            </div>
          </div>
        )}

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
              <button
                onClick={() => setKind(null)}
                className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold"
              >
                Boshqa tur
              </button>
            </div>
          </div>
        )}

        {!finished && kind && q && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            {/* ---- LISTENING: diktant (eski) ---- */}
            {["listen_type", "listen_choice", "listen_dictation"].includes(
              q.kind,
            ) && (
              <>
                <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wide mb-3">
                  {q.kind === "listen_choice"
                    ? "Eshiting va tarjimasini tanlang"
                    : "Eshiting va yozing"}
                </p>
                <AudioButton text={q.say} />
                <SpeedButtons text={q.say} />
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

            {/* ---- LISTENING: rasmga moslash ---- */}
            {q.kind === "listen_img" && (
              <>
                <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wide mb-3">
                  Eshiting va mos rasmni tanlang
                </p>
                <AudioButton text={q.say} />
                <SpeedButtons text={q.say} />
                <div className="grid grid-cols-2 gap-2">
                  {(q.options || []).map((o: Any) => {
                    const isMine = result && o.label === result._mine;
                    const isAns = result && o.label === result.expected;
                    return (
                      <button
                        key={o.label}
                        disabled={!!result || busy}
                        onClick={() => submit(o.label)}
                        className={`rounded-xl border-2 py-4 flex flex-col items-center gap-1 ${
                          isAns
                            ? "border-emerald-500 bg-emerald-50"
                            : isMine
                              ? "border-red-500 bg-red-50"
                              : "border-slate-200 bg-white"
                        }`}
                      >
                        <span className="text-4xl">{o.emoji}</span>
                        <span className="text-[11px] text-slate-500">
                          {o.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {/* ---- LISTENING: dialog savol-javob ---- */}
            {q.kind === "listen_qa" && (
              <>
                <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wide mb-3">
                  Suhbatni eshiting va javob bering
                </p>
                <AudioButton text={q.say} />
                <SpeedButtons text={q.say} />
                <p className="text-sm font-medium text-slate-900 mb-2">
                  {q.prompt}
                </p>
                <OptButtons opts={q.options || []} />
              </>
            )}

            {/* ---- LISTENING: tartiblash ---- */}
            {q.kind === "listen_order" && (
              <>
                <p className="text-[11px] font-semibold text-amber-600 uppercase tracking-wide mb-3">
                  Eshiting va voqealarni TARTIB bilan bosing
                </p>
                <AudioButton text={q.say} />
                <SpeedButtons text={q.say} />
                <div className="min-h-[52px] border-2 border-dashed border-slate-200 rounded-xl p-2 mb-2 space-y-1">
                  {seq.map((st, i) => (
                    <button
                      key={`${st}-${i}`}
                      disabled={!!result}
                      onClick={() =>
                        setSeq((p) => p.filter((_, j) => j !== i))
                      }
                      className="w-full text-left px-2.5 py-1.5 rounded-lg bg-amber-600 text-white text-xs font-medium"
                    >
                      {i + 1}. {st}
                    </button>
                  ))}
                  {seq.length === 0 && (
                    <p className="text-xs text-slate-300 px-1 py-2">
                      Birinchi voqeadan boshlab bosing...
                    </p>
                  )}
                </div>
                <div className="space-y-1">
                  {(q.options || [])
                    .filter((o: string) => !seq.includes(o))
                    .map((o: string) => (
                      <button
                        key={o}
                        disabled={!!result}
                        onClick={() => setSeq((p) => [...p, o])}
                        className="w-full text-left px-2.5 py-2 rounded-lg border border-slate-200 text-xs font-medium text-slate-700"
                      >
                        {o}
                      </button>
                    ))}
                </div>
                {!result && seq.length === (q.options || []).length && (
                  <button
                    disabled={busy}
                    onClick={() => submit(seq.join("|"))}
                    className="w-full mt-2 py-3 rounded-xl bg-amber-600 text-white text-sm font-semibold"
                  >
                    Tekshirish
                  </button>
                )}
              </>
            )}

            {/* ---- READING: MCQ (eski) va TFNG ---- */}
            {(q.kind === "read_mcq" || q.kind === "read_tfng") && (
              <>
                <p className="text-[11px] font-semibold text-sky-600 uppercase tracking-wide mb-2">
                  {q.kind === "read_tfng"
                    ? "Bu fikr matnga mosmi?"
                    : `Savol ${idx + 1}`}
                </p>
                <p className="text-base font-medium text-slate-900 mb-3">
                  {q.prompt}
                </p>
                <OptButtons opts={q.options || []} />
                {q.kind === "read_tfng" && !result && (
                  <p className="text-[10px] text-slate-400 mt-2">
                    Not Given = matnda bu haqda ma'lumot yo'q
                  </p>
                )}
              </>
            )}

            {/* ---- READING: bo'sh joy / sarlavha moslash ---- */}
            {(q.kind === "read_gap" || q.kind === "read_match") && (
              <>
                <p className="text-[11px] font-semibold text-sky-600 uppercase tracking-wide mb-2">
                  {q.kind === "read_gap"
                    ? "Matndagi bo'sh joylarni to'ldiring"
                    : "Har abzasga sarlavha tanlang"}
                </p>
                {q.kind === "read_gap" ? (
                  <p className="text-sm text-slate-700 leading-relaxed mb-3 whitespace-pre-line">
                    {tappable(q.text)}
                  </p>
                ) : (
                  <div className="space-y-2 mb-3">
                    {(q.paragraphs || []).map((p: string, i: number) => (
                      <div
                        key={i}
                        className="bg-slate-50 rounded-lg p-2.5 text-sm text-slate-700"
                      >
                        <b className="text-sky-600">{i + 1}.</b>{" "}
                        {tappable(p)}
                      </div>
                    ))}
                  </div>
                )}
                <div className="space-y-3">
                  {(q.options || []).map((grp: string[], bi: number) => (
                    <div key={bi}>
                      <p className="text-[11px] text-slate-500 mb-1">
                        ({bi + 1}) uchun:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {grp.map((o) => (
                          <button
                            key={o}
                            disabled={!!result}
                            onClick={() =>
                              setSel((c) => ({ ...c, [bi]: o }))
                            }
                            className={`px-3 py-2 rounded-lg border text-xs font-medium ${
                              sel[bi] === o
                                ? "bg-sky-600 text-white border-transparent"
                                : "bg-white text-slate-700 border-slate-200"
                            }`}
                          >
                            {o}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                  {!result && (
                    <button
                      disabled={busy || !groupsDone((q.options || []).length)}
                      onClick={() =>
                        submit(
                          (q.options || [])
                            .map((_: Any, bi: number) => sel[bi] || "")
                            .join("|"),
                        )
                      }
                      className="w-full py-3 rounded-xl bg-sky-600 text-white text-sm font-semibold disabled:opacity-40"
                    >
                      Tekshirish
                    </button>
                  )}
                </div>
              </>
            )}

            {/* ---- WRITING: tarjima (eski) ---- */}
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

            {/* ---- WRITING: qayta tuzish ---- */}
            {q.kind === "write_transform" && (
              <>
                <p className="text-[11px] font-semibold text-rose-600 uppercase tracking-wide mb-2">
                  {q.instruction}
                </p>
                <p className="text-base font-medium text-slate-900 mb-3 bg-rose-50 rounded-lg px-3 py-2">
                  {q.given}
                </p>
                {!result && (
                  <div className="space-y-2">
                    <input
                      value={typed}
                      onChange={(e) => setTyped(e.target.value)}
                      placeholder="Yangi gapni yozing..."
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

            {/* ---- SPEAKING: o'qib berish (eski) ---- */}
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
              </>
            )}

            {/* ---- SPEAKING: eshitib takrorlash ---- */}
            {q.kind === "speak_repeat" && (
              <>
                <p className="text-[11px] font-semibold text-teal-600 uppercase tracking-wide mb-2">
                  Eshiting va AYNAN takrorlang
                </p>
                <AudioButton text={q.say} tone="teal" />
                <p className="text-[11px] text-slate-400 mb-3">
                  Matn ko'rsatilmaydi — faqat eshitib takrorlang
                </p>
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
                    {listening ? "Eshitilmoqda... gapiring" : "Takrorlash"}
                  </button>
                )}
              </>
            )}

            {/* ---- SPEAKING: savolga javob ---- */}
            {q.kind === "speak_answer" && (
              <>
                <p className="text-[11px] font-semibold text-teal-600 uppercase tracking-wide mb-2">
                  Savolga og'zaki javob bering
                </p>
                <p className="text-base font-semibold text-slate-900 mb-1">
                  {q.say}
                </p>
                <button
                  onClick={() => speak(q.say)}
                  className="text-xs text-teal-600 font-medium flex items-center gap-1 mb-2"
                >
                  <Volume2 size={13} />
                  Savolni eshitish
                </button>
                <p className="text-[11px] text-slate-400 mb-3">
                  Namuna: {q.hint}
                </p>
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
                    {listening ? "Eshitilmoqda... gapiring" : "Javob berish"}
                  </button>
                )}
              </>
            )}

            {heard && (
              <p className="text-xs text-slate-500 mt-2">
                Siz aytdingiz: "{heard}"
              </p>
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
                {/* SO'Z RANGLARI: aytilganlari yashil, xatolari qizil */}
                {(q.kind === "speak_read" || q.kind === "speak_repeat") &&
                  result.expected &&
                  heard && (
                    <ColoredWords target={result.expected} heard={heard} />
                  )}
                {!result.correct &&
                  result.expected &&
                  !(q.kind === "speak_read" || q.kind === "speak_repeat") && (
                    <p className="text-sm text-slate-700 mt-1">
                      To'g'ri javob: <b>{result.expected}</b>
                    </p>
                  )}
                {result.explain && (
                  <p className="text-xs text-slate-500 mt-1">
                    {result.explain}
                  </p>
                )}
                {(q.kind?.startsWith("listen") || q.kind === "speak_repeat") &&
                  q.say && (
                    <p className="text-xs text-slate-600 mt-1.5 bg-white/60 rounded-lg px-2 py-1.5">
                      📜 Skript: <i>{q.say}</i>
                    </p>
                  )}
                <button
                  onClick={next}
                  className="w-full mt-2.5 py-2.5 rounded-lg bg-slate-900 text-white text-sm font-semibold"
                >
                  {idx + 1 >= items.length ? "Yakunlash" : "Keyingisi"}
                  {autoNext.secsLeft > 0 ? ` (${autoNext.secsLeft})` : ""}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
