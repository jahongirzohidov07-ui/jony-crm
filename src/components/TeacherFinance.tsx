import { useEffect, useState } from "react";
import {
  Wallet, ChevronDown, ChevronUp, TrendingUp, Info,
} from "lucide-react";
import { api, type TeacherFinance as Fin, type TeacherFinanceMonth } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { SalaryBreakdown } from "./SalaryBreakdown";

/**
 * USTOZNING MOLIYA BO'LIMI — oylar bo'yicha oylik tarixi.
 *
 * 2026-09-05, Jahongir: "ustozlarda moliya bo'limi qo'shilib oldin
 * olgan oyliklari har oylik oyliklar o'sha yerga hisoblanib borsin
 * oyliklar tarixi bo'lsin".
 *
 * Har oy: ishlab topgan (yo'qlamadan) · shu oy oyligi uchun berilgan ·
 * qoldiq. Oy bosilsa — guruhlar kesimi va shu oy oyligiga yozilgan
 * pullar ro'yxati.
 *
 * NAVBAT QOIDASI (2026-09-05, Jahongir: "balans bilan o'tgan oyniki va
 * bu oyniki ham turishi kerak ... ustozlar bir oyniki deb o'ylab
 * qolyabdi"): berilgan pul eng eski berilmagan oyning oyligiga yoziladi
 * — avgust oyligi sentabrda berilsa, avgustniki. Shunda har oyning
 * qoldig'i aniq, balans = oylar qoldiqlarining yig'indisi.
 *
 * Hech narsa saqlanmaydi: server har safar yo'qlamadan qayta
 * hisoblaydi, shuning uchun raqam "Darslarim va oyligim" va rahbarning
 * Oyliklar sahifasi bilan bir xil.
 */
const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];

export function monthTitle(period: string): string {
  const [y, m] = period.split("-").map(Number);
  if (!y || !m) return period;
  return `${MONTHS[m - 1]} ${y}`;
}

export function TeacherFinance({
  teacherId,
  self = false,
  compact = false,
}: {
  teacherId?: number;
  self?: boolean;
  /** Mobil: kichik shrift, ustunlar kam */
  compact?: boolean;
}) {
  const [d, setD] = useState<Fin | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<Fin>(self ? "/my/finance" : `/teachers/${teacherId}/finance`)
      .then((r) => {
        setD(r);
        // Hozirgi oy sukut bo'yicha ochiq turadi
        const cur = r.months?.find((m) => m.is_current);
        setOpen(cur ? cur.period : r.months?.[0]?.period ?? null);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }, [teacherId, self]);

  if (loading) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda...</p>;
  if (err) return <p className="text-sm text-slate-500 py-6">{err}</p>;
  if (!d) return null;
  if (d.volunteer) return <p className="text-sm text-slate-500 py-6">{d.hint}</p>;

  const months = d.months ?? [];
  const withActivity = months.filter((m) => m.earned || m.paid_for || m.paid_in_month).length;

  return (
    <div className="space-y-4">
      {/* --- Umumiy --- */}
      <div className="grid grid-cols-3 gap-2">
        <Stat label="Balans (jami)" value={formatSom(d.balance)}
          hint={d.balance === 0 ? "hisob yopilgan" : d.balance_label}
          tone={d.balance > 0 ? "good" : d.balance < 0 ? "bad" : "plain"} />
        <Stat
          label={`O'tgan oy${d.prev_title ? ` — ${d.prev_title.split(" ")[0]}` : ""} qoldig'i`}
          value={formatSom(d.prev_left ?? 0)}
          hint={d.prev_period ? "berilmagan qismi" : "o'tgan oy yo'q"}
          tone={(d.prev_left ?? 0) > 0 ? "good" : (d.prev_left ?? 0) < 0 ? "bad" : "plain"} />
        <Stat
          label={`Bu oy — ${monthTitle(d.month).split(" ")[0]} qoldig'i`}
          value={formatSom(d.month_left ?? 0)}
          hint="berilmagan qismi"
          tone={(d.month_left ?? 0) > 0 ? "good" : (d.month_left ?? 0) < 0 ? "bad" : "plain"} />
      </div>
      <p className="text-[11px] text-slate-400 -mt-2">
        Jami ishlab topgan {formatSom(d.earned_total)} ({monthTitle(d.since)} dan beri) ·
        jami olgan {formatSom(d.paid_total)}
      </p>

      {/* --- Oylar --- */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <TrendingUp size={13} className="text-slate-400" />
          <p className="text-xs font-medium text-slate-700">
            Oyliklar tarixi
          </p>
          <span className="text-[11px] text-slate-400">
            · {withActivity} oy
          </span>
        </div>

        {months.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">Hali yozuv yo'q</p>
        ) : (
          <div className="rounded-xl border border-slate-200 overflow-hidden divide-y divide-slate-100">
            {!compact && (
              <div className="grid grid-cols-[1.3fr_1fr_1fr_1fr_20px] gap-2 px-3 py-2 bg-slate-50 text-[11px] font-medium text-slate-500">
                <span>Oy</span>
                <span className="text-right">Ishlab topgan</span>
                <span className="text-right">Shu oy uchun berilgan</span>
                <span className="text-right">Qoldiq</span>
                <span />
              </div>
            )}
            {months.map((m) => (
              <MonthRow
                key={m.period}
                m={m}
                teacherId={teacherId ?? d.teacher_id}
                open={open === m.period}
                compact={compact}
                onToggle={() => setOpen(open === m.period ? null : m.period)}
              />
            ))}
          </div>
        )}
      </div>

      <p className="text-[11px] text-slate-400 flex items-start gap-1">
        <Info size={12} className="mt-0.5 shrink-0" />
        <span>
          "Ishlab topgan" — o'sha oyning yo'qlamalaridan, o'sha kundagi
          stavka bilan. Berilgan pul har doim eng eski berilmagan oyning
          oyligiga yoziladi (avgust oyligi sentabrda berilsa — avgustniki).
          "Qoldiq" — o'sha oy oyligining hali berilmagan qismi; balans —
          qoldiqlar yig'indisi.
        </span>
      </p>
    </div>
  );
}

