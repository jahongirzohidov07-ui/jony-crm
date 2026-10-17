import { api, ApiError, getActiveRole, getToken, invalidate } from "./api";

/**
 * SO'Z BILISH (lug'at banki) — Jony Student uchun API turlari va
 * yordamchilar (2026-10-16).
 *
 * Server: api/wordbank.py (/api/wordbank/me, /session, /answer,
 * /size-test/start|next|finish). Bo'lim bayroq orqali YOPIQ
 * (IntegrationSetting "wordbank_branches"): yoqilmagan filial
 * o'quvchisiga /api/wordbank/* 404 qaytaradi.
 *
 * Shuning uchun /wordbank/me bu yerda "jim" o'qiladi: umumiy api.get
 * har xatoda toast chiqaradi — Profil yoki O'rganish sahifasini ochgan
 * HAR bir o'quvchi "Not Found" xabarini ko'rib qolardi. 404 = "bo'lim
 * yo'q" (hech narsa ko'rsatilmaydi), boshqa xato = matn qaytadi.
 * Yozuv so'rovlari (mashq, javob, test) odatdagi api.post orqali ketadi.
 */

export type WbBand = {
  band: number;
  label: string;
  total: number;
  known: number;
  learning: number;
  ready: boolean;
  coins: number;
  done: boolean;
  awarded_at: string | null;
};

/** Hajm testi natijasi — faqat TAXMINIY, tasdiqlangan songa qo'shilmaydi. */
export type WbSizeTest = {
  taxminiy: boolean;
  label: string;
  test_id: number;
  estimate: number;
  low: number;
  high: number;
  /** {daraja: [to'g'ri, xato, savollar soni]} */
  bands: Record<string, [number, number, number]>;
  date: string | null;
};

export type WbMe = {
  known: number;
  known_label: string;
  due_today: number;
  bands: WbBand[];
  coins_earned: number;
  size_test: WbSizeTest | null;
  /** Server hozircha bermaydi (2026-10-16); qo'shilsa ekranda chiqadi. */
  streak?: number | null;
  /** 2026-10-17: "Jami" reytingidagi o'rin (null — reytingda yo'q). */
  ranks?: WbRanks;
  /** 2026-10-17: eng yaxshi natija (tarix) — hech qachon pasaymaydi. */
  best_known?: number;
  /** 2026-10-17: FAQAT tasdiqlangan sertifikatlar (eng oxirgisi birinchi). */
  certs?: WbCertBadge[];
  /** 2026-10-17: tekshirilayotgan yuklamalar SONI (natijasiz). */
  certs_pending?: number;
};

export type WbRanks = {
  group: number | null;
  branch: number | null;
  school: number | null;
};

/** Tasdiqlangan sertifikat belgisi (profil, reyting, ota-ona, ustoz). */
export type WbCertBadge = {
  id: number;
  exam_type: CertExamType;
  exam_label: string;
  /** "IELTS 7.0", "Multilevel B2 (58)" — server yasaydi */
  label: string;
  test_date: string | null;
};

export type WbItemR = {
  item_id: number;
  mode: "R";
  word: string;
  options: string[];
  tts?: boolean;
};
export type WbItemP = {
  item_id: number;
  mode: "P";
  uz: string;
  example: string | null;
  example_uz: string | null;
  hint: string;
};
export type WbItem = WbItemR | WbItemP;

export type WbSession = {
  session_id: number | null;
  kind: string;
  expires_at?: string;
  items: WbItem[];
  message?: string;
};

export type WbAward = { band: number; coins: number; already_paid?: boolean };

export type WbAnswer = {
  /** null — juda tez yozilgan (shubhali) javob, baho qaytarilmaydi */
  correct: boolean | null;
  expected: string | null;
  suspect: boolean;
  /** 2026-10-16 (review): vaqt tugadi — holat o'zgarmadi, baho/javob yo'q */
  timeout?: boolean;
  stage: number;
  known: boolean;
  due: string | null;
  awards?: WbAward[];
  message?: string;
};

export type WbTestStart = {
  session_id: number;
  band: number;
  items: WbItemR[];
  expires_at: string;
};
export type WbTestStep =
  | { done: false; band: number; items: WbItemR[] }
  | { done: true; result: WbSizeTest };

