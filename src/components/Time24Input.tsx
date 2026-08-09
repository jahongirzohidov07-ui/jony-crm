/**
 * Har doim 24 soatlik, AM/PM UMUMAN YO'Q — qurilma yoki brauzerdan
 * qat'i nazar (2026-08-09).
 *
 * Nega native <input type="time"> ishlatilmaydi: Android'da bu
 * input OS'ning O'Z vaqt tanlash dialogini ochadi (Chrome emas,
 * qurilmaning o'zi chizadi) — va o'sha dialog 12/24 soatni
 * QURILMA SOZLAMASIGA qarab tanlaydi, sahifaning `lang` atributi
 * unga UMUMAN ta'sir qilmaydi. Avval `lang="en-GB"` bilan tuzatishga
 * urinildi (bu desktop Chrome'da ishlaydi), lekin Jahongir skrinshot
 * bilan tasdiqladi: Android'da hech narsa o'zgarmadi. Shuning uchun
 * vaqtni TO'LIQ o'zimiz chizamiz — hech qanday native OS dialogi
 * ishga tushmaydi, demak AM/PM chiqishning iloji yo'q.
 *
 * Qiymat va onChange shakli native input bilan BIR XIL ("HH:MM"
 * satr, e.target.value orqali) — shuning uchun barcha chaqiruv
 * joylarida faqat <input type="time" .../> ni <Time24Input .../>
 * ga almashtirish yetarli, boshqa hech narsa o'zgarmaydi.
 */
export function Time24Input({
  value,
  onChange,
  className = "",
  disabled = false,
}: {
  value: string;
  onChange: (e: { target: { value: string } }) => void;
  className?: string;
  disabled?: boolean;
}) {
  const [hRaw, mRaw] = (value || "00:00").split(":");
  const h = /^\d{1,2}$/.test(hRaw || "") ? hRaw.padStart(2, "0") : "00";
  const m = /^\d{1,2}$/.test(mRaw || "") ? mRaw.padStart(2, "0") : "00";

  function set(newH: string, newM: string) {
    onChange({ target: { value: `${newH}:${newM}` } });
  }

  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0"));
  const minutes = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0"));

  return (
    <span
      className={`inline-flex items-center justify-center gap-0.5 ${className}`}
    >
      <select
        aria-label="Soat"
        value={h}
        disabled={disabled}
        onChange={(e) => set(e.target.value, m)}
        className="bg-transparent outline-none border-0 p-0 text-inherit disabled:opacity-50"
      >
        {hours.map((x) => (
          <option key={x} value={x}>
            {x}
          </option>
        ))}
      </select>
      <span className="text-slate-400">:</span>
      <select
        aria-label="Daqiqa"
        value={m}
        disabled={disabled}
        onChange={(e) => set(h, e.target.value)}
        className="bg-transparent outline-none border-0 p-0 text-inherit disabled:opacity-50"
      >
        {minutes.map((x) => (
          <option key={x} value={x}>
            {x}
          </option>
        ))}
      </select>
    </span>
  );
}
