import { useState, useRef, useEffect } from "react";
import { formatPhone } from "./PhoneInput";
import { NavLink, Outlet, useNavigate, Link } from "react-router-dom";
import { BrandIcon } from "./BrandIcon";
import {
  LogOut,
  UserCog,
  KeyRound,
  ClipboardList,
  ShieldCheck,
  X,
  Menu,
  Bell,
  Search,
  Smartphone,
} from "lucide-react";
import { useAuth } from "../lib/AuthContext";
import { buildNav } from "./navItems";
import {
  FOUNDER,
  can,
  roleLabel,
  TASK_ACCESS,
  CASH_ACCESS,
  STUDENT,
  PARENT,
  BRANCH_SWITCH,
  ALL_BRANCH_ROLES,
} from "../lib/roles";
import {
  api, setGlobalBranch, getGlobalBranch, setActiveRole, getActiveRole,
  setToken,
} from "../lib/api";
import type { Branch } from "../lib/api";
import { QuickPayment } from "./QuickPayment";
import { DrillTimer } from "./DrillTimer";
import { PasswordInput } from "./PasswordInput";

// Menyu bandlari endi ./navItems.ts da (buildNav) — JonyOS xodim
// ilovasi (/app) ham AYNAN shu ro'yxatni ishlatadi (2026-09-27).


