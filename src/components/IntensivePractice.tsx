import { useId, useState } from 'react';
import { Eye, RotateCcw } from 'lucide-react';
import { isCorrect } from '../lib/intensive';
import type { Question } from '../lib/intensive';
const button='inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-blue-400 hover:text-blue-700 disabled:opacity-40';
const panel='rounded-2xl border border-slate-200 bg-white p-4 md:p-6';

const labels = {
  "uz": {
    "empty": "Bu to‘plamda mashq yo‘q.",
    "questions": "savol",
    "note": "Natija shu mashg‘ulot uchun; rasmiy bahoga yozilmaydi.",
    "hint": "Yordam",
    "placeholder": "Javobingiz…",
    "correct": "✓ To‘g‘ri",
    "retry": "Qayta mashq qiling",
    "sample": "Namuna:",
    "check": "Tekshirish",
    "hide": "Javoblarni yopish",
    "answers": "Javoblar",
    "reset": "Qaytadan",
    "mistakes": "Faqat xatolar",
    "score": "to‘g‘ri",
    "viewed": " · Javoblar ko‘rilgan mashq"
  },
  "ru": {
    "empty": "В этом наборе нет упражнений.",
    "questions": "Вопросов:",
    "note": "Результат относится только к этому упражнению и не учитывается в официальной оценке.",
    "hint": "Подсказка",
    "placeholder": "Ваш ответ…",
    "correct": "✓ Верно",
    "retry": "Попробуйте ещё раз",
    "sample": "Пример:",
    "check": "Проверить",
    "hide": "Скрыть ответы",
    "answers": "Ответы",
    "reset": "Начать заново",
    "mistakes": "Только ошибки",
    "score": "верно",
    "viewed": " · Упражнение с просмотренными ответами"
  }
};

export default function IntensivePractice({questions,title,locale='uz'}:{questions:Question[];title:string;locale?:'uz'|'ru'}) {
  const text=labels[locale];
  const instance=useId();
  const [answers,setAnswers]=useState<Record<string,string>>({});
  const [checked,setChecked]=useState(false);
  const [retry,setRetry]=useState<string[]|null>(null);
  const [revealed,setRevealed]=useState(false);
  const active=retry?questions.filter(q=>retry.includes(q.id)):questions;
  const wrong=active.filter(q=>!isCorrect(answers[q.id]??'',q.answers,q.caseSensitive));
  if(!active.length) return <p className="text-sm text-slate-500">{text.empty}</p>;
  return <section className={panel} aria-label={title}>
    <h3 className="font-bold text-slate-900">{title} <span className="text-sm font-normal text-slate-500">· {locale==='ru'?`${text.questions} ${active.length}`:`${active.length} ${text.questions}`}</span></h3>
    <p className="mt-1 text-xs leading-5 text-slate-500">{text.note}</p>
    <form className="mt-4 space-y-4" onSubmit={e=>{e.preventDefault();setChecked(true);}}>
      {active.map((q,i)=><div key={q.id} className="rounded-xl bg-slate-50 p-3">
        <label htmlFor={`${instance}-${q.id}`} className="block text-sm font-medium leading-6 text-slate-800">{i+1}. {q.prompt}</label>
        {q.hint&&<details className="my-1 text-xs text-slate-500"><summary className="cursor-pointer">{text.hint}</summary><p className="mt-1">{q.hint}</p></details>}
        <input id={`${instance}-${q.id}`} autoComplete="off" spellCheck={false} value={answers[q.id]??''} onChange={e=>{setAnswers({...answers,[q.id]:e.target.value});setChecked(false);}} aria-invalid={checked&&!isCorrect(answers[q.id]??'',q.answers,q.caseSensitive)} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder={text.placeholder} />
        {checked&&<p className={`mt-2 text-sm ${isCorrect(answers[q.id]??'',q.answers,q.caseSensitive)?'text-emerald-700':'text-rose-700'}`}>{isCorrect(answers[q.id]??'',q.answers,q.caseSensitive)?text.correct:text.retry} · {q.answers.join(' / ')}<span className="mt-1 block text-slate-600">{q.explanation}</span></p>}
        {!checked&&revealed&&<p className="mt-2 text-sm text-blue-700">{text.sample} {q.answers.join(' / ')} · {q.explanation}</p>}
      </div>)}
      <div className="flex flex-wrap gap-2"><button className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700" type="submit">{text.check}</button><button type="button" className={button} onClick={()=>setRevealed(!revealed)}><Eye size={16}/>{revealed?text.hide:text.answers}</button>
        <button type="button" className={button} onClick={()=>{setAnswers({});setChecked(false);setRevealed(false);setRetry(null);}}><RotateCcw size={16}/>{text.reset}</button>
        {checked&&wrong.length>0&&<button type="button" className={button} onClick={()=>{setRetry(wrong.map(q=>q.id));setAnswers({});setChecked(false);setRevealed(false);}}>{text.mistakes} ({wrong.length})</button>}
      </div>
      {checked&&<p role="status" className="rounded-xl bg-blue-50 p-3 font-semibold text-blue-800">{active.length-wrong.length}/{active.length} {text.score} · {Math.round((active.length-wrong.length)/active.length*100)}%{revealed?text.viewed:''}</p>}
    </form>
  </section>;
}
