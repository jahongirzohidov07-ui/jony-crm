import { useMemo, useState } from "react";
import { Percent, TrendingDown, Users, ArrowDownWideNarrow } from "lucide-react";

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface FunnelStageIn {
  stage: string;
  reached: number;
  here_now: number;
  percent: number;
  lost_here: number;
}

interface Props {
  total: number;
  stages: FunnelStageIn[];
  rejected: number;
  labelOf: (s: string) => string;
}

/** Voronka rangi: tepasi ochiq havorang, pastga qarab to'q ko'k. */
const C_TOP = [56, 189, 248];
const C_BOT = [12, 45, 107];

function bandColor(t: number) {
  const c = C_TOP.map((a, i) => Math.round(a + (C_BOT[i] - a) * t));
  return "rgb(" + c[0] + "," + c[1] + "," + c[2] + ")";
}

const pct1 = (n: number) => {
  const r = Math.round(n * 10) / 10;
  return (Number.isInteger(r) ? r.toFixed(0) : r.toFixed(1)) + "%";
};

function Card({
  label, value, sub, tone, icon: Icon,
}: {
  label: string; value: string; sub?: string;
  tone: "emerald" | "rose" | "slate" | "amber"; icon: any;
}) {
  const tones: Record<string, string> = {
    emerald: "text-emerald-600 bg-emerald-50",
    rose: "text-rose-600 bg-rose-50",
    amber: "text-amber-600 bg-amber-50",
    slate: "text-slate-600 bg-slate-100",
  };
  const vt: Record<string, string> = {
    emerald: "text-emerald-700",
    rose: "text-rose-700",
    amber: "text-amber-700",
    slate: "text-slate-800",
  };
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-start gap-3">
      <span className={"rounded-lg p-2 shrink-0 " + tones[tone]}>
        <Icon size={16} />
      </span>
      <div className="min-w-0">
        <p className={"text-2xl font-semibold leading-tight " + vt[tone]}>{value}</p>
        <p className="text-xs text-slate-500 mt-0.5 leading-snug">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5 leading-snug">{sub}</p>}
      </div>
    </div>
  );
}

