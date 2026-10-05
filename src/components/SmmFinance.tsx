import { Wallet, Users, Trophy, CheckCircle2 } from "lucide-react";
import { SmmSalaryCardView, useSalary, type SmmSalary } from "./SmmSalaryCoach";
import { formatSom } from "../lib/format";

export function SmmFinanceView({ r }: { r: SmmSalary }) {
  const steps = [...r.scale].sort((a, b) => a.min - b.min);
  return <div className="mx-auto max-w-6xl space-y-5 pb-8">
    <header>
      <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900"><Wallet className="text-brand-600" /> Moliya</h1>
      <p className="mt-1 text-sm text-slate-500">Oyligingiz qanday hisoblanadi: fiks, bonuslar va keyingi maqsadlar.</p>
    </header>
    <SmmSalaryCardView r={r} />
    <section className="rounded-2xl border border-brand-100 bg-brand-50 p-5">
      <h2 className="font-semibold text-slate-900">Jami oylik = fiks + reja bonusi</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">Fiks filialdagi faol o‘quvchilar soniga qarab belgilanadi. Bonus uchun faol o‘quvchilar soni shu oyning o‘quvchi soni rejasiga bo‘linadi va 100 ga ko‘paytiriladi.</p>
      {r.status === "active" && <p className="mt-3 font-semibold text-brand-700">{r.fact} ÷ {r.plan} × 100 = {r.percent}%</p>}
      {r.total != null && <p className="mt-2 font-semibold text-slate-900">{formatSom(r.fix_salary ?? 0)} + {formatSom(r.bonus)} = {formatSom(r.total)}</p>}
      <p className="mt-2 text-xs leading-5 text-slate-500">Bu hozirgi natija bo‘yicha hisoblangan summa, to‘langan oylik emas. Alohida qo‘lda berilgan bonuslar va ushlab qolishlar yakuniy hisob-kitobda hisobga olinadi.</p>
    </section>
    <div className="grid items-start gap-5 lg:grid-cols-2">
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 p-5"><h2 className="flex items-center gap-2 font-semibold text-slate-900"><Users size={19} className="text-brand-600" /> Fiks oylik pog‘onalari</h2><p className="mt-1 text-sm text-slate-500">Filialdagi faol o‘quvchilar soni bo‘yicha.</p></div>
        <table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th scope="col" className="px-5 py-3">O‘quvchilar</th><th scope="col" className="px-5 py-3 text-right">Fiks oylik</th></tr></thead>
          <tbody>{r.fixed_scale.map(tier => {
            const current = r.branch_id != null && r.fact >= tier.min && (tier.max == null || r.fact <= tier.max);
            return <tr key={tier.min} className={`border-t border-slate-100 ${current ? "bg-brand-50 text-brand-800" : "text-slate-700"}`}>
              <td className="px-5 py-4">{tier.max == null ? `${tier.min}+` : `${tier.min}–${tier.max}`} ta{current && <span className="mt-1 flex items-center gap-1 text-xs font-medium"><CheckCircle2 size={13} /> Sizning pog‘onangiz</span>}</td>
              <td className="px-5 py-4 text-right font-semibold tabular-nums">{formatSom(tier.salary)}</td>
            </tr>;
          })}</tbody>
        </table>
      </section>
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 p-5"><h2 className="flex items-center gap-2 font-semibold text-slate-900"><Trophy size={19} className="text-amber-500" /> Barcha reja bonuslari</h2><p className="mt-1 text-sm leading-5 text-slate-500">Bonuslar qo‘shilmaydi. Erishilgan eng yuqori pog‘onaning bitta bonusi olinadi.</p></div>
        <table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th scope="col" className="px-5 py-3">Reja bajarilishi</th><th scope="col" className="px-5 py-3 text-right">Bonus</th></tr></thead>
          <tbody>
            <tr className={`border-t border-slate-100 ${r.status === "active" && r.bonus === 0 ? "bg-amber-50" : ""}`}><td className="px-5 py-4">{steps[0]?.min ?? 80}% dan kam</td><td className="px-5 py-4 text-right font-semibold">0 so‘m</td></tr>
            {steps.map((tier, index) => {
              const current = r.status === "active" && r.bonus === tier.bonus;
              const target = r.plan > 0 ? Math.ceil(r.plan * tier.min / 100) : null;
              const next = steps[index + 1];
              return <tr key={tier.min} className={`border-t border-slate-100 ${current ? "bg-emerald-50 text-emerald-800" : "text-slate-700"}`}>
                <td className="px-5 py-4"><span>{next ? `${tier.min}% dan ${next.min}% gacha` : `${tier.min}% va yuqori`}</span>
                  {target != null && <span className="mt-1 block text-xs text-slate-500">Kamida {target} ta faol o‘quvchi</span>}
                  {current && <span className="mt-1 flex items-center gap-1 text-xs font-medium"><CheckCircle2 size={13} /> Hozirgi bonusingiz</span>}</td>
                <td className="px-5 py-4 text-right font-semibold tabular-nums">{formatSom(tier.bonus)}</td>
              </tr>;
            })}
          </tbody>
        </table>
        <p className="border-t border-slate-100 px-5 py-3 text-xs leading-5 text-slate-500">Oraliqning yuqori chegarasiga yetganda keyingi pog‘ona boshlanadi. Reja kiritilmagan bo‘lsa, bonus hali hisoblanmaydi.</p>
      </section>
    </div>
  </div>;
}

export function SmmFinance() {
  const { data, error, reload } = useSalary();
  if (error) return <div role="alert" className="rounded-xl border bg-white p-5">Moliya ma’lumotlari yuklanmadi. <button onClick={reload} className="ml-2 text-brand-600 underline">Qayta yuklash</button></div>;
  if (!data) return <p role="status" className="p-5 text-slate-500">Moliya ma’lumotlari yuklanmoqda…</p>;
  return <SmmFinanceView r={data} />;
}
