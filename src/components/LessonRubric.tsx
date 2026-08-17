import { useEffect, useState } from "react";
import { ClipboardCheck, X, Info, Pencil, Check, FileSpreadsheet} from "lucide-react";
import {
  api, type RubricList, type RubricRow, type ObservationRow,
  type Teacher,
} from "../lib/api";
import { formatDate } from "../lib/format";
import { exportSheetsToExcel } from "../lib/exportXlsx";

const TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
};

/**
 * Dars baholash varaqasi.
 *
 * Baholovchi faqat "Fakt" ustunini to'ldiradi — jami va foiz o'zi
 * hisoblanadi va serverda qayta tekshiriladi. Mezon balidan ortiq
 * ball qo'yib bo'lmaydi.
 */
export function ObservationForm({
  rubricKey,
  teacherId,
  candidateId,
  onClose,
  onSaved,
}: {
  rubricKey?: string;
  teacherId?: number;
  candidateId?: number;
  onClose: () => void;
  onSaved?: () => void;
}) {
  const [d, setD] = useState<RubricList | null>(null);
  const [key, setKey] = useState(rubricKey || "main_lesson");
  const [facts, setFacts] = useState<Record<number, number>>({});
  const [strengths, setStrengths] = useState("");
  const [weaknesses, setWeaknesses] = useState("");
  const [note, setNote] = useState("");
  const [day, setDay] = useState(new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<{
    total: number; percent: number; band_label: string; passed: boolean;
  } | null>(null);

  useEffect(() => {
    api.get<RubricList>("/rubrics").then(setD);
  }, []);

  if (!d)
    return (
      <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8">
          <p className="text-sm text-slate-400">Yuklanmoqda...</p>
        </div>
      </div>
    );

  const rubric = d.rows.find((r) => r.key === key) as RubricRow;
  const total = rubric.criteria.reduce(
    (s, c) => s + (facts[c.id] ?? 0),
    0
  );
  const percent = rubric.max_total
    ? Math.round((total / rubric.max_total) * 1000) / 10
    : 0;
  const band =
    percent >= 85
      ? { label: "A'lo", tone: "emerald" }
      : percent >= 70
        ? { label: "Yaxshi", tone: "teal" }
        : percent >= d.pass_score
          ? { label: "O'tdi", tone: "amber" }
          : { label: "Yetarli emas", tone: "red" };

  function setAll(ratio: number) {
    const next: Record<number, number> = {};
    rubric.criteria.forEach((c) => {
      next[c.id] = Math.round(c.points * ratio * 10) / 10;
    });
    setFacts(next);
  }

  async function save() {
    setSaving(true);
    setErr("");
    try {
      const r = await api.post<{
        total: number; percent: number; band_label: string; passed: boolean;
      }>("/observations", {
        rubric_key: key,
        target_type: candidateId ? "candidate" : "teacher",
        teacher_id: teacherId,
        candidate_id: candidateId,
        date: day,
        strengths: strengths || undefined,
        weaknesses: weaknesses || undefined,
        note: note || undefined,
        scores: rubric.criteria.map((c) => ({
          criterion_id: c.id,
          fact: facts[c.id] ?? 0,
        })),
      });
      setDone(r);
      onSaved?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  if (done)
    return (
      <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
        <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 text-center">
          <div
            className={`w-16 h-16 rounded-full mx-auto flex items-center justify-center text-2xl font-semibold mb-3 ${
              TONE[
                done.percent >= 85
                  ? "emerald"
                  : done.percent >= 70
                    ? "teal"
                    : done.passed
                      ? "amber"
                      : "red"
              ]
            }`}
          >
            {done.percent}
          </div>
          <p className="text-lg font-semibold text-slate-900">
            {done.total} / {rubric.max_total} ball
          </p>
          <p className="text-sm text-slate-500 mb-1">{done.band_label}</p>
          <p className="text-xs text-slate-400 mb-4">
            {done.passed
              ? "Natija saqlandi va ustozning mahorat balliga tushdi."
              : `O'tish uchun ${d.pass_score} ball kerak edi.`}
          </p>
          <button
            onClick={onClose}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium"
          >
            Yopish
          </button>
        </div>
      </div>
    );

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-start justify-center z-50 px-4 py-6 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl">
        {/* Sarlavha */}
        <div className="flex items-start justify-between p-5 border-b border-slate-100 sticky top-0 bg-white rounded-t-xl z-10">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <ClipboardCheck size={16} className="text-slate-400" />
              <h2 className="font-semibold text-slate-900">Dars baholash</h2>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {d.rows.map((r) => (
                <button
                  key={r.key}
                  onClick={() => {
                    setKey(r.key);
                    setFacts({});
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                    key === r.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {r.name}
                </button>
              ))}
            </div>
          </div>
          <div className="text-right ml-4">
            <p className="text-2xl font-semibold text-slate-900">
              {Math.round(total * 10) / 10}
              <span className="text-sm font-normal text-slate-400">
                {" "}
                / {rubric.max_total}
              </span>
            </p>
            <span
              className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                TONE[band.tone]
              }`}
            >
              {percent}% · {band.label}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 ml-3"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-5">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <input
              type="date"
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
              value={day}
              onChange={(e) => setDay(e.target.value)}
            />
            <span className="text-xs text-slate-400">Tez to'ldirish:</span>
            {[
              [1, "To'liq"],
              [0.75, "75%"],
              [0.5, "Yarim"],
              [0, "Tozalash"],
            ].map(([r, l]) => (
              <button
                key={String(l)}
                onClick={() => setAll(r as number)}
                className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-brand-300"
              >
                {l}
              </button>
            ))}
          </div>

          {/* Mezonlar */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <div className="grid grid-cols-[36px_1fr_60px_84px] bg-slate-50 text-xs text-slate-500 px-3 py-2">
              <span>№</span>
              <span>Mezon</span>
              <span className="text-right">Ball</span>
              <span className="text-right pr-1">Fakt</span>
            </div>
            {rubric.criteria.map((c) => {
              const v = facts[c.id] ?? 0;
              const full = v >= c.points;
              return (
                <div
                  key={c.id}
                  className={`grid grid-cols-[36px_1fr_60px_84px] items-center px-3 py-2 border-t border-slate-100 ${
                    full ? "bg-emerald-50/50" : ""
                  }`}
                >
                  <span className="text-xs text-slate-400">{c.no}</span>
                  <span className="text-sm text-slate-700 pr-3">{c.text}</span>
                  <span className="text-sm text-slate-500 text-right">
                    {c.points}
                  </span>
                  <div className="flex items-center gap-1 justify-end">
                    <button
                      onClick={() =>
                        setFacts({ ...facts, [c.id]: full ? 0 : c.points })
                      }
                      title={full ? "Olib tashlash" : "To'liq ball"}
                      className={`w-6 h-6 rounded-md border flex items-center justify-center shrink-0 ${
                        full
                          ? "bg-emerald-500 border-emerald-500 text-white"
                          : "border-slate-200 text-slate-300 hover:border-emerald-400"
                      }`}
                    >
                      <Check size={13} />
                    </button>
                    <input
                      type="number"
                      min={0}
                      max={c.points}
                      step={0.5}
                      className="w-12 rounded-md border border-slate-300 px-1.5 py-1 text-sm text-right"
                      value={v || ""}
                      onChange={(e) => {
                        const n = Math.max(
                          0,
                          Math.min(Number(e.target.value) || 0, c.points)
                        );
                        setFacts({ ...facts, [c.id]: n });
                      }}
                    />
                  </div>
                </div>
              );
            })}
            <div className="grid grid-cols-[36px_1fr_60px_84px] items-center px-3 py-2.5 bg-slate-50 border-t border-slate-200 font-medium">
              <span />
              <span className="text-sm text-slate-800">Jami</span>
              <span className="text-sm text-slate-600 text-right">
                {rubric.max_total}
              </span>
              <span className="text-sm text-slate-900 text-right pr-1">
                {Math.round(total * 10) / 10}
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-3 mt-4">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Kuchli tomonlari
              </label>
              <textarea
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm h-20"
                value={strengths}
                onChange={(e) => setStrengths(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Ustida ishlash kerak
              </label>
              <textarea
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm h-20"
                value={weaknesses}
                onChange={(e) => setWeaknesses(e.target.value)}
              />
            </div>
          </div>
          <div className="mt-3">
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Izoh
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          {err && <p className="text-sm text-red-600 mt-3">{err}</p>}
          <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
            <Info size={11} className="mt-0.5 shrink-0" />
            {d.hint}
          </p>

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-4 disabled:opacity-60"
          >
            {saving
              ? "Saqlanmoqda..."
              : `Saqlash — ${Math.round(total * 10) / 10} ball (${percent}%)`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ================================================ Baholashlar ro'yxati
export function ObservationList({
  teacherId,
  candidateId,
  canAdd = false,
}: {
  teacherId?: number;
  candidateId?: number;
  canAdd?: boolean;
}) {
  const [rows, setRows] = useState<ObservationRow[]>([]);
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<ObservationRow | null>(null);
  const [xls, setXls] = useState(false);

  function load() {
    const q = teacherId
      ? `teacher_id=${teacherId}`
      : `candidate_id=${candidateId}`;
    api
      .get<{ rows: ObservationRow[] }>(`/observations?${q}`)
      .then((d) => setRows(d.rows))
      .catch(() => setRows([]));
  }
  useEffect(load, [teacherId, candidateId]);

  async function openDetail(id: number) {
    setDetail(await api.get<ObservationRow>(`/observations/${id}`));
  }

  /**
   * BAHOLASHNI EXCELGA CHIQARISH (2026-08-16).
   *
   * Jahongir: "daras baholagandan keyin jadval qilib excell qilish
   * mumkin bo'lsin ustozga tashlab berishga oson bo'ladi".
   *
   * Har baholash ALOHIDA varaq bo'ladi: mezonlar, maksimal ball,
   * qo'yilgan ball va izoh. Oxirida jami natija, sana, baholovchi,
   * kuchli va zaif tomonlar. Shu holida ustozga yuborsa bo'ladi.
   */
  async function toExcel() {
    if (rows.length === 0) return;
    setXls(true);
    try {
      const full = await Promise.all(
        rows.map((o) => api.get<ObservationRow>(`/observations/${o.id}`))
      );
      const sheets = full.map((o, i) => {
        const body: Record<string, unknown>[] = (o.scores || []).map((c) => ({
          "\u2116": c.no,
          Mezon: c.text,
          "Maksimal ball": c.points,
          "Qo'yilgan ball": c.fact,
          Izoh: c.note || "",
        }));
        const line = (m: string, izoh: unknown) =>
          body.push({ "\u2116": "", Mezon: m, "Maksimal ball": "",
                      "Qo'yilgan ball": "", Izoh: izoh ?? "" });
        body.push({ "\u2116": "", Mezon: "", "Maksimal ball": "",
                    "Qo'yilgan ball": "", Izoh: "" });
        body.push({ "\u2116": "", Mezon: "JAMI",
                    "Maksimal ball": o.max_total,
                    "Qo'yilgan ball": o.total,
                    Izoh: `${o.percent}% \u2014 ${o.band_label}` });
        line("Sana", o.date);
        line("Baholadi", o.observer);
        line("Kuchli tomonlari", o.strengths);
        line("Rivojlantirish kerak", o.weaknesses);
        if (o.note) line("Izoh", o.note);
        const nm = `${i + 1}-baholash ${o.date || ""}`.trim();
        return { name: nm.slice(0, 31), rows: body };
      });
      const who = full[0]?.teacher || "nomzod";
      exportSheetsToExcel(`Dars baholash - ${who}`, sheets);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Excelga chiqarib bo'lmadi");
    } finally {
      setXls(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-3">
        {canAdd && (
          <button
            onClick={() => setOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            <ClipboardCheck size={15} /> Dars baholash
          </button>
        )}
        {rows.length > 0 && (
          <button
            onClick={toExcel}
            disabled={xls}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-emerald-300 text-emerald-700 bg-white text-sm font-medium hover:bg-emerald-50 disabled:opacity-60"
          >
            <FileSpreadsheet size={15} />
            {xls ? "Tayyorlanmoqda\u2026" : "Excelga yuklash"}
          </button>
        )}
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hali baholanmagan.
        </p>
      ) : (
        <div className="space-y-2">
          {rows.map((o) => (
            <button
              key={o.id}
              onClick={() => openDetail(o.id)}
              className="w-full text-left flex flex-wrap items-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white hover:border-brand-300 transition"
            >
              <span
                className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-semibold shrink-0 ${
                  TONE[o.tone] || TONE.amber
                }`}
              >
                {o.percent}
              </span>
              <div className="flex-1 min-w-[140px]">
                <p className="text-sm font-medium text-slate-800">
                  {o.rubric}
                </p>
                <p className="text-xs text-slate-400">
                  {o.date ? formatDate(o.date) : "—"} ·{" "}
                  {o.observer || "—"}
                </p>
              </div>
              <span className="text-sm text-slate-600">
                {o.total} / {o.max_total}
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  TONE[o.tone] || TONE.amber
                }`}
              >
                {o.band_label}
              </span>
            </button>
          ))}
        </div>
      )}

      {open && (
        <ObservationForm
          teacherId={teacherId}
          candidateId={candidateId}
          onClose={() => setOpen(false)}
          onSaved={load}
        />
      )}
      {detail && (
        <DetailModal row={detail} onClose={() => setDetail(null)} />
      )}
    </div>
  );
}

function DetailModal({
  row,
  onClose,
}: {
  row: ObservationRow;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-start justify-center z-50 px-4 py-6 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl">
        <div className="flex items-start justify-between p-5 border-b border-slate-100">
          <div>
            <h2 className="font-semibold text-slate-900">{row.rubric}</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {row.date ? formatDate(row.date) : "—"} · {row.observer}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xl font-semibold text-slate-900">
              {row.total} / {row.max_total}
            </p>
            <span
              className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                TONE[row.tone] || TONE.amber
              }`}
            >
              {row.percent}% · {row.band_label}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 ml-3"
          >
            <X size={18} />
          </button>
        </div>
        <div className="p-5">
          <div className="border border-slate-100 rounded-xl overflow-hidden">
            {(row.scores || []).map((s) => (
              <div
                key={s.criterion_id}
                className={`grid grid-cols-[32px_1fr_50px_50px] items-center px-3 py-2 border-b border-slate-50 text-sm ${
                  s.fact >= s.points ? "bg-emerald-50/50" : ""
                }`}
              >
                <span className="text-xs text-slate-400">{s.no}</span>
                <span className="text-slate-700 pr-2">{s.text}</span>
                <span className="text-right text-slate-400 text-xs">
                  {s.points}
                </span>
                <span
                  className={`text-right font-medium ${
                    s.fact >= s.points
                      ? "text-emerald-600"
                      : s.fact === 0
                        ? "text-red-500"
                        : "text-slate-700"
                  }`}
                >
                  {s.fact}
                </span>
              </div>
            ))}
          </div>
          {row.strengths && (
            <p className="text-sm text-slate-600 mt-3">
              <span className="text-xs text-slate-400 block">
                Kuchli tomonlari
              </span>
              {row.strengths}
            </p>
          )}
          {row.weaknesses && (
            <p className="text-sm text-slate-600 mt-2">
              <span className="text-xs text-slate-400 block">
                Ustida ishlash kerak
              </span>
              {row.weaknesses}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// =================================================== Mezonlarni tahrirlash
export function RubricSettings() {
  const [d, setD] = useState<RubricList | null>(null);
  const [key, setKey] = useState("main_lesson");
  const [editing, setEditing] = useState<number | null>(null);
  const [val, setVal] = useState("");

  function load() {
    api.get<RubricList>("/rubrics").then(setD);
  }
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const r = d.rows.find((x) => x.key === key) as RubricRow;

  async function save(cid: number) {
    await api.put(`/rubrics/criteria/${cid}`, { points: Number(val) });
    setEditing(null);
    load();
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {d.rows.map((x) => (
          <button
            key={x.key}
            onClick={() => setKey(x.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              key === x.key
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {x.name}
          </button>
        ))}
        <span className="text-sm text-slate-500">
          {r.criteria.length} mezon · jami {r.max_total} ball
        </span>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {r.criteria.map((c) => (
          <div
            key={c.id}
            className="grid grid-cols-[36px_1fr_100px] items-center px-4 py-2.5 border-b border-slate-50 text-sm"
          >
            <span className="text-xs text-slate-400">{c.no}</span>
            <span className="text-slate-700 pr-3">{c.text}</span>
            <div className="flex items-center justify-end gap-2">
              {editing === c.id ? (
                <>
                  <input
                    className="w-14 rounded-md border border-slate-300 px-2 py-1 text-sm text-right"
                    value={val}
                    onChange={(e) => setVal(e.target.value)}
                    autoFocus
                  />
                  <button
                    onClick={() => save(c.id)}
                    className="text-emerald-600"
                  >
                    <Check size={15} />
                  </button>
                </>
              ) : (
                <>
                  <span className="font-medium text-slate-800">
                    {c.points}
                  </span>
                  {d.can_edit && (
                    <button
                      onClick={() => {
                        setEditing(c.id);
                        setVal(String(c.points));
                      }}
                      className="text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={13} />
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>
    </div>
  );
}

// ============================================= HR: baholash bo'limi
export function ObservationsTab() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [tid, setTid] = useState<number | null>(null);
  const [tab, setTab] = useState<"baholash" | "mezon">("baholash");

  useEffect(() => {
    api
      .get<Teacher[]>("/teachers")
      .then((rows) => {
        const live = rows.filter((t) => t.is_active !== 0);
        setTeachers(live);
        if (live.length) setTid(live[0].id);
      })
      .catch(() => setTeachers([]));
  }, []);

  return (
    <div>
      <div className="flex gap-1 mb-4">
        {(
          [
            ["baholash", "Baholashlar"],
            ["mezon", "Mezonlar"],
          ] as const
        ).map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {tab === "mezon" ? (
        <RubricSettings />
      ) : (
        <div>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white mb-4"
            value={tid ?? ""}
            onChange={(e) => setTid(Number(e.target.value))}
          >
            {teachers.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
          </select>
          {tid && <ObservationList teacherId={tid} canAdd />}
        </div>
      )}
    </div>
  );
}
