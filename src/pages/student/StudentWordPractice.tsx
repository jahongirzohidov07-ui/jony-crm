import { StudentLoading } from "../../components/StudentLoading";
import { StudentCoinIcon } from "../../components/StudentIcon";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Volume2, X } from "lucide-react";
import { BandCelebration } from "../../components/wordbank/BandCelebration";
import { TimerBar, useItemTimer } from "../../components/wordbank/ItemTimer";
import { WordbankUnavailable } from "../../components/wordbank/WordbankCards";
import { JSA, JsaLogo } from "../../components/Jsa";
import { ApiError, api } from "../../lib/api";
import { formatDayMonth } from "../../lib/format";
import { useLearningLanguage } from "../../lib/lang";
import { useAutoNext, autoNextDelay } from "../../lib/useAutoNext";
import {
  LIMIT_SEC, SUSPECT_MS, invalidateWordbank, loadWordbank, speakEn,
  type WbAnswer, type WbAward, type WbItem, type WbSession,
} from "../../lib/wordbankApi";

/**
 * JONY STUDENT — "BUGUNGI MASHQ" (So'z bilish, 2026-10-16).
 *
 * Savollarni server beradi (POST /api/wordbank/session) — to'g'ri javob
 * mijozga kelmaydi. Har savolga javob POST /api/wordbank/answer ga
 * ketadi va baho FAQAT javobdan keyin ko'rsatiladi (oldin hech qachon).
 *
 *   R — inglizcha so'z, 4 ta o'zbekcha variant + "Bilmayman", 15 s;
 *   P — o'zbekcha ma'no, bo'sh joyli misol, matn maydoni, 30 s.
 * Daraja tugasa javob tanasida "awards" keladi — bayram ekrani chiqadi.
 *
 * 2026-10-16 (review): vaqt tugasa "timeout: true" yuboriladi — server uni
 * "o'tkazib yuborildi" deb yozadi, so'z holatiga tegmaydi va javobni
 * ochmaydi (DESIGN §2). Avval u oddiy xato edi va mashq o'zi keyingisiga
 * o'tardi: ochiq qoldirilgan ekran 20 savolni ketma-ket "xato" qilib,
 * tasdiqlangan so'zlarni unuttirardi. Endi vaqt tugagach avto-o'tish YO'Q
 * — o'quvchi "Keyingisi"ni o'zi bosadi. Javob qayta yuborilishi kutilayotganda
 * (taymer to'xtagan) boshqa javob tanlab bo'lmaydi.
 */

type Phase = "loading" | "off" | "empty" | "play" | "done" | "expired" | "error";
type Given = number | string | null;
type Pending = { given: Given; timedOut: boolean; ms: number };
type Feedback = { res: WbAnswer; given: Given; timedOut: boolean; newKnown: boolean };
type Tally = { correct: number; wrong: number; timeout: number; suspect: number; newKnown: number };

const ZERO: Tally = { correct: 0, wrong: 0, timeout: 0, suspect: 0, newKnown: 0 };

