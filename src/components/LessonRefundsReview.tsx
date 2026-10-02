import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "../lib/api";
import { formatSom } from "../lib/format";

/**
 * "KAM DARS — FARQ QAYTARILDI" QATORLARI (2026-10-02).
 *
 * Jahongir: "ba'zi o'quvchilarda 1-oktabrda qanaqadur chegirma bilan pul
 * qo'shilib qolyabdi ... qayerdan paydo bo'lyabdi shuni bilish kerak" va
 * "bu qanaqa chegirma va nega berilganligiga bog'liq".
 *
 * Avtomat oylik oy oxirida o'tilgan dars standartdan kam sanalsa farqni
 * "+summa chegirma" qilib yozardi (endi o'chirilgan). Bu karta har bir
 * qatorni SABABI bilan ko'rsatadi; asoschi tanlab bekor qiladi. Qator
 * O'chirilganlar arxiviga tushadi, kerak bo'lsa qaytariladi.
 */
interface RefundRow {
  payment_id: number;
  student_id: number;
  name: string;
  branch: string | null;
  status: string;
  period: string | null;
  amount: number;
  refund_group: string;
  charged_groups: string[];
  counted_lessons: number | null;
  standard: number;
  charged: number;
  balance: number;
  reasons: string[];
}

export default function LessonRefundsReview() {
  const [rows, setRows] = useState<RefundRow[] | null>(null);
  const [open, setOpen] = useState(false);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = () =>
    api
      .fresh<{ rows: RefundRow[] }>("/admin/lesson-refunds")
      .then((r) => setRows(r.rows || []))
      .catch(() => setRows([]));
  useEffect(() => {
    load();
  }, []);

  if (!rows || rows.length === 0) return msg ? (
    <p className="mb-5 text-sm text-emerald-700">{msg}</p>
  ) : null;

  const total = rows.reduce((s, r) => s + r.amount, 0);
  const allOn = sel.size === rows.length;

  function toggle(id: number) {
    setSel((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  async function cancel() {
    const ids = [...sel];
    const sum = rows!.filter((r) => sel.has(r.payment_id))
      .reduce((s, r) => s + r.amount, 0);
    if (!confirm(
      `${ids.length} ta qator bekor qilinsinmi? Jami ${formatSom(sum)}.\n\n` +
      "O'quvchilarning qarzi shu summaga oshadi (to'liq oylikka qaytadi). " +
      "Qatorlar O'chirilganlar arxiviga tushadi."
    )) return;
    setBusy(true);
    try {
      const r = await api.post<{ count: number }>(
        "/admin/lesson-refunds/cancel", { ids });
      setMsg(`${r.count} ta qator bekor qilindi.`);
      setSel(new Set());
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-3 p-4 text-left"
      >
        <AlertTriangle size={18} className="text-amber-600 mt-0.5 shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-medium text-amber-900">
            Tekshirish kerak: {rows.length} ta o'quvchiga "kam dars" uchun
            avtomat {formatSom(total)} qaytarilgan
          </p>
          <p className="text-xs text-amber-800 mt-0.5">
            Oy oxirida dars 12 tadan kam sanalgani uchun "+summa chegirma"
            yozilgan. Bu qoida o'chirildi — endi oylik har doim to'liq.
            Har biri nega yozilganini ko'rib, keraklisini bekor qiling.
          </p>
        </div>
        {open ? <ChevronUp size={18} className="text-amber-700" />
          : <ChevronDown size={18} className="text-amber-700" />}
      </button>

      {open && (
        <div className="border-t border-amber-200 bg-white rounded-b-xl">
          <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b border-slate-100">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={allOn}
                onChange={() =>
                  setSel(allOn ? new Set() : new Set(rows.map((r) => r.payment_id)))}
              />
              Hammasini tanlash
            </label>
            <div className="flex-1" />
            <button
              disabled={busy || sel.size === 0}
              onClick={cancel}
              className="px-3 py-2 rounded-lg bg-red-600 text-white text-sm font-medium disabled:opacity-40"
            >
              Tanlanganlarni bekor qilish ({sel.size})
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-xs text-slate-500">
                  <th className="w-8" />
                  <th className="text-left px-3 py-2">O'quvchi</th>
                  <th className="text-left px-3">Oy</th>
                  <th className="text-right px-3">Qaytarilgan</th>
                  <th className="text-left px-3">Nega</th>
                  <th className="text-right px-3">Balans</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.payment_id} className="border-t border-slate-100 align-top">
                    <td className="pl-3 py-2.5">
                      <input
                        type="checkbox"
                        checked={sel.has(r.payment_id)}
                        onChange={() => toggle(r.payment_id)}
                      />
                    </td>
                    <td className="px-3 py-2.5">
                      <Link to={`/students/${r.student_id}`}
                            className="font-medium text-slate-800 hover:underline">
                        {r.name}
                      </Link>
                      <p className="text-xs text-slate-400">
                        {r.branch || "—"} · {r.refund_group}
                      </p>
                    </td>
                    <td className="px-3 py-2.5 text-slate-600">{r.period}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums font-medium text-slate-800">
                      {formatSom(r.amount)}
                      <p className="text-xs font-normal text-slate-400">
                        {r.counted_lessons ?? "?"} / {r.standard} dars sanalgan
                      </p>
                    </td>
                    <td className="px-3 py-2.5">
                      <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                        {r.reasons.map((x, i) => <li key={i}>{x}</li>)}
                      </ul>
                    </td>
                    <td className={`px-3 py-2.5 text-right tabular-nums ${
                      r.balance < 0 ? "text-red-700" : "text-slate-700"}`}>
                      {formatSom(r.balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
