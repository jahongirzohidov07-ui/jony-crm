import { useEffect, useId, useState } from 'react';

const sources = {
  format: 'https://gov.uz/oz/uzbmb/sections/view/49512',
  samples: 'https://gov.uz/oz/uzbmb/sections/view/49518',
  criteria: 'https://gov.uz/oz/uzbmb/sections/view/49531',
  papers: 'https://uzbmb.uz/upload/file/chet_tili/test_namuna/Ingliz_Multi_V1.zip',
  writing: 'https://api-portal.gov.uz/uploads/165/2025/10/13/5a2f6c1e-345c-2d5c-bee2-ad0d7765e2c0_media_.rar',
  writingSpec: 'https://api-portal.gov.uz/uploads/165/2025/10/13/99dfbb36-0f1d-2c70-8a4e-e1382a5f255b_media_.pdf',
  writingRubric: 'https://api-portal.gov.uz/uploads/165/2025/10/13/b260e792-2fc6-630d-5bfe-399a2a0e55b6_media_.pdf',
  speaking: 'https://uzbmb.uz/upload/file/pdf/phone/Speaking_yangi_format.pdf',
  listeningPractice: 'https://learnenglish.britishcouncil.org/free-resources/listening/b2/business-interview',
};
const skills = ['listening', 'reading', 'writing', 'speaking'] as const;
type Skill = typeof skills[number];
type Session = { startedAt: number; deadline: number; finishedAt?: number };
const durations: Record<Skill, number> = { listening: 2700, reading: 3600, writing: 3600, speaking: 555 };
const labels: Record<Skill, string> = { listening: 'Listening', reading: 'Reading', writing: 'Writing', speaking: 'Speaking' };
const speakingSteps = [
  ['1.1 · 1-savol', 30], ['1.1 · 2-savol', 30], ['1.1 · 3-savol', 30],
  ['1.2 · rasmlarni solishtirish', 45], ['1.2 · 5-savol', 30], ['1.2 · 6-savol', 30],
  ['2-qism · tayyorgarlik', 60], ['2-qism · uch savolga javob', 120],
  ['3-qism · tayyorgarlik', 60], ['3-qism · ikki tomonlama dalil', 120],
] as const;
const scoreFields = [
  ['listening', 'Listening · to‘g‘ri javob', 35], ['reading', 'Reading · to‘g‘ri javob', 35],
  ['email1', 'Writing · norasmiy xat', 5], ['email2', 'Writing · rasmiy xat', 5],
  ['post', 'Writing · onlayn matn', 6],
] as const;
type ScoreKey = typeof scoreFields[number][0];
type Review = { teacher: string; notes: Record<Skill, string>; scores: Record<ScoreKey, string>; reviewedAt?: number };
type Attempt = {
  version: 1; resourceReady: boolean; paper: string;
  sessions: Partial<Record<Skill, Session>>;
  answers: Record<'listening' | 'reading', string[]>;
  writing: [string, string, string]; speakingEvidence: string; review: Review;
};
const panel = 'rounded-2xl border border-slate-200 bg-white p-4 md:p-6';
const button = 'rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:border-blue-500 focus-visible:outline-2 focus-visible:outline-blue-600 disabled:opacity-40';
const input = 'mt-1 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm text-slate-900 disabled:bg-slate-100';

