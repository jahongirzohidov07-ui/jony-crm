import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../lib/AuthContext";
import { api, getActiveRole, getGlobalBranch, setActiveRole, setGlobalBranch } from "../../lib/api";
import { ALL_BRANCH_ROLES, BRANCH_SWITCH, can, roleLabel } from "../../lib/roles";
import { initials } from "./AppHome";
import { Gem } from "./Gem";

/**
 * PROFIL — lavozim va filial almashtirish, parol, chiqish (2026-09-27).
 * Qoidalar paneldagi profil menyusi bilan bir xil (ProfileRolePicker,
 * MobileBranchPicker): biriktirilgan filialli xodim faqat o'z
 * filiallarini tanlaydi, "Barcha filiallar" unga chiqmaydi.
 */
export default function AppProfile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [all, setAll] = useState<{ id: number; name: string }[]>([]);
  const mine = user?.branches ?? [];
  const restricted = !can(user?.role, ALL_BRANCH_ROLES) && mine.length >= 1;
  const orgWide = !restricted && can(user?.role, BRANCH_SWITCH);
  useEffect(() => {
    if (!orgWide) return;
    api.get<{ id: number; name: string }[]>("/branches").then(setAll).catch(() => {});
  }, [orgWide]);
  const branches = orgWide ? all : mine;
  const curBranch = getGlobalBranch();

  const picked = getActiveRole();
  const curRole = picked || user?.role || "";
  const roles = [...(user?.roles ?? [])];
  if (curRole && !roles.some((r) => r.key === curRole)) roles.push({ key: curRole, label: roleLabel(curRole) });

  const isTeacher = user?.role === "teacher" || user?.role === "support_teacher";

  return (
    <div className="jos-page">
      <div className="jos-hero t3" style={{ textAlign: "center", paddingTop: 24 }}>
        <div className="jos-ava" style={{ width: 72, height: 72, borderRadius: 24, fontSize: 24, margin: "0 auto",
                                          background: "linear-gradient(135deg,#FF8A00,#FF3B5C)", position: "relative" }}>
          {initials(user?.full_name || "")}
        </div>
        <div className="big" style={{ fontSize: 20, marginTop: 12 }}>{user?.full_name}</div>
        <div className="s">{roleLabel(user?.role || "")}</div>
      </div>

      {roles.length >= 2 && (
        <>
          <div className="jos-sect"><b>Lavozim</b></div>
          <div className="jos-chips" style={{ flexWrap: "wrap" }}>
            {roles.map((r) => (
              <button key={r.key} className={`jos-chip ${r.key === curRole ? "on" : ""}`}
                      onClick={() => { if (r.key === curRole) return; setActiveRole(r.key === user?.role && !picked ? null : r.key); window.location.href = "/app"; }}>
                {r.label}
              </button>
            ))}
          </div>
          {picked && picked !== user?.role && (
            <button className="jos-btn o" style={{ marginTop: 6 }}
                    onClick={() => { setActiveRole(null); window.location.href = "/app"; }}>
              Asosiy lavozimga qaytish
            </button>
          )}
        </>
      )}

      {branches.length >= 2 && (
        <>
          <div className="jos-sect"><b>Filial</b></div>
          <div className="jos-chips" style={{ flexWrap: "wrap" }}>
            {!restricted && (
              <button className={`jos-chip ${!curBranch ? "on" : ""}`}
                      onClick={() => { setGlobalBranch(null); window.location.reload(); }}>
                Barcha filiallar
              </button>
            )}
            {branches.map((b) => (
              <button key={b.id} className={`jos-chip ${String(b.id) === String(curBranch) ? "on" : ""}`}
                      onClick={() => { setGlobalBranch(String(b.id)); window.location.reload(); }}>
                {b.name}
              </button>
            ))}
          </div>
        </>
      )}

      <div className="jos-sect"><b>Sozlamalar</b></div>
      <div className="jos-list">
        <Link to="/app/p/profile" className="jos-it"><Gem name="lock" size={38} />
          <div className="m"><b>Shaxsiy ma'lumotlar va parol</b><small>Login, parol, Telegram</small></div></Link>
        {isTeacher && (
          <Link to="/teacher" className="jos-it"><Gem name="check" size={38} />
            <div className="m"><b>Jony Teacher</b><small>Yo'qlama va bugungi darslar</small></div></Link>
        )}
        <a href="/" className="jos-it"><Gem name="open" size={38} />
          <div className="m"><b>To'liq panel (kompyuter ko'rinishi)</b><small>Barcha jadval va hisobotlar</small></div></a>
        <button className="jos-it" onClick={() => { logout(); navigate("/login", { replace: true }); }}>
          <Gem name="logout" size={38} />
          <div className="m"><b>Chiqish</b><small>Hisobdan chiqish</small></div>
        </button>
      </div>
      <p style={{ textAlign: "center", color: "#8B89A6", fontSize: 11, marginTop: 18, fontWeight: 700 }}>JonyOS · Jony Academy</p>
    </div>
  );
}
