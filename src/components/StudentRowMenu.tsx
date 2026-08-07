import { useEffect, useRef, useState } from "react";
import {
  MoreVertical, Play, RefreshCw, Trash2, X, Snowflake, Wallet,
  Undo2, UserX,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";
import { FREEZE_ROLES, can } from "../lib/roles";
import { api, ApiError, type Student, type Group, type CheckProblem }
  from "../lib/api";
import { ScheduleProblems } from "./ScheduleProblems";

/** Faollashtirishdan oldin: shu sanadan qancha pul yechilishi. */
interface ActivatePreview {
  lessons: number;
  amount: number;
  discount: number;
  already: boolean;
  group: string | null;
  lesson_price?: number;
  cap: number;
  hint: string;
}

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
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = can(user?.role, FREEZE_ROLES);
  const [open, setOpen] = useState(false);
  const [freezing, setFreezing] = useState(false);
  const [fUntil, setFUntil] = useState("");
  const [fNote, setFNote] = useState("");
  // Faollashtirish: qaysi kundan o'qishni boshlagani so'raladi —
  // shu kundan oy oxirigacha nechta dars bo'lsa, shuncha pul yechiladi.
  const [activating, setActivating] = useState(false);
  const [aOn, setAOn] = useState(() =>
    new Date().toISOString().slice(0, 10)
  );
  const [aPrev, setAPrev] = useState<ActivatePreview | null>(null);
  const [moving, setMoving] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  // Sig'im va daraja tekshiruvi natijasi
  const [problems, setProblems] = useState<CheckProblem[]>([]);
  const [pendingGroup, setPendingGroup] = useState<number | null>(null);
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
      setActivating(false);
      setAPrev(null);
      setProblems([]);
      setPendingGroup(null);
      onChanged();
    } catch (e) {
      if (e instanceof ApiError && e.problems.length) {
        setProblems(e.problems);
        setErr("");
      } else {
        setErr(e instanceof Error ? e.message : "Xatolik");
      }
    } finally {
      setBusy(false);
    }
  }

  // Sana o'zgarganda qancha pul yechilishini oldindan ko'rsatamiz
  useEffect(() => {
    if (!activating || !aOn) return;
    let alive = true;
    api
      .get<ActivatePreview>(
        `/students/${student.id}/activate-preview?on=${aOn}`
      )
      .then((p) => alive && setAPrev(p))
      .catch(() => alive && setAPrev(null));
    return () => {
      alive = false;
    };
  }, [activating, aOn, student.id]);

  const activate = () =>
    run(() => api.post(`/students/${student.id}/activate`, { on: aOn }));

  const freeze = () => {
    if (!fUntil) { setErr("Qaytish sanasini belgilang"); return; }
    run(() => api.post(`/students/${student.id}/freeze`,
      { until: fUntil, note: fNote || null }));
  };
  const toTrial = () =>
    run(() => api.post(`/students/${student.id}/to-trial`, {}));
  const toLead = () =>
    run(() => api.post(`/students/${student.id}/to-lead`, {}));

  const moveTo = (groupId: number, force = false) => {
    setPendingGroup(groupId);
    if (!force) setProblems([]);
    return run(() =>
      api.post(
        `/students/${student.id}/move-group${force ? "?force=true" : ""}`,
        { group_id: groupId }
      )
    );
  };

  // Chiqarish sabablari — ustozlar aniq bilishi uchun ro'yxatdan
  // tanlanadi; "Boshqa sabab"da qo'lda yoziladi.
  const REMOVE_REASONS = [
    "Dars yoqmadi",
    "Boshqa joyga ko'chib ketdi",
    "Yo'nalishini o'zgartirdi",
    "Umuman bog'lanib bo'lmayapti",
    "Narx to'g'ri kelmadi",
    "Vaqti to'g'ri kelmadi",
  ];
  const [removing, setRemoving] = useState(false);
  const [rReason, setRReason] = useState("");
  const [rOther, setROther] = useState("");

  const removeFromGroup = () => {
    setRemoving(true);
    setRReason("");
    setROther("");
  };

  const confirmRemove = () => {
    const reason = rReason === "__other__" ? rOther.trim() : rReason;
    if (!reason) {
      setErr("Chiqarish sababini tanlang yoki yozing");
      return;
    }
    run(async () => {
      const r = await api.post<{ archived: boolean; debt: number }>(
        `/students/${student.id}/remove-from-group`,
        { reason }
      );
      setRemoving(false);
      alert(
        r.archived
          ? "O'quvchi guruhdan chiqarildi va arxivga o'tkazildi."
          : `O'quvchi guruhdan chiqarildi. ${r.debt.toLocaleString()} so'm ` +
            "qarzi borligi uchun arxivga tushmadi — qarz to'langach " +
            "avtomat arxivga o'tadi."
      );
      return r;
    });
  };

  const others = groups.filter((g) => g.id !== student.group?.id);

  if (!canManage) return null;

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

      {removing && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="bg-white rounded-xl w-full max-w-sm p-5 shadow-xl">
            <h3 className="font-semibold text-slate-900 mb-1">
              Guruhdan chiqarish
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              {student.full_name} — sababni tanlang. Qarzi bo'lmasa arxivga
              o'tadi, qarzi bo'lsa to'langach avtomat arxivlanadi.
            </p>
            <div className="space-y-1.5 mb-3">
              {REMOVE_REASONS.map((r) => (
                <label
                  key={r}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer ${
                    rReason === r
                      ? "border-brand-500 bg-brand-50 text-brand-800"
                      : "border-slate-200 text-slate-700 hover:border-slate-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="rm-reason"
                    checked={rReason === r}
                    onChange={() => setRReason(r)}
                  />
                  {r}
                </label>
              ))}
              <label
                className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer ${
                  rReason === "__other__"
                    ? "border-brand-500 bg-brand-50 text-brand-800"
                    : "border-slate-200 text-slate-700 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="rm-reason"
                  checked={rReason === "__other__"}
                  onChange={() => setRReason("__other__")}
                />
                Boshqa sabab
              </label>
              {rReason === "__other__" && (
                <input
                  value={rOther}
                  onChange={(e) => setROther(e.target.value)}
                  placeholder="Sababni yozing"
                  autoFocus
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              )}
            </div>
            {err && <p className="text-xs text-red-600 mb-2">{err}</p>}
            <div className="flex gap-2">
              <button
                onClick={confirmRemove}
                disabled={busy}
                className="flex-1 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                Chiqarish
              </button>
              <button
                onClick={() => setRemoving(false)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
              >
                Bekor
              </button>
            </div>
          </div>
        </div>
      )}

      {open && (
        <div className="absolute right-0 top-7 z-30 w-60 bg-white rounded-xl border border-slate-200 shadow-lg py-1.5">
          {err && (
            <p className="text-xs text-red-600 px-3 py-1.5">{err}</p>
          )}

          {problems.length > 0 && (
            <div className="px-2 pb-1">
              <ScheduleProblems
                problems={problems}
                canForce={problems.every((p) => p.severity !== "block")}
                saving={busy}
                onForce={() =>
                  pendingGroup !== null && moveTo(pendingGroup, true)
                }
              />
            </div>
          )}

          {activating ? (
            <div className="px-3 py-2">
              <p className="text-xs font-medium text-slate-600 mb-1.5">
                Qaysi kundan o'qishni boshladi? *
              </p>
              <input
                type="date"
                value={aOn}
                max={new Date().toISOString().slice(0, 10)}
                onChange={(e) => setAOn(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-2"
              />
              {aPrev && (
                <div
                  className={`rounded-lg px-2.5 py-2 mb-2 text-xs ${
                    aPrev.already
                      ? "bg-slate-50 text-slate-500"
                      : "bg-emerald-50 text-emerald-800"
                  }`}
                >
                  {aPrev.already ? (
                    aPrev.hint
                  ) : (
                    <>
                      Hisobidan{" "}
                      <b>{aPrev.amount.toLocaleString("ru-RU")} so'm</b>{" "}
                      yechiladi
                      <div className="text-[11px] opacity-80 mt-0.5">
                        {aPrev.hint}
                        {aPrev.lessons >= aPrev.cap &&
                          " — oyiga eng ko'pi 12 dars, ortig'i bonus"}
                      </div>
                    </>
                  )}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => { setActivating(false); setAPrev(null); }}
                  className="flex-1 text-sm text-slate-500 py-1.5"
                >
                  Bekor
                </button>
                <button
                  onClick={activate}
                  disabled={busy || !aOn}
                  className="flex-1 bg-emerald-600 text-white rounded-lg py-1.5 text-sm font-medium disabled:opacity-40"
                >
                  Faollashtirish
                </button>
              </div>
            </div>
          ) : freezing ? (
            <div className="px-3 py-2">
              <p className="text-xs font-medium text-slate-600 mb-1.5">
                Muzlatish — qachon qaytadi? *
              </p>
              <input type="date" value={fUntil}
                onChange={(e) => setFUntil(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-1.5" />
              <input value={fNote}
                onChange={(e) => setFNote(e.target.value)}
                placeholder="Sabab (ixtiyoriy)"
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-2" />
              <p className="text-[11px] text-slate-400 mb-2">
                Shu sanada adminlarga "aloqaga chiqing" vazifasi tushadi.
              </p>
              <div className="flex gap-2">
                <button onClick={() => setFreezing(false)}
                  className="flex-1 text-sm text-slate-500 py-1.5">
                  Bekor
                </button>
                <button onClick={freeze} disabled={busy || !fUntil}
                  className="flex-1 bg-sky-600 text-white rounded-lg py-1.5 text-sm font-medium disabled:opacity-40">
                  Muzlatish
                </button>
              </div>
            </div>
          ) : !moving ? (
            <>
              <button
                onClick={() => {
                  setOpen(false);
                  navigate(`/students/${student.id}`);
                }}
                disabled={busy}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <Wallet size={15} className="text-emerald-600" />
                To'lov qo'shish
              </button>
              <button
                onClick={() => { setActivating(true); setErr(""); }}
                disabled={busy || student.status === "active"}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white"
              >
                <Play size={15} className="text-emerald-600" />
                Faollashtirish
              </button>
              <button
                onClick={() => { setFreezing(true); setErr(""); }}
                disabled={busy || student.status === "frozen"}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                <Snowflake size={15} className="text-sky-600" />
                Muzlatish
              </button>
              {student.status === "active" && (
                <button
                  onClick={toTrial}
                  disabled={busy}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <Undo2 size={15} className="text-amber-600" />
                  Sinov darsiga qaytarish
                </button>
              )}
              {student.status === "trial" && (
                <button
                  onClick={toLead}
                  disabled={busy}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <UserX size={15} className="text-amber-600" />
                  Lid bo'limiga qaytarish
                </button>
              )}
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
