/**
 * OFFLINE REJIM (2026-10-07).
 *
 * Jahongir: "ilovada offline rejimda ham mashqlar ishlash mumkin
 * bo'lsin".
 *
 * Qanday ishlaydi:
 *  1) Internet bor paytda /student/offline/pack yuklab olinadi
 *     (300 ta so'z + 200 ta grammatika savoli) va telefonda
 *     (localStorage) saqlanadi. Kuniga bir marta yangilanadi.
 *  2) Internet yo'q paytda mashq shu to'plamdan ishlaydi, javob
 *     telefonda tekshiriladi.
 *  3) Har bir javob NAVBATGA yoziladi. Internet qaytgach ODDIY
 *     /student/vocab/answer va /student/grammar/answer manzillariga
 *     birma-bir yuboriladi — XP'ni server o'zi qayta tekshirib beradi.
 *
 * Navbat oddiy fetch bilan yuboriladi (api.ts emas): xato bo'lsa
 * o'quvchiga toast ko'rsatilmasin va 401 da login sahifasiga
 * otib yuborilmasin — navbat keyingi safar qayta urinadi.
 */
import { api, getToken } from "./api";

const PACK_KEY = (lang: string) => `jony_offline_pack_${lang}`;
const QUEUE_KEY = "jony_offline_queue";
const PACK_MAX_AGE_MS = 24 * 60 * 60 * 1000;
const QUEUE_MAX = 2000;

export interface OfflineWord {
  id: number;
  word: string;
  translation: string;
}

export interface OfflineGrammar {
  id: number;
  kind: string;
  prompt: string;
  options: string[];
  answer: string;
  explain?: string | null;
  topic?: string;
  level?: string;
}

export interface OfflinePack {
  language: string;
  generated_at: string;
  saved_at?: number;
  vocab: OfflineWord[];
  grammar: OfflineGrammar[];
  vocab_xp: number;
  grammar_xp: number;
}

export interface QueuedAnswer {
  path: "/student/vocab/answer" | "/student/grammar/answer";
  body: Record<string, unknown>;
  at: number;
}

export function isOnline(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine !== false;
}

export function loadPack(lang: string): OfflinePack | null {
  try {
    const raw = localStorage.getItem(PACK_KEY(lang));
    return raw ? (JSON.parse(raw) as OfflinePack) : null;
  } catch {
    return null;
  }
}

/** To'plamni yangilaydi (eskirgan bo'lsa yoki force). Xato jim o'tadi. */
export async function refreshPack(lang: string, force = false): Promise<OfflinePack | null> {
  const cur = loadPack(lang);
  if (!force && cur?.saved_at && Date.now() - cur.saved_at < PACK_MAX_AGE_MS) {
    return cur;
  }
  if (!isOnline() || !getToken()) return cur;
  try {
    const res = await fetch(`/api/student/offline/pack?language=${encodeURIComponent(lang)}`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) return cur;
    const pack = (await res.json()) as OfflinePack;
    pack.saved_at = Date.now();
    try {
      localStorage.setItem(PACK_KEY(lang), JSON.stringify(pack));
    } catch {
      /* xotira to'la — eski to'plam qoladi */
    }
    return pack;
  } catch {
    return cur;
  }
}

export function readQueue(): QueuedAnswer[] {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    const q = raw ? JSON.parse(raw) : [];
    return Array.isArray(q) ? q : [];
  } catch {
    return [];
  }
}

function writeQueue(q: QueuedAnswer[]) {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(q.slice(-QUEUE_MAX)));
  } catch {
    /* xotira to'la */
  }
  window.dispatchEvent(new CustomEvent("jony-offline-queue", { detail: q.length }));
}

export function enqueue(item: Omit<QueuedAnswer, "at">) {
  const q = readQueue();
  q.push({ ...item, at: Date.now() });
  writeQueue(q);
}

let flushing = false;

/** Navbatni serverga yuboradi. Yuborilgan javoblar soni qaytadi. */
export async function flushQueue(): Promise<number> {
  if (flushing || !isOnline() || !getToken()) return 0;
  flushing = true;
  let sent = 0;
  try {
    let q = readQueue();
    while (q.length) {
      const item = q[0];
      let res: Response;
      try {
        res = await fetch(`/api${item.path}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getToken()}`,
          },
          body: JSON.stringify(item.body),
        });
      } catch {
        break; // internet yana uzildi — keyinroq
      }
      if (res.status === 401 || res.status >= 500) break;
      // 2xx — yozildi; 4xx (savol o'chirilgan va h.k.) — tashlab yuboriladi
      q = readQueue().slice(1);
      writeQueue(q);
      if (res.ok) sent++;
    }
  } finally {
    flushing = false;
  }
  if (sent) api.invalidate("/student");
  return sent;
}

let started = false;

/** Ilova ochilganda bir marta: navbat va to'plamni internet bilan
 *  bog'laydi. */
export function startOfflineSync(lang: string) {
  if (started) {
    void refreshPack(lang);
    return;
  }
  started = true;
  const tick = () => {
    void flushQueue().then(() => refreshPack(lang));
  };
  window.addEventListener("online", tick);
  tick();
}

/** Ro'yxatdan tasodifiy n ta (takrorsiz). */
export function sample<T>(arr: T[], n: number): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, Math.max(0, n));
}
