import { StudentLoading } from "../../components/StudentLoading";
import { StudentImage } from "../../components/StudentIcon";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, X, AlertTriangle, Clock } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import SpeakRecorder from "../../components/SpeakRecorder";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * SPEAKING — QISM BO'YICHA TAYYORGARLIK (2026-08-26).
 *
 * Uch bo'lim bitta ekranda:
 *   O'RGANISH  — shablon (qaysi soniyada nima aytiladi), tayyor
 *                iboralar, namuna javob va rasmiy baholash shkalasi
 *   MASHQ      — vazifa, tayyorgarlik taymeri, diktafon
 *   TAHLIL     — javob tahlili va ball
 *
 * Tayyorgarlik vaqti (2 va 3-qismda 60 soniya) ALOHIDA taymer —
 * imtihonda ham shunday: avval o'ylaysiz, keyin gapirasiz.
 */
export default function StudentCefrSpeakingPart() {
  const { key = "p11" } = useParams();
  const [g, setG] = useState<Any>(null);
  const [t, setT] = useState<Any>(null);
  const [idx, setIdx] = useState(0);
  const [qi, setQi] = useState(0);
  const [tab, setTab] = useState<"learn" | "do">("learn");
  const [prep, setPrep] = useState(0);
  const [prepOn, setPrepOn] = useState(false);
  const [res, setRes] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [openStep, setOpenStep] = useState<number | null>(0);
  const tick = useRef<number | null>(null);

  useEffect(() => {
    api.get<Any>("/student/cefr/speaking/guide/" + key)
      .then(setG)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [key]);

  useEffect(() => {
    api.get<Any>(`/student/cefr/speaking/task?part=${key}&idx=${idx}`)
      .then((r) => { setT(r); setQi(0); setRes(null); })
      .catch(() => undefined);
  }, [key, idx]);

  const stop = useCallback(() => {
    if (tick.current) window.clearInterval(tick.current);
    tick.current = null;
  }, []);
  useEffect(() => stop, [stop]);

  const startPrep = () => {
    if (!t?.prep) return;
    setPrep(t.prep);
    setPrepOn(true);
    stop();
    tick.current = window.setInterval(() => {
      setPrep((s) => {
        if (s <= 1) { stop(); setPrepOn(false); return 0; }
        return s - 1;
      });
    }, 1000);
  };

  const send = async (r: Any) => {
    setBusy(true);
    setErr("");
    try {
      const out = await api.post<Any>("/student/cefr/speaking/answer", {
        part: key, idx, qi, seconds: r.used || secs,
        transcript: r.transcript, audio: r.audio, mime: r.mime,
      });
      setRes(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  if (err && !g)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!g || !t)
    return <StudentLoading />;

  const multi = key === "p11" || key === "p12";
  const secs = multi ? t.seconds[qi] : t.seconds[0];

  return (
    <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/cefr/speaking"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          Part {g.meta.part} · {g.meta.level}
        </p>
      </div>

      <h1 className="text-[22px] font-extrabold text-white leading-tight mt-3">
        {g.title}
      </h1>

      <div className="flex gap-2 mt-3">
        {([["learn", "O'rganish"], ["do", "Mashq qilish"]] as const).map(
          ([k, lbl]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className="flex-1 rounded-xl px-3 py-2 text-[12.5px] font-bold border"
              style={{
                background: tab === k ? "#2B49C8" : JSA.card,
                borderColor: tab === k ? "#2B49C8" : JSA.cardBorder,
                color: tab === k ? "#fff" : "#94A3B8",
              }}
            >
              {lbl}
            </button>
          ))}
      </div>

      {/* ============ O'RGANISH ============ */}
      {tab === "learn" && (
        <>
          <div className="student-study-card rounded-2xl border p-3.5 mt-3" style={card}>
            <p className="text-[12.5px] text-slate-300 leading-relaxed">
              {g.idea}
            </p>
            <p className="text-[11px] text-brand-300 mt-2">
              Vaqt: {g.seconds} soniya · mos so'z soni: {g.words[0]}-
              {g.words[1]}
            </p>
          </div>

          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-4 mb-1.5">
            Shablon — qaysi soniyada nima aytiladi
          </p>
          <div className="space-y-2">
            {g.template.map((s: Any, i: number) => (
              <button
                key={i}
                onClick={() => setOpenStep(openStep === i ? null : i)}
                className="w-full text-left rounded-2xl border p-3.5"
                style={card}
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-brand-300 bg-brand-600/15 rounded-full px-2 py-0.5 shrink-0">
                    {s.t}
                  </span>
                  <span className="text-white font-bold text-[13.5px]">
                    {s.name}
                  </span>
                </div>
                <p className="text-[11.5px] text-slate-400 leading-snug mt-1">
                  {s.how}
                </p>
                {openStep === i && (
                  <p className="text-[12px] text-emerald-200 bg-emerald-400/5 border border-emerald-400/15 rounded-lg px-2 py-1.5 mt-2">
                    {s.eg}
                  </p>
                )}
              </button>
            ))}
          </div>

          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-4 mb-1.5">
            Tayyor iboralar
          </p>
          <div className="space-y-2">
            {Object.entries(g.phrases).map(([k, arr]: Any) => (
              <div key={k} className="student-study-card rounded-2xl border p-3" style={card}>
                <p className="text-[11px] font-bold text-brand-300 mb-1">
                  {k}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {arr.map((p: string, i: number) => (
                    <span
                      key={i}
                      className="text-[11.5px] text-slate-200 bg-white/5 border border-white/10 rounded-lg px-2 py-1"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-4 mb-1.5">
            Namuna javob
          </p>
          <div className="student-study-card rounded-2xl border p-3.5" style={card}>
            <p className="text-[11.5px] text-slate-400 italic leading-relaxed">
              {g.sample_q}
            </p>
            <p className="text-[12.5px] text-emerald-100 leading-relaxed mt-2 whitespace-pre-line">
              {g.sample}
            </p>
            <div className="mt-3 space-y-1">
              {g.notes.map((n: string, i: number) => (
                <p key={i} className="text-[11.5px] text-amber-200 leading-snug">
                  • {n}
                </p>
              ))}
            </div>
          </div>

          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-4 mb-1.5">
            Rasmiy baholash — {g.band.title}
          </p>
          <div className="student-study-card rounded-2xl border p-3.5" style={card}>
            {g.band.scale.map((b: Any) => (
              <div key={b.point} className="flex gap-2 py-1">
                <span className="w-5 shrink-0 text-[13px] font-extrabold text-brand-300 text-center">
                  {b.point}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] font-semibold text-slate-200">
                    {b.label}
                  </p>
                  <p className="text-[11px] text-slate-400 leading-snug">
                    {b.why}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="student-study-card rounded-2xl border p-3.5 mt-3" style={card}>
            <p className="text-[12px] font-bold text-rose-300 mb-1.5">
              Eng ko'p uchraydigan xato
            </p>
            {g.avoid.map((a: string, i: number) => (
              <p key={i} className="flex gap-1.5 text-[12px] text-slate-300 mt-1">
                <X size={13} className="text-rose-400 shrink-0 mt-0.5" />
                <span>{a}</span>
              </p>
            ))}
          </div>
        </>
      )}

      {/* ============ MASHQ ============ */}
      {tab === "do" && (
        <>
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={() => setIdx((i) => Math.max(0, i - 1))}
              disabled={idx === 0}
              className="rounded-xl border px-3 py-2 text-[12px] text-slate-300 disabled:opacity-30"
              style={card}
            >
              ‹
            </button>
            <span className="flex-1 text-center text-[12px] text-slate-400">
              Vazifa {t.idx + 1} / {t.total} — {t.topic}
            </span>
            <button
              onClick={() => setIdx((i) => i + 1)}
              className="rounded-xl border px-3 py-2 text-[12px] text-slate-300"
              style={card}
            >
              ›
            </button>
          </div>

          {/* rasm tavsiflari */}
          {key === "p12" && (
            <div className="grid grid-cols-1 gap-2 mt-3">
              {[["A", t.scene_a, t.img_a], ["B", t.scene_b, t.img_b]].map(
                ([lb, sc, im]: Any) => (
                  <div key={lb} className="student-study-card rounded-2xl border p-3" style={card}>
                    <p className="text-[10px] font-bold text-brand-300 mb-1">
                      RASM {lb}
                    </p>
                    {im ? (
                      <StudentImage src={im} alt="" className="w-full rounded-xl" />
                    ) : (
                      <p className="text-[12px] text-slate-300 leading-relaxed">
                        {sc}
                      </p>
                    )}
                  </div>
                ))}
            </div>
          )}
          {key === "p2" && (
            <div className="student-study-card rounded-2xl border p-3 mt-3" style={card}>
              <p className="text-[10px] font-bold text-brand-300 mb-1">RASM</p>
              {t.img ? (
                <StudentImage src={t.img} alt="" className="w-full rounded-xl" />
              ) : (
                <p className="text-[12px] text-slate-300 leading-relaxed">
                  {t.scene}
                </p>
              )}
              <p className="text-[10.5px] text-slate-500 mt-1.5">
                Rasmni tasvirlash talab qilinmaydi — u faqat mavzuni
                bildiradi.
              </p>
            </div>
          )}

          {/* savol(lar) */}
          <div className="student-study-card rounded-2xl border p-3.5 mt-2.5" style={card}>
            {key === "p3" ? (
              <>
                <p className="text-[14px] font-bold text-white leading-snug">
                  {t.topic}
                </p>
                <div className="grid grid-cols-2 gap-2 mt-2.5">
                  <div>
                    <p className="text-[10px] font-bold text-emerald-300 mb-1">
                      FOR
                    </p>
                    {t.for.map((x: string, i: number) => (
                      <p key={i} className="text-[11.5px] text-slate-300 leading-snug mb-1">
                        • {x}
                      </p>
                    ))}
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-rose-300 mb-1">
                      AGAINST
                    </p>
                    {t.against.map((x: string, i: number) => (
                      <p key={i} className="text-[11.5px] text-slate-300 leading-snug mb-1">
                        • {x}
                      </p>
                    ))}
                  </div>
                </div>
                <p className="text-[10.5px] text-slate-500 mt-2">
                  Har ro'yxatdan IKKITADAN band tanlang.
                </p>
              </>
            ) : multi ? (
              <>
                <div className="flex gap-1.5 mb-2">
                  {t.questions.map((_: Any, i: number) => (
                    <button
                      key={i}
                      onClick={() => { setQi(i); setRes(null); }}
                      className="flex-1 rounded-lg px-2 py-1 text-[11px] font-bold border"
                      style={{
                        background: qi === i ? "#2B49C8" : "transparent",
                        borderColor: qi === i ? "#2B49C8" : JSA.cardBorder,
                        color: qi === i ? "#fff" : "#94A3B8",
                      }}
                    >
                      {key === "p11" ? i + 1 : i + 4}-savol
                    </button>
                  ))}
                </div>
                <p className="text-[14px] text-white leading-relaxed">
                  {t.questions[qi]}
                </p>
              </>
            ) : (
              t.questions.map((q: string, i: number) => (
                <p key={i} className="text-[13.5px] text-white leading-relaxed mb-1.5">
                  {i + 1}. {q}
                </p>
              ))
            )}
          </div>

          {/* tayyorgarlik taymeri */}
          {t.prep > 0 && !res && (
            <div className="mt-2.5">
              {!prepOn && prep === 0 ? (
                <button
                  onClick={startPrep}
                  className="w-full rounded-xl border px-4 py-2.5 text-[13px] font-semibold text-slate-200"
                  style={card}
                >
                  Tayyorgarlik vaqtini boshlash ({t.prep} soniya)
                </button>
              ) : (
                <div className="student-study-card flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5" style={card}
                >
                  <Clock size={14} className="text-amber-400" />
                  <span className="text-[13px] font-bold text-white tabular-nums">
                    Tayyorgarlik: {prep}s
                  </span>
                </div>
              )}
            </div>
          )}

          {!res && (
            <div className="mt-2.5">
              <SpeakRecorder
                seconds={secs}
                busy={busy}
                onDone={send}
                label={`Javob berish (${secs} soniya)`}
              />
            </div>
          )}
          {busy && (
            <p className="text-[12px] text-slate-400 text-center mt-2">
              Javob tahlil qilinmoqda…
            </p>
          )}
          {err && (
            <p className="text-[12px] text-rose-300 text-center mt-2">{err}</p>
          )}

          {/* natija */}
          {res && (
            <div className="mt-3 space-y-2.5">
              <div className="student-study-card rounded-2xl border p-4 text-center" style={card}>
                <p className="text-[40px] font-extrabold text-white leading-none">
                  {res.point}
                  <span className="text-[18px] text-slate-500">/{res.max}</span>
                </p>
                <p className="text-[13px] font-bold text-brand-300 mt-1">
                  {res.band_label}
                </p>
                <p className="text-[11.5px] text-slate-400 leading-snug mt-1">
                  {res.band_why}
                </p>
                {!res.from_ai && (
                  <p className="text-[10.5px] text-amber-300 mt-2">
                    Bu avtomat tahlil bahosi — ekspert bahosi hozir
                    mavjud emas.
                  </p>
                )}
                {res.xp > 0 && (
                  <p className="text-[11px] text-emerald-300 mt-1">
                    +{res.xp} XP
                  </p>
                )}
              </div>

              <div className="student-study-card rounded-2xl border p-3.5" style={card}>
                <p className="text-[12px] font-bold text-white mb-2">
                  Tahlil
                </p>
                {res.tips.map((c: Any, i: number) => (
                  <div key={i} className="flex gap-2 mb-2">
                    <span className="shrink-0 mt-0.5">
                      {c.ok === true ? (
                        <Check size={14} className="text-emerald-400" />
                      ) : c.ok === false ? (
                        <X size={14} className="text-rose-400" />
                      ) : (
                        <AlertTriangle size={13} className="text-amber-400" />
                      )}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-semibold text-slate-200">
                        {c.label}
                      </p>
                      <p className="text-[11.5px] text-slate-400 leading-snug">
                        {c.detail}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {res.ai && (
                <div className="student-study-card rounded-2xl border p-3.5" style={card}>
                  <p className="text-[12px] font-bold text-white mb-1.5">
                    Ekspert izohi
                  </p>
                  <p className="text-[12.5px] text-slate-200 leading-relaxed whitespace-pre-line">
                    {res.ai}
                  </p>
                </div>
              )}

              <div className="student-study-card rounded-2xl border p-3.5" style={card}>
                <p className="text-[12px] font-bold text-white mb-1.5">
                  Siz aytgan matn
                </p>
                <p className="text-[12.5px] text-slate-300 leading-relaxed">
                  {res.transcript}
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setRes(null)}
                  className="flex-1 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-bold text-white"
                >
                  Qayta javob berish
                </button>
                <button
                  onClick={() => {
                    if (multi && qi + 1 < t.questions.length) {
                      setQi(qi + 1); setRes(null);
                    } else { setIdx(idx + 1); }
                  }}
                  className="flex-1 rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-200"
                  style={card}
                >
                  Keyingisi
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
