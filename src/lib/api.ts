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
  /** Adminlar (sotuv menejeri) uchun fiks oylik. Faqat asoschi o'zgartiradi. */
  fix_salary?: number | null;
  public_id?: string | null;
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
  subject?: string | null;
  level?: string | null;
  /** Guruh boshlangan sana - yoqlama shundan oldin qo'yilmaydi. */
  start_date?: string | null;
  /** "09:00 - 11:00" */
  lesson_time?: string | null;
  /** "mon,wed,fri" */
  lesson_days?: string | null;
  monthly_fee: number;
  lesson_price: number;
  standard_lessons_per_month: number;
  teacher_rate_per_student: number;
  teacher?: Teacher;
  branch?: Branch;
  student_count: number;
  end_date?: string | null;
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
  public_id?: string | null;
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
  /** Arxivga o'tkazilganda avtomatik qo'yiladi - LTV shundan hisoblanadi. */
  left_date?: string | null;
  status: string;
  note?: string;
  group?: Group;
  branch?: Branch;
  balance: number;
  public_id?: string | null;
  parent_id?: number | null;
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
  month_payment_count: number;
  month_new_payment_count: number;
  staff_count: number;
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
  public_id?: string | null;
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
  channel?: string | null;
  method?: string | null;
}

// ---------- Davomat / Baholash ----------
export interface GridStudent {
  id: number;
  full_name: string;
  status: string;
}

export interface GridLesson {
  id: number;
  date: string; // YYYY-MM-DD
  /** 1 - dars o'tilgan (yoqlama qo'yilgan), 0 - jadval bo'yicha reja. */
  held: number;
}

/** marks kaliti "lessonId:studentId". Davomat uchun qiymat boolean,
 *  baholash uchun 1-5 son. */
export interface AttendanceGrid {
  students: GridStudent[];
  lessons: GridLesson[];
  marks: Record<string, boolean | number>;
}

// ---------- Imtihonlar ----------
export type ExamKind = "unit" | "mid" | "end" | "mock";

export interface Exam {
  id: number;
  group_id: number;
  kind: ExamKind;
  unit_no?: number | null;
  title?: string | null;
  date: string;
  max_score?: number | null;
  created_by?: string | null;
  created_at: string;
  result_count: number;
  avg_percent?: number | null;
}

export interface ExamResult {
  id: number;
  exam_id: number;
  student_id: number;
  score?: number | null;
  band?: number | null;
  percent?: number | null;
  coins: number;
  absent: boolean;
  note?: string | null;
}

export interface ExamDetail extends Exam {
  results: ExamResult[];
  students: GridStudent[];
}

// ---------- Coin / gamification ----------
export interface CoinBalance {
  student_id: number;
  full_name: string;
  group?: string | null;
  branch?: string | null;
  balance: number;
  earned: number;
  spent: number;
}

export interface CoinEntry {
  id: number;
  student_id: number;
  amount: number;
  source: string;
  ref_id?: number | null;
  note?: string | null;
  created_by?: string | null;
  created_at: string;
}

export interface ExamCoinRule {
  id?: number;
  min_percent: number;
  coins: number;
  kind?: string | null;
}

export interface Reward {
  id: number;
  name: string;
  cost: number;
  value_som?: number | null;
  stock?: number | null;
  active: boolean;
  branch_id?: number | null;
  branch?: Branch | null;
}

export interface Redemption {
  id: number;
  student_id: number;
  reward_id: number;
  coins: number;
  created_by?: string | null;
  created_at: string;
  student?: GridStudent | null;
  reward?: Reward | null;
}

// ---------- O'quvchi sahifasi ----------
export interface StudentExamRow {
  exam_id: number;
  kind: string;
  unit_no?: number | null;
  title?: string | null;
  date: string;
  max_score?: number | null;
  group?: string | null;
  score?: number | null;
  band?: number | null;
  percent?: number | null;
  coins: number;
  absent: boolean;
}

export interface StudentExams {
  results: StudentExamRow[];
  count: number;
  avg_percent: number | null;
  coins: number;
}

export interface StudentAttendanceRow {
  date: string;
  present: boolean;
  grade?: number | null;
}

export interface StudentAttendance {
  rows: StudentAttendanceRow[];
  marked: number;
  present: number;
  absent: number;
  percent: number;
  avg_grade: number | null;
}

// ---------- Ta'lim sifati ----------
export interface QualityGroup {
  group_id: number;
  group: string;
  subject?: string | null;
  level?: string | null;
  teacher_id?: number | null;
  teacher?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  exams: number;
  results: number;
  avg: number;
}

export interface QualityRollup {
  id: number;
  name: string;
  groups: number;
  exams: number;
  avg: number;
}

