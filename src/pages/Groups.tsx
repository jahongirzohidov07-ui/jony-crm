import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, X, Pencil } from "lucide-react";
import { api, type Group, type Teacher, type Branch } from "../lib/api";
import { formatSom } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { FULL_ACCESS, can } from "../lib/roles";

function GroupFormModal({
  teachers,
  branches,
  defaultBranchId,
  initial,
  submitLabel,
  onClose,
  onSaved,
}: {
  teachers: Teacher[];
  branches: Branch[];
  defaultBranchId: number | null;
  initial?: Group;
  submitLabel: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [room, setRoom] = useState(initial?.room ?? "");
  const [teacherId, setTeacherId] = useState(
    initial?.teacher_id ? String(initial.teacher_id) : ""
  );
  const [branchId, setBranchId] = useState(
    initial?.branch_id
      ? String(initial.branch_id)
      : defaultBranchId
      ? String(defaultBranchId)
      : ""
  );
  const [lessonPrice, setLessonPrice] = useState(
    String(initial?.lesson_price ?? 40000)
  );
  const [standardLessons, setStandardLessons] = useState(
    String(initial?.standard_lessons_per_month ?? 12)
  );
  const [teacherRate, setTeacherRate] = useState(
    String(initial?.teacher_rate_per_student ?? 0)
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lessonPriceNum = Number(lessonPrice) || 0;
  const standardLessonsNum = Number(standardLessons) || 0;
  const computedMonthlyFee = lessonPriceNum * standardLessonsNum;

  async function submit() {
    if (!name.trim()) {
      setError("Guruh nomini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        name,
        room: room || null,
        teacher_id: teacherId ? Number(teacherId) : null,
        branch_id: branchId ? Number(branchId) : null,
        monthly_fee: computedMonthlyFee,
        lesson_price: lessonPriceNum,
        standard_lessons_per_month: standardLessonsNum,
        teacher_rate_per_student: Number(teacherRate) || 0,
      };
      if (initial) {
        await api.put(`/groups/${initial.id}`, payload);
      } else {
        await api.post("/groups", payload);
      }
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
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {initial ? "Guruhni tahrirlash" : "Yangi guruh"}
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
              placeholder="Masalan: IELTS 1.0"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Xona</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={room}
              onChange={(e) => setRoom(e.target.value)}
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
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">O'qituvchi</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={teacherId}
              onChange={(e) => setTeacherId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {teachers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.full_name}
                </option>
              ))}
            </select>
          </div>

          <div className="border-t border-slate-100 pt-3 mt-1">
            <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
              Dars-asosidagi hisoblash
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  1 dars narxi (so'm)
                </label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={lessonPrice}
                  onChange={(e) => setLessonPrice(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  Standart dars/oy
                </label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={standardLessons}
                  onChange={(e) => setStandardLessons(e.target.value)}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Standart oy narxi: {formatSom(computedMonthlyFee)}. Bundan ortiq
              o'tilgan darslar (masalan 13-14-chi) talabaga bepul hisoblanadi.
            </p>
            <div className="mt-3">
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Ustoz stavkasi (1 talabadan, to'liq oy uchun, so'm)
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={teacherRate}
                onChange={(e) => setTeacherRate(e.target.value)}
              />
              <p className="text-xs text-slate-400 mt-1">
                Ustoz yoqlama qo'ygan darslar soniga qarab shu summadan
                ulush oladi (barcha darsni o'tsa - to'liq summa).
              </p>
            </div>
          </div>

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

export default function Groups() {
  const { user } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Group | null>(null);

  function load() {
    setLoading(true);
    Promise.all([
      api.get<Group[]>("/groups"),
      api.get<Teacher[]>("/teachers"),
      api.get<Branch[]>("/branches"),
    ])
      .then(([g, t, b]) => {
        setGroups(g);
        setTeachers(t);
        setBranches(b);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);
  const canEdit = can(user?.role, FULL_ACCESS);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Guruhlar</h1>
          <p className="text-sm text-slate-500">Jami: {groups.length}</p>
        </div>
        {canEdit && (
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
          >
            <Plus size={16} /> Yangi guruh
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map((g) => (
            <div key={g.id} className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-start justify-between mb-1">
                <Link
                  to={`/groups/${g.id}`}
                  className="font-semibold text-slate-900 hover:text-brand-700"
                >
                  {g.name}
                </Link>
                {canEdit && (
                  <button
                    onClick={() => setEditing(g)}
                    className="text-slate-400 hover:text-brand-600"
                  >
                    <Pencil size={15} />
                  </button>
                )}
              </div>
              <p className="text-sm text-slate-500 mb-3">
                {g.branch?.name || "Filial belgilanmagan"} · {g.room || "Xona belgilanmagan"}
              </p>
              <div className="text-sm space-y-1">
                <p className="text-slate-600">
                  O'qituvchi: <span className="font-medium">{g.teacher?.full_name || "—"}</span>
                </p>
                <p className="text-slate-600">
                  Talabalar: <span className="font-medium">{g.student_count}</span>
                </p>
                <p className="text-slate-600">
                  Oylik to'lov: <span className="font-medium">{formatSom(g.monthly_fee)}</span>
                </p>
              </div>
              <Link
                to={`/groups/${g.id}`}
                className="inline-block mt-3 text-xs font-medium text-brand-600 hover:underline"
              >
                Darslar va hisob-kitob →
              </Link>
            </div>
          ))}
        </div>
      )}

      {showAdd && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          submitLabel="Yaratish"
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          initial={editing}
          submitLabel="Saqlash"
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
    </div>
  );
}
