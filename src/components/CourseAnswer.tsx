import CourseQuestionInput from "./CourseQuestionInput";
import { getCourseQuestionOrdering } from "../lib/courseQuestionInteraction";
import { useEffect, useRef, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { api } from "../lib/api";
import { CourseActiveTime } from "../lib/courseActiveTime";
import { RewardFeedback, type LearningReward } from "./CourseMotivation";
export type Question = { id: string; prompt: string; mode: "exact" | "self"; options?: string[] };
export type Result = { attempt_id?: number; correct: boolean | null; expected: string[]; explanation: string; criteria?: string[]; saved: boolean; reward?: LearningReward; transcript?: string };
export type Drafts = Map<string, { answer: string; result: Result | null }>;
export default function CourseAnswer({ question: q, number, language, lesson, onSaved, drafts, beforeSubmit, onCommitted }: { question: Question; number: number; language: string; lesson: number; onSaved: () => void; drafts: Drafts; beforeSubmit?: () => boolean; onCommitted?: () => void }) {
  const mounted = useRef(true);
  useEffect(() => {mounted.current = true; return () => {mounted.current = false;};}, []);
  const card = useRef<HTMLDivElement>(null);
  const clock = useRef(new CourseActiveTime());
  useEffect(() => {
    const active = () => {
      const rect = card.current?.getBoundingClientRect();
      return document.visibilityState === "visible" && document.hasFocus() && !!card.current?.contains(document.activeElement)
        && !!rect && rect.bottom > 0 && rect.top < window.innerHeight;
    };
    const sample = () => clock.current.tick(performance.now(), active());
    const engage = () => { if (active()) clock.current.engage(performance.now()); };
    const root = card.current;
    root?.addEventListener("focusin", engage);
    root?.addEventListener("input", engage);
    root?.addEventListener("pointerdown", engage);
    root?.addEventListener("keydown", engage);
    const pause = () => clock.current.tick(performance.now(), false);
    root?.addEventListener("focusout", pause);
    document.addEventListener("visibilitychange", pause);
    window.addEventListener("blur", pause);
    const interval = window.setInterval(sample, 1000);
    return () => {
      clearInterval(interval);
      root?.removeEventListener("focusin", engage); root?.removeEventListener("input", engage);
      root?.removeEventListener("pointerdown", engage); root?.removeEventListener("keydown", engage);
      root?.removeEventListener("focusout", pause); document.removeEventListener("visibilitychange", pause);
      window.removeEventListener("blur", pause);
    };
  }, []);
  const draftKey = `${language}:${lesson}:${q.id}`;
  const [answer, updateAnswer] = useState(drafts.get(draftKey)?.answer || "");
  const [result, updateResult] = useState<Result | null>(drafts.get(draftKey)?.result || null);
  function setAnswer(value: string) { updateAnswer(value); drafts.set(draftKey, {answer: value, result: drafts.get(draftKey)?.result || null}); }
  function setResult(value: Result | null) { updateResult(value); drafts.set(draftKey, {answer: drafts.get(draftKey)?.answer || answer, result: value}); }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit() {
    if (!answer.trim() || busy || beforeSubmit?.() === false) return;
    setBusy(true); setError("");
    clock.current.tick(performance.now(), document.visibilityState === "visible" && document.hasFocus() && !!card.current?.contains(document.activeElement));
    const activeSeconds = clock.current.seconds();
    const submittedAnswer = answer;
    const snapshot = drafts.get(draftKey) || {answer: submittedAnswer, result: null};
    drafts.set(draftKey, snapshot);
    try {
      const saved = await api.post<Result>("/student/course-practice/answer", { language, lesson, question_id: q.id, answer: submittedAnswer });
      if (saved.attempt_id && activeSeconds >= 3) {
        // Optional timing never makes a successfully saved answer appear failed.
        void api.post("/student/course-practice/pace", {language, lesson, question_id: q.id, attempt_id: saved.attempt_id, active_seconds: activeSeconds}).catch(() => {});
      }
      onCommitted?.();
      clock.current.reset();
      if (drafts.get(draftKey) === snapshot) {
        drafts.set(draftKey, {answer: submittedAnswer, result: saved});
        if (mounted.current) updateResult(saved);
      }
      if (mounted.current) onSaved();
    }
    catch (e) { if (mounted.current) setError(e instanceof Error ? e.message : "Saqlashda xato. Qayta urinib ko‘ring."); }
    finally { if (mounted.current) setBusy(false); }
  }
  return <div ref={card} id={`course-question-${q.id}`} tabIndex={-1} className="scroll-mt-4 space-y-3 border-t pt-4">
    <p className="whitespace-pre-line break-words text-sm font-medium" lang={language}>{number}. {q.prompt}</p>
    {q.mode === "self" && <p className="text-xs text-slate-500">Ochiq javob: yozib yuboring, so‘ng namuna va mezonlar bilan solishtiring. Avtomatik baho qo‘yilmaydi.</p>}
    {q.mode === "self" && !!q.options?.length && !getCourseQuestionOrdering(q).length && <ul className="space-y-1 rounded-xl bg-slate-50 p-3 text-sm">{q.options.map((o, i) => <li key={i}>{o}</li>)}</ul>}
    <CourseQuestionInput question={q} value={answer} onChange={setAnswer} disabled={!!result || busy} aria-label={`${number}-savol javobi`}/>
    {!result && <button onClick={submit} disabled={busy || !answer.trim()} className="rounded-xl bg-sky-800 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">{busy ? "Saqlanmoqda…" : q.mode === "self" ? "Yuborish va namunani ko‘rish" : "Tekshirish"}</button>}
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    {result && <div role="status" className={`space-y-2 rounded-xl p-3 text-sm ${result.correct === false ? "bg-amber-50" : "bg-emerald-50"}`}>
      <p className="flex items-center gap-2 font-semibold"><CheckCircle2 size={17}/>{result.correct === null ? "Javob saqlandi · namuna bilan solishtiring" : result.correct ? "To‘g‘ri · javob saqlandi" : "Javob saqlandi · tuzatishni ko‘ring"}</p>
      <RewardFeedback reward={result.reward}/>
      <p className="whitespace-pre-line break-words">{result.expected.join(" / ")}</p>
      <p className="whitespace-pre-line break-words">{result.explanation}</p>
      {!!result.criteria?.length && <ul className="list-disc pl-5">{result.criteria.map((c, i) => <li key={i}>{c}</li>)}</ul>}
      {result.transcript && <details><summary className="cursor-pointer font-semibold">Transkriptni ko‘rish</summary><p lang={language} className="mt-2 whitespace-pre-line break-words">{result.transcript}</p></details>}
      <button onClick={() => { clock.current.reset(); setResult(null); setAnswer(""); }} className="underline">Qayta mashq qilish</button>
    </div>}
  </div>;
}
