import { useEffect, useState } from "react";
import {
  X, Plus, Trash2, ChevronUp, ChevronDown, Loader2, RotateCcw, Printer,
} from "lucide-react";
import { api } from "../lib/api";
import type { Guide, GuideQ, Section } from "./InterviewSheet";
import { printSheet } from "./InterviewSheet";

/**
 * SUHBAT SAVOLLARINI TAHRIRLASH (2026-10-08, Jahongir: savollarni HR
 * o'zi o'zgartira olsin, baholashi bilan).
 *
 * Har savolda: matn, maqsad, nimaga e'tibor berish, yaxshi/yomon javob
 * belgisi, baholash turi (1-5 ball / ha-yo'q / faqat javob), "asosiy"
 * belgisi. O'chirilgan savolning eski javoblari yo'qolmaydi — savol
 * qaytarilsa yana ko'rinadi.
 */

const KIND_LABEL: Record<GuideQ["kind"], string> = {
  score: "1-5 ball",
  check: "Ha / Yo'q (kuzatuv)",
  note: "Faqat javob (ballsiz)",
};

const blankQ = (): GuideQ => ({
  id: "", text: "", why: "", look: "", good: "", bad: "",
  kind: "score", core: false, only: null,
});

function move<T>(arr: T[], i: number, d: number): T[] {
  const j = i + d;
  if (j < 0 || j >= arr.length) return arr;
  const next = [...arr];
  [next[i], next[j]] = [next[j], next[i]];
  return next;
}

