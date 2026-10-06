import { useEffect, useState } from "react";
import { formatPhone } from "./PhoneInput";
import { X, Copy, Send, Play, Link as LinkIcon, GraduationCap, Trash2 } from "lucide-react";
import { api } from "../lib/api";

// Ingliz tili diagnostik testi — Lidlar sahifasining tepasida.
// Lid tanlanadi → "Shu yerda" (test shu qurilmada ochiladi) yoki
// "Havola" (telefoniga bir martalik havola). Natija lidga o'zi tushadi:
// bosqich (Step 1..4 / IELTS), CEFR darajasi va uniti. Kitob nomi
// ko'rsatilmaydi (2026-09-15).

type Any = any;
const inp = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm";

/** BARABAN (2026-09-25): test oxirida tushgan sovg'a. Admin o'quvchi
 *  ochayotganda ko'rib tursin — sovg'a avtomat qo'llanadi, lekin
 *  odam "menga 30% tushgan edi" desa, shu yerdan tekshiradi. */
export function WheelBadge({ lead }: { lead: Any }) {
  const w = lead?.wheel;
  if (!w?.prize) return null;
  const p = w.prize;
  const isDisc = p.kind === "discount" || p.kind === "discount_sum";
  const txt = p.kind === "discount" ? `${p.value}% chegirma`
    : p.kind === "discount_sum" ? `${Number(p.value).toLocaleString("ru-RU")} so'm chegirma`
    : `${p.value} tanga`;
  const tip = isDisc
    ? `Baraban: ${txt} — faqat BIRINCHI oyga, faollashganda avtomat${w.applied ? " (qo'llangan)" : ""}`
    : `Baraban: ${txt} — o'quvchi ochilganda avtomat${w.applied ? " (qo'llangan)" : ""}`;
  return (
    <span title={tip}
          className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold ${
            w.applied ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"}`}>
      🎁 {txt}
    </span>
  );
}

export function PlacementBadge({ lead }: { lead: Any }) {
  const p = lead?.placement;
  const o = lead?.placement_open;
  if (p) {
    return (
      <>
        <span title={`${p.book} · Unit ${p.unit} · ${p.score}/${p.total} · ${p.date}`}
              className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 rounded px-1.5 py-0.5 text-[11px] font-semibold">
          <GraduationCap size={11} /> {p.level} · U{p.unit}
        </span>
        <WheelBadge lead={lead} />
      </>
    );
  }
  if (o) {
    return (
      <span className="inline-block bg-amber-50 text-amber-700 rounded px-1.5 py-0.5 text-[11px]">
        {o.status === "running" ? "test ishlanmoqda" : "havola yuborilgan"}
      </span>
    );
  }
  return null;
}

export default function PlacementBar({ leads, onChanged }: {
  leads: Any[]; onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<Any[]>([]);
  const [showAll, setShowAll] = useState(false);

  function loadRows() {
    api.get<Any>("/placement/sessions?limit=12").then((r) => setRows(r.rows || [])).catch(() => {});
  }
  useEffect(() => { loadRows(); }, []);

  /** Tugallangan diagnostikalarni JSON faylga — Jony School'dagi
   *  "JonyOS diagnostikasini import" o'qiydi (ikki tizim alohida
   *  bazada; parol ko'chirilmaydi, fayl ko'chiriladi). */
  async function exportSchool() {
    try {
      const r = await api.get<Any>("/placement/export?days=30");
      if (!r.count) { alert("Oxirgi 30 kunda tugallangan diagnostika yo'q"); return; }
      const blob = new Blob([JSON.stringify(r, null, 1)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `jonyos_diagnostika_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      alert("Eksport bo'lmadi — qayta urinib ko'ring");
    }
  }

  const done = rows.filter((r) => r.status === "done");
  const live = rows.filter((r) => r.status === "running" || r.status === "new");

  return (
    <div className="mb-5 rounded-xl border border-indigo-100 bg-indigo-50/50 p-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-sm font-medium text-indigo-900">
          <GraduationCap size={16} /> Ingliz tili diagnostikasi
          <span className="text-xs font-normal text-indigo-700/70">50 savol · 30 s · adaptiv · Step 1 – IELTS (A1–C1)</span>
        </div>
        <button onClick={() => setOpen(true)}
                className="ml-auto flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-700">
          <Play size={14} /> Test boshlash
        </button>
        <button onClick={() => { setShowAll((v) => !v); loadRows(); }}
                className="rounded-lg border border-indigo-200 bg-white px-3 py-1.5 text-sm text-indigo-800">
          Natijalar {done.length > 0 && `(${done.length})`}
        </button>
        <button onClick={exportSchool}
                title="Oxirgi 30 kundagi tugallangan diagnostikalar JSON faylga — Jony School → Kompyuter testlari → 'JonyOS diagnostikasini import' orqali Jony 360 ga tushadi"
                className="rounded-lg border border-indigo-200 bg-white px-3 py-1.5 text-sm text-indigo-800">
          Jony School'ga eksport
        </button>
      </div>
      <a href="/nemis-test" target="_blank" rel="noreferrer" className="mt-3 inline-flex rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700">Nemis tili kirish testi · A1–B1 →</a>
      {live.length > 0 && (
        <p className="mt-2 text-xs text-amber-700">
          Kutilmoqda: {live.map((r) => r.name + (r.status === "running" ? ` (${r.answered}/50)` : "")).join(", ")}
        </p>
      )}
      {showAll && (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white">
          {rows.length === 0 && <p className="p-3 text-xs text-slate-400">Hali test ishlanmagan</p>}
          {rows.map((r) => (
            <ResultRow key={r.id} r={r} onDelete={() => {
              if (!confirm(`${r.name} — test yozuvini o'chirasizmi?`)) return;
              api.delete(`/placement/sessions/${r.id}`).then(() => { loadRows(); onChanged(); }).catch(() => {});
            }} />
          ))}
        </div>
      )}
      {open && (
        <StartModal leads={leads} onClose={() => setOpen(false)}
                    onDone={() => { loadRows(); onChanged(); }} />
      )}
    </div>
  );
}

