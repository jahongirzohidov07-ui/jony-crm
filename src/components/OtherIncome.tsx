/**
 * QO'SHIMCHA DAROMAD (2026-10-06).
 *
 * Jahongir: "qo'shimcha daromadlar bo'limini qo'shib ber
 * administratorlar qila oladigan bo'lsin, pul oqimida ko'rinishi
 * kerak u ham".
 *
 * O'quvchi to'lovidan tashqari kassaga kirgan pul — kitob sotuvi,
 * mock imtihon, sertifikat, ijara... Administrator kiritadi va
 * tuzatadi; o'chirish (aslida arxivlash — bazadan o'chmaydi) faqat
 * moliyada. Kiritilgan pul Pul oqimida KIRIM bo'lib chiqadi.
 */
import { useEffect, useState } from "react";
import { Pencil, Plus, Trash2, X } from "lucide-react";
import { api, getGlobalBranch, type Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { formatDate, formatSom } from "../lib/format";
import { PAYMENT_METHODS } from "../lib/payments";
import { MONTHS } from "../lib/expenses";

export interface OtherIncomeRow {
  id: number;
  date: string;
  category: string;
  category_label: string;
  amount: number;
  method: string;
  method_label: string;
  note: string | null;
  branch_id: number | null;
  branch: string | null;
  created_by: string | null;
}

interface OtherIncomeList {
  period: string;
  rows: OtherIncomeRow[];
  total: number;
  by_category: { category: string; label: string; amount: number }[];
  categories: { key: string; label: string }[];
  can_archive: boolean;
}

function todayIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
}

