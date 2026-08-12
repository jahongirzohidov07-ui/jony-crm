import { useEffect, useMemo, useState } from "react";
import {
  Layers, Users, BarChart3, CheckCircle2, XCircle, Target,
} from "lucide-react";
import { api } from "../lib/api";

/**
 * Imtihonlar hisoboti — markaz bo'yicha umumiy ko'rinish.
 *
 * Tepada 6 ta karta, ostida 4 kesim: guruhlar, talabalar, ustozlar va
 * yiqilganlar. O'tish chegarasi serverdan keladi (hozir 65%) — imtihonda
 * alohida "o'tish bali" maydoni yo'q, shuning uchun bitta umumiy chegara.
 */

type Card = {
  guruh: number; natija: number; ortacha: number;
  otgan: number; yiqilgan: number; otish_foizi: number;
};
type GRow = {
  guruh: string; ustoz: string; imtihon: number; natija: number;
  ortacha: number; otish_foizi: number;
};
type TRow = {
  ustoz: string; guruh: number; natija: number;
  ortacha: number; otish_foizi: number;
};
type SRow = {
  oquvchi: string; guruh: string; imtihon: string; sana: string;
  ball: number | null; foiz: number; otdi: boolean;
};
type Data = {
  pass_mark: number; start: string; end: string; cards: Card;
  groups: GRow[]; teachers: TRow[]; students: SRow[]; failed: SRow[];
};

type Tab = "groups" | "students" | "teachers" | "failed";

const TABS: { key: Tab; label: string }[] = [
  { key: "groups", label: "Guruhlar bo'yicha" },
  { key: "students", label: "Talabalar bo'yicha" },
  { key: "teachers", label: "Ustozlar bo'yicha" },
  { key: "failed", label: "Yiqilganlar" },
];

function iso(d: Date) {
  return d.getFullYear() + "-" +
    String(d.getMonth() + 1).padStart(2, "0") + "-" +
    String(d.getDate()).padStart(2, "0");
}

function monthsAgo(n: number) {
  const d = new Date();
  d.setMonth(d.getMonth() - n);
  return iso(d);
}

function pctColor(v: number) {
  if (v >= 80) return "text-emerald-600";
  if (v >= 60) return "text-amber-600";
  return "text-rose-600";
}

