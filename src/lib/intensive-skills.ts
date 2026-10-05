import data from '../data/intensive-skills.json';
import type { Question } from './intensive';

export type SkillQuestion = Omit<Question, 'id'>;
export type SkillText = { title: string; text: string; questions: SkillQuestion[] };
export type SkillPack = {
  lesson: number; level: string; objective: string;
  reading: SkillText; listening: SkillText;
  speaking: { prompt: string; success: string[] };
  writing: { prompt: string; model: string; success: string[] };
  teacherNote: string;
};
export const skillPacks = data as SkillPack[];
export const skillsForLesson = (lesson: number) => skillPacks.find(pack => pack.lesson === lesson);
export const skillQuestions = (pack: SkillPack, mode: 'reading' | 'listening'): Question[] =>
  pack[mode].questions.map((question, index) => ({ ...question, id: `${mode}-${pack.lesson}-${index}` }));

// This rubric is for classroom feedback. It is not the official Multilevel scale.
export const productionRubric = [
  ['Vazifa bajarilishi', 'Savolga javob berdi, kerakli tafsilot va misolni keltirdi.'],
  ['Tushunarlilik va izchillik', 'Fikrlar tartibli, bog‘lovchilar o‘rinli; tinglovchi yoki o‘quvchi ma’noni tushunadi.'],
  ['Lug‘at', 'Mavzuga mos so‘zlarni mustaqil va to‘g‘ri ma’noda ishlatdi.'],
  ['Grammar', 'O‘tilgan shakllarni ishlatdi; xatolar asosiy ma’noni buzmaydi.'],
] as const;
