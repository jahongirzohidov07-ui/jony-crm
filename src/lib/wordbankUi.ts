import {
  CERT_MAX_BYTES,
  CERT_RULES,
  type CertExamType,
  type CertForm,
  type StaffCert,
} from "./wordbankApi";

/**
 * SO'Z BILISH — ekran uchun kichik yordamchilar (2026-10-17).
 *
 * wordbankApi.ts — server bilan shartnoma (turlar va chaqiruvlar), u
 * yerga tegilmaydi. Bu faylda faqat brauzer tomoni: tanlangan tablarni
 * eslab qolish, sertifikat formasi tekshiruvi (server ham AYNAN shu
 * qoidani tekshiradi — bu yerda faqat o'quvchi xatoni darrov ko'rsin)
 * va rasmni yuborishdan oldin kichraytirish.
 */

// ------------------------------------------------ tanlovni eslash ---
/**
 * localStorage — faqat qulaylik uchun (oxirgi tanlangan tab). Shaxsiy
 * oynada, tozalangan saytda yoki WebView'da xato berishi mumkin —
 * shuning uchun har chaqiruv try/catch ichida va xato jim o'tadi.
 */
export function readPref(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writePref(key: string, value: string | null) {
  try {
    if (value === null || value === "") window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch {
    /* saqlab bo'lmadi — keyingi safar standart tab ochiladi */
  }
}

/** Saqlangan qiymat ro'yxatda bo'lsa — o'zi, aks holda standart. */
export function pickPref<T extends string>(
  key: string,
  allowed: readonly T[],
  fallback: T,
): T {
  const v = readPref(key);
  return v && (allowed as readonly string[]).includes(v) ? (v as T) : fallback;
}

// -------------------------------------------------------- sanalar ---
/** Toshkent bugungi sanasi (UTC+5) — "YYYY-MM-DD". */
export function tashkentToday(): string {
  return new Date(Date.now() + 5 * 3600_000).toISOString().slice(0, 10);
}

/** Test sanasi 5 yildan eski bo'lmasin (server: MAX_AGE_YEARS). */
export function certMinDate(): string {
  const t = tashkentToday();
  const y = Number(t.slice(0, 4)) - 5;
  const md = t.slice(5) === "02-29" ? "03-01" : t.slice(5);
  return `${y}-${md}`;
}

export function fmtBytes(n: number | null | undefined): string {
  const b = Number(n || 0);
  if (b >= 1024 * 1024) return `${(b / 1024 / 1024).toFixed(1)} MB`;
  if (b >= 1024) return `${Math.round(b / 1024)} KB`;
  return `${b} B`;
}

// ------------------------------------------- sertifikat formasi ---
export const SUB_LABELS: Record<string, string> = {
  L: "Listening",
  R: "Reading",
  W: "Writing",
  S: "Speaking",
};

/** Forma maydonlari — kiritish paytida matn holida. */
export type CertDraft = {
  exam_type: CertExamType;
  exam_name: string;
  score: string;
  level: string;
  subs: Record<string, string>;
  test_date: string;
  cert_no: string;
};

export function emptyDraft(exam_type: CertExamType = "ielts"): CertDraft {
  return {
    exam_type,
    exam_name: "",
    score: "",
    level: "",
    subs: {},
    test_date: "",
    cert_no: "",
  };
}

/** Xodim navbatidagi yozuvdan tahrirlanadigan forma (xodim ballni ko'radi). */
export function draftFromStaff(c: StaffCert): CertDraft {
  const subs: Record<string, string> = {};
  for (const [k, v] of Object.entries(c.sub_scores || {})) {
    if (v !== null && v !== undefined) subs[k] = String(v);
  }
  return {
    exam_type: c.exam_type,
    exam_name: c.exam_name || "",
    score: c.score === null || c.score === undefined ? "" : String(c.score),
    level: c.level || "",
    subs,
    test_date: c.test_date || "",
    cert_no: c.cert_no || "",
  };
}

export function scoreLabel(t: CertExamType): string {
  const r = CERT_RULES[t].score;
  if (!r) return "Ball";
  if (t === "ielts") return "Umumiy ball (Overall Band)";
  if (t === "cambridge") return "Cambridge English Scale (80–230)";
  return `Ball (${r.min}–${r.max})`;
}

export function levelLabel(t: CertExamType): string {
  if (t === "topik") return "TOPIK darajasi (1–6)";
  if (t === "other") return "Natija";
  return "Daraja (CEFR)";
}

export function examNameLabel(t: CertExamType): string {
  if (t === "cambridge") return "Imtihon";
  if (t === "cefr_other") return "Imtihon nomi (ixtiyoriy)";
  return "Imtihon nomi";
}

function num(s: string): number | null {
  const t = (s || "").trim().replace(",", ".");
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : NaN;
}

function onStep(x: number, step: number): boolean {
  const k = x / step;
  return Math.abs(k - Math.round(k)) < 1e-9;
}

/**
 * Formani tekshiradi va serverga yuboriladigan ko'rinishga keltiradi.
 * Bu turdagi imtihonda ishlatilmaydigan maydonlar null bo'ladi (server
 * ham ularni saqlamaydi). Xato bo'lsa — o'zbekcha matn.
 */
export function draftToForm(
  d: CertDraft,
): { form: CertForm; error: null } | { form: null; error: string } {
  const rule = CERT_RULES[d.exam_type];
  if (!rule) return { form: null, error: "Imtihon turini tanlang" };
  const fail = (error: string) => ({ form: null, error }) as const;

  let exam_name: string | null = null;
  if (rule.exam_name) {
    const v = d.exam_name.trim();
    if (rule.exam_name.options) {
      if (!v || !rule.exam_name.options.includes(v)) {
        if (rule.exam_name.required) return fail("Imtihonni tanlang");
      } else exam_name = v;
    } else {
      if (!v && rule.exam_name.required) return fail("Imtihon nomini yozing");
      if (rule.exam_name.maxLen && v.length > rule.exam_name.maxLen)
        return fail(`Imtihon nomi ${rule.exam_name.maxLen} belgidan oshmasin`);
      exam_name = v || null;
    }
  }

  let level: string | null = null;
  if (rule.level) {
    const v = d.level.trim();
    if (rule.level.options) {
      if (!v || !rule.level.options.includes(v)) {
        if (rule.level.required) return fail("Darajani tanlang");
      } else level = v;
    } else {
      if (!v && rule.level.required) return fail("Natijani yozing");
      if (rule.level.maxLen && v.length > rule.level.maxLen)
        return fail(`Natija ${rule.level.maxLen} belgidan oshmasin`);
      level = v || null;
    }
  }

  let score: number | null = null;
  if (rule.score) {
    const r = rule.score;
    const n = num(d.score);
    if (n === null) {
      if (r.required) return fail("Ballni kiriting");
    } else if (Number.isNaN(n)) {
      return fail("Ball son bo'lsin");
    } else {
      if (n < r.min || n > r.max)
        return fail(`Ball ${r.min} dan ${r.max} gacha bo'lsin`);
      if (!onStep(n, r.step))
        return fail(
          r.step === 1
            ? "Ball butun son bo'lsin"
            : r.step < 1
              ? `Ball ${r.step} qadam bilan bo'lsin (masalan 6.5 yoki 7.0)`
              : `Ball ${r.step} ga karrali bo'lsin`,
        );
      score = n;
    }
  }

  let sub_scores: Record<string, number> | null = null;
  if (rule.sub_scores) {
    const out: Record<string, number> = {};
    for (const k of rule.sub_scores) {
      const n = num(d.subs[k] || "");
      if (n === null) continue;
      if (Number.isNaN(n) || n < 0 || n > 9 || !onStep(n, 0.5))
        return fail(`${SUB_LABELS[k] || k} bali 0 dan 9 gacha, 0.5 qadam bilan`);
      out[k] = n;
    }
    sub_scores = Object.keys(out).length ? out : null;
  }

  const test_date = d.test_date.trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(test_date)) return fail("Test sanasini kiriting");
  if (test_date > tashkentToday())
    return fail("Test sanasi kelajakda bo'lishi mumkin emas");
  if (test_date < certMinDate()) return fail("Test sanasi 5 yildan eski bo'lmasin");

  const cert_no = d.cert_no.trim();
  if (cert_no.length > 40) return fail("Sertifikat raqami 40 belgidan oshmasin");

  return {
    form: {
      exam_type: d.exam_type,
      exam_name,
      score,
      level,
      sub_scores,
      test_date,
      cert_no: cert_no || null,
    },
    error: null,
  };
}

// ------------------------------------------------- fayl tayyorlash ---
const MAX_SIDE = 2000;

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Rasmni o'qib bo'lmadi — JPG yoki PNG formatida yuklang"));
    };
    img.src = url;
  });
}

