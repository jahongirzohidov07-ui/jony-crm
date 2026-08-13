// Lid voronkasi - backend/roles.py bilan bir xil bo'lishi shart.

export type LeadStage =
  | "new"
  | "contacted"
  | "trial_scheduled"
  | "trial_attended"
  | "no_show"
  | "converted"
  | "rejected";

export type LeadSource =
  | "visit"
  | "phone"
  | "instagram"
  | "telegram"
  | "website"
  | "referral"
  | "ads"
  | "other";

export interface StageDef {
  key: LeadStage;
  label: string;
  /** Ustun sarlavhasi rangi (Tailwind sinflari). */
  tone: string;
  /** Yakuniy bosqich - lid bu yerga tushsa, ish tugagan hisoblanadi. */
  terminal?: boolean;
}

export const LEAD_STAGES: StageDef[] = [
  { key: "new", label: "Yangi", tone: "bg-slate-100 text-slate-600" },
  { key: "contacted", label: "Bog'lanildi", tone: "bg-sky-50 text-sky-700" },
  {
    key: "trial_scheduled",
    label: "Sinovga yozildi",
    tone: "bg-amber-50 text-amber-700",
  },
  {
    key: "trial_attended",
    label: "Sinovga keldi",
    tone: "bg-violet-50 text-violet-700",
  },
  {
    key: "no_show",
    label: "Sinov darsiga kelmadi",
    tone: "bg-orange-50 text-orange-700",
    terminal: true,
  },
  {
    key: "rejected",
    label: "Rad etdi",
    tone: "bg-red-50 text-red-600",
    terminal: true,
  },
];

/** "O'quvchiga aylandi" doskada KO'RINMAYDI - u endi lid emas, Talabalar
 * bo'limida turadi. Nomi faqat hisobotlarda kerak bo'ladi. */
export const CONVERTED_LABEL = "O'quvchi bo'ldi";

export const LEAD_SOURCES: { key: LeadSource; label: string }[] = [
  { key: "visit", label: "Tashrif" },
  { key: "phone", label: "Telefon" },
  { key: "instagram", label: "Instagram" },
  { key: "telegram", label: "Telegram" },
  // 2026-08-13: saytdan (jonyacademy.uz) kelgan arizalar
  { key: "website", label: "Sayt (jonyacademy.uz)" },
  { key: "referral", label: "Tanish orqali" },
  { key: "ads", label: "Reklama" },
  { key: "other", label: "Boshqa" },
];

/** Manba lidni voronkaning qaysi nuqtasidan boshlashini belgilaydi.
 * backend/roles.py'dagi LEAD_SOURCE_DEFAULT_STAGE bilan bir xil. */
export const SOURCE_DEFAULT_STAGE: Record<LeadSource, LeadStage> = {
  visit: "trial_scheduled",
  phone: "contacted",
  instagram: "new",
  telegram: "new",
  website: "new",
  referral: "new",
  ads: "new",
  other: "new",
};

/** Sinf tanlash ro'yxati. Matn sifatida saqlanadi, shuning uchun
 * kelajakda "9-A" kabi qiymat ham qo'shish mumkin. */
export const GRADES = [
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "Kattalar",
];

export function stageLabel(stage: string): string {
  if (stage === "converted") return CONVERTED_LABEL;
  return LEAD_STAGES.find((s) => s.key === stage)?.label || stage;
}

export function sourceLabel(source: string): string {
  return LEAD_SOURCES.find((s) => s.key === source)?.label || source;
}
