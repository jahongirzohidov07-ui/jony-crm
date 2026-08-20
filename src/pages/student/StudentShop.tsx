import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Check, X, ShoppingBag, AlertCircle, ChevronRight, Search,
  ShoppingCart, Flame, Trophy, Lock, BookOpen, Star, Calendar, Award,
  Target, Clock, ArrowLeft, Gift, Percent,
} from "lucide-react";
import { CoinIcon } from "../../components/CoinIcon";
import { formatDate } from "../../lib/format";
import { api, type MyCoins, type RewardItem } from "../../lib/api";

/**
 * JONY STUDENT — COIN DO'KONI.
 *
 * 2026-08-20, Jahongir: "menga shopdagi korinish umuman yoqmadi,
 * o'sha narsani rasmi bo'lishi kerak va men senga shop degan
 * dizaynni tashladim shuni 100% bir xil qilib bergin ... 1ga 1
 * copya bolishi kerak".
 *
 * Ekran uning dizayni bo'yicha qayta qurildi:
 *   sarlavha + savat ikonkasi (buyurtmalar, kutilayotgani bo'lsa nuqta)
 *   ko'k balans kartasi: coin soni, "Coin tarixi", keyingi sovringa
 *     qancha qolgani progress bilan
 *   "Coinlaringizni sovringa aylantiring" bloki -> Yutuqlar
 *   qidiruv + kategoriya chiplari
 *   ikki ustunli RASMLI mahsulot kartalari
 *
 * Mantiq o'zgarmadi (2026-08-15/20 qoidalari): 33% va 100% chegirma
 * coin yetsa darrov beriladi; qolgan chegirma va sovg'alar xodim
 * tasdig'i bilan - coin band bo'lib turadi, rad etilsa qaytadi.
 */

const TONE: Record<string, string> = {
  teal: "bg-teal-100 text-teal-700",
  sky: "bg-sky-100 text-sky-700",
  emerald: "bg-emerald-100 text-emerald-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

type Badge = {
  key: string; label: string; hint: string; icon: string; tone: string;
  have: number; target: number; done: boolean; percent: number; left: number;
};

type Ach = {
  streak: number;
  badges: Badge[];
  done: number;
  total: number;
  streak_rewards: { days: number; coin: number; done: boolean;
                    left: number; percent: number }[];
  next: Badge | null;
};

/* eslint-disable @typescript-eslint/no-explicit-any */
const BADGE_ICON: Record<string, any> = {
  flame: Flame, book: BookOpen, check: Check, star: Star,
  calendar: Calendar, award: Award,
};

const BADGE_TONE: Record<string, string> = {
  amber: "bg-amber-100 text-amber-600",
  orange: "bg-orange-100 text-orange-500",
  red: "bg-red-100 text-red-500",
  emerald: "bg-emerald-100 text-emerald-600",
  teal: "bg-teal-100 text-teal-600",
  violet: "bg-violet-100 text-violet-600",
  sky: "bg-sky-100 text-sky-600",
  rose: "bg-rose-100 text-rose-500",
};

function money(n?: number | null) {
  if (!n) return "";
  return Math.round(n).toLocaleString("ru-RU").replace(/ /g, " ") + " so'm";
}

const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];
function periodLabel(p?: string | null) {
  if (!p || p.length < 7) return "";
  const m = Number(p.slice(5, 7));
  return MONTHS[m - 1] || p;
}

function discountText(r: RewardItem) {
  if (r.discount_percent) return `${r.discount_percent}% chegirma`;
  if (r.discount_amount) return `${money(r.discount_amount)} chegirma`;
  return "Chegirma";
}

/** Dizayndagidek bo'shliq bilan: 1 240 */
function coinNum(n: number) {
  return Math.round(n).toLocaleString("ru-RU").replace(/ /g, " ");
}

/**
 * MAHSULOT RASMI. Avval xodim yuklagan rasm (reward.image), bo'lmasa
 * nomiga qarab tayyor rasm topiladi - do'kon birinchi kundanoq
 * dizayndagidek to'la ko'rinadi. Hech biri bo'lmasa ikonka.
 */
