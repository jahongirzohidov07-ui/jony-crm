import { createContext, useContext, useState, type ReactNode } from "react";
import { api, getToken, setToken, clearToken } from "./api";

interface AuthUser {
  full_name: string;
  role: string;
  branch_id: number | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = sessionStorage.getItem("jony_crm_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function login(username: string, password: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<{
        access_token: string;
        role: string;
        full_name: string;
        branch_id: number | null;
      }>("/auth/login", { username, password });
      setToken(res.access_token);
      const u = { full_name: res.full_name, role: res.role, branch_id: res.branch_id };
      sessionStorage.setItem("jony_crm_user", JSON.stringify(u));
      setUser(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik yuz berdi");
      throw e;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearToken();
    sessionStorage.removeItem("jony_crm_user");
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
