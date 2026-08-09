/**
 * Jony Academy logotipi belgisi (2026-08-09).
 *
 * Jahongir yubordi rasm — ko'k dumaloq kvadrat + 3 ta oq o'ngga
 * qaragan uchburchak (o'sib boruvchi o'lcham). Rasm fayl sifatida
 * emas, suhbatga to'g'ridan-to'g'ri joylashtirilgan rasm sifatida
 * kelgani uchun asl pikselларни chiqarib olib bo'lmadi — shuning
 * uchun bu SVG qo'lda, ko'rgan rasmga qarab qayta chizilgan aniq
 * nusxa (yaqin, lekin 100% bir xil emas). Agar Jahongir asl faylni
 * (SVG yoki katta PNG) yuborsa, buni bir zumda asl fayl bilan
 * almashtirish mumkin — barcha chaqiruv joylari shu komponent
 * orqali ishlaydi.
 */
export function BrandIcon({
  size = 32,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      className={className}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="7.04" fill="#2563eb" />
      <polygon points="8.75,13.188 14.375,16 8.75,18.812" fill="#ffffff" />
      <polygon points="13.438,11.312 20,16 13.438,20.688" fill="#ffffff" />
      <polygon points="18.75,9 26.875,16 18.75,23" fill="#ffffff" />
    </svg>
  );
}

/** Ikonka + "JONY ACADEMY" yozuvi — login sahifasi kabi to'liq
 * brendlash kerak bo'lgan joylar uchun. */
export function BrandLockup({
  iconSize = 48,
  className = "",
}: {
  iconSize?: number;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div
        className="rounded-xl overflow-hidden shrink-0"
        style={{ width: iconSize, height: iconSize }}
      >
        <BrandIcon size={iconSize} />
      </div>
      <span className="font-extrabold tracking-tight text-slate-900 leading-none text-xl">
        JONY<br />ACADEMY
      </span>
    </div>
  );
}
