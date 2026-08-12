import { useEffect, useState } from "react";
import { Percent, Plus, X, Check, Ban, ShieldCheck } from "lucide-react";
import {
  api, type StudentDiscounts, type Student, type User,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { roleLabel } from "../lib/roles";

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
          {/* 2026-08-12, Jahongir: "10% chegirma berganimdan keyin jami
              chegirmada 0% turibdi". Chegirma bor edi, lekin boshlanish
              sanasi kelajakda edi — buni endi ochiq yozamiz. */}
          {(data.upcoming_percent ?? 0) > 0 && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2 py-1 mt-1.5 inline-block">
              Yana {data.upcoming_percent}% —{" "}
              {data.upcoming_from ? formatDate(data.upcoming_from) : ""} dan
              boshlanadi (hozircha hisobga olinmaydi)
            </p>
          )}
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
                  <p className="text-xs text-slate-600 mt-1">
                    {d.hidden && (
                      <span className="inline-block mr-1.5 px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 text-[10px] font-medium align-middle">
                        yashirin
                      </span>
                    )}
                    {d.reason}
                  </p>
                  {d.referrer_name && (
                    <p className="text-xs text-slate-500 mt-0.5">
                      {d.kind === "family" ? "Oila" : "Olib kelgan"}:{" "}
                      {d.referrer_name}
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


/**
 * Ism/familiyaning 3 harfini yozganda tavsiya chiqaradigan tanlagich.
 * 2026-08-12, Jahongir: "undan ism yoki familya 3ta harfini yozsa
 * qaysilar borligi tavsiya chiqsin". Ilgari bu yerda 2000+ o'quvchili
 * uzun <select> turardi - kerakli odamni topib bo'lmasdi.
 */
function SearchPick({
  label,
  placeholder,
  value,
  onPick,
  search,
  hint,
}: {
  label: string;
  placeholder: string;
  value: { id: number; full_name: string } | null;
  onPick: (v: { id: number; full_name: string } | null) => void;
  search: (q: string) => Promise<{ id: number; full_name: string; sub?: string }[]>;
  hint?: string;
}) {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<{ id: number; full_name: string; sub?: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    const needle = q.trim();
    if (needle.length < 3) {
      setRows([]);
      return;
    }
    let dead = false;
    setBusy(true);
    const t = setTimeout(() => {
      search(needle)
        .then((r) => { if (!dead) setRows(r.slice(0, 8)); })
        .catch(() => { if (!dead) setRows([]); })
        .finally(() => { if (!dead) setBusy(false); });
    }, 250);
    return () => { dead = true; clearTimeout(t); };
  }, [q]);

  if (value) {
    return (
      <div>
        <label className="block text-xs text-slate-500 mb-1">{label}</label>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-brand-300 bg-brand-50">
          <span className="text-sm text-slate-800 flex-1 truncate">
            {value.full_name}
          </span>
          <button
            onClick={() => { onPick(null); setQ(""); }}
            className="text-slate-400 hover:text-red-600"
            title="Boshqasini tanlash"
          >
            <X size={15} />
          </button>
        </div>
        {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
      </div>
    );
  }

  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      <input
        value={q}
        onChange={(e) => { setQ(e.target.value); setTouched(true); }}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
      />
      {touched && q.trim().length > 0 && q.trim().length < 3 && (
        <p className="text-xs text-slate-400 mt-1">
          Kamida 3 ta harf yozing…
        </p>
      )}
      {busy && <p className="text-xs text-slate-400 mt-1">Qidirilmoqda…</p>}
      {rows.length > 0 && (
        <div className="mt-1 border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-52 overflow-y-auto">
          {rows.map((r) => (
            <button
              key={r.id}
              onClick={() => { onPick({ id: r.id, full_name: r.full_name }); setRows([]); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-50"
            >
              <p className="text-sm text-slate-800">{r.full_name}</p>
              {r.sub && <p className="text-xs text-slate-400">{r.sub}</p>}
            </button>
          ))}
        </div>
      )}
      {!busy && q.trim().length >= 3 && rows.length === 0 && (
        <p className="text-xs text-slate-400 mt-1">Topilmadi</p>
      )}
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
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
  // "family_link" - haqiqiy chegirma turi emas, bu IKKI O'QUVCHINI
  // oila qilib bog'lash. Chegirmani keyin tizim o'zi hisoblaydi
  // (Jahongir, 2026-08-12: "oilaviy chegirma yo'q ekan").
  const ALL_KINDS = [
    {
      key: "family_link",
      label: "Oila (aka-uka / opa-singil)",
      hint: "Ikki o'quvchi bog'lanadi — 10% chegirma IKKALASIGA avtomat "
        + "hisoblanadi, ikkinchisini qayta bog'lash shart emas. "
        + "Familiya bir xil bo'lsa (Fozilov / Fozilova) darrov "
        + "bog'lanadi; familiya boshqa bo'lsa filial rahbari, "
        + "moliyachi va asoschiga tasdiq uchun so'rov ketadi.",
    },
    ...types,
  ];
  const [kind, setKind] = useState(ALL_KINDS[0]?.key ?? "individual");
  const [percent, setPercent] = useState("");
  const [reason, setReason] = useState("");
  // 2026-08-12: yashirin (individual) chegirma - o'quvchiga ko'rinmaydi
  const [hidden, setHidden] = useState(false);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [pickStudent, setPickStudent] =
    useState<{ id: number; full_name: string } | null>(null);
  const [pickStaff, setPickStaff] =
    useState<{ id: number; full_name: string } | null>(null);
  const [staff, setStaff] = useState<User[]>([]);
  const [err, setErr] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const isFamily = kind === "family_link";

  useEffect(() => {
    if (kind === "staff_child" && staff.length === 0)
      api.get<User[]>("/users").then(setStaff).catch(() => {});
  }, [kind]);

  const searchStudents = async (q: string) => {
    const r = await api.get<Student[]>(
      `/students?q=${encodeURIComponent(q)}`);
    return r
      .filter((x) => x.id !== studentId)
      .map((x) => ({
        id: x.id,
        full_name: x.full_name,
        sub: [x.group?.name, x.branch?.name].filter(Boolean).join(" · "),
      }));
  };

  const searchStaff = async (q: string) => {
    const needle = q.toLowerCase();
    return staff
      .filter((x) => (x.full_name || "").toLowerCase().includes(needle))
      .map((x) => ({ id: x.id, full_name: x.full_name,
                     sub: roleLabel(x.role) }));
  };

  const hint = ALL_KINDS.find((t) => t.key === kind)?.hint;

  async function save() {
    if (isFamily) {
      if (!pickStudent) {
        setErr("Qaysi o'quvchi bilan bir oila ekanini tanlang");
        return;
      }
      setSaving(true);
      try {
        const r = await api.post<{ message: string }>(
          `/students/${studentId}/family-link`,
          { sibling_id: pickStudent.id });
        setOkMsg(r.message);
        setTimeout(onSaved, r.message.length > 90 ? 3500 : 1500);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Xatolik");
        setSaving(false);
      }
      return;
    }
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
        referrer_student_id: pickStudent ? pickStudent.id : null,
        staff_user_id: pickStaff ? pickStaff.id : null,
        hidden,
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
          {isFamily
            ? "Oila bog'langach, chegirmani tizim o'zi hisoblaydi"
            : "Chegirmani rahbar tasdiqlaguncha amal qilmaydi"}
        </p>
        {okMsg && (
          <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2 mb-3">
            {okMsg}
          </p>
        )}
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
              onChange={(e) => {
                setKind(e.target.value);
                setErr("");
                setPickStudent(null);
                setPickStaff(null);
              }}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
            >
              {ALL_KINDS.map((t) => (
                <option key={t.key} value={t.key}>
                  {t.label}
                </option>
              ))}
            </select>
            {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
          </div>

          {isFamily && (
            <SearchPick
              label="Qaysi o'quvchi bilan bir oila"
              placeholder="Ism yoki familiyaning 3 harfi…"
              value={pickStudent}
              onPick={setPickStudent}
              search={searchStudents}
              hint="Familiya bir xil bo'lsa darrov bog'lanadi. Boshqa
                    familiya bo'lsa — tasdiqqa so'rov ketadi."
            />
          )}

          {kind === "referral" && (
            <SearchPick
              label="Qaysi do'sti olib keldi"
              placeholder="Ism yoki familiyaning 3 harfi…"
              value={pickStudent}
              onPick={setPickStudent}
              search={searchStudents}
            />
          )}

          {kind === "staff_child" && (
            <SearchPick
              label="Qaysi xodimning farzandi"
              placeholder="Ism yoki familiyaning 3 harfi…"
              value={pickStaff}
              onPick={setPickStaff}
              search={searchStaff}
              hint="Xodim ishdan ketsa chegirma avtomat bekor bo'ladi."
            />
          )}

          {!isFamily && (
          <>
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
            <p className="text-[11px] text-slate-400 mt-1">
              Xohlagan foizni yozishingiz mumkin — chegirma faqat
              TASDIQLANGANDAN keyin ishlaydi. 50% dan oshig'ini
              asoschi tasdiqlaydi.
            </p>
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
            <p className="text-[11px] text-slate-400 mt-1">
              Sabab va muddat o'quvchi/ota-ona portalida ko'rinadi
              (yashirin bo'lmasa).
            </p>
          </div>

          <label className="flex items-start gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={hidden}
              onChange={(e) => setHidden(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              Individual (yashirin) chegirma
              <span className="block text-[11px] text-slate-400">
                O'quvchi va ota-onaga KO'RINMAYDI — faqat xodimlar ko'radi
              </span>
            </span>
          </label>

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
            Boshlanish sanasi kelajakda bo'lsa — chegirma o'sha kungacha
            hisobga olinmaydi. Tugash sanasidan keyin o'zi yo'qoladi.
          </p>
          </>
          )}

          <button
            onClick={save}
            disabled={saving}
            className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {saving
              ? "Saqlanmoqda..."
              : isFamily ? "Oila qilib bog'lash" : "So'rov yuborish"}
          </button>
        </div>
      </div>
    </div>
  );
}
