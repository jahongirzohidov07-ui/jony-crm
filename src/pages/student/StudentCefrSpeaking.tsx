import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ChevronRight, Play } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * MULTILEVEL SPEAKING — BOSH EKRAN (2026-08-26).
 *
 * Jahongir: "multilevelga tayyorlashi uchun eng zor platforma
 * bo'lsin va Multilevel Free Mock olsayam bo'lsin bahosini
 * chiqarib bersin."
 *
 * Ekran ikki yo'l beradi:
 *   - QISM BO'YICHA tayyorgarlik (shablon, iboralar, namuna,
 *     cheksiz mashq savollari)
 *   - FREE MOCK — to'liq imtihon, 0-75 ball va CEFR darajasi
 */
export default function StudentCefrSpeaking() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/cefr/speaking/home")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/ielts/exam/cefr"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          CEFR Multilevel
        </p>
        <StudentImage src="/jsicons/learn-jony-teacher.png" alt=""
             className="w-10 h-10 shrink-0" />
      </div>

      <h1 className="text-[30px] font-extrabold text-white leading-none mt-3">
        Speaking
      </h1>

      {/* --- FREE MOCK --- */}
      <Link
        to="/student/cefr/speaking/mock"
        className="block rounded-2xl border p-4 mt-4"
        style={{ background: "#0c2258", borderColor: "#2B3B8A" }}
      >
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-brand-600 flex items-center justify-center shrink-0">
            <Play size={20} className="text-white" fill="#fff" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white font-bold text-[16px]">Free Mock</p>
            <p className="text-[11.5px] text-slate-300 leading-snug mt-0.5">
              To'liq imtihon: 4 qism, 10 savol. Oxirida 0-75 ball va
              CEFR darajangiz.
            </p>
          </div>
          <ChevronRight size={18} className="text-slate-400 shrink-0" />
        </div>
        {d.best > 0 && (
          <p className="text-[11px] text-brand-200 mt-2">
            Eng yaxshi natijangiz: <b>{d.best}</b>/{d.score_max}
          </p>
        )}
      </Link>

      {/* --- ball shkalasi --- */}
      <div className="rounded-2xl border p-3.5 mt-3" style={card}>
        <p className="text-[12px] font-bold text-white mb-2">
          Ball va daraja ({d.score_max} balldan)
        </p>
        <div className="space-y-1.5">
          {(d.levels || []).map((l: Any) => (
            <div key={l.level} className="flex items-center gap-2 text-[11.5px]">
              <span className="w-14 shrink-0 font-bold tabular-nums text-slate-300">
                {l.from}-{l.to}
              </span>
              <span className="w-7 shrink-0 font-bold text-brand-300">
                {l.level}
              </span>
              <span className="flex-1 min-w-0 text-slate-400 truncate">
                {l.desc}
              </span>
            </div>
          ))}
        </div>
        <p className="text-[10.5px] text-slate-500 mt-2.5 leading-relaxed">
          Rasmiy shkala 4 blokni {d.raw_max} xom balldan baholaydi
          (1-3 savol · 4-6 savol · 7-savol · 8-savol). Xom ball{" "}
          {d.score_max} ballik shkalaga o'tkaziladi.
        </p>
      </div>

      {/* --- qismlar --- */}
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5 mb-1.5">
        Qism bo'yicha tayyorgarlik
      </p>
      <div className="space-y-2">
        {(d.parts || []).map((p: Any) => (
          <Link
            key={p.key}
            to={`/student/cefr/speaking/part/${p.key}`}
            className="flex items-center gap-3 rounded-2xl border p-3.5"
            style={card}
          >
            <div className="w-11 h-11 rounded-2xl flex flex-col items-center justify-center shrink-0"
                 style={{ background: "#0c2258" }}>
              <span className="text-[13px] font-extrabold text-white leading-none">
                {p.part}
              </span>
              <span className="text-[9px] text-brand-300 mt-0.5">
                {p.level}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-[14px]">{p.title}</p>
              <p className="text-[11px] text-slate-400 leading-snug mt-0.5">
                {p.uz}
              </p>
              <p className="text-[11px] text-brand-300 mt-1">
                {p.sets} ta vazifa · {p.questions} savol ·{" "}
                {p.prep ? `${p.prep}s tayyorgarlik · ` : ""}
                {p.seconds.length > 1
                  ? p.seconds.join("/") + " soniya"
                  : `${p.seconds[0]} soniya`}
              </p>
            </div>
            <ChevronRight size={16} className="text-slate-500 shrink-0" />
          </Link>
        ))}
      </div>

      {/* --- oldingi mocklar --- */}
      {(d.mocks || []).length > 0 && (
        <>
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5 mb-1.5">
            Oldingi mocklar
          </p>
          <div className="rounded-2xl border p-3.5" style={card}>
            {d.mocks.map((m: Any, i: number) => (
              <div key={i} className="flex items-center gap-2 py-1 text-[12px]">
                <span className="flex-1 text-slate-400">{m.date}</span>
                <span className="font-bold text-white tabular-nums">
                  {m.score}
                </span>
                <span className="w-7 text-right font-bold text-brand-300">
                  {m.level}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
