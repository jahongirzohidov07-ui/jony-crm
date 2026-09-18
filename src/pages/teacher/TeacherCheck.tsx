import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ClipboardCheck, Sparkles, Mic, Check } from "lucide-react";
import { api } from "../../lib/api";
import SpeakRecorder from "../../components/SpeakRecorder";

/**
 * TEKSHIRISH (2026-09-18, Jahongir, 4-band): writing / speaking / erkin
 * javoblar — tayyor mezon (rubrika), tayyor izohlar (tanlanadi,
 * o'zgartiriladi), ovozli fikr, AI dastlabki tavsiya; yakuniy bahoni
 * ustoz tasdiqlaydi. Har safar uzun izoh yozilmaydi.
 */

type Row = { submission_id: number; assignment_id: number; title: string; kind: string; student: string; group: string; submitted_at: string | null; has_ai: boolean };
type Q = { kind: string; prompt: string; answer?: unknown; options?: string[] };
type AiReview = { score: number | null; max: number; errors: { wrong: string; right: string; why_uz: string }[]; comment_uz: string; heuristic?: boolean };
type Detail = {
  id: number; student: string; status: string; text: string | null; transcript: string | null; media_id: number | null;
  answers: Record<string, unknown>; max_score: number | null; teacher_score: number | null; comment: string | null;
  ai_review: AiReview | null;
  assignment: { title: string; kind: string; questions: Q[]; instr?: string | null };
  canned: string[]; rubric: [string, number][]; lesson_mistakes: string[][];
};

export default function TeacherCheck() {
  const { sid } = useParams();
  if (sid) return <CheckOne sid={Number(sid)} />;
  return <CheckList />;
}

