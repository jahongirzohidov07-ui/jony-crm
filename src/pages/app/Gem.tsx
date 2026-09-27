import { GEM } from "./gemIcons";

/**
 * GEM — premium ikonka plitkasi (maketdagi bilan bir xil, 2026-09-27).
 *
 * Qatlamlar: yorqin gradientli squircle → pastki o'ng burchakda yumshoq
 * yorug'lik → tepada shisha kabi yaltiroq yoy → ichki oq chiziq →
 * belgining rangli soyasi → oq belgi. Tashqi rangli soya CSS'da
 * (.gem filtri, --gc o'zgaruvchisi).
 *
 * Belgi matni (path) — gemIcons.ts dagi O'ZIMIZNING statik
 * konstantalar; foydalanuvchi ma'lumoti bu yerga tushmaydi.
 */
export function Gem({ name, size = 40, className = "" }: {
  name: string;
  size?: number;
  className?: string;
}) {
  const g = GEM[name] || GEM.more;
  const c = g[2];
  const last = c[c.length - 1];
  const k = `gm-${name}`;
  return (
    <svg
      className={`gem ${className}`}
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
      style={{ ["--gc" as string]: last }}
    >
      <defs>
        <linearGradient id={`${k}a`} x1="0" y1="0" x2="1" y2="1">
          {c.map((x, i) => (
            <stop key={i} offset={c.length < 2 ? 0 : i / (c.length - 1)} stopColor={x} />
          ))}
        </linearGradient>
        <linearGradient id={`${k}b`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" stopOpacity=".42" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
        <radialGradient id={`${k}c`} cx=".85" cy="1" r=".75">
          <stop offset="0" stopColor="#fff" stopOpacity=".16" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${k}d`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" />
          <stop offset="1" stopColor="#fff" stopOpacity=".86" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="14.5" fill={`url(#${k}a)`} />
      <rect x="2" y="2" width="44" height="44" rx="14.5" fill={`url(#${k}c)`} />
      <path
        d="M16.5 2h15A14.5 14.5 0 0 1 46 16.5v1.2C38 22 30 23.4 24 23.4S10 22 2 17.7v-1.2A14.5 14.5 0 0 1 16.5 2z"
        fill={`url(#${k}b)`}
      />
      <rect x="2.6" y="2.6" width="42.8" height="42.8" rx="13.9" fill="none"
            stroke="#fff" strokeOpacity=".45" strokeWidth="1.1" />
      <g transform="translate(12.5 13.2) scale(.0898)" fill={last} opacity=".45"
         dangerouslySetInnerHTML={{ __html: g[0] }} />
      <g transform="translate(12.5 12) scale(.0898)" fill={`url(#${k}d)`}
         dangerouslySetInnerHTML={{ __html: g[0] }} />
    </svg>
  );
}

/** Oddiy belgi — tugma, menyu va sarlavha ichida; rangni atrofidan oladi. */
export function Glyph({ name, size = 20, className = "" }: {
  name: string;
  size?: number;
  className?: string;
}) {
  const g = GEM[name] || GEM.more;
  return (
    <svg
      className={`gl ${className}`}
      width={size}
      height={size}
      viewBox="0 0 256 256"
      fill="currentColor"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: g[1] }}
    />
  );
}
