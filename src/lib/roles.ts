// Mirrors backend/roles.py - keep in sync.

export const ADMINISTRATOR = "administrator";
export const BRANCH_MANAGER = "branch_manager";
export const TEACHER = "teacher";
export const SUPPORT_TEACHER = "support_teacher";
export const EXAMINER = "examiner";
export const HR_MANAGER = "hr_manager";
export const SMM_MANAGER = "smm_manager";

export const UZ_LABELS: Record<string, string> = {
  [ADMINISTRATOR]: "Administrator",
  [BRANCH_MANAGER]: "Filial menejeri",
  [TEACHER]: "O'qituvchi",
  [SUPPORT_TEACHER]: "Support teacher",
  [EXAMINER]: "Examiner",
  [HR_MANAGER]: "HR manager",
  [SMM_MANAGER]: "SMM manager",
};

export const ALL_ROLES = [
  ADMINISTRATOR,
  BRANCH_MANAGER,
  TEACHER,
  SUPPORT_TEACHER,
  EXAMINER,
  HR_MANAGER,
  SMM_MANAGER,
];

export const FULL_ACCESS = [ADMINISTRATOR, BRANCH_MANAGER];
export const TEACHING_STAFF = [...FULL_ACCESS, TEACHER, SUPPORT_TEACHER, EXAMINER];
export const STAFF_MANAGERS = [...FULL_ACCESS, HR_MANAGER];
export const FINANCE_ACCESS = FULL_ACCESS;

// Lidlar bilan ishlaydiganlar. SMM manager ataylab kiritilgan - Instagram
// va Telegram lidlari uniki. Support teacher qabulda tashrifchilar bilan
// ishlaydi. backend/roles.py'dagi LEAD_ACCESS bilan bir xil.
export const LEAD_ACCESS = [...FULL_ACCESS, SMM_MANAGER, SUPPORT_TEACHER];

// Roles that are org-wide (not tied to one branch) - only a real
// administrator may create or edit accounts with these roles.
// Mirrors backend main.py's _guard_role_assignment - keep in sync.
const ORG_WIDE_ROLES = [ADMINISTRATOR, HR_MANAGER, SMM_MANAGER];
const BRANCH_SCOPED_ROLES = [BRANCH_MANAGER, TEACHER, SUPPORT_TEACHER, EXAMINER];

export function roleLabel(role?: string): string {
  if (!role) return "";
  return UZ_LABELS[role] || role;
}

export function can(role: string | undefined, group: string[]): boolean {
  return !!role && group.includes(role);
}

/** Which roles `requesterRole` is allowed to assign when creating/editing a
 * staff account. Administrator can assign anything; HR manager and branch
 * manager can only assign branch-scoped roles (not administrator/HR/SMM). */
export function assignableRoles(requesterRole?: string): string[] {
  if (requesterRole === ADMINISTRATOR) return ALL_ROLES;
  if (requesterRole === HR_MANAGER || requesterRole === BRANCH_MANAGER) {
    return BRANCH_SCOPED_ROLES;
  }
  return [];
}

export { ORG_WIDE_ROLES };
