import { useEffect, useState } from "react";
import {
  AlertTriangle, FileText, Plane, LogOut, Info, X, Users, Briefcase,
  UserPlus, CalendarCheck, Target, Timer,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
  CartesianGrid, Legend, PieChart, Pie,
} from "recharts";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  amber: "bg-amber-100 text-amber-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
};

/* HR DASHBOARD (2026-10-22, Jahongir: "hr dashboard ham professional,
   statistika va barchartlar qo'shib ber rangli"). Avvalgi hamma narsa
   joyida: ogohlantirishlar, 8 ta ko'rsatkich, rad sabablari, izoh.
   Qo'shildi: kelgan/ketgan (6 oy), lavozim va filial bo'yicha xodimlar,
   nomzodlar voronkasi va manbalari — rangli grafiklarda. */
const PALETTE = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#f43f5e",
                 "#8b5cf6", "#14b8a6", "#f97316", "#06b6d4", "#84cc16",
                 "#ec4899", "#64748b"];

const KPI: Record<string, { icon: Any; grad: string; tint: string }> = {
  staff: { icon: Users, grad: "from-indigo-500 to-blue-600", tint: "from-indigo-50" },
  vacancies: { icon: Briefcase, grad: "from-violet-500 to-purple-600", tint: "from-violet-50" },
  pipeline: { icon: UserPlus, grad: "from-sky-400 to-cyan-600", tint: "from-sky-50" },
  interviews: { icon: CalendarCheck, grad: "from-emerald-400 to-teal-600", tint: "from-emerald-50" },
  on_leave: { icon: Plane, grad: "from-amber-400 to-orange-500", tint: "from-amber-50" },
  pips: { icon: Target, grad: "from-rose-400 to-pink-600", tint: "from-rose-50" },
  offboarding: { icon: LogOut, grad: "from-slate-500 to-slate-700", tint: "from-slate-100" },
  tth: { icon: Timer, grad: "from-fuchsia-500 to-purple-600", tint: "from-fuchsia-50" },
};

