import { StudentLoading } from "../../components/StudentLoading";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, ChevronRight, Crown, Lock } from "lucide-react";
import { api } from "../../lib/api";
import { StudentCoinIcon as CoinIcon } from "../../components/StudentIcon";
import { XpHex, JSA } from "../../components/Jsa";
import { fmtNum, type StudentHome as Home } from "../../lib/studentApi";
import { getLang, LANGS } from "../../lib/lang";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — GRAMMAR.
 *
 * 2026-08-20: "ORganish grammar.png" dizayni bo'yicha to'q temada
 * qayta terildi (Jahongir: "1ga 1 qilib ber"). Ma'lumot va qulf
 * mantig'i o'zgarmadi: /student/grammar/topics, A1->A2->B1->B2
 * zanjiri, boss mavzular.
 */

const ALL_LEVELS = [
  { key: "a1", chip: "A1", name: "A1 — Beginner" },
  { key: "a2", chip: "A2", name: "A2 — Elementary" },
  { key: "b1", chip: "B1", name: "B1 — Intermediate" },
  { key: "b2", chip: "B2", name: "B2 — Upper-Intermediate" },
  // 2026-08-24, Jahongir: "c1 va C2 mavzularni ham qoyish kerak"
  { key: "c1", chip: "C1", name: "C1 — Advanced" },
  { key: "c2", chip: "C2", name: "C2 — Native" },
] as const;

