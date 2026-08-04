import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, X, Pencil, Search , Trash2 } from "lucide-react";
import {
  api, ApiError, type Group, type Teacher, type Branch, type Room,
  type CheckProblem,
  type CareerMap,
} from "../lib/api";
import { formatSom } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { GROUP_MANAGE, can } from "../lib/roles";
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
              onChange={(e) => setName(e.target.value)}
              placeholder="Masalan: IELTS 1.0"
              autoFocus
            />
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
              {rooms.map((r) => (
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
              {teachers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.full_name}
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
  const [editing, setEditing] = useState<Group | null>(null);

  // Filtrlar
  const [q, setQ] = useState("");
  const [teacherFilter, setTeacherFilter] = useState("");
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

  async function removeGroup(g: Group) {
    if (!confirm(`"${g.name}" guruhi o'chirilsinmi?\n\nIchida o'quvchi`
      + ` yoki yoqlama tarixi bo'lsa, tizim o'zi to'xtatadi.`)) return;
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
    if (subjectFilter && g.subject !== subjectFilter) return false;
    if (branchFilter && String(g.branch?.id ?? "") !== branchFilter)
      return false;
    return true;
  });

  const hasFilter = q || teacherFilter || subjectFilter || branchFilter;

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
        {canEdit && (
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
          >
            <Plus size={16} /> Yangi guruh qo'shish
          </button>
        )}
      </div>

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
          {teachers.map((t) => (
            <option key={t.id} value={t.id}>
              {t.full_name}
            </option>
          ))}
        </select>
        {hasFilter && (
          <button
            onClick={() => {
              setQ("");
              setTeacherFilter("");
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
                <tr key={g.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-400">{i + 1}.</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/groups/${g.id}`}
                      className="font-medium text-slate-800 hover:text-brand-700"
                    >
                      {g.name}
                    </Link>
                    <span className="text-slate-400 ml-1.5">[{g.student_count}]</span>
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
                    <span className="text-slate-700">
                      {g.teacher?.full_name || "—"}
                    </span>
                    {g.teacher_rate_per_student > 0 && (
                      <span className="block text-xs text-slate-400">
                        {formatSom(g.teacher_rate_per_student)}/talaba
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
                        title="O'chirish"
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

      {showAdd && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          submitLabel="Qo'shish"
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <GroupFormModal
          teachers={teachers}
          branches={branches}
          defaultBranchId={user?.branch_id ?? null}
          initial={editing}
          submitLabel="Saqlash"
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
    </div>
  );
}
