import { useId, useState } from 'react';
import { Eye, RotateCcw } from 'lucide-react';
import { isCorrect } from '../lib/intensive';
import type { Question } from '../lib/intensive';
const button='inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-blue-400 hover:text-blue-700 disabled:opacity-40';
const panel='rounded-2xl border border-slate-200 bg-white p-4 md:p-6';

export default function IntensivePractice({questions,title}:{questions:Question[];title:string}) {
  const instance=useId();
  const [answers,setAnswers]=useState<Record<string,string>>({});
  const [checked,setChecked]=useState(false);
  const [retry,setRetry]=useState<string[]|null>(null);
  const [revealed,setRevealed]=useState(false);
  const active=retry?questions.filter(q=>retry.includes(q.id)):questions;
  const wrong=active.filter(q=>!isCorrect(answers[q.id]??'',q.answers,q.caseSensitive));
  if(!active.length) return <p className="text-sm text-slate-500">Bu to‘plamda mashq yo‘q.</p>;
  return <section className={panel} aria-label={title}>
    <h3 className="font-bold text-slate-900">{title} <span className="text-sm font-normal text-slate-500">· {active.length} savol</span></h3>
    <p className="mt-1 text-xs leading-5 text-slate-500">Natija shu mashg‘ulot uchun; rasmiy bahoga yozilmaydi.</p>
    <form className="mt-4 space-y-4" onSubmit={e=>{e.preventDefault();setChecked(true);}}>
      {active.map((q,i)=><div key={q.id} className="rounded-xl bg-slate-50 p-3">
        <label htmlFor={`${instance}-${q.id}`} className="block text-sm font-medium leading-6 text-slate-800">{i+1}. {q.prompt}</label>
        {q.hint&&<details className="my-1 text-xs text-slate-500"><summary className="cursor-pointer">Yordam</summary><p className="mt-1">{q.hint}</p></details>}
        <input id={`${instance}-${q.id}`} autoComplete="off" spellCheck={false} value={answers[q.id]??''} onChange={e=>{setAnswers({...answers,[q.id]:e.target.value});setChecked(false);}} aria-invalid={checked&&!isCorrect(answers[q.id]??'',q.answers,q.caseSensitive)} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Javobingiz…" />
        {checked&&<p className={`mt-2 text-sm ${isCorrect(answers[q.id]??'',q.answers,q.caseSensitive)?'text-emerald-700':'text-rose-700'}`}>{isCorrect(answers[q.id]??'',q.answers,q.caseSensitive)?'✓ To‘g‘ri':'Qayta mashq qiling'} · {q.answers.join(' / ')}<span className="mt-1 block text-slate-600">{q.explanation}</span></p>}
        {!checked&&revealed&&<p className="mt-2 text-sm text-blue-700">Namuna: {q.answers.join(' / ')} · {q.explanation}</p>}
      </div>)}
      <div className="flex flex-wrap gap-2"><button className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700" type="submit">Tekshirish</button><button type="button" className={button} onClick={()=>setRevealed(!revealed)}><Eye size={16}/>{revealed?'Javoblarni yopish':'Javoblar'}</button>
        <button type="button" className={button} onClick={()=>{setAnswers({});setChecked(false);setRevealed(false);setRetry(null);}}><RotateCcw size={16}/>Qaytadan</button>
        {checked&&wrong.length>0&&<button type="button" className={button} onClick={()=>{setRetry(wrong.map(q=>q.id));setAnswers({});setChecked(false);setRevealed(false);}}>Faqat xatolar ({wrong.length})</button>}
      </div>
      {checked&&<p role="status" className="rounded-xl bg-blue-50 p-3 font-semibold text-blue-800">{active.length-wrong.length}/{active.length} to‘g‘ri · {Math.round((active.length-wrong.length)/active.length*100)}%{revealed?' · Javoblar ko‘rilgan mashq':''}</p>}
    </form>
  </section>;
}
