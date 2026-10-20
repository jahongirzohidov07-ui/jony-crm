import auditedTopics from '../data/course-practice-audited-prompts.json';
import { extendedPracticeFamilies } from './coursePracticeVariants';
export type PracticeTheme = 'everyday' | 'football' | 'robots';
export type PracticeQuestion = { id: string; prompt: string };
export type PracticeExercise = { prompt: string; answer: string; scaffold: string; explanation: string; caseSensitive?: boolean };
export type PracticeFamily = { id: string; language: 'en' | 'de'; title: string; variants: Record<PracticeTheme, PracticeExercise> };
export const practiceThemes: { id: PracticeTheme; label: string }[] = [
  { id: 'everyday', label: 'Kundalik hayot' }, { id: 'football', label: 'Futbol' }, { id: 'robots', label: 'Robotlar' },
];
const exercise = (prompt: string, answer: string, scaffold: string, explanation: string, caseSensitive = false): PracticeExercise => ({ prompt, answer, scaffold, explanation, caseSensitive });
// Only supplemental answers live here. Never import a graded question bank into this helper.
export const practiceFamilies: readonly PracticeFamily[] = [
  { id: 'en-noun', language: 'en', title: 'Otni ajratish', variants: {
    everyday: exercise('The cup is clean. Buyum nomini bildirgan otni yozing.', 'cup', 'Nima? deb so‘rang. Buyum nomini uning belgisidan ajrating.', 'Cup — piyola, buyum nomi. Clean uning holatini bildiradi.'),
    football: exercise('The stadium is huge. Joy nomini bildirgan otni yozing.', 'stadium', 'Qaysi so‘z joy nomi? Huge uning qandayligini aytadi.', 'Stadium — stadion, joy nomi. Huge — katta degan sifat.'),
    robots: exercise('The sensor is new. Buyum nomini bildirgan otni yozing.', 'sensor', 'Qaysi so‘z qurilma qismini nomlayapti?', 'Sensor qurilma qismining nomi, shuning uchun ot. New — sifat.'),
  } },
  { id: 'en-adjective', language: 'en', title: 'Sifatni ajratish', variants: {
    everyday: exercise('The warm soup is ready. Soup oldidagi sifatni yozing.', 'warm', 'Sho‘rva qanday? Ot oldidagi belgini toping.', 'Warm — iliq; soup otini tavsiflaydi.'),
    football: exercise('The fast goalkeeper wins. Goalkeeper oldidagi sifatni yozing.', 'fast', 'Darvozabon qanday? Bu gapda fast shaxsni tavsiflaydi.', 'Fast goalkeeper birikmasida fast — tezkor degan sifat.'),
    robots: exercise('The shiny machine works. Machine oldidagi sifatni yozing.', 'shiny', 'Mashina qanday? Harakatni emas, uning belgisini toping.', 'Shiny — yaltiroq; machine otini tavsiflaydi. Works — fe’l.'),
  } },
  { id: 'en-verb', language: 'en', title: 'Harakat fe’lini ajratish', variants: {
    everyday: exercise('We cook dinner. Harakat fe’lini yozing.', 'cook', 'Nima qilamiz? degan savolga javob bo‘lgan so‘zni toping.', 'Cook — ovqat pishirmoq, ega bajarayotgan harakat.'),
    football: exercise('The players kick the ball. Harakat fe’lini yozing.', 'kick', 'O‘yinchilar nima qiladi? Buyum yoki shaxs nomini tanlamang.', 'Kick — tepmoq. Players — ega, ball — harakat yo‘nalgan buyum.'),
    robots: exercise('The robots lift boxes. Harakat fe’lini yozing.', 'lift', 'Robotlar nima qiladi? Harakatni toping.', 'Lift — ko‘tarmoq, robotlar bajarayotgan harakat. Boxes — ot.'),
  } },
  { id: 'de-capital-noun', language: 'de', title: 'Nemischa otning bosh harfi', variants: {
    everyday: exercise('Otni bosh harf bilan yozing: die ___ (tasse).', 'Tasse', 'Nemis tilida barcha otlar bosh harf bilan boshlanadi.', 'Tasse — ot: T bosh harf bilan yoziladi. Artikli die.', true),
    football: exercise('Otni bosh harf bilan yozing: der ___ (ball).', 'Ball', 'Bu so‘z buyum nomi. Birinchi harfni bosh harfga aylantiring.', 'Ball — ot: B bosh harf bilan yoziladi. Artikli der.', true),
    robots: exercise('Otni bosh harf bilan yozing: der ___ (roboter).', 'Roboter', 'Qavsdagi otning birinchi harfini tekshiring.', 'Roboter — ot: R bosh harf bilan yoziladi. Artikli der.', true),
  } },
  { id: 'de-sein', language: 'de', title: 'Sein: hozirgi zamon tasdiq gapi', variants: {
    everyday: exercise('Ich ___ zu Hause. (sein, Präsens)', 'bin', 'Bu qo‘shimcha gapning egasi ich. Shu egaga mos sein shaklini eslang.', 'Ich bilan sein hozirgi zamonda bin bo‘ladi: Ich bin zu Hause.'),
    football: exercise('Ich ___ im Stadion. (sein, Präsens)', 'bin', 'Joy o‘zgarsa ham ega ich bo‘lib qoladi. Fe’lni egaga moslang.', 'Ich bin im Stadion — men stadiondaman. Ich uchun bin ishlatiladi.'),
    robots: exercise('Ich ___ ein Roboter. (sein, Präsens)', 'bin', 'Robot o‘zi haqida ich deb gapiryapti. Sein fe’lini shu egaga moslang.', 'Ich bin ein Roboter — men robotman. Ich uchun bin ishlatiladi.'),
  } },
  ...extendedPracticeFamilies,
];
const deInstruction = 'Bo‘shliqni ko‘rsatmaga muvofiq to‘ldiring. Faqat yetishmayotgan qismni yozing; gapni to‘liq ko‘chirmang. ';
// Audited public prompt + identity pairs. Topic/lesson alone is insufficient:
// e.g. g001 also tests umlauts, and a broad "sein" match could include negation.
const supported: readonly [string, string, string][] = [
  ['grammar:1.1:0', 'Otni yozing: happy / pencil / slowly.', 'en-noun'],
  ['grammar:1.2:0', 'Sifatni yozing: blue / bag / jump.', 'en-adjective'],
  ['grammar:1.2:1', 'The tiny robot is here. Robotni tavsiflovchi sifatni yozing.', 'en-adjective'],
  ['grammar:1.3:0', 'Harakat fe’lini yozing: chair / dance / red.', 'en-verb'],
  ['grammar:1.3:1', 'We laugh. Gapdagi fe’lni yozing.', 'en-verb'],
  ['g001-q1', deInstruction + 'Otni bosh harf bilan yozing: das ___ (buch).', 'de-capital-noun'],
  ['g003-q1', deInstruction + 'Du ___ heute hier. (sein, Präsens)', 'de-sein'],
  ['g003-q2', deInstruction + 'Wir ___ aus Samarkand. (sein, Präsens)', 'de-sein'],
  ['g003-q3', deInstruction + 'Ihr ___ sehr freundlich. (sein, Präsens)', 'de-sein'],
];
export function getPracticeFamily(question: PracticeQuestion, language: string, lesson: number): PracticeFamily | undefined {
  if (!['en', 'de'].includes(language) || !Number.isInteger(lesson) || lesson < 1) return;
  const match = supported.find(([suffix, prompt]) => question.id === `${language}:${lesson}:${suffix}` && question.prompt === prompt);
  if (match) return practiceFamilies.find(f => f.id === match[2] && f.language === language);
  const prefix = language + ':' + lesson + ':';
  if (!question.id.startsWith(prefix)) return;
  const suffix = question.id.slice(prefix.length);
  const parts = language === 'en' ? /^grammar:(\d+\.\d+):(\d+)$/.exec(suffix) : /^(g\d{3})-(q\d+)$/.exec(suffix);
  if (!parts) return;
  const rule = auditedTopics.find(row => row.language === language && row.topic === parts[1]);
  // Closed allowlist: an unreviewed question within a known topic still falls back.
  if (!rule || (rule.prompts as Partial<Record<string, string>>)[parts[2]] !== question.prompt) return;
  return practiceFamilies.find(f => f.id === rule.family && f.language === language);
}
export function checkPracticeAnswer(exercise: PracticeExercise, answer: string): boolean {
  const normalize = (s: string) => {
    const trimmed = s.normalize('NFC').trim();
    return exercise.caseSensitive ? trimmed : trimmed.toLowerCase();
  };
  return normalize(answer) === normalize(exercise.answer);
}
export function practiceThemeKey(family: PracticeFamily): string { return `jony:practice-theme:v1:${family.language}:${family.id}`; }
export function readPracticeTheme(family: PracticeFamily): PracticeTheme {
  try {
    const saved = localStorage.getItem(practiceThemeKey(family));
    return practiceThemes.find(t => t.id === saved)?.id ?? 'everyday';
  } catch { return 'everyday'; }
}
export function savePracticeTheme(family: PracticeFamily, theme: PracticeTheme): void {
  try { localStorage.setItem(practiceThemeKey(family), theme); } catch { /* Optional preference; private mode must not block practice. */ }
}
