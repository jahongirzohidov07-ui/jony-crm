import { useEffect, useState } from 'react';
import brand from '../assets/brand-icon.png';
import { oralDirections, oralRubric, placementStages, publicRequest } from '../lib/russianPlacement';
import type { PlacementQuestion, RussianPlacementResult } from '../lib/russianPlacement';
import { useSeqPlacement } from '../lib/placementSeq';
import PlacementChoices from '../components/PlacementChoices';

// 2026-10-22: savollar serverdan bittadan keladi (faqat oldinga). Javob
// vaqtini server o'lchaydi — savolni o'qimay bosilgan to'g'ri javob ham
// xato. "Bilmayman" — oxirgi alohida tanlov (-1), server savolda idk:true
// yuborganda chiqadi. Deploydan oldin boshlangan urinish (state yo'q)
// bugungidek /questions bilan oxirigacha ishlanadi (legacy).
const storageKey = 'jony-russian-placement-v1';
const BASE = '/api/public/russian-placement';
const TOTAL = 48;
const IDS = Array.from({ length: TOTAL }, (_, i) => `rp-${i + 1}`);
const button = 'rounded-xl border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-800 disabled:opacity-40';
const primary = `${button} !border-blue-600 !bg-blue-600 !text-white`;
const skills = { grammar: 'Grammatika', vocabulary: 'Lug‘at', reading: 'O‘qib tushunish' };
const validPhone = (v: string) => /^(998)?[0-9]{9}$/.test(v.replace(/\D/g, ''));

