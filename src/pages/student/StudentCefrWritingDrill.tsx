import { StudentLoading } from "../../components/StudentLoading";
import { StudentIcon } from "../../components/StudentIcon";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, X } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * CEFR WRITING — MAYDA KO'NIKMA MASHQLARI (2026-08-26).
 *
 * NEGA MAYDA MASHQ. To'liq xatni avtomat baholab bo'lmaydi,
 * lekin uni tashkil qiladigan ko'nikmalarni baholash mumkin:
 * uslubni tanish, ochilishga mos yopilish, abzatslar tartibi,
 * band qamrovi. Bular mustahkam bo'lmasa, to'liq matn yozganda
 * baribir buziladi.
 *
 * UCH XIL JAVOB SHAKLI bitta ekranda:
 *   variant tanlash (w_register, w_formal, w_close, w_spot,
 *                    w_missing)
 *   yozib kiritish (w_phrase)
 *   tartibda bosish (w_order)
 */
export default function StudentCefrWritingDrill() {
  const { kind = "" } = useParams();
  const [items, setItems] = useState<Any[]>([]);
  const [idx, setIdx] = useState(0);
  const [count, setCount] = useState(10);
  const [started, setStarted] = useState(false);
  const [pick, setPick] = useState<number | null>(null);
  const [typed, setTyped] = useState("");
  const [seq, setSeq] = useState<number[]>([]);
  const [res, setRes] = useState<Any>(null);
  const [right, setRight] = useState(0);
  const [metaLoading, setMetaLoading] = useState(true);
  const [meta, setMeta] = useState<Any>({});
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api
      .get<Any>(`/student/cefr/writing/drill?kind=${kind}&count=${count}`)
      .then((r) => {
        setItems(r.items || []);
        setMeta({ total: r.total, solved: r.solved });
        setIdx(0);
        setRight(0);
        setStarted(true);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [kind, count]);

  useEffect(() => {
    setMetaLoading(true);
    api
      .get<Any>(`/student/cefr/writing/drill?kind=${kind}&count=1`)
      .then((r) => setMeta({ total: r.total, solved: r.solved }))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setMetaLoading(false));
  }, [kind]);

  const q = items[idx];
  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  const send = async (answer: Any) => {
    if (busy || !q) return;
    setBusy(true);
    try {
      const r = await api.post<Any>("/student/cefr/writing/drill/answer", {
        kind: q.kind, idx: q.idx, answer,
      });
      setRes(r);
      if (r.correct) setRight((x) => x + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const next = () => {
    setRes(null);
    setPick(null);
    setTyped("");
    setSeq([]);
    setIdx((i) => i + 1);
  };

  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;

  const Head = (
    <div className="student-lesson-heading student-hero student-pattern flex items-center gap-2.5 text-white">
      <Link
        to="/student/cefr/writing"
        className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
        style={card}
      >
        <ArrowLeft size={18} />
      </Link>
      <p className="text-[15px] font-extrabold tracking-wide flex-1">
        CEFR Writing mashqi
      </p>
    <StudentIcon name="writing" size={42} />
      </div>
  );

  /* ---------- boshlanish ekrani ---------- */
  if (metaLoading && !started) return <StudentLoading />;
  if (err && !started) return <div role="alert" className="max-w-md mx-auto p-5"><p className="student-panel p-5 text-red-700">{err}</p><Link to="/student/cefr/writing" className="block text-center mt-4 text-white">Mashqlar ro‘yxatiga qaytish</Link></div>;

  if (!started)
    return (
      <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
        {Head}
        <div className="student-study-card rounded-2xl border p-4 mt-4" style={card}>
          <p className="text-white font-bold text-[15px]">
            Nechta mashq ishlaysiz?
          </p>
          <p className="text-[11.5px] text-slate-400 mt-1">
            Bazada {meta.total || 0} ta · siz {meta.solved || 0} tasini
            to'g'ri ishlagansiz. Avval ishlanmaganlari chiqadi.
          </p>
          <div className="flex gap-2 mt-3">
            {[10, 20, 30].map((n) => (
              <button
                key={n}
                onClick={() => setCount(n)}
                className="flex-1 rounded-xl px-3 py-2.5 text-sm font-bold border"
                style={{
                  background: count === n ? "#2B49C8" : JSA.card,
                  borderColor: count === n ? "#2B49C8" : JSA.cardBorder,
                  color: count === n ? "#fff" : "#94A3B8",
                }}
              >
                {n}
              </button>
            ))}
          </div>
          <button
            onClick={load}
            className="w-full mt-3 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white"
          >
            Boshlash
          </button>
        </div>
      </div>
    );

  /* ---------- yakun ---------- */
  if (!q)
    return (
      <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
        {Head}
        <div className="student-study-card rounded-2xl border p-5 mt-4 text-center" style={card}>
          <p className="text-[34px] font-extrabold text-white">
            {right}/{items.length}
          </p>
          <p className="text-[12px] text-slate-400 mt-1">
            {right === items.length
              ? "Hammasi to'g'ri — bu ko'nikma mustahkam."
              : "Xato qilganlaringizni qayta ishlang — izohlarni "
                + "o'qib chiqing."}
          </p>
          <div className="flex gap-2 mt-4">
            <button
              onClick={load}
              className="flex-1 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-bold text-white"
            >
              Yana
            </button>
            <Link
              to="/student/cefr/writing"
              className="student-study-card flex-1 rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-300"
              style={card}
            >
              Bo'limga
            </Link>
          </div>
        </div>
      </div>
    );

  /* ---------- savol ---------- */
  return (
    <div className="student-study max-w-md mx-auto px-4 pt-5 pb-8">
      {Head}
      <div className="flex items-center gap-2 mt-3">
        <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${(idx / items.length) * 100}%` }}
          />
        </div>
        <span className="text-[11px] text-slate-400 shrink-0">
          {idx + 1}/{items.length}
        </span>
      </div>

      <div className="student-study-card rounded-2xl border p-4 mt-3" style={card}>
        <p className="text-[13.5px] text-slate-100 leading-relaxed whitespace-pre-line">
          {q.prompt}
        </p>
      </div>

      {/* --- variant tanlash --- */}
      {q.options && (
        <div className="space-y-2 mt-3">
          {q.options.map((o: string, i: number) => {
            const isPick = pick === i;
            // Server javob MATNINI qaytaradi (indeks emas) —
            // to'g'ri variant shu matn bo'yicha topiladi.
            const isRight = !!res && !res.correct && o === res.expected;
            let bg = JSA.card;
            let bd = JSA.cardBorder;
            if (res) {
              if (isPick && res.correct) { bg = "#0C3A2A"; bd = "#1B8A5A"; }
              else if (isPick) { bg = "#3A1220"; bd = "#8A2540"; }
              else if (isRight) { bg = "#0C3A2A"; bd = "#1B8A5A"; }
            } else if (isPick) { bg = "#0c2258"; bd = "#2B3B8A"; }
            return (
              <button
                key={i}
                disabled={!!res}
                onClick={() => { setPick(i); send(i); }}
                className="w-full text-left rounded-2xl border px-3.5 py-3 text-[13px] text-slate-100 leading-snug"
                style={{ background: bg, borderColor: bd }}
              >
                <span className="font-bold text-brand-300 mr-2">
                  {String.fromCharCode(65 + i)}
                </span>
                {o}
                {isRight ? " ✓" : ""}
              </button>
            );
          })}
        </div>
      )}

      {/* --- yozib kiritish --- */}
      {q.kind === "w_phrase" && (
        <div className="mt-3">
          <input
            value={typed}
            disabled={!!res}
            onChange={(e) => setTyped(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && typed) send(typed); }}
            placeholder="Tushib qolgan so'zni yozing"
            className="w-full rounded-xl border px-3.5 py-3 text-[14px] text-white outline-none"
            style={{ background: JSA.card, borderColor: JSA.cardBorder }}
          />
          {!res && (
            <button
              disabled={!typed}
              onClick={() => send(typed)}
              className="w-full mt-2 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-40"
            >
              Tekshirish
            </button>
          )}
        </div>
      )}

      {/* --- tartibda bosish --- */}
      {q.kind === "w_order" && (
        <div className="mt-3">
          <p className="text-[11px] text-slate-500 mb-2">
            Abzatslarni to'g'ri ketma-ketlikda bosing.
          </p>
          <div className="space-y-2">
            {q.pieces.map((p: Any, i: number) => {
              const at = seq.indexOf(i);
              return (
                <button
                  key={i}
                  disabled={!!res || at >= 0}
                  onClick={() => setSeq((s) => [...s, i])}
                  className="w-full text-left rounded-2xl border px-3.5 py-2.5"
                  style={{
                    background: at >= 0 ? "#0c2258" : JSA.card,
                    borderColor: at >= 0 ? "#2B3B8A" : JSA.cardBorder,
                    opacity: at >= 0 ? 0.55 : 1,
                  }}
                >
                  {at >= 0 && (
                    <span className="text-[11px] font-bold text-brand-300 mr-2">
                      {at + 1}.
                    </span>
                  )}
                  <span className="text-[12.5px] text-slate-100 leading-snug">
                    {p.text}
                  </span>
                  {res && (
                    <span className="block text-[10px] text-amber-300 mt-1 uppercase tracking-wide">
                      {p.role}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          {!res && (
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => setSeq([])}
                className="rounded-xl border px-4 py-3 text-sm font-semibold text-slate-300"
                style={card}
              >
                Tozalash
              </button>
              <button
                disabled={seq.length !== q.pieces.length}
                onClick={() => send(seq)}
                className="flex-1 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-40"
              >
                Tekshirish
              </button>
            </div>
          )}
        </div>
      )}

      {/* --- natija --- */}
      {res && (
        <div
          className="rounded-2xl border p-3.5 mt-3"
          style={{
            background: res.correct ? "#0C3A2A" : "#3A1220",
            borderColor: res.correct ? "#1B8A5A" : "#8A2540",
          }}
        >
          <p className="flex items-center gap-1.5 text-[13px] font-bold text-white">
            {res.correct ? <Check size={15} /> : <X size={15} />}
            {res.correct ? "To'g'ri" : "Xato"}
            {res.xp > 0 && (
              <span className="ml-auto text-[11px] text-emerald-200">
                +{res.xp} XP
              </span>
            )}
          </p>
          {!res.correct && (
            <p className="text-[12.5px] text-slate-100 mt-1.5">
              To'g'ri javob: <b>{res.expected}</b>
            </p>
          )}
          {res.explain && (
            <p className="text-[12px] text-slate-300 leading-relaxed mt-1.5">
              {res.explain}
            </p>
          )}
          <button
            onClick={next}
            className="w-full mt-3 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-bold text-white"
          >
            {idx + 1 >= items.length ? "Yakunlash" : "Keyingisi"}
          </button>
        </div>
      )}
    </div>
  );
}
