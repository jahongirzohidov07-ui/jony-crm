import { useState } from "react";
import { Upload, X, AlertTriangle, CheckCircle2 } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;
type Item = { name: string; kind: string; date: string; points?: number };

/**
 * Na'munali xodim: "Na'munali xodim.xlsx" jadvalini import qilish
 * (2026-09-16, Jahongir: "Exceldagi ma'lumotlarni ham qo'shib ber").
 *
 * Fayl brauzerda o'qiladi:
 *   "setup" varag'i — A: sana, B: kech kelish, C: ziddiyat sababchi,
 *     D: ziddiyat qatnashchi, E: beyjik, F: manualga amal qilmaslik;
 *   birinchi varaq — B: xodim, E: "xayfsan uchun" bali.
 * Server ismlarni xodimlarga moslaydi; mos kelmaganini HR o'zi tanlaydi.
 * Qayta import qilinsa, yozuvlar takrorlanmaydi.
 */

const SETUP_COLS: [number, string][] = [
  [1, "late"], [2, "conflict_cause"], [3, "conflict_part"],
  [4, "badge"], [5, "manual"],
];

const pad = (n: number) => String(n).padStart(2, "0");

/** Excel sanasi (seriya raqami, Date yoki matn) -> "YYYY-MM-DD". */
function excelDate(v: unknown): string | null {
  if (typeof v === "number" && v > 0) {
    const d = new Date(Date.UTC(1899, 11, 30) + Math.round(v) * 86400000);
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
  }
  if (v instanceof Date && !Number.isNaN(v.getTime())) {
    return `${v.getFullYear()}-${pad(v.getMonth() + 1)}-${pad(v.getDate())}`;
  }
  if (typeof v === "string") {
    const m = v.trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) return `${m[1]}-${m[2]}-${m[3]}`;
    const m2 = v.trim().match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/);
    if (m2) return `${m2[3]}-${pad(Number(m2[2]))}-${pad(Number(m2[1]))}`;
  }
  return null;
}

async function parseWorkbook(f: File): Promise<Item[]> {
  const XLSX = await import("xlsx");
  const wb = XLSX.read(await f.arrayBuffer());
  const setupName = wb.SheetNames.find(
    (n) => n.trim().toLowerCase() === "setup");
  if (!setupName) {
    throw new Error("Faylda \"setup\" varag'i topilmadi");
  }
  const rows = (ws: Any): unknown[][] =>
    XLSX.utils.sheet_to_json(ws, { header: 1, raw: true, blankrows: false });

  const setup = rows(wb.Sheets[setupName]);
  const head = String(setup[0]?.[1] ?? "").toLowerCase();
  if (!head.includes("kech")) {
    throw new Error(
      "\"setup\" varag'i kutilgan tuzilishda emas (B ustuni — kech kelish)");
  }
  const items: Item[] = [];
  for (const r of setup.slice(2)) {
    const date = excelDate(r[0]);
    if (!date) continue;
    for (const [col, kind] of SETUP_COLS) {
      const name = String(r[col] ?? "").trim();
      if (name) items.push({ name, kind, date });
    }
  }

  // Xayfsan ballari — asosiy varaqning E ustuni. Sanasi yo'q, shuning
  // uchun yilning 1-yanvari bilan yoziladi.
  const mainName = wb.SheetNames.find(
    (n) => n !== setupName && n.trim().toLowerCase() !== "jazo");
  if (mainName) {
    const year = items.length
      ? items.map((i) => i.date).sort()[0].slice(0, 4)
      : String(new Date().getFullYear());
    for (const r of rows(wb.Sheets[mainName]).slice(1)) {
      const name = String(r[1] ?? "").trim();
      const pts = Number(r[4]);
      if (name && Number.isFinite(pts) && pts !== 0) {
        items.push({ name, kind: "reprimand", date: `${year}-01-01`, points: pts });
      }
    }
  }
  if (!items.length) throw new Error("Faylda import qilinadigan yozuv yo'q");
  return items;
}

const STATUS: Record<string, { label: string; tone: string }> = {
  matched: { label: "Topildi", tone: "text-emerald-700" },
  mapped: { label: "Qo'lda tanlandi", tone: "text-emerald-700" },
  unmatched: { label: "Topilmadi", tone: "text-red-600" },
  ambiguous: { label: "Bir nechta mos xodim", tone: "text-amber-600" },
  skipped: { label: "O'tkazib yuboriladi", tone: "text-slate-400" },
};

