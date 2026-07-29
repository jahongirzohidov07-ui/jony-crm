import { useEffect, useState } from "react";
import { Download, Banknote, CreditCard, Smartphone, Wallet } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import {
  api,
  type AdminKpiResult,
  type KpiRules,
  type CashflowReport,
  type PnlReport,
  type LtvReport,
  type LtvDimension,
  type RetentionReport,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, FOUNDER, can } from "../lib/roles";
import { categoryLabel, MONTHS } from "../lib/expenses";
import { formatSom, formatPeriodLabel, formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "cashflow" | "pnl" | "ltv" | "retention" | "kpi";

const TABS: { key: Tab; label: string }[] = [
  { key: "cashflow", label: "Pul oqimi" },
  { key: "pnl", label: "Foyda / zarar" },
  { key: "ltv", label: "LTV" },
  { key: "retention", label: "Ustozlar" },
  { key: "kpi", label: "Adminlar KPI" },
];

/** Katta summalarni o'qishga oson qilib qisqartiradi: 12 400 000 -> "12.4 mln". */
function short(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (abs >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

function Stat({
  label,
  value,
  hint,
  tone = "slate",
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red";
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const toneClass =
    tone === "green"
      ? "text-emerald-600"
      : tone === "red"
      ? "text-red-600"
      : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${toneClass}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-slate-400 mt-3 max-w-3xl">{children}</p>;
}

// ---------------------------------------------------------------- Cashflow
function CashflowTab() {
  const [months, setMonths] = useState(6);
  const [data, setData] = useState<CashflowReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<CashflowReport>(`/reports/cashflow?months=${months}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [months]);

  if (loading) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  if (!data) return null;

  const t = data.totals;
  // "Boshqa" grafikda ko'rsatilmaydi - u deyarli har doim nol bo'ladi va
  // faqat shovqin qo'shadi; jadvalda esa jamiga kirib turadi.
  const chart = data.rows.map((r) => ({
    name: formatPeriodLabel(r.period),
    Naqd: r.cash,
    Plastik: r.card,
    Terminal: r.terminal,
  }));

  function exportRows() {
    exportToExcel("pul-oqimi", "Pul oqimi",
      data!.rows.map((r) => ({
        Davr: r.period,
        Naqd: r.cash,
        Plastik: r.card,
        Terminal: r.terminal,
        Boshqa: r.other,
        "Jami kirim": r.income,
        Xarajat: r.expenses,
        "Ustozlar ish haqi": r.payroll,
        "Jami chiqim": r.outflow,
        Sof: r.net,
      })));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1">
          {[3, 6, 12].map((m) => (
            <button
              key={m}
              onClick={() => setMonths(m)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                months === m
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {m} oy
            </button>
          ))}
        </div>
        <button
          onClick={exportRows}
          className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
        >
          <Download size={15} /> Excel
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="Naqd" value={formatSom(t.cash)} icon={Banknote} />
        <Stat label="Plastik" value={formatSom(t.card)} icon={CreditCard} />
        <Stat label="Terminal" value={formatSom(t.terminal)} icon={Smartphone} />
        <Stat label="Jami kirim" value={formatSom(t.income)} icon={Wallet} tone="green" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
        <p className="text-sm font-medium text-slate-700 mb-3">
          To'lov usullari bo'yicha tushum
        </p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis tickFormatter={short} tick={{ fontSize: 12, fill: "#64748b" }} />
            <Tooltip formatter={(v: number) => formatSom(v)} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {/* Yonma-yon ustunlar - qaysi kanal o'sib, qaysi tushib
                borayotgani bir qarashda ko'rinadi. */}
            <Bar dataKey="Naqd" fill="#0d9488" radius={[4, 4, 0, 0]}
                 isAnimationActive={false} />
            <Bar dataKey="Plastik" fill="#38bdf8" radius={[4, 4, 0, 0]}
                 isAnimationActive={false} />
            <Bar dataKey="Terminal" fill="#a78bfa" radius={[4, 4, 0, 0]}
                 isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Oy</th>
              <th className="text-right px-4 py-3 font-medium">Naqd</th>
              <th className="text-right px-4 py-3 font-medium">Plastik</th>
              <th className="text-right px-4 py-3 font-medium">Terminal</th>
              <th className="text-right px-4 py-3 font-medium">Kirim</th>
              <th className="text-right px-4 py-3 font-medium">Xarajat</th>
              <th className="text-right px-4 py-3 font-medium">Ish haqi</th>
              <th className="text-right px-4 py-3 font-medium">Sof</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.period} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-700">
                  {formatPeriodLabel(r.period)}
                </td>
                <td className="px-4 py-3 text-right text-slate-600">{short(r.cash)}</td>
                <td className="px-4 py-3 text-right text-slate-600">{short(r.card)}</td>
                <td className="px-4 py-3 text-right text-slate-600">
                  {short(r.terminal)}
                </td>
                <td className="px-4 py-3 text-right font-medium text-emerald-600">
                  {short(r.income)}
                </td>
                <td className="px-4 py-3 text-right text-slate-600">
                  {short(r.expenses)}
                </td>
                <td className="px-4 py-3 text-right text-slate-600">
                  {short(r.payroll)}
                </td>
                <td
                  className={`px-4 py-3 text-right font-semibold ${
                    r.net >= 0 ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {short(r.net)}
                </td>
              </tr>
            ))}
            <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
              <td className="px-4 py-3 text-slate-700">Jami</td>
              <td className="px-4 py-3 text-right">{short(t.cash)}</td>
              <td className="px-4 py-3 text-right">{short(t.card)}</td>
              <td className="px-4 py-3 text-right">{short(t.terminal)}</td>
              <td className="px-4 py-3 text-right text-emerald-600">
                {short(t.income)}
              </td>
              <td className="px-4 py-3 text-right">{short(t.expenses)}</td>
              <td className="px-4 py-3 text-right">{short(t.payroll)}</td>
              <td
                className={`px-4 py-3 text-right ${
                  t.net >= 0 ? "text-emerald-600" : "text-red-600"
                }`}
              >
                {short(t.net)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <Note>
        Kirim — haqiqatda kassaga tushgan pul. Hisoblangan oylik (qarz) bu
        yerga kirmaydi. Ustozlar ish haqi yoqlamadan avtomatik olinadi.
      </Note>
    </div>
  );
}

// --------------------------------------------------------------------- P&L
function PnlTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<PnlReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<PnlReport>(`/reports/pnl?year=${year}&month=${month}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [year, month]);

  const years = [now.getFullYear() - 1, now.getFullYear()];

  return (
    <div>
      <div className="flex items-center gap-2 mb-5">
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>
              {m}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
        >
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <Stat label="Kirim" value={formatSom(data.income)} tone="green" />
            <Stat
              label="Chiqim"
              value={formatSom(data.outflow_total)}
              hint={
                data.payroll_total > 0
                  ? `shundan ish haqi ${short(data.payroll_total)}`
                  : undefined
              }
            />
            <Stat
              label="Foyda"
              value={formatSom(data.profit)}
              tone={data.profit >= 0 ? "green" : "red"}
            />
            <Stat
              label="Rentabellik"
              value={`${data.margin}%`}
              hint="foyda / kirim"
              tone={data.margin >= 0 ? "green" : "red"}
            />
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                <tr className="bg-emerald-50/60">
                  <td className="px-4 py-3 font-medium text-slate-700">Kirim</td>
                  <td className="px-4 py-3 text-right font-semibold text-emerald-700">
                    {formatSom(data.income)}
                  </td>
                </tr>
                {(
                  [
                    ["cash", "Naqd"],
                    ["card", "Plastik"],
                    ["terminal", "Terminal"],
                    ["other", "Boshqa"],
                  ] as const
                )
                  .filter(([k]) => (data.income_by_method[k] || 0) > 0)
                  .map(([k, label]) => (
                    <tr key={k} className="border-t border-slate-100">
                      <td className="px-4 py-2 pl-8 text-slate-500">{label}</td>
                      <td className="px-4 py-2 text-right text-slate-600">
                        {formatSom(data.income_by_method[k])}
                      </td>
                    </tr>
                  ))}

                <tr className="border-t-2 border-slate-200 bg-red-50/50">
                  <td className="px-4 py-3 font-medium text-slate-700">Chiqim</td>
                  <td className="px-4 py-3 text-right font-semibold text-red-700">
                    {formatSom(data.outflow_total)}
                  </td>
                </tr>
                {data.expense_lines.length === 0 && (
                  <tr className="border-t border-slate-100">
                    <td colSpan={2} className="px-4 py-3 text-center text-slate-400">
                      Bu oyda chiqim kiritilmagan
                    </td>
                  </tr>
                )}
                {data.expense_lines.map((l) => (
                  <tr key={l.category} className="border-t border-slate-100">
                    <td className="px-4 py-2 pl-8 text-slate-500">
                      {l.auto ? "Ustozlar ish haqi" : categoryLabel(l.category)}
                      {l.auto && (
                        <span className="ml-2 text-[10px] uppercase tracking-wide bg-brand-50 text-brand-700 px-1.5 py-0.5 rounded">
                          avtomatik
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-600">
                      {formatSom(l.amount)}
                    </td>
                  </tr>
                ))}

                <tr className="border-t-2 border-slate-300 bg-slate-50">
                  <td className="px-4 py-3 font-semibold text-slate-800">
                    Sof foyda
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-bold ${
                      data.profit >= 0 ? "text-emerald-700" : "text-red-700"
                    }`}
                  >
                    {formatSom(data.profit)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <Note>
            "Avtomatik" belgisi qo'yilgan qator yoqlama asosida o'zi
            hisoblanadi — uni Xarajatlar bo'limiga qayta kiritish kerak emas,
            aks holda ikki marta ayiriladi.
          </Note>
        </>
      )}
    </div>
  );
}

