import { useEffect, useState } from "react";
import {
  Megaphone, AlertTriangle, Plus, X, Info, Calendar,
  Lightbulb, Inbox, ExternalLink, MessageSquare, TrendingUp,
  Palette, Image, BookOpen, BarChart3, Table2,
} from "lucide-react";
import {
  api, type ContentMeta, type ContentList, type ContentRow,
  type ContentFull, type SmmDashboard, type IdeaRow,
  type RequestRow, type Branch, type InboxList, type InboxRow,
  type AttributionReport, type Attribution, type CampaignRow,
  type FunnelStep, type BrandBook, type BrandRow, type MediaList,
  type KbList, type KbRow, type SmmAnalytics, type SmmKpi,
  type SmmReport,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { Time24Input } from "../components/Time24Input";
import { ContentPlan, ContentAnalytics } from "../components/ContentPlan";
import { InstagramPanel } from "../components/InstagramPanel";
import { VideoCheck } from "../components/VideoCheck";
import {
  SMM_ACCESS, IDEA_SUBMIT, CONTENT_REQUESTER, INBOX_ACCESS, can,
} from "../lib/roles";
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;

type Tab = "dashboard" | "calendar" | "plan" | "board" | "canalytics"
  | "instagram" | "inbox"
  | "attribution" | "ideas" | "requests" | "brand" | "media" | "kb"
  | "report";

const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
  { key: "dashboard", label: "Bugun", icon: Megaphone },
  { key: "calendar", label: "Kontent taqvimi", icon: Calendar },
  // 2026-08-27, Jahongir Excel kontent-planini yubordi: oy bir
  // ko'zda ko'rinadigan jadval + ichida ssenariy + havoladan
  // avtomat natija.
  { key: "plan", label: "Kontent-plan", icon: Table2 },
  { key: "board", label: "Holat doskasi", icon: Table2 },
  { key: "canalytics", label: "Kontent tahlili", icon: TrendingUp },
  { key: "instagram", label: "Instagram", icon: Image },
  { key: "inbox", label: "Murojaatlar", icon: MessageSquare },
  { key: "attribution", label: "Natija", icon: TrendingUp },
  { key: "ideas", label: "G'oyalar", icon: Lightbulb },
  { key: "requests", label: "So'rovlar", icon: Inbox },
  { key: "report", label: "Hisobot", icon: BarChart3 },
  { key: "media", label: "Media", icon: Image },
  { key: "brand", label: "Brend kitob", icon: Palette },
  { key: "kb", label: "Bilimlar bazasi", icon: BookOpen },
];

