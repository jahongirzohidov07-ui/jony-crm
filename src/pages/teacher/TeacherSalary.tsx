import { SalaryCard } from "../../components/SalaryCard";
import { TeacherFinance } from "../../components/TeacherFinance";

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
      {/* Oylar bo'yicha: oylik qancha edi, qancha berildi — yonma-yon
          (2026-09-16, Jahongir) */}
      <h2 className="text-sm font-semibold text-slate-800 mt-6 mb-2">
        Oylar bo'yicha: oylik va berilgan pul
      </h2>
      <TeacherFinance self compact />
      <p className="text-xs text-slate-400 mt-4">
        Batafsil hisob-kitob (darslar ro'yxati bilan) kompyuter
        ko'rinishida ham bor: Profil → To'liq panelga o'tish.
      </p>
    </div>
  );
}
