import { useEffect, useState } from "react";
import { formatPhone } from "../components/PhoneInput";
import { TeacherOverviewModal, SupportGroupsModal, TeacherGroupsModal } from "../components/TeacherOverview";
import {
  Plus, X, UserMinus, UserCheck, Pencil, KeyRound, Copy, Check,
  FileUp,
 Layers } from "lucide-react";
import {
  api, getGlobalBranch, type Teacher, type Branch, type GradeRow,
  type CareerMap,
  type TeacherAccount,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  STAFF_VIEWERS, SALARY_SELF_VIEW, TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
  ACCOUNT_MANAGE, can, FOUNDER, ACADEMIC_HEAD,
 SUPPORT_ASSIGN } from "../lib/roles";
import { formatDate, formatSom } from "../lib/format";
import { SUBJECTS, subjectLabel } from "../lib/subjects";
import { SalaryCard } from "../components/SalaryCard";
import { TeacherScoreboard } from "../components/TeacherScoreboard";
import { CareerCard } from "../components/Career";

type TeachTab = "list" | "support" | "score" | "salary";

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
  // SUPPORT teacher uchun daraja boshqa zina: Volontyor -> Junior ->
  // Middle -> Senior (ustoz darajasi EMAS). Jahongir: "Supportni
  // teacherni tahrirlasa darajasini o'zgartirishda o'qituvchi bo'lim
  // tahrirlanyabdi" - endi support o'z darajasi bilan tahrirlanadi.
  const isSupport = initial?.kind === "support";
  const [sGrade, setSGrade] = useState(initial?.staff_grade ?? "volunteer");
  const [sGrades, setSGrades] = useState<
    { key: string; label: string; coef: number }[]
  >([]);
  useEffect(() => {
    if (isSupport) {
      api
        .get<{ grades: { key: string; label: string; coef: number }[] }>(
          "/staff-grades"
        )
        .then((d) => setSGrades(d.grades))
        .catch(() =>
          setSGrades([
            { key: "volunteer", label: "Volontyor", coef: 0 },
            { key: "junior", label: "Junior", coef: 1 },
            { key: "middle", label: "Middle", coef: 1.15 },
            { key: "senior", label: "Senior", coef: 1.3 },
          ])
        );
      return;
    }
    api
      .get<CareerMap>("/career")
      .then((d) => setGrades(d.grades))
      .catch(() => setGrades([]));
  }, [isSupport]);
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
      if (isSupport) body.grade = null; // ustoz darajasi supportga tegishli emas
      if (editing) await api.put(`/teachers/${initial!.id}`, body);
      else await api.post("/teachers", body);
      if (
        isSupport &&
        initial?.user_id &&
        sGrade !== (initial.staff_grade ?? "volunteer")
      ) {
        await api.put(`/staff-grades/${initial.user_id}`, { grade: sGrade });
      }
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[92vh] overflow-y-auto">
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
          {isSupport ? (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Support darajasi
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={sGrade}
                onChange={(e) => setSGrade(e.target.value)}
                disabled={!initial?.user_id}
              >
                {sGrades.map((g) => (
                  <option key={g.key} value={g.key}>
                    {g.label}
                    {g.coef === 0
                      ? " · oylik yo'q"
                      : ` · koef ${g.coef}`}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-400 mt-1">
                {initial?.user_id
                  ? "Volontyorga oylik berilmaydi; qolganlarida seans " +
                    "oyligi koeffitsiyentga ko'paytiriladi."
                  : "Daraja qo'yish uchun avval akkaunt oching (kalit belgisi)."}
              </p>
            </div>
          ) : (
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
          )}

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
  // Guruhlari oynasi (2026-08-21) — oyliksiz versiya, barcha xodimga
  const [groupsFor, setGroupsFor] = useState<Teacher | null>(null);
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
  // Support boshlig'i O'Z JAMOASINI (support teacherlar) to'liq
  // tahrirlaydi - qator darajasida tekshiriladi (Jahongir)
  const isHeadSupport = user?.role === HEAD_SUPPORT;
  const canEditRow = (row: Teacher) =>
    canEdit || (isHeadSupport && row.kind === "support");
  const canAccountRow = (row: Teacher) =>
    canAccount || (isHeadSupport && row.kind === "support");
  // Support biriktirish huquqi bor, lekin tahrirlash yo'q rollar
  // (masalan o'quv bo'limi rahbari) ham amal ustunini ko'radi.
  const canAssign = can(user?.role, SUPPORT_ASSIGN);
  const canAccount = can(user?.role, ACCOUNT_MANAGE);
  // Ustozning o'zi hamkasbining oyligini ochmaydi
  const canSeeSalary =
    can(user?.role, SALARY_SELF_VIEW) && !can(user?.role, [TEACHER, SUPPORT_TEACHER]);
  // Filtrlar: qidiruv / filial / fan / holat
  const [tq, setTq] = useState("");
  const [branchF, setBranchF] = useState("");
  const [subjectF, setSubjectF] = useState("");
  // Sukut bo'yicha faqat ishlayotganlar — ketganlar Arxivda
  const [activeF, setActiveF] = useState("active");
  // Yordamchi o'qituvchilar alohida bo'limda turadi (LC UP dagidek)
  const isSupportTab = tab === "support";
  // Supportlarning shu oy oyligi — ro'yxatda summa ko'rinadi
  const [supSalaries, setSupSalaries] = useState<
    Record<number, { salary: number; session_count: number;
                     grade_note?: string }>
  >({});
  useEffect(() => {
    if (!isSupportTab || !canSeeSalary) return;
    api
      .get<{ rows: { teacher_id: number; salary: number;
                     session_count: number;
                     grade_note?: string }[] }>(
        "/support-teachers/salaries?x=1")
      .then((r) => {
        const m: Record<number, { salary: number; session_count: number;
                                  grade_note?: string }> = {};
        for (const row of r.rows)
          m[row.teacher_id] = {
            salary: row.salary,
            session_count: row.session_count,
            grade_note: row.grade_note,
          };
        setSupSalaries(m);
      })
      .catch(() => setSupSalaries({}));
  }, [isSupportTab, canSeeSalary]);
  const visibleTeachers = teachers.filter((t) => {
    if (isSupportTab ? t.kind !== "support" : t.kind === "support")
      return false;
    if (tq && !t.full_name.toLowerCase().includes(tq.toLowerCase()))
      return false;
    if (branchF && !(t.branch_ids || (t.branch_id ? [t.branch_id] : []))
        .includes(Number(branchF)))
      return false;
    if (subjectF && t.subject !== subjectF) return false;
    if (activeF === "active" && t.is_active === 0) return false;
    if (activeF === "left" && t.is_active !== 0) return false;
    return true;
  });
  const supportCount = teachers.filter((t) => t.kind === "support").length;
  const activeCount = visibleTeachers.filter(
    (t) => t.is_active !== 0
  ).length;

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

  // Volontyor supportga "Mening oyligim" umuman chiqmaydi - u oylik
  // olmaydi (Jahongir). Rahbariyat hisobotlariga bu ta'sir qilmaydi.
  const isTeacher =
    (user?.role === TEACHER || user?.role === SUPPORT_TEACHER) &&
    !user?.salary_hidden;

  return (
    <div className="p-8">
      <div className="flex items-center gap-1 mb-5">
        {[
          ...(isTeacher ? [{ k: "salary", l: "Mening oyligim" }] : []),
          { k: "list", l: "O'qituvchilar" },
          { k: "support", l: `Yordamchi o'qituvchilar (${supportCount})` },
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

      {(tab === "list" || tab === "support") && (
      <>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">
            {isSupportTab ? "Yordamchi o'qituvchilar" : "O'qituvchilar"}
          </h1>
          <p className="text-sm text-slate-500">
            Ishlayapti: {activeCount}
            {visibleTeachers.length > activeCount &&
              ` · ketgan: ${visibleTeachers.length - activeCount}`}
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

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-52"
          placeholder="Ism bo'yicha qidirish"
          value={tq}
          onChange={(e) => setTq(e.target.value)}
        />
        {branches.length > 1 && (
          <select value={branchF} onChange={(e) => setBranchF(e.target.value)}
            className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white">
            <option value="">Barcha filiallar</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        )}
        <select value={subjectF} onChange={(e) => setSubjectF(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white">
          <option value="">Barcha fanlar</option>
          {SUBJECTS.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>
        <select value={activeF} onChange={(e) => setActiveF(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white">
          <option value="">Hammasi</option>
          <option value="active">Ishlayapti</option>
          <option value="left">Ketgan</option>
        </select>
        {(tq || branchF || subjectF || activeF) && (
          <button
            onClick={() => { setTq(""); setBranchF(""); setSubjectF(""); setActiveF(""); }}
            className="text-xs text-slate-400 hover:text-slate-600">
            Tozalash
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">F.I.Sh.</th>
                <th className="text-left px-4 py-3 font-medium">Telefon</th>
                <th className="text-left px-4 py-3 font-medium">Fan</th>
                <th className="text-left px-4 py-3 font-medium">Daraja</th>
                <th className="text-left px-4 py-3 font-medium">Filial</th>
                <th className="text-left px-4 py-3 font-medium">Ishga kirgan</th>
                {isSupportTab && canSeeSalary && (
                  <th className="text-right px-4 py-3 font-medium">
                    Oylik (shu oy)
                  </th>
                )}
                {(canEdit || canAssign || isHeadSupport) && (
                  <th className="px-4 py-3"></th>
                )}
              </tr>
            </thead>
            <tbody>
              {visibleTeachers.map((t) => {
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
                      ) : (
                        <button
                          onClick={() => setGroupsFor(t)}
                          className="hover:text-brand-700"
                          title="Guruhlari"
                        >
                          {t.full_name}
                        </button>
                      )}
                      {canSeeSalary &&
                        user?.role !== FOUNDER &&
                        user?.role !== ACADEMIC_HEAD && (
                        <button
                          onClick={() => setSalary(t.id)}
                          className="ml-1.5 text-[11px] text-emerald-600 hover:text-emerald-800"
                          title="Ish haqi kartasi"
                        >
                          so'm
                        </button>
                      )}
                      {left && (
                        <span className="ml-2 text-[10px] uppercase tracking-wide bg-slate-200 text-slate-500 px-1.5 py-0.5 rounded">
                          ketgan {t.left_date ? formatDate(t.left_date) : ""}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatPhone(t.phone) || "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{subjectLabel(t.subject) || "—"}</td>
                    <td className="px-4 py-3">
                      {t.kind === "support" ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-sky-50 text-sky-700">
                          Support · {t.staff_grade_label || "Volontyor"}
                        </span>
                      ) : (
                      <button
                        onClick={() => setCareer(t.id)}
                        className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 hover:bg-brand-50 hover:text-brand-700"
                        title="Karyera kartasi"
                      >
                        {gradeLabels[t.grade || ""] || "—"}
                      </button>
                      )}
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
                    {isSupportTab && canSeeSalary && (
                      <td className="px-4 py-3 text-right">
                        {supSalaries[t.id] ? (
                          <span className="font-medium text-slate-800">
                            {supSalaries[t.id].grade_note ? (
                              <span className="text-amber-700">Volontyor</span>
                            ) : (
                              formatSom(supSalaries[t.id].salary)
                            )}
                            <span className="block text-[11px] font-normal text-slate-400">
                              {supSalaries[t.id].session_count} ta seans
                              {supSalaries[t.id].grade_note
                                ? " · oylik yo'q"
                                : ""}
                            </span>
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                    )}
                    {(canEdit || canAssign || isHeadSupport) && (
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        {canEditRow(t) && (
                        <button
                          onClick={() => setEditing(t)}
                          title="Tahrirlash"
                          className="text-slate-400 hover:text-brand-600 mr-2"
                        >
                          <Pencil size={15} />
                        </button>
                        )}
                        {canAccountRow(t) && !left && (
                          <button
                            onClick={() => setAccountFor(t)}
                            title={
                              t.login
                                ? `Login: ${t.login} — login / parolni o'zgartirish`
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
                        {canEditRow(t) && (
                        <button
                          onClick={() => toggleActive(t)}
                          title={left ? "Ishga qaytarish" : "Ishdan ketgan deb belgilash"}
                          className="text-slate-400 hover:text-brand-600"
                        >
                          {left ? <UserCheck size={16} /> : <UserMinus size={16} />}
                        </button>
                        )}
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
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <TeacherModal
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
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
      {groupsFor && (
        <TeacherGroupsModal
          teacherId={groupsFor.id}
          onClose={() => setGroupsFor(null)}
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
  // Loginni shu yerning o'zida almashtirish (2026-09-16, Jahongir:
  // "login o'zgartirib bo'lmadiku ... HR edit qila olsin")
  const [login, setLogin] = useState(teacher.login ?? "");
  const [newLogin, setNewLogin] = useState(teacher.login ?? "");
  const [loginMsg, setLoginMsg] = useState<string | null>(null);

  async function saveLogin() {
    const v = newLogin.trim();
    if (!teacher.user_id || v === login) return;
    if (!/^[A-Za-z0-9._@-]{3,40}$/.test(v)) {
      setError("Login 3-40 belgi bo'lsin: lotin harflari, raqamlar va "
        + ". _ - @ belgilari, probelsiz");
      return;
    }
    setBusy(true);
    setError(null);
    setLoginMsg(null);
    try {
      const r = await api.put<{ username: string }>(
        `/users/${teacher.user_id}`, { username: v });
      setLogin(r.username);
      setNewLogin(r.username);
      setLoginMsg("Login saqlandi. Ustoz endi shu login bilan kiradi.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

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
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[92vh] overflow-y-auto">
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
                  <p className="text-xs text-slate-500 mb-1">Login</p>
                  {teacher.user_id ? (
                    <div className="flex gap-2">
                      <input
                        value={newLogin}
                        onChange={(e) => setNewLogin(e.target.value)}
                        autoCapitalize="none"
                        spellCheck={false}
                        className="flex-1 min-w-0 rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-mono text-sm"
                      />
                      <button
                        onClick={saveLogin}
                        disabled={busy || newLogin.trim() === login}
                        className="rounded-lg bg-brand-600 text-white px-3 text-xs font-medium disabled:opacity-40"
                      >
                        Saqlash
                      </button>
                    </div>
                  ) : (
                    <p className="font-mono text-sm text-slate-900">{login}</p>
                  )}
                  {loginMsg && (
                    <p className="text-xs text-emerald-700 mt-1.5">{loginMsg}</p>
                  )}
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
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-4">
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
                          <td className="px-3 py-1.5 text-slate-600">{formatPhone(r.phone)}</td>
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
