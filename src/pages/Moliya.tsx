import { useEffect, useState } from "react";
import {
  Download, Plus, X, Trash2, Pencil,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { Link } from "react-router-dom";
import {
  api,
  type CashflowReport,
  type CashflowLedger,
  type BillingMonth,
  type CollectionReport,
  type CashMethodBlock,
  type LedgerRow,
  type PnlReport,
  type Expense,
  type Branch,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  FINANCE_ACCESS, CASH_ACCESS, PAYROLL_VIEW, PAYMENT_LIST_VIEW, can,
} from "../lib/roles";
import Debtors from "./Debtors";
import {
  categoryLabel, categoriesByGroup, groupLabel, categoryGroup, MONTHS,
} from "../lib/expenses";
import { formatSom, formatPeriodLabel, formatDate } from "../lib/format";
import { methodLabel, MARKETING_CHANNELS, PAYMENT_METHODS } from "../lib/payments";
import { exportToExcel } from "../lib/exportXlsx";
import { BreakEvenTab } from "../components/BreakEven";
import { FinanceOverviewTab } from "../components/FinanceOverview";
import { BudgetTab } from "../components/Budget";
import { PaymentCalendarTab } from "../components/PaymentCalendar";
import { PayrollTab, MonthPaymentsTab } from "../components/Payroll";

type Tab = "overview" | "debtors" | "cashflow" | "pnl" | "expenses" | "billing" | "breakeven" | "budget" | "calendar" | "payroll" | "paid";

/**
 * Administrator (sotuv menejeri) kassa bilan ishlaydi — qarzdorlar va
 * oylik hisob-kitob. Foyda-zarar va xarajatlar unga ko'rinmaydi.
 */
const CASH_TABS: { key: Tab; label: string }[] = [
  { key: "debtors", label: "Qarzdorlar" },
  { key: "billing", label: "Oylik hisob-kitob" },
];

const FULL_TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Umumiy ko'rinish" },
  { key: "debtors", label: "Qarzdorlar" },
  { key: "cashflow", label: "Pul oqimi" },
  { key: "pnl", label: "Foyda / zarar" },
  { key: "breakeven", label: "Zararsizlik" },
  { key: "budget", label: "Budjet" },
  { key: "calendar", label: "To'lov kalendari" },
  { key: "expenses", label: "Xarajatlar" },
  { key: "billing", label: "Oylik hisob-kitob" },
];

// Shu oy to'lovlari — administratorga ham ochiq, shuning uchun
// tab ro'yxatiga rolga qarab qo'shiladi.
const PAID_TAB: { key: Tab; label: string } = {
  key: "paid", label: "Shu oy to'lovlari",
};
// Xodim oyliklari — faqat oylik beradigan va nazorat qiladiganlar.
const PAYROLL_TAB: { key: Tab; label: string } = {
  key: "payroll", label: "Oyliklar",
};

