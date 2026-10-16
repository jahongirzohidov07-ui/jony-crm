/**
 * TERMINAL ↔ NAQD O'TKAZMASI (2026-10-16).
 *
 * Jahongir: terminal (bank) hisobidagi pulni naqdga yechganda bank 1%
 * komissiya oladi — naqd kassaga sof summa o'zi tushsin; naqdni
 * terminalga topshirish — to'liq avtomat. Faqat shu ikki amal bor.
 *
 * Joyi: Moliya → Pul oqimi (kassa daftari tepasida). Ikki tugma:
 *   "Terminaldan naqd yechish" — summa, sana, izoh; komissiya va naqdga
 *     tushadigan sof summa yozish paytida ko'rinib turadi;
 *   "Naqdni terminalga topshirish" — summa, sana, izoh.
 * Pastda shu oy tarixi; tahrirlash/o'chirish faqat rahbariyat/moliyada
 * (server can_manage belgisi). Qoldiqdan oshiq summada server aniq
 * ogohlantirish qaytaradi; rahbariyat "Baribir saqlash" bilan tasdiqlaydi.
 */
import { useEffect, useState } from "react";
import {
  ArrowDownToLine, ArrowUpFromLine, ArrowLeftRight, Pencil, Trash2, X, Check,
} from "lucide-react";
import {
  api, ApiError, getGlobalBranch,
  type Branch, type BankTransfer, type BankTransferKind,
  type BankTransferList, type BankTransferBalance,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { formatDate, formatSom } from "../lib/format";
import { MoneyInput } from "./MoneyInput";

function todayIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
}

/** Backend bilan bir xil: komissiya 2 xonagacha yaxlitlanadi. */
function calc(kind: BankTransferKind, amount: number, rate: number) {
  if (kind === "withdraw") {
    const fee = Math.round(amount * rate) / 100;
    return { fee, net: Math.round((amount - fee) * 100) / 100 };
  }
  return { fee: 0, net: amount };
}

function pct(rate: number): string {
  return `${Number(rate.toFixed(4))}%`;
}

