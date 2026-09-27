import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

/**
 * MOCK — QAT'IY TARTIB (2026-09-27).
 *
 * Jahongir: "test boshlanganda bunaqa google translate boshqa boshqa
 * narsalari ishlamasligi kerak mock test faqat kompyuterda ishlanadi
 * bizda telda mumkinmas, boshqa joyga ham chiqshi mumkinmas qatiy tizim
 * bo'lishi kerak. Mock testda telefon ruxsat berilmaydi mumkinmas
 * rasmga olish ham".
 *
 * Halol chegara: veb sahifa brauzer kengaytmasini o'chira olmaydi,
 * ikkinchi telefonning kamerasini ham to'xtata olmaydi. Shuning uchun
 * SEZISH + TO'SISH + QO'RQITISH:
 *   - telefon / planshet — mock boshlanmaydi (server ham 403 qaytaradi);
 *   - test to'liq ekranda; chiqilsa — to'sib turuvchi oyna + qoidabuzarlik;
 *   - boshqa varaq, oyna, ilova (Win+Shift+S ham), PrintScreen —
 *     qoidabuzarlik; o'sha payt matn xiralashadi (skrinshotda o'qilmaydi);
 *   - kengaytma sahifaga qo'shgan narsa (Google Translate, Grammarly, AI
 *     yordamchilar) — boshlashdan oldin rad etiladi, test paytida
 *     to'sadi va qoidabuzarlik bo'ladi;
 *   - tarjima o'chiq (translate="no"), nusxa / qo'yish / chop etish /
 *     o'ng tugma / dasturchi vositalari tugmalari to'silgan;
 *   - suv belgisi (o'quvchi ismi) qoladi — telefon bilan olingan surat
 *     kimniki ekani ko'rinib turadi (2026-09-23).
 * Faqat mockda: unit / mid / end testlar avvalgidek ishlaydi.
 *
 * Qolgan chegaralar (to'sib bo'lmaydi, faqat sezish): brauzerning o'z
 * AI paneli sahifaga hech narsa qo'shmaydi — unga o'tish "oynadan
 * chiqish" bo'lib sanaladi va o'sha payt matn yashiriladi (visibility),
 * lekin kengaytmaning o'z skripti DOM'ni baribir o'qiy oladi. Firefox /
 * Safari'da Esc to'liq ekrandan chiqaradi — u sanalmaydi (keysLocked).
 * Ilova ichidagi Orqaga tugmasini to'xtatib bo'lmaydi — chiqish sanaladi.
 *
 * Ilovaning o'zi document.body ga chizadigan qatlamlari (imtihon ekrani,
 * "Belgilash" tugmasi, katta rasm, xabar oynasi, shu to'siq) data-jony-ui
 * belgisi bilan — ular kengaytma deb hisoblanmaydi.
 */

export type StrictReason =
  | "tab" | "blur" | "fullscreen" | "extension" | "printscreen" | "devtools";

const UI_ATTR = "data-jony-ui";

export const MOBILE_TITLE = "Mock test faqat kompyuterda ishlanadi";
export const MOBILE_TEXT =
  "Mock test IELTS kompyuter imtihonidagidek faqat kompyuter yoki noutbukda " +
  "ishlanadi. Telefon va planshetda ochib bo'lmaydi — shu havolani " +
  "kompyuterda oching.";
export const FRAME_TITLE = "Mock testni boshqa sayt ichida ochib bo'lmaydi";
export const FRAME_TEXT =
  "Havolani brauzerning manzil satriga qo'yib, to'g'ridan-to'g'ri oching.";
export const EXT_MSG =
  "Brauzer kengaytmalarini o'chiring (Google Translate, AI yordamchilar, ...) " +
  "va sahifani yangilang";
/** Chrome'ning o'z tarjimasi — kengaytma emas, alohida xabar. */
export const TRANSLATED = "sahifa tarjimasi";
export const TRANSLATE_MSG =
  "Chrome tarjimasini o'chiring (manzil satridagi tarjima belgisi → " +
  "\"Asl nusxa\" / \"Hech qachon tarjima qilinmasin\") va sahifani yangilang";

/** Topilgan narsalarga mos xabar (tarjima va/yoki kengaytma). */
export function foreignMsg(list: string[]): string {
  const tr = list.includes(TRANSLATED);
  const ext = list.some((x) => x !== TRANSLATED);
  if (tr && !ext) return TRANSLATE_MSG;
  if (tr) return `${EXT_MSG}. ${TRANSLATE_MSG}`;
  return EXT_MSG;
}

export const REASON_TEXT: Record<StrictReason, string> = {
  tab: "boshqa varaqqa o'tildi",
  blur: "boshqa oyna yoki ilovaga o'tildi",
  fullscreen: "to'liq ekrandan chiqildi",
  extension: "brauzer kengaytmasi aniqlandi",
  printscreen: "ekran rasmini olishga urinildi",
  devtools: "dasturchi vositalari ochildi",
};

// ------------------------------------------------------------ qurilma
const MOBILE_RE = /Android|iPhone|iPad|iPod|Mobile|Tablet|Silk|Kindle|IEMobile|Opera Mini/i;

