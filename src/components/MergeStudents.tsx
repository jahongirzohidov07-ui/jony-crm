import { useState } from "react";
import { Merge, X, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";

/**
 * IKKI YOZUVNI BITTA QILISH (2026-08-17).
 *
 * Jahongir: "qara sen aytyabman shu ikktani bitta qil, bittasini
 * toliq ochirib tashla, davomatri, otsin lekin bunga".
 *
 * Kelib chiqishi: ilgari bazada bitta o'quvchida bitta guruh bo'lgani
 * uchun ikki fanga qatnaydigan bola IKKI MARTA kiritilgan. Bekobod 2
 * da uchta shunday juft topilgan edi.
 *
 * Bu oyna ortiqcha yozuvni tanlaydi va serverga birlashtirishni
 * buyuradi: davomat, baho, imtihon, coin, XP, to'lov — hammasi shu
 * kartaga ko'chadi, keyin bo'm-bo'sh qolgan yozuv o'chiriladi.
 * Ya'ni "o'chirish" hech qanday ma'lumotni yo'qotmaydi.
 *
 * Faqat ASOSCHIGA ko'rinadi (server ham shuni tekshiradi).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Hit = { id: number; full_name: string; group?: string | null;
             branch?: string | null };

export function MergeStudents({
  studentId,
  studentName,
  onClose,
  onDone,
}: {
  studentId: number;
  studentName: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [q, setQ] = useState(studentName.split(" ")[0] || "");
  const [hits, setHits] = useState<Hit[]>([]);
  const [pick, setPick] = useState<Hit | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<any>(null);

  async function search() {
    if (q.trim().length < 3) return;
    setErr("");
    try {
      const r = await api.get<Hit[]>(
        `/family-search?q=${encodeURIComponent(q.trim())}&exclude=${studentId}`
      );
      setHits((r || []).filter((x) => x.id !== studentId));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Qidirib bo'lmadi");
    }
  }

  async function merge() {
    if (!pick) return;
    if (
      !confirm(
        `"${pick.full_name}" (#${pick.id}) yozuvi butunlay yo'q qilinadi.\n\n` +
          `Uning davomati, baholari, imtihonlari, coinlari, XP va ` +
          `to'lovlari SHU kartaga ko'chadi.\n\nDavom etamizmi?`
      )
    )
      return;
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<any>(
        `/students/${studentId}/merge/${pick.id}`
      );
      setDone(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Birlashtirib bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-5 max-h-[88vh] overflow-y-auto">
        <div className="flex items-center gap-2 mb-1">
          <Merge size={18} className="text-brand-600" />
          <p className="font-semibold text-slate-900 flex-1">
            Ikki yozuvni bitta qilish
          </p>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Qoladigan karta: <b>{studentName}</b> (#{studentId})
        </p>

        {done ? (
          <>
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-emerald-800">
                Birlashtirildi
              </p>
              <ul className="text-xs text-emerald-800 mt-2 space-y-0.5">
                {Object.entries(done.moved || {}).map(([k, v]) => (
                  <li key={k}>
                    {k}: <b>{String(v)}</b> ta ko'chdi
                  </li>
                ))}
              </ul>
              <p className="text-xs text-emerald-800 mt-2">
                Guruhlari: <b>{done.groups}</b> ta · Balans:{" "}
                <b>{Number(done.balance).toLocaleString("ru-RU")} so'm</b>
              </p>
            </div>
            <button
              onClick={onDone}
              className="mt-4 w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-semibold"
            >
              Yopish
            </button>
          </>
        ) : (
          <>
            <div className="flex gap-2">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && search()}
                placeholder="Ismi bo'yicha qidiring…"
                className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
              <button
                onClick={search}
                className="px-4 py-2 rounded-lg bg-slate-100 text-slate-700 text-sm font-medium"
              >
                Qidirish
              </button>
            </div>

            <div className="mt-3 space-y-1.5 max-h-52 overflow-y-auto">
              {hits.map((h) => (
                <button
                  key={h.id}
                  onClick={() => setPick(h)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg border text-sm ${
                    pick?.id === h.id
                      ? "border-brand-400 bg-brand-50"
                      : "border-slate-200"
                  }`}
                >
                  <span className="font-medium text-slate-900">
                    {h.full_name}
                  </span>
                  <span className="text-xs text-slate-400">
                    {" "}
                    #{h.id}
                    {h.group ? ` · ${h.group}` : ""}
                    {h.branch ? ` · ${h.branch}` : ""}
                  </span>
                </button>
              ))}
              {hits.length === 0 && (
                <p className="text-xs text-slate-400 py-3 text-center">
                  Kamida 3 harf yozib qidiring.
                </p>
              )}
            </div>

            {pick && (
              <div className="mt-3 bg-amber-50 border border-amber-200 rounded-xl p-3 flex gap-2">
                <AlertTriangle
                  size={15}
                  className="text-amber-600 shrink-0 mt-0.5"
                />
                <p className="text-xs text-amber-900 leading-snug">
                  <b>{pick.full_name}</b> (#{pick.id}) yozuvi o'chiriladi.
                  Uning davomati, baholari, coinlari va to'lovlari shu
                  kartaga ko'chadi — hech narsa yo'qolmaydi. Amal
                  tarixga yoziladi.
                </p>
              </div>
            )}

            {err && (
              <p className="mt-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {err}
              </p>
            )}

            <div className="mt-4 flex gap-2">
              <button
                onClick={onClose}
                disabled={busy}
                className="flex-1 py-2.5 rounded-lg border border-slate-200 text-slate-600 text-sm"
              >
                Bekor
              </button>
              <button
                onClick={merge}
                disabled={busy || !pick}
                className="flex-1 py-2.5 rounded-lg bg-red-600 text-white text-sm font-semibold disabled:opacity-50"
              >
                {busy ? "Birlashtirilmoqda…" : "Birlashtirish"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