export default function StudentGrammar() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [sel, setSel] = useState<string>("a1");
  const [xp, setXp] = useState<number | null>(null);
  // O'RGANILAYOTGAN TIL (2026-08-24, Jahongir: "Boshqa tillarni
  // grammatikasi yoq ekan ularni ham qoshib qoygin") — bayroqdagi
  // tanlov endi grammatikaga ham ta'sir qiladi.
  const lang = getLang();
  const langLabel = LANGS.find((l) => l.code === lang)?.label || "";

  useEffect(() => {
    api
      .get<Any>(`/student/grammar/topics?language=${lang}`)
      .then((r) => {
        setD(r);
        // Ochilganda hozir o'qilayotgan daraja tanlangan bo'lsin
        const cur = !r?.a1?.completed ? "a1"
          : r?.a2_locked ? "a1"
          : !(r?.a2?.completed) ? "a2"
          : r?.b1_locked ? "a2"
          : !(r?.b1?.completed) ? "b1"
          : r?.b2_locked ? "b1"
          : !(r?.b2?.completed) ? "b2"
          : r?.c1_locked ? "b2"
          : !(r?.c1?.completed) ? "c1"
          : r?.c2_locked ? "c1" : "c2";
        setSel(cur);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
    api.get<Home>("/student/home")
      .then((h) => setXp(h.gamification?.lifetime_xp ?? null))
      .catch(() => {});
  }, []);

  const info = useMemo(() => {
    if (!d) return null;
    const lv: Record<string, Any> = {
      a1: d.a1, a2: d.a2, b1: d.b1, b2: d.b2, c1: d.c1, c2: d.c2,
    };
    const locked: Record<string, boolean> = {
      a1: false, a2: !!d.a2_locked, b1: !!d.b1_locked,
      b2: !!d.b2_locked, c1: !!d.c1_locked, c2: !!d.c2_locked,
    };
    // Shu tilda QAYSI darajalarda kontent bor — faqat o'shalar chiziladi
    const avail = new Set(
      ((d.available || ["A1", "A2", "B1", "B2"]) as string[])
        .map((x: string) => x.toLowerCase()),
    );
    const levels = ALL_LEVELS.filter((l) => avail.has(l.key));
    let done = 0, total = 0;
    for (const k of Object.keys(lv)) {
      const x = lv[k];
      if (x?.topics) { done += x.done || 0; total += x.total || x.topics.length; }
    }
    return { lv, locked, levels, done, total,
             pct: total ? Math.round((done / total) * 100) : 0 };
  }, [d]);

  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!d || !info)
    return <StudentLoading />;

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const cur = info.lv[sel];
  const curLocked = info.locked[sel];
  const curName = ALL_LEVELS.find((l) => l.key === sel)?.name || "";
  const topics: Any[] = cur?.topics || [];
  // Birinchi tugallanmagan mavzu - "faol" (oq karta); undan keyingisi
  // "Keyingi" belgisini oladi.
  const activeIdx = topics.findIndex((t) => !t.done);

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      {/* ------------------------------------------------ sarlavha */}
      <div className="flex items-center gap-2.5">
        <Link
          to="/student/games"
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold text-white tracking-wide flex-1">
          JONY STUDENT APP
        </p>
        {xp != null && (
          <span className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 border shrink-0"
                style={card}>
            <XpHex size={16} />
            <b className="text-white text-sm">{fmtNum(xp)} XP</b>
          </span>
        )}
      </div>

      <div className="flex items-end gap-3 mt-3">
        <div className="flex-1">
          <h1 className="text-[38px] font-extrabold text-white leading-none">
            Grammar
          </h1>
          <p className="text-[15px] text-slate-400 mt-2">
            {langLabel} · {info.done}/{info.total} mavzu
          </p>
        </div>
        <span className="text-[52px] leading-none -mb-1">📖</span>
      </div>

      {/* ------------------------------------- umumiy progress */}
      <div className="rounded-2xl border p-4 mt-4" style={card}>
        <div className={`grid gap-1 ${
          info.levels.length <= 2 ? "grid-cols-2"
          : info.levels.length <= 4 ? "grid-cols-4" : "grid-cols-6"
        }`}>
          {info.levels.map((l) => {
            const x = info.lv[l.key];
            const doneAll = !!x?.completed;
            const active = !doneAll && !info.locked[l.key];
            return (
              <div key={l.key} className="text-center">
                <div className="relative inline-block">
                  <svg width="46" height="46" viewBox="0 0 24 24">
                    <path d="M12 1.5 21 6.75v10.5L12 22.5 3 17.25V6.75Z"
                          fill={doneAll || active ? "#5B4BE8" : "#2A3670"}
                          stroke={doneAll || active ? "#8F7CFF" : "#3A4890"}
                          strokeWidth="1.2" />
                    <text x="12" y="15.5" textAnchor="middle" fontSize="7.5"
                          fontWeight="800" fill="#fff">{l.chip}</text>
                  </svg>
                  {doneAll && (
                    <span className="absolute -top-1 -right-1 w-4.5 h-4.5 w-[18px] h-[18px] rounded-full bg-white flex items-center justify-center">
                      <Check size={11} strokeWidth={4} className="text-slate-900" />
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-300 leading-tight mt-0.5">
                  {doneAll ? `${l.chip} tugatildi 🎉`
                    : info.locked[l.key] ? `${l.chip} qulflangan`
                    : `${l.chip} davom etmoqda`}
                </p>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-3 mt-3">
          <div className="h-2.5 flex-1 rounded-full bg-[#26326B] overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-400"
                 style={{ width: `${info.pct}%` }} />
          </div>
          <b className="text-white text-[15px]">{info.pct}%</b>
        </div>
        <p className="text-xs text-slate-400 mt-1.5">Umumiy progress</p>
      </div>

      {/* ---- QIYNALGAN MAVZULAR (2026-08-24, Jahongir: "Qaysidur
           mavzuda qiynalsa qiynalgan mavzularidan yana takrorlaydigan
           joyi ham bo'lsin") ---- */}
      {(d.weak || []).length > 0 && (
        <div className="rounded-2xl border p-4 mt-4"
             style={{ background: "#2A1E0E", borderColor: "#7A5A1E" }}>
          <p className="text-[15px] font-bold text-amber-300">
            Qiynalgan mavzular
          </p>
          <p className="text-[12px] text-amber-200/70 mt-0.5">
            Shu mavzularda xato ko'p — takrorlash darajani ko'taradi.
            Mashq xato qilingan savollardan boshlanadi.
          </p>
          <div className="space-y-2 mt-3">
            {d.weak.map((w: Any) => (
              <Link
                key={w.topic}
                to={`/student/grammar/${encodeURIComponent(w.topic)}`}
                className="flex items-center gap-3 rounded-xl border px-3 py-2.5"
                style={{ background: "#1A2558", borderColor: "#3A4890" }}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-white truncate">
                    {w.topic}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {w.wrong} ta xato · aniqlik {w.accuracy}%
                  </p>
                </div>
                <span className="text-[11px] font-bold text-amber-300 bg-amber-400/10 border border-amber-400/30 rounded-full px-2.5 py-1 shrink-0">
                  Takrorlash
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ------------------------------------------- daraja chiplari */}
      <div className="flex gap-2.5 mt-4">
        {info.levels.map((l) => (
          <button
            key={l.key}
            onClick={() => setSel(l.key)}
            className={`flex-1 py-2.5 rounded-full text-[15px] font-bold transition ${
              sel === l.key
                ? "bg-violet-600 text-white"
                : "text-slate-300 border"
            }`}
            style={sel === l.key ? undefined : card}
          >
            {l.chip}
          </button>
        ))}
      </div>

      {/* ------------------------------------------- daraja nomi */}
      <h2 className="text-[24px] font-extrabold text-white mt-5">{curName}</h2>
      <p className="text-sm text-slate-400 mt-1">
        {curLocked
          ? "Oldingi darajani tugating — bu bosqich ochiladi"
          : `${cur?.done ?? 0}/${cur?.total ?? topics.length} mavzu`}
      </p>

      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2.5 text-[12px] text-slate-400">
        <span className="inline-flex items-center gap-1">
          <span className="w-3.5 h-3.5 rounded-full bg-emerald-500 inline-flex items-center justify-center">
            <Check size={9} strokeWidth={4} className="text-white" />
          </span>
          Tugatildi
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="w-3.5 h-3.5 rounded-full border-2 border-violet-400 inline-block" />
          Davom etyapti
        </span>
        <span className="inline-flex items-center gap-1">
          <Lock size={11} /> Qulflangan
        </span>
        <span className="inline-flex items-center gap-1">
          <Crown size={12} className="text-amber-400" /> Boss
        </span>
      </div>

      {/* --------------------------------------------- mavzular */}
      <div className="space-y-3 mt-4">
        {curLocked && (
          <div className="rounded-2xl border-2 border-dashed p-5 flex items-center gap-3"
               style={{ borderColor: "#2A3670" }}>
            <span className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: "#1A2558" }}>
              <Lock size={17} className="text-slate-400" />
            </span>
            <p className="text-sm text-slate-300">
              {curName} hali qulf — oldingi darajadagi barcha mavzularni
              tugating.
            </p>
          </div>
        )}

        {!curLocked && topics.map((t: Any, i: number) => {
          const boss = !!t.boss;
          const isActive = i === activeIdx && !t.done;
          const isNext = activeIdx >= 0 && i === activeIdx + 1 && !t.done;
          const href = `/student/grammar/${encodeURIComponent(t.topic)}`;

          if (boss) {
            return (
              <Link key={t.topic} to={href}
                className="flex items-center gap-3 rounded-2xl border p-3.5 active:scale-[0.99] transition"
                style={{ background: "#241B45", borderColor: "#7A5B16" }}>
                <span className="w-12 h-12 rounded-2xl bg-violet-600/60 flex items-center justify-center shrink-0">
                  <Crown size={22} className="text-amber-400" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-amber-300 font-bold">BOSS —</p>
                  <p className="text-[17px] font-extrabold text-amber-400 truncate">
                    {t.topic}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {t.solved}/{t.total} · 🕐 4 daqiqa
                  </p>
                </div>
                <span className="px-3 py-1.5 rounded-full border border-amber-500/60 text-amber-300 text-xs font-bold shrink-0">
                  Boss sinovi
                </span>
                {t.done ? (
                  <span className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                    <Check size={13} strokeWidth={4} className="text-white" />
                  </span>
                ) : (
                  <Lock size={15} className="text-slate-400 shrink-0" />
                )}
              </Link>
            );
          }

          if (isActive) {
            return (
              <Link key={t.topic} to={href}
                className="flex items-center gap-3 rounded-2xl bg-white p-3.5 active:scale-[0.99] transition shadow-[0_0_24px_rgba(124,92,240,0.35)]">
                <span className="w-12 h-12 rounded-2xl bg-violet-600 flex items-center justify-center text-white font-extrabold text-[15px] shrink-0">
                  Aa
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-slate-500 font-semibold">
                    Level {i + 1} —
                  </p>
                  <p className="text-[18px] font-extrabold text-slate-900 truncate">
                    {t.topic}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    <b className="text-violet-600">{t.solved}/{t.total}</b>
                    {" "}· 🕐 4 daqiqa
                  </p>
                  <div className="h-1.5 rounded-full bg-slate-100 mt-1.5 overflow-hidden">
                    <div className="h-full bg-violet-500 rounded-full"
                         style={{ width: `${t.percent}%` }} />
                  </div>
                </div>
                <div className="text-right shrink-0 space-y-1">
                  <p className="text-xs font-bold text-slate-700 inline-flex items-center gap-1">
                    <XpHex size={13} /> +9 XP
                  </p>
                  <p className="text-xs font-bold text-slate-700 flex items-center gap-1 justify-end">
                    <CoinIcon size={13} /> +5 Coin
                  </p>
                  <span className="inline-flex w-10 h-10 rounded-xl bg-violet-600 items-center justify-center">
                    <ChevronRight size={19} className="text-white" />
                  </span>
                </div>
              </Link>
            );
          }

          return (
            <Link key={t.topic} to={href}
              className="flex items-center gap-3 rounded-2xl border p-3.5 active:scale-[0.99] transition"
              style={card}>
              <span className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${
                t.done ? "bg-emerald-500/20" : "bg-violet-600/40"}`}>
                {t.done
                  ? <Check size={20} className="text-emerald-400" strokeWidth={3} />
                  : <Lock size={18} className="text-violet-200" />}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-slate-400 font-semibold">
                  Level {i + 1} —
                </p>
                <p className="text-[17px] font-extrabold text-white truncate">
                  {t.topic}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t.solved}/{t.total} · 🕐 4 daqiqa
                </p>
              </div>
              {isNext ? (
                <span className="px-3.5 py-2 rounded-xl border text-slate-200 text-sm font-semibold shrink-0"
                      style={{ borderColor: "#3A4890", background: "#1A2558" }}>
                  Keyingi
                </span>
              ) : !t.done ? (
                <Lock size={16} className="text-slate-500 shrink-0" />
              ) : (
                <ChevronRight size={17} className="text-slate-500 shrink-0" />
              )}
            </Link>
          );
        })}

        {!curLocked && topics.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-8">
            Bu darajaga mashqlar tez orada yuklanadi.
          </p>
        )}
      </div>
    </div>
  );
}
