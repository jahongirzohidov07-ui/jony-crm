import { useOutletContext } from "react-router-dom";
import { Coins } from "lucide-react";
import { ParentPageHeader } from "../components/ParentPageHeader";
import type { ParentCtx } from "./Parent";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const TONE: Record<string, string> = {
  sky: "bg-sky-100 text-sky-700",
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  violet: "bg-violet-100 text-violet-700",
  teal: "bg-teal-100 text-teal-700",
  rose: "bg-rose-100 text-rose-700",
  slate: "bg-slate-100 text-slate-600",
};

/** OTA-ONA — COIN VA XP (alohida sahifa, 2026-08-09). */
export default function ParentGamification() {
  const { d, fmt } = useOutletContext<ParentCtx>();
  const gam = d.gamification;

  return (
    <>
      <ParentPageHeader title="Coin va XP" icon={<Coins size={18} />} />

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        {!gam ? (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
            <p className="text-sm text-slate-400">
              Hali gamifikatsiya ma'lumoti yo'q.
            </p>
          </div>
        ) : (
          <div
            className="rounded-xl p-5 text-white relative overflow-hidden"
            style={{
              background: gam.league?.color
                ? `linear-gradient(135deg, ${gam.league.color} 0%, #0f172a 130%)`
                : "linear-gradient(135deg,#334155,#0f172a)",
            }}
          >
            <div className="flex items-start gap-3">
              <div className="text-4xl leading-none">
                {gam.league?.icon || "🌱"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs opacity-80">
                  {gam.league?.name || "Newcomer"}
                </p>
                <p className="text-2xl font-semibold leading-tight">
                  {fmt(gam.lifetime_xp)}
                  <span className="text-sm font-normal opacity-80"> XP</span>
                </p>
                <p className="text-sm opacity-90 mt-0.5">
                  {gam.level}-daraja · {gam.coins} coin
                </p>
              </div>
            </div>
            {!gam.max_league && (
              <div className="mt-4">
                <div className="flex justify-between text-[11px] opacity-80 mb-1">
                  <span>Keyingi liga: {gam.next_league?.name}</span>
                  <span>{fmt(gam.league_to_next)} XP qoldi</span>
                </div>
                <div className="h-2 rounded-full bg-white/20 overflow-hidden">
                  <div
                    className="h-2 rounded-full bg-white"
                    style={{ width: `${gam.league_percent}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            So'nggi XP harakatlari
          </p>
          {(!d.xp_history || d.xp_history.length === 0) && (
            <p className="text-sm text-slate-400 text-center py-6">
              Hali XP tarixi yo'q.
            </p>
          )}
          <div className="space-y-1.5">
            {d.xp_history?.map((h: Any, i: number) => (
              <div
                key={i}
                className="flex flex-wrap items-center gap-2.5 px-3 py-2.5 rounded-lg border border-slate-100"
              >
                <span
                  className={`text-sm font-semibold w-14 text-right shrink-0 ${
                    h.amount < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {h.amount > 0 ? "+" : ""}
                  {h.amount} XP
                </span>
                <p className="text-sm text-slate-800 flex-1 min-w-[120px]">
                  {h.label}
                </p>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs shrink-0 ${
                    TONE[h.tone] || TONE.slate
                  }`}
                >
                  {h.category_label}
                </span>
                <span className="text-xs text-slate-400 w-20 text-right shrink-0">
                  {(h.date || "").slice(0, 10)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
