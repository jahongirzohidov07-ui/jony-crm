import type { RewardItem } from "./api";

export function rewardGoalKey(studentId: number): string {
  return `jony:reward-goal:v1:${studentId}`;
}
export function readRewardGoal(storage: Pick<Storage, "getItem">, studentId: number): number | null {
  try {
    const raw = storage.getItem(rewardGoalKey(studentId));
    if (!raw || !/^\d+$/.test(raw)) return null;
    const id = Number(raw);
    return Number.isSafeInteger(id) && id > 0 ? id : null;
  } catch { return null; }
}
export function writeRewardGoal(storage: Pick<Storage, "setItem">, studentId: number, id: number): boolean {
  if (!Number.isSafeInteger(id) || id <= 0) return false;
  try { storage.setItem(rewardGoalKey(studentId), String(id)); return true; } catch { return false; }
}
export function resolveRewardGoal(rewards: RewardItem[], selectedId: number | null, available: number) {
  const active = rewards.filter(r => r.active);
  const selected = active.find(r => r.id === selectedId);
  const stocked = active.filter(r => r.in_stock).sort((a,b) => a.cost - b.cost || a.id - b.id);
  const reward = selected ?? stocked.find(r => r.cost > available) ?? stocked[0] ?? null;
  const balance = Math.max(0, Number.isFinite(available) ? available : 0);
  return {
    reward,
    unavailableSelection: selectedId !== null && !selected,
    left: reward ? Math.max(0, reward.cost - balance) : 0,
    percent: reward ? (reward.cost > 0 ? Math.max(0, Math.min(100, Math.floor(balance / reward.cost * 100))) : 100) : 0,
  };
}
