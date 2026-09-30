/** Explicit month names prevent browser MM/DD and DD/MM ambiguity.
 * Server bounds share the same Tashkent calendar as order validation.
 */
const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
  "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
type Bounds = { min_date?: string; max_date?: string; min_notice_days: number; max_ahead_days: number };
export function examOrderDates(bounds: Bounds, now = new Date()) {
  // Fallback supports a cached response from before date bounds were added.
  const parts = new Intl.DateTimeFormat("en", { timeZone: "Asia/Tashkent",
    year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now);
  const part = (key: string) => parts.find(p => p.type === key)!.value;
  const today = Date.UTC(Number(part("year")), Number(part("month")) - 1, Number(part("day")));
  const start = bounds.min_date ? Date.parse(bounds.min_date + "T00:00:00Z") : today + bounds.min_notice_days * 86400000;
  const end = bounds.max_date ? Date.parse(bounds.max_date + "T00:00:00Z") : today + bounds.max_ahead_days * 86400000;
  const result: {value: string; label: string}[] = [];
  for (let day = start; day <= end; day += 86400000) {
    const d = new Date(day);
    result.push({ value: d.toISOString().slice(0, 10),
      label: d.getUTCDate() + "-" + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear() });
  }
  return result;
}
