import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Lock } from "lucide-react";
import { JsaLogo, JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * CEFR / IELTS BO'LIMI (2026-08-24).
 *
 * Jahongir: "biz CEFR va IELTS qismini intermediate tugatganda
 * ochiladigan qilgan edik u yoqolib qolibdi, alohida bo'lim
 * ochilishi kerak va birgalikda ularga alohida mashqlar kirgizamiz
 * hali avval bolimlarni och".
 *
 * QOIDA. Bo'lim Intermediate TUGAGANDA ochiladi (umumiy daraja
 * Upper-Intermediate va undan yuqori). Qulf holati serverda
 * hisoblanadi (/student/learn -> ielts.unlocked) - mijozda hiyla
 * qilib ochib bo'lmaydi.
 *
 * HOZIRGI BOSQICH: bo'lim tuzilmasi ochildi (IELTS 4 ko'nikma +
 * CEFR zinasi). Maxsus IELTS mashqlari keyin birga kiritiladi;
 * ungacha C1/C2 darajali Reading/Listening mashqlariga yo'l bor.
 */

const PARTS: {
  key: string; title: string; desc: string; icon: string;
  href?: string; hint?: string;
}[] = [
  {
    key: "listening", title: "IELTS Listening",
    desc: "4 qism · 40 savol · 30 daqiqa. Suhbat, monolog, " +
      "ma'ruza - barchasi bir marta eshittiriladi.",
    icon: "/jsicons/learn-listening.png",
    // Listening mashqlari pastda alohida blokda (2026-08-24)
  },
  {
    key: "reading", title: "IELTS Reading",
    desc: "3 matn · 40 savol · 60 daqiqa. T/F/NG, sarlavha " +
      "moslash, bo'sh joy to'ldirish.",
    icon: "/jsicons/learn-reading.png",
    href: "/student/practice/reading",
    hint: "Hozircha: C1/C2 darajali reading mashqlari",
  },
  {
    key: "writing", title: "IELTS Writing",
    desc: "Task 1 (grafik/jadval tavsifi) va Task 2 (esse) · " +
      "60 daqiqa.",
    icon: "/jsicons/learn-writing.png",
  },
  {
    key: "speaking", title: "IELTS Speaking",
    desc: "3 qism · 11-14 daqiqa. Tanishuv, mavzu kartasi (cue " +
      "card) va munozara.",
    icon: "/jsicons/learn-jony-teacher.png",
  },
];

