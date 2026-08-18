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
