/** JONY TEACHER — API turlari (2026-08-10).
 *
 * Backend: api/teacher_app.py. Yo'qlama YOZISH esa mavjud
 * PUT /api/lessons/{id}/attendance orqali ketadi (u yerda sana
 * qoidalari, XP, Telegram xabarnomalari va oylik hisobi bor —
 * ikkinchi nusxa yozilmadi). */

export interface LessonCard {
  lesson_id: number;
  group_id: number;
  group: string;
  level: string | null;
  time: string | null;
  date: string;
  held: boolean;
  students: number;
  marked: number;
  graded: number;
  done: boolean;
}

export interface TeacherHome {
  teacher: string;
  grade: string | null;
  date: string;
  groups: number;
  students: number;
  lessons_this_month: number;
  today: LessonCard[];
  pending: number;
}

export interface TeacherToday {
  date: string;
  teacher: string;
  lessons: LessonCard[];
  missed: LessonCard[];
  groups: number;
  students: number;
  pending: number;
  hint?: string;
}

export interface LessonStudent {
  id: number;
  full_name: string;
  status: string;
  /** 1 keldi · 2 kech keldi · 0 kelmadi · null belgilanmagan */
  present: number | null;
  /** 2 bajardi · 1 qisman · 0 qilmadi · null */
  homework: number | null;
  /** kundalik baho 1-5 */
  grade: number | null;
}

export interface LessonDetail {
  lesson_id: number;
  group_id: number;
  group: string;
  level: string | null;
  date: string;
  time: string | null;
  editable: boolean;
  readonly_reason: string | null;
  students: LessonStudent[];
}

export interface WeekDay {
  date: string;
  label: string;
  is_today: boolean;
  lessons: LessonCard[];
}

export interface TeacherWeek {
  start: string;
  end: string;
  days: WeekDay[];
  teacher?: string;
}

/** Yo'qlama belgilari — bitta joyda, butun ilova shundan foydalanadi. */
export const PRESENT_OPTS = [
  { v: 1, label: "Keldi", short: "✓", cls: "bg-emerald-600 text-white", soft: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  { v: 2, label: "Kech", short: "🕒", cls: "bg-amber-500 text-white", soft: "bg-amber-50 text-amber-700 border-amber-200" },
  { v: 0, label: "Yo'q", short: "✗", cls: "bg-red-600 text-white", soft: "bg-red-50 text-red-600 border-red-200" },
];

export const HOMEWORK_OPTS = [
  { v: 2, label: "Bajardi" },
  { v: 1, label: "Qisman" },
  { v: 0, label: "Qilmadi" },
];
