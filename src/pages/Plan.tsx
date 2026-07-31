import { useEffect, useState } from "react";
import { Target, ChevronLeft, ChevronRight, Pencil, X } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * Yillik Reja / Fakt — rahbarning bosh jadvali.
 * Oy · Hafta · Kun kesimlari; reja yil boshida tuziladi (o'tgan yil
 * fakti + o'sish % taklif qilinadi), fakt avtomat to'ladi.
 */

const SEC_TONE: Record<string, string> = {
  online: "bg-sky-50 text-sky-700",
  sotuv: "bg-amber-50 text-amber-700",
  moliya: "bg-emerald-50 text-emerald-700",
};

const fmt = (v: Any, money: boolean) => {
  if (v === null || v === undefined) return "";
  const n = Number(v);
  if (money) return n.toLocaleString().replace(/,/g, " ");
  return n % 1 === 0 ? String(n) : n.toFixed(1);
};

function faktTone(plan: Any, fakt: Any) {
  if (fakt === null || fakt === undefined || plan === null ||
      plan === undefined || plan === 0)
    return "text-slate-700";
  const p = (fakt / plan) * 100;
  if (p >= 100) return "text-emerald-700 font-medium";
  if (p >= 80) return "text-amber-600";
  return "text-red-600";
}

export default function Plan() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [year, setYear] = useState<number | null>(null);
  const [gran, setGran] = useState<"month" | "week" | "day">("month");
  const [month, setMonth] = useState(9);
  const [edit, setEdit] = useState(false);

  const load = () => {
    const q = new URLSearchParams();
    if (year) q.set("year", String(year));
    q.set("granularity", gran);
    if (gran === "day") q.set("month", String(month));
    api
      .get<Any>(`/plan?${q}`)
      .then((r) => {
        setD(r);
        setYear(r.year);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, [year, gran, month]);

  if (err)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  const secOrder = Object.keys(d.sections);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Target size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Reja va Fakt
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-4">{d.hint}</p>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg px-1 py-1">
          <button
            onClick={() => setYear((y) => (y || d.year) - 1)}
            className="p-1 text-slate-400 hover:text-slate-700"
          >
            <ChevronLeft size={15} />
          </button>
          <span className="text-sm font-medium text-slate-800 px-1">
            {d.year_label}
          </span>
          <button
            onClick={() => setYear((y) => (y || d.year) + 1)}
            className="p-1 text-slate-400 hover:text-slate-700"
          >
            <ChevronRight size={15} />
          </button>
        </div>
        <div className="flex gap-1 bg-white border border-slate-200 rounded-lg p-1">
          {(["month", "week", "day"] as const).map((g) => (
            <button
              key={g}
              onClick={() => setGran(g)}
              className={`px-3 py-1 rounded-md text-sm ${
                gran === g
                  ? "bg-brand-600 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {g === "month" ? "Oy" : g === "week" ? "Hafta" : "Kun"}
            </button>
          ))}
        </div>
        {gran === "day" && (
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
          >
            {d.months.map((m: number, i: number) => (
              <option key={m} value={m}>
                {["Sentabr", "Oktabr", "Noyabr", "Dekabr", "Yanvar",
                  "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul",
                  "Avgust"][i]}
              </option>
            ))}
          </select>
        )}
        <div className="flex-1" />
        {d.can_edit && (
          <button
            onClick={() => setEdit(true)}
            className="flex items-center gap-1.5 bg-slate-900 text-white rounded-lg px-3 py-1.5 text-sm font-medium"
          >
            <Pencil size={13} /> Reja tuzish
          </button>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="text-xs whitespace-nowrap">
          <thead>
            <tr className="bg-slate-100 text-slate-600">
              <th className="sticky left-0 bg-slate-100 text-left px-3 py-2 font-medium z-10">
                Ko'rsatkich
              </th>
              <th className="px-2 py-2 font-medium" />
              {d.columns.map((c: string, i: number) => (
                <th
                  key={i}
                  className={`px-2 py-2 font-medium text-right ${
                    d.sundays.includes(i) ? "bg-red-100 text-red-500" : ""
                  }`}
                >
                  {c}
                </th>
              ))}
              <th className="px-3 py-2 font-semibold text-right bg-rose-50">
                SUM
              </th>
              <th className="px-3 py-2 font-semibold text-right">
                Bajarilish
              </th>
              <th className="px-3 py-2 font-semibold text-right">
                Shu ketishda
              </th>
            </tr>
          </thead>
          <tbody>
            {secOrder.map((sec) => (
              <>
                <tr key={`h-${sec}`}>
                  <td
                    colSpan={d.columns.length + 5}
                    className={`px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide ${SEC_TONE[sec]}`}
                  >
                    {d.sections[sec]}
                  </td>
                </tr>
                {d.rows
                  .filter((r: Any) => r.section === sec)
                  .map((r: Any) => {
                    const money = r.kind === "money";
                    return (
                      <>
                        <tr
                          key={`${r.metric}-p`}
                          className="border-t border-slate-100"
                        >
                          <td
                            rowSpan={2}
                            className="sticky left-0 bg-white px-3 py-1.5 text-slate-800 font-medium align-middle z-10 border-t border-slate-100"
                          >
                            {r.label}
                            {!r.auto && (
                              <span
                                className="text-slate-300 ml-1"
                                title="Fakt avtomat emas"
                              >
                                *
                              </span>
                            )}
                          </td>
                          <td className="px-2 py-1 text-slate-400">Reja</td>
                          {r.cells.map((c: Any, i: number) => (
                            <td
                              key={i}
                              className={`px-2 py-1 text-right bg-amber-50/60 text-slate-600 ${
                                d.sundays.includes(i) ? "!bg-red-50" : ""
                              }`}
                            >
                              {fmt(c.plan, money)}
                            </td>
                          ))}
                          <td className="px-3 py-1 text-right bg-rose-50 font-medium text-slate-700">
                            {fmt(r.sum_plan, money)}
                          </td>
                          <td rowSpan={2} className="px-3 py-1 text-right align-middle border-t border-slate-100">
                            <span className={
                              r.percent === null ? "text-slate-300"
                              : r.percent >= 100 ? "text-emerald-700 font-semibold"
                              : r.percent >= 80 ? "text-amber-600 font-medium"
                              : "text-red-600 font-medium"}>
                              {r.percent !== null ? `${r.percent}%` : "—"}
                            </span>
                          </td>
                          <td rowSpan={2} className="px-3 py-1 text-right align-middle border-t border-slate-100">
                            <span className={
                              r.pace === null ? "text-slate-300"
                              : r.pace >= 100 ? "text-emerald-700 font-semibold"
                              : r.pace >= 80 ? "text-amber-600 font-medium"
                              : "text-red-600 font-medium"}>
                              {r.pace !== null ? `${r.pace}%` : "—"}
                            </span>
                          </td>
                        </tr>
                        <tr key={`${r.metric}-f`}>
                          <td className="px-2 py-1 text-slate-400">Fakt</td>
                          {r.cells.map((c: Any, i: number) => (
                            <td
                              key={i}
                              className={`px-2 py-1 text-right ${
                                d.sundays.includes(i)
                                  ? "bg-red-50"
                                  : ""
                              } ${faktTone(c.plan, c.fakt)}`}
                            >
                              {fmt(c.fakt, money)}
                            </td>
                          ))}
                          <td className="px-3 py-1 text-right bg-rose-50 font-semibold text-slate-900">
                            {fmt(r.sum_fakt, money)}
                          </td>
                        </tr>
                      </>
                    );
                  })}
              </>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400 mt-2">
        Fakt rangi: yashil — reja bajarildi, sariq — 80%+, qizil — 80% dan
        past. "Bajarilish" — yillik rejaga nisbatan; "Shu ketishda" — shu
        kungacha bo'lishi kerak bo'lgan rejaga nisbatan (100% dan past
        bo'lsa, shu sur'atda reja bajarilmaydi). * — fakt hozircha avtomat yig'ilmaydi.
      </p>

      {edit && (
        <PlanEditor
          year={d.year}
          yearLabel={d.year_label}
          months={d.months}
          raw={d.plan_raw}
          onClose={() => {
            setEdit(false);
            load();
          }}
        />
      )}
    </div>
  );
}

const METRICS = [
  ["leads", "Lid"],
  ["online_visits", "Onlinedan tashriflar"],
  ["online_payments", "Yangi to'lovlar (online)"],
  ["visits", "Tashrif"],
  ["new_payments", "Yangi to'lovlar soni"],
  ["old_payments", "Eski to'lovlar soni"],
  ["students", "O'qiyotgan o'quvchilar"],
  ["revenue", "Yalpi tushum"],
  ["expenses", "Xarajatlar"],
  ["profit", "Foyda"],
];
const MONTH_SHORT = ["Sen", "Okt", "Noy", "Dek", "Yan", "Fev", "Mar",
  "Apr", "May", "Iyn", "Iyl", "Avg"];

function PlanEditor({
  year, yearLabel, months, raw, onClose,
}: {
  year: number; yearLabel: string; months: number[];
  raw: Any; onClose: () => void;
}) {
  const [vals, setVals] = useState<Record<string, Record<number, string>>>(
    () => {
      const v: Any = {};
      for (const [k] of METRICS) {
        v[k] = {};
        for (const m of months) v[k][m] = raw?.[k]?.[m] ?? "";
      }
      return v;
    });
  const [growth, setGrowth] = useState(15);
  const [busy, setBusy] = useState(false);

  const suggest = async () => {
    setBusy(true);
    try {
      const r = await api.get<Any>(
        `/plan/suggest?year=${year}&growth=${growth}`);
      setVals((old) => {
        const v = { ...old };
        for (const [k] of METRICS) {
          const sg = r.suggest[k] || {};
          v[k] = { ...v[k] };
          for (const m of months) {
            const s = sg[m] ?? sg[String(m)];
            if (s !== undefined) v[k][m] = String(s);
          }
        }
        return v;
      });
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    setBusy(true);
    const items: Any[] = [];
    for (const [k] of METRICS)
      for (const m of months) {
        const s = vals[k][m];
        if (s !== "" && s !== null && !isNaN(Number(s)))
          items.push({ metric: k, month: m, value: Number(s) });
      }
    try {
      await api.put(`/plan/${year}`, { items });
      onClose();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-5xl max-h-[90vh] overflow-auto p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-900">
            Reja tuzish — {yearLabel}
          </h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="flex items-center gap-2 mb-3 text-sm">
          <span className="text-slate-600">O'tgan yil fakti +</span>
          <select
            value={growth}
            onChange={(e) => setGrowth(Number(e.target.value))}
            className="border border-slate-300 rounded-lg px-2 py-1"
          >
            {[10, 15, 20].map((g) => (
              <option key={g} value={g}>{g}%</option>
            ))}
          </select>
          <button
            onClick={suggest}
            disabled={busy}
            className="bg-slate-100 text-slate-700 rounded-lg px-3 py-1.5 font-medium disabled:opacity-40"
          >
            Taklifni to'ldirish
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="text-xs">
            <thead>
              <tr className="text-slate-500">
                <th className="text-left px-2 py-1.5 font-medium">
                  Ko'rsatkich
                </th>
                {months.map((m, i) => (
                  <th key={m} className="px-1 py-1.5 font-medium">
                    {MONTH_SHORT[i]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {METRICS.map(([k, label]) => (
                <tr key={k} className="border-t border-slate-100">
                  <td className="px-2 py-1 text-slate-700 whitespace-nowrap">
                    {label}
                  </td>
                  {months.map((m) => (
                    <td key={m} className="px-0.5 py-1">
                      <input
                        value={vals[k][m]}
                        onChange={(e) =>
                          setVals({
                            ...vals,
                            [k]: { ...vals[k], [m]: e.target.value },
                          })
                        }
                        className="border border-slate-200 rounded px-1 py-1 w-20 text-right"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600"
          >
            Bekor
          </button>
          <button
            onClick={save}
            disabled={busy}
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
          >
            Saqlash
          </button>
        </div>
      </div>
    </div>
  );
}
