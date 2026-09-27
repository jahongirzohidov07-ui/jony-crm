import type { NavItem } from "../../components/navItems";

/**
 * JonyOS xodim ilovasi — yo'nalishlar va rolga qarab pastki menyu
 * (2026-09-27).
 *
 * QAYSI BO'LIM KIMGA OCHIQ — bu yerda HAL QILINMAYDI. Ro'yxat
 * components/navItems.ts dagi buildNav() dan keladi (xodimlar paneli
 * bilan AYNAN bir xil). Bu fayl faqat: har bandga ikonka, ilova ichidagi
 * manzil va pastki menyuning tartibi.
 */

/** Panel manzili → gem ikonka. */
export const ROUTE_GEM: Record<string, string> = {
  "/": "home",
  "/timetable": "cal",
  "/support-schedule": "clock",
  "/leads": "target",
  "/students": "users",
  "/groups": "stack",
  "/teachers": "teacher",
  "/gamification": "trophy",
  "/my-career": "rocket",
  "/my-coins": "coin",
  "/finance": "wallet",
  "/reports": "chart",
  "/analytics": "pie",
  "/library": "book",
  "/advisor": "spark",
  "/academic": "cap",
  "/learning": "trend",
  "/plans": "notebook",
  "/exam": "exam",
  "/mock-practice": "spark",
  "/smm": "insta",
  "/marketing": "mega",
  "/users": "usergear",
  "/hr": "brief",
  "/namunali": "medal",
  "/complaints": "warn",
  "/audit": "shield",
  "/inventory": "box",
  "/archive": "archive",
  "/mashq": "timer",
  "/events": "party",
  "/settings": "gear",
  "/development": "film",
  "/my-groups": "stack",
  "/my-students": "cap",
  "/my-schedule": "cal",
  "/my-books": "book",
  "/my-exams": "exam",
  "/my-finance": "wallet",
  "/my-results": "pie",
  "/my-sessions": "clock",
  "/tasks": "task",
};

export function gemFor(to: string): string {
  return ROUTE_GEM[to] || "grid";
}

/** Ilovadan TASHQARIDA ochiladigan manzillar (o'z qobig'i bor). */
const OWN_SHELL = new Set(["/student", "/parent", "/t", "/live",
  "/teacher-run", "/play", "/apply", "/ariza", "/r", "/login", "/app", "/api"]);

/** Panel manzilini ilova ichidagi manzilga aylantiradi:
 *  "/students/5" → "/app/p/students/5", "/" → "/app". */
