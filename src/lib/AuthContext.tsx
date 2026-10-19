import {
  createContext, useContext, useEffect, useState, type ReactNode,
} from "react";
import { api, getToken, setToken, clearToken, setActiveRole, setGlobalBranch } from "./api";
import { setPartnerHead } from "./roles";

export interface AuthBranch {
  id: number;
  name: string;
}

export interface AuthRole {
  key: string;
  label: string;
}

interface AuthUser {
  full_name: string;
  role: string;
  branch_id: number | null;
  /** Xodim ishlaydigan BARCHA filiallar (asosiy + qo'shimcha).
   * Ikkitadan ko'p bo'lsa tepada filial tanlagich chiqadi. */
  branches?: AuthBranch[];
  /** Xodim bajaradigan BARCHA lavozimlar (asosiy + qo'shimcha).
   * Ikkitadan ko'p bo'lsa tepada lavozim tanlagich chiqadi. */
  roles?: AuthRole[];
  /** Volontyor support/examiner - "Mening oyligim" ko'rinmaydi. */
  salary_hidden?: boolean;
  /** Hamkor markaz (Stech) rahbari — o'z markazida asoschi kabi. */
  partner_head?: boolean;
  /** Dars rejalari / jonli o'yin — faqat ingliz tili ustozlariga (2026-09-18). */
  english_teacher?: boolean;
  /** Kuzatuvchi (2026-10-19) — faqat ko'rish, server yozishni yopadi. */
  read_only?: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  login: (
    username: string,
    password: string,
    remember?: boolean,
  ) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    // Eslab qolish yoqilgan bo'lsa foydalanuvchi localStorage'da
    // turadi - ilova qayta ochilganda ham darhol ichkarida bo'ladi.
    try {
      if (!getToken()) return null;
      const saved = sessionStorage.getItem("jony_crm_user") ?? localStorage.getItem("jony_crm_user");
      const parsed = saved ? JSON.parse(saved) : null;
      return parsed && typeof parsed.role === "string" && typeof parsed.full_name === "string" ? parsed : null;
    } catch { return null; }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // can() shu belgiga qaraydi — render paytida sinxron o'rnatiladi,
  // shunda birinchi chizishdayoq tugmalar to'g'ri chiqadi.
  setPartnerHead(!!user?.partner_head);

  // Keshdagi ism/rol eskirib qolmasin: har ochilishda serverdan
  // yangilab olamiz (masalan, ism serverda o'zgartirilgan bo'lsa).
  //
  // MUHIM (2026-08-11, Jahongir: "2 filialli xodim filialdan
  // filialga o'ta olmayapti"): bu so'rov avval FAQAT ilova birinchi
  // ochilganda ketardi. Login qilingan zahoti esa foydalanuvchida
  // branches/roles ro'yxati BO'LMASDI - natijada filial va lavozim
  // tanlagichlari sahifa qo'lda yangilanmaguncha umuman chiqmasdi
  // (PWA/APK da hech kim yangilamaydi). Endi refreshMe() login
  // tugashi bilan ham chaqiriladi.
  const refreshMe = () => {
    if (!getToken()) return;
    api
      .get<{
        full_name: string;
        role: string;
        branch_id: number | null;
        branches?: AuthBranch[];
        roles?: AuthRole[];
        salary_hidden?: boolean;
        partner_head?: boolean;
        english_teacher?: boolean;
        read_only?: boolean;
      }>("/me")
      .then((r) => {
        const u = {
          full_name: r.full_name,
          role: r.role,
          branch_id: r.branch_id,
          branches: r.branches ?? [],
          roles: r.roles ?? [],
          salary_hidden: r.salary_hidden ?? false,
          partner_head: r.partner_head ?? false,
          english_teacher: r.english_teacher ?? true,
          read_only: r.read_only ?? false,
        };
        // Qaysi omborda saqlangan bo'lsa, o'shani yangilaymiz
        (localStorage.getItem("jony_crm_user")
          ? localStorage
          : sessionStorage
        ).setItem("jony_crm_user", JSON.stringify(u));
        setUser((prev) =>
          prev &&
          prev.full_name === u.full_name &&
          prev.role === u.role &&
          prev.branch_id === u.branch_id &&
          (prev.branches?.length ?? 0) === u.branches.length &&
          (prev.roles?.length ?? 0) === u.roles.length &&
          (prev.salary_hidden ?? false) === u.salary_hidden &&
          (prev.partner_head ?? false) === u.partner_head &&
          (prev.english_teacher ?? true) === u.english_teacher &&
          (prev.read_only ?? false) === u.read_only
            ? prev
            : u,
        );
      })
      .catch(() => {});
  };

  useEffect(refreshMe, []);

  async function login(
    username: string,
    password: string,
    remember = false,
  ) {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<{
        access_token: string;
        role: string;
        full_name: string;
        branch_id: number | null;
        must_change_password?: boolean;
      }>("/auth/login", { username, password, remember });
      // STANDART PAROL — MAJBURIY ALMASHTIRISH (2026-09-06 xavfsizlik
      // auditi): login = telefon raqami, parol esa hisob ochilganda
      // "jonyjony". Almashtirilmagan bo'lsa ilova birinchi ekranda
      // so'raydi (Layout.tsx dagi parol oynasi ochiladi).
      try {
        if (res.must_change_password) {
          localStorage.setItem("jony_must_change_pw", "1");
        } else {
          localStorage.removeItem("jony_must_change_pw");
        }
      } catch { /* localStorage yopiq bo'lsa — e'tiborsiz */ }
      setActiveRole(null);
      setGlobalBranch(null);
      setToken(res.access_token, remember);
      const u = { full_name: res.full_name, role: res.role, branch_id: res.branch_id };
      sessionStorage.removeItem("jony_crm_user");
      localStorage.removeItem("jony_crm_user");
      (remember ? localStorage : sessionStorage).setItem(
        "jony_crm_user",
        JSON.stringify(u),
      );
      // Filial/lavozim tanlagichlari darhol chiqishi uchun to'liq
      // profilni fon rejimida yuklaymiz (kutmaymiz - yo'naltirish
      // login javobidagi rol bilan ketaveradi)
      setTimeout(refreshMe, 0);
      setUser(u);
      // Kirgan odamning roli qaytariladi — chaqirgan joy (Login.tsx)
      // qayerga yo'naltirishni shundan biladi (o'quvchi -> /student).
      return u;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik yuz berdi");
      throw e;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearToken();
    setActiveRole(null);
    setGlobalBranch(null);
    sessionStorage.removeItem("jony_crm_user");
    localStorage.removeItem("jony_crm_user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function isAuthed() {
  return !!getToken();
}
