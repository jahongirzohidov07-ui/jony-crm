import { useEffect, useState } from "react";
import { formatDate } from "../../lib/format";
import { NpsCard } from "../../components/NpsCard";
import { Link } from "react-router-dom";
import { getLang, setLang, LANGS } from "../../lib/lang";
import { Flag } from "../../components/Flag";
import { CoinIcon } from "../../components/CoinIcon";
import { Lock as LockIcon, Bell,
  ChevronDown, ChevronRight, Flame, Sparkles, Trophy,
  } from "lucide-react";
import type { ReactNode } from "react";
import { api } from "../../lib/api";
import { BrandIcon } from "../../components/BrandIcon";
import {
  fmtNum, TONE_BAR, type SkillProgress, type StudentHome as Home,
} from "../../lib/studentApi";

/**
 * JONY STUDENT — bosh ekran (2026-08-09).
 *
 * Jahongir aynan shuni so'radi: "o'quvchiga umumiy darajasi va ustiga
 * bosganda har bir bo'limdan alohida darajalari progress ko'rinib
 * tursin, qachon keyingi darajaga yetadi qancha qoldi."
 * Shuning uchun umumiy daraja kartasi BOSILADI va ichidan olti
 * ko'nikma (lug'at, grammatika, o'qish, tinglash, yozish, gapirish)
 * har biri o'z progress chizig'i bilan ochiladi.
 */
