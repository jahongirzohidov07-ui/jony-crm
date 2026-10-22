/** to_top10 is the displayed XP difference to tenth place, not membership
 * or a guaranteed entry/reward threshold (ties are possible).
 */
export function leaderboardStanding(rank: number | null | undefined, toTop10: number | null | undefined) {
  const ranked = typeof rank === "number" && Number.isInteger(rank) && rank >= 1;
  const top10 = ranked && rank <= 10;
  const gap = !top10 && typeof toTop10 === "number" && Number.isFinite(toTop10) && toTop10 > 0
    ? toTop10 : null;
  const message = top10
    ? "Siz eng yaxshi 10 talikdasiz"
    : !ranked
      ? "Hali reytingda emassiz. Mashq qilib XP to'plang."
      : toTop10 === 0
        ? "10-o'rin bilan XP teng. Oldinga o'tish uchun yana XP to'plang."
        : gap !== null
          ? "10-o'rindagi o'quvchiga yetish uchun"
          : "Top 10 sari mashq qilib XP to'plang.";
  return { rank: ranked ? rank : null, top10, gap, message,
    action: ranked ? "Mashq qilish" : "Mashqni boshlash" };
}
