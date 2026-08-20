import { useEffect, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Users, Wallet, AlertCircle } from "lucide-react";
import { api } from "../lib/api";
import { formatSom } from "../lib/format";

/**
 * BI PANEL (2026-08-20, Jahongir: "analitik bo'limini eng zor BI
 * texnologiyalari bilan qaror qilishga oson statistikalarini
 * chiroyli pie chart, line graph yoki boshqa chiroyli shartlar
 * bilan korsatadigan qil. eng zor statistikalar qosh").
 *
 * Bitta so'rov (/analytics/bi) - o'nlab emas. Har grafik bitta
 * savolga javob beradi: pul qayoqqa ketyapti, o'quvchi qayerdan
 * kelib qayerga ketyapti, qaysi filial tortyapti.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Bi = any;

const COLORS = ["#1A6EE4", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444",
  "#14B8A6", "#F97316", "#6366F1"];

const OY: Record<string, string> = {
  "01": "Yan", "02": "Fev", "03": "Mar", "04": "Apr", "05": "May",
  "06": "Iyn", "07": "Iyl", "08": "Avg", "09": "Sen", "10": "Okt",
  "11": "Noy", "12": "Dek",
};
const mLbl = (m: string) => `${OY[m.slice(5)] || m.slice(5)} ${m.slice(2, 4)}`;

function short(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (abs >= 1_000) return `${Math.round(n / 1_000)}k`;
  return String(Math.round(n));
}

function Kpi({ label, value, hint, tone = "slate", icon: Icon }: {
  label: string; value: string; hint?: string;
  tone?: "slate" | "green" | "red" | "amber"; icon?: any;
}) {
  const cls = tone === "green" ? "text-emerald-600"
    : tone === "red" ? "text-red-600"
    : tone === "amber" ? "text-amber-600" : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-1.5 mb-1">
        {Icon && <Icon size={13} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-bold ${cls}`}>{value}</p>
      {hint && <p className="text-[11px] text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Card({ title, hint, children }: {
  title: string; hint?: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="font-semibold text-slate-900 text-sm">{title}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5 mb-3">{hint}</p>}
      {!hint && <div className="h-3" />}
      {children}
    </div>
  );
}

export function BiPanel() {
  const [d, setD] = useState<Bi | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get<Bi>("/analytics/bi").then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (err) return <p className="text-sm text-red-600">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  const k = d.kpi;
  const rev = d.revenue_by_month.map((r: any) => ({ ...r, oy: mLbl(r.month) }));
  const trend = d.students_trend.map((r: any) => ({ ...r, oy: mLbl(r.month) }));
  const flow = d.flow_by_month.map((r: any) => ({ ...r, oy: mLbl(r.month) }));

  return (
    <div className="space-y-4">
      {/* ------------------------------------------------ KPI qatori */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi label="Faol o'quvchilar" value={String(k.active)}
             hint={`+${k.new_this} kelgan · −${k.left_this} ketgan (shu oy)`}
             icon={Users} />
        <Kpi label="Shu oy tushum" value={formatSom(k.rev_this)}
             hint={k.rev_mom != null
               ? `o'tgan oyga nisbatan ${k.rev_mom > 0 ? "+" : ""}${k.rev_mom}%`
               : undefined}
             tone={k.rev_mom != null && k.rev_mom < 0 ? "red" : "green"}
             icon={k.rev_mom != null && k.rev_mom < 0 ? TrendingDown : TrendingUp} />
        <Kpi label="Shu oy foyda" value={formatSom(k.profit_this)}
             tone={k.profit_this >= 0 ? "green" : "red"} icon={Wallet} />
        <Kpi label="Qarzdorlik" value={formatSom(k.debt_total)}
             hint={`${k.debtors} o'quvchida`} tone="amber" icon={AlertCircle} />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi label="Yig'ilish darajasi"
             value={k.collection != null ? `${k.collection}%` : "—"}
             hint="tushum / hisoblangan haq" />
        <Kpi label="O'rtacha chek" value={formatSom(k.avg_check)}
             hint="bitta to'lovning o'rtachasi" />
        <Kpi label="Lid konversiyasi (90 kun)"
             value={k.lead_conv != null ? `${k.lead_conv}%` : "—"}
             hint={`${k.lead_won_90d} / ${k.lead_total_90d} lid`} />
        <Kpi label="Ketish (churn)" value={`${k.churn}%`}
             hint="shu oy ketganlar / faollar"
             tone={k.churn > 5 ? "red" : "slate"} />
      </div>

      {/* ------------------------------------- tushum-xarajat-foyda */}
      <Card title="Pul oqimi — 12 oy"
            hint="Tushum, xarajat (ustoz oyligi bilan) va foyda">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={rev}>
            <defs>
              <linearGradient id="gRev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1A6EE4" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#1A6EE4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
            <XAxis dataKey="oy" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={short} tick={{ fontSize: 11 }} width={52} />
            <Tooltip formatter={(v: any) => formatSom(Number(v))} />
            <Legend />
            <Area type="monotone" dataKey="tushum" stroke="#1A6EE4"
                  fill="url(#gRev)" strokeWidth={2.5} name="Tushum" />
            <Line type="monotone" dataKey="xarajat" stroke="#EF4444"
                  strokeWidth={2} dot={false} name="Xarajat" />
            <Line type="monotone" dataKey="foyda" stroke="#10B981"
                  strokeWidth={2} dot={false} name="Foyda" />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* ------------------------------------ o'quvchilar trendi */}
        <Card title="O'quvchilar soni — 12 oy"
              hint="Faol + muzlatilganlar (oy oxiridagi holat)">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
              <XAxis dataKey="oy" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} width={36} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#1A6EE4"
                    strokeWidth={2.5} name="O'quvchi" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* ------------------------------------------ kelgan/ketgan */}
        <Card title="Kelgan va ketganlar — 12 oy"
              hint="Ketganlar ko'payishi — signal">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={flow}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
              <XAxis dataKey="oy" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} width={30} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="kelgan" fill="#10B981" name="Kelgan"
                   radius={[4, 4, 0, 0]} />
              <Bar dataKey="ketgan" fill="#EF4444" name="Ketgan"
                   radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* ------------------------------------------- filial pie */}
        <Card title="Shu oy tushumi — filiallar"
              hint="Qaysi filial nechani tortyapti">
          {d.branch_revenue.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              Bu oyda hali to'lov yo'q
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={d.branch_revenue} dataKey="value" nameKey="name"
                     innerRadius={55} outerRadius={90} paddingAngle={3}>
                  {d.branch_revenue.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any) => formatSom(Number(v))} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* ------------------------------------------ to'lov usuli */}
        <Card title="To'lov usullari — shu oy"
              hint="Naqd, Click, terminal ulushi">
          {d.method_split.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              Bu oyda hali to'lov yo'q
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={d.method_split} dataKey="value" nameKey="name"
                     innerRadius={55} outerRadius={90} paddingAngle={3}>
                  {d.method_split.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[(i + 1) % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any) => formatSom(Number(v))} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* --------------------------------------------- qarz bar */}
        <Card title="Qarzdorlik — filiallar" hint="Kimni birinchi siqish kerak">
          {d.debt_by_branch.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              Qarzdorlik yo'q 🎉
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={d.debt_by_branch} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
                <XAxis type="number" tickFormatter={short}
                       tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={92}
                       tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: any) => formatSom(Number(v))} />
                <Bar dataKey="value" fill="#F59E0B" name="Qarz"
                     radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* ---------------------------------------------- top guruh */}
        <Card title="TOP guruhlar — oylik tushum salohiyati"
              hint="Faol o'quvchi × guruh narxi">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={d.top_groups} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" />
              <XAxis type="number" tickFormatter={short}
                     tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={110}
                     tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: any, n: any) =>
                n === "revenue" ? formatSom(Number(v)) : v} />
              <Bar dataKey="revenue" fill="#1A6EE4" name="Tushum"
                   radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
