import { useEffect, useRef, useState } from "react";
import { Paperclip, Trash2, Upload, X, FileText } from "lucide-react";
import { api, type AttachmentMeta, type AttachmentData } from "../lib/api";

const KINDS = [
  { key: "photo", label: "Rasm" },
  { key: "certificate", label: "Sertifikat" },
  { key: "resume", label: "Rezyume" },
  { key: "document", label: "Hujjat" },
  { key: "other", label: "Boshqa" },
];

function human(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

/**
 * Fayl biriktirish. Fayl bazada saqlanadi, shuning uchun hajm 3 MB
 * bilan cheklangan — rasm va sertifikat uchun yetarli.
 */
export function Attachments({
  entity,
  entityId,
  kinds = KINDS,
  compact = false,
}: {
  entity: string;
  entityId: number;
  kinds?: { key: string; label: string }[];
  compact?: boolean;
}) {
  const [rows, setRows] = useState<AttachmentMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [kind, setKind] = useState(kinds[0]?.key ?? "document");
  const [preview, setPreview] = useState<AttachmentData | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function load() {
    setLoading(true);
    api
      .get<AttachmentMeta[]>(`/attachments?entity=${entity}&entity_id=${entityId}`)
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }
  useEffect(load, [entity, entityId]);

  async function upload(file: File) {
    setBusy(true);
    setErr("");
    try {
      let data: string = await new Promise((resolve, reject) => {
        const r = new FileReader();
        r.onload = () => resolve(String(r.result));
        r.onerror = () => reject(new Error("Faylni o'qib bo'lmadi"));
        r.readAsDataURL(file);
      });
      // Rasmlarni yuklashdan OLDIN siqamiz: telefon kamerasidan
      // kelgan 5-10 MB rasm bazani shishirib, sahifani sekinlashtiradi.
      // 1200px va JPEG 82% — hujjat/portret uchun bemalol yetadi.
      if (file.type.startsWith("image/") && file.size > 300 * 1024) {
        try {
          data = await compressImage(data, 1200, 0.82);
        } catch {
          /* siqilmasa asl holicha ketadi */
        }
      }
      await api.post("/attachments", {
        entity, entity_id: entityId, kind,
        filename: file.name, mime: file.type, data,
      });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Yuklab bo'lmadi");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function open(a: AttachmentMeta) {
    const full = await api.get<AttachmentData>(`/attachments/${a.id}`);
    setPreview(full);
  }

  async function remove(a: AttachmentMeta) {
    if (!confirm(`"${a.filename}" o'chirilsinmi?`)) return;
    await api.delete(`/attachments/${a.id}`);
    load();
  }

  const photo = rows.find((r) => r.kind === "photo" && r.is_image);

  return (
    <div>
      {!compact && (
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
          >
            {kinds.map((k) => (
              <option key={k.key} value={k.key}>
                {k.label}
              </option>
            ))}
          </select>
          <input
            ref={fileRef}
            type="file"
            accept="image/*,.pdf,.doc,.docx"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload(f);
            }}
            className="hidden"
            id={`file-${entity}-${entityId}`}
          />
          <label
            htmlFor={`file-${entity}-${entityId}`}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-brand-300 cursor-pointer"
          >
            <Upload size={14} />
            {busy ? "Yuklanmoqda..." : "Fayl tanlash"}
          </label>
          <span className="text-xs text-slate-400">3 MB gacha</span>
        </div>
      )}

      {err && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
          {err}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-slate-400">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400">Fayl biriktirilmagan</p>
      ) : (
        <div className="space-y-1.5">
          {rows.map((a) => (
            <div
              key={a.id}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-white"
            >
              {a.is_image ? (
                <Paperclip size={14} className="text-slate-400 shrink-0" />
              ) : (
                <FileText size={14} className="text-slate-400 shrink-0" />
              )}
              <button
                onClick={() => open(a)}
                className="text-sm text-slate-800 hover:text-brand-700 truncate flex-1 text-left"
              >
                {a.filename || "fayl"}
              </button>
              <span className="text-xs text-slate-400 shrink-0">
                {a.kind_label} · {human(a.size)}
              </span>
              <button
                onClick={() => remove(a)}
                className="p-1 text-slate-400 hover:text-red-600 shrink-0"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      )}

      {preview && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          onClick={() => setPreview(null)}
        >
          <div
            className="bg-white rounded-xl max-w-2xl w-full max-h-[88vh] overflow-auto p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-medium text-slate-800">
                {preview.filename}
              </p>
              <button
                onClick={() => setPreview(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X size={18} />
              </button>
            </div>
            {preview.mime?.startsWith("image/") ? (
              <img
                src={`data:${preview.mime};base64,${preview.data}`}
                alt={preview.filename || ""}
                className="max-w-full rounded-lg"
              />
            ) : (
              <a
                href={`data:${preview.mime || "application/octet-stream"};base64,${preview.data}`}
                download={preview.filename || "fayl"}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 text-white text-sm"
              >
                <Upload size={14} className="rotate-180" /> Yuklab olish
              </a>
            )}
          </div>
        </div>
      )}

      {compact && photo && (
        <img
          src=""
          alt=""
          className="hidden"
          onError={(e) => (e.currentTarget.style.display = "none")}
        />
      )}
    </div>
  );
}

/** Rasmni brauzerda kichraytirib JPEG'ga siqadi (eng uzun tomoni
 *  maxSide px). Baza va trafik uchun 10 barobargacha tejaydi. */
function compressImage(dataUrl: string, maxSide: number,
                       quality: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const w = Math.round(img.width * scale);
      const h = Math.round(img.height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) { reject(new Error("canvas yo'q")); return; }
      ctx.drawImage(img, 0, 0, w, h);
      resolve(canvas.toDataURL("image/jpeg", quality));
    };
    img.onerror = () => reject(new Error("rasm o'qilmadi"));
    img.src = dataUrl;
  });
}
