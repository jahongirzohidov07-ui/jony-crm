import { useEffect, useMemo, useState } from "react";
import { X, Search, CalendarX2 } from "lucide-react";
import { api } from "../lib/api";
import { formatPhone } from "./PhoneInput";

/**
 * SANASI KIRITILMAGANLAR (2026-10-06, Jahongir: "tadbirlarga bitta click
 * bilan tug'ilgan kuni yoki ishga kirgan sanasi kiritilmaganlar degan
 * knopka qo'shib ber, xodim ismiga bosib akkauntiga tug'ilgan kun
 * biriktirib qo'ya olay").
 *
 * Sanasi yo'q odam tug'ilgan kun / yubiley ro'yxatiga umuman tushmaydi.
 * Bu oyna ularni topadi: ismni bosib sanani shu yerda yozasiz — u
 * xodim/o'quvchi kartasiga yoziladi (faqat shu ikki sana o'zgaradi).
 */
type Row = {
  who: "staff" | "student"; id: number; full_name: string;
  sub: string | null; branch: string | null; phone: string | null;
  birth_date: string | null; hired_date: string | null;
  locked?: boolean;
};
type Data = {
  staff: Row[]; students: Row[];
  no_birth_staff: number; no_hired_staff: number; can_edit: boolean;
};

export function MissingDatesDialog({ onClose, onChanged }: {
  onClose: () => void; onChanged: () => void;
}) {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<"staff" | "students">("staff");
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState<Row | null>(null);

  const load = () =>
    api.fresh<Data>("/events/missing-dates")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  useEffect(() => { load(); }, []);

  const rows = useMemo(() => {
    if (!d) return [];
    const n = q.trim().toLowerCase();
    return (tab === "staff" ? d.staff : d.students)
      .filter((r) => !n || r.full_name.toLowerCase().includes(n));
  }, [d, tab, q]);

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-start justify-center p-4 pt-10 overflow-y-auto"
         onClick={onClose}>
      <div className="bg-white rounded-xl w-full max-w-2xl p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <CalendarX2 size={18} className="text-amber-600" /> Sanasi kiritilmaganlar
          </h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Ular tug'ilgan kun va yubiley ro'yxatiga tushmaydi.
          {d?.can_edit ? " Ismni bosib sanani kiriting." : " Sanani event menejer yoki HR kiritadi."}
        </p>

        {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{err}</p>}
        {!d ? (
          <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              {([["staff", `Xodimlar (${d.staff.length})`], ["students", `O'quvchilar (${d.students.length})`]] as const).map(([k, l]) => (
                <button key={k} onClick={() => setTab(k)}
                        className={`px-3 py-1.5 rounded-lg text-sm border ${
                          tab === k ? "bg-brand-50 border-brand-400 text-brand-700 font-medium"
                            : "bg-white border-slate-200 text-slate-600"}`}>
                  {l}
                </button>
              ))}
              <div className="relative ml-auto">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ism bo'yicha"
                       className="rounded-lg border border-slate-200 pl-8 pr-3 py-1.5 text-sm w-44" />
              </div>
            </div>
            {tab === "staff" && (
              <p className="text-xs text-slate-500 mb-2">
                Tug'ilgan sanasi yo'q: <b>{d.no_birth_staff}</b> · Ishga kirgan sanasi yo'q: <b>{d.no_hired_staff}</b>
              </p>
            )}

            {rows.length === 0 ? (
              <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-6 text-center">
                Hammasining sanasi kiritilgan 👌
              </p>
            ) : (
              <ul className="border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-[55vh] overflow-y-auto">
                {rows.map((r) => (
                  <li key={`${r.who}-${r.id}`}>
                    <button type="button" disabled={!d.can_edit || r.locked} onClick={() => setEditing(r)}
                            title={r.locked ? "Asoschi kartasini faqat asoschining o'zi tahrirlaydi" : undefined}
                            className="w-full text-left px-3 py-2.5 hover:bg-slate-50 disabled:hover:bg-white flex flex-wrap items-center gap-x-3 gap-y-1">
                      <span className="flex-1 min-w-[180px]">
                        <span className={`font-medium ${d.can_edit && !r.locked ? "text-brand-700" : "text-slate-800"}`}>{r.full_name}</span>
                        {r.locked && <span className="ml-2 text-[10px] text-slate-400">faqat asoschi kiritadi</span>}
                        <span className="block text-[11px] text-slate-400">
                          {[r.sub, r.branch, r.phone ? formatPhone(r.phone) : null].filter(Boolean).join(" · ") || "—"}
                        </span>
                      </span>
                      <span className="flex gap-1.5 text-[11px]">
                        {!r.birth_date && <span className="rounded px-1.5 py-0.5 bg-rose-50 text-rose-700">tug'ilgan sana yo'q</span>}
                        {r.who === "staff" && !r.hired_date && <span className="rounded px-1.5 py-0.5 bg-amber-50 text-amber-700">ishga kirgan sana yo'q</span>}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {editing && (
          <DateEditDialog
            row={editing}
            onClose={() => setEditing(null)}
            onSaved={() => { setEditing(null); load(); onChanged(); }}
          />
        )}
      </div>
    </div>
  );
}

function DateEditDialog({ row, onClose, onSaved }: {
  row: Row; onClose: () => void; onSaved: () => void;
}) {
  const staff = row.who === "staff";
  const [birth, setBirth] = useState(row.birth_date || "");
  const [hired, setHired] = useState(row.hired_date || "");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const today = new Date().toISOString().slice(0, 10);

  async function save() {
    if (!birth && !(staff && hired)) {
      setErr("Kamida bitta sanani kiriting");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const body: Record<string, string | null> = {};
      if (birth) body.birth_date = birth;
      if (staff && hired) body.hired_date = hired;
      await api.put(`/events/dates/${row.who}/${row.id}`, body);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-[60] flex items-start justify-center p-4 pt-24"
         onClick={onClose}>
      <div className="bg-white rounded-xl w-full max-w-sm p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">{row.full_name}</h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          {[staff ? "Xodim" : "O'quvchi", row.sub, row.branch].filter(Boolean).join(" · ")}
        </p>

        <label className="block text-xs text-slate-500 mb-1">Tug'ilgan sana</label>
        <input type="date" value={birth} max={today} onChange={(e) => setBirth(e.target.value)}
               className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm mb-3" />
        {staff && (
          <>
            <label className="block text-xs text-slate-500 mb-1">Ishga kirgan sana</label>
            <input type="date" value={hired} max={today} onChange={(e) => setHired(e.target.value)}
                   className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm mb-1" />
            <p className="text-[11px] text-slate-400 mb-3">Ish yubileyi shu sanadan hisoblanadi.</p>
          </>
        )}
        {err && <p className="text-sm text-red-600 mb-3">{err}</p>}
        <button onClick={save} disabled={busy}
                className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-50">
          {busy ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </div>
    </div>
  );
}
