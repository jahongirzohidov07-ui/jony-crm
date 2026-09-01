import { useEffect, useState } from "react";
import { X, Pencil } from "lucide-react";
import { api, ApiError, type CheckProblem } from "../lib/api";

/**
 * USTOZ O'Z GURUHINI TAHRIRLAYDI — faqat 4 maydon.
 *
 * 2026-09-01, Jahongir: "ustozlar o'zlarini guruhlarini edit qilishda
 * guruh nomini o'zgartirish darajasini va vaqtini o'zgartirish
 * xonasini ozgartirish huquqi bolsin".
 *
 * Bu ATAYLAB GroupFormModal EMAS. Guruhlar sahifasidagi katta forma
 * narx, stavka, ustoz va filialni ham yuboradi — ustozga u forma
 * berilsa, bitta noto'g'ri bosishda guruh narxi yoki ustozi
 * o'zgarib ketardi. Shuning uchun bu yerda alohida, tor oyna:
 * /api/me/groups/{id} manziliga faqat nom, daraja, vaqt va xona
 * boradi. Server tomoni ham xuddi shu to'rttasidan boshqasini
 * qabul qilmaydi.
 */

interface Opt {
  key: string;
  label: string;
}

interface EditOptions {
  subject_label?: string | null;
  levels: Opt[];
  lesson_times: { start: string; label: string }[];
  rooms: { id: number; name: string; capacity?: number | null }[];
  current: {
    name: string;
    level?: string | null;
    lesson_time?: string | null;
    room_id?: number | null;
  };
  hint: string;
}

export function MyGroupEditModal({
  groupId,
  onClose,
  onSaved,
}: {
  groupId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [opt, setOpt] = useState<EditOptions | null>(null);
  const [name, setName] = useState("");
  const [level, setLevel] = useState("");
  const [time, setTime] = useState("");
  const [roomId, setRoomId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<CheckProblem[]>([]);
  const [canForce, setCanForce] = useState(false);

  useEffect(() => {
    api
      .get<EditOptions>(`/me/groups/${groupId}/edit-options`)
      .then((d) => {
        setOpt(d);
        setName(d.current.name ?? "");
        setLevel(d.current.level ?? "");
        setTime(d.current.lesson_time ?? "");
        setRoomId(d.current.room_id ? String(d.current.room_id) : "");
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Ochib bo'lmadi"),
      );
  }, [groupId]);

  async function submit(force = false) {
    if (!name.trim()) {
      setError("Guruh nomini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    if (!force) setProblems([]);
    try {
      await api.put(`/me/groups/${groupId}${force ? "?force=true" : ""}`, {
        name: name.trim(),
        level: level || null,
        lesson_time: time || null,
        room_id: roomId ? Number(roomId) : null,
      });
      onSaved();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.problems.length) {
        setProblems(e.problems);
        setCanForce(e.canForce);
        setError(null);
      } else {
        setError(e instanceof Error ? e.message : "Xatolik");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-semibold text-slate-900">Guruhni tahrirlash</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>
        <p className="text-[11px] text-slate-400 mb-4">
          Nom, daraja, dars vaqti va xona. Narx, ustoz va filial
          rahbariyatda qoladi.
        </p>

        {!opt && !error && (
          <p className="text-sm text-slate-400 py-6 text-center">Yuklanmoqda…</p>
        )}

        {opt && (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Guruh nomi *
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Daraja
                {opt.subject_label ? ` (${opt.subject_label})` : ""}
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {opt.levels.map((l) => (
                  <option key={l.key} value={l.key}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Dars vaqti
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {opt.lesson_times.map((t) => (
                  <option key={t.start} value={t.start}>
                    {t.label}
                  </option>
                ))}
                {time &&
                  !opt.lesson_times.some((t) => t.start === time) && (
                    <option value={time}>{time}</option>
                  )}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Xona
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {opt.rooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                    {r.capacity ? ` (${r.capacity} kishilik)` : ""}
                  </option>
                ))}
              </select>
            </div>

            {problems.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 space-y-1">
                {problems.map((p, i) => (
                  <p key={i} className="text-xs text-amber-800">
                    {p.message}
                  </p>
                ))}
                {!canForce && (
                  <p className="text-[11px] text-amber-700 pt-1">
                    Bu to'siqni aylanib o'tib bo'lmaydi — boshqa vaqt yoki
                    xona tanlang.
                  </p>
                )}
              </div>
            )}
            {error && <p className="text-xs text-red-600">{error}</p>}

            <div className="flex gap-2 pt-1">
              <button
                onClick={onClose}
                className="flex-1 rounded-lg border border-slate-300 py-2 text-sm text-slate-600"
              >
                Bekor
              </button>
              <button
                onClick={() => submit(canForce && problems.length > 0)}
                disabled={saving}
                className="flex-1 rounded-lg bg-brand-600 py-2 text-sm font-medium text-white disabled:opacity-60"
              >
                {saving
                  ? "Saqlanmoqda…"
                  : canForce && problems.length > 0
                    ? "Baribir saqlash"
                    : "Saqlash"}
              </button>
            </div>
          </div>
        )}

        {!opt && error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}

/** Kartochka burchagidagi kichik qalamcha. */
export function MyGroupEditButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
      }}
      title="Guruhni tahrirlash"
      className="shrink-0 rounded-lg border border-slate-200 p-1.5 text-slate-400 hover:text-brand-600 hover:border-brand-300 transition"
    >
      <Pencil size={14} />
    </button>
  );
}
