import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

/**
 * Ko'zchali parol maydoni.
 *
 * 2026-08-12, Jahongir: "Mana shu parollarniyam ko'zchani bosib
 * ko'rinadigan qilinsa yaxshi bo'lardi" (parol almashtirish oynasi).
 * Telefonda ko'r-ko'rona yozilgan parol ko'pincha xato chiqadi va odam
 * nima yozganini bilmaydi — ko'zcha shuni hal qiladi.
 */
export function PasswordInput({
  value,
  onChange,
  placeholder,
  autoFocus,
  autoComplete,
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  autoComplete?: string;
  className?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? "text" : "password"}
        className={
          className ??
          "w-full rounded-lg border border-slate-300 px-3 py-2 pr-10 text-sm"
        }
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        autoComplete={autoComplete}
      />
      <button
        type="button"
        tabIndex={-1}
        onClick={() => setShow((v) => !v)}
        title={show ? "Parolni yashirish" : "Parolni ko'rish"}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
      >
        {show ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}
