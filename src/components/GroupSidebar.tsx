import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download, Phone, Pencil } from "lucide-react";
import { api, type Group, type Student } from "../lib/api";
import { StudentRowMenu } from "./StudentRowMenu";
import { formatSom, formatDate } from "../lib/format";
import { subjectLine, WEEKDAYS, parseDays } from "../lib/subjects";
import { exportToExcel } from "../lib/exportXlsx";

/** O'quvchi holatiga qarab rangli nuqta - ro'yxatda darrov ko'zga tashlanadi. */
function statusDot(status: string, balance: number) {
  // Muzlatilgan — KO'K va hamma narsadan ustun: qarzdor bo'lsa ham
  // avval muzlatilgani ko'rinadi
  if (status === "frozen") return { color: "bg-sky-500", title: "Muzlatilgan" };
  if (balance < 0) return { color: "bg-red-500", title: "Qarzdor" };
  // Sinovdagi o'quvchi yonida chiroq bo'lmaydi
  if (status === "trial") return null;
  if (status === "archived") return { color: "bg-slate-300", title: "Arxiv" };
  return { color: "bg-emerald-500", title: "Faol" };
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <p className="text-sm text-slate-600">
      <span className="font-medium text-slate-700">{label}:</span> {value}
    </p>
  );
}

export function GroupSidebar({
  group,
  onEdit,
}: {
  group: Group;
  onEdit?: () => void;
}) {
  const [students, setStudents] = useState<Student[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<Student[]>(`/students?group_id=${group.id}`)
      .then(setStudents)
      .finally(() => setLoading(false));
  }

  useEffect(load, [group.id]);

  // "Boshqa guruhga o'tkazish" ro'yxati uchun.
  useEffect(() => {
    api.get<Group[]>("/groups").then(setGroups).catch(() => setGroups([]));
  }, []);

  const days = parseDays(group.lesson_days);
  const debtors = students.filter((s) => s.balance < 0).length;
  const trials = students.filter((s) => s.status === "trial").length;

  return (
    <aside className="w-full lg:w-80 shrink-0 bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start justify-between gap-2 mb-3">
        <h1 className="text-lg font-semibold text-slate-900">{group.name}</h1>
        {onEdit && (
          <button
            onClick={onEdit}
            title="Guruhni tahrirlash"
            className="p-1.5 rounded-md text-slate-400 hover:text-brand-600 hover:bg-slate-50 shrink-0"
          >
            <Pencil size={15} />
          </button>
        )}
      </div>

      <div className="space-y-1 mb-4">
        <Row
          label="O'qituvchi"
          value={
            <span className="text-brand-700">{group.teacher?.full_name || "—"}</span>
          }
        />
        <Row label="Narx" value={formatSom(group.monthly_fee)} />
        {group.lesson_time && <Row label="Vaqt" value={group.lesson_time} />}
        {subjectLine(group) && <Row label="Kurs" value={subjectLine(group)} />}
        {group.start_date && (
          <Row label="Boshlanish sanasi" value={formatDate(group.start_date)} />
        )}
        {group.room && <Row label="Xona" value={group.room} />}
        <Row label="Filial" value={group.branch?.name || "—"} />
        {days.length > 0 && (
          <p className="text-sm text-slate-600">
            <span className="font-medium text-slate-700">Dars kunlari:</span>{" "}
            {WEEKDAYS.filter((d) => days.includes(d.key))
              .map((d) => d.label)
              .join(", ")}
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 pb-3 mb-3 border-b border-slate-100">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Qarzdor
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Faol
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-sky-500 inline-block" /> Muzlatilgan
        </span>
        <span className="text-slate-400">Sinovda — chiroqsiz</span>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">Yuklanmoqda...</p>
      ) : students.length === 0 ? (
        <p className="text-sm text-slate-400 py-3">Guruhda o'quvchi yo'q</p>
      ) : (
        <>
          <div className="space-y-0.5 -mx-2">
            {students.map((s, i) => {
              const dot = statusDot(s.status, s.balance);
              const frozen = s.status === "frozen";
              return (
                <div
                  key={s.id}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 group"
                >
                  <span className="text-xs text-slate-400 w-4 shrink-0">{i + 1}</span>
                  {dot ? (
                    <span
                      className={`w-2.5 h-2.5 rounded-full shrink-0 ${dot.color}`}
                      title={dot.title}
                    />
                  ) : (
                    <span className="w-2.5 h-2.5 shrink-0" title="Sinovda" />
                  )}
                  <Link
                    to={`/students/${s.id}`}
                    className={`text-sm flex-1 min-w-0 break-words leading-snug ${
                      frozen
                        ? "text-sky-600 font-medium hover:text-sky-700"
                        : "text-slate-800 hover:text-brand-700"
                    }`}
                    title={frozen ? "Muzlatilgan" : undefined}
                  >
                    {s.full_name}
                    {frozen && (
                      <span className="ml-1.5 text-[10px] uppercase tracking-wide bg-sky-50 text-sky-600 px-1.5 py-0.5 rounded">
                        muz
                      </span>
                    )}
                  </Link>
                  {s.phone && (
                    <span className="text-xs text-slate-400 shrink-0 hidden sm:flex items-center gap-1">
                      <Phone size={11} />
                      {s.phone}
                    </span>
                  )}
                  <StudentRowMenu student={s} groups={groups} onChanged={load} />
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
            <p className="text-xs text-slate-500">
              {students.length} o'quvchi
              {trials > 0 && (
                <span className="text-sky-600"> · {trials} sinovda</span>
              )}
              {debtors > 0 && (
                <span className="text-red-600"> · {debtors} qarzdor</span>
              )}
            </p>
            <button
              onClick={() =>
                exportToExcel(`${group.name}-oquvchilar`, "O'quvchilar",
                  students.map((s, i) => ({
                    "T/R": i + 1,
                    "F.I.Sh.": s.full_name,
                    Telefon: s.phone ?? "",
                    "Ota-ona": s.parent_phone ?? "",
                    Holat: s.status,
                    Balans: s.balance,
                  })))
              }
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-brand-600"
            >
              <Download size={13} /> Excel
            </button>
          </div>
        </>
      )}
    </aside>
  );
}
