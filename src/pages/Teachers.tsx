import { useEffect, useState } from "react";
import { TeacherOverviewModal, SupportGroupsModal } from "../components/TeacherOverview";
import {
  Plus, X, UserMinus, UserCheck, Pencil, KeyRound, Copy, Check,
  FileUp,
 Layers } from "lucide-react";
import {
  api, type Teacher, type Branch, type GradeRow, type CareerMap,
  type TeacherAccount,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  STAFF_VIEWERS, SALARY_SELF_VIEW, TEACHER, SUPPORT_TEACHER,
  ACCOUNT_MANAGE, can, FOUNDER, ACADEMIC_HEAD,
 SUPPORT_ASSIGN } from "../lib/roles";
import { formatDate } from "../lib/format";
import { SUBJECTS, subjectLabel } from "../lib/subjects";
import { SalaryCard } from "../components/SalaryCard";
import { TeacherScoreboard } from "../components/TeacherScoreboard";
import { CareerCard } from "../components/Career";

type TeachTab = "list" | "score" | "salary";

function TeacherModal({
  branches,
  defaultBranchId,
  initial,
  onClose,
  onSaved,
}: {
  branches: Branch[];
  defaultBranchId: number | null;
  initial?: Teacher;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editing = !!initial;
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [phone, setPhone] = useState(initial?.phone ?? "");
  const [subject, setSubject] = useState(initial?.subject ?? "");
  // Ustoz 2-3 filialda ishlashi mumkin — bir nechtasini belgilash mumkin.
  // Birinchi belgilangani "asosiy" hisoblanadi.
  const [branchIds, setBranchIds] = useState<number[]>(
    initial?.branch_ids?.length
      ? initial.branch_ids
      : initial?.branch_id
      ? [initial.branch_id]
      : defaultBranchId
      ? [defaultBranchId]
      : []
  );
  const [hiredDate, setHiredDate] = useState(
    initial?.hired_date ?? new Date().toISOString().slice(0, 10)
  );
  // Daraja va uning shartlari. Stavka shu darajadan chiqadi, shuning
  // uchun sertifikat va mahorat balli bo'sh qolsa ustoz ko'tarilmay
  // qolib ketadi.
  const [grade, setGrade] = useState(initial?.grade ?? "");
  const [cert, setCert] = useState(initial?.cert ?? "");
  const [certScore, setCertScore] = useState(
    initial?.cert_score != null ? String(initial.cert_score) : ""
  );
  const [qualification, setQualification] = useState(
    initial?.qualification ?? ""
  );
  const [birthDate, setBirthDate] = useState(initial?.birth_date ?? "");
  const [skillScore, setSkillScore] = useState(
    initial?.skill_score != null ? String(initial.skill_score) : ""
  );
  const [supportMonths, setSupportMonths] = useState(
    initial?.support_months != null ? String(initial.support_months) : ""
  );
  const [grades, setGrades] = useState<GradeRow[]>([]);
  useEffect(() => {
    api
      .get<CareerMap>("/career")
      .then((d) => setGrades(d.grades))
      .catch(() => setGrades([]));
  }, []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!fullName.trim()) {
      setError("Ism-familiyani kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body = {
        full_name: fullName,
        phone: phone || null,
        subject: subject || null,
        branch_id: branchIds[0] ?? null,
        branch_ids: branchIds,
        hired_date: hiredDate || null,
        is_active: initial ? initial.is_active ?? 1 : 1,
        grade: grade || null,
        cert: cert || null,
        cert_score: certScore === "" ? null : Number(certScore),
        qualification: qualification || null,
        birth_date: birthDate || null,
        skill_score: skillScore === "" ? null : Number(skillScore),
        support_months: supportMonths === "" ? null : Number(supportMonths),
      };
      if (editing) await api.put(`/teachers/${initial!.id}`, body);
      else await api.post("/teachers", body);
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {editing ? "O'qituvchini tahrirlash" : "Yangi o'qituvchi"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">F.I.Sh. *</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Telefon</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Fan</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {SUBJECTS.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
              {subject && !SUBJECTS.some((s) => s.key === subject) && (
                <option value={subject}>{subject}</option>
              )}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Daraja
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
            >
              <option value="">— birinchi daraja —</option>
              {grades.map((g) => (
                <option key={g.key} value={g.key}>
                  {g.label} · {g.rate_per_student.toLocaleString("ru-RU")} so'm
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-400 mt-1">
              Bir o'quvchidan qancha olishi va nechta guruh olib borishi
              shundan chiqadi.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Sertifikat
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={cert}
                onChange={(e) => setCert(e.target.value)}
                placeholder="IELTS 6.5"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Ball
              </label>
              <input
                type="number"
                step="0.5"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={certScore}
                onChange={(e) => setCertScore(e.target.value)}
                placeholder="6.5"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Mahorat balli
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={skillScore}
                onChange={(e) => setSkillScore(e.target.value)}
                placeholder="50"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Support tajribasi (oy)
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={supportMonths}
                onChange={(e) => setSupportMonths(e.target.value)}
                placeholder="3"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Tug'ilgan sana
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Metodika sertifikati
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={qualification}
                onChange={(e) => setQualification(e.target.value)}
              >
                <option value="">— yo'q —</option>
                <option value="CELTA">CELTA</option>
                <option value="TESOL">TESOL</option>
                <option value="DELTA">DELTA</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Filiallar (bir nechtasini belgilash mumkin)
            </label>
            <div className="flex flex-wrap gap-1.5">
              {branches.map((b) => {
                const on = branchIds.includes(b.id);
                return (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() =>
                      setBranchIds((prev) =>
                        on ? prev.filter((x) => x !== b.id) : [...prev, b.id]
                      )
                    }
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
                      on
                        ? "bg-brand-50 border-brand-400 text-brand-700"
                        : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                    }`}
                  >
                    {b.name}
                    {on && branchIds[0] === b.id && branchIds.length > 1 && (
                      <span className="ml-1 opacity-60">(asosiy)</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Ishga kirgan sana
            </label>
            <input
              type="date"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={hiredDate}
              onChange={(e) => setHiredDate(e.target.value)}
            />
            <p className="text-xs text-slate-400 mt-1">
              Retention hisoboti shu sanadan boshlab stajni sanaydi.
            </p>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={submit}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-2 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Teachers() {
  const { user } = useAuth();
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [editing, setEditing] = useState<Teacher | null>(null);
  const [accountFor, setAccountFor] = useState<Teacher | null>(null);
  const [overviewFor, setOverviewFor] = useState<Teacher | null>(null);
  const [supportFor, setSupportFor] = useState<Teacher | null>(null);
  const [salary, setSalary] = useState<number | null>(null);
  const [career, setCareer] = useState<number | null>(null);
  // Daraja nomlarini bir marta olamiz - har bir qatorda so'ramaslik uchun
  const [gradeLabels, setGradeLabels] = useState<Record<string, string>>({});
  useEffect(() => {
    api
      .get<CareerMap>("/career")
      .then((d) =>
        setGradeLabels(
          Object.fromEntries(d.grades.map((g) => [g.key, g.label]))
        )
      )
      .catch(() => setGradeLabels({}));
  }, []);
  const [tab, setTab] = useState<TeachTab>(
    user?.role === TEACHER || user?.role === SUPPORT_TEACHER
      ? "salary"
      : "list"
  );

  function load() {
    setLoading(true);
    Promise.all([api.get<Teacher[]>("/teachers"), api.get<Branch[]>("/branches")])
      .then(([t, b]) => {
        setTeachers(t);
        setBranches(b);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);
  const canEdit = can(user?.role, STAFF_VIEWERS);
  const canAccount = can(user?.role, ACCOUNT_MANAGE);
  // Ustozning o'zi hamkasbining oyligini ochmaydi
  const canSeeSalary =
    can(user?.role, SALARY_SELF_VIEW) && !can(user?.role, [TEACHER, SUPPORT_TEACHER]);
  const activeCount = teachers.filter((t) => t.is_active !== 0).length;

  /** Ishdan ketgan deb belgilash - o'chirish o'rniga. Shunda ustozning
   * tarixi (ish haqi, staj) saqlanadi va retention hisoboti to'g'ri chiqadi. */
  async function toggleActive(t: Teacher) {
    const leaving = t.is_active !== 0;
    if (
      leaving &&
      !confirm(
        `${t.full_name} ishdan ketgan deb belgilansinmi? Ketgan sana bugungi kun bilan qo'yiladi.`
      )
    )
      return;
    try {
      await api.put(`/teachers/${t.id}`, {
        full_name: t.full_name,
        phone: t.phone ?? null,
        subject: t.subject ?? null,
        branch_id: t.branch_id ?? null,
        hired_date: t.hired_date ?? null,
        is_active: leaving ? 0 : 1,
      });
      load();
    } catch {
      /* xatolik bo'lsa ro'yxat o'zgarmaydi */
    }
  }

  const isTeacher =
    user?.role === TEACHER || user?.role === SUPPORT_TEACHER;

  return (
    <div className="p-8">
      <div className="flex items-center gap-1 mb-5">
        {[
          ...(isTeacher ? [{ k: "salary", l: "Mening oyligim" }] : []),
          { k: "list", l: "Ro'yxat" },
          { k: "score", l: "Natijalar" },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setTab(t.k as TeachTab)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === t.k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {t.l}
          </button>
        ))}
      </div>

      {tab === "salary" && (
        <div className="max-w-4xl">
          <h1 className="text-xl font-semibold text-slate-900 mb-1">
            Mening oyligim
          </h1>
          <p className="text-sm text-slate-500 mb-5">
            Yoqlama qo'yilishi bilan o'zi hisoblanadi
          </p>
          <SalaryCard self />
        </div>
      )}

      {tab === "score" && <TeacherScoreboard />}

      {tab === "list" && (
      <>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">O'qituvchilar</h1>
          <p className="text-sm text-slate-500">
            Ishlayapti: {activeCount}
            {teachers.length > activeCount &&
              ` · ketgan: ${teachers.length - activeCount}`}
          </p>
        </div>
        {canEdit && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowImport(true)}
              className="flex items-center gap-2 bg-white border border-slate-200 hover:border-brand-300 text-slate-600 rounded-lg px-4 py-2 text-sm font-medium"
            >
              <FileUp size={15} /> Excel'dan import
            </button>
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
            >
              <Plus size={16} /> Yangi o'qituvchi
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">F.I.Sh.</th>
                <th className="text-left px-4 py-3 font-medium">Telefon</th>
                <th className="text-left px-4 py-3 font-medium">Fan</th>
                <th className="text-left px-4 py-3 font-medium">Daraja</th>
                <th className="text-left px-4 py-3 font-medium">Filial</th>
                <th className="text-left px-4 py-3 font-medium">Ishga kirgan</th>
                {canEdit && <th className="px-4 py-3"></th>}
              </tr>
            </thead>
            <tbody>
              {teachers.map((t) => {
                const left = t.is_active === 0;
                return (
                  <tr
                    key={t.id}
                    className={`border-t border-slate-100 ${left ? "bg-slate-50/60" : ""}`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {user?.role === FOUNDER || user?.role === ACADEMIC_HEAD ? (
                        <button
                          onClick={() => setOverviewFor(t)}
                          className="hover:text-brand-700"
                          title="Umumiy ko'rinish"
                        >
                          {t.full_name}
                        </button>
                      ) : canSeeSalary ? (
                        <button
                          onClick={() => setSalary(t.id)}
                          className="hover:text-brand-700"
                          title="Ish haqi kartasi"
                        >
                          {t.full_name}
                        </button>
                      ) : (
                        t.full_name
                      )}
                      {left && (
                        <span className="ml-2 text-[10px] uppercase tracking-wide bg-slate-200 text-slate-500 px-1.5 py-0.5 rounded">
                          ketgan {t.left_date ? formatDate(t.left_date) : ""}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{t.phone || "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{subjectLabel(t.subject) || "—"}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setCareer(t.id)}
                        className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 hover:bg-brand-50 hover:text-brand-700"
                        title="Karyera kartasi"
                      >
                        {gradeLabels[t.grade || ""] || "—"}
                      </button>
                      {t.remediation_until && (
                        <span
                          className="ml-1.5 text-xs text-red-600"
                          title={t.remediation_reason || ""}
                        >
                          qayta tayyorlash
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{t.branches_label || t.branch?.name || "—"}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {t.hired_date ? formatDate(t.hired_date) : "—"}
                    </td>
                    {canEdit && (
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => setEditing(t)}
                          title="Tahrirlash"
                          className="text-slate-400 hover:text-brand-600 mr-2"
                        >
                          <Pencil size={15} />
                        </button>
                        {canAccount && !left && (
                          <button
                            onClick={() => setAccountFor(t)}
                            title={
                              t.login
                                ? `Login: ${t.login} — yangi parol berish`
                                : "Akkaunt ochish (login va parol)"
                            }
                            className={`mr-2 ${
                              t.login
                                ? "text-emerald-500 hover:text-emerald-600"
                                : "text-slate-400 hover:text-brand-600"
                            }`}
                          >
                            <KeyRound size={15} />
                          </button>
                        )}
                        {can(user?.role, SUPPORT_ASSIGN) && (
                          <button
                            onClick={() => setSupportFor(t)}
                            title="Support guruhlari (biriktirish)"
                            className="mr-2 text-slate-400 hover:text-brand-600"
                          >
                            <Layers size={15} />
                          </button>
                        )}
                        <button
                          onClick={() => toggleActive(t)}
                          title={left ? "Ishga qaytarish" : "Ishdan ketgan deb belgilash"}
                          className="text-slate-400 hover:text-brand-600"
                        >
                          {left ? <UserCheck size={16} /> : <UserMinus size={16} />}
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      </>
      )}

      {showImport && (
        <ImportTeachersModal
          branches={branches}
          onClose={() => setShowImport(false)}
          onDone={() => {
            setShowImport(false);
            load();
          }}
        />
      )}
      {showAdd && (
        <TeacherModal
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <TeacherModal
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
      {salary !== null && (
        <SalaryCard teacherId={salary} onClose={() => setSalary(null)} />
      )}
      {career !== null && (
        <CareerCard
          teacherId={career}
          onClose={() => {
            setCareer(null);
            load();
          }}
        />
      )}
      {supportFor && (
        <SupportGroupsModal
          teacherId={supportFor.id}
          name={supportFor.full_name}
          onClose={() => setSupportFor(null)}
        />
      )}
      {overviewFor && (
        <TeacherOverviewModal
          teacherId={overviewFor.id}
          onClose={() => setOverviewFor(null)}
        />
      )}
      {accountFor && (
        <AccountModal
          teacher={accountFor}
          onClose={() => {
            setAccountFor(null);
            load();
          }}
        />
      )}
    </div>
  );
}

/** Ustozga akkaunt ochish. Login ismdan yasaladi, parol tasodifiy —
 *  ikkalasini ham tizim o'zi beradi. Parol FAQAT shu oynada
 *  ko'rinadi: bazada shifrlangan holda saqlanadi, keyin uni hech kim
 *  qayta ocha olmaydi. */
function AccountModal({
  teacher,
  onClose,
}: {
  teacher: Teacher;
  onClose: () => void;
}) {
  const [data, setData] = useState<TeacherAccount | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const hasAccount = !!teacher.login;

  async function run(reset: boolean) {
    setBusy(true);
    setError(null);
    try {
      const path = reset
        ? `/teachers/${teacher.id}/account/reset`
        : `/teachers/${teacher.id}/account`;
      setData(await api.post<TeacherAccount>(path, {}));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  function copyAll() {
    if (!data) return;
    navigator.clipboard?.writeText(
      `${data.full_name}\nManzil: ${data.url}\n` +
        `Login: ${data.login}\nParol: ${data.password}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {teacher.full_name}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        {!data && (
          <>
            {hasAccount ? (
              <>
                <div className="bg-slate-50 rounded-lg p-3 mb-3">
                  <p className="text-xs text-slate-500 mb-0.5">Login</p>
                  <p className="font-mono text-sm text-slate-900">
                    {teacher.login}
                  </p>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Bu ustozda akkaunt bor. Parol shifrlangan — uni ko'rish
                  imkoni yo'q. Ustoz parolni unutgan bo'lsa, yangisini
                  yasang: eskisi darhol ishlamay qoladi.
                </p>
                <button
                  onClick={() => run(true)}
                  disabled={busy}
                  className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
                >
                  {busy ? "..." : "Yangi parol yasash"}
                </button>
              </>
            ) : (
              <>
                <p className="text-sm text-slate-600 mb-4">
                  Login ismdan yasaladi, parol tasodifiy tanlanadi.
                  Ikkalasi ham shu yerda bir marta ko'rsatiladi.
                </p>
                <button
                  onClick={() => run(false)}
                  disabled={busy}
                  className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
                >
                  {busy ? "..." : "Akkaunt ochish"}
                </button>
              </>
            )}
            {error && (
              <p className="text-sm text-red-600 mt-3">{error}</p>
            )}
          </>
        )}

        {data && (
          <>
            <div className="space-y-2 mb-4">
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-0.5">Manzil</p>
                <p className="text-sm text-slate-900">{data.url}</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-0.5">Login</p>
                <p className="font-mono text-base text-slate-900">
                  {data.login}
                </p>
              </div>
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                <p className="text-xs text-emerald-700 mb-0.5">Parol</p>
                <p className="font-mono text-base text-slate-900 tracking-wide">
                  {data.password}
                </p>
              </div>
            </div>

            <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
              {data.warning}
            </p>

            <button
              onClick={copyAll}
              className="w-full border border-slate-300 rounded-lg py-2 text-sm font-medium text-slate-700 mb-2 flex items-center justify-center gap-2"
            >
              {copied ? <Check size={15} /> : <Copy size={15} />}
              {copied ? "Nusxalandi" : "Hammasini nusxalash"}
            </button>
            <button
              onClick={onClose}
              className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium"
            >
              Yozib oldim, yopish
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* ==================== EXCEL'DAN IMPORT ==================== */
/** Eski platformadan (LC UP va o'xshash) eksport qilingan .xlsx
 *  faylni o'qib, ustozlarni bir bosishda qo'shadi. Ustunlar nomidan
 *  o'zi topiladi: Name/Ism, Mobile/Phone/Telefon, Birth, Groups.
 *  Dublikatlar (bir xil ism yoki telefon) o'zi o'tkazib yuboriladi. */
type ImpRow = {
  full_name: string; phone: string; birth_date: string; note: string;
};

function ImportTeachersModal({
  branches, onClose, onDone,
}: {
  branches: Branch[]; onClose: () => void; onDone: () => void;
}) {
  const [rows, setRows] = useState<ImpRow[]>([]);
  const [branchId, setBranchId] = useState("");
  const [fileName, setFileName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState<{
    created: number;
    results: { name: string; status: string; reason?: string }[];
  } | null>(null);

  async function readFile(f: File) {
    setErr("");
    setResult(null);
    try {
      const XLSX = await import("xlsx");
      const wb = XLSX.read(await f.arrayBuffer());
      const ws = wb.Sheets[wb.SheetNames[0]];
      const raw: unknown[][] = XLSX.utils.sheet_to_json(ws, {
        header: 1, raw: false,
      });
      if (raw.length < 2) throw new Error("Faylda ma'lumot topilmadi");
      const head = (raw[0] as unknown[]).map((h) =>
        String(h || "").toLowerCase());
      const col = (...keys: string[]) =>
        head.findIndex((h) => keys.some((k) => h.includes(k)));
      const iName = col("name", "ism", "f.i");
      const iPhone = col("mobile", "phone", "telefon", "raqam");
      const iBirth = col("birth", "tug'ilgan", "tugilgan");
      const iGroups = col("group", "guruh");
      if (iName < 0)
        throw new Error("Ism ustuni topilmadi (Name/Ism bo'lishi kerak)");
      const out: ImpRow[] = [];
      for (const r of raw.slice(1)) {
        const name = String(r[iName] ?? "").trim();
        if (!name) continue;
        out.push({
          full_name: name,
          phone: iPhone >= 0 ? String(r[iPhone] ?? "").trim() : "",
          birth_date: iBirth >= 0
            ? String(r[iBirth] ?? "").trim().slice(0, 10) : "",
          note: iGroups >= 0 ? String(r[iGroups] ?? "").trim() : "",
        });
      }
      if (out.length === 0) throw new Error("Bironta ham qator o'qilmadi");
      setRows(out);
      setFileName(f.name);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Faylni o'qib bo'lmadi");
    }
  }

  async function doImport() {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<{
        created: number;
        results: { name: string; status: string; reason?: string }[];
      }>("/teachers/import", {
        rows,
        branch_id: branchId ? Number(branchId) : null,
      });
      setResult(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Import bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            Ustozlarni Excel'dan import qilish
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {result ? (
          <div>
            <p className="text-sm font-medium text-emerald-700 mb-3">
              ✓ {result.created} ta ustoz qo'shildi
            </p>
            <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 mb-4 max-h-72 overflow-auto">
              {result.results.map((r, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2 text-sm">
                  <span>{r.status === "ok" ? "✅" : "⏭️"}</span>
                  <span className="text-slate-800">{r.name}</span>
                  {r.reason && (
                    <span className="text-xs text-slate-400">— {r.reason}</span>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={onDone}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium"
            >
              Tayyor
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <input
                type="file"
                accept=".xlsx,.xls,.csv"
                id="imp-file"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) readFile(f);
                }}
              />
              <label
                htmlFor="imp-file"
                className="flex items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl py-6 text-sm text-slate-500 cursor-pointer hover:border-brand-400"
              >
                <FileUp size={16} />
                {fileName || "Excel faylni tanlang (.xlsx)"}
              </label>
            </div>

            {rows.length > 0 && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">
                    Qaysi filialga qo'shilsin
                  </label>
                  <select
                    value={branchId}
                    onChange={(e) => setBranchId(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="">— filialsiz —</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <div className="border border-slate-200 rounded-lg max-h-64 overflow-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50 text-slate-500 sticky top-0">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium">F.I.Sh.</th>
                        <th className="text-left px-3 py-2 font-medium">Telefon</th>
                        <th className="text-left px-3 py-2 font-medium">Tug'ilgan</th>
                        <th className="text-left px-3 py-2 font-medium">Guruhlari (ma'lumot)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {rows.map((r, i) => (
                        <tr key={i}>
                          <td className="px-3 py-1.5 text-slate-800">{r.full_name}</td>
                          <td className="px-3 py-1.5 text-slate-600">{r.phone}</td>
                          <td className="px-3 py-1.5 text-slate-500">{r.birth_date}</td>
                          <td className="px-3 py-1.5 text-slate-400 max-w-[16rem] truncate">
                            {r.note}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-slate-400">
                  {rows.length} ta qator o'qildi. Bir xil ism yoki telefon
                  allaqachon bo'lsa, o'sha qator o'tkazib yuboriladi —
                  ikki marta bosishdan qo'rqmang. Guruhlari ustuni faqat
                  ma'lumot uchun: guruhlar keyin alohida biriktiriladi.
                </p>
              </>
            )}

            {err && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{err}</p>
            )}

            <button
              onClick={doImport}
              disabled={busy || rows.length === 0}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-50"
            >
              {busy ? "Qo'shilmoqda..." : `${rows.length} ta ustozni qo'shish`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