/** Sotuv voronkasi: 4 ta ko'rsatkich + bosqichma-bosqich voronka shakli. */
export default function SalesFunnel({ total, stages, rejected, labelOf }: Props) {
  const [sel, setSel] = useState(0);

  const rows = useMemo(() => {
    return stages.map((s, i) => {
      const prev = i > 0 ? stages[i - 1].reached : total;
      const stepLost = Math.max(prev - s.reached, 0);
      const cumLost = Math.max(total - s.reached, 0);
      return {
        ...s,
        idx: i,
        label: labelOf(s.stage),
        prev,
        stepLost,
        stepPct: prev ? (stepLost / prev) * 100 : 0,
        cumLost,
        cumPct: total ? (cumLost / total) * 100 : 0,
        ofTotal: total ? (s.reached / total) * 100 : 0,
      };
    });
  }, [stages, total, labelOf]);

  if (!total || rows.length === 0) {
    return <p className="text-sm text-slate-400 py-4">Hali lid kiritilmagan.</p>;
  }

  const last = rows[rows.length - 1];
  const conv = last.ofTotal;
  const worst = rows.reduce(
    (a, b) => (b.idx > 0 && b.stepPct > a.stepPct ? b : a),
    rows[0],
  );
  const cur = rows[Math.min(sel, rows.length - 1)];

  // Voronka kengligi: eng kamida 8% ko'rinib turadi.
  const w = (v: number) => Math.max(8, Math.min(100, v));
  const widths = rows.map((r) => w(r.ofTotal));
  const tailW = Math.max(widths[widths.length - 1] * 0.78, 6);

  return (
    <div>
      {/* ---------- 4 ta ko'rsatkich ---------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 mb-5">
        <Card
          icon={Percent}
          tone="emerald"
          value={pct1(conv)}
          label="Umumiy sotuv konversiyasi"
          sub={last.reached + " / " + total + " ta lid"}
        />
        <Card
          icon={ArrowDownWideNarrow}
          tone={cur.cumLost > 0 ? "rose" : "slate"}
          value={String(cur.cumLost)}
          label="Shu bosqichgacha yo'qotilgan lidlar"
          sub={cur.label + " · " + pct1(cur.cumPct)}
        />
        <Card
          icon={TrendingDown}
          tone={cur.stepLost > 0 ? "rose" : "slate"}
          value={String(cur.stepLost)}
          label="Avvalgi bosqichdan yo'qotilgan lidlar"
          sub={cur.label + " · " + pct1(cur.stepPct)}
        />
        <Card
          icon={Users}
          tone="amber"
          value={pct1(worst.stepPct)}
          label={"Eng katta yo'qotish — " + worst.label}
          sub={worst.stepLost + " ta lid shu bosqichda ketdi"}
        />
      </div>

      <p className="text-xs text-slate-400 mb-3">
        Bosqichni bosing — 2- va 3- ko'rsatkich shu bosqich bo'yicha
        qayta hisoblanadi.
      </p>

      {/* ---------- Voronka ---------- */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="hidden sm:grid grid-cols-[minmax(180px,1fr)_minmax(160px,300px)_92px_92px] gap-0 px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-400 font-medium">
          <span>Bosqich</span>
          <span />
          <span className="text-right">Shu yergacha</span>
          <span className="text-right">Bir qadamda</span>
        </div>

        {rows.map((r, i) => {
          const w0 = widths[i];
          const w1 = i + 1 < widths.length ? widths[i + 1] : tailW;
          const t = rows.length > 1 ? i / (rows.length - 1) : 0;
          const fill = bandColor(t);
          const on = i === cur.idx;
          const l0 = 50 - w0 / 2, r0 = 50 + w0 / 2;
          const l1 = 50 - w1 / 2, r1 = 50 + w1 / 2;
          const d =
            "M " + l0 + " 0 C " + l0 + " 42, " + l1 + " 58, " + l1 + " 100 " +
            "L " + r1 + " 100 C " + r1 + " 58, " + r0 + " 42, " + r0 + " 0 Z";
          return (
            <button
              key={r.stage}
              onClick={() => setSel(i)}
              className={
                "w-full text-left grid grid-cols-[1fr_minmax(90px,150px)] sm:grid-cols-[minmax(180px,1fr)_minmax(160px,300px)_92px_92px] items-stretch border-b border-slate-100 last:border-b-0 transition-colors " +
                (on ? "bg-sky-50/70" : "hover:bg-slate-50")
              }
            >
              <span className="px-4 py-3 flex flex-col justify-center">
                <span className="flex items-baseline gap-2">
                  <span className="text-xl font-semibold text-slate-900">
                    {r.reached}
                  </span>
                  <span className="text-xs text-slate-400">ta</span>
                </span>
                <span
                  className={
                    "text-sm mt-0.5 " +
                    (on ? "text-sky-700 font-medium" : "text-slate-600")
                  }
                >
                  {r.label}
                </span>
                <span className="text-xs font-medium text-indigo-500 mt-0.5">
                  {pct1(r.ofTotal)}
                  {r.here_now > 0 && (
                    <span className="text-slate-400 font-normal">
                      {" · hozir " + r.here_now + " ta"}
                    </span>
                  )}
                </span>
              </span>

              <span className="relative block h-[78px] sm:h-[88px]">
                <svg
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                  className="absolute inset-0 w-full h-full block"
                >
                  <path d={d} fill={fill} />
                  {on && (
                    <path
                      d={d}
                      fill="none"
                      stroke="#ffffff"
                      strokeWidth="1.6"
                      vectorEffect="non-scaling-stroke"
                    />
                  )}
                </svg>
              </span>

              <span className="hidden sm:flex px-3 items-center justify-end">
                <span
                  className={
                    "text-sm font-medium " +
                    (r.cumPct > 0 ? "text-slate-700" : "text-slate-300")
                  }
                >
                  {pct1(r.cumPct)}
                </span>
              </span>
              <span className="hidden sm:flex px-4 items-center justify-end">
                <span
                  className={
                    "text-sm font-semibold " +
                    (r.stepPct > 0 ? "text-rose-600" : "text-slate-300")
                  }
                >
                  {pct1(r.stepPct)}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 mt-3 text-xs text-slate-400">
        <span>Jami lid: {total} ta</span>
        {rejected > 0 && <span>Rad etdi: {rejected} ta</span>}
        <span>Oxirgi bosqichga yetgan: {last.reached} ta</span>
      </div>
    </div>
  );
}
