import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Wallet, Target, TrendingUp, Trophy } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { formatSom } from "../lib/format";

export type ExaminerSalaryData = {
  period: string; salary: number; min: number; max: number; unit: number;
  points: number; base_points: number; penalty_points: number; adjustment_points: number;
  exam_count: number; students_total: number; volunteer?: boolean; volunteer_hint?: string;
  goal: { status: "active" | "maximum" | "no_exams" | "volunteer";
    next_salary: number | null; gap_points: number | null; target_points: number | null;
    progress: number; days_left: number };
};

export function ExaminerSalaryCardView({ r }: { r: ExaminerSalaryData }) {
  const g = r.goal;
  return <section aria-label="Examiner oyligi va keyingi maqsad" className="mb-5 rounded-2xl bg-gradient-to-br from-brand-600 via-brand-700 to-indigo-700 p-5 text-white shadow-lg">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0 flex-1 basis-60">
        <p className="flex items-center gap-1.5 text-sm text-white/80"><Wallet size={15} /> Shu oy hisoblangan oyligingiz</p>
        <p className="mt-1 text-3xl font-bold tabular-nums md:text-4xl">{r.volunteer ? "Volontyor" : formatSom(r.salary)}</p>
        <p className="mt-2 text-xs text-white/80">{r.period} · {r.exam_count} ta imtihon · {r.students_total} ta qatnashuv</p>
      </div>
      {g.next_salary != null && <div className="rounded-xl bg-white/15 px-4 py-3">
        <p className="text-xs text-white/80">{g.status === "no_exams" ? "Birinchi hisoblanadigan imtihondan so‘ng" : "Keyingi oylik maqsadi"}</p>
        <p className="text-2xl font-bold tabular-nums text-amber-300">{formatSom(g.next_salary)}</p>
      </div>}
    </div>
    {g.status === "active" ? <div className="mt-4 grid gap-3 md:grid-cols-2">
      <div className="rounded-xl bg-white/10 p-3.5">
        <div className="mb-2 flex items-center justify-between gap-2 text-sm"><span className="flex items-center gap-1.5"><TrendingUp size={14} /> Sof ball</span><b>{r.points} ball</b></div>
        <div role="progressbar" aria-label="Keyingi oylik maqsadiga erishish" aria-valuenow={g.progress} aria-valuemin={0} aria-valuemax={100} className="h-2.5 overflow-hidden rounded-full bg-white/20"><div className="h-full rounded-full bg-white transition-[width] duration-700 motion-reduce:transition-none" style={{ width: `${g.progress}%` }} /></div>
        <p className="mt-2 text-xs leading-5 text-white/85">Yig‘ilgan: {r.base_points} ball<br />Ayirilgan: {r.penalty_points + r.adjustment_points} ball</p>
      </div>
      <div className="rounded-xl bg-white/10 p-3.5">
        <p className="mb-2 flex items-center gap-1.5 text-sm"><Target size={14} /> Keyingi maqsadgacha</p>
        <p className="text-xl font-bold tabular-nums text-amber-300">Yana {g.gap_points} ball</p>
        <p className="mt-1 text-xs leading-5 text-white/90">Sof ball {g.target_points} ga yetganda oylik {formatSom(g.next_salary ?? 0)} bo‘ladi.</p>
      </div>
    </div> : <p className="mt-4 rounded-xl bg-white/10 p-4 text-sm leading-6">
      {g.status === "volunteer" ? (r.volunteer_hint || "Volontyor uchun oylik hisoblanmaydi. Imtihon va ballaringiz qayd etiladi.")
        : g.status === "no_exams" ? "Bu oy hali oylikka hisoblanadigan imtihon o‘tkazilmagan. Hozir oylik 0 so‘m."
        : `Eng yuqori oylik chegarasiga yetdingiz: ${formatSom(r.max)}. Sof ball: ${r.points}.`}
    </p>}
    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-white/80">
      <p className="flex items-center gap-1.5"><Trophy size={13} className="text-amber-300" /> Oy tugashiga {g.days_left} kun qoldi.</p>
      <Link to={r.volunteer ? "/exam" : "/exam?tab=pay"} className="font-medium underline underline-offset-4 hover:text-white">{r.volunteer ? "Imtihonlarim" : "Oylik hisobi — batafsil"}</Link>
    </div>
    {!r.volunteer && <p className="mt-2 text-[11px] leading-5 text-white/75">1 ball = {formatSom(r.unit)}. Ishlagan examiner uchun {formatSom(r.min)}–{formatSom(r.max)}. Keyingi maqsad 100 ming so‘mlik qadamda ko‘rsatiladi; bu alohida bonus emas. Ko‘rsatilgan summa — hisoblangan oylik.</p>}
  </section>;
}

export function ExaminerSalaryCard() {
  const { user } = useAuth();
  const [data, setData] = useState<ExaminerSalaryData | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const identity = `${user?.full_name}:${user?.role}:${user?.branch_id}`;
  useEffect(() => {
    let active = true;
    setData(null); setError(false);
    api.get<ExaminerSalaryData>("/me/examiner-salary").then(r => { if (active) setData(r); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [identity, retry]);
  if (error) return <div role="status" className="mb-5 rounded-xl border bg-white p-4 text-sm text-slate-500">Oylik ma’lumotlari yuklanmadi. <button onClick={() => setRetry(r => r + 1)} className="ml-2 text-brand-600 underline">Qayta yuklash</button></div>;
  return data ? <ExaminerSalaryCardView r={data} /> : <p role="status" className="mb-5 text-sm text-slate-400">Oylik yuklanmoqda…</p>;
}
