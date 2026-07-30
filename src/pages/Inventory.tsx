import { useEffect, useState } from "react";
import {
  Package, Plus, X, Trash2, Wrench, ShoppingCart, AlertTriangle,
  ArrowDownUp, Shield,
} from "lucide-react";
import {
  api, type AssetList, type AssetRow, type ConsumableList,
  type ConsumableRow, type StockMoveRow, type User, type Room,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { INVENTORY_VIEW, can } from "../lib/roles";
import { formatSom, formatDate } from "../lib/format";
import { BranchPicker, branchParam } from "../components/BranchPicker";

const TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-500",
};

type Tab = "assets" | "stock";

export default function Inventory() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("assets");
  const [branchId, setBranchId] = useState<number | null>(null);

  if (!can(user?.role, INVENTORY_VIEW)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Package size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Ombor va aktivlar
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Har bir jihozda inventar raqami va mas'ul xodim bor
      </p>

      <div className="flex items-center gap-2 mb-5">
        {[
          { k: "assets", l: "Aktivlar" },
          { k: "stock", l: "Sarflanadigan" },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setTab(t.k as Tab)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === t.k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {t.l}
          </button>
        ))}
        <BranchPicker value={branchId} onChange={setBranchId} />
      </div>

      {tab === "assets" ? (
        <Assets branchId={branchId} />
      ) : (
        <Stock branchId={branchId} />
      )}
    </div>
  );
}

