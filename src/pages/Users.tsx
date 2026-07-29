import { useEffect, useState } from "react";
import { Plus, X, Pencil } from "lucide-react";
import { api, type User, type Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  STAFF_MANAGERS,
  BRANCH_MANAGER,
  can,
  roleLabel,
  assignableRoles,
} from "../lib/roles";

function UserForm({
  branches,
  lockBranchId,
  initial,
  onCancel,
  onSubmit,
  submitLabel,
}: {
  branches: Branch[];
  lockBranchId: number | null;
  initial?: Partial<{
    username: string;
    full_name: string;
    role: string;
    branch_id: number | null;
    is_active: boolean;
  }>;
  onCancel: () => void;
  onSubmit: (data: {
    username?: string;
    password?: string;
    full_name: string;
    role: string;
    branch_id: number | null;
    is_active?: boolean;
  }) => Promise<void>;
  submitLabel: string;
}) {
  const { user } = useAuth();
  const roles = assignableRoles(user?.role);
  const isEdit = !!initial;

  const [username, setUsername] = useState(initial?.username ?? "");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [role, setRole] = useState(initial?.role ?? roles[0] ?? "");
  const [branchId, setBranchId] = useState(
    lockBranchId ? String(lockBranchId) : initial?.branch_id ? String(initial.branch_id) : ""
  );
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!isEdit && (!username.trim() || !password.trim())) {
      setError("Login va parolni kiriting");
      return;
    }
    if (!fullName.trim()) {
      setError("Ism-familiyani kiriting");
      return;
    }
    if (!role) {
      setError("Rolni tanlang");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        username: isEdit ? undefined : username,
        password: password || undefined,
        full_name: fullName,
        role,
        branch_id: branchId ? Number(branchId) : null,
        is_active: isEdit ? isActive : undefined,
      });
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
            {isEdit ? "Xodimni tahrirlash" : "Yangi xodim"}
          </h2>
          <button onClick={onCancel} className="text-slate-400 hover:text-slate-600">
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

          {!isEdit && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Login *</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="off"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              {isEdit ? "Yangi parol (o'zgartirmasa bo'sh qoldiring)" : "Parol *"}
            </label>
            <input
              type="password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Rol *</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              {roles.map((r) => (
                <option key={r} value={r}>
                  {roleLabel(r)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Filial</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white disabled:bg-slate-100 disabled:text-slate-400"
              value={branchId}
              onChange={(e) => setBranchId(e.target.value)}
              disabled={!!lockBranchId}
            >
              <option value="">— tanlanmagan —</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {isEdit && (
            <label className="flex items-center gap-2 text-sm text-slate-700 pt-1">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              Faol hisob
            </label>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={submit}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-2 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : submitLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Users() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    Promise.all([api.get<User[]>("/users"), api.get<Branch[]>("/branches")])
      .then(([u, b]) => {
        setUsers(u);
        setBranches(b);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const canManage = can(user?.role, STAFF_MANAGERS);
  const lockBranchId = user?.role === BRANCH_MANAGER ? user?.branch_id ?? null : null;

  async function toggleActive(u: User) {
    setRowError(null);
    try {
      await api.put(`/users/${u.id}`, { is_active: !u.is_active });
      load();
    } catch (e) {
      setRowError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (!canManage) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">Bu sahifani ko'rish uchun ruxsatingiz yo'q.</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Xodimlar</h1>
          <p className="text-sm text-slate-500">Jami: {users.length}</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          <Plus size={16} /> Yangi xodim
        </button>
      </div>

      {rowError && <p className="text-sm text-red-600 mb-3">{rowError}</p>}

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">F.I.Sh.</th>
                <th className="text-left px-4 py-3 font-medium">Login</th>
                <th className="text-left px-4 py-3 font-medium">Rol</th>
                <th className="text-left px-4 py-3 font-medium">Filial</th>
                <th className="text-left px-4 py-3 font-medium">Holat</th>
                <th className="text-right px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{u.full_name}</td>
                  <td className="px-4 py-3 text-slate-600">{u.username}</td>
                  <td className="px-4 py-3 text-slate-600">{roleLabel(u.role)}</td>
                  <td className="px-4 py-3 text-slate-600">{u.branch?.name || "—"}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleActive(u)}
                      className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${
                        u.is_active
                          ? "bg-green-50 text-green-700 hover:bg-green-100"
                          : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                      }`}
                    >
                      {u.is_active ? "Faol" : "Faolsiz"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setEditing(u)}
                      className="text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAdd && (
        <UserForm
          branches={branches}
          lockBranchId={lockBranchId}
          submitLabel="Yaratish"
          onCancel={() => setShowAdd(false)}
          onSubmit={async (data) => {
            await api.post("/users", data);
            setShowAdd(false);
            load();
          }}
        />
      )}

      {editing && (
        <UserForm
          branches={branches}
          lockBranchId={lockBranchId}
          initial={{
            username: editing.username,
            full_name: editing.full_name,
            role: editing.role,
            branch_id: editing.branch_id ?? null,
            is_active: editing.is_active,
          }}
          submitLabel="Saqlash"
          onCancel={() => setEditing(null)}
          onSubmit={async (data) => {
            await api.put(`/users/${editing.id}`, {
              full_name: data.full_name,
              role: data.role,
              branch_id: data.branch_id,
              is_active: data.is_active,
              ...(data.password ? { password: data.password } : {}),
            });
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}
