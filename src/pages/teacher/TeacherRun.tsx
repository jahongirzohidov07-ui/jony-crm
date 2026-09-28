import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, Check, ChevronRight, Monitor, MonitorOff, Users, Gamepad2, Flag, Timer as TimerIcon,
} from "lucide-react";
import { api } from "../../lib/api";
// Mashqlarni reja ekranidagi bilan BIR XIL ko'rsatish uchun (2026-09-26):
// grid/pairs/flow/mcq/tfng/match/qa/list ko'rinishlari shu komponentda.
import { ExBody } from "../LessonPlans";

/**
 * DARS REJIMI — "Darsni boshlash" (2026-09-18, Jahongir: "Dars paytida
 * ustoz bir nechta sahifa orasida yurmasligi kerak. Bitta oynada: dars
 * bosqichlari va taymer, doska/proyektor materiali, topshiriq yuborish,
 * javoblarni ko'rish, bajarilgan qismlarni belgilash. 'Proyektor rejimi'
 * alohida — javob kalitlari, baholar va maxfiy izohlar ko'rinmasin").
 *
 * Bir sahifa, ikki ustun: chapda bosqichlar + taymer, o'ngda material.
 * Proyektor rejimi — javoblar, izohlar, o'quvchilar ro'yxati yashirinadi,
 * shrift kattalashadi.
 */

type Stage = { title: string; min: number; desc: string; done: boolean; carried: boolean };
type Ex = { title: string; type?: string; instr?: string; items?: string[]; answers?: string[] | string; note?: string; box?: string[]; why?: string[];
  layout?: "grid" | "pairs" | "flow" | "mcq" | "tfng" | "match" | "qa" | "list";
  head?: string[]; rows?: string[][] };
/** IELTS 5.0 darslarida bitta darsda bir nechta reading/listening bor
 * (readings / listenings), eski darslarda bittadan (reading / listening).
 * Ikkalasi ham ko'rsatiladi — avval faqat birlik kalit o'qilardi, shuning
 * uchun IELTS 5.0 ning 20 reading va 15 listeningi jonli darsda umuman
 * ko'rinmasdi (2026-09-26). */
type PlanReading = { title: string; qtype?: string; book_ref?: string; text?: string[];
  glossary?: string[]; paraphrases?: [string, string][]; tasks?: Ex[] };
type PlanListen = { title?: string; qtype?: string; audios?: string; audio?: string;
  intro?: string[]; transcript?: string[]; tasks?: Ex[] };
type Plan = {
  no: number; title: string; grammar_topic: string; vocab_topic: string;
  grammar: { intro: string[]; formulas: string[][]; presentation: [string, string][]; notes: string[]; mistakes: string[][] };
  vocab: { core: string[][]; strong: string[][]; super: string[][] };
  class_ex: Ex[];
  reading?: PlanReading;
  listening?: PlanListen;
  readings?: PlanReading[];
  listenings?: PlanListen[];
  homework_intro: string[]; homework: Ex[];
  kahoot?: unknown[];
};
type Run = {
  id: number; lesson_id: number; group_id: number; group: string | null; course: string; lesson_no: number;
  status: "running" | "finished"; current: number; stages: Stage[]; notes: string;
  stage_started_at: string | null; done_count: number; total: number;
  plan?: Plan | null; students?: { id: number; name: string }[];
};

const TABS = [
  { key: "grammar", label: "Grammatika" }, { key: "vocab", label: "Lug'at" }, { key: "class", label: "Mashqlar" },
  { key: "reading", label: "Reading" }, { key: "listening", label: "Listening" }, { key: "home", label: "Uyga vazifa" },
] as const;
type Tab = typeof TABS[number]["key"];

