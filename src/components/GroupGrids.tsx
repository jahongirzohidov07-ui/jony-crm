import { useEffect, useState } from "react";
import { Check, X, Plus, Trash2, Coins, CalendarClock } from "lucide-react";
import {
  api,
  type AttendanceGrid,
  type Exam,
  type ExamDetail,
  type ExamKind,
} from "../lib/api";
import {
  EXAM_KINDS,
  UNIT_COUNT,
  MOCK_MAX_BAND,
  examTitle,
  examKindLabel,
  gradeTone,
} from "../lib/exams";
import { formatDate } from "../lib/format";

/** Sana ustuni sarlavhasi: "01 iyul" ko'rinishida qisqa. */
const SHORT_MONTHS = [
  "yan", "fev", "mar", "apr", "may", "iyun",
  "iyul", "avg", "sen", "okt", "noy", "dek",
];

function dayLabel(iso: string): string {
  const [, m, d] = iso.split("-").map(Number);
  return `${String(d).padStart(2, "0")} ${SHORT_MONTHS[m - 1]}`;
}

function EmptyState({ text }: { text: string }) {
  return <p className="text-sm text-slate-400 py-6 text-center">{text}</p>;
}

// ------------------------------------------------------------- Davomat ----

/** Bitta katak uchun tanlov oynasi.
 *
 *  Ilgari katak bosilganda holat aylanardi: bo'sh → keldi → kelmadi →
 *  keldi. Bu tez, lekin xato ham tez bo'ladi — noto'g'ri holatga
 *  o'tib ketilsa yana ikki marta bosish kerak. Endi ustoz nimani
 *  qo'yayotganini KO'RIB tanlaydi. */
