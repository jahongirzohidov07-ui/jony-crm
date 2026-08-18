import { useEffect, useState } from "react";
import { Pencil, Target } from "lucide-react";
import { api } from "../lib/api";

/**
 * MAQSAD: IELTS BALLI (2026-08-18).
 *
 * Jahongir: "target ballini kirgizsa uni progressidan kelib chiqib shu
 * ballni olishga qancha vaqt qolganligni korsatib tursin, shuncha yil,
 * shuncha kun va shuncha soatdan keyin olasan deb" + "nechi XP emas
 * IELTS nechi olmoqchiligi bolishi kerak".
 *
 * Muddat SERVERDA hisoblanadi (mashq ballari zinasi + oxirgi 30 kunlik
 * tezlik). Bu taxminiy baho — karta buni yashirmaydi.
 */

type Goal = {
  target: number | null;
  band: number;
  level: string;
  points: number;
  done: boolean;
  percent: number | null;
  per_day: number | null;
  eta: { years: number; days: number; hours: number } | null;
};

const BANDS = [4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9];

function etaText(e: NonNullable<Goal["eta"]>): string {
  const parts: string[] = [];
  if (e.years > 0) parts.push(`${e.years} yil`);
  if (e.days > 0) parts.push(`${e.days} kun`);
  parts.push(`${e.hours} soat`);
  return parts.join(", ");
}

const fmtBand = (b: number) => (Number.isInteger(b) ? `${b}.0` : `${b}`);

export function GoalCard() {
  const [g, setG] = useState<Goal | null>(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Goal>("/student/goal").then(setG).catch(() => setG(null));
  }, []);

  async function save(band: number) {
    if (busy) return;
    setBusy(true);
    try {
      const r = await api.post<Goal>("/student/goal", { target: band });
      setG(r);
      setEditing(false);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (!g) return null;

  /* ─── Maqsad qo'yilmagan / tahrirlash ─── */
  if (!g.target || editing) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-1.5">
          <Target size={17} className="text-violet-600" />
          <p className="text-[14px] font-bold text-slate-900">
            IELTS maqsadingiz nechchi?
          </p>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          Hozirgi darajangiz: <b>{g.level}</b> (taxminan ~{fmtBand(g.band)}).
          Maqsad qo'ysangiz, unga qachon yetishingizni hisoblab beraman.
        </p>
        <div className="flex flex-wrap gap-1.5">
          {BANDS.map((b) => (
            <button key={b} onClick={() => save(b)} disabled={busy}
              className={`px-3 py-2 rounded-lg text-[13px] font-bold border transition active:scale-95 ${
                b <= g.band
                  ? "border-slate-100 bg-slate-50 text-slate-300"
                  : "border-violet-200 bg-violet-50 text-violet-700"
              }`}>
              {fmtBand(b)}
            </button>
          ))}
          {editing && (
            <button onClick={() => setEditing(false)}
              className="px-3 py-2 rounded-lg text-[13px] text-slate-500 border border-slate-200">
              Bekor
            </button>
          )}
        </div>
      </div>
    );
  }

  /* ─── Yetildi ─── */
  if (g.done) {
    return (
      <div className="bg-gradient-to-br from-emerald-600 to-teal-500 rounded-xl p-4 text-white">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🏆</span>
          <div className="flex-1">
            <p className="text-[15px] font-bold">
              Maqsad darajaga yetdingiz! ~{fmtBand(g.band)}
            </p>
            <p className="text-xs text-white/85 mt-0.5">
              Maqsadingiz IELTS {fmtBand(g.target)} edi. Yangisini qo'ying!
            </p>
          </div>
          <button onClick={() => setEditing(true)}
            className="px-3 py-1.5 rounded-lg bg-white/20 text-xs font-bold shrink-0">
            Yangi maqsad
          </button>
        </div>
      </div>
    );
  }

  /* ─── Yo'lda ─── */
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center gap-2">
        <Target size={17} className="text-violet-600" />
        <p className="text-[14px] font-bold text-slate-900">
          Maqsad: IELTS {fmtBand(g.target)}
        </p>
        <button onClick={() => setEditing(true)}
          className="ml-auto p-1 text-slate-300 hover:text-slate-500">
          <Pencil size={13} />
        </button>
      </div>

      <div className="flex items-center gap-2 mt-2.5">
        <span className="text-xs font-bold text-slate-500 shrink-0">
          ~{fmtBand(g.band)}
        </span>
        <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all"
            style={{ width: `${g.percent ?? 0}%` }}
          />
        </div>
        <span className="text-xs font-bold text-violet-700 shrink-0">
          {fmtBand(g.target)}
        </span>
      </div>
      <p className="text-[11px] text-slate-400 mt-1">
        Hozir: {g.level} · taxminiy ~{fmtBand(g.band)}
      </p>

      {g.eta ? (
        <p className="text-[13px] text-slate-700 mt-2">
          🕐 Shu tezlikda IELTS {fmtBand(g.target)} ni{" "}
          <b className="text-violet-700">{etaText(g.eta)}</b>dan keyin
          olasiz
          {g.per_day ? (
            <span className="text-xs text-slate-400">
              {" "}(kuniga ~{g.per_day} ball)
            </span>
          ) : null}
        </p>
      ) : (
        <p className="text-[13px] text-slate-500 mt-2">
          Muddatni aytishim uchun mashq qilishni boshlang — har mashq
          maqsadga yaqinlashtiradi 💪
        </p>
      )}
    </div>
  );
}
