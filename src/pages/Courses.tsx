import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, CalendarClock, BookOpen } from "lucide-react";
import { api, type Course, type Branch } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { FOUNDER } from "../lib/roles";
import { SUBJECTS } from "../lib/subjects";

/**
 * KURSLAR — filialning narx ro'yxati (2026-08-15).
 *
 * Jahongir: "sozlamalar ichida kurslar bolimini ochib u yerda
 * kurslarni yozadi dars vaqti narxini bitta darsga narxini yozadi,
 * shu narxlar hamma joyga ulanadi va shu boyicha hisob kitob
 * qilinaveradi bizda ham sentabrdan narxlar oshadi".
 *
 * Har filialning O'Z kurslari bo'ladi — hamkor markazda fanlar,
 * narx va dars davomiyligi butunlay boshqacha bo'lishi mumkin.
 */
export default function Courses() {
  const { user } = useAuth();
  const isFounder = user?.role === FOUNDER;
  const [rows, setRows] = useState<Course[] | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Course | null>(null);
  const [priceFor, setPriceFor] = useState<Course | null>(null);
  const [err, setErr] = useState("");

  const load = () => {
    api
      .fresh<Course[]>("/courses")
      .then(setRows)
      .catch(() => setRows([]));
    if (isFounder)
      api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  };
  useEffect(load, []);

  async function remove(c: Course) {
    if (!confirm(`"${c.name}" kursi o'chirilsinmi?`)) return;
    try {
      await api.delete(`/courses/${c.id}`);
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }

  if (rows === null)
    return <p className="p-8 text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div className="p-8">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Kurslar</h2>
          <p className="mt-1 text-sm text-slate-500 max-w-2xl">
            Har bir kursga dars davomiyligi va <b>bitta dars narxi</b>{" "}
            yoziladi. Guruh kursni tanlaganda narx o'sha guruhga
            ko'chadi va butun hisob-kitob shu bo'yicha ketadi. Narxni
            kelajakdagi sanadan boshlab oshirish mumkin — o'sha kun
            kelguncha eski narx ishlaydi, o'tgan oylarga esa hech
            qachon tegilmaydi.
          </p>
        </div>
        <button
          onClick={() => {
            setEditing(null);
            setModal(true);
          }}
          className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus size={15} /> Kurs qo'shish
        </button>
      </div>

      {err && (
        <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
          {err}
        </p>
      )}

      {rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center">
          <BookOpen size={22} className="mx-auto text-slate-300" />
          <p className="mt-2 text-sm text-slate-500">
            Hali kurs qo'shilmagan. Birinchi kursni qo'shing — keyin
            guruhlar narxni shundan oladi.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((c) => (
            <div
              key={c.id}
              className={`rounded-xl border bg-white p-4 ${
                c.active ? "border-slate-200" : "border-slate-200 opacity-60"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-900 leading-tight">
                    {c.name}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {[c.subject_label, c.level, c.branch]
                      .filter(Boolean)
                      .join(" · ") || "—"}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button
                    onClick={() => {
                      setEditing(c);
                      setModal(true);
                    }}
                    className="p-1 text-slate-300 hover:text-brand-600"
                    title="Tahrirlash"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => remove(c)}
                    className="p-1 text-slate-300 hover:text-red-500"
                    title="O'chirish"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <div className="mt-3 flex items-baseline gap-1.5">
                <span className="text-lg font-bold text-slate-900">
                  {formatSom(c.lesson_price)}
                </span>
                <span className="text-xs text-slate-400">/ bitta dars</span>
              </div>
              <p className="text-xs text-slate-500">
                {c.lesson_minutes || "—"} daqiqa · oyiga{" "}
                {c.lessons_per_month || "—"} dars ·{" "}
                <b>{formatSom(c.monthly_fee || 0)}</b> oylik
              </p>

              <p className="mt-2 text-xs text-slate-400">
                {c.groups > 0
                  ? `${c.groups} ta guruh: ${(c.group_names || []).join(", ")}`
                  : "Hali guruh biriktirilmagan"}
              </p>

              {c.next_change && (
                <p className="mt-2 flex items-start gap-1.5 rounded-lg bg-amber-50 px-2 py-1.5 text-[11px] leading-snug text-amber-800">
                  <CalendarClock size={12} className="mt-0.5 shrink-0" />
                  <span>
                    {formatDate(c.next_change.from_date)} dan —{" "}
                    <b>{formatSom(c.next_change.lesson_price)}</b>
                    {c.next_change.note ? ` · ${c.next_change.note}` : ""}
                  </span>
                </p>
              )}

              <button
                onClick={() => setPriceFor(c)}
                className="mt-3 w-full rounded-lg border border-slate-300 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                Narxni sanadan boshlab o'zgartirish
              </button>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <CourseModal
          initial={editing}
          branches={branches}
          isFounder={isFounder}
          onClose={() => setModal(false)}
          onSaved={() => {
            setModal(false);
            load();
          }}
          onError={setErr}
        />
      )}
      {priceFor && (
        <PriceModal
          course={priceFor}
          onClose={() => setPriceFor(null)}
          onSaved={() => {
            setPriceFor(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function CourseModal({
  initial,
  branches,
  isFounder,
  onClose,
  onSaved,
  onError,
}: {
  initial: Course | null;
  branches: Branch[];
  isFounder: boolean;
  onClose: () => void;
  onSaved: () => void;
  onError: (s: string) => void;
}) {
  const [f, setF] = useState({
    name: initial?.name ?? "",
    subject: initial?.subject ?? "",
    level: initial?.level ?? "",
    lesson_minutes: String(initial?.lesson_minutes ?? 90),
    lesson_price: initial ? String(Math.round(initial.lesson_price)) : "",
    lessons_per_month: String(initial?.lessons_per_month ?? 12),
    branch_id: initial?.branch_id ? String(initial.branch_id) : "",
    active: initial ? initial.active : true,
    note: initial?.note ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const set = (k: string, v: unknown) => setF((p) => ({ ...p, [k]: v }));

  const monthly =
    (Number(f.lesson_price) || 0) * (Number(f.lessons_per_month) || 0);

  async function save() {
    if (!f.name.trim()) return setErr("Kurs nomini yozing");
    if (!Number(f.lesson_price)) return setErr("Bitta dars narxini yozing");
    setSaving(true);
    setErr("");
    try {
      const body = {
        name: f.name.trim(),
        subject: f.subject || null,
        level: f.level || null,
        lesson_minutes: Number(f.lesson_minutes) || 90,
        lesson_price: Number(f.lesson_price),
        lessons_per_month: Number(f.lessons_per_month) || 12,
        active: f.active,
        note: f.note || null,
        ...(initial ? {} : { branch_id: f.branch_id ? Number(f.branch_id) : null }),
      };
      if (initial) await api.put(`/courses/${initial.id}`, body);
      else await api.post("/courses", body);
      onError("");
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const inp =
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm";
  const lbl = "block text-xs font-medium text-slate-500 mb-1";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="max-h-[88vh] w-full max-w-md overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">
            {initial ? "Kursni tahrirlash" : "Yangi kurs"}
          </h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className={lbl}>Kurs nomi</label>
            <input
              className={inp}
              value={f.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Masalan: General English — Beginner"
              autoFocus
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>Fan</label>
              <select
                className={inp}
                value={f.subject}
                onChange={(e) => set("subject", e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {SUBJECTS.map((sb) => (
                  <option key={sb.key} value={sb.key}>
                    {sb.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={lbl}>Daraja</label>
              <input
                className={inp}
                value={f.level}
                onChange={(e) => set("level", e.target.value)}
                placeholder="A1, B2…"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>Dars davomiyligi (daqiqa)</label>
              <input
                type="number"
                className={inp}
                value={f.lesson_minutes}
                onChange={(e) => set("lesson_minutes", e.target.value)}
              />
            </div>
            <div>
              <label className={lbl}>Oyiga nechta dars</label>
              <input
                type="number"
                className={inp}
                value={f.lessons_per_month}
                onChange={(e) => set("lessons_per_month", e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className={lbl}>Bitta dars narxi (so'm)</label>
            <input
              type="number"
              className={inp}
              value={f.lesson_price}
              onChange={(e) => set("lesson_price", e.target.value)}
              placeholder="50000"
            />
            {monthly > 0 && (
              <p className="mt-1 text-xs text-slate-500">
                Oylik narx: <b>{formatSom(monthly)}</b>
              </p>
            )}
          </div>
          {!initial && isFounder && branches.length > 1 && (
            <div>
              <label className={lbl}>Qaysi filial</label>
              <select
                className={inp}
                value={f.branch_id}
                onChange={(e) => set("branch_id", e.target.value)}
              >
                <option value="">— tanlang —</option>
                {branches.map((b) => (
                  <option key={b.id} value={String(b.id)}>
                    {b.name}
                    {b.is_partner ? " (hamkor)" : ""}
                  </option>
                ))}
              </select>
            </div>
          )}
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={f.active}
              onChange={(e) => set("active", e.target.checked)}
            />
            Faol (yangi guruhlarga taklif qilinadi)
          </label>
          <textarea
            className={inp}
            rows={2}
            value={f.note}
            onChange={(e) => set("note", e.target.value)}
            placeholder="Izoh (ixtiyoriy)"
          />
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button
            onClick={save}
            disabled={saving}
            className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda…" : "Saqlash"}
          </button>
          {initial && (
            <p className="text-xs text-slate-400 leading-snug">
              Narx o'zgartirilsa shu kursning barcha guruhlariga DARROV
              ko'chadi. Kelajakdagi sanadan boshlash uchun "Narxni
              sanadan boshlab o'zgartirish" tugmasidan foydalaning.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function PriceModal({
  course,
  onClose,
  onSaved,
}: {
  course: Course;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [from, setFrom] = useState("");
  const [price, setPrice] = useState(String(Math.round(course.lesson_price)));
  const [perMonth, setPerMonth] = useState(
    String(course.lessons_per_month ?? 12)
  );
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  async function save() {
    if (!from) return setErr("Qaysi sanadan boshlashini tanlang");
    if (!Number(price)) return setErr("Yangi narxni yozing");
    setSaving(true);
    setErr("");
    try {
      const r = await api.post<{ message: string }>(
        `/courses/${course.id}/price-change`,
        {
          from_date: from,
          lesson_price: Number(price),
          lessons_per_month: Number(perMonth) || null,
          note: note || null,
        }
      );
      setMsg(r.message);
      setTimeout(onSaved, 1200);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const inp = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm";
  const lbl = "block text-xs font-medium text-slate-500 mb-1";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-1 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Narxni o'zgartirish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          {course.name} · hozirgi narx {formatSom(course.lesson_price)}
        </p>
        <div className="space-y-3">
          <div>
            <label className={lbl}>Qaysi sanadan boshlab</label>
            <input
              type="date"
              className={inp}
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            />
            <p className="mt-1 text-xs text-slate-400 leading-snug">
              Shu kungacha eski narx ishlaydi. O'tgan oylarning hisobi
              o'zgarmaydi.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>Yangi dars narxi</label>
              <input
                type="number"
                className={inp}
                value={price}
                onChange={(e) => setPrice(e.target.value)}
              />
            </div>
            <div>
              <label className={lbl}>Oyiga dars soni</label>
              <input
                type="number"
                className={inp}
                value={perMonth}
                onChange={(e) => setPerMonth(e.target.value)}
              />
            </div>
          </div>
          <input
            className={inp}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Izoh: masalan «Sentabrdan narx oshdi»"
          />
          {err && <p className="text-sm text-red-600">{err}</p>}
          {msg && (
            <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              {msg}
            </p>
          )}
          <button
            onClick={save}
            disabled={saving}
            className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda…" : "Rejalashtirish"}
          </button>
        </div>
      </div>
    </div>
  );
}
