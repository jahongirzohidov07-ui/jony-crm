import { useEffect, useState } from "react";
import { Wallet, Info, MinusCircle, Download } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { exportToExcel } from "../lib/exportXlsx";
import { branchQs } from "../components/BranchPicker";

const MONTHS_UP = ["YANVAR", "FEVRAL", "MART", "APREL", "MAY", "IYUN",
  "IYUL", "AVGUST", "SENTABR", "OKTABR", "NOYABR", "DEKABR"];
const MONTHS = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"];

/** Oy tanlagich (oxirgi 12 oy). */
function MonthPicker({ value, onChange }: {
  value: string; onChange: (v: string) => void;
}) {
  const now = new Date();
  const opts = Array.from({ length: 12 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const v = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    return { v, l: `${MONTHS[d.getMonth()]} ${d.getFullYear()}` };
  });
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white">
      {opts.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}

const thisMonth = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};
const qs = (period: string) =>
  `?year=${Number(period.slice(0, 4))}&month=${Number(period.slice(5, 7))}`;

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * Examiner oyligi — imtihonlar kesimida ball tizimi.
 *
 * Har o'tkazilgan imtihon: daraja balli + o'quvchi soni x koeffitsiyent.
 * Jarimalar (LC UP, Coin, jadval kechikishi) va qo'lda ayirilgan ballar
 * minus. Oy yakuni: ball x 1 000 so'm, 400 000 — 1 500 000 chegarada.
 */

const fmt = (n: Any) =>
  Number(n || 0).toLocaleString().replace(/,/g, " ");

