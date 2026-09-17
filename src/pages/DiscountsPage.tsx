// CHEGIRMALAR BO'LIMI (2026-09-17, Jahongir: "chegirmalar degan
// bo'limni ham qo'shish kerak ... chegirmadagilar korinishi kerak").
// Hamma chegirmalar bitta joyda: kim, qaysi guruh, qancha, nega, kim
// tasdiqlagan va oyiga markaz qancha kam oladi.
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Percent, Search, Download, Check, X } from "lucide-react";
import { api } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { exportToExcel } from "../lib/exportXlsx";

type Row = {
  id: number;
  student_id: number;
  student_name: string;
  student_status: string | null;
  group_id: number | null;
  group: string | null;
  branch: string | null;
  kind: string;
  kind_label: string;
  percent: number | null;
  amount: number | null;
  fee: number;
  monthly: number;
  reason: string | null;
  referrer_name: string | null;
  start_date: string | null;
  end_date: string | null;
  status: string;
  status_label: string;
  alive: boolean;
  requested_by: string | null;
  approved_by: string | null;
  cancelled_reason: string | null;
  created_at: string | null;
};

type Data = {
  rows: Row[];
  summary: {
    students: number;
    active: number;
    monthly: number;
    pending: number;
    by_kind: { kind: string; label: string; count: number; monthly: number }[];
  };
  types: { key: string; label: string }[];
  can_approve: boolean;
};

type View = "alive" | "pending" | "ended" | "all";

const VIEWS: { key: View; label: string }[] = [
  { key: "alive", label: "Amaldagi" },
  { key: "pending", label: "Tasdiq kutayotgan" },
  { key: "ended", label: "Tugagan / bekor" },
  { key: "all", label: "Hammasi" },
];

const STATUS_CLS: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  paused: "bg-sky-50 text-sky-700",
  expired: "bg-slate-100 text-slate-500",
  cancelled: "bg-rose-50 text-rose-600",
};

function size(r: Row) {
  return r.amount ? formatSom(r.amount) : `${r.percent ?? 0}%`;
}

