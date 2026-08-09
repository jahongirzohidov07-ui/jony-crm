import { useOutletContext } from "react-router-dom";
import { ClipboardCheck } from "lucide-react";
import { ParentPageHeader } from "../components/ParentPageHeader";
import type { ParentCtx } from "./Parent";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** OTA-ONA — O'ZLASHTIRISH VA TEST NATIJALARI (alohida sahifa, 2026-08-09). */
export default function ParentResults() {
  const { d } = useOutletContext<ParentCtx>();
  const hasExams = d.exam_results && d.exam_results.length > 0;
  const hasGrades = d.daily_grades && d.daily_grades.length > 0;

  return (
    <>
      <ParentPageHeader
        title="Natijalar"
        icon={<ClipboardCheck size={18} />}
      />

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            Test natijalari
          </p>
          {!hasExams && (
            <p className="text-sm text-slate-400 text-center py-6">
              Hali tasdiqlangan test natijasi yo'q.
            </p>
          )}
          <div className="space-y-2">
            {d.exam_results?.map((e: Any, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between text-sm"
              >
                <div className="min-w-0">
                  <p className="text-slate-700">{e.title}</p>
                  <p className="text-[11px] text-slate-400">
                    {(e.date || "").slice(0, 10)}
                  </p>
                </div>
                {e.absent ? (
                  <span className="text-[11px] rounded-full px-2 py-0.5 font-medium bg-red-100 text-red-600 shrink-0">
                    Kelmadi
                  </span>
                ) : (
                  <span className="text-sm font-medium text-slate-800 shrink-0">
                    {e.band != null
                      ? `Band ${e.band}`
                      : e.max_score
                      ? `${e.score}/${e.max_score}`
                      : e.score}
                    {e.percent != null && (
                      <span className="text-[11px] text-slate-400 font-normal">
                        {" "}
                        ({e.percent}%)
                      </span>
                    )}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            Kundalik baholar (har bir dars)
          </p>
          {!hasGrades && (
            <p className="text-sm text-slate-400 text-center py-6">
              Hali kundalik baho yo'q.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            {d.daily_grades?.map((g: Any, i: number) => (
              <div
                key={i}
                title={(g.date || "").slice(0, 10)}
                className={`text-xs font-medium rounded-lg px-2 py-1 ${
                  g.score >= 4
                    ? "bg-emerald-100 text-emerald-700"
                    : g.score === 3
                    ? "bg-amber-100 text-amber-700"
                    : "bg-red-100 text-red-600"
                }`}
              >
                {(g.date || "").slice(5, 10)} · {g.score}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
