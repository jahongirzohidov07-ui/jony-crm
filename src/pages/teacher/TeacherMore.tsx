import { Link } from "react-router-dom";
import {
  BookMarked, CalendarDays, ChevronRight, ClipboardCheck, ClipboardList,
  Layers, MessageSquareWarning, PieChart, Timer, TrendingUp, Trophy, Wallet,
  Users,
} from "lucide-react";
import { useAuth } from "../../lib/AuthContext";
import { setActiveRole, getActiveRole } from "../../lib/api";

/**
 * JONY TEACHER — "Bo'limlar".
 *
 * Jahongir: "ularda bor barcha funksiyalar chiqsin." Bu sahifa aynan
 * shuning uchun: ustozning xodimlar panelidagi HAMMA bo'limi shu
 * yerdan ochiladi.
 *
 * MUHIM QAROR: bu sahifalar QAYTA YOZILMADI. Ular allaqachon
 * ishlaydi, sinovdan o'tgan va murakkab (oylik hisobi, imtihon
 * buyurtmasi va h.k.). Ularni telefon uchun qaytadan yozish —
 * xatolar kiritishning eng qisqa yo'li bo'lardi. Shuning uchun
 * ilova KUNLIK ish (yo'qlama, jadval) uchun maxsus qurildi, qolgani
 * esa mavjud sahifalarga olib boradi.
 */
const SECTIONS = [
  {
    title: "Kundalik ish",
    items: [
      { to: "/my-groups", label: "Guruhlarim", icon: Layers,
        hint: "Davomat, baholash, imtihonlar" },
      { to: "/my-students", label: "O'quvchilarim", icon: Users,
        hint: "Barcha o'quvchilaringiz ro'yxati" },
      { to: "/my-schedule", label: "Dars jadvalim", icon: CalendarDays,
        hint: "To'liq jadval va ko'chirishlar" },
      { to: "/timetable", label: "Umumiy jadval", icon: ClipboardList,
        hint: "Markazning dars jadvali" },
    ],
  },
  {
    title: "Buyurtmalar",
    items: [
      { to: "/my-books", label: "Kitob buyurtma", icon: BookMarked,
        hint: "O'quvchilaringiz uchun kitob" },
      { to: "/my-exams", label: "Imtihon buyurtma", icon: ClipboardCheck,
        hint: "Unit / mock test so'rash" },
      { to: "/teacher/vocab", label: "Lug'at unitlari", icon: BookMarked,
        hint: "Unit topshirganini tasdiqlash (100%)" },
    ],
  },
  {
    title: "Natijalar va oylik",
    items: [
      { to: "/teacher/session", label: "Soat belgilash", icon: Timer,
        hint: "Support seanslarini yozish", supportOnly: true },
      { to: "/teacher/salary", label: "Darslarim va oyligim", icon: Timer,
        hint: "Ishlab topganim va balans" },
      { to: "/teacher/finance", label: "Moliya", icon: Wallet,
        hint: "Oyliklar tarixi: oylar bo'yicha olgan va qoldiq" },
      { to: "/my-results", label: "Mening natijalarim", icon: PieChart,
        hint: "Guruhlaringiz o'zlashtirishi" },
      { to: "/my-career", label: "Karyera yo'lim", icon: TrendingUp,
        hint: "Daraja va o'sish rejasi" },
      { to: "/gamification", label: "Gamifikatsiya", icon: Trophy,
        hint: "O'quvchilar XP va ligalari" },
    ],
  },
  {
    title: "Boshqa",
    items: [
      { to: "/tasks", label: "Vazifalar", icon: ClipboardList,
        hint: "Sizga berilgan topshiriqlar" },
      { to: "/complaints", label: "Murojaatlar", icon: MessageSquareWarning,
        hint: "Shikoyat va takliflar" },
    ],
  },
];

// Support teacher'da kitob/imtihon buyurtma va gamifikatsiya yo'q —
// xodimlar panelidagi menyu qoidasi bilan bir xil.
const SUPPORT_HIDDEN = ["/my-books", "/my-exams", "/gamification"];

export default function TeacherMore() {
  const { user } = useAuth();
  const isSupport = user?.role === "support_teacher";

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-10">
        <div className="max-w-md mx-auto">
          <h1 className="text-xl font-semibold">Bo'limlar</h1>
          <p className="text-sm opacity-90 mt-0.5">
            Barcha funksiyalaringiz
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-5">
        {/* LAVOZIM ALMASHTIRISH (2026-08-12, Jahongir): ham ustoz, ham
            rahbar bo'lgan xodim (Nodir, Go'zal) shu yerdan boshqaruv
            paneliga o'tadi. 2+ lavozimlilardagina ko'rinadi. */}
        <RoleSwitchCard />
        {SECTIONS.map((sec) => {
          const items = sec.items.filter(
            (i) =>
              !(isSupport && SUPPORT_HIDDEN.includes(i.to)) &&
              // supportOnly bo'limlar faqat support teacherga
              !(!isSupport && (i as { supportOnly?: boolean }).supportOnly),
          );
          if (items.length === 0) return null;
          return (
            <div key={sec.title}>
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2 px-1">
                {sec.title}
              </p>
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                {items.map((i, n) => (
                  <Link
                    key={i.to}
                    to={i.to}
                    className={`flex items-center gap-3 p-3.5 active:bg-slate-50 transition ${
                      n > 0 ? "border-t border-slate-100" : ""
                    }`}
                  >
                    <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                      <i.icon size={17} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800">
                        {i.label}
                      </p>
                      <p className="text-[11px] text-slate-400 truncate">
                        {i.hint}
                      </p>
                    </div>
                    <ChevronRight size={16} className="text-slate-300 shrink-0" />
                  </Link>
                ))}
              </div>
            </div>
          );
        })}

        <p className="text-[11px] text-slate-400 text-center px-6">
          Bu bo'limlar to'liq ko'rinishda ochiladi — kompyuterda ham
          xuddi shunday ishlaydi.
        </p>
      </div>
    </>
  );
}


function RoleSwitchCard() {
  const { user } = useAuth();
  const myRoles = user?.roles ?? [];
  const picked = getActiveRole();
  const current = picked || user?.role || "";
  // 2026-08-25: ustoz kabinetiga o'tgan xodim boshqa lavozimiga
  // QAYTA OLISHI shart — shuning uchun tanlangan lavozim ro'yxatga
  // majburan qo'shiladi va karta har doim ko'rinadi.
  const opts = [...myRoles];
  if (current && !opts.some((r) => r.key === current))
    opts.push({ key: current, label: current });
  if (opts.length < 2 && !picked) return null;
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-brand-200 p-4">
      <p className="text-sm font-bold text-slate-800 mb-1">Lavozim</p>
      <p className="text-[11px] text-slate-400 mb-2">
        Qaysi lavozimda ishlashni tanlang — panel to'liq o'zgaradi
      </p>
      <select
        value={current}
        onChange={(e) => {
          setActiveRole(e.target.value || null);
          window.location.href = "/";
        }}
        className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm bg-white"
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
          className="mt-2 w-full rounded-xl border border-slate-200 py-2 text-[12px] font-semibold text-brand-600"
        >
          Asosiy lavozimga qaytish
        </button>
      )}
    </div>
  );
}
