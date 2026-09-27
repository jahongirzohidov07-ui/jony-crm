import { useCallback, useEffect, useRef, useState } from "react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, ComposedChart, Area, LabelList,
} from "recharts";
import { RefreshCw, Users, Eye, Radio, Heart, UserPlus, Sparkles } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * INSTAGRAM AUDITORIYA (2026-09-27). Jahongir: "jins bo'yicha, yosh
 * guruhi, qayerdan kuzatishlar, foydalanuvchilar aktiv paytlar, to'liq
 * instagramdagi barcha statistikalarni eng oson tushunadigan va chiroyli
 * vizual animatsiya chartlar bilan ... SMM managerimiz ko'rib mazza
 * qivorsin sodda va oson tushunarliligidan va o'ziga foydaligidan".
 *
 * Ma'lumot: GET /api/smm/instagram/audience (Meta + bazadagi postlar,
 * 6 soat kesh). Har blok bo'sh bo'lsa ham sahifa yiqilmaydi.
 */

const C = {
  brand: "#4f46e5", pink: "#ec4899", sky: "#0ea5e9", amber: "#f59e0b",
  emerald: "#10b981", violet: "#8b5cf6", slate: "#94a3b8", rose: "#f43f5e",
};
const GENDER: Record<string, { label: string; color: string }> = {
  F: { label: "Ayollar", color: C.pink },
  M: { label: "Erkaklar", color: C.sky },
  U: { label: "Ko'rsatilmagan", color: C.slate },
};
const COUNTRY: Record<string, string> = {
  UZ: "O'zbekiston", RU: "Rossiya", KZ: "Qozog'iston", TR: "Turkiya",
  US: "AQSh", KR: "Janubiy Koreya", DE: "Germaniya", KG: "Qirg'iziston",
  TJ: "Tojikiston", AE: "BAA", GB: "Buyuk Britaniya", PL: "Polsha",
  CZ: "Chexiya", IT: "Italiya", CN: "Xitoy", JP: "Yaponiya", SA: "Saudiya Arabistoni",
};
const flag = (cc: string) =>
  cc && cc.length === 2
    ? String.fromCodePoint(...[...cc.toUpperCase()].map((ch) => 127397 + ch.charCodeAt(0)))
    : "🌍";
const fmt = (n: number | null | undefined) =>
  n == null ? "—" : Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ");
const pct = (a: number, b: number) => (b ? Math.round((100 * a) / b) : 0);

