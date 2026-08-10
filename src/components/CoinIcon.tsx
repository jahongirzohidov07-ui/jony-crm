/** JONY COIN IKONKASI (2026-08-11, Jahongir: "coin joyida umuman
 * tufta iconca turibdi - menga iconca yasab ber").
 *
 * Oltin tanga: gradientli disk, ichida "J" harfi (Jony), yuqorida
 * yaltirash chizig'i. Sof SVG - hamma qurilmada bir xil, o'lchami
 * moslashuvchan. */
export function CoinIcon({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="jc-body" x1="8" y1="4" x2="40" y2="44">
          <stop offset="0" stopColor="#FFE082" />
          <stop offset="0.5" stopColor="#FFC107" />
          <stop offset="1" stopColor="#F59E0B" />
        </linearGradient>
        <linearGradient id="jc-rim" x1="24" y1="2" x2="24" y2="46">
          <stop offset="0" stopColor="#FFD54F" />
          <stop offset="1" stopColor="#E65100" />
        </linearGradient>
      </defs>
      {/* tashqi gardish */}
      <circle cx="24" cy="24" r="22" fill="url(#jc-rim)" />
      {/* asosiy disk */}
      <circle cx="24" cy="24" r="18.5" fill="url(#jc-body)" />
      {/* ichki chiziq (zarb halqasi) */}
      <circle
        cx="24"
        cy="24"
        r="15.5"
        fill="none"
        stroke="#B45309"
        strokeOpacity="0.55"
        strokeWidth="1.6"
        strokeDasharray="2.6 2.2"
      />
      {/* J harfi */}
      <path
        d="M28.5 14v13.2c0 3.6-2.6 6-6.1 6-2.9 0-5.2-1.6-6-4.2l3.5-1.4c.4 1.3 1.3 2 2.5 2 1.4 0 2.4-1 2.4-2.6V17.6h-5V14h8.7z"
        fill="#7C2D12"
      />
      <path
        d="M28 13.4v13.2c0 3.6-2.6 6-6.1 6-2.9 0-5.2-1.6-6-4.2l3.5-1.4c.4 1.3 1.3 2 2.5 2 1.4 0 2.4-1 2.4-2.6V17h-5v-3.6H28z"
        fill="#FFF8E1"
      />
      {/* yaltirash */}
      <path
        d="M12 12.5c3-3.8 8-5.6 12.6-4.9"
        stroke="#FFFDE7"
        strokeOpacity="0.9"
        strokeWidth="2.4"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
