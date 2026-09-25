import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, ChevronUp, ChevronDown } from "lucide-react";
import { api } from "../lib/api";
import { SUBJECT_LEVELS, levelLabel } from "../lib/subjects";
import { EXAM_KINDS, UNIT_COUNT, examKindLabel } from "../lib/exams";

/**
 * TEST BAZASI (2026-09-18) — online test (link) savollari.
 *
 * Har test: daraja + tur (Unit / Mid-course / End of course) + unit
 * raqami. Guruh testiga link ochilganda shu yerdan tanlanadi va
 * savollar o'sha paytda nusxalanadi — keyingi tahrir o'tib ketgan
 * testlarga ta'sir qilmaydi. Tahrirlash: asoschi, filial rahbari,
 * examinerlar boshlig'i. Examinerlar ko'radi.
 */

type Q = {
  id?: string;
  n?: number;
  type: "choice" | "text";
  q: string;
  options?: string[];
  answer: number | string[];
  image?: string | null;
  /** Mavzu (#177): "Grammar · Present simple" — tahlil shu bo'yicha */
  topic?: string | null;
};
type TopicRow = { topic: string; count: number };
type Part = {
  title: string;
  instructions: string;
  passage: string;
  audio_url: string | null;
  image?: string | null;
  /** Listening skripti — audio yo'q variantlarda examiner o'qib beradi */
  script?: string;
  questions: Q[];
};
type Tpl = {
  id: number;
  level: string | null;
  kind: string;
  unit_no: number | null;
  title: string;
  q_count: number;
  paper_max: number;
  is_active: boolean;
  /** A (asl), B, C, D, E (2026-09-26) */
  variant?: string;
  parts?: Part[];
};

const LEVELS = (() => {
  const seen = new Set<string>();
  const out: { key: string; label: string }[] = [];
  for (const ls of Object.values(SUBJECT_LEVELS))
    for (const l of ls) if (!seen.has(l.key)) { seen.add(l.key); out.push(l); }
  return out;
})();
const ONLINE_KINDS = EXAM_KINDS.filter((k) => k.key !== "mock");
const LETTERS = "ABCDEFGH";
const inp = "w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm";

/** Savol rasmi: 480px gacha kichraytirib JPEG (data URL) qiladi. */
function imageToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, 480 / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * k);
      c.height = Math.round(img.height * k);
      const ctx = c.getContext("2d")!;
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      resolve(c.toDataURL("image/jpeg", 0.82));
    };
    img.onerror = () => reject(new Error("Rasmni o'qib bo'lmadi"));
    img.src = url;
  });
}

function blankPart(i: number): Part {
  return { title: `Part ${i}`, instructions: "", passage: "", audio_url: null, questions: [] };
}

