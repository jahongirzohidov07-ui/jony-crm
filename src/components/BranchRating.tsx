import { useEffect, useState } from "react";
import { Trophy, Sliders, X, Check } from "lucide-react";
import { api, type BranchRating as Data } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FOUNDER } from "../lib/roles";
import { formatSom } from "../lib/format";

const GRADE_TONE: Record<string, string> = {
  a: "bg-emerald-100 text-emerald-800 border-emerald-300",
  b: "bg-sky-100 text-sky-800 border-sky-300",
  c: "bg-amber-100 text-amber-800 border-amber-300",
  d: "bg-red-100 text-red-800 border-red-300",
};

function barTone(v: number): string {
  if (v >= 75) return "bg-emerald-500";
  if (v >= 55) return "bg-sky-500";
  if (v >= 40) return "bg-amber-500";
  return "bg-red-500";
}

/**
 * Filial reytingi. Filialni faqat tushum bilan baholash — eng katta
 * xato: ko'p pul yig'ib, o'quvchini yo'qotayotgan filial "yaxshi"
 * ko'rinib qoladi. Shuning uchun 7 o'lchov, har birining og'irligi bilan.
 */
export function BranchRating({ months = 3 }: { months?: number }) {
  const { user } = useAuth();
  const [data, setData] = useState<Data | null>(null);
  const [period, setPeriod] = useState(months);
  const [weights, setWeights] = useState(false);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<Data>(`/ceo/branch-rating?months=${period}`)
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, [period]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <Trophy size={16} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Filial reytingi</p>
        <div className="flex-1" />
        <div className="flex gap-1">
          {[1, 3, 6, 12].map((m) => (
            <button
              key={m}
              onClick={() => setPeriod(m)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                period === m
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {m} oy
            </button>
          ))}
        </div>
        {user?.role === FOUNDER && (
          <button
            onClick={() => setWeights(true)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
          >
            <Sliders size={12} /> Og'irliklar
          </button>
        )}
      </div>
      <p className="text-xs text-slate-400 mb-4">
        {data.period} · tushum yagona o'lchov emas
      </p>

      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Ma'lumot yo'q.
        </p>
      ) : (
        <div className="space-y-4">
          {data.rows.map((r) => (
            <div
              key={r.branch_id}
              className="border border-slate-100 rounded-xl p-4"
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 text-sm font-semibold flex items-center justify-center">
                  {r.rank}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900">
                    {r.branch}
                  </p>
                  <p className="text-xs text-slate-400">
                    {r.raw.active} o'quvchi · {formatSom(r.raw.income)} tushum
                  </p>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                    GRADE_TONE[r.grade] || GRADE_TONE.d
                  }`}
                >
                  {r.grade_label}
                </span>
                <span className="text-2xl font-semibold text-slate-900 w-16 text-right">
                  {r.score}
                </span>
              </div>

              <div className="space-y-1.5">
                {data.dimensions.map((d) => {
                  const v = r.scores[d.key] ?? 0;
                  return (
                    <div key={d.key} className="flex items-center gap-2">
                      <span className="text-xs text-slate-500 w-36 shrink-0">
                        {d.label}
                        <span className="text-slate-300 ml-1">
                          {d.weight}%
                        </span>
                      </span>
                      <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${barTone(v)}`}
                          style={{ width: `${v}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-600 w-8 text-right">
                        {Math.round(v)}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 pt-3 border-t border-slate-50 text-xs text-slate-500">
                <span>Rentabellik {r.raw.margin}%</span>
                <span>Ketish {r.raw.churn}%</span>
                <span>Konversiya {r.raw.conversion}%</span>
                {r.raw.academic !== null && r.raw.academic !== undefined && (
                  <span>Imtihon {r.raw.academic}%</span>
                )}
                <span>
                  Qarz/o'quvchi {formatSom(r.raw.debt_per_student)}
                </span>
                <span>Shikoyat {r.raw.complaints}</span>
                <span>Tartibsizlik {r.raw.issues}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {weights && (
        <WeightsForm
          current={data.weights}
          dimensions={data.dimensions}
          onClose={() => setWeights(false)}
          onSaved={() => {
            setWeights(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function WeightsForm({
  current,
  dimensions,
  onClose,
  onSaved,
}: {
  current: Record<string, number>;
  dimensions: { key: string; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [w, setW] = useState<Record<string, string>>(
    Object.fromEntries(
      dimensions.map((d) => [d.key, String(current[d.key] ?? 0)])
    )
  );
  const [err, setErr] = useState("");
  const total = Object.values(w).reduce((a, b) => a + (Number(b) || 0), 0);

  async function save() {
    if (total <= 0) {
      setErr("Yig'indi 0 bo'lishi mumkin emas");
      return;
    }
    try {
      await api.put(
        "/ceo/branch-rating/weights",
        Object.fromEntries(
          Object.entries(w).map(([k, v]) => [k, Number(v) || 0])
        )
      );
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-24">
      <div className="bg-white rounded-xl w-full max-w-sm p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Reyting og'irliklari</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Strategiya o'zgarsa — foizlar ham o'zgaradi
        </p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-2 mb-4">
          {dimensions.map((d) => (
            <div key={d.key} className="flex items-center gap-3">
              <span className="text-sm text-slate-600 flex-1">{d.label}</span>
              <input
                type="number"
                value={w[d.key]}
                onChange={(e) => setW({ ...w, [d.key]: e.target.value })}
                className="w-16 px-2 py-1.5 rounded-lg border border-slate-200 text-sm text-right"
              />
              <span className="text-xs text-slate-400">%</span>
            </div>
          ))}
        </div>
        <div
          className={`flex items-center justify-between px-3 py-2 rounded-lg mb-4 ${
            total === 100
              ? "bg-emerald-50 text-emerald-800"
              : "bg-amber-50 text-amber-800"
          }`}
        >
          <span className="text-sm">Yig'indi</span>
          <span className="text-sm font-semibold flex items-center gap-1">
            {total}%{total === 100 && <Check size={14} />}
          </span>
        </div>
        <button
          onClick={save}
          className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          Saqlash
        </button>
      </div>
    </div>
  );
}
