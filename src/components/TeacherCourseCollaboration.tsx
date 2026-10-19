import { useEffect, useRef, useState } from 'react';
import CourseCollaboration from './CourseCollaboration';
import { getToken } from '../lib/api';

type QueueItem = { entry_id: string; group_id: number; group_name: string; language: string; lesson: number; title: string; version: number };

/** Mount inside the existing authenticated teacher layout. Server checks group ownership. */
export default function TeacherCourseCollaboration() {
  const [token, setToken] = useState(getToken);
  useEffect(() => {
    const timer = window.setInterval(() => setToken(getToken()), 500);
    return () => clearInterval(timer);
  }, []);
  return token ? <TeacherWorkspace key={token} token={token} /> : <p>O‘qituvchi hisobiga kiring.</p>;
}

function TeacherWorkspace({ token }: { token: string }) {
  const [language, setLanguage] = useState('en');
  const [lesson, setLesson] = useState(1);
  const [groupId, setGroupId] = useState<number>();
  const [items, setItems] = useState<QueueItem[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const alive = useRef(true);
  const controller = useRef<AbortController | null>(null);
  async function refresh() {
    controller.current?.abort();
    const next = new AbortController(); controller.current = next;
    setLoading(true); setError('');
    try {
      if (getToken() !== token) throw new Error('Hisob o‘zgardi.');
      const response = await fetch('/api/course-collaboration/review-queue', { cache: 'no-store', signal: next.signal,
        headers: { Authorization: `Bearer ${token}`, 'X-Active-Role': 'teacher' } });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Navbat yuklanmadi.');
      if (alive.current && getToken() === token && !next.signal.aborted) setItems(data.items);
    } catch (e) {
      if (alive.current && !next.signal.aborted) setError(e instanceof Error ? e.message : 'Navbat yuklanmadi.');
    } finally { if (alive.current && !next.signal.aborted) setLoading(false); }
  }
  useEffect(() => {
    alive.current = true; void refresh();
    return () => { alive.current = false; controller.current?.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <section className="mx-auto max-w-4xl space-y-4 p-4">
    <h2 className="text-2xl font-bold">Juftlik ishlarini baholash</h2>
    <div className="space-y-2 rounded-xl border p-4"><h3 className="font-bold">Tekshiruv kutayotgan ishlar</h3>
      <button className="rounded border px-3 py-2" disabled={loading} onClick={() => void refresh()}>Navbatni yangilash</button>
      {error && <p role="alert">{error}</p>}
      {loading && <p role="status">Yuklanmoqda…</p>}
      {!loading && !error && !items.length && <p>Hozircha tekshiruv kutayotgan ish yo‘q.</p>}
      {items.map(item => <button key={item.entry_id} className="block w-full rounded border p-3 text-left" onClick={() => { setLanguage(item.language); setLesson(item.lesson); setGroupId(item.group_id); }}>
        {item.group_name} · {item.language.toUpperCase()} · {item.lesson}-dars · {item.title} (v{item.version})
      </button>)}
    </div>
    <div className="flex gap-4"><label>Til<select className="block rounded border p-2" value={language} onChange={e => { setLanguage(e.target.value); setLesson(1); }}><option value="en">English</option><option value="de">Deutsch</option></select></label>
      <label>Dars<select className="block rounded border p-2" value={lesson} onChange={e => setLesson(Number(e.target.value))}>{Array.from({ length: language === 'de' ? 72 : 192 }, (_, n) => <option key={n + 1} value={n + 1}>{n + 1}-dars</option>)}</select></label></div>
    <CourseCollaboration language={language} lesson={lesson} groupId={groupId} mode="teacher" />
  </section>;
}
