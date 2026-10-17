import { useEffect, useState } from "react";
import { Award, BadgeCheck, ChevronDown, ChevronUp, CircleAlert, Clock, Undo2, X } from "lucide-react";
import { CertFields } from "../components/wordbank/CertFields";
import { CertFilePreview } from "../components/wordbank/CertFilePreview";
import { getGlobalBranch } from "../lib/api";
import { formatDate, formatDateTime } from "../lib/format";
import { pushToast } from "../lib/toast";
import {
  CERT_REJECT_REASONS,
  CERT_VERIFY_METHODS,
  confirmCert,
  rejectCert,
  revokeCert,
  wbQuietGet,
  type CertRejectReason,
  type CertVerifyMethod,
  type StaffCert,
  type StaffCertList,
  type WbQuiet,
} from "../lib/wordbankApi";
import { draftFromStaff, draftToForm, fmtBytes, pickPref, writePref } from "../lib/wordbankUi";

/**
 * SERTIFIKATLAR TEKSHIRUVI (2026-10-17, "So'z bilish", OWNER D3).
 *
 * O'quvchi profilda yuklagan sertifikat shu yerda tekshiriladi:
 * faylni ko'rish, kerak bo'lsa natijani tuzatish, tekshirish usulini
 * tanlab tasdiqlash yoki sabab bilan rad etish. Tasdiqlangandan keyingina
 * natija o'quvchi profilida, reytingda va ota-ona sahifasida ✓ bilan
 * chiqadi. Bekor qilish (tasdiqlanganini) — asoschi, filial rahbari va
 * o'quv bo'limi rahbari.
 *
 * Kim nimani ko'radi — serverda: ustoz faqat o'z guruhlari o'quvchilarini,
 * filial rahbari/administrator o'z filialini, o'quv bo'limi rahbari va
 * asoschi hammasini. Navbat eng eskisidan boshlanadi; 3 kundan ortiq
 * kutayotgani qizil. Fayl token bilan olinadi (blob URL), PDF sandbox'li
 * iframe ichida ochiladi.
 */

type Tab = "pending" | "confirmed" | "rejected";
const TABS: readonly [Tab, string, string][] = [
  ["pending", "Kutilmoqda", "pending"],
  ["confirmed", "Tasdiqlangan", "confirmed"],
  ["rejected", "Rad etilgan", "rejected,revoked"],
];
const TAB_KEYS = TABS.map(([k]) => k);
const K_TAB = "jony_vc_tab";

const box = "bg-white rounded-xl border border-slate-200 shadow-sm";
const input = "w-full min-h-[44px] rounded-xl border border-slate-300 bg-white px-3 py-2 text-[15px] text-slate-900";

