import { getActiveRole, getToken } from "./api";

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
