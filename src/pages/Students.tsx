import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, X, Download, Pencil } from "lucide-react";
import { api, type Student, type Group, type Branch } from "../lib/api";
import { formatSom } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, can } from "../lib/roles";
import { exportToExcel } from "../lib/exportXlsx";
import { PhoneInput, formatPhone } from "../components/PhoneInput";

const STATUSES = [
  { key: "active", label: "Faol" },
  { key: "trial", label: "Sinovda" },
  { key: "frozen", label: "Muzlatilgan" },
  { key: "archived", label: "Arxiv (ketgan)" },
];

function StudentModal({
  groups,
  branches,
  defaultBranchId,
  initial,
  onClose,
  onSaved,
}: {
  groups: Group[];
  branches: Branch[];
  defaultBranchId: number | null;
  initial?: Student;
  onClose: () => void;
  onSaved: (s: Student) => void;
}) {
  const editing = !!initial;
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [phone, setPhone] = useState(initial?.phone ?? "");
  const [parentPhone, setParentPhone] = useState(initial?.parent_phone ?? "");
  const [groupId, setGroupId] = useState<string>(
    initial?.group ? String(initial.group.id) : ""
  );
  const [branchId, setBranchId] = useState(
    initial?.branch
      ? String(initial.branch.id)
      : defaultBranchId
      ? String(defaultBranchId)
      : ""
  );
  // Yangi o'quvchi "sinov darsida" boshlanadi - guruhga qo'shilishi bilan
  // avtomat faol bo'lib qolmasligi kerak. Faollashtirish guruh ro'yxatidagi
  // uch nuqta menyusidan qilinadi.
  const [status, setStatus] = useState(initial?.status ?? "trial");
  const [enrolledDate, setEnrolledDate] = useState(
    initial?.enrolled_date ?? new Date().toISOString().slice(0, 10)
  );
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
        parent_phone: parentPhone || null,
        group_id: groupId ? Number(groupId) : null,
        branch_id: branchId ? Number(branchId) : null,
        enrolled_date: enrolledDate || null,
        status,
      };
      const s = editing
        ? await api.put<Student>(`/students/${initial!.id}`, body)
        : await api.post<Student>("/students", body);
      onSaved(s);
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
            {editing ? "Talabani tahrirlash" : "Yangi talaba qo'shish"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              F.I.Sh. *
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Talaba telefoni
            </label>
            <PhoneInput value={phone} onChange={setPhone} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Ota-ona telefoni
            </label>
            <PhoneInput value={parentPhone} onChange={setParentPhone} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Qo'shilgan sana
            </label>
            <input
              type="date"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={enrolledDate}
              onChange={(e) => setEnrolledDate(e.target.value)}
            />
            <p className="text-xs text-slate-400 mt-1">
              Oy o'rtasida qo'shilgan talaba uchun to'lov shu sanadan hisoblanadi
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Filial
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={branchId}
              onChange={(e) => setBranchId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Guruh
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Holat
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
            {status === "archived" && (
              <p className="text-xs text-slate-400 mt-1">
                Ketgan sana avtomatik bugungi kun bilan qo'yiladi — LTV shundan
                hisoblanadi.
              </p>
            )}
            {!initial && status === "trial" && (
              <p className="text-xs text-slate-400 mt-1">
                Yangi o'quvchi sinov darsida boshlanadi. Guruh ro'yxatidagi uch
                nuqta menyusidan "Faollashtirish" bosilganda faol bo'ladi.
              </p>
            )}
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

export { StudentModal };

export default function Students() {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Student | null>(null);

  function load() {
    setLoading(true);
    const query = q ? `?q=${encodeURIComponent(q)}` : "";
    Promise.all([
      api.get<Student[]>(`/students${query}`),
      api.get<Group[]>("/groups"),
      api.get<Branch[]>("/branches"),
    ])
      .then(([s, g, b]) => {
        setStudents(s);
        setGroups(g);
        setBranches(b);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const canEdit = can(user?.role, TEACHING_STAFF);
  const showBranchColumn = branches.length > 1;

  function exportStudents() {
    exportToExcel(
      `Talabalar-${new Date().toISOString().slice(0, 10)}`,
      "Talabalar",
      students.map((s) => ({
        "F.I.Sh.": s.full_name,
        Telefon: s.phone || "",
        "Ota-ona telefoni": s.parent_phone || "",
        Guruh: s.group?.name || "",
        Filial: s.branch?.name || "",
        "Balans (so'm)": Math.round(s.balance),
      }))
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Talabalar</h1>
          <p className="text-sm text-slate-500">Jami: {students.length}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportStudents}
            disabled={students.length === 0}
            className="flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            <Download size={16} />
            Excel'ga eksport
          </button>
          {canEdit && (
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
            >
              <Plus size={16} />
              Yangi talaba
            </button>
          )}
        </div>
      </div>

      <div className="relative mb-4 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
        <input
          className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm"
          placeholder="Ism orqali qidirish..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">F.I.Sh.</th>
              <th className="text-left px-4 py-3 font-medium">Telefon</th>
              <th className="text-left px-4 py-3 font-medium">Guruh</th>
              {showBranchColumn && (
                <th className="text-left px-4 py-3 font-medium">Filial</th>
              )}
              <th className="text-left px-4 py-3 font-medium">Holat</th>
              <th className="text-right px-4 py-3 font-medium">Balans</th>
              {canEdit && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                  Yuklanmoqda...
                </td>
              </tr>
            )}
            {!loading && students.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                  Talaba topilmadi
                </td>
              </tr>
            )}
            {students.map((s) => (
              <tr key={s.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link
                    to={`/students/${s.id}`}
                    className="font-medium text-brand-700 hover:underline"
                  >
                    {s.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600 text-xs">
                  {formatPhone(s.phone) || "—"}
                </td>
                <td className="px-4 py-3">
                  {s.group ? (
                    <span className="inline-block bg-brand-50 text-brand-700 rounded-md px-2 py-0.5 text-xs">
                      {s.group.name}
                    </span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                {showBranchColumn && (
                  <td className="px-4 py-3 text-slate-600">{s.branch?.name || "—"}</td>
                )}
                <td className="px-4 py-3">
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                      s.status === "active"
                        ? "bg-green-50 text-green-700"
                        : s.status === "archived"
                        ? "bg-slate-100 text-slate-500"
                        : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    {STATUSES.find((x) => x.key === s.status)?.label || s.status}
                  </span>
                </td>
                <td
                  className={`px-4 py-3 text-right font-medium ${
                    s.balance < 0 ? "text-red-600" : "text-slate-700"
                  }`}
                >
                  {formatSom(s.balance)}
                </td>
                {canEdit && (
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setEditing(s)}
                      title="Tahrirlash"
                      className="text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={15} />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAdd && (
        <StudentModal
          groups={groups}
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          onClose={() => setShowAdd(false)}
          onSaved={() => load()}
        />
      )}
      {editing && (
        <StudentModal
          groups={groups}
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
    </div>
  );
}
