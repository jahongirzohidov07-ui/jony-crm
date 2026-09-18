import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen, CheckCircle2, Clock, Coins, RotateCcw, Send } from "lucide-react";
import { api } from "../../lib/api";
import SpeakRecorder from "../../components/SpeakRecorder";

/**
 * JONY STUDENT — "Darslar" (2026-09-18, Jahongir, 6-band: "Ustoz yuborgan
 * narsalar o'quvchining ilovasida avtomatik paydo bo'ladi: bugungi dars
 * mavzusi, o'tilgan lug'atlar va takrorlash kartochkalari, uy vazifasi
 * va muddati, ustoz izohi, xatolar ustida qayta ishlash, qoldirilgan
 * darsni o'zlashtirish paketi").
 */

type Sub = { id: number; status: string; attempt: number; auto_score: number | null; auto_max: number | null;
  teacher_score: number | null; max_score: number | null; comment: string | null; voice_media_id: number | null;
  graded_by: string | null; coins: number; text?: string | null; transcript?: string | null;
  result?: { items: { i: number; ok: boolean; given: unknown; answer: unknown; explain?: string | null }[] } | null;
  rubric_scores?: Record<string, number> | null };
type Item = { id: number; kind: string; skill: string; title: string; auto: boolean; due_at: string | null;
  questions_count: number; max_score: number | null; submission: Sub | null; overdue: boolean };
type Q = { kind: "mcq" | "gap" | "tf" | "text" | "audio"; prompt: string; sub?: string | null; options?: string[]; answer?: unknown; explain?: string | null };
type Detail = Item & { instr?: string | null; text?: { text: string[]; glossary: string[] } | null; questions: Q[];
  answers?: Record<string, unknown>; rubric?: [string, number][] | null };
type Card = { w: string; uz: string; ex: string; ipa?: string };
type Today = { lesson_no: number; title: string; grammar: string; vocab_topic: string; cards: Card[]; homework: string[]; formulas: string[][] };
type Data = {
  items: Item[]; pending: number; graded_new: number;
  today: Today | Record<string, never>;
  missed: { date: string; lesson_no: number; title: string; grammar_intro: string[]; formulas: string[][]; cards: Card[]; homework: string[] } | null;
};
type ReviewRow = { i: number; prompt: string; ok: boolean; given: unknown; answer: unknown; explain?: string | null };

const KIND_LABEL: Record<string, string> = {
  vocab_test: "Lug'at testi", grammar_test: "Grammatika testi", homework: "Uy vazifasi", reading: "Reading",
  writing: "Writing", speaking: "Speaking", free: "Mashq",
};

export default function StudentLessons() {
  const { aid } = useParams();
  if (aid) return <DoAssignment aid={Number(aid)} />;
  return <LessonsHome />;
}

