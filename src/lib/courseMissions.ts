import missions from '../data/course-weekly-missions.json';

/** Canonical data shared with portfolio choices; a mission is a task, not mastery evidence. */
export type CourseMission = {
  id: string;
  language: string;
  week: number;
  /** Week-end lesson under which the portfolio output is saved. */
  lesson: number;
  title: string;
  prompt: string;
  output: string;
  criteria: readonly string[];
  suggested_type: string;
};

export function getCourseMission(language: string, lesson: number): CourseMission | null {
  if ((language !== 'en' && language !== 'de') || !Number.isInteger(lesson) || lesson < 1) return null;
  const perWeek = language === 'de' ? 3 : 6;
  return missions[language][Math.floor((lesson - 1) / perWeek)] ?? null;
}
