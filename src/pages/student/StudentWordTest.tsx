import { StudentLoading } from "../../components/StudentLoading";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Gauge, Volume2, X } from "lucide-react";
import { TimerBar, useItemTimer } from "../../components/wordbank/ItemTimer";
import { WordbankUnavailable } from "../../components/wordbank/WordbankCards";
import { useWordbank } from "../../components/wordbank/useWordbank";
import { JSA, JsaLogo } from "../../components/Jsa";
import { ApiError, api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { useLearningLanguage } from "../../lib/lang";
import { fmtNum } from "../../lib/studentApi";
import {
  LIMIT_SEC, invalidateWordbank, pHat, roundEst, speakEn,
  type WbItemR, type WbSizeTest, type WbTestStart, type WbTestStep,
} from "../../lib/wordbankApi";

/**
 * JONY STUDENT — "LUG'AT HAJMI TESTI" (So'z bilish, 2026-10-16).
 *
 * POST /api/wordbank/size-test/start → har darajadan 10 ta so'z;
 * blok tugagach /next (javoblar bilan) → keyingi blok yoki natija;
 * "Testni tugatish" → /finish. Testda baho ko'rsatilmaydi (bu o'lchov,
 * mashq emas). Natija — TAXMINIY, oraliq bilan; tasdiqlangan so'zlar
 * soni, coin va reytingga ta'sir qilmaydi (server ham tegmaydi).
 */

type Phase = "intro" | "quiz" | "sending" | "result" | "error";
type Ans = { item_id: number; given: number | null; ms: number };

export default function StudentWordTest() {
  const lang = useLearningLanguage();
  const { state } = useWordbank(true);
  const [phase, setPhase] = useState<Phase>("intro");
  const [sid, setSid] = useState<number | null>(null);
  const [band, setBand] = useState(0);
  const [items, setItems] = useState<WbItemR[]>([]);
  const [i, setI] = useState(0);
  const [block, setBlock] = useState(1);
  const [result, setResult] = useState<WbSizeTest | null>(null);
  const [err, setErr] = useState("");
  const [confirmEnd, setConfirmEnd] = useState(false);
  const answers = useRef<Ans[]>([]);
  const busy = useRef(false);

  const item: WbItemR | undefined = items[i];
  const timer = useItemTimer(
    LIMIT_SEC.R,
    `${sid ?? 0}-${band}-${i}`,
    phase === "quiz" && !!item && !confirmEnd,
    () => record(null, LIMIT_SEC.R * 1000),
  );

  function fail(e: unknown) {
    const st = e instanceof ApiError ? e.status : 0;
    setErr(
      st === 410
        ? "Test vaqti tugadi (90 daqiqa). Qaytadan boshlang."
        : e instanceof Error && e.message
          ? e.message
          : "Xatolik — internetni tekshirib, qayta urinib ko'ring",
    );
    setPhase("error");
  }

  function showResult(r: WbSizeTest) {
    invalidateWordbank();
    setResult(r);
    setPhase("result");
  }

  async function begin() {
    if (busy.current) return;
    busy.current = true;
    setErr("");
    setPhase("sending");
    try {
      const r = await api.post<WbTestStart>("/wordbank/size-test/start");
      answers.current = [];
      setSid(r.session_id);
      setBand(r.band);
      setItems(r.items || []);
      setI(0);
      setBlock(1);
      setConfirmEnd(false);
      setPhase("quiz");
    } catch (e) {
      fail(e);
    } finally {
      busy.current = false;
    }
  }

  async function sendBlock(list: Ans[]) {
    if (busy.current || sid == null) return;
    busy.current = true;
    setPhase("sending");
    try {
      const r = await api.post<WbTestStep>("/wordbank/size-test/next", {
        session_id: sid, band, answers: list,
      });
      if (r.done) {
        showResult(r.result);
      } else {
        answers.current = [];
        setBand(r.band);
        setItems(r.items || []);
        setI(0);
        setBlock((b) => b + 1);
        setPhase("quiz");
      }
    } catch (e) {
      fail(e);
    } finally {
      busy.current = false;
    }
  }

  /** Javobni yozib qo'yadi (baho ko'rsatilmaydi) va keyingisiga o'tadi.
   * 2026-10-16 (review): "Testni tugatish" oynasi ochiq bo'lsa (taymer
   * to'xtagan) javob qabul qilinmaydi — aks holda vaqt cheksiz bo'lardi. */
  function record(given: number | null, ms: number) {
    if (!item || phase !== "quiz" || busy.current || confirmEnd) return;
    if (answers.current.some((a) => a.item_id === item.item_id)) return;
    const list = [...answers.current, { item_id: item.item_id, given, ms }];
    answers.current = list;
    if (i + 1 >= items.length) void sendBlock(list);
    else setI(i + 1);
  }

  /** Erta tugatish: shu blokdagi javoblar /finish ning o'ziga beriladi
   * (yo'qolmasin), qolganlar server qoidasi bo'yicha "Bilmayman".
   * 2026-10-16 (review): avval javoblar /next ga yuborilardi — u keyingi
   * darajaning o'quvchi ko'rmagan 10 savolini ochar, /finish esa ularni
   * "Bilmayman" (0%) deb natijaga qo'shib, taxminni buzardi. */
  async function finishNow() {
    if (busy.current || sid == null) return;
    setConfirmEnd(false);
    busy.current = true;
    setPhase("sending");
    try {
      const f = await api.post<{ done: true; result: WbSizeTest }>(
        "/wordbank/size-test/finish",
        { session_id: sid, band, answers: answers.current });
      answers.current = [];
      showResult(f.result);
    } catch (e) {
      fail(e);
    } finally {
      busy.current = false;
    }
  }

  if (lang !== "en") return <WordbankUnavailable reason="lang" />;
  if (!state) return <StudentLoading />;
  if (state.status === "off") return <WordbankUnavailable reason="off" />;
  const me = state.status === "ok" ? state.data : null;
  const last = me?.size_test ?? null;

  const top = (
    <div className="flex items-center justify-between gap-2">
      <Link to="/student/words" aria-label="Testdan chiqish"
        className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
        style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}>
        <X size={18} className="text-slate-300" />
      </Link>
      <JsaLogo small />
      <div className="w-11" />
    </div>
  );

  // -------------------------------------------------------- savol
  if (phase === "quiz" && item) {
    return (
      <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
        <div className="flex items-center gap-3">
          <Link to="/student/words" aria-label="Testdan chiqish"
            className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: JSA.card, border: `1px solid ${JSA.cardBorder}` }}>
            <X size={18} className="text-slate-300" />
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between text-[12px] font-bold text-slate-300">
              <span>{block}-blok · Common {band}000</span>
              <span className="tabular-nums">{i + 1}/{items.length}</span>
            </div>
            <div className="h-2 rounded-full bg-white/15 overflow-hidden mt-1.5">
              <div className="h-full rounded-full bg-sky-400 transition-all"
                   style={{ width: `${(i / Math.max(1, items.length)) * 100}%` }} />
            </div>
          </div>
        </div>

        <div className="student-panel bg-white rounded-3xl p-4">
          <TimerBar left={timer.left} limitMs={timer.limitMs} />
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
            {item.options.map((o, k) => (
              <button key={`${item.item_id}-${k}`} type="button"
                disabled={confirmEnd}
                onClick={() => record(k, timer.elapsedMs())}
                className="min-h-[52px] w-full rounded-2xl border-2 border-slate-200 bg-white px-4 py-2.5 text-left text-[16px] font-semibold text-slate-900 active:bg-brand-50 transition disabled:opacity-40">
                {o}
              </button>
            ))}
          </div>
          <button type="button" disabled={confirmEnd}
            onClick={() => record(null, timer.elapsedMs())}
            className="mt-2 w-full min-h-[48px] rounded-2xl border-2 border-dashed border-slate-300 text-[15px] font-bold text-slate-600 disabled:opacity-40">
            Bilmayman
          </button>
          <p className="text-[11px] text-slate-400 mt-2 leading-snug">
            Bilmasangiz taxmin qilmang — xato javob natijani pasaytiradi,
            «Bilmayman» esa yo'q.
          </p>
        </div>

        {!confirmEnd ? (
          <button type="button" onClick={() => setConfirmEnd(true)}
            className="w-full min-h-[44px] rounded-2xl border text-[14px] font-bold text-slate-300"
            style={{ background: JSA.card, borderColor: JSA.cardBorder }}>
            Testni tugatish
          </button>
        ) : (
          <div className="rounded-2xl border p-3" role="alertdialog" aria-label="Testni tugatish"
               style={{ background: JSA.card, borderColor: JSA.cardBorder }}>
            <p className="text-[13px] text-slate-200 leading-snug">
              Testni hozir tugatasizmi? Shu blokdagi javob berilmagan savollar
              «Bilmayman» deb hisoblanadi.
            </p>
            <div className="grid grid-cols-2 gap-2 mt-3">
              <button type="button" onClick={() => setConfirmEnd(false)}
                className="min-h-[44px] rounded-xl bg-white/10 text-white text-[14px] font-bold">
                Davom etish
              </button>
              <button type="button" onClick={() => void finishNow()}
                className="min-h-[44px] rounded-xl bg-rose-600 text-white text-[14px] font-bold">
                Ha, tugatish
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (phase === "sending") {
    return (
      <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
        {top}
        <div className="student-hero student-pattern rounded-3xl p-6 text-center text-white">
          <Gauge size={40} className="mx-auto" />
          <p className="text-[17px] font-bold mt-3">Hisoblanmoqda…</p>
          <p className="text-[13px] text-white/80 mt-1">Javoblaringiz yuborilmoqda</p>
        </div>
      </div>
    );
  }

  // ------------------------------------------------------ natija
  if (phase === "result" && result) {
    const tested = Object.entries(result.bands || {})
      .map(([b, v]) => ({ band: Number(b), p: pHat(v[0], v[1], v[2]) }))
      .filter((x) => Number.isFinite(x.band))
      .sort((a, b) => a.band - b.band);
    return (
      <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
        {top}
        <div className="rounded-3xl border-2 border-dashed p-5 text-center"
             style={{ borderColor: "#5b6f9c", background: "#0a1c4a" }}>
          <p className="text-[13px] font-bold text-slate-400">Taxminiy lug'at hajmi</p>
          <p className="text-[46px] font-extrabold text-slate-200 leading-none mt-2 tabular-nums">
            ≈ {fmtNum(roundEst(result.estimate))}
          </p>
          <p className="text-[14px] text-slate-400 mt-2">
            Oraliq: {fmtNum(roundEst(result.low))} – {fmtNum(roundEst(result.high))} so'z
          </p>
          <p className="text-[11.5px] text-slate-500 mt-1">
            Haqiqiy son 95% ehtimol bilan shu oraliqda
            {result.date ? ` · ${formatDate(result.date)}` : ""}
          </p>
        </div>

        <div className="student-panel bg-white rounded-3xl p-4">
          <p className="text-[15px] font-extrabold text-slate-900">
            Bu natija taxminiy
          </p>
          <p className="text-[13px] text-slate-600 mt-1 leading-relaxed">
            U tasdiqlangan so'zlar sonini, coin va reytingni o'zgartirmaydi.
            Tasdiqlangan so'zlar faqat «Bugungi mashq»da turli kunlarda to'g'ri
            topilganda oshadi.
          </p>
          {me && (
            <p className="text-[13px] text-slate-800 mt-2">
              Hozir tasdiqlangan: <b>{fmtNum(me.known)}</b> ta so'z
            </p>
          )}
        </div>

        {tested.length > 0 && (
          <div className="student-panel bg-white rounded-3xl p-4">
            <p className="text-[15px] font-extrabold text-slate-900">Test bo'yicha darajalar</p>
            <div className="mt-2 space-y-2">
              {tested.map((x) => (
                <div key={x.band} className="flex items-center gap-2">
                  <span className="text-[12.5px] text-slate-700 w-[104px] shrink-0">
                    Common {x.band}000
                  </span>
                  <div className="h-2 flex-1 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full rounded-full bg-slate-400"
                         style={{ width: `${Math.round(x.p * 100)}%` }} />
                  </div>
                  <b className="text-[12px] text-slate-600 w-10 text-right shrink-0">
                    {Math.round(x.p * 100)}%
                  </b>
                </div>
              ))}
            </div>
          </div>
        )}

        <Link to="/student/words/practice"
          className="w-full min-h-[52px] rounded-2xl bg-brand-600 text-white text-[16px] font-extrabold flex items-center justify-center">
          Bugungi mashqni boshlash
        </Link>
        <Link to="/student/words"
          className="w-full min-h-[48px] rounded-2xl border flex items-center justify-center text-white font-bold"
          style={{ background: JSA.card, borderColor: JSA.cardBorder }}>
          So'z bilishga qaytish
        </Link>
      </div>
    );
  }

  // ------------------------------------------------- kirish / xato
  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-3">
      {top}
      {phase === "error" && err && (
        <div className="student-panel bg-white rounded-2xl border border-rose-200 p-4" role="alert">
          <p className="text-[13px] text-rose-700">{err}</p>
        </div>
      )}

      <div className="student-hero student-pattern rounded-3xl p-5 text-white">
        <Gauge size={40} />
        <h1 className="text-[26px] font-extrabold leading-tight mt-2">Lug'at hajmi testi</h1>
        <p className="text-[13px] text-white/85 mt-1.5 leading-snug">
          Inglizcha nechta so'z bilishingizni taxminan aniqlaymiz. Har
          darajadan 10 ta so'z: ma'nosini tanlang yoki «Bilmayman»ni bosing.
        </p>
      </div>

      <div className="rounded-2xl border p-4" style={{ background: JSA.card, borderColor: JSA.cardBorder }}>
        <ul className="space-y-2 text-[13px] text-slate-200 leading-snug list-disc pl-4">
          <li>Har savolga {LIMIT_SEC.R} soniya; vaqt tugasa — «Bilmayman».</li>
          <li>Bilmasangiz taxmin qilmang: xato javob natijani pasaytiradi.</li>
          <li>Javoblar tekshirilib ko'rsatilmaydi — bu mashq emas, o'lchov.</li>
          <li>
            Natija <b>taxminiy</b> va tasdiqlangan so'zlar soniga ta'sir
            qilmaydi.
          </li>
        </ul>
      </div>

      {last && (
        <div className="rounded-2xl border border-dashed px-4 py-3" style={{ borderColor: "#5b6f9c" }}>
          <p className="text-[12px] font-semibold text-slate-400">Oxirgi natija (taxminiy)</p>
          <p className="text-[18px] font-bold text-slate-300 mt-0.5">
            ≈ {fmtNum(roundEst(last.estimate))}{" "}
            <span className="text-[13px] font-medium text-slate-400">
              ({fmtNum(roundEst(last.low))}–{fmtNum(roundEst(last.high))})
            </span>
          </p>
          {last.date && (
            <p className="text-[11px] text-slate-500">{formatDate(last.date)}</p>
          )}
        </div>
      )}

      <button type="button" onClick={() => void begin()}
        className="w-full min-h-[52px] rounded-2xl bg-brand-600 text-white text-[16px] font-extrabold active:scale-[0.99] transition">
        {phase === "error" ? "Qaytadan boshlash" : "Testni boshlash"}
      </button>
    </div>
  );
}
