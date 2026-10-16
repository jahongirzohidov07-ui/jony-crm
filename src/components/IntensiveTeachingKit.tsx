import { useState } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { intensiveTeachingKit } from '../lib/intensiveTeaching';
import type { IntensiveTeachingKit } from '../lib/intensiveTeaching';

function KitBody({kit, homeworkOnly=false, printView=false}:{kit:IntensiveTeachingKit;homeworkOnly?:boolean;printView?:boolean}) {
  const used = new Set([...kit.mandatoryExerciseIds,...kit.homework.flatMap(h=>h.exerciseIds)]);
  const required = kit.questions.filter(q=>used.has(q.id));
  const skills=kit.materials.skills;
  return <article className="space-y-4 text-sm leading-6">
    <h3 className="text-lg font-bold">{kit.lesson}-dars · {kit.profileLabel}</h3>
    {printView&&<p><b>USTOZ NUSXASI — javoblar, transkriptlar va modellar mavjud. O‘quvchi savol varag‘i emas.</b></p>}
    <p>{kit.objective}</p><p><b>Grammatik chegara:</b> {kit.boundary}</p>
    {!homeworkOnly&&<><p>{kit.groupSize} o‘quvchi · {kit.totalMinutes} daqiqa. Asosiy mashqlar majburiy; qo‘shimcha bank vaqtga qo‘shilmaydi.</p>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Doskaga yozish va tushuntirish</summary>{kit.materials.board.map(x=><p key={x}>{x}</p>)}<p>{kit.materials.explain}</p><p><b>Kutiladigan xato:</b> {kit.materials.commonMistake}</p><p>{kit.materials.differentiation}</p></details>
    <ol className="space-y-3">{kit.stages.map(s=><li key={s.start} className="rounded-lg bg-slate-50 p-3"><b>{s.start}–{s.end} · {s.title}</b><p>{s.instruction}</p><p className="break-words text-xs text-slate-500">Mashq havolalari: {s.exerciseIds.join(' · ')||'Ustoz ko‘rsatmasi'}</p></li>)}</ol>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Bugungi lug‘at · {kit.materials.vocabulary.length} so‘z</summary>{kit.materials.vocabulary.map(w=><p key={w.id}><span className="text-xs text-slate-500">{w.id} · </span><b>{w.word}</b> {w.ipa} — {w.meaning}<br/>{w.example} · {w.translation}</p>)}</details>
    {kit.exam&&<p>{kit.exam.notice}</p>}
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Asosiy mashqlar · savollar</summary><p className="text-xs text-slate-500">Sinf va uy vazifasi uchun aniq savollar. Javoblar alohida yopiq bo‘limda.</p>{required.map(q=><p key={q.id}><span className="block text-xs text-slate-500">{q.id}</span>{q.prompt}</p>)}</details>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Javob kalitlari — faqat ustoz uchun</summary><p>Mustaqil urinishdan keyin oching.</p>{required.map(q=><p key={q.id}><span className="block text-xs text-slate-500">{q.id}</span><b>{q.answers.join(' / ')}</b> · {q.explanation}</p>)}</details>
    {skills&&<><details open={printView||undefined}><summary className="cursor-pointer font-bold">O‘qish matni · {skills.reading.title}</summary><p>{skills.reading.text}</p></details>
    <p>Listening audio: <a className="text-blue-700 underline" href={kit.materials.audioUrl}>{kit.lesson}-dars MP3</a></p>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Tinglash transkripti — urinishdan keyin</summary><p>{kit.materials.audioUrl}</p><p>{skills.listening.text}</p></details>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Gapirish va yozish · vazifa va mezonlar</summary><p>{skills.speaking.prompt}</p><ul>{skills.speaking.success.map(x=><li key={x}>{x}</li>)}</ul><p>{skills.writing.prompt}</p><ul>{skills.writing.success.map(x=><li key={x}>{x}</li>)}</ul></details>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Yozish namunasi — mustaqil urinishdan keyin</summary><p>{skills.writing.model}</p></details></>}
    {kit.materials.previousSkills&&<details open={printView||undefined}><summary className="cursor-pointer font-bold">Uy vazifasi uchun avvalgi dars materiallari va namuna</summary><p>{kit.materials.previousSkills.reading.text}</p><p>{kit.materials.previousSkills.listening.text}</p><p>{kit.materials.previousSkills.writing.model}</p><p>{kit.materials.previousSkills.writing.success.join(' · ')}</p><p>{kit.materials.previousSkills.speaking.success.join(' · ')}</p></details>}
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Qo‘shimcha bank · {kit.extensionExerciseIds.length} savol va kalit</summary><p>{kit.extensionInstruction}</p>{kit.questions.filter(q=>kit.extensionExerciseIds.includes(q.id)).map(q=><p key={q.id}><span className="block text-xs text-slate-500">{q.id}</span>{q.prompt} → {q.answers.join(' / ')}. {q.explanation}</p>)}</details>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Chiqish bileti — ustoz kaliti</summary>{kit.exitTicket.map(x=><p key={x}>{x}</p>)}</details></>}
    {kit.unseenHomework&&<details open={printView||undefined}><summary className="cursor-pointer font-bold">Haftalik yangi matn · {kit.unseenHomework.title}</summary><p className="whitespace-pre-line">{kit.unseenHomework.text}</p><ol className="list-decimal pl-5">{kit.unseenHomework.tasks.map(task=><li key={task.id} className="my-2"><p>{task.prompt}</p>{task.options.map(option=><p key={option}>{option}</p>)}<details open={printView||undefined}><summary>Ustoz kaliti · mustaqil urinishdan keyin</summary><p>{task.teacher.answer}</p><p>Dalil: {task.teacher.evidence.join(' / ')}</p></details></li>)}</ol></details>}
    <h4 className="font-bold">Uy vazifasi · {kit.homeworkMinutes} daqiqa</h4><ol className="space-y-2">{kit.homework.map(h=><li key={h.task}><b>{h.minutes} daqiqa:</b> {h.task}</li>)}</ol>
    <p>Vaqt tugasa qolgan mashqlarni belgilang va keyingi ustozga topshiring. Qo‘shimcha bank asosiy 120 daqiqaga kirmaydi.</p>
    <details open={printView||undefined}><summary className="cursor-pointer font-bold">Keyingi ustozga topshirish</summary><p>{kit.handoff.nextLesson ? `${kit.handoff.nextLesson}-dars: ` : ''}{kit.handoff.nextObjective}</p><p>{kit.handoff.instruction}</p>{kit.handoff.fields.map(x=><p key={x}>{x}: ____________________</p>)}</details>
  </article>;
}
export default function IntensiveTeachingKitView({lesson,homeworkOnly=false}:{lesson:number;homeworkOnly?:boolean}) {
  const [size,setSize]=useState(16), [error,setError]=useState('');
  const kit=intensiveTeachingKit(lesson,size);
  function printKit() {
    const win=window.open('','_blank');
    if(!win){setError('Chop etish oynasi bloklandi. Brauzerda yangi oynaga ruxsat bering.');return;}
    setError('');
    win.document.write('<!doctype html><html lang="uz"><head><meta charset="utf-8"><title>Jony — '+lesson+'-dars ustoz to‘plami</title><style>body{font:11pt/1.5 Arial;margin:18mm;color:#10213b}h3,h4,summary{break-after:avoid}li{margin-bottom:10px}summary{font-weight:bold}p{overflow-wrap:anywhere}@page{size:A4;margin:12mm}</style></head><body>'+renderToStaticMarkup(<KitBody kit={kit} homeworkOnly={homeworkOnly} printView/> )+'</body></html>');
    win.document.close();win.focus();win.print();
  }
  return <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-6"><div className="mb-4 flex flex-wrap gap-3"><label>Guruh hajmi <input type="number" min={1} max={60} value={size} onChange={e=>setSize(Math.max(1,Math.min(60,Number(e.target.value)||1)))} className="w-20 rounded border p-2"/></label><button type="button" onClick={printKit} className="rounded border px-4 py-2 font-semibold">Ustoz nusxasini chop etish</button></div>{error&&<p role="alert">{error}</p>}<KitBody kit={kit} homeworkOnly={homeworkOnly}/></section>;
}
