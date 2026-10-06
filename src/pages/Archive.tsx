import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Archive as ArchiveIcon, Download, RotateCcw, X, FileUp,
  Upload, Check, AlertTriangle, Trash2, FileDown, Search,
} from "lucide-react";
import {
  api, type ArchiveStudents, type ArchiveStaff, type ArchiveStaffRow,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  TEACHING_STAFF, STAFF_VIEWERS, HR_ACCESS, FREEZE_ROLES, FOUNDER, can,
  GROUP_MANAGE,
} from "../lib/roles";
import { ArchivedGroupsTab } from "../components/GroupArchive";
import { StaffRestoreModal } from "../components/StaffRestore";
import { BranchPicker, branchParam } from "../components/BranchPicker";
import { formatSom, formatDate } from "../lib/format";
import { formatPhone } from "../components/PhoneInput";
import { exportToExcel } from "../lib/exportXlsx";

type Tab = "students" | "staff" | "groups";

/** Arxiv toifalari rangi. */
const GROUP_TONE: Record<string, { box: string; text: string; dot: string }> = {
  debtor: {
    box: "bg-red-50 border-red-200",
    text: "text-red-700",
    dot: "bg-red-500",
  },
  credit: {
    box: "bg-amber-50 border-amber-200",
    text: "text-amber-700",
    dot: "bg-amber-500",
  },
  clear: {
    box: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-700",
    dot: "bg-emerald-500",
  },
  green: {
    box: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-700",
    dot: "bg-emerald-500",
  },
  neutral: {
    box: "bg-slate-50 border-slate-200",
    text: "text-slate-600",
    dot: "bg-slate-400",
  },
  red: {
    box: "bg-red-50 border-red-200",
    text: "text-red-700",
    dot: "bg-red-500",
  },
};

function toneOf(key: string) {
  return GROUP_TONE[key] || GROUP_TONE.neutral;
}

