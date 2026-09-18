import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { BrandIcon } from "../components/BrandIcon";

/**
 * ONLINE TEST — loginsiz, link orqali (2026-09-18, Jahongir: "shu
 * linkni examiner telegramdan tashlab bersa o'quvchilar kirib baholay
 * olsin").
 *
 * 1) ro'yxatdan o'zini tanlaydi (yo'q bo'lsa ismini yozadi);
 * 2) kameradan rasm oladi (galereyadan emas);
 * 3) testni yechadi — ball serverda hisoblanadi.
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
  questions: Q[];
};
type PublicExam = {
  title: string;
  group: string;
  date: string | null;
  is_open: boolean;
  q_count: number;
  paper_max: number;
  students: { id: number; name: string }[];
  parts: Part[];
};
type Done = { score: number; max: number; paper_max: number; pending: boolean };

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

export default function ExamTake() {
  const { token = "" } = useParams();
  const [exam, setExam] = useState<PublicExam | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [step, setStep] = useState<"who" | "photo" | "test">("who");
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
  const [done, setDone] = useState<Done | null>(
    () => store(`exam:${token}:done`)
  );

  useEffect(() => {
    fetch(`/api/public/exam/${encodeURIComponent(token)}`)
      .then(async (r) => {
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.detail || "Test topilmadi");
        setExam(j);
      })
      .catch((e) => setLoadErr(e.message));
  }, [token]);

  useEffect(() => {
    store(`exam:${token}:answers`, answers);
  }, [token, answers]);

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

  async function submit() {
    if (!exam) return;
    if (
      answered < exam.q_count &&
      !confirm(
        `${exam.q_count - answered} ta savolga javob berilmagan. Baribir topshirasizmi?`
      )
    )
      return;
    setSending(true);
    setError(null);
    try {
      const r = await fetch(
        `/api/public/exam/${encodeURIComponent(token)}/submit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            student_id: notListed ? null : studentId,
            name: notListed ? name.trim() : null,
            photo,
            answers,
          }),
        }
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.detail || "Yuborib bo'lmadi");
      const d: Done = {
        score: j.score, max: j.max, paper_max: j.paper_max, pending: j.pending,
      };
      store(`exam:${token}:done`, d);
      setDone(d);
      window.scrollTo(0, 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSending(false);
    }
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
        <h1 className="text-lg font-bold text-slate-900 mb-1">Javoblaringiz qabul qilindi</h1>
        <p className="text-3xl font-bold text-brand-700 my-3">
          {done.score} / {done.max}
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

  if (!exam.is_open)
    return shell(
      <div className={`${card} text-center`}>
        <p className="text-3xl mb-2">🔒</p>
        <p className="text-slate-700">Test yopilgan. Examinerga murojaat qiling.</p>
      </div>
    );

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

  if (step === "photo")
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
          disabled={!photo}
          onClick={() => {
            setStep("test");
            window.scrollTo(0, 0);
          }}
          className="w-full mt-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold disabled:opacity-50"
        >
          Testni boshlash
        </button>
        <button
          onClick={() => setStep("who")}
          className="w-full mt-2 text-sm text-slate-500"
        >
          ← Orqaga
        </button>
      </div>
    );

  return shell(
    <div className="space-y-4 pb-24">
      {exam.parts.map((p, pi) => (
        <div key={pi} className={card}>
          <h2 className="font-bold text-slate-900">{p.title}</h2>
          {p.instructions && (
            <p className="text-sm text-slate-600 mt-1">{p.instructions}</p>
          )}
          {p.audio_url && (
            <audio controls src={p.audio_url} className="w-full mt-3" />
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
                <p className="text-sm text-slate-800 mb-2">
                  <span className="font-semibold text-slate-500 mr-1.5">{q.n}.</span>
                  {q.q}
                </p>
                {q.type === "choice" ? (
                  <div className="grid gap-1.5">
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
                        {o}
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
                    placeholder="To'liq so'zni yozing"
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
          <span className="text-sm text-slate-600 whitespace-nowrap">
            {answered} / {exam.q_count}
          </span>
          {error && <span className="text-xs text-red-600 flex-1 truncate">{error}</span>}
          <button
            onClick={submit}
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