export function ConductImport({
  onClose, onDone,
}: {
  onClose: () => void;
  onDone: () => void;
}) {
  const [items, setItems] = useState<Item[] | null>(null);
  const [fileName, setFileName] = useState("");
  const [mapping, setMapping] = useState<Record<string, number>>({});
  const [res, setRes] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const check = async (its: Item[], map: Record<string, number>,
                       apply = false) => {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<Any>("/conduct/import",
                                    { items: its, mapping: map, apply });
      setRes(r);
      if (apply) onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const pick = async (f: File | undefined) => {
    if (!f) return;
    setErr("");
    setRes(null);
    setMapping({});
    setFileName(f.name);
    try {
      const its = await parseWorkbook(f);
      setItems(its);
      await check(its, {});
    } catch (e) {
      setItems(null);
      setErr(e instanceof Error ? e.message : "Faylni o'qib bo'lmadi");
    }
  };

  const setMap = (name: string, v: string) => {
    const next = { ...mapping };
    if (v === "") delete next[name];
    else next[name] = Number(v);
    setMapping(next);
    if (items) check(items, next);
  };

  const unresolved = (res?.names || []).filter(
    (n: Any) => n.status === "unmatched" || n.status === "ambiguous");

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-3xl my-8">
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
          <p className="font-semibold text-slate-900">Excel'dan import</p>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 p-1">
            <X size={18} />
          </button>
        </div>
        <div className="p-5">
          <p className="text-sm text-slate-500 mb-3">
            "Na'munali xodim" Excel faylini tanlang. "setup" varag'idagi har bir
            qoidabuzarlik va "xayfsan uchun" ballari qo'shiladi. Ball tizim
            qoidasi bo'yicha qayta hisoblanadi. Qayta import qilinsa,
            yozuvlar takrorlanmaydi.
          </p>
          <label className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer">
            <Upload size={15} />
            {fileName || "Faylni tanlash (.xlsx)"}
            <input
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                pick(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </label>

          {err && (
            <p className="text-sm text-red-600 mt-3 flex items-start gap-1.5">
              <AlertTriangle size={15} className="shrink-0 mt-0.5" /> {err}
            </p>
          )}
          {busy && <p className="text-sm text-slate-400 mt-3">Tekshirilmoqda…</p>}

          {res && (
            <>
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="text-xs text-slate-500">Fayldagi yozuvlar</p>
                  <p className="text-lg font-semibold text-slate-900">{res.total}</p>
                </div>
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="text-xs text-slate-500">
                    {res.applied ? "Qo'shildi" : "Qo'shiladi"}
                  </p>
                  <p className="text-lg font-semibold text-emerald-700">
                    {res.applied ? res.added : res.to_add}
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 p-3">
                  <p className="text-xs text-slate-500">Avval import qilingan</p>
                  <p className="text-lg font-semibold text-slate-500">{res.already}</p>
                </div>
              </div>

              <div className="mt-4 border border-slate-200 rounded-lg overflow-x-auto max-h-[45vh]">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-slate-500 text-xs sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium">Excel'dagi ism</th>
                      <th className="text-right px-3 py-2 font-medium">Yozuv</th>
                      <th className="text-left px-3 py-2 font-medium">Holat</th>
                      <th className="text-left px-3 py-2 font-medium">Tizimdagi xodim</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {res.names.map((n: Any) => (
                      <tr key={n.name}>
                        <td className="px-3 py-1.5 text-slate-800">{n.name}</td>
                        <td className="px-3 py-1.5 text-right text-slate-600">{n.count}</td>
                        <td className={`px-3 py-1.5 text-xs ${STATUS[n.status]?.tone}`}>
                          {STATUS[n.status]?.label || n.status}
                        </td>
                        <td className="px-3 py-1.5">
                          <select
                            value={n.name in mapping ? String(mapping[n.name])
                              : n.user_id ? String(n.user_id) : ""}
                            disabled={res.applied}
                            onChange={(e) => setMap(n.name, e.target.value)}
                            className="border border-slate-300 rounded px-1.5 py-1 text-xs bg-white max-w-[240px]"
                          >
                            <option value="">— tanlang —</option>
                            <option value="0">O'tkazib yuborish</option>
                            {res.users.map((u: Any) => (
                              <option key={u.id} value={u.id}>
                                {u.name} — {u.role_label}
                              </option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {res.applied ? (
                <p className="text-sm text-emerald-700 mt-4 flex items-center gap-1.5">
                  <CheckCircle2 size={15} /> Import tugadi: {res.added} ta yozuv qo'shildi.
                </p>
              ) : (
                <div className="flex flex-wrap items-center gap-3 mt-4">
                  {unresolved.length > 0 && (
                    <p className="text-xs text-amber-700 flex-1 min-w-[200px]">
                      {unresolved.length} ta ism xodimga moslanmagan — ular import
                      qilinmaydi. Kerak bo'lsa, o'ng tomondan xodimni tanlang.
                    </p>
                  )}
                  <button
                    onClick={() => items && check(items, mapping, true)}
                    disabled={busy || !res.to_add}
                    className="ml-auto bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
                  >
                    {res.to_add
                      ? `${res.to_add} ta yozuvni import qilish`
                      : "Qo'shiladigan yozuv yo'q"}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
