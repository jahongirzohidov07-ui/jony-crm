import { useEffect, useState } from "react";
import {
  Megaphone, TrendingUp, Users, Target, RefreshCw, Camera as Instagram, Send,
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell,
} from "recharts";
import {
  api, type MarketingFunnel, type CacReport, type SocialStats,
  type MarketingJourney, type AdStat,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { MARKETING_ACCESS, FINANCE_ACCESS, can } from "../lib/roles";
import { formatSom, formatPeriodLabel } from "../lib/format";
import { MARKETING_CHANNELS } from "../lib/payments";
import { MONTHS } from "../lib/expenses";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "smm" | "journey" | "funnel" | "channels" | "romi" | "rfm"
  | "notify" | "referral" | "ads" | "social" | "salesplan";

import {
  RomiTab, RfmTab, NotifyTab, ReferralTab,
} from "../components/MarketingExtras";
import Smm from "./Smm";

const TABS: { key: Tab; label: string }[] = [
  { key: "journey", label: "To'liq yo'l" },
  { key: "funnel", label: "Lid voronkasi" },
  { key: "channels", label: "Kanallar va CAC" },
  { key: "romi", label: "ROMI" },
  { key: "rfm", label: "RFM segmentlar" },
  { key: "notify", label: "Xabarnomalar" },
  { key: "referral", label: "Referral" },
  { key: "ads", label: "Reklama ko'rsatkichlari" },
  { key: "social", label: "Ijtimoiy tarmoqlar" },
  { key: "salesplan", label: "Sotuv rejasi va bonus" },
];

const STAGE_COLORS = ["#94a3b8", "#38bdf8", "#818cf8", "#a78bfa", "#10b981"];

function short(n: number): string {
  const a = Math.abs(n);
  if (a >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (a >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

function Stat({
  label, value, hint, tone = "slate", icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red" | "amber";
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const cls =
    tone === "green" ? "text-emerald-600"
      : tone === "red" ? "text-red-600"
        : tone === "amber" ? "text-amber-600"
          : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${cls}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function RangePicker({
  months, setMonths,
}: {
  months: number;
  setMonths: (n: number) => void;
}) {
  return (
    <div className="flex gap-1 mb-5">
      {[
        { m: 1, l: "1 oy" },
        { m: 3, l: "3 oy" },
        { m: 6, l: "6 oy" },
        { m: 12, l: "1 yil" },
        { m: 0, l: "Butun davr" },
      ].map(({ m, l }) => (
        <button
          key={m}
          onClick={() => setMonths(m)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
            months === m
              ? "bg-brand-50 border-brand-400 text-brand-700"
              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

// -------------------------------------------------------- Voronka tab
function FunnelTab({ data }: { data: MarketingFunnel }) {
  const t = data.totals;
  const chart = data.stages.map((s, i) => ({
    name: s.label,
    Yetgan: s.reached,
    color: STAGE_COLORS[i] || "#cbd5e1",
  }));

  if (t.leads === 0) {
    return (
      <p className="text-sm text-slate-400 py-10 text-center">
        Bu davrda lid kiritilmagan. Lidlar bo'limidan qo'shing — voronka
        shundan keyin chiqadi.
      </p>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat label="Jami lid" value={String(t.leads)} icon={Users} />
        <Stat
          label="O'quvchiga aylandi"
          value={String(t.converted)}
          hint={`${t.conversion}% konversiya`}
          tone="green"
          icon={Target}
        />
        <Stat label="Reklama xarajati" value={formatSom(t.spend)} tone="red" />
        <Stat
          label="Bitta mijoz narxi (CAC)"
          value={t.cac ? formatSom(t.cac) : "—"}
          hint={t.cpl ? `bitta lid ${formatSom(t.cpl)}` : undefined}
          tone="amber"
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
        <p className="text-sm font-medium text-slate-700">Voronka bosqichlari</p>
        <p className="text-xs text-slate-400 mb-3">
          Odam qaysi bosqichda yo'qolyapti
        </p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chart} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis
              type="category"
              dataKey="name"
              width={130}
              tick={{ fontSize: 11, fill: "#64748b" }}
            />
            <Tooltip />
            <Bar dataKey="Yetgan" radius={[0, 4, 4, 0]} isAnimationActive={false}>
              {chart.map((c, i) => (
                <Cell key={i} fill={c.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <table className="w-full text-sm mt-4">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-100">
              <th className="text-left py-2">Bosqich</th>
              <th className="text-right">Yetgan</th>
              <th className="text-right">Shu yerda qolgan</th>
              <th className="text-right">Foiz</th>
            </tr>
          </thead>
          <tbody>
            {data.stages.map((s, i) => (
              <tr key={s.stage} className="border-b border-slate-50">
                <td className="py-2 flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ background: STAGE_COLORS[i] || "#cbd5e1" }}
                  />
                  {s.label}
                </td>
                <td className="text-right font-medium">{s.reached}</td>
                <td className="text-right text-slate-500">
                  {s.stuck_here || "—"}
                </td>
                <td className="text-right text-slate-500">{s.percent}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <p className="text-sm font-medium text-slate-700">Kanal bo'yicha lid</p>
        <p className="text-xs text-slate-400 mb-3">
          Qaysi kanal ko'proq odam olib kelyapti
        </p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data.channels.map((c) => ({
            name: c.label,
            Lid: c.leads,
            "O'quvchi": c.converted,
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} />
            <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Lid" fill="#38bdf8" radius={[4, 4, 0, 0]} isAnimationActive={false} />
            <Bar dataKey="O'quvchi" fill="#10b981" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ------------------------------------------------------- Kanallar tab
function ChannelsTab({
  data, cac,
}: {
  data: MarketingFunnel;
  cac: CacReport | null;
}) {
  const rows = data.channels;

  return (
    <div>
      {cac && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
          <Stat
            label="O'rtacha CAC"
            value={cac.totals.cac ? formatSom(cac.totals.cac) : "—"}
            hint="bitta yangi mijoz qancha turdi"
            tone="amber"
          />
          <Stat
            label="O'rtacha LTV"
            value={cac.totals.ltv ? formatSom(cac.totals.ltv) : "—"}
            hint="mijoz umri davomida to'lagani"
            tone="green"
          />
          <Stat
            label="LTV / CAC"
            value={cac.totals.ratio ? `${cac.totals.ratio}x` : "—"}
            hint={
              cac.totals.ratio >= 3
                ? "sog'lom — 3x dan yuqori"
                : cac.totals.ratio > 0
                  ? "past — 3x dan oshirish kerak"
                  : undefined
            }
            tone={cac.totals.ratio >= 3 ? "green" : cac.totals.ratio > 0 ? "red" : "slate"}
          />
          <Stat
            label="Yangi mijozlar"
            value={String(cac.totals.new_clients)}
            hint={`${formatSom(cac.totals.spend)} reklama`}
            icon={TrendingUp}
          />
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-sm font-medium text-slate-700">Kanallar taqqoslamasi</p>
            <p className="text-xs text-slate-400">
              CAC — bitta o'quvchi qancha turdi. ROI — sarflangan pulga nisbatan
              qaytgan daromad.
            </p>
          </div>
          <button
            onClick={() =>
              exportToExcel("marketing-kanallar", "Kanallar",
                rows.map((c) => ({
                  Kanal: c.label,
                  Xarajat: c.spend,
                  Lid: c.leads,
                  Sinovda: c.trial,
                  "O'quvchi": c.converted,
                  "Konversiya %": c.conversion,
                  CPL: c.cpl,
                  CAC: c.cac,
                  Daromad: c.revenue,
                  "ROI %": c.roi,
                })))
            }
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
          >
            Excel
          </button>
        </div>

        {rows.length === 0 ? (
          <p className="text-sm text-slate-400 py-6 text-center">
            Hali ma'lumot yo'q
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-500 border-b border-slate-100">
                  <th className="text-left py-2">Kanal</th>
                  <th className="text-right">Xarajat</th>
                  <th className="text-right">Lid</th>
                  <th className="text-right">O'quvchi</th>
                  <th className="text-right">Konv.</th>
                  <th className="text-right">CPL</th>
                  <th className="text-right">CAC</th>
                  <th className="text-right">Daromad</th>
                  <th className="text-right">ROI</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.channel} className="border-b border-slate-50">
                    <td className="py-2 font-medium text-slate-700">{c.label}</td>
                    <td className="text-right text-red-600">
                      {c.spend ? formatSom(c.spend) : "—"}
                    </td>
                    <td className="text-right">{c.leads}</td>
                    <td className="text-right text-emerald-600 font-medium">
                      {c.converted}
                    </td>
                    <td className="text-right text-slate-500">{c.conversion}%</td>
                    <td className="text-right text-slate-500">
                      {c.cpl ? formatSom(c.cpl) : "—"}
                    </td>
                    <td className="text-right font-medium text-amber-600">
                      {c.cac ? formatSom(c.cac) : "—"}
                    </td>
                    <td className="text-right text-emerald-600">
                      {c.revenue ? formatSom(c.revenue) : "—"}
                    </td>
                    <td
                      className={`text-right font-medium ${
                        c.spend === 0
                          ? "text-slate-400"
                          : c.roi >= 0
                            ? "text-emerald-600"
                            : "text-red-600"
                      }`}
                    >
                      {c.spend ? `${c.roi}%` : "—"}
                    </td>
                  </tr>
                ))}
                <tr className="border-t-2 border-slate-200 font-medium">
                  <td className="py-2">Jami</td>
                  <td className="text-right text-red-600">
                    {formatSom(data.totals.spend)}
                  </td>
                  <td className="text-right">{data.totals.leads}</td>
                  <td className="text-right text-emerald-600">
                    {data.totals.converted}
                  </td>
                  <td className="text-right">{data.totals.conversion}%</td>
                  <td className="text-right">
                    {data.totals.cpl ? formatSom(data.totals.cpl) : "—"}
                  </td>
                  <td className="text-right text-amber-600">
                    {data.totals.cac ? formatSom(data.totals.cac) : "—"}
                  </td>
                  <td className="text-right text-emerald-600">
                    {formatSom(data.totals.revenue)}
                  </td>
                  <td className="text-right">
                    {data.totals.spend ? `${data.totals.roi}%` : "—"}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
        <p className="text-xs text-slate-400 mt-3">
          Kanal bo'yicha xarajat Moliya → Xarajatlar bo'limida "Reklama"
          kategoriyasini tanlab, kanalni ko'rsatganda chiqadi.
        </p>
      </div>

      {cac && cac.rows.some((r) => r.spend > 0 || r.new_clients > 0) && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <p className="text-sm font-medium text-slate-700">CAC dinamikasi</p>
          <p className="text-xs text-slate-400 mb-3">
            Bitta mijozni jalb qilish oydan oyga qimmatlashyaptimi
          </p>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={cac.rows.map((r) => ({
              name: formatPeriodLabel(r.period),
              CAC: r.cac,
              "Yangi mijoz": r.new_clients,
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} />
              <YAxis yAxisId="l" tickFormatter={short} tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 12, fill: "#64748b" }} />
              <Tooltip
                formatter={(v: number, n: string) =>
                  n === "CAC" ? formatSom(v) : v
                }
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                yAxisId="l"
                type="monotone"
                dataKey="CAC"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                yAxisId="r"
                type="monotone"
                dataKey="Yangi mijoz"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// -------------------------------------------------------- Ijtimoiy tab
function SocialTab() {
  const [data, setData] = useState<SocialStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [manual, setManual] = useState<Record<string, string>>({});

  const load = () => {
    setLoading(true);
    api.get<SocialStats>("/social").then(setData).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const refresh = async () => {
    setBusy(true);
    setMsg("");
    try {
      const r = await api.post<{ instagram_note?: string | null }>(
        "/social/refresh", {}
      );
      setMsg(r.instagram_note || "Yangilandi");
      load();
    } catch {
      setMsg("Yangilab bo'lmadi");
    } finally {
      setBusy(false);
    }
  };

  const saveManual = async (platform: string) => {
    const v = Number(manual[platform]);
    if (!v || v < 0) return;
    await api.post("/social/manual", { platform, followers: v });
    setManual({ ...manual, [platform]: "" });
    load();
  };

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const icons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
    instagram: Instagram,
    telegram: Send,
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={refresh}
          disabled={busy}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          <RefreshCw size={14} className={busy ? "animate-spin" : ""} />
          Yangilash
        </button>
        {msg && <span className="text-xs text-slate-500">{msg}</span>}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {Object.values(data).map((p) => {
          const Icon = icons[p.platform];
          return (
            <div
              key={p.platform}
              className="bg-white rounded-xl border border-slate-200 p-5"
            >
              <div className="flex items-center gap-2 mb-3">
                {Icon && <Icon size={18} className="text-slate-400" />}
                <p className="font-medium text-slate-800">{p.label}</p>
                <span className="text-xs text-slate-400">@{p.handle}</span>
              </div>

              <p className="text-3xl font-semibold text-slate-900">
                {p.followers !== null ? p.followers.toLocaleString("uz-UZ") : "—"}
              </p>
              <div className="flex items-center gap-2 mt-1 text-xs">
                <span className="text-slate-400">obunachi</span>
                {p.growth !== null && p.growth !== 0 && (
                  <span
                    className={p.growth > 0 ? "text-emerald-600" : "text-red-600"}
                  >
                    {p.growth > 0 ? "+" : ""}
                    {p.growth} shu davrda
                  </span>
                )}
              </div>
              {p.date && (
                <p className="text-xs text-slate-400 mt-1">
                  {p.date} · {p.source === "auto" ? "avtomatik" : "qo'lda"}
                </p>
              )}

              {p.history.length > 1 && (
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={p.history}>
                    <XAxis dataKey="date" hide />
                    <YAxis hide domain={["dataMin", "dataMax"]} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="followers"
                      stroke="#0d9488"
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}

              <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100">
                <input
                  type="number"
                  value={manual[p.platform] ?? ""}
                  onChange={(e) =>
                    setManual({ ...manual, [p.platform]: e.target.value })
                  }
                  placeholder="Qo'lda kiritish"
                  className="flex-1 px-3 py-1.5 rounded-lg border border-slate-200 text-sm"
                />
                <button
                  onClick={() => saveManual(p.platform)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
                >
                  Saqlash
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-5">
        <p className="text-sm text-amber-900 font-medium mb-1">
          Avtomatik yangilanish haqida
        </p>
        <p className="text-xs text-amber-800 leading-relaxed">
          <b>Telegram</b> — kanal ochiq bo'lgani uchun obunachilar soni
          "Yangilash" tugmasida avtomat o'qiladi, hech narsa sozlash shart emas.
          <br />
          <b>Instagram</b> — Instagram raqamni faqat rasmiy API orqali beradi.
          Buning uchun akkaunt Business yoki Creator bo'lishi va Facebook
          sahifaga ulanishi kerak, keyin Vercel'ga <code>INSTAGRAM_TOKEN</code>{" "}
          va <code>INSTAGRAM_USER_ID</code> qo'shiladi. Token qo'shilmaguncha
          raqamni qo'lda kiritib turasiz.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------- To'liq yo'l tab
const JOURNEY_COLORS = [
  "#cbd5e1", "#94a3b8", "#38bdf8", "#60a5fa", "#818cf8",
  "#10b981", "#059669", "#047857", "#f59e0b",
];

function JourneyTab({ months }: { months: number }) {
  const [data, setData] = useState<MarketingJourney | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<MarketingJourney>(`/reports/marketing-journey?months=${months}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [months]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  // Eng keng bosqichga nisbatan kenglik - voronka shakli chiqishi uchun
  const max = Math.max(...data.stages.map((s) => s.count), 1);

  return (
    <div>
      {!data.has_ad_data && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5">
          <p className="text-sm text-amber-900 font-medium mb-1">
            Reklama ko'rsatkichlari kiritilmagan
          </p>
          <p className="text-xs text-amber-800">
            "Reklama ko'rildi" va "Bosildi" bosqichlari Instagram/Facebook
            reklama kabinetidan olinadi. "Reklama ko'rsatkichlari" bo'limidan
            oyiga bir marta kiriting — shundan keyin butun yo'l to'liq
            ko'rinadi.
          </p>
        </div>
      )}

      {data.worst_stage && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5">
          <p className="text-sm text-red-900 font-medium">
            Eng katta yo'qotish: {data.worst_stage.label}
          </p>
          <p className="text-xs text-red-800 mt-0.5">
            Bu bosqichda {data.worst_stage.lost} ta odam yo'qolyapti —
            oldingi bosqichdan atigi {data.worst_stage.step_percent}% o'tgan.
          </p>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
        <p className="text-sm font-medium text-slate-700">
          Reklamadan sertifikatgacha
        </p>
        <p className="text-xs text-slate-400 mb-4">
          Har bir bosqichda oldingisidan qanchasi o'tgani
        </p>
        <div className="space-y-2">
          {data.stages.map((st, i) => {
            const w = Math.max(2, (st.count / max) * 100);
            return (
              <div key={st.key} className="flex items-center gap-3">
                <div className="w-40 shrink-0 text-right">
                  <p className="text-sm text-slate-700">{st.label}</p>
                  {st.source === "ad" && (
                    <p className="text-[10px] text-slate-400">reklama kabineti</p>
                  )}
                </div>
                <div className="flex-1 flex items-center gap-2">
                  <div
                    className="h-8 rounded-md flex items-center px-2 min-w-[2%] transition-all"
                    style={{
                      width: `${w}%`,
                      background: JOURNEY_COLORS[i] || "#cbd5e1",
                    }}
                  >
                    <span className="text-xs font-medium text-white">
                      {st.count.toLocaleString("uz-UZ")}
                    </span>
                  </div>
                  {st.step_percent !== null && (
                    <span
                      className={`text-xs shrink-0 ${
                        st.step_percent < 30 ? "text-red-600" : "text-slate-500"
                      }`}
                    >
                      {st.step_percent}%
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <p className="text-sm font-medium text-slate-700 mb-3">
          Kanal bo'yicha to'liq yo'l
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-100">
                <th className="text-left py-2">Kanal</th>
                <th className="text-right">Ko'rildi</th>
                <th className="text-right">Bosildi</th>
                <th className="text-right">CTR</th>
                <th className="text-right">Lid</th>
                <th className="text-right">Sotildi</th>
                <th className="text-right">1 oy</th>
                <th className="text-right">3 oy</th>
                <th className="text-right">Sertifikat</th>
              </tr>
            </thead>
            <tbody>
              {data.channels.map((c) => (
                <tr key={c.channel} className="border-b border-slate-50">
                  <td className="py-2 font-medium text-slate-700">{c.label}</td>
                  <td className="text-right text-slate-500">
                    {c.impressions ? c.impressions.toLocaleString("uz-UZ") : "—"}
                  </td>
                  <td className="text-right text-slate-500">
                    {c.clicks ? c.clicks.toLocaleString("uz-UZ") : "—"}
                  </td>
                  <td className="text-right text-slate-500">
                    {c.ctr !== null ? `${c.ctr}%` : "—"}
                  </td>
                  <td className="text-right">{c.leads}</td>
                  <td className="text-right text-emerald-600 font-medium">
                    {c.sold}
                  </td>
                  <td className="text-right text-slate-600">
                    {c.month1}
                    {c.retention_1m !== null && (
                      <span className="text-xs text-slate-400">
                        {" "}
                        ({c.retention_1m}%)
                      </span>
                    )}
                  </td>
                  <td className="text-right text-slate-600">
                    {c.month3}
                    {c.retention_3m !== null && (
                      <span className="text-xs text-slate-400">
                        {" "}
                        ({c.retention_3m}%)
                      </span>
                    )}
                  </td>
                  <td className="text-right text-emerald-700">{c.certificate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 mt-3">
          "1 oy" va "3 oy" — birinchi to'lovdan keyin shuncha vaqt qolgan
          o'quvchilar. Bu raqam past bo'lsa muammo sotuvda emas, ta'lim
          sifatida.
        </p>
      </div>
    </div>
  );
}

// -------------------------------------------- Reklama ko'rsatkichlari
function AdsTab() {
  const now = new Date();
  const [rows, setRows] = useState<AdStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState("instagram");
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [impressions, setImpressions] = useState("");
  const [clicks, setClicks] = useState("");
  const [err, setErr] = useState("");

  function load() {
    setLoading(true);
    api.get<AdStat[]>("/ad-stats?months=12").then(setRows)
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function save() {
    setErr("");
    try {
      await api.post("/ad-stats", {
        channel,
        period: `${year}-${String(month).padStart(2, "0")}`,
        impressions: Number(impressions) || 0,
        clicks: Number(clicks) || 0,
      });
      setImpressions("");
      setClicks("");
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function remove(a: AdStat) {
    if (!confirm(`${a.label} · ${a.period} o'chirilsinmi?`)) return;
    await api.delete(`/ad-stats/${a.id}`);
    load();
  }

  const years = [now.getFullYear(), now.getFullYear() - 1];

  return (
    <div>
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
        <p className="text-sm font-medium text-slate-700">Ko'rsatkich kiritish</p>
        <p className="text-xs text-slate-400 mb-3">
          Instagram/Facebook reklama kabinetidagi raqamlarni oyiga bir marta
          kiriting — voronkaning birinchi ikki bosqichi shundan chiqadi.
        </p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="flex flex-wrap gap-2 items-end">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Kanal</label>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              {MARKETING_CHANNELS.map((c) => (
                <option key={c.key} value={c.key}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Oy</label>
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              {MONTHS.map((m, i) => (
                <option key={m} value={i + 1}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Yil</label>
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Ko'rildi (impressions)
            </label>
            <input
              type="number"
              value={impressions}
              onChange={(e) => setImpressions(e.target.value)}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm w-36"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Bosildi (clicks)
            </label>
            <input
              type="number"
              value={clicks}
              onChange={(e) => setClicks(e.target.value)}
              className="px-3 py-2 rounded-lg border border-slate-200 text-sm w-36"
            />
          </div>
          <button
            onClick={save}
            className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            Saqlash
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali ko'rsatkich kiritilmagan
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Davr</th>
                <th className="text-left">Kanal</th>
                <th className="text-right">Ko'rildi</th>
                <th className="text-right">Bosildi</th>
                <th className="text-right">CTR</th>
                <th className="w-12" />
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5">{formatPeriodLabel(a.period)}</td>
                  <td className="text-slate-600">{a.label}</td>
                  <td className="text-right tabular-nums">
                    {a.impressions.toLocaleString("uz-UZ")}
                  </td>
                  <td className="text-right tabular-nums">
                    {a.clicks.toLocaleString("uz-UZ")}
                  </td>
                  <td className="text-right text-slate-500">{a.ctr}%</td>
                  <td className="pr-3 text-right">
                    <button
                      onClick={() => remove(a)}
                      className="p-1.5 text-slate-400 hover:text-red-600"
                    >
                      ×
                    </button>
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

// ---------------------------------------------------------------- Sahifa
export default function Marketing() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>(
    "journey"
  );
  const [months, setMonths] = useState(6);
  const [data, setData] = useState<MarketingFunnel | null>(null);
  const [cac, setCac] = useState<CacReport | null>(null);
  const [loading, setLoading] = useState(true);

  const showCac = can(user?.role, FINANCE_ACCESS);

  useEffect(() => {
    if (tab === "social" || tab === "ads" || tab === "journey"
        || tab === "smm") return;
    setLoading(true);
    const jobs: Promise<unknown>[] = [
      api.get<MarketingFunnel>(`/reports/marketing-funnel?months=${months}`)
        .then(setData),
    ];
    if (showCac) {
      jobs.push(
        api.get<CacReport>(`/analytics/cac?months=${months}`)
          .then(setCac)
          .catch(() => setCac(null))
      );
    }
    Promise.all(jobs).finally(() => setLoading(false));
  }, [months, tab, showCac]);

  if (!can(user?.role, MARKETING_ACCESS)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Megaphone size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Marketing</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Voronka, kanallar samaradorligi va ijtimoiy tarmoqlar
      </p>

      <div className="flex gap-1 border-b border-slate-200 mb-5 overflow-x-auto">
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

      {tab !== "social" && tab !== "ads" && (
        <RangePicker months={months} setMonths={setMonths} />
      )}

      {tab === "salesplan" ? (
        <SalesPlanTab />
      ) : tab === "social" ? (
        <SocialTab />
      ) : tab === "romi" ? (
        <RomiTab />
      ) : tab === "rfm" ? (
        <RfmTab />
      ) : tab === "smm" ? (
        <div className="-mx-8 -my-2">
          <Smm />
        </div>
      ) : tab === "notify" ? (
        <NotifyTab />
      ) : tab === "referral" ? (
        <ReferralTab />
      ) : tab === "ads" ? (
        <AdsTab />
      ) : tab === "journey" ? (
        <JourneyTab months={months} />
      ) : loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : !data ? null : tab === "funnel" ? (
        <FunnelTab data={data} />
      ) : (
        <ChannelsTab data={data} cac={cac} />
      )}
    </div>
  );
}

// ------------------- Sotuv rejasi va marketolog bonusi -------------
// Jahongir (2026-08-11): sotuv rejasi bajarilishiga qarab bonus aniq
// jadval bo'yicha: 80% dan 1 mln ... 150%+ da 8 mln. Yangi to'lovlar
// soni va hozirgi o'quvchilar soni ham shu yerda ko'rinadi.
type SalesPlanRow = {
  branch_id: number; branch: string; plan: number; fact: number;
  percent: number | null; bonus: number; bonus_label: string;
  new_payments_count: number; students_now: number;
};

function SalesPlanTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<{
    rows: SalesPlanRow[]; can_edit: boolean;
    scale: { min: number; bonus: number; label: string }[];
  } | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [val, setVal] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    api
      .get<typeof d>(`/smm/sales-plan?year=${year}&month=${month}`)
      .then((r) => setD(r as never))
      .catch(() => setD(null));
  }, [year, month, reload]);

  async function save(branchId: number) {
    try {
      await api.put("/smm/sales-plan", {
        branch_id: branchId, year, month, amount: Number(val) || 0,
      });
      setEditing(null);
      setReload((k) => k + 1);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const MONTH_NAMES = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"];

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <select value={month} onChange={(e) => setMonth(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm">
          {MONTH_NAMES.map((m, i) => (
            <option key={m} value={i + 1}>{m}</option>
          ))}
        </select>
        <select value={year} onChange={(e) => setYear(Number(e.target.value))}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm">
          {[now.getFullYear(), now.getFullYear() - 1].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto mb-5">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Filial</th>
              <th className="text-right px-3 py-2.5 font-medium">Reja (so'm)</th>
              <th className="text-right px-3 py-2.5 font-medium">Fakt (tushum)</th>
              <th className="text-right px-3 py-2.5 font-medium">%</th>
              <th className="text-left px-3 py-2.5 font-medium">Holat</th>
              <th className="text-right px-3 py-2.5 font-medium">Bonus</th>
              <th className="text-right px-3 py-2.5 font-medium">Yangi to'lovlar</th>
              <th className="text-right px-3 py-2.5 font-medium">O'quvchilar</th>
            </tr>
          </thead>
          <tbody>
            {d.rows.map((r) => {
              const tone = r.percent == null
                ? "text-slate-400"
                : r.percent >= 100 ? "text-emerald-600"
                : r.percent >= 80 ? "text-amber-600" : "text-rose-600";
              return (
                <tr key={r.branch_id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 font-medium text-slate-900">
                    {r.branch}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums">
                    {editing === r.branch_id ? (
                      <span className="inline-flex items-center gap-1">
                        <input type="number" value={val} autoFocus
                          onChange={(e) => setVal(e.target.value)}
                          className="w-32 border border-slate-300 rounded-lg px-2 py-1 text-sm text-right" />
                        <button onClick={() => save(r.branch_id)}
                          className="text-emerald-600 text-xs font-medium">OK</button>
                        <button onClick={() => setEditing(null)}
                          className="text-slate-400 text-xs">✕</button>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5">
                        {r.plan ? formatSom(r.plan) : "—"}
                        {d.can_edit && (
                          <button
                            onClick={() => {
                              setEditing(r.branch_id);
                              setVal(r.plan ? String(r.plan) : "");
                            }}
                            className="text-slate-300 hover:text-brand-600"
                            title="Rejani kiritish/o'zgartirish">
                            ✎
                          </button>
                        )}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums">
                    {formatSom(r.fact)}
                  </td>
                  <td className={`px-3 py-2.5 text-right font-semibold tabular-nums ${tone}`}>
                    {r.percent != null ? `${r.percent}%` : "—"}
                  </td>
                  <td className={`px-3 py-2.5 text-xs ${tone}`}>
                    {r.bonus_label}
                  </td>
                  <td className={`px-3 py-2.5 text-right font-medium tabular-nums ${tone}`}>
                    {r.percent != null ? formatSom(r.bonus) : "—"}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums">
                    {r.new_payments_count}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums">
                    {r.students_now}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4 max-w-md">
        <p className="text-sm font-medium text-slate-900 mb-2">
          Bonus shkalasi
        </p>
        <table className="w-full text-xs">
          <tbody>
            <tr className="text-slate-500">
              <td className="py-1">80% dan past</td>
              <td>Sotuv rejasi bajarilmadi</td>
              <td className="text-right">bonus yo'q</td>
            </tr>
            {[...d.scale].sort((a, b) => a.min - b.min).map((s) => (
              <tr key={s.min} className="border-t border-slate-50">
                <td className="py-1">{s.min}%+</td>
                <td>{s.label}</td>
                <td className="text-right font-medium">{formatSom(s.bonus)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-[11px] text-slate-400 mt-2">
          Fakt — shu oyda filialga tushgan jami to'lovlar. Marketolog o'z
          panelida (Dashboard) xuddi shu raqamlarni ko'radi.
        </p>
      </div>
    </div>
  );
}
