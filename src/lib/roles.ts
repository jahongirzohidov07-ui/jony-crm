// backend/roles.py bilan bir xil bo'lishi shart.
//
// Diqqat: "Administrator" va "Sotuv menejeri" — ikki alohida rol.
// Administrator qabul va kassa bilan, sotuv menejeri lidlar bilan
// ishlaydi. Tizim egasi — ASOSCHI (founder).

// ---- Rahbariyat ----
export const FOUNDER = "founder";
export const FINANCE_DIRECTOR = "finance_director";
export const ACCOUNTANT = "accountant";
export const BRANCH_MANAGER = "branch_manager";
/** HAMKOR MARKAZ (Stech) RAHBARI — haqiqiy rol emas, virtual belgi
 * (2026-09-17, api roles.PARTNER_HEAD). Ro'yxatda bo'lsa, asosiy
 * filiali hamkor markaz bo'lgan filial rahbari ham o'tadi. */
export const PARTNER_HEAD = "partner_head";
let _partnerHead = false;
export function setPartnerHead(v: boolean) {
  _partnerHead = v;
}
export function isPartnerHead(): boolean {
  return _partnerHead;
}

// ---- Sotuv va marketing ----
export const SALES_HEAD = "sales_head";
export const SALES_MANAGER = "sales_manager";
export const ADMINISTRATOR = "administrator";
export const SMM_MANAGER = "smm_manager";

// ---- O'quv bo'limi ----
export const ACADEMIC_HEAD = "academic_head";
export const TEACHER = "teacher";
export const SUPPORT_TEACHER = "support_teacher";
export const HEAD_SUPPORT = "head_support";
export const EXAMINER = "examiner";
export const HEAD_EXAMINER = "head_examiner";

// ---- Qo'llab-quvvatlash ----
export const HR_MANAGER = "hr_manager";
export const FACILITY_MANAGER = "facility_manager";
export const EVENT_MANAGER = "event_manager";

// ---- Tashqi ----
export const PARENT = "parent";
export const STUDENT = "student";

export const UZ_LABELS: Record<string, string> = {
  [FOUNDER]: "Asoschi",
  [FINANCE_DIRECTOR]: "Moliya direktori",
  [ACCOUNTANT]: "Buxgalter",
  [BRANCH_MANAGER]: "Filial rahbari",
  [SALES_HEAD]: "Sotuv rahbari",
  [SALES_MANAGER]: "Administrator",
  // Eski hisoblar sales_manager'ga ko'chirildi — ikkalasi bir xil ish.
  [ADMINISTRATOR]: "Administrator",
  [SMM_MANAGER]: "Marketolog / SMM",
  [ACADEMIC_HEAD]: "O'quv bo'limi rahbari",
  [TEACHER]: "O'qituvchi",
  [SUPPORT_TEACHER]: "Support teacher",
  [HEAD_SUPPORT]: "Support teacherlar boshlig'i",
  [EXAMINER]: "Examiner",
  [HEAD_EXAMINER]: "Examinerlar boshlig'i",
  [HR_MANAGER]: "HR menejer",
  [FACILITY_MANAGER]: "Xo'jalik ishlari menejeri",
  [EVENT_MANAGER]: "Event menejer (tadbirlar)",
  [PARENT]: "Ota-ona",
  [STUDENT]: "O'quvchi",
};

// Tanlanadigan rollar. "Administrator (qabul)" bu yerda yo'q — u
// Administrator bilan birlashdi, eski hisoblar ham shunga ko'chdi.
export const ALL_ROLES = [
  FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, BRANCH_MANAGER,
  SALES_HEAD, SALES_MANAGER, SMM_MANAGER,
  ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
  EXAMINER, HEAD_EXAMINER, HR_MANAGER, FACILITY_MANAGER, EVENT_MANAGER,
  PARENT, STUDENT,
];

