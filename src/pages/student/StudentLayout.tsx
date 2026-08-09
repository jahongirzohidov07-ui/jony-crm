import { useEffect } from "react";
import { NavLink, Outlet, Navigate } from "react-router-dom";
import { Home, Gamepad2, Trophy, User } from "lucide-react";
import { useAuth } from "../../lib/AuthContext";

const TABS = [
  { to: "/student", end: true, icon: Home, label: "Asosiy" },
  { to: "/student/games", end: false, icon: Gamepad2, label: "Mashq" },
  { to: "/student/leaderboard", end: false, icon: Trophy, label: "Reyting" },
  { to: "/student/profile", end: false, icon: User, label: "Profil" },
];

/**
 * JONY STUDENT — ilova qobig'i (2026-08-09).
 *
 * Xodimlar panelidan (Layout.tsx) ATAYLAB alohida: bu telefonga
 * mo'ljallangan, pastda tab paneli bilan ishlaydigan ilova. O'quvchi
 * uchun yon menyu, filial tanlagich va boshqa xodim vositalari
 * umuman ko'rinmasligi kerak.
 *
 * Kirish: o'quvchining O'Z login/paroli (administrator o'quvchi
 * kartasidan ochib beradi). Rol "student" bo'lmagan odam bu yerga
 * kirsa — xodimlar paneliga qaytariladi.
 */
export default function StudentLayout() {
  const { user } = useAuth();

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
  if (user.role !== "student") return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Outlet />

      <nav className="fixed bottom-0 inset-x-0 bg-white border-t border-slate-200 z-40">
        <div className="max-w-md mx-auto grid grid-cols-4">
          {TABS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              end={t.end}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium transition ${
                  isActive ? "text-brand-600" : "text-slate-400"
                }`
              }
            >
              <t.icon size={20} />
              {t.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
