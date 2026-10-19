import { useEffect, useRef, useState } from 'react';
import { getToken } from '../lib/api';

type Review = { decision: 'approved' | 'changes_requested'; task: number; language: number; collaboration: number; strength: string; next_step: string; version: number; created_at: string; speaking_observed?: boolean; fluency?: number | null; pronunciation?: number | null; observed_at?: string | null; observed_by?: number | null };
type Version = { number: number; title: string; text: string; contributions: Record<string, string>; consents: Record<string, string>; submitted_at: string | null; review: Review | null; created_at: string };
type Entry = { id: string; members: number[]; names: Record<string, string>; status: string; versions: Version[]; task?: { prompt: string } };
type Listing = { entries: Entry[]; peers: { id: number; name: string }[]; me: number; role: string; lesson_title: string; prompt: string; rubric: Record<string, string>; scale: Record<string, string> };
type Props = { language: string; lesson: number; demo?: boolean; mode?: 'student' | 'teacher'; groupId?: number };
type Requester = <T>(path: string, body?: unknown) => Promise<T>;
const base = '/api/course-collaboration';
const button = 'rounded-lg border px-3 py-2 disabled:opacity-50';
const input = 'w-full rounded-lg border p-2 bg-white text-gray-900';
const oralRubric = {
  fluency: ['Darajaga mos so‘z yoki iborani mustaqil ayta olmadi', 'Ko‘p yordam va uzun to‘xtalishlar bilan aytdi', 'Tez-tez to‘xtaldi, lekin fikrini yetkazdi', 'Darajaga mos so‘z/iboralarni odatiy pauzalar bilan aytdi', 'Darajaga mos nutqni ravon olib bordi, navbat almashdi'],
  pronunciation: ['Aytilgan so‘zlarni tushunib bo‘lmadi', 'Ko‘p takrorlashdan keyin ayrim so‘zlar tushunildi', 'Ba’zi so‘zlarni takrorlash kerak bo‘ldi', 'Darajaga mos so‘zlar asosan tushunarli aytildi', 'So‘zlar aniq, oson tushunarli aytildi; ona tili aksenti talab qilinmaydi'],
};

function SpeakingEvidence({ review }: { review: Review }) {
  if (!review.speaking_observed) return <p>Og‘zaki ijro jonli kuzatilmagan — ravonlik va talaffuz baholanmagan.</p>;
  return <div className="rounded-lg border p-3 space-y-1">
    <h6 className="font-semibold">O‘qituvchining jonli kuzatuvi — v{review.version}</h6>
    <p>Juftlikning shu dialogdagi ijrosi, joriy dars darajasiga nisbatan. Bu AI bahosi yoki individual CEFR darajasi emas.</p>
    <p>Ravonlik: {review.fluency}/4 — {oralRubric.fluency[review.fluency ?? 0]}</p>
    <p>Talaffuz / tushunarlilik: {review.pronunciation}/4 — {oralRubric.pronunciation[review.pronunciation ?? 0]}</p>
    <p>O‘qituvchi #{review.observed_by}. Kuzatuv qayd etilgan vaqt: {review.observed_at ? new Date(review.observed_at).toLocaleString() : '—'}.</p>
  </div>;
}

/** Demo is deliberately read-only and makes no authenticated network requests. */
export default function CourseCollaboration({ demo = false, mode = 'student', ...props }: Props) {
  const [token, setToken] = useState(getToken);
  useEffect(() => {
    const sync = () => setToken(getToken());
    const timer = window.setInterval(sync, 500);
    window.addEventListener('storage', sync);
    window.addEventListener('focus', sync);
    return () => { clearInterval(timer); window.removeEventListener('storage', sync); window.removeEventListener('focus', sync); };
  }, []);
  if (demo) return <section className="rounded-xl border p-4"><h2>Juftlik ishi — namuna</h2><p>Haqiqiy hisobda: guruhdoshga taklif → sherik roziligi → umumiy ish → ikkala tasdiq → o‘qituvchi bahosi. Namuna hech kimga yuborilmaydi va XP bermaydi.</p></section>;
  if (!token) return <p>Juftlik ishini ochish uchun hisobingizga kiring.</p>;
  return <Workspace key={`${token}:${mode}:${props.language}:${props.lesson}:${props.groupId}`} {...props} mode={mode} token={token} />;
}

