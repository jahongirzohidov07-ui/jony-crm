import { useEffect, useState } from "react";
import { MinusCircle, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  EXAMINER_PENALTY_SET, SUPPORT_PENALTY_SET, can,
} from "../lib/roles";
import { MONTHS } from "../lib/expenses";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;
type Kind = "examiner" | "support";

/**
 * JARIMA BALLARI (2026-09-16, Jahongir: "examinerlar boshlig'i uchun
 * examinerlardan ayirish, HR uchun ham examiner ham supportlardan
 * ayirish uchun jarima ball bo'limi").
 *
 * Examiner va support oyligi ball bilan hisoblanadi; bu yerda ayirilgan
 * ball oylikka aylantirilishidan OLDIN chegiriladi. Kim nimani ayira
 * olishi backend bilan bir xil: EXAMINER_PENALTY_SET / SUPPORT_PENALTY_SET.
 */

const KIND_LABEL: Record<Kind, string> = {
  examiner: "Examinerlar",
  support: "Support teacherlar",
};
const ENDPOINTS: Record<Kind, { list: string; adj: string }> = {
  examiner: { list: "/examiners/salary", adj: "/examiner-adjustments" },
  support: { list: "/support/salary", adj: "/support-adjustments" },
};

const fmt = (n: Any) =>
  Number(n || 0).toLocaleString().replace(/,/g, " ");
const pad = (n: number) => String(n).padStart(2, "0");

/** Tanlangan oy uchun standart sana: joriy oy bo'lsa bugun,
 *  o'tgan oy bo'lsa o'sha oyning oxirgi kuni. */
function defaultDate(year: number, month: number): string {
  const now = new Date();
  if (year === now.getFullYear() && month === now.getMonth() + 1) {
    return `${year}-${pad(month)}-${pad(now.getDate())}`;
  }
  const last = new Date(year, month, 0).getDate();
  return `${year}-${pad(month)}-${pad(last)}`;
}

