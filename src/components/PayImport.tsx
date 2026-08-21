import { useEffect, useState } from "react";
import { Upload, Check, AlertTriangle, Trash2, FileDown } from "lucide-react";
import { api } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { useAuth } from "../lib/AuthContext";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;
import { exportToExcel } from "../lib/exportXlsx";

interface ImpRow {
  name: string;
  phone?: string;
  date: string;
  amount: string | number;
  method?: string;
  note?: string;
}

interface ResRow {
  row: number;
  name: string;
  student_id?: number;
  date?: string;
  amount?: number;
  method?: string;
  status:
    | "ok"
    | "created"
    | "will_create"
    | "not_found"
    | "ambiguous"
    | "duplicate"
    | "skip";
  reason?: string;
}

interface ImpResult {
  committed: boolean;
  ok: number;
  duplicate: number;
  not_found: number;
  /** Arxiv o'quvchi sifatida ochilgan (yoki ochiladigan) odamlar soni. */
  created: number;
  total: number;
  rows: ResRow[];
  shown: number;
  all_rows: number;
}

interface ImpStats {
  count: number;
  total: number;
  first: string | null;
  last: string | null;
}

const STATUS_LABEL: Record<string, string> = {
  ok: "tayyor",
  created: "arxivga qo'shildi",
  will_create: "arxivga qo'shiladi",
  not_found: "o'quvchi topilmadi",
  ambiguous: "noaniq",
  duplicate: "allaqachon bor",
  skip: "o'tkazildi",
};

const STATUS_TONE: Record<string, string> = {
  ok: "bg-emerald-100 text-emerald-700",
  created: "bg-sky-100 text-sky-700",
  will_create: "bg-sky-100 text-sky-700",
  not_found: "bg-red-100 text-red-700",
  ambiguous: "bg-amber-100 text-amber-700",
  duplicate: "bg-slate-100 text-slate-500",
  skip: "bg-slate-100 text-slate-500",
};

/**
 * LC UP'dan eski to'lovlar tarixini ko'chirish.
 *
 * Muhim: har bir to'lov yoniga o'sha kunning "hisoblangan" yozuvi ham
 * qo'yiladi — shuning uchun BALANS O'ZGARMAYDI. Tarix ko'rinadi, qarz
 * buzilmaydi.
 */
