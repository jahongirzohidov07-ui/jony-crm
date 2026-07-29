// Xarajat turlari - backend/roles.py'dagi EXPENSE_CATEGORIES bilan bir xil.
//
// DIQQAT: ustozlar ish haqi bu ro'yxatda yo'q - u avtomatik hisoblanadi
// (Guruhlar -> Ustozlar ish haqi). "salary" - ustozlardan boshqa
// xodimlar uchun.

export const EXPENSE_CATEGORIES = [
  { key: "rent", label: "Ijara" },
  { key: "utilities", label: "Kommunal" },
  { key: "salary", label: "Xodimlar oyligi" },
  { key: "ads", label: "Reklama" },
  { key: "tax", label: "Soliq" },
  { key: "repair", label: "Ta'mir" },
  { key: "equipment", label: "Jihoz / kanstovar" },
  { key: "other", label: "Boshqa" },
];

export function categoryLabel(key?: string | null): string {
  if (!key) return "";
  return EXPENSE_CATEGORIES.find((c) => c.key === key)?.label || key;
}

export const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];
