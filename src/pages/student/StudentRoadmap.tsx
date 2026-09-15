import { StudentLevelBadge } from "../../components/StudentLevelBadge";
import { StudentLoading } from "../../components/StudentLoading";
import { StudentXpHelp } from "../../components/StudentXpHelp";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, ChevronRight, Lock } from "lucide-react";
import { api } from "../../lib/api";
import { StudentCoinIcon as CoinIcon } from "../../components/StudentIcon";
import { XpHex, JSA } from "../../components/Jsa";
import { fmtNum, type SkillsCard } from "../../lib/studentApi";

/**
 * JONY STUDENT — YO'L XARITASI.
 *
 * 2026-08-20: "Yo'l xaritasi.png" dizayni bo'yicha to'q temada
 * qayta terildi (Jahongir: "1ga 1 qilib ber"). Ma'lumot o'zgarmadi:
 * /student/skills — darajalar zanjiri va ballar.
 */

export default function StudentRoadmap() {
  const [d, setD] = useState<SkillsCard | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<SkillsCard>("/student/skills")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <StudentLoading />;

  // 2026-08-25: zina endi chiziqli emas — har darajaning O'Z chegarasi
  // bor (lv.need). Jahongir: "har bir darajalar orasi 500XP bu juda
  // oson bolib qolyabdi".
  const points = d.overall.points;
  const curKey = d.overall.level.key;
  const curIdx = d.levels.findIndex((l) => l.key === curKey);
  const cur = d.levels[curIdx];
  const next = d.levels[curIdx + 1];
  const from = cur?.need ?? 0;
  const per = Math.max(1, (next?.need ?? from) - from);
  const inLevel = Math.max(0, Math.min(per, points - from));
  const pct = Math.round((inLevel / per) * 100);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const NODE_COLORS = ["#7C5CF0", "#22B8F0", "#7C5CF0", "#3A4890", "#3A4890"];

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* ---------------------------------------------- sarlavha */}
      <div className="flex items-center gap-2.5">
        <Link to="/student"
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}>
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold text-white tracking-wide flex-1">
          JONY STUDENT APP
        </p>
        <span className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 border shrink-0"
              style={card}>
          <XpHex size={16} />
          <b className="text-white text-sm">{fmtNum(points)} ball</b>
        </span>
      </div>

      <h1 className="text-[38px] font-extrabold text-white leading-none mt-4">
        Yo'l xaritasi
      </h1>
      <p className="text-[15px] mt-2">
        <span className="text-slate-400">Jami</span>{" "}
        <b className="text-brand-400">{fmtNum(points)} ball</b>
      </p>

      {/* --------------------------------------- Coin/XP farqi */}
      <div className="rounded-2xl border mt-4 divide-y"
           style={{ ...card, borderColor: JSA.cardBorder }}>
        <div className="flex items-center gap-3 px-4 py-3.5">
          <CoinIcon size={26} />
          <p className="text-[15px] text-white">
            <b>Coin</b> <span className="text-slate-400">— sarflanadi</span>
          </p>
        </div>
        <div className="flex items-center gap-3 px-4 py-3.5"
             style={{ borderColor: "#1E2A5E" }}>
          <XpHex size={24} />
          <p className="text-[15px] text-white">
            <b>XP</b> <span className="text-slate-400">— reyting va liga uchun</span>
          </p>
        </div>
      </div>

      {/* ------------------------------------- IELTS taxminiy bali */}
      {/* 2026-08-25, Jahongir: "hamma skillarni qoshib ortachasini
          chiqarganda uni IELTS balli kelib chiqsin". Ilgari band
          faqat umumiy balldan chiqardi — lug'at o'ynagan bola ham
          9.0 ga "yaqinlashardi". */}
      {d.ielts && (
        <div className="rounded-2xl border p-4 mt-4" style={card}>
          <div className="flex items-center gap-3">
            <div className="w-[62px] h-[62px] rounded-2xl flex flex-col items-center justify-center shrink-0"
                 style={{ background: "#122057", border: "1px solid #2E56E8" }}>
              <b className="text-white text-[19px] leading-none">
                {d.ielts.band > 0 ? d.ielts.band.toFixed(1) : "—"}
              </b>
              <span className="text-[9px] text-slate-400 mt-0.5">IELTS</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-[15px]">
                Taxminiy IELTS bali
              </p>
              <p className="text-[11.5px] text-slate-400 leading-snug mt-0.5">
                Oltita ko'nikma balining o'rtachasi. Bitta ko'nikma
                bo'sh tursa — umumiy ball ham ko'tarilmaydi.
              </p>
            </div>
          </div>

          <div className="space-y-1.5 mt-3">
            {d.ielts.skills.map((sk) => (
              <div key={sk.key} className="flex items-center gap-2">
                <span className="text-[12px] text-slate-300 w-[74px] shrink-0">
                  {sk.label}
                </span>
                <div className="h-1.5 flex-1 rounded-full bg-slate-700/60 overflow-hidden">
                  <div className="h-full rounded-full"
                       style={{ width: `${Math.max(sk.score, 2)}%`,
                                background: sk.score >= 44
                                  ? "#22C55E" : sk.score >= 18
                                  ? "#F59E0B" : "#64748B" }} />
                </div>
                <span className="text-[10px] text-slate-400 w-8 shrink-0 text-right">
                  {sk.cefr}
                </span>
                <b className="text-[11px] text-white w-7 shrink-0 text-right">
                  {sk.band > 0 ? sk.band.toFixed(1) : "—"}
                </b>
              </div>
            ))}
          </div>

          {/* 2026-08-25, Jahongir: "shu joyi kerak emas" — shkala
              izohi olib tashlandi. */}
          <p className="text-[11px] text-slate-500 mt-2.5 leading-relaxed">
            Eng zaif tomoningiz — <b className="text-amber-300">
            {d.ielts.weakest}</b>.
          </p>
        </div>
      )}

      {/* ------------------------------------------- ligalar havolasi */}
      <Link to="/student/leagues"
            className="flex items-center gap-3 rounded-2xl border p-4 mt-3"
            style={card}>
        <span className="text-[24px] shrink-0">🏅</span>
        <div className="flex-1 min-w-0">
          <p className="text-white font-bold text-[15px]">Ligalar</p>
          <p className="text-[11.5px] text-slate-400 leading-snug">
            14 ta liga · har ko'tarilishda mukofot coin
          </p>
        </div>
        <ChevronRight size={18} className="text-slate-500 shrink-0" />
      </Link>

      {/* ------------------------------------ joriy daraja kartasi */}
      <div className="student-hero student-pattern rounded-3xl p-5 mt-4"
           style={{ background:
             "linear-gradient(120deg,#2B50E0 0%,#4A56EC 55%,#7B5CF0 100%)" }}>
        <div className="flex items-center gap-4">
          <StudentLevelBadge level={cur?.cefr} size={80} />
          <div className="min-w-0 flex-1">
            <p className="text-[24px] font-extrabold text-white leading-tight truncate">
              {cur?.label} · {cur?.cefr}
            </p>
            <p className="text-sm text-white/85 mt-1">
              Daraja balli <b className="text-white">{fmtNum(inLevel)}</b>/{per}
            </p>
              <StudentXpHelp />
            <div className="flex items-center gap-2.5 mt-2">
              <div className="h-2.5 flex-1 rounded-full bg-white/25 overflow-hidden">
                <div className="h-full rounded-full bg-white"
                     style={{ width: `${Math.max(pct, 4)}%` }} />
              </div>
              <b className="text-white text-sm shrink-0">{pct}%</b>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 mt-3">
          <p className="text-[13px] text-white/85 flex-1">
            {next ? (
              <>
                {next.label}'gacha{" "}
                <b className="text-sky-200">{per - inLevel} ball</b>
              </>
            ) : "Eng yuqori daraja 🏆"}
          </p>
          {next && (
            <span className="inline-flex items-center gap-1.5 rounded-xl bg-white/95 px-3 py-2 text-[13px] font-bold text-slate-800 shrink-0">
              <CoinIcon size={15} />
              Keyingi daraja: {next.cefr}
            </span>
          )}
        </div>
      </div>

      {/* ------------------------------------------ darajalar zanjiri */}
      <div className="relative mt-5">
        {/* vertikal chiziq */}
        <span className="absolute left-[27px] top-4 bottom-4 w-0.5"
              style={{ background: "#26326B" }} />

        <div className="space-y-3">
          {d.levels.map((lv, i) => {
            const passed = i < curIdx;
            const current = i === curIdx;
            const need = lv.need;
            return (
              <div key={lv.key} className="flex items-center gap-3 relative">
                {/* tugun */}
                <span
                  className="w-[56px] h-[56px] rounded-full flex items-center justify-center shrink-0 z-10 border-4"
                  style={{
                    background: passed ? "#16A34A"
                      : current ? "#1A6FE4" : "#182258",
                    borderColor: passed ? "#22C55E"
                      : current ? "#7FB2FF"
                      : NODE_COLORS[i % NODE_COLORS.length],
                    boxShadow: current
                      ? "0 0 22px rgba(63,131,248,0.65)" : undefined,
                  }}
                >
                  {passed ? (
                    <Check size={22} strokeWidth={3.5} className="text-white" />
                  ) : current ? (
                    <b className="text-white text-[17px]">{lv.cefr}</b>
                  ) : (
                    <Lock size={18} className="text-slate-300" />
                  )}
                </span>

                {/* karta */}
                <div
                  className={`flex-1 rounded-2xl border p-4 flex items-center gap-3 ${
                    current ? "" : ""}`}
                  style={current
                    ? { background: "#14245E", borderColor: "#2E56E8",
                        boxShadow: "0 0 18px rgba(46,86,232,0.35)" }
                    : card}
                >
                  <div className="min-w-0 flex-1">
                    <p className={`text-[17px] font-extrabold truncate ${
                      passed || current ? "text-white" : "text-slate-300"}`}>
                      {lv.label}{" "}
                      <span className="text-slate-400 font-semibold">
                        · {lv.cefr}
                      </span>
                    </p>
                    {passed ? (
                      <p className="text-[13px] text-emerald-400 mt-0.5">Ochildi</p>
                    ) : current ? (
                      <p className="text-[13px] text-sky-300 mt-0.5">
                        Siz shu yerdasiz
                      </p>
                    ) : (
                      <p className="text-[13px] text-slate-400 mt-0.5 inline-flex items-center gap-1">
                        <XpHex size={12} /> {fmtNum(need)} XP
                      </p>
                    )}
                  </div>
                  {passed ? (
                    <span className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                      <Check size={15} strokeWidth={4} className="text-white" />
                    </span>
                  ) : current ? (
                    <Link to="/student/games"
                      className="px-4 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-bold shrink-0 inline-flex items-center gap-1">
                      Mashq qilish <ChevronRight size={15} />
                    </Link>
                  ) : (
                    <ChevronRight size={18} className="text-slate-500 shrink-0" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
