import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ChevronDown, ChevronRight, Coins, Flame, Sparkles, Trophy,
} from "lucide-react";
import type { ReactNode } from "react";
import { api } from "../../lib/api";
import { BrandIcon } from "../../components/BrandIcon";
import {
  fmtNum, TONE_BAR, type SkillProgress, type StudentHome as Home,
} from "../../lib/studentApi";

/**
 * JONY STUDENT — bosh ekran (2026-08-09).
 *
 * Jahongir aynan shuni so'radi: "o'quvchiga umumiy darajasi va ustiga
 * bosganda har bir bo'limdan alohida darajalari progress ko'rinib
 * tursin, qachon keyingi darajaga yetadi qancha qoldi."
 * Shuning uchun umumiy daraja kartasi BOSILADI va ichidan olti
 * ko'nikma (lug'at, grammatika, o'qish, tinglash, yozish, gapirish)
 * har biri o'z progress chizig'i bilan ochiladi.
 */
export default function StudentHome() {
  const [d, setD] = useState<Home | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api
      .get<Home>("/student/home")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (err)
    return <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>;

  const ov = d.overall;

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-12">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2 mb-4 opacity-90">
            <BrandIcon size={18} className="rounded-md" />
            <span className="text-sm font-medium">Jony Student</span>
          </div>
          <h1 className="text-xl font-semibold">{d.name}</h1>
          <p className="text-sm opacity-90 mt-0.5">
            {d.group || "guruh biriktirilmagan"}
            {d.level_label ? ` · ${d.level_label}` : ""}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 space-y-4">
        {/* --- UMUMIY DARAJA: bosilsa ko'nikmalar ochiladi --- */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <button
            onClick={() => setOpen((v) => !v)}
            className="w-full text-left p-5 active:bg-slate-50 transition"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-slate-500">Umumiy darajangiz</p>
                <p className="text-2xl font-bold text-slate-900 leading-tight">
                  {ov.level.label}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  IELTS {ov.level.ielts} · CEFR {ov.level.cefr}
                </p>
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-brand-600 shrink-0 mt-1">
                Bo'limlar
                {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
              </span>
            </div>

            {ov.max_level ? (
              <p className="mt-4 text-sm font-medium text-emerald-600">
                Eng yuqori daraja 🎉
              </p>
            ) : (
              <div className="mt-4">
                <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                  <span>Keyingi: {ov.next!.label}</span>
                  <span className="font-medium text-slate-700">
                    yana {fmtNum(ov.next!.points_left)} ball
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-600"
                    style={{ width: `${ov.next!.progress_percent}%` }}
                  />
                </div>
              </div>
            )}
          </button>

          {open && (
            <div className="border-t border-slate-100 p-4 space-y-3.5 bg-slate-50/60">
              <p className="text-[11px] text-slate-400">
                Har bir bo'lim alohida hisoblanadi
              </p>
              {d.skills.map((s) => (
                <SkillRow key={s.key} s={s} />
              ))}
            </div>
          )}
        </div>

        {/* --- Statistika --- */}
        <div className="grid grid-cols-2 gap-3">
          <Stat
            icon={<Coins size={16} />}
            tone="bg-amber-50 text-amber-600"
            value={fmtNum(d.gamification.coins)}
            label="Coin"
          />
          <Stat
            icon={<Sparkles size={16} />}
            tone="bg-violet-50 text-violet-600"
            value={fmtNum(d.gamification.lifetime_xp)}
            label="XP"
          />
          <Stat
            icon={<Flame size={16} />}
            tone="bg-orange-50 text-orange-600"
            value={`${d.streak} kun`}
            label="Ketma-ket"
          />
          <Stat
            icon={<Trophy size={16} />}
            tone="bg-emerald-50 text-emerald-600"
            value={
              d.ranks.group_rank
                ? `${d.ranks.group_rank}/${d.ranks.group_total}`
                : "—"
            }
            label="Guruhda"
          />
        </div>

        {/* --- Bugun --- */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-800">Bugun</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {d.today.answered === 0
                  ? "Hali mashq qilmadingiz"
                  : `${d.today.correct} to'g'ri / ${d.today.answered} javob`}
              </p>
            </div>
            <Link
              to="/student/games"
              className="text-xs font-medium px-3.5 py-2 rounded-lg bg-brand-600 text-white shrink-0"
            >
              Mashq qilish
            </Link>
          </div>
        </div>

        {/* --- O'yinlar --- */}
        <div>
          <p className="text-sm font-semibold text-slate-800 mb-2">
            Lug'at o'yinlari
          </p>
          <div className="space-y-2">
            {d.games.map((gm) => (
              <Link
                key={gm.key}
                to={`/student/games/${gm.key}`}
                className="flex items-center gap-3 bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 active:scale-[0.99] transition"
              >
                <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 text-sm font-bold">
                  {gm.label.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800">
                    {gm.label}
                  </p>
                  <p className="text-[11px] text-slate-400 truncate">
                    {gm.hint}
                  </p>
                </div>
                <ChevronRight size={16} className="text-slate-300 shrink-0" />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function SkillRow({ s }: { s: SkillProgress }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <span className="text-sm text-slate-700">{s.label}</span>
        <span className="text-xs font-medium text-slate-800">
          {s.level.label}
        </span>
      </div>
      <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
        <div
          className={`h-full rounded-full ${TONE_BAR[s.tone] || TONE_BAR.slate}`}
          style={{ width: `${s.next ? s.next.progress_percent : 100}%` }}
        />
      </div>
      <p className="text-[11px] text-slate-400 mt-1">
        {s.max_level
          ? "Eng yuqori daraja 🎉"
          : `${s.level.label} → ${s.next!.label} · yana ${fmtNum(
              s.next!.points_left,
            )} ball`}
      </p>
    </div>
  );
}

function Stat({
  icon,
  tone,
  value,
  label,
}: {
  icon: ReactNode;
  tone: string;
  value: string;
  label: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3.5">
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${tone}`}
      >
        {icon}
      </div>
      <p className="text-lg font-semibold text-slate-900 leading-tight">
        {value}
      </p>
      <p className="text-[11px] text-slate-500">{label}</p>
    </div>
  );
}