function MarkPicker({
  present,
  homework,
  onPresent,
  onHomework,
  onClose,
}: {
  present?: boolean;
  homework?: number;
  onPresent: (v: boolean) => void;
  onHomework: (v: number) => void;
  onClose: () => void;
}) {
  return (
    <div
      className="absolute z-30 left-1/2 -translate-x-1/2 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg p-2 w-40"
      onMouseLeave={onClose}
    >
      <p className="text-[10px] uppercase text-slate-400 px-1 mb-1">
        Davomat
      </p>
      <div className="flex gap-1 mb-2">
        <button
          onClick={() => onPresent(true)}
          className={`flex-1 rounded-lg py-1.5 text-xs font-medium border transition ${
            present === true
              ? "bg-brand-500 border-brand-500 text-white"
              : "border-slate-200 text-slate-600 hover:bg-brand-50"
          }`}
        >
          Bor
        </button>
        <button
          onClick={() => onPresent(false)}
          className={`flex-1 rounded-lg py-1.5 text-xs font-medium border transition ${
            present === false
              ? "bg-red-500 border-red-500 text-white"
              : "border-slate-200 text-slate-600 hover:bg-red-50"
          }`}
        >
          Yo'q
        </button>
      </div>

      <p className="text-[10px] uppercase text-slate-400 px-1 mb-1">
        Uy vazifasi
      </p>
      <div className="flex gap-1">
        {[
          { v: 1, label: "✓", title: "Bajardi", on: "bg-emerald-500" },
          { v: 2, label: "±", title: "Qisman", on: "bg-amber-500" },
          { v: 0, label: "✗", title: "Bajarmadi", on: "bg-red-500" },
        ].map((h) => (
          <button
            key={h.v}
            title={h.title}
            onClick={() => onHomework(h.v)}
            className={`flex-1 rounded-lg py-1.5 text-xs font-bold border transition ${
              homework === h.v
                ? `${h.on} border-transparent text-white`
                : "border-slate-200 text-slate-500 hover:bg-slate-50"
            }`}
          >
            {h.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Sana sarlavhasi menyusi: dars holati va "Dars ko'chirish". */
function DateMenu({
  date,
  held,
  box,
  moved,
  onMove,
  onClose,
}: {
  date: string;
  held: number;
  box: NonNullable<AttendanceGrid["reschedule"]>;
  moved?: { status_label: string; to_date: string };
  onMove: () => void;
  onClose: () => void;
}) {
  const past = date < new Date().toISOString().slice(0, 10);
  const q = box.quota;
  return (
    <div className="absolute z-40 left-1/2 -translate-x-1/2 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg p-3 w-60 text-left">
      <p className="text-sm font-medium text-slate-900">
        {formatDate(date)}
      </p>
      <p className="text-xs text-slate-500 mb-2">
        {held ? "Dars o'tilgan" : "Jadval bo'yicha reja"}
      </p>

      {moved ? (
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-2 mb-2">
          <p className="text-xs text-slate-700">
            {formatDate(moved.to_date)} ga ko'chirilgan
          </p>
          <p className="text-[11px] text-slate-400">{moved.status_label}</p>
        </div>
      ) : !box.can ? (
        <p className="text-xs text-slate-400 mb-2">
          Dars ko'chirish huquqingiz yo'q.
        </p>
      ) : held ? (
        <p className="text-xs text-slate-400 mb-2">
          O'tilgan darsni ko'chirib bo'lmaydi — u ish haqi asosi.
        </p>
      ) : past ? (
        <p className="text-xs text-slate-400 mb-2">
          O'tib ketgan darsni ko'chirib bo'lmaydi.
        </p>
      ) : (
        <button
          onClick={onMove}
          className="w-full flex items-center justify-center gap-1.5 bg-brand-600 text-white rounded-lg py-2 text-sm font-medium mb-2"
        >
          <CalendarClock size={14} />
          Dars ko'chirish
        </button>
      )}

      {q && (
        <p className="text-[11px] text-slate-500">
          Shu oyda {q.used_month}/{q.per_month} ishlatilgan
          {q.left != null ? ` · ${q.left} ta qoldi` : ""}
        </p>
      )}
      <p className="text-[11px] text-slate-400 mt-1">{box.cannot_cancel}</p>

      <button
        onClick={onClose}
        className="w-full text-xs text-slate-400 mt-2 hover:text-slate-600"
      >
        Yopish
      </button>
    </div>
  );
}

export function AttendanceTab({
  groupId,
  year,
  month,
  canEdit,
}: {
  groupId: number;
  year: number;
  month: number;
  canEdit: boolean;
}) {
  const [grid, setGrid] = useState<AttendanceGrid | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null); // ochiq katak
  const [menu, setMenu] = useState<number | null>(null); // ochiq sana
  const [moving, setMoving] = useState<{ id: number; date: string } | null>(
    null
  );

  const load = () => {
    setLoading(true);
    api
      .get<AttendanceGrid>(
        `/groups/${groupId}/attendance?year=${year}&month=${month}`
      )
      .then(setGrid)
      .finally(() => setLoading(false));
  };
  useEffect(load, [groupId, year, month]);

  /** Davomat — aniq qiymat bilan saqlanadi, aylanma emas. */
  async function setPresent(
    lessonId: number,
    studentId: number,
    next: boolean
  ) {
    if (!canEdit || !grid) return;
    const key = `${lessonId}:${studentId}`;
    const before = grid.marks[key];
    setGrid({ ...grid, marks: { ...grid.marks, [key]: next } });
    setSaving(key);
    try {
      await api.put(`/lessons/${lessonId}/attendance`, {
        marks: [{ student_id: studentId, present: next }],
      });
    } catch {
      setGrid({ ...grid, marks: { ...grid.marks, [key]: before } });
    } finally {
      setSaving(null);
    }
  }

  /** Uy vazifasi davomat bilan bitta oynada — alohida ekran bo'lsa
   *  hech kim to'ldirmaydi. */
  async function setHomework(
    lessonId: number,
    studentId: number,
    next: number
  ) {
    if (!canEdit || !grid) return;
    const key = `${lessonId}:${studentId}`;
    const hw = { ...(grid.homework || {}), [key]: next };
    const marks = { ...grid.marks };
    // Uy vazifasi belgilandi — demak bola darsda bo'lgan
    if (marks[key] === undefined) marks[key] = true;
    setGrid({ ...grid, homework: hw, marks });
    setSaving(key);
    try {
      await api.put(`/lessons/${lessonId}/attendance`, {
        marks: [
          {
            student_id: studentId,
            present: marks[key] === true,
            homework: next,
          },
        ],
      });
    } catch {
      load();
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (!grid) return null;
  if (grid.lessons.length === 0)
    return (
      <EmptyState text="Bu oyda dars kuni yo'q. Guruhni tahrirlab dars kunlarini (masalan Dushanba, Chorshanba, Juma) tanlang — butun oy jadvali avtomat chiqadi." />
    );
  if (grid.students.length === 0)
    return <EmptyState text="Guruhda o'quvchi yo'q" />;

  const total = grid.lessons.length * grid.students.length;
  const present = Object.values(grid.marks).filter((v) => v === true).length;
  const marked = Object.keys(grid.marks).length;
  const heldCount = grid.lessons.filter((l) => l.held).length;
  const box = grid.reschedule;

  return (
    <div>
      <p className="text-xs text-slate-500 mb-3">
        {grid.lessons.length} dars kuni ({heldCount} o'tilgan) ·{" "}
        {grid.students.length} o'quvchi
        {marked > 0 && (
          <>
            {" "}
            · davomat{" "}
            <span className="font-medium text-slate-700">
              {Math.round((present / marked) * 100)}%
            </span>{" "}
            ({present}/{marked} belgilangan, jami {total})
          </>
        )}
      </p>

      <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
        <table className="text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50">
              <th className="sticky left-0 z-10 bg-slate-50 text-left px-4 py-3 font-medium text-xs uppercase text-slate-500 min-w-[200px] border-r border-slate-200">
                Talabalar
              </th>
              {grid.lessons.map((ls) => {
                const mv = box?.moved?.[ls.date];
                return (
                  <th
                    key={ls.id}
                    className="px-2 py-2 font-medium min-w-[76px] relative"
                  >
                    <button
                      onClick={() => setMenu(menu === ls.id ? null : ls.id)}
                      className={`text-xs whitespace-nowrap px-1.5 py-1 rounded-lg hover:bg-slate-200 transition ${
                        ls.held ? "text-slate-700" : "text-slate-400"
                      } ${mv ? "line-through" : ""}`}
                      title="Menyu: dars ko'chirish"
                    >
                      {dayLabel(ls.date)}
                    </button>
                    {menu === ls.id && box && (
                      <DateMenu
                        date={ls.date}
                        held={ls.held}
                        box={box}
                        moved={mv}
                        onMove={() => {
                          setMenu(null);
                          setMoving({ id: ls.id, date: ls.date });
                        }}
                        onClose={() => setMenu(null)}
                      />
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {grid.students.map((s, i) => (
              <tr key={s.id} className="border-t border-slate-100">
                <td className="sticky left-0 z-10 bg-white px-4 py-2.5 text-slate-800 whitespace-nowrap border-r border-slate-200">
                  <span className="text-slate-400 mr-2 text-xs">{i + 1}</span>
                  {s.full_name}
                </td>
                {grid.lessons.map((ls) => {
                  const key = `${ls.id}:${s.id}`;
                  const v = grid.marks[key];
                  const h = grid.homework?.[key];
                  return (
                    <td
                      key={ls.id}
                      className="px-2 py-2 text-center relative"
                      onMouseEnter={() => canEdit && setOpen(key)}
                      onMouseLeave={() =>
                        setOpen((k) => (k === key ? null : k))
                      }
                    >
                      <button
                        onClick={() => setOpen(open === key ? null : key)}
                        disabled={!canEdit || saving === key}
                        className={`w-8 h-8 rounded-lg inline-flex items-center justify-center transition relative ${
                          v === true
                            ? "bg-brand-500 text-white"
                            : v === false
                            ? "bg-red-500 text-white"
                            : "bg-slate-100 hover:bg-slate-200"
                        } ${canEdit ? "cursor-pointer" : "cursor-default"}`}
                      >
                        {v === true ? (
                          <Check size={15} />
                        ) : v === false ? (
                          <X size={15} />
                        ) : null}
                        {h !== undefined && (
                          <span
                            title={
                              h === 1
                                ? "Uy vazifasi: bajardi"
                                : h === 2
                                ? "Uy vazifasi: qisman"
                                : "Uy vazifasi: bajarmadi"
                            }
                            className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
                              h === 1
                                ? "bg-emerald-500"
                                : h === 2
                                ? "bg-amber-500"
                                : "bg-red-500"
                            }`}
                          />
                        )}
                      </button>
                      {open === key && canEdit && (
                        <MarkPicker
                          present={v as boolean | undefined}
                          homework={h}
                          onPresent={(x) => setPresent(ls.id, s.id, x)}
                          onHomework={(x) => setHomework(ls.id, s.id, x)}
                          onClose={() => setOpen(null)}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 mt-3">
        Katak ustiga sichqonchani olib boring — <b>Bor</b> yoki{" "}
        <b>Yo'q</b> ni tanlang. Shu yerda uy vazifasi ham belgilanadi
        (burchakdagi nuqta): yashil bajardi, sariq qisman, qizil bajarmadi.
        Har bir o'quvchi alohida belgilanadi — ommaviy belgilash yo'q,
        chunki u yoqlamani rasmiyatchilikka aylantiradi. Sana ustiga
        bosilsa dars ko'chirish menyusi chiqadi. Kulrang sana — hali
        yoqlama qo'yilmagan reja; u pulga ham, ustoz ish haqiga ham
        kirmaydi.
      </p>

      {moving && box && (
        <MoveLessonModal
          groupId={groupId}
          fromDate={moving.date}
          box={box}
          onClose={() => setMoving(null)}
          onDone={() => {
            setMoving(null);
            load();
          }}
        />
      )}
    </div>
  );
}

/** Dars ko'chirish oynasi. Bekor qilish tugmasi ATAYLAB yo'q. */
function MoveLessonModal({
  groupId,
  fromDate,
  box,
  onClose,
  onDone,
}: {
  groupId: number;
  fromDate: string;
  box: NonNullable<AttendanceGrid["reschedule"]>;
  onClose: () => void;
  onDone: () => void;
}) {
  const [to, setTo] = useState("");
  const [reason, setReason] = useState(box.reasons[0]?.key || "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const min = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
  const max = new Date(
    new Date(fromDate).getTime() + box.max_shift_days * 86400000
  )
    .toISOString()
    .slice(0, 10);

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<{ message: string; applied: boolean }>(
        `/groups/${groupId}/reschedule`,
        { from_date: fromDate, to_date: to, reason, note: note || null }
      );
      setOk(r.message);
      setTimeout(onDone, 1200);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-900">Darsni ko'chirish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">
          {formatDate(fromDate)} darsi
        </p>

        {ok ? (
          <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            {ok}
          </p>
        ) : (
          <>
            <label className="block text-xs text-slate-500 mb-1">
              Yangi sana
            </label>
            <input
              type="date"
              value={to}
              min={min}
              max={max}
              onChange={(e) => setTo(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
            />

            <label className="block text-xs text-slate-500 mb-1">Sabab</label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
            >
              {box.reasons.map((r) => (
                <option key={r.key} value={r.key}>
                  {r.label}
                </option>
              ))}
            </select>

            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              placeholder="Izoh (ixtiyoriy)"
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
            />

            {box.quota && (
              <p className="text-xs text-slate-500 mb-2">
                Shu oyda {box.quota.used_month}/{box.quota.per_month}{" "}
                ishlatilgan.
                {box.quota.auto_ok
                  ? " Bu so'rov avtomat tasdiqlanadi."
                  : " Kvota tugagan — so'rov o'quv bo'limiga boradi."}
              </p>
            )}
            {box.hint && (
              <p className="text-xs text-slate-400 mb-3">{box.hint}</p>
            )}

            {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
            <button
              onClick={save}
              disabled={busy || !to}
              className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
            >
              Ko'chirish
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------ Baholash ----
export function GradesTab({
  groupId,
  year,
  month,
  canEdit,
}: {
  groupId: number;
  year: number;
  month: number;
  canEdit: boolean;
}) {
  const [grid, setGrid] = useState<AttendanceGrid | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<AttendanceGrid>(`/groups/${groupId}/grades?year=${year}&month=${month}`)
      .then(setGrid)
      .finally(() => setLoading(false));
  }, [groupId, year, month]);

  /** Bosilganda 1→2→3→4→5→bo'sh aylanadi. Har ball shuncha coin beradi. */
  async function cycle(lessonId: number, studentId: number) {
    if (!canEdit || !grid) return;
    const key = `${lessonId}:${studentId}`;
    const current = grid.marks[key] as number | undefined;
    const next = current === undefined ? 5 : current === 1 ? null : current - 1;

    const marks = { ...grid.marks };
    if (next === null) delete marks[key];
    else marks[key] = next;
    setGrid({ ...grid, marks });

    try {
      await api.put(`/lessons/${lessonId}/grades`, {
        marks: [{ student_id: studentId, score: next }],
      });
    } catch {
      setGrid({ ...grid, marks: grid.marks });
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (!grid) return null;
  if (grid.lessons.length === 0)
    return <EmptyState text="Bu oyda hali dars belgilanmagan" />;
  if (grid.students.length === 0)
    return <EmptyState text="Guruhda o'quvchi yo'q" />;

  const scores = Object.values(grid.marks) as number[];
  const avg = scores.length
    ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
    : null;
  const coinTotal = scores.reduce((a, b) => a + b, 0);

  return (
    <div>
      <p className="text-xs text-slate-500 mb-3">
        {grid.lessons.length} dars
        {avg && (
          <>
            {" "}
            · o'rtacha baho{" "}
            <span className="font-medium text-slate-700">{avg}</span> · bu oyda{" "}
            <span className="font-medium text-brand-700">{coinTotal} coin</span>{" "}
            berilgan
          </>
        )}
      </p>

      <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
        <table className="text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50">
              <th className="sticky left-0 z-10 bg-slate-50 text-left px-4 py-3 font-medium text-xs uppercase text-slate-500 min-w-[200px] border-r border-slate-200">
                Talabalar
              </th>
              {grid.lessons.map((ls) => (
                <th
                  key={ls.id}
                  className="px-2 py-3 font-medium min-w-[70px] text-xs text-slate-600 whitespace-nowrap"
                >
                  {dayLabel(ls.date)}
                </th>
              ))}
              <th className="px-3 py-3 text-xs uppercase text-slate-500 font-medium">
                Coin
              </th>
            </tr>
          </thead>
          <tbody>
            {grid.students.map((s, i) => {
              const rowScores = grid.lessons
                .map((ls) => grid.marks[`${ls.id}:${s.id}`] as number | undefined)
                .filter((v): v is number => typeof v === "number");
              const rowCoins = rowScores.reduce((a, b) => a + b, 0);
              return (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="sticky left-0 z-10 bg-white px-4 py-2.5 text-slate-800 whitespace-nowrap border-r border-slate-200">
                    <span className="text-slate-400 mr-2 text-xs">{i + 1}</span>
                    {s.full_name}
                  </td>
                  {grid.lessons.map((ls) => {
                    const v = grid.marks[`${ls.id}:${s.id}`] as number | undefined;
                    return (
                      <td key={ls.id} className="px-2 py-2 text-center">
                        <button
                          onClick={() => cycle(ls.id, s.id)}
                          disabled={!canEdit}
                          className={`w-8 h-8 rounded-lg inline-flex items-center justify-center font-semibold text-sm transition ${
                            v ? gradeTone(v) : "bg-slate-100 hover:bg-slate-200"
                          }`}
                        >
                          {v ?? ""}
                        </button>
                      </td>
                    );
                  })}
                  <td className="px-3 py-2 text-center font-medium text-brand-700 whitespace-nowrap">
                    {rowCoins || "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 mt-3">
        Katakni bosing — baho 5 dan 1 gacha aylanadi, yana bossangiz o'chadi.
        Har bir ball shuncha coin beradi (5 baho = 5 coin) va o'quvchi
        balansiga o'zi tushadi.
      </p>
    </div>
  );
}

// --------------------------------------------------------- Imtihonlar ----
function ExamForm({
  groupId,
  onClose,
  onCreated,
}: {
  groupId: number;
  onClose: () => void;
  onCreated: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [kind, setKind] = useState<ExamKind>("unit");
  const [unitNo, setUnitNo] = useState("1");
  const [date, setDate] = useState(today);
  const [maxScore, setMaxScore] = useState("50");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await api.post(`/groups/${groupId}/exams`, {
        kind,
        unit_no: kind === "unit" ? Number(unitNo) : null,
        date,
        max_score: kind === "mock" ? null : Number(maxScore),
      });
      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Yangi test</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Turi
            </label>
            <div className="flex flex-wrap gap-1.5">
              {EXAM_KINDS.map((k) => (
                <button
                  key={k.key}
                  type="button"
                  onClick={() => setKind(k.key as ExamKind)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                    kind === k.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {k.label}
                </button>
              ))}
            </div>
          </div>

          {kind === "unit" && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Unit raqami
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={unitNo}
                onChange={(e) => setUnitNo(e.target.value)}
              >
                {Array.from({ length: UNIT_COUNT }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    Unit {n}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Sana
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
            {kind !== "mock" && (
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  Maksimal ball
                </label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={maxScore}
                  onChange={(e) => setMaxScore(e.target.value)}
                />
              </div>
            )}
          </div>

          {kind === "mock" && (
            <p className="text-xs text-slate-400">
              Mock testda ball emas, IELTS band (0–{MOCK_MAX_BAND}) kiritiladi.
            </p>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-1 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Yaratish"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ExamSheet({
  examId,
  canEdit,
  onBack,
  onChanged,
}: {
  examId: number;
  canEdit: boolean;
  onBack: () => void;
  onChanged: () => void;
}) {
  const [exam, setExam] = useState<ExamDetail | null>(null);
  const [draft, setDraft] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<ExamDetail>(`/exams/${examId}`).then((d) => {
      setExam(d);
      const next: Record<number, string> = {};
      for (const r of d.results) {
        if (r.absent) next[r.student_id] = "";
        else next[r.student_id] = String(d.kind === "mock" ? r.band ?? "" : r.score ?? "");
      }
      setDraft(next);
    });
  }

  useEffect(load, [examId]);
  if (!exam) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  const isMock = exam.kind === "mock";
  const byStudent = Object.fromEntries(exam.results.map((r) => [r.student_id, r]));

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const marks = exam!.students
        .map((s) => {
          const raw = (draft[s.id] ?? "").trim();
          if (raw === "") {
            // Bo'sh qoldirilgan katak = kelmagan deb belgilanadi
            return byStudent[s.id]
              ? { student_id: s.id, absent: true }
              : null;
          }
          const num = Number(raw);
          if (Number.isNaN(num)) return null;
          return isMock
            ? { student_id: s.id, band: num, absent: false }
            : { student_id: s.id, score: num, absent: false };
        })
        .filter(Boolean);
      const updated = await api.put<ExamDetail>(`/exams/${examId}/results`, { marks });
      setExam(updated);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <button
            onClick={onBack}
            className="text-sm text-slate-500 hover:text-slate-700 mb-1"
          >
            ← Testlar ro'yxati
          </button>
          <h3 className="font-semibold text-slate-900">
            {examTitle(exam)}{" "}
            <span className="text-slate-400 font-normal text-sm">
              · {formatDate(exam.date)}
              {!isMock && exam.max_score ? ` · max ${exam.max_score} ball` : ""}
            </span>
          </h3>
        </div>
        {canEdit && (
          <button
            onClick={save}
            disabled={saving}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        )}
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <div className="border border-slate-200 rounded-xl bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Talaba</th>
              <th className="text-left px-4 py-3 font-medium w-32">
                {isMock ? `Band (0-${MOCK_MAX_BAND})` : "Ball"}
              </th>
              <th className="text-right px-4 py-3 font-medium">Foiz</th>
              <th className="text-right px-4 py-3 font-medium">Coin</th>
            </tr>
          </thead>
          <tbody>
            {exam.students.map((s) => {
              const r = byStudent[s.id];
              return (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">{s.full_name}</td>
                  <td className="px-4 py-2">
                    <input
                      type="number"
                      step={isMock ? "0.5" : "1"}
                      disabled={!canEdit}
                      className="w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                      value={draft[s.id] ?? ""}
                      onChange={(e) =>
                        setDraft({ ...draft, [s.id]: e.target.value })
                      }
                      placeholder="—"
                    />
                  </td>
                  <td className="px-4 py-2 text-right text-slate-600">
                    {r && r.percent != null ? `${r.percent}%` : "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {r && r.coins > 0 ? (
                      <span className="inline-flex items-center gap-1 text-brand-700 font-medium">
                        <Coins size={13} /> {r.coins}
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 mt-3">
        Faqat {isMock ? "band" : "ball"} kiriting — foiz va coin o'zi
        hisoblanadi. Bo'sh qoldirilgan katak "kelmagan" deb yoziladi.
      </p>
    </div>
  );
}

export function ExamsTab({
  groupId,
  canEdit,
  canDelete,
}: {
  groupId: number;
  canEdit: boolean;
  canDelete: boolean;
}) {
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);

  function load() {
    setLoading(true);
    api
      .get<Exam[]>(`/groups/${groupId}/exams`)
      .then(setExams)
      .finally(() => setLoading(false));
  }

  useEffect(load, [groupId]);

  async function remove(e: Exam) {
    if (
      !confirm(
        `${examTitle(e)} o'chirilsinmi? Bergan coinlari ham qaytariladi.`
      )
    )
      return;
    await api.delete(`/exams/${e.id}`);
    load();
  }

  if (openId)
    return (
      <ExamSheet
        examId={openId}
        canEdit={canEdit}
        onBack={() => {
          setOpenId(null);
          load();
        }}
        onChanged={load}
      />
    );

  return (
    <div>
      {canEdit && (
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium mb-4"
        >
          <Plus size={16} /> Yangi test
        </button>
      )}

      {loading ? (
        <p className="text-sm text-slate-400">Yuklanmoqda...</p>
      ) : exams.length === 0 ? (
        <EmptyState text="Hali test o'tkazilmagan" />
      ) : (
        <div className="border border-slate-200 rounded-xl bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Test</th>
                <th className="text-left px-4 py-3 font-medium">Turi</th>
                <th className="text-left px-4 py-3 font-medium">Sana</th>
                <th className="text-right px-4 py-3 font-medium">Natija</th>
                <th className="text-right px-4 py-3 font-medium">O'rtacha</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {exams.map((e) => (
                <tr
                  key={e.id}
                  className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                  onClick={() => setOpenId(e.id)}
                >
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {examTitle(e)}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {examKindLabel(e.kind)}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(e.date)}</td>
                  <td className="px-4 py-3 text-right text-slate-600">
                    {e.result_count || "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-slate-800">
                    {e.avg_percent != null ? `${e.avg_percent}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {canDelete && (
                      <button
                        onClick={(ev) => {
                          ev.stopPropagation();
                          remove(e);
                        }}
                        className="text-slate-300 hover:text-red-500"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showNew && (
        <ExamForm
          groupId={groupId}
          onClose={() => setShowNew(false)}
          onCreated={load}
        />
      )}
    </div>
  );
}
