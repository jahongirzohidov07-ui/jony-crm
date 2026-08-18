import { useEffect, useState } from "react";
import { Pencil, Target } from "lucide-react";
import { api } from "../lib/api";

/**
 * MAQSAD BALLI KARTASI (2026-08-18).
 *
 * Jahongir: "o'quvchilar kirganda target ballini kirgizsa uni
 * progressidan kelib chiqib shu ballni olishga qancha vaqt qolganligni
 * korsatib tursin, shuncha yil, shuncha kun va shuncha soatdan keyin
 * olasan deb".
 *
 * Muddat SERVERDA hisoblanadi (oxirgi 30 kunlik XP tezligidan) —
 * mijoz faqat ko'rsatadi. Tezroq mashq qilsa muddat qisqaradi,
 * tashlab qo'ysa uzayadi — har kirganda yangilanadi.
 */

type Goal = {
  target: number | null;
  xp: number;
  done: boolean;
  percent: number | null;
  per_day: number | null;
  eta: { years: number; days: number; hours: number } | null;
};

function etaText(e: NonNullable<Goal["eta"]>): string {
  const parts: string[] = [];
  if (e.years > 0) parts.push(`${e.years} yil`);
  if (e.days > 0) parts.push(`${e.days} kun`);
  parts.push(`${e.hours} soat`);
  return parts.join(", ");
}

export function GoalCard() {
  const [g, setG] = useState<Goal | null>(null);
  const [editing, setEditing] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Goal>("/student/goal").then(setG).catch(() => setG(null));
  }, []);

  async function save() {
    const v = parseInt(typed.replace(/\D/g, ""), 10);
    if (!v || busy) return;
    setBusy(true);
    try {
      const r = await api.post<Goal>("/student/goal", { target: v });
      setG(r);
      setEditing(false);
      setTyped("");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (!g) return null;

  /* ─── Maqsad hali qo'yilmagan yoki tahrirlanyapti ─── */
  if (!g.target || editing) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 mb-2">
          <Target size={17} className="text-violet-600" />
          <p className="text-[14px] font-bold text-slate-900">
            Maqsad ball
          </p>
          {g.target ? (
            <span className="ml-auto text-xs text-slate-400">
              hozirgi: {g.target.toLocaleString()} XP
            </span>
          ) : null}
        </div>
        <p className="text-xs text-slate-500 mb-2.5">
          Nechchi XP yig'moqchisiz? Ilova unga yetish vaqtini hisoblab
          beradi.
        </p>
        <div className="flex gap-2">
          <input
            inputMode="numeric"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") save(); }}
            placeholder="Masalan: 5000"
            className="flex-1 h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm focus:outline-none focus:border-violet-400"
          />
          <button onClick={save} disabled={busy || !typed.trim()}
            className="px-4 h-10 rounded-lg bg-violet-600 text-white text-sm font-semibold disabled:opacity-40">
            Qo'yish
          </button>
          {editing && (
            <button onClick={() => { setEditing(false); setTyped(""); }}
              className="px-3 h-10 rounded-lg border border-slate-200 text-sm text-slate-500">
              Bekor
            </button>
          )}
        </div>
      </div>
    );
  }

  /* ─── Maqsadga yetildi ─── */
  if (g.done) {
    return (
      <div className="bg-gradient-to-br from-emerald-600 to-teal-500 rounded-xl p-4 text-white">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🏆</span>
          <div className="flex-1">
            <p className="text-[15px] font-bold">
              Maqsadga yetdingiz! {g.target.toLocaleString()} XP
            </p>
            <p className="text-xs text-white/85 mt-0.5">
              Sizda {g.xp.toLocaleString()} XP bor. Yangi maqsad qo'ying!
            </p>
          </div>
          <button onClick={() => setEditing(true)}
            className="px-3 py-1.5 rounded-lg bg-white/20 text-xs font-bold">
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
          Maqsad: {g.target.toLocaleString()} XP
        </p>
        <button onClick={() => setEditing(true)}
          className="ml-auto p-1 text-slate-300 hover:text-slate-500">
          <Pencil size={13} />
        </button>
      </div>
      <div className="flex items-center gap-2 mt-2.5">
        <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
          <div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all"
            style={{ width: `${g.percent ?? 0}%` }} />
        </div>
        <span className="text-xs font-bold text-slate-600 shrink-0">
          {g.xp.toLocaleString()} / {g.target.toLocaleString()}
        </span>
      </div>
      {g.eta ? (
        <p className="text-[13px] text-slate-700 mt-2.5">
          🕐 Shu tezlikda{" "}
          <b className="text-violet-700">{etaText(g.eta)}</b>dan keyin
          olasiz
          {g.per_day ? (
            <span className="text-xs text-slate-400">
              {" "}(kuniga ~{g.per_day} XP)
            </span>
          ) : null}
        </p>
      ) : (
        <p className="text-[13px] text-slate-500 mt-2.5">
          Muddatni aytishim uchun mashq qilishni boshlang — har mashq
          maqsadga yaqinlashtiradi 💪
        </p>
      )}
    </div>
  );
}
