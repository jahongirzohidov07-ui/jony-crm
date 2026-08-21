import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, ArrowRight, Check, ChevronRight, Search, X,
} from "lucide-react";
import { api } from "../../lib/api";
import type { StudentHome, VocabStats } from "../../lib/studentApi";
import { getLang, LANGS } from "../../lib/lang";
import { Flag } from "../../components/Flag";
import { XpHex } from "../../components/Jsa";
import { fmtNum } from "../../lib/studentApi";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — LUG'AT.
 *
 * 2026-08-21: "lugat.png" dizayni bo'yicha YASHIL-TO'Q temada qayta
 * terildi (Jahongir: "hammasini 1ga 1 qilib ber 100% kopya bolsin").
 * Unit ro'yxati, 3x/6x qoidasi, mashq turi tanlash - mantiq
 * o'zgarmadi.
 */
export default function StudentVocab() {
  const nav = useNavigate();
  const lang = getLang();
  const [d, setD] = useState<StudentHome | null>(null);
  const [st, setSt] = useState<VocabStats | null>(null);
  const [units, setUnits] = useState<Any[]>([]);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [filt, setFilt] = useState<"all" | "started" | "solid">("all");
  const [picker, setPicker] = useState<string | null>(null);
  // Mashq soni tanlash (2026-08-21, Jahongir: "10 yoki 25 va 60 va
  // hammasi tanlaydigan bolishi kerak"). null = hali tur tanlanmagan.
  const [pickGame, setPickGame] = useState<string | null>(null);

  useEffect(() => {
    api.get<StudentHome>("/student/home").then(setD).catch(() => {});
    api.get<VocabStats>("/student/vocab/stats").then(setSt).catch(() => {});
    api
      .get<Any>(`/student/vocab/units?language=${lang}`)
      .then((r) => setUnits(r.units || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [lang]);

  const games: Any[] = d?.games || [];
  const langMeta = LANGS.find((l) => l.code === lang) || LANGS[0];
  const xp = d?.gamification?.lifetime_xp;

  function openGame(game: string, count: number) {
    const base = picker
      ? `?unit=${encodeURIComponent(picker)}&lang=${lang}`
      : `?lang=${lang}`;
    nav(`/student/games/${game}${base}&count=${count}`);
  }

  const shown = units.filter((u) => {
    if (q.trim() && !String(u.key).toLowerCase().includes(q.trim().toLowerCase()))
      return false;
    if (filt === "started") return (u.percent || 0) > 0;
    if (filt === "solid") return (u.learned6 || 0) > 0;
    return true;
  });

  // Yashil tema kartasi (dizaynda lug'at yashil ohangda)
  const card = { background: "#0E1F32", borderColor: "#1E3A4E" };

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8"
         style={{ margin: "0 auto" }}>
      {/* ------------------------------------------------ sarlavha */}
      <div className="flex items-center gap-2.5">
        <Link to="/student/games"
          className="w-10 h-10 rounded-xl flex items-center justify-center text-white shrink-0"
          style={{ background: "#0F5132" }}>
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-bold text-slate-300 flex-1">O'rganish</p>
        {xp != null && (
          <span className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 border shrink-0"
                style={card}>
            <XpHex size={16} />
            <b className="text-white text-sm">{fmtNum(xp)} XP</b>
          </span>
        )}
      </div>

      <div className="flex items-end gap-3 mt-3">
        <div className="flex-1 min-w-0">
          <h1 className="text-[30px] font-extrabold text-white leading-tight">
            JONY STUDENT APP
          </h1>
          <span className="mt-2 inline-flex items-center gap-2 rounded-full border px-3.5 py-2 text-sm font-semibold text-white"
                style={card}>
            <Flag code={lang} size={17} /> {langMeta.label}
          </span>
        </div>
        <img src="/jsicons/learn-vocabulary.png" alt=""
             className="w-[74px] h-[74px] shrink-0" />
      </div>

      {/* --------------------------------------------- statistika */}
      {st && (
        <div className="rounded-2xl border mt-4 px-2 py-4 grid grid-cols-4 gap-1 text-center"
             style={card}>
          <div>
            <p className="text-[24px] font-extrabold text-white leading-none">
              {fmtNum(st.correct)}
            </p>
            <p className="text-[11px] text-slate-400 mt-1.5">to'g'ri javob</p>
          </div>
          <div className="border-l" style={{ borderColor: "#1E3A4E" }}>
            <p className="text-[24px] font-extrabold text-white leading-none">
              {fmtNum(st.total)}
            </p>
            <p className="text-[11px] text-slate-400 mt-1.5">urinish</p>
          </div>
          <div className="border-l" style={{ borderColor: "#1E3A4E" }}>
            <p className="text-[24px] font-extrabold text-emerald-400 leading-none">
              {st.percent}%
            </p>
            <p className="text-[11px] text-slate-400 mt-1.5">aniqlik</p>
          </div>
          <div className="border-l" style={{ borderColor: "#1E3A4E" }}>
            <p className="text-[24px] font-extrabold text-white leading-none">
              🔥{st.streak}
            </p>
            <p className="text-[11px] text-slate-400 mt-1.5">kun</p>
          </div>
        </div>
      )}

      {err && <p className="text-sm text-red-400 mt-3">{err}</p>}

      {/* ------------------------------------------ umumiy mashq */}
      <button
        onClick={() => setPicker("")}
        className="w-full mt-3 rounded-2xl p-4 flex items-center gap-3 text-left active:scale-[0.99] transition"
        style={{ background: "linear-gradient(100deg,#12B76A,#039855)" }}
      >
        <span className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center text-[22px] shrink-0">
          🔀
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[19px] font-extrabold text-white">
            Umumiy mashq
          </span>
          <span className="block text-[13px] text-white/85 mt-0.5">
            Barcha unitlardan aralash so'zlar
          </span>
        </span>
        <span className="px-2.5 py-1 rounded-full bg-white/20 text-white text-xs font-bold shrink-0 inline-flex items-center gap-1">
          <XpHex size={12} /> +10 XP
        </span>
        <span className="w-10 h-10 rounded-full bg-white flex items-center justify-center shrink-0">
          <ArrowRight size={18} className="text-emerald-600" />
        </span>
      </button>

      {/* ------------------------------------------------ qidiruv */}
      <div className="mt-3 rounded-2xl border flex items-center gap-2.5 px-4 h-[48px]"
           style={card}>
        <Search size={18} className="text-slate-400 shrink-0" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Unit qidirish"
          className="flex-1 min-w-0 text-[15px] text-white placeholder:text-slate-500 outline-none bg-transparent"
        />
      </div>

      <div className="flex gap-2 mt-3">
        {([["all", "Barchasi"], ["started", "Boshlangan"],
           ["solid", "Mustahkam"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setFilt(k)}
            className={`flex-1 py-2.5 rounded-full text-sm font-bold transition ${
              filt === k ? "bg-emerald-600 text-white" : "text-slate-300 border"}`}
            style={filt === k ? undefined : card}>
            {l}
          </button>
        ))}
      </div>

      <p className="mt-3 text-[12px] text-slate-400 rounded-xl border px-3 py-2 flex gap-4"
         style={card}>
        <span><span className="text-sky-400">●</span> 3× — o'rganilgan</span>
        <span><span className="text-emerald-400">●</span> 6× — mustahkam</span>
      </p>

      {/* --------------------------------------------- unitlar */}
      <p className="text-[17px] font-extrabold text-white mt-4">Unitlar</p>
      <div className="space-y-2.5 mt-2">
        {shown.map((u, i) => (
          <button
            key={u.key}
            onClick={() => setPicker(u.key)}
            className="w-full bg-white rounded-2xl p-3.5 flex items-center gap-3 text-left active:scale-[0.99] transition"
          >
            <span className="w-11 h-11 rounded-xl bg-emerald-600 text-white text-[19px] font-extrabold flex items-center justify-center shrink-0">
              {String(u.key).replace(/\D/g, "") || i + 1}
            </span>
            <span className="min-w-0 flex-1">
              <span className="text-[16px] font-extrabold text-slate-900 flex items-center gap-1.5">
                {u.key}
                {u.passed && (
                  <Check size={13} className="text-amber-500" strokeWidth={4} />
                )}
              </span>
              <span className="block text-[12px] text-slate-400">
                {u.n} so'z
              </span>
            </span>
            <span className="text-[12px] shrink-0 text-right leading-tight">
              <span className="block">
                <span className="text-sky-600 font-bold">3×:</span>{" "}
                <b className="text-sky-600">{u.learned3}</b>
              </span>
              <span className="block mt-0.5">
                <span className="text-emerald-600 font-bold">6×:</span>{" "}
                <b className="text-emerald-600">{u.learned6}</b>
              </span>
            </span>
            <b className="text-[17px] text-slate-800 shrink-0 w-11 text-right">
              {u.percent}%
            </b>
            {(u.percent || 0) > 0 ? (
              <span className="px-3 py-2 rounded-xl bg-emerald-600 text-white text-[12px] font-bold shrink-0">
                Davom etish
              </span>
            ) : (
              <span className="w-9 h-9 rounded-full bg-emerald-50 flex items-center justify-center shrink-0">
                <ArrowRight size={16} className="text-emerald-600" />
              </span>
            )}
          </button>
        ))}
        {shown.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-8">
            Unit topilmadi
          </p>
        )}
      </div>

      <p className="text-[11px] text-slate-500 mt-3 px-1">
        So'zni 3 marta to'g'ri topsangiz "o'rganilgan", 6 marta topsangiz
        mustahkam sanaladi. 100% — ustozingiz unitni "topshirildi" deb
        tasdiqlaganda bo'ladi.
      </p>

      {/* ---- MASHQ TURI TANLASH ---- */}
      {picker !== null && (
        <div
          className="fixed inset-0 bg-black/50 z-[60] flex items-end justify-center"
          onClick={() => { setPicker(null); setPickGame(null); }}
        >
          <div
            className="w-full max-w-md bg-white rounded-t-2xl p-4 overflow-y-auto overscroll-contain"
            style={{
              maxHeight: "85dvh",
              paddingBottom: "calc(2rem + env(safe-area-inset-bottom))",
              WebkitOverflowScrolling: "touch",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-slate-800">
                {picker || "Umumiy mashq"} —{" "}
                {pickGame === null ? "qaysi turdagi practice?" : "nechta so'z?"}
              </p>
              <button onClick={() => { setPicker(null); setPickGame(null); }} className="text-slate-400"
                      aria-label="Yopish">
                <X size={18} />
              </button>
            </div>
            {pickGame !== null && (
              <div className="space-y-1.5">
                {[
                  [10, "10 ta", "Tezkor mashq"],
                  [25, "25 ta", "O'rtacha mashq"],
                  [60, "60 ta", "Katta mashq"],
                  [500, "Hammasi", "Barcha mavjud so'zlar"],
                ].map(([n, lbl, hint]) => (
                  <button
                    key={n as number}
                    onClick={() => openGame(pickGame, n as number)}
                    className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                  >
                    <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 text-sm font-bold">
                      {n === 500 ? "∞" : (n as number)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800">{lbl}</p>
                      <p className="text-[11px] text-slate-400">{hint}</p>
                    </div>
                    <ChevronRight size={16} className="text-slate-300" />
                  </button>
                ))}
                <button
                  onClick={() => setPickGame(null)}
                  className="w-full text-center text-xs text-slate-400 pt-2"
                >
                  ← Mashq turiga qaytish
                </button>
              </div>
            )}
            {pickGame === null && (
            <div className="space-y-1.5">
              {games.map((gm) => (
                <button
                  key={gm.key}
                  onClick={() => setPickGame(gm.key)}
                  className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                >
                  <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 text-sm font-bold">
                    {gm.label.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800">
                      {gm.label}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate">
                      {gm.hint}
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-slate-300" />
                </button>
              ))}
            </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
