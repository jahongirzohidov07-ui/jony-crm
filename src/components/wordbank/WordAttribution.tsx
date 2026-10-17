/**
 * So'zlar ro'yxati manbasi (2026-10-17). wordfreq ma'lumoti CC BY-SA
 * 4.0 litsenziyasida — muallif va litsenziya ko'rinib turishi SHART.
 */
export function WordAttribution({ className = "" }: { className?: string }) {
  return (
    <p className={`text-[11px] leading-snug text-slate-500 ${className}`}>
      So'z chastotasi: wordfreq (Robyn Speer va boshq.),{" "}
      <a
        href="https://creativecommons.org/licenses/by-sa/4.0/"
        target="_blank"
        rel="noopener noreferrer"
        className="underline"
      >
        CC BY-SA 4.0
      </a>{" "}
      — Jony Academy tomonidan moslashtirilgan
    </p>
  );
}
