import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Building2, Layers, Users } from "lucide-react";
import { api, type SalaryBreakdown as Breakdown, type SalaryBreakdownStudent } from "../lib/api";
import { formatSom } from "../lib/format";

/**
 * OYLIK TO'LIQ HISOBOTI — filial -> guruh -> o'quvchi (2026-09-15).
 *
 * Jahongir: "oqituvchilarga oyligini aynan qaysi oquvchi nechta kelgan
 * toliq hisoboti oquvchilar kesimida guruhlar kesimida oziniki
 * korinsin ... 2ta filialda ishlasa filiallar kesimida korinsin".
 *
 * Ikki ko'rinish: "Guruhlar bo'yicha" (filial bo'lsa filial sarlavhasi
 * bilan, guruh bosilsa o'quvchilari ochiladi) va "O'quvchilar bo'yicha"
 * (bitta ro'yxat). Raqamlar server hisobidan — oylik bilan bir xil.
 */
export function SalaryBreakdown({
  teacherId,
  period,
  compact = false,
}: {
  teacherId: number;
  period: string;
  compact?: boolean;
}) {
  const [d, setD] = useState<Breakdown | null>(null);
  const [err, setErr] = useState("");
  const [view, setView] = useState<"groups" | "students">("groups");
  const [open, setOpen] = useState<Set<number>>(new Set());

  useEffect(() => {
    const [y, m] = period.split("-");
    setD(null);
    setErr("");
    api
      .get<Breakdown>(`/teachers/${teacherId}/salary-breakdown?year=${Number(y)}&month=${Number(m)}`)
      .then((r) => {
        setD(r);
        // Guruh bitta bo'lsa — darrov ochiq
        const all = r.branches.flatMap((b) => b.groups);
        setOpen(new Set(all.length === 1 ? [all[0].group_id] : []));
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [teacherId, period]);

  if (err) return <p className="text-[11px] text-red-600 pt-1">{err}</p>;
  if (!d) return <p className="text-[11px] text-slate-400 pt-1">Hisobot yuklanmoqda...</p>;
  if (d.branches.length === 0)
    return <p className="text-[11px] text-slate-400 pt-1">Bu oyda yo'qlama yo'q.</p>;

  const toggle = (id: number) =>
    setOpen((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <p className="text-[11px] font-medium text-slate-500">
          Qanday hisoblandi · {d.attendances} yo'qlama · {d.students.length} o'quvchi
          {d.multi_branch && ` · ${d.branches.length} filial`}
        </p>
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 text-[11px]">
          <button
            type="button"
            onClick={() => setView("groups")}
            className={`flex items-center gap-1 rounded-md px-2 py-1 ${
              view === "groups" ? "bg-brand-600 text-white" : "text-slate-600"
            }`}
          >
            <Layers size={12} /> Guruhlar
          </button>
          <button
            type="button"
            onClick={() => setView("students")}
            className={`flex items-center gap-1 rounded-md px-2 py-1 ${
              view === "students" ? "bg-brand-600 text-white" : "text-slate-600"
            }`}
          >
            <Users size={12} /> O'quvchilar
          </button>
        </div>
      </div>

      {d.sealed && d.sealed_amount != null && Math.abs(d.sealed_amount - d.amount) >= 1 && (
        <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
          Oy muhrlangan: oylik {formatSom(d.sealed_amount)}. Quyidagi batafsil hisob hozirgi
          yo'qlamalardan — oy yopilgandan keyin yo'qlama o'zgargani uchun farq bor.
        </p>
      )}

      {view === "groups" ? (
        <div className="space-y-2">
          {d.branches.map((b) => (
            <div key={b.branch_id ?? 0} className="space-y-1">
              {d.multi_branch && (
                <div className="flex items-center justify-between rounded-lg bg-brand-50 border border-brand-100 px-2.5 py-1.5">
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-brand-800">
                    <Building2 size={13} /> {b.branch}
                  </span>
                  <span className="text-xs text-brand-800">
                    {b.attendances} yo'qlama · <b>{formatSom(b.amount)}</b>
                  </span>
                </div>
              )}
              {b.groups.map((g) => {
                const isOpen = open.has(g.group_id);
                return (
                  <div key={g.group_id} className="bg-white rounded-lg border border-slate-100">
                    <button
                      type="button"
                      onClick={() => toggle(g.group_id)}
                      className="w-full flex items-center justify-between gap-2 text-xs px-2.5 py-1.5 text-left"
                    >
                      <div className="min-w-0 flex items-start gap-1.5">
                        {isOpen ? (
                          <ChevronDown size={13} className="mt-0.5 text-slate-400 shrink-0" />
                        ) : (
                          <ChevronRight size={13} className="mt-0.5 text-slate-400 shrink-0" />
                        )}
                        <div className="min-w-0">
                          <p className="text-slate-800 truncate">{g.group}</p>
                          <p className="text-[11px] text-slate-500">
                            {g.lessons} dars · {g.attendances} yo'qlama × {formatSom(g.rate)}
                            <span className="text-slate-400">
                              {" "}({formatSom(g.rate_per_student_month)} ÷ {g.standard_lessons})
                            </span>
                          </p>
                        </div>
                      </div>
                      <span className="font-medium text-slate-900 shrink-0">{formatSom(g.amount)}</span>
                    </button>
                    {isOpen && <StudentTable rows={g.students} compact={compact} />}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-slate-100">
          <StudentTable rows={d.students} compact={compact} showGroups={true} multiBranch={d.multi_branch} />
        </div>
      )}

      <p className="text-[10px] text-slate-400">
        Har bir belgi (keldi ham, kelmadi ham) = 1 yo'qlama × o'sha guruh narxi.
        {d.not_counted > 0 &&
          ` Guruhdan chiqqan o'quvchining oxirgi kelgan kunidan keyingi ${d.not_counted} ta belgisi oylikka qo'shilmagan.`}
      </p>
    </div>
  );
}

function StudentTable({
  rows,
  compact,
  showGroups = false,
  multiBranch = false,
}: {
  rows: SalaryBreakdownStudent[];
  compact: boolean;
  showGroups?: boolean;
  multiBranch?: boolean;
}) {
  if (rows.length === 0)
    return <p className="text-[11px] text-slate-400 px-2.5 pb-2">Yo'qlama belgilanmagan.</p>;
  return (
    <div className="overflow-x-auto border-t border-slate-100">
      <table className="w-full text-[11px]">
        <thead className="text-slate-400">
          <tr>
            <th className="text-left font-medium px-2.5 py-1">O'quvchi</th>
            <th className="text-right font-medium px-1.5 py-1">Keldi</th>
            <th className="text-right font-medium px-1.5 py-1">Kelmadi</th>
            {!compact && <th className="text-right font-medium px-1.5 py-1">Hisoblandi</th>}
            <th className="text-right font-medium px-2.5 py-1">Summa</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {rows.map((s) => (
            <tr key={s.student_id}>
              <td className="px-2.5 py-1 text-slate-700">
                <span className="block truncate max-w-[180px] sm:max-w-none">{s.student}</span>
                {showGroups && (s.groups || (multiBranch && s.branches)) && (
                  <span className="block text-[10px] text-slate-400 truncate max-w-[180px] sm:max-w-none">
                    {s.groups}
                    {multiBranch && s.branches ? ` · ${s.branches}` : ""}
                  </span>
                )}
                {s.not_counted > 0 && (
                  <span className="block text-[10px] text-amber-600">
                    {s.not_counted} ta belgi sanalmadi (guruhdan chiqqan)
                  </span>
                )}
              </td>
              <td className="px-1.5 py-1 text-right text-emerald-700">{s.present}</td>
              <td className="px-1.5 py-1 text-right text-red-600">{s.absent}</td>
              {!compact && <td className="px-1.5 py-1 text-right text-slate-600">{s.counted}</td>}
              <td className="px-2.5 py-1 text-right font-medium text-slate-900 whitespace-nowrap">
                {formatSom(s.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
