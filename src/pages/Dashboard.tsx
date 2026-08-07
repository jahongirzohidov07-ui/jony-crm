import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users,
  Layers,
  Wallet,
  AlertTriangle,
  UserCheck,
  Download,
  Receipt,
  Briefcase,
  Percent,
  Play as Youtube,
  Camera as Instagram,
  Send,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import {
  api,
  type DashboardStats,
  type TrendPoint,
  type Group,
  type StudentGrowthWindow,
  type StudentGrowthResponse,
  type SocialStats,
  type CollectionReport,
} from "../lib/api";
import { formatSom, formatPeriodLabel, formatGrowthLabel } from "../lib/format";
import {
  CASH_ACCESS, DEBTOR_ACCESS, PROFIT_VIEW, SALES_MANAGER, ADMINISTRATOR, can,
} from "../lib/roles";
import { SalesPanelCards, AdminCollectionCard } from "../components/SalesPanel";
import { MyPanel } from "../components/MyPanel";
import { FillCard } from "../components/FillReport";
import { useAuth } from "../lib/AuthContext";
import Plan from "./Plan";
import { PLAN_VIEW } from "../lib/roles";
import Ceo from "./Ceo";
import { exportSheetsToExcel } from "../lib/exportXlsx";

const BRAND = "#0d9488";
const BRAND_LIGHT = "#5eead4";
const AMBER = "#d97706";
const SLATE = "#94a3b8";

function KpiCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "default",
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "danger" | "brand";
}) {
  const toneClasses =
    tone === "danger"
      ? "bg-red-50 text-red-600"
      : tone === "brand"
      ? "bg-brand-50 text-brand-600"
      : "bg-slate-100 text-slate-600";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${toneClasses}`}>
          <Icon size={18} />
        </div>
        <span className="text-sm text-slate-500">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
    </div>
  );
}

/** Instagram / Telegram obunachilar - Marketing bo'limidan olinadi. */
function SocialCards() {
  const [data, setData] = useState<SocialStats | null>(null);

  useEffect(() => {
    api.get<SocialStats>("/social").then(setData).catch(() => setData(null));
  }, []);

  if (!data) return null;
  const items = Object.values(data).filter((p) => p.followers !== null);
  if (items.length === 0) return null;

  const icons: Record<string, React.ElementType> = {
    instagram: Instagram,
    telegram: Send,
    youtube: Youtube,
  };

  return (
    <>
      {items.map((p) => (
        <KpiCard
          key={p.platform}
          icon={icons[p.platform] || Users}
          label={`${p.label} obunachilar`}
          value={(p.followers as number).toLocaleString("uz-UZ")}
          hint={
            p.growth && p.growth !== 0
              ? `${p.growth > 0 ? "+" : ""}${p.growth} oxirgi davrda`
              : p.date
                ? `${p.date} holatiga`
                : undefined
          }
        />
      ))}
    </>
  );
}

function ChartCard({
  title,
  children,
  actions,
}: {
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="font-semibold text-slate-900 text-sm">{title}</h2>
        {actions}
      </div>
      <div className="h-64">{children}</div>
    </div>
  );
}

function tooltipFormatter(value: number) {
  return formatSom(value);
}

const GROWTH_WINDOWS: { key: StudentGrowthWindow; label: string }[] = [
  { key: "all", label: "Barcha vaqt" },
  { key: "1y", label: "1 yillik" },
  { key: "6m", label: "6 oylik" },
  { key: "1m", label: "1 oylik" },
];

function WindowTabs({
  value,
  onChange,
}: {
  value: StudentGrowthWindow;
  onChange: (w: StudentGrowthWindow) => void;
}) {
  return (
    <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
      {GROWTH_WINDOWS.map((w) => (
        <button
          key={w.key}
          onClick={() => onChange(w.key)}
          className={`px-2.5 py-1 rounded-md text-xs font-medium transition ${
            value === w.key
              ? "bg-white text-brand-700 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          {w.label}
        </button>
      ))}
    </div>
  );
}