export function PenaltyPointsTab({ only }: { only?: Kind }) {
  const { user } = useAuth();
  const kinds = (["examiner", "support"] as Kind[]).filter(
    (k) =>
      (!only || only === k) &&
      can(user?.role, k === "examiner"
        ? EXAMINER_PENALTY_SET
        : SUPPORT_PENALTY_SET),
  );
  const now = new Date();
  const [kind, setKind] = useState<Kind | undefined>(kinds[0]);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [f, setF] = useState({
    user_id: "", points: "", reason: "",
    date: defaultDate(now.getFullYear(), now.getMonth() + 1),
  });
  const [busy, setBusy] = useState(false);

  const load = () => {
    if (!kind) return;
    setErr("");
    api
      .get<Any>(`${ENDPOINTS[kind].list}?year=${year}&month=${month}`)
      .then(setD)
      .catch((e) => {
        setD(null);
        setErr(e instanceof Error ? e.message : "Xatolik");
      });
  };
  useEffect(load, [kind, year, month]);
  useEffect(() => {
    setF((p) => ({ ...p, user_id: "", date: defaultDate(year, month) }));
  }, [kind, year, month]);

  if (!kind) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Jarima ball qo'yishga ruxsatingiz yo'q.
      </p>
    );
  }

  const rows: Any[] = (d?.rows || []).filter((r: Any) => r.user_id);
  const history = rows
    .flatMap((r: Any) =>
      (r.adjustments || []).map((a: Any) => ({ ...a, name: r.name })))
    .sort((a: Any, b: Any) =>
      b.date.localeCompare(a.date) || b.id - a.id);
  const gathered = (r: Any) =>
    kind === "examiner" ? r.base_points : r.gross_points;
  const minus = (r: Any) =>
    kind === "examiner"
      ? (r.penalty_points || 0) + (r.adjustment_points || 0)
      : r.adjustment_points || 0;

  const add = async () => {
    setBusy(true);
    try {
      await api.post(ENDPOINTS[kind].adj, {
        user_id: Number(f.user_id),
        points: Number(f.points),
        reason: f.reason.trim(),
        date: f.date || null,
      });
      setF({ ...f, points: "", reason: "" });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (a: Any) => {
    if (!confirm(`${a.name}: −${a.points} ball jarimani bekor qilasizmi?`))
      return;
    try {
      await api.delete(`${ENDPOINTS[kind].adj}/${a.id}`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const years = [now.getFullYear(), now.getFullYear() - 1];
  const canSave =
    !busy && f.user_id && Number(f.points) > 0 && f.reason.trim();

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {kinds.length > 1 &&
          kinds.map((k) => (
            <button
              key={k}
              onClick={() => setKind(k)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                kind === k
                  ? "bg-brand-600 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:border-brand-300"
              }`}
            >
              {KIND_LABEL[k]}
            </button>
          ))}
        <div className="flex gap-2 ml-auto">
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>{m}</option>
            ))}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
          >
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {/* ---- Ball ayirish formasi ---- */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
        <p className="text-sm font-medium text-slate-700 mb-3">
          Jarima ball ayirish — {KIND_LABEL[kind].toLowerCase()}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={f.user_id}
            onChange={(e) => setF({ ...f, user_id: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white min-w-[180px]"
          >
            <option value="">Xodimni tanlang</option>
            {rows.map((r) => (
              <option key={r.user_id} value={r.user_id}>{r.name}</option>
            ))}
          </select>
          <input
            type="number"
            min={0.5}
            max={500}
            step={0.5}
            value={f.points}
            onChange={(e) => setF({ ...f, points: e.target.value })}
            placeholder="Ball"
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm w-20"
          />
          <input
            type="date"
            value={f.date}
            onChange={(e) => setF({ ...f, date: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
          />
          <input
            value={f.reason}
            onChange={(e) => setF({ ...f, reason: e.target.value })}
            placeholder="Sabab (majburiy)"
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm flex-1 min-w-[180px]"
          />
          <button
            onClick={add}
            disabled={!canSave}
            className="bg-red-600 hover:bg-red-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-40"
          >
            Ball ayirish
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          {kind === "examiner"
            ? "1 ball = 1 000 so'm."
            : "1 ball = 10 000 so'm."}{" "}
          Ball oylikka aylantirilishidan oldin ayiriladi. Oylik baribir{" "}
          {fmt(d?.min)} so'mdan kam bo'lmaydi.
        </p>
      </div>

      {err && (
        <p className="text-sm text-slate-500 py-6 text-center">{err}</p>
      )}
      {!d && !err && (
        <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>
      )}

      {d && (
        <>
          {/* ---- Xodimlar kesimida ---- */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto mb-4">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
                  <th className="text-right px-3 py-2.5 font-medium">
                    Yig'ilgan ball
                  </th>
                  <th className="text-right px-3 py-2.5 font-medium">Jarima</th>
                  <th className="text-right px-3 py-2.5 font-medium">Sof ball</th>
                  <th className="text-right px-4 py-2.5 font-medium">Oylik</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((r) => (
                  <tr key={r.user_id}>
                    <td className="px-4 py-2.5 text-slate-800">{r.name}</td>
                    <td className="px-3 py-2.5 text-right text-emerald-700">
                      +{gathered(r) ?? 0}
                    </td>
                    <td className="px-3 py-2.5 text-right text-red-600">
                      {minus(r) > 0 ? `−${Number(minus(r).toFixed(2))}` : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-right font-medium text-slate-900">
                      {r.points}
                    </td>
                    <td className="px-4 py-2.5 text-right text-slate-900">
                      {fmt(r.salary)} so'm
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length === 0 && (
              <p className="text-sm text-slate-400 py-8 text-center">
                Bu oyda xodim topilmadi.
              </p>
            )}
          </div>

          {/* ---- Shu oyda ayirilgan ballar ---- */}
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-sm font-medium text-slate-700 mb-2">
              {d.period} — ayirilgan ballar
            </p>
            {history.length === 0 && (
              <p className="text-sm text-slate-400 py-3">
                Bu oyda jarima ball qo'yilmagan.
              </p>
            )}
            {history.map((a: Any) => (
              <div
                key={a.id}
                className="flex items-start gap-2 text-sm py-1.5 border-b border-slate-100 last:border-0"
              >
                <MinusCircle size={14} className="text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <span className="font-medium text-slate-800">{a.name}</span>
                  <span className="font-medium text-red-600 ml-1.5">
                    −{a.points} ball
                  </span>
                  <span className="text-slate-500"> — {a.reason}</span>
                  <span className="text-xs text-slate-400 ml-1.5">
                    {a.date}
                    {a.created_by ? ` · ${a.created_by}` : ""}
                  </span>
                </div>
                <button
                  onClick={() => remove(a)}
                  title="Bekor qilish"
                  className="text-slate-400 hover:text-red-600 p-1"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
          {kind === "examiner" && (
            <p className="text-xs text-slate-400 mt-3">
              Imtihon bo'yicha jarima (LC UP, Coin, kechikish) "Jarima"
              ustuniga qo'shilgan; uni Audit → Examiner oyliklari
              bo'limidan belgilanadi.
            </p>
          )}
        </>
      )}
    </div>
  );
}
