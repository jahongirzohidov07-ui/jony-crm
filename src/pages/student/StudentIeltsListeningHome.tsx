import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, ChevronRight } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * IELTS LISTENING — BO'LIM SAHIFASI (2026-08-24).
 *
 * Jahongir: "qara listening asosiy ko'nikmalar, listening ichida
 * bo'lishi kerak".
 *
 * Ilgari uch mashq (spelling, raqamlar, postcode) CEFR/IELTS
 * sahifasining PASTIDA alohida blok bo'lib turardi — ya'ni
 * "Listening" kartasi bilan bog'lanmagan edi. Endi ular aynan shu
 * yerda: Listening kartasini bossang shu sahifa ochiladi.
 */
export default function StudentIeltsListeningHome() {
  const [parts, setParts] = useState<Any[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  /* 2026-08-26, Jahongir: "hozir men CEFR mashqarni qayerdan
     kiraman yoqku". CEFR qismlari IELTS ro'yxati ichida qolib
     ketgan edi. Endi bir xil sahifa ikki rejimda ishlaydi:
     ?exam=cefr bo'lsa faqat CEFR qismlari ko'rinadi. */
  const [sp] = useSearchParams();
  const exam = sp.get("exam") === "cefr" ? "cefr" : "ielts";
  const isCefr = exam === "cefr";

  useEffect(() => {
    api
      .get<Any>("/student/ielts/listening/parts?exam=" + exam)
      .then((r) => setParts(r.parts || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }, [exam]);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to={`/student/ielts/exam/${exam}`}
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          {isCefr ? "CEFR Multilevel" : "IELTS"}
        </p>
        <StudentImage src="/jsicons/learn-listening.png" alt=""
             className="w-10 h-10 shrink-0" />
      </div>

      <h1 className="text-[30px] font-extrabold text-white leading-tight mt-3">
        {isCefr ? "CEFR Listening" : "IELTS Listening"}
      </h1>
      <p className="text-[13px] text-slate-400 mt-2 leading-relaxed">
        {isCefr
          ? "Multilevel (CEFR) imtihoni: 6 qism. Har gap ikki marta " +
            "aytiladi — matnlar haqiqiy imtihon kitobidan olingan."
          : "4 qism · 40 savol · 30 daqiqa. Audio bir marta " +
            "eshittiriladi — ism, raqam va postcodeni birinchi " +
            "eshitishda ilib olish kerak."}
      </p>

      {err && (
        <p className="text-sm text-red-400 mt-4">{err}</p>
      )}
      {loading && (
        <p className="text-sm text-slate-500 mt-6">Yuklanmoqda…</p>
      )}

      {/* ---- Asosiy ko'nikmalar: 3 ta mashq ---- */}
      {parts.length > 0 && (
        <>
          <div className="rounded-2xl border p-4 mt-5" style={card}>
            <p className="text-white font-bold text-[15px]">
              Asosiy ko'nikmalar
            </p>
            <p className="text-[12px] text-slate-400 mt-1 leading-relaxed">
              IELTS'da eng ko'p ball yo'qotiladigan joy shu uchtasi.
              Har mashq sekin va osondan boshlanib, asta-sekin imtihon
              tezligiga chiqadi.
            </p>
          </div>

          <div className="space-y-2.5 mt-3">
            {parts.map((p: Any) => (
              <Link
                key={p.kind}
                to={`/student/ielts/listening/${p.kind}?exam=${exam}`}
                className="flex items-center gap-3 rounded-2xl border p-4 active:scale-[0.99] transition"
                style={card}
              >
                <div className="w-10 h-10 rounded-xl bg-amber-400/15 text-amber-300 flex items-center justify-center shrink-0 text-[15px] font-extrabold">
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
                        className="h-full bg-amber-400 rounded-full"
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

      {/* ---- To'liq test qismlari ---- */}
      <div className="rounded-2xl border p-4 mt-4" style={card}>
        <p className="text-white font-bold text-[15px]">
          To'liq test qismlari
        </p>
        <div className="space-y-2 mt-2.5">
          {[
            ["1-qism", "Ikki kishi suhbati — kundalik mavzu " +
              "(ro'yxatga yozilish, buyurtma)"],
            ["2-qism", "Bir kishining monologi — joy yoki tadbir " +
              "haqida ma'lumot"],
            ["3-qism", "2-4 kishi suhbati — o'quv mavzusi, loyiha " +
              "muhokamasi"],
            ["4-qism", "Ma'ruza — ilmiy mavzu, eng qiyin qism"],
          ].map(([t, d]) => (
            <div key={t} className="flex gap-2.5">
              <span className="text-[11px] font-bold text-amber-300 shrink-0 w-12">
                {t}
              </span>
              <span className="text-[12px] text-slate-400 leading-snug">
                {d}
              </span>
            </div>
          ))}
        </div>
        <p className="text-[11px] text-slate-500 mt-3 leading-relaxed">
          To'liq test mashqlari keyingi bosqichda qo'shiladi. Hozircha
          yuqoridagi uch ko'nikmani mustahkamlang — imtihonda eng ko'p
          xato aynan shu yerda bo'ladi.
        </p>
      </div>

      <Link
        to="/student/practice/listening"
        className="flex items-center gap-3 rounded-2xl border p-4 mt-3"
        style={card}
      >
        <StudentImage src="/jsicons/learn-listening.png" alt=""
             className="w-10 h-10 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-[14px] font-bold text-white">
            C1/C2 darajali listening
          </p>
          <p className="text-[11.5px] text-slate-400 leading-snug">
            Dialog, tartiblash va diktant — imtihon darajasida
          </p>
        </div>
        <ChevronRight size={18} className="text-slate-500 shrink-0" />
      </Link>
    </div>
  );
}
