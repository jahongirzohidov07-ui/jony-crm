import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, Clock, X, AlertTriangle } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * CEFR WRITING — TO'LIQ YOZISH EKRANI (2026-08-26).
 *
 * IMTIHON SHAROITI. Uyda cheksiz vaqt bilan yozilgan xat imtihonga
 * tayyorlamaydi. Shuning uchun bu yerda:
 *   - vaqt hisoblagichi (1.1 = 7 daq, 1.2 = 23 daq, Part 2 = 30)
 *   - jonli so'z sanagichi (talab oralig'i rangi bilan)
 *   - topshiriq bandlari doim ko'z oldida
 *
 * VAQT TUGASA MATN O'CHMAYDI. Faqat ogohlantirish chiqadi va
 * o'quvchi baribir topshira oladi — maqsad jazolash emas, vaqt
 * hissini shakllantirish.
 *
 * TOPSHIRGANDAN KEYIN ikki qavat javob:
 *   1. Avtomat tekshiruv — har doim ishlaydi (so'z soni, band
 *      qamrovi, ochilish/yopilish, uslub, abzatslar).
 *   2. AI ekspert — daraja va uchta aniq tuzatish. Ishlamasa,
 *      birinchi qavat baribir to'liq javob beradi.
 * Va faqat SHUNDAN KEYIN namuna javob ochiladi — oldin ko'rsatilsa
 * ko'chirib yozish yo'li ochiq qolardi.
 */
