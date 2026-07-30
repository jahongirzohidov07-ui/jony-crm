import { useEffect, useState } from "react";
import {
  Plus, Trash2, Pencil, Users, UserCheck, Clock, Briefcase, X,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell,
} from "recharts";
import {
  api, type Vacancy, type Candidate, type HrFunnel, type Branch,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { HR_ACCESS, can, ALL_ROLES, roleLabel } from "../lib/roles";
import {
  CANDIDATE_STAGES, CANDIDATE_SOURCES,
  VACANCY_STATUSES, stageLabel, stageColor, candidateSourceLabel,
  vacancyStatusLabel,
} from "../lib/hr";
import { CandidateCard } from "../components/CandidateCard";
import { formatSom, formatDate } from "../lib/format";
import { Attachments } from "../components/Attachments";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "funnel" | "candidates" | "vacancies";

const TABS: { key: Tab; label: string }[] = [
  { key: "funnel", label: "HR voronka" },
  { key: "candidates", label: "Nomzodlar" },
  { key: "vacancies", label: "Vakansiyalar" },
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
const emptyCand = {
  full_name: "",
  phone: "",
  vacancy_id: "" as string | number,
  stage: "applied",
  source: "other",
  branch_id: "" as string | number,
  note: "",
};

function CandidatesTab({ branches }: { branches: Branch[] }) {
  const [rows, setRows] = useState<Candidate[]>([]);
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Candidate | null>(null);
  const [card, setCard] = useState<number | null>(null);
  const [form, setForm] = useState({ ...emptyCand });
  const [stageFilter, setStageFilter] = useState("");
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

  const open = (c?: Candidate) => {
    setErr("");
    if (c) {
      setEditing(c);
      setForm({
        full_name: c.full_name,
        phone: c.phone ?? "",
        vacancy_id: c.vacancy_id ?? "",
        stage: c.stage,
        source: c.source,
        branch_id: c.branch_id ?? "",
        note: c.note ?? "",
      });
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
      stage: form.stage,
      source: form.source,
      branch_id: form.branch_id ? Number(form.branch_id) : null,
      note: form.note || null,
    };
    try {
      if (editing) await api.put(`/candidates/${editing.id}`, body);
      else await api.post("/candidates", body);
      setModal(false);
      load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const move = async (c: Candidate, stage: string) => {
    await api.put(`/candidates/${c.id}`, { stage });
    load();
  };

  const remove = async (c: Candidate) => {
    if (!confirm(`${c.full_name} o'chirilsinmi?`)) return;
    await api.delete(`/candidates/${c.id}`);
    load();
  };

  const shown = stageFilter ? rows.filter((r) => r.stage === stageFilter) : rows;

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
        <span className="text-sm text-slate-500">{shown.length} ta nomzod</span>
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("nomzodlar", "Nomzodlar",
              shown.map((c) => ({
                "F.I.Sh.": c.full_name,
                Telefon: c.phone ?? "",
                Vakansiya: c.vacancy ?? "",
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
                  <td className="text-slate-500">{c.vacancy || "—"}</td>
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
          canEdit
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
  const [tab, setTab] = useState<Tab>("funnel");
  const [branches, setBranches] = useState<Branch[]>([]);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  if (!can(user?.role, HR_ACCESS)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

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
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "funnel" && <FunnelTab />}
      {tab === "candidates" && <CandidatesTab branches={branches} />}
      {tab === "vacancies" && <VacanciesTab branches={branches} />}
    </div>
  );
}
