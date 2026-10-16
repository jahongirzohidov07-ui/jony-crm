import seeds from '../data/german/grammar-teaching.json';
import checkpointSeeds from '../data/german/teaching-checkpoints.json';
import { germanGrammar, germanLessons, germanWords, lessonWords, finalWeekTimeline, orientationTimeline } from './german';

export type TeachingExercise = { id: string; topicId: string; kind: 'production' | 'correction' | 'transfer'; prompt: string; model: string; guidance: string; criteria: string[] };
export type TeachingTimeline = [number, string, string][];
export const germanExamSource = { url: 'https://www.goethe.de/ins/de/de/prf/gzb1.cfm', checked: '2026-10-16', note: 'Lesen 65, Hören 40, Schreiben 60, Sprechen 15 daqiqa. Ichki qisqa mashqlar rasmiy modul sinovi emas.' };
export const germanTeachingExercises: TeachingExercise[] = germanGrammar.flatMap(topic => {
  const seed = seeds.find(s => s.topicId === topic.id);
  if (!seed) throw new Error(`Missing teaching material: ${topic.id}`);
  const questionRewrite = ['g005', 'g013', 'g017'].includes(topic.id);
  const criteria = ['Vaziyatdagi ma’no yetkazilgan.', `${topic.title}: maqsad shakli to‘g‘ri ishlatilgan.`, 'O‘quvchi tuzatish sababini ayta oladi va yangi misolda qo‘llaydi.'];
  return [
    { id: `${topic.id}-production`, topicId: topic.id, kind: 'production' as const, prompt: `${seed.context} So‘ralgan javobni mustaqil tuzing; g001/g002 da ism/harflar yoki olmoshning o‘zi yetarli.`, model: seed.model, guidance: `Bu mumkin bo‘lgan namuna, yagona javob emas. Ma’nosi va maqsad shakli mos boshqa javoblarni qabul qiling. ${topic.rule}`, criteria },
    { id: `${topic.id}-correction`, topicId: topic.id, kind: 'correction' as const, prompt: questionRewrite ? `«${seed.error}» intonatsiya bilan tasdiqni aniqlashtiruvchi savol bo‘lishi mumkin. Uni fe’l birinchi o‘rinda keladigan neytral ha/yo‘q savoliga qayta yozing; bu asl gapni noto‘g‘ri deb belgilash emas.` : `Vaziyat: ${seed.context} O‘quvchi shunday yozdi: «${seed.error}» Vaziyat va maqsad qoidasiga moslab tuzating; o‘zgarish sababini tushuntiring.`, model: seed.model, guidance: questionRewrite ? `Darak tartibli savol intonatsiya bilan mumkin; mashq talabi — neytral fe’l-birinchi savol: ${seed.model} Fe’lni birinchi o‘ringa ko‘chirish va ega bilan moslikni tekshiring; asl variantni grammatik xato deb baholamang.` : `«${seed.error}» → «${seed.model}». Ba’zi gaplar boshqa vaziyatda mumkin, lekin berilgan ma’no/shaklga mos emas. Tekshirish asosi: ${topic.rule}`, criteria },
    { id: `${topic.id}-transfer`, topicId: topic.id, kind: 'transfer' as const, prompt: seed.transfer, model: `Tayanch tuzilma: ${seed.model}`, guidance: `${topic.id === 'g001' || topic.id === 'g002' ? 'Birinchi dars: ism/harflar yoki olmosh kartasi yetarli; fe’l va yangi gap talab qilmang. g002 kaliti: ich; wir; Sie.' : 'Yangi shaxs, buyum yoki vaziyat bilan 2 gap yoki 2 replikali almashinuv talab qiling.'} Tayanchni aynan ko‘chirish yetarli emas. ${topic.rule} Sherik ma’noni qayta aytsin; ustoz bitta aniq tuzatishdan keyin qayta urinishni eshitsin.`, criteria },
  ];
});

export function germanVocabularyPlan(no: number) {
  const pool = lessonWords(no);
  const count = no === 1 || no % 12 === 0 || no >= 70 ? 10 : no <= 24 ? 12 : no <= 48 ? 12 : 15;
  const active = pool.slice(0, count);
  const receptive = pool.slice(count);
  // Previously assigned active words only; never silently assess the receptive bank.
  const reviewIds = [...new Set([no - 1, no - 3, no - 9].filter(n => n > 0).flatMap(n => lessonWords(n).slice(0, 3).map(w => w.id)))];
  return { activeIds: active.map(w => w.id), receptiveIds: receptive.map(w => w.id), reviewIds, active, receptive, review: germanWords.filter(w => reviewIds.includes(w.id)) };
}

