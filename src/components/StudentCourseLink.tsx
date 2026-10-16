import { Link } from "react-router-dom";
import { Headphones } from "lucide-react";
export function StudentCourseLink({ language, skill }: { language: string; skill?: string }) {
  if (language !== "en" && language !== "de") return null;
  return <Link to={`/student/course-practice${skill ? `?section=${encodeURIComponent(skill)}` : ""}`} className="my-4 block rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sky-950">
    <span className="flex items-center gap-2 font-bold"><Headphones size={20}/>{language === "de" ? "Deutsch B1" : "English Intensive"} · yangi mashqlar</span>
    <span className="mt-1 block text-sm">Darslar bo‘yicha mashqlar, tayyor audio va javob izohlari →</span>
  </Link>;
}
