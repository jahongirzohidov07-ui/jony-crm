import type { CSSProperties, ImgHTMLAttributes } from "react";

const ICONS = ["grammar", "vocabulary", "listening", "reading", "writing", "speaking", "coin", "xp", "level", "mission", "streak", "trophy", "gift", "certificate", "settings", "wallet"] as const;
export type StudentIconName = typeof ICONS[number];

export function StudentIcon({ name, size, className = "", style, label }: { name: StudentIconName; size?: number; className?: string; style?: CSSProperties; label?: string }) {
  const index = ICONS.indexOf(name);
  return <span className={`student-icon ${className}`} role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true}
    style={{ width: size, height: size, clipPath: index >= 8 && index <= 11 ? "inset(0 0 9% 0)" : undefined, backgroundPosition: `${index % 4 * 100 / 3}% ${Math.floor(index / 4) * 100 / 3}%`, ...style }} />;
}

const ALIASES: Record<string, StudentIconName> = {
  "learn-grammar": "grammar", "learn-vocabulary": "vocabulary", "learn-listening": "listening", "learn-reading": "reading", "learn-writing": "writing", "learn-jony-teacher": "speaking",
  "game-coin": "coin", "game-xp": "xp", "game-level": "level", "game-mission": "mission", "game-streak": "streak", "game-reward": "gift",
  "learn-certificate": "certificate", "learn-exam": "certificate", "learn-quiz": "grammar", "learn-lesson": "grammar", "profile-payment": "wallet", "shop-wallet": "wallet", "auth-protected": "level",
};

/** Keep real photos and product images; replace only known decorative assets. */
export function StudentImage(props: ImgHTMLAttributes<HTMLImageElement>) {
  const key = props.src?.match(/^\/jsicons\/([^/]+)\.png$/)?.[1];
  const name = key ? ALIASES[key] : undefined;
  if (!name) return <img {...props} />;
  return <StudentIcon name={name} className={props.className} style={props.style} label={props.alt || undefined} />;
}

export function StudentCoinIcon({ size = 18, className = "" }: { size?: number; className?: string }) {
  return <StudentIcon name="coin" size={size} className={className} />;
}
