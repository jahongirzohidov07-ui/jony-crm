/**
 * WRITING AI BAHOSI — natija kartasi (2026-09-28).
 *
 * Jahongir: "Writingni ham avtobaholaydigan qilib qoysak yaxshi
 * bo'lardi". Backend: api/writing_ai.py. Examiner paneli (ExamOnline)
 * va xodim sinovi (MockPracticeTake) shu kartani ko'rsatadi.
 */

export type AiTask = {
  qid: string;
  n: number | null;
  label?: string;
  part?: string;
  words: number;
  min_words: number;
  /** IELTS: har mezon 0-9 */
  criteria?: { ta: number; cc: number; lr: number; gra: number };
  band?: number;
  /** CEFR: bitta baho */
  mark?: number;
  max?: number;
  level?: string;
  feedback: string;
  /** Bo'sh / juda qisqa — AI'ga yuborilmagan, 0 */
  skipped?: boolean;
};

export type AiReview = {
  skill?: "ielts_writing" | "cefr_writing";
  status?: string;
  score?: number;
  band?: number;
  max?: number;
  level?: string;
  exact?: boolean;
  tasks?: AiTask[];
  at?: string;
  error?: string;
  /** Nechta urinish bo'ldi (xatoda avtomat qayta urinish uchun) */
  tries?: number;
};

/** Vaqtinchalik xato — o'zi qayta urinib ko'rish mumkin. */
export const AI_TRANSIENT = ["rate_limit", "ai_error", "bad_reply"];

export const AI_ERROR_TEXT: Record<string, string> = {
  no_key: "AI kaliti sozlanmagan",
  rate_limit: "AI hozir band (bepul limit) — birozdan keyin qayta urinib ko'ring",
  ai_error: "AI javob bermadi — qayta urinib ko'ring",
  bad_reply: "AI javobi tushunarsiz bo'ldi — qayta urinib ko'ring",
  bad_answers: "Javoblar saqlanishida xato — qo'lda baholang",
  shape: "Bu test Writing mocki emas",
};

const CRIT: [keyof NonNullable<AiTask["criteria"]>, string][] = [
  ["ta", "Task"],
  ["cc", "Coherence"],
  ["lr", "Lexical"],
  ["gra", "Grammar"],
];

/** Umumiy natija: "Band 6.5" yoki "54 / 75 · B2 (taxminiy)". */
export function aiSummary(r: AiReview | null | undefined): string {
  if (!r || r.score == null) return "";
  if (r.skill === "cefr_writing")
    return `${r.score} / 75 · ${r.level || ""}${r.exact === false ? " (taxminiy)" : ""}`;
  return `Band ${r.band ?? r.score}`;
}

export function AiReviewCard({ review }: { review: AiReview }) {
  const ielts = review.skill !== "cefr_writing";
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="text-lg font-bold text-slate-900">{aiSummary(review)}</span>
        <span className="text-xs text-slate-500">
          AI bahosi ·{" "}
          {ielts
            ? "4 mezon, Task 2 ikki barobar og'ir"
            : "rasmiy shkala (1.1: 0–5, 1.2 va 2: 0–6)"}
        </span>
      </div>
      {(review.tasks || []).map((t) => (
        <div key={t.qid} className="rounded-lg border border-slate-200 bg-white px-3 py-2.5">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="font-semibold text-slate-800">
              {t.label || `Task ${t.part || t.n}`}
            </span>
            <span
              className={`text-xs ${
                t.min_words && t.words < t.min_words ? "text-amber-600" : "text-slate-500"
              }`}
            >
              {t.words} so'z{t.min_words ? ` (kamida ${t.min_words})` : ""}
            </span>
            <span className="ml-auto text-sm font-semibold text-slate-900">
              {ielts
                ? `Band ${t.band ?? 0}`
                : `${t.mark ?? 0} / ${t.max ?? 0} · ${t.level || ""}`}
            </span>
          </div>
          {ielts && t.criteria ? (
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {CRIT.map(([k, label]) => (
                <span key={k} className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                  {label} <b>{t.criteria![k]}</b>
                </span>
              ))}
            </div>
          ) : null}
          {t.skipped ? (
            <p className="mt-1.5 text-xs text-amber-700">
              Javob bo'sh yoki juda qisqa — baholanmadi (0).
            </p>
          ) : t.feedback ? (
            <p className="mt-1.5 text-sm text-slate-700">{t.feedback}</p>
          ) : null}
        </div>
      ))}
    </div>
  );
}
