import { useEffect } from "react";
import { NavLink, Outlet, Navigate } from "react-router-dom";
import { Home, BookOpen, Trophy, Gift, User } from "lucide-react";
import { useAuth } from "../../lib/AuthContext";

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
  { to: "/student", end: true, icon: Home, label: "Asosiy",
    tone: "text-brand-600 bg-brand-50" },
  { to: "/student/games", end: false, icon: BookOpen, label: "O'rganish",
    tone: "text-emerald-600 bg-emerald-50" },
  { to: "/student/leaderboard", end: false, icon: Trophy, label: "Reyting",
    tone: "text-amber-600 bg-amber-50" },
  { to: "/student/shop", end: false, icon: Gift, label: "Mukofotlar",
    tone: "text-violet-600 bg-violet-50" },
  { to: "/student/profile", end: false, icon: User, label: "Profil",
    tone: "text-sky-600 bg-sky-50" },
];

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

      <nav className="fixed bottom-0 inset-x-0 bg-white border-t border-slate-200 z-40 pb-safe">
        <div className="max-w-md mx-auto grid grid-cols-5">
          {TABS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              end={t.end}
              className="flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium"
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`flex items-center justify-center w-11 h-7 rounded-full transition ${
                      isActive ? t.tone : "text-slate-400"
                    }`}
                  >
                    <t.icon size={19} />
                  </span>
                  <span
                    className={
                      isActive
                        ? t.tone.split(" ")[0] + " font-semibold"
                        : "text-slate-400"
                    }
                  >
                    {t.label}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
