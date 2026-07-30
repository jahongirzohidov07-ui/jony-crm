import { useEffect, useState } from "react";
import { Clock, Wallet, TrendingUp, Info } from "lucide-react";
import { api, type LtvFull } from "../lib/api";
import { formatSom } from "../lib/format";
import { BranchPicker, branchParam } from "../components/BranchPicker";

/**
 * LTV — mijoz qancha vaqt qoladi va qancha pul keltiradi.
 *
 * Ikki xil LTV bor va ular chalkashmasligi kerak:
 *   VAQT LTV - o'quvchi o'rtacha necha oy qoladi
 *   PUL LTV  - shu vaqt ichida qancha to'laydi va qancha SOF FOYDA
 *              qoldiradi
 */
export function LtvFullReport() {
  const [data, setData] = useState<LtvFull | null>(null);
  const [dim, setDim] = useState("overall");
  const [branchId, setBranchId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<LtvFull>(`/analytics/ltv?dimension=${dim}${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [dim, branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const o = data.overall;
  const maxMonths = Math.max(...data.rows.map((r) => r.avg_months), 1);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-1.5 mb-4">
        {data.dimensions.map((d) => (
          <button
            key={d.key}
            onClick={() => setDim(d.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              dim === d.key
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {d.label}
          </button>
        ))}
        <BranchPicker value={branchId} onChange={setBranchId} />
      </div>

      {/* --- Umumiy --- */}
      {o && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
          <Box
            icon={Clock}
            label="Vaqt LTV"
            value={`${o.avg_months} oy`}
            hint="o'quvchi o'rtacha shuncha qoladi"
            tone="brand"
          />
          <Box
            icon={Wallet}
            label="Pul LTV"
            value={formatSom(o.avg_revenue)}
            hint="bitta o'quvchi shuncha to'laydi"
            tone="plain"
          />
          <Box
            icon={TrendingUp}
            label="Sof foyda LTV"
            value={formatSom(o.avg_profit)}
            hint={`rentabellik ${o.margin}%`}
            tone={o.avg_profit > 0 ? "good" : "bad"}
          />
          <Box
            label="Bir oyga xarajat"
            value={formatSom(o.overhead_per_month)}
            hint="bitta o'quvchiga to'g'ri keladi"
            tone="plain"
          />
        </div>
      )}

      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Ma'lumot yo'q.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">{data.dimension_label}</th>
                <th className="text-right w-20">O'quvchi</th>
                <th className="w-40">Qancha qoladi</th>
                <th className="text-right w-24">Ketganlar</th>
                <th className="text-right w-28">Pul LTV</th>
                <th className="text-right w-28">Sof foyda</th>
                <th className="text-right w-24">Oyiga</th>
                <th className="text-right w-20">Ketish</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.key} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">{r.label}</td>
                  <td className="text-right text-slate-600">
                    {r.students}
                    {r.active !== r.students && (
                      <span className="text-slate-400">
                        {" "}
                        ({r.active} faol)
                      </span>
                    )}
                  </td>
                  <td className="px-2">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-brand-400"
                          style={{
                            width: `${(r.avg_months / maxMonths) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-slate-700 w-12 text-right">
                        {r.avg_months} oy
                      </span>
                    </div>
                  </td>
                  <td className="text-right text-slate-500 text-xs">
                    {r.finished_avg_months !== null &&
                    r.finished_avg_months !== undefined
                      ? `${r.finished_avg_months} oy`
                      : "—"}
                  </td>
                  <td className="text-right text-slate-700">
                    {formatSom(r.avg_revenue)}
                  </td>
                  <td
                    className={`text-right font-medium ${
                      r.avg_profit > 0 ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    {formatSom(r.avg_profit)}
                  </td>
                  <td className="text-right text-slate-500">
                    {formatSom(r.revenue_per_month)}
                  </td>
                  <td
                    className={`text-right pr-4 ${
                      r.churn >= 30
                        ? "text-red-600 font-medium"
                        : "text-slate-500"
                    }`}
                  >
                    {r.churn}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-start gap-1.5 mt-3">
        <Info size={13} className="text-slate-400 mt-0.5 shrink-0" />
        <p className="text-xs text-slate-500">
          {data.hint} "Ketganlar" ustuni — faqat ketib bo'lganlar bo'yicha
          o'rtacha; bu haqiqiy umr, hali o'qiyotganlar uni pasaytirmaydi.
        </p>
      </div>
    </div>
  );
}

function Box({
  icon: Icon,
  label,
  value,
  hint,
  tone,
}: {
  icon?: React.ElementType;
  label: string;
  value: string;
  hint?: string;
  tone: "plain" | "brand" | "good" | "bad";
}) {
  const cls = {
    plain: "bg-white border-slate-200 text-slate-900",
    brand: "bg-brand-50 border-brand-200 text-brand-800",
    good: "bg-emerald-50 border-emerald-200 text-emerald-800",
    bad: "bg-red-50 border-red-200 text-red-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <div className="flex items-center gap-1.5 mb-1">
        {Icon && <Icon size={13} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className="text-lg font-semibold">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}
