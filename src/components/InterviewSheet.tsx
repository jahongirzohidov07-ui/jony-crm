import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { X, Printer, Lightbulb, Check, Loader2 } from "lucide-react";
import { api } from "../lib/api";

/**
 * SUHBAT VARAQASI (2026-10-08, Jahongir: "nomzodlar degan joyiga
 * qo'shib ber, savol va javobini yozishga bo'sh joy qoldirib ishni
 * osonlashtir").
 *
 * Savollar serverda (api/interview_guide.py). Har suhbatdosh O'Z
 * varaqasini to'ldiradi: javob, 1-5 ball, kuzatuvlarda ha/yo'q.
 * Yozib turganda o'zi saqlanadi, alohida "Saqlash" bosish shart emas.
 */

type Kind = "score" | "check" | "note";
type GuideQ = {
  id: string; text: string; why: string; look: string;
  good: string; bad: string; kind: Kind; core: boolean; only: string | null;
};
type Section = { key: string; title: string; hint: string; items: GuideQ[] };
type Rec = { key: string; label: string; tone: string };
type Guide = {
  version: string; sections: Section[]; recommendations: Rec[];
  total: number; core_total: number;
};
type Answer = { a?: string; s?: number; ok?: boolean };
type Sheet = {
  id: number; author_id: number; author: string | null;
  answers: Record<string, Answer>;
  recommendation: string | null; recommendation_label: string | null;
  strengths: string | null; concerns: string | null; note: string | null;
  percent: number | null; answered: number;
  checks_ok: number; checks_total: number;
  by_section: { key: string; title: string; avg: number | null; count: number }[];
  updated_at: string | null;
};
type Data = {
  candidate: { id: number; full_name: string; phone: string | null;
    position: string | null; subject: string | null };
  guide: Guide; mine: Sheet | null; others: Sheet[];
};

const qNo = (id: string) =>
  id.startsWith("o") ? "K" + id.slice(1) : id.slice(1);

const SCORE_TONE = ["", "bg-red-500", "bg-orange-500", "bg-amber-500",
  "bg-lime-500", "bg-emerald-600"];
const REC_TONE: Record<string, string> = {
  emerald: "bg-emerald-600 text-white border-emerald-600",
  teal: "bg-teal-600 text-white border-teal-600",
  amber: "bg-amber-500 text-white border-amber-500",
  orange: "bg-orange-500 text-white border-orange-500",
  red: "bg-red-600 text-white border-red-600",
};

