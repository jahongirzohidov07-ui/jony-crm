import { useEffect, useState } from "react";
import {
  Info, UserPlus, Snowflake, ArrowLeftRight, Repeat, ClipboardCheck,
  Pencil, BadgePercent,
} from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/* ==================== 1. UYGA VAZIFALAR ==================== */
/** Yoqlama qilingan darslarga uy vazifasi belgilash matritsasi.
 *  Bosganda aylanadi: bo'sh → 2 (bajardi) → 1 (qisman) → 0 (qilmadi)
 *  → bo'sh. Yoqlamasiz katakka qo'yilmaydi. */
export function GroupHomeworkTab({ groupId }: { groupId: number }) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  const load = () => {
    api.get<Any>(`/groups/${groupId}/attendance?year=${year}&month=${month}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, [groupId, year, month]);

  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const todayIso = new Date().toISOString().slice(0, 10);
  const lessons = d.lessons.filter((ls: Any) => ls.date <= todayIso);

  const cycle = async (lessonId: number, studentId: number) => {
    const key = `${lessonId}:${studentId}`;
    if (!(key in d.marks)) {
      alert("Avval yoqlama belgilang — yoqlamasiz darsga vazifa qo'yilmaydi");
      return;
    }
    const cur = d.homework?.[key];
    const next = cur === undefined || cur === null ? 2
      : cur === 2 ? 1 : cur === 1 ? 0 : null;
    // optimistik
    const hw = { ...(d.homework || {}) };
    if (next === null) delete hw[key]; else hw[key] = next;
    setD({ ...d, homework: hw });
    try {
      await api.put(`/lessons/${lessonId}/homework`,
        { student_id: studentId, homework: next });
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
      load();
    }
  };

  const HW_UI: Record<string, { t: string; cls: string }> = {
    "2": { t: "✓", cls: "bg-emerald-100 text-emerald-700" },
    "1": { t: "±", cls: "bg-amber-100 text-amber-700" },
    "0": { t: "✗", cls: "bg-red-100 text-red-600" },
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <select value={month} onChange={(e) => setMonth(+e.target.value)}
          className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
          {["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul",
            "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
            .map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
        </select>
        <select value={year} onChange={(e) => setYear(+e.target.value)}
          className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
          {[year - 1, year, year + 1].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>
      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="text-sm whitespace-nowrap">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-left px-4 py-2 font-medium sticky left-0 bg-slate-50">
                O'quvchi
              </th>
              {lessons.map((ls: Any) => (
                <th key={ls.id} className="px-1.5 py-2 font-medium">
                  {ls.date.slice(8)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.students.map((st: Any) => (
              <tr key={st.id}>
                <td className="px-4 py-1.5 text-slate-800 sticky left-0 bg-white">
                  {st.full_name}
                </td>
                {lessons.map((ls: Any) => {
                  const key = `${ls.id}:${st.id}`;
                  const attended = key in d.marks;
                  const hw = d.homework?.[key];
                  const ui = hw !== undefined && hw !== null
                    ? HW_UI[String(hw)] : null;
                  return (
                    <td key={ls.id} className="px-1 py-1 text-center">
                      <button
                        onClick={() => cycle(ls.id, st.id)}
                        disabled={!attended}
                        title={!attended ? "Yoqlama yo'q"
                          : hw === 2 ? "Bajardi" : hw === 1 ? "Qisman"
                          : hw === 0 ? "Qilmadi" : "Belgilash"}
                        className={`w-7 h-7 rounded-md text-xs font-semibold ${
                          !attended
                            ? "bg-slate-50 text-slate-200 cursor-not-allowed"
                            : ui ? ui.cls
                            : "bg-slate-100 text-slate-300 hover:bg-slate-200"}`}
                      >
                        {ui ? ui.t : "·"}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        Bosganda aylanadi: ✓ bajardi → ± qisman → ✗ qilmadi → bo'sh.
        Vazifa faqat yoqlama qilingan darsga qo'yiladi; o'tgan darslarga
        ham qo'yish mumkin — vazifa keyingi darsda tekshiriladi.
      </p>
    </div>
  );
}

/* ==================== 2. TARIX ==================== */
const EV_ICON: Record<string, Any> = {
  user: <UserPlus size={14} className="text-emerald-600" />,
  snow: <Snowflake size={14} className="text-sky-600" />,
  move: <ArrowLeftRight size={14} className="text-amber-600" />,
  swap: <Repeat size={14} className="text-violet-600" />,
  exam: <ClipboardCheck size={14} className="text-brand-600" />,
  edit: <Pencil size={14} className="text-slate-400" />,
};

export function GroupHistoryTab({ groupId }: { groupId: number }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Any>(`/groups/${groupId}/history`).then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [groupId]);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      {d.events.map((e: Any, i: number) => (
        <div key={i}
             className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
          <span className="mt-0.5 shrink-0">
            {EV_ICON[e.icon] || EV_ICON.edit}
          </span>
          <div className="min-w-0">
            <p className="text-sm text-slate-700">{e.text}</p>
            <p className="text-xs text-slate-400">
              {e.date}
              {/* kim qilgani (2026-09-17) */}
              <span className="ml-2 text-slate-500">
                · {e.by ? <>Kim: <b className="font-medium">{e.by}</b></> : "kim qilgani yozilmagan"}
              </span>
            </p>
          </div>
        </div>
      ))}
      {d.events.length === 0 && (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hozircha tarix yo'q.
        </p>
      )}
    </div>
  );
}

/* ==================== 3. IZOH: CHEGIRMA ==================== */
export function GroupNotesTab({ groupId }: { groupId: number }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Any>(`/groups/${groupId}/notes`).then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [groupId]);
  if (err) return <p className="text-sm text-slate-500 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th className="text-left px-4 py-2.5 font-medium">O'quvchi</th>
            <th className="text-left px-3 py-2.5 font-medium">
              Manzil / maktab</th>
            <th className="text-left px-3 py-2.5 font-medium">Izoh</th>
            <th className="text-left px-4 py-2.5 font-medium">
              Chegirmalar</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {d.students.map((s: Any) => (
            <tr key={s.id}>
              <td className="px-4 py-2.5 text-slate-800">{s.name}</td>
              <td className="px-3 py-2.5 text-slate-500 text-xs">
                {[s.address, s.school, s.school_grade]
                  .filter(Boolean).join(" · ") || "—"}
              </td>
              <td className="px-3 py-2.5 text-slate-600 text-xs max-w-xs">
                {s.note || "—"}
              </td>
              <td className="px-4 py-2.5">
                {s.discounts.length === 0 ? (
                  <span className="text-xs text-slate-400">yo'q</span>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {s.discounts.map((dc: Any, i: number) => (
                      <span key={i} title={dc.reason}
                        className="inline-flex items-center gap-1 text-[11px] bg-emerald-50 text-emerald-700 rounded-full px-2 py-0.5">
                        <BadgePercent size={11} />
                        {dc.percent ? `${dc.percent}%`
                          : `${Number(dc.amount).toLocaleString()
                              .replace(/,/g, " ")} so'm`}
                        {dc.until ? ` · ${dc.until}gacha` : ""}
                      </span>
                    ))}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {d.students.length === 0 && (
        <p className="text-sm text-slate-400 py-6 text-center">
          O'quvchi yo'q.
        </p>
      )}
    </div>
  );
}
