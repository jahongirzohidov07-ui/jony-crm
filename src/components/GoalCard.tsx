import { StudentLoadError } from "./StudentLoading";
import { StudentIcon } from "./StudentIcon";
import { useEffect, useState } from "react";
import { Pencil, Clock3 } from "lucide-react";
import { api } from "../lib/api";

type Plan = { daily_hours: number; target_hours: number | null; remaining_hours: number | null; target_cefr: string | null; days: number | null };
type Goal = { target: number | null; band: number; level: string; done: boolean; percent: number | null; study_plan: Plan };
const BANDS = [4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9];
const fmtBand = (b: number) => b.toFixed(1);
const fmt = (n: number) => n.toLocaleString("uz-UZ");
function duration(days: number) {
  const months = Math.floor(days / 30), rest = days % 30;
  return [months ? `${months} oy` : "", rest ? `${rest} kun` : ""].filter(Boolean).join(" ") || "0 kun";
}

export function GoalCard() {
  const [g, setG] = useState<Goal | null>(null);
  const [reload, setReload] = useState(0);
  const [loadError, setLoadError] = useState("");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [band, setBand] = useState(6.5);
  const [daily, setDaily] = useState(2);
  useEffect(() => { let active = true; setLoadError("");
    api.fresh<Goal>("/student/goal").then(r => { if (active) { setG(r); setBand(r.target || 6.5); setDaily(r.study_plan?.daily_hours || 2); } }).catch(e => { if (active) setLoadError(e instanceof Error ? e.message : "Maqsad yuklanmadi"); });
    return () => { active = false; };
  }, [reload]);
  async function save() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      const r = await api.post<Goal>("/student/goal", { target: band, daily_hours: daily });
      setG(r); setEditing(false);
    } catch (e) { setError(e instanceof Error ? e.message : "Saqlanmadi. Qayta urinib ko‘ring."); }
    finally { setBusy(false); }
  }
  function edit() { setBand(g?.target || 6.5); setDaily(g?.study_plan?.daily_hours || 2); setError(""); setEditing(true); }
  if (!g && loadError) return <StudentLoadError message={loadError} onRetry={() => { setLoadError(""); setReload(n => n + 1); }} />;
  if (!g) return <div className="student-panel rounded-2xl p-4 text-sm text-slate-600" role="status">Maqsad rejasi yuklanmoqda…</div>;
  const p = g.study_plan;
  return <section className="student-panel student-pattern rounded-2xl p-4" aria-label="IELTS tayyorgarlik rejasi">
    <div className="flex items-center gap-2">
      <StudentIcon name="mission" size={38} />
      <h2 className="text-[15px] font-bold text-slate-900">{editing || !g.target ? "Maqsad va kunlik reja" : `Maqsad: IELTS ${fmtBand(g.target)}`}</h2>
      {!editing && g.target && <button onClick={edit} aria-label="Maqsad va kunlik vaqtni o‘zgartirish" className="ml-auto min-h-11 min-w-11 rounded-xl text-blue-700 bg-blue-50 flex items-center justify-center"><Pencil size={18} /></button>}
    </div>
    {editing || !g.target ? <>
      <p className="text-sm text-slate-600 mt-3">IELTS maqsadini tanlang</p>
      <div className="flex flex-wrap gap-2 mt-2">{BANDS.map(b => <button key={b} onClick={() => setBand(b)} disabled={busy} aria-pressed={band === b} className={`min-h-11 min-w-11 rounded-xl px-3 text-sm font-bold border ${band === b ? "bg-blue-600 text-white border-blue-600" : "bg-blue-50 text-blue-800 border-blue-100"}`}>{fmtBand(b)}</button>)}</div>
      <p className="text-sm font-semibold text-slate-700 mt-4">Kuniga qancha vaqt ajratasiz?</p>
      <div className="grid grid-cols-5 gap-1.5 mt-2">{[1, 2, 3, 4, 5].map(h => <button key={h} onClick={() => setDaily(h)} disabled={busy} aria-pressed={daily === h} className={`min-h-11 rounded-xl text-xs font-bold border ${daily === h ? "bg-blue-600 text-white border-blue-600" : "bg-blue-50 text-blue-800 border-blue-100"}`}>{h} soat</button>)}</div>
      <p className="text-xs text-slate-600 mt-2">Dars va mustaqil o‘qish vaqtini birga hisoblang. Reja har kuni o‘qishga asoslanadi.</p>
      {error && <p role="alert" className="text-sm text-red-700 mt-2">{error}</p>}
      <div className="flex gap-2 mt-4"><button disabled={busy} onClick={save} className="min-h-11 rounded-xl bg-blue-600 text-white px-5 font-bold text-sm">{busy ? "Saqlanmoqda…" : "Rejani saqlash"}</button>{g.target && <button disabled={busy} onClick={() => setEditing(false)} className="min-h-11 px-4 rounded-xl text-slate-600 text-sm">Bekor</button>}</div>
    </> : <>
      <div className="flex items-center gap-2 mt-3 text-xs font-bold"><span className="text-slate-600">~{fmtBand(g.band)}</span><div className="flex-1 h-2 rounded-full bg-blue-100 overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-500 to-violet-500" style={{ width: `${g.percent ?? 0}%` }} /></div><span className="text-blue-700">{fmtBand(g.target)}</span></div>
      <p className="text-xs text-slate-600 mt-2">Hozirgi taxminiy IELTS darajasi: ~{fmtBand(g.band)}</p>
      {g.done ? <p className="mt-3 text-sm font-bold text-emerald-700">Ilovadagi taxminiy darajangiz maqsadga yetdi. Natijani sinov imtihoni bilan tekshiring.</p> : p?.days != null ? <div className="mt-3 rounded-xl bg-blue-50 border border-blue-100 p-3">
        <p className="text-xs text-blue-800 flex items-center gap-1.5"><Clock3 size={16} /> Taxminiy tayyorgarlik muddati</p>
        <p className="text-2xl font-extrabold text-blue-700 mt-1">{duration(p.days)}</p>
        <p className="text-sm text-slate-700 mt-1">Kuniga <b>{p.daily_hours} soat</b> · taxminan <b>{fmt(p.remaining_hours!)} soat</b> qoldi</p>
      </div> : <p className="mt-3 text-sm text-slate-600">IELTS 8.5–9.0 uchun soat me’yori hali belgilanmagan. Shaxsiy reja uchun ustozingiz bilan maslahatlashing.</p>}
      <details className="mt-3 text-xs text-slate-600"><summary className="cursor-pointer min-h-11 flex items-center text-blue-700 font-semibold">Hisob qanday qilinadi?</summary>
        <p>Noldan boshlab jami: A1 — 105, A2 — 330, B1 — 780, B1+ — 1080, B2 — 1380, C1 — 2000 soat.</p>
        <p className="mt-2">IELTS 6.5 — 1380, IELTS 8.0 — 2000 soat. Oraliq ballar uchun soatlar mutanosib hisoblanadi. Hozirgi ko‘nikmalar bahosi asosida qolgan soatlar taxmin qilinadi va kunlik vaqtga bo‘linadi. Bu o‘lchangan o‘qish vaqti emas.</p>
        <p className="mt-2">XP muddatga aylantirilmaydi. Oy 30 kun deb olinadi. Bu Jony Academy tayyorgarlik rejasi, IELTS natijasi kafolati emas.</p>
      </details>
    </>}
  </section>;
}
