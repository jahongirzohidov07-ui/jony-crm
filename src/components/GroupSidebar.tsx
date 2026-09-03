import { useEffect, useState } from "react";
// (2026-08-18) "Guruhdan o'chirilganlar" yig'ma bo'limi uchun
import { ChevronDown, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Download, Phone, Pencil } from "lucide-react";
import { api, type Group, type GroupProgress, type Student } from "../lib/api";
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

/** "Step 2 · Unit 7/12" — guruh qayerga yetgani.
 *
 *  Ma'lumot IMTIHONLARDAN olinadi: natijasi kiritilgan eng oxirgi unit
 *  testi. Hech kim qo'lda kiritmaydi, shuning uchun eskirmaydi. */
function ProgressBox({ groupId }: { groupId: number }) {
  const [p, setP] = useState<GroupProgress | null>(null);

  useEffect(() => {
    api
      .get<GroupProgress>(`/groups/${groupId}/progress`)
      .then(setP)
      .catch(() => setP(null));
  }, [groupId]);

  if (!p) return null;
  const pct = Math.max(0, Math.min(100, p.percent));

  return (
    <div className="mb-4 rounded-xl border border-brand-100 bg-brand-50/60 px-3 py-2.5">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-brand-800">
          {p.level_label || "Daraja tanlanmagan"}
          {p.unit > 0 ? (
            <>
              {" · "}
              <span className="text-brand-700">
                Unit {p.unit}
                <span className="text-brand-500 font-normal">
                  /{p.unit_total}
                </span>
              </span>
            </>
          ) : null}
        </p>
        {p.unit > 0 && p.next_unit ? (
          <span className="text-[11px] text-brand-600 shrink-0">
            keyingisi: Unit {p.next_unit}
          </span>
        ) : null}
      </div>

      {p.unit > 0 ? (
        <div className="mt-2 h-1.5 rounded-full bg-brand-100 overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}

      <p className="text-[11px] text-slate-500 mt-1.5">
        {p.last_exam ? (
          <>
            Oxirgi imtihon: Unit {p.last_exam.unit_no}
            {p.last_exam.date ? ` · ${formatDate(p.last_exam.date)}` : ""}
            {p.last_exam.avg_percent !== null &&
            p.last_exam.avg_percent !== undefined
              ? ` · o'rtacha ${p.last_exam.avg_percent}%`
              : ""}
          </>
        ) : (
          "Hali natijasi kiritilgan unit imtihoni yo'q"
        )}
      </p>
    </div>
  );
}

/** Telefonni 998siz qisqa ko'rsatish: 88-773-87-93 — ro'yxatda joy tejaydi. */
function shortPhone(p: string): string {
  const d = p.replace(/\D/g, "");
  const t = d.length > 9 ? d.slice(-9) : d;
  return t.length === 9
    ? `${t.slice(0, 2)}-${t.slice(2, 5)}-${t.slice(5, 7)}-${t.slice(7, 9)}`
    : p;
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
  // GURUHDAN O'CHIRILGANLAR (2026-08-18, Jahongir: "Pastda alohida
  // guruhdan ochirilganlar bolimi tursa osha yerdni bossagina alohida
  // chiqsin bosilmasa chiqmasin"). Ro'yxat faqat ochilganda so'raladi.
  const [goneOpen, setGoneOpen] = useState(false);
  const [gone, setGone] = useState<Student[] | null>(null);
  const [goneBusy, setGoneBusy] = useState(false);
  function toggleGone() {
    const next = !goneOpen;
    setGoneOpen(next);
    if (next && gone === null && !goneBusy) {
      setGoneBusy(true);
      api.get<Student[]>(`/students?group_id=${group.id}&left=1`)
        .then(setGone)
        .catch(() => setGone([]))
        .finally(() => setGoneBusy(false));
    }
  }

  // MUZLATILGAN O'QUVCHI USTOZGA HAM KO'RINADI (2026-09-03,
  // Jahongir: "ustozlarga muzlatilgan o'quvchilari korinsin faqat
  // yoqlamasi chiqmasin").
  //
  // Ilgari bu yerda ustoz uchun muzlatilganlar ro'yxatdan
  // filtrlanardi. Endi ular ko'k nuqta va "Muzlatilgan" belgisi
  // bilan turadi — ustoz kim qaytishini biladi. Yo'qlamaga esa
  // ular baribir tushmaydi: davomat jadvalini server beradi va
  // muzlatilganlar u yerdan chiqarilgan.
  function load() {
    setLoading(true);
    api
      .get<Student[]>(`/students?group_id=${group.id}`)
      .then(setStudents)
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    setGone(null);
    setGoneOpen(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [group.id]);

  // "Boshqa guruhga o'tkazish" ro'yxati uchun.
  useEffect(() => {
    api.get<Group[]>("/groups").then(setGroups).catch(() => setGroups([]));
  }, []);

  const days = parseDays(group.lesson_days);
  const debtors = students.filter((s) => s.balance < 0).length;
  const trials = students.filter((s) => s.status === "trial").length;

  return (
    <aside className="w-full lg:w-[27rem] shrink-0 bg-white rounded-xl border border-slate-200 p-5">
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

      <ProgressBox groupId={group.id} />

      <div className="space-y-1 mb-4">
        <Row
          label="O'qituvchi"
          value={
            <span className="text-brand-700">{group.teacher?.full_name || "—"}</span>
          }
        />
        <Row
          label="Support"
          value={
            group.support_label ? (
              <span className="text-sky-700">{group.support_label}</span>
            ) : (
              <span className="text-amber-600">yo'q</span>
            )
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
                    className={`text-[13px] whitespace-nowrap ${
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
                    <span className="text-[11px] text-slate-400 shrink-0 ml-auto hidden sm:flex items-center gap-1">
                      <Phone size={10} />
                      {shortPhone(s.phone)}
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

          {/* GURUHDAN O'CHIRILGANLAR — yig'ma bo'lim. Bosilmasa
              so'ralmaydi ham, ko'rinmaydi ham. */}
          <div className="mt-3 pt-2 border-t border-slate-100">
            <button
              onClick={toggleGone}
              className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-600"
            >
              {goneOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
              Guruhdan o'chirilganlar
              {gone !== null && ` (${gone.length})`}
            </button>
            {goneOpen && (
              <div className="mt-1.5 space-y-0.5 -mx-2">
                {goneBusy && (
                  <p className="text-xs text-slate-400 px-2 py-1">
                    Yuklanmoqda...
                  </p>
                )}
                {gone !== null && gone.length === 0 && !goneBusy && (
                  <p className="text-xs text-slate-400 px-2 py-1">
                    Bu guruhdan o'chirilganlar yo'q
                  </p>
                )}
                {(gone || []).map((s) => (
                  <div key={s.id}
                    className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-slate-50">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0 bg-slate-300" />
                    <Link to={`/students/${s.id}`}
                      className="text-[13px] text-slate-400 hover:text-slate-600 line-through decoration-slate-300">
                      {s.full_name}
                    </Link>
                    <span className="ml-auto text-[10px] uppercase tracking-wide text-slate-400 shrink-0">
                      {s.status === "archived" ? "arxiv"
                        : s.status === "left" ? "ketgan" : s.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </aside>
  );
}

// LC UP uslubi: ism bitta qatorda, panel kengaytirilgan
