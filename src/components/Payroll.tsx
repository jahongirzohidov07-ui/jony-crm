import { ExaminerPayAdminTab } from "../pages/ExaminerPay";
import { useEffect, useState } from "react";
import { formatPhone } from "./PhoneInput";
import { TeacherPayrollTab, SalaryDetailTab } from "./TeacherPayroll";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";
import { PayEditModal, type PayEditTarget } from "./PayEditModal";
import { QuickPayment } from "./QuickPayment";
import { PAYMENT_EDIT, FINANCE_ACCESS, can } from "../lib/roles";
import { Wallet, Check, Trash2, Search, Download, Pencil } from "lucide-react";
import {
  api,
  type StaffPayrollList,
  type StaffPayrollRow,
  type StaffSalaryHistory,
  type MonthPayments,
  type StaffGrades,
  type AdminKpiResult,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { MONTHS } from "../lib/expenses";
import { exportToExcel } from "../lib/exportXlsx";

const now = new Date();

/** Oy va yilni tanlash — uchala bo'limda bir xil ko'rinadi. */
function PeriodPicker({
  year, month, onYear, onMonth,
}: {
  year: number;
  month: number;
  onYear: (v: number) => void;
  onMonth: (v: number) => void;
}) {
  const years = [now.getFullYear(), now.getFullYear() - 1];
  return (
    <div className="flex gap-2">
      <select
        value={month}
        onChange={(e) => onMonth(Number(e.target.value))}
        className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
      >
        {MONTHS.map((m, i) => (
          <option key={m} value={i + 1}>{m}</option>
        ))}
      </select>
      <select
        value={year}
        onChange={(e) => onYear(Number(e.target.value))}
        className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
      >
        {years.map((y) => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>
    </div>
  );
}

/**
 * Bitta xodimga oylik berish oynasi. Summa avtomat "qoldiq" bilan
 * to'ldiriladi — eng ko'p uchraydigan holat shu, bir bosishda tugaydi.
 */
function PayModal({
  row, period, kinds, onClose, onDone,
}: {
  row: StaffPayrollRow;
  period: string;
  kinds: { key: string; label: string }[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [amount, setAmount] = useState(String(Math.max(0, row.left)));
  const [kind, setKind] = useState("salary");
  const [method, setMethod] = useState("cash");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [hist, setHist] = useState<StaffSalaryHistory | null>(null);

  function loadHist() {
    if (!row.user_id) return;
    api
      .get<StaffSalaryHistory>(
        `/staff-salary?user_id=${row.user_id}&period=${period}`
      )
      .then(setHist)
      .catch(() => setHist(null));
  }
  useEffect(loadHist, [row.user_id, period]);

  async function save() {
    setBusy(true);
    setErr("");
    try {
      await api.post("/staff-salary", {
        user_id: row.user_id,
        amount: Number(amount),
        kind,
        method,
        period,
        note,
      });
      onDone();
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Bu yozuv o'chirilsinmi?")) return;
    try {
      await api.delete(`/staff-salary/${id}`);
      loadHist();
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <h3 className="font-semibold text-slate-900 mb-0.5">
          {row.name} — oylik berish
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          {period} · hisoblangan {formatSom(row.salary)} · berilgan{" "}
          {formatSom(row.paid)} · qoldiq{" "}
          <b className={row.left > 0 ? "text-red-600" : "text-emerald-600"}>
            {formatSom(row.left)}
          </b>
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Summa (so'm) *
            </label>
            <input
              type="number"
              autoFocus
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Turi
              </label>
              <select
                value={kind}
                onChange={(e) => setKind(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                {kinds.map((k) => (
                  <option key={k.key} value={k.key}>{k.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Usul
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                <option value="cash">Naqd</option>
                <option value="card">Click</option>
                <option value="terminal">Terminal</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Izoh
            </label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Ixtiyoriy"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {hist && hist.rows.length > 0 && (
          <div className="mt-4 border-t border-slate-100 pt-3">
            <p className="text-xs font-medium text-slate-600 mb-2">
              Shu oyda berilgan:
            </p>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {hist.rows.map((h) => (
                <div
                  key={h.id}
                  className="flex items-center justify-between text-xs text-slate-600"
                >
                  <span>
                    {h.date && formatDate(h.date)} · {h.kind_label}
                    {h.note && ` · ${h.note}`}
                  </span>
                  <span className="flex items-center gap-2">
                    <b className="text-slate-800">{formatSom(h.amount)}</b>
                    {hist.can_pay && (
                      <button
                        onClick={() => remove(h.id)}
                        className="text-slate-400 hover:text-red-600"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {err && <p className="text-sm text-red-600 mt-3">{err}</p>}

        <div className="flex gap-2 mt-5">
          <button
            onClick={save}
            disabled={busy || !Number(amount)}
            className="flex-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
          >
            {busy ? "Saqlanmoqda…" : "Berildi"}
          </button>
          <button
            onClick={onClose}
            className="px-4 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Examiner yoki support teacher oyliklari jadvali. Har qatorda
 * "To'lash" tugmasi — Moliya bo'limidan chiqmasdan oylik beriladi.
 */
function PayrollTable({ url, title, hint }: {
  url: string;
  title: string;
  hint: string;
}) {
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<StaffPayrollList | null>(null);
  const [err, setErr] = useState("");
  const [pay, setPay] = useState<StaffPayrollRow | null>(null);

  function load() {
    setErr("");
    api
      .get<StaffPayrollList>(`${url}?year=${year}&month=${month}`)
      .then(setD)
      .catch((e) => {
        setD(null);
        setErr(e instanceof Error ? e.message : "Xatolik");
      });
  }
  useEffect(load, [url, year, month]);

  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <p className="text-sm font-medium text-slate-800">{title}</p>
          <p className="text-xs text-slate-500">
            {d.period} · hisoblangan{" "}
            <b className="text-slate-800">{formatSom(d.total)}</b> · berilgan{" "}
            <b className="text-emerald-600">{formatSom(d.paid_total)}</b> ·
            qoldiq{" "}
            <b className="text-red-600">{formatSom(d.left_total)}</b>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <PeriodPicker
            year={year} month={month} onYear={setYear} onMonth={setMonth}
          />
          <button
            onClick={() =>
              exportToExcel(`${title}-${d.period}`, title, d.rows.map((r) => ({
                "F.I.Sh.": r.name,
                Daraja: r.grade_label ?? "",
                Hisoblangan: r.salary,
                Berilgan: r.paid,
                Qoldiq: r.left,
              })))
            }
            className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
          >
            <Download size={14} /> Excel
          </button>
        </div>
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Bu oyda xodim topilmadi.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">F.I.Sh.</th>
                <th className="text-left px-3 py-2.5 font-medium w-32">
                  Daraja
                </th>
                <th className="text-right px-3 py-2.5 font-medium">
                  Hisoblangan
                </th>
                <th className="text-right px-3 py-2.5 font-medium">Berilgan</th>
                <th className="text-right px-3 py-2.5 font-medium">Qoldiq</th>
                <th className="px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {d.rows.map((r) => (
                <tr
                  key={r.user_id ?? r.teacher_id ?? r.name}
                  className="border-t border-slate-100"
                >
                  <td className="px-4 py-2.5">
                    <p className="text-slate-900">{r.name}</p>
                    <p className="text-xs text-slate-400">
                      {r.exam_count !== undefined
                        ? `${r.exam_count} imtihon · ${r.points} ball`
                        : `${r.hours ?? 0} soat · ${r.students ?? 0} o'quvchi`}
                    </p>
                  </td>
                  <td className="px-3 py-2.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        r.grade === "volunteer"
                          ? "bg-slate-100 text-slate-500"
                          : r.grade === "senior"
                          ? "bg-emerald-50 text-emerald-700"
                          : r.grade === "middle"
                          ? "bg-sky-50 text-sky-700"
                          : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      {r.grade_label || "—"}
                    </span>
                    {r.grade_coef !== undefined && r.grade_coef !== 1 && (
                      <span className="text-[11px] text-slate-400 ml-1">
                        x{r.grade_coef}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right text-slate-800">
                    {formatSom(r.salary)}
                    {r.grade === "volunteer" ? (
                      <p className="text-[11px] text-slate-400">
                        volontyor — oylik yo'q
                      </p>
                    ) : r.salary_base !== undefined &&
                      r.salary_base !== r.salary ? (
                      <p className="text-[11px] text-slate-400">
                        baza {formatSom(r.salary_base)}
                      </p>
                    ) : null}
                    {(r.clamped_min || r.clamped_max) && (
                      <span className="text-xs text-amber-600 ml-1">
                        ({r.clamped_min ? "min" : "max"})
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right text-emerald-600">
                    {r.paid ? formatSom(r.paid) : "—"}
                  </td>
                  <td
                    className={`px-3 py-2.5 text-right font-medium ${
                      r.left > 0 ? "text-red-600" : "text-emerald-600"
                    }`}
                  >
                    {r.left <= 0 ? (
                      <span className="inline-flex items-center gap-1">
                        <Check size={13} /> To'landi
                      </span>
                    ) : (
                      formatSom(r.left)
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    {d.can_pay && r.user_id && r.grade !== "volunteer" && (
                      <button
                        onClick={() => setPay(r)}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 text-xs font-medium"
                      >
                        <Wallet size={13} /> Oylik berish
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-400 mt-3 max-w-3xl">{hint}</p>

      {pay && (
        <PayModal
          row={pay}
          period={d.period}
          kinds={d.kinds || [{ key: "salary", label: "Oylik" }]}
          onClose={() => setPay(null)}
          onDone={load}
        />
      )}
    </div>
  );
}

/** Moliya > Oyliklar: ustoz, examiner, support va ma'muriy xodimlar
 *  oyliklari BIR JOYDA (2026-08-20, Jahongir: "oyliklar bo'limini
 *  hisobotlardan moliyaga olib o't"). Ustoz oyligi va uning o'quvchi
 *  kesimidagi tafsiloti ilgari Hisobotlar sahifasida edi. */
export function PayrollTab() {
  type Sub = "teacher" | "teacher_detail" | "examiner" | "support"
    | "staff" | "grades";
  const { user } = useAuth();
  // Ustoz oyligi ilgari Hisobotlar sahifasida edi va u yerni faqat
  // moliya ko'rardi — ko'chirishda HUQUQ KENGAYIB KETMASLIGI uchun
  // shu ikki bo'lim ham FINANCE_ACCESS bilan yopiladi. HR va o'quv
  // rahbari avvalgidek faqat examiner/support oyligini ko'radi.
  const finance = can(user?.role, FINANCE_ACCESS);
  const [sub, setSub] = useState<Sub>(finance ? "teacher" : "examiner");
  const SUBS: { key: Sub; label: string }[] = [
    ...(finance ? [
      { key: "teacher" as Sub, label: "Ustozlar oyligi" },
      // 2026-08-13, Jahongir: "har bir o'quvchidan qancha summa nechta
      // yo'qlama qoyganligi to'liq korinib turadigan"
      { key: "teacher_detail" as Sub, label: "O'quvchi kesimida" },
    ] : []),
    { key: "examiner", label: "Examiner oyliklari" },
    { key: "support", label: "Support teacher oyliklari" },
    // 2026-08-12, Jahongir: Moliya > Xarajatlardan "Oylik" berilsa,
    // shu yerda ham ko'rinib tursin.
    { key: "staff", label: "Ma'muriy xodimlar" },
    { key: "grades", label: "Darajalar" },
  ];

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 mb-5">
        {SUBS.map((s) => (
          <button
            key={s.key}
            onClick={() => setSub(s.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              sub === s.key
                ? "bg-brand-600 text-white"
                : "bg-white border border-slate-200 text-slate-600 hover:border-brand-300"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {sub === "teacher" ? (
        <TeacherPayrollTab />
      ) : sub === "teacher_detail" ? (
        <SalaryDetailTab />
      ) : sub === "examiner" ? (
        <>
          <PayrollTable
            url="/examiners/salary"
            title="Examiner oyliklari"
            hint="Oylik o'tkazilgan imtihonlardan avtomat hisoblanadi:
                  daraja bo'yicha baza ball + qatnashgan o'quvchi. Jarima va
                  qo'lda ayirilgan ballar chegiriladi. Volontyorga oylik
                  berilmaydi."
          />
          {/* Har examiner: qaysi imtihonlar, ball va oylik qayerdan
              chiqdi — jadval ko'rinishida (2026-10-02) */}
          <div className="mt-6">
            <p className="text-sm font-medium text-slate-700 mb-2">
              Imtihonlar kesimida (examinerni bosing)
            </p>
            <ExaminerPayAdminTab />
          </div>
        </>
      ) : sub === "support" ? (
        <PayrollTable
          url="/support/salary"
          title="Support teacher oyliklari"
          hint="Oylik seanslardan avtomat hisoblanadi: (soat x 0.30 +
                o'quvchi x 0.20 + test koef x 0.50) x 10 000 so'm.
                Volontyorga oylik berilmaydi."
        />
      ) : sub === "staff" ? (
        <StaffSalaryTable />
      ) : (
        <StaffGradesTab />
      )}
    </div>
  );
}

/**
 * Ma'muriy xodimlarga berilgan oyliklar — Moliya > Xarajatlar
 * bo'limidan "Oylik" tanlab kiritilganlari (Jahongir, 2026-08-12:
 * "nargi tomonlardagi joylarda ham oylik berilganligi korinsin").
 * Ustozlarniki bu yerda emas: ular o'z oylik kartasida.
 */
function StaffSalaryTable() {
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  // 2026-08-30, Jahongir: "ma'muriy xodimlar oyligi degan joyda
  // BULAR HAM KO'RINISHI KERAK" — adminning KPI'si (fiks + eski
  // to'lov yig'ish bonusi + o'zi olib kelgan yangi mijozlar bonusi).
  // Ilgari bu faqat Hisobotlar > Adminlar KPI da turardi, oylik
  // berayotgan odam ikki joyni ochib solishtirishga majbur edi.
  const [kpi, setKpi] = useState<AdminKpiResult | null>(null);
  const [d, setD] = useState<{
    rows: {
      id: number; date: string; name: string; role_label: string;
      amount: number; method_label?: string | null;
      branch?: string | null; note?: string | null;
      created_by?: string | null;
    }[];
    total: number; count: number;
  } | null>(null);

  useEffect(() => {
    api
      .get<typeof d>(`/expenses/staff-salaries?year=${year}&month=${month}`)
      .then(setD)
      .catch(() => setD(null));
    api
      .get<AdminKpiResult>(`/kpi/admins?year=${year}&month=${month}`)
      .then(setKpi)
      .catch(() => setKpi(null));
  }, [year, month]);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <PeriodPicker
          year={year} month={month} onYear={setYear} onMonth={setMonth}
        />
        <span className="text-sm text-slate-500">
          {d ? `${d.count} ta to'lov · ${formatSom(d.total)}` : ""}
        </span>
      </div>

      {/* ---- HISOBLANGAN OYLIK (KPI) ---- */}
      {kpi && kpi.rows.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-bold text-slate-800 mb-1">
            Hisoblangan oylik — administratorlar
          </h3>
          <p className="text-xs text-slate-500 mb-3">
            Fiks + eski to'lovlarni yig'ish bonusi (filial ko'rsatkichi)
            + o'zi olib kelgan yangi mijozlar bonusi (shaxsiy).
          </p>
          <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Xodim</th>
                  <th className="text-left px-4 py-3 font-medium">Filial</th>
                  <th className="text-right px-4 py-3 font-medium">Fiks</th>
                  <th className="text-right px-4 py-3 font-medium">
                    Yig'ish
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    Yangi mijoz
                  </th>
                  <th className="text-right px-4 py-3 font-medium">Jami</th>
                  <th className="text-right px-4 py-3 font-medium">Berildi</th>
                </tr>
              </thead>
              <tbody>
                {kpi.rows.map((r) => {
                  // Shu xodimga shu oyda haqiqatda berilgan oylik
                  const berildi = (d?.rows || [])
                    .filter((x) => x.name === r.full_name)
                    .reduce((a, x) => a + x.amount, 0);
                  return (
                    <tr key={r.user_id} className="border-t border-slate-100">
                      <td className="px-4 py-3 text-slate-800">
                        {r.full_name}
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {r.branch || "—"}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600">
                        {formatSom(r.fix_salary)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={r.collection_bonus > 0
                          ? "text-emerald-600 font-medium" : "text-slate-400"}>
                          {r.collection_bonus > 0
                            ? `+${formatSom(r.collection_bonus)}` : "—"}
                        </span>
                        <span className="block text-[11px] text-slate-400">
                          {r.collection_percent}% (filial)
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={r.new_client_bonus > 0
                          ? "text-emerald-600 font-medium" : "text-slate-400"}>
                          {r.new_client_bonus > 0
                            ? `+${formatSom(r.new_client_bonus)}` : "—"}
                        </span>
                        <span className="block text-[11px] text-slate-400">
                          {r.new_clients} ta o'zi
                          {(r.branch_new_clients ?? 0) > r.new_clients
                            ? ` / ${r.branch_new_clients} filialda` : ""}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-900">
                        {formatSom(r.total)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={berildi >= r.total && r.total > 0
                          ? "text-emerald-600" : "text-slate-500"}>
                          {berildi ? formatSom(berildi) : "—"}
                        </span>
                        {r.total > 0 && berildi < r.total && (
                          <span className="block text-[11px] text-amber-600">
                            {formatSom(r.total - berildi)} qoldi
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <h3 className="text-sm font-bold text-slate-800 mb-3">
        Berilgan oyliklar
      </h3>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Sana</th>
              <th className="text-left px-4 py-3 font-medium">Xodim</th>
              <th className="text-left px-4 py-3 font-medium">Lavozim</th>
              <th className="text-left px-4 py-3 font-medium">Filial</th>
              <th className="text-left px-4 py-3 font-medium">Usul</th>
              <th className="text-left px-4 py-3 font-medium">Kim berdi</th>
              <th className="text-right px-4 py-3 font-medium">Summa</th>
            </tr>
          </thead>
          <tbody>
            {(!d || d.rows.length === 0) && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                  Bu oyda ma'muriy xodimlarga oylik berilmagan.
                </td>
              </tr>
            )}
            {d?.rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-600">{formatDate(r.date)}</td>
                <td className="px-4 py-3 text-slate-800">{r.name}</td>
                <td className="px-4 py-3 text-slate-500">{r.role_label}</td>
                <td className="px-4 py-3 text-slate-500">{r.branch || "—"}</td>
                <td className="px-4 py-3 text-slate-500">
                  {r.method_label || "—"}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {r.created_by || "—"}
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-800">
                  {formatSom(r.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Moliya > Shu oy to'lovlari. Administrator har kuni "kim to'ladi?"
 * deb so'raydi — ro'yxat shu yerda turadi.
 */
export function MonthPaymentsTab() {
  const { user } = useAuth();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<MonthPayments | null>(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  // Dashboard "Shu oy yangi to'lovlar" kartasidan ?filter=new bilan
  // kelganda darhol yangi to'lovlar filtri yoqilgan holda ochiladi.
  const [spq] = useSearchParams();
  const _f = spq.get("filter");
  const [only, setOnly] = useState<"all" | "new" | "old">(
    _f === "new" ? "new" : _f === "old" ? "old" : "all");
  // Xato kiritilgan to'lovni to'g'rilash (summa, naqd/plastik, izoh)
  const canPayEdit = can(user?.role, PAYMENT_EDIT);
  const [editing, setEditing] = useState<PayEditTarget | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    setErr("");
    api
      .get<MonthPayments>(`/payments/month?year=${year}&month=${month}`)
      .then(setD)
      .catch((e) => {
        setD(null);
        setErr(e instanceof Error ? e.message : "Xatolik");
      });
  }, [year, month, reloadKey]);

  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const needle = q.trim().toLowerCase();
  const rows = d.rows.filter((r) => {
    if (only === "new" && !r.is_new) return false;
    if (only === "old" && r.is_new) return false;
    if (!needle) return true;
    return (
      r.student.toLowerCase().includes(needle) ||
      (r.phone || "").includes(needle)
    );
  });

  const FILTERS: { key: "all" | "new" | "old"; label: string }[] = [
    { key: "all", label: `Hammasi (${d.count})` },
    { key: "new", label: "Yangi mijoz" },
    { key: "old", label: "Eski to'lov" },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        {[
          { l: "Jami tushum", v: formatSom(d.total), c: "text-slate-900" },
          { l: "To'lovlar soni", v: String(d.count), c: "text-slate-900" },
          {
            l: "Yangi mijozlardan", v: formatSom(d.new_total),
            c: "text-brand-700",
          },
          {
            l: "Eski to'lovlardan", v: formatSom(d.old_total),
            c: "text-emerald-600",
          },
        ].map((s) => (
          <div
            key={s.l}
            className="bg-white rounded-xl border border-slate-200 p-4"
          >
            <p className="text-xs text-slate-500 mb-1">{s.l}</p>
            <p className={`text-lg font-semibold ${s.c}`}>{s.v}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative">
          <Search
            size={15}
            className="absolute left-2.5 top-2.5 text-slate-400"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="O'quvchi yoki telefon"
            className="rounded-lg border border-slate-300 pl-8 pr-3 py-1.5 text-sm w-56"
          />
        </div>
        <div className="flex gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setOnly(f.key)}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                only === f.key
                  ? "bg-brand-600 text-white"
                  : "bg-white border border-slate-200 text-slate-600"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <PeriodPicker
          year={year} month={month} onYear={setYear} onMonth={setMonth}
        />
        {/* Shu oy to'lovlari - administrator eng ko'p ochadigan ro'yxat.
            Yangi to'lovni shu yerdan kiritadi (Jahongir, 2026-08-12). */}
        <QuickPayment onDone={() => setReloadKey((k) => k + 1)} />
        <button
          onClick={() =>
            exportToExcel(`Tolovlar-${d.period}`, "To'lovlar", rows.map((r) => ({
              Sana: r.date || "",
              "O'quvchi": r.student,
              Telefon: r.phone || "",
              Summa: r.amount,
              Usul: r.method_label,
              Turi: r.is_new ? "Yangi mijoz" : "Eski to'lov",
              Filial: r.branch,
              "Qabul qilgan": r.created_by || "",
            })))
          }
          className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
        >
          <Download size={14} /> Excel
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Bu oyda to'lov yo'q.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">Sana</th>
                <th className="text-left px-3 py-2.5 font-medium">O'quvchi</th>
                <th className="text-right px-3 py-2.5 font-medium">Summa</th>
                <th className="text-left px-3 py-2.5 font-medium">Usul</th>
                <th className="text-left px-3 py-2.5 font-medium">Turi</th>
                <th className="text-left px-3 py-2.5 font-medium">
                  Qabul qilgan
                </th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">
                    {r.date && formatDate(r.date)}
                  </td>
                  <td className="px-3 py-2.5">
                    <p className="text-slate-900">{r.student}</p>
                    {r.phone && (
                      <p className="text-xs text-slate-400">{formatPhone(r.phone)}</p>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right font-medium text-emerald-600 whitespace-nowrap">
                    {formatSom(r.amount)}
                  </td>
                  <td className="px-3 py-2.5 text-slate-600">
                    {r.method_label}
                  </td>
                  <td className="px-3 py-2.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        r.is_new
                          ? "bg-brand-100 text-brand-700"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {r.is_new ? "Yangi mijoz" : "Eski to'lov"}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-slate-500">
                    {r.created_by || "—"}
                  </td>
                  <td className="px-2 py-2.5 text-right">
                    {canPayEdit && (
                      <button
                        onClick={() =>
                          setEditing({
                            kind: "payment",
                            id: r.id,
                            amount: r.amount,
                            method: r.method,
                            note: r.note,
                            title: r.student,
                          })
                        }
                        className="text-slate-300 hover:text-brand-600"
                        title="Tahrirlash (summa, usul, izoh)"
                      >
                        <Pencil size={13} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <PayEditModal
          target={editing}
          onClose={() => setEditing(null)}
          onSaved={() => setReloadKey((k) => k + 1)}
        />
      )}
    </div>
  );
}

// ------------------------------------------- Darajalar (Volontyor...) ----

/** Examiner va support teacherlarning darajasi.
 *
 *  Volontyorga oylik berilmaydi — bu tajriba to'plash bosqichi.
 *  Junior/Middle/Senior darajalarida hisoblangan oylik
 *  koeffitsiyentga ko'paytiriladi (koeffitsiyentni asoschi
 *  o'zgartiradi). */
export function StaffGradesTab() {
  const [d, setD] = useState<StaffGrades | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [err, setErr] = useState("");
  const [coefs, setCoefs] = useState<Record<string, string>>({});

  const load = () => {
    api
      .get<StaffGrades>("/staff-grades")
      .then((x) => {
        setD(x);
        setCoefs(
          Object.fromEntries(x.grades.map((g) => [g.key, String(g.coef)]))
        );
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  async function setGrade(uid: number, grade: string) {
    setBusy(uid);
    setErr("");
    try {
      await api.put(`/staff-grades/${uid}`, { grade });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  async function saveCoefs() {
    setErr("");
    try {
      await api.put("/staff-grades", {
        rates: Object.entries(coefs).map(([key, v]) => ({
          key,
          coef: Number(v.replace(",", ".")) || 0,
        })),
      });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (err && !d) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <p className="text-xs text-slate-500 mb-4 max-w-3xl">{d.hint}</p>

      {err && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
          {err}
        </p>
      )}

      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
        <p className="text-sm font-medium text-slate-800 mb-2">
          Daraja koeffitsiyentlari
        </p>
        <div className="flex flex-wrap items-end gap-3">
          {d.grades.map((g) => (
            <div key={g.key}>
              <label className="block text-xs text-slate-500 mb-1">
                {g.label}
              </label>
              <input
                value={coefs[g.key] ?? ""}
                onChange={(e) =>
                  setCoefs((c) => ({ ...c, [g.key]: e.target.value }))
                }
                disabled={!d.can_edit_rates}
                className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
              />
            </div>
          ))}
          {d.can_edit_rates && (
            <button
              onClick={saveCoefs}
              className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-sm font-medium"
            >
              Saqlash
            </button>
          )}
        </div>
        <p className="text-xs text-slate-400 mt-2">
          0 — oylik berilmaydi. 1 — hisoblangan oylikning o'zi. 1.3 —
          30% ustama. Koeffitsiyentni faqat asoschi o'zgartiradi.
        </p>
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Examiner yoki support teacher topilmadi.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">F.I.Sh.</th>
                <th className="text-left px-3 py-2.5 font-medium w-40">
                  Lavozim
                </th>
                <th className="text-left px-3 py-2.5 font-medium w-32">
                  Berilgan sana
                </th>
                <th className="text-left px-3 py-2.5 font-medium">Daraja</th>
              </tr>
            </thead>
            <tbody>
              {d.rows.map((r) => (
                <tr key={r.user_id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-900">{r.name}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">
                    {r.role}
                  </td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">
                    {r.since ? formatDate(r.since) : "—"}
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex flex-wrap gap-1.5">
                      {d.grades.map((g) => {
                        const on = r.grade === g.key;
                        return (
                          <button
                            key={g.key}
                            onClick={() => setGrade(r.user_id, g.key)}
                            disabled={!d.can_edit || busy === r.user_id || on}
                            className={`px-2.5 py-1 rounded-full text-xs border transition disabled:cursor-default ${
                              on
                                ? g.key === "volunteer"
                                  ? "bg-slate-500 border-slate-500 text-white"
                                  : "bg-brand-600 border-brand-600 text-white"
                                : "bg-white border-slate-200 text-slate-500 hover:border-brand-300 disabled:opacity-40"
                            }`}
                          >
                            {g.label}
                            {g.coef !== 1 && (
                              <span className="opacity-70"> x{g.coef}</span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
