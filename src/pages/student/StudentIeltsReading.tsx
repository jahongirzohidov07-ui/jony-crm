import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BookOpen, Check, ChevronDown, X } from "lucide-react";
import { api } from "../../lib/api";
import { autoNextDelay, useAutoNext } from "../../lib/useAutoNext";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * IELTS READING — TFNG / YNNG MASHQI (2026-08-25).
 *
 * Jahongir: "shuni true false ichiga tiplar bilan boshida orgatib
 * o'rganishga eng zor samarali qilib qoy agar kerak bolsa bundan
 * ham osonroqlarini tuzib kirish olish uchun boshlanishiga qoygin
 * chunki bu yerdagi hammasi real examdan olinganlar boshlanishiga
 * qiyinroq bolishi mumkin".
 *
 * SHUNING UCHUN EKRAN UCH BOSQICHLI:
 *   1) QOIDALAR — Tip 15..30 kartalari, misoli bilan. O'quvchi
 *      o'qimasdan mashqqa o'tolmaydi (tugma pastda turadi).
 *   2) Nechta mashq — 10 / 20 / 40.
 *   3) Mashqning o'zi: matn -> savol -> uchta tugma. Javobdan
 *      keyin QAYSI QOIDA ishlaganini aytadi (masalan "Tip 24 —
 *      mutlaq so'z"), shuning uchun xato ham dars bo'ladi.
 *
 * Serverdan elementlar OSONDAN QIYINGA keladi: 1-bosqich bir gapli
 * matn, 5-bosqich haqiqiy imtihon savoli.
 */

/* Backend reading_pick_seed.SEP bilan bir xil bo'lishi SHART —
   ikkita javob shu belgi bilan ulanadi. */
const PICK_SEP = " ||| ";

const STEP_COLOR: Record<number, string> = {
  1: "bg-emerald-50 text-emerald-700",
  2: "bg-sky-50 text-sky-700",
  3: "bg-indigo-50 text-indigo-700",
  4: "bg-amber-50 text-amber-700",
  5: "bg-rose-50 text-rose-700",
};

export default function StudentIeltsReading() {
  const { kind } = useParams();
  const [tips, setTips] = useState<Any>(null);
  const [open, setOpen] = useState<number | null>(0);
  const [phase, setPhase] = useState<"tips" | "count" | "play">("tips");
  const [cnt, setCnt] = useState<number | null>(null);
  const [d, setD] = useState<Any>(null);
  const [idx, setIdx] = useState(0);
  const [result, setResult] = useState<Any>(null);
  const [picked, setPicked] = useState("");
  // 2026-08-25: Table Completion'da javob YOZILADI (variant yo'q)
  const [typed, setTyped] = useState("");
  // 2026-08-26, Jahongir: "bitta savolga 2ta togri javobni 5ta
  // variant ichidan tanlash kerak bo'ladi" — Pick from a List
  // uchun tanlanganlar ro'yxati (q.pick = 2 bo'lganda ishlaydi).
  const [multi, setMulti] = useState<string[]>([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [score, setScore] = useState({ ok: 0, xp: 0 });
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    api
      .get<Any>(`/student/ielts/reading/tips?kind=${kind}`)
      .then(setTips)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [kind]);

  const load = useCallback(() => {
    if (cnt === null) return;
    setErr("");
    setD(null);
    setIdx(0);
    setPicked("");
    setTyped("");
    setMulti([]);
    setResult(null);
    setScore({ ok: 0, xp: 0 });
    setFinished(false);
    api
      .get<Any>(`/student/ielts/reading/round?kind=${kind}&count=${cnt}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [kind, cnt]);

  useEffect(load, [load]);

  const items: Any[] = d?.items || [];
  const q = items[idx];
  const autoNext = useAutoNext(() => next());
  // Pick from a List: nechta javob kerak (server aytadi, odatda 2)
  const need = Number(q?.pick || 1);
  // Javob bir nechta bo'lsa, to'g'ri variantlar ro'yxati
  const rightSet: string[] = result?.expected
    ? String(result.expected).split(PICK_SEP).map((x: string) => x.trim())
    : [];

  function toggleMulti(o: string) {
    if (result || busy) return;
    setMulti((m) =>
      m.includes(o)
        ? m.filter((x) => x !== o)
        : m.length >= need
          ? m
          : [...m, o],
    );
  }

  async function submit(choice: string) {
    if (!q || busy || result || !choice.trim()) return;
    setBusy(true);
    setPicked(choice);
    try {
      const r = await api.post<Any>("/student/ielts/reading/answer", {
        ref: q.ref,
        answer: choice,
      });
      setResult(r);
      if (r.correct)
        setScore((s) => ({ ok: s.ok + 1, xp: s.xp + (r.xp || 0) }));
      // Xato bo'lsa uzoqroq turadi — izohni o'qib ulgurish kerak
      autoNext.schedule(
        autoNextDelay({ correct: !!r.correct, hasAnswer: true,
                        hasExtra: true }) * (r.correct ? 1.2 : 2.2),
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
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
    setPicked("");
    setTyped("");
    setMulti([]);
    setResult(null);
  }

  const card = { background: "#111C4B", borderColor: "#223070" };

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* -------------------------------------------- sarlavha */}
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/ielts/reading"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <BookOpen size={18} />
        </Link>
        <div className="flex-1 min-w-0">
          <p className="text-[15px] font-extrabold truncate">
            {tips?.title || d?.title || "IELTS Reading"}
          </p>
          <p className="text-[11px] text-slate-400">IELTS Reading</p>
        </div>
        {phase === "play" && !finished && items.length > 0 && (
          <span className="text-[11px] font-bold text-slate-300 shrink-0">
            {idx + 1}/{items.length}
          </span>
        )}
      </div>

      {err && (
        <div className="bg-white rounded-xl border border-red-200 p-4 mt-4">
          <p className="text-sm text-red-600">{err}</p>
        </div>
      )}

      {/* ---------------------------------------- 1) QOIDALAR */}
      {phase === "tips" && tips && (
        <>
          <div className="bg-white rounded-xl border border-slate-200 p-4 mt-4">
            <p className="text-sm font-semibold text-slate-800">
              Avval qoidalarni o'qing
            </p>
            <p className="text-[11.5px] text-slate-500 mt-1 leading-relaxed">
              Bu savol turida xato ko'pincha bilimdan emas —
              QOIDANI bilmaslikdan chiqadi. Quyidagi kartalarni
              bosing, har birida misol bor.
            </p>
          </div>

          <div className="space-y-1.5 mt-3">
            {(tips.tips || []).map((t: Any, i: number) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden"
              >
                <button
                  onClick={() => setOpen(open === i ? null : i)}
                  className="w-full flex items-center gap-2.5 p-3.5 text-left"
                >
                  <span className="w-6 h-6 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center shrink-0 text-[11px] font-extrabold">
                    {i + 1}
                  </span>
                  <span className="flex-1 text-[13px] font-semibold text-slate-800">
                    {t.title}
                  </span>
                  <ChevronDown
                    size={16}
                    className={`text-slate-400 shrink-0 transition ${
                      open === i ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {open === i && (
                  <div className="px-3.5 pb-3.5 -mt-1">
                    <p className="text-[12.5px] text-slate-600 leading-relaxed">
                      {t.body}
                    </p>
                    {t.example && (
                      <pre className="mt-2 text-[11.5px] text-slate-700 bg-slate-50 border border-slate-200 rounded-lg p-2.5 whitespace-pre-wrap font-sans leading-relaxed">
                        {t.example}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {(tips.steps || []).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-4 mt-3">
              <p className="text-sm font-semibold text-slate-800 mb-2">
                Mashq bosqichlari
              </p>
              {tips.steps.map((s: Any) => (
                <div key={s.step} className="flex items-center gap-2.5 py-1">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded shrink-0 ${
                      STEP_COLOR[s.step] || "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {s.step}-bosqich
                  </span>
                  <span className="text-[12px] text-slate-700 flex-1">
                    {s.title}
                  </span>
                  <span className="text-[11px] text-slate-400 shrink-0">
                    {s.total} ta
                  </span>
                </div>
              ))}
              <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                Oxirgi bosqich — haqiqiy imtihondan olingan savollar.
                Ulargacha oson mashqlarda qo'lni qotirasiz.
              </p>
            </div>
          )}

          <button
            onClick={() => setPhase("count")}
            className="w-full mt-4 rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white active:scale-[0.99]"
          >
            Tushundim, mashqni boshlaymiz
          </button>
        </>
      )}

      {/* ------------------------------------- 2) nechta mashq */}
      {phase === "count" && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mt-4">
          <p className="text-sm font-semibold text-slate-800 mb-1">
            Nechta savol ishlaymiz?
          </p>
          <p className="text-[11px] text-slate-400 mb-3">
            Savollar osondan qiyinga qarab keladi.
          </p>
          <div className="space-y-1.5">
            {[
              [10, "10 ta", "Qisqa mashq — 5-6 daqiqa"],
              [20, "20 ta", "O'rtacha — 12-15 daqiqa"],
              [40, "40 ta", "To'liq blok — imtihon hajmi"],
            ].map(([n, lbl, hint]) => (
              <button
                key={String(n)}
                onClick={() => {
                  setCnt(n as number);
                  setPhase("play");
                }}
                className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 text-left active:scale-[0.99]"
              >
                <div className="w-11 h-9 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center shrink-0 text-sm font-extrabold">
                  {n}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800">{lbl}</p>
                  <p className="text-[11px] text-slate-400">{hint}</p>
                </div>
              </button>
            ))}
          </div>
          <button
            onClick={() => setPhase("tips")}
            className="w-full mt-3 text-[12px] text-slate-500 py-2"
          >
            ← Qoidalarga qaytish
          </button>
        </div>
      )}

      {/* ----------------------------------------- 3) MASHQ */}
      {phase === "play" && !finished && q && (
        <>
          <div className="bg-white rounded-xl border border-slate-200 p-4 mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-slate-500">
                {q.title || "Passage"}
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  STEP_COLOR[q.step] || "bg-slate-100 text-slate-600"
                }`}
              >
                {q.step}-bosqich · {q.step_title}
              </span>
            </div>
            {q.paragraphs ? (
              /* Matching Headings: so'ralayotgan xatboshi ajratiladi */
              <div className="space-y-2">
                {q.paragraphs.map((pp: Any) => (
                  <p key={pp.letter}
                     className={`text-[13px] leading-relaxed rounded px-2 py-1.5 ${
                       pp.letter === q.para
                         ? "bg-amber-50 border border-amber-300 text-slate-900"
                         : "text-slate-600"}`}>
                    <b className="mr-1">{pp.letter}.</b>{pp.text}
                  </p>
                ))}
              </div>
            ) : (
              <p className="text-[13.5px] text-slate-800 leading-relaxed whitespace-pre-line">
                {q.passage}
              </p>
            )}
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4 mt-3">
            <p className="text-[11px] font-semibold text-slate-500 mb-1.5">
              {q.instruction || "Question"}
            </p>
            {!q.questions && (
              <p className="text-[14px] font-medium text-slate-900 leading-relaxed">
                {q.prompt}
              </p>
            )}

            {/* --- Diagram labelling: chizma yorliqlari (2026-08-25) --- */}
            {!q.options && q.labels && (
              <div className="mt-3 rounded-xl border-2 border-dashed border-slate-300 p-3">
                <p className="text-[12px] font-bold text-slate-500 text-center mb-2 uppercase tracking-wide">
                  {q.figure}
                </p>
                <div className="space-y-1.5">
                  {q.labels.map((ln: string, i: number) => {
                    const active = ln.includes("______");
                    return (
                      <p key={i}
                         className={`text-[12.5px] leading-snug rounded px-2 py-1.5 border ${
                           active
                             ? "text-slate-900 font-medium bg-amber-50 border-amber-300"
                             : "text-slate-500 border-slate-200"}`}>
                        {ln}
                      </p>
                    );
                  })}
                </div>
              </div>
            )}

            {/* --- Short answer: savollar ro'yxati (2026-08-25) --- */}
            {!q.options && q.questions && (
              <div className="mt-3 space-y-1">
                {q.questions.map((qq: string, i: number) => {
                  const active = i + 1 === q.q_no;
                  return (
                    <p key={i}
                       className={`text-[12.5px] leading-snug rounded px-1.5 py-1 ${
                         active
                           ? "text-slate-900 font-semibold bg-amber-50"
                           : "text-slate-400"}`}>
                      {i + 1}. {qq}
                    </p>
                  );
                })}
              </div>
            )}

            {/* --- Flow-chart: qutilar va strelkalar (2026-08-25) --- */}
            {!q.options && q.flow && (
              <div className="mt-3">
                {q.flow_title && (
                  <p className="text-[13px] font-bold text-slate-900 mb-2">
                    {q.flow_title}
                  </p>
                )}
                <div className="flex flex-col items-stretch">
                  {q.flow.map((bx: string, i: number) => {
                    const active = bx.includes("______");
                    return (
                      <div key={i}>
                        <div className={`rounded-lg border px-2.5 py-2 text-[12.5px] leading-snug text-center ${
                          active
                            ? "border-amber-400 bg-amber-50 text-slate-900 font-medium"
                            : "border-slate-300 bg-white text-slate-700"}`}>
                          {bx}
                        </div>
                        {i < q.flow.length - 1 && (
                          <p className="text-center text-slate-400 text-[13px] leading-none py-0.5">
                            ↓
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* --- Summary Completion: xulosa qutisi (2026-08-25) --- */}
            {!q.options && q.summary && (
              <div className="mt-3 rounded-xl border-2 border-slate-300 p-3">
                {q.summary_title && (
                  <p className="text-[13px] font-bold text-slate-900 mb-2">
                    {q.summary_title}
                  </p>
                )}
                <div className="space-y-1.5">
                  {q.summary.map((ln: string, i: number) => {
                    const bullet = ln.trim().startsWith("•");
                    const active = ln.includes("______");
                    return (
                      <p key={i}
                         className={`text-[12.5px] leading-relaxed ${
                           bullet ? "pl-3" : ""} ${
                           active
                             ? "text-slate-900 font-medium bg-amber-50 rounded px-1.5 py-1"
                             : "text-slate-600"}`}>
                        {ln}
                      </p>
                    );
                  })}
                </div>
              </div>
            )}

            {/* --- Table Completion: jadval + yozma javob --- */}
            {!q.options && q.headers && (
              <div className="mt-3 -mx-4 px-4 overflow-x-auto">
                <table className="w-full text-[11.5px] border-collapse">
                  <thead>
                    <tr>
                      {q.headers.map((h: string) => (
                        <th key={h}
                            className="border border-slate-200 bg-slate-50 px-2 py-1.5 text-left font-semibold text-slate-600">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(q.rows || []).map((r: string[], ri: number) => (
                      <tr key={ri}>
                        {r.map((cvalue: string, ci: number) => (
                          <td key={ci}
                              className={`border border-slate-200 px-2 py-1.5 align-top ${
                                cvalue.includes("______")
                                  ? "bg-amber-50 text-slate-900 font-medium"
                                  : "text-slate-700"}`}>
                            {cvalue}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {!q.options && (
              <div className="mt-3.5">
                <input
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") submit(typed);
                  }}
                  disabled={!!result || busy}
                  autoComplete="off"
                  autoCapitalize="off"
                  spellCheck={false}
                  placeholder={q.flow || q.questions || q.labels ? "Matndan 1-2 so'z yozing" : "Matndan bitta so'z yozing"}
                  className={`w-full rounded-xl border px-3 py-3 text-[15px] ${
                    result
                      ? result.correct
                        ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                        : "border-red-300 bg-red-50 text-red-700"
                      : "border-slate-200"}`}
                />
                {!result && (
                  <button
                    onClick={() => submit(typed)}
                    disabled={busy || !typed.trim()}
                    className="w-full mt-2 rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
                  >
                    Tekshirish
                  </button>
                )}
              </div>
            )}

            {/* 2026-08-26: Pick from a List — ikkita javob tanlanadi.
                Ikkitasi to'planmaguncha "Tekshirish" faol emas, chunki
                IELTS'da bittasini topish ball bermaydi. */}
            {need > 1 && !result && (
              <p className="mt-3.5 text-[11.5px] font-bold text-slate-500">
                {q.instruction || "Choose TWO letters, A-E."} —{" "}
                <span className={multi.length === need ? "text-emerald-600" : "text-amber-600"}>
                  {multi.length}/{need} tanlandi
                </span>
              </p>
            )}

            <div className="space-y-1.5 mt-3.5">
              {(q.options || []).map((o: string) => {
                const isPicked =
                  need > 1 ? multi.includes(o) : picked === o;
                const isRight = result && rightSet.includes(o);
                let cls =
                  "border-slate-200 bg-white text-slate-800";
                if (result) {
                  if (isRight)
                    cls = "border-emerald-300 bg-emerald-50 text-emerald-800";
                  else if (isPicked)
                    cls = "border-red-300 bg-red-50 text-red-700";
                  else cls = "border-slate-200 bg-white text-slate-400";
                } else if (isPicked) {
                  cls = "border-brand-500 bg-brand-50 text-brand-800";
                }
                return (
                  <button
                    key={o}
                    disabled={!!result || busy}
                    onClick={() => {
                      if (need > 1) return toggleMulti(o);
                      submit(o);
                    }}
                    className={`w-full flex items-start gap-2.5 border rounded-xl p-3 text-left text-[13px] font-semibold leading-snug active:scale-[0.99] ${cls}`}
                  >
                    {need > 1 && (
                      <span
                        className={`mt-0.5 w-4 h-4 rounded border-2 shrink-0 flex items-center justify-center ${
                          isPicked
                            ? "border-brand-500 bg-brand-500"
                            : "border-slate-300"
                        }`}
                      >
                        {isPicked && <Check size={11} className="text-white" />}
                      </span>
                    )}
                    <span className="flex-1">{o}</span>
                    {result && isRight && (
                      <Check size={16} className="text-emerald-600 shrink-0" />
                    )}
                    {result && isPicked && !isRight && (
                      <X size={16} className="text-red-500 shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>

            {need > 1 && !result && (
              <button
                onClick={() => submit(multi.join(PICK_SEP))}
                disabled={busy || multi.length !== need}
                className="w-full mt-2.5 rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
              >
                Tekshirish
              </button>
            )}
          </div>

          {result && (
            <div
              className={`rounded-xl border p-4 mt-3 ${
                result.correct
                  ? "border-emerald-200 bg-emerald-50"
                  : "border-amber-200 bg-amber-50"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-bold ${
                    result.correct ? "text-emerald-700" : "text-amber-800"
                  }`}
                >
                  {result.correct
                    ? "To'g'ri!"
                    : `To'g'risi: ${String(result.expected).split(PICK_SEP).join("  +  ")}`}
                </span>
                {result.tip && (
                  <span className="text-[10px] font-bold text-slate-600 bg-white border border-slate-200 rounded px-1.5 py-0.5">
                    {result.tip}
                  </span>
                )}
              </div>
              {/* 2026-08-25, Jahongir: "javoblar tushuntirilganda
                  readingda doim paraphraselarni korsatib tushuntirish
                  kerak" — paraffraz alohida, ko'zga tashlanadigan
                  blokda turadi. */}
              {result.paraphrase && (
                <div className="mt-2 rounded-lg bg-white border border-slate-200 p-2.5">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                    Paraffraz
                  </p>
                  <p className="text-[12.5px] text-slate-800 mt-1">
                    Jadvalda:{" "}
                    <b className="text-brand-700">
                      {result.paraphrase.table}
                    </b>
                  </p>
                  <p className="text-[12.5px] text-slate-800">
                    Matnda:{" "}
                    <b className="text-emerald-700">
                      {result.paraphrase.passage}
                    </b>
                  </p>
                </div>
              )}
              <p className="text-[12.5px] text-slate-700 mt-1.5 leading-relaxed">
                {result.explain}
              </p>
              <button
                onClick={next}
                className="w-full mt-3 rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white"
              >
                Keyingisi
              </button>
            </div>
          )}
        </>
      )}

      {/* -------------------------------------------- yakun */}
      {phase === "play" && finished && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mt-4 text-center">
          <p className="text-sm font-semibold text-slate-800">
            Mashq tugadi
          </p>
          <p className="text-3xl font-extrabold text-slate-900 mt-2">
            {score.ok}/{items.length}
          </p>
          {score.xp > 0 && (
            <p className="text-[12px] text-emerald-600 font-semibold mt-1">
              +{score.xp} XP
            </p>
          )}
          <p className="text-[11.5px] text-slate-500 mt-2 leading-relaxed">
            Xato qilgan savollaringiz keyingi mashqda yana chiqadi —
            to'g'ri qilmagunicha yo'qolmaydi.
          </p>
          <div className="space-y-1.5 mt-4">
            <button
              onClick={load}
              className="w-full rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white"
            >
              Yana bir bo'lim
            </button>
            <button
              onClick={() => setPhase("tips")}
              className="w-full rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-600"
            >
              Qoidalarni takrorlash
            </button>
            <Link
              to="/student/ielts/reading"
              className="block w-full rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-600"
            >
              Bo'limga qaytish
            </Link>
          </div>
        </div>
      )}

      {phase === "play" && !finished && !q && !err && (
        <p className="text-sm text-slate-500 text-center py-10">
          Yuklanmoqda…
        </p>
      )}
    </div>
  );
}