/** Telefon yoki planshetmi. iPadOS o'zini "Macintosh" deb tanitadi —
 * sensorli nuqtalar soni bilan ajratiladi. Katta Android planshet
 * Chrome'da "kompyuter versiyasi"ni so'raydi (UA "X11; Linux", mobile
 * yo'q, ekrani 1280) — u faqat SENSORLI (sichqonchasiz) bo'lgani bilan
 * ajraladi. Sensorli noutbukda sichqoncha / sensorli panel bor
 * ("any-pointer: fine") — u to'silmaydi. */
export function isMobileDevice(): boolean {
  if (typeof navigator === "undefined") return false;
  const nav = navigator as Navigator & {
    userAgentData?: { mobile?: boolean; platform?: string };
  };
  if (nav.userAgentData?.mobile) return true;
  if (/^(android|ios)$/i.test(nav.userAgentData?.platform || "")) return true;
  const ua = nav.userAgent || "";
  if (MOBILE_RE.test(ua)) return true;
  if (/Macintosh/i.test(ua) && (nav.maxTouchPoints || 0) > 1) return true;
  try {
    const mq = (q: string) => !!window.matchMedia?.(q).matches;
    const coarse = mq("(pointer: coarse)");
    if (coarse && (window.screen?.width || 9999) < 1024) return true;
    // Faqat barmoq bilan boshqariladigan qurilma — kengligidan qat'i nazar
    if (coarse && mq("(hover: none)")) return true;
    if ((nav.maxTouchPoints || 0) > 0 && coarse && !mq("(any-pointer: fine)")) return true;
  } catch {
    /* matchMedia yo'q — UA bo'yicha qaror yetarli */
  }
  return false;
}

/** Sahifa boshqa sayt ichida (iframe) ochilganmi. U yerda to'liq ekran
 * o'chiq bo'ladi — mock boshlanmaydi (vercel.json frame-ancestors ham). */
export function isFramed(): boolean {
  try {
    return window.top !== window.self;
  } catch {
    return true;
  }
}

/** Qurilma tekshiruvi: burilganda / oyna o'zgarganda qayta. recheck() —
 * "Boshlash" bosilganda ham. */
export function useStrictEnv(watch = true) {
  const [mobile, setMobile] = useState(isMobileDevice);
  const [framed] = useState(isFramed);
  useEffect(() => {
    if (!watch) return;
    const re = () => setMobile(isMobileDevice());
    window.addEventListener("orientationchange", re);
    window.addEventListener("resize", re);
    return () => {
      window.removeEventListener("orientationchange", re);
      window.removeEventListener("resize", re);
    };
  }, [watch]);
  const recheck = useCallback(() => {
    const m = isMobileDevice();
    setMobile(m);
    return m || framed;
  }, [framed]);
  return { mobile, framed, blocked: mobile || framed, recheck };
}

// ------------------------------------------------------------ to'liq ekran
type FsDoc = Document & {
  webkitFullscreenElement?: Element | null;
  webkitFullscreenEnabled?: boolean;
  webkitExitFullscreen?: () => void;
};
type FsEl = HTMLElement & { webkitRequestFullscreen?: () => void };
type KeyboardLock = { lock?: (codes?: string[]) => Promise<void>; unlock?: () => void };

function keyboardApi(): KeyboardLock | undefined {
  return (navigator as unknown as { keyboard?: KeyboardLock }).keyboard;
}

/** Keyboard Lock haqiqatan ishladimi (faqat Chrome / Edge). Ishlasa Esc
 * to'liq ekrandan faqat BOSIB TURILGANDA chiqaradi — demak chiqish
 * ataylab, qoidabuzarlik sanaladi. Firefox / Safari'da Esc bir bosishda
 * chiqaradi (katta rasmni yoki sozlamalarni yopish uchun bosilgan Esc
 * ham) — u yerda to'liq ekrandan chiqish SANALMAYDI, faqat to'siq
 * chiqadi va test matni yashirinadi; boshqa oyna / varaqqa o'tish
 * baribir blur / visibilitychange bilan sanaladi. */
let keysLocked = false;

export function isFullscreen(): boolean {
  const d = document as FsDoc;
  return !!(d.fullscreenElement || d.webkitFullscreenElement);
}

export function fsSupported(): boolean {
  const d = document as FsDoc;
  return !!(d.fullscreenEnabled || d.webkitFullscreenEnabled);
}

/** Chrome / Edge: to'liq ekranda Esc darhol chiqarib yubormasin (bosib
 * turish kerak), Windows tugmasi (Win+Shift+S) sahifaga kelsin. Boshqa
 * brauzerlarda yo'q — jim o'tadi. */
function lockKeys() {
  try {
    const p = keyboardApi()?.lock?.(["Escape", "MetaLeft", "MetaRight", "PrintScreen"]);
    if (p)
      p.then(
        () => {
          keysLocked = true;
        },
        () => {
          keysLocked = false;
        }
      );
  } catch {
    /* Keyboard Lock yo'q */
  }
}

function unlockKeys() {
  keysLocked = false;
  try {
    keyboardApi()?.unlock?.();
  } catch {
    /* Keyboard Lock yo'q */
  }
}

/** To'liq ekranni so'raydi. Faqat foydalanuvchi bosganda (click) ishlaydi —
 * shuning uchun bosish hodisasining ichida, await'dan OLDIN chaqiriladi. */
