import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import {
  api,
  type Group,
  type Teacher,
  type Lesson,
  type BillingRunResult,
  type PayrollRunResult,
  type TeacherPayout,
  type Branch,
  type Student,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, FINANCE_ACCESS, can, ACADEMIC_HEAD, HR_MANAGER, SALES_MANAGER, ADMINISTRATOR, TEACHER, SUPPORT_TEACHER } from "../lib/roles";
import { exportToExcel } from "../lib/exportXlsx";
import { QuickXp } from "../components/XpAdmin";
import {
  AttendanceTab,
  GradesTab,
  ExamsTab,
  SupportAttendanceTab,
} from "../components/GroupGrids";
import { GroupHomeworkTab, GroupHistoryTab, GroupNotesTab } from "../components/GroupExtras";
import { GroupSidebar } from "../components/GroupSidebar";
import { MyGroupEditModal } from "../components/MyGroupEdit";
import { GroupFormModal } from "./Groups";

type GroupTab =
  | "attendance"
  | "support"
  | "grades"
  | "exams"
  | "xp"
  | "homework"
  | "mashqlar"
  | "history"
  | "notes";

const GROUP_TABS: { key: GroupTab; label: string }[] = [
  { key: "attendance", label: "Davomat" },
  { key: "support", label: "Support davomati" },
  { key: "homework", label: "Uyga vazifalar" },
  { key: "mashqlar", label: "Mashqlar" },
  { key: "grades", label: "Baholash" },
  { key: "exams", label: "Imtihonlar" },
  { key: "xp", label: "Tezkor XP" },
  { key: "history", label: "Tarix" },
  { key: "notes", label: "Izoh: chegirma" },
];

const MONTH_NAMES = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];

function today() {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() + 1, iso: d.toISOString().slice(0, 10) };
}

