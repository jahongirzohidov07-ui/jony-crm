import { useEffect, useState } from "react";
import {
  Plus, X, Info, Check, AlertTriangle,
} from "lucide-react";
import {
  api, type HrStructure, type Workforce,
  type StaffRequestList, type StaffRequestRow, type HrVacancyList,
  type HrVacancy, type Branch,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  orange: "bg-orange-100 text-orange-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
};

function Hint({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs text-slate-500 mb-4 flex items-start gap-1.5">
      <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
      {children}
    </p>
  );
}

function Card({ label, value, tone = "slate", sub }: {
  label: string; value: string | number; tone?: string; sub?: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${
        tone === "red" ? "text-red-600"
        : tone === "amber" ? "text-amber-600"
        : tone === "emerald" ? "text-emerald-600" : "text-slate-900"}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

/* ==================================================== Shtat rejasi */
export function WorkforceTab() {
  const [d, setD] = useState<Workforce | null>(null);
  const [st, setSt] = useState<HrStructure | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [adding, setAdding] = useState(false);

  const load = () => { api.get<Workforce>("/hr/workforce").then(setD); };
  useEffect(load, []);
  useEffect(() => {
    api.get<HrStructure>("/hr/structure").then(setSt).catch(() => {});
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
        <Card label="Tasdiqlangan shtat" value={d.totals.approved} />
        <Card label="Hozirgi xodim" value={d.totals.current} />
        <Card label="Bo'shliq" value={d.totals.gap}
              tone={d.totals.gap > 0 ? "amber" : "emerald"} />
        <Card label="Bo'sh guruh o'rni" value={d.free_group_slots}
              sub="ustozlar yana shuncha guruh oladi" />
        <Card label="Ortiqcha yuklangan" value={d.overloaded.length}
              tone={d.overloaded.length ? "red" : "emerald"} />
      </div>

      <Hint>{d.hint}</Hint>

      {/* Shtat jadvali */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-5">
        <div className="flex items-center gap-2 mb-3">
          <p className="text-sm font-medium text-slate-700">
            {d.year}-yil shtat rejasi
          </p>
          {d.can_edit && (
            <button onClick={() => setAdding(true)}
              className="ml-auto bg-brand-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium flex items-center gap-1">
              <Plus size={14} /> Qator
            </button>
          )}
        </div>
        {d.rows.length === 0 ? (
          <p className="text-sm text-slate-400 py-6 text-center">
            Reja hali tuzilmagan.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-slate-500 text-xs">
                <tr>
                  <th className="text-left py-2 font-medium">Filial</th>
                  <th className="text-left py-2 px-2 font-medium">Lavozim</th>
                  <th className="text-right py-2 px-2 font-medium">Shtat</th>
                  <th className="text-right py-2 px-2 font-medium">Bor</th>
                  <th className="text-right py-2 px-2 font-medium">Bo'shliq</th>
                  <th className="text-right py-2 px-2 font-medium">Byudjet</th>
                  <th className="text-left py-2 font-medium">Holat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {d.rows.map((r) => (
                  <tr key={r.id}>
                    <td className="py-2 text-slate-900">{r.branch}</td>
                    <td className="py-2 px-2 text-slate-600">
                      {r.position || "—"}
                    </td>
                    <td className="text-right py-2 px-2">{r.approved_headcount}</td>
                    <td className="text-right py-2 px-2">{r.current_headcount}</td>
                    <td className={`text-right py-2 px-2 font-medium ${
                      r.gap > 0 ? "text-amber-600"
                      : r.gap < 0 ? "text-red-600" : "text-slate-500"}`}>
                      {r.gap > 0 ? "+" : ""}{r.gap}
                      {r.over_staffed && (
                        <span className="text-[10px] block text-red-500">
                          ortiqcha
                        </span>
                      )}
                    </td>
                    <td className="text-right py-2 px-2 text-slate-600">
                      {r.budgeted_salary ? formatSom(r.budgeted_salary) : "—"}
                    </td>
                    <td className="py-2">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                        TONE[r.status_tone] || TONE.slate}`}>
                        {r.status_label}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Ustoz yuklamasi */}
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <p className="text-sm font-medium text-slate-700 mb-3">
          Ustozlar yuklamasi
        </p>
        <div className="flex gap-2 mb-3 flex-wrap">
          {d.load_summary.map((s) => (
            <span key={s.key}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium ${
                TONE[s.tone] || TONE.slate}`}>
              {s.label}: {s.count}
            </span>
          ))}
        </div>
        {d.teacher_load.length === 0 ? (
          <p className="text-sm text-slate-400 py-4 text-center">
            Ustoz yo'q.
          </p>
        ) : (
          <div className="space-y-2">
            {d.teacher_load.map((t) => (
              <div key={t.teacher_id} className="flex items-center gap-3">
                <span className="text-sm text-slate-900 w-40 truncate shrink-0">
                  {t.name}
                </span>
                <span className="text-xs text-slate-400 w-24 shrink-0 hidden md:block">
                  {t.grade_label}
                </span>
                <div className="flex-1 bg-slate-100 rounded h-5 overflow-hidden">
                  <div className={`h-full ${
                    t.tone === "red" ? "bg-red-400"
                    : t.tone === "amber" ? "bg-amber-400"
                    : t.tone === "sky" ? "bg-sky-300" : "bg-emerald-400"}`}
                    style={{ width: Math.min(t.percent, 100) + "%" }} />
                </div>
                <span className="text-xs text-slate-500 w-16 text-right shrink-0">
                  {t.groups}/{t.max_groups}
                </span>
                <span className={`text-[11px] px-1.5 py-0.5 rounded w-28 text-center shrink-0 ${
                  TONE[t.tone] || TONE.slate}`}>
                  {t.band_label}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {adding && st && (
        <PlanForm structure={st} branches={branches}
                  onClose={() => setAdding(false)}
                  onDone={() => { setAdding(false); load(); }} />
      )}
    </div>
  );
}

function PlanForm({ structure, branches, onClose, onDone }: {
  structure: HrStructure; branches: Branch[];
  onClose: () => void; onDone: () => void;
}) {
  const [f, setF] = useState({
    year: new Date().getFullYear(), branch_id: "", position_id: "",
    approved_headcount: "", planned_hires: "", budgeted_salary: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    setBusy(true); setErr("");
    try {
      const pos = structure.positions.find(
        (p) => String(p.id) === f.position_id);
      await api.post("/hr/workforce", {
        year: f.year,
        branch_id: f.branch_id ? Number(f.branch_id) : null,
        position_id: f.position_id ? Number(f.position_id) : null,
        department_id: pos?.department_id ?? null,
        approved_headcount: Number(f.approved_headcount || 0),
        planned_hires: Number(f.planned_hires || 0),
        budgeted_salary: f.budgeted_salary
          ? Number(f.budgeted_salary) : null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <div className="bg-white rounded-xl p-5 w-full max-w-md"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Shtat qatori</h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <div className="grid grid-cols-2 gap-2 mb-2">
          <input type="number" value={f.year}
                 onChange={(e) => setF({ ...f, year: Number(e.target.value) })}
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <select value={f.branch_id}
                  onChange={(e) => setF({ ...f, branch_id: e.target.value })}
                  className="border border-slate-300 rounded-lg px-2 py-2 text-sm">
            <option value="">Umumiy</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
        <select value={f.position_id}
                onChange={(e) => setF({ ...f, position_id: e.target.value })}
                className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2">
          <option value="">Lavozimni tanlang</option>
          {structure.positions.filter((p) => p.is_active).map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <div className="grid grid-cols-2 gap-2 mb-2">
          <input value={f.approved_headcount} type="number"
                 onChange={(e) => setF({ ...f, approved_headcount: e.target.value })}
                 placeholder="Tasdiqlangan shtat"
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <input value={f.planned_hires} type="number"
                 onChange={(e) => setF({ ...f, planned_hires: e.target.value })}
                 placeholder="Reja: ishga olish"
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <input value={f.budgeted_salary} type="number"
               onChange={(e) => setF({ ...f, budgeted_salary: e.target.value })}
               placeholder="Yillik maosh byudjeti (so'm)"
               className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3" />
        <p className="text-xs text-slate-500 mb-3">
          Hozirgi xodim soni va bo'shliq avtomat hisoblanadi — qo'lda
          kiritilmaydi.
        </p>
        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button onClick={save} disabled={busy}
                className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
          Saqlash
        </button>
      </div>
    </div>
  );
}

/* ================================================== Xodim so'rovlari */
export function StaffRequestsTab() {
  const [d, setD] = useState<StaffRequestList | null>(null);
  const [st, setSt] = useState<HrStructure | null>(null);
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState<StaffRequestRow | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    const q = status ? `?status=${status}` : "";
    api.get<StaffRequestList>("/hr/staff-requests" + q).then(setD);
  };
  useEffect(load, [status]);
  useEffect(() => {
    api.get<HrStructure>("/hr/structure").then(setSt).catch(() => {});
  }, []);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      {d.waiting_my_decision > 0 && (
        <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 flex items-center gap-2">
          <AlertTriangle size={15} className="shrink-0" />
          {d.waiting_my_decision} ta so'rov sizning qaroringizni kutmoqda.
        </p>
      )}

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button onClick={() => setStatus("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
            !status ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600"}`}>
          Hammasi
        </button>
        {d.statuses.filter((s) => s.count > 0).map((s) => (
          <button key={s.key}
            onClick={() => setStatus(s.key === status ? "" : s.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              status === s.key ? "bg-slate-800 text-white"
              : TONE[s.tone] || TONE.slate}`}>
            {s.label} {s.count}
          </button>
        ))}
        <button onClick={() => setAdding(true)}
          className="ml-auto bg-brand-600 text-white rounded-lg px-3 py-1.5 text-xs font-medium flex items-center gap-1">
          <Plus size={14} /> So'rov
        </button>
      </div>

      <Hint>{d.hint}</Hint>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          So'rov yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <button key={r.id} onClick={() => setOpen(r)}
              className="w-full text-left bg-white border border-slate-200 rounded-xl p-3.5 hover:border-slate-300">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-xs font-mono text-slate-400">
                  {r.public_id}
                </span>
                <span className="text-sm font-medium text-slate-900">
                  {r.position || "Lavozim tanlanmagan"}
                </span>
                <span className="text-xs text-slate-500">
                  {r.branch} · {r.headcount} ta
                </span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  TONE[r.priority_tone] || TONE.slate}`}>
                  {r.priority_label}
                </span>
                <span className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                  TONE[r.status_tone] || TONE.slate}`}>
                  {r.status_label}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {r.reason_label}
                {r.replacing ? ` · ${r.replacing} o'rniga` : ""}
                {r.requested_by ? ` · ${r.requested_by}` : ""}
                {r.days_left != null
                  ? ` · ${r.days_left} kundan keyin kerak` : ""}
              </p>
            </button>
          ))}
        </div>
      )}

      {open && (
        <RequestDrawer row={open} onClose={() => setOpen(null)}
                       onDone={() => { setOpen(null); load(); }} />
      )}
      {adding && st && (
        <RequestForm structure={st} meta={d}
                     onClose={() => setAdding(false)}
                     onDone={() => { setAdding(false); load(); }} />
      )}
    </div>
  );
}

function RequestDrawer({ row, onClose, onDone }: {
  row: StaffRequestRow; onClose: () => void; onDone: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [note, setNote] = useState("");
  const [rejecting, setRejecting] = useState(false);

  const act = async (path: string, body: object = {}) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/hr/staff-requests/${row.id}/${path}`, body);
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex justify-end"
         onClick={onClose}>
      <div className="bg-white w-full max-w-md h-full overflow-y-auto p-5"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-mono text-slate-400">{row.public_id}</p>
            <h3 className="text-lg font-semibold text-slate-900">
              {row.position}
            </h3>
            <p className="text-sm text-slate-500">
              {row.branch} · {row.headcount} ta · {row.employment_label}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>

        <span className={`inline-block px-2 py-1 rounded text-xs font-medium mb-4 ${
          TONE[row.status_tone] || TONE.slate}`}>
          {row.status_label}
        </span>

        {row.waiting_for && row.waiting_for.length > 0 && (
          <p className="text-sm text-slate-600 mb-4">
            Kutilmoqda: {row.waiting_for.join(", ")}
          </p>
        )}

        <div className="space-y-2 mb-4">
          {[
            ["Sabab", row.reason_label],
            ["Kim o'rniga", row.replacing],
            ["Qachondan kerak", row.needed_from
              ? formatDate(row.needed_from) : null],
            ["Maosh", row.salary_from
              ? `${formatSom(row.salary_from)} — ${
                  row.salary_to ? formatSom(row.salary_to) : "…"}` : null],
            ["Tajriba", row.experience_years
              ? `${row.experience_years} yil` : null],
            ["Ish grafigi", row.work_schedule],
            ["Talablar", row.requirements],
            ["Vazifalar", row.duties],
            ["So'ragan", row.requested_by],
          ].filter(([, v]) => v).map(([k, v]) => (
            <div key={k as string}>
              <p className="text-xs text-slate-500">{k}</p>
              <p className="text-sm text-slate-800">{v}</p>
            </div>
          ))}
        </div>

        {row.reject_reason && (
          <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
            Rad etish sababi: {row.reject_reason}
          </p>
        )}

        {row.approvals.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-slate-600 mb-2">
              Tasdiqlash tarixi
            </p>
            <div className="space-y-2">
              {row.approvals.map((a, i) => (
                <div key={i} className="flex gap-2.5">
                  <span className={`shrink-0 mt-0.5 w-5 h-5 rounded-full flex items-center justify-center ${
                    a.decision === "approved"
                      ? "bg-emerald-100 text-emerald-600"
                      : "bg-red-100 text-red-600"}`}>
                    {a.decision === "approved" ? <Check size={12} /> : <X size={12} />}
                  </span>
                  <div>
                    <p className="text-sm text-slate-800">
                      {a.step_label} — {a.by}
                    </p>
                    {a.note && (
                      <p className="text-xs text-slate-500">{a.note}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {err && <p className="text-sm text-red-600 mb-3">{err}</p>}

        {!row.locked && (
          <div className="space-y-2">
            {row.status === "draft" && (
              <button onClick={() => act("submit")} disabled={busy}
                className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
                Tasdiqlashga yuborish
              </button>
            )}
            {row.waiting_for && row.status !== "draft" && (
              <>
                <textarea value={note}
                          onChange={(e) => setNote(e.target.value)}
                          rows={2} placeholder="Izoh (ixtiyoriy)"
                          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
                <button onClick={() => act("approve", { note })} disabled={busy}
                  className="w-full bg-emerald-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
                  Tasdiqlash
                </button>
              </>
            )}
            {rejecting ? (
              <>
                <textarea value={note}
                          onChange={(e) => setNote(e.target.value)}
                          rows={2} placeholder="Rad etish sababi (majburiy)"
                          className="w-full border border-red-300 rounded-lg px-3 py-2 text-sm" />
                <button onClick={() => act("reject", { reason: note })}
                        disabled={busy || !note.trim()}
                  className="w-full bg-red-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
                  Rad etishni tasdiqlash
                </button>
              </>
            ) : (
              row.status !== "draft" && (
                <button onClick={() => setRejecting(true)}
                  className="w-full border border-red-300 text-red-700 rounded-lg py-2 text-sm font-medium">
                  Rad etish
                </button>
              )
            )}
          </div>
        )}

        {row.status === "approved" && (
          <button onClick={() => act("convert")} disabled={busy}
            className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40 mt-2">
            Vakansiya ochish
          </button>
        )}
        {row.status === "converted" && (
          <p className="text-sm text-teal-700 bg-teal-50 border border-teal-200 rounded-lg px-3 py-2">
            Bu so'rov bo'yicha vakansiya ochilgan.
          </p>
        )}
      </div>
    </div>
  );
}

function RequestForm({ structure, meta, onClose, onDone }: {
  structure: HrStructure; meta: StaffRequestList;
  onClose: () => void; onDone: () => void;
}) {
  const [f, setF] = useState({
    position_id: "", headcount: "1", reason: "", priority: "normal",
    employment_type: "full", needed_from: "", salary_from: "",
    salary_to: "", work_schedule: "", requirements: "", duties: "",
    replacing_user_id: "",
  });
  const [staff, setStaff] = useState<{ id: number; full_name: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get<{ id: number; full_name: string }[]>("/users")
      .then(setStaff).catch(() => {});
  }, []);

  const reason = meta.reasons.find((r) => r.key === f.reason);
  const needsReplacement = !!reason?.needs_replacement;

  const save = async () => {
    setBusy(true); setErr("");
    try {
      await api.post("/hr/staff-requests", {
        position_id: f.position_id ? Number(f.position_id) : null,
        department_id: structure.positions.find(
          (p) => String(p.id) === f.position_id)?.department_id ?? null,
        headcount: Number(f.headcount || 1),
        reason: f.reason || null,
        priority: f.priority,
        employment_type: f.employment_type,
        needed_from: f.needed_from || null,
        salary_from: f.salary_from ? Number(f.salary_from) : null,
        salary_to: f.salary_to ? Number(f.salary_to) : null,
        work_schedule: f.work_schedule || null,
        requirements: f.requirements || null,
        duties: f.duties || null,
        replacing_user_id: f.replacing_user_id
          ? Number(f.replacing_user_id) : null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <div className="bg-white rounded-xl p-5 w-full max-w-lg max-h-[90vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Yangi xodim so'rovi</h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>

        <select value={f.position_id}
                onChange={(e) => setF({ ...f, position_id: e.target.value })}
                className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2">
          <option value="">Lavozimni tanlang *</option>
          {structure.positions.filter((p) => p.is_active).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}{p.department ? ` — ${p.department}` : ""}
            </option>
          ))}
        </select>

        <div className="grid grid-cols-2 gap-2 mb-2">
          <input type="number" min={1} value={f.headcount}
                 onChange={(e) => setF({ ...f, headcount: e.target.value })}
                 placeholder="Nechta odam"
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <select value={f.priority}
                  onChange={(e) => setF({ ...f, priority: e.target.value })}
                  className="border border-slate-300 rounded-lg px-2 py-2 text-sm">
            {meta.priorities.map((p) => (
              <option key={p.key} value={p.key}>
                {p.label} ({p.sla_days} kun)
              </option>
            ))}
          </select>
        </div>

        <select value={f.reason}
                onChange={(e) => setF({ ...f, reason: e.target.value })}
                className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2">
          <option value="">Sababni tanlang *</option>
          {meta.reasons.map((r) => (
            <option key={r.key} value={r.key}>{r.label}</option>
          ))}
        </select>

        {needsReplacement && (
          <select value={f.replacing_user_id}
                  onChange={(e) => setF({ ...f, replacing_user_id: e.target.value })}
                  className="w-full border border-amber-300 rounded-lg px-2 py-2 text-sm mb-2">
            <option value="">Kimning o'rniga? *</option>
            {staff.map((s) => (
              <option key={s.id} value={s.id}>{s.full_name}</option>
            ))}
          </select>
        )}

        <div className="grid grid-cols-2 gap-2 mb-2">
          <select value={f.employment_type}
                  onChange={(e) => setF({ ...f, employment_type: e.target.value })}
                  className="border border-slate-300 rounded-lg px-2 py-2 text-sm">
            {meta.employment_types.map((t) => (
              <option key={t.key} value={t.key}>{t.label}</option>
            ))}
          </select>
          <input type="date" value={f.needed_from}
                 onChange={(e) => setF({ ...f, needed_from: e.target.value })}
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        </div>

        <div className="grid grid-cols-2 gap-2 mb-2">
          <input type="number" value={f.salary_from}
                 onChange={(e) => setF({ ...f, salary_from: e.target.value })}
                 placeholder="Maosh, dan"
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
          <input type="number" value={f.salary_to}
                 onChange={(e) => setF({ ...f, salary_to: e.target.value })}
                 placeholder="Maosh, gacha"
                 className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        </div>

        <input value={f.work_schedule}
               onChange={(e) => setF({ ...f, work_schedule: e.target.value })}
               placeholder="Ish grafigi"
               className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-2" />
        <textarea value={f.requirements}
                  onChange={(e) => setF({ ...f, requirements: e.target.value })}
                  rows={2} placeholder="Talablar"
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-2" />
        <textarea value={f.duties}
                  onChange={(e) => setF({ ...f, duties: e.target.value })}
                  rows={2} placeholder="Vazifalar"
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3" />

        <p className="text-xs text-slate-500 mb-3">
          Saqlangach so'rov qoralama bo'lib qoladi — tasdiqlash zanjiri
          "Yuborish" bosilgandan keyin boshlanadi.
        </p>
        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button onClick={save} disabled={busy || !f.position_id || !f.reason}
                className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
          Saqlash
        </button>
      </div>
    </div>
  );
}

/* ================================================ Vakansiyalar (HR) */
export function HrVacanciesTab() {
  const [d, setD] = useState<HrVacancyList | null>(null);
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState<HrVacancy | null>(null);

  const load = () => {
    const q = status ? `?status=${status}` : "";
    api.get<HrVacancyList>("/hr/vacancies" + q).then(setD);
  };
  useEffect(load, [status]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
        <Card label="Ochiq vakansiya" value={d.summary.open} />
        <Card label="Kritik" value={d.summary.critical}
              tone={d.summary.critical ? "red" : "slate"} />
        <Card label="Muddati o'tgan" value={d.summary.overdue}
              tone={d.summary.overdue ? "amber" : "emerald"} />
        <Card label="Bo'sh o'rin" value={d.summary.seats} />
        <Card label="O'rtacha ochiqlik"
              value={d.summary.avg_days_open + " kun"} />
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button onClick={() => setStatus("")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
            !status ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600"}`}>
          Hammasi
        </button>
        {d.statuses.filter((s) => s.count > 0).map((s) => (
          <button key={s.key}
            onClick={() => setStatus(s.key === status ? "" : s.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              status === s.key ? "bg-slate-800 text-white"
              : TONE[s.tone] || TONE.slate}`}>
            {s.label} {s.count}
          </button>
        ))}
      </div>

      <Hint>{d.hint}</Hint>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Vakansiya yo'q. Ular tasdiqlangan xodim so'rovidan ochiladi.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((v) => (
            <button key={v.id} onClick={() => setOpen(v)}
              className={`w-full text-left bg-white border rounded-xl p-3.5 hover:border-slate-300 ${
                v.overdue ? "border-amber-300 bg-amber-50/30"
                : "border-slate-200"}`}>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-xs font-mono text-slate-400">
                  {v.public_id}
                </span>
                <span className="text-sm font-medium text-slate-900">
                  {v.title}
                </span>
                <span className="text-xs text-slate-500">{v.branch}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  TONE[v.priority_tone] || TONE.slate}`}>
                  {v.priority_label}
                </span>
                {v.trial_required && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-100 text-violet-700">
                    sinov darsi kerak
                  </span>
                )}
                <span className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                  TONE[v.status_tone] || TONE.slate}`}>
                  {v.status_label}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {v.hired_count}/{v.headcount} to'ldirildi ·
                {" "}{v.applications} nomzod ·
                {" "}{v.days_open} kun ochiq
                {v.overdue && (
                  <span className="text-amber-700 font-medium">
                    {" "}· {v.sla_days} kundan oshdi
                  </span>
                )}
              </p>
            </button>
          ))}
        </div>
      )}

      {open && (
        <VacancyDrawer row={open} closeReasons={d.close_reasons}
                       canEdit={d.can_edit}
                       onClose={() => setOpen(null)}
                       onDone={() => { setOpen(null); load(); }} />
      )}
    </div>
  );
}

function VacancyDrawer({ row, closeReasons, canEdit, onClose, onDone }: {
  row: HrVacancy;
  closeReasons: { key: string; label: string }[];
  canEdit: boolean;
  onClose: () => void; onDone: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [closing, setClosing] = useState(false);
  const [reason, setReason] = useState("");

  const setStatus = async (status: string, close_reason?: string) => {
    setBusy(true); setErr("");
    try {
      await api.post(`/hr/vacancies/${row.id}/status`, {
        status, close_reason,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  const top = Math.max(...row.by_stage.map((s) => s.count), 1);

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex justify-end"
         onClick={onClose}>
      <div className="bg-white w-full max-w-md h-full overflow-y-auto p-5"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-mono text-slate-400">{row.public_id}</p>
            <h3 className="text-lg font-semibold text-slate-900">{row.title}</h3>
            <p className="text-sm text-slate-500">
              {row.branch} · {row.hired_count}/{row.headcount}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>

        <div className="flex gap-2 mb-4 flex-wrap">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            TONE[row.status_tone] || TONE.slate}`}>
            {row.status_label}
          </span>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            TONE[row.priority_tone] || TONE.slate}`}>
            {row.priority_label}
          </span>
          {row.overdue && (
            <span className="px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-700">
              {row.days_open} kun ochiq ({row.sla_days} dan oshdi)
            </span>
          )}
        </div>

        {/* Voronka */}
        <div className="bg-slate-50 rounded-xl p-3 mb-4">
          <p className="text-xs font-medium text-slate-600 mb-2">
            Nomzodlar voronkasi — {row.applications} ta
          </p>
          <div className="space-y-1.5">
            {row.by_stage.map((s) => (
              <div key={s.key} className="flex items-center gap-2 text-xs">
                <span className="w-32 shrink-0 text-slate-500">{s.label}</span>
                <div className="flex-1 bg-white rounded h-4 overflow-hidden">
                  <div className="bg-brand-400 h-full"
                       style={{ width: (s.count / top) * 100 + "%" }} />
                </div>
                <span className="w-6 text-right text-slate-600">{s.count}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Ishga olish {row.hire_rate}% · Taklifgacha {row.offer_rate}%
          </p>
        </div>

        <div className="space-y-2 mb-4">
          {[
            ["Lavozim", row.position],
            ["Bo'lim", row.department],
            ["Bandlik", row.employment_label],
            ["Ish grafigi", row.work_schedule],
            ["Maosh", row.salary_from
              ? `${formatSom(row.salary_from)} — ${
                  row.salary_to ? formatSom(row.salary_to) : "…"}` : null],
            ["Hiring manager", row.hiring_manager],
            ["Rekruter", row.recruiter],
            ["Ochilgan", formatDate(row.opened_on)],
            ["Mo'ljal", row.target_close ? formatDate(row.target_close) : null],
            ["Yopilgan", row.closed_at ? formatDate(row.closed_at) : null],
            ["Yopilish sababi", row.close_reason_label],
            ["Vazifalar", row.duties],
            ["Talablar", row.requirements],
          ].filter(([, v]) => v).map(([k, v]) => (
            <div key={k as string}>
              <p className="text-xs text-slate-500">{k}</p>
              <p className="text-sm text-slate-800">{v}</p>
            </div>
          ))}
        </div>

        {err && <p className="text-sm text-red-600 mb-3">{err}</p>}

        {canEdit && (
          closing ? (
            <div className="space-y-2">
              <select value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm">
                <option value="">Yopish sababi *</option>
                {closeReasons.map((r) => (
                  <option key={r.key} value={r.key}>{r.label}</option>
                ))}
              </select>
              <button onClick={() => setStatus("closed", reason)}
                      disabled={busy || !reason}
                className="w-full bg-red-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
                Yopishni tasdiqlash
              </button>
              <button onClick={() => setClosing(false)}
                className="w-full text-sm text-slate-500 py-1">
                Bekor qilish
              </button>
            </div>
          ) : row.is_open ? (
            <div className="space-y-2">
              <button onClick={() => setStatus("filled", "filled")}
                      disabled={busy}
                className="w-full bg-emerald-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
                To'ldirildi deb belgilash
              </button>
              <button onClick={() => setStatus("hold")} disabled={busy}
                className="w-full border border-slate-300 text-slate-700 rounded-lg py-2 text-sm font-medium">
                To'xtatib turish
              </button>
              <button onClick={() => setClosing(true)}
                className="w-full border border-red-300 text-red-700 rounded-lg py-2 text-sm font-medium">
                Yopish
              </button>
            </div>
          ) : (
            <button onClick={() => setStatus("open")} disabled={busy}
              className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40">
              Qayta ochish
            </button>
          )
        )}
      </div>
    </div>
  );
}
