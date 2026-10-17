import "./wordbank.css";
import { Check } from "lucide-react";
import { formatDayMonth } from "../../lib/format";
import { fmtNum } from "../../lib/studentApi";
import { pHat, type WbBand, type WbSizeTest } from "../../lib/wordbankApi";

/**
 * SO'Z BILISH — 20 ta daraja ro'yxati (2026-10-16, OWNER D1/D5).
 *
 * Har qator: "Common 1000: 870/1000", bo'lingan chiziq (yashil —
 * tasdiqlangan, ko'k — o'rganilmoqda, kulrang — yangi), coin belgisi
 * ("+N coin" — N-daraja uchun N coin; tugagach oltin rang, ✓ va sana).
 * Nuqtali chiziq — oxirgi hajm testi bo'yicha TAXMIN (alohida, songa
 * qo'shilmaydi).
 */
export function BandList({
  bands,
  focus,
  sizeTest,
}: {
  bands: WbBand[];
  focus: number | null;
  sizeTest: WbSizeTest | null;
}) {
  return (
    <div className="divide-y divide-slate-100">
      {bands.map((b) => (
        <BandRow
          key={b.band}
          b={b}
          isFocus={focus === b.band}
          est={sizeTest?.bands?.[String(b.band)] ?? null}
        />
      ))}
    </div>
  );
}

function BandRow({
  b,
  isFocus,
  est,
}: {
  b: WbBand;
  isFocus: boolean;
  est: [number, number, number] | null;
}) {
  const total = Math.max(0, b.total);
  const knownPct = total ? Math.min(100, (b.known / total) * 100) : 0;
  const learnPct = total
    ? Math.min(100 - knownPct, (Math.max(0, b.learning) / total) * 100)
    : 0;
  const estPct = est ? pHat(est[0], est[1], est[2]) * 100 : null;
  const left = Math.max(0, total - b.known);

  return (
    <div className={`py-2.5 ${isFocus ? "bg-sky-50 -mx-3 px-3 rounded-xl" : ""}`}>
      <div className="flex items-center gap-2">
        <span
          className={`w-8 h-8 rounded-lg text-[13px] font-extrabold flex items-center justify-center shrink-0 ${
            b.done
              ? "bg-amber-400 text-white"
              : isFocus
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-500"
          }`}
        >
          {b.band}
        </span>
        <p className="flex-1 min-w-0 text-[14px] text-slate-900 leading-tight">
          <b>{b.label}:</b>{" "}
          <span className={b.done ? "text-emerald-700 font-bold" : "text-slate-600"}>
            {fmtNum(b.known)}/{fmtNum(total || 1000)}
          </span>
        </p>
        <span
          className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11.5px] font-extrabold shrink-0 ${
            b.done
              ? "bg-amber-400 text-white"
              : "border border-amber-300 text-amber-700 bg-amber-50"
          }`}
          title={b.done ? "Coin berildi" : "Darajani tugatsangiz beriladi"}
        >
          {b.done && <Check size={12} strokeWidth={4} />}+{b.coins} coin
        </span>
      </div>

      {b.ready ? (
        <div className="wb-bar-wrap mt-2 ml-10">
          <div
            className="wb-bar"
            role="progressbar"
            aria-label={`${b.label}: ${b.known} ta tasdiqlangan`}
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={b.known}
          >
            <div className="wb-known" style={{ width: `${knownPct}%` }} />
            <div className="wb-learning" style={{ width: `${learnPct}%` }} />
          </div>
          {estPct !== null && estPct > 0 && (
            <span
              className="wb-est-mark"
              style={{ left: `${Math.min(99.5, estPct)}%` }}
              title={`Test bo'yicha taxminan ${Math.round(estPct)}%`}
            />
          )}
        </div>
      ) : null}

      <p className="text-[11.5px] mt-1 ml-10 leading-snug">
        {b.done ? (
          <span className="text-amber-700 font-semibold">
            Tugatildi{b.awarded_at ? ` · ${formatDayMonth(b.awarded_at)}` : ""}
          </span>
        ) : !b.ready ? (
          <span className="text-slate-400">Tez orada</span>
        ) : isFocus ? (
          <span className="text-brand-700 font-semibold">
            Hozirgi daraja · yana {fmtNum(left)} so'z → +{b.coins} coin
          </span>
        ) : b.learning > 0 ? (
          <span className="text-slate-500">
            O'rganilmoqda: {fmtNum(b.learning)} so'z
          </span>
        ) : (
          <span className="text-slate-400">Hali boshlanmagan</span>
        )}
      </p>
    </div>
  );
}

/** Rang izohi — ro'yxat ustida bir marta. */
export function BandLegend({ withEstimate }: { withEstimate: boolean }) {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-500">
      <span className="inline-flex items-center gap-1">
        <i className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
        tasdiqlangan
      </span>
      <span className="inline-flex items-center gap-1">
        <i className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block" />
        o'rganilmoqda
      </span>
      <span className="inline-flex items-center gap-1">
        <i className="w-2.5 h-2.5 rounded-full bg-slate-200 inline-block" />
        yangi
      </span>
      {withEstimate && (
        <span className="inline-flex items-center gap-1">
          <i className="h-2.5 inline-block border-l-2 border-dotted border-slate-500" />
          test bo'yicha (taxminiy)
        </span>
      )}
    </div>
  );
}
