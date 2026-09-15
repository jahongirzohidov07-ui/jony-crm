import { StudentIcon } from "./StudentIcon";
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
  bg: "#020d38",          // sahifa foni (to'q navy)
  card: "#0c2258",        // to'q karta
  cardBorder: "#35538c",  // karta chegarasi
  nav: "#0C163E",         // pastki menyu
};

/** Chap yuqoridagi logo: ko'k kvadrat + JONY STUDENT APP. */
export function JsaLogo({ small = false }: { small?: boolean }) {
  return (
    <div className="student-logo flex items-center gap-2.5 min-w-0">
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
  return <StudentIcon name="xp" size={size} />;
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