export function requestFs(): Promise<boolean> {
  try {
    if (isFullscreen()) return Promise.resolve(true);
    if (!fsSupported()) return Promise.resolve(false);
    const el = document.documentElement as FsEl;
    const r = el.requestFullscreen
      ? el.requestFullscreen({ navigationUI: "hide" })
      : el.webkitRequestFullscreen?.();
    const asked = Promise.resolve(r).then(
      () => {
        lockKeys();
        return true;
      },
      () => false
    );
    // Ba'zi ilova ichidagi brauzerlarda (WebView) va'da hech qachon
    // tugamaydi — o'quvchi to'siq ortida qolib ketmasin: 2 s dan keyin
    // "ruxsat berilmadi" deb hisoblanadi (keyin kirsa — fullscreenchange)
    const late = new Promise<boolean>((ok) =>
      window.setTimeout(() => ok(isFullscreen()), FS_WAIT_MS)
    );
    return Promise.race([asked, late]);
  } catch {
    return Promise.resolve(false);
  }
}

export function exitFs() {
  unlockKeys();
  try {
    if (!isFullscreen()) return;
    const d = document as FsDoc;
    if (d.exitFullscreen) d.exitFullscreen().catch(() => {});
    else d.webkitExitFullscreen?.();
  } catch {
    /* chiqib bo'lmadi — muhim emas */
  }
}

// ------------------------------------------------------------ kengaytmalar
const SAFE_TAGS = new Set([
  "HEAD", "BODY", "SCRIPT", "STYLE", "LINK", "META", "NOSCRIPT", "TEMPLATE",
  "TITLE", "BASE", "VITE-ERROR-OVERLAY",
]);
// #root — React ildizi; recharts matn o'lchash uchun body ga span qo'yadi
const SAFE_IDS = new Set(["root", "recharts_measurement_span"]);
const XHTML = "http://www.w3.org/1999/xhtml";

function label(el: Element): string {
  const tag = el.tagName.toLowerCase();
  const cls = typeof el.className === "string" ? el.className : "";
  const s = `${tag} ${el.id} ${cls}`.toLowerCase();
  if (/gtx|translat/.test(s)) return "Google Translate";
  if (/grammarly/.test(s)) return "Grammarly";
  if (/monica/.test(s)) return "Monica";
  if (/sider/.test(s)) return "Sider";
  if (/merlin/.test(s)) return "Merlin";
  if (/maxai|max-ai/.test(s)) return "MaxAI";
  if (/quillbot/.test(s)) return "QuillBot";
  if (/deepl/.test(s)) return "DeepL";
  if (/lastpass|bitwarden|1password|dashlane/.test(s)) return "parol menejeri";
  if (tag === "font") return TRANSLATED;
  return `noma'lum kengaytma (${tag}${el.id ? "#" + el.id : ""})`;
}

/** body / html ning bevosita bolasi: bizniki bo'lmasa — begona. */
function topForeign(el: Element): boolean {
  if (el.hasAttribute(UI_ATTR)) return false;
  if (SAFE_TAGS.has(el.tagName.toUpperCase())) return false;
  if (SAFE_IDS.has(el.id)) return false;
  return true;
}

/** Chuqurda (bizning ildizlar ichida): ilova hech qachon chizmaydigan
 * belgilar — custom element (nomida "-"), gtx-* (Google Translate),
 * ochiq shadow-root egasi. */
function nestedForeign(el: Element): boolean {
  if (el.namespaceURI !== XHTML) return false;
  return (
    el.tagName.includes("-") ||
    /^gtx-/i.test(el.id) ||
    !!el.shadowRoot ||
    el.hasAttribute("data-grammarly-shadow-root")
  );
}

/** Sahifadagi begona (kengaytma qo'shgan) narsalar ro'yxati.
 *
 * Tarjimaning <font> o'ramlari faqat IMTIHON qatlamlari (data-jony-ui)
 * ichida qidiriladi: xodim menyusi (#root) Chrome'ning "doim tarjima
 * qil" sozlamasi bilan mock sahifasiga o'tishdan OLDIN tarjima qilingan
 * bo'lishi mumkin — React u matnlarni qayta chizmaydi, <font> abadiy
 * qoladi va test hech qachon boshlanmasdi (2026-09-27 ko'rigi). Tarjima
 * endi sahifa ochilishi bilan o'chiriladi (useNoTranslate), imtihon
 * matni tarjima qilinsa — shu yerda ko'rinadi. */
export function scanForeign(): string[] {
  const html = document.documentElement;
  const body = document.body;
  if (!html || !body) return [];
  const found = new Set<string>();
  for (const el of Array.from(html.children)) {
    if (el === body || el === document.head) continue;
    if (topForeign(el)) found.add(label(el));
  }
  for (const el of Array.from(body.children)) {
    if (topForeign(el)) found.add(label(el));
    else if (el.hasAttribute(UI_ATTR) && el.getElementsByTagName("font").length)
      found.add(TRANSLATED);
  }
  for (const el of Array.from(body.getElementsByTagName("*"))) {
    if (nestedForeign(el)) found.add(label(el));
  }
  return Array.from(found).sort();
}

function sameList(a: string[], b: string[]) {
  return a.length === b.length && a.every((x, i) => x === b[i]);
}

/**
 * Kengaytmalarni kuzatish. foreign — hozir sahifada turganlari; seen —
 * shu sahifa ochilgandan beri ko'rilganlari (boshlashdan oldingi
 * tekshiruv uchun: Google Translate belgisi tanlov yo'qolganda
 * olib tashlanadi, lekin kengaytma baribir yoqilgan).
 */
