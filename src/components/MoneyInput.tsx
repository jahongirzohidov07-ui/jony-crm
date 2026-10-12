import type { InputHTMLAttributes } from "react";

/**
 * SUMMA MAYDONI — 1,000,000 ko'rinishida (2026-10-12, Jahongir:
 * "summani kirgizganda 1,000,000 shunaqa shaklda bo'lsin, ko'rib
 * raqamni tushunishga osonroq bo'ladi").
 *
 * Qiymat ichkarida faqat raqamlar satri ("1000000") bo'lib qoladi —
 * chaqiruvchilar avvalgidek Number(value) qiladi. Ekranda esa
 * minglik vergul bilan ko'rinadi. Telefonda raqamli klaviatura.
 */
export function groupDigits(digits: string): string {
  // "1703333.33" kabi kasrli qiymat kelsa — butun qismi ko'rinadi
  const d = String(digits ?? "").split(".")[0]
    .replace(/\D/g, "").replace(/^0+(?=\d)/, "");
  return d.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function MoneyInput({
  value,
  onChange,
  className,
  ...rest
}: Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "type"> & {
  value: string;
  onChange: (digits: string) => void;
}) {
  return (
    <input
      {...rest}
      type="text"
      inputMode="numeric"
      autoComplete="off"
      value={groupDigits(value)}
      onChange={(e) => {
        // Kasr qismini (",50" yoki ".5") tashlab yuboramiz — so'm butun
        const raw = e.target.value.split(".")[0];
        onChange(raw.replace(/\D/g, "").replace(/^0+(?=\d)/, ""));
      }}
      className={className}
    />
  );
}
