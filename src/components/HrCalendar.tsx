import { useCallback, useEffect, useMemo, useState } from "react";
import { formatPhone, telHref } from "./PhoneInput";
import {
  CalendarDays, ChevronLeft, ChevronRight, Clock, MapPin, Phone,
  User as UserIcon, X, CalendarCheck, Presentation, PhoneCall, Users,
  Ban, Sun, LayoutGrid, Rows3, ListTodo, StickyNote,
} from "lucide-react";
import { api } from "../lib/api";

/**
 * SUHBAT VA SINOV DARSI KALENDARI.
 *
 * 2026-08-16, Jahongir: "suhbat va sinov darsi kalendari qo'shish kerak".
 * 2026-10-22, Jahongir: "hr kalendar ham ming so'mlik kalendarga
 * o'xshab yotibdi uniyam qimmatlashtir 10000$ proyektdek ko'rinishi
 * kerak" — to'liq qayta chizildi:
 *   · rangli bosh panel: oy, "Bugun", ko'rinish tanlagichi, statistika;
 *   · uch ko'rinish — Oy (to'r), Hafta (soat bo'yicha jadval),
 *     Ro'yxat (kunlar bo'yicha kun tartibi);
 *   · o'ng panel — bugun va yaqin kunlar;
 *   · kun bosilsa o'ngdan siljib chiqadigan panel — vaqt chizig'i,
 *     telefon, joy, suhbatdosh;
 *   · klaviatura: ← → davr, T — bugun, Esc — yopish.
 *
 * Ma'lumot o'sha /api/ats/interviews (date_from/date_to) — ko'rinayotgan
 * davr BITTA so'rovda keladi. Backend o'zgarmagan.
 */

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

type View = "month" | "week" | "agenda";

const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];
const WD = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];
const WD_FULL = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma",
                 "Shanba", "Yakshanba"];

/* Har tur o'z rangida: chip foni, chap chiziq, nuqta, gradient */
const KIND: Record<string, {
  chip: string; bar: string; dot: string; grad: string; icon: typeof Users;
}> = {
  demo: { chip: "bg-amber-50 text-amber-900", bar: "bg-amber-400",
          dot: "bg-amber-400", grad: "from-amber-400 to-orange-500",
          icon: Presentation },
  phone: { chip: "bg-sky-50 text-sky-900", bar: "bg-sky-400",
           dot: "bg-sky-400", grad: "from-sky-400 to-blue-500",
           icon: PhoneCall },
  hr: { chip: "bg-violet-50 text-violet-900", bar: "bg-violet-500",
        dot: "bg-violet-500", grad: "from-violet-500 to-purple-600",
        icon: Users },
  tech: { chip: "bg-indigo-50 text-indigo-900", bar: "bg-indigo-500",
          dot: "bg-indigo-500", grad: "from-indigo-500 to-blue-600",
          icon: Users },
  final: { chip: "bg-teal-50 text-teal-900", bar: "bg-teal-500",
           dot: "bg-teal-500", grad: "from-teal-400 to-emerald-600",
           icon: CalendarCheck },
};
const kindOf = (k: string) => KIND[k] || KIND.hr;

const LEGEND: [string, string][] = [
  ["hr", "HR suhbati"], ["tech", "Kasbiy suhbat"], ["demo", "Sinov darsi"],
  ["phone", "Telefon suhbati"], ["final", "Yakuniy suhbat"],
];

const STATUS_TONE: Record<string, string> = {
  sky: "bg-sky-100 text-sky-700 ring-sky-200",
  emerald: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  red: "bg-red-100 text-red-700 ring-red-200",
  slate: "bg-slate-100 text-slate-600 ring-slate-200",
};

const HOUR_FROM = 8;
const HOUR_TO = 20;
const HOUR_PX = 56;

function iso(d: Date) {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
function addDays(d: Date, n: number) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
}
function mondayOf(d: Date) {
  return addDays(d, -((d.getDay() + 6) % 7));
}
function minutesOf(t?: string | null) {
  const m = /^(\d{1,2}):(\d{2})/.exec(t || "");
  return m ? Number(m[1]) * 60 + Number(m[2]) : null;
}
function initials(name?: string | null) {
  const p = (name || "?").trim().split(/\s+/);
  return ((p[0]?.[0] || "") + (p[1]?.[0] || "")).toUpperCase() || "?";
}
function niceDay(k: string) {
  const d = new Date(k + "T00:00:00");
  return `${d.getDate()}-${MONTHS[d.getMonth()].toLowerCase()}, `
    + WD_FULL[(d.getDay() + 6) % 7].toLowerCase();
}
const cancelled = (r: Row) => r.status === "cancelled";

