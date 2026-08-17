import { useState } from "react";
import { CalendarClock, X } from "lucide-react";
import { api } from "../lib/api";

/**
 * SUHBAT / SINOV DARSI SANASINI SO'RASH (2026-08-16).
 *
 * Jahongir: "suhbat va sinov darsi kalendari qo'shish kerak,
 * suhbatga chaqrildi yoki sinov darsi belgilansa sana so'rasin
 * soati va kunini kiritsam shu bo'limga biriktirilsin".
 *
 * Ilgari HR ikki joyda ish qilardi: nomzod kartasida bosqichni
 * o'zgartirardi, keyin ALOHIDA quvurga kirib suhbat qo'shardi.
 * Ikkinchisi ko'pincha unutilardi — "suhbatga chaqirildi" deb
 * yozilgan, lekin qachonligi hech qayerda yo'q edi.
 *
 * Endi bosqich tanlanishi bilan shu oyna chiqadi va bitta so'rov
 * bilan ikkalasi ham bajariladi (POST /candidates/{id}/schedule).
 */

const KINDS_INTERVIEW = [
  ["hr", "HR suhbati"],
  ["phone", "Telefon suhbati"],
  ["tech", "Kasbiy suhbat"],
  ["final", "Yakuniy suhbat"],
] as const;

/** Bugungi sana YYYY-MM-DD ko'rinishida (mahalliy vaqt bo'yicha). */
function todayISO() {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function ScheduleDialog({
  candidateId,
  candidateName,
  stage,
  onClose,
  onDone,
}: {
  candidateId: number;
  candidateName: string;
  /** "interview" yoki "demo" */
  stage: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const isDemo = stage === "demo";
  const [date, setDate] = useState(todayISO());
  const [time, setTime] = useState("10:00");
  const [kind, setKind] = useState(isDemo ? "demo" : "hr");
  const [place, setPlace] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function save() {
    if (!date) {
      setErr("Sanani tanlang");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await api.post(`/candidates/${candidateId}/schedule`, {
        stage,
        date,
        time: time || null,
        kind,
        place: place || null,
        note: note || null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Saqlab bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-5">
        <div className="flex items-start gap-3 mb-4">
          <span
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              isDemo
                ? "bg-amber-50 text-amber-600"
                : "bg-violet-50 text-violet-600"
            }`}
          >
            <CalendarClock size={20} />
          </span>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-slate-900">
              {isDemo ? "Sinov darsi" : "Suhbat"} belgilash
            </p>
            <p className="text-xs text-slate-500 truncate">{candidateName}</p>
          </div>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        {!isDemo && (
          <div className="mb-3">
            <label className="block text-xs text-slate-500 mb-1">Turi</label>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
            >
              {KINDS_INTERVIEW.map(([k, l]) => (
                <option key={k} value={k}>
                  {l}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Kun</label>
            <input
              type="date"
              value={date}
              min={todayISO()}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Soat</label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
        </div>

        <div className="mb-3">
          <label className="block text-xs text-slate-500 mb-1">
            Joyi (ixtiyoriy)
          </label>
          <input
            value={place}
            onChange={(e) => setPlace(e.target.value)}
            placeholder="Bekobod 1, 3-xona"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
        </div>

        <div className="mb-4">
          <label className="block text-xs text-slate-500 mb-1">
            Izoh (ixtiyoriy)
          </label>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Nimaga e'tibor berish kerak"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
        </div>

        {err && (
          <p className="text-sm text-red-600 mb-3 bg-red-50 border border-red-200 rounded-lg p-2.5">
            {err}
          </p>
        )}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            disabled={busy}
            className="flex-1 py-2.5 rounded-lg border border-slate-200 text-slate-600 text-sm font-medium"
          >
            Bekor
          </button>
          <button
            onClick={save}
            disabled={busy}
            className="flex-1 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-semibold disabled:opacity-60"
          >
            {busy ? "Saqlanmoqda…" : "Kalendarga qo'yish"}
          </button>
        </div>

        <p className="text-[11px] text-slate-400 mt-3 leading-snug">
          Bosqich o'zgaradi, ishga olish quvuri ham yuradi va yozuv
          "Kalendar" bo'limida ko'rinadi.
        </p>
      </div>
    </div>
  );
}