// --------------------------------------------------------------------- LTV
const DIMENSIONS: { key: LtvDimension; label: string }[] = [
  { key: "branch", label: "Filiallar" },
  { key: "teacher", label: "Ustozlar" },
  { key: "group", label: "Guruhlar" },
];

function LtvTab() {
  const [dimension, setDimension] = useState<LtvDimension>("branch");
  const [data, setData] = useState<LtvReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<LtvReport>(`/reports/ltv?dimension=${dimension}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [dimension]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1">
          {DIMENSIONS.map((d) => (
            <button
              key={d.key}
              onClick={() => setDimension(d.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                dimension === d.key
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>
        {data && data.rows.length > 0 && (
          <button
            onClick={() =>
              exportToExcel("ltv", "LTV",
                data.rows.map((r) => ({
                  Kesim: r.label,
                  "O'quvchilar": r.students,
                  "Ketganlar": r.left,
                  "O'rtacha oy": r.avg_months,
                  "O'rtacha daromad": r.avg_revenue,
                  "Jami daromad": r.total_revenue,
                  "Ketish %": r.churn,
                })))
            }
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
          >
            <Download size={15} /> Excel
          </button>
        )}
      </div>

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : !data.overall ? (
        <p className="text-slate-400 text-sm">Hali ma'lumot yo'q.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <Stat label="O'quvchilar" value={String(data.overall.students)} />
            <Stat
              label="O'rtacha qolish muddati"
              value={`${data.overall.avg_months} oy`}
              hint="qo'shilgandan bugungacha"
            />
            <Stat
              label="O'rtacha LTV"
              value={formatSom(data.overall.avg_revenue)}
              hint="bitta o'quvchidan tushgan pul"
              tone="green"
            />
            <Stat
              label="Ketganlar"
              value={String(data.overall.left)}
              hint={`jami ${data.overall.students} tadan`}
            />
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">
                    {DIMENSIONS.find((d) => d.key === dimension)?.label}
                  </th>
                  <th className="text-right px-4 py-3 font-medium">O'quvchi</th>
                  <th className="text-right px-4 py-3 font-medium">O'rt. oy</th>
                  <th className="text-right px-4 py-3 font-medium">O'rt. LTV</th>
                  <th className="text-right px-4 py-3 font-medium">Jami</th>
                  <th className="text-right px-4 py-3 font-medium">Ketish %</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={String(r.key)} className="border-t border-slate-100">
                    <td className="px-4 py-3 text-slate-800">{r.label}</td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {r.students}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {r.avg_months}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-slate-800">
                      {formatSom(r.avg_revenue)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {short(r.total_revenue)}
                    </td>
                    <td
                      className={`px-4 py-3 text-right ${
                        r.churn > 20 ? "text-red-600 font-medium" : "text-slate-500"
                      }`}
                    >
                      {r.churn}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Note>
            Qolish muddati o'quvchi qo'shilgan sanadan bugungacha (ketgan
            bo'lsa — ketgan sanagacha) hisoblanadi. Ketgan sana o'quvchi
            "Arxiv" holatiga o'tkazilganda avtomatik qo'yiladi. Ustoz va guruh
            kesimida o'quvchi hozirgi guruhiga qarab bo'linadi.
          </Note>
        </>
      )}
    </div>
  );
}

// --------------------------------------------------------------- Retention
function RetentionTab() {
  const [data, setData] = useState<RetentionReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<RetentionReport>("/reports/teacher-retention")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  const s = data.summary;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="Hozir ishlayapti" value={String(s.active)} />
        <Stat
          label="O'rtacha staj"
          value={`${s.avg_tenure_active} oy`}
          hint="faol ustozlar"
        />
        <Stat
          label="Ketganlar (12 oy)"
          value={String(s.left_last_12m)}
          hint={s.left ? `jami ketgan: ${s.left}` : undefined}
        />
        <Stat
          label="Kadrlar almashuvi"
          value={`${s.turnover_12m}%`}
          hint="oxirgi 12 oy"
          tone={s.turnover_12m > 25 ? "red" : "slate"}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Ustoz</th>
              <th className="text-left px-4 py-3 font-medium">Filial</th>
              <th className="text-left px-4 py-3 font-medium">Ishga kirgan</th>
              <th className="text-left px-4 py-3 font-medium">Ketgan</th>
              <th className="text-right px-4 py-3 font-medium">Staj (oy)</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  Ustozlar qo'shilmagan
                </td>
              </tr>
            )}
            {data.rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-800">
                  {r.full_name}
                  {!r.active && (
                    <span className="ml-2 text-[10px] uppercase tracking-wide bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                      ketgan
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500">{r.branch || "—"}</td>
                <td className="px-4 py-3 text-slate-600">{formatDate(r.hired_date)}</td>
                <td className="px-4 py-3 text-slate-500">
                  {r.left_date ? formatDate(r.left_date) : "—"}
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-800">
                  {r.months}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Note>
        Ishga kirgan sana ustoz qo'shilganda avtomatik qo'yiladi, ketgan sana
        esa O'qituvchilar bo'limida "ishdan ketgan" deb belgilanganda. Ustozni
        o'chirib tashlash o'rniga shu belgini qo'ying — shunda tarix saqlanadi.
      </Note>
    </div>
  );
}


// -------------------------------------------------------- Adminlar KPI ----
function KpiRulesEditor({
  rules,
  setRules,
  canAdmin,
  onSave,
  saving,
  saved,
}: {
  rules: KpiRules;
  setRules: (r: KpiRules) => void;
  canAdmin: boolean;
  onSave: () => void;
  saving: boolean;
  saved: boolean;
}) {
  function upd<K extends "collection" | "new_clients">(
    key: K,
    i: number,
    patch: Partial<KpiRules[K][number]>
  ) {
    setRules({
      ...rules,
      [key]: rules[key].map((r, idx) => (idx === i ? { ...r, ...patch } : r)),
    });
  }

  const cell =
    "w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50";

  return (
    <div className="mt-8">
      <h3 className="font-medium text-slate-800 mb-1">Bonus qoidalari</h3>
      <p className="text-xs text-slate-500 mb-4 max-w-3xl">
        Bu jadvallar ish haqiga bevosita ta'sir qiladi, shuning uchun ularni
        faqat asoschi o'zgartira oladi. O'zgartirish darrov keyingi hisobga
        qo'llanadi.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">
            Eski to'lovlarni yig'ish
          </p>
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-3 py-2.5 font-medium">O'quvchi</th>
                  <th className="text-left px-3 py-2.5 font-medium">gacha</th>
                  <th className="text-left px-3 py-2.5 font-medium">Foiz</th>
                  <th className="text-left px-3 py-2.5 font-medium">Bonus</th>
                  <th className="px-2"></th>
                </tr>
              </thead>
              <tbody>
                {rules.collection.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        value={r.min_students}
                        onChange={(e) =>
                          upd("collection", i, {
                            min_students: Number(e.target.value),
                          })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        placeholder="cheksiz"
                        value={r.max_students ?? ""}
                        onChange={(e) =>
                          upd("collection", i, {
                            max_students:
                              e.target.value === "" ? null : Number(e.target.value),
                          })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        value={r.min_percent}
                        onChange={(e) =>
                          upd("collection", i, { min_percent: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className="w-32 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                        value={r.bonus}
                        onChange={(e) =>
                          upd("collection", i, { bonus: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-2 py-2 text-right">
                      {canAdmin && (
                        <button
                          onClick={() =>
                            setRules({
                              ...rules,
                              collection: rules.collection.filter((_, x) => x !== i),
                            })
                          }
                          className="text-slate-300 hover:text-red-500 text-xs"
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {canAdmin && (
            <button
              onClick={() =>
                setRules({
                  ...rules,
                  collection: [
                    ...rules.collection,
                    { min_students: 0, max_students: null, min_percent: 90, bonus: 0 },
                  ],
                })
              }
              className="text-sm text-slate-600 hover:text-brand-600 mt-2"
            >
              + Qator qo'shish
            </button>
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">
            Yangi mijozlar
          </p>
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-3 py-2.5 font-medium">Nechtadan</th>
                  <th className="text-left px-3 py-2.5 font-medium">Bonus</th>
                  <th className="px-2"></th>
                </tr>
              </thead>
              <tbody>
                {rules.new_clients.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        value={r.min_clients}
                        onChange={(e) =>
                          upd("new_clients", i, { min_clients: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className="w-32 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                        value={r.bonus}
                        onChange={(e) =>
                          upd("new_clients", i, { bonus: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-2 py-2 text-right">
                      {canAdmin && (
                        <button
                          onClick={() =>
                            setRules({
                              ...rules,
                              new_clients: rules.new_clients.filter((_, x) => x !== i),
                            })
                          }
                          className="text-slate-300 hover:text-red-500 text-xs"
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {canAdmin && (
            <button
              onClick={() =>
                setRules({
                  ...rules,
                  new_clients: [...rules.new_clients, { min_clients: 10, bonus: 0 }],
                })
              }
              className="text-sm text-slate-600 hover:text-brand-600 mt-2"
            >
              + Pog'ona qo'shish
            </button>
          )}
        </div>
      </div>

      {canAdmin && (
        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={onSave}
            disabled={saving}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Qoidalarni saqlash"}
          </button>
          {saved && <span className="text-sm text-emerald-600">Saqlandi</span>}
        </div>
      )}
    </div>
  );
}

function KpiTab({ canAdmin }: { canAdmin: boolean }) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<AdminKpiResult | null>(null);
  const [rules, setRules] = useState<KpiRules | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<AdminKpiResult>(`/kpi/admins?year=${year}&month=${month}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [year, month]);

  useEffect(() => {
    api.get<KpiRules>("/kpi/rules").then(setRules);
  }, []);

  async function saveRules() {
    if (!rules) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.put<KpiRules>("/kpi/rules", {
        collection: rules.collection.map((r) => ({
          min_students: r.min_students,
          max_students: r.max_students ?? null,
          min_percent: r.min_percent,
          bonus: r.bonus,
        })),
        new_clients: rules.new_clients.map((r) => ({
          min_clients: r.min_clients,
          bonus: r.bonus,
        })),
      });
      setRules(updated);
      setSaved(true);
      const fresh = await api.get<AdminKpiResult>(
        `/kpi/admins?year=${year}&month=${month}`
      );
      setData(fresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const years = [now.getFullYear() - 1, now.getFullYear()];

  return (
    <div>
      <div className="flex items-center justify-between mb-5 gap-2">
        <div className="flex items-center gap-2">
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
        {data && data.rows.length > 0 && (
          <button
            onClick={() =>
              exportToExcel("adminlar-kpi", "KPI",
                data.rows.map((r) => ({
                  Admin: r.full_name,
                  Filial: r.branch ?? "",
                  "Fiks oylik": r.fix_salary,
                  "Faol o'quvchi": r.active_students,
                  "Tushishi kerak": r.expected,
                  Tushgan: r.collected,
                  "Foiz %": r.collection_percent,
                  "Yig'ish bonusi": r.collection_bonus,
                  "Yangi mijoz": r.new_clients,
                  "Yangi mijoz bonusi": r.new_client_bonus,
                  Jami: r.total,
                })))
            }
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
          >
            <Download size={15} /> Excel
          </button>
        )}
      </div>

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hali administrator (sotuv menejeri) roli berilgan xodim yo'q.
          Xodimlar bo'limidan qo'shing va fiks oyligini belgilang.
        </p>
      ) : (
        <>
          {data.rows.map((r) => (
            <div
              key={r.user_id}
              className="bg-white rounded-xl border border-slate-200 p-5 mb-4"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="font-semibold text-slate-900">{r.full_name}</p>
                  <p className="text-xs text-slate-500">
                    {r.branch || "Filial belgilanmagan"} · {r.active_students} faol
                    o'quvchi
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Jami ish haqi</p>
                  <p className="text-xl font-bold text-brand-700">
                    {formatSom(r.total)}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Fiks oylik</p>
                  <p className="font-semibold text-slate-800">
                    {formatSom(r.fix_salary)}
                  </p>
                  {!r.fix_salary && (
                    <p className="text-xs text-amber-600 mt-1">
                      Xodimlar bo'limidan belgilang
                    </p>
                  )}
                </div>

                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">
                    Eski to'lovlar · {r.collection_percent}%
                  </p>
                  <p
                    className={`font-semibold ${
                      r.collection_bonus > 0 ? "text-emerald-600" : "text-slate-400"
                    }`}
                  >
                    {r.collection_bonus > 0 ? `+${formatSom(r.collection_bonus)}` : "bonus yo'q"}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {short(r.collected)} / {short(r.expected)} tushdi
                  </p>
                </div>

                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">
                    Yangi mijoz · {r.new_clients} ta
                  </p>
                  <p
                    className={`font-semibold ${
                      r.new_client_bonus > 0 ? "text-emerald-600" : "text-slate-400"
                    }`}
                  >
                    {r.new_client_bonus > 0 ? `+${formatSom(r.new_client_bonus)}` : "bonus yo'q"}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {short(r.new_client_revenue)} tushum
                  </p>
                </div>
              </div>
            </div>
          ))}

          <Note>
            Bonuslar filial ko'rsatkichi bo'yicha hisoblanadi — bitta filialda
            ikkita admin bo'lsa, ikkalasi ham to'liq bonusni oladi. Foiz summa
            bo'yicha: shu oyda eski o'quvchilarga hisoblangan summadan qanchasi
            kassaga tushgani. Yangi mijoz — birinchi marta to'lov qilgan
            o'quvchi; uning to'lovi yig'ish foiziga kirmaydi.
          </Note>
        </>
      )}

      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

      {rules && (
        <KpiRulesEditor
          rules={rules}
          setRules={(r) => {
            setRules(r);
            setSaved(false);
          }}
          canAdmin={canAdmin}
          onSave={saveRules}
          saving={saving}
          saved={saved}
        />
      )}
    </div>
  );
}

// -------------------------------------------------------------------- Page
export default function Reports() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("cashflow");

  if (!can(user?.role, FINANCE_ACCESS)) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl">
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Hisobotlar</h1>
      <p className="text-sm text-slate-500 mb-5">
        Moliya va o'quvchi ko'rsatkichlari
      </p>

      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "kpi" && <KpiTab canAdmin={user?.role === FOUNDER} />}
      {tab === "cashflow" && <CashflowTab />}
      {tab === "pnl" && <PnlTab />}
      {tab === "ltv" && <LtvTab />}
      {tab === "retention" && <RetentionTab />}
    </div>
  );
}
