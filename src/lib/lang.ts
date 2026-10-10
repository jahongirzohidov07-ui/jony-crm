/** O'RGANILAYOTGAN TIL (2026-08-11, Jahongir: "glavniy ekranda qaysi
 * tilni o'rganayotgani bayrog'i tursin, bayroqqa bosganda boshqa
 * tillarga o'zgaradi va shu til lug'ati chiqadi").
 *
 * Botning o'zida 4 til kursi bor - hammasi yuklangan. Tanlov
 * localStorage'da, lug'at sahifalari shu tilga qarab ishlaydi.
 * Mashqlar til tanlovini saqlaydi. */
export const LANGS = [
  { code: "en", label: "Ingliz tili" },
  { code: "ru", label: "Rus tili" },
  { code: "de", label: "Nemis tili" },
  { code: "ko", label: "Koreys tili" },
];

export function getLang(): string {
  const v = localStorage.getItem("jonyos_lang") || "en";
  return LANGS.some((l) => l.code === v) ? v : "en";
}

export function setLang(code: string) {
  localStorage.setItem("jonyos_lang", code);
}

/** UI text for the selected learning language; game IDs remain compatible. */
export function learningText(text: string, lang: string): string {
  if (lang === "en") return text;
  const name = ({de:"Nemis",ru:"Rus",ko:"Koreys"} as Record<string,string>)[lang] || "Tanlangan";
  return text.replace(/Ingliz/g, name).replace(/ingliz/g, name.toLowerCase())
    .replace(/English/g, name + " tili").replace(/\bEN\b/g, lang.toUpperCase());
}
export function skillLabel(skill: string, fallback: string, lang: string): string {
  if (lang === "en") return fallback;
  const labels: Record<string,string> = {grammar:"Grammatika",vocabulary:"Lug‘at",reading:"O‘qish",listening:"Tinglash",writing:"Yozish",speaking:"Gapirish"};
  return labels[skill] || fallback;
}
