import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Layers,
  GraduationCap as TeacherIcon,
  LogOut,
  School,
  Building2,
  UserCog,
  KeyRound,
  Target,
  Wallet,
  BarChart3,
  PieChart,
  Trophy,
  Megaphone,
  Briefcase,
  History,
  GraduationCap as AcademicIcon,
  CalendarDays,
  Archive as ArchiveIcon,
  ClipboardList,
  Package,
  ShieldCheck,
  Coins,
  MessageSquareWarning,
  X,
} from "lucide-react";
import { useAuth } from "../lib/AuthContext";
import {
  FOUNDER,
  STAFF_VIEWERS,
  LEAD_ACCESS,
  FINANCE_ACCESS,
  TEACHING_STAFF,
  HR_ACCESS,
  MARKETING_ACCESS,
  AUDIT_VIEW,
  EXAM_VIEW,
  ACADEMIC_VIEW,
  can,
  roleLabel,
  TASK_ACCESS,
  INVENTORY_VIEW,
  CASH_ACCESS,
  STUDENT,
  PARENT,
} from "../lib/roles";
import { api } from "../lib/api";
import { QuickPayment } from "./QuickPayment";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/students", label: "Talabalar", icon: Users },
  { to: "/groups", label: "Guruhlar", icon: Layers },
  { to: "/teachers", label: "O'qituvchilar", icon: TeacherIcon },
];

/**
 * Asoschida menyu qisqaroq: Talabalar va Guruhlar O'quv bo'limi
 * ichida, Xodimlar esa HR ichida turadi. Menyuda 20 ta qator
 * bo'lgandan ko'ra, o'z joyida turgani yaxshi.
 */
const FOUNDER_MOVED = ["/students", "/groups", "/users"];

