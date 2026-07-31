import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardList, AlertTriangle } from "lucide-react";
import { api, type MyDashboard } from "../lib/api";
import { formatSom } from "../lib/format";
import { TeacherDash } from "./TeacherDash";

const TONE: Record<string, string> = {
  plain: "bg-white border-slate-200 text-slate-900",
  brand: "bg-brand-50 border-brand-200 text-brand-800",
  good: "bg-emerald-50 border-emerald-200 text-emerald-800",
  bad: "bg-red-50 border-red-200 text-red-800",
  amber: "bg-amber-50 border-amber-200 text-amber-800",
};

/** Pul ko'rinadigan qiymatlar - so'm bilan, qolganlari oddiy son. */
function show(label: string, v: number | string): string {
  if (typeof v === "string") return v;
  const money = /pul|tushum|chiqim|foyda|balans|topgan|olgan|qarz|xarajat|narxi/i;
  if (money.test(label)) return formatSom(v);
  if (label.toLowerCase().includes("konversiya")) return `${v}%`;
  return String(v);
}

/**
 * Xodimning O'Z paneli. Har bir rol o'ziga tegishli raqamni ko'radi —
 * birovning ishi uni chalg'itmaydi.
 */
export function MyPanel({
  onLoaded,
}: {
  onLoaded?: (showGeneral: boolean) => void;
} = {}) {
  const [d, setD] = useState<MyDashboard | null>(null);

  useEffect(() => {
    api
      .get<MyDashboard>("/me/dashboard")
      .then((x) => {
        setD(x);
        onLoaded?.(x.show_general);
      })
      .catch(() => setD(null));
  }, []);

  if (!d) return null;
  if (d.cards.length === 0 && d.tasks.open === 0 && !d.teacher) return null;

  return (
    <div className="mb-6">
      {/* Ustozda ogohlantirishlar eng tepada — ular bugungi ish. */}
      {d.teacher && <TeacherDash d={d.teacher} />}

      {d.cards.length > 0 && (
        <>
          <p className="text-sm font-medium text-slate-700 mb-1">
            Mening ishim
          </p>
          <p className="text-xs text-slate-400 mb-3">
            {d.role_label}
            {d.branch ? ` · ${d.branch}` : ""}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 mb-4">
            {d.cards.map((c) => {
              const body = (
                <div
                  className={`rounded-xl border p-4 h-full ${
                    TONE[c.tone] || TONE.plain
                  } ${c.link ? "hover:border-brand-400 transition" : ""}`}
                >
                  <p className="text-xs text-slate-500 mb-1">{c.label}</p>
                  <p className="text-lg font-semibold">
                    {show(c.label, c.value)}
                  </p>
                  {c.hint && (
                    <p className="text-xs text-slate-400 mt-0.5">{c.hint}</p>
                  )}
                </div>
              );
              return c.link ? (
                <Link key={c.label} to={c.link} className="block">
                  {body}
                </Link>
              ) : (
                <div key={c.label}>{body}</div>
              );
            })}
          </div>
        </>
      )}

      {/* --- Mening vazifalarim --- */}
      {d.tasks.open > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <ClipboardList size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              Mening vazifalarim
            </p>
            {d.tasks.overdue > 0 && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                <AlertTriangle size={10} />
                {d.tasks.overdue} kechikkan
              </span>
            )}
            <div className="flex-1" />
            <Link to="/tasks" className="text-xs text-brand-600 hover:underline">
              hammasi ({d.tasks.open})
            </Link>
          </div>
          <div className="space-y-1.5">
            {d.tasks.rows.map((t) => (
              <Link
                key={t.id}
                to="/tasks"
                className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-slate-100 hover:border-brand-300 transition"
              >
                <span className="text-sm text-slate-800 truncate">
                  {t.title}
                </span>
                <span
                  className={`text-xs shrink-0 ${
                    t.overdue ? "text-red-600 font-medium" : "text-slate-400"
                  }`}
                >
                  {t.deadline
                    ? t.overdue
                      ? `${Math.abs(t.days_left ?? 0)} kun kechikdi`
                      : `${t.days_left} kun qoldi`
                    : "muddatsiz"}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
