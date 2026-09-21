import { useEffect, useState } from "react";
import { formatDayMonth } from "../../lib/format";
import { Link } from "react-router-dom";
import {
  AlertTriangle, CheckCircle2, ChevronRight, Clock, Timer, Users,
  BookOpen, Play, Send, ClipboardCheck, X, LifeBuoy, Undo2,
} from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { BrandIcon } from "../../components/BrandIcon";
import type { LessonCard, TeacherHome } from "../../lib/teacherApi";

/** Reja qatlami (2026-09-18): bugungi dars uchun mavzu, ko'chgan qismlar,
 *  uy vazifasini bajarmaganlar, yordam kerak o'quvchilar, "Darsni boshlash". */
type PlanItem = {
  lesson_id: number; group_id: number; group: string;
  plan: { course: string; course_title: string; next_lesson_no: number; total: number;
    next_title: string | null; next_grammar: string | null; next_vocab: string | null; carry: string[] } | null;
  run: { id: number; status: string; done: number; total: number } | null;
  homework_missing: string[]; help_needed: { name: string; why: string }[]; pending_checks: number;
};
type PlanToday = { items: PlanItem[]; english: boolean; courses: { course: string; title: string; total: number }[] };

/**
 * JONY TEACHER — bosh ekran: "bugun nima qilishim kerak".
 *
 * Ustoz ilovani ochganda ko'radigan BIRINCHI narsa — bugungi darslari
 * va qaysinisiga hali yo'qlama qo'yilmagani. Boshqa hamma narsa
 * pastda yoki "Bo'limlar" tabida.
 */
