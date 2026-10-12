import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BookOpen, ChevronLeft, ChevronRight, Headphones, Languages, Mic, PenLine, Play, RotateCcw, Square } from "lucide-react";
import { api } from "../../lib/api";
import "./StudentRussianCourse.css";

type Kind = "vocabulary" | "grammar";
const sections = [
  { key: "vocabulary", label: "Lug‘at", icon: Languages },
  { key: "grammar", label: "Grammatika", icon: BookOpen },
  { key: "reading", label: "O‘qish", icon: BookOpen },
  { key: "listening", label: "Tinglash", icon: Headphones },
  { key: "writing", label: "Yozish", icon: PenLine },
  { key: "speaking", label: "Gapirish", icon: Mic },
] as const;
type Section = typeof sections[number]["key"];
type Summary = { no: number; month: number; title: string; objective: string; phrase_count: number; grammar_title: string };
type Progress = { lesson_no: number; kind: string; best_score: number; total: number; attempts: number };
type Course = { lessons: Summary[]; progress: Progress[] };
type Lesson = {
  no: number; month: number; title: string; objective: string;
  grammar: { title: string; rule: string; examples: (string | { ru: string; uz: string })[]; exercises: { prompt: string }[] };
  phrases: { ru: string; uz: string }[];
  dialog: { speaker: string; ru: string; uz: string }[];
  questions: { prompt: string; answer: string }[];
  homework: string | string[]; exit: string;
  roleplay: { a: string; b: string; twist: string; success: string };
};
type Check = { score: number; total: number; results: { correct: boolean; answer: string; explanation: string }[]; progress: Progress };
const isSection = (value: string | null | undefined): value is Section => sections.some(s => s.key === value);
const errorText = (error: unknown) => error instanceof Error ? error.message : "Ma’lumotni yuklab bo‘lmadi. Qayta urinib ko‘ring.";

