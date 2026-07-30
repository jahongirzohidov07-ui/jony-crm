import { useEffect, useState } from "react";
import { Building2, Download } from "lucide-react";
import { api, type BranchCompare as Data } from "../lib/api";
import { formatSom } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

/** Ustunlar ta'rifi: qaysi raqam, qanday ko'rsatiladi, kattaroq yaxshimi. */
const COLS: {
  key: string;
  label: string;
  fmt: (v: number | null) => string;
  hint?: string;
}[] = [
  { key: "income", label: "Tushum", fmt: (v) => formatSom(v ?? 0) },
  { key: "expense", label: "Chiqim", fmt: (v) => formatSom(v ?? 0) },
  { key: "profit", label: "Foyda", fmt: (v) => formatSom(v ?? 0) },
  { key: "margin", label: "Rentabellik", fmt: (v) => `${v ?? 0}%` },
  { key: "active", label: "O'quvchi", fmt: (v) => String(v ?? 0) },
  {
    key: "fill",
    label: "Guruh to'lishi",
    fmt: (v) => (v === null ? "—" : `${v}%`),
  },
  {
    key: "arpu",
    label: "Bir o'quvchidan",
    fmt: (v) => formatSom(v ?? 0),
    hint: "o'rtacha tushum",
  },
  { key: "leads", label: "Lid", fmt: (v) => String(v ?? 0) },
  { key: "conversion", label: "Konversiya", fmt: (v) => `${v ?? 0}%` },
  { key: "new_clients", label: "Yangi mijoz", fmt: (v) => String(v ?? 0) },
  { key: "left", label: "Ketgan", fmt: (v) => String(v ?? 0) },
  { key: "churn", label: "Ketish %", fmt: (v) => `${v ?? 0}%` },
  { key: "debt", label: "Qarzdorlik", fmt: (v) => formatSom(v ?? 0) },
];

/**
 * Filiallarni yonma-yon solishtirish. Har bir ustunda eng yaxshi filial
 * yashil, eng yomoni qizil bo'ladi — shunda ko'z bilan darrov ko'rinadi.
 */
export function BranchCompare({ months = 1 }: { months?: number }) {
  const [data, setData] = useState<Data | null>(null);
  const [m, setM] = useState(months);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<Data>(`/ceo/branches?months=${m}`)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [m]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data || data.rows.length === 0) return null;

  const single = data.rows.length < 2;

  function tone(colKey: string, branchId: number): string {
    if (single || !data) return "";
    const h = data.highlight[colKey];
    if (!h) return "";
    if (h.best === branchId) return "text-emerald-600 font-medium";
    if (h.worst === branchId) return "text-red-600 font-medium";
    return "";
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <Building2 size={15} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">
          Filiallar solishtiruvi
        </p>
        <div className="flex-1" />
        <div className="flex gap-1">
          {[
            { v: 1, l: "1 oy" },
            { v: 3, l: "3 oy" },
            { v: 6, l: "6 oy" },
            { v: 12, l: "1 yil" },
          ].map((x) => (
            <button
              key={x.v}
              onClick={() => setM(x.v)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                m === x.v
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {x.l}
            </button>
          ))}
          <button
            onClick={() =>
              exportToExcel("filiallar", "Filiallar",
                data.rows.map((r) => {
                  const o: Record<string, string | number> = { Filial: r.branch };
                  for (const c of COLS) {
                    const v = (r as unknown as Record<string, number | null>)[c.key];
                    o[c.label] = v ?? 0;
                  }
                  return o;
                }))
            }
            className="px-2.5 py-1 rounded-lg text-xs border border-slate-200 text-slate-500 hover:border-slate-300"
            title="Excel"
          >
            <Download size={12} className="inline" />
          </button>
        </div>
      </div>
      <p className="text-xs text-slate-400 mb-3">
        {single
          ? data.period
          : `${data.period} · yashil — eng yaxshi, qizil — e'tibor talab qiladi`}
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-100">
              <th className="text-left py-2 sticky left-0 bg-white">
                Ko'rsatkich
              </th>
              {data.rows.map((r) => (
                <th key={r.branch_id} className="text-right px-3 min-w-[110px]">
                  {r.branch}
                </th>
              ))}
              {!single && <th className="text-right px-3">Jami</th>}
            </tr>
          </thead>
          <tbody>
            {COLS.map((c) => (
              <tr key={c.key} className="border-b border-slate-50">
                <td className="py-2 text-slate-600 sticky left-0 bg-white">
                  {c.label}
                  {c.hint && (
                    <span className="block text-xs text-slate-400">{c.hint}</span>
                  )}
                </td>
                {data.rows.map((r) => {
                  const v = (r as unknown as Record<string, number | null>)[c.key];
                  return (
                    <td
                      key={r.branch_id}
                      className={`text-right px-3 tabular-nums ${tone(
                        c.key,
                        r.branch_id
                      )}`}
                    >
                      {c.fmt(v)}
                    </td>
                  );
                })}
                {!single && (
                  <td className="text-right px-3 text-slate-700 font-medium tabular-nums">
                    {c.key in data.totals ? c.fmt(data.totals[c.key]) : "—"}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
