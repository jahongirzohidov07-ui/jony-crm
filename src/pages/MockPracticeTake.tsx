import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Flag as FlagIcon, Volume2, Square } from "lucide-react";
import { api, getActiveRole, getToken } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { MOCK_LIMITED, can } from "../lib/roles";
import {
  type PaperAnswers, type PaperPart, type PaperQ,
} from "../components/ExamPaper";
import { CdExam } from "../components/CdExam";
import { AnswerSheetTable, type AnswerRow } from "../components/ExamOnline";
import {
  MockIssueDialog, IssueStatusBadge, type IssueTarget,
} from "../components/MockIssueDialog";
import {
  MobileBlock, REASON_TEXT, StrictOverlay, useStrictEnv, useStrictGuard,
} from "../components/StrictExam";

/** Xodim urinishida ruxsat etilgan qoidabuzarlik — 3-chisida urinish
 * avtomatik topshiriladi (o'quvchi mockidagi 2 bilan bir xil). */
const PRACTICE_AWAY_LIMIT = 2;

/**
 * MOCKNI O'ZI YECHISH — bitta urinish (2026-09-27).
 *
 * Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib ishlaydigan
 * bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq ustozlarga
 * ular ham experience qilib xatolarni aytadida".
 *
 * O'quvchi ko'radigan AYNAN o'sha savollar (ExamPaper) — lekin bu yerda
 * ro'yxat, rasm, "chiqib ketdi" hisobi yo'q, natija hech qayerga
 * (guruh jadvali, coin, XP) yozilmaydi. Server vaqti bo'yicha sanoq,
 * javoblar 10 soniyada bir saqlanadi, vaqt tugasa o'zi topshiriladi.
 *
 * Listening'da audio yo'q bo'lsa "Tinglash" tugmasi skriptni serverdan
 * oladi va brauzer ovozi bilan (en-GB) BIR MARTA o'qib beradi — matn
 * ekranga chiqmaydi. Har savol yonida bayroqcha: "savolda xato bor".
 *
 * QAT'IY TARTIB (2026-09-27, Jahongir: "mock test faqat kompyuterda
 * ishlanadi ... boshqa joyga ham chiqshi mumkinmas qatiy tizim bo'lishi
 * kerak") — xodim urinishi ham doim qat'iy: telefonda ochilmaydi, to'liq
 * ekran, kengaytma / tarjima / nusxa o'chiq. Chiqishlar shu brauzerda
 * sanaladi (serverga yozilmaydi), 3-chisida urinish o'zi topshiriladi.
 * Suv belgisi yo'q (bugun olib tashlangan) — shunday qoladi.
 */

type Any = Record<string, unknown>;
type MyIssue = {
  id: number;
  qid: string | null;
  kind: string;
  status: string;
  resolution_note?: string | null;
};
type Running = {
  id: number;
  title: string;
  skill?: string | null;
  variant?: string | null;
  content_key?: string | null;
  server_now: string;
  ends_at: string | null;
  parts: PaperPart[];
  answers?: PaperAnswers | null;
  script_parts?: number[];
  /** Server ro'yxat beradi ([0, 2]); eski ko'rinish "0,2" ham o'qiladi */
  script_opened?: number[] | string | null;
  tpl_changed?: boolean;
  issues?: MyIssue[];
};
type Review = {
  id: number;
  title?: string | null;
  skill?: string | null;
  variant?: string | null;
  content_key?: string | null;
  score: number;
  max?: number;
  max_score?: number;
  band?: number | null;
  cefr?: { level?: string; correct?: number; of?: number } | null;
  script_opened?: number[] | string | null;
  detail: AnswerRow[];
  issues?: MyIssue[];
  tpl_changed?: boolean;
  submitted_at?: string | null;
  /** Ustozlarda: 60% dan kam javob yoki 50% dan kam to'g'ri — kalit butunlay yashirilgan */
  key_hidden?: boolean;
  answered?: number;
  auto_count?: number;
};

function isReview(d: Any): boolean {
  return d.status === "submitted" || Array.isArray(d.detail);
}

function store(key: string, val?: unknown) {
  try {
    if (val === undefined) {
      const v = localStorage.getItem(key);
      return v ? JSON.parse(v) : null;
    }
    if (val === null) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(val));
  } catch {
    /* maxfiy oyna — saqlanmaydi, test baribir ishlaydi */
  }
  return null;
}