const STOCK_IMG: { test: RegExp; src: string }[] = [
  { test: /daftar|bloknot|notebook/i, src: "/shop/daftar.png" },
  { test: /ruchka|qalam|pen/i, src: "/shop/ruchka.png" },
  { test: /mock|imtihon|test/i, src: "/shop/mock.png" },
  { test: /event|bilet|tadbir/i, src: "/shop/event.png" },
];
function rewardImage(r: RewardItem): string | null {
  if (r.image) return r.image;
  const hit = STOCK_IMG.find((s) => s.test.test(r.name));
  if (hit) return hit.src;
  if (r.kind === "discount") return null;
  return "/shop/gift.png";
}

export default function StudentShop() {
  const [d, setD] = useState<MyCoins | null>(null);
  const [err, setErr] = useState("");
  const [cat, setCat] = useState("");
  const [q, setQ] = useState("");
  const [params] = useSearchParams();
  const [view, setView] = useState<"shop" | "orders" | "badges" | "history">(
    params.get("tab") === "badges" ? "badges" : "shop"
  );
  const [ach, setAch] = useState<Ach | null>(null);
  const [ask, setAsk] = useState<RewardItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState("");

  function load() {
    api
      .fresh<MyCoins>("/me/coins")
      .then((r) => { setD(r); setErr(""); })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }
  useEffect(load, []);

  useEffect(() => {
    if (view === "badges" && !ach) {
      api.get<Ach>("/student/achievements").then(setAch).catch(() => {});
    }
  }, [view, ach]);

  async function buy(r: RewardItem) {
    setBusy(true);
    try {
      const res = await api.post<{ message?: string }>(`/me/rewards/${r.id}`);
      setAsk(null);
      setOk(res?.message || "Bajarildi");
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setAsk(null);
    } finally {
      setBusy(false);
    }
  }

  async function cancelOrder(id: number) {
    try {
      await api.delete(`/me/rewards/${id}`);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  const waiting = useMemo(
    () => (d ? d.orders.filter((o) => o.status === "requested") : []),
    [d]
  );

  if (err && !d)
    return <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>;

  const rewards = d.rewards.filter(
    (r) =>
      (!cat || r.category === cat) &&
      (!q.trim() || r.name.toLowerCase().includes(q.trim().toLowerCase()))
  );

  // Keyingi sovrin: balansdan qimmatroq eng arzoni - dizayndagi
  // "Yana 60 coin — yangi sovrin" chizig'i shundan chiqadi.
  const goal = d.next_goal;
  const goalLeft = goal ? Math.max(0, goal.cost - d.available) : 0;
  const goalPct = goal && goal.cost > 0
    ? Math.min(100, Math.round((d.available / goal.cost) * 100))
    : 100;

  /* ------------------------------------------------- mahsulot karta */
  const card = (r: RewardItem) => {
    const img = rewardImage(r);
    const can = d.available >= r.cost && r.in_stock;
    const badge =
      !r.in_stock ? { text: "Tugagan", cls: "bg-red-50 text-red-600" }
      : r.kind === "discount" && r.auto
        ? { text: "Darrov", cls: "bg-emerald-50 text-emerald-700" }
      : r.kind === "discount"
        ? { text: "Tasdiqlanadi", cls: "bg-amber-50 text-amber-700" }
      : null;
    return (
      <button
        key={r.id}
        onClick={() => can && setAsk(r)}
        className={`text-left bg-white rounded-2xl p-3 flex flex-col transition ${
          can ? "active:scale-[0.99]" : "opacity-60"
        }`}
        style={{ boxShadow: "0 1px 3px rgba(15,23,42,0.06)" }}
      >
        <div className="relative h-[104px] flex items-center justify-center">
          {badge && (
            <span
              className={`absolute top-0 right-0 px-2.5 py-1 rounded-full text-[11px] font-medium ${badge.cls}`}
            >
              {badge.text}
            </span>
          )}
          {img ? (
            <img
              src={img}
              alt=""
              className="max-h-[96px] max-w-full object-contain"
              loading="lazy"
            />
          ) : (
            <span className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Percent size={28} />
            </span>
          )}
        </div>

        <p className="text-[15px] font-semibold text-slate-900 mt-2 leading-tight">
          {r.name}
        </p>
        {r.kind === "discount" && r.period && (
          <p className="text-[11px] text-emerald-600 mt-0.5">
            {periodLabel(r.period)} to'loviga
          </p>
        )}

        <div className="flex items-end mt-2">
          <span className="flex items-center gap-1.5 flex-1 min-w-0">
            <CoinIcon size={17} />
            <b className="text-[17px] text-slate-900 leading-none">{r.cost}</b>
            <span className="text-xs text-slate-400 leading-none pb-[1px]">
              coin
            </span>
          </span>
          <span
            className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
              can ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-300"
            }`}
          >
            <ShoppingCart size={18} />
          </span>
        </div>
        {r.in_stock && !can && (
          <p className="text-[11px] text-amber-600 mt-1.5">
            Yana {r.cost - d.available} coin kerak
          </p>
        )}
      </button>
    );
  };

  /* --------------------------------------------------------- ekran */
  return (
    <div className="min-h-screen" style={{ background: "#F7FAFE" }}>
      <div className="max-w-md mx-auto px-4 pt-5 pb-6">
        {/* ----------------------------------------- sarlavha qatori */}
        <div className="flex items-start justify-between mb-4">
          {view === "shop" ? (
            <h1 className="text-[26px] font-extrabold text-slate-900 leading-tight">
              Coin do'koni
            </h1>
          ) : (
            <button
              onClick={() => setView("shop")}
              className="flex items-center gap-1.5 text-[17px] font-bold text-slate-900"
            >
              <ArrowLeft size={20} />
              {view === "orders" ? "Buyurtmalarim"
                : view === "history" ? "Coin tarixi" : "Yutuqlar"}
            </button>
          )}
          <button
            onClick={() => setView(view === "orders" ? "shop" : "orders")}
            className="relative shrink-0 text-slate-900"
            aria-label="Buyurtmalarim"
          >
            <ShoppingBag size={26} strokeWidth={1.8} />
            {waiting.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-[11px] h-[11px] rounded-full bg-brand-600 border-2 border-[#F7FAFE]" />
            )}
          </button>
        </div>

        {ok && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex gap-2.5 mb-3">
            <Check size={17} className="text-emerald-600 shrink-0 mt-0.5" />
            <p className="text-sm text-emerald-800 flex-1">{ok}</p>
            <button onClick={() => setOk("")} className="text-emerald-500">
              <X size={16} />
            </button>
          </div>
        )}
        {err && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3.5 flex gap-2.5 mb-3">
            <AlertCircle size={17} className="text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 flex-1">{err}</p>
            <button onClick={() => setErr("")} className="text-red-400">
              <X size={16} />
            </button>
          </div>
        )}

        {/* -------------------------------------- ko'k balans kartasi */}
        {view !== "badges" && (
          <div
            className="relative rounded-[20px] px-5 py-5 overflow-hidden"
            style={{ background: "#1A6EE4" }}
          >
            <img
              src="/shop/coins.png"
              alt=""
              className="absolute right-2 top-1/2 -translate-y-1/2 w-[168px] pointer-events-none select-none"
            />
            <div className="relative">
              <p className="text-[15px] text-white/90">Sizning balansingiz</p>
              <p className="mt-1 flex items-end gap-2">
                <span className="text-[42px] font-extrabold text-white leading-none">
                  {coinNum(d.available)}
                </span>
                <span className="text-white/85 text-[17px] pb-1">coin</span>
              </p>
              <button
                onClick={() => setView("history")}
                className="mt-3 flex items-center gap-1.5 text-white text-[15px] font-medium"
              >
                <span className="underline underline-offset-4">Coin tarixi</span>
                <ChevronRight size={17} />
              </button>
              {d.held > 0 && (
                <p className="text-[12px] text-white/75 mt-2">
                  {d.held} coin so'ralgan sovg'aga band qilingan
                </p>
              )}
              <div className="mt-5">
                <p className="text-[14px] text-white/90">
                  {goal
                    ? `Yana ${goalLeft} coin — ${goal.name}`
                    : "Barcha sovrinlar sizga yetadi"}
                </p>
                <div className="mt-2 h-2 rounded-full bg-white/30 w-[62%] overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${goalPct}%`, background: "#F5C518" }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================================================== DO'KON */}
        {view === "shop" && (
          <>
            {/* promo blok */}
            <div
              className="mt-4 rounded-[18px] px-5 py-4 flex items-center gap-2"
              style={{ background: "#EBF2FE" }}
            >
              <div className="min-w-0 flex-1">
                <p className="text-[17px] font-bold text-slate-900 leading-snug">
                  Coinlaringizni sovringa aylantiring
                </p>
                <p className="text-[13px] text-slate-500 mt-1.5 leading-snug">
                  Mashqlarni bajaring va ko'proq coin oling
                </p>
              </div>
              <img
                src="/shop/gift.png"
                alt=""
                className="w-[92px] shrink-0 -my-1"
              />
              <button
                onClick={() => setView("badges")}
                className="shrink-0 bg-brand-600 text-white rounded-xl px-4 py-3 text-[14px] font-semibold"
              >
                Coin yig'ish
              </button>
            </div>

            {/* qidiruv */}
            <div
              className="mt-4 bg-white rounded-2xl flex items-center gap-2.5 px-4 h-[52px]"
              style={{ boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}
            >
              <Search size={20} className="text-slate-400 shrink-0" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Sovrin qidiring"
                className="flex-1 min-w-0 text-[15px] text-slate-800 placeholder:text-slate-400 outline-none bg-transparent"
              />
              {q && (
                <button onClick={() => setQ("")} className="text-slate-300">
                  <X size={17} />
                </button>
              )}
            </div>

            {/* kategoriya chiplari */}
            <div className="mt-4 flex gap-2.5 overflow-x-auto pb-1 -mx-4 px-4">
              <button
                onClick={() => setCat("")}
                className={`shrink-0 px-5 py-2.5 rounded-full text-[15px] font-semibold transition ${
                  cat === ""
                    ? "bg-brand-600 text-white"
                    : "bg-white text-slate-600 border border-slate-200"
                }`}
              >
                Barchasi
              </button>
              {d.categories.map((c) => (
                <button
                  key={c.key}
                  onClick={() => setCat(c.key)}
                  className={`shrink-0 px-5 py-2.5 rounded-full text-[15px] font-semibold transition ${
                    cat === c.key
                      ? "bg-brand-600 text-white"
                      : "bg-white text-slate-600 border border-slate-200"
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>

            {/* bo'lim sarlavhasi */}
            <div className="mt-5 flex items-center">
              <h2 className="text-[21px] font-extrabold text-slate-900 flex-1">
                {cat || q ? "Sovrinlar" : "Mashhur sovrinlar"}
              </h2>
              {(cat || q) && (
                <button
                  onClick={() => { setCat(""); setQ(""); }}
                  className="flex items-center gap-0.5 text-[15px] font-semibold text-brand-600"
                >
                  Barchasi <ChevronRight size={17} />
                </button>
              )}
            </div>

            <div className="mt-3 grid grid-cols-2 gap-3">
              {rewards.map(card)}
            </div>
            {rewards.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-10">
                Bunday sovrin topilmadi
              </p>
            )}
          </>
        )}

        {/* =============================================== COIN TARIXI */}
        {view === "history" && (
          <div className="mt-4 space-y-2">
            {d.history.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-10">
                Hozircha yozuv yo'q
              </p>
            )}
            {d.history.map((h) => (
              <div
                key={h.id}
                className="bg-white rounded-2xl p-3.5 flex items-center gap-3"
                style={{ boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}
              >
                <span
                  className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 text-sm font-bold ${
                    h.amount >= 0
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-rose-50 text-rose-500"
                  }`}
                >
                  {h.amount >= 0 ? "+" : "−"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[14px] font-medium text-slate-800 truncate">
                    {h.note || h.source_label}
                  </p>
                  <p className="text-[12px] text-slate-400">
                    {h.date ? formatDate(h.date) : ""}
                  </p>
                </div>
                <span
                  className={`text-[15px] font-bold shrink-0 ${
                    h.amount >= 0 ? "text-emerald-600" : "text-rose-500"
                  }`}
                >
                  {h.amount >= 0 ? "+" : ""}
                  {h.amount}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* ============================================= BUYURTMALARIM */}
        {view === "orders" && (
          <div className="mt-4 space-y-2">
            {d.orders.length === 0 && (
              <div className="bg-white rounded-2xl p-8 text-center">
                <ShoppingBag size={28} className="mx-auto text-slate-300 mb-2" />
                <p className="text-sm text-slate-500">
                  Hali hech narsa olmagansiz
                </p>
              </div>
            )}
            {d.orders.map((o) => (
              <div
                key={o.id}
                className="bg-white rounded-2xl p-3.5"
                style={{ boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}
              >
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-900 flex-1 truncate">
                    {o.reward}
                  </p>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${
                      TONE[o.tone] || TONE.slate
                    }`}
                  >
                    {o.status_label}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                  <CoinIcon size={12} />
                  {o.coins} coin
                  {o.date && (
                    <>
                      <Clock size={11} className="ml-1 text-slate-400" />
                      {formatDate(o.date)}
                    </>
                  )}
                </p>
                {o.note && <p className="text-xs text-slate-500 mt-1">{o.note}</p>}
                {o.status === "requested" && (
                  <div className="mt-2.5 flex items-center gap-2">
                    <p className="text-[11px] text-amber-600 flex-1">
                      Administrator tasdiqlashini kutmoqda
                    </p>
                    <button
                      onClick={() => cancelOrder(o.id)}
                      className="text-[11px] text-slate-400 underline"
                    >
                      Bekor qilish
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ================================================== YUTUQLAR */}
        {view === "badges" && !ach && (
          <p className="text-sm text-slate-400 text-center py-10">Yuklanmoqda…</p>
        )}
        {view === "badges" && ach && (
          <div className="mt-4 space-y-4">
            <div
              className="bg-white rounded-2xl p-4"
              style={{ boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Flame size={18} className="text-orange-500" />
                <p className="text-sm font-bold text-slate-900 flex-1">
                  Uzluksiz mashq sovrinlari
                </p>
                <span className="text-sm font-bold text-orange-500">
                  {ach.streak} kun
                </span>
              </div>
              <div className="space-y-2">
                {ach.streak_rewards.map((r) => (
                  <div key={r.days} className="flex items-center gap-2.5">
                    <span
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        r.done
                          ? "bg-emerald-500 text-white"
                          : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {r.done ? <Check size={15} strokeWidth={3} /> : <Lock size={13} />}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-800">
                        {r.days} kun ketma-ket
                      </p>
                      <div className="h-1.5 rounded-full bg-slate-100 mt-1 overflow-hidden">
                        <div
                          className="h-full bg-orange-400 rounded-full"
                          style={{ width: `${r.percent}%` }}
                        />
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 text-sm font-bold text-slate-700 shrink-0">
                      <CoinIcon size={13} />
                      {r.coin}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-3">
                Sovrin ochilgach administrator coinni hisobingizga qo'shadi.
              </p>
            </div>

            {ach.next && (
              <div className="bg-brand-50 border border-brand-200 rounded-2xl p-3.5 flex items-center gap-3">
                <Target size={18} className="text-brand-600 shrink-0" />
                <p className="text-sm text-brand-800 flex-1">
                  Keyingi yutuq: <b>{ach.next.label}</b> — yana {ach.next.left} ta
                </p>
              </div>
            )}

            <div className="flex items-center gap-2 px-1">
              <Trophy size={16} className="text-brand-600" />
              <p className="text-[15px] font-bold text-slate-900 flex-1">Yutuqlar</p>
              <span className="text-sm text-slate-400">
                {ach.done}/{ach.total}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {ach.badges.map((b) => {
                const Icon = BADGE_ICON[b.icon] || Trophy;
                return (
                  <div
                    key={b.key}
                    className="rounded-2xl bg-white p-3.5"
                    style={{ boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}
                  >
                    <span
                      className={`w-11 h-11 rounded-full flex items-center justify-center ${
                        b.done
                          ? BADGE_TONE[b.tone] || BADGE_TONE.amber
                          : "bg-slate-100 text-slate-300"
                      }`}
                    >
                      <Icon size={20} />
                    </span>
                    <p
                      className={`text-sm font-bold mt-2 ${
                        b.done ? "text-slate-900" : "text-slate-400"
                      }`}
                    >
                      {b.label}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                      {b.hint}
                    </p>
                    {!b.done && (
                      <>
                        <div className="h-1.5 rounded-full bg-slate-100 mt-2 overflow-hidden">
                          <div
                            className="h-full bg-brand-500 rounded-full"
                            style={{ width: `${b.percent}%` }}
                          />
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1">
                          {b.have}/{b.target}
                        </p>
                      </>
                    )}
                    {b.done && (
                      <p className="text-[11px] text-emerald-600 font-semibold mt-2">
                        Ochildi
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ------------------------------------------- tasdiqlash oynasi */}
      {ask && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-end"
          onClick={() => !busy && setAsk(null)}
        >
          <div
            className="w-full max-w-md mx-auto bg-white rounded-t-3xl p-5 pb-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-3">
              {rewardImage(ask) ? (
                <img
                  src={rewardImage(ask)!}
                  alt=""
                  className="w-14 h-14 object-contain shrink-0"
                />
              ) : (
                <span className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                  {ask.kind === "discount" ? <Percent size={22} /> : <Gift size={22} />}
                </span>
              )}
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">{ask.name}</p>
                <p className="text-sm text-slate-500 flex items-center gap-1">
                  <CoinIcon size={13} />
                  {ask.cost} coin
                </p>
              </div>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed">
              {ask.kind === "discount" && ask.auto ? (
                <>
                  {discountText(ask)} <b>{periodLabel(ask.period)}</b> oyi
                  to'loviga hisoblanadi va balansingizda darrov ko'rinadi.
                  Hisobingizdan <b>{ask.cost} coin</b> yechiladi.
                </>
              ) : ask.kind === "discount" ? (
                <>
                  <b>{ask.cost} coin</b> band qilinadi va administratorga
                  so'rov boradi. Tasdiqlangach {discountText(ask)}{" "}
                  to'lovingizga hisoblanadi. Rad etilsa coin qaytadi.
                </>
              ) : (
                <>
                  <b>{ask.cost} coin</b> band qilinadi va administratorga
                  so'rov boradi. Sovg'ani qo'lga olganingizda coin yechiladi.
                  Rad etilsa coin qaytadi.
                </>
              )}
            </p>
            <p className="text-xs text-slate-400 mt-2">
              So'ngra qoladi: {d.available - ask.cost} coin
            </p>

            <div className="mt-5 flex gap-2">
              <button
                disabled={busy}
                onClick={() => setAsk(null)}
                className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 font-medium text-sm"
              >
                Bekor
              </button>
              <button
                disabled={busy}
                onClick={() => buy(ask)}
                className="flex-1 py-3 rounded-xl bg-brand-600 text-white font-semibold text-sm disabled:opacity-60"
              >
                {busy ? "..." : ask.kind === "discount" && ask.auto
                  ? "Sotib olish" : "So'rash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
