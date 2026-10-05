import brand from '../assets/brand-icon.png';
import { vocabularyPractice } from './intensive';
import type { Word } from './intensive';

export type VocabularyPdfKind = 'words' | 'exercises' | 'answers';
const titles = { words: 'Vocabulary · lug‘at', exercises: 'Vocabulary · mashqlar', answers: 'Vocabulary · javoblar' };

// The same high-resolution image/PDF approach used by examReportExport preserves
// Uzbek characters and IPA without a network font or an additional dependency.
function pagesPdf(pages: HTMLCanvasElement[]): Blob {
  const bytes = (s: string) => new TextEncoder().encode(s);
  const combine = (parts: Uint8Array[]) => {
    const out = new Uint8Array(parts.reduce((sum, b) => sum + b.length, 0));
    let at = 0; for (const b of parts) { out.set(b, at); at += b.length; } return out;
  };
  const objects = [bytes('<< /Type /Catalog /Pages 2 0 R >>'), bytes(`<< /Type /Pages /Count ${pages.length} /Kids [${pages.map((_, i) => `${3 + i * 3} 0 R`).join(' ')}] >>`)];
  pages.forEach((canvas, i) => {
    const id = 3 + i * 3;
    const jpg = Uint8Array.from(atob(canvas.toDataURL('image/jpeg', 0.95).split(',')[1]), ch => ch.charCodeAt(0));
    objects.push(bytes(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Resources << /XObject << /Im ${id + 1} 0 R >> >> /Contents ${id + 2} 0 R >>`));
    objects.push(combine([bytes(`<< /Type /XObject /Subtype /Image /Width ${canvas.width} /Height ${canvas.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpg.length} >>\nstream\n`), jpg, bytes('\nendstream')]));
    const content = 'q 595.28 0 0 841.89 0 0 cm /Im Do Q';
    objects.push(bytes(`<< /Length ${content.length} >>\nstream\n${content}\nendstream`));
  });
  const parts = [bytes('%PDF-1.4\n')], offsets: number[] = [];
  let offset = parts[0].length;
  objects.forEach((obj, i) => {
    offsets.push(offset); const part = combine([bytes(`${i + 1} 0 obj\n`), obj, bytes('\nendobj\n')]);
    parts.push(part); offset += part.length;
  });
  parts.push(bytes(`xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${offsets.map(o => `${String(o).padStart(10, '0')} 00000 n \n`).join('')}trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${offset}\n%%EOF`));
  return new Blob([combine(parts)], { type: 'application/pdf' });
}

export async function vocabularyPdf(pool: Word[], mixed: boolean, kind: VocabularyPdfKind): Promise<Blob> {
  if (!pool.length || pool.length > 20) throw new Error('PDF uchun 1–20 ta so‘z tanlang.');
  await document.fonts.ready;
  const logo = new Image(); logo.src = brand; await logo.decode();
  const pages: HTMLCanvasElement[] = [];
  let c: CanvasRenderingContext2D, y = 0;
  const font = (size: number, bold = false) => { c.font = `${bold ? 700 : 400} ${size}px Arial, sans-serif`; };
  const text = (value: string, x: number, top: number, size = 22, color = '#172b4d', bold = false) => {
    font(size, bold); c.fillStyle = color; c.fillText(value, x, top);
  };
  const lines = (value: string, size = 22, bold = false) => {
    font(size, bold); const result: string[] = []; let line = '';
    for (const word of value.split(/\s+/)) {
      const next = line ? `${line} ${word}` : word;
      if (line && c.measureText(next).width > 1008) { result.push(line); line = word; } else line = next;
    }
    result.push(line); return result;
  };
  function page() {
    const canvas = document.createElement('canvas'); canvas.width = 1200; canvas.height = 1697;
    const context = canvas.getContext('2d'); if (!context) throw new Error('PDF tayyorlab bo‘lmadi.'); c = context;
    c.fillStyle = '#ffffff'; c.fillRect(0, 0, 1200, 1697);
    c.drawImage(logo, 64, 54, 52, 52); text('JONY INTENSIVE', 134, 89, 25, '#2162e8', true);
    c.fillStyle = '#2162e8'; c.fillRect(64, 132, 1072, 4);
    text(titles[kind], 64, 192, 36, '#10213b', true);
    text(`${pool.length} ta so‘z · ${mixed ? 'Aralash to‘plam' : 'Tanlangan to‘plam'}`, 64, 233, 22, '#62748b');
    if (kind === 'exercises') text('Ism: ________________________   Sana: ______________', 64, 275, 21);
    if (kind === 'answers') text('Ustoz uchun · o‘quvchiga mashqdan keyin ko‘rsating', 64, 275, 21);
    y = kind === 'words' ? 275 : 315; pages.push(canvas);
  }
  function block(rows: { value: string; size?: number; color?: string; bold?: boolean }[], answerSpace = false) {
    const prepared = rows.map(row => ({ ...row, size: row.size ?? 22, lines: lines(row.value, row.size ?? 22, row.bold) }));
    const height = prepared.reduce((sum, row) => sum + row.lines.length * (row.size + 9) + 6, 26) + (answerSpace ? 52 : 0);
    if (y + height > 1560) page();
    c.fillStyle = '#f3f6fc'; c.fillRect(64, y, 1072, height);
    let at = y + 32;
    for (const row of prepared) {
      for (const line of row.lines) { text(line, 84, at, row.size, row.color, row.bold); at += row.size + 9; }
      at += 6;
    }
    if (answerSpace) text('Javob: ______________________________________________________', 84, at + 15, 22, '#62748b');
    y += height + 16;
  }
  page();
  if (kind === 'words') {
    for (const w of pool) block([
      { value: `${w.id}. ${w.word}  ${w.ipa}`, size: 26, bold: true, color: '#2162e8' },
      { value: w.meaning, bold: true },
      { value: w.example },
      { value: w.translation, color: '#62748b' },
    ]);
  } else {
    vocabularyPractice(pool, mixed).forEach((q, i) => block(kind === 'exercises'
      ? [{ value: `${i + 1}. ${q.prompt}`, bold: true }, ...(q.hint ? [{ value: `Yordam: ${q.hint}`, size: 19, color: '#62748b' }] : [])]
      : [{ value: `${i + 1}. ${q.answers.join(' / ')}`, bold: true, color: '#2162e8' }, { value: q.explanation }], kind === 'exercises'));
  }
  pages.forEach((canvas, i) => {
    c = canvas.getContext('2d')!; c.strokeStyle = '#dfe6f0'; c.beginPath(); c.moveTo(64, 1600); c.lineTo(1136, 1600); c.stroke();
    text('O‘rganish → mashq → tekshirish', 64, 1640, 19, '#62748b');
    text(`${i + 1} / ${pages.length}`, 1060, 1640, 19, '#62748b');
  });
  return pagesPdf(pages);
}
