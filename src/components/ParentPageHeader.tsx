import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";

/**
 * Ota-ona portalidagi ichki sahifalar (to'lovlar, coin/XP, natijalar,
 * reyting) uchun bir xil sarlavha — orqaga qaytish tugmasi va sarlavha
 * har doim bir xil ko'rinishda bo'lishi uchun (2026-08-09, Jahongir:
 * "professional qilib ... kerakli joylariga kerakli tugmalar").
 */
export function ParentPageHeader({
  title,
  icon,
}: {
  title: string;
  icon: ReactNode;
}) {
  return (
    <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-8">
      <div className="max-w-md mx-auto">
        <Link
          to=".."
          relative="path"
          className="inline-flex items-center gap-1.5 text-sm text-white/85 hover:text-white mb-4"
        >
          <ArrowLeft size={16} />
          Bosh sahifa
        </Link>
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
            {icon}
          </div>
          <h1 className="text-lg font-semibold">{title}</h1>
        </div>
      </div>
    </div>
  );
}
