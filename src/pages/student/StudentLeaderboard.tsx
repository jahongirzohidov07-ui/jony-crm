import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowUp, Crown, ShieldCheck } from "lucide-react";
import { CoinIcon } from "../../components/CoinIcon";
import { api } from "../../lib/api";
import { fmtNum } from "../../lib/studentApi";

/**
 * JONY STUDENT — REYTING (2026-08-16 da qayta yozildi).
 *
 * Jahongir: "Eng katta UX kamchiligi — reyting faqat lug'at
 * o'yinlari asosida ekanligi. Bu grammatikasi yoki speaking'i kuchli
 * bolaga adolatsiz tuyuladi. Alohida reytinglar bo'lsin: umumiy XP,
 * haftalik XP, guruh ichida, filial bo'yicha."
 *
 * Endi reyting XP jurnalidan hisoblanadi — lug'at, grammatika, 4
 * ko'nikma, davomat, imtihon, hammasi qo'shiladi.
 *
 * Bo'sh holat ham o'zgardi: "hech kim ball yig'magan" emas, balki
 * aniq chaqiruv — "10 ta savol yechib, birinchi o'rinni egallang".
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Row = {
  rank: number;
  name: string;
  photo?: string | null;
  points: number;
  is_me: boolean;
  trend?: string | null;
};

type Board = {
  scope: string;
  period: string;
  prize_coin: number;
  podium: Row[];
  rows: Row[];
  me: Row | null;
  to_top10?: number | null;
  total: number;
  hint?: string | null;
};

const SCOPES = [
  ["group", "Guruhim"],
  ["branch", "Filialim"],
  ["all", "Umumiy"],
] as const;

const PERIODS = [
  ["week", "Shu hafta"],
  ["all", "Barcha vaqt"],
] as const;

function Avatar({
  row,
  size,
  ring,
}: {
  row: Row;
  size: number;
  ring: string;
}) {
  return (
    <div
      className={`rounded-full overflow-hidden border-4 ${ring} bg-slate-100 flex items-center justify-center shrink-0`}
      style={{ width: size, height: size }}
    >
      {row.photo ? (
        <img src={row.photo} alt="" className="w-full h-full object-cover" />
      ) : (
        <span
          className="font-bold text-slate-400"
          style={{ fontSize: size * 0.36 }}
        >
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

  useEffect(() => {
    setD(null);
    api
      .get<Board>(`/student/leaderboard?scope=${scope}&period=${period}`)
      .then((r) => {
        setD(r);
        setErr("");
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [scope, period]);

  const podium = d?.podium || [];
  const p1 = podium[0];
  const p2 = podium[1];
  const p3 = podium[2];

  return (
    <>
      <div className="bg-brand-600 text-white px-4 pt-6 pb-16">
        <div className="max-w-md mx-auto flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-[26px] font-bold leading-tight">Reyting</h1>
            <p className="text-sm text-white/85 mt-0.5">
              {period === "week" ? "Haftalik XP bo'yicha" : "Umumiy XP bo'yicha"}
            </p>
          </div>
          <span className="h-9 px-3.5 rounded-full border border-white/40 flex items-center gap-1.5 text-sm font-semibold shrink-0">
            <CoinIcon size={15} />
            Sovrin: {d?.prize_coin ?? 50} Coin
          </span>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-11 pb-8 space-y-4">
        {/* -------------------------------------------- FILTRLAR */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-2 space-y-2">
          <div className="grid grid-cols-3 gap-1.5">
            {SCOPES.map(([k, l]) => (
              <button
                key={k}
                onClick={() => setScope(k)}
                className={`py-2.5 rounded-xl text-sm font-semibold transition ${
                  scope === k ? "bg-brand-600 text-white" : "text-slate-500"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {PERIODS.map(([k, l]) => (
              <button
                key={k}
                onClick={() => setPeriod(k)}
                className={`py-2.5 rounded-xl text-sm font-semibold transition ${
                  period === k
                    ? "bg-brand-600 text-white"
                    : "bg-slate-50 text-slate-500"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>

        {err && (
          <p className="text-sm text-red-600 text-center py-6">{err}</p>
        )}
        {!d && !err && (
          <p className="text-sm text-slate-400 text-center py-10">
            Yuklanmoqda…
          </p>
        )}

        {/* --------------------------------------- BO'SH HOLAT */}
        {d && d.hint && (
          <div className="bg-white rounded-2xl border border-slate-200 p-7 text-center">
            <span className="text-4xl">🏆</span>
            <p className="text-sm text-slate-600 mt-3 leading-relaxed">
              {d.hint}
            </p>
            <Link
              to="/student/games"
              className="inline-block mt-4 px-5 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold"
            >
              Mashqni boshlash
            </Link>
          </div>
        )}

        {/* ------------------------------------------- PODIUM */}
        {d && !d.hint && podium.length > 0 && (
          <div className="flex items-end justify-center gap-3 pt-3">
            {/* 2-o'rin */}
            <div className="text-center w-[28%]">
              {p2 ? (
                <>
                  <div className="relative inline-block">
                    <Avatar row={p2} size={84} ring="border-slate-300" />
                    <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-slate-300 text-slate-700 text-xs font-bold flex items-center justify-center border-2 border-white">
                      2
                    </span>
                  </div>
                  <p className="text-sm font-bold text-slate-900 mt-4 truncate">
                    {p2.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {fmtNum(p2.points)} XP
                  </p>
                </>
              ) : (
                <div className="h-24" />
              )}
            </div>

            {/* 1-o'rin */}
            <div className="text-center w-[38%]">
              {p1 && (
                <>
                  <Crown
                    size={26}
                    className="mx-auto text-amber-400 mb-0.5"
                    fill="currentColor"
                  />
                  <div className="relative inline-block">
                    <Avatar row={p1} size={112} ring="border-amber-300" />
                    <span className="absolute -bottom-2.5 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-amber-400 text-white text-sm font-bold flex items-center justify-center border-2 border-white">
                      1
                    </span>
                  </div>
                  <p className="text-base font-bold text-slate-900 mt-4 truncate">
                    {p1.name}
                  </p>
                  <p className="text-sm text-slate-500">
                    {fmtNum(p1.points)} XP
                  </p>
                </>
              )}
            </div>

            {/* 3-o'rin */}
            <div className="text-center w-[28%]">
              {p3 ? (
                <>
                  <div className="relative inline-block">
                    <Avatar row={p3} size={84} ring="border-orange-300" />
                    <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-7 h-7 rounded-full bg-orange-400 text-white text-xs font-bold flex items-center justify-center border-2 border-white">
                      3
                    </span>
                  </div>
                  <p className="text-sm font-bold text-slate-900 mt-4 truncate">
                    {p3.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {fmtNum(p3.points)} XP
                  </p>
                </>
              ) : (
                <div className="h-24" />
              )}
            </div>
          </div>
        )}

        {/* -------------------------------------- REYTING JADVALI */}
        {d && !d.hint && d.rows.length > 0 && (
          <div>
            <p className="text-[15px] font-bold text-slate-900 mb-2 mt-2">
              Reyting jadvali
            </p>
            <div className="space-y-2">
              {d.rows.map((r) => (
                <div
                  key={r.rank}
                  className={`flex items-center gap-3 rounded-xl border p-3 ${
                    r.is_me
                      ? "bg-brand-50 border-brand-300"
                      : "bg-white border-slate-200"
                  }`}
                >
                  <span className="w-5 text-sm font-bold text-slate-500 text-center shrink-0">
                    {r.rank}
                  </span>
                  <Avatar row={r} size={40} ring="border-white" />
                  <span className="text-sm font-semibold text-slate-900 flex-1 truncate">
                    {r.name}
                  </span>
                  <span className="text-sm font-semibold text-slate-600 shrink-0">
                    {fmtNum(r.points)} XP
                  </span>
                  {r.trend && r.trend !== "same" && (
                    <span
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        r.trend === "up"
                          ? "bg-emerald-50 text-emerald-600"
                          : "bg-red-50 text-red-500"
                      }`}
                    >
                      {r.trend === "up" ? (
                        <ArrowUp size={15} />
                      ) : (
                        <ArrowDown size={15} />
                      )}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ------------------------------------ SIZNING O'RNINGIZ */}
        {d && !d.hint && d.me && (
          <div className="bg-brand-50 border border-brand-200 rounded-2xl p-4">
            <p className="text-sm font-semibold text-brand-700 mb-3">
              Sizning o'rningiz
            </p>
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-slate-700 shrink-0">
                {d.me.rank ?? "—"}
              </span>
              <Avatar row={d.me} size={52} ring="border-white" />
              <div className="min-w-0 flex-1">
                <p className="text-base font-bold text-slate-900 truncate">
                  {d.me.name}
                </p>
                {typeof d.to_top10 === "number" && d.to_top10 > 0 ? (
                  <p className="text-xs text-slate-500 mt-0.5">
                    Top 10 gacha yana {fmtNum(d.to_top10)} XP
                  </p>
                ) : (
                  <p className="text-xs text-emerald-600 mt-0.5">
                    Siz eng yaxshi 10 talikdasiz
                  </p>
                )}
              </div>
              <span className="text-lg font-bold text-brand-600 shrink-0">
                {fmtNum(d.me.points)} XP
              </span>
            </div>

            {typeof d.to_top10 === "number" && d.to_top10 > 0 && (
              <div className="h-2 rounded-full bg-white mt-3 overflow-hidden border border-brand-200">
                <div
                  className="h-full bg-brand-600 rounded-full"
                  style={{
                    width: `${Math.min(
                      95,
                      Math.round(
                        (d.me.points / (d.me.points + d.to_top10 || 1)) * 100
                      )
                    )}%`,
                  }}
                />
              </div>
            )}

            <Link
              to="/student/games"
              className="mt-3 block w-full py-3 rounded-xl bg-brand-600 text-white text-sm font-semibold text-center"
            >
              Mashq qilish
            </Link>
          </div>
        )}

        {d && !d.hint && (
          <p className="text-xs text-slate-400 flex items-start gap-1.5 px-1">
            <ShieldCheck size={14} className="shrink-0 mt-0.5 text-brand-400" />
            Reyting barcha mashqlardan yig'ilgan XP asosida hisoblanadi.
          </p>
        )}
      </div>
    </>
  );
}
