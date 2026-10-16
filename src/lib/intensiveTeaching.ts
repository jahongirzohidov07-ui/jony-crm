import { lessonPlan, lessonGrammarPractice, topicPractice, vocabularyPractice, teacherNotes } from './intensive';
import { skillsForLesson, skillQuestions } from './intensive-skills';
import guidance from '../data/intensive-lesson-guidance.json';
import authenticListening from '../data/intensive-authentic-listening.json';
import skillExtensions from '../data/intensive-skills-extension.json';

export type TeachingProfile = 'foundation' | 'grammar-heavy' | 'skills-focused' | 'review' | 'mock-receptive' | 'mock-production';
export const teachingProfileLabels: Record<TeachingProfile,string> = {foundation:'Boshlang‘ich tayanch', 'grammar-heavy':'Grammatikaga e’tibor', 'skills-focused':'Ko‘nikmalarga e’tibor', review:'Takrorlash va tekshiruv', 'mock-receptive':'Imtihon mashqi: tinglash va o‘qish', 'mock-production':'Imtihon mashqi: yozish va gapirish'};
export type TeachingStage = { minutes: number; start: number; end: number; title: string; instruction: string; exerciseIds: string[] };

/** Plain JSON data only: shared by the teacher UI and monthly PDF exporter. */
export function intensiveTeachingKit(lesson: number, groupSize = 16) {
  const plan = lessonPlan(lesson), no = plan.no;
  const guide = guidance[no - 1], pack = skillsForLesson(no);
  const skillExtension = skillExtensions.lessons.find(item => item.lesson === no)!;
  const unseenHomework = skillExtensions.homework.find(item => item.afterLesson === no);
  const size = Number.isFinite(groupSize) ? Math.max(1, Math.min(60, Math.trunc(groupSize))) : 16;
  const profile: TeachingProfile = [181,187].includes(no) ? 'mock-receptive'
    : [182,188].includes(no) ? 'mock-production' : plan.review ? 'review'
    : no <= 30 ? 'foundation' : plan.spiral || plan.day >= 4 ? 'skills-focused' : 'grammar-heavy';
  const mock = profile.startsWith('mock-');
  const bank = lessonGrammarPractice(no).filter(q => !q.id.startsWith('model-'));
  // Spread core questions over every assigned topic before adding a second round.
  const scoped = plan.topics.map(t => topicPractice(t.id).filter(q => q.id.startsWith('topic-')));
  const ordered = plan.review || plan.spiral ? bank : [0,1,2,3,4,5].flatMap(i => scoped.flatMap(qs => qs[i] ? [qs[i]] : []));
  const count = mock ? 0 : profile === 'grammar-heavy' ? Math.max(plan.topics.length, 10) : profile === 'review' ? 12 : profile === 'foundation' ? Math.max(plan.topics.length, 6) : 6;
  const core = ordered.slice(0, count), extra = ordered.slice(core.length);
  const vocab = vocabularyPractice(plan.words.slice(0, plan.review ? 10 : 8), false);
  const toQuestion = (task: typeof skillExtension.reading.tasks[number]) => ({id:task.id,prompt:[task.prompt,...task.options].join('\n'),answers:[task.teacher.answer],explanation:`Namuna; mazmuni mos boshqa javoblar ham qabul qilinadi. Dalil: ${task.teacher.evidence.join(' / ')}. ${task.teacher.guidance}`});
  const extraReading = skillExtension.reading.tasks.map(toQuestion), extraListening = skillExtension.listening.tasks.map(toQuestion);
  const reading = pack ? [extraReading[0],...skillQuestions(pack, 'reading'),extraReading.at(-1)!] : [];
  const listening = pack ? [extraListening[0],...skillQuestions(pack, 'listening'),extraListening.at(-1)!] : [];
  const additionalSkills = [...extraReading.slice(1,-1),...extraListening.slice(1,-1)];
  const ids = (qs: {id:string}[]) => qs.map(q => q.id);
  const questions = [...core, ...extra, ...vocab, ...reading, ...listening, ...additionalSkills, ...(unseenHomework?.tasks.map(toQuestion) ?? [])];
  const stages: TeachingStage[] = [];
  function add(minutes: number, title: string, instruction: string, exerciseIds: string[] = []) {
    const start = stages.at(-1)?.end ?? 0;
    stages.push({minutes,start,end:start+minutes,title,instruction,exerciseIds});
  }
  const boundary = no <= 6 ? 'Faqat turkum, yorliq, tayyor birikma va namuna tahlili; erkin gap yoki fe’l tuslash talab qilinmaydi.'
    : no <= 30 ? 'Faqat bugungi qo‘llanmadagi o‘tilgan qoliplar; hali o‘tilmagan zamon yoki erkin uzun matn talab qilinmaydi.'
    : 'Bugungi o‘tilgan shakllar va ko‘nikma mezonlari asosida baholang.';
  const grouping = size === 1 ? '1 o‘quvchi: ustoz sherik; o‘quvchi ikki marta gapiradi, ustoz qisqa fikr beradi.'
    : `${size} o‘quvchi: ${Math.floor(size/2)-(size%2 ? 1 : 0)} juft${size%2 ? ' va 1 uchlik' : ''}. Juftlar: A 2 daqiqa, B 2 daqiqa, so‘ng 2 daqiqa o‘zaro fikr. Uchlik: A/B/C har biri 2 daqiqadan; tinglovchilar mezon belgilaydi.`;
  const speaking = `${grouping} Hamma bir vaqtda ishlaydi. 2 daqiqa namuna; 6 daqiqa navbat; qolgan vaqt qayta urinish va fikr. Ustoz har dars 4 o‘quvchini navbat bilan kuzatadi; qolganlar sherik mezonlarini belgilaydi. ${boundary}`;
  const audioUrl = `/intensive/audio/lesson-${String(no).padStart(3,'0')}.mp3`;
  const writing = no <= 6 ? '2 daqiqa namuna; 6 daqiqa yorliq/birikma; 2 daqiqa asl namuna bilan tekshiruv.'
    : '3 daqiqa reja; ajratilgan vaqtning oxirgi 3 daqiqasi mezon bilan tekshiruv; qolgan vaqt mustaqil qoralama. To‘liq hajm sig‘masa shu yerda tugagan joyni belgilang, uyda davom ettiring. Ustoz 4 ishni batafsil, qolganlarini bitta maqsadli mezon bilan tekshiradi.';
  if (profile === 'mock-receptive') {
    add(5,'Variant va audio tekshiruvi','Exam preparation bo‘limidagi mavjud tashqi listening/reading varaqlari va audioni tayyorlang; variant nomi va sanani yozing.');
    add(45,'Listening — mavjud sessiya','Exam preparation → Listening. Mavjud 45 daqiqali taymer; tashqi audio va savollar, javob kaliti yopiq.',['exam:listening']);
    add(60,'Reading — mavjud sessiya','Darhol Readingni boshlang; mavjud 60 daqiqali taymer. Bugungi qisqa ko‘nikma matni buning o‘rnini bosmaydi.',['exam:reading']);
    add(10,'Saqlash va topshirish','Natijani eksport qiling. Keyingi darsda shu urinishning Writing bo‘limidan davom eting; yangi urinish yaratmang.');
  } else if (profile === 'mock-production') {
    add(5,'Oldingi urinishni ochish','Oldingi listening/reading sessiyalari tugaganini tekshiring. Tugamagan bo‘lsa ularni bajarish uchun alohida vaqt belgilang; tartibni chetlab o‘tmang.');
    add(60,'Writing — mavjud sessiya','Exam preparation → Writing: mavjud 60 daqiqali sessiya va komponentdagi yangi writing namunasi.',['exam:writing']);
    add(5,'Tanaffus va yozuv tayyorlash','Har o‘quvchi o‘z qurilmasi/yozuv vositasi bilan tayyorlansin.');
    add(30,'Speaking — parallel navbatlar','Mavjud 9:15 topshiriq taymeriga 10 daqiqalik uch navbat: A, B, uchlikdagi C. Har bir o‘quvchi o‘z sessiyasidan foydalanadi; boshqalar sherik yoki kuzatuvchi. Yozuv/live dalilini qayd eting. Bir ustoz barchani shu vaqtda individual baholamaydi; 4 ishni tanlab tekshiradi, qolgan yozuvlarni keyin. Qurilma yetmasa alohida individual slot belgilang.',['exam:speaking']);
    add(20,'Dalil va keyingi qadam','Yozuv/ish havolasi, variant nomi va xato turini qayd eting. Ustoz ko‘rmagan ishni baholangan deb belgilamang.');
  } else {
    const budget = profile === 'foundation' ? [10,25,20,5,12,13,15,10,10]
      : profile === 'grammar-heavy' ? [8,35,15,5,12,12,13,12,8]
      : profile === 'review' ? [10,20,10,5,15,15,15,20,10]
      : [5,15,10,5,20,20,15,22,8];
    add(budget[0], no === 1 ? 'Kirish va namuna' : 'Oldingi natijani qaytarish', no === 1 ? 'Daftar, taymer va mustaqil urinish → tekshiruv tartibini ko‘rsating. '+boundary : 'Oldingi dars qaydlaridagi ikki xato bandini javobsiz qayta bering; yordam ishlatilganini belgilang.');
    add(budget[1], 'Grammar: model → mustaqil', `${plan.topics.map(t=>t.id+' '+t.title).join('; ')}. Doskadagi modellarni oching. Vaqtning uchdan biri tushuntirish, qolgani quyidagi aniq savollar va javob sababini tekshirish. ${boundary}`,ids(core));
    add(budget[2], 'Lug‘at: asosiy va tanishtirish', `Asosiy ${vocab.length} so‘zning IDlari: ${plan.words.slice(0,vocab.length).map(w=>w.id).join(', ')}. Avval ayting/ko‘rsating, keyin yashirib tekshiring. Qolgan ${plan.words.length-vocab.length} so‘z — tanishtirish va bosqichli uy takrori; sinfda barchasini egalladi deb hisoblamang.`,ids(vocab));
    add(budget[3], 'Tanaffus','Taymerni to‘xtating, qisqa harakat.');
    add(budget[4], `Reading: ${pack?.reading.title ?? 'material yetishmaydi'}`, 'Matnni o‘qing, aniq savollarga qisqa javob va dalil belgilang. Kalitni mustaqil urinishdan keyin oching.',ids(reading));
    add(budget[5], `Listening: ${pack?.listening.title ?? 'material yetishmaydi'}`, `Audio: ${audioUrl}. Transkript yopiq: birinchi tinglashda vaziyat, ikkinchisida tafsilot. So‘ng kalit va transkript. Bu dars audiosi, rasmiy mock audio o‘rnini bosmaydi.`,ids(listening));
    add(budget[6], 'Speaking: parallel juftlar',speaking+` Vazifa: ${pack?.speaking.prompt ?? 'Material yetishmaydi'}`,[`speaking-${no}`]);
    add(budget[7], 'Writing: sinf qoralamasi',writing+` Vazifa: ${pack?.writing.prompt ?? 'Material yetishmaydi'}`,[`writing-${no}`]);
    add(budget[8], 'Chiqish va topshirish','Quyidagi qo‘llanma chiqish biletini javoblari yopiq holda bering. 4/5 dan past: xato ID, berilgan yordam va keyingi qayta tekshiruvni keyingi dars qaydiga yozing.');
  }
  const homeworkQuestions = extra.slice(0,6);
  const authentic = authenticListening.find(item => item.lesson === no);
  const previous = skillsForLesson(no-1);
  const previousGrammar = no>1 ? lessonGrammarPractice(no-1).filter(q=>!q.id.startsWith('model-')).slice(0,6) : [];
  const previousQuestions = previous ? [...skillQuestions(previous,'reading'),...skillQuestions(previous,'listening')] : [];
  if(mock) questions.push(...previousGrammar.filter(q=>!questions.some(existing=>existing.id===q.id)),...previousQuestions);
  const homework = mock ? [
    {minutes:25,task:`Bugungi yangi lug‘at ${plan.start}–${plan.end}: ${plan.words.map(w=>w.id).join(', ')}. 5 tadan ma’no/talaffuzni o‘rganing, yoping va tekshiring. Bu so‘zlar mock tufayli tashlab ketilmaydi; qiyin IDlarni keyingi kirishga topshiring.`,exerciseIds:ids(vocab)},
    {minutes:25,task:`Yakunlangan bo‘lim xatolarini dalil bilan tuzating; avvalgi dars grammatik takrorlash savollari: ${ids(previousGrammar).join(', ')}. Bugungi grammar kartalari spiral takrorlash, yangi qoida emas. Eksportni shu blokning oxirgi 2 daqiqasida saqlang.`,exerciseIds:ids(previousGrammar)},
    {minutes:25,task:`Faqat avval bajarilgan ${no-1}-dars reading «${previous?.reading.title}» va listening «${previous?.listening.title}»: /intensive/audio/lesson-${String(no-1).padStart(3,'0')}.mp3. Dalil va xatoni qayta tekshiring. Kelgusi exam bo‘limi savolini oldindan ishlamang.`,exerciseIds:ids(previousQuestions)},
    {minutes:15,task:`Avvalgi ${no-1}-dars speaking: ${previous?.speaking.prompt} Yoki tugagan exam speaking yozuvini mezon bilan tahlil qilib qayta ayting.`,exerciseIds:[`speaking-${no-1}`]},
    {minutes:30,task:`Avval bajarilgan ${no-1}-dars writing: ${previous?.writing.prompt} Qoralamani mezon bilan qayta yozing va ikki tuzatish sababini belgilang. Faqat tugagan exam writing ishini buning o‘rniga olish mumkin; kelgusi sessiya savolini oldindan ishlamang.`,exerciseIds:[`writing-${no-1}`]},
  ] : [
    {minutes:25,task:`Grammar: ${ids(homeworkQuestions).join(', ') || 'sinfda xato bo‘lgan core IDlar'}. Avval mustaqil, so‘ng javob va sabab; bitta xatoni qayta yeching. ${boundary}`,exerciseIds:ids(homeworkQuestions)},
    {minutes:25,task:`Lug‘at ${plan.start}–${plan.end}: avval bugungi asosiy ${vocab.length} so‘z, keyin qolganidan 5 tadan. 25 daqiqada to‘xtang; o‘zlashtirilmagan IDlarni qayd eting.`,exerciseIds:ids(vocab)},
    {minutes:25,task:`«${pack?.reading.title}»: savollarga dalil. «${pack?.listening.title}»: aniq audio ${audioUrl}, avval matnsiz ikki tinglash, keyin transkript bilan xato dalilini belgilang.`,exerciseIds:[...ids(reading),...ids(listening)]},
    {minutes:15,task:`Speaking: ${pack?.speaking.prompt} Mezonlardan bittasiga ko‘ra qayta urinish; yozuv yoki sherik qaydi.`,exerciseIds:[`speaking-${no}`]},
    {minutes:30,task:`Writing: ${pack?.writing.prompt} Sinf qoralamasini tugating; asl modelni faqat keyin solishtiring, bir tuzatishni rang bilan belgilang.`,exerciseIds:[`writing-${no}`]},
  ];
  if (unseenHomework) {
    const block = homework.find(h => h.exerciseIds.includes(`reading-${no}-0`));
    if (!block) throw new Error(`Missing weekly reading block: ${no}`);
    block.minutes = Math.max(25, unseenHomework.minutes);
    block.task = `${unseenHomework.week}-hafta yangi mustaqil matni: «${unseenHomework.title}». ${unseenHomework.instructions} ${unseenHomework.minutes < 25 ? 'Qolgan 5 daqiqa: bugungi MP3dan ikkita qiyin iborani qayta tinglang.' : ''} Matn va topshiriqlar quyida hamda 4 ko‘nikma bo‘limida. Kalitni mustaqil urinishdan keyin oching.`;
    block.exerciseIds = unseenHomework.tasks.map(task => task.id);
    if (block.minutes > 25) { homework[0].minutes -= (block.minutes-25)/2; homework[1].minutes -= (block.minutes-25)/2; homework[1].task = homework[1].task.replace("25 daqiqada", `${homework[1].minutes} daqiqada`); }
  }
  if (authentic) {
    const block = homework.find(h => h.exerciseIds.includes(`reading-${no}-0`));
    if (!block) throw new Error(`Missing listening homework block: ${no}`);
    block.task = `25 daqiqa — British Council: ${authentic.title} (${authentic.level}). ${authentic.url}. ${authentic.focus} 3 daqiqa tayyorgarlik; 14 daqiqagacha ikki tinglash va Task 1/Task 2; 8 daqiqa asl sahifadagi javob/transkript bilan xatolarni tekshirish. Bu bugungi reading/listening uy bloki o‘rnida, qo‘shimcha vaqt emas. Natijani ustozga qayd bilan bering; avtomatik saqlanmaydi.`;
    block.exerciseIds = [];
  }
  return {
    unseenHomework: unseenHomework ?? null, authenticListening: authentic ?? null, schemaVersion:1, lesson:no, week:plan.week, month:plan.month, groupSize:size, profile, profileLabel:teachingProfileLabels[profile],
    title:plan.title, objective:guide.objective, boundary, totalMinutes:stages.at(-1)!.end, stages,
    materials:{guideId:`intensive-lesson-guidance:${no}`,board:guide.board,explain:guide.explain,commonMistake:guide.commonMistake,differentiation:guide.differentiation,
      grammar:plan.topics.map(t=>({id:t.id,title:t.title,model:t.example,teacherNotes:teacherNotes[t.module]})),
      vocabulary:plan.words,audioUrl,skills:pack ?? null,previousSkills:mock ? previous ?? null : null},
    mandatoryExerciseIds:mock ? stages.flatMap(s=>s.exerciseIds) : [...ids(core),...ids(vocab),...ids(reading),...ids(listening),`speaking-${no}`,`writing-${no}`],
    extensionExerciseIds:[...ids(extra),...ids(additionalSkills)], extensionInstruction:'Faqat asosiy vazifa tugasa. Qo‘shimcha bank 120 daqiqaga qo‘shilmaydi; bugungi grammatik chegarani kengaytirmang.',
    questions, exitTicket:guide.exitTicket, checkQuestions:guide.checkQuestions,
    homework, homeworkMinutes:homework.reduce((n,h)=>n+h.minutes,0), guideHomework:guide.homework,
    handoff:{nextLesson:no < 192 ? no+1 : null, nextObjective:no < 192 ? guidance[no].objective : 'Kurs yakuni: individual davom rejasi',
      fields:['O‘quvchi / guruh','Chiqish __/5; mustaqil yoki yordam bilan','Xato mashq raqami + javob + xato sababi','Writing qoralama / speaking dalili','Uy vazifasi bajarilgan IDlar / qolgan IDlar','Keyingi kirishda ikki xato bandini qayta tekshirish'],
      instruction:no < 192 ? 'Keyingi ustoz dastlabki kirish vaqtida ikki xato bandini qayta tekshiradi; 4/5 bo‘lmasa yangi murakkablashtirish o‘rniga tayanch model bilan ishlaydi.' : 'Qolgan xato IDlari va ish dalillari bilan individual davom rejasini bering.'},
    exam:no >= 169 ? {enabled:true,cycle:no >= 187 ? 187 : 181,session:profile,notice:'Mavjud tashqi namuna va exam preparation komponenti. Yangi rasmiy mock bank yaratilmagan. 181/187: listening + reading; 182/188: writing + speaking. Bu ikki darsga bo‘lingan mashq; uzluksiz to‘liq imtihon emas. Qayta ishlangan namunani yangi diagnostika deb baholamang. Boshqa kunlar: tayyorgarlik va xatolar ustida ishlash.'} : null,
  };
}
export type IntensiveTeachingKit = ReturnType<typeof intensiveTeachingKit>;
export const intensiveTeachingCourse = (groupSize = 16) => Array.from({length:192},(_,i)=>intensiveTeachingKit(i+1,groupSize));
