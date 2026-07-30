import { useEffect, useState } from "react";
import {
  Megaphone, AlertTriangle, Plus, X, Info, Calendar,
  Lightbulb, Inbox, ExternalLink,
} from "lucide-react";
import {
  api, type ContentMeta, type ContentList, type ContentRow,
  type ContentFull, type SmmDashboard, type IdeaRow,
  type RequestRow, type Branch,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { SMM_ACCESS, IDEA_SUBMIT, CONTENT_REQUESTER, can } from "../lib/roles";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  slate900: "bg-slate-800 text-white",
  sky: "bg-sky-100 text-sky-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  orange: "bg-orange-100 text-orange-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
  rose: "bg-rose-100 text-rose-700",
  brown: "bg-yellow-800/20 text-yellow-900",
};

type Tab = "dashboard" | "calendar" | "ideas" | "requests";

const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
  { key: "dashboard", label: "Bugun", icon: Megaphone },
  { key: "calendar", label: "Kontent taqvimi", icon: Calendar },
  { key: "ideas", label: "G'oyalar", icon: Lightbulb },
  { key: "requests", label: "So'rovlar", icon: Inbox },
];

export default function Smm() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("dashboard");
  const isSmm = can(user?.role, SMM_ACCESS);

  if (!can(user?.role, CONTENT_REQUESTER) && !can(user?.role, IDEA_SUBMIT))
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );

  const shown = TABS.filter(
    (t) => isSmm || t.key === "ideas" || t.key === "requests"
  );

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Megaphone size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">SMM</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        G'oya → reja → ssenariy → tasdiq → joylash → natija
      </p>

      <div className="flex gap-1 border-b border-slate-200 mb-5 overflow-x-auto">
        {shown.map((t) => (
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

      {tab === "dashboard" && <DashboardTab />}
      {tab === "calendar" && <CalendarTab />}
      {tab === "ideas" && <IdeasTab isSmm={isSmm} />}
      {tab === "requests" && <RequestsTab isSmm={isSmm} />}
    </div>
  );
}

// ============================================================ Bugun
function DashboardTab() {
  const [d, setD] = useState<SmmDashboard | null>(null);
  const [open, setOpen] = useState<number | null>(null);

  function load() {
    api.get<SmmDashboard>("/smm/dashboard").then(setD);
  }
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const blocks = d.alerts.filter((a) => a.severity === "block");
  const warns = d.alerts.filter((a) => a.severity !== "block");

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {d.cards.map((c) => (
          <div
            key={c.key}
            className={`rounded-xl border p-4 ${
              {
                brand: "bg-brand-50 border-brand-200 text-brand-800",
                good: "bg-emerald-50 border-emerald-200 text-emerald-800",
                bad: "bg-red-50 border-red-200 text-red-800",
                amber: "bg-amber-50 border-amber-200 text-amber-800",
                plain: "bg-white border-slate-200 text-slate-900",
              }[c.tone] || "bg-white border-slate-200 text-slate-900"
            }`}
          >
            <p className="text-xs text-slate-500 mb-1">{c.label}</p>
            <p className="text-lg font-semibold">
              {typeof c.value === "number"
                ? c.value.toLocaleString("ru-RU")
                : c.value}
            </p>
            {c.hint && (
              <p className="text-xs text-slate-400 mt-0.5">{c.hint}</p>
            )}
          </div>
        ))}
      </div>

      {/* Kritik ogohlantirishlar */}
      {d.alerts.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={15} className="text-amber-500" />
            <p className="text-sm font-medium text-slate-700">
              E'tibor talab qiladi
            </p>
            <span className="text-xs text-slate-400">
              {blocks.length} jiddiy · {warns.length} ogohlantirish
            </span>
          </div>
          <div className="space-y-1.5">
            {d.alerts.slice(0, 12).map((a, i) => (
              <button
                key={i}
                onClick={() => a.content_id && setOpen(a.content_id)}
                className={`w-full text-left flex items-start gap-2.5 px-3 py-2 rounded-lg border ${
                  a.severity === "block"
                    ? "border-red-200 bg-red-50"
                    : "border-amber-200 bg-amber-50"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    a.severity === "block" ? "bg-red-500" : "bg-amber-500"
                  }`}
                />
                <span className="flex-1">
                  <span className="text-sm text-slate-800">{a.text}</span>
                  <span className="block text-xs text-slate-500">
                    {a.title}
                    {a.planned_date ? ` · ${formatDate(a.planned_date)}` : ""}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Bugun qilinishi kerak */}
      <p className="text-sm font-medium text-slate-700 mb-2">
        Bugun qilinishi kerak
      </p>
      {d.today.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center bg-white rounded-xl border border-slate-200">
          Bugunga rejalashtirilgan kontent yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {d.today.map((c) => (
            <ContentRowCard key={c.id} c={c} onOpen={() => setOpen(c.id)} />
          ))}
        </div>
      )}

      {d.waiting.length > 0 && (
        <>
          <p className="text-sm font-medium text-slate-700 mt-5 mb-2">
            Tasdiq kutilmoqda ({d.waiting.length})
          </p>
          <div className="space-y-2">
            {d.waiting.map((c) => (
              <ContentRowCard key={c.id} c={c} onOpen={() => setOpen(c.id)} />
            ))}
          </div>
        </>
      )}

      {d.late.length > 0 && (
        <>
          <p className="text-sm font-medium text-slate-700 mt-5 mb-2">
            Kechikkanlar ({d.late.length})
          </p>
          <div className="space-y-2">
            {d.late.map((c) => (
              <ContentRowCard key={c.id} c={c} onOpen={() => setOpen(c.id)} />
            ))}
          </div>
        </>
      )}

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>

      {open !== null && (
        <ContentCard
          id={open}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function ContentRowCard({
  c,
  onOpen,
}: {
  c: ContentRow;
  onOpen: () => void;
}) {
  return (
    <button
      onClick={onOpen}
      className={`w-full text-left flex flex-wrap items-center gap-3 px-4 py-3 rounded-xl border transition hover:border-brand-400 ${
        c.blocked ? "border-red-200 bg-red-50" : "border-slate-200 bg-white"
      }`}
    >
      <span className="text-xs text-slate-400 w-12 shrink-0">
        {c.planned_time || "—"}
      </span>
      <div className="flex-1 min-w-[160px]">
        <p className="text-sm font-medium text-slate-800">{c.title}</p>
        <p className="text-xs text-slate-400">
          {c.platform_label} · {c.pillar_label}
          {c.branch ? ` · ${c.branch}` : ""}
          {c.owner ? ` · ${c.owner}` : ""}
        </p>
      </div>
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
          TONE[c.tone] || TONE.slate
        }`}
      >
        {c.status_label}
      </span>
      {c.status === "approval" && (
        <span className="text-xs text-slate-500">
          {c.approver_role_label}
        </span>
      )}
      {c.warnings.length > 0 && (
        <span className="flex items-center gap-1 text-xs text-red-600">
          <AlertTriangle size={11} /> {c.warnings.length}
        </span>
      )}
    </button>
  );
}

// ==================================================== Kontent taqvimi
function CalendarTab() {
  const [meta, setMeta] = useState<ContentMeta | null>(null);
  const [d, setD] = useState<ContentList | null>(null);
  const [month, setMonth] = useState(() => {
    const t = new Date();
    return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}`;
  });
  const [pillar, setPillar] = useState("");
  const [platform, setPlatform] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  const [y, m] = month.split("-").map(Number);
  const from = `${month}-01`;
  const to = new Date(y, m, 0).toISOString().slice(0, 10);

  function load() {
    api
      .get<ContentList>(
        `/content?date_from=${from}&date_to=${to}` +
          (pillar ? `&pillar=${pillar}` : "") +
          (platform ? `&platform=${platform}` : "")
      )
      .then(setD);
  }
  useEffect(() => {
    api.get<ContentMeta>("/content-meta").then(setMeta);
  }, []);
  useEffect(load, [month, pillar, platform]);

  if (!meta || !d)
    return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  // Kunlar bo'yicha guruhlash
  const byDay: Record<string, ContentRow[]> = {};
  d.rows.forEach((r) => {
    const k = r.planned_date || "—";
    (byDay[k] = byDay[k] || []).push(r);
  });
  const days = Object.keys(byDay).sort();

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <input
          type="month"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
        />
        <select
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
          value={pillar}
          onChange={(e) => setPillar(e.target.value)}
        >
          <option value="">Barcha yo'nalishlar</option>
          {meta.pillars.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
        >
          <option value="">Barcha platformalar</option>
          {meta.platforms.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
        <div className="flex-1" />
        <span
          className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
            d.plan_ok
              ? "bg-emerald-100 text-emerald-700"
              : "bg-amber-100 text-amber-700"
          }`}
        >
          Reja bajarilishi {d.plan_percent}%
        </span>
        {meta.can_edit && (
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            <Plus size={15} /> Kontent
          </button>
        )}
      </div>

      {/* Holat bo'yicha */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {d.by_status.map((s) => (
          <span
            key={s.key}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
              TONE[s.tone] || TONE.slate
            }`}
          >
            {s.label} {s.count}
          </span>
        ))}
      </div>

      {days.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Bu oyga kontent rejalashtirilmagan.
        </p>
      ) : (
        <div className="space-y-4">
          {days.map((day) => (
            <div key={day}>
              <p className="text-xs font-medium text-slate-500 mb-1.5">
                {day === "—" ? "Sanasi belgilanmagan" : formatDate(day)}
              </p>
              <div className="space-y-1.5">
                {byDay[day]
                  .sort((a, b) =>
                    (a.planned_time || "").localeCompare(b.planned_time || "")
                  )
                  .map((c) => (
                    <ContentRowCard
                      key={c.id}
                      c={c}
                      onOpen={() => setOpen(c.id)}
                    />
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {open !== null && (
        <ContentCard
          id={open}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
      {adding && (
        <NewContent
          meta={meta}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function NewContent({
  meta,
  onClose,
  onSaved,
}: {
  meta: ContentMeta;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    title: "",
    platform: meta.platforms[0]?.key || "",
    fmt: "",
    pillar: meta.pillars[0]?.key || "",
    goal: "",
    planned_date: new Date().toISOString().slice(0, 10),
    planned_time: "",
    course: "",
  });
  const [consent, setConsent] = useState(false);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchId, setBranchId] = useState("");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  async function save() {
    if (!f.title.trim()) {
      setErr("Kontent nomini yozing");
      return;
    }
    if (!f.goal) {
      setErr("Maqsadni tanlang — maqsadsiz kontent yaratilmaydi");
      return;
    }
    setSaving(true);
    setErr("");
    try {
      await api.post("/content", {
        ...f,
        branch_id: branchId ? Number(branchId) : null,
        needs_consent: consent,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const goal = meta.goals.find((g) => g.key === f.goal);

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-6 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Yangi kontent</h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Kontent nomi *
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={f.title}
              onChange={(e) => setF({ ...f, title: e.target.value })}
              placeholder="Abdulaziz IELTS 7.0 oldi"
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Sel
              label="Platforma"
              value={f.platform}
              onChange={(v) => setF({ ...f, platform: v })}
              opts={meta.platforms}
            />
            <Sel
              label="Format"
              value={f.fmt}
              onChange={(v) => setF({ ...f, fmt: v })}
              opts={meta.formats}
              empty="— tanlanmagan —"
            />
            <Sel
              label="Yo'nalish"
              value={f.pillar}
              onChange={(v) => setF({ ...f, pillar: v })}
              opts={meta.pillars}
            />
            <Sel
              label="Maqsad *"
              value={f.goal}
              onChange={(v) => setF({ ...f, goal: v })}
              opts={meta.goals}
              empty="— tanlang —"
            />
          </div>
          {goal && (
            <p className="text-xs text-slate-500 -mt-1">
              Natija shu bilan o'lchanadi: <b>{goal.metric}</b>
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Chiqish sanasi
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.planned_date}
                onChange={(e) =>
                  setF({ ...f, planned_date: e.target.value })
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Vaqti
              </label>
              <input
                type="time"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.planned_time}
                onChange={(e) =>
                  setF({ ...f, planned_time: e.target.value })
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Filial
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={branchId}
                onChange={(e) => setBranchId(e.target.value)}
              >
                <option value="">— hammasi —</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Kurs
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.course}
                onChange={(e) => setF({ ...f, course: e.target.value })}
                placeholder="IELTS"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            Kontentda o'quvchi rasmi yoki videosi bor
          </label>
          {consent && (
            <p className="text-xs text-amber-600 -mt-1">
              Ota-ona roziligi belgilanmaguncha joylashga ruxsat berilmaydi.
            </p>
          )}

          {err && <p className="text-sm text-red-600">{err}</p>}
          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Yaratish"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Sel({
  label,
  value,
  onChange,
  opts,
  empty,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  opts: { key: string; label: string }[];
  empty?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">
        {label}
      </label>
      <select
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {empty && <option value="">{empty}</option>}
        {opts.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export { ContentCard };

// ================================================ Kontent kartasi
function ContentCard({ id, onClose }: { id: number; onClose: () => void }) {
  const { user } = useAuth();
  const [d, setD] = useState<ContentFull | null>(null);
  const [meta, setMeta] = useState<ContentMeta | null>(null);
  const [tab, setTab] = useState<"brief" | "matn" | "kadr" | "natija">(
    "brief"
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function load() {
    api.get<ContentFull>(`/content/${id}`).then(setD);
  }
  useEffect(() => {
    load();
    api.get<ContentMeta>("/content-meta").then(setMeta);
  }, [id]);

  if (!d || !meta)
    return (
      <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8">
          <p className="text-sm text-slate-400">Yuklanmoqda...</p>
        </div>
      </div>
    );

  const canEdit = meta.can_edit;
  const isApprover = user?.role === d.approver_role;

  async function save(patch: Record<string, unknown>) {
    setBusy(true);
    setErr("");
    try {
      await api.put(`/content/${id}`, patch);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(status: string) {
    setBusy(true);
    setErr("");
    try {
      await api.post(`/content/${id}/status`, { status });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function decide(decision: string) {
    const comment =
      decision === "approved"
        ? undefined
        : prompt("Nima o'zgartirish kerak?") || undefined;
    setBusy(true);
    try {
      await api.post(`/content/${id}/approve`, { decision, comment });
      load();
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    const url = prompt("Post havolasi:");
    if (!url) return;
    setBusy(true);
    setErr("");
    try {
      await api.post(`/content/${id}/publish`, { post_url: url });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function move() {
    const day = prompt("Yangi sana (YYYY-MM-DD):", d?.planned_date || "");
    if (!day) return;
    const reason = prompt("Nega ko'chirilyapti?");
    if (!reason) return;
    setBusy(true);
    setErr("");
    try {
      await api.post(`/content/${id}/move`, {
        planned_date: day,
        reason,
      });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  const idx = meta.flow.indexOf(d.status);
  const next = idx >= 0 && idx < meta.flow.length - 1 ? meta.flow[idx + 1] : null;

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-start justify-center z-50 px-4 py-6 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl">
        {/* Sarlavha */}
        <div className="p-5 border-b border-slate-100">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    TONE[d.tone] || TONE.slate
                  }`}
                >
                  {d.status_label}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs ${
                    TONE[d.pillar_tone] || TONE.slate
                  }`}
                >
                  {d.pillar_label}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {d.code}
                </span>
              </div>
              <h2 className="font-semibold text-slate-900">{d.title}</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {d.platform_label} · {d.format_label} ·{" "}
                {d.planned_date ? formatDate(d.planned_date) : "sanasiz"}
                {d.planned_time ? ` ${d.planned_time}` : ""}
                {d.owner ? ` · ${d.owner}` : ""}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Maqsad: <b>{d.goal_label}</b> — natija{" "}
                {d.goal_metric.toLowerCase()} bilan o'lchanadi
              </p>
            </div>
            <button onClick={onClose} className="text-slate-400">
              <X size={18} />
            </button>
          </div>

          {d.warnings.length > 0 && (
            <div className="mt-3 space-y-1">
              {d.warnings.map((w, i) => (
                <p
                  key={i}
                  className={`text-xs flex items-center gap-1.5 ${
                    w.severity === "block" ? "text-red-600" : "text-amber-600"
                  }`}
                >
                  <AlertTriangle size={11} /> {w.text}
                </p>
              ))}
            </div>
          )}

          {/* Harakatlar */}
          {canEdit && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {next && d.status !== "published" && (
                <button
                  onClick={() => setStatus(next)}
                  disabled={busy}
                  className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-medium disabled:opacity-50"
                >
                  {meta.statuses.find((s) => s.key === next)?.label} ga o'tkazish
                </button>
              )}
              {d.status === "ready" && (
                <button
                  onClick={publish}
                  disabled={busy}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-white text-xs font-medium"
                >
                  Joylandi deb belgilash
                </button>
              )}
              {d.needs_consent && !d.consent_ok && (
                <button
                  onClick={() => save({ consent_ok: true })}
                  disabled={busy}
                  className="px-3 py-1.5 rounded-lg border border-emerald-300 text-emerald-700 text-xs font-medium"
                >
                  Rozilik olindi
                </button>
              )}
              <button
                onClick={move}
                disabled={busy}
                className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-xs"
              >
                Boshqa kunga
              </button>
            </div>
          )}

          {d.status === "approval" && isApprover && (
            <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-100">
              <span className="text-xs text-slate-500 self-center mr-1">
                Sizning qaroringiz:
              </span>
              {meta.decisions.map((x) => (
                <button
                  key={x.key}
                  onClick={() => decide(x.key)}
                  disabled={busy}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                    TONE[x.tone] || TONE.slate
                  }`}
                >
                  {x.label}
                </button>
              ))}
            </div>
          )}
          {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
        </div>

        {/* Tablar */}
        <div className="flex gap-1 px-5 border-b border-slate-100">
          {(
            [
              ["brief", "Brief"],
              ["matn", "Matn"],
              ["kadr", `Kadrlar (${d.shots.length})`],
              ["natija", "Tarix va tasdiq"],
            ] as const
          ).map(([k, l]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`px-3 py-2.5 text-sm font-medium border-b-2 -mb-px ${
                tab === k
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        <div className="p-5">
          {tab === "brief" && (
            <div className="grid md:grid-cols-2 gap-3">
              {(
                [
                  ["problem", "Asosiy muammo"],
                  ["message", "Asosiy xabar"],
                  ["hook", "Hook"],
                  ["audience", "Auditoriya"],
                  ["location", "Lokatsiya"],
                  ["participants", "Ishtirokchilar"],
                  ["props", "Rekvizitlar"],
                  ["duration", "Davomiyligi"],
                  ["music", "Musiqa"],
                  ["design_format", "Dizayn formati"],
                  ["cta", "CTA"],
                  ["references", "Referenslar"],
                ] as const
              ).map(([k, l]) => (
                <Field
                  key={k}
                  label={l}
                  value={(d[k] as string) || ""}
                  canEdit={canEdit}
                  onSave={(v) => save({ [k]: v })}
                />
              ))}
            </div>
          )}

          {tab === "matn" && (
            <div className="space-y-3">
              {(
                [
                  ["script", "Ssenariy"],
                  ["caption", "Caption (o'zbekcha)"],
                  ["caption_ru", "Caption (ruscha)"],
                  ["caption_en", "Caption (inglizcha)"],
                  ["hashtags", "Hashtaglar"],
                  ["story_text", "Story matnlari"],
                  ["on_video_text", "Video ichidagi yozuvlar"],
                ] as const
              ).map(([k, l]) => (
                <Field
                  key={k}
                  label={l}
                  value={(d[k] as string) || ""}
                  canEdit={canEdit}
                  big
                  onSave={(v) => save({ [k]: v })}
                />
              ))}
            </div>
          )}

          {tab === "kadr" && (
            <ShotList d={d} canEdit={canEdit} onDone={load} />
          )}

          {tab === "natija" && (
            <div className="space-y-4">
              {d.approvals.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-slate-700 mb-2">
                    Tasdiqlash tarixi
                  </p>
                  <div className="space-y-1.5">
                    {d.approvals.map((a) => (
                      <div
                        key={a.id}
                        className="flex flex-wrap items-start gap-2 px-3 py-2 rounded-lg border border-slate-100"
                      >
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            TONE[a.tone] || TONE.slate
                          }`}
                        >
                          {a.decision_label}
                        </span>
                        <span className="flex-1 min-w-[140px]">
                          {a.comment && (
                            <span className="block text-sm text-slate-700">
                              {a.comment}
                            </span>
                          )}
                          {a.quote && (
                            <span className="block text-xs text-slate-400 italic">
                              "{a.quote}"
                            </span>
                          )}
                        </span>
                        <span className="text-xs text-slate-400">
                          {a.by || a.role_label}
                          {a.date ? ` · ${formatDate(a.date)}` : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">
                  Matn versiyalari ({d.versions.length})
                </p>
                {d.versions.length === 0 ? (
                  <p className="text-sm text-slate-400">
                    Hali o'zgartirilmagan.
                  </p>
                ) : (
                  <div className="space-y-1.5">
                    {d.versions.slice(0, 12).map((v) => (
                      <div
                        key={v.id}
                        className="px-3 py-2 rounded-lg border border-slate-100 text-xs"
                      >
                        <p className="text-slate-500">
                          {v.field} · {v.by}
                          {v.date ? ` · ${formatDate(v.date)}` : ""}
                        </p>
                        {v.old && (
                          <p className="text-red-500 line-through truncate">
                            {v.old}
                          </p>
                        )}
                        <p className="text-slate-700 truncate">{v.new}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {d.post_url && (
                <a
                  href={d.post_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-brand-600 hover:underline"
                >
                  <ExternalLink size={13} /> Postni ochish
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  canEdit,
  big,
  onSave,
}: {
  label: string;
  value: string;
  canEdit: boolean;
  big?: boolean;
  onSave: (v: string) => void;
}) {
  const [v, setV] = useState(value);
  const [dirty, setDirty] = useState(false);
  useEffect(() => {
    setV(value);
    setDirty(false);
  }, [value]);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <label className="text-xs font-medium text-slate-500">{label}</label>
        {dirty && (
          <button
            onClick={() => {
              onSave(v);
              setDirty(false);
            }}
            className="text-xs text-brand-600 hover:underline"
          >
            saqlash
          </button>
        )}
      </div>
      {big ? (
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm h-24 disabled:bg-slate-50"
          value={v}
          disabled={!canEdit}
          onChange={(e) => {
            setV(e.target.value);
            setDirty(true);
          }}
        />
      ) : (
        <input
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
          value={v}
          disabled={!canEdit}
          onChange={(e) => {
            setV(e.target.value);
            setDirty(true);
          }}
        />
      )}
    </div>
  );
}

function ShotList({
  d,
  canEdit,
  onDone,
}: {
  d: ContentFull;
  canEdit: boolean;
  onDone: () => void;
}) {
  const [text, setText] = useState("");

  async function add() {
    if (!text.trim()) return;
    await api.post(`/content/${d.id}/shots`, { text });
    setText("");
    onDone();
  }
  async function setState(sid: number, state: string) {
    await api.post(`/content-shots/${sid}`, { state });
    onDone();
  }

  const STATES: [string, string, string][] = [
    ["todo", "Olinmagan", "bg-slate-100 text-slate-600"],
    ["done", "Olingan", "bg-emerald-100 text-emerald-700"],
    ["retake", "Qayta olish", "bg-amber-100 text-amber-700"],
  ];

  return (
    <div>
      {canEdit && (
        <div className="flex gap-2 mb-3">
          <input
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Kadr: o'quvchining markazga kirishi"
            onKeyDown={(e) => e.key === "Enter" && add()}
          />
          <button
            onClick={add}
            className="px-3 py-2 rounded-lg bg-brand-600 text-white text-sm"
          >
            <Plus size={15} />
          </button>
        </div>
      )}
      {d.shots.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Kadrlar ro'yxati bo'sh.
        </p>
      ) : (
        <div className="space-y-1.5">
          {d.shots.map((s) => (
            <div
              key={s.id}
              className="flex flex-wrap items-center gap-2 px-3 py-2 rounded-lg border border-slate-100"
            >
              <span className="text-xs text-slate-400 w-5">{s.no}</span>
              <span className="text-sm text-slate-700 flex-1 min-w-[140px]">
                {s.text}
              </span>
              {STATES.map(([k, l, cls]) => (
                <button
                  key={k}
                  onClick={() => canEdit && setState(s.id, k)}
                  disabled={!canEdit}
                  className={`px-2 py-0.5 rounded-full text-xs ${
                    s.state === k ? cls : "text-slate-300 hover:text-slate-500"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ================================================== G'oyalar bazasi
function IdeasTab({ isSmm }: { isSmm: boolean }) {
  const [d, setD] = useState<{
    rows: IdeaRow[]; counts: Record<string, number>; can_triage: boolean;
  } | null>(null);
  const [meta, setMeta] = useState<ContentMeta | null>(null);
  const [status, setStatus] = useState("");
  const [adding, setAdding] = useState(false);

  type IdeaList = {
    rows: IdeaRow[]; counts: Record<string, number>; can_triage: boolean;
  };
  function load() {
    api
      .get<IdeaList>(`/content-ideas${status ? `?status=${status}` : ""}`)
      .then(setD);
  }
  useEffect(() => {
    api.get<ContentMeta>("/content-meta").then(setMeta).catch(() => setMeta(null));
  }, []);
  useEffect(load, [status]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <button
          onClick={() => setStatus("")}
          className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
            status === ""
              ? "bg-slate-100 border-slate-300 text-slate-700"
              : "bg-white border-slate-200 text-slate-500"
          }`}
        >
          Hammasi
        </button>
        {(meta?.idea_statuses || []).map((s) => (
          <button
            key={s.key}
            onClick={() => setStatus(s.key)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
              status === s.key
                ? "bg-slate-100 border-slate-300 text-slate-700"
                : "bg-white border-slate-200 text-slate-500"
            }`}
          >
            {s.label} {d.counts[s.key] || 0}
          </button>
        ))}
        <div className="flex-1" />
        <button
          onClick={() => setAdding(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium"
        >
          <Plus size={15} /> G'oya
        </button>
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali g'oya yo'q. Har qanday xodim g'oya yubora oladi.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((i) => (
            <div
              key={i.id}
              className="rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-start gap-2">
                <div className="flex-1 min-w-[180px]">
                  <p className="text-sm font-medium text-slate-800">
                    {i.title}
                  </p>
                  {i.description && (
                    <p className="text-xs text-slate-500 mt-0.5">
                      {i.description}
                    </p>
                  )}
                  <p className="text-xs text-slate-400 mt-1">
                    {i.pillar_label} · {i.platform_label} · {i.author}
                    {i.date ? ` · ${formatDate(i.date)}` : ""}
                  </p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    TONE[i.tone] || TONE.slate
                  }`}
                >
                  {i.status_label}
                </span>
              </div>
              {isSmm && i.status !== "converted" && (
                <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-50">
                  {(meta?.idea_statuses || [])
                    .filter((s) => s.key !== i.status)
                    .map((s) => (
                      <button
                        key={s.key}
                        onClick={async () => {
                          await api.post(`/content-ideas/${i.id}`, {
                            status: s.key,
                          });
                          load();
                        }}
                        className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-brand-300"
                      >
                        {s.label}
                      </button>
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {adding && meta && (
        <NewIdea
          meta={meta}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function NewIdea({
  meta,
  onClose,
  onSaved,
}: {
  meta: ContentMeta;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    title: "",
    description: "",
    pillar: meta.pillars[0]?.key || "",
    platform: meta.platforms[0]?.key || "",
    reference: "",
  });
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!f.title.trim()) return;
    setSaving(true);
    try {
      await api.post("/content-ideas", f);
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Yangi g'oya</h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={f.title}
            onChange={(e) => setF({ ...f, title: e.target.value })}
            placeholder="G'oya nomi"
            autoFocus
          />
          <textarea
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm h-20"
            value={f.description}
            onChange={(e) => setF({ ...f, description: e.target.value })}
            placeholder="Qisqa tavsif"
          />
          <div className="grid grid-cols-2 gap-3">
            <Sel
              label="Yo'nalish"
              value={f.pillar}
              onChange={(v) => setF({ ...f, pillar: v })}
              opts={meta.pillars}
            />
            <Sel
              label="Platforma"
              value={f.platform}
              onChange={(v) => setF({ ...f, platform: v })}
              opts={meta.platforms}
            />
          </div>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={f.reference}
            onChange={(e) => setF({ ...f, reference: e.target.value })}
            placeholder="Referens havolasi (ixtiyoriy)"
          />
          <p className="text-xs text-slate-400">
            G'oya SMM tasdiqlagunicha kontent rejaga tushmaydi.
          </p>
          <button
            onClick={save}
            disabled={saving || !f.title.trim()}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-50"
          >
            {saving ? "Yuborilmoqda..." : "Yuborish"}
          </button>
        </div>
      </div>
    </div>
  );
}

// =================================================== Ichki so'rovlar
function RequestsTab({ isSmm }: { isSmm: boolean }) {
  const [d, setD] = useState<{
    rows: RequestRow[]; counts: Record<string, number>; can_decide: boolean;
  } | null>(null);
  const [meta, setMeta] = useState<ContentMeta | null>(null);
  const [adding, setAdding] = useState(false);

  type ReqList = {
    rows: RequestRow[]; counts: Record<string, number>; can_decide: boolean;
  };
  function load() {
    api.get<ReqList>("/content-requests").then(setD);
  }
  useEffect(() => {
    api.get<ContentMeta>("/content-meta").then(setMeta).catch(() => setMeta(null));
  }, []);
  useEffect(load, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <p className="text-sm text-slate-500">
          Boshqa bo'limlar SMMga tartibli so'rov yuboradi
        </p>
        <div className="flex-1" />
        <button
          onClick={() => setAdding(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium"
        >
          <Plus size={15} /> So'rov
        </button>
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali so'rov yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <div
              key={r.id}
              className="rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-start gap-2">
                <div className="flex-1 min-w-[180px]">
                  <p className="text-sm font-medium text-slate-800">
                    {r.course || "Kontent"} — {r.branch}
                    {r.students_needed
                      ? ` · ${r.students_needed} o'quvchi kerak`
                      : ""}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {r.offer || "—"}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {r.requester} ({r.department}) ·{" "}
                    {r.goal_label}
                    {r.group_time ? ` · ${r.group_time}` : ""}
                    {r.deadline ? ` · ${formatDate(r.deadline)} gacha` : ""}
                  </p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    TONE[r.tone] || TONE.slate
                  }`}
                >
                  {r.status_label}
                </span>
              </div>
              {isSmm && r.status === "new" && (
                <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-slate-50">
                  {(meta?.request_statuses || [])
                    .filter((s) => s.key !== "new")
                    .map((s) => (
                      <button
                        key={s.key}
                        onClick={async () => {
                          await api.post(`/content-requests/${r.id}`, {
                            status: s.key,
                          });
                          load();
                        }}
                        className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-brand-300"
                      >
                        {s.label}
                      </button>
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {adding && meta && (
        <NewRequest
          meta={meta}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function NewRequest({
  meta,
  onClose,
  onSaved,
}: {
  meta: ContentMeta;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    course: "",
    goal: "lead",
    offer: "",
    group_time: "",
    students_needed: "",
    start_date: "",
    deadline: "",
    cta: "",
  });
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchId, setBranchId] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  async function save() {
    setSaving(true);
    try {
      await api.post("/content-requests", {
        ...f,
        branch_id: branchId ? Number(branchId) : null,
        students_needed: f.students_needed
          ? Number(f.students_needed)
          : null,
        start_date: f.start_date || null,
        deadline: f.deadline || null,
      });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-6 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">SMMga so'rov</h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Filial
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={branchId}
                onChange={(e) => setBranchId(e.target.value)}
              >
                <option value="">— tanlang —</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Kurs
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.course}
                onChange={(e) => setF({ ...f, course: e.target.value })}
                placeholder="Elementary"
              />
            </div>
            <Sel
              label="Maqsad"
              value={f.goal}
              onChange={(v) => setF({ ...f, goal: v })}
              opts={meta.goals}
            />
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Nechta o'quvchi kerak
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.students_needed}
                onChange={(e) =>
                  setF({ ...f, students_needed: e.target.value })
                }
                placeholder="6"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Guruh vaqti
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.group_time}
                onChange={(e) => setF({ ...f, group_time: e.target.value })}
                placeholder="18:00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Boshlanish sanasi
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.start_date}
                onChange={(e) => setF({ ...f, start_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Deadline
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={f.deadline}
                onChange={(e) => setF({ ...f, deadline: e.target.value })}
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Taklif
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={f.offer}
              onChange={(e) => setF({ ...f, offer: e.target.value })}
              placeholder="Birinchi oyga 20% chegirma"
            />
          </div>
          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Yuborilmoqda..." : "Yuborish"}
          </button>
        </div>
      </div>
    </div>
  );
}
