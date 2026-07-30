import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Download, ArrowRight, ShieldCheck, CheckCircle2, RotateCcw,
  Award, TrendingDown,
} from "lucide-react";
import {
  api, type AuditResponse, type AuditMeta, type AuditRow,
  type ExamRow, type ExaminerAnalysis,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { AUDIT_VIEW, EXAM_VIEW, EXAM_ACCESS, can, roleLabel } from "../lib/roles";
import { BranchPicker, branchParam } from "../components/BranchPicker";
import { formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "log" | "exams" | "analysis";

/** Xavfli amallar qizil, oddiy o'zgarish kulrang. */
const DANGER = new Set([
  "delete", "debt_write_off", "payment_cancel", "group_remove",
  "role_change", "salary_change",
]);
const GOOD = new Set(["create", "activate"]);

function actionTone(action: string): string {
  if (DANGER.has(action)) return "bg-red-50 text-red-700";
  if (GOOD.has(action)) return "bg-emerald-50 text-emerald-700";
  if (action === "discount") return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-600";
}

function when(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("uz-UZ", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

const FIELD_LABELS: Record<string, string> = {
  full_name: "F.I.Sh.",
  phone: "Telefon",
  parent_phone: "Ota-ona telefoni",
  phone2: "Qo'shimcha telefon",
  status: "Holat",
  group: "Guruh",
  group_id: "Guruh",
  branch_id: "Filial",
  balance: "Balans",
  amount: "Summa",
  monthly_fee: "Oylik to'lov",
  role: "Lavozim",
  fix_salary: "Fiks oylik",
  password: "Parol",
  note: "Izoh",
  birth_date: "Tug'ilgan sana",
  enrolled_date: "Qo'shilgan sana",
  discount: "Chegirma",
  charge: "Hisoblangan to'lov",
  payment: "To'lov",
  is_active: "Faollik",
  severity: "Muhimlik",
  resolution: "Yechim",
  risk: "Risk signali",
  risk_task: "Risk vazifasi",
  parent_talk: "Ota-ona suhbati",
  certificate: "Sertifikat",
  support_plan: "Ishlash rejasi",
  attachment: "Fayl",
};

function fieldLabel(f?: string | null): string {
  if (!f) return "";
  return FIELD_LABELS[f] || f;
}

// -------------------------------------------------- O'zgarishlar tarixi
function LogTab() {
  const [data, setData] = useState<AuditResponse | null>(null);
  const [meta, setMeta] = useState<AuditMeta | null>(null);
  const [entity, setEntity] = useState("");
  const [action, setAction] = useState("");
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AuditMeta>("/audit/meta").then(setMeta).catch(() => setMeta(null));
  }, []);

  useEffect(() => {
    setLoading(true);
    const p = new URLSearchParams({ days: String(days), limit: "300" });
    if (entity) p.set("entity", entity);
    if (action) p.set("action", action);
    api
      .get<AuditResponse>(`/audit?${p}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [entity, action, days]);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <select
          value={entity}
          onChange={(e) => setEntity(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
        >
          <option value="">Barcha obyektlar</option>
          {meta?.entities.map((e) => (
            <option key={e.key} value={e.key}>
              {e.label}
            </option>
          ))}
        </select>
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
        >
          <option value="">Barcha amallar</option>
          {meta?.actions.map((a) => (
            <option key={a.key} value={a.key}>
              {a.label}
            </option>
          ))}
        </select>
        <div className="flex gap-1">
          {[7, 30, 90, 365].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
                days === d
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {d} kun
            </button>
          ))}
        </div>
        <span className="text-sm text-slate-500">
          {data ? `${data.rows.length} / ${data.total}` : ""}
        </span>
        <div className="flex-1" />
        <button
          onClick={() =>
            data &&
            exportToExcel("ozgarishlar-tarixi", "Tarix",
              data.rows.map((r) => ({
                Vaqt: when(r.created_at),
                Kim: r.user_name ?? "",
                Lavozim: roleLabel(r.user_role || ""),
                Amal: r.action_label,
                Obyekt: r.entity_label_type,
                Nomi: r.entity_label ?? "",
                Maydon: fieldLabel(r.field),
                "Eski qiymat": r.old_value ?? "",
                "Yangi qiymat": r.new_value ?? "",
                Izoh: r.note ?? "",
              })))
          }
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <Download size={14} /> Excel
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : !data || data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Bu davrda o'zgarish yo'q
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5 w-40">Vaqt</th>
                <th className="text-left w-40">Kim</th>
                <th className="text-left w-36">Amal</th>
                <th className="text-left w-48">Nima ustida</th>
                <th className="text-left w-32">Maydon</th>
                <th className="text-left">O'zgarish</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r: AuditRow) => (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">
                    {when(r.created_at)}
                  </td>
                  <td className="py-2.5">
                    <p className="text-sm text-slate-800">{r.user_name || "—"}</p>
                    <p className="text-xs text-slate-400">
                      {roleLabel(r.user_role || "")}
                    </p>
                  </td>
                  <td className="py-2.5">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${actionTone(
                        r.action
                      )}`}
                    >
                      {r.action_label}
                    </span>
                  </td>
                  <td className="py-2.5">
                    <p className="text-sm text-slate-800">{r.entity_label || "—"}</p>
                    <p className="text-xs text-slate-400">{r.entity_label_type}</p>
                  </td>
                  <td className="py-2.5 text-sm text-slate-500">
                    {fieldLabel(r.field)}
                  </td>
                  <td className="py-2.5 pr-4">
                    {r.old_value || r.new_value ? (
                      <div className="flex items-center gap-2 text-sm flex-wrap">
                        {r.old_value && (
                          <span className="text-red-600 line-through">
                            {r.old_value}
                          </span>
                        )}
                        {r.old_value && r.new_value && (
                          <ArrowRight size={12} className="text-slate-300" />
                        )}
                        {r.new_value && (
                          <span className="text-emerald-700">{r.new_value}</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-300 text-sm">—</span>
                    )}
                    {r.note && (
                      <p className="text-xs text-slate-400 mt-0.5">{r.note}</p>
                    )}
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

// -------------------------------------------------------- Imtihonlar
const EXAM_STATUS_TONE: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  approved: "bg-sky-50 text-sky-700",
  done: "bg-emerald-50 text-emerald-700",
  cancelled: "bg-red-50 text-red-600",
};

function ExamsTab({ branchId }: { branchId: number | null }) {
  const { user } = useAuth();
  const [rows, setRows] = useState<ExamRow[]>([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<number | null>(null);

  function load() {
    setLoading(true);
    const p = `months=6${status ? `&status=${status}` : ""}${branchParam(branchId)}`;
    api.get<ExamRow[]>(`/examiner/exams?${p}`).then(setRows)
      .finally(() => setLoading(false));
  }
  useEffect(load, [status, branchId]);

  const canApprove = can(user?.role, EXAM_ACCESS);

  async function approve(e: ExamRow) {
    setBusy(e.id);
    try {
      await api.post(`/examiner/exams/${e.id}/approve`, {});
      load();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  async function retake(e: ExamRow) {
    if (!confirm(`"${e.title}" uchun qayta imtihon yaratilsinmi?`)) return;
    await api.post(`/examiner/exams/${e.id}/retake`, {});
    load();
  }

  const drafts = rows.filter((r) => r.status === "draft").length;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1">
          {[
            { k: "", l: "Hammasi" },
            { k: "draft", l: "Tasdiq kutmoqda" },
            { k: "approved", l: "Tasdiqlangan" },
            { k: "done", l: "O'tkazilgan" },
          ].map((f) => (
            <button
              key={f.k}
              onClick={() => setStatus(f.k)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                status === f.k
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {f.l}
            </button>
          ))}
        </div>
        <span className="text-sm text-slate-500">{rows.length} ta imtihon</span>
      </div>

      {drafts > 0 && status !== "draft" && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <p className="text-sm text-amber-900">
            {drafts} ta test tasdiqlashni kutmoqda — tasdiqlanmaguncha ustoz
            natija kirita olmaydi.
          </p>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Imtihon yo'q. Guruh sahifasidan test yarating.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Test</th>
                <th className="text-left">Guruh</th>
                <th className="text-left">Ustoz</th>
                <th className="text-left">Filial</th>
                <th className="text-left w-28">Sana</th>
                <th className="text-right w-24">Natija</th>
                <th className="text-right w-24">O'rtacha</th>
                <th className="text-left w-36">Holat</th>
                <th className="w-40" />
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5">
                    <p className="text-slate-800">{e.title}</p>
                    {e.retake_of_id && (
                      <p className="text-xs text-amber-600">qayta imtihon</p>
                    )}
                  </td>
                  <td>
                    <Link
                      to={`/groups/${e.group_id}`}
                      className="text-slate-600 hover:text-brand-700"
                    >
                      {e.group}
                    </Link>
                  </td>
                  <td className="text-slate-500">{e.teacher || "—"}</td>
                  <td className="text-slate-500">{e.branch || "—"}</td>
                  <td className="text-slate-500 text-xs">
                    {e.date ? formatDate(e.date) : "—"}
                  </td>
                  <td className="text-right text-slate-600">
                    {e.result_count}
                    {e.absent > 0 && (
                      <span className="text-xs text-slate-400"> ({e.absent} yo'q)</span>
                    )}
                  </td>
                  <td
                    className={`text-right font-medium ${
                      e.avg_percent === null
                        ? "text-slate-300"
                        : e.avg_percent >= 70
                          ? "text-emerald-600"
                          : "text-red-600"
                    }`}
                  >
                    {e.avg_percent !== null ? `${e.avg_percent}%` : "—"}
                  </td>
                  <td>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        EXAM_STATUS_TONE[e.status] || "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {e.status_label}
                    </span>
                    {e.approved_by && (
                      <p className="text-xs text-slate-400 mt-0.5">
                        {e.approved_by}
                      </p>
                    )}
                  </td>
                  <td className="pr-4 text-right whitespace-nowrap">
                    {canApprove && e.status === "draft" && (
                      <button
                        onClick={() => approve(e)}
                        disabled={busy === e.id}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                      >
                        <CheckCircle2 size={12} /> Tasdiqlash
                      </button>
                    )}
                    {canApprove && e.status === "done" && (
                      <button
                        onClick={() => retake(e)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs text-slate-500 hover:text-slate-800"
                      >
                        <RotateCcw size={12} /> Qayta
                      </button>
                    )}
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

// ---------------------------------------------------------- Tahlil
function AnalysisTable({
  title, subtitle, rows, standard,
}: {
  title: string;
  subtitle: string;
  rows: { key: number; label: string; avg: number; results: number; band: string }[];
  standard: number;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm font-medium text-slate-700">{title}</p>
      <p className="text-xs text-slate-400 mb-3">{subtitle}</p>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-4">Ma'lumot yo'q</p>
      ) : (
        <table className="w-full text-sm">
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-b border-slate-50 last:border-0">
                <td className="py-2 text-slate-700">{r.label}</td>
                <td className="w-40">
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        r.avg >= standard ? "bg-emerald-500" : "bg-red-500"
                      }`}
                      style={{ width: `${Math.min(100, r.avg)}%` }}
                    />
                  </div>
                </td>
                <td
                  className={`text-right w-16 font-medium ${
                    r.avg >= standard ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {r.avg}%
                </td>
                <td className="text-right w-20 text-xs text-slate-400">
                  {r.results} ta
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function AnalysisTab({ branchId }: { branchId: number | null }) {
  const [data, setData] = useState<ExaminerAnalysis | null>(null);
  const [months, setMonths] = useState(6);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<ExaminerAnalysis>(
        `/examiner/analysis?months=${months}${branchParam(branchId)}`
      )
      .then(setData)
      .finally(() => setLoading(false));
  }, [months, branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  if (data.total_results === 0) {
    return (
      <p className="text-sm text-slate-400 py-10 text-center">
        Bu davrda imtihon natijasi yo'q.
      </p>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <div className="flex gap-1">
          {[
            { m: 1, l: "1 oy" },
            { m: 3, l: "3 oy" },
            { m: 6, l: "6 oy" },
            { m: 12, l: "1 yil" },
          ].map(({ m, l }) => (
            <button
              key={m}
              onClick={() => setMonths(m)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                months === m
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        <span className="text-sm text-slate-500">
          {data.total_results} ta natija · o'rtacha{" "}
          <span
            className={
              (data.avg ?? 0) >= data.standard
                ? "text-emerald-600 font-medium"
                : "text-red-600 font-medium"
            }
          >
            {data.avg}%
          </span>{" "}
          · standart {data.standard}%
        </span>
      </div>

      {data.behind.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown size={15} className="text-red-600" />
            <p className="text-sm font-medium text-red-900">
              {data.behind.length} ta guruh standartdan ortda
            </p>
          </div>
          <p className="text-xs text-red-800">
            {data.behind.map((g) => `${g.label} (${g.avg}%)`).join(", ")}
          </p>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3 mb-5">
        <AnalysisTable
          title="Ustozlar kesimida"
          subtitle="O'rtacha natija"
          rows={data.by_teacher}
          standard={data.standard}
        />
        <AnalysisTable
          title="Guruhlar kesimida"
          subtitle="O'rtacha natija"
          rows={data.by_group}
          standard={data.standard}
        />
        <AnalysisTable
          title="Filiallar kesimida"
          subtitle="O'rtacha natija"
          rows={data.by_branch}
          standard={data.standard}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <Award size={15} className="text-emerald-600" />
            <p className="text-sm font-medium text-slate-700">
              Sertifikatga tavsiya
            </p>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            O'rtachasi yuqori va kamida 2 ta imtihon topshirgan
          </p>
          {data.recommend_certificate.length === 0 ? (
            <p className="text-sm text-slate-400 py-4">Hozircha yo'q</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.recommend_certificate.map((p) => (
                  <tr key={p.student_id} className="border-b border-slate-50 last:border-0">
                    <td className="py-2">
                      <Link
                        to={`/students/${p.student_id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {p.full_name}
                      </Link>
                      <span className="block text-xs text-slate-400">{p.group}</span>
                    </td>
                    <td className="text-right text-emerald-600 font-medium">
                      {p.avg}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <RotateCcw size={15} className="text-amber-600" />
            <p className="text-sm font-medium text-slate-700">
              Qayta imtihonga tavsiya
            </p>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Oxirgi natijasi past bo'lganlar
          </p>
          {data.recommend_retake.length === 0 ? (
            <p className="text-sm text-slate-400 py-4">Hozircha yo'q</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.recommend_retake.map((p) => (
                  <tr key={p.student_id} className="border-b border-slate-50 last:border-0">
                    <td className="py-2">
                      <Link
                        to={`/students/${p.student_id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {p.full_name}
                      </Link>
                      <span className="block text-xs text-slate-400">{p.group}</span>
                    </td>
                    <td className="text-right text-red-600 font-medium">
                      {p.percent}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <p className="text-sm font-medium text-slate-700">O'quvchi progressi</p>
        <p className="text-xs text-slate-400 mb-3">
          Birinchi va oxirgi imtihon farqi — eng ko'p tushgani yuqorida
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-100">
                <th className="text-left py-2">O'quvchi</th>
                <th className="text-left">Guruh</th>
                <th className="text-right w-20">Birinchi</th>
                <th className="text-right w-20">Oxirgi</th>
                <th className="text-right w-24">O'zgarish</th>
                <th className="text-right w-20">O'rtacha</th>
              </tr>
            </thead>
            <tbody>
              {data.progress.map((p) => (
                <tr key={p.student_id} className="border-b border-slate-50">
                  <td className="py-2">
                    <Link
                      to={`/students/${p.student_id}`}
                      className="text-slate-800 hover:text-brand-700"
                    >
                      {p.full_name}
                    </Link>
                  </td>
                  <td className="text-slate-500">{p.group || "—"}</td>
                  <td className="text-right text-slate-500">{p.first}%</td>
                  <td className="text-right text-slate-700">{p.last}%</td>
                  <td
                    className={`text-right font-medium ${
                      p.change > 0
                        ? "text-emerald-600"
                        : p.change < 0
                          ? "text-red-600"
                          : "text-slate-400"
                    }`}
                  >
                    {p.change > 0 ? "+" : ""}
                    {p.change}
                  </td>
                  <td className="text-right text-slate-500">{p.avg}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Sahifa
export default function Audit() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("log");
  const [branchId, setBranchId] = useState<number | null>(null);

  const showLog = can(user?.role, AUDIT_VIEW);
  const showExams = can(user?.role, EXAM_VIEW);

  useEffect(() => {
    if (!showLog && showExams) setTab("exams");
  }, [showLog, showExams]);

  if (!showLog && !showExams) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const tabs: { key: Tab; label: string; show: boolean }[] = [
    { key: "log", label: "O'zgarishlar tarixi", show: showLog },
    { key: "exams", label: "Imtihonlar", show: showExams },
    { key: "analysis", label: "Imtihon tahlili", show: showExams },
  ];

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Audit</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Nazorat bo'limi: o'zgarishlar tarixi va imtihonlar. Examiner
        to'g'ridan-to'g'ri asoschiga bo'ysunadi.
      </p>

      <div className="flex items-center gap-2 border-b border-slate-200 mb-5">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.filter((t) => t.show).map((t) => (
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
        <div className="flex-1" />
        {tab !== "log" && (
          <BranchPicker value={branchId} onChange={setBranchId} className="pb-2" />
        )}
      </div>

      {tab === "log" && <LogTab />}
      {tab === "exams" && <ExamsTab branchId={branchId} />}
      {tab === "analysis" && <AnalysisTab branchId={branchId} />}
    </div>
  );
}
