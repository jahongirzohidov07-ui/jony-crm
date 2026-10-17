import { useCallback, useEffect, useState } from "react";
import { BadgeCheck, Check, Eye, EyeOff, FileUp, Hourglass, RotateCcw, Undo2, X } from "lucide-react";
import { formatDate } from "../../lib/format";
import {
  getMyCerts,
  invalidateWordbank,
  withdrawMyCert,
  type CertExamType,
  type MyCert,
  type MyCerts,
  type WbQuiet,
} from "../../lib/wordbankApi";
import { CertFilePreview } from "./CertFilePreview";
import { CertUploadSheet } from "./CertUploadSheet";

/**
 * "SERTIFIKATLARIM" — profildagi karta (2026-10-17, OWNER D3).
 *
 * Holatlar (ko'rinish qoidasi QAT'IY):
 *   * kutilmoqda — "Yuklandi — tekshirilmoqda", BALL YO'Q (server ham
 *     bermaydi), "Qaytarib olish" mumkin;
 *   * tasdiqlangan — natija + ✓ "tasdiqlangan";
 *   * rad etilgan — "Rad etildi: {sabab}" + "Qayta yuklash";
 *   * bekor qilingan — "Bekor qilindi".
 * Natija faqat result_label dan olinadi va u faqat tasdiqlanganda
 * keladi — boshqa holatda ekranga hech qanday ball chiqmaydi.
 */
export function CertUploadCard({
  onChange,
  bare = false,
}: {
  onChange?: () => void;
  /** true — alohida karta sifatida (tepada chiziq yo'q) */
  bare?: boolean;
}) {
  const [res, setRes] = useState<WbQuiet<MyCerts> | null>(null);
  const [tick, setTick] = useState(0);
  const [sheet, setSheet] = useState<{ type?: CertExamType } | null>(null);
  const [done, setDone] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [askId, setAskId] = useState<number | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    getMyCerts().then((r) => {
      if (alive) setRes(r);
    });
    return () => {
      alive = false;
    };
  }, [tick]);

  const reload = useCallback(() => {
    invalidateWordbank();
    setTick((t) => t + 1);
    onChange?.();
  }, [onChange]);

  async function withdraw(id: number) {
    if (busyId) return;
    setBusyId(id);
    setErr("");
    try {
      await withdrawMyCert(id);
      setAskId(null);
      setDone(false);
      if (openId === id) setOpenId(null);
      reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Qaytarib olib bo'lmadi");
    } finally {
      setBusyId(null);
    }
  }

  // Bo'lim yopiq — karta umuman chiqmaydi
  if (res?.status === "off") return null;

  const items = res?.status === "ok" ? res.data.items : [];
  const lim = res?.status === "ok" ? res.data.limits : null;
  const blocked = lim
    ? lim.pending >= lim.max_pending
      ? `Tekshirilayotgan sertifikatlar ${lim.max_pending} tadan oshmasin — avvalgilari tekshirilsin.`
      : lim.used_30d >= lim.max_30d
        ? `30 kunda ${lim.max_30d} tadan ko'p yuklab bo'lmaydi.`
        : ""
    : "";

  return (
    <div className={bare ? "" : "mt-4 pt-4 border-t border-slate-100"}>
      <p className={`${bare ? "text-[20px]" : "text-[15px]"} font-extrabold text-slate-900`}>Sertifikatlarim</p>
      <p className="text-[12px] text-slate-600 mt-1 leading-relaxed">
        IELTS, CEFR/Multilevel, SAT, Duolingo yoki boshqa natijangiz bormi?
        Sertifikatni yuklang — tasdiqlangach so'zlaringiz soni yonida ✓ belgi
        bilan chiqadi va reytingda ko'rinadi.
      </p>

      {done && (
        <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 px-3 py-2 flex items-start gap-2">
          <Check size={16} className="text-emerald-600 mt-0.5 shrink-0" />
          <p className="text-[12.5px] text-emerald-800 flex-1 leading-snug">
            <b>Yuklandi — tekshirilmoqda.</b> Natija tekshirilgandan keyin shu
            yerda chiqadi.
          </p>
          <button type="button" onClick={() => setDone(false)} aria-label="Yopish"
                  className="text-emerald-600 shrink-0 w-7 h-7 flex items-center justify-center">
            <X size={14} />
          </button>
        </div>
      )}

      {res === null && <p className="text-[12px] text-slate-400 mt-3">Yuklanmoqda…</p>}
      {res?.status === "error" && (
        <p className="text-[12px] text-red-600 mt-3">
          {res.message}{" "}
          <button type="button" className="underline font-semibold" onClick={() => setTick((t) => t + 1)}>
            Qayta urinish
          </button>
        </p>
      )}

      {items.length > 0 && (
        <ul className="mt-3 space-y-2">
          {items.map((c) => (
            <CertRow
              key={c.id}
              c={c}
              busy={busyId === c.id}
              asking={askId === c.id}
              open={openId === c.id}
              onAsk={() => setAskId(askId === c.id ? null : c.id)}
              onWithdraw={() => withdraw(c.id)}
              onReupload={() => {
                setDone(false);
                setSheet({ type: c.exam_type });
              }}
              onToggle={() => setOpenId(openId === c.id ? null : c.id)}
            />
          ))}
        </ul>
      )}

      {err && <p role="alert" className="text-[12px] text-red-600 mt-2">{err}</p>}

      <button
        type="button"
        disabled={!!blocked || res?.status !== "ok"}
        onClick={() => {
          setDone(false);
          setSheet({});
        }}
        className="mt-3 w-full min-h-[48px] rounded-2xl bg-brand-600 text-white text-[14px] font-bold inline-flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <FileUp size={17} /> Sertifikat yuklash
      </button>
      {blocked && <p className="text-[11.5px] text-slate-500 mt-1.5">{blocked}</p>}

      {sheet && (
        <CertUploadSheet
          initialType={sheet.type}
          onClose={() => setSheet(null)}
          onDone={() => {
            setSheet(null);
            setDone(true);
            reload();
          }}
        />
      )}
    </div>
  );
}

