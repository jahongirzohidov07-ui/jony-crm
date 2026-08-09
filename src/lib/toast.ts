/**
 * Global xato/xabar bildirishnomasi (toast) tizimi (2026-08-09).
 *
 * Muammo (Jahongir aytdi): ruxsat etilmagan (yoki boshqa sabab bilan
 * muvaffaqiyatsiz tugagan) amal qilinganda ekran shunchaki
 * "yangilanadi" — hech qanday xato ko'rinmaydi. Xodim (masalan HR
 * menejer) biror narsa qo'shmoqchi bo'lib muvaffaqiyatsiz tugasa,
 * hech nima ko'rmaydi va "qildim" deb o'ylab qo'yishi mumkin.
 *
 * Yechim: React daraxtidan tashqarida ham chaqirsa bo'ladigan oddiy
 * pub-sub do'kon. src/lib/api.ts'ning request() funksiyasi HAR BIR
 * muvaffaqiyatsiz so'rovda shu yerga xabar yuboradi — shuning uchun
 * hech bir chaqiruv joyi o'zi alohida .catch() yozishni "unutib
 * qo'ysa" ham, xato ko'rinmasdan qolmaydi. Har bir sahifaning o'z
 * mahalliy xato ko'rsatish (masalan forma ichidagi qizil matn) bilan
 * BIR VAQTDA ishlaydi — bir-biriga xalaqit bermaydi.
 */
export type ToastKind = "error" | "success" | "info";

export interface ToastMsg {
  id: number;
  kind: ToastKind;
  text: string;
}

let toasts: ToastMsg[] = [];
let nextId = 1;
const listeners = new Set<(t: ToastMsg[]) => void>();

function emit() {
  listeners.forEach((fn) => fn(toasts));
}

export function subscribeToasts(fn: (t: ToastMsg[]) => void): () => void {
  listeners.add(fn);
  fn(toasts);
  return () => {
    listeners.delete(fn);
  };
}

export function pushToast(text: string, kind: ToastKind = "error", ms = 6000) {
  const id = nextId++;
  toasts = [...toasts, { id, kind, text }];
  emit();
  if (ms > 0) {
    setTimeout(() => dismissToast(id), ms);
  }
  return id;
}

export function dismissToast(id: number) {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}