// ============================================================== Aktivlar
function Assets({ branchId }: { branchId: number | null }) {
  const [data, setData] = useState<AssetList | null>(null);
  const [staff, setStaff] = useState<User[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [kind, setKind] = useState("");
  const [form, setForm] = useState(false);
  const [edit, setEdit] = useState<AssetRow | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<AssetList>(`/assets?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }

  useEffect(load, [branchId]);
  useEffect(() => {
    api.get<User[]>("/users").then(setStaff).catch(() => setStaff([]));
    api.get<Room[]>("/rooms").then(setRooms).catch(() => setRooms([]));
  }, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const rows = kind ? data.rows.filter((r) => r.kind === kind) : data.rows;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Jami jihoz</p>
          <p className="text-xl font-semibold text-slate-900">{data.count}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Umumiy qiymat</p>
          <p className="text-xl font-semibold text-slate-900">
            {formatSom(data.total_value)}
          </p>
        </div>
        <div
          className={`rounded-xl border p-4 ${
            data.needs_attention > 0
              ? "bg-amber-50 border-amber-200"
              : "bg-white border-slate-200"
          }`}
        >
          <p className="text-xs text-slate-500 mb-1">Ta'mir kerak</p>
          <p
            className={`text-xl font-semibold ${
              data.needs_attention > 0 ? "text-amber-700" : "text-slate-900"
            }`}
          >
            {data.needs_attention}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <button
          onClick={() => setKind("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
            !kind
              ? "bg-brand-50 border-brand-400 text-brand-700"
              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
          }`}
        >
          Hammasi
        </button>
        {data.kinds
          .filter((k) => k.count > 0)
          .map((k) => (
            <button
              key={k.key}
              onClick={() => setKind(kind === k.key ? "" : k.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                kind === k.key
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {k.label} <span className="text-slate-400">{k.count}</span>
            </button>
          ))}
        <div className="flex-1" />
        {data.can_edit && (
          <button
            onClick={() => {
              setEdit(null);
              setForm(true);
            }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            <Plus size={15} /> Aktiv
          </button>
        )}
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Aktiv yo'q.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5 w-24">Inventar</th>
                <th className="text-left">Nomi</th>
                <th className="text-left">Turi</th>
                <th className="text-left">Xona</th>
                <th className="text-left">Mas'ul</th>
                <th className="text-right">Narxi</th>
                <th className="text-left w-32">Holati</th>
                <th className="w-20" />
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <>
                  <tr key={a.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5">
                      <button
                        onClick={() => setOpen(open === a.id ? null : a.id)}
                        className="font-mono text-xs text-brand-700 hover:underline"
                      >
                        {a.inventory_no}
                      </button>
                    </td>
                    <td className="text-slate-800">{a.name}</td>
                    <td className="text-slate-500">{a.kind_label}</td>
                    <td className="text-slate-500">{a.room || "—"}</td>
                    <td className="text-slate-500">{a.responsible || "—"}</td>
                    <td className="text-right text-slate-600">
                      {a.price ? formatSom(a.price) : "—"}
                    </td>
                    <td>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          TONE[a.condition_tone] || TONE.slate
                        }`}
                      >
                        {a.condition_label}
                      </span>
                      {a.warranty_active && (
                        <Shield
                          size={12}
                          className="inline ml-1.5 text-emerald-500"
                        />
                      )}
                    </td>
                    <td className="pr-3">
                      {data.can_edit && (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => {
                              setEdit(a);
                              setForm(true);
                            }}
                            className="p-1.5 rounded-md text-slate-300 hover:text-brand-600 hover:bg-slate-50"
                            title="Tahrirlash"
                          >
                            <Wrench size={14} />
                          </button>
                          <button
                            onClick={async () => {
                              if (!confirm(`${a.name} o'chirilsinmi?`)) return;
                              await api.delete(`/assets/${a.id}`);
                              load();
                            }}
                            className="p-1.5 rounded-md text-slate-300 hover:text-red-600 hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                  {open === a.id && (
                    <tr key={`${a.id}-d`}>
                      <td colSpan={8} className="bg-slate-50 px-4 py-3">
                        <AssetDetail
                          a={a}
                          canEdit={data.can_edit}
                          onDone={load}
                        />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {form && (
        <AssetForm
          asset={edit}
          kinds={data.kinds}
          conditions={data.conditions}
          staff={staff}
          rooms={rooms}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function AssetDetail({
  a,
  canEdit,
  onDone,
}: {
  a: AssetRow;
  canEdit: boolean;
  onDone: () => void;
}) {
  const [repair, setRepair] = useState(false);
  const [cost, setCost] = useState("");
  const [vendor, setVendor] = useState("");
  const [note, setNote] = useState("");

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div>
          <p className="text-slate-500">Sotib olingan</p>
          <p className="text-slate-800">
            {a.purchased_on ? formatDate(a.purchased_on) : "—"}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Kafolat</p>
          <p
            className={
              a.warranty_active ? "text-emerald-700" : "text-slate-800"
            }
          >
            {a.warranty_until ? formatDate(a.warranty_until) : "—"}
          </p>
        </div>
        <div>
          <p className="text-slate-500">Seriya raqami</p>
          <p className="text-slate-800 font-mono">{a.serial_no || "—"}</p>
        </div>
        <div>
          <p className="text-slate-500">Ta'mir xarajati</p>
          <p className="text-slate-800">
            {a.repair_cost ? formatSom(a.repair_cost) : "—"}
          </p>
        </div>
      </div>

      {a.replace_hint && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-start gap-2">
          <AlertTriangle size={14} className="text-amber-600 mt-0.5 shrink-0" />
          <p className="text-xs text-amber-900">
            Ta'mirga {formatSom(a.repair_cost)} ketdi — bu jihoz narxining
            yarmidan ko'p. Yangisini olish arzonroq bo'lishi mumkin.
          </p>
        </div>
      )}

      {a.note && <p className="text-xs text-slate-600">{a.note}</p>}

      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <p className="text-xs font-medium text-slate-700">
            Ta'mirlash tarixi
          </p>
          {canEdit && (
            <button
              onClick={() => setRepair(!repair)}
              className="text-xs text-brand-600 hover:underline"
            >
              + ta'mir qo'shish
            </button>
          )}
        </div>

        {repair && (
          <div className="flex flex-wrap gap-2 mb-2">
            <input
              type="number"
              value={cost}
              onChange={(e) => setCost(e.target.value)}
              placeholder="Narxi"
              className="w-28 px-2 py-1.5 rounded-lg border border-slate-200 text-xs"
            />
            <input
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
              placeholder="Ustaxona"
              className="w-36 px-2 py-1.5 rounded-lg border border-slate-200 text-xs"
            />
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Nima qilindi"
              className="flex-1 min-w-40 px-2 py-1.5 rounded-lg border border-slate-200 text-xs"
            />
            <button
              onClick={async () => {
                await api.post(`/assets/${a.id}/repairs`, {
                  cost: Number(cost) || 0,
                  vendor: vendor || null,
                  note: note || null,
                });
                setRepair(false);
                setCost("");
                setVendor("");
                setNote("");
                onDone();
              }}
              className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-medium"
            >
              Saqlash
            </button>
          </div>
        )}

        {a.repairs.length === 0 ? (
          <p className="text-xs text-slate-400">Ta'mirlanmagan</p>
        ) : (
          <div className="space-y-1">
            {a.repairs.map((r) => (
              <div
                key={r.id}
                className="flex items-center gap-3 text-xs text-slate-600"
              >
                <span className="text-slate-400 w-24">
                  {r.date ? formatDate(r.date) : "—"}
                </span>
                <span className="w-24">
                  {r.cost ? formatSom(r.cost) : "—"}
                </span>
                <span className="text-slate-500">{r.vendor}</span>
                <span className="flex-1">{r.note}</span>
                {canEdit && a.condition === "repair" && (
                  <button
                    onClick={async () => {
                      await api.post(`/assets/repairs/${r.id}/done`, {});
                      onDone();
                    }}
                    className="text-emerald-600 hover:underline"
                  >
                    ta'mir tugadi
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AssetForm({
  asset,
  kinds,
  conditions,
  staff,
  rooms,
  onClose,
  onSaved,
}: {
  asset: AssetRow | null;
  kinds: { key: string; label: string }[];
  conditions: { key: string; label: string }[];
  staff: User[];
  rooms: Room[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    name: asset?.name ?? "",
    kind: asset?.kind ?? "other",
    room_id: asset?.room_id ? String(asset.room_id) : "",
    responsible_id: asset?.responsible_id ? String(asset.responsible_id) : "",
    purchased_on: asset?.purchased_on ?? "",
    price: asset?.price ? String(asset.price) : "",
    condition: asset?.condition ?? "good",
    warranty_until: asset?.warranty_until ?? "",
    serial_no: asset?.serial_no ?? "",
    note: asset?.note ?? "",
  });
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  function set(k: string, v: string) {
    setF({ ...f, [k]: v });
  }

  async function save() {
    if (!f.name.trim()) {
      setErr("Nomini yozing");
      return;
    }
    setSaving(true);
    const body = {
      name: f.name.trim(),
      kind: f.kind,
      room_id: f.room_id ? Number(f.room_id) : null,
      responsible_id: f.responsible_id ? Number(f.responsible_id) : null,
      purchased_on: f.purchased_on || null,
      price: f.price ? Number(f.price) : null,
      condition: f.condition,
      warranty_until: f.warranty_until || null,
      serial_no: f.serial_no || null,
      note: f.note || null,
    };
    try {
      if (asset) await api.put(`/assets/${asset.id}`, body);
      else await api.post("/assets", body);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-16 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-lg p-5 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800">
            {asset ? asset.inventory_no : "Yangi aktiv"}
          </h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <input
            value={f.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="Nomi (masalan Epson EB-S41)"
            autoFocus
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <div className="grid grid-cols-2 gap-3">
            <Field label="Turi">
              <select
                value={f.kind}
                onChange={(e) => set("kind", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                {kinds.map((k) => (
                  <option key={k.key} value={k.key}>
                    {k.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Holati">
              <select
                value={f.condition}
                onChange={(e) => set("condition", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                {conditions.map((c) => (
                  <option key={c.key} value={c.key}>
                    {c.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Xona">
              <select
                value={f.room_id}
                onChange={(e) => set("room_id", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— tanlang —</option>
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Mas'ul xodim">
              <select
                value={f.responsible_id}
                onChange={(e) => set("responsible_id", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— tanlang —</option>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Sotib olingan sana">
              <input
                type="date"
                value={f.purchased_on}
                onChange={(e) => set("purchased_on", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
            <Field label="Narxi">
              <input
                type="number"
                value={f.price}
                onChange={(e) => set("price", e.target.value)}
                placeholder="4500000"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
            <Field label="Kafolat tugashi">
              <input
                type="date"
                value={f.warranty_until}
                onChange={(e) => set("warranty_until", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
            <Field label="Seriya raqami">
              <input
                value={f.serial_no}
                onChange={(e) => set("serial_no", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
          </div>
          <input
            value={f.note}
            onChange={(e) => set("note", e.target.value)}
            placeholder="Izoh"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <button
            onClick={save}
            disabled={saving}
            className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      {children}
    </div>
  );
}

// =================================================== Sarflanadigan mahsulot
function Stock({ branchId }: { branchId: number | null }) {
  const [data, setData] = useState<ConsumableList | null>(null);
  const [form, setForm] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<ConsumableList>(`/consumables?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }

  useEffect(load, [branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  return (
    <div>
      {data.requests.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-2">
            <ShoppingCart size={15} className="text-amber-600" />
            <p className="text-sm font-medium text-amber-900">
              {data.requests.length} ta xarid so'rovi
            </p>
            <span className="text-xs text-amber-700">
              tizim o'zi yaratdi — qoldiq minimaldan pastga tushdi
            </span>
          </div>
          <div className="space-y-1.5">
            {data.requests.map((r) => (
              <div key={r.id} className="flex items-center gap-3 text-sm">
                <span className="text-amber-900 flex-1">{r.name}</span>
                <span className="text-amber-800">{r.qty} dona kerak</span>
                {data.can_edit && (
                  <>
                    <button
                      onClick={async () => {
                        const q = prompt("Nechta keldi?", String(r.qty));
                        if (!q) return;
                        await api.post(`/purchase-requests/${r.id}/close`, {
                          status: "done",
                          qty: Number(q),
                        });
                        load();
                      }}
                      className="text-xs px-2 py-1 rounded-md bg-emerald-600 text-white"
                    >
                      Keldi
                    </button>
                    <button
                      onClick={async () => {
                        await api.post(`/purchase-requests/${r.id}/close`, {
                          status: "cancelled",
                        });
                        load();
                      }}
                      className="text-xs text-amber-700 hover:underline"
                    >
                      kerak emas
                    </button>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Nomenklatura</p>
          <p className="text-xl font-semibold text-slate-900">
            {data.rows.length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Ombor qiymati</p>
          <p className="text-xl font-semibold text-slate-900">
            {formatSom(data.total_value)}
          </p>
        </div>
        <div
          className={`rounded-xl border p-4 ${
            data.low_count > 0
              ? "bg-red-50 border-red-200"
              : "bg-white border-slate-200"
          }`}
        >
          <p className="text-xs text-slate-500 mb-1">Kam qolgan</p>
          <p
            className={`text-xl font-semibold ${
              data.low_count > 0 ? "text-red-700" : "text-slate-900"
            }`}
          >
            {data.low_count}
          </p>
        </div>
      </div>

      {data.can_edit && (
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setForm(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            <Plus size={15} /> Mahsulot
          </button>
        </div>
      )}

      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Mahsulot yo'q.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Nomi</th>
                <th className="text-left">Turi</th>
                <th className="text-right w-24">Qoldiq</th>
                <th className="text-right w-24">Minimal</th>
                <th className="text-right w-28">Qiymati</th>
                <th className="w-40" />
              </tr>
            </thead>
            <tbody>
              {data.rows.map((c) => (
                <>
                  <tr
                    key={c.id}
                    className={`border-t border-slate-100 ${
                      c.low ? "bg-red-50/40" : ""
                    }`}
                  >
                    <td className="px-4 py-2.5">
                      <button
                        onClick={() => setOpen(open === c.id ? null : c.id)}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {c.name}
                      </button>
                      {c.low && (
                        <AlertTriangle
                          size={12}
                          className="inline ml-1.5 text-red-500"
                        />
                      )}
                    </td>
                    <td className="text-slate-500">{c.kind_label}</td>
                    <td
                      className={`text-right font-medium ${
                        c.low ? "text-red-600" : "text-slate-700"
                      }`}
                    >
                      {c.qty} {c.unit}
                    </td>
                    <td className="text-right text-slate-400">{c.min_qty}</td>
                    <td className="text-right text-slate-600">
                      {c.value ? formatSom(c.value) : "—"}
                    </td>
                    <td className="pr-4">
                      {data.can_edit && (
                        <MoveButtons c={c} reasons={data.reasons} onDone={load} />
                      )}
                    </td>
                  </tr>
                  {open === c.id && (
                    <tr key={`${c.id}-m`}>
                      <td colSpan={6} className="bg-slate-50 px-4 py-3">
                        <Moves id={c.id} />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {form && (
        <ConsumableForm
          kinds={data.kinds}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function MoveButtons({
  c,
  reasons,
  onDone,
}: {
  c: ConsumableRow;
  reasons: { key: string; label: string }[];
  onDone: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [qty, setQty] = useState("");
  const [reason, setReason] = useState("out");
  const [err, setErr] = useState("");

  async function save() {
    if (!qty) return;
    try {
      await api.post(`/consumables/${c.id}/move`, {
        qty: Number(qty),
        reason,
      });
      setOpen(false);
      setQty("");
      setErr("");
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (!open)
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1 text-xs text-brand-600 hover:underline ml-auto"
      >
        <ArrowDownUp size={12} /> kirim / chiqim
      </button>
    );

  return (
    <div className="flex items-center gap-1.5">
      <select
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="px-1.5 py-1 rounded border border-slate-200 text-xs bg-white"
      >
        {reasons.map((r) => (
          <option key={r.key} value={r.key}>
            {r.label}
          </option>
        ))}
      </select>
      <input
        type="number"
        value={qty}
        onChange={(e) => setQty(e.target.value)}
        placeholder="0"
        autoFocus
        onKeyDown={(e) => e.key === "Enter" && save()}
        className={`w-16 px-1.5 py-1 rounded border text-xs ${
          err ? "border-red-400" : "border-slate-200"
        }`}
        title={err}
      />
      <button
        onClick={save}
        className="px-2 py-1 rounded bg-brand-600 text-white text-xs"
      >
        OK
      </button>
      <button
        onClick={() => {
          setOpen(false);
          setErr("");
        }}
        className="text-slate-400"
      >
        <X size={13} />
      </button>
    </div>
  );
}

function Moves({ id }: { id: number }) {
  const [rows, setRows] = useState<StockMoveRow[]>([]);
  useEffect(() => {
    api.get<StockMoveRow[]>(`/consumables/${id}/moves`).then(setRows);
  }, [id]);

  if (rows.length === 0)
    return <p className="text-xs text-slate-400">Harakat yo'q</p>;

  return (
    <div className="space-y-1">
      {rows.map((m) => (
        <div key={m.id} className="flex items-center gap-3 text-xs">
          <span className="text-slate-400 w-32">
            {m.created_at ? formatDate(m.created_at) : "—"}
          </span>
          <span
            className={`w-16 font-medium ${
              m.delta > 0 ? "text-emerald-600" : "text-red-600"
            }`}
          >
            {m.delta > 0 ? "+" : ""}
            {m.delta}
          </span>
          <span className="text-slate-500 w-20">{m.reason_label}</span>
          <span className="text-slate-600 flex-1">{m.note}</span>
          <span className="text-slate-400">{m.by}</span>
        </div>
      ))}
    </div>
  );
}

function ConsumableForm({
  kinds,
  onClose,
  onSaved,
}: {
  kinds: { key: string; label: string; unit: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("book");
  const [qty, setQty] = useState("");
  const [min, setMin] = useState("");
  const [price, setPrice] = useState("");
  const [err, setErr] = useState("");

  async function save() {
    if (!name.trim()) {
      setErr("Nomini yozing");
      return;
    }
    try {
      await api.post("/consumables", {
        name: name.trim(),
        kind,
        qty: Number(qty) || 0,
        min_qty: Number(min) || 0,
        unit_price: price ? Number(price) : null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-20">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800">Yangi mahsulot</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nomi (masalan Cambridge Step 1 kitobi)"
            autoFocus
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <Field label="Turi">
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
            >
              {kinds.map((k) => (
                <option key={k.key} value={k.key}>
                  {k.label}
                </option>
              ))}
            </select>
          </Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Qoldiq">
              <input
                type="number"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
            <Field label="Minimal">
              <input
                type="number"
                value={min}
                onChange={(e) => setMin(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
            <Field label="Birlik narxi">
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </Field>
          </div>
          <p className="text-xs text-slate-400">
            Qoldiq minimaldan pastga tushsa — xarid so'rovi o'zi yaratiladi.
          </p>
          <button
            onClick={save}
            className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            Saqlash
          </button>
        </div>
      </div>
    </div>
  );
}