export function useForeignNodes(enabled: boolean) {
  const [foreign, setForeign] = useState<string[]>([]);
  const [seen, setSeen] = useState<string[]>([]);

  const rescan = useCallback(() => {
    const f = scanForeign();
    setForeign((prev) => (sameList(prev, f) ? prev : f));
    if (f.length)
      setSeen((prev) => {
        const u = Array.from(new Set([...prev, ...f])).sort();
        return sameList(prev, u) ? prev : u;
      });
    return f;
  }, []);

  useEffect(() => {
    if (!enabled) return;
    rescan();
    let t = 0;
    const later = () => {
      window.clearTimeout(t);
      t = window.setTimeout(rescan, 200);
    };
    const mo = new MutationObserver((recs) => {
      for (const r of recs) {
        if (r.addedNodes.length || r.removedNodes.length) {
          later();
          return;
        }
      }
    });
    mo.observe(document.documentElement, { childList: true });
    if (document.body) mo.observe(document.body, { childList: true, subtree: true });
    // Kengaytmalar sahifa yuklangandan keyin kechroq qo'shadi
    const t1 = window.setTimeout(rescan, 1500);
    const iv = window.setInterval(rescan, 4000);
    return () => {
      mo.disconnect();
      window.clearTimeout(t);
      window.clearTimeout(t1);
      window.clearInterval(iv);
    };
  }, [enabled, rescan]);

  return {
    foreign: enabled ? foreign : [],
    seen: enabled ? seen : [],
    rescan,
  };
}

/** Sahifa tarjimasini o'chiradi (Chrome'ning o'zi ham, "Tarjima qilish"
 * taklifi ham): <html translate="no" class="notranslate"> va
 * <meta name="google" content="notranslate">. Chiqqanda qaytariladi.
 * Bir nechta joy bir vaqtda yoqishi mumkin (sahifa ochilishi bilan +
 * nazorat) — oxirgisi o'chganda qaytariladi. Mock sahifalari buni
 * OCHILISHI BILAN yoqadi: Chrome sahifani tarjima qilib ulgurmasin. */
const noTr = { n: 0, prev: null as string | null, had: false, meta: null as HTMLMetaElement | null };

export function useNoTranslate(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    const html = document.documentElement;
    if (noTr.n++ === 0) {
      noTr.prev = html.getAttribute("translate");
      noTr.had = html.classList.contains("notranslate");
      html.setAttribute("translate", "no");
      html.classList.add("notranslate");
      const meta = document.createElement("meta");
      meta.name = "google";
      meta.content = "notranslate";
      meta.setAttribute(UI_ATTR, "");
      document.head.appendChild(meta);
      noTr.meta = meta;
    }
    return () => {
      if (--noTr.n > 0) return;
      if (noTr.prev === null) html.removeAttribute("translate");
      else html.setAttribute("translate", noTr.prev);
      if (!noTr.had) html.classList.remove("notranslate");
      noTr.meta?.remove();
      noTr.meta = null;
    };
  }, [enabled]);
}

// ------------------------------------------------------------ nazorat
/** Bitta chiqish. sent — serverga allaqachon yuborilgan soniyalar
 * (10 soniyada qayd qilinib, o'quvchi keyinroq qaytsa qolgani
 * "extend" bilan yuboriladi). nav — imtihon sahifasidan ilova ichida
 * boshqa sahifaga o'tildi (Orqaga / Alt+←). */
type Episode = {
  since: number;
  reason: StrictReason;
  reported: boolean;
  eid: string;
  sent: number;
  nav?: boolean;
};

/** Serverga yuboriladigan hodisa. eid — takror yuborilsa ikki marta
 * sanalmasin; extend — o'sha chiqishning davomi (faqat soniyalar). */
export type Violation = {
  eid: string;
  reason: StrictReason;
  seconds: number;
  extend: boolean;
};

const CAP_MS = 10_000;         // qaytmasa ham 10 soniyada qayd qilinadi
const PRINT_MS = 1_500;        // PrintScreen'da matn shuncha xira turadi
const FS_WAIT_MS = 2_000;      // to'liq ekran javobini shuncha kutadi

function newEid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function secsOf(e: Episode): number {
  return Math.max(0, Math.round((Date.now() - e.since) / 1000));
}

/** Qaysi nazoratlar hozir sahifada turibdi (storageKey bo'yicha) — React
 * StrictMode'ning sinov uchun "o'chirib-yoqishi"ni haqiqiy chiqishdan
 * ajratish uchun. */
const LIVE = new Map<string, number>();

function wipeClipboard() {
  try {
    navigator.clipboard?.writeText(" ").catch(() => {});
  } catch {
    /* ruxsat yo'q — muhim emas */
  }
}

/**
 * Qat'iy tartib nazorati.
 *   enabled — sahifa qat'iy (mock): tarjima o'chadi, kengaytmalar
 *     kuzatiladi (boshlashdan oldin ham);
 *   active  — test ketyapti: chiqishlar sanaladi, tugmalar to'siladi.
 * Bir "chiqish" (blur + visibilitychange juftligi, to'liq ekrandan
 * chiqish, kengaytma, PrintScreen) — BITTA qoidabuzarlik. U qaytilganda
 * (yoki 10 soniyadan keyin) onViolation({eid, reason, seconds}) bilan
 * bir marta xabar qilinadi; 10 soniyadan keyin qaytsa, qolgan vaqti
 * extend: true bilan (sanalmaydi, faqat soniya). Sahifa yangilansa ham,
 * ilova ichida boshqa sahifaga o'tib qaytilsa ham yo'qolmaydi
 * (localStorage).
 */