/** Shu oyning to'lov yig'ish foizi — administratorlar uchun eng muhim
 *  raqam, shuning uchun Dashboard'da eng tepada va eng katta turadi.
 *
 *  Muhim nuqta: ortiqcha to'lov foizni oshirmaydi. Bir o'quvchi ikki
 *  oylik to'lasa, ortig'i keyingi oyga o'tadi va to'lamagan o'quvchi
 *  baribir ko'rinib turadi. */
function CollectionCard() {
  const [data, setData] = useState<CollectionReport | null>(null);
  const [open, setOpen] = useState(false);
  const now = new Date();

  useEffect(() => {
    api
      .get<CollectionReport>(
        `/billing/collection?year=${now.getFullYear()}&month=${now.getMonth() + 1}`
      )
      .then(setData)
      .catch(() => setData(null));
  }, []);

  if (!data || data.charged === 0) return null;

  const pct = data.percent;
  const tone =
    pct >= 95 ? "text-emerald-600"
      : pct >= 80 ? "text-amber-600"
        : "text-red-600";
  const bar =
    pct >= 95 ? "bg-emerald-500"
      : pct >= 80 ? "bg-amber-500"
        : "bg-red-500";
  const ring =
    pct >= 95 ? "#10b981" : pct >= 80 ? "#f59e0b" : "#ef4444";

  const owing = data.rows.filter((r) => r.state !== "paid");

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* Katta doira - eng ko'zga tashlanadigan raqam */}
        <div className="relative w-32 h-32 shrink-0">
          <svg viewBox="0 0 120 120" className="w-32 h-32 -rotate-90">
            <circle
              cx="60" cy="60" r="52" fill="none"
              stroke="#f1f5f9" strokeWidth="14"
            />
            <circle
              cx="60" cy="60" r="52" fill="none"
              stroke={ring} strokeWidth="14" strokeLinecap="round"
              strokeDasharray={`${Math.min(100, pct) * 3.267} 1000`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-semibold ${tone}`}>{pct}%</span>
            <span className="text-xs text-slate-400">yig'ildi</span>
          </div>
        </div>

        <div className="flex-1 w-full">
          <div className="flex items-center gap-2 mb-1">
            <Percent size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              Shu oy to'lovlarni yig'ish
            </p>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            {data.students} ta o'quvchidan {data.paid_students} tasi to'liq
            to'ladi
            {data.unpaid_students > 0 &&
              `, ${data.unpaid_students} tasi umuman to'lamadi`}
          </p>

          <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden mb-3">
            <div
              className={`h-full rounded-full ${bar}`}
              style={{ width: `${Math.min(100, pct)}%` }}
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-xs text-slate-500">Hisoblangan</p>
              <p className="text-slate-900 font-medium">
                {formatSom(data.charged)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Yig'ilgan</p>
              <p className="text-emerald-600 font-medium">
                {formatSom(data.collected)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Qolgan qarz</p>
              <p className="text-red-600 font-medium">{formatSom(data.debt)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Keyingi oyga</p>
              <p className="text-sky-600 font-medium">
                {formatSom(data.carry_out)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {owing.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <button
            onClick={() => setOpen(!open)}
            className="text-sm text-slate-700 hover:text-brand-700"
          >
            {owing.length} ta o'quvchi to'lovni yopmadi{" "}
            <span className="text-slate-400">{open ? "▾" : "▸"}</span>
          </button>
          {open && (
            <table className="w-full text-sm mt-2">
              <tbody>
                {owing.slice(0, 20).map((r) => (
                  <tr key={r.student_id} className="border-b border-slate-50">
                    <td className="py-1.5">
                      <Link
                        to={`/students/${r.student_id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {r.full_name}
                      </Link>
                      <span className="block text-xs text-slate-400">
                        {r.group}
                      </span>
                    </td>
                    <td className="text-right text-red-600 font-medium">
                      {formatSom(r.left)}
                    </td>
                    <td className="text-right w-16 text-xs text-slate-400">
                      {r.percent}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {data.by_admin.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <p className="text-xs text-slate-500 mb-1.5">Kassaga kim yig'di</p>
          <div className="flex flex-wrap gap-x-5 gap-y-1">
            {data.by_admin.map((a) => (
              <span key={a.name} className="text-sm text-slate-700">
                {a.name}{" "}
                <span className="text-slate-500">{formatSom(a.collected)}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

type DashTab = "overview" | "today" | "plan";

export default function Dashboard() {
  const { user } = useAuth();
  // Administratorning ekrani boshqacha: unga daromad grafigi va
  // obunachilar soni emas, BUGUN nima qilish kerakligi kerak.
  const isSales =
    user?.role === SALES_MANAGER || user?.role === ADMINISTRATOR;
  // Butun markaz bo'yicha kartalar — Examiner, HR va SMM'ga kerak
  // emas: ular faqat o'z ishini ko'radi.
  const [showGeneral, setShowGeneral] = useState(true);
  const [tab, setTab] = useState<DashTab>("overview");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [growthWindow, setGrowthWindow] = useState<StudentGrowthWindow>("6m");
  const [growth, setGrowth] = useState<StudentGrowthResponse | null>(null);
  const [growthLoading, setGrowthLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<DashboardStats>("/dashboard"),
      api.get<TrendPoint[]>("/dashboard/trend?months=6"),
      api.get<Group[]>("/groups"),
    ])
      .then(([s, t, g]) => {
        setStats(s);
        setTrend(t);
        setGroups(g);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setGrowthLoading(true);
    api
      .get<StudentGrowthResponse>(`/dashboard/student-growth?window=${growthWindow}`)
      .then(setGrowth)
      .finally(() => setGrowthLoading(false));
  }, [growthWindow]);

  const statusBreakdown = stats
    ? [
        { name: "Faol", value: stats.active_students, fill: BRAND },
        { name: "Sinovda", value: stats.trial_students, fill: AMBER },
        { name: "Muzlatilgan", value: stats.frozen_students, fill: SLATE },
      ]
    : [];

  const topGroups = [...groups]
    .sort((a, b) => b.student_count - a.student_count)
    .slice(0, 8)
    .map((g) => ({ name: g.name, talabalar: g.student_count }));

  function downloadReport() {
    if (!stats) return;
    exportSheetsToExcel(`Jony-CRM-hisobot-${new Date().toISOString().slice(0, 10)}`, [
      {
        name: "Umumiy",
        rows: [
          { "Ko'rsatkich": "Faol talabalar", Qiymat: stats.active_students },
          { "Ko'rsatkich": "Sinovdagi talabalar", Qiymat: stats.trial_students },
          { "Ko'rsatkich": "Muzlatilgan talabalar", Qiymat: stats.frozen_students },
          { "Ko'rsatkich": "Guruhlar soni", Qiymat: stats.total_groups },
          { "Ko'rsatkich": "Shu oy yangi to'lovlar", Qiymat: stats.month_new_payment_count },
          { "Ko'rsatkich": "Shu oy jami to'lovlar", Qiymat: stats.month_payment_count },
          { "Ko'rsatkich": "Xodimlar soni", Qiymat: stats.staff_count },
          { "Ko'rsatkich": "Shu oy tushum (so'm)", Qiymat: Math.round(stats.month_income) },
          { "Ko'rsatkich": "Umumiy qarzdorlik (so'm)", Qiymat: Math.round(stats.total_debt) },
          { "Ko'rsatkich": "Qarzdorlar soni", Qiymat: stats.debtor_count },
        ],
      },
      {
        name: "Oylik daromad",
        rows: trend.map((t) => ({
          Davr: t.period,
          Oy: formatPeriodLabel(t.period),
          "Daromad (so'm)": Math.round(t.income),
        })),
      },
      {
        name: "Guruhlar",
        rows: groups.map((g) => ({
          Guruh: g.name,
          Filial: g.branch?.name || "—",
          "O'qituvchi": g.teacher?.full_name || "—",
          "Talabalar soni": g.student_count,
          "Oylik to'lov (so'm)": Math.round(g.monthly_fee),
        })),
      },
    ]);
  }

  const showToday = can(user?.role, PROFIT_VIEW);
  const showPlan = can(user?.role, PLAN_VIEW);

  if (showPlan && tab === "plan") {
    return (
      <div className="p-8">
        <DashTabs tab={tab} setTab={setTab} showToday={showToday}
                  showPlan={showPlan} />
        <Plan />
      </div>
    );
  }

  if (showToday && tab === "today") {
    return (
      <div className="p-8 max-w-6xl">
        <DashTabs tab={tab} setTab={setTab} showToday={showToday}
                  showPlan={showPlan} />
        <Ceo />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl">
      <DashTabs tab={tab} setTab={setTab} showToday={showToday}
                showPlan={showPlan} />
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 mb-1">Dashboard</h1>
          <p className="text-sm text-slate-500">"Maktab" filiali bo'yicha umumiy holat</p>
        </div>
        {stats && (
          <button
            onClick={downloadReport}
            className="flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg px-4 py-2 text-sm font-medium"
          >
            <Download size={16} />
            Hisobotni yuklab olish
          </button>
        )}
      </div>

      {loading && <p className="text-slate-400 text-sm">Yuklanmoqda...</p>}
      {err && <p className="text-red-600 text-sm">{err}</p>}

      {/* Har bir xodim avval O'Z ishini ko'radi */}
      <MyPanel onLoaded={setShowGeneral} />

      {stats && showGeneral && (
        <>
          {can(user?.role, CASH_ACCESS) && <CollectionCard />}
          {/* Administratorning bonusi eski to'lov yig'imidan chiqadi —
              shuning uchun u xonalar bandligidan ham tepada turadi. */}
          {isSales && <AdminCollectionCard />}
          <FillCard />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <KpiCard icon={UserCheck} label="Faol talabalar" value={String(stats.active_students)} tone="brand" />
            <KpiCard icon={Users} label="Sinovdagi talabalar" value={String(stats.trial_students)} />
            <KpiCard icon={Users} label="Muzlatilgan talabalar" value={String(stats.frozen_students)} />
            {/* Guruh va xodim soni administratorning ishiga aloqasiz —
                unga o'quvchi, to'lov va qarzdorlik kerak. */}
            {!isSales && (
              <KpiCard icon={Layers} label="Guruhlar soni" value={String(stats.total_groups)} />
            )}
            <KpiCard
              icon={Receipt}
              label="Shu oy yangi to'lovlar"
              value={String(stats.month_new_payment_count)}
              hint={`jami ${stats.month_payment_count} ta to'lov`}
              tone="brand"
            />
            {!isSales && (
              <KpiCard icon={Briefcase} label="Xodimlar soni" value={String(stats.staff_count)} />
            )}
            <KpiCard icon={Wallet} label="Shu oy tushum" value={formatSom(stats.month_income)} tone="brand" />
            <KpiCard
              icon={AlertTriangle}
              label="Umumiy qarzdorlik"
              value={formatSom(stats.total_debt)}
              tone="danger"
            />
            {can(user?.role, DEBTOR_ACCESS) ? (
              <Link to="/finance" className="block">
                <KpiCard
                  icon={AlertTriangle}
                  label="Qarzdorlar soni"
                  value={String(stats.debtor_count)}
                  hint="ro'yxatni ochish uchun bosing"
                  tone="danger"
                />
              </Link>
            ) : (
              <KpiCard icon={AlertTriangle} label="Qarzdorlar soni" value={String(stats.debtor_count)} tone="danger" />
            )}
            {!isSales && <SocialCards />}
          </div>

          <ChartCard
            title="Talabalar soni statistikasi"
            actions={<WindowTabs value={growthWindow} onChange={setGrowthWindow} />}
          >
            {growthLoading ? (
              <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
            ) : !growth || growth.points.length === 0 ? (
              <p className="text-slate-400 text-sm">Ma'lumot yo'q</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={growth.points} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="period"
                    tickFormatter={(p: string) => formatGrowthLabel(p, growth.granularity)}
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    interval={growth.granularity === "day" ? 3 : 0}
                  />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} width={32} />
                  <Tooltip
                    labelFormatter={(p) => formatGrowthLabel(String(p), growth.granularity)}
                    contentStyle={{ fontSize: 13, borderRadius: 8 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    name="Talabalar soni"
                    stroke={BRAND}
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: BRAND }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          {/* Administratorga daromad grafigi emas, to'ldirilishi kerak
              bo'lgan guruhlar va shu oy ketganlar kerak. */}
          {isSales && <SalesPanelCards />}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4 mt-4">
            {!isSales && (
            <ChartCard title="Oylik daromad trendi (so'nggi 6 oy)">
              {trend.length === 0 ? (
                <p className="text-slate-400 text-sm">Ma'lumot yo'q</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      dataKey="period"
                      tickFormatter={formatPeriodLabel}
                      tick={{ fontSize: 12, fill: "#64748b" }}
                    />
                    <YAxis
                      tickFormatter={(v) => `${Math.round(v / 1000)}k`}
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      width={44}
                    />
                    <Tooltip
                      formatter={tooltipFormatter}
                      labelFormatter={formatPeriodLabel}
                      contentStyle={{ fontSize: 13, borderRadius: 8 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="income"
                      name="Daromad"
                      stroke={BRAND}
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: BRAND }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
            )}

            <ChartCard title="Talabalar holati bo'yicha taqsimot">
              {statusBreakdown.every((s) => s.value === 0) ? (
                <p className="text-slate-400 text-sm">Ma'lumot yo'q</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusBreakdown} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} width={32} />
                    <Tooltip contentStyle={{ fontSize: 13, borderRadius: 8 }} />
                    <Bar dataKey="value" name="Talabalar" radius={[6, 6, 0, 0]}>
                      {statusBreakdown.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>

          <ChartCard title="Guruhlar bo'yicha talabalar soni (top 8)">
            {topGroups.length === 0 ? (
              <p className="text-slate-400 text-sm">Hali guruh yo'q</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={topGroups}
                  layout="vertical"
                  margin={{ top: 8, right: 24, left: 8, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={140}
                    tick={{ fontSize: 12, fill: "#64748b" }}
                  />
                  <Tooltip contentStyle={{ fontSize: 13, borderRadius: 8 }} />
                  <Bar dataKey="talabalar" name="Talabalar" fill={BRAND_LIGHT} radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </>
      )}
    </div>
  );
}


/** Dashboard ichidagi bo'limlar. "Bugungi holat" alohida sahifa emas,
 *  shu yerning ichida turadi. */
function DashTabs({
  tab, setTab, showToday, showPlan,
}: {
  tab: DashTab;
  setTab: (t: DashTab) => void;
  showToday: boolean;
  showPlan?: boolean;
}) {
  if (!showToday && !showPlan) return null;
  const items: { key: DashTab; label: string }[] = [
    { key: "overview", label: "Umumiy" },
    ...(showToday ? [{ key: "today" as DashTab, label: "Bugungi holat" }] : []),
    ...(showPlan ? [{ key: "plan" as DashTab, label: "Reja va Fakt" }] : []),
  ];
  return (
    <div className="flex gap-1 border-b border-slate-200 mb-6">
      {items.map((t) => (
        <button
          key={t.key}
          onClick={() => setTab(t.key)}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition ${
            tab === t.key
              ? "border-brand-600 text-brand-700"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
