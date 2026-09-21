import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { BookOpen, Gamepad2, ArrowLeft, ChevronDown, ChevronUp, ChevronRight, Headphones, FileText, Download } from "lucide-react";
import { api, getToken } from "../lib/api";
import brandIconSrc from "../assets/brand-icon.png";

/**
 * DARS REJALARI (2026-09-18, Jahongir: "saytgayam qoy ... kahoot
 * korinishidagi oyinlar ham qosh ... har bir unitda").
 *
 * Ustoz uchun tayyorlangan IELTS 1.0 rejalari (28 dars): grammatika,
 * 20/40/60 lug'at, mashqlar, reading, listening, uyga vazifa. Har
 * darsdan "Jonli o'yin" ochiladi — PIN/QR bilan Kahoot uslubida.
 */

type Summary = { no: number; title: string; grammar_topic: string; vocab_topic: string;
  test_after: string; audios: string; reading: boolean; words: number; ready: boolean; writing?: string };
type Level = { course: string; title: string; cefr: string; ready: boolean;
  ready_count: number; lessons: Summary[] };
type LiveGroup = { id: number; name: string; students: { id: number; name: string }[] };

type Ex = { title: string; type?: string; instr?: string; items?: string[];
  answers?: string[] | string; note?: string; box?: string[]; why?: string[];
  layout?: "grid" | "pairs" | "flow" | "mcq" | "tfng" | "match" | "qa" | "list";
  head?: string[]; rows?: string[][] };
/** IELTS 5.0 (Introduction): bitta darsda bir nechta reading/listening,
 * har birida savol turi, paraphrase ro'yxati, javob izohi va transkript
 * (2026-09-20, Jahongir so'rovi). */
type Reading = { title: string; qtype?: string; source?: string; book_ref?: string;
  image?: string; text?: string[]; paraphrases?: [string, string][]; glossary?: string[]; tasks?: Ex[] };
type Listen = { title: string; qtype?: string; audios?: string; audio?: string; image?: string; intro?: string[];
  transcript?: string[]; tasks?: Ex[] };
type Lesson = {
  no: number; title: string; grammar_topic: string; vocab_topic: string; duration: number;
  test_after?: string; book_ref?: string; objectives: string[]; materials: string[];
  timeline: [number, string, string][];
  grammar: { intro: string[]; formulas: string[][]; presentation: [string, string][];
    notes: string[]; mistakes: string[][] };
  vocab: { how: string[]; core: string[][]; strong: string[][]; super: string[][]; normativ: string[] };
  class_ex: Ex[];
  reading?: { book_ref?: string; title: string; text: string[]; glossary: string[]; tasks: Ex[] };
  listening?: { audios: string; intro: string[]; tasks: Ex[] };
  readings?: Reading[];
  listenings?: Listen[];
  homework_intro: string[]; homework: Ex[]; normativ: [string, string, string][];
};

const MODES = [
  { key: "mixed", label: "Aralash (grammatika + lug'at)" },
  { key: "vocab", label: "Lug'at — CORE 20" },
  { key: "vocab40", label: "Lug'at — 40 so'z" },
  { key: "grammar", label: "Grammatika" },
];

/** Daraja ro'yxati -> darslar ro'yxati -> dars (2026-09-18, Jahongir:
 * "alohida list korinishida IELTS 1.0 (A1) IELTS 2.0 (A2) ... keyin
 * kirganda list korinishida 1-dars - Shaping the mindset ..."). */
export default function LessonPlans() {
  const { course, no } = useParams();
  if (course && no) return <LessonView course={course} no={Number(no)} />;
  if (course) return <LessonList course={course} />;
  return <LevelList />;
}

function useLevels() {
  const [levels, setLevels] = useState<Level[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Level[]>("/plans").then(setLevels).catch((e) => setErr(e.message));
  }, []);
  return { levels, err };
}

