import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Wallet, TrendingUp, Target, Trophy, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { formatSom } from "../lib/format";

export type SmmSalary = {
  period: string; full_name: string; branch: string | null; branch_id: number | null;
  fix_salary: number | null; bonus: number; total: number | null; plan: number; fact: number;
  percent: number | null; status: "active" | "no_plan" | "no_branch";
  next_percent: number | null; next_bonus: number | null; next_total: number | null;
  gap: number | null; days_left: number; target_count: number | null;
  next_fixed_count: number | null; next_fixed_salary: number | null; fixed_status: string;
  scale: { min: number; bonus: number; label: string }[];
};

function useSalary() {
  const { user } = useAuth();
  const [state, setState] = useState<{ data: SmmSalary | null; error: boolean }>({ data: null, error: false });
  const [retry, setRetry] = useState(0);
  const identity = `${user?.full_name}:${user?.role}:${user?.branch_id}`;
  useEffect(() => {
    let active = true;
    setState({ data: null, error: false });
    api.get<SmmSalary>("/me/smm-salary").then(data => {
      if (active) setState({ data, error: false });
    }).catch(() => { if (active) setState({ data: null, error: true }); });
    return () => { active = false; };
  }, [identity, retry]);
  return { ...state, reload: () => setRetry(value => value + 1) };
}

function goalText(r: SmmSalary) {
  if (r.status === "no_branch") return "Filial biriktirilgach, bonusga qolgan yo‘l ko‘rinadi.";
  if (r.status === "no_plan") return "Bu oy uchun o‘quvchi soni rejasi kiritilmagan.";
  if (r.gap != null) return `Keyingi bonusgacha yana ${r.gap} ta faol o‘quvchi kerak.`;
  return "Eng yuqori bonus pog‘onasiga yetdingiz!";
}

/** Same placement and visual hierarchy as the administrator's salary coach. */
export function SmmSalaryCardView({ r }: { r: SmmSalary }) {
  const percent = r.percent ?? 0;
  const target = r.next_percent ?? r.scale.at(-1)?.min ?? 100;
  const progress = Math.min(100, Math.max(0, percent / target * 100));
  return (
    <section aria-label="Oylik va keyingi bonus" className="mb-5 rounded-2xl bg-gradient-to-br from-brand-600 via-brand-700 to-indigo-700 p-5 text-white shadow-lg">
      <div className="flex flex-wrap items-start gap-4">
        <div className="min-w-0 flex-1 basis-64">
          <p className="flex items-center gap-1.5 text-sm text-white/80"><Wallet size={15} /> Shu oy oylingiz (hozirgi natija bilan)</p>
          <p className="mt-1 text-3xl font-bold tabular-nums md:text-4xl">{r.total == null ? "Hisob aniqlashtirilmoqda" : formatSom(r.total)}</p>
          <p className="mt-1 text-xs text-white/75">Fiks {r.fix_salary == null ? "Pog‘ona belgilanmagan" : formatSom(r.fix_salary)} · O‘quvchi rejasi bonusi {formatSom(r.bonus)}</p>
          <p className="mt-2 text-xs text-white/75">{r.full_name} · {r.branch ?? "Filial biriktirilmagan"} · {r.period}</p>
        </div>
        {r.next_total != null && (
          <div className="rounded-xl bg-white/15 px-4 py-3">
            <p className="text-xs text-white/80">Maqsadga yetsangiz</p>
            <p className="text-2xl font-bold tabular-nums text-amber-300">{formatSom(r.next_total)}</p>
            <p className="text-xs text-white/80">+{formatSom(r.next_total - (r.total ?? 0))} ko‘proq</p>
          </div>
        )}
      </div>
      {r.status === "active" ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl bg-white/10 p-3.5">
            <div className="mb-2 flex items-center justify-between gap-2 text-sm">
              <span className="flex items-center gap-1.5"><TrendingUp size={14} /> Filial o‘quvchi soni rejasi</span>
              <b className="tabular-nums">{percent}%</b>
            </div>
            <div role="progressbar" aria-label="Keyingi bonus pog‘onasiga erishish" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100} className="h-2.5 overflow-hidden rounded-full bg-white/20">
              <div className="h-full rounded-full bg-white transition-[width] duration-700 motion-reduce:transition-none" style={{ width: `${progress}%` }} />
            </div>
            <p className="mt-2 text-xs leading-5 text-white/85">Reja: {r.plan} ta o‘quvchi<br />Hozir: {r.fact} ta faol o‘quvchi</p>
          </div>
          <div className="rounded-xl bg-white/10 p-3.5">
            <p className="mb-2 flex items-center gap-1.5 text-sm"><Target size={14} /> Keyingi bonusgacha</p>
            {r.gap != null ? <>
              <p className="text-xl font-bold tabular-nums text-amber-300">{r.gap} ta o‘quvchi</p>
              <p className="mt-1 text-xs leading-5 text-white/90">{r.next_percent}% ga yetganda bonus <b>{formatSom(r.next_bonus ?? 0)}</b> bo‘ladi.</p>
              <p className="mt-1 text-xs text-white/80">Maqsad: jami {r.target_count} ta faol o‘quvchi.</p>
            </> : <p className="text-sm leading-6 text-amber-200">{goalText(r)} Oy oxirigacha natijani saqlang.</p>}
          </div>
        </div>
      ) : <p className="mt-4 rounded-xl bg-white/10 p-4 text-sm leading-6">{goalText(r)} Fiks faol o‘quvchilar soni bo‘yicha hisoblanadi.</p>}
      {r.next_fixed_count != null && <p className="mt-3 text-xs text-white/90">Fiks oshishigacha {r.next_fixed_count - r.fact} ta o‘quvchi: {r.next_fixed_count} taga yetganda fiks {formatSom(r.next_fixed_salary ?? 0)} bo‘ladi.</p>}
      {r.fixed_status === "unconfigured" && <p className="mt-3 text-sm text-amber-200">Fiks pog‘onasi aniqlashtirilishi kerak. Jami oylik hozircha ko‘rsatilmaydi.</p>}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-white/80">
        <p className="flex items-center gap-1.5"><Trophy size={13} className="text-amber-300" /> Oy tugashiga {r.days_left} kun qoldi.</p>
        <Link to="/marketing" className="font-medium underline underline-offset-4 hover:text-white">Reja va bonuslar</Link>
      </div>
      <p className="mt-2 text-[11px] text-white/70">Hisob: fiks + o‘quvchi rejasi bonusi. Alohida bonus va ushlab qolishlar yakuniy hisob-kitobda ko‘riladi.</p>
    </section>
  );
}

