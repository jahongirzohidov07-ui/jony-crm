import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { BookOpen, Gamepad2, ArrowLeft, ChevronDown, ChevronUp, ChevronRight, Headphones, FileText, Download } from "lucide-react";
import { api, getToken } from "../lib/api";

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
  answers?: string[] | string; note?: string; box?: string[] };
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
                  {lv.lessons.length > 0 && !lv.ready && " · reja tayyorlanmoqda"}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs">
              {lv.ready
                ? <span className="bg-emerald-50 text-emerald-700 rounded px-2 py-0.5">Tayyor</span>
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
                  <div className={`font-medium ${l.ready ? "text-slate-900" : "text-slate-500"}`}>{l.no}-dars — {l.title}</div>
                  <div className="text-xs text-slate-500 truncate">
                    Lug'at: {l.vocab_topic || "—"}{l.audios ? ` · Audio ${l.audios}` : ""}{l.writing ? ` · ${l.writing}` : ""}
                  </div>
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

const TABS = [
  { key: "plan", label: "Reja" }, { key: "grammar", label: "Grammatika" },
  { key: "vocab", label: "Lug'at 20/40/60" }, { key: "class", label: "Sinf mashqlari" },
  { key: "reading", label: "Reading" }, { key: "listening", label: "Listening" },
  { key: "home", label: "Uyga vazifa" },
] as const;
type Tab = typeof TABS[number]["key"];

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

  return (
    <div className="p-6 md:p-8 max-w-6xl">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div>
          <Link to={`/plans/${course}`} className="text-sm text-slate-500 hover:text-brand-600 flex items-center gap-1 mb-1">
            <ArrowLeft size={14} /> Darslar ro'yxati
          </Link>
          <h1 className="text-xl font-semibold text-slate-900">Dars {L.no} — {L.title}</h1>
          <div className="text-sm text-slate-500 mt-1">
            Grammatika: {L.grammar_topic} · Lug'at: {L.vocab_topic} · {L.duration} daqiqa
            {L.test_after ? ` · keyin: ${L.test_after}` : ""}
          </div>
          <div className="flex gap-3 mt-2">
            {no > 1 && <Link to={`/plans/${course}/${no - 1}`} className="text-xs text-brand-600">← Dars {no - 1}</Link>}
            <Link to={`/plans/${course}/${no + 1}`} className="text-xs text-brand-600">Dars {no + 1} →</Link>
          </div>
        </div>
        <div className="bg-gradient-to-br from-brand-600 to-indigo-700 text-white rounded-2xl p-4 w-full md:w-80 shadow">
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
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-200 mb-4 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
                  className={`px-3 py-2 text-sm whitespace-nowrap border-b-2 -mb-px ${tab === t.key ? "border-brand-600 text-brand-700 font-medium" : "border-transparent text-slate-500 hover:text-slate-800"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "plan" && <PlanTab L={L} />}
      {tab === "grammar" && <GrammarTab L={L} />}
      {tab === "vocab" && <VocabTab L={L} course={course} />}
      {tab === "class" && <ExList list={L.class_ex} />}
      {tab === "reading" && <ReadingTab L={L} />}
      {tab === "listening" && <ListeningTab L={L} />}
      {tab === "home" && (
        <>
          {L.homework_intro.map((t, i) => <p key={i} className="text-sm text-slate-700 mb-3">{t}</p>)}
          <ExList list={L.homework} />
          <Section title="Normativ va coin">
            <Table head={["Normativ", "Shart", "Mukofot"]} rows={L.normativ} />
          </Section>
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
      <Section title="Dars maqsadlari"><Bullets items={L.objectives} /></Section>
      <Section title="Kerakli materiallar"><Bullets items={L.materials} /></Section>
      <Section title={`Vaqt jadvali (${L.duration} daqiqa)`}>
        <Table head={["Daq.", "Bosqich", "Nima qilinadi"]} rows={L.timeline} />
      </Section>
    </>
  );
}

function GrammarTab({ L }: { L: Lesson }) {
  const G = L.grammar;
  return (
    <>
      <Section title="Tushuntirish"><Bullets items={G.intro} /></Section>
      <Section title="Formulalar"><Table head={["Mavzu", "Formula", "Misol", "Tarjima"]} rows={G.formulas} /></Section>
      <Section title="Ustoz–o'quvchi savol-javob"><Table head={["Ustoz", "O'quvchi"]} rows={G.presentation} /></Section>
      {G.notes?.length > 0 && <Section title="Ustoz uchun eslatma"><Bullets items={G.notes} /></Section>}
      <Section title="Tipik xatolar"><Table head={["Xato", "To'g'ri", "Nega"]} rows={G.mistakes} /></Section>
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
          {ex.box && <div className="text-xs bg-slate-50 rounded px-2 py-1 mt-2 text-slate-600">{ex.box.join(" · ")}</div>}
          {ex.items && (
            <ol className="list-decimal pl-5 text-sm text-slate-800 mt-2 space-y-0.5">
              {ex.items.map((it, j) => (
                <li key={j}>{it}{show[i] && Array.isArray(ex.answers) && ex.answers[j] !== undefined && (
                  <span className="text-emerald-700 font-medium"> → {ex.answers[j]}</span>)}</li>
              ))}
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

function ReadingTab({ L }: { L: Lesson }) {
  const R = L.reading;
  if (!R) return <p className="text-sm text-slate-500">Bu darsda reading matni yo'q (6-darsdan boshlanadi).</p>;
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

function ListeningTab({ L }: { L: Lesson }) {
  const S = L.listening;
  if (!S) return <p className="text-sm text-slate-500">Bu darsda listening yo'q.</p>;
  return (
    <>
      <div className="flex items-center gap-2 text-sm text-slate-700 mb-3"><Headphones size={16} className="text-brand-600" /> Audio {S.audios}</div>
      {S.intro.map((t, i) => <p key={i} className="text-sm text-slate-700 mb-3">{t}</p>)}
      <ExList list={S.tasks} />
    </>
  );
}
