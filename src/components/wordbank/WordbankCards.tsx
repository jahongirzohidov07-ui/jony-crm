import { Link } from "react-router-dom";
import { Check, ChevronRight, FileUp, Lock } from "lucide-react";
import { StudentIcon } from "../StudentIcon";
import { formatDate } from "../../lib/format";
import { fmtNum } from "../../lib/studentApi";
import { useLearningLanguage } from "../../lib/lang";
import { focusBand, roundEst } from "../../lib/wordbankApi";
import { useWordbank } from "./useWordbank";

/**
 * SO'Z BILISH — boshqa sahifalardagi kartalar (2026-10-16).
 *
 * Bo'lim bayroq bilan yopiq bo'lsa (server 404) yoki o'quvchi ingliz
 * tilini o'rganmayotgan bo'lsa — kartalar UMUMAN chiqmaydi.
 */

/** O'rganish sahifasidagi kirish kartasi. */
export function WordbankEntryCard() {
  const lang = useLearningLanguage();
  const { state } = useWordbank();
  if (lang !== "en" || state?.status !== "ok") return null;
  const d = state.data;
  const f = focusBand(d.bands);
  const fresh = d.known === 0 && !d.size_test;

  return (
    <Link
      to="/student/words"
      className="flex items-center gap-3 rounded-3xl p-4 mt-3 bg-white active:scale-[0.98] transition"
    >
      <StudentIcon name="vocabulary" size={48} className="shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-[17px] font-extrabold text-slate-900">So'z bilish</p>
        {fresh ? (
          <p className="text-[12px] text-slate-500 leading-snug mt-0.5">
            Inglizcha nechta so'z bilasiz? Test yoki bugungi mashqdan boshlang
          </p>
        ) : (
          <>
            <p className="text-[12.5px] text-slate-700 leading-snug mt-0.5">
              <b className="text-emerald-700">{fmtNum(d.known)}</b> ta
              tasdiqlangan so'z
            </p>
            {f && (
              <p className="text-[11.5px] text-slate-500 leading-snug">
                {f.label}: {fmtNum(f.known)}/{fmtNum(f.total)} · +{f.coins} coin
              </p>
            )}
          </>
        )}
      </div>
      {d.due_today > 0 && (
        <span className="px-2 py-1 rounded-full bg-sky-50 text-sky-700 text-[11px] font-bold shrink-0">
          {d.due_today} takror
        </span>
      )}
      <ChevronRight size={17} className="text-slate-300 shrink-0" />
    </Link>
  );
}

/**
 * Profil bo'limi: tasdiqlangan son, tugatilgan darajalar va
 * "Sertifikatlarim" joyi (OWNER D3).
 *
 * Sertifikat yuklash endpointi bu bosqichda YO'Q — tugma o'chiq va
 * "tez orada" deb turadi; hech qanday "yuklandi" holati soxta
 * ko'rsatilmaydi. Yuklangach o'quvchi faqat "yuklandi — tekshirilmoqda"
 * holatini ko'radi (ball yo'q), natija xodim tasdiqlagach chiqadi.
 */
