import { useCallback, useEffect, useState } from "react";
import { Timer, Info, Trash2, Wallet, GraduationCap, Check, Users, X as XIcon } from "lucide-react";
import { api } from "../lib/api";
import { Time24Input } from "../components/Time24Input";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * Support teacher seanslari va avtomat oylik.
 *
 * Har dars o'sha kuni kiritiladi: guruh, boshlanish-tugash vaqti,
 * o'quvchilar soni. Oylik asoschi formulasi bilan o'zi chiqadi:
 *   (soat x 0.30 + o'quvchi x 0.20 + test koef x 0.50) x 10 000
 * kamida 400 000, ko'pi bilan 1 500 000.
 */
const BUSY_DAYS = [
  ["mon", "Du"], ["tue", "Se"], ["wed", "Chor"], ["thu", "Pay"],
  ["fri", "Ju"], ["sat", "Shan"], ["sun", "Yak"],
] as const;

/** Support o'zi belgilaydigan BAND VAQTLAR: "bu soatlarga menga dars
 *  qo'yilmasin" (o'z darsi, repetitorlik...). Support manager guruh
 *  biriktirayotganda shu vaqtlar to'qnashsa ogohlantirish oladi. */
function BusyTimes() {
  type Row = { id: number; days: string; start: string; end: string;
               note?: string | null };
  const [rows, setRows] = useState<Row[]>([]);
  const [days, setDays] = useState<string[]>([]);
  const [start, setStart] = useState("14:00");
  const [end, setEnd] = useState("16:00");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState("");
  const load = () =>
    api.get<Row[]>("/me/support-busy").then(setRows).catch(() => {});
  useEffect(() => {
    load();
  }, []);
  const dayUz = (d: string) =>
    d.split(",").map((k) => BUSY_DAYS.find((x) => x[0] === k)?.[1] || k)
      .join(", ");
  async function add() {
    if (!days.length) {
      setMsg("Kamida bitta kun tanlang");
      return;
    }
    setMsg("");
    try {
      await api.post("/me/support-busy", {
        days: days.join(","), start, end, note: note || null,
      });
      setDays([]); setNote("");
      load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    }
  }
  async function del(id: number) {
    await api.delete(`/me/support-busy/${id}`);
    load();
  }
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
      <p className="text-sm font-medium text-slate-700 mb-1">
        Band vaqtlarim
      </p>
      <p className="text-xs text-slate-500 mb-3">
        Bu vaqtlarga sizga guruh biriktirilmasin desangiz — belgilab
        qo'ying. Support manager guruh qo'yayotganda ogohlantirish oladi.
      </p>
      {rows.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {rows.map((r) => (
            <span
              key={r.id}
              className="inline-flex items-center gap-1.5 rounded-lg bg-red-50 border border-red-200 text-red-700 px-2.5 py-1.5 text-xs"
            >
              <span className="font-semibold">{r.start}-{r.end}</span>
              {dayUz(r.days)}
              {r.note ? ` · ${r.note}` : ""}
              <button
                onClick={() => del(r.id)}
                className="ml-1 text-red-400 hover:text-red-700"
                title="O'chirish"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex gap-1">
          {BUSY_DAYS.map(([k, l]) => (
            <button
              key={k}
              onClick={() =>
                setDays((d) =>
                  d.includes(k) ? d.filter((x) => x !== k) : [...d, k]
                )
              }
              className={`px-2 py-1.5 rounded-lg text-xs border ${
                days.includes(k)
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white border-slate-200 text-slate-600"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        <Time24Input value={start}
          onChange={(e) => setStart(e.target.value)}
          className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
        <span className="text-slate-400 text-xs">—</span>
        <Time24Input value={end}
          onChange={(e) => setEnd(e.target.value)}
          className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
        <input value={note} onChange={(e) => setNote(e.target.value)}
          placeholder="Izoh (repetitorlik...)"
          className="flex-1 min-w-[140px] rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
        <button onClick={add}
          className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs">
          Qo'shish
        </button>
      </div>
      {msg && <p className="text-xs text-red-600 mt-2">{msg}</p>}
    </div>
  );
}

export default function MySessions() {
  const [d, setD] = useState<Any>(null);
  const [jp, setJp] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [f, setF] = useState({
    group_id: "",
    start_time: "",
    end_time: "",
    students_count: "",
  });
  const [busy, setBusy] = useState(false);

  const load = () => {
    api
      .get<Any>("/me/support-sessions")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(() => {
    load();
    api.get<Any>("/me/junior-path").then(setJp).catch(() => {});
  }, []);

  const add = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post("/me/support-sessions", {
        group_id: Number(f.group_id),
        start_time: f.start_time,
        end_time: f.end_time,
        students_count: Number(f.students_count),
      });
      setF({ group_id: "", start_time: "", end_time: "", students_count: "" });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const del = async (id: number) => {
    setErr("");
    try {
      await api.delete(`/me/support-sessions/${id}`);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  if (err && !d)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Timer size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          {d.volunteer ? "Darslarim" : "Darslarim va oyligim"}
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">{d.period}</p>

      <BusyTimes />

      {/* ---- Oylik kartasi ---- */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Wallet size={15} className="text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            {d.volunteer ? "Shu oygi ishim" : "Shu oygi oylik — avtomat"}
          </p>
        </div>
        {/* Volontyorga oylik hisoblanmaydi (2026-09-23, Jahongir) */}
        {d.volunteer ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 mb-1">
            <p className="text-sm font-medium text-amber-900">
              Volontyor bosqichi — oylik hisoblanmaydi
            </p>
            {d.volunteer_hint && (
              <p className="text-xs text-amber-800 mt-1">
                {d.volunteer_hint}
              </p>
            )}
          </div>
        ) : (
        <p className="text-3xl font-semibold text-slate-900 mb-1">
          {Number(d.salary).toLocaleString().replace(/,/g, " ")}{" "}
          <span className="text-base font-normal text-slate-400">so'm</span>
        </p>
        )}
        {!d.volunteer && d.clamped_min && (
          <p className="text-xs text-amber-600 mb-2">
            Hisob {Number(d.raw).toLocaleString().replace(/,/g, " ")} chiqdi —
            eng kam oylik {Number(d.min).toLocaleString().replace(/,/g, " ")}{" "}
            to'lanadi.
          </p>
        )}
        {!d.volunteer && d.clamped_max && (
          <p className="text-xs text-amber-600 mb-2">
            Hisob yuqori chegaradan oshdi — {" "}
            {Number(d.max).toLocaleString().replace(/,/g, " ")} to'lanadi.
          </p>
        )}

        <div className="grid grid-cols-3 gap-3 mt-3">
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">Soatlar</p>
            <p className="text-lg font-semibold text-slate-900">{d.hours}</p>
            {!d.volunteer && (
              <p className="text-xs text-slate-400">
                x 0.30 = {d.hours_part}
              </p>
            )}
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">O'quvchilar</p>
            <p className="text-lg font-semibold text-slate-900">
              {d.students}
            </p>
            {!d.volunteer && (
              <p className="text-xs text-slate-400">
                {d.solo_count
                  ? `${d.students_points} x 0.20 = ${d.students_part}`
                  : `x 0.20 = ${d.students_part}`}
              </p>
            )}
            {!d.volunteer && d.solo_count ? (
              <p className="text-[11px] text-slate-400">
                yakka dars {d.solo_as_students} o'quvchidek
              </p>
            ) : null}
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">Test natijasi</p>
            <p className="text-lg font-semibold text-slate-900">
              {d.avg_percent != null ? `${d.avg_percent}%` : "—"}
            </p>
            {!d.volunteer && (
              <p className="text-xs text-slate-400">
                koef {d.coef} x 0.50 = {d.result_part}
              </p>
            )}
          </div>
        </div>
        {!d.volunteer && (
          <p className="text-xs text-slate-400 mt-2">
            {d.formula} = {Number(d.raw).toLocaleString().replace(/,/g, " ")}
          </p>
        )}
        {/* HR ayirgan jarima ballari (2026-09-16) */}
        {d.adjustments?.length > 0 && (
          <div className="mt-3 border-t border-slate-100 pt-2">
            <p className="text-xs font-medium text-slate-600 mb-1">
              Jarima ballari: −{d.adjustment_points}
            </p>
            {d.adjustments.map((a: Any) => (
              <p key={a.id} className="text-xs text-slate-500">
                <span className="text-red-600 font-medium">−{a.points}</span>
                {" "}— {a.reason}
                <span className="text-slate-400"> · {a.date}</span>
              </p>
            ))}
          </div>
        )}
      </div>

      <SoloStudents />

      {/* ---- Junior teacher yo'li ---- */}
      {jp && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
          <div className="flex items-center gap-2 mb-1">
            <GraduationCap size={15} className="text-slate-400" />
            <p className="text-sm font-medium text-slate-700">
              Junior teacher bo'lish yo'li
            </p>
            <span className="text-xs text-slate-400 ml-auto">
              {jp.done_count}/{jp.total} bajarildi
            </span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full mb-3">
            <div className="h-1.5 bg-brand-600 rounded-full"
                 style={{ width: `${(jp.done_count / jp.total) * 100}%` }} />
          </div>
          {jp.items.map((it: Any) => (
            <div key={it.key}
                 className="flex items-center gap-2 py-1.5 text-sm">
              {it.done ? (
                <Check size={15} className="text-emerald-600 shrink-0" />
              ) : (
                <XIcon size={15} className="text-slate-300 shrink-0" />
              )}
              <span className={it.done ? "text-slate-700"
                : "text-slate-500"}>{it.label}</span>
              <span className="ml-auto text-xs text-slate-400">
                {it.value ?? "—"} / {it.target}
              </span>
            </div>
          ))}
          <p className="text-xs text-slate-400 mt-2">{jp.hint}</p>
        </div>
      )}

      {/* ---- Yangi seans ---- */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
        <p className="text-sm font-medium text-slate-700 mb-2">
          Bugungi darsni kiritish
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
          <select
            value={f.group_id}
            onChange={(e) => setF({ ...f, group_id: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm"
          >
            <option value="">Guruh *</option>
            {d.all_groups.map((g: Any) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
          <Time24Input
            value={f.start_time}
            onChange={(e) => setF({ ...f, start_time: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm"
          />
          <Time24Input
            value={f.end_time}
            onChange={(e) => setF({ ...f, end_time: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm"
          />
          <input
            type="number"
            min={1}
            max={d.max_students}
            value={f.students_count}
            onChange={(e) => setF({ ...f, students_count: e.target.value })}
            placeholder="O'quvchi soni *"
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={add}
          disabled={
            busy ||
            !f.group_id ||
            !f.start_time ||
            !f.end_time ||
            !f.students_count
          }
          className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          Kiritish
        </button>
      </div>

      {/* ---- Seanslar ---- */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Sana</th>
              <th className="text-left px-3 py-2.5 font-medium">Guruh</th>
              <th className="text-left px-3 py-2.5 font-medium">Vaqt</th>
              <th className="text-right px-3 py-2.5 font-medium">Soat</th>
              <th className="text-right px-3 py-2.5 font-medium">O'quvchi</th>
              <th className="px-3 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.sessions.map((s: Any) => (
              <tr key={s.id}>
                <td className="px-4 py-2.5 text-slate-700">{s.date}</td>
                <td className="px-3 py-2.5 text-slate-700">{s.group}</td>
                <td className="px-3 py-2.5 text-slate-500">
                  {s.start_time} — {s.end_time}
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {s.hours}
                </td>
                <td className="px-3 py-2.5 text-right text-slate-700">
                  {s.students_count}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <button
                    onClick={() => del(s.id)}
                    className="text-slate-300 hover:text-red-600"
                    title="O'chirish (faqat bugungisini)"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.sessions.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Bu oyda hali seans kiritilmagan.
          </p>
        )}
      </div>

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}

/** YAKKA O'QUVCHILAR (2026-09-23). Ustoz orqada qolgan o'quvchini
 *  supportga biriktiradi. Bu yerda bitta tugma bilan dars yoziladi:
 *  yo'qlama ham, seans ham birga tushadi — shunda pul hisobi va
 *  yo'qlama bir-biridan ajralib qolmaydi. */
type SoloStudent = {
  student_id: number;
  name: string;
  group: string | null;
  days: string | null;
  start: string | null;
  end: string | null;
  note: string | null;
  done: number;
  missed: number;
  today_done: boolean;
};

const DAY_UZ: Record<string, string> = {
  mon: "Du", tue: "Se", wed: "Ch", thu: "Pa", fri: "Ju", sat: "Sh",
  sun: "Ya",
};

function SoloStudents() {
  const [d, setD] = useState<{ rows: SoloStudent[]; hint: string } | null>(
    null
  );
  const [busy, setBusy] = useState(0);

  const load = useCallback(() => {
    api
      .fresh<{ rows: SoloStudent[]; hint: string }>("/me/support-solo")
      .then(setD)
      .catch(() => setD({ rows: [], hint: "" }));
  }, []);
  useEffect(load, [load]);

  if (!d || d.rows.length === 0) return null;

  const mark = async (sid: number, present: boolean) => {
    setBusy(sid);
    try {
      await api.post(`/me/support-solo/${sid}/lesson`, { present });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Yozilmadi");
    } finally {
      setBusy(0);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
      <div className="flex items-center gap-2 mb-1">
        <Users size={15} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">
          Yakka o'quvchilar
        </p>
      </div>
      <p className="text-xs text-slate-500 mb-3">{d.hint}</p>

      {d.rows.map((r) => (
        <div key={r.student_id}
             className="border-t border-slate-100 py-3 first:border-t-0">
          <div className="flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900">{r.name}</p>
              <p className="text-xs text-slate-500">
                {r.group}
                {r.days
                  ? " · " +
                    r.days
                      .split(",")
                      .filter(Boolean)
                      .map((x) => DAY_UZ[x] || x)
                      .join(", ")
                  : ""}
                {r.start && r.end ? ` ${r.start}-${r.end}` : ""}
              </p>
              {r.note && (
                <p className="text-xs text-slate-600 mt-1">{r.note}</p>
              )}
              <p className="text-xs text-slate-400 mt-1">
                Shu oy: {r.done} ta dars
                {r.missed ? ` · ${r.missed} marta kelmadi` : ""}
              </p>
            </div>
            {r.today_done ? (
              <span className="text-xs text-emerald-600 whitespace-nowrap">
                Bugun yozilgan
              </span>
            ) : (
              <div className="flex gap-1.5 shrink-0">
                <button
                  disabled={busy === r.student_id}
                  onClick={() => mark(r.student_id, true)}
                  className="rounded-lg bg-brand-600 text-white text-xs px-3 py-1.5 disabled:opacity-50"
                >
                  Dars o'tdim
                </button>
                <button
                  disabled={busy === r.student_id}
                  onClick={() => mark(r.student_id, false)}
                  className="rounded-lg border border-slate-300 text-slate-600 text-xs px-3 py-1.5 disabled:opacity-50"
                >
                  Kelmadi
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