export default function GroupDetail() {
  const { id } = useParams();
  const groupId = Number(id);
  const { user } = useAuth();
  const [editOpen, setEditOpen] = useState(false);
  // USTOZNING O'Z GURUHI (2026-09-01, Jahongir: "ustozlar o'zlarini
  // guruhlarini edit qilishda ... huquqi bolsin"). Bu katta forma
  // emas — faqat nom/daraja/vaqt/xona uchun tor oyna.
  const [myEditOpen, setMyEditOpen] = useState(false);
  const [branches, setBranches] = useState<Branch[]>([]);
  const t = today();

  const [group, setGroup] = useState<Group | null>(null);
  const [groupError, setGroupError] = useState<string | null>(null);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [lessonsLoading, setLessonsLoading] = useState(true);
  // Guruh ochilganda birinchi bo'lib o'quvchilar va davomat ko'rinadi.
  const [tab, setTab] = useState<GroupTab>("attendance");
  const [selYear, setSelYear] = useState(t.year);
  const [selMonth, setSelMonth] = useState(t.month);

  const [lessonDate, setLessonDate] = useState(t.iso);
  const [lessonTeacherId, setLessonTeacherId] = useState("");
  const [addingLesson, setAddingLesson] = useState(false);
  const [lessonError, setLessonError] = useState<string | null>(null);

  const [billingResult, setBillingResult] = useState<BillingRunResult | null>(null);
  const [billingLoading, setBillingLoading] = useState(false);
  const [payrollResult, setPayrollResult] = useState<PayrollRunResult | null>(null);
  const [payrollLoading, setPayrollLoading] = useState(false);
  const [persistedPayouts, setPersistedPayouts] = useState<TeacherPayout[]>([]);

  // Rahbar o'zi dars beradigan guruhda yo'qlama/baho qo'ya olmaydi —
  // yo'qlama pul hujjati, o'z oyligini o'zi yozib qo'ymasligi kerak.
  const [ownLock, setOwnLock] = useState<{
    locked: boolean; reason: string | null; own_group?: boolean;
  } | null>(null);
  useEffect(() => {
    if (!groupId) return;
    api
      .get<{ locked: boolean; reason: string | null; own_group?: boolean }>(
        `/groups/${groupId}/my-access`,
      )
      .then(setOwnLock)
      .catch(() => setOwnLock(null));
  }, [groupId]);

  const canMarkLesson =
    (can(user?.role, TEACHING_STAFF) || user?.role === "hr_manager") &&
    !ownLock?.locked;
  // Support ustozning DAVOMAT varag'iga tegmaydi — uning o'z varag'i
  // bor ("Support davomati"). Ilgari ikkalasi bitta jadvalga yozardi
  // va support belgi qo'yganda ustozning yoqlamasi o'chib ketardi.
  // Baholash va imtihonlar supportda o'zgarishsiz qoladi.
  const isSupport =
    user?.role === "support_teacher" || user?.role === "head_support";
  const canFinance = can(user?.role, FINANCE_ACCESS);
  // Imtihon yaratish/baholash ustoz va supportdan olib tashlandi -
  // ular faqat buyurtma beradi (Jahongir)
  const isTeacherRole =
    user?.role === TEACHER || user?.role === SUPPORT_TEACHER;
  const canExamManage = canMarkLesson && !isTeacherRole;
  // Guruhni tahrirlash qalami: moliya ruxsati borlar + o'quv bo'limi
  // rahbari, administrator, HR (Jahongir so'radi)
  const canGroupEdit =
    canFinance ||
    can(user?.role, [ACADEMIC_HEAD, HR_MANAGER, SALES_MANAGER, ADMINISTRATOR]);
  // Guruhning O'Z ustozi — rahbariyat ruxsati bo'lmasa ham qalamcha
  // ko'rinadi, lekin u tor oynani ochadi (narx/ustoz/filialga
  // tegmaydi).
  const isOwnTeacher = Boolean(ownLock?.own_group);

  // Tezkor XP uchun guruhdagi o'quvchilar ro'yxati
  const [groupStudents, setGroupStudents] = useState<Student[]>([]);
  function loadStudents() {
    api
      .get<Student[]>(`/students?group_id=${groupId}`)
      .then((rows) => setGroupStudents(rows.filter(
        (s) => s.status === "active" || s.status === "trial")))
      .catch(() => setGroupStudents([]));
  }
  useEffect(loadStudents, [groupId]);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  function teacherName(id?: number | null): string {
    if (!id) return "—";
    return teachers.find((x) => x.id === id)?.full_name || `#${id}`;
  }

  function loadGroup() {
    setGroupError(null);
    api
      .get<Group>(`/groups/${groupId}`)
      .then((g) => {
        setGroup(g);
        setLessonTeacherId((prev) => prev || (g.teacher_id ? String(g.teacher_id) : ""));
      })
      .catch((e) =>
        setGroupError(e instanceof Error ? e.message : "Guruhni yuklab bo'lmadi")
      );
    api.get<Teacher[]>("/teachers").then(setTeachers).catch(() => setTeachers([]));
  }

  function loadLessons(y: number, m: number) {
    setLessonsLoading(true);
    api
      .get<Lesson[]>(`/groups/${groupId}/lessons?year=${y}&month=${m}`)
      .then(setLessons)
      .finally(() => setLessonsLoading(false));
  }

  function loadPersistedPayouts(y: number, m: number) {
    if (!canGroupEdit) return;
    api
      .get<TeacherPayout[]>(`/payouts?year=${y}&month=${m}`)
      .then((all) => setPersistedPayouts(all.filter((p) => p.group_id === groupId)))
      .catch(() => setPersistedPayouts([]));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadGroup, [groupId]);

  useEffect(() => {
    loadLessons(selYear, selMonth);
    setBillingResult(null);
    setPayrollResult(null);
    loadPersistedPayouts(selYear, selMonth);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupId, selYear, selMonth]);

  async function addLesson() {
    setAddingLesson(true);
    setLessonError(null);
    try {
      await api.post(`/groups/${groupId}/lessons`, {
        date: lessonDate,
        teacher_id: lessonTeacherId ? Number(lessonTeacherId) : null,
      });
      loadLessons(selYear, selMonth);
    } catch (e) {
      setLessonError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setAddingLesson(false);
    }
  }

  async function deleteLesson(lessonId: number) {
    await api.delete(`/lessons/${lessonId}`);
    loadLessons(selYear, selMonth);
  }

  async function runBilling(commit: boolean) {
    if (commit) {
      const ok = confirm(
        `${selYear}-${String(selMonth).padStart(2, "0")} uchun hisoblangan to'lovlarni talabalar balansiga yozishni tasdiqlaysizmi? Bu moliyaviy amal.`
      );
      if (!ok) return;
    }
    setBillingLoading(true);
    try {
      const r = await api.post<BillingRunResult>(
        `/groups/${groupId}/billing/run?year=${selYear}&month=${selMonth}&commit=${commit}`
      );
      setBillingResult(r);
    } finally {
      setBillingLoading(false);
    }
  }

  async function runPayroll(commit: boolean) {
    setPayrollLoading(true);
    try {
      const r = await api.post<PayrollRunResult>(
        `/groups/${groupId}/payroll/run?year=${selYear}&month=${selMonth}&commit=${commit}`
      );
      setPayrollResult(r);
      if (commit) loadPersistedPayouts(selYear, selMonth);
    } finally {
      setPayrollLoading(false);
    }
  }

  async function togglePaid(payout: TeacherPayout) {
    if (!payout.id) return;
    await api.put(`/payouts/${payout.id}`, { paid: !payout.paid });
    loadPersistedPayouts(selYear, selMonth);
  }

  function exportBilling() {
    if (!billingResult || !group) return;
    exportToExcel(
      `${group.name}-hisobkitob-${billingResult.period}`,
      "Hisob-kitob",
      billingResult.results.map((r) => ({
        Talaba: r.student_name,
        Darslar: r.billable_lessons,
        "Summa (so'm)": Math.round(r.amount),
        Holat: r.created ? "yozildi" : r.already_charged ? "allaqachon hisoblangan" : "—",
      }))
    );
  }

  function exportPayroll() {
    if (!group) return;
    const rows = (payrollResult?.results ?? persistedPayouts).map((r) => ({
      "O'qituvchi": r.teacher?.full_name || teacherName(r.teacher_id),
      "O'tgan dars": r.taught_lessons,
      "Jami dars": r.held_lessons,
      Talabalar: r.student_count,
      "Summa (so'm)": Math.round(r.amount),
      "To'landimi": r.paid ? "Ha" : "Yo'q",
    }));
    exportToExcel(
      `${group.name}-ish-haqi-${payrollResult?.period ?? `${selYear}-${String(selMonth).padStart(2, "0")}`}`,
      "Ish haqi",
      rows
    );
  }

  if (!group) {
    // Darslar tabi olib tashlandi (platforma avtomat hisoblaydi).
  // Eski yordamchilar keyin kerak bo'lishi mumkin — hozircha saqlanadi.
  void lessons; void lessonsLoading; void setLessonDate;
  void addingLesson; void lessonError; void billingLoading;
  void payrollLoading; void addLesson; void deleteLesson;
  void runBilling; void runPayroll; void togglePaid;
  void exportBilling; void exportPayroll;

  // Xato bo'lsa ABADIY "Yuklanmoqda..."da qotib qolmasin — sabab va
  // qayta urinish tugmasi ko'rsatiladi (2026-08-09, ustoz o'z
  // guruhiga kirolmasligi haqida xabar berdi: sabab shu — xato
  // hech qachon ko'rinmagan, sahifa abadiy kutib turaverardi).
  if (groupError) {
    return (
      <div className="p-8">
        <p className="text-sm text-red-600 mb-3">{groupError}</p>
        <button
          onClick={loadGroup}
          className="text-sm text-brand-600 hover:text-brand-700 underline"
        >
          Qayta urinish
        </button>
      </div>
    );
  }

  return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      </div>
    );
  }

  const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);
  const yearOptions = [t.year - 1, t.year, t.year + 1];

  return (
    <div className="p-8">
      <Link
        to="/groups"
        className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-4"
      >
        <ArrowLeft size={15} /> Guruhlarga qaytish
      </Link>

      {/* Chapda guruh ma'lumoti va o'quvchilar, o'ngda davomat jadvali */}
      <div className="flex flex-col lg:flex-row gap-5 items-start">
        <GroupSidebar
          group={group}
          onEdit={
            canGroupEdit
              ? () => setEditOpen(true)
              : isOwnTeacher
                ? () => setMyEditOpen(true)
                : undefined
          }
        />

        <div className="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex gap-1 mb-5 border-b border-slate-200 overflow-x-auto">
            {GROUP_TABS.map((tb) => (
              <button
                key={tb.key}
                data-guide={"gtab-" + tb.key}
                onClick={() => setTab(tb.key)}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition whitespace-nowrap ${
                  tab === tb.key
                    ? "border-brand-600 text-brand-700"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {tb.label}
              </button>
            ))}
          </div>

          {ownLock?.locked && (
            <div className="mb-5 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
              <p className="text-sm text-amber-900">{ownLock.reason}</p>
            </div>
          )}

          <div className="flex items-center gap-2 mb-5">
            <select
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={selMonth}
              onChange={(e) => setSelMonth(Number(e.target.value))}
            >
              {monthOptions.map((m) => (
                <option key={m} value={m}>
                  {MONTH_NAMES[m - 1]}
                </option>
              ))}
            </select>
            <select
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={selYear}
              onChange={(e) => setSelYear(Number(e.target.value))}
            >
              {yearOptions.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>

      {tab === "xp" && (
        <QuickXp students={groupStudents} onDone={loadStudents} />
      )}
      {tab === "attendance" && (
        <AttendanceTab
          groupId={group.id}
          year={selYear}
          month={selMonth}
          canEdit={canMarkLesson && !isSupport}
        />
      )}
      {tab === "support" && (
        <SupportAttendanceTab
          groupId={group.id}
          year={selYear}
          month={selMonth}
        />
      )}
      {tab === "grades" && (
        <GradesTab
          groupId={group.id}
          year={selYear}
          month={selMonth}
          canEdit={canMarkLesson}
        />
      )}
      {tab === "exams" && (
        <>
          {isTeacherRole && (
            <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 mb-3">
              Imtihonni examiner o'tkazadi va baholaydi. Sizga imtihon
              kerak bo'lsa — "Imtihonlarim" bo'limidan buyurtma bering.
            </p>
          )}
          <ExamsTab
            groupId={group.id}
            canEdit={canExamManage}
            canDelete={canFinance}
          />
        </>
      )}

      {tab === "homework" && <GroupHomeworkTab groupId={groupId} />}
      {tab === "mashqlar" && (
        <ExercisesTab groupId={group.id} canEdit={canMarkLesson} />
      )}
      {tab === "history" && <GroupHistoryTab groupId={groupId} />}
      {tab === "notes" && <GroupNotesTab groupId={groupId} />}
        </div>
      </div>

      {editOpen && group && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={group.branch_id ?? null}
          initial={group}
          submitLabel="Saqlash"
          onClose={() => setEditOpen(false)}
          onSaved={() => {
            setEditOpen(false);
            loadGroup();
          }}
        />
      )}

      {myEditOpen && group && (
        <MyGroupEditModal
          groupId={group.id}
          onClose={() => setMyEditOpen(false)}
          onSaved={loadGroup}
        />
      )}
    </div>
  );
}


