import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Plus, Trash2, Pencil, Users, UserCheck, Clock, Briefcase, X,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell,
} from "recharts";
import {
  api, type Vacancy, type Candidate, type HrFunnel, type Branch,
  type LibraryList, type LibraryItem, type LibraryPeople,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { AtsBoard } from "../components/AtsBoard";
import { HrOverviewTab, HrLifecycleTab } from "../components/HrLifecycle";
import {
  HR_ACCESS, HR_CANDIDATE_VIEW, can, ALL_ROLES, roleLabel,
} from "../lib/roles";
import {
  CANDIDATE_STAGES, CANDIDATE_SOURCES, APPLY_POSITIONS,
  APPLY_MARITAL, APPLY_WORK_DURATIONS,
  VACANCY_STATUSES, stageLabel, stageColor, candidateSourceLabel,
  vacancyStatusLabel,
} from "../lib/hr";
import { CandidateCard } from "../components/CandidateCard";
import { AttendanceTab, NpsTab } from "../components/HrExtras";
import { StaffDatesTab } from "../components/StaffDates";
import { ObservationsTab } from "../components/LessonRubric";
import { StaffTab } from "./Users";
import {
  WorkforceTab, StaffRequestsTab, HrVacanciesTab,
} from "../components/HrCore";
import { formatSom, formatDate } from "../lib/format";
import { Attachments } from "../components/Attachments";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "overview" | "ats" | "lifecycle" | "funnel" | "candidates" | "vacancies" | "staff"
  | "rubric" | "dates" | "attendance" | "nps"
  | "workforce" | "requests" | "hrvacancies" | "library";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Umumiy holat" },
  { key: "ats", label: "Ishga olish quvuri" },
  { key: "lifecycle", label: "Hayotiy sikl" },
  { key: "funnel", label: "HR voronka" },
  { key: "workforce", label: "Shtat rejasi" },
  { key: "requests", label: "Xodim so'rovlari" },
  { key: "hrvacancies", label: "Vakansiyalar (yangi)" },
  { key: "candidates", label: "Nomzodlar" },
  { key: "vacancies", label: "Vakansiyalar" },
  { key: "staff", label: "Xodimlar" },
  { key: "rubric", label: "Dars baholash" },
  { key: "dates", label: "Sanalar" },
  { key: "attendance", label: "Davomat" },
  { key: "nps", label: "Ustozlar NPS" },
  { key: "library", label: "Kutubxona" },
];

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

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  if (data.total === 0) {
    return (
      <p className="text-sm text-slate-400 py-10 text-center">
        Bu davrda nomzod kiritilmagan. "Nomzodlar" bo'limidan qo'shing —
        voronka shundan keyin chiqadi.
      </p>
    );
  }

  const chart = data.stages.map((s) => ({
    name: s.label,
    Yetgan: s.reached,
    color: stageColor(s.stage),
  }));

  return (
    <div>
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
  };
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

  const save = async () => {
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
      else await api.post("/candidates", bodyWithDate);
      setModal(false);
      load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const move = async (c: Candidate, stage: string) => {
    // 2026-08-12, Jahongir: "rad etildidan keyin sabab so'rasa yaxshi edi"
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
                Vakansiya: c.role_label ?? "",
                Fan: c.subject ?? "",
                Bosqich: stageLabel(c.stage),
                Manba: candidateSourceLabel(c.source),
                Filial: c.branch ?? "",
                Sana: c.created_at?.slice(0, 10) ?? "",
              })))
          }
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          Excel
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
                  </td>
                  <td className="text-slate-500">{c.phone || "—"}</td>
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
              <input
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                placeholder="Ism familiya"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="Telefon"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
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
              {/* Vakansiya ochilmagan bo'lsa ham QAYSI ISHGA kelgani
                  bilinib tursin (2026-08-15). Ustoz bo'lsa — fani. */}
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
              {form.position === "teacher" && (
                <>
                  <input
                    value={form.subject}
                    onChange={(e) =>
                      setForm({ ...form, subject: e.target.value })
                    }
                    placeholder="Qaysi fandan? (Ingliz tili, Matematika…)"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  />
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
              <input
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="Yashash manzili"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  value={form.birth_date}
                  onChange={(e) =>
                    setForm({ ...form, birth_date: e.target.value })
                  }
                  placeholder="Tug'ilgan sana"
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
                <select
                  value={form.marital}
                  onChange={(e) =>
                    setForm({ ...form, marital: e.target.value })
                  }
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Oilaviy holati</option>
                  {APPLY_MARITAL.map((m) => (
                    <option key={m.key} value={m.key}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
              <input
                value={form.education}
                onChange={(e) =>
                  setForm({ ...form, education: e.target.value })
                }
                placeholder="Ma'lumoti (maktab raqami yoki bitirgan joyi)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <textarea
                value={form.workplaces}
                onChange={(e) =>
                  setForm({ ...form, workplaces: e.target.value })
                }
                rows={2}
                placeholder="Avvalgi ish joylari (lavozim, qancha vaqt)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <input
                value={form.socials}
                onChange={(e) => setForm({ ...form, socials: e.target.value })}
                placeholder="Ijtimoiy tarmoqlar (Instagram, Telegram…)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
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
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={form.stage}
                  onChange={(e) => setForm({ ...form, stage: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {CANDIDATE_STAGES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
                <select
                  value={form.source}
                  onChange={(e) => setForm({ ...form, source: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {CANDIDATE_SOURCES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
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
              <textarea
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
                placeholder="Izoh"
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />

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
  const [spHr] = useSearchParams();
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
  const visibleTabs = fullHr
    ? TABS
    : TABS.filter((t) => t.key === "candidates" || t.key === "rubric");
  const activeTab = visibleTabs.some((t) => t.key === tab)
    ? tab
    : visibleTabs[0].key;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Briefcase size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">HR</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Vakansiyalar, nomzodlar va ishga olish voronkasi
      </p>

      <div className="flex gap-1 border-b border-slate-200 mb-5 overflow-x-auto">
        {visibleTabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
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
      {activeTab === "rubric" && <ObservationsTab />}
      {activeTab === "dates" && <StaffDatesTab />}
      {activeTab === "attendance" && <AttendanceTab />}
      {activeTab === "nps" && <NpsTab />}
      {activeTab === "library" && <LibraryTab />}
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

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <p className="text-sm text-slate-500">
          {data.items.length} ta material
        </p>
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

      {data.items.length === 0 ? (
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
              {data.items.map((it) => (
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
  roles: roleList, kinds, onClose, onSaved,
}: {
  roles: { key: string; label: string }[];
  kinds: { key: string; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("video");
  const [url, setUrl] = useState("");
  const [minutes, setMinutes] = useState("");
  const [desc, setDesc] = useState("");
  const [required, setRequired] = useState(true);
  const [target, setTarget] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function save() {
    setBusy(true);
    setErr("");
    try {
      await api.post("/library", {
        title,
        kind,
        url,
        minutes: Number(minutes) || 0,
        description: desc,
        required,
        target_roles: target,
      });
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
          <h2 className="font-semibold text-slate-900">Yangi material</h2>
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
              Havola *
            </label>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://youtu.be/... yoki Google Drive havolasi"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <p className="text-xs text-slate-400 mt-1">
              Video YouTube yoki Drive'da tursin — bazaga yuklanmaydi,
              shuning uchun tizim sekinlashmaydi.
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
            disabled={busy || !title.trim() || !url.trim()}
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