export function useStrictGuard({
  enabled,
  active,
  storageKey,
  onViolation,
}: {
  enabled: boolean;
  active: boolean;
  storageKey: string;
  onViolation: (v: Violation) => void;
}) {
  const { foreign, seen, rescan } = useForeignNodes(enabled);
  useNoTranslate(enabled);
  const on = enabled && active;

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [fsOn, setFsOn] = useState(() => isFullscreen());
  const [fsRefused, setFsRefused] = useState(() => !fsSupported());

  const epRef = useRef<Episode | null>(null);
  const onRef = useRef(false);
  const wasOn = useRef(false);
  const foreignRef = useRef<string[]>([]);
  const refusedRef = useRef(fsRefused);
  const cbRef = useRef(onViolation);
  const ignoreUntil = useRef(0);
  const capTimer = useRef(0);
  const pKey = `${storageKey}:strict-away`;
  const pKeyRef = useRef(pKey);
  pKeyRef.current = pKey;

  useEffect(() => {
    cbRef.current = onViolation;
  });

  const persist = useCallback(
    (e: Episode | null) => {
      try {
        if (e) localStorage.setItem(pKey, JSON.stringify(e));
        else localStorage.removeItem(pKey);
      } catch {
        /* maxfiy oyna — xotirada qoladi */
      }
    },
    [pKey]
  );

  const report = useCallback(() => {
    const e = epRef.current;
    if (!e || e.reported) return;
    const seconds = secsOf(e);
    e.reported = true;
    e.sent = seconds;
    persist(e);
    cbRef.current({ eid: e.eid, reason: e.reason, seconds, extend: false });
  }, [persist]);

  const tryEnd = useCallback(() => {
    const e = epRef.current;
    if (!e) return;
    if (document.hidden || !document.hasFocus()) return;
    if (!refusedRef.current && fsSupported() && !isFullscreen()) return;
    if (foreignRef.current.length) return;
    if (e.reason === "printscreen" && Date.now() - e.since < PRINT_MS) return;
    if (e.reported) {
      // 10 soniyada qayd qilingan edi — qolgan vaqti ham examinerga
      // ko'rinsin (15 daqiqalik chiqish "10 s" bo'lib qolmasin)
      const rest = secsOf(e) - (e.sent || 0);
      if (rest > 0)
        cbRef.current({ eid: `${e.eid}+`, reason: e.reason, seconds: rest, extend: true });
    } else report();
    epRef.current = null;
    persist(null);
    window.clearTimeout(capTimer.current);
    setEpisode(null);
  }, [persist, report]);

  const begin = useCallback(
    (reason: StrictReason) => {
      if (!onRef.current) return;
      const now = Date.now();
      if (now < ignoreUntil.current) return;
      const cur = epRef.current;
      if (cur) {
        // blur va visibilitychange bir chiqishning ikki hodisasi —
        // aniqrog'i (varaq almashtirildi) yoziladi, soni oshmaydi
        if (cur.reason === "blur" && reason === "tab" && !cur.reported && now - cur.since < 1500) {
          cur.reason = "tab";
          persist(cur);
          setEpisode({ ...cur });
        }
        return;
      }
      const e: Episode = { since: now, reason, reported: false, eid: newEid(), sent: 0 };
      epRef.current = e;
      // Darhol (React chizishini kutmay) — ekran rasmida matn o'qilmasin
      document.documentElement.classList.add("jony-away");
      persist(e);
      setEpisode({ ...e });
      window.clearTimeout(capTimer.current);
      capTimer.current = window.setTimeout(report, CAP_MS);
    },
    [persist, report]
  );

  // Test boshlandi / tugadi. Yangilangan sahifada tugallanmagan chiqish
  // bo'lsa — davom ettiriladi (qayta sanalmaydi, yo'qolmaydi ham).
  useEffect(() => {
    onRef.current = on;
    if (on) {
      let saved: Episode | null = null;
      try {
        saved = JSON.parse(localStorage.getItem(pKey) || "null");
      } catch {
        saved = null;
      }
      if (saved && saved.nav && !saved.reported) {
        // Sahifadan "chiqish" React StrictMode'ning sinovi edi (haqiqiy
        // chiqishda u bir lahzada qayd qilinadi — pastdagi tozalashga q.)
        persist(null);
        saved = null;
      }
      if (
        saved && !epRef.current && typeof saved.since === "number" &&
        Date.now() - saved.since < 6 * 3600_000 && REASON_TEXT[saved.reason]
      ) {
        const e: Episode = {
          since: saved.since,
          reason: saved.reason,
          reported: !!saved.reported,
          eid: typeof saved.eid === "string" && saved.eid ? saved.eid : newEid(),
          sent: Number(saved.sent) || 0,
        };
        epRef.current = e;
        document.documentElement.classList.add("jony-away");
        setEpisode({ ...e });
        if (!e.reported)
          capTimer.current = window.setTimeout(
            report,
            Math.max(0, CAP_MS - (Date.now() - e.since))
          );
      }
    } else if (wasOn.current) {
      // Topshirildi / chetlatildi — to'siq olinadi, to'liq ekrandan chiqadi
      epRef.current = null;
      persist(null);
      window.clearTimeout(capTimer.current);
      setEpisode(null);
      exitFs();
    }
    wasOn.current = on;
  }, [on, pKey, persist, report]);

  // Kengaytma paydo bo'ldi / yo'qoldi
  useEffect(() => {
    foreignRef.current = foreign;
    if (!on) return;
    if (foreign.length) begin("extension");
    else tryEnd();
  }, [foreign, on, begin, tryEnd]);

  // To'liq ekran holati (kutish paytida ham kuzatiladi)
  useEffect(() => {
    if (!enabled) return;
    const onFs = () => {
      const f = isFullscreen();
      setFsOn(f);
      if (f) {
        lockKeys();
        tryEnd();
      } else if (onRef.current && !refusedRef.current && keysLocked) {
        // Faqat Keyboard Lock ishlaganda (Esc bosib turilgan — ataylab).
        // Aks holda to'siq baribir chiqadi (needFs), matn yashirinadi,
        // lekin sanalmaydi — keysLocked izohiga qarang
        begin("fullscreen");
      }
    };
    document.addEventListener("fullscreenchange", onFs);
    document.addEventListener("webkitfullscreenchange", onFs);
    return () => {
      document.removeEventListener("fullscreenchange", onFs);
      document.removeEventListener("webkitfullscreenchange", onFs);
    };
  }, [enabled, begin, tryEnd]);

  // Chiqish, qaytish, tugmalar, bufer, chop etish — faqat test paytida
  useEffect(() => {
    if (!on) return;
    const onVis = () => {
      if (document.hidden) begin("tab");
      else tryEnd();
    };
    const onBlur = () => begin("blur");
    const onFocus = () => tryEnd();
    const onKey = (e: KeyboardEvent) => {
      const k = (e.key || "").toLowerCase();
      const letter = e.code?.startsWith("Key") ? e.code.slice(3).toLowerCase() : k;
      const mod = e.ctrlKey || e.metaKey;
      const bad =
        k === "f12" ||
        k === "printscreen" ||
        (mod && e.shiftKey && ["i", "j", "c", "k"].includes(letter)) ||
        (e.metaKey && e.altKey && ["i", "j", "c", "u"].includes(letter)) ||
        (mod && ["c", "x", "v", "p", "s", "u", "a"].includes(letter)) ||
        // Orqaga / oldinga (ilova ichidagi imtihonda sahifadan chiqarardi)
        (e.altKey && (k === "arrowleft" || k === "arrowright")) ||
        k === "browserback" ||
        k === "browserforward";
      if (bad) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    // Sichqonchaning "orqaga / oldinga" tugmalari (Chrome / Edge'da
    // to'xtatiladi; boshqalarida chiqilsa — pastdagi tozalash sanaydi)
    const onMouse = (e: MouseEvent) => {
      if (e.button === 3 || e.button === 4) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.key !== "PrintScreen") return;
      begin("printscreen");
      wipeClipboard();
      window.setTimeout(tryEnd, PRINT_MS + 100);
    };
    const stop = (e: Event) => e.preventDefault();
    const blocked = ["copy", "cut", "paste", "contextmenu", "dragstart", "drop"];
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("blur", onBlur);
    window.addEventListener("focus", onFocus);
    window.addEventListener("keydown", onKey, true);
    window.addEventListener("keyup", onKeyUp, true);
    window.addEventListener("mousedown", onMouse, true);
    window.addEventListener("mouseup", onMouse, true);
    blocked.forEach((n) => document.addEventListener(n, stop, true));
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("blur", onBlur);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("keyup", onKeyUp, true);
      window.removeEventListener("mousedown", onMouse, true);
      window.removeEventListener("mouseup", onMouse, true);
      blocked.forEach((n) => document.removeEventListener(n, stop, true));
    };
  }, [on, begin, tryEnd]);

  // Chop etish: menyudan bosilsa ham imtihon qog'ozga chiqmaydi
  useEffect(() => {
    if (!enabled) return;
    const html = document.documentElement;
    html.classList.add("jony-strict");
    const before = () => html.classList.add("jony-noprint");
    const after = () => html.classList.remove("jony-noprint");
    window.addEventListener("beforeprint", before);
    window.addEventListener("afterprint", after);
    return () => {
      window.removeEventListener("beforeprint", before);
      window.removeEventListener("afterprint", after);
      after();
      html.classList.remove("jony-strict");
    };
  }, [enabled]);

  // Chiqish davom etayotganda har soniyada qaytganini tekshiradi
  // (focus hodisasi kelmay qolgan holatlar uchun)
  useEffect(() => {
    if (!episode) return;
    const iv = window.setInterval(tryEnd, 1000);
    return () => window.clearInterval(iv);
  }, [episode, tryEnd]);

  const needFs = on && !fsRefused && !fsOn;
  const blocked = on && (!!episode || needFs || foreign.length > 0);

  useEffect(() => {
    const html = document.documentElement;
    if (blocked) html.classList.add("jony-away");
    else html.classList.remove("jony-away");
  }, [blocked]);

  // Sahifadan ketganda: xiralik, tugmalar qulfi, to'liq ekran olinadi.
  // Test KETAYOTGANDA ketilsa (Jony Student ichida Orqaga / Alt+← —
  // sahifa yopilmaydi, blur ham, visibilitychange ham kelmaydi) — bu
  // ham chiqish: darhol qayd qilinadi, qaytilsa o'sha chiqish davom
  // etadi va tugaganda qolgan vaqti yuboriladi (2026-09-27 ko'rigi).
  useEffect(() => {
    const k0 = pKeyRef.current;
    LIVE.set(k0, (LIVE.get(k0) || 0) + 1);
    return () => {
      const k = pKeyRef.current;
      LIVE.set(k, Math.max(0, (LIVE.get(k) || 1) - 1));
      window.clearTimeout(capTimer.current);
      document.documentElement.classList.remove("jony-away");
      if (wasOn.current) exitFs();
      if (!onRef.current) return;
      // epRef ga yozilmaydi: StrictMode qayta o'rnatganda ref'lar
      // saqlanadi, "ochiq chiqish" qolib ketib keyingilarini yutardi
      const ep: Episode = epRef.current ?? {
        since: Date.now(), reason: "tab", reported: false, eid: newEid(), sent: 0, nav: true,
      };
      const cb = cbRef.current;
      const save = (x: Episode) => {
        try {
          localStorage.setItem(k, JSON.stringify(x));
        } catch {
          /* maxfiy oyna */
        }
      };
      save(ep);
      // StrictMode (faqat ishlab chiqishda) shu zahoti qayta o'rnatadi —
      // unda hech narsa yuborilmaydi; haqiqiy chiqishda yuboriladi
      window.setTimeout(() => {
        if (LIVE.get(k) || ep.reported) return;
        const seconds = secsOf(ep);
        ep.reported = true;
        ep.sent = seconds;
        save(ep);
        cb({ eid: ep.eid, reason: ep.reason, seconds, extend: false });
      }, 0);
    };
  }, []);

  /** To'liq ekranga o'tish / testga qaytish (tugma bosilganda). */
  const enterFs = useCallback(() => {
    try {
      window.focus();
    } catch {
      /* fokus berib bo'lmadi */
    }
    ignoreUntil.current = Date.now() + 600;
    if (refusedRef.current || !fsSupported()) {
      tryEnd();
      return;
    }
    requestFs().then((ok) => {
      if (!ok) {
        // Brauzer ruxsat bermadi — test oddiy oynada davom etadi,
        // hech narsa sanalmaydi
        refusedRef.current = true;
        setFsRefused(true);
      }
      setFsOn(isFullscreen());
      tryEnd();
    });
  }, [tryEnd]);

  /** confirm() oynasi ochilganda oyna "blur" bo'ladi — qoidabuzarlik emas. */
  const confirmSafe = useCallback((msg: string) => {
    ignoreUntil.current = Date.now() + 3600_000;
    try {
      return window.confirm(msg);
    } finally {
      ignoreUntil.current = Date.now() + 600;
    }
  }, []);

  return {
    on,
    blocked,
    reason: episode?.reason ?? null,
    foreign,
    seen,
    rescan,
    needFs,
    fsOn,
    fsRefused,
    enterFs,
    confirmSafe,
  };
}

