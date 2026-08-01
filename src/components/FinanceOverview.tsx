import { useEffect, useState } from "react";
import { X, Info } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** Moliyaviy umumiy ko'rinish — asoschi va moliya direktori uchun. */

const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");

const TONE: Record<string, string> = {
  green: "border-emerald-200 bg-emerald-50/40",
  amber: "border-amber-200 bg-amber-50/40",
  red: "border-red-200 bg-red-50/40",
};
const DOT: Record<string, string> = {
  green: "bg-emerald-500", amber: "bg-amber-500", red: "bg-red-500",
};

export function FinanceOverviewTab() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<Any>(null);
  useEffect(() => {
    api.get<Any>("/finance/overview").then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
        {d.cards.map((c: Any) => (
          <button
            key={c.key}
            onClick={() => setOpen(c)}
            className={`text-left rounded-xl border p-3.5 transition hover:shadow-sm ${TONE[c.state]}`}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className={`w-2 h-2 rounded-full ${DOT[c.state]}`} />
              <p className="text-xs font-medium text-slate-600">
                {c.label}
              </p>
            </div>
            <p className="text-lg font-semibold text-slate-900">
              {c.value !== null ? fmt(c.value) : "—"}
              <span className="text-xs font-normal text-slate-400 ml-1">
                {c.unit}
              </span>
            </p>
            <p className="text-[11px] text-slate-400 mb-1">{c.sub}</p>
            {c.plan ? (
              <p className="text-[11px] text-slate-500">
                Reja: {fmt(c.plan)} ·{" "}
                <span className={
                  c.plan_pct >= 100 ? "text-emerald-600 font-medium"
                  : c.plan_pct >= 80 ? "text-amber-600" : "text-red-600"}>
                  {c.plan_pct}%
                </span>
              </p>
            ) : (
              <p className="text-[11px] text-slate-400">Reja: —</p>
            )}
            {c.diff !== null && (
              <p className={`text-[11px] ${
                c.diff >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                {c.diff >= 0 ? "+" : ""}{fmt(c.diff)} o'tgan oyga
              </p>
            )}
          </button>
        ))}
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {open && (
        <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
             onClick={() => setOpen(null)}>
          <div className="bg-white rounded-xl w-full max-w-md p-5"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-base font-semibold text-slate-900">
                {open.label}
              </h3>
              <button onClick={() => setOpen(null)}
                      className="text-slate-400">
                <X size={18} />
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-3">{open.sub}</p>
            <p className="text-2xl font-semibold text-slate-900 mb-3">
              {open.value !== null ? fmt(open.value) : "—"}{" "}
              <span className="text-sm font-normal text-slate-400">
                {open.unit}
              </span>
            </p>
            <div className="divide-y divide-slate-100 border-t border-slate-100">
              {open.plan && (
                <div className="flex justify-between py-2 text-sm">
                  <span className="text-slate-500">Oylik reja</span>
                  <span className="text-slate-800">
                    {fmt(open.plan)} ({open.plan_pct}%)
                  </span>
                </div>
              )}
              {open.prev !== null && open.prev !== undefined && (
                <div className="flex justify-between py-2 text-sm">
                  <span className="text-slate-500">O'tgan oy</span>
                  <span className="text-slate-800">{fmt(open.prev)}</span>
                </div>
              )}
              {open.details.map((r: Any, i: number) => (
                <div key={i} className="flex justify-between py-2 text-sm">
                  <span className="text-slate-500">{r.label}</span>
                  <span className={r.value < 0 ? "text-red-600"
                                   : "text-slate-800"}>
                    {fmt(r.value)} {r.unit || ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
