export function formatSom(amount: number): string {
  const rounded = Math.round(amount);
  return `${rounded.toLocaleString("en-US")} so'm`;
}

/**
 * Sana OY NOMI bilan: "12-Avg 2026".
 *
 * 2026-08-12, Jahongir: "hamma joyda date faqat raqamda yozilgan, shu
 * oylarni nomlarini yozgin chalkashlik bolmasin". 12.08 va 08.12 ni
 * chalkashtirib yuborish oson — oy nomi bo'lsa chalkashlik yo'q.
 */
export function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  // "2026-08-12" ni Date orqali o'tkazmaymiz: zona farqi bilan bir kun
  // surilib ketishi mumkin.
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr);
  if (m) {
    const [, y, mo, day] = m;
    return `${day}-${SHORT_MONTHS[Number(mo) - 1]} ${y}`;
  }
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return `${String(d.getDate()).padStart(2, "0")}-` +
    `${SHORT_MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

/** Yilsiz, ixcham: "12-Avg". Jadval ustunlari uchun. */
export function formatDayMonth(dateStr?: string): string {
  if (!dateStr) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(dateStr);
  if (m) return `${m[3]}-${SHORT_MONTHS[Number(m[2]) - 1]}`;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return `${String(d.getDate()).padStart(2, "0")}-${SHORT_MONTHS[d.getMonth()]}`;
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

/** Toshkent vaqti (UTC+5) — server vaqtni zona belgisisiz (UTC) yuboradi. */
const UZ_OFFSET_MIN = 5 * 60;

function toUz(ts: string): Date | null {
  const iso = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(ts) ? ts : ts + "Z";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return null;
  return new Date(d.getTime() + UZ_OFFSET_MIN * 60000);
}

const p2 = (n: number) => String(n).padStart(2, "0");

/**
 * "2026-08-12T12:41:59.129" -> "12.08.2026 17:41:59" (Toshkent vaqti).
 * 2026-08-12, Jahongir: "kim va qaysi soatda kirgizganligi aniq
 * ko'rinib tursin sekundlarigacha".
 */
export function formatDateTime(ts?: string | null,
                               withSeconds = true): string {
  if (!ts) return "—";
  const t = toUz(ts);
  if (!t) return ts;
  return `${p2(t.getUTCDate())}-${SHORT_MONTHS[t.getUTCMonth()]} ` +
    `${t.getUTCFullYear()} ${p2(t.getUTCHours())}:${p2(t.getUTCMinutes())}` +
    (withSeconds ? `:${p2(t.getUTCSeconds())}` : "");
}

/** Faqat soat: "17:41:59" (Toshkent vaqti). */
export function formatTime(ts?: string | null,
                           withSeconds = true): string {
  if (!ts) return "—";
  const t = toUz(ts);
  if (!t) return "—";
  return `${p2(t.getUTCHours())}:${p2(t.getUTCMinutes())}` +
    (withSeconds ? `:${p2(t.getUTCSeconds())}` : "");
}