export type StrictGuard = ReturnType<typeof useStrictGuard>;

// ------------------------------------------------------------ ko'rinish
/** Test ustidagi to'siq: kengaytma / chiqish / to'liq ekran. */
export function StrictOverlay({ guard, info }: { guard: StrictGuard; info?: ReactNode }) {
  if (!guard.blocked) return null;
  let icon = "⛶";
  let title = "Test to'liq ekranda ishlanadi";
  let text: ReactNode =
    "Davom etish uchun tugmani bosing. To'liq ekrandan chiqish, boshqa " +
    "varaq, oyna yoki ilovaga o'tish qoidabuzarlik hisoblanadi.";
  let button: ReactNode = (
    <button
      type="button"
      autoFocus
      onClick={guard.enterFs}
      className="w-full mt-4 bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand-500"
    >
      {guard.needFs ? "To'liq ekranga o'tish" : "Testga qaytish"}
    </button>
  );
  if (guard.foreign.length) {
    const onlyTr = guard.foreign.every((x) => x === TRANSLATED);
    icon = onlyTr ? "🌐" : "🧩";
    title = onlyTr ? "Sahifa tarjima qilingan" : "Brauzer kengaytmasi aniqlandi";
    text = (
      <>
        <span className="block font-medium text-slate-800">
          Topildi: {guard.foreign.join(", ")}
        </span>
        <span className="block mt-2">
          {foreignMsg(guard.foreign)} (F5). Javoblaringiz saqlangan. Bu
          qoidabuzarlik sifatida qayd qilindi.
        </span>
      </>
    );
    button = (
      <div className="mt-4 grid gap-2">
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold"
        >
          Sahifani yangilash
        </button>
        <button
          type="button"
          onClick={() => guard.rescan()}
          className="w-full border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-xl py-2.5 text-sm font-semibold"
        >
          Qayta tekshirish
        </button>
      </div>
    );
  } else if (guard.reason) {
    icon = "⚠️";
    title =
      guard.reason === "fullscreen"
        ? "Siz to'liq ekrandan chiqdingiz"
        : guard.reason === "printscreen"
          ? "Ekran rasmini olish taqiqlangan"
          : "Siz test oynasidan chiqdingiz";
    text =
      `Qoidabuzarlik qayd qilindi (${REASON_TEXT[guard.reason]}). ` +
      "Test paytida boshqa varaq, oyna yoki ilovaga o'tish, to'liq ekrandan " +
      "chiqish va ekran rasmini olish mumkin emas.";
    if (guard.needFs)
      button = (
        <button
          type="button"
          autoFocus
          onClick={guard.enterFs}
          className="w-full mt-4 bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold"
        >
          To'liq ekranga qaytish
        </button>
      );
  }
  return createPortal(
    <div
      data-jony-ui="guard"
      role="alertdialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 p-4"
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-6 text-center shadow-2xl">
        <p className="text-4xl mb-2" aria-hidden>
          {icon}
        </p>
        <h2 className="text-lg font-bold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-600 mt-2">{text}</p>
        {info ? (
          <p className="text-sm font-medium text-amber-800 bg-amber-50 rounded-lg px-3 py-2 mt-3">
            {info}
          </p>
        ) : null}
        {button}
      </div>
    </div>,
    document.body
  );
}

