import { useEffect, useState } from "react";
import {
  Gift, Percent, Clock, Check, X, ShoppingBag, Target, AlertCircle,
} from "lucide-react";
import { CoinIcon } from "../../components/CoinIcon";
import { formatDate } from "../../lib/format";
import { api, type MyCoins, type RewardItem } from "../../lib/api";

/**
 * JONY STUDENT — DO'KON (2026-08-16).
 *
 * Jahongir: "ichida Do'konni qoshmabmiz nega coin yigyabdi nimadur
 * sotib olishi kerakku, sotib olgandan keyin masalan skidka sotib
 * olsa avtomat hisobiga ishlasin ... sovga yutib olsa adminlarga
 * vazifa bolib borsin falonchi coinga shu narsa olmoqchi deb".
 *
 * Do'kon xodimlar panelida (MyCoins.tsx) allaqachon bor edi, lekin
 * o'quvchi ilovasiga (/student) ulanmagan ekan — o'quvchi coin
 * yig'ardi-yu, sarflay olmasdi. Shu bo'shliq to'ldirildi.
 *
 * Ikki xil mahsulot bir joyda, lekin ATAYLAB ajratib ko'rsatilgan:
 *
 *   CHEGIRMA — odam aralashmaydi. Bosildi = coin yechildi, chegirma
 *   to'lovga tushdi. 15-kungacha olinsa shu oyga, keyin olinsa
 *   keyingi oyga (server hal qiladi, oy nomi kartada yozib turadi).
 *
 *   SOVG'A — qo'lga beriladi, ya'ni odam kerak. Coin BAND qilinadi,
 *   administratorga vazifa boradi; u "Berildi" bosgandagina coin
 *   yechiladi. Rad etilsa coin qaytadi.
 *
 * Shuning uchun tugma matni ham har xil: "Sotib olish" ↔ "So'rash".
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

function money(n?: number | null) {
  if (!n) return "";
  return Math.round(n).toLocaleString("ru-RU").replace(/ /g, " ") + " so'm";
}

const MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];
/** "2026-09" -> "Sentabr" */
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