export const ROLE_GROUPS: { key: string; label: string; roles: string[] }[] = [
  { key: "leadership", label: "Rahbariyat",
    roles: [FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, BRANCH_MANAGER] },
  { key: "sales", label: "Sotuv va marketing",
    roles: [SALES_HEAD, SALES_MANAGER, SMM_MANAGER] },
  { key: "academic", label: "O'quv bo'limi",
    roles: [ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
            EXAMINER, HEAD_EXAMINER] },
  { key: "support", label: "Qo'llab-quvvatlash",
    roles: [HR_MANAGER, FACILITY_MANAGER, EVENT_MANAGER] },
  { key: "external", label: "Tashqi", roles: [PARENT, STUDENT] },
];

export const EXTERNAL_ROLES = [PARENT, STUDENT];
// Eski "administrator" hisoblari ham xodim — ro'yxatdan tushib
// qolmasin, aks holda vazifa va oylik ularga ko'rinmay qoladi.
export const STAFF_ROLES = [
  ...ALL_ROLES.filter((r) => !EXTERNAL_ROLES.includes(r)),
  ADMINISTRATOR,
];

export const FULL_ACCESS = [FOUNDER, BRANCH_MANAGER];
// Guruh ochish/tahrirlash — o'quv bo'limi rahbari ham qiladi
export const GROUP_MANAGE = [...FULL_ACCESS, ACADEMIC_HEAD, HR_MANAGER];
// Tepadagi filial almashtirgich — butun tashkilotni ko'radiganlar
export const BRANCH_SWITCH = [
  FOUNDER, ACADEMIC_HEAD, SMM_MANAGER, HR_MANAGER, FINANCE_DIRECTOR,
  // 2026-08-22, Jahongir: "Exam manager boshligi bor bizda Husniddin
  // qilganmiz u butun filiallarni examlarini korib turishi kerak" —
  // examinerlar boshlig'i butun tashkilotni nazorat qiladi.
  HEAD_EXAMINER,
];

/**
 * FILIALI BIRIKTIRILGAN BO'LSA HAM BUTUN TASHKILOTNI KO'RADIGANLAR.
 *
 * Odatda xodimga filial biriktirilgan bo'lsa, u faqat o'sha filialni
 * ko'radi va tanlagich "Barcha filiallar"ni bermaydi (2026-08-11
 * qoidasi). Lekin ba'zi lavozimlar mohiyatan butun tashkilotniki:
 * asoschi va examinerlar boshlig'i. Ularga biriktirilgan filial —
 * shunchaki "qayerda o'tiradi" degani, ish doirasi emas.
 *
 * Backend allaqachon shunday ishlaydi (roles.ORG_WIDE_ROLES) — bu
 * ro'yxat frontenddagi qamalib qolishni ochadi.
 */
// 2026-09-16, Jahongir: "HR lavozimi uchun barcha filiallar degan
// qismni qo'yib ber" — HR biriktirilgan filialga qamalib qolgani
// uchun filial belgilamay ariza to'ldirgan nomzodlar unga ko'rinmasdi.
export const ALL_BRANCH_ROLES = [FOUNDER, HEAD_EXAMINER, HR_MANAGER];
export const TEACHING_STAFF = [
  ...FULL_ACCESS,
  SALES_HEAD, SALES_MANAGER, ADMINISTRATOR,
  TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
  EXAMINER, HEAD_EXAMINER, ACADEMIC_HEAD,
];

/** Dars rejalari: ustozlar va rahbariyat (support, examiner, admin — yo'q). */
export const PLANS_ACCESS = [
  ...FULL_ACCESS, ACADEMIC_HEAD, TEACHER, SALES_HEAD, SALES_MANAGER,
];

/** Dars jadvali, davomat va baholashni KO'RA oladiganlar
 *  (HR belgilay olmaydi — faqat kuzatadi). */
export const SCHEDULE_VIEW = [...TEACHING_STAFF, HR_MANAGER];

/** Supportlar jadvalini ko'radiganlar. */
export const SUPPORT_TT_VIEW = [
  ...FULL_ACCESS, HEAD_SUPPORT, ACADEMIC_HEAD, HR_MANAGER,
];

/** Refund: sotuv menejeri so'raydi, rahbar/moliyachi tasdiqlaydi. */
export const REFUND_REQUEST = [SALES_MANAGER, FOUNDER, PARTNER_HEAD];
export const REFUND_APPROVE = [BRANCH_MANAGER, FINANCE_DIRECTOR, FOUNDER];

