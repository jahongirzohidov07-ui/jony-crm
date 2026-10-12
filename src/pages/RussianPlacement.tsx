import { useEffect, useState } from 'react';
import brand from '../assets/brand-icon.png';
import { oralDirections, oralRubric, placementStages, publicRequest } from '../lib/russianPlacement';
import type { PlacementQuestion, RussianPlacementResult } from '../lib/russianPlacement';

const storageKey = 'jony-russian-placement-v1';
type Identity = { full_name: string; phone: string; branch_id: number };
type Attempt = { answers: Record<string, number>; index: number; done: boolean; identity?: Identity; attemptId?: string };
const empty = (): Attempt => ({ answers: {}, index: 0, done: false });
function restore(): Attempt {
  try {
    const v = JSON.parse(sessionStorage.getItem(storageKey) || 'null');
    if (!v || !v.identity || typeof v.identity.full_name !== 'string' || typeof v.identity.phone !== 'string'
      || !Number.isInteger(v.identity.branch_id) || typeof v.attemptId !== 'string'
      || !/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(v.attemptId)) return empty();
    const answers: Record<string, number> = {};
    for (let n = 1; n <= 48; n++) {
      const value = v.answers?.[`rp-${n}`];
      if (Number.isInteger(value) && value >= -1 && value < 4) answers[`rp-${n}`] = value;
    }
    return { answers, index: Number.isInteger(v.index) && v.index >= 0 && v.index < 48 ? v.index : 0,
      done: v.done === true && Object.keys(answers).length === 48, identity: v.identity, attemptId: v.attemptId };
  } catch { return empty(); }
}
const button = 'rounded-xl border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-800 disabled:opacity-40';
const primary = `${button} !border-blue-600 !bg-blue-600 !text-white`;
const skills = { grammar: 'Grammatika', vocabulary: 'Lug‘at', reading: 'O‘qib tushunish' };
const validPhone = (v: string) => /^(998)?[0-9]{9}$/.test(v.replace(/\D/g, ''));