function Panel({ title, sub, children, className = "" }: {
  title: string; sub?: string; children: React.ReactNode; className?: string;
}) {
  return (
    <div className={`bg-white border border-slate-200/80 rounded-2xl p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_8px_24px_-12px_rgba(15,23,42,0.12)] ${className}`}>
      <h3 className="text-[15px] font-bold text-slate-900">{title}</h3>
      {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      <div className="mt-4">{children}</div>
    </div>
  );
}

function Empty({ text = "Hozircha ma'lumot yo'q" }: { text?: string }) {
  return (
    <p className="text-sm text-slate-400 py-10 text-center">{text}</p>
  );
}

const TIP = {
  contentStyle: {
    borderRadius: 12, border: "1px solid #e2e8f0",
    boxShadow: "0 10px 30px -12px rgba(15,23,42,.25)", fontSize: 12,
  },
  cursor: { fill: "rgba(99,102,241,0.06)" },
};

/** Gorizontal rangli ustunlar — har ustun o'z rangida. */
function HBars({ rows, colors = PALETTE, unit = "" }: {
  rows: { label: string; value: number }[]; colors?: string[]; unit?: string;
}) {
  if (!rows.length || rows.every((r) => !r.value)) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height={Math.max(140, rows.length * 34 + 16)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 4, right: 28, top: 0, bottom: 0 }}>
        <XAxis type="number" hide allowDecimals={false} />
        <YAxis type="category" dataKey="label" width={150} tickLine={false}
               axisLine={false} tick={{ fontSize: 12, fill: "#475569" }} />
        <Tooltip {...TIP} formatter={(v: Any) => [`${v}${unit}`, "Soni"]} />
        <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18}
             label={{ position: "right", fontSize: 12, fill: "#0f172a", fontWeight: 600 }}>
          {rows.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** HR grafiklari bloki — "Umumiy holat" va "HR analitika" ikkalasida
 *  (2026-10-22, Jahongir: "barchart bo'lmabdiku" — analitika tabida
 *  grafik faqat nomzod bo'lsa chiqardi). ch — /hr/overview "charts". */
export function HrCharts({ ch, rejects }: { ch: Any; rejects: Any[] }) {
  const funnel = (ch.funnel || []) as Any[];
  const FUNNEL_COLORS = ["#6366f1", "#0ea5e9", "#06b6d4", "#14b8a6",
                         "#10b981", "#22c55e", "#f43f5e"];
  const d = { reject_reasons: rejects };
  return (
    <>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <Panel className="xl:col-span-2" title="Kelgan va ketgan xodimlar"
               sub="Oxirgi 6 oy — oyma-oy">
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="text-xs font-semibold rounded-full px-2.5 py-1 bg-emerald-50 text-emerald-700">
              Kelgan: {ch.hired_6m ?? 0}
            </span>
            <span className="text-xs font-semibold rounded-full px-2.5 py-1 bg-rose-50 text-rose-700">
              Ketgan: {ch.left_6m ?? 0}
            </span>
            {ch.turnover_6m != null && (
              <span className="text-xs font-semibold rounded-full px-2.5 py-1 bg-indigo-50 text-indigo-700">
                Kadrlar almashinuvi: {ch.turnover_6m}%
              </span>
            )}
          </div>
          {(ch.flow || []).length ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={ch.flow} margin={{ left: -18, right: 6, top: 6 }}>
                <defs>
                  <linearGradient id="hrHired" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#34d399" />
                    <stop offset="100%" stopColor="#059669" />
                  </linearGradient>
                  <linearGradient id="hrLeft" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#fb7185" />
                    <stop offset="100%" stopColor="#e11d48" />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#eef2f7" />
                <XAxis dataKey="month" tickLine={false} axisLine={false}
                       tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false}
                       tick={{ fontSize: 12, fill: "#94a3b8" }} />
                <Tooltip {...TIP} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="hired" name="Kelgan" fill="url(#hrHired)" radius={[8, 8, 0, 0]} barSize={22} />
                <Bar dataKey="left" name="Ketgan" fill="url(#hrLeft)" radius={[8, 8, 0, 0]} barSize={22} />
              </BarChart>
            </ResponsiveContainer>
          ) : <Empty />}
        </Panel>

        <Panel title="Nomzodlar qayerdan keladi" sub="Manba bo'yicha, barcha nomzodlar">
          {(ch.sources || []).length ? (
            <>
              <ResponsiveContainer width="100%" height={190}>
                <PieChart>
                  <Pie data={ch.sources} dataKey="value" nameKey="label"
                       innerRadius={52} outerRadius={82} paddingAngle={3}
                       stroke="none">
                    {(ch.sources as Any[]).map((_, i) => (
                      <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                    ))}
                  </Pie>
                  <Tooltip {...TIP} />
                </PieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-2">
                {(ch.sources as Any[]).map((s, i) => (
                  <span key={s.label} className="flex items-center gap-1.5 text-xs text-slate-600 min-w-0">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ background: PALETTE[i % PALETTE.length] }} />
                    <span className="truncate">{s.label}</span>
                    <b className="ml-auto text-slate-900">{s.value}</b>
                  </span>
                ))}
              </div>
            </>
          ) : <Empty />}
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Panel title="Xodimlar lavozim bo'yicha" sub="Faol xodimlar">
          <HBars rows={ch.by_role || []} />
        </Panel>
        <Panel title="Xodimlar filial bo'yicha" sub="Asosiy filiali bo'yicha">
          <HBars rows={ch.by_branch || []}
                 colors={["#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6", "#f43f5e", "#14b8a6"]} />
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Panel title="Ishga olish voronkasi" sub="Nomzodlar qaysi bosqichda">
          {funnel.some((f) => f.value) ? (
            <div className="space-y-2">
              {funnel.map((f, i) => {
                const max = Math.max(1, ...funnel.map((x) => x.value));
                const w = Math.max(f.value ? 6 : 0, Math.round(100 * f.value / max));
                return (
                  <div key={f.key} className="flex items-center gap-3">
                    <span className="w-40 shrink-0 text-xs text-slate-600 truncate">{f.label}</span>
                    <div className="flex-1 h-6 rounded-lg bg-slate-100 overflow-hidden">
                      <div className="h-full rounded-lg transition-all"
                           style={{ width: `${w}%`, background: `linear-gradient(90deg, ${FUNNEL_COLORS[i % FUNNEL_COLORS.length]}cc, ${FUNNEL_COLORS[i % FUNNEL_COLORS.length]})` }} />
                    </div>
                    <b className="w-8 text-right text-sm text-slate-900">{f.value}</b>
                  </div>
                );
              })}
            </div>
          ) : <Empty />}
        </Panel>
        <Panel title="Rad etish sabablari" sub="Nega odam topilmayapti">
          <HBars rows={(d.reject_reasons || []).map((r: Any) => ({ label: r.label, value: r.count }))}
                 colors={["#f43f5e", "#f97316", "#f59e0b", "#ec4899", "#8b5cf6", "#64748b"]} />
        </Panel>
      </div>
    </>
  );
}

