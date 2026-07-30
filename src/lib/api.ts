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

/** Avtomatik tekshiruv topgan muammo. */
export interface CheckProblem {
  key: string;
  label: string;
  severity: "block" | "warn";
  message: string;
}

/** Tekshiruv muammolarini ham olib yuradigan xato. */
export class ApiError extends Error {
  problems: CheckProblem[] = [];
  canForce = false;
  status = 0;
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
    const d = body.detail;
    // Avtomatik tekshiruvlar xatoni obyekt sifatida qaytaradi:
    // {message, problems, can_force}. Oddiy xatolarda esa matn keladi.
    if (d && typeof d === "object" && !Array.isArray(d)) {
      const err = new ApiError(d.message || `Xatolik: ${res.status}`);
      err.problems = d.problems ?? [];
      err.canForce = Boolean(d.can_force);
      err.status = res.status;
      throw err;
    }
    const err = new ApiError(
      typeof d === "string" ? d : `Xatolik: ${res.status}`
    );
    err.status = res.status;
    throw err;
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
  room_id?: number | null;
  capacity?: number | null;
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

// ---------------------------------------------------- O'quv bo'limi ----
export interface Room {
  id: number;
  name: string;
  capacity: number;
  branch_id?: number | null;
  branch?: string | null;
  note?: string | null;
  active: boolean;
  groups: { id: number; name: string }[];
}

export interface GroupFillRow {
  id: number;
  name: string;
  teacher?: string | null;
  branch?: string | null;
  room?: string | null;
  students: number;
  capacity: number;
  percent: number;
  band: string;
  band_label: string;
  free_seats: number;
}

export interface GroupFillReport {
  rows: GroupFillRow[];
  no_capacity: { id: number; name: string }[];
  summary: {
    groups: number;
    students: number;
    capacity: number;
    percent: number;
    free_seats: number;
    by_band: { band: string; label: string; count: number }[];
  };
}

export interface RiskSignal {
  key: string;
  label: string;
  weight: number;
  detail?: string | null;
}

export interface RiskTaskBrief {
  id: number;
  title: string;
  assigned_user?: string | null;
  due_date?: string | null;
}

export interface RiskRow {
  student_id: number;
  public_id?: string | null;
  full_name: string;
  group_id?: number | null;
  group?: string | null;
  teacher?: string | null;
  branch?: string | null;
  phone?: string | null;
  score: number;
  level: string;
  level_label: string;
  signals: RiskSignal[];
  tasks: RiskTaskBrief[];
}

export interface RiskReport {
  total: number;
  at_risk: number;
  levels: { key: string; label: string; color: string; count: number }[];
  rows: RiskRow[];
  signals: { key: string; label: string; weight: number }[];
}

export interface RiskTask {
  id: number;
  student_id: number;
  student?: string | null;
  level?: string | null;
  level_label: string;
  title: string;
  assigned_user_id?: number | null;
  assigned_user?: string | null;
  due_date?: string | null;
  overdue: boolean;
  status: string;
  result?: string | null;
  created_at?: string | null;
}

// ------------------------------------------------- O'quvchi tarixi ----
export interface HistoryEvent {
  date?: string | null;
  kind: string;
  title: string;
  detail?: string | null;
  by?: string | null;
}

export interface StudentHistory {
  summary: {
    groups: string[];
    group_count: number;
    teachers: string[];
    group_changes: number;
    marked_lessons: number;
    absences: number;
    attendance_percent: number | null;
    complaints: number;
    talks: number;
    certificates: number;
    freezes: number;
    leaves: number;
    returns: number;
  };
  absent_dates: string[];
  timeline: HistoryEvent[];
}

export interface ParentTalk {
  id: number;
  date?: string | null;
  channel: string;
  topic: string;
  summary?: string | null;
  outcome?: string | null;
  created_by?: string | null;
}

export interface Certificate {
  id: number;
  kind: string;
  kind_label: string;
  level?: string | null;
  score?: number | null;
  date?: string | null;
  note?: string | null;
}

// ------------------------------------------------ Oilaviy chegirma ----
export interface StudentPricing {
  base_fee: number;
  family_discount: number;
  family_min_children: number;
  personal_discount: number;
  total_discount: number;
  final_fee: number;
  parent_id?: number | null;
  siblings: { id: number; full_name: string; status: string }[];
  active_siblings: number;
  explanation: string;
}

export interface FamilyDiscountReport {
  percent: number;
  min_children: number;
  families: number;
  monthly_total: number;
  rows: {
    parent_id: number;
    public_id?: string | null;
    parent: string;
    phone?: string | null;
    children: { id: number; full_name: string; status: string; group?: string | null }[];
    active_children: number;
    discount_percent: number;
    monthly_saved: number;
  }[];
}

// ------------------------------------------- Marketing to'liq yo'li ----
export interface JourneyStage {
  key: string;
  label: string;
  source: "ad" | "crm";
  count: number;
  step_percent: number | null;
  of_leads: number | null;
  lost: number;
}

export interface JourneyChannel {
  channel: string;
  label: string;
  impressions: number;
  clicks: number;
  leads: number;
  contacted: number;
  trial: number;
  sold: number;
  month1: number;
  month3: number;
  certificate: number;
  ctr: number | null;
  click_to_lead: number | null;
  lead_to_sale: number;
  retention_1m: number | null;
  retention_3m: number | null;
}

export interface MarketingJourney {
  months: number;
  stages: JourneyStage[];
  channels: JourneyChannel[];
  totals: Record<string, number>;
  worst_stage: JourneyStage | null;
  has_ad_data: boolean;
}

export interface AdStat {
  id: number;
  channel: string;
  label: string;
  period: string;
  impressions: number;
  clicks: number;
  ctr: number;
  branch_id?: number | null;
  note?: string | null;
}

// ------------------------------------------- Oylik hisob-kitob ----
export interface BillingRow {
  student_id: number;
  public_id?: string | null;
  full_name: string;
  group: string;
  lessons: number;
  discount: number;
  amount: number;
  already_charged: boolean;
}

export interface BillingMonth {
  period: string;
  committed: boolean;
  students: number;
  created: number;
  expected_total: number;
  rows: BillingRow[];
}

export interface CollectionReport {
  period: string;
  charged: number;
  /** Shu oyning hisobiga qo'shilgan pul (ortiqchasi kirmaydi). */
  collected: number;
  /** Kassaga haqiqatda tushgan pul - ortiqcha to'lov ham kiradi. */
  cash_in: number;
  percent: number;
  debt: number;
  carry_in: number;
  carry_out: number;
  students: number;
  paid_students: number;
  partial_students: number;
  unpaid_students: number;
  rows: CollectionRow[];
  by_admin: { name: string; collected: number }[];
}

export interface TrialStatus {
  status: string;
  attended: number;
  need: number;
  left: number;
  dates: string[];
  first_date: string | null;
}

// ------------------------------------------- Filiallar solishtiruvi ----
export interface BranchRow {
  branch_id: number;
  branch: string;
  active: number;
  trial: number;
  left: number;
  groups: number;
  income: number;
  expense: number;
  profit: number;
  margin: number;
  arpu: number;
  fill: number | null;
  leads: number;
  converted: number;
  conversion: number;
  new_clients: number;
  debt: number;
  churn: number;
}

export interface BranchCompare {
  months: number;
  period: string;
  rows: BranchRow[];
  totals: Record<string, number>;
  highlight: Record<string, { best: number | null; worst: number | null }>;
}

// -------------------------------------------------------- Examiner ----
export interface ExamRow {
  id: number;
  group_id: number;
  group?: string | null;
  teacher?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  kind: string;
  kind_label: string;
  unit_no?: number | null;
  title: string;
  date?: string | null;
  max_score?: number | null;
  status: string;
  status_label: string;
  approved_by?: string | null;
  approved_at?: string | null;
  retake_of_id?: number | null;
  note?: string | null;
  result_count: number;
  avg_percent: number | null;
  absent: number;
}

export interface AnalysisRow {
  key: number;
  label: string;
  avg: number;
  results: number;
  exams: number;
  students: number;
  band: string;
  band_label: string;
}

export interface ProgressRow {
  student_id: number;
  full_name: string;
  group?: string | null;
  first: number;
  last: number;
  change: number;
  exams: number;
  avg: number;
}

export interface ExaminerAnalysis {
  months: number;
  standard: number;
  total_results: number;
  avg: number | null;
  by_teacher: AnalysisRow[];
  by_group: AnalysisRow[];
  by_branch: AnalysisRow[];
  behind: AnalysisRow[];
  progress: ProgressRow[];
  recommend_certificate: ProgressRow[];
  recommend_retake: { student_id: number; full_name: string; group?: string | null; percent: number }[];
}

// ------------------------------------------------- Support teacher ----
export interface SupportStudent {
  student_id: number;
  public_id?: string | null;
  full_name: string;
  status: string;
  group_id?: number | null;
  group?: string | null;
  phone?: string | null;
  parent_phone?: string | null;
  attendance: {
    marked: number;
    present: number;
    absent: number;
    percent: number | null;
  };
  attendance_problem: boolean;
  homework_problem: boolean;
  homework_note?: string | null;
  open_plans: {
    id: number;
    issue: string;
    issue_label: string;
    plan: string;
    due_date?: string | null;
  }[];
}

export interface SupportPanel {
  user_id: number | null;
  groups: { id: number; name: string; teacher?: string | null; students: number }[];
  students: SupportStudent[];
  summary: {
    students: number;
    attendance_problem: number;
    homework_problem: number;
    threshold: number;
    open_plans: number;
    done_plans: number;
    plan_success: number | null;
    retention: number | null;
    stayed: number;
    left: number;
  };
}

export interface SupportPlanRow {
  id: number;
  student_id: number;
  student?: string | null;
  user?: string | null;
  issue: string;
  issue_label: string;
  plan: string;
  due_date?: string | null;
  overdue: boolean;
  status: string;
  result?: string | null;
  created_at?: string | null;
}

export interface SupportAssignment {
  id: number;
  user_id: number;
  user?: string | null;
  group_id?: number | null;
  group?: string | null;
  student_id?: number | null;
  student?: string | null;
  note?: string | null;
}

// ------------------------------------------------------- Fayllar ----
export interface AttachmentMeta {
  id: number;
  kind: string;
  kind_label: string;
  filename?: string | null;
  mime?: string | null;
  size: number;
  note?: string | null;
  created_by?: string | null;
  created_at?: string | null;
  is_image: boolean;
}

export interface AttachmentData {
  id: number;
  filename?: string | null;
  mime?: string | null;
  size: number;
  kind: string;
  data: string;
}

// ---------------------------------------------- Kollektsiya (yangi) ----
export interface CollectionRow {
  student_id: number;
  public_id?: string | null;
  full_name: string;
  group?: string | null;
  phone?: string | null;
  charged: number;
  paid: number;
  carry_in: number;
  covered: number;
  left: number;
  carry_out: number;
  old_debt: number;
  percent: number;
  state: "paid" | "partial" | "unpaid";
}

// -------------------------------------------------- Ma'lumotnomalar ----
export interface Reference {
  areas: string[];
  schools: string[];
  lesson_times: { start: string; end: string; label: string }[];
  lesson_minutes: number;
  exit_types: { key: string; label: string; hint: string }[];
  archive_groups: { key: string; label: string; hint: string }[];
}

// ------------------------------------------------------ Dars jadvali ----
export interface TimetableItem {
  group_id: number;
  group: string;
  public_id?: string | null;
  subject?: string | null;
  subject_label: string;
  level?: string | null;
  level_label: string;
  teacher?: string | null;
  branch?: string | null;
  room?: string | null;
  capacity: number | null;
  students: number;
  days: string[];
  start?: string | null;
  end: string;
  time_label: string;
  start_date?: string | null;
  end_date?: string | null;
}

export interface Timetable {
  days: { key: string; label: string; short: string }[];
  by_day: Record<string, TimetableItem[]>;
  items: TimetableItem[];
  no_schedule: { id: number; name: string }[];
  clashes: { day: string; room: string; time: string; groups: string[] }[];
}

// ------------------------------------------------------------ Arxiv ----
export interface ArchiveStudent {
  id: number;
  public_id?: string | null;
  full_name: string;
  phone?: string | null;
  parent_phone?: string | null;
  group?: string | null;
  branch?: string | null;
  enrolled_date?: string | null;
  left_date?: string | null;
  months: number | null;
  balance: number;
  amount: number;
  group_key: string;
}

export interface ArchiveStudents {
  groups: { key: string; label: string; hint: string; count: number; total: number }[];
  rows: ArchiveStudent[];
  total: number;
}

export interface ArchiveStaffRow {
  id: number;
  public_id?: string | null;
  full_name: string;
  username: string;
  role: string;
  role_label: string;
  branch?: string | null;
  exit_type: string;
  exit_label: string;
  exit_reason?: string | null;
  exit_date?: string | null;
}

export interface ArchiveStaff {
  groups: { key: string; label: string; hint: string; count: number }[];
  rows: ArchiveStaffRow[];
  total: number;
}

// ------------------------------------------- Manzil / maktab statistikasi
export interface GeoRow {
  name: string;
  leads: number;
  converted: number;
  conversion: number;
  known: boolean;
}

export interface GeographyReport {
  months: number;
  total_leads: number;
  areas: GeoRow[];
  schools: GeoRow[];
  top_area: GeoRow | null;
  top_school: GeoRow | null;
  free_text_areas: number;
  free_text_schools: number;
}

// ------------------------------------------------ Avtomatik tekshiruvlar
export interface CheckResult {
  problems: CheckProblem[];
  ok: boolean;
  blocking: boolean;
}

// ------------------------------------------------------------ Chegirmalar
export interface DiscountRow {
  id: number;
  student_id: number;
  student_name?: string;
  kind: string;
  kind_label: string;
  percent?: number | null;
  amount?: number | null;
  reason: string;
  start_date?: string | null;
  end_date?: string | null;
  status: string;
  status_label: string;
  alive: boolean;
  referrer_student_id?: number | null;
  referrer_name?: string | null;
  staff_user_id?: number | null;
  staff_name?: string | null;
  requested_by?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  cancelled_reason?: string | null;
  created_at?: string | null;
}

export interface DiscountType {
  key: string;
  label: string;
  hint: string;
}

export interface StudentDiscounts {
  rows: DiscountRow[];
  family_percent: number;
  total_percent: number;
  max_percent: number;
  can_approve: boolean;
  types: DiscountType[];
}

export interface DiscountList {
  rows: DiscountRow[];
  types: DiscountType[];
  statuses: { key: string; label: string }[];
  max_percent: number;
  can_approve: boolean;
  pending: number;
}

// -------------------------------------------------------- Nomzod kartasi
export interface CandidateCard {
  id: number;
  full_name: string;
  phone?: string | null;
  vacancy?: string | null;
  stage: string;
  stage_label: string;
  source: string;
  branch_id?: number | null;
  branch?: string | null;
  note?: string | null;
  reject_reason?: string | null;
  hired_date?: string | null;
  created_at?: string | null;
  cv?: string | null;
  experience_years?: number | null;
  workplaces?: string | null;
  certificates?: string | null;
  language_level?: string | null;
  language_level_label?: string | null;
  expected_salary?: number | null;
  trial_score?: number | null;
  interview_score?: number | null;
  overall_score?: number | null;
  strengths?: string | null;
  weaknesses?: string | null;
  reference_note?: string | null;
  decision: string;
  decision_label: string;
  files: { id: number; name?: string | null; kind: string; size: number;
           created_at?: string | null }[];
  language_levels: { key: string; label: string }[];
  decisions: { key: string; label: string }[];
}

// ----------------------------------------------------------- Onboarding
export interface OnboardingRow {
  step: string;
  label: string;
  done: boolean;
  done_at?: string | null;
  done_by?: string | null;
  note?: string | null;
}

export interface Onboarding {
  user_id: number;
  full_name: string;
  rows: OnboardingRow[];
  done: number;
  total: number;
  percent: number;
  complete: boolean;
}

// --------------------------------------------------------- Xodim kartasi
export interface StaffEventRow {
  id: number;
  kind: string;
  kind_label: string;
  tone: "good" | "bad" | "neutral";
  date?: string | null;
  end_date?: string | null;
  title?: string | null;
  note?: string | null;
  score?: number | null;
  amount?: number | null;
  minutes?: number | null;
  by?: string | null;
}

export interface StaffEvents {
  rows: StaffEventRow[];
  kinds: { key: string; label: string; tone: string }[];
}

export interface StaffCard {
  id: number;
  public_id?: string | null;
  full_name: string;
  username: string;
  phone?: string | null;
  birth_date?: string | null;
  photo?: string | null;
  role: string;
  role_label: string;
  position: string;
  branch_id?: number | null;
  branch?: string | null;
  manager_id?: number | null;
  manager?: string | null;
  hired_date?: string | null;
  is_active: boolean;
  exit_type?: string | null;
  exit_type_label?: string | null;
  exit_reason?: string | null;
  exit_date?: string | null;
  salary?: number | null;
  salary_hidden: boolean;
  bonus_total?: number | null;
  groups: { id: number; name: string; students: number }[];
  students: number;
  vacation_days: number;
  absences: number;
  late_count: number;
  late_minutes: number;
  trainings: number;
  reviews: number;
  avg_review?: number | null;
  disciplines: number;
  rewards: number;
  onboarding: OnboardingRow[];
  onboarding_done: number;
  onboarding_total: number;
  onboarding_percent: number;
}

// ------------------------------------------------------ Filial reytingi
export interface RatingRow {
  branch_id: number;
  branch: string;
  score: number;
  grade: string;
  grade_label: string;
  rank: number;
  scores: Record<string, number>;
  raw: {
    margin: number;
    churn: number;
    conversion: number;
    academic?: number | null;
    debt_per_student: number;
    complaints: number;
    issues: number;
    active: number;
    income: number;
    profit: number;
  };
}

export interface BranchRating {
  months: number;
  period: string;
  rows: RatingRow[];
  weights: Record<string, number>;
  dimensions: { key: string; label: string; weight: number }[];
  grades: { key: string; label: string; min: number }[];
}

// ------------------------------------------------------------- Vazifalar
export interface TaskRow {
  id: number;
  public_id?: string | null;
  title: string;
  description?: string | null;
  assignee_id?: number | null;
  assignee?: string | null;
  watcher_id?: number | null;
  watcher?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  deadline?: string | null;
  days_left?: number | null;
  overdue: boolean;
  priority: string;
  priority_label: string;
  priority_rank: number;
  status: string;
  status_label: string;
  status_tone: string;
  stored_status: string;
  source: string;
  source_label: string;
  meeting?: string | null;
  checklist: { text: string; done: boolean }[];
  checklist_done: number;
  checklist_total: number;
  result?: string | null;
  delay_reason?: string | null;
  done_at?: string | null;
  created_by?: string | null;
  created_at?: string | null;
}

export interface TaskList {
  rows: TaskRow[];
  counts: Record<string, number>;
  statuses: { key: string; label: string; tone: string; count: number }[];
  priorities: { key: string; label: string }[];
  sources: { key: string; label: string }[];
  can_manage: boolean;
  overdue: number;
  open: number;
}

// -------------------------------------------------------- Ombor/aktivlar
export interface AssetRepairRow {
  id: number;
  date?: string | null;
  cost?: number | null;
  vendor?: string | null;
  note?: string | null;
}

export interface AssetRow {
  id: number;
  inventory_no: string;
  name: string;
  kind: string;
  kind_label: string;
  branch_id?: number | null;
  branch?: string | null;
  room_id?: number | null;
  room?: string | null;
  responsible_id?: number | null;
  responsible?: string | null;
  purchased_on?: string | null;
  price?: number | null;
  condition: string;
  condition_label: string;
  condition_tone: string;
  warranty_until?: string | null;
  warranty_active: boolean;
  serial_no?: string | null;
  photo?: string | null;
  note?: string | null;
  written_off_on?: string | null;
  repairs: AssetRepairRow[];
  repair_count: number;
  repair_cost: number;
  replace_hint: boolean;
}

export interface AssetList {
  rows: AssetRow[];
  total_value: number;
  count: number;
  needs_attention: number;
  kinds: { key: string; label: string; count: number }[];
  conditions: { key: string; label: string; tone: string; count: number }[];
  can_edit: boolean;
}

export interface ConsumableRow {
  id: number;
  name: string;
  kind: string;
  kind_label: string;
  branch_id?: number | null;
  branch?: string | null;
  qty: number;
  min_qty: number;
  unit: string;
  unit_price?: number | null;
  value: number;
  low: boolean;
  note?: string | null;
  request_id?: number | null;
  request_qty?: number | null;
}

export interface ConsumableList {
  rows: ConsumableRow[];
  low_count: number;
  total_value: number;
  kinds: { key: string; label: string; unit: string }[];
  reasons: { key: string; label: string }[];
  requests: {
    id: number;
    consumable_id: number;
    name: string;
    qty: number;
    auto: boolean;
    note?: string | null;
    created_at?: string | null;
  }[];
  can_edit: boolean;
}

export interface StockMoveRow {
  id: number;
  delta: number;
  reason: string;
  reason_label: string;
  note?: string | null;
  by?: string | null;
  created_at?: string | null;
}
