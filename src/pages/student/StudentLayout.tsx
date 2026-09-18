import "../../student-design.css";
import { studentTabFor } from "../../lib/studentNavigation";
import { useEffect } from "react";
import { Link, Outlet, Navigate, useLocation } from "react-router-dom";
import { Home, BookOpen, Trophy, Gift, User, ClipboardList } from "lucide-react";
import { useAuth } from "../../lib/AuthContext";
import { isStudentApp } from "../../lib/appMode";

/**
 * JONY STUDENT — ilova qobig'i (2026-08-09, menyu 2026-08-16 da
 * qayta tuzildi).
 *
 * Jahongir bergan yangi tartib:
 *   Asosiy      — kunlik vazifa va progress
 *   O'rganish   — Grammar, vocabulary va 4 skill
 *   Reyting     — guruh, filial va umumiy natija
 *   Mukofotlar  — coin do'koni, badge va sovrinlar
 *   Profil      — statistika, to'lov va sozlamalar
 *
 * "Mashq" -> "O'rganish", "Do'kon" -> "Mukofotlar" deb o'zgardi:
 * do'kon endi sovg'a va yutuqlar bilan bir bo'limda turadi, chunki
 * coin yig'ishning maqsadi shu yerda ko'rinadi.
 *
 * Xodimlar panelidan (Layout.tsx) ATAYLAB alohida: bu telefonga
 * mo'ljallangan. Kirish: o'quvchining O'Z login/paroli.
 */

const TABS = [
  { to: "/student", icon: Home, label: "Asosiy" },
  { to: "/student/games", icon: BookOpen, label: "O'rganish" },
  { to: "/student/lessons", icon: ClipboardList, label: "Darslar" },
  { to: "/student/leaderboard", icon: Trophy, label: "Reyting" },
  // Dizaynda (shop.png, 2026-08-20) faol "Mukofotlar" ko'k rangda -
  // do'kon ekrani bilan bir xil bo'lsin.
  { to: "/student/shop", icon: Gift, label: "Mukofotlar" },
  { to: "/student/profile", icon: User, label: "Profil" },
];

export default function StudentLayout() {
  const { user, logout } = useAuth();
  const path = useLocation().pathname;
  const activeTab = studentTabFor(path);

  // PWA: "Jony Student" nomi bilan uy ekraniga o'rnatiladi. Manifest
  // faqat shu bo'limda ulanadi — xodimlar paneli o'zicha qoladi.
  useEffect(() => {
    let link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = "manifest";
      document.head.appendChild(link);
    }
    link.href = "/student.webmanifest";
    const prevTitle = document.title;
    document.title = "Jony Student";
    return () => {
      link?.parentNode?.removeChild(link);
      document.title = prevTitle;
    };
  }, []);

  if (!user) return <Navigate to="/login" replace />;
  // Ilova rejimida xodim hisobi bilan ochilsa — xodim paneliga OLIB
  // KETILMAYDI (2026-08-18, "xodimlar ham akkauntlariga kirib
  // ketyabdi"): login sahifasiga qaytariladi, u yerda tushuntirish
  // chiqadi. Oddiy saytda esa avvalgidek o'z paneliga o'tadi.
  if (user.role !== "student" && isStudentApp()) {
    logout();
    return <Navigate to="/login" replace />;
  }
  if (user.role !== "student") return <Navigate to="/" replace />;

  return (
    <div className="student-app" data-design-version="jony-2026-09">
      <main className="student-content" id="student-content"><Outlet /></main>
      <nav aria-label="Asosiy menyu" className="student-nav fixed bottom-0 inset-x-0 z-40 border-t">
        <div className="max-w-md mx-auto grid grid-cols-5 pt-1.5 pb-1">
          {TABS.map((t) => (
            <Link key={t.to} to={t.to} aria-current={activeTab === t.to ? "page" : undefined}
              className="flex flex-col items-center gap-1 py-1 text-[11px] font-medium">
              <span className="student-nav-icon"><t.icon size={23} strokeWidth={1.8} /></span>
              <span>{t.label}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}
