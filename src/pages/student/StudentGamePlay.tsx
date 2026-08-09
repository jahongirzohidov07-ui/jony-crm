import {
  useCallback, useEffect, useState,
  type FormEvent, type ReactNode,
} from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, RotateCcw, X } from "lucide-react";
import { api } from "../../lib/api";
import type { AnswerResult, RoundItem, VocabRound } from "../../lib/studentApi";

/**
 * JONY STUDENT — o'yin maydoni (2026-08-09).
 *
 * ATAYLAB BITTA komponent barcha o'yin turlarini yuritadi: savollar
 * serverdan bir xil ko'rinishda keladi (RoundItem), farqi faqat
 * qaysi maydonlar to'lganida. Shuning uchun yangi o'yin qo'shish =
 * backend'da roles.VOCAB_GAMES ga bitta qator + shu yerda bitta
 * ko'rinish — butun ilovani qayta yozish shart emas.
 *
 * BALL SERVERDA: har javob /student/vocab/answer ga yuboriladi va
 * to'g'riligini server o'zi hal qiladi. Bu yerdagi "to'g'ri/xato"
 * ko'rinishi ham serverning javobiga qarab chiziladi — telefondagi
 * kodni o'zgartirib ball yig'ib bo'lmaydi.
 */
export default function StudentGamePlay() {
  const { game = "en_uz" } = useParams();
  const [round, setRound] = useState<VocabRound | null>(null);
  const [err, setErr] = useState("");
  const [idx, setIdx] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [feedback, setFeedback] = useState<AnswerResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const load = useCallback(() => {
    setErr("");
    setRound(null);
    setIdx(0);
    setCorrectCount(0);
    setFeedback(null);
    setDone(false);
    api
      .get<VocabRound>(`/student/vocab/round?game=${game}`)
      .then(setRound)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [game]);

  useEffect(load, [load]);

  /** Javobni serverga yuboradi.
   *
   * wordId — juftlash (match) o'yini uchun: u yerda BITTA "item"
   * ichida bir nechta so'z bor, shuning uchun qaysi so'z ekanini
   * o'yin o'zi aytadi. Qolgan o'yinlarda joriy savolning so'zi.
   *
   * silent — juftlashda har juftlik uchun katta "To'g'ri!" oynasi
   * chiqmasin (o'yin ravon ketsin); ball baribir yoziladi. */
  async function answer(value: string, wordId?: number, silent = false) {
    if (!round || busy || (feedback && !silent)) return;
    const item = round.items[idx];
    const wid = wordId ?? item.word_id;
    if (!wid) return;
    setBusy(true);
    try {
      const res = await api.post<AnswerResult>("/student/vocab/answer", {
        word_id: wid,
        game: round.game,
        answer: value,
        // "To'g'ri/Xato" uchun: ekranda qaysi tarjima turganini ham
        // yuboramiz, chunki to'g'riligini SERVER hal qiladi.
        shown: item.shown,
      });
      if (res.correct) setCorrectCount((c) => c + 1);
      if (!silent) setFeedback(res);
    } catch {
      // xato toast orqali ko'rinadi (api.ts)
    } finally {
      setBusy(false);
    }
  }

  function next() {
    setFeedback(null);
    if (!round) return;
    if (idx + 1 >= round.items.length) setDone(true);
    else setIdx((i) => i + 1);
  }

  if (err)
    return (
      <Shell title="Mashq">
        <p className="text-sm text-slate-500 text-center py-16 px-6">{err}</p>
      </Shell>
    );
  if (!round)
    return (
      <Shell title="Mashq">
        <p className="text-sm text-slate-400 text-center py-16">Yuklanmoqda…</p>
      </Shell>
    );

  if (done) {
    const pct = Math.round((correctCount / round.items.length) * 100);
    return (
      <Shell title={round.label}>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 text-center">
          <p className="text-5xl mb-2">
            {pct >= 80 ? "🎉" : pct >= 50 ? "👍" : "💪"}
          </p>
          <p className="text-2xl font-bold text-slate-900">
            {correctCount} / {round.items.length}
          </p>
          <p className="text-sm text-slate-500 mt-1">
            {pct}% to'g'ri · +{correctCount} ball
          </p>
          <button
            onClick={load}
            className="mt-5 w-full py-3 rounded-xl bg-brand-600 text-white text-sm font-medium flex items-center justify-center gap-2"
          >
            <RotateCcw size={16} />
            Yana o'ynash
          </button>
          <Link
            to="/student/games"
            className="mt-2 block w-full py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium"
          >
            Boshqa o'yin
          </Link>
        </div>
      </Shell>
    );
  }

  const item = round.items[idx];
  const progress = ((idx + (feedback ? 1 : 0)) / round.items.length) * 100;

  return (
    <Shell title={round.label}>
      <div className="mb-4">
        <div className="flex justify-between text-[11px] text-slate-500 mb-1">
          <span>
            {idx + 1} / {round.items.length}
          </span>
          <span>{correctCount} to'g'ri</span>
        </div>
        <div className="h-1.5 rounded-full bg-slate-200 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        {round.game === "flashcard" && (
          <Flashcard item={item} onAnswer={answer} disabled={!!feedback} />
        )}
        {(round.game === "en_uz" || round.game === "uz_en") && (
          <Choice
            item={item}
            onAnswer={answer}
            feedback={feedback}
            disabled={!!feedback}
          />
        )}
        {round.game === "spelling" && (
          <Spelling item={item} onAnswer={answer} disabled={!!feedback} />
        )}
        {round.game === "truefalse" && (
          <TrueFalse item={item} onAnswer={answer} disabled={!!feedback} />
        )}
        {round.game === "scramble" && (
          <Scramble item={item} onAnswer={answer} disabled={!!feedback} />
        )}
        {round.game === "match" && (
          <Match
            item={item}
            onPair={(text, wordId) => answer(text, wordId, true)}
            onFinish={() => setDone(true)}
          />
        )}
      </div>

      {feedback && (
        <div
          className={`mt-4 rounded-xl p-4 flex items-start gap-2.5 ${
            feedback.correct
              ? "bg-emerald-50 border border-emerald-200"
              : "bg-red-50 border border-red-200"
          }`}
        >
          {feedback.correct ? (
            <Check size={18} className="text-emerald-600 mt-0.5 shrink-0" />
          ) : (
            <X size={18} className="text-red-500 mt-0.5 shrink-0" />
          )}
          <div className="flex-1 min-w-0">
            <p
              className={`text-sm font-medium ${
                feedback.correct ? "text-emerald-800" : "text-red-800"
              }`}
            >
              {feedback.correct ? "To'g'ri!" : "To'g'ri javob:"}
            </p>
            {!feedback.correct && (
              <p className="text-sm text-red-700">{feedback.expected}</p>
            )}
          </div>
          <button
            onClick={next}
            className="text-xs font-medium px-3.5 py-2 rounded-lg bg-slate-900 text-white shrink-0"
          >
            Keyingi
          </button>
        </div>
      )}
    </Shell>
  );
}

