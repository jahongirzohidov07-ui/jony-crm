import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { JsaLogo, JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import { fmtNum, type DailyGoal, type ContinueCard } from "../../lib/studentApi";

/**
 * JONY STUDENT — O'RGANISH.
 *
 * 2026-08-20/21: Jahongir bergan "organish.png" dizayni bo'yicha
 * TO'Q temada qayta terildi ("qolgan sahifalarini ham qoshdim
 * hammasini 1ga 1 qilib ber 100% kopya bolsin") va u bergan ikonka
 * to'plami (/jsicons) ulandi. Ma'lumot manbai o'zgarmadi:
 * /api/student/learn.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Section = {
  key: string; label: string; tone: string; href: string;
  value: string; percent: number; xp: number;
};

type Learn = {
  lifetime_xp: number; coins: number; streak: number;
  daily: DailyGoal; continue: ContinueCard | null; sections: Section[];
};

/** Dizayn ikonkalari (Jahongir bergan to'plamdan). */
const SEC_ICON: Record<string, string> = {
  grammar: "/jsicons/learn-grammar.png",
  vocabulary: "/jsicons/learn-vocabulary.png",
  listening: "/jsicons/learn-listening.png",
  reading: "/jsicons/learn-reading.png",
  writing: "/jsicons/learn-writing.png",
  speaking: "/jsicons/learn-jony-teacher.png",
};

const BAR: Record<string, string> = {
  violet: "#7C5CF0", emerald: "#10B981", amber: "#F59E0B",
  sky: "#22B8F0", rose: "#EF4444", teal: "#14B8A6",
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
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  const cont = d.continue;
  const daily = d.daily;
  // 2026-08-21, Jahongir: "daraja uchun XP soni juda kam bolib qolgan
  // 2x ga oshir" — endi har daraja 200 XP (backend roles.XP_PER_LEVEL).
  const level = Math.floor((d.lifetime_xp || 0) / 200) + 1;
  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const pill = "flex items-center gap-1.5 rounded-2xl border px-3 py-2 shrink-0";

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* ------------------------------------------------ sarlavha */}
      <div className="flex items-center gap-2">
        <div className="flex-1 min-w-0"><JsaLogo /></div>
        <img src="/jsicons/game-xp.png" alt="XP" className="w-12 h-12" />
      </div>

      <h1 className="text-[38px] font-extrabold text-white leading-none mt-3">
        O'rganish
      </h1>
      <p className="text-[15px] text-slate-400 mt-2">
        Bugungi maqsadingizni bajaring va XP to'plang.
      </p>

      {/* ------------------------------------------- stat pilllari */}
      <div className="flex gap-2 mt-4 overflow-x-auto pb-1 -mx-4 px-4">
        <span className={pill} style={card}>
          <img src="/jsicons/game-level.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">{level}-daraja</b>
        </span>
        <span className={pill} style={card}>
          <img src="/jsicons/game-xp.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">
            {fmtNum(d.lifetime_xp)} <span className="text-brand-300">XP</span>
          </b>
        </span>
        <span className={pill} style={card}>
          <img src="/jsicons/game-coin.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">
            {fmtNum(d.coins)} <span className="text-slate-400">Coin</span>
          </b>
        </span>
        <span className={pill} style={card}>
          <img src="/jsicons/game-streak.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">
            {d.streak} kun
          </b>
        </span>
      </div>

      {/* -------------------------------------- Bugungi missiya */}
      {daily && (
        <div className="bg-white rounded-3xl p-4 mt-4 flex items-center gap-4">
          <img src="/jsicons/game-mission.png" alt="" className="w-16 h-16 shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-[19px] font-extrabold text-slate-900 flex-1">
                Bugungi missiya
              </p>
              <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-bold shrink-0">
                ⭐ +{daily.reward_xp} XP
              </span>
            </div>
            <p className="text-[26px] font-extrabold text-slate-900 leading-none mt-1">
              <span className="text-brand-600">{daily.done}</span>
              <span className="text-slate-400 text-[20px]"> / {daily.total}</span>
            </p>
            <div className="h-2.5 rounded-full bg-slate-100 mt-2 overflow-hidden">
              <div className="h-full bg-brand-600 rounded-full"
                   style={{ width: `${daily.percent}%` }} />
            </div>
            <p className="text-[13px] text-slate-500 mt-1.5">
              {daily.all_done
                ? "Bugungi missiya bajarildi! 🎉"
                : `Yana ${daily.total - daily.done} ta mashq qoldi`}
            </p>
          </div>
        </div>
      )}

      {/* ----------------------------------------- Davom ettirish */}
      {cont && (
        <div className="bg-white rounded-3xl p-4 mt-3 flex items-center gap-4">
          <img src="/jsicons/learn-listening.png" alt=""
               className="w-14 h-14 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-[19px] font-extrabold text-slate-900">
              Davom ettirish
            </p>
            <p className="text-sm text-slate-500 mt-0.5 truncate">
              {cont.subtitle} <span className="text-brand-600">•</span>{" "}
              {cont.title}
            </p>
            <div className="flex items-center gap-2 mt-1.5">
              <b className="text-brand-600 text-sm">{cont.percent}%</b>
              <div className="h-1.5 flex-1 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full bg-brand-600 rounded-full"
                     style={{ width: `${cont.percent}%` }} />
              </div>
            </div>
          </div>
          <Link to={cont.href}
            className="px-4 py-3 rounded-xl bg-brand-600 text-white text-sm font-bold shrink-0">
            Davom etish
          </Link>
        </div>
      )}

      {/* ------------------------------------------- Daraja testi */}
      <Link to="/student/level-test"
        className="block rounded-3xl p-4 mt-3 text-white"
        style={{
          background:
            "linear-gradient(120deg,#2B50E0,#4A56EC 55%,#7B5CF0)",
        }}>
        <div className="flex items-center gap-4">
          <img src="/jsicons/learn-exam.png" alt=""
               className="w-14 h-14 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-[19px] font-extrabold">Daraja testi</p>
            <p className="text-[12.5px] text-white/80 mt-0.5 leading-snug">
              Grammar, Vocabulary, Reading va Listening bo'yicha aniq
              darajangizni aniqlang
            </p>
          </div>
          <span className="px-3.5 py-2.5 rounded-xl bg-white/15 text-sm font-bold shrink-0">
            Boshlash
          </span>
        </div>
      </Link>

      {/* --------------------------------------------- bo'limlar */}
      <div className="grid grid-cols-2 gap-3 mt-3">
        {d.sections.map((s) => (
          <Link key={s.key} to={s.href}
            className="bg-white rounded-3xl p-4 active:scale-[0.98] transition">
            <img src={SEC_ICON[s.key] || "/jsicons/learn-lesson.png"} alt=""
                 className="w-12 h-12" />
            <div className="flex items-center mt-2">
              <p className="text-[17px] font-extrabold text-slate-900 flex-1 truncate">
                {s.label}
              </p>
              <ChevronRight size={17} className="text-slate-300 shrink-0" />
            </div>
            <div className="flex items-center gap-2 mt-1.5">
              <b className="text-sm shrink-0" style={{ color: BAR[s.tone] || "#1A6FE4" }}>
                {s.percent}%
              </b>
              <div className="h-1.5 flex-1 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full rounded-full"
                     style={{ width: `${s.percent}%`,
                              background: BAR[s.tone] || "#1A6FE4" }} />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