function CheckList() {
  const [rows, setRows] = useState<Row[] | null>(null);
  useEffect(() => { api.fresh<Row[]>("/teacher/checks").then(setRows).catch(() => setRows([])); }, []);
  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-lg font-semibold text-slate-900 flex items-center gap-2 mb-1"><ClipboardCheck size={18} className="text-brand-600" /> Tekshirish</h1>
      <p className="text-xs text-slate-500 mb-3">Writing, speaking va erkin javoblar. Testlar avtomat tekshirilgan.</p>
      {!rows ? <p className="text-sm text-slate-400">Yuklanmoqda…</p> : rows.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-sm text-slate-500">Tekshirishni kutayotgan ish yo'q 🎉</div>
      ) : (
        <div className="space-y-2">
          {rows.map((r) => (
            <Link key={r.submission_id} to={`/teacher/check/${r.submission_id}`} className="block bg-white rounded-xl border border-slate-200 p-3">
              <div className="text-sm font-medium text-slate-900">{r.student} <span className="text-slate-400 font-normal">· {r.group}</span></div>
              <div className="text-xs text-slate-500">{r.title} · {r.kind}{r.submitted_at ? ` · ${r.submitted_at.slice(0, 16).replace("T", " ")}` : ""}</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function CheckOne({ sid }: { sid: number }) {
  const nav = useNavigate();
  const [d, setD] = useState<Detail | null>(null);
  const [err, setErr] = useState("");
  const [audio, setAudio] = useState<string | null>(null);
  const [rub, setRub] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");
  const [voice, setVoice] = useState<{ audio?: string; mime?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);

  useEffect(() => {
    api.fresh<Detail>(`/submissions/${sid}`).then((x) => {
      setD(x);
      const init: Record<string, number> = {};
      x.rubric.forEach(([k, p]) => { init[k] = p; });
      setRub(init);
      if (x.media_id) api.get<{ data: string }>(`/media/${x.media_id}`).then((m) => setAudio(m.data)).catch(() => {});
    }).catch((e) => setErr(e.message));
  }, [sid]);

  const total = Object.values(rub).reduce((a, b) => a + b, 0);
  const max = d?.rubric.reduce((a, [, p]) => a + p, 0) ?? 10;

  async function ai() {
    setAiBusy(true);
    try { const r = await api.post<AiReview>(`/submissions/${sid}/ai-review`); setD((p) => p ? { ...p, ai_review: r } : p); }
    catch (e) { setErr((e as Error).message); }
    finally { setAiBusy(false); }
  }
  async function grade(returnForFix = false) {
    setBusy(true); setErr("");
    try {
      await api.post(`/submissions/${sid}/grade`, { score: total, rubric_scores: rub, comment, voice: voice?.audio, voice_mime: voice?.mime, return_for_fix: returnForFix });
      nav("/teacher/check");
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }
  function addCanned(c: string) { setComment((p) => (p ? p + " " + c : c)); }
  function applyAi() {
    if (!d?.ai_review) return;
    const r = d.ai_review;
    if (r.score != null && r.max) {
      const k = r.score / r.max;   // AI umumiy ballini mezonlarga proporsional taqsimlash
      const next: Record<string, number> = {};
      d.rubric.forEach(([name, p]) => { next[name] = Math.round(p * k); });
      setRub(next);
    }
    if (r.comment_uz) setComment(r.comment_uz + (r.errors?.length ? " Xatolar: " + r.errors.map((e) => `${e.wrong} → ${e.right}`).join("; ") : ""));
  }

  if (err && !d) return <p className="p-6 text-sm text-rose-600">{err}</p>;
  if (!d) return <p className="p-6 text-sm text-slate-400">Yuklanmoqda…</p>;
  const a = d.assignment;

  return (
    <div className="p-4 space-y-3 max-w-md mx-auto">
      <Link to="/teacher/check" className="text-sm text-slate-500 flex items-center gap-1"><ArrowLeft size={14} /> Tekshirish</Link>
      <h1 className="text-base font-semibold text-slate-900">{d.student}</h1>
      <div className="text-xs text-slate-500">{a.title}</div>

      <div className="bg-white rounded-xl border border-slate-200 p-3 text-sm">
        {a.questions.map((q, i) => (
          <div key={i} className="mb-2">
            <div className="text-xs text-slate-500">{i + 1}. {q.prompt}</div>
            {q.kind === "text" && <div className="whitespace-pre-wrap mt-1">{d.text || String(d.answers[String(i)] ?? "")}</div>}
            {q.kind !== "text" && q.kind !== "audio" && (
              <div className="mt-1">{String(d.answers[String(i)] ?? "—")}
                {q.answer !== undefined && q.answer !== "" && <span className="text-emerald-700 text-xs"> (kalit: {q.kind === "mcq" && q.options ? q.options[Number(q.answer)] : String(q.answer)})</span>}
              </div>
            )}
          </div>
        ))}
        {audio && <audio controls src={audio} className="w-full mt-1" />}
        {d.transcript && <div className="text-xs text-slate-600 bg-slate-50 rounded-lg p-2 mt-2">Transkript: {d.transcript}</div>}
      </div>

      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 text-sm">
        <div className="flex items-center justify-between">
          <div className="font-semibold text-indigo-900 flex items-center gap-1"><Sparkles size={14} /> AI dastlabki tavsiya</div>
          <button onClick={ai} disabled={aiBusy} className="text-xs bg-indigo-600 text-white rounded-lg px-3 py-1.5">{aiBusy ? "…" : d.ai_review ? "Qayta" : "Tahlil qil"}</button>
        </div>
        {d.ai_review && (
          <div className="mt-2 text-xs text-indigo-900 space-y-1">
            {d.ai_review.score != null && <div>Taxminiy ball: <b>{d.ai_review.score}/{d.ai_review.max}</b>{d.ai_review.heuristic ? " (evristika)" : ""}</div>}
            {d.ai_review.errors?.map((e, i) => <div key={i}><span className="line-through text-rose-700">{e.wrong}</span> → <b className="text-emerald-700">{e.right}</b> — {e.why_uz}</div>)}
            <div className="italic">{d.ai_review.comment_uz}</div>
            <button onClick={applyAi} className="text-xs underline">Tavsiyani mezonlarga qo'llash (keyin o'zgartirasiz)</button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-3">
        <div className="text-sm font-semibold text-slate-800 mb-2">Baholash mezoni — {total}/{max}</div>
        {d.rubric.map(([name, p]) => (
          <div key={name} className="flex items-center justify-between gap-2 py-1.5 border-b border-slate-100 last:border-0">
            <div className="text-xs text-slate-700 flex-1">{name}</div>
            <div className="flex gap-1">
              {Array.from({ length: p + 1 }, (_, v) => (
                <button key={v} onClick={() => setRub({ ...rub, [name]: v })}
                        className={`w-7 h-7 rounded-lg text-xs border ${rub[name] === v ? "bg-brand-600 text-white border-brand-600" : "bg-white border-slate-200"}`}>{v}</button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-3">
        <div className="text-sm font-semibold text-slate-800 mb-2">Izoh</div>
        <div className="flex flex-wrap gap-1 mb-2">
          {d.canned.map((c, i) => <button key={i} onClick={() => addCanned(c)} className="text-[11px] bg-slate-100 hover:bg-brand-50 rounded-full px-2 py-1 text-left">{c}</button>)}
        </div>
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} placeholder="Tayyor izohni tanlang yoki yozing…" className="w-full text-sm border border-slate-200 rounded-lg p-2" />
        <div className="mt-2">
          <div className="text-xs text-slate-500 mb-1 flex items-center gap-1"><Mic size={12} /> Ovozli fikr (ixtiyoriy)</div>
          <SpeakRecorder seconds={60} label="Ovozli izoh yozish" busy={busy} onDone={(r) => setVoice({ audio: r.audio, mime: r.mime })} />
          {voice?.audio && <div className="text-xs text-emerald-700 mt-1">✓ Ovozli izoh tayyor</div>}
        </div>
      </div>

      {err && <div className="text-sm text-rose-600">{err}</div>}
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => grade(true)} disabled={busy} className="bg-amber-100 text-amber-800 rounded-xl py-3 text-sm font-semibold">↩ Qayta topshirsin</button>
        <button onClick={() => grade(false)} disabled={busy} className="bg-emerald-600 text-white rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-1"><Check size={16} /> Tasdiqlash {total}/{max}</button>
      </div>
    </div>
  );
}