export function SmmSalaryCard() {
  const { data, error, reload } = useSalary();
  if (error) return <div role="status" className="mb-5 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">Oylik ma’lumotlari yuklanmadi. <button onClick={reload} className="ml-2 text-brand-600 underline">Qayta yuklash</button></div>;
  return data ? <SmmSalaryCardView r={data} /> : null;
}

export function SmmSalaryFloat() {
  const { data: r } = useSalary();
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  if (!r || pathname === "/") return null;
  return (
    <div className="fixed bottom-4 right-4 z-40 max-w-[calc(100vw-2rem)]">
      {open && <div id="smm-salary-details" className="mb-2 w-72 max-w-full rounded-xl bg-white p-3 text-sm shadow-xl ring-1 ring-slate-200">
        <p className="text-xs text-slate-500">{r.branch} · Shu oy oylingiz</p>
        <p className="text-xl font-bold tabular-nums text-slate-900">{r.total == null ? "Hisob aniqlashtirilmoqda" : formatSom(r.total)}</p>
        <p className="mt-1 text-xs text-slate-500">Fiks {r.fix_salary == null ? "Pog‘ona belgilanmagan" : formatSom(r.fix_salary)} + bonus {formatSom(r.bonus)}</p>
        {r.next_total != null && <p className="mt-2 text-xs text-emerald-700">Maqsadga yetsangiz: <b>{formatSom(r.next_total)}</b></p>}
        <p className="mt-2 text-xs leading-5 text-slate-600">{goalText(r)}</p>
        <Link to="/" className="mt-2 block text-xs text-brand-600 hover:underline">Batafsil — Dashboard</Link>
      </div>}
      <button onClick={() => setOpen(value => !value)} aria-expanded={open} aria-controls={open ? "smm-salary-details" : undefined} aria-label="Oylingiz va keyingi bonus" className="flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-600 to-indigo-600 px-3.5 py-2 text-white shadow-lg ring-2 ring-white hover:brightness-110">
        <Wallet size={16} /><span className="text-sm font-semibold tabular-nums">{r.total == null ? "Hisob aniqlashtirilmoqda" : formatSom(r.total)}</span>
        <span className="hidden border-l border-white/30 pl-2 text-xs sm:inline">{r.next_percent != null ? `Keyingi maqsad: ${r.next_percent}%` : r.status === "active" ? "Barcha bonuslar sizda!" : "Reja kutilmoqda"}</span>
        {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>
    </div>
  );
}
