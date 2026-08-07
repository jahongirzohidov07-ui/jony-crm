import { useEffect, useState } from "react";
import { api, type Reference } from "../lib/api";

/** Ma'lumotnomalarni bir marta yuklab, keyin keshdan beradi. Filial
 * bo'yicha alohida keshlanadi — har filialning o'z hudud/maktab
 * ro'yxati bor, birinchi yuklangani boshqasiga "yopishib qolmasin". */
const cacheByBranch = new Map<string, Reference>();
const pendingByBranch = new Map<string, Promise<Reference>>();

export function useReference(branchId?: number | null): Reference | null {
  const key = branchId ? String(branchId) : "_";
  const [ref, setRef] = useState<Reference | null>(
    cacheByBranch.get(key) ?? null
  );

  useEffect(() => {
    const cached = cacheByBranch.get(key);
    if (cached) {
      setRef(cached);
      return;
    }
    let p = pendingByBranch.get(key);
    if (!p) {
      p = api.get<Reference>(
        `/reference${branchId ? `?branch_id=${branchId}` : ""}`
      );
      pendingByBranch.set(key, p);
    }
    p.then((r) => {
      cacheByBranch.set(key, r);
      setRef(r);
    }).catch(() => setRef(null));
  }, [branchId, key]);

  return ref;
}

const OTHER = "__boshqa__";

/**
 * Ro'yxatdan tanlanadigan maydon. Eng tagida "Boshqa" bor — bosilsa
 * o'zi qo'lda yozadigan maydonga aylanadi. Ro'yxatda yo'q eski qiymat
 * bo'lsa ham yo'qolmaydi — qo'lda yozish holatida ochiladi.
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
  const isKnown = !value || options.includes(value);
  const [custom, setCustom] = useState(!isKnown);

  if (custom) {
    return (
      <div className="flex gap-1.5">
        <input
          autoFocus
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Qo'lda yozing"
          className={`flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm ${className}`}
        />
        <button
          type="button"
          onClick={() => {
            setCustom(false);
            onChange("");
          }}
          className="px-2 text-xs text-slate-500 hover:text-brand-600 whitespace-nowrap"
        >
          ro'yxatdan
        </button>
      </div>
    );
  }

  const list = value && !options.includes(value) ? [value, ...options] : options;
  return (
    <select
      value={value}
      onChange={(e) => {
        if (e.target.value === OTHER) {
          setCustom(true);
          onChange("");
        } else {
          onChange(e.target.value);
        }
      }}
      className={`w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white ${className}`}
    >
      <option value="">{placeholder}</option>
      {list.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
      <option value={OTHER}>— Boshqa (o'zi yoziladi) —</option>
    </select>
  );
}
