import { useEffect, useState } from "react";
import {
  Coins, Gift, Check, X, Target, TrendingUp, Clock, Sparkles,
} from "lucide-react";
import { api, type MyCoins as Data, type RewardItem } from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, { chip: string; ring: string }> = {
  teal: { chip: "bg-teal-100 text-teal-700", ring: "border-teal-200" },
  sky: { chip: "bg-sky-100 text-sky-700", ring: "border-sky-200" },
  emerald: { chip: "bg-emerald-100 text-emerald-700", ring: "border-emerald-200" },
  violet: { chip: "bg-violet-100 text-violet-700", ring: "border-violet-200" },
  slate: { chip: "bg-slate-100 text-slate-600", ring: "border-slate-200" },
  amber: { chip: "bg-amber-100 text-amber-700", ring: "border-amber-200" },
  red: { chip: "bg-red-100 text-red-700", ring: "border-red-200" },
};

/**
 * O'quvchining coin kabineti. Kirgan zahoti balansini ko'radi va
 * shu coinga qaysi sovg'ani olishi mumkinligini biladi.
 */
export default function MyCoins() {
  const [d, setD] = useState<Data | null>(null);
  const [cat, setCat] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<"shop" | "history" | "orders">("shop");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    setErr("");
    api
      .get<Data>("/me/coins")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"))
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (err)
    return (
      <div className="max-w-lg py-10">
        <p className="text-sm text-slate-600">{err}</p>
      </div>
    );
  if (!d) return null;

  const rewards = cat
    ? d.rewards.filter((r) => r.category === cat)
    : d.rewards;
  const pending = d.orders.filter((o) => o.status === "requested");

  async function buy(r: RewardItem) {
    if (
      !confirm(
        `"${r.name}" — ${r.cost} coin.\n\nSo'ralgach coin band qilinadi, ` +
          `sovg'ani markazdan olib ketasiz. Rozimisiz?`
      )
    )
      return;
    try {
      const res = await api.post<{ message: string }>(`/me/rewards/${r.id}`, {});
      setMsg(res.message);
      setErr("");
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setMsg("");
    }
  }

  return (
    <div className="max-w-5xl">
      {/* --- Balans --- */}
      <div className="bg-gradient-to-br from-brand-600 to-brand-700 rounded-2xl p-6 mb-5 text-white">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-brand-100 mb-1">
              {d.full_name}
              {d.group ? ` · ${d.group}` : ""}
            </p>
            <div className="flex items-baseline gap-2">
              <Coins size={28} className="text-amber-300" />
              <span className="text-5xl font-bold">{d.available}</span>
              <span className="text-lg text-brand-100">coin</span>
            </div>
            {d.held > 0 && (
              <p className="text-xs text-brand-100 mt-1.5">
                {d.held} coin band qilingan ({pending.length} ta so'rov
                kutilmoqda)
              </p>
            )}
          </div>
          <div className="text-right text-sm">
            <p className="text-brand-100">Jami yig'gan</p>
            <p className="text-xl font-semibold">{d.earned}</p>
            <p className="text-brand-100 mt-2">Sarflagan</p>
            <p className="text-xl font-semibold">{d.spent}</p>
          </div>
        </div>

        {d.next_goal && (
          <div className="mt-4 pt-4 border-t border-white/20">
            <div className="flex items-center gap-2 mb-1.5">
              <Target size={14} className="text-amber-300" />
              <p className="text-sm">
                Keyingi maqsad:{" "}
                <span className="font-semibold">{d.next_goal.name}</span> —
                yana {d.next_goal.need_more} coin
              </p>
            </div>
            <div className="h-2 rounded-full bg-white/20 overflow-hidden">
              <div
                className="h-full rounded-full bg-amber-300"
                style={{
                  width: `${(d.available / d.next_goal.cost) * 100}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {msg && (
        <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-4 py-3 mb-4 flex items-start gap-2">
          <Sparkles size={15} className="mt-0.5 shrink-0" />
          {msg}
        </p>
      )}
      {err && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-3 mb-4">
          {err}
        </p>
      )}

      {/* --- Tablar --- */}
      <div className="flex gap-1 mb-4">
        {[
          { k: "shop", l: "Sovg'alar" },
          { k: "orders", l: `Mening so'rovlarim${pending.length ? ` (${pending.length})` : ""}` },
          { k: "history", l: "Coin tarixi" },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setTab(t.k as "shop" | "history" | "orders")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
              tab === t.k
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {t.l}
          </button>
        ))}
      </div>

      {/* ------------------------------------------------ Sovg'alar */}
      {tab === "shop" && (
        <>
          <div className="flex flex-wrap gap-1.5 mb-4">
            <button
              onClick={() => setCat("")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                !cat
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              Hammasi ({d.rewards.length})
            </button>
            {d.categories.map((c) => {
              const n = d.rewards.filter((r) => r.category === c.key).length;
              if (!n) return null;
              return (
                <button
                  key={c.key}
                  onClick={() => setCat(cat === c.key ? "" : c.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                    cat === c.key
                      ? "bg-brand-50 border-brand-400 text-brand-700"
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {c.label} ({n})
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {rewards.map((r) => {
              const t = TONE[r.tone] || TONE.slate;
              return (
                <div
                  key={r.id}
                  className={`bg-white rounded-xl border p-4 flex flex-col ${
                    r.affordable ? "border-brand-300" : "border-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${t.chip}`}
                    >
                      {r.category_label}
                    </span>
                    {!r.in_stock && (
                      <span className="text-[10px] text-red-600">tugagan</span>
                    )}
                  </div>

                  <p className="text-sm font-medium text-slate-900 mb-1 flex-1">
                    {r.name}
                  </p>

                  <div className="flex items-center gap-1.5 mb-3">
                    <Coins size={14} className="text-amber-500" />
                    <span className="text-lg font-bold text-slate-900">
                      {r.cost}
                    </span>
                  </div>

                  {r.affordable && r.in_stock ? (
                    <button
                      onClick={() => buy(r)}
                      className="w-full py-2 rounded-lg bg-brand-600 text-white text-xs font-medium hover:bg-brand-700 flex items-center justify-center gap-1.5"
                    >
                      <Gift size={13} /> Olish
                    </button>
                  ) : (
                    <div className="w-full py-2 rounded-lg bg-slate-50 text-center">
                      <p className="text-xs text-slate-400">
                        {!r.in_stock
                          ? "Hozircha yo'q"
                          : `Yana ${r.need_more} coin`}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* ------------------------------------------- Mening so'rovlarim */}
      {tab === "orders" &&
        (d.orders.length === 0 ? (
          <p className="text-sm text-slate-400 py-10 text-center">
            Hali sovg'a so'ramagansiz.
          </p>
        ) : (
          <div className="space-y-2">
            {d.orders.map((o) => (
              <div
                key={o.id}
                className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3"
              >
                <Gift size={16} className="text-slate-400 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-900">
                    {o.reward}
                  </p>
                  <p className="text-xs text-slate-400">
                    {o.date ? formatDate(o.date) : ""}
                    {o.given_at ? ` · berilgan ${formatDate(o.given_at)}` : ""}
                    {o.note ? ` · ${o.note}` : ""}
                  </p>
                </div>
                <span className="text-sm text-slate-600 shrink-0">
                  {o.coins} coin
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${
                    (TONE[o.tone] || TONE.slate).chip
                  }`}
                >
                  {o.status_label}
                </span>
                {o.status === "requested" && (
                  <button
                    onClick={async () => {
                      if (!confirm("So'rov bekor qilinsinmi?")) return;
                      await api.delete(`/me/rewards/${o.id}`);
                      load();
                    }}
                    title="Bekor qilish"
                    className="p-1.5 rounded-md text-slate-300 hover:text-red-600 shrink-0"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        ))}

      {/* ------------------------------------------------ Coin tarixi */}
      {tab === "history" &&
        (d.history.length === 0 ? (
          <p className="text-sm text-slate-400 py-10 text-center">
            Hali coin yig'ilmagan.
          </p>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-50">
            {d.history.map((h) => (
              <div key={h.id} className="flex items-center gap-3 px-4 py-2.5">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                    h.amount > 0
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {h.amount > 0 ? (
                    <TrendingUp size={13} />
                  ) : (
                    <Gift size={13} />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-slate-800">{h.source_label}</p>
                  {h.note && (
                    <p className="text-xs text-slate-400">{h.note}</p>
                  )}
                </div>
                <span className="text-xs text-slate-400 shrink-0">
                  {h.date ? formatDate(h.date) : ""}
                </span>
                <span
                  className={`text-sm font-semibold w-16 text-right shrink-0 ${
                    h.amount > 0 ? "text-emerald-600" : "text-slate-500"
                  }`}
                >
                  {h.amount > 0 ? "+" : ""}
                  {h.amount}
                </span>
              </div>
            ))}
          </div>
        ))}
    </div>
  );
}

/** Xodimlar uchun: o'quvchilar so'ragan sovg'alar navbati. */
export function RewardRequestsTab() {
  const [d, setD] = useState<import("../lib/api").RewardRequests | null>(null);
  const [filter, setFilter] = useState("requested");

  function load() {
    api
      .get<import("../lib/api").RewardRequests>(
        `/rewards/requests?status_filter=${filter}`
      )
      .then(setD);
  }
  useEffect(load, [filter]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {d.statuses.map((s) => (
          <button
            key={s.key}
            onClick={() => setFilter(s.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
              filter === s.key
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          {filter === "requested"
            ? "Kutayotgan so'rov yo'q."
            : "Yozuv yo'q."}
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <div
              key={r.id}
              className="bg-white rounded-xl border border-slate-200 p-4 flex flex-wrap items-center gap-3"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-slate-900">
                    {r.student}
                  </span>
                  {r.group && (
                    <span className="text-xs text-slate-400">{r.group}</span>
                  )}
                  {r.by_student && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-sky-100 text-sky-700">
                      o'zi so'radi
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-600 mt-0.5 flex items-center gap-1.5">
                  <Gift size={13} className="text-slate-400" />
                  {r.reward}
                  <span className="text-xs text-slate-400">
                    · {r.coins} coin
                  </span>
                </p>
              </div>

              <span className="text-xs text-slate-400 shrink-0 flex items-center gap-1">
                <Clock size={11} />
                {r.date ? formatDate(r.date) : ""}
              </span>

              {r.status === "requested" ? (
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={async () => {
                      await api.post(`/rewards/requests/${r.id}/give`, {
                        give: true,
                      });
                      load();
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700"
                  >
                    <Check size={13} /> Berildi
                  </button>
                  <button
                    onClick={async () => {
                      const note = prompt("Rad etish sababi?");
                      if (note === null) return;
                      await api.post(`/rewards/requests/${r.id}/give`, {
                        give: false,
                        note,
                      });
                      load();
                    }}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50"
                  >
                    <X size={15} />
                  </button>
                </div>
              ) : (
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${
                    (TONE[r.tone] || TONE.slate).chip
                  }`}
                >
                  {r.status_label}
                  {r.given_by ? ` · ${r.given_by}` : ""}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