function openedSet(s: number[] | string | null | undefined): number[] {
  if (Array.isArray(s)) return s.filter((x) => Number.isInteger(x));
  return String(s || "")
    .split(",")
    .map((x) => parseInt(x, 10))
    .filter((x) => !Number.isNaN(x));
}

/* BRAUZER OVOZI (StudentIeltsListening.tsx dagi usul: en-GB). Uzun
   matn bitta SpeechSynthesisUtterance bo'lsa, Chrome ~15 soniyadan
   keyin jim bo'lib qoladi — shuning uchun gaplarga bo'lib navbatga
   qo'yiladi. */
function ttsAvailable(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window
    && typeof SpeechSynthesisUtterance !== "undefined";
}

function chunks(text: string): string[] {
  const sentences = text
    .replace(/([.!?])\s+/g, "$1\n")
    .split(/\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const out: string[] = [];
  let cur = "";
  for (const s of sentences) {
    if (cur && (cur + " " + s).length > 220) {
      out.push(cur);
      cur = s;
    } else {
      cur = cur ? `${cur} ${s}` : s;
    }
  }
  if (cur) out.push(cur);
  return out;
}

function stopSpeaking() {
  try {
    window.speechSynthesis.cancel();
  } catch {
    /* TTS yo'q */
  }
}

function speakAll(text: string, onEnd: () => void) {
  try {
    const synth = window.speechSynthesis;
    synth.cancel();
    const voice = synth.getVoices().find((v) => v.lang === "en-GB")
      || synth.getVoices().find((v) => v.lang.startsWith("en"));
    const cs = chunks(text);
    if (!cs.length) {
      onEnd();
      return;
    }
    cs.forEach((c, i) => {
      const u = new SpeechSynthesisUtterance(c);
      u.lang = "en-GB";
      if (voice) u.voice = voice;
      u.rate = 0.95;
      u.volume = 1;
      if (i === cs.length - 1) {
        u.onend = onEnd;
        u.onerror = onEnd;
      }
      synth.speak(u);
    });
  } catch {
    onEnd();
  }
}

export default function MockPracticeTake() {
  const { id = "" } = useParams();
  const pid = Number(id);
  const { user } = useAuth();
  const limited = can(user?.role, MOCK_LIMITED);

  const [run, setRun] = useState<Running | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [answers, setAnswers] = useState<PaperAnswers>({});
  const [offset, setOffset] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flagFor, setFlagFor] = useState<{ t: IssueTarget; given?: string | null } | null>(null);
  // Shu urinishda yuborilgan xabarlar (savol id -> holat)
  const [sent, setSent] = useState<Record<string, string>>({});
  const [onlyWrong, setOnlyWrong] = useState(false);
  // Tinglash: qaysi bo'lim o'qilyapti / o'qib bo'lingan
  const [playing, setPlaying] = useState<number | null>(null);
  const [played, setPlayed] = useState<number[]>(() => store(`mockp:${id}:played`) || []);
  const [ttsErr, setTtsErr] = useState<string | null>(null);
  const savedRef = useRef<string>("");
  const submittingRef = useRef(false);
  const autoTriedRef = useRef(false);

  const keyA = `mockp:${id}:answers`;

  const applyIssues = useCallback((list?: MyIssue[]) => {
    if (!list?.length) return;
    const m: Record<string, string> = {};
    for (const i of list) m[i.qid ?? ""] = i.status;
    setSent((s) => ({ ...s, ...m }));
  }, []);

  const load = useCallback(() => {
    setLoadErr(null);
    api
      .fresh<Any>(`/mock-practice/${pid}`)
      .then((d) => {
        if (isReview(d)) {
          const r = d as unknown as Review;
          setReview(r);
          setRun(null);
          applyIssues(r.issues);
          store(keyA, null);
          return;
        }
        const r = d as unknown as Running;
        setOffset(Date.parse(r.server_now) - Date.now());
        setRun(r);
        applyIssues(r.issues);
        // Server saqlagani + shu qurilmada oxirgi 10 soniyada yozilgani
        const local = (store(keyA) || {}) as PaperAnswers;
        const merged = { ...r.answers, ...local };
        setAnswers(merged);
        savedRef.current = JSON.stringify(r.answers || {});
        const op = openedSet(r.script_opened);
        if (op.length) setPlayed((p) => Array.from(new Set([...p, ...op])));
      })
      .catch((e) => setLoadErr(e instanceof Error ? e.message : "Test topilmadi"));
  }, [pid, keyA, applyIssues]);

  useEffect(() => {
    if (!pid) {
      setLoadErr("Urinish topilmadi");
      return;
    }
    load();
  }, [pid, load]);

  // Sahifadan chiqilsa ovoz to'xtaydi
  useEffect(() => () => stopSpeaking(), []);

  // Soniya sanagich
  useEffect(() => {
    if (!run) return;
    const t = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(t);
  }, [run]);

  useEffect(() => {
    if (run) store(keyA, answers);
  }, [run, keyA, answers]);

  useEffect(() => {
    store(`mockp:${id}:played`, played);
  }, [id, played]);

  const endsIn = run?.ends_at ? (Date.parse(run.ends_at) - (now + offset)) / 1000 : null;

  const submit = useCallback(
    async (auto = false) => {
      if (!run || submittingRef.current) return;
      // Vaqt tugaganda o'zi faqat BIR marta urinadi — internet uzilgan
      // bo'lsa har yarim soniyada qayta yubormasin (server baribir
      // muhlatdan keyin o'zi yakunlaydi, "Topshirish" ham ishlaydi).
      if (auto) {
        if (autoTriedRef.current) return;
        autoTriedRef.current = true;
      }
      submittingRef.current = true;
      setSending(true);
      setError(null);
      stopSpeaking();
      setPlaying(null);
      try {
        const r = await api.post<Review>(`/mock-practice/${pid}/submit`, { answers });
        store(keyA, null);
        setReview(r);
        applyIssues(r.issues);
        setRun(null);
        window.scrollTo(0, 0);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Xatolik");
        submittingRef.current = false;
      } finally {
        setSending(false);
      }
    },
    [run, pid, answers, keyA, applyIssues]
  );

  // Javoblarni 10 soniyada bir serverga saqlash (ExamTake'dagidek).
  // Oddiy fetch — internet uzilsa har 10 soniyada xato xabari chiqmasin.
  useEffect(() => {
    if (!run) return;
    const t = setInterval(() => {
      const body = JSON.stringify(answers);
      if (body === savedRef.current) return;
      savedRef.current = body;
      const tok = getToken();
      const role = getActiveRole();
      fetch(`/api/mock-practice/${pid}/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(tok ? { Authorization: `Bearer ${tok}` } : {}),
          ...(role ? { "X-Active-Role": role } : {}),
        },
        body: JSON.stringify({ answers }),
      })
        .then((r) => {
          if (!r.ok) savedRef.current = "";
        })
        .catch(() => {
          savedRef.current = "";
        });
    }, 10000);
    return () => clearInterval(t);
  }, [run, pid, answers]);

  // Vaqt tugadi — belgilanganlari bilan o'zi topshiriladi
  useEffect(() => {
    if (run && endsIn !== null && endsIn <= 0) submit(true);
  }, [run, endsIn, submit]);

  // QAT'IY TARTIB — chiqishlar shu brauzerda sanaladi (serverga
  // yozilmaydi); PRACTICE_AWAY_LIMIT dan oshsa urinish o'zi topshiriladi
  const env = useStrictEnv(!run);
  const mobile = env.blocked;
  const keyV = `mockp:${id}:viol`;
  const [viol, setViol] = useState<number>(() => Number(store(keyV)) || 0);
  const violRef = useRef(viol);
  const [strictEnd, setStrictEnd] = useState<string | null>(null);
  const submitRef = useRef(submit);
  useEffect(() => {
    submitRef.current = submit;
  }, [submit]);
  const guard = useStrictGuard({
    enabled: !mobile && !review,
    active: !mobile && !!run && !review,
    storageKey: `mockp:${id}`,
    onViolation: ({ reason, extend }) => {
      // extend — o'sha chiqishning davomi (vaqti), yangi qoidabuzarlik emas
      if (extend) return;
      const n = violRef.current + 1;
      violRef.current = n;
      setViol(n);
      store(keyV, n);
      if (n > PRACTICE_AWAY_LIMIT) {
        setStrictEnd(
          `${n}-qoidabuzarlik (${REASON_TEXT[reason]}) — urinish avtomatik topshirildi.`
        );
        submitRef.current(false);
      }
    },
  });
  useEffect(() => {
    if (review) store(keyV, null);
  }, [review, keyV]);

  const qCount = useMemo(
    () => (run?.parts || []).reduce((a, p) => a + p.questions.length, 0),
    [run]
  );
  const answered = Object.values(answers).filter((v) =>
    Array.isArray(v) ? v.length > 0 : v !== "" && v !== null && v !== undefined
  ).length;

  function manualSubmit() {
    if (
      answered < qCount &&
      // confirm oynasi "oynadan chiqish" deb sanalmasin
      !guard.confirmSafe(`${qCount - answered} ta savolga javob berilmagan. Baribir topshirasizmi?`)
    )
      return;
    submit(false);
  }

  async function listen(pi: number) {
    setTtsErr(null);
    if (!ttsAvailable()) {
      setTtsErr("Bu brauzer matnni ovoz chiqarib o'qiy olmaydi — Chrome'da oching.");
      return;
    }
    if (played.includes(pi) || playing !== null) return;
    setPlaying(pi);
    try {
      const r = await api.post<{ script: string }>(`/mock-practice/${pid}/script/${pi}`);
      setPlayed((p) => Array.from(new Set([...p, pi])));
      speakAll(r.script || "", () => setPlaying((cur) => (cur === pi ? null : cur)));
    } catch (e) {
      setPlaying(null);
      setTtsErr(e instanceof Error ? e.message : "Skriptni olib bo'lmadi");
    }
  }

  function stopListening() {
    stopSpeaking();
    setPlaying(null);
  }

  const back = (
    <Link to="/mock-practice" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
      <ArrowLeft size={15} /> Mock sinab ko'rish
    </Link>
  );

  const flagBtn = (target: IssueTarget, given?: string | null) => {
    const st = sent[target.id ?? ""];
    return st ? (
      <IssueStatusBadge status={st} />
    ) : (
      <button
        type="button"
        title="Savolda xato bor — examinerga xabar berish"
        onClick={() => setFlagFor({ t: target, given })}
        className="text-slate-300 hover:text-amber-600 p-1"
      >
        <FlagIcon size={15} />
      </button>
    );
  };

  const dialog = flagFor ? (
    <MockIssueDialog
      practiceId={pid}
      target={flagFor.t}
      given={flagFor.given}
      onClose={() => setFlagFor(null)}
      onSent={(r, qid) => setSent((s) => ({ ...s, [qid ?? ""]: r.status || "open" }))}
    />
  ) : null;

  if (loadErr)
    return (
      <div className="max-w-2xl mx-auto">
        {back}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mt-3 text-center text-slate-700">
          {loadErr}
        </div>
      </div>
    );

  // ------------------------------------------------ natija
  if (review) {
    const max = review.max ?? review.max_score ?? 0;
    const skill = String(review.skill || "");
    const essay = /writing|speaking/.test(skill) || max === 0;
    const rows = onlyWrong ? review.detail.filter((d) => d.ok === false) : review.detail;
    const wrong = review.detail.filter((d) => d.ok === false).length;
    return (
      <div className="max-w-2xl mx-auto space-y-4 pb-10">
        {back}
        {strictEnd ? (
          <p className="text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            {strictEnd}
          </p>
        ) : null}
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <p className="text-xs text-slate-500">
            {review.title || review.content_key}
            {review.variant ? ` · ${review.variant}` : ""}
          </p>
          {essay ? (
            <>
              <p className="text-lg font-bold text-slate-900 mt-1">
                Writing / Speaking avtomat tekshirilmaydi
              </p>
              <p className="text-sm text-slate-600 mt-1">
                Javoblaringiz saqlandi. Ball qo'yilmaydi — savol yoki topshiriqda
                xato ko'rsangiz, pastdan xabar bering.
              </p>
            </>
          ) : review.band != null ? (
            <div className="flex items-end gap-4 mt-1">
              <div>
                <p className="text-[11px] text-slate-500 uppercase">IELTS band</p>
                <p className="text-4xl font-extrabold text-brand-700 tabular-nums">{review.band}</p>
              </div>
              <p className="text-sm text-slate-600 pb-1">
                {review.score} / {max} to'g'ri
              </p>
            </div>
          ) : review.cefr?.level ? (
            <div className="mt-1">
              <div className="flex items-end gap-4">
                <div>
                  <p className="text-[11px] text-slate-500 uppercase">Taxminiy daraja</p>
                  <p className="text-4xl font-extrabold text-brand-700">{review.cefr.level}</p>
                </div>
                <p className="text-sm text-slate-600 pb-1">
                  {review.score} / {max} to'g'ri
                </p>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                CEFR tinglash va o'qishda rasmiy ball Rasch metodi bilan chiqadi —
                bu faqat mo'ljal (taxminiy).
              </p>
            </div>
          ) : (
            <div className="flex items-end gap-4 mt-1">
              <div>
                <p className="text-[11px] text-slate-500 uppercase">Natija</p>
                <p className="text-4xl font-extrabold text-brand-700 tabular-nums">
                  {review.score} / {max}
                </p>
              </div>
              <p className="text-sm text-slate-500 pb-1">band qo'yilmaydi</p>
            </div>
          )}
          <p className="text-xs text-slate-500 mt-3 bg-slate-50 rounded-lg px-3 py-2">
            Natija hech qayerga yozilmaydi — faqat o'zingiz ko'rasiz.
            {limited
              ? " To'g'ri javob faqat siz javob berib, xato qilgan savollarda ko'rinadi" +
                " — agar savollarning kamida 60% iga javob bergan va kamida yarmini" +
                " to'g'ri topgan bo'lsangiz."
              : ""}
          </p>
          {review.key_hidden ? (
            <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2 mt-2">
              {review.auto_count
                ? `${review.auto_count} ta savoldan ${review.answered ?? 0} tasiga javob berilgan` +
                  (review.score != null ? `, ${review.score} tasi to'g'ri` : "") + " — "
                : ""}
              to'g'ri javoblar ko'rsatilmaydi.
            </p>
          ) : null}
          {review.tpl_changed ? (
            <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2 mt-2">
              Test siz yechayotgan paytda tahrirlangan — natija yangi kalit bo'yicha hisoblandi.
            </p>
          ) : null}
        </div>

        <div className="bg-white rounded-2xl border border-slate-200">
          <div className="flex items-center gap-3 px-4 pt-4 flex-wrap">
            <h2 className="font-semibold text-slate-900 flex-1">Javoblar varag'i</h2>
            {!essay && (
              <label className="text-xs text-slate-600 flex items-center gap-1.5 whitespace-nowrap">
                <input type="checkbox" checked={onlyWrong}
                       onChange={(e) => setOnlyWrong(e.target.checked)} />
                Faqat xatolar ({wrong})
              </label>
            )}
            <button
              type="button"
              onClick={() => setFlagFor({ t: { id: null } })}
              className="text-xs text-amber-700 hover:underline"
            >
              Test haqida xabar
            </button>
          </div>
          <p className="text-[11px] text-slate-400 px-4 mt-1">
            Savol yoki kalitda xato ko'rsangiz — qator yonidagi bayroqchani bosing.
          </p>
          <AnswerSheetTable
            detail={rows}
            keyHiddenText="yashirin"
            rowAction={(d) => flagBtn({ id: d.id, n: d.n, q: d.q }, d.given_text)}
          />
        </div>
        {dialog}
      </div>
    );
  }

  if (!run) return <div className="max-w-2xl mx-auto text-sm text-slate-400">Yuklanmoqda...</div>;

  // Mock faqat kompyuterda (2026-09-27) — natijani telefonda ko'rish mumkin
  if (mobile)
    return (
      <div className="max-w-2xl mx-auto">
        {back}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mt-3">
          <MobileBlock framed={env.framed && !env.mobile} />
        </div>
      </div>
    );

  // ------------------------------------------------ test
  // KOMPYUTERDAGI IELTS KO'RINISHI (2026-09-27) — o'quvchi ko'radigan
  // aynan o'sha ekran (CdExam). "Savolda xato bor" bayrog'i va
  // "Tinglash" tugmasi avvalgidek; "Keyinroq ko'rish" — alohida narsa.
  const scriptParts = new Set(run.script_parts || []);
  const left = PRACTICE_AWAY_LIMIT - viol;
  const violText =
    viol > 0
      ? left > 0
        ? `Qoidabuzarlik qayd qilindi (${viol}): yana ${left} marta ruxsat bor, keyingisida urinish avtomatik topshiriladi`
        : "Oxirgi ogohlantirish: yana bir qoidabuzarlik — urinish avtomatik topshiriladi"
      : null;
  const fsNote = guard.fsRefused;
  const notice =
    run.tpl_changed || ttsErr || error || violText || fsNote ? (
      <>
        {violText ? <span className="font-medium">{violText}</span> : null}
        {fsNote ? (
          <span>
            Brauzer to'liq ekranga ruxsat bermadi — test oddiy oynada davom etadi,
            boshqa oynaga o'tish baribir qoidabuzarlik.
          </span>
        ) : null}
        {run.tpl_changed ? (
          <span>
            Bu test siz boshlagandan keyin tahrirlandi — natija yangi kalit bo'yicha hisoblanadi.
          </span>
        ) : null}
        {ttsErr ? <span className="text-red-600">{ttsErr}</span> : null}
        {error ? <span className="text-red-600">{error}</span> : null}
      </>
    ) : null;
  return (
    <>
      <CdExam
        parts={run.parts}
        answers={answers}
        onChange={(qid, v) => setAnswers((a) => ({ ...a, [qid]: v }))}
        title={run.title}
        subtitle={`${qCount} ta savol · ${run.ends_at ? "vaqtli" : "vaqtsiz"} · natija faqat sizga ko'rinadi`}
        headerLeft={
          <Link
            to="/mock-practice"
            title="Mock sinab ko'rish"
            aria-label="Mock sinab ko'rish sahifasiga qaytish"
            className="shrink-0 rounded-lg border border-slate-200 p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-50"
          >
            <ArrowLeft size={16} />
          </Link>
        }
        headerRight={
          <button
            type="button"
            onClick={() => setFlagFor({ t: { id: null } })}
            title="Test haqida xabar"
            className="inline-flex items-center gap-1 rounded-lg px-1.5 py-1 text-xs text-amber-700 hover:bg-amber-50"
          >
            <FlagIcon size={14} />
            <span className="hidden md:inline">Test haqida xabar</span>
          </button>
        }
        notice={notice}
        endsIn={endsIn}
        answered={answered}
        total={qCount}
        onSubmit={manualSubmit}
        sending={sending}
        // Suv belgisi YO'Q (2026-09-27, Jahongir: "orqadagi yozuvchalarni
        // olib tashla") — xodim o'zi uchun sinaydi, matnni o'qishga
        // xalaqit berardi. O'quvchi imtihonida (ExamTake) u qoladi.
        storageKey={`mockp:${id}`}
        renderQuestionAction={(q: PaperQ) => flagBtn({ id: q.id, n: q.n, q: q.q })}
        renderPartExtra={(p, pi) =>
          !p.audio_url && scriptParts.has(pi) ? (
            <div className="mt-3 flex items-center gap-3 rounded-xl bg-brand-50 border border-brand-100 px-3 py-2">
              {playing === pi ? (
                <button
                  type="button"
                  onClick={stopListening}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 text-white px-3 py-1.5 text-sm font-medium"
                >
                  <Square size={14} /> To'xtatish
                </button>
              ) : (
                <button
                  type="button"
                  disabled={played.includes(pi) || playing !== null}
                  onClick={() => listen(pi)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 text-sm font-medium disabled:opacity-50"
                >
                  <Volume2 size={15} /> Tinglash
                </button>
              )}
              <span className="text-xs text-slate-600">
                {playing === pi
                  ? "O'qilmoqda… (bir marta)"
                  : played.includes(pi)
                    ? "Tinglandi — imtihondagidek bir marta"
                    : "Audio yo'q: brauzer ovozi skriptni bir marta o'qib beradi"}
              </span>
            </div>
          ) : null
        }
      />
      {/* Imtihon qatlami document.body da z-80 (JonyOS pastki paneli
          z-50 dan yuqori). Dialog ham body ga, z-85 qatlam ichida —
          imtihon ustida turadi. MockIssueDialog o'zi o'zgarmadi. */}
      {/* data-jony-ui — ilovaning o'z qatlami, kengaytma emas (2026-09-27) */}
      {dialog
        ? createPortal(
            <div data-jony-ui="" className="relative z-[85]">
              {dialog}
            </div>,
            document.body
          )
        : null}
      <StrictOverlay guard={guard} info={violText ?? undefined} />
    </>
  );
}
