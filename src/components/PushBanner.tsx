import { useEffect, useState } from "react";
import { BellRing } from "lucide-react";
import { ensurePush, pushPermission } from "../lib/push";
import { JSA } from "./Jsa";

/**
 * "BILDIRISHNOMALARNI YOQING" (2026-10-03). Jony Student bosh sahifasi.
 * Ruxsat berilgan bo'lsa — jim obunani yangilaydi, hech narsa
 * ko'rsatmaydi. Hali so'ralmagan bo'lsa — karta (brauzer ruxsatni faqat
 * tugma bosilganda so'raydi).
 */
export function PushBanner() {
  const [perm, setPerm] = useState(pushPermission());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (perm === "granted") ensurePush(false).catch(() => {});
  }, [perm]);

  if (perm !== "default") return null;
  return (
    <div className="rounded-2xl border p-4 flex items-center gap-3"
      style={{ background: JSA.card, borderColor: JSA.cardBorder }}>
      <BellRing size={22} className="text-amber-300 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white">Imtihon xabarlari</p>
        <p className="text-xs text-white/70">
          Imtihon ochilsa telefoningizga darrov xabar kelsin
        </p>
      </div>
      <button
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          try {
            await ensurePush(true);
          } catch {
            /* ruxsat berilmadi yoki tarmoq — karta qoladi */
          }
          setPerm(pushPermission());
          setBusy(false);
        }}
        className="rounded-xl bg-brand-600 text-white text-sm font-semibold px-4 py-2 shrink-0 disabled:opacity-50"
      >
        Yoqish
      </button>
    </div>
  );
}
