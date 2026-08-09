import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { BrandIcon } from "../../components/BrandIcon";
import {
  fmtNum, TONE_BAR, type SkillsCard, type StudentHome,
} from "../../lib/studentApi";

/** JONY STUDENT — profil: barcha ko'nikmalar to'liq ro'yxati va
 * hisobdan chiqish. */
export default function StudentProfile() {
  const { user, logout } = useAuth();
  const [h, setH] = useState<StudentHome | null>(null);
  const [sk, setSk] = useState<SkillsCard | null>(null);

  useEffect(() => {
    api.get<StudentHome>("/student/home").then(setH).catch(() => {});
    api.get<SkillsCard>("/student/skills").then(setSk).catch(() => {});
  }, []);

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-12">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center shrink-0">
            <BrandIcon size={34} className="rounded-lg" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-semibold truncate">
              {h?.name || user?.full_name}
            </h1>
            <p className="text-sm opacity-90">
              {h?.group || "guruh biriktirilmagan"}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 space-y-4">
        {sk && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-1">
              Barcha bo'limlar
            </p>
            <p className="text-[11px] text-slate-400 mb-4">
              Har {fmtNum(sk.points_per_level)} ball — keyingi daraja
            </p>
            <div className="space-y-4">
              {sk.skills.map((s) => (
                <div key={s.key}>
                  <div className="flex items-baseline justify-between gap-2 mb-1">
                    <span className="text-sm text-slate-700">{s.label}</span>
                    <span className="text-xs font-medium text-slate-800">
                      {s.level.label}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        TONE_BAR[s.tone] || TONE_BAR.slate
                      }`}
                      style={{
                        width: `${s.next ? s.next.progress_percent : 100}%`,
                      }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {fmtNum(s.points)} ball
                    {s.max_level
                      ? " · eng yuqori daraja 🎉"
                      : ` · ${s.next!.label} gacha yana ${fmtNum(
                          s.next!.points_left,
                        )}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {h && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Hisobim
            </p>
            <Row label="Coin" value={fmtNum(h.gamification.coins)} />
            <Row label="Umumiy XP" value={fmtNum(h.gamification.lifetime_xp)} />
            <Row label="Daraja" value={String(h.gamification.level)} />
            {h.gamification.league && (
              <Row
                label="Liga"
                value={`${h.gamification.league.icon} ${h.gamification.league.name}`}
              />
            )}
            <Row label="Ketma-ket kunlar" value={`${h.streak} kun`} />
            {h.ranks.branch_rank && (
              <Row
                label="Filialdagi o'rin"
                value={`${h.ranks.branch_rank} / ${h.ranks.branch_total}`}
              />
            )}
          </div>
        )}

        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-slate-200 bg-white text-slate-600 text-sm font-medium"
        >
          <LogOut size={16} />
          Chiqish
        </button>
      </div>
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-medium text-slate-800">{value}</span>
    </div>
  );
}