function ChangePasswordModal({ onClose, forced = false }: {
  onClose: () => void;
  /** Standart parol bilan kirilgan — yopib bo'lmaydi (2026-09-06) */
  forced?: boolean;
}) {
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
          {!forced && (
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
              <X size={18} />
            </button>
          )}
        </div>

        {forced && !done && (
          <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200
                        rounded-lg px-3 py-2 mb-3">
            Hisobingizda standart parol turibdi. Login — telefon raqamingiz,
            ya'ni uni har kim biladi. Davom etish uchun yangi parol
            qo'ying.
          </p>
        )}

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
              <PasswordInput
                value={current}
                onChange={setCurrent}
                autoFocus
                autoComplete="current-password"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Yangi parol
              </label>
              <PasswordInput
                value={next}
                onChange={setNext}
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Yangi parolni tasdiqlang
              </label>
              <PasswordInput
                value={confirm}
                onChange={setConfirm}
                autoComplete="new-password"
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

/** Xodim o'z loginini almashtiradi (2026-09-16, Jahongir: "loginni ham
 *  har bir xodim ... edit qila olsin"). Token ichida login turadi —
 *  server yangi token qaytaradi, shu zahoti saqlanadi. */
export function ChangeUsernameModal({
  onClose, onDone,
}: {
  onClose: () => void;
  onDone?: (login: string) => void;
}) {
  const [currentLogin, setCurrentLogin] = useState("");
  const [next, setNext] = useState("");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ username: string }>("/auth/me", true)
      .then((r) => setCurrentLogin(r.username))
      .catch(() => {});
  }, []);

  async function submit() {
    const login = next.trim();
    if (!/^[A-Za-z0-9._@-]{3,40}$/.test(login)) {
      setError("Login 3-40 belgi bo'lsin: lotin harflari, raqamlar va "
        + ". _ - @ belgilari, probelsiz");
      return;
    }
    if (!password) {
      setError("Tasdiqlash uchun joriy parolni kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const r = await api.put<{ username: string; access_token: string }>(
        "/auth/me/username",
        { current_password: password, new_username: login },
      );
      // Qaysi omborda turgan bo'lsa ("eslab qolish"), o'shanga yoziladi
      setToken(r.access_token, localStorage.getItem("jony_crm_token") !== null);
      setDone(r.username);
      onDone?.(r.username);
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
          <h2 className="font-semibold text-slate-900">Loginni almashtirish</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        {done ? (
          <div className="space-y-3">
            <p className="text-sm text-green-700">
              Login yangilandi. Endi tizimga <b>{done}</b> bilan kirasiz.
            </p>
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
                Hozirgi login
              </label>
              <p className="text-sm font-medium text-slate-800 px-1">
                {currentLogin || "…"}
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Yangi login
              </label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                autoFocus
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Joriy parol (tasdiqlash uchun)
              </label>
              <PasswordInput
                value={password}
                onChange={setPassword}
                autoComplete="current-password"
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
  const [showUsernameModal, setShowUsernameModal] = useState(false);
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  // STANDART PAROL: login javobida must_change_password kelgan bo'lsa
  // (2026-09-06 xavfsizlik auditi) — oyna majburiy ochiladi.
  const [forcePw, setForcePw] = useState(() => {
    try {
      return localStorage.getItem("jony_must_change_pw") === "1";
    } catch {
      return false;
    }
  });

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  // SINOV FILIALI (2026-09-26): "Mashq" bandi faqat shu filial
  // tanlanganda ko'rinadi. Filial ro'yxati bir marta olinadi;
  // so'rov muvaffaqiyatsiz bo'lsa band chiqmaydi (xavfsiz tomoni).
  const [testBranches, setTestBranches] = useState<number[]>([]);
  useEffect(() => {
    let alive = true;
    api
      .get<Branch[]>("/branches")
      .then((bs) => {
        if (alive) setTestBranches(bs.filter((b) => b.is_test).map((b) => b.id));
      })
      .catch(() => {
        if (alive) setTestBranches([]);
      });
    return () => {
      alive = false;
    };
  }, []);
  const onTestBranch = (() => {
    const cur = getGlobalBranch();
    return !!cur && testBranches.includes(Number(cur));
  })();

  const items = buildNav(user, { onTestBranch });

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
          <div className="w-8 h-8 rounded-lg overflow-hidden shrink-0">
            <BrandIcon size={32} />
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
              data-guide={"nav-" + (to === "/" ? "dashboard" : to.replace(/^\//, ""))}
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

      {/* pt-8: yuqoridagi suzuvchi panel (qidiruv, qo'ng'iroq, profil)
          sahifaning o'z tugmalarini bosib qolmasin. Suzuvchi elementlar
          absolute — ular joyida qoladi, faqat sahifa tarkibi pastga
          suriladi. */}
      <main className="flex-1 min-w-0 relative pt-8">
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
        <BranchSwitcher />
        <RoleSwitcher />
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
              {user?.role !== STUDENT && user?.role !== PARENT && (
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    setShowUsernameModal(true);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <UserCog size={15} />
                  Loginni almashtirish
                </button>
              )}
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
              {/* TELEFONDA filial almashtirish: tepadagi tanlagich
                  keng ekran uchun (hidden sm:block), shuning uchun
                  ikki filialli xodim telefonda ham almashtira olsin
                  (2026-08-10). */}
              <MobileRolePicker onDone={() => setProfileOpen(false)} />
              <MobileBranchPicker onDone={() => setProfileOpen(false)} />
              <ProfileRolePicker />
              {/* JonyOS xodim ilovasi (2026-09-27) — telefon uchun, har
                  xodimga faqat o'z bo'limlari */}
              {user?.role !== "parent" && user?.role !== "student" && (
                <Link
                  to="/app"
                  onClick={() => setProfileOpen(false)}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <Smartphone size={15} />
                  JonyOS ilova (telefon)
                </Link>
              )}
              {(user?.role === "teacher" ||
                user?.role === "support_teacher") && (
                <Link
                  to="/teacher"
                  onClick={() => setProfileOpen(false)}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <Smartphone size={15} />
                  Telefon ko'rinishiga qaytish
                </Link>
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

      {/* MASHQ SEKUNDOMERI (2026-09-25, Jahongir: "har safar chiqib
          ketganda sekundomer o'chib qolyabdi") — mashq ketayotgan
          bo'lsa har qanday sahifada osilib turadi. */}
      <DrillTimer />

      {(showPasswordModal || forcePw) && (
        <ChangePasswordModal
          forced={forcePw && !showPasswordModal}
          onClose={() => {
            setShowPasswordModal(false);
            setForcePw(false);
            try {
              localStorage.removeItem("jony_must_change_pw");
            } catch { /* e'tiborsiz */ }
          }}
        />
      )}
      {showUsernameModal && (
        <ChangeUsernameModal onClose={() => setShowUsernameModal(false)} />
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
            <PasswordInput
              value={current}
              onChange={setCurrent}
              placeholder="Joriy parolingiz"
              autoComplete="current-password"
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
          placeholder="Ism yoki telefon raqami…"
          data-guide="topbar-search"
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
              <p className="text-sm text-slate-800">
                {s.name}
                {s.archived && (
                  <span className="ml-1.5 text-[10px] font-semibold bg-slate-200 text-slate-600 rounded px-1.5 py-0.5 align-middle">
                    arxiv
                  </span>
                )}
              </p>
              <p className="text-xs text-slate-400">
                {s.group || "guruhsiz"} · {s.status_label}
                {s.phone ? ` · ${formatPhone(s.phone)}` : ""}
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
          {/* XODIMLAR bo'limi olib tashlandi (2026-08-18, Jahongir:
              "qidiruvda xodimlar chiqmasin") — tepadagi qidiruv
              o'quvchi, lid, guruh va ustoz uchun. */}
          {res.students.length === 0 && res.leads.length === 0 &&
            (res.groups || []).length === 0 &&
            (res.teachers || []).length === 0 && (
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
  /** Arxivdagi o'quvchi — ro'yxatda belgilanadi (2026-08-13). */
  archived?: boolean;
  phone?: string | null;
};
type SearchRes = {
  students: SearchRow[]; leads: SearchRow[];
  groups?: { id: number; name: string }[];
  teachers?: { id: number; name: string }[];
  staff?: SearchRow[];
};


/** Profil menyusidagi lavozim tanlash — telefonda. */
function MobileRolePicker({ onDone }: { onDone: () => void }) {
  const { user } = useAuth();
  const myRoles = user?.roles ?? [];
  const current = getActiveRole() || user?.role || "";
  if (myRoles.length < 2) return null;
  return (
    <div className="lg:hidden border-t border-slate-100 px-4 py-2.5">
      <p className="text-[11px] text-slate-400 mb-1.5">Lavozim</p>
      <select
        value={current}
        onChange={(e) => {
          setActiveRole(e.target.value || null);
          onDone();
          window.location.href = "/";
        }}
        className="w-full rounded-lg border border-slate-200 px-2.5 py-2 text-sm bg-white"
      >
        {myRoles.map((r) => (
          <option key={r.key} value={r.key}>{r.label}</option>
        ))}
      </select>
    </div>
  );
}


/** LAVOZIM ALMASHTIRGICH (2026-08-10).
 *
 *  Jahongir: "bir xodim bir nechta lavozim qo'shsak bo'ladimi, filial
 *  almashtirgandek lavozimini almashtirib kiraverardi. Masalan HR
 *  managerimiz Support managerlik ishini ham qiladi; Nodir filial
 *  rahbari ham, ustoz ham."
 *
 *  Tanlangan lavozim BUTUN platformaga ta'sir qiladi: menyu, huquqlar
 *  va ko'rinadigan ma'lumot AYNAN o'sha lavozimniki bo'ladi (aralash
 *  emas). Shu sababli xodim bir vaqtda faqat bitta "rolda" ishlaydi —
 *  bu tasodifan ortiqcha ma'lumot ko'rinishining oldini oladi.
 *
 *  Faqat IKKI VA UNDAN KO'P lavozimi bor xodimga chiqadi. */
function RoleSwitcher() {
  const { user } = useAuth();
  const myRoles = user?.roles ?? [];
  const current = getActiveRole() || user?.role || "";

  if (myRoles.length < 2) return null;

  return (
    <div className="absolute top-4 right-[30.5rem] z-40 hidden lg:block">
      <select
        value={current}
        onChange={(e) => {
          setActiveRole(e.target.value || null);
          // Menyu va huquqlar butunlay o'zgaradi — to'liq qayta yuklash
          window.location.href = "/";
        }}
        title="Lavozim bo'yicha ishlash"
        className="h-10 rounded-full border border-brand-400 bg-brand-50 px-3 pr-7 text-sm text-brand-700 font-medium shadow-sm focus:outline-none max-w-[11rem] truncate"
      >
        {myRoles.map((r) => (
          <option key={r.key} value={r.key}>{r.label}</option>
        ))}
      </select>
    </div>
  );
}


/** Profil menyusidagi LAVOZIM tanlash (2026-08-12, Jahongir: "Nodir
 *  ham ustoz ham filial rahbari... Go'zal ham ustoz ham o'quv bo'limi
 *  rahbari — lavozim almashtirish funksiyasi qo'shilsin profil
 *  bo'limida"). Ikki va undan ko'p lavozimli xodimga chiqadi. */
function ProfileRolePicker() {
  const { user } = useAuth();
  const myRoles = user?.roles ?? [];
  const picked = getActiveRole();
  const current = picked || user?.role || "";
  // 2026-08-25, Jahongir: "ustoz lavozimiga otsa manager lavozimi
  // yoqolib qolibdi kira olmayabdi ekan". Endi tanlangan lavozim
  // ro'yxatda bo'lmasa ham u qo'shiladi va tanlagich lavozim
  // tanlangan bo'lsa HAR DOIM ko'rinadi — xodim qamalib qolmaydi.
  const opts = [...myRoles];
  if (current && !opts.some((r) => r.key === current))
    opts.push({ key: current, label: current });
  if (opts.length < 2 && !picked) return null;
  return (
    <div className="border-t border-slate-100 px-4 py-2.5">
      <p className="text-[11px] text-slate-400 mb-1.5">Lavozim</p>
      <select
        value={current}
        onChange={(e) => {
          setActiveRole(e.target.value || null);
          window.location.href = "/";
        }}
        className="w-full rounded-lg border border-slate-200 px-2.5 py-2 text-sm bg-white"
      >
        {opts.map((r) => (
          <option key={r.key} value={r.key}>{r.label}</option>
        ))}
      </select>
      {picked && picked !== user?.role && (
        <button
          onClick={() => {
            setActiveRole(null);
            window.location.href = "/";
          }}
          className="mt-1.5 text-[11px] text-brand-600 font-medium"
        >
          Asosiy lavozimga qaytish
        </button>
      )}
    </div>
  );
}


/** Profil menyusidagi filial tanlash — FAQAT telefonda ko'rinadi
 *  (keng ekranda tepadagi BranchSwitcher bor). Ikki va undan ko'p
 *  filialda ishlaydigan xodimga chiqadi. */
function MobileBranchPicker({ onDone }: { onDone: () => void }) {
  const { user } = useAuth();
  const [all, setAll] = useState<{ id: number; name: string }[]>([]);
  const mine = user?.branches ?? [];
  // Xodimga biriktirilgan filiallar bo'lsa - faqat o'shalari
  // (Jahongir, 2026-08-11); asoschiga hammasi
  const restricted = !can(user?.role, ALL_BRANCH_ROLES) && mine.length >= 1;
  const orgWide = !restricted && can(user?.role, BRANCH_SWITCH);
  const current = getGlobalBranch();

  useEffect(() => {
    if (!orgWide) return;
    api.get<{ id: number; name: string }[]>("/branches")
      .then(setAll)
      .catch(() => {});
  }, [orgWide]);

  const branches = orgWide ? all : mine;
  if (branches.length < 2) return null;

  return (
    <div className="sm:hidden border-t border-slate-100 px-4 py-2.5">
      <p className="text-[11px] text-slate-400 mb-1.5">Filial</p>
      <select
        value={current || ""}
        onChange={(e) => {
          setGlobalBranch(e.target.value || null);
          onDone();
          window.location.reload();
        }}
        className="w-full rounded-lg border border-slate-200 px-2.5 py-2 text-sm bg-white"
      >
        {!restricted && <option value="">Barcha filiallar</option>}
        {branches.map((b) => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </select>
    </div>
  );
}


/** FILIAL ALMASHTIRGICH. Tanlangan filial BUTUN platformaga ta'sir
 *  qiladi: har bir sahifa faqat shu filial ma'lumotini ko'rsatadi.
 *  "Barcha filiallar" — umumiy ko'rinish.
 *
 *  IKKI XIL foydalanuvchiga chiqadi:
 *   1. Rahbariyat (BRANCH_SWITCH) — BARCHA filiallar ro'yxati bilan;
 *   2. IKKI YOKI UNDAN KO'P filialda ishlaydigan xodim — masalan ikki
 *      filialda dars beradigan ustoz yoki guruhlari turli filialda
 *      bo'lgan SUPPORT TEACHER — faqat O'Z filiallari bilan.
 *
 *  (2) 2026-08-10 da qo'shildi (Jahongir: "supportlarda agar guruhi
 *  bir nechta filialda bo'lsa, filial almashtirish bo'lsin — tepada
 *  o'ng tomonda boshqa xodimlarga o'xshab"). Bitta filialli xodimga
 *  hamon chiqmaydi — unga tanlov ko'rsatish chalg'itadi. */
function BranchSwitcher() {
  const { user } = useAuth();
  const [all, setAll] = useState<{ id: number; name: string }[]>([]);
  const current = getGlobalBranch();
  // 2026-08-11 (Jahongir): xodimga filial biriktirilgan bo'lsa,
  // tanlagichda FAQAT o'sha filiallar chiqadi - u kira olmaydigan
  // filiallar ko'rinmaydi. "Barcha filiallar" ham chiqmaydi.
  // Faqat asoschi (yoki filial biriktirilmagan rahbariyat) butun
  // ro'yxatni ko'radi.
  const mine = user?.branches ?? [];
  const restricted = !can(user?.role, ALL_BRANCH_ROLES) && mine.length >= 1;
  const orgWide = !restricted && can(user?.role, BRANCH_SWITCH);

  useEffect(() => {
    // To'liq ro'yxat faqat rahbariyatga kerak — qolganlarga o'z
    // filiallari /api/me dan allaqachon keladi.
    if (!orgWide) return;
    api.get<{ id: number; name: string }[]>("/branches")
      .then(setAll)
      .catch(() => {});
  }, [orgWide]);

  // Cheklangan xodim "Barcha filiallar" holatida qolib ketmasin -
  // avtomatik o'z (asosiy) filialiga o'tkaziladi
  useEffect(() => {
    if (!restricted || mine.length === 0) return;
    const cur = getGlobalBranch();
    if (!cur || !mine.some((b) => String(b.id) === String(cur))) {
      setGlobalBranch(String(mine[0].id));
      window.location.reload();
    }
  }, [restricted, mine.length]);

  const branches = orgWide ? all : mine;

  if (branches.length < 2) return null;

  // "Vazifalar" tugmasi bor rollarda u right-[16.5rem] da turadi,
  // yo'q rollarda esa o'sha joy bo'sh qoladi — almashtirgich o'shanga
  // qarab suriladi, aks holda o'rtada bo'sh oraliq ko'rinardi.
  const right = can(user?.role, TASK_ACCESS)
    ? "sm:right-[19.5rem]"
    : "sm:right-[16.5rem]";

  return (
    <div className={`absolute top-4 ${right} z-40 hidden sm:block`}>
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
        {!restricted && <option value="">Barcha filiallar</option>}
        {branches.map((b) => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </select>
    </div>
  );
}
