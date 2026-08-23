import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
import { GraduationCap, X, ArrowRight, Check, MousePointerClick } from "lucide-react";
import { api, getGlobalBranch, setGlobalBranch } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { lessonById, lessonsForRole, type GuideLesson } from "../../lib/guide/lessons";
import { FOUNDER } from "../../lib/roles";

/**
 * INTERAKTIV O'RGATUVCHI (2026-08-23).
 *
 * Jahongir: "shu yerni bosasan deb strelkalar turib hammasini
 * korsatib turishi kerak".
 *
 * ISHLASH TARTIBI. Dars boshlanadi -> tizim kerakli sahifaga o'zi
 * o'tadi -> ekrandagi mo'ljal (data-guide) topiladi -> atrofi
 * yoritiladi, qolgan joy qorayadi -> strelka va matn chiqadi ->
 * xodim O'ZI bosadi -> keyingi qadam.
 *
 * MASHQ TEST FILIALIDA. Dars boshlanganda global filial test
 * filialiga o'tkaziladi, tugagach avvalgisi qaytariladi. Shuning
 * uchun xodim tugmani haqiqatdan bossa ham, haqiqiy o'quvchi va
 * haqiqiy pulga tegmaydi.
 *
 * MO'LJAL TOPILMASA. Sahifa hali yuklanayotgan bo'lishi mumkin —
 * 6 soniya davomida kutamiz. Baribir topilmasa: qadam "ixtiyoriy"
 * bo'lsa o'tkazib yuboriladi, aks holda xodimga tushunarli xabar
 * chiqadi (dars yarim yo'lda "o'lib" qolmaydi).
 */

interface GuideCtx {
  start: (lessonId: string) => void;
  done: string[];
  lessons: GuideLesson[];
  running: string | null;
  refresh: () => void;
  /** Asoschi boshqa lavozim ko'zi bilan qarayotgan bo'lsa — o'sha rol */
  asRole: string | null;
  setAsRole: (r: string | null) => void;
  canPreviewRoles: boolean;
}

const Ctx = createContext<GuideCtx>({
  start: () => {},
  done: [],
  lessons: [],
  running: null,
  refresh: () => {},
  asRole: null,
  setAsRole: () => {},
  canPreviewRoles: false,
});

export const useGuide = () => useContext(Ctx);

interface State {
  role?: string;
  done: string[];
  intro_seen: boolean;
  test_branch_id: number | null;
}

const FIND_TIMEOUT_MS = 6000;

function findTarget(name?: string): HTMLElement | null {
  if (!name) return null;
  return document.querySelector<HTMLElement>(`[data-guide="${name}"]`);
}

