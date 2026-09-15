import { StudentLoading } from "../../components/StudentLoading";
import { StudentImage } from "../../components/StudentIcon";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, X, AlertTriangle, Clock } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import SpeakRecorder from "../../components/SpeakRecorder";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * MULTILEVEL SPEAKING — FREE MOCK (2026-08-26).
 *
 * Jahongir: "Multilevel Free Mock olsayam bo'lsin bahosini
 * chiqarib bersin ... 0-75 orasida ballini hisoblab chiqarib
 * berishing kerak."
 *
 * IMTIHON OQIMI aynan haqiqiy tartibda:
 *   Part 1.1  3 savol · 30 soniyadan · tayyorgarliksiz
 *   Part 1.2  3 savol · 45/30/30 soniya · tayyorgarliksiz
 *   Part 2    3 savol birdaniga · 60s o'ylash · 120s javob
 *   Part 3    1 mavzu · 60s o'ylash · 120s javob
 *
 * MUHIM QOIDA — ORQAGA QAYTIB BO'LMAYDI. Haqiqiy imtihonda ham
 * javobni qayta yozib bo'lmaydi. Shuning uchun bu yerda ham har
 * savol bir marta: mikrofon o'chdi — keyingisiga o'tildi. Mashq
 * qilish uchun "Qism bo'yicha tayyorgarlik" bo'limi bor.
 */
type Step = { part: string; taskIdx: number; qi: number;
              seconds: number; prep: number };