/** Xodimlar ro'yxatini ko'ra oladiganlar. */
export const STAFF_VIEWERS = [...FULL_ACCESS, HR_MANAGER, FINANCE_DIRECTOR];

/** Xodim yaratish va rol berish - faqat asoschi. */
export const USER_ADMIN = [FOUNDER];

export const FINANCE_ACCESS = [...FULL_ACCESS, FINANCE_DIRECTOR, ACCOUNTANT];

/** Tadbirlar va tug'ilgan kunlar (2026-09-14) — backend roles.EVENTS_* bilan bir xil. */
export const EVENTS_ACCESS = [...FULL_ACCESS, EVENT_MANAGER, HR_MANAGER, SMM_MANAGER];
export const EVENTS_MANAGE = [...FULL_ACCESS, EVENT_MANAGER];

/**
 * Coin balansini to'g'rilash (o'quvchi kartasidagi qalamcha).
 *
 * 2026-09-01, Jahongir: "filial rahbarlari balansni tahrirlash
 * huquqi bormi yoq bolsa shu tahrirlash huquqi bolsin".
 *
 * PUL balansi filial rahbariga allaqachon ochiq edi (CASH_ACCESS va
 * PAYMENT_EDIT). Yopiq bo'lgani COIN balansi edi. Server filial
 * rahbarini O'Z FILIALI o'quvchisi bilan cheklaydi.
 */
export const COIN_BALANCE_EDIT = [FOUNDER, BRANCH_MANAGER];

/**
 * PUL BALANSINI TO'G'RILASH (2026-09-26, Jahongir: "o'quvchi kartasiga
 * balans tahrirlash qo'shib ber faqat filial rahbariga ruxsat
 * berilsin"). Server ham faqat filial rahbariga va faqat o'z filiali
 * o'quvchisiga ruxsat beradi (roles.MONEY_BALANCE_EDIT).
 */
export const MONEY_BALANCE_EDIT = [BRANCH_MANAGER];

/**
 * Kassa: pul qabul qilish, qarzdorlar, to'lov foizi.
 * Administrator shu ishni qiladi — lekin FOYDANI ko'rmaydi.
 */
export const CASH_ACCESS = [
  ...FINANCE_ACCESS, SALES_HEAD, SALES_MANAGER, ADMINISTRATOR,
];

/** Lidlar bilan ishlaydiganlar. */
export const LEAD_ACCESS = [
  ...FULL_ACCESS,
  SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, SMM_MANAGER, SUPPORT_TEACHER,
];

export const HR_ACCESS = [...FULL_ACCESS, HR_MANAGER];

/** Nomzodni KO'RISH (2026-08-16, Jahongir: "nomzod o'qituvchi bo'lsa
 *  o'quv bo'limi rahbariga ham ko'rinish kerak. shunda baholay
 *  olardi"). O'quv bo'limi rahbariga faqat USTOZ nomzodlari
 *  ko'rinadi (server ham shuni cheklaydi) va u kartani TAHRIRLAY
 *  olmaydi — faqat dars baholaydi. */
export const HR_CANDIDATE_VIEW = [...HR_ACCESS, ACADEMIC_HEAD];
export const MARKETING_ACCESS = [...FULL_ACCESS, SMM_MANAGER, SALES_HEAD];
export const AUDIT_VIEW = [FOUNDER, BRANCH_MANAGER, HR_MANAGER];
export const PROFIT_VIEW = [...FULL_ACCESS, FINANCE_DIRECTOR];

export const ACADEMIC_ACCESS = [...FULL_ACCESS, ACADEMIC_HEAD, HEAD_SUPPORT];
export const ACADEMIC_VIEW = [
  ...ACADEMIC_ACCESS,
  TEACHER, SUPPORT_TEACHER, SALES_HEAD, SALES_MANAGER,
];

