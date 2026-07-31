import { useEffect, useState } from "react";
import { BookOpen, Info, X, Plus, Trash2 } from "lucide-react";
import {
  api, type MyBookOrders, type BookCatalogue,
} from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
};

/** Ustoz kitob so'raydi — so'rov filial rahbariga vazifa bo'lib boradi. */
export default function MyBooks() {
  const [d, setD] = useState<MyBookOrders | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    api
      .get<MyBookOrders>("/me/book-orders")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <BookOpen size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Kitob buyurtmasi
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Guruhingiz uchun kitob so'rang
      </p>

      <button
        onClick={() => setAdding(true)}
        className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium mb-5"
      >
        Yangi buyurtma
      </button>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Hali buyurtma bermagansiz.
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
                  {o.total_qty} dona · {o.titles} xil
                </span>
                {o.group && (
                  <span className="text-xs text-slate-500">{o.group}</span>
                )}
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    TONE[o.urgency_tone] || TONE.slate
                  }`}
                >
                  {o.urgency_label}
                </span>
                <span
                  className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                    TONE[o.status_tone] || TONE.slate
                  }`}
                >
                  {o.status_label}
                </span>
              </div>

              <div className="space-y-0.5 mb-2">
                {o.items.map((i) => (
                  <p key={i.id} className="text-sm text-slate-700">
                    · {i.title}
                    {i.level ? ` (${i.level})` : ""} —{" "}
                    <b>{i.qty} dona</b>
                    {i.delivered_qty > 0 && i.delivered_qty >= i.qty && (
                      <span className="text-emerald-600 text-xs">
                        {" "}
                        yetkazildi
                      </span>
                    )}
                  </p>
                ))}
              </div>

              <p className="text-xs text-slate-500">
                {o.needed_by ? `Kerak: ${formatDate(o.needed_by)}` : ""}
                {o.delivered_at
                  ? ` · Yetkazildi: ${formatDate(o.delivered_at)}`
                  : ""}
                {o.decision_note ? ` · ${o.decision_note}` : ""}
              </p>
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

type Item = { title: string; qty: string; level: string; consumable_id?: number };

function OrderForm({
  data,
  onClose,
  onDone,
}: {
  data: MyBookOrders;
  onClose: () => void;
  onDone: () => void;
}) {
  const [cat, setCat] = useState<BookCatalogue["rows"]>([]);
  const [items, setItems] = useState<Item[]>([
    { title: "", qty: "1", level: "" },
  ]);
  const [f, setF] = useState({
    group_id: "",
    needed_by: "",
    urgency: "normal",
    note: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<BookCatalogue>("/books/catalogue")
      .then((d) => setCat(d.rows))
      .catch(() => {});
  }, []);

  const setItem = (i: number, patch: Partial<Item>) =>
    setItems(items.map((x, n) => (n === i ? { ...x, ...patch } : x)));

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post("/me/book-orders", {
        group_id: f.group_id ? Number(f.group_id) : null,
        needed_by: f.needed_by || null,
        urgency: f.urgency,
        note: f.note || null,
        items: items
          .filter((i) => i.title.trim())
          .map((i) => ({
            title: i.title.trim(),
            qty: Number(i.qty || 1),
            level: i.level || null,
            consumable_id: i.consumable_id ?? null,
          })),
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const valid = items.some((i) => i.title.trim() && Number(i.qty) > 0);

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Kitob buyurtmasi</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <p className="text-xs font-medium text-slate-600 mb-2">
          Qaysi kitob va nechta
        </p>
        {items.map((it, i) => (
          <div key={i} className="flex gap-2 mb-2">
            <input
              list="book-catalogue"
              value={it.title}
              onChange={(e) => {
                const hit = cat.find((c) => c.name === e.target.value);
                setItem(i, {
                  title: e.target.value,
                  consumable_id: hit?.id,
                });
              }}
              placeholder="Kitob nomi *"
              className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
            <input
              value={it.level}
              onChange={(e) => setItem(i, { level: e.target.value })}
              placeholder="Daraja"
              className="w-24 border border-slate-300 rounded-lg px-2 py-2 text-sm"
            />
            <input
              type="number"
              min={1}
              value={it.qty}
              onChange={(e) => setItem(i, { qty: e.target.value })}
              placeholder="Soni"
              className="w-20 border border-slate-300 rounded-lg px-2 py-2 text-sm"
            />
            {items.length > 1 && (
              <button
                onClick={() => setItems(items.filter((_, n) => n !== i))}
                className="text-slate-400 hover:text-red-600 px-1"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        ))}
        <datalist id="book-catalogue">
          {cat.map((c) => (
            <option key={c.id} value={c.name}>
              {c.in_stock ? `omborda ${c.qty} ta` : "omborda yo'q"}
            </option>
          ))}
        </datalist>

        <button
          onClick={() =>
            setItems([...items, { title: "", qty: "1", level: "" }])
          }
          className="text-xs text-brand-600 font-medium flex items-center gap-1 mb-4"
        >
          <Plus size={14} /> Yana kitob qo'shish
        </button>

        <div className="grid grid-cols-2 gap-2 mb-2">
          <select
            value={f.group_id}
            onChange={(e) => setF({ ...f, group_id: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm"
          >
            <option value="">Guruh (ixtiyoriy)</option>
            {data.groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
          <select
            value={f.urgency}
            onChange={(e) => setF({ ...f, urgency: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm"
          >
            {data.urgencies.map((u) => (
              <option key={u.key} value={u.key}>
                {u.label}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-2">
          <label className="block text-xs text-slate-500 mb-1">
            Qachonga kerak
          </label>
          <input
            type="date"
            value={f.needed_by}
            onChange={(e) => setF({ ...f, needed_by: e.target.value })}
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <textarea
          value={f.note}
          onChange={(e) => setF({ ...f, note: e.target.value })}
          rows={2}
          placeholder="Izoh"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <p className="text-xs text-slate-500 mb-3">
          Yuborilgach filial rahbariga vazifa bo'lib boradi va bajarilishi
          kuzatiladi.
        </p>

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={save}
          disabled={busy || !valid}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
        >
          Yuborish
        </button>
      </div>
    </div>
  );
}
