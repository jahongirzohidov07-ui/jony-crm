import { useState } from "react";
import { Target } from "lucide-react";
import type { MyCoins, RewardItem } from "../lib/api";
import { readRewardGoal, resolveRewardGoal, writeRewardGoal } from "../lib/studentRewardGoal";

export default function StudentRewardGoal({ data, onRequest }: { data: MyCoins; onRequest: (reward: RewardItem) => void }) {
  const [selected, setSelected] = useState<number | null>(() => {
    try { return readRewardGoal(localStorage, data.student_id); } catch { return null; }
  });
  const [storageFailed, setStorageFailed] = useState(false);
  const {reward, left, percent, unavailableSelection} = resolveRewardGoal(data.rewards, selected, data.available);
  const choices = data.rewards.filter(r => r.active);
  return <section aria-label="Mening sovrin maqsadim" className="student-panel mt-4 rounded-2xl bg-white p-4 text-slate-900">
    <h2 className="flex items-center gap-2 text-lg font-bold"><Target size={20}/>Mening sovrin maqsadim</h2>
    <p className="mt-1 text-sm text-slate-600">O‘zingiz xohlagan sovrinni tanlang. Tanlash coin sarflamaydi va buyurtma bermaydi.</p>
    {choices.length ? <>
      <label className="mt-3 block text-sm font-semibold" htmlFor="reward-goal">Qaysi sovringa yig‘aman?</label>
      <select id="reward-goal" value={reward?.id ?? ""} onChange={e => {
        const id = Number(e.target.value); setSelected(id);
        try { setStorageFailed(!writeRewardGoal(localStorage, data.student_id, id)); } catch { setStorageFailed(true); }
      }} className="mt-2 min-h-12 w-full min-w-0 rounded-xl border border-slate-300 bg-white p-3 text-sm">
        {!reward && <option value="">Sovrinni tanlang</option>}
        {choices.map(r => <option key={r.id} value={r.id}>{r.name} · {r.cost} coin{!r.in_stock ? " · hozir tugagan" : ""}</option>)}
      </select>
      <p role="status" className="mt-2 text-xs text-slate-500">{storageFailed ? "Tanlov hozir ishlaydi, lekin qurilmaga saqlanmadi. Qayta kirganda yana tanlang." : "Tanlov shu qurilmada, sizning hisobingiz uchun saqlanadi."}</p>
      {unavailableSelection && <p className="mt-2 text-sm text-amber-700">Oldingi tanlagan sovriningiz endi ro‘yxatda yo‘q. Boshqa sovrin tanlang.</p>}
      {reward && <div className="mt-4 rounded-xl bg-indigo-50 p-3">
        <p className="font-bold break-words">{reward.name}</p>
        <p className="mt-1 text-sm">{Math.max(0, data.available)} / {reward.cost} coin · {left > 0 ? `yana ${left} coin kerak` : "coin yetarli"}</p>
        <div role="progressbar" aria-label="Sovrin uchun yig‘ilgan coin" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100} className="mt-2 h-2 overflow-hidden rounded-full bg-indigo-100"><div className="h-full bg-indigo-600" style={{width: `${percent}%`}}/></div>
        {!reward.in_stock ? <p className="mt-3 text-sm text-amber-800">Bu sovrin hozir tugagan. Maqsadingiz saqlanadi; hozir olish uchun boshqa sovrin tanlashingiz mumkin.</p> : left === 0 ? <button type="button" onClick={() => onRequest(reward)} className="mt-3 min-h-11 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Sovrinni olish shartlarini ko‘rish</button> : <p className="mt-3 text-sm text-slate-700">Quyidagi «Sovringa keyingi qadam» bo‘limidan coin olish shartini va mos mashqni oching.</p>}
      </div>}
    </> : <p className="mt-3 text-sm">Hozir tanlash uchun faol sovrin yo‘q. Coinlaringiz hisobingizda saqlanadi.</p>}
  </section>;
}