export default function StudentIelts() {
  const [gate, setGate] = useState<Any>(null);
  const [parts, setParts] = useState<Any[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/learn")
      .then((r) => setGate(r.ielts || { unlocked: false }))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  // Listening mashqlari (2026-08-24): spelling / raqam / aralash
  useEffect(() => {
    if (!gate?.unlocked) return;
    api
      .get<Any>("/student/ielts/listening/parts")
      .then((r) => setParts(r.parts || []))
      .catch(() => setParts([]));
  }, [gate?.unlocked]);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  if (err)
    return (
      <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>
    );
  if (!gate)
    return (
      <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>
    );

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2">
        <div className="flex-1 min-w-0">
          <JsaLogo />
        </div>
        <img src="/jsicons/learn-exam.png" alt="" className="w-12 h-12" />
      </div>

      <h1 className="text-[34px] font-extrabold text-white leading-none mt-3">
        CEFR / IELTS
      </h1>
      <p className="text-[14px] text-slate-400 mt-2">
        Xalqaro imtihon formatidagi tayyorgarlik bo'limi.
      </p>

      {!gate.unlocked ? (
        <div className="rounded-2xl border p-5 mt-5 text-center" style={card}>
          <div
            className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center"
            style={{ background: "#111C4B" }}
          >
            <Lock size={24} className="text-amber-400" />
          </div>
          <p className="text-white font-bold text-[16px] mt-3">
            Bo'lim hali qulflangan
          </p>
          <p className="text-[13px] text-slate-400 mt-1.5 leading-relaxed">
            {gate.need_label}. Hozirgi darajangiz:{" "}
            <b className="text-slate-200">{gate.level_label || "—"}</b>.
            Mashq qilib ball to'plasangiz - daraja o'sadi va bo'lim
            o'zi ochiladi.
          </p>
          <Link
            to="/student/games"
            className="inline-block mt-4 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white"
          >
            Mashqlarga qaytish
          </Link>
        </div>
      ) : (
        <>
          <div className="rounded-2xl border p-4 mt-5" style={card}>
            <p className="text-[13px] text-emerald-300 font-semibold">
              Tabriklaymiz - Intermediate bosqichi ortda!
            </p>
            <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
              Bu bo'limda IELTS formatidagi mashqlar bosqichma-bosqich
              qo'shib boriladi. Hozircha har qismning tuzilishi bilan
              tanishing va C1/C2 darajali mashqlarni ishlang.
            </p>
          </div>

          <div className="space-y-2.5 mt-4">
            {PARTS.map((p) =>
              p.href ? (
                <Link
                  key={p.key}
                  to={p.href}
                  className="flex items-center gap-3 rounded-2xl border p-4"
                  style={card}
                >
                  <img src={p.icon} alt="" className="w-11 h-11 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-bold text-[15px]">
                      {p.title}
                    </p>
                    <p className="text-[12px] text-slate-400 leading-snug mt-0.5">
                      {p.desc}
                    </p>
                    {p.hint && (
                      <p className="text-[11px] text-brand-300 mt-1">
                        {p.hint}
                      </p>
                    )}
                  </div>
                  <ChevronRight size={18} className="text-slate-500 shrink-0" />
                </Link>
              ) : (
                <div
                  key={p.key}
                  className="flex items-center gap-3 rounded-2xl border p-4 opacity-80"
                  style={card}
                >
                  <img src={p.icon} alt="" className="w-11 h-11 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-bold text-[15px]">
                      {p.title}
                    </p>
                    <p className="text-[12px] text-slate-400 leading-snug mt-0.5">
                      {p.desc}
                    </p>
                  </div>
                  <span className="text-[10px] font-bold text-amber-300 bg-amber-400/10 border border-amber-400/30 rounded-full px-2 py-1 shrink-0">
                    Tez orada
                  </span>
                </div>
              ),
            )}
          </div>

          {/* ---- LISTENING MASHQLARI (2026-08-24, Jahongir:
               "Listening bo'limda birinchi spelling names bo'lsin...
               keyin number practice... 3-mashq spelling mixed") ---- */}
          {parts.length > 0 && (
            <div className="rounded-2xl border p-4 mt-4" style={card}>
              <p className="text-white font-bold text-[15px]">
                Listening — asosiy ko'nikmalar
              </p>
              <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
                IELTS'da eng ko'p ball yo'qotiladigan joy: ism, raqam
                va postcode. Har mashq sekin va osondan boshlanib,
                asta-sekin imtihon tezligiga chiqadi.
              </p>
              <div className="space-y-2 mt-3">
                {parts.map((p: Any) => (
                  <Link
                    key={p.kind}
                    to={`/student/ielts/listening/${p.kind}`}
                    className="flex items-center gap-3 rounded-xl border px-3 py-3"
                    style={{ background: "#1A2558", borderColor: "#3A4890" }}
                  >
                    <div className="w-9 h-9 rounded-lg bg-amber-400/15 text-amber-300 flex items-center justify-center shrink-0 text-sm font-extrabold">
                      {p.no}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[14px] font-bold text-white">
                        {p.title}
                      </p>
                      <p className="text-[11px] text-slate-400 leading-snug">
                        {p.hint}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <div className="h-1.5 flex-1 rounded-full bg-slate-700/60 overflow-hidden">
                          <div className="h-full bg-amber-400 rounded-full"
                               style={{ width: `${p.percent}%` }} />
                        </div>
                        <span className="text-[10px] text-slate-400 shrink-0">
                          {p.solved}/{p.total}
                        </span>
                      </div>
                    </div>
                    <ChevronRight size={17} className="text-slate-500 shrink-0" />
                  </Link>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-2xl border p-4 mt-4" style={card}>
            <p className="text-white font-bold text-[15px]">CEFR zinasi</p>
            <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
              Reading va Listening bo'limlarida endi A1 (Beginner) dan
              C2 (Native) gacha daraja tanlanadi. IELTS'ga tayyorlanish
              uchun C1-C2 bo'limlarini ishlang - matn va topshiriqlar
              imtihon uslubiga yaqin.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