export default function StudentHome() {
  const [d, setD] = useState<Home | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(false);

  const [hasNew, setHasNew] = useState(false);
  const [lang, setLangState] = useState(getLang());
  const [langOpen, setLangOpen] = useState(false);
  const [lockMsg, setLockMsg] = useState<any>(null);

  useEffect(() => {
    // Yangi bildirishnoma bormi - oxirgi ko'rilgan vaqt bilan
    // solishtiramiz (sahifasi ochilganda o'sha vaqt yangilanadi)
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
    return <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>;

  const ov = d.overall;

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-12">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2 mb-4 opacity-90">
            <BrandIcon size={18} className="rounded-md" />
            <span className="text-sm font-medium">Jony Student</span>
          </div>
          {/* ENG TEPADA: rasm + ism (2026-08-10, Jahongir). Bosilsa
              profil ochiladi - rasm qo'yish/ism o'zgartirish o'sha
              yerda. */}
          <div className="flex items-center gap-3">
          <Link to="/student/profile" className="flex items-center gap-3 flex-1 min-w-0">
            <div className="w-14 h-14 rounded-full bg-white/20 border-2 border-white/40 overflow-hidden flex items-center justify-center shrink-0">
              {(d as any).photo ? (
                <img
                  src={(d as any).photo}
                  alt=""
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-xl font-bold">
                  {d.name?.charAt(0) || "?"}
                </span>
              )}
            </div>
            <div className="min-w-0">
              <h1 className="text-xl font-semibold truncate">{d.name}</h1>
              <p className="text-sm opacity-90 mt-0.5">
                {d.group || "guruh biriktirilmagan"}
                {d.level_label ? ` · ${d.level_label}` : ""}
              </p>
            </div>
          </Link>
          {/* BAYROQ (2026-08-11): o'rganilayotgan til. Bosilsa
              tanlash oynasi ochiladi - lug'at shu tilga o'tadi. */}
          <button
            onClick={() => setLangOpen(true)}
            className="w-11 h-11 rounded-full bg-white/15 flex items-center justify-center shrink-0"
            aria-label="Til tanlash"
          >
            <Flag code={lang} size={22} />
          </button>
          {/* QO'NG'IROQCHA (2026-08-10, Jahongir): to'lov vaqti va
              imtihon natijasi xabarlari. Qizil nuqta - oxirgi
              ko'rilgandan keyin yangi xabar bor degani. */}
          <Link
            to="/student/notifications"
            className="relative w-11 h-11 rounded-full bg-white/15 flex items-center justify-center shrink-0"
            aria-label="Bildirishnomalar"
          >
            <Bell size={20} />
            {hasNew && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-red-500 border-2 border-brand-600" />
            )}
          </Link>
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 space-y-4">
        <div className="-mt-6 mb-4"><NpsCard /></div>
        {/* --- BALANS (2026-08-10, Jahongir: "bosh sahifada balansi
            ko'rinib turishi kerak"). Manfiy - qizil, to'lov
            eslatmasi bilan. --- */}
        {typeof (d as any).balance === "number" && (
          <Link
            to="/student/profile"
            className={`flex items-center justify-between rounded-2xl shadow-sm border p-4 ${
              (d as any).balance < 0
                ? "bg-red-50 border-red-200"
                : "bg-white border-slate-200"
            }`}
          >
            <div>
              <p className="text-xs text-slate-500">Balansingiz</p>
              <p
                className={`text-xl font-bold leading-tight ${
                  (d as any).balance < 0 ? "text-red-600" : "text-slate-900"
                }`}
              >
                {Math.round((d as any).balance).toLocaleString("ru-RU")} so'm
              </p>
              {(d as any).balance < 0 && (
                <p className="text-[11px] text-red-500 mt-0.5">
                  To'lov vaqti keldi — administratorga murojaat qiling
                </p>
              )}
            </div>
            <span className="text-xs font-medium text-brand-600 shrink-0">
              Tarix →
            </span>
          </Link>
        )}

        {/* --- CHEGIRMA (2026-08-12, Jahongir: "o'quvchiga chegirmani
            nega olgani va qancha chegirmasi qachongacha borligi
            ko'rinib tursin"). Yashirin (individual) chegirmalar
            serverdan umuman kelmaydi. --- */}
        {((d as any).discounts || []).length > 0 && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4">
            {((d as any).discounts || []).map((ds: any, i: number) => (
              <div key={i} className={i > 0 ? "mt-2 pt-2 border-t border-emerald-100" : ""}>
                <p className="text-sm font-bold text-emerald-800">
                  🎁 Chegirmangiz:{" "}
                  {ds.percent
                    ? `${ds.percent}%`
                    : `${Math.round(ds.amount || 0).toLocaleString("ru-RU")} so'm`}
                </p>
                <p className="text-[12px] text-emerald-700 mt-0.5">
                  {ds.reason}
                </p>
                <p className="text-[11px] text-emerald-600 mt-0.5">
                  {ds.until
                    ? `${formatDate(ds.until)} gacha amal qiladi`
                    : "Muddatsiz"}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* --- UMUMIY DARAJA: bosilsa ko'nikmalar ochiladi --- */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <button
            onClick={() => setOpen((v) => !v)}
            className="w-full text-left p-5 active:bg-slate-50 transition"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-slate-500">Umumiy darajangiz</p>
                <p className="text-2xl font-bold text-slate-900 leading-tight">
                  {ov.level.label}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  IELTS {ov.level.ielts} · CEFR {ov.level.cefr}
                </p>
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-brand-600 shrink-0 mt-1">
                Bo'limlar
                {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
              </span>
            </div>

            {ov.max_level ? (
              <p className="mt-4 text-sm font-medium text-emerald-600">
                Eng yuqori daraja 🎉
              </p>
            ) : (
              <div className="mt-4">
                <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                  <span>Keyingi: {ov.next!.label}</span>
                  <span className="font-medium text-slate-700">
                    yana {fmtNum(ov.next!.points_left)} ball
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-600"
                    style={{ width: `${ov.next!.progress_percent}%` }}
                  />
                </div>
              </div>
            )}
          </button>

          {open && (
            <div className="border-t border-slate-100 p-4 space-y-3.5 bg-slate-50/60">
              <p className="text-[11px] text-slate-400">
                Har bir bo'lim alohida hisoblanadi
              </p>
              {d.skills.map((s) => (
                <SkillRow key={s.key} s={s} />
              ))}
            </div>
          )}
        </div>

        {/* --- Statistika (2026-08-11: yorqin gradientlar) --- */}
        <div className="grid grid-cols-2 gap-3">
          <Stat
            icon={<CoinIcon size={22} />}
            tone="from-amber-400 to-orange-500"
            value={fmtNum(d.gamification.coins)}
            label="Coin"
          />
          <Stat
            icon={<Sparkles size={19} />}
            tone="from-violet-500 to-purple-600"
            value={fmtNum(d.gamification.lifetime_xp)}
            label="XP"
          />
          <Stat
            icon={<Flame size={19} />}
            tone="from-orange-500 to-red-500"
            value={`${d.streak} kun`}
            label="Ketma-ket"
          />
          <Stat
            icon={<Trophy size={19} />}
            tone="from-emerald-500 to-teal-600"
            value={
              d.ranks.group_rank
                ? `${d.ranks.group_rank}/${d.ranks.group_total}`
                : "—"
            }
            label="Guruhda"
          />
        </div>

        {/* --- Bugun --- */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-800">Bugun</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {d.today.answered === 0
                  ? "Hali mashq qilmadingiz"
                  : `${d.today.correct} to'g'ri / ${d.today.answered} javob`}
              </p>
            </div>
            <Link
              to="/student/games"
              className="text-xs font-medium px-3.5 py-2 rounded-lg bg-brand-600 text-white shrink-0"
            >
              Mashq qilish
            </Link>
          </div>
        </div>

        {/* CEFR / IELTS QULFLARI (2026-08-11): "Bugun mashq qil"
            kartasining TAGIDA, har biri alohida qatorda. */}
        <div className="space-y-2">
          {[
            {
              key: "cefr",
              label: "CEFR",
              hint: "Til darajasi imtihoniga tayyorgarlik",
              needIdx: 2,
              needLabel: "PRE-INTERMEDIATE",
            },
            {
              key: "ielts",
              label: "IELTS",
              hint: "Xalqaro imtihonga tayyorgarlik",
              needIdx: 3,
              needLabel: "INTERMEDIATE",
            },
          ].map((c) => {
            const levels = [
              "beginner", "elementary", "pre_intermediate",
              "intermediate", "upper_intermediate", "advanced",
              "native",
            ];
            const myIdx = levels.indexOf(
              (d as any).overall?.level?.key || "beginner",
            );
            const open = myIdx >= c.needIdx;
            return (
              <button
                key={c.key}
                onClick={() => setLockMsg(c as any)}
                className={`w-full flex items-center gap-3 rounded-2xl border p-4 text-left ${
                  open
                    ? "bg-white border-emerald-200"
                    : "bg-slate-50 border-dashed border-2 border-slate-300"
                }`}
              >
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    open
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-200 text-slate-500"
                  }`}
                >
                  <LockIcon size={17} />
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-sm font-bold ${
                      open ? "text-emerald-700" : "text-slate-600"
                    }`}
                  >
                    {c.label}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {c.hint}
                  </p>
                </div>
                <span
                  className={`text-[11px] font-semibold shrink-0 ${
                    open ? "text-emerald-600" : "text-slate-400"
                  }`}
                >
                  {open ? "Ochilgan" : "Qulf"}
                </span>
              </button>
            );
          })}
        </div>

      </div>

      {/* ---- CEFR/IELTS QULF XABARI ---- */}
      {lockMsg && (
        <div
          className="fixed inset-0 bg-black/40 z-40 flex items-center justify-center px-6"
          onClick={() => setLockMsg(null)}
        >
          <div
            className="w-full max-w-sm bg-white rounded-2xl p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-base font-bold text-slate-900 mb-1.5">
              {lockMsg.label} bo'limi
            </p>
            <p className="text-sm text-slate-600 leading-relaxed">
              Bu bo'lim ochilishi uchun sizning darajangiz kamida{" "}
              <b>{lockMsg.needLabel}</b> bo'lishi kerak. Mashqlarni
              bajarib darajangizni oshiring!
            </p>
            <button
              onClick={() => setLockMsg(null)}
              className="w-full mt-4 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold"
            >
              Tushunarli
            </button>
          </div>
        </div>
      )}

      {/* ---- TIL TANLASH ---- */}
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
              Lug'at mashqlari tanlangan tilda bo'ladi. Grammatika
              hozircha ingliz tilida.
            </p>
          </div>
        </div>
      )}
    </>
  );
}

function SkillRow({ s }: { s: SkillProgress }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <span className="text-sm text-slate-700">{s.label}</span>
        <span className="text-xs font-medium text-slate-800">
          {s.level.label}
        </span>
      </div>
      <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
        <div
          className={`h-full rounded-full ${TONE_BAR[s.tone] || TONE_BAR.slate}`}
          style={{ width: `${s.next ? s.next.progress_percent : 100}%` }}
        />
      </div>
      <p className="text-[11px] text-slate-400 mt-1">
        {s.max_level
          ? "Eng yuqori daraja 🎉"
          : `${s.level.label} → ${s.next!.label} · yana ${fmtNum(
              s.next!.points_left,
            )} ball`}
      </p>
    </div>
  );
}

function Stat({
  icon,
  tone,
  value,
  label,
}: {
  icon: ReactNode;
  tone: string;
  value: string;
  label: string;
}) {
  return (
    <div
      className={`bg-gradient-to-br ${tone} rounded-2xl shadow-sm p-3.5 text-white`}
    >
      <div className="w-9 h-9 rounded-xl bg-white/25 flex items-center justify-center mb-2">
        {icon}
      </div>
      <p className="text-xl font-bold leading-tight">
        {value}
      </p>
      <p className="text-[11px] text-slate-500">{label}</p>
    </div>
  );
}
