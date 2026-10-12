import { hasUnreadNotifications, type NotificationFeed } from "../../lib/studentNotifications";
import { StudentLevelBadge } from "../../components/StudentLevelBadge";
import { StudentLoading, StudentLoadError } from "../../components/StudentLoading";
import { StudentIcon } from "../../components/StudentIcon";
import { StudentImage } from "../../components/StudentIcon";
import { StudentXpHelp } from "../../components/StudentXpHelp";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell, ChevronDown, ChevronRight, Map as MapIcon, Check, CreditCard,
} from "lucide-react";
import { useLearningLanguage, setLang, LANGS } from "../../lib/lang";
import { Flag } from "../../components/Flag";
import { StudentCoinIcon as CoinIcon } from "../../components/StudentIcon";
import { NpsCard } from "../../components/NpsCard";
import { GoalCard } from "../../components/GoalCard";
import { JsaLogo, XpHex, JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import { PushBanner } from "../../components/PushBanner";
import { fmtNum, type StudentHome as Home } from "../../lib/studentApi";

/**
 * JONY STUDENT — BOSH EKRAN.
 *
 * 2026-08-20: Jahongir to'liq dizayn to'plamini berdi ("dizaynini
 * toliq tashladim papkada 1ga 1 qilib ber") - ekran "Bosh sahifa.png"
 * bo'yicha TO'Q KO'K temada qayta terildi. Ma'lumot va mantiq
 * o'zgarmadi: /student/home, kunlik missiya, coin/XP/streak,
 * IELTS maqsad, davom etish - hammasi avvalgi joyidan olinadi.
 */

const MISSION_ICONS = ["vocabulary", "grammar", "listening"] as const;

/** Ochiq imtihon (bosh sahifa banneri) — /student/home dagi exam_live */
type ExamLive = {
  token: string;
  title: string;
  group?: string;
  state: "waiting" | "countdown" | "running" | string;
  duration_min?: number | null;
  q_count?: number;
  my_status?: string;
};

export default function StudentHome() {
  const [d, setD] = useState<Home | null>(null);
  const [err, setErr] = useState("");
  const [hasNew, setHasNew] = useState(false);
  const lang = useLearningLanguage();
  const [langOpen, setLangOpen] = useState(false);

  useEffect(() => {
    api
      .get<NotificationFeed>("/student/notifications")
      .then((r) => {
        setHasNew(hasUnreadNotifications(r));
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
      <StudentLoadError message={err} />
    );
  if (!d)
    return (
      <StudentLoading />
    );

  const ov = d.overall;
  const daily = d.daily;
  const cont = lang === "en" ? d.continue : null;
  const firstName = (d.name || "").split(" ").slice(-1)[0] || d.name;
  const pct = ov?.next ? Math.round(ov.next.progress_percent) : 100;
  // 2026-08-25: daraja oralig'i endi har darajada har xil — 500 deb
  // qotirib qo'yish noto'g'ri edi (roles.ENG_LEVEL_POINTS).
  const lvFrom = ov?.level_from ?? 0;
  const lvTo = ov?.next?.need ?? ov?.level_to ?? lvFrom;
  const perLevel = Math.max(1, lvTo - lvFrom);
  const inLevel = ov?.next ? perLevel - ov.next.points_left : perLevel;
  const lg = d.gamification?.league;
  const balance = d.balance;
  const xp = d.gamification?.lifetime_xp ?? 0;

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  return (
    <>
      <div className="max-w-md mx-auto px-4 pt-5 pb-6 space-y-4">
        {/* ============================================= SARLAVHA */}
        <div className="flex items-center gap-2">
          <div className="flex-1 min-w-0">
            <JsaLogo />
          </div>
          <button
            onClick={() => setLangOpen(true)}
            className="h-10 px-3 rounded-xl border flex items-center gap-1.5 text-sm font-semibold text-white shrink-0"
            style={card}
            aria-label="Til tanlash"
          >
            {lang.toUpperCase()}
            <ChevronDown size={14} className="opacity-70" />
          </button>
          <Link
            to="/student/notifications"
            className="relative w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
            style={card}
            aria-label="Bildirishnomalar"
          >
            <Bell size={19} />
            {hasNew && (
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-red-500" />
            )}
          </Link>
          <Link
            to="/student/profile"
            className="w-11 h-11 rounded-full bg-brand-600 border-2 border-brand-400 overflow-hidden flex items-center justify-center shrink-0"
          >
            {d.photo ? (
              <StudentImage src={d.photo} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="text-base font-bold text-white">
                {d.name?.charAt(0) || "?"}
              </span>
            )}
          </Link>
        </div>

        <PushBanner />

        {/* ====================================== SALOM + UMUMIY XP */}
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-[26px] font-extrabold text-white leading-tight">
              Salom, {firstName}! 👋
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Bugun maqsadingizga bir qadam yaqinlashing.
            </p>
          </div>
          <div className="rounded-2xl border px-3.5 py-2.5 text-center shrink-0"
               style={card}>
            <p className="text-[11px] text-slate-400">Umumiy XP</p>
            <p className="flex items-center gap-1.5 mt-1">
              <XpHex size={18} />
              <b className="text-white text-[17px]">{fmtNum(xp)}</b>
            </p>
          </div>
        </div>

        {/* ============ OCHIQ IMTIHON (2026-09-25, Jahongir: "cherer
            Student app qiladigan qilish kerak link ham shu Student appga
            keladigan qilaylik") — examiner guruh uchun test ochgan bo'lsa
            shu yerda banner: link shart emas, bir bosishda kiradi. */}
        {((d as unknown as { exam_live?: ExamLive[] }).exam_live || []).map((ex) => (
          <Link
            key={ex.token}
            to={`/student/exam/${encodeURIComponent(ex.token)}`}
            className="block rounded-3xl p-4 border-2 active:scale-[0.99] transition"
            style={{
              background: ex.state === "running"
                ? "linear-gradient(120deg,#B91C1C 0%,#DC2626 100%)"
                : "linear-gradient(120deg,#B45309 0%,#D97706 100%)",
              borderColor: "rgba(255,255,255,0.35)",
            }}
          >
            <div className="flex items-center gap-3">
              <span className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center text-[24px] shrink-0">
                📝
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-bold text-white/80 uppercase tracking-wide">
                  {ex.state === "running" ? "Imtihon ketyapti" : "Imtihon ochildi"}
                </p>
                <p className="text-[17px] font-extrabold text-white truncate">{ex.title}</p>
                <p className="text-[12px] text-white/85 mt-0.5">
                  {ex.state === "running"
                    ? "Hoziroq kiring — vaqt ketyapti"
                    : ex.my_status === "in_progress"
                      ? "Siz kirgansiz — examiner Start bosishini kuting"
                      : "Rasmingizni olib, examiner Start bosishini kuting"}
                  {ex.duration_min ? ` · ${ex.duration_min} daqiqa` : ""}
                </p>
              </div>
              <ChevronRight size={22} className="text-white shrink-0" />
            </div>
          </Link>
        ))}

        {/* ======================================= DARAJA KARTASI */}
        {lang !== "ru" && <div
          className="student-hero student-pattern rounded-3xl p-5 relative overflow-hidden"
          style={{
            background:
              "linear-gradient(120deg,#2B50E0 0%,#4A56EC 55%,#7B5CF0 100%)",
          }}
        >
          <div className="flex items-center gap-4">
            {/* Qalqon */}
            <StudentLevelBadge level={ov?.level?.cefr} size={86} />

            <div className="min-w-0 flex-1">
              <p className="text-[27px] font-extrabold text-white leading-tight truncate">
                {ov?.level?.label || "—"}
              </p>
              <p className="text-[15px] text-white/85 mt-1">
                Daraja balli <b className="text-white">{fmtNum(inLevel)}</b>
                <span className="text-white/70"> / {perLevel}</span>
              </p>
              <StudentXpHelp />
              <div className="flex items-center gap-2.5 mt-2.5">
                <div className="h-2.5 flex-1 rounded-full bg-white/25 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-white"
                    style={{ width: `${Math.max(pct, 4)}%` }}
                  />
                </div>
                <b className="text-white text-sm shrink-0">{pct}%</b>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 mt-3.5">
            <p className="text-[13px] text-white/85 flex-1 min-w-0">
              {ov?.next ? (
                <>
                  {ov.next.label}'gacha{" "}
                  <b className="text-sky-200">{ov.next.points_left} ball</b> qoldi
                </>
              ) : (
                "Eng yuqori darajadasiz 🏆"
              )}
            </p>
            <Link
              to="/student/roadmap"
              className="inline-flex items-center gap-2 rounded-xl border border-white/50 px-3.5 py-2 text-sm font-semibold text-white shrink-0"
            >
              <MapIcon size={15} />
              Yo'l xaritasi
            </Link>
          </div>
        </div>}

        {lang === "ru" && <Link to="/student/russian"
          className="block rounded-3xl border border-blue-400/40 bg-gradient-to-br from-blue-700 to-indigo-800 p-5 text-white">
          <p className="text-xs font-bold uppercase tracking-wide text-blue-100">Rus tili · 1 yillik kurs</p>
          <h2 className="text-2xl font-extrabold mt-2">Suhbatdan boshlaymiz</h2>
          <p className="text-sm text-blue-100 mt-2">12 oy · 144 dars. Darsingizga mos iboralar, grammatika va dialoglar.</p>
          <span className="inline-flex items-center gap-2 mt-4 font-semibold">Dars va mashqlarni ochish <ChevronRight size={18} /></span>
        </Link>}

        {/* ====================================== BUGUNGI MISSIYA */}
        {daily && lang !== "ru" && (
          <div className="student-panel student-pattern bg-white rounded-3xl p-4">
            <div className="flex items-center gap-3">
              <StudentIcon name="mission" size={48} />
              <p className="text-[19px] font-extrabold text-slate-900 flex-1">
                Bugungi missiya
              </p>
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold shrink-0 ${
                  daily.all_done
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-slate-100 text-slate-600"
                }`}
              >
                {daily.all_done && <Check size={11} className="inline mr-0.5 -mt-0.5" />}
                {daily.done}/{daily.total}
                {daily.all_done ? " bajarildi" : ""}
              </span>
            </div>

            <div className="flex justify-end gap-2 mt-2">
              <span className="px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold inline-flex items-center gap-1">
                +{daily.reward_xp} XP <XpHex size={13} />
              </span>
              <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-bold inline-flex items-center gap-1">
                +{daily.reward_coin} Coin <CoinIcon size={13} />
              </span>
            </div>

            <div className="mt-3 space-y-2">
              {daily.tasks.map((t, i) => (
                <Link
                  key={t.key}
                  to={t.href}
                  className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50/70 px-3 py-3"
                >
                  <StudentIcon name={MISSION_ICONS[i % 3]} size={36} />
                  <span className="text-[15px] font-semibold text-slate-800 flex-1 min-w-0 truncate">
                    {t.title}
                  </span>
                  <b
                    className={`text-sm shrink-0 ${
                      t.done ? "text-emerald-600" : "text-slate-500"
                    }`}
                  >
                    {t.done_count}/{t.target}
                  </b>
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                      t.done
                        ? "bg-emerald-500 text-white"
                        : "border-2 border-slate-300"
                    }`}
                  >
                    {t.done && <Check size={14} strokeWidth={3.5} />}
                  </span>
                </Link>
              ))}
            </div>

            {!daily.all_done && daily.next && (
              <Link
                to={daily.next.href}
                className="mt-3 w-full h-12 rounded-xl bg-brand-600 text-white font-semibold flex items-center justify-center gap-2 active:bg-brand-700"
              >
                Boshlash — {daily.next.title}
              </Link>
            )}
          </div>
        )}

        {/* ============================== COIN / XP / STREAK ===== */}
        <div className="student-home-stats grid grid-cols-3 gap-2.5">
          <Link
            to="/student/shop"
            className="rounded-2xl border p-3.5 active:scale-[0.98] transition"
            style={card}
          >
            <CoinIcon size={30} />
            <p className="text-[21px] font-extrabold text-white mt-2 leading-none">
              {fmtNum(d.gamification?.coins)}
            </p>
            <p className="text-xs text-slate-400 mt-1">Coin</p>
          </Link>

          <Link
            to="/student/roadmap"
            className="rounded-2xl bg-brand-600 p-3.5 active:scale-[0.98] transition"
          >
            <XpHex size={30} />
            <p className="text-[21px] font-extrabold text-white mt-2 leading-none">
              {fmtNum(xp)}
            </p>
            <p className="text-xs text-white/75 mt-1">XP</p>
          </Link>

          <Link
            to="/student/games"
            className="rounded-2xl border p-3.5 active:scale-[0.98] transition"
            style={card}
          >
            <StudentIcon name="streak" size={32} />
            <p className="text-[21px] font-extrabold text-white mt-2 leading-none">
              {d.streak}{" "}
              <span className="text-sm font-semibold text-slate-400">kun</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">Streak</p>
          </Link>
        </div>

        {/* ================================ LIGA (2026-08-25) ==== */}
        {/* Jahongir: "ligasini ham bosh sahifani qayerigadur qo'shish
            kerak" — coin ligaga ko'tarilganda beriladi, shuning
            uchun liga bosh sahifada, XP kartasining yonida turadi. */}
        {lg && (
          <Link
            to="/student/leagues"
            className="flex items-center gap-3 rounded-2xl border p-4 active:scale-[0.99] transition"
            style={card}
          >
            <span className="text-[30px] leading-none shrink-0">
              {lg.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-[11px] text-slate-400">Ligangiz</p>
              <p className="text-white font-extrabold text-[17px] truncate">
                {lg.name}
              </p>
              {d.gamification?.next_league && (
                <>
                  <div className="h-1.5 rounded-full bg-slate-700/60 overflow-hidden mt-1.5">
                    <div
                      className="h-full rounded-full bg-amber-400"
                      style={{
                        width: `${Math.max(
                          d.gamification.league_percent || 0, 3)}%`,
                      }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {d.gamification.next_league.name} ligasigacha{" "}
                    <b className="text-amber-300">
                      {fmtNum(d.gamification.league_to_next || 0)} XP
                    </b>
                  </p>
                </>
              )}
              {d.gamification?.max_league && (
                <p className="text-[11px] text-amber-300 mt-1">
                  Eng yuqori liga 🏆
                </p>
              )}
            </div>
            <ChevronRight size={18} className="text-slate-500 shrink-0" />
          </Link>
        )}

        {/* ===================== MAQSAD: IELTS (GoalCard) ======== */}
        {lang === "en" && <GoalCard />}

        {d.streak === 0 && lang !== "ru" && (
          <p className="text-xs text-slate-500 -mt-1.5 px-1">
            Bugun mashq qilsangiz streak boshlanadi. 7 kun ketma-ket = 50 coin.
          </p>
        )}

        {/* ===================================== DAVOM ETTIRISH */}
        {cont && (
          <Link
            to={cont.href}
            className="block bg-white rounded-3xl p-4 active:scale-[0.99] transition"
          >
            <div className="flex items-center gap-3">
              <StudentIcon name="grammar" size={48} />
              <div className="min-w-0 flex-1">
                <p className="text-[17px] font-extrabold text-slate-900 truncate">
                  {cont.title}
                </p>
                <p className="text-sm mt-0.5">
                  <span className="text-violet-600 font-semibold">
                    {cont.subtitle}
                  </span>
                </p>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                  <span>◔ {cont.solved}/{cont.total}</span>
                  <span>·</span>
                  <span>🕐 {cont.minutes} daqiqa</span>
                  <span>·</span>
                  <span className="inline-flex items-center gap-0.5">
                    <XpHex size={11} /> +{cont.xp} XP
                  </span>
                </p>
              </div>
              <span className="px-4 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-bold shrink-0">
                Davom etish
              </span>
            </div>
          </Link>
        )}

        <NpsCard />

        {typeof balance === "number" && balance < 0 && (
          <Link
            to="/student/payments"
            className="flex items-center gap-2.5 bg-red-500/10 border border-red-500/40 rounded-2xl px-3.5 py-3"
          >
            <span className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center shrink-0">
              <CreditCard size={16} className="text-red-400" />
            </span>
            <span className="text-sm font-semibold text-red-400 flex-1">
              To'lov muddati keldi
            </span>
            <ChevronRight size={16} className="text-red-400" />
          </Link>
        )}
      </div>

      {/* ------------------------------------------ TIL TANLASH */}
      {langOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 flex items-end justify-center"
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
              Lug‘at, grammatika va mavjud ko‘nikma mashqlari tanlangan tilga mos ochiladi.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