export default function ExamReport() {
  const [start, setStart] = useState(monthsAgo(6));
  const [end, setEnd] = useState(iso(new Date()));
  const [tab, setTab] = useState<Tab>("groups");
  const [q, setQ] = useState("");
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr("");
    // api.get global filial tanlagichini o'zi qo'shadi (branch_id).
    const url = "/analytics/exam-report?start=" + start +
      "&end=" + end + "&limit=500";
    api.get<Data>(url)
      .then((j) => { if (alive) setData(j); })
      .catch((e) => { if (alive) setErr(String(e.message || e)); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [start, end]);

  const quick = (n: number | null) => {
    setEnd(iso(new Date()));
    setStart(n === null ? "2024-01-01" : monthsAgo(n));
  };

  const needle = q.trim().toLowerCase();
  const groups = useMemo(
    () => (data?.groups || []).filter((x) =>
      !needle || x.guruh.toLowerCase().includes(needle) ||
      (x.ustoz || "").toLowerCase().includes(needle)),
    [data, needle]);
  const teachers = useMemo(
    () => (data?.teachers || []).filter((x) =>
      !needle || (x.ustoz || "").toLowerCase().includes(needle)),
    [data, needle]);
  const students = useMemo(
    () => (data?.students || []).filter((x) =>
      !needle || x.oquvchi.toLowerCase().includes(needle) ||
      x.guruh.toLowerCase().includes(needle) ||
      x.imtihon.toLowerCase().includes(needle)),
    [data, needle]);
  const failed = useMemo(
    () => (data?.failed || []).filter((x) =>
      !needle || x.oquvchi.toLowerCase().includes(needle) ||
      x.guruh.toLowerCase().includes(needle)),
    [data, needle]);

  const c = data?.cards;
  const cards = [
    { t: "Imtihon olingan guruh", v: c ? String(c.guruh) : "—",
      Icon: Layers, tone: "text-indigo-600 bg-indigo-50" },
    { t: "Jami natija", v: c ? String(c.natija) : "—",
      Icon: Users, tone: "text-sky-600 bg-sky-50" },
    { t: "O'rtacha o'zlashtirish", v: c ? c.ortacha + " %" : "—",
      Icon: BarChart3, tone: "text-amber-600 bg-amber-50" },
    { t: "O'tganlar", v: c ? String(c.otgan) : "—",
      Icon: CheckCircle2, tone: "text-emerald-600 bg-emerald-50" },
    { t: "Yiqilganlar", v: c ? String(c.yiqilgan) : "—",
      Icon: XCircle, tone: "text-rose-600 bg-rose-50" },
    { t: "O'tish foizi", v: c ? c.otish_foizi + " %" : "—",
      Icon: Target, tone: "text-violet-600 bg-violet-50" },
  ];

  const th = "px-3 py-2 text-left text-xs font-semibold text-slate-500";
  const td = "px-3 py-2 text-sm text-slate-700";

  return (
    <>
    <ExamTrendBlock />
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {cards.map((x) => (
          <div key={x.t}
            className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2">
              <span className={"rounded-lg p-1.5 " + x.tone}>
                <x.Icon size={16} />
              </span>
              <span className="text-xs text-slate-500">{x.t}</span>
            </div>
            <div className="mt-2 text-2xl font-semibold text-slate-800">
              {x.v}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input type="date" value={start}
          onChange={(e) => setStart(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
        <input type="date" value={end}
          onChange={(e) => setEnd(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
        {[["1 oy", 1], ["3 oy", 3], ["6 oy", 6], ["1 yil", 12]].map(
          ([lbl, n]) => (
            <button key={String(lbl)} onClick={() => quick(Number(n))}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50">
              {lbl}
            </button>
          ))}
        <button onClick={() => quick(null)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50">
          Butun davr
        </button>
        <input value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Qidirish — ism, guruh yoki imtihon..."
          className="ml-auto w-64 rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
      </div>

      {data && (
        <p className="text-xs text-slate-500">
          O'tish chegarasi: {data.pass_mark}% — shundan yuqorisi «o'tgan»
          hisoblanadi. Imtihonga kelmaganlar hisobga olinmaydi.
        </p>
      )}

      <div className="flex flex-wrap gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={"px-3 py-2 text-sm " + (tab === t.key
              ? "border-b-2 border-indigo-500 font-medium text-indigo-600"
              : "text-slate-500 hover:text-slate-700")}>
            {t.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-slate-500">Yuklanmoqda...</p>}
      {err && <p className="text-sm text-rose-600">{err}</p>}

      {!loading && !err && data && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          {tab === "groups" && (
            <table className="min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50">
                <tr>
                  <th className={th}>Guruh</th>
                  <th className={th}>Ustoz</th>
                  <th className={th}>Imtihon</th>
                  <th className={th}>Natija</th>
                  <th className={th}>O'rtacha</th>
                  <th className={th}>O'tish foizi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {groups.map((x, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className={td + " font-medium"}>{x.guruh}</td>
                    <td className={td}>{x.ustoz}</td>
                    <td className={td}>{x.imtihon}</td>
                    <td className={td}>{x.natija}</td>
                    <td className={td}>{x.ortacha} %</td>
                    <td className={td + " font-semibold " +
                      pctColor(x.otish_foizi)}>{x.otish_foizi} %</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {tab === "teachers" && (
            <table className="min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50">
                <tr>
                  <th className={th}>Ustoz</th>
                  <th className={th}>Guruh</th>
                  <th className={th}>Natija</th>
                  <th className={th}>O'rtacha</th>
                  <th className={th}>O'tish foizi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {teachers.map((x, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className={td + " font-medium"}>{x.ustoz}</td>
                    <td className={td}>{x.guruh}</td>
                    <td className={td}>{x.natija}</td>
                    <td className={td}>{x.ortacha} %</td>
                    <td className={td + " font-semibold " +
                      pctColor(x.otish_foizi)}>{x.otish_foizi} %</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {(tab === "students" || tab === "failed") && (
            <table className="min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50">
                <tr>
                  <th className={th}>T/r</th>
                  <th className={th}>FISH</th>
                  <th className={th}>Guruh</th>
                  <th className={th}>Imtihon</th>
                  <th className={th}>Ball</th>
                  <th className={th}>Foiz</th>
                  <th className={th}>Sana</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(tab === "students" ? students : failed).map((x, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className={td}>{i + 1}</td>
                    <td className={td + " font-medium"}>{x.oquvchi}</td>
                    <td className={td}>{x.guruh}</td>
                    <td className={td}>{x.imtihon}</td>
                    <td className={td}>{x.ball ?? "—"}</td>
                    <td className={td + " font-semibold " + pctColor(x.foiz)}>
                      {x.foiz} %
                    </td>
                    <td className={td + " text-slate-500"}>{x.sana}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {((tab === "groups" && !groups.length) ||
            (tab === "teachers" && !teachers.length) ||
            (tab === "students" && !students.length) ||
            (tab === "failed" && !failed.length)) && (
            <p className="p-6 text-center text-sm text-slate-500">
              Bu davrda ma'lumot yo'q.
            </p>
          )}
        </div>
      )}
    </div>
  </>
  );
}


/* eslint-disable @typescript-eslint/no-explicit-any */
/** Oyma-oy o'rtacha imtihon foizi (2026-08-12, Jahongir: "guruh/ustoz
 *  kesimida o'rtacha foizning oyma-oy o'zgarishi - shuni qosh"). */
export function ExamTrendBlock() {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    api.get<any>("/analytics/exam-trend?months=12").then(setD)
      .catch(() => {});
  }, []);
  if (!d) return null;
  const pts = d.months.filter((m: any) => m.avg !== null);
  if (pts.length === 0) return null;
  const max = 100;
  const W = 660, H = 120;
  const xs = (i: number) => 30 + (i * (W - 40)) / Math.max(d.months.length - 1, 1);
  const ys = (v: number) => H - 15 - (v / max) * (H - 30);
  const line = d.months
    .map((m: any, i: number) => (m.avg === null ? null : `${xs(i)},${ys(m.avg)}`))
    .filter(Boolean)
    .join(" ");
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
      <p className="text-sm font-semibold text-slate-900 mb-1">
        Imtihon natijalari trendi (oyma-oy o'rtacha %)
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        {[40, 65, 90].map((g) => (
          <g key={g}>
            <line x1="30" x2={W - 10} y1={ys(g)} y2={ys(g)}
                  stroke="#e2e8f0" strokeDasharray="3 3" />
            <text x="2" y={ys(g) + 3} fontSize="9" fill="#94a3b8">{g}%</text>
          </g>
        ))}
        <polyline points={line} fill="none" stroke="#7c3aed"
                  strokeWidth="2" />
        {d.months.map((m: any, i: number) => m.avg !== null && (
          <g key={m.period}>
            <circle cx={xs(i)} cy={ys(m.avg)} r="3" fill="#7c3aed" />
            <text x={xs(i)} y={ys(m.avg) - 6} fontSize="8.5"
                  textAnchor="middle" fill="#475569">{m.avg}</text>
          </g>
        ))}
        {d.months.map((m: any, i: number) => (
          <text key={m.period} x={xs(i)} y={H - 2} fontSize="8"
                textAnchor="middle" fill="#94a3b8">{m.label}</text>
        ))}
      </svg>
      {d.teachers.length > 0 && (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                <th className="text-left py-1.5 font-medium">Ustoz</th>
                <th className="text-right font-medium">Avvalgi 3 oy</th>
                <th className="text-right font-medium">Oxirgi 3 oy</th>
                <th className="text-right font-medium">O'zgarish</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.teachers.map((t: any) => (
                <tr key={t.teacher}>
                  <td className="py-1.5 text-slate-800">{t.teacher}</td>
                  <td className="text-right text-slate-500">
                    {t.prev3 ?? "—"}
                  </td>
                  <td className="text-right font-medium text-slate-800">
                    {t.last3 ?? "—"}
                  </td>
                  <td className={`text-right font-medium ${
                    t.delta === null ? "text-slate-400"
                    : t.delta >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                    {t.delta === null ? "—"
                     : (t.delta >= 0 ? "+" : "") + t.delta}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-slate-400 mt-2">{d.hint}</p>
    </div>
  );
}
