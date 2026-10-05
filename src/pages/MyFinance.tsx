import { Link } from "react-router-dom";
import { TeacherFinance } from "../components/TeacherFinance";
import { useAuth } from "../lib/AuthContext";
import { SmmFinance } from "../components/SmmFinance";

/**
 * Ustozning MOLIYA bo'limi (kompyuter ko'rinishi) — oylar bo'yicha
 * oylik tarixi. 2026-09-05, Jahongir: "ustozlarda moliya bo'limi
 * qo'shilib oldin olgan oyliklari har oylik oyliklar o'sha yerga
 * hisoblanib borsin oyliklar tarixi bo'lsin".
 */
export default function MyFinance() {
  const { user } = useAuth();
  if (user?.role === "smm_manager") return <SmmFinance />;
  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Moliya</h1>
          <p className="text-sm text-slate-500">
            Oylar bo'yicha oylik tarixi: ishlab topgan, olgan, qoldiq, balans
          </p>
        </div>
        <Link to="/my-sessions" className="text-sm text-brand-600 hover:underline">
          Shu oy batafsil →
        </Link>
      </div>
      <TeacherFinance self />
    </div>
  );
}
