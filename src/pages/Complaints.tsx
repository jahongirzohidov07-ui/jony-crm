import { useEffect, useState } from "react";
import { MessageSquareWarning, Plus, Trash2, Pencil, X } from "lucide-react";
import {
  api, type Complaint, type Student, type Group, type Branch,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, FULL_ACCESS, can } from "../lib/roles";
import { formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

const STATUSES = [
  { key: "open", label: "Ochiq", cls: "bg-red-50 text-red-700" },
  { key: "in_progress", label: "Ko'rilmoqda", cls: "bg-amber-50 text-amber-700" },
  { key: "closed", label: "Yopilgan", cls: "bg-emerald-50 text-emerald-700" },
];

const SEVERITIES = [
  { key: "low", label: "Past" },
  { key: "normal", label: "O'rtacha" },
  { key: "high", label: "Yuqori" },
];

const SOURCES = [
  { key: "phone", label: "Telefon" },
  { key: "visit", label: "Tashrif" },
  { key: "telegram", label: "Telegram" },
  { key: "instagram", label: "Instagram" },
  { key: "teacher", label: "Ustoz aytdi" },
  { key: "other", label: "Boshqa" },
];

const label = (list: { key: string; label: string }[], k?: string | null) =>
  list.find((x) => x.key === k)?.label || k || "—";

const empty = {
  subject: "",
  body: "",
  student_id: "" as string | number,
  group_id: "" as string | number,
  branch_id: "" as string | number,
  source: "phone",
  severity: "normal",
  status: "open",
  resolution: "",
};

export default function Complaints() {
  const { user } = useAuth();
  const [rows, setRows] = useState<Complaint[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("open");
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Complaint | null>(null);
  const [form, setForm] = useState({ ...empty });
  const [err, setErr] = useState("");

  function load() {
    setLoading(true);
    api
      .get<Complaint[]>("/complaints")
      .then(setRows)
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  useEffect(() => {
    api.get<Student[]>("/students").then(setStudents).catch(() => {});
    api.get<Group[]>("/groups").then(setGroups).catch(() => {});
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, []);

  function open(c?: Complaint) {
    setErr("");
    if (c) {
      setEditing(c);
      setForm({
        subject: c.subject,
        body: c.body ?? "",
        student_id: c.student_id ?? "",
        group_id: c.group_id ?? "",
        branch_id: c.branch_id ?? "",
        source: c.source,
        severity: c.severity,
        status: c.status,
        resolution: c.resolution ?? "",
      });
    } else {
      setEditing(null);
      setForm({ ...empty });
    }
    setModal(true);
  }

  async function save() {
    if (!form.subject.trim()) {
      setErr("Shikoyat mavzusini yozing");
      return;
    }
    const body = {
      subject: form.subject.trim(),
      body: form.body || null,
      student_id: form.student_id ? Number(form.student_id) : null,
      group_id: form.group_id ? Number(form.group_id) : null,
      branch_id: form.branch_id ? Number(form.branch_id) : null,
      source: form.source,
      severity: form.severity,
      status: form.status,
      resolution: form.resolution || null,
    };
    try {
      if (editing) await api.put(`/complaints/${editing.id}`, body);
      else await api.post("/complaints", body);
      setModal(false);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function setStatus(c: Complaint, status: string) {
    await api.put(`/complaints/${c.id}`, { status });
    load();
  }

  async function remove(c: Complaint) {
    if (!confirm(`"${c.subject}" o'chirilsinmi?`)) return;
    await api.delete(`/complaints/${c.id}`);
    load();
  }

  if (!can(user?.role, TEACHING_STAFF)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const shown =
    filter === "all"
      ? rows
      : filter === "open"
        ? rows.filter((r) => r.status !== "closed")
        : rows.filter((r) => r.status === filter);

  const canDelete = can(user?.role, FULL_ACCESS);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <MessageSquareWarning size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Shikoyatlar</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Ota-ona va o'quvchi murojaatlari. Ochiq shikoyat asoschi panelida
        ko'rinib turadi.
      </p>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1">
          {[
            { k: "open", l: "Ochiq" },
            { k: "in_progress", l: "Ko'rilmoqda" },
            { k: "closed", l: "Yopilgan" },
            { k: "all", l: "Hammasi" },
          ].map((f) => (
            <button
              key={f.k}
              onClick={() => setFilter(f.k)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                filter === f.k
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {f.l}
            </button>
          ))}
        </div>
        <span className="text-sm text-slate-500">{shown.length} ta</span>
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("shikoyatlar", "Shikoyatlar",
              shown.map((c) => ({
                Sana: c.created_at?.slice(0, 10) ?? "",
                Mavzu: c.subject,
                "O'quvchi": c.student ?? "",
                Guruh: c.group ?? "",
                Muhimlik: label(SEVERITIES, c.severity),
                Manba: label(SOURCES, c.source),
                Holat: label(STATUSES, c.status),
                Yechim: c.resolution ?? "",
              })))
          }
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          Excel
        </button>
        <button
          onClick={() => open()}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={15} /> Shikoyat
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : shown.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Shikoyat yo'q — yaxshi belgi.
        </p>
      ) : (
        <div className="space-y-2">
          {shown.map((c) => {
            const st = STATUSES.find((s) => s.key === c.status);
            return (
              <div
                key={c.id}
                className="bg-white rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${
                      c.severity === "high"
                        ? "bg-red-500"
                        : c.severity === "low"
                          ? "bg-slate-300"
                          : "bg-amber-400"
                    }`}
                    title={label(SEVERITIES, c.severity)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-slate-900">
                        {c.subject}
                      </p>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${st?.cls}`}
                      >
                        {st?.label}
                      </span>
                      {c.age_days >= 3 && (
                        <span className="text-xs text-red-600">
                          {c.age_days} kundan beri ochiq
                        </span>
                      )}
                    </div>
                    {c.body && (
                      <p className="text-sm text-slate-600 mt-1">{c.body}</p>
                    )}
                    <p className="text-xs text-slate-400 mt-1">
                      {[c.student, c.group, c.branch,
                        label(SOURCES, c.source),
                        c.created_at ? formatDate(c.created_at.slice(0, 10)) : null]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                    {c.resolution && (
                      <p className="text-xs text-emerald-700 mt-1">
                        Yechim: {c.resolution}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {c.status !== "closed" && (
                      <button
                        onClick={() => setStatus(c, "closed")}
                        className="px-2.5 py-1 rounded-md text-xs font-medium border border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                      >
                        Yopish
                      </button>
                    )}
                    <button
                      onClick={() => open(c)}
                      className="p-1.5 text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={14} />
                    </button>
                    {canDelete && (
                      <button
                        onClick={() => remove(c)}
                        className="p-1.5 text-slate-400 hover:text-red-600"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {modal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg p-5 max-h-[88vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">
                {editing ? "Shikoyatni tahrirlash" : "Yangi shikoyat"}
              </h3>
              <button onClick={() => setModal(false)} className="text-slate-400">
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
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                placeholder="Nima haqida? (masalan: Ustoz darsga kech keldi)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <textarea
                value={form.body}
                onChange={(e) => setForm({ ...form, body: e.target.value })}
                placeholder="Batafsil"
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <div className="grid grid-cols-2 gap-3">
                <select
                  value={form.student_id}
                  onChange={(e) => setForm({ ...form, student_id: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">O'quvchi tanlanmagan</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.full_name}
                    </option>
                  ))}
                </select>
                <select
                  value={form.group_id}
                  onChange={(e) => setForm({ ...form, group_id: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Guruh tanlanmagan</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <select
                  value={form.severity}
                  onChange={(e) => setForm({ ...form, severity: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {SEVERITIES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
                <select
                  value={form.source}
                  onChange={(e) => setForm({ ...form, source: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {SOURCES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {STATUSES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
              {branches.length > 1 && (
                <select
                  value={form.branch_id}
                  onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Filial tanlanmagan</option>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              )}
              {form.status === "closed" && (
                <textarea
                  value={form.resolution}
                  onChange={(e) => setForm({ ...form, resolution: e.target.value })}
                  placeholder="Qanday hal qilindi?"
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
              )}
            </div>
            <div className="flex gap-2 mt-5">
              <button
                onClick={save}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
              >
                Saqlash
              </button>
              <button
                onClick={() => setModal(false)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
              >
                Bekor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
