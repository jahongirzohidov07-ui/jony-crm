/**
 * OFFLINE MASHQLAR (2026-10-07).
 *
 * Jahongir: "ilovada offline rejimda ham mashqlar ishlash mumkin
 * bo'lsin". Internet bo'lmasa ham o'quvchi lug'at va grammatika
 * mashqini davom ettiradi. Javoblar telefonda tekshiriladi va
 * navbatga yoziladi; internet qaytgach serverga yuboriladi va XP
 * o'shanda beriladi (lib/offline.ts).
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle2, CloudOff, PenLine, RefreshCw, XCircle } from "lucide-react";
import { getLang } from "../../lib/lang";
import {
  enqueue, flushQueue, isOnline, loadPack, readQueue, refreshPack, sample,
  type OfflineGrammar, type OfflinePack, type OfflineWord,
} from "../../lib/offline";

const ROUND = 10;

type Q =
  | { kind: "vocab"; word: OfflineWord; options: string[]; answer: string }
  | { kind: "grammar"; g: OfflineGrammar; options: string[]; answer: string };

function buildVocab(pack: OfflinePack): Q[] {
  const words = pack.vocab;
  if (words.length < 4) return [];
  return sample(words, Math.min(ROUND, words.length)).map((w) => {
    const others = sample(
      words.filter((x) => x.id !== w.id && x.translation !== w.translation),
      3,
    ).map((x) => x.translation);
    return {
      kind: "vocab" as const,
      word: w,
      options: sample([w.translation, ...others], 4),
      answer: w.translation,
    };
  });
}

function buildGrammar(pack: OfflinePack): Q[] {
  return sample(pack.grammar, Math.min(ROUND, pack.grammar.length)).map((g) => ({
    kind: "grammar" as const,
    g,
    options: g.options,
    answer: g.answer,
  }));
}

export default function StudentOffline() {
  const lang = getLang();
  const [pack, setPack] = useState<OfflinePack | null>(() => loadPack(lang));
  const [online, setOnline] = useState(isOnline());
  const [pending, setPending] = useState(readQueue().length);
  const [mode, setMode] = useState<"menu" | "vocab" | "grammar">("menu");
  const [qs, setQs] = useState<Q[]>([]);
  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    const q = () => setPending(readQueue().length);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    window.addEventListener("jony-offline-queue", q);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
      window.removeEventListener("jony-offline-queue", q);
    };
  }, []);

  async function download() {
    setLoading(true);
    const p = await refreshPack(lang, true);
    setPack(p);
    await flushQueue();
    setPending(readQueue().length);
    setLoading(false);
  }

  function start(m: "vocab" | "grammar") {
    if (!pack) return;
    const list = m === "vocab" ? buildVocab(pack) : buildGrammar(pack);
    if (!list.length) return;
    setQs(list);
    setIdx(0);
    setPicked(null);
    setScore(0);
    setMode(m);
  }

  const cur = qs[idx];
  const done = mode !== "menu" && idx >= qs.length;

  function choose(opt: string) {
    if (!cur || picked !== null) return;
    setPicked(opt);
    const ok = opt === cur.answer;
    if (ok) setScore((s) => s + 1);
    if (cur.kind === "vocab") {
      enqueue({
        path: "/student/vocab/answer",
        body: { word_id: cur.word.id, game: "en_uz", answer: opt },
      });
    } else {
      enqueue({
        path: "/student/grammar/answer",
        body: { question_id: cur.g.id, answer: opt },
      });
    }
    // Internet bo'lsa — darrov yuboriladi (navbat bo'shab turadi)
    if (isOnline()) void flushQueue();
  }

  function next() {
    setPicked(null);
    setIdx((i) => i + 1);
  }

  const savedText = useMemo(() => {
    if (!pack?.saved_at) return null;
    const d = new Date(pack.saved_at);
    return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")} ${d.getHours()}:${String(
      d.getMinutes(),
    ).padStart(2, "0")}`;
  }, [pack]);

  return (
    <div className="max-w-md mx-auto px-4 py-5">
      <div className="flex items-center gap-3 mb-4">
        {mode === "menu" ? (
          <Link to="/student" className="p-2 -ml-2 text-slate-500"><ArrowLeft size={20} /></Link>
        ) : (
          <button onClick={() => setMode("menu")} className="p-2 -ml-2 text-slate-500">
            <ArrowLeft size={20} />
          </button>
        )}
        <h1 className="text-lg font-semibold text-slate-900">Offline mashqlar</h1>
      </div>

      <div className={`flex items-start gap-2 rounded-xl px-3 py-2.5 mb-4 text-sm ${
        online ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>
        <CloudOff size={18} className="shrink-0 mt-0.5" />
        <div>
          {online
            ? "Internet bor. Mashqlar telefonga yuklab olingan — internet uzilsa ham shu yerda davom etasiz."
            : "Internet yo'q. Mashq qilavering — javoblaringiz saqlanadi va internet qaytganda ball qo'shiladi."}
          {pending > 0 && (
            <div className="mt-1 font-medium">Yuborilishini kutayotgan javoblar: {pending} ta</div>
          )}
        </div>
      </div>

      {mode === "menu" && (
        <>
          {!pack ? (
            <div className="student-panel bg-white rounded-2xl border border-slate-200 p-5 text-center">
              <p className="text-sm text-slate-600 mb-4">
                Offline mashqlar hali yuklanmagan. Internet bor paytda bir marta yuklab oling.
              </p>
              <button
                onClick={download}
                disabled={!online || loading}
                className="inline-flex items-center gap-2 bg-blue-600 text-white rounded-xl px-4 py-2.5 text-sm font-medium disabled:opacity-50"
              >
                <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
                {loading ? "Yuklanmoqda..." : "Yuklab olish"}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <button
                onClick={() => start("vocab")}
                disabled={pack.vocab.length < 4}
                className="w-full student-panel bg-white rounded-2xl border border-slate-200 p-4 flex items-center gap-3 text-left disabled:opacity-50"
              >
                <span className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <BookOpen size={22} />
                </span>
                <span className="flex-1">
                  <span className="block font-semibold text-slate-900">Lug'at</span>
                  <span className="block text-xs text-slate-500">{pack.vocab.length} ta so'z · {ROUND} ta savol</span>
                </span>
              </button>
              <button
                onClick={() => start("grammar")}
                disabled={pack.grammar.length === 0}
                className="w-full student-panel bg-white rounded-2xl border border-slate-200 p-4 flex items-center gap-3 text-left disabled:opacity-50"
              >
                <span className="w-11 h-11 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
                  <PenLine size={22} />
                </span>
                <span className="flex-1">
                  <span className="block font-semibold text-slate-900">Grammatika</span>
                  <span className="block text-xs text-slate-500">{pack.grammar.length} ta savol · {ROUND} tadan</span>
                </span>
              </button>
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <span>Yuklangan: {savedText || "—"}</span>
                <button onClick={download} disabled={!online || loading} className="text-blue-600 disabled:opacity-40">
                  {loading ? "Yangilanmoqda..." : "Yangilash"}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {mode !== "menu" && !done && cur && (
        <div className="student-panel bg-white rounded-2xl border border-slate-200 p-5">
          <p className="text-xs text-slate-400 mb-2">{idx + 1} / {qs.length}</p>
          <p className="text-lg font-semibold text-slate-900 mb-4 break-words">
            {cur.kind === "vocab" ? cur.word.word : cur.g.prompt}
          </p>
          <div className="space-y-2">
            {cur.options.map((o) => {
              const isAns = o === cur.answer;
              const isPick = o === picked;
              const tone = picked === null
                ? "border-slate-200 hover:bg-slate-50"
                : isAns
                  ? "border-emerald-400 bg-emerald-50"
                  : isPick
                    ? "border-red-300 bg-red-50"
                    : "border-slate-200 opacity-60";
              return (
                <button
                  key={o}
                  onClick={() => choose(o)}
                  className={`w-full text-left border rounded-xl px-4 py-3 text-sm ${tone}`}
                >
                  {o}
                </button>
              );
            })}
          </div>
          {picked !== null && (
            <div className="mt-4">
              <p className={`flex items-center gap-1.5 text-sm font-medium ${
                picked === cur.answer ? "text-emerald-700" : "text-red-600"}`}>
                {picked === cur.answer ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                {picked === cur.answer ? "To'g'ri!" : `To'g'risi: ${cur.answer}`}
              </p>
              {cur.kind === "grammar" && cur.g.explain && (
                <p className="text-xs text-slate-500 mt-1">{cur.g.explain}</p>
              )}
              <button onClick={next} className="mt-3 w-full bg-blue-600 text-white rounded-xl py-2.5 text-sm font-medium">
                Davom etish
              </button>
            </div>
          )}
        </div>
      )}

      {done && (
        <div className="student-panel bg-white rounded-2xl border border-slate-200 p-6 text-center">
          <p className="text-3xl font-bold text-slate-900">{score} / {qs.length}</p>
          <p className="text-sm text-slate-500 mt-1 mb-5">
            {online ? "Ballar hisobingizga yozildi." : "Internet qaytganda ballar hisobingizga qo'shiladi."}
          </p>
          <div className="flex gap-2">
            <button onClick={() => setMode("menu")} className="flex-1 border border-slate-200 rounded-xl py-2.5 text-sm">
              Menyu
            </button>
            <button onClick={() => start(mode as "vocab" | "grammar")} className="flex-1 bg-blue-600 text-white rounded-xl py-2.5 text-sm font-medium">
              Yana
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
