import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Lock } from "lucide-react";
import { JsaLogo, JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import { EXAMS } from "./examsConfig";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * IMTIHONLAR — BIRINCHI QAVAT (2026-08-26).
 *
 * Jahongir: "Yoq yanada alohida qil, IELTS va CEFR alohida tursin
 * SAT ham alohida tursin".
 *
 * Avval bu sahifada IELTS ko'nikmalari va CEFR kartalari ARALASH
 * turardi — 8 ta karta bir ro'yxatda. Endi bu yerda faqat UCH
 * imtihon turadi; ko'nikmalar ularning ichida.
 *
 * QULF. Bo'lim Intermediate tugaganda ochiladi. Qulf serverda
 * hisoblanadi (/student/learn -> ielts.unlocked), mijozda hiyla
 * qilib ochib bo'lmaydi.
 */
export default function StudentIelts() {
  const [gate, setGate] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/learn")
      .then((r) => setGate(r.ielts || { unlocked: false }))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

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
        Imtihonlar
      </h1>
      <p className="text-[14px] text-slate-400 mt-2">
        Har imtihon o'z bo'limida — kirib, ko'nikmani tanlaysiz.
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
          <div className="space-y-2.5 mt-5">
            {EXAMS.map((e) => (
              <Link
                key={e.key}
                to={`/student/ielts/exam/${e.key}`}
                className="flex items-center gap-3 rounded-2xl border p-4"
                style={card}
              >
                <img src={e.icon} alt="" className="w-12 h-12 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-white font-bold text-[17px]">
                      {e.title}
                    </p>
                    <span className="text-[10px] font-bold text-slate-300 bg-white/5 border border-white/10 rounded-full px-2 py-0.5">
                      {e.tag}
                    </span>
                  </div>
                  <p className="text-[12px] text-slate-400 leading-snug mt-1">
                    {e.desc}
                  </p>
                  <p className="text-[11px] mt-1.5">
                    {e.ready ? (
                      <span className="text-brand-300">
                        {e.skills.filter((s) => s.href).length} ko'nikmada
                        mashqlar tayyor
                      </span>
                    ) : (
                      <span className="text-amber-300">
                        Tuzilma tayyor · mashqlar qo'shilmoqda
                      </span>
                    )}
                  </p>
                </div>
                <ChevronRight size={18} className="text-slate-500 shrink-0" />
              </Link>
            ))}
          </div>

          <div className="rounded-2xl border p-4 mt-4" style={card}>
            <p className="text-white font-bold text-[15px]">CEFR zinasi</p>
            <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
              Reading va Listening bo'limlarida A1 (Beginner) dan C2
              (Native) gacha daraja tanlanadi. IELTS'ga tayyorlanish
              uchun C1-C2 bo'limlarini ishlang — matn va topshiriqlar
              imtihon uslubiga yaqin.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
