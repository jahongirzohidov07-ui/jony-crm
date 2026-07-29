import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft, Plus, Trash2, Coins, Phone, X, Check,
} from "lucide-react";
import {
  api,
  type StudentDetail as StudentDetailType,
  type StudentExams,
  type StudentAttendance,
  type CoinEntry,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { FINANCE_ACCESS, TEACHING_STAFF, can } from "../lib/roles";
import { PAYMENT_METHODS, methodLabel } from "../lib/payments";
import { subjectLine, WEEKDAYS, parseDays } from "../lib/subjects";
import { examTitle, coinSourceLabel, gradeTone } from "../lib/exams";

const KIND_LABEL: Record<string, string> = {
  payment: "To'lov",
  charge: "Hisoblandi",
  discount: "Chegirma",
};

const STATUS_LABEL: Record<string, string> = {
  active: "Faol",
  trial: "Sinovda",
  frozen: "Muzlatilgan",
  archived: "Arxiv",
};

type Tab = "groups" | "payments" | "attendance" | "exams" | "coins" | "note";

const TABS: { key: Tab; label: string }[] = [
  { key: "groups", label: "Guruhlar" },
  { key: "payments", label: "To'lovlar" },
  { key: "attendance", label: "Davomat" },
  { key: "exams", label: "Imtihonlar" },
  { key: "coins", label: "Coin hisoboti" },
  { key: "note", label: "Eslatma" },
];

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 py-1.5">
      <span className="text-sm text-slate-500 shrink-0">{label}</span>
      <span className="text-sm text-slate-800 text-right">{value}</span>
    </div>
  );
}

// ------------------------------------------------------------ Chap panel
function ProfileCard({
  student,
  coins,
}: {
  student: StudentDetailType;
  coins: number;
}) {
  const initial = student.full_name.trim().charAt(0).toUpperCase();

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-lg font-semibold shrink-0">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-lg font-semibold text-slate-900 leading-tight">
            {student.full_name}
          </h1>
          <p className="text-xs text-slate-400">ID: {student.id}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <div
          className={`rounded-lg px-3 py-1.5 ${
            student.balance < 0
              ? "bg-red-50 text-red-700"
              : "bg-emerald-50 text-emerald-700"
          }`}
        >
          <span className="font-semibold">{formatSom(student.balance)}</span>
          <span className="text-xs ml-1 opacity-70">balans</span>
        </div>
        <div className="rounded-lg px-3 py-1.5 bg-amber-50 text-amber-700 flex items-center gap-1.5">
          <Coins size={14} />
          <span className="font-semibold">{coins}</span>
          <span className="text-xs opacity-70">coin</span>
        </div>
        <div
          className={`rounded-lg px-3 py-1.5 text-xs font-medium flex items-center ${
            student.status === "active"
              ? "bg-green-50 text-green-700"
              : student.status === "archived"
              ? "bg-slate-100 text-slate-500"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          {STATUS_LABEL[student.status] || student.status}
        </div>
      </div>

      <div className="divide-y divide-slate-100">
        <Row
          label="Telefon raqam"
          value={
            student.phone ? (
              <span className="flex items-center gap-1.5 justify-end">
                <Phone size={12} className="text-slate-400" />
                {student.phone}
              </span>
            ) : (
              <span className="text-slate-400">Mavjud emas</span>
            )
          }
        />
        <Row
          label="Ota-ona telefoni"
          value={
            student.parent_phone || <span className="text-slate-400">Mavjud emas</span>
          }
        />
        <Row
          label="Tug'ilgan sana"
          value={
            student.birth_date ? (
              formatDate(student.birth_date)
            ) : (
              <span className="text-slate-400">Mavjud emas</span>
            )
          }
        />
        <Row
          label="Qo'shilgan sana"
          value={student.enrolled_date ? formatDate(student.enrolled_date) : "—"}
        />
        {student.left_date && (
          <Row
            label="Ketgan sana"
            value={<span className="text-red-600">{formatDate(student.left_date)}</span>}
          />
        )}
        <Row label="Filial" value={student.branch?.name || "—"} />
      </div>

      <p className="text-xs text-slate-400 mt-4 pt-3 border-t border-slate-100">
        Ma'lumotlarni o'zgartirish uchun Talabalar ro'yxatidagi qalam
        tugmasidan foydalaning.
      </p>
    </div>
  );
}

// -------------------------------------------------------------- Guruhlar
function GroupsTab({ student }: { student: StudentDetailType }) {
  const g = student.group;
  if (!g)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        O'quvchi hech qaysi guruhga biriktirilmagan. Talabalar ro'yxatidan
        tahrirlab guruh tanlang.
      </p>
    );

  const days = parseDays(g.lesson_days);

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden max-w-lg">
      <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
        <Link
          to={`/groups/${g.id}`}
          className="font-semibold text-slate-900 hover:text-brand-700"
        >
          {g.name}
        </Link>
      </div>
      <div className="p-4 divide-y divide-slate-100">
        <Row
          label="O'qituvchi"
          value={<span className="text-brand-700">{g.teacher?.full_name || "—"}</span>}
        />
        {days.length > 0 && (
          <Row
            label="Dars kunlari"
            value={WEEKDAYS.filter((d) => days.includes(d.key))
              .map((d) => d.label)
              .join(", ")}
          />
        )}
        {g.lesson_time && <Row label="Vaqt" value={g.lesson_time} />}
        {subjectLine(g) && (
          <Row
            label="Kursi"
            value={
              <span className="bg-brand-50 text-brand-700 rounded-md px-2 py-0.5 text-xs font-medium">
                {subjectLine(g)}
              </span>
            }
          />
        )}
        <Row
          label="Holati"
          value={
            <span
              className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                student.status === "active"
                  ? "bg-green-50 text-green-700"
                  : "bg-amber-50 text-amber-700"
              }`}
            >
              {STATUS_LABEL[student.status] || student.status}
            </span>
          }
        />
        <Row
          label="Guruhga qo'shilgan sana"
          value={student.enrolled_date ? formatDate(student.enrolled_date) : "—"}
        />
        <Row
          label="Boshlanish sanasi"
          value={g.start_date ? formatDate(g.start_date) : "—"}
        />
        {g.room && <Row label="Xona" value={g.room} />}
        <Row label="Guruh narxi" value={formatSom(g.monthly_fee)} />
      </div>
      <Link
        to={`/groups/${g.id}`}
        className="block text-center py-2.5 text-sm font-medium text-brand-600 hover:bg-brand-50 border-t border-slate-200"
      >
        Davomat &amp; Baho →
      </Link>
    </div>
  );
}

