import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowDownLeft, ArrowUpRight, ChevronRight, Percent } from "lucide-react";
import { formatDate } from "../../lib/format";
import { api } from "../../lib/api";
import { fmtNum } from "../../lib/studentApi";

/**
 * JONY STUDENT — TO'LOVLAR.
 *
 * 2026-08-21: "Tolovlar.png" dizayni bo'yicha to'q temada qayta
 * terildi. Manba o'zgarmadi — /api/student/payments.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

export default function StudentPayments() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [filt, setFilt] = useState<"all" | "pay" | "charge">("all");

  useEffect(() => {
    api
      .get<Any>("/student/payments")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const all: Any[] = d?.rows || [];
  const rows = all.filter((r) => {
    if (filt === "pay") return Number(r.amount) > 0 && r.kind !== "discount";
    if (filt === "charge") return Number(r.amount) < 0;
    return true;
  });
  const bal = d?.balance ?? 0;
  const card = { background: "#111C4B", borderColor: "#223070" };

  // Sana bo'yicha guruhlaymiz (dizayndagidek "17-avgust" sarlavhalari)
  const groups: [string, Any[]][] = [];
  for (const r of rows) {
    const label = r.date ? formatDate(r.date) : "Sanasiz";
    const g = groups.find((x) => x[0] === label);
    if (g) g[1].push(r); else groups.push([label, [r]]);
  }

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5">
        <Link to="/student/profile"
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}>
          <ArrowLeft size={18} />
        </Link>
        <span className="text-[15px] font-semibold text-brand-300">Profil</span>
        <h1 className="text-[26px] font-extrabold text-white flex-1 text-center pr-16">
          To'lovlar
        </h1>
      </div>

      {/* ------------------------------------------ hamyon kartasi */}
      <div className="rounded-3xl p-5 mt-4 flex items-center gap-4"
           style={{ background:
             "linear-gradient(115deg,#1B3FA8 0%,#2D4FD0 55%,#7B5CF0 100%)" }}>
        <img src="/jsicons/shop-wallet.png" alt=""
             className="w-[76px] h-[76px] shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-bold text-white/80 tracking-wide">
            JONY STUDENT APP
          </p>
          <p className="text-[34px] font-extrabold text-white leading-tight">
            {bal > 0 ? "+" : ""}{fmtNum(bal)}{" "}
            <span className="text-[17px] font-bold">so'm</span>
          </p>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold mt-1 ${
            bal < 0 ? "bg-red-500/25 text-red-200"
                    : "bg-emerald-500/25 text-emerald-200"}`}>
            {bal < 0 ? "✕ Qarzdorlik bor" : "✓ Balans musbat"}
          </span>
        </div>
      </div>

      {/* ---------------------------------------------- filtrlar */}
      <div className="flex gap-2 mt-4">
        {([["all", "Barchasi"], ["pay", "To'lov"],
           ["charge", "Hisob"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setFilt(k)}
            className={`flex-1 py-2.5 rounded-full text-sm font-bold transition ${
              filt === k ? "bg-brand-600 text-white" : "text-slate-300 border"}`}
            style={filt === k ? undefined : card}>
            {l}
          </button>
        ))}
      </div>

      <h2 className="text-[22px] font-extrabold text-white mt-5">
        Oxirgi operatsiyalar
      </h2>

      {err && <p className="text-sm text-red-400 mt-3">{err}</p>}
      {d && rows.length === 0 && (
        <div className="rounded-2xl border p-8 text-center mt-3" style={card}>
          <p className="text-sm text-slate-400">Hozircha yozuv yo'q</p>
        </div>
      )}

      {groups.map(([label, list]) => (
        <div key={label}>
          <p className="text-[14px] font-bold text-slate-400 mt-4 mb-2">
            {label}
          </p>
          <div className="bg-white rounded-3xl divide-y divide-slate-100 overflow-hidden">
            {list.map((r: Any) => {
              const plus = Number(r.amount) > 0;
              const isDisc = r.kind === "discount";
              return (
                <div key={r.id} className="p-3.5 flex items-center gap-3">
                  <span className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 ${
                    isDisc ? "bg-violet-500"
                      : plus ? "bg-emerald-500" : "bg-red-500"}`}>
                    {isDisc ? <Percent size={18} className="text-white" />
                      : plus ? <ArrowDownLeft size={18} className="text-white" />
                      : <ArrowUpRight size={18} className="text-white" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[16px] font-extrabold text-slate-900">
                      {r.kind_label}
                    </p>
                    <p className="text-[12px] text-slate-400 mt-0.5 truncate">
                      {r.note || (plus ? "Qabul qilindi" : "")}
                    </p>
                  </div>
                  <b className={`text-[16px] shrink-0 ${
                    plus ? "text-emerald-600" : "text-red-500"}`}>
                    {plus ? "+" : "−"}{fmtNum(Math.abs(r.amount))} so'm
                  </b>
                  <ChevronRight size={16} className="text-slate-300 shrink-0" />
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <div className="rounded-2xl border p-4 mt-4 flex items-center gap-3"
           style={card}>
        <img src="/jsicons/auth-protected.png" alt="" className="w-11 h-11" />
        <p className="text-[14px] text-slate-300">
          <b className="text-white">Hisob va to'lovlar</b><br />
          avtomatik solishtiriladi.
        </p>
      </div>
    </div>
  );
}
