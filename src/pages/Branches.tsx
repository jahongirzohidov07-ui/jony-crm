import { useEffect, useState } from "react";
import { Plus, X, Building2, Pencil, Trash2 } from "lucide-react";
import { api, type Branch } from "../lib/api";

function BranchModal({
  initial,
  onClose,
  onSaved,
}: {
  initial?: Branch;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editing = !!initial;
  const [name, setName] = useState(initial?.name ?? "");
  const [address, setAddress] = useState(initial?.address ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!name.trim()) {
      setError("Filial nomini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body = { name, address: address || null };
      if (editing) await api.put(`/branches/${initial!.id}`, body);
      else await api.post("/branches", body);
      onSaved();
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
            {editing ? "Filialni tahrirlash" : "Yangi filial"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Nomi *</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Masalan: Bekobod 3"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Manzil</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
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

export default function Branches() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Branch | null>(null);
  const [error, setError] = useState<string | null>(null);

  /** Filialni o'chirish - faqat bo'sh bo'lsa. Aks holda backend
   *  nima to'sqinlik qilayotganini aytadi. */
  async function remove(b: Branch) {
    if (!confirm(`"${b.name}" filiali o'chirilsinmi?`)) return;
    setError(null);
    try {
      await api.delete(`/branches/${b.id}`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  function load() {
    setLoading(true);
    api.get<Branch[]>("/branches").then(setBranches).finally(() => setLoading(false));
  }

  useEffect(load, []);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Filiallar</h1>
          <p className="text-sm text-slate-500">Jami: {branches.length}</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          <Plus size={16} /> Yangi filial
        </button>
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {branches.map((b) => (
            <div key={b.id} className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
                  <Building2 size={18} />
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => setEditing(b)}
                    title="Tahrirlash"
                    className="text-slate-400 hover:text-brand-600 p-1"
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    onClick={() => remove(b)}
                    title="O'chirish"
                    className="text-slate-300 hover:text-red-500 p-1"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
              <h3 className="font-semibold text-slate-900 mb-1">{b.name}</h3>
              <p className="text-sm text-slate-500">{b.address || "Manzil kiritilmagan"}</p>
            </div>
          ))}
        </div>
      )}

      {showAdd && <BranchModal onClose={() => setShowAdd(false)} onSaved={load} />}
      {editing && (
        <BranchModal
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
      {error && (
        <p className="text-sm text-red-600 mt-4">{error}</p>
      )}
    </div>
  );
}
