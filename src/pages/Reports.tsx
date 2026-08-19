import { useEffect, useState } from "react";
import SalesFunnel from "../components/SalesFunnel";
import { PayrollTab } from "../components/Payroll";
import { Download, Users, TrendingDown } from "lucide-react";
import {
  api,
  type AdminKpiResult,
  type KpiRules,
  type FunnelReport,
  type SalesManagerReport,
  type SalesWindow,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, PAYROLL_VIEW, FOUNDER, can } from "../lib/roles";
import { MONTHS } from "../lib/expenses";
import { stageLabel } from "../lib/leads";
import { formatSom } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "payroll" | "discipline" | "tasks" | "funnel" | "sales" | "kpi";

// OYLIKLAR BO'LIMI MOLIYADAN SHU YERGA KO'CHDI (2026-08-20,
// Jahongir: "uzr molyia bolimidan hisobotlarga olib ot demoqchi
// edim"). Ichida: Ustozlar oyligi, O'quvchi kesimida, Examiner,
// Support teacher, Ma'muriy xodimlar, Darajalar.
const TABS: { key: Tab; label: string }[] = [
  { key: "payroll", label: "Oyliklar" },
  { key: "discipline", label: "Ustoz intizomi" },
  { key: "tasks", label: "Vazifalar" },
  { key: "funnel", label: "Sales funnel" },
  { key: "sales", label: "Sotuv menejerlari" },
  { key: "kpi", label: "Adminlar KPI" },
];

