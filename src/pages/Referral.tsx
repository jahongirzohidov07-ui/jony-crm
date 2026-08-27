import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { BrandIcon } from "../components/BrandIcon";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * DO'ST KO'RADIGAN SAHIFA — loginsiz (2026-08-28).
 *
 * Jahongir: "do'stiga yuborgan linkda men Jony Academyda falon kursga
 * yozildim, shunaqa shunaqa foydalarni bor ekan deb maqtan, Jony
 * Student app orqali o'rganish oson ekan bo'lib o'rtog'iga tavsiya
 * qilish MUKAMMAL MARKETING TIZIM bo'lib ishlashi kerak".
 *
 * Havola: https://jonyos.uz/r/JONY-XXXXX
 *
 * Sahifa uch ishni qiladi:
 *   1. ISHONCH — "seni do'sting Aziz taklif qildi" (notanish reklama
 *      emas, tanish odamning tavsiyasi)
 *   2. SABAB — nega aynan bu yerda o'qish kerak (6 ta aniq foyda)
 *   3. QADAM — bitta qisqa forma, ikkita maydon. Ko'p savol
 *      so'ralsa odam yarim yo'lda tashlab ketadi.
 *
 * MAXFIYLIK: sahifa faqat taklif qilgan bolaning ISMINI ko'rsatadi.
 * Familiya, telefon, filial ichidagi hech narsa chiqmaydi.
 */

const FOYDA = [
  {
    icon: "📱",
    t: "Jony Student ilovasi",
    d: "Darsdan tashqari telefonda o'ynab o'rganasan — so'z, grammatika, "
      + "listening, speaking. Kuniga 10 daqiqa ham natija beradi.",
  },
  {
    icon: "🪙",
    t: "Har dars uchun coin",
    d: "Qatnashsang, uy vazifasini qilsang — coin yig'iladi. Coinga "
      + "do'kondan sovg'a va o'qish chegirmasini olasan.",
  },
  {
    icon: "🎯",
    t: "Darajang aniq o'lchanadi",
    d: "Boshida daraja testi, keyin har oy o'sishing grafikda ko'rinadi. "
      + "\"Bilyapmanmi yo'qmi\" degan savol qolmaydi.",
  },
  {
    icon: "🏆",
    t: "Reyting va ligalar",
    d: "Guruhdoshlaring bilan musobaqa. Zerikarli yodlash emas — "
      + "o'yin bo'lib ketadi.",
  },
  {
    icon: "🎓",
    t: "IELTS va Multilevel",
    d: "Alohida tayyorlov bo'limi: real format, mock imtihon, "
      + "javobingning tahlili bilan.",
  },
  {
    icon: "👨‍👩‍👦",
    t: "Ota-onang ham ko'radi",
    d: "Davomat, to'lov, natija — hammasi ota-onangning telefonida. "
      + "Hech narsa yashirin qolmaydi.",
  },
];

