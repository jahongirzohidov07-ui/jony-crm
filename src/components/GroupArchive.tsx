import { useEffect, useMemo, useState } from "react";
import { Archive as ArchiveIcon, RotateCcw, X } from "lucide-react";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

/**
 * GURUH ARXIVI (2026-09-30, Jahongir: "guruhda o'quvchi qolmagan yoki
 * faol bo'lmagan guruhlarni arxivga tushirib ko'rinmaydigan qilish").
 *
 * Avtomat emas: server hozirgi o'quvchisi (faol, sinov, muzlatilgan)
 * qolmagan guruhlarni TAKLIF qiladi, odam belgilab tasdiqlaydi. Arxivdagi
 * guruh ro'yxat, tanlagich va jadvaldan yashiriladi, lekin o'chmaydi —
 * "Arxiv" bo'limidan qaytariladi.
 */

type Candidate = {
  id: number; name: string; teacher: string | null; branch: string | null;
  last_lesson: string | null; idle_days: number | null;
  past_students: number; created_at: string | null;
};
type Result = {
  archived: { id: number; name: string }[];
  skipped: { id: number; name: string | null; reason: string }[];
};

/** Bo'sh guruhlar ro'yxati — belgilanganlarini arxivga o'tkazish. */
export function EmptyGroupsDialog({ onClose, onDone }: {
  onClose: () => void; onDone: () => void;
}) {
  const [rows, setRows] = useState<Candidate[] | null>(null);
  const [total, setTotal] = useState(0);
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    api.get<{ rows: Candidate[]; total_groups: number }>("/groups/archive-candidates")
      .then((r) => {
        setRows(r.rows);
        setTotal(r.total_groups);
        // Bir oydan beri darsi yo'qlari oldindan belgilanadi; umuman
        // darsi bo'lmagani (yangi ochilgan bo'lishi mumkin) — yo'q.
        setPicked(new Set(r.rows.filter((x) => (x.idle_days ?? -1) >= 30).map((x) => x.id)));
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const allOn = useMemo(() => !!rows?.length && rows.every((r) => picked.has(r.id)), [rows, picked]);

  function toggle(id: number) {
    const n = new Set(picked);
    if (n.has(id)) n.delete(id); else n.add(id);
    setPicked(n);
  }

  async function save() {
    if (!picked.size) { setErr("Kamida bitta guruhni belgilang"); return; }
    setSaving(true); setErr("");
    try {
      const r = await api.post<Result>("/groups/archive-bulk", {
        ids: [...picked], note: note.trim() || null,
      });
      setResult(r);
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-12 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-2xl p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <ArchiveIcon size={18} className="text-slate-400" /> Bo'sh guruhlar
          </h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Hozirgi o'quvchisi (faol, sinovdagi yoki muzlatilgan) qolmagan
          guruhlar. Arxivga o'tgani ro'yxat va jadvaldan yashiriladi,
          kelajakdagi bo'sh darslari va support biriktirishi olinadi.
          O'tgan darslar, yo'qlama va to'lovlar o'chmaydi — "Arxiv"
          bo'limidan qaytarsa bo'ladi.
        </p>

        {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{err}</p>}

        {result ? (
          <div className="space-y-3">
            <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
              {result.archived.length} ta guruh arxivga o'tkazildi.
            </p>
            {result.skipped.length > 0 && (
              <div className="text-sm text-amber-800 bg-amber-50 rounded-lg px-3 py-2">
                O'tkazilmadi:
                <ul className="list-disc ml-5 mt-1">
                  {result.skipped.map((s) => (
                    <li key={s.id}>{s.name ?? `#${s.id}`} — {s.reason}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="text-right">
              <button onClick={onClose}
                      className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium">
                Yopish
              </button>
            </div>
          </div>
        ) : !rows ? (
          <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-slate-500 py-6 text-center">
            {total} ta guruhning hammasida o'quvchi bor — arxivlanadigan
            bo'sh guruh yo'q.
          </p>
        ) : (
          <>
            <div className="border border-slate-200 rounded-lg overflow-hidden max-h-[50vh] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-500 text-xs uppercase sticky top-0">
                  <tr>
                    <th className="px-3 py-2 w-8">
                      <input type="checkbox" checked={allOn}
                             onChange={() => setPicked(allOn ? new Set() : new Set(rows.map((r) => r.id)))} />
                    </th>
                    <th className="text-left px-3 py-2 font-medium">Guruh</th>
                    <th className="text-left px-3 py-2 font-medium">Oxirgi dars</th>
                    <th className="text-right px-3 py-2 font-medium">Ilgari o'qigan</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} onClick={() => toggle(r.id)}
                        className="border-t border-slate-100 cursor-pointer hover:bg-slate-50">
                      <td className="px-3 py-2 text-center">
                        <input type="checkbox" checked={picked.has(r.id)} onChange={() => toggle(r.id)}
                               onClick={(e) => e.stopPropagation()} />
                      </td>
                      <td className="px-3 py-2">
                        <p className="font-medium text-slate-800">{r.name}</p>
                        <p className="text-[11px] text-slate-400">
                          {[r.teacher, r.branch].filter(Boolean).join(" · ") || "—"}
                        </p>
                      </td>
                      <td className="px-3 py-2 text-slate-600 whitespace-nowrap">
                        {r.last_lesson ? (
                          <>
                            {formatDate(r.last_lesson)}
                            <span className="block text-[11px] text-slate-400">{r.idle_days} kun oldin</span>
                          </>
                        ) : (
                          <span className="text-amber-700 text-xs">dars o'tilmagan — yangi bo'lishi mumkin</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-600">{r.past_students}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3">
              <label className="block text-xs text-slate-500 mb-1">Sabab (ixtiyoriy)</label>
              <input value={note} onChange={(e) => setNote(e.target.value)}
                     placeholder="Masalan: kurs tugadi, guruh tarqaldi"
                     className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
            </div>
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-slate-500">{picked.size} ta belgilandi</span>
              <button onClick={save} disabled={saving || !picked.size}
                      className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60">
                {saving ? "O'tkazilmoqda..." : "Arxivga o'tkazish"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

type ArchivedGroup = {
  id: number; name: string;
  teacher?: { full_name: string } | null;
  branch?: { name: string } | null;
  archived_at?: string | null; archived_by?: string | null; archive_note?: string | null;
};

/** Arxiv bo'limi: arxivdagi guruhlar va qaytarish. */
export function ArchivedGroupsTab({ canRestore }: { canRestore: boolean }) {
  const [rows, setRows] = useState<ArchivedGroup[] | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  function load() {
    api.get<ArchivedGroup[]>("/groups?archived=1")
      .then(setRows)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }
  useEffect(load, []);

  async function restore(g: ArchivedGroup) {
    if (!window.confirm(`"${g.name}" guruhini arxivdan qaytarasizmi? U yana ro'yxat va jadvalda chiqadi.`)) return;
    setBusy(g.id);
    try {
      await api.post(`/groups/${g.id}/restore`, {});
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  if (err && !rows) return <p className="text-sm text-red-600">{err}</p>;
  if (!rows) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;
  if (!rows.length) {
    return (
      <p className="text-sm text-slate-500 py-8 text-center">
        Arxivda guruh yo'q. Bo'sh guruhlarni "Guruhlar" sahifasidagi
        "Bo'sh guruhlar" tugmasi orqali arxivga o'tkazasiz.
      </p>
    );
  }
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {err && <p className="text-sm text-red-600 px-4 pt-3">{err}</p>}
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Guruh</th>
            <th className="text-left px-4 py-2 font-medium">Arxivga o'tgan</th>
            <th className="text-left px-4 py-2 font-medium">Sabab</th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody>
          {rows.map((g) => (
            <tr key={g.id} className="border-t border-slate-100">
              <td className="px-4 py-2.5">
                <p className="font-medium text-slate-800">{g.name}</p>
                <p className="text-[11px] text-slate-400">
                  {[g.teacher?.full_name, g.branch?.name].filter(Boolean).join(" · ") || "—"}
                </p>
              </td>
              <td className="px-4 py-2.5 text-slate-600 whitespace-nowrap">
                {g.archived_at ? formatDate(g.archived_at) : "—"}
                {g.archived_by && <span className="block text-[11px] text-slate-400">{g.archived_by}</span>}
              </td>
              <td className="px-4 py-2.5 text-slate-600">{g.archive_note || "—"}</td>
              <td className="px-4 py-2.5 text-right">
                {canRestore && (
                  <button onClick={() => restore(g)} disabled={busy === g.id}
                          className="inline-flex items-center gap-1.5 text-sm text-brand-700 hover:underline disabled:opacity-50">
                    <RotateCcw size={14} /> Qaytarish
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
