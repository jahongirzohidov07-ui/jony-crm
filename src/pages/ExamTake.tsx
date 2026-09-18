import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { BrandIcon } from "../components/BrandIcon";

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

type Q = {
  id: string;
  n: number;
  type: "choice" | "text";
  q: string;
  options?: string[];
  image?: string | null;
};
type Part = {
  title: string;
  instructions?: string;
  passage?: string;
  audio_url?: string | null;
  image?: string | null;
  questions: Q[];
};
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

const LETTERS = "ABCDEFGH";

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

function mmss(sec: number) {
  const s = Math.max(0, Math.ceil(sec));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

export default function ExamTake() {
  const { token = "" } = useParams();
  const api = `/api/public/exam/${encodeURIComponent(token)}`;
  const [exam, setExam] = useState<PublicExam | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  // Server soati bilan farq (ms) — sanoq va taymer server vaqti bo'yicha
  const [offset, setOffset] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [key, setKey] = useState<string | null>(() => store(`exam:${token}:key`));
  const [step, setStep] = useState<"who" | "photo">("who");
  const [studentId, setStudentId] = useState<number | null>(null);
  const [notListed, setNotListed] = useState(false);
  const [name, setName] = useState("");
  const [search, setSearch] = useState("");
  const [photo, setPhoto] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | number>>(
    () => store(`exam:${token}:answers`) || {}
  );
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<Done | null>(() => store(`exam:${token}:done`));
  const savedRef = useRef<string>("");
  const submittingRef = useRef(false);

  const load = useCallback(() => {
    return fetch(api)
      .then(async (r) => {
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.detail || "Test topilmadi");
        setOffset(Date.parse(j.server_now) - Date.now());
        setExam(j);
        return j as PublicExam;
      })
      .catch((e) => {
        setLoadErr(e.message);
        return null;
      });
  }, [api]);

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
        const r = await fetch(`${api}/submit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key, answers }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.detail || "Yuborib bo'lmadi");
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
    [key, answers, api, token]
  );

  // Javoblarni 15 soniyada bir serverga saqlash — telefon o'chib qolsa ham
  useEffect(() => {
    if (done || !key || state !== "running") return;
    const t = setInterval(() => {
      const body = JSON.stringify(answers);
      if (body === savedRef.current) return;
      savedRef.current = body;
      fetch(`${api}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, answers }),
      }).catch(() => {
        savedRef.current = "";
      });
    }, 15000);
    return () => clearInterval(t);
  }, [done, key, state, answers, api]);

  // Vaqt tugadi — belgilanganlari bilan avtomatik topshiriladi
  useEffect(() => {
    if (done || !key) return;
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

  const answered = Object.values(answers).filter(
    (v) => v !== "" && v !== null && v !== undefined
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: notListed ? null : studentId,
          name: notListed ? name.trim() : null,
          photo,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.detail || "Kirib bo'lmadi");
      store(`exam:${token}:key`, j.key);
      setKey(j.key);
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

  const shell = (body: React.ReactNode) => (
    <div className="min-h-screen bg-gradient-to-br from-brand-700 to-brand-500 py-6 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-white rounded-xl p-2 shadow">
            <BrandIcon size={32} className="rounded-lg" />
          </div>
          <div className="text-white">
            <p className="font-extrabold tracking-wide leading-tight">JONY ACADEMY</p>
            {exam && (
              <p className="text-xs text-white/85">
                {exam.title} · {exam.group}
              </p>
            )}
          </div>
        </div>
        {body}
      </div>
    </div>
  );
  const card = "bg-white rounded-2xl shadow-xl p-5";

  if (loadErr)
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-3xl mb-2">🔍</p>
        <p className="text-slate-700">{loadErr}</p>
      </div>
    );
  if (!exam) return shell(<div className={`${card} text-slate-400 text-sm`}>Yuklanmoqda...</div>);

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
        <h1 className="text-lg font-bold text-slate-900">Rasmingizni oling</h1>
        <p className="text-xs text-slate-500 mb-4">
          Kamera ochiladi — yuzingiz aniq ko'rinsin. Rasm faqat examinerga
          ko'rinadi.
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
        <button onClick={() => setStep("who")} className="w-full mt-2 text-sm text-slate-500">
          ← Orqaga
        </button>
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
  const low = endsIn !== null && endsIn <= 60;
  return shell(
    <div className="space-y-4 pb-24">
      {exam.parts.map((p, pi) => (
        <div key={pi} className={card}>
          <h2 className="font-bold text-slate-900">{p.title}</h2>
          {p.instructions && (
            <p className="text-sm text-slate-600 mt-1 whitespace-pre-line">{p.instructions}</p>
          )}
          {p.audio_url && <audio controls src={p.audio_url} className="w-full mt-3" />}
          {p.image && (
            <img src={p.image} alt="" className="mt-3 w-full max-w-xl rounded-lg border border-slate-200" />
          )}
          {p.passage && (
            <div className="mt-3 bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm text-slate-800 whitespace-pre-line leading-relaxed">
              {p.passage}
            </div>
          )}
          <div className="mt-4 space-y-5">
            {p.questions.map((q) => (
              <div key={q.id}>
                {q.image && (
                  <img
                    src={q.image}
                    alt=""
                    className="max-h-40 max-w-full rounded-lg border border-slate-200 mb-2"
                  />
                )}
                <p className="text-sm text-slate-800 mb-2 whitespace-pre-line">
                  <span className="font-semibold text-slate-500 mr-1.5">{q.n}.</span>
                  {q.q}
                </p>
                {q.type === "choice" ? (
                  // Faqat harfli variantlar (rasmdan tanlash) — bir qatorda
                  <div
                    className={
                      (q.options || []).every((o, i) => o === LETTERS[i])
                        ? "flex flex-wrap gap-1.5"
                        : "grid gap-1.5"
                    }
                  >
                    {(q.options || []).map((o, oi) => (
                      <button
                        key={oi}
                        onClick={() => setAnswers({ ...answers, [q.id]: oi })}
                        className={`text-left rounded-xl border px-3 py-2.5 text-sm transition ${
                          answers[q.id] === oi
                            ? "border-brand-500 bg-brand-50 text-brand-800 font-medium"
                            : "border-slate-200 text-slate-700 hover:border-slate-300"
                        }`}
                      >
                        <span className="font-semibold mr-2">{LETTERS[oi]}</span>
                        {o !== LETTERS[oi] && o}
                      </button>
                    ))}
                  </div>
                ) : (
                  <input
                    className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
                    value={String(answers[q.id] ?? "")}
                    autoCapitalize="off"
                    autoCorrect="off"
                    spellCheck={false}
                    placeholder="Javobni yozing"
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="fixed bottom-0 inset-x-0 bg-white/95 border-t border-slate-200 px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          {endsIn !== null && (
            <span
              className={`text-lg font-bold tabular-nums ${
                low ? "text-red-600" : "text-slate-800"
              }`}
              title="Qolgan vaqt"
            >
              ⏱ {mmss(endsIn)}
            </span>
          )}
          <span className="text-sm text-slate-500 whitespace-nowrap">
            {answered} / {exam.q_count}
          </span>
          {error && <span className="text-xs text-red-600 flex-1 truncate">{error}</span>}
          <button
            onClick={manualSubmit}
            disabled={sending}
            className="ml-auto bg-brand-600 hover:bg-brand-700 text-white rounded-xl px-6 py-2.5 text-sm font-semibold disabled:opacity-60"
          >
            {sending ? "Yuborilmoqda..." : "Topshirish"}
          </button>
        </div>
      </div>
    </div>
  );
}