export function appHref(to: string): string {
  if (!to.startsWith("/") || to.startsWith("//")) return to;
  const first = "/" + to.slice(1).split(/[/?#]/)[0];
  if (OWN_SHELL.has(first)) return to;
  // Sobiq Jony Teacher — endi ilova ichida (2026-09-27)
  if (first === "/teacher") {
    const rest = to.slice("/teacher".length);
    if (rest.startsWith("/more")) return "/app/menu";
    if (rest.startsWith("/profile")) return "/app/profile";
    return "/app/t" + rest;
  }
  if (first === "/") return "/app" + to.slice(1);
  // Vazifalar — ilovaning o'z (telefon uchun qurilgan) sahifasi
  if (to === "/tasks") return "/app/tasks";
  return "/app/p" + to;
}

/** Ilova ichida ochilsa bo'ladigan panel manzilimi (havolani ushlash uchun). */
export function isPanelPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//") && appHref(path) !== path;
}

/** Ustoz ishi (yo'qlama, jadval, soat) ilovasi bor lavozimlar. */
export const TEACHER_ROLES = ["teacher", "support_teacher"];

export interface AppTab {
  to: string;
  label: string;
  gem: string;
  end?: boolean;
}

/** Rolning asosiy ishi — o'rtadagi katta tugma. */
const FAB_BY_ROLE: Record<string, { to: string; label: string; gem: string }> = {
  founder: { to: "/finance", label: "Moliya", gem: "wallet" },
  branch_manager: { to: "/finance", label: "Moliya", gem: "wallet" },
  finance_director: { to: "/finance", label: "Moliya", gem: "wallet" },
  accountant: { to: "/finance", label: "Moliya", gem: "wallet" },
  sales_head: { to: "/leads", label: "Lidlar", gem: "target" },
  sales_manager: { to: "/leads", label: "Lidlar", gem: "target" },
  administrator: { to: "/leads", label: "Lidlar", gem: "target" },
  smm_manager: { to: "/smm", label: "SMM", gem: "insta" },
  academic_head: { to: "/academic", label: "O'quv", gem: "cap" },
  teacher: { to: "/plans", label: "Rejalar", gem: "notebook" },
  support_teacher: { to: "/teacher/session", label: "Soat", gem: "timer" },
  head_support: { to: "/support-schedule", label: "Yuklama", gem: "clock" },
  examiner: { to: "/exam", label: "Imtihon", gem: "exam" },
  head_examiner: { to: "/exam", label: "Imtihon", gem: "exam" },
  hr_manager: { to: "/hr", label: "HR", gem: "brief" },
  facility_manager: { to: "/inventory", label: "Ombor", gem: "box" },
  event_manager: { to: "/events", label: "Tadbirlar", gem: "party" },
};

/**
 * Pastki menyu: [Bosh sahifa] [ikkinchi] (O'RTA TUGMA) [Vazifalar] [Bo'limlar].
 * O'rta tugma va ikkinchi tab faqat shu xodimga OCHIQ bo'lim bo'lsa
 * chiqadi — aks holda ro'yxatdagi keyingi ochiq bo'lim olinadi.
 */
export function buildTabs(role: string, nav: NavItem[], hasTasks: boolean): {
  tabs: AppTab[];
  fab: AppTab | null;
} {
  const allowed = new Set(nav.map((i) => i.to));
  const f = FAB_BY_ROLE[role];
  let fab: AppTab | null = null;
  if (f && ((f.to.startsWith("/teacher") && TEACHER_ROLES.includes(role)) || allowed.has(f.to))) {
    fab = { to: appHref(f.to), label: f.label, gem: f.gem };
  }
  // USTOZ va SUPPORT: kuni darsdan boshlanadi (sobiq Jony Teacher tartibi)
  if (TEACHER_ROLES.includes(role)) {
    const tabs: AppTab[] = [
      { to: "/app/t", label: "Bugun", gem: "home", end: true },
      { to: "/app/t/week", label: "Jadval", gem: "cal" },
      hasTasks
        ? { to: "/app/tasks", label: "Vazifalar", gem: "task" }
        : { to: "/app/profile", label: "Profil", gem: "user" },
      { to: "/app/menu", label: "Bo'limlar", gem: "grid" },
    ];
    return { tabs, fab };
  }
  const second = ["/timetable", "/my-schedule", "/leads", "/students",
    "/events", "/hr", "/exam", "/inventory", "/smm"]
    .find((to) => allowed.has(to) && appHref(to) !== fab?.to)
    ?? nav.find((i) => i.to !== "/" && appHref(i.to) !== fab?.to)?.to;
  const tabs: AppTab[] = [{ to: "/app", label: "Asosiy", gem: "home", end: true }];
  if (second) {
    const item = nav.find((i) => i.to === second);
    tabs.push({ to: appHref(second), label: shortLabel(item?.label || ""), gem: gemFor(second) });
  }
  tabs.push(hasTasks
    ? { to: "/app/tasks", label: "Vazifalar", gem: "task" }
    : { to: "/app/profile", label: "Profil", gem: "user" });
  tabs.push({ to: "/app/menu", label: "Bo'limlar", gem: "grid" });
  return { tabs, fab };
}

/** Pastki menyuga sig'adigan qisqa nom. */
export function shortLabel(label: string): string {
  const map: Record<string, string> = {
    "Dars jadvali": "Jadval",
    "Dars jadvalim": "Jadval",
    "Darslarim": "Darslar",
    "Talabalar": "O'quvchilar",
    "Imtihonlar": "Imtihon",
    "Shaxsiy rivojlanish": "Rivojlanish",
  };
  return map[label] || (label.length > 10 ? label.slice(0, 9) + "…" : label);
}
