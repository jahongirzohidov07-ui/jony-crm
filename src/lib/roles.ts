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

// ---- Tashqi ----
export const PARENT = "parent";
export const STUDENT = "student";

export const UZ_LABELS: Record<string, string> = {
  [FOUNDER]: "Asoschi",
  [FINANCE_DIRECTOR]: "Moliya direktori",
  [ACCOUNTANT]: "Buxgalter",
  [BRANCH_MANAGER]: "Filial rahbari",
  [SALES_HEAD]: "Sotuv rahbari",
  [SALES_MANAGER]: "Sotuv menejeri",
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
  [PARENT]: "Ota-ona",
  [STUDENT]: "O'quvchi",
};

export const ALL_ROLES = [
  FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, BRANCH_MANAGER,
  SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, SMM_MANAGER,
  ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
  EXAMINER, HEAD_EXAMINER, HR_MANAGER, FACILITY_MANAGER,
  PARENT, STUDENT,
];

export const ROLE_GROUPS: { key: string; label: string; roles: string[] }[] = [
  { key: "leadership", label: "Rahbariyat",
    roles: [FOUNDER, FINANCE_DIRECTOR, ACCOUNTANT, BRANCH_MANAGER] },
  { key: "sales", label: "Sotuv va marketing",
    roles: [SALES_HEAD, SALES_MANAGER, ADMINISTRATOR, SMM_MANAGER] },
  { key: "academic", label: "O'quv bo'limi",
    roles: [ACADEMIC_HEAD, TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
            EXAMINER, HEAD_EXAMINER] },
  { key: "support", label: "Qo'llab-quvvatlash",
    roles: [HR_MANAGER, FACILITY_MANAGER] },
  { key: "external", label: "Tashqi", roles: [PARENT, STUDENT] },
];

export const EXTERNAL_ROLES = [PARENT, STUDENT];
export const STAFF_ROLES = ALL_ROLES.filter(
  (r) => !EXTERNAL_ROLES.includes(r)
);

export const FULL_ACCESS = [FOUNDER, BRANCH_MANAGER];
export const TEACHING_STAFF = [
  ...FULL_ACCESS,
  SALES_HEAD, SALES_MANAGER, ADMINISTRATOR,
  TEACHER, SUPPORT_TEACHER, HEAD_SUPPORT,
  EXAMINER, HEAD_EXAMINER, ACADEMIC_HEAD,
];

/** Xodimlar ro'yxatini ko'ra oladiganlar. */
export const STAFF_VIEWERS = [...FULL_ACCESS, HR_MANAGER, FINANCE_DIRECTOR];

/** Xodim yaratish va rol berish - faqat asoschi. */
export const USER_ADMIN = [FOUNDER];

export const FINANCE_ACCESS = [...FULL_ACCESS, FINANCE_DIRECTOR, ACCOUNTANT];

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
export const MARKETING_ACCESS = [...FULL_ACCESS, SMM_MANAGER, SALES_HEAD];
export const AUDIT_VIEW = [FOUNDER, BRANCH_MANAGER, FINANCE_DIRECTOR];
export const PROFIT_VIEW = [...FULL_ACCESS, FINANCE_DIRECTOR];

export const ACADEMIC_ACCESS = [...FULL_ACCESS, ACADEMIC_HEAD, HEAD_SUPPORT];
export const ACADEMIC_VIEW = [
  ...ACADEMIC_ACCESS,
  TEACHER, SUPPORT_TEACHER, SALES_HEAD, SALES_MANAGER,
];

/** Imtihon moduli — Examiner asoschiga bo'ysunadi. */
export const EXAM_ACCESS = [FOUNDER, EXAMINER, HEAD_EXAMINER];
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
export const SALARY_PAY = [...FULL_ACCESS, FINANCE_DIRECTOR, ACCOUNTANT];

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
];

/** Faqat umumiy statistikani ko'radiganlar. */
export const DASHBOARD_ONLY = [SMM_MANAGER];

export function can(role: string | undefined, allowed: string[]): boolean {
  return !!role && allowed.includes(role);
}

export function roleLabel(role: string | undefined): string {
  if (!role) return "—";
  return UZ_LABELS[role] ?? role;
}

/**
 * Kim kimga qanday rol bera oladi. Rol berish tizimdagi eng xavfli
 * amal, shuning uchun faqat asoschi barcha rollarni bera oladi.
 */
export function assignableRoles(myRole: string | undefined): string[] {
  if (myRole === FOUNDER) return ALL_ROLES;
  if (myRole === BRANCH_MANAGER)
    return [
      SALES_MANAGER, ADMINISTRATOR, TEACHER, SUPPORT_TEACHER,
      EXAMINER, PARENT, STUDENT,
    ];
  if (myRole === HR_MANAGER)
    return [TEACHER, SUPPORT_TEACHER, ADMINISTRATOR, SALES_MANAGER];
  return [];
}

// ---- SMM: kontent quvuri ----
export const SMM_ACCESS = [FOUNDER, BRANCH_MANAGER, SMM_MANAGER, SALES_HEAD];
export const CONTENT_REQUESTER = [
  FOUNDER, BRANCH_MANAGER, SMM_MANAGER, SALES_HEAD, SALES_MANAGER,
  ACADEMIC_HEAD, ADMINISTRATOR,
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
