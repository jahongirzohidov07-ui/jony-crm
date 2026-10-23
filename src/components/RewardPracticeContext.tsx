import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, getToken, type MyCoins } from "../lib/api";
import { useLearningLanguage } from "../lib/lang";
import { readRewardGoal, resolveRewardGoal } from "../lib/studentRewardGoal";
import { REWARD_PRACTICE_UPDATED } from "../lib/rewardPracticeEvents";
import { REWARD_UNITS, type RewardPathData, type RewardSource } from "./StudentRewardPath";

type Snapshot = { coins: MyCoins; source: RewardSource | null };
export function validRewardSource(value: string | null): value is string {
  return !!value && /^(league|streak|wordbank|daily-six):[a-zA-Z0-9_-]{1,64}$/.test(value);
}
export default function RewardPracticeContext() {
  const {pathname, search} = useLocation();
  const language = useLearningLanguage();
  const source = new URLSearchParams(search).get("reward_source");
  if (!validRewardSource(source) || !/^\/student\/(course-practice|games\/|words\/practice|russian)/.test(pathname)) return null;
  if (language !== "en" && source.startsWith("wordbank:")) return null;
  return <LiveContext key={`${language}:${source}`} sourceId={source}/>;
}
function LiveContext({sourceId}: {sourceId: string}) {
  const [snapshot,setSnapshot] = useState<Snapshot|null>(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState(false);
  const [version,setVersion] = useState(0);
  const baseline = useRef<number|null>(null);
  useEffect(()=>{
    let active = true, generation = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let identity = getToken();
    const refresh = async () => {
      const request = ++generation;
      const requestIdentity = getToken();
      if (identity !== requestIdentity) {
        identity = requestIdentity; baseline.current = null; setSnapshot(null);
      }
      setLoading(true); setError(false);
      try {
        const [coins,path] = await Promise.all([
          api.fresh<MyCoins>("/me/coins"), api.fresh<RewardPathData>("/student/reward-path"),
        ]);
        if (!active || request !== generation) return;
        if (requestIdentity !== getToken()) {
          baseline.current = null; setSnapshot(null); setLoading(false); setError(true); return;
        }
        if (coins.student_id !== path.student_id) throw new Error("Hisob mos emas");
        const source = path.sources.find(s=>s.id===sourceId) || null;
        if (baseline.current === null && source?.have !== null && source?.have !== undefined) baseline.current = source.have;
        setSnapshot({coins,source}); setLoading(false);
      } catch {
        if (active && request === generation) {
          if (requestIdentity !== getToken()) {baseline.current = null; setSnapshot(null);}
          setError(true); setLoading(false);
        }
      }
    };
    const updated = () => {
      if (identity !== getToken()) {
        ++generation; baseline.current = null; setSnapshot(null); setLoading(true);
      }
      clearTimeout(timer); timer = setTimeout(()=>void refresh(),300);
    };
    const accountChanged = (event: StorageEvent) => { if (event.key === "jony_crm_token" || event.key === null) updated(); };
    const focused = () => { if(document.visibilityState !== "hidden") updated(); };
    void refresh();
    window.addEventListener(REWARD_PRACTICE_UPDATED,updated);
    window.addEventListener("focus",focused);
    window.addEventListener("storage",accountChanged);
    document.addEventListener("visibilitychange",focused);
    return()=>{active=false;clearTimeout(timer);window.removeEventListener(REWARD_PRACTICE_UPDATED,updated);window.removeEventListener("focus",focused);window.removeEventListener("storage",accountChanged);document.removeEventListener("visibilitychange",focused);};
  },[sourceId,version]);
  return <aside aria-label="Mashqdagi sovrin maqsadi" className="mx-auto mt-3 max-w-xl rounded-2xl border border-indigo-200 bg-white p-4 text-slate-900">
    <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-bold">Sovringa keyingi qadam</h2><Link to="/student/shop" className="inline-flex min-h-11 items-center text-sm font-semibold text-indigo-700 underline">Sovrinimga qaytish</Link></div>
    {error ? <p role="alert" className="text-sm">Maqsad hisobini yangilab bo‘lmadi. Mashq javobingizning natijasi pastda ko‘rsatiladi.<button onClick={()=>setVersion(n=>n+1)} className="block min-h-11 font-semibold underline">Qayta yangilash</button></p> : snapshot ? <RewardPracticeProgress snapshot={snapshot} baseline={baseline.current}/> : <p role="status" className="text-sm">Maqsadingiz yuklanmoqda…</p>}
    {snapshot && !error && <button disabled={loading} onClick={()=>setVersion(n=>n+1)} className="mt-1 min-h-11 text-xs font-semibold text-indigo-700 underline disabled:opacity-50">{loading?"Hisob yangilanmoqda…":"Hisobni yangilash"}</button>}
  </aside>;
}
export function RewardPracticeProgress({snapshot,baseline}: {snapshot:Snapshot;baseline:number|null}) {
  const {coins,source} = snapshot;
  let selection: number|null = null;
  try { selection = readRewardGoal(localStorage,coins.student_id); } catch { /* storage unavailable */ }
  const {reward,left} = resolveRewardGoal(coins.rewards,selection,coins.available);
  const unit = source ? REWARD_UNITS[source.unit] || "" : "";
  return <div className="space-y-2 text-sm">
    {reward && <p className="break-words"><strong>{reward.name}</strong> · {Math.max(0,coins.available)} / {reward.cost} coin · {left>0?`yana ${left} coin kerak`:"coin yetarli"}{!reward.in_stock?" · sovrin hozir tugagan":""}</p>}
    {!source ? <p>Bu mukofot sharti endi mavjud emas. Sovrinlar sahifasidan boshqa qadam tanlang.</p> : <>
      <p className="font-semibold text-indigo-800">{source.title}</p>
      {source.have !== null && source.target !== null && <p aria-live="polite">{baseline !== null && baseline !== source.have ? `${baseline} → `:""}{source.have} / {source.target} {unit}{source.target>source.have?` · yana ${source.target-source.have} ${unit}`:" · chegara bajarilgan"}</p>}
      <p className="text-xs text-slate-600">{source.status === "awarded" ? "Coin berilgani hisob tarixida tasdiqlangan." : source.status === "eligible" ? "Shart bajarilgan. Coin berilgani hali tasdiqlanmagan." : source.status === "untracked" ? "Mukofot to‘lovini coin tarixidan tekshiring." : "Mashq natijasi serverda tekshiriladi. Har javob coin bermaydi; XP faqat amaldagi qoida bo‘yicha beriladi."}</p>
    </>}
  </div>;
}
