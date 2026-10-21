import { api } from "./api";

/**
 * SMM BRENDLARI (2026-10-17).
 *
 * Jahongir: "keyin SMM bo'limida aynan Marhaboni profilida faqat bitta
 * proyekt emas u Jony School va Jahongir Zoxidovning shaxsiy brend
 * profilini ham yurgizadi". Tanlangan yo'l: "Brendlar ro'yxati, kontent
 * bo'yicha" — har bir kontent bitta brendga tegishli (Jony Academy,
 * Jony School, Jahongir Zoxidov — shaxsiy brend), SMM menejer
 * profilida o'z brendlarini ko'radi, SMM ekranida brend bo'yicha
 * filtr bor. Instagram ulanishi hozircha BITTA (brendga alohida token
 * yo'q).
 *
 * Server: api/smm_brands.py
 *   GET  /api/smm/brands               — SMM_ACCESS
 *   POST /api/smm/brands               — faqat FULL_ACCESS
 *   PUT  /api/smm/brands/{id}          — faqat FULL_ACCESS
 *   PUT  /api/smm/brands/{id}/members  — faqat FULL_ACCESS
 * Kontentda brand_id bo'sh bo'lsa = Jony Academy (seed to'ldiradi).
 * A'zolik kontent ko'rinishini O'ZGARTIRMAYDI — faqat profil kartasi
 * va standart filtr uchun.
 */

export type SmmBrandKind = "academy" | "school" | "personal" | "brand";

export type SmmBrandMember = { id: number; name: string };

export type SmmBrand = {
  id: number;
  code: string;
  name: string;
  kind: SmmBrandKind | string;
  is_active: boolean;
  note: string | null;
  members: SmmBrandMember[];
  /** Joriy xodim shu brendga biriktirilganmi. */
  mine: boolean;
  content_count: number;
};

export type SmmBrandsResponse = {
  brands: SmmBrand[];
  /** Joriy xodim a'zo bo'lgan brendlar id'lari. */
  mine: number[];
  /** Biriktirish mumkin bo'lgan SMM menejerlar — server faqat
   *  FULL_ACCESS'ga to'ldiradi (boshqalarga bo'sh yoki yo'q). */
  managers?: SmmBrandMember[];
};

/** Kontent javobidagi brend maydonlari (ro'yxat va bitta kontent). */
export type ContentBrandFields = {
  brand_id?: number | null;
  brand_name?: string | null;
};

export const BRAND_KIND_LABEL: Record<string, string> = {
  academy: "Akademiya",
  school: "Maktab",
  personal: "Shaxsiy brend",
  brand: "Brend",
};

export function getSmmBrands(fresh = false): Promise<SmmBrandsResponse> {
  return fresh
    ? api.fresh<SmmBrandsResponse>("/smm/brands")
    : api.get<SmmBrandsResponse>("/smm/brands");
}

export function createSmmBrand(body: { name: string; kind?: SmmBrandKind }) {
  return api.post<unknown>("/smm/brands", body);
}

export function updateSmmBrand(
  id: number,
  body: { name?: string; is_active?: boolean },
) {
  return api.put<unknown>(`/smm/brands/${id}`, body);
}

/** A'zolarni TO'LIQ almashtiradi (ro'yxatda yo'q xodim chiqariladi). */
export function setSmmBrandMembers(id: number, user_ids: number[]) {
  return api.put<unknown>(`/smm/brands/${id}/members`, { user_ids });
}

/** Jony Academy brendi — yangi kontent uchun standart. */
export function academyBrand(brands: SmmBrand[]): SmmBrand | undefined {
  return brands.find((b) => b.code === "academy")
    || brands.find((b) => b.kind === "academy");
}

// ---- Tanlangan filtr (har xodim brauzerida, faqat qulaylik) ----
const FILTER_KEY = "jony_smm_brand_filter";

/** Kalit HAR XODIMGA alohida (2026-10-17): ofisdagi umumiy kompyuterda
 *  bir SMM menejerning tanlovi keyingi xodimning a'zolik bo'yicha
 *  standart filtrini bosib ketmasin. Kalitda ism ochiq turmasin —
 *  qisqa xesh. */
function filterKey(owner: string): string {
  let h = 5381;
  for (let i = 0; i < owner.length; i++) {
    h = ((h << 5) + h + owner.charCodeAt(i)) | 0;
  }
  return `${FILTER_KEY}:${(h >>> 0).toString(36)}`;
}

/** "all" | brend id (matn). Saqlanmagan bo'lsa null. owner — xodim
 *  (useAuth().user.full_name). */
export function readBrandFilter(owner: string): string | null {
  try {
    return localStorage.getItem(filterKey(owner));
  } catch {
    return null; // maxfiy oyna / bloklangan saqlash — standart filtr
  }
}

export function saveBrandFilter(v: string, owner: string) {
  try {
    localStorage.setItem(filterKey(owner), v);
  } catch {
    /* saqlab bo'lmadi — filtr shu ochilishda ishlayveradi */
  }
}

/** Yangi post / import uchun standart brend (id matn, "" — brend yo'q).
 *  Filtrda bitta faol brend tanlangan bo'lsa — o'sha (aks holda yangi
 *  post filtrdan "yo'qolib" qolardi), bo'lmasa Jony Academy. */
export function defaultBrandFor(
  brands: SmmBrand[],
  filter: string | null,
): string {
  const active = brands.filter((b) => b.is_active);
  if (filter && active.some((b) => String(b.id) === filter)) return filter;
  // Akademiya nofaol bo'lsa — ro'yxatdagi birinchisi (ko'ringan bilan
  // yuborilgan bir xil bo'lsin)
  const ac = academyBrand(active) || active[0];
  return ac ? String(ac.id) : "";
}

/**
 * Qaysi filtr bilan ochilsin: avval xodim o'zi tanlagani (brend hali
 * faol bo'lsa), aks holda bitta brendga biriktirilgan bo'lsa — o'sha,
 * qolgan hollarda "Hammasi". Marhaboda 3 ta brend — "Hammasi".
 */
export function pickBrandFilter(
  r: SmmBrandsResponse,
  stored: string | null,
): string {
  const active = r.brands.filter((b) => b.is_active);
  if (stored === "all") return "all";
  if (stored && active.some((b) => String(b.id) === stored)) return stored;
  const mine = active.filter((b) => r.mine.includes(b.id));
  return mine.length === 1 ? String(mine[0].id) : "all";
}
