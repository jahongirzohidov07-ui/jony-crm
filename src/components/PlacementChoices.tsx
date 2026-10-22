// Kirish testlaridagi javob variantlari (nemis / rus, 2026-10-22).
// Haqiqiy variantlar (4 yoki 5 ta, server bergan tartibda) A, B, C...
// harflari bilan; "Bilmayman" esa HAR DOIM oxirida, kulrang va alohida —
// haqiqiy variant bilan adashtirilmaydi, lekin o'lchami bir xil. Hammasi
// bitta radio guruh: klaviatura bilan ham tanlanadi. "Bilmayman" = -1.

const row = 'flex min-w-0 cursor-pointer items-center gap-3 rounded-xl border p-3 sm:p-4';

export default function PlacementChoices({ name, options, value, onChange, idk, lang, disabled = false }: {
  name: string; options: string[]; value: number | undefined; onChange: (choice: number) => void;
  idk: boolean; lang: string; disabled?: boolean;
}) {
  return <div className="space-y-2 sm:space-y-3">
    {options.map((option, i) => <label key={`${name}-${i}`}
      className={`${row} ${value === i ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:bg-slate-50'}`}>
      <input type="radio" name={name} className="shrink-0" checked={value === i} disabled={disabled} onChange={() => onChange(i)} />
      <span className="w-5 shrink-0 text-sm font-semibold text-slate-400" aria-hidden="true">{String.fromCharCode(65 + i)}.</span>
      <span lang={lang} className="min-w-0 break-words">{option}</span>
    </label>)}
    {idk && <label className={`${row} !mt-4 border-dashed text-slate-600 ${value === -1 ? 'border-slate-500 bg-slate-100' : 'border-slate-300 bg-slate-50 hover:bg-slate-100'}`}>
      <input type="radio" name={name} className="shrink-0" checked={value === -1} disabled={disabled} onChange={() => onChange(-1)} />
      <span className="w-5 shrink-0 text-sm font-semibold text-slate-400" aria-hidden="true">?</span>
      <span lang="uz" className="min-w-0 font-semibold">Bilmayman</span>
    </label>}
  </div>;
}