/** Mashq taymeri (DESIGN §2): tanlash 15 s, yozib topish 30 s. */
export const LIMIT_SEC = { R: 15, P: 30 } as const;
/** Server shubhali deb hisoblaydigan chegara (api/wordbank.py SUSPECT_MS). */
export const SUSPECT_MS = 1200;

// ------------------------------------------------- jim o'qish ---
export type WbLoad =
  | { status: "ok"; data: WbMe }
  | { status: "off" }
  | { status: "error"; message: string };

const TTL_MS = 30_000;
let cache: { at: number; token: string; value: WbLoad } | null = null;
let inflight: { token: string; p: Promise<WbLoad> } | null = null;

/** Javob/testdan keyin chaqiriladi — raqamlar darhol yangilansin. */
export function invalidateWordbank() {
  cache = null;
  inflight = null;
}

async function fetchMe(token: string): Promise<WbLoad> {
  const role = getActiveRole();
  let res: Response;
  try {
    res = await fetch("/api/wordbank/me", {
      headers: {
        Authorization: `Bearer ${token}`,
        ...(role ? { "X-Active-Role": role } : {}),
      },
    });
  } catch {
    return { status: "error", message: "Internet bilan bog'lanib bo'lmadi" };
  }
  // Bayroq o'chiq / filial yoqilmagan — bo'lim yo'qdek
  if (res.status === 404) return { status: "off" };
  if (!res.ok) {
    let message = `Xatolik: ${res.status}`;
    try {
      const j = await res.json();
      if (j && typeof j.detail === "string") message = j.detail;
    } catch {
      /* JSON emas — umumiy matn qoladi */
    }
    return { status: "error", message };
  }
  try {
    return { status: "ok", data: (await res.json()) as WbMe };
  } catch {
    return { status: "error", message: "Javobni o'qib bo'lmadi" };
  }
}

/** /api/wordbank/me — toast chiqarmaydi, 30 s keshlanadi. */
export async function loadWordbank(fresh = false): Promise<WbLoad> {
  const token = getToken();
  if (!token) return { status: "off" };
  if (!fresh && cache && cache.token === token
      && Date.now() - cache.at < TTL_MS) {
    return cache.value;
  }
  if (!fresh && inflight && inflight.token === token) return inflight.p;
  const p = fetchMe(token);
  const mine = { token, p };
  inflight = mine;
  const value = await p;
  if (inflight === mine) {
    inflight = null;
    // Xato keshlanmaydi — keyingi ochishda qayta uriniladi
    if (value.status !== "error" && getToken() === token) {
      cache = { at: Date.now(), token, value };
    }
  }
  return value;
}

// ------------------------------------------------ hisob-kitob ---
/** Hozirgi daraja: tugatilmagan va so'zlari tayyor eng past daraja. */
export function focusBand(bands: WbBand[]): WbBand | null {
  return bands.find((b) => b.ready && b.total > 0 && !b.done) ?? null;
}

/** Test bo'yicha daraja ulushi (taxmin uchun tuzatilgan, DESIGN §3). */
export function pHat(right: number, wrong: number, n: number, k = 4) {
  if (!n) return 0;
  return Math.min(1, Math.max(0, (right - wrong / (k - 1)) / n));
}

/** Taxminiy son ekranda 100 gacha yaxlitlanadi (DESIGN §3). */
export function roundEst(x: number) {
  return Math.max(0, Math.round((x || 0) / 100) * 100);
}

/** Inglizcha so'zni ovoz chiqarib o'qish (Android polifili ham shu API). */
export function speakEn(text: string) {
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.9;
    window.speechSynthesis.speak(u);
  } catch {
    /* TTS yo'q — jim o'tadi */
  }
}

// =====================================================================
//  2026-10-17: REYTING ("So'z bilish"), TARIX va SERTIFIKATLAR
//  (OWNER D2–D4). Shartnoma: scratchpad/vocab/PHASE23_CONTRACT.md.
//  Server: api/wordbank_social.py (reyting, tarix, ustoz ro'yxati) va
//  api/wordbank_certs.py (sertifikatlar). Hammasi yupqa chaqiruvlar —
//  hisob-kitob serverda.
// =====================================================================

