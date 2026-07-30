import { useEffect, useState } from "react";
import {
  UserCircle, Wallet, Clock, CheckCircle2, Circle, TrendingUp,
} from "lucide-react";
import { api, type MyProfile as Profile } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { formatPhone } from "../components/PhoneInput";

const PART_TONE: Record<string, string> = {
  fix: "bg-slate-100 text-slate-700",
  lessons: "bg-brand-100 text-brand-800",
  collection: "bg-emerald-100 text-emerald-800",
  new_clients: "bg-sky-100 text-sky-800",
  kpi: "bg-emerald-100 text-emerald-800",
  bonus: "bg-violet-100 text-violet-800",
};

/**
 * Mening profilim. Har bir xodim o'z ish haqi holatini ko'radi:
 * fiks, yo'qlamadan hisoblangan qism, KPI bonusi va jami.
 */
export default function MyProfile() {
  const [p, setP] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Profile>("/me/profile")
      .then(setP)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!p) return null;

  const max = Math.max(...p.parts.map((x) => x.amount), 1);

  return (
    <div className="max-w-4xl">
      {/* --- Shaxsiy --- */}
      <div className="flex items-center gap-4 mb-6">
        {p.photo ? (
          <img
            src={p.photo}
            alt=""
            className="w-16 h-16 rounded-xl object-cover"
          />
        ) : (
          <div className="w-16 h-16 rounded-xl bg-slate-100 flex items-center justify-center">
            <UserCircle size={32} className="text-slate-400" />
          </div>
        )}
        <div>
          <h1 className="text-xl font-semibold text-slate-900">
            {p.full_name}
          </h1>
          <p className="text-sm text-slate-500">
            {[p.position, p.branch].filter(Boolean).join(" · ")}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {[
              p.public_id,
              p.phone ? formatPhone(p.phone) : null,
              p.hired_date ? `${formatDate(p.hired_date)} dan beri` : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
      </div>

      {/* --- Ish haqi --- */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
        <div className="flex items-center gap-2 mb-1">
          <Wallet size={16} className="text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            Ish haqi holati
          </p>
          <span className="text-xs text-slate-400">{p.period}</span>
        </div>
        <p className="text-3xl font-semibold text-slate-900 mb-4">
          {formatSom(p.total)}
        </p>

        {p.parts.length === 0 ? (
          <p className="text-sm text-slate-400">
            Bu oyda hali hisoblanadigan narsa yo'q.
          </p>
        ) : (
          <div className="space-y-2.5">
            {p.parts.map((x) => (
              <div key={x.key}>
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span
                    className={`px-2 py-0.5 rounded-md text-xs font-medium ${
                      PART_TONE[x.key] || "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {x.label}
                  </span>
                  <span className="text-sm font-medium text-slate-800">
                    {formatSom(x.amount)}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-400"
                    style={{ width: `${(x.amount / max) * 100}%` }}
                  />
                </div>
                {x.hint && (
                  <p className="text-xs text-slate-400 mt-0.5">{x.hint}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* --- Ustoz bo'lsa: balans va guruhlar --- */}
      {p.teacher && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Yo'qlamadan hisoblangan
          </p>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <Mini
              label="Ishlab topgan"
              value={formatSom(p.teacher.earned_month)}
            />
            <Mini label="Olgan" value={formatSom(p.teacher.paid_month)} />
            <Mini
              label="Balans"
              value={formatSom(p.teacher.balance)}
              tone={
                p.teacher.balance > 0
                  ? "good"
                  : p.teacher.balance < 0
                    ? "bad"
                    : "plain"
              }
            />
          </div>
          {p.teacher.by_group.map((g) => (
            <div
              key={g.group_id}
              className="flex items-center justify-between gap-2 py-1.5 border-b border-slate-50 last:border-0"
            >
              <div className="min-w-0">
                <p className="text-sm text-slate-800">{g.group}</p>
                <p className="text-xs text-slate-400">
                  {formatSom(g.rate_per_student_month)} ÷ {g.standard_lessons}{" "}
                  dars = {formatSom(g.rate)} · {g.attendances} yo'qlama
                </p>
              </div>
              <span className="text-sm font-medium text-slate-800 shrink-0">
                {formatSom(g.amount)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* --- KPI --- */}
      {p.kpi && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">KPI</p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Mini
              label="Faol o'quvchilar"
              value={String(p.kpi.active_students)}
            />
            <Mini
              label="To'lov yig'ildi"
              value={`${p.kpi.collection_percent}%`}
              hint={`${formatSom(p.kpi.collected)} / ${formatSom(
                p.kpi.expected
              )}`}
              tone={p.kpi.collection_percent >= 90 ? "good" : "plain"}
            />
            <Mini
              label="Yangi mijozlar"
              value={String(p.kpi.new_clients)}
              hint={
                p.kpi.new_client_bonus
                  ? `bonus ${formatSom(p.kpi.new_client_bonus)}`
                  : "bonus yo'q"
              }
            />
            <Mini
              label="Jami bonus"
              value={formatSom(
                p.kpi.collection_bonus + p.kpi.new_client_bonus
              )}
              tone="good"
            />
          </div>
        </div>
      )}

      {/* --- Intizom --- */}
      {(p.late_count > 0 || p.onboarding_total > 0) && (
        <div className="grid gap-4 md:grid-cols-2">
          {p.late_count > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-center gap-2 mb-2">
                <Clock size={15} className="text-amber-500" />
                <p className="text-sm font-medium text-slate-700">
                  Shu oy kechikish
                </p>
              </div>
              <p className="text-lg font-semibold text-amber-700">
                {p.late_count} marta · {p.late_minutes} daqiqa
              </p>
            </div>
          )}

          {p.onboarding_total > 0 &&
            p.onboarding_done < p.onboarding_total && (
              <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-sm font-medium text-slate-700 mb-2">
                  Onboarding — {p.onboarding_done}/{p.onboarding_total}
                </p>
                <div className="space-y-1">
                  {p.onboarding.map((r) => (
                    <div
                      key={r.step}
                      className="flex items-center gap-2 text-sm"
                    >
                      {r.done ? (
                        <CheckCircle2
                          size={14}
                          className="text-emerald-500 shrink-0"
                        />
                      ) : (
                        <Circle size={14} className="text-slate-300 shrink-0" />
                      )}
                      <span
                        className={
                          r.done ? "text-slate-400 line-through" : "text-slate-700"
                        }
                      >
                        {r.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
        </div>
      )}
    </div>
  );
}

function Mini({
  label,
  value,
  hint,
  tone = "plain",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "plain" | "good" | "bad";
}) {
  const cls = {
    plain: "text-slate-900",
    good: "text-emerald-700",
    bad: "text-red-700",
  }[tone];
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className={`text-base font-semibold ${cls}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}
