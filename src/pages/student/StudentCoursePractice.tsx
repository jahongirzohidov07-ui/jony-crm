import CourseCollaboration from "../../components/CourseCollaboration";
import Answer, { type Question, type Result, type Drafts } from "../../components/CourseAnswer";
import CourseDailySession from "../../components/CourseDailySession";
import { CourseMotivation, CourseCheckpoint, type CheckpointStatus, type PlanStep } from "../../components/CourseMotivation";
import CoursePortfolio from "../../components/CoursePortfolio";
import { CourseJourney } from "../../components/CourseJourney";
import { CourseSpeaking } from "../../components/CourseSpeaking";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, BookOpen } from "lucide-react";
import { api } from "../../lib/api";
import { useLearningLanguage } from "../../lib/lang";
import CourseLessonAudio from "../../components/CourseLessonAudio";

type Section = { id: string; title: string; skill: string; text?: string; questions: Question[] };
type Lesson = { lesson: number; title: string; level?: string; question_count: number; completed?: boolean; submitted_count?: number; correct_count?: number };
type Detail = { language: string; lesson: number; title: string; audio_url: string; sections: Section[]; answers?: Record<string, {answer: string; result: Result}> };
const labels: Record<string, string> = { reading: "O‘qish", listening: "Tinglash", grammar: "Grammatika", homework: "Haftalik mashq", writing: "Yozish", speaking: "Gapirish" };

