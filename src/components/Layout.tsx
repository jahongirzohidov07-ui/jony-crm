import { useState, useRef, useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Layers,
  BookMarked,
  GraduationCap as TeacherIcon,
  LogOut,
  School,
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
  ClipboardCheck,
  Timer,
  Package,
  ShieldCheck,
  Coins,
  MessageSquareWarning,
  X,
  Menu,
  Bell,
  Settings as SettingsIcon,
 Search } from "lucide-react";
import { useAuth } from "../lib/AuthContext";
import {
  SCHEDULE_VIEW,
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
  TEACHER,
  SUPPORT_TEACHER,
  CONTENT_REQUESTER,
  IDEA_SUBMIT,
  TEACHER_MENU,
  BRANCH_SWITCH,
} from "../lib/roles";
import { api, setGlobalBranch, getGlobalBranch } from "../lib/api";
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
    if (next.length < 8 || !/[a-zA-Z]/.test(next) || !/\d/.test(next)) {
      setError("Parol kamida 8 belgi bo'lib, ichida harf ham, raqam "
        + "ham bo'lishi kerak");
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
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (profileRef.current &&
          !profileRef.current.contains(e.target as Node))
        setProfileOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);
  const navigate = useNavigate();
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);

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
  if (can(user?.role, SCHEDULE_VIEW)) {
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
    items = [...items, { to: "/gamification", label: "Gamification", icon: Trophy }];
  }
  // Ustoz o'z karyera yo'lini ko'radi: daraja, stavka, keyingi bosqich.
  if (user?.role === TEACHER || user?.role === SUPPORT_TEACHER) {
    items = [
      ...items,
      { to: "/my-career", label: "Mening yo'lim", icon: TeacherIcon },
    ];
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
  // Sotuv menejerining ishi sotuv — bu bo'lim unga ko'rinmaydi.
  if (can(user?.role, ACADEMIC_VIEW) && user?.role !== "sales_manager") {
    items = [...items, { to: "/academic", label: "O'quv bo'limi", icon: AcademicIcon }];
  }
  // SMM - kontent quvuri: g'oyadan natijagacha. HR menejeriga bu
  // bo'lim kerak emas — uning ishi odamlar, kontent emas.
  // SMM endi Marketing ICHIDA (tab). Marketingga kirolmaydigan, lekin
  // kontent so'rovi/g'oya beradigan rollargagina alohida band qoladi.
  if (
    (can(user?.role, CONTENT_REQUESTER) || can(user?.role, IDEA_SUBMIT)) &&
    !can(user?.role, MARKETING_ACCESS) &&
    user?.role !== "hr_manager" &&
    user?.role !== "sales_manager"
  ) {
    items = [...items, { to: "/smm", label: "SMM", icon: Megaphone }];
  }
  // Marketing - reklama va voronka analitikasi.
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
  // Vazifalar endi tepada, qo'ng'iroqcha yonida turadi — menyuda emas.
  if (can(user?.role, INVENTORY_VIEW)) {
    items = [...items, { to: "/inventory", label: "Ombor", icon: Package }];
  }
  if (can(user?.role, TEACHING_STAFF)) {
    items = [...items, { to: "/archive", label: "Arxiv", icon: ArchiveIcon }];
  }
  if (user?.role === FOUNDER) {
    items = [
      ...items,
      { to: "/settings", label: "Sozlamalar", icon: SettingsIcon },
    ];
  }
  // Ustozda menyu ochiq ro'yxat bo'yicha kesiladi: dars berishga
  // aloqasi yo'q bo'lim ko'rinmaydi.
  if (user?.role === TEACHER) {
    // Ustozda "Guruhlar" va "Talabalar" o'rniga o'ziniki: butun
    // markazning ro'yxati ustozning ishiga aloqador emas
    items = [
      ...items,
      { to: "/my-groups", label: "Guruhlarim", icon: Layers },
      { to: "/my-students", label: "O'quvchilarim", icon: AcademicIcon },
      { to: "/my-schedule", label: "Darslarim", icon: CalendarDays },
      { to: "/my-books", label: "Kitob buyurtma", icon: BookMarked },
      { to: "/my-exams", label: "Imtihon buyurtma", icon: ClipboardCheck },
      { to: "/my-results", label: "Mening natijalarim", icon: PieChart },
    ];
    items = TEACHER_MENU
      .map((to) => items.find((i) => i.to === to))
      .filter((i): i is (typeof items)[number] => !!i);
  }
  // Support teacher: qisqa menyu — coin, imtihon va kitob buyurtma YO'Q.
  // Jadvali biriktirilgan guruhlardan chiqadi.
  if (user?.role === SUPPORT_TEACHER) {
    items = [
      items[0],
      { to: "/my-schedule", label: "Dars jadvalim", icon: CalendarDays },
      { to: "/my-groups", label: "Guruhlarim", icon: Layers },
      { to: "/my-students", label: "O'quvchilarim", icon: AcademicIcon },
      { to: "/my-sessions", label: "Darslarim va oyligim", icon: Timer },
      { to: "/my-results", label: "Mening natijalarim", icon: PieChart },
    ];
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Mobil parda — menyu ochiq bo'lsa orqa fonni qoraytiradi */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        onClick={(e) => {
          // Mobilda menyu bandi bosilganda panel yopiladi
          if ((e.target as HTMLElement).closest("a")) setMobileOpen(false);
        }}
        className={`${
          mobileOpen ? "fixed inset-y-0 left-0 z-50 flex" : "hidden"
        } md:static md:flex md:z-auto w-60 shrink-0 bg-white border-r border-slate-200 flex-col overflow-y-auto`}
      >
        <div className="h-16 shrink-0 flex items-center gap-2 px-5 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <School className="text-white" size={18} />
          </div>
          <span className="font-semibold text-slate-900">JonyOS</span>
          <button
            onClick={() => setMobileOpen(false)}
            className="ml-auto md:hidden text-slate-400 p-1"
          >
            <X size={18} />
          </button>
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

      </aside>

      <main className="flex-1 min-w-0 relative">
        {/* Yuqori panel: mobil menyu, qidiruv, qo'ng'iroqcha, profil */}
        <div className="absolute top-4 left-3 z-40 md:hidden">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 bg-white border border-slate-200 rounded-lg shadow-sm text-slate-600"
          >
            <Menu size={18} />
          </button>
        </div>
        {/* Global o'quvchi qidiruv — barcha xodimlar uchun */}
        <GlobalSearch />
        {can(user?.role, BRANCH_SWITCH) && <BranchSwitcher />}
        {can(user?.role, TASK_ACCESS) && (
          <div className="absolute top-4 right-28 sm:right-[16.5rem] z-40">
            <button
              onClick={() => navigate("/tasks")}
              title="Vazifalar"
              className="p-2.5 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:text-slate-700"
            >
              <ClipboardList size={20} />
            </button>
          </div>
        )}
        <NotifBell />
        {/* Profil — yuqori o'ng burchakda */}
        <div className="absolute top-4 right-3 md:right-6 z-40" ref={profileRef}>
          <button
            onClick={() => setProfileOpen((v) => !v)}
            className="flex items-center gap-2 bg-white border border-slate-200 rounded-full pl-1.5 pr-1.5 sm:pr-3 py-1.5 shadow-sm hover:shadow transition"
          >
            <span className="w-7 h-7 rounded-full bg-brand-600 text-white text-sm font-semibold flex items-center justify-center">
              {(user?.full_name || "?").charAt(0)}
            </span>
            <span className="hidden sm:block text-sm font-medium text-slate-700 max-w-[140px] truncate">
              {user?.full_name}
            </span>
          </button>
          {profileOpen && (
            <div className="absolute right-0 mt-2 w-60 bg-white border border-slate-200 rounded-xl shadow-lg py-2">
              <NavLink
                to="/profile"
                onClick={() => setProfileOpen(false)}
                className="block px-4 py-2 hover:bg-slate-50"
              >
                <p className="text-sm font-medium text-slate-800 truncate">
                  {user?.full_name}
                </p>
                <p className="text-xs text-slate-400">
                  {roleLabel(user?.role)} · profilim
                </p>
              </NavLink>
              <button
                onClick={() => {
                  setProfileOpen(false);
                  setShowPasswordModal(true);
                }}
                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
              >
                <KeyRound size={15} />
                Parolni almashtirish
              </button>
              {user?.role === FOUNDER && (
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    setShowRecoveryModal(true);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <ShieldCheck size={15} />
                  Tiklash kodini o'rnatish
                </button>
              )}
              <button
                onClick={onLogout}
                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
              >
                <LogOut size={15} />
                Chiqish
              </button>
            </div>
          )}
        </div>
        <Outlet />
      </main>

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
      {showRecoveryModal && (
        <RecoveryModal onClose={() => setShowRecoveryModal(false)} />
      )}
    </div>
  );
}


