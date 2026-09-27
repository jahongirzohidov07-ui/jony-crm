import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../lib/AuthContext";
import { api, getGlobalBranch, type Branch } from "../../lib/api";
import { can, TASK_ACCESS } from "../../lib/roles";
import { buildNav, type NavItem } from "../../components/navItems";
import { buildTabs, isPanelPath, appHref, type AppTab } from "./appNav";
import { Gem, Glyph } from "./Gem";
import "./app.css";

interface AppCtxValue {
  nav: NavItem[];
  tabs: AppTab[];
  fab: AppTab | null;
}
const AppCtx = createContext<AppCtxValue>({ nav: [], tabs: [], fab: null });
export const useApp = () => useContext(AppCtx);

/**
 * JonyOS — XODIM ILOVASI QOBIG'I (2026-09-27).
 *
 * Jahongir: "Staff uchun JonyOS programmasini yaratmasligimiz kerak
 * ... har bir xodim uchun alohida o'zigagina tegishli funksiyalari
 * ochilishi kerak ... dizaynni juda ham mukammal qilishing kerak".
 *
 * - Kim qaysi bo'limni ko'radi — buildNav() (xodimlar paneli bilan
 *   bitta manba). Backend ham har so'rovda ruxsatni o'zi tekshiradi.
 * - Bosh sahifa, Vazifalar, Bo'limlar va Profil — telefon uchun yangi.
 * - Qolgan bo'limlar (moliya, lidlar, HR...) qayta yozilmadi: ular
 *   ilova ichida (/app/p/...) o'z sarlavhasi bilan ochiladi.
 */
export default function AppLayout() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();

  // Sinov filiali — "Mashq" bandi faqat shunda (paneldagi bilan bir xil)
  const [testBranches, setTestBranches] = useState<number[]>([]);
  useEffect(() => {
    let alive = true;
    api.get<Branch[]>("/branches")
      .then((bs) => { if (alive) setTestBranches(bs.filter((b) => b.is_test).map((b) => b.id)); })
      .catch(() => { if (alive) setTestBranches([]); });
    return () => { alive = false; };
  }, []);
  const cur = getGlobalBranch();
  const onTestBranch = !!cur && testBranches.includes(Number(cur));

  // PWA nomi, rangi va shriftlar — faqat ilova ochiq turganda
  useEffect(() => {
    const made: HTMLElement[] = [];
    let link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = "manifest";
      document.head.appendChild(link);
      made.push(link);
    }
    const prevHref = link.href;
    link.href = "/jonyos.webmanifest";
    const font = document.createElement("link");
    font.rel = "stylesheet";
    font.href = "https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Unbounded:wght@600;700&display=swap";
    document.head.appendChild(font);
    made.push(font);
    const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
    const prevColor = meta?.content;
    if (meta) meta.content = "#FDF8FF";
    const prevTitle = document.title;
    document.title = "JonyOS";
    return () => {
      made.forEach((n) => n.parentNode?.removeChild(n));
      if (link && !made.includes(link)) link.href = prevHref;
      if (meta && prevColor) meta.content = prevColor;
      document.title = prevTitle;
    };
  }, []);

  const value = useMemo<AppCtxValue>(() => {
    const nav = buildNav(user, { onTestBranch });
    const { tabs, fab } = buildTabs(user?.role || "", nav, can(user?.role, TASK_ACCESS));
    return { nav, tabs, fab };
  }, [user, onTestBranch]);

  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "student") return <Navigate to="/student" replace />;
  if (user.role === "parent") return <Navigate to="/" replace />;

  const embedded = pathname.startsWith("/app/p");

  // Ilova ichida ochilgan panel sahifasidagi havolalar ilovadan
  // chiqib ketmasin: "/students/5" → "/app/p/students/5".
  function onClickCapture(e: React.MouseEvent) {
    if (!embedded || e.defaultPrevented || e.button !== 0 ||
        e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = (e.target as HTMLElement).closest("a");
    if (!a || (a.target && a.target !== "_self") || a.hasAttribute("download")) return;
    const href = a.getAttribute("href") || "";
    if (!isPanelPath(href)) return;
    e.preventDefault();
    navigate(appHref(href));
  }

  return (
    <AppCtx.Provider value={value}>
      <div className="jos" onClickCapture={onClickCapture}>
        <Outlet />
        <nav className="jos-tabs" aria-label="Asosiy menyu">
          {value.tabs.slice(0, 2).map((t) => <Tab key={t.to} t={t} />)}
          {value.fab && (
            <NavLink to={value.fab.to} className="jos-fab" aria-label={value.fab.label}>
              <Glyph name={value.fab.gem} size={27} />
              <small>{value.fab.label}</small>
            </NavLink>
          )}
          {value.tabs.slice(2).map((t) => <Tab key={t.to} t={t} />)}
        </nav>
      </div>
    </AppCtx.Provider>
  );
}

function Tab({ t }: { t: AppTab }) {
  return (
    <NavLink to={t.to} end={t.end} className={({ isActive }) => `jos-tab ${isActive ? "on" : ""}`}>
      {({ isActive }) => (
        <>
          {isActive ? <Gem name={t.gem} size={34} /> : <Glyph name={t.gem} size={24} />}
          {t.label}
        </>
      )}
    </NavLink>
  );
}
