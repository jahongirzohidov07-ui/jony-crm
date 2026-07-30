import { useEffect, useState } from "react";
import { Award, Info } from "lucide-react";
import { api, type TeacherScoreboard as Data } from "../lib/api";
import { formatSom } from "../lib/format";

function tone(v: number): string {
  if (v >= 75) return "bg-emerald-500";
  if (v >= 55) return "bg-sky-500";
  if (v >= 40) return "bg-amber-500";
  return "bg-red-500";
}

function cmp(mine: number | null | undefined, avg: number | null | undefined) {
  if (mine === null || mine === undefined || avg === null || avg === undefined)
    return null;
  const d = Math.round((mine - avg) * 10) / 10;
  if (Math.abs(d) < 0.5) return { text: "o'rtacha darajada", cls: "text-slate-500" };
  return d > 0
    ? { text: `o'rtachadan +${d} yuqori`, cls: "text-emerald-600" }
    : { text: `o'rtachadan ${d} past`, cls: "text-amber-600" };
}

/**
 * Ustozlar reytingi. Ustozning o'ziga ham ochiq — hamkasblari
 * orasidagi o'rnini ko'rsin. Lekin ularning MAOSHI bu yerda yo'q:
 * faqat natija.
 */
export function TeacherScoreboard({ months = 12 }: { months?: number }) {
  const [data, setData] = useState<Data | null>(null);
  const [period, setPeriod] = useState(months);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<Data>(`/teachers/scoreboard?months=${period}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [period]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data || data.rows.length === 0)
    return (
      <p className="text-sm text-slate-400 py-10 text-center">
        Hali ma'lumot yig'ilmagan.
      </p>
    );

  const me = data.me ? data.rows.find((r) => r.teacher_id === data.me) : null;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <Award size={16} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Ustozlar natijasi</p>
        <div className="flex-1" />
        <div className="flex gap-1">
          {[3, 6, 12].map((m) => (
            <button
              key={m}
              onClick={() => setPeriod(m)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                period === m
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {m} oy
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Dars sifati 40% · O'quvchi saqlanishi 30% · LTV 20% · Davomat 10%
      </p>

      {/* --- O'zining natijasi --- */}
      {me && (
        <div className="bg-brand-50 border border-brand-200 rounded-xl p-5 mb-4">
          <div className="flex items-center gap-3 mb-3">
            <span className="w-9 h-9 rounded-lg bg-white text-brand-700 text-base font-semibold flex items-center justify-center">
              {me.rank}
            </span>
            <div className="flex-1">
              <p className="text-sm font-medium text-brand-900">
                Sizning natijangiz
              </p>
              <p className="text-xs text-brand-700">
                {data.count} ta ustoz orasida {me.rank}-o'rin
              </p>
            </div>
            <span className="text-3xl font-semibold text-brand-800">
              {me.score}
            </span>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Me
              label="Dars sifati"
              value={me.quality !== null ? `${me.quality}%` : "—"}
              note={cmp(me.quality, data.averages.quality)}
            />
            <Me
              label="O'quvchi saqlanishi"
              value={`${me.retention}%`}
              note={cmp(me.retention, data.averages.retention)}
            />
            <Me
              label="O'quvchi qiymati"
              value={formatSom(me.ltv)}
              note={cmp(me.ltv, data.averages.ltv)}
            />
            <Me
              label="Davomat"
              value={me.attendance !== null ? `${me.attendance}%` : "—"}
              note={cmp(me.attendance, data.averages.attendance)}
            />
          </div>

          <p className="text-xs text-brand-700 mt-3 flex items-start gap-1.5">
            <Info size={12} className="mt-0.5 shrink-0" />
            O'quvchilaringiz o'rtacha {me.avg_months} oy qoladi
            {data.averages.avg_months
              ? ` (markaz bo'yicha ${data.averages.avg_months} oy)`
              : ""}
            .
          </p>
        </div>
      )}

      {/* --- Umumiy jadval --- */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5 w-10">#</th>
              <th className="text-left">Ustoz</th>
              <th className="text-right w-20">Guruh</th>
              <th className="text-right w-20">O'quvchi</th>
              <th className="text-right w-20">Sifat</th>
              <th className="text-right w-24">Saqlanish</th>
              <th className="text-right w-28">LTV</th>
              <th className="text-right w-20">Davomat</th>
              <th className="w-40">Umumiy ball</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr
                key={r.teacher_id}
                className={`border-t border-slate-100 ${
                  r.teacher_id === data.me ? "bg-brand-50/50" : ""
                }`}
              >
                <td className="px-4 py-2.5 text-slate-400">{r.rank}</td>
                <td className="text-slate-800">
                  {r.full_name}
                  {r.teacher_id === data.me && (
                    <span className="ml-1.5 text-xs text-brand-600">siz</span>
                  )}
                </td>
                <td className="text-right text-slate-500">{r.groups}</td>
                <td className="text-right text-slate-600">{r.students}</td>
                <td className="text-right text-slate-600">
                  {r.quality !== null ? `${r.quality}%` : "—"}
                </td>
                <td
                  className={`text-right font-medium ${
                    r.retention >= 85
                      ? "text-emerald-600"
                      : r.retention >= 70
                        ? "text-slate-600"
                        : "text-red-600"
                  }`}
                >
                  {r.retention}%
                </td>
                <td className="text-right text-slate-700">
                  {formatSom(r.ltv)}
                </td>
                <td className="text-right text-slate-500">
                  {r.attendance !== null ? `${r.attendance}%` : "—"}
                </td>
                <td className="pr-4">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${tone(r.score)}`}
                        style={{ width: `${r.score}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-700 w-8 text-right">
                      {r.score}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Me({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: { text: string; cls: string } | null;
}) {
  return (
    <div className="bg-white rounded-lg p-3">
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
      {note && <p className={`text-xs mt-0.5 ${note.cls}`}>{note.text}</p>}
    </div>
  );
}
