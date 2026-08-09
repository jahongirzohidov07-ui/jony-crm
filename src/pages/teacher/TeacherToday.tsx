import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle, CheckCircle2, ChevronRight, Clock, Users,
} from "lucide-react";
import { api } from "../../lib/api";
import { BrandIcon } from "../../components/BrandIcon";
import type { LessonCard, TeacherHome } from "../../lib/teacherApi";

/**
 * JONY TEACHER — bosh ekran: "bugun nima qilishim kerak".
 *
 * Ustoz ilovani ochganda ko'radigan BIRINCHI narsa — bugungi darslari
 * va qaysinisiga hali yo'qlama qo'yilmagani. Boshqa hamma narsa
 * pastda yoki "Bo'limlar" tabida.
 */
export default function TeacherToday() {
  const [d, setD] = useState<TeacherHome | null>(null);
  const [missed, setMissed] = useState<LessonCard[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<TeacherHome>("/teacher/home")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
    api
      .get<{ missed: LessonCard[] }>("/teacher/today")
      .then((r) => setMissed(r.missed || []))
      .catch(() => {});
  }, []);

  if (err)
    return <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>;

  const today = new Date(d.date);
  const dayName = [
    "Yakshanba", "Dushanba", "Seshanba", "Chorshanba",
    "Payshanba", "Juma", "Shanba",
  ][today.getDay()];

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-14">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2 mb-4 opacity-90">
            <BrandIcon size={18} className="rounded-md" />
            <span className="text-sm font-medium">Jony Teacher</span>
          </div>
          <h1 className="text-xl font-semibold">{d.teacher}</h1>
          <p className="text-sm opacity-90 mt-0.5">
            {dayName} · {d.date.slice(8, 10)}.{d.date.slice(5, 7)}
            {d.grade ? ` · ${d.grade}` : ""}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-9 space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <Stat value={String(d.groups)} label="Guruh" />
          <Stat value={String(d.students)} label="O'quvchi" />
          <Stat value={String(d.lessons_this_month)} label="Bu oy dars" />
        </div>

        {missed.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-start gap-2.5 mb-2">
              <AlertTriangle size={17} className="text-amber-600 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-amber-900">
                  Yo'qlama qo'yilmagan darslar
                </p>
                <p className="text-xs text-amber-700">
                  Oyligingiz shu yo'qlamadan hisoblanadi
                </p>
              </div>
            </div>
            <div className="space-y-1.5 mt-3">
              {missed.slice(0, 5).map((l) => (
                <Link
                  key={l.lesson_id}
                  to={`/teacher/lesson/${l.lesson_id}`}
                  className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 border border-amber-200"
                >
                  <span className="text-xs text-slate-500 shrink-0">
                    {l.date.slice(8, 10)}.{l.date.slice(5, 7)}
                  </span>
                  <span className="text-sm text-slate-800 flex-1 truncate">
                    {l.group}
                  </span>
                  <ChevronRight size={15} className="text-slate-300 shrink-0" />
                </Link>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="flex items-baseline justify-between mb-2">
            <p className="text-sm font-semibold text-slate-800">
              Bugungi darslar
            </p>
            {d.pending > 0 && (
              <span className="text-xs font-medium text-amber-600">
                {d.pending} ta kutmoqda
              </span>
            )}
          </div>

          {d.today.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <p className="text-sm text-slate-500">Bugun darsingiz yo'q</p>
              <p className="text-xs text-slate-400 mt-1">Dam oling 🙂</p>
            </div>
          ) : (
            <div className="space-y-2">
              {d.today.map((l) => (
                <LessonRow key={l.lesson_id} l={l} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export function LessonRow({ l }: { l: LessonCard }) {
  return (
    <Link
      to={`/teacher/lesson/${l.lesson_id}`}
      className="flex items-center gap-3 bg-white rounded-xl shadow-sm border border-slate-200 p-4 active:scale-[0.99] transition"
    >
      <div
        className={`w-11 h-11 rounded-xl flex flex-col items-center justify-center shrink-0 ${
          l.done
            ? "bg-emerald-50 text-emerald-600"
            : "bg-brand-50 text-brand-600"
        }`}
      >
        {l.done ? (
          <CheckCircle2 size={20} />
        ) : (
          <>
            <Clock size={15} />
            <span className="text-[9px] font-semibold leading-none mt-0.5">
              {(l.time || "--:--").slice(0, 5)}
            </span>
          </>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-800 truncate">
          {l.group}
          {l.level ? (
            <span className="ml-1.5 text-[11px] font-normal text-slate-400">
              {l.level}
            </span>
          ) : null}
        </p>
        <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
          <Users size={12} />
          {l.marked}/{l.students} belgilangan
          {l.graded > 0 ? ` · ${l.graded} baho` : ""}
        </p>
      </div>
      <ChevronRight size={17} className="text-slate-300 shrink-0" />
    </Link>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3 text-center">
      <p className="text-xl font-bold text-slate-900 leading-tight">{value}</p>
      <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}