export const germanCheckpointRubric = {
  objective: 'Lesen 3 + Hören 3 + grammatika 4 + faol lug‘at 4 = 14 ball. Har javobga 1 ball. Mazmuni mos qisqa javobni qabul qiling; grammatika bandida maqsad shakli shart. Boshqa mayda xatoni alohida qayd qiling.',
  speaking: ['Topshiriqning uch mazmuniy bandi', 'Sherikka javob va savol; navbat almashish', 'Tushunarlilik va o‘tilgan maqsad shakllari'],
  writing: ['Topshiriqning mazmuniy bandlari', 'Mantiqiy ketma-ketlik va adresatga moslik', 'O‘tilgan shakllar va tushunarli imlo'],
  anchors: 'Har mezon: 0 — dalil yo‘q yoki ma’no tushunarsiz; 1 — qisman, tayanch/yordam bilan; 2 — mustaqil va tushunarli, mayda xato mumkin. Nutq 6, yozuv 6; jami 26. Bu Goethe shkalasi emas.',
  decision: 'Davom etish mezoni: obyektiv bandlarda kamida 12/14, nutq va yozuvning har birida kamida 4/6, hech bir mezonda 0 yo‘q. Aks holda zaif ko‘nikmaga support, 3–7 kundan keyin yangi vaziyat bilan qayta tekshiruv. Guruh o‘rtachasi individual natija o‘rnini bosmaydi.',
};

export function germanCheckpoint(no: number) {
  const seed = checkpointSeeds.find(s => s.no === no);
  if (!seed) return null;
  const first = no - 11;
  const topicIds = [first, first + 2, first + 5, first + 8].map(n => germanLessons[n - 1].topicIds[0]);
  const grammar = topicIds.map((id, i) => germanTeachingExercises.find(e => e.id === `${id}-${i % 2 ? 'production' : 'correction'}`)!);
  const vocabulary = [first, first + 2, first + 5, first + 8].map(n => germanVocabularyPlan(n).active[0]).map(w => ({ id: w.id, prompt: `Nemischa yozing (ot bo‘lsa artikl bilan): ${w.meaning}`, answer: w.word }));
  return { ...seed, grammar, vocabulary, rubric: germanCheckpointRubric,
    administration: 'Yangi ichki matnlar: tayyor namunalarni avval ko‘rsatmang. Hören matnini ustoz tabiiy, aniq tezlikda ikki marta o‘qiydi; o‘quvchida transkript bo‘lmasin. Bu nazorat skripti kundalik dars MP3sidan alohida. Nutq juftliklarda: A1 juftiga 4 daqiqa (20 daqiqada ko‘pi bilan 4 juft), A2 juftiga 6 daqiqa (3 juft), B1 juftiga 8 daqiqa (2 juft). Navbatdan tashqaridagi juftlar mustaqil mashq qiladi. Supportning 15 daqiqasida A1 3 juft / A2 2 juft / B1 1 juft kuzatiladi; qolganlar keyingi supportlarga yoziladi. 60-darsdan keyin 61-dars supportida yangi grammatika bor: qolgan B1 juftlarini 62/63 va zarur keyingi supportlarga rejalang. O‘quvchi, sana, juft va kuzatilgan dalilni yozing. Kuzatilmagan ishga ball qo‘ymang; barcha bandlar kuzatilmaguncha yakuniy profil tugallanmagan.',
    retest: 'Supportda xato turini tushuntirib, o‘sha shakl bilan boshqa shaxs/joy/vaqtli ikki gap tuzdiring. Keyingi tekshiruv uchun o‘tgan, lekin nazoratda ishlatilmagan mavzudan yangi production bandi tanlang; yangi reading/listening uchun oldingi dars matnidan foydalaning va oldin ko‘rilganini qayd eting. Bu qayta tekshiruv natijasini alohida yozing.' };
}

