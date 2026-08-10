import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, BookOpenCheck, Check, ChevronRight } from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — GRAMMAR MAVZULARI (2026-08-10).
 *
 * Jahongir: "Grammar har bir ingliz tilidagi mavzuga xilma-xil
 * mashqlar bo'lsin." Mavzular daraja bo'yicha (A1 → B1) guruhlangan,
 * har birida progress halqasi: mavzuni "yopish" uchun hamma savolni
 * kamida bir marta TO'G'RI yechish kerak.
 */
export default function StudentGrammar() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/grammar/topics")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const levels: Any[] = d?.levels || [];
  const done = levels
    .flatMap((l: Any) => l.topics)
    .filter((t: Any) => t.done).length;
  const total = levels.flatMap((l: Any) => l.topics).length;

  return (
    <>
      <div className="bg-gradient-to-br from-violet-700 to-violet-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/games"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Mashqlar
          </Link>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <BookOpenCheck size={22} />
            Grammar
          </h1>
          <p className="text-sm opacity-90 mt-0.5">
            {total
              ? `${done}/${total} mavzu yopildi · ${d?.total_correct || 0} savol yechildi`
              : "Mavzuni tanlang"}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4 pb-8">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4 text-sm text-red-600">
            {err}
          </div>
        )}
        {levels.map((lv: Any) => (
          <div key={lv.level}>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2 px-1">
              {lv.level} daraja
            </p>
            <div className="space-y-2">
              {lv.topics.map((t: Any) => (
                <Link
                  key={t.topic}
                  to={`/student/grammar/${encodeURIComponent(t.topic)}`}
                  className="flex items-center gap-3 bg-white rounded-xl shadow-sm border border-slate-200 p-4 active:scale-[0.99] transition"
                >
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
                      t.done
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-violet-50 text-violet-600"
                    }`}
                  >
                    {t.done ? <Check size={18} /> : `${t.percent}%`}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">
                      {t.topic}
                    </p>
                    <p className="text-xs text-slate-400">
                      {t.solved}/{t.total} savol yechildi
                    </p>
                    <div className="h-1.5 bg-slate-100 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          t.done ? "bg-emerald-500" : "bg-violet-500"
                        }`}
                        style={{ width: `${t.percent}%` }}
                      />
                    </div>
                  </div>
                  <ChevronRight size={18} className="text-slate-300 shrink-0" />
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
