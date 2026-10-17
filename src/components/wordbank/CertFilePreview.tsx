import { useEffect, useState } from "react";
import { Download, ExternalLink } from "lucide-react";
import { fetchCertFile } from "../../lib/wordbankApi";

/**
 * SERTIFIKAT FAYLINI KO'RSATISH (2026-10-17).
 *
 * Oddiy <img src="/api/..."> ishlamaydi — server tokenni sarlavhada
 * so'raydi. Fayl token bilan olinadi, blob URL qilinadi va komponent
 * yopilganda (yoki boshqa fayl tanlanganda) URL darhol bo'shatiladi.
 *
 * PDF (2026-10-17, review): sandbox'li iframe Chromium'da (Chrome, Edge,
 * JonyOS ilovasi) BO'SH oyna bo'lib qolardi — brauzer PDF ko'rsatgichini
 * sandbox ichida ishga tushirmaydi. Endi <object type="application/pdf">:
 * blob turi serverdagi sehrli baytlardan (application/pdf), uni
 * brauzerning o'z PDF ko'rsatgichi ochadi, sahifa skripti sifatida
 * ishlamaydi. Ko'rsata olmaydigan brauzerda (masalan Android) ichidagi
 * "Yangi oynada ochish" tugmasi chiqadi.
 */
export function CertFilePreview({
  path,
  mime,
  name,
  tone = "light",
}: {
  /** `/wordbank/certs/mine/${id}/file` yoki `/wordbank/certs/${id}/file` */
  path: string;
  mime?: string | null;
  /** Yuklab olinadigan fayl nomi (kengaytmasiz) */
  name?: string;
  tone?: "light" | "dark";
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [type, setType] = useState<string>(mime || "");
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    let made: string | null = null;
    setUrl(null);
    setErr("");
    fetchCertFile(path)
      .then((b) => {
        if (!alive) return;
        made = URL.createObjectURL(b);
        setType(b.type || mime || "");
        setUrl(made);
      })
      .catch((e) => {
        if (alive) setErr(e instanceof Error ? e.message : "Faylni ochib bo'lmadi");
      });
    return () => {
      alive = false;
      if (made) URL.revokeObjectURL(made);
    };
  }, [path, mime]);

  const muted = tone === "dark" ? "text-slate-400" : "text-slate-500";
  if (err) return <p className="text-[12px] text-red-500">{err}</p>;
  if (!url)
    return (
      <div className={`h-40 rounded-xl flex items-center justify-center text-[12px] ${muted} ${
        tone === "dark" ? "bg-white/5" : "bg-slate-100"}`}>
        Fayl yuklanmoqda…
      </div>
    );

  const isPdf = type.includes("pdf");
  const ext = isPdf ? "pdf" : type.includes("png") ? "png" : type.includes("webp") ? "webp" : "jpg";
  const link = `inline-flex items-center gap-1 text-[12px] font-semibold min-h-[36px] ${
    tone === "dark" ? "text-sky-300" : "text-brand-600"}`;

  return (
    <div>
      {isPdf ? (
        <object
          data={url}
          type="application/pdf"
          aria-label="Sertifikat (PDF)"
          className="w-full h-[420px] rounded-xl border border-slate-200 bg-white"
        >
          <div className={`h-40 rounded-xl flex flex-col items-center justify-center gap-2 text-[12px] ${muted} ${
            tone === "dark" ? "bg-white/5" : "bg-slate-100"}`}>
            <span>PDF fayl — bu yerda ko'rsatib bo'lmadi</span>
            <a href={url} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-1 min-h-[40px] px-4 rounded-xl bg-brand-600 text-white font-semibold">
              <ExternalLink size={13} /> PDF — Yangi oynada ochish
            </a>
          </div>
        </object>
      ) : (
        <img
          src={url}
          alt="Sertifikat"
          className="w-full max-h-[480px] object-contain rounded-xl bg-slate-100"
        />
      )}
      <div className="flex flex-wrap gap-x-4">
        <a href={url} target="_blank" rel="noopener noreferrer" className={link}>
          <ExternalLink size={13} /> Yangi oynada ochish
        </a>
        <a href={url} download={`${name || "sertifikat"}.${ext}`} className={link}>
          <Download size={13} /> Yuklab olish
        </a>
      </div>
    </div>
  );
}
