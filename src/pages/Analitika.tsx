import { useEffect, useState } from "react";
import { TrendingUp, Users, GraduationCap, PieChart as PieIcon } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import {
  api,
  type AnalyticsSummary,
  type LtvReport,
  type LtvDimension,
  type RetentionReport,
  type QualityReport,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, can } from "../lib/roles";
import { groupColor, MONTHS } from "../lib/expenses";
import { subjectLine } from "../lib/subjects";
import { formatSom, formatPeriodLabel } from "../lib/format";

type Tab = "biznes" | "sifat" | "xarajat" | "oquvchi" | "ustoz";

const TABS: { key: Tab; label: string }[] = [
  { key: "biznes", label: "Biznes ko'rsatkichlari" },
  { key: "sifat", label: "Ta'lim sifati" },
  { key: "xarajat", label: "Xarajatlar tahlili" },
  { key: "oquvchi", label: "O'quvchi qiymati (LTV)" },
  { key: "ustoz", label: "Ustozlar" },
];

function short(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (abs >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

function Stat({
  label,
  value,
  hint,
  tone = "slate",
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red" | "amber";
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const toneClass =
    tone === "green"
      ? "text-emerald-600"
      : tone === "red"
      ? "text-red-600"
      : tone === "amber"
      ? "text-amber-600"
      : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${toneClass}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Card({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {subtitle && <p className="text-xs text-slate-400 mb-3">{subtitle}</p>}
      <div className={subtitle ? "" : "mt-3"}>{children}</div>
    </div>
  );
}

function RangePicker({
  months,
  setMonths,
}: {
  months: number;
  setMonths: (n: number) => void;
}) {
  return (
    <div className="flex gap-1 mb-5">
      {[6, 12, 24].map((m) => (
        <button
          key={m}
          onClick={() => setMonths(m)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
            months === m
              ? "bg-brand-50 border-brand-400 text-brand-700"
              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
          }`}
        >
          {m} oy
        </button>
      ))}
    </div>
  );
}

// ------------------------------------------------- Biznes ko'rsatkichlari
function BusinessTab({ data }: { data: AnalyticsSummary }) {
  const t = data.totals;
  const chart = data.months.map((m) => ({
    name: formatPeriodLabel(m.period),
    Kirim: m.income,
    Chiqim: m.outflow,
    Foyda: m.profit,
    "Ustozlar %": m.teacher_share,
  }));

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="Jami kirim" value={formatSom(t.income)} tone="green" icon={TrendingUp} />
        <Stat label="Jami chiqim" value={formatSom(t.outflow)} />
        <Stat
          label="Sof foyda"
          value={formatSom(t.profit)}
          hint={`rentabellik ${t.margin}%`}
          tone={t.profit >= 0 ? "green" : "red"}
        />
        <Stat
          label="Ustozlarning ulushi"
          value={`${t.teacher_share}%`}
          hint={`${short(t.payroll)} ish haqi`}
          tone={t.teacher_share > 50 ? "red" : t.teacher_share > 40 ? "amber" : "slate"}
          icon={GraduationCap}
        />
      </div>

      <Card
        title="Kirim, chiqim va foyda"
        subtitle="Oylar bo'yicha o'sish yoki pasayish"
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis tickFormatter={short} tick={{ fontSize: 12, fill: "#64748b" }} />
            <Tooltip formatter={(v: number) => formatSom(v)} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="Kirim"
              stroke="#0d9488"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="Chiqim"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="Foyda"
              stroke="#38bdf8"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card
        title="Ustozlarning ulushi"
        subtitle="Kirimning necha foizi ustozlar ish haqiga ketyapti"
      >
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis
              tickFormatter={(v) => `${v}%`}
              tick={{ fontSize: 12, fill: "#64748b" }}
            />
            <Tooltip formatter={(v: number) => `${v}%`} />
            <Bar
              dataKey="Ustozlar %"
              fill="#f59e0b"
              radius={[4, 4, 0, 0]}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-slate-400 mt-3">
          Bu ko'rsatkich barqaror bo'lishi kerak. Keskin o'sib ketsa — dars
          narxi qolib ketgan yoki guruhlarda o'quvchi kamaygan degani.
        </p>
      </Card>
    </div>
  );
}

// -------------------------------------------------------- Xarajat tahlili
function ExpenseTab({ data }: { data: AnalyticsSummary }) {
  const groups = data.expense_groups;
  const cats = data.expense_categories;
  const total = groups.reduce((s, g) => s + g.amount, 0);

  const pie = groups.map((g) => ({
    name: g.label,
    value: g.amount,
    color: groupColor(g.key),
  }));

  if (total === 0) {
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        Bu davrda xarajat kiritilmagan. Moliya → Xarajatlar bo'limidan
        kiriting — shundan keyin tahlil shu yerda paydo bo'ladi.
      </p>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <p className="text-sm font-medium text-slate-700 mb-1">
            Xarajat guruhlari
          </p>
          <p className="text-xs text-slate-400 mb-3">
            Jami {formatSom(total)}
          </p>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pie}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                isAnimationActive={false}
              >
                {pie.map((p) => (
                  <Cell key={p.name} fill={p.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => formatSom(v)} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <p className="text-sm font-medium text-slate-700 mb-1">Ulushi</p>
          <p className="text-xs text-slate-400 mb-3">Katta yo'nalishlar</p>
          {groups.map((g) => {
            const pct = Math.round((g.amount / total) * 100);
            return (
              <div key={g.key} className="mb-3 last:mb-0">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="flex items-center gap-2 text-slate-700">
                    <span
                      className="w-2.5 h-2.5 rounded-sm inline-block"
                      style={{ background: groupColor(g.key) }}
                    />
                    {g.label}
                  </span>
                  <span className="text-slate-500">
                    <span className="font-medium text-slate-800">
                      {short(g.amount)}
                    </span>{" "}
                    · {pct}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${pct}%`, background: groupColor(g.key) }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <Card
        title="Har bir xarajat turi"
        subtitle="Eng kattadan kichigiga - kelasi yilga reja tuzishda asos bo'ladi"
      >
        <div className="overflow-hidden rounded-lg border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">Xarajat</th>
                <th className="text-left px-4 py-2.5 font-medium">Guruh</th>
                <th className="text-right px-4 py-2.5 font-medium">Summa</th>
                <th className="text-right px-4 py-2.5 font-medium">Ulushi</th>
                <th className="text-right px-4 py-2.5 font-medium">Oyiga o'rtacha</th>
              </tr>
            </thead>
            <tbody>
              {cats.map((c) => (
                <tr key={c.key} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">{c.label}</td>
                  <td className="px-4 py-2.5 text-slate-500">
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        className="w-2 h-2 rounded-sm inline-block"
                        style={{ background: groupColor(c.group) }}
                      />
                      {groups.find((g) => g.key === c.group)?.label || c.group}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-medium text-slate-800">
                    {formatSom(c.amount)}
                  </td>
                  <td className="px-4 py-2.5 text-right text-slate-500">
                    {Math.round((c.amount / total) * 100)}%
                  </td>
                  <td className="px-4 py-2.5 text-right text-slate-500">
                    {short(c.amount / data.months.length)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 mt-3">
          "Oyiga o'rtacha" ustuni kelasi yil byudjetini tuzishda ishlaydi:
          o'sha summani 12 ga ko'paytirsangiz, yillik reja chiqadi.
        </p>
      </Card>
    </div>
  );
}

// ------------------------------------------------------------------- LTV
const DIMENSIONS: { key: LtvDimension; label: string }[] = [
  { key: "branch", label: "Filiallar" },
  { key: "teacher", label: "Ustozlar" },
  { key: "group", label: "Guruhlar" },
];

function LtvTab() {
  const [dimension, setDimension] = useState<LtvDimension>("branch");
  const [data, setData] = useState<LtvReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<LtvReport>(`/reports/ltv?dimension=${dimension}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [dimension]);

  if (loading || !data) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  if (!data.overall)
    return <p className="text-sm text-slate-400 py-8 text-center">Hali ma'lumot yo'q.</p>;

  const chart = data.rows.slice(0, 12).map((r) => ({
    name: r.label.length > 14 ? r.label.slice(0, 13) + "…" : r.label,
    LTV: r.avg_revenue,
    "Oy": r.avg_months,
  }));

  return (
    <div>
      <div className="flex gap-1 mb-5">
        {DIMENSIONS.map((d) => (
          <button
            key={d.key}
            onClick={() => setDimension(d.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
              dimension === d.key
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="O'quvchilar" value={String(data.overall.students)} icon={Users} />
        <Stat
          label="O'rtacha qolish"
          value={`${data.overall.avg_months} oy`}
        />
        <Stat
          label="O'rtacha LTV"
          value={formatSom(data.overall.avg_revenue)}
          hint="bitta o'quvchidan tushgan pul"
          tone="green"
        />
        <Stat
          label="Ketganlar"
          value={String(data.overall.left)}
          hint={`jami ${data.overall.students} tadan`}
          tone={data.overall.left > 0 ? "red" : "slate"}
        />
      </div>

      <Card title="LTV taqqoslash" subtitle="Qaysi kesimda mijoz ko'proq pul olib keladi">
        <ResponsiveContainer width="100%" height={Math.max(240, chart.length * 34)}>
          <BarChart data={chart} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis type="number" tickFormatter={short} tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis
              type="category"
              dataKey="name"
              width={110}
              tick={{ fontSize: 12, fill: "#64748b" }}
            />
            <Tooltip formatter={(v: number) => formatSom(v)} />
            <Bar dataKey="LTV" fill="#0d9488" radius={[0, 4, 4, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">
                {DIMENSIONS.find((d) => d.key === dimension)?.label}
              </th>
              <th className="text-right px-4 py-3 font-medium">O'quvchi</th>
              <th className="text-right px-4 py-3 font-medium">O'rt. oy</th>
              <th className="text-right px-4 py-3 font-medium">O'rt. LTV</th>
              <th className="text-right px-4 py-3 font-medium">Jami</th>
              <th className="text-right px-4 py-3 font-medium">Ketish %</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={String(r.key)} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-800">{r.label}</td>
                <td className="px-4 py-3 text-right text-slate-600">{r.students}</td>
                <td className="px-4 py-3 text-right text-slate-600">{r.avg_months}</td>
                <td className="px-4 py-3 text-right font-medium text-slate-800">
                  {formatSom(r.avg_revenue)}
                </td>
                <td className="px-4 py-3 text-right text-slate-600">
                  {short(r.total_revenue)}
                </td>
                <td
                  className={`px-4 py-3 text-right ${
                    r.churn > 20 ? "text-red-600 font-medium" : "text-slate-500"
                  }`}
                >
                  {r.churn}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 mt-3 max-w-3xl">
        Ketgan sana o'quvchi "Arxiv" holatiga o'tkazilganda avtomatik qo'yiladi.
        Ustoz va guruh kesimida o'quvchi hozirgi guruhiga qarab bo'linadi.
      </p>
    </div>
  );
}

// ------------------------------------------------------------- Ustozlar
function TeacherTab({ data }: { data: AnalyticsSummary }) {
  const [ret, setRet] = useState<RetentionReport | null>(null);

  useEffect(() => {
    api.get<RetentionReport>("/reports/teacher-retention").then(setRet);
  }, []);

  if (!ret) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  const s = ret.summary;

  const tenure = ret.rows
    .slice(0, 15)
    .map((r) => ({ name: r.full_name, Oy: r.months, active: r.active }));

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="Hozir ishlayapti" value={String(s.active)} icon={GraduationCap} />
        <Stat label="O'rtacha staj" value={`${s.avg_tenure_active} oy`} hint="faol ustozlar" />
        <Stat
          label="Kadrlar almashuvi"
          value={`${s.turnover_12m}%`}
          hint="oxirgi 12 oy"
          tone={s.turnover_12m > 25 ? "red" : "slate"}
        />
        <Stat
          label="Ustozlarning ulushi"
          value={`${data.totals.teacher_share}%`}
          hint="kirimdan ish haqiga"
          tone={data.totals.teacher_share > 50 ? "red" : "slate"}
        />
      </div>

      {tenure.length > 0 && (
        <Card title="Ustozlar staji" subtitle="Kim qancha vaqtdan beri ishlayapti (oy)">
          <ResponsiveContainer width="100%" height={Math.max(240, tenure.length * 32)}>
            <BarChart data={tenure} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <Tooltip formatter={(v: number) => `${v} oy`} />
              <Bar dataKey="Oy" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                {tenure.map((t) => (
                  <Cell key={t.name} fill={t.active ? "#0d9488" : "#cbd5e1"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate-400 mt-3">
            Kulrang ustun — ishdan ketgan ustoz.
          </p>
        </Card>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Ustoz</th>
              <th className="text-left px-4 py-3 font-medium">Filial</th>
              <th className="text-left px-4 py-3 font-medium">Holat</th>
              <th className="text-right px-4 py-3 font-medium">Staj (oy)</th>
            </tr>
          </thead>
          <tbody>
            {ret.rows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  Ustozlar qo'shilmagan
                </td>
              </tr>
            )}
            {ret.rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-800">{r.full_name}</td>
                <td className="px-4 py-3 text-slate-500">{r.branch || "—"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                      r.active
                        ? "bg-green-50 text-green-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {r.active ? "Ishlayapti" : "Ketgan"}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-800">
                  {r.months}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ----------------------------------------------------------- Ta'lim sifati
function qualityTone(avg: number): string {
  if (avg >= 85) return "text-emerald-600";
  if (avg >= 70) return "text-teal-600";
  if (avg >= 55) return "text-amber-600";
  return "text-red-600";
}

function qualityBar(avg: number): string {
  if (avg >= 85) return "#10b981";
  if (avg >= 70) return "#14b8a6";
  if (avg >= 55) return "#f59e0b";
  return "#ef4444";
}

function QualityTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<QualityReport>(`/reports/quality?year=${year}&month=${month}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [year, month]);

  const years = [now.getFullYear() - 1, now.getFullYear()];

  return (
    <div>
      <div className="flex items-center gap-2 mb-5">
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>
              {m}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
        >
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : data.centre.avg === null ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Bu oyda imtihon o'tkazilmagan. Guruh sahifasidagi "Imtihonlar"
          bo'limidan test qo'shing va natijalarni kiriting — ta'lim sifati
          shundan avtomat hisoblanadi.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <div className="bg-white rounded-xl border-2 border-brand-200 p-4">
              <p className="text-xs text-slate-500 mb-1">O'quv markaz sifati</p>
              <p className={`text-2xl font-bold ${qualityTone(data.centre.avg)}`}>
                {data.centre.avg}%
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                {data.centre.groups} guruh · {data.centre.exams} imtihon
              </p>
            </div>
            <Stat
              label="Baholangan natijalar"
              value={String(data.centre.results)}
              hint="kelmaganlar hisobga olinmagan"
            />
            <Stat
              label="Eng yaxshi ustoz"
              value={data.teachers[0]?.name || "—"}
              hint={data.teachers[0] ? `${data.teachers[0].avg}%` : undefined}
              tone="green"
              icon={GraduationCap}
            />
            <Stat
              label="Eng past guruh"
              value={data.groups[data.groups.length - 1]?.group || "—"}
              hint={
                data.groups.length
                  ? `${data.groups[data.groups.length - 1].avg}%`
                  : undefined
              }
              tone="red"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
            <Card title="Filiallar" subtitle="Guruhlar o'rtachasi bo'yicha">
              {data.branches.length === 0 ? (
                <p className="text-sm text-slate-400">Ma'lumot yo'q</p>
              ) : (
                data.branches.map((b) => (
                  <div key={b.id} className="mb-3 last:mb-0">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-700">{b.name}</span>
                      <span className={`font-semibold ${qualityTone(b.avg)}`}>
                        {b.avg}%
                      </span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${b.avg}%`, background: qualityBar(b.avg) }}
                      />
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {b.groups} guruh · {b.exams} imtihon
                    </p>
                  </div>
                ))
              )}
            </Card>

            <Card title="Ustozlar" subtitle="O'z guruhlarining o'rtachasi">
              {data.teachers.length === 0 ? (
                <p className="text-sm text-slate-400">Ma'lumot yo'q</p>
              ) : (
                data.teachers.map((t) => (
                  <div key={t.id} className="mb-3 last:mb-0">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-700">{t.name}</span>
                      <span className={`font-semibold ${qualityTone(t.avg)}`}>
                        {t.avg}%
                      </span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${t.avg}%`, background: qualityBar(t.avg) }}
                      />
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {t.groups} guruh · {t.exams} imtihon
                    </p>
                  </div>
                ))
              )}
            </Card>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Guruh</th>
                  <th className="text-left px-4 py-3 font-medium">Kurs</th>
                  <th className="text-left px-4 py-3 font-medium">Ustoz</th>
                  <th className="text-left px-4 py-3 font-medium">Filial</th>
                  <th className="text-right px-4 py-3 font-medium">Imtihon</th>
                  <th className="text-right px-4 py-3 font-medium">Sifat</th>
                </tr>
              </thead>
              <tbody>
                {data.groups.map((g) => (
                  <tr key={g.group_id} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-medium text-slate-800">{g.group}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {subjectLine(g) || "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{g.teacher || "—"}</td>
                    <td className="px-4 py-3 text-slate-500">{g.branch || "—"}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{g.exams}</td>
                    <td
                      className={`px-4 py-3 text-right font-semibold ${qualityTone(g.avg)}`}
                    >
                      {g.avg}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-xs text-slate-400 mt-3 max-w-3xl">
            Sifat = shu oydagi imtihonlarda olingan o'rtacha foiz. Guruh →
            ustoz → filial → markaz tartibida yig'iladi. Guruhlar teng vaznda
            olinadi: bitta katta guruh butun ko'rsatkichni belgilab qo'ymaydi.
            Imtihonga kelmagan o'quvchi o'rtachani pasaytirmaydi.
          </p>
        </>
      )}
    </div>
  );
}

// -------------------------------------------------------------------- Page
export default function Analitika() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("biznes");
  const [months, setMonths] = useState(12);
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<AnalyticsSummary>(`/analytics/summary?months=${months}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [months]);

  if (!can(user?.role, FINANCE_ACCESS)) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl">
      <h1 className="text-xl font-semibold text-slate-900 mb-1 flex items-center gap-2">
        <PieIcon size={20} className="text-brand-600" /> Analitika
      </h1>
      <p className="text-sm text-slate-500 mb-5">
        Qaror qabul qilish uchun kerak bo'ladigan ko'rsatkichlar
      </p>

      <div className="flex gap-1 mb-6 border-b border-slate-200 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition whitespace-nowrap ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab !== "oquvchi" && tab !== "sifat" && (
        <RangePicker months={months} setMonths={setMonths} />
      )}

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <>
          {tab === "biznes" && <BusinessTab data={data} />}
          {tab === "sifat" && <QualityTab />}
          {tab === "xarajat" && <ExpenseTab data={data} />}
          {tab === "oquvchi" && <LtvTab />}
          {tab === "ustoz" && <TeacherTab data={data} />}
        </>
      )}
    </div>
  );
}