/** Telefon / planshet (yoki boshqa sayt ichida ochilgan) uchun to'siq. */
export function MobileBlock({ framed = false }: { framed?: boolean }) {
  return (
    <div className="text-center">
      <p className="text-4xl mb-2" aria-hidden>
        💻
      </p>
      <h1 className="text-lg font-bold text-slate-900 mb-1">
        {framed ? FRAME_TITLE : MOBILE_TITLE}
      </h1>
      <p className="text-sm text-slate-600">{framed ? FRAME_TEXT : MOBILE_TEXT}</p>
    </div>
  );
}

/**
 * Boshlashdan oldingi kengaytma sinovi. Ba'zi kengaytmalar (Google
 * Translate) faqat matn tanlanganda sahifaga belgi qo'shadi — shu
 * jumla bir lahzaga tanlanadi, belgi paydo bo'lsa seen ga tushadi.
 */
export function ExtensionProbe() {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    let t = 0;
    const t0 = window.setTimeout(() => {
      const el = ref.current;
      try {
        const sel = window.getSelection();
        if (!el || !sel || !sel.isCollapsed) return;
        const r = document.createRange();
        r.selectNodeContents(el);
        sel.removeAllRanges();
        sel.addRange(r);
        const b = el.getBoundingClientRect();
        el.dispatchEvent(
          new MouseEvent("mouseup", {
            bubbles: true,
            cancelable: true,
            view: window,
            button: 0,
            clientX: b.left + b.width / 2,
            clientY: b.top + b.height / 2,
          })
        );
        t = window.setTimeout(() => {
          try {
            if (sel.anchorNode && el.contains(sel.anchorNode)) sel.removeAllRanges();
          } catch {
            /* tanlovni tozalab bo'lmadi */
          }
        }, 1200);
      } catch {
        /* sinab bo'lmadi — oddiy kuzatuv baribir ishlaydi */
      }
    }, 700);
    return () => {
      window.clearTimeout(t0);
      window.clearTimeout(t);
    };
  }, []);
  return (
    <span ref={ref} lang="en" className="block text-[11px] text-slate-400 mt-2">
      Browser check: this sentence helps us detect translation extensions.
    </span>
  );
}

