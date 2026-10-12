export type PlacementQuestion = {
  id: string; stage: number; skill: 'grammar' | 'vocabulary' | 'reading';
  topic: string; prompt: string; options: string[]; text?: string;
};
export type RussianPlacementResult = {
  score: number; stage: number | null; month: number | null; lesson: number | null;
  allPassed: boolean; label: string; gaps: string[];
  blocks: { stage: number; label: string; correct: number; total: number; grammar: number; reading: number; passed: boolean }[];
  recommendation: { branch_id: number; branch_name: string; stage: number | null; label: string; oral_required: boolean };
};
export const placementStages = [
  '1–2-oy: tanishuv va oila', '3–4-oy: kundalik hayot va xarid',
  '5–6-oy: shahar va sayohat', '7–8-oy: uy-joy va salomatlik',
  '9–10-oy: ish va xizmatlar', '11–12-oy: fikr va erkin suhbat',
];
export const oralRubric = [
  'Tinglab tushunish: ustoz ruscha 3–4 gap aytsin, o‘quvchi asosiy ma’lumot va ikki tafsilotni aytib bersin.',
  'Suhbat: tavsiya bosqichining mavzusida savol bersin, javob qaytarsin va tushunmagan joyini aniqlashtirsin.',
  'Mustaqil nutq: o‘z hayotidan misol aytsin; keyingi bosqichlarda voqea, reja va fikrini sabab bilan bog‘lasin.',
  'Tushunarlilik: talaffuz va grammatik xatolarga qaramay, suhbatdosh mazmunni tushuna olsin.',
];
export const oralDirections = 'Ustoz bilan 10–15 daqiqa. Har mezon: 0 — bajara olmadi, 1 — yordam bilan, 2 — mustaqil. Bu ballar avtomatik guruh tayinlamaydi. Ustoz suhbat natijasi va bo‘shliqlarni qayd etib, boshlanish darsini tasdiqlaydi; zarur bo‘lsa oldingi bosqichni tekshiradi. Barcha bloklar o‘tilsa, yakuniy suhbatda kundalik vaziyat, muammo yechimi va fikr bildirish tekshiriladi. Test til darajasini kafolatlamaydi.';

// Questions arrive from the server without the answer key. Scoring is server-only.
export async function publicRequest<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/public/russian-placement${path}`, {
    ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}), signal,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Ma’lumotlarni tekshirib qayta urinib ko‘ring.');
  return data;
}
