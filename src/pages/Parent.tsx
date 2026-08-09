import { useEffect, useState } from "react";
import { Outlet, useParams } from "react-router-dom";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

export type ParentCtx = {
  d: Any;
  token: string;
  fmt: (n: Any) => string;
  installEvt: Any;
  installHidden: boolean;
  setInstallHidden: (v: boolean) => void;
  installApp: () => void;
};

export const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");

/**
 * OTA-ONA PORTALI — QOBIQ (layout), loginsiz, faqat maxsus havola
 * bilan ochiladi.
 *
 * Tuzatildi (2026-08-09, Jahongir): ilgari hammasi (davomat, balans,
 * to'lovlar, coin/XP, test natijalari) BITTA uzun sahifada edi —
 * "chalkash" deb topildi. Endi bu fayl faqat MA'LUMOTNI BIR MARTA
 * yuklaydi (barcha ichki sahifalar shu yerdan Outlet context orqali
 * foydalanadi — har biri qayta so'rov yubormaydi) va PWA (uy ekraniga
 * o'rnatish) mantiqini boshqaradi. Har bir bo'lim (to'lovlar, coin/XP,
 * natijalar, guruhdagi reyting) o'zining ALOHIDA sahifasiga ega —
 * bosh sahifadagi (ParentHome) tugmalar orqali ochiladi.
 */
export default function Parent() {
  const { token } = useParams();
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [installEvt, setInstallEvt] = useState<Any>(null);
  const [installHidden, setInstallHidden] = useState(false);

  useEffect(() => {
    fetch(`/api/parent/${token}`)
      .then(async (r) => {
        if (!r.ok) throw new Error("Havola eskirgan yoki noto'g'ri");
        setD(await r.json());
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [token]);

  // PWA: shu FARZANDGA xos manifest ulanadi (uy ekraniga qo'shilsa,
  // to'g'ridan-to'g'ri shu sahifaga ochiladi) va servis worker faqat
  // /parent/ doirasida ro'yxatdan o'tadi — xodimlar paneliga tegmaydi.
  useEffect(() => {
    if (!token) return;
    let link = document.querySelector<HTMLLinkElement>(
      'link[rel="manifest"]'
    );
    if (!link) {
      link = document.createElement("link");
      link.rel = "manifest";
      document.head.appendChild(link);
    }
    link.href = `/api/parent/${token}/manifest.webmanifest`;

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/parent/" })
        .catch(() => {});
    }

    return () => {
      link?.parentNode?.removeChild(link);
    };
  }, [token]);

  // Android/Chrome "uy ekraniga qo'shish mumkin" deb topsa shu
  // hodisani otadi — brauzerning o'zi ko'rsatadigan (ko'zga unча
  // tashlanmaydigan) taklif o'rniga aniq tugma ko'rsatamiz. Holat
  // shu qobiqda saqlanadi (ichki sahifalar orasida yo'qolmasin).
  useEffect(() => {
    function onPrompt(e: Any) {
      e.preventDefault();
      setInstallEvt(e);
    }
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

  async function installApp() {
    if (!installEvt) return;
    installEvt.prompt();
    await installEvt.userChoice;
    setInstallEvt(null);
  }

  if (err)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <p className="text-sm text-slate-500">{err}</p>
      </div>
    );
  if (!d)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-400">Yuklanmoqda…</p>
      </div>
    );

  const ctx: ParentCtx = {
    d,
    token: token || "",
    fmt,
    installEvt,
    installHidden,
    setInstallHidden,
    installApp,
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-10">
      <Outlet context={ctx} />
    </div>
  );
}
