import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, X } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * CEFR WRITING — BITTA XAT TURI QO'LLANMASI (2026-08-26).
 *
 * ENG MUHIM QISMI — IZOHLANGAN NAMUNA. Oddiy namuna xatni
 * o'qigan o'quvchi "yaxshi yozilgan ekan" deydi-yu, nusxa
 * ko'chirishdan nariga o'tolmaydi. Chunki qaysi gap NIMA ISH
 * qilayotgani ko'rinmaydi.
 *
 * Shuning uchun bu yerda har abzats yonida uning VAZIFASI
 * (Salomlashish, Sabab, Talab...) va NEGA aynan shunday
 * yozilgani turadi. O'quvchi keyin o'z xatini shu qolipga solib
 * ko'radi — bu ko'chirish emas, ko'chirib o'rganish.
 */
export default function StudentCefrWritingGuide() {
  const { key = "" } = useParams();
  const [g, setG] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [show, setShow] = useState<number | null>(0);

  useEffect(() => {
    api
      .get<Any>("/student/cefr/writing/guide/" + key)
      .then(setG)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [key]);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!g)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/cefr/writing"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          CEFR Writing
        </p>
      </div>

      <h1 className="text-[24px] font-extrabold text-white leading-tight mt-3">
        {g.title}
      </h1>
      <p className="text-[11.5px] text-brand-300 mt-1">
        Part {g.part} · {g.level} · {g.words[0]}-{g.words[1]} so'z ·{" "}
        {g.minutes} daqiqa
      </p>

      <div className="rounded-2xl border p-3.5 mt-3" style={card}>
        <p className="text-[12px] text-slate-300 leading-relaxed">
          <b className="text-white">Qachon keladi.</b> {g.when}
        </p>
        <p className="text-[12px] text-slate-300 leading-relaxed mt-2">
          <b className="text-white">Asosiy fikr.</b> {g.idea}
        </p>
      </div>

      {/* --- qadamlar + iboralar -------------------------- */}
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5 mb-1.5">
        Tuzilma va tayyor iboralar
      </p>
      <div className="space-y-2">
        {g.steps.map((s: Any, i: number) => (
          <div key={i} className="rounded-2xl border p-3.5" style={card}>
            <div className="flex items-start gap-2">
              <span className="w-5 h-5 shrink-0 rounded-full bg-brand-600 text-white text-[11px] font-bold flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-white font-bold text-[14px]">{s.name}</p>
                <p className="text-[11.5px] text-slate-400 leading-snug mt-0.5">
                  {s.why}
                </p>
                <div className="mt-2 space-y-1">
                  {s.phrases.map((p: string, k: number) => (
                    <p
                      key={k}
                      className="text-[12px] text-emerald-200 bg-emerald-400/5 border border-emerald-400/15 rounded-lg px-2 py-1"
                    >
                      {p}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* --- izohlangan namuna --------------------------- */}
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5 mb-1.5">
        Namuna xat — har abzatsi izohi bilan
      </p>
      <div className="rounded-2xl border p-3.5" style={card}>
        <p className="text-[11.5px] text-slate-400 leading-relaxed italic">
          {g.model.task}
        </p>
        <p className="text-[10.5px] text-slate-500 mt-1.5">
          {g.model.words} so'z · abzatsga bosing, izohi ochiladi
        </p>
        <div className="mt-3 space-y-1.5">
          {g.model.paras.map((p: Any, i: number) => (
            <div key={i}>
              <button
                onClick={() => setShow(show === i ? null : i)}
                className="w-full text-left rounded-xl px-2.5 py-2 border"
                style={{
                  background: show === i ? "#111C4B" : "transparent",
                  borderColor: show === i ? "#2B3B8A" : "rgba(255,255,255,.07)",
                }}
              >
                <span className="text-[10px] font-bold text-brand-300 uppercase tracking-wide">
                  {p[0]}
                </span>
                <span className="block text-[12.5px] text-slate-100 leading-relaxed mt-1 whitespace-pre-line">
                  {p[1]}
                </span>
              </button>
              {show === i && (
                <p className="text-[11.5px] text-amber-200 leading-relaxed px-2.5 py-2">
                  {p[2]}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* --- shart / xato -------------------------------- */}
      <div className="grid grid-cols-1 gap-2 mt-4">
        <div className="rounded-2xl border p-3.5" style={card}>
          <p className="text-[12px] font-bold text-emerald-300 mb-1.5">
            Bo'lishi shart
          </p>
          {g.must.map((m: string, i: number) => (
            <p key={i} className="flex gap-1.5 text-[12px] text-slate-300 mt-1">
              <Check size={13} className="text-emerald-400 shrink-0 mt-0.5" />
              <span>{m}</span>
            </p>
          ))}
        </div>
        <div className="rounded-2xl border p-3.5" style={card}>
          <p className="text-[12px] font-bold text-rose-300 mb-1.5">
            Eng ko'p uchraydigan xato
          </p>
          {g.avoid.map((m: string, i: number) => (
            <p key={i} className="flex gap-1.5 text-[12px] text-slate-300 mt-1">
              <X size={13} className="text-rose-400 shrink-0 mt-0.5" />
              <span>{m}</span>
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