/** Katta summalarni o'qishga oson qilib qisqartiradi: 12 400 000 -> "12.4 mln". */
function short(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (abs >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

function Stat({
  label, value, hint, tone = "slate", icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "slate" | "green" | "red";
  icon?: React.ComponentType<{ size?: number; className?: string }>;
}) {
  const toneClass =
    tone === "green" ? "text-emerald-600"
      : tone === "red" ? "text-red-600"
      : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon size={14} className="text-slate-400" />}
        <p className="text-xs text-slate-500">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${toneClass}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-slate-400 mt-3 max-w-3xl">{children}</p>;
}

// --------------------------------------------------------- Ustozlar oyligi

// ------------------------------------------------------------ Sales funnel
function FunnelTab() {
  const [data, setData] = useState<FunnelReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<FunnelReport>("/reports/funnel")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;

  const lf = data.leads;
  const sf = data.students;
  const maxLost = Math.max(...sf.months.map((m) => m.lost), 1);

  return (
    <div>
      {/* ---------------- Lid voronkasi ---------------- */}
      <h3 className="font-medium text-slate-800 mb-1">
        1-qism · So'rovdan o'quvchigacha
      </h3>
      <p className="text-xs text-slate-500 mb-4">
        Qaysi bosqichda odam yo'qolayotgani
      </p>

      <SalesFunnel
        total={lf.total}
        stages={lf.stages}
        rejected={lf.rejected}
        labelOf={stageLabel}
      />

      {/* ---------------- Oylik voronka ---------------- */}
      <h3 className="font-medium text-slate-800 mb-1">
        2-qism · To'lovdan keyin qaysi oyda ketyapti
      </h3>
      <p className="text-xs text-slate-500 mb-4">
        Birinchi to'lovdan boshlab 12 oygacha
      </p>

      {sf.paying === 0 ? (
        <p className="text-sm text-slate-400 py-4">
          Hali to'lov qilgan o'quvchi yo'q.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
            <Stat label="To'lagan o'quvchilar" value={String(sf.paying)} icon={Users} />
            <Stat
              label="Ketganlar"
              value={String(sf.churned)}
              hint={`${Math.round((sf.churned / sf.paying) * 100)}%`}
              tone={sf.churned > 0 ? "red" : "slate"}
            />
            <Stat
              label="Eng ko'p yo'qotiladigan oy"
              value={sf.worst_month ? `${sf.worst_month}-oy` : "—"}
              hint={sf.worst_month ? `${sf.worst_month_lost} ta o'quvchi` : undefined}
              icon={TrendingDown}
              tone="red"
            />
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Oy</th>
                  <th className="text-right px-4 py-3 font-medium">Shu oyda ketgan</th>
                  <th className="text-left px-4 py-3 font-medium w-1/3"></th>
                  <th className="text-right px-4 py-3 font-medium">Qolgan</th>
                  <th className="text-right px-4 py-3 font-medium">Retention</th>
                </tr>
              </thead>
              <tbody>
                {sf.months.map((m) => (
                  <tr
                    key={m.month}
                    className={`border-t border-slate-100 ${
                      m.month === sf.worst_month ? "bg-red-50/50" : ""
                    }`}
                  >
                    <td className="px-4 py-2.5 text-slate-700">{m.month}-oy</td>
                    <td className="px-4 py-2.5 text-right font-medium text-slate-800">
                      {m.lost || "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-400"
                          style={{ width: `${(m.lost / maxLost) * 100}%` }}
                        />
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-right text-slate-600">
                      {m.survived}/{m.eligible}
                    </td>
                    <td
                      className={`px-4 py-2.5 text-right font-medium ${
                        m.retention >= 70
                          ? "text-emerald-600"
                          : m.retention >= 40
                          ? "text-amber-600"
                          : "text-red-600"
                      }`}
                    >
                      {m.eligible ? `${m.retention}%` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Note>
            "Qolgan" ustuni: shu oyga yetgan o'quvchilar / natijasi ma'lum
            bo'lganlar. Yaqinda qo'shilgan o'quvchi keyingi oylarning hisobiga
            kirmaydi — u hali o'sha oyga yetmagan, shuning uchun ko'rsatkichni
            buzmaydi. Umr birinchi to'lovdan boshlab sanaladi.
          </Note>
        </>
      )}
    </div>
  );
}

// -------------------------------------------------- Sotuv menejerlari
const SALES_WINDOWS: { key: SalesWindow; label: string }[] = [
  { key: "month", label: "Oylik" },
  { key: "3m", label: "3 oy" },
  { key: "6m", label: "6 oy" },
  { key: "1y", label: "1 yil" },
  { key: "all", label: "Butun davr" },
];

function SalesTab() {
  const now = new Date();
  const [win, setWin] = useState<SalesWindow>("month");
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<SalesManagerReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const q =
      win === "month"
        ? `window=month&year=${year}&month=${month}`
        : `window=${win}`;
    api
      .get<SalesManagerReport>(`/reports/sales-managers?${q}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [win, year, month]);

  const years = [now.getFullYear() - 1, now.getFullYear()];
  const best = data && data.rows.length ? data.rows[0] : null;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-5">
        {SALES_WINDOWS.map((w) => (
          <button
            key={w.key}
            onClick={() => setWin(w.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
              win === w.key
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {w.label}
          </button>
        ))}

        {win === "month" && (
          <>
            <select
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm bg-white ml-2"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
            >
              {MONTHS.map((m, i) => (
                <option key={m} value={i + 1}>
                  {m}
                </option>
              ))}
            </select>
            <select
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm bg-white"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
            >
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </>
        )}

        {data && data.rows.length > 0 && (
          <button
            onClick={() =>
              exportToExcel("sotuv-menejerlari", "Sotuv",
                data.rows.map((r) => ({
                  Menejer: r.full_name,
                  Filial: r.branch ?? "",
                  Lidlar: r.leads,
                  "O'quvchiga aylandi": r.converted,
                  "Rad etdi": r.rejected,
                  Jarayonda: r.in_progress,
                  "Sotuv %": r.conversion,
                })))
            }
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600 ml-auto"
          >
            <Download size={15} /> Excel
          </button>
        )}
      </div>

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hali administrator (sotuv menejeri) roli berilgan xodim yo'q.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <Stat label="Davr" value={data.label} />
            <Stat label="Jami lid" value={String(data.totals.leads)} icon={Users} />
            <Stat
              label="O'quvchiga aylandi"
              value={String(data.totals.converted)}
              tone="green"
            />
            <Stat
              label="Umumiy sotuv"
              value={`${data.totals.conversion}%`}
              hint={best ? `eng yaxshi: ${best.full_name} (${best.conversion}%)` : undefined}
            />
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Menejer</th>
                  <th className="text-left px-4 py-3 font-medium">Filial</th>
                  <th className="text-right px-4 py-3 font-medium">Lidlar</th>
                  <th className="text-right px-4 py-3 font-medium">Sotildi</th>
                  <th className="text-right px-4 py-3 font-medium">Rad</th>
                  <th className="text-right px-4 py-3 font-medium">Jarayonda</th>
                  <th className="text-left px-4 py-3 font-medium w-48">Sotuv %</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r, i) => (
                  <tr
                    key={r.user_id}
                    className={`border-t border-slate-100 ${
                      !r.active ? "opacity-50" : ""
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {i === 0 && r.conversion > 0 && "🥇 "}
                      {r.full_name}
                      {!r.active && (
                        <span className="ml-2 text-[10px] uppercase bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                          faolsiz
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{r.branch || "—"}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{r.leads}</td>
                    <td className="px-4 py-3 text-right font-medium text-emerald-600">
                      {r.converted}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-500">
                      {r.rejected || "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-500">
                      {r.in_progress || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              r.conversion >= 50
                                ? "bg-emerald-500"
                                : r.conversion >= 25
                                ? "bg-amber-400"
                                : "bg-red-400"
                            }`}
                            style={{ width: `${Math.min(r.conversion, 100)}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-slate-800 w-12 text-right">
                          {r.conversion}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.unassigned > 0 && (
            <p className="text-xs text-amber-600 mt-3">
              {data.unassigned} ta lid hech kimga biriktirilmagan — ular
              hech kimning ko'rsatkichiga kirmayapti. Lidlar bo'limidan
              mas'ul xodimni belgilang.
            </p>
          )}

          <Note>
            Sotuv foizi = o'quvchiga aylangan lidlar / menejerga biriktirilgan
            lidlar. Davr lid yaratilgan sanaga qarab olinadi.
          </Note>
        </>
      )}
    </div>
  );
}

// -------------------------------------------------------- Adminlar KPI ----
function KpiRulesEditor({
  rules,
  setRules,
  canAdmin,
  onSave,
  saving,
  saved,
}: {
  rules: KpiRules;
  setRules: (r: KpiRules) => void;
  canAdmin: boolean;
  onSave: () => void;
  saving: boolean;
  saved: boolean;
}) {
  function upd<K extends "collection" | "new_clients">(
    key: K,
    i: number,
    patch: Partial<KpiRules[K][number]>
  ) {
    setRules({
      ...rules,
      [key]: rules[key].map((r, idx) => (idx === i ? { ...r, ...patch } : r)),
    });
  }

  const cell =
    "w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50";

  return (
    <div className="mt-8">
      <h3 className="font-medium text-slate-800 mb-1">Bonus qoidalari</h3>
      <p className="text-xs text-slate-500 mb-4 max-w-3xl">
        Bu jadvallar ish haqiga bevosita ta'sir qiladi, shuning uchun ularni
        faqat asoschi o'zgartira oladi. O'zgartirish darrov keyingi hisobga
        qo'llanadi.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">
            Eski to'lovlarni yig'ish
          </p>
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-3 py-2.5 font-medium">O'quvchi</th>
                  <th className="text-left px-3 py-2.5 font-medium">gacha</th>
                  <th className="text-left px-3 py-2.5 font-medium">Foiz</th>
                  <th className="text-left px-3 py-2.5 font-medium">Bonus</th>
                  <th className="px-2"></th>
                </tr>
              </thead>
              <tbody>
                {rules.collection.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        value={r.min_students}
                        onChange={(e) =>
                          upd("collection", i, {
                            min_students: Number(e.target.value),
                          })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        placeholder="cheksiz"
                        value={r.max_students ?? ""}
                        onChange={(e) =>
                          upd("collection", i, {
                            max_students:
                              e.target.value === "" ? null : Number(e.target.value),
                          })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        value={r.min_percent}
                        onChange={(e) =>
                          upd("collection", i, { min_percent: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className="w-32 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                        value={r.bonus}
                        onChange={(e) =>
                          upd("collection", i, { bonus: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-2 py-2 text-right">
                      {canAdmin && (
                        <button
                          onClick={() =>
                            setRules({
                              ...rules,
                              collection: rules.collection.filter((_, x) => x !== i),
                            })
                          }
                          className="text-slate-300 hover:text-red-500 text-xs"
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {canAdmin && (
            <button
              onClick={() =>
                setRules({
                  ...rules,
                  collection: [
                    ...rules.collection,
                    { min_students: 0, max_students: null, min_percent: 90, bonus: 0 },
                  ],
                })
              }
              className="text-sm text-slate-600 hover:text-brand-600 mt-2"
            >
              + Qator qo'shish
            </button>
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">
            Yangi mijozlar
          </p>
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-3 py-2.5 font-medium">Nechtadan</th>
                  <th className="text-left px-3 py-2.5 font-medium">Bonus</th>
                  <th className="px-2"></th>
                </tr>
              </thead>
              <tbody>
                {rules.new_clients.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className={cell}
                        value={r.min_clients}
                        onChange={(e) =>
                          upd("new_clients", i, { min_clients: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        disabled={!canAdmin}
                        className="w-32 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                        value={r.bonus}
                        onChange={(e) =>
                          upd("new_clients", i, { bonus: Number(e.target.value) })
                        }
                      />
                    </td>
                    <td className="px-2 py-2 text-right">
                      {canAdmin && (
                        <button
                          onClick={() =>
                            setRules({
                              ...rules,
                              new_clients: rules.new_clients.filter((_, x) => x !== i),
                            })
                          }
                          className="text-slate-300 hover:text-red-500 text-xs"
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {canAdmin && (
            <button
              onClick={() =>
                setRules({
                  ...rules,
                  new_clients: [...rules.new_clients, { min_clients: 10, bonus: 0 }],
                })
              }
              className="text-sm text-slate-600 hover:text-brand-600 mt-2"
            >
              + Pog'ona qo'shish
            </button>
          )}
        </div>
      </div>

      {canAdmin && (
        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={onSave}
            disabled={saving}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Qoidalarni saqlash"}
          </button>
          {saved && <span className="text-sm text-emerald-600">Saqlandi</span>}
        </div>
      )}
    </div>
  );
}

function KpiTab({ canAdmin }: { canAdmin: boolean }) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<AdminKpiResult | null>(null);
  const [rules, setRules] = useState<KpiRules | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<AdminKpiResult>(`/kpi/admins?year=${year}&month=${month}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [year, month]);

  useEffect(() => {
    api.get<KpiRules>("/kpi/rules").then(setRules);
  }, []);

  async function saveRules() {
    if (!rules) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.put<KpiRules>("/kpi/rules", {
        collection: rules.collection.map((r) => ({
          min_students: r.min_students,
          max_students: r.max_students ?? null,
          min_percent: r.min_percent,
          bonus: r.bonus,
        })),
        new_clients: rules.new_clients.map((r) => ({
          min_clients: r.min_clients,
          bonus: r.bonus,
        })),
      });
      setRules(updated);
      setSaved(true);
      const fresh = await api.get<AdminKpiResult>(
        `/kpi/admins?year=${year}&month=${month}`
      );
      setData(fresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const years = [now.getFullYear() - 1, now.getFullYear()];

  return (
    <div>
      <div className="flex items-center justify-between mb-5 gap-2">
        <div className="flex items-center gap-2">
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
        {data && data.rows.length > 0 && (
          <button
            onClick={() =>
              exportToExcel("adminlar-kpi", "KPI",
                data.rows.map((r) => ({
                  Admin: r.full_name,
                  Filial: r.branch ?? "",
                  "Fiks oylik": r.fix_salary,
                  "Faol o'quvchi": r.active_students,
                  "Tushishi kerak": r.expected,
                  Tushgan: r.collected,
                  "Foiz %": r.collection_percent,
                  "Yig'ish bonusi": r.collection_bonus,
                  "Yangi mijoz": r.new_clients,
                  "Yangi mijoz bonusi": r.new_client_bonus,
                  Jami: r.total,
                })))
            }
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
          >
            <Download size={15} /> Excel
          </button>
        )}
      </div>

      {loading || !data ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hali administrator (sotuv menejeri) roli berilgan xodim yo'q.
          Xodimlar bo'limidan qo'shing va fiks oyligini belgilang.
        </p>
      ) : (
        <>
          {data.rows.map((r) => (
            <div
              key={r.user_id}
              className="bg-white rounded-xl border border-slate-200 p-5 mb-4"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="font-semibold text-slate-900">{r.full_name}</p>
                  <p className="text-xs text-slate-500">
                    {r.branch || "Filial belgilanmagan"} · {r.active_students} faol
                    o'quvchi
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Jami ish haqi</p>
                  <p className="text-xl font-bold text-brand-700">
                    {formatSom(r.total)}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Fiks oylik</p>
                  <p className="font-semibold text-slate-800">
                    {formatSom(r.fix_salary)}
                  </p>
                  {!r.fix_salary && (
                    <p className="text-xs text-amber-600 mt-1">
                      Xodimlar bo'limidan belgilang
                    </p>
                  )}
                </div>

                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">
                    Eski to'lovlar · {r.collection_percent}%
                  </p>
                  <p
                    className={`font-semibold ${
                      r.collection_bonus > 0 ? "text-emerald-600" : "text-slate-400"
                    }`}
                  >
                    {r.collection_bonus > 0 ? `+${formatSom(r.collection_bonus)}` : "bonus yo'q"}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {short(r.collected)} / {short(r.expected)} tushdi
                  </p>
                </div>

                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">
                    Yangi mijoz · {r.new_clients} ta
                  </p>
                  <p
                    className={`font-semibold ${
                      r.new_client_bonus > 0 ? "text-emerald-600" : "text-slate-400"
                    }`}
                  >
                    {r.new_client_bonus > 0 ? `+${formatSom(r.new_client_bonus)}` : "bonus yo'q"}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {short(r.new_client_revenue)} tushum
                  </p>
                </div>
              </div>
            </div>
          ))}

          <Note>
            Bonuslar filial ko'rsatkichi bo'yicha hisoblanadi — bitta filialda
            ikkita admin bo'lsa, ikkalasi ham to'liq bonusni oladi. Foiz summa
            bo'yicha: shu oyda eski o'quvchilarga hisoblangan summadan qanchasi
            kassaga tushgani. Yangi mijoz — birinchi marta to'lov qilgan
            o'quvchi; uning to'lovi yig'ish foiziga kirmaydi.
          </Note>
        </>
      )}

      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

      {rules && (
        <KpiRulesEditor
          rules={rules}
          setRules={(r) => {
            setRules(r);
            setSaved(false);
          }}
          canAdmin={canAdmin}
          onSave={saveRules}
          saving={saving}
          saved={saved}
        />
      )}
    </div>
  );
}


// -------------------------------------------------------------------- Page
/* eslint-disable @typescript-eslint/no-explicit-any */
type AnyRow = any;

const DISC_STATE: Record<string, { label: string; cls: string }> = {
  good: { label: "Yaxshi", cls: "bg-emerald-100 text-emerald-700" },
  mid: { label: "O'rtacha", cls: "bg-amber-100 text-amber-700" },
  bad: { label: "Zaif", cls: "bg-red-100 text-red-700" },
};

function discBarColor(p: number | null): string {
  if (p == null) return "bg-slate-300";
  if (p >= 90) return "bg-emerald-500";
  if (p >= 70) return "bg-amber-500";
  return "bg-red-500";
}

function MonthPicker({ year, month, setYear, setMonth }: {
  year: number; month: number;
  setYear: (v: number) => void; setMonth: (v: number) => void;
}) {
  const now = new Date();
  return (
    <div className="flex items-center gap-2 mb-4">
      <select value={month} onChange={(e) => setMonth(Number(e.target.value))}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
        {MONTHS.map((m, i) => (
          <option key={i} value={i + 1}>{m}</option>
        ))}
      </select>
      <select value={year} onChange={(e) => setYear(Number(e.target.value))}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
        {[0, 1, 2].map((d) => (
          <option key={d} value={now.getFullYear() - d}>
            {now.getFullYear() - d}
          </option>
        ))}
      </select>
    </div>
  );
}

// ------------------------------------------------------ Ustoz intizomi
function DisciplineTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<AnyRow>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get<AnyRow>(`/reports/teacher-discipline?year=${year}&month=${month}`)
      .then(setD)
      .finally(() => setLoading(false));
  }, [year, month]);

  if (loading || !d)
    return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  const c = d.cards;

  return (
    <div>
      <MonthPicker year={year} month={month}
                   setYear={setYear} setMonth={setMonth} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <Stat label="O'z vaqtida belgilash"
              value={c.ontime_pct != null ? `${c.ontime_pct}%` : "—"}
              hint={`${c.ontime} / ${c.measured} darsdan`}
              tone={c.ontime_pct >= 90 ? "green"
                : c.ontime_pct >= 70 ? "slate" : "red"} />
        <Stat label="O'zi belgilagan"
              value={c.self_pct != null ? `${c.self_pct}%` : "—"}
              hint={`menejer belgilagan: ${c.manager_marked} ta`} />
        <Stat label="O'rtacha kechikish" value={c.avg_delay_label}
              hint="kechikkan belgilashlar bo'yicha" />
        <Stat label="Belgilanmagan darslar" value={String(c.unmarked)}
              tone={c.unmarked > 0 ? "red" : "green"}
              hint="o'tib ketgan, yo'qlamasiz" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">O'qituvchi</th>
              <th className="text-right px-3 py-2.5 font-medium">Belgilangan</th>
              <th className="text-left px-3 py-2.5 font-medium w-[30%]">O'z vaqtida</th>
              <th className="text-right px-3 py-2.5 font-medium">O'rtacha kechikish</th>
              <th className="text-right px-3 py-2.5 font-medium">Menejer belgilagan</th>
              <th className="text-right px-3 py-2.5 font-medium">Belgilanmagan</th>
              <th className="text-right px-4 py-2.5 font-medium">Holat</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.rows.map((r: AnyRow) => (
              <tr key={r.teacher_id}>
                <td className="px-4 py-2.5 font-medium text-slate-800">
                  {r.name}
                  {r.problems > 0 && (
                    <span className="ml-2 text-xs text-red-500">
                      {r.problems} muammoli
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {r.marked}
                  <span className="block text-xs text-slate-400">
                    o'zi: {r.self_marked}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${discBarColor(r.on_time_pct)}`}
                        style={{ width: `${r.on_time_pct ?? 0}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-slate-800 w-11 text-right">
                      {r.on_time_pct != null ? `${r.on_time_pct}%` : "—"}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    !r.avg_delay_min ? "bg-emerald-50 text-emerald-700"
                      : r.avg_delay_min <= 120 ? "bg-amber-50 text-amber-700"
                      : "bg-red-50 text-red-700"}`}>
                    {r.avg_delay_label}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right text-slate-600">
                  {r.manager_marked || "—"}
                </td>
                <td className="px-3 py-2.5 text-right">
                  {r.unmarked ? (
                    <span className="text-red-600 font-medium">{r.unmarked}</span>
                  ) : "—"}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {r.state && (
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      DISC_STATE[r.state]?.cls || ""}`}>
                      {DISC_STATE[r.state]?.label}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Bu oyda ma'lumot yo'q.
          </p>
        )}
      </div>
      <Note>{d.hint}</Note>
    </div>
  );
}

// -------------------------------------------------- Vazifalar hisoboti
function TaskReportTab() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<AnyRow>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get<AnyRow>(`/reports/task-performance?year=${year}&month=${month}`)
      .then(setD)
      .finally(() => setLoading(false));
  }, [year, month]);

  if (loading || !d)
    return <p className="text-slate-400 text-sm">Yuklanmoqda...</p>;
  const c = d.cards;

  return (
    <div>
      <MonthPicker year={year} month={month}
                   setYear={setYear} setMonth={setMonth} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <Stat label="Qo'yilgan vazifalar" value={String(c.total)} />
        <Stat label="Bajarilgan"
              value={c.done_pct != null ? `${c.done_pct}%` : "—"}
              hint={`${c.done} ta`}
              tone={c.done_pct >= 80 ? "green"
                : c.done_pct >= 50 ? "slate" : "red"} />
        <Stat label="O'rtacha bajarish tezligi" value={c.avg_speed_label} />
        <Stat label="Ochiq kechikkan" value={String(c.overdue_open)}
              tone={c.overdue_open > 0 ? "red" : "green"}
              hint="muddati o'tgan, bajarilmagan" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
              <th className="text-right px-3 py-2.5 font-medium">Vazifa</th>
              <th className="text-left px-3 py-2.5 font-medium w-[26%]">Bajarilgan</th>
              <th className="text-right px-3 py-2.5 font-medium">Tezlik</th>
              <th className="text-right px-3 py-2.5 font-medium">Kechikib bajardi</th>
              <th className="text-right px-4 py-2.5 font-medium">Ochiq kechikkan</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.rows.map((r: AnyRow) => (
              <tr key={r.user_id}>
                <td className="px-4 py-2.5">
                  <p className="font-medium text-slate-800">{r.name}</p>
                  <p className="text-xs text-slate-400">{r.role_label}</p>
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {r.total}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${discBarColor(r.done_pct)}`}
                        style={{ width: `${r.done_pct ?? 0}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-slate-800 w-16 text-right">
                      {r.done}/{r.total}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {r.speed_label}
                </td>
                <td className="px-3 py-2.5 text-right">
                  {r.done_late ? (
                    <span className="text-amber-600 font-medium">{r.done_late}</span>
                  ) : "—"}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {r.overdue_open ? (
                    <span className="text-red-600 font-medium">{r.overdue_open}</span>
                  ) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Bu oyda vazifa qo'yilmagan.
          </p>
        )}
      </div>
      <Note>{d.hint}</Note>
    </div>
  );
}

export default function Reports() {
  const { user } = useAuth();
  // Oylik bo'limini moliyachidan tashqari HR, o'quv rahbari va bosh
  // examiner/support ham ko'radi (PAYROLL_VIEW) — ular uchun sahifada
  // FAQAT "Oyliklar" tabi ochiladi, qolgan hisobotlar avvalgidek
  // yopiq. Shunday qilib ko'chirishda hech kimning huquqi
  // o'zgarmadi.
  const finance = can(user?.role, FINANCE_ACCESS);
  const payrollOnly = !finance && can(user?.role, PAYROLL_VIEW);
  const tabs = finance ? TABS : TABS.filter((t) => t.key === "payroll");
  const [tab, setTab] = useState<Tab>(finance ? "payroll" : "payroll");

  if (!finance && !payrollOnly) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl">
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Hisobotlar</h1>
      <p className="text-sm text-slate-500 mb-5">
        Oyliklar, ustoz intizomi, sotuv voronkasi va adminlar KPI'si
      </p>

      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "payroll" && <PayrollTab />}
      {tab === "discipline" && <DisciplineTab />}
      {tab === "tasks" && <TaskReportTab />}
      {tab === "funnel" && <FunnelTab />}
      {tab === "sales" && <SalesTab />}
      {tab === "kpi" && <KpiTab canAdmin={user?.role === FOUNDER} />}
    </div>
  );
}

