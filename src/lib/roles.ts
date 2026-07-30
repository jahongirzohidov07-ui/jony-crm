// Diqqat: bizning o'quv markazda "Administrator" deganda SOTUV MENEJERI
// tushuniladi, tizim egasi emas. Tizim egasi - ASOSCHI (founder).
// backend/roles.py bilan bir xil bo'lishi shart.

export const FOUNDER = "founder";
export const BRANCH_MANAGER = "branch_manager";
export const SALES_MANAGER = "sales_manager";
export const TEACHER = "teacher";
export const SUPPORT_TEACHER = "support_teacher";
export const EXAMINER = "examiner";
export const HR_MANAGER = "hr_manager";
export const SMM_MANAGER = "smm_manager";
export const ACADEMIC_HEAD = "academic_head";

export const UZ_LABELS: Record<string, string> = {
  [FOUNDER]: "Asoschi",
  [BRANCH_MANAGER]: "Filial menejeri",
  [SALES_MANAGER]: "Administrator (sotuv menejeri)",
  [TEACHER]: "O'qituvchi",
  [SUPPORT_TEACHER]: "Support teacher",
  [EXAMINER]: "Examiner",
  [HR_MANAGER]: "HR manager",
  [SMM_MANAGER]: "SMM manager",
  [ACADEMIC_HEAD]: "O'quv bo'limi rahbari",
};

export const ALL_ROLES = [
  FOUNDER,
  BRANCH_MANAGER,
  SALES_MANAGER,
  TEACHER,
  SUPPORT_TEACHER,
  EXAMINER,
  HR_MANAGER,
  SMM_MANAGER,
  ACADEMIC_HEAD,
];

export const FULL_ACCESS = [FOUNDER, BRANCH_MANAGER];
export const TEACHING_STAFF = [
  ...FULL_ACCESS,
  SALES_MANAGER,
  TEACHER,
  SUPPORT_TEACHER,
  EXAMINER,
  ACADEMIC_HEAD,
];

/** Xodimlar ro'yxatini ko'ra oladiganlar. */
export const STAFF_VIEWERS = [...FULL_ACCESS, HR_MANAGER];

/** Xodim yaratish va rol berish - faqat asoschi. */
export const USER_ADMIN = [FOUNDER];

export const FINANCE_ACCESS = FULL_ACCESS;

/** Lidlar bilan ishlaydiganlar. */
export const LEAD_ACCESS = [
  ...FULL_ACCESS,
  SALES_MANAGER,
  SMM_MANAGER,
  SUPPORT_TEACHER,
];

const ORG_WIDE_ROLES = [FOUNDER, HR_MANAGER, SMM_MANAGER];

export function roleLabel(role?: string): string {
  if (!role) return "";
  return UZ_LABELS[role] || role;
}

export function can(role: string | undefined, group: string[]): boolean {
  return !!role && group.includes(role);
}

/** Asoschi istalgan rolni bera oladi; boshqalar umuman bera olmaydi. */
export function assignableRoles(requesterRole?: string): string[] {
  return requesterRole === FOUNDER ? ALL_ROLES : [];
}

export { ORG_WIDE_ROLES };

/** HR bo'limi - kadrlar bilan ishlaydiganlar. */
export const HR_ACCESS = [...FULL_ACCESS, HR_MANAGER];

/** Marketing bo'limi. */
export const MARKETING_ACCESS = [...FULL_ACCESS, SMM_MANAGER];

/** Audit logni ko'radiganlar. */
export const AUDIT_VIEW = [FOUNDER, BRANCH_MANAGER];

/** Asoschi paneli - umumiy foyda ko'rinadigan joy. */
export const PROFIT_VIEW = FULL_ACCESS;


/** O'quv bo'limini boshqaradiganlar. */
export const ACADEMIC_ACCESS = [...FULL_ACCESS, ACADEMIC_HEAD];

/** Risk ro'yxatini ko'radiganlar - ustoz ham o'z o'quvchisini ko'radi. */
export const ACADEMIC_VIEW = [
  ...ACADEMIC_ACCESS,
  TEACHER,
  SUPPORT_TEACHER,
  SALES_MANAGER,
];

/** Imtihon moduli — Examiner asoschiga bo'ysunadi, o'quv bo'limiga emas. */
export const EXAM_ACCESS = [FOUNDER, EXAMINER];
export const EXAM_VIEW = [
  ...EXAM_ACCESS,
  BRANCH_MANAGER,
  ACADEMIC_HEAD,
  TEACHER,
];

/** Support teacher paneli. */
export const SUPPORT_ACCESS = [
  ...FULL_ACCESS,
  ACADEMIC_HEAD,
  SUPPORT_TEACHER,
];

/** Chegirma: kim so'ray oladi, kim tasdiqlaydi. */
export const DISCOUNT_REQUEST = [...FULL_ACCESS, SALES_MANAGER];
export const DISCOUNT_APPROVE = [FOUNDER, BRANCH_MANAGER];

/** Vazifalar. */
export const TASK_ACCESS = [
  ...FULL_ACCESS,
  HR_MANAGER,
  SMM_MANAGER,
  ACADEMIC_HEAD,
  SALES_MANAGER,
  TEACHER,
  SUPPORT_TEACHER,
  EXAMINER,
];
export const TASK_MANAGE = [...FULL_ACCESS, HR_MANAGER, ACADEMIC_HEAD];

/** Ombor va aktivlar. */
export const INVENTORY_ACCESS = [...FULL_ACCESS, HR_MANAGER];
export const INVENTORY_VIEW = [
  ...INVENTORY_ACCESS,
  ACADEMIC_HEAD,
  SUPPORT_TEACHER,
];
