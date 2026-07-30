import { useEffect, useState } from "react";
import { Percent, Plus, X, Check, Ban, ShieldCheck } from "lucide-react";
import {
  api, type StudentDiscounts, type Student, type User,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";

const STATUS_TONE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  active: "bg-emerald-100 text-emerald-700",
  expired: "bg-slate-100 text-slate-500",
  cancelled: "bg-slate-100 text-slate-500",
  rejected: "bg-red-100 text-red-700",
};

/**
 * O'quvchi kartasidagi chegirmalar. Chegirma - bu pul, shuning uchun
 * har birida sabab, muddat va TASDIQLAGAN SHAXS ko'rinib turadi.
 */
export function Discounts({ studentId }: { studentId: number }) {
  const [data, setData] = useState<StudentDiscounts | null>(null);
  const [form, setForm] = useState(false);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<StudentDiscounts>(`/students/${studentId}/discounts`)
      .then(setData)
      .finally(() => setLoading(false));
  }

  useEffect(load, [studentId]);

  if (loading) return <p className="text-sm text-slate-400 py-4">Yuklanmoqda...</p>;
  if (!data) return null;

  return (
    <div>
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-baseline gap-2">
            <Percent size={15} className="text-slate-400" />
            <span className="text-2xl font-semibold text-slate-900">
              {data.total_percent}%
            </span>
            <span className="text-sm text-slate-500">jami chegirma</span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {data.family_percent > 0
              ? `Shundan ${data.family_percent}% — oilaviy chegirma (tizim o'zi beradi)`
              : `Chegara ${data.max_percent}%`}
          </p>
        </div>
        <button
          onClick={() => setForm(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-brand-300 hover:text-brand-700"
        >
          <Plus size={14} /> Chegirma
        </button>
      </div>

      {data.family_percent > 0 && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-3 flex items-start gap-2">
          <ShieldCheck size={14} className="text-emerald-600 mt-0.5 shrink-0" />
          <p className="text-xs text-emerald-900">
            Oilaviy chegirma {data.family_percent}% — bir oiladan ikki va
            undan ortiq farzand o'qiyapti. Aka-uka ketsa chegirma o'zi
            yo'qoladi.
          </p>
        </div>
      )}

      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-4">
          Qo'shimcha chegirma yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {data.rows.map((d) => (
            <div
              key={d.id}
              className={`rounded-lg border p-3 ${
                d.alive
                  ? "bg-white border-slate-200"
                  : "bg-slate-50 border-slate-200"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-slate-800">
                      {d.kind_label}
                    </span>
                    <span className="text-sm font-semibold text-brand-700">
                      {d.percent
                        ? `${d.percent}%`
                        : d.amount
                          ? formatSom(d.amount)
                          : "—"}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_TONE[d.status] || STATUS_TONE.expired
                      }`}
                    >
                      {d.status_label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{d.reason}</p>
                  {d.referrer_name && (
                    <p className="text-xs text-slate-500 mt-0.5">
                      Olib kelgan: {d.referrer_name}
                    </p>
                  )}
                  {d.staff_name && (
                    <p className="text-xs text-slate-500 mt-0.5">
                      Xodim: {d.staff_name}
                    </p>
                  )}
                  <p className="text-xs text-slate-400 mt-1">
                    {d.start_date ? formatDate(d.start_date) : "—"} —{" "}
                    {d.end_date ? formatDate(d.end_date) : "muddatsiz"}
                    {d.approved_by && ` · tasdiqladi: ${d.approved_by}`}
                    {!d.approved_by &&
                      d.requested_by &&
                      ` · so'radi: ${d.requested_by}`}
                  </p>
                  {d.cancelled_reason && (
                    <p className="text-xs text-amber-700 mt-1">
                      {d.cancelled_reason}
                    </p>
                  )}
                </div>

                {data.can_approve && (
                  <div className="flex items-center gap-1 shrink-0">
                    {d.status === "pending" && (
                      <>
                        <button
                          onClick={async () => {
                            await api.post(`/discounts/${d.id}/approve`, {
                              approve: true,
                            });
                            load();
                          }}
                          title="Tasdiqlash"
                          className="p-1.5 rounded-md text-slate-400 hover:text-emerald-600 hover:bg-emerald-50"
                        >
                          <Check size={15} />
                        </button>
                        <button
                          onClick={async () => {
                            const r = prompt("Rad etish sababi?");
                            if (r === null) return;
                            await api.post(`/discounts/${d.id}/approve`, {
                              approve: false,
                              reason: r,
                            });
                            load();
                          }}
                          title="Rad etish"
                          className="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50"
                        >
                          <X size={15} />
                        </button>
                      </>
                    )}
                    {d.status === "active" && (
                      <button
                        onClick={async () => {
                          const r = prompt("Bekor qilish sababi?");
                          if (r === null) return;
                          await api.post(`/discounts/${d.id}/cancel`, {
                            approve: false,
                            reason: r,
                          });
                          load();
                        }}
                        title="Bekor qilish"
                        className="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50"
                      >
                        <Ban size={15} />
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {form && (
        <DiscountForm
          studentId={studentId}
          types={data.types}
          onClose={() => setForm(false)}
          onSaved={() => {
            setForm(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function DiscountForm({
  studentId,
  types,
  onClose,
  onSaved,
}: {
  studentId: number;
  types: { key: string; label: string; hint: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [kind, setKind] = useState(types[0]?.key ?? "individual");
  const [percent, setPercent] = useState("");
  const [reason, setReason] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [referrer, setReferrer] = useState("");
  const [staffId, setStaffId] = useState("");
  const [students, setStudents] = useState<Student[]>([]);
  const [staff, setStaff] = useState<User[]>([]);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (kind === "referral" && students.length === 0)
      api.get<Student[]>("/students").then(setStudents).catch(() => {});
    if (kind === "staff_child" && staff.length === 0)
      api.get<User[]>("/users").then(setStaff).catch(() => {});
  }, [kind]);

  const hint = types.find((t) => t.key === kind)?.hint;

  async function save() {
    if (!reason.trim()) {
      setErr("Sababni yozing — chegirma sababsiz berilmaydi");
      return;
    }
    if (!percent) {
      setErr("Chegirma foizini kiriting");
      return;
    }
    setSaving(true);
    try {
      await api.post("/discounts", {
        student_id: studentId,
        kind,
        percent: Number(percent),
        reason: reason.trim(),
        start_date: start || null,
        end_date: end || null,
        referrer_student_id: referrer ? Number(referrer) : null,
        staff_user_id: staffId ? Number(staffId) : null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-16 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Chegirma so'rovi</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Chegirmani rahbar tasdiqlaguncha amal qilmaydi
        </p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Turi</label>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
            >
              {types.map((t) => (
                <option key={t.key} value={t.key}>
                  {t.label}
                </option>
              ))}
            </select>
            {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
          </div>

          {kind === "referral" && (
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Qaysi do'sti olib keldi
              </label>
              <select
                value={referrer}
                onChange={(e) => setReferrer(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— tanlang —</option>
                {students
                  .filter((s) => s.id !== studentId)
                  .map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.full_name}
                    </option>
                  ))}
              </select>
            </div>
          )}

          {kind === "staff_child" && (
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Qaysi xodimning farzandi
              </label>
              <select
                value={staffId}
                onChange={(e) => setStaffId(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
              >
                <option value="">— tanlang —</option>
                {staff.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-amber-600 mt-1">
                Xodim ishdan ketsa chegirma avtomat bekor bo'ladi.
              </p>
            </div>
          )}

          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Chegirma foizi
            </label>
            <input
              type="number"
              value={percent}
              onChange={(e) => setPercent(e.target.value)}
              placeholder="10"
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-1">Sabab</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              placeholder="Nima uchun chegirma berilyapti"
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Boshlanishi
              </label>
              <input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">
                Tugashi
              </label>
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
          </div>
          <p className="text-xs text-slate-400">
            Tugash sanasi qo'yilsa — o'sha kundan keyin chegirma o'zi
            yo'qoladi.
          </p>

          <button
            onClick={save}
            disabled={saving}
            className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? "Saqlanmoqda..." : "So'rov yuborish"}
          </button>
        </div>
      </div>
    </div>
  );
}
