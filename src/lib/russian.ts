import p1 from '../data/russian/part-1.json';
import p2 from '../data/russian/part-2.json';
import p3 from '../data/russian/part-3.json';
import p4 from '../data/russian/part-4.json';

export type RussianLesson = {
  no:number; month:number; week:number; title:string; objective:string;
  grammar:{title:string;rule:string;examples:{ru:string;uz:string}[];exercises:{prompt:string;answer:string;explanation:string}[]};
  phrases:{ru:string;uz:string}[];
  dialog:{speaker:string;ru:string;uz:string}[];
  questions:{prompt:string;answer:string}[];
  roleplay:{a:string;b:string;twist:string;success:string};
  teacherTip:string;homework:string[];exit:string;
};
export const russianLessons:RussianLesson[] = [...p1,...p2,...p3,...p4];
export const russianMonths = ['Ilk suhbat va talaffuz','Oila, sonlar va vaqt','Kundalik hayot','Xarid va kafe','Shahar va yo‘l','Voqealar va rejalar','Uy-joy va tanlov','Yordam va uchrashuvlar','Ish va o‘qish','Safar va muammolar','Fikr va hikoya','Mustaqil muloqot'];
export const russianTimeline = [
  [10,'Eslash va uy vazifasi','Oldingi darsdan 3 iborani yordamsiz ayttiring. Ovozli uy vazifasidan bitta yutuq va bitta tuzatish. Birinchi darsda kurs xaritasi va mashq tartibini tushuntiring.'],
  [10,'Talaffuz va iboralar','8 iborani namuna → birgalikda → individual usulida ayting. Urg‘u va eshitilgan tovushga e’tibor; ma’noni vaziyat bilan tekshiring.'],
  [15,'Grammatika','Ikki misoldan qoidani chiqaring. Uch mashqni individual bajartiring; keyin nima uchunligini juftlikda tekshirtiring.'],
  [15,'Tinglash va tushunish','Dialog matnini yoping. Ustoz ikki marta tabiiy, tushunarli sur’atda o‘qiydi: avval umumiy vaziyat, keyin 3 savol. Oxirida matnni oching.'],
  [5,'Tanaffus','Qisqa harakat va dam olish.'],
  [15,'Dialogni o‘zgartirish','Juftlikda A/B rollarni almashtiring. Ism, joy, vaqt yoki miqdorni almashtirib yangi suhbat tuzing.'],
  [25,'Vaziyatli suhbat','Har o‘quvchi faqat o‘z rolini ko‘radi. Tayyor dialogni o‘qimasdan maqsadga erishadi. Sherikni almashtiring; ustoz umumiy xatolarni qayd etadi.'],
  [10,'Yangi sharoit','Rol kartasidagi kutilmagan vaziyatni bering. Yodlangan gapni vaziyatga moslashtirsin.'],
  [10,'Yozish va uy vazifasi','Bugungi suhbatdan qisqa yozma xabar tuzing. Uch uy vazifasining namunasi va topshirish usulini ko‘rsating.'],
  [5,'Chiqish tekshiruvi','Darsdagi chiqish vazifasini matnsiz bajartiring. Ustoz keyingi dars uchun bitta shaxsiy tavsiya beradi.'],
] as const;
export const russianRubric = ['Vazifani bajarish','Tushunarli talaffuz','Savol-javob va sherikni tinglash','Iboralar va so‘z tanlash','Grammatik aniqlik'];
export const russianRubricGuide = 'Har mezon 0–4: 0 — bajarmadi; 1 — ko‘p yordam bilan; 2 — qisman mustaqil; 3 — asosan mustaqil; 4 — erkin va vaziyatga mos. Ichki o‘tish mezoni: jami kamida 14/20, vazifani bajarish va tushunarli talaffuz har biri kamida 2. Yetmagan mezonni mashq qilib qayta tekshiring. Bu sertifikat bahosi emas.';