export default function StudentShop() {
  const [d, setD] = useState<MyCoins | null>(null);
  const [err, setErr] = useState("");
  const [cat, setCat] = useState("");
  const [tab, setTab] = useState<"shop" | "orders">("shop");
  const [ask, setAsk] = useState<RewardItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState("");

  function load() {
    api
      .fresh<MyCoins>("/me/coins")
      .then((r) => {
        setD(r);
        setErr("");
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }
  useEffect(load, []);

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

  if (err && !d)
    return (
      <p className="text-sm text-slate-500 text-center py-20 px-6">{err}</p>
    );
  if (!d)
    return (
      <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>
    );

  const rewards = cat ? d.rewards.filter((r) => r.category === cat) : d.rewards;
  const discounts = rewards.filter((r) => r.kind === "discount");
  const gifts = rewards.filter((r) => r.kind !== "discount");
  const waiting = d.orders.filter((o) => o.status === "requested");

  const card = (r: RewardItem) => {
    const isDisc = r.kind === "discount";
    const can = d.available >= r.cost && r.in_stock;
    return (
      <button
        key={r.id}
        disabled={!can}
        onClick={() => setAsk(r)}
        className={`w-full text-left bg-white rounded-xl border p-3.5 flex items-center gap-3 transition ${
          can
            ? "border-slate-200 active:scale-[0.99] active:border-brand-300"
            : "border-slate-100 opacity-60"
        }`}
      >
        <div
          className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
            isDisc
              ? "bg-emerald-50 text-emerald-600"
              : "bg-violet-50 text-violet-600"
          }`}
        >
          {isDisc ? <Percent size={20} /> : <Gift size={20} />}
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-900 truncate">
            {r.name}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {isDisc ? (
              <>
                {discountText(r)}
                {r.period && (
                  <span className="text-emerald-600">
                    {" · "}
                    {periodLabel(r.period)} to'loviga
                  </span>
                )}
              </>
            ) : (
              <span
                className={`px-1.5 py-0.5 rounded ${TONE[r.tone] || TONE.slate}`}
              >
                {r.category_label}
              </span>
            )}
          </p>
          {!r.in_stock && (
            <p className="text-[11px] text-red-500 mt-1">Tugagan</p>
          )}
          {r.in_stock && !can && (
            <p className="text-[11px] text-amber-600 mt-1">
              Yana {r.cost - d.available} coin kerak
            </p>
          )}
        </div>

        <span className="shrink-0 inline-flex items-center gap-1 font-bold text-slate-900">
          <CoinIcon size={15} />
          {r.cost}
        </span>
      </button>
    );
  };

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-7 pb-12">
        <div className="max-w-md mx-auto">
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <ShoppingBag size={19} />
            Jony Shop
          </h1>
          <div className="mt-4 flex items-end gap-2">
            <CoinIcon size={30} />
            <span className="text-4xl font-bold leading-none">
              {d.available}
            </span>
            <span className="text-white/70 text-sm pb-0.5">coin</span>
          </div>
          {d.held > 0 && (
            <p className="text-xs text-white/70 mt-2">
              {d.held} coin so'ralgan sovg'aga band qilingan
            </p>
          )}
          {d.next_goal && (
            <p className="text-xs text-white/80 mt-2 flex items-center gap-1.5">
              <Target size={12} />
              Keyingi maqsad: {d.next_goal.name} —{" "}
              {d.next_goal.cost - d.available} coin qoldi
            </p>
          )}
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 pb-8 space-y-4">
        {ok && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex gap-2.5">
            <Check size={17} className="text-emerald-600 shrink-0 mt-0.5" />
            <p className="text-sm text-emerald-800 flex-1">{ok}</p>
            <button onClick={() => setOk("")} className="text-emerald-500">
              <X size={16} />
            </button>
          </div>
        )}
        {err && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3.5 flex gap-2.5">
            <AlertCircle size={17} className="text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 flex-1">{err}</p>
            <button onClick={() => setErr("")} className="text-red-400">
              <X size={16} />
            </button>
          </div>
        )}

        <div className="bg-white rounded-xl border border-slate-200 p-1 grid grid-cols-2 gap-1">
          {(
            [
              ["shop", "Do'kon"],
              [
                "orders",
                `Buyurtmalarim${waiting.length ? ` (${waiting.length})` : ""}`,
              ],
            ] as const
          ).map(([k, l]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`py-2 rounded-lg text-sm font-medium transition ${
                tab === k ? "bg-brand-600 text-white" : "text-slate-500"
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        {tab === "shop" && (
          <>
            <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
              <button
                onClick={() => setCat("")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border whitespace-nowrap ${
                  cat === ""
                    ? "bg-brand-50 border-brand-400 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500"
                }`}
              >
                Hammasi
              </button>
              {d.categories.map((c) => (
                <button
                  key={c.key}
                  onClick={() => setCat(c.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border whitespace-nowrap ${
                    cat === c.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500"
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>

            {discounts.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide px-1">
                  To'lovga chegirma
                </p>
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-3.5 py-2.5">
                  <p className="text-[12px] text-emerald-800 leading-snug">
                    Chegirma darrov ishlaydi — coin yechiladi va to'lov
                    hisobingiz o'zi kamayadi. Oyning <b>15-kunigacha</b>{" "}
                    olsangiz shu oyga, keyinroq olsangiz keyingi oyga tushadi.
                  </p>
                </div>
                {discounts.map(card)}
              </div>
            )}

            {gifts.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide px-1">
                  Sovg'alar
                </p>
                {gifts.map(card)}
              </div>
            )}

            {rewards.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-10">
                Bu bo'limda hozircha narsa yo'q
              </p>
            )}
          </>
        )}

        {tab === "orders" && (
          <div className="space-y-2">
            {d.orders.length === 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
                <ShoppingBag size={28} className="mx-auto text-slate-300 mb-2" />
                <p className="text-sm text-slate-500">
                  Hali hech narsa olmagansiz
                </p>
              </div>
            )}
            {d.orders.map((o) => (
              <div
                key={o.id}
                className="bg-white rounded-xl border border-slate-200 p-3.5"
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
                {o.note && (
                  <p className="text-xs text-slate-500 mt-1">{o.note}</p>
                )}
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
      </div>

      {ask && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-end"
          onClick={() => !busy && setAsk(null)}
        >
          <div
            className="w-full max-w-md mx-auto bg-white rounded-t-2xl p-5 pb-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-3">
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center ${
                  ask.kind === "discount"
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-violet-50 text-violet-600"
                }`}
              >
                {ask.kind === "discount" ? (
                  <Percent size={20} />
                ) : (
                  <Gift size={20} />
                )}
              </div>
              <div className="min-w-0">
                <p className="font-semibold text-slate-900">{ask.name}</p>
                <p className="text-sm text-slate-500 flex items-center gap-1">
                  <CoinIcon size={13} />
                  {ask.cost} coin
                </p>
              </div>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed">
              {ask.kind === "discount" ? (
                <>
                  {discountText(ask)} <b>{periodLabel(ask.period)}</b> oyi
                  to'loviga hisoblanadi va balansingizda darrov ko'rinadi.
                  Hisobingizdan <b>{ask.cost} coin</b> yechiladi.
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
                {busy
                  ? "..."
                  : ask.kind === "discount"
                  ? "Sotib olish"
                  : "So'rash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
