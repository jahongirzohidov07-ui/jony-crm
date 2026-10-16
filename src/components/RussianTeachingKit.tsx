import { useState, useRef } from 'react';
import { russianLessonPlan, russianScaffoldedPractice } from '../lib/russianTeaching';
import { russianTeacherLessons } from '../lib/russianTeacher';
import extendedData from '../data/russian/listening-extended.json';
import Practice from './IntensivePractice';
const panel='rounded-2xl border border-slate-200 bg-white p-5 md:p-6';
export function TeachingPlan({no}:{no:number}) {
 const [size,setSize]=useState(12); const plan=russianLessonPlan(no,size);
 return <section className={panel}><div className="flex flex-wrap items-center justify-between gap-4"><h3 className="text-xl font-bold">{plan.label} · 120 минут</h3><label className="text-sm">Учеников в группе <input aria-label="Учеников в группе" type="number" min={1} max={40} value={size} onChange={e=>setSize(Math.max(1,Math.min(40,Math.floor(Number(e.target.value))||1)))} className="ml-2 w-20 rounded-lg border p-2"/></label></div>
 <details className="mt-5 rounded-xl bg-slate-50 p-4"><summary className="cursor-pointer font-semibold">Подготовка к уроку · карточки, опоры и ключи</summary><ul className="mt-3 list-disc space-y-2 pl-5">{plan.preparation.map((s,i)=><li key={i}>{s}</li>)}</ul></details>{(plan.kind==='monthly'||plan.kind==='final')&&<p className="mt-4 rounded-xl bg-blue-50 p-4 leading-7" role="status">{plan.preparation.find(s=>s.startsWith('Один преподаватель:'))}</p>}
 <ol className="mt-6 space-y-4">{plan.timeline.map((stage,i)=>{const start=plan.timeline.slice(0,i).reduce((a,s)=>a+s.minutes,0);return <li key={i} className="flex gap-4 border-t pt-4"><span className="min-w-16 font-bold text-blue-700">{start}–{start+stage.minutes}</span><div><h4 className="font-semibold">{stage.title}</h4><p className="mt-1 leading-7 text-slate-600">{stage.instruction}</p></div></li>;})}</ol>
 <div className="mt-5 rounded-xl bg-amber-50 p-4"><h4 className="font-semibold">Проверка и организация группы</h4><ul className="mt-2 list-disc space-y-2 pl-5">{plan.assessment.map((s,i)=><li key={i}>{s}</li>)}</ul></div>
 <h4 className="mt-5 font-semibold">Что задать и как проверить</h4><ol className="mt-2 list-decimal space-y-2 pl-5">{plan.homework.map((s,i)=><li key={i}>{s}</li>)}</ol></section>;
}
export function ScaffoldedPractice({no}:{no:number}) {
 const tasks=russianScaffoldedPractice(no);
 return <><p className="rounded-xl bg-blue-50 p-4 leading-7">Сначала выполните задания с опорой на правило, затем повторите изученное без подсказок. Автопроверка сравнивает ответ с изученной моделью. Другую верную формулировку обсудите с преподавателем. В свободных ответах допустимы разные формулировки: их оценивает преподаватель по критериям.</p>
 <Practice key={`controlled-${no}`} locale="ru" title="1. Грамматика и речевые модели · с опорой" questions={tasks.controlled}/>
 <Practice key={`mixed-${no}`} locale="ru" title="2. Смешанное повторение · без конспекта" questions={tasks.mixed}/>
 <section className={panel}><h3 className="text-lg font-bold">3. Самостоятельная речь</h3><div className="mt-4 space-y-4">{tasks.production.map((q,i)=><div key={i} className="rounded-xl bg-slate-50 p-4"><p className="font-semibold">{i+1}. {q.prompt}</p><ul className="mt-2 list-disc pl-5 text-sm leading-6">{q.criteria.map((c,j)=><li key={j}>{c}</li>)}</ul><details className="mt-3"><summary className="cursor-pointer text-blue-700">Один из возможных ответов · после попытки</summary><p className="mt-2 whitespace-pre-line leading-7">{q.sample}</p></details></div>)}</div></section></>;
}
function AudioTrack({id,title}:{id:string;title:string}) {
 const ref=useRef<HTMLAudioElement>(null);const [failed,setFailed]=useState(false);
 const url=`/russian/audio/${id}.mp3`;
 return <div className="my-4 rounded-xl border border-blue-100 bg-blue-50 p-4"><p className="font-semibold">{title}</p><p className="mt-1 text-xs text-slate-600">Готовая учебная запись · синтезированные русские голоса. Это не запись живых носителей языка.</p>
 <audio ref={ref} controls preload="none" src={url} aria-label={title} className="mt-3 w-full" onError={()=>setFailed(true)} onPlay={e=>{document.querySelectorAll('audio').forEach(a=>{if(a!==e.currentTarget)a.pause();});setFailed(false);}}/>
 <div className="mt-3 flex flex-wrap items-center gap-4 text-sm"><label>Скорость <select aria-label={`Скорость: ${title}`} defaultValue="1" onChange={e=>{if(ref.current)ref.current.playbackRate=Number(e.target.value);}} className="ml-2 rounded border bg-white p-1"><option value="0.85">0,85×</option><option value="1">1×</option><option value="1.15">1,15×</option></select></label><a href={url} download className="font-semibold text-blue-700 underline">Скачать MP3 для урока без интернета</a></div>
 {failed&&<p role="alert" className="mt-2 text-rose-700">Аудио не загрузилось. Проверьте соединение или откройте ссылку MP3. Резерв: преподаватель читает текст дважды, ученики закрывают текст.</p>}</div>;
}
export function RussianListening({no}:{no:number}) {
 const lesson=russianTeacherLessons[no-1]; const ext=extendedData.find(x=>x.month===lesson.month)!;
 return <section className={panel}><h3 className="text-xl font-bold">Аудирование: от короткого диалога к самостоятельному пониманию</h3>
 <ol className="mt-3 list-decimal space-y-2 pl-5 text-slate-600"><li>До прослушивания прочитайте вопросы. Текст и ответы держите закрытыми.</li><li>Первое прослушивание — кто говорит, где и зачем? Второе — запишите детали.</li><li>Сравните ответы в парах, прослушайте спорный фрагмент, затем откройте текст.</li><li>Повторите две реплики с интонацией и разыграйте ситуацию с новыми деталями.</li></ol>
 <AudioTrack key={`lesson-${no}`} id={`lesson-${no}`} title={`Диалог урока ${no}`}/>
 <ol className="list-decimal space-y-4 pl-5">{lesson.questions.map((q,i)=><li key={i}><p>{q.prompt}</p><details className="mt-2 text-sm"><summary className="cursor-pointer text-blue-700">Ответ · после прослушивания</summary><p>{q.answer}</p></details></li>)}</ol>
 <details className="mt-5 rounded-xl bg-slate-50 p-4"><summary className="cursor-pointer font-semibold">Текст диалога и перевод</summary>{lesson.dialog.map((line,i)=><div key={i} className="mt-3"><p><strong>{line.speaker}:</strong> {line.ru}</p><details className="mt-1 text-sm text-slate-500"><summary>Перевод на узбекский</summary><p lang="uz">{line.uz}</p></details></div>)}</details>
 <div className="mt-8 border-t pt-6"><p className="text-sm font-semibold text-blue-700">Расширенное аудирование месяца {lesson.month} · плановый урок {ext.lesson}</p><h4 className="mt-2 text-xl font-bold">{ext.title}</h4><p className="mt-2 text-sm text-slate-600">{ext.format} · {ext.levelNote}</p><p className="mt-4 leading-7">{ext.preListening}</p><p className="mt-3 font-semibold">Первое прослушивание: {ext.firstTask.prompt}</p>
 <AudioTrack key={`extended-${ext.month}`} id={`extended-${ext.month}`} title={`Расширенное аудирование · месяц ${ext.month}`}/>
 <h5 className="font-semibold">Второе прослушивание: детали</h5><ol className="mt-3 list-decimal space-y-3 pl-5">{ext.questions.map((q,i)=><li key={i}>{q.prompt}</li>)}</ol>
 <details className="mt-4 rounded-xl bg-slate-50 p-4"><summary className="cursor-pointer font-semibold">Ответы и доказательства из записи</summary><p className="mt-3">Общий смысл: {ext.firstTask.answer}</p>{ext.questions.map((q,i)=><div key={i} className="mt-3"><p>{i+1}. {q.answer}</p><p className="text-sm text-slate-600">В записи: «{q.evidence}»</p></div>)}</details>
 <details className="mt-4 rounded-xl bg-slate-50 p-4"><summary className="cursor-pointer font-semibold">Текст расширенной записи</summary>{ext.lines.map((l,i)=><p key={i} className="mt-3 leading-7"><strong>{l.speaker}:</strong> {l.text}</p>)}</details>
 <p className="mt-4 rounded-xl bg-emerald-50 p-4"><strong>После прослушивания:</strong> {ext.followUp}</p><p className="mt-4 text-sm leading-7 text-slate-600"><strong>Преподавателю:</strong> {ext.teacherNotes}</p></div></section>;
}
