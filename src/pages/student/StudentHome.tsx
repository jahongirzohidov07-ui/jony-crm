import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell, ChevronDown, ChevronRight, Flame, Globe, Map as MapIcon,
  Play, Sparkles, CreditCard, Check, BookOpen,
} from "lucide-react";
import { getLang, setLang, LANGS } from "../../lib/lang";
import { Flag } from "../../components/Flag";
import { CoinIcon } from "../../components/CoinIcon";
import { NpsCard } from "../../components/NpsCard";
import { GoalCard } from "../../components/GoalCard";
import { api } from "../../lib/api";
import { fmtNum, type StudentHome as Home } from "../../lib/studentApi";

/**
 * JONY STUDENT — BOSH EKRAN (2026-08-16 da to'liq qayta yozildi).
 *
 * Jahongir bergan tanqid va yangi dizayn:
 *
 *   "hozircha u 'gamification app'dan ko'ra chiroyli elektron
 *   kabinetga yaqinroq ... O'quvchi coinni qayerda ishlatishini, XP
 *   nima berishini bilmaydi ... Bosh sahifada balans juda katta
 *   e'tibor olgan ... 'Bugun' bloki juda bo'sh."
 *
 * Shunga ko'ra tartib qat'iy o'zgardi:
 *   1. Salomlashuv
 *   2. Daraja va progress (foiz + son bilan)
 *   3. Kunlik maqsad (0/3 halqa, mukofot ko'rinib turadi)
 *   4. Coin / XP / Streak — uchtasi ham BOSILADI
 *   5. Davom ettirish
 *   6. To'lov — eng pastda, kichkina qatorda
 *
 * To'lov ataylab pastga tushirildi: qizil karta tepada turganda
 * butun ilova "qarzdorlik ilovasi"dek ko'rinardi. Ma'lumot
 * yo'qolmadi — faqat o'z o'rniga o'tdi.
 */