export function germanOfficialPractice(no: number) {
  const module = ({ 61: 'Lesen', 64: 'Hören', 67: 'Schreiben', 70: 'Lesen', 71: 'Hören + Sprechen', 72: 'Schreiben' } as Record<number, string>)[no];
  if (!module) return null;
  return { module, url: 'https://www.goethe.de/ins/dk/de/spr/prf/ueb/pb1.html',
    material: no < 70 ? 'B1 Erwachsene → Prüfungstraining 1 → Kandidatenblätter; tegishli modulning to‘liq topshirig‘i, javob varag‘i va Lösungen/Bewertung. Hören uchun aynan Prüfungstraining 1 Hören B1 Erwachsene yozuvi.' : 'B1 Erwachsene → Prüfungstraining 2 → Kandidatenblätter; tegishli modul va o‘z audio/kaliti. Avval ishlatilmaganini tekshiring. Yoshlar guruhida mos B1 Jugendliche 1/2 juftligini tanlang.',
    validity: 'Ustoz sana, variant 1/2, modul va oldin ko‘rilgan/ko‘rilmaganini qayd etadi. Agar o‘sha variant qayta ishlatilsa, natija mashq/takror hisoblanadi, yangi diagnostika emas. Rasmiy kalit/rubrika bilan baholang; ichki 26 ballik nazorat shkalasini bu modulga qo‘llamang.',
    remediation: 'Eng qiyin ikki topshiriq uchun dalil/xato sababini belgilang. Keyingi supportda boshqa parcha yoki yangi vaziyat bilan qayta urinish; asl test javobini yodlash natija emas.' };
}

