/** SVG BAYROQLAR (2026-08-11, Jahongir: "bayroq faqat yozuv bo'lib
 * ko'rinyapti" - Windows emoji bayroqlarni harf qilib ko'rsatadi,
 * shuning uchun SVG chizilgan - hamma qurilmada bir xil). */
export function Flag({ code, size = 22 }: { code: string; size?: number }) {
  const s = { width: size, height: Math.round(size * 0.72) };
  if (code === "ru")
    return (
      <svg {...s} viewBox="0 0 30 22" className="rounded-[3px] shadow-sm">
        <rect width="30" height="22" fill="#fff" />
        <rect y="7.33" width="30" height="7.33" fill="#0039A6" />
        <rect y="14.66" width="30" height="7.34" fill="#D52B1E" />
      </svg>
    );
  if (code === "de")
    return (
      <svg {...s} viewBox="0 0 30 22" className="rounded-[3px] shadow-sm">
        <rect width="30" height="7.33" fill="#000" />
        <rect y="7.33" width="30" height="7.33" fill="#DD0000" />
        <rect y="14.66" width="30" height="7.34" fill="#FFCE00" />
      </svg>
    );
  if (code === "ko")
    return (
      <svg {...s} viewBox="0 0 30 22" className="rounded-[3px] shadow-sm">
        <rect width="30" height="22" fill="#fff" />
        <circle cx="15" cy="11" r="5.5" fill="#CD2E3A" />
        <path
          d="M9.5 11a5.5 5.5 0 0 0 11 0 2.75 2.75 0 0 0-5.5 0 2.75 2.75 0 0 1-5.5 0z"
          fill="#0047A0"
        />
        <g stroke="#000" strokeWidth="1.1">
          <path d="M5 5.2l3.2-2.3M6 6.6l3.2-2.3M7 8l3.2-2.3" />
          <path d="M22 16.3l3.2-2.3M23 17.7l3.2-2.3M24 19.1l3.2-2.3" />
        </g>
      </svg>
    );
  // en - Union Jack (soddalashtirilgan)
  return (
    <svg {...s} viewBox="0 0 30 22" className="rounded-[3px] shadow-sm">
      <rect width="30" height="22" fill="#012169" />
      <path d="M0 0l30 22M30 0L0 22" stroke="#fff" strokeWidth="4" />
      <path d="M0 0l30 22M30 0L0 22" stroke="#C8102E" strokeWidth="2" />
      <path d="M15 0v22M0 11h30" stroke="#fff" strokeWidth="7" />
      <path d="M15 0v22M0 11h30" stroke="#C8102E" strokeWidth="4" />
    </svg>
  );
}
