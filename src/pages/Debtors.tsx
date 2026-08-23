import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle, Phone, Check, X, CalendarClock, Clock, History,
} from "lucide-react";
import {
  api, type DebtorList, type DebtorRow, type DebtContactRow,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { formatPhone } from "../components/PhoneInput";
import { StudentPayButton } from "../components/QuickPayment";
import { BranchPicker, branchParam } from "../components/BranchPicker";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-600",
  amber: "bg-amber-100 text-amber-700",
  orange: "bg-orange-100 text-orange-700",
  red: "bg-red-100 text-red-700",
  emerald: "bg-emerald-100 text-emerald-700",
};

/**
 * Qarzdorlar bilan ishlash. Administratorning kuni shu ro'yxatdan
 * boshlanadi: kim va'dasini buzdi, kim bugun to'layman degan, kim bilan
 * hali umuman gaplashilmagan.
 */
export default function Debtors() {
  const [data, setData] = useState<DebtorList | null>(null);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [contact, setContact] = useState<DebtorRow | null>(null);
  const [history, setHistory] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<DebtorList>(`/debtors?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, [branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const today = new Date().toISOString().slice(0, 10);
  const rows = data.rows.filter((r) => {
    if (filter === "broken") return r.promise_broken;
    if (filter === "today") return r.promised_date === today;
    if (filter === "never") return !r.last_contact;
    if (filter.startsWith("age:")) return r.bucket === filter.slice(4);
    return true;
  });


  return (
    <div data-guide="debtors-table">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Stat
          label="Jami qarz"
          value={formatSom(data.total_debt)}
          hint={`${data.count} ta o'quvchi`}
          tone="red"
        />
        <Stat
          label="Va'dasini buzganlar"
          value={String(data.broken_promises)}
          hint="birinchi shularga qo'ng'iroq"
          tone={data.broken_promises > 0 ? "red" : "plain"}
          onClick={() => setFilter(filter === "broken" ? "" : "broken")}
          active={filter === "broken"}
        />
        <Stat
          label="Bugun to'layman deganlar"
          value={String(data.due_today)}
          hint="eslatib qo'yish kerak"
          tone={data.due_today > 0 ? "amber" : "plain"}
          onClick={() => setFilter(filter === "today" ? "" : "today")}
          active={filter === "today"}
        />
        <Stat
          label="Hali gaplashilmagan"
          value={String(data.never_contacted)}
          hint="bog'lanish kerak"
          tone={data.never_contacted > 0 ? "amber" : "plain"}
          onClick={() => setFilter(filter === "never" ? "" : "never")}
          active={filter === "never"}
        />
      </div>

      {/* Qarz eskirish (aging) — 2026-08-12, Jahongir: "0-15 / 16-30 /
          31-60 / 60+ kun bo'yicha bo'lish" */}
      {data.aging && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          {data.aging.map((a) => (
            <button
              key={a.key}
              onClick={() => setFilter(filter === `age:${a.key}` ? "" : `age:${a.key}`)}
              className={`text-left bg-white rounded-xl border p-3 transition ${
                filter === `age:${a.key}`
                  ? "border-brand-500 ring-1 ring-brand-300"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <p className="text-xs text-slate-500 mb-0.5">
                Minusda: {a.label}
              </p>
              <p className={`text-base font-semibold ${
                a.key === "b60p" && a.count ? "text-red-700" : "text-slate-900"}`}>
                {a.count} ta
                <span className="block text-xs font-normal text-slate-400">
                  {formatSom(a.sum)}
                </span>
              </p>
            </button>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 mb-4">
        {filter && (
          <button
            onClick={() => setFilter("")}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-50 border border-brand-400 text-brand-700"
          >
            Filtr yoqilgan <X size={12} />
          </button>
        )}
        <BranchPicker value={branchId} onChange={setBranchId} />
        <span className="text-sm text-slate-500">{rows.length} ta</span>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Qarzdor yo'q — hammasi to'lagan.
        </p>
      ) : (
        <div className="space-y-2">
          {rows.map((r) => (
            <div
              key={r.student_id}
              className={`bg-white rounded-xl border p-4 ${
                r.promise_broken ? "border-red-300" : "border-slate-200"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Link
                      to={`/students/${r.student_id}`}
                      className="text-sm font-medium text-slate-900 hover:text-brand-700"
                    >
                      {r.full_name}
                    </Link>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        TONE[r.urgency_tone] || TONE.slate
                      }`}
                    >
                      {r.urgency_label} · {r.days} kun
                    </span>
                    {r.aging_days > 15 && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        TONE[
                          r.bucket === "b60p" ? "red"
                          : r.bucket === "b60" ? "orange" : "amber"
                        ]}`}>
                        {r.aging_days} kundan beri minusda
                      </span>
                    )}
                    {r.promise_broken && (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 flex items-center gap-1">
                        <AlertTriangle size={11} />
                        Va'dasini buzdi
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {[r.group, formatPhone(r.phone || r.parent_phone)]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>

                  {r.last_contact ? (
                    <p className="text-xs text-slate-500 mt-1.5 flex items-center gap-1.5 flex-wrap">
                      <Clock size={11} className="text-slate-400" />
                      <span>
                        {formatDate(r.last_contact)} — {r.last_result_label}
                        {r.last_by ? ` (${r.last_by})` : ""}
                      </span>
                      {r.promised_date && (
                        <span
                          className={
                            r.promise_broken
                              ? "text-red-600 font-medium"
                              : "text-emerald-700"
                          }
                        >
                          · {formatDate(r.promised_date)} ga va'da
                          {r.promised_amount
                            ? ` (${formatSom(r.promised_amount)})`
                            : ""}
                        </span>
                      )}
                    </p>
                  ) : (
                    <p className="text-xs text-amber-600 mt-1.5">
                      Hali bog'lanilmagan
                    </p>
                  )}
                  {r.last_note && (
                    <p className="text-xs text-slate-600 mt-1">{r.last_note}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <div className="text-right mr-1">
                    <p className="text-xs text-slate-500">Qarzi</p>
                    <p className="text-base font-semibold text-red-600">
                      {formatSom(r.debt)}
                    </p>
                  </div>
                  <button
                    onClick={() =>
                      setHistory(history === r.student_id ? null : r.student_id)
                    }
                    title="Bog'lanishlar tarixi"
                    className="p-2 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-slate-50"
                  >
                    <History size={15} />
                  </button>
                  <button
                    onClick={() => setContact(r)}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-300 text-sm text-brand-700 hover:bg-brand-50"
                  >
                    <Phone size={14} /> Bog'lanildi
                  </button>
                  <StudentPayButton
                    student={
                      {
                        id: r.student_id,
                        full_name: r.full_name,
                        balance: -r.debt,
                        group: r.group ? { name: r.group } : null,
                      } as never
                    }
                    onDone={load}
                  />
                </div>
              </div>

              {history === r.student_id && (
                <ContactHistory studentId={r.student_id} />
              )}
            </div>
          ))}
        </div>
      )}

      {contact && (
        <ContactForm
          row={contact}
          results={data.results}
          onClose={() => setContact(null)}
          onSaved={() => {
            setContact(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  tone,
  onClick,
  active,
}: {
  label: string;
  value: string;
  hint?: string;
  tone: string;
  onClick?: () => void;
  active?: boolean;
}) {
  const bg =
    tone === "red"
      ? "bg-red-50 border-red-200"
      : tone === "amber"
        ? "bg-amber-50 border-amber-200"
        : "bg-white border-slate-200";
  const fg =
    tone === "red"
      ? "text-red-700"
      : tone === "amber"
        ? "text-amber-700"
        : "text-slate-900";
  return (
    <button
      onClick={onClick}
      disabled={!onClick}
      className={`rounded-xl border p-4 text-left transition ${bg} ${
        active ? "ring-2 ring-brand-400" : ""
      } ${onClick ? "hover:border-brand-300" : "cursor-default"}`}
    >
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${fg}`}>{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </button>
  );
}

function ContactHistory({ studentId }: { studentId: number }) {
  const [rows, setRows] = useState<DebtContactRow[]>([]);
  useEffect(() => {
    api
      .get<DebtContactRow[]>(`/students/${studentId}/debt-contacts`)
      .then(setRows);
  }, [studentId]);

  if (rows.length === 0)
    return (
      <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-100">
        Bog'lanish yozuvi yo'q
      </p>
    );

  return (
    <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
      {rows.map((c) => (
        <div key={c.id} className="flex items-start gap-3 text-xs">
          <span className="text-slate-400 w-24 shrink-0">
            {c.date ? formatDate(c.date) : "—"}
          </span>
          <span
            className={`px-1.5 py-0.5 rounded shrink-0 ${
              TONE[c.tone] || TONE.slate
            }`}
          >
            {c.result_label}
          </span>
          {c.promised_date && (
            <span className="text-slate-600 shrink-0">
              {formatDate(c.promised_date)} ga
            </span>
          )}
          <span className="text-slate-600 flex-1">{c.note}</span>
          <span className="text-slate-400">{c.by}</span>
        </div>
      ))}
    </div>
  );
}

function ContactForm({
  row,
  results,
  onClose,
  onSaved,
}: {
  row: DebtorRow;
  results: { key: string; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [result, setResult] = useState("promised");
  const [when, setWhen] = useState("");
  const [amount, setAmount] = useState(String(Math.round(row.debt)));
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  const today = new Date();
  function quick(days: number) {
    const d = new Date(today);
    d.setDate(d.getDate() + days);
    setWhen(d.toISOString().slice(0, 10));
  }

  async function save() {
    if (result === "promised" && !when) {
      setErr("Qachonga to'layman deganini tanlang");
      return;
    }
    setSaving(true);
    try {
      await api.post("/debtors/contact", {
        student_id: row.student_id,
        result,
        promised_date: result === "promised" ? when : null,
        promised_amount: amount ? Number(amount) : null,
        note: note || null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-20">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">{row.full_name}</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Qarzi {formatSom(row.debt)} ·{" "}
          {formatPhone(row.phone || row.parent_phone)}
        </p>

        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">
              Nima dedi?
            </label>
            <div className="grid grid-cols-2 gap-1.5">
              {results.map((r) => (
                <button
                  key={r.key}
                  onClick={() => setResult(r.key)}
                  className={`px-2 py-2 rounded-lg text-xs font-medium border transition ${
                    result === r.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          {result === "promised" && (
            <>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">
                  Qachonga to'layman dedi?
                </label>
                <div className="flex gap-1.5 mb-2">
                  {[
                    { d: 0, l: "Bugun" },
                    { d: 1, l: "Ertaga" },
                    { d: 3, l: "3 kun" },
                    { d: 7, l: "1 hafta" },
                  ].map((q) => (
                    <button
                      key={q.d}
                      onClick={() => quick(q.d)}
                      className="flex-1 px-2 py-1.5 rounded-lg text-xs border border-slate-200 text-slate-600 hover:border-brand-300 hover:text-brand-700"
                    >
                      {q.l}
                    </button>
                  ))}
                </div>
                <input
                  type="date"
                  value={when}
                  onChange={(e) => setWhen(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-500 mb-1">
                  Qancha to'layman dedi?
                </label>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                />
              </div>
            </>
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
            className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            <Check size={15} />
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
          {result === "promised" && when && (
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <CalendarClock size={11} />
              {formatDate(when)} kuni to'lamasa — ro'yxatning eng tepasiga
              chiqadi.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