export function InterviewSheet({ candidateId, onClose, onSaved }: {
  candidateId: number;
  onClose: () => void;
  onSaved?: () => void;
}) {
  const [data, setData] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [rec, setRec] = useState<string | null>(null);
  const [strengths, setStrengths] = useState("");
  const [concerns, setConcerns] = useState("");
  const [note, setNote] = useState("");
  const [coreOnly, setCoreOnly] = useState(false);
  const [hints, setHints] = useState(true);
  // null — o'z varaqam; son — boshqa suhbatdoshning varaqasi (faqat o'qish)
  const [viewId, setViewId] = useState<number | null>(null);
  const [status, setStatus] = useState<"" | "dirty" | "saving" | "saved" | "error">("");
  const [stats, setStats] = useState<Sheet | null>(null);
  const timer = useRef<number | null>(null);
  const dirty = useRef(false);

  useEffect(() => {
    api.get<Data>(`/candidates/${candidateId}/interview-sheet`, true)
      .then((d) => {
        setData(d);
        const m = d.mine;
        if (m) {
          setAnswers(m.answers || {});
          setRec(m.recommendation);
          setStrengths(m.strengths || "");
          setConcerns(m.concerns || "");
          setNote(m.note || "");
          setStats(m);
        }
      })
      .catch((e) => setErr(e.message || "Yuklab bo'lmadi"));
  }, [candidateId]);

  const payload = useMemo(() => ({
    answers, recommendation: rec, strengths, concerns, note,
  }), [answers, rec, strengths, concerns, note]);
  const latest = useRef(payload);
  latest.current = payload;

  const save = useCallback(async () => {
    if (!dirty.current) return;
    dirty.current = false;
    setStatus("saving");
    try {
      const s = await api.put<Sheet>(
        `/candidates/${candidateId}/interview-sheet`, latest.current);
      setStats(s);
      setStatus(dirty.current ? "dirty" : "saved");
      onSaved?.();
    } catch {
      dirty.current = true;
      setStatus("error");
    }
  }, [candidateId, onSaved]);

  // Avto-saqlash: oxirgi o'zgarishdan 1.2 soniya o'tib
  const touch = () => {
    dirty.current = true;
    setStatus("dirty");
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(save, 1200);
  };
  useEffect(() => () => {
    if (timer.current) window.clearTimeout(timer.current);
  }, []);

  const close = async () => {
    if (timer.current) window.clearTimeout(timer.current);
    await save();
    onClose();
  };

  const viewing = viewId === null
    ? null
    : data?.others.find((s) => s.id === viewId) || null;
  const readOnly = !!viewing;
  const shownAnswers = viewing ? viewing.answers : answers;
  const shownStats = viewing || stats;

  const setA = (id: string, patch: Answer) => {
    if (readOnly) return;
    setAnswers((prev) => {
      const next = { ...(prev[id] || {}), ...patch };
      (Object.keys(next) as (keyof Answer)[]).forEach((k) => {
        if (next[k] === undefined || next[k] === "") delete next[k];
      });
      return { ...prev, [id]: next };
    });
    touch();
  };

  if (err) {
    return (
      <Shell onClose={onClose}>
        <p className="p-6 text-red-600 text-sm">{err}</p>
      </Shell>
    );
  }
  if (!data) {
    return (
      <Shell onClose={onClose}>
        <div className="p-10 flex justify-center text-slate-400">
          <Loader2 className="animate-spin" />
        </div>
      </Shell>
    );
  }

  const g = data.guide;
  const total = coreOnly ? g.core_total : g.total;

  return (
    <Shell onClose={close}>
      {/* Sarlavha */}
      <div className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 sm:px-6 py-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <div className="min-w-0 flex-1">
            <p className="text-xs text-slate-400">Suhbat varaqasi</p>
            <h2 className="font-semibold text-slate-900 truncate">
              {data.candidate.full_name}
            </h2>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-500">
              Javob: <b className="text-slate-800">{shownStats?.answered ?? 0}</b>/{total}
            </span>
            <span className="text-slate-500">
              Ball:{" "}
              <b className="text-slate-800">
                {shownStats?.percent != null ? `${shownStats.percent}%` : "—"}
              </b>
            </span>
            {!readOnly && <SaveStatus status={status} />}
          </div>
          <div className="flex items-center gap-2">
            {data.others.length > 0 && (
              <select
                value={viewId ?? ""}
                onChange={(e) => setViewId(e.target.value ? Number(e.target.value) : null)}
                className="text-sm px-2 py-1.5 rounded-lg border border-slate-200 bg-white"
                title="Boshqa suhbatdoshlar varaqasi"
              >
                <option value="">Mening varaqam</option>
                {data.others.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.author || "—"}{s.percent != null ? ` · ${s.percent}%` : ""}
                  </option>
                ))}
              </select>
            )}
            <button
              onClick={() => printSheet(g, data.candidate.full_name,
                viewing || (stats ? { ...stats, answers } : null), coreOnly)}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50"
              title="Chop etish yoki PDF saqlash"
            >
              <Printer size={15} /> Chop etish
            </button>
            <button onClick={close} className="p-1.5 text-slate-400 hover:text-slate-700" title="Yopish">
              <X size={20} />
            </button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 mt-2.5 text-xs">
          <Toggle on={!coreOnly} onClick={() => setCoreOnly(false)}>
            Hamma savollar ({g.total})
          </Toggle>
          <Toggle on={coreOnly} onClick={() => setCoreOnly(true)}>
            Faqat asosiy ({g.core_total}) · 45-60 daqiqa
          </Toggle>
          <span className="mx-1 h-4 w-px bg-slate-200" />
          <Toggle on={hints} onClick={() => setHints(!hints)}>
            <Lightbulb size={12} className="inline -mt-0.5 mr-1" />
            Yo'riqnoma
          </Toggle>
          {readOnly && (
            <span className="ml-auto px-2 py-1 rounded bg-amber-50 text-amber-800">
              {viewing?.author} varaqasi — faqat ko'rish
            </span>
          )}
        </div>
      </div>

      <div className="px-4 sm:px-6 py-5 space-y-6 bg-slate-50">
        {g.sections.map((sec) => {
          const items = sec.items.filter((q) => !coreOnly || q.core);
          if (!items.length) return null;
          const avg = shownStats?.by_section.find((x) => x.key === sec.key)?.avg;
          return (
            <section key={sec.key}>
              <div className="flex items-baseline gap-3 mb-1">
                <h3 className="font-semibold text-slate-800">{sec.title}</h3>
                {avg != null && (
                  <span className="text-xs text-slate-500">o'rtacha {avg}/5</span>
                )}
              </div>
              {hints && sec.hint && (
                <p className="text-xs text-slate-500 mb-2.5">{sec.hint}</p>
              )}
              <div className="space-y-2.5">
                {items.map((q) => (
                  <QuestionCard
                    key={q.id}
                    q={q}
                    hints={hints}
                    value={shownAnswers[q.id] || {}}
                    readOnly={readOnly}
                    onChange={(p) => setA(q.id, p)}
                  />
                ))}
              </div>
            </section>
          );
        })}

        {/* Xulosa */}
        <section className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5">
          <h3 className="font-semibold text-slate-800 mb-3">Xulosa</h3>
          <p className="text-xs text-slate-500 mb-2">Tavsiyangiz</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {g.recommendations.map((r) => {
              const on = (viewing ? viewing.recommendation : rec) === r.key;
              return (
                <button
                  key={r.key}
                  disabled={readOnly}
                  onClick={() => { setRec(on ? null : r.key); touch(); }}
                  className={`px-3 py-1.5 rounded-lg border text-sm ${on
                    ? REC_TONE[r.tone] || "bg-slate-700 text-white"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                >
                  {r.label}
                </button>
              );
            })}
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <Area label="Kuchli tomonlari" readOnly={readOnly}
              value={viewing ? viewing.strengths || "" : strengths}
              onChange={(v) => { setStrengths(v); touch(); }} />
            <Area label="Xavotirlar / tekshirish kerak" readOnly={readOnly}
              value={viewing ? viewing.concerns || "" : concerns}
              onChange={(v) => { setConcerns(v); touch(); }} />
          </div>
          <div className="mt-3">
            <Area label="Umumiy izoh" readOnly={readOnly}
              value={viewing ? viewing.note || "" : note}
              onChange={(v) => { setNote(v); touch(); }} />
          </div>
          {shownStats && shownStats.checks_total > 0 && (
            <p className="text-xs text-slate-500 mt-3">
              Kuzatuv: {shownStats.checks_ok}/{shownStats.checks_total} ijobiy.
              Kuzatuvlar ballga qo'shilmaydi, faqat qo'shimcha belgi.
            </p>
          )}
          <p className="text-xs text-slate-400 mt-1">
            Ball — 1-5 baholar o'rtachasi. Nomzod kartasidagi "Intervyu bahosi"
            barcha suhbatdoshlar varaqalaridan o'zi hisoblanadi.
          </p>
        </section>
      </div>
    </Shell>
  );
}

function QuestionCard({ q, hints, value, readOnly, onChange }: {
  q: GuideQ; hints: boolean; value: Answer; readOnly: boolean;
  onChange: (p: Answer) => void;
}) {
  const ta = useRef<HTMLTextAreaElement>(null);
  // Matn uzaysa maydon ham o'sadi
  useEffect(() => {
    const el = ta.current;
    if (el) { el.style.height = "auto"; el.style.height = el.scrollHeight + "px"; }
  }, [value.a]);
  const filled = !!(value.a || value.s || value.ok !== undefined);

  return (
    <div className={`bg-white rounded-xl border p-3.5 sm:p-4 ${filled ? "border-brand-200" : "border-slate-200"}`}>
      <div className="flex gap-3">
        <span className={`shrink-0 w-7 h-7 rounded-full text-xs font-semibold flex items-center justify-center ${filled ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-500"}`}>
          {qNo(q.id)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-800 leading-snug">
            {q.text}
            {q.core && (
              <span className="ml-2 align-middle text-[10px] font-semibold px-1.5 py-0.5 rounded bg-brand-50 text-brand-700">ASOSIY</span>
            )}
            {q.only && (
              <span className="ml-1.5 align-middle text-[10px] font-semibold px-1.5 py-0.5 rounded bg-violet-50 text-violet-700">{q.only}</span>
            )}
          </p>
          {hints && (q.why || q.look || q.good || q.bad) && (
            <div className="mt-1.5 text-xs space-y-1">
              {q.why && <p className="text-slate-500"><b className="text-slate-600">Maqsad:</b> {q.why}</p>}
              {q.look && <p className="text-slate-500"><b className="text-slate-600">E'tibor bering:</b> {q.look}</p>}
              {(q.good || q.bad) && (
                <div className="grid sm:grid-cols-2 gap-1.5 pt-0.5">
                  {q.good && <p className="rounded-md bg-emerald-50 text-emerald-800 px-2 py-1">✅ {q.good}</p>}
                  {q.bad && <p className="rounded-md bg-rose-50 text-rose-800 px-2 py-1">❌ {q.bad}</p>}
                </div>
              )}
            </div>
          )}

          {q.kind === "check" ? (
            <div className="flex gap-2 mt-2.5">
              {[true, false].map((v) => (
                <button
                  key={String(v)}
                  disabled={readOnly}
                  onClick={() => onChange({ ok: value.ok === v ? undefined : v })}
                  className={`px-3 py-1 rounded-lg border text-sm ${value.ok === v
                    ? v ? "bg-emerald-600 text-white border-emerald-600" : "bg-rose-600 text-white border-rose-600"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
                >
                  {v ? "✅ Ha" : "❌ Yo'q"}
                </button>
              ))}
            </div>
          ) : null}

          <textarea
            ref={ta}
            rows={q.kind === "check" ? 1 : 2}
            readOnly={readOnly}
            value={value.a || ""}
            onChange={(e) => onChange({ a: e.target.value })}
            placeholder={q.kind === "check" ? "Izoh (ixtiyoriy)" : "Nomzod javobi..."}
            className="mt-2.5 w-full resize-none overflow-hidden px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200 read-only:bg-slate-50"
          />

          {q.kind === "score" && (
            <div className="flex items-center gap-1.5 mt-2">
              <span className="text-xs text-slate-400 mr-1">Baho:</span>
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  disabled={readOnly}
                  onClick={() => onChange({ s: value.s === n ? undefined : n })}
                  className={`w-8 h-8 rounded-lg text-sm font-semibold border ${value.s === n
                    ? `${SCORE_TONE[n]} text-white border-transparent`
                    : "border-slate-200 text-slate-500 hover:bg-slate-50"}`}
                >
                  {n}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Shell({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex sm:p-4">
      <div className="bg-white w-full max-w-4xl mx-auto sm:rounded-xl overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

function Toggle({ on, onClick, children }: {
  on: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 rounded-full border ${on
        ? "bg-slate-800 text-white border-slate-800"
        : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}
    >
      {children}
    </button>
  );
}

function Area({ label, value, onChange, readOnly }: {
  label: string; value: string; onChange: (v: string) => void; readOnly: boolean;
}) {
  return (
    <label className="block">
      <span className="text-xs text-slate-500">{label}</span>
      <textarea
        rows={3}
        readOnly={readOnly}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-200 text-sm read-only:bg-slate-50"
      />
    </label>
  );
}

function SaveStatus({ status }: { status: string }) {
  if (status === "saving" || status === "dirty")
    return <span className="text-xs text-slate-400">Saqlanmoqda…</span>;
  if (status === "saved")
    return <span className="text-xs text-emerald-600 inline-flex items-center gap-1"><Check size={13} />Saqlandi</span>;
  if (status === "error")
    return <span className="text-xs text-red-600">Saqlanmadi — internetni tekshiring</span>;
  return null;
}

// ------------------------------------------------------------ chop etish
const esc = (s: string) =>
  s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));

/** Varaqani alohida oynada chop etish (yoki PDF qilib saqlash).
 *  Javob bo'lmasa — qog'ozda to'ldirish uchun bo'sh qatorlar. */
export function printSheet(g: Guide, name: string, sheet: Sheet | null, coreOnly = false) {
  const ans = sheet?.answers || {};
  const today = new Date().toLocaleDateString("uz-UZ");
  const body = g.sections.map((sec) => {
    const items = sec.items.filter((q) => !coreOnly || q.core);
    if (!items.length) return "";
    return `<h2>${esc(sec.title)}</h2>${sec.hint ? `<p class="hint">${esc(sec.hint)}</p>` : ""}` +
      items.map((q) => {
        const a = ans[q.id] || {};
        const score = q.kind === "score"
          ? `<div class="score">Baho: ${[1, 2, 3, 4, 5].map((n) =>
              `<span class="${a.s === n ? "on" : ""}">${n}</span>`).join("")}</div>`
          : q.kind === "check"
            ? `<div class="score"><span class="${a.ok === true ? "on" : ""}">Ha</span><span class="${a.ok === false ? "on" : ""}">Yo'q</span></div>`
            : "";
        const answer = a.a
          ? `<div class="ans">${esc(a.a).replace(/\n/g, "<br>")}</div>`
          : `<div class="lines">${"<div></div>".repeat(q.kind === "check" ? 1 : 3)}</div>`;
        return `<div class="q"><p class="t"><b>${qNo(q.id)}.</b> ${esc(q.text)}${q.core ? ' <i>(asosiy)</i>' : ""}${q.only ? ` <i>[${esc(q.only)}]</i>` : ""}</p>` +
          (q.good || q.bad
            ? `<p class="gb">${q.good ? "✅ " + esc(q.good) : ""}${q.good && q.bad ? "<br>" : ""}${q.bad ? "❌ " + esc(q.bad) : ""}</p>`
            : "") +
          answer + score + "</div>";
      }).join("");
  }).join("");
  const rec = sheet?.recommendation_label;
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>Suhbat varaqasi — ${esc(name)}</title>
<style>
body{font:12px/1.45 Arial,sans-serif;color:#111;margin:24px}
h1{font-size:18px;margin:0}h2{font-size:14px;margin:18px 0 4px;border-bottom:1px solid #999;padding-bottom:2px}
.meta{color:#555;margin:4px 0 10px}.hint{color:#555;font-size:11px;margin:2px 0 6px}
.q{break-inside:avoid;margin:8px 0 10px}.t{margin:0 0 2px}.gb{color:#555;font-size:10.5px;margin:0 0 4px}
.lines div{border-bottom:1px dotted #999;height:20px}.ans{border:1px solid #ccc;border-radius:4px;padding:4px 6px}
.score{margin-top:4px;font-size:11px}.score span{display:inline-block;min-width:18px;text-align:center;border:1px solid #999;border-radius:3px;margin-left:4px;padding:0 3px}
.score span.on{background:#111;color:#fff}.sum div{border-bottom:1px dotted #999;height:20px}
</style></head><body>
<h1>Suhbat varaqasi</h1>
<p class="meta">Nomzod: <b>${esc(name)}</b> · Sana: ${today}${sheet?.author ? ` · Suhbatdosh: ${esc(sheet.author)}` : " · Suhbatdosh: ____________"}${sheet?.percent != null ? ` · Ball: ${sheet.percent}%` : ""}</p>
${body}
<h2>Xulosa</h2>
<p>Tavsiya: ${rec ? `<b>${esc(rec)}</b>` : g.recommendations.map((r) => "☐ " + esc(r.label)).join("&nbsp;&nbsp; ")}</p>
<p><b>Kuchli tomonlari:</b></p>${sheet?.strengths ? `<div class="ans">${esc(sheet.strengths)}</div>` : '<div class="sum"><div></div><div></div></div>'}
<p><b>Xavotirlar:</b></p>${sheet?.concerns ? `<div class="ans">${esc(sheet.concerns)}</div>` : '<div class="sum"><div></div><div></div></div>'}
<p><b>Izoh:</b></p>${sheet?.note ? `<div class="ans">${esc(sheet.note)}</div>` : '<div class="sum"><div></div><div></div></div>'}
<script>window.onload=function(){window.print()}</script>
</body></html>`;
  const w = window.open("", "_blank");
  if (!w) return;
  w.document.open();
  w.document.write(html);
  w.document.close();
}
