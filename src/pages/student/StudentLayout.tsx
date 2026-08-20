import { useEffect } from "react";
import { NavLink, Outlet, Navigate, useLocation } from "react-router-dom";
import { Home, BookOpen, Trophy, Gift, User } from "lucide-react";
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
  { to: "/student", end: true, icon: Home, label: "Asosiy",
    tone: "text-brand-600 bg-brand-50" },
  { to: "/student/games", end: false, icon: BookOpen, label: "O'rganish",
    tone: "text-emerald-600 bg-emerald-50" },
  { to: "/student/leaderboard", end: false, icon: Trophy, label: "Reyting",
    tone: "text-amber-600 bg-amber-50" },
  // Dizaynda (shop.png, 2026-08-20) faol "Mukofotlar" ko'k rangda -
  // do'kon ekrani bilan bir xil bo'lsin.
  { to: "/student/shop", end: false, icon: Gift, label: "Mukofotlar",
    tone: "text-brand-600 bg-brand-50" },
  { to: "/student/profile", end: false, icon: User, label: "Profil",
    tone: "text-sky-600 bg-sky-50" },
];

export default function StudentLayout() {
  const { user, logout } = useAuth();

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

  // TO'Q KO'K TEMA (2026-08-20, Jahongir: "Jony Student appning
  // dizaynini toliq tashladim papkada 1ga 1 qilib ber"). Dizayn
  // berilgan 5 asosiy ekran to'q navy fonda; ichki sahifalar
  // (mashqlar, sozlamalar, to'lovlar...) hali eski och temada -
  // ularning matni to'q fonda ko'rinmay qolmasligi uchun fon
  // marshrutga qarab tanlanadi. Do'kon o'z fonini o'zi qo'yadi.
  const path = useLocation().pathname;
  const dark =
    path === "/student" ||
    path === "/student/leaderboard" ||
    path === "/student/roadmap" ||
    path === "/student/profile" ||
    path === "/student/grammar";
  return (
    <div className="min-h-screen pb-24"
         style={{ background: dark ? "#0A1233" : "#F1F5F9" }}>
      <Outlet />

      <nav
        className="fixed bottom-0 inset-x-0 z-40 pb-safe border-t"
        style={{ background: "rgba(10,17,46,0.97)", borderColor: "#1D2A63" }}
      >
        <div className="max-w-md mx-auto grid grid-cols-5 pt-1.5 pb-1">
          {TABS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              end={t.end}
              className="flex flex-col items-center gap-1 py-1 text-[11px] font-medium"
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`flex items-center justify-center w-12 h-8 rounded-2xl transition ${
                      isActive ? "bg-brand-600 text-white" : "text-slate-400"
                    }`}
                  >
                    <t.icon size={19} />
                  </span>
                  <span
                    className={
                      isActive
                        ? "text-brand-400 font-semibold"
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
