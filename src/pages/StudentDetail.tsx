import { useEffect, useState } from "react";
import { PurchasesTab, RemindersTab } from "../components/StudentExtras";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Plus, Trash2, Coins, Phone, X, Check, Award, MessageCircle, Pencil, Printer } from "lucide-react";
import {
  api,
  type Student,
  type StudentDetail as StudentDetailType,
  type StudentExams,
  type StudentAttendance,
  type CoinEntry,
  type Branch,
  type Group,
  type StudentHistory,
  type StudentPricing,
} from "../lib/api";
import { formatSom, formatDate, formatTime, formatDateTime } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import {
  FINANCE_ACCESS, CASH_ACCESS, TEACHING_STAFF, PAYMENT_EDIT,
  REFUND_REQUEST, REFUND_APPROVE, FOUNDER, FINANCE_DIRECTOR, can,
  HR_MANAGER,
} from "../lib/roles";
import { XpCard } from "../components/XpCard";
import { PAYMENT_METHODS, methodLabel } from "../lib/payments";
import { subjectLine, WEEKDAYS, parseDays } from "../lib/subjects";
import { examTitle, coinSourceLabel, gradeTone } from "../lib/exams";
import {
  HISTORY_KINDS, CERTIFICATE_KINDS, TALK_CHANNELS,
} from "../lib/academic";
import { StudentPayButton } from "../components/QuickPayment";
import { printXReceipt, printCertificate } from "../lib/receipt";
import { Discounts } from "../components/Discounts";
import { formatPhone } from "../components/PhoneInput";
import { StudentModal } from "./Students";

const KIND_LABEL: Record<string, string> = {
  payment: "To'lov",
  charge: "Hisoblandi",
  discount: "Chegirma",
  refund: "Refund (qaytarildi)",
};

const STATUS_LABEL: Record<string, string> = {
  active: "Faol",
  trial: "Sinovda",
  frozen: "Muzlatilgan",
  archived: "Arxiv",
};

type Tab =
  | "groups" | "payments" | "price" | "attendance" | "exams"
  | "history" | "gamification" | "coins" | "note"
  | "purchases" | "reminders";

const TABS: { key: Tab; label: string }[] = [
  { key: "groups", label: "Guruhlar" },
  { key: "payments", label: "To'lovlar" },
  { key: "price", label: "Narx va chegirma" },
  { key: "attendance", label: "Davomat" },
  { key: "exams", label: "Imtihonlar" },
  { key: "history", label: "Tarix" },
  { key: "purchases", label: "Xaridlar" },
  { key: "reminders", label: "Eslatmalar" },
  { key: "gamification", label: "XP va liga" },
  { key: "coins", label: "Coin hisoboti" },
  { key: "note", label: "Izoh" },
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
  onEdit,
  onChanged,
}: {
  student: StudentDetailType;
  coins: number;
  onEdit: () => void;
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const canEdit = can(user?.role, [...TEACHING_STAFF, HR_MANAGER]);
  const canFinance = can(user?.role, FINANCE_ACCESS);
  // To'lovni ADMINISTRATOR ham qabul qiladi (server tomonda ham
  // CASH_ACCESS). Ilgari bu tugma FINANCE_ACCESS bilan yopilgan
  // edi va administrator o'quvchi kartasidan to'lov kirita
  // olmasdi - Jahongir, 2026-08-12: "o'quvchini profilida ham
  // qoshish uchun joy bolsin".
  const canCash = can(user?.role, CASH_ACCESS);
  const initial = student.full_name.trim().charAt(0).toUpperCase();

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start gap-3 mb-4">
        {/* O'quvchi ilovadan qo'ygan rasm shu yerda ham ko'rinadi
            (2026-08-10) - bo'lmasa bosh harfi */}
        <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-lg font-semibold shrink-0 overflow-hidden">
          {(student as any).photo ? (
            <img
              src={(student as any).photo}
              alt=""
              className="w-full h-full object-cover"
            />
          ) : (
            initial
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-lg font-semibold text-slate-900 leading-tight">
            {student.full_name}
          </h1>
          <p className="text-xs text-slate-400">
            ID: {student.id}
            {(student as any).middle_name
              ? ` · ${(student as any).last_name || ""} ${
                  (student as any).first_name || ""
                } ${(student as any).middle_name}`
              : ""}
          </p>
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
                {formatPhone(student.phone)}
              </span>
            ) : (
              <span className="text-slate-400">Mavjud emas</span>
            )
          }
        />
        <Row
          label="Ota-ona telefoni"
          value={
            formatPhone(student.parent_phone) || (
              <span className="text-slate-400">Mavjud emas</span>
            )
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

      <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100">
        {canCash && <StudentPayButton student={student} onDone={onChanged} />}
        {canEdit && (
          <button
            onClick={onEdit}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-brand-300"
          >
            <Pencil size={14} /> Tahrirlash
          </button>
        )}
      </div>
      {canFinance && <ParentTools student={student} />}
    </div>
  );
}

/** Ota-ona bilan aloqa vositalari: Telegram bog'lash kodi, ota-ona
 *  sahifasi havolasi, onlayn to'lov havolasi, shartnoma chop etish. */
