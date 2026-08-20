import { useEffect, useState } from "react";
import {
  ClipboardList, Plus, X, Check, Trash2,
  CalendarClock, Eye, Users, Coffee,
} from "lucide-react";
import { api, type TaskList, type TaskRow, type User } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { TASK_ACCESS, DISCOUNT_APPROVE, PAYMENT_FIX_APPROVE,
  RESCHEDULE_APPROVE, can } from "../lib/roles";
import { BranchPicker, branchParam } from "../components/BranchPicker";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-600",
  sky: "bg-sky-100 text-sky-700",
  violet: "bg-violet-100 text-violet-700",
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
};

const PRIORITY_TONE: Record<string, string> = {
  low: "text-slate-400",
  normal: "text-slate-500",
  high: "text-amber-600",
  urgent: "text-red-600",
};

function daysLabel(t: TaskRow): string {
  if (!t.deadline) return "muddatsiz";
  const d = t.days_left ?? 0;
  if (t.overdue) return `${Math.abs(d)} kun kechikdi`;
  if (d === 0) return "bugun";
  if (d === 1) return "ertaga";
  return `${d} kun qoldi`;
}

export default function Tasks() {
  const { user } = useAuth();
  const [data, setData] = useState<TaskList | null>(null);
  const [staff, setStaff] = useState<User[]>([]);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>("");
  // 2026-08-12, Jahongir: "vazifa kimga tegishli bo'lsa shunga borsin" —
  // default faqat MENIKI; rahbariyat xohlasa "Hammasi"ni yoqadi.
  const [scope, setScope] = useState<"mine" | "all">("mine");
  const [form, setForm] = useState(false);
  const [meeting, setMeeting] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<TaskList>(
        `/tasks?x=1${scope === "all" ? "&all=1" : ""}${branchParam(branchId)}`,
      )
      .then(setData)
      .finally(() => setLoading(false));
  }

  useEffect(load, [branchId, scope]);
  useEffect(() => {
    api.get<User[]>("/users").then(setStaff).catch(() => setStaff([]));
  }, []);

  if (!can(user?.role, TASK_ACCESS)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const rows = (data?.rows ?? []).filter(
    (r) => !filter || r.status === filter
  );
  const canManage = data?.can_manage ?? false;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ClipboardList size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Vazifalar</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Majlisdagi qaror shu yerga tushmasa — choy qoladi, natija qolmaydi
      </p>

      {data && (data.overdue > 0 || data.open > 0) && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500 mb-1">Ochiq vazifa</p>
            <p className="text-xl font-semibold text-slate-900">{data.open}</p>
          </div>
          <div
            className={`rounded-xl border p-4 ${
              data.overdue > 0
                ? "bg-red-50 border-red-200"
                : "bg-white border-slate-200"
            }`}
          >
            <p className="text-xs text-slate-500 mb-1">Kechikkan</p>
            <p
              className={`text-xl font-semibold ${
                data.overdue > 0 ? "text-red-700" : "text-slate-900"
              }`}
            >
              {data.overdue}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500 mb-1">Tekshiruvda</p>
            <p className="text-xl font-semibold text-violet-700">
              {data.counts.review ?? 0}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500 mb-1">Bajarildi</p>
            <p className="text-xl font-semibold text-emerald-700">
              {data.counts.done ?? 0}
            </p>
          </div>
        </div>
      )}

      {canManage && (
        <div className="flex items-center gap-1 mb-3">
          {([["mine", "Menga tegishli"], ["all", "Hammaniki"]] as const).map(
            ([k, lbl]) => (
              <button
                key={k}
                onClick={() => setScope(k)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                  scope === k
                    ? "bg-slate-900 border-slate-900 text-white"
                    : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                }`}
              >
                {lbl}
              </button>
            ),
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <button
          onClick={() => setFilter("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
            !filter
              ? "bg-brand-50 border-brand-400 text-brand-700"
              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
          }`}
        >
          Hammasi
        </button>
        {(data?.statuses ?? []).map((s) => (
          <button
            key={s.key}
            onClick={() => setFilter(filter === s.key ? "" : s.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
              filter === s.key
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {s.label}
            {s.count > 0 && (
              <span className="ml-1 text-slate-400">{s.count}</span>
            )}
          </button>
        ))}
        <BranchPicker value={branchId} onChange={setBranchId} />
        <div className="flex-1" />
        {canManage && (
          <button
            onClick={() => setMeeting(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
          >
            <Coffee size={14} /> Majlis qarorlari
          </button>
        )}
        <button
          onClick={() => setForm(true)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={15} /> Vazifa
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Vazifa yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {rows.map((t) => (
            <div
              key={t.id}
              className={`bg-white rounded-xl border p-4 ${
                t.overdue ? "border-red-200" : "border-slate-200"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={() => setOpen(open === t.id ? null : t.id)}
                      className="text-sm font-medium text-slate-900 hover:text-brand-700 text-left"
                    >
                      {t.title}
                    </button>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        TONE[t.status_tone] || TONE.slate
                      }`}
                    >
                      {t.status_label}
                    </span>
                    {t.priority !== "normal" && (
                      <span
                        className={`text-xs font-medium ${
                          PRIORITY_TONE[t.priority]
                        }`}
                      >
                        {t.priority_label}
                      </span>
                    )}
                    {t.source !== "manual" && (
                      <span className="text-xs text-slate-400">
                        {t.source_label}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500 flex-wrap">
                    {t.assignee && (
                      <span className="flex items-center gap-1">
                        <Users size={11} /> {t.assignee}
                      </span>
                    )}
                    {t.watcher && (
                      <span className="flex items-center gap-1">
                        <Eye size={11} /> {t.watcher}
                      </span>
                    )}
                    <span
                      className={`flex items-center gap-1 ${
                        t.overdue ? "text-red-600 font-medium" : ""
                      }`}
                    >
                      <CalendarClock size={11} /> {daysLabel(t)}
                    </span>
                    {t.checklist_total > 0 && (
                      <span>
                        {t.checklist_done}/{t.checklist_total} bajarildi
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {t.status !== "done" && (
                    <StatusMenu task={t} onDone={load} />
                  )}
                  {canManage && (
                    <button
                      onClick={async () => {
                        if (!confirm(`"${t.title}" o'chirilsinmi?`)) return;
                        await api.delete(`/tasks/${t.id}`);
                        load();
                      }}
                      className="p-1.5 rounded-md text-slate-300 hover:text-red-600 hover:bg-red-50"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>

              {open === t.id && (
                <TaskBody task={t} onDone={load} canManage={canManage} />
              )}
            </div>
          ))}
        </div>
      )}

      {form && (
        <TaskForm
          staff={staff}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
          priorities={data?.priorities ?? []}
        />
      )}
      {meeting && (
        <MeetingForm
          staff={staff}
          onClose={() => setMeeting(false)}
          onSaved={() => {
            setMeeting(false);
            load();
          }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------- Status menu
function StatusMenu({ task, onDone }: { task: TaskRow; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [result, setResult] = useState("");
  const [err, setErr] = useState("");

  const options = [
    { key: "new", label: "Yangi" },
    { key: "in_progress", label: "Jarayonda" },
    { key: "review", label: "Tekshiruvda" },
    { key: "done", label: "Bajarildi" },
    { key: "rework", label: "Qayta ishlashga" },
    { key: "cancelled", label: "Bekor qilindi" },
  ];

  async function set(status: string) {
    setErr("");
    const body: Record<string, unknown> = { status };
    if (status === "done") {
      if (task.overdue && !reason.trim() && !task.delay_reason) {
        setErr("Muddat o'tgan — kechikish sababini yozing");
        return;
      }
      if (reason.trim()) body.delay_reason = reason.trim();
      if (result.trim()) body.result = result.trim();
    }
    try {
      await api.put(`/tasks/${task.id}`, body);
      setOpen(false);
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-1.5 rounded-md text-slate-400 hover:text-emerald-600 hover:bg-emerald-50"
        title="Statusni o'zgartirish"
      >
        <Check size={15} />
      </button>
      {open && (
        <div className="absolute right-0 top-8 z-20 bg-white rounded-lg border border-slate-200 shadow-lg p-2 w-64">
          {err && (
            <p className="text-xs text-red-600 bg-red-50 rounded px-2 py-1 mb-2">
              {err}
            </p>
          )}
          {task.overdue && (
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Kechikish sababi"
              className="w-full px-2 py-1.5 rounded border border-amber-300 bg-amber-50 text-xs mb-1"
            />
          )}
          <input
            value={result}
            onChange={(e) => setResult(e.target.value)}
            placeholder="Natija (ixtiyoriy)"
            className="w-full px-2 py-1.5 rounded border border-slate-200 text-xs mb-2"
          />
          {options.map((o) => (
            <button
              key={o.key}
              onClick={() => set(o.key)}
              className={`w-full text-left px-2 py-1.5 rounded text-xs hover:bg-slate-50 ${
                task.stored_status === o.key
                  ? "text-brand-700 font-medium"
                  : "text-slate-600"
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------ Task body
function TaskBody({
  task,
  onDone,
  canManage,
}: {
  task: TaskRow;
  onDone: () => void;
  canManage: boolean;
}) {
  async function toggle(i: number) {
    const list = task.checklist.map((c, j) =>
      j === i ? { ...c, done: !c.done } : c
    );
    await api.put(`/tasks/${task.id}`, { checklist: list });
    onDone();
  }

  return (
    <div className="mt-3 pt-3 border-t border-slate-100 space-y-3">
      {task.description && (
        <p className="text-sm text-slate-600 whitespace-pre-wrap">
          {task.description}
        </p>
      )}

      {/* Chegirma so'rovini VAZIFANING O'ZIDA tasdiqlash (2026-08-12,
          Jahongir: "sorovni kelgan joyida tasdiqlaydigan qilaylik,
          men uni oquvchini topib profiliga kirib osha yerdan
          tasdiqlashim kerak ekan"). */}
      <DiscountTaskActions task={task} onDone={onDone} />
      {/* Boshqa so'rovlar ham vazifaning o'zida hal qilinadi
          (2026-08-20, Jahongir: "menga shu narsa vazifalar bolimiga
          kelsin va vazifalardan tasdiqlansan vazifa avtomat
          bajarilgan bo'lsin"). */}
      <RequestTaskActions task={task} onDone={onDone} />

      {task.meeting && (
        <p className="text-xs text-slate-500">
          Majlis: <span className="text-slate-700">{task.meeting}</span>
        </p>
      )}

      {task.checklist.length > 0 && (
        <div className="space-y-1">
          {task.checklist.map((c, i) => (
            <label
              key={i}
              className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={c.done}
                onChange={() => toggle(i)}
                className="rounded border-slate-300"
              />
              <span className={c.done ? "line-through text-slate-400" : ""}>
                {c.text}
              </span>
            </label>
          ))}
        </div>
      )}

      {task.delay_reason && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
          <p className="text-xs text-amber-800 font-medium mb-0.5">
            Kechikish sababi
          </p>
          <p className="text-sm text-amber-900">{task.delay_reason}</p>
        </div>
      )}

      {task.result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
          <p className="text-xs text-emerald-800 font-medium mb-0.5">Natija</p>
          <p className="text-sm text-emerald-900">{task.result}</p>
        </div>
      )}

      <p className="text-xs text-slate-400">
        {task.public_id} · {task.created_by} qo'ydi
        {canManage && task.branch ? ` · ${task.branch}` : ""}
      </p>
    </div>
  );
}

// ------------------------------------------------------------ Task form
function TaskForm({
  staff,
  onClose,
  onSaved,
  priorities,
}: {
  staff: User[];
  onClose: () => void;
  onSaved: () => void;
  priorities: { key: string; label: string }[];
}) {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [assignee, setAssignee] = useState("");
  const [watcher, setWatcher] = useState("");
  const [deadline, setDeadline] = useState("");
  const [priority, setPriority] = useState("normal");
  const [checks, setChecks] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!title.trim()) {
      setErr("Vazifa nomini yozing");
      return;
    }
    setSaving(true);
    try {
      await api.post("/tasks", {
        title: title.trim(),
        description: desc || null,
        assignee_id: assignee ? Number(assignee) : null,
        watcher_id: watcher ? Number(watcher) : null,
        deadline: deadline || null,
        priority,
        checklist: checks
          .split("\n")
          .map((x) => x.trim())
          .filter(Boolean),
      });
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
          <h3 className="font-semibold text-slate-800">Yangi vazifa</h3>
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
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Vazifa nomi"
            autoFocus
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <textarea
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="Tavsif"
            rows={3}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Mas'ul
              </label>
              <select
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— tanlang —</option>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Kuzatuvchi
              </label>
              <select
                value={watcher}
                onChange={(e) => setWatcher(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— tanlang —</option>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Muddat
              </label>
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Ustuvorlik
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                {priorities.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Checklist — har bir qatorda bitta
            </label>
            <textarea
              value={checks}
              onChange={(e) => setChecks(e.target.value)}
              rows={3}
              placeholder={"Kitob buyurtma\nJadval tuzish"}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
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

// --------------------------------------------------------- Meeting form
function MeetingForm({
  staff,
  onClose,
  onSaved,
}: {
  staff: User[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [deadline, setDeadline] = useState("");
  const [rows, setRows] = useState([{ title: "", assignee: "" }]);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  async function save() {
    const list = rows.filter((r) => r.title.trim());
    if (!name.trim() || list.length === 0) {
      setErr("Majlis nomi va kamida bitta qaror kerak");
      return;
    }
    setSaving(true);
    try {
      await api.post("/tasks/from-meeting", {
        meeting: name.trim(),
        deadline: deadline || null,
        decisions: list.map((r) => ({
          title: r.title.trim(),
          assignee_id: r.assignee ? Number(r.assignee) : null,
        })),
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-16 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-2xl p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Majlis qarorlari</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Har bir qaror alohida vazifaga aylanadi — mas'uli va muddati bilan
        </p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Majlis nomi va sanasi"
            autoFocus
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <input
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
        </div>
        <div className="space-y-2 mb-3">
          {rows.map((r, i) => (
            <div key={i} className="flex gap-2">
              <input
                value={r.title}
                onChange={(e) => {
                  const list = [...rows];
                  list[i] = { ...list[i], title: e.target.value };
                  setRows(list);
                }}
                placeholder={`${i + 1}-qaror`}
                className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <select
                value={r.assignee}
                onChange={(e) => {
                  const list = [...rows];
                  list[i] = { ...list[i], assignee: e.target.value };
                  setRows(list);
                }}
                className="w-44 px-2 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— mas'ul —</option>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
              </select>
              {rows.length > 1 && (
                <button
                  onClick={() => setRows(rows.filter((_, j) => j !== i))}
                  className="p-2 text-slate-300 hover:text-red-600"
                >
                  <X size={15} />
                </button>
              )}
            </div>
          ))}
        </div>
        <button
          onClick={() => setRows([...rows, { title: "", assignee: "" }])}
          className="text-sm text-brand-600 hover:underline mb-4"
        >
          + yana qaror
        </button>
        <button
          onClick={save}
          disabled={saving}
          className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {saving ? "Saqlanmoqda..." : "Vazifalarga aylantirish"}
        </button>
      </div>
    </div>
  );
}


/**
 * Vazifa "Chegirma so'rovi #12 — Ism" bo'lsa, shu yerning o'zida
 * tasdiqlash/rad etish tugmalari chiqadi. Foydalanuvchi o'quvchini
 * qidirib, kartasiga kirib o'tirmasin.
 */
function DiscountTaskActions({
  task,
  onDone,
}: {
  task: TaskRow;
  onDone: () => void;
}) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const m = /Chegirma so'rovi #(\d+)/.exec(task.title || "");
  const id = m ? Number(m[1]) : null;
  const canApprove = can(user?.role, DISCOUNT_APPROVE);
  if (!id || !canApprove || task.status === "done") return null;

  const decide = async (approve: boolean) => {
    let reason: string | undefined;
    if (!approve) {
      const r = prompt("Rad etish sababi:");
      if (r === null) return;
      reason = r.trim() || undefined;
    }
    setBusy(true);
    try {
      await api.post(`/discounts/${id}/approve`, { approve, reason });
      // Vazifa(lar)ni server o'zi yopadi - BARCHA tasdiqlovchilarda
      // (2026-08-20). Bu yerda qo'lda yopish shart emas.
      setMsg(approve ? "Tasdiqlandi ✓" : "Rad etildi");
      onDone();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-violet-50 border border-violet-200 rounded-lg p-3">
      <p className="text-xs text-violet-900 mb-2">
        Chegirma so'rovi — shu yerdan hal qilishingiz mumkin
      </p>
      <div className="flex items-center gap-2">
        <button
          disabled={busy}
          onClick={() => decide(true)}
          className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-50"
        >
          Tasdiqlash
        </button>
        <button
          disabled={busy}
          onClick={() => decide(false)}
          className="border border-slate-300 text-slate-600 rounded-lg px-3 py-1.5 text-xs disabled:opacity-50"
        >
          Rad etish
        </button>
        {msg && <span className="text-xs text-slate-600">{msg}</span>}
      </div>
    </div>
  );
}


/**
 * SO'ROV VAZIFALARI UCHUN UMUMIY TUGMALAR (2026-08-20).
 *
 * Jahongir: "moliya boyicha tolovni notogri kirgizib qoygan shuni
 * torlash sorovini yubordi dashboardda chiqdi shuni dashboarddan
 * o'zgartirib bolmaydi, men uni moliyaga kirib tolovni ozgartirish
 * sorovini topib ozgartirishim kerak, menga shu narsa vazifalar
 * bolimiga kelsin va vazifalardan tasdiqlansan vazifa avtomat
 * bajarilgan bo'lsin".
 *
 * Sarlavhadagi raqamga qarab qaysi so'rov ekani topiladi va shu
 * yerning o'zida Tasdiqlash/Rad etish bosiladi. Server so'rovni
 * bajaradi va BARCHA tasdiqlovchilardagi vazifalarni yopadi.
 */
function RequestTaskActions({
  task,
  onDone,
}: {
  task: TaskRow;
  onDone: () => void;
}) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  if (task.status === "done") return null;

  type Kind = {
    label: string;
    tone: string;
    approve: () => Promise<unknown>;
    reject: (reason: string) => Promise<unknown>;
  };
  let kind: Kind | null = null;
  let m = /To'lovni tuzatish so'rovi #(\d+)/.exec(task.title || "");
  if (m && can(user?.role, PAYMENT_FIX_APPROVE)) {
    const id = Number(m[1]);
    kind = {
      label: "To'lovni tuzatish so'rovi — shu yerdan hal qiling",
      tone: "emerald",
      approve: () => api.post(`/payments/fix-requests/${id}/approve`, {}),
      reject: (reason) =>
        api.post(`/payments/fix-requests/${id}/reject`, { note: reason }),
    };
  }
  if (!kind) {
    m = /Dars ko'chirish so'rovi #(\d+)/.exec(task.title || "");
    if (m && can(user?.role, RESCHEDULE_APPROVE)) {
      const id = Number(m[1]);
      kind = {
        label: "Dars ko'chirish so'rovi — shu yerdan hal qiling",
        tone: "sky",
        approve: () =>
          api.post(`/reschedules/${id}/decide`, { decision: "approved" }),
        reject: (reason) =>
          api.post(`/reschedules/${id}/decide`,
            { decision: "rejected", note: reason }),
      };
    }
  }
  if (!kind) {
    m = /Sovg'a so'rovi #R(\d+)/.exec(task.title || "");
    if (m) {
      const id = Number(m[1]);
      kind = {
        label: "Sovg'a so'rovi — berilganini shu yerda belgilang",
        tone: "amber",
        approve: () =>
          api.post(`/rewards/requests/${id}/give`, { give: true }),
        reject: (reason) =>
          api.post(`/rewards/requests/${id}/give`,
            { give: false, note: reason }),
      };
    }
  }
  if (!kind) return null;

  const TONES: Record<string, string> = {
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-900",
    sky: "bg-sky-50 border-sky-200 text-sky-900",
    amber: "bg-amber-50 border-amber-200 text-amber-900",
  };

  const run = async (ok: boolean) => {
    let reason = "";
    if (!ok) {
      const r = prompt("Rad etish sababi:");
      if (r === null) return;
      reason = r.trim();
    }
    setBusy(true);
    try {
      if (ok) await kind!.approve();
      else await kind!.reject(reason);
      setMsg(ok ? "Tasdiqlandi ✓" : "Rad etildi");
      onDone();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`border rounded-lg p-3 ${TONES[kind.tone]}`}>
      <p className="text-xs mb-2">{kind.label}</p>
      <div className="flex items-center gap-2">
        <button
          disabled={busy}
          onClick={() => run(true)}
          className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-50"
        >
          Tasdiqlash
        </button>
        <button
          disabled={busy}
          onClick={() => run(false)}
          className="border border-slate-300 bg-white text-slate-600 rounded-lg px-3 py-1.5 text-xs disabled:opacity-50"
        >
          Rad etish
        </button>
        {msg && <span className="text-xs">{msg}</span>}
      </div>
    </div>
  );
}
