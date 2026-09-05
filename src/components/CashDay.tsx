import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronLeft, ChevronRight, CalendarDays, Wallet } from "lucide-react";
import { api } from "../lib/api";
import { formatSom } from "../lib/format";

/**
 * BUGUNGI TUSHUM (2026-09-05).
 *
 * Jahongir: "moliya bo'limida qaysi joyga qoyilsa eng mos va mukammal
 * bolsa bugungi tushumlarni kim toladi qancha va qanchasi klik yoki
 * terminal shularni ham korsatadigan joy kerak".
 *
 * Joyi: Moliya -> Pul oqimi, oylik jadvalning TEPASIDA. Sabab: kassa
 * bilan ishlaydigan odam aynan shu tabni ochadi; oylik kassa daftari
 * pastda qoladi, kunlik holat esa birinchi ko'zga tashlanadi.
 *
 * Ko'rsatadi: kun (sukut — bugun, o'q bilan oldinga/orqaga), usullar
 * kesimida jami va soni (Naqd / Click / Terminal), yangi/eski, kim
 * qabul qilgani kesimi va har bir to'lov: vaqt, kim, guruh, summa,
 * usul, qabul qilgan xodim.
 */

interface CashDayData {
  date: string;
  total: number;
  count: number;
  by_method: { method: string; label: string; amount: number; count: number }[];
  new_count: number;
  new_sum: number;
  old_count: number;
  old_sum: number;
  by_receiver: { name: string; amount: number; count: number }[];
  rows: {
    id: number;
    time: string | null;
    student_id: number;
    student: string;
    group: string | null;
    amount: number;
    method: string;
    method_label: string;
    received_by: string | null;
    branch: string;
    is_new: boolean;
    note: string | null;
  }[];
}

const METHOD_TONE: Record<string, string> = {
  cash: "bg-emerald-50 text-emerald-700 border-emerald-200",
  card: "bg-sky-50 text-sky-700 border-sky-200",
  terminal: "bg-violet-50 text-violet-700 border-violet-200",
  other: "bg-slate-50 text-slate-600 border-slate-200",
};

