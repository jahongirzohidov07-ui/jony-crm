import { useCallback, useEffect, useState } from "react";
import { formatPhone } from "../components/PhoneInput";
import { useSearchParams } from "react-router-dom";
import {
  Plus, Trash2, Pencil, Users, UserCheck, Clock, Briefcase, X,
  ClipboardList, LayoutDashboard, UserPlus, GraduationCap, ShieldCheck,
  MoreHorizontal,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell,
} from "recharts";
import {
  api, type Vacancy, type Candidate, type HrFunnel, type Branch,
  type LibraryList, type LibraryItem, type LibraryPeople,
  type CandidateHistoryRow,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { AtsBoard } from "../components/AtsBoard";
import { HrOverviewTab, HrLifecycleTab } from "../components/HrLifecycle";
import {
  HR_ACCESS, HR_CANDIDATE_VIEW, can, ALL_ROLES, roleLabel,
  EXAMINER_PENALTY_SET, SUPPORT_PENALTY_SET, BLACKLIST_VIEW,
} from "../lib/roles";
import {
  CANDIDATE_STAGES, CANDIDATE_SOURCES, APPLY_POSITIONS,
  APPLY_MARITAL, APPLY_WORK_DURATIONS,
  VACANCY_STATUSES, stageLabel, stageColor, candidateSourceLabel,
  vacancyStatusLabel,
} from "../lib/hr";
import { CandidateCard } from "../components/CandidateCard";
import { ScheduleDialog } from "../components/ScheduleDialog";
import { HrCalendar } from "../components/HrCalendar";
import { AttendanceTab, NpsTab } from "../components/HrExtras";
import { StaffDatesTab } from "../components/StaffDates";
import { ObservationsTab } from "../components/LessonRubric";
import { StaffTab } from "./Users";
import {
  WorkforceTab, StaffRequestsTab, HrVacanciesTab,
} from "../components/HrCore";
import { formatSom, formatDate } from "../lib/format";
import { Attachments } from "../components/Attachments";
import { PenaltyPointsTab } from "../components/PenaltyPoints";
import { HrBlacklistTab, BlacklistBadge } from "../components/HrBlacklist";
import { DuplicateCandidateDialog } from "../components/CandidateHistory";
import { exportToExcel } from "../lib/exportXlsx";
import { HrVacancyReport } from "../components/HrVacancyReport";
import { ChecklistTab } from "../components/HrChecklist";
import { ExaminerStatusTab } from "../components/HrExaminers";
import { StaffRestoreModal } from "../components/StaffRestore";
import { PayrollTab } from "../components/Payroll";
import { InterviewSheet } from "../components/InterviewSheet";
import { InterviewGuideEditor } from "../components/InterviewGuideEditor";

/** Nomzodning suhbat bahosi (barcha suhbatdoshlar bo'yicha) */
type InterviewSum = {
  percent: number | null; band: string; band_tone: string;
  interviewers: number; final_label: string | null; split: boolean;
};
const IV_TONE: Record<string, string> = {
  emerald: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100",
  teal: "bg-teal-50 text-teal-700 hover:bg-teal-100",
  amber: "bg-amber-50 text-amber-800 hover:bg-amber-100",
  red: "bg-red-50 text-red-700 hover:bg-red-100",
};

type Tab = "overview" | "ats" | "lifecycle" | "funnel" | "candidates" | "vacancies" | "staff"
  | "calendar"
  | "rubric" | "dates" | "attendance" | "nps"
  | "workforce" | "requests" | "hrvacancies" | "library" | "onbsteps"
  | "penalty" | "blacklist" | "solo" | "exited" | "drill" | "checklist"
  | "examiners" | "payroll";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Umumiy holat" },
  { key: "ats", label: "Ishga olish quvuri" },
  { key: "lifecycle", label: "Hayotiy sikl" },
  { key: "funnel", label: "HR analitika" },
  { key: "workforce", label: "Shtat rejasi" },
  { key: "requests", label: "Xodim so'rovlari" },
  { key: "hrvacancies", label: "Vakansiyalar" },
  { key: "candidates", label: "Nomzodlar" },
  { key: "vacancies", label: "Vakansiyalar (eski ko'rinish)" },
  { key: "staff", label: "Xodimlar" },
  { key: "calendar", label: "Kalendar" },
  { key: "rubric", label: "Dars baholash" },
  { key: "dates", label: "Sanalar" },
  { key: "attendance", label: "Davomat" },
  { key: "nps", label: "Ustozlar NPS" },
  { key: "library", label: "Kutubxona" },
  // 2026-09-26, Jahongir: "supportlarga ko'rgan videolari va o'qigan
  // kitobini o'tdi o'tmadi qilib bitta katta jadvalda"
  { key: "checklist", label: "Checklist" },
  // 2026-10-05, Jahongir: "hr uchun examinerlarni valantyor va examiner
  // qilib o'zgartirishni qo'shib ber"
  { key: "examiners", label: "Examinerlar" },
  // 2026-10-07, Jahongir: "hrga supportlarni examinerlarni oyligi
  // ko'rinadigan bo'lim ochib ber" — Hisobotlar -> Ish haqi dagi
  // jadvallarning o'zi (HR menyusida Hisobotlar yo'q).
  { key: "payroll", label: "Oyliklar" },
  // 2026-08-20, Jahongir: "hamma xodimga xar xilda onboarding"
  { key: "onbsteps", label: "Onboarding" },
  // 2026-09-23, Jahongir: "hr qo'sha olsin u o'quvchilarni"
  { key: "solo", label: "Yakka support" },
  // 2026-09-24, Jahongir: "hr ga xodimlar arxivini ochib ber"
  { key: "exited", label: "Ketganlar arxivi" },
  // 2026-09-25: adminlar mashqi — vazifalar va soniyalar
  { key: "drill", label: "Admin mashqi" },
  // 2026-09-16, Jahongir: examiner va supportlardan jarima ball ayirish
  { key: "penalty", label: "Jarima ballari" },
  // 2026-09-16, Jahongir: "o'quv markaz qora ro'yxatini shakllantir"
  { key: "blacklist", label: "Qora ro'yxat" },
];

/* BO'LIMLAR (2026-10-22, Jahongir: "hr bo'limi juda tartibsz shuni
   chiroyli qilib tartibla lekin hech narsa yo'qolmasin"). 25 ta tab
   bitta qatorda turardi — endi 5 ta guruh, har birining ichida o'z
   tablari. Tablar o'zi, ularning ichidagi narsalar va ?tab= havolalari
   o'zgarmagan. Guruhga kiritilmay qolgan yangi tab "Boshqa" ga tushadi
   — hech qachon yo'qolib qolmaydi. */
type GroupKey = "home" | "hiring" | "people" | "growth" | "quality" | "other";

const GROUPS: {
  key: GroupKey; label: string; hint: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  tabs: Tab[];
}[] = [
  { key: "home", label: "Umumiy", icon: LayoutDashboard,
    hint: "Holat, analitika va kalendar",
    tabs: ["overview", "funnel", "calendar"] },
  { key: "hiring", label: "Ishga olish", icon: UserPlus,
    hint: "Vakansiya, nomzod, suhbat, shtat",
    tabs: ["ats", "candidates", "hrvacancies", "requests", "workforce",
           "vacancies", "blacklist"] },
  { key: "people", label: "Xodimlar", icon: Users,
    hint: "Ro'yxat, davomat, oylik, arxiv",
    tabs: ["staff", "lifecycle", "examiners", "solo", "attendance",
           "payroll", "dates", "exited"] },
  { key: "growth", label: "O'qitish", icon: GraduationCap,
    hint: "Onboarding, kutubxona, mashqlar",
    tabs: ["onbsteps", "library", "checklist", "drill"] },
  { key: "quality", label: "Sifat va intizom", icon: ShieldCheck,
    hint: "Dars baholash, NPS, jarima",
    tabs: ["rubric", "nps", "penalty"] },
];

function groupsFor(tabs: { key: Tab; label: string }[]) {
  const label = new Map(tabs.map((t) => [t.key, t.label]));
  const placed = new Set<Tab>();
  const out = GROUPS.map((g) => {
    const items = g.tabs.filter((k) => label.has(k))
      .map((k) => ({ key: k, label: label.get(k)! }));
    items.forEach((t) => placed.add(t.key));
    return { ...g, items };
  });
  const rest = tabs.filter((t) => !placed.has(t.key));
  if (rest.length)
    out.push({ key: "other", label: "Boshqa", icon: MoreHorizontal,
               hint: "", tabs: [], items: rest });
  return out.filter((g) => g.items.length > 0);
}

/** Nomzod formasidagi maydon: SAVOL doim tepada turadi (2026-09-16,
 *  Jahongir: "katakda nima so'ralgani ham tursin tepada") — qiymat
 *  yozilgach placeholder yo'qolib, nima haqida ekani bilinmay qolardi. */
function FormField({ label, children }: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-slate-500 mb-1">
        {label}
      </span>
      {children}
    </label>
  );
}

