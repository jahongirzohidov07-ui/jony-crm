import { SalaryCard } from "../../components/SalaryCard";

/**
 * MOBIL oylik sahifasi (Jahongir: "telefon versiyadan oylikni
 * ko'rmoqchi bo'lsa kompyuter versiyaga o'tib ketyabdi ishlamayabdi").
 * Endi ustoz telefonda ham oyligini shu yerda ko'radi.
 */
export default function TeacherSalary() {
  return (
    <div className="p-4 pb-24">
      <h1 className="text-lg font-bold text-slate-900 mb-3">
        Darslarim va oyligim
      </h1>
      <SalaryCard self />
      <p className="text-xs text-slate-400 mt-4">
        Batafsil hisob-kitob (darslar ro'yxati bilan) kompyuter
        ko'rinishida ham bor: Profil → To'liq panelga o'tish.
      </p>
    </div>
  );
}
