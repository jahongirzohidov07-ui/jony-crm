import { useEffect, useState } from "react";
import { History, Download, ArrowRight } from "lucide-react";
import {
  api, type AuditResponse, type AuditMeta, type AuditRow,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { AUDIT_VIEW, can, roleLabel } from "../lib/roles";
import { exportToExcel } from "../lib/exportXlsx";

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

/** Maydon nomlarini o'zbekchaga o'giradi. */
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
};

function fieldLabel(f?: string | null): string {
  if (!f) return "";
  return FIELD_LABELS[f] || f;
}

function Row({ r }: { r: AuditRow }) {
  return (
    <tr className="border-t border-slate-100 hover:bg-slate-50">
      <td className="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">
        {when(r.created_at)}
      </td>
      <td className="py-2.5">
        <p className="text-sm text-slate-800">{r.user_name || "—"}</p>
        <p className="text-xs text-slate-400">{roleLabel(r.user_role || "")}</p>
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
      <td className="py-2.5 text-sm">
        {r.field && (
          <span className="text-slate-500">{fieldLabel(r.field)}</span>
        )}
      </td>
      <td className="py-2.5 pr-4">
        {r.old_value || r.new_value ? (
          <div className="flex items-center gap-2 text-sm flex-wrap">
            {r.old_value && (
              <span className="text-red-600 line-through">{r.old_value}</span>
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
        {r.note && <p className="text-xs text-slate-400 mt-0.5">{r.note}</p>}
      </td>
    </tr>
  );
}

export default function Audit() {
  const { user } = useAuth();
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

  if (!can(user?.role, AUDIT_VIEW)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <History size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">O'zgarishlar tarixi</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Kim, qachon, nimani o'zgartirdi. Yozuvlarni hech kim o'chira yoki
        tahrirlay olmaydi.
      </p>

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
              {data.rows.map((r) => (
                <Row key={r.id} r={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