function LessonsHome() {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [flip, setFlip] = useState<Record<number, boolean>>({});
  const [showMissed, setShowMissed] = useState(false);
  const nav = useNavigate();
  useEffect(() => { api.fresh<Data>("/student/assignments").then(setD).catch((e) => setErr(e.message)); }, []);

  async function startMissed() {
    try { const a = await api.post<{ id: number }>("/student/assignments/missed-test"); nav(`/student/lessons/${a.id}`); }
    catch (e) { setErr((e as Error).message); }
  }

  if (err) return <p className="p-6 text-sm text-rose-600">{err}</p>;
  if (!d) return <p className="p-6 text-sm text-slate-400">Yuklanmoqda…</p>;
  const t: Today | null = d.today && "title" in d.today ? (d.today as Today) : null;
  const pending = d.items.filter((i) => !i.submission || i.submission.status === "returned");
  const done = d.items.filter((i) => i.submission && i.submission.status !== "returned");

  return (
    <div className="p-4 space-y-4 max-w-md mx-auto">
      <h1 className="text-lg font-semibold text-slate-900 flex items-center gap-2"><BookOpen size={18} className="text-brand-600" /> Darslarim</h1>

      {t && (
        <div className="bg-gradient-to-br from-brand-600 to-indigo-600 text-white rounded-2xl p-4">
          <div className="text-xs opacity-80">Bugungi / joriy dars</div>
          <div className="font-bold">{t.lesson_no}-dars — {t.title}</div>
          <div className="text-xs opacity-90 mt-1">Lug'at: {t.vocab_topic}</div>
          {t.formulas.length > 0 && (
            <div className="mt-2 space-y-1 text-xs bg-white/10 rounded-lg p-2">
              {t.formulas.map((f, i) => <div key={i}><b>{f[0]}</b>: {f[1]} — <i>{f[2]}</i></div>)}
            </div>
          )}
        </div>
      )}

      {d.missed && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
          <div className="font-semibold text-amber-900">Qoldirilgan dars — {d.missed.lesson_no}-dars</div>
          <div className="text-xs text-amber-800 mb-2">{d.missed.date} · {d.missed.title}</div>
          <button onClick={() => setShowMissed(!showMissed)} className="text-xs text-amber-700 underline">{showMissed ? "Yashirish" : "Darsni o'zlashtirish paketi"}</button>
          {showMissed && (
            <div className="mt-2 text-sm text-amber-900 space-y-2">
              <ul className="list-disc pl-5 text-xs">{d.missed.grammar_intro.map((x, i) => <li key={i}>{x}</li>)}</ul>
              <div className="text-xs bg-white/70 rounded-lg p-2">{d.missed.formulas.map((f, i) => <div key={i}><b>{f[0]}</b>: {f[1]} — {f[2]}</div>)}</div>
              <div className="text-xs">Uy vazifasi: {d.missed.homework.join("; ")}</div>
              <button onClick={startMissed} className="w-full bg-amber-600 text-white rounded-xl py-2 text-sm font-semibold">Lug'at testini boshlash (20 so'z)</button>
            </div>
          )}
        </div>
      )}

      <section>
        <div className="text-sm font-semibold text-slate-800 mb-2">Bajarish kerak ({pending.length})</div>
        {pending.length === 0 && <div className="bg-white rounded-xl border border-slate-200 p-4 text-sm text-slate-500 text-center">Hozircha yangi topshiriq yo'q 🙂</div>}
        <div className="space-y-2">{pending.map((i) => <ItemRow key={i.id} i={i} />)}</div>
      </section>

      {t && t.cards.length > 0 && (
        <section>
          <div className="text-sm font-semibold text-slate-800 mb-2">Takrorlash kartochkalari — {t.vocab_topic}</div>
          <div className="grid grid-cols-2 gap-2">
            {t.cards.map((c, i) => (
              <button key={i} onClick={() => setFlip({ ...flip, [i]: !flip[i] })}
                      className={`rounded-xl p-3 text-left min-h-[76px] border ${flip[i] ? "bg-emerald-50 border-emerald-200" : "bg-white border-slate-200"}`}>
                {flip[i] ? (
                  <><div className="text-sm font-semibold text-emerald-800">{c.uz}</div><div className="text-[11px] text-slate-500 mt-1">{c.ex}</div></>
                ) : (
                  <><div className="text-sm font-semibold text-slate-900">{c.w}</div>{c.ipa && <div className="text-[11px] text-slate-400">/{c.ipa}/</div>}</>
                )}
              </button>
            ))}
          </div>
        </section>
      )}

      {done.length > 0 && (
        <section>
          <div className="text-sm font-semibold text-slate-800 mb-2">Bajarilgan ({done.length})</div>
          <div className="space-y-2">{done.map((i) => <ItemRow key={i.id} i={i} />)}</div>
        </section>
      )}
    </div>
  );
}

function scoreOf(i: Item) {
  const s = i.submission;
  if (!s) return null;
  if (s.status === "graded" && s.teacher_score != null) return `${s.teacher_score}/${i.max_score}`;
  if (s.status === "graded" && s.auto_score != null) return `${s.auto_score}/${s.auto_max}`;
  if (s.status === "returned") return "qayta topshiring";
  return "tekshirilmoqda";
}

