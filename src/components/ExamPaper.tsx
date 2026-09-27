import type { ReactNode } from "react";

/**
 * SAVOLLAR VARAG'I — umumiy chizuvchi (2026-09-27).
 *
 * Ilgari faqat ExamTake.tsx ichida edi (o'quvchi /t/<token> va ilovada
 * topshiradigan test). Endi xodimlar ham mockni o'zi yechib ko'radi
 * (Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib
 * ishlaydigan bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq
 * ustozlarga ular ham experience qilib xatolarni aytadida") — ular
 * o'quvchi ko'radigan AYNAN o'sha savollarni ko'rishi kerak. Shuning
 * uchun chizuvchi o'zgarishsiz shu yerga ko'chirildi; ExamTake'ning
 * saqlash / chiqish / ro'yxat mantiqi joyida qoldi.
 *
 * Ixtiyoriy qo'shimchalar (faqat xodim sahifasida ishlatiladi):
 *   renderQuestionAction — savol matni yonida (masalan "xato bor" bayrog'i);
 *   renderPartExtra      — bo'lim sarlavhasi ostida (masalan "Tinglash").
 * Ular berilmasa, chiqadigan HTML avvalgisi bilan bir xil.
 */

export type PaperQ = {
  id: string;
  n: number;
  type: "choice" | "text" | "multi" | "essay";
  q: string;
  options?: string[];
  image?: string | null;
  /** multi — nechta variant belgilanishi kerak ("Choose TWO letters") */
  pick?: number | null;
  /** essay — eng kam so'z (IELTS Writing: 150 / 250) */
  min_words?: number | null;
};
export type PaperPart = {
  title: string;
  instructions?: string;
  passage?: string;
  audio_url?: string | null;
  image?: string | null;
  questions: PaperQ[];
};
export type PaperValue = string | number | number[];
export type PaperAnswers = Record<string, PaperValue>;

const LETTERS = "ABCDEFGH";

/** SUV BELGISI (2026-09-23, Jahongir: "ismiga suv belgi qo'shchi").
 *  Savollar ustida o'quvchining ismi xira takrorlanib turadi —
 *  skrinshot tarqalsa, kimdan chiqqani ko'rinib turadi. Bosishga
 *  xalaqit bermaydi (pointer-events yo'q).
 *  2026-09-27: ExamTake.tsx dan shu yerga ko'chdi — xodim mock
 *  sahifasida ham o'z ismi bilan turadi. */