export default function VocabCerts() {
  const [tab, setTab] = useState<Tab>(() => pickPref(K_TAB, TAB_KEYS, "pending"));
  const [res, setRes] = useState<WbQuiet<StaffCertList> | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  const [openId, setOpenId] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const status = TABS.find(([k]) => k === tab)?.[2] || "pending";
    const q = new URLSearchParams({ status });
    // Tepadagi umumiy filial tanlagichi — server uni qamrov ichida filtr qiladi
    const br = getGlobalBranch();
    if (br) q.set("branch_id", br);
    // Jim o'qish: bo'lim butunlay o'chiq bo'lsa (404) toast chiqmaydi
    wbQuietGet<StaffCertList>(`/wordbank/certs?${q.toString()}`).then((r) => {
      if (!alive) return;
      setRes(r);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [tab, tick]);

  const chooseTab = (t: Tab) => {
    setTab(t);
    setOpenId(null);
    writePref(K_TAB, t);
  };
  const reload = () => setTick((t) => t + 1);

  const d = res?.status === "ok" ? res.data : null;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-2 mb-1">
        <Award size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Sertifikatlar tekshiruvi</h1>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        O'quvchilar yuklagan IELTS, CEFR va boshqa sertifikatlar. Tasdiqlangach
        natija o'quvchi profilida, "So'z bilish" reytingida va ota-ona
        sahifasida ✓ belgi bilan chiqadi. Tasdiqlanmagan natijani hech kim
        ko'rmaydi.
      </p>

      {res?.status === "off" ? (
        <div className={`${box} p-6 text-center`}>
          <p className="text-sm text-slate-600">"So'z bilish" bo'limi hali yoqilmagan.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1 mb-4" role="tablist">
            {TABS.map(([k, label]) => {
              const n = d ? d.counts[k] : null;
              return (
                <button key={k} type="button" role="tab" aria-selected={tab === k}
                  onClick={() => chooseTab(k)}
                  className={`min-h-[40px] rounded-lg text-[13px] font-semibold px-1 ${
                    tab === k ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}>
                  {label}
                  {n !== null && n > 0 && (
                    <span className={`ml-1 inline-flex min-w-[20px] justify-center rounded-full px-1.5 text-[11px] ${
                      k === "pending" ? "bg-amber-500 text-white" : "bg-slate-200 text-slate-700"}`}>
                      {n}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {res?.status === "error" && (
            <div className={`${box} p-4 text-sm text-red-600`}>
              {res.message}{" "}
              <button type="button" onClick={reload} className="underline font-semibold">
                Qayta urinish
              </button>
            </div>
          )}
          {!res && <p className="text-sm text-slate-400">Yuklanmoqda…</p>}

          {d && (
            <div className={`space-y-3 ${loading ? "opacity-60" : ""}`}>
              {d.items.length === 0 && (
                <div className={`${box} p-6 text-center text-sm text-slate-500`}>
                  {tab === "pending"
                    ? "Tekshiruvni kutayotgan sertifikat yo'q."
                    : tab === "confirmed"
                      ? "Hali tasdiqlangan sertifikat yo'q."
                      : "Rad etilgan yoki bekor qilingan sertifikat yo'q."}
                </div>
              )}
              {d.items.map((c) => (
                <CertCard
                  key={c.id}
                  c={c}
                  canRevoke={d.can_revoke}
                  open={openId === c.id}
                  onToggle={() => setOpenId(openId === c.id ? null : c.id)}
                  onChanged={() => {
                    setOpenId(null);
                    reload();
                  }}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function CertCard({
  c,
  canRevoke,
  open,
  onToggle,
  onChanged,
}: {
  c: StaffCert;
  canRevoke: boolean;
  open: boolean;
  onToggle: () => void;
  onChanged: () => void;
}) {
  const pending = c.status === "pending";
  const late = (c.days_waiting ?? 0) > 3;
  const meta = [c.branch_name, c.groups.length ? c.groups.join(", ") : null].filter(Boolean).join(" · ");

  return (
    <div className={`${box} p-4 ${late && pending ? "border-l-4 border-l-red-500" : ""}`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-[15px] font-semibold text-slate-900 break-words">
            {c.student_name}
            {c.student_public_id && (
              <span className="ml-1.5 text-[12px] font-normal text-slate-400">{c.student_public_id}</span>
            )}
            {!c.student_exists && (
              <span className="ml-1.5 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                o'chirilgan
              </span>
            )}
          </p>
          {meta && <p className="text-[12px] text-slate-500 break-words">{meta}</p>}
          <p className="text-[14px] text-slate-800 mt-1.5">
            <b>{c.result_label || c.exam_label}</b>
            {c.test_date && <span className="text-slate-500"> · test {formatDate(c.test_date)}</span>}
            {c.cert_no && <span className="text-slate-500"> · № {c.cert_no}</span>}
          </p>
          <p className="text-[11.5px] text-slate-400 mt-0.5">
            Yuklangan: {formatDateTime(c.created_at, false)}
            {c.size ? ` · ${fmtBytes(c.size)}` : ""}
            {c.mime ? ` · ${c.mime.includes("pdf") ? "PDF" : "rasm"}` : ""}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <StatusPill c={c} />
          {pending && c.days_waiting !== null && (
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
              late ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600"}`}>
              <Clock size={11} />
              {c.days_waiting === 0 ? "bugun" : `${c.days_waiting} kun kutmoqda`}
            </span>
          )}
        </div>
      </div>

      {c.duplicate_warning && (
        <p className="mt-2 flex items-start gap-1.5 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-[12.5px] font-semibold text-red-700">
          <CircleAlert size={15} className="shrink-0 mt-0.5" /> {c.duplicate_warning}
        </p>
      )}

      <DecisionTrail c={c} />

      <button type="button" onClick={onToggle}
        className="mt-2 inline-flex items-center gap-1 min-h-[40px] text-[13px] font-semibold text-brand-600">
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        {open ? "Yopish" : pending ? "Tekshirish" : "Faylni ko'rish"}
      </button>

      {open && (
        <div className="mt-2 grid gap-4 md:grid-cols-2">
          <div className="min-w-0">
            <CertFilePreview path={`/wordbank/certs/${c.id}/file`} mime={c.mime}
                             name={`sertifikat-${c.id}`} />
          </div>
          <div className="min-w-0">
            {pending && <ReviewForm c={c} onChanged={onChanged} />}
            {c.status === "confirmed" && canRevoke && <RevokeForm c={c} onChanged={onChanged} />}
            {c.status === "confirmed" && !canRevoke && (
              <p className="text-[12px] text-slate-500">
                Tasdiqni bekor qilish — asoschi, filial rahbari yoki o'quv bo'limi rahbari.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusPill({ c }: { c: StaffCert }) {
  const base = "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap";
  switch (c.status) {
    case "pending":
      return <span className={`${base} bg-amber-100 text-amber-800`}>Kutilmoqda</span>;
    case "confirmed":
      return <span className={`${base} bg-emerald-100 text-emerald-700`}><BadgeCheck size={12} /> Tasdiqlangan</span>;
    case "rejected":
      return <span className={`${base} bg-red-100 text-red-700`}>Rad etilgan</span>;
    case "revoked":
      return <span className={`${base} bg-slate-200 text-slate-700`}>Bekor qilingan</span>;
    default:
      return <span className={`${base} bg-slate-100 text-slate-600`}>Qaytarib olingan</span>;
  }
}

/** Kim, qachon, qanday qaror qildi — tasdiq/rad/bekor izi. */
function DecisionTrail({ c }: { c: StaffCert }) {
  if (c.status === "confirmed" || c.status === "revoked") {
    return (
      <div className="mt-2 text-[12px] text-slate-600 space-y-0.5">
        {c.reviewed_at && (
          <p>
            Tasdiqladi: <b>{c.reviewed_by_name || "—"}</b> · {formatDateTime(c.reviewed_at, false)}
            {c.verify_method ? ` · ${c.verify_method}` : ""}
          </p>
        )}
        {c.review_note && <p className="text-slate-500">Izoh: {c.review_note}</p>}
        {c.status === "revoked" && (
          <p className="text-red-700">
            Bekor qildi: <b>{c.revoked_by_name || "—"}</b>
            {c.revoked_at ? ` · ${formatDateTime(c.revoked_at, false)}` : ""}
            {c.revoke_note ? ` — ${c.revoke_note}` : ""}
          </p>
        )}
      </div>
    );
  }
  if (c.status === "rejected") {
    return (
      <p className="mt-2 text-[12px] text-red-700">
        Rad etdi: <b>{c.reviewed_by_name || "—"}</b>
        {c.reviewed_at ? ` · ${formatDateTime(c.reviewed_at, false)}` : ""} · sabab:{" "}
        <b>{c.reject_reason || "—"}</b>
        {c.reject_note ? ` — ${c.reject_note}` : ""}
      </p>
    );
  }
  return null;
}

function ReviewForm({ c, onChanged }: { c: StaffCert; onChanged: () => void }) {
  const [draft, setDraft] = useState(() => draftFromStaff(c));
  const [verify, setVerify] = useState<CertVerifyMethod | "">("");
  const [note, setNote] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState<CertRejectReason | "">("");
  const [rNote, setRNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function confirm() {
    if (busy) return;
    setErr("");
    const v = draftToForm(draft);
    if (v.error !== null) return setErr(v.error);
    if (!verify) return setErr("Qanday tekshirilganini tanlang");
    setBusy(true);
    try {
      const out = await confirmCert(c.id, {
        ...v.form,
        test_date: v.form.test_date,
        verify_method: verify,
        note: note.trim() || null,
      });
      pushToast(`Tasdiqlandi: ${out.result_label || c.exam_label}`, "success", 3000);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Tasdiqlab bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  async function reject() {
    if (busy) return;
    setErr("");
    if (!reason) return setErr("Sababni tanlang");
    if (reason === "boshqa" && !rNote.trim()) return setErr("Sababni qisqacha yozing");
    setBusy(true);
    try {
      await rejectCert(c.id, { reason_code: reason, note: rNote.trim() || null });
      pushToast("Rad etildi — o'quvchiga xabar yuborildi", "success", 3000);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Rad etib bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-[12px] text-slate-500 leading-snug">
        Natijani fayl bilan solishtiring; xato bo'lsa — tuzatib keyin tasdiqlang.
      </p>
      <CertFields value={draft} onChange={setDraft} disabled={busy || rejecting} idPrefix={`rv${c.id}`} />

      {!rejecting && (
        <>
          <div>
            <label htmlFor={`vm${c.id}`} className="block text-[12px] font-semibold text-slate-600 mb-1">
              Qanday tekshirildi
            </label>
            <select id={`vm${c.id}`} value={verify} disabled={busy}
              onChange={(e) => setVerify(e.target.value as CertVerifyMethod | "")}
              className={input}>
              <option value="">Tanlang</option>
              {CERT_VERIFY_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`nt${c.id}`} className="block text-[12px] font-semibold text-slate-600 mb-1">
              Izoh (ixtiyoriy)
            </label>
            <input id={`nt${c.id}`} value={note} maxLength={300} disabled={busy}
              onChange={(e) => setNote(e.target.value)} className={input} />
          </div>
          {!c.student_exists && (
            <p className="text-[12px] text-amber-700">
              O'quvchi bazadan o'chirilgan — tasdiqlab bo'lmaydi, faqat rad etish mumkin.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={confirm} disabled={busy || !c.student_exists}
              className="flex-1 min-w-[140px] min-h-[44px] rounded-xl bg-emerald-600 text-white text-sm font-semibold inline-flex items-center justify-center gap-1.5 disabled:opacity-50">
              <BadgeCheck size={16} /> {busy ? "…" : "Tasdiqlash"}
            </button>
            <button type="button" onClick={() => { setErr(""); setRejecting(true); }} disabled={busy}
              className="flex-1 min-w-[140px] min-h-[44px] rounded-xl border border-red-300 text-red-700 text-sm font-semibold inline-flex items-center justify-center gap-1.5">
              <X size={16} /> Rad etish
            </button>
          </div>
        </>
      )}

      {rejecting && (
        <div className="rounded-xl border border-red-200 bg-red-50/60 p-3 space-y-2">
          <div>
            <label htmlFor={`rr${c.id}`} className="block text-[12px] font-semibold text-slate-600 mb-1">
              Rad etish sababi
            </label>
            <select id={`rr${c.id}`} value={reason} disabled={busy}
              onChange={(e) => setReason(e.target.value as CertRejectReason | "")}
              className={input}>
              <option value="">Tanlang</option>
              {CERT_REJECT_REASONS.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`rn${c.id}`} className="block text-[12px] font-semibold text-slate-600 mb-1">
              O'quvchiga izoh {reason === "boshqa" ? "" : "(ixtiyoriy)"}
            </label>
            <input id={`rn${c.id}`} value={rNote} maxLength={300} disabled={busy}
              placeholder="Masalan: sana ko'rinmayapti, qayta suratga oling"
              onChange={(e) => setRNote(e.target.value)} className={input} />
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={reject} disabled={busy}
              className="flex-1 min-w-[140px] min-h-[44px] rounded-xl bg-red-600 text-white text-sm font-semibold disabled:opacity-50">
              {busy ? "…" : "Rad etishni tasdiqlash"}
            </button>
            <button type="button" onClick={() => setRejecting(false)} disabled={busy}
              className="flex-1 min-w-[140px] min-h-[44px] rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold">
              Orqaga
            </button>
          </div>
        </div>
      )}

      {err && <p role="alert" className="text-[13px] text-red-600">{err}</p>}
    </div>
  );
}

function RevokeForm({ c, onChanged }: { c: StaffCert; onChanged: () => void }) {
  const [asking, setAsking] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function revoke() {
    if (busy) return;
    setErr("");
    if (!note.trim()) return setErr("Bekor qilish sababini yozing");
    setBusy(true);
    try {
      await revokeCert(c.id, { note: note.trim() });
      pushToast("Tasdiq bekor qilindi", "success", 3000);
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Bekor qilib bo'lmadi");
    } finally {
      setBusy(false);
    }
  }

  if (!asking)
    return (
      <button type="button" onClick={() => setAsking(true)}
        className="min-h-[44px] px-4 rounded-xl border border-red-300 text-red-700 text-sm font-semibold inline-flex items-center gap-1.5">
        <Undo2 size={15} /> Tasdiqni bekor qilish
      </button>
    );

  return (
    <div className="rounded-xl border border-red-200 bg-red-50/60 p-3 space-y-2">
      <p className="text-[12.5px] text-slate-700 leading-snug">
        Natija o'quvchi profili, reyting va ota-ona sahifasidan olib tashlanadi.
        Fayl va tarix saqlanadi.
      </p>
      <label htmlFor={`rv-note${c.id}`} className="block text-[12px] font-semibold text-slate-600">
        Sabab
      </label>
      <input id={`rv-note${c.id}`} value={note} maxLength={300} disabled={busy}
        onChange={(e) => setNote(e.target.value)} className={input} />
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={revoke} disabled={busy}
          className="flex-1 min-w-[140px] min-h-[44px] rounded-xl bg-red-600 text-white text-sm font-semibold disabled:opacity-50">
          {busy ? "…" : "Bekor qilish"}
        </button>
        <button type="button" onClick={() => setAsking(false)} disabled={busy}
          className="flex-1 min-w-[140px] min-h-[44px] rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold">
          Orqaga
        </button>
      </div>
      {err && <p role="alert" className="text-[13px] text-red-600">{err}</p>}
    </div>
  );
}
