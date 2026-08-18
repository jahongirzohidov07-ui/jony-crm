import { useCallback, useEffect, useRef, useState } from "react";

/**
 * MASHQDA AVTOMAT KEYINGI SAVOLGA O'TISH (2026-08-18).
 *
 * Jahongir: "practice qilganda javobni belgilab keyin davom etish
 * tugmasini bosish kere shu narsa avtomat otsin keyingisiga".
 *
 * Oldin har javobdan keyin o'quvchi "Keyingisi"ni bosishi SHART edi.
 * 15 savollik mashqda bu 15 ta ortiqcha bosish — mashq cho'zilib,
 * zerikarli bo'lib qolardi.
 *
 * Endi javob berilgach o'zi o'tadi. Lekin darrov emas: o'quvchi
 * o'qishi kerak bo'lgan matn qancha ko'p bo'lsa, shuncha uzoq turadi.
 * Ayniqsa XATO javobda — to'g'ri javobni va izohni ko'rmay o'tib
 * ketish o'rganishga zarar qiladi, shuning uchun u yerda vaqt eng
 * uzun.
 *
 * Tugma o'chirilmaydi: sanoq bilan ko'rinib turadi ("Keyingisi (3)"),
 * kutgisi kelmagan bosadi va darhol o'tadi.
 */

/** Javobga qarab necha millisekund kutilishi. */
export function autoNextDelay(opts: {
  correct: boolean;
  /** Xato bo'lganda to'g'ri javob matni ko'rsatiladimi */
  hasAnswer?: boolean;
  /** Izoh / skript kabi qo'shimcha o'qiladigan matn bormi */
  hasExtra?: boolean;
}): number {
  const { correct, hasAnswer, hasExtra } = opts;
  if (correct) return hasExtra ? 2500 : 900;
  // Xato — o'quvchi to'g'ri javobni yodda tutib qolishi kerak
  let ms = 3500;
  if (hasAnswer) ms += 500;
  if (hasExtra) ms += 1000;
  return ms;
}

/**
 * Sanoqli avto-o'tish.
 *
 *  schedule(ms) — belgilangan vaqtdan keyin onNext chaqiriladi;
 *  cancel()     — taymerni to'xtatadi (tugma bosilganda yoki chiqishda);
 *  secsLeft     — tugmada ko'rsatiladigan qolgan soniya (0 = yashirin).
 *
 * onNext ref'da saqlanadi — taymer eskirgan qiymatlar bilan ishlamaydi.
 */
export function useAutoNext(onNext: () => void) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ticker = useRef<ReturnType<typeof setInterval> | null>(null);
  const cb = useRef(onNext);
  cb.current = onNext;
  const [secsLeft, setSecsLeft] = useState(0);

  const cancel = useCallback(() => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
    if (ticker.current) {
      clearInterval(ticker.current);
      ticker.current = null;
    }
    setSecsLeft(0);
  }, []);

  const schedule = useCallback((ms: number) => {
    if (timer.current) clearTimeout(timer.current);
    if (ticker.current) clearInterval(ticker.current);
    setSecsLeft(Math.ceil(ms / 1000));
    ticker.current = setInterval(
      () => setSecsLeft((n) => (n > 1 ? n - 1 : 0)),
      1000,
    );
    timer.current = setTimeout(() => {
      if (ticker.current) clearInterval(ticker.current);
      ticker.current = null;
      timer.current = null;
      setSecsLeft(0);
      cb.current();
    }, ms);
  }, []);

  // Sahifadan chiqilganda taymer qolib ketmasin
  useEffect(() => cancel, [cancel]);

  return { schedule, cancel, secsLeft };
}
