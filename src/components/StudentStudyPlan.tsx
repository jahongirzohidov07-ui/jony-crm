import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

type Lesson = {lesson: number; title: string; completed: boolean; submitted_count: number; question_count: number};
type Detail = {sections: {id: string; skill: string; questions: {id: string}[]}[]; answers?: Record<string, unknown>};
const labels: Record<string, string> = {reading: "O‘qish", listening: "Tinglash", grammar: "Grammatika", writing: "Yozish", speaking: "Gapirish", homework: "Haftalik mustahkamlash"};
export function StudentStudyPlan({language}: {language: string}) {
  const [data, setData] = useState<{lessons: Lesson[]; current: Lesson; detail: Detail} | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setData(null); setError(false);
    async function load() {
      try {
        const list = await api.fresh<{lessons: Lesson[]; resume_lesson?: number}>(`/student/course-practice?language=${language}`);
        const current = list.lessons.find(l => l.lesson === list.resume_lesson) || list.lessons[0];
        if (!current) throw new Error("No lessons");
        const detail = await api.fresh<Detail>(`/student/course-practice/${current.lesson}?language=${language}`);
        if (active) setData({lessons: list.lessons, current, detail});
      } catch { if (active) setError(true); }
    }
    void load(); return () => {active = false;};
  }, [language, retry]);
  const title = language === "de" ? "Deutsch · 6 oylik B1 reja" : "English Intensive · 8 oylik B2 reja";
  return <section className="my-4 space-y-3 rounded-3xl border border-sky-200 bg-sky-50 p-5 text-slate-900" aria-label="Bugungi darsim va uyga vazifam">
    <h2 className="text-lg font-bold">Bugungi darsim va uyga vazifam</h2>
    <p className="text-sm text-sky-800">{title}</p>
    <p className="text-xs text-slate-600">Kurs maqsadi; sertifikat natijasi imtihonda aniqlanadi. Ustozingiz belgilagan darsni ochishingiz ham mumkin.</p>
    {error ? <p role="alert">Reja yuklanmadi. <button className="underline" onClick={() => setRetry(n => n + 1)}>Qayta urinish</button></p> : !data ? <p role="status">Dars rejangiz yuklanmoqda…</p> : <>
      <p className="text-xs text-slate-600">{data.lessons.filter(l => l.completed).length} / {data.lessons.length} darsning barcha javoblari yuborilgan</p>
      <h3 className="font-semibold">{data.current.lesson}-dars · {data.current.title}</h3>
      <p className="text-sm">Yuborilgan: {data.current.submitted_count} / {data.current.question_count} mashq</p>
      <Link className="block rounded-xl bg-sky-800 px-4 py-3 text-center font-semibold text-white" to={`/student/course-practice?lesson=${data.current.lesson}`}>Darsni davom ettirish →</Link>
      <div className="divide-y divide-sky-100">{data.detail.sections.map(s => {
        const done = s.questions.filter(q => Object.prototype.hasOwnProperty.call(data.detail.answers || {}, q.id)).length;
        return <Link key={s.id} to={`/student/course-practice?lesson=${data.current.lesson}&section=${s.skill}`} className="flex items-center justify-between gap-3 py-3 text-sm"><span>{labels[s.skill] || s.skill}</span><span>{done} / {s.questions.length} {done === s.questions.length ? "✓" : "→"}</span></Link>;
      })}</div>
      <p className="text-xs text-slate-600">Bu hisob javob yuborilganini bildiradi. Ochiq javoblarni namuna va mezonlar bilan tekshiring.</p>
      {data.current.completed && data.current.lesson < data.lessons.length && <Link className="block font-semibold text-sky-800" to={`/student/course-practice?lesson=${data.current.lesson + 1}`}>Keyingi darsga o‘tish →</Link>}
    </>}
  </section>;
}
