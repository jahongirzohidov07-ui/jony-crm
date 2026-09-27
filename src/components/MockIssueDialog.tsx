import { useState } from "react";
import { X } from "lucide-react";
import { api } from "../lib/api";
import { pushToast } from "../lib/toast";

/**
 * SAVOLDA XATO BOR — xabar oynasi (2026-09-27).
 *
 * Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib ishlaydigan
 * bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq ustozlarga
 * ular ham experience qilib xatolarni aytadida".
 *
 * Xodim mockni yechayotganda yoki yechib bo'lgach savol yonidagi
 * bayroqchani bosadi: xato turini tanlaydi, izoh va (bo'lsa) to'g'ri
 * javob taklifini yozadi. Xabar examinerlar boshlig'iga boradi.
 * Pastdan chiqadigan varaq — taymerni TO'XTATMAYDI (test davom etadi).
 *
 * Savolning o'zi, xodim bergan javob, bo'lim nomi va hokazolarni
 * server o'zi yozib oladi — bu yerdan faqat tur, izoh va taklif ketadi.
 * Javobda kalit (to'g'ri javob) qaytmaydi.
 */

export const ISSUE_KINDS: { key: string; label: string }[] = [
  { key: "answer_key", label: "Kalit xato" },
  { key: "two_answers", label: "Ikki javob to'g'ri" },
  { key: "typo", label: "Imlo-matn xato" },
  { key: "unclear", label: "Tushunarsiz" },
  { key: "script_audio", label: "Skript-audio" },
  { key: "other", label: "Boshqa" },
];

export function issueKindLabel(k: string | null | undefined): string {
  return ISSUE_KINDS.find((x) => x.key === k)?.label || k || "—";
}

export const ISSUE_STATUS: Record<string, { label: string; cls: string }> = {
  open: { label: "Ko'rib chiqilmoqda", cls: "bg-amber-50 text-amber-700" },
  fixed: { label: "Tuzatildi", cls: "bg-emerald-50 text-emerald-700" },
  rejected: { label: "Rad etildi", cls: "bg-slate-100 text-slate-600" },
  duplicate: { label: "Dublikat", cls: "bg-slate-100 text-slate-600" },
};

export function IssueStatusBadge({ status }: { status: string }) {
  const s = ISSUE_STATUS[status] || { label: status, cls: "bg-slate-100 text-slate-600" };
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-medium ${s.cls}`}>
      {s.label}
    </span>
  );
}

export type IssueTarget = {
  /** null — butun test (bo'lim) haqida */
  id: string | null;
  n?: number | null;
  q?: string | null;
};

export function MockIssueDialog({
  practiceId,
  contentKey,
  target,
  given,
  onClose,
  onSent,
}: {
  /** Xodimning urinishi (odatiy yo'l) */
  practiceId?: number | null;
  /** Urinishsiz xabar (examinerlar) — faqat practiceId bo'lmasa ketadi */
  contentKey?: string | null;
  target: IssueTarget;
  /** Xodimning o'z javobi — faqat ko'rsatish uchun (server o'zi yozadi) */
  given?: string | null;
  onClose: () => void;
  onSent?: (r: { id: number; status: string }, qid: string | null) => void;
}) {
  const [kind, setKind] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [suggested, setSuggested] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const needComment = kind === "other" || !target.id;
  const canSend = !!kind && (!needComment || comment.trim().length >= 3) && !busy;

  async function send() {
    if (!kind) return;
    setBusy(true);
    setErr(null);
    try {
      const body: Record<string, unknown> = {
        qid: target.id,
        kind,
        comment: comment.trim().slice(0, 1000),
        suggested: suggested.trim().slice(0, 300) || null,
      };
      if (practiceId) body.practice_id = practiceId;
      else body.content_key = contentKey;
      const r = await api.post<{ id: number; status: string }>("/mock-issues", body);
      pushToast("Rahmat — examinerga yuborildi", "success");
      onSent?.(r, target.id);
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-end sm:items-center justify-center"
         onClick={onClose}>
      <div
        className="bg-white w-full sm:max-w-lg rounded-t-2xl sm:rounded-2xl shadow-xl p-5 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <h2 className="font-bold text-slate-900">
              {target.id ? `${target.n ?? ""}-savolda xato bor` : "Test haqida xabar"}
            </h2>
            {target.q ? (
              <p className="text-xs text-slate-500 mt-0.5 line-clamp-2 whitespace-pre-line">{target.q}</p>
            ) : null}
            {given ? (
              <p className="text-xs text-slate-500 mt-1">
                Sizning javobingiz: <span className="font-medium text-slate-700">{given}</span>
              </p>
            ) : null}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600" title="Yopish">
            <X size={18} />
          </button>
        </div>

        <p className="text-xs font-medium text-slate-600 mb-1.5">Nima xato?</p>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {ISSUE_KINDS.map((k) => (
            <button
              key={k.key}
              type="button"
              onClick={() => setKind(k.key)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                kind === k.key
                  ? "border-brand-500 bg-brand-50 text-brand-800"
                  : "border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {k.label}
            </button>
          ))}
        </div>

        <label className="block text-xs font-medium text-slate-600 mb-1">
          Izoh{needComment ? "" : " (ixtiyoriy)"}
        </label>
        <textarea
          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          rows={3}
          maxLength={1000}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Masalan: matnda 'in 1998' deyilgan, kalitda 1989"
        />

        <label className="block text-xs font-medium text-slate-600 mb-1 mt-3">
          To'g'ri javob taklifi (ixtiyoriy)
        </label>
        <input
          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          maxLength={300}
          value={suggested}
          onChange={(e) => setSuggested(e.target.value)}
          placeholder="Masalan: B yoki 'library'"
        />

        {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
        <p className="text-[11px] text-slate-400 mt-3">
          Xabar examinerlar boshlig'iga boradi. Test vaqti to'xtamaydi.
        </p>
        <div className="flex gap-2 mt-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-xl border border-slate-300 py-2.5 text-sm text-slate-600"
          >
            Bekor qilish
          </button>
          <button
            type="button"
            disabled={!canSend}
            onClick={send}
            className="flex-1 rounded-xl bg-brand-600 hover:bg-brand-700 text-white py-2.5 text-sm font-semibold disabled:opacity-50"
          >
            {busy ? "Yuborilmoqda..." : "Yuborish"}
          </button>
        </div>
      </div>
    </div>
  );
}
