import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Users, UserMinus, TrendingUp, Award } from "lucide-react";
import {
  api, type SalesPanel, type TeacherScoreboard, type AdminKpiResult,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";

const BAND_TONE: Record<string, string> = {
  good: "bg-emerald-100 text-emerald-700",
  ok: "bg-sky-100 text-sky-700",
  problem: "bg-amber-100 text-amber-700",
  critical: "bg-red-100 text-red-700",
};

const DAYS: Record<string, string> = {
  mon: "Du", tue: "Se", wed: "Ch", thu: "Pa",
  fri: "Ju", sat: "Sha", sun: "Ya",
};

/**
 * Administrator paneli. Daromad grafigi o'rniga — bugun nima qilish
 * kerak: qaysi guruhda bo'sh joy bor, kim ketdi, qaysi ustoz
 * o'quvchini ushlab tura olyapti.
 */
export function SalesPanelCards() {
  const [data, setData] = useState<SalesPanel | null>(null);

  useEffect(() => {
    api.get<SalesPanel>("/sales/panel").then(setData).catch(() => setData(null));
  }, []);

  if (!data) return null;

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* --- To'ldirilishi kerak bo'lgan guruhlar --- */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <Users size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              To'ldirilishi kerak bo'lgan guruhlar
            </p>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            {data.fill.free_seats} ta bo'sh joy ·{" "}
            <span className="text-brand-700">
              oyiga {formatSom(data.fill.lost_income)}
            </span>{" "}
            qo'shimcha tushum
          </p>

          {data.fill.rows.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">
              Hamma guruh to'la — ajoyib.
            </p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {data.fill.rows.map((r) => (
                <Link
                  key={r.group_id}
                  to={`/groups/${r.group_id}`}
                  className="block px-3 py-2 rounded-lg border border-slate-100 hover:border-brand-300 transition"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-slate-800 truncate">
                      {r.group}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${
                        BAND_TONE[r.band] || BAND_TONE.problem
                      }`}
                    >
                      {r.free} joy bo'sh
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                    <span>
                      {r.students}/{r.capacity}
                    </span>
                    {r.teacher && <span>· {r.teacher}</span>}
                    {r.days.length > 0 && (
                      <span>
                        · {r.days.map((d) => DAYS[d] || d).join(", ")}
                      </span>
                    )}
                    {r.time && <span>· {r.time}</span>}
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden mt-1.5">
                    <div
                      className={`h-full rounded-full ${
                        r.fill >= 70
                          ? "bg-sky-400"
                          : r.fill >= 50
                            ? "bg-amber-400"
                            : "bg-red-400"
                      }`}
                      style={{ width: `${r.fill}%` }}
                    />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* --- Shu oy ketganlar --- */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-1">
            <UserMinus size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              Shu oy ketganlar
            </p>
            {data.left.count > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                {data.left.count}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Nega ketganini bilish — keyingisini ushlab qolish demak
          </p>

          {data.left.rows.length === 0 ? (
            <p className="text-sm text-emerald-600 py-4 text-center">
              Bu oyda hech kim ketmadi.
            </p>
          ) : (
            <div className="space-y-1.5 max-h-80 overflow-y-auto">
              {data.left.rows.map((r) => (
                <Link
                  key={r.student_id}
                  to={`/students/${r.student_id}`}
                  className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-slate-100 hover:border-brand-300 transition"
                >
                  <div className="min-w-0">
                    <p className="text-sm text-slate-800 truncate">
                      {r.full_name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {[r.group, r.teacher].filter(Boolean).join(" · ")}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-slate-500">
                      {formatDate(r.left_date)}
                    </p>
                    {r.months !== null && r.months !== undefined && (
                      <p className="text-xs text-slate-400">
                        {r.months} oy o'qidi
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <TeacherMini />
    </>
  );
}

/** Ustozlar reytingi — qisqartirilgan ko'rinish. */
export function TeacherMini() {
  const [data, setData] = useState<TeacherScoreboard | null>(null);

  useEffect(() => {
    api
      .get<TeacherScoreboard>("/teachers/scoreboard?months=12")
      .then(setData)
      .catch(() => setData(null));
  }, []);

  if (!data || data.rows.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
      <div className="flex items-center gap-2 mb-1">
        <Award size={15} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Ustozlar natijasi</p>
        <div className="flex-1" />
        <Link
          to="/teachers"
          className="text-xs text-brand-600 hover:underline"
        >
          batafsil
        </Link>
      </div>
      <p className="text-xs text-slate-400 mb-3">
        O'quvchi kimning oldida qoladi va qancha qiymat keltiradi
      </p>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-slate-500 border-b border-slate-100">
            <th className="text-left py-2">Ustoz</th>
            <th className="text-right w-20">O'quvchi</th>
            <th className="text-right w-24">Retention</th>
            <th className="text-right w-28">LTV</th>
            <th className="text-right w-20">O'rtacha</th>
          </tr>
        </thead>
        <tbody>
          {data.rows.slice(0, 8).map((r) => (
            <tr key={r.teacher_id} className="border-b border-slate-50">
              <td className="py-2">
                <span className="text-slate-400 mr-1.5">{r.rank}.</span>
                <span className="text-slate-800">{r.full_name}</span>
              </td>
              <td className="text-right text-slate-600">{r.students}</td>
              <td
                className={`text-right font-medium ${
                  r.retention >= 85
                    ? "text-emerald-600"
                    : r.retention >= 70
                      ? "text-slate-600"
                      : "text-red-600"
                }`}
              >
                {r.retention}%
              </td>
              <td className="text-right text-slate-700">
                {formatSom(r.ltv)}
              </td>
              <td className="text-right text-slate-500">{r.avg_months} oy</td>
            </tr>
          ))}
        </tbody>
      </table>

      {data.averages.retention !== null && (
        <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
          <TrendingUp size={11} />
          O'rtacha: retention {data.averages.retention}%, LTV{" "}
          {formatSom(data.averages.ltv ?? 0)}, o'quvchi{" "}
          {data.averages.avg_months} oy qoladi
        </p>
      )}
    </div>
  );
}

/**
 * Administratorning eng muhim raqami: ESKI to'lovlarni yig'ish foizi.
 * Bonus aynan shundan hisoblanadi, shuning uchun Dashboard'da xonalar
 * bandligidan ham tepada turadi.
 *
 * Yangi mijozning birinchi to'lovi bu foizga kirmaydi — u alohida
 * bonus. Ko'rsatkich filial bo'yicha jamoaviy: bir filialdagi ikkala
 * administrator ham bir xil raqamni ko'radi.
 */
export function AdminCollectionCard() {
  const [d, setD] = useState<AdminKpiResult | null>(null);
  const now = new Date();

  useEffect(() => {
    api
      .get<AdminKpiResult>(
        `/kpi/admins?year=${now.getFullYear()}&month=${now.getMonth() + 1}`
      )
      .then(setD)
      .catch(() => setD(null));
  }, []);

  const row = d?.rows?.[0];
  if (!row) return null;

  const pct = row.collection_percent;
  const tone =
    pct >= 95 ? "text-emerald-600"
      : pct >= 80 ? "text-amber-600"
        : "text-red-600";
  const bar =
    pct >= 95 ? "bg-emerald-500"
      : pct >= 80 ? "bg-amber-500"
        : "bg-red-500";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
      <div className="flex flex-wrap items-center gap-5">
        <div>
          <div className="flex items-center gap-1.5 mb-0.5">
            <TrendingUp size={14} className="text-slate-400" />
            <p className="text-xs text-slate-500">
              Eski to'lovlarni yig'ish
            </p>
          </div>
          <p className={`text-3xl font-semibold leading-none ${tone}`}>
            {pct}
            <span className="text-lg text-slate-400">%</span>
          </p>
        </div>

        <div className="flex-1 min-w-[220px]">
          <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={`h-full rounded-full ${bar}`}
              style={{ width: `${Math.min(100, pct)}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1.5">
            {formatSom(row.collected)} yig'ildi ·{" "}
            {formatSom(row.expected)} hisoblangan · qoldiq{" "}
            <b className="text-red-600">
              {formatSom(Math.max(0, row.expected - row.collected))}
            </b>
          </p>
        </div>

        <div className="flex gap-5">
          <div>
            <p className="text-xs text-slate-500">Yig'im bonusi</p>
            <p className="text-sm font-semibold text-emerald-600">
              {formatSom(row.collection_bonus)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">
              Yangi mijoz ({row.new_clients} ta)
            </p>
            <p className="text-sm font-semibold text-brand-700">
              {formatSom(row.new_client_bonus)}
            </p>
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-400 mt-3">
        Ko'rsatkich filial bo'yicha jamoaviy — bir filialdagi barcha
        administratorlar uchun bir xil. Yangi mijozning birinchi to'lovi
        bu foizga kirmaydi, u alohida bonus.
      </p>
    </div>
  );
}
