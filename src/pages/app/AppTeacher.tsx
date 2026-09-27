import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../lib/AuthContext";
import { AutoTranslate } from "../../components/AutoTranslate";

const ALLOWED = ["teacher", "support_teacher"];

/**
 * USTOZ ISHI — sobiq "Jony Teacher" ilovasi, endi JonyOS ichida
 * (2026-09-27, Jahongir: "Jony Teacher va JonyOS xodimlar uchun bitta
 * programma bo'laversin, hamma xodimga alohida programma qilib
 * o'tirmaymizku").
 *
 * Sahifalar (bugungi darslar, yo'qlama, jadval, tekshirish, soat
 * belgilash, lug'at, oylik) o'zgarmadi — faqat JonyOS qobig'i va
 * dizayni ichida ochiladi. Yo'qlama va oylik hisobi aynan o'sha kod.
 */
export default function AppTeacher() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!ALLOWED.includes(user.role)) return <Navigate to="/app" replace />;
  return (
    <div className="jos-t">
      {/* Ruscha rejim (2026-08-13) — ustoz kabinetida bo'lgani kabi */}
      <AutoTranslate />
      <Outlet />
    </div>
  );
}
