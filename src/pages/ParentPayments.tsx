import { useOutletContext } from "react-router-dom";
import { formatDate } from "../lib/format";
import { Wallet } from "lucide-react";
import { ParentPageHeader } from "../components/ParentPageHeader";
import type { ParentCtx } from "./Parent";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** OTA-ONA — TO'LOVLAR TARIXI (alohida sahifa, 2026-08-09). */
export default function ParentPayments() {
  const { d, fmt } = useOutletContext<ParentCtx>();

  return (
    <>
      <ParentPageHeader title="To'lovlar tarixi" icon={<Wallet size={18} />} />

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Joriy balans</p>
          <p
            className={`text-2xl font-semibold ${
              d.balance < 0 ? "text-red-600" : "text-emerald-600"
            }`}
          >
            {fmt(d.balance)} so'm
          </p>
          {d.balance < 0 && (
            <p className="text-xs text-slate-500 mt-1">
              To'lov qilishingizni so'raymiz. Savol bo'lsa
              administratorga murojaat qiling.
            </p>
          )}
        </div>

        {/* Chegirma (2026-08-12): sabab va muddat ota-onaga ham ko'rinadi,
            yashirin (individual) chegirmalar serverdan kelmaydi */}
        {((d as any).discounts || []).length > 0 && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
            {((d as any).discounts || []).map((ds: Any, i: number) => (
              <div key={i} className={i > 0 ? "mt-2 pt-2 border-t border-emerald-100" : ""}>
                <p className="text-sm font-semibold text-emerald-800">
                  Chegirma:{" "}
                  {ds.percent
                    ? `${ds.percent}%`
                    : `${fmt(ds.amount || 0)} so'm`}
                </p>
                <p className="text-xs text-emerald-700 mt-0.5">{ds.reason}</p>
                <p className="text-[11px] text-emerald-600 mt-0.5">
                  {ds.until
                    ? `${formatDate(ds.until)} gacha`
                    : "Muddatsiz"}
                </p>
              </div>
            ))}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            Harakatlar tarixi
          </p>
          {(!d.payments || d.payments.length === 0) && (
            <p className="text-sm text-slate-400 text-center py-6">
              Hali to'lov yozuvi yo'q.
            </p>
          )}
          <div className="space-y-3">
            {d.payments?.map((p: Any, i: number) => (
              <div
                key={i}
                className="flex items-start justify-between gap-3 text-sm"
              >
                <div className="min-w-0">
                  <p className="text-slate-700">
                    {p.kind}
                    {p.method ? ` · ${p.method}` : ""}
                  </p>
                  <p className="text-[11px] text-slate-400 truncate">
                    {(p.date || "").slice(0, 10)}
                    {p.note ? ` · ${p.note}` : ""}
                  </p>
                </div>
                <span
                  className={`font-medium shrink-0 ${
                    p.amount < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {p.amount > 0 ? "+" : ""}
                  {fmt(p.amount)} so'm
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
