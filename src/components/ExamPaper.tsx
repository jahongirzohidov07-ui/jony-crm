import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Runs } from "./ExamText";
import { questionRuns } from "../lib/examFormat";

/**
 * SAVOLLAR VARAG'I — umumiy chizuvchi (2026-09-27).
 *
 * Ilgari faqat ExamTake.tsx ichida edi (o'quvchi /t/<token> va ilovada
 * topshiradigan test). Endi xodimlar ham mockni o'zi yechib ko'radi
 * (Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib
 * ishlaydigan bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq
 * ustozlarga ular ham experience qilib xatolarni aytadida") — ular
 * o'quvchi ko'radigan AYNAN o'sha savollarni ko'rishi kerak.
 *
 * 2026-09-27 (kechqurun): kompyuterdagi IELTS ko'rinishi CdExam.tsx da
 * (bo'limma-bo'lim, pastda savol raqamlari, readingda chapda matn /
 * o'ngda savollar). Bu fayl endi uning bo'laklarini beradi:
 *   QuestionInput — bitta savolning javob maydoni (javob qiymatlari
 *                   avvalgidek: choice -> indeks, multi -> indekslar,
 *                   text/essay -> matn);
 *   Figure        — katta rasm (xarita/reja), bosilsa to'liq ekran;
 *   isAnswered    — savolga javob berilganmi.
 * ExamPaper (hammasi bitta ro'yxatda) eskicha ishlatish uchun qoldi.
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

/** Savolga javob berilganmi (pastki raqamlar paneli uchun). */
export function isAnswered(v: PaperValue | null | undefined): boolean {
  if (v === null || v === undefined) return false;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "number") return true;
  return v.trim() !== "";
}

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

/**
 * KATTA RASM (2026-09-27, Jahongir: "listeningda map debsan qani map").
 * Xarita / reja savol ustida ustun kengligida (eng ko'pi ~720px, nisbati
 * saqlanadi) turadi; bosilsa to'liq ekranda ochiladi. To'liq ekran
 * document.body ga chiziladi — shrift kattalashtirish (zoom) va
 * imtihon qatlami unga ta'sir qilmaydi.
 */
export function Figure({ src, className = "" }: { src: string; className?: string }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="Kattalashtirish"
        className={`relative block w-full max-w-[720px] rounded-lg border border-slate-200 bg-white overflow-hidden cursor-zoom-in focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${className}`}
      >
        <img src={src} alt="" className="block w-full h-auto" />
        {/* Rasm USTIDA emas, ostida: xarita burchagidagi harf (masalan
            H) yopilib qolmasin — 2026-09-27 brauzerdagi tekshiruv. */}
        <span className="block border-t border-slate-100 bg-slate-50 text-right text-[11px] text-slate-500 px-2 py-1">
          ⤢ Kattalashtirish
        </span>
      </button>
      {open
        ? createPortal(
            <div
              data-jony-ui=""
              role="dialog"
              aria-modal="true"
              aria-label="Rasm"
              className="fixed inset-0 z-[88] bg-slate-900/85 flex items-center justify-center p-3"
              onClick={() => setOpen(false)}
            >
              <img
                src={src}
                alt=""
                className="w-[95vw] max-w-[1400px] h-auto max-h-[88vh] object-contain bg-white rounded-lg"
              />
              <button
                type="button"
                autoFocus
                onClick={() => setOpen(false)}
                className="absolute top-3 right-3 rounded-lg bg-white/90 text-slate-800 px-3 py-1.5 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              >
                ✕ Yopish
              </button>
            </div>,
            document.body
          )
        : null}
    </>
  );
}

/**
 * Bitta savolning javob maydoni. Qiymatlar avvalgidek:
 * choice -> variant indeksi, multi -> indekslar ro'yxati, text/essay -> matn.
 * tall — Writing (o'ng ustunda) javob maydoni balandroq.
 */
