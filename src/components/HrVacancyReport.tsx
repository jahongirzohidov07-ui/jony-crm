import { useEffect, useState } from "react";
import { Clock, Briefcase, UserCheck, AlertTriangle, Download } from "lucide-react";
import { api, type HrVacancyReport as Report, type HrVacancySummary } from "../lib/api";
import { formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

/**
 * VAKANSIYALAR ANALITIKASI (2026-09-16, Jahongir: "HR bitta
 * vakansiyani nechi kunda yopayotganligini hisobotlarda analitikasi
 * kerak, nechta nomzoddan nechtasi ishga olinayotganligi ham kerak").
 *
 * Tepada: o'rtacha yopilish muddati, ochiq vakansiyalar, konversiya.
 * Keyin: nomzod -> suhbat -> ishga olindi zinasi, lavozim va filial
 * kesimi, va har bir vakansiya qatori.
 */
const days = (n: number | null | undefined) => (n == null ? "—" : `${n} kun`);

function Card({
  label, value, hint, icon: Icon, tone = "slate",
}: {
  label: string;
  value: string;
  hint?: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  tone?: "slate" | "green" | "amber" | "red";
}) {
  const cls = {
    slate: "text-slate-900", green: "text-emerald-600",
    amber: "text-amber-600", red: "text-red-600",
  }[tone];
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className="text-slate-400" />
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${cls}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Bar({ label, n, total, color }: { label: string; n: number; total: number; color: string }) {
  const pct = total ? Math.round((n / total) * 1000) / 10 : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-32 shrink-0 text-slate-600">{label}</span>
      <div className="flex-1 h-6 rounded-md bg-slate-100 overflow-hidden">
        <div className="h-full rounded-md" style={{ width: `${Math.max(pct, n ? 2 : 0)}%`, background: color }} />
      </div>
      <span className="w-24 shrink-0 text-right">
        <b className="text-slate-900">{n}</b>
        <span className="text-slate-400 text-xs"> · {pct}%</span>
      </span>
    </div>
  );
}

function SliceTable({ title, rows }: { title: string; rows: HrVacancySummary[] }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm font-medium text-slate-700 mb-3">{title}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-100">
              <th className="text-left py-2">Nomi</th>
              <th className="text-right">Vakansiya</th>
              <th className="text-right">Yopilgan</th>
              <th className="text-right">O'rtacha muddat</th>
              <th className="text-right">Nomzod</th>
              <th className="text-right">Olindi</th>
              <th className="text-right">Konversiya</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-b border-slate-50">
                <td className="py-2 text-slate-800">{r.label}</td>
                <td className="text-right">{r.vacancies}</td>
                <td className="text-right text-slate-500">{r.filled}</td>
                <td className="text-right font-medium">{days(r.avg_days_to_close)}</td>
                <td className="text-right">{r.candidates}</td>
                <td className="text-right font-medium text-emerald-600">{r.hired}</td>
                <td className="text-right text-slate-600">
                  {r.conversion}%
                  {r.candidates_per_hire != null && (
                    <span className="block text-[11px] text-slate-400">
                      {r.candidates_per_hire} nomzoddan 1
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function HrVacancyReport({ months }: { months: number }) {
  const [d, setD] = useState<Report | null>(null);
  const [err, setErr] = useState("");
  const [show, setShow] = useState<"all" | "open" | "closed">("all");

  useEffect(() => {
    setD(null);
    setErr("");
    api
      .get<Report>(`/reports/hr-vacancies?months=${months}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [months]);

  if (err) return <p className="text-sm text-red-600 py-4">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-4">Vakansiyalar analitikasi yuklanmoqda...</p>;
  if (d.rows.length === 0)
    return (
      <p className="text-sm text-slate-400 py-6 text-center bg-white rounded-xl border border-slate-200 mb-5">
        Bu davrda vakansiya yo'q — vakansiya ochilgach yopilish muddati va konversiya shu yerda chiqadi.
      </p>
    );

  const s = d.summary;
  const rows = d.rows.filter((r) => show === "all" || (show === "open" ? !r.closed : r.closed));

  return (
    <div className="space-y-5 mb-8">
      <div>
        <p className="text-base font-semibold text-slate-900">Vakansiyalar analitikasi</p>
        <p className="text-xs text-slate-400">{d.hint}</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card
          icon={Clock}
          label="O'rtacha yopilish muddati"
          value={days(s.avg_days_to_close)}
          hint={s.filled
            ? `${s.filled} ta yopilgan · mediana ${days(s.median_days_to_close)} · ${s.fastest}–${s.slowest} kun`
            : "hali xodim topilib yopilgan vakansiya yo'q"}
        />
        <Card
          icon={Briefcase}
          label="Ochiq vakansiyalar"
          value={String(s.open)}
          hint={s.open ? `o'rtacha ${days(s.avg_open_age)} dan beri ochiq` : "hammasi yopilgan"}
        />
        <Card
          icon={UserCheck}
          tone="green"
          label="Nomzoddan ishga olish"
          value={`${s.conversion}%`}
          hint={s.candidates_per_hire != null
            ? `${s.candidates} nomzoddan ${s.hired} tasi · har ${s.candidates_per_hire} tadan 1`
            : `${s.candidates} nomzod, hali hech kim olinmagan`}
        />
        <Card
          icon={AlertTriangle}
          tone={s.overdue ? "red" : "slate"}
          label="Muddatidan o'tgan"
          value={String(s.overdue)}
          hint="rejadagi yopilish sanasi o'tgan ochiq vakansiya"
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-2">
        <p className="text-sm font-medium text-slate-700">Nomzoddan xodimgacha</p>
        <p className="text-xs text-slate-400 mb-2">Vakansiyalarga kelgan nomzodlar qayergacha yetyapti</p>
        <Bar label="Nomzodlar" n={s.candidates} total={s.candidates} color="#94a3b8" />
        <Bar label="Suhbatga yetdi" n={s.interviewed} total={s.candidates} color="#8b5cf6" />
        <Bar label="Ishga olindi" n={s.hired} total={s.candidates} color="#10b981" />
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <SliceTable title="Lavozim kesimida" rows={d.by_position} />
        {d.by_branch.length > 1 && <SliceTable title="Filial kesimida" rows={d.by_branch} />}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center justify-between gap-2 flex-wrap mb-3">
          <p className="text-sm font-medium text-slate-700">Har bir vakansiya</p>
          <div className="flex items-center gap-2">
            {(["all", "open", "closed"] as const).map((k) => (
              <button
                key={k}
                onClick={() => setShow(k)}
                className={`px-2.5 py-1 rounded-lg text-xs border ${
                  show === k ? "bg-brand-50 border-brand-400 text-brand-700" : "bg-white border-slate-200 text-slate-500"
                }`}
              >
                {k === "all" ? "Hammasi" : k === "open" ? "Ochiq" : "Yopilgan"}
              </button>
            ))}
            <button
              onClick={() =>
                exportToExcel("vakansiyalar-analitikasi", "Vakansiyalar",
                  d.rows.map((r) => ({
                    Vakansiya: r.title,
                    Lavozim: r.position ?? "",
                    Filial: r.branch,
                    Holat: r.status_label,
                    Ochilgan: r.opened_on ?? "",
                    Yopilgan: r.closed_on ?? "",
                    "Kun": r.days ?? "",
                    "Yopilish sababi": r.close_reason ?? "",
                    Nomzod: r.candidates,
                    "Suhbatga yetdi": r.interviewed,
                    "Ishga olindi": r.hired,
                    "Konversiya %": r.conversion,
                  })))
              }
              className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-brand-600"
            >
              <Download size={14} /> Excel
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 border-b border-slate-100">
                <th className="text-left py-2">Vakansiya</th>
                <th className="text-left">Holat</th>
                <th className="text-left">Ochilgan → yopilgan</th>
                <th className="text-right">Muddat</th>
                <th className="text-right">Nomzod</th>
                <th className="text-right">Suhbat</th>
                <th className="text-right">Olindi</th>
                <th className="text-right">Konversiya</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-slate-50 align-top">
                  <td className="py-2 pr-2">
                    <p className="text-slate-800">{r.title}</p>
                    <p className="text-[11px] text-slate-400">
                      {r.branch}{r.headcount > 1 ? ` · ${r.headcount} o'rin` : ""}
                    </p>
                  </td>
                  <td className="pr-2 py-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      r.closed
                        ? r.filled ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"
                        : "bg-sky-50 text-sky-700"
                    }`}>
                      {r.status_label}
                    </span>
                    {r.close_reason && (
                      <p className="text-[11px] text-slate-400 mt-0.5">{r.close_reason}</p>
                    )}
                  </td>
                  <td className="pr-2 py-2 text-xs text-slate-500 whitespace-nowrap">
                    {r.opened_on ? formatDate(r.opened_on) : "—"} →{" "}
                    {r.closed_on ? formatDate(r.closed_on) : "hali ochiq"}
                  </td>
                  <td className={`py-2 text-right font-medium whitespace-nowrap ${r.overdue ? "text-red-600" : "text-slate-900"}`}>
                    {days(r.days)}
                    {r.overdue && <span className="block text-[11px] font-normal">muddatdan o'tgan</span>}
                    {!r.closed && r.days != null && !r.overdue && (
                      <span className="block text-[11px] font-normal text-slate-400">ochiq turibdi</span>
                    )}
                  </td>
                  <td className="py-2 text-right">{r.candidates}</td>
                  <td className="py-2 text-right text-slate-500">{r.interviewed}</td>
                  <td className="py-2 text-right font-medium text-emerald-600">
                    {r.hired}
                    {r.first_hire_days != null && (
                      <span className="block text-[11px] font-normal text-slate-400">
                        {r.first_hire_days}-kuni
                      </span>
                    )}
                  </td>
                  <td className="py-2 text-right text-slate-600">{r.candidates ? `${r.conversion}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