export function germanLessonTimeline(no: number): TeachingTimeline {
  const lesson = germanLessons[no - 1];
  if (!lesson) throw new RangeError(`Unknown German lesson ${no}`);
  if (no >= 70) return finalWeekTimeline(no);
  if ([61, 64, 67].includes(no)) {
    const exam = germanOfficialPractice(no)!;
    const rows: TeachingTimeline = [[5, 'Rasmiy materialni tayyorlash', exam.material],
      [no === 61 ? 65 : no === 64 ? 40 : 60, `${exam.module} · to‘liq rasmiy modul`, 'Ko‘rsatma, vaqt va javob varag‘ini saqlang; Hören faqat shu variantning rasmiy yozuvi. Kalitni vaqt tugamaguncha ochmang.'],
      [10, 'Faol lug‘at', 'Kitdagi 15 faol so‘z: ma’no va misol. Qolgan to‘plam retseptiv; supportda faol eslash.'],
      [5, 'Tanaffus', 'Qisqa harakat va dam.'],
      [no === 61 ? 20 : 25, 'Sprechen · hamma ishtirok etadi', 'Darsdagi speaking topshirig‘i: juftliklarda ikki davra, rollarni almashtirish, savol va javob.']];
    if (no === 64) rows.push([20, 'Lesen va yozma qayta aytish', 'Dars matnidan dalil toping, uning mazmunini yangi sherikka yozma xabar qiling.']);
    rows.push([15, 'Tahlil va grammatika vazifalarini taqsimlash', `${exam.remediation} Bugungi ${lesson.topicIds.join(', ')} yangi mavzulari supportning 20 daqiqalik o‘rgatish va 15 daqiqalik qo‘llash blokiga ko‘chiriladi. ${exam.validity}`]);
    return rows;
  }
  if (no === 1) return orientationTimeline.map(row => row[1] === 'Dars lug‘atining qolgan qismi'
    ? [row[0], '10 faol so‘zni vaziyatda ishlatish', 'Qolgan so‘zlarni faqat ma’nosini tanish uchun ko‘rsating. Faol 10 so‘z bilan tanishuv; sherik ismni yozib tekshirsin.'] : [...row]);
  if (germanCheckpoint(no)) return [
    [10, 'Tayyorlash va faol lug‘at', 'Bugungi 10 faol so‘zni tanishtiring. Nazoratda faqat avvalgi darslar lug‘ati baholanadi.'],
    [15, 'Bugungi ikki yangi mavzu', `${lesson.topicIds.join(', ')}: qisqa namuna va bir production bandi. Bugungi yangi shakllar nazorat bali tarkibiga kirmaydi; supportda davom etadi.`],
    [10, 'Grammatika va lug‘at nazorati', 'Kitdagi 4 grammatika va 4 lug‘at bandini mustaqil bajartiring.'],
    [15, 'Lesen nazorati', 'Kitdagi yangi matn va 3 savol.'], [15, 'Hören nazorati', 'Kit skriptini ikki marta o‘qing; 3 savolga mustaqil javob.'],
    [5, 'Tanaffus', 'Natijalarni hali ochmang.'], [20, 'Schreiben nazorati', 'Kitdagi yozuv topshirig‘i; uch mezon bo‘yicha 0–2 ball.'],
    [20, 'Sprechen nazorati', 'Kitdagi juftlik topshirig‘i. Tinglanmagan o‘quvchilar uchun support navbati yozilsin.'],
    [10, 'Dalil va support topshirig‘i', '14 obyektiv ball va ikki 6 ballik profilni alohida qayd eting. Har o‘quvchiga bitta aniq keyingi qadam.'],
  ];
  const titles = lesson.topicIds.map(id => germanGrammar.find(t => t.id === id)!.title).join('; ');
  const pattern = (no - 1) % 3;
  const exam = no >= 49 ? 'Imtihon formati bilan erta tanishuv: ' : '';
  const focus: TeachingTimeline = pattern === 0 ? [
    [20, 'Ma’no va shakl', titles], [15, 'Production va correction', 'Har mavzudan yangi production; keyin xato gapni sabab bilan tuzatish. 3 eski savol faqat qisqa diagnostika.'],
    [15, 'Lesen: dalil topish', 'Dars matnida javobga dalil belgilang; keyin qisqa qayta ayting.'], [10, 'Hören: mazmun va tafsilot', 'Saqlangan dars yozuvini ikki tinglash.'],
    [25, `${exam}juftlik va yozuv`, '15 daqiqa: har sherik gapiradi, savol beradi, rollar almashadi. 10 daqiqa: shu vaziyatdan yozma xabar. 49-darsdan mezon va topshiriq bandlariga e’tibor; bu to‘liq rasmiy modul emas.'],
  ] : pattern === 1 ? [
    [15, 'Qoidani vaziyatdan topish', titles], [15, 'Correction va transfer', 'Har mavzudan xato tahlili, so‘ng yangi shaxs va joy bilan ikki replika.'],
    [20, 'Hören va qayta aytish', 'Birinchi tinglashda maqsad; ikkinchisida dalil. 5 daqiqa juftlikda mazmunni ayting.'], [10, 'Lesen: muhim bandlar', 'Dars matnidagi uch muhim ma’lumotni toping.'],
    [25, `${exam}yozish va javob`, '15 daqiqa darsdagi yozuv topshirig‘i, 10 daqiqa sherik bilan savol-javob. 49-darsdan ko‘rsatma bandlari va adresatga moslikni vaqt bilan mashq qiling.'],
  ] : [
    [15, 'Qisqa grammatika klinikasi', titles], [10, 'Mustaqil production', 'Har mavzudan bir yangi gap; yordam talab qilgan joylarni qayd qiling.'],
    [15, 'Lesen va Hören', 'Qisqa o‘qish, ikki tinglash va dalilni solishtirish; qolgan savollar support uchun tanlanadi.'],
    [30, `${exam}muloqot ustaxonasi`, 'Dars speaking vaziyatida 2 davra: birinchi urinish, aniq tuzatish, yangi sherik bilan qayta urinish. Har kishi kamida 4 daqiqa jami gapirsin; 49-darsdan rejalash, fikr va savol-javobni navbatlang.'],
    [15, 'Yozma transfer', 'Dars writing topshirig‘ining qisqa variantini mustaqil bajaring; uch bandni tekshiring.'],
  ];
  return [[10, 'Eslash', 'Kitdagi avvalgi faol so‘z IDlari va ikki eski shaklni daftarsiz qaytaring.'],
    ...focus.slice(0, 2), [10, 'Faol lug‘at', 'Kitdagi 12–15 faol so‘zni artikl, talaffuz va bitta vaziyat bilan ishlating. Qolganlari tanib tushunish uchun.'],
    [5, 'Faol tanaffus', 'Yangi sherik toping va bitta savol bering.'], ...focus.slice(2),
    [10, 'Chiqish va qayd', '3 faol so‘z + har mavzudan bitta mustaqil gap. 2 xato namunasi, keyingi mashq va qayta tekshiruv vaqtini supportga yozing.']];
}

