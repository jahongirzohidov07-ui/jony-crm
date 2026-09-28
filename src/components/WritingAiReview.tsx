/**
 * WRITING AI BAHOSI — natija kartasi (2026-09-28).
 *
 * Jahongir: "Writingni ham avtobaholaydigan qilib qoysak yaxshi
 * bo'lardi". Backend: api/writing_ai.py. Examiner paneli (ExamOnline)
 * va xodim sinovi (MockPracticeTake) shu kartani ko'rsatadi.
 */

/** Bitta xato: asl matn -> to'g'risi, qisqa sabab (inglizcha).
 *  serious — xato ma'noni buzadi (band'ni shu hal qiladi). */
export type AiError = { wrong: string; right: string; why?: string; serious?: boolean };

export type AiTask = {
  qid: string;
  /** Grammatika va lug'at xatolari — alohida, bittama-bitta (2026-09-28) */
  grammar?: AiError[];
  vocabulary?: AiError[];
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

/** Xatolar ro'yxati (Jahongir: "Grammar mistakes, vocabulary mistakes
 *  alohida har bir korsatilsin bitta bitta"). */
function ErrorList({ title, items, tone }: { title: string; items: AiError[]; tone: string }) {
  return (
    <div className="mt-2">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        {title} ({items.length})
      </p>
      {items.length ? (
        <ol className="mt-1 space-y-1">
          {items.map((e, i) => (
            <li key={i} className="flex gap-2 text-sm leading-snug">
              <span className="w-5 shrink-0 text-right text-xs text-slate-400 tabular-nums pt-0.5">
                {i + 1}.
              </span>
              <span className="min-w-0">
                <span className="text-rose-700 line-through decoration-rose-300">{e.wrong}</span>
                <span className="mx-1.5 text-slate-400">→</span>
                <span className={`font-semibold ${tone}`}>{e.right}</span>
                {e.why ? <span className="ml-2 text-xs text-slate-500">· {e.why}</span> : null}
                {e.serious ? (
                  <span className="ml-2 rounded bg-amber-100 px-1.5 py-px text-[10px] font-semibold text-amber-800">
                    affects meaning
                  </span>
                ) : null}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-0.5 text-xs text-slate-400">No mistakes found.</p>
      )}
    </div>
  );
}

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
            : "rasmiy shkala (1.1 va 1.2: 0–5, 2: 0–6; jami 16)"}
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
          {/* Izoh inglizcha, rasmiy "Examiner comment" uslubida (2026-09-28,
              Jahongir: "writing feedback inglizcha bolishi kerak") */}
          {t.feedback ? (
            <div className="mt-2">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Examiner comment
              </p>
              <p className="text-sm leading-relaxed text-slate-700">{t.feedback}</p>
            </div>
          ) : t.skipped ? (
            <p className="mt-1.5 text-xs text-amber-700">Javob yozilmagan — 0.</p>
          ) : null}
          {!t.skipped && (t.grammar || t.vocabulary) ? (
            <div className="grid gap-x-6 sm:grid-cols-2">
              <ErrorList title="Grammar mistakes" items={t.grammar || []} tone="text-emerald-700" />
              <ErrorList title="Vocabulary mistakes" items={t.vocabulary || []} tone="text-emerald-700" />
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
