import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ChevronRight, Lock } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * IELTS READING — BO'LIM SAHIFASI (2026-08-25).
 *
 * Jahongir: "keyin amna oxirida question types hammasini toliq
 * tashladim, true/false va yes nolar hamma mashqlarni aytdib
 * qolganini keyinroq aytaman lekin hozircha bo'limlar ochib
 * qo'ysang bo'ladi".
 *
 * Shuning uchun 12 TURNING HAMMASI shu yerda ro'yxat bo'lib turadi —
 * ikkitasi (TFNG, YNNG) ochiq va mashqlar bilan to'la, qolgan
 * o'ntasi "Tez orada" belgisi bilan. Bo'lim tuzilmasi ko'rinib
 * turgani uchun o'quvchi imtihonda nima kutayotganini biladi.
 */
export default function StudentIeltsReadingHome() {
  const [parts, setParts] = useState<Any[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Any>("/student/ielts/reading/parts")
      .then((r) => setParts(r.parts || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }, []);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const ready = parts.filter((p: Any) => p.ready);
  const soon = parts.filter((p: Any) => !p.ready);

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/ielts"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          CEFR / IELTS
        </p>
        <img src="/jsicons/learn-reading.png" alt=""
             className="w-10 h-10 shrink-0" />
      </div>

      <h1 className="text-[30px] font-extrabold text-white leading-tight mt-3">
        IELTS Reading
      </h1>
      <p className="text-[13px] text-slate-400 mt-2 leading-relaxed">
        3 matn · 40 savol · 60 daqiqa. Imtihonda 12 xil savol turi
        uchraydi — quyida hammasi ro'yxat qilingan.
      </p>

      {err && <p className="text-sm text-red-400 mt-4">{err}</p>}
      {loading && (
        <p className="text-sm text-slate-500 mt-6">Yuklanmoqda…</p>
      )}

      {ready.length > 0 && (
        <>
          <div className="rounded-2xl border p-4 mt-5" style={card}>
            <p className="text-white font-bold text-[15px]">
              Ochiq mashqlar
            </p>
            <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
              Har mashq QOIDALARDAN boshlanadi, keyin eng oddiy bir
              gapli matndan haqiqiy imtihon savoligacha bosqichma-
              bosqich ko'tariladi.
            </p>
          </div>

          <div className="space-y-2.5 mt-3">
            {ready.map((p: Any) => (
              <Link
                key={p.kind}
                to={`/student/ielts/reading/${p.kind}`}
                className="flex items-center gap-3 rounded-2xl border p-4 active:scale-[0.99] transition"
                style={card}
              >
                <div className="w-10 h-10 rounded-xl bg-sky-400/15 text-sky-300 flex items-center justify-center shrink-0 text-[15px] font-extrabold">
                  {p.no}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[15px] font-bold text-white">
                    {p.title}
                  </p>
                  <p className="text-[11.5px] text-slate-400 leading-snug mt-0.5">
                    {p.hint}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="h-1.5 flex-1 rounded-full bg-slate-700/60 overflow-hidden">
                      <div
                        className="h-full bg-sky-400 rounded-full"
                        style={{ width: `${p.percent}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 shrink-0">
                      {p.solved}/{p.total}
                    </span>
                  </div>
                </div>
                <ChevronRight size={18} className="text-slate-500 shrink-0" />
              </Link>
            ))}
          </div>
        </>
      )}

      {soon.length > 0 && (
        <>
          <div className="rounded-2xl border p-4 mt-4" style={card}>
            <p className="text-white font-bold text-[15px]">
              Qolgan savol turlari
            </p>
            <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
              Bo'limlar ochildi — mashqlar navbat bilan to'ldiriladi.
            </p>
          </div>
          <div className="space-y-2 mt-3">
            {soon.map((p: Any) => (
              <div
                key={p.no}
                className="flex items-center gap-3 rounded-2xl border p-3.5 opacity-75"
                style={card}
              >
                <div className="w-9 h-9 rounded-xl bg-slate-700/40 text-slate-400 flex items-center justify-center shrink-0 text-[13px] font-bold">
                  {p.no}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-bold text-white">
                    {p.title}
                  </p>
                  <p className="text-[11px] text-slate-400 leading-snug mt-0.5">
                    {p.hint}
                  </p>
                </div>
                <Lock size={15} className="text-slate-500 shrink-0" />
              </div>
            ))}
          </div>
        </>
      )}

      <Link
        to="/student/practice/reading"
        className="flex items-center gap-3 rounded-2xl border p-4 mt-4"
        style={card}
      >
        <img src="/jsicons/learn-reading.png" alt=""
             className="w-10 h-10 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-[14px] font-bold text-white">
            C1/C2 darajali reading
          </p>
          <p className="text-[11.5px] text-slate-400 leading-snug">
            Uzun matnlar va tushunish savollari — imtihon darajasida
          </p>
        </div>
        <ChevronRight size={18} className="text-slate-500 shrink-0" />
      </Link>
    </div>
  );
}
