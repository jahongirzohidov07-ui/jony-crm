import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Lock } from "lucide-react";
import { JSA, XpHex } from "../../components/Jsa";
import { StudentCoinIcon as CoinIcon } from "../../components/StudentIcon";
import { api } from "../../lib/api";
import { fmtNum, type LeaguesCard } from "../../lib/studentApi";

/**
 * LIGALAR (2026-08-25).
 *
 * Jahongir: "keyin ligalarga kotarish bor unga coin beryabsan lekin
 * biror joyda ligalar royxati va u yerda qaysi ligaga chiqqanligini
 * korsatadigan joy yoq ekan hamma kerakli joylarga qoshgin shu
 * narsalari bilmayabdi o'quvchilar".
 *
 * Coin ligaga ko'tarilganda avtomat berilardi, lekin bola buni
 * ko'rmasdi — na hozirgi ligasini, na oldindagi mukofotni. Endi
 * to'liq zina: o'tilganlar (yashil), hozirgisi (yorug'), oldindagilari
 * (qulf) va har biriga XP chegarasi hamda mukofot coini.
 */
export default function StudentLeagues() {
  const [d, setD] = useState<LeaguesCard | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<LeaguesCard>("/student/leagues")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  const earned = d.leagues
    .filter((l) => l.state === "passed" || l.state === "current")
    .reduce((a, l) => a + l.coin, 0);

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5">
        <Link to="/student/roadmap"
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
          <b className="text-white text-sm">{fmtNum(d.xp)} XP</b>
        </span>
      </div>

      <h1 className="text-[34px] font-extrabold text-white leading-none mt-4">
        Ligalar
      </h1>
      <p className="text-[13px] text-slate-400 mt-2 leading-relaxed">
        {d.note}
      </p>

      {/* ------------------------------------------ hozirgi liga */}
      <div className="student-hero student-pattern rounded-3xl p-5 mt-4"
           style={{ background:
             "linear-gradient(120deg,#2B50E0 0%,#4A56EC 55%,#7B5CF0 100%)" }}>
        <div className="flex items-center gap-4">
          <span className="text-[46px] leading-none shrink-0">
            {d.current?.icon || "🌱"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[11px] text-white/70 uppercase tracking-wide">
              Hozirgi ligangiz
            </p>
            <p className="text-[26px] font-extrabold text-white leading-tight truncate">
              {d.current?.name || "Newcomer"}
            </p>
            {!d.max_league && d.next && (
              <>
                <div className="flex items-center gap-2.5 mt-2">
                  <div className="h-2.5 flex-1 rounded-full bg-white/25 overflow-hidden">
                    <div className="h-full rounded-full bg-white"
                         style={{ width: `${Math.max(d.percent, 4)}%` }} />
                  </div>
                  <b className="text-white text-sm shrink-0">
                    {Math.round(d.percent)}%
                  </b>
                </div>
                <p className="text-[13px] text-white/85 mt-2">
                  {d.next.name} ligasigacha{" "}
                  <b className="text-sky-200">{fmtNum(d.to_next)} XP</b>
                </p>
              </>
            )}
            {d.max_league && (
              <p className="text-[13px] text-white/85 mt-2">
                Eng yuqori liga 🏆
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ----------------------------------------- yig'ilgan coin */}
      <div className="flex gap-2.5 mt-3">
        <div className="flex-1 rounded-2xl border p-3.5" style={card}>
          <p className="text-[11px] text-slate-400">Ligalardan olingan</p>
          <p className="flex items-center gap-1.5 mt-1">
            <CoinIcon size={17} />
            <b className="text-white text-[18px]">{earned}</b>
          </p>
        </div>
        <div className="flex-1 rounded-2xl border p-3.5" style={card}>
          <p className="text-[11px] text-slate-400">Hozirgi balans</p>
          <p className="flex items-center gap-1.5 mt-1">
            <CoinIcon size={17} />
            <b className="text-white text-[18px]">{d.coins}</b>
          </p>
        </div>
      </div>

      {/* --------------------------------------------- to'liq zina */}
      <div className="space-y-2 mt-4">
        {d.leagues.map((l) => {
          const passed = l.state === "passed";
          const current = l.state === "current";
          return (
            <div key={l.key}
                 className="flex items-center gap-3 rounded-2xl border p-3.5"
                 style={current
                   ? { background: "#14245E", borderColor: "#2E56E8",
                       boxShadow: "0 0 18px rgba(46,86,232,0.35)" }
                   : card}>
              <span className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 text-[22px]"
                    style={{ background: passed ? "rgba(34,197,94,0.15)"
                      : current ? "rgba(127,178,255,0.18)"
                      : "rgba(100,116,139,0.12)" }}>
                {passed || current ? l.icon : <Lock size={17} className="text-slate-500" />}
              </span>
              <div className="flex-1 min-w-0">
                <p className={`text-[15px] font-bold ${
                  passed || current ? "text-white" : "text-slate-400"}`}>
                  {l.rank}. {l.name}
                </p>
                <p className="text-[11px] text-slate-400">
                  {fmtNum(l.min_xp)}
                  {l.max_xp ? `–${fmtNum(l.max_xp)}` : "+"} XP
                  {l.state === "locked" && l.xp_left > 0 && (
                    <> · yana <b className="text-sky-300">
                      {fmtNum(l.xp_left)} XP</b></>
                  )}
                </p>
              </div>
              {l.coin > 0 && (
                <span className="inline-flex items-center gap-1 shrink-0 rounded-lg px-2 py-1"
                      style={{ background: passed || current
                        ? "rgba(245,158,11,0.15)" : "rgba(100,116,139,0.12)" }}>
                  <CoinIcon size={13} />
                  <b className={`text-[12px] ${
                    passed || current ? "text-amber-300" : "text-slate-500"}`}>
                    +{l.coin}
                  </b>
                </span>
              )}
              {passed && (
                <Check size={17} strokeWidth={3}
                       className="text-emerald-400 shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      <p className="text-[11px] text-slate-500 text-center mt-4 leading-relaxed">
        XP lug'at, grammatika, 4 ko'nikma, davomat va imtihonlardan
        yig'iladi — hammasi bitta hisobga tushadi.
      </p>
    </div>
  );
}
