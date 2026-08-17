import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layers, Plus, Star, X, Users } from "lucide-react";
import { api } from "../lib/api";
import { formatDate, formatSom } from "../lib/format";

/**
 * O'QUVCHINING GURUHLARI (2026-08-17).
 *
 * Jahongir: "Abduvaliyeva Munisa degan qiz 2ta gruppaga keladi,
 * shuning uchun ham biz ham bazda 2ta gruppa qilishimiz kerak".
 *
 * Ilgari o'quvchida bitta guruh bo'lardi va ikki fanga qatnaydigan
 * bola IKKI MARTA kiritilardi — natijada faol o'quvchilar soni ham,
 * qarz ham ikki barobar ko'rinardi. Endi bitta o'quvchi bir nechta
 * guruhda tura oladi.
 *
 * DIQQAT: bu bosqichda oylik hisob HALI asosiy guruh bo'yicha
 * chiqadi. Ikki fan uchun hisob va 10% chegirma keyingi bosqichda —
 * Jahongir qoidani aytgach qo'shiladi. Shuning uchun kartada shu
 * haqda ochiq yozib qo'yildi, xodim adashmasin.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Row = {
  id: number;
  group_id: number;
  group: string;
  subject?: string | null;
  level?: string | null;
  teacher?: string | null;
  lesson_price?: number | null;
  is_primary: boolean;
  active: boolean;
  joined_date?: string | null;
  left_date?: string | null;
};

export function StudentGroupsCard({
  studentId,
  allGroups,
  canEdit,
  onChanged,
}: {
  studentId: number;
  allGroups: { id: number; name: string; subject?: string | null }[];
  canEdit: boolean;
  onChanged?: () => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [adding, setAdding] = useState(false);
  const [pick, setPick] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function load() {
    api
      .fresh<{ rows: Row[] }>(`/students/${studentId}/groups`)
      .then((d) => setRows(d.rows || []))
      .catch(() => setRows([]));
  }
  useEffect(load, [studentId]);

  const active = rows.filter((r) => r.active);
  const closed = rows.filter((r) => !r.active);
  const taken = new Set(active.map((r) => r.group_id));

  async function add() {
    if (!pick) return;
    setBusy(true);
    setErr("");
    try {
      await api.post(`/students/${studentId}/groups`, {
        group_id: Number(pick),
      });
      setPick("");
      setAdding(false);
      load();
      onChanged?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Qo'shib bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  async function drop(r: Row) {
    if (!confirm(`"${r.group}" guruhidan chiqarilsinmi?`)) return;
    setErr("");
    try {
      await api.delete(`/students/${studentId}/groups/${r.group_id}`);
      load();
      onChanged?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Chiqarib bo'lmadi");
    }
  }

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden max-w-lg mb-4">
      <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center gap-2">
        <Layers size={16} className="text-slate-400" />
        <p className="font-semibold text-slate-900 flex-1">
          Guruhlari
          {active.length > 1 && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 text-xs font-semibold">
              {active.length} ta fan
            </span>
          )}
        </p>
        {canEdit && !adding && (
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            <Plus size={14} /> Guruh qo'shish
          </button>
        )}
      </div>

      <div className="divide-y divide-slate-100">
        {active.map((r) => (
          <div key={r.id} className="px-4 py-3 flex items-center gap-3">
            <Users size={15} className="text-slate-300 shrink-0" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <Link
                  to={`/groups/${r.group_id}`}
                  className="text-sm font-medium text-slate-900 hover:text-brand-700 truncate"
                >
                  {r.group}
                </Link>
                {r.is_primary && (
                  <span
                    title="Asosiy guruh — oylik hisob shu bo'yicha chiqadi"
                    className="shrink-0"
                  >
                    <Star size={12} className="text-amber-500" fill="currentColor" />
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {r.teacher || "—"}
                {r.lesson_price
                  ? ` · ${formatSom(r.lesson_price)}/dars`
                  : ""}
                {r.joined_date ? ` · ${formatDate(r.joined_date)}` : ""}
              </p>
            </div>
            {canEdit && active.length > 1 && (
              <button
                onClick={() => drop(r)}
                title="Shu guruhdan chiqarish"
                className="p-1.5 rounded-lg text-slate-300 hover:text-red-600 hover:bg-red-50 shrink-0"
              >
                <X size={15} />
              </button>
            )}
          </div>
        ))}

        {active.length === 0 && (
          <p className="px-4 py-4 text-sm text-slate-400">
            Guruhga biriktirilmagan.
          </p>
        )}

        {adding && (
          <div className="px-4 py-3 bg-slate-50">
            <select
              value={pick}
              onChange={(e) => setPick(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
            >
              <option value="">— guruhni tanlang —</option>
              {allGroups
                .filter((g) => !taken.has(g.id))
                .map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                    {g.subject ? ` (${g.subject})` : ""}
                  </option>
                ))}
            </select>
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => {
                  setAdding(false);
                  setPick("");
                  setErr("");
                }}
                className="flex-1 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm"
              >
                Bekor
              </button>
              <button
                onClick={add}
                disabled={busy || !pick}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-50"
              >
                {busy ? "..." : "Qo'shish"}
              </button>
            </div>
          </div>
        )}

        {err && (
          <p className="px-4 py-2.5 text-sm text-red-600 bg-red-50">{err}</p>
        )}

        {closed.length > 0 && (
          <div className="px-4 py-2.5">
            <p className="text-xs text-slate-400">
              Chiqqan guruhlari:{" "}
              {closed
                .map(
                  (r) =>
                    r.group +
                    (r.left_date ? ` (${formatDate(r.left_date)})` : "")
                )
                .join(", ")}
            </p>
          </div>
        )}
      </div>

      {active.length > 1 && (
        <p className="px-4 py-2.5 text-[11px] text-amber-700 bg-amber-50 border-t border-amber-200 leading-snug">
          Oylik hisob hozircha faqat asosiy guruh (⭐) bo'yicha chiqadi.
          Ikki fan uchun hisob va chegirma keyingi bosqichda ulanadi.
        </p>
      )}
    </div>
  );
}
