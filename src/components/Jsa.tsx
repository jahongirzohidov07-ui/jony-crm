import { BrandIcon } from "./BrandIcon";

/**
 * JONY STUDENT APP — umumiy kichik bo'laklar (2026-08-20).
 *
 * Jahongir to'liq dizayn to'plamini tashladi ("Jony Student appning
 * dizaynini toliq tashladim papkada 1ga 1 qilib ber") - barcha
 * ekranlar TO'Q KO'K temaga o'tdi. Shu faylda dizayndagi
 * takrorlanuvchi elementlar turadi: logo bloki, XP olti burchagi.
 */

/** To'q fonda ishlatiladigan ranglar - dizayndan pipetka bilan. */
export const JSA = {
  bg: "#0A1233",          // sahifa foni (to'q navy)
  card: "#111C4B",        // to'q karta
  cardBorder: "#223070",  // karta chegarasi
  nav: "#0C163E",         // pastki menyu
};

/** Chap yuqoridagi logo: ko'k kvadrat + JONY STUDENT APP. */
export function JsaLogo({ small = false }: { small?: boolean }) {
  return (
    <div className="flex items-center gap-2.5 min-w-0">
      <BrandIcon size={small ? 34 : 42} />
      <div className="leading-none">
        <p className={`font-extrabold tracking-tight text-white ${
          small ? "text-[15px]" : "text-[17px]"}`}>
          JONY
        </p>
        <p className={`font-extrabold tracking-tight text-white ${
          small ? "text-[15px]" : "text-[17px]"}`}>
          STUDENT APP
        </p>
      </div>
    </div>
  );
}

/** XP olti burchak nishoni (dizayndagi ko'k hexagon). */
export function XpHex({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path
        d="M12 1.5 21 6.75v10.5L12 22.5 3 17.25V6.75Z"
        fill="#1A6FE4" stroke="#5EA0F2" strokeWidth="1.2"
      />
      <text x="12" y="15.5" textAnchor="middle" fontSize="8.5"
            fontWeight="800" fill="#fff">XP</text>
    </svg>
  );
}

/** Yuqori o'ngdagi XP kartochkasi. */
export function XpPill({ value }: { value: number | string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-2xl px-3.5 py-2 border"
          style={{ background: "#101B4A", borderColor: "#2A3A7C" }}>
      <XpHex size={20} />
      <b className="text-white text-[15px]">{value}</b>
    </span>
  );
}
