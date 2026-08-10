import { useEffect } from "react";
import { NavLink, Outlet, Navigate } from "react-router-dom";
import { CalendarDays, Home, LayoutGrid, User } from "lucide-react";
import { useAuth } from "../../lib/AuthContext";

const TABS = [
  { to: "/teacher", end: true, icon: Home, label: "Bugun" },
  { to: "/teacher/week", end: false, icon: CalendarDays, label: "Jadval" },
  { to: "/teacher/more", end: false, icon: LayoutGrid, label: "Bo'limlar" },
  { to: "/teacher/profile", end: false, icon: User, label: "Profil" },
];

const ALLOWED = ["teacher", "support_teacher"];

/**
 * JONY TEACHER — ilova qobig'i (2026-08-10).
 *
 * Jahongir: "ustozlar uchun ham alohida qilib ber, ular yo'qlama
 * qo'yishi va ularda bor barcha funksiyalar chiqsin."
 *
 * NEGA ALOHIDA: xodimlar paneli katta ekran uchun — yon menyu, keng
 * jadvallar. Ustoz esa darsxonaga TELEFON bilan kiradi va kuniga bir
 * marta, tez yo'qlama qo'yadi. Shuning uchun bu qobiq: pastda 4 ta
 * tab, katta bosiladigan tugmalar, bitta ekranda bitta ish.
 *
 * "Barcha funksiyalar" — "Bo'limlar" tabida: mavjud sahifalar
 * (guruhlarim, kitob/imtihon buyurtma, oylik, natijalar, karyera...)
 * qayta yozilmadi, shu yerdan ochiladi.
 */
export default function TeacherLayout() {
  const { user } = useAuth();

  useEffect(() => {
    let link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = "manifest";
      document.head.appendChild(link);
    }
    link.href = "/teacher.webmanifest";
    const prev = document.title;
    document.title = "Jony Teacher";
    return () => {
      link?.parentNode?.removeChild(link);
      document.title = prev;
    };
  }, []);

  if (!user) return <Navigate to="/login" replace />;
  if (!ALLOWED.includes(user.role)) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Outlet />

      <nav className="fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur border-t border-slate-200 z-40 pb-safe">
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
