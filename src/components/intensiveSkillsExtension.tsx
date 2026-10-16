import { useRef, useState } from 'react';
import extension from '../data/intensive-skills-extension.json';
import type { SkillPack } from '../lib/intensive-skills';

export type ExtensionTask = {
  id: string;
  stage: 'first-pass' | 'close-pass' | 'respond';
  type: string;
  prompt: string;
  options: string[];
  teacher: { answer: string; evidence: string[]; guidance: string };
};
type SkillExtension = { before: string; tasks: ExtensionTask[] };
type Homework = {
  week: number; afterLesson: number; minutes: number;
  title: string; text: string; instructions: string; tasks: ExtensionTask[];
};
type ExtensionData = {
  version: number;
  lessons: { lesson: number; reading: SkillExtension; listening: SkillExtension }[];
  homework: Homework[];
};
export const intensiveSkillsExtension = extension as ExtensionData;

const box = 'rounded-2xl border border-slate-200 bg-white p-4 md:p-6';
const button = 'rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800';
const stages = { 'first-pass': '1 · Umumiy mazmun', 'close-pass': '2 · Tafsilot va dalil', respond: '3 · Izohlash' };
const labels: Record<string, string> = {
  gist: 'Asosiy mazmun', sequence: 'Ma’lumotlar tartibi', 'evidence-selection': 'Dalilni tanlash',
  inference: 'Xulosa chiqarish', detail: 'Aniq ma’lumot', comparison: 'Taqqoslash',
  'evidence-limits': 'Dalil chegarasi', matching: 'Moslashtirish', reference: 'Ishorani aniqlash',
  classification: 'Ajratish', correction: 'Xatoni tuzatish', 'cause-effect': 'Sabab va natija',
  'opinion-matching': 'Fikr egasini aniqlash', purpose: 'Maqsad', timeline: 'Vaqt tartibi',
  synthesis: 'Dalillarni birlashtirish', 'source-attribution': 'Manbani aniqlash',
};
function escapeHTML(value: string) {
  return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]!);
}
function keyHTML(task: ExtensionTask, index: number) {
  return '<section><h3>' + (index + 1) + '. ' + escapeHTML(task.prompt) + '</h3><p><b>Javob:</b> ' +
    escapeHTML(task.teacher.answer) + '</p>' + task.teacher.evidence.map(quote => '<blockquote>' + escapeHTML(quote) + '</blockquote>').join('') +
    '<p><b>Tekshirish:</b> ' + escapeHTML(task.teacher.guidance) + '</p></section>';
}

/** A dedicated document avoids printing navigation, hidden keys, or another lesson.
 * All content comes from our JSON; escape it before writing the isolated frame.
 */
function printWorksheet(title: string, instructions: string, text: string, tasks: ExtensionTask[], listening: boolean, teacher: boolean) {
  const frame = document.createElement('iframe');
  frame.title = title + ' — chop etish';
  frame.setAttribute('aria-hidden', 'true');
  frame.style.cssText = 'position:fixed;width:1px;height:1px;left:-10000px;top:0;border:0';
  document.body.appendChild(frame);
  const target = frame.contentWindow;
  if (!target) { frame.remove(); return; }
  const html = '<!doctype html><html lang="uz"><head><meta charset="utf-8"><title>' + escapeHTML(title) +
    '</title><style>@page{size:A4;margin:16mm}body{font:11pt/1.55 Arial,sans-serif;color:#111}h1{font-size:19pt}h2{font-size:15pt}h3{font-size:11pt}section{break-inside:avoid;margin:16px 0}.passage{white-space:pre-line}blockquote{border-left:2px solid #777;padding-left:12px;margin-left:0}.line{height:25px;border-bottom:1px solid #bbb}.key{break-before:page}small{color:#444}</style></head><body><h1>' +
    escapeHTML(title) + '</h1><p>Ism: ____________________ Sana: ______________</p><p>' + escapeHTML(instructions) + '</p>' +
    (!listening ? '<h2>Matn</h2><div class="passage">' + escapeHTML(text) + '</div>' :
      '<p>Audio: ikki tinglash. 1-bosqichdan so‘ng javob kartalari bilan qayta tinglang. Transkript o‘quvchi varag‘iga kiritilmagan.</p>') +
    tasks.map((task, index) => '<section><small>' + escapeHTML(stages[task.stage] + ' · ' + (labels[task.type] || task.type)) +
      '</small><h3>' + (index + 1) + '. ' + escapeHTML(task.prompt) + '</h3>' +
      task.options.map(option => '<p>' + escapeHTML(option) + '</p>').join('') +
      '<div class="line"></div><div class="line"></div><small>Dalil:</small><div class="line"></div></section>').join('') +
    (teacher ? '<div class="key"><h2>Ustoz kaliti — o‘quvchi varag‘idan ajrating</h2>' +
      (listening ? '<h3>Transkript</h3><div class="passage">' + escapeHTML(text) + '</div>' : '') +
      tasks.map(keyHTML).join('') + '</div>' : '') + '</body></html>';
  let cleanupTimer: ReturnType<typeof setTimeout> | undefined;
  const cleanup = () => { if (cleanupTimer) clearTimeout(cleanupTimer); frame.remove(); };
  target.addEventListener('afterprint', cleanup, { once: true });
  frame.onload = () => {
    target.focus();
    target.print();
    // Fallback for browsers that do not emit afterprint on a child frame.
    if (frame.isConnected) cleanupTimer = setTimeout(cleanup, 300_000);
  };
  frame.srcdoc = html;
}