/** Asoschi uchun favqulodda tiklash kodi: parol unutilsa, login
 *  oynasidagi "Parolni unutdingizmi?" orqali shu kod bilan tiklanadi. */
function RecoveryModal({ onClose }: { onClose: () => void }) {
  const [current, setCurrent] = useState("");
  const [code, setCode] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit() {
    if (code.trim().length < 10) {
      setError("Kod kamida 10 belgi bo'lsin (masalan, uzun ibora)");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.put("/auth/recovery-code", {
        current_password: current,
        recovery_code: code.trim(),
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
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-900">Tiklash kodi</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        {done ? (
          <div className="space-y-3">
            <p className="text-sm text-green-700">
              Kod o'rnatildi. Uni QOG'OZGA yozib, ishonchli joyda
              saqlang — parolni unutsangiz faqat shu kod qutqaradi.
            </p>
            <button onClick={onClose}
              className="w-full bg-slate-900 text-white rounded-lg py-2.5 text-sm">
              Yopish
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-slate-500">
              Parolni unutsangiz, login oynasida shu kod bilan yangi
              parol o'rnatasiz. Kodni hech kimga bermang.
            </p>
            <input
              type="password"
              placeholder="Joriy parolingiz"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
            />
            <input
              type="text"
              placeholder="Yangi tiklash kodi (kamida 10 belgi)"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              onClick={submit}
              disabled={saving}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60"
            >
              {saving ? "Saqlanmoqda..." : "O'rnatish"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}


/** Qo'ng'iroqcha: vazifalar, qaytadigan muzlatilganlar, qarzdorlar,
 *  muddati yaqin hujjatlar — bo'limlarga kirmasdan bir joyda. */
function NotifBell() {
  const navigate = useNavigate();
  const [d, setD] = useState<{ items: NotifItem[]; count: number } | null>(null);
  const [openB, setOpenB] = useState(false);
  // O'qilganini eslab qolamiz: ochilganda belgi o'chadi, faqat YANGI
  // xabar kelganda qaytib chiqadi.
  const [seenKey, setSeenKey] = useState(
    () => localStorage.getItem("jonyos_alerts_seen") || ""
  );
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const load = () =>
      api.get<{ items: NotifItem[]; count: number }>("/my/alerts")
        .then(setD)
        .catch(() => {});
    load();
    const t = setInterval(load, 3 * 60 * 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node))
        setOpenB(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const TONE: Record<string, string> = {
    red: "bg-red-500", amber: "bg-amber-500",
    sky: "bg-sky-500", emerald: "bg-emerald-500",
  };

  return (
    <div className="absolute top-4 right-16 sm:right-56 z-40" ref={ref}>
      <button
        onClick={() => {
          setOpenB((v) => !v);
          const key = d ? JSON.stringify(d.items.map((i) => i.text)) : "";
          localStorage.setItem("jonyos_alerts_seen", key);
          setSeenKey(key);
        }}
        className="relative p-2.5 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:text-slate-700"
      >
        <Bell size={20} />
        {(d?.count || 0) > 0 &&
          JSON.stringify(d!.items.map((i) => i.text)) !== seenKey && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-semibold flex items-center justify-center">
            {d!.count > 9 ? "9+" : d!.count}
          </span>
        )}
      </button>
      {openB && (
        <div className="absolute right-0 mt-2 w-80 max-w-[86vw] bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 max-h-96 overflow-auto">
          {(d?.items || []).map((it, i) => (
            <button
              key={i}
              onClick={() => {
                setOpenB(false);
                if (it.link) navigate(it.link);
              }}
              className="w-full text-left px-3 py-2.5 hover:bg-slate-50 flex items-start gap-2.5"
            >
              <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${TONE[it.tone] || "bg-slate-300"}`} />
              <span className="text-sm text-slate-700">{it.text}</span>
            </button>
          ))}
          {(!d || d.items.length === 0) && (
            <p className="text-sm text-slate-400 px-3 py-3 text-center">
              Hozircha yangilik yo'q 👌
            </p>
          )}
        </div>
      )}
    </div>
  );
}

type NotifItem = { icon: string; text: string; link?: string; tone: string };


/** Tepadagi global qidiruv: 3 harfdan boshlab o'quvchilar va
 *  potensial o'quvchilar (lidlar) chiqadi. */
function GlobalSearch() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [res, setRes] = useState<SearchRes | null>(null);
  const [openS, setOpenS] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node))
        setOpenS(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  useEffect(() => {
    if (q.trim().length < 3) { setRes(null); return; }
    const t = setTimeout(() => {
      api.get<SearchRes>(
        `/search/students?q=${encodeURIComponent(q.trim())}`)
        .then((r) => { setRes(r); setOpenS(true); })
        .catch(() => setRes(null));
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div className="absolute top-4 left-14 right-40 sm:left-auto sm:right-[30.5rem] z-40 sm:w-64"
         ref={boxRef}>
      <div className="relative">
        <Search size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => res && setOpenS(true)}
          placeholder="O'quvchi qidirish…"
          className="w-full bg-white border border-slate-200 rounded-full pl-8 pr-3 py-2 text-sm shadow-sm focus:border-brand-400 focus:outline-none"
        />
      </div>
      {openS && res && (
        <div className="absolute mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 max-h-96 overflow-auto">
          {res.students.length > 0 && (
            <p className="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
              O'quvchilar
            </p>
          )}
          {res.students.map((s) => (
            <button key={`s${s.id}`}
              onClick={() => { setOpenS(false); setQ("");
                navigate(`/students/${s.id}`); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-50">
              <p className="text-sm text-slate-800">{s.name}</p>
              <p className="text-xs text-slate-400">
                {s.group || "guruhsiz"} · {s.status_label}
              </p>
            </button>
          ))}
          {res.leads.length > 0 && (
            <p className="px-3 pt-1.5 pb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400 border-t border-slate-100">
              Potensial o'quvchilar (lidlar)
            </p>
          )}
          {res.leads.map((l) => (
            <button key={`l${l.id}`}
              onClick={() => { setOpenS(false); setQ("");
                navigate("/leads"); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-50">
              <p className="text-sm text-slate-800">{l.name}</p>
              <p className="text-xs text-slate-400">{l.status_label}</p>
            </button>
          ))}
          {(res.groups || []).length > 0 && (
            <p className="px-3 pt-1.5 pb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400 border-t border-slate-100">
              Guruhlar
            </p>
          )}
          {(res.groups || []).map((g) => (
            <button key={`g${g.id}`}
              onClick={() => { setOpenS(false); setQ("");
                navigate(`/groups/${g.id}`); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-50">
              <p className="text-sm text-slate-800">{g.name}</p>
            </button>
          ))}
          {(res.teachers || []).length > 0 && (
            <p className="px-3 pt-1.5 pb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400 border-t border-slate-100">
              Ustozlar
            </p>
          )}
          {(res.teachers || []).map((t) => (
            <button key={`t${t.id}`}
              onClick={() => { setOpenS(false); setQ("");
                navigate("/teachers"); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-50">
              <p className="text-sm text-slate-800">{t.name}</p>
            </button>
          ))}
          {(res.staff || []).length > 0 && (
            <p className="px-3 pt-1.5 pb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400 border-t border-slate-100">
              Xodimlar
            </p>
          )}
          {(res.staff || []).map((u) => (
            <button key={`u${u.id}`}
              onClick={() => { setOpenS(false); setQ("");
                navigate("/users"); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-50">
              <p className="text-sm text-slate-800">{u.name}</p>
              <p className="text-xs text-slate-400">{u.status_label}</p>
            </button>
          ))}
          {res.students.length === 0 && res.leads.length === 0 &&
            (res.groups || []).length === 0 &&
            (res.teachers || []).length === 0 &&
            (res.staff || []).length === 0 && (
            <p className="text-sm text-slate-400 px-3 py-2.5">
              Topilmadi.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

type SearchRow = {
  id: number; name: string; group?: string | null;
  status_label: string;
};
type SearchRes = {
  students: SearchRow[]; leads: SearchRow[];
  groups?: { id: number; name: string }[];
  teachers?: { id: number; name: string }[];
  staff?: SearchRow[];
};


/** FILIAL ALMASHTIRGICH — rahbariyat uchun (asoschi, o'quv bo'limi,
 *  SMM, HR, moliya direktori). Tanlangan filial BUTUN platformaga
 *  ta'sir qiladi: har bir sahifa faqat shu filial ma'lumotini
 *  ko'rsatadi. "Barcha filiallar" — umumiy ko'rinish. Qolgan xodimlar
 *  o'z filialiga bog'langan, ularga bu tanlagich chiqmaydi. */
function BranchSwitcher() {
  const [branches, setBranches] = useState<
    { id: number; name: string }[]
  >([]);
  const current = getGlobalBranch();

  useEffect(() => {
    api.get<{ id: number; name: string }[]>("/branches")
      .then(setBranches)
      .catch(() => {});
  }, []);

  if (branches.length < 2) return null;

  return (
    <div className="absolute top-4 right-[19.5rem] z-40 hidden sm:block">
      <select
        value={current || ""}
        onChange={(e) => {
          setGlobalBranch(e.target.value || null);
          // Hamma sahifa yangi filial bilan qayta yuklansin
          window.location.reload();
        }}
        title="Filial bo'yicha ko'rish"
        className={`h-10 rounded-full border px-3 pr-7 text-sm shadow-sm bg-white focus:outline-none max-w-[10.5rem] truncate ${
          current
            ? "border-brand-400 text-brand-700 font-medium"
            : "border-slate-200 text-slate-600"
        }`}
      >
        <option value="">Barcha filiallar</option>
        {branches.map((b) => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </select>
    </div>
  );
}