function emptyAttempt(): Attempt {
  return { version: 1, resourceReady: false, paper: '', sessions: {},
    answers: { listening: Array<string>(35).fill(''), reading: Array<string>(35).fill('') },
    writing: ['', '', ''], speakingEvidence: '',
    review: { teacher: '', scores: { listening: '', reading: '', email1: '', email2: '', post: '' },
      notes: { listening: '', reading: '', writing: '', speaking: '' } },
  };
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isTimestamp(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > 0;
}
function validScore(value: string, max: number) {
  return /^\d+$/.test(value) && Number(value) >= 0 && Number(value) <= max;
}
function parseAttempt(raw: string): Attempt {
  const v: unknown = JSON.parse(raw);
  if (!isRecord(v) || v.version !== 1 || typeof v.resourceReady !== 'boolean' || typeof v.paper !== 'string'
    || !isRecord(v.sessions) || !isRecord(v.answers) || !Array.isArray(v.writing) || v.writing.length !== 3
    || !v.writing.every(x => typeof x === 'string') || typeof v.speakingEvidence !== 'string'
    || !isRecord(v.review)) throw new Error('Invalid attempt');
  for (const skill of skills) {
    const s = v.sessions[skill];
    if (s !== undefined && (!isRecord(s) || !isTimestamp(s.startedAt) || !isTimestamp(s.deadline)
      || s.deadline - s.startedAt !== durations[skill] * 1000
      || (s.finishedAt !== undefined && (!isTimestamp(s.finishedAt) || s.finishedAt < s.startedAt || s.finishedAt > s.deadline)))) {
      throw new Error('Invalid session');
    }
  }
  for (const skill of ['listening', 'reading'] as const) {
    const a = v.answers[skill];
    if (!Array.isArray(a) || a.length !== 35 || !a.every(x => typeof x === 'string')) throw new Error('Invalid answers');
  }
  const review = v.review;
  if (typeof review.teacher !== 'string' || !isRecord(review.notes) || !isRecord(review.scores)
    || skills.some(s => typeof (review.notes as Record<string, unknown>)[s] !== 'string')
    || scoreFields.some(([key, , max]) => {
      const value = (review.scores as Record<string, unknown>)[key];
      return typeof value !== 'string' || (value !== '' && !validScore(value, max));
    }) || (review.reviewedAt !== undefined && !isTimestamp(review.reviewedAt))) throw new Error('Invalid review');
  return v as unknown as Attempt;
}
function loadAttempt(key: string): { attempt: Attempt; error: string } {
  try {
    const raw = window.localStorage.getItem(key);
    return { attempt: raw ? parseAttempt(raw) : emptyAttempt(), error: '' };
  } catch {
    return { attempt: emptyAttempt(), error: 'Saqlangan sessiya o‘qilmadi. Eski ma’lumot avtomatik almashtirilmaydi. Davom etishdan oldin yangi urinish yarating.' };
  }
}
function completed(session: Session | undefined, now: number) {
  return !!session && (session.finishedAt !== undefined || now >= session.deadline);
}
function remaining(session: Session | undefined, now: number) {
  return session && !completed(session, now) ? Math.max(0, Math.ceil((session.deadline - now) / 1000)) : 0;
}
function clock(seconds: number) { return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`; }
function speakingPhase(start: number, now: number) {
  let end = start;
  for (const [label, seconds] of speakingSteps) {
    end += seconds * 1000;
    if (now < end) return `${label} · ${clock(Math.ceil((end - now) / 1000))}`;
  }
  return 'Speaking vaqti tugadi';
}
function Link({ href, children }: { href: string; children: React.ReactNode }) {
  return <a href={href} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-700 underline underline-offset-2">{children} ↗</a>;
}

export type IntensiveExamPreparationProps = {
  /** Parent supplies a stable learner/group-specific key and existing role permission. */
  storageKey?: string;
  canReview?: boolean;
};
export default function IntensiveExamPreparation({ storageKey = 'jony:intensive:exam:v1:local', canReview = false }: IntensiveExamPreparationProps) {
  // Remount on identity change so one learner's answers cannot be saved under another key.
  return <ExamPreparation key={storageKey} storageKey={storageKey} canReview={canReview} />;
}
function ExamPreparation({ storageKey, canReview }: Required<IntensiveExamPreparationProps>) {
  const id = useId();
  const [loaded] = useState(() => loadAttempt(storageKey));
  const [attempt, setAttempt] = useState(loaded.attempt);
  const [storageError, setStorageError] = useState(loaded.error);
  const [blocked, setBlocked] = useState(!!loaded.error);
  const [now, setNow] = useState(() => Date.now());
  const [selected, setSelected] = useState<Skill>('listening');
  const [resetRequested, setResetRequested] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => {
    const tick = () => setNow(Date.now());
    const timer = window.setInterval(tick, 1000);
    window.addEventListener('focus', tick);
    return () => { window.clearInterval(timer); window.removeEventListener('focus', tick); };
  }, []);
  function save(next: Attempt) {
    if (blocked) return;
    setAttempt(next);
    try { window.localStorage.setItem(storageKey, JSON.stringify(next)); setStorageError(''); }
    catch { setStorageError('Brauzerga saqlanmadi. Sahifani yopmang; natijani yuklab oling. Taymer qayta ochilganda tiklanmasligi mumkin.'); }
  }
  function reset() {
    const next = emptyAttempt();
    setBlocked(false); setAttempt(next); setResetRequested(false); setMessage('Yangi urinish tayyor.');
    try { window.localStorage.setItem(storageKey, JSON.stringify(next)); setStorageError(''); }
    catch { setStorageError('Brauzerga saqlash ishlamayapti. Natijani yuklab oling.'); }
  }
  const session = attempt.sessions[selected];
  const activeSkill = skills.find(s => attempt.sessions[s] && !completed(attempt.sessions[s], now));
  const done = skills.every(s => completed(attempt.sessions[s], now));
  const editable = !!session && !completed(session, now) && !blocked;
  function start(skill: Skill) {
    const time = Date.now();
    const index = skills.indexOf(skill);
    if (blocked || !attempt.resourceReady || !attempt.paper.trim() || attempt.sessions[skill]
      || skills.some(s => attempt.sessions[s] && !completed(attempt.sessions[s], time))
      || skills.slice(0, index).some(s => !completed(attempt.sessions[s], time))) return;
    save({ ...attempt, sessions: { ...attempt.sessions, [skill]: { startedAt: time, deadline: time + durations[skill] * 1000 } } });
    setNow(time); setMessage(`${labels[skill]} boshlandi.`);
  }
  function editWork(change: Partial<Attempt>) {
    if (!session || completed(session, Date.now())) return;
    save({ ...attempt, ...change });
  }
  function editReview(review: Review) {
    if (!canReview || !done) return;
    save({ ...attempt, review: { ...review, reviewedAt: undefined } });
  }
  function exportAttempt() {
    const blob = new Blob([JSON.stringify({ ...attempt, notOfficialScore: true, exportedAt: new Date().toISOString(), sources }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'intensive-exam-practice.json'; a.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="space-y-4 text-slate-900" aria-label="8-oy imtihonga tayyorgarlik">
    <header className={`${panel} !border-blue-200 !bg-blue-50`}>
      <p className="text-xs font-bold uppercase tracking-wide text-blue-700">8-oy · yakuniy tayyorgarlik · B1–C1 Multilevel</p>
      <h3 className="mt-2 text-xl font-bold">To‘rt ko‘nikma: rasmiy namuna bilan mashq</h3>
      <p className="mt-2 text-sm leading-6">Listening → Reading → Writing → Speaking. Rasmiy materiallarni oldindan oching; javoblar va ustoz fikri shu brauzerda saqlanadi. Serverga yuborilmaydi.</p>
      <p className="mt-2 text-sm font-semibold">Mashq natijasi — rasmiy ball yoki CEFR sertifikati emas. Avtomatik daraja chiqarilmaydi.</p>
      <p className="mt-2 text-xs text-slate-600">Manbalar tekshirildi: 07.10.2026. <Link href={sources.format}>Amaldagi format</Link> · <Link href={sources.criteria}>Baholash mezonlari</Link></p>
    </header>
    <details className={panel}>
      <summary className="cursor-pointer font-semibold">Yakuniy oy rejasi va rasmiy format</summary>
      <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-6">
        <li>1-hafta: rasmiy namuna bilan diagnostika; har xato uchun sabab va tuzatish yozing.</li>
        <li>2-hafta: zaif ko‘nikmalar; kuniga bitta tinglash/reading qismi, ikki uslubdagi xatlar va speaking javoblari.</li>
        <li>3-hafta: to‘rt ko‘nikmali sinov; ustoz bilan yozma ish va og‘zaki javoblarni tahlil qiling.</li>
        <li>4-hafta: xatolarni qayta ishlash, boshqa ustoz tanlagan variant bilan takrorlash, imtihon tartibini mashq qilish.</li>
      </ol>
      <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6">
        <li>Listening: 45 daqiqa, 6 qism, 35 savol. Matnlar ikki marta; taxminan 35 daqiqa audio va 10 daqiqa javob ko‘chirish. Yozuvdagi takrorlarni yana ikki marta qo‘ymang.</li>
        <li>Reading: 60 daqiqa, 5 qism, 35 savol. Javob ko‘chirish shu vaqt ichida.</li>
        <li>Writing: 60 daqiqa, 2 qism / 3 matn: norasmiy xat ≈50, rasmiy xat 120–150, onlayn nashr uchun matn 180–200 so‘z. <Link href={sources.writingSpec}>Yangi tafsilotlar</Link></li>
        <li>Speaking: 1.1 — 3 × 30 soniya; 1.2 — 45 + 30 + 30 soniya; 2 va 3-qismlarda 1 daqiqa tayyorgarlik + 2 daqiqa nutq. Taymerdagi 9:15 faqat shu bosqichlar yig‘indisi; yo‘riqnoma va texnik vaqt kiritilmagan.</li>
      </ul>
      <p className="mt-3 text-sm leading-6">Bu sahifa tashqi rasmiy namuna bilan ishlash daftaridir. Qisqa mualliflik matni yoki British Council mashqi to‘liq Multilevel mock deb hisoblanmaydi.</p>
    </details>
    <div className={panel}>
      <h4 className="font-bold">1. Materiallarni tayyorlang</h4>
      <ul className="mt-3 list-disc space-y-3 pl-5 text-sm leading-6">
        <li><Link href={sources.papers}>Rasmiy English Multilevel ZIP</Link>: LISTENING PAPER.pdf, listening.mp3 (haqiqiy audioyozuv), READING PAPER.pdf va Answer key.pdf. Kalitni sinovdan keyin ustoz ochadi.</li>
        <li><Link href={sources.writing}>Yangi writing namunasi · RAR</Link>: arxivdan INGLIZ TILI.pdf ni oching. Eski ZIP ichidagi WRITING PAPER.pdf o‘rniga shu namunani ishlating.</li>
        <li><Link href={sources.speaking}>Speaking formati, savollar va rasmlar · PDF</Link>. Ustoz savollarni navbat bilan ko‘rsatsin. 2-qismda rasmni tasvirlash talab qilinmaydi.</li>
      </ul>
      <p className="mt-3 text-sm leading-6">Yuklama ochilmasa, <Link href={sources.samples}>gov.uz namunalar sahifasidan</Link> foydalaning. Telefoningizda ZIP/RAR ochish ilovasi kerak bo‘lishi mumkin. Audio va rasmlar tayyor bo‘lmaguncha taymerni boshlamang.</p>
      <label className="mt-4 block text-sm font-medium">Variant nomi / mashq sanasi<input className={input} value={attempt.paper} maxLength={160} disabled={!!Object.keys(attempt.sessions).length || blocked} onChange={e => save({ ...attempt, paper: e.target.value })} placeholder="Official V1 + yangi writing · 7-oktabr" /></label>
      <label className="mt-3 flex items-start gap-2 text-sm leading-6"><input type="checkbox" className="mt-1" checked={attempt.resourceReady} disabled={!!Object.keys(attempt.sessions).length || blocked} onChange={e => save({ ...attempt, resourceReady: e.target.checked })} />Savol varaqlari, yangi writing, speaking rasmlari va listening audiosi ochildi; ovozni tekshirdim.</label>
      <details className="mt-4 rounded-xl bg-slate-50 p-3 text-sm leading-6"><summary className="cursor-pointer font-semibold">Qo‘shimcha B2 tinglash — British Council</summary><p className="mt-2"><Link href={sources.listeningPractice}>A business interview: audio, topshiriqlar, transkript</Link>. Avval tinglang, keyin topshiriqlarni bajaring; oxirida transkript bilan tekshiring. Bu alohida mashq, rasmiy Multilevel varianti o‘rnini bosmaydi.</p></details>
    </div>
    {storageError && <p role="alert" className="rounded-xl bg-amber-50 p-4 text-sm text-amber-950">{storageError}</p>}
    <div className={panel}>
      <h4 className="font-bold">2. Vaqt bilan ishlang</h4>
      <p className="mt-2 text-sm leading-6 text-slate-600">Har bo‘lim alohida boshlanadi. Sahifa yopilsa ham vaqt o‘tadi; pauza yo‘q. Yozma imtihonning 165 daqiqasini mashq qilish uchun dastlabki uch bo‘limni tanaffussiz ketma-ket boshlang. Speakingni alohida o‘tkazish mumkin.</p>
      <nav className="mt-4 flex flex-wrap gap-2" aria-label="Imtihon bo‘limi">{skills.map(s => <button type="button" key={s} className={`${button} ${selected === s ? '!border-blue-600 !bg-blue-50' : ''}`} aria-pressed={selected === s} onClick={() => setSelected(s)}>{labels[s]} {completed(attempt.sessions[s], now) ? '✓' : activeSkill === s ? '· davom etmoqda' : ''}</button>)}</nav>
      {activeSkill && activeSkill !== selected && <p role="status" className="mt-3 text-sm font-semibold text-blue-800">{labels[activeSkill]} davom etmoqda · {clock(remaining(attempt.sessions[activeSkill], now))}</p>}
      <div className="mt-4 rounded-xl bg-slate-50 p-4">
        <h5 className="font-semibold">{labels[selected]} · {clock(durations[selected])}</h5>
        <p role="timer" aria-label={`${labels[selected]} qolgan vaqt`} className="my-2 font-mono text-3xl tabular-nums">{session ? clock(remaining(session, now)) : clock(durations[selected])}</p>
        {selected === 'speaking' && session && !completed(session, now) && <p className="mb-3 font-semibold text-blue-800">{speakingPhase(session.startedAt, now)}</p>}
        {session && <p className="mb-3 text-xs leading-5 text-slate-600">Boshlanish: {new Date(session.startedAt).toLocaleString()} · Muddat: {new Date(session.deadline).toLocaleString()}</p>}
        {!session ? <button type="button" className={button} disabled={blocked || !attempt.resourceReady || !attempt.paper.trim() || !!activeSkill || skills.slice(0, skills.indexOf(selected)).some(s => !completed(attempt.sessions[s], now))} onClick={() => start(selected)}>{labels[selected]} boshlash</button>
          : completed(session, now) ? <p role="status" className="text-sm font-semibold">{session.finishedAt ? 'Topshirildi.' : 'Vaqt tugadi.'} Javoblar yopildi; keyingi bo‘limni tanlang.</p>
            : <button type="button" className={button} disabled={blocked} onClick={() => { const time = Date.now(); save({ ...attempt, sessions: { ...attempt.sessions, [selected]: { ...session, finishedAt: Math.min(time, session.deadline) } } }); setNow(time); setMessage(`${labels[selected]} topshirildi; javoblar endi o‘zgarmaydi.`); }}>Bo‘limni topshirish va javoblarni yopish</button>}
      </div>
      {(selected === 'listening' || selected === 'reading') && <fieldset disabled={!editable} className="mt-4"><legend className="text-sm leading-6">Rasmiy varaqdagi 1–35 javobni kiriting. Savol va matnlar tashqi PDFda. Tekshiruvni ustoz kalit bilan bajaradi.</legend><div className="mt-3 grid grid-cols-3 gap-3 sm:grid-cols-5">{attempt.answers[selected].map((answer, index) => <label key={index} className="text-xs font-semibold" htmlFor={`${id}-${selected}-${index}`}>{index + 1}<input id={`${id}-${selected}-${index}`} autoComplete="off" spellCheck={false} className={input} value={answer} maxLength={100} onChange={e => editWork({ answers: { ...attempt.answers, [selected]: attempt.answers[selected].map((a, i) => i === index ? e.target.value : a) } })} /></label>)}</div></fieldset>}
      {selected === 'writing' && <div className="mt-4 space-y-4"><p className="text-sm leading-6">Yangi rasmiy namunadagi topshiriqlarni bajaring. Tavsiya: 1-qismga 25, 2-qismga 35 daqiqa; umumiy chegara 60 daqiqa.</p>{['1.1 · norasmiy xat · ≈50 so‘z', '1.2 · rasmiy xat · 120–150 so‘z', '2 · onlayn matn · 180–200 so‘z'].map((label, index) => <label key={label} className="block text-sm font-medium">{label}<textarea disabled={!editable} className={input} rows={index === 2 ? 9 : 5} value={attempt.writing[index]} maxLength={15000} spellCheck={false} onChange={e => { const writing: Attempt['writing'] = [...attempt.writing]; writing[index] = e.target.value; editWork({ writing }); }} /><span className="text-xs text-slate-500">{attempt.writing[index].trim().split(/\s+/).filter(Boolean).length} so‘z · taxminiy sanash</span></label>)}</div>}
      {selected === 'speaking' && <div className="mt-4 space-y-3 text-sm leading-6"><p>PDFdagi rasmlar va savollarni ustoz navbat bilan ochadi. Taymer bosqichlarni o‘zi almashtiradi. Telefon diktofonini oldindan yoqing yoki ustozga jonli javob bering; bu modul mikrofon yozmaydi va audio yuklamaydi.</p><ol className="list-decimal space-y-1 pl-5">{speakingSteps.map(([label, seconds]) => <li key={label}>{label} — {seconds} soniya</li>)}</ol><label className="block font-medium">Yozuv nomi yoki jonli tinglash qaydi<textarea disabled={!editable} className={input} rows={2} maxLength={2000} value={attempt.speakingEvidence} onChange={e => editWork({ speakingEvidence: e.target.value })} placeholder="Masalan: telefon diktofoni, 7-oktabr; ustoz jonli tingladi" /></label></div>}
    </div>
    <div className={panel}>
      <h4 className="font-bold">3. Ustoz tekshiruvi</h4>
      <p className="mt-2 text-sm leading-6">{attempt.review.reviewedAt ? 'Ustoz tekshiruvi qayd etilgan.' : done ? 'To‘rt bo‘lim yakunlandi — ustoz tekshiruvi kutilmoqda.' : 'Tekshiruv barcha bo‘limlar yakunlangach ochiladi.'} Bu yerda kiritilgan ballar mashq uchun; rasmiy standart ballga aylantirilmaydi.</p>
      <p className="mt-2 text-sm"><Link href={sources.writingRubric}>Writing mezonlari</Link> · <Link href={sources.criteria}>Speaking mezonlari</Link></p>
      {canReview ? <fieldset disabled={!done || blocked} className="mt-4 space-y-4"><legend className="text-sm text-slate-600">Ustoz: kalit, yozma ish va og‘zaki javobni tekshirib kiriting.</legend><label className="block text-sm font-medium">Tekshirgan ustoz<input className={input} maxLength={100} value={attempt.review.teacher} onChange={e => editReview({ ...attempt.review, teacher: e.target.value })} /></label><div className="grid gap-3 sm:grid-cols-2">{scoreFields.map(([key, label, max]) => <label key={key} className="text-sm">{label} / {max}<input type="number" min={0} max={max} step={1} className={input} value={attempt.review.scores[key]} onChange={e => { const value = e.target.value; if (value === '' || validScore(value, max)) editReview({ ...attempt.review, scores: { ...attempt.review.scores, [key]: value } }); }} /></label>)}</div>{skills.map(skill => <label key={skill} className="block text-sm font-medium">{labels[skill]} · dalil, xato va keyingi qadam<textarea className={input} rows={2} maxLength={4000} value={attempt.review.notes[skill]} onChange={e => editReview({ ...attempt.review, notes: { ...attempt.review.notes, [skill]: e.target.value } })} placeholder={skill === 'speaking' ? 'Ravonlik, talaffuz, grammatika, lug‘at va vazifaga javob: misollar bilan fikr bering.' : 'Aniq xato va uni tuzatish mashqini yozing.'} /></label>)}<button type="button" className={button} disabled={!attempt.review.teacher.trim() || skills.some(s => !attempt.review.notes[s].trim()) || scoreFields.some(([key, , max]) => !validScore(attempt.review.scores[key], max))} onClick={() => { if (!canReview || !done) return; save({ ...attempt, review: { ...attempt.review, reviewedAt: Date.now() } }); setMessage('Ustoz tekshiruvi saqlandi. Rasmiy ball emas.'); }}>Tekshiruvni tasdiqlash</button></fieldset>
        : <p className="mt-3 text-sm text-slate-600">Natijani yuklab, ustozga ko‘rsating. Baholashni ilovaning ustoz huquqiga ega foydalanuvchisi qayd etadi.</p>}
      {attempt.review.reviewedAt && <div className="mt-4 rounded-xl bg-emerald-50 p-4 text-sm leading-6"><p className="font-bold">Mashq hisoboti — rasmiy ball emas</p><p>{attempt.review.teacher} · {new Date(attempt.review.reviewedAt).toLocaleString()}</p><ul className="mt-2 list-disc pl-5">{scoreFields.map(([key, label, max]) => <li key={key}>{label}: {attempt.review.scores[key]} / {max}</li>)}</ul>{skills.map(s => <p key={s} className="mt-2 whitespace-pre-wrap"><strong>{labels[s]}:</strong> {attempt.review.notes[s]}</p>)}</div>}
    </div>
    <div className="flex flex-wrap gap-2"><button type="button" className={button} onClick={exportAttempt}>Javoblar va hisobotni yuklab olish</button><button type="button" className={button} onClick={() => setResetRequested(true)}>Yangi urinish</button></div>
    {resetRequested && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm"><p>Joriy javoblar, taymer va ustoz fikri almashtiriladi. Kerak bo‘lsa avval hisobotni yuklab oling.</p><div className="mt-3 flex gap-2"><button type="button" className={button} onClick={reset}>Almashtirish va boshlash</button><button type="button" className={button} onClick={() => setResetRequested(false)}>Bekor qilish</button></div></div>}
    <p role="status" className="text-sm text-slate-600">{message}</p>
    <p className="text-xs leading-5 text-slate-500">Shu brauzerdagi mahalliy mashq daftari. Boshqa qurilmaga avtomatik o‘tmaydi. Umumiy qurilmada ishlashdan keyin hisobotni yuklab, yangi urinish bilan ma’lumotlarni tozalang.</p>
  </section>;
}
