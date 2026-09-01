import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, ChevronLeft, ChevronRight, Info } from "lucide-react";
import { api } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import { Time24Input } from "../../components/Time24Input";
import { PRESENT_OPTS } from "../../lib/teacherApi";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY TEACHER — SUPPORT YO'QLAMASI (2026-08-10, qayta qurildi).
 *
 * Jahongir: "support hisobotini ustoznikidek qilish zarur, faqat
 * support yo'qlamasi bo'limiga tushsin... ha ustoznikiday va unga
 * qo'shimcha ravishda qancha dars o'tganligini qo'lda belgilaydigan
 * bo'lishi kerak."
 *
 * Avval bu ekran faqat SON kiritardi ("nechta o'quvchi bilan
 * ishladingiz") — endi ustozning dars ekranidagidek HAR BIR O'QUVCHI
 * alohida belgilanadi (Keldi / Kech / Yo'q) va qo'shimcha qilib
 * necha soat dars o'tilgani tanlanadi (1–3, erkin yozish ham mumkin).
 *
 * SAQLASH mavjud PUT /api/groups/{id}/support-attendance orqali
 * ketadi — bu yozuvlar FAQAT "Support davomati" bo'limiga tushadi,
 * ustozning asosiy yo'qlamasiga umuman aralashmaydi. Seans (oylik
 * hisobi uchun) yo'qlamadan avtomat sinxronlanadi — alohida
 * "seans yozish" degan ikkinchi ish qolmadi.
 */

const dayNames = ["Du", "Se", "Cho", "Pa", "Ju", "Sha", "Ya"];

function fmtDay(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return { n: d.getDate(), w: dayNames[(d.getDay() + 6) % 7] };
}

const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];

