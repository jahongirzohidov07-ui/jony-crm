import { useEffect, useRef, useState } from "react";
import {
  Award, BadgeCheck, ChevronDown, ChevronUp, CircleAlert, Clock, ExternalLink,
  EyeOff, Link2, RotateCcw, Search, Send, Undo2, X,
} from "lucide-react";
import { CertFields } from "../components/wordbank/CertFields";
import { CertFilePreview } from "../components/wordbank/CertFilePreview";
import { useAuth } from "../lib/AuthContext";
import { ApiError, getGlobalBranch } from "../lib/api";
import { formatDate, formatDateTime } from "../lib/format";
import { can, VOCAB_CERT_REVOKE } from "../lib/roles";
import { pushToast } from "../lib/toast";
import {
  CERT_REJECT_REASONS,
  CERT_VERIFY_METHODS,
  confirmCert,
  dismissTgResult,
  getTgResults,
  linkTgResult,
  rejectCert,
  revokeCert,
  searchStaffStudents,
  TG_DUP,
  wbQuietGet,
  type CertRejectReason,
  type CertVerifyMethod,
  type StaffCert,
  type StaffCertList,
  type StaffStudentHit,
  type TgList,
  type TgRow,
  type TgStatus,
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
 *
 * TELEGRAM NATIJALARI (2026-10-17): kanaldagi (t.me/JonyAcademy) natija
 * postlari avtomat bog'langanda ko'pchiligi qolib ketdi — CRM dagi ism
 * yozilishi boshqacha (-xon/-oy, o'/u, dj/j, ruscha yozilish). Alohida
 * tabda xodim ularni qo'lda o'quvchiga bog'laydi yoki "Bizniki emas" deb
 * yashiradi. Bog'langan natija DARHOL tasdiqlangan sertifikat bo'ladi
 * (egasi qarori, tekshiruv navbatisiz). Tab faqat VOCAB_CERT_REVOKE
 * (asoschi, filial rahbari, o'quv bo'limi rahbari) uchun chiziladi —
 * boshqa rolda so'rov umuman yuborilmaydi. "So'z bilish" filial
 * bayrog'iga bog'liq emas: bo'lim yopiq bo'lsa ham bu tab ishlaydi.
 */

type Tab = "pending" | "confirmed" | "rejected";
/** 2026-10-17: sertifikat tablari + "Telegram natijalari". */
type View = Tab | "telegram";
const TABS: readonly [Tab, string, string][] = [
  ["pending", "Kutilmoqda", "pending"],
  ["confirmed", "Tasdiqlangan", "confirmed"],
  ["rejected", "Rad etilgan", "rejected,revoked"],
];
const TAB_KEYS = TABS.map(([k]) => k);
const VIEW_KEYS: readonly View[] = [...TAB_KEYS, "telegram"];
const K_TAB = "jony_vc_tab";

const box = "bg-white rounded-xl border border-slate-200 shadow-sm";
const input = "w-full min-h-[44px] rounded-xl border border-slate-300 bg-white px-3 py-2 text-[15px] text-slate-900";

export default function VocabCerts() {
  const { user } = useAuth();
  // Telegram tabi — faqat VOCAB_CERT_REVOKE (serverda ham shu ro'yxat)
  const canTg = can(user?.role, VOCAB_CERT_REVOKE);
  const [view, setView] = useState<View>(() => pickPref(K_TAB, VIEW_KEYS, "pending"));
  // Oxirgi ochilgan sertifikat tabi: Telegram tabida turganda ham
  // yuqoridagi sonlar shu tab bo'yicha bir marta yuklanadi
  const [tab, setTab] = useState<Tab>(() => pickPref(K_TAB, TAB_KEYS, "pending"));
  const [res, setRes] = useState<WbQuiet<StaffCertList> | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  const [openId, setOpenId] = useState<number | null>(null);
  const [tgCounts, setTgCounts] = useState<Record<TgStatus, number> | null>(null);
  // Saqlangan "telegram" tabi, lekin rol yetmaydi — sertifikatlar ochiladi
  const tg = canTg && view === "telegram";

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

  // 2026-10-17 (review): tab belgisi Telegram tabi ochilmasdan ham
  // ko'rinsin — sonlar bir marta olinadi (status=linked: bu qatorlarga
  // nomzod hisoblanmaydi, eng yengil so'rov). Tab o'zi yuklagan sonlar ustun.
  useEffect(() => {
    if (!canTg) return;
    let alive = true;
    getTgResults("linked").then((r) => {
      if (alive && r.status === "ok") setTgCounts((cur) => cur ?? r.data.counts);
    });
    return () => {
      alive = false;
    };
  }, [canTg]);

  const chooseTab = (t: View) => {
    setView(t);
    if (t !== "telegram") setTab(t);
    setOpenId(null);
    writePref(K_TAB, t);
  };
  const reload = () => setTick((t) => t + 1);

  const d = res?.status === "ok" ? res.data : null;
  const active: View = tg ? "telegram" : tab;
  // Ishtirok talab qiladiganlari: bog'lanmagan + bir nechta mos
  const tgTodo = tgCounts ? tgCounts.unmatched + tgCounts.ambiguous : null;
  const offBox = (
    <div className={`${box} p-6 text-center`}>
      <p className="text-sm text-slate-600">"So'z bilish" bo'limi hali yoqilmagan.</p>
    </div>
  );

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

      {res?.status === "off" && !canTg ? (
        offBox
      ) : (
        <>
          <div className={`grid ${canTg ? "grid-cols-2 sm:grid-cols-4" : "grid-cols-3"} gap-1 rounded-xl bg-slate-100 p-1 mb-4`}
               role="tablist">
            {TABS.map(([k, label]) => {
              const n = d ? d.counts[k] : null;
              return (
                <button key={k} type="button" role="tab" aria-selected={active === k}
                  onClick={() => chooseTab(k)}
                  className={`min-h-[40px] rounded-lg text-[13px] font-semibold px-1 ${
                    active === k ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}>
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
            {canTg && (
              <button type="button" role="tab" aria-selected={tg}
                onClick={() => chooseTab("telegram")}
                className={`min-h-[40px] rounded-lg text-[13px] font-semibold px-1 ${
                  tg ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}>
                Telegram natijalari
                {tgTodo !== null && tgTodo > 0 && (
                  <span className="ml-1 inline-flex min-w-[20px] justify-center rounded-full px-1.5 text-[11px] bg-sky-500 text-white">
                    {tgTodo}
                  </span>
                )}
              </button>
            )}
          </div>

          {tg ? (
            <TelegramResults onCounts={setTgCounts} />
          ) : res?.status === "off" ? (
            offBox
          ) : (
          <>
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

// ================================================ TELEGRAM NATIJALARI ===
// 2026-10-17. Holat serverda jonli hisoblanadi (fayl + baza): bog'langan,
// yashirilgan, bir nechta mos (bir nechta o'quvchiga), bog'lanmagan.
// Amaldan keyin qator joyida yangilanadi (ro'yxatdan chiqib ketmaydi —
// xodim natijani ko'rib turadi). 2026-10-17 (review): bitta amal boshqa
// qatorlarni ham o'zgartiradi, shuning uchun keyin hamma holat va sonlar
// serverdan qayta olinadi (refresh).

const TG_FILTERS: readonly [TgStatus, string][] = [
  ["unmatched", "Bog'lanmagan"],
  ["ambiguous", "Bir nechta mos"],
  ["linked", "Bog'langan"],
  ["dismissed", "Yashirilgan"],
];
const TG_KEYS = TG_FILTERS.map(([k]) => k);
const K_TG = "jony_vc_tg";
const TG_EMPTY: Record<TgStatus, string> = {
  unmatched: "Bog'lanmagan natija qolmadi.",
  ambiguous: "Bir nechta o'quvchiga mos keladigan natija yo'q.",
  linked: "Hali bog'langan natija yo'q.",
  dismissed: "Yashirilgan natija yo'q.",
};
const searchInput =
  "w-full min-h-[44px] rounded-xl border border-slate-300 bg-white pl-9 pr-3 py-2 text-[15px] text-slate-900";

function TelegramResults({ onCounts }: { onCounts: (c: Record<TgStatus, number>) => void }) {
  const [filter, setFilter] = useState<TgStatus>(() => pickPref(K_TG, TG_KEYS, "unmatched"));
  const [res, setRes] = useState<WbQuiet<TgList> | null>(null);
  // res qaysi filtrniki: filtr almashib yuklanayotganda eski qatorlar va
  // boshqa filtrning "bo'sh" matni ko'rsatilmaydi
  const [resFor, setResFor] = useState<TgStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  // Amaldan keyingi yangilashlar: kech kelgan eski javob yangisini bosmasin
  const refreshSeq = useRef(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getTgResults(filter).then((r) => {
      if (!alive) return;
      setRes(r);
      setResFor(filter);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [filter, tick]);

  // Tepadagi tab belgisi (bog'lanmagan + bir nechta mos) shu sonlardan
  useEffect(() => {
    if (res?.status === "ok") onCounts(res.data.counts);
  }, [res, onCounts]);

  const choose = (k: TgStatus) => {
    setFilter(k);
    writePref(K_TG, k);
  };

  /** Server qaytargan yangi qatorni joyiga qo'yadi va sonlarni tuzatadi. */
  const replaceRow = (next: TgRow) =>
    setRes((cur) => {
      if (!cur || cur.status !== "ok") return cur;
      const prev = cur.data.rows.find((x) => x.row === next.row);
      const counts = { ...cur.data.counts };
      if (prev && prev.status !== next.status) {
        counts[prev.status] = Math.max(0, (counts[prev.status] ?? 0) - 1);
        counts[next.status] = (counts[next.status] ?? 0) + 1;
      }
      return {
        status: "ok",
        data: { rows: cur.data.rows.map((x) => (x.row === next.row ? next : x)), counts },
      };
    });

  /**
   * Amaldan keyin: "Bizniki emas" shu postdagi shu odamning hamma natijasini
   * yashiradi, bog'lash esa shu odamning boshqa postdagi xuddi shu natijasini
   * ham "bog'langan" qiladi. Shuning uchun hamma holat qayta olinadi:
   * ko'rinib turgan kartalar joyida yangilanadi, sonlar — serverdan.
   */
  const refresh = (next?: TgRow) => {
    if (next) replaceRow(next);
    const my = ++refreshSeq.current;
    getTgResults("all").then((r) => {
      if (r.status !== "ok" || my !== refreshSeq.current) return;
      const fresh = new Map(r.data.rows.map((x) => [x.row, x] as const));
      setRes((cur) =>
        !cur || cur.status !== "ok"
          ? cur
          : {
              status: "ok",
              data: { rows: cur.data.rows.map((x) => fresh.get(x.row) ?? x), counts: r.data.counts },
            },
      );
    });
  };

  const d = res?.status === "ok" ? res.data : null;
  const stale = resFor !== filter;

  return (
    <div>
      <p className="flex items-start gap-1.5 text-[13px] text-slate-600 mb-3">
        <Send size={14} className="mt-0.5 shrink-0 text-sky-500" />
        Kanal postlaridan olingan natijalar. Bog'lash — darhol tasdiqlangan sertifikat bo'ladi.
      </p>

      <div className="flex flex-wrap gap-2 mb-4" role="tablist" aria-label="Holat">
        {TG_FILTERS.map(([k, label]) => {
          const on = filter === k;
          const n = d ? d.counts[k] ?? 0 : null;
          return (
            <button key={k} type="button" role="tab" aria-selected={on} onClick={() => choose(k)}
              className={`min-h-[40px] rounded-full border px-3 text-[13px] font-semibold inline-flex items-center gap-1.5 ${
                on ? "border-brand-600 bg-brand-600 text-white" : "border-slate-200 bg-white text-slate-700"}`}>
              {label}
              {n !== null && (
                <span className={`inline-flex min-w-[20px] justify-center rounded-full px-1.5 text-[11px] ${
                  on ? "bg-white/25 text-white" : "bg-slate-100 text-slate-600"}`}>
                  {n}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {res?.status === "off" && (
        <div className={`${box} p-6 text-center text-sm text-slate-600`}>
          Telegram natijalari hali serverda yo'q.
        </div>
      )}
      {res?.status === "error" && (
        <div className={`${box} p-4 text-sm text-red-600`}>
          {res.message}{" "}
          <button type="button" onClick={() => setTick((t) => t + 1)} className="underline font-semibold">
            Qayta urinish
          </button>
        </div>
      )}
      {(!res || (d && stale)) && <p className="text-sm text-slate-400">Yuklanmoqda…</p>}

      {d && !stale && (
        <div className={`space-y-3 ${loading ? "opacity-60" : ""}`}>
          {d.rows.length === 0 && (
            <div className={`${box} p-6 text-center text-sm text-slate-500`}>{TG_EMPTY[filter]}</div>
          )}
          {d.rows.map((r) => (
            <TgCard key={r.row} r={r} onChanged={refresh} />
          ))}
        </div>
      )}
    </div>
  );
}

function TgPill({ s }: { s: TgStatus }) {
  const base = "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap";
  switch (s) {
    case "linked":
      return <span className={`${base} bg-emerald-100 text-emerald-700`}><BadgeCheck size={12} /> Bog'langan</span>;
    case "ambiguous":
      return <span className={`${base} bg-violet-100 text-violet-700`}>Bir nechta mos</span>;
    case "dismissed":
      return <span className={`${base} bg-slate-200 text-slate-700`}>Yashirilgan</span>;
    default:
      return <span className={`${base} bg-amber-100 text-amber-800`}>Bog'lanmagan</span>;
  }
}

type TgPick = { id: number; name: string; meta: string | null };

function TgCard({ r, onChanged }: { r: TgRow; onChanged: (next?: TgRow) => void }) {
  const [pick, setPick] = useState<TgPick | null>(null);
  const [busy, setBusy] = useState<"" | "link" | "dismiss">("");
  const [err, setErr] = useState("");
  // 409 TG_DUP: tanlangan o'quvchida shu natija allaqachon bor — xodim
  // tasdiqlasa, yangi sertifikatsiz "bog'langan" deb yoziladi
  const [dup, setDup] = useState(false);
  const open = r.status === "unmatched" || r.status === "ambiguous";
  // Havola serverdan keladi; baribir faqat Telegram manzili ochiladi
  const safeLink = /^https:\/\/t\.me\//.test(r.link) ? r.link : null;

  const choose = (p: TgPick) => {
    setErr("");
    setDup(false);
    setPick((cur) => (cur?.id === p.id ? null : p));
  };

  async function link(existing = false) {
    if (busy || !pick) return;
    setErr("");
    setBusy("link");
    try {
      const next = await linkTgResult(r.row, pick.id, existing);
      const who = next.student_name || pick.name;
      pushToast(
        existing ? `Bog'langan deb belgilandi: ${who}` : `Bog'landi: ${who} — ${next.label || r.label}`,
        "success", 3000);
      setPick(null);
      setDup(false);
      onChanged(next);
    } catch (e) {
      const code = e instanceof ApiError ? e.status : 0;
      const msg = e instanceof Error ? e.message : "Bog'lab bo'lmadi";
      if (code === 409 && msg === TG_DUP && !existing) {
        setDup(true);
      } else {
        setErr(msg);
        // Boshqa o'quvchiga bog'langan (ikkinchi xodim / eski ro'yxat) —
        // karta haqiqiy egasini ko'rsatsin
        if (code === 409) onChanged();
      }
    } finally {
      setBusy("");
    }
  }

  async function dismiss(undo: boolean) {
    if (busy) return;
    setErr("");
    setBusy("dismiss");
    try {
      const next = await dismissTgResult(r.row, undo);
      pushToast(undo ? "Qaytarildi" : "Yashirildi", "success", 2500);
      setPick(null);
      setDup(false);
      onChanged(next);
    } catch (e) {
      setErr(e instanceof Error ? e.message : undo ? "Qaytarib bo'lmadi" : "Yashirib bo'lmadi");
      // 409 — natija shu orada bog'langan: haqiqiy holat ko'rinsin
      if (e instanceof ApiError && e.status === 409) onChanged();
    } finally {
      setBusy("");
    }
  }

  return (
    <div className={`${box} p-4`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-[15px] font-semibold text-slate-900 break-words">{r.name}</p>
          <p className="text-[14px] text-slate-800 mt-0.5">
            <b>{r.label}</b>
            <span className="text-slate-500"> · {formatDate(r.date)}</span>
          </p>
          {safeLink && (
            <a href={safeLink} target="_blank" rel="noopener noreferrer"
              className="mt-0.5 inline-flex items-center gap-1 min-h-[36px] text-[13px] font-semibold text-brand-600">
              <ExternalLink size={14} /> Postni ochish
            </a>
          )}
        </div>
        <div className="shrink-0">
          <TgPill s={r.status} />
        </div>
      </div>

      {r.status === "linked" && (
        <p className="mt-1 flex items-start gap-1.5 text-[13px] text-slate-700">
          <BadgeCheck size={15} className="mt-0.5 shrink-0 text-emerald-600" />
          <span className="min-w-0 break-words">
            O'quvchi: <b>{r.student_name || (r.student_id ? `#${r.student_id}` : "boshqa filial o'quvchisi")}</b>
          </span>
        </p>
      )}

      {open && (
        <div className="mt-3 space-y-3">
          {r.candidates.length > 0 && (
            <div>
              <p className="text-[12px] font-semibold text-slate-600 mb-1">
                {r.status === "ambiguous"
                  ? "Bir nechta o'quvchiga mos — to'g'risini tanlang"
                  : "Ismi yaqin o'quvchilar"}
              </p>
              <div className="flex flex-wrap gap-2">
                {r.candidates.map((c) => {
                  const sel = pick?.id === c.id;
                  // #id — bir filialda bir xil ismli ikki o'quvchi farqlansin
                  const meta = [c.branch, `#${c.id}`].filter(Boolean).join(" · ");
                  return (
                    <button key={c.id} type="button" aria-pressed={sel} disabled={!!busy}
                      onClick={() => choose({ id: c.id, name: c.name, meta })}
                      className={`min-h-[44px] max-w-full rounded-xl border px-3 py-1.5 text-left text-[13px] ${
                        sel ? "border-emerald-500 bg-emerald-50 text-emerald-800" : "border-slate-300 bg-white text-slate-800"}`}>
                      <span className="block font-semibold break-words">{c.name}</span>
                      <span className="block text-[11px] text-slate-500">{meta}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <StudentSearch idPrefix={`tg${r.row}`} disabled={!!busy}
            onPick={(h) => choose({
              id: h.id,
              name: h.name,
              meta: [h.group || "guruhsiz", h.status_label, `#${h.id}`].filter(Boolean).join(" · "),
            })} />

          {pick && (
            <div className="flex items-start gap-2 rounded-xl bg-emerald-50 border border-emerald-200 px-3 py-2 text-[13px] text-emerald-900">
              <span className="flex-1 min-w-0 break-words">
                Tanlandi: <b>{pick.name}</b>
                {pick.meta && <span className="text-emerald-700"> · {pick.meta}</span>}
              </span>
              <button type="button" onClick={() => { setPick(null); setDup(false); }} disabled={!!busy}
                aria-label="Tanlovni bekor qilish" className="shrink-0 -m-1 p-1 text-emerald-700">
                <X size={16} />
              </button>
            </div>
          )}

          {pick && dup && (
            <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-3 space-y-2">
              <p className="text-[13px] text-slate-800 leading-snug">
                Tanlangan o'quvchida bu natija allaqachon bor (boshqa postdan yoki CRM'ga
                kiritilgan). Shu natija uniki bo'lsa — yangi sertifikat yaratilmaydi,
                natija unga bog'langan deb belgilanadi.
              </p>
              <button type="button" onClick={() => link(true)} disabled={!!busy}
                className="w-full min-h-[44px] rounded-xl bg-amber-600 text-white text-sm font-semibold inline-flex items-center justify-center gap-1.5 disabled:opacity-50">
                <BadgeCheck size={16} /> {busy === "link" ? "…" : "Ha, uniki — belgilash"}
              </button>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => link()} disabled={!!busy || !pick}
              className="flex-1 min-w-[140px] min-h-[44px] rounded-xl bg-emerald-600 text-white text-sm font-semibold inline-flex items-center justify-center gap-1.5 disabled:opacity-50">
              <Link2 size={16} /> {busy === "link" ? "…" : "Bog'lash"}
            </button>
            <button type="button" onClick={() => dismiss(false)} disabled={!!busy}
              className="flex-1 min-w-[140px] min-h-[44px] rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold inline-flex items-center justify-center gap-1.5 disabled:opacity-50">
              <EyeOff size={16} /> {busy === "dismiss" ? "…" : "Bizniki emas"}
            </button>
          </div>
        </div>
      )}

      {r.status === "dismissed" && (
        <button type="button" onClick={() => dismiss(true)} disabled={!!busy}
          className="mt-3 min-h-[44px] px-4 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold inline-flex items-center gap-1.5 disabled:opacity-50">
          <RotateCcw size={15} /> {busy ? "…" : "Qaytarish"}
        </button>
      )}

      {err && <p role="alert" className="mt-2 text-[13px] text-red-600">{err}</p>}
    </div>
  );
}

/**
 * O'quvchi qidiruvi — panel tepasidagi global qidiruv bilan bir xil yo'l
 * (/api/search/students, 3 harfdan, 300 ms kutib). Eski javob kech kelsa
 * e'tiborsiz qoladi. Filial doirasi serverda.
 */
function StudentSearch({
  idPrefix,
  disabled,
  onPick,
}: {
  idPrefix: string;
  disabled: boolean;
  onPick: (h: StaffStudentHit) => void;
}) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<StaffStudentHit[] | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    const t = q.trim();
    if (t.length < 3) {
      setHits(null);
      setSearching(false);
      return;
    }
    let alive = true;
    setSearching(true);
    const timer = setTimeout(() => {
      searchStaffStudents(t)
        .then((r) => {
          if (alive) setHits(r);
        })
        .catch(() => {
          if (alive) setHits([]);
        })
        .finally(() => {
          if (alive) setSearching(false);
        });
    }, 300);
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [q]);

  const branchOnly = !!getGlobalBranch();

  return (
    <div>
      <label htmlFor={`${idPrefix}-q`} className="block text-[12px] font-semibold text-slate-600 mb-1">
        O'quvchini qidirish
      </label>
      <div className="relative">
        <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input id={`${idPrefix}-q`} value={q} disabled={disabled} autoComplete="off"
          enterKeyHint="search" maxLength={60}
          placeholder="Ism, telefon yoki ID (kamida 3 harf)"
          onChange={(e) => setQ(e.target.value)} className={searchInput} />
      </div>
      {branchOnly && (
        <p className="mt-1 text-[11.5px] text-slate-400">Qidiruv tepada tanlangan filial ichida.</p>
      )}
      {searching && <p className="mt-1 text-[12px] text-slate-400">Qidirilmoqda…</p>}
      {!searching && hits && hits.length === 0 && (
        <p className="mt-1 text-[12px] text-slate-500">Hech kim topilmadi.</p>
      )}
      {!searching && hits && hits.length > 0 && (
        <ul className="mt-1.5 rounded-xl border border-slate-200 divide-y divide-slate-100 overflow-hidden">
          {hits.map((h) => (
            <li key={h.id}>
              <button type="button" disabled={disabled}
                onClick={() => {
                  onPick(h);
                  setQ("");
                  setHits(null);
                }}
                className="w-full min-h-[44px] text-left px-3 py-2 hover:bg-slate-50">
                <span className="block text-[14px] text-slate-800 break-words">{h.name}</span>
                <span className="block text-[12px] text-slate-500">
                  {h.group || "guruhsiz"}
                  {h.status_label ? ` · ${h.status_label}` : ""}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
