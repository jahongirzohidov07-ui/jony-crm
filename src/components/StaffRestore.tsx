import { useState } from "react";
import { X, RotateCcw } from "lucide-react";
import { api, ApiError } from "../lib/api";

/**
 * KETGAN XODIMNI QAYTARISH (2026-10-06, Jahongir: "arxivdagi ketgan
 * xodimlarni akkauntlarini tiklash qaytarishni ham qo'shib ber hrga").
 *
 * HR "Ketganlar arxivi" va Arxiv → Xodimlar bir xil oynani ochadi.
 * "Qizil yo'lak" bo'lsa server ogohlantiradi — tasdiq bilan qaytadi.
 */
export type RestoreTarget = {
  id: number;            // user id (karta bo'lsa — manfiy)
  kind: string;          // "user" | "teacher"
  teacher_id?: number | null;
  full_name: string;
  username?: string | null;
  role_label?: string | null;
  exit_type?: string | null;
  exit_label?: string | null;
};

export function StaffRestoreModal({ row, onClose, onDone }: {
  row: RestoreTarget;
  onClose: () => void;
  onDone: () => void;
}) {
  const isCard = row.kind === "teacher";
  const [reset, setReset] = useState(false);
  const [note, setNote] = useState("");
  const [warn, setWarn] = useState<string | null>(
    row.exit_type === "red"
      ? "Bu xodim \"Qizil yo'lak\"da — qayta ishga olinmaydi deb belgilangan." : null);
  const [force, setForce] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<{ login?: string; reset: boolean } | null>(null);

  async function save() {
    setBusy(true);
    setErr("");
    try {
      if (isCard) {
        await api.post(`/staff/teacher-card/${row.teacher_id ?? -row.id}/restore`, {});
        setDone({ reset: false });
      } else {
        const r = await api.post<{ login: string; password_reset: boolean }>(
          `/staff/${row.id}/restore`,
          { reset_password: reset, force, note: note.trim() || null });
        setDone({ login: r.login, reset: r.password_reset });
      }
      onDone();
    } catch (e) {
      if (e instanceof ApiError && e.canForce) {
        setWarn(e.message);
        setForce(true);
      } else {
        setErr(e instanceof Error ? e.message : "Xatolik");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-start justify-center p-4 pt-16 overflow-y-auto"
         onClick={onClose}>
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <RotateCcw size={17} className="text-brand-600" /> Ishga qaytarish
          </h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <p className="text-sm text-slate-700 mb-4">
          <b>{row.full_name}</b>
          {row.role_label ? <span className="text-slate-500"> · {row.role_label}</span> : null}
          {row.exit_label ? <span className="text-slate-500"> · {row.exit_label}</span> : null}
        </p>

        {done ? (
          <div className="space-y-3">
            <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
              {row.full_name} faol xodimlarga qaytarildi.
            </p>
            {!isCard && (
              <p className="text-sm text-slate-700 bg-slate-50 border border-slate-100 rounded-lg px-3 py-2">
                Login: <b>{done.login}</b>
                <br />
                {done.reset
                  ? "Parol standart parolga qaytarildi — birinchi kirishda tizim yangi parol qo'yishni so'raydi."
                  : "Parol o'zgarmadi — eski paroli bilan kiradi."}
              </p>
            )}
            <div className="text-right">
              <button onClick={onClose}
                      className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium">
                Yopish
              </button>
            </div>
          </div>
        ) : (
          <>
            <ul className="text-xs text-slate-500 list-disc ml-5 mb-4 space-y-1">
              <li>{isCard ? "Ustoz kartasi faol bo'ladi." : "Akkaunt ochiladi — xodim yana tizimga kira oladi."}</li>
              <li>Ustoz/support kartasi bo'lsa — u ham qaytadi.</li>
              <li>Ketish sababi va chiqish suhbati tarixda qoladi.</li>
              <li>Guruh va lavozim biriktirishlari qaytmaydi — kerak bo'lsa qayta beriladi.</li>
            </ul>

            {!isCard && (
              <>
                <label className="flex items-start gap-2 text-sm text-slate-700 cursor-pointer mb-3">
                  <input type="checkbox" checked={reset} onChange={(e) => setReset(e.target.checked)} className="mt-0.5" />
                  <span>
                    Parolni tiklash
                    <span className="block text-[11px] text-slate-400">
                      Parol standartga qaytadi, xodim kirgach o'zi yangisini qo'yadi.
                      Paroli esdan chiqqan bo'lsa belgilang.
                    </span>
                  </span>
                </label>
                <label className="block text-xs text-slate-500 mb-1">Izoh (ixtiyoriy)</label>
                <input value={note} onChange={(e) => setNote(e.target.value)}
                       placeholder="Masalan: qayta ishga olindi, 1-oktabrdan"
                       className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm mb-3" />
              </>
            )}

            {warn && (
              <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
                {warn}
                {!force && !isCard && (
                  <label className="flex items-center gap-2 mt-2 text-red-800 cursor-pointer">
                    <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} />
                    Baribir qaytaraman
                  </label>
                )}
              </p>
            )}
            {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{err}</p>}

            <button onClick={save} disabled={busy || (!!warn && !force && !isCard)}
                    className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-50">
              {busy ? "Qaytarilmoqda..." : force ? "Baribir qaytarish" : "Ishga qaytarish"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
