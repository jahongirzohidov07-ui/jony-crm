import { useEffect, useState } from "react";
import { Flame, Info, RotateCcw } from "lucide-react";
import {
  api, type StudentGamification, type XpHistoryRow,
} from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  sky: "bg-sky-100 text-sky-700",
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  violet: "bg-violet-100 text-violet-700",
  teal: "bg-teal-100 text-teal-700",
  rose: "bg-rose-100 text-rose-700",
  slate: "bg-slate-100 text-slate-600",
};
const BAR: Record<string, string> = {
  sky: "bg-sky-500",
  emerald: "bg-emerald-500",
  amber: "bg-amber-500",
  violet: "bg-violet-500",
  teal: "bg-teal-500",
  rose: "bg-rose-500",
  slate: "bg-slate-400",
};

/**
 * O'quvchining gamification kartasi.
 *
 * Coin va XP ataylab ajratilgan: XP — yig'ilgan mehnat (sarflanmaydi),
 * coin — hamyon (sovg'aga ketadi). Ikkalasi bir kartada ko'rinsa ham
 * bir-biriga aralashmaydi.
 */
export function XpCard({
  studentId,
  self = false,
}: {
  studentId?: number;
  self?: boolean;
}) {
  const [d, setD] = useState<StudentGamification | null>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<"umumiy" | "tarix" | "yutuq">("umumiy");

  useEffect(() => {
    const url = self
      ? "/me/gamification"
      : `/students/${studentId}/gamification`;
    api
      .get<StudentGamification>(url)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [studentId, self]);

  if (err)
    return <p className="text-sm text-slate-500 py-8 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const lg = d.league;
  const maxCat = Math.max(...d.by_category.map((c) => c.xp), 1);

  return (
    <div>
      {/* --- Liga kartasi --- */}
      <div
        className="rounded-2xl p-6 mb-4 text-white relative overflow-hidden"
        style={{
          background: lg?.color
            ? `linear-gradient(135deg, ${lg.color} 0%, #0f172a 130%)`
            : "linear-gradient(135deg,#334155,#0f172a)",
        }}
      >
        <div className="flex flex-wrap items-start gap-4">
          <div className="text-5xl leading-none">{lg?.icon || "🌱"}</div>
          <div className="flex-1 min-w-[160px]">
            <p className="text-sm opacity-80">{lg?.name || "Newcomer"}</p>
            <p className="text-4xl font-semibold leading-tight">
              {d.lifetime_xp.toLocaleString("ru-RU")}
              <span className="text-base font-normal opacity-80"> XP</span>
            </p>
            <p className="text-sm opacity-90 mt-0.5">
              Level {d.level} · {d.coins} coin
              {d.season ? ` · ${d.season}: ${d.season_xp} XP` : ""}
            </p>
          </div>
          <div className="text-right">
            {d.ranks.group_rank && (
              <p className="text-sm opacity-90">
                Guruhda {d.ranks.group_rank}/{d.ranks.group_total}
              </p>
            )}
            {d.ranks.branch_rank && (
              <p className="text-sm opacity-90">
                Filialda {d.ranks.branch_rank}/{d.ranks.branch_total}
              </p>
            )}
          </div>
        </div>

        {/* Keyingi ligagacha */}
        <div className="mt-5">
          {d.max_league ? (
            <p className="text-sm font-medium">Maximum League 🐐</p>
          ) : (
            <>
              <div className="flex justify-between text-xs opacity-90 mb-1">
                <span>
                  {lg?.name} → {d.next_league?.name}
                </span>
                <span>
                  yana {d.league_to_next.toLocaleString("ru-RU")} XP
                </span>
              </div>
              <div className="h-2.5 rounded-full bg-white/25 overflow-hidden">
                <div
                  className="h-full rounded-full bg-white"
                  style={{ width: `${d.league_percent}%` }}
                />
              </div>
            </>
          )}
        </div>

        {/* Level progressi */}
        <div className="mt-3">
          <div className="flex justify-between text-xs opacity-80 mb-1">
            <span>Level {d.level}</span>
            <span>Level {d.level + 1} gacha {d.level_to_next} XP</span>
          </div>
          <div className="h-1.5 rounded-full bg-white/20 overflow-hidden">
            <div
              className="h-full rounded-full bg-white/80"
              style={{ width: `${d.level_percent}%` }}
            />
          </div>
        </div>
      </div>

      {/* --- Streak va haftalik --- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Box label="Bu hafta" value={`${d.xp_week} XP`} />
        <Box label="Bu oy" value={`${d.xp_month} XP`} />
        {d.streaks.slice(0, 2).map((s) => (
          <div
            key={s.kind}
            className="rounded-xl border border-slate-200 bg-white p-4"
          >
            <p className="text-xs text-slate-500 mb-1">{s.label}</p>
            <p className="text-lg font-semibold flex items-center gap-1.5">
              {s.current > 0 && (
                <Flame size={15} className="text-orange-500" />
              )}
              {s.current}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              eng uzuni {s.longest}
            </p>
          </div>
        ))}
      </div>

      <div className="flex gap-1 border-b border-slate-200 mb-4">
        {(
          [
            ["umumiy", "Umumiy"],
            ["tarix", `XP tarixi (${d.history.length})`],
            ["yutuq", `Yutuqlar (${d.achievements.length})`],
          ] as const
        ).map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === k
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {tab === "umumiy" && (
        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">
            XP qayerdan yig'ilgan
          </p>
          {d.by_category.length === 0 ? (
            <p className="text-sm text-slate-400 py-6 text-center">
              {d.empty_hint}
            </p>
          ) : (
            <div className="space-y-2">
              {d.by_category.map((c) => (
                <div key={c.key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-600">{c.label}</span>
                    <span className="text-slate-800 font-medium">
                      {c.xp.toLocaleString("ru-RU")} XP
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${BAR[c.tone] || BAR.slate}`}
                      style={{ width: `${(c.xp / maxCat) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {d.league_history.length > 0 && (
            <>
              <p className="text-sm font-medium text-slate-700 mt-5 mb-2">
                Liga tarixi
              </p>
              <div className="space-y-1.5">
                {d.league_history.map((h) => (
                  <div
                    key={h.id}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-slate-100 bg-white"
                  >
                    <span className="text-lg">{h.icon || "🏅"}</span>
                    <span className="text-sm text-slate-800 flex-1">
                      {h.from ? `${h.from} → ` : ""}
                      {h.to}
                    </span>
                    {h.reward_coin > 0 && (
                      <span className="text-xs text-amber-600">
                        +{h.reward_coin} coin
                      </span>
                    )}
                    <span className="text-xs text-slate-400">
                      {h.date ? formatDate(h.date) : ""}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {tab === "tarix" && <History rows={d.history} hint={d.empty_hint} />}

      {tab === "yutuq" && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {d.achievements.length === 0 ? (
            <p className="text-sm text-slate-400 py-6 col-span-full text-center">
              Hali yutuq yo'q.
            </p>
          ) : (
            d.achievements.map((a) => (
              <div
                key={a.id}
                className="rounded-xl border border-slate-200 bg-white p-4 text-center"
              >
                <div className="text-3xl mb-1">{a.icon || "🏅"}</div>
                <p className="text-sm font-medium text-slate-800">{a.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {a.description}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function History({ rows, hint }: { rows: XpHistoryRow[]; hint: string }) {
  if (rows.length === 0)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">{hint}</p>
    );
  return (
    <div className="space-y-1.5">
      {rows.map((h) => (
        <div
          key={h.id}
          className={`flex flex-wrap items-center gap-2.5 px-3 py-2.5 rounded-lg border ${
            h.is_reversal
              ? "border-red-200 bg-red-50"
              : "border-slate-100 bg-white"
          }`}
        >
          <span
            className={`text-sm font-semibold w-16 text-right ${
              h.amount < 0 ? "text-red-600" : "text-emerald-600"
            }`}
          >
            {h.amount > 0 ? "+" : ""}
            {h.amount} XP
          </span>
          <div className="flex-1 min-w-[160px]">
            <p className="text-sm text-slate-800 flex items-center gap-1.5">
              {h.is_reversal && <RotateCcw size={12} className="text-red-500" />}
              {h.label}
            </p>
            {h.reason && (
              <p className="text-xs text-slate-500">{h.reason}</p>
            )}
          </div>
          <span
            className={`px-2 py-0.5 rounded-full text-xs ${
              TONE[h.tone] || TONE.slate
            }`}
          >
            {h.category_label}
          </span>
          <span className="text-xs text-slate-400 w-24 text-right">
            {h.by}
          </span>
          <span className="text-xs text-slate-400 w-20 text-right">
            {h.date ? formatDate(h.date) : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

function Box({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

// ==================================================== Leaderboard
export function LeaderboardTab() {
  const [d, setD] = useState<import("../lib/api").Leaderboard | null>(null);
  const [scope, setScope] = useState("lifetime");
  const [league, setLeague] = useState("");

  useEffect(() => {
    api
      .get<import("../lib/api").Leaderboard>(
        `/gamification/leaderboard?scope=${scope}` +
          (league ? `&league=${league}` : "")
      )
      .then(setD);
  }, [scope, league]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1">
          {d.scopes.map((s) => (
            <button
              key={s.key}
              onClick={() => setScope(s.key)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                scope === s.key
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <select
          value={league}
          onChange={(e) => setLeague(e.target.value)}
          className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm bg-white"
        >
          <option value="">Barcha ligalar</option>
          {d.leagues.map((l) => (
            <option key={l.key} value={l.key}>
              {l.icon} {l.name}
            </option>
          ))}
        </select>
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali XP yig'ilmagan.
        </p>
      ) : (
        <div className="space-y-1.5">
          {d.rows.map((r) => (
            <div
              key={r.student_id}
              className={`flex flex-wrap items-center gap-3 px-4 py-3 rounded-xl border ${
                r.rank <= 3
                  ? "border-amber-200 bg-amber-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <span
                className={`w-8 text-center font-semibold ${
                  r.rank === 1
                    ? "text-amber-500"
                    : r.rank <= 3
                      ? "text-amber-600"
                      : "text-slate-400"
                }`}
              >
                {r.rank}
              </span>
              <span className="text-xl w-7">{r.league_icon || "🌱"}</span>
              <div className="flex-1 min-w-[140px]">
                <p className="text-sm font-medium text-slate-800">
                  {r.full_name}
                </p>
                <p className="text-xs text-slate-400">
                  {r.group || "—"}
                  {r.branch ? ` · ${r.branch}` : ""} · Level {r.level}
                </p>
              </div>
              <span className="text-xs text-slate-500 w-20 text-right">
                {r.league}
              </span>
              <span className="text-sm font-semibold text-slate-800 w-24 text-right">
                {r.xp.toLocaleString("ru-RU")} XP
              </span>
              <span className="w-14 text-right text-xs">
                {r.is_new ? (
                  <span className="text-sky-600">yangi</span>
                ) : r.change === null || r.change === 0 ? (
                  <span className="text-slate-300">—</span>
                ) : (r.change ?? 0) > 0 ? (
                  <span className="text-emerald-600">↑ {r.change}</span>
                ) : (
                  <span className="text-red-500">↓ {Math.abs(r.change ?? 0)}</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}

      {d.masked && (
        <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
          <Info size={11} className="mt-0.5 shrink-0" />
          Maxfiylik uchun familiyalar qisqartirilgan.
        </p>
      )}
    </div>
  );
}
