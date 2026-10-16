import { useState } from 'react';
import { Headphones } from 'lucide-react';
import Practice from './IntensivePractice';
import CourseLessonAudio from './CourseLessonAudio';
import IntensiveSkillsExtension, { IntensiveWeeklyHomework } from './intensiveSkillsExtension';
import authenticListening from '../data/intensive-authentic-listening.json';
import { productionRubric, skillQuestions } from '../lib/intensive-skills';
import type { SkillPack } from '../lib/intensive-skills';

const button = 'rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40';
const panel = 'rounded-2xl border border-slate-200 bg-white p-4 md:p-6';

export default function IntensiveSkills({ pack }: { pack: SkillPack }) {
  const [mode, setMode] = useState<'reading' | 'listening' | 'production'>('reading');
  const authentic = authenticListening.find(item => item.lesson === pack.lesson);
  return <section className="space-y-4" aria-label="To‘rt ko‘nikma mashqlari">
    <div className={panel}>
      <p className="text-xs font-bold uppercase tracking-wide text-blue-600">{pack.level} · {pack.lesson}-dars</p>
      <h3 className="mt-2 text-lg font-bold text-slate-900">Bugungi natija</h3><p className="mt-2 text-sm leading-6 text-slate-700">{pack.objective}</p>
      <details className="mt-3 rounded-xl bg-amber-50 p-3 text-sm leading-6 text-amber-950"><summary className="cursor-pointer font-semibold">Ustoz: tayyorlash va o‘tkazish</summary><p className="mt-2 whitespace-pre-line">{pack.teacherNote}</p></details>
    </div>
    <nav aria-label="Ko‘nikma tanlash" className="flex flex-wrap gap-2">
      {([['reading', 'Reading'], ['listening', 'Listening'], ['production', 'Speaking / Writing']] as const).map(([key, label]) => <button key={key} className={`${button} ${mode === key ? '!border-blue-600 !bg-blue-50 !text-blue-800' : ''}`} aria-pressed={mode === key} onClick={() => setMode(key)}>{label}</button>)}
    </nav>
    {mode === 'reading' && <>
      <article className={panel}><h4 className="text-lg font-bold">{pack.reading.title}</h4><p className="mt-3 whitespace-pre-line text-base leading-8 text-slate-700">{pack.reading.text}</p></article>
      <Practice key={`reading-${pack.lesson}`} title="Matnni tushunish" questions={skillQuestions(pack, 'reading')} />
      <IntensiveSkillsExtension key={pack.lesson} pack={pack} mode="reading" />
    </>}
    {mode === 'listening' && <>
      {authentic && <aside className={panel} aria-label="Authentic listening">
        <h4 className="font-bold">{authentic.title} · {authentic.level}</h4>
        <p className="mt-2 text-sm leading-6 text-slate-700">{authentic.focus}</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">{authentic.minutes} daqiqa: 120 daqiqalik uy vazifasining odatdagi reading/listening bloki o‘rniga; qo‘shimcha vaqt emas.</p>
        <a className="mt-3 inline-block text-sm font-semibold text-blue-700 underline" href={authentic.url} target="_blank" rel="noreferrer">{authentic.provider} · {authentic.title}</a>
        <p className="mt-2 text-sm leading-6 text-slate-600">Asl saytda: Preparation → audio → Task 1 → Task 2 → javoblarni tekshirish. Ustoz tashqi saytdagi worksheet va uning kalitidan foydalanadi. Natija Jony kabinetiga avtomatik ko‘chirilmaydi.</p>
      </aside>}
      <div className={panel}><h4 className="mb-3 flex items-center gap-2 text-lg font-bold"><Headphones size={20} />{pack.listening.title}</h4><CourseLessonAudio key={pack.lesson} course="intensive" lesson={pack.lesson} title={pack.listening.title} /></div>
      <Practice key={`listening-${pack.lesson}`} title="Tinglab tushunish" questions={skillQuestions(pack, 'listening')} />
      <IntensiveSkillsExtension key={pack.lesson} pack={pack} mode="listening" />
      <details className={panel}><summary className="cursor-pointer font-semibold">Transkript — tekshirgandan keyin oching</summary><p className="mt-3 whitespace-pre-line text-base leading-8 text-slate-700">{pack.listening.text}</p></details>
    </>}
    {mode === 'production' && <>
      {(['speaking', 'writing'] as const).map(skill => <div key={skill} className={panel}>
        <h4 className="text-lg font-bold">{skill === 'speaking' ? 'Speaking · gapirish' : 'Writing · yozish'}</h4>
        <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">{pack[skill].prompt}</p>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">{pack[skill].success.map(item => <li key={item}>{item}</li>)}</ul>
        {skill === 'writing' && <details className="mt-4 rounded-xl bg-slate-50 p-3"><summary className="cursor-pointer text-sm font-semibold">Namuna — o‘z matningizdan keyin solishtiring</summary><p className="mt-2 whitespace-pre-line text-sm leading-7">{pack.writing.model}</p></details>}
      </div>)}
      <div className={panel}><h4 className="font-bold">Ustozning tekshiruv mezoni</h4><p className="mt-2 text-sm leading-6 text-slate-500">Har mezon: 0 — hali bajarmadi, 1 — yordam bilan, 2 — mustaqil bajardi. Jami 8 ball. Bu ichki mashq mezoni; milliy sertifikat bali emas.</p><dl className="mt-3 space-y-3">{productionRubric.map(([title, description]) => <div key={title}><dt className="text-sm font-semibold">{title}</dt><dd className="mt-1 text-sm leading-6 text-slate-600">{description}</dd></div>)}</dl><p className="mt-4 text-sm leading-6 text-blue-800">6/8 dan past yoki bir mezon 0 bo‘lsa: aynan shu bandni qayta mashq qildiring. Bitta yaxshi jihat, bitta tuzatish va qayta topshirish vazifasini ayting.</p></div>
    </>}
    <IntensiveWeeklyHomework key={pack.lesson} lesson={pack.lesson} />
  </section>;
}
