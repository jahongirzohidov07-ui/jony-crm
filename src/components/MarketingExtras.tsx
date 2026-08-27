import { useEffect, useState } from "react";
import { DoorOpen, Send, Gift, X, Check, Info, Zap } from "lucide-react";
import {
  api, type RomiReport, type CapacityReport, type RfmReport,
  type NotifyList, type NotifyTemplates, type ReferralReport,
} from "../lib/api";
import { formatSom } from "../lib/format";

const TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  sky: "bg-sky-100 text-sky-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  orange: "bg-orange-100 text-orange-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

// ============================================================== ROMI
export function RomiTab() {
  const [d, setD] = useState<RomiReport | null>(null);
  const [months, setMonths] = useState(6);

  useEffect(() => {
    api.get<RomiReport>(`/analytics/romi?months=${months}`).then(setD);
  }, [months]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <div className="flex gap-1">
          {[3, 6, 12].map((m) => (
            <button
              key={m}
              onClick={() => setMonths(m)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                months === m
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {m} oy
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-400">{d.period}</span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Box label="Reklama xarajati" value={formatSom(d.total_spend)} />
        <Box label="Keltirgan tushum" value={formatSom(d.total_revenue)} />
        <Box
          label="Sof foyda"
          value={formatSom(d.total_profit)}
          tone={d.total_profit > 0 ? "good" : "bad"}
        />
        <Box
          label="Umumiy ROMI"
          value={d.romi !== null && d.romi !== undefined ? `${d.romi}%` : "—"}
          hint="100% dan yuqori — foydali"
          tone={(d.romi ?? 0) >= 100 ? "good" : "bad"}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Kanal</th>
              <th className="text-right w-20">Lid</th>
              <th className="text-right w-24">O'quvchi</th>
              <th className="text-right w-20">Konv.</th>
              <th className="text-right w-28">Xarajat</th>
              <th className="text-right w-24">Lid narxi</th>
              <th className="text-right w-28">Mijoz narxi</th>
              <th className="text-right w-28">Foyda</th>
              <th className="text-right w-28 pr-4">ROMI</th>
            </tr>
          </thead>
          <tbody>
            {d.rows.map((r) => (
              <tr key={r.key} className="border-t border-slate-100">
                <td className="px-4 py-2.5 text-slate-800">{r.label}</td>
                <td className="text-right text-slate-600">{r.leads}</td>
                <td className="text-right text-emerald-600 font-medium">
                  {r.converted}
                </td>
                <td className="text-right text-slate-500">{r.conversion}%</td>
                <td className="text-right text-slate-600">
                  {r.spend ? formatSom(r.spend) : "—"}
                </td>
                <td className="text-right text-slate-500">
                  {r.cpl ? formatSom(r.cpl) : "—"}
                </td>
                <td className="text-right text-slate-500">
                  {r.cac ? formatSom(r.cac) : "—"}
                </td>
                <td
                  className={`text-right ${
                    r.profit > 0 ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {formatSom(r.profit)}
                </td>
                <td className="text-right pr-4">
                  {r.romi !== null && r.romi !== undefined ? (
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        TONE[r.tone] || TONE.slate
                      }`}
                    >
                      {r.romi}%
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">
                      xarajat yo'q
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>
    </div>
  );
}

// =================================================== Xonalar bandligi
export function CapacityTab() {
  const [d, setD] = useState<CapacityReport | null>(null);

  useEffect(() => {
    api.get<CapacityReport>("/analytics/capacity").then(setD);
  }, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Box
          label="O'rin bandligi"
          value={`${d.seat_usage}%`}
          hint={`${d.active_students} / ${d.total_capacity} o'rin`}
          tone={d.seat_usage >= 70 ? "good" : "bad"}
        />
        <Box
          label="Vaqt bandligi"
          value={`${d.time_usage}%`}
          hint="xonalar necha foiz vaqt ishlaydi"
          tone={d.time_usage >= 40 ? "good" : "bad"}
        />
        <Box label="Bo'sh o'rinlar" value={String(d.free_seats)} tone="bad" />
        <Box
          label="Yo'qotilayotgan pul"
          value={formatSom(d.lost_income)}
          hint="bo'sh o'rinlarning oylik qiymati"
          tone="bad"
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center gap-2 mb-3">
          <DoorOpen size={15} className="text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            Xonalar bo'yicha
          </p>
          <span className="text-xs text-slate-400">
            haftada {d.open_hours_week} soat ochiq
          </span>
        </div>
        <div className="space-y-3">
          {d.rooms.map((r) => (
            <div key={r.room_id}>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-sm text-slate-800">
                  {r.name}
                  <span className="text-xs text-slate-400 ml-1.5">
                    {r.groups} guruh · {r.students}/{r.capacity} o'rin
                  </span>
                </span>
                <span className="text-xs text-slate-600">
                  {r.hours_week} soat · {r.time_usage}%
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    r.time_usage >= 50
                      ? "bg-emerald-500"
                      : r.time_usage >= 25
                        ? "bg-amber-500"
                        : "bg-red-400"
                  }`}
                  style={{ width: `${Math.min(100, r.time_usage)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
          <Info size={11} className="mt-0.5 shrink-0" />
          {d.hint}
        </p>
      </div>
    </div>
  );
}

// =============================================================== RFM
export function RfmTab() {
  const [d, setD] = useState<RfmReport | null>(null);
  const [seg, setSeg] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  function load() {
    api.get<RfmReport>("/marketing/rfm").then(setD);
  }
  useEffect(load, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const rows = seg ? d.rows.filter((r) => r.segment === seg) : d.rows;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-5">
        {d.segments.map((s) => (
          <button
            key={s.key}
            onClick={() => setSeg(seg === s.key ? "" : s.key)}
            className={`rounded-xl border p-4 text-left transition ${
              seg === s.key
                ? "border-brand-400 ring-2 ring-brand-200"
                : "border-slate-200 hover:border-brand-300"
            } bg-white`}
          >
            <span
              className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium mb-1.5 ${
                TONE[s.tone] || TONE.slate
              }`}
            >
              {s.label}
            </span>
            <p className="text-lg font-semibold text-slate-900">{s.count}</p>
            <p className="text-xs text-slate-400">{s.percent}%</p>
          </button>
        ))}
      </div>

      {seg && (
        <div className="bg-brand-50 border border-brand-200 rounded-xl p-4 mb-4">
          <div className="flex items-start gap-2">
            <Zap size={15} className="text-brand-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-brand-900">
                {d.segments.find((s) => s.key === seg)?.action}
              </p>
              <p className="text-xs text-brand-700 mt-0.5">
                {d.segments.find((s) => s.key === seg)?.hint}
              </p>
            </div>
            <button
              onClick={async () => {
                const body = prompt(
                  "Xabar matni ({ism} — o'quvchi ismi):",
                  "{ism}, siz uchun maxsus taklifimiz bor!"
                );
                if (!body) return;
                const r = await api.post<{ created: number }>(
                  "/notifications/custom",
                  { body, segment: seg, kind: "new_course" }
                );
                setMsg(`${r.created} ta xabar navbatga qo'yildi`);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-medium shrink-0"
            >
              <Send size={12} /> Xabar yuborish
            </button>
          </div>
          {msg && <p className="text-xs text-emerald-700 mt-2">{msg}</p>}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">O'quvchi</th>
              <th className="text-left">Guruh</th>
              <th className="text-center w-16">R</th>
              <th className="text-center w-16">F</th>
              <th className="text-center w-16">M</th>
              <th className="text-right w-28">Oxirgi to'lov</th>
              <th className="text-right w-32">Jami to'lagan</th>
              <th className="text-left w-40 pr-4">Segment</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 100).map((r) => (
              <tr key={r.student_id} className="border-t border-slate-100">
                <td className="px-4 py-2.5 text-slate-800">{r.full_name}</td>
                <td className="text-slate-500">{r.group || "—"}</td>
                {[r.r, r.f, r.m].map((v, i) => (
                  <td key={i} className="text-center">
                    <span
                      className={`inline-block w-5 h-5 rounded text-xs leading-5 font-medium ${
                        v === 3
                          ? "bg-emerald-100 text-emerald-700"
                          : v === 2
                            ? "bg-amber-100 text-amber-700"
                            : "bg-red-100 text-red-700"
                      }`}
                    >
                      {v}
                    </span>
                  </td>
                ))}
                <td className="text-right text-slate-500">
                  {r.days_since_payment} kun
                </td>
                <td className="text-right text-slate-700">
                  {formatSom(r.total_paid)}
                </td>
                <td className="pr-4">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      TONE[r.tone] || TONE.slate
                    }`}
                  >
                    {r.segment_label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>
    </div>
  );
}

// ==================================================== Xabarnomalar
export function NotifyTab() {
  const [d, setD] = useState<NotifyList | null>(null);
  const [tpl, setTpl] = useState<NotifyTemplates | null>(null);
  const [filter, setFilter] = useState("");
  const [msg, setMsg] = useState("");
  const [show, setShow] = useState<"queue" | "templates">("queue");

  function load() {
    api.get<NotifyList>("/notifications").then(setD);
    api.get<NotifyTemplates>("/notifications/templates").then(setTpl);
  }
  useEffect(load, []);

  if (!d || !tpl)
    return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const rows = filter ? d.rows.filter((r) => r.status === filter) : d.rows;

  return (
    <div>
      {!d.telegram_ready && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <p className="text-sm text-amber-900">
            Telegram bot tokeni ulanmagan — xabarlar navbatda turadi,
            avtomat yuborilmaydi.
          </p>
          <p className="text-xs text-amber-800 mt-1">
            Ulash uchun Vercel'da <code>TELEGRAM_BOT_TOKEN</code>{" "}
            o'zgaruvchisini qo'shish kerak. Hozircha xabarlarni bu yerdan
            ko'chirib qo'lda yuborish mumkin.
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 mb-4">
        {[
          { k: "queue", l: "Navbat" },
          { k: "templates", l: "Shablonlar" },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setShow(t.k as "queue" | "templates")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              show === t.k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {t.l}
          </button>
        ))}
        <div className="flex-1" />
        <button
          onClick={async () => {
            const r = await api.post<{ created: number }>(
              "/notifications/generate",
              {}
            );
            setMsg(
              r.created
                ? `${r.created} ta yangi xabar navbatga qo'yildi`
                : "Yangi xabar yo'q — hammasi allaqachon yaratilgan"
            );
            load();
          }}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Zap size={14} /> Xabarlarni yaratish
        </button>
      </div>

      {msg && (
        <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2 mb-3">
          {msg}
        </p>
      )}

      {show === "templates" ? (
        <div className="space-y-2">
          {tpl.rows.map((t) => (
            <div
              key={t.id}
              className="bg-white rounded-xl border border-slate-200 p-4"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <p className="text-sm font-medium text-slate-800">
                  {t.kind_label}
                </p>
                <span className="text-xs text-slate-400">
                  {t.channel === "telegram" ? "Telegram" : "SMS"}
                </span>
                {t.days_before > 0 && (
                  <span className="text-xs text-slate-400">
                    · {t.days_before} kun oldin
                  </span>
                )}
                <div className="flex-1" />
                <button
                  onClick={async () => {
                    await api.put(`/notifications/templates/${t.id}`, {
                      active: !t.active,
                    });
                    load();
                  }}
                  className={`px-2 py-1 rounded-md text-xs font-medium ${
                    t.active
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {t.active ? "Yoqilgan" : "O'chirilgan"}
                </button>
              </div>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">
                {t.body}
              </p>
            </div>
          ))}
          <p className="text-xs text-slate-400">
            O'rinbosarlar: {tpl.placeholders.join(", ")}
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-1.5 mb-3">
            <button
              onClick={() => setFilter("")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                !filter
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500"
              }`}
            >
              Hammasi
            </button>
            {d.statuses.map((s) => (
              <button
                key={s.key}
                onClick={() => setFilter(filter === s.key ? "" : s.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                  filter === s.key
                    ? "bg-brand-50 border-brand-400 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500"
                }`}
              >
                {s.label} <span className="text-slate-400">{s.count}</span>
              </button>
            ))}
          </div>

          {rows.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              Xabar yo'q. "Xabarlarni yaratish" tugmasini bosing.
            </p>
          ) : (
            <div className="space-y-1.5">
              {rows.map((n) => (
                <div
                  key={n.id}
                  className="bg-white rounded-lg border border-slate-200 px-4 py-2.5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm text-slate-800">
                          {n.student || n.phone || "—"}
                        </span>
                        <span className="text-xs text-slate-400">
                          {n.kind_label}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            TONE[n.tone] || TONE.slate
                          }`}
                        >
                          {n.status_label}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 mt-0.5">{n.body}</p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {n.status === "queued" && (
                        <>
                          <button
                            onClick={async () => {
                              await navigator.clipboard?.writeText(n.body);
                              await api.post(
                                `/notifications/${n.id}/status`,
                                { status: "sent" }
                              );
                              load();
                            }}
                            title="Matnni nusxalab, yuborilgan deb belgilash"
                            className="p-1.5 rounded-md text-slate-400 hover:text-emerald-600 hover:bg-emerald-50"
                          >
                            <Check size={14} />
                          </button>
                          <button
                            onClick={async () => {
                              await api.post(
                                `/notifications/${n.id}/status`,
                                { status: "cancelled" }
                              );
                              load();
                            }}
                            className="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50"
                          >
                            <X size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ============================== Do'st taklifi dasturi (2026-08-28)
// Jahongir: "referallar holati ko'rinib turishi kerak". Bu YANGI
// dastur — ilovadagi havola orqali. Pastdagi eski jadval esa
// QO'LDA yoziladigan "kim kimni olib keldi" (u ham qoladi:
// hech narsa o'chirilmaydi).
type RefProgram = {
  period: string;
  rows: {
    student_id: number; name: string; code: string; branch: string | null;
    leads: number; students: number; paid_this_period: number;
    level: number; percent: number; earned: number;
  }[];
  totals: {
    inviters: number; leads: number; students: number; paid: number;
    earned_sum: number; discount_sum: number; discount_count: number;
  };
  ladder: { n: number; percent: number }[];
};

function ReferralProgramPanel() {
  const [d, setD] = useState<RefProgram | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get<RefProgram>("/referral-program")
      .then(setD)
      .catch((e) => setErr(e?.message || ""));
  }, []);

  if (err) return null;
  if (!d) return <p className="text-sm text-slate-400 py-4">Yuklanmoqda...</p>;

  const money = (n: number) =>
    (Math.round(n) || 0).toLocaleString("ru-RU").replace(/,/g, " ");

  return (
    <div className="mb-7">
      <h3 className="text-sm font-bold text-slate-800 mb-1">
        Do'st taklifi dasturi (ilova havolasi)
      </h3>
      <p className="text-xs text-slate-500 mb-3">
        {d.period} · o'quvchi havolasi orqali kelganlar. Chegirma:
        {d.ladder.map((l) => ` ${l.n}-do'st ${l.percent}%`).join(" ·")}.
        Foizlar qo'shilmaydi.
      </p>
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <Box label="Havola tarqatganlar" value={String(d.totals.inviters)}
             tone="brand" />
        <Box label="Kelgan lidlar" value={String(d.totals.leads)} />
        <Box label="O'quvchi bo'ldi" value={String(d.totals.students)} />
        <Box label="Shu oyda to'ladi" value={String(d.totals.paid)}
             hint="chegirma shundan hisoblanadi" />
        <Box label="Ishlab topilgan chegirma"
             value={money(d.totals.earned_sum) + " so'm"}
             hint={`${d.totals.discount_count} ta qatorda ` +
                   `${money(d.totals.discount_sum)} so'm shu oyga`} />
      </div>
      {d.rows.length === 0 ? (
        <p className="text-xs text-slate-400 py-3">
          Hali hech kim havolasidan odam olib kelmagan.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="text-left px-3 py-2">O'quvchi</th>
                <th className="text-left px-3 py-2">Filial</th>
                <th className="text-right px-3 py-2">Lid</th>
                <th className="text-right px-3 py-2">O'quvchi</th>
                <th className="text-right px-3 py-2">Shu oyda to'ladi</th>
                <th className="text-right px-3 py-2">Daraja</th>
                <th className="text-right px-3 py-2">Chegirma</th>
              </tr>
            </thead>
            <tbody>
              {d.rows.map((r) => (
                <tr key={r.student_id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-medium text-slate-800">
                    {r.name}
                    <span className="text-slate-400 ml-1.5">{r.code}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-500">{r.branch || "-"}</td>
                  <td className="px-3 py-2 text-right">{r.leads}</td>
                  <td className="px-3 py-2 text-right">{r.students}</td>
                  <td className="px-3 py-2 text-right font-semibold">
                    {r.paid_this_period}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {r.percent ? `${r.percent}%` : "-"}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {r.earned ? money(r.earned) + " so'm" : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ========================================================== Referral
export function ReferralTab() {
  const [d, setD] = useState<ReferralReport | null>(null);

  useEffect(() => {
    api.get<ReferralReport>("/referrals").then(setD);
  }, []);

  return (
    <div>
      <ReferralProgramPanel />
      <h3 className="text-sm font-bold text-slate-800 mb-3">
        Qo'lda kiritilgan referrallar
      </h3>
      {!d ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : (
      <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Box label="Olib kelganlar" value={String(d.inviters)} tone="brand" />
        <Box
          label="Olib kelinganlar"
          value={String(d.invited)}
          hint={`${d.active} chegirma faol, ${d.pending} kutmoqda`}
        />
        <Box
          label="Keltirgan tushum"
          value={formatSom(d.revenue)}
          tone="good"
        />
        <Box
          label="Sof natija"
          value={formatSom(d.net)}
          hint={`chegirma ${formatSom(d.discount)}`}
          tone={d.net > 0 ? "good" : "bad"}
        />
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali hech kim do'stini olib kelmagan.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Kim olib keldi</th>
                <th className="text-right w-24">Nechta</th>
                <th className="text-left">Kimlarni</th>
                <th className="text-right w-32">Keltirgan pul</th>
                <th className="text-right w-32">Chegirma</th>
                <th className="text-right w-32 pr-4">Sof</th>
              </tr>
            </thead>
            <tbody>
              {d.rows.map((r) => (
                <tr key={r.student_id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">
                    {r.full_name}
                  </td>
                  <td className="text-right text-slate-600">
                    {r.invited}
                    {r.active !== r.invited && (
                      <span className="text-slate-400"> ({r.active} faol)</span>
                    )}
                  </td>
                  <td className="text-slate-500 text-xs">
                    {r.friends.map((f) => f.name).join(", ")}
                  </td>
                  <td className="text-right text-emerald-600">
                    {formatSom(r.revenue_brought)}
                  </td>
                  <td className="text-right text-slate-500">
                    {formatSom(r.discount_given)}
                  </td>
                  <td className="text-right pr-4 font-medium text-slate-800">
                    {formatSom(r.net)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Gift size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>
      </div>
      )}
    </div>
  );
}

function Box({
  label,
  value,
  hint,
  tone = "plain",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "plain" | "brand" | "good" | "bad";
}) {
  const cls = {
    plain: "bg-white border-slate-200 text-slate-900",
    brand: "bg-brand-50 border-brand-200 text-brand-800",
    good: "bg-emerald-50 border-emerald-200 text-emerald-800",
    bad: "bg-red-50 border-red-200 text-red-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}