function ParentTools({ student }: { student: StudentDetailType }) {
  const [tg, setTg] = useState<{
    enabled: boolean; linked?: boolean; code?: string; bot?: string | null;
  } | null>(null);
  const [pay, setPay] = useState<{
    enabled: boolean; links?: Record<string, string>;
  } | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get<{ enabled: boolean; linked?: boolean; code?: string;
      bot?: string | null }>(`/students/${student.id}/telegram`)
      .then(setTg).catch(() => {});
    api.get<{ enabled: boolean; links?: Record<string, string> }>(
      `/students/${student.id}/pay-link`)
      .then(setPay).catch(() => {});
  }, [student.id]);

  const copy = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setMsg(`${label} nusxalandi — ota-onaga yuboring`);
      setTimeout(() => setMsg(""), 3000);
    } catch {
      prompt("Nusxalash uchun:", text);
    }
  };

  const parentLink = async () => {
    const r = await api.get<{ url: string; expires_at: string }>(
      `/students/${student.id}/parent-link`);
    copy(r.url, "Ota-ona sahifasi havolasi");
  };

  const parentLinkRegenerate = async () => {
    if (!confirm(
      "Eski havola DARHOL ishlamay qoladi. Ota-onaga yangisini "
      + "yuborishga tayyormisiz?"
    )) return;
    const r = await api.post<{ url: string; expires_at: string }>(
      `/students/${student.id}/parent-link/regenerate`, {});
    copy(r.url, "Yangi ota-ona sahifasi havolasi");
  };

  const notifyDebt = async () => {
    const r = await api.post<{ sent: boolean; reason?: string }>(
      `/students/${student.id}/notify-debt`, {});
    setMsg(r.sent ? "Qarz eslatmasi Telegram'ga yuborildi ✓"
      : `Yuborilmadi: ${r.reason}`);
    setTimeout(() => setMsg(""), 3500);
  };

  return (
    <div className="mt-3 pt-3 border-t border-slate-100 space-y-2">
      <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">
        Ota-ona bilan aloqa
      </p>
      {tg?.enabled && (
        <div className="text-xs text-slate-600 bg-slate-50 rounded-lg px-2.5 py-2">
          {tg.linked ? (
            <span className="text-emerald-700">
              ✓ Telegram ulangan — davomat va to'lov xabarlari boradi
            </span>
          ) : (
            <span>
              Telegram: ota-ona{" "}
              <b>@{tg.bot || "bot"}</b> ga{" "}
              <button
                onClick={() => copy(`/start ${tg.code}`, "Bog'lash buyrug'i")}
                className="text-brand-600 underline"
              >
                /start {tg.code}
              </button>{" "}
              deb yozsin
            </span>
          )}
        </div>
      )}
      <div className="flex flex-wrap gap-1.5">
        <button onClick={parentLink}
          className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:border-brand-300">
          Ota-ona sahifasi
        </button>
        <button onClick={parentLinkRegenerate}
          title="Eski havolani bekor qilib, yangisini yaratadi (havola 180 kunda eskiradi)"
          className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:border-amber-300 hover:text-amber-700">
          Havolani yangilash
        </button>
        {pay?.enabled && pay.links && Object.keys(pay.links).length > 0 &&
          Object.entries(pay.links).map(([k, url]) => (
            <button key={k}
              onClick={() => copy(url, k === "payme" ? "Payme havolasi"
                : "Click havolasi")}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:border-brand-300">
              {k === "payme" ? "Payme havola" : "Click havola"}
            </button>
          ))}
        {tg?.enabled && tg.linked && student.balance < 0 && (
          <button onClick={notifyDebt}
            className="text-xs px-2.5 py-1.5 rounded-lg border border-amber-200 bg-amber-50 text-amber-700 hover:border-amber-300">
            Qarz eslatmasi yuborish
          </button>
        )}
        <button onClick={() => printContract(student)}
          className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:border-brand-300">
          Shartnoma chop etish
        </button>
      </div>
      {msg && <p className="text-xs text-emerald-600">{msg}</p>}
    </div>
  );
}

