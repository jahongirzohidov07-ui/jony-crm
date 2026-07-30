// HR voronkasi - backend/roles.py'dagi CANDIDATE_STAGES bilan bir xil.

export const CANDIDATE_STAGES = [
  { key: "applied", label: "Ariza topshirdi", color: "#94a3b8" },
  { key: "screening", label: "Rezyume ko'rildi", color: "#38bdf8" },
  { key: "interview", label: "Suhbatga chaqirildi", color: "#818cf8" },
  { key: "demo", label: "Sinov darsi / vazifa", color: "#a78bfa" },
  { key: "offer", label: "Taklif berildi", color: "#f59e0b" },
  { key: "hired", label: "Ishga olindi", color: "#10b981" },
  { key: "rejected", label: "Rad etildi", color: "#ef4444" },
];

/** Voronka ustunlari - "rad etildi" alohida turadi, u bosqich emas. */
export const CANDIDATE_FUNNEL = CANDIDATE_STAGES.filter(
  (s) => s.key !== "rejected"
);

export function stageLabel(key?: string | null): string {
  if (!key) return "";
  return CANDIDATE_STAGES.find((s) => s.key === key)?.label || key;
}

export function stageColor(key?: string | null): string {
  return CANDIDATE_STAGES.find((s) => s.key === key)?.color || "#cbd5e1";
}

export const CANDIDATE_SOURCES = [
  { key: "instagram", label: "Instagram" },
  { key: "telegram", label: "Telegram" },
  { key: "referral", label: "Tanish orqali" },
  { key: "job_site", label: "Ish e'lonlari sayti" },
  { key: "walk_in", label: "O'zi keldi" },
  { key: "alumni", label: "O'z bitiruvchimiz" },
  { key: "other", label: "Boshqa" },
];

export function candidateSourceLabel(key?: string | null): string {
  if (!key) return "";
  return CANDIDATE_SOURCES.find((s) => s.key === key)?.label || key;
}

export const VACANCY_STATUSES = [
  { key: "open", label: "Ochiq", color: "emerald" },
  { key: "paused", label: "To'xtatilgan", color: "amber" },
  { key: "closed", label: "Yopilgan", color: "slate" },
];

export function vacancyStatusLabel(key?: string | null): string {
  if (!key) return "";
  return VACANCY_STATUSES.find((s) => s.key === key)?.label || key;
}
