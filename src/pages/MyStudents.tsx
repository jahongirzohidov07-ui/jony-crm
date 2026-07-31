import { useEffect, useState } from "react";
import { GraduationCap, Info, AlertTriangle } from "lucide-react";
import { api, type MyStudentList } from "../lib/api";
import { formatDate } from "../lib/format";

/**
 * Ustozning o'z o'quvchilari.
 *
 * Bu yerda BALANS va TO'LOV yo'q — ataylab. Ustoz bolaga qarzdorligi
 * orqali emas, o'qishi orqali qarashi kerak. Pul masalasi
 * administrator va moliya bo'limining ishi.
 */
export default function MyStudents() {
  const [d, setD] = useState<MyStudentList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [group, setGroup] = useState("");
  const [q, setQ] = useState("");
  const [onlyRisk, setOnlyRisk] = useState(false);

  useEffect(() => {
    const p = new URLSearchParams();
    if (group) p.set("group_id", group);
    if (q) p.set("q", q);
    api
      .get<MyStudentList>("/me/students?" + p.toString())
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  }, [group, q]);

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  const rows = onlyRisk ? d.rows.filter((r) => r.at_risk) : d.rows;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <GraduationCap size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          O'quvchilarim
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">{d.total} o'quvchi</p>

      {d.at_risk > 0 && (
        <button
          onClick={() => setOnlyRisk(!onlyRisk)}
          className={`w-full text-left text-sm rounded-lg px-3 py-2 mb-4 flex items-center gap-2 border ${
            onlyRisk
              ? "bg-amber-100 border-amber-300 text-amber-900"
              : "bg-amber-50 border-amber-200 text-amber-800"
          }`}
        >
          <AlertTriangle size={15} className="shrink-0" />
          {d.at_risk} o'quvchining davomati 70% dan past —
          {onlyRisk ? " hammasini ko'rish" : " ularni ko'rish"}
        </button>
      )}

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <select
          value={group}
          onChange={(e) => setGroup(e.target.value)}
          className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
        >
          <option value="">Barcha guruhlarim</option>
          {d.groups.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ism bo'yicha qidirish…"
          className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm flex-1 min-w-[180px]"
        />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">O'quvchi</th>
              <th className="text-left px-3 py-2.5 font-medium">Guruh</th>
              <th className="text-right px-3 py-2.5 font-medium">Davomat</th>
              <th className="text-right px-3 py-2.5 font-medium">
                O'rtacha baho
              </th>
              <th className="text-right px-3 py-2.5 font-medium">Imtihon</th>
              <th className="text-right px-4 py-2.5 font-medium">Qancha vaqt</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((s) => (
              <tr
                key={s.id}
                className={s.at_risk ? "bg-amber-50/40" : undefined}
              >
                <td className="px-4 py-2.5">
                  <p className="font-medium text-slate-900">{s.full_name}</p>
                  {s.enrolled_date && (
                    <p className="text-xs text-slate-400">
                      {formatDate(s.enrolled_date)} dan
                    </p>
                  )}
                </td>
                <td className="px-3 py-2.5 text-slate-500">
                  {s.group || "—"}
                </td>
                <td className="px-3 py-2.5 text-right">
                  {s.attendance_percent != null ? (
                    <span
                      className={
                        s.at_risk
                          ? "text-amber-700 font-medium"
                          : "text-slate-700"
                      }
                    >
                      {s.attendance_percent}%
                      <span className="block text-xs text-slate-400">
                        {s.missed} qoldirgan
                      </span>
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {s.avg_grade ?? <span className="text-slate-300">—</span>}
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {s.last_exam ?? <span className="text-slate-300">—</span>}
                </td>
                <td className="px-4 py-2.5 text-right text-slate-500">
                  {s.months != null ? `${s.months} oy` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="text-sm text-slate-400 py-10 text-center">
            O'quvchi topilmadi.
          </p>
        )}
      </div>

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}