export function InterviewGuideEditor({ onClose, onSaved }: {
  onClose: () => void;
  onSaved?: () => void;
}) {
  const [guide, setGuide] = useState<Guide | null>(null);
  const [secs, setSecs] = useState<Section[]>([]);
  const [open, setOpen] = useState<string | null>(null);   // "si:qi"
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [dirty, setDirty] = useState(false);

  const load = () =>
    api.get<Guide>("/hr/interview-guide", true).then((g) => {
      setGuide(g);
      setSecs(JSON.parse(JSON.stringify(g.sections)));
      setDirty(false);
    }).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);

  const edit = (fn: (s: Section[]) => Section[]) => {
    setSecs((prev) => fn(prev));
    setDirty(true);
  };
  const setSec = (si: number, patch: Partial<Section>) =>
    edit((s) => s.map((x, i) => (i === si ? { ...x, ...patch } : x)));
  const setQ = (si: number, qi: number, patch: Partial<GuideQ>) =>
    edit((s) => s.map((x, i) => i !== si ? x : {
      ...x, items: x.items.map((q, j) => (j === qi ? { ...q, ...patch } : q)),
    }));

  const save = async () => {
    setBusy(true); setErr("");
    try {
      const g = await api.put<Guide>("/hr/interview-guide", { sections: secs });
      setGuide(g);
      setSecs(JSON.parse(JSON.stringify(g.sections)));
      setDirty(false);
      onSaved?.();
    } catch (e) {
      setErr((e as Error).message || "Saqlanmadi");
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    if (!confirm("Savollar standart ro'yxatga qaytariladi. Siz kiritgan "
      + "o'zgarishlar o'chadi (nomzodlarning javoblari saqlanib qoladi). Davom etamizmi?")) return;
    setBusy(true);
    try {
      const g = await api.post<Guide>("/hr/interview-guide/reset");
      setGuide(g);
      setSecs(JSON.parse(JSON.stringify(g.sections)));
      setDirty(false);
      onSaved?.();
    } finally {
      setBusy(false);
    }
  };

  const close = () => {
    if (dirty && !confirm("Saqlanmagan o'zgarishlar bor. Chiqib ketamizmi?")) return;
    onClose();
  };

  const total = secs.reduce((n, s) => n + s.items.length, 0);

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex sm:p-4">
      <div className="bg-white w-full max-w-4xl mx-auto sm:rounded-xl overflow-y-auto">
        <div className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 sm:px-6 py-3 flex flex-wrap items-center gap-2">
          <div className="flex-1 min-w-0">
            <h2 className="font-semibold text-slate-900">Suhbat savollari</h2>
            <p className="text-xs text-slate-500">
              {secs.length} bo'lim · {total} savol
              {guide?.customized && guide.updated_by
                ? ` · oxirgi o'zgartirgan: ${guide.updated_by}` : " · standart ro'yxat"}
            </p>
          </div>
          {guide && (
            <button
              onClick={() => printSheet({ ...guide, sections: secs }, "", null)}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50"
              title="Bo'sh blank — qog'ozda suhbat uchun"
            >
              <Printer size={15} /> Bo'sh blank
            </button>
          )}
          {guide?.can_edit && guide.customized && (
            <button
              onClick={reset}
              disabled={busy}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
            >
              <RotateCcw size={14} /> Standartga qaytarish
            </button>
          )}
          {guide?.can_edit && (
            <button
              onClick={save}
              disabled={busy || !dirty}
              className="inline-flex items-center gap-1.5 text-sm px-4 py-1.5 rounded-lg bg-brand-600 text-white disabled:opacity-50"
            >
              {busy && <Loader2 size={14} className="animate-spin" />}
              Saqlash
            </button>
          )}
          <button onClick={close} className="p-1.5 text-slate-400 hover:text-slate-700">
            <X size={20} />
          </button>
        </div>

        {err && <p className="mx-6 mt-3 text-sm text-red-600">{err}</p>}
        {!guide ? (
          <div className="p-10 flex justify-center text-slate-400"><Loader2 className="animate-spin" /></div>
        ) : (
          <div className="px-4 sm:px-6 py-5 space-y-5 bg-slate-50">
            {!guide.can_edit && (
              <p className="text-sm text-amber-800 bg-amber-50 rounded-lg px-3 py-2">
                Savollarni faqat HR o'zgartira oladi — siz faqat ko'rasiz.
              </p>
            )}
            {secs.map((sec, si) => (
              <section key={sec.key || si} className="bg-white rounded-xl border border-slate-200 p-3.5 sm:p-4">
                <div className="flex items-start gap-2">
                  <div className="flex-1 space-y-1.5">
                    <input
                      value={sec.title}
                      disabled={!guide.can_edit}
                      onChange={(e) => setSec(si, { title: e.target.value })}
                      placeholder="Bo'lim nomi"
                      className="w-full font-semibold text-slate-800 px-2 py-1 rounded border border-transparent hover:border-slate-200 focus:border-brand-300 outline-none"
                    />
                    <textarea
                      value={sec.hint}
                      rows={1}
                      disabled={!guide.can_edit}
                      onChange={(e) => setSec(si, { hint: e.target.value })}
                      placeholder="Bo'lim uchun yo'riqnoma (ixtiyoriy)"
                      className="w-full text-xs text-slate-600 px-2 py-1 rounded border border-transparent hover:border-slate-200 focus:border-brand-300 outline-none resize-y"
                    />
                  </div>
                  {guide.can_edit && (
                    <Tools
                      onUp={() => edit((s) => move(s, si, -1))}
                      onDown={() => edit((s) => move(s, si, 1))}
                      onDel={() => {
                        if (sec.items.length && !confirm(`"${sec.title}" bo'limi va undagi ${sec.items.length} ta savol o'chirilsinmi?`)) return;
                        edit((s) => s.filter((_, i) => i !== si));
                      }}
                    />
                  )}
                </div>

                <div className="mt-2 space-y-1.5">
                  {sec.items.map((q, qi) => {
                    const k = `${si}:${qi}`;
                    const isOpen = open === k;
                    return (
                      <div key={q.id || k} className="rounded-lg border border-slate-200">
                        <div className="flex items-start gap-2 px-2.5 py-2">
                          <button
                            onClick={() => setOpen(isOpen ? null : k)}
                            className="flex-1 text-left text-sm text-slate-800"
                          >
                            {q.text || <span className="text-slate-400">Yangi savol — matnini yozing</span>}
                            <span className="ml-2 text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 align-middle">
                              {KIND_LABEL[q.kind]}
                            </span>
                            {q.core && (
                              <span className="ml-1 text-[10px] font-semibold px-1.5 py-0.5 rounded bg-brand-50 text-brand-700 align-middle">ASOSIY</span>
                            )}
                          </button>
                          {guide.can_edit && (
                            <Tools
                              onUp={() => setSec(si, { items: move(sec.items, qi, -1) })}
                              onDown={() => setSec(si, { items: move(sec.items, qi, 1) })}
                              onDel={() => setSec(si, { items: sec.items.filter((_, j) => j !== qi) })}
                            />
                          )}
                        </div>
                        {isOpen && (
                          <div className="border-t border-slate-100 px-2.5 py-2.5 grid gap-2 text-sm">
                            <Field label="Savol" value={q.text} rows={2} disabled={!guide.can_edit}
                              onChange={(v) => setQ(si, qi, { text: v })} />
                            <div className="flex flex-wrap gap-3 items-center">
                              <label className="text-xs text-slate-500">
                                Baholash:{" "}
                                <select
                                  value={q.kind}
                                  disabled={!guide.can_edit}
                                  onChange={(e) => setQ(si, qi, { kind: e.target.value as GuideQ["kind"] })}
                                  className="ml-1 px-2 py-1 rounded border border-slate-200 text-sm"
                                >
                                  {(Object.keys(KIND_LABEL) as GuideQ["kind"][]).map((x) => (
                                    <option key={x} value={x}>{KIND_LABEL[x]}</option>
                                  ))}
                                </select>
                              </label>
                              <label className="text-xs text-slate-600 inline-flex items-center gap-1.5">
                                <input type="checkbox" checked={q.core} disabled={!guide.can_edit}
                                  onChange={(e) => setQ(si, qi, { core: e.target.checked })} />
                                Asosiy savol (vaqt kam bo'lsa ham beriladi)
                              </label>
                              <label className="text-xs text-slate-500">
                                Faqat lavozim uchun:{" "}
                                <input
                                  value={q.only || ""}
                                  disabled={!guide.can_edit}
                                  onChange={(e) => setQ(si, qi, { only: e.target.value || null })}
                                  placeholder="masalan: Sotuv"
                                  className="ml-1 w-36 px-2 py-1 rounded border border-slate-200 text-sm"
                                />
                              </label>
                            </div>
                            <Field label="Maqsad — nima uchun so'raladi" value={q.why} disabled={!guide.can_edit}
                              onChange={(v) => setQ(si, qi, { why: v })} />
                            <Field label="Nimaga e'tibor berish kerak" value={q.look} disabled={!guide.can_edit}
                              onChange={(v) => setQ(si, qi, { look: v })} />
                            <div className="grid sm:grid-cols-2 gap-2">
                              <Field label="✅ Yaxshi javob belgisi (5 ball)" value={q.good} disabled={!guide.can_edit}
                                onChange={(v) => setQ(si, qi, { good: v })} />
                              <Field label="❌ Yomon javob belgisi (1-2 ball)" value={q.bad} disabled={!guide.can_edit}
                                onChange={(v) => setQ(si, qi, { bad: v })} />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                {guide.can_edit && (
                  <button
                    onClick={() => {
                      setSec(si, { items: [...sec.items, blankQ()] });
                      setOpen(`${si}:${sec.items.length}`);
                    }}
                    className="mt-2 inline-flex items-center gap-1 text-sm text-brand-700 hover:underline"
                  >
                    <Plus size={14} /> Savol qo'shish
                  </button>
                )}
              </section>
            ))}
            {guide.can_edit && (
              <button
                onClick={() => edit((s) => [...s, { key: "", title: "Yangi bo'lim", hint: "", items: [blankQ()] }])}
                className="w-full py-2.5 rounded-xl border-2 border-dashed border-slate-300 text-sm text-slate-600 hover:bg-white"
              >
                <Plus size={14} className="inline -mt-0.5" /> Bo'lim qo'shish
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Tools({ onUp, onDown, onDel }: { onUp: () => void; onDown: () => void; onDel: () => void }) {
  return (
    <div className="flex shrink-0 text-slate-400">
      <button onClick={onUp} className="p-1 hover:text-slate-700" title="Yuqoriga"><ChevronUp size={16} /></button>
      <button onClick={onDown} className="p-1 hover:text-slate-700" title="Pastga"><ChevronDown size={16} /></button>
      <button onClick={onDel} className="p-1 hover:text-red-600" title="O'chirish"><Trash2 size={15} /></button>
    </div>
  );
}

function Field({ label, value, onChange, rows = 1, disabled }: {
  label: string; value: string; onChange: (v: string) => void; rows?: number; disabled?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-xs text-slate-500">{label}</span>
      <textarea
        rows={rows}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="mt-0.5 w-full px-2.5 py-1.5 rounded-lg border border-slate-200 text-sm resize-y"
      />
    </label>
  );
}