export function germanTeacherKit(no: number) {
  const lesson = germanLessons[no - 1];
  if (!lesson) throw new RangeError(`Unknown German lesson ${no}`);
  const vocab = germanVocabularyPlan(no);
  const ids = (numbers: number[]) => numbers.map(n => `#${n}`).join(', ') || 'Oldingi dars yo‘q';
  const support: TeachingTimeline = [
    [5, 'Asosiy ustoz qaydini o‘qish', 'Ustoz qaydi: o‘quvchi ___; xato gap ___; to‘g‘ri shakl ___; so‘z ID ___; mustaqil/yordam bilan ___; qayta tekshiruv sanasi ___.'],
    [10, 'Faol lug‘atni eslash', `${ids(vocab.activeIds)}. Avval aytish, keyin artikl va misol. Yangi retseptiv so‘zlarni majburiy yodlashga qo‘shmang.`],
    [10, 'Oraliqli takror va retseptiv tanish', `Oldingi faol IDlar: ${ids(vocab.reviewIds)}. Qolgan bugungi IDlar: ${ids(vocab.receptiveIds)} — ma’noni tanish; faqat 3–5 qiyinini matnda ko‘rsating.`],
    [10, 'Grammatika klinikasi', `${lesson.topicIds.join(', ')}: asosiy darsda bajarilmagan correction/transfer; o‘quvchi sababni tushuntirib yangi misol aytsin.`],
    [15, 'Juftlikda davom', `${lesson.supportTask} Har o‘quvchi kamida 3 daqiqa gapirsin; rollarni almashtiring. Nazoratdan qolgan individual baholash shu blokda navbat bilan.`],
    [5, 'Tinglab qayta aytish', 'Dars MP3sidan 2–3 jumla: tinglash, bo‘laklash, matnsiz mazmunni qayta aytish.'],
    [5, 'Qayta tekshiruv va javob qaydi', 'Dastlab xato bo‘lgan 3 faol so‘z va bitta yangi gap. Asosiy ustozga dalil + keyingi qadamni qaytaring.'],
  ];
  if ([61, 64, 67].includes(no)) {
    support.splice(0, support.length,
      [5, 'Rasmiy moduldan handoff', germanOfficialPractice(no)!.remediation],
      [10, 'Faol lug‘at va oldingi takror', `${ids(vocab.activeIds)}; oldingi faol IDlar ${ids(vocab.reviewIds)}. Retseptiv bank matnda tanish uchun saqlanadi.`],
      [20, 'Ko‘chirilgan yangi grammatika', `${lesson.topicIds.join(', ')}: har mavzuga 10 daqiqa. Vaziyat → namuna → maqsad shakli → production; ushbu mavzular tashlab ketilmaydi.`],
      [15, 'Yangi grammatikani qo‘llash', 'Har mavzudan correction/transfer. Juftlikda rollarni almashtiring; har kishi kamida 3 daqiqa nutq. Moduldagi xato turini yangi vaziyat bilan bog‘lang.'],
      [5, 'Modul xatosini qayta sinash', 'Oldingi xato turiga boshqa dalil yoki yangi jumla; yodlangan javob emas.'],
      [5, 'Chiqish va keyingi reja', 'Har yangi mavzudan mustaqil bitta gap; faol lug‘atdan 3 so‘z. Natijani asosiy ustozga qaytaring.']);
  }
  const deferredGrammar = [61, 64, 67].includes(no);
  const homework: TeachingTimeline = [
    [15, 'Faol so‘zlarni eslash', `${ids(vocab.activeIds)}: ma’nodan nemischaga, artikl bilan; keyin uchta qisqa vaziyatda ishlating. Qiyin 5 tasini belgilang, hammasini qayta ko‘chirmang.`],
    [10, 'Retseptiv lug‘at konteksti', `${ids(vocab.receptiveIds)}: 5–6 tasini tanlab lug‘atdagi misollarida ma’noni toping, o‘xshash ikki so‘zni farqlang. Keyingi support kuni boshqa 5–6 so‘zni tanlang. Barcha so‘zni yoddan aytish talab qilinmaydi.`],
    [15, deferredGrammar ? 'Oldingi grammatikani mustahkamlash' : 'Grammatika: production va correction', no === 1 ? 'g001: uch ismni harflab yozing; g002: shaxs rasmlariga ich/du/wir/ihr/sie/Sie kartalarini moslang. Yangi fe’l yoki mustaqil to‘liq gap kerak emas.' : deferredGrammar ? 'Bugungi yangi mavzular supportda o‘rgatiladi. Hozir oldingi dars mavzularidan ikki yangi production va bitta correction tanlang; namunani keyin tekshiring.' : 'Bugungi mavzulardan ikki yangi production va bitta correction tanlang. Namuna bilan solishtiring, xato sababini izohlang; shaklni ko‘chirish bilan cheklanmang.'],
    [20, 'Mustaqil o‘qish va tinglash', 'Darsning Lesen matnidan uch ma’lumotni matnsiz qayta ayting (10 daqiqa). MP3ni transkriptsiz tinglab ikki tafsilotni yozing, keyin tekshiring (10 daqiqa). 1-darsda ism, tovush va tanish iboralar yetarli.'],
    [15, 'Shaxsiy mahsulot va tekshirish', no === 1 ? 'O‘z ism kartangizni yozing va harflab ayting. Uch kishiga olmosh kartasi tanlang; sherik yoki ustoz namunasi bilan tekshiring. Talaffuzni qayta yozib farqni tinglang.' : `Asl topshiriqlar bankidan bitta mahsulot: ${lesson.homework[1] ?? lesson.homework[0]} 10 daqiqa yozing; 3 daqiqa og‘zaki ayting; 2 daqiqa bitta xatoni tuzating. Tugamaganini supportga olib keling.`],
  ];
  return { no, title: lesson.title, topicIds: lesson.topicIds, objective: lesson.objective,
    vocabulary: vocab, timeline: germanLessonTimeline(no), support, homework,
    supportDayHomework: [
      [15, 'Oraliqli faol takror', `Bugungi qiyin faol so‘zlar va ${ids(vocab.reviewIds)}. Daftarsiz eslash, so‘ng tekshirish; to‘g‘ri bo‘lgan so‘zlarni ko‘chirmang.`],
      [10, 'Yangi retseptiv kontekst', 'Asosiy kuni tanlanmagan 5–6 retseptiv so‘zning misolini o‘qing; ma’nosini taxmin qilib tarjima bilan tekshiring.'],
      [15, 'Supportdan keyingi grammatika', no === 1 ? 'Yangi ism diktanti va shaxs/olmosh kartalari; hali o‘tilmagan fe’lni yasash talab qilinmaydi.' : `${lesson.topicIds.join(', ')}: supportda o‘rgatilgan shakllardan ikki yangi transfer va bitta correction. Oldingi javobni yoddan takrorlamang.`],
      [20, 'Boshqa matn va tinglash', no === 1 ? 'Dars matni/yozuvidan ism va tovushlarni ajrating, yozuvni ikki qisqa tinglashga bo‘ling. Faqat tanish so‘z va iboralarni yozing.' : 'Oldingi darsning Lesen yoki Hören matnini tanlang. 10 daqiqa asosiy ma’no va dalil, 10 daqiqa matnsiz qayta aytish va tekshirish. Bugungi matnni yana ko‘chirish emas.'],
      [15, 'Yangi vaziyatda nutq', no === 1 ? 'Boshqa ismni harflang, o‘zingiz va sherik uchun olmosh tanlang; ikki yozuvni tinglab bitta tovushni yaxshilang.' : 'Support vaziyatiga yangi joy/vaqt qo‘shing: 2–3 daqiqa reja, 2 daqiqa nutq, tinglab tekshirish va ikkinchi urinish. Yakunda uch bandli yozma xulosa.'],
    ] as TeachingTimeline,
    workload: 'Mustaqil ish — 75 daqiqa, haftada 6 kun (3 asosiy + 3 support kuni, jami 450 daqiqa). Faol eslash, retseptiv kontekst, grammatika, o‘qish/tinglash va shaxsiy mahsulot alohida ishlanadi. Retseptiv bankni to‘liq faol yodlash talab qilinmaydi; qiyinchilikni ustozga qayd eting.',
    handoff: 'O‘quvchi ___ | faol so‘z ID va natija ___ | xato gap → tuzatish ___ | kerakli yordam ___ | support mashqi ___ | qayta tekshiruv sanasi/natijasi ___',
    speaking: 'Har asosiy va support darsida juftlik, rollar almashinuvi va qayta urinish. Sustroq o‘quvchiga kalit so‘zlar; tezroq o‘quvchiga yangi shart va javob savoli. Faqat kuchli o‘quvchini tinglab baholamang.',
    exercises: germanTeachingExercises.filter(e => lesson.topicIds.includes(e.topicId)), checkpoint: germanCheckpoint(no),
    officialPractice: germanOfficialPractice(no),
    audioPath: `/german/audio/lesson-${String(no).padStart(3, '0')}.mp3`, examSource: germanExamSource,
  };
}

// JSON.stringify(germanTeachingExport) is the PDF builder's sole teaching source.
export const germanTeachingExport = { version: 1, exercises: germanTeachingExercises, lessons: germanLessons.map(l => germanTeacherKit(l.no)), examSource: germanExamSource };