function CertRow({
  c,
  busy,
  asking,
  open,
  onAsk,
  onWithdraw,
  onReupload,
  onToggle,
}: {
  c: MyCert;
  busy: boolean;
  asking: boolean;
  open: boolean;
  onAsk: () => void;
  onWithdraw: () => void;
  onReupload: () => void;
  onToggle: () => void;
}) {
  const confirmed = c.status === "confirmed";
  const btn = "inline-flex items-center gap-1 min-h-[36px] text-[12px] font-bold";

  return (
    <li className="rounded-2xl border border-slate-200 bg-slate-50/60 p-3">
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          {/* Natija FAQAT tasdiqlanganda — aks holda imtihon nomi xolos */}
          <p className="text-[15px] font-extrabold text-slate-900 break-words">
            {confirmed && c.result_label ? c.result_label : c.exam_label}
          </p>
          <p className="text-[11.5px] text-slate-500 mt-0.5">
            {c.test_date ? `Test: ${formatDate(c.test_date)} · ` : ""}
            Yuklangan: {formatDate(c.created_at)}
          </p>
        </div>
        <StatusChip c={c} />
      </div>

      {c.status === "rejected" && (
        <p className="text-[12.5px] text-red-700 mt-2 leading-snug">
          Rad etildi: <b>{c.reject_reason || "sabab ko'rsatilmagan"}</b>
          {c.reject_note ? ` — ${c.reject_note}` : ""}
        </p>
      )}
      {c.status === "pending" && (
        <p className="text-[12px] text-slate-500 mt-2 leading-snug">
          <b className="text-slate-700">Yuklandi — tekshirilmoqda.</b> Natija
          ustoz yoki rahbariyat tasdiqlagandan keyin chiqadi.
        </p>
      )}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1">
        <button type="button" onClick={onToggle} className={`${btn} text-brand-600`}>
          {open ? <EyeOff size={14} /> : <Eye size={14} />}
          {open ? "Yopish" : "Faylni ko'rish"}
        </button>
        {c.can_withdraw && !asking && (
          <button type="button" onClick={onAsk} className={`${btn} text-slate-600`}>
            <Undo2 size={14} /> Qaytarib olish
          </button>
        )}
        {c.can_reupload && (
          <button type="button" onClick={onReupload} className={`${btn} text-brand-600`}>
            <RotateCcw size={14} /> Qayta yuklash
          </button>
        )}
      </div>

      {asking && (
        <div className="mt-2 rounded-xl bg-white border border-slate-200 p-2.5">
          <p className="text-[12.5px] text-slate-700">Bu yuklama tekshiruvdan qaytarib olinsinmi?</p>
          <div className="flex gap-2 mt-2">
            <button type="button" disabled={busy} onClick={onWithdraw}
                    className="flex-1 min-h-[40px] rounded-xl bg-red-600 text-white text-[13px] font-bold disabled:opacity-60">
              {busy ? "…" : "Ha, qaytarib olish"}
            </button>
            <button type="button" disabled={busy} onClick={onAsk}
                    className="flex-1 min-h-[40px] rounded-xl border border-slate-300 text-slate-700 text-[13px] font-bold">
              Yo'q
            </button>
          </div>
        </div>
      )}

      {open && (
        <div className="mt-2">
          <CertFilePreview path={`/wordbank/certs/mine/${c.id}/file`} mime={c.mime}
                           name={`sertifikat-${c.id}`} />
        </div>
      )}
    </li>
  );
}

function StatusChip({ c }: { c: MyCert }) {
  const base = "inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-bold shrink-0 whitespace-nowrap";
  if (c.status === "confirmed")
    return (
      <span className={`${base} bg-emerald-100 text-emerald-700`}>
        <BadgeCheck size={13} /> tasdiqlangan
      </span>
    );
  if (c.status === "pending")
    return (
      <span className={`${base} bg-amber-100 text-amber-800`}>
        <Hourglass size={12} /> tekshirilmoqda
      </span>
    );
  if (c.status === "rejected")
    return <span className={`${base} bg-red-100 text-red-700`}>Rad etildi</span>;
  return <span className={`${base} bg-slate-200 text-slate-600`}>{c.status_label || "Bekor qilindi"}</span>;
}
