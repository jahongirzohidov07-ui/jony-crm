import { useEffect, useState } from "react";
import { Check, X, Plus, Trash2, Coins } from "lucide-react";
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

  useEffect(() => {
    setLoading(true);
    api
      .get<AttendanceGrid>(
        `/groups/${groupId}/attendance?year=${year}&month=${month}`
      )
      .then(setGrid)
      .finally(() => setLoading(false));
  }, [groupId, year, month]);

  /** Katakni bosganda uch holat aylanadi: belgilanmagan -> keldi ->
   *  kelmadi -> belgilanmagan emas, balki keldi (chunki "belgilanmagan"
   *  holatni backend saqlamaydi, u shunchaki yozuv yo'qligi). */
  async function toggle(lessonId: number, studentId: number) {
    if (!canEdit || !grid) return;
    const key = `${lessonId}:${studentId}`;
    const current = grid.marks[key];
    const next = current === undefined ? true : current === true ? false : true;

    setGrid({ ...grid, marks: { ...grid.marks, [key]: next } });
    setSaving(key);
    try {
      await api.put(`/lessons/${lessonId}/attendance`, {
        marks: [{ student_id: studentId, present: next }],
      });
    } catch {
      setGrid({ ...grid, marks: { ...grid.marks, [key]: current } });
    } finally {
      setSaving(null);
    }
  }

  /** Butun ustunni "hamma keldi" qilish - eng ko'p uchraydigan holat. */
  async function markAllPresent(lessonId: number) {
    if (!canEdit || !grid) return;
    const marks = grid.students.map((s) => ({ student_id: s.id, present: true }));
    const next = { ...grid.marks };
    for (const s of grid.students) next[`${lessonId}:${s.id}`] = true;
    setGrid({ ...grid, marks: next });
    await api.put(`/lessons/${lessonId}/attendance`, { marks });
  }

  /** Uy vazifasi: bajardi -> qisman -> bajarmadi -> bajardi.
   *  Davomat bilan bitta jadvalda turadi, chunki alohida ekran
   *  bo'lsa hech kim to'ldirmaydi. Belgilangan baho o'chirilmaydi —
   *  faqat boshqasiga almashtiriladi. */
  async function toggleHw(lessonId: number, studentId: number) {
    if (!canEdit || !grid) return;
    const key = `${lessonId}:${studentId}`;
    const cur = grid.homework?.[key];
    const cycle = [1, 2, 0];
    const next = cur === undefined ? 1 : cycle[(cycle.indexOf(cur) + 1) % 3];

    const hw = { ...(grid.homework || {}), [key]: next };
    // Uy vazifasi belgilansa bola darsda bo'lgan — davomat ham qo'yiladi
    const marks = { ...grid.marks };
    if (marks[key] === undefined) marks[key] = true;
    setGrid({ ...grid, homework: hw, marks });
    setSaving("hw" + key);
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
      setGrid(grid);
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
              {grid.lessons.map((ls) => (
                <th key={ls.id} className="px-2 py-2 font-medium min-w-[70px]">
                  <div
                    className={`text-xs whitespace-nowrap ${
                      ls.held ? "text-slate-700" : "text-slate-400"
                    }`}
                    title={
                      ls.held
                        ? "Dars o'tilgan"
                        : "Jadval bo'yicha reja — yoqlama qo'yilsa o'tilgan bo'ladi"
                    }
                  >
                    {dayLabel(ls.date)}
                  </div>
                  {canEdit && (
                    <button
                      onClick={() => markAllPresent(ls.id)}
                      title="Hammasini 'keldi' qilish"
                      className="text-[10px] text-slate-400 hover:text-brand-600"
                    >
                      hammasi ✓
                    </button>
                  )}
                </th>
              ))}
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
                    <td key={ls.id} className="px-2 py-2 text-center">
                      <div className="inline-flex items-center gap-1">
                        <button
                          onClick={() => toggle(ls.id, s.id)}
                          disabled={!canEdit || saving === key}
                          className={`w-8 h-8 rounded-lg inline-flex items-center justify-center transition ${
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
                        </button>
                        <button
                          onClick={() => toggleHw(ls.id, s.id)}
                          disabled={!canEdit || saving === "hw" + key}
                          title={
                            h === 1
                              ? "Uy vazifasi: bajardi"
                              : h === 2
                              ? "Uy vazifasi: qisman"
                              : h === 0
                              ? "Uy vazifasi: bajarmadi"
                              : "Uy vazifasi belgilanmagan — bosing"
                          }
                          className={`w-5 h-8 rounded text-[10px] font-bold inline-flex items-center justify-center transition ${
                            h === 1
                              ? "bg-emerald-100 text-emerald-700"
                              : h === 2
                              ? "bg-amber-100 text-amber-700"
                              : h === 0
                              ? "bg-red-100 text-red-700"
                              : "bg-slate-50 text-slate-300 hover:bg-slate-200"
                          } ${canEdit ? "cursor-pointer" : "cursor-default"}`}
                        >
                          {h === 1 ? "✓" : h === 2 ? "±" : h === 0 ? "✗" : "·"}
                        </button>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 mt-3">
        Katta katakni bosing: ✓ keldi, ✗ kelmadi. Yonidagi tor katak — uy
        vazifasi: ✓ bajardi, ± qisman, ✗ bajarmadi. Kunlar guruhning dars
        kunlaridan avtomat chiqadi — har birini alohida kiritish shart emas.
        Kulrang sana — hali yoqlama qo'yilmagan reja; u pulga ham, ustoz ish
        haqiga ham kirmaydi. Yoqlama qo'yilishi bilan dars "o'tilgan" bo'ladi.
      </p>
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
