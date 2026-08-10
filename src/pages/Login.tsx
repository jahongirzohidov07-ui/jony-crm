import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { BrandLockup } from "../components/BrandIcon";
import { useAuth } from "../lib/AuthContext";
import { api } from "../lib/api";

export default function Login() {
  const { login, loading, error } = useAuth();
  const [username, setUsername] = useState(
    () => localStorage.getItem("jonyos_last_login") || "",
  );
  const [password, setPassword] = useState("");
  // ESLAB QOLISH (2026-08-10, Jahongir): belgi qo'yilsa 60 kunlik
  // sessiya + login maydoni keyingi safar o'zi to'lgan bo'ladi.
  // Odatiy holatda YOQIQ - o'quvchilar har safar qayta kirib
  // o'tirmasin.
  const [remember, setRemember] = useState(true);
  // Ko'z belgisi: bosilsa parol ochiq ko'rinadi (telefonda xato yozmaslik uchun)
  const [showPw, setShowPw] = useState(false);
  const [recovery, setRecovery] = useState(false);
  const navigate = useNavigate();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const u = await login(username, password, remember);
      if (remember) localStorage.setItem("jonyos_last_login", username);
      else localStorage.removeItem("jonyos_last_login");
      if (password === "jonyjony") {
        alert(
          "Siz standart parol bilan kirdingiz.\\n\\nXavfsizlik uchun " +
            "parolni o'zgartirib olishni tavsiya qilamiz: " +
            "Profil → Parolni o'zgartirish."
        );
      }
      // Har kim O'Z ilovasiga tushadi: o'quvchi -> Jony Student,
      // ustoz/support -> Jony Teacher (telefonda yo'qlama uchun),
      // qolganlar -> xodimlar paneli. Ustoz xohlasa Profil'dagi
      // "To'liq panelga o'tish" orqali eski ko'rinishga o'tadi.
      const dest =
        u?.role === "student"
          ? "/student"
          : u?.role === "teacher" || u?.role === "support_teacher"
            ? "/teacher"
            : "/";
      navigate(dest, { replace: true });
    } catch {
      // error is surfaced via context
    }
  }

  if (recovery) return <RecoverForm onBack={() => setRecovery(false)} />;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-8">
        <div className="flex flex-col items-center mb-6">
          <BrandLockup iconSize={56} className="mb-3" />
          <p className="text-sm text-slate-500">JonyOS &middot; Boshqaruv paneliga kirish</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Login
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Parol
            </label>
            <div className="relative">
              <input
                type={showPw ? "text" : "password"}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                tabIndex={-1}
                onClick={() => setShowPw((v) => !v)}
                title={showPw ? "Parolni yashirish" : "Parolni ko'rish"}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="w-4 h-4 rounded border-slate-300 accent-brand-600"
            />
            <span className="text-sm text-slate-600">
              Meni eslab qol (60 kun qayta kirish shart emas)
            </span>
          </label>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium transition disabled:opacity-60"
          >
            {loading ? "Kirilmoqda..." : "Kirish"}
          </button>
          <button
            type="button"
            onClick={() => setRecovery(true)}
            className="w-full text-center text-xs text-slate-400 hover:text-slate-600"
          >
            Parolni unutdingizmi? (asoschi uchun)
          </button>
        </form>
      </div>
    </div>
  );
}

/** Asoschi parolni unutsa: profilda oldindan o'rnatgan tiklash kodi
 *  bilan yangi parol qo'yadi. Kod bo'lmasa — bu yo'l yopiq. */
function RecoverForm({ onBack }: { onBack: () => void }) {
  const [username, setUsername] = useState("");
  const [code, setCode] = useState("");
  const [next, setNext] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (next.length < 8 || !/[a-zA-Z]/.test(next) || !/\d/.test(next)) {
      setErr("Parol kamida 8 belgi bo'lib, ichida harf ham, raqam ham bo'lsin");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await api.post("/auth/recover", {
        username, recovery_code: code, new_password: next,
      });
      setOk(true);
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-lg font-semibold text-slate-900 mb-1">
          Parolni tiklash
        </h1>
        <p className="text-xs text-slate-500 mb-5">
          Bu yo'l faqat asoschi hisobi uchun. Profilda oldindan
          o'rnatilgan tiklash kodi kerak bo'ladi.
        </p>
        {ok ? (
          <div className="space-y-4">
            <p className="text-sm text-green-700 bg-green-50 rounded-lg px-3 py-2">
              Yangi parol o'rnatildi. Endi kirishingiz mumkin.
            </p>
            <button onClick={onBack}
              className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium">
              Kirish oynasiga qaytish
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <input
              placeholder="Login"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <input
              placeholder="Tiklash kodi"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Yangi parol"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              required
            />
            {err && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                {err}
              </p>
            )}
            <button type="submit" disabled={busy}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60">
              {busy ? "Tekshirilmoqda..." : "Yangi parol o'rnatish"}
            </button>
            <button type="button" onClick={onBack}
              className="w-full text-center text-xs text-slate-400 hover:text-slate-600">
              ← Orqaga
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
