import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { BrandIcon } from "../components/BrandIcon";
import { type PaperPart } from "../components/ExamPaper";
import { CdExam } from "../components/CdExam";
import { useAuth } from "../lib/AuthContext";
import { getToken } from "../lib/api";

/**
 * ONLINE TEST — loginsiz, link orqali (2026-09-18, Jahongir: "shu
 * linkni examiner telegramdan tashlab bersa o'quvchilar kirib baholay
 * olsin").
 *
 * 1) ro'yxatdan o'zini tanlaydi (yo'q bo'lsa ismini yozadi);
 * 2) kameradan rasm oladi (galereyadan emas);
 * 3) KUTADI — examiner vaqt belgilab "Start" bosganda teskari sanoq
 *    bilan savollar ochiladi (2026-09-18);
 * 4) testni yechadi — javoblar oraliqda serverga saqlanadi, vaqt
 *    tugaganda belgilangan javoblar bilan avtomatik topshiriladi.
 * Havola: https://jonyos.uz/t/<token>
 */

type Part = PaperPart;
type State = "waiting" | "countdown" | "running" | "finished" | "closed";
type PublicExam = {
  title: string;
  group: string;
  date: string | null;
  is_open: boolean;
  state: State;
  server_now: string;
  starts_at: string | null;
  ends_at: string | null;
  duration_min: number | null;
  q_count: number;
  paper_max: number;
  students: { id: number; name: string }[];
  parts: Part[];
};
type Done = { paper_max: number; pending: boolean; auto?: boolean };

function store(key: string, val?: unknown) {
  try {
    if (val === undefined) {
      const v = localStorage.getItem(key);
      return v ? JSON.parse(v) : null;
    }
    localStorage.setItem(key, JSON.stringify(val));
  } catch {
    /* maxfiy oyna — saqlanmaydi, test baribir ishlaydi */
  }
  return null;
}

/** Kameradan olingan rasmni 480px gacha kichraytirib JPEG qiladi. */
function shrink(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, 480 / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * k);
      c.height = Math.round(img.height * k);
      c.getContext("2d")!.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      resolve(c.toDataURL("image/jpeg", 0.7));
    };
    img.onerror = () => reject(new Error("Rasmni o'qib bo'lmadi"));
    img.src = url;
  });
}

type Me = { id: number; name: string };
type Mine = {
  status: string;
  key: string | null;
  submitted_at: string | null;
  pending: boolean;
  paper_max: number;
};

/**
 * inApp=true — JONY STUDENT ILOVASI ICHIDA (2026-09-25, Jahongir:
 * "cherer Student app qiladigan qilish kerak link ham shu Student
 * appga keladigan qilaylik"). Kim ekani login'dan (ro'yxat yo'q),
 * rasm bilan tasdiqlash qoladi, natija to'g'ridan-to'g'ri o'z
 * qatoriga tushadi. Javob saqlash/topshirish avvalgi public yo'llar
 * bilan (kalit orqali) — bitta mantiq.
 *
 * inApp=false — /t/<token> havolasi: o'quvchi kirgan bo'lsa ilovaga
 * yo'naltiriladi; kirmagan bo'lsa "Ilovada topshirish" (login) yoki
 * mehmon tartibi (ro'yxatdan tanlash — ilovada hisobi yo'qlar uchun).
 */