/** The URL wins over the route's default. Lesson selection is derived, never copied into state. */
export default function StudentRussianCourse({ initialSection }: { initialSection?: string }) {
  const [params, setParams] = useSearchParams();
  const [course, setCourse] = useState<Course | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const requestedSection = params.get("section");
  const section: Section = isSection(requestedSection) ? requestedSection : isSection(initialSection) ? initialSection : "vocabulary";

  useEffect(() => {
    let active = true;
    setError("");
    api.get<Course>("/student/russian/course", true).then(data => {
      if (active) setCourse({ ...data, lessons: [...data.lessons].sort((a, b) => a.no - b.no) });
    }).catch(e => { if (active) setError(errorText(e)); });
    return () => { active = false; };
  }, [retry]);

  const lessons = course?.lessons ?? [];
  const requestedLesson = lessons.find(l => l.no === Number(params.get("lesson")));
  const requestedMonth = Number(params.get("month"));
  const validMonth = Number.isInteger(requestedMonth) && requestedMonth >= 1 && requestedMonth <= 12;
  // A valid lesson deep link wins a conflicting month so its content and selector always agree.
  const month = requestedLesson?.month ?? (validMonth ? requestedMonth : lessons[0]?.month ?? 1);
  const monthLessons = lessons.filter(l => l.month === month);
  const selected = requestedLesson ?? monthLessons[0];
  const selectedIndex = lessons.findIndex(l => l.no === selected?.no);

  function navigate(next: { month?: number; lesson?: number; section?: Section }) {
    const updated = new URLSearchParams(params);
    updated.set("month", String(next.month ?? month));
    if (next.lesson ?? selected?.no) updated.set("lesson", String(next.lesson ?? selected?.no));
    else updated.delete("lesson");
    updated.set("section", next.section ?? section);
    setParams(updated);
  }

  function changeMonth(value: number) {
    const first = lessons.find(l => l.month === value);
    const updated = new URLSearchParams(params);
    updated.set("month", String(value));
    updated.set("section", section);
    if (first) updated.set("lesson", String(first.no));
    else updated.delete("lesson");
    setParams(updated);
  }

  function saveProgress(progress: Progress) {
    setCourse(current => current && ({ ...current, progress: [
      ...current.progress.filter(p => !(p.lesson_no === progress.lesson_no && p.kind === progress.kind)), progress,
    ] }));
  }

  return <div className="ruc" lang="uz">
    <header className="ruc-hero">
      <div className="ruc-eyebrow">JONY STUDENT <span>RUS TILI</span></div>
      <h1>Har dars — yangi imkoniyat.</h1>
      <p>Kursingizga mos iboralar va 6 yo‘nalishda mustaqil mashq.</p>
      <div className="ruc-chips"><span>12 oy</span><span>{course ? lessons.length : 144} dars</span><span>Mustaqil mashq</span></div>
    </header>

    {error ? <ErrorBox message={error} retry={() => setRetry(n => n + 1)} /> : !course ? <Loading /> : <>
      <div className="ruc-selectors">
        <label>O‘quv oyi<select value={month} onChange={e => changeMonth(Number(e.target.value))}>
          {Array.from({ length: 12 }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}-oy</option>)}
        </select></label>
        <label>Dars<select value={selected?.no ?? ""} onChange={e => {
          const lesson = lessons.find(l => l.no === Number(e.target.value));
          if (lesson) navigate({ month: lesson.month, lesson: lesson.no });
        }} disabled={!monthLessons.length}>
          {!monthLessons.length && <option value="">Darslar mavjud emas</option>}
          {monthLessons.map(l => <option key={l.no} value={l.no}>{l.no}. {l.title}</option>)}
        </select></label>
      </div>
      <nav className="ruc-sections" aria-label="Mashq yo‘nalishi">
        {sections.map(({ key, label, icon: Icon }) => <button type="button" key={key} aria-current={section === key ? "page" : undefined} onClick={() => navigate({ section: key })}><Icon size={19} aria-hidden="true" /><span>{label}</span></button>)}
      </nav>
      {selected ? <>
        <div className="ruc-lesson-heading"><div><span className="ruc-kicker">{month}-OY / {selected.no}-DARS</span><h2>{selected.title}</h2><p>{selected.objective}</p></div><span className="ruc-count">{selected.phrase_count}<small>ibora</small></span></div>
        <div className="ruc-progress" aria-label="Darsdagi server natijalari">
          {(["vocabulary", "grammar"] as const).map(kind => {
            const p = course.progress.find(p => p.lesson_no === selected.no && p.kind === kind);
            return <div key={kind}><span>{kind === "vocabulary" ? "Lug‘at" : "Grammatika"}</span><strong>{p ? `${p.best_score} / ${p.total}` : "Hali natija yo‘q"}</strong><small>{p ? `${p.attempts} ta urinish · eng yaxshi natija` : "Birinchi mashqni boshlang"}</small></div>;
          })}
        </div>
        <LessonContent key={`${selected.no}:${section}`} no={selected.no} section={section} onProgress={saveProgress} />
        <div className="ruc-pagination">
          <button type="button" disabled={selectedIndex <= 0} onClick={() => { const l = lessons[selectedIndex - 1]; if (l) navigate({ month: l.month, lesson: l.no }); }}><ChevronLeft size={18} />Oldingi dars</button>
          <button type="button" disabled={selectedIndex >= lessons.length - 1} onClick={() => { const l = lessons[selectedIndex + 1]; if (l) navigate({ month: l.month, lesson: l.no }); }}>Keyingi dars<ChevronRight size={18} /></button>
        </div>
      </> : <div className="ruc-card">Bu oy uchun darslar hali mavjud emas. Boshqa oyni tanlang.</div>}
    </>}
    <p className="ruc-footnote">Bu mustaqil mashq. Rasmiy imtihon bahosi yoki XP berilmaydi.</p>
  </div>;
}

function Loading() { return <div className="ruc-card ruc-loading" role="status">Dars materiallari yuklanmoqda…</div>; }
function ErrorBox({ message, retry }: { message: string; retry: () => void }) {
  return <div className="ruc-error" role="alert"><p>{message}</p><button type="button" onClick={retry}><RotateCcw size={16} />Qayta urinish</button></div>;
}

