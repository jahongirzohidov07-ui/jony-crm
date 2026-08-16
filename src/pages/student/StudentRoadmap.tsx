import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Lock, Sparkles, Map as MapIcon } from "lucide-react";
import { api } from "../../lib/api";
import { fmtNum, type SkillsCard } from "../../lib/studentApi";

/**
 * JONY STUDENT — YO'L XARITASI (2026-08-16).
 *
 * Jahongir: "XP nima berishini, keyingi mukofot qachon ochilishini,
 * coin bilan XP orasidagi farqni bilmaydi ... XP bosilganda
 * 'Darajalar yo'li' ochilishi kerak."
 *
 * Shu sahifa aynan shu savolga javob beradi: qaysi darajadaman,
 * keyingisiga qancha qoldi, va eng tepasida COIN va XP farqi bir
 * jumlada tushuntirilgan.
 *
 * Ma'lumot manbai — mavjud /api/student/skills (umumiy daraja,
 * bosqichlar ro'yxati va har daraja uchun kerakli ball). Yangi
 * endpoint yozilmadi.
 */

export default function StudentRoadmap() {
  const [d, setD] = useState<SkillsCard | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<SkillsCard>("/student/skills")
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

  const per = d.points_per_level;
  const points = d.overall.points;
  const curKey = d.overall.level.key;
  const curIdx = d.levels.findIndex((l) => l.key === curKey);

  return (
    <>
      <div className="bg-brand-600 text-white px-4 pt-6 pb-12">
        <div className="max-w-md mx-auto">
          <Link
            to="/student"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Asosiy
          </Link>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <MapIcon size={20} />
            Yo'l xaritasi
          </h1>
          <p className="text-sm text-white/80 mt-1">
            Jami {fmtNum(points)} ball · har daraja uchun {per} ball
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 pb-8 space-y-4">
        {/* COIN va XP farqi — eng ko'p tushunmovchilik shu yerda */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
          <div className="flex gap-3">
            <span className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center shrink-0 text-lg">
              🪙
            </span>
            <div>
              <p className="text-sm font-bold text-slate-900">Coin — pul</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-snug">
                Sarflanadi. Mukofotlar bo'limida sovg'a yoki to'lovga
                chegirma sotib olasiz. Sarflansa kamayadi.
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
              <Sparkles size={18} className="text-brand-500" />
            </span>
            <div>
              <p className="text-sm font-bold text-slate-900">XP — daraja</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-snug">
                Sarflanmaydi, faqat o'sadi. Darajangizni va reytingdagi
                o'rningizni belgilaydi.
              </p>
            </div>
          </div>
        </div>

        <p className="text-[15px] font-bold text-slate-900 px-1">
          Darajalar
        </p>

        <div className="space-y-2">
          {d.levels.map((lv, i) => {
            const need = i * per;
            const passed = i < curIdx;
            const current = i === curIdx;
            const inLevel = Math.max(0, Math.min(per, points - need));
            const pct = Math.round((inLevel / per) * 100);
            return (
              <div
                key={lv.key}
                className={`rounded-xl border p-4 ${
                  current
                    ? "bg-brand-50 border-brand-300"
                    : passed
                    ? "bg-white border-slate-200"
                    : "bg-white border-slate-100"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                      passed
                        ? "bg-emerald-500 text-white"
                        : current
                        ? "bg-brand-600 text-white"
                        : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {passed ? (
                      <Check size={16} strokeWidth={3} />
                    ) : current ? (
                      lv.cefr
                    ) : (
                      <Lock size={14} />
                    )}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-sm font-bold ${
                        passed || current ? "text-slate-900" : "text-slate-400"
                      }`}
                    >
                      {lv.label}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      CEFR {lv.cefr} · IELTS {lv.ielts.replace("~", "")}
                    </p>
                  </div>
                  <span className="text-xs text-slate-400 shrink-0">
                    {passed ? "ochilgan" : `${need} ball`}
                  </span>
                </div>

                {current && (
                  <>
                    <div className="h-2 rounded-full bg-white mt-3 overflow-hidden border border-brand-200">
                      <div
                        className="h-full bg-brand-600 rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <p className="text-xs text-brand-700 font-medium mt-2">
                      {inLevel}/{per} ball · keyingi darajagacha yana{" "}
                      {per - inLevel}
                    </p>
                  </>
                )}
              </div>
            );
          })}
        </div>

        <Link
          to="/student/games"
          className="block w-full h-13 py-3.5 rounded-xl bg-brand-600 text-white font-semibold text-center"
        >
          Mashq qilish
        </Link>
      </div>
    </>
  );
}
