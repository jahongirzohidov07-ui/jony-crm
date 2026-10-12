import { useState } from 'react';
import { api } from '../lib/api';
import { oralDirections, oralRubric } from '../lib/russianPlacement';
import type { RussianPlacementResult } from '../lib/russianPlacement';

type Row = { id: number; lead_id: number; name: string; phone: string; date: string; result: RussianPlacementResult };

export default function RussianPlacementResults() {
  const [rows, setRows] = useState<Row[]>([]);
  const [open, setOpen] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function load() {
    setOpen(true); setBusy(true); setError('');
    try { setRows((await api.fresh<{ rows: Row[] }>('/russian-placement/results')).rows); }
    catch { setError('Natijalar yuklanmadi. Qayta urinib ko‘ring.'); }
    finally { setBusy(false); }
  }
  return <div className="mt-3">
    <button className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700" onClick={load} disabled={busy}>
      {busy ? 'Yuklanmoqda…' : 'Rus tili testi natijalari · yangilash'}
    </button>
    {open && <div className="mt-3 space-y-2">
      <button className="text-sm text-slate-500" onClick={() => setOpen(false)}>Yopish</button>
      {error && <p role="alert">{error}</p>}
      {!busy && !error && !rows.length && <p>Hali natija yo‘q.</p>}
      {rows.map(r => <details key={r.id} className="rounded-xl border bg-white p-3 text-sm">
        <summary className="cursor-pointer font-semibold">{r.name} · {r.result.score}/48 · {r.result.label}</summary>
        <p className="my-2">+{r.phone} · {new Date(r.date).toLocaleString('uz-UZ', { timeZone: 'Asia/Tashkent' })}</p>
        <p>Filial: {r.result.recommendation.branch_name} · {r.result.allPassed ? 'Yakuniy og‘zaki tekshiruv' : `${r.result.month}-oy, ${r.result.lesson}-dars`}</p>
        <p>Qaytarish: {r.result.gaps.join(', ') || 'Asosiy bo‘shliq topilmadi.'}</p>
        <ul className="my-3 list-disc pl-5">{r.result.blocks.map(b => <li key={b.stage}>{b.label}: {b.correct}/8 · grammatika {b.grammar}/4 · o‘qish {b.reading}/2 · {b.passed ? 'mezon bajarildi' : 'mustahkamlash kerak'}</li>)}</ul>
        <h3 className="mt-3 font-semibold">Guruhga qabuldan oldin og‘zaki tekshiruv shart</h3>
        <p className="my-2">{oralDirections}</p>
        <ol className="list-decimal space-y-2 pl-5">{oralRubric.map(item => <li key={item}>{item}</li>)}</ol>
        <a className="mt-3 inline-block font-semibold text-blue-700 underline" href={`/plans/russian?lesson=${r.result.lesson ?? 144}`}>{r.result.allPassed ? "Yakuniy suhbat darsini ochish" : "Tavsiya darsini ochish"}</a>
        <p className="mt-3 text-slate-500">Natija lid izohiga yozildi. Bu bosqich va filial tavsiyasi; guruh avtomatik tayinlanmaydi.</p>
      </details>)}
    </div>}
  </div>;
}