function LevelList() {
  const { levels, err } = useLevels();
  return (
    <div className="p-6 md:p-8 max-w-3xl">
      <h1 className="text-xl font-semibold text-slate-900 mb-1 flex items-center gap-2">
        <BookOpen size={20} className="text-brand-600" /> Dars rejalari
      </h1>
      <p className="text-sm text-slate-500 mb-5">
        Darajani tanlang. Har mavzu — bitta 120 daqiqalik dars: grammatika, 20/40/60 lug'at,
        mashqlar, reading, listening, uyga vazifa va <b>jonli o'yin</b> (Kahoot uslubi).
      </p>
      {err && <div className="text-sm text-rose-600 mb-3">{err}</div>}
      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        {levels.map((lv) => (
          <Link key={lv.course} to={`/plans/${lv.course}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50">
            <div className="flex items-center gap-3">
              <span className="w-10 h-10 rounded-lg bg-brand-50 text-brand-700 font-bold flex items-center justify-center text-sm">{lv.cefr}</span>
              <div>
                <div className="font-semibold text-slate-900">{lv.title} <span className="text-slate-400 font-normal">({lv.cefr})</span></div>
                <div className="text-xs text-slate-500">
                  {lv.lessons.length ? `${lv.lessons.length} dars` : "Mavzular hali kiritilmagan"}
                  {lv.lessons.length > 0 && !lv.ready && (lv.ready_count > 0 ? ` · ${lv.ready_count}/${lv.lessons.length} tayyor` : " · reja tayyorlanmoqda")}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs">
              {lv.ready
                ? <span className="bg-emerald-50 text-emerald-700 rounded px-2 py-0.5">Tayyor</span>
                : lv.ready_count > 0
                  ? <span className="bg-amber-50 text-amber-700 rounded px-2 py-0.5">{lv.ready_count} dars tayyor</span>
                  : <span className="bg-slate-100 text-slate-500 rounded px-2 py-0.5">Tez orada</span>}
              <ChevronRight size={16} className="text-slate-400" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function LessonList({ course }: { course: string }) {
  const { levels, err } = useLevels();
  const lv = levels.find((l) => l.course === course);
  if (err) return <div className="p-8 text-rose-600">{err}</div>;
  if (!levels.length) return <div className="p-8 text-slate-500">Yuklanmoqda…</div>;
  if (!lv) return <div className="p-8 text-slate-500">Daraja topilmadi.</div>;
  return (
    <div className="p-6 md:p-8 max-w-3xl">
      <Link to="/plans" className="text-sm text-slate-500 hover:text-brand-600 flex items-center gap-1 mb-1">
        <ArrowLeft size={14} /> Darajalar
      </Link>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">{lv.title} <span className="text-slate-400 font-normal">({lv.cefr})</span></h1>
      <p className="text-sm text-slate-500 mb-4">
        {lv.lessons.length
          ? `${lv.lessons.length} dars` + (lv.ready ? "" : " · to'liq reja tayyorlanmoqda, hozircha mavzular ro'yxati")
          : "Bu daraja uchun mavzular hali kiritilmagan."}
      </p>
      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        {lv.lessons.map((l) => {
          const inner = (
            <>
              <div className="flex items-center gap-3 min-w-0">
                <span className="w-9 shrink-0 text-sm font-semibold text-slate-400">{l.no}</span>
                <div className="min-w-0">
                  {/* Faqat "N-dars" (2026-09-18, Jahongir: "mavzular bo'lsa
                      ko'payib ketarkan tushunarsiz") — mavzu dars ichida. */}
                  <div className={`font-medium ${l.ready ? "text-slate-900" : "text-slate-500"}`}>{l.no}-dars</div>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0 text-[11px]">
                {l.test_after && <span className="bg-amber-50 text-amber-700 rounded px-1.5 py-0.5">{l.test_after}</span>}
                {l.ready
                  ? <ChevronRight size={16} className="text-slate-400" />
                  : <span className="bg-slate-100 text-slate-500 rounded px-1.5 py-0.5">tayyorlanmoqda</span>}
              </div>
            </>
          );
          return l.ready ? (
            <Link key={l.no} to={`/plans/${course}/${l.no}`} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-slate-50">{inner}</Link>
          ) : (
            <div key={l.no} className="flex items-center justify-between gap-3 px-4 py-3">{inner}</div>
          );
        })}
      </div>
    </div>
  );
}

type Tab = "plan" | "grammar" | "vocab" | "class" | "reading" | "listening" | "home";

/** Dars qaysi bo'limlarga ega — shular ko'rinadi. Skill darslarida
 * (IELTS 5.0) grammatika/lug'at yo'q, o'rniga "Savol turi" turadi. */
function tabsFor(L: Lesson): { key: Tab; label: string }[] {
  const G = L.grammar ?? ({} as Lesson["grammar"]);
  const V = L.vocab ?? ({} as Lesson["vocab"]);
  const words = (V.core ?? []).length + (V.strong ?? []).length + (V.super ?? []).length;
  const skill = words === 0;
  const out: { key: Tab; label: string }[] = [{ key: "plan", label: "Reja" }];
  if ((G.intro ?? []).length || (G.formulas ?? []).length || (G.presentation ?? []).length) {
    out.push({ key: "grammar", label: skill ? "Savol turi" : "Grammatika" });
  }
  if (!skill) out.push({ key: "vocab", label: "Lug'at 20/40/60" });
  if ((L.class_ex ?? []).length) out.push({ key: "class", label: "Sinf mashqlari" });
  if (L.reading || (L.readings ?? []).length) out.push({ key: "reading", label: "Reading" });
  if (L.listening || (L.listenings ?? []).length) out.push({ key: "listening", label: "Listening" });
  out.push({ key: "home", label: "Uyga vazifa" });
  return out;
}

function LessonView({ course, no }: { course: string; no: number }) {
  const nav = useNavigate();
  const [L, setL] = useState<Lesson | null>(null);
  const [tab, setTab] = useState<Tab>("plan");
  const [err, setErr] = useState("");
  const [mode, setMode] = useState("mixed");
  const [count, setCount] = useState(20);
  const [secs, setSecs] = useState(20);
  const [busy, setBusy] = useState(false);
  const [groups, setGroups] = useState<LiveGroup[]>([]);
  const [groupId, setGroupId] = useState<number | "">("");

  useEffect(() => {
    setL(null);
    api.get<Lesson>(`/plans/${course}/${no}`).then(setL).catch((e) => setErr(e.message));
  }, [course, no]);
  // Ustoz o'z guruhini tanlaydi — coin va natija shu guruhga yoziladi
  useEffect(() => {
    api.get<LiveGroup[]>("/live/groups").then((g) => {
      setGroups(g);
      if (g.length === 1) setGroupId(g[0].id);
    }).catch(() => {});
  }, []);

  async function startGame() {
    if (!groupId) { setErr("Avval guruhni tanlang"); return; }
    setBusy(true); setErr("");
    try {
      const g = await api.post<{ id: number }>("/live/games",
        { course, lesson_no: no, group_id: groupId, mode, count: Math.max(20, count), seconds: secs });
      nav(`/live/${g.id}`);
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  if (err && !L) return <div className="p-8 text-rose-600">{err}</div>;
  if (!L) return <div className="p-8 text-slate-500">Yuklanmoqda…</div>;
  const tabs = tabsFor(L);
  const hasVocab = tabs.some((t) => t.key === "vocab");
  const active: Tab = tabs.some((t) => t.key === tab) ? tab : "plan";

  return (
    <div className="p-6 md:p-8 max-w-6xl">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div>
          <Link to={`/plans/${course}`} className="text-sm text-slate-500 hover:text-brand-600 flex items-center gap-1 mb-1">
            <ArrowLeft size={14} /> Darslar ro'yxati
          </Link>
          <h1 className="text-xl font-semibold text-slate-900">Dars {L.no} — {L.title}</h1>
          <div className="text-sm text-slate-500 mt-1">
            {hasVocab
              ? <>Grammatika: {L.grammar_topic} · Lug'at: {L.vocab_topic}</>
              : <>Savol turi: {L.grammar_topic}{L.vocab_topic ? ` · Mavzu: ${L.vocab_topic}` : ""}</>} · {L.duration} daqiqa
            {L.test_after ? ` · keyin: ${L.test_after}` : ""}
          </div>
          <div className="flex gap-3 mt-2">
            {no > 1 && <Link to={`/plans/${course}/${no - 1}`} className="text-xs text-brand-600">← Dars {no - 1}</Link>}
            <Link to={`/plans/${course}/${no + 1}`} className="text-xs text-brand-600">Dars {no + 1} →</Link>
          </div>
        </div>
        {hasVocab && <div className="bg-gradient-to-br from-brand-600 to-indigo-700 text-white rounded-2xl p-4 w-full md:w-80 shadow">
          <div className="font-semibold flex items-center gap-2 mb-2"><Gamepad2 size={18} /> Jonli o'yin (Kahoot)</div>
          <select value={groupId} onChange={(e) => setGroupId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full text-slate-900 bg-white rounded-lg px-2 py-1.5 text-sm mb-2">
            <option value="">Guruhni tanlang…</option>
            {groups.map((g) => <option key={g.id} value={g.id}>{g.name} ({g.students.length} o'quvchi)</option>)}
          </select>
          <select value={mode} onChange={(e) => setMode(e.target.value)}
                  className="w-full text-slate-900 bg-white rounded-lg px-2 py-1.5 text-sm mb-2">
            {MODES.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
          </select>
          <div className="grid grid-cols-2 gap-2 text-sm mb-3">
            <label className="flex flex-col gap-0.5"><span className="text-white/80 text-xs">Savollar</span>
              <input type="number" min={20} max={60} value={count} onChange={(e) => setCount(Number(e.target.value))}
                     className="text-slate-900 bg-white rounded-lg px-2 py-1" /></label>
            <label className="flex flex-col gap-0.5"><span className="text-white/80 text-xs">Soniya / savol</span>
              <input type="number" min={5} max={90} value={secs} onChange={(e) => setSecs(Number(e.target.value))}
                     className="text-slate-900 bg-white rounded-lg px-2 py-1" /></label>
          </div>
          <button onClick={startGame} disabled={busy}
                  className="w-full bg-white text-brand-700 font-bold rounded-xl py-2.5 disabled:opacity-50">
            O'yin ochish → PIN + QR
          </button>
          <div className="text-[11px] text-white/70 mt-2">O'quvchilar jonyos.uz/play sahifasidan PIN bilan kirib, ro'yxatdan ismini tanlaydi. Kamida 20 savol. Coin avtomat: 100% to'g'ri — 3, 1-o'rin +3, 2-o'rin +2, 3-o'rin +1. Natija guruh imtihonlarida saqlanadi.</div>
          {err && <div className="text-xs bg-rose-500/80 rounded px-2 py-1 mt-2">{err}</div>}
        </div>}
      </div>

      <div className="flex gap-1 border-b border-slate-200 mb-4 overflow-x-auto">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
                  className={`px-3 py-2 text-sm whitespace-nowrap border-b-2 -mb-px ${active === t.key ? "border-brand-600 text-brand-700 font-medium" : "border-transparent text-slate-500 hover:text-slate-800"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {active === "plan" && <PlanTab L={L} />}
      {active === "grammar" && <GrammarTab L={L} />}
      {active === "vocab" && <VocabTab L={L} course={course} />}
      {active === "class" && <ExList list={L.class_ex ?? []} />}
      {active === "reading" && <ReadingTab L={L} />}
      {active === "listening" && <ListeningTab L={L} />}
      {active === "home" && (
        <>
          {(L.homework_intro ?? []).map((t, i) => <p key={i} className="text-sm text-slate-700 mb-3">{t}</p>)}
          <ExList list={L.homework ?? []} />
          {(L.normativ ?? []).length > 0 && <Section title="Normativ va coin">
            <Table head={["Normativ", "Shart", "Mukofot"]} rows={L.normativ} />
          </Section>}
        </>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
      <h3 className="font-semibold text-slate-800 mb-2">{title}</h3>
      {children}
    </div>
  );
}

function Bullets({ items }: { items: string[] }) {
  return <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">{items.map((t, i) => <li key={i}>{t}</li>)}</ul>;
}

function Table({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead><tr>{head.map((h) => <th key={h} className="text-left bg-slate-50 border border-slate-200 px-2 py-1.5 font-medium text-slate-600">{h}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => (
          <tr key={i} className={i % 2 ? "bg-slate-50/50" : ""}>{r.map((c, j) => <td key={j} className="border border-slate-200 px-2 py-1.5 align-top text-slate-800">{c}</td>)}</tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function PlanTab({ L }: { L: Lesson }) {
  return (
    <>
      {L.book_ref && <p className="text-xs text-slate-500 mb-3">{L.book_ref}</p>}
      <Section title="Dars maqsadlari"><Bullets items={L.objectives ?? []} /></Section>
      <Section title="Kerakli materiallar"><Bullets items={L.materials ?? []} /></Section>
      <Section title={`Vaqt jadvali (${L.duration} daqiqa)`}>
        <Table head={["Daq.", "Bosqich", "Nima qilinadi"]} rows={L.timeline ?? []} />
      </Section>
    </>
  );
}

function GrammarTab({ L }: { L: Lesson }) {
  // 1-dars (mindset) kabi darslarda formulalar/xatolar bo'lmasligi mumkin
  const G = L.grammar ?? ({} as Lesson["grammar"]);
  const intro = G.intro ?? [], formulas = G.formulas ?? [], pres = G.presentation ?? [], notes = G.notes ?? [], mistakes = G.mistakes ?? [];
  return (
    <>
      {intro.length > 0 && <Section title="Tushuntirish"><Bullets items={intro} /></Section>}
      {formulas.length > 0 && <Section title="Formulalar"><Table head={["Mavzu", "Formula", "Misol", "Tarjima"]} rows={formulas} /></Section>}
      {pres.length > 0 && <Section title="Ustoz–o'quvchi savol-javob"><Table head={["Ustoz", "O'quvchi"]} rows={pres} /></Section>}
      {notes.length > 0 && <Section title="Ustoz uchun eslatma"><Bullets items={notes} /></Section>}
      {mistakes.length > 0 && <Section title="Tipik xatolar"><Table head={["Xato", "To'g'ri", "Nega"]} rows={mistakes} /></Section>}
      {!intro.length && !formulas.length && !pres.length && <p className="text-sm text-slate-500">Bu darsda grammatika bo'limi yo'q.</p>}
    </>
  );
}

/** Lug'at PDF (2026-09-18, Jahongir: "20/40/60 ... har birni yuklab
 * olish imkoniyati bo'lishi kerak, pdf shaklda"). Token bilan yuklab,
 * brauzerga fayl sifatida beradi. */
async function downloadPdf(path: string, filename: string) {
  const token = getToken();
  const res = await fetch(`/api${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) throw new Error("PDF tayyorlab bo'lmadi");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

function VocabTab({ L, course }: { L: Lesson; course: string }) {
  const V = L.vocab;
  const [dl, setDl] = useState<string | null>(null);
  const [dlErr, setDlErr] = useState("");
  async function pdf(tier: "20" | "40" | "60") {
    setDl(tier); setDlErr("");
    try { await downloadPdf(`/plans/${course}/${L.no}/vocab.pdf?tier=${tier}`, `Dars ${L.no} - lugat ${tier}.pdf`); }
    catch (e) { setDlErr((e as Error).message); }
    finally { setDl(null); }
  }
  if (!V) return <p className="text-sm text-slate-500">Bu darsda lug'at yo'q.</p>;
  const tiers: { key: "core" | "strong" | "super"; label: string; cls: string }[] = [
    { key: "core", label: "CORE 20 — hamma uchun", cls: "text-emerald-700" },
    { key: "strong", label: "STRONG +20 — kuchli o'quvchi (jami 40)", cls: "text-sky-700" },
    { key: "super", label: "SUPER +20 — eng kuchli (jami 60)", cls: "text-violet-700" },
  ];
  const [open, setOpen] = useState<Record<string, boolean>>({ core: true });
  return (
    <>
      {V.how?.length > 0 && <p className="text-sm text-slate-600 mb-3">{V.how.join(" ")}</p>}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs text-slate-500 flex items-center gap-1"><Download size={14} /> PDF yuklab olish:</span>
        {(["20", "40", "60"] as const).map((t) => (
          <button key={t} onClick={() => pdf(t)} disabled={dl !== null}
                  className="text-xs bg-white border border-slate-200 hover:border-brand-400 rounded-lg px-3 py-1.5 font-medium text-slate-700 disabled:opacity-50">
            {dl === t ? "Tayyorlanmoqda…" : t === "20" ? "CORE 20" : t === "40" ? "40 so'z (CORE+STRONG)" : "60 so'z (hammasi)"}
          </button>
        ))}
        {dlErr && <span className="text-xs text-rose-600">{dlErr}</span>}
      </div>
      {tiers.map((t) => (
        <div key={t.key} className="bg-white rounded-xl border border-slate-200 mb-3">
          <button onClick={() => setOpen({ ...open, [t.key]: !open[t.key] })}
                  className={`w-full flex items-center justify-between px-4 py-3 font-semibold ${t.cls}`}>
            {t.label} {open[t.key] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {open[t.key] && (
            <div className="px-4 pb-4">
              <Table head={["#", "So'z", "Tarjima", "Transkripsiya", "Misol", "Tarjimasi"]}
                     rows={V[t.key].map((w, i) => [i + 1, w[0], w[1], w[4] ? `[${w[4]}]` : "", w[2] ?? "", w[3] ?? ""])} />
            </div>
          )}
        </div>
      ))}
      {V.normativ?.length > 0 && <Section title="Normativ"><Bullets items={V.normativ} /></Section>}
    </>
  );
}

/** Javobni bo'sh joyning O'RNIDA ko'rsatadi (2026-09-18, Jahongir:
 * "javob yonida emas qoyiladigan joyida korinsin"). Bir nechta bo'sh joy
 * bo'lsa javob " / " bo'yicha bo'linadi; bo'sh joy bo'lmasa — oxiriga. */
function fillBlank(item: string, answer: string): React.ReactNode {
  const parts = item.split(/_{2,}|…{2,}|\.{4,}/);
  if (parts.length < 2) {
    return <>{item} <span className="text-emerald-700 font-medium">→ {answer}</span></>;
  }
  const answers = parts.length > 2 && answer.includes(" / ") ? answer.split(" / ") : [answer];
  return (
    <>
      {parts.map((p, k) => (
        <span key={k}>
          {p}
          {k < parts.length - 1 && (
            <span className="text-emerald-700 font-semibold border-b border-emerald-500 px-0.5">
              {answers[k] ?? answers[answers.length - 1]}
            </span>
          )}
        </span>
      ))}
    </>
  );
}

/* ---- Topshiriq ko'rinishlari (2026-09-21, Jahongir: "Tableni ham chiroyliq
   qilib tushunarli qilib qoy ... quruq sozlar gaplar bolmasin"). Savol turi
   o'z shaklida chiqadi: jadval, forma/qaydlar, jarayon sxemasi, variantlar,
   T/F/NG jadvali, sarlavhalar mosligi. Bo'sh joylar raqamli katak bo'lib
   turadi; "Javobni ko'rsat" bosilganda javob shu katakning o'zida chiqadi. */
const GAP_RE = /\((\d+)\)|_{3,}/g;

function Gap({ n, ans }: { n: number; ans?: string }) {
  if (ans !== undefined) {
    return <span className="mx-0.5 px-1.5 rounded bg-emerald-50 text-emerald-700 font-semibold border-b-2 border-emerald-500">{ans}</span>;
  }
  return (
    <span className="mx-0.5 inline-flex items-center gap-1 align-baseline">
      <span className="text-[11px] font-bold text-white bg-brand-600 rounded px-1">{n}</span>
      <span className="inline-block w-20 border-b-2 border-dotted border-slate-400">&nbsp;</span>
    </span>
  );
}

/** Matndagi "(3)" yoki "___" ni raqamli katakka aylantiradi. */
function withGaps(text: string, fallbackNo: number, answers: string[] | undefined, show: boolean) {
  const out: React.ReactNode[] = [];
  let last = 0; let k = 0;
  text.replace(GAP_RE, (m, num, idx: number) => {
    out.push(text.slice(last, idx));
    const n = num ? Number(num) : fallbackNo;
    out.push(<Gap key={k++} n={n} ans={show && answers ? answers[n - 1] : undefined} />);
    last = idx + m.length;
    return m;
  });
  out.push(text.slice(last));
  return out;
}

function splitPair(item: string): [string, string] {
  const dash = item.lastIndexOf(" — ");
  if (dash > 0) return [item.slice(0, dash), item.slice(dash + 3)];
  const colon = item.indexOf(": ");
  if (colon > 0) return [item.slice(0, colon), item.slice(colon + 2)];
  return ["", item];
}

function Why({ text }: { text?: string }) {
  if (!text) return null;
  return <div className="text-xs text-slate-500 mt-1">Nega: {text}</div>;
}

function Cell({ text, answers, show }: { text: string; answers?: string[]; show: boolean }) {
  const lines = text.split(/\s*;;\s*/);
  if (lines.length > 1) {
    return <ul className="list-disc pl-4 space-y-0.5">{lines.map((l, i) => <li key={i}>{withGaps(l, 0, answers, show)}</li>)}</ul>;
  }
  return <>{withGaps(text, 0, answers, show)}</>;
}
const TH = "text-left bg-brand-50 text-brand-800 border border-slate-200 px-3 py-2 font-semibold text-xs uppercase tracking-wide";
const TD = "border border-slate-200 px-3 py-2 align-top text-slate-800";

function ExBody({ ex, show }: { ex: Ex; show: boolean }) {
  const items = ex.items ?? [];
  const answers = Array.isArray(ex.answers) ? ex.answers : undefined;
  const why = ex.why ?? [];
  const lay = ex.layout;
  // Jadval/sxemada bo'sh joy raqami (7, 8...) savol raqamiga bog'lanadi
  const labelOf = (j: number) => { const n = parseInt(items[j] ?? "", 10); return Number.isNaN(n) ? j + 1 : n; };
  const byNo: string[] = [];
  if (answers) items.forEach((_, j) => { byNo[labelOf(j) - 1] = answers[j]; });

  if (lay === "grid" && ex.head && ex.rows) {
    return (
      <>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-sm border-collapse">
            <thead><tr>{ex.head.map((h, i) => <th key={i} className={TH}>{h}</th>)}</tr></thead>
            <tbody>{ex.rows.map((r, i) => (
              <tr key={i} className={i % 2 ? "bg-slate-50/60" : ""}>
                {r.map((c, j) => <td key={j} className={`${TD} ${j === 0 ? "font-semibold" : ""}`}><Cell text={c} answers={byNo} show={show} /></td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
        {show && items.length > 0 && (
          <div className="mt-3 bg-emerald-50/40 rounded-lg p-3">
            <div className="text-xs font-semibold text-emerald-800 mb-1">Javoblar va izoh</div>
            <ol className="space-y-1.5">{items.map((_, j) => (
              <li key={j} className="text-sm"><span className="font-bold text-brand-700 mr-1">{labelOf(j)}.</span>
                <span className="font-semibold text-emerald-700">{answers?.[j]}</span><Why text={why[j]} /></li>
            ))}</ol>
          </div>
        )}
      </>
    );
  }

  if (lay === "pairs" && !items.some((it) => /_{3,}|\(\d+\)/.test(it))) {
    // Bo'sh joysiz juftlar (paraphrase moslash): so'z | javob
    return (
      <div className="overflow-x-auto mt-3">
        <table className="w-full text-sm border-collapse">
          <thead><tr><th className={`${TH} w-10`}>#</th><th className={TH}>So'z / ibora</th><th className={TH}>Javob</th></tr></thead>
          <tbody>{items.map((it, j) => (
            <tr key={j} className={j % 2 ? "bg-slate-50/60" : ""}>
              <td className={`${TD} text-center font-bold text-brand-700`}>{j + 1}</td>
              <td className={`${TD} font-medium`}>{it}</td>
              <td className={TD}>{show
                ? <><span className="font-semibold text-emerald-700">{answers?.[j]}</span><Why text={why[j]} /></>
                : <span className="inline-block w-28 border-b-2 border-dotted border-slate-400">&nbsp;</span>}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    );
  }

  if (lay === "pairs") {
    return (
      <div className="overflow-x-auto mt-3">
        <table className="w-full text-sm border-collapse">
          <tbody>{items.map((it, j) => {
            const [l, r] = splitPair(it);
            return (
              <tr key={j} className={j % 2 ? "bg-slate-50/60" : ""}>
                <td className={`${TD} w-10 text-center font-bold text-brand-700`}>{j + 1}</td>
                {l && <td className={`${TD} font-medium text-slate-600 w-2/5`}>{l}</td>}
                <td className={TD} colSpan={l ? 1 : 2}>{withGaps(r, j + 1, answers, show)}<Why text={show ? why[j] : undefined} /></td>
              </tr>
            );
          })}</tbody>
        </table>
      </div>
    );
  }

  if (lay === "flow" && ex.rows && ex.rows.length) {
    // Qutilar alohida (row), javoblar alohida (items) — ustoz sxemasi
    const boxes = ex.rows.map((r) => r[0]);
    return (
      <>
        <div className="mt-3 flex flex-col items-center">
          {boxes.map((b, j) => (
            <div key={j} className="w-full max-w-md flex flex-col items-center">
              <div className="w-full text-center border-2 border-brand-200 bg-white rounded-lg px-3 py-2 text-sm shadow-sm">
                {withGaps(b, 0, byNo, show)}
              </div>
              {j < boxes.length - 1 && <div className="text-brand-400 text-lg leading-none py-0.5">↓</div>}
            </div>
          ))}
        </div>
        {show && items.length > 0 && (
          <div className="mt-3 bg-emerald-50/40 rounded-lg p-3">
            <div className="text-xs font-semibold text-emerald-800 mb-1">Javoblar va izoh</div>
            <ol className="space-y-1.5">{items.map((_, j) => (
              <li key={j} className="text-sm"><span className="font-bold text-brand-700 mr-1">{labelOf(j)}.</span>
                <span className="font-semibold text-emerald-700">{answers?.[j]}</span><Why text={why[j]} /></li>
            ))}</ol>
          </div>
        )}
      </>
    );
  }

  if (lay === "flow") {
    return (
      <div className="mt-3 flex flex-col items-stretch max-w-xl">
        {items.map((it, j) => (
          <div key={j}>
            <div className="border-2 border-brand-200 bg-white rounded-lg px-3 py-2 text-sm">
              <span className="text-[11px] font-bold text-brand-600 mr-2">{j + 1}-bosqich</span>
              {withGaps(it.replace(/\s*→\s*/g, " → "), j + 1, answers, show)}
              <Why text={show ? why[j] : undefined} />
            </div>
            {j < items.length - 1 && <div className="text-center text-brand-400 text-lg leading-none py-0.5">↓</div>}
          </div>
        ))}
      </div>
    );
  }
  if (lay === "mcq") {
    return (
      <div className="mt-3 space-y-3">
        {items.map((it, j) => {
          // A–E va "Choose TWO" (javob "B, C"), raqam "1–2" ham bo'lishi mumkin
          const parts = it.split(/\s+(?=[A-E]\)\s)/);
          const qn = parts[0].match(/^(\d+(?:[–-]\d+)?)\s+/)?.[1];
          const q = parts[0].replace(/^\d+(?:[–-]\d+)?\s+/, "");
          const opts = parts.slice(1);
          const lead = (answers?.[j] ?? "").trim().match(/^[A-E](?:\s*,\s*[A-E])*(?![a-z])/)?.[0] ?? "";
          const correct = new Set(lead.match(/[A-E]/g) ?? []);
          return (
            <div key={j} className="rounded-lg border border-slate-200 p-3">
              <div className="text-sm font-medium text-slate-800"><span className="font-bold text-brand-700 mr-1">{qn ?? j + 1}.</span>{q}</div>
              <div className="grid sm:grid-cols-2 gap-1.5 mt-2">
                {opts.map((o, k) => {
                  const letter = o.charAt(0);
                  const ok = show && correct.has(letter);
                  return (
                    <div key={k} className={`text-sm rounded-md px-2.5 py-1.5 border ${ok ? "border-emerald-500 bg-emerald-50 text-emerald-800 font-semibold" : "border-slate-200 bg-slate-50 text-slate-700"}`}>
                      <span className="font-bold mr-1">{letter}</span>{o.slice(2).trim()}
                    </div>
                  );
                })}
              </div>
              <Why text={show ? why[j] : undefined} />
            </div>
          );
        })}
      </div>
    );
  }

  if (lay === "tfng" || lay === "match" || lay === "qa") {
    const colA = lay === "tfng" ? "Gap (statement)" : lay === "match" ? "Savol / so'z" : "Savol / holat";
    const colB = lay === "tfng" ? "Javob" : lay === "match" ? "Mos variant" : "Javob";
    return (
      <>
        {ex.box && ex.box.length > 0 && (
          <div className="mt-3 rounded-lg border border-brand-200 bg-brand-50/50 p-3">
            <div className="text-xs font-semibold text-brand-800 mb-1">Variantlar ro'yxati</div>
            <ul className="text-sm text-slate-800 space-y-0.5">{ex.box.map((b, k) => <li key={k}>{b}</li>)}</ul>
          </div>
        )}
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-sm border-collapse">
            <thead><tr><th className={`${TH} w-10`}>#</th><th className={TH}>{colA}</th><th className={`${TH} w-40`}>{colB}</th></tr></thead>
            <tbody>{items.map((it, j) => (
              <tr key={j} className={j % 2 ? "bg-slate-50/60" : ""}>
                <td className={`${TD} text-center font-bold text-brand-700`}>{j + 1}</td>
                <td className={TD}>{it.replace(/^\d+\s+/, "")}<Why text={show ? why[j] : undefined} /></td>
                <td className={TD}>{show
                  ? <span className="font-semibold text-emerald-700">{answers?.[j]}</span>
                  : <span className="inline-block w-24 border-b-2 border-dotted border-slate-400">&nbsp;</span>}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </>
    );
  }

  // Oddiy ro'yxat (savollar, gap to'ldirish): raqamli, bo'sh joy katak bilan
  return (
    <ol className="mt-3 space-y-2">
      {items.map((it, j) => (
        <li key={j} className="text-sm text-slate-800 flex gap-2">
          <span className="font-bold text-brand-700 w-6 shrink-0 text-right">{j + 1}.</span>
          <div className="flex-1">
            {/_{3,}|\(\d+\)/.test(it)
              ? withGaps(it, j + 1, answers, show)
              : <>{it}{show && answers?.[j] && <span className="ml-2 font-semibold text-emerald-700">→ {answers[j]}</span>}</>}
            <Why text={show ? why[j] : undefined} />
          </div>
        </li>
      ))}
    </ol>
  );
}

function ExList({ list }: { list: Ex[] }) {
  const [show, setShow] = useState<Record<number, boolean>>({});
  return (
    <>
      {list.map((ex, i) => (
        <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 mb-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="font-semibold text-slate-800">{i + 1}. {ex.title}</div>
              {ex.type && <div className="text-xs text-slate-500">{ex.type}</div>}
            </div>
            {ex.answers && (
              <button onClick={() => setShow({ ...show, [i]: !show[i] })}
                      className="text-xs text-brand-600 whitespace-nowrap">{show[i] ? "Javobni yashir" : "Javobni ko'rsat"}</button>
            )}
          </div>
          {ex.instr && <p className="text-sm text-slate-700 mt-2">{ex.instr}</p>}
          {ex.box && ex.layout !== "match" && ex.layout !== "tfng" && <div className="text-xs bg-slate-50 rounded px-2 py-1 mt-2 text-slate-600">{ex.box.join(" · ")}</div>}
          {ex.layout && <ExBody ex={ex} show={!!show[i]} />}
          {!ex.layout && ex.items && (
            <ol className="list-decimal pl-5 text-sm text-slate-800 mt-2 space-y-0.5">
              {ex.items.map((it, j) => {
                const ans = show[i] && Array.isArray(ex.answers) ? ex.answers[j] : undefined;
                const why = show[i] && ex.why ? ex.why[j] : undefined;
                return (
                  <li key={j}>
                    {ans !== undefined ? fillBlank(it, ans) : it}
                    {why && <div className="text-xs text-slate-500 mt-0.5">Nega: {why}</div>}
                  </li>
                );
              })}
            </ol>
          )}
          {show[i] && (!ex.items || !Array.isArray(ex.answers)) && ex.answers && (
            <div className="text-sm text-emerald-700 mt-2">
              {Array.isArray(ex.answers) ? ex.answers.join("; ") : ex.answers}
            </div>
          )}
          {ex.note && <div className="text-xs text-slate-500 mt-2">{ex.note}</div>}
        </div>
      ))}
    </>
  );
}

/** Matndagi _so'z_ belgisi — tagiga chizilgan (paraphrase) so'z. */
function renderRich(t: string): React.ReactNode {
  const parts = t.split(/(_[^_]+_)/g);
  return parts.map((p, i) => p.length > 2 && p.startsWith("_") && p.endsWith("_")
    ? <span key={i} className="underline decoration-brand-500 decoration-2 underline-offset-2 font-medium">{p.slice(1, -1)}</span>
    : <span key={i}>{p}</span>);
}

function Paraphrases({ rows }: { rows: [string, string][] }) {
  return (
    <Section title="Paraphrase — ma'nosi bir xil so'zlar">
      <Table head={["So'z", "Paraphrase (ma'nosi bir xil)"]} rows={rows} />
    </Section>
  );
}

/** Himoyalangan material rasmi: token bilan yuklab, blob sifatida
 * ko'rsatiladi (ochiq havola yo'q). */
function AuthImage({ name, alt }: { name: string; alt: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [bad, setBad] = useState(false);
  useEffect(() => {
    let u: string | null = null;
    const token = getToken();
    fetch(`/api/plan-media/${name}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => { if (!r.ok) throw new Error(); return r.blob(); })
      .then((b) => { u = URL.createObjectURL(b); setUrl(u); })
      .catch(() => setBad(true));
    return () => { if (u) URL.revokeObjectURL(u); };
  }, [name]);
  if (bad) return <p className="text-xs text-rose-600">Materialni yuklab bo'lmadi.</p>;
  if (!url) return <p className="text-xs text-slate-400">Yuklanmoqda…</p>;
  return <img src={url} alt={alt} className="w-full max-w-3xl rounded-lg border border-slate-200" />;
}

/** Ustoz bergan listening audiosi: AuthImage kabi token bilan yuklanadi. */
function AuthAudio({ name }: { name: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [bad, setBad] = useState(false);
  useEffect(() => {
    let u: string | null = null;
    const token = getToken();
    fetch(`/api/plan-media/${name}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => { if (!r.ok) throw new Error(); return r.blob(); })
      .then((b) => { u = URL.createObjectURL(b); setUrl(u); })
      .catch(() => setBad(true));
    return () => { if (u) URL.revokeObjectURL(u); };
  }, [name]);
  if (bad) return <p className="text-xs text-rose-600">Audioni yuklab bo'lmadi.</p>;
  if (!url) return <p className="text-xs text-slate-400">Audio yuklanmoqda…</p>;
  return <audio controls preload="metadata" src={url} className="w-full max-w-xl" controlsList="nodownload" />;
}

function ReadingBlock({ R, idx }: { R: Reading; idx: number }) {
  const [open, setOpen] = useState(idx === 0);
  return (
    <div className="mb-5">
      <button onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between gap-3 bg-white rounded-xl border border-slate-200 px-4 py-3 text-left">
        <span>
          <span className="font-semibold text-slate-800">{idx + 1}. {R.title}</span>
          {R.qtype && <span className="ml-2 text-xs bg-brand-50 text-brand-700 rounded px-2 py-0.5">{R.qtype}</span>}
          {R.source && <span className="ml-2 text-xs text-slate-500">{R.source}</span>}
        </span>
        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </button>
      {open && (
        <div className="mt-3">
          {R.book_ref && <p className="text-xs text-slate-500 mb-2">{R.book_ref}</p>}
          {R.image && !(R.text ?? []).length && (
            <Section title="Matn (Jony Academy hujjati)">
              <AuthImage name={R.image} alt={R.title} />
            </Section>
          )}
          {(R.text ?? []).length > 0 && (
            <Section title="Matn">
              <div className="flex items-center gap-1 text-xs text-slate-400 mb-2"><FileText size={13} /> Sinfda o'qish uchun</div>
              <div className="relative">
                <img src={brandIconSrc} alt="" aria-hidden="true"
                     className="pointer-events-none select-none absolute inset-0 m-auto w-2/3 max-w-sm opacity-[0.07]" />
                <div className="relative">
                  {R.text!.map((t, i) => <p key={i} className="text-[15px] text-slate-800 mb-3 leading-relaxed">{renderRich(t)}</p>)}
                </div>
                <div className="relative text-right text-[11px] font-semibold tracking-widest text-brand-700/60 mt-1">JONY ACADEMY</div>
              </div>
              {(R.glossary ?? []).length > 0 && (
                <div className="text-xs text-slate-600 bg-slate-50 rounded px-3 py-2 mt-2">{R.glossary!.join(" · ")}</div>
              )}
            </Section>
          )}
          {R.image && (R.text ?? []).length > 0 && (
            <Section title="Chizma">
              <AuthImage name={R.image} alt={R.title} />
            </Section>
          )}
          {(R.paraphrases ?? []).length > 0 && <Paraphrases rows={R.paraphrases!} />}
          <ExList list={R.tasks ?? []} />
        </div>
      )}
    </div>
  );
}

function ReadingTab({ L }: { L: Lesson }) {
  const R = L.reading;
  const many = L.readings ?? [];
  if (many.length > 0) return <>{many.map((r, i) => <ReadingBlock key={i} R={r} idx={i} />)}</>;
  if (!R) return <p className="text-sm text-slate-500">Bu darsda reading matni yo'q.</p>;
  return (
    <>
      {R.book_ref && <p className="text-xs text-slate-500 mb-3">{R.book_ref}</p>}
      <Section title={R.title}>
        <div className="flex items-center gap-1 text-xs text-slate-400 mb-2"><FileText size={13} /> Sinfda o'qish uchun matn</div>
        {R.text.map((p, i) => <p key={i} className="text-sm text-slate-800 mb-2 leading-relaxed">{p}</p>)}
        {R.glossary?.length > 0 && (
          <div className="text-xs text-slate-600 bg-slate-50 rounded px-3 py-2 mt-2">{R.glossary.join(" · ")}</div>
        )}
      </Section>
      <ExList list={R.tasks} />
    </>
  );
}

function ListenBlock({ S, idx }: { S: Listen; idx: number }) {
  const [open, setOpen] = useState(idx === 0);
  const [tr, setTr] = useState(false);
  return (
    <div className="mb-5">
      <button onClick={() => setOpen(!open)}
              className="w-full flex items-center justify-between gap-3 bg-white rounded-xl border border-slate-200 px-4 py-3 text-left">
        <span>
          <span className="font-semibold text-slate-800">{idx + 1}. {S.title}</span>
          {S.qtype && <span className="ml-2 text-xs bg-brand-50 text-brand-700 rounded px-2 py-0.5">{S.qtype}</span>}
          {S.audios && <span className="ml-2 text-xs text-slate-500">{S.audios}</span>}
        </span>
        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </button>
      {open && (
        <div className="mt-3">
          {S.audio && (
            <div className="bg-white rounded-xl border border-slate-200 p-3 mb-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 mb-2">
                <Headphones size={15} className="text-brand-600" /> Audio
              </div>
              <AuthAudio name={S.audio} />
            </div>
          )}
          {(S.intro ?? []).map((t, i) => <p key={i} className="text-sm text-slate-700 mb-2">{t}</p>)}
          {S.image && (
            <Section title="Chizma">
              <AuthImage name={S.image} alt={S.title} />
            </Section>
          )}
          <ExList list={S.tasks ?? []} />
          {(S.transcript ?? []).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <button onClick={() => setTr(!tr)} className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <Headphones size={15} className="text-brand-600" /> Transkript {tr ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>
              {tr && <div className="mt-2">{S.transcript!.map((t, i) => <p key={i} className="text-sm text-slate-800 mb-1.5 leading-relaxed">{t}</p>)}</div>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ListeningTab({ L }: { L: Lesson }) {
  const S = L.listening;
  const many = L.listenings ?? [];
  if (many.length > 0) return <>{many.map((x, i) => <ListenBlock key={i} S={x} idx={i} />)}</>;
  if (!S) return <p className="text-sm text-slate-500">Bu darsda listening yo'q.</p>;
  return (
    <>
      <div className="flex items-center gap-2 text-sm text-slate-700 mb-3"><Headphones size={16} className="text-brand-600" /> Audio {S.audios}</div>
      {S.intro.map((t, i) => <p key={i} className="text-sm text-slate-700 mb-3">{t}</p>)}
      <ExList list={S.tasks} />
    </>
  );
}