function Shell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-8">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/games"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            O'yinlar
          </Link>
          <h1 className="text-lg font-semibold">{title}</h1>
        </div>
      </div>
      <div className="max-w-md mx-auto px-4 -mt-4">{children}</div>
    </>
  );
}

/* ---------------- Kartochka: o'quvchi o'zini o'zi tekshiradi ------- */
function Flashcard({
  item,
  onAnswer,
  disabled,
}: {
  item: RoundItem;
  onAnswer: (v: string) => void;
  disabled: boolean;
}) {
  const [shown, setShown] = useState(false);
  useEffect(() => setShown(false), [item.word_id]);

  return (
    <div className="text-center">
      <p className="text-3xl font-bold text-slate-900 py-6">{item.prompt}</p>
      {shown ? (
        <>
          <p className="text-lg text-brand-700 font-medium pb-2">
            {item.answer}
          </p>
          {item.example && (
            <p className="text-xs text-slate-400 pb-4">{item.example}</p>
          )}
          <div className="grid grid-cols-2 gap-2">
            <button
              disabled={disabled}
              onClick={() => onAnswer("bilmadim")}
              className="py-3 rounded-xl border border-red-200 text-red-600 text-sm font-medium"
            >
              Bilmadim
            </button>
            <button
              disabled={disabled}
              onClick={() => onAnswer("bildim")}
              className="py-3 rounded-xl bg-emerald-600 text-white text-sm font-medium"
            >
              Bildim
            </button>
          </div>
        </>
      ) : (
        <button
          onClick={() => setShown(true)}
          className="w-full py-3 rounded-xl bg-brand-600 text-white text-sm font-medium"
        >
          Tarjimasini ko'rsat
        </button>
      )}
    </div>
  );
}