export default function StudentCefrSpeakingMock() {
  const [mock, setMock] = useState<Any>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [at, setAt] = useState(-1);          // -1 = boshlanish ekrani
  const [answers, setAnswers] = useState<Any[]>([]);
  const [prep, setPrep] = useState(0);
  const [prepOn, setPrepOn] = useState(false);
  const [res, setRes] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const tick = useRef<number | null>(null);

  useEffect(() => {
    api.get<Any>("/student/cefr/speaking/mock")
      .then((r) => {
        setMock(r);
        const st: Step[] = [];
        (r.tasks || []).forEach((t: Any, ti: number) => {
          const n = t.part === "p11" || t.part === "p12"
            ? t.questions.length : 1;
          for (let q = 0; q < n; q++) {
            st.push({ part: t.part, taskIdx: ti, qi: q,
                      seconds: t.seconds[q] ?? t.seconds[0],
                      prep: q === 0 ? t.prep : 0 });
          }
        });
        setSteps(st);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const stop = useCallback(() => {
    if (tick.current) window.clearInterval(tick.current);
    tick.current = null;
  }, []);
  useEffect(() => stop, [stop]);

  const beginPrep = useCallback((sec: number) => {
    setPrep(sec);
    setPrepOn(true);
    stop();
    tick.current = window.setInterval(() => {
      setPrep((s) => {
        if (s <= 1) { stop(); setPrepOn(false); return 0; }
        return s - 1;
      });
    }, 1000);
  }, [stop]);

  const goto = (i: number) => {
    setAt(i);
    const st = steps[i];
    if (st?.prep) beginPrep(st.prep);
    else { setPrepOn(false); setPrep(0); }
  };

  const onDone = (r: Any) => {
    const st = steps[at];
    const t = mock.tasks[st.taskIdx];
    setAnswers((a) => [...a, {
      part: st.part, idx: t.idx, qi: st.qi,
      seconds: r.used || st.seconds,
      transcript: r.transcript || "", audio: r.audio, mime: r.mime,
    }]);
    if (at + 1 < steps.length) goto(at + 1);
    else setAt(steps.length);        // yakun ekrani
  };

  const finish = async () => {
    setBusy(true);
    setErr("");
    try {
      const out = await api.post<Any>("/student/cefr/speaking/mock/score",
        { items: answers });
      setRes(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const Head = (
    <div className="flex items-center gap-2.5 text-white">
      <Link
        to="/student/cefr/speaking"
        className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
        style={card}
      >
        <ArrowLeft size={18} />
      </Link>
      <p className="text-[15px] font-extrabold tracking-wide flex-1">
        Multilevel Speaking — Free Mock
      </p>
    </div>
  );

  if (err && !mock)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!mock)
    return <StudentLoading />;

  /* ---------- NATIJA ---------- */
  if (res) {
    const cl = res.score >= 65 ? "#34D399" : res.score >= 51 ? "#60A5FA"
      : res.score >= 30 ? "#FBBF24" : "#FB7185";
    return (
      <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
        {Head}
        <div className="student-study-card rounded-2xl border p-5 mt-4 text-center" style={card}>
          <p className="text-[56px] font-extrabold leading-none"
             style={{ color: cl }}>
            {res.score}
          </p>
          <p className="text-[12px] text-slate-400 mt-1">
            {res.score_max} balldan · xom ball {res.raw}/{res.raw_max}
          </p>
          <p className="text-[30px] font-extrabold text-white mt-2">
            {res.level}
          </p>
          <p className="text-[12px] text-slate-400 leading-snug mt-1">
            {res.level_desc}
          </p>
          {res.next_level && (
            <p className="text-[12px] text-brand-300 mt-2">
              {res.next_level} darajasiga yana <b>{res.next_gap}</b> ball
            </p>
          )}
          {res.xp > 0 && (
            <p className="text-[11px] text-emerald-300 mt-1">+{res.xp} XP</p>
          )}
        </div>

        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-4 mb-1.5">
          Blok bo'yicha
        </p>
        <div className="student-study-card rounded-2xl border p-3.5" style={card}>
          {res.blocks.map((b: Any) => (
            <div key={b.block} className="py-1.5">
              <div className="flex items-center gap-2">
                <span className="flex-1 text-[12.5px] text-slate-200">
                  {b.title}
                </span>
                <span className="text-[14px] font-extrabold text-white tabular-nums">
                  {b.point}/{b.max}
                </span>
                <span className="w-20 text-right text-[11px] font-bold text-brand-300">
                  {b.label}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug mt-0.5">
                {b.why}
              </p>
            </div>
          ))}
        </div>

        {(res.detail || []).map((d: Any, i: number) => (
          <div key={i} className="student-study-card rounded-2xl border p-3.5 mt-2.5" style={card}>
            <p className="text-[12px] font-bold text-white mb-2">
              {d.part === "p11" ? "Part 1.1" : d.part === "p12" ? "Part 1.2"
                : d.part === "p2" ? "Part 2" : "Part 3"}
              {" — "}{d.point}/{d.max}
              {!d.from_ai && (
                <span className="text-[10px] text-amber-300 ml-2">
                  avtomat tahlil
                </span>
              )}
            </p>
            {(d.tips || []).map((c: Any, k: number) => (
              <div key={k} className="flex gap-2 mb-1.5">
                <span className="shrink-0 mt-0.5">
                  {c.ok === true ? <Check size={13} className="text-emerald-400" />
                    : c.ok === false ? <X size={13} className="text-rose-400" />
                      : <AlertTriangle size={12} className="text-amber-400" />}
                </span>
                <p className="flex-1 text-[11.5px] text-slate-400 leading-snug">
                  <b className="text-slate-200">{c.label}.</b> {c.detail}
                </p>
              </div>
            ))}
            {d.ai && (
              <p className="text-[12px] text-slate-200 leading-relaxed whitespace-pre-line mt-2 pt-2 border-t border-white/10">
                {d.ai}
              </p>
            )}
            {d.transcript && (
              <p className="text-[11.5px] text-slate-500 leading-relaxed mt-2">
                <b>Siz aytdingiz:</b> {d.transcript}
              </p>
            )}
          </div>
        ))}

        <Link
          to="/student/cefr/speaking"
          className="block text-center mt-4 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white"
        >
          Bo'limga qaytish
        </Link>
      </div>
    );
  }

  /* ---------- BOSHLANISH ---------- */
  if (at < 0)
    return (
      <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
        {Head}
        <div className="student-study-card rounded-2xl border p-4 mt-4" style={card}>
          <p className="text-white font-bold text-[15px]">
            Imtihon tartibi
          </p>
          <div className="space-y-1.5 mt-2.5">
            {(mock.format || []).map((f: Any) => (
              <div key={f.part} className="flex items-center gap-2 text-[11.5px]">
                <span className="w-8 shrink-0 font-bold text-brand-300">
                  {f.part}
                </span>
                <span className="w-7 shrink-0 text-slate-500">{f.level}</span>
                <span className="flex-1 text-slate-300">
                  {f.questions} savol
                </span>
                <span className="shrink-0 text-slate-400">
                  {f.prep ? `${f.prep}s + ` : ""}
                  {f.seconds.join("/")}s
                </span>
              </div>
            ))}
          </div>
          <p className="text-[11.5px] text-amber-200 leading-relaxed mt-3">
            Diqqat: har savol BIR MARTA. Mikrofon o'zi o'chgach
            keyingisiga o'tiladi va orqaga qaytib bo'lmaydi —
            haqiqiy imtihondagidek.
          </p>
          <p className="text-[11px] text-slate-500 leading-relaxed mt-2">
            Tinch xonada, mikrofoni ishlaydigan qurilmada boshlang.
            Umumiy davomiyligi taxminan 9-10 daqiqa.
          </p>
          <button
            onClick={() => goto(0)}
            className="w-full mt-3 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white"
          >
            Mockni boshlash
          </button>
        </div>
      </div>
    );

  /* ---------- YAKUN ---------- */
  if (at >= steps.length)
    return (
      <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
        {Head}
        <div className="student-study-card rounded-2xl border p-5 mt-4 text-center" style={card}>
          <p className="text-white font-bold text-[16px]">
            Hamma savollarga javob berildi
          </p>
          <p className="text-[12px] text-slate-400 mt-1.5 leading-relaxed">
            {answers.length} ta javob yig'ildi. Baholash bir necha
            soniya oladi.
          </p>
          <button
            onClick={finish}
            disabled={busy}
            className="w-full mt-4 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-40"
          >
            {busy ? "Baholanmoqda…" : "Natijani olish"}
          </button>
          {err && <p className="text-[12px] text-rose-300 mt-2">{err}</p>}
        </div>
      </div>
    );

  /* ---------- SAVOL ---------- */
  const st = steps[at];
  const t = mock.tasks[st.taskIdx];
  const pname = t.part === "p11" ? "1.1" : t.part === "p12" ? "1.2"
    : t.part === "p2" ? "2" : "3";

  return (
    <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
      {Head}
      <div className="flex items-center gap-2 mt-3">
        <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
          <div className="h-full rounded-full bg-brand-500 transition-all"
               style={{ width: `${(at / steps.length) * 100}%` }} />
        </div>
        <span className="text-[11px] text-slate-400 shrink-0">
          {at + 1}/{steps.length}
        </span>
      </div>
      <p className="text-[11px] font-bold text-brand-300 mt-2">
        Part {pname} · {t.level}
      </p>

      {t.part === "p12" && (
        <div className="grid grid-cols-1 gap-2 mt-2">
          {[["A", t.scene_a, t.img_a], ["B", t.scene_b, t.img_b]].map(
            ([lb, sc, im]: Any) => (
              <div key={lb} className="student-study-card rounded-2xl border p-3" style={card}>
                <p className="text-[10px] font-bold text-brand-300 mb-1">
                  RASM {lb}
                </p>
                {im ? <StudentImage src={im} alt="" className="w-full rounded-xl" />
                  : <p className="text-[12px] text-slate-300 leading-relaxed">{sc}</p>}
              </div>
            ))}
        </div>
      )}
      {t.part === "p2" && (
        <div className="student-study-card rounded-2xl border p-3 mt-2" style={card}>
          <p className="text-[10px] font-bold text-brand-300 mb-1">RASM</p>
          {t.img ? <StudentImage src={t.img} alt="" className="w-full rounded-xl" />
            : <p className="text-[12px] text-slate-300 leading-relaxed">{t.scene}</p>}
        </div>
      )}

      <div className="student-study-card rounded-2xl border p-3.5 mt-2.5" style={card}>
        {t.part === "p3" ? (
          <>
            <p className="text-[14px] font-bold text-white leading-snug">
              {t.topic}
            </p>
            <div className="grid grid-cols-2 gap-2 mt-2.5">
              <div>
                <p className="text-[10px] font-bold text-emerald-300 mb-1">FOR</p>
                {t.for.map((x: string, i: number) => (
                  <p key={i} className="text-[11.5px] text-slate-300 leading-snug mb-1">• {x}</p>
                ))}
              </div>
              <div>
                <p className="text-[10px] font-bold text-rose-300 mb-1">AGAINST</p>
                {t.against.map((x: string, i: number) => (
                  <p key={i} className="text-[11.5px] text-slate-300 leading-snug mb-1">• {x}</p>
                ))}
              </div>
            </div>
          </>
        ) : t.part === "p2" ? (
          t.questions.map((q: string, i: number) => (
            <p key={i} className="text-[13.5px] text-white leading-relaxed mb-1.5">
              {i + 1}. {q}
            </p>
          ))
        ) : (
          <p className="text-[15px] text-white leading-relaxed">
            {t.questions[st.qi]}
          </p>
        )}
      </div>

      {prepOn && (
        <div className="flex items-center justify-center gap-2 rounded-xl border px-4 py-3 mt-2.5"
             style={{ background: "#3A2A12", borderColor: "#8A6A25" }}>
          <Clock size={15} className="text-amber-400" />
          <span className="text-[14px] font-bold text-amber-200 tabular-nums">
            O'ylash vaqti: {prep}s
          </span>
        </div>
      )}

      {!prepOn && (
        <div className="mt-2.5">
          <SpeakRecorder
            key={at}
            seconds={st.seconds}
            onDone={onDone}
            label={`Javob berish (${st.seconds} soniya)`}
          />
        </div>
      )}
    </div>
  );
}
