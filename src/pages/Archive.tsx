import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Archive as ArchiveIcon, Download, X } from "lucide-react";
import {
  api, type ArchiveStudents, type ArchiveStaff, type ArchiveStaffRow,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, STAFF_VIEWERS, HR_ACCESS, can } from "../lib/roles";
import { BranchPicker, branchParam } from "../components/BranchPicker";
import { formatSom, formatDate } from "../lib/format";
import { formatPhone } from "../components/PhoneInput";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "students" | "staff";

/** Arxiv toifalari rangi. */
const GROUP_TONE: Record<string, { box: string; text: string; dot: string }> = {
  debtor: {
    box: "bg-red-50 border-red-200",
    text: "text-red-700",
    dot: "bg-red-500",
  },
  credit: {
    box: "bg-amber-50 border-amber-200",
    text: "text-amber-700",
    dot: "bg-amber-500",
  },
  clear: {
    box: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-700",
    dot: "bg-emerald-500",
  },
  green: {
    box: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-700",
    dot: "bg-emerald-500",
  },
  neutral: {
    box: "bg-slate-50 border-slate-200",
    text: "text-slate-600",
    dot: "bg-slate-400",
  },
  red: {
    box: "bg-red-50 border-red-200",
    text: "text-red-700",
    dot: "bg-red-500",
  },
};

function toneOf(key: string) {
  return GROUP_TONE[key] || GROUP_TONE.neutral;
}

