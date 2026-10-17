import { useOutletContext } from "react-router-dom";
import { BadgeCheck, BookA, Trophy } from "lucide-react";
import { ParentPageHeader } from "../components/ParentPageHeader";
import type { ParentWordbank } from "../lib/wordbankApi";
import type { ParentCtx } from "./Parent";

/**
 * OTA-ONA — GURUHDAGI O'RIN / REYTING (yangi, alohida sahifa,
 * 2026-08-09). Boshqa o'quvchilarning ismini KO'RSATMAYDI — faqat
 * farzandning o'z o'rni (maxfiylik uchun ataylab shunday: bu sahifa
 * loginsiz, havola orqali ochiladi, boshqa oilalarning ma'lumotini
 * fosh qilmaslik kerak). Hisob-kitob mavjud _student_ranks() dan
 * (xodim panelidagi XpCard bilan bir xil, faqat ism ro'yxatisiz).
 *
 * 2026-10-17 (OWNER D2/D3): "So'z bilish" kartasi — farzandning
 * tasdiqlangan so'zlari, guruh/filialdagi o'rni va FAQAT tasdiqlangan
 * sertifikatlari. Bo'lim filialda yopiq bo'lsa server null beradi —
 * karta chiqmaydi. Boshqa o'quvchilar haqida hech narsa yo'q.
 */
export default function ParentRank() {
  const { d, fmt } = useOutletContext<ParentCtx>();
  const ranks = d.ranks || {};
  const raw = (d.wordbank ?? null) as ParentWordbank;
  // 2026-10-17 (review): so'z mashqi qilmagan bola (masalan koreys / rus
  // tili o'quvchisi) — "0 ta so'z · 0/20" ko'rsatilmaydi; tasdiqlangan
  // sertifikati bo'lsa faqat o'shalar chiqadi, hech narsa bo'lmasa karta yo'q.
  const wbWords = Boolean(raw && (raw.known > 0 || raw.best > 0 || raw.bands_done > 0));
  const wb = raw && (wbWords || (raw.certs || []).length > 0) ? raw : null;
  const hasGroupRank = Boolean(ranks.group_rank);
  const hasBranchRank = Boolean(ranks.branch_rank);

  return (
    <>
      <ParentPageHeader title="Guruhdagi reyting" icon={<Trophy size={18} />} />

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        {!hasGroupRank && !hasBranchRank ? (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
            <Trophy size={28} className="text-slate-300 mx-auto mb-2" />
            <p className="text-sm text-slate-500">
              Hali reyting ma'lumoti yo'q.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Guruh biriktirilgach va XP yig'ila boshlagach, bu yerda
              farzandingizning o'rni ko'rinadi.
            </p>
          </div>
        ) : (
          <>
            {hasGroupRank && (
              <RankCard
                label="Guruhda"
                rank={ranks.group_rank}
                total={ranks.group_total}
              />
            )}
            {hasBranchRank && (
              <RankCard
                label="Filialda"
                rank={ranks.branch_rank}
                total={ranks.branch_total}
              />
            )}
          </>
        )}

        {wb && <WordbankCard wb={wb} fmt={fmt} words={wbWords} />}

        <p className="text-[11px] text-slate-400 text-center px-6">
          Reyting umumiy yig'ilgan XP (mehnat ballari) asosida
          hisoblanadi.{wbWords ? " So'z bilish — tekshirilib tasdiqlangan inglizcha so'zlar soni bo'yicha." : ""}{" "}
          Maxfiylik uchun boshqa o'quvchilarning ma'lumoti ko'rsatilmaydi.
        </p>
      </div>
    </>
  );
}

function RankCard({
  label,
  rank,
  total,
}: {
  label: string;
  rank: number;
  total: number;
}) {
  const top3 = rank <= 3;
  return (
    <div
      className={`rounded-xl p-5 border ${
        top3
          ? "bg-amber-50 border-amber-200"
          : "bg-white border-slate-200 shadow-sm"
      }`}
    >
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <div className="flex items-end gap-2">
        <span
          className={`text-4xl font-bold leading-none ${
            rank === 1
              ? "text-amber-500"
              : top3
              ? "text-amber-600"
              : "text-slate-800"
          }`}
        >
          {rank}
        </span>
        <span className="text-sm text-slate-500 mb-1">/ {total} o'quvchidan</span>
        {top3 && <span className="text-2xl mb-0.5">🏅</span>}
      </div>
    </div>
  );
}

/** So'z bilish: N · guruhda K-o'rin + tasdiqlangan sertifikatlar. */
function WordbankCard({
  wb,
  fmt,
  words,
}: {
  wb: NonNullable<ParentWordbank>;
  fmt: (n: number) => string;
  /** false — so'z mashqi yo'q, faqat tasdiqlangan sertifikatlar */
  words: boolean;
}) {
  const certs = wb.certs || [];
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <p className="text-xs text-slate-500 mb-1 flex items-center gap-1.5">
        <BookA size={14} className="text-brand-600" /> {words ? "So'z bilish" : "Sertifikatlar"}
      </p>
      {words && (
        <>
          <div className="flex items-end gap-2 flex-wrap">
            <span className="text-4xl font-bold leading-none text-slate-800">{fmt(wb.known)}</span>
            <span className="text-sm text-slate-500 mb-1">ta tasdiqlangan so'z</span>
          </div>
          <p className="text-sm text-slate-700 mt-2">
            So'z bilish: <b>{fmt(wb.known)}</b>
            {wb.rank_group ? <> · guruhda <b>{wb.rank_group}-o'rin</b></> : null}
            {wb.rank_branch ? <> · filialda <b>{wb.rank_branch}-o'rin</b></> : null}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Darajalar: {wb.bands_done}/20 tugatildi
            {wb.best > wb.known ? ` · eng yaxshi natija: ${fmt(wb.best)}` : ""}
          </p>
        </>
      )}
      {certs.length > 0 && (
        <div className={`flex flex-wrap gap-1.5 ${words ? "mt-3" : "mt-1"}`}>
          {certs.map((c) => (
            <span key={c.id}
                  className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 px-2.5 py-1 text-xs font-semibold">
              <BadgeCheck size={13} className="text-emerald-600" /> {c.label}
              <span className="text-emerald-600 font-normal">· tasdiqlangan</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
