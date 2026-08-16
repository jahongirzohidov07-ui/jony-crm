import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowDownLeft, ArrowUpRight, Percent } from "lucide-react";
import { formatDate } from "../../lib/format";
import { api } from "../../lib/api";
import { fmtNum } from "../../lib/studentApi";

/**
 * JONY STUDENT — TO'LOVLAR (2026-08-16).
 *
 * Jahongir bosh sahifadan to'lov kartasini pastga tushirishni so'radi,
 * lekin ma'lumotning o'zi yo'qolmasligi kerak. Shuning uchun to'liq
 * tarix shu sahifada: Profil -> To'lovlar.
 *
 * Manba o'zgarmadi — /api/student/payments (payments jadvali).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

export default function StudentPayments() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/payments")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const rows: Any[] = d?.rows || [];
  const bal = d?.balance ?? 0;

  return (
    <>
      <div
        className={`text-white px-4 pt-6 pb-14 ${
          bal < 0 ? "bg-red-500" : "bg-brand-600"
        }`}
      >
        <div className="max-w-md mx-auto">
          <Link
            to="/student/profile"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Profil
          </Link>
          <h1 className="text-xl font-bold">To'lovlar</h1>
          <p className="text-3xl font-extrabold mt-3">
            {fmtNum(bal)} <span className="text-lg font-semibold">so'm</span>
          </p>
          <p className="text-sm text-white/85 mt-1">
            {bal < 0
              ? "Qarzdorlik bor — administratorga murojaat qiling"
              : "Balans musbat"}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-9 pb-8 space-y-2">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4">
            <p className="text-sm text-red-600">{err}</p>
          </div>
        )}
        {d && rows.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
            <p className="text-sm text-slate-500">Hozircha yozuv yo'q</p>
          </div>
        )}
        {rows.map((r) => {
          const plus = Number(r.amount) > 0;
          const isDisc = r.kind === "discount";
          return (
            <div
              key={r.id}
              className="bg-white rounded-xl border border-slate-200 p-3.5 flex items-center gap-3"
            >
              <span
                className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                  isDisc
                    ? "bg-violet-50 text-violet-600"
                    : plus
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-red-50 text-red-500"
                }`}
              >
                {isDisc ? (
                  <Percent size={17} />
                ) : plus ? (
                  <ArrowDownLeft size={17} />
                ) : (
                  <ArrowUpRight size={17} />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900">
                  {r.kind_label}
                </p>
                {r.note && (
                  <p className="text-xs text-slate-500 mt-0.5 truncate">
                    {r.note}
                  </p>
                )}
                {r.date && (
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {formatDate(r.date)}
                  </p>
                )}
              </div>
              <span
                className={`text-sm font-bold shrink-0 ${
                  plus ? "text-emerald-600" : "text-slate-700"
                }`}
              >
                {plus ? "+" : ""}
                {fmtNum(r.amount)}
              </span>
            </div>
          );
        })}
      </div>
    </>
  );
}
