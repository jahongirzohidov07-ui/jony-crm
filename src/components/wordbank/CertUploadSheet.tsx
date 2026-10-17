import { useEffect, useRef, useState } from "react";
import { FileText, FileUp, Image as ImageIcon, X } from "lucide-react";
import { CERT_ACCEPT, uploadMyCert, type CertExamType } from "../../lib/wordbankApi";
import {
  draftToForm,
  emptyDraft,
  fmtBytes,
  prepareCertFile,
  type CertDraft,
} from "../../lib/wordbankUi";
import { CertFields } from "./CertFields";

/**
 * "SERTIFIKAT YUKLASH" — pastdan chiqadigan oyna (2026-10-17, OWNER D3).
 *
 * O'quvchi imtihon turi, natija, sana va faylni kiritadi. Yuborilgach
 * oyna YOPILADI va ball hech qayerda qaytarib ko'rsatilmaydi — o'quvchi
 * faqat "Yuklandi — tekshirilmoqda" holatini ko'radi; natija xodim
 * tasdiqlagandan keyin chiqadi. Rasm yuborishdan oldin kichraytiriladi
 * (EXIF ham o'chadi), PDF — 3 MB gacha o'zicha.
 */
export function CertUploadSheet({
  initialType,
  onClose,
  onDone,
}: {
  /** Rad etilganini qayta yuklashda — o'sha imtihon turi */
  initialType?: CertExamType;
  onClose: () => void;
  onDone: () => void;
}) {
  const [draft, setDraft] = useState<CertDraft>(() => emptyDraft(initialType || "ielts"));
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const panel = useRef<HTMLDivElement>(null);
  const closeRef = useRef(() => {});
  closeRef.current = () => {
    if (!busy) onClose();
  };

  // Orqa sahifa aylanmasin; Esc — yopish (faqat bir marta ulanadi,
  // aks holda har qayta chizishda fokus maydondan sakrab ketardi)
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeRef.current();
    };
    window.addEventListener("keydown", onKey);
    panel.current?.focus();
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  async function submit() {
    if (busy) return;
    setErr("");
    const v = draftToForm(draft);
    if (v.error !== null) {
      setErr(v.error);
      return;
    }
    if (!file) {
      setErr("Sertifikat faylini tanlang (rasm yoki PDF)");
      return;
    }
    setBusy(true);
    try {
      const prepared = await prepareCertFile(file);
      await uploadMyCert(v.form, prepared.blob, prepared.name);
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Yuklab bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  const isPdf = !!file && (file.type === "application/pdf" || /\.pdf$/i.test(file.name));

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-end"
      onClick={() => !busy && onClose()}
    >
      <div
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cert-sheet-title"
        className="w-full max-w-md mx-auto bg-white text-slate-900 rounded-t-3xl px-4 pt-4 max-h-[92dvh] overflow-y-auto outline-none"
        style={{ paddingBottom: "calc(20px + env(safe-area-inset-bottom, 0px))" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-slate-200" aria-hidden="true" />
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <h2 id="cert-sheet-title" className="text-[19px] font-extrabold text-slate-900">
              Sertifikat yuklash
            </h2>
            <p className="text-[12px] text-slate-500 mt-0.5 leading-snug">
              Natija ustoz yoki rahbariyat tekshirib tasdiqlagandan keyin
              profilingizda ✓ belgi bilan chiqadi.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            aria-label="Yopish"
            className="w-11 h-11 -mr-1 rounded-xl flex items-center justify-center text-slate-500 shrink-0"
          >
            <X size={20} />
          </button>
        </div>

        <div className="mt-3">
          <CertFields value={draft} onChange={setDraft} disabled={busy} idPrefix="up" />
        </div>

        <div className="mt-3">
          <p className="block text-[12px] font-semibold text-slate-600 mb-1">Fayl</p>
          <label
            className={`flex items-center gap-3 rounded-2xl border-2 border-dashed px-3 py-3 min-h-[56px] cursor-pointer ${
              file ? "border-emerald-300 bg-emerald-50/50" : "border-slate-300"}`}
          >
            <span className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0 text-slate-500">
              {file ? (isPdf ? <FileText size={20} /> : <ImageIcon size={20} />) : <FileUp size={20} />}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[14px] font-bold text-slate-800 truncate">
                {file ? file.name : "Rasm yoki PDF tanlang"}
              </span>
              <span className="block text-[11.5px] text-slate-500">
                {file
                  ? isPdf ? `PDF · ${fmtBytes(file.size)}` : `Rasm · ${fmtBytes(file.size)} · yuborishda kichraytiriladi`
                  : "JPG, PNG, WEBP yoki PDF (3 MB gacha)"}
              </span>
            </span>
            <input
              type="file"
              accept={CERT_ACCEPT}
              className="sr-only"
              disabled={busy}
              onChange={(e) => {
                setErr("");
                setFile(e.target.files?.[0] || null);
              }}
            />
          </label>
          <p className="text-[11px] text-slate-500 mt-1.5 leading-snug">
            Fayldagi ism-familiya va natija aniq o'qilsin. Boshqa odamning
            sertifikatini yuklash taqiqlanadi.
          </p>
        </div>

        {err && (
          <p role="alert" className="mt-3 rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-[13px] text-red-700">
            {err}
          </p>
        )}

        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className="mt-4 w-full min-h-[50px] rounded-2xl bg-brand-600 text-white text-[16px] font-extrabold disabled:opacity-60"
        >
          {busy ? "Yuklanmoqda…" : "Yuklash"}
        </button>
      </div>
    </div>
  );
}