function localToday() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export default function StudentWordPractice() {
  const lang = useLearningLanguage();
  const [phase, setPhase] = useState<Phase>("loading");
  const [sess, setSess] = useState<WbSession | null>(null);
  const [idx, setIdx] = useState(0);
  const [fb, setFb] = useState<Feedback | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [retry, setRetry] = useState<Pending | null>(null);
  const [text, setText] = useState("");
  const [tally, setTally] = useState<Tally>(ZERO);
  const [awards, setAwards] = useState<WbAward[]>([]);
  const [celebrate, setCelebrate] = useState<WbAward[] | null>(null);
  const [note, setNote] = useState("");
  const busyRef = useRef(false);
  const started = useRef(false);

  const items: WbItem[] = sess?.items ?? [];
  const item: WbItem | undefined = items[idx];
  const limitSec = item?.mode === "P" ? LIMIT_SEC.P : LIMIT_SEC.R;

  const start = useCallback(async () => {
    setPhase("loading");
    setSess(null);
    setIdx(0);
    setFb(null);
    setErr("");
    setRetry(null);
    setText("");
    setTally(ZERO);
    setAwards([]);
    setCelebrate(null);
    setNote("");
    // Bo'lim yopiq bo'lsa POST 404 toast chiqarmasin — avval jim tekshiruv
    const w = await loadWordbank();
    if (w.status === "off") {
      setPhase("off");
      return;
    }
    try {
      const r = await api.post<WbSession>("/wordbank/session", { size: 20 });
      invalidateWordbank();
      if (!r.session_id || !r.items?.length) {
        setNote(r.message || "Bugun uchun savol qolmadi");
        setPhase("empty");
        return;
      }
      setSess(r);
      setPhase("play");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Mashqni boshlab bo'lmadi");
      setPhase("error");
    }
  }, []);

  useEffect(() => {
    if (lang !== "en" || started.current) return;
    started.current = true;
    void start();
  }, [lang, start]);

  const advance = useCallback(() => {
    setFb(null);
    setText("");
    setErr("");
    setRetry(null);
    if (idx + 1 >= items.length) {
      invalidateWordbank();
      setPhase("done");
    } else {
      setIdx(idx + 1);
    }
  }, [idx, items.length]);

  const auto = useAutoNext(advance);

  const timer = useItemTimer(
    limitSec,
    `${sess?.session_id ?? 0}-${idx}`,
    phase === "play" && !!item && !fb && !busy && !retry,
    () => {
      void send({ given: null, timedOut: true, ms: limitSec * 1000 });
    },
  );

  async function send(p: Pending) {
    if (!sess?.session_id || !item || fb || busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<WbAnswer>("/wordbank/answer", {
        session_id: sess.session_id,
        item_id: item.item_id,
        given: p.given,
        ms: p.ms,
        timeout: p.timedOut,
      });
      invalidateWordbank();
      setRetry(null);
      // Server tasdiqlagan vaqt tugashi (holat o'zgarmadi, baho yo'q)
      const timedOut = r.timeout === true;
      // Yangi tasdiqlangan: 2-pog'onadan 3-ga (tasdiqlangan) o'tgan javob
      const newKnown = r.correct === true && r.known && r.stage === 3;
      setTally((t) => ({
        correct: t.correct + (r.correct === true ? 1 : 0),
        wrong: t.wrong + (r.correct === false ? 1 : 0),
        timeout: t.timeout + (timedOut ? 1 : 0),
        suspect: t.suspect + (r.suspect ? 1 : 0),
        newKnown: t.newKnown + (newKnown ? 1 : 0),
      }));
      setFb({ res: r, given: p.given, timedOut, newKnown });
      const won = (r.awards || []).filter((a) => a && a.band);
      if (won.length) {
        setAwards((a) => [...a, ...won]);
        setCelebrate(won);
      } else if (!p.timedOut && !timedOut) {
        // Vaqt tugaganda avto-o'tish yo'q — o'quvchi o'zi "Keyingisi"ni bosadi
        auto.schedule(
          autoNextDelay({
            correct: r.correct === true,
            hasAnswer: r.correct === false && !!r.expected,
            hasExtra: item.mode === "P",
          }),
        );
      }
    } catch (e) {
      const st = e instanceof ApiError ? e.status : 0;
      if (st === 410) {
        setPhase("expired");
      } else if (st === 409) {
        // Allaqachon javob berilgan (ikki bosish / boshqa qurilma)
        advance();
      } else {
        setRetry(p);
        setErr(
          e instanceof Error && e.message
            ? e.message
            : "Javob yuborilmadi — internetni tekshirib, qayta yuboring",
        );
      }
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  function pick(given: Given) {
    // Qayta yuborish kutilmoqda (taymer to'xtagan) — yangi javob yo'q
    if (retry) return;
    send({ given, timedOut: false, ms: timer.elapsedMs() });
  }

  if (lang !== "en") return <WordbankUnavailable reason="lang" />;
  if (phase === "off") return <WordbankUnavailable reason="off" />;
  if (phase === "loading") return <StudentLoading />;

  const closeBtn = (
    <Link to="/student/words" aria-label="Mashqdan chiqish"
      className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
      style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}>
      <X size={18} className="text-slate-300" />
    </Link>
  );

  // ------------------------------------------------ yakuniy holatlar
  if (phase !== "play" || !item) {
    const answered = tally.correct + tally.wrong + tally.timeout + tally.suspect;
    const coins = awards.reduce((s, a) => s + (a.coins || 0), 0);
    return (
      <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
        <div className="flex items-center justify-between gap-2">
          {closeBtn}
          <JsaLogo small />
          <div className="w-11" />
        </div>

        {phase === "done" && (
          <>
            <div className="student-pattern rounded-3xl p-5 text-white"
                 style={{ background: "linear-gradient(120deg,#10b981,#059669 55%,#0e7490)" }}>
              <p className="text-[26px] font-extrabold leading-tight">Mashq tugadi!</p>
              <p className="text-[13px] text-white/85 mt-1">
                {answered} ta savolga javob berdingiz
              </p>
              {tally.newKnown > 0 && (
                <p className="mt-3 inline-flex rounded-full bg-white/20 px-3 py-1.5 text-[14px] font-extrabold">
                  +{tally.newKnown} ta yangi tasdiqlangan so'z
                </p>
              )}
            </div>
            <div className="grid grid-cols-3 gap-2">
              <Stat value={tally.correct} label="to'g'ri" tone="text-emerald-600" />
              <Stat value={tally.wrong} label="xato / bilmadim" tone="text-rose-600" />
              <Stat value={tally.timeout} label="vaqt tugadi" tone="text-amber-600" />
            </div>
            {awards.length > 0 && (
              <div className="student-panel bg-white rounded-3xl p-4">
                <p className="text-[16px] font-extrabold text-slate-900">Tugatilgan darajalar</p>
                {awards.map((a) => (
                  <p key={a.band} className="flex items-center gap-2 mt-2 text-[14px] text-slate-800">
                    <span className="w-7 h-7 rounded-full bg-amber-400 text-white flex items-center justify-center shrink-0">
                      <Check size={15} strokeWidth={4} />
                    </span>
                    <b className="flex-1">Common {a.band}000</b>
                    {a.coins > 0 && (
                      <span className="inline-flex items-center gap-1 font-extrabold text-amber-600">
                        <StudentCoinIcon size={18} /> +{a.coins} coin
                      </span>
                    )}
                  </p>
                ))}
                {coins > 0 && (
                  <p className="text-[12px] text-slate-500 mt-2">Coin hisobingizga qo'shildi.</p>
                )}
              </div>
            )}
            <p className="text-[12px] text-slate-400 px-1 leading-relaxed">
              So'z turli kunlarda to'g'ri topilgandagina tasdiqlanadi — ertaga
              yana kiring, takrorlash vaqti kelgan so'zlar shu yerda chiqadi.
            </p>
          </>
        )}

        {phase === "empty" && (
          <div className="student-panel bg-white rounded-3xl p-6 text-center">
            <p className="text-[44px] leading-none" aria-hidden="true">🎉</p>
            <p className="text-[19px] font-extrabold text-slate-900 mt-3">Barakalla!</p>
            <p className="text-[13px] text-slate-600 mt-2 leading-relaxed">
              {note}. Ertaga takrorlash vaqti kelgan so'zlar shu yerda chiqadi.
            </p>
          </div>
        )}

        {phase === "expired" && (
          <div className="student-panel bg-white rounded-3xl p-6 text-center">
            <p className="text-[19px] font-extrabold text-slate-900">Mashq vaqti tugadi</p>
            <p className="text-[13px] text-slate-600 mt-2 leading-relaxed">
              Bitta mashq 45 daqiqa ochiq turadi. Yangi mashqni boshlang —
              javob bergan so'zlaringiz saqlangan.
            </p>
          </div>
        )}

        {phase === "error" && (
          <div className="student-panel bg-white rounded-3xl p-6 text-center">
            <p className="text-[19px] font-extrabold text-slate-900">Mashq ochilmadi</p>
            <p className="text-[13px] text-slate-600 mt-2">{err}</p>
          </div>
        )}

        {phase !== "empty" && (
          <button onClick={() => void start()}
            className="w-full min-h-[52px] rounded-2xl bg-brand-600 text-white text-[16px] font-extrabold active:scale-[0.99] transition">
            {phase === "done" ? "Yana mashq qilish" : "Yangi mashqni boshlash"}
          </button>
        )}
        <Link to="/student/words"
          className="w-full min-h-[48px] rounded-2xl border flex items-center justify-center text-white font-bold"
          style={{ background: JSA.card, borderColor: JSA.cardBorder }}>
          So'z bilishga qaytish
        </Link>
      </div>
    );
  }

  // ---------------------------------------------------- savol ekrani
  const res = fb?.res ?? null;
  const elapsed = timer.limitMs - timer.left;
  const isR = item.mode === "R";
  const today = localToday();
  // Javob berilgan, yuborilmoqda yoki qayta yuborish kutilmoqda (taymer
  // to'xtagan) — javob tugmalari yopiq (2026-10-16, review).
  const locked = !!fb || busy || !!retry;

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
      <div className="flex items-center gap-3">
        {closeBtn}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between text-[12px] font-bold text-slate-300">
            <span>Bugungi mashq</span>
            <span className="tabular-nums">{idx + 1}/{items.length}</span>
          </div>
          <div className="h-2 rounded-full bg-white/15 overflow-hidden mt-1.5">
            <div className="h-full rounded-full bg-emerald-400 transition-all"
                 style={{ width: `${((idx + (fb ? 1 : 0)) / items.length) * 100}%` }} />
          </div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-xl px-2.5 py-2 border text-emerald-300 text-[13px] font-extrabold shrink-0"
              style={{ background: JSA.card, borderColor: JSA.cardBorder }}
              aria-label={`${tally.correct} ta to'g'ri`}>
          <Check size={14} strokeWidth={3} /> {tally.correct}
        </span>
      </div>

      <div className="student-panel bg-white rounded-3xl p-4">
        {!fb ? (
          <TimerBar left={timer.left} limitMs={timer.limitMs} />
        ) : (
          <div className="h-[18px]" aria-hidden="true" />
        )}

        {isR ? (
          <>
            <p className="text-[12px] font-bold text-slate-500 mt-3">
              Bu so'z nimani anglatadi?
            </p>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-[32px] font-extrabold text-slate-900 leading-tight break-words flex-1 min-w-0">
                {item.word}
              </p>
              <button type="button" onClick={() => speakEn(item.word)} aria-label="Tinglash"
                className="w-11 h-11 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                <Volume2 size={20} />
              </button>
            </div>
            <div className="grid gap-2 mt-3">
              {item.options.map((o, k) => {
                const isRight = !!res && res.expected === o;
                const isMine = !!fb && fb.given === k;
                const cls = !fb
                  ? "bg-white border-slate-200 text-slate-900 active:bg-brand-50"
                  : isRight
                    ? "bg-emerald-50 border-emerald-500 text-emerald-800"
                    : isMine
                      ? "bg-rose-50 border-rose-400 text-rose-800"
                      : "bg-white border-slate-200 text-slate-400";
                return (
                  <button key={k} type="button" disabled={locked}
                    onClick={() => pick(k)}
                    className={`min-h-[52px] w-full rounded-2xl border-2 px-4 py-2.5 text-left text-[16px] font-semibold transition ${cls}`}>
                    {o}
                  </button>
                );
              })}
            </div>
            <button type="button" disabled={locked} onClick={() => pick(null)}
              className="mt-2 w-full min-h-[44px] rounded-2xl text-[14px] font-bold text-slate-500 disabled:opacity-40">
              Bilmayman
            </button>
          </>
        ) : (
          <>
            <p className="text-[12px] font-bold text-slate-500 mt-3">
              Inglizchasini yozing
            </p>
            <p className="text-[26px] font-extrabold text-slate-900 leading-tight mt-1 break-words">
              {item.uz}
            </p>
            {item.example && (
              <p className="text-[15px] text-slate-800 mt-3 leading-relaxed rounded-xl bg-slate-50 px-3 py-2">
                {item.example}
                {item.example_uz && (
                  <span className="block text-[12px] text-slate-500 mt-1">{item.example_uz}</span>
                )}
              </p>
            )}
            <form className="mt-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (text.trim() && !locked) pick(text);
              }}>
              <label className="block text-[12px] text-slate-500 mb-1" htmlFor="wb-answer">
                Birinchi harfi: <b className="text-slate-800">{item.hint}</b>
              </label>
              <input
                id="wb-answer"
                key={item.item_id}
                autoFocus
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={locked}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck={false}
                placeholder={`${item.hint}…`}
                className={`w-full min-h-[52px] rounded-2xl border-2 px-4 text-[18px] font-semibold text-slate-900 outline-none ${
                  !fb
                    ? "border-slate-200 focus:border-brand-500"
                    : res?.correct
                      ? "border-emerald-500 bg-emerald-50"
                      : res?.correct === false
                        ? "border-rose-400 bg-rose-50"
                        : "border-amber-400 bg-amber-50"
                }`}
              />
              {!fb && (
                <button type="submit" disabled={!text.trim() || locked}
                  className="mt-2 w-full min-h-[52px] rounded-2xl bg-brand-600 text-white text-[16px] font-extrabold disabled:opacity-40">
                  Tekshirish
                </button>
              )}
            </form>
            {!fb && (
              <button type="button" disabled={locked || elapsed < SUSPECT_MS + 300}
                onClick={() => pick(null)}
                className="mt-1 w-full min-h-[44px] rounded-2xl text-[14px] font-bold text-slate-500 disabled:opacity-40">
                Bilmayman
              </button>
            )}
          </>
        )}

        {/* ------------------------- javobdan KEYIN baho (oldin emas) */}
        {fb && res && (
          <div role="status" aria-live="polite"
            className={`mt-3 rounded-2xl p-3 ${
              res.suspect || res.timeout ? "bg-amber-50 border border-amber-200"
                : res.correct ? "bg-emerald-50 border border-emerald-200"
                  : "bg-rose-50 border border-rose-200"}`}>
            {res.suspect ? (
              <p className="text-[14px] font-bold text-amber-800">
                {res.message || "Juda tez yozildi — javob hisobga olinmadi."}
              </p>
            ) : res.timeout ? (
              <>
                <p className="text-[17px] font-extrabold text-amber-700">Vaqt tugadi</p>
                <p className="text-[13px] text-amber-800 mt-0.5">
                  {res.message || "So'z holati o'zgarmadi — u keyinroq yana beriladi."}
                </p>
              </>
            ) : res.correct ? (
              <>
                <p className="text-[17px] font-extrabold text-emerald-700">✓ To'g'ri!</p>
                {fb.newKnown && (
                  <p className="text-[13px] font-bold text-emerald-800 mt-0.5">
                    So'z tasdiqlandi — tasdiqlangan so'zlaringizga qo'shildi
                  </p>
                )}
              </>
            ) : (
              <>
                <p className="text-[17px] font-extrabold text-rose-700">
                  {fb.timedOut ? "Vaqt tugadi" : fb.given === null ? "Bilmayman" : "Xato"}
                </p>
                {!isR && typeof fb.given === "string" && fb.given.trim() && (
                  <p className="text-[13px] text-rose-800 mt-0.5">
                    Siz yozdingiz: <s>{fb.given.trim()}</s>
                  </p>
                )}
                {res.expected && (
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-[15px] text-slate-800 flex-1 min-w-0 break-words">
                      To'g'ri javob:{" "}
                      <b>{isR ? `${item.word} — ${res.expected}` : res.expected}</b>
                    </p>
                    <button type="button" aria-label="Tinglash"
                      onClick={() => speakEn(isR ? item.word : res.expected || "")}
                      className="w-10 h-10 rounded-xl bg-white text-brand-600 flex items-center justify-center shrink-0">
                      <Volume2 size={18} />
                    </button>
                  </div>
                )}
              </>
            )}
            {!res.suspect && !res.timeout && res.due && (
              <p className="text-[11.5px] text-slate-500 mt-1.5">
                {res.due <= today
                  ? "Bu so'z yana takrorlanadi"
                  : `Keyingi takrorlash: ${formatDayMonth(res.due)}`}
              </p>
            )}
          </div>
        )}

        {err && (
          <div className="mt-3 rounded-2xl bg-rose-50 border border-rose-200 p-3" role="alert">
            <p className="text-[13px] text-rose-700">{err}</p>
            {retry && (
              <button type="button" disabled={busy} onClick={() => void send(retry)}
                className="mt-2 w-full min-h-[44px] rounded-xl bg-rose-600 text-white text-[14px] font-bold">
                Qayta yuborish
              </button>
            )}
          </div>
        )}
      </div>

      {fb && !celebrate && (
        <button type="button" onClick={() => { auto.cancel(); advance(); }}
          className="w-full min-h-[52px] rounded-2xl bg-brand-600 text-white text-[16px] font-extrabold active:scale-[0.99] transition">
          {idx + 1 >= items.length ? "Natijani ko'rish" : "Keyingisi"}
          {auto.secsLeft > 0 ? ` (${auto.secsLeft})` : ""}
        </button>
      )}

      {celebrate && (
        <BandCelebration
          awards={celebrate}
          onClose={() => {
            setCelebrate(null);
            auto.schedule(1500);
          }}
        />
      )}
    </div>
  );
}

function Stat({ value, label, tone }: { value: number; label: string; tone: string }) {
  return (
    <div className="student-panel bg-white rounded-2xl px-2 py-3 text-center">
      <p className={`text-[26px] font-extrabold leading-none ${tone}`}>{value}</p>
      <p className="text-[11px] text-slate-500 mt-1.5 leading-tight">{label}</p>
    </div>
  );
}
