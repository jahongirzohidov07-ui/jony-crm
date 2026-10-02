import { useEffect, useState } from "react";
import {
  Download, Plus, X, Trash2, Pencil,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { Link, useSearchParams } from "react-router-dom";
import {
  api,
  getGlobalBranch,
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
  FINANCE_ACCESS, CASH_ACCESS, PAYMENT_LIST_VIEW, can, PAYMENT_EDIT, founderLike,
  SALARY_PAY } from "../lib/roles";
import Debtors from "./Debtors";
import {
  categoryLabel, categoriesByGroup, groupLabel, categoryGroup, MONTHS,
  isCountable,
} from "../lib/expenses";
import { formatSom, formatPeriodLabel, formatDate, formatDateTime } from "../lib/format";
import { methodLabel, MARKETING_CHANNELS, PAYMENT_METHODS } from "../lib/payments";
import { PayEditModal, type PayEditTarget } from "../components/PayEditModal";
import { exportToExcel } from "../lib/exportXlsx";
import { BreakEvenTab } from "../components/BreakEven";
import { FinanceOverviewTab } from "../components/FinanceOverview";
import { BudgetTab } from "../components/Budget";
import { PaymentCalendarTab } from "../components/PaymentCalendar";
import { MonthPaymentsTab } from "../components/Payroll";
import { QuickPayment } from "../components/QuickPayment";
import { PayImportTab } from "../components/PayImport";
import { CashDayCard } from "../components/CashDay";

type Tab = "overview" | "debtors" | "cashflow" | "pnl" | "expenses" | "billing" | "breakeven" | "budget" | "calendar" | "paid" | "lcup" | "trash" | "fixes";

/**
 * Administrator (sotuv menejeri) kassa bilan ishlaydi — qarzdorlar,
 * oylik hisob-kitob, PUL OQIMI va XARAJATLAR (2026-08-10, Jahongir:
 * "administratorlarga cashflow bo'limini ochib ber va xarajatlarni
 * kirgizishni ham ochib ber").
 *
 * Foyda-zarar, zararsizlik, budjet va oyliklar unga ATAYLAB
 * ko'rinmaydi — ular boshqa darajadagi ma'lumot.
 */
const CASH_TABS: { key: Tab; label: string }[] = [
  { key: "debtors", label: "Qarzdorlar" },
  { key: "cashflow", label: "Pul oqimi" },
  { key: "expenses", label: "Xarajatlar" },
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
// OYLIKLAR BO'LIMI HISOBOTLARGA KO'CHDI (2026-08-20, Jahongir:
// "uzr molyia bolimidan hisobotlarga olib ot demoqchi edim").
// Moliyada faqat kassa-hisob qoldi; barcha oyliklar - ustoz,
// examiner, support, ma'muriy - Hisobotlar > Oyliklar ichida.
// O'chirilgan to'lovlar arxivi (2026-08-15) - hech narsa yo'qolmaydi
const TRASH_TAB: { key: Tab; label: string } = {
  key: "trash", label: "O'chirilganlar",
};
// To'lovni tuzatish so'rovlari (2026-08-15)
const FIX_TAB: { key: Tab; label: string } = {
  key: "fixes", label: "Tuzatish so'rovlari",
};
// Eski tizimdan tarix ko'chirish — bir martalik ish, moliya bo'limida.
// 2026-08-18, Jahongir: "LC upda hammasini togrlab qoydim sen uni toliq
// kochirib ber JonyOS ga tolovlar tarixini". Ko'chirish ekrani (PayImport)
// allaqachon yozilgan edi, lekin hech qaysi sahifaga ULANMAGAN — ya'ni
// undan umuman foydalanib bo'lmasdi. Endi Moliya bo'limida tab bo'lib
// turadi. Faqat asoschi va moliya direktoriga ko'rinadi: eski tarixni
// ko'chirish - bir martalik va qaytarib olinadigan amal.
const LCUP_TAB: { key: Tab; label: string } = {
  key: "lcup", label: "LC UP tarixi",
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
    ...(data.opening
      ? [{ label: "Qoldiq", block: data.opening, cls: "bg-slate-100 text-slate-800" }]
      : []),
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
  if (r.direction === "balance") return "Oldingi oydan qoldiq";
  if (r.direction === "in") {
    return r.category === "new_payment" ? "Yangi to'lov" : "Eski to'lov";
  }
  if (r.category === "teacher_salary") return "Ustozlar oyligi";
  return "Xarajat";
}

function CashflowTab() {
  const now = new Date();
  const { user } = useAuth();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [filter, setFilter] = useState<"all" | "in" | "out">("all");
  const [data, setData] = useState<CashflowLedger | null>(null);
  const [trend, setTrend] = useState<CashflowReport | null>(null);
  const [loading, setLoading] = useState(true);
  // Xato kiritilgan kirim/chiqimni to'g'rilash (asoschi, moliyachi,
  // filial rahbari) - Jahongir so'radi
  const canPayEdit = can(user?.role, PAYMENT_EDIT);
  const [editing, setEditing] = useState<PayEditTarget | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // DAVR (2026-09-16, Jahongir: "faqat 1 oylikni koryabmiz shuni 2-3
  // oylikni toliq yillikni korsa boladigan qilib bergin").
  // 1 — bitta oy; 3/6 — tanlangan oy bilan tugaydigan oxirgi N oy;
  // 12 — tanlangan yilning yanvar–dekabri; 0 — erkin oraliq.
  const [span, setSpan] = useState<1 | 3 | 6 | 12 | 0>(1);
  const [fromY, setFromY] = useState(now.getFullYear());
  const [fromM, setFromM] = useState(1);
  const range = (() => {
    if (span === 1) return null;
    if (span === 12) return { fy: year, fm: 1, ty: year, tm: 12 };
    if (span === 0) return { fy: fromY, fm: fromM, ty: year, tm: month };
    const t = year * 12 + (month - 1) - (span - 1);
    return { fy: Math.floor(t / 12), fm: (t % 12) + 1, ty: year, tm: month };
  })();
  const qs = range
    ? `year=${range.fy}&month=${range.fm}&to_year=${range.ty}&to_month=${range.tm}`
    : `year=${year}&month=${month}`;
  const periodLabel = range
    ? `${MONTHS[range.fm - 1]} ${range.fy} — ${MONTHS[range.tm - 1]} ${range.ty}`
    : `${MONTHS[month - 1]} ${year}`;

  useEffect(() => {
    setLoading(true);
    api
      .get<CashflowLedger>(`/reports/cashflow-ledger?${qs}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [qs, reloadKey]);

  useEffect(() => {
    api
      .get<CashflowReport>("/reports/cashflow?months=6")
      .then(setTrend)
      .catch(() => setTrend(null));
  }, []);

  if (loading) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  if (!data) return null;

  // ENG YANGISI TEPADA, RAQAM BILAN (2026-09-16, Jahongir: "oy boshi
  // pastda oy oxiri tepada bolishi kerak shunda yangi kiritilgan boshida
  // turadi ... har bir tranzaksiyada raqam qoshilsin"). Raqam oy
  // boshidan sanaladi (1 — eng eski), shuning uchun yangi yozuv
  // qo'shilganda eskilarining raqami o'zgarmaydi.
  const numbered = data.rows.map((r, i) => ({ ...r, no: i + 1 }));
  const rows = (filter === "all"
    ? numbered
    : numbered.filter((r) => r.direction === filter)).slice().reverse();

  function exportRows() {
    exportToExcel(`kassa-${data!.period}${data!.period_to && data!.period_to !== data!.period ? `_${data!.period_to}` : ""}`, "Kassa",
      data!.rows.map((r) => ({
        Sana: r.date,
        Summa: r.amount,
        Izoh: r.title,
        Usul: methodLabel(r.method),
        Turi: r.direction === "balance" ? "Qoldiq"
          : r.direction === "in" ? "Kirim" : "Chiqim",
        Filial: r.branch,
        Kategoriya: ledgerCategoryLabel(r),
      })));
  }

  const years = [now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2];

  return (
    <div>
      {/* BUGUNGI TUSHUM (2026-09-05, Jahongir): kim to'ladi, qancha,
          naqd/Click/terminal — kunlik kassa oylik jadvalning tepasida. */}
      <CashDayCard reloadKey={reloadKey} />

      {/* --- Davr tanlash --- */}
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5">
          {([
            [1, "Oy"], [3, "3 oy"], [6, "6 oy"], [12, "Yil"], [0, "Oraliq"],
          ] as const).map(([k, l]) => (
            <button
              key={k}
              onClick={() => setSpan(k)}
              className={`px-2.5 py-1.5 rounded-md text-xs font-medium ${
                span === k ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        {span === 0 && (
          <>
            <select
              value={fromM}
              onChange={(e) => setFromM(Number(e.target.value))}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              {MONTHS.map((m, i) => (
                <option key={m} value={i + 1}>{m}</option>
              ))}
            </select>
            <select
              value={fromY}
              onChange={(e) => setFromY(Number(e.target.value))}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              {years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
            <span className="text-sm text-slate-400">dan</span>
          </>
        )}
        {span !== 12 && (
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
        )}
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
        {span !== 1 && (
          <span className="text-sm text-slate-500">
            {span === 0 ? "gacha · " : ""}{periodLabel}
          </span>
        )}
        <div className="flex-1" />
        {/* Kirim-chiqim ro'yxatining o'zida ham to'lov qabul qilinadi -
            administrator sahifa almashtirmasin. */}
        <QuickPayment onDone={() => setReloadKey((k) => k + 1)} />
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
          Qoldiq — oldingi oydan qolgan pul (1-sentabr 2026 dan yuritiladi).
          Kassa = qoldiq + kirim − chiqim, har bir usul bo'yicha alohida.
          Chiqimga xarajatlar va haqiqatda berilgan ustoz oyliklari kiradi.
        </Note>
      </div>

      {/* --- Oylar kesimi (oraliq tanlanganda) --- */}
      {data.months && data.months.length > 1 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
          <p className="text-sm font-medium text-slate-700">Oylar kesimida</p>
          <p className="text-xs text-slate-400 mb-3">{periodLabel}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-500 border-b border-slate-100">
                  <th className="text-left py-2">Oy</th>
                  <th className="text-right">Qoldiq</th>
                  <th className="text-right">Kirim</th>
                  <th className="text-right">Chiqim</th>
                  <th className="text-right">Kassa</th>
                  <th className="text-right">Yozuv</th>
                </tr>
              </thead>
              <tbody>
                {data.months.map((m) => (
                  <tr key={m.period} className="border-b border-slate-50">
                    <td className="py-2 text-slate-700">{m.title}</td>
                    <td className="text-right tabular-nums text-slate-600">{formatSom(m.opening ?? 0)}</td>
                    <td className="text-right tabular-nums text-emerald-700">{formatSom(m.kirim)}</td>
                    <td className="text-right tabular-nums text-red-700">{formatSom(m.chiqim)}</td>
                    <td className={`text-right tabular-nums font-medium ${m.kassa < 0 ? "text-red-700" : "text-slate-900"}`}>
                      {formatSom(m.kassa)}
                    </td>
                    <td className="text-right text-slate-400">{m.count}</td>
                  </tr>
                ))}
                <tr className="font-semibold">
                  <td className="py-2">Jami</td>
                  <td className="text-right tabular-nums text-slate-600">{formatSom(data.opening?.total ?? 0)}</td>
                  <td className="text-right tabular-nums text-emerald-700">{formatSom(data.kirim.total)}</td>
                  <td className="text-right tabular-nums text-red-700">{formatSom(data.chiqim.total)}</td>
                  <td className="text-right tabular-nums">{formatSom(data.kassa.total)}</td>
                  <td className="text-right text-slate-400">{data.rows.length}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

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
            Bu davrda yozuv yo'q
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-xs text-slate-500">
                  <th className="text-right pl-3 pr-1 py-2 w-12">№</th>
                  <th className="text-left px-4 py-2 w-28">Sana</th>
                  <th className="text-right w-36 pr-6">Summa</th>
                  <th className="text-left pl-2">Izoh</th>
                  <th className="text-left w-28">Usul</th>
                  <th className="text-left w-24">Turi</th>
                  <th className="text-left w-32">Filial</th>
                  <th className="text-left w-32">Kategoriya</th>
                  <th className="w-8"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const bal = r.direction === "balance";
                  const inRow = r.direction === "in";
                  const bg = bal
                    ? "bg-slate-50 hover:bg-slate-100"
                    : inRow
                    ? "bg-emerald-50 hover:bg-emerald-100"
                    : "bg-red-50 hover:bg-red-100";
                  const fg = bal ? "text-slate-800" : inRow ? "text-emerald-900" : "text-red-900";
                  return (
                    <tr
                      key={r.id}
                      className={`border-t border-white ${bg} ${fg} transition`}
                    >
                      <td className="pl-3 pr-1 py-2 text-right text-xs tabular-nums opacity-60">
                        {r.no}
                      </td>
                      <td className="px-4 py-2">{formatDate(r.date)}</td>
                      <td className="text-right font-medium tabular-nums pr-6">
                        {bal ? "" : inRow ? "+" : "−"}
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
                      <td className="font-medium">
                        {bal ? "Qoldiq" : inRow ? "Kirim" : "Chiqim"}
                      </td>
                      <td>{r.branch}</td>
                      <td>{ledgerCategoryLabel(r)}</td>
                      <td className="pr-3 text-right">
                        {canPayEdit && !bal && (
                          <button
                            onClick={() =>
                              setEditing({
                                kind: r.id.startsWith("e")
                                  ? "expense"
                                  : "payment",
                                id: Number(r.id.slice(1)),
                                amount: r.amount,
                                method: r.method,
                                note: r.note,
                                title: r.title,
                              })
                            }
                            className="opacity-40 hover:opacity-100"
                            title="Tahrirlash (summa, usul, izoh)"
                          >
                            <Pencil size={13} />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {editing && (
        <PayEditModal
          target={editing}
          onClose={() => setEditing(null)}
          onSaved={() => setReloadKey((k) => k + 1)}
        />
      )}

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
/** Oylik beriladigan xodim (ustoz ham, ma'muriy xodim ham). */
type StaffPayee = {
  key: string;
  teacher_id: number | null;
  user_id: number | null;
  name: string;
  role_label: string;
  branch?: string | null;
  to_salary_card: boolean;
};

const EXPENSE_SALARY_KEYS = ["admin_salary", "support_salary", "salary"];

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
  // FILIAL: tepadagi tanlagichda aniq filial turgan bo'lsa, xarajat
  // o'shanga yoziladi va savol berilmaydi (Jahongir, 2026-08-12:
  // "men hozir Bekobod 1 da ishlayabman demak bekobod 1 xarajati
  // bo'ladi, agar barcha filiallarni tanlab ishlaganimda filial
  // so'rasa bo'lardi").
  const globalBranch = getGlobalBranch();
  const lockedBranch = !initial && !!globalBranch;
  const [branchId, setBranchId] = useState(
    initial?.branch_id
      ? String(initial.branch_id)
      : globalBranch
      ? String(globalBranch)
      : defaultBranchId
      ? String(defaultBranchId)
      : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---- IKKI YO'L: OYLIK yoki XARAJAT (Jahongir, 2026-08-12:
  // "bitta tanlaydigan qilish kerak unda 2ta variant boladi oylik
  // yoki xarajat").
  const [mode, setMode] = useState<"salary" | "expense">(
    initial && EXPENSE_SALARY_KEYS.includes(initial.category)
      ? "salary" : "expense");
  const [staff, setStaff] = useState<StaffPayee[]>([]);
  const [payee, setPayee] = useState<StaffPayee | null>(null);
  const [staffQ, setStaffQ] = useState("");
  // Soni va kitob
  const [qty, setQty] = useState("");
  const [books, setBooks] = useState<{ id: number; name: string; qty: number }[]>([]);
  const [bookId, setBookId] = useState("");
  const [newBook, setNewBook] = useState("");

  useEffect(() => {
    if (mode !== "salary" || staff.length) return;
    api.get<{ rows: StaffPayee[] }>(
      `/expenses/staff${branchId ? `?branch_id=${branchId}` : ""}`)
      .then((r) => setStaff(r.rows || []))
      .catch(() => setStaff([]));
  }, [mode, branchId]);

  useEffect(() => {
    if (category !== "book" || books.length) return;
    api.get<{ id: number; name: string; qty: number }[]>("/consumables/books")
      .then(setBooks)
      .catch(() => setBooks([]));
  }, [category]);

  async function save() {
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("To'g'ri summa kiriting");
      return;
    }
    if (mode === "salary" && !payee) {
      setError("Kimga oylik berilayotganini tanlang");
      return;
    }
    if (mode === "expense" && category === "book" && !bookId && !newBook.trim()) {
      setError("Qaysi kitob ekanini tanlang");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const salary = mode === "salary";
      const body = {
        date,
        category: salary ? "admin_salary" : category,
        amount: value,
        note: note || null,
        method,
        // Kanal faqat reklama xarajatida ma'noga ega - CAC shundan
        // hisoblanadi. Boshqa turda tozalab yuboramiz.
        channel: !salary && categoryGroup(category) === "marketing"
          ? channel || null : null,
        branch_id: branchId ? Number(branchId) : null,
        teacher_id: salary ? payee?.teacher_id ?? null : null,
        staff_user_id: salary && !payee?.teacher_id
          ? payee?.user_id ?? null : null,
        period: salary ? date.slice(0, 7) : null,
        qty: !salary && qty ? Number(qty) : null,
        consumable_id: !salary && category === "book" && bookId
          ? Number(bookId) : null,
        new_item_name: !salary && category === "book" && !bookId
          ? newBook.trim() || null : null,
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
            {editing
              ? "Xarajatni tahrirlash"
              : mode === "salary" ? "Oylik berish" : "Yangi xarajat"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          {/* 1-QADAM: oylik yoki xarajat */}
          <div className="grid grid-cols-2 gap-2">
            {([
              ["salary", "Oylik", "Xodimga berilgan pul"],
              ["expense", "Xarajat", "Ijara, kommunal, kanstovar…"],
            ] as const).map(([k, label, hint]) => (
              <button
                key={k}
                type="button"
                onClick={() => { setMode(k); setError(null); }}
                className={`rounded-xl border p-3 text-left transition ${
                  mode === k
                    ? "bg-brand-50 border-brand-400"
                    : "bg-white border-slate-200 hover:border-slate-300"
                }`}
              >
                <p className={`text-sm font-medium ${
                  mode === k ? "text-brand-700" : "text-slate-700"}`}>
                  {label}
                </p>
                <p className="text-[11px] text-slate-400">{hint}</p>
              </button>
            ))}
          </div>

          {/* OYLIK: shu filial xodimlari */}
          {mode === "salary" && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Kimga
              </label>
              {payee ? (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-brand-300 bg-brand-50">
                  <span className="text-sm text-slate-800 flex-1 truncate">
                    {payee.name}
                    <span className="text-xs text-slate-500">
                      {" "}· {payee.role_label}
                    </span>
                  </span>
                  <button type="button" onClick={() => setPayee(null)}
                          className="text-slate-400 hover:text-red-600">
                    <X size={15} />
                  </button>
                </div>
              ) : (
                <>
                  <input
                    value={staffQ}
                    onChange={(e) => setStaffQ(e.target.value)}
                    placeholder="Ism yoki lavozim bo'yicha qidiring…"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                  <div className="mt-1 border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-56 overflow-y-auto">
                    {staff
                      .filter((x) => {
                        const q = staffQ.trim().toLowerCase();
                        if (!q) return true;
                        return (x.name || "").toLowerCase().includes(q)
                          || (x.role_label || "").toLowerCase().includes(q);
                      })
                      .slice(0, 40)
                      .map((x) => (
                        <button
                          key={x.key}
                          type="button"
                          onClick={() => setPayee(x)}
                          className="w-full text-left px-3 py-2 hover:bg-slate-50"
                        >
                          <p className="text-sm text-slate-800">{x.name}</p>
                          <p className="text-xs text-slate-400">
                            {x.role_label}
                            {x.branch ? ` · ${x.branch}` : ""}
                            {x.to_salary_card ? " · oylik kartasiga tushadi" : ""}
                          </p>
                        </button>
                      ))}
                    {staff.length === 0 && (
                      <p className="px-3 py-2 text-xs text-slate-400">
                        Xodimlar yuklanmoqda…
                      </p>
                    )}
                  </div>
                </>
              )}
              {payee?.to_salary_card && (
                <p className="text-[11px] text-emerald-700 mt-1">
                  Bu pul {payee.name}ning oylik kartasida ham ko'rinadi.
                </p>
              )}
            </div>
          )}

          {/* XARAJAT: turlar ro'yxati */}
          {mode === "expense" && (
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">
              Xarajat turi
            </label>
            {/* Xodim oyligi faqat "Oylik" orqali, ism tanlab (2026-09-16) —
                ism izohga qo'lda yozilsa ustoz oyligi ham shu turga tushib
                qolardi. Farrosh/qorovul (akkaunti yo'q) shu yerda qoladi. */}
            {categoriesByGroup()
              .map((g) => ({ ...g, items: g.items.filter((c) => c.key !== "admin_salary") }))
              .filter((g) => g.items.length > 0)
              .map((g) => (
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
          )}

          {/* KITOB: qaysi kitob (Multilevel, Round-up...) */}
          {mode === "expense" && category === "book" && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Qaysi kitob
              </label>
              <select
                value={bookId}
                onChange={(e) => setBookId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                <option value="">— ro'yxatda yo'q, nomini yozaman —</option>
                {books.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} (omborda {b.qty})
                  </option>
                ))}
              </select>
              {!bookId && (
                <input
                  value={newBook}
                  onChange={(e) => setNewBook(e.target.value)}
                  placeholder="Yangi kitob nomi (masalan: Round-up 4)"
                  className="w-full mt-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              )}
              <p className="text-[11px] text-slate-400 mt-1">
                Sotib olingan kitoblar OMBOR qoldig'iga qo'shiladi.
              </p>
            </div>
          )}

          {/* SONI — sanaladigan xarajatlarda */}
          {mode === "expense" && isCountable(category) && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Soni
              </label>
              <input
                type="number"
                min="0"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                placeholder="Masalan: 3"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}

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

          {mode === "expense" && categoryGroup(category) === "marketing" && (
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

          {lockedBranch ? (
            <p className="text-xs text-slate-500">
              Filial:{" "}
              <span className="font-medium text-slate-700">
                {branches.find((b) => String(b.id) === branchId)?.name
                  || "—"}
              </span>{" "}
              — tepadagi tanlovga ko'ra. Boshqa filialga yozish uchun
              tepadan "Barcha filiallar" ni tanlang.
            </p>
          ) : branches.length > 1 && (
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
      .get<Expense[]>(`/expenses?year=${year}&month=${month}&with_teacher=1`)
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

  // Ustozga berilgan pulning filialini to'g'rilash (2026-09-16):
  // ilgari asosiy filialga yozilib qolganlar uchun.
  const canPay = can(user?.role, SALARY_PAY);
  async function moveBranch(e: Expense, branchId: number) {
    try {
      await api.put(`/teacher-payments/${-e.id}/branch`, { branch_id: branchId });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik");
    }
  }

  async function remove(e: Expense) {
    if (!confirm(`${categoryLabel(e.category)} — ${formatSom(e.amount)} o'chirilsinmi?`))
      return;
    try {
      // Manfiy id — ustozga berilgan pul, u ustozning oylik kartasida
      if (e.id < 0) await api.delete(`/teacher-payments/${-e.id}`);
      else await api.delete(`/expenses/${e.id}`);
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
                  <td className="px-4 py-3 text-slate-500">
                    {e.id < 0 && canPay && branches.length > 1 ? (
                      <select
                        value={e.branch_id ?? ""}
                        onChange={(ev) => moveBranch(e, Number(ev.target.value))}
                        title="Qaysi filialdan berilgan — o'zgartirish mumkin"
                        className="rounded-md border border-slate-200 bg-white px-1.5 py-1 text-sm text-slate-600"
                      >
                        {branches.map((b) => (
                          <option key={b.id} value={b.id}>{b.name}</option>
                        ))}
                      </select>
                    ) : (
                      e.branch?.name || "—"
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-slate-800">
                    {formatSom(e.amount)}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {e.id < 0 ? (
                      <span
                        className="inline-block w-[15px] mr-2"
                        title="Ustoz oyligi — ustozning oylik kartasidan tahrirlanadi"
                      />
                    ) : (
                      <button
                        onClick={() => setEditing(e)}
                        className="text-slate-400 hover:text-brand-600 mr-2"
                      >
                        <Pencil size={15} />
                      </button>
                    )}
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
        Ustozga oylik "Oylik" tugmasi orqali ustozni tanlab beriladi — u shu
        ro'yxatda "Ustoz oyligi" bo'lib ismi bilan ko'rinadi va ustozning
        oylik kartasiga tushadi. Foyda-zarardagi ustozlar ish haqi esa
        yo'qlamadan avtomatik hisoblanadi, shuning uchun ikki marta ayirilmaydi.
        Xato "Ma'muriy xodim oyligi" bo'lib kiritilgan bo'lsa — qalamchani
        bosib, ustozni tanlang: pul ustoz oyligiga ko'chadi.
      </Note>

      {showNew && (
        <ExpenseForm
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          defaultDate={defaultDate}
          onClose={() => setShowNew(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <ExpenseForm
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
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
    ...(full ? [TRASH_TAB] : []),
    ...(can(user?.role, CASH_ACCESS) ? [FIX_TAB] : []),
    ...(full ? [LCUP_TAB] : []),
  ];
  // Asoschi va moliya direktori uchun birinchi sahifa — Umumiy ko'rinish.
  // Dashboard kartasidan kelganda ?tab= orqali kerakli bo'lim ochiladi.
  const [sp] = useSearchParams();
  const [payKey, setPayKey] = useState(0);
  const _urlTab = sp.get("tab");
  const [tab, setTab] = useState<Tab>(
    _urlTab && TABS.some((t) => t.key === _urlTab)
      ? (_urlTab as Tab)
      : full ? "overview" : "debtors");

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
      {/* To'lov qabul qilish tugmasi Moliyaning HAR BIR bo'limida
          ko'rinib turadi. Ilgari u faqat yon menyuning tepasida edi va
          administrator qarzdorlar yoki pul oqimida turib to'lov kirita
          olmasdi (Jahongir, 2026-08-12: "oson bolsin topish").
          To'lovdan keyin ochiq bo'lim qayta yuklanadi - payKey. */}
      <div className="flex items-start gap-3 mb-1">
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold text-slate-900 mb-1">Moliya</h1>
          <p className="text-sm text-slate-500">
            {full
              ? "Pul oqimi, foyda-zarar va xarajatlar"
              : "Qarzdorlar va oylik hisob-kitob"}
          </p>
        </div>
        <QuickPayment onDone={() => setPayKey((k) => k + 1)} />
      </div>
      <div className="h-4" />

      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            data-guide={"ftab-" + t.key}
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

      <div key={payKey}>
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
        {tab === "trash" && <DeletedPaymentsTab />}
        {tab === "fixes" && <PaymentFixesTab />}
        {tab === "lcup" && <PayImportTab />}
      </div>
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
  // Eski o'quvchilarni ro'yxatga endi kiritganda: ular oyning
  // boshidan o'qigan, shuning uchun to'liq oy uchun hisoblanadi.
  const [whole, setWhole] = useState(false);

  function load() {
    setLoading(true);
    setMsg("");
    Promise.all([
      api
        .post<BillingMonth>(
          `/billing/month?year=${year}&month=${month}&commit=false` +
            `&whole_month=${whole}`, {}
        )
        .then(setData),
      api
        .get<CollectionReport>(`/billing/collection?year=${year}&month=${month}`)
        .then(setCol)
        .catch(() => setCol(null)),
    ]).finally(() => setLoading(false));
  }
  useEffect(load, [year, month, whole]);

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
        `/billing/month?year=${year}&month=${month}&commit=true` +
          `&whole_month=${whole}`, {}
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
        <label className="flex items-center gap-1.5 text-sm text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={whole}
            onChange={(e) => setWhole(e.target.checked)}
            className="rounded border-slate-300"
          />
          To'liq oy uchun
        </label>
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

          {(data.no_lesson ?? 0) > 0 && (
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mt-1">
              {data.no_lesson} ta o'quvchining guruhida bu oyda dars kuni
              yo'q — ularga pul hisoblanmaydi. Guruh kartasida dars
              kunlari (Du/Chor/Ju) va boshlanish sanasi to'g'ri
              qo'yilganini tekshiring.
            </p>
          )}

          <Note>
            Hisoblash o'quvchi balansidan pulni yechadi — balans manfiyga
            ketsa, bu qarz degani va Talabalar ro'yxatida qizil ko'rinadi.
            Bir oy uchun ikki marta hisoblanmaydi.{" "}
            <b>To'liq oy uchun</b> belgisi qo'yilsa, oy o'rtasida
            qo'shilgan o'quvchi ham butun oy uchun to'laydi — eski
            o'quvchilarni tizimga endi kiritganda shu kerak bo'ladi.
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

      <LegacyCollectionArchive />
    </div>
  );
}

// ---------------------- Eski yillar to'lov arxivi (import) ----
// Jahongirning eski Google Sheets jadvalidan kiritilgan reja/fakt.
// Faqat moliya ruxsati borlarga API javob beradi - boshqalarga
// bo'lim umuman ko'rinmaydi.
type LegacyBlock = {
  label: string;
  year: number;
  months: { month: number; plan: number; fact: number; percent: number | null }[];
  plan: number;
  fact: number;
  percent: number | null;
};

function pctTone(p: number | null): string {
  if (p == null) return "text-slate-400";
  if (p >= 98) return "text-emerald-600";
  if (p >= 90) return "text-sky-600";
  if (p >= 80) return "text-amber-600";
  return "text-rose-600";
}

function LegacyCollectionArchive() {
  const [blocks, setBlocks] = useState<LegacyBlock[] | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ blocks: LegacyBlock[] }>("/billing/collection-legacy")
      .then((r) => setBlocks(r.blocks))
      .catch(() => setBlocks(null));
  }, []);

  if (!blocks || blocks.length === 0) return null;

  return (
    <div className="mt-8">
      <h3 className="text-sm font-semibold text-slate-900 mb-1">
        Eski yillar arxivi — to'lov yig'ilishi
      </h3>
      <p className="text-xs text-slate-500 mb-3">
        Eski jadvaldan import qilingan: qancha tushishi kerak edi va
        qancha tushdi. Foiz reja/faktdan hisoblanadi.
      </p>
      <div className="grid gap-2 sm:grid-cols-2">
        {blocks.map((b) => {
          const key = `${b.year}-${b.label}`;
          const opened = open === key;
          return (
            <div
              key={key}
              className="rounded-xl border border-slate-200 bg-white overflow-hidden"
            >
              <button
                onClick={() => setOpen(opened ? null : key)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50"
              >
                <div>
                  <div className="text-sm font-medium text-slate-900">
                    {b.year} — {b.label}
                  </div>
                  <div className="text-xs text-slate-500">
                    Reja {short(b.plan)} · Fakt {short(b.fact)}
                  </div>
                </div>
                <span
                  className={`text-base font-semibold tabular-nums ${pctTone(b.percent)}`}
                >
                  {b.percent != null ? `${b.percent}%` : "—"}
                </span>
              </button>
              {opened && (
                <table className="w-full text-xs border-t border-slate-100">
                  <thead>
                    <tr className="text-slate-400">
                      <th className="text-left font-medium pl-4 py-1.5">Oy</th>
                      <th className="text-right font-medium">Reja</th>
                      <th className="text-right font-medium">Fakt</th>
                      <th className="text-right font-medium pr-4">Foiz</th>
                    </tr>
                  </thead>
                  <tbody>
                    {b.months.map((m) => (
                      <tr key={m.month} className="border-t border-slate-50">
                        <td className="pl-4 py-1.5 text-slate-600">
                          {MONTHS[m.month - 1]}
                        </td>
                        <td className="text-right tabular-nums text-slate-600">
                          {formatSom(m.plan)}
                        </td>
                        <td className="text-right tabular-nums text-slate-600">
                          {formatSom(m.fact)}
                        </td>
                        <td
                          className={`text-right pr-4 tabular-nums font-medium ${pctTone(m.percent)}`}
                        >
                          {m.percent != null ? `${m.percent}%` : "—"}
                        </td>
                      </tr>
                    ))}
                    <tr className="border-t border-slate-200 font-semibold">
                      <td className="pl-4 py-2 text-slate-900">Umumiy</td>
                      <td className="text-right tabular-nums text-slate-900">
                        {formatSom(b.plan)}
                      </td>
                      <td className="text-right tabular-nums text-slate-900">
                        {formatSom(b.fact)}
                      </td>
                      <td
                        className={`text-right pr-4 tabular-nums ${pctTone(b.percent)}`}
                      >
                        {b.percent != null ? `${b.percent}%` : "—"}
                      </td>
                    </tr>
                  </tbody>
                </table>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}


// ------------------------------- O'chirilgan to'lovlar arxivi ----
// 2026-08-15, Jahongir'ning asosiy qoidasi: "hech narsa o'chmasin".
// Ilgari xato yozuv butunlay yo'q bo'lardi - endi shu yerda turadi:
// kim o'chirgan, qachon, nima sababdan. Asoschi qaytara oladi.
interface DeletedPay {
  id: number;
  payment_id: number;
  public_id?: string | null;
  student_id?: number | null;
  student_name?: string | null;
  amount: number;
  kind?: string | null;
  method?: string | null;
  note?: string | null;
  period?: string | null;
  created_by?: string | null;
  created_at?: string | null;
  deleted_by?: string | null;
  deleted_at?: string | null;
  reason?: string | null;
  restored_at?: string | null;
  restored_by?: string | null;
}

function DeletedPaymentsTab() {
  const { user } = useAuth();
  const [rows, setRows] = useState<DeletedPay[] | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const isFounder = founderLike(user?.role);

  const load = () => {
    api
      .fresh<DeletedPay[]>("/payments/deleted?limit=300")
      .then(setRows)
      .catch(() => setRows([]));
  };
  useEffect(load, []);

  async function restore(r: DeletedPay) {
    if (
      !confirm(
        `${r.student_name || "O'quvchi"} - ${formatSom(r.amount)}\n` +
          "Bu yozuv qaytarilsinmi? Balans darrov o'zgaradi."
      )
    )
      return;
    setBusy(r.id);
    try {
      await api.post(`/payments/deleted/${r.id}/restore`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  if (rows === null)
    return <p className="p-8 text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div className="p-8">
      <h2 className="text-base font-semibold text-slate-900">
        O'chirilgan to'lovlar
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        O'chirilgan yozuv yo'qolmaydi — shu yerda saqlanadi. Xato
        o'chirilgan bo'lsa, asoschi uni qaytara oladi.
      </p>

      {rows.length === 0 ? (
        <p className="mt-6 text-sm text-slate-400">
          Hozircha o'chirilgan yozuv yo'q.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="px-3 py-2 text-left">O'quvchi</th>
                <th className="px-3 py-2 text-right">Summa</th>
                <th className="px-3 py-2 text-left">Turi</th>
                <th className="px-3 py-2 text-left">Kim o'chirdi</th>
                <th className="px-3 py-2 text-left">Qachon</th>
                <th className="px-3 py-2 text-left">Sabab</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.id}
                  className={`border-t border-slate-100 ${
                    r.restored_at ? "opacity-50" : ""
                  }`}
                >
                  <td className="px-3 py-2">
                    {r.student_id ? (
                      <Link
                        to={`/students/${r.student_id}`}
                        className="text-brand-700 hover:underline"
                      >
                        {r.student_name || "—"}
                      </Link>
                    ) : (
                      r.student_name || "—"
                    )}
                    {r.note && (
                      <span className="block text-xs text-slate-400">
                        {r.note}
                      </span>
                    )}
                  </td>
                  <td
                    className={`px-3 py-2 text-right font-medium ${
                      r.amount < 0 ? "text-red-600" : "text-emerald-600"
                    }`}
                  >
                    {formatSom(r.amount)}
                  </td>
                  <td className="px-3 py-2 text-slate-500">
                    {r.kind === "charge"
                      ? "Hisoblangan"
                      : r.kind === "discount"
                        ? "Chegirma"
                        : r.kind === "adjustment"
                          ? "Balans tuzatildi"
                          : "To'lov"}
                    {r.period ? ` · ${r.period}` : ""}
                  </td>
                  <td className="px-3 py-2 text-slate-600">
                    {r.deleted_by || "—"}
                  </td>
                  <td className="px-3 py-2 text-slate-500">
                    {r.deleted_at ? formatDateTime(r.deleted_at) : "—"}
                  </td>
                  <td className="px-3 py-2 text-slate-500">
                    {r.reason || <span className="text-slate-300">—</span>}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {r.restored_at ? (
                      <span className="text-xs text-slate-400">
                        Qaytarilgan
                      </span>
                    ) : isFounder ? (
                      <button
                        onClick={() => restore(r)}
                        disabled={busy === r.id}
                        className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                      >
                        {busy === r.id ? "…" : "Qaytarish"}
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


// ------------------------------ To'lovni tuzatish so'rovlari ----
// 2026-08-15, Jahongir: "sotuv manager tolovni notogri urvordi, shuni
// ozgartirish qilib sorov yuborsa filial rahbari yoki moliyachiga
// borsa yoki asoschiga tasdiqlavorsa ozgarsin, chunki shunaqa holat
// boldi u menga aloqaga chiqadi men uni topaman ozgartiraman vaqt
// ketadi".
interface FixRow {
  id: number;
  public_id?: string | null;
  payment_id: number;
  payment_exists: boolean;
  student_id?: number | null;
  student?: string | null;
  kind: string;
  kind_label: string;
  what: string;
  reason: string;
  status: string;
  requested_by?: string | null;
  created_at?: string | null;
  decided_by?: string | null;
  decided_at?: string | null;
  decision_note?: string | null;
  can_approve: boolean;
}

function PaymentFixesTab() {
  const [rows, setRows] = useState<FixRow[] | null>(null);
  const [status, setStatus] = useState("pending");
  const [busy, setBusy] = useState<number | null>(null);

  const load = () => {
    api
      .fresh<FixRow[]>(`/payments/fix-requests?status=${status}`)
      .then(setRows)
      .catch(() => setRows([]));
  };
  useEffect(load, [status]);

  async function decide(r: FixRow, ok: boolean) {
    if (ok) {
      if (!confirm(`${r.what}\n\nTasdiqlansinmi? O'zgarish darrov qo'llanadi.`))
        return;
    }
    const note = ok ? null : prompt("Rad etish sababi (ixtiyoriy):", "");
    if (!ok && note === null) return;
    setBusy(r.id);
    try {
      await api.post(
        `/payments/fix-requests/${r.id}/${ok ? "approve" : "reject"}`,
        { note }
      );
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  if (rows === null)
    return <p className="p-8 text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div className="p-8">
      <h2 className="text-base font-semibold text-slate-900">
        To'lovni tuzatish so'rovlari
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Xato kiritilgan to'lovni tahrirlash huquqi yo'q xodim shu yerga
        so'rov yuboradi. Tasdiqlansa o'zgarish darrov qo'llanadi —
        kimnidir qidirib, telefon qilib o'tirish shart emas.
      </p>

      <div className="mt-4 flex items-center gap-2">
        {[
          ["pending", "Kutilmoqda"],
          ["approved", "Tasdiqlangan"],
          ["rejected", "Rad etilgan"],
          ["all", "Hammasi"],
        ].map(([k, lbl]) => (
          <button
            key={k}
            onClick={() => setStatus(k)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
              status === k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {lbl}
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="mt-6 text-sm text-slate-400">So'rov yo'q.</p>
      ) : (
        <div className="mt-4 space-y-2">
          {rows.map((r) => (
            <div
              key={r.id}
              className="rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900">
                    {r.student_id ? (
                      <Link
                        to={`/students/${r.student_id}`}
                        className="text-brand-700 hover:underline"
                      >
                        {r.student || "O'quvchi"}
                      </Link>
                    ) : (
                      r.student || "—"
                    )}
                    <span className="ml-2 text-slate-500 font-normal">
                      {r.what}
                    </span>
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Sabab: {r.reason}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-400">
                    So'ragan: {r.requested_by || "—"}
                    {r.created_at ? ` · ${formatDateTime(r.created_at)}` : ""}
                    {!r.payment_exists && (
                      <span className="text-amber-600">
                        {" "}
                        · yozuv topilmadi
                      </span>
                    )}
                  </p>
                  {r.status !== "pending" && (
                    <p className="mt-1 text-xs text-slate-500">
                      {r.status === "approved" ? "Tasdiqladi" : "Rad etdi"}:{" "}
                      {r.decided_by || "—"}
                      {r.decided_at ? ` · ${formatDateTime(r.decided_at)}` : ""}
                      {r.decision_note ? ` · ${r.decision_note}` : ""}
                    </p>
                  )}
                </div>
                {r.status === "pending" && r.can_approve && (
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => decide(r, true)}
                      disabled={busy === r.id}
                      className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                    >
                      Tasdiqlash
                    </button>
                    <button
                      onClick={() => decide(r, false)}
                      disabled={busy === r.id}
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                    >
                      Rad etish
                    </button>
                  </div>
                )}
                {r.status === "pending" && !r.can_approve && (
                  <span className="text-xs text-amber-600 shrink-0">
                    tasdiq kutilmoqda
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
