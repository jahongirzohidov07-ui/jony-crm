import { SectionInsights } from "../components/SectionInsights";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, X, Pencil, Search , Trash2, Archive as ArchiveIcon } from "lucide-react";
import { EmptyGroupsDialog } from "../components/GroupArchive";
import {
  api, ApiError, getGlobalBranch, type Group, type Teacher,
  type Branch, type Room,
  type CheckProblem,
  type CareerMap,
} from "../lib/api";
import { formatSom } from "../lib/format";
import { Time24Input } from "../components/Time24Input";
import { useAuth } from "../lib/AuthContext";
import { ADMINISTRATOR, SALES_MANAGER, GROUP_MANAGE, SUPPORT_ASSIGN, can } from "../lib/roles";
import {
  SUBJECTS, levelsFor, subjectLine, WEEKDAYS, parseDays,
} from "../lib/subjects";
import { useReference } from "../components/PickList";
import { ScheduleProblems } from "../components/ScheduleProblems";

export function GroupFormModal({
  teachers,
  branches,
  defaultBranchId,
  initial,
  submitLabel,
  onClose,
  onSaved,
}: {
  teachers: Teacher[];
  branches: Branch[];
  defaultBranchId: number | null;
  initial?: Group;
  submitLabel: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  // Nom avtomat qo'yiladi ("J/Z - Group 01/25"). Foydalanuvchi qo'lda
  // tekkanidan keyin biz unga boshqa tegmaymiz.
  const [nameTouched, setNameTouched] = useState(!!initial);
  const [room, setRoom] = useState(initial?.room ?? "");
  const [roomId, setRoomId] = useState<string>(
    initial?.room_id ? String(initial.room_id) : ""
  );
  const [rooms, setRooms] = useState<Room[]>([]);
  const [teacherId, setTeacherId] = useState(
    initial?.teacher_id ? String(initial.teacher_id) : ""
  );
  const [branchId, setBranchId] = useState(
    initial?.branch_id
      ? String(initial.branch_id)
      : defaultBranchId
      ? String(defaultBranchId)
      : ""
  );
  const [lessonPrice, setLessonPrice] = useState(
    String(initial?.lesson_price ?? 40000)
  );
  const [standardLessons, setStandardLessons] = useState(
    String(initial?.standard_lessons_per_month ?? 12)
  );
  const [teacherRate, setTeacherRate] = useState(
    String(initial?.teacher_rate_per_student ?? 0)
  );
  // Stavka DARAJADAN avtomat olinadi; faqat istisno holatda qo'lda.
  const [rateManual, setRateManual] = useState(initial?.rate_manual === 1);
  const [gradeRates, setGradeRates] = useState<
    Record<string, { label: string; rate: number }>
  >({});
  useEffect(() => {
    api.get<CareerMap>("/career")
      .then((d) =>
        setGradeRates(Object.fromEntries(d.grades.map((g) => [
          g.key, { label: g.label, rate: g.rate_per_student },
        ]))))
      .catch(() => setGradeRates({}));
  }, []);
  const [subject, setSubject] = useState(initial?.subject ?? "english");
  const [level, setLevel] = useState(initial?.level ?? "");
  const [startDate, setStartDate] = useState(
    initial?.start_date ?? new Date().toISOString().slice(0, 10)
  );
  const [endDate, setEndDate] = useState(initial?.end_date ?? "");
  const [lessonTime, setLessonTime] = useState(initial?.lesson_time ?? "");
  const [days, setDays] = useState<string[]>(
    parseDays(initial?.lesson_days).length
      ? parseDays(initial?.lesson_days)
      : ["mon", "wed", "fri"]
  );
  // Kunlar tez tanlanadi: TOQ (du-chor-ju) / JUFT (se-pay-shan) /
  // BOSHQA (bitta-bitta). Mavjud guruh qaysi to'plamga tushsa, o'sha
  // rejim yoqilib turadi.
  const ODD_DAYS = ["mon", "wed", "fri"];
  const EVEN_DAYS = ["tue", "thu", "sat"];
  const sameDays = (a: string[], b: string[]) =>
    a.length === b.length && b.every((d) => a.includes(d));
  const initDays = parseDays(initial?.lesson_days);
  const [dayMode, setDayMode] = useState<"odd" | "even" | "custom">(
    initDays.length === 0 || sameDays(initDays, ODD_DAYS)
      ? "odd"
      : sameDays(initDays, EVEN_DAYS)
      ? "even"
      : "custom"
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Avtomatik tekshiruvlar: ustoz/xona to'qnashuvi, yuklama, bo'shliq
  const [problems, setProblems] = useState<CheckProblem[]>([]);
  const [canForce, setCanForce] = useState(false);

  const ref = useReference();

  useEffect(() => {
    api.get<Room[]>("/rooms").then(setRooms).catch(() => setRooms([]));
  }, []);

  // Yangi guruh: ustoz yoki boshlanish sanasi tanlangach nom o'zi
  // to'ldiriladi. Tahrirlashda ishlamaydi.
  useEffect(() => {
    if (initial || nameTouched) return;
    const q = new URLSearchParams();
    if (teacherId) q.set("teacher_id", teacherId);
    if (startDate) q.set("on", startDate);
    api
      .get<{ name: string }>(`/group-name/suggest?${q.toString()}`)
      .then((d) => setName(d.name))
      .catch(() => undefined);
  }, [teacherId, startDate, nameTouched, initial]);

  const lessonPriceNum = Number(lessonPrice) || 0;
  const standardLessonsNum = Number(standardLessons) || 0;
  const computedMonthlyFee = lessonPriceNum * standardLessonsNum;

  async function submit(force = false) {
    if (!name.trim()) {
      setError("Guruh nomini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    if (!force) setProblems([]);
    try {
      const payload = {
        name,
        room: room || null,
        room_id: roomId ? Number(roomId) : null,
        teacher_id: teacherId ? Number(teacherId) : null,
        branch_id: branchId ? Number(branchId) : null,
        monthly_fee: computedMonthlyFee,
        lesson_price: lessonPriceNum,
        standard_lessons_per_month: standardLessonsNum,
        teacher_rate_per_student: rateManual ? Number(teacherRate) || 0 : 0,
        subject: subject || null,
        level: level || null,
        start_date: startDate || null,
        end_date: endDate || null,
        lesson_time: lessonTime || null,
        lesson_days: days.length ? days.join(",") : null,
      };
      const q = force ? "?force=true" : "";
      if (initial) {
        await api.put(`/groups/${initial.id}${q}`, payload);
      } else {
        await api.post(`/groups${q}`, payload);
      }
      onSaved();
      onClose();
    } catch (e) {
      if (e instanceof ApiError && e.problems.length) {
        setProblems(e.problems);
        setCanForce(e.canForce);
        setError(null);
      } else {
        setError(e instanceof Error ? e.message : "Xatolik");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {initial ? "Guruhni tahrirlash" : "Yangi guruh"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Nomi *</label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => {
                setNameTouched(true);
                setName(e.target.value);
              }}
              placeholder="J/Z - Group 01/25"
              autoFocus
            />
            {!initial && !nameTouched && (
              <p className="text-xs text-slate-400 mt-1">
                Nom o'zi qo'yildi: ustoz harflari + guruh ochilgan oy/yil.
                Xohlasangiz shu yerda o'zgartiring.
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Fan</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  // Fan o'zgarsa daraja tozalanadi - rus tilida "Step 1" yo'q.
                  setLevel("");
                }}
              >
                <option value="">— tanlanmagan —</option>
                {SUBJECTS.map((x) => (
                  <option key={x.key} value={x.key}>{x.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Daraja</label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white disabled:bg-slate-100"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                disabled={!subject}
              >
                <option value="">— tanlanmagan —</option>
                {levelsFor(subject).map((l) => (
                  <option key={l.key} value={l.key}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Boshlanish sanasi
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Tugash sanasi
              </label>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
              <p className="text-xs text-slate-400 mt-1">
                Ixtiyoriy — ko'rsatilsa, shundan keyin dars kunlari
                yaratilmaydi.
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Dars boshlanish vaqti
              </label>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                value={lessonTime}
                onChange={(e) => setLessonTime(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {(ref?.lesson_times ?? []).map((t) => (
                  <option key={t.start} value={t.start}>
                    {t.label}
                  </option>
                ))}
              </select>
              {lessonTime && (
                <p className="text-xs text-slate-400 mt-1">
                  Har dars {ref?.lesson_minutes ?? 120} daqiqa — tugash vaqti
                  avtomat hisoblandi.
                </p>
              )}
            </div>
          </div>
          <p className="text-xs text-slate-400 -mt-1">
            Yoqlama boshlanish sanasidan boshlanadi — undan oldingi kunga dars
            belgilab bo'lmaydi.
          </p>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Dars kunlari
            </label>
            <div className="flex gap-1.5 mb-2">
              {([
                { k: "odd", l: "Toq kunlar", hint: "Du · Chor · Ju" },
                { k: "even", l: "Juft kunlar", hint: "Se · Pay · Shan" },
                { k: "custom", l: "Boshqa kunlar", hint: "o'zingiz tanlaysiz" },
              ] as const).map((m) => (
                <button
                  key={m.k}
                  type="button"
                  onClick={() => {
                    setDayMode(m.k);
                    if (m.k === "odd") setDays(ODD_DAYS);
                    else if (m.k === "even") setDays(EVEN_DAYS);
                  }}
                  className={`flex-1 px-2 py-2 rounded-lg text-xs font-medium border transition text-center ${
                    dayMode === m.k
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {m.l}
                  <span className="block text-[10px] font-normal opacity-70">
                    {m.hint}
                  </span>
                </button>
              ))}
            </div>
            {dayMode === "custom" && (
              <div className="flex flex-wrap gap-1.5">
                {WEEKDAYS.map((d) => {
                  const on = days.includes(d.key);
                  return (
                    <button
                      key={d.key}
                      type="button"
                      onClick={() =>
                        setDays(on ? days.filter((x) => x !== d.key) : [...days, d.key])
                      }
                      className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                        on
                          ? "bg-brand-50 border-brand-400 text-brand-700"
                          : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                      }`}
                    >
                      {d.label}
                    </button>
                  );
                })}
              </div>
            )}
            <p className="text-xs text-slate-400 mt-1.5">
              Tanlangan kunlar butun oy bo'yicha yoqlama jadvaliga avtomat
              chiqadi — har bir darsni alohida kiritish shart emas.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Xona
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={roomId}
              onChange={(e) => {
                setRoomId(e.target.value);
                const r = rooms.find((x) => String(x.id) === e.target.value);
                setRoom(r ? r.name : "");
              }}
            >
              <option value="">— tanlanmagan —</option>
              {rooms
                .filter(
                  (r) =>
                    !branchId || String(r.branch_id ?? "") === branchId
                )
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.capacity} o'rin)
                  </option>
                ))}
            </select>
            <p className="text-xs text-slate-400 mt-1">
              Xona sig'imi guruh to'lishi koeffitsiyentini hisoblashda
              ishlatiladi. Xona ro'yxati — O'quv bo'limi → Xonalar.
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Filial</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={branchId}
              onChange={(e) => setBranchId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">O'qituvchi</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={teacherId}
              onChange={(e) => setTeacherId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {/* FAQAT ISHLAYOTGAN va SHU FILIAL ustozlari, filiali bilan
                  (2026-10-03: ikki "Rayxona" chalkashib, Zafardan
                  ishdan ketgan ustoz Bekobod 1 guruhiga tanlangan edi —
                  sentabr oyligi unga yozilib qoldi). Guruhda turgan
                  ustoz ro'yxatda bo'lmasa ham ko'rinadi. */}
              {teachers
                .filter((t) =>
                  String(t.id) === teacherId ||
                  (t.is_active !== 0 &&
                    (!branchId || !t.branch_ids?.length ||
                      t.branch_ids.includes(Number(branchId)))))
                .map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name}
                    {t.branches_label ? ` — ${t.branches_label}` : ""}
                    {t.is_active === 0 ? " (ishdan ketgan)" : ""}
                  </option>
                ))}
            </select>
          </div>

          <div className="border-t border-slate-100 pt-3 mt-1">
            <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
              Dars-asosidagi hisoblash
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  1 dars narxi (so'm)
                </label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={lessonPrice}
                  onChange={(e) => setLessonPrice(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  Standart dars/oy
                </label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={standardLessons}
                  onChange={(e) => setStandardLessons(e.target.value)}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Standart oy narxi: {formatSom(computedMonthlyFee)}. Bundan ortiq
              o'tilgan darslar (masalan 13-14-chi) talabaga bepul hisoblanadi.
            </p>
            <div className="mt-3">
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Ustoz stavkasi (1 talabadan, to'liq oy uchun)
              </label>
              {(() => {
                const t = teachers.find((x) => String(x.id) === teacherId);
                const gi = t?.grade ? gradeRates[t.grade] : undefined;
                if (!rateManual) {
                  return (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 flex items-center justify-between gap-2">
                      <span>
                        {!teacherId
                          ? "Ustoz tanlanganda darajasidan avtomat olinadi"
                          : gi
                          ? `${formatSom(gi.rate)} — ${gi.label} darajasidan avtomat`
                          : "Ustozga daraja belgilanmagan (0 so'm)"}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setRateManual(true);
                          setTeacherRate(String(gi?.rate ?? 0));
                        }}
                        className="text-xs text-slate-400 hover:text-brand-600 shrink-0"
                      >
                        qo'lda kiritish
                      </button>
                    </div>
                  );
                }
                return (
                  <>
                    <input
                      type="number"
                      className="w-full rounded-lg border border-amber-300 px-3 py-2 text-sm"
                      value={teacherRate}
                      onChange={(e) => setTeacherRate(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setRateManual(false)}
                      className="text-xs text-brand-600 mt-1"
                    >
                      ← Darajadan avtomat olishga qaytarish
                    </button>
                  </>
                );
              })()}
              <p className="text-xs text-slate-400 mt-1">
                Ustoz darajasi o'zgarsa, stavka ham o'zi yangilanadi
                (qo'lda kiritilgan guruhlarga tegilmaydi).
              </p>
            </div>
          </div>

          <ScheduleProblems
            problems={problems}
            canForce={canForce}
            saving={saving}
            onForce={() => submit(true)}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={() => submit()}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-2 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : submitLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Groups() {
  const { user } = useAuth();
  const [groups, setGroups] = useState<Group[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  // Bo'sh guruhlarni arxivlash (2026-09-30)
  const [showEmpty, setShowEmpty] = useState(false);
  const [editing, setEditing] = useState<Group | null>(null);
  // Ro'yxatdan turib tez tahrirlash
  const [supFor, setSupFor] = useState<Group | null>(null);
  const [teachFor, setTeachFor] = useState<Group | null>(null);

  // Filtrlar
  const [q, setQ] = useState("");
  const [teacherFilter, setTeacherFilter] = useState("");
  // 2026-08-12, Jahongir: "ustozlar filtri ichida supportlar bor,
  // lekin supportni tanlasa guruh chiqmayapti - alohida supportlar
  // kesimida filtr kerak"
  const [supportFilter, setSupportFilter] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("");
  const [branchFilter, setBranchFilter] = useState("");

  function load() {
    setLoading(true);
    Promise.all([
      api.get<Group[]>("/groups"),
      api.get<Teacher[]>("/teachers"),
      api.get<Branch[]>("/branches"),
    ])
      .then(([g, t, b]) => {
        setGroups(g);
        setTeachers(t);
        setBranches(b);
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);
  const canEdit = can(user?.role, GROUP_MANAGE);
  const canCreate = can(user?.role, [...GROUP_MANAGE, ADMINISTRATOR, SALES_MANAGER]);
  const canSupport = can(user?.role, SUPPORT_ASSIGN);

  async function removeGroup(g: Group) {
    if (!confirm(`"${g.name}" guruhi arxivga o'tkazilsinmi?\n\nYo'qlama va barcha ma'lumotlar saqlanadi. Guruh dars jadvalidan olib tashlanadi.`)) return;
    try {
      await api.delete(`/groups/${g.id}`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "O'chirib bo'lmadi");
    }
  }

  const filtered = groups.filter((g) => {
    if (q && !g.name.toLowerCase().includes(q.toLowerCase())) return false;
    if (teacherFilter && String(g.teacher_id ?? "") !== teacherFilter) return false;
    if (supportFilter &&
        !(g.support_label || "")
          .toLowerCase()
          .includes(supportFilter.toLowerCase())) return false;
    if (subjectFilter && g.subject !== subjectFilter) return false;
    if (branchFilter && String(g.branch?.id ?? "") !== branchFilter)
      return false;
    return true;
  });

  const hasFilter =
    q || teacherFilter || supportFilter || subjectFilter || branchFilter;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Guruhlar ro'yxati</h1>
          <p className="text-sm text-slate-500">
            {hasFilter
              ? `${filtered.length} ta topildi (jami ${groups.length})`
              : `Jami: ${groups.length}`}
          </p>
        </div>
        {canCreate && (
          <div className="flex items-center gap-2">
            {/* BO'SH GURUHLAR (2026-09-30, Jahongir: "guruhda o'quvchi
                qolmagan yoki faol bo'lmagan guruhlarni arxivga tushirib
                ko'rinmaydigan qilish") */}
            {canEdit && <button
              onClick={() => setShowEmpty(true)}
              className="flex items-center gap-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg px-3 py-2 text-sm font-medium"
            >
              <ArchiveIcon size={16} /> Bo'sh guruhlar
            </button>}
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
            >
              <Plus size={16} /> Yangi guruh
            </button>
          </div>
        )}
      </div>

      {/* 2026-10-22, Jahongir: "guruhlar bo'limida barchartni olib
          tashla" — faqat ko'rsatkich kartalari qoladi */}
      <SectionInsights section="groups" charts={false} />

      <div className="flex flex-wrap items-center gap-2 mb-5">
        <div className="relative">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            className="rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm w-56"
            placeholder="Nomi bo'yicha qidirish"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        {branches.length > 1 && (
          <select
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            value={branchFilter}
            onChange={(e) => setBranchFilter(e.target.value)}
          >
            <option value="">Barcha filiallar</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        )}
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
        >
          <option value="">Barcha fanlar</option>
          {SUBJECTS.map((s) => (
            <option key={s.key} value={s.key}>
              {s.label}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={teacherFilter}
          onChange={(e) => setTeacherFilter(e.target.value)}
        >
          <option value="">Barcha o'qituvchilar</option>
          {teachers
            .filter((t) => t.kind !== "support")
            .map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
          value={supportFilter}
          onChange={(e) => setSupportFilter(e.target.value)}
        >
          <option value="">Barcha supportlar</option>
          {teachers
            .filter((t) => t.kind === "support" && t.is_active !== 0)
            .map((t) => (
              <option key={t.id} value={(t.full_name || "").trim()}>
                {(t.full_name || "").trim()}
              </option>
            ))}
        </select>
        {hasFilter && (
          <button
            onClick={() => {
              setQ("");
              setTeacherFilter("");
              setSupportFilter("");
              setSubjectFilter("");
              setBranchFilter("");
            }}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Tozalash
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium w-12">T/R</th>
                <th className="text-left px-4 py-3 font-medium">Nomi</th>
                <th className="text-right px-4 py-3 font-medium">Narx</th>
                <th className="text-left px-4 py-3 font-medium">Dars vaqti</th>
                <th className="text-left px-4 py-3 font-medium">Kurs</th>
                <th className="text-left px-4 py-3 font-medium">O'qituvchi</th>
                <th className="text-left px-4 py-3 font-medium">Dars kunlari</th>
                {canEdit && <th className="px-4 py-3"></th>}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                    {hasFilter ? "Guruh topilmadi" : "Hali guruh qo'shilmagan"}
                  </td>
                </tr>
              )}
              {filtered.map((g, i) => (
                <tr key={g.id} data-guide={i === 0 ? "group-row-first" : undefined} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-400">{i + 1}.</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/groups/${g.id}`}
                      className="font-medium text-slate-800 hover:text-brand-700"
                    >
                      {g.name}
                    </Link>
                    <span className="text-slate-400 ml-1.5">[{g.student_count}]</span>
                    {!!g.frozen_count && (
                      <span
                        title="Muzlatilgan o'quvchilar — songa kirmaydi, lekin guruhda turishadi"
                        className="ml-1.5 text-[10px] text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded"
                      >
                        +{g.frozen_count} muzlatilgan
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600 whitespace-nowrap">
                    {formatSom(g.monthly_fee)}
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                    {g.lesson_time || "—"}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-slate-700">
                      {subjectLine(g) || "—"}
                    </span>
                    {g.room && (
                      <span className="text-brand-600 ml-1.5">[{g.room}]</span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      <span className="text-slate-700">
                        {g.teacher?.full_name || "—"}
                      </span>
                      {canEdit && (
                        <button
                          onClick={() => setTeachFor(g)}
                          title="Ustozni almashtirish"
                          className="text-slate-300 hover:text-brand-600"
                        >
                          <Pencil size={13} />
                        </button>
                      )}
                    </span>
                    {g.teacher_rate_per_student > 0 && (
                      <span className="block text-xs text-slate-400">
                        {formatSom(g.teacher_rate_per_student)}/talaba
                      </span>
                    )}
                    {g.support_label ? (
                      <span
                        onClick={() => canSupport && setSupFor(g)}
                        title={canSupport ? "Supportni o'zgartirish" : undefined}
                        className={`block text-xs text-sky-600 ${
                          canSupport
                            ? "cursor-pointer hover:underline"
                            : ""
                        }`}
                      >
                        Support: {g.support_label}
                      </span>
                    ) : (
                      <span
                        onClick={() => canSupport && setSupFor(g)}
                        title={canSupport ? "Support biriktirish" : undefined}
                        className={`block text-xs text-amber-500 ${
                          canSupport
                            ? "cursor-pointer hover:underline"
                            : ""
                        }`}
                      >
                        Support yo'q{canSupport ? " — biriktirish" : ""}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {parseDays(g.lesson_days).length === 0 ? (
                        <span className="text-slate-400">—</span>
                      ) : (
                        WEEKDAYS.filter((d) =>
                          parseDays(g.lesson_days).includes(d.key)
                        ).map((d) => (
                          <span
                            key={d.key}
                            className="bg-brand-50 text-brand-700 rounded px-1.5 py-0.5 text-xs"
                          >
                            {d.label}
                          </span>
                        ))
                      )}
                    </div>
                  </td>
                  {canEdit && (
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <button
                        onClick={() => setEditing(g)}
                        title="Tahrirlash"
                        className="text-slate-400 hover:text-brand-600"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        onClick={() => removeGroup(g)}
                        title="Arxivga o'tkazish"
                        className="text-slate-300 hover:text-red-600 ml-2"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showEmpty && (
        <EmptyGroupsDialog onClose={() => setShowEmpty(false)} onDone={load} />
      )}
      {showAdd && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          submitLabel="Qo'shish"
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          initial={editing}
          submitLabel="Saqlash"
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
      {supFor && (
        <GroupSupportsModal
          group={supFor}
          onClose={() => setSupFor(null)}
          onSaved={() => {
            setSupFor(null);
            load();
          }}
        />
      )}
      {teachFor && (
        <ChangeTeacherModal
          group={teachFor}
          teachers={teachers}
          onClose={() => setTeachFor(null)}
          onSaved={() => {
            setTeachFor(null);
            load();
          }}
        />
      )}
    </div>
  );
}


// ---------------------------------------------------------------
// SUPPORT BIRIKTIRISH \u2014 Guruhlar ro'yxatidan turib, kartaga kirmasdan.
// Har support uchun DARS KUNI va VAQTI so'raladi \u2014 jadval shunga quriladi
// (asosiy dars vaqti emas!). Vaqt boshqa bandlik bilan to'qnashsa \u2014
// ogohlantirish.
type SupOption = { user_id: number; name: string; branch?: string | null };
type SupTime = { days: string[]; start: string; end: string };

function GroupSupportsModal({
  group,
  onClose,
  onSaved,
}: {
  group: Group;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [sel, setSel] = useState<Record<number, SupTime>>({});
  const [options, setOptions] = useState<SupOption[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<{
        assigned: {
          user_id: number;
          days: string | null;
          start: string | null;
          end: string | null;
        }[];
        options: SupOption[];
      }>(`/groups/${group.id}/supports`)
      .then((r) => {
        const m: Record<number, SupTime> = {};
        for (const a of r.assigned) {
          m[a.user_id] = {
            days: parseDays(a.days),
            start: a.start ?? "",
            end: a.end ?? "",
          };
        }
        setSel(m);
        setOptions(r.options);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }, [group.id]);

  function toggle(id: number) {
    setSel((m) => {
      const n = { ...m };
      if (n[id]) delete n[id];
      else n[id] = { days: parseDays(group.lesson_days), start: "", end: "" };
      return n;
    });
  }

  function patch(id: number, p: Partial<SupTime>) {
    setSel((m) => ({ ...m, [id]: { ...m[id], ...p } }));
  }

  async function save(force?: boolean) {
    for (const [uid, t] of Object.entries(sel)) {
      const filled = t.days.length > 0 || t.start || t.end;
      if (filled && (!t.days.length || !t.start || !t.end)) {
        const nm = options.find((o) => o.user_id === Number(uid))?.name;
        setErr(`${nm ?? "Support"} uchun kun va vaqtni to'liq kiriting`);
        return;
      }
    }
    setSaving(true);
    setErr("");
    try {
      await api.put(
        `/groups/${group.id}/supports${force ? "?force=true" : ""}`,
        {
          items: Object.entries(sel).map(([uid, t]) => ({
            user_id: Number(uid),
            days: t.days.length ? t.days.join(",") : null,
            start: t.start || null,
            end: t.end || null,
          })),
        }
      );
      onSaved();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        if (confirm(e.message + "\\n\\nBaribir biriktirilsinmi?")) {
          save(true);
          return;
        }
      } else {
        setErr(e instanceof Error ? e.message : "Xatolik");
      }
    } finally {
      setSaving(false);
    }
  }

  const shown = options.filter(
    (o) => !q || o.name.toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-900">
            Support biriktirish
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          "{group.name}" guruhi. Support darsi asosiy darsdan ALOHIDA
          vaqtda o'tadi \u2014 kuni va vaqtini belgilang.
        </p>
        {loading ? (
          <p className="text-sm text-slate-400 py-4">Yuklanmoqda...</p>
        ) : (
          <>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Support ismini qidirish..."
              autoFocus
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm mb-2"
            />
            <div className="space-y-1 max-h-72 overflow-y-auto mb-2">
              {shown.map((o) => (
                <div key={o.user_id}>
                  <label className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-50 text-sm text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={!!sel[o.user_id]}
                      onChange={() => toggle(o.user_id)}
                    />
                    {o.name}
                    {o.branch && (
                      <span className="text-xs text-slate-400">{o.branch}</span>
                    )}
                  </label>
                  {sel[o.user_id] && (
                    <div className="ml-7 mb-2 rounded-lg bg-slate-50 border border-slate-100 p-2">
                      <div className="flex flex-wrap gap-1 mb-1.5">
                        {WEEKDAYS.map((d) => {
                          const on = sel[o.user_id].days.includes(d.key);
                          return (
                            <button
                              key={d.key}
                              type="button"
                              onClick={() =>
                                patch(o.user_id, {
                                  days: on
                                    ? sel[o.user_id].days.filter(
                                        (x) => x !== d.key
                                      )
                                    : [...sel[o.user_id].days, d.key],
                                })
                              }
                              className={`px-1.5 py-0.5 rounded text-[11px] font-medium border ${
                                on
                                  ? "bg-brand-50 border-brand-400 text-brand-700"
                                  : "bg-white border-slate-200 text-slate-500"
                              }`}
                            >
                              {d.label}
                            </button>
                          );
                        })}
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Time24Input
                          value={sel[o.user_id].start}
                          onChange={(e) =>
                            patch(o.user_id, { start: e.target.value })
                          }
                          className="rounded-md border border-slate-200 px-2 py-1 text-xs"
                        />
                        <span className="text-slate-400 text-xs">\u2014</span>
                        <Time24Input
                          value={sel[o.user_id].end}
                          onChange={(e) =>
                            patch(o.user_id, { end: e.target.value })
                          }
                          className="rounded-md border border-slate-200 px-2 py-1 text-xs"
                        />
                        <span className="text-[10px] text-slate-400 ml-1">
                          support darsi vaqti
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {shown.length === 0 && (
                <p className="text-sm text-slate-400 py-2">
                  Support teacher topilmadi.
                </p>
              )}
            </div>
            {Object.keys(sel).length > 0 && (
              <p className="text-xs text-slate-500 mb-2">
                Tanlangan: {Object.keys(sel).length} ta support
              </p>
            )}
            {err && <p className="text-xs text-red-600 mb-2">{err}</p>}
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => save()}
                disabled={saving}
                className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-60"
              >
                {saving ? "Saqlanmoqda..." : "Saqlash"}
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
              >
                Bekor
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------
// USTOZNI ALMASHTIRISH — ro'yxatdan turib, bitta tanlov bilan
function ChangeTeacherModal({
  group,
  teachers,
  onClose,
  onSaved,
}: {
  group: Group;
  teachers: Teacher[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [val, setVal] = useState<string>(
    group.teacher_id ? String(group.teacher_id) : ""
  );
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  // Asosiy ustozlar; guruh filialidagilar birinchi turadi
  const list = teachers
    .filter((t) => t.kind !== "support" && t.is_active !== 0)
    .sort((a, b) => {
      const ab = a.branch_id === group.branch?.id ? 0 : 1;
      const bb = b.branch_id === group.branch?.id ? 0 : 1;
      return ab !== bb
        ? ab - bb
        : a.full_name.localeCompare(b.full_name);
    });

  async function save(force?: boolean) {
    setSaving(true);
    setErr("");
    try {
      await api.put(`/groups/${group.id}${force ? "?force=true" : ""}`, {
        teacher_id: val ? Number(val) : null,
      });
      onSaved();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        if (confirm(e.message + "\n\nBaribir almashtirilsinmi?")) {
          save(true);
          return;
        }
      } else {
        setErr(e instanceof Error ? e.message : "Xatolik");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-sm p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-900">
            Ustozni almashtirish
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          "{group.name}" guruhi — hozirgi ustoz:{" "}
          {group.teacher?.full_name || "yo'q"}
        </p>
        <select
          value={val}
          onChange={(e) => setVal(e.target.value)}
          autoFocus
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white mb-2"
        >
          <option value="">— O'qituvchisiz —</option>
          {list.map((t) => (
            <option key={t.id} value={t.id}>
              {t.full_name}
              {t.branch_id !== group.branch?.id && t.branch?.name
                ? ` (${t.branch.name})`
                : ""}
            </option>
          ))}
        </select>
        {err && <p className="text-xs text-red-600 mb-2">{err}</p>}
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => save()}
            disabled={saving}
            className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Almashtirish"}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor
          </button>
        </div>
      </div>
    </div>
  );
}