// ------------------------------------------------------- O'quvchilar
function StudentsTab() {
  const { user } = useAuth();
  const [data, setData] = useState<ArchiveStudents | null>(null);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  // 2026-08-22, Jahongir: "arxivda qidirv va filtr qoyib ber" — arxiv
  // yuzlab qatorga yetdi, kerakli odamni ko'z bilan izlab bo'lmaydi.
  const [q, setQ] = useState("");
  const [groupF, setGroupF] = useState("");   // qaysi guruhda o'qigan
  const [yearF, setYearF] = useState("");     // qaysi yilda ketgan
  const [sortBy, setSortBy] = useState("amount"); // amount | name | left
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const [busyId, setBusyId] = useState<number | null>(null);
  // LC UP'dan ketgan o'quvchilar ro'yxatini ko'chirish
  const [showImport, setShowImport] = useState(false);
  // Butunlay o'chirishni tasdiqlash oynasi (faqat asoschi)
  const [purging, setPurging] = useState<{ id: number; name: string } | null>(null);
  // O'quvchilar qaytib kelishi mumkin — qayta tiklash huquqi
  // 2026-09-16: administrator ham tiklaydi (api roles.STUDENT_RESTORE)
  const canRestore = can(user?.role, FREEZE_ROLES) || user?.role === "administrator";
  // 2026-08-22, Jahongir: "arxivdagilarni ochirishni faqat menga qoshib
  // ber" — butunlay o'chirish tarixni ham yo'q qiladi, shuning uchun
  // tugma faqat asoschida ko'rinadi (backend ham FOUNDER bilan yopiq).
  const canPurge = user?.role === FOUNDER;
  const canImport = can(user?.role, HR_ACCESS) ||
    user?.role === "accountant" || user?.role === "finance_director";

  useEffect(() => {
    setLoading(true);
    api
      .get<ArchiveStudents>(`/archive/students?x=1${branchParam(branchId)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [branchId, reloadKey]);

  async function restore(id: number, name: string) {
    if (
      !confirm(
        `${name} arxivdan qayta tiklansinmi?\n\n` +
          "Holati FAOL bo'ladi, keyin kerakli guruhga qo'shasiz."
      )
    )
      return;
    setBusyId(id);
    try {
      await api.post(`/students/${id}/restore`, {});
      setReloadKey((k) => k + 1);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  // Guruh va yil ro'yxatlari — mavjud ma'lumotdan yig'iladi
  const groupNames = Array.from(
    new Set(data.rows.map((r) => r.group).filter(Boolean) as string[])
  ).sort((a, b) => a.localeCompare(b));
  const years = Array.from(
    new Set(
      data.rows.map((r) => (r.left_date ? r.left_date.slice(0, 4) : ""))
        .filter(Boolean)
    )
  ).sort().reverse();

  const needle = q.trim().toLowerCase();
  const digits = needle.replace(/\D/g, "");
  const shown = data.rows
    .filter((r) => (filter ? r.group_key === filter : true))
    .filter((r) => (groupF ? r.group === groupF : true))
    .filter((r) => (yearF ? (r.left_date || "").slice(0, 4) === yearF : true))
    .filter((r) => {
      if (!needle) return true;
      // Ism, ID, guruh, filial va telefon (raqamlar bo'yicha ham) qidiriladi
      const hay = [r.full_name, r.public_id, r.group, r.branch]
        .filter(Boolean).join(" ").toLowerCase();
      if (hay.includes(needle)) return true;
      if (digits.length >= 3) {
        const phones = `${r.phone || ""} ${r.parent_phone || ""}`.replace(/\D/g, "");
        if (phones.includes(digits)) return true;
      }
      return false;
    });
  shown.sort((a, b) => {
    if (sortBy === "name") return a.full_name.localeCompare(b.full_name);
    if (sortBy === "left") return (b.left_date || "").localeCompare(a.left_date || "");
    return Math.abs(b.balance) - Math.abs(a.balance);
  });
  const hasFilter = !!(filter || q.trim() || groupF || yearF);

  async function purge(id: number) {
    setBusyId(id);
    try {
      await api.delete(`/students/${id}`);
      setPurging(null);
      setReloadKey((k) => k + 1);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        {data.groups.map((g) => {
          const T = toneOf(g.key);
          const active = filter === g.key;
          return (
            <button
              key={g.key}
              onClick={() => setFilter(active ? "" : g.key)}
              className={`text-left rounded-xl border p-4 transition ${
                active ? T.box : "bg-white border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2.5 h-2.5 rounded-full ${T.dot}`} />
                <p className="text-sm text-slate-700">{g.label}</p>
              </div>
              <p className="text-xl font-semibold text-slate-900">{g.count}</p>
              {g.total > 0 && (
                <p className={`text-sm mt-0.5 ${T.text}`}>
                  {formatSom(g.total)}
                </p>
              )}
              <p className="text-xs text-slate-400 mt-0.5">{g.hint}</p>
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="relative flex-1 min-w-[14rem] max-w-sm">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            size={16}
          />
          <input
            className="w-full rounded-lg border border-slate-300 pl-9 pr-8 py-2 text-sm"
            placeholder="Ism, ID, telefon, guruh..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {q && (
            <button
              onClick={() => setQ("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X size={14} />
            </button>
          )}
        </div>
        {groupNames.length > 1 && (
          <select
            value={groupF}
            onChange={(e) => setGroupF(e.target.value)}
            className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white max-w-[12rem]"
          >
            <option value="">Barcha guruhlar</option>
            {groupNames.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        )}
        {years.length > 1 && (
          <select
            value={yearF}
            onChange={(e) => setYearF(e.target.value)}
            className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white"
          >
            <option value="">Ketgan yil: barchasi</option>
            {years.map((y) => (
              <option key={y} value={y}>{y}-yil</option>
            ))}
          </select>
        )}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white"
        >
          <option value="amount">Summa bo'yicha</option>
          <option value="name">Ism bo'yicha (A-Z)</option>
          <option value="left">Ketgan sana (yangi)</option>
        </select>
        <BranchPicker value={branchId} onChange={setBranchId} />
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-sm text-slate-500">
          {shown.length} ta o'quvchi
          {hasFilter && (
            <span className="text-slate-400"> / {data.rows.length}</span>
          )}
        </span>
        {hasFilter && (
          <button
            onClick={() => { setFilter(""); setQ(""); setGroupF(""); setYearF(""); }}
            className="text-xs text-brand-600 hover:underline"
          >
            filtrni tozalash
          </button>
        )}
        <div className="flex-1" />
        <button
          onClick={() =>
            exportToExcel("arxiv-oquvchilar", "Arxiv",
              shown.map((r) => ({
                ID: r.public_id ?? "",
                "F.I.Sh.": r.full_name,
                Guruh: r.group ?? "",
                Filial: r.branch ?? "",
                Telefon: formatPhone(r.phone),
                "Qo'shilgan": r.enrolled_date ?? "",
                Ketgan: r.left_date ?? "",
                "Necha oy": r.months ?? "",
                Balans: r.balance,
                Toifa: data.groups.find((g) => g.key === r.group_key)?.label ?? "",
              })))
          }
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-slate-300"
        >
          <Download size={14} /> Excel
        </button>
        {canImport && (
          <button
            onClick={() => setShowImport(true)}
            title="LC UP'dagi ketgan o'quvchilar ro'yxatini ko'chirish"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:border-brand-300 hover:text-brand-700"
          >
            <FileUp size={14} /> Excel'dan qo'shish
          </button>
        )}
      </div>

      {showImport && (
        <ArchiveImportModal
          onClose={() => setShowImport(false)}
          onDone={() => setReloadKey((k) => k + 1)}
        />
      )}

      {shown.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          {hasFilter ? "Qidiruvga mos o'quvchi topilmadi" : "Arxivda o'quvchi yo'q"}
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">O'quvchi</th>
                <th className="text-left">Guruh</th>
                <th className="text-left">Telefon</th>
                <th className="text-left w-28">Ketgan</th>
                <th className="text-right w-24">Necha oy</th>
                <th className="text-right w-36">Hisob</th>
                <th className="text-left w-44 pr-4">Toifa</th>
                {(canRestore || canPurge) && <th className="w-44"></th>}
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => {
                const T = toneOf(r.group_key);
                const g = data.groups.find((x) => x.key === r.group_key);
                return (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5">
                      <Link
                        to={`/students/${r.id}`}
                        className="text-slate-800 hover:text-brand-700"
                      >
                        {r.full_name}
                      </Link>
                      {r.public_id && (
                        <span className="block text-xs text-slate-400">
                          {r.public_id}
                        </span>
                      )}
                    </td>
                    <td className="text-slate-500">{r.group || "—"}</td>
                    <td className="text-slate-500 text-xs">
                      {formatPhone(r.phone) || "—"}
                    </td>
                    <td className="text-slate-500 text-xs">
                      {r.left_date ? formatDate(r.left_date) : "—"}
                    </td>
                    <td className="text-right text-slate-500">
                      {r.months ?? "—"}
                    </td>
                    <td
                      className={`text-right font-medium ${
                        r.balance < 0
                          ? "text-red-600"
                          : r.balance > 0
                            ? "text-amber-600"
                            : "text-slate-400"
                      }`}
                    >
                      {r.balance === 0 ? "—" : formatSom(r.balance)}
                    </td>
                    <td className={`pr-4 text-xs ${T.text}`}>{g?.label}</td>
                    {(canRestore || canPurge) && (
                      <td className="pr-4 text-right whitespace-nowrap">
                        {canRestore && (
                          <button
                            onClick={() => restore(r.id, r.full_name)}
                            disabled={busyId === r.id}
                            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
                            title="Arxivdan qayta tiklash"
                          >
                            <RotateCcw size={12} />
                            Qayta tiklash
                          </button>
                        )}
                        {canPurge && (
                          <button
                            onClick={() => setPurging({ id: r.id, name: r.full_name })}
                            disabled={busyId === r.id}
                            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md text-red-600 hover:bg-red-50 disabled:opacity-50 ml-1"
                            title="Butunlay o'chirish (faqat asoschi)"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {purging && (
        <PurgeModal
          name={purging.name}
          busy={busyId === purging.id}
          onClose={() => setPurging(null)}
          onConfirm={() => purge(purging.id)}
        />
      )}
    </div>
  );
}

/**
 * BUTUNLAY O'CHIRISH TASDIG'I (2026-08-22).
 *
 * Jahongir: "arxivdagilarni ochirishni faqat menga qoshib ber".
 * Bu tizimdagi yagona QAYTARIB BO'LMAYDIGAN amal — o'quvchi bilan
 * birga uning to'lov, yo'qlama va imtihon tarixi ham yo'qoladi.
 * Shuning uchun tasodifan bosib yuborilmasin deb ism yozib tasdiqlash
 * talab qilinadi.
 */
function PurgeModal({
  name, busy, onClose, onConfirm,
}: {
  name: string;
  busy: boolean;
  onClose: () => void;
  onConfirm: () => void;
}) {
  const [typed, setTyped] = useState("");
  const ok = typed.trim().toLowerCase() === name.trim().toLowerCase();
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-600" />
            Butunlay o'chirish
          </h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-600 mb-2">
          <b className="text-slate-900">{name}</b> bazadan butunlay
          o'chiriladi. To'lov tarixi, yo'qlamalari va imtihon natijalari
          ham birga yo'qoladi.
        </p>
        <p className="text-sm text-red-700 bg-red-50 rounded-lg px-3 py-2 mb-3">
          Bu amalni QAYTARIB BO'LMAYDI. Agar shunchaki ro'yxatdan
          yashirish kerak bo'lsa — o'quvchi allaqachon arxivda turibdi,
          o'chirish shart emas.
        </p>
        <label className="block text-xs text-slate-500 mb-1">
          Tasdiqlash uchun o'quvchining to'liq ismini yozing:
        </label>
        <input
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-4"
          placeholder={name}
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          autoFocus
        />
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-600"
          >
            Bekor qilish
          </button>
          <button
            onClick={onConfirm}
            disabled={!ok || busy}
            className="px-3 py-2 rounded-lg bg-red-600 text-white text-sm disabled:opacity-40"
          >
            {busy ? "O'chirilmoqda..." : "Butunlay o'chirish"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------ Xodimlar
function StaffTab() {
  const { user } = useAuth();
  const [data, setData] = useState<ArchiveStaff | null>(null);
  const [filter, setFilter] = useState("");
  const [q, setQ] = useState("");           // ism/lavozim/filial qidiruvi
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<ArchiveStaffRow | null>(null);
  const [restoring, setRestoring] = useState<ArchiveStaffRow | null>(null);

  function load() {
    setLoading(true);
    api
      .get<ArchiveStaff>("/archive/staff")
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const needle = q.trim().toLowerCase();
  const shown = data.rows
    .filter((r) => (filter ? r.exit_type === filter : true))
    .filter((r) =>
      needle
        ? [r.full_name, r.username, r.role_label, r.branch, r.exit_reason]
            .filter(Boolean).join(" ").toLowerCase().includes(needle)
        : true
    );
  const hasFilter = !!(filter || needle);
  const canEdit = can(user?.role, HR_ACCESS);
  const canRehire = can(user?.role, STAFF_VIEWERS);

  // Ishga qaytarish — HR "Ketganlar arxivi" bilan bitta oyna
  // (2026-10-06): parolni tiklash, qizil yo'lak ogohlantirishi.
  function rehire(r: ArchiveStaffRow) {
    setRestoring(r);
  }

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        {data.groups.map((g) => {
          const T = toneOf(g.key);
          const active = filter === g.key;
          return (
            <button
              key={g.key}
              onClick={() => setFilter(active ? "" : g.key)}
              className={`text-left rounded-xl border p-4 transition ${
                active ? T.box : "bg-white border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2.5 h-2.5 rounded-full ${T.dot}`} />
                <p className="text-sm text-slate-700">{g.label}</p>
              </div>
              <p className="text-xl font-semibold text-slate-900">{g.count}</p>
              <p className="text-xs text-slate-400 mt-0.5">{g.hint}</p>
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="relative flex-1 min-w-[14rem] max-w-sm">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            size={16}
          />
          <input
            className="w-full rounded-lg border border-slate-300 pl-9 pr-8 py-2 text-sm"
            placeholder="Ism, lavozim, filial..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {q && (
            <button
              onClick={() => setQ("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <span className="text-sm text-slate-500">
          {shown.length} ta xodim
          {hasFilter && (
            <span className="text-slate-400"> / {data.rows.length}</span>
          )}
        </span>
        {hasFilter && (
          <button
            onClick={() => { setFilter(""); setQ(""); }}
            className="text-xs text-brand-600 hover:underline"
          >
            filtrni tozalash
          </button>
        )}
      </div>

      {shown.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          {hasFilter ? "Qidiruvga mos xodim topilmadi" : "Ishdan bo'shagan xodim yo'q"}
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Xodim</th>
                <th className="text-left">Lavozim</th>
                <th className="text-left">Filial</th>
                <th className="text-left w-28">Ketgan</th>
                <th className="text-left">Sabab</th>
                <th className="text-left w-40">Toifa</th>
                <th className="w-24" />
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => {
                const T = toneOf(r.exit_type);
                return (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5 text-slate-800">
                      {r.full_name}
                      <span className="block text-xs text-slate-400">
                        {r.username}
                      </span>
                    </td>
                    <td className="text-slate-500">{r.role_label}</td>
                    <td className="text-slate-500">{r.branch || "—"}</td>
                    <td className="text-slate-500 text-xs">
                      {r.exit_date ? formatDate(r.exit_date) : "—"}
                    </td>
                    <td className="text-slate-600 text-xs">
                      {r.exit_reason || "—"}
                    </td>
                    <td>
                      <span
                        className={`inline-flex items-center gap-1.5 text-xs ${T.text}`}
                      >
                        <span className={`w-2 h-2 rounded-full ${T.dot}`} />
                        {r.exit_label}
                      </span>
                    </td>
                    <td className="pr-4 text-right whitespace-nowrap">
                      {canRehire && (
                        <button
                          onClick={() => rehire(r)}
                          className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 hover:bg-emerald-100 mr-2"
                          title="Ishga qaytarish"
                        >
                          <RotateCcw size={12} />
                          Qaytarish
                        </button>
                      )}
                      {canEdit && r.kind !== "teacher" && (
                        <button
                          onClick={() => setEditing(r)}
                          className="px-2.5 py-1 rounded-md text-xs border border-slate-200 text-slate-600 hover:border-brand-300"
                        >
                          Belgilash
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {restoring && (
        <StaffRestoreModal
          row={{ ...restoring, kind: restoring.kind ?? "user" }}
          onClose={() => setRestoring(null)}
          onDone={load}
        />
      )}
      {editing && (
        <ExitModal
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

const EXIT_TYPES = [
  { key: "green", label: "Yashil yo'lak", hint: "Qaytarib olsa bo'ladi" },
  { key: "neutral", label: "Neytral", hint: "Oddiy ketish" },
  { key: "red", label: "Qizil yo'lak", hint: "Qayta ishga olinmaydi" },
];

function ExitModal({
  row, onClose, onSaved,
}: {
  row: ArchiveStaffRow;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [type, setType] = useState(row.exit_type || "neutral");
  const [reason, setReason] = useState(row.exit_reason || "");
  const [err, setErr] = useState("");

  async function save() {
    try {
      await api.put(`/archive/staff/${row.id}`, {
        exit_type: type,
        exit_reason: reason || null,
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-5">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">Qanday ajrashildi</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">{row.full_name}</p>
        {err && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">
            {err}
          </p>
        )}
        <div className="space-y-2">
          {EXIT_TYPES.map((t) => {
            const T = toneOf(t.key);
            return (
              <button
                key={t.key}
                onClick={() => setType(t.key)}
                className={`w-full text-left rounded-xl border p-3 transition ${
                  type === t.key ? T.box : "bg-white border-slate-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${T.dot}`} />
                  <span className="text-sm font-medium text-slate-800">
                    {t.label}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 ml-4.5">{t.hint}</p>
              </button>
            );
          })}
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Sabab (ixtiyoriy)"
            rows={2}
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

// ---------------------------------------------------------------- Sahifa
export default function Archive() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("students");

  if (!can(user?.role, TEACHING_STAFF)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const showStaff = can(user?.role, STAFF_VIEWERS);
  // Arxivdagi guruhlar (2026-09-30) — guruhni boshqaradiganlarga
  const showGroups = can(user?.role, GROUP_MANAGE);
  const tabs = [
    { k: "students" as Tab, l: "O'quvchilar", show: true },
    { k: "staff" as Tab, l: "Xodimlar", show: showStaff },
    { k: "groups" as Tab, l: "Guruhlar", show: showGroups },
  ].filter((t) => t.show);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ArchiveIcon size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Arxiv</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Ketgan o'quvchilar, ishdan bo'shagan xodimlar va yopilgan guruhlar
      </p>

      {tabs.length > 1 && (
        <div className="flex gap-1 border-b border-slate-200 mb-5">
          {tabs.map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition ${
                tab === t.k
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.l}
            </button>
          ))}
        </div>
      )}

      {tab === "groups" && showGroups ? (
        <ArchivedGroupsTab canRestore={showGroups} />
      ) : tab === "staff" && showStaff ? (
        <StaffTab />
      ) : (
        <StudentsTab />
      )}
    </div>
  );
}

// ------------------------------ Excel'dan arxiv o'quvchilar

interface Row {
  name: string;
  phone?: string;
  parent_phone?: string;
  branch?: string;
  group?: string;
  enrolled?: string;
  left?: string;
  note?: string;
}

interface ResRow {
  row: number;
  name: string;
  phone?: string | null;
  branch?: string | null;
  group?: string | null;
  enrolled?: string | null;
  left?: string | null;
  status: "ok" | "duplicate" | "skip";
  reason?: string;
}

interface Result {
  committed: boolean;
  ok: number;
  duplicate: number;
  skipped: number;
  rows: ResRow[];
  shown: number;
  all_rows: number;
}

const LABEL: Record<string, string> = {
  ok: "qo'shiladi",
  duplicate: "allaqachon bor",
  skip: "o'tkazildi",
};

const TONE: Record<string, string> = {
  ok: "bg-emerald-100 text-emerald-700",
  duplicate: "bg-slate-100 text-slate-500",
  skip: "bg-amber-100 text-amber-700",
};

/**
 * LC UP'dagi ketgan o'quvchilar ro'yxatini bir marta ko'chirish.
 *
 * Ular ARXIV holatida ochiladi: faol ro'yxatga, oylikka, yo'qlamaga va
 * hisob-kitobga umuman aralashmaydi — faqat eski to'lovlar va tarix
 * bog'lanadigan karta bo'lib turadi.
 */
export function ArchiveImportModal({ onClose, onDone }: {
  onClose: () => void;
  onDone: () => void;
}) {
  const { user } = useAuth();
  const [rows, setRows] = useState<Row[]>([]);
  const [fileName, setFileName] = useState("");
  const [res, setRes] = useState<Result | null>(null);
  const [count, setCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function loadStats() {
    api
      .get<{ count: number }>("/archive/students/import")
      .then((d) => setCount(d.count))
      .catch(() => setCount(0));
  }
  useEffect(loadStats, []);

  async function readFile(f: File) {
    setErr("");
    setRes(null);
    setRows([]);
    try {
      const XLSX = await import("xlsx");
      const wb = XLSX.read(await f.arrayBuffer());
      const ws = wb.Sheets[wb.SheetNames[0]];
      const raw: unknown[][] = XLSX.utils.sheet_to_json(ws, {
        header: 1,
        raw: false,
      });
      if (raw.length < 2) throw new Error("Faylda ma'lumot topilmadi");
      const head = (raw[0] as unknown[]).map((h) =>
        String(h || "").toLowerCase()
      );
      const col = (...keys: string[]) =>
        head.findIndex((h) => keys.some((k) => h.includes(k)));
      const iName = col("name", "ism", "f.i", "student", "o'quvchi", "oquvchi");
      const iPhone = col("phone", "telefon", "raqam", "mobile");
      const iParent = col("parent", "ota", "ona", "родител");
      const iBranch = col("branch", "filial", "фили");
      const iGroup = col("group", "guruh", "груп");
      const iEnroll = col("enroll", "qo'shil", "qoshil", "boshla", "start");
      const iLeft = col("left", "ketgan", "chiqqan", "tugat", "end");
      const iNote = col("note", "izoh", "comment", "коммент", "sabab");
      if (iName < 0)
        throw new Error(
          "Ism ustuni topilmadi — sarlavhada Name / Ism / O'quvchi bo'lsin"
        );

      const out: Row[] = [];
      const g = (r: unknown[], i: number) =>
        i >= 0 ? String(r[i] ?? "").trim() : "";
      for (const r of raw.slice(1)) {
        const name = g(r, iName);
        if (!name) continue;
        out.push({
          name,
          phone: g(r, iPhone),
          parent_phone: g(r, iParent),
          branch: g(r, iBranch),
          group: g(r, iGroup),
          enrolled: g(r, iEnroll),
          left: g(r, iLeft),
          note: g(r, iNote),
        });
      }
      if (out.length === 0) throw new Error("Bironta ham qator o'qilmadi");
      setRows(out);
      setFileName(f.name);
      check(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Faylni o'qib bo'lmadi");
    }
  }

  async function check(list: Row[]) {
    setBusy(true);
    setErr("");
    try {
      setRes(
        await api.post<Result>("/archive/students/import", {
          rows: list,
          commit: false,
        })
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function doImport() {
    if (!res || res.ok === 0) return;
    if (
      !confirm(
        `${res.ok} ta ketgan o'quvchi Arxivga qo'shilsinmi?\n\n` +
          "Ular faol ro'yxatga, oylikka va yo'qlamaga aralashmaydi.\n" +
          "Kerak bo'lsa keyin bitta tugma bilan bekor qilasiz."
      )
    )
      return;
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<Result>("/archive/students/import", {
        rows,
        commit: true,
      });
      setRes(r);
      loadStats();
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function undo() {
    if (
      !confirm(
        "Import bilan qo'shilgan arxiv o'quvchilar o'chirilsinmi?\n\n" +
          "To'lovi yoki yo'qlamasi borlari saqlab qolinadi."
      )
    )
      return;
    setBusy(true);
    try {
      const r = await api.delete<{ deleted: number; kept: number }>(
        "/archive/students/import"
      );
      alert(
        `${r.deleted} ta o'chirildi` +
          (r.kept ? `, ${r.kept} tasida to'lov bor — saqlandi` : "")
      );
      setRes(null);
      setRows([]);
      setFileName("");
      loadStats();
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  const bad = res ? res.rows.filter((r) => r.status !== "ok") : [];

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-900">
            Arxiv o'quvchilarni Excel'dan qo'shish
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <p className="text-xs text-slate-500 mb-4">
          LC UP'dan ketgan o'quvchilar ro'yxatini Excel qilib yuklab oling.
          Sarlavhada <b>Ism</b> bo'lsa yetadi; <b>Telefon</b>,{" "}
          <b>Ota-ona</b>, <b>Filial</b>, <b>Guruh</b>,{" "}
          <b>Qo'shilgan</b>, <b>Ketgan</b> va <b>Izoh</b> bo'lsa
          to'liqroq chiqadi. Bir xil ism-telefon ikkinchi marta
          qo'shilmaydi, shuning uchun faylni qayta tashlashdan
          qo'rqmang.
        </p>

        <div className="flex flex-wrap items-center gap-3 mb-4">
          <label className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 text-sm font-medium cursor-pointer">
            <Upload size={15} />
            Excel faylni tanlang
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) readFile(f);
                e.target.value = "";
              }}
            />
          </label>
          {fileName && (
            <span className="text-sm text-slate-500">{fileName}</span>
          )}
          {busy && (
            <span className="text-sm text-slate-400">Tekshirilmoqda…</span>
          )}
          <div className="flex-1" />
          {count > 0 && (
            <span className="text-xs text-slate-500">
              Import bilan qo'shilgan: {count} ta
            </span>
          )}
          {count > 0 && user?.role === "founder" && (
            <button
              onClick={undo}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 px-3 py-1.5 text-sm disabled:opacity-40"
            >
              <Trash2 size={14} /> Bekor qilish
            </button>
          )}
        </div>

        {err && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
            {err}
          </p>
        )}

        {res && (
          <>
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                {
                  l: res.committed ? "Qo'shildi" : "Qo'shishga tayyor",
                  v: String(res.ok),
                  c: "text-emerald-600",
                },
                {
                  l: "Allaqachon bor",
                  v: String(res.duplicate),
                  c: "text-slate-400",
                },
                {
                  l: "O'tkazildi",
                  v: String(res.skipped),
                  c: res.skipped ? "text-amber-600" : "text-slate-400",
                },
              ].map((s) => (
                <div
                  key={s.l}
                  className="rounded-xl border border-slate-200 p-3"
                >
                  <p className="text-xs text-slate-500 mb-1">{s.l}</p>
                  <p className={`text-lg font-semibold ${s.c}`}>{s.v}</p>
                </div>
              ))}
            </div>

            {!res.committed && res.ok > 0 && (
              <button
                onClick={doImport}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-4 py-2.5 text-sm font-medium mb-4 disabled:opacity-40"
              >
                <Check size={16} />
                {res.ok} ta o'quvchini Arxivga qo'shish
              </button>
            )}

            {res.committed && (
              <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-4">
                {res.ok} ta o'quvchi Arxivga qo'shildi. Endi eski
                to'lovlar importi ularni topa oladi.
              </p>
            )}

            {bad.length > 0 && (
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2.5 bg-amber-50 border-b border-amber-200">
                  <p className="text-sm text-amber-800 flex items-center gap-1.5">
                    <AlertTriangle size={14} />
                    {bad.length} ta qator qo'shilmadi
                  </p>
                  <button
                    onClick={() =>
                      exportToExcel(
                        "Qoshilmagan-arxiv",
                        "Muammoli",
                        bad.map((r) => ({
                          Qator: r.row,
                          "O'quvchi": r.name,
                          Sabab: r.reason || LABEL[r.status],
                        }))
                      )
                    }
                    className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-brand-700"
                  >
                    <FileDown size={13} /> Excel
                  </button>
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-xs text-slate-500">
                    <tr>
                      <th className="text-left px-4 py-2 w-16">Qator</th>
                      <th className="text-left px-3 py-2">O'quvchi</th>
                      <th className="text-left px-3 py-2">Sabab</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bad.slice(0, 100).map((r) => (
                      <tr
                        key={`${r.row}-${r.status}`}
                        className="border-t border-slate-100"
                      >
                        <td className="px-4 py-2 text-slate-400">{r.row}</td>
                        <td className="px-3 py-2 text-slate-800">{r.name}</td>
                        <td className="px-3 py-2">
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${TONE[r.status]}`}
                          >
                            {LABEL[r.status]}
                          </span>
                          {r.reason && (
                            <span className="text-xs text-slate-500 ml-2">
                              {r.reason}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {bad.length > 100 && (
                  <p className="text-xs text-slate-400 px-4 py-2">
                    Yana {bad.length - 100} ta — to'liq ro'yxat Excel'da.
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
