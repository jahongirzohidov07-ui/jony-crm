import { useEffect, useRef, useState } from "react";
import { MoreVertical, Play, RefreshCw, Trash2, X } from "lucide-react";
import { api, type Student, type Group } from "../lib/api";

/**
 * Guruh ro'yxatidagi o'quvchi yonidagi uch nuqta menyusi:
 * Faollashtirish · Boshqa guruhga o'tkazish · O'chirish.
 *
 * "O'chirish" — guruhdan chiqarish, o'quvchi bazada qoladi: to'lov tarixi
 * va davomati yo'qolmasligi kerak.
 */
export function StudentRowMenu({
  student,
  groups,
  onChanged,
}: {
  student: Student;
  groups: Group[];
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [moving, setMoving] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  // Tashqariga bosilganda yopiladi.
  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setErr("");
    try {
      await fn();
      setOpen(false);
      setMoving(false);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  const activate = () =>
    run(() => api.post(`/students/${student.id}/activate`, {}));

  const moveTo = (groupId: number) =>
    run(() =>
      api.post(`/students/${student.id}/move-group`, { group_id: groupId })
    );

  const removeFromGroup = () => {
    if (
      !confirm(
        `${student.full_name} guruhdan chiqarilsinmi?\n\n` +
          "O'quvchi bazada qoladi — to'lov tarixi va davomati saqlanadi."
      )
    )
      return;
    run(() =>
      api.post(`/students/${student.id}/move-group`, { group_id: null })
    );
  };

  const others = groups.filter((g) => g.id !== student.group?.id);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen((v) => !v);
          setMoving(false);
        }}
        className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100"
        title="Amallar"
      >
        <MoreVertical size={15} />
      </button>

      {open && (
        <div className="absolute right-0 top-7 z-30 w-60 bg-white rounded-xl border border-slate-200 shadow-lg py-1.5">
          {err && (
            <p className="text-xs text-red-600 px-3 py-1.5">{err}</p>
          )}

          {!moving ? (
            <>
              <button
                onClick={activate}
                disabled={busy || student.status === "active"}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white"
              >
                <Play size={15} className="text-emerald-600" />
                Faollashtirish
              </button>
              <button
                onClick={() => setMoving(true)}
                disabled={busy}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <RefreshCw size={15} className="text-sky-600" />
                Boshqa guruhga o'tkazish
              </button>
              <button
                onClick={removeFromGroup}
                disabled={busy}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <Trash2 size={15} />
                O'chirish
              </button>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between px-3 py-1.5">
                <span className="text-xs font-medium text-slate-500">
                  Qaysi guruhga?
                </span>
                <button
                  onClick={() => setMoving(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X size={13} />
                </button>
              </div>
              <div className="max-h-56 overflow-y-auto">
                {others.length === 0 ? (
                  <p className="text-xs text-slate-400 px-3 py-2">
                    Boshqa guruh yo'q
                  </p>
                ) : (
                  others.map((g) => (
                    <button
                      key={g.id}
                      onClick={() => moveTo(g.id)}
                      disabled={busy}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      {g.name}
                      {g.teacher?.full_name && (
                        <span className="block text-xs text-slate-400">
                          {g.teacher.full_name}
                        </span>
                      )}
                    </button>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