/** Imtihon moduli — Examiner asoschiga bo'ysunadi. */
export const EXAM_ACCESS = [FOUNDER, EXAMINER, HEAD_EXAMINER];
/** Imtihon buyurtmasini kim qabul qiladi. */
export const EXAM_ORDER_ACCEPT = EXAM_ACCESS;
/** Testni tahrirlash va o'chirish (2026-09-17) — api/roles.py EXAM_EDIT. */
export const EXAM_EDIT = [FOUNDER, BRANCH_MANAGER, HEAD_EXAMINER];
export const EXAM_VIEW = [
  ...EXAM_ACCESS,
  BRANCH_MANAGER, ACADEMIC_HEAD, TEACHER,
];

export const SUPPORT_ACCESS = [
  ...FULL_ACCESS,
  ACADEMIC_HEAD, SUPPORT_TEACHER, HEAD_SUPPORT,
];

/** Chegirma: kim so'raydi, kim tasdiqlaydi. */
export const DISCOUNT_REQUEST = [
  ...FULL_ACCESS, SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, FINANCE_DIRECTOR,
];
export const DISCOUNT_APPROVE = [FOUNDER, BRANCH_MANAGER, FINANCE_DIRECTOR];

/** Vazifalar — har bir xodimda bor. */
export const TASK_ACCESS = STAFF_ROLES;
export const TASK_MANAGE = [
  ...FULL_ACCESS, HR_MANAGER, ACADEMIC_HEAD, SALES_HEAD,
  HEAD_EXAMINER, HEAD_SUPPORT,
];

/** Ombor va aktivlar. */
export const INVENTORY_ACCESS = [
  ...FULL_ACCESS, HR_MANAGER, FACILITY_MANAGER,
];
export const INVENTORY_VIEW = [
  ...INVENTORY_ACCESS, ACADEMIC_HEAD, SUPPORT_TEACHER, ACCOUNTANT,
];

/** Ustoz o'z oyligini ko'radi; boshqaning oyligi ko'rinmaydi. */
export const SALARY_SELF_VIEW = STAFF_ROLES;
/** Oylik beradi. Administrator — faqat o'z filialiga (2026-09-16). */
export const SALARY_PAY = [...FULL_ACCESS, FINANCE_DIRECTOR, ACCOUNTANT, ADMINISTRATOR];

/** Moliyadagi "Oyliklar" bo'limi — examiner va support teacher oyligi.
 *  Administrator bu yerda YO'Q: u oylikni Xarajatlar -> Oylik orqali
 *  beradi, hammaning oyligi ro'yxatini ko'rmaydi. */
export const PAYROLL_VIEW = [
  ...FULL_ACCESS, FINANCE_DIRECTOR, ACCOUNTANT,
  HR_MANAGER, ACADEMIC_HEAD, HEAD_EXAMINER, HEAD_SUPPORT,
];

/**
 * Shu oy to'lov qilganlar ro'yxati. Bu yerda xarajat ham, foyda ham
 * yo'q — faqat kim to'ladi. Shuning uchun administratorga ham ochiq.
 */
export const PAYMENT_LIST_VIEW = [
  FOUNDER, BRANCH_MANAGER, FINANCE_DIRECTOR, ACCOUNTANT,
  SALES_MANAGER, ADMINISTRATOR,
];

/** Qarzdorlar bilan ishlaydiganlar. */
export const DEBTOR_ACCESS = [
  ...FULL_ACCESS, SALES_HEAD, SALES_MANAGER, ADMINISTRATOR,
  FINANCE_DIRECTOR, ACCOUNTANT,
];

/** Ruxsatlar matritsasi — faqat asoschi. */
export const PERMISSION_ADMIN = [FOUNDER];

/** Butun tashkilotni ko'radigan rollar (filialga bog'lanmagan). */
export const ORG_WIDE_ROLES = [
  FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, HR_MANAGER, SMM_MANAGER,
  ACADEMIC_HEAD, SALES_HEAD, HEAD_EXAMINER, HEAD_SUPPORT, FACILITY_MANAGER,
  EVENT_MANAGER,
];

/** Faqat umumiy statistikani ko'radiganlar. */
export const DASHBOARD_ONLY = [SMM_MANAGER];

export function can(role: string | undefined, allowed: string[]): boolean {
  if (!role) return false;
  return allowed.includes(role)
    || (_partnerHead && role === BRANCH_MANAGER && allowed.includes(PARTNER_HEAD));
}

