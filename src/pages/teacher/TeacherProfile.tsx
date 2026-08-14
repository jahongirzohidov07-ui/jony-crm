import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, LogOut, Monitor } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { getUiLang, setUiLang } from "../../lib/uiLang";
import { BrandIcon } from "../../components/BrandIcon";
import type { TeacherHome } from "../../lib/teacherApi";

/** JONY TEACHER — profil va qisqa ko'rsatkichlar. */
export default function TeacherProfile() {
  const { user, logout } = useAuth();
  const [d, setD] = useState<TeacherHome | null>(null);

  useEffect(() => {
    api.get<TeacherHome>("/teacher/home").then(setD).catch(() => {});
  }, []);

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-12">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center shrink-0">
            <BrandIcon size={34} className="rounded-lg" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-semibold truncate">
              {d?.teacher || user?.full_name}
            </h1>
            <p className="text-sm opacity-90">
              {user?.role === "support_teacher" ? "Support teacher" : "O'qituvchi"}
              {d?.grade ? ` · ${d.grade}` : ""}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 space-y-4">
        {d && (
          <div className="grid grid-cols-3 gap-3">
            <Stat value={String(d.groups)} label="Guruh" />
            <Stat value={String(d.students)} label="O'quvchi" />
            <Stat value={String(d.lessons_this_month)} label="Bu oy dars" />
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <Link
            to="/profile"
            className="flex items-center gap-3 p-3.5 active:bg-slate-50"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800">
                Shaxsiy ma'lumotlar
              </p>
              <p className="text-[11px] text-slate-400">
                Parolni o'zgartirish, telefon raqami
              </p>
            </div>
            <ChevronRight size={16} className="text-slate-300 shrink-0" />
          </Link>
          <Link
            to="/"
            className="flex items-center gap-3 p-3.5 border-t border-slate-100 active:bg-slate-50"
          >
            <div className="w-9 h-9 rounded-lg bg-slate-50 text-slate-500 flex items-center justify-center shrink-0">
              <Monitor size={17} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800">
                To'liq panelga o'tish
              </p>
              <p className="text-[11px] text-slate-400">
                Kompyuter ko'rinishi (JonyOS)
              </p>
            </div>
            <ChevronRight size={16} className="text-slate-300 shrink-0" />
          </Link>
        </div>

        {/* TIL / ЯЗЫК — 2026-08-13, Jahongir: "Profil bo'limida til
            o'zgartirish joyini qo'shgin ... hozir faqat rus tiliga,
            faqat ustozlar uchun". */}
        <LangCard />

        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-slate-200 bg-white text-slate-600 text-sm font-medium"
        >
          <LogOut size={16} />
          Chiqish
        </button>
      </div>
    </>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3 text-center">
      <p className="text-xl font-bold text-slate-900 leading-tight">{value}</p>
      <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}


/** Til tanlash: o'zbekcha yoki ruscha. Tanlangach sahifa yangilanadi. */
function LangCard() {
  const cur = getUiLang();
  const pick = (l: "uz" | "ru") => {
    if (l === cur) return;
    setUiLang(l);
    window.location.reload();
  };
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3.5">
      <p className="text-sm font-medium text-slate-800 mb-0.5">
        Til / Язык
      </p>
      <p className="text-[11px] text-slate-400 mb-2.5">
        Ustoz kabineti tanlangan tilda ko'rinadi
      </p>
      <div className="grid grid-cols-2 gap-2">
        {([
          ["uz", "O'zbekcha"],
          ["ru", "Русский"],
        ] as const).map(([k, label]) => (
          <button
            key={k}
            onClick={() => pick(k)}
            className={`py-2.5 rounded-lg text-sm font-medium border transition ${
              cur === k
                ? "bg-brand-600 border-brand-600 text-white"
                : "bg-white border-slate-200 text-slate-600"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
