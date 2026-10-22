import { SectionInsights } from "../components/SectionInsights";
import { tab3d } from "../lib/tabs3d";
import { Fragment, useEffect, useMemo, useState } from "react";
import {
  Award, Download, Trash2, ChevronDown, ChevronRight, Search, Info, Upload,
} from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  CONDUCT_VIEW, HEAD_EXAMINER, HEAD_SUPPORT, can,
} from "../lib/roles";
import { ConductImport } from "../components/ConductImport";
import { MONTHS } from "../lib/expenses";
import { exportToExcel } from "../lib/exportXlsx";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;
type Section = "staff" | "support" | "examiner";

/**
 * NA'MUNALI XODIM (2026-09-16) — Jahongirning "Na'munali xodim.xlsx"
 * jadvali tizimda.
 *
 * Har xodim yilni 100 ball bilan boshlaydi. Qoidabuzarlik yozilsa ball
 * ayiriladi; bir xil qoidabuzarlik bir oy ichida takrorlansa jarima
 * oshadi. Hisobni server qiladi (api/conduct.py) — bu sahifa faqat
 * ko'rsatadi va yozadi.
 */

const pad = (n: number) => String(n).padStart(2, "0");
const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};
const num = (n: Any) => Number(Number(n || 0).toFixed(2));
/** Server vaqtni UTC da (belgisiz) beradi — mahalliy vaqtga o'tkazamiz. */
function localTime(iso: string): string {
  const t = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);
  if (Number.isNaN(t.getTime())) return "";
  return `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())} ` +
    `${pad(t.getHours())}:${pad(t.getMinutes())}`;
}

/** Qolgan ballga qarab rang: jazo chegaralari bilan bir xil. */
function scoreTone(v: number): string {
  if (v <= 0) return "bg-red-600 text-white";
  if (v <= 30) return "bg-red-100 text-red-700";
  if (v <= 50) return "bg-orange-100 text-orange-700";
  if (v < 80) return "bg-amber-50 text-amber-700";
  return "bg-emerald-50 text-emerald-700";
}

function minusText(p: number): string {
  if (p < 0) return `+${num(-p)}`;
  return p > 0 ? `−${num(p)}` : "0";
}