export function BankTransferPanel({
  year,
  month,
  reloadKey = 0,
  limited = false,
  onChanged,
}: {
  year: number;
  month: number;
  reloadKey?: number;
  /** Cheklangan filial administratori — faqat bugungi (server ham shunday) */
  limited?: boolean;
  onChanged?: () => void;
}) {
  const { user } = useAuth();
  const [data, setData] = useState<BankTransferList | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState<
    { kind: BankTransferKind; initial: BankTransfer | null } | null
  >(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [rateEdit, setRateEdit] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null);
    api
      .get<BankTransferList>(`/bank-transfers?year=${year}&month=${month}`)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [year, month, reloadKey, tick]);

  const globalBranch = Number(getGlobalBranch()) || null;
  const needBranch = !globalBranch && !user?.branch_id;
  useEffect(() => {
    if (!needBranch) return;
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, [needBranch]);

  function changed() {
    // Ota sahifa reloadKey ni oshirsa, ro'yxat ham o'sha bilan yangilanadi
    if (onChanged) onChanged();
    else setTick((t) => t + 1);
  }

  async function remove(t: BankTransfer) {
    const extra = t.fee > 0 ? " Bank komissiyasi xarajati ham o'chadi." : "";
    if (!confirm(`${t.title} — o'chirilsinmi?${extra}`)) return;
    try {
      await api.delete(`/bank-transfers/${t.id}`);
      changed();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function saveRate() {
    const v = Number(String(rateEdit ?? "").replace(",", "."));
    if (!Number.isFinite(v) || v < 0) {
      setErr("Foiz noto'g'ri");
      return;
    }
    try {
      await api.put("/bank-transfers/settings", { fee_percent: v });
      setRateEdit(null);
      changed();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  const rate = data?.fee_percent ?? 1;
  const rows = data?.rows ?? [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 mb-5">
      <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-slate-100">
        <ArrowLeftRight size={16} className="text-sky-600" />
        <h3 className="font-semibold text-slate-900">Terminal ↔ naqd</h3>
        <span className="text-xs text-slate-400 flex items-center gap-1">
          bank komissiyasi{" "}
          {rateEdit === null ? (
            <>
              <b className="text-slate-600">{pct(rate)}</b>
              {data?.can_edit_rate && (
                <button
                  onClick={() => setRateEdit(String(rate))}
                  className="text-slate-400 hover:text-brand-600"
                  title="Foizni o'zgartirish — faqat keyingi yechishlarga qo'llanadi"
                >
                  <Pencil size={12} />
                </button>
              )}
            </>
          ) : (
            <span className="inline-flex items-center gap-1">
              <input
                value={rateEdit}
                onChange={(e) => setRateEdit(e.target.value)}
                inputMode="decimal"
                className="w-14 rounded border border-slate-300 px-1.5 py-0.5 text-xs"
                autoFocus
              />
              %
              <button onClick={saveRate} className="text-emerald-600" title="Saqlash">
                <Check size={14} />
              </button>
              <button onClick={() => setRateEdit(null)} className="text-slate-400" title="Bekor">
                <X size={14} />
              </button>
            </span>
          )}
        </span>
        <div className="flex-1" />
        <button
          onClick={() => setForm({ kind: "withdraw", initial: null })}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-sm font-medium"
        >
          <ArrowDownToLine size={14} /> Terminaldan naqd yechish
        </button>
        <button
          onClick={() => setForm({ kind: "deposit", initial: null })}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-sky-300 text-sky-700 hover:bg-sky-50 text-sm font-medium"
        >
          <ArrowUpFromLine size={14} /> Naqdni terminalga topshirish
        </button>
      </div>

      {rateEdit !== null && (
        <p className="px-4 pt-2 text-xs text-amber-700">
          Yangi foiz faqat keyingi yechishlarga qo'llanadi — avvalgi
          o'tkazmalar o'z foizi bilan qoladi.
        </p>
      )}
      {err && <p className="px-4 pt-3 text-sm text-red-600">{err}</p>}

      {data && (data.totals.withdraw > 0 || data.totals.deposit > 0) && (
        <div className="flex flex-wrap gap-x-6 gap-y-1 px-4 pt-3 text-xs text-slate-600">
          <span>
            Terminaldan yechildi: <b className="text-slate-800">{formatSom(data.totals.withdraw)}</b>
            {data.totals.withdraw_fee > 0 && (
              <> (komissiya {formatSom(data.totals.withdraw_fee)}) → naqdga{" "}
                <b className="text-emerald-700">+{formatSom(data.totals.withdraw_net)}</b></>
            )}
          </span>
          <span>
            Naqd → terminalga: <b className="text-slate-800">{formatSom(data.totals.deposit)}</b>
          </span>
        </div>
      )}

      {rows.length === 0 ? (
        <p className="px-4 py-4 text-sm text-slate-400">
          {limited ? "Bugun o'tkazma yo'q." : "Bu oyda o'tkazma yo'q."}
        </p>
      ) : (
        <div className="overflow-x-auto mt-2">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs">
              <tr>
                <th className="text-left px-4 py-2 font-medium w-28">Sana</th>
                <th className="text-left px-3 py-2 font-medium">O'tkazma</th>
                <th className="text-left px-3 py-2 font-medium">Izoh</th>
                <th className="text-left px-3 py-2 font-medium">Filial</th>
                <th className="text-left px-3 py-2 font-medium">Kiritdi</th>
                <th className="px-3 py-2 w-16"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((t) => (
                <tr key={t.id} className="hover:bg-sky-50/40">
                  <td className="px-4 py-2 text-slate-600">{formatDate(t.date)}</td>
                  <td className="px-3 py-2 text-slate-800">
                    {t.title}
                    {t.forced && (
                      <span
                        className="ml-1.5 text-[10px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded"
                        title="Qoldiqdan oshiq summa — rahbariyat tasdig'i bilan saqlangan"
                      >
                        tasdiq bilan
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-slate-500">{t.note || "—"}</td>
                  <td className="px-3 py-2 text-slate-500">{t.branch || "—"}</td>
                  <td className="px-3 py-2 text-slate-500">
                    {t.created_by || "—"}
                    {t.updated_by && (
                      <span className="block text-[11px] text-slate-400">
                        tahrir: {t.updated_by}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    {data?.can_manage && (
                      <>
                        <button
                          onClick={() => setForm({ kind: t.kind, initial: t })}
                          className="text-slate-400 hover:text-brand-600 mr-2"
                          title="Tahrirlash (summa, sana, izoh)"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => remove(t)}
                          className="text-slate-300 hover:text-red-500"
                          title="O'chirish"
                        >
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="px-4 py-2 text-[11px] text-slate-400">
        O'tkazma kirim ham, chiqim ham emas — pul usuldan usulga o'tadi.
        Bank komissiyasi xarajat bo'lib bir marta yoziladi (foyda-zararda
        faqat u ko'rinadi).
      </p>

      {form && (
        <BankTransferForm
          kind={form.kind}
          initial={form.initial}
          feePercent={form.initial ? form.initial.fee_rate : rate}
          limited={limited}
          branches={needBranch && !form.initial ? branches : []}
          defaultBranchId={
            form.initial?.branch_id ?? globalBranch ?? user?.branch_id ?? null
          }
          onClose={() => setForm(null)}
          onSaved={() => {
            setForm(null);
            changed();
          }}
        />
      )}
    </div>
  );
}

function BankTransferForm({
  kind,
  initial,
  feePercent,
  limited,
  branches,
  defaultBranchId,
  onClose,
  onSaved,
}: {
  kind: BankTransferKind;
  initial: BankTransfer | null;
  feePercent: number;
  limited: boolean;
  branches: Branch[];
  defaultBranchId: number | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [amount, setAmount] = useState(initial ? String(initial.amount) : "");
  const [date, setDate] = useState(initial?.date || todayIso());
  const [note, setNote] = useState(initial?.note || "");
  const [branchId, setBranchId] = useState<number | null>(
    defaultBranchId ?? (branches.length === 1 ? branches[0].id : null),
  );
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  // Qoldiqdan oshiq — rahbariyat "Baribir saqlash" bilan tasdiqlaydi
  const [forceMsg, setForceMsg] = useState<string | null>(null);
  const [bal, setBal] = useState<BankTransferBalance | null>(null);

  const amt = Number(String(amount).replace(/\s|,/g, "")) || 0;
  const { fee, net } = calc(kind, amt, feePercent);
  const src = kind === "withdraw" ? "terminal" : "cash";

  useEffect(() => {
    if (branches.length === 1 && !branchId) setBranchId(branches[0].id);
  }, [branches, branchId]);

  // Qoldiq — cheklangan filial administratoriga ko'rsatilmaydi
  useEffect(() => {
    if (limited || !branchId || !date) {
      setBal(null);
      return;
    }
    api
      .get<BankTransferBalance>(
        `/bank-transfers/balance?branch_id=${branchId}&day=${date}`, true)
      .then(setBal)
      .catch(() => setBal(null));
  }, [branchId, date, limited]);

  async function save(force = false) {
    if (!amt || amt <= 0) {
      setErr("Summani kiriting");
      return;
    }
    if (!initial && branches.length > 0 && !branchId) {
      setErr("Filialni tanlang");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      if (initial) {
        await api.put(`/bank-transfers/${initial.id}`, {
          amount: amt, date, note, force,
        });
      } else {
        await api.post("/bank-transfers", {
          kind, amount: amt, date, note, branch_id: branchId, force,
        });
      }
      onSaved();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Xatolik";
      if (e instanceof ApiError && e.canForce && !force) {
        setForceMsg(msg);
      } else {
        setForceMsg(null);
        setErr(msg);
      }
    } finally {
      setSaving(false);
    }
  }

  const title = kind === "withdraw" ? "Terminaldan naqd yechish" : "Naqdni terminalga topshirish";
  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white";
  const avail = bal?.tracked ? (src === "terminal" ? bal.terminal : bal.cash) : null;

  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">
            {initial ? `${title} — tahrirlash` : title}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <label className="block">
            <span className="text-xs text-slate-500">
              {kind === "withdraw" ? "Terminaldan yechiladigan summa (so'm)" : "Topshiriladigan naqd (so'm)"}
            </span>
            <MoneyInput
              className={input}
              value={amount}
              onChange={(v) => {
                setAmount(v);
                setForceMsg(null);
              }}
              placeholder="1,000,000"
              autoFocus
            />
            {avail !== null && avail !== undefined && (
              <span className="text-[11px] text-slate-400">
                {src === "terminal" ? "Terminalda" : "Naqd kassada"} shu kun oxirida:{" "}
                {formatSom(avail)}
                {initial ? " (bu o'tkazma ham hisobga olingan)" : ""}
              </span>
            )}
          </label>

          {/* Jonli hisob: komissiya va sof summa */}
          <div className="rounded-lg bg-sky-50 border border-sky-100 px-3 py-2 text-sm space-y-0.5">
            {kind === "withdraw" ? (
              <>
                <p className="flex justify-between">
                  <span className="text-slate-600">Terminaldan chiqadi</span>
                  <b className="tabular-nums text-red-700">−{formatSom(amt)}</b>
                </p>
                <p className="flex justify-between">
                  <span className="text-slate-600">Bank komissiyasi ({pct(feePercent)})</span>
                  <b className="tabular-nums text-slate-800">{formatSom(fee)}</b>
                </p>
                <p className="flex justify-between">
                  <span className="text-slate-600">Naqd kassaga tushadi</span>
                  <b className="tabular-nums text-emerald-700">+{formatSom(net)}</b>
                </p>
                <p className="text-[11px] text-slate-400 pt-1">
                  Komissiya "Bank komissiyasi (1%)" xarajati bo'lib bir marta
                  yoziladi; qolgani daromad ham, xarajat ham emas.
                </p>
              </>
            ) : (
              <>
                <p className="flex justify-between">
                  <span className="text-slate-600">Naqd kassadan chiqadi</span>
                  <b className="tabular-nums text-red-700">−{formatSom(amt)}</b>
                </p>
                <p className="flex justify-between">
                  <span className="text-slate-600">Terminalga tushadi</span>
                  <b className="tabular-nums text-emerald-700">+{formatSom(amt)}</b>
                </p>
                <p className="text-[11px] text-slate-400 pt-1">
                  Komissiyasiz; foyda-zararga ta'siri yo'q.
                </p>
              </>
            )}
          </div>

          {!limited && (
            <label className="block">
              <span className="text-xs text-slate-500">Sana</span>
              <input
                type="date"
                className={input}
                value={date}
                max={todayIso()}
                onChange={(e) => {
                  setDate(e.target.value);
                  setForceMsg(null);
                }}
              />
            </label>
          )}
          {branches.length > 1 && !initial && (
            <label className="block">
              <span className="text-xs text-slate-500">Filial</span>
              <select
                className={input}
                value={branchId ?? ""}
                onChange={(e) => {
                  setBranchId(Number(e.target.value) || null);
                  setForceMsg(null);
                }}
              >
                <option value="">— tanlang —</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </label>
          )}
          <label className="block">
            <span className="text-xs text-slate-500">Izoh</span>
            <input
              className={input}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={kind === "withdraw" ? "Masalan: bank kassasidan oldim" : "Masalan: inkassatsiya"}
            />
          </label>
        </div>

        {forceMsg && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {forceMsg}
          </div>
        )}
        {err && <p className="text-sm text-red-600 mt-3">{err}</p>}
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-300">
            Bekor qilish
          </button>
          {forceMsg ? (
            <button
              onClick={() => save(true)}
              disabled={saving}
              className="px-4 py-2 text-sm rounded-lg bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-50"
            >
              {saving ? "Saqlanmoqda..." : "Baribir saqlash"}
            </button>
          ) : (
            <button
              onClick={() => save(false)}
              disabled={saving}
              className="px-4 py-2 text-sm rounded-lg bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-50"
            >
              {saving ? "Saqlanmoqda..." : "Saqlash"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
