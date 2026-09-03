import { useEffect, useState } from "react";
import { GraduationCap, Info, AlertTriangle, Coins } from "lucide-react";
import { api, type MyStudentList, type MyStudent } from "../lib/api";
import { formatDate } from "../lib/format";

const HW_TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

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
  // Coin ayirish (intizom). Jahongir (2026-08-12): "ustozlarga coin
  // ayrish imkonini berish... minimum 1ta maksimum 15ta gacha".
  const [deduct, setDeduct] = useState<MyStudent | null>(null);
  const [amt, setAmt] = useState(1);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [dErr, setDErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const doDeduct = async () => {
    if (!deduct) return;
    setBusy(true);
    setDErr(null);
    try {
      await api.post(`/me/students/${deduct.id}/coin-deduct`, {
        amount: amt,
        note: note.trim() || undefined,
      });
      setMsg(`${deduct.full_name}: −${amt} coin ayirildi`);
      setDeduct(null);
      setTimeout(() => setMsg(null), 4000);
    } catch (e) {
      setDErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

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

      {(d.homework_low ?? 0) > 0 && (
        <p className="text-sm rounded-lg px-3 py-2 mb-4 bg-red-50 border border-red-200 text-red-800">
          {d.homework_low} o'quvchining uy vazifasi topshirish foizi{" "}
          {d.homework_threshold}% dan past.
        </p>
      )}

      {/* MUZLATILGANLAR (2026-09-03, Jahongir: "ustozlarga muzlatilgan
          o'quvchilari korinsin faqat yoqlamasi chiqmasin") */}
      {(d.frozen ?? 0) > 0 && (
        <p className="text-sm rounded-lg px-3 py-2 mb-4 bg-sky-50 border border-sky-200 text-sky-800">
          {d.frozen} ta o'quvchi muzlatilgan — ro'yxatda turadi, lekin
          davomat jadvaliga tushmaydi va ularga yo'qlama qo'yilmaydi.
        </p>
      )}

      {msg && (
        <p className="text-sm rounded-lg px-3 py-2 mb-4 bg-emerald-50 border border-emerald-200 text-emerald-800">
          {msg}
        </p>
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
              <th className="text-right px-3 py-2.5 font-medium">
                Uy vazifasi
              </th>
              <th className="text-right px-3 py-2.5 font-medium">Imtihon</th>
              <th className="text-right px-4 py-2.5 font-medium">Qancha vaqt</th>
              <th className="text-right px-3 py-2.5 font-medium">Coin</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((s) => (
              <tr
                key={s.id}
                className={
                  s.status === "frozen"
                    ? "bg-sky-50/40"
                    : s.at_risk
                      ? "bg-amber-50/40"
                      : undefined
                }
              >
                <td className="px-4 py-2.5">
                  <p className="font-medium text-slate-900 flex items-center gap-1.5">
                    {s.full_name}
                    {/* MUZLATILGAN (2026-09-03, Jahongir: "ustozlarga
                        muzlatilgan o'quvchilari korinsin faqat
                        yoqlamasi chiqmasin"). Ro'yxatda turadi,
                        lekin davomat jadvaliga tushmaydi. */}
                    {s.status === "frozen" && (
                      <span className="text-[10px] uppercase tracking-wide bg-sky-50 text-sky-600 border border-sky-200 px-1.5 py-0.5 rounded">
                        muzlatilgan
                      </span>
                    )}
                  </p>
                  {s.status === "frozen" ? (
                    <p className="text-xs text-sky-600">
                      Yo'qlamada chiqmaydi
                    </p>
                  ) : (
                    s.enrolled_date && (
                      <p className="text-xs text-slate-400">
                        {formatDate(s.enrolled_date)} dan
                      </p>
                    )
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
                <td className="px-3 py-2.5 text-right">
                  {s.homework_percent != null ? (
                    <span
                      className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                        HW_TONE[s.homework_tone || "slate"] || HW_TONE.slate
                      }`}
                      title={`${s.homework_checked} ta tekshirilgan`}
                    >
                      {s.homework_percent}%
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {s.last_exam ?? <span className="text-slate-300">—</span>}
                </td>
                <td className="px-4 py-2.5 text-right text-slate-500">
                  {s.months != null ? `${s.months} oy` : "—"}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <button
                    onClick={() => {
                      setDeduct(s);
                      setAmt(1);
                      setNote("");
                      setDErr(null);
                    }}
                    className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-lg border border-amber-300 text-amber-700 hover:bg-amber-50"
                    title="Coin ayirish (intizom, 1–15)"
                  >
                    <Coins size={13} /> −
                  </button>
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

      {deduct && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
          onClick={() => !busy && setDeduct(null)}
        >
          <div
            className="bg-white rounded-xl w-full max-w-xs p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-sm font-semibold text-slate-900 mb-3">
              Coin ayirish — {deduct.full_name}
            </p>
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={() => setAmt(Math.max(1, amt - 1))}
                className="w-8 h-8 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50"
              >
                −
              </button>
              <input
                type="number"
                min={1}
                max={15}
                value={amt}
                onChange={(e) =>
                  setAmt(
                    Math.min(15, Math.max(1, Number(e.target.value) || 1)),
                  )
                }
                className="w-16 text-center border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
              />
              <button
                onClick={() => setAmt(Math.min(15, amt + 1))}
                className="w-8 h-8 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50"
              >
                +
              </button>
              <span className="text-xs text-slate-400">1–15 ta</span>
            </div>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Sababi (ixtiyoriy)"
              className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm mb-3"
            />
            {dErr && <p className="text-xs text-red-600 mb-2">{dErr}</p>}
            <div className="flex gap-2">
              <button
                disabled={busy}
                onClick={doDeduct}
                className="flex-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50"
              >
                {busy ? "..." : `−${amt} coin ayirish`}
              </button>
              <button
                disabled={busy}
                onClick={() => setDeduct(null)}
                className="px-3 rounded-lg border border-slate-300 text-sm text-slate-600"
              >
                Bekor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
