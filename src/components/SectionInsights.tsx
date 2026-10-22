import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
  CartesianGrid, Legend, PieChart, Pie,
} from "recharts";
import {
  Users, Layers, GraduationCap, CalendarDays, Clock, BookOpen, Package,
  AlertTriangle, CheckCircle2, Activity, Star, PartyPopper, UserCog,
  Briefcase, TrendingUp, Snowflake, UserPlus, Ban, History, Boxes,
  Headphones, Trophy, Target, BarChart3, ChevronDown,
} from "lucide-react";
import { api } from "../lib/api";

/* BO'LIM STATISTIKASI (2026-10-22, Jahongir: "dars jadvali, support
   jadvali, talabalar, guruhlar, o'qituvchilar, kutubxona, xodimlar,
   namunali xodim, audit, ombor, tadbirlar, shaxsiy rivojlanish" —
   "premium dizayn + grafiklar").

   Bitta komponent, bitta endpoint: /api/insights/{section} —
   { cards: [...], charts: [...] }. Har sahifa tepasiga
   <SectionInsights section="students" /> qo'yiladi. Faqat sanoq
   keladi; filial cheklovi serverda. Statistikani yig'ib qo'yish
   mumkin — tanlov shu brauzerda eslab qolinadi. */

type Card = {
  key: string; label: string; value: string | number; hint?: string;
  tone?: string; icon?: string;
};
type Row = { label: string; value: number; [k: string]: string | number };
type Chart = {
  key: string; title: string; sub?: string;
  type: "hbar" | "bar" | "donut" | "grouped";
  rows: Row[]; series?: { key: string; label: string; color?: string }[];
  span?: 1 | 2; unit?: string;
};
type Insights = { cards: Card[]; charts: Chart[] };

const PALETTE = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#f43f5e",
                 "#8b5cf6", "#14b8a6", "#f97316", "#06b6d4", "#84cc16",
                 "#ec4899", "#64748b"];

const TONES: Record<string, { grad: string; tint: string }> = {
  indigo: { grad: "from-indigo-500 to-blue-600", tint: "from-indigo-50" },
  violet: { grad: "from-violet-500 to-purple-600", tint: "from-violet-50" },
  sky: { grad: "from-sky-400 to-cyan-600", tint: "from-sky-50" },
  emerald: { grad: "from-emerald-400 to-teal-600", tint: "from-emerald-50" },
  amber: { grad: "from-amber-400 to-orange-500", tint: "from-amber-50" },
  rose: { grad: "from-rose-400 to-pink-600", tint: "from-rose-50" },
  slate: { grad: "from-slate-500 to-slate-700", tint: "from-slate-100" },
  fuchsia: { grad: "from-fuchsia-500 to-purple-600", tint: "from-fuchsia-50" },
  teal: { grad: "from-teal-400 to-cyan-700", tint: "from-teal-50" },
};
const TONE_ORDER = ["indigo", "violet", "sky", "emerald", "amber", "rose",
                    "teal", "fuchsia"];

const ICONS: Record<string, typeof Users> = {
  users: Users, layers: Layers, teacher: GraduationCap, calendar: CalendarDays,
  clock: Clock, book: BookOpen, package: Package, alert: AlertTriangle,
  check: CheckCircle2, activity: Activity, star: Star, party: PartyPopper,
  staff: UserCog, briefcase: Briefcase, trend: TrendingUp, frozen: Snowflake,
  new: UserPlus, ban: Ban, history: History, boxes: Boxes,
  support: Headphones, trophy: Trophy, target: Target,
};

const TIP = {
  contentStyle: {
    borderRadius: 12, border: "1px solid #e2e8f0",
    boxShadow: "0 10px 30px -12px rgba(15,23,42,.25)", fontSize: 12,
  },
  cursor: { fill: "rgba(99,102,241,0.06)" },
};

const SHADOW = "shadow-[0_1px_2px_rgba(15,23,42,0.04),0_8px_24px_-14px_rgba(15,23,42,0.18)]";

function Empty() {
  return <p className="text-sm text-slate-400 py-10 text-center">Hozircha ma'lumot yo'q</p>;
}

