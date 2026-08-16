/** JONY STUDENT — API turlari va yordamchilar (2026-08-09).
 *
 * Backend: api/student_app.py. HAR BIR yo'l faqat KIRGAN o'quvchining
 * o'zi haqida ma'lumot beradi — student_id hech qayerda yuborilmaydi,
 * server tokendan o'zi topadi. */

export interface LevelStep {
  key: string;
  label: string;
  ielts: string;
  cefr: string;
}

export interface LevelProgress {
  points: number;
  level: LevelStep;
  max_level: boolean;
  next: {
    label: string;
    ielts: string;
    cefr: string;
    points_left: number;
    progress_percent: number;
  } | null;
}

export interface SkillProgress extends LevelProgress {
  key: string;
  label: string;
  tone: string;
}

/** Kunlik uchta vazifa (2026-08-16). Bajarilgani BUGUNGI mashq
 * yozuvlaridan hisoblanadi — alohida "bajardim" tugmasi yo'q. */
export interface DailyTask {
  key: string;
  title: string;
  hint: string;
  target: number;
  done_count: number;
  done: boolean;
  minutes: number;
  href: string;
}

export interface DailyGoal {
  tasks: DailyTask[];
  done: number;
  total: number;
  percent: number;
  all_done: boolean;
  reward_xp: number;
  reward_coin: number;
  next: DailyTask | null;
}

/** Yarim qolgan grammatika mavzusi — "Davom ettirish" kartasi. */
export interface ContinueCard {
  kind: string;
  title: string;
  subtitle: string;
  level: string;
  solved: number;
  total: number;
  percent: number;
  minutes: number;
  xp: number;
  coin: number;
  href: string;
}

export interface StudentHome {
  name: string;
  photo?: string | null;
  balance?: number;
  daily?: DailyGoal;
  continue?: ContinueCard | null;
  week_xp?: number;
  group: string | null;
  level_label: string | null;
  status: string;
  overall: LevelProgress;
  skills: SkillProgress[];
  gamification: {
    coins: number;
    lifetime_xp: number;
    level: number;
    league: { name: string; icon: string; color: string } | null;
  };
  streak: number;
  today: { answered: number; correct: number };
  ranks: {
    group_rank: number | null;
    group_total: number;
    branch_rank: number | null;
    branch_total: number;
  };
  games: { key: string; label: string; hint: string }[];
}

export interface SkillsCard {
  overall: LevelProgress;
  skills: SkillProgress[];
  points_per_level: number;
  levels: LevelStep[];
}

/** Bitta o'yin savoli. Maydonlar o'yin turiga qarab to'ladi. */
export interface RoundItem {
  word_id: number;
  prompt?: string;
  answer?: string;
  example?: string | null;
  hint?: string;
  options?: string[];
  /** "To'g'ri / Xato" o'yini: ekranda ko'rsatilgan tarjima. */
  shown?: string;
  /** "Harflarni tartiblash": aralashtirilgan harflar. */
  letters?: string[];
  left?: { word_id: number; text: string }[];
  right?: { word_id: number; text: string }[];
}

export interface VocabRound {
  game: string;
  label: string;
  items: RoundItem[];
  xp_per_correct: number;
}

export interface AnswerResult {
  correct: boolean;
  expected: string;
  xp: number;
  skills: SkillsCard;
}

export interface VocabStats {
  total: number;
  correct: number;
  percent: number;
  streak: number;
  by_game: { game: string; label: string; total: number; correct: number }[];
  week: { date: string; correct: number }[];
}

export interface LeaderboardRow {
  rank: number;
  name: string;
  points: number;
  is_me: boolean;
}

export interface Leaderboard {
  scope: string;
  period: string;
  rows: LeaderboardRow[];
  me: LeaderboardRow | null;
  hint?: string;
}

/** Ko'nikma rangi -> Tailwind klasslari. Backend faqat "tone" nomini
 * beradi (sky/violet/...), rang bu yerda tanlanadi — shunda dizayn
 * o'zgarsa backendga tegilmaydi. */
export const TONE_BAR: Record<string, string> = {
  sky: "bg-sky-500",
  violet: "bg-violet-500",
  emerald: "bg-emerald-500",
  amber: "bg-amber-500",
  rose: "bg-rose-500",
  teal: "bg-teal-500",
  slate: "bg-slate-400",
};

export const TONE_SOFT: Record<string, string> = {
  sky: "bg-sky-50 text-sky-700",
  violet: "bg-violet-50 text-violet-700",
  emerald: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  rose: "bg-rose-50 text-rose-700",
  teal: "bg-teal-50 text-teal-700",
  slate: "bg-slate-50 text-slate-600",
};

export const fmtNum = (n: number | undefined | null) =>
  Number(n || 0).toLocaleString().replace(/,/g, " ");
