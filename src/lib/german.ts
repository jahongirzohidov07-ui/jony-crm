import vocabulary1 from '../data/german/vocabulary-1.json';
import vocabulary2 from '../data/german/vocabulary-2.json';
import vocabulary3 from '../data/german/vocabulary-3.json';
import grammarData from '../data/german/grammar.json';
import lessonData from '../data/german/lessons.json';
import skillsData from '../data/german/skills.json';
import { shuffled } from './intensive';
import type { Question, Word } from './intensive';

export type GermanWord = Word & { week: number; forms: string };
export type GermanTopic = { id: string; level: string; title: string; rule: string; example: string; translation: string; questions: Question[] };
export type GermanLesson = { no: number; week: number; month: number; level: string; title: string; topicIds: string[]; objective: string; teacherTip: string; supportTask: string; homework: string[]; checkpoint: boolean };
export type GermanSkills = { no: number; reading: { title: string; text: string; questions: Question[] }; listening: { title: string; text: string; questions: Question[] }; speaking: { task: string; model: string; criteria: string[] }; writing: { task: string; model: string; criteria: string[] } };
export const germanWords: GermanWord[] = [...vocabulary1, ...vocabulary2, ...vocabulary3];
export const germanGrammar = (grammarData as GermanTopic[]).map(topic => ({ ...topic, questions: topic.questions.map(q => ({ ...q, caseSensitive: q.caseSensitive ?? true })) }));
export const germanLessons = lessonData as GermanLesson[];
export const germanSkills = skillsData as GermanSkills[];
export const germanMonths = ['A1 · Talaffuz va gap poydevori', 'A1 · Kundalik hayot', 'A2 · O‘tmish va tajriba', 'A2 · Mustaqil muloqot', 'B1 · Fikr va dalil', 'B1 · Integratsiya va imtihon'];
export function lessonWords(no: number) {
  const week = Math.ceil(no / 3), day = (no - 1) % 3;
  return germanWords.filter(w => w.week === week).slice(Math.floor(day * 100 / 3), Math.floor((day + 1) * 100 / 3));
}
export function supportWords(no: number) {
  const week = Math.ceil(no / 3), last = lessonWords(no).at(-1)?.id ?? 0;
  return shuffled(germanWords.filter(w => w.week >= Math.max(1, week - 1) && w.id <= last), no).slice(0,20);
}
export function germanWordPractice(pool: GermanWord[], mixed = false): Question[] {
  return shuffled(pool, pool[0]?.id ?? 1).map((w, i) => {
    const explanation = `${w.word} ${w.ipa} — ${w.meaning}. ${w.forms} ${w.example}`;
    if (mixed && i % 3 === 2) return { id: `de-v-${w.id}`, prompt: `Imloni tiklang (artikl bo‘lsa, birga yozing): ${shuffled([...w.word], w.id).join(' · ')}`, answers: [w.word], hint: w.meaning, explanation, caseSensitive: true };
    const match = w.word.match(/^(der|die|das)\s+(.+)$/);
    if (match && i % 2) return { id: `de-v-${w.id}`, prompt: `Artiklni yozing: ___ ${match[2]}`, answers: [match[1]], hint: w.meaning, explanation };
    return { id: `de-v-${w.id}`, prompt: `Nemischa yozing${match ? ' (artikl bilan)' : ''}: ${w.meaning}`, answers: [w.word], hint: `${w.topic} · Shu to‘plamdagi so‘z. Bosh harf va umlautga e’tibor bering.`, explanation, caseSensitive: true };
  });
}
/** Legacy general outline; UI/PDF use germanLessonTimeline(no). */
export const mainTimeline: [number, string, string][] = [
  [10, 'Eslash va uy vazifasi', 'Oldingi darsdan 5 so‘z va 2 gapni daftarsiz ayttiring. Ikki ko‘p uchragan xatoni doskada tuzating.'],
  [20, 'Grammatika: ma’no → shakl', 'Bugungi mavzu kartalaridagi qoida va namunalarni ishlating. Avval vaziyatni tushuntiring, keyin ega, fe’l va kelishikni belgilang. O‘quvchi o‘z misolini aytsin.'],
  [15, 'Boshqariladigan mashq', 'Mavzu mashqlarini mustaqil bajartiring. Juftlikda solishtiring, javobni sabab bilan tekshiring.'],
  [15, 'Lug‘at: faol 12–15 so‘z', 'Faol to‘plam: talaffuz, artikl, misol, tarjimani yopib eslash. Ustoz 5 ta so‘zni qayta so‘rasin.'],
  [5, 'Faol tanaffus', 'Turib harakat bilan beshta fe’lni ko‘rsating.'],
  [15, 'Lug‘at va o‘qish', 'Qolgan so‘zlarni retseptiv tanish uchun ko‘rsating; faol yodlash talab qilinmaydi. Bugungi Lesen matnini o‘qiting; javobning dalilini matndan topdiring.'],
  [15, 'Tinglash', 'Hören matnini avval umumiy ma’no, keyin tafsilot uchun ikki marta o‘qing yoki nemischa ovozda eshittiring. Transkriptni tekshiruvgacha yopiq saqlang.'],
  [15, 'Gapirish va yozish', 'Sprechen topshirig‘ini juftlikda bajartiring. Schreiben topshirig‘i uchun 3 bandli reja va dastlabki gaplarni yozdiring.'],
  [10, 'Chiqish bileti', '3 lug‘at va 2 grammatika bandini tekshiring. Qiyin bandlarni support ustozga aniq yetkazing; bugungi uy vazifasini belgilang.'],
];
export const orientationTimeline: [number, string, string][] = [
  [10, 'Kurs xaritasi va tartib', 'A1 → A2 → B1 yo‘lini ko‘rsating. Asosiy dars, support, mustaqil ish va nazorat vazifalarini ayting. Har o‘quvchi xato daftari va lug‘at daftarini tayyorlasin.'],
  [20, 'Alifbo va tovushlar', 'Ismni harflab aytishdan boshlang. ä, ö, ü, ß, ch, sch, ei va ie ni eshittiring, o‘quvchilar qaytarsin. Og‘iz holatini ko‘rsating; mukammallikni emas, farqni eshitishni tekshiring.'],
  [20, 'Birinchi grammatika', 'Bugungi mavzu kartalarini oching. Ich, du va hurmat Sie olmoshlarini vaziyatda ajrating. Tayyor tanishuv iborasini harflab aytish bilan bog‘lang; hali o‘tilmagan fe’l shaklini qoida sifatida talab qilmang.'],
  [15, 'Birinchi 10 so‘z', 'Talaffuz → ma’no → misol → tarjimani yopib eslash tartibini amalda ko‘rsating. 10 so‘zli mashqni birga boshlang.'],
  [5, 'Faol tanaffus', 'Salomlashib, yangi juft toping.'],
  [20, 'Dars lug‘atining qolgan qismi', 'Faol 10 so‘zni tanishuvda ishlating. Qolganlari retseptiv: ma’noni tanish; supportda faol so‘zlar qaytariladi.'],
  [15, 'Birinchi o‘qish va tinglash', 'Bugungi qisqa matnlarni ishlating. Ism va asosiy ma’lumotni topdiring, transkriptni tekshiruvdan keyin ko‘rsating.'],
  [10, 'O‘zim haqimda', 'Darsdagi speaking va writing topshirig‘idan boshlang‘ich namunani bajartiring. Har o‘quvchi kamida ikki gap aytsin.'],
  [5, 'Uy vazifasini ko‘rsatish', 'Bir so‘zni yodlash va bitta gapni tekshirishni namuna qiling. Keyingi supportga nimalar olib kelishini ayting.'],
];
export function finalWeekTimeline(no: number): [number, string, string][] {
  const opening: [number,string,string] = [10,'Rasmiy material va ko‘rsatma','Goethe B1 bo‘limidagi rasmiy namunaning kattalar/yoshlar uchun mos variantini oching. Ko‘rsatma va javob varag‘ini tushuntiring. Ichki qisqa mashqni to‘liq sinov deb hisoblamang.'];
  const vocabulary: [number,string,string] = [20,'Lug‘atni mustahkamlash','Bugungi 10 faol so‘zni kichik guruhlarda ko‘rib chiqing. Qolgan to‘plam retseptiv tanish uchun saqlanadi. Supportda shu faol IDlarni qaytaring; yangi grammatika kiritmang.'];
  if (no === 70) return [opening,[65,'Lesen · vaqt bilan','Rasmiy namunaning to‘liq Lesen modulini mustaqil bajartiring. Vaqt tugamaguncha javoblarni ochmang.'],vocabulary,[25,'Dalil va xato tahlili','Kalit bilan solishtiring. Har xato uchun matndagi dalilni topdiring; supportga eng qiyin ikki savol turini belgilang.']];
  if (no === 71) return [opening,[40,'Hören · rasmiy audio','Goethe namunasidagi to‘liq audio va ko‘rsatmalar bilan ishlang. Ichki sintetik ovozni ushbu sinovga almashtirmang.'],vocabulary,[30,'Sprechen · juftlik','Rejalash, taqdimot va savol-javobni juftliklarda mashq qiling. Ustoz navbat bilan kuzatadi; har o‘quvchini alohida baholash uchun qo‘shimcha navbat belgilang.'],[20,'Xato tahlili','Tinglashdagi dalil va gapirishdagi takroriy xatolarni yozdiring. Supportda qayta bajariladigan bandlarni tanlang.']];
  return [opening,[60,'Schreiben · vaqt bilan','Rasmiy namunaning yozuv topshiriqlarini mustaqil bajartiring. Namuna javobni oldindan ko‘rsatmang.'],vocabulary,[15,'Yozuvni tekshirish','Rasmiy mezonlar asosida ustoz tekshiruvi uchun ishlarni yig‘ing. Juftlikda topshiriq bandlari bajarilganini ko‘rib chiqing.'],[15,'Shaxsiy keyingi reja','To‘rt modul bo‘yicha kuchli va zaif joylarni yozing. Zarur bo‘lsa qo‘shimcha support va qayta sinov belgilang; kurs tugashi avtomatik sertifikat tayyorligi emas.']];
}
export const supportTimeline: [number, string, string][] = [
  [10, 'Xato va uy vazifasi', 'Asosiy ustoz ajratgan xatolarni tekshiring. Javobni aytishdan oldin o‘quvchiga tuzatish imkonini bering.'],
  [10, 'Talaffuz va artikl', 'Bugungi so‘zlardan 10 tasini ayttiring. Urg‘u, umlaut va otning artiklini birga mashq qiling.'],
  [15, 'Aralash qaytarish', 'Bugungi va avvalgi hafta so‘zlaridan 20 talik aralash mashq. So‘ng asosiy dars grammatikasidan 3 yangi gap.'],
  [15, 'Amaliy juftlik', 'Darsdagi support topshirig‘ini bajaring. Rollarni almashtiring; har o‘quvchi gapirsin.'],
  [5, 'Tinglash ortidan takrorlash', 'Bugungi Hören matnidan 3 jumlani tinglab, bo‘laklab va to‘liq qaytaring.'],
  [5, 'Qayta tekshirish', 'Boshida xato qilingan 3 bandni yana so‘rang. Keyingi mustaqil ishni belgilang.'],
];
/** Legacy 75-minute outline; differentiated daily tasks are in germanTeacherKit. */
export const independentWork: [number, string, string][] = [
  [20, 'So‘zlarni faol eslash', 'Yangi so‘zlarning yarmini asosiy dars kuni, qolganini support kuni mustahkamlang. 1, 3 va 7 kundan so‘ng qaytaring.'],
  [20, 'Grammatika', 'Bugungi mavzu mashqlarini bajaring va har qoida bilan ikki shaxsiy gap tuzing.'],
  [15, 'O‘qish yoki tinglash', 'Bugungi matn va savollarni takrorlang. Uchta foydali iborani yozing.'],
  [15, 'Gapirish yoki yozish', 'Darsdagi topshiriqni yakunlang: asosiy dars kuni yozuv, support kuni ovozli nutq.'],
  [5, 'Xatolar daftari', 'Xato → to‘g‘ri variant → sabab shaklida uchta qayd.'],
];
export const goetheInfo = 'https://www.goethe.de/ins/de/de/prf/gzb1.cfm';
export const goethePractice = 'https://www.goethe.de/ins/dk/de/spr/prf/ueb/pb1.html';
