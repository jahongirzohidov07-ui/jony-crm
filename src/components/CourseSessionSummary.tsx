import { useEffect, useState } from "react";
import { CheckCircle2, RotateCcw, PencilLine } from "lucide-react";
import { api } from "../lib/api";

type Item = { question_id: string; lesson: number; prompt: string; skill?: string };
type Group = { count: number; items: Item[] };
export type SessionSummary = {
  date: string; language: string;
  plan: { total: number; completed: number };
  independent: Group; corrections: Group; needs_practice: Group; ungraded: Group;
  next_review: { due_at: string | null; items: Item[] } | null;
  comparison: { question_count: number; before_correct: number; after_correct: number } | null;
};
function EvidenceList({ items, onLesson }: { items: Item[]; onLesson: (lesson: number, questionId?: string) => void }) {
  return <ul className="mt-3 space-y-2">{items.map(item => <li key={`${item.lesson}:${item.question_id}`} className="rounded-xl bg-white/80 p-3 text-sm"><p className="break-words">{item.prompt}</p><button type="button" onClick={() => onLesson(item.lesson, item.question_id)} className="mt-1 min-h-11 text-xs font-semibold underline">{item.lesson}-dars · shu savolni ochish</button></li>)}</ul>;
}
export default function CourseSessionSummary({ language, onLesson }: { language: string; onLesson: (lesson: number, questionId?: string) => void }) {
  const [data, setData] = useState<SessionSummary | null>(null);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true; setData(null); setError(false);
    api.fresh<SessionSummary>(`/student/course-practice/session-summary?language=${encodeURIComponent(language)}`)
      .then(value => { if (active) setData(value); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [language, revision]);
  return <section aria-label="Bugungi bilim xulosasi" className="space-y-4">
    <div><h2 className="text-xl font-bold">Bugun nimani mashq qildim?</h2><p className="mt-1 text-sm text-slate-600">Shaxsiy rejangizdagi saqlangan javoblar asosida.</p></div>
    {error ? <div role="alert" className="rounded-xl bg-amber-50 p-4 text-sm">Xulosani yuklab bo‘lmadi. Javoblaringiz saqlangan bo‘lsa, yo‘qolmaydi.<button type="button" onClick={() => setRevision(n => n + 1)} className="mt-2 block min-h-11 font-semibold underline">Xulosani qayta yuklash</button></div> : !data ? <p role="status">Javoblaringizdan xulosa tayyorlanmoqda…</p> : <>
      <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4"><h3 className="flex items-center gap-2 font-bold"><CheckCircle2 size={19}/>Birinchi urinishda to‘g‘ri: {data.independent.count}</h3><p className="mt-1 text-xs text-slate-600">Bu savollarga ilk tekshirilgan javobingiz bugun to‘g‘ri bo‘lgan.</p>{data.independent.count ? <EvidenceList items={data.independent.items} onLesson={onLesson}/> : <p className="mt-2 text-sm">Bu reja uchun hali shunday natija qayd etilmagan.</p>}</section>
      <section className="rounded-2xl border border-sky-200 bg-sky-50 p-4"><h3 className="flex items-center gap-2 font-bold"><RotateCcw size={19}/>Tuzatilgan xatolar: {data.corrections.count}</h3><p className="mt-1 text-xs text-slate-600">Oldingi noto‘g‘ri javobdan keyin bugun to‘g‘ri javob berdingiz.</p>{data.corrections.count ? <EvidenceList items={data.corrections.items} onLesson={onLesson}/> : <p className="mt-2 text-sm">Hozircha tuzatib qayta ishlangan savol yo‘q.</p>}</section>
      {!!data.needs_practice.count && <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4"><h3 className="font-bold">Yana birga mashq qilamiz: {data.needs_practice.count}</h3><p className="mt-1 text-sm">Bu savollarning oxirgi javobi hali to‘g‘ri emas. Izohni ko‘rib, keyin yana urinib ko‘ring.</p><EvidenceList items={data.needs_practice.items} onLesson={onLesson}/></section>}
      {!!data.ungraded.count && <section className="rounded-2xl border p-4"><h3 className="flex items-center gap-2 font-bold"><PencilLine size={19}/>Yozib yoki gapirib mashq qildingiz: {data.ungraded.count}</h3><p className="mt-1 text-xs text-slate-600">Bu javoblar avtomatik to‘g‘ri/noto‘g‘ri baholanmagan. Namuna yoki ustoz fikri bilan solishtiring.</p><EvidenceList items={data.ungraded.items} onLesson={onLesson}/></section>}
      <section className="rounded-2xl border border-indigo-200 bg-indigo-50 p-4"><h3 className="font-bold">Keyingi safar nimani eslayman?</h3>{data.next_review?.items.length ? <><p className="mt-1 text-sm">Quyidagi savollarni javobga qaramasdan qayta eslab ko‘ring{data.next_review.due_at ? ` · navbat: ${data.next_review.due_at}` : ""}.</p><EvidenceList items={data.next_review.items} onLesson={onLesson}/></> : <p className="mt-2 text-sm">Hozircha takrorlash uchun savol belgilanmagan. Keyingi kirishda rejangizni tekshiring.</p>}</section>
      {data.comparison && <div className="rounded-2xl border p-4 text-sm"><h3 className="font-bold">Bir xil savollarda oldin va hozir</h3><p className="mt-2">{data.comparison.question_count} ta savol: oldin {data.comparison.before_correct} ta, hozir {data.comparison.after_correct} ta to‘g‘ri.</p><p className="mt-1 text-xs text-slate-600">Shu savollarning qayta ishlangan natijasi; butun til darajangiz bahosi emas.</p></div>}
    </>}
  </section>;
}
