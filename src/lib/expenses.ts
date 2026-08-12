// Xarajatlar ikki qavatli: har bir kategoriya bitta guruhga tegishli.
// backend/roles.py'dagi EXPENSE_GROUPS / EXPENSE_CATEGORY_DEFS bilan bir xil.
//
// DIQQAT: ustozlar oyligi qo'lda kiritilmaydi - u yoqlamadan avtomatik
// hisoblanadi. Shuning uchun kiritish ro'yxatida yo'q, lekin hisobot va
// analitikada alohida guruh sifatida ko'rinadi.

export const EXPENSE_GROUPS = [
  { key: "rent", label: "Ijara", color: "#0d9488" },
  { key: "communal", label: "Kommunal", color: "#38bdf8" },
  { key: "office", label: "Ofis xarajatlari", color: "#a78bfa" },
  { key: "admin_salary", label: "Ma'muriy xodim oyliklari", color: "#f59e0b" },
  { key: "teacher_salary", label: "Ustozlar oyligi", color: "#ef4444" },
  { key: "marketing", label: "Reklama", color: "#ec4899" },
  { key: "tax", label: "Soliq", color: "#64748b" },
  { key: "other", label: "Boshqa", color: "#cbd5e1" },
];

export function groupLabel(key?: string | null): string {
  if (!key) return "";
  return EXPENSE_GROUPS.find((g) => g.key === key)?.label || key;
}

export function groupColor(key?: string | null): string {
  return EXPENSE_GROUPS.find((g) => g.key === key)?.color || "#cbd5e1";
}

interface CategoryDef {
  key: string;
  label: string;
  group: string;
  /** Eski yozuvlarda qolgan kalit - yangi kiritishda ko'rsatilmaydi. */
  legacy?: boolean;
}

export const EXPENSE_CATEGORIES: CategoryDef[] = [
  { key: "rent", label: "Ijara", group: "rent" },

  { key: "electricity", label: "Elektr toki", group: "communal" },
  { key: "gas", label: "Gaz", group: "communal" },
  { key: "water_main", label: "Vodoprovod suv", group: "communal" },
  { key: "internet", label: "Internet / aloqa", group: "communal" },
  { key: "office_phone", label: "Ishxona telefoni", group: "communal" },
  { key: "utilities", label: "Kommunal (umumiy)", group: "communal", legacy: true },

  { key: "cooler_water", label: "Kuler suvi", group: "office" },
  { key: "printer_refill", label: "Printer zapravka", group: "office" },
  { key: "paper", label: "List qog'oz", group: "office" },
  { key: "marker", label: "Marker / doska", group: "office" },
  { key: "stationery", label: "Boshqa kanstovar", group: "office" },
  { key: "equipment", label: "Jihoz", group: "office" },
  // 2026-08-12, Jahongir: vlajniy, kitob va ishxona telefoni alohida
  { key: "wet_wipes", label: "Vlajniy salfetka", group: "office" },
  { key: "book", label: "Kitob", group: "office" },

  { key: "admin_salary", label: "Ma'muriy xodim oyligi", group: "admin_salary" },
  { key: "support_salary", label: "Farrosh / qorovul", group: "admin_salary" },
  { key: "salary", label: "Xodimlar oyligi (eski)", group: "admin_salary", legacy: true },

  { key: "ads", label: "Reklama", group: "marketing" },
  { key: "tax", label: "Soliq", group: "tax" },
  { key: "repair", label: "Ta'mir", group: "other" },
  { key: "other", label: "Boshqa", group: "other" },
];

/** Yangi xarajat kiritishda ko'rsatiladigan kategoriyalar (eskilarsiz). */
export const ACTIVE_CATEGORIES = EXPENSE_CATEGORIES.filter((c) => !c.legacy);

export function categoryLabel(key?: string | null): string {
  if (!key) return "";
  return EXPENSE_CATEGORIES.find((c) => c.key === key)?.label || key;
}

export function categoryGroup(key?: string | null): string {
  if (!key) return "other";
  return EXPENSE_CATEGORIES.find((c) => c.key === key)?.group || "other";
}

/** Kiritish formasi uchun guruhlab berilgan ro'yxat. */
export function categoriesByGroup() {
  return EXPENSE_GROUPS.filter((g) => g.key !== "teacher_salary")
    .map((g) => ({
      ...g,
      items: ACTIVE_CATEGORIES.filter((c) => c.group === g.key),
    }))
    .filter((g) => g.items.length > 0);
}

/**
 * SONI so'raladigan xarajatlar (Jahongir, 2026-08-12: "keyin sonini
 * qoshadigan bo'lsin masalan, list vlajniy, kitob, markerlarni
 * tanlaganda"). api/roles.py EXPENSE_COUNTABLE bilan bir xil.
 */
export const COUNTABLE_CATEGORIES = [
  "book", "wet_wipes", "paper", "marker", "stationery",
  "cooler_water", "printer_refill",
];

export function isCountable(key?: string | null): boolean {
  return !!key && COUNTABLE_CATEGORIES.includes(key);
}

export const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];
