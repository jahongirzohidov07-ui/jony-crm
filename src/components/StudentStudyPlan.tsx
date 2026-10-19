import { CourseMotivation } from "./CourseMotivation";
import { Link } from "react-router-dom";

export function StudentStudyPlan({language}: {language: string}) {
  if (language !== "en" && language !== "de") return null;
  return <section className="my-4 space-y-3" aria-label="Bugungi darsim va uyga vazifam">
    <CourseMotivation key={language} language={language} compact/>
    <div className="flex flex-wrap gap-2 text-sm"><Link to="/student/course-practice?view=lesson" className="flex-1 rounded-xl border bg-white px-4 py-3 text-center font-semibold text-sky-800">Ustoz belgilagan dars →</Link><Link to="/student/course-practice?view=portfolio" className="flex-1 rounded-xl border bg-white px-4 py-3 text-center font-semibold text-indigo-800">Ijodiy ishlarim →</Link></div>
    <p className="text-xs text-slate-500">{language === "de" ? "Deutsch · 6 oylik B1 reja" : "English Intensive · 8 oylik B2 reja"}. Sertifikat darajasi alohida imtihonda aniqlanadi.</p>
  </section>;
}
