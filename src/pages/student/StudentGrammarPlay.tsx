import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, RotateCcw, Sparkles, X } from "lucide-react";
import { api } from "../../lib/api";
import { autoNextDelay, useAutoNext } from "../../lib/useAutoNext";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — GRAMMAR MASHG'ULOTI (2026-08-10).
 *
 * Uch tur bitta ekranda:
 *   fill  — variant tugmalari;
 *   error — gap ko'rsatiladi, XATO bo'lakni bosish kerak;
 *   order — so'z kartochkalarini bosib jumla yig'ish.
 *
 * To'g'riligini SERVER hal qiladi (/grammar/answer) — to'g'ri javob
 * mijozga oldindan kelmaydi. Har savoldan keyin izoh ko'rsatiladi —
 * bola nafaqat "xato", balki NEGA xatoligini ham ko'radi.
 */
export default function StudentGrammarPlay() {
  const { topic } = useParams();
  const [items, setItems] = useState<Any[]>([]);
  const [idx, setIdx] = useState(0);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  // Joriy savol holati
  const [picked, setPicked] = useState<string[]>([]); // order uchun
  // MASHQ TURI (2026-08-11, Jahongir): mavzu tanlangach 4 tur
  // taklif qilinadi. null = hali tanlanmagan (tanlash ekrani).
  const [kind, setKind] = useState<string | null>(null);
  const [kinds, setKinds] = useState<string[]>([]);
  const [clozeSel, setClozeSel] = useState<Record<number, string>>({});
  const [result, setResult] = useState<Any>(null); // serverdan javob
  const [score, setScore] = useState({ ok: 0, xp: 0 });
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    // Bu mavzuda qaysi turlar borligini bilib olamiz
    api
      .get<Any>("/student/grammar/topics")
      .then((r) => {
        const all = [
          ...(r?.a1?.topics || []),
          ...(r?.a2?.topics || []),
        ];
        const t = all.find((x: Any) => x.topic === topic);
        setKinds(t?.kinds || ["fill", "error", "order"]);
      })
      .catch(() => setKinds(["fill", "error", "order"]));
  }, [topic]);

  const load = useCallback(() => {
    setErr("");
    setItems([]);
    setIdx(0);
    setResult(null);
    setPicked([]);
    setScore({ ok: 0, xp: 0 });
    setFinished(false);
    if (kind === null) return;
    api
      .get<Any>(
        `/student/grammar/round?topic=${encodeURIComponent(topic || "")}${
          kind && kind !== "mix" ? `&kind=${kind}` : ""
        }`,
      )
      .then((r) => setItems(r.items || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [topic, kind]);

  useEffect(load, [load]);

  const q = items[idx];

  // Javobdan keyin o'zi keyingi savolga o'tadi (2026-08-18).
  const autoNext = useAutoNext(() => next());

  async function submit(answer: string) {
    if (!q || busy || result) return;
    setBusy(true);
    try {
      const r = await api.post<Any>("/student/grammar/answer", {
        question_id: q.id,
        answer,
      });
      setResult(r);
      if (r.correct)
        setScore((s) => ({ ok: s.ok + 1, xp: s.xp + (r.xp || 0) }));
      autoNext.schedule(
        autoNextDelay({
          correct: !!r.correct,
          hasAnswer: !!r.expected,
          hasExtra: !!r.explain,
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
    if (idx + 1 >= items.length) {
      setFinished(true);
      return;
    }
    setIdx(idx + 1);
    setResult(null);
    setPicked([]);
    setClozeSel({});
  }

  const remainingWords =
    q?.kind === "order"
      ? (() => {
          const left = [...(q.options || [])];
          for (const w of picked) {
            const i = left.indexOf(w);
            if (i >= 0) left.splice(i, 1);
          }
          return left;
        })()
      : [];

  return (
    <>
      <div className="bg-gradient-to-br from-violet-700 to-violet-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/grammar"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Mavzular
          </Link>
          <h1 className="text-lg font-semibold truncate">{topic}</h1>
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
            <button onClick={load} className="mt-2 text-sm font-medium text-violet-600">
              Qayta urinish
            </button>
          </div>
        )}

        {/* ---- YAKUN ---- */}
        {finished && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
            <Sparkles size={36} className="mx-auto text-violet-500 mb-2" />
            <p className="text-2xl font-bold text-slate-900">
              {score.ok}/{items.length}
            </p>
            <p className="text-sm text-slate-500 mt-1">
              to'g'ri javob
              {score.xp > 0 && ` · +${score.xp} XP`}
            </p>
            <div className="flex gap-2 mt-5">
              <button
                onClick={load}
                className="flex-1 py-3 rounded-xl bg-violet-600 text-white text-sm font-semibold flex items-center justify-center gap-2"
              >
                <RotateCcw size={15} />
                Yana mashq
              </button>
              <Link
                to="/student/grammar"
                className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold flex items-center justify-center"
              >
                Mavzular
              </Link>
            </div>
          </div>
        )}

        {/* ---- MASHQ TURINI TANLASH ---- */}
        {kind === null && !err && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Qaysi turdagi mashqni xohlaysiz?
            </p>
            <div className="space-y-1.5">
              {[
                ["mix", "Aralash", "Har xil turdagi mashqlar"],
                ["fill", "Bo'sh joyni to'ldirish", "4 variantdan tanlang"],
                ["order", "Gaplarni tartiblash", "So'zlardan jumla tuzing"],
                ["error", "Xatoni topish", "Gapdagi xato so'zni belgilang"],
                ["cloze", "Kichik matnli test", "Dialog ichida bir nechta bo'sh joy"],
              ]
                .filter(
                  ([k]) => k === "mix" || kinds.includes(k as string),
                )
                .map(([k, lbl, hint]) => (
                  <button
                    key={k}
                    onClick={() => setKind(k as string)}
                    className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                  >
                    <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center shrink-0 text-sm font-bold">
                      {(lbl as string).charAt(0)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-800">
                        {lbl}
                      </p>
                      <p className="text-[11px] text-slate-400">{hint}</p>
                    </div>
                  </button>
                ))}
            </div>
          </div>
        )}

        {/* ---- SAVOL ---- */}
        {!finished && q && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-[11px] font-semibold text-violet-500 uppercase tracking-wide mb-2">
              {q.kind === "fill"
                ? "Bo'sh joyni to'ldiring"
                : q.kind === "error"
                  ? "Xato so'zni toping"
                  : q.kind === "cloze"
                    ? "Matnni to'ldiring"
                    : "So'zlardan jumla tuzing"}
            </p>
            <p className="text-base font-medium text-slate-900 leading-relaxed mb-4 whitespace-pre-line">
              {q.prompt}
            </p>

            {/* CLOZE: har raqamli bo'sh joy uchun variantlar */}
            {q.kind === "cloze" && (
              <div className="space-y-3 mb-1">
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
                            setClozeSel((c) => ({ ...c, [bi]: o }))
                          }
                          className={`px-3 py-2 rounded-lg border text-sm font-medium transition disabled:opacity-60 ${
                            clozeSel[bi] === o
                              ? "bg-violet-600 text-white border-transparent"
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
                    disabled={
                      busy ||
                      Object.keys(clozeSel).length <
                        (q.options || []).length
                    }
                    onClick={() =>
                      submit(
                        (q.options || [])
                          .map((_: Any, bi: number) => clozeSel[bi] || "")
                          .join("|"),
                      )
                    }
                    className="w-full py-3 rounded-xl bg-violet-600 text-white text-sm font-semibold disabled:opacity-40"
                  >
                    Tekshirish
                  </button>
                )}
              </div>
            )}

            {/* order: yig'ilgan jumla */}
            {q.kind === "order" && (
              <div className="min-h-[52px] border-2 border-dashed border-slate-200 rounded-xl p-2 mb-3 flex flex-wrap gap-1.5">
                {picked.map((w, i) => (
                  <button
                    key={`${w}-${i}`}
                    disabled={!!result}
                    onClick={() =>
                      setPicked((p) => p.filter((_, j) => j !== i))
                    }
                    className="px-2.5 py-1.5 rounded-lg bg-violet-600 text-white text-sm font-medium disabled:opacity-70"
                  >
                    {w}
                  </button>
                ))}
                {picked.length === 0 && (
                  <span className="text-sm text-slate-300 self-center px-1">
                    So'zlarni bosing...
                  </span>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-1.5">
              {q.kind === "cloze" ? null : q.kind === "order"
                ? remainingWords.map((w: string, i: number) => (
                    <button
                      key={`${w}-${i}`}
                      disabled={!!result}
                      onClick={() => setPicked((p) => [...p, w])}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 active:scale-95 transition disabled:opacity-40"
                    >
                      {w}
                    </button>
                  ))
                : (q.options || []).map((o: string) => {
                    const isAns = result && o === result.expected;
                    const isMine = result && o === result._mine;
                    return (
                      <button
                        key={o}
                        disabled={!!result || busy}
                        onClick={() => {
                          q._mine = o;
                          submit(o).then(() =>
                            setResult((r: Any) =>
                              r ? { ...r, _mine: o } : r,
                            ),
                          );
                        }}
                        className={`w-full py-2.5 px-3 rounded-lg border text-sm font-medium text-left transition ${
                          isAns
                            ? "bg-emerald-600 text-white border-transparent"
                            : isMine
                              ? "bg-red-600 text-white border-transparent"
                              : "bg-white text-slate-700 border-slate-200 disabled:opacity-60"
                        }`}
                      >
                        {o}
                      </button>
                    );
                  })}
            </div>

            {q.kind === "order" && !result && (
              <button
                disabled={picked.length === 0 || busy}
                onClick={() => submit(picked.join(" "))}
                className="w-full mt-3 py-3 rounded-xl bg-violet-600 text-white text-sm font-semibold disabled:opacity-40"
              >
                Tekshirish
              </button>
            )}

            {/* ---- Natija + izoh ---- */}
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
                {!result.correct && (
                  <p className="text-sm text-slate-700 mt-1">
                    To'g'ri javob: <b>{result.expected}</b>
                  </p>
                )}
                {result.explain && (
                  <p className="text-xs text-slate-500 mt-1">
                    {result.explain}
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
