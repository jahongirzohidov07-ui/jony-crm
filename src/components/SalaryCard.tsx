import { useEffect, useState } from "react";
import {
  Wallet, X, TrendingUp, Info, Trash2, Plus,
} from "lucide-react";
import { api, type SalaryCard as Card } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";

/**
 * Ustoz ish haqi kartasi.
 *
 * Ish haqi YOQLAMADAN avtomat hisoblanadi — hech kim hech narsani
 * bosmaydi. Bu yerda faqat berilgan pul kiritiladi.
 */
export function SalaryCard({
  teacherId,
  self = false,
  onClose,
}: {
  teacherId?: number;
  self?: boolean;
  onClose?: () => void;
}) {
  const [c, setC] = useState<Card | null>(null);
  const [form, setForm] = useState(false);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<Card>(self ? "/my/salary" : `/teachers/${teacherId}/salary`)
      .then(setC)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }
  useEffect(load, [teacherId, self]);

  const body = loading ? (
    <p className="text-sm text-slate-400 py-6">Yuklanmoqda...</p>
  ) : err ? (
    <p className="text-sm text-slate-500 py-6">{err}</p>
  ) : !c ? null : (
    <div className="space-y-5">
      {/* --- Asosiy raqamlar --- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Box
          label="Shu oy ishlab topgan"
          value={formatSom(c.earned_month)}
          hint={`${c.lessons_month} dars · ${c.attendances_month} yoqlama`}
          tone="brand"
        />
        <Box
          label="Shu oy olgan"
          value={formatSom(c.paid_month)}
          hint="avans va oylik"
        />
        <Box
          label="Balans"
          value={formatSom(c.balance)}
          hint={
            c.balance > 0
              ? "sizga berilishi kerak"
              : c.balance < 0
                ? "ortiqcha olingan"
                : "hisob yopilgan"
          }
          tone={c.balance > 0 ? "good" : c.balance < 0 ? "bad" : "plain"}
        />
        <Box
          label="O'tgan oylardan"
          value={formatSom(c.carry)}
          hint={c.carry_label}
          tone={c.carry > 0 ? "good" : c.carry < 0 ? "bad" : "plain"}
        />
      </div>

      {/* --- Formula --- */}
      {c.by_group.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <Info size={13} className="text-slate-400" />
            <p className="text-xs font-medium text-slate-700">
              Qanday hisoblandi
            </p>
          </div>
          <div className="space-y-2">
            {c.by_group.map((g) => (
              <div
                key={g.group_id}
                className="rounded-lg border border-slate-100 px-3 py-2.5"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-sm text-slate-800">{g.group}</span>
                  <span className="text-sm font-semibold text-slate-900">
                    {formatSom(g.amount)}
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Bir o'quvchidan oyiga{" "}
                  {formatSom(g.rate_per_student_month)} ÷ {g.standard_lessons}{" "}
                  dars ={" "}
                  <span className="text-brand-700 font-medium">
                    {formatSom(g.rate)}
                  </span>{" "}
                  har bir yoqlamadan
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {g.lessons} dars · {g.attendances} yoqlama ×{" "}
                  {formatSom(g.rate)} = {formatSom(g.amount)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {c.by_group.length === 0 && (
        <div className="bg-slate-50 rounded-lg px-4 py-6 text-center">
          <p className="text-sm text-slate-500">
            Bu oyda hali yoqlama qo'yilmagan.
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Yoqlama qo'yilishi bilan oylik o'zi hisoblanadi.
          </p>
        </div>
      )}

      {/* --- Oylar bo'yicha --- */}
      {c.by_period.length > 1 && (
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <TrendingUp size={13} className="text-slate-400" />
            <p className="text-xs font-medium text-slate-700">
              Oylar bo'yicha
            </p>
          </div>
          <div className="flex items-end gap-1.5 h-20">
            {c.by_period.map((p) => {
              const max = Math.max(...c.by_period.map((x) => x.amount), 1);
              return (
                <div
                  key={p.period}
                  className="flex-1 flex flex-col items-center gap-1"
                  title={`${p.period}: ${formatSom(p.amount)}`}
                >
                  <div
                    className="w-full rounded-t bg-brand-400"
                    style={{ height: `${(p.amount / max) * 100}%` }}
                  />
                  <span className="text-[10px] text-slate-400">
                    {p.period.slice(5)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- To'lovlar --- */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Wallet size={13} className="text-slate-400" />
          <p className="text-xs font-medium text-slate-700">Berilgan pullar</p>
          <div className="flex-1" />
          {c.can_pay && (
            <button
              onClick={() => setForm(true)}
              className="flex items-center gap-1 text-xs text-brand-600 hover:underline"
            >
              <Plus size={12} /> pul berish
            </button>
          )}
        </div>

        {c.payments.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">Hali pul berilmagan</p>
        ) : (
          <div className="space-y-1">
            {c.payments.map((p) => (
              <div
                key={p.id}
                className="flex items-center gap-3 py-1.5 border-b border-slate-50 text-xs"
              >
                <span className="text-slate-400 w-24">
                  {p.date ? formatDate(p.date) : "—"}
                </span>
                <span className="w-16 text-slate-500">{p.kind_label}</span>
                <span className="w-28 text-slate-800 font-medium">
                  {formatSom(p.amount)}
                </span>
                <span className="flex-1 text-slate-500">{p.note}</span>
                <span className="text-slate-400">{p.by}</span>
                {c.can_pay && (
                  <button
                    onClick={async () => {
                      if (!confirm("Bu yozuv o'chirilsinmi?")) return;
                      await api.delete(`/teacher-payments/${p.id}`);
                      load();
                    }}
                    className="text-slate-300 hover:text-red-600"
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {form && c && (
        <PayForm
          card={c}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
        />
      )}
    </div>
  );

  if (!onClose) return body;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-12 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-3xl shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            <h3 className="font-semibold text-slate-900">
              {c?.full_name ?? "Ish haqi"}
            </h3>
            <p className="text-xs text-slate-500">
              Yoqlamadan avtomat hisoblanadi
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="p-5">{body}</div>
      </div>
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

function PayForm({
  card,
  onClose,
  onSaved,
}: {
  card: Card;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [kind, setKind] = useState("advance");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  async function save() {
    const v = Number(amount);
    if (!v || v <= 0) {
      setErr("Summani kiriting");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/teachers/${card.teacher_id}/payments`, {
        amount: v,
        kind,
        note: note || null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-start justify-center z-[60] p-4 pt-24">
      <div className="bg-white rounded-xl w-full max-w-sm p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Pul berish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">{card.full_name}</p>

        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}

        <div className="space-y-3">
          <div className="flex gap-1.5">
            {[
              { k: "advance", l: "Avans" },
              { k: "salary", l: "Oylik" },
              { k: "correction", l: "Tuzatish" },
            ].map((o) => (
              <button
                key={o.k}
                onClick={() => setKind(o.k)}
                className={`flex-1 px-2 py-2 rounded-lg text-xs font-medium border transition ${
                  kind === o.k
                    ? "bg-brand-50 border-brand-400 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                }`}
              >
                {o.l}
              </button>
            ))}
          </div>

          {kind === "advance" && (
            <div className="bg-slate-50 rounded-lg px-3 py-2">
              <p className="text-xs text-slate-600">
                Bera oladigan summa:{" "}
                <span className="font-medium text-slate-800">
                  {formatSom(card.advance_available)}
                </span>
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                Avans ishlab topilgan puldan ortiq berilmaydi.
              </p>
            </div>
          )}

          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="500000"
            autoFocus
            className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-base"
          />

          {kind === "advance" && card.advance_available > 0 && (
            <button
              onClick={() => setAmount(String(Math.round(card.advance_available)))}
              className="w-full py-2 rounded-lg border border-brand-200 bg-brand-50 text-sm text-brand-700 hover:border-brand-400"
            >
              Hammasini berish — {formatSom(card.advance_available)}
            </button>
          )}

          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Izoh (ixtiyoriy)"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />

          <button
            onClick={save}
            disabled={saving}
            className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? "Saqlanmoqda..." : "Berildi"}
          </button>
        </div>
      </div>
    </div>
  );
}
