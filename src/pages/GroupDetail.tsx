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
import { TEACHING_STAFF, FINANCE_ACCESS, can } from "../lib/roles";
import { exportToExcel } from "../lib/exportXlsx";
import { QuickXp } from "../components/XpAdmin";
import { AttendanceTab, GradesTab, ExamsTab } from "../components/GroupGrids";
import { GroupHomeworkTab, GroupHistoryTab, GroupNotesTab } from "../components/GroupExtras";
import { GroupSidebar } from "../components/GroupSidebar";
import { GroupFormModal } from "./Groups";

type GroupTab = "attendance" | "grades" | "exams" | "xp" | "homework" | "history" | "notes";

const GROUP_TABS: { key: GroupTab; label: string }[] = [
  { key: "attendance", label: "Davomat" },
  { key: "homework", label: "Uyga vazifalar" },
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
  const [branches, setBranches] = useState<Branch[]>([]);
  const t = today();

  const [group, setGroup] = useState<Group | null>(null);
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

  const canMarkLesson = can(user?.role, TEACHING_STAFF);
  const canFinance = can(user?.role, FINANCE_ACCESS);

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
    api.get<Group>(`/groups/${groupId}`).then((g) => {
      setGroup(g);
      setLessonTeacherId((prev) => prev || (g.teacher_id ? String(g.teacher_id) : ""));
    });
    api.get<Teacher[]>("/teachers").then(setTeachers);
  }

  function loadLessons(y: number, m: number) {
    setLessonsLoading(true);
    api
      .get<Lesson[]>(`/groups/${groupId}/lessons?year=${y}&month=${m}`)
      .then(setLessons)
      .finally(() => setLessonsLoading(false));
  }

  function loadPersistedPayouts(y: number, m: number) {
    if (!canFinance) return;
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
          onEdit={canFinance ? () => setEditOpen(true) : undefined}
        />

        <div className="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex gap-1 mb-5 border-b border-slate-200 overflow-x-auto">
            {GROUP_TABS.map((tb) => (
              <button
                key={tb.key}
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
          canEdit={canMarkLesson}
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
        <ExamsTab
          groupId={group.id}
          canEdit={canMarkLesson}
          canDelete={canFinance}
        />
      )}

      {tab === "homework" && <GroupHomeworkTab groupId={groupId} />}
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
    </div>
  );
}
