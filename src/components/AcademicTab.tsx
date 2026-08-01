import { useEffect, useState } from "react";
import { Info, TrendingDown } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** Akademik analitika: fan/daraja kesimi, top ustozlar, voronka, ketish. */
export function AcademicTab({ branchId }: { branchId?: number | null }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    const q = branchId ? `?branch_id=${branchId}` : "";
    api.get<Any>(`/analytics/academic${q}`).then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [branchId]);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const Dist = ({ title, rows, tone }: Any) => (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <p className="text-sm font-medium text-slate-700 mb-3">{title}</p>
      {rows.map((r: Any) => (
        <div key={r.key} className="mb-2">
          <div className="flex justify-between text-sm">
            <span className="text-slate-700">{r.label}</span>
            <span className="text-slate-900 font-medium">
              {r.count}
              <span className="text-xs text-slate-400 ml-1">
                ({r.percent}%)
              </span>
            </span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full mt-1">
            <div className={`h-1.5 rounded-full ${tone}`}
                 style={{ width: `${Math.min(r.percent, 100)}%` }} />
          </div>
        </div>
      ))}
      {rows.length === 0 && (
        <p className="text-sm text-slate-400">Ma'lumot yo'q.</p>
      )}
    </div>
  );

  return (
    <div>
      <div className="grid md:grid-cols-3 gap-4 mb-4">
        <Dist title={`Fanlar bo'yicha o'quvchilar (${d.active_total})`}
              rows={d.subjects} tone="bg-emerald-500" />
        <Dist title="Darajalar bo'yicha o'quvchilar"
              rows={d.levels} tone="bg-blue-500" />
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            O'quvchi soni bo'yicha top ustozlar
          </p>
          {d.top_teachers.map((t: Any, i: number) => (
            <div key={i}
                 className="flex justify-between text-sm py-1.5 border-b border-slate-50">
              <span className="text-slate-700">
                <span className="text-slate-400 mr-2">{i + 1}</span>
                {t.name}
              </span>
              <span className="font-medium text-slate-900">
                {t.students} nafar
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Akademik voronka — Step 1dan natijagacha
          </p>
          {d.funnel.map((f: Any, i: number) => (
            <div key={i} className="mb-2.5">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-700">{f.stage}</span>
                <span className="font-medium text-slate-900">
                  {f.count}
                  <span className="text-xs text-slate-400 ml-1">
                    ({f.percent}%)
                  </span>
                </span>
              </div>
              <div className="h-5 bg-slate-100 rounded">
                <div
                  className={`h-5 rounded text-[10px] text-white flex items-center px-2 ${
                    i === 0 ? "bg-slate-700"
                    : i === 4 ? "bg-emerald-600" : "bg-brand-600"}`}
                  style={{ width: `${Math.max(f.percent, 4)}%` }}
                >
                  {f.percent}%
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-sm font-medium text-slate-700 mb-1 flex items-center gap-1.5">
            <TrendingDown size={14} className="text-red-500" />
            Qaysi darajada ketish ko'p ({d.left_total} ta ketgan)
          </p>
          {d.churn_worst && (
            <p className="text-xs text-red-600 mb-2">
              Eng ko'p ketish: {d.churn_worst.label} —{" "}
              {d.churn_worst.count} ta ({d.churn_worst.percent}%)
            </p>
          )}
          {d.churn.map((r: Any, i: number) => (
            <div key={r.level} className="mb-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-700">{r.label}</span>
                <span className={`font-medium ${
                  i === 0 ? "text-red-600" : "text-slate-900"}`}>
                  {r.count}
                  <span className="text-xs text-slate-400 ml-1">
                    ({r.percent}%)
                  </span>
                </span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full mt-1">
                <div className={`h-1.5 rounded-full ${
                  i === 0 ? "bg-red-500" : "bg-slate-400"}`}
                     style={{ width: `${Math.min(r.percent, 100)}%` }} />
              </div>
            </div>
          ))}
          {d.churn.length === 0 && (
            <p className="text-sm text-slate-400">Ketganlar yo'q.</p>
          )}
        </div>
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}