export default function DiscountsPage() {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [view, setView] = useState<View>("alive");
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  const load = () =>
    api.get<Data>("/discounts/overview")
      .then((x) => { setD(x); setErr(""); })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  useEffect(() => { load(); }, []);

  const rows = useMemo(() => {
    if (!d) return [];
    const s = q.trim().toLowerCase();
    return d.rows.filter((r) => {
      if (view === "alive" && !r.alive) return false;
      if (view === "pending" && r.status !== "pending") return false;
      if (view === "ended" && !["expired", "cancelled"].includes(r.status)) return false;
      if (kind && r.kind !== kind) return false;
      if (s && !`${r.student_name} ${r.group ?? ""} ${r.reason ?? ""}`
        .toLowerCase().includes(s)) return false;
      return true;
    });
  }, [d, view, kind, q]);

  const decide = async (id: number, approve: boolean) => {
    let reason: string | undefined;
    if (!approve) {
      const r = prompt("Rad etish sababi:");
      if (r === null) return;
      reason = r.trim() || undefined;
    }
    setBusy(id);
    try {
      await api.post(`/discounts/${id}/approve`, { approve, reason });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  };

  const exportXlsx = () =>
    exportToExcel("chegirmalar", "Chegirmalar", rows.map((r, i) => ({
      "№": i + 1,
      "O'quvchi": r.student_name,
      "Guruh": r.group ?? "",
      "Filial": r.branch ?? "",
      "Turi": r.kind_label,
      "Miqdori": size(r),
      "Oyiga (so'm)": r.monthly,
      "Sabab": r.reason ?? "",
      "Boshlanishi": r.start_date ?? "",
      "Tugashi": r.end_date ?? "",
      "Holati": r.status_label,
      "So'ragan": r.requested_by ?? "",
      "Tasdiqlagan": r.approved_by ?? "",
    })));

  if (err) return <p className="text-sm text-rose-600 py-8">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;
  const sm = d.summary;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
          <Percent size={20} className="text-brand-600" /> Chegirmalar
        </h1>
        <button onClick={exportXlsx}
          className="flex items-center gap-2 border border-slate-300 rounded-lg px-3 py-2 text-sm hover:bg-slate-50">
          <Download size={15} /> Excel
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card label="Chegirmadagi o'quvchilar" value={String(sm.students)} />
        <Card label="Amaldagi chegirmalar" value={String(sm.active)} />
        <Card label="Oyiga kam tushadi (taxminan)" value={formatSom(sm.monthly)}
              tone="text-rose-600" />
        <Card label="Tasdiq kutmoqda" value={String(sm.pending)}
              tone={sm.pending ? "text-amber-600" : undefined} />
      </div>

      {sm.by_kind.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-500 mb-2">Turlar kesimida (amaldagi)</p>
          <div className="flex flex-wrap gap-2">
            {sm.by_kind.map((k) => (
              <button key={k.kind}
                onClick={() => { setKind(kind === k.kind ? "" : k.kind); setView("alive"); }}
                className={`text-left rounded-lg border px-3 py-2 text-sm ${
                  kind === k.kind ? "border-brand-500 bg-brand-50" : "border-slate-200 hover:bg-slate-50"}`}>
                <span className="font-medium text-slate-800">{k.label}</span>
                <span className="block text-xs text-slate-500">
                  {k.count} ta · oyiga {formatSom(k.monthly)}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {VIEWS.map((v) => (
          <button key={v.key} onClick={() => setView(v.key)}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              view === v.key ? "bg-brand-600 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
            {v.label}
            {v.key === "pending" && sm.pending > 0 && (
              <span className="ml-1.5 rounded-full bg-amber-500 text-white text-xs px-1.5">{sm.pending}</span>
            )}
          </button>
        ))}
        <select value={kind} onChange={(e) => setKind(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm bg-white">
          <option value="">Barcha turlar</option>
          {d.types.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
        </select>
        <div className="relative flex-1 min-w-[12rem]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="O'quvchi, guruh yoki sabab"
            className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-1.5 text-sm" />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="text-right px-3 py-2 w-10">№</th>
              <th className="text-left px-3 py-2">O'quvchi</th>
              <th className="text-left px-3 py-2">Guruh</th>
              <th className="text-left px-3 py-2">Turi</th>
              <th className="text-right px-3 py-2">Miqdori</th>
              <th className="text-right px-3 py-2">Oyiga</th>
              <th className="text-left px-3 py-2">Sabab</th>
              <th className="text-left px-3 py-2">Muddati</th>
              <th className="text-left px-3 py-2">Holati</th>
              <th className="text-left px-3 py-2">Kim</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id} className="border-t border-slate-100 align-top">
                <td className="px-3 py-2 text-right text-xs text-slate-400 tabular-nums">{i + 1}</td>
                <td className="px-3 py-2">
                  <Link to={`/students/${r.student_id}`} className="text-brand-700 hover:underline font-medium">
                    {r.student_name}
                  </Link>
                  {r.branch && <span className="block text-xs text-slate-400">{r.branch}</span>}
                </td>
                <td className="px-3 py-2">
                  {r.group_id
                    ? <Link to={`/groups/${r.group_id}`} className="hover:underline">{r.group}</Link>
                    : <span className="text-slate-400">guruhsiz</span>}
                </td>
                <td className="px-3 py-2">
                  {r.kind_label}
                  {r.referrer_name && <span className="block text-xs text-slate-400">do'sti: {r.referrer_name}</span>}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{size(r)}</td>
                <td className="px-3 py-2 text-right tabular-nums text-rose-600">
                  {r.monthly ? `−${formatSom(r.monthly)}` : "—"}
                </td>
                <td className="px-3 py-2 max-w-[16rem] text-slate-600">
                  {r.reason || "—"}
                  {r.cancelled_reason && (
                    <span className="block text-xs text-rose-500">bekor: {r.cancelled_reason}</span>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
                  {r.start_date ? formatDate(r.start_date) : "—"}
                  {" → "}
                  {r.end_date ? formatDate(r.end_date) : "muddatsiz"}
                </td>
                <td className="px-3 py-2">
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs ${STATUS_CLS[r.status] ?? "bg-slate-100 text-slate-600"}`}>
                    {r.status_label}
                  </span>
                  {r.status === "pending" && d.can_approve && (
                    <div className="flex gap-1 mt-1">
                      <button disabled={busy === r.id} onClick={() => decide(r.id, true)}
                        className="flex items-center gap-1 rounded bg-emerald-600 text-white text-xs px-2 py-1 disabled:opacity-50">
                        <Check size={12} /> Tasdiqlash
                      </button>
                      <button disabled={busy === r.id} onClick={() => decide(r.id, false)}
                        className="flex items-center gap-1 rounded border border-rose-300 text-rose-600 text-xs px-2 py-1 disabled:opacity-50">
                        <X size={12} /> Rad
                      </button>
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-slate-500">
                  {r.requested_by && <span className="block">so'radi: {r.requested_by}</span>}
                  {r.approved_by && <span className="block">tasdiqladi: {r.approved_by}</span>}
                  {!r.requested_by && !r.approved_by && "—"}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={10} className="px-3 py-8 text-center text-slate-400">
                  Bu bo'limda chegirma yo'q.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400">
        "Oyiga" — o'quvchi guruhining oylik narxidan hisoblangan taxminiy
        summa. Yangi chegirma o'quvchi sahifasidagi "Chegirmalar" qismidan
        so'raladi.
      </p>
    </div>
  );
}

function Card({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-lg font-semibold mt-1 ${tone ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}
