import "./wordbank.css";
import { useEffect, useMemo, useRef, type CSSProperties } from "react";
import { StudentCoinIcon } from "../StudentIcon";
import type { WbAward } from "../../lib/wordbankApi";

/**
 * SO'Z BILISH — daraja tugaganda butun ekranli bayram (2026-10-16,
 * OWNER D5: "motivatsiya eng baland"). Coin miqdori serverning javob
 * tanasidan ("awards") olinadi — ekran o'zi hech narsa hisoblamaydi.
 * Konfetti faqat CSS; "harakatni kamaytirish" yoqilgan bo'lsa chiqmaydi.
 */
const COLORS = ["#fbbf24", "#34d399", "#60a5fa", "#f472b6", "#a78bfa", "#ffffff"];

export function BandCelebration({
  awards,
  onClose,
}: {
  awards: WbAward[];
  onClose: () => void;
}) {
  const btn = useRef<HTMLButtonElement | null>(null);
  useEffect(() => {
    btn.current?.focus();
  }, []);

  const pieces = useMemo(
    () =>
      Array.from({ length: 36 }, (_, i) => ({
        left: (i * 37) % 100,
        delay: ((i * 53) % 26) / 10,
        dx: (((i * 29) % 21) - 10) * 6,
        color: COLORS[i % COLORS.length],
      })),
    [],
  );

  if (!awards.length) return null;
  const coins = awards.reduce((s, a) => s + (a.coins || 0), 0);

  return (
    <div className="wb-celebrate" role="dialog" aria-modal="true"
         aria-labelledby="wb-celebrate-title">
      <div className="wb-confetti" aria-hidden="true">
        {pieces.map((p, i) => (
          <i
            key={i}
            style={{
              left: `${p.left}%`,
              background: p.color,
              animationDelay: `${p.delay}s`,
              "--wb-dx": `${p.dx}px`,
            } as CSSProperties}
          />
        ))}
      </div>

      <div className="wb-celebrate-card student-pattern rounded-3xl p-6 text-white"
           style={{ background: "linear-gradient(140deg,#f59e0b,#ea580c 55%,#db2777)" }}>
        <p className="text-[52px] leading-none" aria-hidden="true">🏆</p>
        <h2 id="wb-celebrate-title" className="text-[28px] font-extrabold mt-3 leading-tight">
          Tabriklaymiz!
        </h2>
        {awards.map((a) => (
          <p key={a.band} className="text-[17px] font-bold mt-2">
            Common {a.band}000 tugatildi
          </p>
        ))}
        <p className="text-[13px] text-white/90 mt-1.5 leading-snug">
          Darajadagi barcha so'zlar tasdiqlandi.
        </p>
        {coins > 0 ? (
          <p className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-white/20 px-4 py-2.5 text-[22px] font-extrabold">
            <StudentCoinIcon size={28} /> +{coins} coin
          </p>
        ) : (
          <p className="mt-4 text-[13px] text-white/90">
            Bu daraja uchun coin avval berilgan.
          </p>
        )}
        <button
          ref={btn}
          onClick={onClose}
          className="mt-5 w-full rounded-2xl bg-white text-orange-600 py-3.5 text-[16px] font-extrabold active:scale-[0.99] transition"
        >
          Davom etish
        </button>
      </div>
    </div>
  );
}
