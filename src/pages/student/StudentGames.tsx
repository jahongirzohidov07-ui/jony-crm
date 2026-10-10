import { StudentLoading } from "../../components/StudentLoading";
import { StudentImage, StudentIcon } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, CloudOff } from "lucide-react";
import { JsaLogo, JSA } from "../../components/Jsa";
import { getLang, skillLabel } from "../../lib/lang";
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
  ielts?: { unlocked: boolean; need_label: string;
            level_label?: string; href: string };
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
const LABEL: Record<string, string> = {
  violet: "#6540bf", emerald: "#047857", amber: "#a15c00",
  sky: "#0369a1", rose: "#b91c1c", teal: "#0f766e",
};

export default function StudentGames() {
  const lang = getLang();
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
    return <StudentLoading />;

  const cont = lang === "en" ? d.continue : null;
  const daily = d.daily;
  // 2026-08-21, Jahongir: "daraja uchun XP soni juda kam bolib qolgan
  // 2x ga oshir" — endi har daraja 200 XP (backend roles.XP_PER_LEVEL).
  const level = Math.floor((d.lifetime_xp || 0) / 200) + 1;
  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const pill = "flex items-center justify-center gap-1 rounded-xl border px-1.5 py-2 min-w-0";

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* ------------------------------------------------ sarlavha */}
      <div className="flex items-center gap-2">
        <div className="flex-1 min-w-0"><JsaLogo /></div>
        <StudentImage src="/jsicons/game-xp.png" alt="XP" className="w-12 h-12" />
      </div>

      <h1 className="text-[38px] font-extrabold text-white leading-none mt-3">
        O'rganish
      </h1>
      <p className="text-[15px] text-slate-400 mt-2">
        Bugungi maqsadingizni bajaring va XP to'plang.
      </p>

      {/* ------------------------------------------- stat pilllari */}
      <div className="student-learn-stats grid grid-cols-2 min-[380px]:grid-cols-4 gap-2 mt-4">
        <span className={pill} style={card}>
          <StudentImage src="/jsicons/game-level.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">{level}-daraja</b>
        </span>
        <span className={pill} style={card}>
          <StudentImage src="/jsicons/game-xp.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">
            {fmtNum(d.lifetime_xp)} <span className="text-brand-300">XP</span>
          </b>
        </span>
        <span className={pill} style={card}>
          <StudentImage src="/jsicons/game-coin.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">
            {fmtNum(d.coins)} <span className="text-slate-400">Coin</span>
          </b>
        </span>
        <span className={pill} style={card}>
          <StudentImage src="/jsicons/game-streak.png" alt="" className="w-6 h-6" />
          <b className="text-white text-sm whitespace-nowrap">
            {d.streak} kun
          </b>
        </span>
      </div>

      {/* -------------------------------------- Bugungi missiya */}
      {daily && (
        <div className="student-panel student-pattern bg-white rounded-3xl p-4 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <StudentIcon name="mission" size={44} />
            <h2 className="text-lg font-extrabold flex-1">Bugungi missiya</h2>
            <b className="text-sm text-emerald-700">{daily.done}/{daily.total}</b>
          </div>
          <div className="divide-y divide-slate-100">
            {daily.tasks.map((task, i) => <Link key={task.key} to={task.href} className="flex items-center gap-2 py-2.5">
              <StudentIcon name={(["vocabulary", "grammar", "listening"] as const)[i % 3]} size={34} />
              <span className="text-sm font-semibold flex-1">{task.title}</span>
              <b className={`text-xs ${task.done ? "text-emerald-600" : "text-slate-500"}`}>{task.done_count}/{task.target}</b>
              <span aria-label={task.done ? "Bajarildi" : "Bajarilmagan"} className={`w-6 h-6 rounded-full grid place-items-center ${task.done ? "bg-emerald-500 text-white" : "border-2 border-slate-300"}`}>{task.done ? "✓" : ""}</span>
            </Link>)}
          </div>
        </div>
      )}

      {/* ----------------------------------------- Davom ettirish */}
      {cont && (
        <Link to={cont.href} className="student-hero student-pattern rounded-2xl p-4 mt-3 flex items-center gap-3 text-white">
          <StudentIcon name="grammar" size={52} />
          <div className="min-w-0 flex-1">
            <p className="text-base font-extrabold">O'rganishni davom ettirish</p>
            <p className="text-xs text-white/85 mt-1">{cont.subtitle} · {cont.title}</p>
            <div className="h-1.5 rounded-full bg-white/20 mt-2 overflow-hidden"><div className="h-full rounded-full bg-sky-300" style={{width: `${cont.percent}%`}} /></div>
          </div>
          <ChevronRight size={22} />
        </Link>
      )}

      {/* --------------------------------------------- bo'limlar */}
      <h2 className="text-lg font-bold text-white mt-5">Til ko'nikmalari</h2>
      <div className="grid grid-cols-2 gap-2 mt-3">
        {d.sections.map((s) => (
          <Link key={s.key} to={lang !== "en" && s.key === "speaking" ? "/student/practice/speaking" : s.href}
            className="student-panel student-skill-card bg-white rounded-2xl p-3 active:scale-[0.98] transition">
            <StudentImage src={SEC_ICON[s.key] || "/jsicons/learn-lesson.png"} alt=""
                 className="w-12 h-12" />
            <div className="flex items-center mt-2">
              <p className="text-[17px] font-extrabold text-slate-900 flex-1 truncate">
                {skillLabel(s.key, s.label, lang)}
              </p>
              <ChevronRight size={17} className="text-slate-300 shrink-0" />
            </div>
            <div className="flex items-center gap-2 mt-1.5">
              <b className="text-sm shrink-0" style={{ color: LABEL[s.tone] || "#1A6FE4" }}>
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

      {/* ------------------------------------------- Daraja testi */}
      {lang === "en" && <Link to="/student/level-test"
        className="block rounded-3xl p-4 mt-3 text-white"
        style={{
          background:
            "linear-gradient(120deg,#2B50E0,#4A56EC 55%,#7B5CF0)",
        }}>
        <div className="student-level-test-card flex items-center gap-4">
          <StudentImage src="/jsicons/learn-exam.png" alt=""
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

      }

      {/* ---- CEFR / IELTS (2026-08-24, Jahongir: "alohida bo'lim
           ochilishi kerak... intermediate tugatganda ochiladigan") */}
      {lang === "en" && d.ielts && (
        <Link to={d.ielts.href || "/student/ielts"}
          className="flex items-center gap-3 rounded-3xl p-4 mt-3 bg-white active:scale-[0.98] transition">
          <StudentImage src="/jsicons/learn-exam.png" alt="" className="w-12 h-12 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-[17px] font-extrabold text-slate-900">
              CEFR / IELTS
            </p>
            <p className="text-[12px] text-slate-500 leading-snug mt-0.5">
              {d.ielts.unlocked
                ? "Xalqaro imtihon formatidagi bo'lim ochiq"
                : d.ielts.need_label}
            </p>
          </div>
          {d.ielts.unlocked ? (
            <ChevronRight size={17} className="text-slate-300 shrink-0" />
          ) : (
            <span className="text-lg shrink-0">🔒</span>
          )}
        </Link>
      )}

      {/* ---- Offline mashqlar (2026-10-07): internet yo'q joyda ham */}
      <Link to="/student/offline"
        className="flex items-center gap-3 rounded-3xl p-4 mt-3 bg-white active:scale-[0.98] transition">
        <span className="w-12 h-12 shrink-0 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
          <CloudOff size={24} />
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-[17px] font-extrabold text-slate-900">Offline mashqlar</p>
          <p className="text-[12px] text-slate-500 leading-snug mt-0.5">
            Internet yo'q joyda ham lug'at va grammatika — ballar keyin qo'shiladi
          </p>
        </div>
        <ChevronRight size={17} className="text-slate-300 shrink-0" />
      </Link>
    </div>
  );
}
