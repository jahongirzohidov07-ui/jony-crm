import { useEffect, useState } from "react";
import {
  Download, Banknote, CreditCard, Smartphone, Wallet, Plus, X, Trash2, Pencil,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import {
  api,
  type CashflowReport,
  type PnlReport,
  type Expense,
  type Branch,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, can } from "../lib/roles";
import {
  categoryLabel, categoriesByGroup, groupLabel, categoryGroup, MONTHS,
} from "../lib/expenses";
import { formatSom, formatPeriodLabel, formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "cashflow" | "pnl" | "expenses";

const TABS: { key: Tab; label: string }[] = [
  { key: "cashflow", label: "Pul oqimi" },
  { key: "pnl", label: "Foyda / zarar" },
  { key: "expenses", label: "Xarajatlar" },
];

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
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Moliya</h1>
      <p className="text-sm text-slate-500 mb-5">
        Pul oqimi, foyda-zarar va xarajatlar
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

      {tab === "cashflow" && <CashflowTab />}
      {tab === "pnl" && <PnlTab />}
      {tab === "expenses" && <ExpensesTab />}
    </div>
  );
}
