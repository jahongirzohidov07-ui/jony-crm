import { useEffect, useRef, useState } from 'react';
import { getToken } from '../lib/api';
import { getCourseMission } from '../lib/courseMissions';

type Audio = { mime: string; base64: string };
type Kind = 'dialogue' | 'story' | 'speaking';
type Mission = { id: string; title: string; prompt: string; suggested_type: Kind; targets: string[]; lesson_title: string; output?: string; criteria?: string[] };
type Coaching = { observed_positive: string; next_improvement: string; retry: string; disclaimer: string };
type Feedback = { status: 'pending' | 'ready' | 'unavailable'; version: number; attempts?: number; criteria?: { id: string; label: string; evidence: string; comment: string }[]; next_step?: string; comparison?: { previous_version: number; before: string; after: string; comment: string } | null };
type Version = { number: number; title: string; type: Kind; text: string; audio: Audio | null; created_at: string; coaching?: Coaching; feedback?: Feedback };
type Entry = { id: string; language: string; lesson: number; versions: Version[]; mission?: Mission | null; mission_evidence?: {status: string; version: number} | null };
type Summary = { id: string; title: string; type: Kind; version_count: number; updated_at: string; has_audio: boolean };
type RecentWork = { id: string; lesson: number; title: string; updated_at: string };
type Listing = { entries: Summary[]; recent_works?: RecentWork[]; total_entries: number; lesson_entries: number; total_text_bytes: number; total_audio_bytes: number; lesson_title: string; prompt: string; missions?: Mission[] };
type Props = { language: string; lesson: number; onSaved?: () => void; onOpenWork?: (lesson: number, id: string) => void; initialEntryId?: string };
const MAX_AUDIO = 1024 * 1024;
const labels: Record<Kind, string> = { dialogue: 'Dialog', story: 'Hikoya', speaking: 'Og‘zaki ijod' };
const mimes = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4', 'audio/webm', 'audio/ogg'];