function ItemRow({ i }: { i: Item }) {
  const s = i.submission;
  const sc = scoreOf(i);
  return (
    <Link to={`/student/lessons/${i.id}`} className="flex items-center gap-3 bg-white rounded-xl border border-slate-200 p-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${s?.status === "graded" ? "bg-emerald-50 text-emerald-600" : s?.status === "returned" ? "bg-amber-50 text-amber-600" : "bg-brand-50 text-brand-600"}`}>
        {s?.status === "graded" ? <CheckCircle2 size={18} /> : s?.status === "returned" ? <RotateCcw size={18} /> : <Clock size={18} />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-900 truncate">{i.title}</div>
        <div className="text-[11px] text-slate-500">
          {KIND_LABEL[i.kind] ?? i.kind} · {i.questions_count} savol{i.due_at && !s ? ` · muddat ${i.due_at.slice(0, 10)}` : ""}
          {i.overdue && <span className="text-rose-600"> · muddat o'tgan</span>}
        </div>
        {s?.comment && <div className="text-[11px] text-emerald-700 mt-0.5 truncate">💬 {s.comment}</div>}
      </div>
      {sc && <div className="text-xs font-semibold text-slate-700 whitespace-nowrap">{sc}{s?.coins ? <span className="text-amber-600"> +{s.coins}🪙</span> : null}</div>}
    </Link>
  );
}

// ---------- Topshiriqni bajarish ----------
function DoAssignment({ aid }: { aid: number }) {
  const nav = useNavigate();
  const [d, setD] = useState<Detail | null>(null);
  const [err, setErr] = useState("");
  const [ans, setAns] = useState<Record<string, unknown>>({});
  const [text, setText] = useState("");
  const [audio, setAudio] = useState<{ audio?: string; mime?: string; transcript?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [review, setReview] = useState<ReviewRow[] | null>(null);
  const [voice, setVoice] = useState<string | null>(null);
  const [redo, setRedo] = useState(false);

  useEffect(() => {
    api.fresh<Detail>(`/student/assignments/${aid}`).then((x) => { setD(x); if (x.answers) setAns(x.answers); }).catch((e) => setErr(e.message));
  }, [aid]);
  useEffect(() => {
    const vid = d?.submission?.voice_media_id;
    if (vid) api.get<{ data: string }>(`/media/${vid}`).then((m) => setVoice(m.data)).catch(() => {});
  }, [d?.submission?.voice_media_id]);

  async function submit() {
    if (!d) return;
    setBusy(true); setErr("");
    try {
      const r = await api.post<Sub & { review?: ReviewRow[] }>(`/student/assignments/${aid}/submit`,
        { answers: ans, text: text || undefined, audio: audio?.audio, mime: audio?.mime, transcript: audio?.transcript });
      setReview(r.review ?? null);
      setRedo(false);
      setD(await api.fresh<Detail>(`/student/assignments/${aid}`));
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  if (err && !d) return <p className="p-6 text-sm text-rose-600">{err}</p>;
  if (!d) return <p className="p-6 text-sm text-slate-400">Yuklanmoqda…</p>;
  const s = d.submission;
  const done = !redo && !!s && s.status !== "returned";
  const autoIdx = d.questions.map((q, i) => (["mcq", "gap", "tf"].includes(q.kind) ? i : -1)).filter((i) => i >= 0);
  const answered = autoIdx.every((i) => ans[String(i)] !== undefined && ans[String(i)] !== "");
  const needText = d.questions.some((q) => q.kind === "text");
  const needAudio = d.questions.some((q) => q.kind === "audio");
  const canSubmit = !done && answered && (!needText || text.trim().length > 0) && (!needAudio || !!audio);

  return (
    <div className="p-4 space-y-3 max-w-md mx-auto">
      <button onClick={() => nav("/student/lessons")} className="text-sm text-slate-500 flex items-center gap-1"><ArrowLeft size={14} /> Darslarim</button>
      <h1 className="text-base font-semibold text-slate-900">{d.title}</h1>
      {d.instr && <p className="text-sm text-slate-700">{d.instr}</p>}
      {d.text && (
        <div className="bg-white rounded-xl border border-slate-200 p-3 text-sm leading-relaxed">
          {d.text.text.map((p, i) => <p key={i} className="mb-2">{p}</p>)}
          <div className="text-[11px] text-slate-500 bg-slate-50 rounded px-2 py-1">{d.text.glossary.join(" · ")}</div>
        </div>
      )}

      {done && s && (
        <div className={`rounded-xl p-3 text-sm ${s.status === "graded" ? "bg-emerald-50 border border-emerald-200" : "bg-slate-50 border border-slate-200"}`}>
          {s.status === "graded" ? (
            <div className="font-semibold text-emerald-800">
              Natija: {s.teacher_score ?? s.auto_score}/{s.teacher_score != null ? d.max_score : s.auto_max}
              {s.coins ? <span className="text-amber-600 ml-2"><Coins size={13} className="inline" /> +{s.coins} coin</span> : null}
            </div>
          ) : <div className="text-slate-600">Ustoz tekshirishini kutmoqda…</div>}
          {s.rubric_scores && <div className="text-xs text-slate-600 mt-1">{Object.entries(s.rubric_scores).map(([k, v]) => `${k}: ${v}`).join(" · ")}</div>}
          {s.comment && <div className="text-sm text-slate-800 mt-1">💬 {s.comment}</div>}
          {voice && <audio controls src={voice} className="w-full mt-2" />}
        </div>
      )}
      {s?.status === "returned" && <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm text-amber-800">↩️ Ustoz qayta topshirishni so'radi{s.comment ? `: ${s.comment}` : ""}. Tuzatib qayta yuboring.</div>}

      <div className="space-y-3">
        {d.questions.map((q, i) => {
          const rv: ReviewRow | { i: number; ok: boolean; given: unknown; answer: unknown; explain?: string | null } | null =
            done ? (review?.find((r) => r.i === i) ?? s?.result?.items.find((r) => r.i === i) ?? null) : null;
          const wrong = rv && !rv.ok;
          return (
            <div key={i} className={`bg-white rounded-xl border p-3 ${wrong ? "border-rose-300" : rv ? "border-emerald-300" : "border-slate-200"}`}>
              <div className="text-sm font-medium text-slate-900">{i + 1}. {q.prompt}</div>
              {q.sub && <div className="text-xs text-slate-500">{q.sub}</div>}
              {q.kind === "mcq" && (
                <div className="grid grid-cols-1 gap-1.5 mt-2">
                  {q.options?.map((o, k) => (
                    <button key={k} disabled={done} onClick={() => setAns({ ...ans, [String(i)]: k })}
                            className={`text-left text-sm rounded-lg px-3 py-2 border ${ans[String(i)] === k ? "bg-brand-600 text-white border-brand-600" : "bg-white border-slate-200"} ${done && q.answer === k ? "ring-2 ring-emerald-400" : ""}`}>
                      {o}
                    </button>
                  ))}
                </div>
              )}
              {q.kind === "gap" && (
                <input disabled={done} value={String(ans[String(i)] ?? "")} onChange={(e) => setAns({ ...ans, [String(i)]: e.target.value })}
                       placeholder="Javob…" className="mt-2 w-full text-sm border border-slate-200 rounded-lg px-3 py-2" />
              )}
              {q.kind === "tf" && (
                <div className="flex gap-2 mt-2">
                  {["T", "F"].map((v) => (
                    <button key={v} disabled={done} onClick={() => setAns({ ...ans, [String(i)]: v })}
                            className={`flex-1 rounded-lg py-2 text-sm border ${ans[String(i)] === v ? "bg-brand-600 text-white border-brand-600" : "bg-white border-slate-200"}`}>
                      {v === "T" ? "To'g'ri" : "Noto'g'ri"}
                    </button>
                  ))}
                </div>
              )}
              {q.kind === "text" && (
                done ? <div className="mt-2 text-sm bg-slate-50 rounded-lg p-2 whitespace-pre-wrap">{s?.text}</div>
                     : <textarea value={text} onChange={(e) => setText(e.target.value)} rows={6} placeholder="Matningizni yozing…"
                                 className="mt-2 w-full text-sm border border-slate-200 rounded-lg px-3 py-2" />
              )}
              {q.kind === "audio" && (
                done ? <div className="mt-2 text-xs text-slate-500">Audio yuborilgan{s?.transcript ? `: "${s.transcript.slice(0, 160)}…"` : ""}</div>
                     : <div className="mt-2">
                         <SpeakRecorder seconds={90} label="Javobni yozib oling" busy={busy}
                                        onDone={(r) => setAudio({ audio: r.audio, mime: r.mime, transcript: r.transcript })} />
                         {audio && <div className="text-xs text-emerald-700 mt-1">✓ Audio tayyor{audio.transcript ? ` — "${audio.transcript.slice(0, 80)}…"` : ""}</div>}
                       </div>
              )}
              {rv && (
                <div className={`text-xs mt-2 ${wrong ? "text-rose-700" : "text-emerald-700"}`}>
                  {wrong ? <>✗ To'g'ri javob: <b>{q.kind === "mcq" && q.options ? q.options[Number(rv.answer)] : String(rv.answer)}</b>{rv.explain ? ` — ${rv.explain}` : ""}</> : "✓ To'g'ri"}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {err && <div className="text-sm text-rose-600">{err}</div>}
      {!done && (
        <button onClick={submit} disabled={!canSubmit || busy}
                className="w-full bg-brand-600 disabled:opacity-40 text-white rounded-xl py-3 text-base font-semibold flex items-center justify-center gap-2">
          <Send size={16} /> Topshirish
        </button>
      )}
      {done && d.auto && s && s.auto_score !== s.auto_max && (
        <button onClick={() => { setReview(null); setRedo(true); }}
                className="w-full bg-white border border-brand-300 text-brand-700 rounded-xl py-2.5 text-sm font-semibold">
          Xatolar ustida qayta ishlash (coin berilmaydi)
        </button>
      )}
    </div>
  );
}
