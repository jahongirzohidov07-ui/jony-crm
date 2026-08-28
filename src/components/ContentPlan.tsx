import { useCallback, useEffect, useState } from "react";
import {
  Copy, RefreshCw, Link2, FileText, Check, X, Plus,
  TrendingUp, AlertTriangle, ChevronDown, Upload,
} from "lucide-react";
import { api, getGlobalBranch } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * KONTENT-PLAN (2026-08-27).
 *
 * Jahongir "idealniy kontent plan" deb Excel yubordi:
 * "sen ham SMMdagi kontent planni shunaqa qism bo'limilarni bo'lishi
 * kerak va ichiga ssearniysi scriptini yozadigan ham bo'lishi kerak
 * SMM manager kirib shuni kopya qilishga oson bo'lsin, ozgartirishga
 * oson bo'lsin va shu video joylangangandan keyin linkini joylashi
 * kerak link orqali avtomat nechta korildi nechta koment like repost
 * bolgani avtomat hisoboti unga korinsin kuchli tahlil qilsa
 * ob'ladi."
 *
 * TUZILMA — Excel jadvalining aynan ustunlari:
 *   Sana · Kun · Vaqt · Platforma · Auditoriya · Kontent ustuni ·
 *   Voronka · Maqsad · Mavzu · Hook · Asosiy fikr · Dalil · Format ·
 *   CTA · Mas'ul · Syomka sanasi · Holati · Kutilayotgan KPI ·
 *   Haqiqiy natija · Xulosa
 *
 * NEGA JADVAL, KARTA EMAS: kontent-plan bir oyni BIR KO'ZDA ko'rish
 * uchun kerak. Karta ko'rinishida "juma kunlari nima qilyapmiz?"
 * degan savolga javob topib bo'lmaydi.
 */
const MONTHS = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"];