export default function TeacherToday() {
  const { user } = useAuth();
  const isSupport = user?.role === "support_teacher";
  const [d, setD] = useState<TeacherHome | null>(null);
  const [missed, setMissed] = useState<LessonCard[]>([]);
  const [plan, setPlan] = useState<PlanToday | null>(null);
  const [err, setErr] = useState("");
  const loadPlan = () => api.fresh<PlanToday>("/teacher/plan-today").then(setPlan).catch(() => {});

  useEffect(() => {
    api
      .get<TeacherHome>("/teacher/home")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
    api
      .get<{ missed: LessonCard[] }>("/teacher/today")
      .then((r) => setMissed(r.missed || []))
      .catch(() => {});
    loadPlan();
  }, []);

  if (err)
    return <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>;

  const today = new Date(d.date);
  const dayName = [
    "Yakshanba", "Dushanba", "Seshanba", "Chorshanba",
    "Payshanba", "Juma", "Shanba",
  ][today.getDay()];

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-14">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2 mb-4 opacity-90">
            <BrandIcon size={18} className="rounded-md" />
            <span className="text-sm font-medium">Jony Teacher</span>
          </div>
          <h1 className="text-xl font-semibold">{d.teacher}</h1>
          <p className="text-sm opacity-90 mt-0.5">
            {dayName} · {formatDayMonth(d.date)}
            {d.grade ? ` · ${d.grade}` : ""}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-9 space-y-4">
        {!isSupport && plan?.english !== false && <GuideCard />}
        <div className="grid grid-cols-3 gap-3">
          <Stat value={String(d.groups)} label="Guruh" />
          <Stat value={String(d.students)} label="O'quvchi" />
          <Stat value={String(d.lessons_this_month)} label="Bu oy dars" />
        </div>

        {!isSupport && missed.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-start gap-2.5 mb-2">
              <AlertTriangle size={17} className="text-amber-600 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-amber-900">
                  Yo'qlama qo'yilmagan darslar
                </p>
                <p className="text-xs text-amber-700">
                  Oyligingiz shu yo'qlamadan hisoblanadi
                </p>
              </div>
            </div>
            <div className="space-y-1.5 mt-3">
              {missed.slice(0, 5).map((l) => (
                <Link
                  key={l.lesson_id}
                  to={`/teacher/lesson/${l.lesson_id}`}
                  className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 border border-amber-200"
                >
                  <span className="text-xs text-slate-500 shrink-0">
                    {formatDayMonth(l.date)}
                  </span>
                  <span className="text-sm text-slate-800 flex-1 truncate">
                    {l.group}
                  </span>
                  <ChevronRight size={15} className="text-slate-300 shrink-0" />
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* SUPPORT TEACHER uchun asosiy kunlik amal — SOAT BELGILASH
            (2026-08-10, Jahongir: "supportlar soat belgilashi yo'q
            bo'lib qolibdi"). Yo'qlama ustozning ishi, support esa
            o'z seansini yozadi — oyligi shundan chiqadi. */}
        {isSupport && (
          <Link
            to="/teacher/session"
            className="flex items-center gap-3 bg-brand-600 text-white rounded-xl shadow-sm p-4 active:scale-[0.99] transition"
          >
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
              <Timer size={19} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold">Soat belgilash</p>
              <p className="text-xs opacity-90">
                Bugungi seansingizni yozing — oylik shundan
              </p>
            </div>
            <ChevronRight size={18} className="opacity-70 shrink-0" />
          </Link>
        )}

        <div>
          <div className="flex items-baseline justify-between mb-2">
            <p className="text-sm font-semibold text-slate-800">
              {isSupport ? "Bugungi guruhlarim" : "Bugungi darslar"}
            </p>
            {!isSupport && d.pending > 0 && (
              <span className="text-xs font-medium text-amber-600">
                {d.pending} ta kutmoqda
              </span>
            )}
          </div>

          {d.today.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <p className="text-sm text-slate-500">Bugun darsingiz yo'q</p>
              <p className="text-xs text-slate-400 mt-1">Dam oling 🙂</p>
            </div>
          ) : (
            <div className="space-y-2">
              {d.today.map((l) => (
                <div key={l.lesson_id}>
                  <LessonRow l={l} to={isSupport ? "/teacher/session" : undefined} />
                  {!isSupport && plan?.english !== false && (
                    <PlanBlock item={plan?.items.find((p) => p.lesson_id === l.lesson_id)}
                               courses={plan?.courses ?? []} groupId={l.group_id} lessonId={l.lesson_id}
                               onChanged={loadPlan} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export function LessonRow({
  l,
  to,
}: {
  l: LessonCard;
  /** Support uchun boshqa manzil: u yo'qlama qo'ymaydi. */
  to?: string;
}) {
  return (
    <Link
      to={to ?? `/teacher/lesson/${l.lesson_id}`}
      className="flex items-center gap-3 bg-white rounded-xl shadow-sm border border-slate-200 p-4 active:scale-[0.99] transition"
    >
      <div
        className={`w-11 h-11 rounded-xl flex flex-col items-center justify-center shrink-0 ${
          l.done
            ? "bg-emerald-50 text-emerald-600"
            : "bg-brand-50 text-brand-600"
        }`}
      >
        {l.done ? (
          <CheckCircle2 size={20} />
        ) : (
          <>
            <Clock size={15} />
            <span className="text-[9px] font-semibold leading-none mt-0.5">
              {(l.time || "--:--").slice(0, 5)}
            </span>
          </>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-800 truncate">
          {l.group}
          {l.level ? (
            <span className="ml-1.5 text-[11px] font-normal text-slate-400">
              {l.level}
            </span>
          ) : null}
        </p>
        <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
          <Users size={12} />
          {l.marked}/{l.students} belgilangan
          {l.graded > 0 ? ` · ${l.graded} baho` : ""}
        </p>
        {/* Support uchun vaqt biriktirilmagan bo'lsa — jim turmasin,
            nima qilish kerakligi yozilsin (2026-09-10). */}
        {l.time_note && (
          <p className="text-[11px] text-amber-600 mt-0.5">{l.time_note}</p>
        )}
      </div>
      <ChevronRight size={17} className="text-slate-300 shrink-0" />
    </Link>
  );
}

/** 4 qadamli yo'riqnoma — bir marta ko'rsatiladi (yopilsa qayta chiqmaydi).
 *  Jahongir: "oson bo'lsin ko'rishga tushunishga, dovdirab yurmasin ustozlar". */
function GuideCard() {
  const KEY = "jony_teacher_guide_v1";
  const [open, setOpen] = useState(() => { try { return !localStorage.getItem(KEY); } catch { return true; } });
  if (!open) return null;
  const steps = [
    { icon: BookOpen, t: "Guruhni rejaga bog'lang", d: "Bir marta: daraja va qaysi darsdan boshlashni tanlang." },
    { icon: Play, t: "Darsni boshlang", d: "Bosqichlar, taymer va material — bitta oynada. Proyektor rejimi bor." },
    { icon: Send, t: "Topshiriq yuboring", d: "Rejadan tanlang — o'quvchi ilovasida darhol paydo bo'ladi, testlar o'zi tekshiriladi." },
    { icon: ClipboardCheck, t: "Writing/speaking'ni tekshiring", d: "Tayyor mezon va izohlar — 1 daqiqa." },
  ];
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-brand-100 p-4 relative">
      <button onClick={() => { try { localStorage.setItem(KEY, "1"); } catch { /* */ } setOpen(false); }}
              className="absolute top-3 right-3 text-slate-400" aria-label="Yopish"><X size={16} /></button>
      <p className="text-sm font-semibold text-slate-900 mb-2">Qanday ishlaydi — 4 qadam</p>
      <ol className="space-y-2">
        {steps.map((st, i) => (
          <li key={i} className="flex items-start gap-3">
            <span className="w-7 h-7 rounded-full bg-brand-50 text-brand-700 flex items-center justify-center shrink-0 text-xs font-bold">{i + 1}</span>
            <div><p className="text-sm font-medium text-slate-800 flex items-center gap-1.5"><st.icon size={14} className="text-brand-600" /> {st.t}</p><p className="text-xs text-slate-500">{st.d}</p></div>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Dars kartasining ostidagi reja bloki + katta "Darsni boshlash". */
function PlanBlock({ item, courses, groupId, lessonId, onChanged }: {
  item?: PlanItem; courses: { course: string; title: string; total: number }[];
  groupId: number; lessonId: number; onChanged: () => void;
}) {
  const [course, setCourse] = useState(item?.plan?.course ?? courses[0]?.course ?? "");
  const [no, setNo] = useState(item?.plan?.next_lesson_no ?? 1);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  // Noto'g'ri bog'langan rejani o'zgartirish (2026-09-21, Jahongir:
  // "notogri biriktirib qoysa ozgartirish funksiyasini ham qosh").
  const [editing, setEditing] = useState(false);
  const bind = async () => {
    if (!course) return;
    if (item?.plan && course !== item.plan.course &&
        !window.confirm("Daraja o'zgaradi va oldingi darsdan ko'chgan qismlar tozalanadi. Davom etasizmi?")) return;
    setBusy(true); setErr("");
    try { await api.put(`/groups/${groupId}/plan`, { course, next_lesson_no: no }); setEditing(false); onChanged(); }
    catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  };
  if (!item) return null;
  if (!item.plan || editing) {
    return (
      <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 px-4 py-3 -mt-1">
        <p className="text-sm font-medium text-slate-800">{editing ? "Rejani o'zgartirish" : "1-qadam: guruhni rejaga bog'lang"}</p>
        <p className="text-xs text-slate-500 mb-2">{editing
          ? "To'g'ri darajani va keyingi dars raqamini tanlang."
          : "Daraja va qaysi darsdan boshlashni tanlang. Keyin o'zgartirish mumkin."}</p>
        <div className="flex gap-2">
          <select value={course} onChange={(e) => setCourse(e.target.value)} className="flex-1 text-sm border border-slate-200 rounded-lg px-2 py-1.5 bg-white">
            {courses.map((c) => <option key={c.course} value={c.course}>{c.title}</option>)}
          </select>
          <input type="number" min={1} value={no} onChange={(e) => setNo(Number(e.target.value))} className="w-16 text-sm border border-slate-200 rounded-lg px-2 py-1.5" title="Qaysi darsdan" />
          <button onClick={bind} disabled={busy || !course} className="text-sm bg-brand-600 text-white rounded-lg px-3">{editing ? "Saqlash" : "Bog'lash"}</button>
        </div>
        {editing && (
          <button onClick={() => { setEditing(false); setErr(""); }} className="text-xs text-slate-500 mt-2">Bekor qilish</button>
        )}
        {err && <p className="text-xs text-rose-600 mt-1">{err}</p>}
      </div>
    );
  }
  const p = item.plan;
  const pct = Math.round(100 * (p.next_lesson_no - 1) / Math.max(1, p.total));
  const running = item.run && item.run.status !== "finished";
  const finished = item.run?.status === "finished";
  return (
    <div className="bg-white rounded-b-xl border border-t-0 border-slate-200 px-4 pt-3 pb-4 -mt-1">
      <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
        <span>{p.course_title}</span>
        <span className="flex items-center gap-2">
          {p.next_lesson_no - 1}/{p.total} o'tildi
          <button onClick={() => { setCourse(p.course); setNo(p.next_lesson_no); setEditing(true); }}
                  className="text-brand-600 font-medium">O'zgartirish</button>
        </span>
      </div>
      <div className="h-1 bg-slate-100 rounded-full mb-2"><div className="h-full bg-brand-500 rounded-full" style={{ width: `${pct}%` }} /></div>
      <p className="text-xs text-slate-500">Bugungi mavzu</p>
      <p className="text-base font-semibold text-slate-900 leading-snug">{p.next_lesson_no}-dars — {p.next_title ?? "…"}</p>
      {p.next_vocab && <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1"><BookOpen size={12} /> {p.next_vocab}</p>}
      <div className="mt-2 space-y-1.5">
        {p.carry.length > 0 && <Chip tone="amber" icon={Undo2} label="Oldingi darsdan ko'chgan" text={p.carry.join("; ")} />}
        {item.homework_missing.length > 0 && <Chip tone="rose" icon={AlertTriangle} label="Uy vazifasini bajarmagan" text={item.homework_missing.join(", ")} />}
        {item.help_needed.length > 0 && <Chip tone="sky" icon={LifeBuoy} label="Yordam kerak" text={item.help_needed.map((h) => `${h.name} (${h.why})`).join(", ")} />}
        {item.pending_checks > 0 && (
          <Link to="/teacher/check" className="block"><Chip tone="violet" icon={ClipboardCheck} label="Tekshirishni kutmoqda" text={`${item.pending_checks} ta writing/speaking →`} /></Link>
        )}
        {!p.carry.length && !item.homework_missing.length && !item.help_needed.length && !item.pending_checks && (
          <p className="text-[11px] text-emerald-600 flex items-center gap-1"><CheckCircle2 size={12} /> Hammasi joyida — boshlash mumkin</p>
        )}
      </div>
      <Link to={`/teacher-run/${lessonId}`}
            className={`mt-3 flex items-center justify-center gap-2 rounded-xl py-3.5 text-base font-bold text-white shadow-sm active:scale-[0.99] ${finished ? "bg-slate-400" : "bg-emerald-600"}`}>
        <Play size={18} />
        {finished ? `Dars yakunlangan (${item.run!.done}/${item.run!.total})` : running ? `Darsni davom ettirish (${item.run!.done}/${item.run!.total})` : "Darsni boshlash"}
      </Link>
    </div>
  );
}

function Chip({ tone, icon: Icon, label, text }: { tone: "amber" | "rose" | "sky" | "violet"; icon: typeof Undo2; label: string; text: string }) {
  const cls = { amber: "bg-amber-50 text-amber-800", rose: "bg-rose-50 text-rose-700", sky: "bg-sky-50 text-sky-700", violet: "bg-violet-50 text-violet-700" }[tone];
  return (
    <div className={`text-xs rounded-lg px-2.5 py-1.5 flex items-start gap-1.5 ${cls}`}>
      <Icon size={13} className="mt-0.5 shrink-0" />
      <span><b>{label}:</b> {text}</span>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3 text-center">
      <p className="text-xl font-bold text-slate-900 leading-tight">{value}</p>
      <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}
