import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Award, BadgeCheck, ChevronRight, Flag } from "lucide-react";
import { formatDate } from "../../lib/format";
import { fmtNum } from "../../lib/studentApi";
import {
  roundEst,
  wbQuietGet,
  type TeacherWordStats as Stats,
  type WbQuiet,
} from "../../lib/wordbankApi";

/**
 * USTOZ — GURUHNING "SO'Z BILISH" HOLATI (2026-10-17, OWNER D2/D3).
 *
 * Har o'quvchi: tasdiqlangan so'zlar, eng yaxshi natija, shu haftadagi
 * o'sish, tugatilgan darajalar, oxirgi hajm testi (TAXMINIY) va FAQAT
 * tasdiqlangan sertifikatlar. "tekshirilmoqda" — faqat belgi (coin va
 * o'ringa ta'sir qilmaydi). Ma'lumot: GET /api/wordbank/teacher/students;
 * bo'lim butunlay o'chiq bo'lsa (404) — jim xabar, toast yo'q.
 */
export function TeacherWordStats({ groupId }: { groupId: number }) {
  const [res, setRes] = useState<WbQuiet<Stats> | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    setRes(null);
    wbQuietGet<Stats>(`/wordbank/teacher/students?group_id=${groupId}`).then((r) => {
      if (alive) setRes(r);
    });
    return () => {
      alive = false;
    };
  }, [groupId, tick]);

  const box = "bg-white rounded-xl shadow-sm border border-slate-200";
  if (!res) return <p className="text-sm text-slate-400 px-1">Yuklanmoqda…</p>;
  if (res.status === "off")
    return (
      <div className={`${box} p-4 text-sm text-slate-500`}>
        "So'z bilish" bo'limi hali yoqilmagan.
      </div>
    );
  if (res.status === "error")
    return (
      <div className={`${box} p-4 text-sm text-red-600`}>
        {res.message}{" "}
        <button type="button" onClick={() => setTick((t) => t + 1)} className="underline font-semibold">
          Qayta urinish
        </button>
      </div>
    );

  const d = res.data;
  const total = d.students.reduce((a, s) => a + (s.known || 0), 0);
  const week = d.students.reduce((a, s) => a + (s.week_gain || 0), 0);

  return (
    <div className="space-y-2">
      <Link to="/app/p/vocab-certs"
        className={`${box} p-3.5 flex items-center gap-3`}>
        <span className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center shrink-0">
          <Award size={18} className="text-amber-600" />
        </span>
        <span className="flex-1 min-w-0">
          <span className="block text-sm font-semibold text-slate-800">Sertifikatlar tekshiruvi</span>
          <span className="block text-[11px] text-slate-500">
            O'quvchilar yuklagan sertifikatlarni tasdiqlash
          </span>
        </span>
        <ChevronRight size={16} className="text-slate-300 shrink-0" />
      </Link>

      {!d.enabled ? (
        <div className={`${box} p-4 text-sm text-slate-500`}>
          Bu guruh filialida "So'z bilish" hali yoqilmagan.
        </div>
      ) : d.students.length === 0 ? (
        <div className={`${box} p-4 text-sm text-slate-500`}>Guruhda faol o'quvchi yo'q.</div>
      ) : (
        <>
          <div className={`${box} p-3.5 grid grid-cols-2 gap-2 text-center`}>
            <div>
              <p className="text-[11px] text-slate-500">Guruh bo'yicha jami</p>
              <p className="text-lg font-bold text-slate-900 tabular-nums">{fmtNum(total)}</p>
            </div>
            <div>
              <p className="text-[11px] text-slate-500">Shu hafta ({formatDate(d.week_start)} dan)</p>
              <p className="text-lg font-bold text-emerald-600 tabular-nums">+{fmtNum(week)}</p>
            </div>
          </div>

          <ol className="space-y-2">
            {d.students.map((s, i) => (
              <li key={s.id} className={`${box} p-3.5`}>
                <div className="flex items-start gap-3">
                  <span className="w-6 text-[13px] font-bold text-slate-400 text-center shrink-0 pt-0.5">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800 break-words">{s.name}</p>
                    <p className="text-[11.5px] text-slate-500 mt-0.5">
                      {s.bands_done}/20 daraja
                      {s.best > s.known ? ` · eng yaxshi ${fmtNum(s.best)}` : ""}
                      {s.size_test
                        ? ` · taxminiy ≈ ${fmtNum(roundEst(s.size_test.estimate))} (${fmtNum(
                            roundEst(s.size_test.low))}–${fmtNum(roundEst(s.size_test.high))})`
                        : ""}
                    </p>
                    {(s.certs.length > 0 || s.flagged) && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {s.certs.map((c) => (
                          <span key={c.id}
                                className="inline-flex items-center gap-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 px-1.5 py-0.5 text-[11px] font-semibold">
                            <BadgeCheck size={12} /> {c.label}
                          </span>
                        ))}
                        {s.flagged && (
                          <span className="inline-flex items-center gap-0.5 rounded-full bg-orange-50 border border-orange-200 text-orange-700 px-1.5 py-0.5 text-[11px] font-semibold">
                            <Flag size={11} /> tekshirilmoqda
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[17px] font-bold text-slate-900 leading-tight tabular-nums">
                      {fmtNum(s.known)}
                    </p>
                    <p className="text-[10.5px] text-slate-400">so'z</p>
                    {s.week_gain > 0 && (
                      <p className="text-[11px] font-semibold text-emerald-600 tabular-nums">
                        ▲{fmtNum(s.week_gain)}
                      </p>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ol>
          <p className="text-[11px] text-slate-400 px-1 leading-snug">
            Tasdiqlangan so'z — turli kunlarda to'g'ri topilgan va kamida bir
            marta yozib topilgan. Taxminiy hajm faqat testdan, hech narsaga
            ta'sir qilmaydi.
          </p>
        </>
      )}
    </div>
  );
}