export default function StudentCoursePractice() {
  const language = useLearningLanguage();
  if (language !== "en" && language !== "de") return <div className="p-5"><Link to="/student">← Bosh sahifa</Link><p className="mt-4">Bu kurs uchun bosh sahifadan ingliz yoki nemis tilini tanlang.</p></div>;
  return <Course key={language} language={language}/>;
}
function Course({ language }: { language: string }) {
  const [params, setParams] = useSearchParams();
  const drafts = useRef<Drafts>(new Map());
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const listingRequest = useRef(0);
  const alive = useRef(true);
  const checkpointLauncher = useRef<HTMLElement | null>(null);
  const lessonHeading = useRef<HTMLHeadingElement | null>(null);
  const focusLesson = useRef(false);
  useEffect(() => {alive.current = true; return () => {alive.current = false;};}, []);
  const [selected, setSelected] = useState<number | null>(null);
  const positionQueue = useRef<Promise<unknown>>(Promise.resolve());
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [motivationVersion, setMotivationVersion] = useState(0);
  const [section, setSection] = useState(params.get("section") || "all");
  const initialView = params.get("view");
  const [view, setView] = useState(params.get("action") === "review" ? "today" : initialView && ["today", "lesson", "journey", "portfolio", "pair", "session"].includes(initialView) ? initialView : (params.has("lesson") || params.has("section")) ? "lesson" : "today");
  const [portfolioEntry, setPortfolioEntry] = useState<string | undefined>();
  const viewHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { viewHeading.current?.focus({preventScroll: true}); }, [view]);
  const [targetQuestion] = useState<string | null>(params.get("question"));
  const [checkpoint, setCheckpoint] = useState<number | null>(null);
  const [checkpointStates, setCheckpointStates] = useState<CheckpointStatus[]>([]);
  useEffect(() => {
    let active = true; const request = ++listingRequest.current; setListLoading(true);
    api.fresh<{ lessons: Lesson[]; resume_lesson?: number }>(`/student/course-practice?language=${language}`).then(r => { if (active && request === listingRequest.current) { setListLoading(false); setLessons(r.lessons); setSelected(current => current ?? (r.lessons.some(l => l.lesson === Number(params.get("lesson"))) ? Number(params.get("lesson")) : r.resume_lesson || 1)); } }).catch(e => { if (active && request === listingRequest.current) {setListLoading(false); setError(e.message);} });
    return () => { active = false; };
  }, [language, reload]);
  useEffect(() => {
    let active = true;
    if (selected === null || view !== "lesson") return;
    setDetail(null); setError("");
    api.fresh<Detail>(`/student/course-practice/${selected}?language=${language}`).then(r => { if (active) { for (const [id, saved] of Object.entries(r.answers || {})) { const key = `${language}:${selected}:${id}`; if (!drafts.current.has(key)) drafts.current.set(key, saved); } setDetail(r); } }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [language, selected, reload, view]);
  useEffect(() => {
    if (selected === null) return;
    positionQueue.current = positionQueue.current.catch(() => {}).then(() => api.post("/student/course-practice/position", {language, lesson: selected})).catch(() => { setError("Dars joyini saqlab bo‘lmadi. Qayta urinib ko‘ring."); });
  }, [language, selected, reload]);
  useEffect(() => {if (detail?.lesson === selected && lessonHeading.current && focusLesson.current && view === "lesson") {lessonHeading.current?.focus(); focusLesson.current = false;}}, [detail, selected, view]);
  function openPlanStep(_step: PlanStep) { setParams({view:"session"}, {replace:true}); setView("session"); }
  useEffect(() => {
    if (!targetQuestion || !detail || detail.lesson !== selected || view !== "lesson") return;
    const frame = requestAnimationFrame(() => {
      const el = document.getElementById(`course-question-${targetQuestion}`);
      if (el) { el.scrollIntoView({behavior: "smooth", block: "start"}); el.focus({preventScroll: true}); }
    });
    return () => cancelAnimationFrame(frame);
  }, [targetQuestion, detail, selected, view]);
  function refreshProgress() {
    setMotivationVersion(n => n + 1);
    const request = ++listingRequest.current;
    api.fresh<{ lessons: Lesson[]; resume_lesson?: number }>(`/student/course-practice?language=${language}`).then(r => {if (alive.current && request === listingRequest.current) {setLessons(r.lessons); setListLoading(false);}}).catch(() => {});
  }
  const progress = lessons.find(l => l.lesson === selected);
  const sections = detail?.sections || [];
  const skills = [...new Set(sections.map(s => s.skill))];
  const shown = skills.includes(section) ? section : "all";
  if (view === "session") return <CourseDailySession key={language} language={language} onAnswerSaved={(lesson,id) => {drafts.current.delete(`${language}:${lesson}:${id}`); if(alive.current) setReload(n=>n+1);}} onExit={() => {setParams({view:"today"}, {replace:true}); setView("today"); refreshProgress();}} onLesson={n => {setParams({view:"lesson",lesson:String(n)}, {replace:true}); setSelected(n); setView("lesson"); refreshProgress();}}/>;
  return <main className="mx-auto max-w-2xl space-y-4 p-4 pb-24 text-slate-900">
    <Link to="/student" className="inline-flex items-center gap-2 text-sm text-sky-700"><ArrowLeft size={16}/>Bosh sahifa</Link>
    <header className="rounded-2xl bg-sky-900 p-5 text-white"><BookOpen className="mb-2"/><h1 className="text-xl font-bold">{language === "de" ? "Deutsch B1" : "English Intensive"}</h1><p className="mt-1 text-sm">Bugungi rejangizdan boshlang yoki ustoz belgilagan darsni tanlang.</p></header>
    <nav aria-label="Kurs ko‘rinishi" className="grid grid-cols-2 gap-2 sm:grid-cols-3"><button aria-pressed={view === "today"} onClick={() => setView("today")} className={`rounded-xl border p-3 text-sm font-semibold ${view === "today" ? "bg-sky-800 text-white" : "bg-white"}`}>Bugungi rejam</button><button aria-pressed={view === "lesson"} onClick={() => setView("lesson")} className={`flex-1 rounded-xl border p-3 text-sm font-semibold ${view === "lesson" ? "bg-sky-800 text-white" : "bg-white"}`}>Dars va mashqlar</button><button aria-pressed={view === "journey"} onClick={() => setView("journey")} className={`flex-1 rounded-xl border p-3 text-sm font-semibold ${view === "journey" ? "bg-indigo-800 text-white" : "bg-white"}`}>Mening xaritam</button><button aria-pressed={view === "portfolio"} onClick={() => setView("portfolio")} className={`flex-1 rounded-xl border p-3 text-sm font-semibold ${view === "portfolio" ? "bg-indigo-800 text-white" : "bg-white"}`}>Ijodiy ishlarim</button><button aria-pressed={view === "pair"} onClick={() => setView("pair")} className={`flex-1 rounded-xl border p-3 text-sm font-semibold ${view === "pair" ? "bg-indigo-800 text-white" : "bg-white"}`}>Juftlik vazifasi</button></nav>
    <h2 ref={viewHeading} tabIndex={-1} className="text-lg font-bold">{{today:"Bugungi rejam",lesson:"Dars va mashqlar",journey:"Mening xaritam",portfolio:"Ijodiy ishlarim",pair:"Juftlik vazifasi"}[view]}</h2>
    <div hidden={view !== "today"}><CourseMotivation key={language} language={language} refresh={motivationVersion} onCheckpoints={setCheckpointStates} onAction={openPlanStep} onPair={() => setView("pair")} initialReview={params.get("action") === "review"}/></div>
    {checkpoint !== null && <CourseCheckpoint key={`${language}:${checkpoint}`} language={language} week={checkpoint} onClose={() => {setCheckpoint(null); requestAnimationFrame(() => checkpointLauncher.current?.focus());}} onSaved={refreshProgress}/>}
    {view === "journey" && listLoading && <p role="status">Xarita yuklanmoqda…</p>}
    {view === "journey" && !listLoading && !lessons.length && !error && <p>Kurs darslari hozircha topilmadi.</p>}
    {view === "journey" && lessons.length > 0 && <CourseJourney checkpoints={checkpointStates} language={language} lessons={lessons} selected={selected} onSelect={n => {focusLesson.current = true; setSelected(n); setView("lesson");}} onCheckpoint={week => {checkpointLauncher.current = document.activeElement instanceof HTMLElement ? document.activeElement : null; setCheckpoint(week);}}/>}
    {(view === "lesson" || view === "portfolio" || view === "pair") && <label className="block font-semibold">Dars<select aria-label="Dars" className="mt-2 block w-full min-w-0 rounded-xl border bg-white p-3 text-sm" value={selected ?? 1} onChange={e => {setPortfolioEntry(undefined); setSelected(Number(e.target.value));}}>
      {lessons.length ? lessons.map(l => <option key={l.lesson} value={l.lesson}>{l.lesson}. {l.title}{l.level ? ` · ${l.level}` : ""}</option>) : <option value={1}>Yuklanmoqda…</option>}
    </select></label>}
    {view === "pair" && selected !== null && <CourseCollaboration key={`${language}:${selected}`} language={language} lesson={selected}/>}
    {view === "portfolio" && selected !== null && <CoursePortfolio key={`${language}:${selected}`} language={language} lesson={selected} initialEntryId={portfolioEntry} onOpenWork={(lesson, id) => {setPortfolioEntry(id); setSelected(lesson);}} onSaved={refreshProgress}/>}
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">{error}<button className="ml-3 underline" onClick={() => setReload(n => n + 1)}>Qayta urinish</button></div>}
    {view === "lesson" && !detail && !error && <p role="status">Dars yuklanmoqda…</p>}
    {view === "lesson" && detail && detail.lesson === selected && selected !== null && <div key={`${language}-${selected}`} className="space-y-4">
      <h2 ref={lessonHeading} tabIndex={-1} className="text-lg font-bold">{detail.title}</h2>
      {progress && <p className="text-sm text-slate-600" aria-label="Darsdagi natija">Yuborilgan: {progress.submitted_count || 0} / {progress.question_count} · Avtomatik tekshiruvda to‘g‘ri: {progress.correct_count || 0}</p>}
      <CourseLessonAudio key={`${language}-${selected}`} course={language === "de" ? "german" : "intensive"} lesson={selected} title={detail.title}/>
      <p className="text-sm text-slate-600">Dars va uyga vazifa: quyidagi bo‘limlarni ketma-ket bajaring. Yuborilgan javoblar qayta kirganda ham ko‘rinadi. Ochiq javoblar namuna bilan o‘zini tekshirish uchun.</p>
      <div aria-label="Mashq bo‘limlari" className="flex flex-wrap gap-2">{["all", ...skills].map(s => <button key={s} aria-pressed={shown === s} onClick={() => setSection(s)} className={`rounded-full border px-4 py-2 text-sm ${shown === s ? "bg-sky-800 text-white" : "bg-white"}`}>{s === "all" ? "Hammasi" : labels[s] || s}</button>)}</div>
      {sections.filter(s => shown === "all" || s.skill === shown).map(s => <SectionPractice key={s.id} section={s} language={language} lesson={selected} onSaved={refreshProgress} drafts={drafts.current} targetQuestion={targetQuestion}/>)}
      <div className="flex justify-between gap-3"><button disabled={selected === 1} onClick={() => setSelected(n => Math.max(1, (n || 1) - 1))} className="rounded-xl border p-3 disabled:opacity-40">← Oldingi dars</button><button disabled={selected >= lessons.length} onClick={() => setSelected(n => (n || 1) + 1)} className="rounded-xl bg-sky-800 p-3 text-white disabled:opacity-40">Keyingi dars →</button></div>
    </div>}
  </main>;
}
function SectionPractice({ section: s, language, lesson, onSaved, drafts, targetQuestion }: { section: Section; language: string; lesson: number; onSaved: () => void; drafts: Drafts; targetQuestion: string | null }) {
  const [page, setPage] = useState(0);
  const pages = Math.ceil(s.questions.length / 10);
  useEffect(() => {if (!targetQuestion) return; const frame = requestAnimationFrame(() => {const el = document.getElementById(`course-question-${targetQuestion}`); if (el) {el.scrollIntoView({block:"start",behavior:"smooth"}); el.focus({preventScroll:true});}}); return () => cancelAnimationFrame(frame);}, [page, targetQuestion]);
  useEffect(() => { const index = s.questions.findIndex(q => q.id === targetQuestion); if (index >= 0) setPage(Math.floor(index / 10)); }, [s.questions, targetQuestion]);
  return <section className="space-y-3 rounded-2xl border bg-white p-4">
    <h3 className="font-bold">{s.title}</h3>
    {s.text && <p className="whitespace-pre-line break-words text-sm leading-7" lang={language}>{s.text}</p>}
    <p className="text-xs text-slate-500">{s.questions.length} ta mashq{pages > 1 ? ` · ${page + 1} / ${pages} sahifa` : ""}</p>
    {s.questions.slice(page * 10, page * 10 + 10).map((q, i) => s.skill === "speaking" && language === "en"
      ? <div key={q.id} id={`course-question-${q.id}`} tabIndex={-1}><CourseSpeaking lesson={lesson} questionId={q.id} previous={drafts.get(`${language}:${lesson}:${q.id}`)?.answer} onSaved={(answer, reply) => { drafts.set(`${language}:${lesson}:${q.id}`, {answer, result: {correct: null, expected: [], explanation: reply, saved: true}}); onSaved(); }}/></div>
      : <Answer key={q.id} question={q} number={page * 10 + i + 1} language={language} lesson={lesson} onSaved={onSaved} drafts={drafts}/>)}
    {pages > 1 && <div className="flex justify-between gap-2 pt-3"><button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="rounded-lg border p-2 text-sm disabled:opacity-40">← Oldingi 10 ta</button><button disabled={page + 1 >= pages} onClick={() => setPage(p => p + 1)} className="rounded-lg border p-2 text-sm disabled:opacity-40">Keyingi 10 ta →</button></div>}
  </section>;
}
