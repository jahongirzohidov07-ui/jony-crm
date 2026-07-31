import { useEffect, useState } from "react";
import {
  TrendingUp, TrendingDown, Minus, Info, ArrowRight, CheckCircle2,
  XCircle,
} from "lucide-react";
import { api } from "../lib/api";

const TONE: Record<string, string> = {
  emerald: "bg-emerald-50 border-emerald-200 text-emerald-800",
  teal: "bg-teal-50 border-teal-200 text-teal-800",
  amber: "bg-amber-50 border-amber-200 text-amber-800",
  orange: "bg-orange-50 border-orange-200 text-orange-800",
  red: "bg-red-50 border-red-200 text-red-800",
  slate: "bg-slate-50 border-slate-200 text-slate-700",
  sky: "bg-sky-50 border-sky-200 text-sky-800",
  violet: "bg-violet-50 border-violet-200 text-violet-800",
};

interface Obs {
  id: number;
  stage?: string | null;
  stage_label?: string;
  stage_tone?: string;
  percent: number;
  total: number;
  max_total: number;
  band_label?: string;
  tone?: string;
  date?: string | null;
  observer?: string | null;
  strengths?: string | null;
  weaknesses?: string | null;
}

interface CompareRow {
  criterion_id: number;
  no: number;
  text: string;
  points: number;
  before: number;
  after: number;
  delta: number;
}

interface Evaluation {
  candidate_id: number;
  full_name: string;
  before: Obs | null;
  after: Obs | null;
  extra: (Obs | null)[];
  delta: number | null;
  growth: { label: string; tone: string; advice: string } | null;
  compare: CompareRow[];
  improved: CompareRow[];
  stuck: CompareRow[];
  pass_score: number;
  passed: boolean;
  stages: { key: string; label: string; tone: string }[];
  next_stage: string;
  hint: string;
}

function Score({ o, title }: { o: Obs | null; title: string }) {
  if (!o)
    return (
      <div className="rounded-xl border border-dashed border-slate-300 p-4 text-center">
        <p className="text-xs text-slate-400 mb-1">{title}</p>
        <p className="text-sm text-slate-400">hali baholanmagan</p>
      </div>
    );
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <p className="text-xs text-slate-500 mb-1">{title}</p>
      <p className="text-2xl font-semibold text-slate-900">{o.percent}%</p>
      <p className="text-xs text-slate-400">
        {o.total} / {o.max_total} ball
        {o.band_label ? ` · ${o.band_label}` : ""}
      </p>
      {o.observer && (
        <p className="text-xs text-slate-400 mt-1">Baholadi: {o.observer}</p>
      )}
    </div>
  );
}

/**
 * Nomzodning ikki baholash orasidagi o'sishi.
 *
 * Bu ekranning butun ma'nosi shunda: ikkinchi ballning o'zi kam narsa
 * aytadi. Sust boshlab keskin o'sgan odam — o'rgatsa bo'ladigan odam.
 * Yaxshi boshlab qimirlamagan odam esa bor darajasida qoladi. Ikkovi
 * ham "o'tdi" bo'lishi mumkin, lekin ular bir xil emas.
 */
export function CandidateGrowth({ candidateId }: { candidateId: number }) {
  const [d, setD] = useState<Evaluation | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Evaluation>(`/candidates/${candidateId}/evaluation`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [candidateId]);

  if (err) return <p className="text-sm text-slate-400 py-4">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-4">Yuklanmoqda…</p>;

  const Icon =
    d.delta == null ? Minus : d.delta > 2 ? TrendingUp : d.delta < -2 ? TrendingDown : Minus;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5">
      <p className="text-sm font-medium text-slate-800 mb-1">
        Sinov darsi: o'sish
      </p>
      <p className="text-xs text-slate-400 mb-4">{d.hint}</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <Score o={d.before} title="1-baholash: o'z holicha" />
        <Score o={d.after} title="2-baholash: tushuntirilgandan keyin" />

        <div
          className={`rounded-xl border p-4 ${
            d.growth ? TONE[d.growth.tone] || TONE.slate : TONE.slate
          }`}
        >
          <p className="text-xs opacity-70 mb-1">Farq</p>
          <p className="text-2xl font-semibold flex items-center gap-1">
            <Icon size={20} />
            {d.delta == null
              ? "—"
              : `${d.delta > 0 ? "+" : ""}${d.delta}`}
            {d.delta != null && (
              <span className="text-base font-normal opacity-70">%</span>
            )}
          </p>
          {d.growth && (
            <p className="text-xs font-medium mt-0.5">{d.growth.label}</p>
          )}
        </div>
      </div>

      {d.growth && (
        <div
          className={`rounded-lg border p-3 mb-4 ${
            TONE[d.growth.tone] || TONE.slate
          }`}
        >
          <p className="text-sm">{d.growth.advice}</p>
        </div>
      )}

      {d.after && (
        <p className="text-xs text-slate-500 mb-4 flex items-center gap-1.5">
          {d.passed ? (
            <CheckCircle2 size={13} className="text-emerald-600" />
          ) : (
            <XCircle size={13} className="text-red-600" />
          )}
          O'tish balli {d.pass_score}% —{" "}
          {d.passed ? "bu nomzod o'tdi" : "bu nomzod o'tmadi"}
        </p>
      )}

      {!d.after && (
        <p className="text-xs text-slate-500 mb-2 flex items-start gap-1.5">
          <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
          Keyingi qadam:{" "}
          {d.stages.find((s) => s.key === d.next_stage)?.label ||
            d.next_stage}
        </p>
      )}

      {/* ---- Nimani o'rgandi, nima o'zgarmadi ---- */}
      {d.compare.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-xs font-medium text-emerald-700 mb-1.5">
              Tushuntirgandan keyin tuzatdi ({d.improved.length})
            </p>
            {d.improved.length === 0 ? (
              <p className="text-xs text-slate-400">
                Hech bir mezonda o'sish yo'q.
              </p>
            ) : (
              <div className="space-y-1">
                {d.improved.map((r) => (
                  <div
                    key={r.criterion_id}
                    className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-emerald-50 border border-emerald-100"
                  >
                    <span className="text-xs text-slate-700 flex-1 truncate">
                      {r.no}. {r.text}
                    </span>
                    <span className="text-xs text-slate-500 shrink-0 flex items-center gap-1">
                      {r.before}
                      <ArrowRight size={10} />
                      <b className="text-emerald-700">{r.after}</b>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <p className="text-xs font-medium text-red-700 mb-1.5">
              Aytilgandan keyin ham o'zgarmadi ({d.stuck.length})
            </p>
            {d.stuck.length === 0 ? (
              <p className="text-xs text-slate-400">
                Qotib qolgan mezon yo'q.
              </p>
            ) : (
              <div className="space-y-1">
                {d.stuck.map((r) => (
                  <div
                    key={r.criterion_id}
                    className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-red-50 border border-red-100"
                  >
                    <span className="text-xs text-slate-700 flex-1 truncate">
                      {r.no}. {r.text}
                    </span>
                    <span className="text-xs text-slate-500 shrink-0">
                      {r.after} / {r.points}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {d.extra.filter(Boolean).length > 0 && (
        <p className="text-xs text-slate-400 mt-4">
          Yana {d.extra.filter(Boolean).length} ta qo'shimcha baholash bor —
          ular farqqa kirmaydi.
        </p>
      )}
    </div>
  );
}
