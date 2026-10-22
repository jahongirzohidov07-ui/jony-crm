import { useState } from 'react';
import { api } from '../lib/api';
import { GuessStats, GuessWarningChip } from './PlacementGuessStats';
// 2026-10-22: natijada "Bilmayman" / juda tez javoblar soni (idk, fast) va
// guess_warning bo'lishi mumkin - eski yozuvlarda yo'q, unda yashirin.
type Row={id:number;name:string;phone:string;date:string;result:{score:number;month:number;lesson:number;gaps:string[];idk?:unknown;fast?:unknown;guess_warning?:boolean}};
export default function GermanPlacementResults(){
 const [rows,setRows]=useState<Row[]>([]),[open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function load(){setOpen(true);setBusy(true);setError('');try{const r=await api.fresh<{rows:Row[]}>('/german-placement/results');setRows(r.rows);}catch{setError('Natijalar yuklanmadi. Qayta urinib ko‘ring.');}finally{setBusy(false);}}
 return <div className="mt-3"><button className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700" onClick={load} disabled={busy}>{busy?'Yuklanmoqda…':'Nemis testi natijalari · yangilash'}</button>{open&&<div className="mt-3 space-y-2"><button className="text-sm text-slate-500" onClick={()=>setOpen(false)}>Yopish</button>{error&&<p role="alert">{error}</p>}{!busy&&!error&&!rows.length&&<p className="text-sm">Hali natija yo‘q.</p>}{rows.map(r=><details key={r.id} className="rounded-xl border bg-white p-3 text-sm"><summary className="cursor-pointer font-semibold">{r.name} · {r.result.score}/48 · {r.result.month}-oy, {r.result.lesson}-dars <GuessWarningChip res={r.result} row={r}/></summary><GuessStats res={r.result} row={r} className="mt-2"/><p className="my-2">+{r.phone} · {new Date(r.date).toLocaleString('uz-UZ',{timeZone:'Asia/Tashkent'})}</p><p>Qaytarish: {r.result.gaps.join(', ')||'Asosiy bo‘shliq topilmadi.'}</p><p className="my-2 text-slate-500">Natija lidning izohiga ham yozilgan. Yakuniy guruhni ustoz tasdiqlaydi.</p><a className="text-blue-600 underline" href={`/plans/german?tab=lessons&lesson=${r.result.lesson}`}>Tavsiya darsini ochish</a></details>)}</div>}</div>;
}
