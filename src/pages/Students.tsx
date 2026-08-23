import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Plus, Search, X, Download, Pencil, FileUp } from "lucide-react";
import {
  api, getGlobalBranch, type Student, type Group, type Branch,
} from "../lib/api";
import { formatSom } from "../lib/format";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, can } from "../lib/roles";
import { exportToExcel } from "../lib/exportXlsx";
import { PhoneInput, formatPhone } from "../components/PhoneInput";

const STATUSES = [
  { key: "active", label: "Faol" },
  { key: "trial", label: "Sinovda" },
  { key: "left", label: "Chiqib ketgan" },
  { key: "frozen", label: "Muzlatilgan" },
  { key: "archived", label: "Arxiv (ketgan)" },
];

function StudentModal({
  groups,
  branches,
  defaultBranchId,
  initial,
  onClose,
  onSaved,
}: {
  groups: Group[];
  branches: Branch[];
  defaultBranchId: number | null;
  initial?: Student;
  onClose: () => void;
  onSaved: (s: Student) => void;
}) {
  const editing = !!initial;
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [phone, setPhone] = useState(initial?.phone ?? "");
  const [parentPhone, setParentPhone] = useState(initial?.parent_phone ?? "");
  const [groupId, setGroupId] = useState<string>(
    initial?.group ? String(initial.group.id) : ""
  );
  const [branchId, setBranchId] = useState(
    initial?.branch
      ? String(initial.branch.id)
      : defaultBranchId
      ? String(defaultBranchId)
      : ""
  );
  // Yangi o'quvchi "sinov darsida" boshlanadi - guruhga qo'shilishi bilan
  // avtomat faol bo'lib qolmasligi kerak. Faollashtirish guruh ro'yxatidagi
  // uch nuqta menyusidan qilinadi.
  const [status, setStatus] = useState(initial?.status ?? "trial");
  const [enrolledDate, setEnrolledDate] = useState(
    initial?.enrolled_date ?? new Date().toISOString().slice(0, 10)
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!fullName.trim()) {
      setError("Ism-familiyani kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body = {
        full_name: fullName,
        phone: phone || null,
        parent_phone: parentPhone || null,
        group_id: groupId ? Number(groupId) : null,
        branch_id: branchId ? Number(branchId) : null,
        enrolled_date: enrolledDate || null,
        status,
      };
      const s = editing
        ? await api.put<Student>(`/students/${initial!.id}`, body)
        : await api.post<Student>("/students", body);
      onSaved(s);
      onClose();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Xatolik";
      // Dublikat ogohlantirishi: "yo'q, bu yangi odam" desa — force
      // bilan kiritaveradi
      if (!editing && msg.includes("qayta kiritib qo'ymayapsizmi")) {
        if (confirm(msg + "\n\nOK — yangi odam, kiritilsin.")) {
          try {
            const s2 = await api.post<Student>("/students?force=true", {
              full_name: fullName,
              phone: phone || null,
              parent_phone: parentPhone || null,
              group_id: groupId ? Number(groupId) : null,
              branch_id: branchId ? Number(branchId) : null,
              enrolled_date: enrolledDate || null,
              status,
            });
            onSaved(s2);
            onClose();
          } catch (e2) {
            setError(e2 instanceof Error ? e2.message : "Xatolik");
          } finally {
            setSaving(false);
          }
          return;
        }
      }
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[92vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {editing ? "Talabani tahrirlash" : "Yangi talaba qo'shish"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              F.I.Sh. *
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Talaba telefoni
            </label>
            <PhoneInput value={phone} onChange={setPhone} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Ota-ona telefoni
            </label>
            <PhoneInput value={parentPhone} onChange={setParentPhone} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Qo'shilgan sana
            </label>
            <input
              type="date"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={enrolledDate}
              onChange={(e) => setEnrolledDate(e.target.value)}
            />
            <p className="text-xs text-slate-400 mt-1">
              Oy o'rtasida qo'shilgan talaba uchun to'lov shu sanadan hisoblanadi
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Filial
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={branchId}
              onChange={(e) => setBranchId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Guruh
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
            >
              <option value="">— tanlanmagan —</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Holat
            </label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
            {status === "archived" && (
              <p className="text-xs text-slate-400 mt-1">
                Ketgan sana avtomatik bugungi kun bilan qo'yiladi — LTV shundan
                hisoblanadi.
              </p>
            )}
            {!initial && status === "trial" && (
              <p className="text-xs text-slate-400 mt-1">
                Yangi o'quvchi sinov darsida boshlanadi. Guruh ro'yxatidagi uch
                nuqta menyusidan "Faollashtirish" bosilganda faol bo'ladi.
              </p>
            )}
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={submit}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-2 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}

export { StudentModal };

export default function Students() {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [q, setQ] = useState("");
  // Filtrlar: filial / guruh / holat — yuklangan ro'yxat ustida ishlaydi
  const [branchF, setBranchF] = useState("");
  const [groupF, setGroupF] = useState("");
  // Dashboard kartasidan kelganda filtr URL orqali keladi
  // (2026-08-12, Jahongir: "faol talabalarga ezganda talabalar
  // bo'limiga o'tib faol talabalar filtri bilan chiqsin")
  const [sp] = useSearchParams();
  const _urlStatus = sp.get("status") || "";
  const [statusF, setStatusF] = useState(
    ["active", "trial", "frozen", "archived"].includes(_urlStatus)
      ? _urlStatus : "");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [editing, setEditing] = useState<Student | null>(null);

  function load() {
    setLoading(true);
    const query = q ? `?q=${encodeURIComponent(q)}` : "";
    Promise.all([
      api.get<Student[]>(`/students${query}`),
      api.get<Group[]>("/groups"),
      api.get<Branch[]>("/branches"),
    ])
      .then(([s, g, b]) => {
        setStudents(s);
        setGroups(g);
        setBranches(b);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const canEdit =
    can(user?.role, TEACHING_STAFF) || user?.role === "hr_manager";
  const showBranchColumn = branches.length > 1;
  const filtered = students.filter((s) =>
    (!branchF || String(s.branch?.id ?? "") === branchF) &&
    (!groupF || String(s.group?.id ?? "") === groupF) &&
    (!statusF || s.status === statusF)
  );

  function exportStudents() {
    exportToExcel(
      `Talabalar-${new Date().toISOString().slice(0, 10)}`,
      "Talabalar",
      filtered.map((s) => ({
        "F.I.Sh.": s.full_name,
        Telefon: s.phone || "",
        "Ota-ona telefoni": s.parent_phone || "",
        Guruh: s.group?.name || "",
        Filial: s.branch?.name || "",
        "Balans (so'm)": Math.round(s.balance),
      }))
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Talabalar</h1>
          <p className="text-sm text-slate-500">Ko'rsatilmoqda: {filtered.length} / {students.length}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportStudents}
            disabled={students.length === 0}
            className="flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            <Download size={16} />
            Excel'ga eksport
          </button>
          {canEdit && (
            <>
              <button
                onClick={() => setShowImport(true)}
                className="flex items-center gap-2 bg-white border border-slate-300 hover:border-brand-300 text-slate-700 rounded-lg px-4 py-2 text-sm font-medium"
              >
                <FileUp size={15} /> Excel'dan import
              </button>
              <button
                onClick={() => setShowAdd(true)}
                className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium"
              >
                <Plus size={16} />
                Yangi talaba
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative max-w-sm flex-1 min-w-[12rem]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input
            className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm"
            placeholder="Ism orqali qidirish..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        {branches.length > 1 && (
          <select value={branchF} onChange={(e) => setBranchF(e.target.value)}
            className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white">
            <option value="">Barcha filiallar</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        )}
        <select value={groupF} onChange={(e) => setGroupF(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white max-w-[11rem]">
          <option value="">Barcha guruhlar</option>
          {groups.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
        <select value={statusF} onChange={(e) => setStatusF(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white">
          <option value="">Barcha holatlar</option>
          <option value="active">Faol</option>
          <option value="trial">Sinovda</option>
          <option value="left">Chiqib ketgan</option>
          <option value="frozen">Muzlatilgan</option>
          <option value="archived">Arxiv</option>
        </select>
        {(branchF || groupF || statusF) && (
          <button
            onClick={() => { setBranchF(""); setGroupF(""); setStatusF(""); }}
            className="text-xs text-slate-400 hover:text-slate-600">
            Tozalash
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">F.I.Sh.</th>
              <th className="text-left px-4 py-3 font-medium">Telefon</th>
              <th className="text-left px-4 py-3 font-medium">Guruh</th>
              {showBranchColumn && (
                <th className="text-left px-4 py-3 font-medium">Filial</th>
              )}
              <th className="text-left px-4 py-3 font-medium">Holat</th>
              <th className="text-right px-4 py-3 font-medium">Balans</th>
              {canEdit && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                  Yuklanmoqda...
                </td>
              </tr>
            )}
            {!loading && students.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-400">
                  Talaba topilmadi
                </td>
              </tr>
            )}
            {filtered.map((s, si) => (
              <tr key={s.id} data-guide={si === 0 ? "student-row-first" : undefined} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link
                    to={`/students/${s.id}`}
                    className="font-medium text-brand-700 hover:underline"
                  >
                    {s.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600 text-xs">
                  {formatPhone(s.phone) || "—"}
                </td>
                <td className="px-4 py-3">
                  {s.group ? (
                    <span className="inline-block bg-brand-50 text-brand-700 rounded-md px-2 py-0.5 text-xs">
                      {s.group.name}
                    </span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                {showBranchColumn && (
                  <td className="px-4 py-3 text-slate-600">{s.branch?.name || "—"}</td>
                )}
                <td className="px-4 py-3">
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-medium ${
                      s.status === "active"
                        ? "bg-green-50 text-green-700"
                        : s.status === "archived"
                        ? "bg-slate-100 text-slate-500"
                        : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    {STATUSES.find((x) => x.key === s.status)?.label || s.status}
                  </span>
                </td>
                <td
                  className={`px-4 py-3 text-right font-medium ${
                    s.balance < 0 ? "text-red-600" : "text-slate-700"
                  }`}
                >
                  {formatSom(s.balance)}
                </td>
                {canEdit && (
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setEditing(s)}
                      title="Tahrirlash"
                      className="text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={15} />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showImport && (
        <ImportStudentsModal
          groups={groups}
          onClose={() => setShowImport(false)}
          onDone={() => {
            setShowImport(false);
            load();
          }}
        />
      )}
      {showAdd && (
        <StudentModal
          groups={groups}
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          onClose={() => setShowAdd(false)}
          onSaved={() => load()}
        />
      )}
      {editing && (
        <StudentModal
          groups={groups}
          branches={branches}
          defaultBranchId={Number(getGlobalBranch()) || user?.branch_id || null}
          initial={editing}
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

/* ==================== EXCEL'DAN IMPORT ==================== */
/** LC UP'dan guruh bo'yicha eksport qilingan .xlsx — o'quvchilar
 *  tanlangan guruhga bir bosishda qo'shiladi. Ustunlar: Name/Ism,
 *  Phone, Address/Manzil, Birth, Status. Dublikat (shu guruhda bir xil
 *  ism/telefon) o'zi o'tkazib yuboriladi. */
type ImpStudentRow = {
  full_name: string; phone: string; address: string;
  birth_date: string; status: string;
};

function ImportStudentsModal({
  groups, onClose, onDone,
}: {
  groups: Group[]; onClose: () => void; onDone: () => void;
}) {
  const [rows, setRows] = useState<ImpStudentRow[]>([]);
  const [groupId, setGroupId] = useState("");
  const [fileName, setFileName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState<{
    created: number; group: string;
    results: { name: string; status: string; reason?: string }[];
  } | null>(null);

  async function readFile(f: File) {
    setErr("");
    setResult(null);
    try {
      const XLSX = await import("xlsx");
      const wb = XLSX.read(await f.arrayBuffer());
      const ws = wb.Sheets[wb.SheetNames[0]];
      const raw: unknown[][] = XLSX.utils.sheet_to_json(ws, {
        header: 1, raw: false,
      });
      if (raw.length < 2) throw new Error("Faylda ma'lumot topilmadi");
      const head = (raw[0] as unknown[]).map((h) =>
        String(h || "").toLowerCase());
      const col = (...keys: string[]) =>
        head.findIndex((h) => keys.some((k) => h.includes(k)));
      const iName = col("name", "ism", "f.i");
      const iPhone = col("phone", "mobile", "telefon", "raqam");
      const iAddr = col("address", "manzil");
      const iBirth = col("birth", "tug'ilgan", "tugilgan");
      const iStatus = col("status", "holat");
      if (iName < 0)
        throw new Error("Ism ustuni topilmadi (Name/Ism bo'lishi kerak)");
      const out: ImpStudentRow[] = [];
      for (const r of raw.slice(1)) {
        const name = String(r[iName] ?? "").trim();
        if (!name) continue;
        out.push({
          full_name: name,
          phone: iPhone >= 0 ? String(r[iPhone] ?? "").trim() : "",
          address: iAddr >= 0 ? String(r[iAddr] ?? "").trim() : "",
          birth_date: iBirth >= 0
            ? String(r[iBirth] ?? "").trim().slice(0, 10) : "",
          status: iStatus >= 0 ? String(r[iStatus] ?? "").trim() : "",
        });
      }
      if (out.length === 0) throw new Error("Bironta ham qator o'qilmadi");
      setRows(out);
      setFileName(f.name);
      // Fayl nomi guruh nomi bilan boshlansa — o'zi tanlab qo'yadi
      const base = f.name.toLowerCase();
      const hit = groups.find((g) =>
        base.startsWith(g.name.toLowerCase().slice(0, 6)));
      if (hit) setGroupId(String(hit.id));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Faylni o'qib bo'lmadi");
    }
  }

  async function doImport() {
    if (!groupId) {
      setErr("Avval guruhni tanlang");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<{
        created: number; group: string;
        results: { name: string; status: string; reason?: string }[];
      }>("/students/import", { rows, group_id: Number(groupId) });
      setResult(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Import bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4 py-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            O'quvchilarni Excel'dan import qilish
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {result ? (
          <div>
            <p className="text-sm font-medium text-emerald-700 mb-3">
              ✓ {result.created} ta o'quvchi "{result.group}" guruhiga
              qo'shildi
            </p>
            <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 mb-4 max-h-72 overflow-auto">
              {result.results.map((r, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2 text-sm">
                  <span>{r.status === "ok" ? "✅" : "⏭️"}</span>
                  <span className="text-slate-800">{r.name}</span>
                  {r.reason && (
                    <span className="text-xs text-slate-400">— {r.reason}</span>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={onDone}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium"
            >
              Tayyor
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <input
                type="file"
                accept=".xlsx,.xls,.csv"
                id="imp-students-file"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) readFile(f);
                }}
              />
              <label
                htmlFor="imp-students-file"
                className="flex items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl py-6 text-sm text-slate-500 cursor-pointer hover:border-brand-400"
              >
                <FileUp size={16} />
                {fileName || "Excel faylni tanlang (.xlsx)"}
              </label>
            </div>

            {rows.length > 0 && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">
                    Qaysi guruhga qo'shilsin *
                  </label>
                  <select
                    value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="">— guruhni tanlang —</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}{g.branch ? ` · ${g.branch.name}` : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="border border-slate-200 rounded-lg max-h-64 overflow-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50 text-slate-500 sticky top-0">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium">F.I.Sh.</th>
                        <th className="text-left px-3 py-2 font-medium">Telefon</th>
                        <th className="text-left px-3 py-2 font-medium">Manzil</th>
                        <th className="text-left px-3 py-2 font-medium">Holat</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {rows.map((r, i) => (
                        <tr key={i}>
                          <td className="px-3 py-1.5 text-slate-800">{r.full_name}</td>
                          <td className="px-3 py-1.5 text-slate-600">{r.phone}</td>
                          <td className="px-3 py-1.5 text-slate-500 max-w-[12rem] truncate">
                            {r.address}
                          </td>
                          <td className="px-3 py-1.5 text-slate-500">{r.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-slate-400">
                  {rows.length} ta qator o'qildi. Shu guruhda bir xil ism
                  yoki telefon bo'lsa, o'sha qator o'tkazib yuboriladi —
                  xato ikki marta bossangiz ham ro'yxat ikkilanmaydi.
                  Balans va to'lovlar bu yerdan ko'chmaydi — to'lovlarni
                  kassadan kiritasiz.
                </p>
              </>
            )}

            {err && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{err}</p>
            )}

            <button
              onClick={doImport}
              disabled={busy || rows.length === 0}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-50"
            >
              {busy ? "Qo'shilmoqda..." : `${rows.length} ta o'quvchini qo'shish`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
