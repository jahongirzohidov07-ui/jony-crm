import { useEffect, useState } from "react";
import { Plus, Check, Info } from "lucide-react";
import {
  api, type StaffAttendanceReport, type NpsReport, type User,
  type Teacher,
} from "../lib/api";
import { formatDate } from "../lib/format";
import { StaffCard } from "./StaffCard";

// =============================================== Xodimlar davomati
export function AttendanceTab() {
  const [d, setD] = useState<StaffAttendanceReport | null>(null);
  const [staff, setStaff] = useState<User[]>([]);
  const [open, setOpen] = useState<number | null>(null);
  const [card, setCard] = useState<number | null>(null);
  const [form, setForm] = useState(false);

  function load() {
    api.get<StaffAttendanceReport>("/hr/attendance").then(setD);
  }
  useEffect(() => {
    load();
    api.get<User[]>("/users").then(setStaff).catch(() => setStaff([]));
  }, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="text-sm text-slate-500">
          Ish vaqti {d.work_start} — {d.work_end}
        </span>
        <span className="text-xs text-slate-400">
          {d.tolerance} daqiqagacha kechikish hisoblanmaydi
        </span>
        <div className="flex-1" />
        <button
          onClick={() => setForm(true)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={15} /> Kelib-ketish
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
        <Box label="Xodimlar" value={String(d.rows.length)} />
        <Box
          label="Kechikkanlar"
          value={String(d.staff_with_late)}
          tone={d.staff_with_late > 0 ? "bad" : "good"}
        />
        <Box
          label="Jami kechikish"
          value={`${d.total_late_minutes} daqiqa`}
          tone={d.total_late_minutes > 0 ? "bad" : "good"}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Xodim</th>
              <th className="text-left">Lavozim</th>
              <th className="text-right w-20">Kun</th>
              <th className="text-right w-28">Kechikkan kun</th>
              <th className="text-right w-28">Daqiqa</th>
              <th className="text-right w-28 pr-4">Ishlagan soat</th>
            </tr>
          </thead>
          <tbody>
            {d.rows.map((r) => (
              <>
                <tr key={r.user_id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() =>
                        setOpen(open === r.user_id ? null : r.user_id)
                      }
                      className="text-slate-800 hover:text-brand-700"
                    >
                      {r.full_name}
                    </button>
                  </td>
                  <td className="text-slate-500">{r.role_label}</td>
                  <td className="text-right text-slate-600">{r.days}</td>
                  <td
                    className={`text-right ${
                      r.late_days > 0 ? "text-amber-600" : "text-slate-400"
                    }`}
                  >
                    {r.late_days || "—"}
                  </td>
                  <td
                    className={`text-right ${
                      r.late_minutes > 0
                        ? "text-red-600 font-medium"
                        : "text-slate-400"
                    }`}
                  >
                    {r.late_minutes || "—"}
                  </td>
                  <td className="text-right pr-4 text-slate-600">
                    {r.worked_hours}
                  </td>
                </tr>
                {open === r.user_id && (
                  <tr key={`${r.user_id}-d`}>
                    <td colSpan={6} className="bg-slate-50 px-4 py-3">
                      {r.rows.length === 0 ? (
                        <p className="text-xs text-slate-400">
                          Bu oyda yozuv yo'q
                        </p>
                      ) : (
                        <div className="space-y-1">
                          {r.rows.map((x) => (
                            <div
                              key={x.id}
                              className="flex items-center gap-4 text-xs"
                            >
                              <span className="text-slate-500 w-24">
                                {x.date ? formatDate(x.date) : "—"}
                              </span>
                              <span className="text-slate-700 w-32">
                                {x.check_in || "—"} → {x.check_out || "—"}
                              </span>
                              {x.late_minutes > 0 && (
                                <span className="text-red-600">
                                  {x.late_minutes} daq kechikdi
                                </span>
                              )}
                              {x.early_minutes > 0 && (
                                <span className="text-amber-600">
                                  {x.early_minutes} daq erta ketdi
                                </span>
                              )}
                              <span className="text-slate-500">
                                {x.worked_hours} soat
                              </span>
                              <span className="text-slate-400 flex-1">
                                {x.note}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                      <button
                        onClick={() => setCard(r.user_id)}
                        className="text-xs text-brand-600 hover:underline mt-2"
                      >
                        Xodim kartasini ochish
                      </button>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {form && (
        <AttendanceForm
          staff={staff}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
        />
      )}
      {card !== null && (
        <StaffCard userId={card} canEdit onClose={() => setCard(null)} />
      )}
    </div>
  );
}

function AttendanceForm({
  staff,
  onClose,
  onSaved,
}: {
  staff: User[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [uid, setUid] = useState("");
  const [day, setDay] = useState(new Date().toISOString().slice(0, 10));
  const [inT, setInT] = useState("09:00");
  const [outT, setOutT] = useState("18:00");
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [res, setRes] = useState<string | null>(null);

  async function save() {
    if (!uid) {
      setErr("Xodimni tanlang");
      return;
    }
    try {
      const r = await api.post<{ late_minutes: number; worked_hours: number }>(
        "/hr/attendance",
        {
          user_id: Number(uid),
          date: day,
          check_in: inT || null,
          check_out: outT || null,
          note: note || null,
        }
      );
      setRes(
        r.late_minutes > 0
          ? `${r.late_minutes} daqiqa kechikish yozildi`
          : `Kechikishsiz · ${r.worked_hours} soat ishladi`
      );
      setTimeout(onSaved, 900);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-24">
      <div className="bg-white rounded-xl w-full max-w-sm p-5 shadow-xl">
        <h3 className="font-semibold text-slate-800 mb-1">Kelib-ketish</h3>
        <p className="text-xs text-slate-500 mb-4">
          Kechikish daqiqasi o'zi hisoblanadi
        </p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        {res && (
          <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2 mb-3">
            {res}
          </p>
        )}
        <div className="space-y-3">
          <select
            value={uid}
            onChange={(e) => setUid(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
          >
            <option value="">— xodimni tanlang —</option>
            {staff.map((s) => (
              <option key={s.id} value={s.id}>
                {s.full_name}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Keldi</label>
              <input
                type="time" lang="en-GB"
                value={inT}
                onChange={(e) => setInT(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Ketdi</label>
              <input
                type="time" lang="en-GB"
                value={outT}
                onChange={(e) => setOutT(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
          </div>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Izoh (ixtiyoriy)"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <div className="flex gap-2">
            <button
              onClick={save}
              className="flex-1 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
            >
              Saqlash
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg text-sm text-slate-500"
            >
              Bekor
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================ NPS
export function NpsTab() {
  const [d, setD] = useState<NpsReport | null>(null);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [form, setForm] = useState(false);
  const [open, setOpen] = useState<number | null>(null);

  function load() {
    api.get<NpsReport>("/nps?months=12").then(setD);
  }
  useEffect(() => {
    load();
    api.get<Teacher[]>("/teachers").then(setTeachers).catch(() => {});
  }, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <div className="flex-1" />
        <button
          onClick={() => setForm(true)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
        >
          <Plus size={15} /> Baho qo'shish
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
        <Box
          label="Umumiy NPS"
          value={String(d.overall_nps)}
          hint="−100 dan +100 gacha"
          tone={
            d.overall_nps >= 50 ? "good" : d.overall_nps >= 0 ? "plain" : "bad"
          }
        />
        <Box label="Javoblar" value={String(d.answers)} />
        <Box label="O'rtacha baho" value={`${d.avg} / 10`} />
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali baho berilmagan.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <div
              key={r.teacher_id}
              className="bg-white rounded-xl border border-slate-200 p-4"
            >
              <div className="flex items-center gap-3">
                <button
                  onClick={() =>
                    setOpen(open === r.teacher_id ? null : r.teacher_id)
                  }
                  className="text-sm font-medium text-slate-900 hover:text-brand-700"
                >
                  {r.full_name}
                </button>
                <span className="text-xs text-slate-400">
                  {r.answers} javob · o'rtacha {r.avg}
                </span>
                <div className="flex-1" />
                <span
                  className={`px-2.5 py-1 rounded-lg text-sm font-semibold ${
                    r.nps >= 50
                      ? "bg-emerald-100 text-emerald-800"
                      : r.nps >= 0
                        ? "bg-amber-100 text-amber-800"
                        : "bg-red-100 text-red-800"
                  }`}
                >
                  NPS {r.nps}
                </span>
              </div>

              <div className="flex gap-0.5 mt-2.5 h-2 rounded-full overflow-hidden">
                {[
                  { n: r.promoters, c: "bg-emerald-500" },
                  { n: r.passives, c: "bg-amber-400" },
                  { n: r.detractors, c: "bg-red-500" },
                ].map(
                  (x, i) =>
                    x.n > 0 && (
                      <div
                        key={i}
                        className={x.c}
                        style={{ width: `${(x.n / r.answers) * 100}%` }}
                      />
                    )
                )}
              </div>
              <div className="flex gap-4 mt-1.5 text-xs text-slate-500">
                <span className="text-emerald-600">
                  {r.promoters} tarafdor
                </span>
                <span className="text-amber-600">{r.passives} betaraf</span>
                <span className="text-red-600">{r.detractors} tanqidchi</span>
                <div className="flex-1" />
                <span>
                  O'quvchi {r.by_student} · Ota-ona {r.by_parent}
                </span>
              </div>

              {open === r.teacher_id && r.comments.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                  {r.comments.map((c, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <span
                        className={`px-1.5 py-0.5 rounded shrink-0 ${
                          c.band === "promoter"
                            ? "bg-emerald-100 text-emerald-700"
                            : c.band === "passive"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-red-100 text-red-700"
                        }`}
                      >
                        {c.score}
                      </span>
                      <span className="text-slate-400 w-16">{c.source}</span>
                      <span className="text-slate-600 flex-1">{c.comment}</span>
                      <span className="text-slate-400">
                        {c.date ? formatDate(c.date) : ""}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>

      {form && (
        <NpsForm
          teachers={teachers}
          sources={d.sources}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function NpsForm({
  teachers,
  sources,
  onClose,
  onSaved,
}: {
  teachers: Teacher[];
  sources: { key: string; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [tid, setTid] = useState("");
  const [score, setScore] = useState<number | null>(null);
  const [source, setSource] = useState("student");
  const [comment, setComment] = useState("");
  const [err, setErr] = useState("");

  async function save() {
    if (!tid || score === null) {
      setErr("Ustoz va bahoni tanlang");
      return;
    }
    try {
      await api.post("/nps", {
        teacher_id: Number(tid),
        score,
        source,
        comment: comment || null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-24">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <h3 className="font-semibold text-slate-800 mb-1">Ustozga baho</h3>
        <p className="text-xs text-slate-500 mb-4">
          "Bu ustozni do'stingizga tavsiya qilasizmi?" — 0 dan 10 gacha
        </p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <select
            value={tid}
            onChange={(e) => setTid(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
          >
            <option value="">— ustozni tanlang —</option>
            {teachers.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
          </select>

          <div className="flex gap-1.5">
            {sources.map((s) => (
              <button
                key={s.key}
                onClick={() => setSource(s.key)}
                className={`flex-1 px-2 py-2 rounded-lg text-xs font-medium border transition ${
                  source === s.key
                    ? "bg-brand-50 border-brand-400 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-1.5">Baho</label>
            <div className="flex gap-1">
              {Array.from({ length: 11 }, (_, i) => i).map((n) => (
                <button
                  key={n}
                  onClick={() => setScore(n)}
                  className={`flex-1 h-9 rounded-lg text-sm font-medium border transition ${
                    score === n
                      ? n >= 9
                        ? "bg-emerald-500 border-emerald-500 text-white"
                        : n >= 7
                          ? "bg-amber-500 border-amber-500 text-white"
                          : "bg-red-500 border-red-500 text-white"
                      : "bg-white border-slate-200 text-slate-600 hover:border-slate-400"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>Tavsiya qilmayman</span>
              <span>Albatta tavsiya qilaman</span>
            </div>
          </div>

          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={2}
            placeholder="Izoh (ixtiyoriy)"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />

          <div className="flex gap-2">
            <button
              onClick={save}
              className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
            >
              <Check size={15} /> Saqlash
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg text-sm text-slate-500"
            >
              Bekor
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Box({
  label,
  value,
  hint,
  tone = "plain",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "plain" | "good" | "bad";
}) {
  const cls = {
    plain: "bg-white border-slate-200 text-slate-900",
    good: "bg-emerald-50 border-emerald-200 text-emerald-800",
    bad: "bg-red-50 border-red-200 text-red-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}
