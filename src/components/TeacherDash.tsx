import { Link } from "react-router-dom";
import {
  AlertTriangle, CalendarCheck, BookOpen, TrendingUp, TrendingDown,
  GraduationCap, Minus,
} from "lucide-react";
import type { TeacherDashboard } from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  red: "bg-red-50 border-red-200",
  amber: "bg-amber-50 border-amber-200",
  slate: "bg-slate-50 border-slate-200",
};
const DOT: Record<string, string> = {
  red: "bg-red-500",
  amber: "bg-amber-500",
  slate: "bg-slate-400",
};
const TEXT: Record<string, string> = {
  red: "text-red-800",
  amber: "text-amber-800",
  slate: "text-slate-700",
};

function pct(v: number | null) {
  return v == null ? "—" : `${v}%`;
}

/** O'sish/pasayish belgisi. Davomatda ko'p — yaxshi, shuning uchun
 *  musbat o'zgarish yashil. */
function Delta({ v }: { v: number | null }) {
  if (v == null || v === 0)
    return (
      <span className="text-xs text-slate-400 inline-flex items-center gap-0.5">
        <Minus size={11} /> o'zgarmadi
      </span>
    );
  const up = v > 0;
  const Icon = up ? TrendingUp : TrendingDown;
  return (
    <span
      className={`text-xs inline-flex items-center gap-0.5 ${
        up ? "text-emerald-600" : "text-red-600"
      }`}
    >
      <Icon size={11} />
      {up ? "+" : ""}
      {v}% o'tgan oyga nisbatan
    </span>
  );
}

/**
 * Ustozning dashboard bloki.
 *
 * Eng tepada ogohlantirishlar turadi — chunki ular bugun qilinadigan
 * ish. Har birining yonida nima qilish kerakligi yozilgan: "davomat
 * 68%" degan raqamning o'zi hech kimni harakatga keltirmaydi.
 */
