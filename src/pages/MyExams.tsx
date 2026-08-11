import { useEffect, useState } from "react";
import { ClipboardCheck, Info, X, CheckCircle2 } from "lucide-react";
import { api, type MyExamOrders, type ExamOrder } from "../lib/api";
import { Time24Input } from "../components/Time24Input";

const TONE: Record<string, string> = {
  amber: "bg-amber-100 text-amber-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

/**
 * Ustozning imtihon buyurtmalari.
 *
 * Ilgari ustoz imtihonni "qoralama" qilib yaratardi va u examiner
 * ro'yxatni ochgunicha kutib turardi — ish hech kimga bormasdi.
 * Endi so'rov filialdagi examinerlarga vazifa bo'lib boradi.
 */
export default function MyExams() {
  const [d, setD] = useState<MyExamOrders | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    api
      .get<MyExamOrders>("/me/exam-orders")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  const cancel = async (o: ExamOrder) => {
    await api.post(`/me/exam-orders/${o.id}/cancel`, {});
    load();
  };

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ClipboardCheck size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Imtihon buyurtmasi
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Guruhingizga imtihon so'rang
      </p>

      <button
        onClick={() => setAdding(true)}
        className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium mb-5"
      >
        Yangi buyurtma
      </button>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Hali imtihon buyurtma qilmagansiz.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((o) => (
            <div
              key={o.id}
              className="bg-white border border-slate-200 rounded-xl p-3.5"
            >
              <div className="flex items-center gap-2 flex-wrap mb-2">
                <span className="text-xs font-mono text-slate-400">
                  {o.public_id}
                </span>
                <span className="text-sm font-medium text-slate-900">
                  {o.group} · {o.kind_label}
                </span>
                <span className="text-xs text-slate-500">
                  {o.date_text} {o.time}
                </span>
                <span
                  className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                    TONE[o.status_tone] || TONE.slate
                  }`}
                >
                  {o.status_label}
                </span>
              </div>

              <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                {o.message}
              </pre>

              {o.status === "rejected" && (
                <p className="text-xs text-red-600 mt-1.5">
                  Sabab: {o.reject_reason_label || "—"}
                  {o.decision_note ? ` · ${o.decision_note}` : ""}
                </p>
              )}

              {(o.status === "new" || o.status === "accepted") && (
                <button
                  onClick={() => cancel(o)}
                  className="text-xs text-slate-400 hover:text-red-600 mt-2"
                >
                  Buyurtmani bekor qilish
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {adding && (
        <OrderForm
          data={d}
          onClose={() => setAdding(false)}
          onDone={() => {
            setAdding(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function OrderForm({
  data,
  onClose,
  onDone,
}: {
  data: MyExamOrders;
  onClose: () => void;
  onDone: () => void;
}) {
  const [f, setF] = useState({
    group_id: String(data.groups[0]?.id ?? ""),
    date: "",
    time: "",
    kind: "unit",
    unit_no: "",
    note: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const group = data.groups.find((g) => String(g.id) === f.group_id);
  const min = new Date(Date.now() + data.min_notice_days * 86400000)
    .toISOString()
    .slice(0, 10);
  const max = new Date(Date.now() + data.max_ahead_days * 86400000)
    .toISOString()
    .slice(0, 10);

  const save = async () => {
    if (f.kind === "unit" && !f.unit_no) {
      setErr("Qaysi unit ekanini belgilang — examiner shu unitning testini tayyorlab keladi");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await api.post("/me/exam-orders", {
        group_id: Number(f.group_id),
        date: f.date,
        time: f.time || group?.time || null,
        kind: f.kind,
        unit_no: f.kind === "unit" && f.unit_no ? Number(f.unit_no) : null,
        note: f.note || null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-sm max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Imtihon buyurtmasi</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <label className="block text-xs text-slate-500 mb-1">Guruh</label>
        <select
          value={f.group_id}
          onChange={(e) => setF({ ...f, group_id: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        >
          {data.groups.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name} ({g.students} o'quvchi)
            </option>
          ))}
        </select>

        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Sana</label>
            <input
              type="date"
              value={f.date}
              min={min}
              max={max}
              onChange={(e) => setF({ ...f, date: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Vaqt</label>
            <Time24Input
              value={f.time || group?.time || ""}
              onChange={(e) => setF({ ...f, time: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Test turi
            </label>
            <select
              value={f.kind}
              onChange={(e) => setF({ ...f, kind: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            >
              {data.kinds.map((k) => (
                <option key={k.key} value={k.key}>
                  {k.label}
                </option>
              ))}
            </select>
          </div>
          {f.kind === "unit" && (
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Qaysi unit? *
              </label>
              <input
                type="number"
                min={1}
                max={data.unit_count}
                value={f.unit_no}
                onChange={(e) => setF({ ...f, unit_no: e.target.value })}
                required
                placeholder="masalan: 5"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              />
              <p className="text-[11px] text-slate-400 mt-0.5">
                Examiner aynan shu unitning testini tayyorlab keladi
              </p>
            </div>
          )}
        </div>

        <textarea
          value={f.note}
          onChange={(e) => setF({ ...f, note: e.target.value })}
          rows={2}
          placeholder="Izoh (ixtiyoriy)"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <p className="text-xs text-slate-500 mb-3">
          O'quvchilar soni avtomat qo'shiladi
          {group ? ` — hozir ${group.students} ta` : ""}. Kamida{" "}
          {data.min_notice_days} kun oldin so'raladi.
        </p>

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={save}
          disabled={busy || !f.date || !f.group_id}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
        >
          Yuborish
        </button>
      </div>
    </div>
  );
}

/** Examiner navbati — filialiga mos so'rovlar. */
export function ExamOrderQueueTab() {
  const [d, setD] = useState<import("../lib/api").ExamOrderQueue | null>(null);
  const [filter, setFilter] = useState("");
  const [rejecting, setRejecting] = useState<ExamOrder | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [err, setErr] = useState("");

  const load = () => {
    setErr("");
    const p = filter ? `?status=${filter}` : "";
    api
      .get<import("../lib/api").ExamOrderQueue>("/exam-orders" + p)
      .then(setD)
      .catch((e) =>
        setErr(e instanceof Error ? e.message : "Ro'yxatni yuklab bo'lmadi")
      );
  };
  useEffect(load, [filter]);

  const act = async (o: ExamOrder, what: "accept" | "done") => {
    setBusy(o.id);
    setErr("");
    try {
      await api.post(`/exam-orders/${o.id}/${what}`, {});
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  };

  if (err && !d)
    return (
      <div className="py-6">
        <p className="text-sm text-red-600 mb-2">{err}</p>
        <button
          onClick={load}
          className="text-sm text-brand-600 hover:text-brand-700 underline"
        >
          Qayta urinish
        </button>
      </div>
    );
  if (!d) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <span className="px-2 py-1 rounded-lg text-xs font-medium bg-amber-100 text-amber-700">
          {d.new} yangi so'rov
        </span>
        <span className="px-2 py-1 rounded-lg text-xs font-medium bg-emerald-100 text-emerald-700">
          {d.accepted} qabul qilingan
        </span>
        <div className="flex-1" />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
        >
          <option value="">Barchasi</option>
          {d.statuses.map((s) => (
            <option key={s.key} value={s.key}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {d.urgent.length > 0 && (
        <p className="text-sm rounded-lg px-3 py-2 mb-4 bg-red-50 border border-red-200 text-red-800">
          {d.urgent.length} ta so'rov bugun yoki ertaga — hali qabul
          qilinmagan.
        </p>
      )}

      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          So'rov yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((o) => (
            <div
              key={o.id}
              className="bg-white border border-slate-200 rounded-xl p-3.5"
            >
              <div className="flex items-center gap-2 flex-wrap mb-2">
                <span className="text-xs font-mono text-slate-400">
                  {o.public_id}
                </span>
                <span className="text-sm font-medium text-slate-900">
                  {o.branch} · {o.group}
                </span>
                <span
                  className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                    TONE[o.status_tone] || TONE.slate
                  }`}
                >
                  {o.status_label}
                </span>
              </div>

              <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                {o.message}
              </pre>
              {o.note && (
                <p className="text-xs text-slate-500 mt-1.5">
                  Ustoz izohi: {o.note}
                </p>
              )}

              <div className="flex gap-2 mt-2.5">
                {o.status === "new" && (
                  <>
                    <button
                      onClick={() => act(o, "accept")}
                      disabled={busy === o.id}
                      className="flex items-center gap-1 bg-emerald-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-40"
                    >
                      <CheckCircle2 size={13} /> Qabul qilish
                    </button>
                    <button
                      onClick={() => setRejecting(o)}
                      className="border border-slate-300 text-slate-600 rounded-lg px-3 py-1.5 text-xs"
                    >
                      Rad etish
                    </button>
                  </>
                )}
                {o.status === "accepted" && (
                  <button
                    onClick={() => act(o, "done")}
                    disabled={busy === o.id}
                    className="bg-teal-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-40"
                  >
                    O'tkazildi
                  </button>
                )}
                {o.exam_id && (
                  <a
                    href={`/groups/${o.group_id}`}
                    className="text-xs text-brand-600 hover:underline self-center"
                  >
                    imtihonga o'tish
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {rejecting && (
        <RejectModal
          order={rejecting}
          reasons={d.reject_reasons}
          onClose={() => setRejecting(null)}
          onDone={() => {
            setRejecting(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function RejectModal({
  order,
  reasons,
  onClose,
  onDone,
}: {
  order: ExamOrder;
  reasons: { key: string; label: string }[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [reason, setReason] = useState(reasons[0]?.key || "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post(`/exam-orders/${order.id}/reject`, { reason, note });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-semibold text-slate-900 mb-1">
          Buyurtmani rad etish
        </h3>
        <p className="text-sm text-slate-500 mb-4">
          {order.group} · {order.date_text}
        </p>

        <label className="block text-xs text-slate-500 mb-1">Sabab</label>
        <select
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        >
          {reasons.map((r) => (
            <option key={r.key} value={r.key}>
              {r.label}
            </option>
          ))}
        </select>

        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={3}
          placeholder="Ustozga tushuntirish"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        />
        <p className="text-xs text-slate-400 mb-3">
          Ustoz nima qilishini bilishi kerak — sabab unga yetkaziladi.
        </p>

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={save}
          disabled={busy}
          className="w-full bg-red-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
        >
          Rad etish
        </button>
      </div>
    </div>
  );
}
