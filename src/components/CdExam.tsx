import {
  Fragment, useCallback, useEffect, useMemo, useRef, useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { Bookmark, ChevronLeft, ChevronRight, Settings, X } from "lucide-react";
import {
  Figure, QuestionInput, QuestionText, Watermark, isAnswered,
  type PaperAnswers, type PaperPart, type PaperQ, type PaperValue,
} from "./ExamPaper";
import { InstructionGroup } from "./ExamText";
import { groupText, parseInstructions, passageBlocks, placeGroups, type Group } from "../lib/examFormat";

/**
 * KOMPYUTERDAGI IELTS KO'RINISHI (2026-09-27).
 *
 * Jahongir: "readingda esa chap tomonda text, ong tomonda esa savollar
 * turishi kerak ... IELTS niki" va "listeningda map debsan qani map".
 * Namuna — IDP'ning computer-delivered IELTS tavsifi:
 *   - Reading: chapda matn, o'ngda savollar, har biri alohida aylanadi;
 *     matnni belgilash (highlight) mumkin; savollar istalgan tartibda;
 *   - Writing: chapda topshiriq, o'ngda javob maydoni, so'z soni pastda
 *     chapda;
 *   - pastda barcha savol raqamlari (javob berilgani to'ldirilgan),
 *     oldinga/orqaga strelkalar, "Keyinroq ko'rish" belgisi (raqam
 *     kvadratdan doiraga aylanadi);
 *   - taymer tepada o'rtada, oxirgi 10 va 5 daqiqada miltillaydi;
 *   - sozlamalar: shrift o'lchami, fon rangi.
 *
 * Faqat KO'RINISH. Javob kalitlari/qiymatlari, saqlash, topshirish,
 * chiqish qaydi — sahifalarning (ExamTake, MockPracticeTake) o'zida.
 * Barcha bo'limlar doim chizilgan (faol bo'lmaganlari yashirin) —
 * Listening audiosi boshqa bo'limga o'tganda to'xtab qolmasin.
 *
 * "Keyinroq ko'rish" va matn belgilashlari faqat shu brauzerda
 * (localStorage, storageKey bilan) — serverga yuborilmaydi. Xodim
 * sahifasidagi "Savolda xato bor" bayrog'i (renderQuestionAction) bu
 * emas, u o'zgarishsiz qoladi.
 */

type Span = [number, number];
type ViewSettings = { size: 0 | 1 | 2; bg: "white" | "cream" };

const ZOOM = [0.9, 1, 1.18] as const;
const SIZE_LABEL = ["A−", "A", "A+"] as const;
const SETTINGS_KEY = "cdexam:view";

function readLS<T>(key: string | null, fallback: T): T {
  if (!key) return fallback;
  try {
    const v = localStorage.getItem(key);
    return v ? (JSON.parse(v) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeLS(key: string | null, val: unknown) {
  if (!key) return;
  try {
    localStorage.setItem(key, JSON.stringify(val));
  } catch {
    /* maxfiy oyna — saqlanmaydi, test baribir ishlaydi */
  }
}

function mmss(sec: number) {
  const s = Math.max(0, Math.ceil(sec));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

/** Oraliqlarni tartiblab, ustma-ust tushganlarini birlashtiradi. */
function mergeSpans(list: Span[]): Span[] {
  const all = list
    .filter((x) => Array.isArray(x) && x[1] > x[0])
    .map((x) => [x[0], x[1]] as Span)
    .sort((a, b) => a[0] - b[0]);
  const out: Span[] = [];
  for (const [s, e] of all) {
    const last = out[out.length - 1];
    if (last && s <= last[1]) last[1] = Math.max(last[1], e);
    else out.push([s, e]);
  }
  return out;
}

/** [a, b) oralig'ini belgilashlardan olib tashlaydi. */
function subtractSpan(list: Span[], a: number, b: number): Span[] {
  const out: Span[] = [];
  for (const [s, e] of list) {
    if (e <= a || s >= b) out.push([s, e]);
    else {
      if (s < a) out.push([s, a]);
      if (e > b) out.push([b, e]);
    }
  }
  return out;
}

/** Matn ildizi boshidan (node, off) nuqtasigacha nechta belgi bor. */
function offsetOf(root: Node, node: Node, off: number): number {
  const r = document.createRange();
  r.setStart(root, 0);
  r.setEnd(node, off);
  return r.toString().length;
}

/**
 * READING MATNI — belgilash bilan. Belgilashlar belgi oraliqlari
 * sifatida React holatida turadi va matn bo'laklarga bo'linib
 * <mark> bilan chiziladi — DOM qo'lda o'zgartirilmaydi.
 */
function Passage({
  text,
  spans,
  onSpans,
  readOnly,
}: {
  text: string;
  spans: Span[];
  onSpans: (s: Span[]) => void;
  readOnly?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [sel, setSel] = useState<{ s: number; e: number; x: number; y: number } | null>(null);

  const clean = useMemo(
    () =>
      mergeSpans(spans)
        .map(([s, e]) => [Math.max(0, s), Math.min(text.length, e)] as Span)
        .filter(([s, e]) => e > s),
    [spans, text]
  );

  const measure = useCallback(() => {
    const root = ref.current;
    const ws = window.getSelection();
    if (!root || !ws || ws.rangeCount === 0 || ws.isCollapsed) {
      setSel(null);
      return;
    }
    const r = ws.getRangeAt(0);
    if (!root.contains(r.startContainer) || !root.contains(r.endContainer)) {
      setSel(null);
      return;
    }
    const s = offsetOf(root, r.startContainer, r.startOffset);
    const e = offsetOf(root, r.endContainer, r.endOffset);
    if (e <= s) {
      setSel(null);
      return;
    }
    const box = r.getBoundingClientRect();
    if (!box.width && !box.height) {
      setSel(null);
      return;
    }
    setSel({ s, e, x: box.left + box.width / 2, y: box.bottom });
  }, []);

  useEffect(() => {
    if (readOnly) return;
    document.addEventListener("selectionchange", measure);
    // Panel aylantirilganda tugma tanlov ostida qolsin
    document.addEventListener("scroll", measure, true);
    window.addEventListener("resize", measure);
    return () => {
      document.removeEventListener("selectionchange", measure);
      document.removeEventListener("scroll", measure, true);
      window.removeEventListener("resize", measure);
    };
  }, [measure, readOnly]);

  // Cambridge ko'rinishi (2026-09-27): sarlavha katta qalin, kirish
  // kursiv, paragraf harflari qalin chap chetda. Bo'laklar matnni to'liq
  // qoplaydi va bo'sh qatorlar ham DOM'da (yashirin) qoladi — belgilash
  // o'rinlari (offsetOf, Range.toString) avvalgidek butun matn bo'yicha.
  const blocks = useMemo(() => passageBlocks(text), [text]);

  /** [a, b) oralig'i — belgilangan joylari <mark> bilan. */
  const slice = (a: number, b: number, key: string): ReactNode[] => {
    const out: ReactNode[] = [];
    let pos = a;
    for (const [s, e] of clean) {
      if (e <= a || s >= b) continue;
      const s2 = Math.max(s, a);
      const e2 = Math.min(e, b);
      if (s2 > pos) out.push(<Fragment key={`${key}t${pos}`}>{text.slice(pos, s2)}</Fragment>);
      out.push(
        <mark key={`${key}m${s2}`} className="bg-yellow-200 text-inherit rounded-sm">
          {text.slice(s2, e2)}
        </mark>
      );
      pos = e2;
    }
    if (pos < b) out.push(<Fragment key={`${key}t${pos}`}>{text.slice(pos, b)}</Fragment>);
    return out;
  };

  const overlaps = sel ? clean.some(([s, e]) => s < sel.e && e > sel.s) : false;

  const finish = (next: Span[]) => {
    onSpans(next);
    setSel(null);
    try {
      window.getSelection()?.removeAllRanges();
    } catch {
      /* tanlovni tozalab bo'lmadi — muhim emas */
    }
  };

  const vw = typeof window !== "undefined" ? window.innerWidth : 1024;
  const vh = typeof window !== "undefined" ? window.innerHeight : 768;

  return (
    <>
      <div ref={ref} className="text-[15px] text-slate-800 leading-relaxed">
        {blocks.map((b, i) => {
          const k = `b${i}`;
          switch (b.k) {
            case "sep":
              return (
                <span key={k} className="hidden">
                  {slice(b.s, b.e, k)}
                </span>
              );
            case "title":
              return (
                <h3
                  key={k}
                  className="font-serif text-[1.65em] leading-tight font-bold text-center text-slate-900 mb-2 whitespace-pre-line"
                >
                  {slice(b.s, b.e, k)}
                </h3>
              );
            case "sub":
              return (
                <p
                  key={k}
                  className="italic text-center text-slate-600 max-w-[34rem] mx-auto mb-5 whitespace-pre-line"
                >
                  {slice(b.s, b.e, k)}
                </p>
              );
            case "label":
              return (
                <div key={k} className="flex gap-3 mb-3.5">
                  <span className="w-5 shrink-0 font-sans font-bold text-slate-900">
                    {slice(b.s, b.l, `${k}l`)}
                    <span className="hidden">{slice(b.l, b.b, `${k}w`)}</span>
                  </span>
                  <div className="flex-1 min-w-0 font-serif whitespace-pre-line">
                    {slice(b.b, b.e, `${k}p`)}
                  </div>
                </div>
              );
            default:
              return (
                <p key={k} className="font-serif mb-3.5 whitespace-pre-line">
                  {slice(b.s, b.e, k)}
                </p>
              );
          }
        })}
      </div>
      {/* Tugma document.body ga chiziladi — shrift o'lchami (zoom)
          uning joylashuvini surib yubormasin */}
      {sel && !readOnly ? createPortal(
        <div
          data-jony-ui=""
          role="toolbar"
          aria-label="Matnni belgilash"
          className="fixed z-[86] flex items-center gap-1 rounded-lg bg-slate-900 p-1 shadow-lg"
          style={{
            left: Math.max(8, Math.min(vw - 200, sel.x - 70)),
            top: Math.min(vh - 56, sel.y + 8),
          }}
        >
          <button
            type="button"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => finish(mergeSpans([...clean, [sel.s, sel.e]]))}
            className="rounded-md bg-yellow-300 px-2.5 py-1 text-xs font-semibold text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            Belgilash
          </button>
          {overlaps ? (
            <button
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => finish(subtractSpan(clean, sel.s, sel.e))}
              className="rounded-md px-2.5 py-1 text-xs font-semibold text-white hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              Tozalash
            </button>
          ) : null}
        </div>,
        document.body
      ) : null}
    </>
  );
}

export function CdExam({
  parts,
  answers,
  onChange,
  readOnly = false,
  title,
  subtitle,
  headerLeft,
  headerRight,
  notice,
  endsIn,
  answered,
  total,
  onSubmit,
  sending = false,
  watermark,
  storageKey,
  renderQuestionAction,
  renderPartExtra,
}: {
  parts: PaperPart[];
  answers: PaperAnswers;
  onChange: (qid: string, v: PaperValue) => void;
  readOnly?: boolean;
  title: string;
  subtitle?: string;
  headerLeft?: ReactNode;
  headerRight?: ReactNode;
  /** Sarlavha ostidagi ogohlantirishlar qatori (bo'lmasa null) */
  notice?: ReactNode;
  /** Qolgan soniya; null — taymer ko'rsatilmaydi */
  endsIn: number | null;
  answered: number;
  total: number;
  onSubmit: () => void;
  sending?: boolean;
  watermark?: string;
  /** "Keyinroq ko'rish" va belgilashlarni shu brauzerda saqlash kaliti */
  storageKey?: string;
  renderQuestionAction?: (q: PaperQ) => ReactNode;
  renderPartExtra?: (p: PaperPart, pi: number) => ReactNode;
}) {
  const reviewKey = storageKey ? `${storageKey}:review` : null;
  const hlKey = storageKey ? `${storageKey}:hl` : null;

  const [activeRaw, setActive] = useState(0);
  const active = Math.min(activeRaw, Math.max(0, parts.length - 1));
  const [cur, setCur] = useState<string | null>(null);
  // Tor ekranda (telefon): "Matn" yoki "Savollar" ko'rinadi
  const [tab, setTab] = useState<"text" | "q">("text");
  const [review, setReview] = useState<string[]>(() => readLS<string[]>(reviewKey, []));
  const [hl, setHl] = useState<Record<string, Span[]>>(() =>
    readLS<Record<string, Span[]>>(hlKey, {})
  );
  const [view, setView] = useState<ViewSettings>(() => {
    const v = readLS<Partial<ViewSettings>>(SETTINGS_KEY, {});
    return {
      size: v.size === 0 || v.size === 2 ? v.size : 1,
      bg: v.bg === "cream" ? "cream" : "white",
    };
  });
  const [showSettings, setShowSettings] = useState(false);
  const qRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const navScroll = useRef<HTMLDivElement>(null);

  // Ko'rsatma guruhlari (Cambridge): "Questions 8–13" o'z savollari OLDIDA.
  // Raqamlar savollarga to'liq mos kelmasa — hammasi bo'lim boshida, asl
  // tartibda (placeGroups). Bo'lim rasmi (ExamBank'dagi "A–G rasmlar
  // jadvali") uni tilga olgan guruhdan keyin chiqadi.
  const plans = useMemo(
    () =>
      parts.map((p) => {
        const { intro, at } = placeGroups(parseInstructions(p.instructions), p.questions);
        let imgAt: number | null = null;
        if (p.image && at.size) {
          const keys = [...at.keys()].sort((a, b) => a - b);
          const hit = keys.find((n) =>
            (at.get(n) || []).some((g: Group) =>
              /\b(map|plan|diagram|pictures?|photos?|images?|chart|graph|table|below)\b/i.test(groupText(g))
            )
          );
          imgAt = hit ?? keys[keys.length - 1];
        }
        return { intro, at, imgAt };
      }),
    [parts]
  );

  useEffect(() => writeLS(reviewKey, review), [reviewKey, review]);
  useEffect(() => writeLS(hlKey, hl), [hlKey, hl]);
  useEffect(() => writeLS(SETTINGS_KEY, view), [view]);

  useEffect(() => {
    if (!showSettings) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowSettings(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showSettings]);

  const flat = useMemo(
    () => parts.flatMap((p, pi) => p.questions.map((q) => ({ q, pi }))),
    [parts]
  );
  const reviewSet = useMemo(() => new Set(review), [review]);

  const toggleReview = (qid: string) =>
    setReview((r) => (r.includes(qid) ? r.filter((x) => x !== qid) : [...r, qid]));

  /** Savolga o'tish: bo'limini ochadi, ko'rinishga aylantiradi, fokus beradi. */
  const goTo = useCallback(
    (qid: string) => {
      const hit = flat.find((f) => f.q.id === qid);
      if (!hit) return;
      setActive(hit.pi);
      setTab("q");
      setCur(qid);
      // Bosish hodisasidagi holat yangilanishi sinxron chiziladi —
      // keyingi taktda bo'lim allaqachon ko'rinib turadi
      window.setTimeout(() => {
        const el = qRefs.current[qid];
        if (!el) return;
        const pane = el.closest<HTMLElement>("[data-pane]");
        if (pane) {
          const d = el.getBoundingClientRect().top - pane.getBoundingClientRect().top;
          pane.scrollBy({ top: d - Math.min(80, pane.clientHeight / 5), behavior: "smooth" });
        }
        // Sichqonchali qurilmada javob maydoniga fokus; telefonda
        // klaviatura o'zi ochilib ketmasin — savolning o'ziga
        const fine =
          typeof window.matchMedia === "function" &&
          window.matchMedia("(pointer: fine)").matches;
        const target = fine ? el.querySelector<HTMLElement>("[data-answer]") : null;
        (target ?? el).focus({ preventScroll: true });
      }, 0);
    },
    [flat]
  );

  const curIdx = cur ? flat.findIndex((f) => f.q.id === cur) : -1;
  const step = (dir: 1 | -1) => {
    let i: number;
    if (curIdx >= 0) i = curIdx + dir;
    else {
      // Hali savol tanlanmagan — faol bo'limning birinchisidan
      const first = flat.findIndex((f) => f.pi === active);
      i = first < 0 ? 0 : first;
    }
    if (i >= 0 && i < flat.length) goTo(flat[i].q.id);
  };

  // Pastki paneldagi joriy raqam ko'rinib tursin (faqat panel aylanadi)
  useEffect(() => {
    const sc = navScroll.current;
    const el = sc?.querySelector<HTMLElement>('[data-navcur="1"]');
    if (!sc || !el) return;
    const l = el.offsetLeft;
    const r = l + el.offsetWidth;
    if (l < sc.scrollLeft + 8) sc.scrollLeft = Math.max(0, l - 40);
    else if (r > sc.scrollLeft + sc.clientWidth - 8) sc.scrollLeft = r - sc.clientWidth + 40;
  }, [cur, active]);

  const zoom = ZOOM[view.size];
  const paneBg = view.bg === "cream" ? "bg-[#fbf6e8]" : "bg-white";
  const pane = `${paneBg} min-h-0 overflow-y-auto overscroll-contain`;

  const timerCls =
    endsIn === null
      ? ""
      : endsIn <= 300
        ? "text-red-600 bg-red-50 border-red-200 animate-pulse"
        : endsIn <= 600
          ? "text-amber-700 bg-amber-50 border-amber-200 animate-pulse"
          : "text-slate-800 bg-slate-50 border-slate-200";

  const reviewToggle = (q: PaperQ) => {
    const on = reviewSet.has(q.id);
    return (
      <button
        type="button"
        aria-pressed={on}
        aria-label={`${q.n}-savol: keyinroq ko'rish`}
        title="Keyinroq ko'rish — pastdagi raqam doiraga aylanadi"
        onClick={() => toggleReview(q.id)}
        className={`shrink-0 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
          on
            ? "border-amber-400 bg-amber-100 text-amber-800"
            : "border-slate-200 bg-white/70 text-slate-400 hover:text-slate-600 hover:border-slate-300"
        }`}
      >
        <Bookmark size={12} className={on ? "fill-current" : ""} />
        <span className="hidden sm:inline">Keyinroq ko'rish</span>
      </button>
    );
  };

  /** Savol sarlavhasi: rasm (bo'lsa), matn, "Keyinroq ko'rish", xodim bayrog'i. */
  const questionHead = (q: PaperQ) => {
    const action = renderQuestionAction ? renderQuestionAction(q) : null;
    // Xarita/plan (listening): rasm savollar guruhidan OLDIN. Writing
    // Task 1: avval topshiriq matni ("The bar chart below shows ..."),
    // keyin grafik — haqiqiy imtihon varag'idagidek (2026-09-27).
    const imageAfter = q.type === "essay";
    return (
      <>
        {q.image && !imageAfter ? <Figure src={q.image} className="mb-3" /> : null}
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <QuestionText q={q} />
          </div>
          {reviewToggle(q)}
          {action ? <div className="shrink-0 -mt-1">{action}</div> : null}
        </div>
        {q.image && imageAfter ? <Figure src={q.image} className="mt-3" /> : null}
      </>
    );
  };

  const qWrap = (q: PaperQ, body: ReactNode, register = true) => (
    <div
      key={q.id}
      ref={
        register
          ? (el) => {
              qRefs.current[q.id] = el;
            }
          : undefined
      }
      tabIndex={register ? -1 : undefined}
      data-qid={q.id}
      onFocusCapture={() => setCur(q.id)}
      className={`rounded-xl p-2 -mx-2 outline-none transition-shadow ${
        cur === q.id ? "ring-2 ring-brand-400/50" : ""
      }`}
    >
      {body}
    </div>
  );

  const answerInput = (q: PaperQ, tall = false) => (
    <QuestionInput
      q={q}
      value={answers[q.id]}
      readOnly={readOnly}
      tall={tall}
      onChange={(v) => onChange(q.id, v)}
    />
  );

  /** Shu savoldan boshlanadigan ko'rsatma guruh(lar)i (+ bo'lim rasmi). */
  const groupsAt = (pi: number, q: PaperQ) => {
    const gs = plans[pi]?.at.get(q.n) || [];
    if (!gs.length) return null;
    const p = parts[pi];
    return (
      <div className="pt-4 space-y-4">
        {gs.map((g, i) => (
          <InstructionGroup key={i} g={g} />
        ))}
        {p?.image && plans[pi]?.imgAt === q.n ? <Figure src={p.image} /> : null}
      </div>
    );
  };

  const partIntro = (p: PaperPart, pi: number, withImage = true) => (
    <div className="mb-4">
      <h2 className="font-bold uppercase tracking-wider text-slate-900">{p.title}</h2>
      {plans[pi]?.intro.length ? (
        <div className="mt-2 space-y-4">
          {plans[pi].intro.map((g, i) => (
            <InstructionGroup key={i} g={g} skipHeading={p.title} />
          ))}
        </div>
      ) : null}
      {p.audio_url && <audio controls src={p.audio_url} className="w-full mt-3" />}
      {renderPartExtra ? renderPartExtra(p, pi) : null}
      {withImage && p.image && plans[pi]?.imgAt == null ? (
        <Figure src={p.image} className="mt-3" />
      ) : null}
    </div>
  );

  const mobileTabs = (a: string, b: string) => (
    <div className="lg:hidden shrink-0 flex gap-1 border-b border-slate-200 bg-slate-100 p-1" role="tablist">
      {(["text", "q"] as const).map((t, i) => (
        <button
          key={t}
          type="button"
          role="tab"
          aria-selected={tab === t}
          onClick={() => setTab(t)}
          className={`flex-1 rounded-md py-1.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
            tab === t ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"
          }`}
        >
          {i === 0 ? a : b}
        </button>
      ))}
    </div>
  );

  const renderPart = (p: PaperPart, pi: number) => {
    const passage = (p.passage || "").trim() ? (p.passage as string) : "";
    const writing = !passage && p.questions.length > 0 && p.questions.every((q) => q.type === "essay");
    const spans = hl[String(pi)] || [];

    if (passage) {
      // READING: chapda matn, o'ngda savollar
      return (
        <div className="h-full flex flex-col lg:grid lg:grid-cols-2 lg:grid-rows-[minmax(0,1fr)] lg:divide-x lg:divide-slate-300">
          {mobileTabs("Matn", "Savollar")}
          <div
            data-pane
            className={`${tab === "text" ? "block" : "hidden"} lg:block flex-1 ${pane}`}
          >
            <div style={{ zoom }} className="px-4 sm:px-6 py-5">
              <div className="flex items-center gap-2 mb-3">
                <h2 className="flex-1 min-w-0 font-bold uppercase tracking-wider text-slate-900">
                  {p.title}
                </h2>
                {spans.length && !readOnly ? (
                  <button
                    type="button"
                    onClick={() => setHl((h) => ({ ...h, [String(pi)]: [] }))}
                    className="shrink-0 rounded-md border border-slate-200 bg-white/70 px-2 py-0.5 text-[11px] text-slate-500 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                  >
                    Belgilashlarni tozalash
                  </button>
                ) : null}
              </div>
              {!readOnly ? (
                <p className="text-[11px] text-slate-400 mb-3">
                  Matndan so'z yoki gapni tanlang — "Belgilash" tugmasi chiqadi.
                </p>
              ) : null}
              <Passage
                text={passage}
                spans={spans}
                readOnly={readOnly}
                onSpans={(s) => setHl((h) => ({ ...h, [String(pi)]: s }))}
              />
            </div>
          </div>
          <div
            data-pane
            className={`${tab === "q" ? "block" : "hidden"} lg:block flex-1 ${pane}`}
          >
            <div style={{ zoom }} className="px-4 sm:px-6 py-5">
              {partIntro(p, pi)}
              <div className="space-y-4">
                {p.questions.map((q) => (
                  <Fragment key={q.id}>
                    {groupsAt(pi, q)}
                    {qWrap(
                      q,
                      <>
                        {questionHead(q)}
                        {answerInput(q)}
                      </>
                    )}
                  </Fragment>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (writing) {
      // WRITING: chapda topshiriq, o'ngda javob maydoni
      return (
        <div className="h-full flex flex-col lg:grid lg:grid-cols-2 lg:grid-rows-[minmax(0,1fr)] lg:divide-x lg:divide-slate-300">
          {mobileTabs("Topshiriq", "Javob")}
          <div
            data-pane
            className={`${tab === "text" ? "block" : "hidden"} lg:block flex-1 ${pane}`}
          >
            <div style={{ zoom }} className="px-4 sm:px-6 py-5">
              {partIntro(p, pi)}
              <div className="space-y-4">
                {p.questions.map((q) => (
                  <Fragment key={q.id}>
                    {groupsAt(pi, q)}
                    <div>{questionHead(q)}</div>
                  </Fragment>
                ))}
              </div>
            </div>
          </div>
          <div
            data-pane
            className={`${tab === "q" ? "block" : "hidden"} lg:block flex-1 ${pane}`}
          >
            <div style={{ zoom }} className="px-4 sm:px-6 py-5 space-y-5">
              {p.questions.map((q) =>
                qWrap(
                  q,
                  <>
                    <p className="text-xs font-semibold text-slate-500 mb-1.5">
                      {q.n}. Javobingiz
                    </p>
                    {answerInput(q, p.questions.length === 1)}
                  </>
                )
              )}
            </div>
          </div>
        </div>
      );
    }

    // LISTENING va boshqalar: bitta ustun
    return (
      <div data-pane className={`h-full ${pane}`}>
        <div style={{ zoom }} className="max-w-3xl mx-auto px-4 sm:px-6 py-5">
          {partIntro(p, pi)}
          <div className="space-y-4">
            {p.questions.map((q) => (
              <Fragment key={q.id}>
                {groupsAt(pi, q)}
                {qWrap(
                  q,
                  <>
                    {questionHead(q)}
                    {answerInput(q)}
                  </>
                )}
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const partLabel = (pi: number) => (parts.length > 1 ? `Part ${pi + 1}` : "Savollar");

  // Imtihon ekrani document.body ga, z-80 da chiziladi: JonyOS ilovasi
  // ichida (/app/p/...) pastki .jos-tabs paneli (fixed, z-50) navigatorni
  // yopib qo'ymasin — navigator bo'limlar orasidagi yagona yo'l.
  // Qatlamlar: imtihon 80 < MockIssueDialog 85 < "Belgilash" 86 < rasm 88
  // < qat'iy tartib to'sig'i 100 (StrictExam.tsx).
  // data-jony-ui — body ga ilovaning o'zi chizgan qatlam, brauzer
  // kengaytmasi emas (mockning qat'iy tartibi, 2026-09-27).
  return createPortal(
    <div data-jony-ui="exam" className="fixed inset-0 z-[80] flex flex-col bg-slate-100 text-slate-900">
      {watermark ? <Watermark text={watermark} /> : null}

      {/* ---------------- tepa: nom | taymer | sozlamalar, topshirish */}
      {/* Telefonda o'ng ustun kontent kengligida (auto): tugmalar chapga
          toshib taymerni yopmasin. sm+ da taymer aniq markazda. */}
      <header className="shrink-0 grid grid-cols-[minmax(0,1fr)_auto_auto] sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2 border-b border-slate-200 bg-white px-2 sm:px-4 py-2">
        <div className="min-w-0 flex items-center gap-2">
          {headerLeft}
          <div className="min-w-0">
            <p className="text-sm font-bold text-slate-900 truncate" title={title}>
              {title}
            </p>
            {subtitle ? (
              <p className="hidden sm:block text-[11px] text-slate-500 truncate">{subtitle}</p>
            ) : null}
          </div>
        </div>
        <div className="justify-self-center">
          {endsIn !== null ? (
            <span
              role="timer"
              title="Qolgan vaqt"
              className={`inline-block rounded-lg border px-2.5 sm:px-3 py-1 text-base sm:text-xl font-bold tabular-nums ${timerCls}`}
            >
              ⏱ {mmss(endsIn)}
            </span>
          ) : null}
        </div>
        <div className="relative flex items-center justify-end gap-1.5 sm:gap-2">
          {headerRight}
          <button
            type="button"
            aria-label="Sozlamalar"
            aria-expanded={showSettings}
            title="Sozlamalar: shrift o'lchami, fon"
            onClick={() => setShowSettings((s) => !s)}
            className="rounded-lg border border-slate-200 p-1.5 text-slate-600 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            <Settings size={18} />
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={sending || readOnly}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-xl px-3 sm:px-5 py-2 text-sm font-semibold disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500"
          >
            {sending ? "Yuborilmoqda..." : "Topshirish"}
          </button>
          {showSettings ? (
            <>
              <button
                type="button"
                aria-label="Yopish"
                tabIndex={-1}
                className="fixed inset-0 z-40 cursor-default"
                onClick={() => setShowSettings(false)}
              />
              <div className="absolute right-0 top-full mt-2 z-40 w-64 rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
                <div className="flex items-center mb-2">
                  <p className="flex-1 text-sm font-semibold">Sozlamalar</p>
                  <button
                    type="button"
                    aria-label="Yopish"
                    onClick={() => setShowSettings(false)}
                    className="rounded p-0.5 text-slate-400 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                  >
                    <X size={16} />
                  </button>
                </div>
                <p className="text-[11px] font-medium text-slate-500 mb-1">Matn o'lchami</p>
                <div className="grid grid-cols-3 gap-1 mb-3">
                  {([0, 1, 2] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      aria-pressed={view.size === s}
                      onClick={() => setView((v) => ({ ...v, size: s }))}
                      className={`rounded-lg border py-1.5 font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                        ["text-xs", "text-sm", "text-base"][s]
                      } ${
                        view.size === s
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-slate-200 text-slate-600"
                      }`}
                    >
                      {SIZE_LABEL[s]}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] font-medium text-slate-500 mb-1">Fon</p>
                <div className="grid grid-cols-2 gap-1 mb-3">
                  {(
                    [
                      ["white", "Oq", "bg-white"],
                      ["cream", "Krem", "bg-[#fbf6e8]"],
                    ] as const
                  ).map(([k, label, sw]) => (
                    <button
                      key={k}
                      type="button"
                      aria-pressed={view.bg === k}
                      onClick={() => setView((v) => ({ ...v, bg: k }))}
                      className={`flex items-center justify-center gap-2 rounded-lg border py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                        view.bg === k
                          ? "border-brand-500 text-brand-700 font-semibold"
                          : "border-slate-200 text-slate-600"
                      }`}
                    >
                      <span className={`h-4 w-4 rounded border border-slate-300 ${sw}`} />
                      {label}
                    </button>
                  ))}
                </div>
                <div className="border-t border-slate-100 pt-2 space-y-1 text-[11px] text-slate-500">
                  <p className="flex items-center gap-2">
                    <span className="inline-block h-4 w-4 rounded bg-slate-800" /> javob berilgan
                  </p>
                  <p className="flex items-center gap-2">
                    <span className="inline-block h-4 w-4 rounded-full border-2 border-amber-500" />
                    keyinroq ko'rish uchun belgilangan
                  </p>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </header>

      {notice ? (
        <div className="shrink-0 border-b border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-800 flex flex-wrap items-center gap-x-4 gap-y-1">
          {notice}
        </div>
      ) : null}

      {/* ---------------- bo'limlar (hammasi chizilgan, faoli ko'rinadi) */}
      <main className="flex-1 min-h-0">
        {parts.map((p, pi) => (
          <section
            key={pi}
            aria-label={p.title || partLabel(pi)}
            className={pi === active ? "h-full" : "hidden"}
          >
            {renderPart(p, pi)}
          </section>
        ))}
      </main>

      {/* ---------------- pastki navigator */}
      <nav
        aria-label="Savollar"
        className="shrink-0 border-t border-slate-200 bg-white px-2 py-1.5 flex items-center gap-2"
      >
        <div ref={navScroll} className="relative flex-1 min-w-0 overflow-x-auto">
          <div className="flex items-center gap-3 py-1 px-0.5 w-max">
            {parts.map((p, pi) => {
              const isActive = pi === active;
              const done = p.questions.filter((q) => isAnswered(answers[q.id])).length;
              return (
                <div key={pi} className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => setActive(pi)}
                    aria-current={isActive ? "true" : undefined}
                    data-navcur={isActive && !(cur && flat[curIdx]?.pi === pi) ? "1" : undefined}
                    title={p.title}
                    className={`rounded-md px-2 py-1 text-xs font-bold whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                      isActive ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {partLabel(pi)}
                  </button>
                  {!isActive ? (
                    <span className="xl:hidden text-[11px] text-slate-400 tabular-nums whitespace-nowrap">
                      {done}/{p.questions.length}
                    </span>
                  ) : null}
                  <div className={`${isActive ? "flex" : "hidden xl:flex"} items-center gap-1`}>
                    {p.questions.map((q) => {
                      const ans = isAnswered(answers[q.id]);
                      const rev = reviewSet.has(q.id);
                      const isCur = cur === q.id;
                      return (
                        <button
                          key={q.id}
                          type="button"
                          onClick={() => goTo(q.id)}
                          data-navcur={isCur ? "1" : undefined}
                          aria-current={isCur ? "true" : undefined}
                          aria-label={`${q.n}-savol${ans ? ", javob berilgan" : ""}${
                            rev ? ", keyinroq ko'rish" : ""
                          }`}
                          className={`h-7 min-w-7 px-1 border text-xs font-semibold tabular-nums transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500 ${
                            rev ? "rounded-full border-2" : "rounded-md"
                          } ${
                            ans
                              ? `bg-slate-800 text-white ${rev ? "border-amber-400" : "border-slate-800"}`
                              : `bg-white text-slate-700 hover:border-slate-500 ${
                                  rev ? "border-amber-500" : "border-slate-300"
                                }`
                          } ${isCur ? "ring-2 ring-brand-500 ring-offset-1" : ""}`}
                        >
                          {q.n}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <span
          className="shrink-0 text-[11px] sm:text-xs text-slate-500 tabular-nums whitespace-nowrap"
          title="Javob berilgan savollar"
        >
          {answered} / {total}
        </span>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            aria-label="Oldingi savol"
            onClick={() => step(-1)}
            disabled={curIdx === 0 || flat.length === 0}
            className="rounded-lg bg-slate-800 text-white p-1.5 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            type="button"
            aria-label="Keyingi savol"
            onClick={() => step(1)}
            disabled={curIdx === flat.length - 1 || flat.length === 0}
            className="rounded-lg bg-slate-800 text-white p-1.5 disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-brand-500"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </nav>
    </div>,
    document.body
  );
}
