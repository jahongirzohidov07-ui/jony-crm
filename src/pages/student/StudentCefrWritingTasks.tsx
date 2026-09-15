import { StudentIcon } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, ChevronRight } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** CEFR Writing — imtihon vazifalari ro'yxati (2026-08-26). */
export default function StudentCefrWritingTasks() {
  const { part = "1" } = useParams();
  const [rows, setRows] = useState<Any[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/cefr/writing/tasks?part=" + part)
      .then((r) => setRows(r.items || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [part]);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;

  return (
    <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="student-lesson-heading student-hero student-pattern flex items-center gap-2.5 text-white">
        <Link
          to="/student/cefr/writing"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          {part === "2" ? "Part 2 — C1" : "Part 1 — ikki xat"}
        </p>
      <StudentIcon name="writing" size={42} />
      </div>

      <p className="text-[12px] text-slate-400 mt-3 leading-relaxed">
        {part === "2"
          ? "180-200 so'z, 30 daqiqa. Blog, forum yoki maqola — "
            + "janriga qarab talab boshqacha bo'ladi."
          : "Har vaziyatda ikki xat: do'stingizga (7 daqiqa, ~50 "
            + "so'z) va rahbariyatga (23 daqiqa, 120-150 so'z)."}
      </p>

      <div className="space-y-2 mt-4">
        {rows.map((t: Any) => (
          <Link
            key={t.id}
            to={`/student/cefr/writing/task/${t.id}`}
            className="student-study-card flex items-center gap-3 rounded-2xl border p-3.5"
            style={card}
          >
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-[14px]">{t.title}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {t.from ? "Xabar: " + t.from + " · " : ""}
                {t.type}
              </p>
            </div>
            {t.done && <Check size={16} className="text-emerald-400 shrink-0" />}
            <ChevronRight size={16} className="text-slate-500 shrink-0" />
          </Link>
        ))}
      </div>
    </div>
  );
}