// -------------------------------------------------------------- Guruhlar
function GroupsTab({ student }: { student: StudentDetailType }) {
  const g = student.group;
  const [attOpen, setAttOpen] = useState(false);
  if (!g)
    return (
      <p className="text-sm text-slate-400 py-8 text-center">
        O'quvchi hech qaysi guruhga biriktirilmagan. Talabalar ro'yxatidan
        tahrirlab guruh tanlang.
      </p>
    );

  const days = parseDays(g.lesson_days);

  return (
    <>
      {/* O'NG TOMONDA alohida "Davomat" — bosilganda sahifadan
          chiqmasdan oylik yoqlama oynasi ochiladi (Jahongir,
          2026-08-12: "alohida davomat degan yozuv qoyib bosadigan
          qilib ber o'ng tomonda"). */}
      <div className="flex justify-end mb-3">
        <button
          onClick={() => setAttOpen(true)}
          className="text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          Davomat →
        </button>
      </div>
      {attOpen && (
        <AttendanceGridModal
          studentId={student.id}
          studentName={student.full_name}
          onClose={() => setAttOpen(false)}
        />
      )}
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
      {/* Bu tugma AVVALGIDEK guruh sahifasiga olib boradi (Jahongir,
          2026-08-12: "davomat va baho ezsa gruppaga otaversin"). */}
      <Link
        to={`/groups/${g.id}`}
        className="block text-center py-2.5 text-sm font-medium text-brand-600 hover:bg-brand-50 border-t border-slate-200"
      >
        Davomat &amp; Baho →
      </Link>
    </div>
    </>
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
  // Administrator "Yangi yozuv" formasini (hisoblash, chegirma...)
  // ko'rmaydi, lekin TO'LOV qabul qiladi - shuning uchun unga shu
  // tabda ham alohida to'lov tugmasi (Jahongir, 2026-08-12).
  const canCash = can(user?.role, CASH_ACCESS);
  // Summani tahrirlash — faqat asoschi, moliyachi, filial rahbari
  const canEditAmount = can(user?.role, PAYMENT_EDIT);
  const isFounder = user?.role === FOUNDER;
  // Refund: sotuv so'raydi, rahbar/moliyachi tasdiqlaydi
  const canAskRefund = can(user?.role, REFUND_REQUEST);
  const canApproveRefund = can(user?.role, REFUND_APPROVE);
  type Refund = {
    id: number; amount: number; reason: string; status: string;
    requested_by?: string | null; decided_by?: string | null;
  };
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [refundOpen, setRefundOpen] = useState(false);
  const [refAmount, setRefAmount] = useState("");
  const [refReason, setRefReason] = useState("");
  const loadRefunds = () => {
    if (!canAskRefund && !canApproveRefund) return;
    api
      .get<Refund[]>(`/refunds?student_id=${student.id}`)
      .then(setRefunds)
      .catch(() => setRefunds([]));
  };
  useEffect(loadRefunds, [student.id]);

  async function askRefund() {
    const v = Number(refAmount);
    if (!v || v <= 0 || !refReason.trim()) {
      alert("Summa va sababni kiriting");
      return;
    }
    try {
      await api.post("/refunds", {
        student_id: student.id, amount: v, reason: refReason.trim(),
      });
      setRefundOpen(false);
      setRefAmount(""); setRefReason("");
      loadRefunds();
      alert("Refund so'rovi yuborildi — filial rahbari yoki moliyachi tasdiqlashi kutilmoqda");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function decideRefund(r: Refund, ok: boolean) {
    if (!confirm(ok
      ? `${formatSom(r.amount)} refund TASDIQLANSINMI? Balansdan yechiladi.`
      : "So'rov rad etilsinmi?")) return;
    try {
      await api.post(`/refunds/${r.id}/${ok ? "approve" : "reject"}`, {});
      loadRefunds();
      onChanged();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }
  const [editId, setEditId] = useState<number | null>(null);
  const [editVal, setEditVal] = useState("");
  const [editVer, setEditVer] = useState<string>("");
  // To'lov usulini ham to'g'rilash mumkin (naqd <-> plastik) -
  // Jahongir: "adashib naqd kiritib yuboribmiz aslida u plastikdan"
  const [editMethod, setEditMethod] = useState<string>("");
  const saveAmount = async (pid: number) => {
    try {
      await api.put(`/payments/${pid}`, {
        amount: Number(editVal),
        ...(editMethod ? { method: editMethod } : {}),
        // Parallel tahrir himoyasi: men ochgan versiyani yuboraman —
        // boshqa xodim shu orada o'zgartirgan bo'lsa 409 keladi.
        expected_updated_at: editVer,
      });
      setEditId(null);
      onChanged();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
      onChanged();
    }
  };
  const [showForm, setShowForm] = useState(false);
  const [amount, setAmount] = useState("");
  const [kind, setKind] = useState("payment");
  const [method, setMethod] = useState("cash");
  const [note, setNote] = useState("");
  // ESKI SANA bilan kiritish — faqat asoschi va moliya direktori
  // (2026-08-12, Jahongir: "asoschiga va moliyachiga eski sana bilan
  // to'lov kirgizish funksiyasi qoshilsin, aynan o'quvchini profilida
  // tolovlar qismida yangi yozuv kiritish degan joyda").
  const canBackdate =
    user?.role === FOUNDER || user?.role === FINANCE_DIRECTOR;
  const [payDate, setPayDate] = useState("");
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
      const created = await api.post<{ id?: number }>(
        `/students/${student.id}/payments`,
        {
          amount: value,
          kind,
          method: kind === "payment" ? method : null,
          note: note || null,
          date: canBackdate && payDate ? payDate : null,
        }
      );
      if (kind === "payment" && confirm("Chek chiqarilsinmi?")) {
        printXReceipt({
          student: student.full_name,
          publicId: student.public_id,
          branch: student.branch?.name || null,
          amount: value,
          method,
          note: note || null,
          balance: student.balance + value,
          paymentId: created?.id ?? null,
        });
      }
      setAmount("");
      setNote("");
      setPayDate("");
      setShowForm(false);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  async function remove(p: {
    id: number; amount: number; kind?: string; period?: string | null;
  }) {
    const msg = p.period
      ? `${formatSom(p.amount)} — AVTOMATIK oylik yechimi o'chirilsinmi?\n\n` +
        "Diqqat: bu oy uchun bu o'quvchiga qayta hisoblanmaydi. Kerak " +
        "bo'lsa keyin qo'lda \"Hisoblash\" yozuvi kiritasiz."
      : `${formatSom(p.amount)} yozuvi o'chirilsinmi?`;
    if (!confirm(msg)) return;
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
        <div className="flex items-center gap-2">
          {canAskRefund && (
            <button
              onClick={() => setRefundOpen(!refundOpen)}
              className="flex items-center gap-1.5 rounded-lg border border-amber-300 text-amber-700 hover:bg-amber-50 px-3 py-2 text-sm font-medium"
            >
              Refund so'rovi
            </button>
          )}
          {!canEdit && canCash && (
            <StudentPayButton
              student={student as unknown as Student}
              onDone={onChanged}
            />
          )}
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
      </div>

      {refundOpen && canAskRefund && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4 space-y-2">
          <p className="text-sm font-medium text-amber-800">
            Pul qaytarish so'rovi — filial rahbari yoki moliyachi
            tasdiqlagach balansdan yechiladi
          </p>
          <div className="flex flex-wrap gap-2">
            <input
              type="number"
              value={refAmount}
              onChange={(e) => setRefAmount(e.target.value)}
              placeholder="Summa (so'm)"
              className="rounded-lg border border-amber-300 px-3 py-2 text-sm w-40"
            />
            <input
              value={refReason}
              onChange={(e) => setRefReason(e.target.value)}
              placeholder="Sabab (majburiy)"
              className="flex-1 min-w-[180px] rounded-lg border border-amber-300 px-3 py-2 text-sm"
            />
            <button
              onClick={askRefund}
              className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm hover:bg-amber-700"
            >
              Yuborish
            </button>
          </div>
        </div>
      )}

      {refunds.filter((r) => r.status === "pending").map((r) => (
        <div
          key={r.id}
          className="bg-amber-50 border border-amber-300 rounded-xl p-3 mb-3 flex flex-wrap items-center gap-2 text-sm"
        >
          <span className="font-medium text-amber-900">
            Refund so'rovi: {formatSom(r.amount)}
          </span>
          <span className="text-amber-700">— {r.reason}</span>
          <span className="text-xs text-amber-600">
            (so'ragan: {r.requested_by || "?"})
          </span>
          <div className="flex-1" />
          {canApproveRefund ? (
            <>
              <button
                onClick={() => decideRefund(r, true)}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs hover:bg-emerald-700"
              >
                Tasdiqlash
              </button>
              <button
                onClick={() => decideRefund(r, false)}
                className="px-3 py-1.5 rounded-lg bg-red-50 text-red-700 text-xs hover:bg-red-100"
              >
                Rad etish
              </button>
            </>
          ) : (
            <span className="text-xs text-amber-600">Tasdiq kutilmoqda…</span>
          )}
        </div>
      ))}

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

          {canBackdate && (
            <div className="flex flex-wrap items-center gap-2">
              <label className="text-xs text-slate-500">Sana</label>
              <input
                type="date"
                max={new Date().toISOString().slice(0, 10)}
                value={payDate}
                onChange={(e) => setPayDate(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
              />
              {payDate ? (
                <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2 py-1">
                  Yozuv {formatDate(payDate)} sanasi bilan kiritiladi
                  <button
                    onClick={() => setPayDate("")}
                    className="ml-2 text-slate-500 underline"
                  >
                    bugunga qaytar
                  </button>
                </span>
              ) : (
                <span className="text-xs text-slate-400">
                  Bo'sh qolsa — bugungi kun. O'tgan sana bilan kiritish
                  auditda qayd etiladi.
                </span>
              )}
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
              <th className="text-left px-4 py-3 font-medium">Kim kiritdi</th>
              <th className="text-left px-4 py-3 font-medium">Izoh</th>
              <th className="text-right px-4 py-3 font-medium">Summa</th>
              {canEdit && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody>
            {student.payments.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                  Hali yozuv yo'q
                </td>
              </tr>
            )}
            {student.payments.map((p) => (
              <tr key={p.id} className="border-t border-slate-100">
                {/* Sana + SOAT (sekundigacha) — Jahongir, 2026-08-12:
                    "kim va qaysi soatda kirgizganligi aniq ko'rinib
                    tursin sekundlarigacha". */}
                <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                  {formatDate(p.created_at)}
                  <span className="block text-[11px] text-slate-400">
                    {formatTime(p.created_at)}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {KIND_LABEL[p.kind] || p.kind}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {methodLabel(p.method) || "—"}
                </td>
                <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                  {p.created_by || "—"}
                  {p.entered_at &&
                    p.entered_at.slice(0, 10) !== p.created_at.slice(0, 10) && (
                      <span className="block text-[11px] text-amber-700">
                        kiritilgan: {formatDateTime(p.entered_at)}
                      </span>
                    )}
                </td>
                <td className="px-4 py-3 text-slate-600">{p.note || "—"}</td>
                <td
                  className={`px-4 py-3 text-right font-medium ${
                    p.amount < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {editId === p.id ? (
                    <span className="inline-flex items-center gap-1">
                      <input
                        type="number"
                        value={editVal}
                        onChange={(e) => setEditVal(e.target.value)}
                        className="w-28 border border-slate-300 rounded-lg px-2 py-1 text-sm text-right"
                        autoFocus
                      />
                      {p.kind === "payment" && (
                        <select
                          value={editMethod}
                          onChange={(e) => setEditMethod(e.target.value)}
                          className="border border-slate-300 rounded-lg px-1.5 py-1 text-xs bg-white"
                          title="To'lov usuli"
                        >
                          {PAYMENT_METHODS.map((m) => (
                            <option key={m.key} value={m.key}>
                              {m.label}
                            </option>
                          ))}
                        </select>
                      )}
                      <button
                        onClick={() => saveAmount(p.id)}
                        className="text-emerald-600 hover:text-emerald-700"
                        title="Saqlash"
                      >
                        <Check size={15} />
                      </button>
                      <button
                        onClick={() => setEditId(null)}
                        className="text-slate-400 hover:text-slate-600"
                        title="Bekor"
                      >
                        <X size={15} />
                      </button>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5">
                      {p.amount > 0 ? "+" : ""}
                      {formatSom(p.amount)}
                      {canEditAmount && (
                        <button
                          onClick={() => {
                            setEditId(p.id);
                            setEditVal(String(Math.abs(p.amount)));
                            setEditMethod(
                              (p as unknown as { method?: string })
                                .method || "cash");
                            setEditVer(
                              ((p as unknown as { updated_at?: string })
                                .updated_at) || "");
                          }}
                          className="text-slate-300 hover:text-brand-600"
                          title="Summani tahrirlash"
                        >
                          <Pencil size={13} />
                        </button>
                      )}
                      {p.kind === "payment" && (
                        <button
                          onClick={() => printReceipt(p, student)}
                          className="text-slate-300 hover:text-brand-600"
                          title="Chek chop etish"
                        >
                          <Printer size={13} />
                        </button>
                      )}
                    </span>
                  )}
                </td>
                {canEdit && (
                  <td className="px-4 py-3 text-right">
                    {(isFounder ||
                      (!p.period &&
                        !["payment", "refund"].includes(p.kind as string))) && (
                      <button
                        onClick={() => remove(p)}
                        title={
                          p.kind === "payment"
                            ? "To'lovni o'chirish (faqat asoschi)"
                            : "Yozuvni o'chirish"
                        }
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
  const canEdit = can(user?.role, [...TEACHING_STAFF, HR_MANAGER]);
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
  const [editOpen, setEditOpen] = useState(false);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
    api.get<Group[]>("/groups").then(setGroups).catch(() => setGroups([]));
  }, []);

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
          <ProfileCard
            student={student}
            coins={coins}
            onEdit={() => setEditOpen(true)}
            onChanged={load}
          />
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
          {tab === "price" && <PriceTab studentId={student.id} />}
          {tab === "history" && (
            <HistoryTab
              studentId={student.id}
              studentName={student.full_name}
              publicId={student.public_id}
            />
          )}
          {tab === "gamification" && <XpCard studentId={student.id} />}
          {tab === "coins" && <CoinsTab studentId={student.id} />}
          {tab === "note" && <NoteTab student={student} onSaved={load} />}
          {tab === "purchases" && <PurchasesTab studentId={student.id} />}
          {tab === "reminders" && <RemindersTab studentId={student.id} />}
        </div>
      </div>

      {editOpen && (
        <StudentModal
          groups={groups}
          branches={branches}
          defaultBranchId={student.branch?.id ?? null}
          initial={student}
          onClose={() => setEditOpen(false)}
          onSaved={() => {
            setEditOpen(false);
            load();
          }}
        />
      )}
    </div>
  );
}


// ------------------------------------------------- Narx va chegirma ----
function PriceTab({ studentId }: { studentId: number }) {
  const [data, setData] = useState<StudentPricing | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<StudentPricing>(`/students/${studentId}/pricing`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [studentId]);

  if (loading) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda...</p>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* Chegirmalar — sabab, muddat va tasdiqlagan shaxs bilan */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <Discounts studentId={studentId} />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        <div className="flex items-center justify-between px-4 py-3">
          <span className="text-sm text-slate-500">Guruh narxi</span>
          <span className="text-sm text-slate-800">{formatSom(data.base_fee)}</span>
        </div>
        {data.family_discount > 0 && (
          <div className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-slate-500">Oilaviy chegirma</span>
            <span className="text-sm text-emerald-600">
              −{data.family_discount}%
            </span>
          </div>
        )}
        {data.personal_discount > 0 && (
          <div className="flex items-center justify-between px-4 py-3">
            <span className="text-sm text-slate-500">Shaxsiy chegirma</span>
            <span className="text-sm text-emerald-600">
              −{data.personal_discount}%
            </span>
          </div>
        )}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-50">
          <span className="text-sm font-medium text-slate-700">To'lanadigan</span>
          <span className="text-base font-semibold text-slate-900">
            {formatSom(data.final_fee)}
          </span>
        </div>
      </div>

      <div
        className={`rounded-xl border p-4 ${
          data.family_discount > 0
            ? "bg-emerald-50 border-emerald-200"
            : "bg-slate-50 border-slate-200"
        }`}
      >
        <p className="text-sm text-slate-700">{data.explanation}</p>
      </div>

      {data.siblings.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Oiladagi boshqa farzandlar
          </p>
          <div className="space-y-1">
            {data.siblings.map((s) => (
              <div key={s.id} className="flex items-center justify-between py-1">
                <Link
                  to={`/students/${s.id}`}
                  className="text-sm text-slate-800 hover:text-brand-700"
                >
                  {s.full_name}
                </Link>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    s.status === "active"
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {STATUS_LABEL[s.status] || s.status}
                </span>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-3">
            Chegirma faqat kamida {data.family_min_children} ta farzand FAOL
            bo'lganda amal qiladi va biri to'xtaganda o'zidan yo'qoladi.
          </p>
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------- Tarix tab ----
type CertRow = {
  id: number; kind: string; level?: string | null;
  score?: number | null; date?: string | null; note?: string | null;
};

function HistoryTab({ studentId, studentName, publicId }: {
  studentId: number; studentName: string; publicId?: string | null;
}) {
  const { user } = useAuth();
  const [data, setData] = useState<StudentHistory | null>(null);
  const [certs, setCerts] = useState<CertRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [talkOpen, setTalkOpen] = useState(false);
  const [certOpen, setCertOpen] = useState(false);

  function load() {
    setLoading(true);
    api
      .get<CertRow[]>(`/students/${studentId}/certificates`)
      .then(setCerts)
      .catch(() => setCerts([]));
    api
      .get<StudentHistory>(`/students/${studentId}/history`)
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, [studentId]);

  if (loading) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda...</p>;
  if (!data) return null;

  const s = data.summary;
  const stats: { label: string; value: string; tone?: string }[] = [
    { label: "Guruhlar", value: String(s.group_count) },
    { label: "Guruh almashtirgan", value: String(s.group_changes),
      tone: s.group_changes >= 2 ? "text-amber-600" : undefined },
    { label: "Dars qoldirgan", value: String(s.absences),
      tone: s.absences > 0 ? "text-red-600" : undefined },
    { label: "Davomat",
      value: s.attendance_percent !== null ? `${s.attendance_percent}%` : "—" },
    { label: "Shikoyatlar", value: String(s.complaints),
      tone: s.complaints > 0 ? "text-red-600" : undefined },
    { label: "Ota-ona suhbati", value: String(s.talks) },
    { label: "Muzlatish", value: String(s.freezes) },
    { label: "Qayta tiklanish", value: String(s.returns) },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
        {stats.map((x) => (
          <div key={x.label} className="bg-white rounded-lg border border-slate-200 p-3">
            <p className="text-xs text-slate-500">{x.label}</p>
            <p className={`text-base font-semibold ${x.tone || "text-slate-900"}`}>
              {x.value}
            </p>
          </div>
        ))}
      </div>

      {certs.length > 0 && (
        <div className="bg-white rounded-xl border border-amber-200 p-4 mb-4">
          <p className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-1.5">
            <Award size={15} /> Sertifikatlar
          </p>
          <div className="flex flex-wrap gap-2">
            {certs.map((c) => (
              <div
                key={c.id}
                className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm"
              >
                <span className="font-medium text-slate-800">
                  {c.level || c.kind}
                </span>
                {c.score != null && (
                  <span className="text-xs text-amber-700">{c.score}%</span>
                )}
                <button
                  onClick={() =>
                    printCertificate({
                      student: studentName,
                      level: c.level || c.kind,
                      score: c.score,
                      date: c.date,
                      publicId,
                    })
                  }
                  className="text-xs px-2 py-0.5 rounded-md bg-amber-600 text-white hover:bg-amber-700"
                  title="Sertifikatni yuklab olish / chop etish"
                >
                  Yuklab olish
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {(s.teachers.length > 0 || s.groups.length > 0) && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4 text-sm">
          {s.groups.length > 0 && (
            <p className="text-slate-600">
              <span className="text-slate-500">O'qigan guruhlari:</span>{" "}
              {s.groups.join(", ")}
            </p>
          )}
          {s.teachers.length > 0 && (
            <p className="text-slate-600 mt-1">
              <span className="text-slate-500">Ustozlari:</span>{" "}
              {s.teachers.join(", ")}
            </p>
          )}
        </div>
      )}

      <div className="flex items-center gap-2 mb-3">
        <p className="text-sm font-medium text-slate-700">Voqealar tarixi</p>
        <div className="flex-1" />
        {can(user?.role, TEACHING_STAFF) && (
          <>
            <button
              onClick={() => setTalkOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
            >
              <MessageCircle size={13} /> Suhbat qo'shish
            </button>
            <button
              onClick={() => setCertOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
            >
              <Award size={13} /> Sertifikat
            </button>
          </>
        )}
      </div>

      {data.timeline.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Hali voqea yo'q
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
          {data.timeline.map((e, i) => {
            const K = HISTORY_KINDS[e.kind] || {
              label: e.kind, dot: "bg-slate-300",
            };
            return (
              <div key={i} className="flex items-start gap-3 px-4 py-3">
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${K.dot}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800">{e.title}</p>
                  {e.detail && (
                    <p className="text-xs text-slate-500 mt-0.5">{e.detail}</p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-slate-500">
                    {e.date ? formatDate(e.date.slice(0, 10)) : "—"}
                  </p>
                  {e.by && <p className="text-xs text-slate-400">{e.by}</p>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {data.absent_dates.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mt-4">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Qoldirilgan darslar
          </p>
          <div className="flex flex-wrap gap-1.5">
            {data.absent_dates.map((d) => (
              <span
                key={d}
                className="text-xs px-2 py-0.5 rounded-md bg-red-50 text-red-700"
              >
                {formatDate(d)}
              </span>
            ))}
          </div>
        </div>
      )}

      {talkOpen && (
        <TalkModal
          studentId={studentId}
          onClose={() => setTalkOpen(false)}
          onSaved={() => {
            setTalkOpen(false);
            load();
          }}
        />
      )}
      {certOpen && (
        <CertModal
          studentId={studentId}
          onClose={() => setCertOpen(false)}
          onSaved={() => {
            setCertOpen(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function TalkModal({
  studentId, onClose, onSaved,
}: {
  studentId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [topic, setTopic] = useState("");
  const [summary, setSummary] = useState("");
  const [channel, setChannel] = useState("phone");
  const [err, setErr] = useState("");

  async function save() {
    if (!topic.trim()) {
      setErr("Mavzuni yozing");
      return;
    }
    try {
      await api.post(`/students/${studentId}/talks`, {
        topic: topic.trim(), summary: summary || null, channel,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800">Ota-ona bilan suhbat</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Nima haqida gaplashildi?"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
          <select
            value={channel}
            onChange={(e) => setChannel(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          >
            {TALK_CHANNELS.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Suhbat mazmuni va kelishuv"
            rows={3}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
        </div>
        <div className="flex gap-2 mt-5">
          <button
            onClick={save}
            className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            Saqlash
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor
          </button>
        </div>
      </div>
    </div>
  );
}

function CertModal({
  studentId, onClose, onSaved,
}: {
  studentId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [kind, setKind] = useState("ielts");
  const [level, setLevel] = useState("");
  const [err, setErr] = useState("");

  async function save() {
    try {
      await api.post(`/students/${studentId}/certificates`, {
        kind, level: level || null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800">Sertifikat qo'shish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-3">
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          >
            {CERTIFICATE_KINDS.map((k) => (
              <option key={k.key} value={k.key}>
                {k.label}
              </option>
            ))}
          </select>
          <input
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            placeholder="Daraja yoki ball (masalan: 7.0, B2)"
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
          />
        </div>
        <div className="flex gap-2 mt-5">
          <button
            onClick={save}
            className="flex-1 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
          >
            Saqlash
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor
          </button>
        </div>
      </div>
    </div>
  );
}

/* ==================== CHOP ETISH: chek va shartnoma ==================== */
function openPrint(html: string) {
  const w = window.open("", "_blank", "width=480,height=640");
  if (!w) { alert("Brauzer yangi oynani blokladi"); return; }
  w.document.write(html);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 300);
}

const P_STYLE = `<style>
  body{font-family:Arial,sans-serif;color:#111;margin:24px;font-size:13px}
  h2{margin:0 0 2px;font-size:16px} .m{color:#666;font-size:11px}
  table{width:100%;border-collapse:collapse;margin:12px 0}
  td{padding:5px 0;vertical-align:top}
  td:last-child{text-align:right;font-weight:600}
  .line{border-top:1px dashed #999;margin:10px 0}
  .sig{margin-top:28px;display:flex;justify-content:space-between;font-size:12px}
  .sig span{border-top:1px solid #333;padding-top:4px;width:44%;text-align:center}
  .big{font-size:18px;font-weight:700}
  ol{padding-left:18px} li{margin-bottom:5px}
</style>`;

function printReceipt(p: { id: number; public_id?: string | null;
  amount: number; created_at: string; note?: string | null;
  created_by?: string | null; method?: string | null },
  student: StudentDetailType) {
  const d = new Date(p.created_at);
  openPrint(`<!doctype html><html><head><meta charset="utf-8">
  <title>Chek</title>${P_STYLE}</head><body>
  <h2>Jony Academy</h2>
  <p class="m">To'lov cheki № ${p.public_id || p.id} ·
    ${d.toLocaleDateString("uz-UZ")} ${d.toLocaleTimeString("uz-UZ",
      { hour: "2-digit", minute: "2-digit" })}</p>
  <div class="line"></div>
  <table>
    <tr><td>O'quvchi</td><td>${student.full_name}</td></tr>
    <tr><td>Guruh</td><td>${student.group?.name || "—"}</td></tr>
    <tr><td>Izoh</td><td>${p.note || "oylik to'lov"}</td></tr>
    <tr><td>Summa</td><td class="big">${formatSom(p.amount)}</td></tr>
    <tr><td>Qabul qildi</td><td>${p.created_by || ""}</td></tr>
  </table>
  <div class="line"></div>
  <p class="m">Rahmat! Savollar bo'lsa administratorga murojaat qiling.</p>
  </body></html>`);
}

function printContract(student: StudentDetailType) {
  const g = student.group;
  const today = new Date().toLocaleDateString("uz-UZ");
  openPrint(`<!doctype html><html><head><meta charset="utf-8">
  <title>Shartnoma</title>${P_STYLE}</head><body>
  <h2>Jony Academy — o'quv xizmatlari shartnomasi</h2>
  <p class="m">Bekobod · ${today}</p>
  <table>
    <tr><td>O'quvchi</td><td>${student.full_name}</td></tr>
    <tr><td>ID</td><td>${student.public_id || student.id}</td></tr>
    <tr><td>Telefon</td><td>${student.phone || "____________"}</td></tr>
    <tr><td>Ota-ona telefoni</td><td>${student.parent_phone || "____________"}</td></tr>
    <tr><td>Manzil</td><td>${student.address || "____________"}</td></tr>
    <tr><td>Guruh</td><td>${g?.name || "____________"}</td></tr>
    <tr><td>Dars vaqti</td><td>${g?.lesson_time || "____________"}</td></tr>
    <tr><td>Oylik to'lov</td><td>${g ? formatSom(g.monthly_fee) : "____________"}</td></tr>
  </table>
  <div class="line"></div>
  <ol>
    <li>O'quv markaz o'quvchini belgilangan jadval asosida sifatli
        o'qitish majburiyatini oladi.</li>
    <li>Oylik to'lov har oyning boshida to'lanadi. Darsga kelmaslik
        to'lovdan ozod qilmaydi (muzlatish holati bundan mustasno).</li>
    <li>O'quvchi 3 ta darsga sababsiz kelmasa, o'qish avtomatik
        muzlatiladi va ota-ona bilan bog'laniladi.</li>
    <li>Ota-ona farzandining davomati va natijalari haqida xabardor
        qilib boriladi.</li>
    <li>Tomonlar o'zaro hurmat va hamkorlik tamoyillariga amal qiladi.</li>
  </ol>
  <div class="sig">
    <span>O'quv markaz (imzo)</span>
    <span>Ota-ona (imzo)</span>
  </div>
  </body></html>`);
}


// --------------------------------------------- Oylik davomat panjarasi
/**
 * O'quvchi kartasidan chiqmasdan ochiladigan davomat oynasi
 * (2026-08-12, Jahongir: "davomat degan joyga bossa o'quvchi
 * oynasidan chiqmagan holda oyna ochilsa va yoqlamalari korinib
 * tursa, muzlatilganlarniki ham"). Yil + oy tanlanadi, har bir
 * guruh alohida qator: keldi (✓), kelmadi (✕), kechikdi, hali
 * belgilanmagan (bo'sh) va o'sha kungi baho.
 */
const ATT_MONTHS = [
  "Yan", "Fev", "Mar", "Apr", "May", "Iyun",
  "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek",
];

type AttGridDay = {
  date: string;
  state: "present" | "absent" | "late" | "none";
  grade?: number | null;
  homework_label?: string | null;
};
type AttGridRow = {
  group_id: number;
  group: string;
  teacher?: string | null;
  current: boolean;
  days: AttGridDay[];
  present: number;
  absent: number;
  late: number;
  unmarked: number;
  percent: number | null;
};
type AttGrid = {
  year: number;
  month: number;
  student: string;
  status: string;
  groups: AttGridRow[];
};

function AttendanceGridModal({
  studentId,
  studentName,
  onClose,
}: {
  studentId: number;
  studentName: string;
  onClose: () => void;
}) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [d, setD] = useState<AttGrid | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<AttGrid>(
        `/students/${studentId}/attendance-grid?year=${year}&month=${month}`)
      .then(setD)
      .catch(() => setD(null))
      .finally(() => setLoading(false));
  }, [studentId, year, month]);

  const years = [now.getFullYear(), now.getFullYear() - 1,
                 now.getFullYear() - 2];

  const cell = (day: AttGridDay) => {
    if (day.state === "present")
      return <span className="text-emerald-600 font-semibold">✓</span>;
    if (day.state === "late")
      return <span className="text-amber-600 font-semibold" title="Kechikdi">
        ⏱
      </span>;
    if (day.state === "absent")
      return <span className="text-red-600 font-semibold">✕</span>;
    return <span className="text-slate-300">—</span>;
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex justify-end"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-4xl h-full overflow-y-auto p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              {studentName} — guruhlardagi davomati
            </h3>
            <p className="text-xs text-slate-500">
              Muzlatilgan va arxivdagi o'quvchilarning tarixi ham
              ko'rinadi.
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X size={20} />
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 mb-4">
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white mr-1"
          >
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          {ATT_MONTHS.map((m, i) => (
            <button
              key={m}
              onClick={() => setMonth(i + 1)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                month === i + 1
                  ? "bg-brand-600 border-brand-600 text-white"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        {loading ? (
          <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>
        ) : !d || d.groups.length === 0 ? (
          <p className="text-sm text-slate-400 py-8">
            Bu oyda dars yo'q.
          </p>
        ) : (
          <div className="space-y-5">
            {d.groups.map((row) => (
              <div key={row.group_id}
                   className="border border-slate-200 rounded-xl overflow-hidden">
                <div className="flex flex-wrap items-center gap-2 px-4 py-2.5 bg-slate-50 border-b border-slate-200">
                  <span className="text-sm font-medium text-slate-800">
                    {row.group}
                  </span>
                  {row.teacher && (
                    <span className="text-xs text-slate-500">
                      · {row.teacher}
                    </span>
                  )}
                  {!row.current && (
                    <span className="text-[11px] bg-slate-200 text-slate-600 rounded px-1.5 py-0.5">
                      eski guruh
                    </span>
                  )}
                  <span className="flex-1" />
                  <span className="text-xs text-slate-500">
                    Keldi {row.present} · Kelmadi {row.absent}
                    {row.late ? ` · Kechikdi ${row.late}` : ""}
                    {row.percent !== null ? ` · ${row.percent}%` : ""}
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="text-sm">
                    <thead>
                      <tr>
                        {row.days.map((day) => (
                          <th key={day.date}
                              className="px-3 py-2 text-xs font-medium text-slate-500 whitespace-nowrap border-b border-slate-100">
                            {day.date.slice(8, 10)}.{day.date.slice(5, 7)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        {row.days.map((day) => (
                          <td key={day.date}
                              className="px-3 py-2 text-center border-b border-slate-100">
                            {cell(day)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        {row.days.map((day) => (
                          <td key={day.date}
                              className="px-3 py-1.5 text-center text-xs text-slate-600">
                            {day.grade ?? ""}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
            <p className="text-xs text-slate-400">
              ✓ keldi · ✕ kelmadi · ⏱ kechikdi · — yoqlama qo'yilmagan.
              Pastki qator — o'sha kungi baho.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
