// To'lov usullari - backend/roles.py'dagi PAYMENT_METHODS bilan bir xil.

export const PAYMENT_METHODS = [
  { key: "cash", label: "Naqd" },
  { key: "card", label: "Click" },         // Click, Payme, karta o'tkazmasi
  { key: "terminal", label: "Terminal" },  // POS apparati
  { key: "other", label: "Boshqa" },
];

export function methodLabel(method?: string | null): string {
  if (!method) return "";
  return PAYMENT_METHODS.find((m) => m.key === method)?.label || method;
}

/** Kanal (reklama manbai) - backend'dagi MARKETING_CHANNELS bilan bir xil. */
export const MARKETING_CHANNELS = [
  { key: "instagram", label: "Instagram" },
  { key: "telegram", label: "Telegram" },
  { key: "ads", label: "Reklama (boshqa)" },
  { key: "referral", label: "Tanish orqali" },
  { key: "visit", label: "Tashrif" },
  { key: "phone", label: "Telefon" },
  { key: "other", label: "Boshqa" },
];

export function channelLabel(key?: string | null): string {
  if (!key) return "—";
  return MARKETING_CHANNELS.find((c) => c.key === key)?.label || key;
}