function Playback({ audio, label }: { audio: Audio | null; label: string }) {
  const [url, setUrl] = useState('');
  useEffect(() => {
    if (!audio) { setUrl(''); return; }
    const bytes = Uint8Array.from(atob(audio.base64), c => c.charCodeAt(0));
    const next = URL.createObjectURL(new Blob([bytes], { type: audio.mime }));
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [audio]);
  return audio && url ? <audio aria-label={label} controls preload="none" src={url} className="w-full" /> : null;
}

function TextFeedback({ version, locked, onRequest, onReload }: { version: Version; locked: boolean; onRequest: (number: number) => void; onReload: () => void }) {
  const feedback = version.feedback;
  return <aside aria-label={version.number + '-versiya AI maslahati'} className="space-y-2 rounded-xl border border-indigo-200 p-3 text-sm">
    <h4 className="font-semibold">{version.number}-versiya: matn bo‘yicha AI maslahat</h4>
    <p>AI xato qilishi mumkin. Bu o‘qituvchi tasdig‘i emas; audio va talaffuz baholanmaydi, XP berilmaydi.</p>
    {!feedback && <>
      <p>Saqlangan matningiz, oldingi versiya va dars vazifasi AI yordamida tekshiriladi. Audio va hisob ma’lumotlari yuborilmaydi.</p>
      <details className="text-xs text-slate-600"><summary>Maslahat olish tartibi</summary><p>Avval matnni saqlang. Har versiya uchun 3 urinish, kuniga 6 so‘rov (Toshkent vaqti). Xizmat javob bermagan so‘rov ham hisoblanadi.</p></details>
      <button className="rounded-lg border px-3 py-2 disabled:opacity-50" disabled={locked || !version.text.trim()} onClick={() => onRequest(version.number)}>Saqlangan matnga AI maslahat olish</button>
      {!version.text.trim() && <p>Audio tekshirilmaydi. Maslahat uchun yangi versiyaga matn qo‘shing.</p>}
    </>}
    {feedback?.status === 'pending' && <><p role="status">Maslahat so‘ralgan. Natijani yangilang; 2 daqiqadan keyin javob bo‘lmasa qayta so‘rash mumkin.</p><button disabled={locked} onClick={onReload}>Natijani yangilash</button></>}
    {feedback?.status === 'unavailable' && <p role="status">AI maslahat mavjud emas: xizmat javob bermadi yoki javobni tekshirib bo‘lmadi. Bu matningiz yomon degani emas. Oddiy maslahat bilan davom etishingiz mumkin.</p>}
    {feedback?.status === 'unavailable' && ((feedback.attempts ?? 1) < 3
      ? <><p>Qayta so‘rov kunlik limitga kiradi. Natija olinsa shu versiyada saqlanadi.</p><button disabled={locked} onClick={() => onRequest(version.number)}>AI maslahatni qayta so‘rash ({feedback.attempts ?? 1}/3 urinish)</button></>
      : <p>Bu versiya uchun 3 ta urinish tugadi. Yangi versiya bilan davom eting.</p>)}
    {feedback?.status === 'ready' && <>
      {feedback.criteria?.map(item => <div key={item.id}><strong>{item.label}</strong><blockquote className="whitespace-pre-wrap break-words">“{item.evidence}”</blockquote><p>{item.comment}</p></div>)}
      <p><strong>Keyingi qadam: </strong>{feedback.next_step}</p>
      {feedback.comparison && <div><strong>{feedback.comparison.previous_version}-versiya bilan taqqoslash</strong><p className="whitespace-pre-wrap break-words">Oldin: “{feedback.comparison.before}”</p><p className="whitespace-pre-wrap break-words">Hozir: “{feedback.comparison.after}”</p><p>{feedback.comparison.comment}</p></div>}
    </>}
  </aside>;
}

/** No localStorage drafts or shared GET cache: recordings remain account-private. */
export default function CoursePortfolio(props: Props) {
  const [token, setToken] = useState(getToken);
  useEffect(() => {
    const sync = () => setToken(getToken());
    const timer = window.setInterval(sync, 500);
    window.addEventListener('storage', sync);
    window.addEventListener('focus', sync);
    return () => { clearInterval(timer); window.removeEventListener('storage', sync); window.removeEventListener('focus', sync); };
  }, []);
  if (!token) return <p>Portfolioni ochish uchun hisobingizga kiring.</p>;
  return <PortfolioEditor key={`${token}:${props.language}:${props.lesson}`} {...props} token={token} />;
}

function PortfolioEditor({ language, lesson, onSaved, onOpenWork, initialEntryId, token }: Props & { token: string }) {
  const openedInitial = useRef<string | null>(null);
  const [listing, setListing] = useState<Listing | null>(null);
  const [entry, setEntry] = useState<Entry | null>(null);
  const [earlier, setEarlier] = useState(1);
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState<Kind>('dialogue');
  const [text, setText] = useState('');
  const [audio, setAudio] = useState<Audio | null>(null);
  const [missionId, setMissionId] = useState('');
  const initializedMission = useRef(false);
  const textInput = useRef<HTMLTextAreaElement>(null);
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [message, setMessage] = useState('');
  const alive = useRef(true);
  const generation = useRef(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requests = useRef(new Set<AbortController>());
  const base = '/api/student/course-practice/portfolio';
  const query = `?language=${encodeURIComponent(language)}&lesson=${lesson}`;
  const current = () => alive.current && getToken() === token;

  function cleanupRecording() {
    generation.current += 1;
    if (timer.current) clearTimeout(timer.current);
    if (recorder.current) {
      recorder.current.ondataavailable = null;
      recorder.current.onstop = null;
      recorder.current.onerror = null;
      if (recorder.current.state !== 'inactive') recorder.current.stop();
    }
    stream.current?.getTracks().forEach(track => track.stop());
    stream.current = null;
    recorder.current = null;
  }

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      cleanupRecording();
      requests.current.forEach(controller => controller.abort());
    };
  }, []);

  async function request<T,>(path: string, method = 'GET', body?: unknown): Promise<T> {
    if (!current()) throw new Error('Hisob o‘zgardi. Sahifani qayta oching.');
    const controller = new AbortController();
    requests.current.add(controller);
    try {
      const response = await fetch(base + path + query, {
        method, cache: 'no-store', signal: controller.signal,
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const result = await response.json();
      if (!current()) throw new Error('Hisob o‘zgardi.');
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Ma’lumot formati yoki hajmi noto‘g‘ri.');
      return result;
    } finally { requests.current.delete(controller); }
  }
  const report = (error: unknown) => { if (current()) setMessage(error instanceof Error ? error.message : 'Amal bajarilmadi. Qayta urinib ko‘ring.'); };
  async function refresh() { const result = await request<Listing>(''); if (current()) setListing(result); }
  useEffect(() => { void refresh().catch(report); }, []);
  function defaultMission() {
    const weekly = getCourseMission(language, lesson);
    return weekly?.lesson === lesson ? listing?.missions?.find(m => m.id === weekly.id) : undefined;
  }
  useEffect(() => {
    if (!listing || initializedMission.current) return;
    initializedMission.current = true;
    // Existing work owns its saved mission; new week-end work uses only a server-approved ID.
    if (initialEntryId) return;
    const weekly = defaultMission();
    if (weekly) { setMissionId(weekly.id); setKind(weekly.suggested_type); setTitle(weekly.title); }
  }, [listing]);


  function edit(value: Entry | null) {
    cleanupRecording(); setRecording(false); setPreparing(false);
    setEntry(value); setEarlier(1); setMessage('');
    const weekly = value ? undefined : defaultMission();
    setMissionId(value?.mission?.id ?? weekly?.id ?? '');
    const last = value?.versions.at(-1);
    setTitle(last?.title ?? weekly?.title ?? ''); setKind(last?.type ?? weekly?.suggested_type ?? 'dialogue'); setText(last?.text ?? ''); setAudio(last?.audio ?? null);
  }
  async function open(id: string) {
    setBusy(true);
    try { const value = await request<Entry>(`/${id}`); if (current()) edit(value); }
    catch (error) { report(error); }
    finally { if (current()) setBusy(false); }
  }
  useEffect(() => {
    // The editor remounts on account/language/lesson changes. Wait for this
    // scope's listing, and never fetch a supplied ID from another lesson.
    if (!listing || !initialEntryId || busy || recording || preparing || !current()
        || openedInitial.current === initialEntryId) return;
    openedInitial.current = initialEntryId;
    if (listing.entries.some(item => item.id === initialEntryId)) {
      void open(initialEntryId);
    } else {
      setMessage('Tanlangan ish bu darsda topilmadi.');
    }
  }, [listing, initialEntryId, busy, recording, preparing]);

  async function save() {
    setBusy(true); setMessage('');
    try {
      const value = await request<Entry>(entry ? `/${entry.id}` : '', entry ? 'PUT' : 'POST', {
        title, type: kind, text, audio, ...(missionId ? { mission_id: missionId } : {}),
        ...(entry ? { expected_version: entry.versions.length } : {}),
      });
      if (current()) { edit(value); setMessage('Sizning ijodiy ishingiz saqlandi.'); onSaved?.(); }
      await refresh();
    } catch (error) { report(error); }
    finally { if (current()) setBusy(false); }
  }
  async function feedback(number: number) {
    if (!entry) return;
    setBusy(true); setMessage('');
    try {
      const value = await request<Entry>('/' + entry.id + '/feedback/' + number, 'POST');
      // Keep unsaved draft fields intact when feedback arrives.
      if (current()) setEntry(value);
    } catch (error) { report(error); }
    finally { if (current()) setBusy(false); }
  }
  async function reloadFeedback() {
    if (!entry) return;
    setBusy(true);
    try { const value = await request<Entry>('/' + entry.id); if (current()) setEntry(value); }
    catch (error) { report(error); }
    finally { if (current()) setBusy(false); }
  }
  async function remove() {
    if (!entry || !window.confirm('Ushbu ish va barcha versiyalarini o‘chirasizmi?')) return;
    setBusy(true);
    try { await request(`/${entry.id}`, 'DELETE'); if (current()) { edit(null); onSaved?.(); } await refresh(); }
    catch (error) { report(error); }
    finally { if (current()) setBusy(false); }
  }

  const supported = typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia;
  async function startRecording() {
    if (!supported) { setMessage('Bu brauzer ovoz yozishni qo‘llamaydi. Ishingizni matn bilan saqlang.'); return; }
    cleanupRecording();
    const attempt = generation.current;
    setPreparing(true); setMessage('');
    let acquired: MediaStream | null = null;
    try {
      const mime = mimes.find(value => MediaRecorder.isTypeSupported(value));
      if (!mime) throw new Error('Mos audio formati yo‘q. Matn bilan davom eting.');
      acquired = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!current() || attempt !== generation.current) { acquired.getTracks().forEach(track => track.stop()); return; }
      stream.current = acquired;
      const rec = new MediaRecorder(acquired, { mimeType: mime, audioBitsPerSecond: 48000 });
      recorder.current = rec;
      const chunks: Blob[] = [];
      let size = 0;
      let exceeded = false;
      let failed = false;
      const stop = () => {
        if (timer.current) clearTimeout(timer.current);
        if (rec.state !== 'inactive') rec.stop();
        acquired?.getTracks().forEach(track => track.stop());
      };
      rec.ondataavailable = event => {
        size += event.data.size;
        if (size > MAX_AUDIO) { exceeded = true; stop(); return; }
        chunks.push(event.data);
      };
      rec.onerror = () => { failed = true; stop(); if (current()) setMessage('Ovoz yozilmadi. Matn bilan davom eting.'); };
      rec.onstop = async () => {
        stop();
        if (!current() || attempt !== generation.current) return;
        setRecording(false); setPreparing(true);
        try {
          if (exceeded || failed || !size) {
            if (!failed) setMessage(exceeded ? 'Yozuv 1 MiB dan oshdi. Qisqaroq yozing; oldingi audio saqlandi.' : 'Ovoz yozilmadi. Qayta urinib ko‘ring yoki matn yozing.');
            return;
          }
          const bytes = new Uint8Array(await new Blob(chunks).arrayBuffer());
          let binary = '';
          for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
          if (current() && attempt === generation.current) setAudio({ mime, base64: btoa(binary) });
        } catch (error) { report(error); }
        finally { if (current() && attempt === generation.current) setPreparing(false); }
      };
      rec.start(250); setRecording(true); setPreparing(false);
      timer.current = setTimeout(stop, 60000);
    } catch (error) {
      acquired?.getTracks().forEach(track => track.stop());
      if (current() && attempt === generation.current) {
        setPreparing(false); setRecording(false);
        setMessage(error instanceof DOMException && error.name === 'NotAllowedError'
          ? 'Mikrofonga ruxsat berilmadi. Ishingizni matn bilan saqlashingiz mumkin.'
          : 'Ovoz yozish imkoni bo‘lmadi. Matn bilan davom eting.');
      }
    }
  }
  const latest = entry?.versions.at(-1);
  const previous = entry?.versions.find(version => version.number === earlier);
  const full = !!entry && entry.versions.length >= 3;
  const locked = busy || recording || preparing;
  const mission = entry?.mission ?? listing?.missions?.find(item => item.id === missionId);
  function retry() {
    if (full) {
      // Keep the learner's draft and chosen task; never overwrite saved versions.
      setEntry(null); setEarlier(1);
      setMessage('Davomi alohida yangi ish sifatida saqlanadi. Oldingi versiyalar o‘zgarishsiz qoladi.');
    }
    requestAnimationFrame(() => { textInput.current?.focus(); textInput.current?.scrollIntoView({ block: 'center', behavior: 'smooth' }); });
  }
  const inputClass = 'w-full rounded-xl border border-slate-300 bg-white p-3 text-slate-900';
  const buttonClass = 'rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:opacity-50';

  return <section aria-label="Ijodiy portfolio" className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 text-slate-900">
    <header><h2 className="text-lg font-semibold">Mening ijodiy portfoliom</h2>
      <p className="text-sm text-slate-600">Shaxsiy ishlaringiz. Bu tasdiqlangan mahorat emas va XP bermaydi.</p></header>
    {listing && <nav aria-label="Oxirgi ishlarim" className="space-y-2 rounded-xl bg-slate-50 p-3">
      <h3 className="font-semibold">Oxirgi ishlarim</h3>
      <p className="text-xs text-slate-600">Shu tildagi barcha darslardan eng oxirgi 5 ta ish.</p>
      {listing.recent_works?.length ? <div className="flex flex-wrap gap-2">
        {listing.recent_works.map(item => <button key={item.id} className={buttonClass}
          disabled={locked || (item.lesson !== lesson && !onOpenWork)}
          aria-pressed={entry?.id === item.id}
          onClick={() => {
            if (!current()) return;
            if (item.lesson === lesson) void open(item.id);
            else onOpenWork?.(item.lesson, item.id);
          }}>
          {item.title} · {item.lesson}-dars · {new Date(item.updated_at).toLocaleDateString('uz-UZ')}
        </button>)}
      </div> : <p className="text-sm">Hali saqlangan ish yo‘q.</p>}
    </nav>}
    <details className="text-sm text-slate-600"><summary className="cursor-pointer">Saqlash chegaralari</summary>
      <p className="mt-2">Har darsga 8 ish; har ishga 3 o‘zgarmas versiya. Matn: 6000 belgi, barcha versiyalarga jami 2 MiB. Audio: har versiyaga 1 MiB, jami 8 MiB. Yozuv 60 soniyada to‘xtaydi. Joy tugasa, kerakli darsdagi eski ishni tanlab o‘chirishingiz mumkin; hech narsa avtomatik o‘chirilmaydi.</p>
      {listing && <p className="mt-2">Barcha darslar: {listing.total_entries} ish · {(listing.total_audio_bytes / MAX_AUDIO).toFixed(1)}/8 MiB audio · {((listing.total_text_bytes ?? 0) / MAX_AUDIO).toFixed(2)}/2 MiB matn</p>}
    </details>
    {message && <p role="status" className="rounded-xl bg-amber-50 p-3">{message}</p>}
    {!listing ? <button className={buttonClass} onClick={() => void refresh().catch(report)}>Portfolioni yuklash</button> : <>
      <div className="rounded-xl bg-slate-50 p-3"><strong>{lesson}-dars · {listing.lesson_title}</strong>
        <p className="mt-2 text-sm">Darsga tayanch topshiriq: {listing.prompt}</p>
        <p className="mt-2 text-sm">Shu mavzudagi so‘z va iboralardan o‘z dialogingiz, hikoyangiz yoki ovozli ishingizni yarating. Qahramonlar va voqealarni o‘zingiz tanlang. Dastlabki darslarda qisqa iboralar ham yetarli.</p></div>
      <p className="text-sm">Bu dars: {listing.entries.length}/8 ish</p>
      <div className="flex flex-wrap gap-2"><button className={buttonClass} disabled={locked} onClick={() => edit(null)}>Yangi ish</button>
        {listing.entries.map(item => <button key={item.id} className={buttonClass} disabled={locked} aria-pressed={entry?.id === item.id} onClick={() => void open(item.id)}>
          {item.title} · {labels[item.type]} · {item.version_count}/3 {item.has_audio ? '· Audio' : ''}
        </button>)}</div>
      {!listing.entries.length && <p className="text-sm">Bu darsda hali ijodiy ish yo‘q.</p>}
      <div className="space-y-2 rounded-xl border border-indigo-100 bg-indigo-50 p-3">
        {!entry ? <label className="block font-medium">Hayotda nimani aytmoqchisiz?
          <select aria-label="Hayotiy vazifa" className={inputClass} value={missionId} disabled={locked} onChange={event => {
            setMissionId(event.target.value);
            const chosen = listing.missions?.find(item => item.id === event.target.value);
            if (chosen) setKind(chosen.suggested_type);
          }}><option value="">O‘z mavzum — erkin ijod</option>
            {listing.missions?.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select></label> : <p className="font-medium">{mission ? `Vazifam: ${mission.title}` : 'Mening erkin ijodiy ishim'}</p>}
        {mission && <><p className="text-sm">{mission.prompt}</p>
          {mission.output && <p className="text-sm"><strong>Hafta oxirida: </strong>{mission.output}.</p>}
          {!!mission.criteria?.length && <div className="text-sm"><p className="font-semibold">Saqlashdan oldin tekshiring:</p><ul className="list-disc space-y-1 pl-5">{mission.criteria.map(item => <li key={item}>{item}</li>)}</ul></div>}
          {!!mission.targets.length && <p className="text-sm">Darsdan tayanch so‘zlar: {mission.targets.join(', ')}. Vaziyatingizga mosini tanlang.</p>}</>}
        {entry?.mission_evidence && <p className="text-sm">Vazifaga bog‘langan {entry.mission_evidence.version}-versiya saqlandi. Bu ish namunasi; vazifaning to‘g‘ri bajarilgani hali tekshirilmagan.</p>}
      </div>
      {latest && <TextFeedback version={latest} locked={locked} onRequest={number => void feedback(number)} onReload={() => void reloadFeedback()} />}
      {latest?.coaching && latest.feedback?.status !== 'ready' && <aside aria-label="Keyingi ijodiy qadam" className="space-y-2 rounded-xl bg-emerald-50 p-4">
        <h3 className="font-semibold">Ishingizni bir qadam yaxshilang</h3>
        <p className="text-xs text-slate-600">Saqlangan {latest.number}-versiya bo‘yicha</p>
        <p className="text-sm"><strong>Kuzatilgan jihat: </strong>{latest.coaching.observed_positive}</p>
        <p className="text-sm"><strong>Bitta keyingi qadam: </strong>{latest.coaching.next_improvement}</p>
        <p className="text-sm">{latest.coaching.retry}</p>
        <button className={buttonClass} disabled={locked || (full && listing.entries.length >= 8)} onClick={retry}>{full ? 'Alohida ishda qayta urinish' : 'Maslahat bilan qayta urinish'}</button>
        {full && listing.entries.length >= 8 && <p className="text-sm">Yangi ish uchun bu darsdagi keraksiz ishni tanlab o‘chiring. Saqlangan versiyalar ustiga yozilmaydi.</p>}
        <details className="text-xs text-slate-600"><summary>Maslahat nimaga asoslangan?</summary><p className="mt-2">{latest.coaching.disclaimer}</p></details>
      </aside>}
      <fieldset disabled={locked || full} className="space-y-3">
        <legend className="font-medium">{entry ? 'Yangi versiya tayyorlash' : 'O‘z ishimni yaratish'}</legend>
        <label className="block">Sarlavha<input className={inputClass} maxLength={100} value={title} onChange={event => setTitle(event.target.value)} /></label>
        <label className="block">Ish turi<select className={inputClass} value={kind} onChange={event => setKind(event.target.value as Kind)}>
          {Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select></label>
        <label className="block">Mening matnim<textarea ref={textInput} className={inputClass} rows={6} maxLength={6000} value={text} onChange={event => setText(event.target.value)} /></label>
        <p className="text-xs text-slate-600">{text.length}/6000 belgi — faqat matn uzunligi, bilim yoki mahorat bahosi emas.</p>
      </fieldset>
      {!supported && <p>Bu brauzerda mikrofon yozuvi mavjud emas. Matn bilan davom eting.</p>}
      <div className="flex flex-wrap gap-2">
        {recording ? <button className={buttonClass} onClick={() => { setPreparing(true); recorder.current?.stop(); stream.current?.getTracks().forEach(track => track.stop()); }}>Yozuvni to‘xtatish</button>
          : <button className={buttonClass} disabled={locked || full || !supported} onClick={() => void startRecording()}>{preparing ? 'Mikrofon tayyorlanmoqda…' : 'Ovozimni yozish'}</button>}
        {preparing && !recording && <button className={buttonClass} onClick={() => { cleanupRecording(); setPreparing(false); }}>Bekor qilish</button>}
        {audio && <button className={buttonClass} disabled={locked || full} onClick={() => setAudio(null)}>Yangi versiyadan audioni olib tashlash</button>}
      </div>
      <Playback audio={audio} label="Tayyorlanayotgan versiya ovozi" />
      {entry && audio && <p className="text-xs">Yangi ovoz yozmasangiz, joriy audio yangi versiyada ham saqlanadi va hajm limitiga qo‘shiladi.</p>}
      {full && <p>3 versiya saqlangan. Ular o‘zgartirilmaydi. Alohida yangi ish yaratishingiz mumkin.</p>}
      <div className="flex flex-wrap gap-2"><button className={`${buttonClass} bg-slate-900 text-white`} disabled={locked || full || (!entry && listing.entries.length >= 8) || !title.trim() || (!text.trim() && !audio)} onClick={() => void save()}>{entry ? 'Yangi versiyani saqlash' : 'Ishimni saqlash'}</button>
        {entry && <button className={buttonClass} disabled={locked} onClick={() => void remove()}>Ishni va versiyalarni o‘chirish</button>}</div>
      {entry && latest && <div className="space-y-3 border-t pt-4"><h3 className="font-semibold">Oldingi va oxirgi versiya</h3>
        {entry.versions.length > 1 ? <><label>Oldingi versiyani tanlang <select className="rounded-lg border p-2" value={earlier} onChange={event => setEarlier(Number(event.target.value))}>
          {entry.versions.slice(0, -1).map(version => <option key={version.number} value={version.number}>{version.number}-versiya</option>)}
        </select></label><div className="grid gap-3 md:grid-cols-2">{[previous!, latest].map(version => <article key={version.number} className="min-w-0 rounded-xl bg-slate-50 p-3">
          <h4 className="font-medium">{version.number}-versiya · {version.title}</h4><p className="text-xs">{labels[version.type]} · {new Date(version.created_at).toLocaleString('uz-UZ')}</p>
          <p className="my-3 whitespace-pre-wrap break-words">{version.text || 'Faqat ovozli ish'}</p><Playback audio={version.audio} label={`${version.number}-versiya ovozi`} />
          {version.number !== latest.number && <TextFeedback version={version} locked={locked} onRequest={number => void feedback(number)} onReload={() => void reloadFeedback()} />}
          {version.coaching && version.feedback?.status !== 'ready' && <details className="mt-3 text-sm"><summary>Shu versiyaga maslahat</summary><p className="mt-2">{version.coaching.observed_positive}</p><p className="mt-2">Bitta qadam: {version.coaching.next_improvement}</p></details>}
        </article>)}</div></> : <p>Taqqoslash uchun ikkinchi versiyani saqlang. Birinchi versiya o‘zgarishsiz qoladi.</p>}
      </div>}
    </>}
  </section>;
}
