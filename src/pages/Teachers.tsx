import { useEffect, useState } from "react";
import { Plus, X, UserMinus, UserCheck } from "lucide-react";
import { api, type Teacher, type Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { STAFF_VIEWERS, can } from "../lib/roles";
import { formatDate } from "../lib/format";

function AddTeacherModal({
  branches,
  defaultBranchId,
  onClose,
  onCreated,
}: {
  branches: Branch[];
  defaultBranchId: number | null;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [subject, setSubject] = useState("");
  const [branchId, setBranchId] = useState(defaultBranchId ? String(defaultBranchId) : "");
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
      await api.post("/teachers", {
        full_name: fullName,
        phone: phone || null,
        subject: subject || null,
        branch_id: branchId ? Number(branchId) : null,
      });
      onCreated();
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
          <h2 className="font-semibold text-slate-900">Yangi o'qituvchi</h2>
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
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Filial</label>
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

  return (
    <div className="p-8">
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
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
          >
            <Plus size={16} /> Yangi o'qituvchi
          </button>
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
                      {t.full_name}
                      {left && (
                        <span className="ml-2 text-[10px] uppercase tracking-wide bg-slate-200 text-slate-500 px-1.5 py-0.5 rounded">
                          ketgan {t.left_date ? formatDate(t.left_date) : ""}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{t.phone || "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{t.subject || "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{t.branch?.name || "—"}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {t.hired_date ? formatDate(t.hired_date) : "—"}
                    </td>
                    {canEdit && (
                      <td className="px-4 py-3 text-right whitespace-nowrap">
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

      {showAdd && (
        <AddTeacherModal
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          onClose={() => setShowAdd(false)}
          onCreated={load}
        />
      )}
    </div>
  );
}