export default function Smm() {
  const { user } = useAuth();
  const isSmm = can(user?.role, SMM_ACCESS);
  const seesInbox = can(user?.role, INBOX_ACCESS);
  const [tab, setTab] = useState<Tab>(
    isSmm ? "dashboard" : seesInbox ? "inbox" : "brand");
  // "Boshqa" ro'yxati ochiqmi (hook erta return'dan OLDIN bo'lishi shart)
  const [more, setMore] = useState(false);

  if (!can(user?.role, CONTENT_REQUESTER) && !can(user?.role, IDEA_SUBMIT)
      && !seesInbox)
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );

  const shown = TABS.filter((t) => {
    // Brend kitob va bilimlar bazasini har qanday xodim o'qiy oladi —
    // brend hammaning ishi.
    if (t.key === "brand" || t.key === "kb") return true;
    if (t.key === "inbox" || t.key === "attribution") return seesInbox;
    return isSmm || t.key === "ideas" || t.key === "requests";
  });

  // SODDALASHTIRISH (2026-09-26, Jahongir: "SMM qismini juda ham
  // murakkablashib ketgan shuni eng kerakli qismlarini qoldirib
  // soddalashtirib bergin"). Ekranda faqat kundalik ish uchun 4 ta
  // asosiy bo'lim: Bugun, Kontent-plan, Tahlil, Murojaatlar. Qolganlari
  // O'CHIRILMAGAN — "Boshqa" tugmasi ostida turadi, ma'lumotlari joyida.
  // SMM bo'lmagan xodim (g'oya/so'rov yuboruvchi) uchun bo'limlar kam —
  // ularga hammasi avvalgidek ko'rinadi.
  // 2026-09-26 (2): "Murojaatlar" tushunarsiz edi (Instagram ulanmagan,
  // bo'sh turardi) — "Boshqa"ga o'tdi. O'rniga "Holat doskasi" (Kanban).
  // Jahongir: "brendbookni qoldir" — Brend kitob asosiy qatorda.
  // Instagram (2026-09-26): "telegramdan kora bizga instagram muhim".
  const MAIN: Tab[] = ["dashboard", "plan", "board", "canalytics",
                       "instagram", "brand"];
  const primary = isSmm ? shown.filter((t) => MAIN.includes(t.key)) : shown;
  const extra = isSmm ? shown.filter((t) => !MAIN.includes(t.key)) : [];
  const extraActive = extra.some((t) => t.key === tab);
  const label = (t: { key: Tab; label: string }) =>
    t.key === "canalytics" ? "Tahlil" : t.label;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Megaphone size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">SMM</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Reja → joylash → natija
      </p>

      <div className="flex gap-1 border-b border-slate-200 mb-2 overflow-x-auto">
        {primary.map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setMore(false); }}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px whitespace-nowrap transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {label(t)}
          </button>
        ))}
        {extra.length > 0 && (
          <button
            onClick={() => setMore((v) => !v)}
            className={`ml-auto px-3 py-2.5 text-sm border-b-2 -mb-px whitespace-nowrap ${
              extraActive
                ? "border-brand-600 text-brand-700 font-medium"
                : "border-transparent text-slate-400 hover:text-slate-600"
            }`}
            title="Kam ishlatiladigan bo'limlar: taqvim, g'oyalar, so'rovlar, hisobot, media, brend kitob..."
          >
            {extraActive ? label(extra.find((t) => t.key === tab)!) : "Boshqa"} {more ? "▴" : "▾"}
          </button>
        )}
      </div>
      {more && extra.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {extra.map((t) => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); setMore(false); }}
              className={`px-3 py-1.5 rounded-lg text-sm border ${
                tab === t.key
                  ? "border-brand-300 bg-brand-50 text-brand-700"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}
      {!more && <div className="mb-3" />}

      {tab === "dashboard" && <DashboardTab />}
      {tab === "calendar" && <CalendarTab />}
      {tab === "plan" && <ContentPlan />}
      {tab === "board" && <BoardTab />}
      {tab === "instagram" && <InstagramPanel />}
      {tab === "canalytics" && <ContentAnalytics />}
      {tab === "inbox" && <InboxTab />}
      {tab === "attribution" && <AttributionTab />}
      {tab === "report" && <ReportTab />}
      {tab === "media" && <MediaTab />}
      {tab === "brand" && <BrandTab />}
      {tab === "kb" && <KbTab />}
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

// ==================================================== Holat doskasi
/* KANBAN (2026-09-26). Jahongir: "xuddi LID bolimidagiga oxshab har
   bir kontentni holatni o'tkizadigan qilib qoyish kerak qaysi holatga
   kelganini qo'lda surib o'tkizib qoya oladigan bo'lsa yaxshi
   bo'ladi". Leads.tsx dagi kabi HTML5 drag&drop: kartani ustunga
   tashlasangiz POST /content/{id}/status chaqiriladi (rozilik
   tekshiruvi va audit backendda — bu yerda chetlab o'tilmaydi).
   "Bekor qilingan" ustuni standart yashirin — ma'lumot o'chmaydi. */
function BoardTab() {
  const [meta, setMeta] = useState<ContentMeta | null>(null);
  const [rows, setRows] = useState<ContentRow[] | null>(null);
  const [dragId, setDragId] = useState<number | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [platform, setPlatform] = useState("");
  const [q, setQ] = useState("");
  const [showCancelled, setShowCancelled] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [urgent, setUrgent] = useState(false);

  // MANBA = KONTENT-PLAN (2026-09-26). Jahongir: "bizdagi kontent
  // rejalarimizdagi shu kontentlarni ... kontent plan bo'limida ketma
  // ket ko'rinib turishi kerak". Avval doska /content ro'yxatidan
  // o'qirdi — u filial tanlanganda filialsiz (Exceldan yuklangan)
  // postlarni ko'rsatmasdi va doska bo'sh chiqardi. Endi aynan
  // Kontent-plan qatorlari (bir xil filial qoidasi), sana tartibida.
  const load = () => {
    api
      .get<Any>("/smm/plan")
      .then((d) => {
        const plan: Any[] = d.rows || [];
        setRows(plan.map((r: Any) => ({
          id: r.id, title: r.title,
          planned_date: r.date, planned_time: r.time,
          platform: r.platform,
          platform_label: r.platform || "—",
          platform_tone: /insta/i.test(r.platform || "") ? "rose"
            : /tele/i.test(r.platform || "") ? "sky"
            : /you/i.test(r.platform || "") ? "red" : "slate",
          owner: r.owner, status: r.status,
          status_label: r.status_label, tone: r.status_tone,
          priority: r.priority,
          warnings: r.warnings || [],
          blocked: (r.warnings || []).some((w: Any) => w.severity === "block"),
        } as Any)).sort((a: Any, b: Any) =>
          (a.planned_date || "9999").localeCompare(b.planned_date || "9999")
          || (a.planned_time || "").localeCompare(b.planned_time || "")));
      })
      .catch(() => setRows([]));
  };
  useEffect(() => {
    api.get<ContentMeta>("/content-meta").then(setMeta);
  }, []);
  useEffect(load, []);

  if (!meta || !rows)
    return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const moveTo = async (c: ContentRow, status: string) => {
    if (c.status === status) return;
    const st = meta.statuses.find((s) => s.key === status);
    const prev = rows;
    // Darrov ko'chadi (optimistik), xato bo'lsa joyiga qaytadi
    setRows(rows.map((r) => r.id === c.id
      ? { ...r, status, status_label: st?.label || status,
          tone: st?.tone || r.tone }
      : r));
    setErr("");
    try {
      await api.post(`/content/${c.id}/status`, { status });
      load();
    } catch (e) {
      setRows(prev);
      setErr(`«${c.title}»: ` +
        (e instanceof Error ? e.message : "holat o'zgarmadi"));
    }
  };

  const needle = q.trim().toLowerCase();
  const shownRows = rows.filter((r) =>
    (!platform || (r.platform || "") === platform)
    && (!needle || (r.title || "").toLowerCase().includes(needle)
        || (r.owner || "").toLowerCase().includes(needle)));
  const platformOpts = Array.from(new Set(
    rows.map((r) => r.platform || "").filter(Boolean)));
  const cols = meta.statuses.filter(
    (s) => showCancelled || s.key !== "cancelled");
  const cancelledCount = rows.filter((r) => r.status === "cancelled").length;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Qidirish: mavzu yoki mas'ul"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm w-56"
        />
        <select
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
        >
          <option value="">Barcha platformalar</option>
          {platformOpts.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-xs text-slate-500">
          <input type="checkbox" checked={showCancelled}
            onChange={(e) => setShowCancelled(e.target.checked)} />
          Bekor qilinganlar ({cancelledCount})
        </label>
        <div className="flex-1" />
        <span className="text-xs text-slate-400">
          Kartani sichqoncha bilan kerakli ustunga suring
        </span>
        <button
          onClick={() => setUrgent(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium"
        >
          <AlertTriangle size={14} /> Favqulodda o'zgarish
        </button>
      </div>
      {urgent && (
        <UrgentChange
          rows={rows.filter((r) => r.status !== "cancelled")}
          platforms={[{ key: "instagram", label: "Instagram" },
                      { key: "telegram", label: "Telegram" },
                      { key: "youtube", label: "YouTube" }]}
          onClose={() => setUrgent(false)}
          onDone={(m) => { setUrgent(false); setErr(""); setOk(m); load(); }}
        />
      )}
      {ok && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-[13px] text-emerald-800 flex items-start gap-2">
          <span className="flex-1">{ok}</span>
          <button onClick={() => setOk("")}><X size={14} /></button>
        </div>
      )}
      {err && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-[13px] text-red-700 flex items-start gap-2">
          <span className="flex-1">{err}</span>
          <button onClick={() => setErr("")}><X size={14} /></button>
        </div>
      )}

      <div className="flex gap-3 overflow-x-auto pb-4">
        {cols.map((st) => {
          const items = shownRows.filter((r) => r.status === st.key);
          return (
            <div
              key={st.key}
              data-col={st.key}
              onDragOver={(e) => { e.preventDefault(); setOver(st.key); }}
              onDragLeave={() => setOver((s) => (s === st.key ? null : s))}
              onDrop={(e) => {
                e.preventDefault();
                setOver(null);
                const c = rows.find((r) => r.id === dragId);
                if (c) moveTo(c, st.key);
                setDragId(null);
              }}
              className={`w-60 shrink-0 rounded-xl p-2 transition ${
                over === st.key
                  ? "bg-brand-50/70 ring-2 ring-brand-300" : "bg-slate-50"
              }`}
            >
              <div className="flex items-center justify-between px-1.5 py-1.5 mb-1">
                <span className={`rounded-md px-2 py-0.5 text-xs font-semibold ${
                  TONE[st.tone] || TONE.slate}`}>
                  {st.label}
                </span>
                <span className="text-xs font-medium text-slate-400">
                  {items.length}
                </span>
              </div>
              <div className="space-y-2 min-h-[60px]">
                {items.map((c) => (
                  <div
                    key={c.id}
                    draggable
                    onDragStart={(e) => {
                      setDragId(c.id);
                      e.dataTransfer.effectAllowed = "move";
                    }}
                    onDragEnd={() => setDragId(null)}
                    onClick={() => setOpen(c.id)}
                    className={`cursor-grab active:cursor-grabbing rounded-lg border p-2.5 text-left bg-white hover:border-brand-400 transition ${
                      dragId === c.id ? "opacity-40" : ""
                    } ${c.blocked ? "border-red-200" : "border-slate-200"}`}
                  >
                    <p className="text-[13px] font-medium text-slate-800 leading-snug">
                      {c.title}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {c.planned_date ? formatDate(c.planned_date) : "Sanasiz"}
                      {c.planned_time ? ` · ${c.planned_time}` : ""}
                    </p>
                    <div className="flex flex-wrap items-center gap-1 mt-1.5">
                      {c.priority === "urgent" && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-600 text-white">
                          Favqulodda
                        </span>
                      )}
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        TONE[c.platform_tone] || TONE.slate}`}>
                        {c.platform_label}
                      </span>
                      {c.owner && (
                        <span className="text-[10px] text-slate-500">{c.owner}</span>
                      )}
                      {c.warnings.length > 0 && (
                        <span className="flex items-center gap-0.5 text-[10px] text-red-600"
                          title={c.warnings.map((w) => w.text).join("\n")}>
                          <AlertTriangle size={10} /> {c.warnings.length}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {items.length === 0 && (
                  <p className="text-xs text-slate-300 text-center py-4">Bo'sh</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {open !== null && (
        <ContentCard id={open} onClose={() => { setOpen(null); load(); }} />
      )}
    </div>
  );
}