export function TeacherDash({ d }: { d: TeacherDashboard }) {
  const att = d.attendance;
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
  const disc = (d as any).discipline;

  return (
    <div className="space-y-4 mb-6">
      {/* ---------- KRITIK OGOHLANTIRISHLAR ---------- */}
      {d.alerts.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={15} className="text-red-500" />
            <p className="text-sm font-medium text-slate-800">
              Kritik ogohlantirishlar
            </p>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
              {d.alert_count}
            </span>
          </div>
          <p className="text-xs text-slate-400 mb-3">{d.hint}</p>

          <div className="space-y-2">
            {d.alerts.map((a, i) => (
              <div
                key={i}
                className={`rounded-lg border p-3 ${
                  TONE[a.tone] || TONE.slate
                }`}
              >
                <div className="flex items-start gap-2">
                  <span
                    className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                      DOT[a.tone] || DOT.slate
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-sm font-medium ${
                        TEXT[a.tone] || TEXT.slate
                      }`}
                    >
                      {a.student || a.group || a.label}
                    </p>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {a.label}
                      {a.detail ? ` — ${a.detail}` : ""}
                      {a.student && a.group ? ` · ${a.group}` : ""}
                    </p>
                    <p className="text-xs text-slate-500 mt-1 italic">
                      {a.advice}
                    </p>
                  </div>
                  {a.kind === "attendance_missing" && (
                    <Link
                      to="/my-groups"
                      className="text-xs text-brand-600 hover:underline shrink-0"
                    >
                      belgilash
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---------- DAVOMAT ---------- */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center gap-2 mb-3">
          <CalendarCheck size={15} className="text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            Shu oygi davomat
          </p>
        </div>

        {disc && (
          <div className={`rounded-lg border p-3 mb-3 ${
            disc.state === "good" ? "bg-emerald-50/60 border-emerald-200"
            : disc.state === "mid" ? "bg-amber-50/60 border-amber-200"
            : disc.state === "bad" ? "bg-red-50/60 border-red-200"
            : "bg-slate-50 border-slate-200"}`}>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              <span className="font-medium text-slate-800">
                Yo'qlama intizomim:
              </span>
              <span className={`font-semibold ${
                disc.state === "good" ? "text-emerald-700"
                : disc.state === "mid" ? "text-amber-700"
                : "text-red-700"}`}>
                {disc.on_time_pct !== null
                  ? `${disc.on_time_pct}% o'z vaqtida`
                  : "hali o'lchov yo'q"}
              </span>
              <span className="text-slate-600">
                o'rtacha kechikish: {disc.avg_delay_label}
              </span>
              {disc.unmarked > 0 && (
                <span className="text-red-700 font-medium">
                  {disc.unmarked} dars belgilanmagan!
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Yo'qlamani dars boshlanishidan 60 daqiqa ichida qo'ysangiz
              "o'z vaqtida" hisoblanadi.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500 mb-0.5">O'rtacha davomat</p>
            <p className="text-2xl font-semibold text-slate-900">
              {pct(att.percent)}
            </p>
            <Delta v={att.change} />
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500 mb-0.5">Uy vazifasi</p>
            <p className="text-2xl font-semibold text-slate-900">
              {pct(att.homework_percent)}
            </p>
            <p className="text-xs text-slate-400">
              {att.homework_checked > 0
                ? `${att.homework_checked} ta tekshirilgan`
                : "hali tekshirilmagan"}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500 mb-0.5">Belgilangan yo'qlama</p>
            <p className="text-2xl font-semibold text-slate-900">
              {att.present}
              <span className="text-base text-slate-400">/{att.marks}</span>
            </p>
            <p className="text-xs text-slate-400">keldi / jami belgi</p>
          </div>
        </div>

        {d.groups.length > 0 && (
          <div className="space-y-1.5">
            {d.groups.map((g) => (
              <div
                key={g.id}
                className="flex items-center gap-3 px-3 py-2 rounded-lg border border-slate-100"
              >
                <span className="text-sm text-slate-800 w-32 truncate">
                  {g.name}
                </span>
                <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      g.low ? "bg-red-400" : "bg-brand-500"
                    }`}
                    style={{ width: `${g.percent ?? 0}%` }}
                  />
                </div>
                <span
                  className={`text-sm w-14 text-right ${
                    g.low ? "text-red-600 font-medium" : "text-slate-600"
                  }`}
                >
                  {pct(g.percent)}
                </span>
              </div>
            ))}
            <p className="text-xs text-slate-400 pt-1">
              {d.thresholds.group_attendance}% dan past guruh qizil bilan
              belgilanadi.
            </p>
          </div>
        )}
      </div>

      {/* ---------- RISKDAGI O'QUVCHILAR ---------- */}
      {d.risk_students.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <GraduationCap size={15} className="text-amber-500" />
            <p className="text-sm font-medium text-slate-700">
              E'tibor talab qiladigan o'quvchilar
            </p>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
              {d.risk_count}
            </span>
            <div className="flex-1" />
            <Link
              to="/my-students"
              className="text-xs text-brand-600 hover:underline"
            >
              hammasi
            </Link>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Davomati {d.thresholds.student_attendance}% dan past
          </p>
          <div className="space-y-1.5">
            {d.risk_students.slice(0, 8).map((s) => (
              <div
                key={s.student_id}
                className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-slate-100"
              >
                <div className="min-w-0">
                  <p className="text-sm text-slate-800 truncate">{s.student}</p>
                  <p className="text-xs text-slate-400">
                    {s.group}
                    {s.absent_streak > 0
                      ? ` · ketma-ket ${s.absent_streak} dars yo'q`
                      : ""}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-medium text-amber-700">
                    {s.attendance_percent}%
                  </p>
                  <p className="text-xs text-slate-400">
                    {s.missed} qoldirgan
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---------- RIVOJLANISH VAZIFALARI ---------- */}
      {(d.development.study_left > 0 || d.development.tasks.length > 0) && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <BookOpen size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              Rivojlanish vazifalari
            </p>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Trening va metodik topshiriqlar
          </p>

          {d.development.study_left > 0 && (
            <div className="mb-3">
              <p className="text-xs text-slate-500 mb-1.5">
                O'qish rejasi — {d.development.study_total} tadan{" "}
                {d.development.study_total - d.development.study_left} tasi
                bajarilgan
              </p>
              <div className="space-y-1">
                {d.development.study
                  .filter((x) => !x.done)
                  .slice(0, 5)
                  .map((x) => (
                    <Link
                      key={x.id}
                      to="/my-career"
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-100 hover:border-brand-300 transition"
                    >
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 shrink-0">
                        {x.kind_label}
                      </span>
                      <span className="text-sm text-slate-700 truncate">
                        {x.title}
                      </span>
                    </Link>
                  ))}
              </div>
            </div>
          )}

          {d.development.tasks.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-1.5">
                Topshiriqlar
                {d.development.tasks_overdue > 0
                  ? ` · ${d.development.tasks_overdue} tasi kechikkan`
                  : ""}
              </p>
              <div className="space-y-1">
                {d.development.tasks.slice(0, 5).map((t) => (
                  <Link
                    key={t.id}
                    to="/tasks"
                    className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg border border-slate-100 hover:border-brand-300 transition"
                  >
                    <span className="text-sm text-slate-700 truncate">
                      {t.title}
                    </span>
                    <span
                      className={`text-xs shrink-0 ${
                        t.overdue ? "text-red-600 font-medium" : "text-slate-400"
                      }`}
                    >
                      {t.deadline ? formatDate(t.deadline) : "muddatsiz"}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
