import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Award, ChevronRight, CreditCard, LogOut, Settings, Star, TrendingUp,
  Trophy, User as UserIcon, Camera, Check, X,
} from "lucide-react";
import { CoinIcon } from "../../components/CoinIcon";
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
               points: number };

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
  xp?: number;
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
      <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>
    );

  const lv = d.level;
  const per = 500;
  const inLevel = lv?.next ? per - lv.next.points_left : per;
  const pct = lv?.next ? Math.round(lv.next.progress_percent) : 100;

  return (
    <div className="bg-slate-50 min-h-screen">
      <div className="max-w-md mx-auto px-4 pt-6 pb-8 space-y-4">
        <div className="flex items-center">
          <h1 className="text-xl font-bold text-slate-900 flex-1 text-center pl-8">
            Profil
          </h1>
          <Link
            to="/student/settings"
            className="w-9 h-9 flex items-center justify-center text-slate-400"
          >
            <Settings size={22} />
          </Link>
        </div>

        {msg && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex gap-2 items-center">
            <Check size={16} className="text-emerald-600" />
            <p className="text-sm text-emerald-800 flex-1">{msg}</p>
            <button onClick={() => setMsg("")} className="text-emerald-500">
              <X size={15} />
            </button>
          </div>
        )}
        {err && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex gap-2 items-center">
            <p className="text-sm text-red-700 flex-1">{err}</p>
            <button onClick={() => setErr("")} className="text-red-400">
              <X size={15} />
            </button>
          </div>
        )}

        {/* ------------------------------------------ FOYDALANUVCHI */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
          <div className="flex items-center gap-4">
            <label className="relative shrink-0 cursor-pointer">
              <div className="w-[72px] h-[72px] rounded-full bg-brand-50 overflow-hidden flex items-center justify-center">
                {d.photo ? (
                  <img
                    src={d.photo}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <UserIcon size={32} className="text-brand-300" />
                )}
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-7 h-7 rounded-full bg-brand-600 text-white flex items-center justify-center border-2 border-white">
                <Camera size={13} />
              </span>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                disabled={busy}
                onChange={onPhoto}
              />
            </label>

            <div className="min-w-0 flex-1">
              <p className="text-[22px] font-bold text-slate-900 truncate">
                {d.first_name || d.full_name}
              </p>
              <span className="inline-block mt-1 px-2.5 py-1 rounded-lg bg-brand-600 text-white text-xs font-bold">
                {lv?.level?.cefr || "—"}
              </span>
              <p className="text-xs text-slate-500 mt-2">
                XP {fmtNum(inLevel)} / {fmtNum(per)}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <div className="h-2 flex-1 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full bg-brand-600 rounded-full"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-brand-600 shrink-0">
                  {pct}%
                </span>
              </div>
              {d.group && (
                <p className="text-xs text-slate-400 mt-1.5">{d.group}</p>
              )}
            </div>
          </div>
        </div>

        {/* -------------------------------------- ENGLISH SKILLS */}
        {d.radar && d.radar.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-start">
              <div className="flex-1">
                <p className="text-xl font-bold text-slate-900">
                  English Skills
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {d.radar_note}
                </p>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 text-xs font-bold shrink-0">
                {lv?.level?.cefr}
              </span>
            </div>

            <RadarChart data={d.radar} />

            <div className="grid grid-cols-2 gap-2 mt-1">
              <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-2.5">
                <span className="w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0">
                  <Star size={15} className="text-emerald-600" fill="currentColor" />
                </span>
                <div className="min-w-0">
                  <p className="text-[11px] text-slate-500">Eng kuchli</p>
                  <p className="text-sm font-bold text-emerald-700 truncate">
                    {d.strongest?.label} {d.strongest?.score}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-orange-50 p-2.5">
                <span className="w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0">
                  <TrendingUp size={15} className="text-orange-500" />
                </span>
                <div className="min-w-0">
                  <p className="text-[11px] text-slate-500">Rivojlantirish</p>
                  <p className="text-sm font-bold text-orange-600 truncate">
                    {d.weakest?.label} {d.weakest?.score}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* -------------------------------------------- UCH KARTA */}
        <div className="grid grid-cols-3 gap-2.5">
          <Link
            to="/student/shop?tab=badges"
            className="bg-white rounded-xl border border-slate-200 p-3 text-center active:scale-[0.98] transition"
          >
            <span className="w-10 h-10 rounded-full bg-brand-50 flex items-center justify-center mx-auto">
              <Trophy size={19} className="text-brand-600" />
            </span>
            <p className="text-sm font-bold text-slate-900 mt-2">Yutuqlar</p>
            <p className="text-[11px] text-slate-400">
              {d.badges_done}/{d.badges_total}
            </p>
          </Link>

          <Link
            to="/student/shop"
            className="bg-white rounded-xl border border-slate-200 p-3 text-center active:scale-[0.98] transition"
          >
            <span className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center mx-auto">
              <CoinIcon size={20} />
            </span>
            <p className="text-sm font-bold text-slate-900 mt-2">Coin</p>
            <p className="text-[11px] text-slate-400">{fmtNum(d.coins)}</p>
          </Link>

          <Link
            to="/student/certificates"
            className="bg-white rounded-xl border border-slate-200 p-3 text-center active:scale-[0.98] transition"
          >
            <span className="w-10 h-10 rounded-full bg-violet-50 flex items-center justify-center mx-auto">
              <Award size={19} className="text-violet-600" />
            </span>
            <p className="text-sm font-bold text-slate-900 mt-2">
              Sertifikat
            </p>
            <p className="text-[11px] text-slate-400">{d.certificates ?? 0}</p>
          </Link>
        </div>

        {/* ---------------------------------------------- TO'LOV */}
        <Link
          to="/student/payments"
          className={`flex items-center gap-3 rounded-xl border p-4 ${
            (d.balance ?? 0) < 0
              ? "bg-red-50 border-red-200"
              : "bg-white border-slate-200"
          }`}
        >
          <span
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              (d.balance ?? 0) < 0
                ? "bg-red-100 text-red-500"
                : "bg-emerald-50 text-emerald-600"
            }`}
          >
            <CreditCard size={19} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-slate-900">To'lovlar</p>
            <p
              className={`text-sm mt-0.5 ${
                (d.balance ?? 0) < 0 ? "text-red-600" : "text-slate-500"
              }`}
            >
              Balans: {fmtNum(d.balance)} so'm
            </p>
          </div>
          <ChevronRight size={18} className="text-slate-300" />
        </Link>

        {/* ---------------------------------------------- CHIQISH */}
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl border border-slate-200 bg-white text-slate-500 text-sm font-medium"
        >
          <LogOut size={16} />
          Chiqish
        </button>

        <p className="text-[11px] text-slate-400 text-center pt-1">
          Jony Student · {d.phone}
        </p>
      </div>
    </div>
  );
}
