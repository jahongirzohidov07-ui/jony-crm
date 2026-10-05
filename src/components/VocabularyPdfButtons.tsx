import { useState } from 'react';
import { Download } from 'lucide-react';
import type { Word } from '../lib/intensive';
import type { VocabularyPdfKind } from '../lib/intensivePdf';

export default function VocabularyPdfButtons({ pool, mixed = false }: { pool: Word[]; mixed?: boolean }) {
  const [busy, setBusy] = useState<VocabularyPdfKind | null>(null);
  const [error, setError] = useState('');
  async function download(kind: VocabularyPdfKind) {
    if (busy) return;
    setBusy(kind); setError('');
    try {
      const { vocabularyPdf } = await import('../lib/intensivePdf');
      const blob = await vocabularyPdf(pool, mixed, kind);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url;
      a.download = `jony-${pool.length}-soz-${pool[0].id}-${pool.at(-1)!.id}-${kind}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch { setError('PDF yuklanmadi. Qayta urinib ko‘ring.'); }
    finally { setBusy(null); }
  }
  return <div className="my-4 rounded-xl border border-blue-100 bg-blue-50 p-4">
    <p className="mb-3 text-sm font-semibold text-blue-950">Tanlangan {pool.length} ta so‘zni yuklab olish</p>
    <div className="flex flex-wrap gap-2">{([['words', 'Lug‘at PDF'], ['exercises', 'Mashqlar PDF'], ['answers', 'Javoblar PDF']] as const).map(([kind, label]) => <button key={kind} type="button" disabled={!!busy || !pool.length} onClick={() => download(kind)} className="inline-flex items-center gap-2 rounded-xl border border-blue-200 bg-white px-4 py-2.5 text-sm font-semibold text-blue-800 disabled:opacity-50"><Download size={16} />{busy === kind ? 'Tayyorlanmoqda…' : label}</button>)}</div>
    <p className="mt-2 text-xs leading-5 text-slate-600">Mashqlar javobsiz. Javoblar ustoz uchun alohida PDFda.</p>
    {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
  </div>;
}
