// Fanlar va darajalar - backend/roles.py'dagi SUBJECTS / SUBJECT_LEVELS
// bilan bir xil bo'lishi shart.

export const SUBJECTS = [
  { key: "english", label: "Ingliz tili" },
  { key: "russian", label: "Rus tili" },
  { key: "korean", label: "Koreys tili" },
  { key: "turkish", label: "Turk tili" },
  { key: "german", label: "Nemis tili" },
  { key: "biology", label: "Biologiya" },
  { key: "programming", label: "Dasturlash" },
  { key: "mental_math", label: "Mental arifmetika" },
  { key: "robotics", label: "Robototexnika" },
];

const CEFR_LEVELS = [
  { key: "a1", label: "A1" },
  { key: "a2", label: "A2" },
  { key: "b1", label: "B1" },
  { key: "b2", label: "B2" },
];

const ENGLISH_LEVELS = [
  { key: "step1", label: "Step 1" },
  { key: "step2", label: "Step 2" },
  { key: "step3", label: "Step 3" },
  { key: "step4", label: "Step 4" },
  { key: "ielts_intro", label: "IELTS Introduction" },
  { key: "ielts_foundation", label: "IELTS Foundation" },
  { key: "ielts_graduation", label: "IELTS Graduation" },
  { key: "cefr", label: "CEFR" },
];

const COURSE_LEVELS = [
  { key: "basic", label: "Boshlang'ich" },
  { key: "intermediate", label: "O'rta" },
  { key: "advanced", label: "Yuqori" },
];

export const SUBJECT_LEVELS: Record<string, { key: string; label: string }[]> = {
  english: ENGLISH_LEVELS,
  russian: CEFR_LEVELS,
  korean: CEFR_LEVELS,
  turkish: CEFR_LEVELS,
  german: CEFR_LEVELS,
  biology: COURSE_LEVELS,
  programming: COURSE_LEVELS,
  mental_math: COURSE_LEVELS,
  robotics: COURSE_LEVELS,
};

export function subjectLabel(key?: string | null): string {
  if (!key) return "";
  return SUBJECTS.find((s) => s.key === key)?.label || key;
}

export function levelLabel(key?: string | null): string {
  if (!key) return "";
  for (const levels of Object.values(SUBJECT_LEVELS)) {
    const hit = levels.find((l) => l.key === key);
    if (hit) return hit.label;
  }
  return key;
}

export function levelsFor(subject?: string | null) {
  if (!subject) return [];
  return SUBJECT_LEVELS[subject] || [];
}

/** "Ingliz tili · Step 1" ko'rinishida qisqa yozuv. */
export function subjectLine(g: {
  subject?: string | null;
  level?: string | null;
}): string {
  const parts = [subjectLabel(g.subject), levelLabel(g.level)].filter(Boolean);
  return parts.join(" · ");
}


// ---- Dars kunlari ----
export const WEEKDAYS = [
  { key: "mon", label: "Dushanba", short: "Du" },
  { key: "tue", label: "Seshanba", short: "Se" },
  { key: "wed", label: "Chorshanba", short: "Ch" },
  { key: "thu", label: "Payshanba", short: "Pa" },
  { key: "fri", label: "Juma", short: "Ju" },
  { key: "sat", label: "Shanba", short: "Sha" },
  { key: "sun", label: "Yakshanba", short: "Ya" },
];

export function parseDays(days?: string | null): string[] {
  if (!days) return [];
  return days.split(",").filter(Boolean);
}

export function dayLabels(days?: string | null): string[] {
  const set = parseDays(days);
  return WEEKDAYS.filter((d) => set.includes(d.key)).map((d) => d.label);
}