export function Watermark({ text }: { text: string }) {
  const rows = Array.from({ length: 16 });
  return (
    <div
      aria-hidden
      className="fixed inset-0 z-30 overflow-hidden pointer-events-none select-none"
    >
      <div className="absolute -inset-1/4 rotate-[-24deg]">
        {rows.map((_, i) => (
          <div
            key={i}
            className="whitespace-nowrap text-slate-900/[0.09] text-[15px] font-semibold tracking-wide py-6"
          >
            {Array.from({ length: 8 })
              .map(() => text)
              .join("     •     ")}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ExamPaper({
  parts,
  answers,
  onChange,
  readOnly = false,
  renderQuestionAction,
  renderPartExtra,
}: {
  parts: PaperPart[];
  answers: PaperAnswers;
  onChange: (qid: string, v: PaperValue) => void;
  readOnly?: boolean;
  renderQuestionAction?: (q: PaperQ) => ReactNode;
  renderPartExtra?: (p: PaperPart, pi: number) => ReactNode;
}) {
  const card = "bg-white rounded-2xl shadow-xl p-5";
  const off = readOnly || undefined;
  return (
    <>
      {parts.map((p, pi) => (
        <div key={pi} className={card}>
          <h2 className="font-bold text-slate-900">{p.title}</h2>
          {p.instructions && (
            <p className="text-sm text-slate-600 mt-1 whitespace-pre-line">{p.instructions}</p>
          )}
          {p.audio_url && <audio controls src={p.audio_url} className="w-full mt-3" />}
          {renderPartExtra ? renderPartExtra(p, pi) : null}
          {p.image && (
            <img src={p.image} alt="" className="mt-3 w-full max-w-xl rounded-lg border border-slate-200" />
          )}
          {p.passage && (
            <div className="mt-3 bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm text-slate-800 whitespace-pre-line leading-relaxed">
              {p.passage}
            </div>
          )}
          <div className="mt-4 space-y-5">
            {p.questions.map((q) => {
              const text = (
                <p className="text-sm text-slate-800 mb-2 whitespace-pre-line">
                  <span className="font-semibold text-slate-500 mr-1.5">{q.n}.</span>
                  {q.q}
                </p>
              );
              const action = renderQuestionAction ? renderQuestionAction(q) : null;
              return (
                <div key={q.id}>
                  {q.image && (
                    <img
                      src={q.image}
                      alt=""
                      className="max-h-40 max-w-full rounded-lg border border-slate-200 mb-2"
                    />
                  )}
                  {action ? (
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">{text}</div>
                      <div className="shrink-0">{action}</div>
                    </div>
                  ) : (
                    text
                  )}
                  {q.type === "essay" ? (
                    // IELTS Writing — kompyuterda yoziladi, examiner o'qib
                    // baholaydi. So'z sanagichi CD IELTS'dagidek pastda turadi.
                    (() => {
                      const txt = String(answers[q.id] ?? "");
                      const words = txt.trim() ? txt.trim().split(/\s+/).length : 0;
                      const need = q.min_words || 0;
                      return (
                        <div>
                          <textarea
                            className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm leading-relaxed min-h-[16rem]"
                            value={txt}
                            spellCheck={false}
                            readOnly={off}
                            placeholder="Javobingizni shu yerga yozing"
                            onChange={(e) => onChange(q.id, e.target.value)}
                          />
                          <div className="mt-1 flex items-center justify-between text-xs">
                            <span
                              className={
                                need && words < need
                                  ? "text-amber-600 font-medium"
                                  : "text-slate-500"
                              }
                            >
                              {words} so'z{need ? ` · kamida ${need}` : ""}
                            </span>
                            {need && words < need ? (
                              <span className="text-amber-600">
                                Yana {need - words} so'z kerak
                              </span>
                            ) : null}
                          </div>
                        </div>
                      );
                    })()
                  ) : q.type === "multi" ? (
                    // "Choose TWO letters, A-E" — bir nechta variant belgilanadi.
                    // Kerakligidan ortiq belgilansa eng eskisi o'chadi.
                    (() => {
                      const cur: number[] = Array.isArray(answers[q.id])
                        ? (answers[q.id] as number[])
                        : [];
                      const need = q.pick || 2;
                      const toggle = (oi: number) => {
                        const has = cur.includes(oi);
                        let next = has ? cur.filter((x) => x !== oi) : [...cur, oi];
                        if (next.length > need) next = next.slice(next.length - need);
                        onChange(q.id, next);
                      };
                      return (
                        <div>
                          <p className="text-xs text-slate-500 mb-1.5">
                            {need} ta variant belgilang ({cur.length}/{need})
                          </p>
                          <div className="grid gap-1.5">
                            {(q.options || []).map((o, oi) => (
                              <button
                                key={oi}
                                disabled={off}
                                onClick={() => toggle(oi)}
                                className={`text-left rounded-xl border px-3 py-2.5 text-sm transition ${
                                  cur.includes(oi)
                                    ? "border-brand-500 bg-brand-50 text-brand-800 font-medium"
                                    : "border-slate-200 text-slate-700 hover:border-slate-300"
                                }`}
                              >
                                <span className="font-semibold mr-2">{LETTERS[oi]}</span>
                                {o !== LETTERS[oi] && o}
                              </button>
                            ))}
                          </div>
                        </div>
                      );
                    })()
                  ) : q.type === "choice" ? (
                    // Faqat harfli variantlar (rasmdan tanlash) — bir qatorda
                    <div
                      className={
                        (q.options || []).every((o, i) => o === LETTERS[i])
                          ? "flex flex-wrap gap-1.5"
                          : "grid gap-1.5"
                      }
                    >
                      {(q.options || []).map((o, oi) => (
                        <button
                          key={oi}
                          disabled={off}
                          onClick={() => onChange(q.id, oi)}
                          className={`text-left rounded-xl border px-3 py-2.5 text-sm transition ${
                            answers[q.id] === oi
                              ? "border-brand-500 bg-brand-50 text-brand-800 font-medium"
                              : "border-slate-200 text-slate-700 hover:border-slate-300"
                          }`}
                        >
                          <span className="font-semibold mr-2">{LETTERS[oi]}</span>
                          {o !== LETTERS[oi] && o}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <input
                      className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
                      value={String(answers[q.id] ?? "")}
                      autoCapitalize="off"
                      autoCorrect="off"
                      spellCheck={false}
                      readOnly={off}
                      placeholder="Javobni yozing"
                      onChange={(e) => onChange(q.id, e.target.value)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </>
  );
}