function encode(img: HTMLImageElement, side: number, q: number): Promise<Blob | null> {
  // Canvas / xotira cheklovi (kuchsiz WebView) — xato emas, null:
  // chaqiruvchi asl faylga qaytadi (2026-10-17, review)
  try {
    const w = img.naturalWidth || img.width;
    const h = img.naturalHeight || img.height;
    const k = Math.min(1, side / Math.max(w, h, 1));
    const cw = Math.max(1, Math.round(w * k));
    const ch = Math.max(1, Math.round(h * k));
    const c = document.createElement("canvas");
    c.width = cw;
    c.height = ch;
    const ctx = c.getContext("2d");
    if (!ctx) return Promise.resolve(null);
    // Shaffof PNG JPEG'da qora bo'lib qolmasin
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, cw, ch);
    ctx.drawImage(img, 0, 0, cw, ch);
    return new Promise((resolve) => {
      try {
        c.toBlob((b) => resolve(b), "image/jpeg", q);
      } catch {
        resolve(null);
      }
    });
  } catch {
    return Promise.resolve(null);
  }
}

/** Fayl boshidagi baytlardan rasm turi (server bilan bir xil qoida). */
async function sniffImage(file: Blob): Promise<"image/jpeg" | "image/png" | "image/webp" | null> {
  try {
    const b = new Uint8Array(await file.slice(0, 12).arrayBuffer());
    if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return "image/jpeg";
    if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47) return "image/png";
    const ascii = (i: number, n: number) => String.fromCharCode(...b.slice(i, i + n));
    if (b.length >= 12 && ascii(0, 4) === "RIFF" && ascii(8, 4) === "WEBP") return "image/webp";
  } catch {
    /* o'qib bo'lmadi */
  }
  return null;
}

