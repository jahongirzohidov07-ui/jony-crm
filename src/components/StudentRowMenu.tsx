import { useEffect, useRef, useState } from "react";
import {
  MoreVertical, Play, RefreshCw, Trash2, X, Snowflake, Wallet,
  Undo2, UserX, Building2, Merge,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";
import { FREEZE_ROLES, STUDENT_TRANSFER, CASH_ACCESS, FOUNDER, can }
  from "../lib/roles";
import { api, ApiError, type Student, type Group, type CheckProblem }
  from "../lib/api";
import { ScheduleProblems } from "./ScheduleProblems";
import { StudentPayModal } from "./QuickPayment";
import { MergeStudents } from "./MergeStudents";

/** O'tkazish uchun guruh (boshqa filialdagilari ham) — 2026-09-23. */
interface XbGroup {
  id: number;
  name: string;
  branch_id: number | null;
  branch: string | null;
  same_branch: boolean;
  teacher: string | null;
  lesson_days: string | null;
  lesson_time: string | null;
  lesson_price: number;
  students: number;
  capacity: number | null;
}

/** move-group javobi: filial almashgan bo'lsa pul qayta hisoblanadi. */
interface MoveResult {
  group?: string;
  branch?: string | null;
  branch_changed?: boolean;
  task_for?: string | null;
  recharge?: {
    old: number; new: number; old_lessons: number; new_lessons: number;
  } | null;
}

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
  groupId,
  groupName,
}: {
  student: Student;
  groups: Group[];
  onChanged: () => void;
  /** Guruh sahifasidan ochilganda (2026-10-16): ikki guruhli o'quvchi
   *  faqat SHU guruhda muzlatiladi, ikkinchisida davom etadi. */
  groupId?: number;
  groupName?: string;
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = can(user?.role, FREEZE_ROLES);
  // O'tkazish — administratorga ham ochiq (2026-09-23). Qolgan
  // amallar (muzlatish, faollashtirish, o'chirish) avvalgidek.
  const canTransfer = can(user?.role, STUDENT_TRANSFER);
  const canCash = can(user?.role, CASH_ACCESS);
  const isFounder = can(user?.role, [FOUNDER]);
  const [open, setOpen] = useState(false);
  const [paying, setPaying] = useState(false);
  // Dublikatni birlashtirish (2026-08-20, Jahongir: "dublikat
  // qoshishni ham o'ng tomondan olib o'sha joyga qoshib ber") -
  // ilgari Guruhlar kartasining tepasida alohida tugma edi.
  const [merging, setMerging] = useState(false);
  const [freezing, setFreezing] = useState(false);
  const [fUntil, setFUntil] = useState("");
  const [fNote, setFNote] = useState("");
  // Muzlatish sababi — ro'yxatdan (2026-08-30, statistika uchun)
  const [fReason, setFReason] = useState("");
  const [fFrom, setFFrom] = useState(() => {
    const d = new Date();
    const p = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  });
  const [fPrev, setFPrev] = useState<{
    lessons: number; current: number; target: number;
  } | null>(null);
  // Faollashtirish: qaysi kundan o'qishni boshlagani so'raladi —
  // shu kundan oy oxirigacha nechta dars bo'lsa, shuncha pul yechiladi.
  const [activating, setActivating] = useState(false);
  const [aOn, setAOn] = useState(() =>
    new Date().toISOString().slice(0, 10)
  );
  const [aPrev, setAPrev] = useState<ActivatePreview | null>(null);
  // Boshqa filialga o'tkazish
  const [toBranch, setToBranch] = useState(false);
  const [bId, setBId] = useState("");
  const [bGroup, setBGroup] = useState("");
  const [bNote, setBNote] = useState("");
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
      setToBranch(false);
      setBId("");
      setBGroup("");
      setBNote("");
      setProblems([]);
      setPendingGroup(null);
      // Guruh/filial o'zgargan bo'lishi mumkin — o'tkazish ro'yxati
      // eskirmasin, keyingi ochilishda qaytadan olinadi (2026-09-23).
      setXbRows(null);
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
    run(async () => {
      const r = await api.post<{
        adjust?: { lessons: number; old: number; new: number } | null;
        charge?: { lessons: number; amount: number } | null;
      }>(`/students/${student.id}/activate`, { on: aOn });
      if (r && r.adjust) {
        alert(`Faollashtirildi. Jami ${r.adjust.lessons} dars: ` +
          `${som(r.adjust.old)} → ${som(r.adjust.new)} so'm`);
      } else if (r && r.charge) {
        alert(`Faollashtirildi. ${r.charge.lessons} dars uchun ` +
          `${som(r.charge.amount)} so'm hisoblandi`);
      }
    });

  const som = (n: number) =>
    Number(n || 0).toLocaleString().replace(/,/g, " ");

  /** Muzlatish sanasi bo'yicha nechta dars hisoblanishini oldindan
   *  ko'rsatadi — administrator summani bilib turib bosadi. */
  const loadPrev = (d: string) => {
    if (!d) { setFPrev(null); return; }
    api
      .get<{ lessons: number; current: number; target: number }>(
        `/students/${student.id}/freeze-preview?from_date=${d}`)
      .then(setFPrev)
      .catch(() => setFPrev(null));
  };

  const freeze = () => {
    if (!fUntil) { setErr("Qaytish sanasini belgilang"); return; }
    // 2026-08-30, Jahongir: "muzlatish sabablari statistikasi ham
    // kerak". Sabab ro'yxatdan tanlanmasa statistika yig'ilmaydi —
    // shuning uchun majburiy.
    if (!fReason) { setErr("Muzlatish sababini tanlang"); return; }
    run(async () => {
      // GURUH BO'YICHA (2026-10-16, Jahongir: "bir guruhini muzlatsa
      // ikkinchisi ham muzlayabdi, ikkalasi alohida alohida"). Guruh
      // sahifasidan bosilsa — avval faqat shu guruh muzlatiladi; bu
      // o'quvchining yagona faol guruhi bo'lsa — butun o'quvchi.
      if (groupId) {
        const label = freezeList.find(([k]) => k === fReason)?.[1] || fReason;
        try {
          const lr = await api.post<{ charge?: { old: number; new: number }
            | null }>(`/students/${student.id}/groups/${groupId}/freeze`,
            { from_date: fFrom || null, until: fUntil,
              note: [label, fNote].filter(Boolean).join(" — ") });
          const c = lr && lr.charge;
          alert(`Faqat «${groupName || "shu guruh"}» muzlatildi — boshqa ` +
            `guruhida o'qishda davom etadi.` +
            (c ? ` Shu oy hisobi: ${som(c.old)} → ${som(c.new)} so'm` : ""));
          return;
        } catch (e) {
          const m = e instanceof Error ? e.message : "";
          if (!m.includes("yagona faol guruhi")) throw e;
        }
      }
      const r = await api.post<{ adjust?: { lessons: number;
        old: number; new: number } | null }>(
        `/students/${student.id}/freeze`,
        { until: fUntil, from_date: fFrom || null,
          reason: fReason || null,
          note: fNote || null });
      const a = r && r.adjust;
      if (a) {
        alert(`Muzlatildi. ${a.lessons} dars hisoblandi: ` +
          `${som(a.old)} → ${som(a.new)} so'm`);
      }
    });
  };
  const toTrial = () =>
    run(() => api.post(`/students/${student.id}/to-trial`, {}));
  const toLead = () =>
    run(() => api.post(`/students/${student.id}/to-lead`, {}));

  const moveBranch = (force = false) =>
    run(() =>
      api.post(
        `/students/${student.id}/move-branch${force ? "?force=true" : ""}`,
        {
          branch_id: Number(bId),
          group_id: bGroup ? Number(bGroup) : null,
          note: bNote || null,
        }
      )
    );

  const moveTo = (groupId: number, force = false) => {
    setPendingGroup(groupId);
    if (!force) setProblems([]);
    return run(async () => {
      const r = await api.post<MoveResult>(
        `/students/${student.id}/move-group${force ? "?force=true" : ""}`,
        { group_id: groupId }
      );
      // Filial almashgan bo'lsa — nima bo'lganini aytib qo'yamiz:
      // pul qayta hisoblanadi va qabul qiluvchi filialga vazifa
      // tushadi (2026-09-23).
      if (r && r.branch_changed) {
        const lines = [`Ko'chirildi: ${r.group} — ${r.branch}`];
        if (r.recharge) {
          lines.push(
            `Shu oy hisobi: ${som(r.recharge.old)} → ` +
            `${som(r.recharge.new)} so'm ` +
            `(${r.recharge.old_lessons} dars eski guruhda, ` +
            `${r.recharge.new_lessons} dars yangisida)`);
        }
        if (r.task_for) {
          lines.push(`${r.task_for}ga "o'quvchini kutib oling" vazifasi ` +
            `yuborildi`);
        }
        alert(lines.join("\n"));
      }
    });
  };

  /** Boshqa filial guruhi — avval nima bo'lishini aytamiz. */
  const moveToOtherBranch = (g: XbGroup) => {
    const ok = confirm(
      `${g.name} — ${g.branch} filialida.\n\n` +
      "O'quvchi shu filialga o'tadi. Shu oyning hisobi qayta " +
      "hisoblanadi: eski guruhda o'tgan darslar eski narxda, yangi " +
      "guruhda qolgan darslar yangi narxda.\n\nDavom etamizmi?");
    if (ok) moveTo(g.id);
  };

  // KETISH SABABI — MAJBURIY (2026-08-24, Jahongir: "ketish
  // sababini majburiy qil").
  //
  // 2026-08-30 IKKI O'ZGARISH:
  //  1) RO'YXAT SERVERDAN. Ilgari u shu yerda QAYTA YOZILGAN edi
  //     va izohda "backend bilan aynan bir xil" deb turardi.
  //     Bunday nusxa albatta ajralib ketadi — bugun aynan shu
  //     sabab adminlar KPI'sida eski mantiq jonli saytda ishlab
  //     turgan edi. Endi manba bitta: /api/meta/reasons.
  //  2) RADIO EMAS, RO'YXAT. Jahongir: "sabab tanlash LIST
  //     ko'rinishida bo'lsin, bo'lmasa ko'rinmay ketyabdi" — 12 ta
  //     radio oynadan chiqib ketardi.
  const [reasonList, setReasonList] = useState<[string, string][]>([]);
  const [freezeList, setFreezeList] = useState<[string, string][]>([]);
  useEffect(() => {
    api.get<{ leave: { key: string; label: string }[];
              freeze: { key: string; label: string }[] }>("/meta/reasons")
      .then((m) => {
        setReasonList((m.leave || []).map((x) => [x.key, x.label]));
        setFreezeList((m.freeze || []).map((x) => [x.key, x.label]));
      })
      .catch(() => { /* ro'yxat kelmasa tugma bosilmaydi */ });
  }, []);
  const REMOVE_REASONS = reasonList;
  const [removing, setRemoving] = useState(false);
  const [rReason, setRReason] = useState("");
  const [rOther, setROther] = useState("");
  // QAYSI KUNGACHA (2026-08-20, Jahongir: "guruhdan talabani
  // chiqarishda, sana tanlaydigan bo'lsin va masalan tanlangan
  // sanagacha hisoblanib hisobi o'zgarsin va guruhdan chiqarilsin").
  const [rOn, setROn] = useState(() => new Date().toISOString().slice(0, 10));
  const [rPrev, setRPrev] = useState<{
    lessons: number; returned: number; current: number; target: number;
    changed: boolean; hint: string;
  } | null>(null);

  const loadLeavePrev = (dstr: string) => {
    if (!dstr) { setRPrev(null); return; }
    api
      .get<{ lessons: number; returned: number; current: number;
             target: number; changed: boolean; hint: string }>(
        `/students/${student.id}/leave-preview?on_date=${dstr}`)
      .then(setRPrev)
      .catch(() => setRPrev(null));
  };

  const removeFromGroup = () => {
    const t = new Date().toISOString().slice(0, 10);
    setRemoving(true);
    setRReason("");
    setROther("");
    setROn(t);
    loadLeavePrev(t);
  };

  const confirmRemove = () => {
    if (!rReason) {
      setErr("Ketish sababini ro'yxatdan tanlang — statistika shu "
        + "asosda yig'iladi");
      return;
    }
    const label =
      REMOVE_REASONS.find(([k]) => k === rReason)?.[1] || rReason;
    const note = rOther.trim();
    run(async () => {
      const r = await api.post<{ archived: boolean; debt: number }>(
        `/students/${student.id}/remove-from-group`,
        {
          reason: note ? `${label} — ${note}` : label,
          reason_code: rReason,
          on_date: rOn || null,
        }
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

  // O'TKAZISH RO'YXATI (2026-09-23). Ilgari bu yerda faqat O'SHA
  // FILIAL guruhlari chiqardi va boshqa filial alohida amal edi.
  // Endi ro'yxat serverdan keladi: o'z filiali guruhlari tepada,
  // boshqa filiallarniki pastda alohida bo'limda. /groups
  // serverda filial bo'yicha cheklangani uchun administrator
  // boshqa filial guruhini umuman ko'ra olmasdi.
  const [xbRows, setXbRows] = useState<XbGroup[] | null>(null);
  useEffect(() => {
    if (!moving || xbRows) return;
    api.get<{ rows: XbGroup[] }>(`/students/${student.id}/transfer-groups`)
      .then((d) => setXbRows(d.rows || []))
      .catch(() => setXbRows([]));   // kelmasa — pastdagi zaxira ro'yxat
  }, [moving, xbRows, student.id]);

  const myBranch = student.branch?.id ?? student.group?.branch_id ?? null;
  const others = groups.filter(
    (g) =>
      g.id !== student.group?.id &&
      (!myBranch || !g.branch_id || g.branch_id === myBranch)
  );
  const otherBranchGroups = groups.filter(
    (g) => g.branch_id && myBranch && g.branch_id !== myBranch
  );
  // Ro'yxat serverdan kelmasa (eski server, tarmoq xatosi) — eskicha
  // o'z filiali guruhlari ko'rsatiladi, ya'ni hech narsa yo'qolmaydi.
  const xbList: XbGroup[] = (xbRows && xbRows.length)
    ? xbRows
    : others.map((g) => ({
        id: g.id, name: g.name, branch_id: g.branch_id ?? null,
        branch: g.branch?.name ?? null, same_branch: true,
        teacher: g.teacher?.full_name ?? null,
        lesson_days: null, lesson_time: null,
        lesson_price: 0, students: 0, capacity: null,
      }));
  const xbSame = xbList.filter((g) => g.same_branch);
  const xbOther = xbList.filter((g) => !g.same_branch);
  const branchOptions = Array.from(
    new Map(
      otherBranchGroups
        .filter((g) => g.branch)
        .map((g) => [g.branch!.id, g.branch!])
    ).values()
  );

  if (!canManage && !canTransfer) return null;

  return (
    <div className="relative" ref={ref}>
      {paying && (
        <StudentPayModal
          student={student}
          onClose={() => setPaying(false)}
          onSaved={onChanged}
        />
      )}
      {merging && (
        <MergeStudents
          studentId={student.id}
          studentName={student.full_name}
          onClose={() => setMerging(false)}
          onDone={() => {
            setMerging(false);
            onChanged();
          }}
        />
      )}
      <button
        data-guide="student-menu"
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

            {/* QAYSI KUNGACHA (2026-08-20). Hisob shu sanagacha
                O'TILGAN darslar bo'yicha qayta hisoblanadi — kechikib
                kiritilsa ham o'quvchidan ortiqcha pul yechilmaydi. */}
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Qaysi kungacha o'qidi?
            </label>
            <input
              type="date"
              value={rOn}
              max={new Date().toISOString().slice(0, 10)}
              onChange={(e) => { setROn(e.target.value);
                loadLeavePrev(e.target.value); }}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-2"
            />
            {rPrev && (
              <p className="text-[11px] text-sky-800 bg-sky-50 rounded-lg px-2.5 py-2 mb-3 leading-snug">
                {rPrev.lessons} dars hisoblanadi
                {rPrev.changed ? (
                  <>
                    {" · "}
                    {rPrev.returned > 0
                      ? `${som(rPrev.returned)} so'm qaytariladi`
                      : `${som(-rPrev.returned)} so'm qo'shimcha hisoblanadi`}
                    {" · balans "}
                    {som(rPrev.current)} → <b>{som(rPrev.target)}</b> so'm
                  </>
                ) : (
                  <>{" · "}balans o'zgarmaydi</>
                )}
              </p>
            )}
            <p className="text-[11px] text-slate-500 mb-2">
              Sabab MAJBURIY — analitikada shu bo'yicha hisoblanadi
              (qaysi ustozdan, qaysi sababdan ko'p ketyapti).
            </p>
            <div className="space-y-1.5 mb-3">
              <select
                value={rReason}
                onChange={(e) => setRReason(e.target.value)}
                className={`w-full rounded-lg border px-3 py-2.5 text-sm bg-white ${
                  rReason ? "border-brand-400" : "border-slate-300"
                }`}
              >
                <option value="">— sababni tanlang —</option>
                {REMOVE_REASONS.map(([k, lbl]) => (
                  <option key={k} value={k}>{lbl}</option>
                ))}
              </select>
              {/* Kategoriya tanlangach — ixtiyoriy izoh. Tanlov
                  o'rnini bosmaydi, uni to'ldiradi. */}
              {rReason && (
                <input
                  value={rOther}
                  onChange={(e) => setROther(e.target.value)}
                  placeholder="Qo'shimcha izoh (ixtiyoriy)"
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

          {toBranch ? (
            <div className="px-3 py-2">
              <p className="text-xs font-medium text-slate-600 mb-1.5">
                Qaysi filialga? *
              </p>
              <select
                value={bId}
                onChange={(e) => { setBId(e.target.value); setBGroup(""); }}
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-2 bg-white"
              >
                <option value="">— filialni tanlang —</option>
                {branchOptions.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
              {bId && (
                <select
                  value={bGroup}
                  onChange={(e) => setBGroup(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-2 bg-white"
                >
                  <option value="">
                    — guruhni keyin administrator tanlaydi —
                  </option>
                  {otherBranchGroups
                    .filter((g) => String(g.branch_id) === bId)
                    .map((g) => (
                      <option key={g.id} value={g.id}>{g.name}</option>
                    ))}
                </select>
              )}
              <input
                value={bNote}
                onChange={(e) => setBNote(e.target.value)}
                placeholder="Sabab (ixtiyoriy)"
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-2"
              />
              <p className="text-[11px] text-slate-400 mb-2">
                Yangi filial administratoriga "o'quvchi keldi" vazifasi
                tushadi.
              </p>
              {problems.length > 0 && (
                <div className="mb-2">
                  <ScheduleProblems
                    problems={problems}
                    canForce={problems.every((p) => p.severity !== "block")}
                    saving={busy}
                    onForce={() => moveBranch(true)}
                  />
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={() => { setToBranch(false); setProblems([]); }}
                  className="flex-1 text-sm text-slate-500 py-1.5"
                >
                  Bekor
                </button>
                <button
                  onClick={() => moveBranch()}
                  disabled={busy || !bId}
                  className="flex-1 bg-violet-600 text-white rounded-lg py-1.5 text-sm font-medium disabled:opacity-40"
                >
                  O'tkazish
                </button>
              </div>
            </div>
          ) : activating ? (
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
                Qaysi kundan muzlatiladi?
              </p>
              <input type="date" value={fFrom}
                onChange={(e) => { setFFrom(e.target.value);
                  loadPrev(e.target.value); }}
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-1.5" />
              {fPrev && (
                <p className="text-[11px] text-sky-700 bg-sky-50 rounded-lg px-2 py-1 mb-1.5">
                  {fPrev.lessons} dars hisoblanadi · {som(fPrev.current)} → {" "}
                  <b>{som(fPrev.target)}</b> so'm
                </p>
              )}
              <p className="text-xs font-medium text-slate-600 mb-1.5">
                Qachon qaytadi? *
              </p>
              <input type="date" value={fUntil}
                onChange={(e) => { setFUntil(e.target.value);
                  if (!fPrev) loadPrev(fFrom); }}
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-1.5" />
              {/* SABAB RO'YXATDAN (2026-08-30). Ilgari erkin matn edi
                  va har kim har xil yozardi — statistika yig'ib
                  bo'lmasdi. */}
              <select value={fReason}
                onChange={(e) => setFReason(e.target.value)}
                className={`w-full border rounded-lg px-2 py-1.5 text-sm mb-1.5 bg-white ${
                  fReason ? "border-sky-400" : "border-slate-300"}`}>
                <option value="">— muzlatish sababi —</option>
                {freezeList.map(([k, lbl]) => (
                  <option key={k} value={k}>{lbl}</option>
                ))}
              </select>
              <input value={fNote}
                onChange={(e) => setFNote(e.target.value)}
                placeholder="Qo'shimcha izoh (ixtiyoriy)"
                className="w-full border border-slate-300 rounded-lg px-2 py-1.5 text-sm mb-2" />
              <p className="text-[11px] text-slate-400 mb-2">
                Shu sanada adminlarga "aloqaga chiqing" vazifasi tushadi.
              </p>
              <div className="flex gap-2">
                <button onClick={() => setFreezing(false)}
                  className="flex-1 text-sm text-slate-500 py-1.5">
                  Bekor
                </button>
                <button onClick={freeze} disabled={busy || !fUntil || !fReason}
                  className="flex-1 bg-sky-600 text-white rounded-lg py-1.5 text-sm font-medium disabled:opacity-40">
                  Muzlatish
                </button>
              </div>
            </div>
          ) : !moving ? (
            <>
              {/* Ilgari bu tugma o'quvchi kartasiga OLIB O'TARDI - to'lov
                  uch bosishga cho'zilardi. Endi oyna shu yerda ochiladi
                  (Jahongir, 2026-08-12: "oson bolsin topish"). */}
              <button
                onClick={() => {
                  setOpen(false);
                  if (canCash) setPaying(true);
                  else navigate(`/students/${student.id}`);
                }}
                disabled={busy}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <Wallet size={15} className="text-emerald-600" />
                To'lov qabul qilish
              </button>
              {/* Faollashtirish/muzlatish/qaytarish — avvalgi rollar.
                  Administratorda menyu endi ochiladi (o'tkazish
                  uchun), lekin bu amallar unga ko'rinmaydi. */}
              {canManage && (
              <>
              <button
                onClick={() => { setActivating(true); setErr(""); }}
                disabled={busy || student.status === "active"}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white"
              >
                <Play size={15} className="text-emerald-600" />
                Faollashtirish
              </button>
              <button
                data-guide="student-menu-freeze"
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
              </>
              )}
              <button
                data-guide="student-menu-move"
                onClick={() => setMoving(true)}
                disabled={busy}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <RefreshCw size={15} className="text-sky-600" />
                Boshqa guruhga o'tkazish
              </button>
              {branchOptions.length > 0 && (
                <button
                  onClick={() => { setToBranch(true); setErr(""); }}
                  disabled={busy}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <Building2 size={15} className="text-violet-600" />
                  Boshqa filialga o'tkazish
                </button>
              )}
              {isFounder && (
                <button
                  onClick={() => { setOpen(false); setMerging(true); }}
                  disabled={busy}
                  title="Shu odamning ikkinchi yozuvi bo'lsa — bitta qilish"
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <Merge size={15} className="text-slate-500" />
                  Dublikatni qo'shish
                </button>
              )}
              {canManage && (
                <button
                  data-guide="student-menu-remove"
                  onClick={removeFromGroup}
                  disabled={busy}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <Trash2 size={15} />
                  O'chirish
                </button>
              )}
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
              <div className="max-h-64 overflow-y-auto">
                {xbList.length === 0 ? (
                  <p className="text-xs text-slate-400 px-3 py-2">
                    {xbRows === null ? "Yuklanmoqda…" : "Boshqa guruh yo'q"}
                  </p>
                ) : (
                  <>
                    {xbSame.map((g) => (
                      <button
                        key={g.id}
                        onClick={() => moveTo(g.id)}
                        disabled={busy}
                        className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                      >
                        {g.name}
                        {(g.teacher || g.lesson_time) && (
                          <span className="block text-xs text-slate-400">
                            {[g.teacher, g.lesson_time]
                              .filter(Boolean).join(" · ")}
                          </span>
                        )}
                      </button>
                    ))}
                    {/* BOSHQA FILIALLAR (2026-09-23). Tanlansa filial
                        ham almashadi va shu oyning hisobi qayta
                        bo'linadi — shuning uchun avval so'raladi. */}
                    {xbOther.length > 0 && (
                      <>
                        <div className="sticky top-0 px-3 pt-2 pb-1 text-[11px] font-semibold text-violet-700 bg-violet-50">
                          Boshqa filiallar
                        </div>
                        {xbOther.map((g) => (
                          <button
                            key={g.id}
                            onClick={() => moveToOtherBranch(g)}
                            disabled={busy}
                            className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-violet-50/60"
                          >
                            <span className="flex items-center gap-1.5">
                              <Building2 size={13}
                                className="text-violet-500 shrink-0" />
                              {g.name}
                            </span>
                            <span className="block text-xs text-slate-400 pl-[18px]">
                              {[g.branch, g.teacher, g.lesson_time]
                                .filter(Boolean).join(" · ")}
                              {g.lesson_price
                                ? ` · ${som(g.lesson_price)} so'm/dars`
                                : ""}
                            </span>
                          </button>
                        ))}
                      </>
                    )}
                  </>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
