import "./wordbank.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";

/**
 * SO'Z BILISH — har savol uchun taymer (2026-10-16, DESIGN §2: tanlash
 * 15 s, yozib topish 30 s; vaqt tugasa — server "o'tkazib yuborildi" deb
 * yozadi, so'z holatiga tegmaydi).
 *
 * runKey o'zgarganda (yangi savol) sanoq qaytadan boshlanadi.
 * running=false — sanoq to'xtaydi (javob yuborilayotganda/berilgandan
 * keyin). elapsedMs() — savol YURIB TURGAN vaqt (serverga "ms" sifatida
 * boradi; server baribir o'z oralig'i bilan solishtiradi).
 *
 * 2026-10-16 (review): sanoq faqat taymer yurib, sahifa KO'RINIB turganda
 * o'tadi. Avval to'xtash (qayta yuborish, tasdiqlash oynasi) yoki ilova
 * fonga o'tgan vaqt ham hisoblanardi: "Davom etish"dan keyin yoki boshqa
 * ilovadan qaytganda savol darhol "vaqt tugadi" bo'lib qolardi. Endi
 * to'xtagan vaqt chiqarib tashlanadi va sanoq qolgan joyidan davom etadi.
 */
export function useItemTimer(
  limitSec: number,
  runKey: string | number,
  running: boolean,
  onTimeout: () => void,
) {
  const limitMs = limitSec * 1000;
  const [left, setLeft] = useState(limitMs);
  const [visible, setVisible] = useState(
    () => typeof document === "undefined" || document.visibilityState !== "hidden",
  );
  const used = useRef(0); // shu savolda yig'ilgan (yurgan) vaqt
  const since = useRef<number | null>(null); // joriy yurish boshlangan payt
  const cb = useRef(onTimeout);
  cb.current = onTimeout;

  const elapsedNow = useCallback(
    () => used.current + (since.current == null ? 0 : performance.now() - since.current),
    [],
  );

  useEffect(() => {
    const on = () => setVisible(document.visibilityState !== "hidden");
    document.addEventListener("visibilitychange", on);
    return () => document.removeEventListener("visibilitychange", on);
  }, []);

  // Yangi savol — sanoq noldan (oldingi savolning yurishi quyidagi
  // effekt tozalanishida yopiladi, u bundan OLDIN ishlaydi).
  useEffect(() => {
    used.current = 0;
    since.current = null;
    setLeft(limitMs);
  }, [runKey, limitMs]);

  const active = running && visible;
  useEffect(() => {
    if (!active) return;
    since.current = performance.now();
    const id = setInterval(() => {
      const l = Math.max(0, limitMs - elapsedNow());
      setLeft(l);
      if (l <= 0) {
        clearInterval(id);
        cb.current();
      }
    }, 200);
    return () => {
      clearInterval(id);
      if (since.current != null) {
        used.current += performance.now() - since.current;
        since.current = null;
      }
    };
  }, [active, runKey, limitMs, elapsedNow]);

  const elapsedMs = useCallback(() => Math.round(elapsedNow()), [elapsedNow]);
  return { left, limitMs, elapsedMs };
}

export function TimerBar({ left, limitMs }: { left: number; limitMs: number }) {
  const pct = limitMs ? Math.max(0, Math.min(100, (left / limitMs) * 100)) : 0;
  const secs = Math.ceil(left / 1000);
  const color = secs <= 5 ? "#ef4444" : secs <= 10 ? "#f59e0b" : "#1a6fe4";
  return (
    <div className="flex items-center gap-2">
      <div className="wb-timer flex-1" aria-hidden="true">
        <div style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="inline-flex items-center gap-1 text-[12px] font-bold tabular-nums w-11 justify-end shrink-0"
            style={{ color }} aria-label={`${secs} soniya qoldi`}>
        <Clock size={12} /> {secs}s
      </span>
    </div>
  );
}