/** Favqulodda o'zgarish oynasi: yangi post / ko'chirish / bekor qilish.
 *  Sabab majburiy — backend (/api/smm/urgent) ham tekshiradi. */
function UrgentChange({
  rows, platforms, onClose, onDone,
}: {
  rows: ContentRow[];
  platforms: { key: string; label: string }[];
  onClose: () => void;
  onDone: (msg: string) => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [action, setAction] = useState<"add" | "move" | "cancel">("add");
  const [title, setTitle] = useState("");
  const [platform, setPlatform] = useState("instagram");
  const [cid, setCid] = useState<number | "">("");
  const [pd, setPd] = useState(today);
  const [time, setTime] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async () => {
    setErr("");
    if (reason.trim().length < 3) { setErr("Sababini yozing"); return; }
    if (action === "add" && !title.trim()) { setErr("Mavzuni yozing"); return; }
    if (action !== "add" && !cid) { setErr("Postni tanlang"); return; }
    setBusy(true);
    try {
      await api.post("/smm/urgent", {
        action, reason, title, platform,
        content_id: cid || null,
        planned_date: pd, planned_time: time || null,
      });
      onDone(action === "add" ? "Favqulodda post qo'shildi"
        : action === "move" ? "Post ko'chirildi" : "Post bekor qilindi");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  const inp = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm";
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4"
      onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-md p-5 space-y-3"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Favqulodda o'zgarish</h3>
          <button onClick={onClose}><X size={16} /></button>
        </div>
        <div className="flex gap-1.5">
          {([["add", "Yangi post"], ["move", "Ko'chirish"],
             ["cancel", "Bekor qilish"]] as const).map(([k, l]) => (
            <button key={k} onClick={() => setAction(k)}
              className={`flex-1 px-2 py-1.5 rounded-lg text-sm border ${
                action === k ? "border-red-300 bg-red-50 text-red-700 font-medium"
                  : "border-slate-200 text-slate-600"}`}>
              {l}
            </button>
          ))}
        </div>
        {action === "add" ? (
          <>
            <input className={inp} placeholder="Post mavzusi"
              value={title} onChange={(e) => setTitle(e.target.value)} />
            <select className={inp} value={platform}
              onChange={(e) => setPlatform(e.target.value)}>
              {platforms.map((p) => (
                <option key={p.key} value={p.key}>{p.label}</option>
              ))}
            </select>
          </>
        ) : (
          <select className={inp} value={cid}
            onChange={(e) => setCid(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Postni tanlang…</option>
            {rows.map((r) => (
              <option key={r.id} value={r.id}>
                {r.planned_date ? formatDate(r.planned_date) + " · " : ""}{r.title}
              </option>
            ))}
          </select>
        )}
        {action !== "cancel" && (
          <div className="flex gap-2">
            <input type="date" className={inp} value={pd}
              onChange={(e) => setPd(e.target.value)} />
            <Time24Input value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
        )}
        <textarea className={inp} rows={2}
          placeholder="Sabab (majburiy): nega reja o'zgaryapti?"
          value={reason} onChange={(e) => setReason(e.target.value)} />
        {err && <p className="text-sm text-red-600">{err}</p>}
        <button onClick={submit} disabled={busy}
          className="w-full py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">
          {busy ? "Saqlanmoqda…" : "Tasdiqlash"}
        </button>
        <p className="text-[11px] text-slate-400">
          Hech narsa o'chmaydi: eski sana va holat tarixda qoladi,
          rahbar auditda ko'radi.
        </p>
      </div>
    </div>
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
              <Time24Input
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
          {canEdit && <VideoCheck contentId={d.id} />}

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

// ============================================================ Inbox
function InboxTab() {
  const [d, setD] = useState<InboxList | null>(null);
  const [status, setStatus] = useState("");
  const [channel, setChannel] = useState("");
  const [open, setOpen] = useState<InboxRow | null>(null);

  const load = () => {
    const q = new URLSearchParams();
    if (status) q.set("status", status);
    if (channel) q.set("channel", channel);
    api.get<InboxList>("/inbox?" + q.toString()).then(setD);
  };
  useEffect(load, [status, channel]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const cards = [
    { label: "Javob kutmoqda", value: d.open, tone: d.open ? "amber" : "emerald" },
    { label: "Kechikkan", value: d.overdue, tone: d.overdue ? "red" : "emerald" },
    {
      label: "SLA bajarildi",
      value: d.answered ? d.sla_percent + "%" : "—",
      tone: !d.answered ? "slate"
        : d.sla_percent >= 80 ? "emerald"
        : d.sla_percent >= 50 ? "amber" : "red",
    },
    { label: "O'rtacha javob", value: d.avg_minutes ? d.avg_minutes + " daq" : "—", tone: "slate" },
    { label: "Ish vaqtidan tashqari", value: d.off_hours, tone: "violet" },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
        {cards.map((c) => (
          <div key={c.label} className="bg-white border border-slate-200 rounded-xl p-3">
            <p className="text-xs text-slate-500 mb-1">{c.label}</p>
            <p className={`text-xl font-semibold ${
              c.tone === "red" ? "text-red-600"
              : c.tone === "amber" ? "text-amber-600"
              : c.tone === "emerald" ? "text-emerald-600"
              : c.tone === "violet" ? "text-violet-600" : "text-slate-900"
            }`}>{c.value}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button
          onClick={() => setStatus("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
            !status ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600"
          }`}
        >
          Hammasi
        </button>
        {d.statuses.filter((s) => s.count > 0).map((s) => (
          <button
            key={s.key}
            onClick={() => setStatus(s.key === status ? "" : s.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              status === s.key ? "bg-slate-800 text-white" : TONE[s.tone] || TONE.slate
            }`}
          >
            {s.label} {s.count}
          </button>
        ))}
        <select
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          className="ml-auto border border-slate-200 rounded-lg px-2 py-1.5 text-xs"
        >
          <option value="">Barcha kanallar</option>
          {d.channels.map((c) => (
            <option key={c.key} value={c.key}>{c.label}</option>
          ))}
        </select>
      </div>

      <p className="text-xs text-slate-500 mb-3 flex items-center gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0" />
        {d.hint}
      </p>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Murojaat yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((m) => (
            <button
              key={m.id}
              onClick={() => setOpen(m)}
              className={`w-full text-left bg-white border rounded-xl p-3.5 hover:border-slate-300 transition ${
                m.overdue ? "border-red-200 bg-red-50/40" : "border-slate-200"
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${TONE[m.channel_tone] || TONE.slate}`}>
                      {m.channel_label}
                    </span>
                    <span className="text-xs text-slate-400">{m.kind_label}</span>
                    <span className="text-sm font-medium text-slate-900">
                      {m.author}
                    </span>
                    {m.username && (
                      <span className="text-xs text-slate-400">{m.username}</span>
                    )}
                    {m.off_hours && (
                      <span className="text-[10px] text-violet-600">tunda keldi</span>
                    )}
                  </div>
                  <p className="text-sm text-slate-600 line-clamp-2">
                    {m.text || "—"}
                  </p>
                  {m.content && (
                    <p className="text-xs text-slate-400 mt-1 truncate">
                      Kontent: {m.content_code} {m.content}
                    </p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${TONE[m.status_tone] || TONE.slate}`}>
                    {m.status_label}
                  </span>
                  <p className={`text-xs mt-1.5 ${
                    m.sla_tone === "red" ? "text-red-600"
                    : m.sla_tone === "amber" ? "text-amber-600"
                    : m.sla_tone === "emerald" ? "text-emerald-600" : "text-slate-400"
                  }`}>
                    {m.sla_label}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {open && (
        <MessageDrawer
          row={open}
          templates={d.templates}
          statuses={d.statuses}
          onClose={() => setOpen(null)}
          onDone={() => { setOpen(null); load(); }}
        />
      )}
    </div>
  );
}

function MessageDrawer({
  row, templates, statuses, onClose, onDone,
}: {
  row: InboxRow;
  templates: { id: number; key: string; label: string; text: string }[];
  statuses: { key: string; label: string; tone: string; count: number }[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [text, setText] = useState(row.reply_text || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [leadOpen, setLeadOpen] = useState(false);
  const [phone, setPhone] = useState(row.phone || "");
  const [course, setCourse] = useState(row.course || "");

  const reply = async () => {
    if (!text.trim()) return;
    setBusy(true); setErr("");
    try {
      await api.post(`/inbox/${row.id}/reply`, { text: text.trim() });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  const setStatus = async (s: string) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/inbox/${row.id}/status`, { status: s });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  const makeLead = async () => {
    setBusy(true); setErr("");
    try {
      await api.post(`/inbox/${row.id}/lead`, {
        phone: phone.trim() || undefined,
        course: course.trim() || undefined,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex justify-end" onClick={onClose}>
      <div
        className="bg-white w-full max-w-md h-full overflow-y-auto p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${TONE[row.channel_tone] || TONE.slate}`}>
                {row.channel_label}
              </span>
              <span className="text-xs text-slate-400">{row.kind_label}</span>
            </div>
            <h3 className="text-base font-semibold text-slate-900">{row.author}</h3>
            {row.username && (
              <p className="text-xs text-slate-400">{row.username}</p>
            )}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="bg-slate-50 rounded-xl p-3 mb-4">
          <p className="text-sm text-slate-700 whitespace-pre-wrap">{row.text || "—"}</p>
          <p className="text-xs text-slate-400 mt-2">
            {row.received_at ? formatDate(row.received_at) : ""}
            {row.waiting_minutes != null && ` · ${row.waiting_minutes} daqiqa kutmoqda`}
            {row.reply_minutes != null && ` · ${row.reply_minutes} daqiqada javob berildi`}
          </p>
        </div>

        {row.content && (
          <p className="text-xs text-slate-500 mb-4">
            Bu murojaat <b>{row.content}</b> kontentidan keldi.
          </p>
        )}

        {row.reply_text && (
          <div className="border-l-2 border-emerald-300 pl-3 mb-4">
            <p className="text-xs text-emerald-700 mb-0.5">
              {row.replied_by} javob berdi
            </p>
            <p className="text-sm text-slate-600">{row.reply_text}</p>
          </div>
        )}

        <p className="text-xs font-medium text-slate-600 mb-1.5">Tayyor javoblar</p>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => setText(t.text)}
              className="px-2 py-1 rounded-lg bg-slate-100 text-slate-600 text-[11px] hover:bg-slate-200"
            >
              {t.label}
            </button>
          ))}
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          placeholder="Javob matni…"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2"
        />
        <button
          onClick={reply}
          disabled={busy || !text.trim()}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40 mb-4"
        >
          Javobni yozib qo'yish
        </button>

        {!row.lead_id ? (
          leadOpen ? (
            <div className="border border-slate-200 rounded-xl p-3 mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">Leadga aylantirish</p>
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Telefon"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2"
              />
              <input
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                placeholder="Yo'nalish"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2"
              />
              <button
                onClick={makeLead}
                disabled={busy}
                className="w-full bg-emerald-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
              >
                Lead yaratish
              </button>
            </div>
          ) : (
            <button
              onClick={() => setLeadOpen(true)}
              className="w-full border border-emerald-300 text-emerald-700 rounded-lg py-2 text-sm font-medium mb-4"
            >
              Leadga aylantirish
            </button>
          )
        ) : (
          <p className="text-sm text-emerald-700 mb-4">
            Lead yaratilgan (#{row.lead_id}).
          </p>
        )}

        <p className="text-xs font-medium text-slate-600 mb-1.5">Holatni o'zgartirish</p>
        <div className="flex flex-wrap gap-1.5">
          {statuses.filter((s) => s.key !== row.status).map((s) => (
            <button
              key={s.key}
              onClick={() => setStatus(s.key)}
              disabled={busy}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium ${TONE[s.tone] || TONE.slate}`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {err && <p className="text-sm text-red-600 mt-3">{err}</p>}
      </div>
    </div>
  );
}

// ============================================================ Natija
function AttributionTab() {
  const [d, setD] = useState<AttributionReport | null>(null);
  const [camps, setCamps] = useState<CampaignRow[] | null>(null);
  const [months, setMonths] = useState(3);
  const [open, setOpen] = useState<number | null>(null);
  const [view, setView] = useState<"content" | "campaign">("content");

  useEffect(() => {
    api.get<AttributionReport>(`/smm/attribution?months=${months}`).then(setD);
  }, [months]);
  useEffect(() => {
    api.get<{ rows: CampaignRow[] }>("/campaigns")
      .then((r) => setCamps(r.rows)).catch(() => setCamps([]));
  }, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const t = d.total;
  const cards = [
    { label: "Qamrov", value: t.reach.toLocaleString("ru-RU") },
    { label: "Murojaat", value: t.messages },
    { label: "Lead", value: t.leads },
    { label: "Sotuv", value: t.sales },
    { label: "Tushum", value: (t.revenue / 1000).toLocaleString("ru-RU") + " ming" },
  ];

  return (
    <div>
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {(["content", "campaign"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              view === v ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            {v === "content" ? "Kontent kesimi" : "Kampaniyalar"}
          </button>
        ))}
        <select
          value={months}
          onChange={(e) => setMonths(Number(e.target.value))}
          className="ml-auto border border-slate-200 rounded-lg px-2 py-1.5 text-xs"
        >
          {[1, 3, 6, 12].map((m) => (
            <option key={m} value={m}>Oxirgi {m} oy</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
        {cards.map((c) => (
          <div key={c.label} className="bg-white border border-slate-200 rounded-xl p-3">
            <p className="text-xs text-slate-500 mb-1">{c.label}</p>
            <p className="text-xl font-semibold text-slate-900">{c.value}</p>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-500 mb-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {view === "content" ? (
        <>
          <Funnel steps={t.funnel} />

          {d.by_pillar.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-4 mb-5">
              <p className="text-sm font-medium text-slate-700 mb-3">
                Yo'nalishlar bo'yicha
              </p>
              <div className="space-y-2">
                {d.by_pillar.map((p) => (
                  <div key={p.label} className="flex items-center gap-3 text-sm">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${TONE[p.tone] || TONE.slate}`}>
                      {p.label}
                    </span>
                    <span className="text-xs text-slate-400">{p.count} ta</span>
                    <span className="ml-auto text-xs text-slate-500">
                      {p.leads} lead · {p.sales} sotuv
                    </span>
                    <span className="text-sm font-medium text-slate-900 w-28 text-right">
                      {p.revenue.toLocaleString("ru-RU")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium">Kontent</th>
                  <th className="text-right px-3 py-2.5 font-medium">Qamrov</th>
                  <th className="text-right px-3 py-2.5 font-medium">Murojaat</th>
                  <th className="text-right px-3 py-2.5 font-medium">Lead</th>
                  <th className="text-right px-3 py-2.5 font-medium">Sotuv</th>
                  <th className="text-right px-4 py-2.5 font-medium">Tushum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {d.rows.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => setOpen(r.id)}
                    className="hover:bg-slate-50 cursor-pointer"
                  >
                    <td className="px-4 py-2.5">
                      <p className="font-medium text-slate-900 truncate max-w-xs">
                        {r.title}
                      </p>
                      <p className="text-xs text-slate-400">
                        {r.code} · {r.platform_label}
                        {r.date ? " · " + formatDate(r.date) : ""}
                      </p>
                    </td>
                    <td className="text-right px-3 py-2.5 text-slate-600">
                      {r.reach.toLocaleString("ru-RU")}
                    </td>
                    <td className="text-right px-3 py-2.5 text-slate-600">{r.messages}</td>
                    <td className="text-right px-3 py-2.5 text-slate-600">{r.leads}</td>
                    <td className="text-right px-3 py-2.5 text-slate-600">{r.sales}</td>
                    <td className="text-right px-4 py-2.5 font-medium text-slate-900">
                      {r.revenue.toLocaleString("ru-RU")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {d.rows.length === 0 && (
              <p className="text-sm text-slate-400 py-10 text-center">
                Joylangan kontent yo'q.
              </p>
            )}
          </div>
        </>
      ) : (
        <div className="space-y-3">
          {(camps || []).map((c) => (
            <div key={c.id} className="bg-white border border-slate-200 rounded-xl p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-medium text-slate-900">{c.name}</p>
                  <p className="text-xs text-slate-400">
                    {c.goal_label}
                    {c.course ? " · " + c.course : ""}
                    {c.start_date ? " · " + formatDate(c.start_date) : ""}
                    {" · "}{c.contents} ta kontent
                  </p>
                </div>
                {c.lead_plan_percent != null && (
                  <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                    c.lead_plan_percent >= 80 ? TONE.emerald
                    : c.lead_plan_percent >= 50 ? TONE.amber : TONE.red
                  }`}>
                    Reja {c.lead_plan_percent}%
                  </span>
                )}
              </div>
              <Funnel steps={c.funnel} compact />
            </div>
          ))}
          {camps && camps.length === 0 && (
            <p className="text-sm text-slate-400 py-10 text-center">
              Kampaniya yo'q.
            </p>
          )}
        </div>
      )}

      {open != null && (
        <AttributionDrawer id={open} onClose={() => setOpen(null)} />
      )}
    </div>
  );
}

function Funnel({ steps, compact }: { steps: FunnelStep[]; compact?: boolean }) {
  const top = Math.max(...steps.map((s) => s.value), 1);
  return (
    <div className={`bg-white border border-slate-200 rounded-xl ${compact ? "p-0 border-0" : "p-4 mb-5"}`}>
      {!compact && (
        <p className="text-sm font-medium text-slate-700 mb-3">
          Qamrovdan sotuvgacha
        </p>
      )}
      <div className="space-y-1.5">
        {steps.map((s) => (
          <div key={s.key} className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0 text-slate-500">{s.label}</span>
            <div className="flex-1 bg-slate-100 rounded h-5 relative overflow-hidden">
              <div
                className="bg-brand-500/70 h-full rounded"
                style={{ width: Math.max((s.value / top) * 100, s.value ? 2 : 0) + "%" }}
              />
              <span className="absolute left-2 top-0 leading-5 text-[11px] font-medium text-slate-700">
                {s.value.toLocaleString("ru-RU")}
              </span>
            </div>
            <span className="w-12 text-right text-slate-400">
              {s.from_prev != null ? s.from_prev + "%" : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AttributionDrawer({ id, onClose }: { id: number; onClose: () => void }) {
  const [d, setD] = useState<Attribution | null>(null);
  useEffect(() => {
    api.get<Attribution>(`/content/${id}/attribution`).then(setD);
  }, [id]);

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex justify-end" onClick={onClose}>
      <div
        className="bg-white w-full max-w-md h-full overflow-y-auto p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-base font-semibold text-slate-900 pr-4">
            {d ? d.content.title : "Yuklanmoqda…"}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {d && (
          <>
            <p className="text-sm text-slate-600 bg-slate-50 rounded-xl p-3 mb-4">
              {d.story}
            </p>

            <div className="grid grid-cols-2 gap-2 mb-4">
              {[
                ["Maqsad", d.goal_label],
                ["Asosiy o'lchov", d.goal_metric],
                ["Qamrov", d.reach.toLocaleString("ru-RU")],
                ["Sifatli engagement", d.engagement.toLocaleString("ru-RU")],
                ["Profil ochilishi", d.profile_visits.toLocaleString("ru-RU")],
                ["Havola bosilishi", d.link_clicks.toLocaleString("ru-RU")],
                ["Murojaat → lead", d.lead_rate + "%"],
                ["Lead → sotuv", d.sale_rate + "%"],
                ["Birinchi to'lov", d.first_revenue.toLocaleString("ru-RU")],
                ["Umumiy tushum", d.revenue.toLocaleString("ru-RU")],
                ["30 kun qoldi", String(d.retained_30)],
                ["90 kun qoldi", String(d.retained_90)],
              ].map(([k, v]) => (
                <div key={k} className="bg-slate-50 rounded-lg p-2.5">
                  <p className="text-[11px] text-slate-500">{k}</p>
                  <p className="text-sm font-medium text-slate-900">{v}</p>
                </div>
              ))}
            </div>

            <Funnel steps={d.funnel} />

            <p className="text-xs text-slate-500 flex items-start gap-1.5">
              <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
              {d.hint}
            </p>
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================ Brend kitob
function BrandTab() {
  const [d, setD] = useState<BrandBook | null>(null);
  const [edit, setEdit] = useState<BrandRow | null>(null);
  const [copied, setCopied] = useState("");

  const load = () => { api.get<BrandBook>("/brand").then(setD); };
  useEffect(load, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const copy = (v: string) => {
    navigator.clipboard?.writeText(v);
    setCopied(v);
    setTimeout(() => setCopied(""), 1200);
  };

  const S = (k: string) => d.sections[k] || [];

  return (
    <div className="space-y-5">
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <div className="flex items-start gap-4 flex-wrap">
          <div className="flex-1 min-w-[220px]">
            <p className="text-xs text-slate-500 mb-1">Brend so'zi</p>
            <p className="text-2xl font-semibold text-slate-900 mb-1">
              {d.word}
            </p>
            <p className="text-sm text-slate-600">
              {S("word")[0]?.note?.replace("TO'LDIRILDI. ", "")}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400">Manba</p>
            <p className="text-sm text-slate-600">{d.source}</p>
          </div>
        </div>
      </div>

      {d.gaps.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-sm font-medium text-amber-900 mb-2">
            Brandbookda yo'q edi — to'ldirildi, tasdiqlashingiz kerak
          </p>
          <ul className="space-y-1">
            {d.gaps.map((g, i) => (
              <li key={i} className="text-sm text-amber-800 flex gap-2">
                <span className="text-amber-500">·</span>{g}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Ranglar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <p className="text-sm font-medium text-slate-700 mb-3">Ranglar</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {S("color").map((c) => (
            <button
              key={c.id}
              onClick={() => copy(c.value || "")}
              className="text-left border border-slate-200 rounded-lg overflow-hidden hover:border-slate-300"
            >
              <div className="h-14" style={{ background: c.value || "#fff" }} />
              <div className="p-2.5">
                <p className="text-sm font-medium text-slate-900">{c.title}</p>
                <p className="text-xs text-slate-500 font-mono">
                  {copied === c.value ? "nusxalandi" : c.value}
                </p>
                {c.is_filled && (
                  <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                    {c.source}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Postda faqat: {d.post_colors.join(" · ")}. Yashil, sariq va
          qizil — faqat tizim ichida holat ko'rsatish uchun.
        </p>
      </div>

      {/* Shrift */}
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <p className="text-sm font-medium text-slate-700 mb-3">Shriftlar</p>
        <div className="space-y-2">
          {S("font").map((f) => (
            <div key={f.id} className="flex items-start gap-3">
              <span className="text-sm font-medium text-slate-900 w-40 shrink-0">
                {f.title}
              </span>
              <span className="text-xs text-slate-500 flex-1">{f.note}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Logotip */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Logotip qoidalari
          </p>
          <div className="space-y-2.5">
            {S("logo").map((r) => (
              <div key={r.id}>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-800">
                    {r.title}
                  </p>
                  {r.is_filled && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                      {r.source}
                    </span>
                  )}
                  {d.can_edit && (
                    <button
                      onClick={() => setEdit(r)}
                      className="ml-auto text-xs text-brand-600 hover:underline"
                    >
                      tahrirlash
                    </button>
                  )}
                </div>
                <p className="text-xs text-slate-500">{r.note}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-red-200 rounded-xl p-4">
          <p className="text-sm font-medium text-red-700 mb-3">
            Logotip bilan shunday qilinmaydi
          </p>
          <ul className="space-y-1.5">
            {S("dont").map((r) => (
              <li key={r.id} className="text-sm text-slate-700 flex gap-2">
                <X size={14} className="text-red-500 shrink-0 mt-0.5" />
                {r.title}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Ovoz */}
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <p className="text-sm font-medium text-slate-700 mb-3">
          Qanday yoziladi
        </p>
        <div className="grid md:grid-cols-2 gap-x-6 gap-y-3">
          {S("tone").map((r) => (
            <div key={r.id} className="flex gap-2.5">
              <span
                className={`shrink-0 mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
                  r.kind === "dont"
                    ? "bg-red-100 text-red-600"
                    : "bg-emerald-100 text-emerald-600"
                }`}
              >
                {r.kind === "dont" ? "—" : "+"}
              </span>
              <div>
                <p className="text-sm font-medium text-slate-800">{r.title}</p>
                <p className="text-xs text-slate-500">{r.note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* O'lchamlar va aloqa */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Ijtimoiy tarmoq o'lchamlari
          </p>
          <div className="space-y-2">
            {S("spec").map((r) => (
              <div key={r.id}>
                <div className="flex justify-between gap-3">
                  <span className="text-sm text-slate-800">{r.title}</span>
                  <span className="text-sm font-mono text-slate-600">
                    {r.value}
                  </span>
                </div>
                <p className="text-xs text-slate-500">{r.note}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Rasmiy rekvizitlar
          </p>
          <div className="space-y-2">
            {S("contact").map((r) => (
              <div key={r.id}>
                <div className="flex justify-between gap-3">
                  <span className="text-sm text-slate-500">{r.title}</span>
                  <span className="text-sm text-slate-900">{r.value}</span>
                </div>
                {r.note && (
                  <p className="text-xs text-amber-700 mt-0.5">{r.note}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {edit && (
        <BrandEdit row={edit} onClose={() => setEdit(null)}
                   onDone={() => { setEdit(null); load(); }} />
      )}
    </div>
  );
}

function BrandEdit({ row, onClose, onDone }: {
  row: BrandRow; onClose: () => void; onDone: () => void;
}) {
  const [title, setTitle] = useState(row.title);
  const [value, setValue] = useState(row.value || "");
  const [note, setNote] = useState(row.note || "");
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await api.put(`/brand/${row.id}`, { title, value: value || null, note });
      onDone();
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <div className="bg-white rounded-xl p-5 w-full max-w-md"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Qoidani tahrirlash</h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <input value={title} onChange={(e) => setTitle(e.target.value)}
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2" />
        <input value={value} onChange={(e) => setValue(e.target.value)}
               placeholder="Qiymat (ixtiyoriy)"
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2" />
        <textarea value={note} onChange={(e) => setNote(e.target.value)}
                  rows={3} placeholder="Izoh"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3" />
        <p className="text-xs text-slate-500 mb-3">
          Saqlangach bu qoida "Tasdiqlangan" deb belgilanadi.
        </p>
        <button onClick={save} disabled={busy}
                className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
          Saqlash
        </button>
      </div>
    </div>
  );
}

// ============================================================ Media
function MediaTab() {
  const [d, setD] = useState<MediaList | null>(null);
  const [consent, setConsent] = useState("");
  const [q, setQ] = useState("");
  const [adding, setAdding] = useState(false);

  const load = () => {
    const p = new URLSearchParams();
    if (consent) p.set("consent", consent);
    if (q) p.set("q", q);
    api.get<MediaList>("/media?" + p.toString()).then(setD);
  };
  useEffect(load, [consent, q]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {[
          { l: "Jami", v: d.total, t: "slate" },
          { l: "Joylash mumkin", v: d.publishable, t: "emerald" },
          { l: "Muddati tugayapti", v: d.expiring, t: "amber" },
          { l: "Muddati tugagan", v: d.expired, t: "red" },
        ].map((c) => (
          <div key={c.l} className="bg-white border border-slate-200 rounded-xl p-3">
            <p className="text-xs text-slate-500 mb-1">{c.l}</p>
            <p className={`text-xl font-semibold ${
              c.t === "emerald" ? "text-emerald-600"
              : c.t === "amber" ? "text-amber-600"
              : c.t === "red" ? "text-red-600" : "text-slate-900"
            }`}>{c.v}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button onClick={() => setConsent("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
            !consent ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600"}`}>
          Hammasi
        </button>
        {d.consents.map((c) => (
          <button key={c.key}
            onClick={() => setConsent(c.key === consent ? "" : c.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              consent === c.key ? "bg-slate-800 text-white"
              : TONE[c.tone] || TONE.slate}`}>
            {c.label} {c.count}
          </button>
        ))}
        <input value={q} onChange={(e) => setQ(e.target.value)}
               placeholder="Qidirish…"
               className="ml-auto border border-slate-200 rounded-lg px-3 py-1.5 text-xs w-44" />
        <button onClick={() => setAdding(true)}
          className="bg-brand-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium flex items-center gap-1">
          <Plus size={14} /> Qo'shish
        </button>
      </div>

      <p className="text-xs text-slate-500 mb-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
        {d.rows.map((m) => (
          <div key={m.id}
            className={`bg-white border rounded-xl p-3.5 ${
              m.can_publish ? "border-slate-200" : "border-red-200 bg-red-50/30"}`}>
            <div className="flex items-start gap-2 mb-2">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                TONE[m.kind_tone] || TONE.slate}`}>
                {m.kind_label}
              </span>
              <span className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-medium ${
                TONE[m.consent_tone] || TONE.slate}`}>
                {m.consent_label}
              </span>
            </div>
            <p className="text-sm font-medium text-slate-900 mb-1">{m.name}</p>
            <p className="text-xs text-slate-500">
              {[m.event, m.branch, m.taken_on ? formatDate(m.taken_on) : null]
                .filter(Boolean).join(" · ") || "—"}
            </p>
            {m.days_left != null && (
              <p className={`text-xs mt-1.5 ${
                m.expired ? "text-red-600"
                : m.expiring ? "text-amber-600" : "text-slate-400"}`}>
                {m.expired
                  ? "Rozilik muddati tugagan"
                  : `Rozilik ${m.days_left} kundan keyin tugaydi`}
              </p>
            )}
            {!m.can_publish && (
              <p className="text-xs text-red-600 mt-1.5">
                Ijtimoiy tarmoqqa joylash mumkin emas
              </p>
            )}
          </div>
        ))}
      </div>
      {d.rows.length === 0 && (
        <p className="text-sm text-slate-400 py-10 text-center">
          Material yo'q.
        </p>
      )}

      {adding && (
        <MediaAdd kinds={d.kinds} consents={d.consents}
                  onClose={() => setAdding(false)}
                  onDone={() => { setAdding(false); load(); }} />
      )}
    </div>
  );
}

function MediaAdd({ kinds, consents, onClose, onDone }: {
  kinds: { key: string; label: string }[];
  consents: { key: string; label: string }[];
  onClose: () => void; onDone: () => void;
}) {
  const [f, setF] = useState({
    name: "", kind: "photo", event: "", url: "",
    consent: "pending", consent_until: "", taken_on: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    if (!f.name.trim()) return;
    setBusy(true); setErr("");
    try {
      await api.post("/media", {
        ...f,
        consent_until: f.consent_until || null,
        taken_on: f.taken_on || null,
        url: f.url || null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <div className="bg-white rounded-xl p-5 w-full max-w-md"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Material qo'shish</h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })}
               placeholder="Nomi"
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2" />
        <div className="grid grid-cols-2 gap-2 mb-2">
          <select value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}
                  className="border border-slate-200 rounded-lg px-2 py-2 text-sm">
            {kinds.map((k) => <option key={k.key} value={k.key}>{k.label}</option>)}
          </select>
          <input type="date" value={f.taken_on}
                 onChange={(e) => setF({ ...f, taken_on: e.target.value })}
                 className="border border-slate-200 rounded-lg px-2 py-2 text-sm" />
        </div>
        <input value={f.event} onChange={(e) => setF({ ...f, event: e.target.value })}
               placeholder="Tadbir yoki joy"
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2" />
        <input value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })}
               placeholder="Havola (Drive, Dropbox…)"
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3" />

        <p className="text-xs font-medium text-slate-600 mb-1.5">Rozilik</p>
        <select value={f.consent}
                onChange={(e) => setF({ ...f, consent: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-2 py-2 text-sm mb-2">
          {consents.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
        </select>
        <input type="date" value={f.consent_until}
               onChange={(e) => setF({ ...f, consent_until: e.target.value })}
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2" />
        <p className="text-xs text-slate-500 mb-3">
          Muddat tugagach material avtomat "taqiqlangan"ga o'tadi.
        </p>

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button onClick={save} disabled={busy || !f.name.trim()}
                className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
          Saqlash
        </button>
      </div>
    </div>
  );
}

// ============================================================ Bilimlar bazasi
function KbTab() {
  const [d, setD] = useState<KbList | null>(null);
  const [cat, setCat] = useState("");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<KbRow | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    const p = new URLSearchParams();
    if (cat) p.set("category", cat);
    if (q) p.set("q", q);
    api.get<KbList>("/kb?" + p.toString()).then(setD);
  };
  useEffect(load, [cat, q]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button onClick={() => setCat("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
            !cat ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600"}`}>
          Hammasi
        </button>
        {d.categories.map((c) => (
          <button key={c.key} onClick={() => setCat(c.key === cat ? "" : c.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              cat === c.key ? "bg-slate-800 text-white"
              : TONE[c.tone] || TONE.slate}`}>
            {c.label} {c.count}
          </button>
        ))}
        <input value={q} onChange={(e) => setQ(e.target.value)}
               placeholder="Qidirish…"
               className="ml-auto border border-slate-200 rounded-lg px-3 py-1.5 text-xs w-44" />
        {d.can_edit && (
          <button onClick={() => setAdding(true)}
            className="bg-brand-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium flex items-center gap-1">
            <Plus size={14} /> Maqola
          </button>
        )}
      </div>

      {d.stale > 0 && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
          {d.stale} ta maqola {d.review_months} oydan beri yangilanmagan —
          eskirgan reglament eskirgan ish demakdir.
        </p>
      )}

      <div className="space-y-2">
        {d.rows.map((a) => (
          <button key={a.id} onClick={() => setOpen(a)}
            className="w-full text-left bg-white border border-slate-200 rounded-xl p-3.5 hover:border-slate-300">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                TONE[a.category_tone] || TONE.slate}`}>
                {a.category_label}
              </span>
              <span className="text-sm font-medium text-slate-900">{a.title}</span>
              {a.stale && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                  eskirgan
                </span>
              )}
              <span className="ml-auto text-xs text-slate-400">
                {a.views} marta o'qilgan
              </span>
            </div>
            <p className="text-xs text-slate-500 line-clamp-2">
              {(a.body || "").slice(0, 160)}
            </p>
          </button>
        ))}
      </div>
      {d.rows.length === 0 && (
        <p className="text-sm text-slate-400 py-10 text-center">Maqola yo'q.</p>
      )}

      {open && (
        <div className="fixed inset-0 bg-black/30 z-50 flex justify-end"
             onClick={() => setOpen(null)}>
          <div className="bg-white w-full max-w-lg h-full overflow-y-auto p-5"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  TONE[open.category_tone] || TONE.slate}`}>
                  {open.category_label}
                </span>
                <h3 className="text-lg font-semibold text-slate-900 mt-1.5">
                  {open.title}
                </h3>
              </div>
              <button onClick={() => setOpen(null)} className="text-slate-400">
                <X size={18} />
              </button>
            </div>
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
              {open.body}
            </p>
            <p className="text-xs text-slate-400 mt-5">
              {open.author ? open.author + " · " : ""}
              {open.reviewed_at
                ? "oxirgi ko'rilgan " + formatDate(open.reviewed_at) : ""}
            </p>
          </div>
        </div>
      )}

      {adding && (
        <KbAdd categories={d.categories} onClose={() => setAdding(false)}
               onDone={() => { setAdding(false); load(); }} />
      )}
    </div>
  );
}

function KbAdd({ categories, onClose, onDone }: {
  categories: { key: string; label: string }[];
  onClose: () => void; onDone: () => void;
}) {
  const [f, setF] = useState({ title: "", category: "process", body: "" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    if (!f.title.trim()) return;
    setBusy(true);
    try { await api.post("/kb", f); onDone(); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <div className="bg-white rounded-xl p-5 w-full max-w-lg"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Yangi maqola</h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })}
               placeholder="Sarlavha"
               className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2" />
        <select value={f.category}
                onChange={(e) => setF({ ...f, category: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-2 py-2 text-sm mb-2">
          {categories.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
        </select>
        <textarea value={f.body} onChange={(e) => setF({ ...f, body: e.target.value })}
                  rows={10} placeholder="Matn…"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3" />
        <button onClick={save} disabled={busy || !f.title.trim()}
                className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
          Saqlash
        </button>
      </div>
    </div>
  );
}

// ============================================================ Hisobot
function ReportTab() {
  const [dim, setDim] = useState("platform");
  const [a, setA] = useState<SmmAnalytics | null>(null);
  const [k, setK] = useState<SmmKpi | null>(null);
  const [r, setR] = useState<SmmReport | null>(null);
  const [period, setPeriod] = useState("month");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api.get<SmmAnalytics>(`/smm/analytics?dim=${dim}&months=3`).then(setA);
  }, [dim]);
  useEffect(() => { api.get<SmmKpi>("/smm/kpi?months=1").then(setK); }, []);
  useEffect(() => {
    api.get<SmmReport>(`/smm/report?period=${period}`).then(setR);
  }, [period]);

  const save = async () => {
    setBusy(true);
    try {
      await api.post("/smm/report", { period });
      setSaved("Hisobot saqlandi — raqamlar muzlatildi.");
      setTimeout(() => setSaved(""), 3000);
    } finally { setBusy(false); }
  };

  return (
    <div className="space-y-5">
      {/* KPI */}
      {k && (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            <p className="text-sm font-medium text-slate-700">SMM KPI</p>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              TONE[k.tone] || TONE.slate}`}>
              {k.score} ball · {k.label}
            </span>
            <span className="ml-auto text-xs text-slate-400">
              {k.published} kontent · reja {k.plan_percent}%
            </span>
          </div>
          <div className="space-y-2">
            {k.parts.map((p) => (
              <div key={p.key} className="flex items-center gap-3">
                <span className="text-xs text-slate-600 w-44 shrink-0">
                  {p.label}
                </span>
                <div className="flex-1 bg-slate-100 rounded h-4 overflow-hidden">
                  <div className={`h-full rounded ${
                    p.percent >= 80 ? "bg-emerald-400"
                    : p.percent >= 50 ? "bg-amber-400" : "bg-red-400"}`}
                    style={{ width: Math.max(p.percent, 2) + "%" }} />
                </div>
                <span className="text-xs text-slate-500 w-16 text-right">
                  {p.score}/{p.max}
                </span>
                <span className="text-xs text-slate-400 w-56 truncate hidden lg:block">
                  {p.note}
                </span>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
            <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
            {k.hint}
          </p>
        </div>
      )}

      {/* Kesimlar */}
      {a && (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <p className="text-sm font-medium text-slate-700">Kesimlar</p>
            <select value={dim} onChange={(e) => setDim(e.target.value)}
                    className="ml-auto border border-slate-200 rounded-lg px-2 py-1.5 text-xs">
              {a.dims.map((x) => (
                <option key={x.key} value={x.key}>{x.label}</option>
              ))}
            </select>
          </div>

          {a.trap && (
            <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
              <b>{a.trap.label}</b> eng ko'p ko'rilgan
              ({a.trap.reach.toLocaleString("ru-RU")} qamrov), lekin
              {a.trap.revenue ? "" : " undan bironta sotuv chiqmagan"}.
              Pul <b>{a.trap.better}</b> orqali kelyapti.
            </p>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-slate-500 text-xs">
                <tr>
                  <th className="text-left py-2 font-medium">{a.dim_label}</th>
                  <th className="text-right py-2 px-2 font-medium">Soni</th>
                  <th className="text-right py-2 px-2 font-medium">Qamrov</th>
                  <th className="text-right py-2 px-2 font-medium">Lead</th>
                  <th className="text-right py-2 px-2 font-medium">Sotuv</th>
                  <th className="text-right py-2 font-medium">Tushum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {a.rows.map((row, i) => (
                  <tr key={i}>
                    <td className="py-2 text-slate-900">{row.label}</td>
                    <td className="text-right px-2 text-slate-600">{row.count}</td>
                    <td className="text-right px-2 text-slate-600">
                      {row.reach.toLocaleString("ru-RU")}
                    </td>
                    <td className="text-right px-2 text-slate-600">{row.leads}</td>
                    <td className="text-right px-2 text-slate-600">{row.sales}</td>
                    <td className="text-right font-medium text-slate-900">
                      {row.revenue.toLocaleString("ru-RU")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {a.rows.length === 0 && (
            <p className="text-sm text-slate-400 py-6 text-center">
              Joylangan kontent yo'q.
            </p>
          )}
          <p className="text-xs text-slate-500 mt-3">{a.hint}</p>
        </div>
      )}

      {/* Hisobot */}
      {r && (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <p className="text-sm font-medium text-slate-700">Hisobot</p>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}
                    className="border border-slate-200 rounded-lg px-2 py-1.5 text-xs">
              {(r.periods || []).map((p) => (
                <option key={p.key} value={p.key}>{p.label}</option>
              ))}
            </select>
            <span className="text-xs text-slate-400">
              {formatDate(r.start)} — {formatDate(r.end)}
            </span>
            <button onClick={save} disabled={busy}
              className="ml-auto bg-brand-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-40">
              Saqlash
            </button>
          </div>

          {saved && (
            <p className="text-sm text-emerald-700 mb-3">{saved}</p>
          )}

          <p className="text-sm text-slate-700 bg-slate-50 rounded-lg p-3 whitespace-pre-line mb-4">
            {r.summary}
          </p>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-medium text-slate-600 mb-2">
                Eng ko'p pul olib kelganlar
              </p>
              {r.top.length ? r.top.map((t) => (
                <div key={t.id} className="flex justify-between gap-3 py-1 text-sm">
                  <span className="text-slate-700 truncate">{t.title}</span>
                  <span className="text-slate-900 font-medium shrink-0">
                    {t.revenue.toLocaleString("ru-RU")}
                  </span>
                </div>
              )) : <p className="text-sm text-slate-400">—</p>}
            </div>
            <div>
              <p className="text-xs font-medium text-slate-600 mb-2">
                Ko'rildi, lekin natija bermadi
              </p>
              {r.weak.length ? r.weak.map((t) => (
                <div key={t.id} className="flex justify-between gap-3 py-1 text-sm">
                  <span className="text-slate-700 truncate">{t.title}</span>
                  <span className="text-slate-400 shrink-0">
                    {t.reach.toLocaleString("ru-RU")}
                  </span>
                </div>
              )) : <p className="text-sm text-slate-400">—</p>}
            </div>
          </div>

          {r.tips.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <p className="text-xs font-medium text-slate-600 mb-2">
                Keyingi davr uchun
              </p>
              {r.tips.map((t, i) => (
                <p key={i} className="text-sm text-slate-700 mb-1.5">
                  <b>{t.about}.</b> {t.text}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
