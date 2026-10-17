import { useEffect, useRef, useState } from 'react';
import { getToken } from '../lib/api';

type Audio = { mime: string; base64: string };
type Kind = 'dialogue' | 'story' | 'speaking';
type Version = { number: number; title: string; type: Kind; text: string; audio: Audio | null; created_at: string };
type Entry = { id: string; language: string; lesson: number; versions: Version[] };
type Summary = { id: string; title: string; type: Kind; version_count: number; updated_at: string; has_audio: boolean };
type Listing = { entries: Summary[]; total_entries: number; lesson_entries: number; total_text_bytes: number; total_audio_bytes: number; lesson_title: string; prompt: string };
type Props = { language: string; lesson: number; onSaved?: () => void };
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

function PortfolioEditor({ language, lesson, onSaved, token }: Props & { token: string }) {
  const [listing, setListing] = useState<Listing | null>(null);
  const [entry, setEntry] = useState<Entry | null>(null);
  const [earlier, setEarlier] = useState(1);
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState<Kind>('dialogue');
  const [text, setText] = useState('');
  const [audio, setAudio] = useState<Audio | null>(null);
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

  function edit(value: Entry | null) {
    cleanupRecording(); setRecording(false); setPreparing(false);
    setEntry(value); setEarlier(1); setMessage('');
    const last = value?.versions.at(-1);
    setTitle(last?.title ?? ''); setKind(last?.type ?? 'dialogue'); setText(last?.text ?? ''); setAudio(last?.audio ?? null);
  }
  async function open(id: string) {
    setBusy(true);
    try { const value = await request<Entry>(`/${id}`); if (current()) edit(value); }
    catch (error) { report(error); }
    finally { if (current()) setBusy(false); }
  }
  async function save() {
    setBusy(true); setMessage('');
    try {
      const value = await request<Entry>(entry ? `/${entry.id}` : '', entry ? 'PUT' : 'POST', {
        title, type: kind, text, audio, ...(entry ? { expected_version: entry.versions.length } : {}),
      });
      if (current()) { edit(value); setMessage('Sizning ijodiy ishingiz saqlandi.'); onSaved?.(); }
      await refresh();
    } catch (error) { report(error); }
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
  const inputClass = 'w-full rounded-xl border border-slate-300 bg-white p-3 text-slate-900';
  const buttonClass = 'rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:opacity-50';

  return <section aria-label="Ijodiy portfolio" className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 text-slate-900">
    <header><h2 className="text-lg font-semibold">Mening ijodiy portfoliom</h2>
      <p className="text-sm text-slate-600">Shaxsiy ishlaringiz. Bu tasdiqlangan mahorat emas va XP bermaydi.</p></header>
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
      <fieldset disabled={locked || full} className="space-y-3">
        <legend className="font-medium">{entry ? 'Yangi versiya tayyorlash' : 'O‘z ishimni yaratish'}</legend>
        <label className="block">Sarlavha<input className={inputClass} maxLength={100} value={title} onChange={event => setTitle(event.target.value)} /></label>
        <label className="block">Ish turi<select className={inputClass} value={kind} onChange={event => setKind(event.target.value as Kind)}>
          {Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select></label>
        <label className="block">Mening matnim<textarea className={inputClass} rows={6} maxLength={6000} value={text} onChange={event => setText(event.target.value)} /></label>
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
        </article>)}</div></> : <p>Taqqoslash uchun ikkinchi versiyani saqlang. Birinchi versiya o‘zgarishsiz qoladi.</p>}
      </div>}
    </>}
  </section>;
}