// ------------------------------------------------- jim o'qish (umumiy) ---
export type WbQuiet<T> =
  | { status: "ok"; data: T }
  | { status: "off" }
  /** code — HTTP holati (tarmoq xatosida yo'q), 2026-10-17 */
  | { status: "error"; message: string; code?: number };

function authHeaders(): Record<string, string> {
  const token = getToken();
  const role = getActiveRole();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(role ? { "X-Active-Role": role } : {}),
  };
}

async function errorText(res: Response): Promise<string> {
  try {
    const j = await res.json();
    if (j && typeof j.detail === "string") return j.detail;
  } catch {
    /* JSON emas — umumiy matn qoladi */
  }
  return `Xatolik: ${res.status}`;
}

/** GET — toast chiqarmaydi; 404 = bo'lim yopiq ("off"). */
export async function wbQuietGet<T>(path: string): Promise<WbQuiet<T>> {
  if (!getToken()) return { status: "off" };
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { headers: authHeaders() });
  } catch {
    return { status: "error", message: "Internet bilan bog'lanib bo'lmadi" };
  }
  if (res.status === 404) return { status: "off" };
  if (!res.ok) return { status: "error", message: await errorText(res), code: res.status };
  try {
    return { status: "ok", data: (await res.json()) as T };
  } catch {
    return { status: "error", message: "Javobni o'qib bo'lmadi" };
  }
}

// ------------------------------------------------------- reyting ---
export type WbScope = "group" | "branch" | "school";
export type WbPeriod = "total" | "week" | "history";

export type WbBoardRow = {
  /** O'rin (1 dan). me qatorida null — hali reytingda yo'q (0 so'z). */
  rank: number | null;
  /** Yashirilgan ism ("Aziz K."); o'zingizniki — "Siz". */
  name: string;
  initials: string;
  group: string | null;
  branch: string | null;
  /** Tasdiqlangan so'zlar; period=history da — eng yaxshi natija. */
  known: number;
  week_gain: number;
  bands_done: number;
  /** FAQAT tasdiqlangan oxirgi sertifikat, masalan "IELTS 7.0". */
  cert_badge: string | null;
  /** Faqat period=history: bitirgan | ketgan | null (hozirgi o'quvchi). */
  label: "bitirgan" | "ketgan" | null;
  /** "tekshirilmoqda" belgisi — faqat ko'rsatish, coinga ta'sir qilmaydi. */
  flagged: boolean;
  is_me: boolean;
};

export type WbFirstFinisher = {
  band: number;
  /** "Common 3000" */
  label: string;
  name: string;
  initials: string;
  /** Tugatgan sana (YYYY-MM-DD) */
  at: string | null;
  is_me: boolean;
};

export type WbBoard = {
  scope: WbScope;
  period: WbPeriod;
  /** scope=group da ishlatilgan guruh */
  group_id: number | null;
  /** Eng ko'pi TOP 50 */
  rows: WbBoardRow[];
  /** O'z qatoringiz (TOP 50 dan tashqarida bo'lsa ham) */
  me: WbBoardRow | null;
  /** Keyingi o'ringa yana nechta so'z (1-o'rinda — null) */
  gap_to_next: number | null;
  /** Qamrovdagi reytingdagi o'quvchilar soni */
  total: number;
  /** Guruh tanlagichi uchun (2+ guruh bo'lsa ko'rsatiladi) */
  groups: { id: number; name: string }[];
  /** Faqat period=history, aks holda [] */
  first_finishers: WbFirstFinisher[];
  /** Joriy hafta boshi (Toshkent dushanbasi, YYYY-MM-DD) */
  week_start: string;
  hint: string | null;
};

/** GET /api/wordbank/leaderboard — jim (bo'lim yopiq — "off"). */
export function getWordBoard(p: {
  scope: WbScope;
  period: WbPeriod;
  group_id?: number | null;
}): Promise<WbQuiet<WbBoard>> {
  const q = new URLSearchParams({ scope: p.scope, period: p.period });
  if (p.group_id) q.set("group_id", String(p.group_id));
  return wbQuietGet<WbBoard>(`/wordbank/leaderboard?${q.toString()}`);
}