export default function RussianPlacement() {
  const [attempt, setAttempt] = useState<Attempt>(restore);
  const [questions, setQuestions] = useState<PlacementQuestion[]>([]);
  const [branches, setBranches] = useState<{ id: number; name: string }[]>([]);
  const [name, setName] = useState(''), [phone, setPhone] = useState(''), [branch, setBranch] = useState(0);
  const [loading, setLoading] = useState(true), [loadError, setLoadError] = useState(''), [reload, setReload] = useState(0);
  const [storageError, setStorageError] = useState(false);
  const [result, setResult] = useState<RussianPlacementResult | null>(null);
  const [saving, setSaving] = useState(false), [saveError, setSaveError] = useState(''), [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = setTimeout(() => controller.abort(), 20000);
    setLoading(true); setLoadError('');
    Promise.all([
      publicRequest<{ questions: PlacementQuestion[] }>('/questions', undefined, controller.signal),
      fetch('/api/public/branches', { signal: controller.signal }).then(r => { if (!r.ok) throw Error(); return r.json(); }),
    ]).then(([bank, items]) => {
      if (active) { setQuestions(bank.questions); setBranches(items); }
    }).catch(() => { if (active) setLoadError('Savollar yoki filiallar yuklanmadi. Internetni tekshirib qayta urinib ko‘ring.'); })
      .finally(() => { clearTimeout(timeout); if (active) setLoading(false); });
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [reload]);
  useEffect(() => {
    try { sessionStorage.setItem(storageKey, JSON.stringify(attempt)); }
    catch { setStorageError(true); }
  }, [attempt]);
  useEffect(() => { window.scrollTo(0, 0); }, [attempt.index, attempt.done]);
  useEffect(() => {
    if (!attempt.done || !attempt.identity || !attempt.attemptId) return;
    let active = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    setSaving(true); setSaveError(''); setResult(null);
    publicRequest<{ saved: boolean; result: RussianPlacementResult }>('', {
      ...attempt.identity, attempt_id: attempt.attemptId, answers: attempt.answers,
    }, controller.signal).then(data => { if (active) setResult(data.result); })
      .catch(e => { if (active) setSaveError(e instanceof TypeError || e.name === 'AbortError'
        ? 'Internet bilan aloqa uzildi. Javoblar saqlangan, qayta yuboring.'
        : e.message || 'Natija saqlanmadi. Qayta yuboring.'); })
      .finally(() => { clearTimeout(timeout); if (active) setSaving(false); });
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [attempt, retry]);
  function start() {
    if (name.trim().length < 3 || !validPhone(phone) || !branches.some(b => b.id === branch)) return;
    setAttempt({ ...empty(), identity: { full_name: name.trim(), phone, branch_id: branch }, attemptId: crypto.randomUUID() });
  }
  function reset() {
    if (!window.confirm('Joriy javoblar o‘chiriladi. Yangi o‘quvchi uchun test ochilsinmi?')) return;
    setAttempt(empty()); setResult(null); setSaveError(''); setSaving(false); setName(''); setPhone(''); setBranch(0);
  }
  function download() {
    if (!result) return;
    const text = ['JONY — RUS TILI KIRISH TESTI', `Natija: ${result.score}/48`, result.label,
      `Filial: ${result.recommendation.branch_name}`,
      result.allPassed ? 'Yakuniy og‘zaki tekshiruv kerak' : `Tavsiya: ${result.month}-oy, ${result.lesson}-dars`,
      ...result.blocks.map(b => `${b.label}: ${b.correct}/8`),
      'Qaytarish: ' + (result.gaps.join(', ') || 'Asosiy bo‘shliq topilmadi.'),
      oralDirections, ...oralRubric].join('\n');
    const url = URL.createObjectURL(new Blob(['\ufeff' + text], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'rus-tili-kirish-natijasi.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const q = questions[attempt.index];
  const answered = Object.keys(attempt.answers).length;
  return <main lang="uz" className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900"><div className="mx-auto max-w-3xl space-y-6">
    <header className="rounded-3xl bg-slate-950 p-6 text-white md:p-9">
      <img src={brand} alt="Jony" className="h-10 w-10 rounded-xl" />
      <h1 className="mt-5 text-3xl font-bold">Rus tilini qayerdan boshlaymiz?</h1>
      <p className="mt-3 leading-7 text-slate-300">Noldan boshlanadigan bir yillik suhbat kursi · 48 savol · taxminan 25–35 daqiqa</p>
    </header>
    {storageError && <p role="status">Brauzer javoblarni saqlay olmadi. Test tugaguncha sahifani yangilamang.</p>}
    {loading && <p role="status">Savollar yuklanmoqda…</p>}
    {loadError && <div role="alert"><p>{loadError}</p><button className={button} onClick={() => setReload(n => n + 1)}>Qayta yuklash</button></div>}
    {!attempt.identity && !loading && !loadError && <section className="rounded-2xl bg-white p-6">
      <h2 className="text-xl font-bold">Sizga mos boshlanish nuqtasi</h2>
      <p className="mt-3 leading-7">Har ikki oylik bosqich uchun 8 savol: 4 ta grammatika, 2 ta lug‘at va 2 ta o‘qib tushunish. Javobni bilmasangiz, “Bilmayman”ni tanlang.</p>
      <p lang="ru" className="mt-3">Выберите один ответ. Если не знаете, нажмите «Bilmayman». Не пользуйтесь переводчиком и не просите подсказок.</p>
      <p className="mt-3 text-sm">Testdan so‘ng ustoz bilan og‘zaki tekshiruv shart. Natija til darajasini kafolatlamaydi va sizni avtomatik guruhga biriktirmaydi.</p>
      <form className="mt-5 space-y-3" onSubmit={e => { e.preventDefault(); start(); }}>
        <label className="block">Ism va familiya<input className="mt-1 block w-full rounded-xl border p-3" required minLength={3} maxLength={120} autoComplete="name" value={name} onChange={e => setName(e.target.value)} /></label>
        <label className="block">Telefon<input className="mt-1 block w-full rounded-xl border p-3" required type="tel" maxLength={24} placeholder="+998 90 123 45 67" autoComplete="tel" value={phone} onChange={e => setPhone(e.target.value)} /></label>
        <label className="block">Filial<select className="mt-1 block w-full rounded-xl border p-3" required value={branch || ''} onChange={e => setBranch(Number(e.target.value))}><option value="">Filialni tanlang</option>{branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></label>
        <p className="text-sm text-slate-500">Natijangiz shu ma’lumotlar bilan tanlangan filialning CRM tizimiga saqlanadi. Javoblar shu brauzer oynasida vaqtincha saqlanadi.</p>
        <button className={primary} disabled={name.trim().length < 3 || !validPhone(phone) || !branch}>Testni boshlash</button>
      </form>
    </section>}
    {attempt.identity && !attempt.done && q && <section className="rounded-2xl bg-white p-6">
      <div className="mb-3 flex justify-between gap-3 text-sm"><span>{placementStages[q.stage - 1]} · {skills[q.skill]}</span><span>{attempt.index + 1} / 48</span></div>
      <progress aria-label="Javob berilgan savollar" value={answered} max={48} className="mb-6 h-2 w-full accent-blue-600" />
      {q.text && <p lang="ru" className="mb-6 rounded-xl bg-blue-50 p-5 text-lg leading-8">{q.text}</p>}
      <fieldset><legend lang="ru" className="mb-5 text-xl font-semibold">{q.prompt}</legend>
        <div className="space-y-3">{q.options.map((option, i) => <label key={q.id + i} className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 ${attempt.answers[q.id] === i ? 'border-blue-600 bg-blue-50' : 'border-slate-200'}`}>
          <input type="radio" name={q.id} checked={attempt.answers[q.id] === i} onChange={() => setAttempt({ ...attempt, answers: { ...attempt.answers, [q.id]: i } })} /><span lang="ru">{option}</span>
        </label>)}
        <button type="button" aria-pressed={attempt.answers[q.id] === -1} className={`w-full rounded-xl border p-4 text-left font-semibold ${attempt.answers[q.id] === -1 ? 'border-blue-600 bg-blue-50' : 'border-slate-300'}`}
          onClick={() => setAttempt({ ...attempt, answers: { ...attempt.answers, [q.id]: -1 } })}>Bilmayman</button></div>
      </fieldset>
      <div className="mt-7 flex justify-between gap-3">
        <button className={button} disabled={attempt.index === 0} onClick={() => setAttempt({ ...attempt, index: attempt.index - 1 })}>Oldingi</button>
        <button className={primary} disabled={attempt.answers[q.id] === undefined || (attempt.index === 47 && answered < 48)}
          onClick={() => setAttempt(attempt.index === 47 ? { ...attempt, done: true } : { ...attempt, index: attempt.index + 1 })}>{attempt.index === 47 ? 'Natijani ko‘rish' : 'Keyingi'}</button>
      </div><p className="mt-4 text-sm text-slate-500">{answered} ta javob berildi. “Bilmayman” — 0 ball. Bilmagan savolda taxmin qilmang.</p>
    </section>}
    {attempt.done && <section className="rounded-2xl bg-white p-6" aria-live="polite">
      {saving && <p>Javoblar tekshirilmoqda va CRMga saqlanmoqda…</p>}
      {saveError && <div role="alert"><p>{saveError}</p><button className={button} onClick={() => setRetry(n => n + 1)}>Qayta yuborish</button></div>}
      {result && <><p className="text-sm font-semibold text-blue-600">Natija CRMga saqlandi · {result.score}/48</p>
        <h2 className="mt-3 text-2xl font-bold">{result.label}</h2>
        <p className="my-3">Filial: <strong>{result.recommendation.branch_name}</strong> · {result.allPassed ? 'Yakuniy og‘zaki tekshiruv kerak' : `${result.month}-oy, ${result.lesson}-darsdan boshlash tavsiya qilinadi`}</p>
        <p className="text-sm leading-7">{result.allPassed ? 'Olti blokda bilim mezoni bajarildi. Bu til darajasi kafolati emas.' : 'Birinchi mustahkamlanmagan bosqich tavsiya qilinadi. Keyingi to‘g‘ri javoblar oldingi bo‘shliqni yopmaydi.'} Guruhga qabulni ustoz og‘zaki tekshiruvdan keyin tasdiqlaydi.</p>
        <div className="my-5 grid gap-3 sm:grid-cols-2">{result.blocks.map(b => <div className="rounded-xl bg-slate-50 p-4" key={b.stage}>
          <strong>{b.label}</strong><p>{b.correct}/8 · {b.passed ? 'Mezon bajarildi' : 'Mustahkamlash kerak'}</p>
          <p className="text-sm">Grammatika: {b.grammar}/4 · O‘qish: {b.reading}/2</p>
        </div>)}</div>
        <p className="text-sm">Har blok uchun kamida 6/8, shundan grammatika 3/4 va o‘qib tushunish 1/2 kerak.</p>
        {result.gaps.length > 0 && <><h3 className="mt-5 font-bold">Avval qaytariladigan mavzular</h3><ul className="my-3 list-disc pl-5">{result.gaps.map(g => <li key={g}>{g}</li>)}</ul></>}
        <button className={button} onClick={download}>Natijani yuklash</button>
      </>}
    </section>}
    <section className="rounded-2xl border border-amber-200 bg-amber-50 p-6">
      <h2 className="font-bold">Alohida og‘zaki tekshiruv · guruhga qabuldan oldin shart</h2>
      <p className="my-3 text-sm leading-7">{oralDirections}</p>
      <ol className="list-decimal space-y-3 pl-5 text-sm leading-7">{oralRubric.map(item => <li key={item}>{item}</li>)}</ol>
    </section>
    {attempt.identity && <button className={button} disabled={saving} onClick={reset}>Yangi o‘quvchi uchun test</button>}
  </div></main>;
}
