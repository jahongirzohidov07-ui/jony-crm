import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";
import { api, type Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { ORG_WIDE_ROLES } from "../lib/roles";

/**
 * Filial tanlagich.
 *
 * IKKI XIL foydalanuvchiga ko'rinadi:
 *  1. Butun tashkilotni ko'radigan rol (asoschi, HR, o'quv bo'limi
 *     rahbari va h.k.) — BARCHA filiallar ro'yxati bilan;
 *  2. IKKI YOKI UNDAN KO'P filialga biriktirilgan xodim (masalan ikki
 *     filialda dars beradigan ustoz) — faqat O'Z filiallari bilan.
 *
 * (2) 2026-08-10 da qo'shildi: Jahongir xabar berdi — ikki filialli
 * ustozda tanlagich umuman chiqmasdi, chunki u faqat (1) ga
 * ko'rsatilardi. Bitta filialga bog'langan xodimga esa hamon
 * ko'rinmaydi — unga tanlov ko'rsatish chalg'itadi.
 */
export function BranchPicker({
  value,
  onChange,
  className = "",
}: {
  value: number | null;
  onChange: (id: number | null) => void;
  className?: string;
}) {
  const { user } = useAuth();
  const [all, setAll] = useState<Branch[]>([]);
  const orgWide = !!user?.role && ORG_WIDE_ROLES.includes(user.role);
  const mine = user?.branches ?? [];

  useEffect(() => {
    // Butun tashkilotni ko'radiganlar uchungina to'liq ro'yxat
    // so'raladi — qolganlarga o'z filiallari /me dan allaqachon keladi.
    if (!orgWide) return;
    api.get<Branch[]>("/branches").then(setAll).catch(() => setAll([]));
  }, [orgWide]);

  const branches: Branch[] = orgWide
    ? all
    : (mine as Branch[]);

  if (branches.length < 2) return null;

  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      <Building2 size={14} className="text-slate-400" />
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
      >
        <option value="">Barcha filiallar</option>
        {branches.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name}
          </option>
        ))}
      </select>
    </div>
  );
}

/** URL uchun filial parametri: "&branch_id=3" yoki bo'sh satr. */
export function branchParam(id: number | null): string {
  return id ? `&branch_id=${id}` : "";
}
