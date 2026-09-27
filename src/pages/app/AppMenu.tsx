import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../lib/AuthContext";
import { useApp } from "./AppLayout";
import { appHref, gemFor } from "./appNav";
import { Gem, Glyph } from "./Gem";

/** Bo'limlarni mazmuniga qarab guruhlash (faqat ko'rinish uchun —
 *  qaysi band ko'rinishini buildNav hal qiladi). */
const GROUPS: { title: string; paths: string[] }[] = [
  { title: "Kundalik ish", paths: ["/timetable", "/my-schedule", "/support-schedule", "/leads", "/students", "/groups",
    "/my-groups", "/my-students", "/my-sessions", "/teachers", "/events", "/inventory"] },
  { title: "O'quv jarayoni", paths: ["/academic", "/learning", "/plans", "/exam", "/mock-practice", "/my-exams", "/my-books", "/library",
    "/gamification", "/archive", "/complaints"] },
  { title: "Moliya va hisobotlar", paths: ["/finance", "/my-finance", "/reports", "/analytics", "/my-results", "/my-coins"] },
  { title: "Marketing", paths: ["/smm", "/marketing"] },
  { title: "Jamoa va nazorat", paths: ["/users", "/hr", "/namunali", "/audit", "/my-career", "/development", "/mashq",
    "/advisor", "/settings"] },
];

/**
 * BO'LIMLAR — xodimga OCHIQ bo'lgan hamma narsa bir joyda (2026-09-27).
 * Ro'yxat buildNav() dan: panelda ko'rinmaydigan bo'lim bu yerda ham
 * ko'rinmaydi.
 */
export default function AppMenu() {
  const { user } = useAuth();
  const { nav } = useApp();
  const [q, setQ] = useState("");
  const items = nav.filter((i) => i.to !== "/" &&
    (!q.trim() || i.label.toLowerCase().includes(q.trim().toLowerCase())));
  const used = new Set<string>();
  const sections = GROUPS.map((g) => {
    const list = items.filter((i) => g.paths.includes(i.to) && !used.has(i.to));
    list.forEach((i) => used.add(i.to));
    return { title: g.title, list };
  });
  const rest = items.filter((i) => !used.has(i.to));
  if (rest.length) sections.push({ title: "Boshqa", list: rest });
  const isTeacher = user?.role === "teacher";
  const isSupport = user?.role === "support_teacher";
  // Sobiq Jony Teacher bo'limlari (2026-09-27) — faqat ustoz/supportga
  const teacherItems: { to: string; label: string; gem: string }[] = [
    { to: "/app/t", label: "Bugungi darslar", gem: "home" },
    { to: "/app/t/week", label: "Haftalik jadval", gem: "cal" },
    ...(isTeacher ? [{ to: "/app/t/check", label: "Tekshirish", gem: "exam" },
                     { to: "/app/t/vocab", label: "Lug'at unitlari", gem: "book" }] : []),
    ...(isSupport ? [{ to: "/app/t/session", label: "Soat belgilash", gem: "timer" }] : []),
    { to: "/app/t/salary", label: "Darslarim va oyligim", gem: "cash" },
    { to: "/app/t/finance", label: "Oylik tarixi", gem: "wallet" },
  ];
  let n = 0;

  return (
    <div className="jos-page">
      <div className="jos-sect" style={{ marginTop: 6 }}>
        <b style={{ fontSize: 20, fontFamily: "Unbounded, Manrope, sans-serif" }}>Bo'limlar</b>
      </div>
      <div style={{ position: "relative" }}>
        <span style={{ position: "absolute", left: 13, top: 19, color: "#8B89A6" }}><Glyph name="search" size={17} /></span>
        <input className="jos-input" style={{ paddingLeft: 38, background: "#fff", boxShadow: "0 8px 18px -14px #0006" }}
               value={q} onChange={(e) => setQ(e.target.value)} placeholder="Bo'lim qidirish…" />
      </div>

      {(isTeacher || isSupport) && !q.trim() && (
        <div>
          <div className="jos-sect"><b>Ustoz ishi</b></div>
          <div className="jos-grid">
            {teacherItems.map((i) => (
              <Link key={i.to} to={i.to} className="jos-cell" style={{ animationDelay: `${Math.min(n++, 16) * 30}ms` }}>
                <Gem name={i.gem} size={54} />
                {i.label}
              </Link>
            ))}
          </div>
        </div>
      )}

      {sections.filter((s) => s.list.length).map((s) => (
        <div key={s.title}>
          <div className="jos-sect"><b>{s.title}</b></div>
          <div className="jos-grid">
            {s.list.map((i) => (
              <Link key={i.to} to={appHref(i.to)} className="jos-cell" style={{ animationDelay: `${Math.min(n++, 16) * 30}ms` }}>
                <Gem name={gemFor(i.to)} size={54} />
                {i.label}
              </Link>
            ))}
          </div>
        </div>
      ))}
      {items.length === 0 && <div className="jos-empty">Hech narsa topilmadi</div>}

      <div className="jos-sect"><b>Men</b></div>
      <div className="jos-list">
        <Link to="/app/tasks" className="jos-it"><Gem name="task" size={38} /><div className="m"><b>Vazifalarim</b><small>Ochiq va kechikkan ishlar</small></div></Link>
        <Link to="/app/alerts" className="jos-it"><Gem name="bell" size={38} /><div className="m"><b>Bildirishnomalar</b><small>Sizga tegishli xabarlar</small></div></Link>
        <Link to="/app/profile" className="jos-it"><Gem name="user" size={38} /><div className="m"><b>Profil</b><small>Lavozim, filial, parol, chiqish</small></div></Link>
      </div>
    </div>
  );
}
