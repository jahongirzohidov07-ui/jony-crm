import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";
import { api, type Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { ORG_WIDE_ROLES } from "../lib/roles";

/**
 * Filial tanlagich. Faqat butun tashkilotni ko'radigan foydalanuvchiga
 * ko'rinadi — filialga bog'langan xodim baribir o'z filialini ko'radi,
 * shuning uchun unga tanlov ko'rsatish chalg'itadi.
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
  const [branches, setBranches] = useState<Branch[]>([]);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => setBranches([]));
  }, []);

  const orgWide = !!user?.role && ORG_WIDE_ROLES.includes(user.role);
  if (!orgWide || branches.length < 2) return null;

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
