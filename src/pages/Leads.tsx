import { useEffect, useState } from "react";
import { Plus, X, Trash2, UserPlus, Phone, GripVertical } from "lucide-react";
import { api, getGlobalBranch } from "../lib/api";
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
import PlacementBar, { PlacementBadge } from "../components/PlacementBar";

// ---------------------------------------------------------------- modal ----
function LeadForm({
  branches,
  branchesError,
  onRetryBranches,
  staff,
  defaultBranchId,
  initial,
  onClose,
  onSaved,
}: {
  branches: Branch[];
  branchesError: boolean;
  onRetryBranches: () => void;
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
  const [school, setSchool] = useState(initial?.school ?? "");
  const [grade, setGrade] = useState(initial?.grade ?? "");
  const [note, setNote] = useState(initial?.note ?? "");
  const [branchId, setBranchId] = useState(
    initial?.branch_id ? String(initial.branch_id) : defaultBranchId ? String(defaultBranchId) : ""
  );
  const { user: me } = useAuth();
  // Filial tanlanganda mahalla/maktab ro'yxati o'sha filialga mos
  // almashadi — har filialning o'z hududlari bor (Zafar ro'yxati
  // boshqa filiallarga chiqib turmasin).
  const ref = useReference(
    branchId ? Number(branchId) : me?.branch_id ?? null
  );
  const meIsAdmin =
    me?.role === "administrator" || me?.role === "sales_manager";
  // Xodimning o'z filiali bo'lsa, lid o'sha yerga tushadi — tanlash
  // oynasi ortiqcha. Filialsiz (asoschi, SMM) uchungina chiqadi.
  // MUHIM: bu yerda branches.length > 1 shartini QO'YMAYMIZ — agar
  // filiallar ro'yxati hali yuklanmagan/yuklanmay qolgan bo'lsa ham,
  // backend baribir filial talab qiladi va o'zi hech narsani
  // taxmin qilib bermaydi. Ro'yxatni yashirish shu holatda odamni
  // "filial tanlanmadi" xatosi bilan chiqish yo'li yo'q holatga
  // olib kelardi (aynan shu xato bilan).
  const needBranch = !me?.branch_id;
  // Admin uchun backend o'zi biriktiradi — bu yerda tanlanmaydi.
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
    // Lid to'liq to'ldirilmasa, keyin qaysi mahalladan va qaysi
    // maktabdan ko'p o'quvchi kelayotgani ko'rinmay qoladi — shuning
    // uchun bo'sh qoldirishga yo'l qo'ymaymiz.
    const missing = [
      [fullName.trim(), "Ism-familiya"],
      [(phone ?? "").replace(/\D/g, "").length >= 9 ? "1" : "", "Telefon"],
      [(address ?? "").trim(), "Qayerdan (mahalla / tuman)"],
      [(school ?? "").trim(), "Maktab"],
      [(grade ?? "").trim(), "Sinf"],
      [source, "Qayerdan keldi"],
      [stage, "Bosqich"],
      ...(needBranch ? [[branchId, "Filial"] as [string, string]] : []),
    ].filter(([v]) => !v).map(([, label]) => label);

    if (missing.length) {
      setError(
        missing.length === 1
          ? `"${missing[0]}" to'ldirilmadi`
          : `To'ldirilmadi: ${missing.join(", ")}`
      );
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
      if (!editing && (msg.includes("allaqachon bor") ||
          msg.includes("qayta kiritib qo'ymayapsizmi"))) {
        if (confirm(msg + "\n\nOK — yangi odam, kiritilsin.")) {
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
              Telefon *
            </label>
            <PhoneInput value={phone ?? ""} onChange={setPhone} />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Qayerdan (mahalla / tuman) *
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
                Maktab *
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
                Sinf *
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
              Qayerdan keldi *
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
              Bosqich *
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

          {/* Adminga "mas'ul xodim" ko'rsatilmaydi — u baribir o'zi
              bo'ladi va buni admin biladi. Rahbar boshqaga biriktirishi
              mumkin, shuning uchun unga ro'yxat chiqadi. */}
          {!meIsAdmin && (
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
          )}

          {/* Filiali bor xodimning lidi o'z filialiga tushadi — tanlash
              shart emas. Faqat butun tashkilotni ko'radiganlar (asoschi,
              SMM) uchun ro'yxat chiqadi. */}
          {needBranch && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Filial *
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={branchId}
                onChange={(e) => setBranchId(e.target.value)}
                disabled={branches.length === 0}
              >
                <option value="">— tanlanmagan —</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
              {branches.length === 0 && (
                <p className="text-[11px] text-amber-600 mt-1">
                  {branchesError ? (
                    <>
                      Filiallar ro'yxati yuklanmadi.{" "}
                      <button
                        type="button"
                        onClick={onRetryBranches}
                        className="underline"
                      >
                        Qayta urinish
                      </button>
                    </>
                  ) : (
                    "Filiallar yuklanmoqda..."
                  )}
                </p>
              )}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Izoh (ixtiyoriy)
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
        <PlacementBadge lead={lead} />
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
  const [branchesError, setBranchesError] = useState(false);
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

  function loadBranches() {
    setBranchesError(false);
    api
      .get<Branch[]>("/branches")
      .then(setBranches)
      .catch(() => setBranchesError(true));
  }

  useEffect(() => {
    load();
    loadBranches();
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

  // LIDNI O'CHIRISH — SABAB BILAN (2026-08-30, Jahongir: "lidni
  // o'chirishni ham sabablar qo'shib qo'y, ichida ADASHIB KIRITILIB
  // YUBORILIBDI bo'lsin").
  //
  // Nega muhim: "adashib kiritilgan" yozuv umuman lid EMAS edi, uni
  // yo'qotish deb sanash statistikani buzadi. "Qiziqmadi" esa
  // haqiqiy yo'qotish. Ikkalasini ajratmasak, voronka yolg'on
  // gapiradi.
  //
  // Yozuv o'chmaydi — arxivga ko'chadi va kerak bo'lsa qaytariladi.
  const [delLead, setDelLead] = useState<Lead | null>(null);
  const [delReason, setDelReason] = useState("");
  const [delNote, setDelNote] = useState("");
  const [delList, setDelList] = useState<
    { key: string; label: string; real_loss: boolean }[]>([]);
  const [delBusy, setDelBusy] = useState(false);

  useEffect(() => {
    api.get<{ rows: { key: string; label: string; real_loss: boolean }[] }>(
      "/leads/delete-reasons")
      .then((r) => setDelList(r.rows || []))
      .catch(() => setDelList([]));
  }, []);

  function remove(lead: Lead) {
    setDelLead(lead);
    setDelReason("");
    setDelNote("");
  }

  async function confirmRemove() {
    if (!delLead || !delReason) return;
    setDelBusy(true);
    try {
      const q = `reason=${encodeURIComponent(delReason)}`
        + (delNote.trim() ? `&note=${encodeURIComponent(delNote.trim())}` : "");
      await api.delete(`/leads/${delLead.id}?${q}`);
      setLeads((prev) => prev.filter((l) => l.id !== delLead.id));
      setDelLead(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setDelBusy(false);
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
      {delLead && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="font-semibold text-slate-900 mb-1">
              Lidni o'chirish
            </h2>
            <p className="text-sm text-slate-600 mb-1">
              <b>{delLead.full_name}</b>
              {delLead.phone ? ` · ${delLead.phone}` : ""}
            </p>
            <p className="text-[11px] text-slate-500 mb-3">
              Yozuv arxivga ko'chadi — kerak bo'lsa qaytariladi.
              Sabab statistika uchun majburiy.
            </p>
            <select
              value={delReason}
              onChange={(e) => setDelReason(e.target.value)}
              className={`w-full rounded-lg border px-3 py-2.5 text-sm bg-white mb-2 ${
                delReason ? "border-brand-400" : "border-slate-300"}`}
            >
              <option value="">— o'chirish sababini tanlang —</option>
              {delList.map((r) => (
                <option key={r.key} value={r.key}>{r.label}</option>
              ))}
            </select>
            {delReason && !(delList.find((r) => r.key === delReason)
              ?.real_loss) && (
              <p className="text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-2">
                Bu yozuv haqiqiy lid emas edi — voronka statistikasida
                yo'qotish deb sanalmaydi.
              </p>
            )}
            <input
              value={delNote}
              onChange={(e) => setDelNote(e.target.value)}
              placeholder="Qo'shimcha izoh (ixtiyoriy)"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-3"
            />
            <div className="flex gap-2">
              <button onClick={() => setDelLead(null)}
                className="flex-1 rounded-lg border border-slate-300 py-2 text-sm text-slate-600">
                Bekor
              </button>
              <button onClick={confirmRemove}
                disabled={!delReason || delBusy}
                className="flex-1 rounded-lg bg-red-600 text-white py-2 text-sm font-medium disabled:opacity-40">
                {delBusy ? "O'chirilmoqda…" : "O'chirish"}
              </button>
            </div>
          </div>
        </div>
      )}
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

      <PlacementBar leads={leads} onChanged={load} />
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
          branchesError={branchesError}
          onRetryBranches={loadBranches}
          staff={staff}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          onClose={() => setShowNew(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <LeadForm
          branches={branches}
          branchesError={branchesError}
          onRetryBranches={loadBranches}
          staff={staff}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
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
