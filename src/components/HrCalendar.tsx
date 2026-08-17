import { useEffect, useMemo, useState } from "react";
import {
  CalendarDays, ChevronLeft, ChevronRight, Clock, MapPin, Phone,
  User as UserIcon, X,
} from "lucide-react";
import { api } from "../lib/api";

/**
 * SUHBAT VA SINOV DARSI KALENDARI (2026-08-16).
 *
 * Jahongir: "suhbat va sinov darsi kalendari qo'shish kerak".
 *
 * Oy bo'yicha to'r. Har kunda o'sha kunga belgilangan suhbatlar va
 * sinov darslari — rangi turiga qarab (sinov darsi sariq, suhbat
 * binafsha). Kun bosilsa o'sha kunning to'liq ro'yxati ochiladi:
 * kim, soat nechada, qayerda, telefoni bilan.
 *
 * Ma'lumot mavjud /api/ats/interviews dan olinadi — unga shu kuni
 * date_from/date_to qo'shildi, ya'ni butun oy BITTA so'rovda keladi.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Row = {
  id: number;
  kind: string;
  kind_label: string;
  date: string | null;
  time?: string | null;
  minutes?: number;
  place?: string | null;
  interviewer?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  candidate?: string | null;
  subject?: string | null;
  phone?: string | null;
  note?: string | null;
};

const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];
const WD = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];

const TONE: Record<string, string> = {
  demo: "bg-amber-100 text-amber-800 border-amber-200",
  phone: "bg-sky-100 text-sky-800 border-sky-200",
  hr: "bg-violet-100 text-violet-800 border-violet-200",
  tech: "bg-violet-100 text-violet-800 border-violet-200",
  final: "bg-teal-100 text-teal-800 border-teal-200",
};

const STATUS_TONE: Record<string, string> = {
  sky: "bg-sky-100 text-sky-700",
  emerald: "bg-emerald-100 text-emerald-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

function iso(d: Date) {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function HrCalendar() {
  const today = new Date();
  const [ym, setYm] = useState({ y: today.getFullYear(), m: today.getMonth() });
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [day, setDay] = useState<string | null>(null);

  const first = new Date(ym.y, ym.m, 1);
  const last = new Date(ym.y, ym.m + 1, 0);

  function load() {
    setLoading(true);
    api
      .get<{ rows: Row[] }>(
        `/ats/interviews?date_from=${iso(first)}&date_to=${iso(last)}`
      )
      .then((d) => setRows(d.rows || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }
  useEffect(load, [ym.y, ym.m]);

  const byDay = useMemo(() => {
    const m: Record<string, Row[]> = {};
    for (const r of rows) {
      if (!r.date) continue;
      (m[r.date] ||= []).push(r);
    }
    for (const k of Object.keys(m))
      m[k].sort((a, b) => (a.time || "").localeCompare(b.time || ""));
    return m;
  }, [rows]);

  // Dushanbadan boshlanadigan to'r
  const cells: (Date | null)[] = [];
  const lead = (first.getDay() + 6) % 7;
  for (let i = 0; i < lead; i++) cells.push(null);
  for (let d = 1; d <= last.getDate(); d++) cells.push(new Date(ym.y, ym.m, d));
  while (cells.length % 7 !== 0) cells.push(null);

  const shift = (n: number) => {
    const d = new Date(ym.y, ym.m + n, 1);
    setYm({ y: d.getFullYear(), m: d.getMonth() });
    setDay(null);
  };

  const dayRows = day ? byDay[day] || [] : [];

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <CalendarDays size={18} className="text-slate-400" />
        <h2 className="text-base font-semibold text-slate-900 flex-1">
          Suhbat va sinov darsi kalendari
        </h2>
        <button
          onClick={() => shift(-1)}
          className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:border-slate-300"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm font-semibold text-slate-700 w-32 text-center">
          {MONTHS[ym.m]} {ym.y}
        </span>
        <button
          onClick={() => shift(1)}
          className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:border-slate-300"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-3 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-violet-200" /> Suhbat
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-amber-200" /> Sinov darsi
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-sky-200" /> Telefon suhbati
        </span>
        <span className="ml-auto">
          {loading ? "Yuklanmoqda…" : `${rows.length} ta yozuv`}
        </span>
      </div>

      <div className="grid grid-cols-7 gap-px bg-slate-200 border border-slate-200 rounded-xl overflow-hidden">
        {WD.map((w) => (
          <div
            key={w}
            className="bg-slate-50 py-2 text-center text-xs font-semibold text-slate-500"
          >
            {w}
          </div>
        ))}
        {cells.map((d, i) => {
          if (!d) return <div key={i} className="bg-slate-50 min-h-[92px]" />;
          const k = iso(d);
          const list = byDay[k] || [];
          const isToday = k === iso(today);
          return (
            <button
              key={i}
              onClick={() => setDay(list.length ? k : null)}
              className={`bg-white min-h-[92px] p-1.5 text-left align-top transition ${
                list.length ? "hover:bg-slate-50" : ""
              }`}
            >
              <span
                className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold mb-1 ${
                  isToday
                    ? "bg-brand-600 text-white"
                    : "text-slate-500"
                }`}
              >
                {d.getDate()}
              </span>
              <div className="space-y-0.5">
                {list.slice(0, 3).map((r) => (
                  <div
                    key={r.id}
                    className={`px-1.5 py-0.5 rounded border text-[10px] leading-tight truncate ${
                      TONE[r.kind] || TONE.hr
                    } ${r.status === "cancelled" ? "line-through opacity-60" : ""}`}
                  >
                    {r.time ? `${r.time} ` : ""}
                    {r.candidate || "—"}
                  </div>
                ))}
                {list.length > 3 && (
                  <div className="text-[10px] text-slate-400 px-1">
                    +{list.length - 3} ta
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {day && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
          onClick={() => setDay(null)}
        >
          <div
            className="bg-white rounded-2xl w-full max-w-md p-5 max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-4">
              <CalendarDays size={18} className="text-brand-500" />
              <p className="font-semibold text-slate-900 flex-1">
                {Number(day.slice(8, 10))}-{MONTHS[Number(day.slice(5, 7)) - 1]}{" "}
                {day.slice(0, 4)}
              </p>
              <button onClick={() => setDay(null)} className="text-slate-400">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-2">
              {dayRows.map((r) => (
                <div
                  key={r.id}
                  className={`rounded-xl border p-3.5 ${TONE[r.kind] || TONE.hr}`}
                >
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-sm flex-1 truncate">
                      {r.candidate || "—"}
                    </p>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${
                        STATUS_TONE[r.status_tone] || STATUS_TONE.slate
                      }`}
                    >
                      {r.status_label}
                    </span>
                  </div>
                  <p className="text-xs mt-1 opacity-80">
                    {r.kind_label}
                    {r.subject ? ` · ${r.subject}` : ""}
                  </p>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs opacity-90">
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {r.time || "—"}
                      {r.minutes ? ` · ${r.minutes} daq` : ""}
                    </span>
                    {r.interviewer && (
                      <span className="flex items-center gap-1">
                        <UserIcon size={12} />
                        {r.interviewer}
                      </span>
                    )}
                    {r.place && (
                      <span className="flex items-center gap-1">
                        <MapPin size={12} />
                        {r.place}
                      </span>
                    )}
                    {r.phone && (
                      <a
                        href={`tel:${r.phone}`}
                        className="flex items-center gap-1 underline"
                      >
                        <Phone size={12} />
                        {r.phone}
                      </a>
                    )}
                  </div>
                  {r.note && (
                    <p className="text-xs mt-2 opacity-80">{r.note}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