export function QuestionInput({
  q,
  value,
  onChange,
  readOnly = false,
  tall = false,
}: {
  q: PaperQ;
  value: PaperValue | undefined;
  onChange: (v: PaperValue) => void;
  readOnly?: boolean;
  tall?: boolean;
}) {
  const off = readOnly || undefined;
  if (q.type === "essay") {
    // IELTS Writing — kompyuterda yoziladi, examiner o'qib
    // baholaydi. So'z sanagichi CD IELTS'dagidek pastda chapda turadi.
    const txt = String(value ?? "");
    const words = txt.trim() ? txt.trim().split(/\s+/).length : 0;
    const need = q.min_words || 0;
    return (
      <div>
        <textarea
          data-answer
          className={`w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm leading-relaxed min-h-[16rem] ${
            tall ? "lg:min-h-[calc(100dvh-17rem)]" : ""
          }`}
          value={txt}
          spellCheck={false}
          readOnly={off}
          aria-label={`${q.n}-topshiriq javobi`}
          placeholder="Javobingizni shu yerga yozing"
          onChange={(e) => onChange(e.target.value)}
        />
        <div className="mt-1 flex items-center justify-between text-xs">
          <span
            className={need && words < need ? "text-amber-600 font-medium" : "text-slate-500"}
          >
            {words} so'z{need ? ` · kamida ${need}` : ""}
          </span>
          {need && words < need ? (
            <span className="text-amber-600">Yana {need - words} so'z kerak</span>
          ) : null}
        </div>
      </div>
    );
  }
  if (q.type === "multi") {
    // "Choose TWO letters, A-E" — bir nechta variant belgilanadi.
    // Kerakligidan ortiq belgilansa eng eskisi o'chadi.
    const cur: number[] = Array.isArray(value) ? value : [];
    const need = q.pick || 2;
    const toggle = (oi: number) => {
      const has = cur.includes(oi);
      let next = has ? cur.filter((x) => x !== oi) : [...cur, oi];
      if (next.length > need) next = next.slice(next.length - need);
      onChange(next);
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
              type="button"
              data-answer={oi === 0 || undefined}
              disabled={off}
              aria-pressed={cur.includes(oi)}
              onClick={() => toggle(oi)}
              className={`text-left rounded-xl border px-3 py-2.5 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                cur.includes(oi)
                  ? "border-brand-500 bg-brand-50 text-brand-800 font-medium"
                  : "border-slate-200 bg-white/60 text-slate-700 hover:border-slate-300"
              }`}
            >
              <span className="font-semibold mr-2">{LETTERS[oi]}</span>
              {o !== LETTERS[oi] && o}
            </button>
          ))}
        </div>
      </div>
    );
  }
  if (q.type === "choice") {
    // Faqat harfli variantlar (rasmdan tanlash) — bir qatorda
    return (
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
            type="button"
            data-answer={oi === 0 || undefined}
            disabled={off}
            aria-pressed={value === oi}
            onClick={() => onChange(oi)}
            className={`text-left rounded-xl border px-3 py-2.5 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
              value === oi
                ? "border-brand-500 bg-brand-50 text-brand-800 font-medium"
                : "border-slate-200 bg-white/60 text-slate-700 hover:border-slate-300"
            }`}
          >
            <span className="font-semibold mr-2">{LETTERS[oi]}</span>
            {o !== LETTERS[oi] && o}
          </button>
        ))}
      </div>
    );
  }
  return (
    <input
      data-answer
      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm"
      value={String(value ?? "")}
      autoCapitalize="off"
      autoCorrect="off"
      spellCheck={false}
      readOnly={off}
      aria-label={`${q.n}-savol javobi`}
      placeholder="Javobni yozing"
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

/** Savol matni (raqami bilan) — Cambridge'dagidek raqam qalin, bo'sh joy
 *  nuqtali chiziq (2026-09-27). */
export function QuestionText({ q }: { q: PaperQ }) {
  return (
    <p className="text-sm text-slate-900 mb-2 whitespace-pre-line leading-relaxed">
      <span className="font-bold mr-2">{q.n}</span>
      <Runs runs={questionRuns(q.q)} />
    </p>
  );
}

/**
 * Eski ko'rinish: barcha bo'limlar bitta ro'yxatda (kartochkalar).
 * Imtihon sahifalari endi CdExam'ni ishlatadi.
 */
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
          {p.image && <Figure src={p.image} className="mt-3" />}
          {p.passage && (
            <div className="mt-3 bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm text-slate-800 whitespace-pre-line leading-relaxed">
              {p.passage}
            </div>
          )}
          <div className="mt-4 space-y-5">
            {p.questions.map((q) => {
              const action = renderQuestionAction ? renderQuestionAction(q) : null;
              return (
                <div key={q.id}>
                  {q.image && <Figure src={q.image} className="mb-2" />}
                  {action ? (
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <QuestionText q={q} />
                      </div>
                      <div className="shrink-0">{action}</div>
                    </div>
                  ) : (
                    <QuestionText q={q} />
                  )}
                  <QuestionInput
                    q={q}
                    value={answers[q.id]}
                    readOnly={readOnly}
                    onChange={(v) => onChange(q.id, v)}
                  />
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </>
  );
}