// ------------------------------------------------- sertifikatlar ---
export type CertExamType =
  | "ielts" | "multilevel" | "cefr_other" | "sat" | "duolingo" | "toefl"
  | "cambridge" | "topik" | "goethe" | "torfl" | "other";

export type CertStatus =
  | "pending" | "confirmed" | "rejected" | "withdrawn" | "revoked";

/** api/roles.py VOCAB_CERT_EXAM_TYPES bilan bir xil. */
export const CERT_EXAM_TYPES: { key: CertExamType; label: string }[] = [
  { key: "ielts", label: "IELTS" },
  { key: "multilevel", label: "CEFR / Multilevel" },
  { key: "cefr_other", label: "CEFR (boshqa)" },
  { key: "sat", label: "SAT" },
  { key: "duolingo", label: "Duolingo" },
  { key: "toefl", label: "TOEFL" },
  { key: "cambridge", label: "Cambridge" },
  { key: "topik", label: "TOPIK" },
  { key: "goethe", label: "Goethe" },
  { key: "torfl", label: "TORFL" },
  { key: "other", label: "Boshqa" },
];

export const CERT_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;
export const CAMBRIDGE_EXAMS = [
  "A2 Key", "B1 Preliminary", "B2 First", "C1 Advanced", "C2 Proficiency",
] as const;
export const TOPIK_LEVELS = ["1", "2", "3", "4", "5", "6"] as const;
export const IELTS_SUBS = ["L", "R", "W", "S"] as const;

/**
 * Natija maydonlari (server ham AYNAN shu qoidani tekshiradi —
 * shartnoma §C). score: son chegarasi va qadami; level: ro'yxat yoki
 * erkin matn; exam_name: ro'yxat yoki erkin matn.
 */
export type CertRule = {
  score?: { min: number; max: number; step: number; required: boolean };
  level?: { options?: readonly string[]; maxLen?: number; required: boolean };
  exam_name?: { options?: readonly string[]; maxLen?: number; required: boolean };
  sub_scores?: readonly string[];
};
export const CERT_RULES: Record<CertExamType, CertRule> = {
  ielts: { score: { min: 1, max: 9, step: 0.5, required: true }, sub_scores: IELTS_SUBS },
  multilevel: {
    level: { options: CERT_LEVELS, required: true },
    score: { min: 0, max: 75, step: 1, required: true },
  },
  cefr_other: {
    level: { options: CERT_LEVELS, required: true },
    exam_name: { maxLen: 40, required: false },
  },
  sat: { score: { min: 400, max: 1600, step: 10, required: true } },
  duolingo: { score: { min: 10, max: 160, step: 5, required: true } },
  toefl: { score: { min: 0, max: 120, step: 1, required: true } },
  cambridge: {
    exam_name: { options: CAMBRIDGE_EXAMS, required: true },
    score: { min: 80, max: 230, step: 1, required: true },
  },
  topik: { level: { options: TOPIK_LEVELS, required: true } },
  goethe: { level: { options: CERT_LEVELS, required: true } },
  torfl: { level: { options: CERT_LEVELS, required: true } },
  other: {
    exam_name: { maxLen: 40, required: true },
    level: { maxLen: 20, required: true },
  },
};

export const CERT_VERIFY_METHODS = [
  "asl nusxa ko'rildi", "onlayn tekshirildi", "fayl bo'yicha",
] as const;
export type CertVerifyMethod = (typeof CERT_VERIFY_METHODS)[number];
export const CERT_REJECT_REASONS = [
  "fayl o'qilmaydi", "ma'lumot mos emas", "boshqa odamniki",
  "sertifikat emas", "boshqa",
] as const;
export type CertRejectReason = (typeof CERT_REJECT_REASONS)[number];

export const CERT_STATUS_LABEL: Record<CertStatus, string> = {
  pending: "Yuklandi — tekshirilmoqda",
  confirmed: "Tasdiqlangan",
  rejected: "Rad etildi",
  withdrawn: "Qaytarib olindi",
  revoked: "Bekor qilindi",
};

