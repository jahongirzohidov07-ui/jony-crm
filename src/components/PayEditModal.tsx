import { useState } from "react";
import { X } from "lucide-react";
import { api } from "../lib/api";
import { PAYMENT_METHODS } from "../lib/payments";

/**
 * Kirim/chiqim yozuvini tahrirlash oynasi (Jahongir: "bazida xato
 * kiritib yuborishlar boladi uni togrlash kerak").
 *
 * target.kind:
 *  - "payment" -> PUT /payments/{id} (summa, usul, izoh)
 *  - "expense" -> PUT /expenses/{id} (summa, usul, izoh)
 * Yozuv o'chirilmaydi - eski qiymatlar Auditda qoladi.
 */
export interface PayEditTarget {
  kind: "payment" | "expense";
  id: number;
  amount: number;
  method?: string | null;
  note?: string | null;
  title?: string;
  /** To'lov usuli tanlagichi ko'rsatilsinmi (charge'da ma'nosiz) */
  canMethod?: boolean;
}

export function PayEditModal({
  target,
  onClose,
  onSaved,
}: {
  target: PayEditTarget;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [amount, setAmount] = useState(String(Math.abs(target.amount)));
  const [method, setMethod] = useState(target.method || "cash");
  const [note, setNote] = useState(target.note || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    const num = Number(amount);
    if (!num || num <= 0) {
      setError("Summani musbat son bilan kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (target.kind === "payment") {
        await api.put(`/payments/${target.id}`, {
          amount: num,
          note: note || null,
          ...(target.canMethod !== false ? { method } : {}),
        });
      } else {
        await api.put(`/expenses/${target.id}`, {
          amount: num,
          method,
          note: note || null,
        });
      }
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
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-900 text-sm">
            {target.kind === "payment" ? "To'lovni tahrirlash" : "Chiqimni tahrirlash"}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={17} />
          </button>
        </div>
        {target.title && (
          <p className="text-xs text-slate-500 mb-3">{target.title}</p>
        )}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Summa (so'm)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              autoFocus
            />
          </div>
          {target.canMethod !== false && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                To'lov usuli
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                {PAYMENT_METHODS.map((m) => (
                  <option key={m.key} value={m.key}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Izoh
            </label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="—"
            />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex gap-2 justify-end pt-1">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg text-sm text-slate-600 border border-slate-200"
            >
              Bekor
            </button>
            <button
              onClick={save}
              disabled={saving}
              className="px-4 py-1.5 rounded-lg text-sm font-medium bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-60"
            >
              {saving ? "Saqlanmoqda..." : "Saqlash"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
