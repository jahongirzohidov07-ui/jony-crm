import { useEffect, useState } from "react";
import { Info, Plus, Trash2, X } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/** To'lov kalendari: qachon maosh, ijara, soliq, reklama, yetkazib
 *  beruvchi — va shu sanada pul yetarlimi. */

const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");
const KIND_ICON: Record<string, string> = {
  salary: "\u{1F4B0}", rent: "\u{1F3E2}", tax: "\u{1F3DB}\u{FE0F}",
  ads: "\u{1F4E3}", supplier: "\u{1F4E6}", other: "\u{1F4CC}",
};
const EN_TONE: Record<string, string> = {
  green: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  red: "bg-red-50 text-red-700",
};
const EN_LBL: Record<string, string> = {
  green: "yetadi", amber: "zo'rg'a yetadi", red: "yetmaydi",
};

export function PaymentCalendarTab() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [add, setAdd] = useState(false);

  const load = () => {
    api.get<Any>("/finance/payment-calendar").then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const del = async (id: number) => {
    if (!confirm("Bu to'lov kalendaridan olib tashlansinmi?")) return;
    try {
      await api.delete(`/finance/payment-calendar/${id}`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  };

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <p className="text-xs text-slate-500">Hozirgi holat (oy)</p>
          <p className={`text-lg font-semibold ${
            d.cash_now >= 0 ? "text-slate-900" : "text-red-600"}`}>
            {fmt(d.cash_now)}
          </p>
          <p className="text-[11px] text-slate-400">
            yig'ilgan − xarajat
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <p className="text-xs text-slate-500">Kunlik tushum sur'ati</p>
          <p className="text-lg font-semibold text-slate-900">
            {fmt(d.daily_pace)}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-3">
          <p className="text-xs text-slate-500">Oy majburiyatlari</p>
          <p className="text-lg font-semibold text-slate-900">
            {fmt(d.total_due)}
          </p>
        </div>
        <div className="flex items-center justify-end">
          {d.can_edit && (
            <button onClick={() => setAdd(true)}
              className="flex items-center gap-1.5 bg-slate-900 text-white rounded-lg px-3 py-2 text-sm font-medium">
              <Plus size={14} /> To'lov qo'shish
            </button>
          )}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm whitespace-nowrap">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Sana</th>
              <th className="text-left px-3 py-2.5 font-medium">To'lov</th>
              <th className="text-right px-3 py-2.5 font-medium">Summa</th>
              <th className="text-right px-3 py-2.5 font-medium">
                Prognoz qoldiq</th>
              <th className="text-center px-3 py-2.5 font-medium">
                Pul yetarlimi?</th>
              <th className="px-3 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.items.map((it: Any) => (
              <tr key={`${it.id}-${it.date}`}
                  className={it.passed ? "opacity-50" : ""}>
                <td className="px-4 py-2.5 text-slate-700 font-medium">
                  {it.date.slice(8)}-kun
                  {it.recurring && (
                    <span className="text-[10px] text-slate-400 ml-1">
                      har oy
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-slate-700">
                  {KIND_ICON[it.kind] || ""} {it.title}
                  <span className="text-xs text-slate-400 ml-1.5">
                    {it.kind_label}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right font-medium text-slate-900">
                  {fmt(it.amount)}
                </td>
                <td className={`px-3 py-2.5 text-right ${
                  it.projected_cash < 0 ? "text-red-600" : "text-slate-600"}`}>
                  {fmt(it.projected_cash)}
                </td>
                <td className="px-3 py-2.5 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    EN_TONE[it.enough]}`}>
                    {EN_LBL[it.enough]}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  {d.can_edit && (
                    <button onClick={() => del(it.id)}
                      className="text-slate-300 hover:text-red-600">
                      <Trash2 size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.items.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Hali to'lov kiritilmagan. "To'lov qo'shish" bilan maosh,
            ijara, soliq sanalarini kiriting.
          </p>
        )}
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {add && (
        <AddDue kinds={d.kinds}
          onClose={() => { setAdd(false); load(); }} />
      )}
    </div>
  );
}

function AddDue({ kinds, onClose }: Any) {
  const [f, setF] = useState({ title: "", kind: "salary", due_day: "",
    amount: "", note: "" });
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      await api.post("/finance/payment-calendar", {
        title: f.title, kind: f.kind,
        due_day: Number(f.due_day) || null,
        amount: Number(f.amount) || 0,
        recurring: true, note: f.note || null,
      });
      onClose();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
      setBusy(false);
    }
  };
  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-900">
            To'lov qo'shish
          </h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-2">
          <input value={f.title}
            onChange={(e) => setF({ ...f, title: e.target.value })}
            placeholder="Nomi (masalan: Ofis ijarasi) *"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <select value={f.kind}
            onChange={(e) => setF({ ...f, kind: e.target.value })}
            className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm">
            {kinds.map((k: Any) => (
              <option key={k.key} value={k.key}>{k.label}</option>
            ))}
          </select>
          <div className="flex gap-2">
            <input type="number" min={1} max={31} value={f.due_day}
              onChange={(e) => setF({ ...f, due_day: e.target.value })}
              placeholder="Har oyning kuni *"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-40" />
            <input type="number" value={f.amount}
              onChange={(e) => setF({ ...f, amount: e.target.value })}
              placeholder="Summa *"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm flex-1" />
          </div>
          <input value={f.note}
            onChange={(e) => setF({ ...f, note: e.target.value })}
            placeholder="Izoh"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600">Bekor</button>
          <button onClick={save}
            disabled={busy || !f.title || !f.due_day || !f.amount}
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40">
            Saqlash
          </button>
        </div>
      </div>
    </div>
  );
}
