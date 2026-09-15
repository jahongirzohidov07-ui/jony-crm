import { StudentLoading } from "../../components/StudentLoading";
import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowUp, Clock, Crown, Gift, Info } from "lucide-react";
import { StudentCoinIcon as CoinIcon } from "../../components/StudentIcon";
import { JsaLogo, JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import { fmtNum, type StudentHome as Home } from "../../lib/studentApi";

/**
 * JONY STUDENT — REYTING.
 *
 * 2026-08-20: "Reyting.png" dizayni bo'yicha to'q temada qayta
 * terildi (Jahongir: "1ga 1 qilib ber"). Hisoblash o'zgarmadi:
 * XP jurnalidan, guruh/filial/umumiy va hafta/hamma vaqt kesimida.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Row = {
  rank: number; name: string; photo?: string | null;
  points: number; is_me: boolean; trend?: string | null;
};

type League = { name: string; icon: string; color: string } | null;

type Board = {
  scope: string; period: string; prize_coin: number;
  podium: Row[]; rows: Row[]; me: Row | null;
  /** 2026-08-25: o'z ligangiz reyting sahifasida ham ko'rinadi. */
  league?: League; next_league?: League;
  league_to_next?: number; league_percent?: number;
  to_top10?: number | null; total: number; hint?: string | null;
};

const SCOPES = [
  ["group", "Guruhim"], ["branch", "Filialim"], ["all", "Umumiy"],
] as const;
const PERIODS = [
  ["week", "Shu hafta"], ["all", "Barcha vaqt"],
] as const;

function daysLeftInWeek(): number {
  const d = new Date().getDay(); // 0=yak
  return d === 0 ? 1 : 8 - d;
}

function Avatar({ row, size, ring }: { row: Row; size: number; ring: string }) {
  return (
    <div
      className={`rounded-full overflow-hidden border-4 ${ring} bg-brand-600 flex items-center justify-center shrink-0`}
      style={{ width: size, height: size }}
    >
      {row.photo ? (
        <StudentImage src={row.photo} alt="" className="w-full h-full object-cover" />
      ) : (
        <span className="font-extrabold text-white"
              style={{ fontSize: size * 0.4 }}>
          {row.name?.charAt(0) || "?"}
        </span>
      )}
    </div>
  );
}

