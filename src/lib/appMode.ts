/**
 * QAYSI ILOVADAN OCHILDI (2026-08-18).
 *
 * Jahongir: "jony student appdan faqat studentlar kira olsin xodimlar
 * ham akkauntlariga kirib ketyabdi undan".
 *
 * Jony Student PWA har doim /student?pwa=1 manzilidan ochiladi
 * (student.webmanifest'dagi start_url). Shu belgini sessiyada eslab
 * qolamiz: bu OYNA "o'quvchi ilovasi" rejimida.
 *
 * Nega sessionStorage: telefon brauzeri va o'rnatilgan PWA bitta
 * xotirani bo'lishadi. localStorage'ga yozsak, xodim keyin ODDIY
 * brauzerdan jonyos.uz ga kirsa ham qulflanib qolardi. sessionStorage
 * esa faqat shu oynaga tegishli — PWA har ochilganda start_url orqali
 * belgi qaytadan qo'yiladi, oddiy brauzer esa toza qoladi.
 */

const KEY = "jony_app_mode";

/** Ilova ochilganda bir marta chaqiriladi (main.tsx). */
export function detectAppMode() {
  try {
    const p = new URLSearchParams(window.location.search);
    if (p.get("pwa") === "1" &&
        window.location.pathname.startsWith("/student")) {
      sessionStorage.setItem(KEY, "student");
    }
    // JonyOS xodim ilovasi (2026-09-27): jonyos.webmanifest start_url
    // = /app?pwa=1. Login'dan keyin xodim shu ilovaga qaytadi.
    if (p.get("pwa") === "1" &&
        window.location.pathname.startsWith("/app")) {
      sessionStorage.setItem(KEY, "staff");
    }
  } catch {
    /* sessionStorage yopiq bo'lsa - shunchaki rejimsiz davom etadi */
  }
}

/** Bu oyna Jony Student ilovasi sifatida ochilganmi. */
export function isStudentApp(): boolean {
  try {
    return sessionStorage.getItem(KEY) === "student";
  } catch {
    return false;
  }
}

/** Bu oyna JonyOS xodim ilovasi sifatida ochilganmi (2026-09-27). */
export function isStaffApp(): boolean {
  try {
    return sessionStorage.getItem(KEY) === "staff";
  } catch {
    return false;
  }
}