export interface QualityReport {
  period: string;
  centre: { avg: number | null; groups: number; exams: number; results: number };
  branches: QualityRollup[];
  teachers: QualityRollup[];
  groups: QualityGroup[];
}

// ---------- Sotuv menejerlari ----------
export type SalesWindow = "month" | "3m" | "6m" | "1y" | "all";

export interface SalesManagerRow {
  user_id: number;
  full_name: string;
  branch?: string | null;
  active: boolean;
  leads: number;
  converted: number;
  rejected: number;
  in_progress: number;
  conversion: number;
}

export interface SalesManagerReport {
  window: string;
  label: string;
  rows: SalesManagerRow[];
  unassigned: number;
  totals: { leads: number; converted: number; conversion: number };
}

// ---------- Ustozlar oyligi ----------
export interface PayrollGroupRow {
  group_id: number;
  group: string;
  students: number;
  held_lessons: number;
  taught_lessons: number;
  amount: number;
  paid: boolean;
  payout_id: number | null;
}

export interface TeacherPayrollRow {
  teacher_id: number;
  full_name: string;
  branch?: string | null;
  groups: PayrollGroupRow[];
  students: number;
  lessons: number;
  amount: number;
  paid_amount: number;
}

export interface TeacherPayrollReport {
  period: string;
  rows: TeacherPayrollRow[];
  total: number;
  paid: number;
  unpaid: number;
  teacher_count: number;
}

// ---------- Sotuv voronkasi ----------
export interface FunnelStage {
  stage: string;
  reached: number;
  here_now: number;
  percent: number;
  lost_here: number;
}

export interface FunnelMonth {
  month: number;
  eligible: number;
  survived: number;
  retention: number;
  lost: number;
}

export interface FunnelReport {
  leads: { total: number; stages: FunnelStage[]; rejected: number };
  students: {
    paying: number;
    churned: number;
    months: FunnelMonth[];
    worst_month: number | null;
    worst_month_lost: number;
  };
}

// ---------- Analitika ----------
export interface AnalyticsMonth {
  period: string;
  income: number;
  expenses: number;
  payroll: number;
  outflow: number;
  profit: number;
  teacher_share: number;
}

export interface AnalyticsBreakdown {
  key: string;
  label: string;
  group?: string;
  amount: number;
}

export interface AnalyticsSummary {
  months: AnalyticsMonth[];
  expense_groups: AnalyticsBreakdown[];
  expense_categories: AnalyticsBreakdown[];
  totals: {
    income: number;
    expenses: number;
    payroll: number;
    outflow: number;
    profit: number;
    margin: number;
    teacher_share: number;
  };
}

// ---------- Adminlar KPI ----------
export interface AdminKpi {
  user_id: number;
  full_name: string;
  branch_id?: number | null;
  branch?: string | null;
  fix_salary: number;
  active_students: number;
  expected: number;
  collected: number;
  collection_percent: number;
  collection_bonus: number;
  new_clients: number;
  new_client_revenue: number;
  new_client_bonus: number;
  total: number;
}

export interface AdminKpiResult {
  period: string;
  rows: AdminKpi[];
}

export interface KpiCollectionRule {
  id?: number;
  min_students: number;
  max_students?: number | null;
  min_percent: number;
  bonus: number;
}

export interface KpiNewClientRule {
  id?: number;
  min_clients: number;
  bonus: number;
}

