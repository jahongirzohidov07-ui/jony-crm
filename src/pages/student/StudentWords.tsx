import { StudentLoadError, StudentLoading } from "../../components/StudentLoading";
import { StudentCoinIcon, StudentIcon } from "../../components/StudentIcon";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, Gauge, Target } from "lucide-react";
import { BandLegend, BandList } from "../../components/wordbank/BandList";
import { WordbankUnavailable } from "../../components/wordbank/WordbankCards";
import { useWordbank } from "../../components/wordbank/useWordbank";
import { JSA } from "../../components/Jsa";
import { formatDate } from "../../lib/format";
import { useLearningLanguage } from "../../lib/lang";
import { fmtNum } from "../../lib/studentApi";
import { focusBand, roundEst } from "../../lib/wordbankApi";

/**
 * JONY STUDENT — "SO'Z BILISH" (2026-10-16, OWNER_DECISIONS D1–D5).
 *
 * Ikki son ALOHIDA turadi va hech qachon qo'shilmaydi:
 *   * "Tasdiqlangan so'zlar" (qalin) — turli kunlarda to'g'ri topilgan,
 *     kamida bir marta yozib topilgan so'zlar. Coin va reyting shundan.
 *   * "Taxminiy lug'at hajmi" (kulrang) — oxirgi hajm testidan, oraliq
 *     bilan; hech narsaga ta'sir qilmaydi.
 * 20 daraja: "Common 1000: 870/1000", har darajada "+N coin" (N-daraja
 * tugasa N coin, bir marta). Ma'lumot: GET /api/wordbank/me.
 */