function Workspace({ language, lesson, mode, token, groupId }: Props & { token: string }) {
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([]);
  const [group, setGroup] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const alive = useRef(true);
  const controllers = useRef(new Set<AbortController>());
  const request: Requester = async <T,>(path: string, body?: unknown): Promise<T> => {
    if (!alive.current || getToken() !== token) throw new Error('Hisob o‘zgardi. Sahifani qayta oching.');
    const controller = new AbortController(); controllers.current.add(controller);
    try {
      const response = await fetch(base + path, { method: body === undefined ? 'GET' : 'POST', cache: 'no-store', signal: controller.signal,
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', 'X-Active-Role': mode || 'student' },
        body: body === undefined ? undefined : JSON.stringify(body) });
      const data = await response.json();
      if (!alive.current || getToken() !== token) throw new Error('Hisob o‘zgardi.');
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Ma’lumotlarni tekshiring.');
      return data as T;
    } finally { controllers.current.delete(controller); }
  };
  useEffect(() => {
    alive.current = true;
    void request<{ groups: { id: number; name: string }[] }>('/groups').then(data => {
      setGroups(data.groups); setGroup(String(data.groups.find(g => g.id === groupId)?.id || data.groups[0]?.id || ''));
    }).catch(e => { if (alive.current) setError(String(e.message)); }).finally(() => { if (alive.current) setLoading(false); });
    return () => { alive.current = false; controllers.current.forEach(c => c.abort()); };
    // The enclosing keyed boundary resets the request context when the account changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <section className="space-y-4 rounded-xl border p-4">
    <h2 className="text-xl font-bold">{mode === 'teacher' ? 'Juftlik ishlarini tekshirish' : 'Guruhdosh bilan ijodiy ish'}</h2>
    <p>Faqat ikki sherik va guruh o‘qituvchisi ko‘radi. Ommaviy chat yo‘q. Bu ish XP yoki avtomatik o‘zlashtirish ballini bermaydi.</p>
    {error && <p role="alert">{error} <button className={button} onClick={() => window.location.reload()}>Qayta ochish</button></p>}
    {loading ? <p role="status">Guruhlar yuklanmoqda…</p> : !groups.length && !error ? <p>Faol, ruxsat berilgan guruh topilmadi.</p> : null}
    {!!groups.length && <label className="block">Guruh<select className={input} value={group} onChange={e => setGroup(e.target.value)}>{groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select></label>}
    {group && <GroupWork key={group} path={`/groups/${group}`} query={`language=${encodeURIComponent(language)}&lesson=${lesson}`} request={request} mode={mode || 'student'} />}
  </section>;
}

function GroupWork({ path, query, request, mode }: { path: string; query: string; request: Requester; mode: string }) {
  const [data, setData] = useState<Listing | null>(null);
  const [peer, setPeer] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const alive = useRef(true);
  async function reload() {
    const next = await request<Listing>(`${path}?${query}`);
    if (alive.current) setData(next);
  }
  useEffect(() => {
    alive.current = true;
    void reload().catch(e => { if (alive.current) setError(e.message); });
    return () => { alive.current = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  async function act(suffix: string, body: unknown) {
    if (busy) return;
    setBusy(true); setError('');
    try { await request(`${path}${suffix}${suffix.includes('?') ? '&' : '?'}${query}`, body); await reload(); }
    catch (e) { if (alive.current) setError(e instanceof Error ? e.message : 'So‘rov bajarilmadi.'); }
    finally { if (alive.current) setBusy(false); }
  }
  return <div className="space-y-4" aria-busy={busy}>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <button className={button} disabled={busy} onClick={() => { setError(''); void reload().catch(e => setError(e.message)); }}>Yangilash</button>
    {!data ? <p role="status">{error ? 'Ma’lumot yuklanmadi.' : 'Yuklanmoqda…'}</p> : <>
      <h3 className="font-semibold">{data.lesson_title}</h3><p className="whitespace-pre-wrap">{data.prompt}</p>
      {mode === 'student' && <div className="flex flex-wrap gap-2 items-end"><label>Faol guruhdosh<select className={input} value={peer} onChange={e => setPeer(e.target.value)}><option value="">Sherikni tanlang</option>{data.peers.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><button className={button} disabled={busy || !peer} onClick={() => void act('/invites', { peer_id: Number(peer) })}>Taklif yuborish</button>{!data.peers.length && <p>Taklif qilish mumkin bo‘lgan faol guruhdosh yo‘q.</p>}</div>}
      {!data.entries.length && <p>{mode === 'teacher' ? 'Ikkala sherik tasdiqlagan ishlar shu yerda ko‘rinadi.' : 'Hozircha taklif yoki juftlik ishi yo‘q.'}</p>}
      {data.entries.map(entry => <EntryCard key={entry.id} entry={entry} data={data} busy={busy} act={act} mode={mode} />)}
    </>}
  </div>;
}

function EntryCard({ entry, data, busy, act, mode }: { entry: Entry; data: Listing; busy: boolean; act: (suffix: string, body: unknown) => Promise<void>; mode: string }) {
  const latest = entry.versions.at(-1);
  const [selected, setSelected] = useState(0);
  const version = entry.versions.find(v => v.number === selected) || latest;
  const [editing, setEditing] = useState(false);
  const isLatest = version?.number === latest?.number;
  const action = (name: string, body: unknown) => act(`/${entry.id}/${name}`, body);
  return <article className="space-y-3 rounded-xl border p-4">
    <h4 className="font-bold">{entry.members.map(id => entry.names[id]).join(' + ')}</h4>
    {entry.task && <details><summary>Bu ishning vazifasi</summary><p className="whitespace-pre-wrap">{entry.task.prompt}</p></details>}
    {entry.status === 'invited' && <><p>Taklif javobini kutmoqda.</p>{mode === 'student' && data.me === entry.members[1] && <div className="flex gap-2"><button className={button} disabled={busy} onClick={() => void action('respond?accept=true', {})}>Juftlikka qo‘shilish</button><button className={button} disabled={busy} onClick={() => void action('respond?accept=false', {})}>Rad etish</button></div>}</>}
    {entry.status === 'declined' && <p>Taklif rad etilgan.</p>}
    {entry.versions.length > 0 && <label className="block">O‘zgarmas versiyalar tarixi<select className={input} value={version?.number} onChange={e => setSelected(Number(e.target.value))}>{entry.versions.map(v => <option key={v.number} value={v.number}>v{v.number} — {new Date(v.created_at).toLocaleString()}</option>)}</select></label>}
    {version && <><h5 className="font-semibold">{version.title}</h5><p className="whitespace-pre-wrap break-words">{version.text}</p>
      {entry.members.map(id => <p key={id} className="break-words"><strong>{entry.names[id]} hissasi:</strong> {version.contributions[id]}</p>)}
      <p>{version.submitted_at ? 'Ikkala sherik tasdiqlagan — o‘qituvchiga topshirilgan.' : `Tasdiqlar: ${Object.keys(version.consents).length}/2. Hali o‘qituvchiga yuborilmagan.`}</p>
      {version.review ? <div className="rounded-lg bg-slate-100 p-3 text-gray-900"><strong>v{version.review.version}: {version.review.decision === 'approved' ? 'O‘qituvchi tasdiqladi' : 'Qayta ishlash kerak'}</strong><p>{Object.entries(data.rubric).map(([k, label]) => `${label}: ${version.review![k as 'task' | 'language' | 'collaboration']}/4`).join(' · ')}</p><p><strong>Yaxshi bajarilgan:</strong> {version.review.strength}</p><p><strong>Keyingi aniq qadam:</strong> {version.review.next_step}</p></div> : version.submitted_at && <p>O‘qituvchi tekshiruvini kutmoqda.</p>}
      {version.review && <SpeakingEvidence review={version.review} />}
      {mode === 'student' && isLatest && !version.submitted_at && !version.consents[data.me] && !editing && <button className={button} disabled={busy} onClick={() => void action('consent', { expected_version: version.number })}>v{version.number} ni o‘qidim, hissam to‘g‘ri — topshirishga roziman</button>}
      {mode === 'teacher' && isLatest && version.submitted_at && !version.review && <ReviewForm key={version.number} version={version.number} rubric={data.rubric} scale={data.scale} busy={busy} submit={body => action('review', body)} />}
    </>}
    {mode === 'student' && entry.status === 'accepted' && (!latest?.submitted_at || latest.review) && entry.versions.length < 10 && <>
      <button className={button} disabled={busy} onClick={() => setEditing(!editing)}>{editing ? 'Tahrirni yopish' : latest ? 'Yangi versiya yaratish' : 'Umumiy ish yozish'}</button>
      {editing && <ArtifactForm key={latest?.number || 0} entry={entry} busy={busy} submit={body => action('versions', body)} />}
    </>}
    {entry.versions.length >= 10 && <p>10 versiya chegarasi. Saqlangan tarix o‘zgarmaydi.</p>}
  </article>;
}

function ArtifactForm({ entry, busy, submit }: { entry: Entry; busy: boolean; submit: (body: unknown) => Promise<void> }) {
  const latest = entry.versions.at(-1);
  const [title, setTitle] = useState(latest?.title || '');
  const [text, setText] = useState(latest?.text || '');
  const [contributions, setContributions] = useState<Record<string, string>>(latest?.contributions || {});
  return <form className="space-y-2" onSubmit={e => { e.preventDefault(); void submit({ expected_version: latest?.number || 0, title, text, contributions }); }}>
    <p>Faqat vazifaga oid umumiy ishni yozing. Shaxsiy kontakt ma’lumotlarini kiritmang. Har yangi versiya uchun ikkala sherik yana tasdiqlaydi.</p>
    <label className="block">Sarlavha<input className={input} required maxLength={100} value={title} onChange={e => setTitle(e.target.value)} /></label>
    <label className="block">Umumiy dialog yoki matn<textarea className={input} rows={7} required maxLength={6000} value={text} onChange={e => setText(e.target.value)} /></label>
    {entry.members.map(id => <label className="block" key={id}>{entry.names[id]} nima bajardi?<textarea className={input} required maxLength={500} value={contributions[id] || ''} onChange={e => setContributions({ ...contributions, [id]: e.target.value })} /></label>)}
    <button className={button} disabled={busy}>Yangi versiyani saqlash</button>
  </form>;
}

function ReviewForm({ version, rubric, scale, busy, submit }: { version: number; rubric: Record<string, string>; scale: Record<string, string>; busy: boolean; submit: (body: unknown) => Promise<void> }) {
  const [scores, setScores] = useState<Record<string, number>>({ task: 0, language: 0, collaboration: 0 });
  const [decision, setDecision] = useState('changes_requested');
  const [strength, setStrength] = useState('');
  const [next, setNext] = useState('');
  const [observed, setObserved] = useState(false);
  const [fluency, setFluency] = useState('');
  const [pronunciation, setPronunciation] = useState('');
  return <form className="space-y-2 border-t pt-3" onSubmit={e => { e.preventDefault(); void submit({ expected_version: version, decision, ...scores, strength, next_step: next, speaking_observed: observed, fluency: observed ? Number(fluency) : null, pronunciation: observed ? Number(pronunciation) : null }); }}>
    <h5 className="font-semibold">v{version} uchun o‘qituvchi tekshiruvi</h5>
    <p>Matn va har ikki ishtirokchining hissasini tekshiring. Matnni tasdiqlash uchun quyidagi uch mezon kamida 3/4 bo‘lishi kerak. Jonli og‘zaki kuzatuv alohida qayd etiladi.</p>
    {Object.entries(rubric).map(([k, label]) => <label className="block" key={k}>{label}<select className={input} value={scores[k]} onChange={e => setScores({ ...scores, [k]: Number(e.target.value) })}>{Object.entries(scale).map(([n, description]) => <option key={n} value={n}>{n} — {description}</option>)}</select></label>)}
    <fieldset className="rounded-lg border p-3 space-y-2">
      <legend>Jonli og‘zaki ijro — ixtiyoriy</legend>
      <label className="flex gap-2 items-center"><input type="checkbox" checked={observed} onChange={e => { setObserved(e.target.checked); setFluency(''); setPronunciation(''); }} />Dialogni darsda jonli eshitdim</label>
      <p>Shu versiyani ikkala sherik ijrosida eshitgan bo‘lsangiz belgilang. Joriy darajadagi so‘z/iboralar bilan baholang; boshlang‘ich o‘quvchidan murakkab gap talab qilmang. Bu juftlik ijrosi haqidagi o‘qituvchi kuzatuvi, AI yoki CEFR bahosi emas.</p>
      <label className="block">Ravonlik / nutq oqimi<select className={input} disabled={!observed} required={observed} value={fluency} onChange={e => setFluency(e.target.value)}><option value="">Bahoni tanlang</option>{oralRubric.fluency.map((label, n) => <option key={n} value={n}>{n} — {label}</option>)}</select></label>
      <label className="block">Talaffuz / tushunarlilik<select className={input} disabled={!observed} required={observed} value={pronunciation} onChange={e => setPronunciation(e.target.value)}><option value="">Bahoni tanlang</option>{oralRubric.pronunciation.map((label, n) => <option key={n} value={n}>{n} — {label}</option>)}</select></label>
      {!observed && <p>Jonli kuzatuvsiz og‘zaki baholar saqlanmaydi. Matnni tekshirish davom etadi.</p>}
    </fieldset>
    <label className="block">Aniq yaxshi jihat<textarea className={input} required minLength={10} maxLength={1000} value={strength} onChange={e => setStrength(e.target.value)} /></label>
    <label className="block">Keyingi bajariladigan qadam (aniq misol bilan)<textarea className={input} required minLength={10} maxLength={1000} value={next} onChange={e => setNext(e.target.value)} /></label>
    <label className="block">Matn bo‘yicha qaror<select className={input} value={decision} onChange={e => setDecision(e.target.value)}><option value="changes_requested">Qayta ishlash kerak</option><option value="approved">Tasdiqlash</option></select></label>
    <p>Yuborilgan xulosa o‘zgarmaydi. Keyingi tahrir alohida tekshiriladi.</p>
    <button className={button} disabled={busy || (decision === 'approved' && Object.values(scores).some(n => n < 3))}>Baholashni yuborish</button>
  </form>;
}
