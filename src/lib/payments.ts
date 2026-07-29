// To'lov usullari - backend/roles.py'dagi PAYMENT_METHODS bilan bir xil.

export const PAYMENT_METHODS = [
  { key: "cash", label: "Naqd" },
  { key: "card", label: "Plastik" },       // Click, Payme, karta o'tkazmasi
  { key: "terminal", label: "Terminal" },  // POS apparati
  { key: "other", label: "Boshqa" },
];

export function methodLabel(method?: string | null): string {
  if (!method) return "";
  return PAYMENT_METHODS.find((m) => m.key === method)?.label || method;
}
