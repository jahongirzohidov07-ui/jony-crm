import { useId, useRef, useState } from 'react';
import { checkPracticeAnswer, getPracticeFamily, practiceThemes, readPracticeTheme, savePracticeTheme } from '../lib/coursePracticeChoice';
import type { PracticeFamily, PracticeQuestion, PracticeTheme } from '../lib/coursePracticeChoice';

/** Render before (never instead of) the original unsaved grammar question.
 * No answer, reward, progress, or mastery callback: this is local practice only.
 */
export type CoursePracticeChoiceProps = { question: PracticeQuestion; language: string; lesson: number };
export default function CoursePracticeChoice({ question, language, lesson }: CoursePracticeChoiceProps) {
  const family = getPracticeFamily(question, language, lesson);
  // Unsupported targets offer a strategy, never a fabricated theme or answer hint.
  return family ? <PracticePanel key={`${language}:${lesson}:${question.id}:${question.prompt}`} family={family}/> : <StudyStrategy key={`${language}:${lesson}:${question.id}:${question.prompt}`}/>;
}
function PracticePanel({ family }: { family: PracticeFamily }) {
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<PracticeTheme>(() => readPracticeTheme(family));
  const [guided, setGuided] = useState(false);
  const [answer, setAnswer] = useState('');
  const [checked, setChecked] = useState(false);
  const id = useId();
  const toggle = useRef<HTMLButtonElement>(null);
  const exercise = family.variants[theme];
  const correct = checked && checkPracticeAnswer(exercise, answer);
  const button = 'min-h-11 rounded-xl border px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700';
  function choose(next: PracticeTheme) {
    setTheme(next); savePracticeTheme(family, next); setAnswer(''); setChecked(false);
  }
  return <section aria-label="Ixtiyoriy qo‘shimcha mashq" className="space-y-3 rounded-2xl border border-indigo-100 bg-indigo-50 p-4">
    <button ref={toggle} type="button" aria-expanded={open} aria-controls={`${id}-panel`} onClick={() => setOpen(!open)} className={button}>
      {open ? 'Qo‘shimcha mashqni yig‘ish' : 'Avval mavzuli mashq qilib ko‘rish (ixtiyoriy)'}
    </button>
    <p className="text-xs text-slate-600">Bu tayyorlov mashqi. Natija kunlik reja va tangalarga qo‘shilmaydi. Asosiy savolga darhol o‘tishingiz mumkin.</p>
    <div id={`${id}-panel`} hidden={!open} className="space-y-3">
      <p className="text-sm font-semibold">{family.title}</p>
      <fieldset><legend className="mb-2 text-sm">Mashq vaziyatini tanlang</legend><div className="flex flex-wrap gap-2">
        {practiceThemes.map(t => <button key={t.id} type="button" aria-pressed={theme === t.id} className={`${button} ${theme === t.id ? 'bg-indigo-800 text-white' : 'bg-white'}`} onClick={() => choose(t.id)}>{t.label}</button>)}
      </div></fieldset>
      <fieldset><legend className="mb-2 text-sm">Qanday mashq qilasiz?</legend><div className="flex flex-wrap gap-2">
        <button type="button" aria-pressed={!guided} onClick={() => setGuided(false)} className={button}>Mustaqil sinov</button>
        <button type="button" aria-pressed={guided} onClick={() => setGuided(true)} className={button}>Tayanch bilan</button>
      </div></fieldset>
      <p id={`${id}-prompt`} lang={family.language} className="text-sm leading-6">{exercise.prompt}</p>
      {guided && <p id={`${id}-hint`} className="rounded-xl bg-white p-3 text-sm">Faqat shu qo‘shimcha mashq uchun yordam: {exercise.scaffold}</p>}
      <label htmlFor={`${id}-answer`} className="block text-sm font-medium">Qo‘shimcha mashq javobi</label>
      <input id={`${id}-answer`} lang={family.language} value={answer} maxLength={80} autoComplete="off" spellCheck={false} aria-describedby={`${id}-prompt${guided ? ` ${id}-hint` : ''}`} onChange={e => { setAnswer(e.target.value); setChecked(false); }} className="min-h-11 w-full rounded-xl border bg-white px-3"/>
      <button type="button" disabled={!answer.trim()} className={`${button} bg-white disabled:opacity-50`} onClick={() => { if (answer.trim()) setChecked(true); }}>Mashq javobini tekshirish</button>
      <div role="status" aria-live="polite">{checked && <p className="text-sm">{correct ? 'Qo‘shimcha mashq to‘g‘ri. ' : 'Hali mos kelmadi. '}{correct ? exercise.explanation : 'Qisqa javob yozing; kerak bo‘lsa “Tayanch bilan” usulini tanlang.'}</p>}</div>
      {correct && <button type="button" className={button} onClick={() => { setOpen(false); toggle.current?.focus(); }}>Mashqni yig‘ish va asosiy savolga o‘tish</button>}
    </div>
  </section>;
}



function StudyStrategy() {
  const [strategy, setStrategy] = useState<'read' | 'check'>('read');
  return <details className="rounded-2xl border border-slate-200 p-3 text-sm">
    <summary className="min-h-11 cursor-pointer py-2">Mashq usulini tanlash (ixtiyoriy)</summary>
    <p>Bu savol uchun tekshirilgan mavzuli variant yo‘q. Asosiy savolga darhol o‘tishingiz mumkin.</p>
    <fieldset className="mt-3"><legend>O‘rganish usuli</legend><div className="mt-2 flex flex-wrap gap-2">
      <button type="button" aria-pressed={strategy === 'read'} onClick={() => setStrategy('read')} className="min-h-11 rounded-xl border px-3">Topshiriqni ajratish</button>
      <button type="button" aria-pressed={strategy === 'check'} onClick={() => setStrategy('check')} className="min-h-11 rounded-xl border px-3">Javobni tekshirish rejasi</button>
    </div></fieldset>
    <p role="status" className="mt-3">{strategy === 'read'
      ? 'Avval ko‘rsatmani o‘qing: bitta so‘z, bo‘shliqdagi qism yoki butun gap so‘ralganmi? Keyin o‘zingiz javob yozing.'
      : 'Yuborishdan oldin javob hajmi ko‘rsatmaga mosligini, imlo va bosh harflarni tekshiring. Bu usul javobning to‘g‘riligini baholamaydi.'}</p>
  </details>;
}
