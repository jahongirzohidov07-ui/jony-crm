import { useEffect, useState } from "react";
import { X, Cake, FileText, Award, TrendingUp, Layers } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * Ustoz umumiy kartasi — asoschi va o'quv bo'limi rahbari uchun.
 * Oylik va o'sishi, o'quvchilar soni, guruhlar to'lganligi, shartnoma
 * va sertifikat muddati, tug'ilgan kun, dars sifati, daraja.
 */

const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");

function MiniBars({
  data, val, tone,
}: { data: Any[]; val: (m: Any) => number; tone: string }) {
  const max = Math.max(...data.map(val), 1);
  return (
    <div className="flex items-end gap-1 h-14 mt-2">
      {data.map((m, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
          <div
            className={`w-full rounded-sm ${tone}`}
            style={{ height: `${Math.max((val(m) / max) * 100, 3)}%` }}
            title={`${m.label}: ${fmt(val(m))}`}
          />
          <span className="text-[9px] text-slate-400">
            {m.label.split(" ")[0]}
          </span>
        </div>
      ))}
    </div>
  );
}

function DaysLeft({ days }: { days: number | null }) {
  if (days === null || days === undefined)
    return <span className="text-slate-400">muddatsiz</span>;
  if (days < 0)
    return <span className="text-red-600 font-medium">
      {-days} kun oldin tugagan!
    </span>;
  if (days <= 30)
    return <span className="text-amber-600 font-medium">
      {days} kun qoldi
    </span>;
  return <span className="text-slate-700">{days} kun qoldi</span>;
}

export function TeacherOverviewModal({
  teacherId, onClose,
}: { teacherId: number; onClose: () => void }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api
      .get<Any>(`/teachers/${teacherId}/overview`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [teacherId]);

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] overflow-auto p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-900">
            {d ? d.name : "Yuklanmoqda…"} — umumiy ko'rinish
          </h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        {err && <p className="text-sm text-red-600">{err}</p>}
        {d && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Shu oy oyligi</p>
                <p className="text-lg font-semibold text-slate-900">
                  {fmt(d.salary_now)}
                </p>
                <p className={`text-xs ${d.salary_growth >= 0
                  ? "text-emerald-600" : "text-red-600"}`}>
                  {d.salary_growth >= 0 ? "+" : ""}
                  {fmt(d.salary_growth)} o'tgan oyga
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">O'quvchilari</p>
                <p className="text-lg font-semibold text-slate-900">
                  {d.students_now}
                </p>
                <p className="text-xs text-slate-400">
                  {d.groups_count} guruh
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">To'lganlik</p>
                <p className="text-lg font-semibold text-slate-900">
                  {d.fill_percent !== null ? `${d.fill_percent}%` : "—"}
                </p>
                <p className="text-xs text-slate-400">
                  {d.total_free !== null
                    ? `${d.total_free} bo'sh joy`
                    : "sig'im yo'q"}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Dars sifati</p>
                <p className="text-lg font-semibold text-slate-900">
                  {d.quality_percent !== null
                    ? `${d.quality_percent}%` : "—"}
                </p>
                <p className="text-xs text-slate-400 flex items-center gap-1">
                  <Award size={11} />
                  {d.grade_label || "daraja yo'q"}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-3 mb-4">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <TrendingUp size={12} /> Oylik o'sishi (6 oy)
                </p>
                <MiniBars data={d.months} val={(m) => m.salary}
                          tone="bg-brand-500" />
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs font-medium text-slate-600 flex items-center gap-1">
                  <TrendingUp size={12} /> O'quvchilar soni (6 oy)
                </p>
                <MiniBars data={d.months} val={(m) => m.students}
                          tone="bg-emerald-500" />
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-3 mb-4 text-sm">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500 flex items-center gap-1 mb-1">
                  <FileText size={11} /> Shartnoma
                </p>
                {d.contract ? (
                  <DaysLeft days={d.contract.days_left} />
                ) : (
                  <span className="text-slate-400">kiritilmagan</span>
                )}
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500 flex items-center gap-1 mb-1">
                  <Award size={11} /> Sertifikat
                </p>
                {d.certificate ? (
                  <>
                    <p className="text-slate-800">{d.certificate.title}</p>
                    <DaysLeft days={d.certificate.days_left} />
                  </>
                ) : (
                  <span className="text-slate-400">kiritilmagan</span>
                )}
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500 flex items-center gap-1 mb-1">
                  <Cake size={11} /> Tug'ilgan kun
                </p>
                {d.birthday ? (
                  d.birthday.passed ? (
                    <span className="text-slate-500">
                      o'tib ketdi ({d.birthday.days} kun oldin)
                    </span>
                  ) : (
                    <span className="text-slate-800">
                      {d.birthday.days} kun qoldi
                    </span>
                  )
                ) : (
                  <span className="text-slate-400">kiritilmagan</span>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs text-slate-500">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium">
                      Guruh
                    </th>
                    <th className="text-right px-3 py-2 font-medium">
                      O'quvchi
                    </th>
                    <th className="text-right px-3 py-2 font-medium">
                      Bo'sh joy
                    </th>
                    <th className="text-right px-3 py-2 font-medium">
                      To'lganlik
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {d.groups.map((g: Any) => (
                    <tr key={g.id}>
                      <td className="px-3 py-2 text-slate-800">{g.name}</td>
                      <td className="px-3 py-2 text-right">{g.students}</td>
                      <td className="px-3 py-2 text-right">
                        {g.free ?? "—"}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {g.fill !== null ? `${g.fill}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {d.groups.length === 0 && (
                <p className="text-sm text-slate-400 py-5 text-center">
                  Guruh biriktirilmagan.
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}


/** Support teacherni guruhlarga biriktirish (support manager /
 *  o'quv bo'limi rahbari). Jadvali va o'quvchilari shundan chiqadi. */
export function SupportGroupsModal({
  teacherId, name, onClose,
}: { teacherId: number; name: string; onClose: () => void }) {
  const [groups, setGroups] = useState<Any[]>([]);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<Any>(`/support-teachers/${teacherId}/groups`)
      .then((r) => { setGroups(r.groups); setSel(new Set(r.assigned)); })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [teacherId]);

  const toggle = (id: number) => {
    const n = new Set(sel);
    if (n.has(id)) n.delete(id); else n.add(id);
    setSel(n);
  };
  const save = async () => {
    setBusy(true);
    try {
      await api.put(`/support-teachers/${teacherId}/groups`,
        { group_ids: [...sel] });
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-sm max-h-[85vh] overflow-auto p-5">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Layers size={16} className="text-slate-400" />
            Support guruhlari
          </h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          {name} — belgilangan guruhlar jadvali va o'quvchilari uning
          kabinetida ko'rinadi.
        </p>
        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <div className="space-y-1 mb-4">
          {groups.map((g) => (
            <label key={g.id}
              className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-50 text-sm text-slate-700 cursor-pointer">
              <input type="checkbox" checked={sel.has(g.id)}
                onChange={() => toggle(g.id)} />
              {g.name}
            </label>
          ))}
          {groups.length === 0 && !err && (
            <p className="text-sm text-slate-400">Guruh topilmadi.</p>
          )}
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600">Bekor</button>
          <button onClick={save} disabled={busy}
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40">
            Saqlash ({sel.size})
          </button>
        </div>
      </div>
    </div>
  );
}
