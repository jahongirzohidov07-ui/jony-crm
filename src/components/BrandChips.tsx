import { useEffect, useState } from "react";
import { useAuth } from "../lib/AuthContext";
import {
  getSmmBrands, readBrandFilter, saveBrandFilter, pickBrandFilter,
  type SmmBrandsResponse,
} from "../lib/smmBrands";

/* BREND FILTRI (2026-10-17). Jahongir: Marhabo bitta emas, uchta
   brendni yuritadi — Jony Academy, Jony School va Jahongir Zoxidov
   shaxsiy brendi. "Hammasi" + har bir faol brend tugmasi. Avval faqat
   "Kontent taqvimi"da (Boshqa ostida) edi — endi kundalik
   "Kontent-plan"da ham, shuning uchun alohida faylda (ContentPlan va
   Smm ikkalasi ishlatadi). Tanlov har xodim brauzerida alohida
   saqlanadi (faqat qulaylik). */

/** Brend filtri: sel null — brendlar hali yuklanmadi (so'rov kutadi). */
export function useBrandFilter() {
  const { user } = useAuth();
  const owner = user?.full_name || "";
  const [data, setData] = useState<SmmBrandsResponse | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    getSmmBrands()
      .then((r) => {
        if (!alive) return;
        setData(r);
        setSel(pickBrandFilter(r, readBrandFilter(owner)));
      })
      .catch(() => {
        // Brendlar ochilmasa ham ro'yxat ishlayversin — filtrsiz
        if (!alive) return;
        setData({ brands: [], mine: [] });
        setSel("all");
      });
    return () => { alive = false; };
  }, [owner]);
  const choose = (v: string) => {
    setSel(v);
    saveBrandFilter(v, owner);
  };
  return { data, sel, choose };
}

export function BrandChips({ data, sel, onPick }: {
  data: SmmBrandsResponse | null;
  sel: string | null;
  onPick: (v: string) => void;
}) {
  const active = (data?.brands || []).filter((b) => b.is_active);
  if (active.length === 0) return null;
  const chip = (key: string, text: string, mine = false) => (
    <button
      key={key}
      onClick={() => onPick(key)}
      title={mine ? "Siz shu brendga biriktirilgansiz" : undefined}
      className={`max-w-full truncate px-3 py-1.5 rounded-full text-xs font-medium border ${
        sel === key
          ? "border-brand-300 bg-brand-50 text-brand-700"
          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
      }`}
    >
      {text}
    </button>
  );
  return (
    <div className="flex flex-wrap gap-1.5 mb-3">
      {chip("all", "Hammasi")}
      {active.map((b) => chip(String(b.id), b.name, b.mine))}
    </div>
  );
}
