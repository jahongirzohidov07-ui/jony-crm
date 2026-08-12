import { useEffect, useState } from "react";
import { formatDayMonth } from "../../lib/format";
import { api } from "../../lib/api";
import type { TeacherWeek as Week } from "../../lib/teacherApi";
import { LessonRow } from "./TeacherToday";

/** JONY TEACHER — shu haftaning dars jadvali. */
export default function TeacherWeek() {
  const [d, setD] = useState<Week | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Week>("/teacher/week")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-10">
        <div className="max-w-md mx-auto">
          <h1 className="text-xl font-semibold">Haftalik jadval</h1>
          {d && (
            <p className="text-sm opacity-90 mt-0.5">
              {formatDayMonth(d.start)} —{" "}
              {formatDayMonth(d.end)}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        {err && <p className="text-sm text-slate-500 text-center py-10">{err}</p>}
        {!d && !err && (
          <p className="text-sm text-slate-400 text-center py-10">Yuklanmoqda…</p>
        )}

        {d?.days.map((day) => (
          <div key={day.date}>
            <div className="flex items-baseline gap-2 mb-2 px-1">
              <p
                className={`text-sm font-semibold ${
                  day.is_today ? "text-brand-700" : "text-slate-700"
                }`}
              >
                {day.label}
              </p>
              <span className="text-xs text-slate-400">
                {formatDayMonth(day.date)}
              </span>
              {day.is_today && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-brand-50 text-brand-600">
                  bugun
                </span>
              )}
            </div>
            {day.lessons.length === 0 ? (
              <p className="text-xs text-slate-300 px-1 pb-1">dars yo'q</p>
            ) : (
              <div className="space-y-2">
                {day.lessons.map((l) => (
                  <LessonRow key={l.lesson_id} l={l} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
