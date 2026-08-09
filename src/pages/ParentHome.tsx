import { Link, useOutletContext } from "react-router-dom";
import {
  ChevronRight,
  ClipboardCheck,
  Coins,
  Download,
  Snowflake,
  Trophy,
  Wallet,
  X,
} from "lucide-react";
import type { ReactNode } from "react";
import { BrandIcon } from "../components/BrandIcon";
import type { ParentCtx } from "./Parent";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const AT: Record<string, { t: string; cls: string }> = {
  "1": { t: "keldi", cls: "bg-emerald-100 text-emerald-700" },
  "2": { t: "kech keldi", cls: "bg-amber-100 text-amber-700" },
  "0": { t: "kelmadi", cls: "bg-red-100 text-red-600" },
};
const HW: Record<string, string> = {
  "2": "vazifa: bajardi ✓", "1": "vazifa: qisman ±",
  "0": "vazifa: qilmadi ✗",
};

/**
 * OTA-ONA — BOSH SAHIFA. Faqat eng kerakli narsa: holat, davomat va
 * bo'limlarga o'tish uchun aniq, professional tugmalar (2026-08-09,
 * Jahongir: "bosadigan buttonlarni chiroyli qilib joylab kerakli
 * joylariga"). To'lovlar, coin/XP, test natijalari va guruhdagi
 * reyting endi HAR BIRI o'zining sahifasida — shu yerda faqat qisqa
 * ko'rinish (teaser) va o'tish tugmasi bor.
 */
export default function ParentHome() {
  const { d, fmt, installEvt, installHidden, setInstallHidden, installApp } =
    useOutletContext<ParentCtx>();

  const lastExam = d.exam_results?.[0];
  const resultsTeaser = lastExam
    ? lastExam.absent
      ? "Oxirgi: kelmadi"
      : `Oxirgi: ${
          lastExam.band != null
            ? `Band ${lastExam.band}`
            : lastExam.percent != null
            ? `${lastExam.percent}%`
            : lastExam.score
        }`
    : d.daily_grades?.length
    ? `${d.daily_grades.length} ta baho`
    : "Hali yo'q";

  const rankTeaser = d.ranks?.group_rank
    ? `Guruhda ${d.ranks.group_rank}/${d.ranks.group_total}`
    : "Hali yo'q";

  const gamTeaser = d.gamification
    ? `${fmt(d.gamification.lifetime_xp)} XP · ${d.gamification.coins} coin`
    : "Hali yo'q";

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-10">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2 mb-4 opacity-90">
            <BrandIcon size={18} className="rounded-md" />
            <span className="text-sm font-medium">Jony ota-ona</span>
          </div>
          <h1 className="text-xl font-semibold">{d.name}</h1>
          <p className="text-sm opacity-90 mt-0.5">
            {d.group || "guruh biriktirilmagan"}
            {d.lesson_time ? ` · ${d.lesson_time}` : ""} · {d.status}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        {installEvt && !installHidden && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center shrink-0">
              <Download size={16} className="text-brand-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800">
                Ilovani telefoningizga o'rnating
              </p>
              <p className="text-xs text-slate-500">
                Uy ekranidan bir bosishda oching
              </p>
            </div>
            <button
              onClick={installApp}
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-brand-600 text-white shrink-0"
            >
              O'rnatish
            </button>
            <button
              onClick={() => setInstallHidden(true)}
              className="text-slate-400 shrink-0"
              aria-label="Yopish"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {d.status === "muzlatilgan" && d.frozen_until && (
          <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start gap-2.5">
            <Snowflake size={16} className="text-sky-500 mt-0.5" />
            <p className="text-sm text-sky-800">
              O'qish vaqtincha muzlatilgan. Qaytish sanasi:{" "}
              <b>{d.frozen_until}</b>
            </p>
          </div>
        )}

        {/* --- Bo'limlar: professional navigatsiya kartalari --- */}
        <div className="grid grid-cols-2 gap-3">
          <NavTile
            to="payments"
            icon={<Wallet size={18} />}
            label="To'lovlar"
            value={`${fmt(d.balance)} so'm`}
            valueTone={d.balance < 0 ? "text-red-600" : "text-emerald-600"}
          />
          <NavTile
            to="coins"
            icon={<Coins size={18} />}
            label="Coin va XP"
            value={gamTeaser}
          />
          <NavTile
            to="results"
            icon={<ClipboardCheck size={18} />}
            label="Natijalar"
            value={resultsTeaser}
          />
          <NavTile
            to="rank"
            icon={<Trophy size={18} />}
            label="Reyting"
            value={rankTeaser}
          />
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            So'nggi darslar
          </p>
          {d.practice && d.practice.done > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
              <p className="text-xs text-slate-500 mb-1">
                Mashqlar bo'yicha daraja
              </p>
              <p className="text-lg font-semibold text-slate-900">
                {d.practice.level.label}
                <span className="ml-2 text-xs font-normal text-slate-400">
                  IELTS {d.practice.level.ielts} · CEFR {d.practice.level.cefr}
                </span>
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                {d.practice.done} ta mashq · to'g'ri javoblar{" "}
                {d.practice.percent}%
              </p>
              {d.practice.next && (
                <div className="mt-2">
                  <div className="flex justify-between text-[11px] text-slate-500 mb-0.5">
                    <span>Keyingi: {d.practice.next.label}</span>
                    <span>{d.practice.next.points_left} ball qoldi</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-2 rounded-full bg-emerald-500"
                      style={{ width: `${d.practice.next.progress_percent}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {d.attendance.length === 0 && (
            <p className="text-sm text-slate-400">
              Hozircha dars yozuvi yo'q.
            </p>
          )}
          <div className="space-y-2">
            {d.attendance.map((a: Any, i: number) => {
              const ui = AT[String(a.present)] || AT["0"];
              return (
                <div key={i}
                  className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">{a.date}</span>
                  <span className="flex items-center gap-2">
                    {a.homework !== null && a.homework !== undefined && (
                      <span className="text-[11px] text-slate-400">
                        {HW[String(a.homework)]}
                      </span>
                    )}
                    <span className={`text-[11px] rounded-full px-2 py-0.5 font-medium ${ui.cls}`}>
                      {ui.t}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <p className="text-[11px] text-slate-400 text-center px-6">
          Bu sahifa faqat sizga berilgan maxsus havola orqali ochiladi.
          Havolani begonalarga bermang.
        </p>
      </div>
    </>
  );
}

function NavTile({
  to,
  icon,
  label,
  value,
  valueTone = "text-slate-500",
}: {
  to: string;
  icon: ReactNode;
  label: string;
  value: string;
  valueTone?: string;
}) {
  return (
    <Link
      to={to}
      className="bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 flex flex-col gap-2 active:scale-[0.98] transition"
    >
      <div className="flex items-center justify-between">
        <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center text-brand-600">
          {icon}
        </div>
        <ChevronRight size={16} className="text-slate-300" />
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className={`text-sm font-semibold truncate ${valueTone}`}>
          {value}
        </p>
      </div>
    </Link>
  );
}