export function GuideProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [state, setState] = useState<State | null>(null);
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [stepIx, setStepIx] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const [lost, setLost] = useState(false);
  const [askIntro, setAskIntro] = useState(false);
  // ASOSCHI UCHUN (2026-08-23, Jahongir: "6ta funksiya adminlar uchun
  // edi nega asoschida chiqyabdi"). Endi asoschiga admin darslari
  // ko'rinmaydi, lekin tekshirmoqchi bo'lsa shu yerdan tanlaydi.
  const [asRole, setAsRole] = useState<string | null>(null);
  const prevBranch = useRef<string | null>(null);

  const lesson = lessonId ? lessonById(lessonId) : undefined;
  const step = lesson?.steps[stepIx];

  const refresh = useCallback(() => {
    api.fresh<State>("/guide/state").then(setState).catch(() => setState(null));
  }, []);

  useEffect(() => {
    if (!user) return;
    refresh();
  }, [user, refresh]);

  // Yangi xodim — bir marta taklif qilamiz
  useEffect(() => {
    if (!state || state.intro_seen || lessonId) return;
    const t = setTimeout(() => setAskIntro(true), 1200);
    return () => clearTimeout(t);
  }, [state, lessonId]);

  // ---- dars boshlash / tugatish
  const start = useCallback((id: string) => {
    const l = lessonById(id);
    if (!l) return;
    setAskIntro(false);
    // Mashq test filialida ketsin
    const tb = state?.test_branch_id;
    if (tb) {
      prevBranch.current = getGlobalBranch();
      setGlobalBranch(String(tb));
    }
    setLessonId(id);
    setStepIx(0);
    setLost(false);
    if (l.steps[0]?.path) navigate(l.steps[0].path!);
  }, [navigate, state]);

  const finish = useCallback((completed: boolean) => {
    const id = lessonId;
    setLessonId(null);
    setStepIx(0);
    setRect(null);
    setLost(false);
    // Filialni joyiga qaytaramiz
    if (prevBranch.current !== null) {
      setGlobalBranch(prevBranch.current);
      prevBranch.current = null;
    }
    if (id && completed) {
      api.post("/guide/done", { lesson_id: id })
        .then(refresh).catch(() => {});
    }
  }, [lessonId, refresh]);

  const next = useCallback(() => {
    if (!lesson) return;
    const ni = stepIx + 1;
    if (ni >= lesson.steps.length) {
      finish(true);
      return;
    }
    const ns = lesson.steps[ni];
    setLost(false);
    setRect(null);
    setStepIx(ni);
    if (ns.path) navigate(ns.path);
  }, [lesson, stepIx, finish, navigate]);

  // ---- mo'ljalni topish va kuzatish
  useEffect(() => {
    if (!lesson || !step) return;
    let stop = false;
    const began = Date.now();

    const tick = () => {
      if (stop) return;
      const el = findTarget(step.target);
      if (el) {
        const r = el.getBoundingClientRect();
        if (r.width || r.height) {
          setRect(r);
          setLost(false);
          if (r.top < 80 || r.bottom > window.innerHeight - 80) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        }
      } else if (Date.now() - began > FIND_TIMEOUT_MS) {
        if (step.optional) {
          next();
          return;
        }
        setLost(true);
      }
      raf = requestAnimationFrame(tick);
    };
    let raf = requestAnimationFrame(tick);
    return () => { stop = true; cancelAnimationFrame(raf); };
  }, [lesson, step, stepIx, next]);

  // ---- "click" qadam: xodim o'zi bosishini kutamiz
  useEffect(() => {
    if (!step || step.kind !== "click") return;
    const el = findTarget(step.target);
    if (!el) return;
    const onClick = () => setTimeout(next, 350);
    el.addEventListener("click", onClick, { once: true });
    return () => el.removeEventListener("click", onClick);
  }, [step, stepIx, rect, next]);

  const canPreviewRoles = user?.role === FOUNDER;
  const lessons = useMemo(
    () => lessonsForRole(canPreviewRoles && asRole ? asRole : user?.role),
    [user?.role, asRole, canPreviewRoles]
  );

  const value: GuideCtx = {
    start,
    done: state?.done ?? [],
    lessons,
    running: lessonId,
    refresh,
    asRole,
    setAsRole,
    canPreviewRoles,
  };

  return (
    <Ctx.Provider value={value}>
      {children}

      {/* --- Yangi xodimga taklif --- */}
      {askIntro && !lessonId && !canPreviewRoles && lessons.length > 0 && (
        <div className="fixed inset-0 z-[95] flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-brand-50 text-brand-600">
              <GraduationCap size={20} />
            </div>
            <h3 className="text-lg font-semibold text-slate-900">
              Ishni birga boshlaymizmi?
            </h3>
            <p className="mt-2 text-sm text-slate-600">
              Tizim sizga har bir ishni <b>ko'rsatib</b> beradi: qaysi
              tugmani bosishni strelka bilan belgilaydi, nima uchun
              kerakligini yozib turadi. Mashq <b>test filialida</b>{" "}
              ketadi — haqiqiy o'quvchi va haqiqiy pulga tegmaydi,
              xato qilishdan qo'rqmang.
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Sizning lavozimingiz uchun {lessons.length} ta dars bor.
              Istagan paytda to'xtatib, keyin davom ettirsangiz bo'ladi.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <button
                onClick={() => start(lessons[0].id)}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                Boshlaymiz
              </button>
              <button
                onClick={() => {
                  setAskIntro(false);
                  api.post("/guide/done", {
                    lesson_id: "__intro__", skipped: true,
                  }).then(refresh).catch(() => {});
                }}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600"
              >
                Keyinroq
              </button>
            </div>
            <p className="mt-3 text-xs text-slate-400">
              Keyin ham ochish mumkin: Profil → Mening funksiyalarim.
            </p>
          </div>
        </div>
      )}

      {/* --- Dars ketayotgan payt --- */}
      {lesson && step && (
        <>
          {/* Qorayish — mo'ljal atrofi ochiq qoladi */}
          <div className="pointer-events-none fixed inset-0 z-[90]">
            {rect && !lost ? (
              <div
                className="absolute rounded-xl ring-4 ring-brand-500 transition-all duration-200"
                style={{
                  left: rect.left - 6,
                  top: rect.top - 6,
                  width: rect.width + 12,
                  height: rect.height + 12,
                  boxShadow: "0 0 0 9999px rgba(15,23,42,.55)",
                }}
              />
            ) : (
              <div className="absolute inset-0 bg-slate-900/55" />
            )}
          </div>

          {/* Strelka */}
          {rect && !lost && (
            <div
              className="pointer-events-none fixed z-[92] animate-bounce text-brand-600"
              style={{
                left: Math.min(rect.left + rect.width / 2 - 12,
                  window.innerWidth - 40),
                top: rect.bottom + 8 > window.innerHeight - 120
                  ? rect.top - 40
                  : rect.bottom + 8,
              }}
            >
              <MousePointerClick size={26} strokeWidth={2.5} />
            </div>
          )}

          {/* Matn oynasi */}
          <div className="fixed bottom-4 left-1/2 z-[93] w-[min(92vw,30rem)] -translate-x-1/2 rounded-2xl bg-white p-4 shadow-2xl ring-1 ring-slate-200">
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700">
                {lesson.title} · {stepIx + 1}/{lesson.steps.length}
              </span>
              <button
                onClick={() => finish(false)}
                className="text-slate-400 hover:text-slate-600"
                title="To'xtatish"
              >
                <X size={16} />
              </button>
            </div>

            <h4 className="text-sm font-semibold text-slate-900">
              {step.title}
            </h4>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {step.text}
            </p>

            {lost && (
              <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
                Bu joy hozir ekranda ko'rinmayapti — sahifa boshqacha
                bo'lishi mumkin. «O'tkazib yuborish» bilan davom eting.
              </p>
            )}

            <div className="mt-3 flex items-center gap-2">
              {step.kind === "click" && !lost ? (
                <span className="text-xs text-slate-500">
                  Yoritilgan joyni bosing →
                </span>
              ) : (
                <button
                  onClick={next}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Tushundim <ArrowRight size={14} />
                </button>
              )}
              <div className="flex-1" />
              {step.kind === "click" && (
                <button
                  onClick={next}
                  className="text-xs text-slate-400 hover:text-slate-600"
                >
                  O'tkazib yuborish
                </button>
              )}
            </div>

            {state?.test_branch_id && (
              <p className="mt-2.5 flex items-center gap-1 text-[11px] text-emerald-700">
                <Check size={12} /> Mashq rejimi — test filialida,
                haqiqiy ma'lumotga tegmaydi
              </p>
            )}
          </div>
        </>
      )}
    </Ctx.Provider>
  );
}