export function ExamBankTab({ canEdit }: { canEdit: boolean }) {
  const [rows, setRows] = useState<Tpl[]>([]);
  const [loading, setLoading] = useState(true);
  const [edit, setEdit] = useState<Tpl | null>(null);

  function load() {
    setLoading(true);
    api.fresh<Tpl[]>("/exam-templates").then(setRows).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function open(t: Tpl | null) {
    if (!t) {
      setEdit({
        id: 0, level: "step1", kind: "unit", unit_no: 1, title: "",
        q_count: 0, paper_max: 0, is_active: true, parts: [blankPart(1)],
      });
      return;
    }
    setEdit(await api.fresh<Tpl>(`/exam-templates/${t.id}`));
  }

  async function remove(t: Tpl) {
    if (!confirm(`"${t.title}" o'chirilsinmi?`)) return;
    const r = await api.delete<{ hidden: boolean }>(`/exam-templates/${t.id}`);
    if (r.hidden) alert("Bu test guruhlarda ishlatilgan — o'chirilmadi, yashirildi.");
    load();
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-500">
          Online test savollari. Guruh testiga link ochilganda shu yerdan
          tanlanadi.
        </p>
        {canEdit && (
          <button
            onClick={() => open(null)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
          >
            <Plus size={16} /> Yangi test
          </button>
        )}
      </div>
      {loading ? (
        <p className="text-sm text-slate-400">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">Test bazasi bo'sh</p>
      ) : (
        <div className="border border-slate-200 rounded-xl bg-white overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Test</th>
                <th className="text-left px-4 py-3 font-medium">Daraja</th>
                <th className="text-left px-4 py-3 font-medium">Turi</th>
                <th className="text-right px-4 py-3 font-medium">Savol</th>
                <th className="text-right px-4 py-3 font-medium">Qog'oz</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => open(t)}
                  className={`border-t border-slate-100 hover:bg-slate-50 cursor-pointer ${
                    t.is_active ? "" : "opacity-50"
                  }`}
                >
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {/* Variant belgisi (2026-09-26): A asl, B–E parallel */}
                    <span className={`inline-block w-6 text-center rounded text-[11px] font-bold mr-2 ${
                      (t.variant || "A") === "A" ? "bg-slate-100 text-slate-600" : "bg-violet-100 text-violet-700"
                    }`}>{t.variant || "A"}</span>
                    {t.title}
                    {!t.is_active && <span className="ml-2 text-xs text-slate-400">yashirin</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{levelLabel(t.level) || "—"}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {examKindLabel(t.kind)}
                    {t.unit_no ? ` ${t.unit_no}` : ""}
                  </td>
                  <td className="px-4 py-3 text-right">{t.q_count}</td>
                  <td className="px-4 py-3 text-right">{t.paper_max || "—"}</td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {canEdit && (
                      <span className="inline-flex gap-3">
                        <Pencil size={15} className="text-slate-300 hover:text-brand-600" />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            remove(t);
                          }}
                          className="text-slate-300 hover:text-red-500"
                        >
                          <Trash2 size={15} />
                        </button>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {edit && (
        <TemplateEditor
          tpl={edit}
          readOnly={!canEdit}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function TemplateEditor({
  tpl,
  readOnly,
  onClose,
  onSaved,
}: {
  tpl: Tpl;
  readOnly: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState<Tpl>(tpl);
  const [parts, setParts] = useState<Part[]>(
    (tpl.parts || []).map((p) => ({
      ...p,
      questions: p.questions.map((q) => ({ ...q })),
    }))
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Mavzular ro'yxati (#177) — tanlagich uchun; yangi mavzuni ham yozsa bo'ladi
  const [topics, setTopics] = useState<TopicRow[]>([]);
  useEffect(() => {
    api.get<TopicRow[]>("/exam-templates/topics").then(setTopics).catch(() => setTopics([]));
  }, []);
  const untagged = parts.reduce(
    (a, p) => a + p.questions.filter((q) => !(q.topic || "").trim()).length, 0);

  const setPart = (i: number, patch: Partial<Part>) =>
    setParts(parts.map((p, j) => (j === i ? { ...p, ...patch } : p)));
  const setQ = (pi: number, qi: number, patch: Partial<Q>) =>
    setPart(pi, {
      questions: parts[pi].questions.map((q, j) => (j === qi ? { ...q, ...patch } : q)),
    });
  const move = <T,>(arr: T[], i: number, d: number) => {
    const j = i + d;
    if (j < 0 || j >= arr.length) return arr;
    const c = [...arr];
    [c[i], c[j]] = [c[j], c[i]];
    return c;
  };

  let n = 0;

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const body = {
        level: f.level || null,
        kind: f.kind,
        unit_no: f.kind === "unit" ? f.unit_no : null,
        title: f.title,
        paper_max: Number(f.paper_max || 0),
        is_active: f.is_active,
        variant: f.variant || "A",
        parts,
      };
      if (f.id) await api.put(`/exam-templates/${f.id}`, body);
      else await api.post("/exam-templates", body);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 overflow-y-auto">
      <div className="bg-white max-w-3xl mx-auto my-6 rounded-xl shadow-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {f.id ? (readOnly ? f.title : "Testni tahrirlash") : "Yangi test"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <fieldset disabled={readOnly} className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <label className="col-span-2 text-xs text-slate-500">
              Nomi
              <input className={inp} value={f.title}
                     onChange={(e) => setF({ ...f, title: e.target.value })}
                     placeholder="Step 1 · Unit 1 Progress Test" />
            </label>
            <label className="text-xs text-slate-500">
              Daraja
              <select className={inp + " bg-white"} value={f.level || ""}
                      onChange={(e) => setF({ ...f, level: e.target.value || null })}>
                <option value="">—</option>
                {LEVELS.map((l) => (
                  <option key={l.key} value={l.key}>{l.label}</option>
                ))}
              </select>
            </label>
            <label className="text-xs text-slate-500">
              Writing + Speaking max
              <input type="number" min={0} className={inp} value={f.paper_max}
                     onChange={(e) => setF({ ...f, paper_max: Number(e.target.value) })} />
            </label>
            <label className="text-xs text-slate-500">
              Turi
              <select className={inp + " bg-white"} value={f.kind}
                      onChange={(e) => setF({ ...f, kind: e.target.value })}>
                {ONLINE_KINDS.map((k) => (
                  <option key={k.key} value={k.key}>{k.label}</option>
                ))}
              </select>
            </label>
            {f.kind === "unit" && (
              <label className="text-xs text-slate-500">
                Unit
                <select className={inp + " bg-white"} value={f.unit_no ?? 1}
                        onChange={(e) => setF({ ...f, unit_no: Number(e.target.value) })}>
                  {Array.from({ length: UNIT_COUNT }, (_, i) => i + 1).map((u) => (
                    <option key={u} value={u}>Unit {u}</option>
                  ))}
                </select>
              </label>
            )}
            <label className="text-xs text-slate-500">
              Variant
              <select className={inp + " bg-white"} value={f.variant || "A"}
                      title="A — asl; B–E — parallel variantlar (linkda aralashadi)"
                      onChange={(e) => setF({ ...f, variant: e.target.value })}>
                {LETTERS.slice(0, 6).split("").map((v) => (
                  <option key={v} value={v}>{v}{v === "A" ? " (asl)" : ""}</option>
                ))}
              </select>
            </label>
            <label className="text-xs text-slate-500 flex items-end gap-2 pb-2">
              <input type="checkbox" checked={f.is_active}
                     onChange={(e) => setF({ ...f, is_active: e.target.checked })} />
              Faol
            </label>
          </div>

          {parts.map((p, pi) => (
            <div key={pi} className="border border-slate-200 rounded-xl p-3 bg-slate-50/50">
              <div className="flex items-center gap-2 mb-2">
                <input className={inp + " font-medium"} value={p.title}
                       onChange={(e) => setPart(pi, { title: e.target.value })} />
                {!readOnly && (
                  <>
                    <button type="button" title="Yuqoriga" onClick={() => setParts(move(parts, pi, -1))}
                            className="text-slate-400 hover:text-slate-700"><ChevronUp size={16} /></button>
                    <button type="button" title="Pastga" onClick={() => setParts(move(parts, pi, 1))}
                            className="text-slate-400 hover:text-slate-700"><ChevronDown size={16} /></button>
                    <button type="button" title="Bo'limni o'chirish"
                            onClick={() => confirm("Bo'lim o'chirilsinmi?") &&
                              setParts(parts.filter((_, j) => j !== pi))}
                            className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button>
                  </>
                )}
              </div>
              <textarea className={inp} rows={2} placeholder="Ko'rsatma (instruction)"
                        value={p.instructions}
                        onChange={(e) => setPart(pi, { instructions: e.target.value })} />
              <textarea className={inp + " mt-2"} rows={p.passage ? 5 : 1}
                        placeholder="Matn (reading uchun, ixtiyoriy)"
                        value={p.passage}
                        onChange={(e) => setPart(pi, { passage: e.target.value })} />
              <input className={inp + " mt-2"} placeholder="Audio havolasi (listening uchun, ixtiyoriy)"
                     value={p.audio_url || ""}
                     onChange={(e) => setPart(pi, { audio_url: e.target.value || null })} />
              {/* Listening skripti — examiner o'qib beradi; o'quvchiga ko'rinmaydi */}
              {(p.script || /listening/i.test(p.title)) && (
                <textarea className={inp + " mt-2"} rows={p.script ? 4 : 1}
                          placeholder="Listening skripti — examiner o'qib beradigan matn (o'quvchiga ko'rinmaydi)"
                          value={p.script || ""}
                          onChange={(e) => setPart(pi, { script: e.target.value })} />
              )}
              <div className="mt-2 flex items-center gap-2">
                {p.image ? (
                  <>
                    <img src={p.image} alt="" className="h-20 rounded border border-slate-200" />
                    {!readOnly && (
                      <button type="button" onClick={() => setPart(pi, { image: null })}
                              className="text-xs text-slate-400 hover:text-red-500">bo'lim rasmini olib tashlash</button>
                    )}
                  </>
                ) : (
                  !readOnly && (
                    <label className="text-xs text-brand-600 cursor-pointer">
                      + bo'lim rasmi (masalan A–G rasmlar jadvali)
                      <input type="file" accept="image/*" className="hidden"
                             onChange={async (e) => {
                               const file = e.target.files?.[0];
                               if (!file) return;
                               try {
                                 setPart(pi, { image: await imageToDataUrl(file) });
                               } catch (err) {
                                 setError(err instanceof Error ? err.message : "Xatolik");
                               }
                             }} />
                    </label>
                  )
                )}
              </div>

              <div className="mt-3 space-y-3">
                {p.questions.map((q, qi) => {
                  n += 1;
                  return (
                    <div key={qi} className="bg-white border border-slate-200 rounded-lg p-2.5">
                      <div className="flex items-start gap-2">
                        <span className="text-xs font-semibold text-slate-400 pt-2 w-6">{n}.</span>
                        <input className={inp} value={q.q} placeholder="Savol matni"
                               onChange={(e) => setQ(pi, qi, { q: e.target.value })} />
                        <select className="rounded-lg border border-slate-300 px-1.5 py-1.5 text-xs bg-white"
                                value={q.type}
                                onChange={(e) => {
                                  const t = e.target.value as Q["type"];
                                  setQ(pi, qi, t === "choice"
                                    ? { type: t, options: q.options?.length ? q.options : ["", "", ""], answer: 0 }
                                    : { type: t, answer: [] });
                                }}>
                          <option value="choice">Variantli</option>
                          <option value="text">Yozma javob</option>
                        </select>
                        {!readOnly && (
                          <button type="button" title="Savolni o'chirish"
                                  onClick={() => setPart(pi, {
                                    questions: p.questions.filter((_, j) => j !== qi),
                                  })}
                                  className="text-slate-300 hover:text-red-500 pt-1.5"><X size={15} /></button>
                        )}
                      </div>
                      <div className="ml-8 mt-2 flex items-center gap-2 flex-wrap">
                        {/* MAVZU (#177): tahlil "qaysi mavzuda ko'p xato" shu bo'yicha */}
                        <input className={inp + " max-w-xs text-xs" + (!(q.topic || "").trim() ? " border-amber-300" : "")}
                               list="exam-topic-list" value={q.topic || ""}
                               placeholder="Mavzu: Grammar · Present simple"
                               title="Mavzu — ro'yxatdan tanlang yoki yangisini yozing"
                               onChange={(e) => setQ(pi, qi, { topic: e.target.value })} />
                        {q.image ? (
                          <>
                            <img src={q.image} alt="" className="h-16 rounded border border-slate-200" />
                            {!readOnly && (
                              <button type="button" onClick={() => setQ(pi, qi, { image: null })}
                                      className="text-xs text-slate-400 hover:text-red-500">rasmni olib tashlash</button>
                            )}
                          </>
                        ) : (
                          !readOnly && (
                            <label className="text-xs text-brand-600 cursor-pointer">
                              + rasm
                              <input type="file" accept="image/*" className="hidden"
                                     onChange={async (e) => {
                                       const file = e.target.files?.[0];
                                       if (!file) return;
                                       try {
                                         setQ(pi, qi, { image: await imageToDataUrl(file) });
                                       } catch (err) {
                                         setError(err instanceof Error ? err.message : "Xatolik");
                                       }
                                     }} />
                            </label>
                          )
                        )}
                      </div>
                      {q.type === "choice" ? (
                        <div className="ml-8 mt-2 space-y-1.5">
                          {(q.options || []).map((o, oi) => (
                            <div key={oi} className="flex items-center gap-2">
                              <input type="radio" name={`a-${pi}-${qi}`} checked={q.answer === oi}
                                     title="To'g'ri javob"
                                     onChange={() => setQ(pi, qi, { answer: oi })} />
                              <span className="text-xs font-semibold text-slate-500 w-3">{LETTERS[oi]}</span>
                              <input className={inp} value={o}
                                     onChange={(e) => setQ(pi, qi, {
                                       options: (q.options || []).map((x, j) => (j === oi ? e.target.value : x)),
                                     })} />
                              {!readOnly && (q.options || []).length > 2 && (
                                <button type="button" onClick={() => setQ(pi, qi, {
                                  options: (q.options || []).filter((_, j) => j !== oi),
                                  // O'chirilgan variantdan keyingilari bittaga suriladi
                                  answer: typeof q.answer !== "number" ? q.answer
                                    : q.answer === oi ? 0
                                    : q.answer > oi ? q.answer - 1 : q.answer,
                                })} className="text-slate-300 hover:text-red-500"><X size={13} /></button>
                              )}
                            </div>
                          ))}
                          {!readOnly && (q.options || []).length < 8 && (
                            <button type="button"
                                    onClick={() => setQ(pi, qi, { options: [...(q.options || []), ""] })}
                                    className="text-xs text-brand-600 ml-5">+ variant</button>
                          )}
                        </div>
                      ) : (
                        <div className="ml-8 mt-2">
                          <input className={inp}
                                 value={Array.isArray(q.answer) ? q.answer.join(" / ") : ""}
                                 placeholder="To'g'ri javob(lar), / bilan ajrating: China / hina"
                                 onChange={(e) => setQ(pi, qi, {
                                   answer: e.target.value.split("/").map((x) => x.trim()),
                                 })} />
                          <p className="text-[11px] text-slate-400 mt-1">
                            Katta-kichik harf, bo'sh joy va tinish belgilari hisobga olinmaydi.
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              {!readOnly && (
                <div className="flex gap-3 mt-2">
                  <button type="button"
                          onClick={() => setPart(pi, { questions: [...p.questions,
                            { type: "choice", q: "", options: ["", "", ""], answer: 0 }] })}
                          className="text-xs text-brand-600 font-medium">+ variantli savol</button>
                  <button type="button"
                          onClick={() => setPart(pi, { questions: [...p.questions,
                            { type: "text", q: "", answer: [] }] })}
                          className="text-xs text-brand-600 font-medium">+ yozma savol</button>
                </div>
              )}
            </div>
          ))}
          {!readOnly && (
            <button type="button" onClick={() => setParts([...parts, blankPart(parts.length + 1)])}
                    className="text-sm text-brand-600 font-medium">+ Bo'lim qo'shish</button>
          )}
        </fieldset>

        {/* Mavzular tanlagichi — bazadagi barcha mavzular (#177) */}
        <datalist id="exam-topic-list">
          {topics.map((t) => (
            <option key={t.topic} value={t.topic}>{t.count ? `${t.count} ta savolda` : ""}</option>
          ))}
        </datalist>

        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
        <div className="flex items-center justify-between mt-4">
          <span className="text-xs text-slate-500">
            Jami {n} savol (har biri 1 ball)
            {f.paper_max ? ` + qog'oz ${f.paper_max}` : ""}
            {untagged > 0 && (
              <span className="ml-2 text-amber-600" title="Mavzusiz savollar tahlilga tushmaydi">
                · mavzusiz: {untagged}
              </span>
            )}
          </span>
          {!readOnly && (
            <button onClick={save} disabled={saving}
                    className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-5 py-2 text-sm font-medium disabled:opacity-60">
              {saving ? "Saqlanmoqda..." : "Saqlash"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