function LessonContent({ no, section, onProgress }: { no: number; section: Section; onProgress: (p: Progress) => void }) {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setError("");
    api.get<Lesson>(`/student/russian/lessons/${no}`, retry > 0).then(data => { if (active) setLesson(data); }).catch(e => { if (active) setError(errorText(e)); });
    return () => { active = false; };
  }, [no, retry]);
  if (error) return <ErrorBox message={error} retry={() => setRetry(n => n + 1)} />;
  if (!lesson) return <Loading />;
  if (section === "vocabulary" || section === "grammar") return <Practice lesson={lesson} kind={section} onProgress={onProgress} />;
  if (section === "listening") return <Listening lesson={lesson} />;
  if (section === "reading") return <div className="ruc-stack"><div className="ruc-card"><span className="ruc-kicker">O‘QISH</span><h3>Dialogni tushuning</h3><Dialog lesson={lesson} /></div><Questions lesson={lesson} /></div>;
  if (section === "writing") return <div className="ruc-card"><span className="ruc-kicker">YOZISH · MUSTAQIL MASHQ</span><h3>Fikringizni rus tilida yozing</h3>{(Array.isArray(lesson.homework) ? lesson.homework : [lesson.homework]).map((task, i) => <p key={i} className="ruc-task">{i + 1}. {task}</p>)}<label className="ruc-field">Javobingiz<textarea lang="ru" rows={8} placeholder="Напишите здесь…" /></label><p className="ruc-note">Bu vaqtinchalik yozuv maydoni. Javob yuborilmaydi, saqlanmaydi va avtomatik baholanmaydi. Dars yoki bo‘limni almashtirishdan oldin matnni nusxalang.</p><h4>O‘zingizni tekshiring</h4><p className="ruc-task">{lesson.exit}</p></div>;
  return <div className="ruc-card"><span className="ruc-kicker">GAPIRISH · MUSTAQIL MASHQ</span><h3>Vaziyatni jonlantiring</h3><p className="ruc-note">Ovoz yozilmaydi va baholanmaydi. Sherik bilan yoki mustaqil ovoz chiqarib mashq qiling.</p><h4>Sizning rolingiz · A</h4><p className="ruc-task">{lesson.roleplay.a}</p><details><summary>Sherik rolini ko‘rish · B</summary><p>{lesson.roleplay.b}</p></details><details><summary>Qo‘shimcha vaziyatni ochish</summary><p>{lesson.roleplay.twist}</p></details><h4>Muvaffaqiyat mezoni</h4><p className="ruc-task">{lesson.roleplay.success}</p><h4>Yakuniy mashq</h4><p>{lesson.exit}</p></div>;
}

// Stable per lesson/question, with the correct answer deliberately rotated through the slots.
function translationOptions(lesson: Lesson, index: number) {
  const answer = lesson.phrases[index].uz;
  const distractors = [...new Set(lesson.phrases.map(p => p.uz))].filter(value => value !== answer);
  const start = distractors.length ? (lesson.no + index * 3) % distractors.length : 0;
  const options = [...distractors.slice(start), ...distractors.slice(0, start)].slice(0, 3);
  options.splice((lesson.no + index) % (options.length + 1), 0, answer);
  return options;
}

