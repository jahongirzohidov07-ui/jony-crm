import { useEffect, useState } from "react";
import {
  TrendingUp, TrendingDown, AlertTriangle, Check, Info, X,
  BookOpen, Headphones, Pencil, GraduationCap,
} from "lucide-react";
import {
  api, type CareerMap, type GradeRow, type GradeState,
  type TeacherCareer,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  teal: "bg-teal-100 text-teal-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  rose: "bg-rose-100 text-rose-700",
  emerald: "bg-emerald-100 text-emerald-700",
  red: "bg-red-100 text-red-700",
};

function Badge({ tone, children }: { tone: string; children: React.ReactNode }) {
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
        TONE[tone] || TONE.slate
      }`}
    >
      {children}
    </span>
  );
}

// ======================================================= Karyera xaritasi
export function CareerTab() {
  const [d, setD] = useState<CareerMap | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [editing, setEditing] = useState<GradeRow | null>(null);
  const [tab, setTab] = useState<"ustozlar" | "darajalar">("ustozlar");

  function load() {
    api.get<CareerMap>("/career").then(setD);
  }
  useEffect(load, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex gap-1 mb-4">
        {(
          [
            ["ustozlar", `Ustozlar (${d.rows.length})`],
            ["darajalar", `Daraja jadvali (${d.grades.length})`],
          ] as const
        ).map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {tab === "ustozlar" ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
            <Box label="Ustozlar" value={String(d.rows.length)} />
            <Box
              label="Ko'tarilishga tayyor"
              value={String(d.ready.length)}
              tone={d.ready.length ? "good" : "plain"}
            />
            <Box
              label="Xavf ostida"
              value={String(d.at_risk.length)}
              hint="oylik test o'rtachasi past"
              tone={d.at_risk.length ? "bad" : "plain"}
            />
            <Box
              label="Qayta tayyorlashda"
              value={String(d.remediation.length)}
              hint="yangi guruh ochilmaydi"
              tone={d.remediation.length ? "bad" : "plain"}
            />
          </div>

          {/* Daraja bo'yicha taqsimot */}
          <div className="flex flex-wrap gap-2 mb-5">
            {d.grades.map((g) => (
              <div
                key={g.key}
                className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200 bg-white"
              >
                <Badge tone={g.tone}>{g.label}</Badge>
                <span className="text-sm text-slate-800 font-medium">
                  {g.teachers}
                </span>
                <span className="text-xs text-slate-400">
                  {formatSom(g.rate_per_student)}
                </span>
              </div>
            ))}
          </div>

          <div className="space-y-2">
            {d.rows.map((r) => (
              <TeacherRow
                key={r.teacher_id}
                r={r}
                onOpen={() => setOpen(r.teacher_id)}
              />
            ))}
          </div>
        </>
      ) : (
        <GradeTable d={d} onEdit={setEditing} />
      )}

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>

      {open !== null && (
        <CareerCard
          teacherId={open}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
      {editing && (
        <GradeForm
          row={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function TeacherRow({ r, onOpen }: { r: GradeState; onOpen: () => void }) {
  const border = r.in_remediation
    ? "border-red-300 bg-red-50"
    : r.should_demote
      ? "border-amber-300 bg-amber-50"
      : r.ready
        ? "border-emerald-300 bg-emerald-50"
        : "border-slate-200 bg-white";

  return (
    <button
      onClick={onOpen}
      className={`w-full text-left rounded-xl border p-4 hover:border-brand-400 transition ${border}`}
    >
      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-[160px] flex-1">
          <p className="text-sm font-medium text-slate-800">{r.full_name}</p>
          <p className="text-xs text-slate-400">
            {r.branch ? `${r.branch} · ` : ""}
            {Math.round(r.months)} oy tajriba · {r.groups}
            {r.max_groups ? `/${r.max_groups}` : ""} guruh
          </p>
        </div>

        <Badge tone={r.tone}>{r.grade_label}</Badge>
        <span className="text-sm text-slate-700 w-28 text-right">
          {formatSom(r.rate_per_student)}
          <span className="text-xs text-slate-400"> /o'quvchi</span>
        </span>

        <div className="w-40 text-right">
          {r.pass_rate !== null && r.pass_rate !== undefined ? (
            <>
              <p
                className={`text-sm ${
                  r.pass_needed && r.pass_rate >= r.pass_needed
                    ? "text-emerald-600"
                    : r.pass_rate < 50
                      ? "text-red-600"
                      : "text-slate-700"
                }`}
              >
                {r.pass_rate}% o'tdi
              </p>
              <p className="text-xs text-slate-400">
                {r.pass_needed ? `kerak ${r.pass_needed}%` : "—"}
              </p>
            </>
          ) : (
            <p className="text-xs text-slate-400">natija yo'q</p>
          )}
        </div>

        <div className="w-28 text-right shrink-0">
          {r.in_remediation ? (
            <Badge tone="red">Qayta tayyorlash</Badge>
          ) : r.should_demote ? (
            <span className="flex items-center justify-end gap-1 text-xs text-amber-700">
              <TrendingDown size={12} /> Tushish xavfi
            </span>
          ) : r.ready ? (
            <span className="flex items-center justify-end gap-1 text-xs text-emerald-700">
              <TrendingUp size={12} /> Tayyor
            </span>
          ) : r.next_label ? (
            <span className="text-xs text-slate-400">
              {r.missing.length} ta shart
            </span>
          ) : (
            <span className="text-xs text-slate-400">Eng yuqori</span>
          )}
        </div>
      </div>

      {r.in_remediation && r.remediation_reason && (
        <p className="text-xs text-red-700 mt-2">
          {r.remediation_reason} · {r.remediation_until} gacha yangi guruh
          ochilmaydi
        </p>
      )}
    </button>
  );
}

// ======================================================== Daraja jadvali
function GradeTable({
  d,
  onEdit,
}: {
  d: CareerMap;
  onEdit: (g: GradeRow) => void;
}) {
  return (
    <div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Daraja</th>
              <th className="text-right w-32">Bir o'quvchidan</th>
              <th className="text-right w-24">Tajriba</th>
              <th className="text-right w-20">Guruh</th>
              <th className="text-left w-28 pl-3">Sertifikat</th>
              <th className="text-right w-28">O'tish sharti</th>
              <th className="text-right w-28">Tushish</th>
              <th className="w-16" />
            </tr>
          </thead>
          <tbody>
            {d.grades.map((g) => (
              <tr key={g.key} className="border-t border-slate-100">
                <td className="px-4 py-2.5">
                  <Badge tone={g.tone}>{g.label}</Badge>
                </td>
                <td className="text-right text-slate-800 font-medium">
                  {formatSom(g.rate_per_student)}
                </td>
                <td className="text-right text-slate-600">
                  {g.min_months} oy
                </td>
                <td className="text-right text-slate-600">
                  {g.min_groups === g.max_groups
                    ? g.max_groups
                    : `${g.min_groups}-${g.max_groups}`}
                </td>
                <td className="pl-3 text-slate-600 text-xs">
                  {g.cert_label || "—"}
                  {g.needs_qualification && (
                    <span className="block text-rose-600">
                      + CELTA/TESOL/DELTA
                    </span>
                  )}
                </td>
                <td className="text-right text-slate-600">
                  {g.promote_pass_rate ? `${g.promote_pass_rate}%` : "—"}
                </td>
                <td className="text-right text-slate-600">
                  {g.demote_below ? `${g.demote_below}%` : "—"}
                </td>
                <td className="text-right pr-3">
                  {d.can_edit && (
                    <button
                      onClick={() => onEdit(g)}
                      className="text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500 mt-3">
        O'tish sharti — o'quvchilarning necha foizi bosqichdan o'tishi kerak
        (oxirgi {d.pass_window_months} oy). Tushish — oylik test o'rtachasi
        shundan past bo'lsa daraja pasayadi (oxirgi {d.test_window_days} kun).
        Qaror kamida {d.min_results} ta natija to'planganda qabul qilinadi.
      </p>
    </div>
  );
}

function GradeForm({
  row,
  onClose,
  onSaved,
}: {
  row: GradeRow;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    rate_per_student: String(row.rate_per_student ?? ""),
    min_months: String(row.min_months ?? ""),
    min_groups: String(row.min_groups ?? ""),
    max_groups: String(row.max_groups ?? ""),
    cert_label: row.cert_label ?? "",
    cert_min: String(row.cert_min ?? ""),
    promote_pass_rate: String(row.promote_pass_rate ?? ""),
    demote_below: String(row.demote_below ?? ""),
    min_results: String(row.min_results ?? ""),
    result_band: String(row.result_band ?? ""),
    min_age: String(row.min_age ?? ""),
    min_skill: String(row.min_skill ?? ""),
    level_pass_percent: String(row.level_pass_percent ?? ""),
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  const num = (v: string) => (v === "" ? null : Number(v));

  async function save() {
    setSaving(true);
    setErr("");
    try {
      const r = await api.put<{ groups_updated: number }>(
        `/career/grades/${row.key}`,
        {
          rate_per_student: num(f.rate_per_student),
          min_months: num(f.min_months),
          min_groups: num(f.min_groups),
          max_groups: num(f.max_groups),
          cert_label: f.cert_label || null,
          cert_min: num(f.cert_min),
          promote_pass_rate: num(f.promote_pass_rate),
          demote_below: num(f.demote_below),
          min_results: num(f.min_results),
          result_band: num(f.result_band),
          min_age: num(f.min_age),
          min_skill: num(f.min_skill),
          level_pass_percent: num(f.level_pass_percent),
        }
      );
      if (r.groups_updated) {
        setMsg(`${r.groups_updated} ta guruh stavkasi yangilandi`);
        setTimeout(onSaved, 1200);
      } else onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const F = ({
    k,
    label,
    hint,
  }: {
    k: keyof typeof f;
    label: string;
    hint?: string;
  }) => (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">
        {label}
      </label>
      <input
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        value={f[k]}
        onChange={(e) => setF({ ...f, [k]: e.target.value })}
      />
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-8 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">{row.label}</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <F
            k="rate_per_student"
            label="Bir o'quvchidan (so'm)"
            hint="oylik shundan hisoblanadi"
          />
          <F k="min_months" label="Eng kam tajriba (oy)" />
          <F k="min_groups" label="Eng kam guruh" />
          <F k="max_groups" label="Eng ko'p guruh" />
          <F k="cert_label" label="Sertifikat nomi" />
          <F k="cert_min" label="Sertifikat balli" />
          <F
            k="promote_pass_rate"
            label="O'tish sharti (%)"
            hint="shuncha o'quvchi bosqichdan o'tsa"
          />
          <F
            k="demote_below"
            label="Tushish chegarasi (%)"
            hint="oylik test o'rtachasi"
          />
          <F k="min_age" label="Eng kam yosh" />
          <F k="min_skill" label="Mahorat balli" />
          <F k="min_results" label="Yuqori natija soni" />
          <F k="result_band" label="Natija bandi" />
          <F
            k="level_pass_percent"
            label="O'quvchi o'tish balli (%)"
            hint="testda shundan yuqori = o'tdi"
          />
        </div>

        {err && <p className="text-sm text-red-600 mt-3">{err}</p>}
        {msg && <p className="text-sm text-emerald-600 mt-3">{msg}</p>}

        <p className="text-xs text-slate-400 mt-3">
          Narx o'zgartirilsa shu darajadagi ustozlarning guruhlariga o'zi
          qo'yiladi. Qo'lda narx kiritilgan guruhlarga tegilmaydi, o'tgan
          oylarning oyligi ham qayta hisoblanmaydi.
        </p>

        <button
          onClick={save}
          disabled={saving}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-4 disabled:opacity-60"
        >
          {saving ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </div>
    </div>
  );
}

// ==================================================== Ustoz karyera kartasi
export function CareerCard({
  teacherId,
  onClose,
}: {
  teacherId: number;
  onClose: () => void;
}) {
  const [d, setD] = useState<TeacherCareer | null>(null);
  const [tab, setTab] = useState<"holat" | "oqish" | "tarix">("holat");
  const [busy, setBusy] = useState(false);

  function load() {
    api.get<TeacherCareer>(`/teachers/${teacherId}/career`).then(setD);
  }
  useEffect(load, [teacherId]);

  async function setGrade(key: string) {
    setBusy(true);
    try {
      await api.post(`/teachers/${teacherId}/grade`, {
        grade: key,
        reason: "Karyera bo'limidan qo'lda o'zgartirildi",
      });
      load();
    } finally {
      setBusy(false);
    }
  }

  async function clearRem() {
    setBusy(true);
    try {
      await api.post(`/teachers/${teacherId}/remediation`, {});
      load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-start justify-center z-50 px-4 py-8 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl">
        {!d ? (
          <p className="text-sm text-slate-400 p-8">Yuklanmoqda...</p>
        ) : (
          <>
            <div className="flex items-start justify-between p-5 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2">
                  <GraduationCap size={16} className="text-slate-400" />
                  <h2 className="font-semibold text-slate-900">
                    {d.state.full_name}
                  </h2>
                  <Badge tone={d.state.tone}>{d.state.grade_label}</Badge>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  {formatSom(d.state.rate_per_student)} / o'quvchi ·{" "}
                  {Math.round(d.state.months)} oy tajriba
                  {d.state.grade_since
                    ? ` · ${formatDate(d.state.grade_since)} dan beri shu darajada`
                    : ""}
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex gap-1 px-5 border-b border-slate-100">
              {(
                [
                  ["holat", "Holat"],
                  ["oqish", "O'qish rejasi"],
                  ["tarix", `Tarix (${d.history.length})`],
                ] as const
              ).map(([k, l]) => (
                <button
                  key={k}
                  onClick={() => setTab(k)}
                  className={`px-3 py-2.5 text-sm font-medium border-b-2 -mb-px ${
                    tab === k
                      ? "border-brand-600 text-brand-700"
                      : "border-transparent text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>

            <div className="p-5">
              {tab === "holat" && (
                <StateTab
                  d={d}
                  busy={busy}
                  onSetGrade={setGrade}
                  onClearRem={clearRem}
                />
              )}
              {tab === "oqish" && (
                <StudyTab d={d} teacherId={teacherId} onDone={load} />
              )}
              {tab === "tarix" && <HistoryTab d={d} />}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StateTab({
  d,
  busy,
  onSetGrade,
  onClearRem,
}: {
  d: TeacherCareer;
  busy: boolean;
  onSetGrade: (k: string) => void;
  onClearRem: () => void;
}) {
  const s = d.state;
  return (
    <div>
      {s.in_remediation && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 mb-4">
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle size={13} className="text-red-600" />
            <p className="text-sm font-medium text-red-800">
              Qayta tayyorlash bosqichida
            </p>
          </div>
          <p className="text-xs text-red-700">{s.remediation_reason}</p>
          <p className="text-xs text-red-600 mt-1">
            {s.remediation_until} gacha yangi guruh ochilmaydi. O'tgan
            o'quvchilar boshqa ustozga beriladi, o'ta olmaganlarini ustozning
            o'zi tayyorlaydi.
          </p>
          {d.can_edit && (
            <button
              onClick={onClearRem}
              disabled={busy}
              className="mt-2 px-3 py-1.5 rounded-lg bg-white border border-red-300 text-xs text-red-700 hover:bg-red-100"
            >
              Qayta test topshirildi
            </button>
          )}
        </div>
      )}

      {/* Daraja yo'li */}
      <div className="flex flex-wrap items-center gap-1.5 mb-5">
        {d.grades.map((g, i) => {
          const cur = g.key === s.grade;
          const passed = d.grades.findIndex((x) => x.key === s.grade) > i;
          return (
            <div key={g.key} className="flex items-center gap-1.5">
              <button
                onClick={() => d.can_edit && onSetGrade(g.key)}
                disabled={!d.can_edit || busy}
                title={d.can_edit ? "Shu darajaga qo'yish" : undefined}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
                  cur
                    ? "bg-brand-600 border-brand-600 text-white"
                    : passed
                      ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                      : "bg-white border-slate-200 text-slate-400"
                } ${d.can_edit ? "hover:border-brand-400" : ""}`}
              >
                {g.label}
                <span className="block text-[10px] opacity-80">
                  {formatSom(g.rate_per_student)}
                </span>
              </button>
              {i < d.grades.length - 1 && (
                <span className="text-slate-300">→</span>
              )}
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Box
          label="Bosqichdan o'tganlar"
          value={s.pass_rate !== null && s.pass_rate !== undefined
            ? `${s.pass_rate}%` : "—"}
          hint={s.pass_needed ? `kerak ${s.pass_needed}%` : undefined}
          tone={
            s.pass_rate === null || s.pass_rate === undefined
              ? "plain"
              : s.pass_needed && s.pass_rate >= s.pass_needed
                ? "good"
                : s.pass_rate < 50
                  ? "bad"
                  : "plain"
          }
        />
        <Box
          label="Oylik test o'rtachasi"
          value={s.test_avg !== null && s.test_avg !== undefined
            ? `${s.test_avg}%` : "—"}
          hint={s.demote_below ? `chegara ${s.demote_below}%` : undefined}
          tone={
            s.test_avg !== null && s.test_avg !== undefined && s.demote_below
              ? s.test_avg < s.demote_below
                ? "bad"
                : "good"
              : "plain"
          }
        />
        <Box
          label="Guruhlari"
          value={`${s.groups}${s.max_groups ? ` / ${s.max_groups}` : ""}`}
        />
        <Box
          label="Sertifikat"
          value={s.cert || "—"}
          hint={s.qualification || undefined}
        />
      </div>

      {s.next_label ? (
        <div
          className={`rounded-xl border p-4 ${
            s.ready
              ? "border-emerald-200 bg-emerald-50"
              : "border-slate-200 bg-white"
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp
              size={14}
              className={s.ready ? "text-emerald-600" : "text-slate-400"}
            />
            <p className="text-sm font-medium text-slate-800">
              Keyingi daraja: {s.next_label}
            </p>
            <span className="text-xs text-slate-500">
              {formatSom(s.next_rate || 0)} / o'quvchi
            </span>
          </div>
          {s.ready ? (
            <p className="text-xs text-emerald-700">
              Hamma shart bajarilgan — tizim darajani o'zi ko'taradi.
            </p>
          ) : (
            <ul className="space-y-1.5 mt-1">
              {s.missing.map((m) => (
                <li
                  key={m.key}
                  className="flex items-start gap-2 text-xs text-slate-600"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                  {m.text}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-brand-200 bg-brand-50 p-4">
          <p className="text-sm text-brand-800">Eng yuqori darajada.</p>
        </div>
      )}

      <div className="mt-4">
        <p className="text-xs font-medium text-slate-700 mb-1.5">
          Ustozlikni boshlash sharti
        </p>
        <ul className="space-y-1">
          {d.entry.map((e) => (
            <li
              key={e.key}
              className="flex items-start gap-2 text-xs text-slate-500"
            >
              <Check size={11} className="text-slate-300 mt-0.5 shrink-0" />
              {e.text}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function StudyTab({
  d,
  teacherId,
  onDone,
}: {
  d: TeacherCareer;
  teacherId: number;
  onDone: () => void;
}) {
  const [busy, setBusy] = useState<number | null>(null);

  async function toggle(id: number, done: boolean) {
    setBusy(id);
    try {
      await api.post(`/teachers/${teacherId}/study/${id}`, { done });
      onDone();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-5">
      {d.study.map((st) => (
        <div key={st.key}>
          <div className="flex items-center gap-2 mb-2">
            <p className="text-sm font-medium text-slate-700">{st.label}</p>
            <span
              className={`text-xs ${
                st.done === st.total ? "text-emerald-600" : "text-slate-400"
              }`}
            >
              {st.done}/{st.total}
            </span>
            <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden max-w-[200px]">
              <div
                className={`h-full rounded-full ${
                  st.done === st.total ? "bg-emerald-500" : "bg-brand-400"
                }`}
                style={{
                  width: `${st.total ? (st.done / st.total) * 100 : 0}%`,
                }}
              />
            </div>
          </div>
          <div className="space-y-1">
            {st.items.map((i) => (
              <label
                key={i.id}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border cursor-pointer transition ${
                  i.done
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-slate-100 hover:border-slate-300"
                } ${busy === i.id ? "opacity-50" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={i.done}
                  disabled={busy === i.id}
                  onChange={(e) => toggle(i.id, e.target.checked)}
                />
                {i.kind === "book" ? (
                  <BookOpen size={13} className="text-slate-400 shrink-0" />
                ) : (
                  <Headphones size={13} className="text-slate-400 shrink-0" />
                )}
                <span
                  className={`text-sm flex-1 ${
                    i.done ? "text-emerald-800" : "text-slate-700"
                  }`}
                >
                  {i.title}
                </span>
                {i.done_at && (
                  <span className="text-xs text-slate-400">
                    {formatDate(i.done_at)}
                  </span>
                )}
              </label>
            ))}
          </div>
        </div>
      ))}
      <p className="text-xs text-slate-400">
        Kitob va podkastlar lavozim paytida o'qiladi. Teacherlik ro'yxati
        Junior'dan yuqoriga o'tishda, Head ro'yxati esa Metodistlikka
        o'tishda tekshiriladi.
      </p>
    </div>
  );
}

function HistoryTab({ d }: { d: TeacherCareer }) {
  if (d.history.length === 0)
    return <p className="text-sm text-slate-400 py-6">Hali o'zgarish yo'q.</p>;
  return (
    <div className="space-y-2">
      {d.history.map((h) => (
        <div
          key={h.id}
          className="rounded-lg border border-slate-100 p-3 flex flex-wrap items-start gap-2"
        >
          <Badge tone={h.tone}>{h.kind_label}</Badge>
          <div className="flex-1 min-w-[180px]">
            <p className="text-sm text-slate-800">
              {h.from_label && h.from_label !== h.to_label
                ? `${h.from_label} → ${h.to_label}`
                : h.to_label}
              {h.rate_after !== null &&
                h.rate_after !== undefined &&
                h.rate_before !== h.rate_after && (
                  <span className="text-xs text-slate-500">
                    {"  "}
                    {formatSom(h.rate_before || 0)} →{" "}
                    {formatSom(h.rate_after)}
                  </span>
                )}
            </p>
            <p className="text-xs text-slate-500">{h.reason}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500">
              {h.date ? formatDate(h.date) : "—"}
            </p>
            <p className="text-xs text-slate-400">{h.decided_by}</p>
          </div>
        </div>
      ))}
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