function SalaryCard({ d }: { d: Any }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <Wallet size={15} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">
          {d.volunteer
            ? `Shu oygi ishim (${d.period})`
            : `Shu oygi oylik — avtomat (${d.period})`}
        </p>
      </div>
      {/* Volontyorga oylik hisoblanmaydi (2026-09-23, Jahongir) */}
      {d.volunteer ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 mb-1">
          <p className="text-sm font-medium text-amber-900">
            Volontyor bosqichi — oylik hisoblanmaydi
          </p>
          {d.volunteer_hint && (
            <p className="text-xs text-amber-800 mt-1">{d.volunteer_hint}</p>
          )}
        </div>
      ) : (
        <p className="text-3xl font-semibold text-slate-900 mb-1">
          {fmt(d.salary)}{" "}
          <span className="text-base font-normal text-slate-400">so'm</span>
        </p>
      )}
      {d.clamped_min && (
        <p className="text-xs text-amber-600 mb-1">
          Hisob {fmt(d.raw)} chiqdi — eng kam oylik {fmt(d.min)} to'lanadi.
        </p>
      )}
      {d.clamped_max && (
        <p className="text-xs text-amber-600 mb-1">
          Hisob yuqori chegaradan oshdi — {fmt(d.max)} to'lanadi.
        </p>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
        <div className="rounded-lg border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Imtihonlar</p>
          <p className="text-lg font-semibold text-slate-900">
            {d.exam_count}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Yig'ilgan ball</p>
          <p className="text-lg font-semibold text-emerald-700">
            +{d.base_points}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Jarima + ayirmalar</p>
          <p className="text-lg font-semibold text-red-600">
            −{(d.penalty_points + d.adjustment_points).toFixed(2)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Sof ball</p>
          <p className="text-lg font-semibold text-slate-900">{d.points}</p>
          {!d.volunteer && (
            <p className="text-xs text-slate-400">x 1 000 so'm</p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * EXAMINER JADVALI (2026-10-02, Jahongir: "har bir examinerning oyligini
 * shunaqa nechta imtihon oldi va qancha oylik qayerdan chiqdi ko'rinishi
 * kerak") — Excel'dagi "MUHAMMADHAYOT / SENTABR / STRETINKO" jadvali
 * ko'rinishida, pastida ball -> oylik hisobi.
 */
export function ExamSheet({ d, name }: { d: Any; name: string }) {
  const m = Number(String(d.period || "").slice(5, 7));
  const title = [name, MONTHS_UP[m - 1] || d.period,
                 (d.branches || []).join(", ")].filter(Boolean).join(" / ");
  const ded = Number(d.penalty_points || 0) + Number(d.adjustment_points || 0);
  const hasPen = (d.exams || []).some((e: Any) => e.penalty_points > 0);
  const dm = (iso: string) => `${iso.slice(8, 10)}.${iso.slice(5, 7)}`;
  const exportRows = () =>
    exportToExcel(`examiner-${name}-${d.period}`, "Imtihonlar",
      (d.exams || []).map((e: Any, i: number) => ({
        "#": i + 1, EXAM: e.code, STUDENTS: e.students, DATE: dm(e.date),
        TEACHER: e.teacher, GROUP: e.group, BRANCH: e.branch,
        SCORE: e.points, JARIMA: e.penalty_points || 0,
      })));
  const th = "px-3 py-2 font-semibold text-slate-700 border border-slate-300";
  const td = "px-3 py-1.5 border border-slate-200";
  return (
    <div className="bg-white border border-slate-300 rounded-xl overflow-hidden mb-4">
      <div className="flex items-center gap-2 bg-slate-200 px-4 py-2.5">
        <p className="flex-1 text-center font-semibold tracking-wide text-slate-800 uppercase">
          {title}
        </p>
        <button onClick={exportRows} title="Excel"
                className="flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900">
          <Download size={14} /> Excel
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead className="bg-slate-100 text-xs uppercase">
            <tr>
              <th className={th}>#</th>
              <th className={th}>Exam</th>
              <th className={th}>Students</th>
              <th className={th}>Date</th>
              <th className={`${th} text-left`}>Teacher</th>
              <th className={th}>Group</th>
              <th className={th}>Branch</th>
              <th className={th}>Score</th>
              {hasPen && <th className={`${th} text-red-700`}>Jarima</th>}
            </tr>
          </thead>
          <tbody>
            {(d.exams || []).map((e: Any, i: number) => (
              <tr key={e.exam_id} className="text-center odd:bg-white even:bg-slate-50/60">
                <td className={`${td} text-slate-500`}>{i + 1}</td>
                <td className={`${td} font-semibold text-slate-800 whitespace-nowrap`}
                    title={e.tier_label}>{e.code}</td>
                <td className={`${td} tabular-nums`}>{e.students}</td>
                <td className={`${td} tabular-nums`}>{dm(e.date)}</td>
                <td className={`${td} text-left uppercase whitespace-nowrap`}>{e.teacher}</td>
                <td className={`${td} uppercase whitespace-nowrap`}>{e.group}</td>
                <td className={`${td} uppercase whitespace-nowrap`}>{e.branch}</td>
                <td className={`${td} tabular-nums font-medium`}
                    title={e.points > 0 ? `${e.base} + ${e.students} x ${e.per_student}` : ""}>
                  {String(e.points).replace(".", ",")}
                </td>
                {hasPen && (
                  <td className={`${td} text-red-600 tabular-nums`} title={e.penalty_note || ""}>
                    {e.penalty_points > 0 ? `−${e.penalty_points}` : ""}
                  </td>
                )}
              </tr>
            ))}
            {(d.exams || []).length === 0 && (
              <tr><td colSpan={hasPen ? 9 : 8}
                      className="py-8 text-center text-slate-400">
                Bu oyda o'tkazilgan imtihon yo'q
              </td></tr>
            )}
          </tbody>
          <tfoot>
            <tr className="font-semibold text-center">
              <td colSpan={2} className="px-3 py-2 bg-sky-400 text-white border border-sky-500">
                {d.exam_count} EXAMS
              </td>
              <td className="px-3 py-2 bg-sky-400 text-white border border-sky-500 tabular-nums">
                {d.students_total ?? 0}
              </td>
              <td colSpan={4} className="border border-slate-200" />
              <td className="px-3 py-2 bg-sky-400 text-white border border-sky-500 tabular-nums">
                {String(d.base_points).replace(".", ",")}
              </td>
              {hasPen && (
                <td className="px-3 py-2 text-red-600 border border-slate-200 tabular-nums">
                  −{d.penalty_points}
                </td>
              )}
            </tr>
          </tfoot>
        </table>
      </div>
      {/* Oylik qayerdan chiqdi */}
      <div className="px-4 py-3 border-t border-slate-200 text-sm text-slate-700 space-y-0.5">
        <p>
          Ball jami <b className="tabular-nums">{d.base_points}</b>
          {ded > 0 && <> − jarima va ayirmalar <b className="text-red-600 tabular-nums">{ded.toFixed(2)}</b></>}
          {" "}= sof ball <b className="tabular-nums">{d.points}</b>
        </p>
        {d.volunteer || d.grade_coef === 0 ? (
          <p className="text-amber-700">
            {d.points} ball × {fmt(d.unit || 1000)} so'm = {fmt(d.raw)} so'm, lekin
            volontyor bosqichi — oylik hisoblanmaydi (0 so'm).
          </p>
        ) : (
          <p>
            {d.points} ball × {fmt(d.unit || 1000)} so'm = {fmt(d.raw)} so'm
            {d.clamped_min && <> → eng kam oylik {fmt(d.min)}</>}
            {d.clamped_max && <> → yuqori chegara {fmt(d.max)}</>}
            {d.grade_coef != null && d.grade_coef !== 1 && (
              <> → × {d.grade_coef} ({d.grade_label})</>
            )}
            {" "}= <b className="text-lg text-slate-900">{fmt(d.salary)} so'm</b>
          </p>
        )}
      </div>
    </div>
  );
}

function Adjustments({ d }: { d: Any }) {
  if (!d.adjustments.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
      <p className="text-sm font-medium text-slate-700 mb-2">
        Qo'lda ayirilgan ballar
      </p>
      {d.adjustments.map((a: Any) => (
        <div key={a.id} className="flex items-start gap-2 text-sm py-1.5">
          <MinusCircle size={14} className="text-red-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-medium text-red-600">−{a.points} ball</span>
            <span className="text-slate-500"> — {a.reason}</span>
            <span className="text-xs text-slate-400 ml-1.5">
              {a.date} · {a.created_by}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function RateTable({ d }: { d: Any }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
      <p className="text-sm font-medium text-slate-700 px-4 pt-3 pb-1">
        Ball jadvali
      </p>
      <table className="w-full text-sm">
        <thead className="text-slate-500 text-xs">
          <tr>
            <th className="text-left px-4 py-2 font-medium">Daraja</th>
            <th className="text-right px-3 py-2 font-medium">Imtihon</th>
            <th className="text-right px-3 py-2 font-medium">O'quvchiga</th>
            <th className="text-right px-3 py-2 font-medium">LC UP</th>
            <th className="text-right px-3 py-2 font-medium">Coin</th>
            <th className="text-right px-4 py-2 font-medium">
              Kechikish/soat
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {d.table.map((t: Any) => (
            <tr key={t.tier}>
              <td className="px-4 py-2 text-slate-700">{t.label}</td>
              <td className="px-3 py-2 text-right text-slate-700">
                {t.base}
              </td>
              <td className="px-3 py-2 text-right text-slate-700">
                {t.per_student}
              </td>
              <td className="px-3 py-2 text-right text-red-600">
                −{t.pen_lc_up}
              </td>
              <td className="px-3 py-2 text-right text-red-600">
                −{t.pen_coin}
              </td>
              <td className="px-4 py-2 text-right text-red-600">
                −{t.pen_hour}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Examinerning o'z oyligi (Audit → "Oyligim"). */
export function ExaminerPayTab() {
  const { user } = useAuth();
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [period, setPeriod] = useState(thisMonth());
  useEffect(() => {
    api
      .get<Any>("/me/examiner-salary" + qs(period))
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [period]);
  if (err)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;
  return (
    <div>
      <div className="flex justify-end mb-3">
        <MonthPicker value={period} onChange={setPeriod} />
      </div>
      <SalaryCard d={d} />
      <ExamSheet d={d} name={user?.full_name || ""} />
      <Adjustments d={d} />
      <RateTable d={d} />
      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.volunteer ? d.volunteer_hint : d.hint}
      </p>
    </div>
  );
}

/** Bitta imtihonga jarima belgilash formasi (boshliqlar uchun). */
function PenaltyEditor({
  exam,
  onSaved,
}: {
  exam: Any;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    lc_up: exam.penalty_lc_up,
    coin: exam.penalty_coin,
    delay_hours: String(exam.penalty_delay_hours || ""),
    note: exam.penalty_note || "",
  });
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      await api.post(`/exams/${exam.exam_id}/penalty`, {
        lc_up: f.lc_up,
        coin: f.coin,
        delay_hours: Number(f.delay_hours) || 0,
        note: f.note || null,
      });
      onSaved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs bg-slate-50 rounded-lg px-3 py-2">
      <label className="flex items-center gap-1.5">
        <input
          type="checkbox"
          checked={f.lc_up}
          onChange={(e) => setF({ ...f, lc_up: e.target.checked })}
        />
        LC UP yo'q
      </label>
      <label className="flex items-center gap-1.5">
        <input
          type="checkbox"
          checked={f.coin}
          onChange={(e) => setF({ ...f, coin: e.target.checked })}
        />
        Coin berilmagan
      </label>
      <label className="flex items-center gap-1.5">
        Kechikish
        <input
          type="number"
          min={0}
          max={24}
          step={0.5}
          value={f.delay_hours}
          onChange={(e) => setF({ ...f, delay_hours: e.target.value })}
          className="border border-slate-300 rounded px-1.5 py-1 w-16"
        />
        soat
      </label>
      <input
        value={f.note}
        onChange={(e) => setF({ ...f, note: e.target.value })}
        placeholder="Izoh"
        className="border border-slate-300 rounded px-2 py-1 flex-1 min-w-[120px]"
      />
      <button
        onClick={save}
        disabled={busy}
        className="bg-slate-800 text-white rounded px-3 py-1 font-medium disabled:opacity-40"
      >
        Saqlash
      </button>
    </div>
  );
}

/** Rahbariyat: barcha examinerlar oyligi + jarima va ball ayirish. */
export function ExaminerPayAdminTab({ branchId }: { branchId?: number | null } = {}) {
  const [period, setPeriod] = useState(thisMonth());
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [adj, setAdj] = useState({ points: "", reason: "" });
  const [busy, setBusy] = useState(false);

  const load = () => {
    api
      .get<Any>("/examiners/salary" + qs(period)
        + branchQs(branchId))
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, [period, branchId]);

  const addAdj = async (userId: number) => {
    setBusy(true);
    try {
      await api.post("/examiner-adjustments", {
        user_id: userId,
        points: Number(adj.points),
        reason: adj.reason,
      });
      setAdj({ points: "", reason: "" });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  if (err)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 mb-3">
        <MonthPicker value={period} onChange={setPeriod} />
        <p className="text-sm text-slate-500 flex-1">
          {d.period} · jami{" "}
          <span className="font-semibold text-slate-900">
            {fmt(d.total)} so'm
          </span>
        </p>
        <p className="text-xs text-slate-400">
          Chegara: {fmt(d.min)} — {fmt(d.max)}
        </p>
      </div>

      {d.rows.map((r: Any) => (
        <div
          key={r.user_id}
          className="bg-white border border-slate-200 rounded-xl mb-3"
        >
          <button
            onClick={() => setOpen(open === r.user_id ? null : r.user_id)}
            className="w-full flex items-center justify-between px-4 py-3 text-left"
          >
            <div>
              <p className="text-sm font-medium text-slate-900">{r.name}</p>
              <p className="text-xs text-slate-500">
                {r.role} · {r.exam_count} imtihon · sof {r.points} ball
              </p>
            </div>
            <p className="text-sm font-semibold text-slate-900">
              {fmt(r.salary)} so'm
              {r.clamped_min && (
                <span className="text-xs font-normal text-amber-600 ml-1.5">
                  (min)
                </span>
              )}
              {r.clamped_max && (
                <span className="text-xs font-normal text-amber-600 ml-1.5">
                  (max)
                </span>
              )}
            </p>
          </button>

          {open === r.user_id && (
            <div className="border-t border-slate-100 p-4">
              <ExamSheet d={r} name={r.name} />
              {d.can_penalize && (
                <div className="space-y-2 mb-4">
                  <p className="text-xs font-medium text-slate-600">
                    Jarima belgilash (imtihon bo'yicha):
                  </p>
                  {r.exams.map((e: Any) => (
                    <div key={e.exam_id}>
                      <p className="text-xs text-slate-500 mb-1">
                        {e.date} · {e.group} · {e.tier_label}
                      </p>
                      <PenaltyEditor exam={e} onSaved={load} />
                    </div>
                  ))}
                </div>
              )}
              <Adjustments d={r} />
              {d.can_penalize && (
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="number"
                    min={0.5}
                    value={adj.points}
                    onChange={(e) =>
                      setAdj({ ...adj, points: e.target.value })
                    }
                    placeholder="Ball"
                    className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm w-20"
                  />
                  <input
                    value={adj.reason}
                    onChange={(e) =>
                      setAdj({ ...adj, reason: e.target.value })
                    }
                    placeholder="Sabab (majburiy)"
                    className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm flex-1 min-w-[160px]"
                  />
                  <button
                    onClick={() => addAdj(r.user_id)}
                    disabled={busy || !adj.points || !adj.reason.trim()}
                    className="bg-red-600 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-40"
                  >
                    Ball ayirish
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
      {d.rows.length === 0 && (
        <p className="text-sm text-slate-400 py-8 text-center">
          Faol examiner topilmadi.
        </p>
      )}
    </div>
  );
}
