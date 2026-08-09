import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarDays, Download, AlertTriangle, Users, DoorOpen, Rows3,
} from "lucide-react";
import { api, type TimetableGrid as Grid, type GridItem } from "../lib/api";
import { BranchPicker, branchParam } from "../components/BranchPicker";
import { exportToExcel } from "../lib/exportXlsx";

const SLOT_W = 62;      // bitta 30 daqiqalik ustun eni
const ROW_H = 96;

const HUE: Record<string, { bg: string; border: string; head: string }> = {
  teal: { bg: "bg-teal-50", border: "border-teal-300", head: "bg-teal-100" },
  violet: { bg: "bg-violet-50", border: "border-violet-300", head: "bg-violet-100" },
  emerald: { bg: "bg-emerald-50", border: "border-emerald-300", head: "bg-emerald-100" },
  amber: { bg: "bg-amber-50", border: "border-amber-300", head: "bg-amber-100" },
  rose: { bg: "bg-rose-50", border: "border-rose-300", head: "bg-rose-100" },
  slate: { bg: "bg-slate-50", border: "border-slate-300", head: "bg-slate-100" },
};

function Block({ it }: { it: GridItem }) {
  const h = HUE[it.hue] || HUE.slate;
  const warn =
    it.warn === "full"
      ? "ring-2 ring-red-300"
      : it.warn === "empty"
        ? "ring-2 ring-amber-300"
        : "";
  return (
    <Link
      to={`/groups/${it.group_id}`}
      className={`absolute top-1 bottom-1 rounded-lg border overflow-hidden ${h.bg} ${h.border} ${warn} hover:shadow-md transition`}
      style={{
        left: it.col * SLOT_W + 3,
        width: it.span * SLOT_W - 6,
      }}
    >
      <div className={`px-2 py-1 ${h.head}`}>
        <p className="text-xs font-semibold text-slate-900 truncate">
          {it.group}
        </p>
      </div>
      <div className="px-2 py-1 space-y-0.5">
        <p className="text-[11px] text-slate-600 truncate">
          {[it.subject_label, it.level_label].filter(Boolean).join(" · ")}
        </p>
        {it.teacher && (
          <p className="text-[11px] text-slate-500 truncate">{it.teacher}</p>
        )}
        <div className="flex items-center gap-2 text-[10px] text-slate-500 pt-0.5">
          <span className="whitespace-nowrap">{it.time_label}</span>
          <span
            className={`flex items-center gap-0.5 whitespace-nowrap ${
              it.warn === "full"
                ? "text-red-600 font-medium"
                : it.warn === "empty"
                  ? "text-amber-600"
                  : ""
            }`}
          >
            <Users size={9} />
            {it.students}
            {it.capacity ? `/${it.capacity}` : ""}
          </span>
          {it.lessons_held > 0 && (
            <span className="whitespace-nowrap text-slate-400">
              {it.lessons_held} dars
            </span>
          )}
        </div>
        {it.avg_age && (
          <p className="text-[10px] text-slate-400">
            o'rtacha {it.avg_age} yosh
          </p>
        )}
      </div>
    </Link>
  );
}

type TTChange = {
  kind: "move" | "sub";
  group_id: number;
  group: string;
  teacher?: string | null;
  substitute?: string | null;
  from_date?: string;
  to_date?: string;
  date?: string;
};