/** Asoschi yoki (o'z markazida) hamkor markaz rahbari. */
export function founderLike(role: string | undefined): boolean {
  return role === FOUNDER || (_partnerHead && role === BRANCH_MANAGER);
}

export function roleLabel(role: string | undefined): string {
  if (!role) return "—";
  return UZ_LABELS[role] ?? role;
}

/**
 * Kim kimga qanday rol bera oladi. Rol berish tizimdagi eng xavfli
 * amal, shuning uchun faqat asoschi barcha rollarni bera oladi.
 */
/** HR HAMMAGA xodim ochadi va login/parol beradi — faqat asoschi va
 *  filial rahbari mustasno: ularni faqat asoschi tayinlaydi. */
/** DIQQAT: "Ota-ona" va "O'quvchi" ATAYLAB YO'Q (2026-08-10) —
 *  ular xodim emas va hisobi QO'LDA ochilmaydi:
 *   - o'quvchi hisobi o'quvchi kartasi bilan AVTOMAT ochiladi
 *     (login = telefon, parol = jonyjony);
 *   - ota-ona umuman hisobsiz, maxsus havola bilan kiradi. */
export const HR_ASSIGNABLE_ROLES = [
  TEACHER, SUPPORT_TEACHER, EXAMINER, ADMINISTRATOR,
  SALES_MANAGER, SMM_MANAGER, ACCOUNTANT, FACILITY_MANAGER,
  SALES_HEAD, ACADEMIC_HEAD, FINANCE_DIRECTOR,
  HEAD_EXAMINER, HEAD_SUPPORT, HR_MANAGER, EVENT_MANAGER,
];

/** Xodim sifatida qo'lda tayinlanadigan rollar (ota-ona/o'quvchisiz). */
export const STAFF_ASSIGNABLE_ROLES = ALL_ROLES.filter(
  (r) => r !== PARENT && r !== STUDENT,
);

export function assignableRoles(myRole: string | undefined): string[] {
  if (myRole === FOUNDER) return STAFF_ASSIGNABLE_ROLES;
  if (myRole === BRANCH_MANAGER)
    return [
      SALES_MANAGER, ADMINISTRATOR, TEACHER, SUPPORT_TEACHER,
      EXAMINER,
    ];
  if (myRole === HR_MANAGER) return HR_ASSIGNABLE_ROLES;
  return [];
}

// ---- SMM: kontent quvuri ----
export const SMM_ACCESS = [FOUNDER, BRANCH_MANAGER, SMM_MANAGER, SALES_HEAD];
export const CONTENT_REQUESTER = [
  FOUNDER, BRANCH_MANAGER, SMM_MANAGER, SALES_HEAD, SALES_MANAGER,
  ADMINISTRATOR,
];
/** G'oyani har qanday xodim yubora oladi. */
export const IDEA_SUBMIT = STAFF_ROLES;

/** Ijtimoiy inbox va atributsiya. */
export const INBOX_ACCESS = [
  FOUNDER, BRANCH_MANAGER, SMM_MANAGER, SALES_HEAD, SALES_MANAGER,
  ADMINISTRATOR,
];

/** Kim ustozga akkaunt ocha oladi. */
export const ACCOUNT_MANAGE = [FOUNDER, BRANCH_MANAGER, HR_MANAGER];

/** Ustoz o'z natijalarini ko'radi (boshqa ustozniki emas). */
export const SELF_STATS = [TEACHER, SUPPORT_TEACHER];

/**
 * Ustoz menyusi — ochiq ro'yxat.
 *
 * Boshqa rollarda menyu "kimga ruxsat bor" degan qoidadan chiqadi,
 * lekin ustozda buning teskarisi kerak: dars berishga aloqasi
 * bo'lmagan hech narsa turmasin. SMM, audit, ombor, boshqa
 * ustozlarning ro'yxati — bularning hech biri ustozning ishiga
 * kerak emas va faqat e'tiborni bo'ladi.
 */