function MonthRow({
  m, teacherId, open, compact, onToggle,
}: {
  m: TeacherFinanceMonth;
  teacherId?: number;
  open: boolean;
  compact: boolean;
  onToggle: () => void;
}) {
  const empty = !m.earned && !m.paid_for && !m.paid_in_month;
  const leftTone =
    m.left > 0 ? "text-emerald-700" : m.left < 0 ? "text-red-700" : "text-slate-500";

  return (
    <div className={empty ? "opacity-60" : ""}>
      <button
        onClick={onToggle}
        className={`w-full text-left px-3 py-2.5 hover:bg-slate-50 transition ${
          compact
            ? "flex items-center gap-2"
            : "grid grid-cols-[1.3fr_1fr_1fr_1fr_20px] gap-2 items-center"
        }`}
      >
        {compact ? (
          <>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800">
                {m.title || monthTitle(m.period)}
                {m.is_current && (
                  <span className="ml-1.5 text-[10px] font-normal text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">
                    hozirgi
                  </span>
                )}
                {m.sealed && (
                  <span
                    title="Oy yopilgan — bu raqam endi o'zgarmaydi"
                    className="ml-1.5 text-[10px] font-normal text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded"
                  >
                    muhrlangan
                  </span>
                )}
              </p>
              <p className="text-[11px] text-slate-500">
                {m.lessons} dars · {m.attendances} yo'qlama
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-900">
                {formatSom(m.earned)}
              </p>
              <p className="text-[11px] text-slate-500">
                berilgan {formatSom(m.paid_for)} ·{" "}
                <span className={leftTone}>
                  {m.left >= 0 ? "qoldiq" : "ortiqcha"} {formatSom(Math.abs(m.left))}
                </span>
              </p>
            </div>
            {open ? <ChevronUp size={16} className="text-slate-400" />
              : <ChevronDown size={16} className="text-slate-400" />}
          </>
        ) : (
          <>
            <div>
              <p className="text-sm font-medium text-slate-800">
                {m.title || monthTitle(m.period)}
                {m.is_current && (
                  <span className="ml-1.5 text-[10px] font-normal text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded">
                    hozirgi
                  </span>
                )}
                {m.sealed && (
                  <span
                    title="Oy yopilgan — bu raqam endi o'zgarmaydi"
                    className="ml-1.5 text-[10px] font-normal text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded"
                  >
                    muhrlangan
                  </span>
                )}
              </p>
              <p className="text-[11px] text-slate-500">
                {m.lessons} dars · {m.attendances} yo'qlama
              </p>
            </div>
            <span className="text-right text-sm font-semibold text-slate-900">
              {formatSom(m.earned)}
            </span>
            <span className="text-right text-sm text-slate-700">
              {formatSom(m.paid_for)}
            </span>
            <span className={`text-right text-sm font-medium ${leftTone}`}>
              {formatSom(m.left)}
            </span>
            {open ? <ChevronUp size={16} className="text-slate-400" />
              : <ChevronDown size={16} className="text-slate-400" />}
          </>
        )}
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-3 bg-slate-50/60">
          {compact && (
            <div className="grid grid-cols-2 gap-2 pt-1">
              <Mini label="Shu oy uchun berilgan" value={formatSom(m.paid_for)} cls="text-slate-800" />
              <Mini label="Qoldiq" value={formatSom(m.left)} cls={leftTone} />
            </div>
          )}

          {/* To'liq hisobot: filial -> guruh -> o'quvchi (2026-09-15) */}
          {teacherId && (m.earned || m.lessons) ? (
            <SalaryBreakdown teacherId={teacherId} period={m.period} compact={compact} />
          ) : m.by_group.length > 0 ? (
            <div>
              <p className="text-[11px] font-medium text-slate-500 mb-1">
                Qanday hisoblandi
              </p>
              <div className="space-y-1">
                {m.by_group.map((g) => (
                  <div key={g.group_id}
                    className="flex items-center justify-between gap-2 text-xs bg-white rounded-lg border border-slate-100 px-2.5 py-1.5">
                    <div className="min-w-0">
                      <p className="text-slate-800 truncate">{g.group}</p>
                      <p className="text-[11px] text-slate-500">
                        {g.attendances} yo'qlama × {formatSom(g.rate)}
                        <span className="text-slate-400">
                          {" "}({formatSom(g.rate_per_student_month)} ÷ {g.standard_lessons})
                        </span>
                      </p>
                    </div>
                    <span className="font-medium text-slate-900 shrink-0">
                      {formatSom(g.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-[11px] text-slate-400 pt-1">
              Bu oyda yo'qlama yo'q.
            </p>
          )}

          {/* Olingan pullar */}
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <Wallet size={12} className="text-slate-400" />
              <p className="text-[11px] font-medium text-slate-500">
                Shu oy oyligi uchun berilgan pullar
              </p>
              {m.paid_in_month > 0 && (
                <span className="text-[11px] text-slate-400">
                  · shu oyda qo'lga tekkan {formatSom(m.paid_in_month)}
                </span>
              )}
            </div>
            {m.payments.length === 0 ? (
              <p className="text-[11px] text-slate-400">Bu oy oyligi uchun hali pul berilmagan</p>
            ) : (
              <div className="space-y-1">
                {m.payments.map((p) => (
                  <div key={p.id}
                    className="flex items-center gap-2 text-xs bg-white rounded-lg border border-slate-100 px-2.5 py-1.5">
                    <span className="text-slate-400 w-20 shrink-0">
                      {p.date ? formatDate(p.date) : "—"}
                    </span>
                    <span className="text-slate-500 w-14 shrink-0">{p.kind_label}</span>
                    <span className="font-medium text-slate-900">
                      {formatSom(p.applied)}
                      {p.split && (
                        <span className="text-slate-400 font-normal">
                          {" "}({formatSom(p.amount)} dan)
                        </span>
                      )}
                    </span>
                    {p.note && (
                      <span className="text-slate-400 truncate flex-1">{p.note}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({
  label, value, hint, tone = "plain",
}: {
  label: string; value: string; hint?: string;
  tone?: "plain" | "brand" | "good" | "bad";
}) {
  const cls = {
    plain: "bg-white border-slate-200 text-slate-900",
    brand: "bg-brand-50 border-brand-200 text-brand-800",
    good: "bg-emerald-50 border-emerald-200 text-emerald-800",
    bad: "bg-red-50 border-red-200 text-red-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-3 ${cls}`}>
      <p className="text-[11px] text-slate-500 mb-0.5">{label}</p>
      <p className="text-sm sm:text-base font-semibold leading-tight">{value}</p>
      {hint && <p className="text-[10px] text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Mini({ label, value, cls }: { label: string; value: string; cls: string }) {
  return (
    <div className="bg-white rounded-lg border border-slate-100 px-2.5 py-1.5">
      <p className="text-[10px] text-slate-400">{label}</p>
      <p className={`text-sm font-semibold ${cls}`}>{value}</p>
    </div>
  );
}
