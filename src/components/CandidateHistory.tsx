import { History, X } from "lucide-react";
import type { CandidateHistoryRow } from "../lib/api";
import { formatDate } from "../lib/format";
import { formatPhone } from "./PhoneInput";

/**
 * TAKRORIY NOMZOD (2026-09-16, taklif #1): shu odamning avvalgi
 * arizalari — qachon, qaysi lavozimga, qanday tugagan va nega rad
 * etilgan. Server odamni telefon (yoki telefon bo'lmasa ism) bo'yicha
 * taniydi.
 */

const STAGE_TONE: Record<string, string> = {
  hired: "bg-emerald-50 text-emerald-700",
  rejected: "bg-red-50 text-red-700",
};

export function CandidateHistoryList({
  rows, onOpen, onMerge,
}: {
  rows: CandidateHistoryRow[];
  onOpen?: (id: number) => void;
  onMerge?: (row: CandidateHistoryRow) => void;
}) {
  return (
    <div className="divide-y divide-slate-100">
      {rows.map((h) => (
        <div key={h.id} className="py-2 flex flex-wrap items-start gap-x-3 gap-y-1">
          <div className="flex-1 min-w-[200px]">
            <p className="text-sm text-slate-800">
              <span className="font-medium">
                {h.created_at ? formatDate(h.created_at) : "—"}
              </span>
              {" · "}
              {[h.role_label, h.subject].filter(Boolean).join(" · ") || "lavozim yo'q"}
              {h.vacancy ? ` · ${h.vacancy}` : ""}
              {h.branch ? ` · ${h.branch}` : ""}
            </p>
            <p className="text-xs text-slate-500">
              <span
                className={`inline-block px-1.5 py-0.5 rounded mr-1.5 ${
                  STAGE_TONE[h.stage] || "bg-slate-100 text-slate-600"
                }`}
              >
                {h.stage_label}
              </span>
              {h.reject_reason && <>Sabab: {h.reject_reason}</>}
              {h.hired_date && <>Ishga olingan: {formatDate(h.hired_date)}</>}
            </p>
            <p className="text-[11px] text-slate-400">
              {h.full_name}
              {h.phone ? ` · ${formatPhone(h.phone)}` : ""}
            </p>
          </div>
          <div className="flex gap-1.5">
            {onOpen && (
              <button
                onClick={() => onOpen(h.id)}
                className="text-xs px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
              >
                Ochish
              </button>
            )}
            {onMerge && (
              <button
                onClick={() => onMerge(h)}
                title="Bu arizani joriy kartaga qo'shish (bitta odam bo'lsa)"
                className="text-xs px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 hover:bg-amber-100"
              >
                Shu kartaga birlashtirish
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/** Yangi nomzod kiritilayotganda "bu odam avval ham kelgan" oynasi. */
export function DuplicateCandidateDialog({
  rows, onOpen, onForce, onClose,
}: {
  rows: CandidateHistoryRow[];
  onOpen: (id: number) => void;
  onForce: () => void;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-[60] px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-5 max-h-[88vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <History size={17} className="text-amber-600" />
            Bu odam avval ham ariza bergan
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-600 mb-2">
          Telefon (yoki ism) bo'yicha {rows.length} ta avvalgi yozuv topildi.
          Eskisini ochib, shu kartada davom ettirish tavsiya etiladi.
        </p>
        <CandidateHistoryList rows={rows} onOpen={onOpen} />
        <div className="flex flex-wrap gap-2 justify-end mt-4">
          <button
            onClick={onClose}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor qilish
          </button>
          <button
            onClick={onForce}
            className="px-3 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium"
          >
            Baribir yangi nomzod qo'shish
          </button>
        </div>
      </div>
    </div>
  );
}
