import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { readWritingDraft, saveWritingDraft, removeWritingDraft } from "../lib/studentWritingDrafts";
import { getCourseQuestionChoices } from "../lib/courseQuestionInteraction";

export type DailySixFeedback = {correct: boolean; explanation: string; expected?: string[]; transcript?: string; assessment?: string};
export type DailySixQuestion = {id: string; prompt: string; mode: "exact" | "writing" | "audio"; options?: string[]};
export type DailySixPlan = {
  student_id: number; reward_eligible?: boolean; reward_note?: string;
  id: string; day: string; language: string; lesson: number; title: string;
  skills: {skill: string; target: number; completed_count: number; completed: boolean; questions: DailySixQuestion[]; text?: string; audio_url?: string}[];
  answers: Record<string, {answer: string; feedback: DailySixFeedback}>;
  completed_steps: number; total_steps: number; completed: boolean; awarded: boolean;
};
type AnswerResponse = DailySixFeedback & {reward: {xp: number; coins: number; reason: string}; plan: DailySixPlan};
const endpoint = "/student/course-practice/daily-six";
const names: Record<string, string> = {vocabulary: "Luğat", vocab: "Luğat", grammar: "Grammatika", reading: "Öqiş", listening: "Tinglaş", writing: "Yoziş", speaking: "Gapiriş"};
const button = "min-h-11 rounded-xl border px-4 py-2 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700 disabled:opacity-50";
export const dailySixDay = () => new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Tashkent"}).format(new Date());
export function dailySixDraftKey(plan: Pick<DailySixPlan, "student_id" | "id" | "day" | "language">) {
  return `daily-six:${plan.student_id}:${plan.id}:${plan.day}:${plan.language}`;
}
// Neither a locally filled answer nor a successful HTTP response proves completion.
export function dailySixAccepted(plan: DailySixPlan, questionId: string) {
  return plan.answers[questionId]?.feedback.correct === true;
}

