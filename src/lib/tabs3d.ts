/* RANGLI 3D TABLAR (2026-10-22, Jahongir: "faqat hr bolimmi qolgani
   rangsiz va 3d emasmi" -> "Barcha tablar"). HR'dagi guruh tugmalari
   uslubi butun tizimdagi tab qatorlari uchun bitta joyda.

   Har sahifa o'z rangini oladi; tanlangan tab to'liq rangda, qolganlari
   oq. Pastdagi qalin "qirra" — soya, bosilganda tugma cho'kadi.
   Tailwind sinflari to'liq yozilgan — bo'laklab yig'ilsa JIT ularni
   topolmaydi. */

export type TabColor =
  | "blue" | "violet" | "emerald" | "amber" | "rose" | "cyan" | "indigo"
  | "teal" | "orange" | "slate";

const ON: Record<TabColor, string> = {
  blue: "bg-gradient-to-b from-sky-400 to-blue-600 text-white border-transparent shadow-[0_3px_0_0_#1e3a8a]",
  violet: "bg-gradient-to-b from-violet-400 to-purple-600 text-white border-transparent shadow-[0_3px_0_0_#4c1d95]",
  emerald: "bg-gradient-to-b from-emerald-400 to-teal-600 text-white border-transparent shadow-[0_3px_0_0_#134e4a]",
  amber: "bg-gradient-to-b from-amber-300 to-orange-500 text-white border-transparent shadow-[0_3px_0_0_#9a3412]",
  rose: "bg-gradient-to-b from-rose-400 to-pink-600 text-white border-transparent shadow-[0_3px_0_0_#831843]",
  cyan: "bg-gradient-to-b from-cyan-400 to-sky-600 text-white border-transparent shadow-[0_3px_0_0_#0c4a6e]",
  indigo: "bg-gradient-to-b from-indigo-400 to-indigo-600 text-white border-transparent shadow-[0_3px_0_0_#312e81]",
  teal: "bg-gradient-to-b from-teal-400 to-cyan-700 text-white border-transparent shadow-[0_3px_0_0_#134e4a]",
  orange: "bg-gradient-to-b from-orange-400 to-red-500 text-white border-transparent shadow-[0_3px_0_0_#7c2d12]",
  slate: "bg-gradient-to-b from-slate-500 to-slate-700 text-white border-transparent shadow-[0_3px_0_0_#0f172a]",
};

const OFF =
  "bg-white text-slate-600 border-slate-200 shadow-[0_3px_0_0_#e2e8f0] "
  + "hover:text-slate-900 hover:-translate-y-px";

/** Tab qatori konteyneri (pastki chiziq o'rniga — tugmalar qatori). */
export const TAB_BAR_3D = "flex gap-2 overflow-x-auto pt-0.5 pb-2 px-0.5";

/** Bitta tab tugmasining sinflari. */
export function tab3d(active: boolean, color: TabColor = "blue",
                      size: "md" | "sm" = "md"): string {
  const pad = size === "sm" ? "px-3 py-1 text-xs" : "px-3.5 py-1.5 text-sm";
  return `${pad} rounded-xl border font-semibold whitespace-nowrap `
    + "select-none transition-all duration-100 "
    + "active:translate-y-[3px] active:shadow-none "
    + (active ? ON[color] : OFF);
}