/** "HR analitika" uchun: /hr/overview dan faqat grafiklar. */
export function HrStaffCharts() {
  const [d, setD] = useState<Any>(null);
  useEffect(() => {
    api.get<Any>("/hr/overview").then(setD).catch(() => setD(false));
  }, []);
  if (d === false) return null;
  if (!d) return <div className="h-64 rounded-2xl bg-slate-100 animate-pulse" />;
  return (
    <div className="space-y-5">
      <HrCharts ch={d.charts || {}} rejects={d.reject_reasons || []} />
    </div>
  );
}

/** HR umumiy ko'rinishi: barcha fazalarning signallari bitta ekranda. */
export function HrOverviewTab() {
  const [d, setD] = useState<Any>(null);
  useEffect(() => {
    api.get<Any>("/hr/overview").then(setD).catch(() => {});
  }, []);
  if (!d) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;
  const ch = d.charts || {};

  return (
    <div className="space-y-5">
      {d.alerts.length > 0 && (
        <div className="space-y-1.5">
          {d.alerts.map((a: Any, i: number) => (
            <p
              key={i}
              className={`text-sm rounded-xl px-3.5 py-2.5 border flex items-center gap-2 font-medium ${
                a.tone === "red"
                  ? "bg-gradient-to-r from-red-50 to-white border-red-200 text-red-800"
                  : "bg-gradient-to-r from-amber-50 to-white border-amber-200 text-amber-800"
              }`}
            >
              <AlertTriangle size={15} className="shrink-0" />
              {a.text}
            </p>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {d.cards.map((c: Any) => {
          const k = KPI[c.key] || KPI.staff;
          const Icon = k.icon;
          return (
            <div
              key={c.key}
              className={`relative overflow-hidden rounded-2xl border border-slate-200/80 bg-gradient-to-br ${k.tint} to-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_8px_24px_-14px_rgba(15,23,42,0.18)]`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-medium text-slate-500 leading-snug">{c.label}</p>
                <span className={`grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br ${k.grad} text-white shadow-md shrink-0`}>
                  <Icon size={17} />
                </span>
              </div>
              <p className="font-[family-name:var(--font-display)] text-3xl font-extrabold text-slate-900 mt-1 tracking-tight">
                {c.value}
              </p>
            </div>
          );
        })}
      </div>

      <HrCharts ch={ch} rejects={d.reject_reasons || []} />

      <p className="text-xs text-slate-500 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}

/** Hujjatlar, ta'til va ketish — bitta "hayotiy sikl" tabi. */
export function HrLifecycleTab() {
  const [sub, setSub] = useState<"docs" | "leaves" | "offboard">("leaves");
  return (
    <div>
      <div className="flex gap-1.5 mb-4">
        {[
          { key: "leaves", label: "Ta'til", icon: Plane },
          { key: "docs", label: "Hujjatlar", icon: FileText },
          { key: "offboard", label: "Ketish", icon: LogOut },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setSub(t.key as Any)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${
              sub === t.key
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>
      {sub === "docs" && <DocsSub />}
      {sub === "leaves" && <LeavesSub />}
      {sub === "offboard" && <OffboardSub />}
    </div>
  );
}

function DocsSub() {
  const [d, setD] = useState<Any>(null);
  const load = () => {
    api.get<Any>("/hr/documents").then(setD).catch(() => {});
  };
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {(d.expired.length > 0 || d.expiring.length > 0) && (
        <p className="text-sm rounded-lg px-3 py-2 mb-3 bg-red-50 border border-red-200 text-red-800">
          {d.expired.length > 0 && `${d.expired.length} hujjat muddati o'tgan. `}
          {d.expiring.length > 0 &&
            `${d.expiring.length} hujjat ${d.warn_days} kun ichida tugaydi.`}
        </p>
      )}
      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
              <th className="text-left px-3 py-2.5 font-medium">Hujjat</th>
              <th className="text-left px-3 py-2.5 font-medium">Raqam</th>
              <th className="text-right px-4 py-2.5 font-medium">Muddati</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.rows.map((r: Any) => (
              <tr key={r.id} className={r.expired ? "bg-red-50/50" : ""}>
                <td className="px-4 py-2.5 text-slate-800">{r.user}</td>
                <td className="px-3 py-2.5 text-slate-600">{r.kind_label}</td>
                <td className="px-3 py-2.5 text-slate-500">
                  {r.number || "—"}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {r.expires_on ? (
                    <span
                      className={
                        r.expired
                          ? "text-red-600 font-medium"
                          : r.expiring
                          ? "text-amber-600 font-medium"
                          : "text-slate-500"
                      }
                    >
                      {r.expires_on}
                      {r.days_left != null && r.days_left >= 0
                        ? ` (${r.days_left} kun)`
                        : " (o'tgan)"}
                    </span>
                  ) : (
                    <span className="text-slate-300">muddatsiz</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Hujjat yo'q. Xodim kartasidan qo'shiladi.
          </p>
        )}
      </div>
    </div>
  );
}

function LeavesSub() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    api.get<Any>("/hr/leaves").then(setD).catch(() => {});
  };
  useEffect(load, []);

  const decide = async (id: number, decision: string) => {
    setErr("");
    try {
      await api.post(`/hr/leaves/${id}/decide`, { decision });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {d.today.length > 0 && (
        <p className="text-sm rounded-lg px-3 py-2 mb-3 bg-sky-50 border border-sky-200 text-sky-800">
          Bugun ta'tilda: {d.today.map((x: Any) => x.user).join(", ")}
        </p>
      )}
      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
      <div className="space-y-2">
        {d.rows.map((l: Any) => (
          <div
            key={l.id}
            className="bg-white border border-slate-200 rounded-xl p-3.5"
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-slate-400">
                {l.public_id}
              </span>
              <span className="text-sm font-medium text-slate-900">
                {l.user}
              </span>
              <span className="text-xs text-slate-500">
                {l.kind_label} · {l.date_from} — {l.date_to} ({l.days} kun)
              </span>
              <span
                className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                  TONE[l.status_tone] || TONE.slate
                }`}
              >
                {l.status_label}
              </span>
            </div>
            {l.replacement && (
              <p className="text-xs text-slate-500 mt-1">
                O'rinbosar: {l.replacement}
              </p>
            )}
            {l.reason && (
              <p className="text-xs text-slate-500 mt-0.5">{l.reason}</p>
            )}
            {l.status === "pending" && d.can_approve && (
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => decide(l.id, "approved")}
                  className="bg-emerald-600 text-white rounded-lg px-3 py-1 text-xs font-medium"
                >
                  Tasdiqlash
                </button>
                <button
                  onClick={() => decide(l.id, "rejected")}
                  className="border border-slate-300 text-slate-600 rounded-lg px-3 py-1 text-xs"
                >
                  Rad etish
                </button>
              </div>
            )}
          </div>
        ))}
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Ta'til so'rovi yo'q.
          </p>
        )}
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}

function OffboardSub() {
  const [d, setD] = useState<Any>(null);
  const [open, setOpen] = useState<Any>(null);
  const load = () => {
    api.get<Any>("/hr/offboarding").then(setD).catch(() => {});
  };
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {d.ours_percent != null && (
        <p className="text-sm rounded-lg px-3 py-2 mb-3 bg-slate-50 border border-slate-200 text-slate-700">
          Ketishlarning <b>{d.ours_percent}%</b> i bizga bog'liq sabablar —
          bu ustidan ishlash mumkin bo'lgan qism.
        </p>
      )}
      <div className="space-y-2">
        {d.rows.map((o: Any) => (
          <button
            key={o.id}
            onClick={() => setOpen(o)}
            className="w-full text-left bg-white border border-slate-200 rounded-xl p-3.5 hover:border-brand-400 transition"
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-slate-900">
                {o.user}
              </span>
              {o.reason_label && (
                <span
                  className={`px-1.5 py-0.5 rounded text-[11px] ${
                    o.ours
                      ? "bg-red-100 text-red-700"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {o.reason_label}
                </span>
              )}
              <span className="ml-auto text-xs text-slate-500">
                {o.done_count}/{o.total_steps} band
                {o.completed ? " · yakunlandi" : ""}
              </span>
            </div>
          </button>
        ))}
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Ketish jarayoni yo'q — yaxshi belgi.
          </p>
        )}
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {open && (
        <OffboardModal
          row={open}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function OffboardModal({ row, onClose }: { row: Any; onClose: () => void }) {
  const [o, setO] = useState<Any>(row);
  const [err, setErr] = useState("");

  const toggle = async (step: string, done: boolean) => {
    setErr("");
    try {
      const r = await api.post<Any>(`/hr/offboarding/${o.id}/update`, {
        step,
        done,
      });
      setO(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-900">{o.user}</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          {o.reason_label || "sabab ko'rsatilmagan"}
          {o.last_day ? ` · oxirgi kun ${o.last_day}` : ""}
        </p>

        <div className="space-y-1 mb-3">
          {o.steps.map((s: Any) => (
            <label
              key={s.key}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-100 text-sm cursor-pointer"
            >
              <input
                type="checkbox"
                checked={s.done}
                disabled={o.completed}
                onChange={(e) => toggle(s.key, e.target.checked)}
              />
              <span
                className={s.done ? "text-slate-400 line-through" : "text-slate-700"}
              >
                {s.label}
              </span>
            </label>
          ))}
        </div>

        {o.completed && (
          <p className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg p-2">
            Jarayon yakunlandi — hisob o'chirildi.
          </p>
        )}
        {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
      </div>
    </div>
  );
}
