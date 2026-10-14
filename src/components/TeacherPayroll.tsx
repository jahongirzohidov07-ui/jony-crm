import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download, GraduationCap } from "lucide-react";
import {
  api, type PayrollGroupRow, type TeacherPayrollReport,
} from "../lib/api";
import { MONTHS } from "../lib/expenses";
import { formatSom } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

/**
 * USTOZLAR OYLIGI hisobotlari (2026-08-20).
 *
 * Jahongir: "oyliklar bo'limini hisobotlardan moliyaga olib o't".
 * Ilgari bu ikki ekran Hisobotlar sahifasida edi - oylik pul ishi
 * bo'lgani uchun endi Moliya > Oyliklar ichida sub-bo'lim bo'lib
 * turadi. Kodning o'zi o'zgarmadi, faqat joyi ko'chdi: hisob-kitob,
 * "To'landi" belgisi va Excel eksporti avvalgidek.
 */

function Stat({
  label, value, hint, tone = "slate", icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red";
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const toneClass =
    tone === "green" ? "text-emerald-600"
      : tone === "red" ? "text-red-600"
      : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${toneClass}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-slate-400 mt-3 max-w-3xl">{children}</p>;
}

export function TeacherPayrollTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<TeacherPayrollReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    api
      .get<TeacherPayrollReport>(`/reports/teacher-payroll?year=${year}&month=${month}`)
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, [year, month]);

  const [paying, setPaying] = useState<string | null>(null);

  /** GURUH QATORIDAGI "TO'LANDI" (2026-10-12, Jahongir: "men oylikni
   *  to'lagan bo'lsa ham xarajatlar bo'limida oylikni tanlab shu joyda
   *  to'lanmagan bo'lib turibdi"). Ilgari bu tugma eski TeacherPayout
   *  belgisini bosardi — hisobot uni o'qimasdi, guruh doim
   *  "To'lanmagan" edi. Endi holat ustozga BERILGAN puldan (Xarajatlar
   *  -> Oylik, ustoz kartasi — qayerdan bo'lsa ham) chiqadi; bosilsa
   *  guruhning shu oy uchun QOLGAN summasi ustoz kartasiga yoziladi.
   *  Allaqachon berilgan bo'lsa server hech narsa yozmaydi. */
  async function payGroup(teacherId: number, g: PayrollGroupRow) {
    const left = g.left ?? g.amount;
    if (!confirm(
      `${g.group}: ${formatSom(left)} ustoz oylik kartasiga "berildi" ` +
      `bo'lib yoziladi (kassadan chiqim). Davom etilsinmi?`)) return;
    setPaying(`${teacherId}-${g.group_id}`);
    setError(null);
    try {
      const res = await api.post<{ created: boolean; already_paid?: boolean }>(
        "/reports/teacher-payroll/pay",
        { teacher_id: teacherId, group_id: g.group_id, year, month },
      );
      // Boshqa filialdan yoki Xarajatlar orqali to'liq berilgan bo'lsa
      // server ikkinchi marta yozmaydi (2026-10-12) — jim qolmasin
      if (res?.already_paid) {
        alert(
          "Ustozga shu oy uchun oyligi to'liq berilgan (boshqa filialdan " +
          "yoki Xarajatlar orqali) — yangi to'lov yozilmadi.",
        );
      }
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setPaying(null);
    }
  }

  const years = [now.getFullYear() - 1, now.getFullYear()];

  return (
    <div>
      <div className="flex items-center justify-between mb-5 gap-2">
        <div className="flex items-center gap-2">
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
        {data && data.rows.length > 0 && (
          <button
            onClick={() =>
              exportToExcel("ustozlar-oyligi", "Oylik",
                data.rows.map((r) => ({
                  Ustoz: r.full_name,
                  Filial: r.branch ?? "",
                  Guruhlar: r.groups.length,
                  "O'quvchi": r.students,
                  Darslar: r.lessons,
                  "Ish haqi": r.amount,
                  "To'langan": r.paid_amount,
                })))
            }
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
          >
            <Download size={15} /> Excel
          </button>
        )}
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Bu oy uchun ish haqi hisoblanmagan. Guruh sahifasidan
          "Ustozlar ish haqi → Hisoblash va saqlash" tugmasini bosing.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <Stat label="Ustozlar" value={String(data.teacher_count)} icon={GraduationCap} />
            <Stat label="Jami ish haqi" value={formatSom(data.total)} />
            <Stat label="To'langan" value={formatSom(data.paid)} tone="green" />
            <Stat
              label="To'lanmagan"
              value={formatSom(data.unpaid)}
              tone={data.unpaid > 0 ? "red" : "slate"}
            />
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Ustoz</th>
                  <th className="text-left px-4 py-3 font-medium">Filial</th>
                  <th className="text-right px-4 py-3 font-medium">Guruh</th>
                  <th className="text-right px-4 py-3 font-medium">O'quvchi</th>
                  <th className="text-right px-4 py-3 font-medium">Dars</th>
                  <th className="text-right px-4 py-3 font-medium">Ish haqi</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <>
                    <tr
                      key={r.teacher_id}
                      onClick={() => setOpen(open === r.teacher_id ? null : r.teacher_id)}
                      className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                    >
                      <td className="px-4 py-3 font-medium text-slate-800">
                        {r.full_name}
                        {/* 1 000 so'mdan kam farq — yaxlitlash (1 703 333
                            o'rniga 1 703 300 berilgan), "to'lanmagan" emas */}
                        {r.amount - r.paid_amount >= 1000 && (
                          <span className="ml-2 text-[10px] uppercase tracking-wide bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded">
                            {/* Qisman berilgani ham ko'rinsin (2026-10-12) */}
                            {r.paid_amount > 0
                              ? `qisman · ${formatSom(r.paid_amount)}`
                              : "to'lanmagan"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{r.branch || "—"}</td>
                      <td className="px-4 py-3 text-right text-slate-600">
                        {r.groups.length}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600">{r.students}</td>
                      <td className="px-4 py-3 text-right text-slate-600">{r.lessons}</td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-900">
                        {formatSom(r.amount)}
                      </td>
                    </tr>
                    {open === r.teacher_id &&
                      r.groups.map((g) => (
                        <tr key={`${r.teacher_id}-${g.group_id}`} className="bg-slate-50/60">
                          <td className="px-4 py-2 pl-10 text-slate-500 text-xs">
                            {g.group}
                          </td>
                          <td></td>
                          <td></td>
                          <td className="px-4 py-2 text-right text-slate-500 text-xs">
                            {g.students}
                          </td>
                          <td className="px-4 py-2 text-right text-slate-500 text-xs">
                            {g.taught_lessons}/{g.held_lessons}
                          </td>
                          <td className="px-4 py-2 text-right text-xs">
                            <span className="text-slate-600 mr-2">
                              {formatSom(g.amount)}
                            </span>
                            {g.status === "partial" && !!g.paid_amount && (
                              <span className="text-amber-700 mr-2">
                                berildi {formatSom(g.paid_amount)}
                              </span>
                            )}
                            {/* To'langan guruh — faqat belgi: pul Xarajatlar
                                yoki ustoz kartasida, o'chirish o'sha yerdan */}
                            {g.paid ? (
                              <span className="rounded-md px-2 py-0.5 font-medium bg-green-50 text-green-700">
                                To'landi
                              </span>
                            ) : data.can_pay ? (
                              <button
                                disabled={paying === `${r.teacher_id}-${g.group_id}`}
                                onClick={(ev) => {
                                  ev.stopPropagation();
                                  payGroup(r.teacher_id, g);
                                }}
                                title="Bosilsa qolgan summa ustozga berildi deb yoziladi"
                                className="rounded-md px-2 py-0.5 font-medium bg-slate-200 text-slate-600 hover:bg-slate-300 disabled:opacity-50"
                              >
                                {g.status === "partial" ? "Qisman" : "To'lanmagan"}
                              </button>
                            ) : (
                              <span className="rounded-md px-2 py-0.5 font-medium bg-slate-200 text-slate-600">
                                {g.status === "partial" ? "Qisman" : "To'lanmagan"}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                  </>
                ))}
                <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
                  <td className="px-4 py-3 text-slate-700" colSpan={5}>
                    Jami
                  </td>
                  <td className="px-4 py-3 text-right">{formatSom(data.total)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <Note>
            Ustoz nomini bossangiz guruhlar bo'yicha taqsimoti ochiladi.
            "To'landi" — ustozga shu oy uchun berilgan puldan (Xarajatlar →
            Oylik, ustoz kartasi — qayerdan berilgan bo'lsa ham). Berilmagan
            guruhni shu yerdan "To'landi" qilsangiz, qolgan summa ustoz
            kartasiga yoziladi. Foyda-zararga ustoz oyligi yo'qlamadan
            hisoblangan summa bo'lib bir marta tushadi.
          </Note>
        </>
      )}
    </div>
  );
}



/**
 * Ustoz oyligi O'QUVCHI KESIMIDA (Jahongir, 2026-08-13: "har bir
 * o'quvchidan qancha summa nechta yo'qlama qoyganligi to'liq
 * korinib tursin"). Ustoz nomini bosganda o'quvchilar ochiladi.
 */
type SalStudent = {
  student_id: number; student: string; status?: string | null;
  groups: string; attendances: number; present: number;
  absent: number; amount: number;
};
type SalRow = {
  teacher_id: number; teacher: string; branch?: string | null;
  lessons: number; attendances: number; students_count: number;
  amount: number; per_attendance: number; students: SalStudent[];
};

export function SalaryDetailTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<{
    period: string; rows: SalRow[]; total: number; attendances: number;
    hint: string;
  } | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<typeof d>(
        `/reports/teacher-salary-detail?year=${year}&month=${month}`)
      .then(setD)
      .catch(() => setD(null))
      .finally(() => setLoading(false));
  }, [year, month]);

  const years = [now.getFullYear(), now.getFullYear() - 1];

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>{m}</option>
          ))}
        </select>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
        >
          {years.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        {d && (
          <span className="text-sm text-slate-500">
            Jami{" "}
            <span className="font-semibold text-slate-800">
              {formatSom(d.total)}
            </span>{" "}
            · {d.attendances} ta yo'qlama
          </span>
        )}
        <div className="flex-1" />
        {d && d.rows.length > 0 && (
          <button
            onClick={() =>
              exportToExcel(
                `Ustoz-oyligi-${d.period}`, "Oylik",
                d.rows.flatMap((r) =>
                  r.students.map((s) => ({
                    Ustoz: r.teacher,
                    Filial: r.branch || "",
                    "O'quvchi": s.student,
                    Guruh: s.groups,
                    "Yo'qlama": s.attendances,
                    Keldi: s.present,
                    Kelmadi: s.absent,
                    Summa: s.amount,
                  }))))
            }
            className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
          >
            Excel
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>
      ) : !d || d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8">
          Bu oyda hisoblangan oylik yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <div key={r.teacher_id}
                 className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <button
                onClick={() =>
                  setOpen(open === r.teacher_id ? null : r.teacher_id)}
                className="w-full flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-slate-50 text-left"
              >
                <span className="text-sm font-medium text-slate-800">
                  {r.teacher}
                </span>
                {r.branch && (
                  <span className="text-xs text-slate-400">{r.branch}</span>
                )}
                <span className="flex-1" />
                <span className="text-xs text-slate-500">
                  {r.students_count} o'quvchi · {r.attendances} yo'qlama
                  · {r.lessons} dars
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {formatSom(r.amount)}
                </span>
              </button>

              {open === r.teacher_id && (
                <div className="border-t border-slate-100 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium">O'quvchi</th>
                        <th className="text-left px-4 py-2 font-medium">Guruh</th>
                        <th className="text-right px-4 py-2 font-medium">Yo'qlama</th>
                        <th className="text-right px-4 py-2 font-medium">Keldi</th>
                        <th className="text-right px-4 py-2 font-medium">Kelmadi</th>
                        <th className="text-right px-4 py-2 font-medium">Summa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.students.map((s) => (
                        <tr key={s.student_id}
                            className="border-t border-slate-100">
                          <td className="px-4 py-2">
                            <Link to={`/students/${s.student_id}`}
                                  className="text-slate-800 hover:text-brand-700">
                              {s.student}
                            </Link>
                          </td>
                          <td className="px-4 py-2 text-slate-500">
                            {s.groups}
                          </td>
                          <td className="px-4 py-2 text-right text-slate-700">
                            {s.attendances}
                          </td>
                          <td className="px-4 py-2 text-right text-emerald-700">
                            {s.present}
                          </td>
                          <td className="px-4 py-2 text-right text-red-600">
                            {s.absent}
                          </td>
                          <td className="px-4 py-2 text-right font-medium text-slate-900">
                            {formatSom(s.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="text-xs text-slate-400 px-4 py-2">
                    Bir yo'qlama narxi ≈ {formatSom(r.per_attendance)}
                  </p>
                </div>
              )}
            </div>
          ))}
          <p className="text-xs text-slate-400">{d.hint}</p>
        </div>
      )}
    </div>
  );
}