export function WordbankProfileSection() {
  const lang = useLearningLanguage();
  const { state } = useWordbank(true);
  if (lang !== "en" || state?.status !== "ok") return null;
  const d = state.data;
  const done = d.bands.filter((b) => b.done);
  const t = d.size_test;

  return (
    <section className="student-panel bg-white rounded-3xl p-4"
             aria-labelledby="wb-profile-title">
      <div className="flex items-center gap-2">
        <StudentIcon name="vocabulary" size={36} />
        <h2 id="wb-profile-title" className="text-[20px] font-extrabold text-slate-900 flex-1">
          So'z bilish
        </h2>
        <Link to="/student/words"
              className="text-[13px] font-bold text-brand-600 inline-flex items-center gap-0.5 min-h-[44px]">
          Batafsil <ChevronRight size={15} />
        </Link>
      </div>

      <div className="flex items-end gap-3 mt-2">
        <p className="text-[38px] font-extrabold text-slate-900 leading-none tabular-nums">
          {fmtNum(d.known)}
        </p>
        <div className="pb-1 min-w-0">
          <p className="text-[13px] font-bold text-slate-800 leading-tight">
            Tasdiqlangan so'zlar
          </p>
          <p className="text-[12px] text-slate-500 leading-tight mt-0.5">
            Darajalar: {done.length}/20 tugatildi · {fmtNum(d.coins_earned)} coin
          </p>
        </div>
      </div>

      {done.length > 0 ? (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {done.map((b) => (
            <span key={b.band}
                  className="inline-flex items-center gap-1 rounded-full bg-amber-400 text-white px-2.5 py-1 text-[11.5px] font-extrabold">
              <Check size={12} strokeWidth={4} /> {b.label} · +{b.coins} coin
            </span>
          ))}
        </div>
      ) : (
        <p className="text-[12px] text-slate-500 mt-3 leading-snug">
          Common 1000 dagi barcha so'zlarni tasdiqlasangiz — +1 coin,
          Common 2000 — +2 coin va hokazo.
        </p>
      )}

      {t && (
        <p className="mt-3 rounded-xl border border-dashed border-slate-300 px-3 py-2 text-[12px] text-slate-500">
          Taxminiy lug'at hajmi: ≈ {fmtNum(roundEst(t.estimate))}
          {t.date ? ` · test ${formatDate(t.date)}` : ""}
        </p>
      )}

      {/* ------------------------------------ Sertifikatlarim (D3) */}
      <div className="mt-4 pt-4 border-t border-slate-100">
        <p className="text-[15px] font-extrabold text-slate-900">Sertifikatlarim</p>
        <p className="text-[12px] text-slate-600 mt-1 leading-relaxed">
          IELTS, CEFR/Multilevel, SAT, Duolingo va boshqa natijangiz
          sertifikatini shu yerga yuklaysiz. Yuklangach bu yerda faqat
          «yuklandi — tekshirilmoqda» holati turadi; natija ustoz yoki
          rahbariyat tasdiqlagandan keyin so'zlaringiz soni yonida
          ✓ belgi bilan chiqadi.
        </p>
        <button
          type="button"
          disabled
          className="mt-3 w-full min-h-[48px] rounded-2xl border-2 border-dashed border-slate-300 text-slate-400 text-[14px] font-bold inline-flex items-center justify-center gap-2"
        >
          <FileUp size={17} /> Sertifikat yuklash
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px]">
            <Lock size={11} /> tez orada
          </span>
        </button>
      </div>
    </section>
  );
}

/** Bo'lim yopiq yoki til mos emas — tushunarli ekran. */
export function WordbankUnavailable({
  reason,
  message,
}: {
  reason: "off" | "lang" | "error";
  message?: string;
}) {
  const title =
    reason === "error" ? "Ma'lumot yuklanmadi" : "So'z bilish — tez orada";
  const text =
    reason === "lang"
      ? "Hozircha bu bo'lim faqat ingliz tili uchun. Boshqa tillar keyinroq qo'shiladi."
      : reason === "off"
        ? "Bu bo'lim hozircha sinov tariqasida ayrim filiallarda ishlayapti. Tez orada sizga ham ochiladi."
        : message || "Internetni tekshirib, qayta urinib ko'ring.";
  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="student-panel bg-white rounded-3xl p-6 text-center">
        <StudentIcon name="vocabulary" size={56} />
        <p className="text-[19px] font-extrabold text-slate-900 mt-3">{title}</p>
        <p className="text-[13px] text-slate-600 mt-2 leading-relaxed">{text}</p>
        <Link
          to="/student/games"
          className="mt-5 inline-flex min-h-[48px] items-center justify-center rounded-2xl bg-brand-600 px-5 text-white font-bold"
        >
          O'rganishga qaytish
        </Link>
      </div>
    </div>
  );
}