function TeacherKey({ tasks }: { tasks: ExtensionTask[] }) {
  return <details className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
    <summary className="cursor-pointer font-semibold text-amber-950">Ustoz kaliti · mustaqil urinishdan keyin</summary>
    <p className="mt-3 text-sm">Bu o‘qituvchi uchun tekshirish kaliti; avtomatik yoki rasmiy imtihon bali emas. Har topshiriq 0–2: jami {tasks.length * 2} ball.</p>
    <ol className="mt-4 list-decimal space-y-5 pl-5">{tasks.map(task => <li key={task.id}>
      <p className="font-semibold">{task.prompt}</p>
      <p className="mt-2"><strong>Namuna: </strong>{task.teacher.answer}</p>
      <ul className="mt-2 space-y-2">{task.teacher.evidence.map((quote, index) => <li key={index} className="border-l-2 border-amber-300 pl-3 text-sm">“{quote}”</li>)}</ul>
      <p className="mt-2 text-sm text-amber-950">{task.teacher.guidance}</p>
    </li>)}</ol>
  </details>;
}
function Tasks({ tasks }: { tasks: ExtensionTask[] }) {
  return <ol className="mt-4 space-y-5">{tasks.map(task => <li key={task.id} className="rounded-xl border border-slate-200 p-4">
    <p className="text-xs font-bold uppercase tracking-wide text-blue-700">{stages[task.stage]} · {labels[task.type] || task.type}</p>
    <label htmlFor={task.id} className="mt-2 block font-semibold leading-7">{task.prompt}</label>
    {task.options.length > 0 && <ul className="my-3 space-y-2 text-sm leading-6">{task.options.map(option => <li key={option}>{option}</li>)}</ul>}
    <textarea id={task.id} rows={3} className="mt-3 w-full rounded-lg border border-slate-300 p-3 text-sm leading-6" placeholder="Javob va matndan dalil..." />
  </li>)}</ol>;
}
function Worksheet({ title, text, instructions, tasks, listening = false, showText = false }: {
  title: string; text: string; instructions: string; tasks: ExtensionTask[]; listening?: boolean; showText?: boolean;
}) {
  const [closePass, setClosePass] = useState(!listening);
  const [printError, setPrintError] = useState('');
  const content = useRef<HTMLDivElement>(null);
  function print(teacher: boolean) {
    setPrintError('');
    try { printWorksheet(title, instructions, text, tasks, listening, teacher); }
    catch { setPrintError('Chop etish oynasi ochilmadi. Brauzerda chop etish ruxsatini tekshirib qayta urinib ko‘ring.'); }
  }
  return <div ref={content} className={box}>
    <h4 className="text-lg font-bold text-slate-900">{title}</h4>
    <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-700">{instructions}</p>
    <p className="mt-2 text-xs leading-5 text-slate-500">Javoblar shu ochiq varaqda mashq uchun. Sahifa/dars yoki ko‘nikma almashsa saqlanmaydi. Ustoz kalit bilan tekshiradi.</p>
    <div className="mt-4 flex flex-wrap gap-2 print:hidden">
      <button type="button" className={button} onClick={() => print(false)}>O‘quvchi varag‘ini chop etish</button>
      <button type="button" className={button} onClick={() => print(true)}>Ustoz nusxasi + alohida kalit</button>
    </div>
    {printError && <p role="alert" className="mt-2 text-sm text-amber-900">{printError}</p>}
    {showText && <article className="mt-5 rounded-xl bg-slate-50 p-4"><h5 className="font-semibold">Yangi matn · avval mustaqil o‘qing</h5><p className="mt-3 whitespace-pre-line leading-8" lang="en">{text}</p></article>}
    <Tasks tasks={tasks.filter(task => task.stage === 'first-pass')} />
    {listening && <button type="button" className={button + ' mt-4'} aria-expanded={closePass} onClick={() => setClosePass(value => !value)}>
      {closePass ? 'Tafsilot kartalarini yashirish' : 'Ikki tinglashdan keyin tafsilot kartalarini ochish'}
    </button>}
    {closePass && <Tasks tasks={tasks.filter(task => task.stage !== 'first-pass')} />}
    <TeacherKey tasks={tasks} />
  </div>;
}

export default function IntensiveSkillsExtension({ pack, mode }: { pack: SkillPack; mode: 'reading' | 'listening' }) {
  const lesson = intensiveSkillsExtension.lessons.find(item => item.lesson === pack.lesson);
  if (!lesson) return null;
  const skill = lesson[mode];
  return <Worksheet key={pack.lesson + mode} title={mode === 'reading' ? 'Reading · bosqichli chuqur mashq' : 'Listening · bosqichli chuqur mashq'}
    text={pack[mode].text} listening={mode === 'listening'} tasks={skill.tasks}
    instructions={pack.lesson + '-dars · ' + pack[mode].title + '\n' + skill.before + '\nDarsdagi mavjud reading/listening blokida: 2 daqiqa tayyorgarlik, 3 daqiqa umumiy mazmun, 6 daqiqa tafsilot, 4 daqiqa izoh va tekshiruv. Asl uch savol alohida saqlangan.'} />;
}

export function IntensiveWeeklyHomework({ lesson }: { lesson: number }) {
  const homework = intensiveSkillsExtension.homework.find(item => item.afterLesson === lesson);
  if (!homework) return null;
  return <section aria-label="Haftalik mustaqil o‘qish">
    <Worksheet key={homework.week} title={homework.week + '-hafta · ' + homework.title}
      instructions={homework.instructions} text={homework.text} tasks={homework.tasks} showText />
  </section>;
}
