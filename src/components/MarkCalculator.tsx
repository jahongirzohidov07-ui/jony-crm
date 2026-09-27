import { useEffect, useMemo, useState } from "react";
import { X, Calculator } from "lucide-react";
import { api } from "../lib/api";

/**
 * BAHOLASH KALKULYATORI (2026-09-27).
 *
 * Jahongir: "Examinerga iloji boricha kam ish qoldir."
 *
 * Writing va Speaking'ni tizim avtomat tekshira olmaydi — lekin
 * examiner YAKUNIY BALLNI o'zi hisoblashi shart emas. U faqat
 * MEZONLAR bo'yicha baho qo'yadi, qolganini tizim rasmiy jadvallar
 * bo'yicha chiqaradi:
 *
 *   IELTS Writing/Speaking  4 mezon x 0-9 -> o'rtacha, IELTS yaxlitlash
 *   CEFR Writing            3 topshiriq (5+6+6=17) -> 0-75 va daraja
 *   CEFR Speaking           8 element (21 xom ball) -> 0-75 va daraja
 *
 * Hisob backendda (api/mock_marking.py) — bu yerda ikkinchi nusxasi
 * yozilmaydi, aks holda ikkovi bir kun bir-biridan chetga chiqadi.
 */

type SchemeBand = { mark: number; level: string };
type SchemeCriterion = {
  name: string;
  max: number;
  step: number;
  /** Har bahoning ma'nosi (CEFR yozma ish): 5 -> "B2 yoki undan yuqori" */
  bands?: SchemeBand[];
};
type Scheme = {
  label: string;
  kind: string;
  criteria: SchemeCriterion[];
  result: string;
  note: string;
};
type Schemes = Record<string, Scheme>;

type ScoreResult = {
  /** IELTS: 0-9 band */
  band?: number;
  mean?: number;
  /** CEFR: 0-75 */
  score?: number | null;
  raw?: number;
  raw_max?: number;
  level?: string | null;
  /** false — rasmiy jadvalda bu nuqta yo'q, raqam taxminiy */
  exact?: boolean;
  note?: string;
};

/**
 * Qaysi sxema kerakligini o'zi topadi: examiner ro'yxatdan
 * qidirmasin. Shablon nomida "Speaking"/"Writing", qog'oz maksimali
 * esa imtihonni ajratadi — IELTS bandi 9, CEFR shkalasi 75.
 */
export function guessScheme(title: string | null, paperMax: number): string {
  const t = (title || "").toLowerCase();
  const cefr = t.includes("cefr") || t.includes("multilevel") || paperMax > 9;
  if (t.includes("speaking")) return cefr ? "cefr_speaking" : "ielts_speaking";
  return cefr ? "cefr_writing" : "ielts_writing";
}

function stepValues(c: SchemeCriterion): number[] {
  const out: number[] = [];
  for (let v = 0; v <= c.max + 1e-9; v += c.step || 1)
    out.push(Math.round(v * 100) / 100);
  return out;
}

export function MarkCalculator({
  templateTitle,
  paperMax,
  studentName,
  onApply,
  onClose,
}: {
  templateTitle: string | null;
  paperMax: number;
  studentName: string | null;
  onApply: (value: number) => void;
  onClose: () => void;
}) {
  const [schemes, setSchemes] = useState<Schemes | null>(null);
  const [key, setKey] = useState(() => guessScheme(templateTitle, paperMax));
  const [marks, setMarks] = useState<Record<number, number>>({});
  const [res, setRes] = useState<ScoreResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Schemes>("/mock-schemes")
      .then(setSchemes)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const scheme = schemes?.[key] ?? null;

  // Sxema almashganda oldingi baholar qolib ketmasin
  useEffect(() => {
    setMarks({});
    setRes(null);
  }, [key]);

  const ready =
    !!scheme && scheme.criteria.every((_, i) => marks[i] !== undefined);

  const payload = useMemo(
    () => (scheme ? scheme.criteria.map((_, i) => marks[i] ?? null) : []),
    [scheme, marks]
  );

  useEffect(() => {
    if (!ready) {
      setRes(null);
      return;
    }
    let dead = false;
    api
      .post<ScoreResult>("/mock-score", { skill: key, marks: payload })
      .then((r) => {
        if (!dead) setRes(r);
      })
      .catch((e) => {
        if (!dead) setErr(e instanceof Error ? e.message : "Xatolik");
      });
    return () => {
      dead = true;
    };
  }, [ready, key, payload]);

  const finalValue =
    res?.band != null ? res.band : res?.score != null ? res.score : null;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/40 flex items-start justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-lg mt-10"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <Calculator size={16} className="text-brand-600" />
              Mezonlar bo'yicha hisoblash
            </h3>
            {studentName && (
              <p className="text-xs text-slate-500 mt-0.5">{studentName}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
            aria-label="Yopish"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {err && <p className="text-sm text-rose-600">{err}</p>}
          {!schemes && !err && (
            <p className="text-sm text-slate-400">Yuklanmoqda…</p>
          )}

          {schemes && (
            <label className="block">
              <span className="text-xs text-slate-500">Baholash sxemasi</span>
              <select
                value={key}
                onChange={(e) => setKey(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {Object.entries(schemes).map(([k, s]) => (
                  <option key={k} value={k}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          )}

          {scheme && (
            <>
              <div className="space-y-2.5">
                {scheme.criteria.map((c, i) => (
                  <div key={c.name} className="flex items-center gap-3">
                    <span className="flex-1 text-sm text-slate-700">
                      {c.name}
                      <span className="text-slate-400 text-xs ml-1">
                        / {c.max}
                      </span>
                    </span>
                    <select
                      value={marks[i] ?? ""}
                      onChange={(e) => {
                        const next = { ...marks };
                        if (e.target.value === "") delete next[i];
                        else next[i] = Number(e.target.value);
                        setMarks(next);
                      }}
                      className="w-44 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
                    >
                      <option value="">—</option>
                      {stepValues(c).map((v) => {
                        const band = c.bands?.find((b) => b.mark === v);
                        return (
                          <option key={v} value={v}>
                            {v}
                            {band ? ` — ${band.level}` : ""}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                ))}
              </div>

              <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
                {scheme.note}
              </p>
            </>
          )}

          {res && finalValue != null && (
            <div className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-3">
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-brand-700">
                  {finalValue}
                </span>
                {res.level && (
                  <span className="text-sm font-medium text-brand-700">
                    {res.level}
                  </span>
                )}
                {res.raw != null && (
                  <span className="text-xs text-slate-500 ml-auto">
                    xom ball {res.raw}/{res.raw_max}
                  </span>
                )}
              </div>
              {res.exact === false && res.note && (
                <p className="text-xs text-amber-700 mt-1.5">
                  TAXMINIY: {res.note}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 px-5 py-3 border-t border-slate-200 bg-slate-50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800"
          >
            Bekor qilish
          </button>
          <button
            disabled={finalValue == null}
            onClick={() => {
              if (finalValue != null) {
                onApply(finalValue);
                onClose();
              }
            }}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            Ballni qo'yish
          </button>
        </div>
      </div>
    </div>
  );
}
