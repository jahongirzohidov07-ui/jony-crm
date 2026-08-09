import { useOutletContext } from "react-router-dom";
import { Trophy } from "lucide-react";
import { ParentPageHeader } from "../components/ParentPageHeader";
import type { ParentCtx } from "./Parent";

/**
 * OTA-ONA — GURUHDAGI O'RIN / REYTING (yangi, alohida sahifa,
 * 2026-08-09). Boshqa o'quvchilarning ismini KO'RSATMAYDI — faqat
 * farzandning o'z o'rni (maxfiylik uchun ataylab shunday: bu sahifa
 * loginsiz, havola orqali ochiladi, boshqa oilalarning ma'lumotini
 * fosh qilmaslik kerak). Hisob-kitob mavjud _student_ranks() dan
 * (xodim panelidagi XpCard bilan bir xil, faqat ism ro'yxatisiz).
 */
export default function ParentRank() {
  const { d } = useOutletContext<ParentCtx>();
  const ranks = d.ranks || {};
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

        <p className="text-[11px] text-slate-400 text-center px-6">
          Reyting umumiy yig'ilgan XP (mehnat ballari) asosida
          hisoblanadi. Maxfiylik uchun boshqa o'quvchilarning
          ma'lumoti ko'rsatilmaydi.
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