// ------------------------------------------------------- O'quvchilar
function StudentsTab() {
  const [data, setData] = useState<ArchiveStudents | null>(null);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<ArchiveStudents>(`/archive/students?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const shown = filter
    ? data.rows.filter((r) => r.group_key === filter)
    : data.rows;

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        {data.groups.map((g) => {
          const T = toneOf(g.key);
          const active = filter === g.key;
          return (
            <button
              key={g.key}
              onClick={() => setFilter(active ? "" : g.key)}
              className={`text-left rounded-xl border p-4 transition ${
                active ? T.box : "bg-white border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2.5 h-2.5 rounded-full ${T.dot}`} />
                <p className="text-sm text-slate-700">{g.label}</p>
              </div>
              <p className="text-xl font-semibold text-slate-900">{g.count}</p>
              {g.total > 0 && (
                <p className={`text-sm mt-0.5 ${T.text}`}>
                  {formatSom(g.total)}
                </p>
              )}
              <p className="text-xs text-slate-400 mt-0.5">{g.hint}</p>
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm text-slate-500">{shown.length} ta o'quvchi</span>
        {filter && (
          <button
            onClick={() => setFilter("")}
            className="text-xs text-brand-600 hover:underline"
          >
            filtrni tozalash
          </button>
        )}
        <BranchPicker value={branchId} onChange={setBranchId} />
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("arxiv-oquvchilar", "Arxiv",
              shown.map((r) => ({
                ID: r.public_id ?? "",
                "F.I.Sh.": r.full_name,
                Guruh: r.group ?? "",
                Filial: r.branch ?? "",
                Telefon: formatPhone(r.phone),
                "Qo'shilgan": r.enrolled_date ?? "",
                Ketgan: r.left_date ?? "",
                "Necha oy": r.months ?? "",
                Balans: r.balance,
                Toifa: data.groups.find((g) => g.key === r.group_key)?.label ?? "",
              })))
          }
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <Download size={14} /> Excel
        </button>
      </div>

      {shown.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Arxivda o'quvchi yo'q
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">O'quvchi</th>
                <th className="text-left">Guruh</th>
                <th className="text-left">Telefon</th>
                <th className="text-left w-28">Ketgan</th>
                <th className="text-right w-24">Necha oy</th>
                <th className="text-right w-36">Hisob</th>
                <th className="text-left w-44 pr-4">Toifa</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => {
                const T = toneOf(r.group_key);
                const g = data.groups.find((x) => x.key === r.group_key);
                return (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5">
                      <Link
                        to={`/students/${r.id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {r.full_name}
                      </Link>
                      {r.public_id && (
                        <span className="block text-xs text-slate-400">
                          {r.public_id}
                        </span>
                      )}
                    </td>
                    <td className="text-slate-500">{r.group || "—"}</td>
                    <td className="text-slate-500 text-xs">
                      {formatPhone(r.phone) || "—"}
                    </td>
                    <td className="text-slate-500 text-xs">
                      {r.left_date ? formatDate(r.left_date) : "—"}
                    </td>
                    <td className="text-right text-slate-500">
                      {r.months ?? "—"}
                    </td>
                    <td
                      className={`text-right font-medium ${
                        r.balance < 0
                          ? "text-red-600"
                          : r.balance > 0
                            ? "text-amber-600"
                            : "text-slate-400"
                      }`}
                    >
                      {r.balance === 0 ? "—" : formatSom(r.balance)}
                    </td>
                    <td className={`pr-4 text-xs ${T.text}`}>{g?.label}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------ Xodimlar
function StaffTab() {
  const { user } = useAuth();
  const [data, setData] = useState<ArchiveStaff | null>(null);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<ArchiveStaffRow | null>(null);

  function load() {
    setLoading(true);
    api
      .get<ArchiveStaff>("/archive/staff")
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const shown = filter
    ? data.rows.filter((r) => r.exit_type === filter)
    : data.rows;
  const canEdit = can(user?.role, HR_ACCESS);

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        {data.groups.map((g) => {
          const T = toneOf(g.key);
          const active = filter === g.key;
          return (
            <button
              key={g.key}
              onClick={() => setFilter(active ? "" : g.key)}
              className={`text-left rounded-xl border p-4 transition ${
                active ? T.box : "bg-white border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2.5 h-2.5 rounded-full ${T.dot}`} />
                <p className="text-sm text-slate-700">{g.label}</p>
              </div>
              <p className="text-xl font-semibold text-slate-900">{g.count}</p>
              <p className="text-xs text-slate-400 mt-0.5">{g.hint}</p>
            </button>
          );
        })}
      </div>

      {shown.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Ishdan bo'shagan xodim yo'q
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Xodim</th>
                <th className="text-left">Lavozim</th>
                <th className="text-left">Filial</th>
                <th className="text-left w-28">Ketgan</th>
                <th className="text-left">Sabab</th>
                <th className="text-left w-40">Toifa</th>
                <th className="w-24" />
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => {
                const T = toneOf(r.exit_type);
                return (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5 text-slate-800">
                      {r.full_name}
                      <span className="block text-xs text-slate-400">
                        {r.username}
                      </span>
                    </td>
                    <td className="text-slate-500">{r.role_label}</td>
                    <td className="text-slate-500">{r.branch || "—"}</td>
                    <td className="text-slate-500 text-xs">
                      {r.exit_date ? formatDate(r.exit_date) : "—"}
                    </td>
                    <td className="text-slate-600 text-xs">
                      {r.exit_reason || "—"}
                    </td>
                    <td>
                      <span
                        className={`inline-flex items-center gap-1.5 text-xs ${T.text}`}
                      >
                        <span className={`w-2 h-2 rounded-full ${T.dot}`} />
                        {r.exit_label}
                      </span>
                    </td>
                    <td className="pr-4 text-right">
                      {canEdit && (
                        <button
                          onClick={() => setEditing(r)}
                          className="px-2.5 py-1 rounded-md text-xs border border-slate-200 text-slate-600 hover:border-brand-300"
                        >
                          Belgilash
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <ExitModal
          row={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}

const EXIT_TYPES = [
  { key: "green", label: "Yashil yo'lak", hint: "Qaytarib olsa bo'ladi" },
  { key: "neutral", label: "Neytral", hint: "Oddiy ketish" },
  { key: "red", label: "Qizil yo'lak", hint: "Qayta ishga olinmaydi" },
];

function ExitModal({
  row, onClose, onSaved,
}: {
  row: ArchiveStaffRow;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [type, setType] = useState(row.exit_type || "neutral");
  const [reason, setReason] = useState(row.exit_reason || "");
  const [err, setErr] = useState("");

  async function save() {
    try {
      await api.put(`/archive/staff/${row.id}`, {
        exit_type: type,
        exit_reason: reason || null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Qanday ajrashildi</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">{row.full_name}</p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-2">
          {EXIT_TYPES.map((t) => {
            const T = toneOf(t.key);
            return (
              <button
                key={t.key}
                onClick={() => setType(t.key)}
                className={`w-full text-left rounded-xl border p-3 transition ${
                  type === t.key ? T.box : "bg-white border-slate-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${T.dot}`} />
                  <span className="text-sm font-medium text-slate-800">
                    {t.label}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 ml-4.5">{t.hint}</p>
              </button>
            );
          })}
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Sabab (ixtiyoriy)"
            rows={2}
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

// ---------------------------------------------------------------- Sahifa
export default function Archive() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("students");

  if (!can(user?.role, TEACHING_STAFF)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const showStaff = can(user?.role, STAFF_VIEWERS);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ArchiveIcon size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Arxiv</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Ketgan o'quvchilar va ishdan bo'shagan xodimlar
      </p>

      {showStaff && (
        <div className="flex gap-1 border-b border-slate-200 mb-5">
          {[
            { k: "students" as Tab, l: "O'quvchilar" },
            { k: "staff" as Tab, l: "Xodimlar" },
          ].map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition ${
                tab === t.k
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.l}
            </button>
          ))}
        </div>
      )}

      {tab === "students" || !showStaff ? <StudentsTab /> : <StaffTab />}
    </div>
  );
}
