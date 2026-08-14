import { pushToast } from "./toast";

const TOKEN_KEY = "jony_crm_token";

// ESLAB QOLISH (2026-08-10, Jahongir): belgi qo'yilsa token
// localStorage'da saqlanadi - ilova/brauzer yopilsa ham kirgan
// holda qoladi (ayniqsa o'quvchilar APK'ni har ochganda qayta
// login qilmasin). Belgisiz - avvalgidek sessionStorage (yopilsa
// chiqadi). O'qishda ikkalasi ham tekshiriladi.
export function getToken(): string | null {
  return (
    sessionStorage.getItem(TOKEN_KEY) ?? localStorage.getItem(TOKEN_KEY)
  );
}

export function setToken(token: string, remember = false) {
  if (remember) {
    localStorage.setItem(TOKEN_KEY, token);
    sessionStorage.removeItem(TOKEN_KEY);
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function clearToken() {
  invalidate(); // chiqishda boshqa xodimga eski ma'lumot ko'rinmasin
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
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

// GLOBAL FILIAL FILTRI. Rahbariyat tepadagi tanlagichdan filialni
// tanlasa, har bir GET so'rovga branch_id o'zi qo'shiladi — sahifalar
// alohida-alohida o'zgartirilmaydi. null = barcha filiallar.
let globalBranchId: string | null =
  typeof localStorage !== "undefined"
    ? localStorage.getItem("jonyos_branch")
    : null;

export function setGlobalBranch(id: string | null) {
  globalBranchId = id;
  invalidate(); // filial o'zgardi - eski javoblar yaroqsiz
  if (id) localStorage.setItem("jonyos_branch", id);
  else localStorage.removeItem("jonyos_branch");
}

export function getGlobalBranch(): string | null {
  return globalBranchId;
}

// KO'P LAVOZIMLI XODIM (2026-08-10). Xodimda bir nechta lavozim
// bo'lsa, tepadagi tanlagichdan qaysi lavozimda ishlayotgani
// tanlanadi va HAR BIR so'rovga X-Active-Role sarlavhasi qo'shiladi.
// Server sarlavhaga ko'r-ko'rona ishonmaydi — lavozim xodimning
// haqiqiy ro'yxatida bo'lsagina qabul qiladi (auth.py).
let activeRole: string | null =
  typeof localStorage !== "undefined"
    ? localStorage.getItem("jonyos_role")
    : null;

export function setActiveRole(role: string | null) {
  activeRole = role;
  invalidate(); // lavozim o'zgardi - ruxsatlar boshqa, kesh tozalanadi
  if (role) localStorage.setItem("jonyos_role", role);
  else localStorage.removeItem("jonyos_role");
}

export function getActiveRole(): string | null {
  return activeRole;
}


// ---------------------------------------------------------------
//  GET KESHI + SO'ROVLARNI BIRLASHTIRISH  (2026-08-14, Jahongir:
//  "Frontendda kesh yo'q ... togrla optimizatsiya qilib kuchaytir")
//
//  Ilgari har sahifaga o'tganda hamma narsa noldan yuklanardi va
//  bir sahifadagi 3-4 komponent BIR XIL manzilni bir vaqtda
//  so'rardi. Bu Neon (baza) trafigini bekorga yeb qo'yardi -
//  avgustda kvota shu sababdan tugagan edi.
//
//  Endi:
//   1) DEDUPE - ayni damda ketayotgan bir xil GET so'rov bitta
//      qilib yuboriladi, javob hammaga ulashiladi;
//   2) TTL KESH - yaqinda olingan javob qisqa muddat saqlanadi
//      (odatda 30 soniya; o'zgarmaydigan ro'yxatlar 5 daqiqa);
//   3) YOZUVDAN KEYIN TOZALASH - har qanday POST/PUT/DELETE'dan
//      keyin kesh butunlay tozalanadi, ya'ni to'lov kiritilgach
//      raqamlar HAR DOIM yangi ko'rinadi (eski son ko'rinib qolish
//      xavfi yo'q);
//   4) FILIAL YOKI LAVOZIM almashtirilsa ham kesh tozalanadi.
// ---------------------------------------------------------------

const CACHE_TTL_MS = 30_000;
const CACHE_TTL_LONG_MS = 5 * 60_000;

/** Deyarli o'zgarmaydigan ro'yxatlar - uzoqroq saqlanadi. */
const LONG_TTL = ["/reference", "/branches", "/roles", "/permissions"];

/** Hech qachon keshlanmaydi (jonli bo'lishi shart). */
const NO_CACHE = ["/auth", "/health", "/_bootstrap", "/cron"];

interface CacheRow {
  at: number;
  ttl: number;
  data: unknown;
}

const getCache = new Map<string, CacheRow>();
const inFlight = new Map<string, Promise<unknown>>();

function ttlFor(path: string): number {
  return LONG_TTL.some((p) => path.startsWith(p))
    ? CACHE_TTL_LONG_MS
    : CACHE_TTL_MS;
}

function cacheable(path: string): boolean {
  return !NO_CACHE.some((p) => path.startsWith(p));
}

/** Keshni tozalash. Bo'sh chaqirilsa - hammasini.
 *  Masalan: invalidate("/students") - faqat o'quvchilarga tegishlisini. */
export function invalidate(prefix?: string) {
  if (!prefix) {
    getCache.clear();
    return;
  }
  for (const k of [...getCache.keys()]) {
    if (k.startsWith(prefix)) getCache.delete(k);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  /** true - keshni chetlab o'tib, serverdan yangi javob oladi. */
  fresh = false
): Promise<T> {
  const isGet = !options.method || options.method === "GET";
  // Faqat o'qish so'rovlariga filial filtri qo'shiladi; sahifa o'zi
  // branch_id bergan bo'lsa yoki auth so'rovi bo'lsa — tegilmaydi.
  if (
    isGet &&
    globalBranchId &&
    !path.includes("branch_id=") &&
    !path.startsWith("/auth")
  ) {
    path += (path.includes("?") ? "&" : "?") + "branch_id=" + globalBranchId;
  }

  // ---- KESH (faqat GET) ----
  const useCache = isGet && !fresh && cacheable(path);
  if (useCache) {
    const hit = getCache.get(path);
    if (hit && Date.now() - hit.at < hit.ttl) return hit.data as T;
    const running = inFlight.get(path);
    if (running) return running as Promise<T>;
  }
  if (isGet && cacheable(path)) {
    const p = doRequest<T>(path, options)
      .then((data) => {
        getCache.set(path, { at: Date.now(), ttl: ttlFor(path), data });
        return data;
      })
      .finally(() => {
        inFlight.delete(path);
      });
    inFlight.set(path, p as Promise<unknown>);
    return p;
  }
  // ---- YOZUV so'rovi: bajarilgach kesh tozalanadi ----
  if (!isGet) {
    try {
      return await doRequest<T>(path, options);
    } finally {
      invalidate();
    }
  }
  return doRequest<T>(path, options);
}

async function doRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    // Qaysi lavozimda ishlayotgani (ko'p lavozimli xodim uchun)
    ...(activeRole ? { "X-Active-Role": activeRole } : {}),
  };

  let res: Response;
  try {
    res = await fetch(`/api${path}`, { ...options, headers });
  } catch {
    // Tarmoq darajasidagi xato (internet uzildi, server ishlamayapti
    // va h.k.) — bularda ham hech narsa ko'rsatilmasdan qolmasin.
    pushToast("Tarmoq bilan bog'lanib bo'lmadi. Internetni tekshiring.");
    throw new ApiError("Tarmoq bilan bog'lanib bo'lmadi");
  }

  // MUHIM (2026-08-10): /auth/ so'rovlari bu yerda USHLANMAYDI.
  // Aks holda noto'g'ri parol bilan kirishga uringan odam ham
  // "Sessiya tugadi" degan chalkash xabar olardi (Jahongir shuni
  // ko'rsatdi) - aslida esa "Login yoki parol noto'g'ri" bo'lishi
  // kerak. Auth xatolari pastdagi umumiy tarmoqqa tushadi va
  // serverdagi aniq matn bilan ko'rsatiladi.
  if (res.status === 401 && !path.startsWith("/auth/")) {
    clearToken();
    pushToast("Sessiya tugadi, qayta kiring", "info");
    window.location.href = "/login";
    throw new Error("Sessiya tugadi, qayta kiring");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const d = body.detail;
    // Avtomatik tekshiruvlar xatoni obyekt sifatida qaytaradi:
    // {message, problems, can_force}. Oddiy xatolarda esa matn keladi.
    //
    // MUHIM (2026-08-09): bu yerda pushToast(...) chaqirilishi —
    // ruxsat etilmagan yoki boshqa sabab bilan muvaffaqiyatsiz
    // tugagan HAR BIR so'rov ko'rinadigan xabar bilan chiqishini
    // kafolatlaydi, hatto chaqirgan sahifa o'zi xatoni ushlab
    // (catch) alohida ko'rsatmasa ham ("screen refreshed, hech
    // nima bo'lmagandek" muammosi — Jahongir HR menejer misolida
    // ko'rsatdi). Sahifaning o'z mahalliy xato matni (masalan forma
    // ichidagi qizil yozuv) bilan bir vaqtda, unga xalaqit bermay
    // ishlaydi.
    if (d && typeof d === "object" && !Array.isArray(d)) {
      const err = new ApiError(d.message || `Xatolik: ${res.status}`);
      err.problems = d.problems ?? [];
      err.canForce = Boolean(d.can_force);
      err.status = res.status;
      pushToast(err.message);
      throw err;
    }
    const err = new ApiError(
      typeof d === "string" ? d : `Xatolik: ${res.status}`
    );
    err.status = res.status;
    pushToast(err.message);
    throw err;
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/**
 * DUBL TO'LOVGA QARSHI KALIT (2026-08-14). Forma ochilganda bitta
 * tasodifiy kalit yaratiladi va to'lov shu kalit bilan yuboriladi.
 * Tugma ikki marta bosilsa yoki internet uzilib qayta yuborilsa —
 * server yangi yozuv OCHMAYDI, birinchisini qaytaradi. Kalit faqat
 * muvaffaqiyatli saqlangandan keyin yangilanadi.
 */
export function newClientKey(): string {
  try {
    if (typeof crypto !== "undefined" && crypto.randomUUID)
      return crypto.randomUUID();
  } catch {
    /* eski brauzer */
  }
  return `k${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

export const api = {
  /** Odatiy o'qish - 30 soniyalik kesh bilan. */
  get: <T,>(path: string, fresh = false) => request<T>(path, {}, fresh),
  /** Keshni chetlab o'tib, aniq yangi ma'lumot olish. */
  fresh: <T,>(path: string) => request<T>(path, {}, true),
  /** Keshni qo'lda tozalash (kerak bo'lganda). */
  invalidate,
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
  /** Fiks oylik. Faqat asoschi o'zgartiradi. */
  fix_salary?: number | null;
  phone?: string | null;
  /** Tug'ilgan kun eslatmasi shu sanaga tayanadi. */
  birth_date?: string | null;
  /** Ish yubileyi eslatmasi shu sanaga tayanadi. */
  hired_date?: string | null;
  public_id?: string | null;
  branch_ids?: number[];
  /** Qo'shimcha lavozimlar (ko'p lavozimli xodim). */
  extra_roles?: string[];
  branches_label?: string | null;
}

export interface Teacher {
  id: number;
  full_name: string;
  phone?: string;
  subject?: string;
  branch_id?: number;
  branch?: Branch;
  /** Ustoz ishlaydigan barcha filiallar (2-3 bo'lishi mumkin). */
  branch_ids?: number[];
  /** Qo'shimcha lavozimlar (ko'p lavozimli xodim). */
  extra_roles?: string[];
  branches_label?: string | null;
  /** "support" — yordamchi o'qituvchi, "teacher" — asosiy ustoz. */
  kind?: string | null;
  hired_date?: string | null;
  left_date?: string | null;
  /** 1 = hozir ishlayapti, 0 = ishdan ketgan. */
  is_active?: number;
  max_groups?: number | null;
  max_lessons_per_day?: number | null;
  /** junior / middle / senior / expert / head / metodist */
  grade?: string | null;
  grade_since?: string | null;
  cert?: string | null;
  cert_score?: number | null;
  /** CELTA / TESOL / DELTA */
  qualification?: string | null;
  birth_date?: string | null;
  skill_score?: number | null;
  support_months?: number | null;
  remediation_until?: string | null;
  remediation_reason?: string | null;
  /** Tizimga kirish hisobi. Bo'sh bo'lsa akkaunt ochilmagan. */
  user_id?: number | null;
  login?: string | null;  /** Support darajasi (volunteer/junior/middle/senior) — kind="support" da. */
  staff_grade?: string | null;
  staff_grade_label?: string | null;
}

export interface TeacherAccount {
  created: boolean;
  login: string;
  /** Faqat SHU javobda keladi — keyin bazadan o'qib bo'lmaydi. */
  password: string;
  full_name: string;
  url: string;
  warning: string;
  has_account: boolean;
  user_id: number | null;
}

export interface Group {
  /** 1 — stavka qo'lda kiritilgan (darajadan avtomat emas). */
  rate_manual?: number | null;
  support_label?: string | null;
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
  /** Haqiqiy kiritilish vaqti (eski sana bilan kiritilsa farq qiladi). */
  entered_at?: string | null;
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
  address?: string | null;
  school?: string | null;
  school_grade?: string | null;
  updated_at?: string | null;
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
  note?: string | null;
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
  /** Uy vazifasi: 1 bajardi, 2 qisman, 0 bajarmadi. */
  homework?: Record<string, number>;
  /** Sana menyusi uchun: kim ko'chira oladi va qancha imkon qolgan. */
  reschedule?: {
    can: boolean;
    manager: boolean;
    as_manager: boolean;
    moved: Record<
      string,
      { id: number; status: string; status_label: string; to_date: string }
    >;
    /** Teskarisi: shu (yangi) sanaga BOSHQA kundan ko'chirilgan dars
     *  bo'lsa shu yerda chiqadi — jadvalda "bu ko'chirilgan dars"
     *  belgisini ko'rsatish uchun. */
    moved_in?: Record<
      string,
      { id: number; status: string; status_label: string; from_date: string }
    >;
    reasons: { key: string; label: string }[];
    min_notice_days: number;
    max_shift_days: number;
    cannot_cancel: string;
    hint?: string;
    quota: {
      used_month: number;
      per_month: number;
      left: number | null;
      auto_ok: boolean;
    } | null;
  } | null;
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
  note?: string | null;  retake_score?: number | null;
  retake_band?: number | null;
  retake_percent?: number | null;
  retake_at?: string | null;
  counted?: number | null;
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
  /** Tasdiqlangan chegirmalar (referral, grant, individual...). */
  granted_discount?: number;
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
  /** Guruhida shu oyda dars kuni yo'q - pul hisoblanmaydigan o'quvchilar. */
  no_lesson?: number;
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
  // "user" — hisobli xodim, "teacher" — hisob ochilmagan ustoz kartasi
  kind?: string;
  teacher_id?: number;
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
  hidden?: boolean;
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
  /** Tasdiqlangan, lekin boshlanish sanasi hali kelmagan chegirmalar. */
  upcoming_percent?: number;
  upcoming_from?: string | null;
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

// ------------------------------------------------------- Ustoz ish haqi
export interface SalaryGroupRow {
  group_id: number;
  group: string;
  rate_per_student_month: number;
  standard_lessons: number;
  rate: number;
  lessons: number;
  attendances: number;
  amount: number;
}

export interface SalaryPaymentRow {
  id: number;
  amount: number;
  kind: string;
  kind_label: string;
  date?: string | null;
  period?: string | null;
  note?: string | null;
  by?: string | null;
}

export interface SalaryCard {
  teacher_id: number;
  full_name: string;
  branch?: string | null;
  month: string;
  earned_month: number;
  paid_month: number;
  lessons_month: number;
  attendances_month: number;
  earned_total: number;
  paid_total: number;
  balance: number;
  carry: number;
  carry_label: string;
  advance_available: number;
  by_group: SalaryGroupRow[];
  by_period: { period: string; lessons: number; attendances: number;
               amount: number }[];
  payments: SalaryPaymentRow[];
  can_pay: boolean;
}

export interface PayrollRow {
  teacher_id: number;
  full_name: string;
  branch?: string | null;
  lessons: number;
  attendances: number;
  earned: number;
  paid: number;
  left: number;
  balance: number;
  groups: SalaryGroupRow[];
}

export interface PayrollOverview {
  period: string;
  rows: PayrollRow[];
  teacher_count: number;
  earned: number;
  paid: number;
  left: number;
  kinds: { key: string; label: string; hint: string }[];
  can_pay: boolean;
}

// ---------------------------------------------------------- Qarzdorlar
export interface DebtorRow {
  student_id: number;
  public_id?: string | null;
  full_name: string;
  phone?: string | null;
  parent_phone?: string | null;
  group_id?: number | null;
  group?: string | null;
  branch?: string | null;
  status: string;
  debt: number;
  days: number;
  aging_days: number;
  bucket: string;
  urgency: string;
  urgency_label: string;
  urgency_tone: string;
  last_contact?: string | null;
  last_by?: string | null;
  last_result?: string | null;
  last_result_label?: string | null;
  last_note?: string | null;
  promised_date?: string | null;
  promised_amount?: number | null;
  promise_broken: boolean;
  days_since_contact?: number | null;
}

export interface DebtorList {
  rows: DebtorRow[];
  total_debt: number;
  count: number;
  broken_promises: number;
  due_today: number;
  never_contacted: number;
  results: { key: string; label: string; tone: string }[];
  aging: { key: string; label: string; count: number; sum: number }[];
}

export interface DebtContactRow {
  id: number;
  date?: string | null;
  result: string;
  result_label: string;
  tone: string;
  promised_date?: string | null;
  promised_amount?: number | null;
  note?: string | null;
  by?: string | null;
}

// ------------------------------------------------ Administrator paneli
export interface FillRow {
  group_id: number;
  group: string;
  teacher?: string | null;
  subject_label?: string | null;
  level_label?: string | null;
  days: string[];
  time?: string | null;
  students: number;
  capacity: number;
  free: number;
  fill: number;
  band: string;
  band_label: string;
}

export interface LeftRow {
  student_id: number;
  full_name: string;
  group?: string | null;
  teacher?: string | null;
  left_date: string;
  months?: number | null;
  balance: number;
}

export interface SalesPanel {
  month: string;
  fill: {
    rows: FillRow[];
    count: number;
    free_seats: number;
    lost_income: number;
  };
  left: { rows: LeftRow[]; count: number };
}

// ------------------------------------------------- Ustozlar reytingi
export interface TeacherScoreRow {
  teacher_id: number;
  full_name: string;
  branch?: string | null;
  branch_id?: number | null;
  is_active: boolean;
  groups: number;
  students: number;
  left: number;
  quality?: number | null;
  retention: number;
  ltv: number;
  avg_months: number;
  attendance?: number | null;
  parts: Record<string, number>;
  score: number;
  rank: number;
}

export interface TeacherScoreboard {
  months: number;
  rows: TeacherScoreRow[];
  me?: number | null;
  count: number;
  dimensions: { key: string; label: string; weight: number }[];
  averages: Record<string, number | null>;
}

// ---------------------------------------------------------- Ruxsatlar
export interface PermMatrix {
  roles: { key: string; label: string; locked: boolean; external: boolean }[];
  role_groups: { key: string; label: string; roles: string[] }[];
  resources: { key: string; label: string; group: string;
               secret_hint?: string | null }[];
  actions: { key: string; label: string }[];
  matrix: Record<string, Record<string, string[]>>;
  changed: Record<string, Record<string, string[]>>;
}

export interface MyPermissions {
  role: string;
  role_label: string;
  perms: Record<string, string[]>;
}

// ------------------------------------------------- Mening dashboardim
export interface MyCard {
  label: string;
  value: number | string;
  hint?: string | null;
  tone: string;
  link?: string | null;
}

export interface MyDashboard {
  role: string;
  role_label: string;
  full_name: string;
  branch?: string | null;
  cards: MyCard[];
  tasks: { open: number; overdue: number; rows: TaskRow[] };
  show_company: boolean;
  /** Butun markaz bo'yicha kartalar — Examiner, HR va SMM'da yo'q. */
  show_general: boolean;
  /** Faqat ustoz va yordamchi ustozda to'ladi. */
  teacher?: TeacherDashboard | null;
}

// --------------------------------------------------- Ustoz dashboardi
export interface TeacherAlert {
  kind: string;
  label: string;
  tone: string;
  advice: string;
  detail: string;
  student_id?: number;
  student?: string | null;
  group_id?: number;
  group?: string | null;
  lesson_id?: number;
  date?: string | null;
  since?: string | null;
}

export interface RiskStudent {
  student_id: number;
  student: string;
  group?: string | null;
  attendance_percent: number;
  missed: number;
  absent_streak: number;
}

export interface StudyRow {
  id: number;
  stage: number;
  kind: string;
  kind_label: string;
  title: string;
  done: boolean;
  done_at?: string | null;
}

export interface TeacherDashboard {
  teacher: { id: number; name: string };
  attendance: {
    percent: number | null;
    last_month: number | null;
    change: number | null;
    marks: number;
    present: number;
    homework_percent: number | null;
    homework_last_month: number | null;
    homework_checked: number;
    month: string;
  };
  groups: {
    id: number;
    name: string;
    percent: number | null;
    homework_percent: number | null;
    low: boolean;
  }[];
  risk_students: RiskStudent[];
  risk_count: number;
  alerts: TeacherAlert[];
  alert_count: number;
  alerts_by_kind: { key: string; label: string; tone: string; count: number }[];
  development: {
    study: StudyRow[];
    study_left: number;
    study_total: number;
    tasks: {
      id: number;
      public_id?: string | null;
      title: string;
      deadline?: string | null;
      overdue: boolean;
      priority?: string | null;
    }[];
    tasks_overdue: number;
    observations: unknown[];
  };
  thresholds: {
    absent_streak: number;
    group_attendance: number;
    student_attendance: number;
    homework_drop: number;
    no_growth_days: number;
  };
  hint: string;
}

// ---------------------------------------------------- Mening profilim
export interface PayPart {
  key: string;
  label: string;
  amount: number;
  hint?: string | null;
}

export interface MyProfile {
  id: number;
  public_id?: string | null;
  full_name: string;
  username: string;
  role: string;
  role_label: string;
  position: string;
  branch?: string | null;
  phone?: string | null;
  photo?: string | null;
  hired_date?: string | null;
  period: string;
  parts: PayPart[];
  total: number;
  fix_salary: number;
  teacher?: {
    teacher_id: number;
    earned_month: number;
    paid_month: number;
    balance: number;
    by_group: SalaryGroupRow[];
  } | null;
  kpi?: {
    active_students: number;
    expected: number;
    collected: number;
    collection_percent: number;
    collection_bonus: number;
    new_clients: number;
    new_client_bonus: number;
    total: number;
  } | null;
  late_count: number;
  late_minutes: number;
  onboarding_done: number;
  onboarding_total: number;
  onboarding: OnboardingRow[];
}

// ---------------------------------------------- Dars jadvali (to'r)
export interface GridItem {
  group_id: number;
  group: string;
  subject?: string | null;
  subject_label?: string | null;
  level?: string | null;
  level_label?: string | null;
  teacher_id?: number | null;
  teacher?: string | null;
  room_id?: number | null;
  room?: string | null;
  days: string[];
  start?: string | null;
  end?: string | null;
  time_label?: string | null;
  students: number;
  capacity?: number | null;
  fill?: number | null;
  lessons_held: number;
  avg_age?: number | null;
  hue: string;
  warn?: string | null;
  col: number;
  span: number;
}

export interface GridRoom {
  id: number;
  name: string;
  capacity?: number | null;
  branch?: string | null;
  items: GridItem[];
  busy_hours: number;
  usage: number;
}

export interface TimetableGrid {
  day: string;
  day_label: string;
  days: string[];
  presets: { key: string; label: string; days: string[] }[];
  weekdays: { key: string; label: string; short: string }[];
  slots: string[];
  start: string;
  step: number;
  rooms: GridRoom[];
  no_room: GridItem[];
  unplaced: GridItem[];
  clashes: { room: string; time?: string | null; groups: string[] }[];
  total_groups: number;
  total_students: number;
  can_edit: boolean;
  can_export: boolean;
}

// ---------------------------------------------------------------- LTV
export interface LtvFullRow {
  key: string;
  label: string;
  students: number;
  active: number;
  left: number;
  avg_months: number;
  finished_avg_months?: number | null;
  longest_months?: number | null;
  avg_revenue: number;
  avg_profit: number;
  total_revenue: number;
  total_profit: number;
  avg_payments: number;
  revenue_per_month: number;
  margin: number;
  churn: number;
}

export interface LtvFull {
  dimension: string;
  dimension_label: string;
  dimensions: { key: string; label: string }[];
  rows: LtvFullRow[];
  overall: {
    students: number;
    avg_months: number;
    avg_revenue: number;
    avg_profit: number;
    total_revenue: number;
    total_profit: number;
    margin: number;
    overhead_per_month: number;
  } | null;
  hint: string;
}

// -------------------------------------------------------------- Churn
export interface ChurnReason {
  key: string;
  label: string;
  group: string;
  controllable: boolean;
  count: number;
  students: string[];
}

export interface ChurnBucket {
  key: number | string | null;
  label: string;
  left: number;
  active: number;
  total: number;
  churn: number;
  top_reason?: string | null;
  top_reason_label?: string | null;
  reasons: { key: string; label: string; count: number }[];
}

export interface ChurnReport {
  months: number;
  period: string;
  left: number;
  active: number;
  churn: number;
  reasons: ChurnReason[];
  by_teacher: ChurnBucket[];
  by_group: ChurnBucket[];
  controllable: number;
  controllable_percent: number;
  unknown: number;
  reason_options: { key: string; label: string }[];
  hint: string;
}

// -------------------------------------------------- Xodimlar davomati
export interface AttendanceDay {
  id: number;
  user_id: number;
  full_name?: string | null;
  date?: string | null;
  check_in?: string | null;
  check_out?: string | null;
  late_minutes: number;
  early_minutes: number;
  worked_minutes: number;
  worked_hours: number;
  note?: string | null;
}

export interface StaffAttendanceReport {
  period: string;
  work_start: string;
  work_end: string;
  tolerance: number;
  rows: {
    user_id: number;
    full_name: string;
    role_label: string;
    branch?: string | null;
    days: number;
    late_days: number;
    late_minutes: number;
    early_minutes: number;
    worked_hours: number;
    rows: AttendanceDay[];
  }[];
  total_late_minutes: number;
  staff_with_late: number;
}

// ---------------------------------------------------------------- NPS
export interface NpsRow {
  teacher_id: number;
  full_name: string;
  branch?: string | null;
  answers: number;
  avg: number;
  nps: number;
  promoters: number;
  passives: number;
  detractors: number;
  by_student: number;
  by_parent: number;
  comments: { score: number; band: string; source: string;
              comment?: string | null; date?: string | null }[];
}

export interface NpsReport {
  months: number;
  rows: NpsRow[];
  overall_nps: number;
  answers: number;
  avg: number;
  sources: { key: string; label: string }[];
  bands: { key: string; label: string; tone: string; min: number }[];
  hint: string;
}

// ------------------------------------------- Xodimlarning sanalari
export interface StaffDateRow {
  user_id: number;
  full_name: string;
  role_label: string;
  branch?: string | null;
  phone?: string | null;
  kind: string;
  kind_label: string;
  tone: string;
  date: string;
  date_label: string;
  days_left: number;
  today: boolean;
  soon: boolean;
  years: number;
  age?: number | null;
  tenure: string;
  source_date: string;
}

export interface StaffDates {
  rows: StaffDateRow[];
  soon: StaffDateRow[];
  lead_days: number;
  days: number;
  birthdays: number;
  anniversaries: number;
  missing_birth_date: string[];
  missing_hired_date: string[];
  kinds: { key: string; label: string; tone: string }[];
  hint: string;
}

// --------------------------------------------------------------- ROMI
export interface RomiRow {
  key: string;
  label: string;
  leads: number;
  converted: number;
  spend: number;
  cac?: number | null;
  cpl?: number | null;
  conversion: number;
  revenue: number;
  profit: number;
  romi?: number | null;
  band: string;
  band_label: string;
  tone: string;
}

export interface RomiReport {
  months: number;
  period: string;
  rows: RomiRow[];
  total_spend: number;
  total_revenue: number;
  total_profit: number;
  romi?: number | null;
  no_spend: string[];
  hint: string;
}

// --------------------------------------------------- Xonalar bandligi
export interface CapacityReport {
  rooms: {
    room_id: number;
    name: string;
    branch?: string | null;
    capacity?: number | null;
    groups: number;
    students: number;
    seat_usage: number;
    hours_week: number;
    time_usage: number;
    free_seats: number;
  }[];
  room_count: number;
  total_capacity: number;
  active_students: number;
  seat_usage: number;
  time_usage: number;
  open_hours_week: number;
  free_seats: number;
  lost_income: number;
  worst?: string | null;
  hint: string;
}

// ---------------------------------------------------------------- RFM
export interface RfmRow {
  student_id: number;
  full_name: string;
  phone?: string | null;
  group?: string | null;
  status: string;
  r: number;
  f: number;
  m: number;
  days_since_payment: number;
  payments: number;
  total_paid: number;
  balance: number;
  segment: string;
  segment_label: string;
  tone: string;
  action: string;
}

export interface RfmReport {
  rows: RfmRow[];
  segments: { key: string; label: string; hint: string; tone: string;
              action: string; count: number; revenue: number;
              percent: number }[];
  total: number;
  hint: string;
}

// -------------------------------------------------------- Xabarnomalar
export interface NotifyTemplateRow {
  id: number;
  kind: string;
  kind_label: string;
  title?: string | null;
  body: string;
  channel: string;
  active: boolean;
  days_before: number;
}

export interface NotifyTemplates {
  rows: NotifyTemplateRow[];
  channels: { key: string; label: string }[];
  placeholders: string[];
  telegram_ready: boolean;
}

export interface NotifyRow {
  id: number;
  kind: string;
  kind_label: string;
  channel: string;
  channel_label: string;
  student_id?: number | null;
  student?: string | null;
  phone?: string | null;
  title?: string | null;
  body: string;
  status: string;
  status_label: string;
  tone: string;
  scheduled_for?: string | null;
  sent_at?: string | null;
  error?: string | null;
}

export interface NotifyList {
  rows: NotifyRow[];
  counts: Record<string, number>;
  statuses: { key: string; label: string; tone: string; count: number }[];
  kinds: { key: string; label: string }[];
  telegram_ready: boolean;
}

// ------------------------------------------------------------ Referral
export interface ReferralRow {
  student_id: number;
  full_name: string;
  invited: number;
  active: number;
  friends: { id: number; name: string; status: string; paid: number }[];
  revenue_brought: number;
  discount_given: number;
  net: number;
}

export interface ReferralReport {
  months: number;
  rows: ReferralRow[];
  inviters: number;
  invited: number;
  active: number;
  pending: number;
  revenue: number;
  discount: number;
  net: number;
  percent: number;
  months_valid: number;
  hint: string;
}

// ---------------------------------------------------------- Coin do'koni
export interface RewardItem {
  id: number;
  name: string;
  cost: number;
  category: string;
  category_label: string;
  tone: string;
  stock?: number | null;
  in_stock: boolean;
  active: boolean;
  affordable: boolean;
  need_more?: number | null;
}

export interface CoinHistoryRow {
  id: number;
  amount: number;
  source: string;
  source_label: string;
  note?: string | null;
  date?: string | null;
}

export interface MyOrder {
  id: number;
  reward: string;
  coins: number;
  status: string;
  status_label: string;
  tone: string;
  date?: string | null;
  given_at?: string | null;
  note?: string | null;
}

export interface MyCoins {
  student_id: number;
  full_name: string;
  group?: string | null;
  balance: number;
  earned: number;
  spent: number;
  held: number;
  available: number;
  next_goal?: RewardItem | null;
  history: CoinHistoryRow[];
  categories: { key: string; label: string; tone: string }[];
  rewards: RewardItem[];
  orders: MyOrder[];
}

export interface RewardRequestRow {
  id: number;
  student_id: number;
  student: string;
  group?: string | null;
  reward: string;
  coins: number;
  status: string;
  status_label: string;
  tone: string;
  by_student: boolean;
  date?: string | null;
  given_by?: string | null;
}

export interface RewardRequests {
  rows: RewardRequestRow[];
  count: number;
  statuses: { key: string; label: string; tone: string }[];
}

// ---------------------------------------------- Ustoz darajalari
export interface GradeRow {
  key: string;
  label: string;
  order_no: number;
  rate_per_student: number;
  min_months: number;
  min_groups?: number | null;
  max_groups?: number | null;
  cert_label?: string | null;
  cert_min?: number | null;
  promote_pass_rate?: number | null;
  demote_below?: number | null;
  demote_to?: string | null;
  needs_qualification: boolean;
  min_results?: number | null;
  result_band?: number | null;
  min_age?: number | null;
  min_skill?: number | null;
  level_pass_percent?: number | null;
  tone: string;
  teachers: number;
}

export interface GradeMissing {
  key: string;
  text: string;
}

export interface GradeState {
  teacher_id: number;
  full_name: string;
  branch?: string | null;
  grade: string;
  grade_label: string;
  tone: string;
  grade_since?: string | null;
  rate_per_student: number;
  next_grade?: string | null;
  next_label?: string | null;
  next_rate?: number | null;
  months: number;
  /** Tajriba yilda: 3.5. Ustozga oyda emas yilda ko'rsatiladi. */
  years?: number;
  tenure_text?: string;
  age?: number | null;
  cert?: string | null;
  cert_score?: number | null;
  qualification?: string | null;
  skill_score?: number | null;
  groups: number;
  min_groups?: number | null;
  max_groups?: number | null;
  pass_rate?: number | null;
  pass_results: number;
  pass_needed?: number | null;
  pass_mark?: number | null;
  test_avg?: number | null;
  test_results: number;
  demote_below?: number | null;
  enough_data: boolean;
  ready: boolean;
  missing: GradeMissing[];
  should_demote: boolean;
  need_remediation: boolean;
  in_remediation: boolean;
  remediation_until?: string | null;
  remediation_reason?: string | null;
  /** Oy o'rtasida ko'tarilgan bo'lsa - keyingi oydan kuchga kiradi. */
  pending_grade?: string | null;
  pending_label?: string | null;
  pending_from?: string | null;
  pending_rate?: number | null;
}

export interface CareerMap {
  rows: GradeState[];
  grades: GradeRow[];
  ready: GradeState[];
  at_risk: GradeState[];
  remediation: GradeState[];
  applied: Record<string, number>;
  pass_window_months: number;
  test_window_days: number;
  min_results: number;
  remediation_below: number;
  can_edit: boolean;
  hint: string;
}

export interface GradeEvent {
  id: number;
  kind: string;
  kind_label: string;
  tone: string;
  from_grade?: string | null;
  from_label?: string | null;
  to_grade?: string | null;
  to_label?: string | null;
  date?: string | null;
  reason?: string | null;
  pass_rate?: number | null;
  test_avg?: number | null;
  rate_before?: number | null;
  rate_after?: number | null;
  decided_by?: string | null;
}

export interface StudyItem {
  id: number;
  kind: string;
  title: string;
  done: boolean;
  done_at?: string | null;
  note?: string | null;
}

export interface StudyStage {
  key: string;
  label: string;
  done: number;
  total: number;
  items: StudyItem[];
}

export interface TeacherCareer {
  state: GradeState;
  grades: GradeRow[];
  history: GradeEvent[];
  study: StudyStage[];
  entry: { key: string; text: string }[];
  observations?: ObservationRow[];
  can_edit: boolean;
  is_me: boolean;
}

// ------------------------------------------------- Gamification: XP
export interface XpLeagueRow {
  id: number;
  key: string;
  name: string;
  rank: number;
  minimum_xp: number;
  maximum_xp?: number | null;
  color?: string | null;
  icon?: string | null;
  description?: string | null;
  reward_coin: number;
  is_active: boolean;
  students: number;
}

export interface XpRuleRow {
  id: number;
  event_code: string;
  name: string;
  description?: string | null;
  category: string;
  category_label: string;
  tone: string;
  default_xp: number;
  default_coin: number;
  maximum_per_lesson?: number | null;
  maximum_per_day?: number | null;
  maximum_per_week?: number | null;
  maximum_per_month?: number | null;
  mode: string;
  requires_approval: boolean;
  allowed_roles?: string | null;
  is_active: boolean;
}

export interface XpRuleList {
  rows: XpRuleRow[];
  categories: { key: string; label: string; tone: string }[];
  quick: string[];
  teacher_week_limit: number;
  teacher_lesson_limit: number;
  approval_above: number;
  can_edit: boolean;
}

export interface XpHistoryRow {
  id: number;
  date?: string | null;
  amount: number;
  event_code?: string | null;
  label?: string | null;
  category?: string | null;
  category_label: string;
  tone: string;
  source_type?: string | null;
  source_label: string;
  by: string;
  reason?: string | null;
  is_reversal: boolean;
  lesson_id?: number | null;
  exam_id?: number | null;
}

export interface StudentGamification {
  student_id: number;
  full_name: string;
  group?: string | null;
  branch?: string | null;
  lifetime_xp: number;
  season_xp: number;
  season?: string | null;
  level: number;
  level_percent: number;
  level_to_next: number;
  league?: XpLeagueRow | null;
  next_league?: XpLeagueRow | null;
  league_percent: number;
  league_to_next: number;
  max_league: boolean;
  by_category: { key: string; label: string; tone: string; xp: number }[];
  coins: number;
  last_xp_at?: string | null;
  ranks: {
    group_rank?: number | null;
    group_total?: number;
    branch_rank?: number | null;
    branch_total?: number;
    season_rank?: number | null;
    season_total?: number;
  };
  streaks: {
    kind: string; label: string; tone: string;
    current: number; longest: number;
  }[];
  xp_week: number;
  xp_month: number;
  history: XpHistoryRow[];
  league_history: {
    id: number; from?: string | null; to?: string | null;
    icon?: string | null; xp: number; reward_coin: number;
    date?: string | null;
  }[];
  achievements: {
    id: number; key: string; name: string;
    description?: string | null; icon?: string | null;
    tone: string; date?: string | null;
  }[];
  empty_hint: string;
}

export interface LeaderboardRow {
  student_id: number;
  full_name: string;
  group?: string | null;
  branch?: string | null;
  league?: string | null;
  league_icon?: string | null;
  league_color?: string | null;
  level: number;
  xp: number;
  lifetime_xp: number;
  academic_xp: number;
  rank: number;
  change?: number | null;
  is_new: boolean;
}

export interface Leaderboard {
  rows: LeaderboardRow[];
  scope: string;
  scopes: { key: string; label: string }[];
  leagues: { key: string; name: string; icon?: string | null }[];
  masked: boolean;
}

export interface XpOverview {
  today: number;
  week: number;
  total: number;
  active_students: number;
  avg_per_student: number;
  top_event?: string | null;
  manual_percent: number;
  auto_percent: number;
  season?: string | null;
  season_participants: number;
  league_distribution: { league: string; students: number }[];
  weekly_active_percent: number;
  silent_14d: number;
  silent_names: string[];
  open_alerts: number;
}

export interface XpTransactionRow {
  id: number;
  student_id: number;
  student?: string | null;
  amount: number;
  event_code?: string | null;
  label?: string | null;
  category?: string | null;
  category_label: string;
  source_type?: string | null;
  source_label: string;
  by: string;
  reason?: string | null;
  is_reversal: boolean;
  reversed_id?: number | null;
  date?: string | null;
}

export interface XpSeasonRow {
  id: number;
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  is_active: boolean;
  current: boolean;
  note?: string | null;
}

export interface FraudRow {
  id: number;
  alert_type: string;
  label: string;
  severity: string;
  tone: string;
  student?: string | null;
  user?: string | null;
  description?: string | null;
  status: string;
  transaction_id?: number | null;
  date?: string | null;
}

export interface XpAnalytics {
  by_branch: { key: number; label: string; students: number;
    total_xp: number; avg_xp: number }[];
  by_group: { key: number; label: string; students: number;
    total_xp: number; avg_xp: number }[];
  weakest_groups: { key: number; label: string; students: number;
    total_xp: number; avg_xp: number }[];
  by_teacher: { key: number; label: string; students: number;
    total_xp: number; avg_xp: number }[];
  attendance_correlation?: number | null;
  correlation_hint: string;
  manual_by_user: { user: string; xp: number }[];
}

// ------------------------------------------------ Dars baholash
export interface RubricCriterion {
  id: number;
  no: number;
  text: string;
  points: number;
}

export interface RubricRow {
  key: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  max_total: number;
  criteria: RubricCriterion[];
}

export interface RubricList {
  rows: RubricRow[];
  targets: { key: string; label: string }[];
  pass_score: number;
  head_score: number;
  can_edit: boolean;
  hint: string;
}

export interface ObservationRow {
  id: number;
  rubric_key: string;
  rubric: string;
  target_type: string;
  teacher_id?: number | null;
  candidate_id?: number | null;
  teacher?: string | null;
  date?: string | null;
  total: number;
  max_total: number;
  percent: number;
  band?: string | null;
  band_label: string;
  tone: string;
  observer?: string | null;
  strengths?: string | null;
  weaknesses?: string | null;
  note?: string | null;
  scores?: {
    criterion_id: number; no: number; text: string;
    points: number; fact: number; note?: string | null;
  }[];
}

// ------------------------------------- O'quv markaz to'lganligi
export interface FillRoom {
  room_id: number;
  name: string;
  branch?: string | null;
  branch_id?: number | null;
  seats: number;
  capacity: number;
  groups: number;
  group_slots: number;
  odd_groups: number;
  even_groups: number;
  students: number;
  free: number;
  percent: number;
  label: string;
  tone: string;
}

export interface FillBranch {
  branch_id?: number | null;
  name: string;
  rooms: number;
  capacity: number;
  students: number;
  groups: number;
  group_slots: number;
  free: number;
  percent: number;
  label: string;
  tone: string;
}

export interface FillTeacher {
  teacher_id: number;
  name: string;
  branch?: string | null;
  grade?: string | null;
  grade_label: string;
  groups: number;
  max_groups: number;
  seats: number;
  capacity: number;
  students: number;
  free: number;
  percent: number;
  label: string;
  tone: string;
}

export interface FillReport {
  level: string;
  level_label: string;
  groups_per_room: number;
  rooms: number;
  capacity: number;
  students: number;
  students_without_room: number;
  percent: number;
  label: string;
  tone: string;
  free: number;
  group_slots: number;
  groups_now: number;
  levels: {
    key: string; label: string; groups_per_room: number;
    description: string; capacity: number; percent: number;
    free: number; current: boolean;
  }[];
  by_room: FillRoom[];
  by_branch: FillBranch[];
  by_teacher: FillTeacher[];
  hint: string;
}

// ------------------------------------------------- SMM: kontent
export interface ContentWarning {
  key: string;
  severity: string;
  text: string;
}

export interface ContentRow {
  id: number;
  code: string;
  title: string;
  platform?: string | null;
  platform_label: string;
  platform_tone: string;
  format?: string | null;
  format_label: string;
  pillar?: string | null;
  pillar_label: string;
  pillar_tone: string;
  goal?: string | null;
  goal_label: string;
  goal_metric: string;
  funnel?: string | null;
  funnel_label: string;
  branch?: string | null;
  branch_id?: number | null;
  course?: string | null;
  campaign_id?: number | null;
  status: string;
  status_label: string;
  tone: string;
  planned_date?: string | null;
  planned_time?: string | null;
  published_at?: string | null;
  owner?: string | null;
  owner_id?: number | null;
  approver?: string | null;
  approver_role?: string | null;
  approver_role_label: string;
  priority?: string | null;
  deadline?: string | null;
  needs_consent: boolean;
  consent_ok: boolean;
  post_url?: string | null;
  warnings: ContentWarning[];
  blocked: boolean;
}

export interface ContentFull extends ContentRow {
  audience?: string | null;
  problem?: string | null;
  message?: string | null;
  hook?: string | null;
  location?: string | null;
  participants?: string | null;
  props?: string | null;
  duration?: string | null;
  music?: string | null;
  design_format?: string | null;
  cta?: string | null;
  references?: string | null;
  script?: string | null;
  caption?: string | null;
  caption_ru?: string | null;
  caption_en?: string | null;
  hashtags?: string | null;
  story_text?: string | null;
  on_video_text?: string | null;
  utm?: string | null;
  short_link?: string | null;
  promo_code?: string | null;
  post_external_id?: string | null;
  note?: string | null;
  team: {
    copywriter?: string | null; designer?: string | null;
    videographer?: string | null; editor?: string | null;
  };
  shots: { id: number; no: number; text: string; state: string;
    note?: string | null }[];
  approvals: {
    id: number; role?: string | null; role_label: string;
    decision?: string | null; decision_label: string; tone: string;
    comment?: string | null; quote?: string | null;
    by?: string | null; date?: string | null;
  }[];
  versions: {
    id: number; field: string; old?: string | null;
    new?: string | null; by?: string | null; date?: string | null;
  }[];
}

export interface ContentMeta {
  statuses: { key: string; label: string; tone: string }[];
  flow: string[];
  platforms: { key: string; label: string; tone: string }[];
  formats: { key: string; label: string }[];
  goals: { key: string; label: string; metric: string }[];
  pillars: { key: string; label: string; tone: string; hint: string }[];
  funnels: { key: string; label: string }[];
  consent: { key: string; label: string; tone: string }[];
  idea_statuses: { key: string; label: string; tone: string }[];
  request_statuses: { key: string; label: string; tone: string }[];
  decisions: { key: string; label: string; tone: string }[];
  plan_target: number;
  can_edit: boolean;
}

export interface ContentList {
  rows: ContentRow[];
  total: number;
  plan_percent: number;
  plan_ok: boolean;
  by_status: { key: string; label: string; tone: string; count: number }[];
  blocked: ContentRow[];
}

export interface SmmDashboard {
  cards: { key: string; label: string; value: number | string;
    tone: string; hint?: string }[];
  today: ContentRow[];
  late: ContentRow[];
  waiting: ContentRow[];
  alerts: {
    content_id?: number | null; title: string; key: string;
    severity: string; text: string; planned_date?: string | null;
  }[];
  plan_percent: number;
  month_planned: number;
  month_done: number;
  hint: string;
}

export interface IdeaRow {
  id: number;
  title: string;
  description?: string | null;
  pillar?: string | null;
  pillar_label: string;
  platform?: string | null;
  platform_label: string;
  course?: string | null;
  audience?: string | null;
  reference?: string | null;
  priority?: string | null;
  status: string;
  status_label: string;
  tone: string;
  author?: string | null;
  content_id?: number | null;
  date?: string | null;
}

export interface RequestRow {
  id: number;
  requester?: string | null;
  department?: string | null;
  branch?: string | null;
  course?: string | null;
  goal?: string | null;
  goal_label: string;
  offer?: string | null;
  group_time?: string | null;
  teacher?: string | null;
  students_needed?: number | null;
  start_date?: string | null;
  deadline?: string | null;
  platforms?: string | null;
  approved_price?: number | null;
  cta?: string | null;
  status: string;
  status_label: string;
  tone: string;
  smm_note?: string | null;
  campaign_id?: number | null;
  date?: string | null;
}

// ------------------------------------------- SMM: inbox va atributsiya
export interface InboxRow {
  id: number;
  channel: string;
  channel_label: string;
  channel_tone: string;
  kind: string;
  kind_label: string;
  author: string;
  username?: string | null;
  phone?: string | null;
  text?: string | null;
  content_id?: number | null;
  content?: string | null;
  content_code?: string | null;
  course?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  assigned?: string | null;
  lead_id?: number | null;
  received_at?: string | null;
  first_reply_at?: string | null;
  reply_minutes?: number | null;
  waiting_minutes?: number | null;
  off_hours: boolean;
  sla: string;
  sla_label: string;
  sla_tone: string;
  overdue: boolean;
  reply_text?: string | null;
  replied_by?: string | null;
}

export interface InboxList {
  rows: InboxRow[];
  counts: Record<string, number>;
  open: number;
  overdue: number;
  sla_percent: number;
  avg_minutes: number;
  answered: number;
  off_hours: number;
  statuses: { key: string; label: string; tone: string; count: number }[];
  channels: { key: string; label: string; tone: string }[];
  sla_alert: number;
  work_hours: string;
  templates: { id: number; key: string; label: string; text: string }[];
  hint: string;
}

export interface FunnelStep {
  key: string;
  label: string;
  value: number;
  from_prev?: number | null;
}

export interface Attribution {
  content: ContentRow;
  metrics: Record<string, number>;
  reach: number;
  views: number;
  engagement: number;
  profile_visits: number;
  link_clicks: number;
  messages: number;
  leads: number;
  qualified: number;
  trials: number;
  sales: number;
  revenue: number;
  first_revenue: number;
  retained_30: number;
  retained_90: number;
  funnel: FunnelStep[];
  lead_rate: number;
  qualified_rate: number;
  sale_rate: number;
  story: string;
  goal_label: string;
  goal_metric: string;
  hint: string;
}

export interface AttributionRow {
  id: number;
  code?: string | null;
  title: string;
  platform_label: string;
  pillar?: string | null;
  pillar_label: string;
  pillar_tone: string;
  goal_label: string;
  date?: string | null;
  reach: number;
  engagement: number;
  messages: number;
  leads: number;
  qualified: number;
  sales: number;
  revenue: number;
  retained_30: number;
}

export interface AttributionReport {
  rows: AttributionRow[];
  total: Attribution;
  by_pillar: {
    pillar?: string | null; label: string; tone: string;
    count: number; reach: number; leads: number; sales: number;
    revenue: number;
  }[];
  best: AttributionRow[];
  weak: AttributionRow[];
  months: number;
  hint: string;
}

export interface CampaignRow {
  id: number;
  name: string;
  goal?: string | null;
  goal_label: string;
  course?: string | null;
  branch?: string | null;
  offer?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  contents: number;
  target_leads?: number | null;
  target_sales?: number | null;
  leads: number;
  qualified: number;
  sales: number;
  revenue: number;
  reach: number;
  funnel: FunnelStep[];
  lead_plan_percent?: number | null;
  is_active: boolean;
  conclusion?: string | null;
}

// ------------------------------------------- SMM: brend, media, KB, hisobot
export interface BrandRow {
  id: number;
  section: string;
  key?: string | null;
  title: string;
  value?: string | null;
  note?: string | null;
  kind?: string | null;
  source: string;
  is_filled: boolean;
  position: number;
}

export interface BrandBook {
  sections: Record<string, BrandRow[]>;
  source: string;
  word: string;
  primary: string;
  secondary: string;
  post_colors: string[];
  checks: { key: string; label: string }[];
  required: string[];
  gaps: string[];
  can_edit: boolean;
  hint: string;
}

export interface BrandState {
  items: {
    key: string; label: string; ok: boolean; note?: string | null;
    required: boolean; checked_at?: string | null;
  }[];
  done: number;
  total: number;
  blocked: string[];
  can_publish: boolean;
}

export interface MediaRow {
  id: number;
  name: string;
  kind: string;
  kind_label: string;
  kind_tone: string;
  url?: string | null;
  branch?: string | null;
  branch_id?: number | null;
  course?: string | null;
  student?: string | null;
  event?: string | null;
  taken_on?: string | null;
  author?: string | null;
  tags?: string | null;
  consent: string;
  consent_label: string;
  consent_tone: string;
  consent_until?: string | null;
  days_left?: number | null;
  expired: boolean;
  expiring: boolean;
  can_publish: boolean;
  can_download: boolean;
}

export interface MediaList {
  rows: MediaRow[];
  kinds: { key: string; label: string; tone: string }[];
  consents: {
    key: string; label: string; tone: string;
    count: number; blocks: boolean;
  }[];
  total: number;
  publishable: number;
  expiring: number;
  expired: number;
  hint: string;
}

export interface KbRow {
  id: number;
  title: string;
  category: string;
  category_label: string;
  category_tone: string;
  body?: string | null;
  tags?: string | null;
  author?: string | null;
  views: number;
  is_pinned: boolean;
  stale: boolean;
  reviewed_at?: string | null;
}

export interface KbList {
  rows: KbRow[];
  categories: { key: string; label: string; tone: string; count: number }[];
  stale: number;
  can_edit: boolean;
  review_months: number;
}

export interface AnalyticsRow {
  key: string | number | null;
  label: string;
  count: number;
  reach: number;
  engagement: number;
  messages: number;
  leads: number;
  qualified: number;
  sales: number;
  revenue: number;
  per_content_leads: number;
  per_content_revenue: number;
  lead_rate: number;
  cost_free_score: number;
}

export interface SmmAnalytics {
  dim: string;
  dim_label: string;
  dims: { key: string; label: string }[];
  rows: AnalyticsRow[];
  months: number;
  total_contents: number;
  best?: AnalyticsRow | null;
  trap?: {
    label: string; reach: number; revenue: number; better: string;
  } | null;
  hint: string;
}

export interface KpiPart {
  key: string;
  label: string;
  score: number;
  max: number;
  percent: number;
  note: string;
}

export interface SmmKpi {
  score: number;
  label: string;
  tone: string;
  parts: KpiPart[];
  plan_percent: number;
  on_time: number;
  published: number;
  planned: number;
  sla_percent: number;
  start: string;
  end: string;
  weights: { key: string; label: string; weight: number }[];
  hint: string;
}

export interface SmmReport {
  id?: number;
  period?: string;
  start: string;
  end: string;
  days: number;
  published: number;
  planned: number;
  plan_percent: number;
  on_time: number;
  totals: Record<string, number>;
  funnel: FunnelStep[];
  top: {
    id: number; code?: string | null; title: string;
    platform_label: string; pillar_label: string; date?: string | null;
    reach: number; leads: number; sales: number; revenue: number;
  }[];
  weak: SmmReport["top"];
  dims: Record<string, {
    label: string; count: number; leads: number; revenue: number;
  }[]>;
  messages: number;
  messages_to_lead: number;
  sla_percent: number;
  kpi: SmmKpi;
  summary: string;
  tips: { about: string; text: string }[];
  sections: { key: string; label: string }[];
  periods?: { key: string; label: string }[];
  saved?: {
    id: number; period: string; start: string; end: string;
    score?: number | null; created_at?: string | null;
  }[];
  frozen?: boolean;
}

// ------------------------------------------- Ustozning o'z natijalari
export interface LeaverRow {
  id: number;
  name: string;
  group?: string | null;
  left_date: string;
  enrolled_date?: string | null;
  months: number;
  reason?: string | null;
  reason_label: string;
  /** true = bizga bog'liq sabab, false = bog'liq emas, null = yozilmagan */
  controllable?: boolean | null;
  note?: string | null;
}

export interface LeaverWindow {
  key: string;
  label: string;
  since: string;
  count: number;
  controllable: number;
  not_controllable: number;
  unknown: number;
  rows: LeaverRow[];
}

export interface MyResults {
  teacher: { id: number; name: string; grade?: string | null; grade_label: string };
  students: { active: number; left: number; total: number };
  retention: { value: number; centre_avg?: number | null };
  churn: {
    value: number;
    centre_avg?: number | null;
    verdict: string;
    tone: string;
    diff?: number | null;
    rank?: number | null;
    peers: number;
  };
  ltv: {
    value?: number | null;
    centre_avg?: number | null;
    verdict: string;
    tone: string;
    diff?: number | null;
    rank?: number | null;
    peers: number;
    note: string;
  };
  windows: LeaverWindow[];
  reasons: {
    key: string; label: string; controllable?: boolean | null; count: number;
  }[];
  enough_data: boolean;
  min_students: number;
  hint: string;
}

// ------------------------------------------- HR: tuzilma va shtat
export interface HrDepartment {
  id: number;
  key?: string | null;
  name: string;
  description?: string | null;
  head_id?: number | null;
  head?: string | null;
  position: number;
  is_active: boolean;
  positions: number;
  employees: number;
}

export interface HrPosition {
  id: number;
  key?: string | null;
  name: string;
  department_id?: number | null;
  department?: string | null;
  system_role?: string | null;
  role_label?: string | null;
  probation_months?: number | null;
  trial_required: boolean;
  salary_from?: number | null;
  salary_to?: number | null;
  description?: string | null;
  requirements?: string | null;
  is_active: boolean;
  employees: number;
}

export interface HrStructure {
  departments: HrDepartment[];
  positions: HrPosition[];
  roles: { key: string; label: string }[];
  employment_types: { key: string; label: string }[];
  can_edit: boolean;
  hint: string;
}

export interface PlanRow {
  id: number;
  year: number;
  month?: number | null;
  branch_id?: number | null;
  branch: string;
  department?: string | null;
  position_id?: number | null;
  position?: string | null;
  approved_headcount: number;
  current_headcount: number;
  gap: number;
  over_staffed: boolean;
  planned_hires: number;
  expected_leaves: number;
  expected_groups: number;
  budgeted_salary?: number | null;
  note?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  approved_at?: string | null;
}

export interface TeacherLoad {
  teacher_id: number;
  name: string;
  branch?: string | null;
  grade?: string | null;
  grade_label: string;
  groups: number;
  max_groups: number;
  free_slots: number;
  percent: number;
  band: string;
  band_label: string;
  tone: string;
}

export interface Workforce {
  year: number;
  rows: PlanRow[];
  totals: {
    approved: number; current: number; gap: number;
    planned_hires: number; expected_leaves: number; budget: number;
  };
  teacher_load: TeacherLoad[];
  load_summary: { key: string; label: string; tone: string; count: number }[];
  free_group_slots: number;
  overloaded: TeacherLoad[];
  statuses: { key: string; label: string; tone: string }[];
  can_edit: boolean;
  hint: string;
}

// ------------------------------------------- HR: xodim so'rovi
export interface RequestApprovalRow {
  step: string;
  step_label: string;
  decision: string;
  by?: string | null;
  at?: string | null;
  note?: string | null;
}

export interface StaffRequestRow {
  id: number;
  public_id?: string | null;
  requested_by?: string | null;
  request_date?: string | null;
  branch_id?: number | null;
  branch: string;
  department?: string | null;
  position_id?: number | null;
  position?: string | null;
  headcount: number;
  employment_type?: string | null;
  employment_label: string;
  work_schedule?: string | null;
  needed_from?: string | null;
  days_left?: number | null;
  reason?: string | null;
  reason_label: string;
  replacing?: string | null;
  salary_from?: number | null;
  salary_to?: number | null;
  requirements?: string | null;
  certificates?: string | null;
  experience_years?: number | null;
  duties?: string | null;
  kpi_note?: string | null;
  priority: string;
  priority_label: string;
  priority_tone: string;
  status: string;
  status_label: string;
  status_tone: string;
  reject_reason?: string | null;
  vacancy_id?: number | null;
  locked: boolean;
  waiting_for?: string[] | null;
  approvals: RequestApprovalRow[];
  created_at?: string | null;
}

export interface StaffRequestList {
  rows: StaffRequestRow[];
  statuses: { key: string; label: string; tone: string; count: number }[];
  reasons: { key: string; label: string; needs_replacement: boolean }[];
  priorities: { key: string; label: string; tone: string; sla_days: number }[];
  employment_types: { key: string; label: string }[];
  waiting_my_decision: number;
  hint: string;
}

// ------------------------------------------- HR: vakansiya
export interface HrVacancy {
  id: number;
  public_id?: string | null;
  title: string;
  position?: string | null;
  trial_required: boolean;
  department?: string | null;
  branch: string;
  branch_id?: number | null;
  hiring_manager?: string | null;
  recruiter?: string | null;
  headcount: number;
  hired_count: number;
  employment_label: string;
  work_schedule?: string | null;
  salary_from?: number | null;
  salary_to?: number | null;
  description?: string | null;
  duties?: string | null;
  requirements?: string | null;
  priority: string;
  priority_label: string;
  priority_tone: string;
  status: string;
  status_label: string;
  status_tone: string;
  is_open: boolean;
  opened_on: string;
  target_close?: string | null;
  closed_at?: string | null;
  close_reason?: string | null;
  close_reason_label?: string | null;
  days_open: number;
  sla_days: number;
  overdue: boolean;
  request_id?: number | null;
  applications: number;
  by_stage: { key: string; label: string; count: number }[];
  in_progress: number;
  hired: number;
  rejected: number;
  interviewed: number;
  offered: number;
  hire_rate: number;
  offer_rate: number;
}

export interface HrVacancyList {
  rows: HrVacancy[];
  statuses: { key: string; label: string; tone: string; count: number }[];
  close_reasons: { key: string; label: string }[];
  summary: {
    open: number; critical: number; overdue: number; seats: number;
    applications: number; avg_days_open: number;
  };
  can_edit: boolean;
  hint: string;
}

// ------------------------------------------- Ustoz kabineti
export interface MyGroup {
  id: number;
  public_id?: string | null;
  name: string;
  subject?: string | null;
  subject_label?: string | null;
  level?: string | null;
  days?: string | null;
  time?: string | null;
  room?: string | null;
  students: number;
  started_on?: string | null;
  last_lesson?: string | null;
  next_lesson?: string | null;
  homework?: HomeworkStat;
}

export interface HomeworkStat {
  checked: number;
  done?: number;
  partial?: number;
  missed?: number;
  percent: number | null;
  label: string;
  tone: string;
  enough?: boolean;
}

export interface MyGroupList {
  rows: MyGroup[];
  total_groups: number;
  total_students: number;
  hint: string;
}

/** Diqqat: bu yerda BALANS yo'q va bo'lmaydi. */
export interface MyStudent {
  id: number;
  public_id?: string | null;
  full_name: string;
  group_id?: number | null;
  group?: string | null;
  status: string;
  enrolled_date?: string | null;
  months?: number | null;
  attendance_percent?: number | null;
  lessons_counted: number;
  missed: number;
  avg_grade?: number | null;
  grades_count: number;
  last_exam?: number | null;
  best_exam?: number | null;
  xp: number;
  level: number;
  at_risk: boolean;
  homework_percent?: number | null;
  homework_checked?: number;
  homework_label?: string;
  homework_tone?: string;
  homework_low?: boolean;
}

export interface MyStudentList {
  rows: MyStudent[];
  groups: { id: number; name: string }[];
  total: number;
  at_risk: number;
  hint: string;
  homework_low?: number;
  homework_threshold?: number;
}

export interface RescheduleQuota {
  used_month: number;
  used_window: number;
  per_month: number;
  per_window: number;
  window_days: number;
  left_month: number;
  left_window: number;
  left: number;
  auto_ok: boolean;
}

export interface RescheduleRow {
  id: number;
  group_id: number;
  group?: string | null;
  teacher?: string | null;
  from_date: string;
  to_date: string;
  from_time?: string | null;
  to_time?: string | null;
  shift_days: number;
  reason?: string | null;
  reason_label: string;
  note?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  auto_approved: boolean;
  decided_by?: string | null;
  decision_note?: string | null;
  created_at?: string | null;
}

export interface MyReschedules {
  quota: RescheduleQuota;
  quota_next: RescheduleQuota;
  next_month: string;
  rows: RescheduleRow[];
  reasons: { key: string; label: string }[];
  min_notice_days: number;
  max_shift_days: number;
  carry_over: boolean;
  hint: string;
  cannot_cancel: string;
}

export interface SubstitutionRow {
  id: number;
  group_id: number;
  group?: string | null;
  subject?: string | null;
  lesson_date: string;
  lesson_time?: string | null;
  original_teacher?: string | null;
  substitute_teacher?: string | null;
  substitute_teacher_id?: number | null;
  reason?: string | null;
  reason_label: string;
  note?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  open: boolean;
  created_at?: string | null;
}

export interface MySubstitutions {
  my_requests: SubstitutionRow[];
  assigned_to_me: SubstitutionRow[];
  open_offers: SubstitutionRow[];
  my_groups: { id: number; name: string }[];
  reasons: { key: string; label: string }[];
  hint: string;
}

export interface BookOrderItemRow {
  id: number;
  title: string;
  level?: string | null;
  qty: number;
  delivered_qty: number;
  note?: string | null;
  consumable_id?: number | null;
}

export interface BookOrderRow {
  id: number;
  public_id?: string | null;
  teacher?: string | null;
  branch?: string | null;
  group?: string | null;
  needed_by?: string | null;
  days_left?: number | null;
  urgency: string;
  urgency_label: string;
  urgency_tone: string;
  note?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  is_open: boolean;
  decided_by?: string | null;
  decision_note?: string | null;
  delivered_at?: string | null;
  task_id?: number | null;
  items: BookOrderItemRow[];
  total_qty: number;
  titles: number;
  created_at?: string | null;
}

export interface MyBookOrders {
  rows: BookOrderRow[];
  groups: { id: number; name: string }[];
  urgencies: { key: string; label: string; tone: string; days: number }[];
  hint: string;
}

export interface BookCatalogue {
  rows: { id: number; name: string; qty: number; in_stock: boolean }[];
}


// ------------------------------------------------ Imtihon buyurtmasi
export interface ExamOrder {
  id: number;
  public_id?: string | null;
  group_id: number;
  group?: string | null;
  level?: string | null;
  teacher_id?: number | null;
  teacher?: string | null;
  branch_id?: number | null;
  branch?: string | null;
  date?: string | null;
  date_text: string;
  time?: string | null;
  kind: string;
  kind_label: string;
  unit_no?: number | null;
  students_count: number;
  note?: string | null;
  status: string;
  status_label: string;
  status_tone: string;
  accepted_by?: string | null;
  accepted_at?: string | null;
  decision_note?: string | null;
  reject_reason?: string | null;
  reject_reason_label?: string | null;
  exam_id?: number | null;
  created_at?: string | null;
  /** Ustoz va examiner ko'radigan bir xil xabar matni. */
  message: string;
}

interface ExamOrderForm {
  kinds: { key: string; label: string }[];
  unit_count: number;
  min_notice_days: number;
  max_ahead_days: number;
  reject_reasons: { key: string; label: string }[];
  statuses: { key: string; label: string; tone: string }[];
  hint: string;
}

export interface MyExamOrders extends ExamOrderForm {
  rows: ExamOrder[];
  groups: {
    id: number;
    name: string;
    level?: string | null;
    time?: string | null;
    students: number;
  }[];
}

export interface ExamOrderQueue extends ExamOrderForm {
  rows: ExamOrder[];
  new: number;
  accepted: number;
  urgent: ExamOrder[];
}

// ---------- Moliya: xodim oyliklari va to'lov qilganlar ----------
export interface StaffPayrollRow {
  user_id: number | null;
  teacher_id?: number;
  name: string;
  role?: string;
  salary: number;
  paid: number;
  left: number;
  exam_count?: number;
  points?: number;
  hours?: number;
  students?: number;
  clamped_min?: boolean;
  clamped_max?: boolean;
  /** Volontyor / Junior / Middle / Senior */
  grade?: string;
  grade_label?: string;
  grade_coef?: number;
  salary_base?: number;
  grade_note?: string;
}

export interface StaffPayrollList {
  period: string;
  rows: StaffPayrollRow[];
  total: number;
  paid_total: number;
  left_total: number;
  min: number;
  max: number;
  hint?: string;
  can_pay: boolean;
  kinds: { key: string; label: string }[];
}

export interface StaffSalaryRow {
  id: number;
  amount: number;
  kind: string;
  kind_label: string;
  period?: string | null;
  date?: string | null;
  method?: string | null;
  note?: string | null;
  created_by?: string | null;
}

export interface StaffSalaryHistory {
  rows: StaffSalaryRow[];
  total: number;
  can_pay: boolean;
}

export interface MonthPaymentRow {
  id: number;
  date: string | null;
  student_id: number;
  student: string;
  phone?: string | null;
  amount: number;
  method: string;
  method_label: string;
  branch: string;
  is_new: boolean;
  note?: string | null;
  created_by?: string | null;
}

export interface MonthPayments {
  period: string;
  rows: MonthPaymentRow[];
  count: number;
  students: number;
  total: number;
  new_total: number;
  old_total: number;
}

/** Guruh bosqichi: "Step 2 · Unit 7/12". Manba — imtihonlar. */
export interface GroupProgress {
  group_id: number;
  subject?: string | null;
  level?: string | null;
  level_label?: string | null;
  unit: number;
  unit_total: number;
  next_unit?: number | null;
  done_units: number[];
  percent: number;
  last_exam?: {
    id: number;
    date?: string | null;
    unit_no: number;
    title?: string | null;
    students: number;
    avg_percent?: number | null;
  } | null;
}

/** Support teacherning O'Z seansidagi yo'qlamasi. Ustozning davomati
 *  bilan hech qanday aloqasi yo'q — alohida jadval, alohida kunlar. */
export interface SupportAttendanceGrid {
  days: string[];
  students: GridStudent[];
  /** Kalit: "YYYY-MM-DD:studentId" */
  marks: Record<string, boolean | number>;
  plan: {
    user_id: number;
    name?: string | null;
    days: string[];
    start?: string | null;
    end?: string | null;
  }[];
  label?: string | null;
  today: string;
  can_edit: boolean;
  can_past: boolean;
  hint?: string | null;
  /** Kunlik seans: "YYYY-MM-DD" -> qaysi vaqtdan qaysi vaqtgacha. */
  sessions?: Record<
    string,
    { start: string; end: string; minutes: number; hours: number;
      students: number }
  >;
  default_start?: string | null;
  default_end?: string | null;
  hours_total?: number;
  students_total?: number;
}

/** Examiner / support darajasi: Volontyor -> Junior -> Middle -> Senior. */
export interface StaffGradeRate {
  key: string;
  label: string;
  coef: number;
  order_no: number;
}

export interface StaffGradeRow {
  user_id: number;
  name: string;
  role: string;
  grade: string;
  grade_label: string;
  coef: number;
  since?: string | null;
  note?: string | null;
}

export interface StaffGrades {
  grades: StaffGradeRate[];
  rows: StaffGradeRow[];
  can_edit: boolean;
  can_edit_rates: boolean;
  hint: string;
}

/** HR kutubxonasi: onboarding video, kitob va fayllari. */
export interface LibraryItem {
  id: number;
  title: string;
  kind: string;
  kind_label: string;
  url?: string | null;
  attachment_id?: number | null;
  minutes: number;
  description?: string | null;
  target_roles: string[];
  required: boolean;
  order_no: number;
  active: boolean;
  percent: number;
  passed: boolean;
  passed_at?: string | null;
  note?: string | null;
  /** Faqat HR uchun */
  watchers?: number;
  done?: number;
  avg_percent?: number;
}

export interface LibraryList {
  items: LibraryItem[];
  kinds: { key: string; label: string }[];
  can_manage: boolean;
  my_total: number;
  my_done: number;
  my_percent: number;
  roles: { key: string; label: string }[];
}

export interface LibraryPerson {
  user_id: number;
  name: string;
  role: string;
  percent: number;
  passed: boolean;
  passed_at?: string | null;
  passed_by?: string | null;
  note?: string | null;
}

export interface LibraryPeople {
  item: LibraryItem;
  rows: LibraryPerson[];
  done: number;
  total: number;
}

/** Support teacherning O'Z daraja yo'li — ustoznikidan alohida. */
export interface SupportCareerLevel {
  key: string;
  label: string;
  coef: number;
  groups: string;
  free_courses: number;
  cert?: string | null;
  note?: string | null;
  paid: boolean;
}

export interface SupportCareer {
  kind: string;
  grade: string;
  grade_label: string;
  coef: number;
  since?: string | null;
  months_in_grade: number;
  months_total: number;
  volunteer_months_needed: number;
  levels: SupportCareerLevel[];
  stats: {
    period?: string | null;
    groups: number;
    hours: number;
    students: number;
    avg_percent?: number | null;
    salary_base: number;
    salary: number;
  };
  library: { done: number; total: number; percent: number };
  formula?: string | null;
  hint: string;
}