export function OtherIncomeTab() {
  const { user } = useAuth();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<OtherIncomeList | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<OtherIncomeRow | "new" | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    api
      .get<OtherIncomeList>(`/other-incomes?year=${year}&month=${month}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(load, [year, month]);
  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, []);

  async function archive(r: OtherIncomeRow) {
    if (!confirm(`${r.category_label} — ${formatSom(r.amount)} o'chirilsinmi? (arxivga o'tadi)`))
      return;
    try {
      await api.delete(`/other-incomes/${r.id}`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  const years = [now.getFullYear() - 1, now.getFullYear()];
  const globalBranch = Number(getGlobalBranch()) || null;
  const needBranch = !globalBranch && !user?.branch_id && branches.length > 1;

  return (
    <div>
      <div className="flex items-center justify-between mb-5 gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>{m}</option>
            ))}
          </select>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <span className="text-sm text-slate-500 ml-1">
            jami{" "}
            <span className="font-semibold text-emerald-700">
              {formatSom(data?.total || 0)}
            </span>
          </span>
        </div>
        <button
          onClick={() => setForm("new")}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          <Plus size={16} /> Daromad qo'shish
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {data && data.by_category.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {data.by_category.map((c) => (
            <div key={c.category} className="bg-white border border-slate-200 rounded-lg px-3 py-2">
              <p className="text-xs text-slate-500">{c.label}</p>
              <p className="text-sm font-semibold text-slate-800">{formatSom(c.amount)}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Sana</th>
                <th className="text-left px-4 py-3 font-medium">Turi</th>
                <th className="text-left px-4 py-3 font-medium">Izoh</th>
                <th className="text-left px-4 py-3 font-medium">Usul</th>
                <th className="text-left px-4 py-3 font-medium">Filial</th>
                <th className="text-left px-4 py-3 font-medium">Kiritdi</th>
                <th className="text-right px-4 py-3 font-medium">Summa</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {(data?.rows.length ?? 0) === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-400">
                    Bu oy uchun qo'shimcha daromad kiritilmagan
                  </td>
                </tr>
              )}
              {data?.rows.map((r) => (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-600">{formatDate(r.date)}</td>
                  <td className="px-4 py-3 text-slate-800">{r.category_label}</td>
                  <td className="px-4 py-3 text-slate-500">{r.note || "—"}</td>
                  <td className="px-4 py-3 text-slate-600">{r.method_label}</td>
                  <td className="px-4 py-3 text-slate-500">{r.branch || "—"}</td>
                  <td className="px-4 py-3 text-slate-500">{r.created_by || "—"}</td>
                  <td className="px-4 py-3 text-right font-medium text-emerald-700 tabular-nums">
                    +{formatSom(r.amount)}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button
                      onClick={() => setForm(r)}
                      className="text-slate-400 hover:text-brand-600 mr-2"
                      title="Tahrirlash"
                    >
                      <Pencil size={15} />
                    </button>
                    {data.can_archive && (
                      <button
                        onClick={() => archive(r)}
                        className="text-slate-300 hover:text-red-500"
                        title="O'chirish (arxivga o'tadi)"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-400 mt-3">
        Bu yerdagi pul Pul oqimida "Kirim — Qo'shimcha daromad" bo'lib
        chiqadi va kassa qoldig'iga qo'shiladi.
      </p>

      {form && data && (
        <OtherIncomeForm
          initial={form === "new" ? null : form}
          categories={data.categories}
          branches={needBranch ? branches : []}
          defaultBranchId={globalBranch || user?.branch_id || null}
          onClose={() => setForm(null)}
          onSaved={() => {
            setForm(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function OtherIncomeForm({
  initial,
  categories,
  branches,
  defaultBranchId,
  onClose,
  onSaved,
}: {
  initial: OtherIncomeRow | null;
  categories: { key: string; label: string }[];
  branches: Branch[];
  defaultBranchId: number | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [category, setCategory] = useState(initial?.category || categories[0]?.key || "other");
  const [amount, setAmount] = useState(initial ? String(initial.amount) : "");
  const [method, setMethod] = useState(initial?.method || "cash");
  const [date, setDate] = useState(initial?.date || todayIso());
  const [note, setNote] = useState(initial?.note || "");
  const [branchId, setBranchId] = useState<number | null>(defaultBranchId);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    const amt = Number(String(amount).replace(/\s/g, ""));
    if (!amt || amt <= 0) {
      setErr("Summani kiriting");
      return;
    }
    if (branches.length > 0 && !branchId && !initial) {
      setErr("Filialni tanlang");
      return;
    }
    setSaving(true);
    setErr(null);
    const body = { category, amount: amt, method, date, note };
    try {
      if (initial) await api.put(`/other-incomes/${initial.id}`, body);
      else await api.post("/other-incomes", { ...body, branch_id: branchId });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white";
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">
            {initial ? "Daromadni tahrirlash" : "Qo'shimcha daromad"}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <label className="block">
            <span className="text-xs text-slate-500">Turi</span>
            <select className={input} value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-slate-500">Summa (so'm)</span>
            <input
              className={input}
              inputMode="numeric"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="50000"
              autoFocus
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs text-slate-500">Usul</span>
              <select className={input} value={method} onChange={(e) => setMethod(e.target.value)}>
                {PAYMENT_METHODS.map((m) => (
                  <option key={m.key} value={m.key}>{m.label}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-slate-500">Sana</span>
              <input
                type="date"
                className={input}
                value={date}
                max={todayIso()}
                onChange={(e) => setDate(e.target.value)}
              />
            </label>
          </div>
          {branches.length > 0 && !initial && (
            <label className="block">
              <span className="text-xs text-slate-500">Filial</span>
              <select
                className={input}
                value={branchId ?? ""}
                onChange={(e) => setBranchId(Number(e.target.value) || null)}
              >
                <option value="">— tanlang —</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </label>
          )}
          <label className="block">
            <span className="text-xs text-slate-500">Izoh</span>
            <input
              className={input}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Masalan: 3 ta Round-up 4"
            />
          </label>
        </div>
        {err && <p className="text-sm text-red-600 mt-3">{err}</p>}
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-300">
            Bekor qilish
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="px-4 py-2 text-sm rounded-lg bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-50"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}