export default function RussianPlacement() {
  const t = useSeqPlacement<RussianPlacementResult>({ base: BASE, storageKey, total: TOTAL, ids: IDS });
  const { attempt, setAttempt, question, pick, setPick, busy, stepError, stateBroken } = t;
  const [legacy, setLegacy] = useState<PlacementQuestion[]>([]);
  const [branches, setBranches] = useState<{ id: number; name: string }[]>([]);
  const [name, setName] = useState(''), [phone, setPhone] = useState(''), [branch, setBranch] = useState(0);
  const [loading, setLoading] = useState(true), [loadError, setLoadError] = useState(''), [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = setTimeout(() => controller.abort(), 20000);
    const needLegacy = attempt.mode === 'legacy' && attempt.started && !attempt.done && !legacy.length;
    setLoading(true); setLoadError('');
    Promise.all([
      needLegacy ? publicRequest<{ questions: PlacementQuestion[] }>('/questions', undefined, controller.signal) : Promise.resolve(null),
      branches.length ? Promise.resolve(branches) : fetch('/api/public/branches', { signal: controller.signal }).then(r => { if (!r.ok) throw Error(); return r.json(); }),
    ]).then(([bank, items]) => {
      if (!active) return;
      if (bank) setLegacy(bank.questions);
      setBranches(items);
    }).catch(() => { if (active) setLoadError('Savollar yoki filiallar yuklanmadi. Internetni tekshirib qayta urinib ko‘ring.'); })
      .finally(() => { clearTimeout(timeout); if (active) setLoading(false); });
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, attempt.mode, attempt.started, attempt.done]);
  useEffect(() => { window.scrollTo(0, 0); }, [attempt.index, attempt.done, question?.id]);
  function start() {
    if (name.trim().length < 3 || !validPhone(phone) || !branches.some(b => b.id === branch)) return;
    void t.start({ full_name: name.trim(), phone, branch_id: branch });
  }
  function reset() {
    if (!window.confirm('Joriy javoblar o‘chiriladi. Yangi o‘quvchi uchun test ochilsinmi?')) return;
    t.reset(); setName(''); setPhone(''); setBranch(0);
  }
  const result = attempt.result ?? null;
  function download() {
    if (!result) return;
    const text = ['JONY — RUS TILI KIRISH TESTI', `Natija: ${result.score}/48`, result.label,
      `Filial: ${result.recommendation.branch_name}`,
      result.allPassed ? 'Yakuniy og‘zaki tekshiruv kerak' : `Tavsiya: ${result.month}-oy, ${result.lesson}-dars`,
      ...result.blocks.map(b => `${b.label}: ${b.correct}/8`),
      'Qaytarish: ' + (result.gaps.join(', ') || 'Asosiy bo‘shliq topilmadi.'),
      oralDirections, ...oralRubric].join('\n');
    const url = URL.createObjectURL(new Blob(['﻿' + text], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'rus-tili-kirish-natijasi.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const lq = legacy[attempt.index];
  const answered = Object.keys(attempt.answers).length;
  const isLast = !!question && !!question.no && question.no >= (question.total ?? TOTAL);
  const stepAlert = stepError && <div role="alert" className="mt-4 rounded-xl bg-amber-50 p-4"><p>{stepError}</p>
    {attempt.started && <button className={`${button} mt-3`} disabled={busy} onClick={t.recover}>{stateBroken ? 'Testni qaytadan boshlash' : 'Qayta urinish'}</button>}</div>;
  return <main lang="uz" className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900"><div className="mx-auto max-w-3xl space-y-6">
    <header className="rounded-3xl bg-slate-950 p-6 text-white md:p-9">
      <img src={brand} alt="Jony" className="h-10 w-10 rounded-xl" />
      <h1 className="mt-5 text-3xl font-bold">Rus tilini qayerdan boshlaymiz?</h1>
      <p className="mt-3 leading-7 text-slate-300">Noldan boshlanadigan bir yillik suhbat kursi · 48 savol · taxminan 25–35 daqiqa</p>
    </header>
    {t.storageError && <p role="status">Brauzer javoblarni saqlay olmadi. Test tugaguncha sahifani yangilamang.</p>}
    {loading && (!attempt.started || (attempt.mode !== 'seq' && !attempt.done && !lq)) && <p role="status">Yuklanmoqda…</p>}
    {loadError && <div role="alert"><p>{loadError}</p><button className={button} onClick={() => setReload(n => n + 1)}>Qayta yuklash</button></div>}
    {!attempt.started && !loading && !loadError && <section className="rounded-2xl bg-white p-6">
      <h2 className="text-xl font-bold">Sizga mos boshlanish nuqtasi</h2>
      <p className="mt-3 leading-7">Har ikki oylik bosqich uchun 8 savol: 4 ta grammatika, 2 ta lug‘at va 2 ta o‘qib tushunish. Har savolni o'qib chiqib javob bering. Javobni bilmasangiz, taxmin qilmang — “Bilmayman”ni tanlang. Orqaga qaytib bo'lmaydi.</p>
      <p lang="ru" className="mt-3">Выберите один ответ. Если не знаете, нажмите «Bilmayman». Не пользуйтесь переводчиком и не просите подсказок.</p>
      <p className="mt-3 text-sm">Testdan so‘ng ustoz bilan og‘zaki tekshiruv shart. Natija til darajasini kafolatlamaydi va sizni avtomatik guruhga biriktirmaydi.</p>
      <form className="mt-5 space-y-3" onSubmit={e => { e.preventDefault(); start(); }}>
        <label className="block">Ism va familiya<input className="mt-1 block w-full rounded-xl border p-3" required minLength={3} maxLength={120} autoComplete="name" value={name} onChange={e => setName(e.target.value)} /></label>
        <label className="block">Telefon<input className="mt-1 block w-full rounded-xl border p-3" required type="tel" maxLength={24} placeholder="+998 90 123 45 67" autoComplete="tel" value={phone} onChange={e => setPhone(e.target.value)} /></label>
        <label className="block">Filial<select className="mt-1 block w-full rounded-xl border p-3" required value={branch || ''} onChange={e => setBranch(Number(e.target.value))}><option value="">Filialni tanlang</option>{branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></label>
        <p className="text-sm text-slate-500">Natijangiz shu ma’lumotlar bilan tanlangan filialning CRM tizimiga saqlanadi. Sahifa yangilansa, test shu savoldan davom etadi.</p>
        <button className={primary} disabled={name.trim().length < 3 || !validPhone(phone) || !branch || busy}>{busy ? 'Yuklanmoqda…' : 'Testni boshlash'}</button>
      </form>
      {stepAlert}
    </section>}
    {attempt.started && !attempt.done && attempt.mode === 'seq' && <section className="rounded-2xl bg-white p-6">
      {question ? <>
        <div className="mb-3 flex justify-between gap-3 text-sm"><span>{placementStages[(question.stage ?? 1) - 1]} · {skills[question.skill]}</span><span>{question.no ?? ''} / {question.total ?? TOTAL}</span></div>
        <progress aria-label="Javob berilgan savollar" value={Math.max(0, (question.no ?? 1) - 1)} max={question.total ?? TOTAL} className="mb-6 h-2 w-full accent-blue-600" />
        {question.text && <p lang="ru" className="mb-6 rounded-xl bg-blue-50 p-5 text-lg leading-8">{question.text}</p>}
        <fieldset disabled={busy}><legend lang="ru" className="mb-5 text-xl font-semibold">{question.prompt}</legend>
          <PlacementChoices name={question.id} options={question.options} value={pick} onChange={setPick} idk={question.idk === true} lang="ru" />
        </fieldset>
        <div className="mt-7 flex justify-end">
          <button className={primary} disabled={pick === undefined || busy} onClick={() => void t.answer()}>{isLast ? 'Natijani ko‘rish' : 'Keyingi'}</button>
        </div><p className="mt-4 text-sm text-slate-500">“Bilmayman” — 0 ball. Bilmagan savolda taxmin qilmang.</p>
      </> : busy ? <p role="status">Savol yuklanmoqda…</p> : null}
      {stepAlert}
    </section>}
    {attempt.started && !attempt.done && attempt.mode !== 'seq' && lq && <section className="rounded-2xl bg-white p-6">
      <div className="mb-3 flex justify-between gap-3 text-sm"><span>{placementStages[lq.stage - 1]} · {skills[lq.skill]}</span><span>{attempt.index + 1} / {TOTAL}</span></div>
      <progress aria-label="Javob berilgan savollar" value={answered} max={TOTAL} className="mb-6 h-2 w-full accent-blue-600" />
      {lq.text && <p lang="ru" className="mb-6 rounded-xl bg-blue-50 p-5 text-lg leading-8">{lq.text}</p>}
      <fieldset><legend lang="ru" className="mb-5 text-xl font-semibold">{lq.prompt}</legend>
        <PlacementChoices name={lq.id} options={lq.options} value={attempt.answers[lq.id]} idk lang="ru"
          onChange={v => setAttempt({ ...attempt, answers: { ...attempt.answers, [lq.id]: v } })} />
      </fieldset>
      <div className="mt-7 flex justify-between gap-3">
        <button className={button} disabled={attempt.index === 0} onClick={() => setAttempt({ ...attempt, index: attempt.index - 1 })}>Oldingi</button>
        <button className={primary} disabled={attempt.answers[lq.id] === undefined || (attempt.index === TOTAL - 1 && answered < TOTAL)}
          onClick={() => setAttempt(attempt.index === TOTAL - 1 ? { ...attempt, done: true } : { ...attempt, index: attempt.index + 1 })}>{attempt.index === TOTAL - 1 ? 'Natijani ko‘rish' : 'Keyingi'}</button>
      </div><p className="mt-4 text-sm text-slate-500">{answered} ta javob berildi. “Bilmayman” — 0 ball. Bilmagan savolda taxmin qilmang.</p>
    </section>}
    {attempt.done && <section className="rounded-2xl bg-white p-6" aria-live="polite">
      {t.saving && <p>Javoblar tekshirilmoqda va CRMga saqlanmoqda…</p>}
      {t.saveError && <div role="alert"><p>{t.saveError}</p><button className={button} onClick={t.retrySave}>Qayta yuborish</button></div>}
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
    {attempt.started && <button className={button} disabled={t.saving} onClick={reset}>Yangi o‘quvchi uchun test</button>}
  </div></main>;
}
