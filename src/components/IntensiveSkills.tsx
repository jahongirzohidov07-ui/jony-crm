import { useEffect, useRef, useState } from 'react';
import { Headphones, Square, Volume2 } from 'lucide-react';
import Practice from './IntensivePractice';
import { productionRubric, skillQuestions } from '../lib/intensive-skills';
import type { SkillPack } from '../lib/intensive-skills';

const button = 'rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40';
const panel = 'rounded-2xl border border-slate-200 bg-white p-4 md:p-6';

function ListeningPlayer({ text }: { text: string }) {
  const [playing, setPlaying] = useState(false);
  const [rate, setRate] = useState(0.9);
  const [message, setMessage] = useState('');
  const active = useRef<SpeechSynthesisUtterance | null>(null);
  useEffect(() => () => {
    if (active.current) {
      active.current.onend = null;
      active.current.onerror = null;
      window.speechSynthesis?.cancel();
    }
  }, []);
  function stop() {
    if (active.current) {
      active.current.onend = null;
      active.current.onerror = null;
      window.speechSynthesis.cancel();
      active.current = null;
    }
    setPlaying(false);
  }
  function play() {
    if (!('speechSynthesis' in window)) {
      setMessage('Qurilmangiz ovozli o‘qishni qo‘llamaydi. Ustoz quyidagi transkriptni ikki marta o‘qib beradi.');
      return;
    }
    stop();
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    const english = voices.find(v => /^en[-_]GB/i.test(v.lang)) ?? voices.find(v => /^en/i.test(v.lang));
    if (voices.length && !english) {
      setMessage('Inglizcha ovoz topilmadi. Ustoz transkriptni o‘qib bersin yoki qurilmaga inglizcha ovoz qo‘shing.');
      return;
    }
    if (english) utterance.voice = english;
    utterance.lang = 'en-GB';
    utterance.rate = rate;
    utterance.onend = () => { setPlaying(false); active.current = null; };
    utterance.onerror = () => { setPlaying(false); active.current = null; setMessage('Ovoz ishga tushmadi. Transkript orqali ustoz bilan tinglash mashqini bajaring.'); };
    active.current = utterance;
    setMessage(''); setPlaying(true);
    window.speechSynthesis.speak(utterance);
  }
  return <div className="rounded-xl bg-blue-50 p-4">
    <p className="text-sm leading-6 text-blue-950">1-tinglash: asosiy fikr. 2-tinglash: savollarga javob. Transkriptni tekshiruvdan keyin oching.</p>
    <div className="mt-3 flex flex-wrap items-center gap-3">
      <button type="button" onClick={play} disabled={playing} className={`${button} inline-flex items-center gap-2`}><Volume2 size={16} />Tinglash</button>
      <button type="button" onClick={stop} disabled={!playing} className={`${button} inline-flex items-center gap-2`}><Square size={14} />To‘xtatish</button>
      <label className="text-sm">Tezlik <select value={rate} disabled={playing} onChange={e => setRate(Number(e.target.value))} className="ml-2 rounded-lg border border-blue-200 bg-white p-2"><option value={0.75}>Sekin</option><option value={0.9}>O‘rtacha</option><option value={1}>Tabiiy</option></select></label>
    </div>
    <p className="mt-2 text-xs leading-5 text-slate-600">Qurilmaning sun’iy ovozi. Talaffuz va ovoz mavjudligi qurilmaga bog‘liq; ustoz transkriptni tabiiy ovozda ham o‘qib beradi.</p>
    {message && <p role="status" className="mt-2 text-sm text-amber-900">{message}</p>}
  </div>;
}

export default function IntensiveSkills({ pack }: { pack: SkillPack }) {
  const [mode, setMode] = useState<'reading' | 'listening' | 'production'>('reading');
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
    </>}
    {mode === 'listening' && <>
      <div className={panel}><h4 className="mb-3 flex items-center gap-2 text-lg font-bold"><Headphones size={20} />{pack.listening.title}</h4><ListeningPlayer key={pack.lesson} text={pack.listening.text} /></div>
      <Practice key={`listening-${pack.lesson}`} title="Tinglab tushunish" questions={skillQuestions(pack, 'listening')} />
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
  </section>;
}
