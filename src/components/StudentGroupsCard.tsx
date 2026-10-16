import { useEffect, useRef, useState } from "react";
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
  /** Bog'lanishning o'z holati (2026-10-14): "trial" — shu guruh
   *  sinovda, pul yechilmaydi; "active" — faol. */
  link_status?: "trial" | "active" | "frozen" | string | null;
  activated_on?: string | null;
  /** Faqat shu guruhda muzlatilgan (2026-10-16). */
  frozen_from?: string | null;
  frozen_until?: string | null;
  frozen_note?: string | null;
};

const todayIso = () => {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

/** "Faollashtirish" oynasi uchun server hisobi (hech narsa yozmaydi). */
type Preview = {
  on: string;
  min: string;
  max: string;
  lessons: number;
  price: number;
  discount: number;
  amount: number;
  /** Shu oy shu guruh qatori allaqachon bor (guruhdan chiqib qayta
   *  qo'shilgan) — yuqoridagi summa unga QO'SHILADI (2026-10-14). */
  existing?: { lessons: number; amount: number } | null;
  family: boolean;
  multi_applies: boolean;
  primary_discount_now: number;
  primary_discount_after: number;
  error?: string | null;
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
  // Pul yechiladigan (sinovda bo'lmagan) guruhlar — 10% faqat shular
  // 2 tadan ko'p bo'lsa (2026-10-14).
  const paid = active.filter(
    (r) => r.link_status !== "trial" && r.link_status !== "frozen"
  );
  const trials = active.filter((r) => r.link_status === "trial");

  // ---- GURUH BO'YICHA MUZLATISH (2026-10-16, Jahongir: "ikkalasi
  // alohida alohida muzlatish kerak") ----
  const [fzRow, setFzRow] = useState<Row | null>(null);
  const [fzMode, setFzMode] = useState<"freeze" | "unfreeze">("freeze");
  const [fzFrom, setFzFrom] = useState(todayIso());
  const [fzUntil, setFzUntil] = useState("");
  const [fzNote, setFzNote] = useState("");
  const [fzBusy, setFzBusy] = useState(false);

  function openFz(r: Row, mode: "freeze" | "unfreeze") {
    setErr("");
    setFzRow(r);
    setFzMode(mode);
    setFzFrom(todayIso());
    setFzUntil("");
    setFzNote("");
  }

  async function submitFz() {
    if (!fzRow) return;
    setFzBusy(true);
    setErr("");
    try {
      if (fzMode === "freeze") {
        await api.post(
          `/students/${studentId}/groups/${fzRow.group_id}/freeze`,
          { from_date: fzFrom, until: fzUntil || null, note: fzNote || null }
        );
      } else {
        await api.post(
          `/students/${studentId}/groups/${fzRow.group_id}/unfreeze`,
          { on: fzFrom }
        );
      }
      setFzRow(null);
      load();
      onChanged?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Bajarib bo'lmadi");
    } finally {
      setFzBusy(false);
    }
  }

  // ---- "Faollashtirish": sana tanlanadi, server hisobni ko'rsatadi ----
  const [actRow, setActRow] = useState<Row | null>(null);
  const [actDate, setActDate] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [actBusy, setActBusy] = useState(false);
  // Eng oxirgi so'ralgan sana — kechikib kelgan eski javob yangisini
  // bosib ketmasin.
  const lastAsk = useRef("");

  function loadPreview(r: Row, on?: string) {
    const q = on ? `?on=${encodeURIComponent(on)}` : "";
    const ask = `${r.group_id}|${on || ""}`;
    lastAsk.current = ask;
    setPreview(null);
    api
      .fresh<Preview>(
        `/students/${studentId}/groups/${r.group_id}/activate-preview${q}`
      )
      .then((p) => {
        if (lastAsk.current !== ask) return;
        setPreview(p);
        if (!on) setActDate(p.on);
      })
      .catch((e) => {
        setPreview(null);
        setErr(e instanceof Error ? e.message : "Hisobni olib bo'lmadi");
      });
  }

  function openActivate(r: Row) {
    setErr("");
    setActRow(r);
    setPreview(null);
    setActDate("");
    loadPreview(r);
  }

  async function activate() {
    if (!actRow || !actDate) return;
    setActBusy(true);
    setErr("");
    try {
      await api.post(
        `/students/${studentId}/groups/${actRow.group_id}/activate`,
        { on: actDate }
      );
      setActRow(null);
      setPreview(null);
      load();
      onChanged?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Faollashtirib bo'lmadi");
    } finally {
      setActBusy(false);
    }
  }

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
          {/* 2026-10-14, Jahongir: "Avval qo'shilganda sinovda bo'lishi
              kerak keyin faollashtirilsa pul yechsin". Guruhsiz
              o'quvchining birinchi guruhi avvalgidek. */}
          {active.length > 0 && (
            <p className="mt-2 text-[12px] leading-snug text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
              Guruh <b>«Sinov»</b> sifatida qo'shiladi — pul yechilmaydi va
              10% chegirmaga kirmaydi. <b>«Faollashtirish»</b> bosilganda
              (yoki shu guruhda 3 ta darsga kelgach avtomat) tanlangan
              kundan oy oxirigacha darslar soniga qarab yechiladi.
            </p>
          )}
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
              {/* Bog'lanish holati (2026-10-14): sinovdagi guruh
                  sarlavhada ham ajralib tursin; "Faol"/"Sinov" yozuvi
                  pastdagi "Holati" qatorida. */}
              {r.link_status === "trial" && (
                <span
                  title="Shu guruh sinovda — pul yechilmaydi"
                  className="shrink-0 rounded-full bg-amber-100 text-amber-800 px-2 py-0.5 text-[11px] font-semibold"
                >
                  Sinov
                </span>
              )}
              {r.link_status === "frozen" && (
                <span
                  title="Faqat shu guruhda muzlatilgan — boshqa guruhida o'qiydi"
                  className="shrink-0 rounded-full bg-sky-100 text-sky-800 px-2 py-0.5 text-[11px] font-semibold"
                >
                  Muzlatilgan
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
                        : r.status === "trial" || r.link_status === "trial"
                        ? "bg-amber-50 text-amber-800"
                        : "bg-green-50 text-green-700"
                    }`}
                  >
                    {r.status_label ||
                      (!r.active
                        ? "Guruhdan chiqarilgan"
                        : r.link_status === "trial"
                        ? "Sinov"
                        : "Faol")}
                  </span>
                }
              />
              {r.activated_on && r.link_status !== "trial" && (
                <Row2
                  label="Faollashgan sana"
                  value={formatDate(r.activated_on)}
                />
              )}
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

            {/* SINOVDAGI GURUHNI FAOLLASHTIRISH (2026-10-14, Jahongir:
                "Sinovdan faolga o'tganda pul yechilishi dars sonidan
                kelib chiqsin"). Sana tanlanadi — server shu kundan oy
                oxirigacha darslar x narx x chegirmani ko'rsatadi. */}
            {canEdit && r.link_status === "trial" && actRow?.id !== r.id && (
              <div className="px-4 pb-3">
                <button
                  onClick={() => openActivate(r)}
                  className="w-full py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium"
                >
                  Faollashtirish
                </button>
              </div>
            )}
            {actRow?.id === r.id && (
              <div className="mx-4 mb-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm">
                <label className="block text-[12px] text-slate-600 mb-1">
                  Qaysi kundan faol (pul shu kundan yechiladi)
                </label>
                <input
                  type="date"
                  value={actDate}
                  min={preview?.min}
                  max={preview?.max}
                  onChange={(e) => {
                    setActDate(e.target.value);
                    if (e.target.value) loadPreview(r, e.target.value);
                  }}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
                />
                {preview ? (
                  <div className="mt-2 space-y-1 text-[13px] text-slate-700">
                    <p>
                      {preview.lessons} dars × {formatSom(preview.price)}
                      {preview.discount > 0 && (
                        <> × (1 − {preview.discount}%)</>
                      )}{" "}
                      = <b>{formatSom(preview.amount)}</b>
                    </p>
                    {preview.multi_applies &&
                      preview.primary_discount_after >
                        preview.primary_discount_now && (
                        <p className="text-[12px] text-emerald-800">
                          Asosiy guruh hisobiga ham 10% (2 fan) qo'llanadi.
                        </p>
                      )}
                    {preview.family && (
                      <p className="text-[12px] text-slate-600">
                        Oilaviy chegirma bor — 2 fan chegirmasi
                        qo'llanmaydi.
                      </p>
                    )}
                    {preview.existing && (
                      <p className="text-[12px] text-slate-600">
                        Bu oy shu guruh uchun avval{" "}
                        {preview.existing.lessons} dars hisoblangan (
                        {formatSom(preview.existing.amount)}) — yuqoridagi
                        summa shunga qo'shiladi (oyda standartdan oshmaydi).
                      </p>
                    )}
                    {preview.error && (
                      <p className="text-[12px] text-red-600">
                        {preview.error}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="mt-2 text-[12px] text-slate-500">
                    Hisoblanmoqda...
                  </p>
                )}
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => {
                      setActRow(null);
                      setPreview(null);
                    }}
                    className="flex-1 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 text-sm"
                  >
                    Bekor
                  </button>
                  <button
                    onClick={activate}
                    disabled={
                      actBusy || !actDate || !preview || !!preview.error
                    }
                    className="flex-1 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium disabled:opacity-50"
                  >
                    {actBusy ? "..." : "Faollashtirish"}
                  </button>
                </div>
              </div>
            )}

            {/* GURUH BO'YICHA MUZLATISH (2026-10-16): faqat shu guruh
                to'xtaydi, ikkinchi guruh ishlayveradi. Yagona faol guruh
                bo'lsa — butun o'quvchi (⋮ menyu → Muzlatish). */}
            {r.link_status === "frozen" && r.frozen_from && (
              <p className="mx-4 mb-2 text-[12px] text-sky-800 bg-sky-50 border border-sky-200 rounded-lg px-2.5 py-1.5">
                {formatDate(r.frozen_from)} dan faqat shu guruhda muzlatilgan
                {r.frozen_until ? ` · qaytish: ${formatDate(r.frozen_until)}` : ""}
                {r.frozen_note ? ` · ${r.frozen_note}` : ""}
              </p>
            )}
            {canEdit && fzRow?.id !== r.id && (
              (r.link_status === "frozen" ||
                (r.link_status !== "trial" && paid.length > 1)) && (
                <div className="px-4 pb-3">
                  <button
                    onClick={() =>
                      openFz(r, r.link_status === "frozen" ? "unfreeze" : "freeze")
                    }
                    className={`w-full py-2 rounded-lg text-sm font-medium border ${
                      r.link_status === "frozen"
                        ? "bg-sky-600 hover:bg-sky-700 text-white border-sky-600"
                        : "bg-white hover:bg-sky-50 text-sky-700 border-sky-200"
                    }`}
                  >
                    {r.link_status === "frozen"
                      ? "Shu guruhda faollashtirish"
                      : "Faqat shu guruhni muzlatish"}
                  </button>
                </div>
              )
            )}
            {fzRow?.id === r.id && (
              <div className="mx-4 mb-3 rounded-xl border border-sky-200 bg-sky-50 p-3 text-sm space-y-2">
                <label className="block text-[12px] text-slate-600">
                  {fzMode === "freeze"
                    ? "Qaysi kundan muzlatiladi (shu kundan pul yechilmaydi)"
                    : "Qaysi kundan qaytadi (shu kundan oy oxirigacha pul yechiladi)"}
                </label>
                <input
                  type="date"
                  value={fzFrom}
                  max={todayIso()}
                  onChange={(e) => setFzFrom(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
                />
                {fzMode === "freeze" && (
                  <>
                    <label className="block text-[12px] text-slate-600">
                      Qaytish sanasi (ixtiyoriy)
                    </label>
                    <input
                      type="date"
                      value={fzUntil}
                      onChange={(e) => setFzUntil(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
                    />
                    <input
                      value={fzNote}
                      onChange={(e) => setFzNote(e.target.value)}
                      placeholder="Sabab (ixtiyoriy)"
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
                    />
                    <p className="text-[12px] text-slate-600">
                      Boshqa guruhida o'qishda davom etadi. Shu oy hisobi
                      muzlatilgan kungacha bo'lgan darslarga tushiriladi.
                    </p>
                  </>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => setFzRow(null)}
                    className="flex-1 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 text-sm"
                  >
                    Bekor
                  </button>
                  <button
                    onClick={submitFz}
                    disabled={fzBusy || !fzFrom}
                    className="flex-1 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-sm font-medium disabled:opacity-50"
                  >
                    {fzBusy
                      ? "..."
                      : fzMode === "freeze"
                      ? "Muzlatish"
                      : "Faollashtirish"}
                  </button>
                </div>
              </div>
            )}

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

      {paid.length > 1 && (
        <p className="mt-3 max-w-2xl text-[12px] text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 leading-snug">
          {paid.length} ta fan — har bir fanning oyligi alohida yechiladi va
          har biriga <b>10% chegirma</b> avtomat qo'llanadi (oilaviy chegirma
          bo'lsa 2 fan chegirmasi qo'llanmaydi). Oy o'rtasida faollashgan fan
          faollashgan kunidan, chiqarilgan fan chiqqan kunigacha hisoblanadi.
        </p>
      )}
      {trials.length > 0 && (
        <p className="mt-3 max-w-2xl text-[12px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 leading-snug">
          «Sinov»dagi guruh pul yechmaydi va 10% chegirmaga kirmaydi.
          «Faollashtirish» bosilganda yoki shu guruhda 3 ta darsga kelgach
          avtomat faol bo'ladi — pul faollashgan kundan oy oxirigacha darslar
          soniga qarab yechiladi.
        </p>
      )}
    </div>
  );
}
