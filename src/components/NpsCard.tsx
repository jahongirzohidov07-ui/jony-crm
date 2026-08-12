import { useEffect, useState } from "react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * NPS so'rovi kartasi — chorakda bir marta, o'quvchi va ota-ona
 * portallarida (2026-08-12, Jahongir: "Ota-ona NPS so'rovi...
 * O'quvchiga ham shu chiqsin platformasida").
 */
export function NpsCard() {
  const [st, setSt] = useState<any>(null);
  const [score, setScore] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    api.get<any>("/nps/status").then(setSt).catch(() => {});
  }, []);

  if (!st?.show) return null;
  if (done)
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 text-center">
        <p className="text-sm font-semibold text-emerald-800">
          Rahmat! Fikringiz biz uchun juda muhim 💚
        </p>
      </div>
    );

  async function submit() {
    if (score === null) return;
    setBusy(true);
    try {
      await api.post("/nps/answer", { score, comment: comment.trim() || undefined });
      setDone(true);
    } catch {
      /* jim */
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-violet-200 p-4">
      <p className="text-sm font-bold text-slate-800 mb-1">
        Bir savol 🙌
      </p>
      <p className="text-[13px] text-slate-600 mb-3">{st.question}</p>
      <div className="grid grid-cols-11 gap-1 mb-3">
        {Array.from({ length: 11 }, (_, i) => (
          <button
            key={i}
            onClick={() => setScore(i)}
            className={`h-9 rounded-lg text-xs font-bold transition ${
              score === i
                ? "bg-violet-600 text-white"
                : i <= 6
                  ? "bg-red-50 text-red-600"
                  : i <= 8
                    ? "bg-amber-50 text-amber-600"
                    : "bg-emerald-50 text-emerald-600"
            }`}
          >
            {i}
          </button>
        ))}
      </div>
      {score !== null && (
        <>
          <input
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Izoh (ixtiyoriy)"
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-2"
          />
          <button
            disabled={busy}
            onClick={submit}
            className="w-full bg-violet-600 text-white rounded-xl py-2.5 text-sm font-semibold disabled:opacity-50"
          >
            Yuborish
          </button>
        </>
      )}
    </div>
  );
}
