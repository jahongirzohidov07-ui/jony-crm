import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle2 } from "lucide-react";
import { api } from "../../lib/api";
import { useLearningLanguage } from "../../lib/lang";
import CourseLessonAudio from "../../components/CourseLessonAudio";

type Question = { id: string; prompt: string; mode: "exact" | "self"; options?: string[] };
type Section = { id: string; title: string; skill: string; text?: string; questions: Question[] };
type Lesson = { lesson: number; title: string; level?: string; question_count: number; completed?: boolean; submitted_count?: number; correct_count?: number };
type Detail = { language: string; lesson: number; title: string; audio_url: string; sections: Section[] };
type Result = { correct: boolean | null; expected: string[]; explanation: string; criteria?: string[]; saved: boolean; transcript?: string };
type Drafts = Map<string, { answer: string; result: Result | null }>;
const labels: Record<string, string> = { reading: "O‘qish", listening: "Tinglash", grammar: "Grammatika", homework: "Haftalik mashq", writing: "Yozish", speaking: "Gapirish" };

export default function StudentCoursePractice() {
  const language = useLearningLanguage();
  if (language !== "en" && language !== "de") return <div className="p-5"><Link to="/student">← Bosh sahifa</Link><p className="mt-4">Bu kurs uchun bosh sahifadan ingliz yoki nemis tilini tanlang.</p></div>;
  return <Course key={language} language={language}/>;
}
function Course({ language }: { language: string }) {
  const [params] = useSearchParams();
  const drafts = useRef<Drafts>(new Map());
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selected, setSelected] = useState(1);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [section, setSection] = useState(params.get("section") || "all");
  useEffect(() => {
    let active = true;
    api.fresh<{ lessons: Lesson[] }>(`/student/course-practice?language=${language}`).then(r => { if (active) setLessons(r.lessons); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [language, reload]);
  useEffect(() => {
    let active = true;
    setDetail(null); setError("");
    api.fresh<Detail>(`/student/course-practice/${selected}?language=${language}`).then(r => { if (active) setDetail(r); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [language, selected, reload]);
  function refreshProgress() {
    api.fresh<{ lessons: Lesson[] }>(`/student/course-practice?language=${language}`).then(r => setLessons(r.lessons)).catch(() => {});
  }
  const progress = lessons.find(l => l.lesson === selected);
  const sections = detail?.sections || [];
  const skills = [...new Set(sections.map(s => s.skill))];
  const shown = skills.includes(section) ? section : "all";
  return <main className="mx-auto max-w-2xl space-y-4 p-4 pb-24 text-slate-900">
    <Link to="/student" className="inline-flex items-center gap-2 text-sm text-sky-700"><ArrowLeft size={16}/>Bosh sahifa</Link>
    <header className="rounded-2xl bg-sky-900 p-5 text-white"><BookOpen className="mb-2"/><h1 className="text-xl font-bold">{language === "de" ? "Deutsch B1" : "English Intensive"}</h1><p className="mt-2 text-sm">Darsni tanlang, audioni tinglang va yangi mashqlarni bajaring. Javoblaringiz akkauntingizda saqlanadi.</p></header>
    <label className="block font-semibold">Dars<select aria-label="Dars" className="mt-2 block w-full min-w-0 rounded-xl border bg-white p-3 text-sm" value={selected} onChange={e => setSelected(Number(e.target.value))}>
      {lessons.length ? lessons.map(l => <option key={l.lesson} value={l.lesson}>{l.lesson}. {l.title}{l.level ? ` · ${l.level}` : ""}</option>) : <option value={1}>Yuklanmoqda…</option>}
    </select></label>
    {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">{error}<button className="ml-3 underline" onClick={() => setReload(n => n + 1)}>Qayta urinish</button></div>}
    {!detail && !error && <p role="status">Dars yuklanmoqda…</p>}
    {detail && <div key={`${language}-${selected}`} className="space-y-4">
      <h2 className="text-lg font-bold">{detail.title}</h2>
      {progress && <p className="text-sm text-slate-600" aria-label="Darsdagi natija">Yuborilgan: {progress.submitted_count || 0} / {progress.question_count} · Avtomatik tekshiruvda to‘g‘ri: {progress.correct_count || 0}</p>}
      <CourseLessonAudio key={`${language}-${selected}`} course={language === "de" ? "german" : "intensive"} lesson={selected} title={detail.title}/>
      <div aria-label="Mashq bo‘limlari" className="flex flex-wrap gap-2">{["all", ...skills].map(s => <button key={s} aria-pressed={shown === s} onClick={() => setSection(s)} className={`rounded-full border px-4 py-2 text-sm ${shown === s ? "bg-sky-800 text-white" : "bg-white"}`}>{s === "all" ? "Hammasi" : labels[s] || s}</button>)}</div>
      {sections.filter(s => shown === "all" || s.skill === shown).map(s => <SectionPractice key={s.id} section={s} language={language} lesson={selected} onSaved={refreshProgress} drafts={drafts.current}/>)}
      <div className="flex justify-between gap-3"><button disabled={selected === 1} onClick={() => setSelected(n => n - 1)} className="rounded-xl border p-3 disabled:opacity-40">← Oldingi dars</button><button disabled={selected >= lessons.length} onClick={() => setSelected(n => n + 1)} className="rounded-xl bg-sky-800 p-3 text-white disabled:opacity-40">Keyingi dars →</button></div>
    </div>}
  </main>;
}
function SectionPractice({ section: s, language, lesson, onSaved, drafts }: { section: Section; language: string; lesson: number; onSaved: () => void; drafts: Drafts }) {
  const [page, setPage] = useState(0);
  const pages = Math.ceil(s.questions.length / 10);
  return <section className="space-y-3 rounded-2xl border bg-white p-4">
    <h3 className="font-bold">{s.title}</h3>
    {s.text && <p className="whitespace-pre-line break-words text-sm leading-7" lang={language}>{s.text}</p>}
    <p className="text-xs text-slate-500">{s.questions.length} ta mashq{pages > 1 ? ` · ${page + 1} / ${pages} sahifa` : ""}</p>
    {s.questions.slice(page * 10, page * 10 + 10).map((q, i) => <Answer key={q.id} question={q} number={page * 10 + i + 1} language={language} lesson={lesson} onSaved={onSaved} drafts={drafts}/>)}
    {pages > 1 && <div className="flex justify-between gap-2 pt-3"><button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="rounded-lg border p-2 text-sm disabled:opacity-40">← Oldingi 10 ta</button><button disabled={page + 1 >= pages} onClick={() => setPage(p => p + 1)} className="rounded-lg border p-2 text-sm disabled:opacity-40">Keyingi 10 ta →</button></div>}
  </section>;
}
function Answer({ question: q, number, language, lesson, onSaved, drafts }: { question: Question; number: number; language: string; lesson: number; onSaved: () => void; drafts: Drafts }) {
  const draftKey = `${language}:${lesson}:${q.id}`;
  const [answer, updateAnswer] = useState(drafts.get(draftKey)?.answer || "");
  const [result, updateResult] = useState<Result | null>(drafts.get(draftKey)?.result || null);
  function setAnswer(value: string) { updateAnswer(value); drafts.set(draftKey, {answer: value, result: drafts.get(draftKey)?.result || null}); }
  function setResult(value: Result | null) { updateResult(value); drafts.set(draftKey, {answer: drafts.get(draftKey)?.answer || answer, result: value}); }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit() {
    if (!answer.trim() || busy) return;
    setBusy(true); setError("");
    try { setResult(await api.post<Result>("/student/course-practice/answer", { language, lesson, question_id: q.id, answer })); onSaved(); }
    catch (e) { setError(e instanceof Error ? e.message : "Saqlashda xato. Qayta urinib ko‘ring."); }
    finally { setBusy(false); }
  }
  return <div className="space-y-3 border-t pt-4">
    <p className="whitespace-pre-line break-words text-sm font-medium" lang={language}>{number}. {q.prompt}</p>
    {q.mode === "self" && <p className="text-xs text-slate-500">Ochiq javob: yozib yuboring, so‘ng namuna va mezonlar bilan solishtiring. Avtomatik baho qo‘yilmaydi.</p>}
    {q.mode === "self" && !!q.options?.length && <ul className="space-y-1 rounded-xl bg-slate-50 p-3 text-sm">{q.options.map((o, i) => <li key={i}>{o}</li>)}</ul>}
    {q.mode === "exact" && q.options?.length ? <div className="grid gap-2">{q.options.map((o, i) => <label key={i} className="flex items-start gap-2 rounded-lg border p-3 text-sm"><input type="radio" name={`${lesson}-${q.id}`} disabled={!!result || busy} checked={answer === o} onChange={() => setAnswer(o)}/><span>{o}</span></label>)}</div> : <textarea aria-label={`${number}-savol javobi`} lang={language} value={answer} maxLength={6000} onChange={e => setAnswer(e.target.value)} disabled={!!result || busy} rows={q.mode === "self" ? 3 : 2} placeholder="Javobingizni yozing…" className="w-full rounded-xl border p-3 text-sm"/>}
    {!result && <button onClick={submit} disabled={busy || !answer.trim()} className="rounded-xl bg-sky-800 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">{busy ? "Saqlanmoqda…" : q.mode === "self" ? "Yuborish va namunani ko‘rish" : "Tekshirish"}</button>}
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    {result && <div role="status" className={`space-y-2 rounded-xl p-3 text-sm ${result.correct === false ? "bg-amber-50" : "bg-emerald-50"}`}>
      <p className="flex items-center gap-2 font-semibold"><CheckCircle2 size={17}/>{result.correct === null ? "Javob saqlandi · namuna bilan solishtiring" : result.correct ? "To‘g‘ri · javob saqlandi" : "Javob saqlandi · tuzatishni ko‘ring"}</p>
      <p className="whitespace-pre-line break-words">{result.expected.join(" / ")}</p>
      <p className="whitespace-pre-line break-words">{result.explanation}</p>
      {!!result.criteria?.length && <ul className="list-disc pl-5">{result.criteria.map((c, i) => <li key={i}>{c}</li>)}</ul>}
      {result.transcript && <details><summary className="cursor-pointer font-semibold">Transkriptni ko‘rish</summary><p lang={language} className="mt-2 whitespace-pre-line break-words">{result.transcript}</p></details>}
      <button onClick={() => { setResult(null); setAnswer(""); }} className="underline">Qayta mashq qilish</button>
    </div>}
  </div>;
}