export function PayImportTab() {
  const { user } = useAuth();
  const [rows, setRows] = useState<ImpRow[]>([]);
  const [fileName, setFileName] = useState("");
  const [res, setRes] = useState<ImpResult | null>(null);
  const [stats, setStats] = useState<ImpStats | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  // Ketgan o'quvchilar yangi tizimga umuman kiritilmagan. Shu belgi
  // qo'yilsa, ular ARXIV o'quvchi bo'lib ochiladi va to'lov tarixi
  // o'shanga tushadi — faol ro'yxatga aralashmaydi.
  const [addArchive, setAddArchive] = useState(true);
  // AVGUST DUBL YECHIMI (2026-08-22, Jahongir: "ikki marta avgust
  // uchun yechganlarni ochirsang balans tenglashadiganlari bor").
  // Import har eski to'lov yoniga "eski hisob" yechimini yozgan edi,
  // avgust uchun esa avto oylik ham bor — dubl. Bu blok faqat shu
  // dublni arxivga ko'chiradi.
  const [augRows, setAugRows] = useState<Any[] | null>(null);
  const [augTotal, setAugTotal] = useState(0);
  const [augBusy, setAugBusy] = useState(false);
  const [augDone, setAugDone] = useState(false);

  async function augPreview() {
    setAugBusy(true);
    try {
      const r = await api.post<Any>("/lcup/cleanup-august", {
        commit: false,
      });
      setAugRows(r.rows || []);
      setAugTotal(r.total || 0);
      setAugDone(false);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setAugBusy(false);
    }
  }

  async function augCommit() {
    if (!augRows || augRows.length === 0) return;
    setAugBusy(true);
    try {
      const r = await api.post<Any>("/lcup/cleanup-august", {
        commit: true,
      });
      setAugDone(true);
      setAugRows(r.rows || []);
      setAugTotal(r.total || 0);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setAugBusy(false);
    }
  }

  function loadStats() {
    api
      .get<ImpStats>("/lcup/payments")
      .then(setStats)
      .catch(() => setStats(null));
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
      const iDate = col("date", "sana", "vaqt", "time", "дата");
      const iAmount = col("amount", "summa", "sum", "to'lov", "tolov", "сумма");
      const iMethod = col("method", "usul", "type", "tur", "kassa");
      const iNote = col("note", "izoh", "comment", "коммент");
      if (iName < 0)
        throw new Error(
          "Ism ustuni topilmadi — sarlavhada Name / Ism / O'quvchi bo'lsin"
        );
      if (iDate < 0)
        throw new Error("Sana ustuni topilmadi — Date / Sana bo'lsin");
      if (iAmount < 0)
        throw new Error("Summa ustuni topilmadi — Amount / Summa bo'lsin");

      const out: ImpRow[] = [];
      for (const r of raw.slice(1)) {
        const name = String(r[iName] ?? "").trim();
        const amount = String(r[iAmount] ?? "").trim();
        if (!name && !amount) continue;
        out.push({
          name,
          phone: iPhone >= 0 ? String(r[iPhone] ?? "").trim() : "",
          date: String(r[iDate] ?? "").trim(),
          amount,
          method: iMethod >= 0 ? String(r[iMethod] ?? "").trim() : "",
          note: iNote >= 0 ? String(r[iNote] ?? "").trim() : "",
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

  async function check(list: ImpRow[], withArchive = addArchive) {
    setBusy(true);
    setErr("");
    try {
      setRes(
        await api.post<ImpResult>("/lcup/payments", {
          rows: list,
          commit: false,
          create_missing: withArchive,
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
        `${res.ok} ta eski to'lov ko'chirilsinmi?\n\n` +
          (res.created
            ? `${res.created} ta ketgan o'quvchi Arxivga qo'shiladi.\n`
            : "") +
          "Balans o'zgarmaydi — har to'lov yoniga o'sha oyning " +
          "hisoblangani ham yoziladi.\n" +
          "Kerak bo'lsa keyin bitta tugma bilan bekor qilasiz."
      )
    )
      return;
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<ImpResult>("/lcup/payments", {
        rows,
        commit: true,
        create_missing: addArchive,
      });
      setRes(r);
      loadStats();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function undo() {
    if (
      !confirm(
        "LC UP'dan ko'chirilgan BARCHA eski to'lovlar o'chirilsinmi?\n\n" +
          "Faqat import qilinganlari o'chadi — bu yerda kiritilgan " +
          "to'lovlarga tegilmaydi."
      )
    )
      return;
    setBusy(true);
    try {
      await api.delete("/lcup/payments");
      setRes(null);
      setRows([]);
      setFileName("");
      loadStats();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  const bad = res ? res.rows.filter((r) => r.status !== "ok") : [];

  return (
    <div>
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
        <p className="text-sm font-medium text-slate-800 mb-1">
          LC UP'dan eski to'lovlar tarixini ko'chirish
        </p>
        <p className="text-xs text-slate-500 mb-4 max-w-3xl">
          LC UP'dan to'lovlarni Excel qilib yuklab oling va shu yerga
          tashlang. Fayl sarlavhasida <b>Ism</b>, <b>Sana</b> va{" "}
          <b>Summa</b> ustunlari bo'lsa yetadi — <b>Telefon</b>,{" "}
          <b>Usul</b> va <b>Izoh</b> bo'lsa yanada aniq bo'ladi.
          O'quvchilar ismi bo'yicha topiladi — <b>arxivdagi (ketgan)
          o'quvchilar ham</b> qidiruvga kiradi.
        </p>

        <div className="flex flex-wrap items-center gap-3">
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
          {busy && <span className="text-sm text-slate-400">Tekshirilmoqda…</span>}
        </div>

        <label className="flex items-start gap-2 mt-4 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={addArchive}
            onChange={(e) => {
              setAddArchive(e.target.checked);
              if (rows.length) check(rows, e.target.checked);
            }}
            className="mt-0.5 w-4 h-4 accent-brand-600"
          />
          <span className="text-xs text-slate-600">
            <b>Topilmagan o'quvchilarni Arxivga qo'shib ket.</b> Eski
            tarixdagi odamlarning ko'pi allaqachon ketgan va yangi
            tizimga umuman kiritilmagan. Shu belgi turganda ular{" "}
            <b>arxiv o'quvchi</b> bo'lib ochiladi va to'lov tarixi
            o'shanga tushadi — faol ro'yxatga, oylikka va hisob-kitobga
            aralashmaydi.
          </span>
        </label>

        <p className="text-xs text-slate-400 mt-3">
          Balans o'zgarmaydi: har bir eski to'lov yoniga o'sha kunning
          hisoblangan summasi ham yoziladi. Ya'ni tarix ko'rinadi, lekin
          bugungi qarz buzilmaydi.
        </p>
      </div>

      {stats && stats.count > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4 flex flex-wrap items-center gap-4">
          <div>
            <p className="text-xs text-slate-500">Ko'chirilgan</p>
            <p className="text-lg font-semibold text-slate-900">
              {stats.count} ta · {formatSom(stats.total)}
            </p>
            {stats.first && (
              <p className="text-xs text-slate-400 mt-0.5">
                {formatDate(stats.first)} — {formatDate(stats.last!)}
              </p>
            )}
          </div>
          <div className="flex-1" />
          {user?.role === "founder" && (
            <button
              onClick={undo}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 px-3 py-1.5 text-sm disabled:opacity-40"
            >
              <Trash2 size={14} /> Importni bekor qilish
            </button>
          )}
        </div>
      )}

      {err && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
          {err}
        </p>
      )}

      {res && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
            {[
              {
                l: res.committed ? "Ko'chirildi" : "Ko'chirishga tayyor",
                v: String(res.ok),
                c: "text-emerald-600",
              },
              { l: "Jami summa", v: formatSom(res.total), c: "text-slate-900" },
              {
                l: "Topilmadi / noaniq",
                v: String(res.not_found),
                c: res.not_found ? "text-red-600" : "text-slate-400",
              },
              {
                l: res.committed ? "Arxivga qo'shildi" : "Arxivga qo'shiladi",
                v: String(res.created ?? 0),
                c: res.created ? "text-sky-600" : "text-slate-400",
              },
              {
                l: "Allaqachon bor",
                v: String(res.duplicate),
                c: "text-slate-400",
              },
            ].map((s) => (
              <div
                key={s.l}
                className="bg-white rounded-xl border border-slate-200 p-4"
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
              {res.ok} ta to'lovni ko'chirish
            </button>
          )}

          {res.committed && (
            <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-4">
              {res.ok} ta eski to'lov ko'chirildi
              {res.created ? `, ${res.created} ta ketgan o'quvchi Arxivga
              qo'shildi` : ""}. Endi ular o'quvchi kartasida va "Shu oy
              to'lovlari" bo'limida ko'rinadi.
            </p>
          )}

          {bad.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-amber-50 border-b border-amber-200">
                <p className="text-sm text-amber-800 flex items-center gap-1.5">
                  <AlertTriangle size={14} />
                  {bad.length} ta qator ko'chirilmadi
                </p>
                <button
                  onClick={() =>
                    exportToExcel(
                      "Kochirilmagan-tolovlar",
                      "Muammoli",
                      bad.map((r) => ({
                        Qator: r.row,
                        "O'quvchi": r.name,
                        Sana: r.date || "",
                        Summa: r.amount ?? "",
                        Sabab: r.reason || STATUS_LABEL[r.status],
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
                    <th className="text-left px-3 py-2 w-28">Sana</th>
                    <th className="text-right px-3 py-2 w-28">Summa</th>
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
                      <td className="px-3 py-2 text-slate-500">
                        {r.date || "—"}
                      </td>
                      <td className="px-3 py-2 text-right text-slate-600">
                        {r.amount ? formatSom(r.amount) : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            STATUS_TONE[r.status]
                          }`}
                        >
                          {STATUS_LABEL[r.status]}
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

      {user?.role === "founder" && (
        <div className="mt-6 bg-white rounded-xl border border-amber-200 p-4">
          <p className="text-sm font-semibold text-slate-800">
            Avgust dubl yechimini tozalash
          </p>
          <p className="text-xs text-slate-500 mt-1 mb-3">
            LC UP importi har eski to'lov yoniga "eski hisob" yechimini
            yozgan. 2026-08 uchun avtomat oylik ham yechilgan — ya'ni
            avgust IKKI MARTA yechilgan o'quvchilar bor. Bu tugma faqat
            o'sha dubl yechimlarni topib ARXIVGA ko'chiradi (kerak
            bo'lsa tiklanadi), boshqa hech narsaga tegmaydi.
          </p>
          <div className="flex gap-2">
            <button
              onClick={augPreview}
              disabled={augBusy}
              className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-700 disabled:opacity-60"
            >
              {augBusy && augRows === null ? "Tekshirilmoqda…" : "Ko'rib chiqish"}
            </button>
            {augRows !== null && augRows.length > 0 && !augDone && (
              <button
                onClick={augCommit}
                disabled={augBusy}
                className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-semibold disabled:opacity-60"
              >
                {augBusy ? "Bajarilmoqda…" : `Tasdiqlash — ${augRows.length} ta yechimni arxivga`}
              </button>
            )}
          </div>
          {augDone && (
            <p className="text-sm text-emerald-700 font-medium mt-3">
              ✅ Bajarildi — {augRows?.length} ta dubl yechim arxivga
              ko'chirildi. Balanslar darhol yangilandi.
            </p>
          )}
          {augRows !== null && !augDone && (
            <p className="text-xs text-slate-600 mt-3">
              Topildi: <b>{augRows.length}</b> ta dubl yechim, jami{" "}
              <b>{formatSom(augTotal)}</b>
            </p>
          )}
          {augRows !== null && augRows.length > 0 && (
            <div className="mt-2 max-h-64 overflow-y-auto border border-slate-100 rounded-lg">
              <table className="w-full text-xs">
                <tbody className="divide-y divide-slate-100">
                  {augRows.slice(0, 300).map((r: Any) => (
                    <tr key={r.payment_id}>
                      <td className="px-3 py-1.5 text-slate-700">{r.student}</td>
                      <td className="px-3 py-1.5 text-slate-500">{r.date}</td>
                      <td className="px-3 py-1.5 text-right text-red-600">
                        {formatSom(r.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {augRows !== null && augRows.length === 0 && (
            <p className="text-sm text-slate-500 mt-3">
              Dubl yechim topilmadi.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
