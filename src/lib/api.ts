const TOKEN_KEY = "jony_crm_token";

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`/api${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Sessiya tugadi, qayta kiring");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Xatolik: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T,>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  delete: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
};

// ---------- Types ----------
export interface Branch {
  id: number;
  name: string;
  address?: string;
}

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: string;
  branch_id?: number | null;
  branch?: Branch;
  is_active: boolean;
}

export interface Teacher {
  id: number;
  full_name: string;
  phone?: string;
  subject?: string;
  branch_id?: number;
  branch?: Branch;
  hired_date?: string | null;
  left_date?: string | null;
  /** 1 = hozir ishlayapti, 0 = ishdan ketgan. */
  is_active?: number;
}

export interface Group {
  id: number;
  name: string;
  room?: string;
  teacher_id?: number;
  branch_id?: number;
  monthly_fee: number;
  lesson_price: number;
  standard_lessons_per_month: number;
  teacher_rate_per_student: number;
  teacher?: Teacher;
  branch?: Branch;
  student_count: number;
}

export interface Payment {
  id: number;
  amount: number;
  kind: "payment" | "charge" | "discount";
  method?: string | null;
  note?: string;
  created_by?: string;
  period?: string;
  created_at: string;
}

export interface Lesson {
  id: number;
  group_id: number;
  teacher_id?: number;
  teacher?: Teacher;
  date: string;
  note?: string;
  created_by?: string;
  created_at: string;
}

export interface StudentChargeResult {
  student_id: number;
  student_name: string;
  billable_lessons: number;
  amount: number;
  already_charged: boolean;
  created: boolean;
}

export interface BillingRunResult {
  period: string;
  held_lessons: number;
  committed: boolean;
  results: StudentChargeResult[];
}

export interface TeacherPayout {
  id: number | null;
  teacher_id: number;
  teacher?: Teacher;
  group_id: number;
  period: string;
  student_count: number;
  held_lessons: number;
  taught_lessons: number;
  amount: number;
  paid: boolean;
}

export interface PayrollRunResult {
  period: string;
  committed: boolean;
  results: TeacherPayout[];
}

export interface Student {
  id: number;
  full_name: string;
  phone?: string;
  parent_phone?: string;
  birth_date?: string;
  enrolled_date?: string;
  status: string;
  note?: string;
  group?: Group;
  branch?: Branch;
  balance: number;
}

export interface StudentDetail extends Student {
  payments: Payment[];
}

export interface DashboardStats {
  active_students: number;
  trial_students: number;
  frozen_students: number;
  total_groups: number;
  total_teachers: number;
  month_income: number;
  total_debt: number;
  debtor_count: number;
}

export interface TrendPoint {
  period: string; // "YYYY-MM"
  income: number;
}

export interface StaffOption {
  id: number;
  full_name: string;
  role: string;
}

export interface Lead {
  id: number;
  full_name: string;
  phone?: string | null;
  source: string;
  stage: string;
  address?: string | null;
  school?: string | null;
  grade?: string | null;
  note?: string | null;
  branch_id?: number | null;
  branch?: Branch | null;
  assigned_user_id?: number | null;
  assigned_user?: StaffOption | null;
  converted_student_id?: number | null;
  created_at: string;
  updated_at?: string | null;
}

export interface Expense {
  id: number;
  date: string; // YYYY-MM-DD
  category: string;
  amount: number;
  note?: string | null;
  branch_id?: number | null;
  branch?: Branch | null;
  created_by?: string | null;
  created_at: string;
}

// ---------- Hisobotlar ----------
export interface CashflowRow {
  period: string; // "YYYY-MM"
  cash: number;
  card: number;
  terminal: number;
  other: number;
  income: number;
  expenses: number;
  payroll: number;
  outflow: number;
  net: number;
}

export interface CashflowReport {
  rows: CashflowRow[];
  totals: Omit<CashflowRow, "period">;
}

export interface PnlLine {
  category: string;
  amount: number;
  /** true = qo'lda kiritilmaydi, tizim o'zi hisoblaydi (ustozlar ish haqi). */
  auto: boolean;
}

export interface PnlReport {
  period: string;
  income: number;
  income_by_method: Record<string, number>;
  expense_lines: PnlLine[];
  expenses_total: number;
  payroll_total: number;
  outflow_total: number;
  profit: number;
  margin: number;
}

export type LtvDimension = "branch" | "teacher" | "group";

export interface LtvRow {
  key: number | null;
  label: string;
  students: number;
  left: number;
  avg_months: number;
  avg_revenue: number;
  total_revenue: number;
  churn: number;
}

export interface LtvReport {
  dimension: LtvDimension;
  rows: LtvRow[];
  overall: {
    students: number;
    left: number;
    avg_months: number;
    avg_revenue: number;
    total_revenue: number;
  } | null;
}

export interface RetentionRow {
  id: number;
  full_name: string;
  branch?: string | null;
  hired_date: string;
  left_date?: string | null;
  active: boolean;
  months: number;
}

export interface RetentionReport {
  rows: RetentionRow[];
  summary: {
    active: number;
    left: number;
    left_last_12m: number;
    avg_tenure_active: number;
    avg_tenure_left: number;
    turnover_12m: number;
  };
}

export type StudentGrowthWindow = "1m" | "6m" | "1y" | "all";

export interface StudentGrowthPoint {
  period: string; // "YYYY-MM-DD" when granularity is "day", "YYYY-MM" when "month"
  count: number;
}

export interface StudentGrowthResponse {
  granularity: "day" | "month";
  points: StudentGrowthPoint[];
}