/* ---------------- 4 variantli tanlov ------------------------------- */
function Choice({
  item,
  onAnswer,
  feedback,
  disabled,
}: {
  item: RoundItem;
  onAnswer: (v: string) => void;
  feedback: AnswerResult | null;
  disabled: boolean;
}) {
  const [picked, setPicked] = useState<string | null>(null);
  useEffect(() => setPicked(null), [item.word_id]);

  return (
    <div>
      <p className="text-2xl font-bold text-slate-900 text-center py-5">
        {item.prompt}
      </p>
      <div className="space-y-2">
        {(item.options || []).map((opt) => {
          let cls = "border-slate-200 text-slate-700";
          if (feedback && picked === opt)
            cls = feedback.correct
              ? "border-emerald-400 bg-emerald-50 text-emerald-800"
              : "border-red-400 bg-red-50 text-red-800";
          else if (feedback && opt === feedback.expected)
            cls = "border-emerald-400 bg-emerald-50 text-emerald-800";
          return (
            <button
              key={opt}
              disabled={disabled}
              onClick={() => {
                setPicked(opt);
                onAnswer(opt);
              }}
              className={`w-full text-left px-4 py-3 rounded-xl border text-sm font-medium transition ${cls}`}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ---------------- Imlo: so'zni yozib chiqish ----------------------- */
function Spelling({
  item,
  onAnswer,
  disabled,
}: {
  item: RoundItem;
  onAnswer: (v: string) => void;
  disabled: boolean;
}) {
  const [val, setVal] = useState("");
  useEffect(() => setVal(""), [item.word_id]);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!val.trim()) return;
    onAnswer(val.trim());
  }

  return (
    <form onSubmit={submit}>
      <p className="text-xs text-slate-500 text-center">Shu so'zni inglizcha yozing</p>
      <p className="text-2xl font-bold text-slate-900 text-center py-4">
        {item.prompt}
      </p>
      {item.hint && (
        <p className="text-center text-sm text-slate-400 tracking-widest pb-3">
          {item.hint}
        </p>
      )}
      <input
        value={val}
        onChange={(e) => setVal(e.target.value)}
        disabled={disabled}
        autoFocus
        autoCapitalize="none"
        autoCorrect="off"
        spellCheck={false}
        className="w-full rounded-xl border border-slate-300 px-4 py-3 text-center text-lg focus:outline-none focus:ring-2 focus:ring-brand-400"
        placeholder="javobingiz"
      />
      <button
        type="submit"
        disabled={disabled || !val.trim()}
        className="mt-3 w-full py-3 rounded-xl bg-brand-600 text-white text-sm font-medium disabled:opacity-40"
      >
        Tekshirish
      </button>
    </form>
  );
}

/* ---------------- To'g'ri / Xato --------------------------------- */
function TrueFalse({
  item,
  onAnswer,
  disabled,
}: {
  item: RoundItem;
  onAnswer: (v: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="text-center">
      <p className="text-2xl font-bold text-slate-900 pt-4">{item.prompt}</p>
      <p className="text-xs text-slate-400 py-1">tarjimasi shumi?</p>
      <p className="text-xl font-medium text-brand-700 pb-6">{item.shown}</p>
      <div className="grid grid-cols-2 gap-2">
        <button
          disabled={disabled}
          onClick={() => onAnswer("xato")}
          className="py-3.5 rounded-xl border border-red-200 text-red-600 text-sm font-semibold active:bg-red-50 disabled:opacity-50"
        >
          ✗ Xato
        </button>
        <button
          disabled={disabled}
          onClick={() => onAnswer("togri")}
          className="py-3.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold active:bg-emerald-700 disabled:opacity-50"
        >
          ✓ To'g'ri
        </button>
      </div>
    </div>
  );
}

/* ---------------- Harflarni tartiblash --------------------------- */
function Scramble({
  item,
  onAnswer,
  disabled,
}: {
  item: RoundItem;
  onAnswer: (v: string) => void;
  disabled: boolean;
}) {
  // Tanlangan harflar indeks bo'yicha saqlanadi — bir xil harf ikki
  // marta uchrasa ham ("letter" emas, "index") chalkashmaydi.
  const [picked, setPicked] = useState<number[]>([]);
  useEffect(() => setPicked([]), [item.word_id]);

  const letters = item.letters || [];
  const built = picked.map((i) => letters[i]).join("");

  return (
    <div className="text-center">
      <p className="text-xs text-slate-500 pt-2">Shu so'zni harflardan yig'ing</p>
      <p className="text-xl font-bold text-slate-900 py-3">{item.prompt}</p>

      <div className="min-h-[52px] rounded-xl border-2 border-dashed border-slate-200 flex items-center justify-center gap-1 px-3 py-2 mb-4">
        {built ? (
          <span className="text-2xl font-bold tracking-widest text-brand-700">
            {built}
          </span>
        ) : (
          <span className="text-sm text-slate-300">harflarni bosing</span>
        )}
      </div>

      <div className="flex flex-wrap justify-center gap-2 mb-4">
        {letters.map((ch, i) => (
          <button
            key={i}
            disabled={disabled || picked.includes(i)}
            onClick={() => setPicked((p) => [...p, i])}
            className={`w-11 h-11 rounded-xl border text-lg font-bold transition ${
              picked.includes(i)
                ? "border-slate-100 bg-slate-50 text-slate-300"
                : "border-slate-300 text-slate-800 active:bg-slate-100"
            }`}
          >
            {ch}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          disabled={disabled || picked.length === 0}
          onClick={() => setPicked((p) => p.slice(0, -1))}
          className="py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium disabled:opacity-40"
        >
          O'chirish
        </button>
        <button
          disabled={disabled || picked.length !== letters.length}
          onClick={() => onAnswer(built)}
          className="py-3 rounded-xl bg-brand-600 text-white text-sm font-medium disabled:opacity-40"
        >
          Tekshirish
        </button>
      </div>
    </div>
  );
}

/* ---------------- Juftlash ----------------------------------------- */
function Match({
  item,
  onPair,
  onFinish,
}: {
  item: RoundItem;
  onPair: (text: string, wordId: number) => void;
  onFinish: () => void;
}) {
  const [pickedLeft, setPickedLeft] = useState<number | null>(null);
  const [solved, setSolved] = useState<number[]>([]);
  const [wrong, setWrong] = useState<number | null>(null);

  const left = item.left || [];
  const right = item.right || [];
  const allDone = left.length > 0 && solved.length === left.length;

  function tapRight(wordId: number, text: string) {
    if (pickedLeft === null || solved.includes(wordId)) return;
    if (wordId === pickedLeft) {
      setSolved((s) => [...s, wordId]);
      setPickedLeft(null);
      onPair(text, wordId);
    } else {
      setWrong(wordId);
      setTimeout(() => setWrong(null), 500);
      setPickedLeft(null);
    }
  }

  return (
    <div>
      <p className="text-xs text-slate-500 text-center pb-3">
        So'zni tarjimasi bilan juftlang
      </p>
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-2">
          {left.map((l) => (
            <button
              key={l.word_id}
              disabled={solved.includes(l.word_id)}
              onClick={() => setPickedLeft(l.word_id)}
              className={`w-full px-3 py-2.5 rounded-xl border text-sm font-medium transition ${
                solved.includes(l.word_id)
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700 opacity-60"
                  : pickedLeft === l.word_id
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-slate-200 text-slate-700"
              }`}
            >
              {l.text}
            </button>
          ))}
        </div>
        <div className="space-y-2">
          {right.map((r) => (
            <button
              key={r.word_id}
              disabled={solved.includes(r.word_id)}
              onClick={() => tapRight(r.word_id, r.text)}
              className={`w-full px-3 py-2.5 rounded-xl border text-sm font-medium transition ${
                solved.includes(r.word_id)
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700 opacity-60"
                  : wrong === r.word_id
                    ? "border-red-400 bg-red-50 text-red-700"
                    : "border-slate-200 text-slate-700"
              }`}
            >
              {r.text}
            </button>
          ))}
        </div>
      </div>
      {allDone && (
        <button
          onClick={onFinish}
          className="mt-4 w-full py-3 rounded-xl bg-emerald-600 text-white text-sm font-medium"
        >
          Hammasi juftlandi! Yakunlash 🎉
        </button>
      )}
    </div>
  );
}
