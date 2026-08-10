import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  GraduationCap, DoorOpen, Plus, Trash2, Pencil, X,
  CheckCircle2, ClipboardList,
} from "lucide-react";
import {
  api, type RiskReport, type RiskRow, type RiskTask,
  type GroupFillReport, type Room, type Branch, type User,
  type SupportPanel, type SupportPlanRow, type SupportAssignment,
  type Group,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  ACADEMIC_VIEW, ACADEMIC_ACCESS, SUPPORT_ACCESS, SUPPORT_TEACHER, can,
} from "../lib/roles";
import { BranchPicker, branchParam } from "../components/BranchPicker";
import { riskLevel, fillBand, MANUAL_SIGNALS } from "../lib/academic";
import { formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

import StudentsPage from "./Students";
import GroupsPage from "./Groups";
import { CareerTab } from "../components/Career";

type Tab = "students" | "groups" | "risk" | "fill" | "tasks"
  | "career" | "support" | "rooms";

const TABS: { key: Tab; label: string }[] = [
  { key: "students", label: "Talabalar" },
  { key: "groups", label: "Guruhlar" },
  { key: "risk", label: "Akademik risk" },
  { key: "fill", label: "Guruh to'lishi" },
  { key: "tasks", label: "Vazifalar" },
  { key: "career", label: "Ustozlar karyerasi" },
  { key: "support", label: "Support teacher" },
  { key: "rooms", label: "Xonalar" },
];

// ------------------------------------------------------------ Risk tab
function RiskTab() {
  const [data, setData] = useState<RiskReport | null>(null);
  const [staff, setStaff] = useState<User[]>([]);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(true);
  const [taskFor, setTaskFor] = useState<RiskRow | null>(null);
  const [flagFor, setFlagFor] = useState<RiskRow | null>(null);

  function load() {
    setLoading(true);
    api
      .get<RiskReport>(`/academic/risk${level ? `?level=${level}` : ""}`)
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, [level]);
  useEffect(() => {
    api.get<User[]>("/users").then(setStaff).catch(() => setStaff([]));
  }, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {data.levels.map((l) => {
          const L = riskLevel(l.key);
          return (
            <button
              key={l.key}
              onClick={() => setLevel(level === l.key ? "" : l.key)}
              className={`text-left rounded-xl border p-4 transition ${
                level === l.key ? L.box : "bg-white border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2.5 h-2.5 rounded-full ${L.dot}`} />
                <p className="text-xs text-slate-500">{l.label}</p>
              </div>
              <p className="text-lg font-semibold text-slate-900">{l.count}</p>
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm text-slate-600">
          {data.total} ta o'quvchidan{" "}
          <span className="font-medium text-slate-900">{data.at_risk}</span> tasi
          e'tibor talab qiladi
        </p>
        {level && (
          <button
            onClick={() => setLevel("")}
            className="text-xs text-brand-600 hover:underline"
          >
            filtrni tozalash
          </button>
        )}
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("akademik-risk", "Risk",
              data.rows.map((r) => ({
                "O'quvchi": r.full_name,
                ID: r.public_id ?? "",
                Guruh: r.group ?? "",
                Ustoz: r.teacher ?? "",
                Daraja: r.level_label,
                Ball: r.score,
                Sabablar: r.signals.map((s) => s.label).join("; "),
                Telefon: r.phone ?? "",
              })))
          }
          className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
        >
          Excel
        </button>
      </div>

      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Xavfdagi o'quvchi yo'q — yaxshi belgi.
        </p>
      ) : (
        <div className="space-y-2">
          {data.rows.map((r) => {
            const L = riskLevel(r.level);
            return (
              <div
                key={r.student_id}
                className={`rounded-xl border ${L.box} overflow-hidden`}
              >
                <div className="flex items-start gap-3 p-4">
                  <span className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${L.dot}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Link
                        to={`/students/${r.student_id}`}
                        className="text-sm font-medium text-slate-900 hover:underline"
                      >
                        {r.full_name}
                      </Link>
                      <span className={`text-xs font-medium ${L.text}`}>
                        {r.level_label}
                      </span>
                      <span className="text-xs text-slate-400">{r.score} ball</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {[r.group, r.teacher, r.phone].filter(Boolean).join(" · ")}
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {r.signals.map((s, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-0.5 rounded-full bg-white/70 border border-slate-200 text-slate-600"
                          title={s.detail || undefined}
                        >
                          {s.label}
                          {s.detail && (
                            <span className="text-slate-400"> · {s.detail}</span>
                          )}
                        </span>
                      ))}
                    </div>
                    {r.tasks.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {r.tasks.map((t) => (
                          <p key={t.id} className="text-xs text-slate-600">
                            <ClipboardList size={11} className="inline mr-1" />
                            {t.title}
                            {t.assigned_user && (
                              <span className="text-slate-400"> — {t.assigned_user}</span>
                            )}
                            {t.due_date && (
                              <span className="text-slate-400">
                                {" "}
                                · {formatDate(t.due_date)}
                              </span>
                            )}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-1 shrink-0">
                    <button
                      onClick={() => setTaskFor(r)}
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-white border border-slate-200 text-slate-700 hover:border-brand-300"
                    >
                      Vazifa berish
                    </button>
                    <button
                      onClick={() => setFlagFor(r)}
                      className="px-2.5 py-1 rounded-md text-xs text-slate-500 hover:text-slate-700"
                    >
                      Signal qo'shish
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {taskFor && (
        <TaskModal
          student={taskFor}
          staff={staff}
          onClose={() => setTaskFor(null)}
          onSaved={() => {
            setTaskFor(null);
            load();
          }}
        />
      )}
      {flagFor && (
        <FlagModal
          student={flagFor}
          onClose={() => setFlagFor(null)}
          onSaved={() => {
            setFlagFor(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function TaskModal({
  student, staff, onClose, onSaved,
}: {
  student: RiskRow;
  staff: User[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState("Ota-ona bilan bog'lanish");
  const [assigned, setAssigned] = useState<string>("");
  const [due, setDue] = useState(
    new Date(Date.now() + 2 * 864e5).toISOString().slice(0, 10)
  );
  const [err, setErr] = useState("");

  async function save() {
    if (!title.trim()) {
      setErr("Vazifa nomini yozing");
      return;
    }
    try {
      await api.post("/academic/tasks", {
        student_id: student.student_id,
        title: title.trim(),
        level: student.level,
        assigned_user_id: assigned ? Number(assigned) : null,
        due_date: due || null,
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
          <h3 className="font-semibold text-slate-800">Vazifa berish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">{student.full_name}</p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Nima qilish kerak?"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <div>
            <label className="text-xs text-slate-500">Mas'ul</label>
            <select
              value={assigned}
              onChange={(e) => setAssigned(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              <option value="">Tanlanmagan</option>
              {staff.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500">Muddat</label>
            <input
              type="date"
              value={due}
              onChange={(e) => setDue(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
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

function FlagModal({
  student, onClose, onSaved,
}: {
  student: RiskRow;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [signal, setSignal] = useState(MANUAL_SIGNALS[0].key);
  const [note, setNote] = useState("");

  async function save() {
    await api.post("/academic/risk-flags", {
      student_id: student.student_id,
      signal,
      note: note || null,
    });
    onSaved();
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Signal qo'shish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">{student.full_name}</p>
        <div className="space-y-3">
          <select
            value={signal}
            onChange={(e) => setSignal(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          >
            {MANUAL_SIGNALS.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Izoh"
            rows={3}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <p className="text-xs text-slate-400">
            Dars qoldirish, to'lov kechikishi, shikoyat va guruh almashtirish
            avtomat aniqlanadi — ularni qo'lda qo'shish shart emas.
          </p>
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

// ------------------------------------------------------- To'lish tab
function FillTab({ branchId }: { branchId: number | null }) {
  const [data, setData] = useState<GroupFillReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<GroupFillReport>(`/academic/group-fill?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const s = data.summary;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Umumiy to'lish</p>
          <p
            className={`text-lg font-semibold ${fillBand(
              s.percent >= 85 ? "good" : s.percent >= 70 ? "ok"
                : s.percent >= 50 ? "problem" : "critical"
            ).text}`}
          >
            {s.percent}%
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {s.students} / {s.capacity} joy
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Bo'sh joylar</p>
          <p className="text-lg font-semibold text-slate-900">{s.free_seats}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            shuncha o'quvchi qo'shsa bo'ladi
          </p>
        </div>
        {s.by_band
          .filter((b) => b.band === "problem" || b.band === "critical")
          .map((b) => (
            <div key={b.band} className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs text-slate-500 mb-1">{b.label}</p>
              <p className={`text-lg font-semibold ${fillBand(b.band).text}`}>
                {b.count}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">guruh</p>
            </div>
          ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
          <p className="text-sm font-medium text-slate-700">Guruhlar</p>
          <span className="text-xs text-slate-400">
            eng bo'shi yuqorida
          </span>
          <div className="flex-1" />
          <button
            onClick={() =>
              exportToExcel("guruh-tolishi", "To'lish",
                data.rows.map((r) => ({
                  Guruh: r.name,
                  Ustoz: r.teacher ?? "",
                  Xona: r.room ?? "",
                  "O'quvchi": r.students,
                  "Sig'im": r.capacity,
                  "To'lish %": r.percent,
                  Daraja: r.band_label,
                  "Bo'sh joy": r.free_seats,
                })))
            }
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
          >
            Excel
          </button>
        </div>
        {data.rows.length === 0 ? (
          <p className="text-sm text-slate-400 py-10 text-center">
            Sig'imi belgilangan guruh yo'q. Xonalar bo'limidan sig'im
            kiriting yoki guruhga xona biriktiring.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Guruh</th>
                <th className="text-left">Ustoz</th>
                <th className="text-left">Xona</th>
                <th className="text-right w-24">O'quvchi</th>
                <th className="text-left w-56 px-4">To'lish</th>
                <th className="text-right pr-4 w-40">Holat</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r) => {
                const B = fillBand(r.band);
                return (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5">
                      <Link
                        to={`/groups/${r.id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {r.name}
                      </Link>
                    </td>
                    <td className="text-slate-500">{r.teacher || "—"}</td>
                    <td className="text-slate-500">{r.room || "—"}</td>
                    <td className="text-right text-slate-700">
                      {r.students} / {r.capacity}
                    </td>
                    <td className="px-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${B.bar}`}
                            style={{ width: `${Math.min(100, r.percent)}%` }}
                          />
                        </div>
                        <span className={`text-xs font-medium ${B.text} w-12 text-right`}>
                          {r.percent}%
                        </span>
                      </div>
                    </td>
                    <td className={`text-right pr-4 text-xs ${B.text}`}>
                      {r.band_label}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {data.no_capacity.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-4">
          <p className="text-sm text-amber-900 font-medium mb-1">
            {data.no_capacity.length} ta guruhning sig'imi belgilanmagan
          </p>
          <p className="text-xs text-amber-800">
            {data.no_capacity.map((g) => g.name).join(", ")} — bu guruhlarga
            xona biriktiring yoki guruh tahririda sig'im kiriting, aks holda
            to'lish koeffitsiyenti hisoblanmaydi.
          </p>
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------ Vazifalar tab
function TasksTab() {
  const [rows, setRows] = useState<RiskTask[]>([]);
  const [status, setStatus] = useState("open");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<RiskTask[]>(`/academic/tasks?status=${status}`)
      .then(setRows)
      .finally(() => setLoading(false));
  }
  useEffect(load, [status]);

  async function done(t: RiskTask) {
    const result = prompt("Natija (ixtiyoriy):") ?? "";
    await api.put(`/academic/tasks/${t.id}`, { status: "done", result });
    load();
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <div className="flex gap-1">
          {[
            { k: "open", l: "Ochiq" },
            { k: "done", l: "Bajarilgan" },
          ].map((f) => (
            <button
              key={f.k}
              onClick={() => setStatus(f.k)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                status === f.k
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {f.l}
            </button>
          ))}
        </div>
        <span className="text-sm text-slate-500">{rows.length} ta</span>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Vazifa yo'q. Akademik risk bo'limidan xavfdagi o'quvchiga vazifa
          bering.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Vazifa</th>
                <th className="text-left">O'quvchi</th>
                <th className="text-left">Mas'ul</th>
                <th className="text-left w-32">Muddat</th>
                <th className="w-24" />
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">
                    {t.title}
                    {t.result && (
                      <span className="block text-xs text-emerald-700">
                        {t.result}
                      </span>
                    )}
                  </td>
                  <td>
                    <Link
                      to={`/students/${t.student_id}`}
                      className="text-slate-600 hover:text-brand-700"
                    >
                      {t.student}
                    </Link>
                  </td>
                  <td className="text-slate-500">{t.assigned_user || "—"}</td>
                  <td
                    className={`text-xs ${
                      t.overdue ? "text-red-600 font-medium" : "text-slate-500"
                    }`}
                  >
                    {t.due_date ? formatDate(t.due_date) : "—"}
                    {t.overdue && <span className="block">muddati o'tgan</span>}
                  </td>
                  <td className="pr-4 text-right">
                    {t.status === "open" && (
                      <button
                        onClick={() => done(t)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                      >
                        <CheckCircle2 size={12} /> Bajarildi
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------- Xonalar tab
function RoomsTab({ canEdit, branches }: { canEdit: boolean; branches: Branch[] }) {
  const [rows, setRows] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Room | null>(null);
  const [form, setForm] = useState({ name: "", capacity: 12, branch_id: "" as string | number, note: "" });
  const [err, setErr] = useState("");

  function load() {
    setLoading(true);
    api.get<Room[]>("/rooms").then(setRows).finally(() => setLoading(false));
  }
  useEffect(load, []);

  function open(r?: Room) {
    setErr("");
    if (r) {
      setEditing(r);
      setForm({
        name: r.name, capacity: r.capacity,
        branch_id: r.branch_id ?? "", note: r.note ?? "",
      });
    } else {
      setEditing(null);
      setForm({ name: "", capacity: 12, branch_id: "", note: "" });
    }
    setModal(true);
  }

  async function save() {
    if (!form.name.trim()) {
      setErr("Xona nomini yozing");
      return;
    }
    if (branches.length > 0 && !form.branch_id) {
      setErr("Filialni tanlang — har bir filialning o'z xonalari bo'ladi");
      return;
    }
    const body = {
      name: form.name.trim(),
      capacity: Number(form.capacity) || 1,
      branch_id: form.branch_id ? Number(form.branch_id) : null,
      note: form.note || null,
    };
    try {
      if (editing) await api.put(`/rooms/${editing.id}`, body);
      else await api.post("/rooms", body);
      setModal(false);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function remove(r: Room) {
    if (!confirm(`"${r.name}" o'chirilsinmi?`)) return;
    try {
      await api.delete(`/rooms/${r.id}`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-slate-500">{rows.length} ta xona</span>
        <div className="flex-1" />
        {canEdit && (
          <button
            onClick={() => open()}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            <Plus size={15} /> Xona
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Xona qo'shilmagan. Xona sig'imi kiritilgach guruh to'lishi
          koeffitsiyenti avtomat hisoblanadi.
        </p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {rows.map((r) => (
            <div key={r.id} className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <DoorOpen size={15} className="text-slate-400" />
                  <p className="font-medium text-slate-800">{r.name}</p>
                </div>
                <span className="text-sm font-semibold text-slate-900">
                  {r.capacity}
                </span>
              </div>
              <p className="text-xs mt-1">
                {r.branch ? (
                  <span className="text-slate-400">{r.branch}</span>
                ) : (
                  <span className="text-amber-600">
                    Filial belgilanmagan — tahrirlab filial tanlang!
                  </span>
                )}
                <span className="text-slate-400"> · {r.capacity} o'rin</span>
              </p>
              {r.groups.length > 0 && (
                <p className="text-xs text-slate-500 mt-2">
                  {r.groups.map((g) => g.name).join(", ")}
                </p>
              )}
              {r.note && (
                <p className="text-xs text-slate-400 mt-1">{r.note}</p>
              )}
              {canEdit && (
                <div className="flex justify-end mt-3 pt-3 border-t border-slate-100">
                  <button
                    onClick={() => open(r)}
                    className="p-1.5 text-slate-400 hover:text-brand-600"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => remove(r)}
                    className="p-1.5 text-slate-400 hover:text-red-600"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {modal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">
                {editing ? "Xonani tahrirlash" : "Yangi xona"}
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
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Xona nomi (masalan: 3-xona)"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <div>
                <label className="text-xs text-slate-500">
                  Sig'imi (nechta o'quvchi sig'adi)
                </label>
                <input
                  type="number"
                  min={1}
                  value={form.capacity}
                  onChange={(e) =>
                    setForm({ ...form, capacity: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
              </div>
              {branches.length > 0 && (
                <select
                  value={form.branch_id}
                  onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">— Filialni tanlang (majburiy) —</option>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              )}
              <input
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
                placeholder="Izoh"
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

// ---------------------------------------------------------------- Sahifa
export default function Academic() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("risk");
  const [branchId, setBranchId] = useState<number | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  if (!can(user?.role, ACADEMIC_VIEW)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const canEdit = can(user?.role, ACADEMIC_ACCESS);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <GraduationCap size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">O'quv bo'limi</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Ta'lim sifati: xavfdagi o'quvchilar, guruh to'lishi va xonalar
      </p>

      <div className="flex items-center gap-2 border-b border-slate-200 mb-5">
        <div className="flex gap-1 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
        </div>
        <div className="flex-1" />
        {tab === "fill" && (
          <BranchPicker value={branchId} onChange={setBranchId} className="pb-2" />
        )}
      </div>

      {tab === "students" && <StudentsPage />}
      {tab === "groups" && <GroupsPage />}
      {tab === "risk" && <RiskTab />}
      {tab === "fill" && <FillTab branchId={branchId} />}
      {tab === "tasks" && <TasksTab />}
      {tab === "career" && <CareerTab />}
      {tab === "support" && <SupportTab canAssign={canEdit} />}
      {tab === "rooms" && <RoomsTab canEdit={canEdit} branches={branches} />}
    </div>
  );
}


// ------------------------------------------------- Support teacher tab
function SupportTab({ canAssign }: { canAssign: boolean }) {
  const { user } = useAuth();
  const [data, setData] = useState<SupportPanel | null>(null);
  const [staff, setStaff] = useState<User[]>([]);
  const [assigns, setAssigns] = useState<SupportAssignment[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [who, setWho] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [planFor, setPlanFor] = useState<{ id: number; name: string } | null>(null);
  const [assignOpen, setAssignOpen] = useState(false);

  const isSupport = user?.role === SUPPORT_TEACHER;

  function load() {
    setLoading(true);
    const q = !isSupport && who ? `?user_id=${who}` : "";
    Promise.all([
      api.get<SupportPanel>(`/support/panel${q}`).then(setData),
      api.get<SupportAssignment[]>(`/support/assignments${q}`)
        .then(setAssigns).catch(() => setAssigns([])),
    ]).finally(() => setLoading(false));
  }
  useEffect(load, [who]);

  useEffect(() => {
    if (isSupport) return;
    // /users EMAS: u faqat HR/asoschi/moliya uchun ochiq va o'quv
    // bo'limi rahbarida 403 berardi — natijada tanlagich bo'sh
    // qolardi (2026-08-10 tuzatildi). Yangi yo'l faqat support
    // teacherlarning ismini qaytaradi.
    api.get<{ id: number; full_name: string }[]>("/support/teachers")
      .then((u) => setStaff(u as unknown as User[]))
      .catch(() => setStaff([]));
    api.get<Group[]>("/groups").then(setGroups).catch(() => setGroups([]));
  }, [isSupport]);

  if (!can(user?.role, SUPPORT_ACCESS)) {
    return (
      <p className="text-sm text-slate-400 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const s = data.summary;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {!isSupport && (
          <select
            value={who}
            onChange={(e) => setWho(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
          >
            <option value="">Barcha support teacherlar</option>
            {staff.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name}
              </option>
            ))}
          </select>
        )}
        <div className="flex-1" />
        {canAssign && (
          <button
            onClick={() => setAssignOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
          >
            <Plus size={14} /> Guruh biriktirish
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">O'quvchilar</p>
          <p className="text-lg font-semibold text-slate-900">{s.students}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Davomat muammosi</p>
          <p
            className={`text-lg font-semibold ${
              s.attendance_problem ? "text-red-600" : "text-slate-900"
            }`}
          >
            {s.attendance_problem}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {s.threshold}% dan past
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Uy vazifasi</p>
          <p
            className={`text-lg font-semibold ${
              s.homework_problem ? "text-amber-600" : "text-slate-900"
            }`}
          >
            {s.homework_problem}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Ochiq rejalar</p>
          <p className="text-lg font-semibold text-slate-900">{s.open_plans}</p>
          {s.plan_success !== null && (
            <p className="text-xs text-slate-400 mt-0.5">
              {s.plan_success}% bajarilgan
            </p>
          )}
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500 mb-1">Retention</p>
          <p
            className={`text-lg font-semibold ${
              (s.retention ?? 0) >= 80 ? "text-emerald-600" : "text-amber-600"
            }`}
          >
            {s.retention !== null ? `${s.retention}%` : "—"}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {s.stayed} qoldi · {s.left} ketdi
          </p>
        </div>
      </div>

      {data.groups.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Biriktirilgan guruhlar
          </p>
          <div className="flex flex-wrap gap-2">
            {data.groups.map((g) => (
              <Link
                key={g.id}
                to={`/groups/${g.id}`}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-700 hover:border-brand-300"
              >
                {g.name}
                <span className="text-xs text-slate-400">
                  {" "}
                  · {g.students} o'quvchi
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {data.students.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali guruh biriktirilmagan. Yuqoridagi tugmadan biriktiring.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">O'quvchi</th>
                <th className="text-left">Guruh</th>
                <th className="text-right w-28">Davomat</th>
                <th className="text-left w-48">Muammo</th>
                <th className="text-left">Reja</th>
                <th className="w-28" />
              </tr>
            </thead>
            <tbody>
              {data.students.map((st) => (
                <tr key={st.student_id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5">
                    <Link
                      to={`/students/${st.student_id}`}
                      className="text-slate-800 hover:text-brand-700"
                    >
                      {st.full_name}
                    </Link>
                    {st.parent_phone && (
                      <span className="block text-xs text-slate-400">
                        {st.parent_phone}
                      </span>
                    )}
                  </td>
                  <td className="text-slate-500">{st.group || "—"}</td>
                  <td
                    className={`text-right font-medium ${
                      st.attendance_problem ? "text-red-600" : "text-slate-600"
                    }`}
                  >
                    {st.attendance.percent !== null
                      ? `${st.attendance.percent}%`
                      : "—"}
                    <span className="block text-xs text-slate-400 font-normal">
                      {st.attendance.absent} qoldirgan
                    </span>
                  </td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {st.attendance_problem && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700">
                          Davomat
                        </span>
                      )}
                      {st.homework_problem && (
                        <span
                          className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700"
                          title={st.homework_note || undefined}
                        >
                          Uy vazifasi
                        </span>
                      )}
                      {!st.attendance_problem && !st.homework_problem && (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {st.open_plans.length === 0 ? (
                      <span className="text-xs text-slate-400">yo'q</span>
                    ) : (
                      st.open_plans.map((p) => (
                        <p key={p.id} className="text-xs text-slate-600">
                          {p.plan}
                          {p.due_date && (
                            <span className="text-slate-400">
                              {" "}
                              · {formatDate(p.due_date)}
                            </span>
                          )}
                        </p>
                      ))
                    )}
                  </td>
                  <td className="pr-4 text-right">
                    <button
                      onClick={() =>
                        setPlanFor({ id: st.student_id, name: st.full_name })
                      }
                      className="px-2.5 py-1 rounded-md text-xs font-medium border border-slate-200 text-slate-700 hover:border-brand-300"
                    >
                      Reja
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <PlansList onChanged={load} />

      {planFor && (
        <PlanModal
          student={planFor}
          onClose={() => setPlanFor(null)}
          onSaved={() => {
            setPlanFor(null);
            load();
          }}
        />
      )}
      {assignOpen && (
        <AssignModal
          staff={staff}
          groups={groups}
          existing={assigns}
          onClose={() => setAssignOpen(false)}
          onSaved={() => {
            setAssignOpen(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function PlansList({ onChanged }: { onChanged: () => void }) {
  const [rows, setRows] = useState<SupportPlanRow[]>([]);
  const [status, setStatus] = useState("open");

  function load() {
    api.get<SupportPlanRow[]>(`/support/plans?status=${status}`)
      .then(setRows).catch(() => setRows([]));
  }
  useEffect(load, [status]);

  async function done(p: SupportPlanRow) {
    const result = prompt("Natija (ixtiyoriy):") ?? "";
    await api.put(`/support/plans/${p.id}`, { status: "done", result });
    load();
    onChanged();
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mt-4">
      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm font-medium text-slate-700">
          O'quvchi bilan ishlash rejalari
        </p>
        <div className="flex gap-1">
          {[
            { k: "open", l: "Ochiq" },
            { k: "done", l: "Bajarilgan" },
          ].map((f) => (
            <button
              key={f.k}
              onClick={() => setStatus(f.k)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                status === f.k
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {f.l}
            </button>
          ))}
        </div>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-4">Reja yo'q</p>
      ) : (
        <table className="w-full text-sm">
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-b border-slate-50 last:border-0">
                <td className="py-2">
                  <Link
                    to={`/students/${p.student_id}`}
                    className="text-slate-800 hover:text-brand-700"
                  >
                    {p.student}
                  </Link>
                  <span className="block text-xs text-slate-400">
                    {p.issue_label}
                  </span>
                </td>
                <td className="text-slate-600">
                  {p.plan}
                  {p.result && (
                    <span className="block text-xs text-emerald-700">
                      {p.result}
                    </span>
                  )}
                </td>
                <td
                  className={`text-right w-28 text-xs ${
                    p.overdue ? "text-red-600 font-medium" : "text-slate-500"
                  }`}
                >
                  {p.due_date ? formatDate(p.due_date) : "—"}
                </td>
                <td className="text-right w-28">
                  {p.status === "open" && (
                    <button
                      onClick={() => done(p)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                    >
                      <CheckCircle2 size={12} /> Bajarildi
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const SUPPORT_ISSUES = [
  { key: "attendance", label: "Davomat muammosi" },
  { key: "homework", label: "Uy vazifasi muammosi" },
  { key: "behaviour", label: "Xulq" },
  { key: "motivation", label: "Motivatsiya" },
  { key: "other", label: "Boshqa" },
];

function PlanModal({
  student, onClose, onSaved,
}: {
  student: { id: number; name: string };
  onClose: () => void;
  onSaved: () => void;
}) {
  const [issue, setIssue] = useState("attendance");
  const [plan, setPlan] = useState("");
  const [due, setDue] = useState(
    new Date(Date.now() + 3 * 864e5).toISOString().slice(0, 10)
  );
  const [err, setErr] = useState("");

  async function save() {
    if (!plan.trim()) {
      setErr("Nima qilishni yozing");
      return;
    }
    try {
      await api.post("/support/plans", {
        student_id: student.id, issue, plan: plan.trim(),
        due_date: due || null,
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
          <h3 className="font-semibold text-slate-800">Ishlash rejasi</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">{student.name}</p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <select
            value={issue}
            onChange={(e) => setIssue(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          >
            {SUPPORT_ISSUES.map((i) => (
              <option key={i.key} value={i.key}>
                {i.label}
              </option>
            ))}
          </select>
          <textarea
            value={plan}
            onChange={(e) => setPlan(e.target.value)}
            placeholder="Nima qilinadi? (masalan: ota-onasi bilan uchrashuv)"
            rows={3}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <div>
            <label className="text-xs text-slate-500">Muddat</label>
            <input
              type="date"
              value={due}
              onChange={(e) => setDue(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
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

function AssignModal({
  staff, groups, existing, onClose, onSaved,
}: {
  staff: User[];
  groups: Group[];
  existing: SupportAssignment[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [userId, setUserId] = useState<string>(staff[0] ? String(staff[0].id) : "");
  const [groupId, setGroupId] = useState<string>("");
  const [err, setErr] = useState("");

  async function save() {
    if (!userId || !groupId) {
      setErr("Support teacher va guruhni tanlang");
      return;
    }
    try {
      await api.post("/support/assignments", {
        user_id: Number(userId), group_id: Number(groupId),
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function remove(a: SupportAssignment) {
    await api.delete(`/support/assignments/${a.id}`);
    onSaved();
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800">Guruh biriktirish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        {staff.length === 0 ? (
          <p className="text-sm text-slate-500">
            Support teacher rolidagi xodim yo'q. Avval Xodimlar bo'limidan
            qo'shing.
          </p>
        ) : (
          <div className="space-y-3">
            <select
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              {staff.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name}
                </option>
              ))}
            </select>
            <select
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              <option value="">Guruhni tanlang</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {existing.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-500 mb-2">Biriktirilganlar</p>
            <div className="space-y-1">
              {existing.map((a) => (
                <div key={a.id} className="flex items-center justify-between text-sm">
                  <span className="text-slate-700">
                    {a.user} — {a.group || a.student}
                  </span>
                  <button
                    onClick={() => remove(a)}
                    className="text-slate-400 hover:text-red-600"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2 mt-5">
          <button
            onClick={save}
            disabled={staff.length === 0}
            className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-40"
          >
            Biriktirish
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Yopish
          </button>
        </div>
      </div>
    </div>
  );
}
