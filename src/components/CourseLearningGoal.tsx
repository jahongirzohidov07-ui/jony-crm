import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

type Progress = { question_count: number; submitted_count: number };
type CoursePlan = Progress & {
  lesson: number;
  title: string;
  sections: (Progress & { id: string; title: string; skill: string })[];
};
type CourseResponse = { plan?: CoursePlan };

/** Course content and submission status describe the next task, never mastery. */
export function CourseLearningGoal({ language }: { language: string }) {
  if (language !== "en" && language !== "de") return null;
  return <LearningGoal key={language} language={language} />;
}

function LearningGoal({ language }: { language: string }) {
  const [data, setData] = useState<CourseResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setFailed(false);
    api.fresh<CourseResponse>(`/student/course-practice?language=${encodeURIComponent(language)}`)
      .then(result => { if (active) setData(result); })
      .catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [language, revision]);

  const plan = data?.plan;
  const next = plan?.sections.find(section => section.submitted_count < section.question_count);
  const goals:Record<string,string> = {reading:"Matndan kerakli ma’lumotni topishni mashq qilamiz",listening:"Eshitganimizni tushunishni mashq qilamiz",grammar:"So‘zlardan to‘g‘ri foydalanishni mashq qilamiz",speaking:"O‘z fikrimizni aytishni mashq qilamiz",writing:"O‘z fikrimizni yozishni mashq qilamiz",homework:"O‘rganganimizni mustahkamlaymiz"};
  const href = plan
    ? `/student/course-practice?view=lesson&lesson=${plan.lesson}${next ? `&section=${encodeURIComponent(next.skill)}` : ""}`
    : "/student/course-practice?view=lesson";

  return <section aria-label="Darsdagi maqsad" className="rounded-3xl border border-sky-200 bg-sky-50 p-5 text-slate-900">
    <p className="text-xs font-semibold uppercase tracking-wide text-sky-800">{language === "de" ? "Deutsch" : "English Intensive"} · Darsdagi maqsad</p>
    {failed ? <div role="alert" className="mt-3 text-sm">
      Dars maqsadini yuklab bo‘lmadi.
      <button type="button" onClick={() => setRevision(value => value + 1)} className="ml-2 min-h-11 font-semibold text-sky-800 underline">Qayta urinish</button>
    </div> : !data ? <p role="status" className="mt-3 text-sm">Dars maqsadi yuklanmoqda…</p> : plan ? <>
      <h2 className="mt-2 text-lg font-bold">{next ? goals[next.skill] || "Darsdagi keyingi vazifani bajaramiz" : "Darsdagi ishlaringiz yuborildi"}</h2>
      {next ? <>
        <p className="mt-2 text-xs font-semibold text-sky-800">{plan.lesson}-dars · keyingi mashq</p>
        <p className="mt-1 text-base font-semibold">{next.title}</p>
      </> : <p className="mt-3 text-sm">Bu darsdagi topshiriqlar yuborilgan. Javob izohlarini ko‘rib chiqing yoki bugungi takrorlash rejasini bajaring.</p>}
      
      <details className="mt-3 text-sm">
        <summary className="cursor-pointer py-2 font-semibold">Dars bo‘yicha topshirish holati</summary>
        <p className="mt-2">{plan.title}</p><p className="mt-1 text-xs text-slate-600">Topshirilgan ishlar hisobi; til darajasi bahosi emas.</p><p className="mt-1">{plan.submitted_count} / {plan.question_count} topshiriqqa javob yuborilgan.</p>
        <ul className="mt-2 space-y-1">{plan.sections.map(section => <li key={section.id}>{section.title}: {section.submitted_count} / {section.question_count}</li>)}</ul>
      </details>
    </> : <p className="mt-3 text-sm">Dars maqsadi hozircha mavjud emas. Kursdan dars tanlang.</p>}
    {(data || failed) && <Link to={href} className="mt-2 inline-flex min-h-11 items-center text-sm font-semibold text-sky-800 underline">{next ? "Shu mashqni ochish" : "Darsni ochish"} →</Link>}
  </section>;
}
