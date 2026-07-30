import { useEffect, useState } from "react";

/**
 * O'zbekiston telefon raqami. +998 doim turadi, faqat raqam kiritiladi
 * va "90 123 45 67" ko'rinishida ajratib ko'rsatiladi.
 *
 * Tashqariga toza raqam beriladi: "901234567" — bazada shu saqlanadi,
 * shuning uchun eski yozuvlar ham buziladi emas.
 */
export function PhoneInput({
  value,
  onChange,
  placeholder = "90 123 45 67",
  className = "",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [text, setText] = useState("");

  // Tashqaridan kelgan qiymatni ko'rinishga aylantiramiz
  useEffect(() => {
    setText(pretty(digits(value)));
  }, [value]);

  function digits(v: string): string {
    let d = (v || "").replace(/\D/g, "");
    if (d.startsWith("998")) d = d.slice(3);
    return d.slice(0, 9);
  }

  function pretty(d: string): string {
    const p = [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)];
    return p.filter(Boolean).join(" ");
  }

  return (
    <div
      className={`flex items-stretch rounded-lg border border-slate-200 overflow-hidden bg-white ${className}`}
    >
      <span className="px-3 py-2 text-sm text-slate-500 bg-slate-50 border-r border-slate-200 select-none">
        +998
      </span>
      <input
        inputMode="numeric"
        value={text}
        onChange={(e) => {
          const d = digits(e.target.value);
          setText(pretty(d));
          onChange(d);
        }}
        placeholder={placeholder}
        className="flex-1 px-3 py-2 text-sm outline-none min-w-0"
      />
    </div>
  );
}

/** Ko'rsatish uchun: "901234567" -> "+998 90 123 45 67". */
export function formatPhone(v?: string | null): string {
  if (!v) return "";
  let d = v.replace(/\D/g, "");
  if (d.startsWith("998")) d = d.slice(3);
  if (d.length !== 9) return v;
  return `+998 ${d.slice(0, 2)} ${d.slice(2, 5)} ${d.slice(5, 7)} ${d.slice(7)}`;
}