export const TEACHER_MENU = [
  "/",
  "/timetable",
  "/my-groups",
  "/my-students",
  "/my-schedule",
  // DARS REJALARI (2026-09-26). PLANS_ACCESS ichida ustoz bor edi,
  // lekin ustoz menyusi shu ochiq ro'yxat bo'yicha kesilgani uchun
  // reja bandi baribir yo'qolib ketardi — ustoz dars rejalarini
  // umuman ko'rmasdi. Endi ro'yxatda.
  "/plans",
  "/my-books",
  "/my-exams",
  "/my-sessions",
  "/my-finance",
  "/my-results",
  "/my-career",
  "/development",
  "/gamification",
  "/complaints",
  "/tasks",
];

/**
 * Xodim kartasi: ko'rish, tahrirlash va rol berish — uch xil huquq.
 *
 * Ilgari uchalasi ham USER_ADMIN (faqat asoschi) ostida edi, shuning
 * uchun HR menejer xodimlar ro'yxatini umuman ocholmasdi.
 */
export const STAFF_EDIT = STAFF_VIEWERS;



// Examiner oyligi: o'zi ko'radi; ro'yxatni rahbariyat ko'radi
export const EXAMINER_PAY_OWN = [EXAMINER, HEAD_EXAMINER];
export const EXAMINER_SALARY_VIEW = [
  FOUNDER, HR_MANAGER, FINANCE_DIRECTOR, ACADEMIC_HEAD, HEAD_EXAMINER,
];

/** Jarima ballari (2026-09-16) — backend roles.EXAMINER_PENALTY_SET /
 *  SUPPORT_PENALTY_SET bilan bir xil. Examinerlar boshlig'i faqat
 *  examinerdan, HR ham examinerdan, ham supportdan ayiradi. */
export const EXAMINER_PENALTY_SET = [
  FOUNDER, HEAD_EXAMINER, HR_MANAGER, ACADEMIC_HEAD,
];
export const SUPPORT_PENALTY_SET = [FOUNDER, HR_MANAGER];

/** Na'munali xodim (intizom balli) — backend roles.CONDUCT_VIEW.
 *  HR — hammani; examinerlar boshlig'i — examinerlarni, support
 *  rahbari — supportlarni. Rahbarlarning o'zini faqat HR baholaydi
 *  (qaysi bo'lim va kim ko'rinishini server aytadi). */
export const CONDUCT_VIEW = [HR_MANAGER, HEAD_EXAMINER, HEAD_SUPPORT];

/** HR qora ro'yxati (2026-09-16) — backend roles.BLACKLIST_*.
 *  Ko'radi: asoschi, HR, filial rahbari. Qo'shadi/chiqaradi: asoschi, HR. */
export const BLACKLIST_VIEW = [FOUNDER, HR_MANAGER, BRANCH_MANAGER];
export const BLACKLIST_MANAGE = [FOUNDER, HR_MANAGER];

// Yillik Reja/Fakt jadvali kimga ko'rinadi
export const PLAN_VIEW = [
  FOUNDER, SMM_MANAGER, SALES_HEAD, SALES_MANAGER, BRANCH_MANAGER,
  FINANCE_DIRECTOR,
];

// O'quvchini muzlatish/faollashtirish/ko'chirish — faqat shu rollar
export const FREEZE_ROLES = [
  FOUNDER, SALES_MANAGER, ACADEMIC_HEAD, BRANCH_MANAGER,
];
// Boshqa guruhga (shu jumladan boshqa FILIALDAGI guruhga) o'tkazish —
// administrator ham (2026-09-23). Serverda: roles.STUDENT_TRANSFER.
export const STUDENT_TRANSFER = [...FREEZE_ROLES, ADMINISTRATOR];
// Support teacherni guruhga biriktirish
export const SUPPORT_ASSIGN = [FOUNDER, HEAD_SUPPORT, ACADEMIC_HEAD, HR_MANAGER];

// To'lov summasini tahrirlash — asoschi, moliyachi, filial rahbari
export const PAYMENT_EDIT = [FOUNDER, FINANCE_DIRECTOR, BRANCH_MANAGER];
// So'rovlarni VAZIFA ichida tasdiqlash uchun (2026-08-20)
export const PAYMENT_FIX_APPROVE = [...PAYMENT_EDIT];
export const RESCHEDULE_APPROVE = [...FULL_ACCESS, ACADEMIC_HEAD, HR_MANAGER];
