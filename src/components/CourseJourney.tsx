import { Check, Flag, Map, Play } from "lucide-react";
import { getCourseMission } from "../lib/courseMissions";

type Lesson = {lesson: number; title: string; level?: string; completed?: boolean; correct_count?: number; question_count: number};
type Props = {
  checkpoints: {week: number; passed: boolean; available: boolean}[];
  language: string;
  lessons: Lesson[];
  selected: number | null;
  onSelect: (lesson: number) => void;
  onCheckpoint: (week: number) => void;
  onMission?: (lesson: number) => void;
};

export function CourseJourney({language, lessons, selected, onSelect, onCheckpoint, checkpoints, onMission}: Props) {
  const perMonth = language === "de" ? 12 : 24;
  const perWeek = language === "de" ? 3 : 6;
  // Group by curriculum lesson number, not API array position: gaps never shift missions.
  const ordered = [...lessons].sort((a, b) => a.lesson - b.lesson);
  const months = [...new Set(ordered.map(l => Math.floor((l.lesson - 1) / perMonth)))];
  const active = selected ?? ordered.find(l => !l.completed)?.lesson ?? ordered[0]?.lesson;
  return <section aria-label="Kurs xaritasi" className="space-y-3">
    <div className="flex items-start gap-3 rounded-2xl bg-indigo-950 p-5 text-white"><Map className="shrink-0"/><div><h2 className="text-lg font-bold">Har hafta hayotda ishlatib ko‘ring</h2><p className="mt-1 text-sm text-indigo-100">{months.length} oy · {lessons.length} dars · hafta oxirida o‘zingiz yaratgan ish</p><p className="mt-2 text-xs text-indigo-200">Haqiqiy yoki o‘ylab topilgan vaziyatni tanlang. Ishni saqlash — mashq dalili; til darajasi yoki sertifikat tasdig‘i emas.</p></div></div>
    {months.map(m => {
      const monthLessons = ordered.filter(l => Math.floor((l.lesson - 1) / perMonth) === m);
      const done = monthLessons.filter(l => l.completed).length;
      const weeks = [...new Set(monthLessons.map(l => Math.ceil(l.lesson / perWeek)))];
      return <details key={m} open={active !== undefined && Math.floor((active - 1) / perMonth) === m} className="group overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <summary className="cursor-pointer p-4 font-semibold"><span className="mr-2 inline-flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-800">{m + 1}</span>{m + 1}-oy <span className="ml-2 text-xs font-normal text-slate-500">{done}/{monthLessons.length} dars javoblari yuborilgan</span></summary>
        <div className="space-y-4 px-4 pb-4">{weeks.map(week => {
          const checkpoint = checkpoints.find(c => c.week === week);
          const weekLessons = monthLessons.filter(l => Math.ceil(l.lesson / perWeek) === week);
          const mission = getCourseMission(language, weekLessons[0].lesson);
          return <div key={week} className="space-y-3 border-l-2 border-indigo-100 pl-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">{week}-hafta · {weekLessons[0]?.level}</p>
            {mission && <div className="space-y-2 rounded-xl bg-indigo-50 p-3 text-sm">
              <h3 className="text-base font-bold text-indigo-950">{mission.title}</h3>
              <p>{mission.prompt}</p>
              <p><strong>Hafta oxirida: </strong>{mission.output}.</p>
              <details><summary className="cursor-pointer py-2 font-semibold text-indigo-900">Ishimni qanday tekshiraman?</summary><ul className="list-disc space-y-2 pl-5">{mission.criteria.map(item => <li key={item}>{item}</li>)}</ul><p className="mt-2 text-xs text-slate-600">Mezonlar o‘zingiz tekshirishingiz uchun. Javob yuborish yoki bilim sinovidan o‘tish bu ishni avtomatik tasdiqlamaydi.</p></details>
              {onMission && ordered.some(l => l.lesson === mission.lesson) ? <button type="button" onClick={() => onMission(mission.lesson)} className="min-h-11 w-full rounded-xl bg-indigo-800 px-3 py-2 font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700">Ishimni portfolioga yozish →</button> : <p className="text-xs text-indigo-900">Ishingizni «Ijodiy ishlarim» bo‘limida {mission.lesson}-darsga saqlang.</p>}
            </div>}
            <details open={selected !== null && weekLessons.some(l => l.lesson === selected)}><summary className="cursor-pointer py-2 text-sm font-semibold text-slate-700">Darslar va grammatika · {weekLessons.length} dars</summary><div className="space-y-2">
              {weekLessons.map(l => <button type="button" key={l.lesson} onClick={() => onSelect(l.lesson)} aria-current={selected === l.lesson ? "step" : undefined} className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 ${selected === l.lesson ? "border-indigo-400 bg-indigo-50" : "border-slate-100 hover:bg-slate-50"}`}>
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${l.completed ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{l.completed ? <Check size={16}/> : l.lesson}</span>
                <span className="min-w-0 flex-1"><span className="break-words text-sm font-medium">{l.title}</span><span className="block text-xs text-slate-500">{l.completed ? "Javoblar yuborilgan" : selected === l.lesson ? "Hozirgi dars" : "Mashq qilish"}</span></span><Play size={14} className="shrink-0 text-indigo-700"/>
              </button>)}
            </div></details>
            <button type="button" onClick={() => onCheckpoint(week)} className="flex w-full items-center justify-between gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-left text-sm font-semibold text-amber-950"><span className="flex items-center gap-2"><Flag size={18}/>{week}-hafta bilim sinovi</span><span className="text-xs">{checkpoint?.passed ? "✓ O‘tilgan" : checkpoint?.available ? "Tayyor →" : "Shartlarini ko‘rish →"}</span></button>
          </div>;
        })}</div>
      </details>;
    })}
  </section>;
}
