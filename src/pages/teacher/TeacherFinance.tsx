import { Link } from "react-router-dom";
import { TeacherFinance } from "../../components/TeacherFinance";

/**
 * MOBIL "Moliya" sahifasi (2026-09-05, Jahongir: "ustozlarda moliya
 * bo'limi qo'shilib ... oyliklar tarixi bo'lsin"). Oylar bo'yicha:
 * ishlab topgan, olgan, qoldiq, balans.
 */
export default function TeacherFinancePage() {
  return (
    <div className="p-4 pb-24">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-lg font-bold text-slate-900">Moliya</h1>
        <Link to="/teacher/salary" className="text-xs text-brand-600 hover:underline">
          Shu oy batafsil →
        </Link>
      </div>
      <TeacherFinance self compact />
    </div>
  );
}
