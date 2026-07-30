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

export const UZ_LABELS: Record<string, string> = {
  [FOUNDER]: "Asoschi",
  [BRANCH_MANAGER]: "Filial menejeri",
  [SALES_MANAGER]: "Administrator (sotuv menejeri)",
  [TEACHER]: "O'qituvchi",
  [SUPPORT_TEACHER]: "Support teacher",
  [EXAMINER]: "Examiner",
  [HR_MANAGER]: "HR manager",
  [SMM_MANAGER]: "SMM manager",
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
];

export const FULL_ACCESS = [FOUNDER, BRANCH_MANAGER];
export const TEACHING_STAFF = [
  ...FULL_ACCESS,
  SALES_MANAGER,
  TEACHER,
  SUPPORT_TEACHER,
  EXAMINER,
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