function Practice({ lesson, kind, onProgress }: { lesson: Lesson; kind: Kind; onProgress: (p: Progress) => void }) {
  const [mode, setMode] = useState<"study" | "practice">("study");
  const prompts = kind === "vocabulary" ? lesson.phrases.map(p => p.ru) : lesson.grammar.exercises.map(e => e.prompt);
  const [answers, setAnswers] = useState<(string | undefined)[]>(() => Array(prompts.length).fill(undefined));
  const [result, setResult] = useState<Check | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const active = useRef(true);
  const submitting = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  const answered = answers.filter(a => a !== undefined).length;

  async function check() {
    if (submitting.current || result || answered !== prompts.length || !prompts.length) return;
    submitting.current = true;
    setBusy(true); setError("");
    try {
      const data = await api.post<Check>(`/student/russian/lessons/${lesson.no}/check`, { kind, answers: answers.map(a => a ?? "") });
      if (active.current) { setResult(data); onProgress(data.progress); }
    } catch (e) { if (active.current) setError(errorText(e)); }
    finally { submitting.current = false; if (active.current) setBusy(false); }
  }

  return <div className="ruc-card">
    <div className="ruc-mode" aria-label="Mashq rejimi"><button type="button" aria-pressed={mode === "study"} onClick={() => setMode("study")}>O‘rganish</button><button type="button" aria-pressed={mode === "practice"} onClick={() => setMode("practice")}>Mashq qilish</button></div>
    <h3>{kind === "vocabulary" ? "Dars iboralari" : lesson.grammar.title}</h3>
    {mode === "study" ? kind === "vocabulary" ? <div className="ruc-phrases">{lesson.phrases.map((p, i) => <div key={i}><span className="ruc-number">{String(i + 1).padStart(2, "0")}</span><div><strong lang="ru">{p.ru}</strong><p>{p.uz}</p></div></div>)}</div> : <><p className="ruc-task">{lesson.grammar.rule}</p><h4>Misollar</h4>{lesson.grammar.examples.map((example, i) => <div className="ruc-example" key={i}>{typeof example === "string" ? <p lang="ru">{example}</p> : <><p lang="ru">{example.ru}</p><p>{example.uz}</p></>}</div>)}</> : <>
      <p className="ruc-note">{kind === "vocabulary" ? "Ruscha iboraning o‘zbekcha tarjimasini tanlang. Variantlar shu darsdan olingan; to‘g‘ri javob tekshiruvdan keyin ko‘rsatiladi." : "Rus tilida javob yozing. Tekshiruv darsdagi namunaviy javobga asoslanadi; boshqa to‘g‘ri ifodalarni natijadagi namuna bilan mustaqil solishtiring."}</p>
      <p className="ruc-kicker">{lesson.no}-DARS · {answered}/{prompts.length} JAVOB · MUSTAQIL MASHQ</p>
      {!prompts.length ? <p>Bu dars uchun mashqlar hali mavjud emas.</p> : <form onSubmit={e => { e.preventDefault(); void check(); }}>
        <div className="ruc-stack">{prompts.map((prompt, i) => <fieldset className="ruc-question" key={i} disabled={busy || !!result}>
          <legend><span>{i + 1}.</span> <span lang="ru">{prompt}</span></legend>
          {kind === "vocabulary" ? <div className="ruc-options">{[...translationOptions(lesson, i), ""].map((option, j) => <label key={`${j}:${option}`} className={answers[i] === option ? "is-selected" : ""}><input type="radio" name={`ruc-answer-${i}`} value={option} checked={answers[i] === option} onChange={() => setAnswers(current => current.map((a, n) => n === i ? option : a))} /><span>{option || "Bilmayman"}</span></label>)}</div> : <label className="ruc-field"><span className="ruc-sr-only">{i + 1}-savolga javob</span><input lang="ru" autoComplete="off" value={answers[i] ?? ""} onChange={e => { const value = e.target.value; setAnswers(current => current.map((a, n) => n === i ? (value.trim() ? value : undefined) : a)); }} placeholder="Ответ…" /><button type="button" aria-pressed={answers[i] === ""} onClick={() => setAnswers(current => current.map((a, n) => n === i ? "" : a))}>Bilmayman{answers[i] === "" ? " — tanlandi" : ""}</button></label>}
          {result?.results[i] && <div className={`ruc-feedback ${result.results[i].correct ? "is-correct" : ""}`}><strong>{result.results[i].correct ? "To‘g‘ri" : "Namunani ko‘rib chiqing"}</strong><p>Namunaviy javob: <span lang={kind === "grammar" ? "ru" : "uz"}>{result.results[i].answer}</span></p>{result.results[i].explanation && <p>{result.results[i].explanation}</p>}</div>}
        </fieldset>)}</div>
        {error && <div className="ruc-error" role="alert">{error}<p>Javoblaringiz saqlandi. “Tekshirish” orqali qayta urinishingiz mumkin.</p></div>}
        {result ? <div className="ruc-result" role="status"><span>Mashq natijasi</span><strong>{result.score} / {result.total}</strong><p>Eng yaxshi: {result.progress.best_score}/{result.progress.total} · Urinishlar: {result.progress.attempts}</p><button type="button" onClick={() => { setAnswers(Array(prompts.length).fill(undefined)); setResult(null); setError(""); }}><RotateCcw size={16} />Yana mashq qilish</button></div> : <button className="ruc-primary" type="submit" disabled={busy || answered !== prompts.length}>{busy ? "Tekshirilmoqda…" : "Javoblarni tekshirish"}</button>}
      </form>}
    </>}
  </div>;
}

function Dialog({ lesson }: { lesson: Lesson }) {
  return <div className="ruc-dialog">{lesson.dialog.map((line, i) => <div key={i} className={i % 2 ? "ruc-dialog-other" : ""}><span>{line.speaker}</span><p lang="ru">{line.ru}</p><details><summary>Tarjimasini ko‘rish</summary><p>{line.uz}</p></details></div>)}</div>;
}