export default function TeacherSession() {
  const now = new Date();
  const [ym, setYm] = useState({ y: now.getFullYear(), m: now.getMonth() + 1 });
  const [opts, setOpts] = useState<Any>(null);
  const [gid, setGid] = useState<number | null>(null);
  const [grid, setGrid] = useState<Any>(null);
  const [day, setDay] = useState<string>("");
  const [rows, setRows] = useState<{ id: number; full_name: string; status: string; present: number | null }[]>([]);
  const [orig, setOrig] = useState<Record<number, number | null>>({});
  const [hours, setHours] = useState<number>(0);
  const [freeHours, setFreeHours] = useState("");
  const [start, setStart] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    api
      .get<Any>("/teacher/support-options")
      .then((r) => {
        setOpts(r);
        const gs = r?.groups || [];
        if (gs.length === 1) setGid(gs[0].id);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const loadGrid = useCallback(() => {
    if (!gid) return;
    setErr("");
    setGrid(null);
    api
      .get<Any>(`/groups/${gid}/support-attendance?year=${ym.y}&month=${ym.m}`)
      .then((r) => {
        setGrid(r);
        // Kun tanlash: bugun support kuni bo'lsa — bugun, aks holda
        // oxirgi O'TGAN support kuni (ertangi kunni tanlab bo'lmaydi).
        const days: string[] = r.days || [];
        const today: string = r.today;
        let pick = "";
        if (days.includes(today)) pick = today;
        else {
          const past = days.filter((d) => d <= today);
          pick = past.length ? past[past.length - 1] : "";
        }
        setDay(pick);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [gid, ym]);

  useEffect(loadGrid, [loadGrid]);

  // Tanlangan kun o'zgarganda o'quvchi belgilari va soat yangilanadi
  useEffect(() => {
    if (!grid || !day) {
      setRows([]);
      return;
    }
    const mk: Record<string, Any> = grid.marks || {};
    const rs = (grid.students || []).map((s: Any) => {
      const v = mk[`${day}:${s.id}`];
      // Serverdan: true (keldi) | 2 (kech) | false (yo'q) | yo'q
      const present = v === undefined ? null : v === 2 ? 2 : v ? 1 : 0;
      return { id: s.id, full_name: s.full_name, status: s.status, present };
    });
    setRows(rs);
    setOrig(Object.fromEntries(rs.map((r: Any) => [r.id, r.present])));
    const ses = (grid.sessions || {})[day];
    setHours(ses?.hours || 0);
    setFreeHours("");
    setStart(ses?.start || grid.default_start || "");
    setDirty(false);
  }, [grid, day]);

  const steps: number[] = opts?.hour_steps || [1, 1.5, 2, 2.5, 3];
  const minH: number = opts?.min_hours ?? 1;
  const maxH: number = opts?.max_hours ?? 3;
  const groups: Any[] = opts?.groups || [];
  const days: string[] = grid?.days || [];
  const today: string = grid?.today || "";
  const canPast: boolean = !!grid?.can_past;
  const canEdit: boolean = !!grid?.can_edit;
  const editable =
    canEdit && !!day && (day === today || (day < today && canPast));

  const marked = rows.filter((r) => r.present !== null).length;
  const cameCount = rows.filter((r) => r.present === 1 || r.present === 2).length;
  const hoursOk = hours >= minH && hours <= maxH;
  // Hech kim belgilanmagan holatda soat shart emas (seans o'chadi);
  // kimdir kelgan bo'lsa soat va boshlanish vaqti kerak.
  const needSession = cameCount > 0;
  const valid = dirty && (!needSession || (hoursOk && !!start));

  function setMark(sid: number, v: number) {
    if (!editable) return;
    setRows((rs) =>
      rs.map((r) => (r.id === sid ? { ...r, present: r.present === v ? null : v } : r)),
    );
    setDirty(true);
  }

  async function save() {
    if (!valid || saving || !gid) return;
    setSaving(true);
    try {
      const marks: Any[] = [];
      for (const r of rows) {
        if (r.present === null) {
          // Avval belgi bor edi, endi olib tashlandi
          if (orig[r.id] !== null && orig[r.id] !== undefined)
            marks.push({ student_id: r.id, remove: true });
          continue;
        }
        marks.push({
          student_id: r.id,
          present: r.present !== 0,
          late: r.present === 2,
        });
      }
      await api.put(`/groups/${gid}/support-attendance`, {
        day,
        marks,
        start_time: start || null,
        hours: needSession ? hours : null,
      });
      pushToast("Support yo'qlamasi saqlandi", "success", 2500);
      loadGrid();
    } catch {
      /* xato toast'da */
    } finally {
      setSaving(false);
    }
  }

  const sesCount = useMemo(
    () => Object.keys(grid?.sessions || {}).length,
    [grid],
  );

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/teacher"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Bugun
          </Link>
          <h1 className="text-lg font-semibold">Support yo'qlamasi</h1>
          <p className="text-sm opacity-90">
            {grid
              ? `${MONTHS[ym.m - 1]}: ${sesCount} seans · ${grid.hours_total || 0} soat`
              : "O'quvchilarni belgilang, soatni tanlang"}
          </p>
        </div>
      </div>

      <div
        className="max-w-md mx-auto px-4 -mt-5 space-y-4"
        style={{ paddingBottom: editable ? 130 : 32 }}
      >
        {/* ---- Guruh tanlash ---- */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-800">Guruh</p>
            <div className="flex items-center gap-1 text-slate-500">
              <button
                onClick={() =>
                  setYm((p) =>
                    p.m === 1 ? { y: p.y - 1, m: 12 } : { y: p.y, m: p.m - 1 },
                  )
                }
                className="p-1.5 rounded-lg border border-slate-200"
                aria-label="Oldingi oy"
              >
                <ChevronLeft size={14} />
              </button>
              <span className="text-xs font-medium w-20 text-center">
                {MONTHS[ym.m - 1]}
              </span>
              <button
                onClick={() =>
                  setYm((p) =>
                    p.m === 12 ? { y: p.y + 1, m: 1 } : { y: p.y, m: p.m + 1 },
                  )
                }
                className="p-1.5 rounded-lg border border-slate-200"
                aria-label="Keyingi oy"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
          {groups.length === 0 && (
            <p className="text-sm text-slate-400">
              Sizga hali guruh biriktirilmagan.
            </p>
          )}
          <div className="flex flex-wrap gap-1.5">
            {groups.map((g) => (
              <button
                key={g.id}
                onClick={() => setGid(g.id)}
                className={`px-3.5 py-2 rounded-lg border text-sm font-medium transition ${
                  gid === g.id
                    ? "bg-brand-600 text-white border-transparent"
                    : "bg-white text-slate-600 border-slate-200"
                }`}
              >
                {g.name}
              </button>
            ))}
          </div>
        </div>

        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4">
            <p className="text-sm text-red-600">{err}</p>
            <button
              onClick={loadGrid}
              className="mt-2 text-sm font-medium text-brand-600"
            >
              Qayta urinish
            </button>
          </div>
        )}

        {gid && grid && days.length === 0 && (
          <div className="bg-white rounded-xl border border-amber-200 p-4">
            <p className="text-sm text-amber-700">
              {grid.hint ||
                "Bu oyda support darsi kuni yo'q — biriktirishda kun va vaqt tanlangan bo'lishi kerak."}
            </p>
          </div>
        )}

        {/* ---- Kun tanlash ---- */}
        {gid && grid && days.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-2.5">Kun</p>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {days.map((d) => {
                const f = fmtDay(d);
                const has = !!(grid.sessions || {})[d];
                const future = d > today;
                const lockedPast = d < today && !canPast;
                return (
                  <button
                    key={d}
                    disabled={future}
                    onClick={() => setDay(d)}
                    className={`shrink-0 w-12 py-2 rounded-lg border text-center transition disabled:opacity-30 ${
                      day === d
                        ? "bg-brand-600 text-white border-transparent"
                        : lockedPast
                          ? "bg-slate-50 text-slate-400 border-slate-200"
                          : "bg-white text-slate-600 border-slate-200"
                    }`}
                  >
                    <span className="block text-[10px] opacity-75">{f.w}</span>
                    <span className="block text-sm font-semibold">{f.n}</span>
                    {has && (
                      <span
                        className={`block mx-auto mt-0.5 w-1 h-1 rounded-full ${
                          day === d ? "bg-white" : "bg-emerald-500"
                        }`}
                      />
                    )}
                  </button>
                );
              })}
            </div>
            {day && day < today && !canPast && (
              <p className="text-[11px] text-slate-400 mt-2">
                O'tgan kunni faqat rahbariyat o'zgartira oladi — ko'rish
                mumkin, tahrirlash yopiq.
              </p>
            )}
          </div>
        )}

        {/* ---- O'quvchilar (ustoznikidek) ---- */}
        {gid && grid && day && (
          <div className="space-y-2">
            <div className="flex items-baseline justify-between px-1">
              <p className="text-sm font-semibold text-slate-800">
                O'quvchilar
              </p>
              <p className="text-[11px] text-slate-400">
                {marked}/{rows.length} belgilandi
              </p>
            </div>
            {rows.map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-xl border border-slate-200 p-3"
              >
                <p className="text-sm font-medium text-slate-800 truncate">
                  {s.full_name}
                  {s.status === "trial" && (
                    <span className="ml-1.5 text-[10px] font-normal text-amber-600">
                      sinov
                    </span>
                  )}
                </p>
                <div className="flex gap-1.5 mt-2.5">
                  {PRESENT_OPTS.map((o) => (
                    <button
                      key={o.v}
                      disabled={!editable}
                      onClick={() => setMark(s.id, o.v)}
                      className={`flex-1 py-2.5 rounded-lg text-xs font-semibold border transition disabled:opacity-50 ${
                        s.present === o.v
                          ? o.cls + " border-transparent"
                          : "bg-white text-slate-500 border-slate-200"
                      }`}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}

            {/* ---- Soat (Jahongir: qo'lda belgilanadi) ----
                2026-08-31, Jahongir: "soat o'zgartirish yo'q bo'lib
                qolibdi supportlardan, 1 soatdan ko'p o'tsa avval
                o'zgartirolardiyu. Doimiy 1 soat emas-da, ba'zida
                2 soat ham o'tishi mumkin, 3 soat ham bor".

                SABAB: blok "kimdir keldi" belgilangandan KEYIN
                paydo bo'lardi. Support ekranni ochganda uni umuman
                ko'rmasdi va "yo'qolib qolibdi" deb o'ylardi.

                ENDI: kun tahrirlanadigan bo'lsa — blok DOIM turadi.
                Hech kim belgilanmagan bo'lsa, pastda shu haqda
                eslatma chiqadi (seans hisoblanmaydi), lekin soat
                tanlagichning o'zi ko'rinib turadi. */}
            {editable && (
              <div className={`bg-white rounded-xl border p-4 space-y-3 ${
                needSession ? "border-slate-200" : "border-slate-200 opacity-70"
              }`}>
                <p className="text-sm font-semibold text-slate-800">
                  Necha soat dars o'tdingiz
                </p>
                <p className="text-[11px] text-slate-400 -mt-2">
                  Har seans bir xil emas — 1, 2 yoki 3 soat bo'lishi
                  mumkin. Qancha o'tgan bo'lsangiz, shuni tanlang.
                </p>
                <div className="grid grid-cols-5 gap-1.5">
                  {steps.map((h) => (
                    <button
                      key={h}
                      type="button"
                      disabled={!editable}
                      onClick={() => {
                        setHours(h);
                        setFreeHours("");
                        setDirty(true);
                      }}
                      className={`py-2.5 rounded-lg border text-sm font-semibold transition disabled:opacity-50 ${
                        hours === h && !freeHours
                          ? "bg-brand-600 text-white border-transparent"
                          : "bg-white text-slate-600 border-slate-200"
                      }`}
                    >
                      {h}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400 shrink-0">
                    yoki o'zingiz:
                  </span>
                  <input
                    type="number"
                    inputMode="decimal"
                    step="0.25"
                    min={minH}
                    max={maxH}
                    disabled={!editable}
                    value={freeHours}
                    onChange={(e) => {
                      const v = e.target.value;
                      setFreeHours(v);
                      setHours(v ? Number(v) : 0);
                      setDirty(true);
                    }}
                    className={`flex-1 rounded-lg border px-3 py-2 text-sm ${
                      freeHours && !hoursOk
                        ? "border-red-300 text-red-700"
                        : "border-slate-300"
                    }`}
                    placeholder="masalan 1.75"
                  />
                </div>
                {!needSession && (
                  <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                    Hozircha hech kim &laquo;Keldi&raquo; deb belgilanmagan —
                    bunday holatda seans hisoblanmaydi va oylikka kirmaydi.
                    O&apos;quvchilarni belgilang.
                  </p>
                )}
                <div>
                  <label className="block text-[11px] text-slate-500 mb-1">
                    Boshlanish vaqti
                  </label>
                  <Time24Input
                    value={start}
                    onChange={(e: Any) => {
                      setStart(e.target.value);
                      setDirty(true);
                    }}
                    className="w-full rounded-lg border border-slate-300 px-2 py-2.5 text-sm"
                  />
                </div>
                <p
                  className={`text-[11px] ${
                    hours && !hoursOk ? "text-red-600" : "text-slate-400"
                  }`}
                >
                  {minH}–{maxH} soat oralig'ida. Oyligingiz shu soatdan
                  hisoblanadi.
                </p>
              </div>
            )}

            <p className="text-[11px] text-slate-400 flex items-start gap-1.5 px-1">
              <Info size={11} className="mt-0.5 shrink-0" />
              Bu yo'qlama faqat "Support davomati" bo'limiga tushadi —
              ustozning asosiy yo'qlamasiga aralashmaydi.
            </p>
          </div>
        )}
      </div>

      {/* Saqlash paneli tab panelining USTIDA (ustoz ekranidagidek) */}
      {editable && rows.length > 0 && (
        <div className="fixed bottom-[60px] inset-x-0 px-4 pt-6 pb-3 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent z-30">
          <div className="max-w-md mx-auto">
            <button
              onClick={save}
              disabled={saving || !valid}
              className="w-full py-3.5 rounded-xl bg-brand-600 text-white text-sm font-semibold shadow-lg flex items-center justify-center gap-2 disabled:opacity-40"
            >
              <Check size={17} />
              {saving ? "Saqlanmoqda…" : dirty ? "Saqlash" : "Saqlangan"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