function useCountUp(target: number, ms = 1100) {
  const [v, setV] = useState(0);
  const raf = useRef(0);
  useEffect(() => {
    const start = performance.now();
    const tick = (t: number) => {
      const k = Math.min(1, (t - start) / ms);
      setV(target * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, ms]);
  return v;
}

function Kpi({ icon: Icon, label, value, hint, tone, delay = 0 }: {
  icon: React.ElementType; label: string; value: number | null | undefined;
  hint?: string; tone: string; delay?: number;
}) {
  const v = useCountUp(value || 0);
  return (
    <div className="ig-rise rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
      style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-center gap-2 text-[12px] font-medium text-slate-500">
        <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${tone}`}>
          <Icon size={15} />
        </span>
        {label}
      </div>
      <p className="mt-2 text-2xl font-extrabold text-slate-900 tabular-nums">
        {value == null ? "—" : fmt(v)}
      </p>
      {hint && <p className="mt-0.5 text-[11px] text-slate-400">{hint}</p>}
    </div>
  );
}

function Card({ title, sub, children, className = "", delay = 0 }: {
  title: string; sub?: string; children: React.ReactNode; className?: string; delay?: number;
}) {
  return (
    <div className={`ig-rise rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
      style={{ animationDelay: `${delay}ms` }}>
      <p className="text-[15px] font-bold text-slate-900">{title}</p>
      {sub && <p className="text-[12px] text-slate-500 mb-3">{sub}</p>}
      {!sub && <div className="mb-3" />}
      {children}
    </div>
  );
}

const Empty = ({ text = "Meta bu ma'lumotni hozircha bermadi" }: { text?: string }) => (
  <div className="flex h-40 items-center justify-center rounded-xl bg-slate-50 text-[13px] text-slate-400 text-center px-4">
    {text}
  </div>
);

export function InstagramAudience() {
  const [d, setD] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback((refresh = false) => {
    setBusy(true); setErr("");
    api.get<Any>(`/smm/instagram/audience${refresh ? "?refresh=1" : ""}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setBusy(false));
  }, []);
  useEffect(() => load(false), [load]);

  if (!d && busy)
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-slate-400">
        <RefreshCw className="animate-spin" size={26} />
        <p className="text-sm">Instagram'dan statistika olinmoqda…</p>
      </div>
    );
  if (err && !d) return <p className="text-sm text-red-600 py-8 text-center">{err}</p>;
  if (!d) return null;
  if (d.ok === false)
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Instagram ulanmagan. Avval «Instagram» bo'limida ulang.
      </p>
    );

  const p = d.profile || {};
  const t = d.totals || {};
  const L = d.local || {};
  const gender = (d.gender || []).map((x: Any) => ({
    name: GENDER[x.key]?.label || x.key, value: x.value,
    color: GENDER[x.key]?.color || C.slate,
  }));
  const gTot = gender.reduce((s: number, x: Any) => s + x.value, 0);
  const age = [...(d.age || [])].sort((a: Any, b: Any) =>
    String(a.key).localeCompare(String(b.key)));
  const ageTop = (d.age || [])[0]?.key;
  const cities = (d.city || []).slice(0, 8).map((x: Any) => ({
    name: String(x.key).split(",")[0], value: x.value }));
  const cTot = (d.city || []).reduce((s: number, x: Any) => s + x.value, 0);
  const countries = (d.country || []).slice(0, 6);
  const coTot = (d.country || []).reduce((s: number, x: Any) => s + x.value, 0);
  const hours: number[] = d.online_hours || [];
  const top3 = [...hours.keys()].sort((a, b) => hours[b] - hours[a]).slice(0, 3);
  const hourData = hours.map((v, h) => ({ h: `${String(h).padStart(2, "0")}`, v, top: top3.includes(h) }));
  const growthMap: Record<string, Any> = {};
  (L.growth_days || []).forEach((g: Any) => { growthMap[g.date] = g; });
  const daily = (d.reach_daily || []).map((r: Any) => ({
    date: r.date.slice(5).split("-").reverse().join("."),
    iso: r.date, reach: r.value,
    followers: growthMap[r.date]?.new_followers ?? null,
  }));
  if (!daily.length)
    (L.growth_days || []).forEach((g: Any) => daily.push({
      date: g.date.slice(5).split("-").reverse().join("."), iso: g.date,
      reach: null, followers: g.new_followers }));
  const postHours = (L.post_hours || []).filter((x: Any) => x.posts > 0);
  const net = d.follows != null ? (d.follows || 0) - (d.unfollows || 0) : null;

  return (
    <div className="space-y-5">
      <style>{`
        @keyframes igRise { from { opacity: 0; transform: translateY(14px) } to { opacity: 1; transform: none } }
        .ig-rise { animation: igRise .55s cubic-bezier(.2,.8,.2,1) both }
      `}</style>

      {/* ---------- sarlavha ---------- */}
      <div className="ig-rise relative overflow-hidden rounded-3xl bg-gradient-to-r from-fuchsia-600 via-pink-500 to-amber-400 p-5 text-white shadow-lg">
        <div className="flex flex-wrap items-center gap-4">
          {p.profile_picture_url ? (
            <img src={p.profile_picture_url} alt="" className="h-16 w-16 rounded-full border-4 border-white/70 object-cover" />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 text-2xl">📸</div>
          )}
          <div className="min-w-0">
            <p className="text-xl font-extrabold">@{p.username || "instagram"}</p>
            <p className="text-sm text-white/85">
              {fmt(p.followers_count)} obunachi · {fmt(p.media_count)} post
              {net != null && <> · 28 kunda <b>{net >= 0 ? "+" : ""}{fmt(net)}</b></>}
            </p>
          </div>
          <button onClick={() => load(true)} disabled={busy}
            className="ml-auto inline-flex items-center gap-2 rounded-xl bg-white/20 px-4 py-2 text-sm font-semibold backdrop-blur hover:bg-white/30 disabled:opacity-60">
            <RefreshCw size={15} className={busy ? "animate-spin" : ""} />
            {busy ? "Yangilanmoqda…" : "Yangilash"}
          </button>
        </div>
        {d.fetched_at && (
          <p className="mt-3 text-[11px] text-white/75">
            Instagram'dan olingan: {d.fetched_at.replace("T", " ").slice(0, 16)} (UTC) · har 6 soatda yangilanadi
          </p>
        )}
      </div>

      {/* ---------- asosiy raqamlar ---------- */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <Kpi icon={Users} label="Obunachilar" value={p.followers_count} tone="bg-pink-100 text-pink-600" delay={40} />
        <Kpi icon={Radio} label="Qamrov" value={t.reach} hint="28 kunda ko'rgan odamlar" tone="bg-indigo-100 text-indigo-600" delay={90} />
        <Kpi icon={Eye} label="Ko'rishlar" value={t.views} hint="28 kun" tone="bg-sky-100 text-sky-600" delay={140} />
        <Kpi icon={Sparkles} label="Faol foydalanuvchi" value={t.accounts_engaged} hint="like/izoh/saqlash qilganlar" tone="bg-violet-100 text-violet-600" delay={190} />
        <Kpi icon={Heart} label="Interaksiyalar" value={t.total_interactions} hint="28 kun jami" tone="bg-rose-100 text-rose-600" delay={240} />
        <Kpi icon={UserPlus} label="Yangi obunachi" value={d.follows} hint={d.unfollows != null ? `${fmt(d.unfollows)} kishi chiqdi` : "28 kun"} tone="bg-emerald-100 text-emerald-600" delay={290} />
      </div>

      {/* ---------- xulosalar ---------- */}
      {(d.tips || []).length > 0 && (
        <Card title="💡 Bugungi xulosalar" sub="Raqamlardan chiqqan oddiy maslahatlar" delay={120}>
          <div className="grid gap-2 md:grid-cols-2">
            {d.tips.map((x: Any, i: number) => (
              <div key={i} className="ig-rise flex gap-3 rounded-xl bg-gradient-to-r from-slate-50 to-white border border-slate-100 p-3"
                style={{ animationDelay: `${200 + i * 70}ms` }}>
                <span className="text-xl leading-none">{x.icon}</span>
                <p className="text-[13px] leading-relaxed text-slate-700">{x.text}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ---------- jins va yosh ---------- */}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Jins bo'yicha" sub="Obunachilaringiz kimlar" delay={160}>
          {gender.length ? (
            <div className="flex items-center gap-4">
              <div className="h-52 w-52 shrink-0">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={gender} dataKey="value" nameKey="name" innerRadius={58} outerRadius={90}
                      paddingAngle={3} animationDuration={1100}>
                      {gender.map((g: Any) => <Cell key={g.name} fill={g.color} />)}
                    </Pie>
                    <Tooltip formatter={(v: Any) => [`${fmt(v)} (${pct(v, gTot)}%)`, ""]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1 space-y-3">
                {gender.map((g: Any) => (
                  <div key={g.name}>
                    <div className="flex justify-between text-[13px]">
                      <span className="font-semibold text-slate-700">
                        <span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full" style={{ background: g.color }} />
                        {g.name}
                      </span>
                      <span className="font-bold text-slate-900">{pct(g.value, gTot)}%</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-1000"
                        style={{ width: `${pct(g.value, gTot)}%`, background: g.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : <Empty />}
        </Card>

        <Card title="Yosh guruhlari" sub={ageTop ? `Eng ko'p: ${ageTop} yosh` : "Obunachilar yoshi"} delay={200}>
          {age.length ? (
            <div className="h-56">
              <ResponsiveContainer>
                <BarChart data={age} margin={{ top: 18, right: 8, left: -18, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="key" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: Any) => [fmt(v), "obunachi"]} labelFormatter={(l) => `${l} yosh`} />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} animationDuration={1100}>
                    {age.map((a: Any) => (
                      <Cell key={a.key} fill={a.key === ageTop ? C.brand : "#c7d2fe"} />
                    ))}
                    <LabelList dataKey="value" position="top" formatter={(v: Any) => fmt(v)}
                      style={{ fontSize: 11, fill: "#475569" }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty />}
        </Card>
      </div>

      {/* ---------- geografiya ---------- */}
      <div className="grid gap-5 lg:grid-cols-5">
        <Card title="📍 Shaharlar" sub="Obunachilar qayerda yashaydi" className="lg:col-span-3" delay={220}>
          {cities.length ? (
            <div style={{ height: Math.max(180, cities.length * 34) }}>
              <ResponsiveContainer>
                <BarChart data={cities} layout="vertical" margin={{ top: 0, right: 40, left: 10, bottom: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: Any) => [`${fmt(v)} (${pct(v, cTot)}%)`, "obunachi"]} />
                  <Bar dataKey="value" radius={[0, 8, 8, 0]} fill={C.violet} animationDuration={1200}>
                    <LabelList dataKey="value" position="right"
                      formatter={(v: Any) => `${pct(v, cTot)}%`} style={{ fontSize: 11, fill: "#475569" }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty />}
        </Card>
        <Card title="🌍 Davlatlar" sub="Qaysi davlatlardan kuzatishadi" className="lg:col-span-2" delay={260}>
          {countries.length ? (
            <div className="space-y-3">
              {countries.map((c: Any) => (
                <div key={c.key}>
                  <div className="flex justify-between text-[13px]">
                    <span className="font-semibold text-slate-700">
                      <span className="mr-2 text-base">{flag(c.key)}</span>{COUNTRY[c.key] || c.key}
                    </span>
                    <span className="font-bold text-slate-900">{pct(c.value, coTot)}%</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-sky-400 to-indigo-500 transition-all duration-1000"
                      style={{ width: `${pct(c.value, coTot)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : <Empty />}
        </Card>
      </div>

      {/* ---------- faol soatlar ---------- */}
      <Card title="⏰ Obunachilar qachon onlayn"
        sub={hours.length ? `Eng faol soatlar: ${top3.map((h) => `${String(h).padStart(2, "0")}:00`).join(", ")} (Toshkent vaqti) — postni shu vaqtdan biroz oldin joylang` : "Soatlar bo'yicha"}
        delay={280}>
        {hours.length ? (
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={hourData} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="h" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: Any) => [fmt(v), "onlayn obunachi"]} labelFormatter={(l) => `${l}:00`} />
                <Bar dataKey="v" radius={[6, 6, 0, 0]} animationDuration={1300}>
                  {hourData.map((x) => <Cell key={x.h} fill={x.top ? C.amber : "#fde68a"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <Empty text="Meta onlayn soatlarni hali bermadi (odatda 100+ obunachida ochiladi)" />}
      </Card>

      {/* ---------- kunlik dinamika ---------- */}
      <Card title="📈 Oxirgi 28 kun" sub="Qamrov (to'lqin) va yangi obunachilar (ustun). Ustun ustiga olib boring — o'sha kuni chiqqan postlar ko'rinadi" delay={300}>
        {daily.length ? (
          <div className="h-72">
            <ResponsiveContainer>
              <ComposedChart data={daily} margin={{ top: 10, right: 8, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="igReach" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={C.brand} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={C.brand} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis yAxisId="r" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="f" orientation="right" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={({ active, payload }: Any) => {
                  if (!active || !payload?.length) return null;
                  const row = payload[0].payload;
                  const posts = growthMap[row.iso]?.posts || [];
                  return (
                    <div className="max-w-[260px] rounded-xl border border-slate-200 bg-white p-3 text-[12px] shadow-lg">
                      <p className="font-bold text-slate-900">{row.date}</p>
                      {row.reach != null && <p className="text-indigo-600">Qamrov: {fmt(row.reach)}</p>}
                      {row.followers != null && <p className="text-emerald-600">Yangi obunachi: +{fmt(row.followers)}</p>}
                      {posts.length > 0 && (
                        <div className="mt-1.5 border-t border-slate-100 pt-1.5 text-slate-600">
                          {posts.map((x: Any) => <p key={x.id} className="truncate">🎬 {x.caption}</p>)}
                        </div>
                      )}
                    </div>
                  );
                }} />
                <Area yAxisId="r" type="monotone" dataKey="reach" stroke={C.brand} strokeWidth={2.5}
                  fill="url(#igReach)" animationDuration={1400} />
                <Bar yAxisId="f" dataKey="followers" fill={C.emerald} radius={[5, 5, 0, 0]}
                  barSize={10} animationDuration={1400} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : <Empty />}
      </Card>

      {/* ---------- qachon joylash foydali ---------- */}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="🚀 Qaysi soatda joylangan post ko'proq qamrov oldi" sub="O'zimizning oxirgi 6 oylik postlarimiz bo'yicha o'rtacha qamrov" delay={320}>
          {postHours.length ? (
            <div className="h-56">
              <ResponsiveContainer>
                <BarChart data={postHours.map((x: Any) => ({ ...x, h: `${String(x.hour).padStart(2, "0")}:00` }))}
                  margin={{ top: 10, right: 8, left: -10, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="h" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: Any, _n: Any, it: Any) => [`${fmt(v)} (${it.payload.posts} ta post)`, "o'rtacha qamrov"]} />
                  <Bar dataKey="avg_reach" fill={C.pink} radius={[6, 6, 0, 0]} animationDuration={1200} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty text="Postlar hali yetarli emas" />}
        </Card>
        <Card title="📅 Hafta kunlari" sub="Qaysi kuni joylangan post ko'proq ko'rildi" delay={340}>
          {(L.post_weekdays || []).some((x: Any) => x.posts) ? (
            <div className="h-56">
              <ResponsiveContainer>
                <BarChart data={L.post_weekdays} margin={{ top: 18, right: 8, left: -10, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: Any, _n: Any, it: Any) => [`${fmt(v)} (${it.payload.posts} ta post)`, "o'rtacha qamrov"]} />
                  <Bar dataKey="avg_reach" fill={C.sky} radius={[8, 8, 0, 0]} animationDuration={1200}>
                    <LabelList dataKey="avg_reach" position="top" formatter={(v: Any) => (v ? fmt(v) : "")}
                      style={{ fontSize: 10, fill: "#475569" }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty text="Postlar hali yetarli emas" />}
        </Card>
      </div>

      {/* ---------- format solishtirish ---------- */}
      {(L.types || []).length > 0 && (
        <Card title="🎬 Qaysi format yaxshiroq ishlaydi" sub="Bitta postga o'rtacha (oxirgi 6 oy)" delay={360}>
          <div className="grid gap-3 md:grid-cols-3">
            {L.types.map((x: Any, i: number) => {
              const max = Math.max(...L.types.map((y: Any) => y.avg_views || 0), 1);
              return (
                <div key={x.type} className={`rounded-2xl p-4 border ${i === 0 ? "border-amber-300 bg-amber-50" : "border-slate-200 bg-slate-50"}`}>
                  <p className="text-[13px] font-bold text-slate-800">{i === 0 ? "🏆 " : ""}{x.type}</p>
                  <p className="text-[11px] text-slate-500">{x.posts} ta post</p>
                  <p className="mt-2 text-2xl font-extrabold text-slate-900">{fmt(x.avg_views)}</p>
                  <p className="text-[11px] text-slate-500">o'rtacha ko'rish</p>
                  <div className="mt-2 h-2 rounded-full bg-white overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-pink-500 to-amber-400 transition-all duration-1000"
                      style={{ width: `${Math.round((100 * (x.avg_views || 0)) / max)}%` }} />
                  </div>
                  <p className="mt-2 text-[11px] text-slate-600">
                    Qamrov {fmt(x.avg_reach)} · Interaksiya {fmt(x.avg_engagement)}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* ---------- top postlar ---------- */}
      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="🔥 Top-5: eng ko'p ko'rilgan" sub="Oxirgi 30 kun" delay={380}>
          <PostList items={L.top_views || []} metric="views" label="ko'rish" />
        </Card>
        <Card title="⭐ Eng ko'p obunachi kelgan kunlar" sub="Kunlik o'sish va o'sha kuni chiqqan post" delay={400}>
          {(L.best_days || []).length ? (
            <div className="space-y-2">
              {L.best_days.map((g: Any) => (
                <div key={g.date} className="rounded-xl bg-emerald-50/60 border border-emerald-100 p-2.5">
                  <div className="flex items-center justify-between text-[12px]">
                    <span className="font-semibold text-slate-700">{g.date.split("-").reverse().join(".")}</span>
                    <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[11px] font-bold text-white">+{fmt(g.new_followers)}</span>
                  </div>
                  {g.posts.map((x: Any) => (
                    <a key={x.id} href={x.permalink} target="_blank" rel="noreferrer"
                      className="mt-1 block truncate text-[12px] text-slate-600 hover:text-brand-700">🎬 {x.caption}</a>
                  ))}
                </div>
              ))}
            </div>
          ) : <Empty text="Kunlik obunachi o'sishi hali kelmadi" />}
        </Card>
        <Card title="➕ Obuna olib kelgan postlar" sub="Faqat rasm/karusel — reels uchun Meta bermaydi" delay={420}>
          <PostList items={L.top_follows || []} metric="follows" label="obuna" plus />
        </Card>
      </div>

      <p className="text-[12px] text-slate-400 leading-relaxed">
        ℹ️ Meta reels uchun «shu videodan nechta obuna» raqamini API orqali bermaydi (Instagram ilovasida ko'rinadi, lekin
        tashqi dasturlarga ochilmagan). Shuning uchun reels ta'siri «Eng ko'p obunachi kelgan kunlar» va 28 kunlik
        grafikda — o'sha kuni chiqqan post bilan birga ko'rsatiladi.
      </p>
      {d.errors && Object.keys(d.errors).length > 0 && (
        <details className="text-[11px] text-slate-400">
          <summary className="cursor-pointer">Ba'zi ko'rsatkichlar Meta'dan kelmadi ({Object.keys(d.errors).length})</summary>
          <ul className="mt-1 space-y-0.5">
            {Object.entries(d.errors).map(([k, v]) => <li key={k}><b>{k}</b>: {String(v)}</li>)}
          </ul>
        </details>
      )}
    </div>
  );
}

function PostList({ items, metric, label, plus }: {
  items: Any[]; metric: string; label: string; plus?: boolean;
}) {
  if (!items.length) return <Empty text="Hozircha ma'lumot yo'q" />;
  const max = Math.max(...items.map((x) => x[metric] || 0), 1);
  return (
    <div className="space-y-2.5">
      {items.map((x, i) => (
        <a key={x.id} href={x.permalink} target="_blank" rel="noreferrer" className="block group">
          <div className="flex items-center gap-2 text-[12px]">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[10px] font-bold text-white">{i + 1}</span>
            <span className="min-w-0 flex-1 truncate text-slate-700 group-hover:text-brand-700">{x.caption}</span>
            <span className="shrink-0 font-bold text-slate-900">{plus ? "+" : ""}{fmt(x[metric])}</span>
          </div>
          <div className="ml-7 mt-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 transition-all duration-1000"
              style={{ width: `${Math.round((100 * (x[metric] || 0)) / max)}%` }} title={label} />
          </div>
        </a>
      ))}
    </div>
  );
}
