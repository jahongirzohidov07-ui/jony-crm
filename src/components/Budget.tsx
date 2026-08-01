import { useEffect, useState } from "react";
import { Info, Pencil, X } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** Budjet: yillik/oylik/filial/bo'lim, reja-fakt, yil oxiri prognozi. */

const fmt = (n: Any) =>
  n === null || n === undefined ? "—"
    : Number(n).toLocaleString().replace(/,/g, " ");
const MONTH_N = ["Yan", "Fev", "Mar", "Apr", "May", "Iyn", "Iyl", "Avg",
  "Sen", "Okt", "Noy", "Dek"];

function pctTone(f: Any, p: Any, lower = false) {
  if (!p || f === null || f === undefined) return "text-slate-500";
  const r = (f / p) * 100;
  if (lower) return r <= 100 ? "text-emerald-600" : r <= 110
    ? "text-amber-600" : "text-red-600";
  return r >= 100 ? "text-emerald-600" : r >= 80 ? "text-amber-600"
    : "text-red-600";
}

export function BudgetTab() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [sub, setSub] = useState<"yillik" | "oylik" | "filial" | "bolim" |
    "prognoz">("yillik");
  const [month, setMonth] = useState<number | null>(null);
  const [edit, setEdit] = useState(false);

  const load = () => {
    const q = month ? `?month=${month}` : "";
    api.get<Any>(`/finance/budget${q}`).then((r) => {
      setD(r);
      if (!month) setMonth(r.monthly.month);
    }).catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, [month]);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const subs = [["yillik", "Yillik"], ["oylik", "Oylik"],
    ["filial", "Filial"], ["bolim", "Bo'lim"],
    ["prognoz", "Yil oxiri prognozi"]] as const;
  const fc = d.forecast;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1 bg-white border border-slate-200 rounded-lg p-1">
          {subs.map(([k, l]) => (
            <button key={k} onClick={() => setSub(k)}
              className={`px-3 py-1 rounded-md text-sm ${sub === k
                ? "bg-brand-600 text-white"
                : "text-slate-600 hover:bg-slate-100"}`}>
              {l}
            </button>
          ))}
        </div>
        {(sub === "oylik" || sub === "filial" || sub === "bolim") && (
          <select value={month || d.monthly.month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
            {d.months.map((m: number) => (
              <option key={m} value={m}>{MONTH_N[m - 1]}</option>
            ))}
          </select>
        )}
        <span className="text-sm text-slate-500">{d.year_label}</span>
        <div className="flex-1" />
        {d.can_edit && (
          <button onClick={() => setEdit(true)}
            className="flex items-center gap-1.5 bg-slate-900 text-white rounded-lg px-3 py-1.5 text-sm font-medium">
            <Pencil size={13} /> Budjet kiritish
          </button>
        )}
      </div>

      {sub === "yillik" && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
          <table className="w-full text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Oy</th>
                <th className="text-right px-3 py-2 font-medium">
                  Daromad rejasi</th>
                <th className="text-right px-3 py-2 font-medium">
                  Daromad fakt</th>
                <th className="text-right px-3 py-2 font-medium">
                  Xarajat rejasi</th>
                <th className="text-right px-3 py-2 font-medium">
                  Xarajat fakt</th>
                <th className="text-right px-3 py-2 font-medium">
                  Foyda rejasi</th>
                <th className="text-right px-4 py-2 font-medium">
                  Foyda fakt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.yearly.map((r: Any) => (
                <tr key={r.month}>
                  <td className="px-4 py-2 text-slate-700 capitalize">
                    {r.label}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(r.plan_income)}</td>
                  <td className={`px-3 py-2 text-right font-medium ${
                    pctTone(r.fakt_income, r.plan_income)}`}>
                    {fmt(r.fakt_income)}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(r.plan_expense)}</td>
                  <td className={`px-3 py-2 text-right font-medium ${
                    pctTone(r.fakt_expense, r.plan_expense, true)}`}>
                    {fmt(r.fakt_expense)}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(r.plan_profit)}</td>
                  <td className={`px-4 py-2 text-right font-medium ${
                    (r.fakt_profit ?? 0) >= 0 ? "text-emerald-700"
                    : "text-red-600"}`}>
                    {fmt(r.fakt_profit)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sub === "oylik" && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="flex justify-between px-4 py-3 bg-slate-50 text-sm">
            <span className="font-medium text-slate-700 capitalize">
              {d.monthly.label} — daromad
            </span>
            <span>
              Reja: {fmt(d.monthly.income_plan)} · Fakt:{" "}
              <b className={pctTone(d.monthly.income_fakt,
                d.monthly.income_plan)}>
                {fmt(d.monthly.income_fakt)}
              </b>
            </span>
          </div>
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2 font-medium">
                  Xarajat turi</th>
                <th className="text-right px-3 py-2 font-medium">Reja</th>
                <th className="text-right px-3 py-2 font-medium">Fakt</th>
                <th className="text-right px-4 py-2 font-medium">%</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.monthly.categories.map((c: Any) => (
                <tr key={c.category}>
                  <td className="px-4 py-2 text-slate-700">{c.label}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(c.plan)}</td>
                  <td className={`px-3 py-2 text-right font-medium ${
                    pctTone(c.fakt, c.plan, true)}`}>{fmt(c.fakt)}</td>
                  <td className="px-4 py-2 text-right text-slate-500">
                    {c.pct !== null ? `${c.pct}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sub === "filial" && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
          <table className="w-full text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Filial</th>
                <th className="text-right px-3 py-2 font-medium">
                  Daromad rejasi</th>
                <th className="text-right px-3 py-2 font-medium">
                  Daromad fakt</th>
                <th className="text-right px-3 py-2 font-medium">
                  Xarajat rejasi</th>
                <th className="text-right px-4 py-2 font-medium">
                  Xarajat fakt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.branches.map((b: Any) => (
                <tr key={b.branch}>
                  <td className="px-4 py-2 text-slate-700">{b.branch}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(b.plan_income)}</td>
                  <td className={`px-3 py-2 text-right font-medium ${
                    pctTone(b.fakt_income, b.plan_income)}`}>
                    {fmt(b.fakt_income)}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(b.plan_expense)}</td>
                  <td className={`px-4 py-2 text-right font-medium ${
                    pctTone(b.fakt_expense, b.plan_expense, true)}`}>
                    {fmt(b.fakt_expense)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-slate-400 px-4 py-2">
            Filial rejasi budjet kiritishda filial tanlanganda to'ladi.
          </p>
        </div>
      )}

      {sub === "bolim" && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Bo'lim</th>
                <th className="text-right px-3 py-2 font-medium">Reja</th>
                <th className="text-right px-4 py-2 font-medium">Fakt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.departments.map((r: Any) => (
                <tr key={r.department}>
                  <td className="px-4 py-2 text-slate-700">{r.label}</td>
                  <td className="px-3 py-2 text-right text-slate-500">
                    {fmt(r.plan)}</td>
                  <td className={`px-4 py-2 text-right font-medium ${
                    pctTone(r.fakt, r.plan, true)}`}>{fmt(r.fakt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sub === "prognoz" && (
        <div className="grid sm:grid-cols-3 gap-3">
          {[
            ["Daromad", fc.forecast_income, fc.budget_income, false],
            ["Xarajat", fc.forecast_expense, fc.budget_expense, true],
            ["Foyda", fc.forecast_profit, fc.budget_profit, false],
          ].map(([lbl, v, b, lower]: Any) => (
            <div key={lbl}
                 className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-1">
                Yil oxiri — {lbl}
              </p>
              <p className={`text-xl font-semibold ${
                pctTone(v, b, lower)}`}>{fmt(v)}</p>
              <p className="text-xs text-slate-400 mt-1">
                Budjet: {fmt(b)}
                {b ? ` · ${Math.round((v / b) * 100)}%` : ""}
              </p>
            </div>
          ))}
          <div className="sm:col-span-3 bg-white border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
            Shu kungacha fakt: daromad {fmt(fc.ytd_income)}, xarajat{" "}
            {fmt(fc.ytd_expense)}. Prognoz = fakt + qolgan oylar rejasi.
          </div>
        </div>
      )}

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {edit && (
        <BudgetEditor d={d} month={month || d.monthly.month}
          onClose={() => { setEdit(false); load(); }} />
      )}
    </div>
  );
}

function BudgetEditor({ d, month, onClose }: Any) {
  const [m, setM] = useState(month);
  const [income, setIncome] = useState("");
  const [vals, setVals] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // joriy qiymatlarni oylikdan olamiz
    if (m === d.monthly.month) {
      setIncome(d.monthly.income_plan ? String(d.monthly.income_plan) : "");
      const v: Record<string, string> = {};
      for (const c of d.monthly.categories)
        if (c.plan) v[c.category] = String(c.plan);
      setVals(v);
    } else {
      setIncome(""); setVals({});
    }
  }, [m]);

  const save = async () => {
    setBusy(true);
    const items: Any[] = [];
    if (income !== "" && !isNaN(Number(income)))
      items.push({ month: m, kind: "income", category: null,
        amount: Number(income) });
    for (const [c, s] of Object.entries(vals))
      if (s !== "" && !isNaN(Number(s)))
        items.push({ month: m, kind: "expense", category: c,
          amount: Number(s) });
    try {
      await api.put(`/finance/budget/${d.year}`, { items });
      onClose();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
      setBusy(false);
    }
  };

  const cats = [...d.expense_categories,
    { key: "teacher_payroll", label: "Ustozlar ish haqi" }];

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-auto p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-900">
            Budjet kiritish — {d.year_label}
          </h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="flex items-center gap-2 mb-3">
          <select value={m} onChange={(e) => setM(Number(e.target.value))}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
            {d.months.map((mm: number) => (
              <option key={mm} value={mm}>{MONTH_N[mm - 1]}</option>
            ))}
          </select>
          <input value={income}
            onChange={(e) => setIncome(e.target.value)}
            placeholder="Daromad rejasi (so'm)"
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm flex-1" />
        </div>
        <p className="text-xs font-medium text-slate-500 mb-1.5">
          Xarajat rejasi (kategoriya bo'yicha):
        </p>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {cats.map((c: Any) => (
            <label key={c.key} className="text-xs text-slate-600">
              {c.label}
              <input value={vals[c.key] || ""}
                onChange={(e) =>
                  setVals({ ...vals, [c.key]: e.target.value })}
                className="mt-0.5 w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm text-right" />
            </label>
          ))}
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600">Bekor</button>
          <button onClick={save} disabled={busy}
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40">
            Saqlash
          </button>
        </div>
      </div>
    </div>
  );
}
