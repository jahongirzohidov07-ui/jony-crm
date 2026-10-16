/**
 * KUNLIK TUSHUMNI ADMIN KESIMIDA BO'LISH (2026-09-10).
 *
 * Jahongir: "shu joyini adminni tanlanadigan qilib bering.
 * opam/Mavluda opa qancha naqt qancha clickdan pul olgani chiqib
 * turadigan qilib 1talab hisoblab chiqishyaptikan hozir".
 *
 * Nega frontendda (backendga yangi so'rov yubormasdan): endpoint
 * allaqachon o'sha kunning HAMMA to'lovini `rows` ichida qaytaradi
 * (api/dashboard.py -> cash_day: jami/usullar aynan shu sikldan
 * hisoblanadi, hech narsa kesilmaydi). Demak adminni tanlaganda
 * yangi so'rov shart emas — bu Neon trafigini ham, kutishni ham
 * tejaydi.
 *
 * MUHIM: `who` bo'sh bo'lsa backend bergan raqamlar O'ZGARISHSIZ
 * qaytariladi — ya'ni hozirgi ko'rinish bir zarra ham o'zgarmaydi.
 */

export interface CashDayRow {
  id: number;
  time: string | null;
  student_id: number;
  student: string;
  group: string | null;
  amount: number;
  method: string;
  method_label: string;
  received_by: string | null;
  branch: string;
  is_new: boolean;
  note: string | null;
}

export interface CashDayMethod {
  method: string;
  label: string;
  amount: number;
  count: number;
}

export interface CashDayReceiver {
  name: string;
  amount: number;
  count: number;
}

/** Qo'shimcha daromad (kitob sotuvi, mock va h.k.) — 2026-10-06. */
export interface CashDayOther {
  id: number;
  category: string;
  label: string;
  amount: number;
  method: string;
  method_label: string;
  note: string | null;
  created_by: string | null;
  branch: string;
}

/** Terminal ↔ naqd o'tkazmasi (2026-10-16) — tushum emas, kunning
 *  kassa harakati. */
export interface CashDayTransfer {
  id: number;
  kind: "withdraw" | "deposit";
  kind_label: string;
  /** "Terminaldan naqdga: 1 000 000 (komissiya 1% — 10 000) → naqd +990 000" */
  title: string;
  amount: number;
  fee_rate: number;
  fee: number;
  net: number;
  from_method: string;
  to_method: string;
  note: string | null;
  created_by: string | null;
  branch: string;
}

export interface CashDayData {
  /** Cheklangan filial administratori: faqat bugun (2026-10-06). */
  today_only?: boolean;
  transfer_rows?: CashDayTransfer[];
  /** Usullar bo'yicha to'liq ta'sir (komissiya bilan): terminal −, naqd + */
  transfer_effect?: { method: string; label: string; amount: number }[];
  transfer_fee_total?: number;
  other_rows?: CashDayOther[];
  other_total?: number;
  grand_total?: number;
  date: string;
  total: number;
  count: number;
  by_method: CashDayMethod[];
  new_count: number;
  new_sum: number;
  old_count: number;
  old_sum: number;
  by_receiver: CashDayReceiver[];
  rows: CashDayRow[];
}

export interface CashDaySlice {
  total: number;
  count: number;
  by_method: CashDayMethod[];
  new_count: number;
  new_sum: number;
  old_count: number;
  old_sum: number;
  rows: CashDayRow[];
}

/** Backend `created_by` bo'sh bo'lsa "—" nomi bilan yig'adi
 *  (api/dashboard.py: `who = p.created_by or "—"`). Shu yerda ham
 *  aynan shunday bo'lishi shart, aks holda chip bosilganda ro'yxat
 *  bo'sh chiqib qolardi. */
export const NO_RECEIVER = "—";

export function receiverKey(row: CashDayRow): string {
  return row.received_by || NO_RECEIVER;
}

/** Pul yig'indisida float qoldig'i chiqmasligi uchun — backend ham
 *  `round(x, 2)` qiladi. */
function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

/**
 * `who` — tanlangan adminning nomi (by_receiver dagi `name`).
 * null/bo'sh bo'lsa: backend raqamlari o'zgarishsiz.
 */
export function sliceByReceiver(
  data: CashDayData,
  who: string | null,
): CashDaySlice {
  if (!who) {
    return {
      total: data.total,
      count: data.count,
      by_method: data.by_method,
      new_count: data.new_count,
      new_sum: data.new_sum,
      old_count: data.old_count,
      old_sum: data.old_sum,
      rows: data.rows,
    };
  }

  const rows = data.rows.filter((r) => receiverKey(r) === who);

  const sums: Record<string, { amount: number; count: number }> = {};
  for (const m of data.by_method) sums[m.method] = { amount: 0, count: 0 };

  let total = 0;
  let newCount = 0;
  let newSum = 0;
  for (const r of rows) {
    total += r.amount;
    if (!sums[r.method]) sums[r.method] = { amount: 0, count: 0 };
    sums[r.method].amount += r.amount;
    sums[r.method].count += 1;
    if (r.is_new) {
      newCount += 1;
      newSum += r.amount;
    }
  }

  return {
    total: round2(total),
    count: rows.length,
    // Tartib va yorliqlar backenddagidek qoladi — kartalar sakramaydi.
    by_method: data.by_method.map((m) => ({
      method: m.method,
      label: m.label,
      amount: round2(sums[m.method].amount),
      count: sums[m.method].count,
    })),
    new_count: newCount,
    new_sum: round2(newSum),
    old_count: rows.length - newCount,
    old_sum: round2(total - newSum),
    rows,
  };
}