// ---------------------------------------------------------------
// MASHQLAR: har bir o'quvchining to'g'ri/noto'g'ri javoblari, ball
// va daraja zinasi (Beginner -> Native, IELTS/CEFR mo'ljali bilan).
// Ustoz kiritadi, o'quv bo'limi rahbari kuzatadi.
type ExLevel = { key: string; label: string; ielts: string; cefr: string };
type ExRow = {
  student_id: number;
  full_name: string;
  done: number;
  percent: number;
  points: number;
  level: ExLevel;
  next: {
    label: string; ielts: string; cefr: string;
    points_left: number; progress_percent: number;
  } | null;
};

function ExercisesTab({ groupId, canEdit }: {
  groupId: number; canEdit: boolean;
}) {
  const [rows, setRows] = useState<ExRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [forId, setForId] = useState<number | null>(null);
  const [total, setTotal] = useState("");
  const [correct, setCorrect] = useState("");
  const [topic, setTopic] = useState("");
  const [err, setErr] = useState("");

  function load() {
    setLoading(true);
    api
      .get<{ rows: ExRow[] }>(`/groups/${groupId}/exercises-stats`)
      .then((r) => setRows(r.rows))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }
  useEffect(load, [groupId]);

  async function save() {
    const t = Number(total), c = Number(correct);
    if (!forId || !t || c < 0 || c > t) {
      setErr("Savollar va to'g'ri javoblar sonini to'g'ri kiriting");
      return;
    }
    setErr("");
    try {
      const r = await api.post<{ leveled_up: boolean }>(
        `/students/${forId}/exercises`,
        { total: t, correct: c, topic: topic || null }
      );
      if (r.leveled_up)
        alert("Tabriklaymiz — o'quvchi YANGI DARAJAGA ko'tarildi!");
      setForId(null); setTotal(""); setCorrect(""); setTopic("");
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (loading)
    return <p className="text-sm text-slate-400 py-6">Yuklanmoqda...</p>;

  return (
    <div>
      <p className="text-xs text-slate-500 mb-3">
        Har bir to'g'ri javob — 1 ball. Har 500 ball — yangi daraja:
        Beginner → Elementary → Pre-Int → Intermediate → Upper-Int →
        Advanced → Native (IELTS/CEFR mo'ljali bilan).
      </p>
      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-left px-3 py-2">O'quvchi</th>
              <th className="text-right px-3 py-2">Mashqlar</th>
              <th className="text-right px-3 py-2">To'g'ri %</th>
              <th className="text-left px-3 py-2">Daraja</th>
              <th className="text-left px-3 py-2 w-64">Keyingi darajaga</th>
              {canEdit && <th className="w-24" />}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.student_id} className="border-t border-slate-100">
                <td className="px-3 py-2.5 text-slate-800">{r.full_name}</td>
                <td className="px-3 py-2.5 text-right text-slate-600">
                  {r.done || "—"}
                </td>
                <td className={`px-3 py-2.5 text-right font-medium ${
                  r.percent >= 80 ? "text-emerald-600"
                    : r.percent >= 60 ? "text-amber-600"
                    : r.done ? "text-red-500" : "text-slate-400"
                }`}>
                  {r.done ? `${r.percent}%` : "—"}
                </td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex flex-col">
                    <span className="text-slate-800 font-medium">
                      {r.level.label}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      IELTS {r.level.ielts} · CEFR {r.level.cefr}
                    </span>
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  {r.next ? (
                    <div>
                      <div className="flex justify-between text-[11px] text-slate-500 mb-0.5">
                        <span>{r.next.label}</span>
                        <span>
                          {r.next.progress_percent}% ·{" "}
                          {r.next.points_left} ball qoldi
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-2 rounded-full bg-brand-500"
                          style={{ width: `${r.next.progress_percent}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <span className="text-xs text-emerald-600">
                      Eng yuqori daraja!
                    </span>
                  )}
                </td>
                {canEdit && (
                  <td className="px-2 py-2.5 text-right">
                    <button
                      onClick={() => { setForId(r.student_id); setErr(""); }}
                      className="text-xs px-2 py-1 rounded-md bg-brand-50 text-brand-700 hover:bg-brand-100"
                    >
                      + Natija
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {forId !== null && (
        <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-xs p-5 shadow-xl">
            <h3 className="font-semibold text-slate-900 mb-1">
              Mashq natijasi
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              {rows.find((x) => x.student_id === forId)?.full_name}
            </p>
            <div className="space-y-2">
              <input type="number" value={total}
                onChange={(e) => setTotal(e.target.value)}
                placeholder="Jami savollar soni" autoFocus
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              <input type="number" value={correct}
                onChange={(e) => setCorrect(e.target.value)}
                placeholder="To'g'ri javoblar soni"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              <input value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Mavzu (ixtiyoriy)"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
            {err && <p className="text-xs text-red-600 mt-2">{err}</p>}
            <div className="flex gap-2 mt-4">
              <button onClick={save}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium">
                Saqlash
              </button>
              <button onClick={() => setForId(null)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600">
                Bekor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