export function HrCalendar() {
  const todayKey = iso(new Date());
  const [view, setView] = useState<View>("month");
  const [anchor, setAnchor] = useState(() => new Date());
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [day, setDay] = useState<string | null>(null);

  // Ko'rinayotgan davr
  const range = useMemo(() => {
    if (view === "week") {
      const from = mondayOf(anchor);
      return { from, to: addDays(from, 6) };
    }
    const from = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
    return { from, to: new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0) };
  }, [view, anchor]);
  const fromKey = iso(range.from);
  const toKey = iso(range.to);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api
      .get<{ rows: Row[] }>(`/ats/interviews?date_from=${fromKey}&date_to=${toKey}`)
      .then((d) => { if (alive) setRows(d.rows || []); })
      .catch(() => { if (alive) setRows([]); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [fromKey, toKey]);

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

  const stats = useMemo(() => {
    const live = rows.filter((r) => !cancelled(r));
    return {
      total: live.length,
      interviews: live.filter((r) => r.kind !== "demo").length,
      demos: live.filter((r) => r.kind === "demo").length,
      today: (byDay[todayKey] || []).filter((r) => !cancelled(r)).length,
      cancelled: rows.length - live.length,
    };
  }, [rows, byDay, todayKey]);

  const shift = useCallback((n: number) => {
    setDay(null);
    setAnchor((a) => view === "week"
      ? addDays(a, 7 * n)
      : new Date(a.getFullYear(), a.getMonth() + n, 1));
  }, [view]);
  const goToday = useCallback(() => { setDay(null); setAnchor(new Date()); }, []);

  // Klaviatura: ← → davr, T — bugun, Esc — panelni yopish
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.key === "Escape") setDay(null);
      else if (e.key === "ArrowLeft") shift(-1);
      else if (e.key === "ArrowRight") shift(1);
      else if (e.key === "t" || e.key === "T") goToday();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [shift, goToday]);

  const title = view === "week"
    ? (() => {
        const a = range.from, b = range.to;
        return a.getMonth() === b.getMonth()
          ? `${a.getDate()}–${b.getDate()} ${MONTHS[a.getMonth()]} ${a.getFullYear()}`
          : `${a.getDate()} ${MONTHS[a.getMonth()].slice(0, 3)} – ${b.getDate()} ${MONTHS[b.getMonth()].slice(0, 3)} ${b.getFullYear()}`;
      })()
    : `${MONTHS[anchor.getMonth()]} ${anchor.getFullYear()}`;

  // Yaqin kunlar: ko'rinayotgan davrdan bugundan keyingilari
  const upcoming = useMemo(() => {
    const keys = Object.keys(byDay).filter((k) => k >= todayKey).sort();
    return keys.slice(0, 5).map((k) => ({
      k, list: byDay[k].filter((r) => !cancelled(r)),
    })).filter((x) => x.list.length);
  }, [byDay, todayKey]);

  return (
    <div className="space-y-5">
      {/* ===================== BOSH PANEL ===================== */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#1e1b4b] via-[#312e81] to-[#4c1d95] text-white p-5 sm:p-6 shadow-[0_20px_50px_-24px_rgba(49,46,129,0.75)]">
        <div className="pointer-events-none absolute -top-24 -right-16 w-72 h-72 rounded-full bg-fuchsia-500/25 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 -left-10 w-72 h-72 rounded-full bg-sky-400/20 blur-3xl" />
        <div className="relative flex flex-wrap items-center gap-3">
          <span className="grid place-items-center w-11 h-11 rounded-2xl bg-white/15 ring-1 ring-white/20 backdrop-blur">
            <CalendarDays size={21} />
          </span>
          <div className="min-w-0 mr-auto">
            <p className="text-[11px] uppercase tracking-[0.18em] text-indigo-200 font-semibold">
              Suhbat va sinov darslari
            </p>
            <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-[28px] font-extrabold tracking-tight leading-tight">
              {title}
            </h2>
          </div>

          <div className="flex items-center gap-1.5">
            <button onClick={() => shift(-1)} aria-label="Oldingi"
              className="w-9 h-9 grid place-items-center rounded-xl bg-white/10 ring-1 ring-white/15 hover:bg-white/20 transition">
              <ChevronLeft size={18} />
            </button>
            <button onClick={goToday}
              className="h-9 px-3.5 rounded-xl bg-white text-indigo-900 text-sm font-bold shadow-[0_3px_0_0_rgba(0,0,0,0.25)] active:translate-y-[2px] active:shadow-none transition">
              Bugun
            </button>
            <button onClick={() => shift(1)} aria-label="Keyingi"
              className="w-9 h-9 grid place-items-center rounded-xl bg-white/10 ring-1 ring-white/15 hover:bg-white/20 transition">
              <ChevronRight size={18} />
            </button>
          </div>

          <div className="flex p-1 rounded-xl bg-white/10 ring-1 ring-white/15">
            {([
              ["month", "Oy", LayoutGrid],
              ["week", "Hafta", Rows3],
              ["agenda", "Ro'yxat", ListTodo],
            ] as [View, string, typeof Users][]).map(([k, l, Icon]) => (
              <button key={k} onClick={() => { setView(k); setDay(null); }}
                className={`flex items-center gap-1.5 h-8 px-3 rounded-lg text-sm font-semibold transition ${
                  view === k ? "bg-white text-indigo-900 shadow" : "text-indigo-100 hover:text-white"}`}>
                <Icon size={14} />
                <span className="hidden sm:inline">{l}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="relative grid grid-cols-2 sm:grid-cols-5 gap-2.5 mt-5">
          {([
            ["Jami", stats.total, CalendarCheck, "from-white/20 to-white/5"],
            ["Suhbatlar", stats.interviews, Users, "from-violet-400/30 to-violet-400/5"],
            ["Sinov darslari", stats.demos, Presentation, "from-amber-400/30 to-amber-400/5"],
            ["Bugun", stats.today, Sun, "from-emerald-400/30 to-emerald-400/5"],
            ["Bekor qilingan", stats.cancelled, Ban, "from-rose-400/30 to-rose-400/5"],
          ] as [string, number, typeof Users, string][]).map(([l, v, Icon, g]) => (
            <div key={l} className={`rounded-2xl bg-gradient-to-br ${g} ring-1 ring-white/15 px-3.5 py-2.5 backdrop-blur`}>
              <p className="flex items-center gap-1.5 text-[11px] font-semibold text-indigo-100">
                <Icon size={13} /> {l}
              </p>
              <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold tabular-nums mt-0.5">
                {loading ? <span className="inline-block w-8 h-6 rounded bg-white/20 animate-pulse align-middle" /> : v}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-5 items-start">
        {/* ===================== ASOSIY KO'RINISH ===================== */}
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_-16px_rgba(15,23,42,0.18)] overflow-hidden">
          {view === "month" && (
            <MonthGrid anchor={anchor} byDay={byDay} todayKey={todayKey}
                       loading={loading} onDay={setDay} />
          )}
          {view === "week" && (
            <WeekGrid from={range.from} byDay={byDay} todayKey={todayKey}
                      onDay={setDay} />
          )}
          {view === "agenda" && (
            <Agenda byDay={byDay} loading={loading} onDay={setDay} />
          )}
        </div>

        {/* ===================== O'NG PANEL ===================== */}
        <aside className="space-y-4">
          <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_-16px_rgba(15,23,42,0.18)]">
            <p className="text-[11px] uppercase tracking-[0.16em] font-bold text-slate-400">Yaqin kunlar</p>
            {upcoming.length === 0 ? (
              <div className="py-8 text-center">
                <span className="mx-auto grid place-items-center w-12 h-12 rounded-2xl bg-slate-50 text-slate-300 mb-2">
                  <CalendarCheck size={22} />
                </span>
                <p className="text-sm text-slate-400">Rejalashtirilgan suhbat yo'q</p>
              </div>
            ) : (
              <div className="mt-3 space-y-4">
                {upcoming.map(({ k, list }) => (
                  <button key={k} onClick={() => setDay(k)} className="block w-full text-left group">
                    <p className={`text-xs font-bold mb-1.5 ${k === todayKey ? "text-emerald-600" : "text-slate-500"}`}>
                      {k === todayKey ? "Bugun · " : ""}{niceDay(k)}
                    </p>
                    <div className="space-y-1.5">
                      {list.slice(0, 3).map((r) => (
                        <div key={r.id} className="flex items-center gap-2.5 rounded-xl px-2.5 py-2 bg-slate-50 group-hover:bg-slate-100 transition">
                          <span className={`w-1 self-stretch rounded-full ${kindOf(r.kind).bar}`} />
                          <span className="text-xs font-bold tabular-nums text-slate-900 w-10">{r.time || "—"}</span>
                          <span className="text-sm text-slate-700 truncate flex-1">{r.candidate || "—"}</span>
                        </div>
                      ))}
                      {list.length > 3 && (
                        <p className="text-[11px] text-slate-400 pl-3">yana {list.length - 3} ta</p>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_12px_32px_-16px_rgba(15,23,42,0.18)]">
            <p className="text-[11px] uppercase tracking-[0.16em] font-bold text-slate-400 mb-3">Belgilar</p>
            <div className="space-y-2">
              {LEGEND.map(([k, l]) => (
                <p key={k} className="flex items-center gap-2.5 text-sm text-slate-600">
                  <span className={`w-2.5 h-2.5 rounded-full ${kindOf(k).dot}`} /> {l}
                </p>
              ))}
              <p className="flex items-center gap-2.5 text-sm text-slate-400 line-through">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-300" /> Bekor qilingan
              </p>
            </div>
            <p className="text-[11px] text-slate-400 mt-4 leading-relaxed">
              Klaviatura: <b>←</b> <b>→</b> — davr, <b>T</b> — bugun, <b>Esc</b> — yopish
            </p>
          </div>
        </aside>
      </div>

      {day && <DayDrawer k={day} list={byDay[day] || []} onClose={() => setDay(null)} />}
    </div>
  );
}

/* ============================== OY ============================== */
function MonthGrid({ anchor, byDay, todayKey, loading, onDay }: {
  anchor: Date; byDay: Record<string, Row[]>; todayKey: string;
  loading: boolean; onDay: (k: string) => void;
}) {
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const start = mondayOf(first);
  const last = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0);
  const weeks = Math.ceil(((first.getDay() + 6) % 7 + last.getDate()) / 7);
  const cells = Array.from({ length: weeks * 7 }, (_, i) => addDays(start, i));

  return (
    <div>
      <div className="grid grid-cols-7 border-b border-slate-100 bg-slate-50/60">
        {WD.map((w, i) => (
          <div key={w} className={`py-3 text-center text-[11px] font-bold uppercase tracking-[0.14em] ${
            i >= 5 ? "text-rose-400" : "text-slate-400"}`}>
            {w}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {cells.map((d, i) => {
          const k = iso(d);
          const inMonth = d.getMonth() === anchor.getMonth();
          const list = inMonth ? byDay[k] || [] : [];
          const isToday = k === todayKey;
          const weekend = i % 7 >= 5;
          const past = k < todayKey;
          return (
            <button
              key={k}
              onClick={() => inMonth && onDay(k)}
              disabled={!inMonth}
              className={`group relative flex flex-col justify-start min-h-[104px] sm:min-h-[118px] p-1.5 sm:p-2 text-left border-b border-r border-slate-100 transition ${
                i % 7 === 6 ? "border-r-0" : ""} ${
                !inMonth ? "bg-slate-50/40 cursor-default"
                  : weekend ? "bg-rose-50/20 hover:bg-indigo-50/40"
                    : "bg-white hover:bg-indigo-50/40"}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`inline-grid place-items-center w-7 h-7 rounded-full text-[13px] font-bold tabular-nums transition ${
                  isToday
                    ? "bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-[0_4px_12px_-2px_rgba(99,102,241,0.6)]"
                    : !inMonth ? "text-slate-300"
                      : past ? "text-slate-400" : "text-slate-700 group-hover:text-indigo-700"}`}>
                  {d.getDate()}
                </span>
                {list.length > 0 && (
                  <span className="hidden sm:inline text-[10px] font-bold text-slate-400 tabular-nums">
                    {list.length}
                  </span>
                )}
              </div>
              {loading && inMonth && i % 5 === 2 && (
                <div className="h-4 rounded-md bg-slate-100 animate-pulse" />
              )}
              <div className="space-y-1">
                {list.slice(0, 3).map((r) => {
                  const kd = kindOf(r.kind);
                  return (
                    <div key={r.id}
                      className={`relative flex items-center gap-1 overflow-hidden rounded-md pl-2 pr-1 py-[3px] text-[10.5px] leading-tight ${kd.chip} ${
                        cancelled(r) ? "line-through opacity-50" : ""}`}>
                      <span className={`absolute left-0 inset-y-0 w-[3px] ${kd.bar}`} />
                      {r.time && <b className="tabular-nums shrink-0">{r.time}</b>}
                      <span className="truncate">{r.candidate || "—"}</span>
                    </div>
                  );
                })}
                {list.length > 3 && (
                  <p className="text-[10px] font-semibold text-indigo-500 pl-1">+{list.length - 3} ta yana</p>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ============================== HAFTA ============================== */
function WeekGrid({ from, byDay, todayKey, onDay }: {
  from: Date; byDay: Record<string, Row[]>; todayKey: string;
  onDay: (k: string) => void;
}) {
  const days = Array.from({ length: 7 }, (_, i) => addDays(from, i));
  const hours = Array.from({ length: HOUR_TO - HOUR_FROM }, (_, i) => HOUR_FROM + i);
  const nowMin = (() => { const n = new Date(); return n.getHours() * 60 + n.getMinutes(); })();

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[760px]">
        <div className="grid grid-cols-[56px_repeat(7,1fr)] border-b border-slate-100 bg-slate-50/60">
          <div />
          {days.map((d, i) => {
            const k = iso(d);
            const isToday = k === todayKey;
            return (
              <button key={k} onClick={() => onDay(k)}
                className="py-2.5 text-center hover:bg-indigo-50/50 transition">
                <p className={`text-[11px] font-bold uppercase tracking-[0.14em] ${i >= 5 ? "text-rose-400" : "text-slate-400"}`}>{WD[i]}</p>
                <p className={`mx-auto mt-0.5 w-8 h-8 grid place-items-center rounded-full text-sm font-extrabold tabular-nums ${
                  isToday ? "bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-[0_4px_12px_-2px_rgba(99,102,241,0.6)]" : "text-slate-800"}`}>
                  {d.getDate()}
                </p>
              </button>
            );
          })}
        </div>
        <div className="relative grid grid-cols-[56px_repeat(7,1fr)] pt-2 pb-1">
          {/* Soat yozuvlari chiziqlar bilan bir xil — absolute joylashuv
              (oqimda manfiy margin har qatorda to'planib siljiydi) */}
          <div className="relative" style={{ height: HOUR_PX * hours.length }}>
            {hours.map((h) => (
              <span key={h} style={{ top: (h - HOUR_FROM) * HOUR_PX }}
                    className="absolute right-2 -translate-y-1/2 text-[10px] font-semibold text-slate-400 tabular-nums">
                {String(h).padStart(2, "0")}:00
              </span>
            ))}
          </div>
          {days.map((d, di) => {
            const k = iso(d);
            const list = byDay[k] || [];
            const untimed = list.filter((r) => minutesOf(r.time) == null);
            return (
              <div key={k} className={`relative border-l border-slate-100 ${di >= 5 ? "bg-rose-50/20" : ""}`}
                   style={{ height: HOUR_PX * hours.length }}>
                {hours.map((h) => (
                  <div key={h} style={{ top: (h - HOUR_FROM) * HOUR_PX }}
                       className="absolute inset-x-0 border-t border-slate-100" />
                ))}
                {k === todayKey && nowMin >= HOUR_FROM * 60 && nowMin <= HOUR_TO * 60 && (
                  <div className="absolute inset-x-0 z-20 flex items-center"
                       style={{ top: (nowMin - HOUR_FROM * 60) / 60 * HOUR_PX }}>
                    <span className="w-2 h-2 -ml-1 rounded-full bg-rose-500" />
                    <span className="flex-1 h-[2px] bg-rose-500/80" />
                  </div>
                )}
                {list.map((r) => {
                  const m = minutesOf(r.time);
                  if (m == null) return null;
                  const top = Math.max(0, (m - HOUR_FROM * 60) / 60 * HOUR_PX);
                  const h = Math.max(26, (r.minutes || 45) / 60 * HOUR_PX - 3);
                  const kd = kindOf(r.kind);
                  return (
                    <button key={r.id} onClick={() => onDay(k)}
                      style={{ top, height: h }}
                      className={`absolute left-1 right-1 z-10 overflow-hidden rounded-lg px-2 py-1 text-left text-white bg-gradient-to-br ${kd.grad} shadow-[0_6px_14px_-6px_rgba(15,23,42,0.45)] hover:brightness-110 transition ${
                        cancelled(r) ? "opacity-45 line-through" : ""}`}>
                      <p className="text-[10px] font-bold tabular-nums opacity-90">{r.time}</p>
                      <p className="text-[11px] font-semibold leading-tight truncate">{r.candidate || "—"}</p>
                    </button>
                  );
                })}
                {untimed.length > 0 && (
                  <span className="absolute top-1 right-1 z-10 text-[10px] font-bold rounded-full px-1.5 bg-slate-800 text-white">
                    +{untimed.length}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ============================== RO'YXAT ============================== */
function Agenda({ byDay, loading, onDay }: {
  byDay: Record<string, Row[]>; loading: boolean; onDay: (k: string) => void;
}) {
  const keys = Object.keys(byDay).sort();
  if (loading) {
    return (
      <div className="p-5 space-y-3">
        {[0, 1, 2, 3].map((i) => <div key={i} className="h-16 rounded-2xl bg-slate-100 animate-pulse" />)}
      </div>
    );
  }
  if (!keys.length) {
    return (
      <div className="py-20 text-center">
        <span className="mx-auto grid place-items-center w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-300 mb-3">
          <CalendarDays size={26} />
        </span>
        <p className="font-semibold text-slate-700">Bu davrda suhbat yo'q</p>
        <p className="text-sm text-slate-400 mt-1">Nomzodlar bo'limidan suhbat belgilang</p>
      </div>
    );
  }
  return (
    <div className="divide-y divide-slate-100">
      {keys.map((k) => {
        const d = new Date(k + "T00:00:00");
        return (
          <div key={k} className="flex gap-4 p-4 sm:p-5">
            <button onClick={() => onDay(k)} className="w-14 shrink-0 text-center">
              <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">{WD[(d.getDay() + 6) % 7]}</p>
              <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold text-slate-900 tabular-nums">{d.getDate()}</p>
            </button>
            <div className="flex-1 min-w-0 space-y-2">
              {byDay[k].map((r) => <EventCard key={r.id} r={r} compact onClick={() => onDay(k)} />)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ============================== KARTA ============================== */
function EventCard({ r, compact, onClick }: { r: Row; compact?: boolean; onClick?: () => void }) {
  const kd = kindOf(r.kind);
  const Icon = kd.icon;
  return (
    <div onClick={onClick}
      className={`relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white pl-4 pr-3.5 py-3 shadow-[0_1px_2px_rgba(15,23,42,0.04)] ${
        onClick ? "cursor-pointer hover:shadow-[0_10px_24px_-14px_rgba(15,23,42,0.35)] hover:-translate-y-px transition" : ""} ${
        cancelled(r) ? "opacity-60" : ""}`}>
      <span className={`absolute left-0 inset-y-0 w-1 ${kd.bar}`} />
      <div className="flex items-center gap-3">
        <span className={`grid place-items-center w-10 h-10 rounded-xl text-white text-sm font-extrabold bg-gradient-to-br ${kd.grad} shadow-md shrink-0`}>
          {initials(r.candidate)}
        </span>
        <div className="min-w-0 flex-1">
          <p className={`font-bold text-slate-900 truncate ${cancelled(r) ? "line-through" : ""}`}>
            {r.candidate || "—"}
          </p>
          <p className="flex items-center gap-1.5 text-xs text-slate-500 truncate">
            <Icon size={12} className="shrink-0" />
            {r.kind_label}{r.subject ? ` · ${r.subject}` : ""}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="font-[family-name:var(--font-display)] text-base font-extrabold tabular-nums text-slate-900">
            {r.time || "—"}
          </p>
          <span className={`inline-block mt-0.5 px-2 py-0.5 rounded-full text-[10.5px] font-bold ring-1 ${
            STATUS_TONE[r.status_tone] || STATUS_TONE.slate}`}>
            {r.status_label}
          </span>
        </div>
      </div>
      {!compact && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <span className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-slate-600">
            <Clock size={13} className="text-slate-400" />
            {r.minutes ? `${r.minutes} daqiqa` : "—"}
          </span>
          <span className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-slate-600 truncate">
            <MapPin size={13} className="text-slate-400 shrink-0" />
            <span className="truncate">{r.place || "Joy ko'rsatilmagan"}</span>
          </span>
          <span className="flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-slate-600 truncate col-span-2">
            <UserIcon size={13} className="text-slate-400 shrink-0" />
            <span className="truncate">{r.interviewer || "Suhbatdosh belgilanmagan"}</span>
          </span>
          {r.phone && (
            <a href={telHref(r.phone)}
              className="col-span-2 flex items-center justify-center gap-2 rounded-xl py-2 font-bold text-white bg-gradient-to-b from-emerald-400 to-emerald-600 shadow-[0_3px_0_0_#065f46] active:translate-y-[2px] active:shadow-none transition">
              <Phone size={14} /> {formatPhone(r.phone)}
            </a>
          )}
          {r.note && (
            <p className="col-span-2 flex items-start gap-1.5 rounded-lg bg-amber-50 px-2.5 py-2 text-amber-900">
              <StickyNote size={13} className="mt-0.5 shrink-0" /> {r.note}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ============================== KUN PANELI ============================== */
function DayDrawer({ k, list, onClose }: { k: string; list: Row[]; onClose: () => void }) {
  const [shown, setShown] = useState(false);
  // Siljib kirish animatsiyasi. setTimeout — rAF fon oynasida
  // ishlamasligi mumkin, panel esa doim ochilishi shart.
  useEffect(() => {
    const id = window.setTimeout(() => setShown(true), 16);
    return () => window.clearTimeout(id);
  }, []);
  const d = new Date(k + "T00:00:00");
  const live = list.filter((r) => !cancelled(r)).length;
  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className={`absolute inset-0 bg-slate-900/40 backdrop-blur-[2px] transition-opacity duration-300 ${shown ? "opacity-100" : "opacity-0"}`} />
      <aside
        onClick={(e) => e.stopPropagation()}
        className={`absolute right-0 inset-y-0 w-full max-w-md bg-slate-50 shadow-[-24px_0_60px_-20px_rgba(15,23,42,0.45)] flex flex-col transition-transform duration-300 ease-out ${
          shown ? "translate-x-0" : "translate-x-full"}`}>
        <div className="relative overflow-hidden bg-gradient-to-br from-[#1e1b4b] via-[#312e81] to-[#4c1d95] text-white px-5 pt-5 pb-6">
          <div className="pointer-events-none absolute -top-16 -right-10 w-48 h-48 rounded-full bg-fuchsia-500/25 blur-3xl" />
          <div className="relative flex items-start gap-3">
            <div className="text-center rounded-2xl bg-white/15 ring-1 ring-white/20 px-3 py-2">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-200">{WD[(d.getDay() + 6) % 7]}</p>
              <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold leading-none mt-0.5">{d.getDate()}</p>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-[family-name:var(--font-display)] text-xl font-extrabold">
                {MONTHS[d.getMonth()]} {d.getFullYear()}
              </p>
              <p className="text-sm text-indigo-200">
                {WD_FULL[(d.getDay() + 6) % 7]} · {live} ta uchrashuv
              </p>
            </div>
            <button onClick={onClose} aria-label="Yopish"
              className="w-9 h-9 grid place-items-center rounded-xl bg-white/10 ring-1 ring-white/15 hover:bg-white/20 transition">
              <X size={18} />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          {list.length === 0 ? (
            <div className="py-16 text-center">
              <span className="mx-auto grid place-items-center w-14 h-14 rounded-2xl bg-white text-slate-300 shadow-sm mb-3">
                <CalendarCheck size={26} />
              </span>
              <p className="font-semibold text-slate-700">Bu kunga suhbat yo'q</p>
              <p className="text-sm text-slate-400 mt-1">Bo'sh kun — rejalashtirish uchun qulay</p>
            </div>
          ) : (
            <ol className="relative space-y-4 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-px before:bg-gradient-to-b before:from-indigo-300 before:to-transparent">
              {list.map((r) => (
                <li key={r.id} className="relative pl-8">
                  <span className={`absolute left-[5px] top-4 w-[13px] h-[13px] rounded-full ring-4 ring-slate-50 ${kindOf(r.kind).dot}`} />
                  <EventCard r={r} />
                </li>
              ))}
            </ol>
          )}
        </div>
      </aside>
    </div>
  );
}
