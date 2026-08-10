import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, BookA, ChevronRight, Flame } from "lucide-react";
import { api } from "../../lib/api";
import type { StudentHome, VocabStats } from "../../lib/studentApi";

/**
 * JONY STUDENT — LUG'AT MASHQLARI (2026-08-10).
 *
 * Jahongir: "hammasini bitta bo'lim qilib, grammar tagiga lug'at
 * mashqi qilib yashil rang bilan qo'ygin, lug'at mashqiga kirganda
 * shu mashq turlari chiqsin."
 *
 * Avval 7 ta o'yin "Mashq" sahifasida sochilib yotardi — endi ular
 * shu alohida sahifada (grammar mavzulari sahifasiga o'xshash),
 * statistika ham shu yerda.
 */
export default function StudentVocab() {
  const [d, setD] = useState<StudentHome | null>(null);
  const [st, setSt] = useState<VocabStats | null>(null);

  useEffect(() => {
    api.get<StudentHome>("/student/home").then(setD).catch(() => {});
    api.get<VocabStats>("/student/vocab/stats").then(setSt).catch(() => {});
  }, []);

  const maxWeek = Math.max(1, ...(st?.week || []).map((w) => w.correct));

  return (
    <>
      <div className="bg-gradient-to-br from-emerald-700 to-emerald-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/games"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Mashqlar
          </Link>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <BookA size={22} />
            Lug'at mashqi
          </h1>
          <p className="text-sm opacity-90 mt-0.5">
            Har to'g'ri javob — 1 ball va XP
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4 pb-8">
        {st && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-lg font-semibold text-slate-900 leading-tight">
                  {st.correct}{" "}
                  <span className="text-sm font-normal text-slate-400">
                    to'g'ri javob
                  </span>
                </p>
                <p className="text-xs text-slate-500">
                  {st.total} ta urinishdan · {st.percent}%
                </p>
              </div>
              {st.streak > 0 && (
                <span className="flex items-center gap-1 text-sm font-medium text-orange-600 shrink-0">
                  <Flame size={16} />
                  {st.streak} kun
                </span>
              )}
            </div>
            <div className="flex items-end gap-1.5 h-16">
              {st.week.map((w) => (
                <div
                  key={w.date}
                  className="flex-1 flex flex-col items-center gap-1"
                >
                  <div
                    className="w-full rounded-t bg-emerald-500 min-h-[2px]"
                    style={{ height: `${(w.correct / maxWeek) * 100}%` }}
                    title={`${w.date}: ${w.correct}`}
                  />
                  <span className="text-[9px] text-slate-400">
                    {w.date.slice(8, 10)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-2">
          {(d?.games || []).map((gm) => (
            <Link
              key={gm.key}
              to={`/student/games/${gm.key}`}
              className="flex items-center gap-3 bg-white rounded-xl shadow-sm border border-slate-200 p-4 active:scale-[0.99] transition"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 font-bold">
                {gm.label.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-800">
                  {gm.label}
                </p>
                <p className="text-xs text-slate-400">{gm.hint}</p>
                {st && (
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {st.by_game.find((x) => x.game === gm.key)?.correct || 0}{" "}
                    to'g'ri
                  </p>
                )}
              </div>
              <ChevronRight size={18} className="text-slate-300 shrink-0" />
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
