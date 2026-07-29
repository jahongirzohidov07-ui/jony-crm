export function formatSom(amount: number): string {
  const rounded = Math.round(amount);
  return `${rounded.toLocaleString("en-US")} so'm`;
}

export function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

const SHORT_MONTHS = [
  "Yan", "Fev", "Mar", "Apr", "May", "Iyun",
  "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek",
];

/** "2026-02" -> "Fev '26" - compact label for chart axes. */
export function formatPeriodLabel(period: string): string {
  const [y, m] = period.split("-").map(Number);
  if (!y || !m) return period;
  return `${SHORT_MONTHS[m - 1]} '${String(y).slice(2)}`;
}

/** "2026-07-23" -> "23-Iyul" - compact label for daily chart axes. */
export function formatDayLabel(period: string): string {
  const [, m, d] = period.split("-").map(Number);
  if (!m || !d) return period;
  return `${d}-${SHORT_MONTHS[m - 1]}`;
}

/** Picks the right compact label based on the bucket granularity returned
 * alongside a chart's data points. */
export function formatGrowthLabel(period: string, granularity: "day" | "month"): string {
  return granularity === "day" ? formatDayLabel(period) : formatPeriodLabel(period);
}