export default function CourseDailySix({language, onExit}: {language: string; onExit: () => void}) {
  const [plan, setPlan] = useState<DailySixPlan | null>(null);
  const [skill, setSkill] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const generation = useRef(0);
  const lock = useRef(false);
  const observedDay = useRef(dailySixDay());
  const heading = useRef<HTMLHeadingElement>(null);
  function refreshDay() {
    if (observedDay.current === dailySixDay()) return true;
    observedDay.current = dailySixDay(); generation.current++; lock.current = false;
    setBusy(false); setPlan(null); setLoading(true); setNotice("Yangi kun boşlandi. Bugungi topshiriqlar yuklanmoqda."); setRevision(n => n + 1);
    return false;
  }
  useEffect(() => {
    const resume = () => {if (document.visibilityState !== "hidden") refreshDay();};
    const timer = window.setInterval(resume, 1000);
    window.addEventListener("focus", resume); document.addEventListener("visibilitychange", resume);
    return () => {clearInterval(timer); window.removeEventListener("focus", resume); document.removeEventListener("visibilitychange", resume);};
  }, []);
  useEffect(() => {
    const request = ++generation.current;
    setLoading(true); setError(""); lock.current = false; setBusy(false);
    api.fresh<DailySixPlan>(`${endpoint}?language=${language}`).then(next => {
      if (request !== generation.current || !refreshDay()) return;
      setPlan(next); setSkill(current => next.skills.some(s => s.skill === current) ? current : next.skills.find(s => !s.completed)?.skill || next.skills[0]?.skill || "vocabulary");
      setLoading(false);
    }).catch(e => {if (request === generation.current) {setError(e instanceof Error ? e.message : "Reja yuklanmadi."); setLoading(false);}});
    return () => {generation.current++;};
  }, [language, revision]);
  useEffect(() => {heading.current?.focus({preventScroll: true});}, [skill, loading]);
  async function submit(question: DailySixQuestion, answer: string, spoken: boolean) {
    if (!plan || lock.current || !answer.trim() || !refreshDay()) return;
    const request = generation.current;
    lock.current = true; setBusy(true); setError(""); setNotice("");
    try {
      const result = await api.post<AnswerResponse>(`${endpoint}/answer`, {
        language: plan.language, day: plan.day, question_id: question.id, answer,
        ...(spoken ? {speech_source: "speech_recognition"} : {}),
      });
      if (request !== generation.current || !refreshDay()) return;
      // Keep the learner on this skill so feedback can be read before navigating.
      setPlan(result.plan);
      if (dailySixAccepted(result.plan, question.id)) removeWritingDraft(dailySixDraftKey(plan), question.id);
      setNotice(result.reward.xp > 0 ? `+${result.reward.xp} XP saqlandi.` : "Javob tekşirildi. Natija saqlandi.");
    } catch (e) {
      if (request !== generation.current || !refreshDay()) return;
      if (e instanceof ApiError && e.status === 409) {
        generation.current++; setPlan(null); setLoading(true); lock.current = false; setBusy(false);
        setNotice("Kunlik reja yangilandi. Saqlangan natijalar qayta yuklanmoqda."); setRevision(n => n + 1);
      } else setError(e instanceof Error ? e.message : "Javob saqlanmadi. Qayta urinib köring.");
    } finally {if (request === generation.current) {lock.current = false; setBusy(false);}}
  }
  const current = plan?.skills.find(s => s.skill === skill);
  return <main className="mx-auto w-full min-w-0 max-w-2xl space-y-4 rounded-3xl bg-slate-50 p-4 pb-24 text-slate-900" aria-label="Kunlik olti könikma">
    <button className={button} onClick={onExit}>← Rejaga qaytiş</button>
    <header className="space-y-2 rounded-2xl bg-sky-950 p-4 text-white">
      <h1 className="text-xl font-bold">Kunlik 6 qadam</h1>
      <p className="text-sm">Barcha 6 qadam tekşiruvdan ötganda +1 tanga. Toşkent kuni böyiça, ikkala til uçun jami bir marta. Olingan qisman XP saqlanadi; kunlik XP chegarasi amal qiladi. Ustoz coinlari alohida.</p>
      {plan && <><p className="text-sm">{plan.day} · {plan.language === "de" ? "Deutsch" : "English"} · {plan.lesson}-dars</p><p className="font-semibold">{plan.completed_steps} / {plan.total_steps} könikma tasdiqlangan</p><progress className="h-3 w-full accent-emerald-400" aria-label="Tasdiqlangan könikmalar" value={plan.completed_steps} max={plan.total_steps || 6}/></>}
    </header>
    {notice && <p role="status" className="rounded-xl bg-sky-50 p-3 text-sm">{notice}</p>}
    {error && <div role="alert" className="space-y-2 rounded-xl bg-red-50 p-3 text-red-900"><p>{error}</p><p className="text-sm">Yozilgan javoblar saqlanib turadi. Tekşirilmagan javob bajarilgan hisoblanmaydi.</p>{!plan ? <button className={button} onClick={() => setRevision(n => n + 1)}>Qayta yuklaş</button> : <p className="text-sm">Javob yonidagi «Tekşiriş» tugmasi bilan qayta urinib köring.</p>}</div>}
    {busy && <p role="status" className="text-sm">Tekşiruv davom etmoqda. Natija kelgunça kuting.</p>}
    {loading && <p role="status">Kunlik reja yuklanmoqda…</p>}
    {!loading && plan && <>
      {plan.language !== language && <p className="rounded-xl bg-amber-50 p-3 text-sm">Bugungi reja {plan.language === "de" ? "nemis" : "ingliz"} tilida boşlangan. Shu rejadagi natijalar saqlanadi; ertaga boşqa tilni tanlaş mumkin.</p>}
      {plan.reward_eligible === false && <p className="rounded-xl bg-amber-50 p-3 text-sm">{plan.reward_note || "Bu rejimda tanga berilmaydi."}</p>}
      {plan.completed && <div role="status" className="rounded-xl bg-emerald-50 p-4 font-semibold">Barcha 6 könikma tasdiqlandi. {plan.reward_eligible === false ? (plan.reward_note || "Bu rejimda tanga berilmaydi.") : plan.awarded ? "Bugungi +1 tanga berildi." : "Tanga hali tasdiqlanmagan."}</div>}
      <nav aria-label="Olti könikma" className="grid grid-cols-2 gap-2 sm:grid-cols-3">{plan.skills.map(s => <button key={s.skill} className={`${button} min-w-0 break-words text-left ${s.skill === skill ? "border-sky-800 bg-sky-800 text-white" : "bg-white"}`} aria-pressed={s.skill === skill} onClick={() => setSkill(s.skill)}><span className="block">{names[s.skill] || s.skill}{s.completed ? " ✓" : ""}</span><span className="text-xs">{s.completed_count} / {s.target}</span></button>)}</nav>
      {current && <section className="min-w-0 space-y-4" aria-label={names[current.skill] || current.skill}>
        <h2 ref={heading} tabIndex={-1} className="text-lg font-bold">{names[current.skill] || current.skill}</h2>
        <p className="text-sm text-slate-600">{plan.title}</p>
        {current.text && current.skill !== "listening" && <p lang={plan.language} className="whitespace-pre-line break-words rounded-xl bg-white p-4">{current.text}</p>}
        {current.skill === "listening" && <DailySixAudio key={`${plan.id}:${current.audio_url}`} url={current.audio_url}/>}
        {current.questions.map((q, i) => <DailySixAnswer key={`${plan.id}:${plan.language}:${q.id}`} plan={plan} question={q} index={i} speaking={current.skill === "speaking"} busy={busy} checkDay={refreshDay} onSubmit={submit}/>)}
        <p className="text-sm text-slate-600">Keyingi könikmani yuqoridan özingiz tanlang. Natijalar tekşiruvdan keyin yangilanadi.</p>
      </section>}
      <Link to="/student/course-practice?view=session" className={`${button} inline-flex items-center`}>Qisqa seansni oçiş</Link>
    </>}
  </main>;
}

