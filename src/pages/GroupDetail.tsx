import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Plus, Trash2, Download } from "lucide-react";
import {
  api,
  type Group,
  type Teacher,
  type Lesson,
  type BillingRunResult,
  type PayrollRunResult,
  type TeacherPayout,
  type Branch,
} from "../lib/api";
import { formatSom } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, FINANCE_ACCESS, can } from "../lib/roles";
import { exportToExcel } from "../lib/exportXlsx";
import { AttendanceTab, GradesTab, ExamsTab } from "../components/GroupGrids";
import { GroupSidebar } from "../components/GroupSidebar";
import { GroupFormModal } from "./Groups";

type GroupTab = "lessons" | "attendance" | "grades" | "exams";

const GROUP_TABS: { key: GroupTab; label: string }[] = [
  { key: "attendance", label: "Davomat" },
  { key: "grades", label: "Baholash" },
  { key: "lessons", label: "Darslar" },
  { key: "exams", label: "Imtihonlar" },
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

      {tab === "lessons" && (
      <>
      {/* ---------------- Lesson log ("yoqlama") ---------------- */}
      <section className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
        <h2 className="font-semibold text-slate-900 mb-3">
          Darslar (yoqlama) — {lessons.length} ta o'tilgan
        </h2>

        {canMarkLesson && (
          <div className="flex flex-wrap items-end gap-2 mb-4 bg-slate-50 rounded-lg p-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Sana</label>
              <input
                type="date"
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
                value={lessonDate}
                onChange={(e) => setLessonDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Kim o'tdi
              </label>
              <select
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm bg-white"
                value={lessonTeacherId}
                onChange={(e) => setLessonTeacherId(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {teachers.map((tt) => (
                  <option key={tt.id} value={tt.id}>
                    {tt.full_name}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={addLesson}
              disabled={addingLesson}
              className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-60"
            >
              <Plus size={14} /> Dars belgilash
            </button>
            {lessonError && <p className="text-sm text-red-600 w-full">{lessonError}</p>}
          </div>
        )}

        {lessonsLoading ? (
          <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
        ) : lessons.length === 0 ? (
          <p className="text-slate-400 text-sm">Bu oy uchun dars belgilanmagan.</p>
        ) : (
          <div className="space-y-1">
            {lessons.map((l) => (
              <div
                key={l.id}
                className="flex items-center justify-between text-sm border-b border-slate-50 py-1.5 last:border-0"
              >
                <span className="text-slate-700">{l.date}</span>
                <span className="text-slate-500">{l.teacher?.full_name || teacherName(l.teacher_id)}</span>
                {canMarkLesson && (
                  <button
                    onClick={() => deleteLesson(l.id)}
                    className="text-slate-300 hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {canFinance && (
        <>
          {/* ---------------- Billing ---------------- */}
          <section className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-slate-900">Talabalar uchun hisob-kitob</h2>
              <div className="flex items-center gap-2">
                {billingResult && (
                  <button
                    onClick={exportBilling}
                    className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700"
                    title="Excel'ga eksport"
                  >
                    <Download size={14} /> Excel
                  </button>
                )}
                <button
                  onClick={() => runBilling(false)}
                  disabled={billingLoading}
                  className="text-sm font-medium text-brand-700 hover:underline disabled:opacity-60"
                >
                  Ko'rish
                </button>
                <button
                  onClick={() => runBilling(true)}
                  disabled={billingLoading}
                  className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-60"
                >
                  Hisoblash va tasdiqlash
                </button>
              </div>
            </div>

            {billingResult ? (
              <div>
                <p className="text-xs text-slate-400 mb-2">
                  {billingResult.period} · {billingResult.held_lessons} dars o'tilgan
                  {billingResult.committed ? " · balansga yozildi" : " · faqat ko'rish (hali saqlanmagan)"}
                </p>
                <table className="w-full text-sm">
                  <thead className="text-slate-400 text-xs uppercase">
                    <tr>
                      <th className="text-left py-1">Talaba</th>
                      <th className="text-right py-1">Darslar</th>
                      <th className="text-right py-1">Summa</th>
                      <th className="text-right py-1">Holat</th>
                    </tr>
                  </thead>
                  <tbody>
                    {billingResult.results.map((r) => (
                      <tr key={r.student_id} className="border-t border-slate-50">
                        <td className="py-1.5">{r.student_name}</td>
                        <td className="py-1.5 text-right">{r.billable_lessons}</td>
                        <td className="py-1.5 text-right font-medium">{formatSom(r.amount)}</td>
                        <td className="py-1.5 text-right text-xs">
                          {r.created ? (
                            <span className="text-green-600">yozildi</span>
                          ) : r.already_charged ? (
                            <span className="text-slate-400">allaqachon hisoblangan</span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-slate-400 text-sm">
                Hisoblash uchun "Ko'rish" tugmasini bosing.
              </p>
            )}
          </section>

          {/* ---------------- Payroll ---------------- */}
          <section className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-slate-900">Ustozlar ish haqi</h2>
              <div className="flex items-center gap-2">
                {(payrollResult || persistedPayouts.length > 0) && (
                  <button
                    onClick={exportPayroll}
                    className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700"
                    title="Excel'ga eksport"
                  >
                    <Download size={14} /> Excel
                  </button>
                )}
                <button
                  onClick={() => runPayroll(false)}
                  disabled={payrollLoading}
                  className="text-sm font-medium text-brand-700 hover:underline disabled:opacity-60"
                >
                  Ko'rish
                </button>
                <button
                  onClick={() => runPayroll(true)}
                  disabled={payrollLoading}
                  className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-60"
                >
                  Hisoblash va saqlash
                </button>
              </div>
            </div>

            {payrollResult && (
              <table className="w-full text-sm mb-4">
                <thead className="text-slate-400 text-xs uppercase">
                  <tr>
                    <th className="text-left py-1">O'qituvchi</th>
                    <th className="text-right py-1">O'tgan / jami dars</th>
                    <th className="text-right py-1">Talaba</th>
                    <th className="text-right py-1">Summa</th>
                  </tr>
                </thead>
                <tbody>
                  {payrollResult.results.map((r) => (
                    <tr key={r.teacher_id} className="border-t border-slate-50">
                      <td className="py-1.5">{r.teacher?.full_name || teacherName(r.teacher_id)}</td>
                      <td className="py-1.5 text-right">
                        {r.taught_lessons} / {r.held_lessons}
                      </td>
                      <td className="py-1.5 text-right">{r.student_count}</td>
                      <td className="py-1.5 text-right font-medium">{formatSom(r.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
              Saqlangan yozuvlar
            </p>
            {persistedPayouts.length === 0 ? (
              <p className="text-slate-400 text-sm">
                Bu oy uchun hali hisoblanib saqlanmagan.
              </p>
            ) : (
              <div className="space-y-1">
                {persistedPayouts.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between text-sm border-t border-slate-50 py-1.5"
                  >
                    <span>{p.teacher?.full_name || teacherName(p.teacher_id)}</span>
                    <span className="text-slate-500">{formatSom(p.amount)}</span>
                    <button
                      onClick={() => togglePaid(p)}
                      className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                        p.paid
                          ? "bg-green-50 text-green-700 hover:bg-green-100"
                          : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                      }`}
                    >
                      {p.paid ? "To'landi" : "To'lanmagan"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
      </>
      )}
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