export interface KpiRules {
  collection: KpiCollectionRule[];
  new_clients: KpiNewClientRule[];
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

// ---------------------------------------------------- Kassa daftari ----
export interface CashMethodBlock {
  cash: number;
  card: number;
  terminal: number;
  other: number;
  total: number;
}

export interface LedgerRow {
  id: string;
  date: string;
  amount: number;
  title: string;
  student_id: number | null;
  method: string;
  direction: "in" | "out";
  branch: string;
  category: string;
  note?: string | null;
}

export interface CashflowLedger {
  period: string;
  kirim: CashMethodBlock;
  chiqim: CashMethodBlock;
  kassa: CashMethodBlock;
  new_payments: { count: number; amount: number };
  old_payments: { count: number; amount: number };
  rows: LedgerRow[];
}

// ------------------------------------------------------------- HR ----
export interface Vacancy {
  id: number;
  title: string;
  role?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  headcount: number;
  status: string;
  salary_from?: number | null;
  salary_to?: number | null;
  description?: string | null;
  created_at?: string | null;
  candidate_count: number;
  hired_count: number;
}

export interface Candidate {
  id: number;
  full_name: string;
  phone?: string | null;
  vacancy_id?: number | null;
  vacancy?: string | null;
  stage: string;
  source: string;
  branch_id?: number | null;
  branch?: string | null;
  note?: string | null;
  reject_reason?: string | null;
  hired_date?: string | null;
  created_at?: string | null;
}

export interface FunnelStage {
  stage: string;
  label: string;
  reached: number;
  stuck_here: number;
  percent: number;
}

export interface HrFunnel {
  total: number;
  hired: number;
  rejected: number;
  hire_rate: number;
  avg_days_to_hire: number;
  open_vacancies: number;
  stages: FunnelStage[];
  sources: { key: string; label: string; total: number; hired: number; percent: number }[];
}

// ------------------------------------------------------ Marketing ----
export interface MarketingChannel {
  channel: string;
  label: string;
  spend: number;
  leads: number;
  trial: number;
  converted: number;
  rejected: number;
  revenue: number;
  conversion: number;
  cpl: number;
  cac: number;
  roi: number;
}

export interface MarketingFunnel {
  months: number;
  channels: MarketingChannel[];
  stages: FunnelStage[];
  totals: {
    spend: number;
    leads: number;
    converted: number;
    revenue: number;
    conversion: number;
    cpl: number;
    cac: number;
    roi: number;
  };
}

export interface CacRow {
  period: string;
  spend: number;
  new_clients: number;
  cac: number;
}

export interface CacReport {
  rows: CacRow[];
  totals: {
    spend: number;
    new_clients: number;
    cac: number;
    ltv: number;
    ratio: number;
  };
}

// ------------------------------------------- Ijtimoiy tarmoqlar ----
export interface SocialPlatform {
  platform: string;
  label: string;
  handle?: string | null;
  followers: number | null;
  source?: string | null;
  date?: string | null;
  growth: number | null;
  history: { date: string; followers: number }[];
}

export type SocialStats = Record<string, SocialPlatform>;

// ------------------------------------------------------ Ota-ona ----
export interface ParentStudent {
  id: number;
  public_id?: string | null;
  full_name: string;
  status: string;
}

export interface Parent {
  id: number;
  public_id?: string | null;
  full_name: string;
  phone?: string | null;
  phone2?: string | null;
  relation?: string | null;
  address?: string | null;
  workplace?: string | null;
  note?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  created_at?: string | null;
  students: ParentStudent[];
}

// --------------------------------------------------- Shartnoma ----
export interface Contract {
  id: number;
  public_id?: string | null;
  student_id: number;
  student?: string | null;
  student_public_id?: string | null;
  parent_id?: number | null;
  parent?: string | null;
  group_id?: number | null;
  group?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  monthly_fee: number;
  discount_percent: number;
  status: string;
  note?: string | null;
  created_by?: string | null;
  created_at?: string | null;
}

// --------------------------------------------------- Shikoyat ----
export interface Complaint {
  id: number;
  student_id?: number | null;
  student?: string | null;
  group_id?: number | null;
  group?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  source: string;
  severity: string;
  subject: string;
  body?: string | null;
  status: string;
  resolution?: string | null;
  assigned_user_id?: number | null;
  assigned_user?: string | null;
  closed_at?: string | null;
  created_at?: string | null;
  age_days: number;
}

// -------------------------------------------------- Audit log ----
export interface AuditRow {
  id: number;
  user_name?: string | null;
  user_role?: string | null;
  entity: string;
  entity_label_type: string;
  entity_id?: number | null;
  entity_label?: string | null;
  action: string;
  action_label: string;
  field?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  note?: string | null;
  created_at?: string | null;
}

export interface AuditResponse {
  total: number;
  rows: AuditRow[];
}

export interface AuditMeta {
  actions: { key: string; label: string }[];
  entities: { key: string; label: string }[];
}

// ------------------------------------------------ Asoschi paneli ----
export interface CeoAlert {
  level: "high" | "normal" | "low";
  title: string;
  detail: string;
  link?: string | null;
}

export interface CeoDebtor {
  id: number;
  public_id?: string | null;
  full_name: string;
  balance: number;
  group?: string | null;
}

export interface CeoProblemGroup {
  id: number;
  name: string;
  teacher?: string | null;
  students: number;
  attendance: number | null;
  reasons: string[];
}

export interface CeoToday {
  date: string;
  scope: string;
  money: {
    income: number;
    expense: number;
    net: number;
    payment_count: number;
  };
  sales: { new_leads: number; touched_leads: number; sales: number };
  students: {
    active: number;
    debtors: number;
    total_debt: number;
    left_today: number;
    left_list: { id: number; full_name: string; group?: string | null }[];
    top_debtors: CeoDebtor[];
  };
  attendance: {
    lessons_today: number;
    unmarked: number;
    present: number;
    marked: number;
    percent: number | null;
  };
  problem_groups: CeoProblemGroup[];
  complaints: { open: number; overdue: number; list: Complaint[] };
  alerts: CeoAlert[];
}