/** Katta summalarni o'qishga oson qilib qisqartiradi: 12 400 000 -> "12.4 mln". */
function short(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (abs >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

function Stat({
  label, value, hint, tone = "slate", icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red";
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const toneClass =
    tone === "green" ? "text-emerald-600"
      : tone === "red" ? "text-red-600"
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
// Google Sheet'dagi kassa daftari ko'rinishi: tepada Kirim / Chiqim / Kassa
// jadvali usullar kesimida, pastda har bir yozuv alohida qator - kirim
// yashil, chiqim qizil.
const METHOD_COLS: { key: keyof CashMethodBlock; label: string }[] = [
  { key: "total", label: "Jami" },
  { key: "cash", label: "Naqd" },
  { key: "card", label: "Click" },
  { key: "terminal", label: "Terminal" },
];

function SummaryTable({ data }: { data: CashflowLedger }) {
  const rows: {
    label: string;
    block: CashMethodBlock;
    cls: string;
  }[] = [
    { label: "Kirim", block: data.kirim, cls: "bg-emerald-100 text-emerald-900" },
    { label: "Chiqim", block: data.chiqim, cls: "bg-red-100 text-red-900" },
    { label: "Kassa", block: data.kassa, cls: "bg-amber-100 text-amber-900" },
  ];
  return (
    <div className="overflow-x-auto">
      <table className="text-sm border-separate" style={{ borderSpacing: 2 }}>
        <thead>
          <tr>
            <th className="w-28" />
            {METHOD_COLS.map((c) => (
              <th
                key={c.key}
                className="px-3 py-1.5 text-xs font-medium text-slate-500 text-center min-w-[110px]"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label}>
              <td
                className={`px-3 py-2 rounded-md text-sm font-medium text-center ${r.cls}`}
              >
                {r.label}
              </td>
              {METHOD_COLS.map((c) => (
                <td
                  key={c.key}
                  className={`px-3 py-2 rounded-md text-right tabular-nums ${r.cls}`}
                >
                  {formatSom(r.block[c.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PaymentKindTable({ data }: { data: CashflowLedger }) {
  return (
    <table className="text-sm border-separate" style={{ borderSpacing: 2 }}>
      <thead>
        <tr>
          <th className="w-24" />
          <th className="px-3 py-1.5 text-xs font-medium text-slate-500 min-w-[110px]">
            Yangi to'lov
          </th>
          <th className="px-3 py-1.5 text-xs font-medium text-slate-500 min-w-[110px]">
            Eski to'lov
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td className="px-2 py-2 text-xs text-slate-500 text-right">Soni</td>
          <td className="px-3 py-2 rounded-md bg-emerald-100 text-emerald-900 text-center font-medium">
            {data.new_payments.count}
          </td>
          <td className="px-3 py-2 rounded-md bg-emerald-100 text-emerald-900 text-center font-medium">
            {data.old_payments.count}
          </td>
        </tr>
        <tr>
          <td className="px-2 py-2 text-xs text-slate-500 text-right">Summasi</td>
          <td className="px-3 py-2 rounded-md bg-emerald-100 text-emerald-900 text-right tabular-nums">
            {formatSom(data.new_payments.amount)}
          </td>
          <td className="px-3 py-2 rounded-md bg-emerald-100 text-emerald-900 text-right tabular-nums">
            {formatSom(data.old_payments.amount)}
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function ledgerCategoryLabel(r: LedgerRow): string {
  if (r.direction === "in") {
    return r.category === "new_payment" ? "Yangi to'lov" : "Eski to'lov";
  }
  if (r.category === "teacher_salary") return "Ustozlar oyligi";
  return "Xarajat";
}

function CashflowTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [filter, setFilter] = useState<"all" | "in" | "out">("all");
  const [data, setData] = useState<CashflowLedger | null>(null);
  const [trend, setTrend] = useState<CashflowReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<CashflowLedger>(`/reports/cashflow-ledger?year=${year}&month=${month}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [year, month]);

  useEffect(() => {
    api
      .get<CashflowReport>("/reports/cashflow?months=6")
      .then(setTrend)
      .catch(() => setTrend(null));
  }, []);

  if (loading) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  if (!data) return null;

  const rows =
    filter === "all" ? data.rows : data.rows.filter((r) => r.direction === filter);

  function exportRows() {
    exportToExcel(`kassa-${year}-${String(month).padStart(2, "0")}`, "Kassa",
      data!.rows.map((r) => ({
        Sana: r.date,
        Summa: r.amount,
        Izoh: r.title,
        Usul: methodLabel(r.method),
        Turi: r.direction === "in" ? "Kirim" : "Chiqim",
        Filial: r.branch,
        Kategoriya: ledgerCategoryLabel(r),
      })));
  }

  const years = [now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2];

  return (
    <div>
      {/* --- Sana tanlash --- */}
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>
              {m}
            </option>
          ))}
        </select>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <div className="flex-1" />
        <button
          onClick={exportRows}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <Download size={14} /> Excel
        </button>
      </div>

      {/* --- Tepadagi statistika --- */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
        <div className="flex flex-wrap gap-8">
          <SummaryTable data={data} />
          <PaymentKindTable data={data} />
        </div>
        <Note>
          Kassa = kirim − chiqim, har bir usul bo'yicha alohida. Ustozlar
          oyligi yoqlamadan avtomat hisoblanib, chiqimga qo'shilgan.
        </Note>
      </div>

      {/* --- Kassa daftari --- */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
          <p className="text-sm font-medium text-slate-700">Kassa daftari</p>
          <span className="text-xs text-slate-400">{rows.length} ta yozuv</span>
          <div className="flex-1" />
          <div className="flex gap-1">
            {([
              { k: "all", l: "Hammasi" },
              { k: "in", l: "Kirim" },
              { k: "out", l: "Chiqim" },
            ] as const).map((f) => (
              <button
                key={f.k}
                onClick={() => setFilter(f.k)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                  filter === f.k
                    ? "bg-brand-50 border-brand-400 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                }`}
              >
                {f.l}
              </button>
            ))}
          </div>
        </div>

        {rows.length === 0 ? (
          <p className="text-sm text-slate-400 py-10 text-center">
            Bu oyda yozuv yo'q
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-xs text-slate-500">
                  <th className="text-left px-4 py-2 w-28">Sana</th>
                  <th className="text-right w-36 pr-6">Summa</th>
                  <th className="text-left pl-2">Izoh</th>
                  <th className="text-left w-28">Usul</th>
                  <th className="text-left w-24">Turi</th>
                  <th className="text-left w-32">Filial</th>
                  <th className="text-left w-32">Kategoriya</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const inRow = r.direction === "in";
                  const bg = inRow
                    ? "bg-emerald-50 hover:bg-emerald-100"
                    : "bg-red-50 hover:bg-red-100";
                  const fg = inRow ? "text-emerald-900" : "text-red-900";
                  return (
                    <tr
                      key={r.id}
                      className={`border-t border-white ${bg} ${fg} transition`}
                    >
                      <td className="px-4 py-2">{formatDate(r.date)}</td>
                      <td className="text-right font-medium tabular-nums pr-6">
                        {inRow ? "+" : "−"}
                        {formatSom(r.amount)}
                      </td>
                      <td className="py-2 pl-2">
                        {r.student_id ? (
                          <Link
                            to={`/students/${r.student_id}`}
                            className="hover:underline"
                          >
                            {r.title}
                          </Link>
                        ) : (
                          r.title
                        )}
                      </td>
                      <td>{methodLabel(r.method)}</td>
                      <td className="font-medium">{inRow ? "Kirim" : "Chiqim"}</td>
                      <td>{r.branch}</td>
                      <td>{ledgerCategoryLabel(r)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* --- Oylar bo'yicha dinamika --- */}
      {trend && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mt-5">
          <p className="text-sm font-medium text-slate-700">Oylar bo'yicha tushum</p>
          <p className="text-xs text-slate-400 mb-3">Usullar kesimida, oxirgi 6 oy</p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              data={trend.rows.map((r) => ({
                name: formatPeriodLabel(r.period),
                Naqd: r.cash,
                Click: r.card,
                Terminal: r.terminal,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis
                tickFormatter={(v) =>
                  v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}mln` : String(v / 1000)
                }
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <Tooltip formatter={(v: number) => formatSom(v)} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Naqd" fill="#0d9488" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="Click" fill="#38bdf8" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="Terminal" fill="#a78bfa" radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

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

// -------------------------------------------------------------- Xarajatlar
function ExpenseForm({
  branches,
  defaultBranchId,
  defaultDate,
  initial,
  onClose,
  onSaved,
}: {
  branches: Branch[];
  defaultBranchId: number | null;
  defaultDate: string;
  initial?: Expense;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editing = !!initial;
  const [date, setDate] = useState(initial?.date ?? defaultDate);
  const [category, setCategory] = useState(initial?.category ?? "rent");
  const [amount, setAmount] = useState(
    initial ? String(Math.round(initial.amount)) : ""
  );
  const [note, setNote] = useState(initial?.note ?? "");
  const [method, setMethod] = useState(initial?.method ?? "cash");
  const [channel, setChannel] = useState(initial?.channel ?? "");
  const [branchId, setBranchId] = useState(
    initial?.branch_id
      ? String(initial.branch_id)
      : defaultBranchId
      ? String(defaultBranchId)
      : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("To'g'ri summa kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body = {
        date,
        category,
        amount: value,
        note: note || null,
        method,
        // Kanal faqat reklama xarajatida ma'noga ega - CAC shundan
        // hisoblanadi. Boshqa turda tozalab yuboramiz.
        channel: categoryGroup(category) === "marketing" ? channel || null : null,
        branch_id: branchId ? Number(branchId) : null,
      };
      if (editing) await api.put(`/expenses/${initial!.id}`, body);
      else await api.post("/expenses", body);
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[88vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {editing ? "Xarajatni tahrirlash" : "Yangi xarajat"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">
              Xarajat turi
            </label>
            {categoriesByGroup().map((g) => (
              <div key={g.key} className="mb-2.5">
                <p className="text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  {g.label}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {g.items.map((c) => (
                    <button
                      key={c.key}
                      type="button"
                      onClick={() => setCategory(c.key)}
                      className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                        category === c.key
                          ? "bg-brand-50 border-brand-400 text-brand-700"
                          : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                      }`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Sana</label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Summa (so'm)
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                autoFocus
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              To'lov usuli
            </label>
            <div className="flex gap-1.5">
              {PAYMENT_METHODS.map((m) => (
                <button
                  key={m.key}
                  type="button"
                  onClick={() => setMethod(m.key)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition ${
                    method === m.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {categoryGroup(category) === "marketing" && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Reklama kanali
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
              >
                <option value="">— kanal ko'rsatilmagan —</option>
                {MARKETING_CHANNELS.map((c) => (
                  <option key={c.key} value={c.key}>
                    {c.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-400 mt-1">
                Kanalni ko'rsatsangiz, Marketing bo'limida shu kanalning CAC'i
                avtomat hisoblanadi.
              </p>
            </div>
          )}

          {branches.length > 1 && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Filial</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={branchId}
                onChange={(e) => setBranchId(e.target.value)}
              >
                <option value="">— umumiy (filialsiz) —</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Izoh</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={note ?? ""}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Masalan: Iyul oyi ijarasi"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : editing ? "Saqlash" : "Qo'shish"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ExpensesTab() {
  const { user } = useAuth();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [items, setItems] = useState<Expense[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [editing, setEditing] = useState<Expense | null>(null);

  function load() {
    setLoading(true);
    api
      .get<Expense[]>(`/expenses?year=${year}&month=${month}`)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [year, month]);
  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, []);

  const total = items.reduce((s, e) => s + e.amount, 0);

  // Guruh kesimida yig'indi - qaysi yo'nalishga ko'p ketayotgani ko'rinsin.
  const byGroup = items.reduce<Record<string, number>>((acc, e) => {
    const g = categoryGroup(e.category);
    acc[g] = (acc[g] || 0) + e.amount;
    return acc;
  }, {});
  const groupRows = Object.entries(byGroup).sort((a, b) => b[1] - a[1]);

  async function remove(e: Expense) {
    if (!confirm(`${categoryLabel(e.category)} — ${formatSom(e.amount)} o'chirilsinmi?`))
      return;
    try {
      await api.delete(`/expenses/${e.id}`);
      setItems((prev) => prev.filter((x) => x.id !== e.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik");
    }
  }

  const years = [now.getFullYear() - 1, now.getFullYear(), now.getFullYear() + 1];
  const defaultDate = `${year}-${String(month).padStart(2, "0")}-${String(
    Math.min(now.getDate(), 28)
  ).padStart(2, "0")}`;

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
          <span className="text-sm text-slate-500 ml-1">
            jami <span className="font-semibold text-slate-800">{formatSom(total)}</span>
          </span>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          <Plus size={16} /> Yangi xarajat
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {groupRows.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {groupRows.map(([g, sum]) => (
            <div key={g} className="bg-white border border-slate-200 rounded-lg px-3 py-2">
              <p className="text-xs text-slate-500">{groupLabel(g)}</p>
              <p className="text-sm font-semibold text-slate-800">{formatSom(sum)}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Sana</th>
                <th className="text-left px-4 py-3 font-medium">Turi</th>
                <th className="text-left px-4 py-3 font-medium">Guruh</th>
                <th className="text-left px-4 py-3 font-medium">Izoh</th>
                <th className="text-left px-4 py-3 font-medium">Filial</th>
                <th className="text-right px-4 py-3 font-medium">Summa</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                    Bu oy uchun xarajat kiritilmagan
                  </td>
                </tr>
              )}
              {items.map((e) => (
                <tr key={e.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-600">{formatDate(e.date)}</td>
                  <td className="px-4 py-3 text-slate-800">{categoryLabel(e.category)}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {groupLabel(categoryGroup(e.category))}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{e.note || "—"}</td>
                  <td className="px-4 py-3 text-slate-500">{e.branch?.name || "—"}</td>
                  <td className="px-4 py-3 text-right font-medium text-slate-800">
                    {formatSom(e.amount)}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button
                      onClick={() => setEditing(e)}
                      className="text-slate-400 hover:text-brand-600 mr-2"
                    >
                      <Pencil size={15} />
                    </button>
                    <button
                      onClick={() => remove(e)}
                      className="text-slate-300 hover:text-red-500"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Note>
        Ustozlar ish haqi bu yerga kiritilmaydi — u yoqlama asosida avtomatik
        hisoblanadi va foyda-zarar hisobotiga o'zi qo'shiladi.
      </Note>

      {showNew && (
        <ExpenseForm
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          defaultDate={defaultDate}
          onClose={() => setShowNew(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <ExpenseForm
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          defaultDate={defaultDate}
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
    </div>
  );
}


// -------------------------------------------------------------------- Page
export default function Moliya() {
  const { user } = useAuth();
  const full = can(user?.role, FINANCE_ACCESS);
  const TABS = [
    ...(full ? FULL_TABS : CASH_TABS),
    ...(can(user?.role, PAYMENT_LIST_VIEW) ? [PAID_TAB] : []),
    ...(can(user?.role, PAYROLL_VIEW) ? [PAYROLL_TAB] : []),
  ];
  // Asoschi va moliya direktori uchun birinchi sahifa — Umumiy ko'rinish
  const [tab, setTab] = useState<Tab>(full ? "overview" : "debtors");

  if (!can(user?.role, CASH_ACCESS)) {
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
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Moliya</h1>
      <p className="text-sm text-slate-500 mb-5">
        {full
          ? "Pul oqimi, foyda-zarar va xarajatlar"
          : "Qarzdorlar va oylik hisob-kitob"}
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

      {tab === "debtors" && <Debtors />}
      {tab === "cashflow" && <CashflowTab />}
      {tab === "pnl" && <PnlTab />}
      {tab === "expenses" && <ExpensesTab />}
      {tab === "billing" && <BillingTab />}
      {tab === "breakeven" && <BreakEvenTab />}
      {tab === "overview" && <FinanceOverviewTab />}
      {tab === "budget" && <BudgetTab />}
      {tab === "calendar" && <PaymentCalendarTab />}
      {tab === "paid" && <MonthPaymentsTab />}
      {tab === "payroll" && <PayrollTab />}
    </div>
  );
}


// ------------------------------------------- Oylik hisob-kitob ----
function BillingTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<BillingMonth | null>(null);
  const [col, setCol] = useState<CollectionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  function load() {
    setLoading(true);
    setMsg("");
    Promise.all([
      api
        .post<BillingMonth>(
          `/billing/month?year=${year}&month=${month}&commit=false`, {}
        )
        .then(setData),
      api
        .get<CollectionReport>(`/billing/collection?year=${year}&month=${month}`)
        .then(setCol)
        .catch(() => setCol(null)),
    ]).finally(() => setLoading(false));
  }
  useEffect(load, [year, month]);

  async function run() {
    if (
      !confirm(
        `${year}-${String(month).padStart(2, "0")} oyi uchun barcha faol ` +
          "o'quvchilardan pul hisoblansinmi?\n\n" +
          "Allaqachon hisoblanganlar takrorlanmaydi."
      )
    )
      return;
    setBusy(true);
    try {
      const r = await api.post<BillingMonth>(
        `/billing/month?year=${year}&month=${month}&commit=true`, {}
      );
      setMsg(`${r.created} ta o'quvchiga hisoblandi`);
      load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  const years = [now.getFullYear(), now.getFullYear() - 1];
  const pending = data?.rows.filter((r) => !r.already_charged).length ?? 0;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>
              {m}
            </option>
          ))}
        </select>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        {msg && <span className="text-sm text-slate-600">{msg}</span>}
        <div className="flex-1" />
        <button
          onClick={run}
          disabled={busy || pending === 0}
          className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-40"
        >
          {pending > 0
            ? `${pending} ta o'quvchiga hisoblash`
            : "Hammasi hisoblangan"}
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : !data ? null : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 mb-1">Tushishi kerak</p>
              <p className="text-lg font-semibold text-slate-900">
                {formatSom(data.expected_total)}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                {data.students} ta o'quvchi
              </p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 mb-1">Hisoblangan</p>
              <p className="text-lg font-semibold text-slate-900">
                {col ? formatSom(col.charged) : "—"}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 mb-1">Yig'ilgan</p>
              <p className="text-lg font-semibold text-emerald-600">
                {col ? formatSom(col.collected) : "—"}
              </p>
              {col && (
                <p className="text-xs text-slate-400 mt-0.5">{col.percent}%</p>
              )}
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 mb-1">Qolgan qarz</p>
              <p className="text-lg font-semibold text-red-600">
                {col ? formatSom(col.debt) : "—"}
              </p>
            </div>
          </div>

          <Note>
            Hisoblash o'quvchi balansidan pulni yechadi — balans manfiyga
            ketsa, bu qarz degani va Talabalar ro'yxatida qizil ko'rinadi.
            Bir oy uchun ikki marta hisoblanmaydi.
          </Note>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mt-4">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-xs text-slate-500">
                  <th className="text-left px-4 py-2.5">O'quvchi</th>
                  <th className="text-left">Guruh</th>
                  <th className="text-right w-20">Dars</th>
                  <th className="text-right w-24">Chegirma</th>
                  <th className="text-right w-32">Summa</th>
                  <th className="text-right pr-4 w-28">Holat</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={r.student_id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5">
                      <Link
                        to={`/students/${r.student_id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {r.full_name}
                      </Link>
                    </td>
                    <td className="text-slate-500">{r.group}</td>
                    <td className="text-right">{r.lessons}</td>
                    <td className="text-right text-emerald-600">
                      {r.discount ? `−${r.discount}%` : "—"}
                    </td>
                    <td className="text-right tabular-nums">
                      {formatSom(r.amount)}
                    </td>
                    <td className="text-right pr-4">
                      {r.already_charged ? (
                        <span className="text-xs text-emerald-600">
                          hisoblangan
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">kutilmoqda</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
