import { StudentLoading } from "../../components/StudentLoading";
import { formatPhone } from "../../components/PhoneInput";
import { StudentImage, StudentIcon } from "../../components/StudentIcon";
import { StudentXpHelp } from "../../components/StudentXpHelp";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Camera, Check, ChevronRight, LogOut, Settings,
  TrendingUp, X } from "lucide-react";
import { BrandIcon } from "../../components/BrandIcon";
import { StudentCoinIcon as CoinIcon } from "../../components/StudentIcon";
import { useAuth } from "../../lib/AuthContext";
import { api } from "../../lib/api";
import { fmtNum, type LevelProgress } from "../../lib/studentApi";

/**
 * JONY STUDENT — PROFIL (2026-08-16 da dizayn bo'yicha qayta yozildi).
 *
 * Jahongir: "Progress bosh sahifada ham, profilda ham deyarli bir xil
 * takrorlangan. Profilga quyidagilar ko'proq mos: yutuqlar va
 * badge'lar, coin tarixi, XP tarixi, o'rganish statistikasi,
 * sertifikatlar, to'lovlar, sozlamalar."
 *
 * Shuning uchun profildan kunlik vazifa va daraja progressi olib
 * tashlandi (ular Asosiy sahifada). O'rniga ENGLISH SKILLS radar
 * diagrammasi — o'quvchi qaysi ko'nikmasi kuchli, qaysi biri
 * orqada ekanini bir qarashda ko'radi.
 *
 * Radar sof SVG bilan chizilgan — hech qanday kutubxona
 * qo'shilmadi (ilova og'irlashmasin).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Radar = { key: string; label: string; tone: string; score: number;
               points: number; band?: number; cefr?: string;
               available?: number; coverage?: number };
type Ielts = {
  band: number;
  skills: { key: string; label: string; score: number; band: number;
            cefr: string }[];
  weakest: string;
};

type Profile = {
  full_name: string;
  first_name?: string | null;
  last_name?: string | null;
  photo?: string | null;
  phone?: string | null;
  group?: string | null;
  school?: string | null;
  level?: LevelProgress;
  radar?: Radar[];
  radar_note?: string;
  ielts?: Ielts;
  league?: { name: string; icon: string; color: string } | null;
  xp?: number;
  writing_progress?: {
    submitted: number;
    latest: { format_score: number | null; expert_status: string } | null;
  };
  coins?: number;
  streak?: number;
  balance?: number;
  badges_done?: number;
  badges_total?: number;
  certificates?: number;
  strongest?: { label: string; score: number } | null;
  weakest?: { label: string; score: number } | null;
};

/** Oltiburchak radar. Hech qanday kutubxona ishlatilmaydi. */
function RadarChart({ data }: { data: Radar[] }) {
  const size = 300;
  const cx = size / 2;
  const cy = size / 2 + 6;
  const R = 96;
  const n = data.length || 1;

  const pt = (i: number, r: number) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };

  const ring = (frac: number) =>
    data
      .map((_, i) => pt(i, R * frac).map((v) => v.toFixed(1)).join(","))
      .join(" ");

  const shape = data
    .map((d, i) =>
      pt(i, (R * Math.max(4, Math.min(100, d.score))) / 100)
        .map((v) => v.toFixed(1))
        .join(",")
    )
    .join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size + 30}`} className="w-full">
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon
          key={f}
          points={ring(f)}
          fill="none"
          stroke="#DDE6F5"
          strokeWidth="1"
        />
      ))}
      {data.map((_, i) => {
        const [x, y] = pt(i, R);
        return (
          <line
            key={i}
            x1={cx}
            y1={cy}
            x2={x}
            y2={y}
            stroke="#E8EEF9"
            strokeWidth="1"
          />
        );
      })}

      <polygon
        points={shape}
        fill="#1A6FE4"
        fillOpacity="0.28"
        stroke="#1A6FE4"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      {data.map((d, i) => {
        const [x, y] = pt(i, (R * Math.max(4, Math.min(100, d.score))) / 100);
        return <circle key={i} cx={x} cy={y} r="4.5" fill="#1A6FE4" />;
      })}

      {data.map((d, i) => {
        const [x, y] = pt(i, R + 30);
        return (
          <g key={d.key}>
            <text
              x={x}
              y={y - 4}
              textAnchor="middle"
              className="fill-slate-700"
              style={{ fontSize: 12, fontWeight: 600 }}
            >
              {d.label}
            </text>
            <text
              x={x}
              y={y + 11}
              textAnchor="middle"
              className="fill-brand-600"
              style={{ fontSize: 13, fontWeight: 700 }}
            >
              {d.score}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function StudentProfile() {
  const { logout } = useAuth();
  const [d, setD] = useState<Profile | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  function load() {
    api
      .fresh<Profile>("/student/profile")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }
  useEffect(load, []);

  async function onPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 3 * 1024 * 1024) {
      setErr("Rasm 3 MB dan katta bo'lmasin");
      return;
    }
    setBusy(true);
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        await api.put("/student/photo", { photo: reader.result });
        setMsg("Rasm yangilandi");
        load();
      } catch (ex) {
        setErr(ex instanceof Error ? ex.message : "Xatolik");
      } finally {
        setBusy(false);
      }
    };
    reader.readAsDataURL(f);
  }

  if (err && !d)
    return (
      <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>
    );
  if (!d)
    return (
      <StudentLoading />
    );

  const lv = d.level;
  // 2026-08-25: daraja oralig'i endi har darajada har xil
  // (roles.ENG_LEVEL_POINTS) — 500 deb qotirib qo'yish noto'g'ri edi.
  const from = lv?.level_from ?? 0;
  const to = lv?.next?.need ?? lv?.level_to ?? from;
  const per = Math.max(1, to - from);
  const inLevel = lv?.next ? per - lv.next.points_left : per;
  const pct = lv?.next ? Math.round(lv.next.progress_percent) : 100;

  // 2026-08-20: "profil.png" dizayni bo'yicha TO'Q temada qayta
  // terildi (Jahongir: "1ga 1 qilib ber"). Radar, rasm yuklash,
  // to'lov va chiqish mantig'i o'zgarmadi.
  const card = { background: "#0c2258", borderColor: "#35538c" };

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-4">
      {/* ------------------------------------------------ sarlavha */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2.5 flex-1 min-w-0">
          <span className="shrink-0"><BrandIcon size={40} /></span>
          <div className="leading-none">
            <p className="text-[15px] font-extrabold text-white">JONY</p>
            <p className="text-[15px] font-extrabold text-white">STUDENT APP</p>
          </div>
        </div>
        <Link
          to="/student/settings"
          aria-label="Profil sozlamalari"
          className="w-11 h-11 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}
        >
          <Settings size={20} />
        </Link>
      </div>

      <div>
        <h1 className="text-[34px] font-extrabold text-white leading-none">
          Profil
        </h1>
        <p className="text-sm text-slate-400 mt-1.5">
          O'zingiz haqingizda ma'lumotlar
        </p>
      </div>

      {msg && (
        <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-xl p-3 flex gap-2 items-center">
          <Check size={16} className="text-emerald-400" />
          <p className="text-sm text-emerald-300 flex-1">{msg}</p>
          <button onClick={() => setMsg("")} className="text-emerald-400">
            <X size={15} />
          </button>
        </div>
      )}
      {err && (
        <div className="bg-red-500/10 border border-red-500/40 rounded-xl p-3 flex gap-2 items-center">
          <p className="text-sm text-red-300 flex-1">{err}</p>
          <button onClick={() => setErr("")} className="text-red-400">
            <X size={15} />
          </button>
        </div>
      )}

      {/* -------------------------------------- FOYDALANUVCHI KARTASI */}
      <div className="student-hero student-pattern rounded-3xl p-5"
           style={{ background:
             "linear-gradient(120deg,#16267A 0%,#1D2F8E 60%,#3A2F9E 100%)" }}>
        <div className="flex items-center gap-4">
          <label className="relative shrink-0 cursor-pointer">
            <div className="w-[88px] h-[88px] rounded-full bg-brand-600 border-4 border-brand-400/70 overflow-hidden flex items-center justify-center">
              {d.photo ? (
                <StudentImage src={d.photo} alt="" className="w-full h-full object-cover" />
              ) : (
                <span className="text-[34px] font-extrabold text-white">
                  {(d.first_name || d.full_name || "?").charAt(0)}
                </span>
              )}
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-8 h-8 rounded-full bg-white text-brand-600 flex items-center justify-center border-2 border-brand-300">
              <Camera size={14} />
            </span>
            <input type="file" accept="image/*" className="hidden"
                   disabled={busy} onChange={onPhoto} />
          </label>

          <div className="min-w-0 flex-1">
            <p className="text-[23px] font-extrabold text-white break-words leading-tight">
              {d.first_name || d.full_name}
            </p>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#101B4A] border border-[#2E56E8] text-white text-xs font-bold">
                🛡 {lv?.level?.label} · {lv?.level?.cefr}
              </span>
              {d.group && (
                <span className="px-2.5 py-1 rounded-lg bg-brand-600 text-white text-xs font-bold whitespace-normal break-words max-w-full">
                  {d.group}
                </span>
              )}
            </div>
          </div>
        </div>

        <p className="text-sm text-white/85 mt-4">
          Daraja balli <b className="text-white">{fmtNum(inLevel)}</b>
          <span className="text-white/60"> / {fmtNum(per)}</span>
        </p>
              <StudentXpHelp />
        <div className="flex items-center gap-2.5 mt-2">
          <div className="h-2.5 flex-1 rounded-full bg-white/20 overflow-hidden">
            <div className="h-full rounded-full bg-white"
                 style={{ width: `${Math.max(pct, 4)}%` }} />
          </div>
          <b className="text-white text-sm shrink-0">{pct}%</b>
        </div>
        {lv?.next && (
          <p className="text-[13px] text-white/75 mt-2">
            {lv.next.label}'gacha{" "}
            <b className="text-sky-300">{lv.next.points_left} ball</b> qoldi
          </p>
        )}
      </div>

      {/* ------------------------------- IELTS taxminiy bali (oq) */}
      {/* 2026-08-25, Jahongir: "hamma skillarni qoshib ortachasini
          chiqarganda uni IELTS balli kelib chiqsin". */}
      {d.ielts && (
        <div className="student-panel bg-white rounded-3xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-[64px] h-[64px] rounded-2xl bg-slate-900 flex flex-col items-center justify-center shrink-0">
              <b className="text-white text-[20px] leading-none">
                {d.ielts.band > 0 ? d.ielts.band.toFixed(1) : "—"}
              </b>
              <span className="text-[9px] text-slate-400 mt-0.5">IELTS</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[19px] font-extrabold text-slate-900 leading-tight">
                Taxminiy IELTS bali
              </p>
              <p className="text-[11.5px] text-slate-500 leading-snug mt-0.5">
                Oltita ko'nikma balining o'rtachasi. Bitta ko'nikma
                bo'sh tursa — umumiy ball ko'tarilmaydi.
              </p>
            </div>
          </div>

          <div className="mt-3 divide-y divide-slate-100">
            {d.ielts.skills.map((sk) => (
              <div key={sk.key} className="flex items-center gap-2 py-1.5">
                <span className="text-[12.5px] text-slate-700 w-[78px] shrink-0">
                  {sk.label}
                </span>
                <div className="h-1.5 flex-1 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full rounded-full"
                       style={{ width: `${Math.max(sk.score, 2)}%`,
                                background: sk.score >= 44 ? "#16A34A"
                                  : sk.score >= 18 ? "#F59E0B" : "#94A3B8" }} />
                </div>
                <span className="text-[10px] text-slate-400 w-7 shrink-0 text-right">
                  {sk.cefr}
                </span>
                <b className="text-[12px] text-slate-900 w-8 shrink-0 text-right">
                  {sk.band > 0 ? sk.band.toFixed(1) : "—"}
                </b>
              </div>
            ))}
          </div>

          {/* 2026-08-25, Jahongir: "shu joyi kerak emas 44 ball = B2
              (IELTS 6.0) - 70 = C1 (7.5) - 95 = C2 (9.0)" — shkala
              izohi olib tashlandi, faqat foydali gap qoldi. */}
          <p className="text-[11px] text-slate-400 mt-2.5 leading-relaxed">
            Eng zaif tomon — <b className="text-slate-700">
            {d.ielts.weakest}</b>.
          </p>
        </div>
      )}

      {/* ------------------------------------------------ liga */}
      {!!d.writing_progress?.submitted && (
        <div className="rounded-2xl border p-4 text-slate-200" style={card}>
          <p className="font-bold text-white">Writing natijangiz saqlandi</p>
          <p className="text-sm mt-1">Topshirilgan yozuvlar: {d.writing_progress.submitted}</p>
          {d.writing_progress.latest?.format_score != null && (
            <p className="text-sm">Oxirgi format bahosi: {d.writing_progress.latest.format_score}/100</p>
          )}
          <p className="text-xs mt-2 text-slate-300">
            {d.writing_progress.latest?.expert_status === "available"
              ? "Ekspert tahlili topshiriq natijasida ko'rsatildi."
              : d.writing_progress.latest?.expert_status === "unavailable"
                ? "Ekspert bahosi olinmadi. Keyinroq topshiriqni qayta yuborishingiz mumkin."
                : "Bu eski yozuv uchun ekspert holati saqlanmagan."}
            {" "}Format bahosi IELTS bali emas. Ko'nikma shkalasi yig'ilgan mashq ballariga asoslanadi;
            dastlabki natijalar yaxlitlanganda 0 ko'rinishi mumkin.
          </p>
        </div>
      )}

      <Link to="/student/leagues"
            className="flex items-center gap-3 rounded-2xl border p-4"
            style={card}>
        <span className="text-[26px] shrink-0">{d.league?.icon || "🏅"}</span>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] text-slate-400">Ligangiz</p>
          <p className="text-white font-bold text-[16px] truncate">
            {d.league?.name || "Newcomer"}
          </p>
        </div>
        <ChevronRight size={17} className="text-slate-500 shrink-0" />
      </Link>

      {/* -------------------------------------- ENGLISH SKILLS (oq) */}
      {d.radar && d.radar.length > 0 && (
        <div className="student-panel bg-white rounded-3xl p-4">
          <p className="text-[22px] font-extrabold text-slate-900">
            English Skills
          </p>
          <p className="text-xs text-slate-600 mt-0.5">{d.radar_note}</p>

          <RadarChart data={d.radar} />

          <div className="grid grid-cols-2 gap-2 mt-1">
            <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-2.5">
              <span className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                <TrendingUp size={15} className="text-white" />
              </span>
              <div className="min-w-0">
                <p className="text-[11px] text-emerald-700">Eng kuchli</p>
                <p className="text-sm font-bold text-emerald-700 break-words">
                  {d.strongest?.label}{" "}
                  <span className="text-[17px]">{d.strongest?.score}</span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-red-50 p-2.5">
              <span className="w-8 h-8 rounded-full bg-red-400 flex items-center justify-center shrink-0">
                <TrendingUp size={15} className="text-white" />
              </span>
              <div className="min-w-0">
                <p className="text-[11px] text-red-600">Rivojlantirish</p>
                <p className="text-sm font-bold text-red-600 break-words">
                  {d.weakest?.label}{" "}
                  <span className="text-[17px]">{d.weakest?.score}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------ 2x2 KARTALAR */}
      <div className="grid grid-cols-2 gap-3">
        <Link to="/student/shop?tab=badges"
          className="rounded-2xl border p-4 flex items-center gap-3 active:scale-[0.98] transition"
          style={card}>
          <StudentIcon name="trophy" size={40} />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-white">Yutuqlar</p>
            <p className="text-[15px] font-extrabold text-brand-300">
              {d.badges_done}/{d.badges_total}
            </p>
          </div>
          <ChevronRight size={17} className="text-slate-500 shrink-0" />
        </Link>

        <Link to="/student/shop"
          className="rounded-2xl border p-4 flex items-center gap-3 active:scale-[0.98] transition"
          style={card}>
          <span className="shrink-0"><CoinIcon size={30} /></span>
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-white">Coin</p>
            <p className="text-[15px] font-extrabold text-brand-300">
              {fmtNum(d.coins)}
            </p>
          </div>
          <ChevronRight size={17} className="text-slate-500 shrink-0" />
        </Link>

        <Link to="/student/certificates"
          className="rounded-2xl border p-4 flex items-center gap-3 active:scale-[0.98] transition"
          style={card}>
          <StudentIcon name="certificate" size={40} />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-white">Sertifikatlar</p>
            <p className="text-[15px] font-extrabold text-brand-300">
              {d.certificates ?? 0}
            </p>
          </div>
          <ChevronRight size={17} className="text-slate-500 shrink-0" />
        </Link>

        <Link to="/student/payments"
          className="rounded-2xl border p-4 flex items-center gap-3 active:scale-[0.98] transition"
          style={card}>
          <StudentIcon name="wallet" size={40} />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-white">To'lovlar</p>
            <p className={`text-[15px] font-extrabold truncate ${
              (d.balance ?? 0) < 0 ? "text-red-400" : "text-emerald-400"}`}>
              {(d.balance ?? 0) > 0 ? "+" : ""}{fmtNum(d.balance)} so'm
            </p>
          </div>
          <ChevronRight size={17} className="text-slate-500 shrink-0" />
        </Link>
      </div>

      {/* -------------------------------- DO'STINGNI OLIB KEL
          2026-08-28, Jahongir: "referallar holati ko'rinib turishi
          kerak". Karta 2x2 to'rdan TASHQARIDA va kengroq — bu
          dastur bolaga pul tejaydi, ko'zga tashlanishi kerak. */}
      <Link to="/student/referral"
        className="block rounded-2xl p-4 bg-gradient-to-r from-violet-600 to-brand-600
                   active:scale-[0.98] transition">
        <div className="flex items-center gap-3">
          <StudentIcon name="gift" size={40} />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-white">
              Do'stingni olib kel
            </p>
            <p className="text-[12px] text-white/85 leading-snug">
              1 ta do'st — 10%, 5 ta do'st — o'qish BEPUL
            </p>
          </div>
          <ChevronRight size={18} className="text-white/80 shrink-0" />
        </div>
      </Link>

      {/* ------------------------------------------------ CHIQISH */}
      <button
        onClick={logout}
        className="w-full flex items-center justify-between px-4 py-4 rounded-2xl border-2 border-red-500/70 text-red-400 text-[16px] font-bold"
      >
        <span className="flex items-center gap-2.5">
          <LogOut size={18} />
          Chiqish
        </span>
        <ChevronRight size={18} />
      </button>

      <p className="text-[11px] text-slate-500 text-center pt-1">
        Jony Student · {formatPhone(d.phone)}
      </p>
    </div>
  );
}