function History({ userId, year }: { userId: number; year: number }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api
      .get<Any>(`/conduct/user/${userId}?year=${year}`, true)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [userId, year]);
  if (err) return <p className="text-xs text-slate-500">{err}</p>;
  if (!d) return <p className="text-xs text-slate-400">Yuklanmoqda…</p>;
  if (!d.items.length)
    return (
      <p className="text-xs text-slate-400">
        {year}-yilda hech qanday minus yozilmagan.
      </p>
    );
  return (
    <div>
      <p className="text-xs text-slate-500 mb-2">
        {year}-yil: jami {minusText(d.year_minus)} ball, qoldi{" "}
        <b className="text-slate-800">{num(d.remaining)}</b>
      </p>
      <table className="w-full text-xs">
        <tbody className="divide-y divide-slate-100">
          {d.items.map((e: Any) => (
            <tr key={e.id}>
              <td className="py-1.5 pr-3 text-slate-500 whitespace-nowrap">
                {e.date}
              </td>
              <td className="py-1.5 pr-3 text-slate-700">
                {e.kind_label}
                {e.nth ? (
                  <span className="text-slate-400"> · oyda {e.nth}-marta</span>
                ) : null}
              </td>
              <td
                className={`py-1.5 pr-3 font-semibold whitespace-nowrap ${
                  e.points < 0 ? "text-emerald-600" : "text-red-600"
                }`}
              >
                {minusText(e.points)}
              </td>
              <td className="py-1.5 pr-3 text-slate-500">{e.note || ""}</td>
              <td className="py-1.5 text-slate-400 whitespace-nowrap">
                {e.created_by || ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Namunali() {
  const { user } = useAuth();
  const now = new Date();
  // Rahbar faqat o'z bo'limini ko'radi — shundan boshlanadi
  const [section, setSection] = useState<Section>(
    user?.role === HEAD_EXAMINER ? "examiner"
      : user?.role === HEAD_SUPPORT ? "support" : "staff",
  );
  const [showImport, setShowImport] = useState(false);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [q, setQ] = useState("");
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [f, setF] = useState({
    user_id: "", kind: "late", date: todayIso(), note: "", points: "",
  });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const allowed = can(user?.role, CONDUCT_VIEW);
  const load = () => {
    // Ruxsati yo'q odamga so'rov yubormaymiz — aks holda "ruxsat yo'q"
    // degan ortiqcha xabar chiqadi
    if (!allowed) return;
    setErr("");
    api
      .get<Any>(
        `/conduct?section=${section}&year=${year}&month=${month}`, true)
      .then(setD)
      .catch((e) => {
        setD(null);
        setErr(e instanceof Error ? e.message : "Xatolik");
      });
  };
  useEffect(load, [section, year, month, allowed]);
  useEffect(() => {
    setOpen(null);
    setF((p) => ({ ...p, user_id: "" }));
    setMsg("");
  }, [section]);

  const rows: Any[] = d?.rows || [];
  const log: Any[] = d?.log || [];
  const rules = d?.rules;
  const kinds: Any[] = rules?.kinds || [];
  const reprimand = rules?.reprimand;
  const isRep = f.kind === reprimand?.key;
  const periodLabel = month ? `${MONTHS[month - 1]} ${year}` : `${year}-yil`;

  const shown = useMemo(() => {
    const t = q.trim().toLowerCase();
    return t ? rows.filter((r) => r.name.toLowerCase().includes(t)) : rows;
  }, [rows, q]);
  const byName = useMemo(
    () => [...rows].sort((a, b) => a.name.localeCompare(b.name)),
    [rows],
  );

  // Oldindan ko'rish: shu oydagi nechanchi marta bo'ladi. Jurnalda shu
  // oyning hamma yozuvi bo'lsagina hisoblaymiz — aks holda jim turamiz.
  const preview = useMemo(() => {
    if (!f.user_id || isRep || !f.date) return null;
    const [fy, fm] = f.date.split("-").map(Number);
    if (fy !== year || (month && fm !== month)) return null;
    const prefix = f.date.slice(0, 7);
    const before = log.filter(
      (e) =>
        String(e.user_id) === f.user_id &&
        e.kind === f.kind &&
        e.date.startsWith(prefix) &&
        e.date <= f.date,
    ).length;
    const k = kinds.find((x) => x.key === f.kind);
    if (!k) return null;
    const nth = before + 1;
    const pts = k.steps[Math.min(nth, k.steps.length) - 1];
    return { nth, pts };
  }, [f, log, kinds, isRep, year, month]);

  if (!allowed) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'limga ruxsatingiz yo'q.
      </p>
    );
  }

  const save = async () => {
    setBusy(true);
    setMsg("");
    try {
      const body: Any = {
        user_id: Number(f.user_id),
        kind: f.kind,
        date: f.date || null,
        note: f.note.trim() || null,
      };
      if (isRep) body.points = Number(f.points);
      const r = await api.post<Any>("/conduct", body);
      const who = rows.find((x) => String(x.user_id) === f.user_id);
      const kl = isRep
        ? reprimand.label
        : kinds.find((x) => x.key === f.kind)?.label;
      setMsg(
        `${who?.name || "Xodim"}: ${kl}` +
          (r.nth ? `, oyda ${r.nth}-marta` : "") +
          ` → ${minusText(r.points)} ball yozildi`,
      );
      setF({ ...f, user_id: "", note: "", points: "" });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (e: Any) => {
    if (
      !confirm(
        `${e.name}: ${e.date} — ${e.kind_label} (${minusText(e.points)}) ` +
          `yozuvini o'chirasizmi? Shu oydagi keyingi yozuvlar bali qayta ` +
          `hisoblanadi.`,
      )
    )
      return;
    try {
      await api.delete(`/conduct/${e.id}`);
      load();
    } catch (er) {
      alert(er instanceof Error ? er.message : "Xatolik");
    }
  };

  const exportXlsx = () => {
    const secLabel =
      d?.sections?.find((s: Any) => s.key === section)?.label || section;
    exportToExcel(`${secLabel} ${periodLabel}`, "Ballar", shown.map((r, i) => {
      const row: Record<string, unknown> = {
        "T/r": i + 1,
        "Xodim": r.name,
        "Lavozim": r.role_label,
        "Filial": r.branch || "",
        "Qolgan ball": num(r.remaining),
        "Yil davomida ayrildi": num(r.year_minus),
        [`${periodLabel} ayrildi`]: num(r.period_minus),
      };
      for (const k of kinds) row[k.label] = r.counts[k.key] || 0;
      row[reprimand.label] = r.counts[reprimand.key] || 0;
      row["Jazo"] = r.sanction?.text || "";
      return row;
    }));
  };

  const years = [now.getFullYear(), now.getFullYear() - 1];
  const canSave =
    !busy && !!f.user_id && !!f.date &&
    (!isRep || (Number(f.points) !== 0 && !!f.note.trim()));

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Award size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Na'munali xodim
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Har xodim yilni {rules?.start ?? 100} ball bilan boshlaydi.
        Qoidabuzarlik uchun ball ayiriladi, bir oyda takrorlansa jarima
        oshib boradi.
      </p>

      <SectionInsights section="namunali" />

      {/* ---- Bo'limlar ---- */}
      {d?.sections?.length === 1 && (
        <p className="text-sm font-semibold text-brand-700 border-b border-slate-200 pb-2.5 mb-5">
          {d.sections[0].label}
        </p>
      )}
      {d?.sections?.length > 1 && (
        <div className="flex gap-2 mb-5 overflow-x-auto pt-0.5 pb-2 px-0.5">
          {d.sections.map((s: Any) => (
            <button
              key={s.key}
              onClick={() => setSection(s.key)}
              className={tab3d(section === s.key, "amber")}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* ---- Filtrlar ---- */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative">
          <Search
            size={14}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Xodim qidirish"
            className="pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 text-sm w-52"
          />
        </div>
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
        >
          <option value={0}>Butun yil</option>
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>{m}</option>
          ))}
        </select>
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
        >
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
        <button
          onClick={() => setShowRules(!showRules)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
        >
          <Info size={14} /> Qoidalar va jazolar
        </button>
        <div className="flex gap-2 ml-auto">
          {d?.can_import && (
            <button
              onClick={() => setShowImport(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
            >
              <Upload size={14} /> Excel'dan import
            </button>
          )}
          <button
            onClick={exportXlsx}
            disabled={!rows.length}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
          >
            <Download size={14} /> Excel
          </button>
        </div>
      </div>
      {showImport && (
        <ConductImport
          onClose={() => setShowImport(false)}
          onDone={load}
        />
      )}

      {/* ---- Qoidalar ---- */}
      {showRules && rules && (
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
            <p className="text-sm font-medium text-slate-700 px-4 pt-3 pb-1">
              Bir oy ichida nechanchi marta — nechta ball ayiriladi
            </p>
            <table className="w-full text-sm">
              <thead className="text-slate-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Holat</th>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <th key={n} className="text-right px-2 py-2 font-medium">
                      {n === 5 ? "5+" : n}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {kinds.map((k) => (
                  <tr key={k.key}>
                    <td className="px-4 py-2 text-slate-700">{k.label}</td>
                    {k.steps.map((s: number, i: number) => (
                      <td key={i} className="px-2 py-2 text-right text-red-600">
                        −{s}
                      </td>
                    ))}
                  </tr>
                ))}
                <tr>
                  <td className="px-4 py-2 text-slate-700">{reprimand.label}</td>
                  <td colSpan={5} className="px-2 py-2 text-right text-slate-500 text-xs">
                    ball qo'lda yoziladi (manfiy son — ball qaytariladi)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
            <p className="text-sm font-medium text-slate-700 px-4 pt-3 pb-1">
              Jazo — qolgan ball shu chegaraga tushsa
            </p>
            <table className="w-full text-sm">
              <thead className="text-slate-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Ball</th>
                  <th className="text-left px-3 py-2 font-medium">Ustoz</th>
                  <th className="text-left px-3 py-2 font-medium">
                    Boshqa xodimlar
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[...rules.sanctions].reverse().map((s: Any) => (
                  <tr key={s.level}>
                    <td className="px-4 py-2 font-medium text-slate-800">
                      {s.limit} va past
                    </td>
                    <td className="px-3 py-2 text-slate-600">{s.teacher}</td>
                    <td className="px-3 py-2 text-slate-600">{s.other}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-slate-400 px-4 py-2">
              Ball yil boshida {rules.start} dan boshlanadi. Hisob har oy
              1-martadan boshlanadi, ayirilgan ball esa yil davomida
              yig'iladi.
            </p>
          </div>
        </div>
      )}

      {/* ---- Minus yozish ---- */}
      {d?.can_manage && rules && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-3">
            Minus yozish
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={f.user_id}
              onChange={(e) => setF({ ...f, user_id: e.target.value })}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white min-w-[200px]"
            >
              <option value="">Xodimni tanlang</option>
              {byName.map((r) => (
                <option key={r.user_id} value={r.user_id}>
                  {r.name} — {r.role_label}
                </option>
              ))}
            </select>
            <select
              value={f.kind}
              onChange={(e) => setF({ ...f, kind: e.target.value })}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white"
            >
              {kinds.map((k) => (
                <option key={k.key} value={k.key}>{k.label}</option>
              ))}
              <option value={reprimand.key}>{reprimand.label}</option>
            </select>
            <input
              type="date"
              value={f.date}
              max={todayIso()}
              onChange={(e) => setF({ ...f, date: e.target.value })}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
            />
            {isRep && (
              <input
                type="number"
                step={0.5}
                min={-reprimand.max}
                max={reprimand.max}
                value={f.points}
                onChange={(e) => setF({ ...f, points: e.target.value })}
                placeholder="Ball"
                title="Musbat — ayiriladi, manfiy — qaytariladi"
                className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm w-20"
              />
            )}
            <input
              value={f.note}
              onChange={(e) => setF({ ...f, note: e.target.value })}
              placeholder={isRep ? "Sabab (majburiy)" : "Izoh (ixtiyoriy)"}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm flex-1 min-w-[180px]"
            />
            <button
              onClick={save}
              disabled={!canSave}
              className="bg-red-600 hover:bg-red-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-40"
            >
              Minus yozish
            </button>
          </div>
          {preview && (
            <p className="text-xs text-slate-500 mt-2">
              Bu xodimga shu oyda {preview.nth}-marta →{" "}
              <b className="text-red-600">−{preview.pts} ball</b>
            </p>
          )}
          {isRep && (
            <p className="text-xs text-slate-500 mt-2">
              Musbat son ball ayiradi, manfiy son ball qaytaradi.
            </p>
          )}
          {msg && <p className="text-xs text-emerald-700 mt-2">{msg}</p>}
        </div>
      )}

      {err && (
        <p className="text-sm text-slate-500 py-6 text-center">{err}</p>
      )}
      {!d && !err && (
        <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>
      )}

      {d && (
        <>
          {/* ---- Xodimlar ballari ---- */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto mb-4">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
                  <th className="text-center px-3 py-2.5 font-medium">
                    Qolgan ball
                  </th>
                  <th className="text-right px-3 py-2.5 font-medium">
                    {year}-yil −
                  </th>
                  <th className="text-right px-3 py-2.5 font-medium whitespace-nowrap">
                    {month ? MONTHS[month - 1] : "Yil"} −
                  </th>
                  {kinds.map((k) => (
                    <th
                      key={k.key}
                      title={`${periodLabel}: necha marta`}
                      className="text-right px-2 py-2.5 font-medium"
                    >
                      {k.label}
                    </th>
                  ))}
                  <th className="text-right px-2 py-2.5 font-medium">Xayfsan</th>
                  <th className="text-left px-4 py-2.5 font-medium">Jazo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {shown.map((r) => (
                  <Fragment key={r.user_id}>
                    <tr
                      onClick={() =>
                        setOpen(open === r.user_id ? null : r.user_id)}
                      className="cursor-pointer hover:bg-slate-50"
                    >
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">
                          {open === r.user_id ? (
                            <ChevronDown size={14} className="text-slate-400" />
                          ) : (
                            <ChevronRight size={14} className="text-slate-400" />
                          )}
                          <div>
                            <p className="text-slate-900 font-medium">{r.name}</p>
                            <p className="text-xs text-slate-400">
                              {r.role_label}
                              {r.branch ? ` · ${r.branch}` : ""}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-2.5 text-center">
                        <span
                          className={`inline-block min-w-[3rem] rounded-full px-2 py-0.5 text-sm font-semibold ${scoreTone(r.remaining)}`}
                        >
                          {num(r.remaining)}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-right text-slate-700">
                        {r.year_minus ? minusText(r.year_minus) : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right text-slate-700">
                        {r.period_minus ? minusText(r.period_minus) : "—"}
                      </td>
                      {kinds.map((k) => (
                        <td
                          key={k.key}
                          className="px-2 py-2.5 text-right text-slate-600"
                        >
                          {r.counts[k.key] || ""}
                        </td>
                      ))}
                      <td className="px-2 py-2.5 text-right text-slate-600">
                        {r.counts[reprimand.key] || ""}
                      </td>
                      <td className="px-4 py-2.5 text-xs">
                        {r.sanction ? (
                          <span
                            className={
                              r.sanction.level === "warning"
                                ? "text-orange-700"
                                : "text-red-700 font-medium"
                            }
                          >
                            {r.sanction.text}
                          </span>
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                    </tr>
                    {open === r.user_id && (
                      <tr>
                        <td
                          colSpan={6 + kinds.length}
                          className="bg-slate-50 px-6 py-3"
                        >
                          <History userId={r.user_id} year={year} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
            {shown.length === 0 && (
              <p className="text-sm text-slate-400 py-8 text-center">
                Xodim topilmadi.
              </p>
            )}
          </div>

          {/* ---- Jurnal ---- */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
            <p className="text-sm font-medium text-slate-700 px-4 pt-3 pb-2">
              Kimga, qachon, qanday minus yozildi — {periodLabel}
            </p>
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Sana</th>
                  <th className="text-left px-3 py-2 font-medium">Xodim</th>
                  <th className="text-left px-3 py-2 font-medium">
                    Qoidabuzarlik
                  </th>
                  <th className="text-center px-3 py-2 font-medium">
                    Oyda nechanchi
                  </th>
                  <th className="text-right px-3 py-2 font-medium">Ball</th>
                  <th className="text-left px-3 py-2 font-medium">Izoh</th>
                  <th className="text-left px-3 py-2 font-medium">Kim yozdi</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {log
                  .filter((e) =>
                    !q.trim() ||
                    e.name.toLowerCase().includes(q.trim().toLowerCase()))
                  .map((e) => (
                    <tr key={e.id}>
                      <td className="px-4 py-2 text-slate-600 whitespace-nowrap">
                        {e.date}
                      </td>
                      <td className="px-3 py-2 text-slate-900">{e.name}</td>
                      <td className="px-3 py-2 text-slate-700">{e.kind_label}</td>
                      <td className="px-3 py-2 text-center text-slate-500">
                        {e.nth ? `${e.nth}-marta` : "—"}
                      </td>
                      <td
                        className={`px-3 py-2 text-right font-semibold whitespace-nowrap ${
                          e.points < 0 ? "text-emerald-600" : "text-red-600"
                        }`}
                      >
                        {minusText(e.points)}
                      </td>
                      <td className="px-3 py-2 text-slate-500">{e.note || ""}</td>
                      <td className="px-3 py-2 text-xs text-slate-400 whitespace-nowrap">
                        {e.created_by || "—"}
                        {e.created_at && (
                          <span className="block">{localTime(e.created_at)}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right">
                        {e.can_delete && (
                          <button
                            onClick={() => remove(e)}
                            title="O'chirish"
                            className="text-slate-400 hover:text-red-600 p-1"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
            {log.length === 0 && (
              <p className="text-sm text-slate-400 py-6 text-center">
                {periodLabel} uchun minus yozilmagan.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
