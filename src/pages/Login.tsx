import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";
import { BrandIcon, BrandLockup } from "../components/BrandIcon";
import { useAuth } from "../lib/AuthContext";
import { api } from "../lib/api";
import { PasswordInput } from "../components/PasswordInput";
import { isStudentApp } from "../lib/appMode";

export default function Login() {
  const { login, loading, error, logout } = useAuth();
  const [appBlock, setAppBlock] = useState("");
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
      // JONY STUDENT ILOVASI FAQAT O'QUVCHILAR UCHUN (2026-08-18,
      // Jahongir: "jony student appdan faqat studentlar kira olsin
      // xodimlar ham akkauntlariga kirib ketyabdi undan"). Xodim
      // hisobi bu ilovadan kiritilmaydi — sessiya darhol yopiladi.
      // Xodimlar jonyos.uz saytining o'zidan kiradi (u yerda hech
      // narsa o'zgarmagan).
      if (isStudentApp() && u && u.role !== "student") {
        logout();
        setAppBlock(
          "Bu ilova faqat o'quvchilar uchun. Xodimlar jonyos.uz " +
          "saytidan (brauzer orqali) kiradi."
        );
        return;
      }
      setAppBlock("");
      if (remember) localStorage.setItem("jonyos_last_login", username);
      else localStorage.removeItem("jonyos_last_login");
      if (password === "jonyjony") {
        alert(
          "Siz standart parol bilan kirdingiz.\n\n" +
            (u?.role === "student"
              ? "Parolni o'zgartirish uchun o'quv markazi administratoriga murojaat qiling."
              : "Xavfsizlik uchun Profil → Parolni o'zgartirish bo'limida parolni yangilang.")
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

  // JONY STUDENT ILOVASI UCHUN ALOHIDA KIRISH EKRANI (2026-08-20,
  // Jahongir: "Jony Student appning dizaynini toliq tashladim
  // papkada 1ga 1 qilib ber" - "kirish.png"). Faqat app rejimida
  // (?pwa=1 orqali ochilganda) ko'rinadi; xodimlar jonyos.uz'dan
  // kirganda eski oq oyna o'zgarmagan.
  if (isStudentApp()) {
    return (
      <div className="min-h-screen px-4 py-10 flex flex-col justify-center"
           style={{ background:
             "radial-gradient(120% 90% at 50% 0%,#1B3FA8 0%,#122a80 40%,#0A1550 75%,#070E38 100%)" }}>
        <div className="w-full max-w-sm mx-auto">
          <div className="flex items-center justify-center gap-3">
            <BrandIcon size={64} />
            <div className="leading-none">
              <p className="text-[30px] font-extrabold text-white">JONY</p>
              <p className="text-[30px] font-extrabold text-white">
                STUDENT APP
              </p>
            </div>
          </div>
          <p className="text-center text-[16px] text-white/85 mt-5 leading-relaxed px-2">
            O'qishingiz, natijalaringiz va mukofotlaringiz — barchasi bir
            joyda.
          </p>

          <form onSubmit={onSubmit}
                className="mt-7 bg-white/95 rounded-3xl p-5 shadow-[0_0_60px_rgba(43,80,224,0.55)] space-y-4">
            <div>
              <label className="block text-[17px] font-bold text-slate-900 mb-2">
                Login
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-brand-600">
                  <UserRound size={20} />
                </span>
                <input
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 pl-11 pr-3 py-3.5 text-[15px] focus:outline-none focus:ring-2 focus:ring-brand-400"
                  placeholder="Telefon raqamingiz"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-[17px] font-bold text-slate-900 mb-2">
                Parol
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-brand-600">
                  <LockKeyhole size={20} />
                </span>
                <input
                  type={showPw ? "text" : "password"}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 pl-11 pr-11 py-3.5 text-[15px] focus:outline-none focus:ring-2 focus:ring-brand-400"
                  placeholder="Parolingizni kiriting"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button type="button" tabIndex={-1}
                        onClick={() => setShowPw((v) => !v)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                  {showPw ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox" checked={remember}
                       onChange={(e) => setRemember(e.target.checked)}
                       className="w-5 h-5 rounded accent-brand-600" />
                <span className="text-sm font-medium text-slate-700">
                  Meni eslab qol
                </span>
              </label>
              <button type="button"
                onClick={() => alert(
                  "Parolni administrator yangilab beradi — filialingizga murojaat qiling.")}
                className="text-sm font-semibold text-brand-600">
                Parolni unutdingizmi?
              </button>
            </div>

            {appBlock && (
              <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                {appBlock}
              </p>
            )}
            {error && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-2xl py-4 text-[18px] font-bold transition disabled:opacity-60">
              {loading ? "Kirilmoqda..." : "Kirish"}
            </button>
          </form>

          <p className="text-center text-[15px] text-white mt-6 flex items-center justify-center gap-2">
            <ShieldCheck size={18} className="text-sky-300" />
            Ma'lumotlaringiz xavfsiz himoyalangan
          </p>
          <p className="text-center text-sm text-white/60 mt-4">
            Yordam kerakmi?{" "}
            <span className="text-sky-300 font-medium">
              Administrator bilan bog'laning
            </span>
          </p>
        </div>
      </div>
    );
  }

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

          {appBlock && (
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              {appBlock}
            </p>
          )}
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
            <PasswordInput
              value={next}
              onChange={setNext}
              placeholder="Yangi parol"
              autoComplete="new-password"
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
