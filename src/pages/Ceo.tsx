import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle, TrendingUp, TrendingDown, Wallet,
  UserMinus, MessageSquareWarning, RefreshCw, ArrowRight,
} from "lucide-react";
import { api, type CeoToday } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { PROFIT_VIEW, can } from "../lib/roles";
import { formatSom, formatDate } from "../lib/format";

/** Ogohlantirish darajasiga qarab rang. */
const LEVEL: Record<string, { box: string; dot: string; label: string }> = {
  high: {
    box: "bg-red-50 border-red-200",
    dot: "bg-red-500",
    label: "Shoshilinch",
  },
  normal: {
    box: "bg-amber-50 border-amber-200",
    dot: "bg-amber-500",
    label: "E'tibor bering",
  },
  low: {
    box: "bg-slate-50 border-slate-200",
    dot: "bg-slate-400",
    label: "Ma'lumot",
  },
};

function Money({
  label, value, hint, tone, icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone: "green" | "red" | "slate";
  icon: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const cls =
    tone === "green" ? "text-emerald-600"
      : tone === "red" ? "text-red-600"
        : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={15} className="text-slate-400" />
        <p className="text-sm text-slate-500">{label}</p>
      </div>
      <p className={`text-2xl font-semibold ${cls}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
    </div>
  );
}

function Small({
  label, value, hint, tone = "slate", to,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red" | "amber";
  to?: string;
}) {
  const cls =
    tone === "green" ? "text-emerald-600"
      : tone === "red" ? "text-red-600"
        : tone === "amber" ? "text-amber-600"
          : "text-slate-900";
  const inner = (
    <>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${cls}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </>
  );
  const box =
    "bg-white rounded-xl border border-slate-200 p-4 block" +
    (to ? " hover:border-brand-300 transition" : "");
  return to ? (
    <Link to={to} className={box}>
      {inner}
    </Link>
  ) : (
    <div className={box}>{inner}</div>
  );
}

export default function Ceo() {
  const { user } = useAuth();
  const [data, setData] = useState<CeoToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  function load() {
    setLoading(true);
    setErr("");
    api
      .get<CeoToday>("/ceo/today")
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  if (!can(user?.role, PROFIT_VIEW)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (err) return <p className="text-sm text-red-600 py-8">{err}</p>;
  if (!data) return null;

  const m = data.money;
  const a = data.attendance;

  return (
    <div className="max-w-6xl">
      <div className="flex items-start justify-between mb-5">
        <div>
          <p className="text-sm text-slate-500">
            {formatDate(data.date)} · {data.scope}
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <RefreshCw size={14} /> Yangilash
        </button>
      </div>

      {/* --- Eng muhimi: nima qilish kerak --- */}
      {data.alerts.length > 0 ? (
        <div className="mb-6">
          <p className="text-sm font-medium text-slate-700 mb-2">
            E'tiboringizni talab qiladi
          </p>
          <div className="space-y-2">
            {data.alerts.map((al, i) => {
              const L = LEVEL[al.level] || LEVEL.low;
              const body = (
                <div
                  className={`flex items-start gap-3 rounded-xl border p-4 ${L.box}`}
                >
                  <span
                    className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${L.dot}`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">
                      {al.title}
                    </p>
                    <p className="text-xs text-slate-600 mt-0.5">{al.detail}</p>
                  </div>
                  {al.link && (
                    <ArrowRight size={15} className="text-slate-400 mt-1 shrink-0" />
                  )}
                </div>
              );
              return al.link ? (
                <Link key={i} to={al.link} className="block">
                  {body}
                </Link>
              ) : (
                <div key={i}>{body}</div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-6">
          <p className="text-sm text-emerald-900">
            Bugun shoshilinch e'tibor talab qiladigan holat yo'q.
          </p>
        </div>
      )}

      {/* --- Pul --- */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <Money
          label="Bugungi tushum"
          value={formatSom(m.income)}
          hint={`${m.payment_count} ta to'lov`}
          tone="green"
          icon={TrendingUp}
        />
        <Money
          label="Bugungi xarajat"
          value={formatSom(m.expense)}
          tone="red"
          icon={TrendingDown}
        />
        <Money
          label="Sof pul oqimi"
          value={formatSom(m.net)}
          hint="tushum − xarajat"
          tone={m.net >= 0 ? "green" : "red"}
          icon={Wallet}
        />
      </div>

      {/* --- Sotuv va o'quvchilar --- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Small
          label="Yangi lidlar"
          value={String(data.sales.new_leads)}
          hint={`${data.sales.touched_leads} tasiga bog'lanildi`}
          to="/leads"
        />
        <Small
          label="Sotuvlar"
          value={String(data.sales.sales)}
          hint="bugun birinchi to'lov"
          tone="green"
          to="/students"
        />
        <Small
          label="Faol o'quvchilar"
          value={String(data.students.active)}
          to="/students"
        />
        <Small
          label="Bugun ketganlar"
          value={String(data.students.left_today)}
          tone={data.students.left_today > 0 ? "red" : "slate"}
          hint={
            data.students.left_list.length
              ? data.students.left_list.map((s) => s.full_name).join(", ")
              : undefined
          }
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <Small
          label="Qarzdorlar"
          value={String(data.students.debtors)}
          hint={
            data.students.total_debt
              ? formatSom(Math.abs(data.students.total_debt))
              : undefined
          }
          tone={data.students.debtors ? "red" : "slate"}
        />
        <Small
          label="Bugungi darslar"
          value={String(a.lessons_today)}
          hint={a.unmarked ? `${a.unmarked} tasida yoqlama yo'q` : "hammasi belgilangan"}
          tone={a.unmarked ? "amber" : "slate"}
          to="/groups"
        />
        <Small
          label="Davomat"
          value={a.percent !== null ? `${a.percent}%` : "—"}
          hint={a.marked ? `${a.present}/${a.marked}` : undefined}
          tone={a.percent !== null && a.percent < 80 ? "amber" : "green"}
        />
        <Small
          label="Ochiq shikoyatlar"
          value={String(data.complaints.open)}
          hint={data.complaints.overdue ? `${data.complaints.overdue} tasi kechikkan` : undefined}
          tone={data.complaints.open ? "red" : "slate"}
          to="/complaints"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* --- Eng katta qarzdorlar --- */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-3">
            <UserMinus size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              Eng katta qarzdorlar
            </p>
          </div>
          {data.students.top_debtors.length === 0 ? (
            <p className="text-sm text-slate-400 py-4">Qarzdor yo'q</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.students.top_debtors.map((d) => (
                  <tr key={d.id} className="border-b border-slate-50 last:border-0">
                    <td className="py-2">
                      <Link
                        to={`/students/${d.id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {d.full_name}
                      </Link>
                      {d.group && (
                        <span className="block text-xs text-slate-400">
                          {d.group}
                        </span>
                      )}
                    </td>
                    <td className="text-right text-red-600 font-medium tabular-nums">
                      {formatSom(d.balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* --- Muammoli guruhlar --- */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">Muammoli guruhlar</p>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            O'quvchisi kam yoki davomati past
          </p>
          {data.problem_groups.length === 0 ? (
            <p className="text-sm text-slate-400 py-4">
              Muammoli guruh yo'q
            </p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.problem_groups.map((g) => (
                  <tr key={g.id} className="border-b border-slate-50 last:border-0">
                    <td className="py-2">
                      <Link
                        to={`/groups/${g.id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {g.name}
                      </Link>
                      <span className="block text-xs text-slate-400">
                        {g.teacher || "ustoz yo'q"}
                      </span>
                    </td>
                    <td className="text-right text-xs text-amber-600">
                      {g.reasons.join(" · ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* --- Ochiq shikoyatlar --- */}
      {data.complaints.list.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquareWarning size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">Ochiq shikoyatlar</p>
            <div className="flex-1" />
            <Link
              to="/complaints"
              className="text-xs text-brand-600 hover:underline"
            >
              Hammasi →
            </Link>
          </div>
          <div className="space-y-2">
            {data.complaints.list.map((c) => (
              <div
                key={c.id}
                className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0"
              >
                <span
                  className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                    c.severity === "high" ? "bg-red-500" : "bg-amber-400"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800">{c.subject}</p>
                  <p className="text-xs text-slate-400">
                    {c.student || c.group || c.branch || "—"}
                    {c.age_days > 0 && ` · ${c.age_days} kundan beri ochiq`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
