import { useEffect, useState } from "react";
import {
  UserCircle, Wallet, Clock, TrendingUp,
  BookOpen, PlayCircle, ExternalLink,
} from "lucide-react";
import {
  api, type MyProfile as Profile, type LibraryList,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { formatPhone } from "../components/PhoneInput";
import TelegramLink from "../components/TelegramLink";
import MyFunctions from "../components/guide/MyFunctions";

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
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api
      .get<Profile>("/me/profile")
      .then(setP)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (error)
    return (
      <div className="py-8">
        <p className="text-sm text-red-600 mb-2">{error}</p>
        <button
          onClick={load}
          className="text-sm text-brand-600 hover:text-brand-700 underline"
        >
          Qayta urinish
        </button>
      </div>
    );
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

      {/* --- Telegram (2026-08-15): zaxira va xato ogohlantirishi --- */}
      <TelegramLink />

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
      {/* MENING FUNKSIYALARIM (2026-08-23, Jahongir): lavozimga tegishli
          ishlar ro'yxati — bilmasa bosadi, tizim ko'rsatib boradi */}
      <div className="mb-6">
        <MyFunctions />
      </div>

      {/* ONBOARDING RO'YXATI OLIB TASHLANDI (2026-08-23, Jahongir:
          "manabu 10ta onboarding olib tashla ishlamayabdi bu faqat
          HR uchun qolsin"). Xodim o'zi belgilay olmasdi — HR
          qo'yadigan belgilar edi, shuning uchun profilda faqat
          chalkashtirardi. Endi u faqat HR bo'limida (Hr.tsx va
          xodim kartasi) turadi. Bu yerda o'rniga "Mening
          funksiyalarim" — xodim O'ZI ishlata oladigan narsa. */}
      {p.late_count > 0 && (
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

        </div>
      )}

      <MyLibrary />
    </div>
  );
}

/** Kutubxona: onboarding paytida ko'rishim kerak bo'lgan materiallar.
 *
 *  Ko'rgan foizni o'zim belgilayman; "topshirdi" degan belgini esa HR
 *  qo'yadi. Daraja ko'tarishda shu ro'yxat qaraladi. */
export function MyLibrary() {
  const [d, setD] = useState<LibraryList | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  const load = () => {
    api
      .get<LibraryList>("/library")
      .then(setD)
      .catch(() => setD(null));
  };
  useEffect(load, []);

  async function setPercent(id: number, pct: number) {
    setBusy(id);
    try {
      await api.put(`/library/${id}/progress`, { percent: pct });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  if (!d || d.items.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mt-4">
      <div className="flex items-center gap-2 mb-1">
        <BookOpen size={15} className="text-brand-500" />
        <p className="text-sm font-medium text-slate-700">Kutubxona</p>
        <span className="text-xs text-slate-400">
          {d.my_done}/{d.my_total} topshirilgan
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-3">
        Ko'rganingizni o'zingiz belgilaysiz. "Topshirdi" belgisini HR
        qo'yadi — daraja ko'tarishda shu ro'yxat qaraladi.
      </p>

      <div className="space-y-2">
        {d.items.map((it) => (
          <div
            key={it.id}
            className="rounded-lg border border-slate-200 px-3 py-2.5"
          >
            <div className="flex flex-wrap items-center gap-2">
              {it.kind === "video" ? (
                <PlayCircle size={15} className="text-slate-400 shrink-0" />
              ) : (
                <BookOpen size={15} className="text-slate-400 shrink-0" />
              )}
              <span className="text-sm text-slate-800">{it.title}</span>
              <span className="text-xs text-slate-400">
                {it.kind_label}
                {it.minutes ? ` · ${it.minutes} daq` : ""}
              </span>
              {it.passed && (
                <span className="text-[10px] uppercase tracking-wide bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded">
                  topshirdim
                </span>
              )}
              <div className="flex-1" />
              {it.url && (
                <a
                  href={it.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline"
                >
                  Ochish <ExternalLink size={12} />
                </a>
              )}
            </div>

            {it.description && (
              <p className="text-xs text-slate-400 mt-1">{it.description}</p>
            )}

            <div className="flex items-center gap-2 mt-2">
              <span className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                <span
                  className={`h-full block ${
                    it.passed ? "bg-emerald-500" : "bg-brand-500"
                  }`}
                  style={{ width: `${it.percent}%` }}
                />
              </span>
              <span className="text-xs text-slate-500 w-10 text-right">
                {it.percent}%
              </span>
              {!it.passed &&
                [25, 50, 75, 100].map((v) => (
                  <button
                    key={v}
                    onClick={() => setPercent(it.id, v)}
                    disabled={busy === it.id || it.percent >= v}
                    className="px-2 py-0.5 rounded-md text-[11px] border border-slate-200 text-slate-500 hover:border-brand-300 hover:text-brand-700 disabled:opacity-30"
                  >
                    {v}%
                  </button>
                ))}
            </div>
          </div>
        ))}
      </div>
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
