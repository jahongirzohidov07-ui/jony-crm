/** O'RGANILAYOTGAN TIL (2026-08-11, Jahongir: "glavniy ekranda qaysi
 * tilni o'rganayotgani bayrog'i tursin, bayroqqa bosganda boshqa
 * tillarga o'zgaradi va shu til lug'ati chiqadi").
 *
 * Botning o'zida 4 til kursi bor - hammasi yuklangan. Tanlov
 * localStorage'da, lug'at sahifalari shu tilga qarab ishlaydi.
 * Grammatika hozircha faqat ingliz tilida. */
export const LANGS = [
  { code: "en", flag: "🇬🇧", label: "Ingliz tili" },
  { code: "ru", flag: "🇷🇺", label: "Rus tili" },
  { code: "de", flag: "🇩🇪", label: "Nemis tili" },
  { code: "ko", flag: "🇰🇷", label: "Koreys tili" },
];

export function getLang(): string {
  const v = localStorage.getItem("jonyos_lang") || "en";
  return LANGS.some((l) => l.code === v) ? v : "en";
}

export function setLang(code: string) {
  localStorage.setItem("jonyos_lang", code);
}