function ResultRow({ r, onDelete }: { r: Any; onDelete: () => void }) {
  const [more, setMore] = useState(false);
  const res = r.result;
  const st: Record<string, string> = {
    done: "bg-emerald-50 text-emerald-700", running: "bg-amber-50 text-amber-700",
    new: "bg-slate-100 text-slate-600", expired: "bg-red-50 text-red-600" };
  const stL: Record<string, string> = { done: "Tugadi", running: "Ishlanmoqda", new: "Havola yuborildi", expired: "Muddati o'tdi" };
  return (
    <div className="border-b border-slate-100 last:border-0 px-3 py-2 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-slate-800">{r.name}</span>
        <span className="text-xs text-slate-400">{formatPhone(r.phone)}</span>
        <span className={`rounded px-1.5 py-0.5 text-[11px] ${st[r.status] || ""}`}>{stL[r.status] || r.status}</span>
        {res && (
          <button onClick={() => setMore((v) => !v)}
                  className="ml-auto rounded bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700">
            {res.book} · U{res.unit} · {res.score}/{res.total}
          </button>
        )}
        {res && r.token && (
          <a href={`/placement-report.html?t=${encodeURIComponent(r.token)}`} target="_blank" rel="noopener"
             className="rounded border border-indigo-200 px-2 py-0.5 text-xs text-indigo-700 hover:bg-indigo-50">
            Hisobot
          </a>
        )}
        {!res && <span className="ml-auto text-xs text-slate-400">{r.mode === "office" ? "shu yerda" : "havola"} · {r.created_by}</span>}
        <button onClick={onDelete} className="text-slate-300 hover:text-red-500"><Trash2 size={13} /></button>
      </div>
      {more && res && (
        <div className="mt-2 rounded-lg bg-slate-50 p-2 text-xs text-slate-700">
          <p className="font-medium">{res.advice}</p>
          <p className="text-slate-500">Unit mavzusi: {res.topic}</p>
          {(res.topics || []).length > 0 && (
            <div className="mt-1 space-y-0.5">
              {(res.topics || []).map((t: Any) => (
                <div key={`${t.level}-${t.unit}`} className="flex items-center gap-2">
                  <span className="w-12 shrink-0 text-slate-400">{t.level}</span>
                  <span className="flex-1 truncate">{t.topic}</span>
                  <span className={`w-10 text-right font-semibold ${
                    t.pct >= 75 ? "text-emerald-600" : t.pct >= 50 ? "text-amber-600" : "text-red-600"
                  }`}>{t.pct}%</span>
                </div>
              ))}
            </div>
          )}
          <div className="mt-1 flex flex-wrap gap-2">
            {(res.per_level || []).map((x: Any) => (
              <span key={x.level} className="rounded bg-white border border-slate-200 px-1.5 py-0.5">
                {x.level}: {x.ok}/{x.n} ({x.pct}%)
              </span>
            ))}
          </div>
          <p className="mt-1 text-slate-400">{res.note} · {r.finished_at?.slice(0, 16).replace("T", " ")}</p>
        </div>
      )}
    </div>
  );
}

