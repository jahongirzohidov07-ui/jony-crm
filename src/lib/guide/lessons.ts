/**
 * O'RGATUVCHI DARSLARI — "shu yerni bosasan" (2026-08-23).
 *
 * Jahongir: "yangi xodim kirsa toliq demo yani onboarding qilinsin
 * avtomat... shu yerni bosasan deb strelkalar turib hammasini
 * korsatib turishi kerak".
 *
 * Har bir DARS — bitta haqiqiy ish (to'lov qabul qilish, yo'qlama
 * qo'yish...). Har bir QADAM — ekrandagi bitta joy: strelka o'sha
 * yerga tushadi, matn nima qilishni aytadi.
 *
 * MO'LJAL (target) — `data-guide="..."` belgisi bo'yicha topiladi,
 * CSS klass bo'yicha emas. Sababi: dizayn o'zgarsa klass o'zgaradi
 * va strelka adashadi; `data-guide` maxsus shu ish uchun qo'yilgan.
 *
 * QADAM TURLARI:
 *   click — xodim O'ZI bosishi kerak (strelka turadi, kutamiz);
 *   look  — shunchaki ko'rsatamiz, "Tushundim" bilan davom etadi.
 */

export type StepKind = "click" | "look";

export interface GuideStep {
  /** Qaysi sahifada bo'lishi kerak (bo'sh — joriy sahifada) */
  path?: string;
  /** data-guide belgisi */
  target?: string;
  kind: StepKind;
  title: string;
  text: string;
  /** Mo'ljal topilmasa qadam o'tkazib yuboriladi (xato bermaydi) */
  optional?: boolean;
}

export interface GuideLesson {
  id: string;
  title: string;
  /** Nega kerak — xodim ma'nosini tushunsin */
  why: string;
  minutes: number;
  roles: string[];
  steps: GuideStep[];
}

/** Barcha lavozimlar uchun umumiy tanishuv */
const COMMON: GuideLesson[] = [
  {
    id: "tour-basic",
    title: "Tizim bilan tanishuv",
    why:
      "Qaysi bo'lim nima uchun kerakligini bilib olasiz — keyin har " +
      "safar izlab o'tirmaysiz.",
    minutes: 2,
    roles: ["*"],
    steps: [
      {
        path: "/",
        kind: "look",
        target: "nav-dashboard",
        title: "Dashboard — kunning ko'zgusi",
        text:
          "Har kuni shu yerdan boshlaysiz: bugungi to'lovlar, qarzdorlar, " +
          "yangi lidlar va e'tibor kerak bo'lgan joylar shu yerda ko'rinadi.",
      },
      {
        kind: "look",
        target: "topbar-search",
        title: "Tezkor qidiruv",
        text:
          "Eng ko'p ishlatiladigan joy. Ism yoki telefon raqamini " +
          "yozsangiz — o'quvchi darrov topiladi, bo'limlarni aylanib " +
          "yurish shart emas.",
      },
      {
        kind: "look",
        target: "nav-students",
        title: "O'quvchilar",
        text:
          "Barcha o'quvchilar ro'yxati. Ustiga bosib kartasini ochasiz — " +
          "to'lovi, yo'qlamasi, guruhi hammasi o'sha yerda.",
        optional: true,
      },
      {
        kind: "look",
        target: "nav-groups",
        title: "Guruhlar",
        text:
          "Guruhlar, ularning jadvali va o'quvchilari. Yo'qlama ham shu " +
          "yerdan qo'yiladi.",
        optional: true,
      },
      {
        kind: "look",
        target: "topbar-branch",
        title: "Filial tanlagich",
        text:
          "Bir nechta filialda ishlasangiz — shu yerdan almashtirasiz. " +
          "Butun tizim o'sha filialni ko'rsatadi.",
        optional: true,
      },
    ],
  },
];

/**
 * ADMINISTRATOR ROLLARI (2026-08-23, Jahongir: "menda tepada turgan
 * 6ta funksiya adminlar uchun edi nega asoschida chiqyabdi").
 *
 * Asoschi ATAYIN yo'q: bu darslar administratorning kunlik ishi,
 * asoschining ish stoli boshqa. Asoschi ularni ko'rmoqchi bo'lsa —
 * profildagi "boshqa lavozim ko'zi bilan" tanlagichidan tanlaydi.
 *
 * "sales_manager" ham bor: tizimda u ham "Administrator" deb
 * ataladi (roles.ts, UZ_LABELS) — eski hisoblar o'shanda qolgan.
 */