function Questions({ lesson }: { lesson: Lesson }) {
  return <div className="ruc-card"><h3>O‘zingizni tekshiring</h3><p className="ruc-note">Avval javob yozing, keyin namuna bilan solishtiring. Avtomatik ball berilmaydi; yozuvlar saqlanmaydi.</p>{lesson.questions.map((q, i) => <div className="ruc-selfcheck" key={i}><label className="ruc-field"><span lang="ru">{i + 1}. {q.prompt}</span><textarea lang="ru" rows={2} placeholder="Ваш ответ…" /></label><details><summary>Namunaviy javobni ochish</summary><p lang="ru">{q.answer}</p></details></div>)}</div>;
}

function Listening({ lesson }: { lesson: Lesson }) {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceId, setVoiceId] = useState("");
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const [transcript, setTranscript] = useState(false);
  const generation = useRef(0);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
  useEffect(() => {
    if (!supported) return;
    const synth = window.speechSynthesis;
    const update = () => setVoices(synth.getVoices().filter(v => /^ru(?:[-_]|$)/i.test(v.lang)));
    update(); synth.addEventListener("voiceschanged", update);
    return () => { generation.current++; synth.cancel(); synth.removeEventListener("voiceschanged", update); };
  }, [supported]);
  function stop() { generation.current++; if (supported) window.speechSynthesis.cancel(); setPlaying(false); }
  function play() {
    const voice = voices.find(v => v.voiceURI === voiceId) ?? voices[0];
    if (!supported || !voice) return;
    stop(); setError("");
    const run = generation.current;
    const lines = lesson.dialog.map(l => l.ru).filter(Boolean);
    if (!lines.length) return;
    setPlaying(true);
    const speakLine = (index: number) => {
      if (run !== generation.current) return;
      if (index >= lines.length) { setPlaying(false); return; }
      const utterance = new SpeechSynthesisUtterance(lines[index]);
      utterance.voice = voice; utterance.lang = voice.lang; utterance.rate = 0.85;
      utterance.onend = () => speakLine(index + 1);
      utterance.onerror = () => { if (run === generation.current) { generation.current++; setPlaying(false); setError("Qurilma ovozini ijro etib bo‘lmadi. Qayta urinib ko‘ring."); } };
      try { window.speechSynthesis.speak(utterance); } catch { generation.current++; setPlaying(false); setError("Qurilma ovozi hozir ishlamayapti. Qayta urinib ko‘ring."); }
    };
    speakLine(0);
  }
  return <div className="ruc-stack"><div className="ruc-card"><span className="ruc-kicker">TINGLASH · QURILMA OVOZI</span><h3>Avval tinglang. Keyin o‘qing.</h3><p className="ruc-note">Dialog qurilmangizdagi ruscha ovoz bilan o‘qiladi. Bu darsning original audioyozuvi emas.</p><div className="ruc-audio"><Headphones size={36} aria-hidden="true" />{!supported || !voices.length ? <p role="status">{!supported ? "Bu qurilmada ovozli o‘qish mavjud emas." : "Ruscha qurilma ovozi topilmadi. Qurilma sozlamalarida ruscha ovozni o‘rnating, so‘ng sahifani qayta oching."} Matnni quyida ochib o‘qishingiz mumkin.</p> : <><label className="ruc-field">Qurilma ovozi<select value={voices.find(v => v.voiceURI === voiceId)?.voiceURI ?? voices[0].voiceURI} onChange={e => { stop(); setVoiceId(e.target.value); }}>{voices.map(v => <option value={v.voiceURI} key={v.voiceURI}>{v.name}</option>)}</select></label><button type="button" className="ruc-primary" disabled={!lesson.dialog.length} onClick={playing ? stop : play}>{playing ? <Square size={18} /> : <Play size={18} />}{playing ? "To‘xtatish" : "Dialogni tinglash"}</button></>}{error && <p role="alert" className="ruc-error">{error}</p>}</div><button type="button" aria-expanded={transcript} onClick={() => setTranscript(v => !v)}>{transcript ? "Matnni yashirish" : "Dialog matnini ochish"}</button>{transcript && <Dialog lesson={lesson} />}</div><Questions lesson={lesson} /></div>;
}