function Stat({
  label, value, hint, icon: Icon, tone = "slate",
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  tone?: "slate" | "green" | "amber";
}) {
  const cls =
    tone === "green" ? "text-emerald-600"
      : tone === "amber" ? "text-amber-600"
        : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${cls}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

// ------------------------------------------------------------ Voronka
function FunnelTab() {
  const [data, setData] = useState<HrFunnel | null>(null);
  const [months, setMonths] = useState(12);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<HrFunnel>(`/reports/hr-funnel?months=${months}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [months]);

  const monthPicker = (
    <div className="flex gap-1 mb-5">
      {[3, 6, 12, 24].map((m) => (
        <button
          key={m}
          onClick={() => setMonths(m)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
            months === m
              ? "bg-brand-50 border-brand-400 text-brand-700"
              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
          }`}
        >
          {m} oy
        </button>
      ))}
    </div>
  );

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  if (data.total === 0) {
    return (
      <div>
        {monthPicker}
        <HrVacancyReport months={months} />
        <p className="text-sm text-slate-400 py-10 text-center">
          Bu davrda nomzod kiritilmagan. "Nomzodlar" bo'limidan qo'shing —
          voronka shundan keyin chiqadi.
        </p>
      </div>
    );
  }

  const chart = data.stages.map((s) => ({
    name: s.label,
    Yetgan: s.reached,
    color: stageColor(s.stage),
  }));

  return (
    <div>
      {monthPicker}

      {/* Vakansiya kesimi: necha kunda yopildi, nechta nomzoddan nechtasi olindi */}
      <HrVacancyReport months={months} />

      <p className="text-base font-semibold text-slate-900 mb-3">Nomzodlar voronkasi</p>
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
        <Stat label="Jami nomzod" value={String(data.total)} icon={Users} />
        <Stat label="Ishga olindi" value={String(data.hired)} tone="green" icon={UserCheck} />
        <Stat label="Rad etildi" value={String(data.rejected)} />
        <Stat
          label="Ishga olish foizi"
          value={`${data.hire_rate}%`}
          hint="nomzoddan xodimga"
        />
        <Stat
          label="O'rtacha muddat"
          value={`${data.avg_days_to_hire} kun`}
          hint="arizadan ishga olishgacha"
          icon={Clock}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
        <p className="text-sm font-medium text-slate-700">Bosqichlar</p>
        <p className="text-xs text-slate-400 mb-3">
          Nomzodlar qaysi bosqichda to'xtab qolyapti
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chart} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis
              type="category"
              dataKey="name"
              width={130}
              tick={{ fontSize: 11, fill: "#64748b" }}
            />
            <Tooltip />
            <Bar dataKey="Yetgan" radius={[0, 4, 4, 0]} isAnimationActive={false}>
              {chart.map((c, i) => (
                <Cell key={i} fill={c.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-100">
                <th className="text-left py-2">Bosqich</th>
                <th className="text-right">Yetgan</th>
                <th className="text-right">Shu yerda qolgan</th>
                <th className="text-right">Foiz</th>
              </tr>
            </thead>
            <tbody>
              {data.stages.map((s) => (
                <tr key={s.stage} className="border-b border-slate-50">
                  <td className="py-2 flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ background: stageColor(s.stage) }}
                    />
                    {s.label}
                  </td>
                  <td className="text-right font-medium">{s.reached}</td>
                  <td className="text-right text-slate-500">
                    {s.stuck_here || "—"}
                  </td>
                  <td className="text-right text-slate-500">{s.percent}%</td>
                </tr>
              ))}
              <tr>
                <td className="py-2 flex items-center gap-2 text-red-600">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  Rad etildi
                </td>
                <td className="text-right font-medium text-red-600">
                  {data.rejected}
                </td>
                <td className="text-right">—</td>
                <td className="text-right text-slate-500">
                  {data.total ? Math.round((data.rejected / data.total) * 1000) / 10 : 0}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <p className="text-sm font-medium text-slate-700">Nomzodlar qayerdan kelyapti</p>
        <p className="text-xs text-slate-400 mb-3">
          Qaysi manba haqiqiy xodim beryapti — reklama byudjetini shunga qarab bo'ling
        </p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-100">
              <th className="text-left py-2">Manba</th>
              <th className="text-right">Nomzod</th>
              <th className="text-right">Ishga olindi</th>
              <th className="text-right">Samaradorlik</th>
            </tr>
          </thead>
          <tbody>
            {data.sources.map((s) => (
              <tr key={s.key} className="border-b border-slate-50">
                <td className="py-2">{s.label}</td>
                <td className="text-right">{s.total}</td>
                <td className="text-right font-medium text-emerald-600">
                  {s.hired}
                </td>
                <td className="text-right text-slate-500">{s.percent}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --------------------------------------------------------- Nomzodlar
/**
 * Yangi nomzod formasi — jonyos.uz/apply dagi savollar bilan BIR XIL
 * (2026-08-15, Jahongir: "yangi nomzod qo'lda ochsam biz link jo'natib
 * so'rovnomadagi savollar chiqmas ekan, qo'lda kiritsa ham shu
 * savollar chiqishi kerak").
 */
const emptyCand = {
  full_name: "",
  phone: "",
  vacancy_id: "" as string | number,
  position: "",
  subject: "",
  experience_years: "",
  address: "",
  birth_date: "",
  education: "",
  marital: "",
  socials: "",
  workplaces: "",
  work_duration: "",
  stage: "applied",
  source: "other",
  branch_id: "" as string | number,
  note: "",
};

function CandidatesTab({ branches }: { branches: Branch[] }) {
  const { user } = useAuth();
  const [rows, setRows] = useState<Candidate[]>([]);
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Candidate | null>(null);
  const [card, setCard] = useState<number | null>(null);
  // Suhbat varaqasi (2026-10-08) — savol, javob va ball
  const [sheet, setSheet] = useState<number | null>(null);
  const [guideEd, setGuideEd] = useState(false);
  const [ivs, setIvs] = useState<Record<string, InterviewSum>>({});
  const [schedule, setSchedule] = useState<
    { id: number; name: string; stage: string } | null
  >(null);
  const [form, setForm] = useState({ ...emptyCand });
  const [stageFilter, setStageFilter] = useState("");
  // FILTRLAR (2026-08-15, Jahongir: "filtr ham qoyib bersan shu yerga
  // nomzodlar kopayganda topish osonlashadi"). Hammasi birga ishlaydi.
  const [search, setSearch] = useState("");
  const [posFilter, setPosFilter] = useState("");
  const [subjFilter, setSubjFilter] = useState("");
  const [srcFilter, setSrcFilter] = useState("");
  const [brFilter, setBrFilter] = useState("");
  const [err, setErr] = useState("");

  const load = () => {
    setLoading(true);
    Promise.all([
      api.get<Candidate[]>("/candidates"),
      api.get<Vacancy[]>("/vacancies"),
    ])
      .then(([c, v]) => {
        setRows(c);
        setVacancies(v);
      })
      .finally(() => setLoading(false));
    loadIvs();
  };
  const loadIvs = () =>
    api.get<{ rows: Record<string, InterviewSum> }>("/hr/interview-summary", true)
      .then((d) => setIvs(d.rows))
      .catch(() => setIvs({}));
  useEffect(load, []);

  const open = async (c?: Candidate) => {
    setErr("");
    if (c) {
      setEditing(c);
      setForm({
        ...emptyCand,
        full_name: c.full_name,
        phone: c.phone ?? "",
        vacancy_id: c.vacancy_id ?? "",
        position: c.position ?? "",
        subject: c.subject ?? "",
        stage: c.stage,
        source: c.source,
        branch_id: c.branch_id ?? "",
        note: c.note ?? "",
      });
      setModal(true);
      // Ariza javoblari kartada to'liq saqlanadi — tahrirlashda ham
      // shu savollar to'ldirilgan holda chiqsin (2026-08-15).
      try {
        const full = await api.fresh<Record<string, unknown>>(
          `/candidates/${c.id}`
        );
        const g = (k: string) => (full[k] as string) ?? "";
        setForm((p) => ({
          ...p,
          address: g("address"),
          birth_date: g("birth_date_text"),
          education: g("education"),
          marital: g("marital"),
          socials: g("socials"),
          workplaces: g("workplaces"),
          work_duration: g("work_duration"),
          experience_years:
            full["experience_years"] != null
              ? String(full["experience_years"])
              : "",
        }));
      } catch {
        /* karta yuklanmasa ham asosiy maydonlar joyida */
      }
      return;
    } else {
      setEditing(null);
      setForm({ ...emptyCand });
    }
    setModal(true);
  };

  const [dupRows, setDupRows] = useState<CandidateHistoryRow[] | null>(null);

  const save = async (force = false) => {
    if (!form.full_name.trim()) {
      setErr("Ism-familiya kiritilishi shart");
      return;
    }
    const body = {
      full_name: form.full_name.trim(),
      phone: form.phone || null,
      vacancy_id: form.vacancy_id ? Number(form.vacancy_id) : null,
      position: form.position || null,
      subject: form.position === "teacher" ? (form.subject || null) : null,
      // Ariza savollari (2026-08-15) — havola orqali kelgan nomzod
      // bilan bir xil ma'lumot yig'iladi
      address: form.address || null,
      education: form.education || null,
      marital: form.marital || null,
      socials: form.socials || null,
      workplaces: form.workplaces || null,
      work_duration: form.work_duration || null,
      experience_years: form.experience_years
        ? Number(form.experience_years)
        : null,
      stage: form.stage,
      source: form.source,
      branch_id: form.branch_id ? Number(form.branch_id) : null,
      note: form.note || null,
    };
    const bodyWithDate = editing
      ? { ...body, birth_date_text: form.birth_date || null }
      : { ...body, birth_date: form.birth_date || null };
    try {
      if (editing)
        await api.put(`/candidates/${editing.id}`, bodyWithDate);
      else {
        const r = await api.post<{ duplicate?: boolean;
                                   history?: CandidateHistoryRow[] }>(
          "/candidates", { ...bodyWithDate, force });
        // Bu odam avval ham kelgan — HR qaror qilsin (2026-09-16)
        if (r?.duplicate) {
          setDupRows(r.history || []);
          return;
        }
      }
      setDupRows(null);
      setModal(false);
      load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const move = async (c: Candidate, stage: string) => {
    // 2026-08-12, Jahongir: "rad etildidan keyin sabab so'rasa yaxshi edi"
    // SUHBAT / SINOV DARSI — sana so'raladi (2026-08-16, Jahongir:
    // "suhbatga chaqrildi yoki sinov darsi belgilansa sana so'rasin
    // soati va kunini kiritsam shu bo'limga biriktirilsin").
    // Bosqich shu oynada saqlanadi — bu yerda hech narsa yozilmaydi.
    if (stage === "interview" || stage === "demo") {
      setSchedule({ id: c.id, name: c.full_name, stage });
      return;
    }
    let reject_reason: string | undefined;
    if (stage === "rejected") {
      const r = prompt("Rad etish sababi (nomzod kartasida saqlanadi):");
      if (r === null) return;          // bekor qilindi
      reject_reason = r.trim() || undefined;
    }
    await api.put(`/candidates/${c.id}`, { stage, reject_reason });
    load();
  };

  const remove = async (c: Candidate) => {
    if (!confirm(`${c.full_name} o'chirilsinmi?`)) return;
    await api.delete(`/candidates/${c.id}`);
    load();
  };

  // Fanlar ro'yxati mavjud nomzodlardan yig'iladi — ariza formasida
  // fan erkin yoziladi, oldindan aniq ro'yxat yo'q.
  const subjects = Array.from(
    new Set(rows.map((r) => (r.subject || "").trim()).filter(Boolean))
  ).sort((a, b) => a.localeCompare(b));

  const digits = (v: string) => v.replace(/\D/g, "");
  const term = search.trim().toLowerCase();
  const termDigits = digits(search);
  const shown = rows.filter((r) => {
    if (stageFilter && r.stage !== stageFilter) return false;
    if (posFilter && (r.position || "") !== posFilter) return false;
    if (subjFilter && (r.subject || "") !== subjFilter) return false;
    if (srcFilter && r.source !== srcFilter) return false;
    if (brFilter && String(r.branch_id ?? "") !== brFilter) return false;
    if (term) {
      const byName = r.full_name.toLowerCase().includes(term);
      const byPhone =
        termDigits.length >= 3 &&
        digits(r.phone || "").includes(termDigits);
      const byRole = (r.role_label || "").toLowerCase().includes(term);
      if (!byName && !byPhone && !byRole) return false;
    }
    return true;
  });
  const poolCount = rows.filter((r) => r.stage === "pool").length;
  const anyFilter =
    stageFilter || posFilter || subjFilter || srcFilter || brFilter || term;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          <option value="">Barcha bosqichlar</option>
          {CANDIDATE_STAGES.map((s) => (
            <option key={s.key} value={s.key}>
              {s.label}
            </option>
          ))}
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Ism yoki telefon…"
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm w-52"
        />
        <select
          value={posFilter}
          onChange={(e) => setPosFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          <option value="">Barcha lavozimlar</option>
          {APPLY_POSITIONS.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
        {subjects.length > 0 && (
          <select
            value={subjFilter}
            onChange={(e) => setSubjFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
          >
            <option value="">Barcha fanlar</option>
            {subjects.map((sb) => (
              <option key={sb} value={sb}>
                {sb}
              </option>
            ))}
          </select>
        )}
        <select
          value={srcFilter}
          onChange={(e) => setSrcFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
        >
          <option value="">Barcha manbalar</option>
          {CANDIDATE_SOURCES.map((s2) => (
            <option key={s2.key} value={s2.key}>
              {s2.label}
            </option>
          ))}
        </select>
        {branches.length > 1 && (
          <select
            value={brFilter}
            onChange={(e) => setBrFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
          >
            <option value="">Barcha filiallar</option>
            {branches.map((b) => (
              <option key={b.id} value={String(b.id)}>
                {b.name}
              </option>
            ))}
          </select>
        )}
        <span className="text-sm text-slate-500">
          {shown.length} ta nomzod
          {anyFilter && rows.length !== shown.length && (
            <span className="text-slate-400"> / {rows.length}</span>
          )}
        </span>
        {anyFilter && (
          <button
            onClick={() => {
              setStageFilter("");
              setSearch("");
              setPosFilter("");
              setSubjFilter("");
              setSrcFilter("");
              setBrFilter("");
            }}
            className="px-2.5 py-1 rounded-lg text-xs font-medium border border-slate-200 text-slate-600 hover:border-slate-300"
          >
            Filtrni tozalash
          </button>
        )}
        {poolCount > 0 && (
          <button
            onClick={() => setStageFilter(stageFilter === "pool" ? "" : "pool")}
            title="Hozir olmadik, lekin kelajakda kerak bo'lishi mumkin"
            className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
              stageFilter === "pool"
                ? "bg-teal-600 text-white border-teal-600"
                : "bg-teal-50 text-teal-700 border-teal-200 hover:border-teal-300"
            }`}
          >
            Zaxirada: {poolCount}
          </button>
        )}
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("nomzodlar", "Nomzodlar",
              shown.map((c) => ({
                "F.I.Sh.": c.full_name,
                Telefon: c.phone ?? "",
                "Yashash joyi": c.address ?? "",
                Vakansiya: c.role_label ?? "",
                Fan: c.subject ?? "",
                Bosqich: stageLabel(c.stage),
                Manba: candidateSourceLabel(c.source),
                Filial: c.branch ?? "",
                "Suhbat bahosi": ivs[c.id]?.percent != null ? `${ivs[c.id].percent}%` : "",
                "Suhbat xulosasi": ivs[c.id] ? (ivs[c.id].final_label || ivs[c.id].band) : "",
                Sana: c.created_at?.slice(0, 10) ?? "",
              })))
          }
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          Excel
        </button>
        <button
          onClick={() => setGuideEd(true)}
          title="Suhbat savollarini ko'rish, o'zgartirish va bo'sh blank chop etish"
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <ClipboardList size={15} /> Suhbat savollari
        </button>
        <button
          onClick={() => open()}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={15} /> Nomzod
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : shown.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Nomzod yo'q
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">F.I.Sh.</th>
                <th className="text-left">Telefon</th>
                {/* 2026-09-24, Jahongir: "yashash joyi chiqib tursin
                    karta ochilmasdan turib ham" */}
                <th className="text-left">Yashash joyi</th>
                <th className="text-left">Vakansiya</th>
                <th className="text-left">Manba</th>
                <th className="text-left">Bosqich</th>
                <th className="text-left">Sana</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {shown.map((c) => (
                <tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => setCard(c.id)}
                      className="font-medium text-slate-800 hover:text-brand-700"
                      title="Nomzod kartasi"
                    >
                      {c.full_name}
                    </button>
                    <BlacklistBadge hit={c.blacklist} />
                    {!!c.other_applications && (
                      <span
                        title="Bu odam avval ham ariza bergan — kartada tarixi"
                        className="ml-1.5 inline-block px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-semibold align-middle"
                      >
                        {c.other_applications + 1}-ariza
                      </span>
                    )}
                  </td>
                  <td className="text-slate-500">{formatPhone(c.phone) || "—"}</td>
                  <td className="text-slate-600 max-w-[190px]">
                    {c.address ? (
                      <span className="block truncate" title={c.address}>
                        {c.address}
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="text-slate-600">
                    {c.role_label ? (
                      <>
                        <span>{c.role_label}</span>
                        {c.subject && (
                          <span className="ml-1.5 inline-block px-1.5 py-0.5 rounded bg-brand-50 text-brand-700 text-[11px] font-medium align-middle">
                            {c.subject}
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="text-slate-500">
                    {candidateSourceLabel(c.source)}
                  </td>
                  <td>
                    <select
                      value={c.stage}
                      onChange={(e) => move(c, e.target.value)}
                      className="text-xs px-2 py-1 rounded-md border border-slate-200 bg-white"
                      style={{ color: stageColor(c.stage) }}
                    >
                      {CANDIDATE_STAGES.map((s) => (
                        <option key={s.key} value={s.key}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="text-slate-400 text-xs">
                    {c.created_at ? formatDate(c.created_at.slice(0, 10)) : "—"}
                  </td>
                  <td className="pr-3 text-right whitespace-nowrap">
                    {(() => {
                      const iv = ivs[c.id];
                      const scored = iv && iv.percent != null;
                      return (
                        <button
                          onClick={() => setSheet(c.id)}
                          className={`inline-flex items-center gap-1 px-2 py-1 mr-1 rounded-md text-xs font-medium ${scored
                            ? IV_TONE[iv.band_tone] || IV_TONE.amber
                            : "text-brand-700 bg-brand-50 hover:bg-brand-100"}`}
                          title={scored
                            ? `Suhbat bahosi: ${iv.percent}% — ${iv.band}`
                              + (iv.final_label ? ` · ${iv.final_label}` : "")
                              + ` · ${iv.interviewers} suhbatdosh`
                              + (iv.split ? " · fikrlar tarqoq" : "")
                            : "Suhbat varaqasi: savollar, javoblar va baho"}
                        >
                          <ClipboardList size={13} />
                          {scored ? `${iv.percent}%` : "Suhbat"}
                          {scored && iv.split && <span title="Fikrlar tarqoq">⚠</span>}
                        </button>
                      );
                    })()}
                    <button
                      onClick={() => open(c)}
                      className="p-1.5 text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => remove(c)}
                      className="p-1.5 text-slate-400 hover:text-red-600"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {schedule && (
        <ScheduleDialog
          candidateId={schedule.id}
          candidateName={schedule.name}
          stage={schedule.stage}
          onClose={() => setSchedule(null)}
          onDone={() => {
            setSchedule(null);
            load();
          }}
        />
      )}

      {sheet !== null && (
        <InterviewSheet
          candidateId={sheet}
          onClose={() => { setSheet(null); load(); }}
        />
      )}

      {guideEd && (
        <InterviewGuideEditor
          onClose={() => setGuideEd(false)}
          onSaved={loadIvs}
        />
      )}

      {card !== null && (
        <CandidateCard
          id={card}
          /* O'quv bo'limi rahbari kartani TAHRIRLAMAYDI — u faqat
             ma'lumotni ko'rib, sinov darsini baholaydi
             (2026-08-16). Server ham shu qoidada: PUT hamon
             HR_ACCESS'da. */
          canEdit={can(user?.role, HR_ACCESS)}
          onClose={() => setCard(null)}
          onSaved={load}
        />
      )}

      {modal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-5 max-h-[88vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">
                {editing ? "Nomzodni tahrirlash" : "Yangi nomzod"}
              </h3>
              <button onClick={() => setModal(false)} className="text-slate-400">
                <X size={18} />
              </button>
            </div>
            {err && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
                {err}
              </p>
            )}
            <div className="space-y-3">
              <FormField label="Ism familiya">
              <input
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                placeholder="Ism familiya"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>
              <FormField label="Telefon">
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="Telefon"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>
              <FormField label="Vakansiya">
              <select
                value={form.vacancy_id}
                onChange={(e) => setForm({ ...form, vacancy_id: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                <option value="">Vakansiya tanlanmagan</option>
                {vacancies.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.title}
                  </option>
                ))}
              </select>
              </FormField>
              {/* Vakansiya ochilmagan bo'lsa ham QAYSI ISHGA kelgani
                  bilinib tursin (2026-08-15). Ustoz bo'lsa — fani. */}
              <FormField label="Lavozim">
              <select
                value={form.position}
                onChange={(e) => setForm({ ...form, position: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                <option value="">Lavozim tanlanmagan</option>
                {APPLY_POSITIONS.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.label}
                  </option>
                ))}
              </select>
              </FormField>
              {form.position === "teacher" && (
                <>
                  <FormField label="Qaysi fandan?">
                  <input
                    value={form.subject}
                    onChange={(e) =>
                      setForm({ ...form, subject: e.target.value })
                    }
                    placeholder="Qaysi fandan? (Ingliz tili, Matematika…)"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  />
                  </FormField>
                  <FormField label="Qancha vaqt ustoz bo'lib ishlagan? (yil)">
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    value={form.experience_years}
                    onChange={(e) =>
                      setForm({ ...form, experience_years: e.target.value })
                    }
                    placeholder="Qancha vaqt ustoz bo'lib ishlagan? (yil)"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  />
                  </FormField>
                </>
              )}

              {/* ARIZA SAVOLLARI — jonyos.uz/apply dagi bilan bir xil
                  (2026-08-15). Qo'lda kiritilganda ham shu ma'lumot
                  yig'ilsin, keyin "bilmadik" degan gap bo'lmasin. */}
              <div className="pt-1 border-t border-slate-100">
                <p className="text-xs font-medium text-slate-500 pt-2 pb-1">
                  Ariza savollari
                  <span className="font-normal text-slate-400">
                    {" "}
                    — havola orqali so'raladiganlar bilan bir xil
                  </span>
                </p>
              </div>
              <FormField label="Yashash manzili">
              <input
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="Yashash manzili"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Tug'ilgan sana">
                <input
                  value={form.birth_date}
                  onChange={(e) =>
                    setForm({ ...form, birth_date: e.target.value })
                  }
                  placeholder="Tug'ilgan sana"
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
                </FormField>
                <FormField label="Oilaviy holati">
                <select
                  value={form.marital}
                  onChange={(e) =>
                    setForm({ ...form, marital: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Oilaviy holati</option>
                  {APPLY_MARITAL.map((m) => (
                    <option key={m.key} value={m.key}>
                      {m.label}
                    </option>
                  ))}
                </select>
                </FormField>
              </div>
              <FormField label="Ma'lumoti">
              <input
                value={form.education}
                onChange={(e) =>
                  setForm({ ...form, education: e.target.value })
                }
                placeholder="Ma'lumoti (maktab raqami yoki bitirgan joyi)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>
              <FormField label="Avvalgi ish joylari">
              <textarea
                value={form.workplaces}
                onChange={(e) =>
                  setForm({ ...form, workplaces: e.target.value })
                }
                rows={2}
                placeholder="Avvalgi ish joylari (lavozim, qancha vaqt)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>
              <FormField label="Ijtimoiy tarmoqlar">
              <input
                value={form.socials}
                onChange={(e) => setForm({ ...form, socials: e.target.value })}
                placeholder="Ijtimoiy tarmoqlar (Instagram, Telegram…)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>
              <FormField label="Qancha vaqt ishlamoqchi?">
              <select
                value={form.work_duration}
                onChange={(e) =>
                  setForm({ ...form, work_duration: e.target.value })
                }
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                <option value="">Qancha vaqt ishlamoqchi?</option>
                {APPLY_WORK_DURATIONS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              </FormField>
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Bosqich">
                <select
                  value={form.stage}
                  onChange={(e) => setForm({ ...form, stage: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {CANDIDATE_STAGES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
                </FormField>
                <FormField label="Manba">
                <select
                  value={form.source}
                  onChange={(e) => setForm({ ...form, source: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {CANDIDATE_SOURCES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
                </FormField>
              </div>
              <FormField label="Filial">
              <select
                value={form.branch_id}
                onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                <option value="">Filial tanlanmagan</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
              </FormField>
              <FormField label="Izoh">
              <textarea
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
                placeholder="Izoh"
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              </FormField>

              {/* Fayllar faqat SAQLANGAN nomzodga biriktiriladi -
                  yangi nomzodda hali ID yo'q. */}
              {editing ? (
                <div className="pt-3 border-t border-slate-100">
                  <p className="text-sm font-medium text-slate-700 mb-2">
                    Rasm va hujjatlar
                  </p>
                  <Attachments
                    entity="candidate"
                    entityId={editing.id}
                    kinds={[
                      { key: "photo", label: "Rasm" },
                      { key: "certificate", label: "Sertifikat" },
                      { key: "resume", label: "Rezyume" },
                      { key: "document", label: "Hujjat" },
                    ]}
                  />
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  Rasm va sertifikat nomzod saqlangandan keyin biriktiriladi.
                </p>
              )}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                onClick={() => save()}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
              >
                Saqlash
              </button>
              <button
                onClick={() => setModal(false)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
              >
                Bekor
              </button>
            </div>
          </div>
        </div>
      )}
      {dupRows && (
        <DuplicateCandidateDialog
          rows={dupRows}
          onOpen={(cid) => {
            setDupRows(null);
            setModal(false);
            setCard(cid);
          }}
          onForce={() => save(true)}
          onClose={() => setDupRows(null)}
        />
      )}
    </div>
  );
}

// ------------------------------------------------------- Vakansiyalar
const emptyVac = {
  title: "",
  role: "",
  branch_id: "" as string | number,
  headcount: 1,
  status: "open",
  salary_from: "",
  salary_to: "",
  description: "",
};

function VacanciesTab({ branches }: { branches: Branch[] }) {
  const [rows, setRows] = useState<Vacancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Vacancy | null>(null);
  const [form, setForm] = useState({ ...emptyVac });
  const [err, setErr] = useState("");

  const load = () => {
    setLoading(true);
    api.get<Vacancy[]>("/vacancies").then(setRows).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const open = (v?: Vacancy) => {
    setErr("");
    if (v) {
      setEditing(v);
      setForm({
        title: v.title,
        role: v.role ?? "",
        branch_id: v.branch_id ?? "",
        headcount: v.headcount,
        status: v.status,
        salary_from: v.salary_from ? String(v.salary_from) : "",
        salary_to: v.salary_to ? String(v.salary_to) : "",
        description: v.description ?? "",
      });
    } else {
      setEditing(null);
      setForm({ ...emptyVac });
    }
    setModal(true);
  };

  const save = async () => {
    if (!form.title.trim()) {
      setErr("Lavozim nomi kiritilishi shart");
      return;
    }
    const body = {
      title: form.title.trim(),
      role: form.role || null,
      branch_id: form.branch_id ? Number(form.branch_id) : null,
      headcount: Number(form.headcount) || 1,
      status: form.status,
      salary_from: form.salary_from ? Number(form.salary_from) : null,
      salary_to: form.salary_to ? Number(form.salary_to) : null,
      description: form.description || null,
    };
    try {
      if (editing) await api.put(`/vacancies/${editing.id}`, body);
      else await api.post("/vacancies", body);
      setModal(false);
      load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const remove = async (v: Vacancy) => {
    if (!confirm(`"${v.title}" o'chirilsinmi?`)) return;
    try {
      await api.delete(`/vacancies/${v.id}`);
      load();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-slate-500">{rows.length} ta vakansiya</span>
        <div className="flex-1" />
        <button
          onClick={() => open()}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={15} /> Vakansiya
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Vakansiya yo'q. Odam kerak bo'lsa shu yerga yozib qo'ying — nomzodlar
          shu vakansiyaga biriktiriladi.
        </p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {rows.map((v) => {
            const st = VACANCY_STATUSES.find((s) => s.key === v.status);
            const toneCls =
              st?.color === "emerald"
                ? "bg-emerald-50 text-emerald-700"
                : st?.color === "amber"
                  ? "bg-amber-50 text-amber-700"
                  : "bg-slate-100 text-slate-500";
            return (
              <div
                key={v.id}
                className="bg-white rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <p className="font-medium text-slate-800">{v.title}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${toneCls}`}>
                    {vacancyStatusLabel(v.status)}
                  </span>
                </div>
                <div className="space-y-1 text-xs text-slate-500">
                  {v.role && <p>Rol: {roleLabel(v.role)}</p>}
                  <p>Filial: {v.branch || "—"}</p>
                  <p>
                    Kerak: {v.headcount} ta · Olindi:{" "}
                    <span className="text-emerald-600 font-medium">
                      {v.hired_count}
                    </span>
                  </p>
                  {(v.salary_from || v.salary_to) && (
                    <p>
                      Oylik:{" "}
                      {v.salary_from ? formatSom(v.salary_from) : "…"}
                      {v.salary_to ? ` – ${formatSom(v.salary_to)}` : ""}
                    </p>
                  )}
                </div>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                  <span className="text-xs text-slate-500">
                    {v.candidate_count} nomzod
                  </span>
                  <div>
                    <button
                      onClick={() => open(v)}
                      className="p-1.5 text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => remove(v)}
                      className="p-1.5 text-slate-400 hover:text-red-600"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {modal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">
                {editing ? "Vakansiyani tahrirlash" : "Yangi vakansiya"}
              </h3>
              <button onClick={() => setModal(false)} className="text-slate-400">
                <X size={18} />
              </button>
            </div>
            {err && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
                {err}
              </p>
            )}
            <div className="space-y-3">
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Lavozim nomi (masalan: Ingliz tili ustozi)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Rol tanlanmagan</option>
                  {ALL_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {roleLabel(r)}
                    </option>
                  ))}
                </select>
                <select
                  value={form.branch_id}
                  onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Filial tanlanmagan</option>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-500">Nechta odam</label>
                  <input
                    type="number"
                    min={1}
                    value={form.headcount}
                    onChange={(e) =>
                      setForm({ ...form, headcount: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-500">Holati</label>
                  <select
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  >
                    {VACANCY_STATUSES.map((s) => (
                      <option key={s.key} value={s.key}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  value={form.salary_from}
                  onChange={(e) => setForm({ ...form, salary_from: e.target.value })}
                  placeholder="Oylik (dan)"
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
                <input
                  type="number"
                  value={form.salary_to}
                  onChange={(e) => setForm({ ...form, salary_to: e.target.value })}
                  placeholder="Oylik (gacha)"
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
              </div>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Talablar / izoh"
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
            <div className="flex gap-2 mt-5">
              <button
                onClick={save}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
              >
                Saqlash
              </button>
              <button
                onClick={() => setModal(false)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
              >
                Bekor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Sahifa
export default function Hr() {
  const { user } = useAuth();
  const [spHr, setSpHr] = useSearchParams();
  const _hrTab = spHr.get("tab");
  const [tab, setTab] = useState<Tab>(
    _hrTab && TABS.some((t) => t.key === _hrTab)
      ? (_hrTab as Tab) : "overview");
  const [branches, setBranches] = useState<Branch[]>([]);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  if (!can(user?.role, HR_CANDIDATE_VIEW)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  /* O'quv bo'limi rahbariga HR'ning hammasi kerak emas — u faqat
     ustoz nomzodini ko'rib, sinov darsini baholaydi (2026-08-16).
     Shuning uchun unga faqat ikkita tab ochiladi. */
  const fullHr = can(user?.role, HR_ACCESS);
  // Jarima ballari faqat ball ayira oladiganlarga (filial rahbari emas)
  const canPenalize = can(user?.role, EXAMINER_PENALTY_SET)
    || can(user?.role, SUPPORT_PENALTY_SET);
  const visibleTabs = fullHr
    ? TABS.filter((t) => (t.key !== "penalty" || canPenalize)
        && (t.key !== "blacklist" || can(user?.role, BLACKLIST_VIEW)))
    : TABS.filter((t) => ["candidates", "calendar", "rubric"]
        .includes(t.key));
  const activeTab = visibleTabs.some((t) => t.key === tab)
    ? tab
    : visibleTabs[0].key;
  const groups = groupsFor(visibleTabs);
  const activeGroup = groups.find((g) =>
    g.items.some((t) => t.key === activeTab)) ?? groups[0];
  // Tanlangan tab manzilda turadi — sahifa yangilansa yoki havola
  // yuborilsa o'sha joy ochiladi
  const pick = (t: Tab) => {
    setTab(t);
    const sp = new URLSearchParams(spHr);
    sp.set("tab", t);
    setSpHr(sp, { replace: true });
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Briefcase size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">HR</h1>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Ishga olish, xodimlar, o'qitish va sifat — bir joyda
      </p>

      {groups.length > 1 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 mb-3">
          {groups.map((g) => {
            const on = g.key === activeGroup.key;
            const Icon = g.icon;
            return (
              <button
                key={g.key}
                onClick={() => pick(g.items[0].key)}
                className={`text-left rounded-xl border px-3 py-2.5 transition ${
                  on
                    ? "border-brand-400 bg-brand-50 shadow-sm"
                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                }`}
              >
                <span className={`flex items-center gap-2 text-sm font-semibold ${
                  on ? "text-brand-700" : "text-slate-800"}`}>
                  <Icon size={16} className={on ? "text-brand-600" : "text-slate-400"} />
                  {g.label}
                  <span className={`ml-auto text-[11px] font-medium rounded-full px-1.5 ${
                    on ? "bg-brand-100 text-brand-700" : "bg-slate-100 text-slate-500"}`}>
                    {g.items.length}
                  </span>
                </span>
                {g.hint && (
                  <span className="hidden sm:block text-[11px] text-slate-500 mt-0.5 truncate">
                    {g.hint}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      <div className="flex gap-1 border-b border-slate-200 mb-5 overflow-x-auto">
        {activeGroup.items.map((t) => (
          <button
            key={t.key}
            onClick={() => pick(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition ${
              activeTab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && <HrOverviewTab />}
      {activeTab === "ats" && <AtsBoard />}
      {activeTab === "lifecycle" && <HrLifecycleTab />}
      {activeTab === "funnel" && <FunnelTab />}
      {activeTab === "workforce" && <WorkforceTab />}
      {activeTab === "requests" && <StaffRequestsTab />}
      {activeTab === "hrvacancies" && <HrVacanciesTab />}
      {activeTab === "candidates" && <CandidatesTab branches={branches} />}
      {activeTab === "vacancies" && <VacanciesTab branches={branches} />}
      {activeTab === "staff" && <StaffTab />}
      {activeTab === "calendar" && <HrCalendar />}
      {activeTab === "rubric" && <ObservationsTab />}
      {activeTab === "dates" && <StaffDatesTab />}
      {activeTab === "attendance" && <AttendanceTab />}
      {activeTab === "nps" && <NpsTab />}
      {activeTab === "library" && <LibraryTab />}
      {activeTab === "checklist" && <ChecklistTab />}
      {activeTab === "examiners" && <ExaminerStatusTab />}
      {activeTab === "payroll" && <PayrollTab only={["examiner", "support"]} />}
      {activeTab === "onbsteps" && <OnboardingStepsTab />}
      {activeTab === "solo" && <SoloSupportTab />}
      {activeTab === "exited" && <ExitedStaffTab />}
      {activeTab === "drill" && <DrillAdminTab />}
      {activeTab === "penalty" && <PenaltyPointsTab />}
      {activeTab === "blacklist" && <HrBlacklistTab />}
    </div>
  );
}

// ---------------------------------------------- HR kutubxonasi ----

/** Onboarding kutubxonasi: video, kitob va fayllar.
 *
 *  Yangi xodim ishga kirganda ko'rishi shart bo'lgan narsalar shu
 *  yerda turadi. HR kim qancha ko'rganini ko'radi va "topshirdi" deb
 *  belgilaydi — daraja ko'tarishda shu ro'yxat mezonlardan biri. */
export function LibraryTab() {
  const [data, setData] = useState<LibraryList | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<LibraryItem | null>(null);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<LibraryItem | null>(null);
  const [showHidden, setShowHidden] = useState(false);
  const [err, setErr] = useState("");

  const load = () => {
    setLoading(true);
    api
      .get<LibraryList>("/library")
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  async function remove(it: LibraryItem) {
    if (!confirm(`"${it.title}" o'chirilsinmi?`)) return;
    try {
      await api.delete(`/library/${it.id}`);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (!data) return null;

  const visibleItems = data.items.filter(it => showHidden ? !it.active : !!it.active);
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <p className="text-sm text-slate-500">
          {visibleItems.length} ta material
        </p>
        <label className="text-sm flex gap-2"><input type="checkbox" checked={showHidden} onChange={e => setShowHidden(e.target.checked)} /> Yashirilgan materiallar</label>
        <div className="flex-1" />
        {data.can_manage && (
          <button
            onClick={() => setAdding(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-sm font-medium"
          >
            <Plus size={16} /> Material qo'shish
          </button>
        )}
      </div>

      {err && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
          {err}
        </p>
      )}

      {visibleItems.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali material yo'q. "Material qo'shish" tugmasidan onboarding
          videosi yoki kitobini qo'ying.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2.5">Material</th>
                <th className="text-left w-24">Turi</th>
                <th className="text-left w-40">Kimga</th>
                <th className="text-right w-28">Ko'rgan</th>
                <th className="text-right w-28">Topshirgan</th>
                <th className="w-24"></th>
              </tr>
            </thead>
            <tbody>
              {visibleItems.map((it) => (
                <tr key={it.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => setOpen(it)}
                      className="text-slate-800 hover:text-brand-700 font-medium text-left"
                    >
                      {it.title}
                    </button>
                    {it.required && (
                      <span className="ml-2 text-[10px] uppercase tracking-wide bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded">
                        majburiy
                      </span>
                    )}
                    {!it.active && data.can_manage && <button className="text-xs text-brand-700 mr-2" onClick={async () => { try { await api.put(`/library/${it.id}`, {active: true}); load(); } catch (e) { setErr(e instanceof Error ? e.message : "Xatolik"); } }}>Faollashtirish</button>}
                    {!it.active && (
                      <span className="ml-2 text-[10px] uppercase tracking-wide bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                        yopiq
                      </span>
                    )}
                    {it.description && (
                      <p className="text-xs text-slate-400 mt-0.5">
                        {it.description}
                      </p>
                    )}
                  </td>
                  <td className="text-slate-500">
                    {it.kind_label}
                    {it.minutes ? ` · ${it.minutes} daq` : ""}
                  </td>
                  <td className="text-xs text-slate-500">
                    {it.target_roles.length
                      ? it.target_roles
                          .map((r) =>
                            data.roles.find((x) => x.key === r)?.label || r
                          )
                          .join(", ")
                      : "hammaga"}
                  </td>
                  <td className="text-right text-slate-600">
                    {it.watchers ?? 0}
                    {it.avg_percent ? (
                      <span className="text-xs text-slate-400">
                        {" "}
                        · {it.avg_percent}%
                      </span>
                    ) : null}
                  </td>
                  <td className="text-right">
                    <span
                      className={
                        it.done ? "text-emerald-600 font-medium" : "text-slate-400"
                      }
                    >
                      {it.done ?? 0}
                    </span>
                  </td>
                  <td className="pr-4 text-right">
                    <button
                      onClick={() => setOpen(it)}
                      className="text-xs text-brand-600 hover:underline mr-2"
                    >
                      Kimlar
                    </button>
                    {data.can_manage && (
                      <button
                        onClick={() => setEditing(it)}
                        className="text-slate-400 hover:text-brand-600 mr-2"
                        title="Tahrirlash"
                      >
                        <Pencil size={14} />
                      </button>
                    )}
                    <button
                      onClick={() => remove(it)}
                      className="text-slate-300 hover:text-red-500"
                      title="O'chirish"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {adding && (
        <LibraryForm
          roles={data.roles}
          kinds={data.kinds}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            load();
          }}
        />
      )}
      {editing && (
        <LibraryForm
          roles={data.roles}
          kinds={data.kinds}
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
      {open && (
        <LibraryPeopleModal
          item={open}
          onClose={() => setOpen(null)}
          onChanged={load}
        />
      )}
    </div>
  );
}

function LibraryForm({
  roles: roleList, kinds, initial, onClose, onSaved,
}: {
  roles: { key: string; label: string }[];
  kinds: { key: string; label: string }[];
  /** Tahrirlash rejimi (2026-08-20, Jahongir: "majburiy kitob
   *  videolarni qo'lda o'zgartiradigan qilib bering"). */
  initial?: LibraryItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [kind, setKind] = useState(initial?.kind ?? "video");
  const [url, setUrl] = useState(initial?.url ?? "");
  const [minutes, setMinutes] = useState(
    initial?.minutes ? String(initial.minutes) : "");
  const [desc, setDesc] = useState(initial?.description ?? "");
  const [required, setRequired] = useState(initial?.required ?? true);
  const [target, setTarget] = useState<string[]>(
    initial?.target_roles ?? []);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function save() {
    setBusy(true);
    setErr("");
    try {
      const body = {
        title,
        kind,
        url,
        minutes: Number(minutes) || 0,
        description: desc,
        required,
        target_roles: target,
      };
      if (initial) await api.put(`/library/${initial.id}`, body);
      else await api.post("/library", body);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {initial ? "Materialni tahrirlash" : "Yangi material"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Nomi *
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Onboarding: Jony Academy qoidalari"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              autoFocus
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Turi
              </label>
              <select
                value={kind}
                onChange={(e) => setKind(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                {kinds.map((k) => (
                  <option key={k.key} value={k.key}>
                    {k.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Davomiyligi (daqiqa)
              </label>
              <input
                value={minutes}
                onChange={(e) => setMinutes(e.target.value.replace(/\D/g, ""))}
                placeholder="25"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              {kind === "book" ? "Havola (ixtiyoriy)" : "Havola *"}
            </label>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://youtu.be/... yoki Google Drive havolasi"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <p className="text-xs text-slate-400 mt-1">
              {kind === "book" ? "Qog'oz kitob uchun havola shart emas."
                : "Video uchun YouTube yoki Google Drive havolasini kiriting."}
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Izoh
            </label>
            <input
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Kimga tegishli (bo'sh qolsa — hammaga)
            </label>
            <div className="flex flex-wrap gap-1.5">
              {roleList.map((r) => {
                const on = target.includes(r.key);
                return (
                  <button
                    key={r.key}
                    onClick={() =>
                      setTarget((t) =>
                        on ? t.filter((x) => x !== r.key) : [...t, r.key]
                      )
                    }
                    className={`px-2.5 py-1 rounded-full text-xs border transition ${
                      on
                        ? "bg-brand-600 border-brand-600 text-white"
                        : "bg-white border-slate-200 text-slate-600 hover:border-brand-300"
                    }`}
                  >
                    {r.label}
                  </button>
                );
              })}
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={required}
              onChange={(e) => setRequired(e.target.checked)}
              className="w-4 h-4 accent-brand-600"
            />
            Majburiy — daraja ko'tarishda hisobga olinadi
          </label>
          {err && <p className="text-sm text-red-600">{err}</p>}
        </div>
        <div className="flex gap-2 mt-5">
          <button
            onClick={save}
            disabled={busy || !title.trim() || (kind !== "book" && !url.trim() && !initial?.attachment_id)}
            className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-40"
          >
            Saqlash
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor
          </button>
        </div>
      </div>
    </div>
  );
}

function LibraryPeopleModal({
  item, onClose, onChanged,
}: {
  item: LibraryItem;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [data, setData] = useState<LibraryPeople | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [q, setQ] = useState("");

  const load = () => {
    api
      .get<LibraryPeople>(`/library/${item.id}/people`)
      .then(setData)
      .catch(() => setData(null));
  };
  useEffect(load, [item.id]);

  async function mark(uid: number, passed: boolean) {
    setBusy(uid);
    try {
      await api.put(`/library/${item.id}/people/${uid}`, { passed });
      load();
      onChanged();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  const rows = (data?.rows || []).filter((r) =>
    r.name.toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between mb-1">
          <div>
            <h2 className="font-semibold text-slate-900">{item.title}</h2>
            <p className="text-xs text-slate-500">
              {item.kind_label}
              {item.minutes ? ` · ${item.minutes} daqiqa` : ""}
              {data ? ` · ${data.done}/${data.total} topshirgan` : ""}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-brand-600 hover:underline break-all"
          >
            {item.url}
          </a>
        )}

        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Xodimni qidirish..."
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mt-4 mb-3"
        />

        {!data ? (
          <p className="text-sm text-slate-400 py-6">Yuklanmoqda...</p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-slate-400 py-6 text-center">
            Xodim topilmadi
          </p>
        ) : (
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="text-left px-3 py-2">Xodim</th>
                  <th className="text-left w-36">Lavozim</th>
                  <th className="text-right w-28">Ko'rdi</th>
                  <th className="text-right w-32">Topshirdi</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.user_id} className="border-t border-slate-100">
                    <td className="px-3 py-2 text-slate-800">{r.name}</td>
                    <td className="text-xs text-slate-500">{r.role}</td>
                    <td className="text-right">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-14 h-1.5 rounded-full bg-slate-100 overflow-hidden inline-block">
                          <span
                            className="h-full bg-brand-500 block"
                            style={{ width: `${r.percent}%` }}
                          />
                        </span>
                        <span className="text-xs text-slate-500 w-9 text-right">
                          {r.percent}%
                        </span>
                      </span>
                    </td>
                    <td className="text-right pr-3">
                      <button
                        onClick={() => mark(r.user_id, !r.passed)}
                        disabled={busy === r.user_id}
                        title={
                          r.passed
                            ? `${r.passed_by || ""} ${r.passed_at || ""}`
                            : "Topshirdi deb belgilash"
                        }
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition disabled:opacity-40 ${
                          r.passed
                            ? "bg-emerald-600 border-emerald-600 text-white"
                            : "bg-white border-slate-200 text-slate-500 hover:border-emerald-300"
                        }`}
                      >
                        {r.passed ? "topshirdi" : "belgilash"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}


/**
 * ONBOARDING BOSQICHLARI BOSHQARUVI (2026-08-20).
 *
 * Jahongir: "hamma xodimga xar xilda onboarding". Har bosqichga
 * qaysi rollarga tegishliligi belgilanadi - bo'sh qoldirilsa
 * hammaga. Yangi xodim kartasidagi checklist shu ro'yxatdan rolga
 * qarab yig'iladi. O'chirish - faolsizlantirish: eski xodimlarning
 * bajarilgan belgilari yo'qolmaydi.
 */
function OnboardingStepsTab() {
  type Step = { id: number; key: string; label: string;
    target_roles: string[]; order_no: number; active: boolean };
  const [d, setD] = useState<{ rows: Step[];
    roles: { key: string; label: string }[] } | null>(null);
  const [err, setErr] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [newRoles, setNewRoles] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [editRoles, setEditRoles] = useState<Step | null>(null);

  const load = () => {
    api.get<{ rows: Step[]; roles: { key: string; label: string }[] }>(
      "/onboarding-steps")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  async function run(fn: () => Promise<unknown>) {
    setBusy(true); setErr("");
    try { await fn(); load(); }
    catch (e) { setErr(e instanceof Error ? e.message : "Xatolik"); }
    finally { setBusy(false); }
  }

  if (err && !d) return <p className="text-sm text-red-600">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  const roleLbl = (k: string) =>
    d.roles.find((r) => r.key === k)?.label || k;

  return (
    <div className="max-w-3xl">
      <p className="text-sm text-slate-500 mb-4">
        Yangi xodim checklisti shu yerdan boshqariladi. "Kimga" bo'sh
        bo'lsa — bosqich hammaga tegishli. O'chirilgan bosqich eski
        xodimlarning tarixini buzmaydi.
      </p>
      {err && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
          {err}
        </p>
      )}

      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        {d.rows.map((r) => (
          <div key={r.id} className={`px-4 py-3 ${r.active ? "" : "opacity-50"}`}>
            <div className="flex flex-wrap items-center gap-2">
              <input
                defaultValue={r.label}
                onBlur={(e) => {
                  const v = e.target.value.trim();
                  if (v && v !== r.label)
                    run(() => api.put(`/onboarding-steps/${r.id}`, { label: v }));
                }}
                className="flex-1 min-w-[220px] text-sm text-slate-800 font-medium bg-transparent border border-transparent hover:border-slate-200 focus:border-brand-400 rounded-lg px-2 py-1 outline-none"
              />
              <button
                onClick={() => setEditRoles(r)}
                className="text-xs px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:border-brand-300"
              >
                {r.target_roles.length
                  ? r.target_roles.map(roleLbl).join(", ")
                  : "hammaga"}
              </button>
              <input
                type="number"
                defaultValue={r.order_no}
                title="Tartib raqami"
                onBlur={(e) => {
                  const v = Number(e.target.value) || 0;
                  if (v !== r.order_no)
                    run(() => api.put(`/onboarding-steps/${r.id}`, { order_no: v }));
                }}
                className="w-16 text-sm text-slate-500 border border-slate-200 rounded-lg px-2 py-1"
              />
              {r.active ? (
                <button
                  onClick={() => run(() => api.delete(`/onboarding-steps/${r.id}`))}
                  disabled={busy}
                  className="text-slate-300 hover:text-red-500"
                  title="Faolsizlantirish"
                >
                  <Trash2 size={14} />
                </button>
              ) : (
                <button
                  onClick={() => run(() => api.put(`/onboarding-steps/${r.id}`, { active: true }))}
                  disabled={busy}
                  className="text-xs text-emerald-600 hover:underline"
                >
                  Tiklash
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 bg-white rounded-xl border border-slate-200 p-4">
        <p className="text-sm font-medium text-slate-700 mb-2">
          Yangi bosqich
        </p>
        <input
          value={newLabel}
          onChange={(e) => setNewLabel(e.target.value)}
          placeholder="Masalan: Kompaniya qadriyatlari videosi ko'rildi"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-2"
        />
        <div className="flex flex-wrap gap-1.5 mb-3">
          {d.roles.map((ro) => (
            <button
              key={ro.key}
              onClick={() =>
                setNewRoles((v) =>
                  v.includes(ro.key)
                    ? v.filter((x) => x !== ro.key)
                    : [...v, ro.key])}
              className={`text-xs px-2.5 py-1 rounded-lg border ${
                newRoles.includes(ro.key)
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500"
              }`}
            >
              {ro.label}
            </button>
          ))}
        </div>
        <button
          onClick={() =>
            run(async () => {
              await api.post("/onboarding-steps", {
                label: newLabel, target_roles: newRoles,
                order_no: d.rows.length,
              });
              setNewLabel(""); setNewRoles([]);
            })}
          disabled={busy || !newLabel.trim()}
          className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          Qo'shish
        </button>
        <p className="text-[11px] text-slate-400 mt-2">
          Rol tanlanmasa — hammaga tegishli bo'ladi.
        </p>
      </div>

      {editRoles && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4"
             onClick={() => setEditRoles(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-5"
               onClick={(e) => e.stopPropagation()}>
            <p className="font-semibold text-slate-900 mb-1">
              "{editRoles.label}" — kimga tegishli?
            </p>
            <p className="text-xs text-slate-400 mb-3">
              Hech biri tanlanmasa — hammaga.
            </p>
            <RolePicker
              all={d.roles}
              value={editRoles.target_roles}
              onSave={(v) =>
                run(async () => {
                  await api.put(`/onboarding-steps/${editRoles.id}`,
                    { target_roles: v });
                  setEditRoles(null);
                })}
              onClose={() => setEditRoles(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function RolePicker({ all, value, onSave, onClose }: {
  all: { key: string; label: string }[];
  value: string[];
  onSave: (v: string[]) => void;
  onClose: () => void;
}) {
  const [sel, setSel] = useState<string[]>(value);
  return (
    <>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {all.map((ro) => (
          <button
            key={ro.key}
            onClick={() =>
              setSel((v) => v.includes(ro.key)
                ? v.filter((x) => x !== ro.key) : [...v, ro.key])}
            className={`text-xs px-2.5 py-1 rounded-lg border ${
              sel.includes(ro.key)
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500"
            }`}
          >
            {ro.label}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <button onClick={onClose}
                className="flex-1 py-2 rounded-lg border border-slate-200 text-sm text-slate-600">
          Bekor
        </button>
        <button onClick={() => onSave(sel)}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium">
          Saqlash
        </button>
      </div>
    </>
  );
}

/** YAKKA SUPPORT (2026-09-23, Jahongir: "hr qo'sha olsin u
 *  o'quvchilarni faqat").
 *
 *  HR o'quvchi kartasini ochmaydi — bu yerda faqat ism, guruh va
 *  biriktirma ko'rinadi. To'lov, davomat, imtihon ma'lumotlari HR ga
 *  berilmaydi. Ustoz ham o'z guruhidagi o'quvchini karta orqali
 *  biriktiraveradi — ikkalasi bitta ro'yxatga tushadi. */
const SOLO_DAYS: [string, string][] = [
  ["mon", "Du"], ["tue", "Se"], ["wed", "Ch"], ["thu", "Pa"],
  ["fri", "Ju"], ["sat", "Sh"], ["sun", "Ya"],
];

type SoloAssign = {
  id: number;
  student_id: number;
  student: string;
  group: string | null;
  support: string | null;
  days: string | null;
  start: string | null;
  end: string | null;
  note: string | null;
  created_by: string | null;
  done: number;
};

function SoloSupportTab() {
  const [d, setD] = useState<{
    rows: SoloAssign[];
    supports: { id: number; name: string }[];
    hint: string;
  } | null>(null);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [found, setFound] = useState<
    { id: number; name: string; group: string | null }[]
  >([]);
  const [pick, setPick] = useState<{ id: number; name: string } | null>(null);
  const [f, setF] = useState({
    user_id: "", days: [] as string[], start: "14:00", end: "15:00",
    note: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api.fresh<typeof d>("/support/solo").then(setD);
  }, []);
  useEffect(load, [load]);

  useEffect(() => {
    if (q.trim().length < 2) {
      setFound([]);
      return;
    }
    const t = setTimeout(() => {
      api
        .get<{ rows: { id: number; name: string; group: string | null }[] }>(
          `/support/solo/students?q=${encodeURIComponent(q.trim())}`
        )
        .then((r) => setFound(r.rows))
        .catch(() => setFound([]));
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  const save = async () => {
    if (!pick) return;
    setBusy(true);
    setErr("");
    try {
      await api.post(`/students/${pick.id}/support`, {
        user_id: Number(f.user_id),
        days: f.days.join(","),
        start: f.start,
        end: f.end,
        note: f.note,
      });
      setOpen(false);
      setPick(null);
      setQ("");
      setF({ ...f, note: "", days: [] });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Saqlanmadi");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="flex items-start gap-3 mb-4">
        <p className="text-sm text-slate-500 flex-1">{d.hint}</p>
        {!open && (
          <button
            onClick={() => setOpen(true)}
            className="rounded-lg bg-brand-600 text-white text-sm px-4 py-2 whitespace-nowrap"
          >
            O'quvchi biriktirish
          </button>
        )}
      </div>

      {open && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4 space-y-3">
          {pick ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-900">
                {pick.name}
              </span>
              <button
                onClick={() => setPick(null)}
                className="text-xs text-slate-500 underline decoration-dotted"
              >
                boshqasi
              </button>
            </div>
          ) : (
            <div>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="O'quvchi ismini yozing"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              {found.length > 0 && (
                <div className="border border-slate-200 rounded-lg mt-1 max-h-56 overflow-y-auto">
                  {found.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setPick({ id: s.id, name: s.name })}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50"
                    >
                      {s.name}
                      <span className="text-slate-400"> · {s.group || "guruhsiz"}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <select
            value={f.user_id}
            onChange={(e) => setF({ ...f, user_id: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Support tanlang</option>
            {d.supports.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>

          <div className="flex flex-wrap gap-1.5">
            {SOLO_DAYS.map(([k, lbl]) => (
              <button
                key={k}
                onClick={() =>
                  setF({
                    ...f,
                    days: f.days.includes(k)
                      ? f.days.filter((x) => x !== k)
                      : [...f.days, k],
                  })
                }
                className={`px-3 py-1.5 rounded-lg text-sm border ${
                  f.days.includes(k)
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-slate-600 border-slate-300"
                }`}
              >
                {lbl}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="time" value={f.start}
              onChange={(e) => setF({ ...f, start: e.target.value })}
              className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
            />
            <span className="text-slate-400">—</span>
            <input
              type="time" value={f.end}
              onChange={(e) => setF({ ...f, end: e.target.value })}
              className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
            />
          </div>

          <textarea
            value={f.note}
            onChange={(e) => setF({ ...f, note: e.target.value })}
            rows={2}
            placeholder="Nega orqada qolgan? Masalan: Unit 5 dan 40%, grammatikasi zaif"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />

          {err && <p className="text-sm text-rose-600">{err}</p>}

          <div className="flex gap-2">
            <button
              disabled={busy || !pick || !f.user_id || !f.note.trim()}
              onClick={save}
              className="rounded-lg bg-brand-600 text-white text-sm px-4 py-2 disabled:opacity-50"
            >
              Biriktirish
            </button>
            <button
              onClick={() => { setOpen(false); setErr(""); }}
              className="rounded-lg border border-slate-300 text-sm px-4 py-2"
            >
              Bekor
            </button>
          </div>
        </div>
      )}

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Hozircha yakka biriktirma yo'q.
        </p>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">O'quvchi</th>
                <th className="text-left px-3 py-2.5 font-medium">Guruh</th>
                <th className="text-left px-3 py-2.5 font-medium">Support</th>
                <th className="text-left px-3 py-2.5 font-medium">Kun</th>
                <th className="text-right px-3 py-2.5 font-medium">Shu oy</th>
                <th className="px-3 py-2.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.rows.map((r) => (
                <tr key={r.id}>
                  <td className="px-4 py-2.5 text-slate-800">
                    {r.student}
                    {r.note && (
                      <span className="block text-xs text-slate-500">
                        {r.note}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-slate-600">
                    {r.group || "—"}
                  </td>
                  <td className="px-3 py-2.5 text-slate-600">
                    {r.support || "—"}
                  </td>
                  <td className="px-3 py-2.5 text-slate-500 text-xs">
                    {(r.days || "")
                      .split(",")
                      .filter(Boolean)
                      .map((x) => SOLO_DAYS.find((w) => w[0] === x)?.[1] || x)
                      .join(", ") || "—"}
                    {r.start && r.end ? ` ${r.start}-${r.end}` : ""}
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-700">
                    {r.done} ta
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <button
                      onClick={async () => {
                        if (!confirm(`${r.student} biriktirmasi olib tashlansinmi?`))
                          return;
                        await api.delete(
                          `/students/${r.student_id}/support/${r.id}`
                        );
                        load();
                      }}
                      className="text-xs text-rose-600 underline decoration-dotted"
                    >
                      Olib tashlash
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/** KETGANLAR ARXIVI (2026-09-24, Jahongir: "hr ga xodimlar arxivini
 *  ochib ber, ishdan ketgan nega ketgan hammasi bo'lsin").
 *
 *  Ro'yxat ikki manbadan yig'iladi: hisobi yopilgan xodimlar va
 *  hisobsiz ustoz kartalari. Sababi yozilmaganlar sariq bilan
 *  ajratiladi — HR ularni shu yerda to'ldiradi va o'sha sabab HR
 *  hisobotiga ham tushadi. */
type ExitRow = {
  id: number;
  kind: string;
  teacher_id?: number | null;
  full_name: string;
  username: string;
  role_label: string;
  branch: string | null;
  position: string | null;
  phone: string | null;
  exit_type: string;
  exit_label: string;
  exit_reason: string | null;
  exit_date: string | null;
  hired_date: string | null;
  months: number | null;
  reason_key: string | null;
  reason_label: string | null;
  ours: boolean | null;
  exit_notes: string | null;
  would_return: boolean | null;
  has_reason: boolean;
};

type ExitData = {
  rows: ExitRow[];
  total: number;
  groups: { key: string; label: string; hint: string; count: number }[];
  by_reason: { key: string; label: string; ours: boolean; count: number }[];
  reasons: { key: string; label: string; ours: boolean }[];
  no_reason: number;
  ours_percent: number | null;
  this_year: number;
  avg_months: number | null;
  hint: string;
};

const EXIT_TONE: Record<string, string> = {
  green: "bg-emerald-100 text-emerald-700",
  neutral: "bg-slate-100 text-slate-600",
  red: "bg-red-100 text-red-700",
};

function ExitedStaffTab() {
  const [d, setD] = useState<ExitData | null>(null);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [reason, setReason] = useState("");
  const [year, setYear] = useState("");
  const [edit, setEdit] = useState<ExitRow | null>(null);
  // Ishga qaytarish (2026-10-06)
  const [restoring, setRestoring] = useState<ExitRow | null>(null);

  const load = useCallback(() => {
    api.fresh<ExitData>("/archive/staff").then(setD).catch(() => setD(null));
  }, []);
  useEffect(load, [load]);

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  const years = [...new Set(
    d.rows.map((r) => (r.exit_date || "").slice(0, 4)).filter(Boolean)
  )].sort().reverse();

  const rows = d.rows.filter((r) => {
    if (q && !r.full_name.toLowerCase().includes(q.toLowerCase()))
      return false;
    if (type && r.exit_type !== type) return false;
    if (reason === "none" ? r.has_reason : reason && r.reason_key !== reason)
      return false;
    if (year && !(r.exit_date || "").startsWith(year)) return false;
    return true;
  });

  const card = "bg-white border border-slate-200 rounded-xl p-4";

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <div className={card}>
          <p className="text-xs text-slate-500">Jami ketgan</p>
          <p className="text-xl font-semibold text-slate-900">{d.total}</p>
          <p className="text-xs text-slate-400">shu yil {d.this_year} ta</p>
        </div>
        <div className={card}>
          <p className="text-xs text-slate-500">O'rtacha ishlagan</p>
          <p className="text-xl font-semibold text-slate-900">
            {d.avg_months != null ? `${d.avg_months} oy` : "—"}
          </p>
        </div>
        <div className={card}>
          <p className="text-xs text-slate-500">Bizga bog'liq sabab</p>
          <p className="text-xl font-semibold text-slate-900">
            {d.ours_percent != null ? `${d.ours_percent}%` : "—"}
          </p>
          <p className="text-xs text-slate-400">ish haqi, rahbariyat, yuk</p>
        </div>
        <div className={card}>
          <p className="text-xs text-slate-500">Sababi yozilmagan</p>
          <p className={`text-xl font-semibold ${
            d.no_reason ? "text-amber-600" : "text-slate-900"}`}>
            {d.no_reason}
          </p>
        </div>
      </div>

      {d.by_reason.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Nega ketishgan
          </p>
          <div className="space-y-1.5">
            {d.by_reason.map((x) => (
              <div key={x.key} className="flex items-center gap-2 text-sm">
                <span className="w-44 shrink-0 text-slate-600">
                  {x.label}
                </span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full">
                  <div
                    className={`h-2 rounded-full ${
                      x.ours ? "bg-red-400" : "bg-slate-400"}`}
                    style={{
                      width: `${(x.count / d.by_reason[0].count) * 100}%`,
                    }}
                  />
                </div>
                <span className="w-8 text-right text-slate-700">
                  {x.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2 mb-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ism bo'yicha qidirish"
          className="flex-1 min-w-[180px] rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
        >
          <option value="">Qanday ajrashilgan</option>
          {d.groups.map((g) => (
            <option key={g.key} value={g.key}>
              {g.label} ({g.count})
            </option>
          ))}
        </select>
        <select
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
        >
          <option value="">Sabab</option>
          <option value="none">Sababi yozilmagan ({d.no_reason})</option>
          {d.reasons.map((r) => (
            <option key={r.key} value={r.key}>{r.label}</option>
          ))}
        </select>
        <select
          value={year}
          onChange={(e) => setYear(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
        >
          <option value="">Yil</option>
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
              <th className="text-left px-3 py-2.5 font-medium">Lavozim</th>
              <th className="text-left px-3 py-2.5 font-medium">Filial</th>
              <th className="text-left px-3 py-2.5 font-medium">Ishladi</th>
              <th className="text-left px-3 py-2.5 font-medium">Ketdi</th>
              <th className="text-left px-3 py-2.5 font-medium">Nega</th>
              <th className="px-3 py-2.5"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((r) => (
              <tr key={`${r.kind}-${r.id}`}>
                <td className="px-4 py-2.5">
                  <span className="text-slate-800">{r.full_name}</span>
                  <span
                    className={`ml-2 px-1.5 py-0.5 rounded text-[11px] ${
                      EXIT_TONE[r.exit_type] || EXIT_TONE.neutral}`}
                  >
                    {r.exit_label}
                  </span>
                  {r.would_return === false && (
                    <span className="block text-[11px] text-slate-400">
                      qaytib kelmaydi
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-slate-600">
                  {r.position || r.role_label}
                </td>
                <td className="px-3 py-2.5 text-slate-600">
                  {r.branch || "—"}
                </td>
                <td className="px-3 py-2.5 text-slate-600">
                  {r.months != null ? `${r.months} oy` : "—"}
                </td>
                <td className="px-3 py-2.5 text-slate-600">
                  {r.exit_date || "—"}
                </td>
                <td className="px-3 py-2.5">
                  {r.reason_label ? (
                    <span className={r.ours ? "text-red-700" : "text-slate-700"}>
                      {r.reason_label}
                    </span>
                  ) : (
                    <span className="text-amber-600">sababi yozilmagan</span>
                  )}
                  {(r.exit_notes || r.exit_reason) && (
                    <span className="block text-[11px] text-slate-500">
                      {r.exit_notes || r.exit_reason}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right whitespace-nowrap">
                  {r.kind === "user" && (
                    <button
                      onClick={() => setEdit(r)}
                      className="text-xs text-brand-600 underline decoration-dotted"
                    >
                      To'ldirish
                    </button>
                  )}
                  {/* ISHGA QAYTARISH (2026-10-06, Jahongir: "arxivdagi
                      ketgan xodimlarni akkauntlarini tiklash qaytarishni
                      ham qo'shib ber hrga") */}
                  <button
                    onClick={() => setRestoring(r)}
                    className="ml-3 text-xs font-medium text-emerald-700 hover:underline"
                  >
                    Qaytarish
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-slate-400">
                  Bu shart bo'yicha hech kim topilmadi.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-500 mt-3">{d.hint}</p>

      {restoring && (
        <StaffRestoreModal
          row={restoring}
          onClose={() => setRestoring(null)}
          onDone={load}
        />
      )}
      {edit && (
        <ExitEditModal
          row={edit}
          reasons={d.reasons}
          types={d.groups}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function ExitEditModal({
  row, reasons, types, onClose, onSaved,
}: {
  row: ExitRow;
  reasons: { key: string; label: string }[];
  types: { key: string; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    exit_type: row.exit_type || "neutral",
    reason_key: row.reason_key || "",
    exit_notes: row.exit_notes || row.exit_reason || "",
    exit_date: row.exit_date || "",
    would_return: row.would_return,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.put(`/archive/staff/${row.id}`, {
        exit_type: f.exit_type,
        exit_reason: f.exit_notes || null,
        reason_key: f.reason_key || null,
        exit_notes: f.exit_notes || null,
        exit_date: f.exit_date || null,
        would_return: f.would_return,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Saqlanmadi");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">{row.full_name}</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">
            Nega ketdi
          </label>
          <select
            value={f.reason_key}
            onChange={(e) => setF({ ...f, reason_key: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Tanlanmagan</option>
            {reasons.map((r) => (
              <option key={r.key} value={r.key}>{r.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">
            Qanday ajrashildi
          </label>
          <select
            value={f.exit_type}
            onChange={(e) => setF({ ...f, exit_type: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {types.map((t) => (
              <option key={t.key} value={t.key}>{t.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">
            Ketgan sana
          </label>
          <input
            type="date"
            value={f.exit_date}
            onChange={(e) => setF({ ...f, exit_date: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">
            Chiqish suhbati
          </label>
          <textarea
            rows={3}
            value={f.exit_notes}
            onChange={(e) => setF({ ...f, exit_notes: e.target.value })}
            placeholder="O'z so'zlari bilan: nimadan norozi edi, nima yaxshi edi"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Qaytib kelarmidi:</span>
          {[["ha", true], ["yo'q", false]].map(([lbl, val]) => (
            <button
              key={String(val)}
              onClick={() =>
                setF({ ...f, would_return: f.would_return === val ? null : (val as boolean) })
              }
              className={`px-3 py-1 rounded-lg text-xs border ${
                f.would_return === val
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-slate-600 border-slate-300"
              }`}
            >
              {lbl as string}
            </button>
          ))}
        </div>

        {err && <p className="text-sm text-rose-600">{err}</p>}

        <div className="flex gap-2 pt-1">
          <button
            disabled={busy}
            onClick={save}
            className="rounded-lg bg-brand-600 text-white text-sm px-4 py-2 disabled:opacity-50"
          >
            Saqlash
          </button>
          <button
            onClick={onClose}
            className="rounded-lg border border-slate-300 text-sm px-4 py-2"
          >
            Bekor
          </button>
        </div>
      </div>
    </div>
  );
}

/** ADMIN MASHQI (2026-09-25, Jahongir: "hr uchun shu miqdorni
 *  o'zgartirishni qo'shib qo'y yangi bo'lim ochib").
 *
 *  HR har bandning soniyasini va nomini o'zgartiradi, keraksizini
 *  o'chiradi, qaysi filial SINOV ekanini belgilaydi va kim qanday
 *  topshirganini ko'radi. */
type DrillTask = {
  id: number;
  key: string;
  order_no: number;
  title: string;
  hint: string | null;
  seconds: number;
  verify_label: string;
  is_active: boolean;
};

type DrillAttempt = {
  id: number;
  user: string | null;
  status: string;
  started_at: string | null;
  total: number;
  done: number;
  in_time: number;
  spent: number;
  percent: number;
  passed: boolean;
  verdict: string | null;
};

function DrillAdminTab() {
  const [d, setD] = useState<{
    tasks: DrillTask[];
    total_seconds: number;
    pass_percent: number;
    attempts: DrillAttempt[];
    branches: { id: number; name: string; is_test: boolean }[];
    hint: string;
  } | null>(null);
  const [busy, setBusy] = useState(0);

  const load = useCallback(() => {
    api.fresh<typeof d>("/drill/admin").then(setD);
  }, []);
  useEffect(load, [load]);

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  const save = async (t: DrillTask, patch: Record<string, unknown>) => {
    setBusy(t.id);
    try {
      await api.put(`/drill/tasks/${t.id}`, patch);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Saqlanmadi");
    } finally {
      setBusy(0);
    }
  };

  return (
    <div>
      <p className="text-sm text-slate-500 mb-4">{d.hint}</p>

      {/* O'TISH FOIZI (2026-09-25, Jahongir: "60% foiz o'tsa xodimni
          ishga olsa bo'ladi") */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
        <p className="text-sm font-medium text-slate-700 mb-1">
          O'tish foizi
        </p>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={10}
            max={100}
            defaultValue={d.pass_percent}
            onBlur={async (e) => {
              const v = Number(e.target.value);
              if (!v || v === d.pass_percent) return;
              try {
                await api.put("/drill/settings", { pass_percent: v });
                load();
              } catch (er) {
                alert(er instanceof Error ? er.message : "Saqlanmadi");
              }
            }}
            className="w-20 rounded-lg border border-slate-300 px-2 py-1 text-sm text-right"
          />
          <span className="text-sm text-slate-500">
            % dan yuqori bo'lsa — ishga olsa bo'ladi
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1.5">
          Foiz vaqtida bajarilgan vazifalardan chiqadi: vaqtdan oshgani
          ham, o'tkazib yuborilgani ham hisobga olinmaydi.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
        <p className="text-sm font-medium text-slate-700 mb-2">
          Sinov filiali
        </p>
        <div className="flex flex-wrap gap-2">
          {d.branches.map((b) => (
            <button
              key={b.id}
              onClick={async () => {
                await api.put(`/drill/branches/${b.id}`, {
                  is_test: !b.is_test,
                });
                load();
              }}
              className={`px-3 py-1.5 rounded-lg text-sm border ${
                b.is_test
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-slate-600 border-slate-300"
              }`}
            >
              {b.name}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Mashq faqat belgilangan filialda boshlanadi — haqiqiy filialda
          soxta o'quvchi va to'lov paydo bo'lmaydi.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium w-10">#</th>
              <th className="text-left px-3 py-2.5 font-medium">Vazifa</th>
              <th className="text-left px-3 py-2.5 font-medium">Tekshiruv</th>
              <th className="text-right px-3 py-2.5 font-medium">Soniya</th>
              <th className="px-3 py-2.5"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.tasks.map((t) => (
              <tr key={t.id} className={t.is_active ? "" : "opacity-50"}>
                <td className="px-4 py-2.5 text-slate-400">{t.order_no}</td>
                <td className="px-3 py-2.5">
                  <span className="text-slate-800">{t.title}</span>
                  {t.hint && (
                    <span className="block text-[11px] text-slate-400">
                      {t.hint}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-xs text-slate-500">
                  {t.verify_label}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <input
                    type="number"
                    min={5}
                    max={600}
                    defaultValue={t.seconds}
                    disabled={busy === t.id}
                    onBlur={(e) => {
                      const v = Number(e.target.value);
                      if (v && v !== t.seconds) save(t, { seconds: v });
                    }}
                    className="w-20 rounded-lg border border-slate-300 px-2 py-1 text-sm text-right"
                  />
                </td>
                <td className="px-3 py-2.5 text-right">
                  <button
                    onClick={() => save(t, { is_active: !t.is_active })}
                    className="text-xs text-slate-500 underline decoration-dotted"
                  >
                    {t.is_active ? "O'chirish" : "Yoqish"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500 mb-5">
        Jami: {d.tasks.filter((t) => t.is_active).length} ta vazifa ·{" "}
        {Math.round(d.total_seconds / 60)} daqiqa
      </p>

      <p className="text-sm font-medium text-slate-700 mb-2">Urinishlar</p>
      {d.attempts.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hali hech kim topshirmagan.
        </p>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
                <th className="text-left px-3 py-2.5 font-medium">Sana</th>
                <th className="text-right px-3 py-2.5 font-medium">
                  Vaqtida
                </th>
                <th className="text-right px-3 py-2.5 font-medium">
                  Bajardi
                </th>
                <th className="text-right px-3 py-2.5 font-medium">Vaqt</th>
                <th className="text-left px-3 py-2.5 font-medium">Natija</th>
                <th className="text-left px-3 py-2.5 font-medium">Holat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {d.attempts.map((a) => (
                <tr key={a.id}>
                  <td className="px-4 py-2.5 text-slate-800">
                    {a.user || "—"}
                  </td>
                  <td className="px-3 py-2.5 text-slate-500">
                    {a.started_at?.slice(0, 16).replace("T", " ")}
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-700">
                    {a.in_time} / {a.total}
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-600">
                    {a.done}
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-500">
                    {Math.round(a.spent / 60)} daq
                  </td>
                  <td className="px-3 py-2.5">
                    {a.status === "running" ? (
                      <span className="text-slate-400 text-xs">—</span>
                    ) : (
                      <span
                        className={`px-1.5 py-0.5 rounded text-[11px] ${
                          a.passed
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-amber-100 text-amber-800"
                        }`}
                        title={a.verdict || ""}
                      >
                        {a.percent}%{a.passed ? " · o'tdi" : ""}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">
                    {a.status === "done"
                      ? "yakunlandi"
                      : a.status === "running"
                      ? "ketmoqda"
                      : "to'xtatilgan"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