export function ContentPlan() {
  const now = new Date();
  // 2026-08-28, Jahongir: "shu OY TANLASH EMAS, eng oldingilari
  // bo'yicha SANA bo'yicha eng yaqinlari bo'yicha KETMA-KETLIKDA
  // tursin". Standart holat — HAMMASI, sana tartibida. Oy tanlash
  // olib tashlanmadi, lekin endi ixtiyoriy filtr bo'lib qoldi:
  // yuklangan post qaysi oyga tushganini topolmay qolish holati
  // takrorlanmasin.
  const [pick, setPick] = useState("all");   // "all" | "YYYY-MM"
  const year = pick === "all" ? now.getFullYear() : Number(pick.slice(0, 4));
  const month = pick === "all" ? now.getMonth() + 1 : Number(pick.slice(5));
  const [d, setD] = useState<Any>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [busy, setBusy] = useState<number | "all" | null>(null);
  const [msg, setMsg] = useState("");
  const [tick, setTick] = useState(0);
  const [preview, setPreview] = useState<Any>(null);

  const load = useCallback(() => {
    const q = pick === "all"
      ? "/smm/plan"
      : `/smm/plan?scope=month&year=${year}&month=${month}`;
    api.get<Any>(q).then(setD).catch(() => setD(null));
  }, [pick, year, month]);
  useEffect(load, [load, tick]);

  const save = async (id: number, patch: Any) => {
    try {
      await api.put(`/content/${id}`, patch);
      setTick((k) => k + 1);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const copy = async (id: number) => {
    setBusy(id);
    try {
      await api.post(`/content/${id}/copy`, {});
      setMsg("Nusxa olindi — sanasini va mavzusini o'zgartiring");
      setTick((k) => k + 1);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  const fetchOne = async (id: number) => {
    setBusy(id);
    setMsg("");
    try {
      const r = await api.post<Any>(`/content/${id}/fetch`, {});
      setMsg(r.note || "Yangilandi");
      setTick((k) => k + 1);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  const fetchAll = async () => {
    setBusy("all");
    setMsg("");
    try {
      const r = await api.post<Any>(
        pick === "all"
          ? "/smm/fetch-all"
          : `/smm/fetch-all?year=${year}&month=${month}`, {});
      const why = (r.reasons || [])
        .map((x: Any) => `${x.count} ta — ${x.note}`).join("; ");
      setMsg(`${r.updated} ta yangilandi`
        + (r.failed ? `, ${r.failed} ta olinmadi. ${why}` : ""));
      setTick((k) => k + 1);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  /* EXCEL IMPORT (2026-08-27).
     Fayl BROUZERDA o'qiladi — serverda Excel kutubxonasi yo'q va uni
     qo'shish serverless to'plamini og'irlashtiradi. Brouzerda esa
     xlsx kutubxonasi allaqachon bor (hisobot yuklab olish uchun).
     Avval "ko'rib chiqish", keyin haqiqiy import. */
  /** Yuklanayotgan reja QAYSI FILIALGA yozilsin — tepadagi
   *  tanlagichdan. Avval bu hech qayerdan olinmasdi va asoschi
   *  yuklaganda qatorlar FILIALSIZ saqlanardi; tanlagichda esa
   *  "Bekobod 1" turgani uchun ular ro'yxatga tushmasdi
   *  (2026-08-28 — sentabr rejasi shuning uchun "yo'q" edi). */
  const branchNow = () => {
    const b = getGlobalBranch();
    return b ? Number(b) : null;
  };

  /** Matndan oyni topish: "Sentabr 2026", "sentyabr", "09.2026". */
  const guessMonth = (text: string): [number, number] | null => {
    const t = (text || "").toLowerCase();
    const AL = [
      ["yanvar", "январ", "january"], ["fevral", "феврал", "february"],
      ["mart", "март", "march"], ["aprel", "апрел", "april"],
      ["may", "май"], ["iyun", "июн", "june"],
      ["iyul", "июл", "july"], ["avgust", "август", "august"],
      ["sentabr", "sentyabr", "сентябр", "september"],
      ["oktabr", "oktyabr", "октябр", "october"],
      ["noyabr", "ноябр", "november"], ["dekabr", "декабр", "december"],
    ];
    let mm = 0;
    AL.forEach((names, i) => {
      if (!mm && names.some((n) => t.includes(n))) mm = i + 1;
    });
    if (!mm) return null;
    const ym = t.match(/20\d{2}/);
    return [ym ? Number(ym[0]) : now.getFullYear(), mm];
  };

  const pickFile = async (file: File) => {
    setMsg("Fayl o'qilmoqda…");
    try {
      const XLSX = await import("xlsx");
      // cellDates: Excel sanalari raqam emas, HAQIQIY sana bo'lib
      // kelsin. Aks holda "45900" kabi raqam kun deb o'qilardi.
      const wb = XLSX.read(await file.arrayBuffer(),
        { type: "array", cellDates: true });
      let best: Any[] = [];
      let bestSheet = "";
      const iso = (v: Any) =>
        v instanceof Date
          ? new Date(v.getTime() - v.getTimezoneOffset() * 60000)
            .toISOString().slice(0, 10)
          : v;
      for (const name of wb.SheetNames) {
        const aoa: Any[][] = XLSX.utils.sheet_to_json(wb.Sheets[name],
          { header: 1, blankrows: false, defval: "", raw: false,
            cellDates: true } as Any);
        const hi = aoa.findIndex((r: Any[]) =>
          r.some((c: Any) => String(c).trim().toLowerCase() === "sana"));
        if (hi < 0) continue;
        const hdr = aoa[hi].map((c: Any) => String(c).trim());
        const rows = aoa.slice(hi + 1)
          .filter((r: Any[]) => String(r[0] ?? "").trim())
          .map((r: Any[]) => Object.fromEntries(
            hdr.map((h: string, i: number) => [h, iso(r[i] ?? "")])));
        if (rows.length > best.length) { best = rows; bestSheet = name; }
      }
      if (best.length === 0) {
        setMsg("Faylda «Sana» ustuni topilmadi. Kontent-plan varag'i "
          + "sarlavhalari: Sana, Vaqt, Platforma, Mavzu…");
        return;
      }
      // QAYSI OYGA. 2026-08-28 da tuzatilgan xato: avval bu ekrandagi
      // tanlagichdan olinardi va sentabr rejasi avgustga tushib
      // ketgan edi. Endi tartib: faylning o'zidagi to'liq sana ->
      // varaq nomi -> fayl nomi -> oxirgi chora sifatida tanlagich.
      const firstDate = String(best[0]?.Sana ?? best[0]?.sana ?? "");
      let ty = year, tm = month, qayerdan = "tanlagichdan";
      const m0 = firstDate.match(/^(20\d{2})-(\d{2})-\d{2}/);
      if (m0) {
        ty = Number(m0[1]); tm = Number(m0[2]); qayerdan = "fayldagi sanadan";
      } else {
        const g = guessMonth(bestSheet) || guessMonth(file.name);
        if (g) { [ty, tm] = g; qayerdan = "fayl nomidan"; }
      }
      const r = await api.post<Any>("/smm/plan/import",
        { year: ty, month: tm, rows: best, dry_run: true,
          branch_id: branchNow() });
      setPreview({ ...r, rows: best, ty, tm, qayerdan, file: file.name });
      setMsg("");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Fayl o'qilmadi");
    }
  };

  /** Nishon oy o'zgartirilganda oldindan ko'rishni qayta hisoblash. */
  const repreview = async (ty: number, tm: number) => {
    if (!preview) return;
    try {
      const r = await api.post<Any>("/smm/plan/import",
        { year: ty, month: tm, rows: preview.rows, dry_run: true,
          branch_id: branchNow() });
      setPreview({ ...preview, ...r, rows: preview.rows, ty, tm,
                   qayerdan: "qo'lda tanlandi" });
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const doImport = async () => {
    if (!preview) return;
    setBusy("all");
    try {
      const r = await api.post<Any>("/smm/plan/import",
        { year: preview.ty, month: preview.tm,
          rows: preview.rows, dry_run: false,
          branch_id: branchNow() });
      setMsg(`${r.added} ta post qo'shildi`
        + (r.skipped ? `, ${r.skipped} tasi allaqachon bor edi` : ""));
      setPreview(null);
      setPick("all");        // yangi qatorlar darrov ko\'rinsin
      setTick((k) => k + 1);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const rows: Any[] = d.rows || [];
  // Ro'yxatda o'tgan kunlar qayerdan boshlanadi (chegara chizig'i uchun)
  const firstPast = pick === "all"
    ? rows.findIndex((r) => r.date && d.today && r.date < d.today)
    : -1;
  const published = rows.filter((r) => r.post_url);
  const withMetric = rows.filter((r) => r.metrics?.views);

  return (
    <div>
      {/* --- boshqaruv --- */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <select value={pick} onChange={(e) => setPick(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm">
          <option value="all">Barchasi (sana bo'yicha)</option>
          {(d.months || []).map((m: Any) => (
            <option key={`${m.year}-${m.month}`}
              value={`${m.year}-${String(m.month).padStart(2, "0")}`}>
              {m.label} ({m.count})
            </option>
          ))}
        </select>
        <span className="text-sm text-slate-500">
          {rows.length} ta post · {published.length} tasida havola ·{" "}
          {withMetric.length} tasida natija
        </span>
        <div className="flex-1" />
        <label className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium cursor-pointer hover:bg-slate-50">
          <Upload size={14} /> Excel'dan yuklash
          <input type="file" accept=".xlsx,.xls" className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) pickFile(f);
              e.target.value = "";
            }} />
        </label>
        <button
          onClick={fetchAll}
          disabled={busy === "all" || published.length === 0}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-40"
        >
          <RefreshCw size={14} className={busy === "all" ? "animate-spin" : ""} />
          Natijalarni yangilash
        </button>
      </div>

      {msg && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-[13px] text-slate-700 flex items-start gap-2">
          <span className="flex-1">{msg}</span>
          <button onClick={() => setMsg("")}><X size={14} /></button>
        </div>
      )}

      {/* --- import: ko'rib chiqish --- */}
      {preview && (
        <div className="mb-4 rounded-xl border border-brand-300 bg-brand-50/50 p-4">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <p className="text-sm font-medium text-slate-800">
              Faylda {preview.will_add + preview.skipped} qator topildi
            </p>
            {/* QAYSI OYGA TUSHADI — ochiq ko'rsatiladi. Avval bu
                yashirin edi va sentabr rejasi bilinmay avgustga
                yozilib ketgan edi (2026-08-28). */}
            <span className="text-[12px] px-2 py-0.5 rounded-full
                             bg-brand-100 text-brand-800 font-medium">
              {MONTHS[(preview.tm || 1) - 1]} {preview.ty} ga
            </span>
            <select
              value={`${preview.ty}-${String(preview.tm).padStart(2, "0")}`}
              onChange={(e) => repreview(Number(e.target.value.slice(0, 4)),
                                         Number(e.target.value.slice(5)))}
              className="px-2 py-1 rounded-lg border border-slate-300 text-[12px]"
            >
              {[-1, 0, 1, 2].map((off) => {
                const dt = new Date(now.getFullYear(), now.getMonth() + off, 1);
                const v = `${dt.getFullYear()}-${String(dt.getMonth() + 1)
                  .padStart(2, "0")}`;
                return (
                  <option key={v} value={v}>
                    {MONTHS[dt.getMonth()]} {dt.getFullYear()}
                  </option>
                );
              })}
            </select>
            <span className="text-[11px] text-slate-500">
              ({preview.qayerdan})
            </span>
            <span className="text-[12px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              {preview.will_add} ta qo'shiladi
            </span>
            {preview.skipped > 0 && (
              <span className="text-[12px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                {preview.skipped} tasi allaqachon bor
              </span>
            )}
            {(preview.bad || []).length > 0 && (
              <span className="text-[12px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                {preview.bad.length} qator tushunarsiz
              </span>
            )}
            <div className="flex-1" />
            <button onClick={() => setPreview(null)}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 text-sm">
              Bekor
            </button>
            <button onClick={doImport}
              disabled={busy === "all" || !preview.will_add}
              className="px-4 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-40">
              Qo'shish
            </button>
          </div>
          <div className="max-h-56 overflow-y-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-[12px]">
              <tbody>
                {(preview.preview || []).map((r: Any, i: number) => (
                  <tr key={i} className="border-b border-slate-50">
                    <td className="px-2 py-1 text-slate-400 tabular-nums w-24 whitespace-nowrap">
                      {r.date?.slice(5)} {r.time}
                    </td>
                    <td className="px-2 py-1 text-slate-800">{r.title}</td>
                    <td className="px-2 py-1 text-slate-500 w-36">{r.pillar}</td>
                    <td className="px-2 py-1 text-slate-500 w-20">{r.funnel}</td>
                    <td className="px-2 py-1 text-slate-500 w-24">{r.fmt}</td>
                    <td className="px-2 py-1 w-32">
                      {r.owner ? (
                        <span className={r.owner_found ? "text-slate-600" : "text-amber-600"}>
                          {r.owner}{r.owner_found ? "" : " (topilmadi)"}
                        </span>
                      ) : <span className="text-slate-300">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(preview.bad || []).length > 0 && (
            <p className="text-[12px] text-amber-700 mt-2">
              Tushunarsiz qatorlar:{" "}
              {preview.bad.map((b: Any) => `${b.row}-qator (${b.why})`).join(", ")}
            </p>
          )}
          <p className="text-[11px] text-slate-500 mt-2">
            Mas'ul ismi topilmasa post baribir qo'shiladi — izohga
            yoziladi va keyin qo'lda biriktiriladi.
          </p>
        </div>
      )}

      {/* --- jadval --- */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="text-sm min-w-[1500px]">
          <thead className="bg-slate-50 text-[11px] text-slate-500 uppercase">
            <tr>
              {["Sana", "Kun", "Vaqt", "Platforma", "Auditoriya",
                "Kontent ustuni", "Voronka", "Maqsad", "Mavzu",
                "Format", "Mas'ul", "Syomka", "Holati",
                "Kutilgan KPI", "Natija", ""].map((h) => (
                <th key={h} className="text-left px-2.5 py-2 font-medium whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <>
                {/* O'TGAN KUNLAR CHEGARASI. Ro'yxat sana bo'yicha:
                    tepada kelayotganlar (eng yaqini birinchi), pastda
                    o'tganlar. Chegara ko'rinib tursin — aks holda
                    "bugun qayerda?" degan savol qoladi. */}
                {i === firstPast && firstPast > -1 && (
                  <tr key="past-line">
                    <td colSpan={16}
                      className="px-4 py-1.5 bg-slate-50 text-[11px] font-semibold
                                 text-slate-400 border-t border-slate-200">
                      ——— o'tgan kunlar ———
                    </td>
                  </tr>
                )}
                <tr key={r.id} className={"border-t border-slate-100 hover:bg-slate-50/60"
                  + (r.date === d.today ? " bg-brand-50/60" : "")}>
                  <td className="px-2.5 py-2 whitespace-nowrap tabular-nums">
                    {/* Oy nomi QATORNING O'Z sanasidan — tanlagichdan
                        emas. Barcha oylar birga ko'rsatilganda
                        tanlagichnikini olsa hamma qator "Sentabr"
                        bo'lib chiqib ketardi. */}
                    {r.date ? `${r.date.slice(8)}-${MONTHS[Number(r.date.slice(5, 7)) - 1]
                      .slice(0, 3).toLowerCase()}` : "-"}
                    {r.date === d.today && (
                      <span className="ml-1 text-[10px] text-brand-600 font-bold">
                        bugun
                      </span>
                    )}
                  </td>
                  <td className="px-2.5 py-2 text-slate-500">{r.weekday}</td>
                  <td className="px-2.5 py-2 tabular-nums text-slate-500">{r.time}</td>
                  <td className="px-2.5 py-2 whitespace-nowrap">{r.platform}</td>
                  <td className="px-2.5 py-2 text-slate-600 max-w-[9rem] truncate">
                    {r.audience}
                  </td>
                  <td className="px-2.5 py-2 whitespace-nowrap">
                    <span className="px-1.5 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700">
                      {r.pillar_label}
                    </span>
                  </td>
                  <td className="px-2.5 py-2 text-slate-600">{r.funnel_label}</td>
                  <td className="px-2.5 py-2 text-slate-600">{r.goal_label}</td>
                  <td className="px-2.5 py-2 font-medium text-slate-900 max-w-[16rem]">
                    <button onClick={() => setOpen(open === r.id ? null : r.id)}
                            className="text-left hover:text-brand-700 flex items-start gap-1">
                      <ChevronDown size={13}
                        className={`mt-1 shrink-0 transition ${open === r.id ? "rotate-180" : ""}`} />
                      <span className="line-clamp-2">{r.title}</span>
                    </button>
                  </td>
                  <td className="px-2.5 py-2 text-slate-600 whitespace-nowrap">
                    {r.fmt_label}
                  </td>
                  <td className="px-2.5 py-2 text-slate-600 max-w-[8rem] truncate">
                    {r.owner}
                  </td>
                  <td className="px-2.5 py-2 text-slate-500 tabular-nums whitespace-nowrap">
                    {r.shoot_date?.slice(8)}
                  </td>
                  <td className="px-2.5 py-2 whitespace-nowrap">
                    <span className="px-1.5 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700">
                      {r.status_label}
                    </span>
                  </td>
                  <td className="px-2.5 py-2 text-slate-500 max-w-[9rem] truncate">
                    {r.kpi_target}
                  </td>
                  <td className="px-2.5 py-2 whitespace-nowrap">
                    {r.metrics?.views ? (
                      <span className="text-slate-800 tabular-nums">
                        {r.metrics.views.toLocaleString("ru")} ko'rish
                        <span className="text-slate-400"> · </span>
                        <span className="text-slate-500">
                          {r.metrics.er}%
                        </span>
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                  <td className="px-2.5 py-2 whitespace-nowrap">
                    <button onClick={() => copy(r.id)} disabled={busy === r.id}
                      title="Nusxa olish"
                      className="p-1.5 rounded hover:bg-slate-100 text-slate-500">
                      <Copy size={14} />
                    </button>
                  </td>
                </tr>
                {open === r.id && (
                  <tr key={`${r.id}-x`}>
                    <td colSpan={16} className="px-4 py-4 bg-slate-50 border-t border-slate-200">
                      <RowEditor row={r} meta={d.meta} onSave={save}
                                 onFetch={fetchOne} busy={busy === r.id} />
                    </td>
                  </tr>
                )}
              </>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={16} className="px-4 py-10 text-center text-slate-400 text-sm">
                  {pick === "all"
                    ? "Hali birorta post yo'q. «Excel'dan yuklash» tugmasi "
                      + "orqali kontent-planni yuklang yoki «Kontent taqvimi» "
                      + "bo'limidan qo'ling bilan qo'shing."
                    : "Bu oyda kontent yo'q. Yuqoridagi tanlagichdan "
                      + "«Barchasi» ni tanlab ko'ring — post boshqa oyga "
                      + "tushgan bo'lishi mumkin."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** Qator ichi: brief, ssenariy, havola va natija. */
function RowEditor({ row, meta, onSave, onFetch, busy }: {
  row: Any; meta: Any;
  onSave: (id: number, patch: Any) => void;
  onFetch: (id: number) => void;
  busy: boolean;
}) {
  const [f, setF] = useState<Any>({
    hook: row.hook || "", message: row.message || "",
    proof: row.proof || "", cta: row.cta || "",
    script: row.script || "", caption: row.caption || "",
    hashtags: row.hashtags || "", post_url: row.post_url || "",
    kpi_target: row.kpi_target || "", conclusion: row.conclusion || "",
  });
  const [copied, setCopied] = useState("");

  const set = (k: string, v: string) => setF((o: Any) => ({ ...o, [k]: v }));
  const clip = (text: string, what: string) => {
    navigator.clipboard?.writeText(text || "");
    setCopied(what);
    window.setTimeout(() => setCopied(""), 1500);
  };

  /* Ssenariy skeleti — bo'sh oynaga qarab turmaslik uchun.
     Brief maydonlari o'z joyiga qo'yiladi. */
  const skeleton = () => {
    const t = [
      "[0-3 s] HOOK — ekranda katta yozuv",
      f.hook || "...",
      "",
      "[3-8 s] MUAMMO — tomoshabin o'zini tanisin",
      "...",
      "",
      "[8-20 s] YECHIM — asosiy fikr",
      f.message || "...",
      "",
      "[20-35 s] DALIL — raqam, natija, jonli lavha",
      f.proof || "...",
      "",
      "[35-45 s] CTA — bitta aniq harakat",
      f.cta || "...",
      "",
      "--- SUR'AT ---",
      "Kadr almashishi: har 2-3 soniyada",
      "Ekrandagi yozuv: HOOK va CTA majburiy",
    ].join("\n");
    set("script", t);
  };

  const Field = ({ k, label, rows = 2, ph = "" }: Any) => (
    <div>
      <label className="block text-[11px] font-medium text-slate-500 mb-1">
        {label}
      </label>
      <textarea
        value={f[k]} rows={rows} placeholder={ph}
        onChange={(e) => set(k, e.target.value)}
        className="w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-[13px] resize-y"
      />
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Field k="hook" label="Hook (1-jumla)"
               ph="Birinchi 3 soniyada ushlaydigan gap" />
        <Field k="message" label="Asosiy fikr" />
        <Field k="proof" label="Dalil (raqam, natija, sertifikat)" />
        <Field k="cta" label="CTA" />
      </div>

      {/* --- SSENARIY --- */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <FileText size={14} className="text-slate-400" />
          <span className="text-[11px] font-medium text-slate-500 uppercase">
            Ssenariy
          </span>
          <button onClick={skeleton}
            className="text-[11px] px-2 py-0.5 rounded border border-slate-300 text-slate-600 hover:bg-white">
            <Plus size={10} className="inline -mt-0.5" /> Skelet qo'yish
          </button>
          <button onClick={() => clip(f.script, "script")}
            className="text-[11px] px-2 py-0.5 rounded border border-slate-300 text-slate-600 hover:bg-white">
            {copied === "script" ? <Check size={10} className="inline" /> : <Copy size={10} className="inline" />}
            {" "}Nusxa
          </button>
        </div>
        <textarea
          value={f.script} rows={12}
          onChange={(e) => set("script", e.target.value)}
          placeholder="Ssenariy: vaqt bo'yicha bo'lingan matn. «Skelet qo'yish» tugmasi tayyor qolip beradi."
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-[13px] font-mono leading-relaxed resize-y"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-medium text-slate-500 uppercase">
              Post matni (caption)
            </span>
            <button onClick={() => clip(f.caption + "\n\n" + f.hashtags, "cap")}
              className="text-[11px] px-2 py-0.5 rounded border border-slate-300 text-slate-600 hover:bg-white">
              {copied === "cap" ? <Check size={10} className="inline" /> : <Copy size={10} className="inline" />}
              {" "}Nusxa (hashtag bilan)
            </button>
          </div>
          <textarea value={f.caption} rows={6}
            onChange={(e) => set("caption", e.target.value)}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-[13px] resize-y" />
          <input value={f.hashtags} placeholder="#jonyacademy #bekobod"
            onChange={(e) => set("hashtags", e.target.value)}
            className="w-full mt-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-[13px]" />
        </div>

        {/* --- HAVOLA VA NATIJA --- */}
        <div>
          <span className="block text-[11px] font-medium text-slate-500 uppercase mb-1">
            Post havolasi va natijasi
          </span>
          <div className="flex gap-1.5">
            <input value={f.post_url} placeholder="https://t.me/JonyAcademy/128"
              onChange={(e) => set("post_url", e.target.value)}
              className="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-[13px]" />
            <button
              onClick={() => { onSave(row.id, { post_url: f.post_url }); onFetch(row.id); }}
              disabled={busy || !f.post_url}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-[13px] font-medium disabled:opacity-40">
              <Link2 size={13} /> Olish
            </button>
          </div>
          {row.metrics ? (
            <div className="mt-2 grid grid-cols-3 gap-2">
              {[["Ko'rish", row.metrics.views], ["Like", row.metrics.likes],
                ["Izoh", row.metrics.comments], ["Ulashish", row.metrics.shares],
                ["Saqlash", row.metrics.saves], ["Faollik", `${row.metrics.er}%`]]
                .map(([l, v]: Any) => (
                <div key={l} className="rounded-lg border border-slate-200 bg-white px-2 py-1.5">
                  <p className="text-[10px] text-slate-400">{l}</p>
                  <p className="text-[14px] font-semibold text-slate-800 tabular-nums">
                    {typeof v === "number" ? v.toLocaleString("ru") : v}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
          {row.metrics?.note && (
            <p className="text-[11px] text-slate-500 mt-1.5">
              {row.metrics.source === "auto" ? "✓ " : "⚠ "}
              {row.metrics.note}
            </p>
          )}
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div>
              <label className="block text-[11px] font-medium text-slate-500 mb-1">
                Kutilayotgan KPI
              </label>
              <input value={f.kpi_target} placeholder="8k ko'rish, 100 ulashish"
                onChange={(e) => set("kpi_target", e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-[13px]" />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-500 mb-1">
                Xulosa
              </label>
              <input value={f.conclusion} placeholder="Nima ishladi / ishlamadi"
                onChange={(e) => set("conclusion", e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-[13px]" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button onClick={() => onSave(row.id, f)}
          className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-medium">
          Saqlash
        </button>
        <span className="text-[11px] text-slate-400">
          {meta ? "" : ""}Kod: {row.content_id || "—"}
        </span>
      </div>
    </div>
  );
}

/** Kontent tahlili — nima ishlayapti, nima yo'q. */
export function ContentAnalytics() {
  const [months, setMonths] = useState(3);
  const [d, setD] = useState<Any>(null);

  useEffect(() => {
    api.get<Any>(`/smm/content-analytics?months=${months}`)
      .then(setD).catch(() => setD(null));
  }, [months]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const Cut = ({ title, rows }: { title: string; rows: Any[] }) => (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <p className="text-[12px] font-medium text-slate-700 mb-2">{title}</p>
      {rows.length === 0 ? (
        <p className="text-[12px] text-slate-400">Ma'lumot yo'q</p>
      ) : (
        <div className="space-y-1.5">
          {rows.slice(0, 6).map((r) => {
            const max = rows[0].avg_views || 1;
            return (
              <div key={r.key}>
                <div className="flex items-center gap-2 text-[12px]">
                  <span className="flex-1 truncate text-slate-700">{r.label}</span>
                  <span className="tabular-nums text-slate-800 font-medium">
                    {r.avg_views.toLocaleString("ru")}
                  </span>
                  <span className="w-11 text-right tabular-nums text-slate-400">
                    {r.avg_er}%
                  </span>
                  <span className="w-8 text-right text-slate-300">{r.count}</span>
                </div>
                <div className="h-1 rounded-full bg-slate-100 mt-0.5 overflow-hidden">
                  <div className="h-full rounded-full bg-brand-500"
                       style={{ width: `${(r.avg_views / max) * 100}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
      <p className="text-[10px] text-slate-400 mt-2">
        o'rtacha ko'rish · faollik · post soni
      </p>
    </div>
  );

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        {[1, 3, 6, 12].map((m) => (
          <button key={m} onClick={() => setMonths(m)}
            className={`px-3 py-1.5 rounded-lg text-sm border ${
              months === m ? "bg-brand-600 text-white border-brand-600"
                : "border-slate-200 text-slate-600"}`}>
            {m} oy
          </button>
        ))}
        <span className="text-sm text-slate-500 ml-2">
          {d.count} ta natijasi bor post · o'rtacha{" "}
          {d.avg_views.toLocaleString("ru")} ko'rish · faollik {d.avg_er}%
        </span>
      </div>

      {(d.tips || []).length > 0 && (
        <div className="space-y-2 mb-4">
          {d.tips.map((t: Any, i: number) => (
            <div key={i}
              className={`flex items-start gap-2 px-3 py-2.5 rounded-lg border text-[13px] ${
                t.kind === "good"
                  ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                  : "bg-amber-50 border-amber-200 text-amber-900"}`}>
              {t.kind === "good"
                ? <TrendingUp size={15} className="mt-0.5 shrink-0" />
                : <AlertTriangle size={15} className="mt-0.5 shrink-0" />}
              <span>{t.text}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        <Cut title="Kontent ustuni bo'yicha" rows={d.by_pillar} />
        <Cut title="Format bo'yicha" rows={d.by_format} />
        <Cut title="Platforma bo'yicha" rows={d.by_platform} />
        <Cut title="Voronka bosqichi bo'yicha" rows={d.by_funnel} />
        <Cut title="Hafta kuni bo'yicha" rows={d.by_weekday} />
        <Cut title="Soat bo'yicha" rows={d.by_hour} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
        {[["Eng yaxshi 5 post", d.top], ["Eng past 5 post", d.weak]]
          .map(([title, rows]: Any) => (
          <div key={title} className="bg-white rounded-xl border border-slate-200 p-4">
            <p className="text-[12px] font-medium text-slate-700 mb-2">{title}</p>
            {(rows || []).map((r: Any) => (
              <div key={r.id} className="flex items-center gap-2 py-1 text-[12px]">
                <span className="w-14 shrink-0 text-slate-400 tabular-nums">
                  {r.date?.slice(5)}
                </span>
                <span className="flex-1 truncate text-slate-700">{r.title}</span>
                <span className="tabular-nums text-slate-800">
                  {r.views.toLocaleString("ru")}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
