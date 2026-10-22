import { AlertTriangle } from "lucide-react";

// TAXMINIY BOSISH HISOBI (2026-10-22). Egasi: "diagnostikada hech narsani
// bilmay taxminan bosib tashlaydiganlarning darajasi baland chiqyapti".
// Server har javobni o'zi o'lchaydi: "Bilmayman" (idk) va savolni o'qishga
// yetmaydigan darajada tez bosilgan javoblar (fast) xato hisoblanadi va
// alohida sanaladi. Bu yerda faqat XODIM ko'radigan natijalar chiziladi —
// test topshiruvchiga "tez bosdingiz" degan hech narsa ko'rsatilmaydi.
//
// Natija payloadi (ingliz / nemis / rus testlari):
//   result.idk, result.fast         — umumiy son (yoki {total, <bo'lim>: n})
//   result.guess_warning            — tez javoblar >= 30% bo'lsa true
//   result.skills[] / sections[] / blocks[] — bo'lim bo'yicha {idk, fast}
//   result.timed === false          — vaqt o'lchanmagan (deploydan oldingi
//                                     ingliz/nemis/rus yozuvi): "Juda tez: —"
//                                     (inglizda idk/fast null — "Bilmayman: —")
// Maydonlar ham, timed ham bo'lmasa — hech narsa chizilmaydi.

type Any = any;

const SEC_LABEL: Record<string, string> = {
  grammar: "Grammatika", vocab: "Lug'at", vocabulary: "Lug'at",
  reading: "Reading", listening: "Listening",
};

export type GuessSection = { key: string; label: string; idk: number; fast: number };
export type GuessSummary = {
  idk: number | null; fast: number | null; warning: boolean; sections: GuessSection[];
  /** false — javob vaqti o'lchanmagan (eski yozuv), "juda tez" noma'lum. */
  timed: boolean;
};

const num = (v: unknown): number | undefined =>
  typeof v === "number" && Number.isFinite(v) ? v : undefined;

/** Son yoki {total, grammar: 2, ...} ko'rinishidagi hisoblagich. */
function counter(v: unknown): { total?: number; by: Record<string, number> } {
  const direct = num(v);
  if (direct !== undefined) return { total: direct, by: {} };
  if (!v || typeof v !== "object" || Array.isArray(v)) return { by: {} };
  const o = v as Record<string, unknown>;
  const by: Record<string, number> = {};
  for (const [k, x] of Object.entries(o)) {
    const n = num(x);
    if (n !== undefined && !["total", "all", "overall"].includes(k)) by[k] = n;
  }
  const total = num(o.total) ?? num(o.all) ?? num(o.overall)
    ?? (Object.keys(by).length ? Object.values(by).reduce((a, b) => a + b, 0) : undefined);
  return { total, by };
}

function sectionLabel(item: Any, key: string): string {
  if (typeof item?.label === "string" && item.label) return item.label;
  if (SEC_LABEL[key]) return SEC_LABEL[key];
  if (num(item?.stage) !== undefined) return `${item.stage}-bosqich`;
  if (num(item?.month) !== undefined) return `${item.month}-bosqich`;
  return key;
}

/** Bo'lim ro'yxati: massiv ({key|skill|stage, idk, fast}) yoki
 *  {grammar: {idk, fast}} ko'rinishidagi obyekt. */
function sectionList(src: Any): GuessSection[] {
  for (const field of ["sections", "skills", "blocks"]) {
    const raw = src?.[field];
    const items: [string, Any][] = Array.isArray(raw)
      ? raw.map((x: Any, i: number) => [String(x?.key ?? x?.skill ?? x?.stage ?? x?.month ?? i), x])
      : raw && typeof raw === "object" ? Object.entries(raw) : [];
    const rows = items
      .filter(([, x]) => num(x?.idk) !== undefined || num(x?.fast) !== undefined)
      .map(([key, x]) => ({ key, label: sectionLabel(x, key), idk: num(x.idk) ?? 0, fast: num(x.fast) ?? 0 }));
    if (rows.length) return rows;
  }
  return [];
}

export function guessSummary(res: Any, row?: Any): GuessSummary | null {
  const src = res && typeof res === "object" ? res : {};
  const idk = counter(src.idk ?? row?.idk);
  const fast = counter(src.fast ?? row?.fast);
  const warning = (src.guess_warning ?? row?.guess_warning) === true;
  const timed = (src.timed ?? row?.timed) !== false;
  let sections = sectionList(src);
  if (!sections.length) {
    const keys = [...new Set([...Object.keys(idk.by), ...Object.keys(fast.by)])];
    sections = keys.map((key) => ({
      key, label: SEC_LABEL[key] || key, idk: idk.by[key] ?? 0, fast: fast.by[key] ?? 0 }));
  }
  const sum = (k: "idk" | "fast") => sections.length ? sections.reduce((a, s) => a + s[k], 0) : undefined;
  const totalIdk = idk.total ?? sum("idk");
  const totalFast = fast.total ?? sum("fast");
  // timed === false (deploydan oldingi sessiya) — sonlar yo'q bo'lsa ham
  // "Bilmayman: — · Juda tez: —" va "eski test" izohi chiziladi: 0 deb
  // ko'rsatsak "toza" sessiyadek ko'rinardi.
  if (totalIdk === undefined && totalFast === undefined && !warning && timed) return null;
  return { idk: totalIdk ?? null, fast: totalFast ?? null, warning, sections, timed };
}

export const GUESS_WARNING_TEXT = "Taxminan bosilgan bo'lishi mumkin";

/** Ro'yxat qatoridagi kichik ogohlantirish (yopiq holatda ham ko'rinadi). */
export function GuessWarningChip({ res, row, iconOnly = false }: { res: Any; row?: Any; iconOnly?: boolean }) {
  const s = guessSummary(res, row);
  if (!s?.warning) return null;
  const tip = `${GUESS_WARNING_TEXT}: Juda tez: ${s.fast ?? 0} · Bilmayman: ${s.idk ?? 0}`;
  return (
    <span title={tip} role="note"
          className="inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-[11px] font-semibold text-amber-800">
      <AlertTriangle size={11} aria-hidden="true" />
      {iconOnly ? <span className="sr-only">{GUESS_WARNING_TEXT}</span> : GUESS_WARNING_TEXT}
    </span>
  );
}

/** To'liq hisob: umumiy va bo'limlar bo'yicha "Bilmayman: N · Juda tez: N". */
export function GuessStats({ res, row, className = "" }: { res: Any; row?: Any; className?: string }) {
  const s = guessSummary(res, row);
  if (!s) return null;
  const line = (idk: number | null, fast: number | null) =>
    `Bilmayman: ${idk ?? "—"} · Juda tez: ${s.timed ? fast ?? "—" : "—"}`;
  return (
    <div className={`space-y-1 ${className}`}>
      {s.warning && (
        <p role="note" className="flex items-center gap-1.5 rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">
          <AlertTriangle size={13} aria-hidden="true" /> {GUESS_WARNING_TEXT}
        </p>
      )}
      <p className="text-xs text-slate-700">
        {line(s.idk, s.fast)}
        {!s.timed && <span className="text-slate-400"> (javob vaqti o'lchanmagan — eski test)</span>}
      </p>
      {s.sections.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {s.sections.map((x) => (
            <span key={x.key} className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[11px] text-slate-600">
              {x.label}: {line(x.idk, x.fast)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