export default function TimetableGrid() {
  const [data, setData] = useState<Grid | null>(null);
  const [day, setDay] = useState("mon");
  const [branchId, setBranchId] = useState<number | null>(null);
  const [usage, setUsage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api
      .get<Grid>(`/timetable/grid?day=${day}${branchParam(branchId)}`)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [day, branchId]);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (error)
    return (
      <div className="py-8">
        <p className="text-sm text-red-600 mb-2">{error}</p>
        <button
          onClick={load}
          className="text-sm text-brand-600 hover:text-brand-700 underline"
        >
          Qayta urinish
        </button>
      </div>
    );
  if (!data) return null;

  const width = data.slots.length * SLOT_W;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <CalendarDays size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Dars jadvali</h1>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Qaysi xona, qaysi soat, qaysi guruh — bir qarashda
      </p>

      {/* --- Kun tanlash --- */}
      <div className="flex flex-wrap items-center gap-1.5 mb-4">
        {data.presets.map((p) => (
          <button
            key={p.key}
            onClick={() => setDay(p.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              day === p.key
                ? "bg-brand-600 border-brand-600 text-white"
                : "bg-white border-brand-300 text-brand-700 hover:bg-brand-50"
            }`}
          >
            {p.label}
          </button>
        ))}
        <div className="w-2" />
        {data.weekdays.map((w) => (
          <button
            key={w.key}
            onClick={() => setDay(w.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              day === w.key
                ? "bg-brand-600 text-white"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {w.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <BranchPicker value={branchId} onChange={setBranchId} />
        <span className="text-sm text-slate-500">
          {data.total_groups} guruh · {data.total_students} o'quvchi
        </span>
        <div className="flex-1" />
        <button
          onClick={() => setUsage(!usage)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm transition ${
            usage
              ? "bg-brand-50 border-brand-400 text-brand-700"
              : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
          }`}
        >
          <Rows3 size={14} /> Xonalar samaradorligi
        </button>
        {data.can_export && (
          <button
            onClick={() =>
              exportToExcel(
                `dars-jadvali-${data.day}`,
                data.day_label,
                data.rooms.flatMap((r) =>
                  r.items.map((i) => ({
                    Xona: r.name,
                    Guruh: i.group,
                    Fan: i.subject_label ?? "",
                    Daraja: i.level_label ?? "",
                    "O'qituvchi": i.teacher ?? "",
                    Vaqt: i.time_label ?? "",
                    "O'quvchi": i.students,
                    "Sig'im": i.capacity ?? "",
                    "O'tilgan dars": i.lessons_held,
                  }))
                )
              )
            }
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
          >
            <Download size={14} /> Excelga eksport
          </button>
        )}
      </div>

      {((data as unknown as { changes?: TTChange[] }).changes?.length ?? 0) > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={15} className="text-amber-600" />
            <p className="text-sm font-medium text-amber-900">
              Yaqin kunlardagi o'zgarishlar — yangi o'quvchi chaqirishda
              hisobga oling!
            </p>
          </div>
          {((data as unknown as { changes?: TTChange[] }).changes ?? []).map(
            (c, i) => (
              <p key={i} className="text-xs text-amber-800">
                {c.kind === "move" ? (
                  <>
                    <b>{c.group}</b>
                    {c.teacher ? ` (${c.teacher})` : ""}: {c.from_date} dagi
                    dars <b>{c.to_date}</b> ga ko'chirilgan
                  </>
                ) : (
                  <>
                    <b>{c.group}</b> ({c.date}): {c.teacher || "ustoz"}{" "}
                    o'rniga <b>{c.substitute || "o'rinbosar"}</b> dars o'tadi
                  </>
                )}
              </p>
            )
          )}
        </div>
      )}

      {data.clashes.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={15} className="text-red-600" />
            <p className="text-sm font-medium text-red-900">
              {data.clashes.length} ta xona to'qnashuvi
            </p>
          </div>
          {data.clashes.map((c, i) => (
            <p key={i} className="text-xs text-red-800">
              {c.room} · {c.time}: {c.groups.join(" va ")}
            </p>
          ))}
        </div>
      )}

      {/* --- Xonalar samaradorligi --- */}
      {usage && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Xonalar samaradorligi — {data.day_label}
          </p>
          <div className="space-y-2">
            {[...data.rooms]
              .sort((a, b) => b.usage - a.usage)
              .map((r) => (
                <div key={r.id} className="flex items-center gap-3">
                  <span className="text-sm text-slate-700 w-40 truncate">
                    {r.name}
                  </span>
                  <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        r.usage >= 50
                          ? "bg-emerald-500"
                          : r.usage >= 25
                            ? "bg-amber-500"
                            : "bg-red-400"
                      }`}
                      style={{ width: `${Math.min(100, r.usage)}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-600 w-24 text-right">
                    {r.busy_hours} soat · {r.usage}%
                  </span>
                </div>
              ))}
          </div>
          <p className="text-xs text-slate-400 mt-3">
            Bo'sh turgan xona — bu ijara puli. Eng past qatorlarga guruh
            qo'yish mumkin.
          </p>
        </div>
      )}

      {/* --- To'r --- */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <div style={{ minWidth: width + 180 }}>
          {/* Sarlavha: vaqtlar */}
          <div className="flex sticky top-0 bg-slate-50 border-b border-slate-200 z-10">
            <div className="w-44 shrink-0 px-4 py-2 text-xs font-medium text-slate-500">
              XONA / VAQT
            </div>
            <div className="relative" style={{ width }}>
              <div className="flex">
                {data.slots.map((t) => (
                  <div
                    key={t}
                    className="text-[11px] text-slate-500 py-2 text-center shrink-0 border-l border-slate-100"
                    style={{ width: SLOT_W }}
                  >
                    {t}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Xonalar */}
          {data.rooms.length === 0 ? (
            <p className="text-sm text-slate-400 py-10 text-center">
              Xona kiritilmagan. O'quv bo'limi → Xonalar bo'limidan
              qo'shing.
            </p>
          ) : (
            data.rooms.map((r) => (
              <div
                key={r.id}
                className="flex border-b border-slate-100 last:border-0"
                style={{ height: ROW_H }}
              >
                <div className="w-44 shrink-0 px-4 flex flex-col justify-center">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-brand-200 bg-brand-50 text-xs font-medium text-brand-800 self-start">
                    <DoorOpen size={12} />
                    {r.name}
                  </span>
                  <span className="text-[10px] text-slate-400 mt-1 pl-1">
                    {r.capacity ? `${r.capacity} kishilik · ` : ""}
                    {r.busy_hours} soat band
                  </span>
                </div>
                <div className="relative" style={{ width }}>
                  {/* Fon chiziqlari */}
                  <div className="absolute inset-0 flex">
                    {data.slots.map((t) => (
                      <div
                        key={t}
                        className="border-l border-slate-50 shrink-0"
                        style={{ width: SLOT_W }}
                      />
                    ))}
                  </div>
                  {r.items.map((it) => (
                    <Block key={it.group_id} it={it} />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* --- Xonasiz guruhlar --- */}
      {data.no_room.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-4">
          <p className="text-sm font-medium text-amber-900 mb-1">
            {data.no_room.length} ta guruhga xona biriktirilmagan
          </p>
          <p className="text-xs text-amber-800">
            {data.no_room.map((g) => g.group).join(", ")} — guruhni
            tahrirlab xona tanlang.
          </p>
        </div>
      )}

      {data.unplaced.length > 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mt-3">
          <p className="text-sm font-medium text-slate-700 mb-1">
            {data.unplaced.length} ta guruhda dars kunlari yoki vaqti yo'q
          </p>
          <p className="text-xs text-slate-500">
            {data.unplaced.map((g) => g.group).join(", ")}
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 mt-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded ring-2 ring-red-300 bg-white" />
          to'lgan guruh
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded ring-2 ring-amber-300 bg-white" />
          yarmidan kam to'lgan
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-teal-100 border border-teal-300" />
          ingliz tili
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-violet-100 border border-violet-300" />
          rus tili
        </span>
      </div>
    </div>
  );
}
