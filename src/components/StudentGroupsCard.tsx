import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Star, X } from "lucide-react";
import { api } from "../lib/api";
import { formatDate, formatSom } from "../lib/format";

/**
 * O'QUVCHINING GURUHLARI — LC UP uslubida (2026-08-17).
 *
 * Jahongir: "Abduvaliyeva Munisa degan qiz 2ta gruppaga keladi ...
 * biz ham bazda 2ta gruppa qilishimiz kerak" va keyin: "shu yerda
 * 2ta guruh korinib tursin, LC da shunaqa".
 *
 * Ya'ni ro'yxat emas — HAR GURUH ALOHIDA TO'LIQ KARTA bo'lib, yonma-
 * yon turadi: o'qituvchi, dars kunlari, vaqt, kurs, holat, qo'shilgan
 * sana, xona va guruh narxi. Aynan LC UP dagidek.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Row = {
  id: number;
  group_id: number;
  group: string;
  subject?: string | null;
  level?: string | null;
  teacher?: string | null;
  lesson_days?: string | null;
  lesson_time?: string | null;
  room?: string | null;
  monthly_fee?: number | null;
  start_date?: string | null;
  lesson_price?: number | null;
  is_primary: boolean;
  active: boolean;
  /** Bolaning haqiqiy holati: faol / muzlatilgan / chiqarilgan. */
  status?: string | null;
  status_label?: string | null;
  joined_date?: string | null;
  left_date?: string | null;
  /** Shu guruhda necha oy bo'lgani. */
  months?: number | null;
};

const WD: Record<string, string> = {
  mon: "Dushanba", tue: "Seshanba", wed: "Chorshanba", thu: "Payshanba",
  fri: "Juma", sat: "Shanba", sun: "Yakshanba",
  "1": "Dushanba", "2": "Seshanba", "3": "Chorshanba", "4": "Payshanba",
  "5": "Juma", "6": "Shanba", "7": "Yakshanba",
};

function daysText(v?: string | null) {
  if (!v) return "—";
  return v
    .split(/[,\s]+/)
    .filter(Boolean)
    .map((d) => WD[d.toLowerCase()] || d)
    .join(", ");
}

function Row2({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 py-2">
      <span className="text-sm text-slate-500 shrink-0">{label}</span>
      <span className="text-sm text-slate-800 text-right">{value}</span>
    </div>
  );
}

