import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";
import { formatPhone } from "./PhoneInput";

/**
 * HR → EXAMINERLAR (2026-10-05, Jahongir: "hr uchun examinerlarni
 * valantyor va examiner qilib o'zgartirishni qo'shib ber").
 *
 * Mavjud daraja tizimining (staff_grades) qulay ko'rinishi:
 *   Volontyor — oylik hisoblanmaydi, o'ziga "Oyligim" ko'rinmaydi;
 *   Examiner  — oylikli. Avval volontyor bo'lsa Junior bo'ladi,
 *               Middle/Senior bo'lsa o'z darajasida qoladi.
 * Darajani batafsil (Junior/Middle/Senior) Hisobotlar → Ish haqi →
 * Darajalar bo'limida ham o'zgartirsa bo'ladi.
 */
type Grade = { key: string; label: string; coef: number };
type Row = {
  user_id: number; name: string; role: string; branch: string | null;
  phone: string | null; grade: string; grade_label: string; coef: number;
  since: string | null; updated_by: string | null;
};
type Data = { grades: Grade[]; rows: Row[]; can_edit: boolean };

export function ExaminerStatusTab() {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"" | "volunteer" | "paid">("");

  const load = () =>
    api.get<Data>("/staff-grades?only=examiner")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  useEffect(() => { load(); }, []);

  const rows = useMemo(() => {
    if (!d) return [];
    const n = q.trim().toLowerCase();
    return d.rows.filter((r) =>
      (!n || r.name.toLowerCase().includes(n))
      && (!filter || (filter === "volunteer") === (r.grade === "volunteer")));
  }, [d, q, filter]);

  async function setStatus(r: Row, paid: boolean) {
    if (paid === (r.grade !== "volunteer")) return;
    const msg = paid
      ? `${r.name} examiner (oylikli) bo'ladi. Shu oydan boshlab imtihonlari uchun oylik hisoblanadi. Davom etasizmi?`
      : `${r.name} volontyor bo'ladi — oylik hisoblanmaydi va unga "Oyligim" ko'rinmaydi. Davom etasizmi?`;
    if (!window.confirm(msg)) return;
    setBusy(r.user_id);
    setErr("");
    try {
      await api.put(`/staff-grades/${r.user_id}`, {
        grade: paid ? "junior" : "volunteer",
        note: paid ? "HR: examiner qilindi" : "HR: volontyor qilindi",
      });
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  if (err && !d) return <p className="text-sm text-red-600 py-6">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;

  const vol = d.rows.filter((r) => r.grade === "volunteer").length;

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Examinerlar</h2>
        <p className="text-sm text-slate-500">
          Volontyorga oylik hisoblanmaydi. "Examiner" qilinganda shu oydan
          imtihonlari uchun oylik hisoblanadi.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4 max-w-xl">
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Jami</p>
          <p className="text-lg font-semibold text-slate-900">{d.rows.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Examiner (oylikli)</p>
          <p className="text-lg font-semibold text-brand-700">{d.rows.length - vol}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Volontyor</p>
          <p className="text-lg font-semibold text-slate-700">{vol}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ism bo'yicha"
                 className="rounded-lg border border-slate-200 pl-8 pr-3 py-2 text-sm w-48" />
        </div>
        {([["", "Hammasi"], ["paid", "Examiner"], ["volunteer", "Volontyor"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setFilter(k)}
                  className={`px-3 py-1.5 rounded-lg text-sm border ${
                    filter === k ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-600"}`}>
            {l}
          </button>
        ))}
      </div>

      {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{err}</p>}

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center bg-white rounded-xl border border-slate-200">
          Examiner topilmadi
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">F.I.Sh.</th>
                <th className="text-left px-3 py-2.5 font-medium">Filial</th>
                <th className="text-left px-3 py-2.5 font-medium">Oxirgi o'zgarish</th>
                <th className="text-left px-3 py-2.5 font-medium">Holati</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const paid = r.grade !== "volunteer";
                return (
                  <tr key={r.user_id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5">
                      <p className="font-medium text-slate-900">{r.name}</p>
                      <p className="text-[11px] text-slate-400">
                        {[r.role, r.phone ? formatPhone(r.phone) : null].filter(Boolean).join(" · ")}
                      </p>
                    </td>
                    <td className="px-3 py-2.5 text-slate-600">{r.branch || "—"}</td>
                    <td className="px-3 py-2.5 text-xs text-slate-500">
                      {r.since ? formatDate(r.since) : "—"}
                      {r.updated_by && <span className="block text-slate-400">{r.updated_by}</span>}
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
                        <button
                          onClick={() => setStatus(r, false)}
                          disabled={!d.can_edit || busy === r.user_id}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium ${
                            !paid ? "bg-slate-600 text-white shadow" : "text-slate-500 hover:text-slate-700"}`}>
                          Volontyor
                        </button>
                        <button
                          onClick={() => setStatus(r, true)}
                          disabled={!d.can_edit || busy === r.user_id}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium ${
                            paid ? "bg-brand-600 text-white shadow" : "text-slate-500 hover:text-slate-700"}`}>
                          Examiner
                        </button>
                      </div>
                      {paid && (
                        <span className="ml-2 text-[11px] text-slate-400">{r.grade_label}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
