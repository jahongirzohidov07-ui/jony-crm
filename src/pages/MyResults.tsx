import { useEffect, useState } from "react";
import { PieChart, Info, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { api, type MyResults as Data, type LeaverWindow } from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-700",
};

/**
 * Ustozning o'z natijalari.
 *
 * Bu sahifa baho qo'yish uchun emas — ko'rish uchun. Shuning uchun
 * har bir raqam yonida markaz o'rtachasi turadi va ketish sabablari
 * "bizga bog'liq" / "bog'liq emas" deb ajratiladi: ko'chib ketgan
 * oila uchun ustozni ayblash noto'g'ri bo'lardi.
 */
export default function MyResults() {
  const [d, setD] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [win, setWin] = useState("m6");

  useEffect(() => {
    api
      .get<Data>("/me/results")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  const active = d.windows.find((w) => w.key === win) || d.windows[0];

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <PieChart size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Mening natijalarim
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        {d.teacher.name} · {d.teacher.grade_label}
      </p>

      {/* Asosiy raqamlar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <Card label="Hozir o'qiyapti" value={d.students.active} />
        <Card label="Ketgan" value={d.students.left} />
        <Card
          label="Qolish foizi"
          value={d.retention.value + "%"}
          sub={
            d.retention.centre_avg != null
              ? `markazda ${d.retention.centre_avg}%`
              : undefined
          }
        />
        <Card
          label="O'rtacha qancha oy o'qiydi"
          value={d.ltv.value != null ? d.ltv.value + " oy" : "—"}
          sub={
            d.ltv.centre_avg != null
              ? `markazda ${d.ltv.centre_avg} oy`
              : undefined
          }
        />
      </div>

      {/* Solishtirish */}
      <div className="grid md:grid-cols-2 gap-4 mb-5">
        <Compare
          title="Ketish foizi"
          value={d.churn.value + "%"}
          avg={d.churn.centre_avg != null ? d.churn.centre_avg + "%" : null}
          verdict={d.churn.verdict}
          tone={d.churn.tone}
          diff={d.churn.diff}
          rank={d.churn.rank}
          peers={d.churn.peers}
          lowerIsBetter
        />
        <Compare
          title="O'quvchi qancha qoladi"
          value={d.ltv.value != null ? d.ltv.value + " oy" : "—"}
          avg={d.ltv.centre_avg != null ? d.ltv.centre_avg + " oy" : null}
          verdict={d.ltv.verdict}
          tone={d.ltv.tone}
          diff={d.ltv.diff}
          rank={d.ltv.rank}
          peers={d.ltv.peers}
          note={d.ltv.note}
        />
      </div>

      <p
        className={`text-sm rounded-lg px-3 py-2 mb-5 flex items-start gap-2 ${
          d.enough_data
            ? "text-slate-600 bg-slate-50 border border-slate-200"
            : "text-amber-800 bg-amber-50 border border-amber-200"
        }`}
      >
        <Info size={14} className="shrink-0 mt-0.5 opacity-60" />
        {d.hint}
      </p>

      {/* Ketganlar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <p className="text-sm font-medium text-slate-700">
            Ketgan o'quvchilar
          </p>
          <div className="ml-auto flex gap-1 flex-wrap">
            {d.windows.map((w) => (
              <button
                key={w.key}
                onClick={() => setWin(w.key)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
                  win === w.key
                    ? "bg-slate-800 text-white"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {w.label} {w.count}
              </button>
            ))}
          </div>
        </div>

        {active && <WindowBody w={active} />}
      </div>

      {/* Sabablar */}
      {d.reasons.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 mt-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Nega ketishgan — oxirgi 1 yil
          </p>
          <div className="space-y-2">
            {d.reasons.map((r) => (
              <div key={r.key} className="flex items-center gap-3">
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                    r.controllable === true
                      ? TONE.amber
                      : r.controllable === false
                        ? TONE.slate
                        : TONE.slate
                  }`}
                >
                  {r.controllable === true
                    ? "bizga bog'liq"
                    : r.controllable === false
                      ? "bog'liq emas"
                      : "noma'lum"}
                </span>
                <span className="text-sm text-slate-800">{r.label}</span>
                <span className="ml-auto text-sm font-medium text-slate-900">
                  {r.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Card({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function Compare({
  title,
  value,
  avg,
  verdict,
  tone,
  diff,
  rank,
  peers,
  note,
  lowerIsBetter,
}: {
  title: string;
  value: string;
  avg: string | null;
  verdict: string;
  tone: string;
  diff?: number | null;
  rank?: number | null;
  peers: number;
  note?: string;
  lowerIsBetter?: boolean;
}) {
  const Icon =
    tone === "emerald"
      ? lowerIsBetter
        ? TrendingDown
        : TrendingUp
      : tone === "amber"
        ? lowerIsBetter
          ? TrendingUp
          : TrendingDown
        : Minus;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <p className="text-xs text-slate-500 mb-2">{title}</p>
      <div className="flex items-end gap-3 mb-3">
        <span className="text-3xl font-semibold text-slate-900">{value}</span>
        {avg && (
          <span className="text-sm text-slate-400 mb-1">
            markaz o'rtachasi {avg}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`px-2 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
            TONE[tone] || TONE.slate
          }`}
        >
          <Icon size={13} />
          {verdict}
        </span>
        {diff != null && Math.abs(diff) >= 5 && (
          <span className="text-xs text-slate-500">
            farq {diff > 0 ? "+" : ""}
            {diff}%
          </span>
        )}
        {rank != null && (
          <span className="ml-auto text-xs text-slate-500">
            {peers} ustozdan {rank}-o'rin
          </span>
        )}
      </div>

      {note && <p className="text-xs text-slate-400 mt-2.5">{note}</p>}
    </div>
  );
}

function WindowBody({ w }: { w: LeaverWindow }) {
  if (w.count === 0)
    return (
      <p className="text-sm text-emerald-700 py-6 text-center">
        Bu davrda bironta o'quvchi ketmagan.
      </p>
    );

  return (
    <>
      <div className="flex gap-2 mb-3 flex-wrap">
        {w.controllable > 0 && (
          <span className={`px-2 py-1 rounded-lg text-xs ${TONE.amber}`}>
            {w.controllable} tasi bizga bog'liq sababdan
          </span>
        )}
        {w.not_controllable > 0 && (
          <span className={`px-2 py-1 rounded-lg text-xs ${TONE.slate}`}>
            {w.not_controllable} tasi bizga bog'liq emas
          </span>
        )}
        {w.unknown > 0 && (
          <span className={`px-2 py-1 rounded-lg text-xs ${TONE.slate}`}>
            {w.unknown} tasida sabab yozilmagan
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-500 text-xs">
            <tr>
              <th className="text-left py-2 font-medium">O'quvchi</th>
              <th className="text-left py-2 px-2 font-medium">Guruh</th>
              <th className="text-right py-2 px-2 font-medium">Qancha o'qidi</th>
              <th className="text-left py-2 px-2 font-medium">Ketgan sana</th>
              <th className="text-left py-2 font-medium">Sabab</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {w.rows.map((r) => (
              <tr key={r.id}>
                <td className="py-2 text-slate-900">{r.name}</td>
                <td className="py-2 px-2 text-slate-500">{r.group || "—"}</td>
                <td className="py-2 px-2 text-right text-slate-600">
                  {r.months} oy
                </td>
                <td className="py-2 px-2 text-slate-500">
                  {formatDate(r.left_date)}
                </td>
                <td className="py-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[11px] ${
                      r.controllable === true ? TONE.amber : TONE.slate
                    }`}
                  >
                    {r.reason_label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
