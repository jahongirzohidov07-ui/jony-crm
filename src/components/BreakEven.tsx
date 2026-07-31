import { useEffect, useState } from "react";
import { Info } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * Zararsizlik nuqtasi — Moliya bo'limi.
 * Yashil — kirim, sariq — o'zgarmas xarajat, qizil — umumiy xarajat.
 * Kesishgan joy — markaz o'zini oqlaydigan o'quvchilar soni.
 */

const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");
const mln = (n: number) =>
  n >= 1000000 ? `${(n / 1000000).toFixed(0)} mln` : fmt(n);

function Chart({ d }: { d: Any }) {
  const W = 720, H = 380, L = 70, R = 20, T = 20, B = 40;
  const pts = d.points as Any[];
  const nMax = pts[pts.length - 1].n || 1;
  const yMax = Math.max(...pts.map((p) => Math.max(p.revenue,
    p.total_cost)), 1) * 1.1;
  const x = (n: number) => L + (n / nMax) * (W - L - R);
  const y = (v: number) => T + (1 - v / yMax) * (H - T - B);
  const line = (key: string) =>
    pts.map((p, i) => `${i ? "L" : "M"}${x(p.n).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
  const ticksY = [0, 0.25, 0.5, 0.75, 1].map((f) => yMax * f);
  const ticksX = pts.filter((_, i) => i % Math.ceil(pts.length / 10) === 0);
  const be = d.breakeven_students;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
      {ticksY.map((v, i) => (
        <g key={i}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)}
                stroke="#e2e8f0" strokeWidth={1} />
          <text x={L - 6} y={y(v) + 3} textAnchor="end"
                fontSize={10} fill="#94a3b8">
            {mln(v)}
          </text>
        </g>
      ))}
      {ticksX.map((p, i) => (
        <text key={i} x={x(p.n)} y={H - B + 14} textAnchor="middle"
              fontSize={10} fill="#94a3b8">
          {p.n}
        </text>
      ))}
      <text x={(W + L) / 2} y={H - 6} textAnchor="middle" fontSize={10}
            fill="#64748b">
        O'quvchilar soni
      </text>
      {/* O'zgarmas — sariq tekis chiziq */}
      <line x1={L} x2={W - R} y1={y(d.fixed)} y2={y(d.fixed)}
            stroke="#f59e0b" strokeWidth={2.5} />
      {/* Umumiy xarajat — qizil */}
      <path d={line("total_cost")} fill="none" stroke="#dc2626"
            strokeWidth={2.5} />
      {/* Kirim — yashil */}
      <path d={line("revenue")} fill="none" stroke="#10b981"
            strokeWidth={2.5} />
      {/* Zararsizlik nuqtasi */}
      {be && be <= nMax && (
        <g>
          <line x1={x(be)} x2={x(be)} y1={T} y2={H - B}
                stroke="#475569" strokeWidth={1.5} strokeDasharray="4 4" />
          <circle cx={x(be)} cy={y(d.price_per_student * be)} r={5}
                  fill="#0f172a" />
          <text x={x(be)} y={T + 12} textAnchor="middle" fontSize={11}
                fontWeight={600} fill="#0f172a">
            {be} o'quvchi
          </text>
        </g>
      )}
      {/* Hozirgi holat */}
      {d.students > 0 && d.students <= nMax && (
        <line x1={x(d.students)} x2={x(d.students)} y1={T} y2={H - B}
              stroke="#2563eb" strokeWidth={1.5} strokeDasharray="2 3" />
      )}
    </svg>
  );
}

export function BreakEvenTab({ branchId }: { branchId?: number | null }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    const q = branchId ? `?branch_id=${branchId}` : "";
    api
      .get<Any>(`/finance/break-even${q}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [branchId]);

  if (err)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs text-slate-500">O'zgarmas xarajat</p>
          <p className="text-base font-semibold text-amber-600">
            {fmt(d.fixed)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs text-slate-500">
            O'zgaruvchan (1 o'quvchiga)
          </p>
          <p className="text-base font-semibold text-red-600">
            {fmt(d.variable_per_student)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs text-slate-500">Kirim (1 o'quvchidan)</p>
          <p className="text-base font-semibold text-emerald-600">
            {fmt(d.price_per_student)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs text-slate-500">Zararsizlik nuqtasi</p>
          <p className="text-base font-semibold text-slate-900">
            {d.breakeven_students !== null
              ? `${d.breakeven_students} o'quvchi`
              : "—"}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs text-slate-500">
            Hozir: {d.students} o'quvchi
          </p>
          <p className={`text-base font-semibold ${
            d.safety === null ? "text-slate-400"
            : d.safety >= 0 ? "text-emerald-600" : "text-red-600"}`}>
            {d.safety !== null
              ? `${d.safety > 0 ? "+" : ""}${d.safety}% zaxira`
              : "—"}
          </p>
        </div>
      </div>

      {d.unit_margin <= 0 && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
          Diqqat: bir o'quvchiga o'zgaruvchan xarajat undan keladigan
          kirimdan katta — bu holatda o'quvchi soni oshgani bilan zarar
          ham oshadi. Narx yoki xarajatlarni ko'rib chiqish kerak.
        </p>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-1">
        <p className="text-sm font-semibold text-slate-800 text-center mb-2">
          Zararsizlik nuqtasi — {d.period}
        </p>
        <Chart d={d} />
        <div className="flex flex-wrap justify-center gap-4 text-xs text-slate-600 mt-1">
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-emerald-500 inline-block" />
            Kirim
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-amber-500 inline-block" />
            O'zgarmas xarajatlar
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-red-600 inline-block" />
            Umumiy xarajatlar
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 bg-blue-600 inline-block" />
            Hozirgi o'quvchilar soni
          </span>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden mt-3">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-left px-4 py-2 font-medium">
                Xarajat turi
              </th>
              <th className="text-left px-3 py-2 font-medium">Tasnif</th>
              <th className="text-right px-4 py-2 font-medium">
                Shu oy summasi
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.categories.map((c: Any) => (
              <tr key={c.category}>
                <td className="px-4 py-2 text-slate-800">{c.label}</td>
                <td className="px-3 py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    c.fixed
                      ? "bg-amber-50 text-amber-700"
                      : "bg-red-50 text-red-600"}`}>
                    {c.fixed ? "o'zgarmas" : "o'zgaruvchan"}
                  </span>
                </td>
                <td className="px-4 py-2 text-right text-slate-700">
                  {fmt(c.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.categories.length === 0 && (
          <p className="text-sm text-slate-400 py-6 text-center">
            Bu oyda hali xarajat kiritilmagan.
          </p>
        )}
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}
