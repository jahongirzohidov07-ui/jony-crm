import { useEffect, useState } from "react";
import { Gift, BellRing, Plus, Check, Circle } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");

/** Xaridlar — coin do'konidan olingan sovg'alar. */
export function PurchasesTab({ studentId }: { studentId: number }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Any>(`/students/${studentId}/purchases`).then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [studentId]);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      <div className="flex justify-between items-center px-4 py-3 bg-slate-50">
        <p className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
          <Gift size={14} className="text-slate-400" /> Xaridlar
        </p>
        <p className="text-xs text-slate-500">
          Jami: <b>{d.total_coins}</b> coin
        </p>
      </div>
      <table className="w-full text-sm">
        <thead className="text-xs text-slate-500">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Sovg'a</th>
            <th className="text-right px-3 py-2 font-medium">Coin</th>
            <th className="text-right px-3 py-2 font-medium">Qiymati</th>
            <th className="text-center px-3 py-2 font-medium">Holat</th>
            <th className="text-right px-4 py-2 font-medium">Sana</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {d.purchases.map((p: Any) => (
            <tr key={p.id}>
              <td className="px-4 py-2 text-slate-800">
                {p.reward}
                {p.by_student && (
                  <span className="text-[10px] text-slate-400 ml-1.5">
                    o'zi so'ragan
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-right font-medium text-amber-600">
                {p.coins}
              </td>
              <td className="px-3 py-2 text-right text-slate-500">
                {p.value_som ? fmt(p.value_som) : "—"}
              </td>
              <td className="px-3 py-2 text-center">
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  p.status === "berildi"
                    ? "bg-emerald-50 text-emerald-700"
                    : p.status === "rad etildi"
                    ? "bg-red-50 text-red-600"
                    : "bg-slate-100 text-slate-600"}`}>
                  {p.status}
                </span>
              </td>
              <td className="px-4 py-2 text-right text-slate-500">
                {p.date || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {d.purchases.length === 0 && (
        <p className="text-sm text-slate-400 py-8 text-center">
          Hali xarid yo'q.
        </p>
      )}
    </div>
  );
}

/** Eslatmalar — matn + ixtiyoriy sana; sanasida adminga vazifa tushadi. */
export function RemindersTab({ studentId }: { studentId: number }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [text, setText] = useState("");
  const [when, setWhen] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => {
    api.get<Any>(`/students/${studentId}/reminders`).then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, [studentId]);

  const add = async () => {
    setBusy(true);
    try {
      await api.post(`/students/${studentId}/reminders`,
        { text, remind_on: when || null });
      setText(""); setWhen("");
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };
  const toggle = async (rid: number) => {
    try {
      await api.post(`/students/${studentId}/reminders/${rid}/toggle`, {});
      load();
    } catch { /* jim */ }
  };

  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-3">
        <p className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
          <BellRing size={14} className="text-slate-400" />
          Yangi eslatma
        </p>
        <div className="flex flex-wrap gap-2">
          <input value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Masalan: 5-avgustda to'lov haqida eslatilsin *"
            className="flex-1 min-w-[220px] border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <input type="date" value={when}
            onChange={(e) => setWhen(e.target.value)}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm" />
          <button onClick={add} disabled={busy || !text.trim()}
            className="flex items-center gap-1.5 bg-brand-600 text-white rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-40">
            <Plus size={14} /> Qo'shish
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mt-1.5">
          Sana tanlansa — o'sha kuni admin va sotuv menejeriga vazifa
          tushadi.
        </p>
      </div>
      <div className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100">
        {d.reminders.map((r: Any) => (
          <div key={r.id} className="flex items-start gap-3 px-4 py-3">
            <button onClick={() => toggle(r.id)} className="mt-0.5">
              {r.done ? (
                <Check size={16} className="text-emerald-600" />
              ) : (
                <Circle size={16} className="text-slate-300" />
              )}
            </button>
            <div className="flex-1 min-w-0">
              <p className={`text-sm ${r.done
                ? "text-slate-400 line-through" : "text-slate-800"}`}>
                {r.text}
              </p>
              <p className="text-xs text-slate-400">
                {r.created_by} · {r.date}
              </p>
            </div>
            {r.remind_on && (
              <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
                r.overdue ? "bg-red-50 text-red-600"
                : "bg-sky-50 text-sky-700"}`}>
                {r.remind_on}
              </span>
            )}
          </div>
        ))}
        {d.reminders.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Hali eslatma yo'q.
          </p>
        )}
      </div>
    </div>
  );
}
