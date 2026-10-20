import type { PracticeFamily, PracticeExercise, PracticeTheme } from './coursePracticeChoice';
// Curated supplemental content only. Rules explain these examples, never the graded prompt.
type Example = readonly [prompt: string, answer: string, completed: string];
function family(id: string, language: 'en' | 'de', title: string, scaffold: string, rule: string, rows: readonly Example[]): PracticeFamily {
  const themes: PracticeTheme[] = ['everyday', 'football', 'robots'];
  const variants = Object.fromEntries(rows.map(([prompt, answer, completed], i) => [themes[i], {
    prompt, answer, scaffold, explanation: `${completed} ${rule}`, caseSensitive: language === 'de',
  } satisfies PracticeExercise])) as Record<PracticeTheme, PracticeExercise>;
  return { id, language, title, variants };
}
export const extendedPracticeFamilies: readonly PracticeFamily[] = [
  family('en-present-base', 'en', 'Present Simple: I / you / we / they',
    'Shu gapning egasini toping. I, you, we, they bilan asosiy fe’lga -s qo‘shilmaydi.',
    'Ko‘plikdagi ega bilan Present Simple tasdiq gapida fe’lning asosiy shakli ishlatiladi.', [
      ['We ___ lunch every day. (pack)', 'pack', 'We pack lunch every day.'],
      ['The players ___ every evening. (train)', 'train', 'The players train every evening.'],
      ['The robots ___ parcels every day. (sort)', 'sort', 'The robots sort parcels every day.'],
    ]),
  family('en-present-third', 'en', 'Present Simple: uchinchi shaxs',
    'Shu gapdagi bitta shaxs yoki buyum uchun fe’l oxirini tekshiring: -s, -es yoki undosh + y → -ies.',
    'Uchinchi shaxs birlikda -s/-es ishlatiladi; undoshdan keyingi y esa -ies bo‘ladi.', [
      ['My sister ___ a bag every day. (carry)', 'carries', 'My sister carries a bag every day.'],
      ['The coach ___ each match. (watch)', 'watches', 'The coach watches each match.'],
      ['The robot ___ broken cables. (fix)', 'fixes', 'The robot fixes broken cables.'],
    ]),
  family('en-present-continuous', 'en', 'Present Continuous: tasdiq',
    'Hozir davom etayotgan harakat: egaga mos am/is/are + fe’lning -ing shakli. Ikkala qismni yozing.',
    'Present Continuous egaga mos be va -ing bilan tuziladi; bu yerda harakat ayni paytda davom etmoqda.', [
      ['She ___ tea now. (make; ikkala fe’l qismini yozing)', 'is making', 'She is making tea now.'],
      ['The players ___ now. (stretch; ikkala fe’l qismini yozing)', 'are stretching', 'The players are stretching now.'],
      ['The robot ___ a box now. (carry; ikkala fe’l qismini yozing)', 'is carrying', 'The robot is carrying a box now.'],
    ]),
  family('en-past-regular', 'en', 'Past Simple: muntazam fe’llar',
    'Yesterday o‘tgan vaqtni bildiradi. Qavsdagi muntazam fe’lni -ed bilan o‘zgartiring.',
    'Muntazam fe’lning Past Simple tasdiq shakli -ed bilan yasaladi.', [
      ['We ___ the dishes yesterday. (wash)', 'washed', 'We washed the dishes yesterday.'],
      ['The team ___ yesterday. (practice)', 'practiced', 'The team practiced yesterday.'],
      ['The robot ___ the corridor yesterday. (scan)', 'scanned', 'The robot scanned the corridor yesterday. Scan → scanned: oxirgi n takrorlanadi.'],
    ]),
  family('en-past-irregular', 'en', 'Past Simple: nomuntazam fe’llar',
    'Bu fe’llarga -ed qo‘shmang. Qavsdagi fe’lning o‘tgan zamon shaklini eslang.',
    'Bu nomuntazam fe’lning Past Simple shakli alohida o‘rganiladi.', [
      ['I ___ my cup yesterday. (break)', 'broke', 'I broke my cup yesterday. Break → broke.'],
      ['Our team ___ the cup last year. (win)', 'won', 'Our team won the cup last year. Win → won.'],
      ['The robot ___ the parcel yesterday. (bring)', 'brought', 'The robot brought the parcel yesterday. Bring → brought.'],
    ]),
  family('en-modal-bare', 'en', 'Modal + asosiy fe’l',
    'Shu qo‘shimcha gapda modaldan keyingi fe’lni to va -s qo‘shmasdan yozing.',
    'Can dan keyin fe’lning asosiy shakli keladi: to ham, uchinchi shaxs -s qo‘shimchasi ham qo‘shilmaydi.', [
      ['She can ___ a meal. (cook / cooks / to cook)', 'cook', 'She can cook a meal.'],
      ['The goalkeeper can ___ high. (jump / jumps / to jump)', 'jump', 'The goalkeeper can jump high.'],
      ['The robot can ___ metal. (bend / bends / to bend)', 'bend', 'The robot can bend metal.'],
    ]),
  family('en-should', 'en', 'Should bilan maslahat',
    'Bu maslahat, majburiyat emas. Should + asosiy fe’l: ikkala qismni yozing.',
    'Should maslahat bildiradi va undan keyin to siz asosiy fe’l keladi.', [
      ['Maslahat: You ___ more water. (should + drink)', 'should drink', 'You should drink more water.'],
      ['Maslahat: The team ___ before the game. (should + rest)', 'should rest', 'The team should rest before the game.'],
      ['Maslahat: You ___ the robot regularly. (should + inspect)', 'should inspect', 'You should inspect the robot regularly.'],
    ]),
  family('en-zero', 'en', 'Zero Conditional: umumiy qoida',
    'Bir martalik kelajak emas, takrorlanadigan qoida berilgan. If qismi va natijada Present Simple ishlating.',
    'Umumiy qoida uchun if + Present Simple, Present Simple ishlatiladi; birlikdagi ega bilan -s keladi.', [
      ['Umumiy qoida: If this timer reaches zero, it ___ (beep).', 'beeps', 'If this timer reaches zero, it beeps.'],
      ['O‘yin qoidasi: If the whole ball crosses the touchline, play ___ (stop).', 'stops', 'If the whole ball crosses the touchline, play stops.'],
      ['Qurilma qoidasi: If this robot gets too hot, it ___ (shut) down.', 'shuts', 'If this robot gets too hot, it shuts down.'],
    ]),
  family('en-first', 'en', 'First Conditional: real kelajak sharti',
    'Real kelajak ehtimoli: if qismida Present Simple, natijada will + asosiy fe’l. Natijadagi ikkala qismni yozing.',
    'If qismida Present Simple, kelajak natijasida will + asosiy fe’l ishlatilgan.', [
      ['If I finish my chores, I ___ (relax). Will bilan yozing.', 'will relax', 'If I finish my chores, I will relax.'],
      ['If our team wins, we ___ (celebrate). Will bilan yozing.', 'will celebrate', 'If our team wins, we will celebrate.'],
      ['If the battery is full, the robot ___ (start). Will bilan yozing.', 'will start', 'If the battery is full, the robot will start.'],
    ]),
  family('en-second', 'en', 'Second Conditional: hozirgi faraz',
    'Hozirgi faraz: if + Past Simple, natijada would + asosiy fe’l. Natijadagi ikkala qismni yozing.',
    'Bu hozirgi faraz: if qismidagi Past Simple o‘tgan voqeani emas, farazni bildiradi; natija would bilan tuziladi.', [
      ['If I had a garden, I ___ (plant) roses. Would bilan yozing.', 'would plant', 'If I had a garden, I would plant roses.'],
      ['If I were the coach, I ___ (change) the plan. Would bilan yozing.', 'would change', 'If I were the coach, I would change the plan.'],
      ['If I owned a robot, I ___ (teach) it chess. Would bilan yozing.', 'would teach', 'If I owned a robot, I would teach it chess.'],
    ]),
  family('de-present', 'de', 'Präsens: muntazam fe’l',
    'Shu gapning egasiga mos qo‘shimchani tanlang: ich -e, du -st, er/sie/es -t, wir -en.',
    'Muntazam fe’l Präsensda egaga mos tuslanadi.', [
      ['Ich ___ jeden Tag Brot. (kaufen, Präsens)', 'kaufe', 'Ich kaufe jeden Tag Brot. Ich uchun -e.'],
      ['Der Spieler ___ jeden Tag. (trainieren, Präsens)', 'trainiert', 'Der Spieler trainiert jeden Tag. Uchinchi shaxs birlik uchun -t.'],
      ['Wir ___ einen Roboter. (bauen, Präsens)', 'bauen', 'Wir bauen einen Roboter. Wir uchun -en.'],
    ]),
  family('de-v2', 'de', 'Darak gap: fe’l ikkinchi o‘rinda',
    'Vaqt yoki joy birikmasi birinchi bo‘lak. Tuslangan fe’l ikkinchi bo‘lakda, ega undan keyin keladi. Faqat bo‘shliq qismini yozing.',
    'Birinchi o‘rinda vaqt/joy bo‘lagi turgani uchun tuslangan fe’l undan keyin, ega esa fe’ldan keyin keladi.', [
      ['Tartiblang: ich / kaufe / Brot. Heute ___.', 'kaufe ich Brot', 'Heute kaufe ich Brot.'],
      ['Tartiblang: die Spieler / trainieren. Am Morgen ___.', 'trainieren die Spieler', 'Am Morgen trainieren die Spieler.'],
      ['Tartiblang: der Roboter / arbeitet. Hier ___.', 'arbeitet der Roboter', 'Hier arbeitet der Roboter.'],
    ]),
  family('de-can', 'de', 'Können: tasdiq',
    'Können fe’lini shu qo‘shimcha gapning egasiga moslang. Asosiy fe’l infinitivda gap oxirida turadi.',
    'Können qobiliyatni bildiradi; ich/er/sie/es bilan kann, asosiy fe’l esa gap oxirida infinitivda keladi.', [
      ['Ich ___ gut backen. (können, Präsens)', 'kann', 'Ich kann gut backen.'],
      ['Der Torwart ___ hoch springen. (können, Präsens)', 'kann', 'Der Torwart kann hoch springen.'],
      ['Der Roboter ___ schwere Kisten heben. (können, Präsens)', 'kann', 'Der Roboter kann schwere Kisten heben.'],
    ]),
  family('de-must', 'de', 'Müssen: majburiyat',
    'Bu gapdagi zaruratni müssen bilan ifodalang; egani aniqlab tuslang.',
    'Ich/er/sie/es uchun müssen shakli muss; asosiy fe’l infinitivda gap oxirida qoladi.', [
      ['Ich ___ heute einkaufen. (müssen, Präsens)', 'muss', 'Ich muss heute einkaufen.'],
      ['Der Spieler ___ pünktlich kommen. (müssen, Präsens)', 'muss', 'Der Spieler muss pünktlich kommen.'],
      ['Der Roboter ___ die Kiste tragen. (müssen, Präsens)', 'muss', 'Der Roboter muss die Kiste tragen.'],
    ]),
  family('de-past-sein', 'de', 'Sein: Präteritum',
    'Gestern o‘tgan vaqt. Sein fe’lining o‘tgan zamon shaklini shu egaga moslang.',
    'Sein Präteritumda ich/er/sie/es bilan war bo‘ladi.', [
      ['Ich ___ gestern zu Hause. (sein, Präteritum)', 'war', 'Ich war gestern zu Hause.'],
      ['Der Trainer ___ gestern im Stadion. (sein, Präteritum)', 'war', 'Der Trainer war gestern im Stadion.'],
      ['Der Roboter ___ gestern in der Werkstatt. (sein, Präteritum)', 'war', 'Der Roboter war gestern in der Werkstatt.'],
    ]),
  family('de-past-regular', 'de', 'Präteritum: muntazam fe’l',
    'Muntazam fe’lga Präteritum uchun -te asosini va egaga mos qo‘shimchani qo‘shing.',
    'Muntazam fe’lning Präteritum shaklida -te ishlatiladi; ko‘plikdagi wir bilan -ten bo‘ladi.', [
      ['Ich ___ gestern Suppe. (kochen, Präteritum)', 'kochte', 'Ich kochte gestern Suppe.'],
      ['Wir ___ gestern im Stadion. (trainieren, Präteritum)', 'trainierten', 'Wir trainierten gestern im Stadion.'],
      ['Der Roboter ___ gestern das Paket. (holen, Präteritum)', 'holte', 'Der Roboter holte gestern das Paket.'],
    ]),
  family('de-wuerde', 'de', 'Konjunktiv II: würde + infinitiv',
    'Faraz yoki istak: egaga mos würde shakli va gap oxirida infinitiv. Faqat yordamchi fe’lni yozing.',
    'Ich/er/sie/es bilan würde, asosiy fe’l esa infinitivda ishlatiladi.', [
      ['Ich ___ gern länger schlafen. (würde ni tuslang)', 'würde', 'Ich würde gern länger schlafen.'],
      ['Der Spieler ___ gern gewinnen. (würde ni tuslang)', 'würde', 'Der Spieler würde gern gewinnen.'],
      ['Der Roboter ___ gern tanzen. (würde ni tuslang)', 'würde', 'Der Roboter würde gern tanzen.'],
    ]),
  family('de-conditional', 'de', 'Wenn: haqiqiy bo‘lmagan shart',
    'Bu faraziy shart: wenn qismida Konjunktiv II, natijada würde + infinitiv. Shu gapdagi ich yoki birlikdagi egani tekshiring.',
    'Faraziy wenn qismidagi hätte — haben fe’lining Konjunktiv II shakli; ergash gapda tuslangan fe’l oxirida turadi.', [
      ['Wenn ich mehr Freizeit ___, würde ich malen. (haben, Konjunktiv II)', 'hätte', 'Wenn ich mehr Freizeit hätte, würde ich malen.'],
      ['Wenn der Verein mehr Geld ___, würde er neue Bälle kaufen. (haben, Konjunktiv II)', 'hätte', 'Wenn der Verein mehr Geld hätte, würde er neue Bälle kaufen.'],
      ['Wenn der Roboter Räder ___, würde er schneller fahren. (haben, Konjunktiv II)', 'hätte', 'Wenn der Roboter Räder hätte, würde er schneller fahren.'],
    ]),
  family('de-verb-final', 'de', 'Ergash gap: fe’l oxirida',
    'Weil/dass bilan boshlangan ergash gapda ega oldin, tuslangan fe’l oxirida keladi. Faqat bo‘shliqdagi qismini yozing.',
    'Weil va dass ergash gaplarida tuslangan fe’l oxirgi o‘ringa o‘tadi.', [
      ['Tartiblang: ich / Hunger / habe. Ich esse, weil ___.', 'ich Hunger habe', 'Ich esse, weil ich Hunger habe.'],
      ['Tartiblang: die Spieler / müde / sind. Der Trainer sagt, dass ___.', 'die Spieler müde sind', 'Der Trainer sagt, dass die Spieler müde sind.'],
      ['Tartiblang: der Akku / leer / ist. Der Roboter steht, weil ___.', 'der Akku leer ist', 'Der Roboter steht, weil der Akku leer ist.'],
    ]),
];
