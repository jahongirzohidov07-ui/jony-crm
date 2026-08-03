import { useEffect, useState } from "react";
import { Plus, X, Trash2, UserPlus, Phone, GripVertical } from "lucide-react";
import { api } from "../lib/api";
import type { Lead, Branch, StaffOption, Group } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FULL_ACCESS, LEAD_ACCESS, can } from "../lib/roles";
import {
  LEAD_STAGES,
  LEAD_SOURCES,
  SOURCE_DEFAULT_STAGE,
  GRADES,
  sourceLabel,
} from "../lib/leads";
import type { LeadSource, LeadStage } from "../lib/leads";
import { PhoneInput, formatPhone } from "../components/PhoneInput";
import { PickList, useReference } from "../components/PickList";

// ---------------------------------------------------------------- modal ----
function LeadForm({
  branches,
  staff,
  defaultBranchId,
  initial,
  onClose,
  onSaved,
}: {
  branches: Branch[];
  staff: StaffOption[];
  defaultBranchId: number | null;
  initial?: Lead;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editing = !!initial;
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [phone, setPhone] = useState(initial?.phone ?? "");
  const [source, setSource] = useState<LeadSource>(
    (initial?.source as LeadSource) ?? "visit"
  );
  const [stage, setStage] = useState<LeadStage>(
    (initial?.stage as LeadStage) ?? SOURCE_DEFAULT_STAGE.visit
  );
  // Foydalanuvchi bosqichni qo'lda o'zgartirsa, manba almashganda uni
  // qayta bosib ketmaymiz.
  const [stageTouched, setStageTouched] = useState(editing);
  const [address, setAddress] = useState(initial?.address ?? "");
  const ref = useReference();
  const [school, setSchool] = useState(initial?.school ?? "");
  const [grade, setGrade] = useState(initial?.grade ?? "");
  const [note, setNote] = useState(initial?.note ?? "");
  const [branchId, setBranchId] = useState(
    initial?.branch_id ? String(initial.branch_id) : defaultBranchId ? String(defaultBranchId) : ""
  );
  const [assignedId, setAssignedId] = useState(
    initial?.assigned_user_id ? String(initial.assigned_user_id) : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function pickSource(s: LeadSource) {
    setSource(s);
    if (!stageTouched) setStage(SOURCE_DEFAULT_STAGE[s]);
  }

  // Aylantirilgan lidni qo'lda "converted" ga qaytarib bo'lmaydi - backend
  // ham buni rad etadi, shuning uchun ro'yxatdan olib tashlaymiz.
  const stageOptions = LEAD_STAGES.filter(
    (s) => s.key !== "converted" || initial?.converted_student_id
  );

  async function save() {
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
        source,
        stage,
        address: address || null,
        school: school || null,
        grade: grade || null,
        note: note || null,
        branch_id: branchId ? Number(branchId) : null,
        assigned_user_id: assignedId ? Number(assignedId) : null,
      };
      if (editing) await api.put(`/leads/${initial!.id}`, body);
      else await api.post("/leads", body);
      onSaved();
      onClose();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Xatolik";
      // Dublikat: shu telefon bilan lid/o'quvchi bor — tasdiq so'raymiz
      if (!editing && msg.includes("allaqachon bor")) {
        if (confirm(msg)) {
          try {
            await api.post("/leads", {
              full_name: fullName,
              phone: phone || null,
              source,
              stage,
              address: address || null,
              school: school || null,
              grade: grade || null,
              note: note || null,
              branch_id: branchId ? Number(branchId) : null,
              assigned_user_id: assignedId ? Number(assignedId) : null,
              force: true,
            });
            onSaved();
            onClose();
          } catch (e2) {
            setError(e2 instanceof Error ? e2.message : "Xatolik");
          } finally {
            setSaving(false);
          }
          return;
        }
      }
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {editing ? "Lidni tahrirlash" : "Yangi lid"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Ism-familiya *
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
              Telefon
            </label>
            <PhoneInput value={phone ?? ""} onChange={setPhone} />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Qayerdan (mahalla / tuman)
            </label>
            <PickList
              value={address ?? ""}
              onChange={setAddress}
              options={ref?.areas ?? []}
              placeholder="— mahallani tanlang —"
            />
            <p className="text-xs text-slate-400 mt-1">
              Ro'yxatdan tanlang — shundagina qaysi mahalladan ko'p o'quvchi
              kelayotgani ko'rinadi.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Maktab
              </label>
              <PickList
                value={school ?? ""}
                onChange={setSchool}
                options={ref?.schools ?? []}
                placeholder="— tanlang —"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Sinf
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={grade ?? ""}
                onChange={(e) => setGrade(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {GRADES.map((g) => (
                  <option key={g} value={g}>
                    {g === "Kattalar" ? g : `${g}-sinf`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Qayerdan keldi
            </label>
            <div className="flex flex-wrap gap-1.5">
              {LEAD_SOURCES.map((s) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => pickSource(s.key)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                    source === s.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Bosqich
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={stage}
              onChange={(e) => {
                setStage(e.target.value as LeadStage);
                setStageTouched(true);
              }}
            >
              {stageOptions.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
            {!editing && !stageTouched && (
              <p className="text-xs text-slate-400 mt-1">
                Manbaga qarab avtomatik tanlandi — o'zgartirsangiz ham bo'ladi
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Mas'ul xodim
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={assignedId}
              onChange={(e) => setAssignedId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {staff.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.full_name}
                </option>
              ))}
            </select>
          </div>

          {branches.length > 1 && (
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
          )}

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Izoh
            </label>
            <textarea
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              rows={2}
              value={note ?? ""}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Masalan: kechqurungi guruhni so'radi"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-1 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : editing ? "Saqlash" : "Qo'shish"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConvertModal({
  lead,
  groups,
  onClose,
  onDone,
}: {
  lead: Lead;
  groups: Group[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [groupId, setGroupId] = useState("");
  const [enrolled, setEnrolled] = useState(() =>
    new Date().toISOString().slice(0, 10)
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function convert() {
    setSaving(true);
    setError(null);
    try {
      await api.post(`/leads/${lead.id}/convert`, {
        group_id: groupId ? Number(groupId) : null,
        enrolled_date: enrolled || null,
      });
      onDone();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-semibold text-slate-900">O'quvchiga aylantirish</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">
          <span className="font-medium text-slate-700">{lead.full_name}</span> Talabalar
          bo'limiga qo'shiladi. Lid voronkada qoladi, statistikasi saqlanadi.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Guruh
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
            >
              <option value="">— keyinroq biriktiraman —</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Qo'shilgan sana
            </label>
            <input
              type="date"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={enrolled}
              onChange={(e) => setEnrolled(e.target.value)}
            />
            <p className="text-xs text-slate-400 mt-1">
              To'lov shu sanadan boshlab hisoblanadi
            </p>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={convert}
            disabled={saving}
            className="w-full bg-green-600 hover:bg-green-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Aylantirilmoqda..." : "Tasdiqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------- card ----
function LeadCard({
  lead,
  canDelete,
  onEdit,
  onConvert,
  onDelete,
  onDragStart,
  dragging,
}: {
  lead: Lead;
  canDelete: boolean;
  onEdit: () => void;
  onConvert: () => void;
  onDelete: () => void;
  onDragStart: () => void;
  dragging: boolean;
}) {
  const converted = !!lead.converted_student_id;
  return (
    <div
      draggable
      onDragStart={onDragStart}
      onClick={onEdit}
      className={`group bg-white rounded-lg border border-slate-200 p-3 cursor-pointer hover:border-brand-300 hover:shadow-sm transition ${
        dragging ? "opacity-40" : ""
      }`}
    >
      <div className="flex items-start gap-1.5">
        <GripVertical
          size={14}
          className="text-slate-300 shrink-0 mt-0.5 cursor-grab"
        />
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-800 text-sm truncate">
            {lead.full_name}
          </p>
          {lead.phone && (
            <a
              href={`tel:${lead.phone}`}
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-brand-600 mt-0.5"
            >
              <Phone size={11} />
              {formatPhone(lead.phone)}
            </a>
          )}
        </div>
      </div>

      {(lead.school || lead.grade || lead.address) && (
        <p className="text-xs text-slate-500 mt-1.5 truncate">
          {[
            lead.school,
            lead.grade
              ? lead.grade === "Kattalar"
                ? lead.grade
                : `${lead.grade}-sinf`
              : null,
            lead.address,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      )}

      <div className="flex items-center flex-wrap gap-1 mt-2">
        <span className="inline-block bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 text-[11px]">
          {sourceLabel(lead.source)}
        </span>
        {lead.assigned_user && (
          <span className="inline-block bg-brand-50 text-brand-700 rounded px-1.5 py-0.5 text-[11px] truncate max-w-[110px]">
            {lead.assigned_user.full_name}
          </span>
        )}
      </div>

      {lead.note && (
        <p className="text-xs text-slate-400 mt-1.5 line-clamp-2">{lead.note}</p>
      )}

      <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition">
        {!converted && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onConvert();
            }}
            className="flex items-center gap-1 text-[11px] font-medium text-green-700 hover:underline"
          >
            <UserPlus size={12} /> O'quvchiga
          </button>
        )}
        {converted && (
          <span className="text-[11px] text-green-600">✓ Talabalarda</span>
        )}
        {canDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="ml-auto text-slate-300 hover:text-red-500"
          >
            <Trash2 size={12} />
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- page -----
export default function Leads() {
  const { user } = useAuth();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [staff, setStaff] = useState<StaffOption[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [editing, setEditing] = useState<Lead | null>(null);
  const [converting, setConverting] = useState<Lead | null>(null);
  const [dragId, setDragId] = useState<number | null>(null);
  const [overStage, setOverStage] = useState<string | null>(null);

  function load() {
    setLoading(true);
    api
      .get<Lead[]>("/leads")
      .then(setLeads)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
    api.get<StaffOption[]>("/users/assignable").then(setStaff).catch(() => {});
    api.get<Group[]>("/groups").then(setGroups).catch(() => {});
  }, []);

  const allowed = can(user?.role, LEAD_ACCESS);
  const canDelete = can(user?.role, FULL_ACCESS);

  async function moveTo(lead: Lead, stage: LeadStage) {
    if (lead.stage === stage) return;
    if (stage === "converted") {
      // Bu bosqichga faqat aylantirish orqali o'tiladi.
      setConverting(lead);
      return;
    }
    // Optimistik yangilash - doska darrov javob bersin.
    setLeads((prev) =>
      prev.map((l) => (l.id === lead.id ? { ...l, stage } : l))
    );
    try {
      await api.put(`/leads/${lead.id}`, { stage });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
      load();
    }
  }

  async function remove(lead: Lead) {
    if (!confirm(`"${lead.full_name}" lidini o'chirasizmi?`)) return;
    try {
      await api.delete(`/leads/${lead.id}`);
      setLeads((prev) => prev.filter((l) => l.id !== lead.id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (!allowed) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  const openCount = leads.filter(
    (l) => l.stage !== "converted" && l.stage !== "rejected"
  ).length;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Lidlar</h1>
          <p className="text-sm text-slate-500">
            Jami: {leads.length} · Jarayonda: {openCount}
          </p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          <Plus size={16} /> Yangi lid
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
      {loading && <p className="text-slate-400 text-sm">Yuklanmoqda...</p>}

      {!loading && (
        <div className="flex gap-3 overflow-x-auto pb-4">
          {LEAD_STAGES.map((st) => {
            const items = leads.filter((l) => l.stage === st.key);
            return (
              <div
                key={st.key}
                onDragOver={(e) => {
                  e.preventDefault();
                  setOverStage(st.key);
                }}
                onDragLeave={() => setOverStage((s) => (s === st.key ? null : s))}
                onDrop={(e) => {
                  e.preventDefault();
                  setOverStage(null);
                  const lead = leads.find((l) => l.id === dragId);
                  if (lead) moveTo(lead, st.key);
                  setDragId(null);
                }}
                className={`w-64 shrink-0 rounded-xl p-2 transition ${
                  overStage === st.key ? "bg-brand-50/70 ring-2 ring-brand-300" : "bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between px-1.5 py-1.5 mb-1">
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-semibold ${st.tone}`}
                  >
                    {st.label}
                  </span>
                  <span className="text-xs font-medium text-slate-400">
                    {items.length}
                  </span>
                </div>

                <div className="space-y-2 min-h-[60px]">
                  {items.map((l) => (
                    <LeadCard
                      key={l.id}
                      lead={l}
                      canDelete={canDelete}
                      dragging={dragId === l.id}
                      onDragStart={() => setDragId(l.id)}
                      onEdit={() => setEditing(l)}
                      onConvert={() => setConverting(l)}
                      onDelete={() => remove(l)}
                    />
                  ))}
                  {items.length === 0 && (
                    <p className="text-xs text-slate-300 text-center py-4">
                      Bo'sh
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showNew && (
        <LeadForm
          branches={branches}
          staff={staff}
          defaultBranchId={user?.branch_id ?? null}
          onClose={() => setShowNew(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <LeadForm
          branches={branches}
          staff={staff}
          defaultBranchId={user?.branch_id ?? null}
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
      {converting && (
        <ConvertModal
          lead={converting}
          groups={groups}
          onClose={() => setConverting(null)}
          onDone={load}
        />
      )}
    </div>
  );
}
