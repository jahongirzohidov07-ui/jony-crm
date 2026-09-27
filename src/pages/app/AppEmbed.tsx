import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useApp } from "./AppLayout";
import { Glyph } from "./Gem";

/**
 * PANEL BO'LIMI ILOVA ICHIDA (2026-09-27). Moliya, lidlar, HR kabi
 * murakkab sahifalar qayta yozilmadi — xuddi o'sha sahifa ilova
 * sarlavhasi va pastki menyusi bilan ochiladi. Ruxsatni sahifaning o'zi
 * va server tekshiradi (panel bilan bir xil).
 */
export default function AppEmbed() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { nav } = useApp();
  const path = pathname.replace(/^\/app\/p/, "") || "/";
  const item = [...nav].sort((a, b) => b.to.length - a.to.length)
    .find((i) => i.to !== "/" && (path === i.to || path.startsWith(i.to + "/")));
  const title = item?.label || (path.startsWith("/tasks") ? "Vazifalar" : path.startsWith("/profile") ? "Profil" : "JonyOS");

  function back() {
    if (window.history.length > 1) navigate(-1);
    else navigate("/app");
  }

  return (
    <div className="jos-embed">
      <div className="jos-top">
        <button className="jos-iconbtn" onClick={back} aria-label="Orqaga"><Glyph name="back" size={20} /></button>
        <b>{title}</b>
        <button className="jos-iconbtn" onClick={() => navigate("/app")} aria-label="Bosh sahifa"><Glyph name="home" size={19} /></button>
      </div>
      <Outlet />
    </div>
  );
}