// -------------------------------------------------------------- To'lovlar
function PaymentsTab({
  student,
  onChanged,
}: {
  student: StudentDetailType;
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const canEdit = can(user?.role, FINANCE_ACCESS);
  const [showForm, setShowForm] = useState(false);
  const [amount, setAmount] = useState("");
  const [kind, setKind] = useState("payment");
  const [method, setMethod] = useState("cash");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("To'g'ri summa kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post(`/students/${student.id}/payments`, {
        amount: value,
        kind,
        method: kind === "payment" ? method : null,
        note: note || null,
      });
      setAmount("");
      setNote("");
      setShowForm(false);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  async function remove(p: { id: number; amount: number }) {
    if (!confirm(`${formatSom(p.amount)} yozuvi o'chirilsinmi?`)) return;
    try {
      await api.delete(`/payments/${p.id}`);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-500">
          Balans:{" "}
          <span
            className={`font-semibold ${
              student.balance < 0 ? "text-red-600" : "text-emerald-600"
            }`}
          >
            {formatSom(student.balance)}
          </span>
        </p>
        {canEdit && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
          >
            {showForm ? <X size={16} /> : <Plus size={16} />}
            {showForm ? "Bekor qilish" : "Yangi yozuv"}
          </button>
        )}
      </div>

      {showForm && canEdit && (
        <div className="bg-slate-50 rounded-xl p-4 mb-4 space-y-3">
          <div className="flex flex-wrap gap-1.5">
            {(
              [
                ["payment", "To'lov"],
                ["charge", "Hisoblash"],
                ["discount", "Chegirma"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setKind(k)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                  kind === k
                    ? "bg-brand-50 border-brand-400 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {kind === "payment" && (
            <div className="flex flex-wrap gap-1.5">
              {PAYMENT_METHODS.map((m) => (
                <button
                  key={m.key}
                  onClick={() => setMethod(m.key)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                    method === m.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="number"
              className="w-40 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Summa"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              autoFocus
            />
            <input
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Izoh"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <button
              onClick={submit}
              disabled={saving}
              className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 text-sm font-medium disabled:opacity-60"
            >
              {saving ? "..." : "Saqlash"}
            </button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}

      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Sana</th>
              <th className="text-left px-4 py-3 font-medium">Turi</th>
              <th className="text-left px-4 py-3 font-medium">Usul</th>
              <th className="text-left px-4 py-3 font-medium">Izoh</th>
              <th className="text-right px-4 py-3 font-medium">Summa</th>
              {canEdit && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody>
            {student.payments.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                  Hali yozuv yo'q
                </td>
              </tr>
            )}
            {student.payments.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                <td className="px-4 py-3 text-slate-600">{formatDate(p.created_at)}</td>
                <td className="px-4 py-3 text-slate-600">
                  {KIND_LABEL[p.kind] || p.kind}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {methodLabel(p.method) || "—"}
                </td>
                <td className="px-4 py-3 text-slate-600">{p.note || "—"}</td>
                <td
                  className={`px-4 py-3 text-right font-medium ${
                    p.amount < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {p.amount > 0 ? "+" : ""}
                  {formatSom(p.amount)}
                </td>
                {canEdit && (
                  <td className="px-4 py-3 text-right">
                    {!p.period && (
                      <button
                        onClick={() => remove(p)}
                        className="text-slate-300 hover:text-red-500"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --------------------------------------------------------------- Davomat
function AttendanceTab({ studentId }: { studentId: number }) {
  const [data, setData] = useState<StudentAttendance | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<StudentAttendance>(`/students/${studentId}/attendance?months=6`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (!data || data.marked === 0)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        Davomat hali belgilanmagan. Guruh sahifasidagi "Davomat" jadvalidan
        belgilang.
      </p>
    );

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Davomat</p>
          <p
            className={`text-lg font-semibold ${
              data.percent >= 85
                ? "text-emerald-600"
                : data.percent >= 70
                ? "text-amber-600"
                : "text-red-600"
            }`}
          >
            {data.percent}%
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Keldi</p>
          <p className="text-lg font-semibold text-slate-900">{data.present}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Kelmadi</p>
          <p className="text-lg font-semibold text-red-600">{data.absent}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">O'rtacha baho</p>
          <p className="text-lg font-semibold text-slate-900">
            {data.avg_grade ?? "—"}
          </p>
        </div>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Sana</th>
              <th className="text-left px-4 py-3 font-medium">Davomat</th>
              <th className="text-right px-4 py-3 font-medium">Baho</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={`${r.date}-${i}`} className="border-t border-slate-100">
                <td className="px-4 py-2.5 text-slate-600">{formatDate(r.date)}</td>
                <td className="px-4 py-2.5">
                  {r.present ? (
                    <span className="inline-flex items-center gap-1.5 text-emerald-600">
                      <Check size={14} /> Keldi
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-red-500">
                      <X size={14} /> Kelmadi
                    </span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {r.grade ? (
                    <span
                      className={`inline-flex w-6 h-6 rounded items-center justify-center text-xs font-semibold ${gradeTone(
                        r.grade
                      )}`}
                    >
                      {r.grade}
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400 mt-3">Oxirgi 6 oy ko'rsatilgan.</p>
    </div>
  );
}

// ------------------------------------------------------------ Imtihonlar
function ExamsTab({ studentId }: { studentId: number }) {
  const [data, setData] = useState<StudentExams | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<StudentExams>(`/students/${studentId}/exams`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (!data || data.results.length === 0)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        Hali imtihon natijasi yo'q.
      </p>
    );

  return (
    <div>
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Imtihonlar</p>
          <p className="text-lg font-semibold text-slate-900">{data.count}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">O'rtacha natija</p>
          <p
            className={`text-lg font-semibold ${
              (data.avg_percent ?? 0) >= 85
                ? "text-emerald-600"
                : (data.avg_percent ?? 0) >= 60
                ? "text-amber-600"
                : "text-red-600"
            }`}
          >
            {data.avg_percent != null ? `${data.avg_percent}%` : "—"}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Imtihondan coin</p>
          <p className="text-lg font-semibold text-brand-700">{data.coins}</p>
        </div>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Test</th>
              <th className="text-left px-4 py-3 font-medium">Guruh</th>
              <th className="text-left px-4 py-3 font-medium">Sana</th>
              <th className="text-right px-4 py-3 font-medium">Natija</th>
              <th className="text-right px-4 py-3 font-medium">Foiz</th>
              <th className="text-right px-4 py-3 font-medium">Coin</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((r) => (
              <tr key={r.exam_id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium text-slate-800">
                  {examTitle(r)}
                </td>
                <td className="px-4 py-3 text-slate-500">{r.group || "—"}</td>
                <td className="px-4 py-3 text-slate-600">{formatDate(r.date)}</td>
                <td className="px-4 py-3 text-right text-slate-600">
                  {r.absent ? (
                    <span className="text-red-500 text-xs">kelmagan</span>
                  ) : r.band != null ? (
                    `${r.band} band`
                  ) : r.score != null ? (
                    `${r.score}/${r.max_score}`
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-800">
                  {r.percent != null ? `${r.percent}%` : "—"}
                </td>
                <td className="px-4 py-3 text-right text-brand-700">
                  {r.coins || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------- Coin
function CoinsTab({ studentId }: { studentId: number }) {
  const [rows, setRows] = useState<CoinEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<CoinEntry[]>(`/students/${studentId}/coins`)
      .then(setRows)
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;
  if (rows.length === 0)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        Hali coin yozuvi yo'q. Kunlik baho yoki imtihon natijasi kiritilishi
        bilan coin o'zi tushadi.
      </p>
    );

  const earned = rows.filter((r) => r.amount > 0).reduce((s, r) => s + r.amount, 0);
  const spent = rows.filter((r) => r.amount < 0).reduce((s, r) => s - r.amount, 0);

  return (
    <div>
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Yig'gan</p>
          <p className="text-lg font-semibold text-emerald-600">{earned}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Sarflagan</p>
          <p className="text-lg font-semibold text-slate-700">{spent}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Balans</p>
          <p className="text-lg font-semibold text-brand-700">{earned - spent}</p>
        </div>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Sana</th>
              <th className="text-left px-4 py-3 font-medium">Manba</th>
              <th className="text-left px-4 py-3 font-medium">Izoh</th>
              <th className="text-right px-4 py-3 font-medium">Coin</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-4 py-2.5 text-slate-600">
                  {formatDate(r.created_at)}
                </td>
                <td className="px-4 py-2.5 text-slate-500">
                  {coinSourceLabel(r.source)}
                </td>
                <td className="px-4 py-2.5 text-slate-600">{r.note || "—"}</td>
                <td
                  className={`px-4 py-2.5 text-right font-semibold ${
                    r.amount >= 0 ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {r.amount > 0 ? "+" : ""}
                  {r.amount}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// -------------------------------------------------------------- Eslatma
function NoteTab({
  student,
  onSaved,
}: {
  student: StudentDetailType;
  onSaved: () => void;
}) {
  const { user } = useAuth();
  const canEdit = can(user?.role, TEACHING_STAFF);
  const [text, setText] = useState(student.note ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await api.put(`/students/${student.id}`, { note: text || null });
      setSaved(true);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <textarea
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm min-h-[160px] disabled:bg-slate-50"
        value={text}
        disabled={!canEdit}
        onChange={(e) => {
          setText(e.target.value);
          setSaved(false);
        }}
        placeholder="O'quvchi haqida eslatma: nimaga e'tibor berish kerak, ota-ona bilan nima gaplashildi..."
      />
      {canEdit && (
        <div className="flex items-center gap-3 mt-3">
          <button
            onClick={save}
            disabled={saving}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
          {saved && <span className="text-sm text-emerald-600">Saqlandi</span>}
        </div>
      )}
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
    </div>
  );
}

// ------------------------------------------------------------------ Page
export default function StudentDetail() {
  const { id } = useParams();
  const [student, setStudent] = useState<StudentDetailType | null>(null);
  const [coins, setCoins] = useState(0);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("groups");

  function load() {
    api
      .get<StudentDetailType>(`/students/${id}`)
      .then(setStudent)
      .finally(() => setLoading(false));
    api
      .get<CoinEntry[]>(`/students/${id}/coins`)
      .then((rows) => setCoins(rows.reduce((s, r) => s + r.amount, 0)))
      .catch(() => {});
  }

  useEffect(load, [id]);

  if (loading)
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">Yuklanmoqda...</p>
      </div>
    );
  if (!student)
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">Talaba topilmadi</p>
      </div>
    );

  return (
    <div className="p-8">
      <Link
        to="/students"
        className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-4"
      >
        <ArrowLeft size={15} /> Talabalarga qaytish
      </Link>

      <div className="flex flex-col lg:flex-row gap-5 items-start">
        <div className="w-full lg:w-80 shrink-0">
          <ProfileCard student={student} coins={coins} />
        </div>

        <div className="flex-1 min-w-0 bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex gap-1 mb-5 border-b border-slate-200 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition whitespace-nowrap ${
                  tab === t.key
                    ? "border-brand-600 text-brand-700"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "groups" && <GroupsTab student={student} />}
          {tab === "payments" && <PaymentsTab student={student} onChanged={load} />}
          {tab === "attendance" && <AttendanceTab studentId={student.id} />}
          {tab === "exams" && <ExamsTab studentId={student.id} />}
          {tab === "coins" && <CoinsTab studentId={student.id} />}
          {tab === "note" && <NoteTab student={student} onSaved={load} />}
        </div>
      </div>
    </div>
  );
}
