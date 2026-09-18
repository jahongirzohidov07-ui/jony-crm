import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, Check, ChevronRight, Monitor, MonitorOff, Users, Gamepad2, Flag, Timer as TimerIcon,
} from "lucide-react";
import { api } from "../../lib/api";

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
type Ex = { title: string; type?: string; instr?: string; items?: string[]; answers?: string[] | string; note?: string; box?: string[] };
type Plan = {
  no: number; title: string; grammar_topic: string; vocab_topic: string;
  grammar: { intro: string[]; formulas: string[][]; presentation: [string, string][]; notes: string[]; mistakes: string[][] };
  vocab: { core: string[][]; strong: string[][]; super: string[][] };
  class_ex: Ex[];
  reading?: { title: string; text: string[]; glossary: string[]; tasks: Ex[] };
  listening?: { audios: string; intro: string[]; tasks: Ex[] };
  homework_intro: string[]; homework: Ex[];
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
  async function kahoot() {
    if (!run) return;
    setBusy(true);
    try {
      const g = await api.post<{ id: number }>("/live/games",
        { course: run.course, lesson_no: run.lesson_no, group_id: run.group_id, mode: "mixed", count: 20, seconds: 20 });
      window.open(`/live/${g.id}`, "_blank");
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

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
  const cur = run.stages[run.current];
  const startedMs = run.stage_started_at ? new Date(run.stage_started_at + (run.stage_started_at.endsWith("Z") ? "" : "Z")).getTime() : now;
  const elapsed = (now - startedMs) / 1000;
  const left = (cur?.min ?? 0) * 60 - elapsed;
  const over = left < 0;
  const big = proj ? "text-lg md:text-xl" : "text-sm";

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
            <button onClick={nextStage} className="w-full bg-brand-600 text-white rounded-xl py-2.5 text-sm font-semibold flex items-center justify-center gap-1">
              Bosqich bajarildi → keyingisi <ChevronRight size={16} />
            </button>
          )}
          {!proj && (
            <>
              <div className="text-xs font-semibold text-slate-500 uppercase mt-4 flex items-center gap-1"><Users size={13} /> O'quvchilar ({run.students?.length ?? 0})</div>
              <div className="flex flex-wrap gap-1">
                {(run.students || []).map((s) => <span key={s.id} className="text-[11px] bg-white border border-slate-200 rounded px-1.5 py-0.5">{s.name}</span>)}
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <Link to={`/teacher/lesson/${run.lesson_id}`} className="text-xs text-center bg-white border border-slate-200 rounded-lg py-2">Davomat / baho</Link>
                <button onClick={kahoot} disabled={busy} className="text-xs bg-indigo-600 text-white rounded-lg py-2 flex items-center justify-center gap-1"><Gamepad2 size={14} /> Kahoot</button>
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
          <div className="flex gap-1 border-b border-slate-200 mb-3 overflow-x-auto">
            {TABS.map((t) => (
              <button key={t.key} onClick={() => setTab(t.key)}
                      className={`px-3 py-2 text-sm whitespace-nowrap border-b-2 -mb-px ${tab === t.key ? "border-brand-600 text-brand-700 font-medium" : "border-transparent text-slate-500"}`}>{t.label}</button>
            ))}
          </div>
          {!P && <p className="text-sm text-slate-500">Reja matni topilmadi.</p>}
          {P && tab === "grammar" && (
            <div className={`space-y-4 ${big}`}>
              <Card title="Tushuntirish"><ul className="list-disc pl-5 space-y-1">{P.grammar.intro.map((t, i) => <li key={i}>{t}</li>)}</ul></Card>
              <Card title="Formulalar">
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
              </Card>
              {!proj && <Card title="Ustoz–o'quvchi savol-javob"><table className="w-full"><tbody>{P.grammar.presentation.map((p, i) => <tr key={i}><td className="border border-slate-200 px-2 py-1 w-1/2">{p[0]}</td><td className="border border-slate-200 px-2 py-1 text-emerald-700">{p[1]}</td></tr>)}</tbody></table></Card>}
              <Card title="Tipik xatolar"><table className="w-full"><tbody>{P.grammar.mistakes.map((m, i) => <tr key={i}><td className="border border-slate-200 px-2 py-1 text-rose-600 line-through">{m[0]}</td><td className="border border-slate-200 px-2 py-1 text-emerald-700">{m[1]}</td>{!proj && <td className="border border-slate-200 px-2 py-1 text-slate-500">{m[2]}</td>}</tr>)}</tbody></table></Card>
              {!proj && P.grammar.notes?.length > 0 && <Card title="Ustoz uchun eslatma (maxfiy)"><ul className="list-disc pl-5">{P.grammar.notes.map((t, i) => <li key={i}>{t}</li>)}</ul></Card>}
            </div>
          )}
          {P && tab === "vocab" && (
            <Card title={`CORE 20 — ${P.vocab_topic}`}>
              <table className={`w-full ${big}`}><thead><tr className="bg-slate-50"><th className="border border-slate-200 px-2 py-1 text-left">So'z</th><th className="border border-slate-200 px-2 py-1 text-left">O'qilishi</th><th className="border border-slate-200 px-2 py-1 text-left">Tarjima</th><th className="border border-slate-200 px-2 py-1 text-left">Misol</th></tr></thead>
                <tbody>{P.vocab.core.map((w, i) => <tr key={i} className={i % 2 ? "bg-slate-50/60" : ""}><td className="border border-slate-200 px-2 py-1 font-semibold">{w[0]}</td><td className="border border-slate-200 px-2 py-1 text-slate-500">{w[4] ? `/${w[4]}/` : ""}</td><td className="border border-slate-200 px-2 py-1">{w[1]}</td><td className="border border-slate-200 px-2 py-1">{w[2]}{!proj && w[3] ? <span className="text-slate-400"> — {w[3]}</span> : null}</td></tr>)}</tbody>
              </table>
            </Card>
          )}
          {P && tab === "class" && <ExList list={P.class_ex} proj={proj} show={showAns} setShow={setShowAns} prefix="c" big={big} />}
          {P && tab === "reading" && (P.reading ? (
            <div className={`space-y-4 ${big}`}>
              <Card title={P.reading.title}>{P.reading.text.map((p, i) => <p key={i} className="mb-2 leading-relaxed">{p}</p>)}
                <div className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-1 mt-2">{P.reading.glossary.join(" · ")}</div></Card>
              <ExList list={P.reading.tasks} proj={proj} show={showAns} setShow={setShowAns} prefix="r" big={big} />
            </div>) : <p className="text-sm text-slate-500">Bu darsda reading yo'q.</p>)}
          {P && tab === "listening" && (P.listening ? (
            <div className={`space-y-4 ${big}`}>
              <Card title={`Audio ${P.listening.audios}`}>{P.listening.intro.map((t, i) => <p key={i} className="mb-2">{t}</p>)}</Card>
              <ExList list={P.listening.tasks} proj={proj} show={showAns} setShow={setShowAns} prefix="l" big={big} />
            </div>) : <p className="text-sm text-slate-500">Bu darsda listening yo'q.</p>)}
          {P && tab === "home" && (
            <div className={`space-y-4 ${big}`}>
              {P.homework_intro.map((t, i) => <p key={i} className="text-slate-700">{t}</p>)}
              <ExList list={P.homework} proj={proj} show={showAns} setShow={setShowAns} prefix="h" big={big} />
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
            {ex.items && (
              <ol className="list-decimal pl-5 mt-2 space-y-0.5">
                {ex.items.map((it, j) => {
                  const ans = on && Array.isArray(ex.answers) ? ex.answers[j] : undefined;
                  return <li key={j}>{ans !== undefined ? fillBlank(it, ans) : it}</li>;
                })}
              </ol>
            )}
            {on && (!ex.items || !Array.isArray(ex.answers)) && ex.answers && (
              <div className="text-emerald-700 mt-2">{Array.isArray(ex.answers) ? ex.answers.join("; ") : ex.answers}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
