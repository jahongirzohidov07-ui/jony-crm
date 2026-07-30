import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Building2, Info, DoorOpen, Users } from "lucide-react";
import { api, type FillReport } from "../lib/api";
import { BranchPicker, branchParam } from "./BranchPicker";

const TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  amber: "bg-amber-100 text-amber-700",
  orange: "bg-orange-100 text-orange-700",
  red: "bg-red-100 text-red-700",
};
const BAR: Record<string, string> = {
  emerald: "bg-emerald-500",
  teal: "bg-teal-500",
  amber: "bg-amber-500",
  orange: "bg-orange-500",
  red: "bg-red-500",
};

/**
 * O'quv markaz qanchaga to'lgan.
 *
 * Sig'im: bitta xonaga toq kunlari 2 ta guruh, juft kunlari 2 ta —
 * jami 4 ta. Xona 25 kishilik bo'lsa bitta xona 100 o'quvchi
 * sig'diradi. Zo'r ishlaganda 5 ta guruh, ajoyibda 6 ta.
 */
export function FillTab() {
  const [d, setD] = useState<FillReport | null>(null);
  const [level, setLevel] = useState("normal");
  const [branchId, setBranchId] = useState<number | null>(null);
  const [tab, setTab] = useState<"filial" | "xona" | "ustoz">("filial");

  useEffect(() => {
    api
      .get<FillReport>(
        `/analytics/fill?level=${level}${branchParam(branchId)}`
      )
      .then(setD);
  }, [level, branchId]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1">
          {d.levels.map((l) => (
            <button
              key={l.key}
              onClick={() => setLevel(l.key)}
              title={l.description}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                level === l.key
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {l.label}
              <span className="text-xs opacity-70"> · {l.groups_per_room} guruh</span>
            </button>
          ))}
        </div>
        <BranchPicker value={branchId} onChange={setBranchId} />
      </div>

      {/* --- Katta karta --- */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 mb-4">
        <div className="flex flex-wrap items-end gap-6">
          <div>
            <p className="text-xs text-slate-500 mb-1">
              O'quv markaz to'lganligi
            </p>
            <p className="text-5xl font-semibold text-slate-900 leading-none">
              {d.percent}
              <span className="text-2xl text-slate-400">%</span>
            </p>
            <span
              className={`inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                TONE[d.tone] || TONE.amber
              }`}
            >
              {d.label}
            </span>
          </div>
          <div className="flex-1 min-w-[220px]">
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>
                {d.students.toLocaleString("ru-RU")} o'quvchi
              </span>
              <span>
                sig'im {d.capacity.toLocaleString("ru-RU")}
              </span>
            </div>
            <div className="h-4 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`h-full rounded-full ${BAR[d.tone] || BAR.amber}`}
                style={{ width: `${Math.min(100, d.percent)}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1.5">
              Yana <b>{d.free.toLocaleString("ru-RU")}</b> o'quvchi sig'adi
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5 pt-5 border-t border-slate-100">
          <Small label="Xonalar" value={String(d.rooms)} />
          <Small
            label="Guruh o'rni"
            value={`${d.groups_now} / ${d.group_slots}`}
            hint={`xonaga ${d.groups_per_room} ta`}
          />
          <Small
            label="Bo'sh o'rin"
            value={d.free.toLocaleString("ru-RU")}
          />
          <Small
            label="Xonasiz o'quvchi"
            value={String(d.students_without_room)}
            hint={d.students_without_room ? "sig'imga kirmaydi" : undefined}
          />
        </div>
      </div>

      {/* --- Uch daraja solishtiruvi --- */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        {d.levels.map((l) => (
          <button
            key={l.key}
            onClick={() => setLevel(l.key)}
            className={`text-left rounded-xl border p-4 transition ${
              l.current
                ? "border-brand-400 bg-brand-50"
                : "border-slate-200 bg-white hover:border-slate-300"
            }`}
          >
            <p className="text-xs text-slate-500">{l.label}</p>
            <p className="text-2xl font-semibold text-slate-900">
              {l.percent}%
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              sig'im {l.capacity.toLocaleString("ru-RU")} · yana {l.free}
            </p>
            <p className="text-xs text-slate-400">{l.description}</p>
          </button>
        ))}
      </div>

      {/* --- Kesimlar --- */}
      <div className="flex gap-1 mb-3">
        {(
          [
            ["filial", `Filiallar (${d.by_branch.length})`],
            ["xona", `Xonalar (${d.by_room.length})`],
            ["ustoz", `Ustozlar (${d.by_teacher.length})`],
          ] as const
        ).map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === k
                ? "bg-slate-100 border-slate-300 text-slate-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {tab === "filial" && (
        <Table
          icon={Building2}
          rows={d.by_branch.map((r) => ({
            key: String(r.branch_id),
            name: r.name,
            sub: `${r.rooms} xona · ${r.groups}/${r.group_slots} guruh`,
            students: r.students,
            capacity: r.capacity,
            free: r.free,
            percent: r.percent,
            label: r.label,
            tone: r.tone,
          }))}
        />
      )}
      {tab === "xona" && (
        <Table
          icon={DoorOpen}
          rows={d.by_room.map((r) => ({
            key: String(r.room_id),
            name: r.name,
            sub:
              `${r.branch} · ${r.seats} o'rin · toq ${r.odd_groups}` +
              ` / juft ${r.even_groups} guruh`,
            students: r.students,
            capacity: r.capacity,
            free: r.free,
            percent: r.percent,
            label: r.label,
            tone: r.tone,
          }))}
        />
      )}
      {tab === "ustoz" && (
        <Table
          icon={Users}
          rows={d.by_teacher.map((r) => ({
            key: String(r.teacher_id),
            name: r.name,
            sub:
              `${r.grade_label} · ${r.groups}/${r.max_groups} guruh` +
              (r.branch ? ` · ${r.branch}` : ""),
            students: r.students,
            capacity: r.capacity,
            free: r.free,
            percent: r.percent,
            label: r.label,
            tone: r.tone,
          }))}
        />
      )}

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
        {d.students_without_room > 0 && (
          <span>
            {" "}
            {d.students_without_room} o'quvchi xonasi biriktirilmagan
            guruhda — ular sig'im hisobiga kirmaydi.
          </span>
        )}
      </p>
    </div>
  );
}