/** Fayl chegarasi (server: wordbank_certs.MAX_BYTES). */
export const CERT_MAX_BYTES = 3 * 1024 * 1024;
export const CERT_ACCEPT = "image/*,application/pdf";

/** O'quvchining o'z yuklamasi. Natija maydonlari FAQAT confirmed da. */
export type MyCert = {
  id: number;
  exam_type: CertExamType;
  exam_label: string;
  status: CertStatus;
  status_label: string;
  created_at: string;
  test_date: string | null;
  /** confirmed bo'lmasa — null */
  result_label: string | null;
  score: number | null;
  level: string | null;
  exam_name: string | null;
  sub_scores: Record<string, number> | null;
  cert_no: string | null;
  /** faqat rejected */
  reject_reason: string | null;
  reject_note: string | null;
  can_withdraw: boolean;
  /** rejected — qayta yuklash mumkin */
  can_reupload: boolean;
  mime: string | null;
};

export type MyCerts = {
  items: MyCert[];
  limits: {
    max_pending: number;
    pending: number;
    max_30d: number;
    used_30d: number;
    max_bytes: number;
  };
};

export type CertForm = {
  exam_type: CertExamType;
  exam_name?: string | null;
  score?: number | null;
  level?: string | null;
  sub_scores?: Record<string, number> | null;
  /** YYYY-MM-DD */
  test_date: string;
  cert_no?: string | null;
};

/** GET /api/wordbank/certs/mine — jim. */
export function getMyCerts(): Promise<WbQuiet<MyCerts>> {
  return wbQuietGet<MyCerts>("/wordbank/certs/mine");
}

/**
 * POST /api/wordbank/certs/mine — MULTIPART (api.post JSON yuboradi,
 * shuning uchun bu yerda to'g'ridan-to'g'ri fetch; Content-Type ni
 * brauzer o'zi qo'yadi). Javobda ball YO'Q: {id, status: "pending"}.
 * Xato — ApiError (server matni, status bilan).
 */
export async function uploadMyCert(
  form: CertForm,
  file: Blob,
  filename: string,
): Promise<{ id: number; status: "pending" }> {
  const fd = new FormData();
  fd.append("file", file, filename);
  fd.append("exam_type", form.exam_type);
  fd.append("test_date", form.test_date);
  if (form.exam_name) fd.append("exam_name", form.exam_name);
  if (form.score !== undefined && form.score !== null)
    fd.append("score", String(form.score));
  if (form.level) fd.append("level", form.level);
  if (form.sub_scores && Object.keys(form.sub_scores).length)
    fd.append("sub_scores", JSON.stringify(form.sub_scores));
  if (form.cert_no) fd.append("cert_no", form.cert_no);
  let res: Response;
  try {
    res = await fetch("/api/wordbank/certs/mine", {
      method: "POST",
      headers: authHeaders(),
      body: fd,
    });
  } catch {
    throw new ApiError("Internet bilan bog'lanib bo'lmadi");
  } finally {
    invalidate();
  }
  if (!res.ok) {
    const err = new ApiError(await errorText(res));
    err.status = res.status;
    throw err;
  }
  return res.json();
}

/** DELETE /api/wordbank/certs/mine/{id} — kutilayotganini qaytarib olish. */
export function withdrawMyCert(id: number) {
  return api.delete<{ id: number; status: "withdrawn" }>(
    `/wordbank/certs/mine/${id}`,
  );
}

/**
 * Sertifikat faylini token bilan oladi (oddiy <img src> ishlamaydi —
 * server tokenni sarlavhada so'raydi). Qaytgan Blob dan
 * URL.createObjectURL qiling va keyin revokeObjectURL.
 * path: `/wordbank/certs/mine/${id}/file` yoki `/wordbank/certs/${id}/file`.
 */
export async function fetchCertFile(path: string): Promise<Blob> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { headers: authHeaders() });
  } catch {
    throw new ApiError("Internet bilan bog'lanib bo'lmadi");
  }
  if (!res.ok) {
    const err = new ApiError(await errorText(res));
    err.status = res.status;
    throw err;
  }
  return res.blob();
}

