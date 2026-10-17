import { Check, Flag, Map, Play } from "lucide-react";

type Lesson = {lesson: number; title: string; level?: string; completed?: boolean; correct_count?: number; question_count: number};
export function CourseJourney({language, lessons, selected, onSelect, onCheckpoint, checkpoints}: {checkpoints: {week: number; passed: boolean; available: boolean}[]; language: string; lessons: Lesson[]; selected: number | null; onSelect: (lesson: number) => void; onCheckpoint: (week: number) => void}) {
  const perMonth = language === "de" ? 12 : 24;
  const perWeek = language === "de" ? 3 : 6;
  const months = Math.ceil(lessons.length / perMonth);
  return <section aria-label="Kurs xaritasi" className="space-y-3">
    <div className="flex items-start gap-3 rounded-2xl bg-indigo-950 p-5 text-white"><Map className="shrink-0"/><div><h2 className="text-lg font-bold">Kichik qadamlar, katta maqsad</h2><p className="mt-1 text-sm text-indigo-100">{months} oy · {lessons.length} dars · har hafta yangi vaziyatda bilim sinovi</p><p className="mt-2 text-xs text-indigo-200">Belgilar bajarilgan ishni ko‘rsatadi. B2 yoki B1 sertifikati alohida imtihonda aniqlanadi.</p></div></div>
    {Array.from({length: months}, (_, m) => {
      const monthLessons = lessons.slice(m * perMonth, (m + 1) * perMonth);
      const done = monthLessons.filter(l => l.completed).length;
      return <details key={m} open={selected !== null && Math.floor((selected - 1) / perMonth) === m} className="group overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <summary className="cursor-pointer p-4 font-semibold"><span className="mr-2 inline-flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-800">{m + 1}</span>{m + 1}-oy <span className="ml-2 text-xs font-normal text-slate-500">{done}/{monthLessons.length} dars bajarilgan</span></summary>
        <div className="space-y-4 px-4 pb-4">{Array.from({length: Math.ceil(monthLessons.length / perWeek)}, (_, w) => {
          const week = m * 4 + w + 1;
          const checkpoint = checkpoints.find(c => c.week === week);
          const weekLessons = monthLessons.slice(w * perWeek, (w + 1) * perWeek);
          return <div key={week} className="space-y-2 border-l-2 border-indigo-100 pl-3"><p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">{week}-hafta · {weekLessons[0]?.level}</p>
            {weekLessons.map(l => <button type="button" key={l.lesson} onClick={() => onSelect(l.lesson)} aria-current={selected === l.lesson ? "step" : undefined} className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 ${selected === l.lesson ? "border-indigo-400 bg-indigo-50" : "border-slate-100 hover:bg-slate-50"}`}>
              <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${l.completed ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{l.completed ? <Check size={16}/> : l.lesson}</span>
              <span className="min-w-0 flex-1"><span title={l.title} className="line-clamp-2 text-sm font-medium">{l.title}</span><span className="text-xs text-slate-500">{l.completed ? "Javoblar yuborilgan" : selected === l.lesson ? "Hozirgi dars" : "Mashq qilish"}</span></span><Play size={14} className="shrink-0 text-indigo-700"/>
            </button>)}
            <button type="button" onClick={() => onCheckpoint(week)} className="flex w-full items-center justify-between gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-left text-sm font-semibold text-amber-950"><span className="flex items-center gap-2"><Flag size={18}/>{week}-hafta bilim sinovi</span><span className="text-xs">{checkpoint?.passed ? "✓ O‘tilgan" : checkpoint?.available ? "Tayyor →" : "Shartlarini ko‘rish →"}</span></button>
          </div>;
        })}</div>
      </details>;
    })}
  </section>;
}