function StartModal({ leads, onClose, onDone }: {
  leads: Any[]; onClose: () => void; onDone: () => void;
}) {
  const [q, setQ] = useState("");
  const [lead, setLead] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [link, setLink] = useState<Any>(null);
  const [copied, setCopied] = useState(false);

  const hits = q.trim().length >= 2
    ? leads.filter((l) => (l.full_name || "").toLowerCase().includes(q.trim().toLowerCase())
        || (l.phone || "").includes(q.trim())).slice(0, 8)
    : [];

  async function create(mode: "office" | "link") {
    if (!lead) { setErr("Avval lidni tanlang"); return; }
    setBusy(true); setErr("");
    try {
      const r = await api.post<Any>("/placement/sessions", { lead_id: lead.id, mode });
      if (mode === "office") {
        window.open(r.url, "_blank", "noopener");
        onDone();
        onClose();
      } else {
        setLink(r);
        onDone();
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  }

  function copy() {
    navigator.clipboard?.writeText(link.url).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); });
  }
  const tgText = `Assalomu alaykum, ${lead?.full_name || ""}! Jony Academy ingliz tili darajasini aniqlash testi. 50 savol, har biriga 30 soniya. Havola bir marta ishlaydi: `;
  const tgUrl = link ? `https://t.me/share/url?url=${encodeURIComponent(link.url)}&text=${encodeURIComponent(tgText)}` : "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Diagnostik test</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
        </div>

        {!link && (
          <div className="space-y-3">
            {!lead ? (
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Lid</label>
                <input value={q} onChange={(e) => setQ(e.target.value)} className={inp}
                       placeholder="Ism yoki telefon..." autoFocus />
                {hits.length > 0 && (
                  <div className="mt-1 max-h-48 overflow-y-auto rounded-lg border border-slate-200">
                    {hits.map((l) => (
                      <button key={l.id} onClick={() => setLead(l)}
                              className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50">
                        <span>{l.full_name}</span>
                        <span className="text-xs text-slate-400">{formatPhone(l.phone)}</span>
                      </button>
                    ))}
                  </div>
                )}
                {q.trim().length >= 2 && hits.length === 0 && (
                  <p className="mt-1 text-xs text-slate-400">Topilmadi — avval "Yangi lid" orqali qo'shing.</p>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <div>
                  <p className="font-medium text-slate-800">{lead.full_name}</p>
                  <p className="text-xs text-slate-500">{formatPhone(lead.phone)}</p>
                </div>
                <button onClick={() => setLead(null)} className="text-xs text-slate-400 hover:text-slate-600">o'zgartirish</button>
              </div>
            )}
            {lead?.placement && (
              <p className="text-xs text-amber-700">
                Bu lid testni ishlagan: {lead.placement.level} · Unit {lead.placement.unit} ({lead.placement.date}). Yangi test eskisini almashtirmaydi — ikkalasi ham saqlanadi.
              </p>
            )}
            {err && <p className="text-sm text-red-600">{err}</p>}
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => create("office")} disabled={busy || !lead}
                      className="flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 py-2.5 text-sm text-white disabled:opacity-50">
                <Play size={14} /> Shu yerda ishlatish
              </button>
              <button onClick={() => create("link")} disabled={busy || !lead}
                      className="flex items-center justify-center gap-1.5 rounded-lg border border-indigo-200 bg-white py-2.5 text-sm text-indigo-800 disabled:opacity-50">
                <LinkIcon size={14} /> Havola yuborish
              </button>
            </div>
            <p className="text-xs text-slate-400">
              "Shu yerda" — test yangi oynada ochiladi, planshet/kompyuterni odamga berasiz.
              "Havola" — bir martalik, 48 soat amal qiladi, telefonida ishlaydi.
            </p>
          </div>
        )}

        {link && (
          <div className="space-y-3">
            <p className="text-sm text-slate-700">
              <span className="font-medium">{lead?.full_name}</span> uchun bir martalik havola{link.reused ? " (avvalgisi — hali ishlanmagan)" : ""}:
            </p>
            <div className="break-all rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700">{link.url}</div>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={copy} className="flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 py-2 text-sm">
                <Copy size={14} /> {copied ? "Nusxalandi ✓" : "Nusxalash"}
              </button>
              <a href={tgUrl} target="_blank" rel="noopener"
                 className="flex items-center justify-center gap-1.5 rounded-lg bg-sky-500 py-2 text-sm text-white">
                <Send size={14} /> Telegram
              </a>
            </div>
            <p className="text-xs text-slate-400">Natija tugashi bilan lid kartasida ko'rinadi.</p>
            <button onClick={onClose} className="w-full rounded-lg bg-slate-900 py-2 text-sm text-white">Yopish</button>
          </div>
        )}
      </div>
    </div>
  );
}