function isoToday(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function shiftDay(iso: string, delta: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d + delta);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${dt.getFullYear()}-${p(dt.getMonth() + 1)}-${p(dt.getDate())}`;
}

function dayLabel(iso: string): string {
  const today = isoToday();
  if (iso === today) return "Bugun";
  if (iso === shiftDay(today, -1)) return "Kecha";
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
}

export function CashDayCard({ reloadKey = 0 }: { reloadKey?: number }) {
  const [day, setDay] = useState(isoToday());
  const [data, setData] = useState<CashDayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    api
      .get<CashDayData>(`/reports/cash-day?day=${day}`)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }, [day, reloadKey]);

  const today = isoToday();

  return (
    <div className="bg-white rounded-xl border border-slate-200 mb-5">
      <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-slate-100">
        <Wallet size={16} className="text-emerald-600" />
        <h3 className="font-semibold text-slate-900">
          {dayLabel(day)}gi tushum
        </h3>
        <span className="text-xs text-slate-400">
          kim to'ladi, qancha, qaysi usulda
        </span>
        <div className="flex-1" />
        <div className="flex items-center gap-1">
          <button
            onClick={() => setDay(shiftDay(day, -1))}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50"
            title="Oldingi kun"
          >
            <ChevronLeft size={14} />
          </button>
          <div className="relative">
            <CalendarDays
              size={13}
              className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
            />
            <input
              type="date"
              value={day}
              max={today}
              onChange={(e) => e.target.value && setDay(e.target.value)}
              className="pl-7 pr-2 py-1.5 rounded-lg border border-slate-200 text-sm"
            />
          </div>
          <button
            onClick={() => setDay(shiftDay(day, 1))}
            disabled={day >= today}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40"
            title="Keyingi kun"
          >
            <ChevronRight size={14} />
          </button>
          {day !== today && (
            <button
              onClick={() => setDay(today)}
              className="ml-1 px-2 py-1.5 rounded-lg text-xs text-brand-700 bg-brand-50 hover:bg-brand-100"
            >
              Bugun
            </button>
          )}
        </div>
      </div>

      {loading && (
        <p className="px-4 py-4 text-sm text-slate-400">Yuklanmoqda…</p>
      )}
      {err && <p className="px-4 py-4 text-sm text-red-600">{err}</p>}

      {!loading && data && (
        <>
          {/* Jami + usullar */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 px-4 py-4">
            <div className="rounded-lg bg-slate-900 text-white px-3 py-2.5">
              <p className="text-[11px] opacity-70">Jami tushum</p>
              <p className="text-lg font-semibold leading-tight">
                {formatSom(data.total)}
              </p>
              <p className="text-[11px] opacity-70">{data.count} ta to'lov</p>
            </div>
            {data.by_method
              .filter((m) => m.method !== "other" || m.count > 0)
              .map((m) => (
                <div
                  key={m.method}
                  className={`rounded-lg border px-3 py-2.5 ${
                    METHOD_TONE[m.method] || METHOD_TONE.other
                  }`}
                >
                  <p className="text-[11px] opacity-80">{m.label}</p>
                  <p className="text-lg font-semibold leading-tight">
                    {formatSom(m.amount)}
                  </p>
                  <p className="text-[11px] opacity-80">{m.count} ta</p>
                </div>
              ))}
            <div className="rounded-lg border border-slate-200 px-3 py-2.5">
              <p className="text-[11px] text-slate-500">Yangi / eski</p>
              <p className="text-sm font-semibold text-slate-800 leading-tight">
                {data.new_count} / {data.old_count}
              </p>
              <p className="text-[11px] text-slate-500">
                {formatSom(data.new_sum)} / {formatSom(data.old_sum)}
              </p>
            </div>
          </div>

          {/* Kim qabul qildi */}
          {data.by_receiver.length > 0 && (
            <div className="px-4 pb-3 flex flex-wrap gap-2">
              <span className="text-[11px] text-slate-400 self-center">
                Qabul qildi:
              </span>
              {data.by_receiver.map((r) => (
                <span
                  key={r.name}
                  className="text-xs bg-slate-50 border border-slate-200 rounded-full px-2.5 py-1 text-slate-700"
                >
                  {r.name} — <b>{formatSom(r.amount)}</b>{" "}
                  <span className="text-slate-400">({r.count})</span>
                </span>
              ))}
            </div>
          )}

          {/* Ro'yxat */}
          {data.rows.length === 0 ? (
            <p className="px-4 pb-4 text-sm text-slate-400">
              Bu kunda to'lov yo'q.
            </p>
          ) : (
            <>
              <button
                onClick={() => setOpen(!open)}
                className="w-full text-left px-4 py-2 text-xs text-slate-500 border-t border-slate-100 hover:bg-slate-50"
              >
                {open ? "▾" : "▸"} Kim to'ladi — {data.rows.length} ta
              </button>
              {open && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-slate-500 text-xs">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium">Vaqt</th>
                        <th className="text-left px-3 py-2 font-medium">O'quvchi</th>
                        <th className="text-left px-3 py-2 font-medium">Guruh</th>
                        <th className="text-right px-3 py-2 font-medium">Summa</th>
                        <th className="text-left px-3 py-2 font-medium">Usul</th>
                        <th className="text-left px-3 py-2 font-medium">Qabul qildi</th>
                        <th className="text-left px-3 py-2 font-medium">Filial</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.rows.map((r) => (
                        <tr key={r.id}>
                          <td className="px-4 py-2 text-slate-500 tabular-nums">
                            {r.time || "—"}
                          </td>
                          <td className="px-3 py-2">
                            <Link
                              to={`/students/${r.student_id}`}
                              className="text-slate-900 hover:text-brand-700 font-medium"
                            >
                              {r.student}
                            </Link>
                            {r.is_new && (
                              <span className="ml-1.5 text-[10px] uppercase tracking-wide bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded">
                                yangi
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-slate-500">
                            {r.group || "—"}
                          </td>
                          <td className="px-3 py-2 text-right font-semibold text-emerald-700 tabular-nums">
                            +{formatSom(r.amount)}
                          </td>
                          <td className="px-3 py-2">
                            <span
                              className={`text-xs border rounded-full px-2 py-0.5 ${
                                METHOD_TONE[r.method] || METHOD_TONE.other
                              }`}
                            >
                              {r.method_label}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-slate-600">
                            {r.received_by || "—"}
                          </td>
                          <td className="px-3 py-2 text-slate-500">{r.branch}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
