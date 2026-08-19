import { useEffect, useState } from "react";
import { CalendarOff, Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

/**
 * DAM KUNLARI (2026-08-19).
 *
 * Jahongir: "bizda dam kunlari degan narsa bor buni sozlamalarga
 * qoshib qoysang ham bo'ladi. Dam kunlari darslar bo'lmaydi va bu
 * darslar umuman hisoblanmaydi... dam kunlar belgilanganda 12tadan
 * kamaysa ogohlantirib bunday qilish mumkin emas degan yozuv chiqsin".
 *
 * Dam kuni qo'yilganda o'sha kundagi BARCHA rejadagi darslar bekor
 * bo'ladi. Server har guruhda oyda kamida 12 dars qolishini oldindan
 * tekshiradi — kamaysa hech narsa o'zgarmaydi va sabab ko'rsatiladi.
 */

type Row = { id: number; date: string; name: string | null; by: string | null };

export function HolidaysCard() {
  const [rows, setRows] = useState<Row[]>([]);
  const [d, setD] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  function load() {
    api.get<{ rows: Row[] }>("/holidays")
      .then((r) => setRows(r.rows))
      .catch(() => setRows([]));
  }
  useEffect(load, []);

  async function add() {
    if (!d || busy) return;
    setBusy(true); setErr(""); setOk("");
    try {
      const r = await api.post<{ cancelled_lessons: number }>(
        "/holidays", { date: d, name: name.trim() });
      setOk(`Dam kuni qo'yildi — ${r.cancelled_lessons} ta dars rejadan chiqdi`);
      setD(""); setName("");
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function del(row: Row) {
    if (!confirm(`${formatDate(row.date)} dam kuni olib tashlansinmi? ` +
                 `O'sha kunning darslari rejaga qaytadi.`)) return;
    setErr(""); setOk("");
    try {
      await api.delete(`/holidays/${row.id}`);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 max-w-2xl">
      <div className="flex items-center gap-2 mb-1">
        <CalendarOff size={17} className="text-red-500" />
        <h2 className="text-base font-semibold text-slate-900">Dam kunlari</h2>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Dam kuni qo'yilsa, o'sha kundagi barcha rejadagi darslar bekor
        bo'ladi — davomatda ko'rinmaydi, oylik hisobiga kirmaydi. Har
        guruhda oyda kamida 12 ta dars qolishi shart — kamaysa tizim
        ruxsat bermaydi.
      </p>

      <div className="flex flex-wrap items-end gap-2 mb-3">
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">Sana</label>
          <input type="date" value={d} onChange={(e) => setD(e.target.value)}
            className="h-10 rounded-lg border border-slate-300 px-3 text-sm" />
        </div>
        <div className="flex-1 min-w-40">
          <label className="block text-xs font-medium text-slate-500 mb-1">
            Nomi (ixtiyoriy)
          </label>
          <input value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Masalan: Mustaqillik kuni"
            className="w-full h-10 rounded-lg border border-slate-300 px-3 text-sm" />
        </div>
        <button onClick={add} disabled={busy || !d}
          className="h-10 px-4 rounded-lg bg-brand-600 text-white text-sm font-medium flex items-center gap-1.5 disabled:opacity-40">
          <Plus size={15} /> Qo'shish
        </button>
      </div>

      {err && (
        <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
          {err}
        </p>
      )}
      {ok && (
        <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-3">
          {ok}
        </p>
      )}

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400">Hali dam kuni belgilanmagan.</p>
      ) : (
        <div className="divide-y divide-slate-100">
          {rows.map((r) => (
            <div key={r.id} className="flex items-center gap-3 py-2">
              <p className="text-sm font-medium text-slate-800 w-28">
                {formatDate(r.date)}
              </p>
              <p className="text-sm text-slate-500 flex-1">{r.name || "Dam kuni"}</p>
              {r.by && <p className="text-xs text-slate-400">{r.by}</p>}
              <button onClick={() => del(r)}
                className="p-1.5 text-slate-300 hover:text-red-600">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
