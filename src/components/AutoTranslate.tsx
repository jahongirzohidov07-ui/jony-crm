import { useEffect } from "react";
import { getUiLang, translateDom } from "../lib/uiLang";

/**
 * Ruscha rejim yoqilgan bo'lsa, sahifadagi matnlarni lug'at bo'yicha
 * o'giradi va React qayta chizganda ham qayta qo'llaydi.
 *
 * 2026-08-13, Jahongir: "hozir faqat rus tiliga o'tkiz, faqat
 * ustozlar uchun shu funksiyani ochib ber boshlanishiga".
 */
export function AutoTranslate() {
  useEffect(() => {
    if (getUiLang() !== "ru") return;
    let raf = 0;
    const run = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => translateDom(document.body));
    };
    run();
    const obs = new MutationObserver(run);
    obs.observe(document.body, { childList: true, subtree: true,
                                 characterData: true });
    return () => { obs.disconnect(); cancelAnimationFrame(raf); };
  }, []);
  return null;
}
