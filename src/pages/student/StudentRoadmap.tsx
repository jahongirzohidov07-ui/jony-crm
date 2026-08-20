import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, ChevronRight, Lock } from "lucide-react";
import { api } from "../../lib/api";
import { CoinIcon } from "../../components/CoinIcon";
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
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  const per = d.points_per_level;
  const points = d.overall.points;
  const curKey = d.overall.level.key;
  const curIdx = d.levels.findIndex((l) => l.key === curKey);
  const cur = d.levels[curIdx];
  const next = d.levels[curIdx + 1];
  const inLevel = Math.max(0, Math.min(per, points - curIdx * per));
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
          <b className="text-white text-sm">{fmtNum(points)} XP</b>
        </span>
      </div>

      <h1 className="text-[38px] font-extrabold text-white leading-none mt-4">
        Yo'l xaritasi
      </h1>
      <p className="text-[15px] mt-2">
        <span className="text-slate-400">Jami</span>{" "}
        <b className="text-brand-400">{fmtNum(points)} XP</b>
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
            <b>XP</b> <span className="text-slate-400">— daraja oshiradi</span>
          </p>
        </div>
      </div>

      {/* ------------------------------------ joriy daraja kartasi */}
      <div className="rounded-3xl p-5 mt-4"
           style={{ background:
             "linear-gradient(120deg,#2B50E0 0%,#4A56EC 55%,#7B5CF0 100%)" }}>
        <div className="flex items-center gap-4">
          <div className="relative w-[80px] h-[90px] shrink-0">
            <svg viewBox="0 0 64 72" className="w-full h-full drop-shadow-lg">
              <defs>
                <linearGradient id="shield2" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#7FB2FF" />
                  <stop offset="1" stopColor="#2D5BE8" />
                </linearGradient>
              </defs>
              <path d="M32 2 L60 12 V38 C60 54 46 65 32 70 C18 65 4 54 4 38 V12 Z"
                    fill="url(#shield2)" stroke="#BFD8FF" strokeWidth="2.5" />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-[24px] font-extrabold text-white pt-1">
              {cur?.cefr}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[24px] font-extrabold text-white leading-tight truncate">
              {cur?.label} · {cur?.cefr}
            </p>
            <p className="text-sm text-white/85 mt-1">
              Daraja XP <b className="text-white">{fmtNum(inLevel)}</b>/{per}
            </p>
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
                <b className="text-sky-200">{per - inLevel} XP</b>
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
            const need = i * per;
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
