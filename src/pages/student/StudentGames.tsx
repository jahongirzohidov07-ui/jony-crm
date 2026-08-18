import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen, ChevronRight, Ear, Flame, Headphones, Mic, PenLine,
  Play, Sparkles, Layers,
} from "lucide-react";
import { CoinIcon } from "../../components/CoinIcon";
import { api } from "../../lib/api";
import { fmtNum, type DailyGoal, type ContinueCard } from "../../lib/studentApi";

/**
 * JONY STUDENT — O'RGANISH (2026-08-16 da dizayn bo'yicha qayta
 * yozildi; ilgari "Mashq" deb atalardi).
 *
 * Jahongir: "Bu sahifa dizayn jihatdan eng yaxshi chiqqan. Ranglar
 * orqali bo'limlar tez farqlanadi. Ammo har kartada progress foizi,
 * oxirgi ishlangan mavzu, davom ettirish tugmasi, olinadigan XP va
 * taxminiy vaqt bo'lishi kerak. Hozir '9 ball to'plangan' foydali,
 * ammo o'quvchini keyingi harakatga yetarlicha undamaydi."
 *
 * Shuning uchun sahifa uch qatlamdan iborat:
 *   1. Bugungi progress (nechta vazifa bajarildi + streak)
 *   2. DAVOM ETTIRISH — bitta katta karta, aniq keyingi qadam
 *   3. Barcha mashqlar — olti rangli karta, har birida foiz
 *
 * Tezlik: ilgari sahifa uchta so'rov yuborardi (vocab/stats,
 * grammar/topics, skills). Endi bitta — /api/student/learn.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Section = {
  key: string;
  label: string;
  tone: string;
  href: string;
  value: string;
  percent: number;
  xp: number;
};

type Learn = {
  lifetime_xp: number;
  coins: number;
  streak: number;
  daily: DailyGoal;
  continue: ContinueCard | null;
  sections: Section[];
};

const ICON: Record<string, any> = {
  grammar: BookOpen,
  vocabulary: Layers,
  listening: Headphones,
  reading: BookOpen,
  writing: PenLine,
  speaking: Mic,
};

const TILE: Record<string, string> = {
  violet: "bg-violet-100 text-violet-600",
  emerald: "bg-emerald-100 text-emerald-600",
  amber: "bg-orange-100 text-orange-500",
  sky: "bg-sky-100 text-sky-600",
  rose: "bg-rose-100 text-rose-500",
  teal: "bg-teal-100 text-teal-600",
};

const BAR: Record<string, string> = {
  violet: "bg-violet-500",
  emerald: "bg-emerald-500",
  amber: "bg-orange-400",
  sky: "bg-sky-400",
  rose: "bg-rose-400",
  teal: "bg-teal-400",
};

export default function StudentGames() {
  const [d, setD] = useState<Learn | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Learn>("/student/learn")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (err)
    return (
      <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>
    );
  if (!d)
    return (
      <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>
    );

  const cont = d.continue;

  return (
    <>
      {/* ================================================ SARLAVHA */}
      <div className="bg-brand-600 text-white px-4 pt-6 pb-16">
        <div className="max-w-md mx-auto flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-[26px] font-bold leading-tight">O'rganish</h1>
            <p className="text-sm text-white/85 mt-0.5">
              Bugun o'rganishni davom ettiring
            </p>
          </div>
          <Link
            to="/student/roadmap"
            className="h-9 px-3.5 rounded-full border border-white/40 flex items-center gap-1.5 text-sm font-semibold shrink-0"
          >
            <Sparkles size={14} />
            {fmtNum(d.lifetime_xp)} XP
          </Link>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-11 pb-8 space-y-5">
        {/* ==================================== BUGUNGI PROGRESS */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
          <div className="flex items-center gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-base font-bold text-slate-900">
                Bugungi progress
              </p>
              <div className="flex items-center gap-2.5 mt-2.5">
                <div className="h-2.5 flex-1 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-brand-600 rounded-full transition-all"
                    style={{ width: `${d.daily.percent}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-slate-500 shrink-0">
                  {d.daily.percent}%
                </span>
              </div>
              <p className="text-sm text-slate-500 mt-2">
                {d.daily.done}/{d.daily.total} vazifa bajarildi
              </p>
            </div>

            <div className="text-center shrink-0">
              <div className="w-14 h-14 rounded-full bg-orange-50 flex items-center justify-center">
                <Flame size={26} className="text-orange-500" />
              </div>
              <p className="text-sm font-bold text-slate-900 mt-1.5">
                {d.streak} kun
              </p>
            </div>
          </div>
        </div>

        {/* ===================================== DAVOM ETTIRISH */}
        {cont && (
          <div>
            <p className="text-[15px] font-bold text-slate-900 mb-2">
              Davom ettirish
            </p>
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
              <Link to={cont.href} className="flex items-center gap-3.5">
                <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center shrink-0">
                  <BookOpen size={28} className="text-emerald-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-lg font-bold text-slate-900 truncate">
                    {cont.title}
                  </p>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {cont.subtitle} · {cont.level}
                  </p>
                  <p className="text-sm text-slate-500 mt-1.5">
                    {cont.solved}/{cont.total}
                  </p>
                  <div className="h-2 rounded-full bg-slate-100 mt-1.5 overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${cont.percent}%` }}
                    />
                  </div>
                </div>
                <ChevronRight size={20} className="text-slate-300 shrink-0" />
              </Link>

              <p className="text-xs text-slate-400 mt-3">
                🕐 Taxminan {cont.minutes} daqiqa
              </p>

              <div className="flex gap-2 mt-2.5">
                <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-amber-50 text-amber-800 text-xs font-semibold">
                  ⭐ +{cont.xp} XP
                </span>
                <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold">
                  <CoinIcon size={12} /> +{d.daily.reward_coin} Coin
                </span>
              </div>

              <Link
                to={cont.href}
                className="mt-3.5 w-full h-13 py-3.5 rounded-xl bg-brand-600 text-white font-semibold flex items-center justify-center gap-2.5 active:bg-brand-700"
              >
                <span className="w-7 h-7 rounded-full bg-white/25 flex items-center justify-center">
                  <Play size={14} fill="currentColor" />
                </span>
                Davom etish
              </Link>
            </div>
          </div>
        )}

        {/* ============================== JONY TEACHER (2026-08-18,
            Jahongir: "savol berib koproq oquvchini gapirtiradigan
            Jony Teacher") — AI bilan jonli suhbat. */}
        <Link to="/student/speaking"
          className="block bg-gradient-to-br from-indigo-600 to-violet-500 rounded-2xl p-4 text-white shadow-sm active:scale-[0.99] transition">
          <div className="flex items-center gap-3.5">
            <span className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center text-3xl shrink-0">
              🧑‍🏫
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[16px] font-bold">Jony Teacher</p>
              <p className="text-[12.5px] text-white/85 mt-0.5">
                AI speaking partner — savollarga ingliz tilida javob
                bering, gapirishni mashq qiling
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-white/20 text-[11px] font-bold shrink-0">
              YANGI
            </span>
          </div>
        </Link>

        {/* ==================================== BARCHA MASHQLAR */}
        <div>
          <p className="text-[15px] font-bold text-slate-900 mb-2">
            Barcha mashqlar
          </p>
          <div className="grid grid-cols-2 gap-2.5">
            {d.sections.map((sec) => {
              const Icon = ICON[sec.key] || Ear;
              return (
                <Link
                  key={sec.key}
                  to={sec.href}
                  className="bg-white rounded-xl border border-slate-200 p-3.5 active:scale-[0.98] transition"
                >
                  <div className="flex items-start gap-2.5">
                    <span
                      className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                        TILE[sec.tone] || TILE.sky
                      }`}
                    >
                      <Icon size={21} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[15px] font-bold text-slate-900 truncate">
                        {sec.label}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">
                        {sec.value}
                      </p>
                    </div>
                    <ChevronRight
                      size={16}
                      className="text-slate-300 shrink-0 mt-1"
                    />
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 mt-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${BAR[sec.tone] || BAR.sky}`}
                      style={{ width: `${Math.min(100, sec.percent)}%` }}
                    />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}