/** Mock qoidalari — boshlashdan oldin (o'quvchi va xodim uchun). */
export function StrictRules({
  limit,
  staff = false,
}: {
  limit?: number | null;
  staff?: boolean;
}) {
  const n = limit && limit > 0 ? limit : null;
  return (
    <div className="text-left rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs text-slate-600">
      <p className="font-semibold text-slate-800 mb-1">Mock test qoidalari</p>
      <ul className="list-disc pl-4 space-y-0.5">
        <li>Faqat kompyuterda, to'liq ekranda ishlanadi.</li>
        <li>
          Boshqa varaq, oyna yoki ilovaga o'tish, to'liq ekrandan chiqish, ekran
          rasmini olish — qoidabuzarlik.
          {staff
            ? " 3-qoidabuzarlikda urinish avtomatik topshiriladi."
            : n
              ? ` ${n + 1}-qoidabuzarlikda testdan chetlatilasiz.`
              : " Ko'p takrorlansa testdan chetlatilasiz."}
        </li>
        <li>Nusxa olish, qo'yish, chop etish va tarjima o'chirilgan.</li>
        <li>
          Brauzer kengaytmalari (Google Translate, Grammarly, AI yordamchilar)
          o'chirilgan bo'lishi shart. Brauzerning o'zidagi AI yordamchi
          (masalan, yon paneldagi) ham taqiqlanadi: sahifa uni har doim ham
          sezolmaydi, lekin unga o'tilsa — oynadan chiqish sifatida sanaladi,
          o'sha paytda test matni yashiriladi.
        </li>
        {!staff ? (
          <li>
            Telefon bilan rasmga olish taqiqlanadi: ekranda ismingiz yozilgan —
            har qanday surat kimdan chiqqani ko'rinadi.
          </li>
        ) : null}
      </ul>
    </div>
  );
}

/** Kengaytma topilgan bo'lsa — boshlashdan oldingi ogohlantirish. */
export function ExtensionWarning({ list }: { list: string[] }) {
  if (!list.length) return null;
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 text-left">
      <p className="font-semibold">{foreignMsg(list)}.</p>
      <p className="text-xs mt-1">Topildi: {list.join(", ")}</p>
    </div>
  );
}
