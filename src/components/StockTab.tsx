import { Fragment, useEffect, useMemo, useState } from "react";
import {
  Plus, X, AlertTriangle, ShoppingCart, Search, Pencil, History,
  ArrowDownCircle, ArrowUpCircle, Trash2, ClipboardCheck, Layers,
  HelpCircle, ChevronDown, ChevronRight, Loader2,
} from "lucide-react";
import {
  api, type Branch, type ConsumableList, type ConsumableRow,
  type StockMoveRow,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { ORG_WIDE_ROLES } from "../lib/roles";
import { formatSom, formatDate } from "../lib/format";
import { branchParam } from "./BranchPicker";

/**
 * SARFLANADIGAN MAHSULOTLAR (kitob, marker, qog'oz...) — 2026-10-14 da
 * qayta qurildi. Jahongir: "omborda mahsulotlar juda tartibsiz,
 * takrorlari ko'p ... ishlatishga oson qil".
 *
 * Nima o'zgardi:
 *  - "Barcha filiallar"da bir kitob har filial uchun alohida qator
 *    bo'lib, filial nomisiz chiqardi — takrordek ko'rinardi. Endi bitta
 *    qator, ichida filiallar kesimi.
 *  - Haqiqiy takrorlar (bir filialda "Step 1" va "step-1") bitta
 *    tugma bilan birlashtiriladi, yangisi ochilmaydi.
 *  - "Tuzatish (+/-)" o'rniga "Sanoq": polkada nechta borligini yozasiz.
 *  - Yangi mahsulot filialsiz ochilmaydi.
 */

type Kind = { key: string; label: string; unit: string };
type DupRow = {
  id: number; name: string; kind_label: string; qty: number; unit: string;
  min_qty: number; unit_price: number | null; moves: number;
};
type DupGroup = {
  branch_id: number | null; branch: string; name: string; keep_id: number;
  total_qty: number; rows: DupRow[];
};

/** Backend dagi _norm_name bilan bir xil kalit */
const normKey = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
const fmtQty = (n: number) => Number.isInteger(n) ? String(n) : n.toFixed(1);

export function StockTab({ branchId }: { branchId: number | null }) {
  const [data, setData] = useState<ConsumableList | null>(null);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("");
  const [lowOnly, setLowOnly] = useState(false);
  const [openKey, setOpenKey] = useState<string | null>(null);
  const [history, setHistory] = useState<number | null>(null);
  const [move, setMove] = useState<ConsumableRow | null>(null);
  const [edit, setEdit] = useState<ConsumableRow | "new" | null>(null);
  const [merge, setMerge] = useState(false);
  const [help, setHelp] = useState(() => {
    try { return localStorage.getItem("jonyos_stock_help") !== "0"; } catch { return true; }
  });

  function load() {
    setLoading(true);
    api.get<ConsumableList>(`/consumables?x=1${branchParam(branchId)}`, true)
      .then(setData)
      .finally(() => setLoading(false));
  }
  useEffect(load, [branchId]);

  const toggleHelp = () => {
    setHelp(!help);
    try { localStorage.setItem("jonyos_stock_help", help ? "0" : "1"); } catch { /* */ }
  };

  const filtered = useMemo(() => {
    if (!data) return [];
    const nq = normKey(q);
    return data.rows.filter((r) =>
      (!nq || normKey(r.name).includes(nq))
      && (!kind || r.kind === kind)
      && (!lowOnly || r.low));
  }, [data, q, kind, lowOnly]);

  // Bir nechta filial bo'lsa — nom bo'yicha guruhlanadi
  const multiBranch = useMemo(
    () => new Set((data?.rows || []).map((r) => r.branch_id ?? 0)).size > 1,
    [data]);
  const groups = useMemo(() => {
    const m = new Map<string, ConsumableRow[]>();
    filtered.forEach((r) => {
      const k = normKey(r.name);
      m.set(k, [...(m.get(k) || []), r]);
    });
    return [...m.entries()]
      .map(([key, rows]) => ({
        key, rows,
        name: rows[0].name,
        kind_label: rows[0].kind_label,
        unit: rows[0].unit,
        qty: rows.reduce((s, r) => s + (r.qty || 0), 0),
        value: rows.reduce((s, r) => s + (r.value || 0), 0),
        low: rows.some((r) => r.low),
      }))
      .sort((a, b) => a.kind_label.localeCompare(b.kind_label) || a.name.localeCompare(b.name));
  }, [filtered]);

  if (loading && !data) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;
  const usedKinds = data.kinds.filter((k) => data.rows.some((r) => r.kind === k.key));

  return (
    <div>
      {/* Qanday ishlaydi */}
      <div className="bg-white border border-slate-200 rounded-xl mb-4">
        <button onClick={toggleHelp} className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700">
          <HelpCircle size={15} className="text-brand-600" />
          <span className="font-medium">Ombor qanday ishlaydi?</span>
          <ChevronDown size={15} className={`ml-auto text-slate-400 transition ${help ? "rotate-180" : ""}`} />
        </button>
        {help && (
          <div className="px-4 pb-4 text-sm text-slate-600 grid sm:grid-cols-2 gap-x-6 gap-y-2">
            <p><b>1. Mahsulot bir marta ochiladi</b> — har filialda bittadan. "Step 1" bor bo'lsa, qaytadan ochmang: tizim ruxsat bermaydi.</p>
            <p><b>2. Qoldiq faqat harakat bilan o'zgaradi:</b> <span className="text-emerald-700">Kirim</span> (keldi), <span className="text-red-600">Chiqim</span> (berildi / ishlatildi), <span className="text-slate-700">Hisobdan chiqarish</span> (yo'qoldi, yaroqsiz).</p>
            <p><b>3. Sanoq</b> — oyda bir marta polkani sanab, nechta borligini yozing. Farqni tizim o'zi tuzatadi va tarixda qoldiradi.</p>
            <p><b>4. Avtomatik:</b> to'lovda "kitob berildi" desa — chiqim; Moliyada kitob xarajati — kirim. Kirimni filial rahbari "Qabul qilib oldim" deb tasdiqlaydi.</p>
            <p><b>5. Minimal qoldiq</b> qo'ysangiz, undan kamaysa xarid so'rovi o'zi ochiladi. 0 — kuzatilmaydi.</p>
            <p><b>6. Takror bo'lsa</b> — sariq "Birlashtirish" tugmasi: qoldiqlar qo'shiladi, tarix yo'qolmaydi.</p>
          </div>
        )}
      </div>

      {(data.duplicates ?? 0) > 0 && data.can_edit && (
        <div className="flex flex-wrap items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-4">
          <Layers size={16} className="text-amber-600" />
          <p className="text-sm text-amber-900 flex-1">
            <b>{data.duplicates} ta takror mahsulot</b> topildi — bir filialda bir xil nom bilan bir necha marta ochilgan.
          </p>
          <button onClick={() => setMerge(true)} className="px-3 py-1.5 rounded-lg bg-amber-600 text-white text-sm font-medium hover:bg-amber-700">
            Ko'rib, birlashtirish
          </button>
        </div>
      )}

      {data.requests.length > 0 && (
        <Requests data={data} onDone={load} />
      )}

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Stat label="Mahsulot turlari" value={String(groups.length)} />
        <Stat label="Ombor qiymati" value={formatSom(data.total_value)} />
        <button onClick={() => setLowOnly(!lowOnly)}
          className={`text-left rounded-xl border p-3.5 ${data.low_count > 0 ? "bg-red-50 border-red-200" : "bg-white border-slate-200"} ${lowOnly ? "ring-2 ring-red-300" : ""}`}>
          <p className="text-xs text-slate-500 mb-0.5">Kam qolgan {lowOnly && "· filtr"}</p>
          <p className={`text-xl font-semibold ${data.low_count > 0 ? "text-red-700" : "text-slate-900"}`}>{data.low_count}</p>
        </button>
      </div>

      {/* Qidiruv va filtr */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Qidirish..."
            className="pl-8 pr-3 py-2 w-48 sm:w-56 rounded-lg border border-slate-200 text-sm" />
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Chip on={!kind} onClick={() => setKind("")}>Hammasi</Chip>
          {usedKinds.map((k) => (
            <Chip key={k.key} on={kind === k.key} onClick={() => setKind(kind === k.key ? "" : k.key)}>{k.label}</Chip>
          ))}
        </div>
        {data.can_edit && (
          <button onClick={() => setEdit("new")}
            className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700">
            <Plus size={15} /> Yangi mahsulot
          </button>
        )}
      </div>

      {groups.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          {data.rows.length ? "Bu filtr bo'yicha mahsulot yo'q." : "Mahsulot yo'q."}
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-xs text-slate-500">
                <th className="text-left px-4 py-2.5">Nomi</th>
                <th className="text-left">Turi</th>
                {multiBranch && <th className="text-left">Filiallar</th>}
                <th className="text-right w-24">Qoldiq</th>
                {!multiBranch && <th className="text-right w-20">Minimal</th>}
                <th className="text-right w-28">Qiymati</th>
                <th className="w-44" />
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => {
                const single = !multiBranch || g.rows.length === 1;
                const r0 = g.rows[0];
                const opened = openKey === g.key;
                return (
                  <Fragment key={g.key}>
                    <tr className={`border-t border-slate-100 ${g.low ? "bg-red-50/40" : ""}`}>
                      <td className="px-4 py-2.5">
                        <button
                          onClick={() => multiBranch && g.rows.length > 1
                            ? setOpenKey(opened ? null : g.key)
                            : setHistory(history === r0.id ? null : r0.id)}
                          className="inline-flex items-center gap-1 text-slate-800 hover:text-brand-700 text-left"
                        >
                          {multiBranch && g.rows.length > 1 && (
                            <ChevronRight size={14} className={`text-slate-400 transition ${opened ? "rotate-90" : ""}`} />
                          )}
                          {g.name}
                        </button>
                        {g.low && <AlertTriangle size={12} className="inline ml-1.5 text-red-500" />}
                      </td>
                      <td className="text-slate-500">{g.kind_label}</td>
                      {multiBranch && (
                        <td className="text-xs text-slate-500">
                          {g.rows.map((r) => (
                            <span key={r.id} className={`inline-block mr-1.5 mb-0.5 px-1.5 py-0.5 rounded ${r.low ? "bg-red-100 text-red-700" : (r.qty || 0) > 0 ? "bg-slate-100 text-slate-700" : "bg-slate-50 text-slate-400"}`}>
                              {r.branch || "Umumiy"}: {fmtQty(r.qty || 0)}
                            </span>
                          ))}
                        </td>
                      )}
                      <td className={`text-right font-medium ${g.low ? "text-red-600" : "text-slate-700"}`}>
                        {fmtQty(g.qty)} {g.unit}
                      </td>
                      {!multiBranch && <td className="text-right text-slate-400">{r0.min_qty || "—"}</td>}
                      <td className="text-right text-slate-600">{g.value ? formatSom(g.value) : "—"}</td>
                      <td className="pr-3 text-right whitespace-nowrap">
                        {single ? (
                          <RowActions r={r0} canEdit={data.can_edit}
                            onMove={() => setMove(r0)} onEdit={() => setEdit(r0)}
                            onHistory={() => setHistory(history === r0.id ? null : r0.id)} />
                        ) : (
                          <button onClick={() => setOpenKey(opened ? null : g.key)} className="text-xs text-brand-600 hover:underline">
                            {opened ? "yopish" : "filiallar bo'yicha"}
                          </button>
                        )}
                      </td>
                    </tr>
                    {single && history === r0.id && (
                      <tr><td colSpan={7} className="bg-slate-50 px-4 py-3"><Moves id={r0.id} /></td></tr>
                    )}
                    {!single && opened && g.rows.map((r) => (
                      <Fragment key={r.id}>
                        <tr className="bg-slate-50/70 border-t border-slate-100">
                          <td className="pl-10 py-2 text-slate-600" colSpan={2}>
                            {r.branch || "Umumiy (filialsiz)"}
                            {r.name !== g.name && <span className="text-xs text-slate-400"> · {r.name}</span>}
                            {r.low && <AlertTriangle size={11} className="inline ml-1.5 text-red-500" />}
                          </td>
                          <td className="text-xs text-slate-400">{r.min_qty ? `minimal ${r.min_qty}` : ""}</td>
                          <td className={`text-right ${r.low ? "text-red-600" : "text-slate-700"}`}>{fmtQty(r.qty || 0)} {r.unit}</td>
                          <td className="text-right text-slate-500">{r.value ? formatSom(r.value) : "—"}</td>
                          <td className="pr-3 text-right whitespace-nowrap">
                            <RowActions r={r} canEdit={data.can_edit}
                              onMove={() => setMove(r)} onEdit={() => setEdit(r)}
                              onHistory={() => setHistory(history === r.id ? null : r.id)} />
                          </td>
                        </tr>
                        {history === r.id && (
                          <tr><td colSpan={7} className="bg-slate-50 px-10 py-3"><Moves id={r.id} /></td></tr>
                        )}
                      </Fragment>
                    ))}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {move && <MoveDialog c={move} onClose={() => setMove(null)} onDone={() => { setMove(null); load(); }} />}
      {edit && (
        <ProductForm
          item={edit === "new" ? null : edit}
          kinds={data.kinds}
          defaultBranch={branchId}
          onClose={() => setEdit(null)}
          onSaved={() => { setEdit(null); load(); }}
        />
      )}
      {merge && <MergeDialog branchId={branchId} onClose={() => setMerge(false)} onDone={() => { setMerge(false); load(); }} />}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3.5">
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className="text-xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`px-2.5 py-1 rounded-full text-xs border ${on ? "bg-slate-800 text-white border-slate-800" : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"}`}>
      {children}
    </button>
  );
}

function RowActions({ r, canEdit, onMove, onEdit, onHistory }: {
  r: ConsumableRow; canEdit: boolean; onMove: () => void; onEdit: () => void; onHistory: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1">
      {canEdit && (
        <button onClick={onMove} className="px-2 py-1 rounded-md text-xs font-medium bg-brand-50 text-brand-700 hover:bg-brand-100">
          Kirim / chiqim
        </button>
      )}
      <button onClick={onHistory} title="Harakatlar tarixi" className="p-1.5 text-slate-400 hover:text-slate-700"><History size={14} /></button>
      {canEdit && (
        <button onClick={onEdit} title={`Tahrirlash${r.branch ? ` (${r.branch})` : ""}`} className="p-1.5 text-slate-400 hover:text-brand-600"><Pencil size={13} /></button>
      )}
    </span>
  );
}

// ------------------------------------------------------------- harakat
const MOVE_TYPES = [
  { key: "in", label: "Kirim", hint: "keldi, sotib olindi", icon: ArrowDownCircle, tone: "emerald" },
  { key: "out", label: "Chiqim", hint: "o'quvchiga berildi, ishlatildi", icon: ArrowUpCircle, tone: "red" },
  { key: "write_off", label: "Hisobdan chiqarish", hint: "yo'qoldi, yirtildi, yaroqsiz", icon: Trash2, tone: "slate" },
  { key: "count", label: "Sanoq", hint: "polkada aslida nechta bor", icon: ClipboardCheck, tone: "sky" },
] as const;
const MOVE_TONE: Record<string, string> = {
  emerald: "border-emerald-500 bg-emerald-50 text-emerald-800",
  red: "border-red-500 bg-red-50 text-red-800",
  slate: "border-slate-500 bg-slate-100 text-slate-800",
  sky: "border-sky-500 bg-sky-50 text-sky-800",
};

function MoveDialog({ c, onClose, onDone }: { c: ConsumableRow; onClose: () => void; onDone: () => void }) {
  const [type, setType] = useState<string>("in");
  const [qty, setQty] = useState("");
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const n = Number(qty);
  const now = c.qty || 0;
  const after = !qty || isNaN(n) ? null
    : type === "in" ? now + Math.abs(n)
    : type === "count" ? n
    : now - Math.abs(n);

  async function save() {
    if (!qty || isNaN(n) || (type !== "count" && n <= 0) || n < 0) {
      setErr(type === "count" ? "Polkada nechta borligini yozing" : "Miqdorni kiriting");
      return;
    }
    if (after !== null && after < 0) {
      setErr(`Omborda ${fmtQty(now)} ${c.unit} bor — buncha chiqarib bo'lmaydi`);
      return;
    }
    setBusy(true); setErr("");
    try {
      await api.post(`/consumables/${c.id}/move`, { reason: type, qty: n, note: note.trim() || null });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={c.name} sub={`${c.branch || "Umumiy"} · hozir ${fmtQty(now)} ${c.unit}`} onClose={onClose}>
      <div className="grid grid-cols-2 gap-2 mb-3">
        {MOVE_TYPES.map((t) => {
          const Icon = t.icon;
          const on = type === t.key;
          return (
            <button key={t.key} onClick={() => setType(t.key)}
              className={`text-left rounded-lg border-2 px-3 py-2 ${on ? MOVE_TONE[t.tone] : "border-slate-200 text-slate-600 hover:border-slate-300"}`}>
              <span className="flex items-center gap-1.5 text-sm font-medium"><Icon size={15} />{t.label}</span>
              <span className="block text-[11px] opacity-75 mt-0.5">{t.hint}</span>
            </button>
          );
        })}
      </div>
      <label className="block text-xs text-slate-500 mb-1">
        {type === "count" ? `Polkada aslida nechta ${c.unit} bor?` : `Necha ${c.unit}?`}
      </label>
      <input type="number" min={0} value={qty} autoFocus onChange={(e) => setQty(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && save()}
        className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm mb-2" />
      <input value={note} onChange={(e) => setNote(e.target.value)}
        placeholder={type === "out" ? "Izoh: kimga berildi (ixtiyoriy)" : "Izoh (ixtiyoriy)"}
        className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm mb-3" />
      {after !== null && (
        <p className={`text-sm mb-3 ${after < 0 ? "text-red-600" : "text-slate-600"}`}>
          Qoldiq: <b>{fmtQty(now)}</b> → <b>{fmtQty(after)}</b> {c.unit}
          {type === "count" && after !== now && (
            <span className="text-slate-400"> (farq {after > now ? "+" : ""}{fmtQty(after - now)})</span>
          )}
        </p>
      )}
      {type === "in" && (
        <p className="text-xs text-slate-400 mb-3">Kirimni keyin filial rahbari "Qabul qilib oldim" deb tasdiqlaydi.</p>
      )}
      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
      <button onClick={save} disabled={busy}
        className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
        Saqlash
      </button>
    </Modal>
  );
}

function Moves({ id }: { id: number }) {
  const [rows, setRows] = useState<StockMoveRow[] | null>(null);
  useEffect(() => {
    api.get<StockMoveRow[]>(`/consumables/${id}/moves`, true).then(setRows).catch(() => setRows([]));
  }, [id]);
  if (rows === null) return <p className="text-xs text-slate-400">Yuklanmoqda...</p>;
  if (rows.length === 0) return <p className="text-xs text-slate-400">Hali harakat yo'q</p>;
  return (
    <div className="space-y-1">
      {rows.map((m) => (
        <div key={m.id} className="flex flex-wrap items-center gap-x-3 text-xs">
          <span className="text-slate-400 w-24">{m.created_at ? formatDate(m.created_at.slice(0, 10)) : "—"}</span>
          <span className={`w-12 font-medium ${m.delta > 0 ? "text-emerald-600" : "text-red-600"}`}>
            {m.delta > 0 ? "+" : ""}{fmtQty(m.delta)}
          </span>
          <span className="text-slate-500 w-48 truncate">{m.reason_label}</span>
          <span className="text-slate-600 flex-1 min-w-0">{m.note}</span>
          <span className="text-slate-400">{m.by}</span>
        </div>
      ))}
    </div>
  );
}

// ------------------------------------------------------- xarid so'rovlari
function Requests({ data, onDone }: { data: ConsumableList; onDone: () => void }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <ShoppingCart size={15} className="text-amber-600" />
        <p className="text-sm font-medium text-amber-900">{data.requests.length} ta xarid so'rovi</p>
        <span className="text-xs text-amber-700">qoldiq minimaldan kamaydi — sotib olish kerak</span>
      </div>
      <div className="space-y-1.5">
        {data.requests.map((r) => (
          <div key={r.id} className="flex flex-wrap items-center gap-3 text-sm">
            <span className="text-amber-900 flex-1">{r.name}</span>
            <span className="text-amber-800">{fmtQty(r.qty)} dona kerak</span>
            {data.can_edit && (
              <>
                <button
                  onClick={async () => {
                    const v = prompt("Nechta keldi?", String(r.qty));
                    if (!v) return;
                    await api.post(`/purchase-requests/${r.id}/close`, { status: "done", qty: Number(v) });
                    onDone();
                  }}
                  className="text-xs px-2 py-1 rounded-md bg-emerald-600 text-white">
                  Keldi
                </button>
                <button
                  onClick={async () => {
                    await api.post(`/purchase-requests/${r.id}/close`, { status: "cancelled" });
                    onDone();
                  }}
                  className="text-xs text-amber-700 hover:underline">
                  kerak emas
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------- mahsulot formasi
function ProductForm({ item, kinds, defaultBranch, onClose, onSaved }: {
  item: ConsumableRow | null; kinds: Kind[]; defaultBranch: number | null;
  onClose: () => void; onSaved: () => void;
}) {
  const { user } = useAuth();
  const orgWide = !!user?.role && ORG_WIDE_ROLES.includes(user.role);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [name, setName] = useState(item?.name || "");
  const [kind, setKind] = useState(item?.kind || "book");
  const [branch, setBranch] = useState<string>(String(item?.branch_id ?? defaultBranch ?? ""));
  const [qty, setQty] = useState("");
  const [min, setMin] = useState(item?.min_qty ? String(item.min_qty) : "");
  const [price, setPrice] = useState(item?.unit_price ? String(item.unit_price) : "");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (orgWide && !item) api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, [orgWide, item]);

  async function save() {
    if (!name.trim()) { setErr("Nomini yozing"); return; }
    if (!item && orgWide && !branch) { setErr("Qaysi filial ombori ekanini tanlang"); return; }
    setBusy(true); setErr("");
    try {
      const body = {
        name: name.trim(), kind,
        min_qty: Number(min) || 0,
        unit_price: price ? Number(price) : null,
      };
      if (item) await api.put(`/consumables/${item.id}`, body);
      else await api.post("/consumables", { ...body, qty: Number(qty) || 0, branch_id: branch ? Number(branch) : null });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={item ? "Mahsulotni tahrirlash" : "Yangi mahsulot"} sub={item?.branch || undefined} onClose={onClose}>
      <div className="space-y-3">
        <input value={name} onChange={(e) => setName(e.target.value)} autoFocus
          placeholder="Nomi (masalan: Round-up 2)"
          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs text-slate-500">Turi
            <select value={kind} onChange={(e) => setKind(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white">
              {kinds.map((k) => <option key={k.key} value={k.key}>{k.label}</option>)}
            </select>
          </label>
          {!item && orgWide && (
            <label className="block text-xs text-slate-500">Filial ombori
              <select value={branch} onChange={(e) => setBranch(e.target.value)}
                className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white">
                <option value="">— tanlang —</option>
                {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </label>
          )}
        </div>
        <div className="grid grid-cols-3 gap-3">
          {!item && (
            <label className="block text-xs text-slate-500">Hozir bor
              <input type="number" min={0} value={qty} onChange={(e) => setQty(e.target.value)}
                className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
            </label>
          )}
          <label className="block text-xs text-slate-500">Minimal qoldiq
            <input type="number" min={0} value={min} onChange={(e) => setMin(e.target.value)} placeholder="0"
              className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </label>
          <label className="block text-xs text-slate-500">Bittasining narxi
            <input type="number" min={0} value={price} onChange={(e) => setPrice(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </label>
        </div>
        <p className="text-xs text-slate-400">
          {item ? "Qoldiq bu yerda o'zgarmaydi — buning uchun \"Kirim / chiqim\" yoki \"Sanoq\"."
            : "Minimal qoldiqdan kamaysa xarid so'rovi o'zi ochiladi. 0 — kuzatilmaydi."}
        </p>
        {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{err}</p>}
        <button onClick={save} disabled={busy}
          className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
          Saqlash
        </button>
      </div>
    </Modal>
  );
}

// ----------------------------------------------- takrorlarni birlashtirish
function MergeDialog({ branchId, onClose, onDone }: {
  branchId: number | null; onClose: () => void; onDone: () => void;
}) {
  const [groups, setGroups] = useState<DupGroup[] | null>(null);
  const [keep, setKeep] = useState<Record<string, number>>({});
  const [names, setNames] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState("");

  const load = () =>
    api.get<{ groups: DupGroup[] }>(`/consumables/duplicates?x=1${branchParam(branchId)}`, true)
      .then((d) => {
        setGroups(d.groups);
        setKeep(Object.fromEntries(d.groups.map((g) => [gk(g), g.keep_id])));
        setNames(Object.fromEntries(d.groups.map((g) => [gk(g), g.name])));
      })
      .catch((e) => setErr(e.message));
  useEffect(() => { load(); }, [branchId]); // eslint-disable-line react-hooks/exhaustive-deps

  const gk = (g: DupGroup) => `${g.branch_id ?? 0}:${g.rows.map((r) => r.id).join(",")}`;

  async function doMerge(g: DupGroup) {
    const k = gk(g);
    const keepId = keep[k];
    const others = g.rows.filter((r) => r.id !== keepId).map((r) => r.id);
    setBusy(k); setErr("");
    try {
      await api.post("/consumables/merge", { keep_id: keepId, merge_ids: others, name: names[k] });
      const rest = (groups || []).filter((x) => gk(x) !== k);
      setGroups(rest);
      if (!rest.length) onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Modal title="Takrorlarni birlashtirish" wide
      sub="Bir filialda bir xil nomli mahsulotlar bitta bo'ladi. Qoldiqlar qo'shiladi, tarix yo'qolmaydi."
      onClose={() => (groups && groups.length === 0 ? onDone() : onClose())}>
      {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{err}</p>}
      {!groups ? (
        <div className="py-8 flex justify-center text-slate-400"><Loader2 className="animate-spin" /></div>
      ) : groups.length === 0 ? (
        <p className="text-sm text-emerald-700 py-6 text-center">Takror qolmadi ✓</p>
      ) : (
        <div className="space-y-3">
          {groups.map((g) => {
            const k = gk(g);
            return (
              <div key={k} className="border border-slate-200 rounded-xl p-3">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{g.branch}</span>
                  <span className="text-xs text-slate-500">Jami qoldiq: <b>{fmtQty(g.total_qty)}</b></span>
                </div>
                <div className="space-y-1 mb-2.5">
                  {g.rows.map((r) => (
                    <label key={r.id} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input type="radio" name={k} checked={keep[k] === r.id}
                        onChange={() => setKeep({ ...keep, [k]: r.id })} />
                      <span className="font-medium text-slate-800">{r.name}</span>
                      <span className="text-xs text-slate-500">
                        {r.kind_label} · {fmtQty(r.qty)} {r.unit} · {r.moves} harakat
                        {r.unit_price ? ` · ${formatSom(r.unit_price)}` : ""}
                      </span>
                      {keep[k] === r.id && <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">QOLADI</span>}
                    </label>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <input value={names[k] || ""} onChange={(e) => setNames({ ...names, [k]: e.target.value })}
                    className="flex-1 min-w-40 px-2.5 py-1.5 rounded-lg border border-slate-200 text-sm" title="Yakuniy nomi" />
                  <button onClick={() => doMerge(g)} disabled={busy === k}
                    className="px-3 py-1.5 rounded-lg bg-amber-600 text-white text-sm font-medium hover:bg-amber-700 disabled:opacity-50">
                    {busy === k ? "..." : `${g.rows.length} tasini bitta qilish`}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Modal>
  );
}

function Modal({ title, sub, wide, onClose, children }: {
  title: string; sub?: string; wide?: boolean; onClose: () => void; children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-12 sm:pt-20 overflow-y-auto">
      <div className={`bg-white rounded-xl w-full ${wide ? "max-w-2xl" : "max-w-md"} p-5 shadow-xl`}>
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="min-w-0">
            <h3 className="font-semibold text-slate-800">{title}</h3>
            {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}