export default function StudentHome() {
  const [d, setD] = useState<Home | null>(null);
  const [err, setErr] = useState("");
  const [hasNew, setHasNew] = useState(false);
  const [lang, setLangState] = useState(getLang());
  const [langOpen, setLangOpen] = useState(false);

  useEffect(() => {
    api
      .get<{ latest: string | null }>("/student/notifications")
      .then((r) => {
        const seen = localStorage.getItem("jonyos_notif_seen") || "";
        setHasNew(!!r.latest && r.latest > seen);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    api
      .get<Home>("/student/home")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (err)
    return (
      <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>
    );
  if (!d)
    return (
      <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>
    );

  const ov = d.overall;
  const daily = d.daily;
  const cont = d.continue;
  const firstName = (d.name || "").split(" ").slice(-1)[0] || d.name;
  const pct = ov?.next ? Math.round(ov.next.progress_percent) : 100;
  const perLevel = 500; // roles.PRACTICE_POINTS_PER_LEVEL
  const inLevel = ov?.next ? perLevel - ov.next.points_left : perLevel;
  const balance = d.balance;

  return (
    <>
      {/* ================================================ SARLAVHA */}
      <div className="bg-brand-600 text-white px-4 pt-6 pb-14">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2">
            <div className="flex-1 min-w-0 leading-none">
              <p className="text-[19px] font-extrabold tracking-tight">
                JONY
              </p>
              <p className="text-[10px] font-semibold tracking-[0.35em] text-white/80">
                STUDENT
              </p>
            </div>

            <button
              onClick={() => setLangOpen(true)}
              className="h-9 px-3 rounded-full border border-white/40 flex items-center gap-1.5 text-sm font-medium shrink-0"
              aria-label="Til tanlash"
            >
              <Globe size={15} />
              {lang.toUpperCase()}
              <ChevronDown size={14} className="opacity-70" />
            </button>

            <Link
              to="/student/notifications"
              className="relative w-9 h-9 flex items-center justify-center shrink-0"
              aria-label="Bildirishnomalar"
            >
              <Bell size={21} />
              {hasNew && (
                <span className="absolute top-0.5 right-0.5 w-2.5 h-2.5 rounded-full bg-red-500 border-2 border-brand-600" />
              )}
            </Link>

            <Link
              to="/student/profile"
              className="w-11 h-11 rounded-full bg-white/20 border-2 border-white/50 overflow-hidden flex items-center justify-center shrink-0"
            >
              {d.photo ? (
                <img src={d.photo} alt="" className="w-full h-full object-cover" />
              ) : (
                <span className="text-base font-bold">
                  {d.name?.charAt(0) || "?"}
                </span>
              )}
            </Link>
          </div>

          <h1 className="text-xl font-bold mt-4">Salom, {firstName}! 👋</h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-9 pb-6 space-y-4">
        {/* ======================================= DARAJA KARTASI */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-500">Hozirgi daraja</p>
              <p className="text-[30px] font-extrabold text-slate-900 leading-tight mt-0.5">
                {ov?.level?.label || "—"}
              </p>
              <p className="text-sm text-slate-500 mt-0.5">
                CEFR {ov?.level?.cefr} · IELTS{" "}
                {(ov?.level?.ielts || "").replace("~", "")}
              </p>
            </div>
            {/* Qalqon nishoni — CEFR darajasi */}
            <div className="shrink-0 w-16 h-[72px] relative">
              <svg viewBox="0 0 64 72" className="w-full h-full">
                <path
                  d="M32 2 L60 12 V38 C60 54 46 65 32 70 C18 65 4 54 4 38 V12 Z"
                  fill="#EAF2FE"
                  stroke="#C7DDFB"
                  strokeWidth="2"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center pt-1">
                <span className="text-[19px] font-extrabold text-brand-600">
                  {ov?.level?.cefr}
                </span>
                <Sparkles size={11} className="text-brand-400 mt-0.5" />
              </div>
            </div>
          </div>

          {/* Progress: FOIZ ham, SON ham (Jahongir aynan shuni so'radi) */}
          <div className="mt-4 h-7 rounded-full bg-slate-100 relative overflow-hidden">
            <div
              className="h-full bg-brand-600 rounded-full transition-all"
              style={{ width: `${Math.max(pct, 6)}%` }}
            />
            <span
              className="absolute inset-y-0 flex items-center text-xs font-semibold text-slate-600"
              style={{ left: `calc(${Math.max(pct, 6)}% + 10px)` }}
            >
              {pct}%
            </span>
          </div>

          <div className="flex items-center justify-between mt-2.5 text-sm">
            <span className="text-slate-500">
              Keyingi bosqich:{" "}
              <b className="text-brand-600 font-semibold">
                {ov?.next?.label || "Eng yuqori daraja"}
              </b>
            </span>
            {ov?.next && (
              <span className="text-slate-500 shrink-0">
                {inLevel}/{perLevel} XP
              </span>
            )}
          </div>

          <div className="border-t border-slate-100 mt-4 pt-3">
            <Link
              to="/student/roadmap"
              className="flex items-center justify-center gap-2 text-sm font-semibold text-brand-600"
            >
              <MapIcon size={16} />
              Yo'l xaritasi
            </Link>
          </div>
        </div>

        {/* ====================================== BUGUNGI MAQSAD */}
        {daily && (
          <div
            className={`rounded-2xl border p-4 ${
              daily.all_done
                ? "bg-emerald-50 border-emerald-300"
                : "bg-gradient-to-br from-sky-50 via-white to-violet-50 border-brand-200"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="w-14 h-14 rounded-full bg-brand-600 flex items-center justify-center shrink-0">
                {daily.all_done ? (
                  <Check size={26} className="text-white" strokeWidth={3} />
                ) : (
                  <div className="w-7 h-7 rounded-full border-[3px] border-white flex items-center justify-center">
                    <div className="w-2.5 h-2.5 rounded-full bg-white" />
                  </div>
                )}
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-lg font-bold text-slate-900">
                  {daily.all_done ? "Bugungi maqsad bajarildi!" : "Bugungi maqsad"}
                </p>
                <p className="text-sm text-slate-500 mt-0.5 truncate">
                  {daily.next
                    ? `${daily.next.title} · ${daily.next.minutes} daqiqa`
                    : "Ertaga yangi maqsad ochiladi"}
                </p>
                <div className="flex gap-2 mt-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-semibold">
                    ⭐ +{daily.reward_xp} XP
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
                    <CoinIcon size={12} /> +{daily.reward_coin} Coin
                  </span>
                </div>
              </div>

              {/* Halqa: 0/3 */}
              <div className="relative w-[70px] h-[70px] shrink-0">
                <svg viewBox="0 0 70 70" className="w-full h-full -rotate-90">
                  <circle
                    cx="35" cy="35" r="30" fill="none"
                    stroke="#E5E9F0" strokeWidth="7"
                  />
                  <circle
                    cx="35" cy="35" r="30" fill="none"
                    stroke={daily.all_done ? "#10B981" : "#1A6FE4"}
                    strokeWidth="7" strokeLinecap="round"
                    strokeDasharray={`${(daily.percent / 100) * 188.5} 188.5`}
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-brand-600">
                  {daily.done}/{daily.total}
                </span>
              </div>
            </div>

            {!daily.all_done && daily.next && (
              <Link
                to={daily.next.href}
                className="mt-4 w-full h-14 rounded-xl bg-brand-600 text-white font-semibold flex items-center justify-center gap-2.5 active:bg-brand-700"
              >
                <span className="w-7 h-7 rounded-full bg-white/25 flex items-center justify-center">
                  <Play size={14} fill="currentColor" />
                </span>
                Boshlash
              </Link>
            )}

            {/* Uch vazifaning holati */}
            <div className="mt-3 space-y-1.5">
              {daily.tasks.map((t) => (
                <Link
                  key={t.key}
                  to={t.href}
                  className="flex items-center gap-2 text-xs"
                >
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
                      t.done
                        ? "bg-emerald-500 text-white"
                        : "border-2 border-slate-300"
                    }`}
                  >
                    {t.done && <Check size={10} strokeWidth={4} />}
                  </span>
                  <span
                    className={
                      t.done
                        ? "text-slate-400 line-through flex-1"
                        : "text-slate-600 flex-1"
                    }
                  >
                    {t.title}
                  </span>
                  <span className="text-slate-400 shrink-0">
                    {t.done_count}/{t.target}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* ============================== COIN / XP / STREAK ===== */}
        <div className="grid grid-cols-3 gap-2.5">
          <Link
            to="/student/shop"
            className="bg-white rounded-xl border border-slate-200 p-3 active:scale-[0.98] transition"
          >
            <div className="flex items-start justify-between">
              <CoinIcon size={26} />
              <ChevronRight size={16} className="text-slate-300" />
            </div>
            <p className="text-[22px] font-bold text-slate-900 mt-1.5 leading-none">
              {fmtNum(d.gamification?.coins)}
            </p>
            <p className="text-xs text-slate-500 mt-1">Coin</p>
          </Link>

          <Link
            to="/student/roadmap"
            className="bg-white rounded-xl border border-slate-200 p-3 active:scale-[0.98] transition"
          >
            <div className="flex items-start justify-between">
              <Sparkles size={24} className="text-brand-500" />
              <ChevronRight size={16} className="text-slate-300" />
            </div>
            <p className="text-[22px] font-bold text-slate-900 mt-1.5 leading-none">
              {fmtNum(d.gamification?.lifetime_xp)}
            </p>
            <p className="text-xs text-slate-500 mt-1">XP</p>
          </Link>

          <Link
            to="/student/games"
            className="bg-white rounded-xl border border-slate-200 p-3 active:scale-[0.98] transition"
          >
            <div className="flex items-start justify-between">
              <Flame size={24} className="text-orange-500" />
              <ChevronRight size={16} className="text-slate-300" />
            </div>
            <p className="text-[22px] font-bold text-slate-900 mt-1.5 leading-none">
              {d.streak}
              <span className="text-sm font-medium text-slate-500"> kun</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">Streak</p>
          </Link>
        </div>

        {/* ============================== MAQSAD BALLI (2026-08-18,
            Jahongir: "target ballini kirgizsa ... shuncha yil, shuncha
            kun va shuncha soatdan keyin olasan deb") */}
        <GoalCard />

        {/* Streak uchun keyingi qadam */}
        {d.streak === 0 && (
          <p className="text-xs text-slate-400 -mt-1.5 px-1">
            Bugun mashq qilsangiz streak boshlanadi. 7 kun ketma-ket = 50 coin.
          </p>
        )}

        {/* ===================================== DAVOM ETTIRISH */}
        {cont && (
          <div>
            <p className="text-[15px] font-bold text-slate-900 mb-2">
              Davom ettirish
            </p>
            <Link
              to={cont.href}
              className="block bg-white rounded-xl border border-slate-200 p-4 active:scale-[0.99] transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center shrink-0">
                  <BookOpen size={24} className="text-emerald-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-base font-bold text-slate-900 truncate">
                    {cont.title}
                  </p>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {cont.subtitle} · {cont.solved}/{cont.total}
                  </p>
                </div>
                <ChevronRight size={20} className="text-slate-300 shrink-0" />
              </div>

              <div className="h-2 rounded-full bg-slate-100 mt-3 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${cont.percent}%` }}
                />
              </div>

              <div className="flex items-center justify-between mt-3">
                <span className="text-xs text-slate-400">
                  🕐 Taxminan {cont.minutes} daqiqa · +{cont.xp} XP
                </span>
                <span className="px-4 py-2 rounded-lg border border-brand-500 text-brand-600 text-sm font-semibold">
                  Davom etish
                </span>
              </div>
            </Link>
          </div>
        )}

        <NpsCard />

        {/* ============ TO'LOV — eng pastda, kichik qatorda ====== */}
        {typeof balance === "number" && balance < 0 && (
          <Link
            to="/student/profile"
            className="flex items-center gap-2.5 bg-red-50 border border-red-200 rounded-xl px-3.5 py-3"
          >
            <span className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center shrink-0">
              <CreditCard size={16} className="text-red-500" />
            </span>
            <span className="text-sm font-semibold text-red-600 flex-1">
              To'lov muddati keldi
            </span>
            <span className="text-sm text-red-600 underline">Ko'rish</span>
            <ChevronRight size={16} className="text-red-400" />
          </Link>
        )}
      </div>

      {/* ------------------------------------------ TIL TANLASH */}
      {langOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 flex items-end justify-center"
          onClick={() => setLangOpen(false)}
        >
          <div
            className="w-full max-w-md bg-white rounded-t-2xl p-4 pb-8"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Qaysi tilni o'rganyapsiz?
            </p>
            <div className="space-y-1.5">
              {LANGS.map((l) => (
                <button
                  key={l.code}
                  onClick={() => {
                    setLang(l.code);
                    setLangState(l.code);
                    setLangOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 rounded-xl border p-3.5 text-left ${
                    lang === l.code
                      ? "border-brand-400 bg-brand-50"
                      : "border-slate-200"
                  }`}
                >
                  <Flag code={l.code} size={28} />
                  <span className="text-sm font-medium text-slate-800 flex-1">
                    {l.label}
                  </span>
                  {lang === l.code && (
                    <span className="text-xs font-semibold text-brand-600">
                      Tanlangan
                    </span>
                  )}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-3">
              Lug'at mashqlari tanlangan tilda bo'ladi. Grammatika hozircha
              ingliz tilida.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
