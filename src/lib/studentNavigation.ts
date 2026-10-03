/** One active tab, including nested exercise and account routes. */
export function studentTabFor(pathname: string): string {
  const section = pathname.split("/")[2] || "";
  if (!section || section === "notifications") return "/student";
  if (["leaderboard", "leagues"].includes(section)) return "/student/leaderboard";
  if (["shop", "badges"].includes(section)) return "/student/shop";
  if (["profile", "settings", "payments", "certificates", "referral", "results"].includes(section)) return "/student/profile";
  return "/student/games";
}
