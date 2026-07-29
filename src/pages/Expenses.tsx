import { useEffect, useState } from "react";
import { Plus, X, Trash2, Pencil } from "lucide-react";
import { api } from "../lib/api";
import type { Expense, Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, can } from "../lib/roles";
import { EXPENSE_CATEGORIES, categoryLabel, MONTHS } from "../lib/expenses";
import { formatSom, formatDate } from "../lib/format";

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
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {editing ? "Xarajatni tahrirlash" : "Yangi xarajat"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Turi</label>
            <div className="flex flex-wrap gap-1.5">
              {EXPENSE_CATEGORIES.map((c) => (
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
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Filial
              </label>
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
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-1 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : editing ? "Saqlash" : "Qo'shish"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Expenses() {
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

  const allowed = can(user?.role, FINANCE_ACCESS);
  if (!allowed) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  const total = items.reduce((s, e) => s + e.amount, 0);

  // Tur bo'yicha yig'indi - qaysi moddaga ko'p ketayotgani darrov ko'rinsin.
  const byCategory = EXPENSE_CATEGORIES.map((c) => ({
    ...c,
    sum: items.filter((e) => e.category === c.key).reduce((s, e) => s + e.amount, 0),
  })).filter((c) => c.sum > 0);

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
    <div className="p-8 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Xarajatlar</h1>
          <p className="text-sm text-slate-500">
            {MONTHS[month - 1]} {year} · jami {formatSom(total)}
          </p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          <Plus size={16} /> Yangi xarajat
        </button>
      </div>

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

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {byCategory.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {byCategory.map((c) => (
            <div
              key={c.key}
              className="bg-white border border-slate-200 rounded-lg px-3 py-2"
            >
              <p className="text-xs text-slate-500">{c.label}</p>
              <p className="text-sm font-semibold text-slate-800">
                {formatSom(c.sum)}
              </p>
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
                <th className="text-left px-4 py-3 font-medium">Izoh</th>
                <th className="text-left px-4 py-3 font-medium">Filial</th>
                <th className="text-right px-4 py-3 font-medium">Summa</th>
                <th className="text-right px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                    Bu oy uchun xarajat kiritilmagan
                  </td>
                </tr>
              )}
              {items.map((e) => (
                <tr key={e.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-600">{formatDate(e.date)}</td>
                  <td className="px-4 py-3 text-slate-800">{categoryLabel(e.category)}</td>
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

      <p className="text-xs text-slate-400 mt-4">
        Ustozlar ish haqi bu yerga kiritilmaydi — u yoqlama asosida avtomatik
        hisoblanadi va foyda-zarar hisobotiga o'zi qo'shiladi.
      </p>

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
