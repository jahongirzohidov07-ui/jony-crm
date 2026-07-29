import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Plus } from "lucide-react";
import { api, type StudentDetail as StudentDetailType } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, can } from "../lib/roles";

const KIND_LABEL: Record<string, string> = {
  payment: "To'lov",
  charge: "Hisoblangan to'lov",
  discount: "Chegirma",
};

export default function StudentDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [student, setStudent] = useState<StudentDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [amount, setAmount] = useState("");
  const [kind, setKind] = useState<"payment" | "charge" | "discount">("payment");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    api
      .get<StudentDetailType>(`/students/${id}`)
      .then(setStudent)
      .finally(() => setLoading(false));
  }

  useEffect(load, [id]);

  const canEdit = can(user?.role, FINANCE_ACCESS);

  async function submitPayment() {
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("To'g'ri summa kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post(`/students/${id}/payments`, { amount: value, kind, note: note || null });
      setAmount("");
      setNote("");
      setShowAddPayment(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="p-8 text-slate-400 text-sm">Yuklanmoqda...</div>;
  if (!student) return <div className="p-8 text-slate-400 text-sm">Talaba topilmadi</div>;

  return (
    <div className="p-8 max-w-3xl">
      <Link to="/students" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-4">
        <ArrowLeft size={14} /> Talabalar ro'yhati
      </Link>

      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">{student.full_name}</h1>
            <p className="text-sm text-slate-500">
              {student.group ? student.group.name : "Guruhsiz"} · Qo'shilgan: {formatDate(student.enrolled_date)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400 mb-0.5">Balans</p>
            <p className={`text-xl font-semibold ${student.balance < 0 ? "text-red-600" : "text-slate-900"}`}>
              {formatSom(student.balance)}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-100 text-sm">
          <div>
            <p className="text-xs text-slate-400">Talaba telefoni</p>
            <p className="text-slate-700">{student.phone || "—"}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Ota-ona telefoni</p>
            <p className="text-slate-700">{student.parent_phone || "—"}</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-slate-900 text-sm">To'lovlar tarixi</h2>
        {canEdit && (
          <button
            onClick={() => setShowAddPayment((v) => !v)}
            className="flex items-center gap-1.5 text-sm bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5"
          >
            <Plus size={14} /> Yozuv qo'shish
          </button>
        )}
      </div>

      {showAddPayment && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Turi</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={kind}
                onChange={(e) => setKind(e.target.value as typeof kind)}
              >
                <option value="payment">To'lov (balansni oshiradi)</option>
                <option value="charge">Hisoblangan to'lov (balansni kamaytiradi)</option>
                <option value="discount">Chegirma (balansni kamaytiradi)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Summa (so'm)</label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Izoh</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Masalan: Iyul oyi to'lovi"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={submitPayment}
            disabled={saving}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Sana</th>
              <th className="text-left px-4 py-3 font-medium">Turi</th>
              <th className="text-left px-4 py-3 font-medium">Izoh</th>
              <th className="text-right px-4 py-3 font-medium">Summa</th>
            </tr>
          </thead>
          <tbody>
            {student.payments.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  Hali yozuv yo'q
                </td>
              </tr>
            )}
            {student.payments.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-600">{formatDate(p.created_at)}</td>
                <td className="px-4 py-3 text-slate-600">{KIND_LABEL[p.kind] || p.kind}</td>
                <td className="px-4 py-3 text-slate-600">{p.note || "—"}</td>
                <td className={`px-4 py-3 text-right font-medium ${p.amount < 0 ? "text-red-600" : "text-emerald-600"}`}>
                  {p.amount > 0 ? "+" : ""}
                  {formatSom(p.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
