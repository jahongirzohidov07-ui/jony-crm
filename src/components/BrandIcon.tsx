import brandIconSrc from "../assets/brand-icon.png";

/**
 * Jony Academy logotipi belgisi (tuzatildi 2026-08-09).
 *
 * ILGARIGI XATOLIK: birinchi versiya rasm faylsiz, faqat suhbatga
 * joylashtirilgan tasvirni ko'rib, qo'lda SVG sifatida chizilgan edi
 * (3 ta oddiy o'ngga qaragan uchburchak, ranggi ham taxminiy). Jahongir
 * buni asl logotipdan farq qilishini aniq ko'rsatdi ("logosini
 * buzibsan"). Asl fayl (Ish stolidan "oq fon.jpg") olingandan keyin
 * ma'lum bo'ldiki, haqiqiy belgi ancha murakkab: chap tomonga
 * qaragan uchburchak + tik panel + oraliq + o'ngga qaragan uchburchak
 * + tik panel + kattaroq o'ngga qaragan uchburchak.
 *
 * Bu safar qo'lda qayta chizishga urinilmadi — buning o'rniga asl
 * fayldan ANIQ piksel bilan kesib olingan tasvir ishlatiladi
 * (src/assets/brand-icon.png, fon olib tashlangan, shaffof burchaklar
 * bilan). Rang ham fayldan aniq o'lchandi: #1A6FE4.
 */
export function BrandIcon({
  size = 32,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <img
      src={brandIconSrc}
      width={size}
      height={size}
      alt=""
      className={className}
      style={{ width: size, height: size, objectFit: "contain" }}
    />
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
      <BrandIcon size={iconSize} />
      <span className="font-extrabold tracking-tight text-slate-900 leading-none text-xl">
        JONY<br />ACADEMY
      </span>
    </div>
  );
}
