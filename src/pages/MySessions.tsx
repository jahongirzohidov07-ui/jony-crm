import { useEffect, useState } from "react";
import { Timer, Info, Trash2, Wallet, GraduationCap, Check, X as XIcon } from "lucide-react";
import { api } from "../lib/api";

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
          Darslarim va oyligim
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">{d.period}</p>

      {/* ---- Oylik kartasi ---- */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Wallet size={15} className="text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            Shu oygi oylik — avtomat
          </p>
        </div>
        <p className="text-3xl font-semibold text-slate-900 mb-1">
          {Number(d.salary).toLocaleString().replace(/,/g, " ")}{" "}
          <span className="text-base font-normal text-slate-400">so'm</span>
        </p>
        {d.clamped_min && (
          <p className="text-xs text-amber-600 mb-2">
            Hisob {Number(d.raw).toLocaleString().replace(/,/g, " ")} chiqdi —
            eng kam oylik {Number(d.min).toLocaleString().replace(/,/g, " ")}{" "}
            to'lanadi.
          </p>
        )}
        {d.clamped_max && (
          <p className="text-xs text-amber-600 mb-2">
            Hisob yuqori chegaradan oshdi — {" "}
            {Number(d.max).toLocaleString().replace(/,/g, " ")} to'lanadi.
          </p>
        )}

        <div className="grid grid-cols-3 gap-3 mt-3">
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">Soatlar</p>
            <p className="text-lg font-semibold text-slate-900">{d.hours}</p>
            <p className="text-xs text-slate-400">x 0.30 = {d.hours_part}</p>
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">O'quvchilar</p>
            <p className="text-lg font-semibold text-slate-900">
              {d.students}
            </p>
            <p className="text-xs text-slate-400">
              x 0.20 = {d.students_part}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">Test natijasi</p>
            <p className="text-lg font-semibold text-slate-900">
              {d.avg_percent != null ? `${d.avg_percent}%` : "—"}
            </p>
            <p className="text-xs text-slate-400">
              koef {d.coef} x 0.50 = {d.result_part}
            </p>
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          {d.formula} = {Number(d.raw).toLocaleString().replace(/,/g, " ")}
        </p>
      </div>

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
          <input
            type="time"
            value={f.start_time}
            onChange={(e) => setF({ ...f, start_time: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-2 text-sm"
          />
          <input
            type="time"
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
