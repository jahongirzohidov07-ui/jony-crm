import modules from '../data/intensive-grammar-map.json';
import wordData from '../data/intensive-vocabulary.json';
import checks from '../data/intensive-checks.json';
import notes from '../data/intensive-teacher-notes.json';

export type Word = { id: number; topic: string; word: string; ipa: string; meaning: string; example: string; translation: string };
export type Question = { id: string; prompt: string; answers: string[]; explanation: string; hint?: string };
export const words: Word[] = wordData;
export const grammar = modules;
export const teacherNotes = notes;
export const monthNames = ['Fundament: gap va so‘z', 'Kundalik muloqot', 'O‘tmish va kelajak', 'Natija, taqqoslash, modallar', 'Shart va taxmin', 'Murakkab gaplar', 'Aniqlik va ko‘nikmalar', 'Integratsiya va yakuniy takrorlash'];
export const topics = modules.flatMap((m, mi) => m.items.map(([title, example], ti) => ({ id: `${mi + 1}.${ti + 1}`, module: mi, title, example, goal: m.goal })));
// 27 foundation-to-B2 modules, followed by five spiral-review weeks.
export const weekModules = Array.from({ length: 32 }, (_, i) => i < 27 ? [i] : [[0,1,2,3,4,5,6,7],[8,9,10,11,12],[13,14,15,16,17,18],[19,20,21,22,23],[24,25,26]][i-27]);
export const normalizeAnswer = (value: string) => value.normalize('NFKC').toLocaleLowerCase('en').replace(/[’‘`]/g, "'").replace(/[.!?,;:]/g, '').replace(/\s+/g, ' ').trim();
export const isCorrect = (value: string, answers: string[]) => answers.some(answer => normalizeAnswer(answer) === normalizeAnswer(value));
export function shuffled<T>(items: readonly T[], seed = 1): T[] {
  const result = [...items]; let state = seed >>> 0;
  for (let i = result.length - 1; i > 0; i--) { state = (Math.imul(state,1664525)+1013904223)>>>0; const j=state%(i+1); [result[i],result[j]]=[result[j],result[i]]; }
  return result;
}
export function vocabularyPractice(pool: Word[], mixed = false): Question[] {
  return shuffled(pool, pool[0]?.id ?? 1).map((w, i) => {
    const mode = mixed ? i % 3 : i % 2;
    const escaped = w.word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(`(?<![a-z])${escaped}(?:s|es)?(?![a-z])`, 'i');
    const match = w.example.match(pattern);
    if (mode === 1 && match) return { id: `v-${w.id}`, prompt: w.example.replace(pattern,'_____'), answers:[match[0]], hint:w.translation, explanation:`${w.word} ${w.ipa} — ${w.meaning}. ${w.example}` };
    if (mode === 2) return { id:`v-${w.id}`, prompt:`So‘zning imlosini tiklang: ${shuffled([...w.word],w.id).join(' · ')}`, answers:[w.word], hint:w.meaning, explanation:`${w.word} — ${w.meaning}. ${w.example}` };
    return { id:`v-${w.id}`, prompt:`Inglizcha bosh so‘zni yozing: ${w.meaning}`, answers:[w.word], hint:`Shu to‘plamdan so‘z. ${w.word.length} ta belgi.`, explanation:`${w.word} ${w.ipa}. ${w.example}` };
  });
}
export function grammarChecks(moduleIds: number[]): Question[] {
  return shuffled(moduleIds.flatMap(mi => checks[mi].map(([prompt, answer, explanation],i) => ({ id:`g-${mi}-${i}`, prompt, answers:[answer], explanation }))), 71);
}
export function topicPractice(id: string): Question[] {
  const topic = topics.find(t=>t.id===id);
  if (!topic) return [];
  // Exact model recall is labelled as such; independent grammar production is teacher assessed.
  return [{ id:`model-${id}`, prompt:`Namunani tiklang: ${shuffled(topic.example.split(' '), Number(id.replace('.',''))).join(' / ')}`, answers:[topic.example], explanation:`Namuna: ${topic.example}`, hint:'Xaritadagi namuna tartibini tiklang. Bu yangi gapni erkin baholash testi emas.' }];
}
export function grammarReview(moduleIds: number[]): Question[] {
  return shuffled([...grammarChecks(moduleIds), ...topics.filter(t=>moduleIds.includes(t.module)).flatMap(t=>topicPractice(t.id))], moduleIds[0]+17).slice(0,20);
}
export function lessonPlan(no: number) {
  const safe = Math.min(192, Math.max(1, Math.trunc(no)||1));
  const week=Math.ceil(safe/6), day=(safe-1)%6+1, month=Math.ceil(week/4);
  const moduleIds=weekModules[week-1];
  const allTopics=topics.filter(t=>moduleIds.includes(t.module));
  const assigned=day===6 ? allTopics : allTopics.slice(Math.floor((day-1)*allTopics.length/5),Math.floor(day*allTopics.length/5));
  const from=(week-1)*125+(day-1)*25+1;
  const start=day===6?(week-1)*125+1:from;
  const end=day===6?week*125:from+24;
  const available=words.filter(w=>w.id>=start&&w.id<=end);
  return {no:safe,week,day,month,review:day===6, moduleIds,topics:assigned, start,end,words:available,wordsReady:available.length===end-start+1,
    title:day===6?'Haftalik takrorlash va nazorat':assigned.map(t=>t.title).join(' · ')};
}
export const standardTimeline = [
  [10,'Eslash va uy vazifasi','Kecha o‘tilgan 5 so‘zni tarjimasiz ayttiring. Uy vazifasidan 2 gapni doskada tekshiring. Xatoni yozib oling, darhol uzun izoh bermang.'],
  [20,'Grammatikani ochib berish','Quyidagi har bir mavzuning namunasini ko‘rsating. Ega va fe’lni rang bilan ajrating; shakl va ma’noni savollar bilan aniqlating. Namuna → birga gap → o‘quvchining gapi tartibida ishlang.'],
  [15,'Boshqariladigan mashq','Mavzu kartalaridagi namuna tiklash mashqini bajartiring. Juftlar javobini solishtirsin. Ikki o‘quvchi nega shu tartibni tanlaganini tushuntirsin.'],
  [15,'Vocabulary — birinchi 10 so‘z','So‘z → IPA → kulgili misol → tasavvur → tarjimani yopib eslash. Har so‘zdan keyin birga va yakka talaffuz. Shu 10 so‘z mashqini oching.'],
  [5,'Faol tanaffus','O‘quvchilar tursin: ustoz so‘z aytadi, ular harakat yoki mimika bilan ko‘rsatadi.'],
  [15,'Vocabulary — keyingi 15 so‘z','Keyingi 10 so‘zni o‘rgating; 20 so‘zli aralash mashq bilan tekshiring. Qolgan 5 so‘zni misolda tanishtiring, uyda qaytarilsin.'],
  [15,'Reading va listening','Quyidagi 3 ta misolni ustoz ikki marta o‘qiydi: birinchisida mazmun, ikkinchisida aniq so‘zlar. O‘quvchi tarjimasiz tinglab yozadi, so‘ng matn bilan solishtiradi.'],
  [15,'Speaking va writing','Juftlar: yangi grammatikada kamida 3 gap, bugungi lug‘atdan 5 so‘z. Biri gapiradi, ikkinchisi qoida bo‘yicha tekshiradi. So‘ng 4 gaplik kichik matn yoziladi.'],
  [10,'Chiqish bileti va uyga vazifa','3 lug‘at + 2 grammatika savoli. 4/5 dan past bo‘lsa, keyingi dars boshida qayta mashq qildiring. Uy vazifasining bir bandini sinfda namuna qilib ko‘rsating.'],
] as const;
export const reviewTimeline = [
  [10,'Xotiradan qaytarish','Daftarsiz: hafta mavzulari va 10 so‘zni ayttiring.'],
  [20,'Aralash grammatika','Haftalik nazorat savollari va mavzu kartalaridan 5 ta namuna tiklash topshirig‘ini bajartiring.'],
  [20,'Aralash vocabulary','Hafta so‘zlaridan 20 tasini tanlab, tarjima, bo‘shliq va imlo mashqlarini bajartiring.'],
  [5,'Tanaffus','Yengil harakat; javoblarni bu paytda ko‘rsatmang.'],
  [20,'Tinglash va o‘qish','Hafta davomida ishlatilgan misollarni matnsiz o‘qing. Mazmunini ayttiring, so‘ng matn bilan xatolarni tuzating.'],
  [20,'Gapirish va yozish','Har o‘quvchi 1 daqiqa gapirsin va 5 gap yozsin. To‘g‘ri shakl, ma’no va yangi so‘zlarni tekshiring.'],
  [15,'Xatolar klinikasi','Eng ko‘p takrorlangan 3 xatoni doskaga anonim yozing. Juftlar tuzatsin, yangi o‘xshash misol yaratsin.'],
  [10,'Natija va qayta mashq','80% dan past bo‘lgan bandlarni ajrating. O‘quvchiga qaysi mashqni qayta bajarishini aniq yozing.'],
] as const;
export const homework = [
  [25,'Vocabulary','Bugungi so‘zlarni yopib eslang. 10 va 20 so‘zli mashqlarni bajaring; noto‘g‘ri javoblarni alohida qaytaring.'],
  [25,'Grammar','Har mavzu bo‘yicha 2 ta yangi gap yozing. Namuna tiklash va bo‘lim savollarini bajaring.'],
  [20,'Reading','Bugungi misollarni o‘qing. 5 ta yangi so‘zni belgilang va gap ichidagi ma’nosini tushuntiring.'],
  [20,'Listening','Darsdagi 3 gapni sherigingizga o‘qiting yoki yozib oling. Matnni yopib ikki marta tinglang, keyin tekshiring.'],
  [15,'Speaking','Bugungi mavzu va 5 yangi so‘z bilan 60–90 soniya gapiring. Yozuvni tinglab bitta xatoni tuzating.'],
  [15,'Writing va xato daftari','4–6 gapli kichik matn yozing. 3 ta xatoni “xato → to‘g‘ri → sabab” shaklida qayd eting.'],
] as const;