function DailySixAudio({url}: {url?: string}) {
  const audio = useRef<HTMLAudioElement>(null);
  const [failed, setFailed] = useState(false);
  return <div className="rounded-xl border bg-white p-3"><p className="mb-2 text-sm">Yozuvni tinglang, söng savollarga javob bering.</p>{url ? <audio ref={audio} controls preload="none" src={url} className="w-full min-w-0" aria-label="Tinglaş yozuvi" onError={() => setFailed(true)} onCanPlay={() => setFailed(false)}/> : <p role="alert">Bu reja uçun audio topilmadi.</p>}{failed && <div role="alert"><p>Audio yuklanmadi.</p><button className={button} onClick={() => {setFailed(false); audio.current?.load();}}>Audioni qayta yuklaş</button></div>}</div>;
}

type Recognition = {lang: string; interimResults: boolean; maxAlternatives: number; onresult: ((event: {results: {isFinal?: boolean; 0: {transcript: string}}[]}) => void) | null; onerror: ((event: {error: string}) => void) | null; onend: (() => void) | null; start(): void; stop(): void; abort(): void};
type SpeechWindow = Window & {SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition};
function DailySixAnswer({plan, question: q, index, speaking, busy, checkDay, onSubmit}: {plan: DailySixPlan; question: DailySixQuestion; index: number; speaking: boolean; busy: boolean; checkDay: () => boolean; onSubmit: (q: DailySixQuestion, answer: string, speaking: boolean) => Promise<void>}) {
  const task = dailySixDraftKey(plan);
  const saved = plan.answers[q.id];
  const accepted = dailySixAccepted(plan, q.id);
  const [answer, setAnswer] = useState(() => (accepted ? saved?.answer : readWritingDraft(task, q.id).text || saved?.answer) || "");
  const [listening, setListening] = useState(false);
  const [speechError, setSpeechError] = useState("");
  const [sending, setSending] = useState(false);
  const recognition = useRef<Recognition | null>(null);
  const active = useRef(true);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const speechGeneration = useRef(0);
  const speakingNow = useRef(false);
  const liveAnswer = useRef(answer);
  const choices = q.mode === "exact" ? getCourseQuestionChoices({...q, mode: "exact"}) : [];
  function change(value: string) {
    liveAnswer.current = value; setAnswer(value);
    saveWritingDraft(task, q.id, {text: value, deadline: null});
  }
  function stopSpeech() {
    speechGeneration.current++; speakingNow.current = false;
    if (timer.current) clearTimeout(timer.current);
    const rec = recognition.current;
    if (rec) {rec.onresult = null; rec.onerror = null; rec.onend = null; try {rec.abort();} catch { /* already stopped */ }}
    recognition.current = null;
    window.speechSynthesis?.cancel();
  }
  useEffect(() => {active.current = true; return () => {active.current = false; stopSpeech();};}, []);
  function finishMic() {
    if (timer.current) clearTimeout(timer.current);
    const rec = recognition.current;
    // Native services may never send onend after stop (offline/provider failure).
    timer.current = setTimeout(() => {
      stopSpeech(); setListening(false);
      setSpeechError("Ovozni taniş javob bermadi. Saqlangan matn özgarmadi; qayta urinib köring.");
    }, 8000);
    try {rec?.stop();} catch {
      stopSpeech(); setListening(false);
      setSpeechError("Mikrofonni töxtatib bölmadi. Qayta urinib köring.");
    }
  }
  function startMic() {
    if (!checkDay() || busy || accepted) return;
    if (speakingNow.current) {finishMic(); return;}
    const SR = (window as SpeechWindow).SpeechRecognition || (window as SpeechWindow).webkitSpeechRecognition;
    if (!SR) {setSpeechError("Ovozni taniş bu qurilmada mavjud emas. Jony Student ilovasini yangilang yoki Chrome orqali oçing."); return;}
    stopSpeech(); const request = speechGeneration.current;
    try {
    const rec = new SR(); recognition.current = rec;
    rec.lang = plan.language === "de" ? "de-DE" : "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
    const current = () => active.current && request === speechGeneration.current;
    rec.onresult = event => {
      if (!current() || !checkDay()) return;
      const text = Array.from(event.results).filter(r => r.isFinal !== false).map(r => r[0].transcript).join(" ").trim();
      if (!text) setSpeechError("Ovoz eşitilmadi. Qayta gapiring.");
      else if (text.length > 1000) setSpeechError("Javob juda uzun. Qisqaroq gapiring.");
      else {setSpeechError(""); change(text);}
    };
    rec.onerror = event => {if (!current()) return; const messages: Record<string, string> = {"not-allowed": "Mikrofonga ruxsat bering.", "audio-capture": "Mikrofon topilmadi.", "no-speech": "Ovoz eşitilmadi. Qayta gapiring.", network: "Ovozni taniş xizmati ulanmayapti. Internetni tekşiring."}; if (event.error !== "aborted") setSpeechError(messages[event.error] || "Ovozni aniqlab bölmadi. Qayta urinib köring."); stopSpeech(); setListening(false);};
    rec.onend = () => {if (timer.current) clearTimeout(timer.current); if (current()) {setListening(false); speakingNow.current = false;}};
    setSpeechError(""); setListening(true); speakingNow.current = true; rec.start(); if (speakingNow.current) timer.current = setTimeout(finishMic, 60000);} catch {stopSpeech(); setListening(false); setSpeechError("Mikrofonni işga tuşirib bölmadi.");}
  }
  async function submit() {
    if (sending || !checkDay()) return;
    setSending(true);
    try {await onSubmit(q, liveAnswer.current, speaking);} finally {if (active.current) setSending(false);}
  }
  return <article className="min-w-0 space-y-3 rounded-xl border bg-white p-4">
    <h3 className="whitespace-pre-line break-words font-semibold">{index + 1}. {q.prompt}</h3>
    {speaking ? <>
      <p className="text-sm text-slate-600">Mikrofonga javob bering. AI tanilgan matnning mazmunini tekşiradi; talaffuz baholanmaydi. Matnni yuborişning özi yakunlangan degani emas.</p>
      {!accepted && <div className="flex flex-wrap gap-2"><button className={button} disabled={busy} aria-pressed={listening} onClick={startMic}>{listening ? "Mikrofonni töxtatiş" : "Mikrofonga gapiriş"}</button></div>}
      {listening && <p role="status">Tinglanmoqda…</p>}
      {answer && <p lang={plan.language} className="whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3" aria-label="Tanilgan ovozli javob">{answer}</p>}
      {speechError && <p role="alert" className="text-sm text-red-800">{speechError}</p>}
    </> : choices.length ? <fieldset disabled={busy || accepted} className="space-y-2"><legend className="text-sm">Javobni tanlang</legend>{choices.map(choice => <label key={choice.value} className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border p-3 focus-within:ring-2 focus-within:ring-sky-700"><input type="radio" name={`${task}:${q.id}`} checked={answer === choice.value} onChange={() => change(choice.value)}/><span lang={plan.language} className="break-words">{choice.label}</span></label>)}</fieldset> : <label className="block text-sm">Javobingiz<textarea lang={plan.language} value={answer} onChange={e => change(e.target.value)} disabled={busy || accepted} maxLength={6000} rows={q.mode === "writing" ? 5 : 2} className="mt-2 block min-h-11 w-full min-w-0 rounded-lg border p-3"/></label>}
    {!accepted && <button className={`${button} bg-sky-800 text-white`} disabled={busy || sending || listening || !answer.trim()} onClick={submit}>{sending ? (q.mode === "writing" || speaking ? "AI tekşirmoqda…" : "Tekşirilmoqda…") : "Tekşiriş"}</button>}
    {sending && (q.mode === "writing" || speaking) && <p role="status" className="text-sm">Tekşiruv natijasini kuting. Javob hali tasdiqlanmagan.</p>}
    {saved && <div role="status" className={`space-y-1 rounded-lg p-3 text-sm ${accepted ? "bg-emerald-50" : "bg-amber-50"}`}><p className="font-semibold">{accepted ? "Tekşiruvdan ötdi ✓" : "Hali bajarilmagan — tuzatib qayta yuboring"}</p><p className="whitespace-pre-wrap break-words">{saved.feedback.explanation}</p>{saved.feedback.expected?.length ? <p lang={plan.language}>{saved.feedback.expected.join(" / ")}</p> : null}{saved.feedback.transcript && <details><summary className="min-h-11 cursor-pointer py-3">Audio matnini köriş</summary><p lang={plan.language} className="whitespace-pre-wrap break-words">{saved.feedback.transcript}</p></details>}</div>}
  </article>;
}
