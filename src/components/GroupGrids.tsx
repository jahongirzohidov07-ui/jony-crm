import { useEffect, useState } from "react";
import { Check, X, Plus, Trash2, Pencil, Coins, CalendarClock, Clock, Minus } from "lucide-react";
import {
  api,
  type AttendanceGrid,
  type SupportAttendanceGrid,
  type Exam,
  type ExamDetail,
  type ExamKind,
  type ExamPassRule,
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
import { useAuth } from "../lib/AuthContext";
import { Time24Input } from "./Time24Input";
import { useExamOnline, OnlineLinkCard, OnlineBelow, Photo, AnswerSheetButton, AwayBadge } from "./ExamOnline";

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
  onPick,
  onClose,
}: {
  present?: boolean | number;
  onPick: (v: "present" | "late" | "absent" | "remove") => void;
  onClose: () => void;
}) {
  const marked = present !== undefined;
  // Belgilanmagan: uchala holat. Belgilangan: qolgan ikkitasi +
  // o'ngda olib tashlash (rasmdagidek).
  const options: {
    key: "present" | "late" | "absent" | "remove";
    title: string;
    icon: "check" | "clock" | "x" | "minus";
    on: string;
    hover: string;
  }[] = [];
  if (present !== true)
    options.push({ key: "present", title: "Keldi", icon: "check",
                   on: "bg-brand-500 border-brand-500 text-white",
                   hover: "hover:bg-brand-50" });
  if (present !== 2)
    options.push({ key: "late", title: "Kech keldi", icon: "clock",
                   on: "bg-amber-500 border-amber-500 text-white",
                   hover: "hover:bg-amber-50" });
  if (present !== false)
    options.push({ key: "absent", title: "Kelmadi", icon: "x",
                   on: "bg-red-500 border-red-500 text-white",
                   hover: "hover:bg-red-50" });
  if (marked)
    options.push({ key: "remove", title: "Belgini olib tashlash",
                   icon: "minus", on: "",
                   hover: "hover:bg-slate-100" });

  const ICONS = {
    check: <Check size={14} />,
    clock: <Clock size={14} />,
    x: <X size={14} />,
    minus: <Minus size={14} />,
  };

  const TONE: Record<string, string> = {
    // To'liq bo'yalgan: bor — yashil, kech — sariq, yo'q — qizil
    present: "bg-emerald-500 text-white hover:bg-emerald-600",
    late: "bg-amber-400 text-white hover:bg-amber-500",
    absent: "bg-red-500 text-white hover:bg-red-600",
    remove: "bg-slate-200 text-slate-600 hover:bg-slate-300",
  };
  return (
    // Katakning AYNAN O'ZIDA (markazida) chiqadi — pastda ham,
    // tepada ham emas: kursor hech qayoqqa "sayohat" qilmaydi
    <div
      className="absolute z-30 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
      onMouseLeave={onClose}
    >
      <div className="bg-white border border-slate-200 rounded-full shadow-lg p-1 flex gap-1">
        {options.map((o) => (
          <button
            key={o.key}
            title={o.title}
            onClick={() => onPick(o.key)}
            className={`w-8 h-8 rounded-full inline-flex items-center justify-center transition ${TONE[o.key]}`}
          >
            {ICONS[o.icon]}
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
  movedIn,
  onMove,
  onCancelLesson,
  onClose,
}: {
  date: string;
  held: number;
  box: NonNullable<AttendanceGrid["reschedule"]>;
  moved?: { status_label: string; to_date: string };
  movedIn?: { status_label: string; from_date: string };
  onMove: () => void;
  /** Darsni BEKOR qilish — faqat asoschiga beriladi (2026-08-19,
   *  Jahongir: "buni faqat men qila olaman"). */
  onCancelLesson?: () => void;
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

      {movedIn && (
        <div className="rounded-lg bg-teal-50 border border-teal-200 p-2 mb-2">
          <p className="text-xs text-teal-700">
            {formatDate(movedIn.from_date)}dan ko'chirilgan dars
          </p>
          <p className="text-[11px] text-teal-500">{movedIn.status_label}</p>
        </div>
      )}

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
      ) : past && !box.manager ? (
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

      {/* DARSNI BEKOR QILISH (2026-08-19) — "Dars ko'chirish"ning
          TAGIDA turadi, faqat asoschida. O'tilgan darsni bekor qilib
          bo'lmaydi. Rejadan butunlay chiqadi (dam kuni mantig'i). */}
      {onCancelLesson && !held && !moved && (
        <button
          onClick={onCancelLesson}
          className="w-full flex items-center justify-center gap-1.5 border border-red-200 bg-red-50 text-red-700 rounded-lg py-2 text-sm font-medium mb-2"
        >
          <X size={14} />
          Darsni bekor qilish
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
  const { user } = useAuth();
  const [grid, setGrid] = useState<AttendanceGrid | null>(null);
  const [loading, setLoading] = useState(true);
  // Xato holati SHART: aks holda so'rov xato bersa ekran butunlay
  // bo'sh qolardi (2026-08-10 tuzatildi).
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null); // ochiq katak
  const [menu, setMenu] = useState<number | null>(null); // ochiq sana

  // SANA QOIDALARI: kelajak — hech kimga; o'tgan kun — faqat
  // asoschi va o'quv bo'limi rahbariga; bugun — odatdagidek.
  const todayIso = new Date().toISOString().slice(0, 10);
  const canPast =
    user?.role === "founder" ||
    user?.role === "academic_head" ||
    user?.role === "hr_manager";
  const cellEditable = (lsDate: string) =>
    canEdit &&
    (lsDate === todayIso || (lsDate < todayIso && canPast));
  const cellHint = (lsDate: string) => {
    if (lsDate > todayIso)
      return "Hali kelmagan kun — yoqlama qo'yilmaydi";
    if (lsDate < todayIso && !canPast)
      return "O'tib ketgan kun — o'quv bo'limi rahbari yoki HR " +
             "menejer tuzatadi";
    return undefined;
  };
  const [moving, setMoving] = useState<{ id: number; date: string } | null>(
    null
  );

  // MUZLATILGAN VA KETGANLAR DAVOMATI (2026-08-20, Jahongir:
  // "pastiga ketganlar va muzaltilganlarni daovmatini korsatish
  // degan tugmani qoysak bosganda korinsin"). Odatiy holda jadval
  // faqat faollardan iborat - tugma bosilganda tarix ham ochiladi.
  const [showOthers, setShowOthers] = useState(false);
  const canSeeOthers = [
    "founder", "branch_manager", "academic_head", "hr_manager",
    "finance_director", "sales_manager", "administrator",
  ].includes(user?.role || "");

  const load = () => {
    setLoading(true);
    setErr("");
    api
      .get<AttendanceGrid>(
        `/groups/${groupId}/attendance?year=${year}&month=${month}` +
          (showOthers ? "&others=1" : "")
      )
      .then(setGrid)
      .catch((e) =>
        setErr(e instanceof Error ? e.message : "Yuklab bo'lmadi"),
      )
      .finally(() => setLoading(false));
  };
  useEffect(load, [groupId, year, month, showOthers]);

  /** Bitta amal: keldi / kech keldi / kelmadi / olib tashlash.
   *  Olib tashlangan o'quvchi "belgilanmagan"ga qaytadi va shu dars
   *  uchun oylikka kirmaydi. */
  async function pick(
    lessonId: number,
    studentId: number,
    what: "present" | "late" | "absent" | "remove"
  ) {
    if (!grid) return;
    const key = `${lessonId}:${studentId}`;
    const before = grid.marks[key];
    const marks = { ...grid.marks };
    if (what === "remove") delete marks[key];
    else marks[key] = what === "late" ? 2 : what === "present";
    setGrid({ ...grid, marks });
    setSaving(key);
    setOpen(null);
    try {
      await api.put(`/lessons/${lessonId}/attendance`, {
        marks: [
          what === "remove"
            ? { student_id: studentId, present: false, remove: true }
            : {
                student_id: studentId,
                present: what !== "absent",
                late: what === "late",
              },
        ],
      });
    } catch (e) {
      const back = { ...grid.marks };
      if (before === undefined) delete back[key];
      else back[key] = before;
      setGrid({ ...grid, marks: back });
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (err)
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-red-600 mb-2">{err}</p>
        <button onClick={load} className="text-sm text-brand-600 underline">
          Qayta urinish
        </button>
      </div>
    );
  if (!grid) return null;
  if (grid.lessons.length === 0)
    return (
      <EmptyState text="Bu oyda dars kuni yo'q. Guruhni tahrirlab dars kunlarini (masalan Dushanba, Chorshanba, Juma) tanlang — butun oy jadvali avtomat chiqadi." />
    );
  if (grid.students.length === 0)
    return <EmptyState text="Guruhda o'quvchi yo'q" />;

  const total = grid.lessons.length * grid.students.length;
  const present = Object.values(grid.marks).filter(
    (v) => v === true || v === 2
  ).length;
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

      {/* TELEFON (2026-09-16): ism ustuni ixcham va yopishqoq — yonga
          surganda ismlar joyida qoladi, kataklarga joy yetadi. */}
      <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
        <table data-guide="attendance-grid" className="text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50">
              <th className="sticky left-0 z-20 bg-slate-50 text-left px-2 sm:px-4 py-3 font-medium text-xs uppercase text-slate-500 w-[130px] min-w-[130px] max-w-[130px] sm:w-auto sm:min-w-[200px] sm:max-w-none border-r border-slate-200 shadow-[2px_0_4px_-2px_rgba(15,23,42,0.15)]">
                Talabalar
              </th>
              {grid.lessons.map((ls) => {
                const mv = box?.moved?.[ls.date];
                const movedIn = box?.moved_in?.[ls.date];
                return (
                  <th
                    key={ls.id}
                    className="px-2 py-2 font-medium min-w-[76px] relative"
                  >
                    <button
                      onClick={() => setMenu(menu === ls.id ? null : ls.id)}
                      className={`text-xs whitespace-nowrap px-1.5 py-1 rounded-lg hover:bg-slate-200 transition ${
                        ls.held ? "text-slate-700" : "text-slate-400"
                      } ${mv ? "line-through" : ""} ${
                        movedIn ? "bg-teal-50 text-teal-700" : ""
                      }`}
                      title={
                        movedIn
                          ? `Ko'chirilgan dars — asli ${formatDate(
                              movedIn.from_date
                            )}`
                          : "Menyu: dars ko'chirish"
                      }
                    >
                      {dayLabel(ls.date)}
                    </button>
                    {movedIn && (
                      <p className="text-[9px] leading-none text-teal-600 mt-0.5 whitespace-nowrap">
                        {dayLabel(movedIn.from_date)}dan
                      </p>
                    )}
                    {menu === ls.id && box && (
                      <DateMenu
                        date={ls.date}
                        held={ls.held}
                        box={box}
                        moved={mv}
                        movedIn={movedIn}
                        onMove={() => {
                          setMenu(null);
                          setMoving({ id: ls.id, date: ls.date });
                        }}
                        onCancelLesson={
                          user?.role === "founder"
                            ? async () => {
                                if (!confirm(
                                  formatDate(ls.date) + " darsi BEKOR " +
                                  "qilinsinmi?\n\nU rejadan butunlay " +
                                  "chiqadi: davomatda ko'rinmaydi va " +
                                  "oylik hisobiga kirmaydi. Oyda " +
                                  "kamida 12 ta dars qolishi shart."))
                                  return;
                                try {
                                  await api.post(
                                    `/lessons/${ls.id}/cancel`, {});
                                  setMenu(null);
                                  load();
                                } catch (e) {
                                  alert(e instanceof Error
                                    ? e.message : "Xatolik");
                                }
                              }
                            : undefined
                        }
                        onClose={() => setMenu(null)}
                      />
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {grid.students.map((s, i) => {
              // Muzlatilgan o'quvchi: eski davomat TARIXI rahbariyatga
              // ko'rinadi, lekin belgilab bo'lmaydi (Jahongir:
              // "eski davomatlar tarixi qolishi kerak...
              // ertaga bizga u kerak bo'ladi")
              const frozen = s.status === "frozen";
              // Boshqa guruhga o'tgan: eski yo'qlamalari shu yerda
              // qoladi (eski ustoz oyligi hujjati), faqat o'qish uchun
              const gone = s.status === "transferred";
              const locked = frozen || gone;
              return (
              <tr
                key={s.id}
                className={`border-t border-slate-100 ${
                  frozen ? "bg-sky-50/40" : gone ? "bg-violet-50/40" : ""
                }`}
              >
                <td
                  className={`sticky left-0 z-10 px-2 sm:px-4 py-2.5 text-xs sm:text-sm leading-snug break-words w-[130px] min-w-[130px] max-w-[130px] sm:w-auto sm:min-w-0 sm:max-w-none sm:whitespace-nowrap border-r border-slate-200 shadow-[2px_0_4px_-2px_rgba(15,23,42,0.15)] ${
                    frozen
                      ? "bg-sky-50 text-sky-700"
                      : gone
                      ? "bg-violet-50 text-violet-700"
                      : "bg-white text-slate-800"
                  }`}
                  title={s.note || undefined}
                >
                  <span className="text-slate-400 mr-2 text-xs">{i + 1}</span>
                  {s.full_name}
                  {frozen && (
                    <span className="ml-2 text-[10px] font-medium bg-sky-100 text-sky-700 px-1.5 py-0.5 rounded">
                      muzlatilgan
                    </span>
                  )}
                  {gone && (
                    <span className="ml-2 text-[10px] font-medium bg-violet-100 text-violet-700 px-1.5 py-0.5 rounded">
                      boshqa guruhga o'tgan
                    </span>
                  )}
                  {/* 2026-08-29, Jahongir: "chiqib ketgan ... oxirgi
                      2ta dars kelmagan ... shu kelmagan darsini
                      ayirib tashlash kerak". Kataklar allaqachon
                      bo'sh — bu yozuv NEGA bo'shligini aytadi, aks
                      holda "yo'qlama qani?" degan savol qolardi. */}
                  {(s as unknown as { counted_until?: string })
                    .counted_until && (
                    <span className="ml-2 text-[10px] text-slate-400">
                      {(s as unknown as { counted_until: string })
                        .counted_until.slice(8)}-
                      {(s as unknown as { counted_until: string })
                        .counted_until.slice(5, 7)} gacha hisoblangan
                    </span>
                  )}
                </td>
                {grid.lessons.map((ls) => {
                  const key = `${ls.id}:${s.id}`;
                  const v = grid.marks[key];
                  const editable = !locked && cellEditable(ls.date);
                  return (
                    <td
                      key={ls.id}
                      className="px-2 py-2 text-center relative"
                      onMouseEnter={() => editable && setOpen(key)}
                      onMouseLeave={() =>
                        setOpen((k) => (k === key ? null : k))
                      }
                    >
                      <button
                        onClick={() =>
                          editable && setOpen(open === key ? null : key)
                        }
                        disabled={!editable || saving === key}
                        title={
                          frozen
                            ? "Muzlatilgan o'quvchi — tarix faqat o'qish uchun"
                            : gone
                            ? s.note ||
                              "Boshqa guruhga o'tgan — tarix faqat o'qish uchun"
                            : cellHint(ls.date)
                        }
                        className={`w-8 h-8 rounded-lg inline-flex items-center justify-center transition ${
                          v === true
                            ? "bg-brand-500 text-white"
                            : v === 2
                            ? "bg-amber-500 text-white"
                            : v === false
                            ? "bg-red-500 text-white"
                            : ls.date > todayIso
                            ? "bg-slate-50"
                            : "bg-slate-100 hover:bg-slate-200"
                        } ${
                          editable ? "cursor-pointer" : "cursor-not-allowed"
                        } ${!editable && v === undefined ? "opacity-50" : ""}`}
                      >
                        {v === true ? (
                          <Check size={15} />
                        ) : v === 2 ? (
                          <Clock size={15} />
                        ) : v === false ? (
                          <X size={15} />
                        ) : null}
                      </button>
                      {open === key && editable && (
                        <MarkPicker
                          present={v as boolean | number | undefined}
                          onPick={(what) => pick(ls.id, s.id, what)}
                          onClose={() => setOpen(null)}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Muzlatilgan va ketganlar tarixi tugmasi (2026-08-20) */}
      {canSeeOthers && (
        <div className="mt-2">
          <button
            onClick={() => setShowOthers((v) => !v)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition ${
              showOthers
                ? "bg-sky-50 border-sky-300 text-sky-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-sky-300 hover:text-sky-700"
            }`}
          >
            {showOthers
              ? "Muzlatilgan va ketganlar davomatini yashirish"
              : "Muzlatilgan va ketganlar davomatini ko'rsatish"}
          </button>
          {showOthers && (
            <span className="ml-2 text-[11px] text-slate-400">
              Bu qatorlar faqat o'qish uchun — yoqlama qo'yilmaydi.
            </span>
          )}
        </div>
      )}

      {/* 2026-08-18, Jahongir: "shu joydagi shu yozuvni ham olib
          tashla kerak mas" — jadval ostidagi uzun qo'llanma matni
          olib tashlandi. Qoidalarning o'zi o'zgargani yo'q. */}
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

  // Rahbariyat/HR menejer darsni ISTALGAN sanaga ko'chira oladi —
  // hatto o'tib ketganiga ham (oy oxirini qayta taqsimlash yoki
  // orqada qolgan jadvalni tuzatish uchun, 2026-08-09 so'ralgan) —
  // backend shuni ruxsat beradi (groups_lessons.py:group_reschedule).
  // Yagona chegara ikkala tomonga ham amal qiladigan max_shift_days,
  // shuning uchun min'ni HAM shu masofaga qo'yamiz — aks holda forma
  // backend rad etadigan sanani tanlashga imkon berardi. Oddiy ustoz
  // uchun eskicha: kamida ertaga bo'lishi kerak.
  const min = box.manager
    ? new Date(
        new Date(fromDate).getTime() - box.max_shift_days * 86400000
      )
        .toISOString()
        .slice(0, 10)
    : new Date(Date.now() + 86400000).toISOString().slice(0, 10);
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
  // Xato holati SHART: aks holda so'rov xato bersa ekran butunlay
  // bo'sh qolardi (2026-08-10 tuzatildi).
  const [err, setErr] = useState("");

  const load = () => {
    setLoading(true);
    setErr("");
    api
      .get<AttendanceGrid>(`/groups/${groupId}/grades?year=${year}&month=${month}`)
      .then(setGrid)
      .catch((e) =>
        setErr(e instanceof Error ? e.message : "Yuklab bo'lmadi"),
      )
      .finally(() => setLoading(false));
  };
  useEffect(load, [groupId, year, month]);

  /** Baho qo'yish shartlari: dars o'tgan bo'lsin, o'quvchi kelgan
   *  bo'lsin. Kelmagan bolaga baho qo'yilsa unga coin ham tushib
   *  ketardi — shuning uchun katak umuman bosilmaydi. */
  const g = grid as (AttendanceGrid & {
    present?: Record<string, number>;
    can_past?: boolean;
    today?: string;
  }) | null;
  function cellState(lessonDate: string, lessonId: number, studentId: number) {
    const today = g?.today ?? new Date().toISOString().slice(0, 10);
    if (lessonDate > today)
      return { ok: false, why: "Dars hali bo'lib o'tmagan" };
    if (lessonDate < today && !g?.can_past)
      return { ok: false, why: "O'tib ketgan kun — o'quv bo'limi rahbari tuzatadi" };
    const p = g?.present?.[`${lessonId}:${studentId}`];
    if (p === undefined)
      return { ok: false, why: "Avval yo'qlama qo'ying" };
    if (p === 0)
      return { ok: false, why: "Bu darsga kelmagan — baho qo'yilmaydi" };
    return { ok: true, why: "" };
  }

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
    } catch (e) {
      setGrid({ ...grid, marks: grid.marks });
      alert(e instanceof Error ? e.message : "Baho saqlanmadi");
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (err)
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-red-600 mb-2">{err}</p>
        <button onClick={load} className="text-sm text-brand-600 underline">
          Qayta urinish
        </button>
      </div>
    );
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
              <th className="sticky left-0 z-20 bg-slate-50 text-left px-2 sm:px-4 py-3 font-medium text-xs uppercase text-slate-500 w-[130px] min-w-[130px] max-w-[130px] sm:w-auto sm:min-w-[200px] sm:max-w-none border-r border-slate-200 shadow-[2px_0_4px_-2px_rgba(15,23,42,0.15)]">
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
                  <td className="sticky left-0 z-10 bg-white px-2 sm:px-4 py-2.5 text-xs sm:text-sm leading-snug break-words text-slate-800 w-[130px] min-w-[130px] max-w-[130px] sm:w-auto sm:min-w-0 sm:max-w-none sm:whitespace-nowrap border-r border-slate-200 shadow-[2px_0_4px_-2px_rgba(15,23,42,0.15)]">
                    <span className="text-slate-400 mr-2 text-xs">{i + 1}</span>
                    {s.full_name}
                  </td>
                  {grid.lessons.map((ls) => {
                    const v = grid.marks[`${ls.id}:${s.id}`] as number | undefined;
                    const st = cellState(ls.date, ls.id, s.id);
                    const locked = !canEdit || (!st.ok && v === undefined);
                    return (
                      <td key={ls.id} className="px-2 py-2 text-center">
                        <button
                          onClick={() => cycle(ls.id, s.id)}
                          disabled={locked}
                          title={st.ok ? "" : st.why}
                          className={`w-8 h-8 rounded-lg inline-flex items-center justify-center font-semibold text-sm transition ${
                            v
                              ? gradeTone(v)
                              : locked
                                ? "bg-slate-50 text-slate-300 cursor-not-allowed"
                                : "bg-slate-100 hover:bg-slate-200"
                          }`}
                        >
                          {v ?? (locked ? "·" : "")}
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
  exam,
  onClose,
  onCreated,
}: {
  groupId: number;
  /** Berilsa — mavjud testni TAHRIRLASH (2026-09-17). */
  exam?: Exam;
  onClose: () => void;
  onCreated: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [kind, setKind] = useState<ExamKind>(exam?.kind ?? "unit");
  const [unitNo, setUnitNo] = useState(String(exam?.unit_no ?? 1));
  const [date, setDate] = useState(exam?.date ?? today);
  const [maxScore, setMaxScore] = useState(
    exam?.max_score != null ? String(exam.max_score) : "50"
  );
  const [title, setTitle] = useState(exam?.title ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // O'TISH BALLI (2026-09-10, Jahongir: "Maksimal ball bor o'tish
  // balli yo'qku"). Bu yerda TAHRIRLANMAYDI — sozlamada test turi
  // bo'yicha bir marta belgilanadi (Gamification -> Coin qoidasi),
  // shu yerda faqat ko'rinib turadi, ustoz nima kutilayotganini
  // bilsin. Test ochilganda shu foiz imtihonga muhrlanadi.
  const [passRules, setPassRules] = useState<ExamPassRule[]>([]);
  useEffect(() => {
    api.get<ExamPassRule[]>("/exam-pass-rules")
      .then(setPassRules)
      .catch(() => {});
  }, []);
  const passPercent = exam
    ? exam.pass_percent ?? undefined
    : passRules.find((r) => r.kind === kind)?.percent;
  // Test bazasida mos test bo'lsa — maksimal ball savollar soniga teng
  // va qo'lda o'zgartirilmaydi (2026-09-18)
  const [bankMax, setBankMax] = useState<number | null>(null);
  useEffect(() => {
    if (exam || kind === "mock") {
      setBankMax(null);
      return;
    }
    const q = kind === "unit" ? `&unit_no=${unitNo}` : "";
    api
      .get<{ max_score: number | null }>(`/groups/${groupId}/exam-bank-max?kind=${kind}${q}`)
      .then((r) => {
        setBankMax(r.max_score);
        if (r.max_score) setMaxScore(String(r.max_score));
      })
      .catch(() => setBankMax(null));
  }, [exam, kind, unitNo, groupId]);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const body = {
        kind,
        unit_no: kind === "unit" ? Number(unitNo) : null,
        date,
        max_score: kind === "mock" ? null : Number(maxScore),
      };
      if (exam) {
        await api.put(`/exams/${exam.id}`, { ...body, title: title.trim() });
      } else {
        await api.post(`/groups/${groupId}/exams`, body);
      }
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
          <h2 className="font-semibold text-slate-900">
            {exam ? "Testni tahrirlash" : "Yangi test"}
          </h2>
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

          {exam && (
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Nomi (ixtiyoriy)
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={title}
                placeholder={examTitle({ ...exam, title: null, kind, unit_no: Number(unitNo) })}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
          )}

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
                  disabled={!!bankMax}
                  title={bankMax ? "Test bazasidagi savollar soni" : undefined}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
                  value={maxScore}
                  onChange={(e) => setMaxScore(e.target.value)}
                />
                {bankMax ? (
                  <p className="text-[11px] text-slate-400 mt-1">
                    Test bazasidan: {bankMax} savol
                  </p>
                ) : null}
              </div>
            )}
          </div>

          {kind === "mock" ? (
            <p className="text-xs text-slate-400">
              Mock testda ball emas, IELTS band (0–{MOCK_MAX_BAND}) kiritiladi.
              O'tish balli qo'llanmaydi.
            </p>
          ) : passPercent != null ? (
            <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
              O'tish balli: <b className="text-slate-700">{passPercent}%</b>
              {maxScore && Number(maxScore) > 0 && (
                <> — ya'ni {Math.ceil((Number(maxScore) * passPercent) / 100)}{" "}
                  ball va undan yuqorisi</>
              )}
              . Sozlamada test turi bo'yicha belgilanadi (Gamification →
              Coin qoidasi) va shu test uchun saqlanib qoladi.
            </p>
          ) : null}

          {exam && exam.result_count > 0 && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Natijalar kiritilgan: maksimal ball o'zgarsa foiz va coinlar
              qayta hisoblanadi.
            </p>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-1 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : exam ? "Saqlash" : "Yaratish"}
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
  // Retake: examiner qayta topshiriq ballini kiritadi. Coin va
  // o'rtacha faqat birinchi balldan - retake shunchaki yonida turadi.
  const [retakeFor, setRetakeFor] = useState<number | null>(null);
  const [retakeVal, setRetakeVal] = useState("");

  async function saveRetake(studentId: number, remove = false) {
    setError(null);
    try {
      const num = Number(retakeVal);
      const body = remove
        ? { student_id: studentId, remove: true }
        : exam!.kind === "mock"
        ? { student_id: studentId, band: num }
        : { student_id: studentId, score: num };
      const updated = await api.put<ExamDetail>(
        `/exams/${examId}/retake`,
        body
      );
      setExam(updated);
      setRetakeFor(null);
      setRetakeVal("");
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  // ONLINE TEST (2026-09-18): link, qog'oz ballari, aniqlanmagan natijalar
  const online = useExamOnline(examId, true);
  const placedCount = (online.data?.submissions || []).filter(
    (s) => s.status === "placed"
  ).length;
  useEffect(() => {
    if (placedCount) load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [placedCount]);
  const onlineBy = Object.fromEntries(
    (online.data?.submissions || [])
      .filter((s) => s.status === "placed" && s.student_id)
      .map((s) => [s.student_id as number, s])
  );

  function load(fresh = false) {
    (fresh ? api.fresh<ExamDetail>(`/exams/${examId}`)
           : api.get<ExamDetail>(`/exams/${examId}`)).then((d) => {
      setExam(d);
      const next: Record<number, string> = {};
      for (const r of d.results) {
        if (r.absent) next[r.student_id] = "";
        else next[r.student_id] = String(d.kind === "mock" ? r.band ?? "" : r.score ?? "");
      }
      setDraft(next);
    });
  }

  useEffect(() => load(), [examId]);
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

      <OnlineLinkCard
        examId={examId}
        kind={exam.kind}
        data={online.data}
        setData={online.setData}
        onChanged={() => {
          load(true);
          onChanged();
        }}
      />

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
              <th className="text-right px-4 py-3 font-medium">Retake</th>
            </tr>
          </thead>
          <tbody>
            {exam.students.map((s) => {
              const r = byStudent[s.id];
              return (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5 text-slate-800">
                    {onlineBy[s.id] && (
                      <span className="mr-2 align-middle">
                        <Photo src={onlineBy[s.id].photo} size={24} />
                      </span>
                    )}
                    {s.full_name}
                    {onlineBy[s.id] && (
                      <AnswerSheetButton
                        s={onlineBy[s.id]}
                        className="ml-2 text-[10px] font-medium bg-sky-50 text-sky-700 hover:bg-sky-100 px-1.5 py-0.5 rounded underline decoration-dotted"
                      >
                        online {onlineBy[s.id].online_score}/{onlineBy[s.id].online_max}
                        {online.data?.online?.paper_max && onlineBy[s.id].paper_score == null
                          ? " · qog'oz kutilmoqda"
                          : ""}
                        {online.data?.online && !online.data.online.published_at
                          ? " · tasdiqlanmagan"
                          : ""}
                      </AnswerSheetButton>
                    )}
                    {onlineBy[s.id]?.away_count ? (
                      <AwayBadge
                        n={onlineBy[s.id].away_count}
                        sec={onlineBy[s.id].away_sec}
                        className="ml-2"
                      />
                    ) : null}
                    {r && r.counted === 0 && (
                      <span
                        className="ml-2 text-[10px] font-medium bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded"
                        title="Imtihongacha birorta ham yo'qlamasi yo'q — natija ko'rinadi, lekin umumiy o'rtacha va coinga kirmaydi"
                      >
                        hisobga kirmaydi
                      </span>
                    )}
                  </td>
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
                    {r && r.coins !== 0 ? (
                      <span
                        className={`inline-flex items-center gap-1 font-medium ${
                          r.coins > 0 ? "text-brand-700" : "text-rose-600"
                        }`}
                      >
                        <Coins size={13} /> {r.coins > 0 ? r.coins : r.coins}
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    {retakeFor === s.id ? (
                      <span className="inline-flex items-center gap-1">
                        <input
                          type="number"
                          step={isMock ? "0.5" : "1"}
                          autoFocus
                          className="w-20 rounded-lg border border-slate-300 px-2 py-1 text-sm"
                          value={retakeVal}
                          onChange={(e) => setRetakeVal(e.target.value)}
                          placeholder={isMock ? "band" : "ball"}
                        />
                        <button
                          onClick={() => saveRetake(s.id)}
                          className="text-emerald-600 hover:text-emerald-700 text-xs font-medium"
                        >
                          OK
                        </button>
                        <button
                          onClick={() => {
                            setRetakeFor(null);
                            setRetakeVal("");
                          }}
                          className="text-slate-400 text-xs"
                        >
                          ✕
                        </button>
                      </span>
                    ) : r && r.retake_percent != null ? (
                      <span
                        className="text-violet-600 text-xs font-medium"
                        title={`Retake ${r.retake_at ? formatDate(r.retake_at) : ""} — coin yo'q, o'rtachaga kirmaydi. Birinchi ball saqlanadi.`}
                      >
                        {r.retake_percent}%
                        {canEdit && (
                          <button
                            onClick={() => saveRetake(s.id, true)}
                            title="Retake'ni o'chirish"
                            className="ml-1 text-slate-300 hover:text-rose-500"
                          >
                            ×
                          </button>
                        )}
                      </span>
                    ) : canEdit && r && !r.absent && r.percent != null ? (
                      <button
                        onClick={() => {
                          setRetakeFor(s.id);
                          setRetakeVal("");
                        }}
                        className="text-xs text-slate-400 hover:text-violet-600 underline decoration-dotted"
                      >
                        retake
                      </button>
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

      <OnlineBelow
        examId={examId}
        data={online.data}
        setData={online.setData}
        students={exam.students}
        onChanged={() => {
          load(true);
          onChanged();
        }}
      />

      <p className="text-xs text-slate-400 mt-3">
        Faqat {isMock ? "band" : "ball"} kiriting — foiz va coin o'zi
        hisoblanadi (past natija coin yechadi). Bo'sh katak "kelmagan"
        deb yoziladi. Retake — qayta topshirish: birinchi ball va foiz
        saqlanib qoladi, retake uchun coin berilmaydi va u guruh
        o'rtachasiga kirmaydi. Imtihon kuni endi kelgan (yo'qlamasiz)
        o'quvchi natijasi ko'rinadi, lekin o'rtacha va coinga kirmaydi.
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
  const [editing, setEditing] = useState<Exam | null>(null);

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
                      <span className="inline-flex items-center gap-3">
                        <button
                          title="Tahrirlash"
                          onClick={(ev) => {
                            ev.stopPropagation();
                            setEditing(e);
                          }}
                          className="text-slate-300 hover:text-brand-600"
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          title="O'chirish"
                          onClick={(ev) => {
                            ev.stopPropagation();
                            remove(e);
                          }}
                          className="text-slate-300 hover:text-red-500"
                        >
                          <Trash2 size={15} />
                        </button>
                      </span>
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
      {editing && (
        <ExamForm
          groupId={groupId}
          exam={editing}
          onClose={() => setEditing(null)}
          onCreated={load}
        />
      )}
    </div>
  );
}

// --------------------------------------------- Support davomati ----

/** Support teacherning O'Z seansidagi yo'qlamasi.
 *
 *  Ustozning davomatidan BUTUNLAY ajratilgan: alohida jadval, alohida
 *  kunlar (support biriktirilganda belgilangan kun va vaqt). Bu yerga
 *  qo'yilgan belgi ustoz oyligiga ham, o'quvchi hisobiga ham
 *  tegmaydi — u faqat support ishining ko'zgusi. */
export function SupportAttendanceTab({
  groupId,
  year,
  month,
}: {
  groupId: number;
  year: number;
  month: number;
}) {
  const [grid, setGrid] = useState<SupportAttendanceGrid | null>(null);
  const [loading, setLoading] = useState(true);
  // Xato holati SHART (2026-08-10): xato bo'lsa ekran bo'sh qolmasin.
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  // Seans vaqti: support qaysi kunni tahrirlayotgani va o'sha kunning
  // "qaysi vaqtdan qaysi vaqtgacha"si. Oylik AYNAN shu soatdan
  // hisoblanadi, shuning uchun har kun alohida.
  const [day, setDay] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [tErr, setTErr] = useState("");

  const load = () => {
    setLoading(true);
    api
      .get<SupportAttendanceGrid>(
        `/groups/${groupId}/support-attendance?year=${year}&month=${month}`
      )
      .then(setGrid)
      .catch((e) =>
        setErr(e instanceof Error ? e.message : "Yuklab bo'lmadi"),
      )
      .finally(() => setLoading(false));
  };
  useEffect(load, [groupId, year, month]);

  // Kun tanlanmagan bo'lsa — bugun (yoki oxirgi o'tgan support kuni)
  useEffect(() => {
    if (!grid || grid.days.length === 0) return;
    const past = grid.days.filter((d) => d <= grid.today);
    const pick = grid.days.includes(grid.today)
      ? grid.today
      : past[past.length - 1] || grid.days[0];
    setDay((prev) => (prev && grid.days.includes(prev) ? prev : pick));
  }, [grid]);

  // Tanlangan kunning vaqtlari: yozilgani bo'lsa o'sha, bo'lmasa
  // biriktirishdagi standart vaqt.
  useEffect(() => {
    if (!grid || !day) return;
    const s = grid.sessions?.[day];
    setFrom(s?.start || grid.default_start || "");
    setTo(s?.end || grid.default_end || "");
  }, [grid, day]);

  const today = grid?.today ?? new Date().toISOString().slice(0, 10);
  const editable = (d: string) =>
    !!grid?.can_edit && (d === today || (d < today && grid.can_past));
  const hint = (d: string) => {
    if (d > today) return "Hali kelmagan kun";
    if (d < today && !grid?.can_past)
      return "O'tib ketgan kun — o'quv bo'limi rahbari yoki HR tuzatadi";
    if (!grid?.can_edit) return "Faqat ko'rish uchun";
    return undefined;
  };

  async function pick(
    onDay: string,
    studentId: number,
    what: "present" | "late" | "absent" | "remove"
  ) {
    if (!grid) return;
    const key = `${onDay}:${studentId}`;
    const before = grid.marks[key];
    const marks = { ...grid.marks };
    if (what === "remove") delete marks[key];
    else marks[key] = what === "late" ? 2 : what === "present";
    setGrid({ ...grid, marks });
    setSaving(key);
    setOpen(null);
    try {
      await api.put(`/groups/${groupId}/support-attendance`, {
        day: onDay,
        start_time: from || null,
        end_time: to || null,
        marks: [
          what === "remove"
            ? { student_id: studentId, present: false, remove: true }
            : {
                student_id: studentId,
                present: what !== "absent",
                late: what === "late",
              },
        ],
      });
    } catch (e) {
      const back = { ...grid.marks };
      if (before === undefined) delete back[key];
      else back[key] = before;
      setGrid({ ...grid, marks: back });
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(null);
      load();
    }
  }

  /** Faqat vaqtni saqlash — belgilarga tegmasdan. */
  async function saveTime() {
    if (!day) return;
    setTErr("");
    setSaving("time");
    try {
      await api.put(`/groups/${groupId}/support-attendance`, {
        day,
        start_time: from || null,
        end_time: to || null,
        marks: [],
      });
      load();
    } catch (e) {
      setTErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (err)
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-red-600 mb-2">{err}</p>
        <button onClick={load} className="text-sm text-brand-600 underline">
          Qayta urinish
        </button>
      </div>
    );
  if (!grid) return null;
  if (grid.days.length === 0)
    return (
      <EmptyState
        text={
          grid.hint ||
          "Bu guruhga support biriktirilmagan yoki uning kun/vaqti tanlanmagan."
        }
      />
    );
  if (grid.students.length === 0)
    return <EmptyState text="Guruhda o'quvchi yo'q" />;

  const marked = Object.keys(grid.marks).length;
  const present = Object.values(grid.marks).filter(
    (v) => v === true || v === 2
  ).length;
  const cur = day ? grid.sessions?.[day] : undefined;

  return (
    <div>
      <div className="mb-3 rounded-lg bg-sky-50 border border-sky-100 px-3 py-2">
        <p className="text-xs text-sky-800">
          <b>Support darsi</b>
          {grid.label ? <> — {grid.label}</> : null}. Bu jadval ustozning
          davomatidan mustaqil: bu yerdagi belgi ustoz oyligiga ham,
          o'quvchi hisobiga ham ta'sir qilmaydi.
        </p>
      </div>

      {grid.can_edit && (
        <div className="mb-3 rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-sm font-medium text-slate-800 mb-1">
            Dars qaysi vaqtdan qaysi vaqtgacha bo'ldi?
          </p>
          <p className="text-xs text-slate-500 mb-3">
            Oylik <b>aynan shu soatdan</b> hisoblanadi. Asosiy ustoz
            ko'proq vazifa bergan kuni 1.5, 2 yoki 3 soat qo'yavering —
            har kun alohida. Kelmagan o'quvchi sanalmaydi.
          </p>
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Kun</label>
              <select
                value={day}
                onChange={(e) => setDay(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                {grid.days
                  .filter((d) => d <= grid.today)
                  .map((d) => (
                    <option key={d} value={d}>
                      {dayLabel(d)}
                      {grid.sessions?.[d]
                        ? ` · ${grid.sessions[d].hours} soat`
                        : ""}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Boshlandi
              </label>
              <Time24Input
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Tugadi
              </label>
              <Time24Input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <button
              onClick={saveTime}
              disabled={saving === "time" || !day}
              className="rounded-lg bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              Vaqtni saqlash
            </button>
            {cur && (
              <span className="text-sm text-sky-700">
                {cur.start}–{cur.end} · <b>{cur.hours} soat</b> ·{" "}
                {cur.students} o'quvchi
              </span>
            )}
          </div>
          {tErr && (
            <p className="text-xs text-red-600 mt-2">{tErr}</p>
          )}
        </div>
      )}

      <p className="text-xs text-slate-500 mb-3">
        {grid.days.length} support kuni · {grid.students.length} o'quvchi
        {marked > 0 && (
          <>
            {" "}
            · davomat{" "}
            <span className="font-medium text-slate-700">
              {Math.round((present / marked) * 100)}%
            </span>{" "}
            ({present}/{marked} belgilangan)
          </>
        )}
        {grid.hours_total ? (
          <>
            {" "}
            · shu oyda{" "}
            <span className="font-medium text-sky-700">
              {grid.hours_total} soat
            </span>
          </>
        ) : null}
      </p>

      <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
        <table className="text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50">
              <th className="sticky left-0 z-20 bg-slate-50 text-left px-2 sm:px-4 py-3 font-medium text-xs uppercase text-slate-500 w-[130px] min-w-[130px] max-w-[130px] sm:w-auto sm:min-w-[200px] sm:max-w-none border-r border-slate-200 shadow-[2px_0_4px_-2px_rgba(15,23,42,0.15)]">
                Talabalar
              </th>
              {grid.days.map((d) => (
                <th
                  key={d}
                  className={`px-2 py-2 font-medium min-w-[76px] text-xs whitespace-nowrap ${
                    d > today ? "text-slate-400" : "text-slate-700"
                  }`}
                >
                  {dayLabel(d)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {grid.students.map((s, i) => (
              <tr key={s.id} className="border-t border-slate-100">
                <td className="sticky left-0 z-10 bg-white px-2 sm:px-4 py-2.5 text-xs sm:text-sm leading-snug break-words text-slate-800 w-[130px] min-w-[130px] max-w-[130px] sm:w-auto sm:min-w-0 sm:max-w-none sm:whitespace-nowrap border-r border-slate-200 shadow-[2px_0_4px_-2px_rgba(15,23,42,0.15)]">
                  <span className="text-slate-400 mr-2 text-xs">{i + 1}</span>
                  {s.full_name}
                </td>
                {grid.days.map((d) => {
                  const key = `${d}:${s.id}`;
                  const v = grid.marks[key];
                  const can = editable(d);
                  return (
                    <td
                      key={d}
                      className="px-2 py-2 text-center relative"
                      onMouseEnter={() => can && setOpen(key)}
                      onMouseLeave={() =>
                        setOpen((k) => (k === key ? null : k))
                      }
                    >
                      <button
                        onClick={() => can && setOpen(open === key ? null : key)}
                        disabled={!can || saving === key}
                        title={hint(d)}
                        className={`w-8 h-8 rounded-lg inline-flex items-center justify-center transition ${
                          v === true
                            ? "bg-sky-600 text-white"
                            : v === 2
                            ? "bg-amber-500 text-white"
                            : v === false
                            ? "bg-red-500 text-white"
                            : d > today
                            ? "bg-slate-50"
                            : "bg-slate-100 hover:bg-slate-200"
                        } ${can ? "cursor-pointer" : "cursor-not-allowed"} ${
                          !can && v === undefined ? "opacity-50" : ""
                        }`}
                      >
                        {v === true ? (
                          <Check size={15} />
                        ) : v === 2 ? (
                          <Clock size={15} />
                        ) : v === false ? (
                          <X size={15} />
                        ) : null}
                      </button>
                      {open === key && can && (
                        <MarkPicker
                          present={v as boolean | number | undefined}
                          onPick={(what) => pick(d, s.id, what)}
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
        Kunlar support biriktirilganda tanlangan kunlardan olinadi —
        asosiy dars kunlaridan emas. Belgi qo'yilgan har bir kun uchun
        seans yoziladi va oylik o'sha soatlardan chiqadi; hech kim
        kelmagan kun umuman sanalmaydi.
      </p>
    </div>
  );
}