export default function StudentLeaderboard() {
  const [scope, setScope] = useState<string>("group");
  const [period, setPeriod] = useState<string>("week");
  const [d, setD] = useState<Board | null>(null);
  const [err, setErr] = useState("");
  const [coins, setCoins] = useState<number | null>(null);

  useEffect(() => {
    api.get<Home>("/student/home")
      .then((h) => setCoins(h.gamification?.coins ?? null))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setD(null);
    api
      .get<Board>(`/student/leaderboard?scope=${scope}&period=${period}`)
      .then((r) => { setD(r); setErr(""); })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [scope, period]);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const podium = d?.podium || [];
  const p1 = podium[0]; const p2 = podium[1]; const p3 = podium[2];

  const Pillar = ({ n, h }: { n: number; h: number }) => (
    <div
      className="rounded-t-2xl flex items-start justify-center pt-2"
      style={{
        height: h,
        background: n === 1
          ? "linear-gradient(180deg,#2E56E8,#16255F)"
          : "linear-gradient(180deg,#1D2F74,#101B4A)",
        boxShadow: n === 1 ? "0 0 26px rgba(46,86,232,0.5)" : undefined,
      }}
    >
      <span className="text-[34px] font-extrabold"
            style={{ color: n === 1 ? "#7FA8FF" : "#3D53A8" }}>
        {n}
      </span>
    </div>
  );

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* ---------------------------------------------- sarlavha */}
      <div className="flex items-center gap-2">
        <div className="flex-1 min-w-0"><JsaLogo /></div>
        {coins != null && (
          <span className="inline-flex items-center gap-2 rounded-2xl px-3.5 py-2 border shrink-0"
                style={card}>
            <CoinIcon size={20} />
            <b className="text-white text-[15px]">{fmtNum(coins)}</b>
            <span className="text-slate-400 text-sm">Coin</span>
          </span>
        )}
      </div>

      <div className="student-leaderboard-heading flex items-start gap-3 mt-3">
        <div className="flex-1 min-w-0">
          <h1 className="text-[36px] font-extrabold text-white leading-none">
            Reyting
          </h1>
          <p className="text-[15px] text-slate-400 mt-2">
            {period === "week" ? "Haftalik XP bo'yicha" : "Umumiy XP bo'yicha"}
          </p>
        </div>
        <div className="text-right shrink-0">
          <span className="inline-flex items-center gap-2 rounded-2xl px-3.5 py-2 border border-amber-500/50 text-amber-300 text-sm font-bold"
                style={{ background: "#1A1A38" }}>
            <Gift size={15} />
            Sovrin: {d?.prize_coin ?? 50} Coin
          </span>
          {period === "week" && (
            <p className="text-[13px] text-slate-300 mt-2 inline-flex items-center gap-1.5">
              <Clock size={13} /> {daysLeftInWeek()} kun qoldi
            </p>
          )}
        </div>
      </div>

      {/* --------------------------------------------- MENING LIGAM */}
      {/* 2026-08-25, Jahongir: "ligalarga kotarish bor unga coin
          beryabsan lekin biror joyda ligalar royxati va u yerda
          qaysi ligaga chiqqanligini korsatadigan joy yoq ekan". */}
      {d?.league && (
        <Link to="/student/leagues"
              className="flex items-center gap-3 rounded-2xl border p-4 mt-4"
              style={card}>
          <span className="text-[30px] shrink-0">{d.league.icon}</span>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] text-slate-400">Mening ligam</p>
            <p className="text-white font-extrabold text-[17px] truncate">
              {d.league.name}
            </p>
            {d.next_league && (
              <>
                <div className="h-1.5 rounded-full bg-slate-700/60 overflow-hidden mt-1.5">
                  <div className="h-full rounded-full bg-amber-400"
                       style={{ width: `${Math.max(d.league_percent || 0, 3)}%` }} />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  {d.next_league.name} ligasigacha{" "}
                  <b className="text-amber-300">
                    {fmtNum(d.league_to_next || 0)} XP
                  </b>
                </p>
              </>
            )}
          </div>
          <span className="text-[11px] font-bold text-brand-300 shrink-0">
            Barchasi →
          </span>
        </Link>
      )}

      {/* ------------------------------------------------ tablar */}
      <div className="rounded-2xl border p-2 mt-4 space-y-2" style={card}>
        <div className="grid grid-cols-3 gap-1.5">
          {SCOPES.map(([k, l]) => (
            <button key={k} onClick={() => setScope(k)}
              className={`py-2.5 rounded-xl text-[15px] font-bold transition ${
                scope === k ? "bg-brand-600 text-white" : "text-slate-300"}`}>
              {l}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {PERIODS.map(([k, l]) => (
            <button key={k} onClick={() => setPeriod(k)}
              className={`py-2.5 rounded-xl text-[15px] font-bold transition ${
                period === k ? "bg-brand-600 text-white" : "text-slate-300"}`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {err && <p className="text-sm text-red-400 mt-4">{err}</p>}
      {!d && !err && (
        <StudentLoading />
      )}

      {/* ------------------------------------------- bo'sh holat */}
      {d?.hint && (
        <div className="rounded-2xl border p-5 mt-4 text-center" style={card}>
          <p className="text-sm text-slate-300">{d.hint}</p>
          <Link to="/student/games"
            className="mt-4 inline-block px-5 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold">
            Mashqni boshlash
          </Link>
        </div>
      )}

      {/* ---------------------------------------------- PODIUM */}
      {d && !d.hint && podium.length > 0 && (
        <div className="mt-6">
          <div className="flex items-end justify-center gap-3">
            <div className="text-center w-[28%]">
              {p2 ? (
                <>
                  <div className="relative inline-block">
                    <Avatar row={p2} size={84} ring="border-slate-300" />
                    <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-slate-300 text-slate-800 text-xs font-bold flex items-center justify-center border-2 border-slate-100">
                      2
                    </span>
                  </div>
                  <p className="text-sm font-bold text-white mt-4 truncate">
                    {p2.is_me ? "Siz" : p2.name}
                  </p>
                  <p className="text-xs text-slate-400">{fmtNum(p2.points)} XP</p>
                </>
              ) : <div className="h-24" />}
            </div>

            <div className="text-center w-[38%]">
              {p1 && (
                <>
                  <Crown size={28} className="mx-auto text-amber-400 mb-1"
                         fill="currentColor" />
                  <div className="relative inline-block">
                    <Avatar row={p1} size={112} ring="border-amber-400" />
                    <span className="absolute -bottom-2.5 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-amber-400 text-white text-sm font-bold flex items-center justify-center border-2 border-amber-200">
                      1
                    </span>
                  </div>
                  <p className="text-base font-bold text-white mt-4 truncate">
                    {p1.is_me ? "Siz" : p1.name}
                  </p>
                  <p className="text-sm text-brand-300 font-semibold">
                    {fmtNum(p1.points)} XP
                  </p>
                </>
              )}
            </div>

            <div className="text-center w-[28%]">
              {p3 ? (
                <>
                  <div className="relative inline-block">
                    <Avatar row={p3} size={84} ring="border-orange-400" />
                    <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-orange-400 text-white text-xs font-bold flex items-center justify-center border-2 border-orange-200">
                      3
                    </span>
                  </div>
                  <p className="text-sm font-bold text-white mt-4 truncate">
                    {p3.is_me ? "Siz" : p3.name}
                  </p>
                  <p className="text-xs text-slate-400">{fmtNum(p3.points)} XP</p>
                </>
              ) : <div className="h-24" />}
            </div>
          </div>

          {/* Poydevor */}
          <div className="grid grid-cols-3 gap-1.5 items-end mt-3 px-2">
            <Pillar n={2} h={64} />
            <Pillar n={1} h={92} />
            <Pillar n={3} h={52} />
          </div>
        </div>
      )}

      {/* --------------------------------- SIZNING O'RNINGIZ (oq) */}
      {d && !d.hint && d.me && (
        <div className="student-panel bg-white rounded-3xl p-4 mt-4">
          <p className="text-[17px] font-extrabold text-slate-900 mb-3">
            Sizning o'rningiz
          </p>
          <div className="rounded-2xl border border-slate-100 bg-slate-50/60 p-3">
            <div className="flex items-center gap-2.5">
              <span className="text-[24px] font-extrabold text-brand-600 w-7 text-center shrink-0">
                {d.me.rank ?? "—"}
              </span>
              <Avatar row={d.me} size={44} ring="border-white" />
              <p className="text-[13px] text-slate-600 leading-snug flex-1 min-w-0">
                {typeof d.to_top10 === "number" && d.to_top10 > 0 ? (
                  <>Top 10 gacha yana <b>{fmtNum(d.to_top10)} XP</b></>
                ) : (
                  <>Siz eng yaxshi 10 talikdasiz</>
                )}
              </p>
              <b className="text-[17px] text-brand-600 shrink-0">
                {fmtNum(d.me.points)} XP
              </b>
              <Link to="/student/games"
                className="px-3.5 py-2.5 rounded-xl bg-brand-600 text-white text-[13px] font-bold shrink-0">
                Mashq qilish
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------ KEYINGI SOVRIN */}
      {d && !d.hint && d.me && typeof d.to_top10 === "number" && d.to_top10 > 0 && (
        <div className="rounded-3xl border p-4 mt-3 flex items-center gap-3"
             style={card}>
          <span className="text-[30px] shrink-0">🎁</span>
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-white">Keyingi sovrin</p>
            <div className="h-2 rounded-full bg-[#26326B] mt-2 overflow-hidden">
              <div className="h-full bg-brand-500 rounded-full"
                   style={{ width: `${Math.min(95, Math.round(
                     (d.me.points / (d.me.points + d.to_top10 || 1)) * 100))}%` }} />
            </div>
          </div>
          <p className="text-sm text-slate-300 shrink-0">
            Yana {fmtNum(d.to_top10)} XP —{" "}
            <b className="text-amber-400">+10 Coin</b>
          </p>
        </div>
      )}

      {/* -------------------------------------- REYTING JADVALI */}
      {d && !d.hint && d.rows.length > 0 && (
        <div className="mt-4 space-y-2">
          {d.rows.map((r) => (
            <div key={r.rank}
              className={`flex items-center gap-3 rounded-2xl border p-3 ${
                r.is_me ? "border-brand-500" : ""}`}
              style={r.is_me
                ? { background: "#14245E", borderColor: "#2E56E8" }
                : card}>
              <span className="w-5 text-sm font-bold text-slate-400 text-center shrink-0">
                {r.rank}
              </span>
              <Avatar row={r} size={40} ring="border-transparent" />
              <span className="text-sm font-semibold text-white flex-1 truncate">
                {r.is_me ? "Siz" : r.name}
              </span>
              <span className="text-sm font-bold text-slate-300 shrink-0">
                {fmtNum(r.points)} XP
              </span>
              {r.trend && r.trend !== "same" && (
                <span className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                  r.trend === "up"
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "bg-red-500/15 text-red-400"}`}>
                  {r.trend === "up" ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {d && !d.hint && (
        <p className="text-[13px] text-slate-400 flex items-center gap-2 mt-4 px-1">
          <Info size={14} className="shrink-0" />
          Reyting barcha mashqlardan yig'ilgan XP asosida hisoblanadi.
        </p>
      )}
    </div>
  );
}
