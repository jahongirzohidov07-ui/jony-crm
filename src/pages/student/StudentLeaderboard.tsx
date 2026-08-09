import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Leaderboard } from "../../lib/studentApi";

const SCOPES = [
  { key: "group", label: "Guruhim" },
  { key: "branch", label: "Filialim" },
];
const PERIODS = [
  { key: "all", label: "Umumiy" },
  { key: "week", label: "Shu hafta" },
];

/**
 * JONY STUDENT — reyting.
 *
 * Maxfiylik: boshqa o'quvchilarning FAMILIYASI QISQARTIRILADI
 * (server tomonda, "Malika Y." ko'rinishida) va faqat o'z guruhi /
 * filiali doirasida ko'rsatiladi — butun markaz bo'yicha ro'yxat
 * berilmaydi.
 */
export default function StudentLeaderboard() {
  const [scope, setScope] = useState("group");
  const [period, setPeriod] = useState("all");
  const [d, setD] = useState<Leaderboard | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    setD(null);
    setErr("");
    api
      .get<Leaderboard>(`/student/leaderboard?scope=${scope}&period=${period}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [scope, period]);

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-10">
        <div className="max-w-md mx-auto">
          <h1 className="text-xl font-semibold">Reyting</h1>
          <p className="text-sm opacity-90 mt-0.5">
            Lug'at o'yinlaridagi to'g'ri javoblar bo'yicha
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-2 space-y-2">
          <Segmented value={scope} onChange={setScope} items={SCOPES} />
          <Segmented value={period} onChange={setPeriod} items={PERIODS} />
        </div>

        {err && (
          <p className="text-sm text-slate-500 text-center py-10">{err}</p>
        )}
        {!d && !err && (
          <p className="text-sm text-slate-400 text-center py-10">
            Yuklanmoqda…
          </p>
        )}

        {d && d.rows.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
            <p className="text-sm text-slate-500">
              {d.hint || "Hali hech kim ball yig'magan."}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Birinchi bo'ling — mashq qilishni boshlang!
            </p>
          </div>
        )}

        {d && d.rows.length > 0 && (
          <div className="space-y-1.5">
            {d.rows.map((r) => (
              <div
                key={r.rank}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${
                  r.is_me
                    ? "border-brand-400 bg-brand-50"
                    : r.rank <= 3
                      ? "border-amber-200 bg-amber-50"
                      : "border-slate-200 bg-white"
                }`}
              >
                <span
                  className={`w-7 text-center font-bold ${
                    r.rank === 1
                      ? "text-amber-500"
                      : r.rank <= 3
                        ? "text-amber-600"
                        : "text-slate-400"
                  }`}
                >
                  {r.rank}
                </span>
                {r.rank <= 3 && (
                  <span className="text-lg">
                    {r.rank === 1 ? "🥇" : r.rank === 2 ? "🥈" : "🥉"}
                  </span>
                )}
                <p
                  className={`flex-1 text-sm truncate ${
                    r.is_me
                      ? "font-semibold text-brand-800"
                      : "text-slate-800"
                  }`}
                >
                  {r.name}
                </p>
                <span className="text-sm font-semibold text-slate-800 shrink-0">
                  {r.points}
                </span>
              </div>
            ))}
          </div>
        )}

        {d && d.me && (
          <p className="text-xs text-slate-400 text-center">
            Sizning o'rningiz: {d.me.rank} · {d.me.points} ball
          </p>
        )}
      </div>
    </>
  );
}

function Segmented({
  value,
  onChange,
  items,
}: {
  value: string;
  onChange: (v: string) => void;
  items: { key: string; label: string }[];
}) {
  return (
    <div className="grid grid-cols-2 gap-1 bg-slate-100 rounded-lg p-1">
      {items.map((i) => (
        <button
          key={i.key}
          onClick={() => onChange(i.key)}
          className={`py-2 rounded-md text-sm font-medium transition ${
            value === i.key
              ? "bg-white text-brand-700 shadow-sm"
              : "text-slate-500"
          }`}
        >
          {i.label}
        </button>
      ))}
    </div>
  );
}