function fmt(sec: number) {
  const s = Math.max(0, Math.round(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function TeacherRun() {
  const { lessonId } = useParams();
  const nav = useNavigate();
  const [run, setRun] = useState<Run | null>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<Tab>("grammar");
  const [proj, setProj] = useState(false);
  const [showAns, setShowAns] = useState<Record<string, boolean>>({});
  const [notes, setNotes] = useState("");
  const [now, setNow] = useState(Date.now());
  const [finishing, setFinishing] = useState(false);
  const [advance, setAdvance] = useState(true);
  const [busy, setBusy] = useState(false);
  const notesTimer = useRef<number | null>(null);
  // Topshiriq yuborish (4-band): rejadan tanlab, bir bosishda
  const [sendOpen, setSendOpen] = useState(false);
  const [parts, setParts] = useState<{ part: string; label: string; auto: boolean | null }[]>([]);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [dueDays, setDueDays] = useState(2);
  const [sent, setSent] = useState("");
  const [stagesOpen, setStagesOpen] = useState(false);   // telefonda ro'yxatni ochish

  useEffect(() => {
    api.post<Run>(`/lessons/${lessonId}/run`).then((r) => { setRun(r); setNotes(r.notes || ""); })
      .catch((e) => setErr((e as Error).message));
  }, [lessonId]);
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t); }, []);

  const save = useCallback(async (body: Record<string, unknown>) => {
    if (!run) return;
    try {
      const r = await api.put<Run>(`/runs/${run.id}`, body);
      setRun((prev) => prev ? { ...prev, ...r, plan: prev.plan, students: prev.students } : prev);
    } catch (e) { setErr((e as Error).message); }
  }, [run]);

  function toggleDone(i: number) {
    if (!run) return;
    const done = run.stages.map((s, k) => (k === i ? !s.done : s.done)).map((d, k) => (d ? k : -1)).filter((k) => k >= 0);
    save({ done });
  }
  function goTo(i: number) { save({ current: i, restart_timer: true }); }
  function nextStage() {
    if (!run) return;
    const doneIdx = run.stages.map((s, k) => (s.done || k === run.current ? k : -1)).filter((k) => k >= 0);
    const next = Math.min(run.stages.length - 1, run.current + 1);
    save({ done: doneIdx, current: next, restart_timer: true });
  }
  function onNotes(v: string) {
    setNotes(v);
    if (notesTimer.current) window.clearTimeout(notesTimer.current);
    notesTimer.current = window.setTimeout(() => save({ notes: v }), 800);
  }
  async function finish() {
    if (!run) return;
    setBusy(true);
    try {
      const r = await api.post<{ carry: string[]; next_lesson_no: number | null }>(`/runs/${run.id}/finish`, { advance });
      alert(`Dars yakunlandi. Keyingi dars: ${r.next_lesson_no ?? "—"}-dars.` + (r.carry.length ? `\nKeyingi darsga ko'chdi: ${r.carry.join("; ")}` : ""));
      nav("/teacher");
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }
  async function openSend() {
    if (!run) return;
    setSendOpen(true);
    try { const p = await api.get<typeof parts>(`/plans/${run.course}/${run.lesson_no}/assignable`); setParts(p); }
    catch (e) { setErr((e as Error).message); }
  }
  async function sendAssignments() {
    if (!run) return;
    const list = Object.keys(picked).filter((k) => picked[k]);
    if (!list.length) return;
    setBusy(true); setSent("");
    try {
      const r = await api.post<{ title: string }[]>(`/groups/${run.group_id}/assignments/from-plan`,
        { course: run.course, lesson_no: run.lesson_no, parts: list, due_days: dueDays, lesson_id: run.lesson_id });
      setSent(`${r.length} ta topshiriq yuborildi — o'quvchilar ilovasida paydo bo'ldi.`);
      setPicked({});
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }
  /** Jonli o'yin: bugungi dars yoki o'tgan dars to'plami (2026-09-28).
   * Rejalarda dars boshidagi takror — o'tgan darsning Kahooti; tugma
   * faqat bugungi darsnikini ochardi va o'quvchi hali o'tilmagan mavzuga
   * tushib qolardi. */
  async function kahoot(lessonNo: number) {
    if (!run) return;
    setBusy(true);
    try {
      const g = await api.post<{ id: number }>("/live/games",
        { course: run.course, lesson_no: lessonNo, group_id: run.group_id, mode: "mixed", count: 20, seconds: 20 });
      window.open(`/live/${g.id}`, "_blank");
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  // Hook'lar har renderda bir xil tartibda chaqirilishi shart (2026-09-28):
  // useStageAlarm avval "Yuklanmoqda…" return'idan keyin turardi — run
  // yuklanishi bilan React "Rendered more hooks" xatosini berib, dars rejimi
  // ochilmasdi. Endi run yo'q paytda ham chaqiriladi (left = Infinity — jim).
  const cur = run ? run.stages[run.current] : undefined;
  const startedMs = run?.stage_started_at ? new Date(run.stage_started_at + (run.stage_started_at.endsWith("Z") ? "" : "Z")).getTime() : now;
  const left = run ? (cur?.min ?? 0) * 60 - (now - startedMs) / 1000 : Infinity;
  // BOSQICH TUGADI — ovoz va tebranish (2026-09-26). Avval taymer faqat
  // qizarardi: sinfga qarab turgan ustoz bosqich tugaganini bilmasdi.
  useStageAlarm(run ? run.current : -1, left);

  if (err && !run) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 text-center">
        <p className="text-rose-600 mb-3">{err}</p>
        <Link to="/teacher" className="text-brand-600 underline text-sm">← Bugungi darslar</Link>
      </div>
    );
  }
  if (!run) return <div className="min-h-screen bg-slate-50 p-6 text-slate-500">Yuklanmoqda…</div>;

  const P = run.plan;
  const over = left < 0;
  const big = proj ? "text-lg md:text-xl" : "text-sm";
  // Kahoot faqat savol manbai bor darsda (IELTS 5.0 da lug'at ham, kahoot ham
  // yo'q — tugma har safar "savol tuzib bo'lmadi" xatosini berardi)
  const canKahoot = !!(P && ((P.kahoot ?? []).length || (P.vocab?.core ?? []).length));

  return (
    <div className={`min-h-screen ${proj ? "bg-white" : "bg-slate-50"}`}>
      {/* ---- Sarlavha ---- */}
      <header className={`sticky top-0 z-10 ${proj ? "bg-slate-900 text-white" : "bg-white border-b border-slate-200"} px-4 py-2.5 flex items-center gap-3`}>
        {!proj && <Link to="/teacher" className="text-slate-400 hover:text-slate-700"><ArrowLeft size={18} /></Link>}
        <div className="flex-1 min-w-0">
          <div className="font-semibold truncate">{run.group} · {run.lesson_no}-dars{P ? ` — ${P.title}` : ""}</div>
          <div className={`text-xs ${proj ? "text-white/70" : "text-slate-500"}`}>
            {run.done_count}/{run.total} bosqich · {cur ? cur.title : ""}
          </div>
        </div>
        {/* Taymer — hozirgi bosqich */}
        <div className={`flex items-center gap-1.5 font-mono text-lg px-3 py-1 rounded-lg ${over ? "bg-rose-100 text-rose-700" : proj ? "bg-white/15" : "bg-brand-50 text-brand-700"}`}>
          <TimerIcon size={16} /> {over ? "-" : ""}{fmt(Math.abs(left))}
        </div>
        <button onClick={() => setProj(!proj)} title="Proyektor rejimi"
                className={`flex items-center gap-1 text-xs rounded-lg px-3 py-2 ${proj ? "bg-white/15" : "bg-slate-100 text-slate-700"}`}>
          {proj ? <MonitorOff size={15} /> : <Monitor size={15} />} {proj ? "Ustoz rejimi" : "Proyektor"}
        </button>
        {!proj && run.status === "running" && (
          <button onClick={() => setFinishing(true)} className="flex items-center gap-1 text-xs bg-emerald-600 text-white rounded-lg px-3 py-2">
            <Flag size={15} /> Yakunlash
          </button>
        )}
      </header>

      {err && <div className="mx-4 mt-3 text-sm text-rose-600">{err}</div>}

      <div className={`grid ${proj ? "md:grid-cols-[260px_1fr]" : "md:grid-cols-[320px_1fr]"} gap-4 p-4 max-w-7xl mx-auto`}>
        {/* ---- Bosqichlar ---- */}
        <aside className="space-y-2">
          {/* Telefon uchun: joriy bosqich kartasi (ro'yxat yig'ilgan) */}
          {!proj && (
            <div className="md:hidden bg-brand-600 text-white rounded-2xl p-4">
              <div className="text-[11px] opacity-80">Hozirgi bosqich · {run.current + 1}/{run.total}</div>
              <div className="font-semibold text-base leading-snug">{cur?.title}</div>
              {cur?.desc && <div className="text-xs opacity-90 mt-1">{cur.desc}</div>}
              <div className="flex items-center gap-2 mt-3">
                {run.status === "running" && (
                  <button onClick={nextStage} className="flex-1 bg-white text-brand-700 rounded-xl py-2.5 text-sm font-bold flex items-center justify-center gap-1">
                    <Check size={16} /> Bajarildi → keyingisi
                  </button>
                )}
                <button onClick={() => setStagesOpen(!stagesOpen)} className="bg-white/15 rounded-xl px-3 py-2.5 text-sm">{stagesOpen ? "Yashir" : "Ro'yxat"}</button>
              </div>
            </div>
          )}
          <div className={`${stagesOpen || proj ? "" : "hidden md:block"} space-y-2`}>
          <div className="text-xs font-semibold text-slate-500 uppercase">Dars bosqichlari</div>
          {run.stages.map((s, i) => (
            <div key={i} onClick={() => !proj && goTo(i)}
                 className={`rounded-xl border p-3 flex gap-2 items-start cursor-pointer ${i === run.current ? "border-brand-500 bg-brand-50" : s.done ? "border-emerald-200 bg-emerald-50/60" : "border-slate-200 bg-white"} ${s.carried ? "ring-1 ring-amber-300" : ""}`}>
              {!proj && (
                <button onClick={(e) => { e.stopPropagation(); toggleDone(i); }}
                        className={`w-5 h-5 mt-0.5 rounded border flex items-center justify-center shrink-0 ${s.done ? "bg-emerald-600 border-emerald-600 text-white" : "border-slate-300 bg-white"}`}>
                  {s.done && <Check size={13} />}
                </button>
              )}
              <div className="min-w-0 flex-1">
                <div className={`text-sm font-medium ${s.done ? "line-through text-slate-400" : "text-slate-800"}`}>{s.title} <span className="text-xs text-slate-400">· {s.min} daq</span></div>
                {!proj && <div className="text-[11px] text-slate-500 mt-0.5">{s.desc}</div>}
              </div>
            </div>
          ))}
          {!proj && run.status === "running" && (
            <button onClick={nextStage} className="hidden md:flex w-full bg-brand-600 text-white rounded-xl py-2.5 text-sm font-semibold items-center justify-center gap-1">
              Bosqich bajarildi → keyingisi <ChevronRight size={16} />
            </button>
          )}
          </div>
          {!proj && (
            <>
              <div className="text-xs font-semibold text-slate-500 uppercase mt-4 flex items-center gap-1"><Users size={13} /> O'quvchilar ({run.students?.length ?? 0})</div>
              <div className="flex flex-wrap gap-1">
                {(run.students || []).map((s) => <span key={s.id} className="text-[11px] bg-white border border-slate-200 rounded px-1.5 py-0.5">{s.name}</span>)}
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <Link to={`/teacher/lesson/${run.lesson_id}`} className="text-xs text-center bg-white border border-slate-200 rounded-lg py-2">Davomat / baho</Link>
                {canKahoot ? (
                  <button onClick={() => kahoot(run.lesson_no)} disabled={busy} className="text-xs bg-indigo-600 text-white rounded-lg py-2 flex items-center justify-center gap-1"><Gamepad2 size={14} /> Kahoot: bugungi</button>
                ) : (
                  <span className="text-[11px] text-center text-slate-400 border border-dashed border-slate-200 rounded-lg py-2">Kahoot: bu darsda savol yo'q</span>
                )}
                {canKahoot && run.lesson_no > 1 && (
                  <button onClick={() => kahoot(run.lesson_no - 1)} disabled={busy} className="col-span-2 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg py-2 flex items-center justify-center gap-1"><Gamepad2 size={14} /> Kahoot: o'tgan dars takrori ({run.lesson_no - 1}-dars)</button>
                )}
                <button onClick={openSend} className="col-span-2 text-xs bg-emerald-600 text-white rounded-lg py-2">📤 Topshiriq yuborish (o'quvchi ilovasiga)</button>
                <Link to="/teacher/check" className="col-span-2 text-xs text-center bg-white border border-slate-200 rounded-lg py-2">Tekshirish (writing / speaking)</Link>
              </div>
              {sendOpen && (
                <div className="bg-white border border-emerald-200 rounded-xl p-3 mt-2 space-y-2">
                  <div className="text-xs font-semibold text-slate-700">Rejadan nimani yuboramiz?</div>
                  {parts.length === 0 && <div className="text-xs text-slate-400">Yuklanmoqda…</div>}
                  {parts.map((p) => (
                    <label key={p.part} className="flex items-start gap-2 text-xs">
                      <input type="checkbox" checked={!!picked[p.part]} onChange={(e) => setPicked({ ...picked, [p.part]: e.target.checked })} className="mt-0.5" />
                      <span>{p.label} <span className={p.auto ? "text-emerald-600" : "text-violet-600"}>· {p.auto ? "avtomat" : "ustoz tekshiradi"}</span></span>
                    </label>
                  ))}
                  <div className="flex items-center gap-2 text-xs">Muddat: <input type="number" min={0} max={30} value={dueDays} onChange={(e) => setDueDays(Number(e.target.value))} className="w-14 border border-slate-200 rounded px-1 py-0.5" /> kun</div>
                  <button onClick={sendAssignments} disabled={busy} className="w-full bg-emerald-600 text-white rounded-lg py-2 text-xs font-semibold">Yuborish</button>
                  {sent && <div className="text-xs text-emerald-700">{sent}</div>}
                </div>
              )}
              <div className="text-xs font-semibold text-slate-500 uppercase mt-4">Maxfiy izoh (faqat siz)</div>
              <textarea value={notes} onChange={(e) => onNotes(e.target.value)} rows={4}
                        placeholder="Kim qiynaldi, nimani keyingi darsda takrorlash kerak…"
                        className="w-full text-sm border border-slate-200 rounded-lg p-2 bg-white" />
            </>
          )}
        </aside>

        {/* ---- Material ---- */}
        <main>
          <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1">
            {TABS.map((t) => (
              <button key={t.key} onClick={() => setTab(t.key)}
                      className={`px-3.5 py-2 text-sm whitespace-nowrap rounded-full border ${tab === t.key ? "bg-brand-600 text-white border-brand-600" : "bg-white text-slate-600 border-slate-200"}`}>{t.label}</button>
            ))}
          </div>
          {!P && <p className="text-sm text-slate-500">Reja matni topilmadi.</p>}
          {P && tab === "grammar" && (
            <div className={`space-y-4 ${big}`}>
              {(P.grammar?.intro ?? []).length > 0 && <Card title="Tushuntirish"><ul className="list-disc pl-5 space-y-1">{P.grammar.intro.map((t, i) => <li key={i}>{t}</li>)}</ul></Card>}
              {(P.grammar?.formulas ?? []).length > 0 && <Card title="Formulalar">
                <table className="w-full border-collapse"><tbody>
                  {P.grammar.formulas.map((f, i) => (
                    <tr key={i} className={i % 2 ? "bg-slate-50" : ""}>
                      <td className="border border-slate-200 px-2 py-1.5 font-semibold w-1/6">{f[0]}</td>
                      <td className="border border-slate-200 px-2 py-1.5 font-mono text-brand-700">{f[1]}</td>
                      <td className="border border-slate-200 px-2 py-1.5">{f[2]}</td>
                      <td className="border border-slate-200 px-2 py-1.5 text-slate-500">{f[3]}</td>
                    </tr>
                  ))}
                </tbody></table>
              </Card>}
              {!proj && (P.grammar?.presentation ?? []).length > 0 && <Card title="Ustoz–o'quvchi savol-javob"><table className="w-full"><tbody>{P.grammar.presentation.map((p, i) => <tr key={i}><td className="border border-slate-200 px-2 py-1 w-1/2">{p[0]}</td><td className="border border-slate-200 px-2 py-1 text-emerald-700">{p[1]}</td></tr>)}</tbody></table></Card>}
              {(P.grammar?.mistakes ?? []).length > 0 && <Card title="Tipik xatolar"><table className="w-full"><tbody>{P.grammar.mistakes.map((m, i) => <tr key={i}><td className="border border-slate-200 px-2 py-1 text-rose-600 line-through">{m[0]}</td><td className="border border-slate-200 px-2 py-1 text-emerald-700">{m[1]}</td>{!proj && <td className="border border-slate-200 px-2 py-1 text-slate-500">{m[2]}</td>}</tr>)}</tbody></table></Card>}
              {!proj && (P.grammar?.notes ?? []).length > 0 && <Card title="Ustoz uchun eslatma (maxfiy)"><ul className="list-disc pl-5">{P.grammar.notes.map((t, i) => <li key={i}>{t}</li>)}</ul></Card>}
            </div>
          )}
          {P && tab === "vocab" && (
            !P.vocab?.core ? <p className="text-sm text-slate-500">Bu darsda lug'at yo'q.</p> :
            <Card title={`CORE 20 — ${P.vocab_topic}`}>
              <table className={`w-full ${big}`}><thead><tr className="bg-slate-50"><th className="border border-slate-200 px-2 py-1 text-left">So'z</th><th className="border border-slate-200 px-2 py-1 text-left">O'qilishi</th><th className="border border-slate-200 px-2 py-1 text-left">Tarjima</th><th className="border border-slate-200 px-2 py-1 text-left">Misol</th></tr></thead>
                <tbody>{P.vocab.core.map((w, i) => <tr key={i} className={i % 2 ? "bg-slate-50/60" : ""}><td className="border border-slate-200 px-2 py-1 font-semibold">{w[0]}</td><td className="border border-slate-200 px-2 py-1 text-slate-500">{w[4] ? `/${w[4]}/` : ""}</td><td className="border border-slate-200 px-2 py-1">{w[1]}</td><td className="border border-slate-200 px-2 py-1">{w[2]}{!proj && w[3] ? <span className="text-slate-400"> — {w[3]}</span> : null}</td></tr>)}</tbody>
              </table>
            </Card>
          )}
          {P && tab === "class" && <ExList list={P.class_ex ?? []} proj={proj} show={showAns} setShow={setShowAns} prefix="c" big={big} />}
          {P && tab === "reading" && (readings(P).length ? (
            <div className={`space-y-4 ${big}`}>
              {readings(P).map((R, ri) => (
                <div key={ri} className="space-y-3">
                  <Card title={readings(P).length > 1 ? `${ri + 1}. ${R.title}` : R.title}>
                    {R.qtype && <p className="text-xs text-slate-500 mb-2">{R.qtype}</p>}
                    {(R.text ?? []).map((t, i) => <p key={i} className="mb-2 leading-relaxed">{t}</p>)}
                    {(R.paraphrases ?? []).length > 0 && (
                      <div className="mt-2 text-xs text-slate-600 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                        {(R.paraphrases ?? []).map((pp, i) => <div key={i}>{pp[0]} → {pp[1]}</div>)}
                      </div>
                    )}
                    {(R.glossary ?? []).length > 0 && (
                      <div className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-1 mt-2">{(R.glossary ?? []).join(" · ")}</div>
                    )}
                  </Card>
                  <ExList list={R.tasks ?? []} proj={proj} show={showAns} setShow={setShowAns} prefix={`r${ri}`} big={big} />
                </div>
              ))}
            </div>) : <p className="text-sm text-slate-500">Bu darsda reading yo'q.</p>)}
          {P && tab === "listening" && (listenings(P).length ? (
            <div className={`space-y-4 ${big}`}>
              {listenings(P).map((Ls, li) => (
                <div key={li} className="space-y-3">
                  <Card title={Ls.title || (Ls.audios ? `Audio ${Ls.audios}` : `Listening ${li + 1}`)}>
                    {Ls.qtype && <p className="text-xs text-slate-500 mb-2">{Ls.qtype}</p>}
                    {Ls.audios && Ls.title && <p className="text-xs text-slate-500 mb-2">Audio: {Ls.audios}</p>}
                    {(Ls.intro ?? []).map((t, i) => <p key={i} className="mb-2">{t}</p>)}
                    {/* Transkript — faqat ustozga, proyektorda yashiriladi */}
                    {!proj && (Ls.transcript ?? []).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-brand-600 cursor-pointer">Transkript</summary>
                        <div className="text-sm text-slate-600 mt-1 space-y-1">
                          {(Ls.transcript ?? []).map((t, i) => <p key={i}>{t}</p>)}
                        </div>
                      </details>
                    )}
                  </Card>
                  <ExList list={Ls.tasks ?? []} proj={proj} show={showAns} setShow={setShowAns} prefix={`l${li}`} big={big} />
                </div>
              ))}
            </div>) : <p className="text-sm text-slate-500">Bu darsda listening yo'q.</p>)}
          {P && tab === "home" && (
            <div className={`space-y-4 ${big}`}>
              {(P.homework_intro ?? []).map((t, i) => <p key={i} className="text-slate-700">{t}</p>)}
              <ExList list={P.homework ?? []} proj={proj} show={showAns} setShow={setShowAns} prefix="h" big={big} />
            </div>
          )}
        </main>
      </div>

      {/* ---- Yakunlash oynasi ---- */}
      {finishing && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-20" onClick={() => setFinishing(false)}>
          <div className="bg-white rounded-2xl p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="font-semibold text-lg mb-2">Darsni yakunlash</div>
            <p className="text-sm text-slate-600 mb-2">Bajarilgan: {run.done_count}/{run.total} bosqich.</p>
            {run.stages.some((s) => !s.done) && (
              <div className="text-sm bg-amber-50 text-amber-800 rounded-lg p-3 mb-3">
                Tugallanmagan qismlar keyingi darsga ko'chadi:
                <ul className="list-disc pl-5 mt-1">{run.stages.filter((s) => !s.done).map((s, i) => <li key={i}>{s.title}</li>)}</ul>
              </div>
            )}
            <label className="flex items-center gap-2 text-sm mb-4">
              <input type="checkbox" checked={advance} onChange={(e) => setAdvance(e.target.checked)} />
              Guruh rejada keyingi darsga o'tsin ({run.lesson_no + 1}-dars)
            </label>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setFinishing(false)} className="text-sm px-4 py-2 rounded-lg bg-slate-100">Bekor</button>
              <button onClick={finish} disabled={busy} className="text-sm px-4 py-2 rounded-lg bg-emerald-600 text-white">Yakunlash</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <h3 className="font-semibold text-slate-800 mb-2">{title}</h3>
      {children}
    </div>
  );
}

function fillBlank(item: string, answer: string): React.ReactNode {
  const parts = item.split(/_{2,}|…{2,}|\.{4,}/);
  if (parts.length < 2) return <>{item} <span className="text-emerald-700 font-medium">→ {answer}</span></>;
  const answers = parts.length > 2 && answer.includes(" / ") ? answer.split(" / ") : [answer];
  return <>{parts.map((p, k) => <span key={k}>{p}{k < parts.length - 1 && <span className="text-emerald-700 font-semibold border-b border-emerald-500 px-0.5">{answers[k] ?? answers[answers.length - 1]}</span>}</span>)}</>;
}

/** Bosqich vaqti tugaganda bir marta signal beradi: qisqa "bip" va
 * telefonda tebranish. Bosqich almashganda qayta qurollanadi. Ovoz
 * brauzer tomonidan to'silsa — jim o'tadi, xato chiqarmaydi. */
function useStageAlarm(stageIdx: number, left: number) {
  const fired = useRef<number | null>(null);
  useEffect(() => {
    if (left > 0 || fired.current === stageIdx) return;
    fired.current = stageIdx;
    try {
      const Ctx = window.AudioContext
        || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (Ctx) {
        const ctx = new Ctx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.frequency.value = 880;
        gain.gain.value = 0.15;
        osc.connect(gain).connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
        setTimeout(() => ctx.close().catch(() => {}), 800);
      }
    } catch {
      /* brauzer ovozga ruxsat bermadi — muhim emas */
    }
    try {
      navigator.vibrate?.([200, 100, 200]);
    } catch {
      /* tebranishni qo'llamaydi */
    }
  }, [stageIdx, left]);
  useEffect(() => { fired.current = null; }, [stageIdx]);
}

/** Eski (birlik) va yangi (ko'plik) reja kalitlarini bitta ro'yxatga
 * keltiradi — IELTS 1.0-4.0 da "reading", IELTS 5.0 da "readings". */
function readings(P: Plan): PlanReading[] {
  if (P.readings && P.readings.length) return P.readings;
  return P.reading ? [P.reading] : [];
}
function listenings(P: Plan): PlanListen[] {
  if (P.listenings && P.listenings.length) return P.listenings;
  return P.listening ? [P.listening] : [];
}

function ExList({ list, proj, show, setShow, prefix, big }: {
  list: Ex[]; proj: boolean; show: Record<string, boolean>;
  setShow: (v: Record<string, boolean>) => void; prefix: string; big: string;
}) {
  return (
    <div className={`space-y-3 ${big}`}>
      {list.map((ex, i) => {
        const k = `${prefix}${i}`;
        const on = !proj && show[k];
        return (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-semibold text-slate-800">{i + 1}. {ex.title}</div>
                {ex.type && <div className="text-xs text-slate-500">{ex.type}</div>}
              </div>
              {!proj && ex.answers && (
                <button onClick={() => setShow({ ...show, [k]: !show[k] })} className="text-xs text-brand-600 whitespace-nowrap">
                  {on ? "Javobni yashir" : "Javobni ko'rsat"}
                </button>
              )}
            </div>
            {ex.instr && <p className="text-slate-700 mt-2">{ex.instr}</p>}
            {ex.box && <div className="text-xs bg-slate-50 rounded px-2 py-1 mt-2 text-slate-600">{ex.box.join(" · ")}</div>}
            {/* Jadval/juftlik/oqim ko'rinishlari — reja ekranidagi bilan bir xil */}
            {ex.layout ? <div className="mt-2"><ExBody ex={ex} show={on} /></div> : null}
            {!ex.layout && ex.items && (
              <ol className="list-decimal pl-5 mt-2 space-y-0.5">
                {ex.items.map((it, j) => {
                  const ans = on && Array.isArray(ex.answers) ? ex.answers[j] : undefined;
                  return <li key={j}>{ans !== undefined ? fillBlank(it, ans) : it}</li>;
                })}
              </ol>
            )}
            {!ex.layout && on && (!ex.items || !Array.isArray(ex.answers)) && ex.answers && (
              <div className="text-emerald-700 mt-2">{Array.isArray(ex.answers) ? ex.answers.join("; ") : ex.answers}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
