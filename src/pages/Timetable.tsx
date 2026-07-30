import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarDays, AlertTriangle, Download, Clock, DoorOpen, Users,
} from "lucide-react";
import { api, type Timetable as Data, type TimetableItem } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, can } from "../lib/roles";
import { BranchPicker, branchParam } from "../components/BranchPicker";
import { exportToExcel } from "../lib/exportXlsx";

/** Fan bo'yicha rang - jadvalda ko'z bilan ajratish uchun. */
const SUBJECT_TONE: Record<string, string> = {
  english: "border-l-sky-400 bg-sky-50",
  russian: "border-l-violet-400 bg-violet-50",
  korean: "border-l-emerald-400 bg-emerald-50",
  turkish: "border-l-amber-400 bg-amber-50",
  german: "border-l-rose-400 bg-rose-50",
};

function tone(subject?: string | null): string {
  return SUBJECT_TONE[subject || ""] || "border-l-slate-300 bg-slate-50";
}

function Card({ it }: { it: TimetableItem }) {
  const full =
    it.capacity && it.students >= it.capacity
      ? "text-red-600"
      : it.capacity && it.students / it.capacity < 0.5
        ? "text-amber-600"
        : "text-slate-500";
  return (
    <Link
      to={`/groups/${it.group_id}`}
      className={`block rounded-lg border border-slate-200 border-l-4 p-3 hover:border-brand-300 transition ${tone(
        it.subject
      )}`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-slate-900 leading-tight">
          {it.group}
        </p>
        {it.time_label && (
          <span className="text-xs font-medium text-slate-700 whitespace-nowrap">
            {it.time_label}
          </span>
        )}
      </div>
      <p className="text-xs text-slate-600 mt-1">
        {[it.subject_label, it.level_label].filter(Boolean).join(" · ")}
      </p>
      <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
        {it.teacher && <span>{it.teacher}</span>}
        {it.room && (
          <span className="flex items-center gap-1">
            <DoorOpen size={11} />
            {it.room}
          </span>
        )}
        <span className={`flex items-center gap-1 ${full}`}>
          <Users size={11} />
          {it.students}
          {it.capacity ? `/${it.capacity}` : ""}
        </span>
      </div>
    </Link>
  );
}

export default function Timetable() {
  const { user } = useAuth();
  const [data, setData] = useState<Data | null>(null);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [view, setView] = useState<"week" | "list">("week");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<Data>(`/timetable?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [branchId]);

  if (!can(user?.role, TEACHING_STAFF)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <CalendarDays size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Dars jadvali</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Qaysi kun, qaysi vaqt, qaysi guruh va qaysi xonada
      </p>

      <div className="flex flex-wrap items-center gap-2 mb-5">
        <div className="flex gap-1">
          {[
            { k: "week", l: "Hafta bo'yicha" },
            { k: "list", l: "Ro'yxat" },
          ].map((v) => (
            <button
              key={v.k}
              onClick={() => setView(v.k as "week" | "list")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                view === v.k
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {v.l}
            </button>
          ))}
        </div>
        <BranchPicker value={branchId} onChange={setBranchId} />
        <span className="text-sm text-slate-500">
          {data.items.length} ta guruh
        </span>
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("dars-jadvali", "Jadval",
              data.items.map((i) => ({
                Guruh: i.group,
                Fan: i.subject_label,
                Daraja: i.level_label,
                "O'qituvchi": i.teacher ?? "",
                Xona: i.room ?? "",
                Kunlar: i.days
                  .map((d) => data.days.find((x) => x.key === d)?.label || d)
                  .join(", "),
                Vaqt: i.time_label,
                "O'quvchi": i.students,
                "Sig'im": i.capacity ?? "",
              })))
          }
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <Download size={14} /> Excel
        </button>
      </div>

      {data.clashes.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={15} className="text-red-600" />
            <p className="text-sm font-medium text-red-900">
              {data.clashes.length} ta xona to'qnashuvi
            </p>
          </div>
          <div className="space-y-0.5">
            {data.clashes.map((c, i) => (
              <p key={i} className="text-xs text-red-800">
                {data.days.find((d) => d.key === c.day)?.label} · {c.time} ·{" "}
                {c.room}: {c.groups.join(" va ")}
              </p>
            ))}
          </div>
        </div>
      )}

      {view === "week" ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {data.days.map((d) => {
            const items = data.by_day[d.key] || [];
            return (
              <div
                key={d.key}
                className="bg-white rounded-xl border border-slate-200 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <p className="text-sm font-medium text-slate-800">{d.label}</p>
                  <span className="text-xs text-slate-400">
                    {items.length} ta dars
                  </span>
                </div>
                {items.length === 0 ? (
                  <p className="text-sm text-slate-300 py-3 text-center">
                    Dars yo'q
                  </p>
                ) : (
                  <div className="space-y-2">
                    {items.map((it) => (
                      <Card key={`${d.key}-${it.group_id}`} it={it} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Guruh</th>
                <th className="text-left">Fan / daraja</th>
                <th className="text-left">O'qituvchi</th>
                <th className="text-left">Xona</th>
                <th className="text-left">Kunlar</th>
                <th className="text-left w-32">Vaqt</th>
                <th className="text-right w-24 pr-4">O'quvchi</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((i) => (
                <tr key={i.group_id} className="border-t border-slate-100">
                  <td className="px-4 py-2.5">
                    <Link
                      to={`/groups/${i.group_id}`}
                      className="text-slate-800 hover:text-brand-700"
                    >
                      {i.group}
                    </Link>
                  </td>
                  <td className="text-slate-600">
                    {[i.subject_label, i.level_label].filter(Boolean).join(" · ")}
                  </td>
                  <td className="text-slate-500">{i.teacher || "—"}</td>
                  <td className="text-slate-500">{i.room || "—"}</td>
                  <td className="text-slate-500 text-xs">
                    {i.days
                      .map((d) => data.days.find((x) => x.key === d)?.short || d)
                      .join(", ")}
                  </td>
                  <td className="text-slate-700">
                    {i.time_label ? (
                      <span className="flex items-center gap-1">
                        <Clock size={12} className="text-slate-400" />
                        {i.time_label}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="text-right pr-4 text-slate-600">
                    {i.students}
                    {i.capacity ? (
                      <span className="text-slate-400">/{i.capacity}</span>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data.no_schedule.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-4">
          <p className="text-sm text-amber-900 font-medium mb-1">
            {data.no_schedule.length} ta guruhda dars kunlari belgilanmagan
          </p>
          <p className="text-xs text-amber-800">
            {data.no_schedule.map((g) => g.name).join(", ")} — guruhni
            tahrirlab dars kunlari va vaqtini tanlang.
          </p>
        </div>
      )}
    </div>
  );
}
