import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { rewardPracticePlan, rewardVocabHref } from "../lib/studentRewardPractice";
import { useLearningLanguage } from "../lib/lang";

export type RewardSource = {
  id: string; title: string; description: string; coins: number | null;
  have: number | null; target: number | null; unit: string;
  status: "in_progress" | "eligible" | "awarded" | "untracked" | "manual_review";
  award_mode: "automatic" | "staff"; href: string | null; action_label: string | null;
};
export type RewardPathData = { student_id: number; sources: RewardSource[]; note: string };
export function sourcesForLanguage(sources: RewardSource[], language: string) {
  return sources.filter(s => language === "en" || !s.id.startsWith("wordbank:"));
}
export const REWARD_UNITS: Record<string,string> = {xp:"XP", days:"kun", correct_answers:"ta to‘g‘ri javob", topics:"mavzu", lessons:"dars", exams:"imtihon", verified_words:"tasdiqlangan so‘z"};
const STATUS: Record<RewardSource["status"],string> = {
  in_progress: "Shartni bajarish davom etmoqda",
  eligible: "Shart bajarilgan · coin berilgani hali tasdiqlanmagan",
  awarded: "Coin berilgan · tarixda qayd etilgan",
  untracked: "Berilganini coin tarixidan tekshiring",
  manual_review: "Xodim belgilaydi · so‘rov yuborilmagan",
};
function VocabLauncher({source, language}: {source: RewardSource; language: string}) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const active = useRef(true);
  const pending = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  async function launch() {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      const href = await rewardVocabHref(source, language, path => api.fresh(path));
      if (active.current) navigate(href);
    } catch (e) {
      if (active.current) setError(e instanceof Error ? e.message : "Mashqni ochib bo‘lmadi. Qayta urinib ko‘ring.");
    } finally {
      pending.current = false;
      if (active.current) setBusy(false);
    }
  }
  return <div className="w-full">
    <button type="button" disabled={busy} aria-busy={busy} onClick={launch}
      className="inline-flex min-h-11 items-center rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60">
      {busy ? "Mashq tayyorlanmoqda…" : error ? "Qayta urinish" : "Lug‘at mashqini boshlash"}
    </button>
    {busy && <p role="status" className="mt-2 text-sm">Mos lug‘at bo‘limi tanlanmoqda…</p>}
    {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
  </div>;
}
export function SourceCard({source:s,onHistory,language = "en"}: {source:RewardSource;onHistory:()=>void;language?:string}) {
  const canPractice=s.status === "in_progress" || s.status === "eligible";
  const practice=rewardPracticePlan(s, language);
  const progress=s.target !== null && s.have !== null && s.target>0;
  return <article className="rounded-xl border border-slate-200 p-3">
    <h3 className="font-semibold text-slate-900">{s.title}{s.coins !== null ? ` · ${s.coins} coin` : ""}</h3>
    <p className="mt-1 text-sm text-slate-600">{s.description}</p>
    {progress && <p className="mt-2 text-sm font-semibold text-indigo-700">{s.have} / {s.target} {REWARD_UNITS[s.unit] || ""}{Math.max(0,s.target!-s.have!)>0 ? ` · yana ${Math.max(0,s.target!-s.have!)} ${REWARD_UNITS[s.unit] || ""}` : ""}</p>}
    <p className="mt-2 text-xs font-semibold text-slate-700">{STATUS[s.status]}</p>
    <p className="mt-1 text-xs text-slate-500">{s.award_mode === "automatic" ? "Tizim qoidasi bo‘yicha avtomatik hisoblanadi." : "Miqdor va berish qarorini vakolatli xodim belgilaydi."}</p>
    <div className="mt-2 flex flex-wrap gap-2">
      {practice?.kind === "link" && <Link to={practice.href} className="inline-flex min-h-11 items-center rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white">{practice.label}</Link>}
      {practice?.kind === "vocab" && <VocabLauncher key={`${s.id}:${language}:${s.status}`} source={s} language={language}/>}
      {practice?.kind === "unavailable" && <p className="text-sm text-slate-600">{practice.message}</p>}
      {s.id.startsWith("league:") && canPractice && <Link to="/student/leagues" className="inline-flex min-h-11 items-center px-2 text-sm font-semibold underline">Liga shartlari</Link>}
      {(s.status === "awarded" || s.status === "untracked" || s.status === "eligible") && <button type="button" onClick={onHistory} className="min-h-11 px-2 text-sm font-semibold underline">Coin tarixini ko‘rish</button>}
    </div>
  </article>;
}
export default function StudentRewardPath({studentId,onHistory}: {studentId:number;onHistory:()=>void}) {
  const language = useLearningLanguage();
  const [data,setData]=useState<RewardPathData|null>(null);
  const [error,setError]=useState(false);
  const [retry,setRetry]=useState(0);
  useEffect(()=>{
    let active=true;setData(null);setError(false);
    api.fresh<RewardPathData>("/student/reward-path").then(value=>{
      if(!active)return;
      if(value.student_id !== studentId) {setError(true);return;}
      setData(value);
    }).catch(()=>{if(active)setError(true);});
    return ()=>{active=false;};
  },[studentId,retry]);
  const sources=sourcesForLanguage(data?.sources ?? [], language);
  const pending=sources.filter(s=>s.status==="eligible" || s.status==="in_progress") ?? [];
  // Show one next milestone per earning route, not every later league/day.
  const seen=new Set<string>();
  const next=pending.filter(s=>{const family=s.id.split(":")[0];if(seen.has(family))return false;seen.add(family);return true;}).slice(0,3);
  const other=sources.filter(s=>!next.includes(s));
  return <section aria-label="Sovringa keyingi qadam" className="student-panel mt-4 rounded-2xl bg-white p-4 text-slate-900">
    <h2 className="text-lg font-bold">Sovringa keyingi qadam</h2>
    <p className="mt-1 text-sm text-slate-600">Mos shartni tanlang va mashqni boshlang. Har bir mashq alohida coin bermaydi; mukofot quyidagi shartlar bajarilganda hisoblanadi.</p>
    {error ? <div role="alert" className="mt-3 text-sm">Coin olish yo‘lini yuklab bo‘lmadi.<button type="button" onClick={()=>setRetry(n=>n+1)} className="block min-h-11 font-semibold underline">Qayta yuklash</button></div> : !data ? <p role="status" className="mt-3 text-sm">Coin olish shartlari yuklanmoqda…</p> : <>
      <div className="mt-3 space-y-3">{next.map(s=><SourceCard key={s.id} source={s} onHistory={onHistory} language={language}/>)}</div>
      {!next.length && <p className="mt-3 text-sm">Hozir yangi avtomatik mukofotga olib boradigan shart ko‘rsatilmagan. Hisoblangan coinlarni tarixdan tekshiring.</p>}
      {!!other.length && <details className="mt-3"><summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold">Boshqa shartlar va berilgan coinlar</summary><div className="space-y-3">{other.map(s=><SourceCard key={s.id} source={s} onHistory={onHistory} language={language}/>)}</div></details>}
      <p className="mt-3 text-xs text-slate-500">Coin berilgani faqat hisob yozuvi bilan tasdiqlanadi. Shart bajarilgani hali coin tushganini anglatmaydi. Bu sahifani ko‘rish coin sarflamaydi va ariza yubormaydi.</p>
    </>}
  </section>;
}