export default function StudentCefrWritingExam() {
  const { tid = "" } = useParams();
  const [t, setT] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [sub, setSub] = useState<"1.1" | "1.2" | "2">("1.1");
  const [text, setText] = useState("");
  const [left, setLeft] = useState(0);
  const [running, setRunning] = useState(false);
  const [res, setRes] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [showModel, setShowModel] = useState(false);
  const tick = useRef<number | null>(null);

  useEffect(() => {
    api
      .get<Any>("/student/cefr/writing/task/" + tid)
      .then((r) => {
        setT(r);
        setSub(r.part === "2" ? "2" : "1.1");
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [tid]);

  const spec: Any =
    !t ? null : sub === "2" ? t : sub === "1.1" ? t.t11 : t.t12;

  const stop = useCallback(() => {
    if (tick.current) window.clearInterval(tick.current);
    tick.current = null;
  }, []);
  useEffect(() => stop, [stop]);

  const start = () => {
    if (!spec) return;
    setLeft(spec.minutes * 60);
    setRunning(true);
    stop();
    tick.current = window.setInterval(() => {
      setLeft((s) => (s <= 1 ? 0 : s - 1));
    }, 1000);
  };

  const words = (text.match(/[A-Za-z][A-Za-z'’-]*/g) || []).length;
  const lo = spec?.words?.[0] || 0;
  const hi = spec?.words?.[1] || 0;
  const wColor =
    words === 0 ? "#64748B"
      : words < lo ? "#F59E0B"
        : words > hi ? "#FB7185" : "#34D399";

  const submit = async () => {
    if (busy || !t) return;
    setBusy(true);
    stop();
    setRunning(false);
    try {
      const r = await api.post<Any>("/student/cefr/writing/submit", {
        task_id: t.id, part: sub, text,
      });
      setRes(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const reset = (nx: "1.1" | "1.2" | "2") => {
    setSub(nx);
    setText("");
    setRes(null);
    setShowModel(false);
    setRunning(false);
    setLeft(0);
    stop();
  };

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!t)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  const mm = String(Math.floor(left / 60)).padStart(2, "0");
  const ss = String(left % 60).padStart(2, "0");

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to={`/student/cefr/writing/tasks/${t.part === "2" ? "2" : "1"}`}
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          {t.part === "2" ? "Part 2" : t.topic}
        </p>
        <span className="text-[11px] font-bold text-brand-300 shrink-0">
          {spec?.level}
        </span>
      </div>

      {/* --- 1.1 / 1.2 almashtirgich --- */}
      {t.part === "1" && (
        <div className="flex gap-2 mt-3">
          {(["1.1", "1.2"] as const).map((p) => (
            <button
              key={p}
              onClick={() => reset(p)}
              className="flex-1 rounded-xl px-3 py-2 text-[12px] font-bold border"
              style={{
                background: sub === p ? "#2B49C8" : JSA.card,
                borderColor: sub === p ? "#2B49C8" : JSA.cardBorder,
                color: sub === p ? "#fff" : "#94A3B8",
              }}
            >
              Task {p} · {p === "1.1" ? "do'stga" : "rasmiy"}
            </button>
          ))}
        </div>
      )}

      {/* --- kelgan xabar --- */}
      {t.part === "1" && (
        <div className="rounded-2xl border p-3.5 mt-3" style={card}>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">
            Xabar: {t.from}
          </p>
          <p className="text-[12.5px] text-slate-200 leading-relaxed mt-1.5 whitespace-pre-line">
            {t.context}
          </p>
        </div>
      )}

      {/* --- topshiriq --- */}
      <div className="rounded-2xl border p-3.5 mt-2.5" style={card}>
        <p className="text-[13px] text-white leading-relaxed">
          {spec.prompt}
        </p>
        {spec.bullets?.length > 0 && (
          <ul className="mt-2 space-y-1">
            {spec.bullets.map((b: string, i: number) => (
              <li key={i} className="text-[12px] text-slate-300 flex gap-1.5">
                <span className="text-brand-300">•</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        )}
        <p className="text-[11px] text-slate-500 mt-2">
          {lo}-{hi} so'z · {spec.minutes} daqiqa
        </p>
      </div>

      {/* --- taymer + sanagich --- */}
      {!res && (
        <div className="flex items-center gap-2 mt-3">
          {!running ? (
            <button
              onClick={start}
              className="flex-1 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-bold text-white"
            >
              Vaqtni boshlash ({spec.minutes} daq)
            </button>
          ) : (
            <div
              className="flex items-center gap-1.5 rounded-xl border px-3 py-2.5"
              style={{
                background: left === 0 ? "#3A1220" : JSA.card,
                borderColor: left === 0 ? "#8A2540" : JSA.cardBorder,
              }}
            >
              <Clock size={14} className={left === 0 ? "text-rose-400" : "text-slate-400"} />
              <span
                className="text-[14px] font-bold tabular-nums"
                style={{ color: left === 0 ? "#FB7185" : "#E2E8F0" }}
              >
                {mm}:{ss}
              </span>
            </div>
          )}
          <div
            className="rounded-xl border px-3 py-2.5 text-[13px] font-bold tabular-nums"
            style={{ background: JSA.card, borderColor: JSA.cardBorder, color: wColor }}
          >
            {words} / {lo}-{hi}
          </div>
        </div>
      )}

      {running && left === 0 && !res && (
        <p className="flex items-center gap-1.5 text-[11.5px] text-rose-300 mt-2">
          <AlertTriangle size={13} />
          Vaqt tugadi. Matn saqlanib turibdi — yakunlab topshirsangiz
          bo'ladi.
        </p>
      )}

      {/* --- yozish maydoni --- */}
      {!res && (
        <>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={14}
            placeholder={
              sub === "1.1"
                ? "Hi ...,\n\nHow are you? ..."
                : sub === "1.2"
                  ? "Dear Sir or Madam,\n\nI am writing to ..."
                  : "Yozishni boshlang…"
            }
            className="w-full mt-3 rounded-2xl border px-3.5 py-3 text-[13.5px] text-white leading-relaxed outline-none resize-y"
            style={{ background: JSA.card, borderColor: JSA.cardBorder }}
          />
          <button
            disabled={busy || words < 15}
            onClick={submit}
            className="w-full mt-2 rounded-xl bg-brand-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-40"
          >
            {busy ? "Tekshirilmoqda…" : "Topshirish va baho olish"}
          </button>
          <p className="text-[10.5px] text-slate-500 mt-1.5 text-center">
            Namuna javob faqat topshirgandan keyin ochiladi.
          </p>
        </>
      )}

      {/* --- natija --- */}
      {res && (
        <div className="mt-3 space-y-2.5">
          <div className="rounded-2xl border p-4 text-center" style={card}>
            <p
              className="text-[40px] font-extrabold leading-none"
              style={{
                color: res.score >= 80 ? "#34D399"
                  : res.score >= 60 ? "#FBBF24" : "#FB7185",
              }}
            >
              {res.score}
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              format bo'yicha ball · {res.words} so'z · {res.paras} abzats
            </p>
            {res.xp > 0 && (
              <p className="text-[11px] text-emerald-300 mt-1">+{res.xp} XP</p>
            )}
          </div>

          {/* avtomat tekshiruv */}
          <div className="rounded-2xl border p-3.5" style={card}>
            <p className="text-[12px] font-bold text-white mb-2">
              Format tekshiruvi
            </p>
            <div className="space-y-2">
              {res.checks.map((c: Any, i: number) => (
                <div key={i} className="flex gap-2">
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
          </div>

          {/* AI ekspert */}
          {res.ai ? (
            <div className="rounded-2xl border p-3.5" style={card}>
              <p className="text-[12px] font-bold text-white mb-1.5">
                Ekspert bahosi
              </p>
              <p className="text-[12.5px] text-slate-200 leading-relaxed whitespace-pre-line">
                {res.ai}
              </p>
            </div>
          ) : (
            <p className="text-[11px] text-slate-500 px-1">
              Ekspert bahosi hozir mavjud emas — yuqoridagi format
              tekshiruvi to'liq ishlaydi.
            </p>
          )}

          {/* namuna */}
          {res.model && (
            <div className="rounded-2xl border p-3.5" style={card}>
              <button
                onClick={() => setShowModel((x) => !x)}
                className="w-full text-left text-[12px] font-bold text-white"
              >
                {showModel ? "Namunani yashirish" : "Namuna javobni ko'rish"}
              </button>
              {showModel && (
                <>
                  <p className="text-[12.5px] text-emerald-100 leading-relaxed mt-2 whitespace-pre-line">
                    {res.model}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                    Namunani ko'chirmang — o'z matningiz bilan
                    solishtiring: qaysi abzats sizda yo'q, qaysi
                    ibora kuchliroq?
                  </p>
                </>
              )}
            </div>
          )}

          {/* o'z matni */}
          <div className="rounded-2xl border p-3.5" style={card}>
            <p className="text-[12px] font-bold text-white mb-1.5">
              Siz yozgan matn
            </p>
            <p className="text-[12.5px] text-slate-300 leading-relaxed whitespace-pre-line">
              {text}
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => reset(sub)}
              className="flex-1 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-bold text-white"
            >
              Qayta yozish
            </button>
            {t.part === "1" && sub === "1.1" && (
              <button
                onClick={() => reset("1.2")}
                className="flex-1 rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-200"
                style={card}
              >
                Task 1.2 ga
              </button>
            )}
            {(t.part === "2" || sub === "1.2") && (
              <Link
                to={`/student/cefr/writing/tasks/${t.part === "2" ? "2" : "1"}`}
                className="flex-1 rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-200 text-center"
                style={card}
              >
                Boshqa vazifa
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
