import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { CheckCircle2, Clock, CircleDashed, Wallet, X } from "lucide-react";
import { api } from "../lib/api";
import { formatSom } from "../lib/format";
import { PAYMENT_METHODS, methodLabel } from "../lib/payments";

/**
 * OY YOPILISHI VA P&L (2026-10-02, Jahongir).
 *
 * Pul oqimi -> "Oy kesimida": to'lov QAYSI OY UCHUN bo'lsa o'sha oyga
 * (sentabr qarzi oktabrda to'lansa ham — sentabr daromadi), oy
 * xarajatlari va har xodimning hisoblangan oyligi berildi/berilmadi
 * bilan. "Berish" — shu oy uchun yoziladi va qator yopiladi.
 * P&L — o'quv yili oyma-oy foyda yoki zarar.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const MONTHS = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul",
  "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"];

function prevMonth() {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - 1);
  return { y: d.getFullYear(), m: d.getMonth() + 1 };
}

function short(n: number): string {
  const a = Math.abs(n);
  if (a >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (a >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

const STATUS: Record<string, { label: string; cls: string; Icon: Any }> = {
  paid: { label: "Berildi", cls: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    Icon: CheckCircle2 },
  partial: { label: "Qisman", cls: "bg-amber-50 text-amber-700 ring-amber-200",
    Icon: Clock },
  unpaid: { label: "Berilmadi", cls: "bg-red-50 text-red-700 ring-red-200",
    Icon: CircleDashed },
};

function Tile({ label, value, tone, hint }: {
  label: string; value: string; tone?: "green" | "red" | "slate"; hint?: string;
}) {
  const c = tone === "green" ? "text-emerald-700"
    : tone === "red" ? "text-red-700" : "text-slate-900";
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 min-w-0">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-xl font-bold tabular-nums mt-1 truncate ${c}`}>{value}</p>
      {hint && <p className="text-[11px] text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

// ------------------------------------------------------------ Oy kesimida
export function MonthCloseView() {
  const p = prevMonth();
  const [y, setY] = useState(p.y);
  const [m, setM] = useState(p.m);
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [pay, setPay] = useState<Any>(null);
  const [filter, setFilter] = useState<"all" | "open">("all");

  const load = () => {
    setErr("");
    api.get<Any>(`/month-close?year=${y}&month=${m}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(() => { setD(null); load(); }, [y, m]);

  const now = new Date();
  const years = [now.getFullYear() - 1, now.getFullYear()];
  const rows: Any[] = d ? d.salary_rows.filter((r: Any) =>
    filter === "all" || r.status !== "paid") : [];

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <select value={m} onChange={(e) => setM(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white">
          {MONTHS.map((x, i) => <option key={x} value={i + 1}>{x}</option>)}
        </select>
        <select value={y} onChange={(e) => setY(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white">
          {years.map((x) => <option key={x} value={x}>{x}</option>)}
        </select>
        {d && !d.closed && (
          <span className="text-xs rounded-full bg-amber-50 text-amber-700 ring-1 ring-amber-200 px-2.5 py-1">
            Oy hali tugamagan — raqamlar o'zgarib turadi
          </span>
        )}
      </div>

      {err && <p className="text-sm text-red-600 mb-3">{err}</p>}
      {!d ? (
        !err && <p className="text-sm text-slate-400">Yuklanmoqda...</p>
      ) : (
        <>
          {!d.limited && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                <Tile label={`${d.title} uchun daromad`}
                  value={formatSom(d.income.total)} tone="green"
                  hint={`${d.income.students} o'quvchi · qarz ${short(d.income.pending)}`} />
                <Tile label="Xarajatlar" value={formatSom(d.expenses.total)} />
                <Tile label="Oyliklar (hisoblangan)"
                  value={formatSom(d.salaries.total)}
                  hint={d.salaries.left > 0
                    ? `berilmagan ${short(d.salaries.left)}` : "hammasi berilgan"} />
                <Tile label={d.profit >= 0 ? "Foyda" : "Zarar"}
                  value={formatSom(d.profit)}
                  tone={d.profit >= 0 ? "green" : "red"}
                  hint={`marja ${d.margin}%`} />
              </div>

              <div className="grid lg:grid-cols-2 gap-3 mb-4">
                <div className="bg-white rounded-xl border border-slate-200 p-4">
                  <p className="text-sm font-semibold text-slate-800 mb-2">
                    Daromad — {d.title} uchun to'langan
                  </p>
                  <ul className="text-sm space-y-1">
                    {Object.entries(d.income.by_method as Record<string, number>)
                      .sort((a, b) => b[1] - a[1])
                      .map(([k, v]) => (
                        <li key={k} className="flex justify-between">
                          <span className="text-slate-500">{methodLabel(k)}</span>
                          <span className="tabular-nums">{formatSom(v)}</span>
                        </li>
                      ))}
                    {d.income.refunds < 0 && (
                      <li className="flex justify-between">
                        <span className="text-slate-500">Qaytarilgan</span>
                        <span className="tabular-nums text-red-600">
                          {formatSom(d.income.refunds)}
                        </span>
                      </li>
                    )}
                    <li className="flex justify-between border-t border-slate-100 pt-1 mt-1">
                      <span className="text-slate-500">Hali to'lanmagan (qarz)</span>
                      <span className="tabular-nums text-amber-700">
                        {formatSom(d.income.pending)}
                      </span>
                    </li>
                  </ul>
                  <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                    To'lov qachon kelganidan qat'i nazar, qaysi oy uchun
                    bo'lsa o'sha oyga yoziladi (eng eski qarzdan yopiladi).
                    Oy hali yechilmagan oldindan to'lovlar ({short(d.advance || 0)})
                    hech bir oyga qo'shilmaydi.
                  </p>
                </div>
                <div className="bg-white rounded-xl border border-slate-200 p-4">
                  <p className="text-sm font-semibold text-slate-800 mb-2">
                    Xarajatlar ({d.title})
                  </p>
                  {d.expenses.lines.length === 0 ? (
                    <p className="text-sm text-slate-400">Xarajat kiritilmagan</p>
                  ) : (
                    <ul className="text-sm space-y-1 max-h-56 overflow-auto">
                      {d.expenses.lines.map((l: Any) => (
                        <li key={l.category} className="flex justify-between gap-2">
                          <span className="text-slate-500 truncate">{l.label}</span>
                          <span className="tabular-nums">{formatSom(l.amount)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  <p className="text-[11px] text-slate-400 mt-2">
                    Xodimlarga berilgan oyliklar bu yerda emas — pastdagi
                    oyliklar ro'yxatida hisoblangan summasi bilan turadi.
                  </p>
                </div>
              </div>
            </>
          )}

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-slate-100">
              <Wallet size={16} className="text-slate-400" />
              <p className="text-sm font-semibold text-slate-800">
                {d.title} oyliklari
              </p>
              <span className="text-xs text-slate-500">
                {d.salaries.count} xodim · berilmagan {d.salaries.unpaid_count} ta
                · qoldi {formatSom(d.salaries.left)}
              </span>
              <div className="flex-1" />
              <div className="flex gap-1 bg-slate-100 rounded-lg p-0.5">
                {([["all", "Hammasi"], ["open", "Berilmaganlar"]] as const).map(([k, l]) => (
                  <button key={k} onClick={() => setFilter(k)}
                    className={`px-2.5 py-1 rounded-md text-xs ${filter === k
                      ? "bg-white shadow-sm text-slate-900" : "text-slate-500"}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs text-slate-500">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium">Xodim</th>
                    <th className="text-right px-3 py-2 font-medium">Hisoblangan</th>
                    <th className="text-right px-3 py-2 font-medium">Berilgan</th>
                    <th className="text-right px-3 py-2 font-medium">Qoldi</th>
                    <th className="text-left px-3 py-2 font-medium">Holat</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 && (
                    <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                      {filter === "open" ? "Hammasiga berilgan" : "Bu oyda oylik yo'q"}
                    </td></tr>
                  )}
                  {rows.map((r: Any) => {
                    const st = STATUS[r.status];
                    return (
                      <tr key={r.key} className="border-t border-slate-100">
                        <td className="px-4 py-2.5 min-w-[180px]">
                          <p className="font-medium text-slate-800">{r.name}</p>
                          <p className="text-[11px] text-slate-400">
                            {[r.roles, r.branch].filter(Boolean).join(" · ")}
                            {r.parts.length > 1 && (
                              <> — {r.parts.map((x: Any) =>
                                `${x.label} ${short(x.amount)}`).join(" + ")}</>
                            )}
                          </p>
                        </td>
                        <td className="px-3 py-2.5 text-right tabular-nums">{formatSom(r.accrued)}</td>
                        <td className="px-3 py-2.5 text-right tabular-nums text-slate-600">{formatSom(r.paid)}</td>
                        <td className={`px-3 py-2.5 text-right tabular-nums ${r.left > 0 ? "text-red-700 font-medium" : "text-slate-400"}`}>
                          {formatSom(r.left)}
                        </td>
                        <td className="px-3 py-2.5">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ring-1 ${st.cls}`}>
                            <st.Icon size={12} /> {st.label}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          {d.can_pay && r.left > 0 && (
                            <button onClick={() => setPay(r)}
                              className="rounded-lg bg-brand-600 text-white px-3 py-1 text-xs font-medium hover:bg-brand-700">
                              Berish
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
            Oylik bu yerdan yoki Xarajatlar → Oylik orqali "{d.title} uchun"
            deb berilsa, qator yopiladi. Oy ichida berilgan avans ham shu
            oydan ayiriladi.
          </p>
        </>
      )}

      {pay && d && (
        <PayModal row={pay} period={d.period} title={d.title}
          onClose={(ok) => { setPay(null); if (ok) load(); }} />
      )}
    </div>
  );
}

function PayModal({ row, period, title, onClose }: {
  row: Any; period: string; title: string; onClose: (ok: boolean) => void;
}) {
  const [amount, setAmount] = useState(String(Math.round(row.left)));
  const [method, setMethod] = useState("cash");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    const v = Number(amount);
    if (!v || v <= 0) { setErr("To'g'ri summa kiriting"); return; }
    setBusy(true); setErr("");
    try {
      await api.post("/month-close/pay", {
        period, key: row.key, amount: v, method, date, note,
      });
      onClose(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-900">Oylik berish</h2>
          <button onClick={() => onClose(false)} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-700">{row.name}</p>
        <p className="text-xs text-slate-500 mb-3">
          <b>{title}</b> uchun · hisoblangan {formatSom(row.accrued)},
          berilgan {formatSom(row.paid)}
        </p>
        <div className="space-y-3">
          <label className="block text-xs text-slate-500">Summa
            <input value={amount} inputMode="numeric"
              onChange={(e) => setAmount(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-right" />
          </label>
          <div className="grid grid-cols-2 gap-2">
            <label className="block text-xs text-slate-500">Usul
              <select value={method} onChange={(e) => setMethod(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-2 text-sm bg-white">
                {PAYMENT_METHODS.map((pm) => (
                  <option key={pm.key} value={pm.key}>{pm.label}</option>
                ))}
              </select>
            </label>
            <label className="block text-xs text-slate-500">Sana
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-2 text-sm" />
            </label>
          </div>
          <label className="block text-xs text-slate-500">Izoh
            <input value={note} onChange={(e) => setNote(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </label>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <div className="flex justify-end gap-2">
            <button onClick={() => onClose(false)}
              className="px-4 py-2 text-sm text-slate-600">Bekor</button>
            <button onClick={save} disabled={busy}
              className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40">
              Berish
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------- P&L
export function PnlBoard() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Any>("/pnl").then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  if (err) return <p className="text-sm text-red-600">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  const t = d.totals;
  const chart = d.rows.map((r: Any) => ({
    name: r.title.split(" ")[0], profit: r.profit, title: r.title,
  }));

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Tile label={`Daromad · ${d.year_label}`} value={formatSom(t.income)} tone="green" />
        <Tile label="Xarajat + oyliklar" value={formatSom(t.outflow)}
          hint={`oyliklar ${short(t.salaries)}`} />
        <Tile label={t.profit >= 0 ? "Foyda" : "Zarar"} value={formatSom(t.profit)}
          tone={t.profit >= 0 ? "green" : "red"} />
        <Tile label="Marja" value={`${t.margin}%`} hint="foyda / daromad"
          tone={t.margin >= 0 ? "green" : "red"} />
      </div>

      {d.rows.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <p className="text-sm font-semibold text-slate-800 mb-2">
            Oyma-oy foyda / zarar
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }}
                  axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => short(v)} width={64}
                  domain={[(lo: number) => Math.min(0, lo), (hi: number) => Math.max(0, hi)]}
                  tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <ReferenceLine y={0} stroke="#94a3b8" />
                <Tooltip formatter={(v: number) => [formatSom(v), "Natija"]}
                  labelFormatter={(_l, p: Any) => p?.[0]?.payload?.title || ""} />
                <Bar dataKey="profit" radius={[4, 4, 0, 0]} animationDuration={700}>
                  {chart.map((c: Any) => (
                    <Cell key={c.title} fill={c.profit >= 0 ? "#1baf7a" : "#e34948"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Oy</th>
              <th className="text-right px-3 py-2 font-medium">Daromad</th>
              <th className="text-right px-3 py-2 font-medium">Xarajatlar</th>
              <th className="text-right px-3 py-2 font-medium">Oyliklar</th>
              <th className="text-right px-3 py-2 font-medium">Natija</th>
              <th className="text-right px-3 py-2 font-medium">Marja</th>
              <th className="text-right px-4 py-2 font-medium">Qarz</th>
            </tr>
          </thead>
          <tbody>
            {d.rows.map((r: Any) => (
              <tr key={r.period} className="border-t border-slate-100">
                <td className="px-4 py-2.5">
                  {r.title}
                  {!r.closed && (
                    <span className="ml-1.5 text-[10px] text-amber-700 bg-amber-50 rounded px-1 py-0.5">
                      davom etmoqda
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-emerald-700">{formatSom(r.income)}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">{formatSom(r.expenses)}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatSom(r.salaries)}
                  {r.salaries_left > 0 && (
                    <p className="text-[10px] text-red-600">berilmagan {short(r.salaries_left)}</p>
                  )}
                </td>
                <td className={`px-3 py-2.5 text-right tabular-nums font-semibold ${r.profit >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                  {formatSom(r.profit)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-slate-500">{r.margin}%</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-amber-700">{formatSom(r.pending)}</td>
              </tr>
            ))}
            <tr className="border-t-2 border-slate-200 bg-slate-50 font-semibold">
              <td className="px-4 py-2.5">Jami</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatSom(t.income)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatSom(t.expenses)}</td>
              <td className="px-3 py-2.5 text-right tabular-nums">{formatSom(t.salaries)}</td>
              <td className={`px-3 py-2.5 text-right tabular-nums ${t.profit >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                {formatSom(t.profit)}
              </td>
              <td className="px-3 py-2.5 text-right tabular-nums">{t.margin}%</td>
              <td className="px-4 py-2.5 text-right tabular-nums">{formatSom(t.pending)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
        Daromad — shu oy UCHUN to'langan pul (keyin to'langan qarz ham o'z
        oyiga yoziladi). Oyliklar — hisoblangan summa (ustoz yoqlamadan,
        examiner va support ishidan, xodimlar fiks + KPI), berilgan-berilmaganidan
        qat'i nazar. Qarz — shu oy uchun hali to'lanmagan pul.
      </p>
    </div>
  );
}