// ------------------------------------------- xodim: tekshiruv navbati ---
export type StaffCert = {
  id: number;
  student_id: number;
  /** Xodimga to'liq ism */
  student_name: string;
  student_public_id: string | null;
  /** O'quvchi bazada hali bormi (o'chirilgan bo'lsa false — name_snap) */
  student_exists: boolean;
  branch_id: number | null;
  branch_name: string | null;
  groups: string[];
  exam_type: CertExamType;
  exam_label: string;
  exam_name: string | null;
  score: number | null;
  level: string | null;
  sub_scores: Record<string, number> | null;
  result_label: string | null;
  test_date: string | null;
  cert_no: string | null;
  mime: string | null;
  size: number | null;
  status: CertStatus;
  created_at: string;
  /** faqat pending: necha kundan beri kutmoqda (3 dan ko'p — qizil) */
  days_waiting: number | null;
  /** "bu fayl boshqa o'quvchi tomonidan ham yuklangan" yoki null */
  duplicate_warning: string | null;
  verify_method: string | null;
  review_note: string | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  reject_reason: string | null;
  reject_note: string | null;
  revoked_by_name: string | null;
  revoked_at: string | null;
  revoke_note: string | null;
};

export type StaffCertList = {
  items: StaffCert[];
  counts: { pending: number; confirmed: number; rejected: number };
  /** Bekor qilish tugmasi (VOCAB_CERT_REVOKE) */
  can_revoke: boolean;
};

/** status: "pending" (standart) | "confirmed" | "rejected,revoked" ... */
export function listCerts(p: {
  status?: string;
  branch_id?: number | null;
  group_id?: number | null;
} = {}) {
  const q = new URLSearchParams({ status: p.status || "pending" });
  if (p.branch_id) q.set("branch_id", String(p.branch_id));
  if (p.group_id) q.set("group_id", String(p.group_id));
  return api.fresh<StaffCertList>(`/wordbank/certs?${q.toString()}`);
}

/** Kutilayotganlar soni (menyu belgisi) — jim. */
export function certsPendingCount(): Promise<WbQuiet<{ pending: number }>> {
  return wbQuietGet<{ pending: number }>("/wordbank/certs/count");
}

export type CertConfirmBody = {
  exam_type: CertExamType;
  exam_name?: string | null;
  score?: number | null;
  level?: string | null;
  sub_scores?: Record<string, number> | null;
  test_date: string;
  cert_no?: string | null;
  verify_method: CertVerifyMethod;
  note?: string | null;
};

export function confirmCert(id: number, body: CertConfirmBody) {
  return api.post<StaffCert>(`/wordbank/certs/${id}/confirm`, body);
}

export function rejectCert(
  id: number,
  body: { reason_code: CertRejectReason; note?: string | null },
) {
  return api.post<StaffCert>(`/wordbank/certs/${id}/reject`, body);
}

export function revokeCert(id: number, body: { note: string }) {
  return api.post<StaffCert>(`/wordbank/certs/${id}/revoke`, body);
}

// ------------------------------------------ ustoz: guruh so'z bilishi ---
export type TeacherWordRow = {
  id: number;
  /** Xodimga to'liq ism */
  name: string;
  known: number;
  best: number;
  week_gain: number;
  bands_done: number;
  /** Oxirgi hajm testi — TAXMINIY */
  size_test: { estimate: number; low: number; high: number; date: string | null } | null;
  /** FAQAT tasdiqlangan */
  certs: WbCertBadge[];
  flagged: boolean;
};

export type TeacherWordStats = {
  group: { id: number; name: string };
  /** Guruh filialida bo'lim yoqilmagan bo'lsa false va students bo'sh */
  enabled: boolean;
  week_start: string;
  students: TeacherWordRow[];
};

export function getTeacherWordStats(groupId: number) {
  return api.get<TeacherWordStats>(
    `/wordbank/teacher/students?group_id=${groupId}`,
  );
}

// ------------------------------------------------------ ota-ona ---
/** GET /api/parent/{token} javobidagi "wordbank" (bo'lim yopiq — null). */
export type ParentWordbank = {
  known: number;
  best: number;
  bands_done: number;
  rank_group: number | null;
  rank_branch: number | null;
  /** FAQAT tasdiqlangan */
  certs: WbCertBadge[];
} | null;