export default function Referral() {
  const { code = "" } = useParams();
  const [info, setInfo] = useState<any>(null);
  const [f, setF] = useState({ full_name: "", phone: "", course: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    fetch(`/api/public/ref/${encodeURIComponent(code)}`)
      .then((r) => r.json())
      .then(setInfo)
      .catch(() => setInfo({ ok: false }));
  }, [code]);

  async function submit() {
    setErr("");
    if (f.full_name.trim().length < 3) return setErr("Ismingizni to'liq yozing");
    if (f.phone.replace(/\D/g, "").length < 7)
      return setErr("Telefon raqamingizni to'g'ri kiriting");
    setBusy(true);
    try {
      const res = await fetch(`/api/public/ref/${encodeURIComponent(code)}/lead`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(f),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || "Xatolik yuz berdi");
      setDone(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  const inviter = info?.inviter;

  if (done)
    return (
      <div className="min-h-screen bg-gradient-to-br from-brand-700 to-brand-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-xl p-8 max-w-md w-full text-center">
          <p className="text-5xl mb-3">🎉</p>
          <h1 className="text-xl font-bold text-slate-900 mb-2">
            Arizangiz qabul qilindi!
          </h1>
          <p className="text-sm text-slate-600 leading-relaxed">
            Tez orada administratorimiz qo'ng'iroq qilib, sizni{" "}
            <b>bepul sinov darsiga</b> yozib qo'yadi.
            {inviter ? (
              <>
                {" "}Do'stingiz <b>{inviter}</b>ga rahmat ayting — u sizni
                ajoyib joyga chaqirdi 😊
              </>
            ) : null}
          </p>
          <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-left">
            <p className="text-xs font-semibold text-slate-700 mb-1">
              Keyingi qadam
            </p>
            <p className="text-xs text-slate-600">
              Telefoningizni yoningizda tuting — bugunning o'zida
              bog'lanamiz. Darsga kelganda hujjat kerak emas, faqat
              o'zingiz keling.
            </p>
          </div>
        </div>
      </div>
    );

  const inp =
    "w-full rounded-xl border border-slate-300 px-3.5 py-3 text-sm "
    + "focus:border-brand-500 focus:outline-none";

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-700 via-brand-600 to-slate-50">
      <div className="max-w-lg mx-auto px-4 py-7">
        {/* ---- Sarlavha ---- */}
        <div className="flex flex-col items-center gap-2 mb-5">
          <div className="bg-white rounded-2xl p-3 shadow-lg">
            <BrandIcon size={44} className="rounded-xl" />
          </div>
          <span className="text-white text-2xl font-extrabold tracking-wide drop-shadow">
            JONY ACADEMY
          </span>
        </div>

        {/* ---- ISHONCH: kim taklif qildi ---- */}
        {inviter ? (
          <div className="bg-white/15 backdrop-blur rounded-2xl border border-white/25 p-4 mb-4 text-center">
            <p className="text-white text-sm">
              <b className="text-white">{inviter}</b> sizni Jony Academyga
              taklif qilyapti
            </p>
            {info?.course ? (
              <p className="text-white/80 text-xs mt-1">
                U hozir <b>{info.course}</b> kursida o'qiyapti
              </p>
            ) : null}
          </div>
        ) : null}

        <h1 className="text-white text-2xl font-extrabold leading-snug text-center">
          Ingliz tilini o'rganish
          <br />
          <span className="text-amber-300">o'yinga o'xshasa-chi?</span>
        </h1>
        <p className="text-white/85 text-sm text-center mt-2 mb-5">
          Darsda ustoz bilan, uyda esa Jony Student ilovasida.
          <br />
          Birinchi dars — <b className="text-white">butunlay bepul</b>.
        </p>

        {/* ---- FORMA (yuqorida — odam pastga tushmasdan yozsin) ---- */}
        <div className="bg-white rounded-3xl shadow-xl p-5 mb-6">
          <h2 className="text-base font-bold text-slate-900">
            Bepul sinov darsiga yozilish
          </h2>
          <p className="text-xs text-slate-500 mb-3">
            Ikkita maydon — shundan keyin o'zimiz qo'ng'iroq qilamiz.
          </p>

          <label className="block text-xs font-medium text-slate-600 mb-1">
            Ism va familiyangiz
          </label>
          <input
            className={inp}
            value={f.full_name}
            placeholder="Masalan: Diyor Sobirov"
            onChange={(e) => setF({ ...f, full_name: e.target.value })}
          />

          <label className="block text-xs font-medium text-slate-600 mb-1 mt-3">
            Telefon raqamingiz
          </label>
          <input
            className={inp}
            value={f.phone}
            inputMode="tel"
            placeholder="+998 90 123 45 67"
            onChange={(e) => setF({ ...f, phone: e.target.value })}
          />

          <label className="block text-xs font-medium text-slate-600 mb-1 mt-3">
            Qaysi yo'nalish qiziq? <span className="text-slate-400">(ixtiyoriy)</span>
          </label>
          <input
            className={inp}
            value={f.course}
            placeholder="Ingliz tili / IELTS / Multilevel"
            onChange={(e) => setF({ ...f, course: e.target.value })}
          />

          {err ? (
            <p className="text-xs text-red-600 mt-3 bg-red-50 rounded-lg px-3 py-2">
              {err}
            </p>
          ) : null}

          <button
            className="mt-4 w-full rounded-xl bg-brand-600 py-3.5 text-white text-sm font-bold
                       hover:bg-brand-700 disabled:opacity-60 transition"
            disabled={busy}
            onClick={submit}
          >
            {busy ? "Yuborilmoqda..." : "Bepul darsga yozilish"}
          </button>
          <p className="text-[11px] text-slate-400 text-center mt-2">
            Hech qanday to'lov talab qilinmaydi. Raqamingiz faqat
            qo'ng'iroq uchun ishlatiladi.
          </p>
        </div>

        {/* ---- SABAB ---- */}
        <h2 className="text-slate-900 text-lg font-bold mb-3">
          Nega aynan Jony Academy?
        </h2>
        <div className="space-y-2.5 mb-6">
          {FOYDA.map((x) => (
            <div
              key={x.t}
              className="bg-white rounded-2xl border border-slate-200 p-4 flex gap-3"
            >
              <span className="text-2xl leading-none">{x.icon}</span>
              <div>
                <p className="text-sm font-bold text-slate-900">{x.t}</p>
                <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                  {x.d}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-slate-900 rounded-2xl p-5 text-center">
          <p className="text-white text-sm font-semibold mb-1">
            Hali ikkilanyapsizmi?
          </p>
          <p className="text-white/70 text-xs mb-3">
            Sinov darsi bepul va hech narsaga majburlamaydi. Yoqmasa —
            kelmaysiz, xolos.
          </p>
          <button
            className="rounded-xl bg-white px-5 py-2.5 text-slate-900 text-sm font-bold"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            Formaga qaytish
          </button>
        </div>

        <p className="text-center text-[11px] text-slate-400 mt-6">
          Jony Academy · jonyos.uz
        </p>
      </div>
    </div>
  );
}