function ChartBody({ c }: { c: Chart }) {
  const rows = c.rows || [];
  if (!rows.length || (c.type !== "grouped" && rows.every((r) => !r.value)))
    return <Empty />;
  const fmt = (v: unknown) => [`${v}${c.unit || ""}`, "Soni"];

  if (c.type === "donut") {
    return (
      <>
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie data={rows} dataKey="value" nameKey="label" innerRadius={50}
                 outerRadius={78} paddingAngle={3} stroke="none">
              {rows.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
            </Pie>
            <Tooltip {...TIP} />
          </PieChart>
        </ResponsiveContainer>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-2">
          {rows.map((r, i) => (
            <span key={r.label} className="flex items-center gap-1.5 text-xs text-slate-600 min-w-0">
              <span className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: PALETTE[i % PALETTE.length] }} />
              <span className="truncate">{r.label}</span>
              <b className="ml-auto text-slate-900 tabular-nums">{r.value}</b>
            </span>
          ))}
        </div>
      </>
    );
  }

  if (c.type === "bar" || c.type === "grouped") {
    const series = c.type === "grouped"
      ? (c.series || [])
      : [{ key: "value", label: "Soni" }];
    return (
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={rows} margin={{ left: -18, right: 6, top: 8 }}>
          <CartesianGrid vertical={false} stroke="#eef2f7" />
          <XAxis dataKey="label" tickLine={false} axisLine={false}
                 tick={{ fontSize: 11, fill: "#64748b" }}
                 interval="preserveStartEnd" minTickGap={8} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false}
                 tick={{ fontSize: 11, fill: "#94a3b8" }} />
          <Tooltip {...TIP} />
          {c.type === "grouped" && <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />}
          {series.map((s, si) => (
            <Bar key={s.key} dataKey={s.key} name={s.label}
                 radius={[7, 7, 0, 0]} maxBarSize={c.type === "grouped" ? 18 : 30}
                 fill={s.color || PALETTE[si % PALETTE.length]}>
              {c.type === "bar" && rows.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  // hbar
  return (
    <ResponsiveContainer width="100%" height={Math.max(140, rows.length * 32 + 16)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 4, right: 30, top: 0, bottom: 0 }}>
        <XAxis type="number" hide allowDecimals={false} />
        <YAxis type="category" dataKey="label" width={150} tickLine={false}
               axisLine={false} tick={{ fontSize: 12, fill: "#475569" }} />
        <Tooltip {...TIP} formatter={fmt as never} />
        <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={17}
             label={{ position: "right", fontSize: 12, fill: "#0f172a", fontWeight: 600 }}>
          {rows.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SectionInsights({ section, params = "" }: {
  section: string; params?: string;
}) {
  const storeKey = `jony_insights_open_${section}`;
  const [open, setOpen] = useState<boolean>(() => {
    try { return localStorage.getItem(storeKey) !== "0"; } catch { return true; }
  });
  const [d, setD] = useState<Insights | null | false>(null);

  useEffect(() => {
    let alive = true;
    setD(null);
    api.get<Insights>(`/insights/${section}${params ? `?${params}` : ""}`)
      .then((x) => { if (alive) setD(x); })
      .catch(() => { if (alive) setD(false); });
    return () => { alive = false; };
  }, [section, params]);

  const toggle = () => {
    const v = !open;
    setOpen(v);
    try { localStorage.setItem(storeKey, v ? "1" : "0"); } catch { /* ignore */ }
  };

  if (d === false) return null;   // ruxsat yo'q yoki xato — sahifa ishlayveradi

  return (
    <section className="mb-6">
      <button onClick={toggle} data-no3d
        className="group flex items-center gap-2 mb-3 text-slate-500 hover:text-slate-800 transition">
        <span className="grid place-items-center w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-sm">
          <BarChart3 size={15} />
        </span>
        <span className="font-[family-name:var(--font-display)] text-[15px] font-extrabold text-slate-900">
          Statistika
        </span>
        <ChevronDown size={16} className={`transition-transform ${open ? "" : "-rotate-90"}`} />
        <span className="text-xs">{open ? "Yashirish" : "Ko'rsatish"}</span>
      </button>

      {open && (
        !d ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-[92px] rounded-2xl bg-slate-100 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {d.cards.length > 0 && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {d.cards.map((c, i) => {
                  const t = TONES[c.tone || TONE_ORDER[i % TONE_ORDER.length]] || TONES.indigo;
                  const Icon = ICONS[c.icon || ""] || Activity;
                  return (
                    <div key={c.key}
                      className={`relative overflow-hidden rounded-2xl border border-slate-200/80 bg-gradient-to-br ${t.tint} to-white p-4 ${SHADOW}`}>
                      <div className="flex items-start justify-between gap-2">
                        <p className="min-w-0 text-xs font-medium text-slate-500 leading-snug [overflow-wrap:anywhere] hyphens-auto" lang="uz">{c.label}</p>
                        <span className={`grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br ${t.grad} text-white shadow-md shrink-0`}>
                          <Icon size={17} />
                        </span>
                      </div>
                      <p className="font-[family-name:var(--font-display)] text-[28px] leading-tight font-extrabold text-slate-900 mt-1 tracking-tight tabular-nums">
                        {c.value}
                      </p>
                      {c.hint && <p className="text-[11px] text-slate-500 mt-0.5 truncate">{c.hint}</p>}
                    </div>
                  );
                })}
              </div>
            )}
            {d.charts.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {d.charts.map((c) => (
                  <div key={c.key}
                    className={`bg-white border border-slate-200/80 rounded-2xl p-5 ${SHADOW} ${
                      c.span === 2 ? "lg:col-span-2" : ""}`}>
                    <h3 className="text-[15px] font-bold text-slate-900">{c.title}</h3>
                    {c.sub && <p className="text-xs text-slate-500 mt-0.5">{c.sub}</p>}
                    <div className="mt-4"><ChartBody c={c} /></div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      )}
    </section>
  );
}