export default function ExamTake({ inApp = false }: { inApp?: boolean }) {
  const { token = "" } = useParams();
  const { user } = useAuth();
  const pub = `/api/public/exam/${encodeURIComponent(token)}`;
  const api = inApp ? `/api/student/exam/${encodeURIComponent(token)}` : pub;
  const authHeaders = useCallback((): Record<string, string> => {
    if (!inApp) return {};
    const t = getToken();
    return t ? { Authorization: `Bearer ${t}` } : {};
  }, [inApp]);
  // Mehmon tartibi (ro'yxatdan tanlab) — faqat havola sahifasida,
  // o'quvchi ilovada hisobi yo'qligini o'zi tanlaganda
  const [guest, setGuest] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [exam, setExam] = useState<PublicExam | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  // Server soati bilan farq (ms) — sanoq va taymer server vaqti bo'yicha
  const [offset, setOffset] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [key, setKey] = useState<string | null>(() => store(`exam:${token}:key`));
  // Suv belgisida turadigan ism (sahifa yangilansa ham saqlanib qoladi)
  const [who, setWho] = useState<string>(() => store(`exam:${token}:who`) || "");
  // Ilovada ro'yxat bosqichi yo'q — to'g'ridan-to'g'ri rasm
  const [step, setStep] = useState<"who" | "photo">(inApp ? "photo" : "who");
  const [studentId, setStudentId] = useState<number | null>(null);
  const [notListed, setNotListed] = useState(false);
  const [name, setName] = useState("");
  const [search, setSearch] = useState("");
  const [photo, setPhoto] = useState<string | null>(null);
  const [answers, setAnswers] = useState<
    Record<string, string | number | number[]>
  >(
    () => store(`exam:${token}:answers`) || {}
  );
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<Done | null>(() => store(`exam:${token}:done`));
  // Testdan chetlatilgan (chiqishlar chegarasidan oshdi yoki examiner
  // chetlatdi) — 2026-09-23
  const [expelled, setExpelled] = useState<boolean>(
    () => !!store(`exam:${token}:expelled`)
  );
  const kickOut = useCallback(() => {
    store(`exam:${token}:expelled`, true);
    setExpelled(true);
    window.scrollTo(0, 0);
  }, [token]);
  const [awayLeft, setAwayLeft] = useState<number | null>(null);
  const savedRef = useRef<string>("");
  const submittingRef = useRef(false);

  const load = useCallback(() => {
    return fetch(api, { headers: authHeaders() })
      .then(async (r) => {
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.detail || "Test topilmadi");
        setOffset(Date.parse(j.server_now) - Date.now());
        setExam(j);
        if (inApp) {
          // Ilovada: kim ekani serverdan; davom etayotgan topshiriq
          // bo'lsa kaliti qaytadi (telefon o'chib qolsa ham davom
          // etadi); allaqachon topshirgan bo'lsa yakun ekrani.
          const m = j.me as Me | undefined;
          if (m) {
            setMe(m);
            setWho(m.name);
            store(`exam:${token}:who`, m.name);
          }
          const mine = j.my as Mine | null | undefined;
          if (mine?.status === "in_progress" && mine.key) {
            store(`exam:${token}:key`, mine.key);
            setKey(mine.key);
          } else if (mine && ["placed", "duplicate", "pending"].includes(mine.status)) {
            const d: Done = { paper_max: mine.paper_max, pending: mine.pending };
            store(`exam:${token}:done`, d);
            setDone(d);
          } else if (mine?.status === "expelled") {
            store(`exam:${token}:expelled`, true);
            setExpelled(true);
          }
        }
        return j as PublicExam;
      })
      .catch((e) => {
        setLoadErr(e.message);
        return null;
      });
  }, [api, authHeaders, inApp, token]);

  useEffect(() => {
    load();
  }, [load]);

  // Soniya sanagich
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    store(`exam:${token}:answers`, answers);
  }, [token, answers]);

  const serverNow = now + offset;
  const startsIn = exam?.starts_at ? (Date.parse(exam.starts_at) - serverNow) / 1000 : null;
  const endsIn = exam?.ends_at ? (Date.parse(exam.ends_at) - serverNow) / 1000 : null;

  // Kutish: examiner Start bosishini kuzatamiz (4 soniyada bir)
  const state = exam?.state;
  useEffect(() => {
    if (done || !key || state !== "waiting") return;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [done, key, state, load]);

  // Sanoq tugadi — savollarni olamiz
  useEffect(() => {
    if (state === "countdown" && startsIn !== null && startsIn <= 0) load();
  }, [state, startsIn, load]);

  // ANDROID ILOVASI BILAN ALOQA (2026-09-23). Test "Jony Imtihon"
  // ilovasida ochilgan bo'lsa, savollar chiqqanda ekran qulflanadi
  // (boshqa ilovaga o'tib bo'lmaydi), test tugagach qo'yib yuboriladi.
  // Brauzerda JonyApp bo'lmaydi — u yerda hammasi eskicha ishlayveradi.
  useEffect(() => {
    const app = (window as unknown as {
      JonyApp?: { examStarted?: () => void; examFinished?: () => void };
    }).JonyApp;
    if (!app) return;
    if (state === "running" && !done && !expelled) app.examStarted?.();
    else app.examFinished?.();
  }, [state, done, expelled]);

  // Test ketyapti: 20 soniyada bir holatni yangilaymiz (examiner
  // muddatidan oldin tugatishi mumkin)
  useEffect(() => {
    if (done || state !== "running") return;
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, [done, state, load]);

  const submit = useCallback(
    async (auto = false) => {
      if (!key || submittingRef.current) return;
      submittingRef.current = true;
      setSending(true);
      setError(null);
      try {
        // Topshirish/saqlash/chiqish — kalit bilan public yo'l (ilovada ham)
        const r = await fetch(`${pub}/submit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key, answers }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.detail || "Yuborib bo'lmadi");
        if (j.expelled) {
          store(`exam:${token}:expelled`, true);
          setExpelled(true);
          return;
        }
        const d: Done = { paper_max: j.paper_max, pending: j.pending, auto };
        store(`exam:${token}:done`, d);
        setDone(d);
        window.scrollTo(0, 0);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Xatolik");
        submittingRef.current = false;
      } finally {
        setSending(false);
      }
    },
    [key, answers, pub, token]
  );

  // Javoblarni 15 soniyada bir serverga saqlash — telefon o'chib qolsa ham
  useEffect(() => {
    if (done || !key || state !== "running") return;
    const t = setInterval(() => {
      const body = JSON.stringify(answers);
      if (body === savedRef.current) return;
      savedRef.current = body;
      fetch(`${pub}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, answers }),
      })
        .then((r) => r.json())
        .then((j) => {
          if (j?.expelled) kickOut();
        })
        .catch(() => {
          savedRef.current = "";
        });
    }, 15000);
    return () => clearInterval(t);
  }, [done, key, state, answers, pub, kickOut]);

  // SAHIFADAN CHIQISH QAYDI (2026-09-23, Jahongir). O'quvchi boshqa
  // ilovaga o'tsa — necha marta va qancha vaqtga chiqqani yoziladi.
  useEffect(() => {
    if (done || !key || state !== "running") return;
    let left = 0;
    const onChange = () => {
      if (document.visibilityState === "hidden") {
        left = Date.now();
        return;
      }
      if (!left) return;
      const sec = Math.round((Date.now() - left) / 1000);
      left = 0;
      fetch(`${pub}/away`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, seconds: sec }),
      })
        .then((r) => r.json())
        .then((j) => {
          if (j?.expelled) kickOut();
          else if (j?.left != null)
            setAwayLeft(j.left as number);
        })
        .catch(() => {});
    };
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, [done, key, state, pub, kickOut]);

  // Vaqt tugadi — belgilanganlari bilan avtomatik topshiriladi
  useEffect(() => {
    if (done || expelled || !key) return;
    const timeUp =
      (state === "running" && endsIn !== null && endsIn <= 0) || state === "finished";
    if (timeUp) submit(true);
  }, [done, key, state, endsIn, submit]);

  const students = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (exam?.students || []).filter(
      (s) => !q || s.name.toLowerCase().includes(q)
    );
  }, [exam, search]);

  const answered = Object.values(answers).filter((v) =>
    Array.isArray(v) ? v.length > 0 : v !== "" && v !== null && v !== undefined
  ).length;

  async function onPhoto(file?: File) {
    if (!file) return;
    setError(null);
    try {
      setPhoto(await shrink(file));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function begin() {
    setSending(true);
    setError(null);
    try {
      const r = await fetch(`${api}/begin`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(
          inApp
            ? { photo }        // ilovada kim ekani login'dan
            : {
                student_id: notListed ? null : studentId,
                name: notListed ? name.trim() : null,
                photo,
              },
        ),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.detail || "Kirib bo'lmadi");
      store(`exam:${token}:key`, j.key);
      setKey(j.key);
      const nm = j.name || me?.name || (notListed ? name.trim() : "");
      store(`exam:${token}:who`, nm);
      setWho(nm);
      await load();
      window.scrollTo(0, 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSending(false);
    }
  }

  function manualSubmit() {
    if (
      exam &&
      answered < exam.q_count &&
      !confirm(
        `${exam.q_count - answered} ta savolga javob berilmagan. Baribir topshirasizmi?`
      )
    )
      return;
    submit(false);
  }

  // "ILOVADA OCHISH" (2026-09-23). Telegram havolani o'z ichki
  // brauzerida ochib yuboradi — u yerda skrinshotni to'sib bo'lmaydi.
  // Androidda shu tugma ilovani to'g'ridan-to'g'ri ochadi; ilova
  // o'rnatilmagan bo'lsa sahifaning o'zi qolaveradi.
  const androidLink =
    !inApp &&
    typeof navigator !== "undefined" &&
    /Android/i.test(navigator.userAgent) &&
    !(window as unknown as { JonyApp?: unknown }).JonyApp
      ? `intent://${window.location.host}/t/${token}#Intent;scheme=https;` +
        `package=uz.jonyacademy.exam;S.browser_fallback_url=` +
        `${encodeURIComponent(window.location.href)};end`
      : null;

  // Test ketayotganda ilovaga qaytish havolasi ko'rsatilmaydi (chalg'itmasin)
  const canLeave = inApp && (!key || !!done || expelled);

  const shell = (body: React.ReactNode) => (
    <div className="min-h-screen bg-gradient-to-br from-brand-700 to-brand-500 py-6 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-white rounded-xl p-2 shadow">
            <BrandIcon size={32} className="rounded-lg" />
          </div>
          <div className="text-white flex-1 min-w-0">
            <p className="font-extrabold tracking-wide leading-tight">
              {inApp ? "JONY STUDENT · IMTIHON" : "JONY ACADEMY"}
            </p>
            {exam && (
              <p className="text-xs text-white/85 truncate">
                {exam.title} · {exam.group}
              </p>
            )}
          </div>
          {canLeave && (
            <Link
              to="/student"
              className="text-xs font-semibold text-white/90 bg-white/15 border border-white/30 rounded-lg px-3 py-1.5 shrink-0"
            >
              ← Ilovaga
            </Link>
          )}
        </div>
        {androidLink && !done && (
          <a
            href={androidLink}
            className="flex items-center justify-center gap-2 mb-3 rounded-xl bg-white/15 border border-white/30 px-4 py-2.5 text-sm font-medium text-white"
          >
            📱 Jony Imtihon ilovasida ochish
          </a>
        )}
        {body}
      </div>
    </div>
  );
  const card = "bg-white rounded-2xl shadow-xl p-5";

  // HAVOLA ILOVAGA OLIB KIRADI (2026-09-25). /t/<kod> ochilganda:
  //  - o'quvchi ilovada kirgan bo'lsa -> ilovadagi imtihon sahifasi;
  //  - kirmagan bo'lsa -> "Ilovada topshirish" (login, keyin shu
  //    imtihonga qaytadi) yoki mehmon tartibi (ilovada hisobi yo'q).
  if (!inApp && user?.role === "student")
    return <Navigate to={`/student/exam/${encodeURIComponent(token)}`} replace />;
  if (!inApp && !guest && !key && !done)
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-4xl mb-2">📱</p>
        <h1 className="text-lg font-bold text-slate-900 mb-1">
          Imtihon Jony Student ilovasida topshiriladi
        </h1>
        <p className="text-sm text-slate-600 mb-4">
          Ilovaga o'z login-parolingiz bilan kiring — imtihon o'sha yerda
          ochiladi va natija to'g'ridan-to'g'ri sizning ismingizga tushadi.
        </p>
        <Link
          to={`/login?next=${encodeURIComponent(`/student/exam/${token}`)}`}
          className="block w-full bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold"
        >
          Ilovaga kirib topshirish
        </Link>
        <button
          onClick={() => setGuest(true)}
          className="w-full mt-3 text-sm text-slate-500 underline decoration-dotted"
        >
          Ilovada hisobim yo'q — ro'yxatdan tanlab topshiraman
        </button>
      </div>
    );

  if (loadErr)
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-3xl mb-2">🔍</p>
        <p className="text-slate-700">{loadErr}</p>
      </div>
    );
  if (!exam) return shell(<div className={`${card} text-slate-400 text-sm`}>Yuklanmoqda...</div>);

  if (expelled)
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-4xl mb-2">🚫</p>
        <h1 className="text-lg font-bold text-slate-900 mb-1">
          Siz testdan chetlatildingiz
        </h1>
        <p className="text-sm text-slate-600">
          Test sahifasidan ruxsat etilganidan ko'p marta chiqib ketdingiz yoki
          examiner sizni chetlatdi. Bu test hisobga olinmaydi — examinerga
          murojaat qiling.
        </p>
      </div>
    );

  if (done)
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-4xl mb-2">✅</p>
        <h1 className="text-lg font-bold text-slate-900 mb-1">
          {done.auto ? "Vaqt tugadi — javoblaringiz topshirildi" : "Javoblaringiz qabul qilindi"}
        </h1>
        {/* Ball bu yerda ko'rsatilmaydi — examiner tasdiqlagach e'lon
            qilinadi (2026-09-18, Jahongir) */}
        <p className="text-sm text-slate-600 my-3">
          Natijangiz examiner tekshirib tasdiqlagandan keyin e'lon qilinadi.
        </p>
        {done.paper_max > 0 && (
          <p className="text-sm text-slate-600">
            Writing va Speaking (qog'ozda, {done.paper_max} ball) examiner
            tomonidan qo'shiladi.
          </p>
        )}
        {done.pending && (
          <p className="text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2 mt-3">
            Natijangizni examiner tekshirib, ismingizga biriktiradi.
          </p>
        )}
      </div>
    );

  if (exam.state === "closed" || (exam.state === "finished" && !key))
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-3xl mb-2">🔒</p>
        <p className="text-slate-700">
          {exam.state === "finished" ? "Test vaqti tugagan." : "Test yopilgan."} Examinerga
          murojaat qiling.
        </p>
      </div>
    );

  // ------------------------------------------------ o'zini tanitish
  if (!key) {
    if (step === "who")
      return shell(
        <div className={card}>
          <h1 className="text-lg font-bold text-slate-900">Ro'yxatdan o'zingizni tanlang</h1>
          <p className="text-xs text-slate-500 mb-3">
            {exam.title} · {exam.q_count} ta savol
          </p>
          {!notListed ? (
            <>
              {exam.students.length > 8 && (
                <input
                  className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm mb-3"
                  placeholder="Qidirish..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              )}
              <div className="grid gap-2">
                {students.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setStudentId(s.id)}
                    className={`text-left rounded-xl border px-4 py-3 text-sm font-medium transition ${
                      studentId === s.id
                        ? "border-brand-500 bg-brand-50 text-brand-800"
                        : "border-slate-200 text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
              <button
                onClick={() => {
                  setNotListed(true);
                  setStudentId(null);
                }}
                className="w-full mt-3 text-sm text-slate-500 underline decoration-dotted"
              >
                Ro'yxatda yo'qman
              </button>
            </>
          ) : (
            <>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Ism va familiyangiz
              </label>
              <input
                autoFocus
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Familiya Ism"
              />
              <button
                onClick={() => setNotListed(false)}
                className="w-full mt-3 text-sm text-slate-500 underline decoration-dotted"
              >
                ← Ro'yxatga qaytish
              </button>
            </>
          )}
          <button
            disabled={notListed ? name.trim().length < 3 : !studentId}
            onClick={() => setStep("photo")}
            className="w-full mt-4 bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold disabled:opacity-50"
          >
            Davom etish
          </button>
        </div>
      );

    return shell(
      <div className={card}>
        {inApp && me && (
          <div className="mb-3 rounded-xl bg-brand-50 border border-brand-100 px-3 py-2">
            <p className="text-[11px] text-slate-500">Imtihon topshiruvchi</p>
            <p className="text-sm font-bold text-slate-900">{me.name}</p>
            <p className="text-[11px] text-slate-500">
              {exam.title} · {exam.q_count} ta savol
              {exam.duration_min ? ` · ${exam.duration_min} daqiqa` : ""}
            </p>
          </div>
        )}
        <h1 className="text-lg font-bold text-slate-900">Rasmingizni oling</h1>
        <p className="text-xs text-slate-500 mb-4">
          Kamera ochiladi — yuzingiz aniq ko'rinsin. Rasm faqat examinerga
          ko'rinadi{inApp ? " (siz ekaningizni tasdiqlash uchun)" : ""}.
        </p>
        {photo ? (
          <img src={photo} alt="" className="w-40 h-40 object-cover rounded-2xl mx-auto mb-3" />
        ) : (
          <div className="w-40 h-40 rounded-2xl bg-slate-100 mx-auto mb-3 flex items-center justify-center text-5xl">
            📷
          </div>
        )}
        <label className="block w-full text-center border border-brand-500 text-brand-700 rounded-xl py-3 text-sm font-semibold cursor-pointer">
          {photo ? "Qayta olish" : "Kamerani ochish"}
          <input
            type="file"
            accept="image/*"
            capture="user"
            className="hidden"
            onChange={(e) => onPhoto(e.target.files?.[0])}
          />
        </label>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        <button
          disabled={!photo || sending}
          onClick={begin}
          className="w-full mt-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold disabled:opacity-50"
        >
          {sending ? "Kirilmoqda..." : "Tayyorman"}
        </button>
        {!inApp && (
          <button onClick={() => setStep("who")} className="w-full mt-2 text-sm text-slate-500">
            ← Orqaga
          </button>
        )}
      </div>
    );
  }

  // ------------------------------------------------ kutish / sanoq
  if (exam.state === "waiting" || exam.state === "countdown" || !exam.parts.length) {
    const counting = exam.state === "countdown" && startsIn !== null && startsIn > 0;
    return shell(
      <div className={`${card} text-center py-10`}>
        {counting ? (
          <>
            <p className="text-sm text-slate-500 mb-2">Test boshlanmoqda</p>
            <p className="text-7xl font-extrabold text-brand-700 tabular-nums">
              {Math.ceil(startsIn!)}
            </p>
          </>
        ) : exam.state === "finished" ? (
          <>
            <p className="text-3xl mb-2">⏱</p>
            <p className="text-slate-700">Vaqt tugadi — javoblaringiz topshirilmoqda…</p>
          </>
        ) : (
          <>
            <p className="text-4xl mb-3">⏳</p>
            <h1 className="text-lg font-bold text-slate-900">Kuting, test hali boshlanmadi</h1>
            <p className="text-sm text-slate-500 mt-2">
              Examiner "Start" bosganda savollar shu yerda o'zi ochiladi.
              Sahifani yopmang.
            </p>
            {exam.duration_min ? (
              <p className="text-xs text-slate-400 mt-3">Vaqt: {exam.duration_min} daqiqa</p>
            ) : null}
          </>
        )}
      </div>
    );
  }

  // ------------------------------------------------ test
  // KOMPYUTERDAGI IELTS KO'RINISHI (2026-09-27, Jahongir: "readingda
  // esa chap tomonda text, ong tomonda esa savollar turishi kerak ...
  // IELTS niki"). Butun ekran: tepada taymer, bo'limma-bo'lim, pastda
  // savol raqamlari. Saqlash / chiqish / topshirish mantiqi o'zgarmadi.
  const awayWarn = awayLeft != null && awayLeft <= 2;
  const notice =
    awayWarn || error || (androidLink && !done) ? (
      <>
        {awayWarn ? (
          <span className="font-medium">
            {(awayLeft ?? 0) > 0
              ? `Yana ${awayLeft} marta chiqsangiz — chetlatilasiz`
              : "Yana chiqsangiz — chetlatilasiz"}
          </span>
        ) : null}
        {error ? <span className="text-red-600">{error}</span> : null}
        {androidLink && !done ? (
          <a href={androidLink} className="underline font-medium">
            📱 Jony Imtihon ilovasida ochish
          </a>
        ) : null}
      </>
    ) : null;
  return (
    <CdExam
      parts={exam.parts}
      answers={answers}
      onChange={(qid, v) => setAnswers({ ...answers, [qid]: v })}
      title={exam.title}
      subtitle={`${exam.group}${inApp ? " · Jony Student" : " · Jony Academy"}`}
      endsIn={endsIn}
      answered={answered}
      total={exam.q_count}
      onSubmit={manualSubmit}
      sending={sending}
      notice={notice}
      watermark={who ? `${who} · ${exam.title}` : undefined}
      storageKey={`exam:${token}`}
    />
  );
}
