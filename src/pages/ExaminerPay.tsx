import { useEffect, useState } from "react";
import { Wallet, Info, MinusCircle } from "lucide-react";
import { api } from "../lib/api";

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
          Shu oygi oylik — avtomat ({d.period})
        </p>
      </div>
      <p className="text-3xl font-semibold text-slate-900 mb-1">
        {fmt(d.salary)}{" "}
        <span className="text-base font-normal text-slate-400">so'm</span>
      </p>
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
          <p className="text-xs text-slate-400">x 1 000 so'm</p>
        </div>
      </div>
    </div>
  );
}

function ExamsTable({ d }: { d: Any }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto mb-4">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-slate-500 text-xs">
          <tr>
            <th className="text-left px-4 py-2.5 font-medium">Sana</th>
            <th className="text-left px-3 py-2.5 font-medium">Guruh</th>
            <th className="text-left px-3 py-2.5 font-medium">Daraja</th>
            <th className="text-right px-3 py-2.5 font-medium">O'quvchi</th>
            <th className="text-right px-3 py-2.5 font-medium">Ball</th>
            <th className="text-right px-3 py-2.5 font-medium">Jarima</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {d.exams.map((e: Any) => (
            <tr key={e.exam_id}>
              <td className="px-4 py-2.5 text-slate-700">{e.date}</td>
              <td className="px-3 py-2.5 text-slate-700">
                {e.group}
                <span className="text-xs text-slate-400 ml-1.5">
                  {e.kind}
                  {e.retake ? " · retake" : ""}
                </span>
              </td>
              <td className="px-3 py-2.5 text-slate-500">{e.tier_label}</td>
              <td className="px-3 py-2.5 text-right text-slate-700">
                {e.students}
              </td>
              <td className="px-3 py-2.5 text-right font-medium text-emerald-700">
                {e.points > 0 ? `+${e.points}` : "0"}
                {e.points > 0 && (
                  <span className="text-xs font-normal text-slate-400 ml-1">
                    ({e.base}+{e.students}x{e.per_student})
                  </span>
                )}
              </td>
              <td className="px-3 py-2.5 text-right text-red-600">
                {e.penalty_points > 0 ? `−${e.penalty_points}` : "—"}
                {e.penalty_points > 0 && (
                  <span
                    className="text-xs text-slate-400 ml-1"
                    title={e.penalty_note || ""}
                  >
                    ({[
                      e.penalty_lc_up ? "LC UP" : null,
                      e.penalty_coin ? "Coin" : null,
                      e.penalty_delay_hours
                        ? `${e.penalty_delay_hours} soat`
                        : null,
                    ]
                      .filter(Boolean)
                      .join(", ")})
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {d.exams.length === 0 && (
        <p className="text-sm text-slate-400 py-8 text-center">
          Bu oyda hali o'tkazilgan imtihon yo'q.
        </p>
      )}
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
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api
      .get<Any>("/me/examiner-salary")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  if (err)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;
  if (d.volunteer)
    return (
      <p className="text-sm text-slate-500 py-10 text-center max-w-md mx-auto">
        {d.hint}
      </p>
    );
  return (
    <div>
      <SalaryCard d={d} />
      <ExamsTable d={d} />
      <Adjustments d={d} />
      <RateTable d={d} />
      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
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
export function ExaminerPayAdminTab() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [adj, setAdj] = useState({ points: "", reason: "" });
  const [busy, setBusy] = useState(false);

  const load = () => {
    api
      .get<Any>("/examiners/salary")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

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
      <div className="flex items-baseline justify-between mb-3">
        <p className="text-sm text-slate-500">
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
              <ExamsTable d={r} />
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
