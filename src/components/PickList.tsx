import { useEffect, useState } from "react";
import { api, type Reference } from "../lib/api";

/** Ma'lumotnomalarni bir marta yuklab, keyin keshdan beradi. */
let cache: Reference | null = null;
let pending: Promise<Reference> | null = null;

export function useReference(branchId?: number | null): Reference | null {
  const [ref, setRef] = useState<Reference | null>(cache);

  useEffect(() => {
    if (cache) {
      setRef(cache);
      return;
    }
    if (!pending) {
      pending = api.get<Reference>(
        `/reference${branchId ? `?branch_id=${branchId}` : ""}`
      );
    }
    pending
      .then((r) => {
        cache = r;
        setRef(r);
      })
      .catch(() => setRef(null));
  }, [branchId]);

  return ref;
}

/**
 * Ro'yxatdan tanlanadigan maydon. Ro'yxatda yo'q eski qiymat bo'lsa ham
 * yo'qolmaydi — u alohida variant sifatida qo'shiladi.
 */
export function PickList({
  value,
  onChange,
  options,
  placeholder = "Tanlang",
  className = "",
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
  className?: string;
}) {
  const list = value && !options.includes(value) ? [value, ...options] : options;
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white ${className}`}
    >
      <option value="">{placeholder}</option>
      {list.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );
}
