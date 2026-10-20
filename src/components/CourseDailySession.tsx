import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, CheckCircle2, Flag } from "lucide-react";
import { api } from "../lib/api";
import CourseAnswer, { type Drafts, type Question } from "./CourseAnswer";
import { Recall, type Motivation, type PlanStep } from "./CourseMotivation";
import { CourseSpeaking } from "./CourseSpeaking";
import CourseLessonAudio from "./CourseLessonAudio";

type Section = {id:string; title:string; skill:string; text?:string; questions:Question[]};
type Detail = {lesson:number; title:string; sections:Section[]};
const skillNames:Record<string,string> = {reading:"Matndan ma’no topamiz", listening:"Tinglab tushunamiz", grammar:"Gap qanday tuzilishini mashq qilamiz", writing:"O‘z fikrimizni yozamiz", speaking:"Ovoz chiqarib gapiramiz", homework:"Bilimni mustahkamlaymiz"};

export default function CourseDailySession({language,onExit,onLesson,onAnswerSaved}:{language:string;onExit:()=>void;onLesson:(lesson:number)=>void;onAnswerSaved:(lesson:number,questionId:string)=>void}) {
  const [data,setData]=useState<Motivation|null>(null);
  const [step,setStep]=useState<PlanStep|null>(null);
  const [detail,setDetail]=useState<Detail|null>(null);
  const [saved,setSaved]=useState(false);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [loadVersion,setLoadVersion]=useState(0);
  const drafts=useRef<Drafts>(new Map());
  const localDay=()=>new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Tashkent"}).format(new Date());
  const day=useRef(localDay());
  function checkDay() {
    const current=localDay();
    if(current===day.current)return true;
    day.current=current;drafts.current.clear();setSaved(false);setLoading(true);setLoadVersion(n=>n+1);return false;
  }
  useEffect(()=>{
    const resume=()=>{if(document.visibilityState!=="hidden")checkDay();};
    const timer=window.setInterval(resume,1000);
    document.addEventListener("visibilitychange",resume);window.addEventListener("focus",resume);
    return()=>{clearInterval(timer);document.removeEventListener("visibilitychange",resume);window.removeEventListener("focus",resume);};
  },[]);
  const heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{
    let live=true; setLoading(true); setError("");
    api.fresh<Motivation>(`/student/course-practice/motivation?language=${language}`).then(async next=>{
      const current=next.plan?.steps.find(s=>!s.done)||null;
      const lesson=current&&current.kind!=="review" ? await api.fresh<Detail>(`/student/course-practice/${current.lesson}?language=${language}`):null;
      if(!live)return;
      setData(next);setStep(current);setDetail(lesson);setSaved(false);setLoading(false);
      requestAnimationFrame(()=>heading.current?.focus());
    }).catch(e=>{if(live){setError(e instanceof Error?e.message:"Reja yuklanmadi");setLoading(false);}});
    return()=>{live=false;};
  },[language,loadVersion]);
  const steps=data?.plan?.steps||[];
  const completed=steps.filter(s=>s.done).length;
  const index=step?steps.findIndex(s=>s.id===step.id):-1;
  const section=detail?.sections.find(s=>s.questions.some(q=>q.id===step?.question_id));
  const question=section?.questions.find(q=>q.id===step?.question_id);
  const review=data?.review.find(q=>q.id===step?.question_id);
  const next=()=>setLoadVersion(n=>n+1);
  return <main className="mx-auto max-w-xl space-y-4 p-4 pb-24 text-slate-900" aria-label="Qisqa mashq seansi">
    <div className="flex items-center justify-between gap-3"><button onClick={onExit} className="inline-flex min-h-11 items-center gap-2 rounded-xl border bg-white px-3 text-sm"><ArrowLeft size={16}/>Rejaga qaytish</button><span className="text-sm text-slate-500">{language==="de"?"Deutsch B1":"English Intensive"}</span></div>
    <header className="rounded-3xl bg-indigo-950 p-5 text-white"><p className="text-xs uppercase tracking-wider text-indigo-200">Bitta qadam — bitta vazifa</p><h1 ref={heading} tabIndex={-1} className="mt-2 text-xl font-bold">{loading?"Rejangiz tayyorlanmoqda…":step?`${index+1} / ${steps.length} · ${step.kind==="review"?"Eslab ko‘ramiz":skillNames[section?.skill||""]||"Navbatdagi kichik qadam"}`:steps.length?"Bugungi rejangiz bajarildi!":"Bugungi reja"}</h1>{data&&<><p className="mt-2 text-sm text-indigo-100">{Math.min(steps.length,completed+(saved?1:0))} / {steps.length} qadam bajarildi</p><progress aria-label="Seansdagi qadamlar" max={Math.max(1,steps.length)} value={Math.min(steps.length,completed+(saved?1:0))} className="mt-3 h-2 w-full accent-emerald-400"/></>}</header>
    {error&&<div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4"><p>{error}</p><button onClick={next} className="mt-3 min-h-11 rounded-xl border px-4 font-semibold">Qayta urinish</button></div>}
    {loading&&<p role="status">Faqat navbatdagi topshiriq yuklanmoqda…</p>}
    {!loading&&!error&&data&&!step&&<section className="space-y-4 rounded-3xl border bg-white p-6" aria-label="Seans yakuni"><CheckCircle2 className="text-emerald-600" size={36}/><h2 className="text-lg font-bold">{steps.length?`${completed} ta foydali qadam — bugunga yetarli.`:"Hozircha yangi topshiriq yo‘q."}</h2><p className="text-sm text-slate-600">{steps.length?"Mashq qilish, xatoni ko‘rish va takrorlash — barchasi oldinga qadam. Bu natija barcha javoblar to‘g‘ri degani emas. Dam olib, keyingi safar davom etishingiz mumkin.":"Rejaga qaytib darsingizni tanlang yoki keyinroq qayta tekshiring."}</p><button onClick={onExit} className="min-h-12 w-full rounded-xl bg-indigo-800 p-3 font-semibold text-white">Bugun yakunlash</button><Link to="/student" className="block text-center text-sm underline">Bosh sahifaga</Link></section>}
    {!loading&&!error&&step&&<section key={step.id} className="space-y-4 rounded-3xl border bg-white p-4 sm:p-6" aria-label="Joriy topshiriq">
      <p className="flex items-center gap-2 text-xs font-semibold text-indigo-700"><Flag size={15}/>{step.lesson}-dars · ~{step.minutes} daqiqa</p>
      <p className="text-sm text-slate-600">{step.reason}</p>
      {step.kind==="review" ? review?<Recall question={review} language={language} onDone={next} beforeSubmit={checkDay} nextLabel="Keyingi qadam →"/>:<div role="status"><p>Bu takrorlash navbati o‘zgargan. Rejani yangilang.</p><button onClick={next} className="min-h-11 underline">Rejani yangilash</button></div> : question&&section ? <>
        {section.text&&<div className="rounded-2xl bg-sky-50 p-4"><p className="mb-2 text-xs font-semibold text-sky-800">Avval matnni o‘qing</p><p lang={language} className="whitespace-pre-line break-words text-sm leading-7">{section.text}</p></div>}
        {section.skill==="listening"&&<CourseLessonAudio course={language==="de"?"german":"intensive"} lesson={step.lesson} title={section.title}/>}
        {section.skill==="speaking"&&language==="en"?<CourseSpeaking beforeSubmit={checkDay} lesson={step.lesson} questionId={question.id} onCommitted={()=>onAnswerSaved(step.lesson,question.id)} onSaved={()=>setSaved(true)}/>:<CourseAnswer key={step.id} question={question} number={index+1} language={language} lesson={step.lesson} drafts={drafts.current} beforeSubmit={checkDay} onCommitted={()=>onAnswerSaved(step.lesson,question.id)} onSaved={()=>setSaved(true)}/>}
        {saved&&<button onClick={next} className="min-h-12 w-full rounded-xl bg-indigo-800 p-3 font-bold text-white">{completed+1>=steps.length?"Natijani ko‘rish":"Keyingi qadam →"}</button>}
      </>:<div role="alert"><p>Topshiriq topilmadi. Darsni ochib davom etishingiz mumkin.</p><button onClick={()=>onLesson(step.lesson)} className="min-h-11 underline">To‘liq darsni ochish</button></div>}
      <details className="border-t pt-3 text-sm text-slate-500"><summary className="cursor-pointer">Yordam va dars</summary><p className="mt-2">Xato qilish mumkin. Avval urinib ko‘ring, keyin izohni o‘qing. Saqlangan qadamlaringiz qayta kirganda qoladi; yuborilmagan matn sahifani yangilaganda yo‘qolishi mumkin.</p><button onClick={()=>onLesson(step.lesson)} className="mt-2 min-h-11 underline">To‘liq darsni ochish</button></details>
    </section>}
  </main>;
}