/**
 * JPEG'dan EXIF (APP1, FF E1) bo'laklarini olib tashlaydi — GPS va
 * kamera ma'lumoti asl fayl yuborilganda ham ketmasin. Tuzilma
 * tanilmasa — asl fayl o'zgarmay qaytadi.
 */
async function stripJpegExif(file: Blob): Promise<Blob> {
  try {
    const b = new Uint8Array(await file.arrayBuffer());
    if (b[0] !== 0xff || b[1] !== 0xd8) return file;
    const keep: Uint8Array[] = [b.subarray(0, 2)];
    let i = 2;
    while (i + 4 <= b.length && b[i] === 0xff) {
      const marker = b[i + 1];
      if (marker === 0xff) {                      // to'ldiruvchi bayt
        i += 1;
        continue;
      }
      if (marker === 0xda) break;                 // SOS — rasm ma'lumoti
      const len = (b[i + 2] << 8) | b[i + 3];
      if (len < 2 || i + 2 + len > b.length) return file;
      if (marker !== 0xe1) keep.push(b.subarray(i, i + 2 + len));
      i += 2 + len;
    }
    if (i >= b.length || b[i] !== 0xff) return file;
    keep.push(b.subarray(i));
    return new Blob(keep as BlobPart[], { type: "image/jpeg" });
  } catch {
    return file;
  }
}

/**
 * Yuborishdan oldin: rasm canvas orqali qayta chiziladi (uzun tomoni
 * 2000 px gacha, JPEG 0.85) — bu EXIF/GPS ma'lumotini ham olib
 * tashlaydi va fayl kichrayadi. PDF o'zgarmaydi, faqat 3 MB tekshiriladi.
 * Haqiqiy tur (magic bytes) serverda tekshiriladi.
 *
 * 2026-10-17 (review): canvas ishlamasa (kuchsiz WebView, xotira,
 * maxfiylik rejimi) va asl fayl JPG / PNG / WEBP bo'lib 3 MB dan
 * oshmasa — asl fayl yuboriladi (JPEG'dan EXIF olib tashlanadi).
 * Brauzer ocholmaydigan HEIC uchun aniq ko'rsatma chiqadi.
 */
export async function prepareCertFile(
  file: File,
): Promise<{ blob: Blob; name: string; mime: string }> {
  const isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
  if (isPdf) {
    if (file.size > CERT_MAX_BYTES)
      throw new Error("Fayl juda katta — 3 MB dan oshmasin");
    return { blob: file, name: "sertifikat.pdf", mime: "application/pdf" };
  }
  const isHeic = /hei[cf]/i.test(file.type) || /\.hei[cf]$/i.test(file.name);
  if (!file.type.startsWith("image/") && !/\.(jpe?g|png|webp|heic|heif)$/i.test(file.name))
    throw new Error("Faqat rasm (JPG, PNG, WEBP) yoki PDF yuklang");
  let img: HTMLImageElement | null = null;
  try {
    img = await loadImage(file);
  } catch {
    img = null;
  }
  let blob: Blob | null = null;
  if (img) {
    blob = await encode(img, MAX_SIDE, 0.85);
    // Juda tafsilotli rasm — sifatni biroz pasaytirib qayta urinamiz
    if (blob && blob.size > CERT_MAX_BYTES) blob = await encode(img, 1600, 0.75);
    if (blob && blob.size <= CERT_MAX_BYTES)
      return { blob, name: "sertifikat.jpg", mime: "image/jpeg" };
  }
  // Qayta chizib bo'lmadi — asl fayl (server qabul qiladigan tur bo'lsa)
  const orig = await sniffImage(file);
  if (orig && file.size <= CERT_MAX_BYTES) {
    const out = orig === "image/jpeg" ? await stripJpegExif(file) : file;
    const ext = orig === "image/png" ? "png" : orig === "image/webp" ? "webp" : "jpg";
    return { blob: out, name: `sertifikat.${ext}`, mime: orig };
  }
  if (isHeic && !orig)
    throw new Error("HEIC formatini JPG ga o'tkazing yoki skrinshot yuklang");
  if (blob || (orig && file.size > CERT_MAX_BYTES))
    throw new Error("Fayl juda katta — 3 MB dan oshmasin");
  if (!img) throw new Error("Rasmni o'qib bo'lmadi — JPG yoki PNG formatida yuklang");
  throw new Error("Rasmni tayyorlab bo'lmadi — boshqa rasm tanlang");
}