function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit() {
    if (next.length < 6) {
      setError("Yangi parol kamida 6 belgidan iborat bo'lishi kerak");
      return;
    }
    if (next !== confirm) {
      setError("Yangi parollar mos kelmadi");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.put("/auth/me/password", {
        current_password: current,
        new_password: next,
      });
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Parolni almashtirish</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        {done ? (
          <div className="space-y-3">
            <p className="text-sm text-green-700">Parol muvaffaqiyatli yangilandi.</p>
            <button
              onClick={onClose}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium"
            >
              Yopish
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Joriy parol
              </label>
              <input
                type="password"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Yangi parol
              </label>
              <input
                type="password"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={next}
                onChange={(e) => setNext(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Yangi parolni tasdiqlang
              </label>
              <input
                type="password"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              onClick={submit}
              disabled={saving}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-1 disabled:opacity-60"
            >
              {saving ? "Saqlanmoqda..." : "Saqlash"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  let items = navItems;
  // Asoschida bu bo'limlar o'z bo'limi ichiga ko'chirilgan
  if (user?.role === FOUNDER) {
    items = items.filter((i) => !FOUNDER_MOVED.includes(i.to));
  }
  // "Bugungi holat" endi Dashboard ICHIDA alohida bo'lim - menyuda
  // takrorlanmaydi.
  // Dars jadvali va Lidlar - administratorning kuni shulardan boshlanadi,
  // shuning uchun eng tepada turadi.
  if (can(user?.role, TEACHING_STAFF)) {
    items = [
      items[0],
      { to: "/timetable", label: "Dars jadvali", icon: CalendarDays },
      ...items.slice(1),
    ];
  }
  if (can(user?.role, LEAD_ACCESS)) {
    items = [
      items[0],
      { to: "/leads", label: "Lidlar", icon: Target },
      ...items.slice(1),
    ];
  }
  // Coin tizimi o'quv jarayoniga tegishli - ustozlar ham ko'radi.
  if (can(user?.role, TEACHING_STAFF)) {
    items = [...items, { to: "/gamification", label: "Coin tizimi", icon: Trophy }];
  }
  // O'quvchi va ota-ona uchun - o'z coin kabineti
  if (user?.role === STUDENT || user?.role === PARENT) {
    items = [
      ...items,
      { to: "/my-coins", label: "Mening coinlarim", icon: Coins },
    ];
  }
  // Moliya - administratorda ham bor, lekin ichida faqat qarzdorlar
  // va oylik hisob-kitob turadi (foyda-zarar unga ko'rinmaydi).
  if (can(user?.role, CASH_ACCESS)) {
    items = [...items, { to: "/finance", label: "Moliya", icon: Wallet }];
  }
  if (can(user?.role, FINANCE_ACCESS)) {
    items = [
      ...items,
      { to: "/reports", label: "Hisobotlar", icon: BarChart3 },
      { to: "/analytics", label: "Analitika", icon: PieChart },
    ];
  }
  // O'quv bo'limi - ta'lim sifati. Guruhlardan keyin turadi.
  if (can(user?.role, ACADEMIC_VIEW)) {
    items = [...items, { to: "/academic", label: "O'quv bo'limi", icon: AcademicIcon }];
  }
  // Marketing - SMM manager uchun asosiy bo'lim.
  if (can(user?.role, MARKETING_ACCESS)) {
    items = [...items, { to: "/marketing", label: "Marketing", icon: Megaphone }];
  }
  // Asoschida Xodimlar HR ichida turadi — menyuda takrorlanmaydi.
  if (can(user?.role, STAFF_VIEWERS) && user?.role !== FOUNDER) {
    items = [...items, { to: "/users", label: "Xodimlar", icon: UserCog }];
  }
  // HR - xodimlar ro'yxatidan keyin, chunki u kadr ishining davomi.
  if (can(user?.role, HR_ACCESS)) {
    items = [...items, { to: "/hr", label: "HR", icon: Briefcase }];
  }
  if (can(user?.role, TEACHING_STAFF)) {
    items = [...items,
             { to: "/complaints", label: "Shikoyatlar", icon: MessageSquareWarning }];
  }
  // O'zgarishlar tarixi - eng oxirida, kamdan-kam ochiladi.
  // Audit - nazorat bo'limi: o'zgarishlar tarixi va imtihonlar.
  // Examiner ham shu yerga kiradi (u asoschiga bo'ysunadi).
  if (can(user?.role, AUDIT_VIEW) || can(user?.role, EXAM_VIEW)) {
    items = [...items, { to: "/audit", label: "Audit", icon: History }];
  }
  if (can(user?.role, TASK_ACCESS)) {
    items = [...items, { to: "/tasks", label: "Vazifalar", icon: ClipboardList }];
  }
  if (can(user?.role, INVENTORY_VIEW)) {
    items = [...items, { to: "/inventory", label: "Ombor", icon: Package }];
  }
  if (can(user?.role, TEACHING_STAFF)) {
    items = [...items, { to: "/archive", label: "Arxiv", icon: ArchiveIcon }];
  }
  if (user?.role === FOUNDER) {
    items = [
      ...items,
      { to: "/branches", label: "Filiallar", icon: Building2 },
      { to: "/permissions", label: "Ruxsatlar", icon: ShieldCheck },
    ];
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-60 shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <School className="text-white" size={18} />
          </div>
          <span className="font-semibold text-slate-900">Jony CRM</span>
        </div>

        {/* Tez to'lov - administrator uchun eng ko'p bosiladigan tugma,
            shuning uchun menyuning eng tepasida turadi. */}
        {can(user?.role, CASH_ACCESS) && (
          <div className="px-3 pt-3">
            <QuickPayment />
          </div>
        )}

        <nav className="flex-1 px-3 py-4 space-y-1">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-slate-100">
          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `block px-3 py-2 mb-1 rounded-lg transition ${
                isActive ? "bg-brand-50" : "hover:bg-slate-100"
              }`
            }
          >
            <p className="text-sm font-medium text-slate-800 truncate">
              {user?.full_name}
            </p>
            <p className="text-xs text-slate-400">
              {roleLabel(user?.role)} · profilim
            </p>
          </NavLink>
          <button
            onClick={() => setShowPasswordModal(true)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100"
          >
            <KeyRound size={16} />
            Parolni almashtirish
          </button>
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100"
          >
            <LogOut size={16} />
            Chiqish
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </div>
  );
}
