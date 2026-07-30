import { useEffect, useState } from "react";
import { UserMinus, AlertTriangle, Info } from "lucide-react";
import { api, type ChurnReport as Data } from "../lib/api";
import { BranchPicker, branchParam } from "../components/BranchPicker";

/**
 * Churn — kim, qayerdan va NEGA ketyapti.
 * Sababsiz raqam hech narsani o'zgartirmaydi: "10 kishi ketdi" emas,
 * "10 kishi ustozdan norozi bo'lib ketdi" degani qaror keltiradi.
 */
export function ChurnReport() {
  const [data, setData] = useState<Data | null>(null);
  const [months, setMonths] = useState(12);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [tab, setTab] = useState<"teacher" | "group">("teacher");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<Data>(`/analytics/churn?months=${months}${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [months, branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const rows = tab === "teacher" ? data.by_teacher : data.by_group;
  const maxReason = Math.max(...data.reasons.map((r) => r.count), 1);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1">
          {[3, 6, 12].map((m) => (
            <button
              key={m}
              onClick={() => setMonths(m)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                months === m
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {m} oy
            </button>
          ))}
        </div>
        <BranchPicker value={branchId} onChange={setBranchId} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="Ketganlar" value={String(data.left)} tone="bad" />
        <Stat label="Ketish foizi" value={`${data.churn}%`} tone="bad" />
        <Stat
          label="Bizga bog'liq"
          value={String(data.controllable)}
          hint={`${data.controllable_percent}% — buni kamaytirish mumkin`}
          tone="amber"
        />
        <Stat
          label="Sababi noma'lum"
          value={String(data.unknown)}
          hint={data.unknown > 0 ? "sabab yozilmagan" : "hammasi yozilgan"}
          tone={data.unknown > 0 ? "amber" : "good"}
        />
      </div>

      {/* --- Sabablar --- */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <UserMinus size={15} className="text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            Nega ketishyapti
          </p>
        </div>
        {data.reasons.length === 0 ? (
          <p className="text-sm text-slate-400 py-3">
            Bu davrda hech kim ketmagan.
          </p>
        ) : (
          <div className="space-y-2">
            {data.reasons.map((r) => (
              <div key={r.key} className="flex items-center gap-3">
                <span className="text-sm text-slate-700 w-44 shrink-0">
                  {r.label}
                  {r.controllable && (
                    <span
                      className="ml-1.5 text-xs text-amber-600"
                      title="Bizga bog'liq — kamaytirish mumkin"
                    >
                      ●
                    </span>
                  )}
                </span>
                <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      r.controllable ? "bg-amber-500" : "bg-slate-400"
                    }`}
                    style={{ width: `${(r.count / maxReason) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-slate-700 w-8 text-right">
                  {r.count}
                </span>
              </div>
            ))}
          </div>
        )}
        <p className="text-xs text-slate-400 mt-3 flex items-start gap-1.5">
          <Info size={11} className="mt-0.5 shrink-0" />
          {data.hint}
        </p>
      </div>

      {/* --- Kesim --- */}
      <div className="flex gap-1 mb-3">
        {[
          { k: "teacher", l: "Ustozlar bo'yicha" },
          { k: "group", l: "Guruhlar bo'yicha" },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setTab(t.k as "teacher" | "group")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === t.k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {t.l}
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Ma'lumot yo'q.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">
                  {tab === "teacher" ? "Ustoz" : "Guruh"}
                </th>
                <th className="text-right w-24">Hozir bor</th>
                <th className="text-right w-20">Ketdi</th>
                <th className="text-right w-24">Ketish %</th>
                <th className="text-left">Asosiy sabab</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={String(r.key)} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">{r.label}</td>
                  <td className="text-right text-slate-600">{r.active}</td>
                  <td className="text-right text-slate-600">{r.left}</td>
                  <td
                    className={`text-right font-medium ${
                      r.churn >= 30
                        ? "text-red-600"
                        : r.churn >= 15
                          ? "text-amber-600"
                          : "text-slate-600"
                    }`}
                  >
                    {r.churn}%
                  </td>
                  <td className="text-slate-600">
                    {r.top_reason_label ? (
                      <span className="flex items-center gap-1.5">
                        {r.churn >= 30 && (
                          <AlertTriangle size={12} className="text-red-500" />
                        )}
                        {r.top_reason_label}
                        {r.reasons.length > 1 && (
                          <span className="text-xs text-slate-400">
                            +{r.reasons.length - 1} boshqa
                          </span>
                        )}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint?: string;
  tone: "bad" | "amber" | "good";
}) {
  const cls = {
    bad: "bg-red-50 border-red-200 text-red-800",
    amber: "bg-amber-50 border-amber-200 text-amber-800",
    good: "bg-emerald-50 border-emerald-200 text-emerald-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}
