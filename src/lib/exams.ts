// Imtihon turlari - backend/roles.py'dagi EXAM_KINDS bilan bir xil.

export const EXAM_KINDS = [
  { key: "unit", label: "Unit test" },
  { key: "mid", label: "Mid-course" },
  { key: "end", label: "End of course" },
  { key: "mock", label: "Mock test" },
] as const;

export const UNIT_COUNT = 12;
export const MOCK_MAX_BAND = 9;

/** Qo'lda yaratilmaydigan turlar (ro'yxatda ko'rinadi, tanlanmaydi). */
const EXTRA_KIND_LABELS: Record<string, string> = {
  kahoot: "Kahoot (jonli o'yin)",
};

export function examKindLabel(key?: string | null): string {
  if (!key) return "";
  return EXAM_KINDS.find((k) => k.key === key)?.label || EXTRA_KIND_LABELS[key] || key;
}

/** Ro'yxatda ko'rinadigan to'liq nom: "Unit 3" yoki "Mock test". */
export function examTitle(e: {
  kind: string;
  unit_no?: number | null;
  title?: string | null;
}): string {
  if (e.title) return e.title;
  if (e.kind === "unit" && e.unit_no) return `Unit ${e.unit_no}`;
  return examKindLabel(e.kind);
}

export const COIN_SOURCE_LABELS: Record<string, string> = {
  daily: "Kunlik baho",
  exam: "Imtihon",
  kahoot: "Kahoot o'yini",
  manual: "Qo'lda",
  reward: "Sovg'a",
  teacher_deduct: "Ustoz ayirdi (intizom)",
  pay_ontime: "O'z vaqtida to'lov",
};

export function coinSourceLabel(key?: string | null): string {
  if (!key) return "";
  return COIN_SOURCE_LABELS[key] || key;
}

/** Baho rangi - 5 yashil, 1 qizil. Jadvalda ko'z bilan darrov ajratish uchun. */
export function gradeTone(score: number): string {
  if (score >= 5) return "bg-emerald-500 text-white";
  if (score === 4) return "bg-teal-400 text-white";
  if (score === 3) return "bg-amber-400 text-white";
  if (score === 2) return "bg-orange-400 text-white";
  return "bg-red-500 text-white";
}