const ADMIN_ROLES = ["administrator", "sales_manager"];

/** ADMINISTRATOR — kunlik ishning o'zagi */
const ADMIN: GuideLesson[] = [
  {
    id: "admin-payment",
    title: "To'lov qabul qilish",
    why:
      "Kunlik ishning eng ko'p takrorlanadigan qismi. Noto'g'ri " +
      "kiritilgan to'lov kechqurun kassani to'g'rilashga majbur qiladi.",
    minutes: 3,
    roles: [...ADMIN_ROLES, "accountant", "branch_manager"],
    steps: [
      {
        path: "/",
        kind: "click",
        target: "btn-take-payment",
        title: "To'lov qabul qilish tugmasi",
        text:
          "Ota-ona pul olib kelganda shu tugmani bosasiz. U har sahifada, " +
          "chap tepada turadi — izlab yurmaysiz.",
      },
      {
        kind: "look",
        target: "pay-student",
        title: "O'quvchini tanlash",
        text:
          "Ismini yozishni boshlang — ro'yxat o'zi qisqaradi. Kerakli " +
          "o'quvchi chiqqach ustiga bosasiz.",
      },
      {
        kind: "look",
        target: "pay-amount",
        title: "Summa",
        text:
          "Ota-ona qancha bergan bo'lsa — o'shani yozasiz. Yarim to'lov " +
          "ham bo'ladi, tizim qolganini qarz qilib qo'yadi.",
        optional: true,
      },
      {
        kind: "look",
        target: "pay-method",
        title: "To'lov usuli — eng ko'p xato shu yerda",
        text:
          "Naqd, plastik yoki terminal. Kechqurun kassa hisoblanganda " +
          "aynan shu bo'yicha ajratiladi — noto'g'ri tanlasangiz naqd " +
          "pul yetishmay qoladi.",
        optional: true,
      },
      {
        kind: "look",
        target: "pay-submit",
        title: "Saqlash",
        text:
          "Saqlagandan keyin: o'quvchi balansi o'zgaradi, ota-onaga " +
          "Telegram xabar ketadi va Pul oqimida ko'rinadi. Xato bo'lsa — " +
          "o'chirmang, rahbarga tuzatish so'rovi yuboring.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-attendance",
    title: "Yo'qlama qo'yish",
    why:
      "Yo'qlama — pul. Ustoz oyligi va o'quvchi hisobi aynan yo'qlamadan " +
      "chiqadi. Qo'yilmagan yo'qlama = hisoblanmagan dars.",
    minutes: 3,
    roles: [...ADMIN_ROLES, "teacher", "academic_head", "branch_manager"],
    steps: [
      {
        path: "/groups",
        kind: "click",
        target: "group-row-first",
        title: "Guruhni oching",
        text:
          "Guruhlar ro'yxatidan kerakligini bosing. Mashq uchun " +
          "birinchisini oching.",
      },
      {
        kind: "click",
        target: "gtab-attendance",
        title: "Davomat bo'limi",
        text: "Guruh kartasidagi «Davomat» bo'limiga o'ting.",
        optional: true,
      },
      {
        kind: "look",
        target: "attendance-grid",
        title: "Belgilash",
        text:
          "Har o'quvchi qatorida bugungi kun ustuni bor. Bosgan sari belgi " +
          "almashadi: keldi → kelmadi → kech keldi. Faqat " +
          "O'ZGARTIRGANINGIZ yoziladi va auditda kim qo'ygani ko'rinadi.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-debtors",
    title: "Qarzdorlar bilan ishlash",
    why:
      "Oy oxirida pul yig'ilmay qolishining sababi — qarzdor bilan o'z " +
      "vaqtida gaplashmaslik. Bu ro'yxat har kuni ochiladi.",
    minutes: 2,
    roles: [
      ...ADMIN_ROLES, "accountant", "branch_manager", "finance_director",
    ],
    steps: [
      {
        path: "/finance",
        kind: "click",
        target: "ftab-debtors",
        title: "Moliya → Qarzdorlar",
        text:
          "Qarzdorlar Moliya bo'limining ichida. «Qarzdorlar» yorlig'ini " +
          "bosing.",
      },
      {
        kind: "look",
        target: "debtors-table",
        title: "Ro'yxatni qanday o'qiysiz",
        text:
          "Kim qancha qarzdor va necha kundan beri — hammasi shu yerda. " +
          "Eng katta va eng eski qarz tepada turadi: kunni o'shalarga " +
          "qo'ng'iroq qilishdan boshlaysiz.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-freeze",
    title: "O'quvchini muzlatish",
    why:
      "Bola kasal bo'lsa yoki ta'tilga chiqsa — muzlatiladi. Muzlatilmasa " +
      "oylik hisoblanaveradi va keraksiz qarz yig'iladi.",
    minutes: 2,
    roles: [...ADMIN_ROLES, "branch_manager", "academic_head"],
    steps: [
      {
        path: "/students",
        kind: "click",
        target: "student-row-first",
        title: "O'quvchini oching",
        text: "Ro'yxatdan o'quvchini bosing — kartasi ochiladi.",
      },
      {
        kind: "click",
        target: "student-menu",
        title: "Uch nuqta menyusi",
        text:
          "Kartaning o'ng tepasidagi uch nuqta — muzlatish, guruhdan " +
          "chiqarish kabi amallar shu yerda.",
        optional: true,
      },
      {
        kind: "look",
        target: "student-menu-freeze",
        title: "Muzlatish",
        text:
          "Sanani tanlaysiz va sababini yozasiz. Muzlatilgan kundan " +
          "boshlab oylik yechilmaydi, chegirmasi ham vaqtincha to'xtaydi — " +
          "qaytib kelsa o'zi tiklanadi.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-discount",
    title: "Chegirma so'rash",
    why:
      "Chegirma — bu pul. Shuning uchun xodim o'zi bera olmaydi, faqat " +
      "so'raydi; rahbar tasdiqlaydi.",
    minutes: 2,
    roles: [...ADMIN_ROLES, "branch_manager"],
    steps: [
      {
        path: "/students",
        kind: "click",
        target: "student-row-first",
        title: "O'quvchi kartasi",
        text:
          "Chegirma har doim aniq bir o'quvchiga beriladi — avval " +
          "kartasini oching.",
      },
      {
        kind: "click",
        target: "stab-price",
        title: "Chegirma bo'limi",
        text: "«Narx va chegirma» bo'limiga o'ting.",
        optional: true,
      },
      {
        kind: "look",
        target: "discount-add",
        title: "So'rov yuborish",
        text:
          "Turini (oila, xodim farzandi, grant...), foizini va SABABINI " +
          "yozasiz. So'rov rahbarga vazifa bo'lib tushadi; u " +
          "tasdiqlamaguncha chegirma ishlamaydi.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-group-move",
    title: "Guruhdan guruhga o'tkazish",
    why:
      "Bola darajasi ko'tarilsa yoki vaqti to'g'ri kelmasa — guruhi " +
      "almashadi. Noto'g'ri o'tkazsangiz eski ustozning oyligi ham, " +
      "o'quvchining hisobi ham chalkashadi.",
    minutes: 3,
    roles: [...ADMIN_ROLES, "branch_manager", "academic_head"],
    steps: [
      {
        path: "/students",
        kind: "click",
        target: "student-row-first",
        title: "O'quvchini toping",
        text:
          "Ro'yxatdan o'quvchini bosing. Mashq uchun birinchisini oling — " +
          "bu test filiali, hech narsa buzilmaydi.",
      },
      {
        kind: "click",
        target: "student-menu",
        title: "Uch nuqta menyusi",
        text:
          "O'ng tomondagi uch nuqta — o'quvchi ustidagi barcha amallar " +
          "shu yerda yig'ilgan.",
        optional: true,
      },
      {
        kind: "click",
        target: "student-menu-move",
        title: "«Boshqa guruhga o'tkazish»",
        text:
          "Shuni bosing — ochilgan ro'yxatdan yangi guruhni tanlaysiz.",
        optional: true,
      },
      {
        kind: "look",
        target: "student-menu-move",
        title: "Nima o'zgaradi",
        text:
          "Tizim o'zi qiladi: eski guruhdan chiqaradi, yangisiga qo'shadi, " +
          "shu oy uchun to'langan pulni ikki ustoz o'rtasida O'TILGAN " +
          "darslar bo'yicha bo'ladi va ko'chish tarixiga yozadi. Sig'im " +
          "yoki daraja mos kelmasa — ogohlantiradi, o'qib chiqing.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-group-remove",
    title: "Guruhdan chiqarish",
    why:
      "O'quvchi tashlab ketsa guruhdan chiqarilishi kerak, aks holda " +
      "unga oylik yechilaveradi va qarzdorlar ro'yxatini bo'yaydi. " +
      "Lekin chiqarish — O'CHIRISH emas: tarixi joyida qoladi.",
    minutes: 3,
    roles: [...ADMIN_ROLES, "branch_manager", "academic_head"],
    steps: [
      {
        path: "/students",
        kind: "click",
        target: "student-row-first",
        title: "O'quvchini oching",
        text: "Ro'yxatdan o'quvchini bosing.",
      },
      {
        kind: "click",
        target: "student-menu",
        title: "Uch nuqta menyusi",
        text: "Amallar ro'yxatini oching.",
        optional: true,
      },
      {
        kind: "look",
        target: "student-menu-remove",
        title: "«O'chirish» — bu guruhdan chiqarish",
        text:
          "Qizil yozuv qo'rqitmasin: o'quvchi bazadan yo'qolmaydi. " +
          "Faqat guruhdan chiqadi, to'lov tarixi va davomati saqlanadi.",
        optional: true,
      },
      {
        kind: "look",
        target: "student-menu-remove",
        title: "Sana va sabab — eng muhimi",
        text:
          "QAYSI KUNGACHA o'qiganini belgilaysiz. Hisob aynan shu " +
          "sanagacha o'tilgan darslar bo'yicha qayta hisoblanadi — " +
          "kechikib kiritsangiz ham ortiqcha pul yechilmaydi. Qarzi " +
          "bo'lmasa darrov arxivga, qarzi bo'lsa to'langach avtomat.",
        optional: true,
      },
    ],
  },
  {
    id: "admin-pay-fix",
    title: "To'lovni xato kiritsangiz — tuzatish so'rovi",
    why:
      "Eng ko'p uchraydigan xato: summa yoki usul noto'g'ri kiritiladi. " +
      "To'lovni O'ZINGIZ o'chirmaysiz va tahrirlamaysiz — kassa " +
      "buziladi. To'g'ri yo'l: rahbarga so'rov yuborish.",
    minutes: 3,
    roles: [...ADMIN_ROLES, "accountant", "branch_manager"],
    steps: [
      {
        path: "/students",
        kind: "click",
        target: "student-row-first",
        title: "O'quvchi kartasini oching",
        text: "Xato to'lov qaysi o'quvchida bo'lsa — o'shani oching.",
      },
      {
        kind: "click",
        target: "stab-payments",
        title: "«To'lovlar» bo'limi",
        text: "Uning barcha to'lovlari va yechimlari shu yerda.",
        optional: true,
      },
      {
        kind: "look",
        target: "pay-fix-request",
        title: "Qatordagi qalamcha",
        text:
          "Xato yozuv qatorida qalamcha bor. Bosing — to'g'ri summani " +
          "va NEGA xato bo'lganini yozasiz.",
        optional: true,
      },
      {
        kind: "look",
        target: "pay-fix-request",
        title: "Keyin nima bo'ladi",
        text:
          "So'rov rahbarga vazifa bo'lib tushadi. U bir bosishda " +
          "tasdiqlaydi — shundagina summa o'zgaradi. Kim so'ragani va " +
          "kim tasdiqlagani auditda qoladi, ya'ni sizni himoya qiladi.",
        optional: true,
      },
    ],
  },
];

export const LESSONS: GuideLesson[] = [...COMMON, ...ADMIN];

/** Shu lavozim uchun darslar */
export function lessonsForRole(role?: string): GuideLesson[] {
  if (!role) return [];
  return LESSONS.filter(
    (l) => l.roles.includes("*") || l.roles.includes(role)
  );
}

/**
 * Darsi bor lavozimlar ro'yxati (umumiy "*" darslardan tashqari).
 * Asoschi profilda "boshqa lavozim ko'zi bilan" tanlaganda kerak:
 * o'zi ko'rmaydigan darslarni ham tekshirib ko'ra oladi.
 */
export function rolesWithLessons(): string[] {
  const out: string[] = [];
  for (const l of LESSONS) {
    for (const r of l.roles) {
      if (r !== "*" && !out.includes(r)) out.push(r);
    }
  }
  return out;
}

export function lessonById(id: string): GuideLesson | undefined {
  return LESSONS.find((l) => l.id === id);
}
