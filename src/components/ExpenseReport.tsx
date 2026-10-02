import { useEffect, useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { Download } from "lucide-react";
import { api, type ExpenseReport as Report } from "../lib/api";
import { formatSom } from "../lib/format";
import { EXPENSE_GROUPS, MONTHS, isCountable } from "../lib/expenses";
import { exportToExcel } from "../lib/exportXlsx";

/**
 * XARAJATLAR HISOBOTI (2026-10-02).
 *
 * Jahongir: "harajatlar kesimida ham nechta qaysinga qaysi oyda qancha
 * harajat ketyabdi hisobotlarda to'g'ri tushunarli animatsiyalarda
 * chartlar bilan bo'lsin".
 *
 * Manba — /reports/expenses: xarajatlar + haqiqatda berilgan ustoz
 * oyliklari (Pul oqimi bilan bir xil), tepadagi filial tanlovi bo'yicha.
 *
 * RANGLAR: guruh har doim O'Z rangida (oy yoki filtr o'zgarsa ham
 * bo'yalmaydi). Palitra rang ko'rlikka tekshirilgan (dataviz validator,
 * qo'shni juftlar CVD ΔE ≥ 9). Uchta och rang oq fonda past kontrastli —
 * shuning uchun har bir summa yonida yozuv bor va pastda jadval turadi.
 */
const GROUP_COLOR: Record<string, string> = {
  rent: "#2a78d6",
  communal: "#eb6834",
  office: "#1baf7a",
  household: "#8a5a2b",
  admin_salary: "#eda100",
  teacher_salary: "#e87ba4",
  marketing: "#008300",
  tax: "#4a3aa7",
  other: "#e34948",
};
const GROUP_ORDER = EXPENSE_GROUPS.map((g) => g.key);
const groupName = (k: string) =>
  EXPENSE_GROUPS.find((g) => g.key === k)?.label || k;

function short(n: number): string {
  const a = Math.abs(n);
  if (a >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (a >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

// Iyun va Iyul ikkalasi ham "Iyu" bo'lib qolmasin
const MONTH_SHORT = ["Yan", "Fev", "Mar", "Apr", "May", "Iyn",
  "Iyl", "Avg", "Sen", "Okt", "Noy", "Dek"];

function monthShort(period: string): string {
  const m = Number(period.slice(5, 7));
  return `${MONTH_SHORT[m - 1] ?? period} ${period.slice(2, 4)}`;
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-xl font-semibold text-slate-900 mt-1 tabular-nums">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5 truncate">{hint}</p>}
    </div>
  );
}

interface TipPayload {
  dataKey?: string | number;
  value?: number;
  payload?: Record<string, number | string>;
}

function MonthTip({ active, payload, label }: {
  active?: boolean; payload?: TipPayload[]; label?: string;
}) {
  if (!active || !payload?.length) return null;
  const rows = payload.filter((p) => (p.value ?? 0) > 0)
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  const total = rows.reduce((s, p) => s + (p.value ?? 0), 0);
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-md px-3 py-2 text-xs">
      <p className="font-medium text-slate-800 mb-1">{label}</p>
      {rows.map((p) => (
        <div key={String(p.dataKey)} className="flex items-center gap-2 py-0.5">
          <span className="w-2.5 h-2.5 rounded-sm"
                style={{ background: GROUP_COLOR[String(p.dataKey)] }} />
          <span className="text-slate-600 flex-1">{groupName(String(p.dataKey))}</span>
          <span className="tabular-nums text-slate-800">{formatSom(p.value ?? 0)}</span>
        </div>
      ))}
      <div className="flex justify-between border-t border-slate-100 mt-1 pt-1 font-medium text-slate-900">
        <span>Jami</span>
        <span className="tabular-nums">{formatSom(total)}</span>
      </div>
    </div>
  );
}

export default function ExpenseReport() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [span, setSpan] = useState<3 | 6 | 12>(6);
  const [data, setData] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  // Jadvalda bitta guruhni ajratib ko'rish (donut yoki legend bosilganda)
  const [focus, setFocus] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    api
      .get<Report>(`/reports/expenses?year=${year}&month=${month}&months=${span}`)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }, [year, month, span]);

  // Faqat shu davrda xarajati bor guruhlar — doimiy tartibda
  const present = useMemo(
    () => (data ? GROUP_ORDER.filter((g) => data.groups.some((x) => x.key === g)) : []),
    [data]);

  const chartRows = useMemo(
    () => (data?.months || []).map((m) => ({
      name: monthShort(m.period),
      ...Object.fromEntries(present.map((g) => [g, m.groups[g] || 0])),
    })),
    [data, present]);

  const years = [now.getFullYear(), now.getFullYear() - 1];
  const top = data?.groups[0];
  const cats = (data?.categories || []).filter((c) => !focus || c.group === focus);

  function exportRows() {
    if (!data) return;
    exportToExcel(`xarajatlar-${data.from}_${data.to}`, "Xarajatlar",
      data.categories.map((c) => ({
        Guruh: groupName(c.group),
        Tur: c.label,
        ...Object.fromEntries(data.periods.map((p) => [p, c.by_month[p] || 0])),
        Jami: c.total,
        "Yozuvlar soni": c.count,
        Dona: c.qty || "",
      })));
  }

  return (
    <div className="space-y-5">
      {/* Filtrlar — bitta qatorda */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5">
          {([3, 6, 12] as const).map((k) => (
            <button
              key={k}
              onClick={() => setSpan(k)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium ${
                span === k ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}
            >
              {k} oy
            </button>
          ))}
        </div>
        <select value={month} onChange={(e) => setMonth(Number(e.target.value))}
                className="px-3 py-2 rounded-lg border border-slate-200 text-sm">
          {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
        </select>
        <select value={year} onChange={(e) => setYear(Number(e.target.value))}
                className="px-3 py-2 rounded-lg border border-slate-200 text-sm">
          {years.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        <span className="text-sm text-slate-500">gacha</span>
        <div className="flex-1" />
        <button
          onClick={exportRows}
          disabled={!data}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <Download size={14} /> Excel
        </button>
      </div>

      {err && <p className="text-sm text-red-600">{err}</p>}
      {loading && !data && <p className="text-sm text-slate-400">Yuklanmoqda...</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Jami xarajat" value={formatSom(data.total)}
                  hint={`${monthShort(data.from)} — ${monthShort(data.to)}`} />
            <Stat label="Oyiga o'rtacha" value={formatSom(data.avg_month)} />
            <Stat label="Eng katta yo'nalish"
                  value={top ? groupName(top.key) : "—"}
                  hint={top ? `${formatSom(top.total)} · ${top.share}%` : undefined} />
            <Stat label="Yozuvlar soni" value={String(data.count)}
                  hint={`${data.categories.length} xil tur`} />
          </div>

          {data.total === 0 ? (
            <p className="text-sm text-slate-400 bg-white rounded-xl border border-slate-200 p-8 text-center">
              Bu davrda xarajat kiritilmagan
            </p>
          ) : (
            <div className="grid lg:grid-cols-3 gap-5">
              {/* Oylar kesimida — guruhlar ustma-ust */}
              <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-sm font-medium text-slate-700">Har oy qancha xarajat</p>
                <p className="text-xs text-slate-400 mb-3">
                  Yo'nalishlar kesimida · ustun ustiga olib boring
                </p>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartRows} barCategoryGap="28%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#eef0f3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }}
                           axisLine={false} tickLine={false} />
                    <YAxis tickFormatter={(v) => short(Number(v))} width={72}
                           tick={{ fontSize: 12, fill: "#64748b" }}
                           axisLine={false} tickLine={false} />
                    <Tooltip content={<MonthTip />} cursor={{ fill: "#f1f5f9" }} />
                    {present.map((g, i) => (
                      <Bar
                        key={g}
                        dataKey={g}
                        stackId="x"
                        fill={GROUP_COLOR[g]}
                        stroke="#ffffff"
                        strokeWidth={2}
                        radius={i === present.length - 1 ? [4, 4, 0, 0] : 0}
                        fillOpacity={focus && focus !== g ? 0.25 : 1}
                        animationDuration={900}
                        animationBegin={i * 90}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
                {/* Legend — bosilsa shu yo'nalish ajratiladi */}
                <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-2">
                  {present.map((g) => (
                    <button
                      key={g}
                      onClick={() => setFocus((f) => (f === g ? null : g))}
                      className={`flex items-center gap-1.5 text-xs ${
                        focus && focus !== g ? "opacity-40" : ""}`}
                    >
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ background: GROUP_COLOR[g] }} />
                      <span className="text-slate-600">{groupName(g)}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Ulushlar */}
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-sm font-medium text-slate-700">Pul qayerga ketyapti</p>
                <p className="text-xs text-slate-400 mb-1">Butun davr bo'yicha ulush</p>
                <ResponsiveContainer width="100%" height={190}>
                  <PieChart>
                    <Pie
                      data={data.groups}
                      dataKey="total"
                      nameKey="key"
                      innerRadius={52}
                      outerRadius={82}
                      paddingAngle={2}
                      stroke="#ffffff"
                      strokeWidth={2}
                      animationDuration={900}
                      onClick={(d: { key?: string }) =>
                        setFocus((f) => (f === d.key ? null : d.key ?? null))}
                    >
                      {data.groups.map((g) => (
                        <Cell key={g.key} fill={GROUP_COLOR[g.key] || "#94a3b8"}
                              fillOpacity={focus && focus !== g.key ? 0.25 : 1}
                              className="cursor-pointer" />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: number, k: string) => [formatSom(v), groupName(k)]} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1.5 mt-1">
                  {data.groups.map((g) => (
                    <button
                      key={g.key}
                      onClick={() => setFocus((f) => (f === g.key ? null : g.key))}
                      className={`w-full flex items-center gap-2 text-xs ${
                        focus && focus !== g.key ? "opacity-40" : ""}`}
                    >
                      <span className="w-2.5 h-2.5 rounded-sm shrink-0"
                            style={{ background: GROUP_COLOR[g.key] || "#94a3b8" }} />
                      <span className="text-slate-600 flex-1 text-left truncate">
                        {groupName(g.key)}
                      </span>
                      <span className="text-slate-400 tabular-nums">{g.share}%</span>
                      <span className="text-slate-800 tabular-nums w-24 text-right">
                        {short(g.total)}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Turlar × oylar jadvali */}
          {data.categories.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-medium text-slate-700">Turlar bo'yicha</p>
                {focus && (
                  <button onClick={() => setFocus(null)}
                          className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                    {groupName(focus)} ✕
                  </button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr className="text-xs text-slate-500">
                      <th className="text-left px-4 py-2">Tur</th>
                      {data.periods.map((p) => (
                        <th key={p} className="text-right px-3 whitespace-nowrap">{monthShort(p)}</th>
                      ))}
                      <th className="text-right px-3">Jami</th>
                      <th className="text-right px-4">Nechta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cats.map((c) => (
                      <tr key={c.key} className="border-t border-slate-100">
                        <td className="px-4 py-2">
                          <span className="inline-flex items-center gap-2">
                            <span className="w-2 h-2 rounded-sm"
                                  style={{ background: GROUP_COLOR[c.group] || "#94a3b8" }} />
                            <span className="text-slate-800">{c.label}</span>
                          </span>
                        </td>
                        {data.periods.map((p) => (
                          <td key={p} className="text-right px-3 tabular-nums text-slate-600">
                            {c.by_month[p] ? short(c.by_month[p]) : "—"}
                          </td>
                        ))}
                        <td className="text-right px-3 tabular-nums font-medium text-slate-900">
                          {formatSom(c.total)}
                        </td>
                        <td className="text-right px-4 text-slate-500 whitespace-nowrap">
                          {c.count} ta
                          {isCountable(c.key) && c.qty > 0 && (
                            <span className="text-slate-400"> · {c.qty} dona</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    <tr className="border-t border-slate-200 bg-slate-50 font-medium">
                      <td className="px-4 py-2 text-slate-800">Jami</td>
                      {data.periods.map((p) => {
                        const v = cats.reduce((s, c) => s + (c.by_month[p] || 0), 0);
                        return (
                          <td key={p} className="text-right px-3 tabular-nums text-slate-800">
                            {v ? short(v) : "—"}
                          </td>
                        );
                      })}
                      <td className="text-right px-3 tabular-nums text-slate-900">
                        {formatSom(cats.reduce((s, c) => s + c.total, 0))}
                      </td>
                      <td className="text-right px-4 text-slate-500">
                        {cats.reduce((s, c) => s + c.count, 0)} ta
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