export function StudentGroupsCard({
  studentId,
  allGroups,
  canEdit,
  onChanged,
}: {
  studentId: number;
  /** endi ishlatilmaydi — dublikat menyuga ko'chdi, chaqiruvchilar
   *  moslashguncha qoladi */
  studentName?: string;
  allGroups: { id: number; name: string; subject?: string | null }[];
  canEdit: boolean;
  onChanged?: () => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [adding, setAdding] = useState(false);
  const [pick, setPick] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function load() {
    api
      .fresh<{ rows: Row[] }>(`/students/${studentId}/groups`)
      .then((d) => setRows(d.rows || []))
      .catch(() => setRows([]));
  }
  useEffect(load, [studentId]);

  const active = rows.filter((r) => r.active);
  const closed = rows.filter((r) => !r.active);
  const taken = new Set(active.map((r) => r.group_id));

  async function add() {
    if (!pick) return;
    setBusy(true);
    setErr("");
    try {
      await api.post(`/students/${studentId}/groups`, {
        group_id: Number(pick),
      });
      setPick("");
      setAdding(false);
      load();
      onChanged?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Qo'shib bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  async function drop(r: Row) {
    if (!confirm(`"${r.group}" guruhidan chiqarilsinmi?`)) return;
    setErr("");
    try {
      await api.delete(`/students/${studentId}/groups/${r.group_id}`);
      load();
      onChanged?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Chiqarib bo'lmadi");
    }
  }

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm font-semibold text-slate-700 flex-1">
          Guruhlari
          {active.length > 1 && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 text-xs font-semibold">
              {active.length} ta fan
            </span>
          )}
        </p>
        {canEdit && !adding && (
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            <Plus size={14} /> Guruh qo'shish
          </button>
        )}
      </div>

      {err && (
        <p className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {err}
        </p>
      )}

      {adding && (
        <div className="mb-3 max-w-md bg-slate-50 border border-slate-200 rounded-xl p-3">
          <select
            value={pick}
            onChange={(e) => setPick(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
          >
            <option value="">— guruhni tanlang —</option>
            {allGroups
              .filter((g) => !taken.has(g.id))
              .map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                  {g.subject ? ` (${g.subject})` : ""}
                </option>
              ))}
          </select>
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => {
                setAdding(false);
                setPick("");
              }}
              className="flex-1 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm"
            >
              Bekor
            </button>
            <button
              onClick={add}
              disabled={busy || !pick}
              className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-50"
            >
              {busy ? "..." : "Qo'shish"}
            </button>
          </div>
        </div>
      )}

      {/* ---- LC UP dagidek: har guruh alohida karta, yonma-yon ---- */}
      <div className="grid gap-4 md:grid-cols-2">
        {active.map((r) => (
          <div
            key={r.id}
            className="border border-slate-200 rounded-xl overflow-hidden bg-white"
          >
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center gap-2">
              <Link
                to={`/groups/${r.group_id}`}
                className="font-semibold text-slate-900 hover:text-brand-700 flex-1 min-w-0 truncate"
              >
                {r.group}
              </Link>
              {r.is_primary && (
                <span title="Asosiy guruh — oylik hisob shu bo'yicha chiqadi">
                  <Star size={13} className="text-amber-500" fill="currentColor" />
                </span>
              )}
              {canEdit && active.length > 1 && (
                <button
                  onClick={() => drop(r)}
                  title="Shu guruhdan chiqarish"
                  className="p-1 rounded-lg text-slate-300 hover:text-red-600 hover:bg-red-50"
                >
                  <X size={15} />
                </button>
              )}
            </div>

            <div className="px-4 divide-y divide-slate-100">
              <Row2
                label="O'qituvchi"
                value={
                  <span className="text-brand-700">{r.teacher || "—"}</span>
                }
              />
              <Row2 label="Dars kunlari" value={daysText(r.lesson_days)} />
              <Row2 label="Vaqt" value={r.lesson_time || "—"} />
              {(r.subject || r.level) && (
                <Row2
                  label="Kursi"
                  value={
                    <span className="bg-brand-50 text-brand-700 rounded-md px-2 py-0.5 text-xs font-medium">
                      {[r.subject, r.level].filter(Boolean).join(" · ")}
                    </span>
                  }
                />
              )}
              {/* Holat qotirilgan "Faol" emas: muzlatilgan yoki
                  guruhdan chiqarilgan bola ham shu kartada turadi,
                  yolg'on yashil yorliq ekranga ishonchni yo'qotadi. */}
              <Row2
                label="Holati"
                value={
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                      !r.active || r.status === "left"
                        ? "bg-slate-100 text-slate-600"
                        : r.status === "frozen"
                        ? "bg-sky-50 text-sky-700"
                        : r.status === "archived"
                        ? "bg-slate-100 text-slate-600"
                        : "bg-green-50 text-green-700"
                    }`}
                  >
                    {r.status_label || (r.active ? "Faol" : "Guruhdan chiqarilgan")}
                  </span>
                }
              />
              <Row2
                label="Guruhga qo'shilgan sana"
                value={r.joined_date ? formatDate(r.joined_date) : "—"}
              />
              <Row2
                label="Boshlanish sanasi"
                value={r.start_date ? formatDate(r.start_date) : "—"}
              />
              {r.room && <Row2 label="Xona" value={r.room} />}
              <Row2
                label="Guruh narxi"
                value={formatSom(r.monthly_fee || 0)}
              />
            </div>

            <Link
              to={`/groups/${r.group_id}`}
              className="block text-center py-2.5 text-sm font-medium text-brand-600 hover:bg-brand-50 border-t border-slate-200"
            >
              Davomat &amp; Baho →
            </Link>
          </div>
        ))}
      </div>

      {active.length === 0 && (
        <p className="text-sm text-slate-400 py-6 text-center">
          O'quvchi hech qaysi guruhga biriktirilmagan.
        </p>
      )}

      {/* GURUH TARIXI (2026-09-24, Jahongir: "avval qaysi guruhda
          bo'lgani xozirda qaysi guruhda ekani ko'rinsin"). Ilgari
          bu yerda bitta kulrang qator turardi — qachondan qachongacha
          va qaysi ustozda o'qigani ko'rinmasdi. */}
      {closed.length > 0 && (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Avvalgi guruhlari
          </p>
          <div className="space-y-1.5">
            {closed.map((r) => (
              <div
                key={r.id}
                className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-sm"
              >
                <span className="text-slate-700">{r.group}</span>
                {r.teacher && (
                  <span className="text-xs text-slate-500">{r.teacher}</span>
                )}
                <span className="text-xs text-slate-500">
                  {r.joined_date ? formatDate(r.joined_date) : "—"} →{" "}
                  {r.left_date ? formatDate(r.left_date) : "—"}
                </span>
                {r.months != null && (
                  <span className="text-xs text-slate-400">
                    {r.months} oy
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {active.length > 1 && (
        <p className="mt-3 max-w-2xl text-[12px] text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 leading-snug">
          {active.length} ta fan — har bir fanning oyligi alohida yechiladi va
          har biriga <b>10% chegirma</b> avtomat qo'llanadi. Oy o'rtasida
          qo'shilgan fan qo'shilgan kunidan, chiqarilgan fan chiqqan kunigacha
          hisoblanadi.
        </p>
      )}
    </div>
  );
}
