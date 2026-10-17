import { Link } from "react-router-dom";
import { BadgeCheck, Check, ChevronRight, Trophy } from "lucide-react";
import { StudentIcon } from "../StudentIcon";
import { formatDate } from "../../lib/format";
import { fmtNum } from "../../lib/studentApi";
import { useLearningLanguage } from "../../lib/lang";
import { focusBand, roundEst } from "../../lib/wordbankApi";
import { CertUploadCard } from "./CertUploadCard";
import { useWordbank } from "./useWordbank";

/**
 * SO'Z BILISH — boshqa sahifalardagi kartalar (2026-10-16).
 *
 * Bo'lim bayroq bilan yopiq bo'lsa (server 404) yoki o'quvchi ingliz
 * tilini o'rganmayotgan bo'lsa — kartalar UMUMAN chiqmaydi.
 * 2026-10-17: istisno — profildagi "Sertifikatlarim" boshqa til
 * o'quvchisiga ham chiqadi (TOPIK, Goethe, TORFL natijalari uchun).
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
 * "Sertifikatlarim" (OWNER D3).
 *
 * 2026-10-17: "tez orada" o'rnida haqiqiy karta (CertUploadCard).
 * "So'z bilish: N" yonida FAQAT tasdiqlangan sertifikatlar (me.certs)
 * ✓ bilan turadi; tekshirilayotganlar faqat SON sifatida
 * (me.certs_pending) — ball hech qachon ko'rinmaydi.
 */
export function WordbankProfileSection() {
  const lang = useLearningLanguage();
  const { state, reload } = useWordbank(true);
  if (state?.status !== "ok") return null;
  const d = state.data;
  // Boshqa til o'quvchisi (TOPIK, Goethe, TORFL...) ham sertifikatini
  // yuklay olsin — so'zlar soni yo'q, faqat "Sertifikatlarim"
  if (lang !== "en") {
    return (
      <section className="student-panel bg-white rounded-3xl p-4">
        {(d.certs || []).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-1">
            {(d.certs || []).map((c) => (
              <span key={c.id}
                    className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 px-2.5 py-1 text-[12px] font-extrabold">
                <BadgeCheck size={14} className="text-emerald-600" /> {c.label}
                <span className="font-semibold text-emerald-600">· tasdiqlangan</span>
              </span>
            ))}
          </div>
        )}
        <CertUploadCard onChange={reload} bare />
      </section>
    );
  }
  const done = d.bands.filter((b) => b.done);
  const t = d.size_test;
  const certs = d.certs || [];
  const pending = d.certs_pending || 0;
  const best = d.best_known || 0;

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

      {/* Tasdiqlangan natijalar — "So'z bilish: N" yonida (D3) */}
      {(certs.length > 0 || pending > 0 || best > d.known) && (
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          {certs.map((c) => (
            <span key={c.id}
                  className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 px-2.5 py-1 text-[12px] font-extrabold">
              <BadgeCheck size={14} className="text-emerald-600" /> {c.label}
              <span className="font-semibold text-emerald-600">· tasdiqlangan</span>
            </span>
          ))}
          {pending > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 px-2.5 py-1 text-[11.5px] font-bold">
              {pending} ta sertifikat tekshirilmoqda
            </span>
          )}
          {best > d.known && (
            <span className="inline-flex items-center rounded-full bg-slate-100 text-slate-600 px-2.5 py-1 text-[11.5px] font-bold">
              Eng yaxshi natija: {fmtNum(best)}
            </span>
          )}
        </div>
      )}

      {/* Reytingdagi o'rin (Jami) — reytingga havola */}
      {d.ranks && (d.ranks.group || d.ranks.branch) && (
        <Link to="/student/leaderboard?board=words"
              className="mt-2.5 flex items-center gap-2 rounded-xl bg-brand-50 px-3 min-h-[44px] text-[12.5px] text-brand-700">
          <Trophy size={15} className="text-brand-600 shrink-0" />
          <span className="flex-1 min-w-0">
            {d.ranks.group ? <>Guruhda <b>{d.ranks.group}-o'rin</b></> : null}
            {d.ranks.group && d.ranks.branch ? " · " : null}
            {d.ranks.branch ? <>Filialda <b>{d.ranks.branch}-o'rin</b></> : null}
          </span>
          <ChevronRight size={15} className="text-brand-400 shrink-0" />
        </Link>
      )}

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
      <CertUploadCard onChange={reload} />
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