export default function StudentWords() {
  const lang = useLearningLanguage();
  const { state, reload } = useWordbank(true);

  if (lang !== "en") return <WordbankUnavailable reason="lang" />;
  if (!state) return <StudentLoading />;
  if (state.status === "off") return <WordbankUnavailable reason="off" />;
  if (state.status === "error")
    return <StudentLoadError message={state.message} onRetry={reload} />;

  const d = state.data;
  const f = focusBand(d.bands);
  const t = d.size_test;
  const doneCount = d.bands.filter((b) => b.done).length;
  const nextHundred = (Math.floor(d.known / 100) + 1) * 100;
  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const streak = d.streak ?? 0;

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
      {/* ------------------------------------------------ sarlavha */}
      <div className="flex items-center gap-2.5">
        <Link to="/student/games" aria-label="O'rganishga qaytish"
          className="w-11 h-11 rounded-xl flex items-center justify-center text-white shrink-0"
          style={{ background: "#1242a0" }}>
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-bold text-slate-300 flex-1">O'rganish</p>
        <span className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 border shrink-0"
              style={card} title="So'z bilishdan yig'ilgan coin">
          <StudentCoinIcon size={18} />
          <b className="text-white text-sm">{fmtNum(d.coins_earned)} coin</b>
        </span>
      </div>

      <div className="flex items-end gap-3">
        <div className="flex-1 min-w-0">
          <h1 className="text-[30px] font-extrabold text-white leading-tight">
            So'z bilish
          </h1>
          <p className="text-[13px] text-slate-400 mt-1">
            Inglizcha so'zlaringiz — tekshirilgan va tasdiqlangan
          </p>
        </div>
        <StudentIcon name="vocabulary" size={64} className="shrink-0" />
      </div>

      {/* -------------------------------- TASDIQLANGAN (asosiy son) */}
      <div className="student-hero student-pattern rounded-3xl p-5 text-white">
        <p className="text-[13px] font-bold text-white/85">Tasdiqlangan so'zlar</p>
        <p className="text-[52px] font-extrabold leading-none mt-1 tabular-nums">
          {fmtNum(d.known)}
        </p>
        <p className="text-[12px] text-white/80 mt-2 leading-snug">
          Turli kunlarda to'g'ri topilgan va kamida bir marta yozib topilgan
          so'zlar. Coin va reyting shu songa qarab.
        </p>
        <div className="flex flex-wrap gap-1.5 mt-3">
          <span className="rounded-full bg-white/20 px-2.5 py-1 text-[12px] font-bold">
            {doneCount}/20 daraja tugatildi
          </span>
          {streak > 0 && (
            <span className="rounded-full bg-white/20 px-2.5 py-1 text-[12px] font-bold">
              🔥 {streak} kun ketma-ket
            </span>
          )}
          {d.due_today > 0 && (
            <span className="rounded-full bg-white/20 px-2.5 py-1 text-[12px] font-bold">
              Bugun takrorlash: {fmtNum(d.due_today)} so'z
            </span>
          )}
        </div>
      </div>

      {/* ------------------------------ TAXMINIY (kulrang, alohida) */}
      <div className="rounded-2xl border border-dashed px-4 py-3"
           style={{ borderColor: "#5b6f9c" }}>
        <p className="text-[12px] font-semibold text-slate-400">
          Taxminiy lug'at hajmi
        </p>
        {t ? (
          <>
            <p className="text-[22px] font-bold text-slate-300 leading-tight mt-0.5">
              ≈ {fmtNum(roundEst(t.estimate))}{" "}
              <span className="text-[13px] font-medium text-slate-400">
                ({fmtNum(roundEst(t.low))}–{fmtNum(roundEst(t.high))})
              </span>
            </p>
            <p className="text-[11px] text-slate-500 mt-1 leading-snug">
              Lug'at hajmi testi{t.date ? ` · ${formatDate(t.date)}` : ""} ·
              tasdiqlangan songa qo'shilmaydi
            </p>
          </>
        ) : (
          <p className="text-[13px] text-slate-400 mt-0.5 leading-snug">
            Hali test topshirilmagan — nechta so'z bilishingizni taxminan
            bilib oling.
          </p>
        )}
      </div>

      {/* ------------------------------------------------- tugmalar */}
      <Link to="/student/words/practice"
        className="student-pattern w-full rounded-2xl p-4 flex items-center gap-3 text-left active:scale-[0.99] transition"
        style={{ background: "linear-gradient(120deg,#10b981,#059669 55%,#0e7490)",
                 boxShadow: "0 8px 30px #05966940" }}>
        <span className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center shrink-0">
          <Target size={24} className="text-white" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[19px] font-extrabold text-white">
            Bugungi mashq
          </span>
          <span className="block text-[12.5px] text-white/85 mt-0.5">
            {d.due_today > 0
              ? `${fmtNum(d.due_today)} ta takrorlash + yangi so'zlar`
              : "20 ta savol · taxminan 5 daqiqa"}
          </span>
        </span>
        <span className="w-10 h-10 rounded-full bg-white flex items-center justify-center shrink-0">
          <ArrowRight size={18} className="text-emerald-600" />
        </span>
      </Link>

      <Link to="/student/words/test"
        className="w-full rounded-2xl border p-4 flex items-center gap-3 text-left active:scale-[0.99] transition"
        style={card}>
        <span className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center shrink-0">
          <Gauge size={24} className="text-sky-300" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[17px] font-extrabold text-white">
            Lug'at hajmi testi
          </span>
          <span className="block text-[12px] text-slate-400 mt-0.5">
            Taxminiy natija · tasdiqlangan songa ta'sir qilmaydi
          </span>
        </span>
        <ArrowRight size={18} className="text-slate-400 shrink-0" />
      </Link>

      {/* ------------------------------------------ keyingi marra */}
      <div className="student-panel bg-white rounded-3xl p-4">
        <p className="text-[17px] font-extrabold text-slate-900">Keyingi marra</p>
        {f ? (
          <>
            <p className="text-[14px] text-slate-800 mt-1.5">
              <b>{f.label}</b> — yana{" "}
              <b className="text-brand-700">{fmtNum(Math.max(0, f.total - f.known))} so'z</b>{" "}
              → <b className="text-amber-600">+{f.coins} coin</b>
            </p>
            <div className="h-2 rounded-full bg-slate-100 overflow-hidden mt-2">
              <div className="h-full rounded-full bg-emerald-500"
                   style={{ width: `${f.total ? Math.min(100, (f.known / f.total) * 100) : 0}%` }} />
            </div>
          </>
        ) : doneCount === 20 ? (
          <p className="text-[14px] text-emerald-700 font-bold mt-1.5">
            Barcha 20 daraja tugatildi — ajoyib natija! 🎉
          </p>
        ) : (
          <p className="text-[13px] text-slate-500 mt-1.5">
            Keyingi daraja so'zlari tayyorlanmoqda — tez orada ochiladi.
          </p>
        )}
        <p className="text-[12.5px] text-slate-600 mt-2">
          {fmtNum(nextHundred)} ta tasdiqlangan so'zgacha yana{" "}
          <b>{fmtNum(nextHundred - d.known)}</b> ta
        </p>
      </div>

      {/* ------------------------------------------- 20 ta daraja */}
      <div className="student-panel bg-white rounded-3xl p-4">
        <div className="flex items-baseline gap-2">
          <p className="text-[17px] font-extrabold text-slate-900 flex-1">Darajalar</p>
          <p className="text-[12px] text-slate-500">N-daraja = N coin, jami 210</p>
        </div>
        <div className="mt-2 mb-1"><BandLegend withEstimate={!!t} /></div>
        <BandList bands={d.bands} focus={f?.band ?? null} sizeTest={t} />
      </div>

      {/* ------------------------------------------------- izoh */}
      <details className="rounded-2xl border px-4 py-3 text-slate-300" style={card}>
        <summary className="cursor-pointer text-[14px] font-bold text-white min-h-[28px]">
          Qanday hisoblanadi?
        </summary>
        <ul className="mt-2 space-y-1.5 text-[12.5px] leading-relaxed list-disc pl-4">
          <li>
            Yangi so'z kamida 3 xil kunda to'g'ri topilganda tasdiqlanadi;
            shulardan kamida bittasi — so'zni yozib topish.
          </li>
          <li>
            Avvaldan bilgan so'zingiz tezroq tasdiqlanadi: birinchi ko'rishda
            to'g'ri topsangiz, 3 kundan keyin yozib topish kifoya.
          </li>
          <li>
            Unutilgan so'z sondan chiqadi va yozib topilganda qaytadi.
          </li>
          <li>
            Daraja tugaganda (1000 ta so'zning hammasi tasdiqlanganda) coin
            beriladi: Common 1000 — 1 coin, Common 2000 — 2 coin … Common
            20000 — 20 coin. Har daraja uchun bir marta.
          </li>
          <li>
            Lug'at hajmi testi faqat taxmin beradi — tasdiqlangan son, coin
            va reytingga ta'sir qilmaydi.
          </li>
        </ul>
      </details>
    </div>
  );
}