function Table({
  rows,
  icon: Icon,
}: {
  rows: {
    key: string; name: string; sub: string; students: number;
    capacity: number; free: number; percent: number;
    label: string; tone: string;
  }[];
  icon: React.ElementType;
}) {
  if (rows.length === 0)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        Ma'lumot yo'q.
      </p>
    );
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div
          key={r.key}
          className="flex flex-wrap items-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white"
        >
          <Icon size={15} className="text-slate-400 shrink-0" />
          <div className="min-w-[150px] flex-1">
            <p className="text-sm font-medium text-slate-800">{r.name}</p>
            <p className="text-xs text-slate-400">{r.sub}</p>
          </div>

          <div className="w-40">
            <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`h-full rounded-full ${BAR[r.tone] || BAR.amber}`}
                style={{ width: `${Math.min(100, r.percent)}%` }}
              />
            </div>
          </div>

          <span className="text-sm text-slate-600 w-28 text-right">
            {r.students} / {r.capacity}
          </span>
          <span className="text-sm font-semibold text-slate-900 w-14 text-right">
            {r.percent}%
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium w-24 text-center ${
              TONE[r.tone] || TONE.amber
            }`}
          >
            {r.label}
          </span>
          <span className="text-xs text-slate-400 w-20 text-right">
            +{r.free} joy
          </span>
        </div>
      ))}
    </div>
  );
}

function Small({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

/**
 * Dashboarddagi ixcham karta: markaz qanchaga to'lgan.
 * Asoschi uchun kunlik raqam — batafsili Analitika bo'limida.
 */
export function FillCard() {
  const [d, setD] = useState<FillReport | null>(null);

  useEffect(() => {
    api
      .get<FillReport>("/analytics/fill")
      .then(setD)
      .catch(() => setD(null));
  }, []);

  if (!d || d.capacity === 0) return null;

  return (
    <Link
      to="/analytics"
      className="block rounded-xl border border-slate-200 bg-white p-5 mb-6 hover:border-brand-400 transition"
    >
      <div className="flex flex-wrap items-center gap-5">
        <div>
          <p className="text-xs text-slate-500 mb-0.5">
            Markaz to'lganligi
          </p>
          <p className="text-3xl font-semibold text-slate-900 leading-none">
            {d.percent}
            <span className="text-lg text-slate-400">%</span>
          </p>
        </div>
        <div className="flex-1 min-w-[200px]">
          <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={`h-full rounded-full ${BAR[d.tone] || BAR.amber}`}
              style={{ width: `${Math.min(100, d.percent)}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1.5">
            {d.students.toLocaleString("ru-RU")} o'quvchi ·{" "}
            {d.rooms} xona · sig'im{" "}
            {d.capacity.toLocaleString("ru-RU")} · yana{" "}
            <b>{d.free.toLocaleString("ru-RU")}</b> sig'adi
          </p>
        </div>
        <span
          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
            TONE[d.tone] || TONE.amber
          }`}
        >
          {d.label}
        </span>
      </div>
    </Link>
  );
}
