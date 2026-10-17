import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { BadgeCheck, Crown, Flag, Info, Medal } from "lucide-react";
import { StudentLoading } from "../StudentLoading";
import { JSA } from "../Jsa";
import { formatDate } from "../../lib/format";
import { fmtNum } from "../../lib/studentApi";
import {
  getWordBoard,
  type WbBoard,
  type WbBoardRow,
  type WbFirstFinisher,
  type WbPeriod,
  type WbQuiet,
  type WbScope,
} from "../../lib/wordbankApi";
import { pickPref, readPref, writePref } from "../../lib/wordbankUi";

/**
 * "SO'Z BILISH" REYTINGI (2026-10-17, OWNER D2/D4/D5).
 *
 * Tasdiqlangan so'zlar soni bo'yicha: Guruhim / Filialim / Umumiy va
 * Jami / Shu hafta / Tarix. Hisob-kitob to'liq serverda
 * (GET /api/wordbank/leaderboard) — bu yerda faqat ko'rsatish.
 *   * Ismlar server tomonda yashirilgan ("Aziz K."), rasm yo'q —
 *     faqat bosh harflar.
 *   * Sertifikat belgisi — FAQAT tasdiqlangani; o'ringa ta'sir qilmaydi.
 *   * "tekshirilmoqda" — faqat belgi, coin yoki o'ringa ta'sir qilmaydi.
 *   * Sovrin YO'Q — bu reyting motivatsiya uchun.
 * Bo'lim yopiq bo'lsa (404) onOff() chaqiriladi — tab yashiriladi.
 */

const SCOPES: readonly [WbScope, string][] = [
  ["group", "Guruhim"], ["branch", "Filialim"], ["school", "Umumiy"],
];
const PERIODS: readonly [WbPeriod, string][] = [
  ["total", "Jami"], ["week", "Shu hafta"], ["history", "Tarix"],
];
const SCOPE_KEYS = SCOPES.map(([k]) => k);
const PERIOD_KEYS = PERIODS.map(([k]) => k);

const K_SCOPE = "jony_wb_scope";
const K_PERIOD = "jony_wb_period";
const K_GROUP = "jony_wb_group";

const SUBTITLE: Record<WbPeriod, string> = {
  total: "Tasdiqlangan so'zlar bo'yicha",
  week: "Shu haftada tasdiqlangan so'zlar",
  history: "Eng yaxshi natijalar — hech qachon o'chmaydi",
};

export function WordBoard({ onOff }: { onOff: () => void }) {
  const [scope, setScope] = useState<WbScope>(() => pickPref(K_SCOPE, SCOPE_KEYS, "group"));
  const [period, setPeriod] = useState<WbPeriod>(() => pickPref(K_PERIOD, PERIOD_KEYS, "total"));
  const [groupId, setGroupId] = useState<number | null>(() => Number(readPref(K_GROUP)) || null);
  const [res, setRes] = useState<WbQuiet<WbBoard> | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getWordBoard({ scope, period, group_id: scope === "group" ? groupId : null }).then((r) => {
      if (!alive) return;
      // Saqlangan guruh endi o'quvchiniki emas (ko'chirilgan) — asosiy
      // guruhga qaytamiz, xato ko'rsatmaymiz. 2026-10-17 (review): FAQAT
      // server guruhni rad etganda (403 "Bu guruh sizniki emas" / 400) —
      // internet uzilishi yoki 500 tanlovni o'chirib yubormasin.
      if (r.status === "error" && (r.code === 403 || r.code === 400)
          && scope === "group" && groupId) {
        writePref(K_GROUP, null);
        setGroupId(null);
        return;
      }
      setLoading(false);
      if (r.status === "off") {
        onOff();
        return;
      }
      setRes(r);
    });
    return () => {
      alive = false;
    };
  }, [scope, period, groupId, tick, onOff]);

  const chooseScope = (s: WbScope) => {
    setScope(s);
    writePref(K_SCOPE, s);
  };
  const choosePeriod = (p: WbPeriod) => {
    setPeriod(p);
    writePref(K_PERIOD, p);
  };
  const chooseGroup = (id: number) => {
    setGroupId(id);
    writePref(K_GROUP, String(id));
  };

  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  const d = res?.status === "ok" ? res.data : null;
  const meInRows = !!d?.rows.some((r) => r.is_me);
  const activeGroup = d?.group_id ?? groupId;

  return (
    <div>
      <p className="text-[15px] text-slate-400 mt-2">{SUBTITLE[period]}</p>

      {/* ------------------------------------------------ tablar */}
      <div className="rounded-2xl border p-2 mt-4 space-y-2" style={card}>
        <div className="grid grid-cols-3 gap-1.5" role="tablist" aria-label="Qamrov">
          {SCOPES.map(([k, l]) => (
            <button key={k} type="button" role="tab" aria-selected={scope === k}
              onClick={() => chooseScope(k)}
              className={`py-2.5 rounded-xl text-[15px] font-bold transition ${
                scope === k ? "bg-brand-600 text-white" : "text-slate-300"}`}>
              {l}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-1.5" role="tablist" aria-label="Davr">
          {PERIODS.map(([k, l]) => (
            <button key={k} type="button" role="tab" aria-selected={period === k}
              onClick={() => choosePeriod(k)}
              className={`py-2.5 rounded-xl text-[15px] font-bold transition ${
                period === k ? "bg-brand-600 text-white" : "text-slate-300"}`}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* 2+ guruhda o'qisa — guruh tanlagichi */}
      {scope === "group" && d && d.groups.length >= 2 && (
        <div className="flex flex-wrap gap-1.5 mt-3" aria-label="Guruh">
          {d.groups.map((g) => (
            <button key={g.id} type="button" onClick={() => chooseGroup(g.id)}
              aria-pressed={activeGroup === g.id}
              className={`px-3 min-h-[36px] rounded-full text-[13px] font-bold border max-w-full truncate ${
                activeGroup === g.id
                  ? "bg-white text-slate-900 border-white"
                  : "text-slate-300 border-slate-600"}`}>
              {g.name}
            </button>
          ))}
        </div>
      )}

      {res?.status === "error" && (
        <div className="rounded-2xl border p-4 mt-4 text-center" style={card}>
          <p className="text-sm text-red-300">{res.message}</p>
          <button type="button" onClick={() => setTick((t) => t + 1)}
            className="mt-3 px-5 min-h-[44px] rounded-xl bg-brand-600 text-white text-sm font-bold">
            Qayta urinish
          </button>
        </div>
      )}
      {!res && loading && <StudentLoading />}

      <div className={loading && res ? "opacity-60 transition-opacity" : "transition-opacity"}>
        {/* ------------------------------------------- bo'sh holat */}
        {/* Guruh / filial yo'q — boshqa qamrovni taklif qilamiz
            (mashq tugmasi bu yerda ma'nosiz edi, 2026-10-17) */}
        {d?.hint && (
          <div className="rounded-2xl border p-5 mt-4 text-center" style={card}>
            <p className="text-sm text-slate-300">{d.hint}</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {SCOPES.filter(([k]) => k !== scope).map(([k, l]) => (
                <button key={k} type="button" onClick={() => chooseScope(k)}
                  className="inline-flex items-center min-h-[44px] px-5 rounded-xl bg-brand-600 text-white text-sm font-semibold">
                  {l}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ------------------------------- SIZNING O'RNINGIZ (oq) */}
        {d && !d.hint && d.me && <MeCard d={d} me={d.me} period={period} />}

        {/* ---------------------------- birinchi tugatganlar (Tarix) */}
        {d && !d.hint && period === "history" && <FirstFinishers list={d.first_finishers} />}

        {/* -------------------------------------- REYTING JADVALI */}
        {d && !d.hint && d.rows.length > 0 && (
          <ol className="mt-4 space-y-2" aria-label="So'z bilish reytingi">
            {d.rows.map((r, i) => (
              <BoardRow key={`${r.rank}-${i}`} r={r} period={period} scope={scope} />
            ))}
          </ol>
        )}

        {d && !d.hint && d.rows.length === 0 && (
          <div className="rounded-2xl border p-5 mt-4 text-center" style={card}>
            <p className="text-sm text-slate-300">
              {period === "week"
                ? "Shu hafta hali hech kim so'z tasdiqlamagan — birinchi bo'ling!"
                : "Hali hech kim so'z tasdiqlamagan — birinchi bo'ling!"}
            </p>
            <Link to="/student/words/practice"
              className="mt-4 inline-flex items-center min-h-[44px] px-5 rounded-xl bg-brand-600 text-white text-sm font-semibold">
              Mashqni boshlash
            </Link>
          </div>
        )}

        {/* O'z qatoringiz TOP 50 dan tashqarida — pastda qotib turadi */}
        {d && !d.hint && d.me && !meInRows && d.rows.length > 0 && (
          <div className="sticky z-10 mt-2"
               style={{ bottom: "calc(80px + env(safe-area-inset-bottom, 0px))" }}>
            <BoardRow r={d.me} period={period} scope={scope} pinned />
          </div>
        )}

        {d && !d.hint && (
          <p className="text-[12.5px] text-slate-400 flex items-start gap-2 mt-4 px-1 leading-snug">
            <Info size={14} className="shrink-0 mt-0.5" />
            <span>
              {period === "week"
                ? `Shu hafta (${formatDate(d.week_start)} dushanbadan beri) tasdiqlangan yangi so'zlar soni.`
                : period === "history"
                  ? "Har bir o'quvchining eng yaxshi natijasi — bitirgan va ketgan o'quvchilar ham shu yerda qoladi."
                  : "Reyting tasdiqlangan so'zlar soni bo'yicha. Sertifikat belgisi o'ringa ta'sir qilmaydi."}
              {" "}«tekshirilmoqda» — natija tekshirilayotganini bildiradi.
            </span>
          </p>
        )}
      </div>
    </div>
  );
}

/** Asosiy son: Shu hafta — haftalik o'sish, qolganida — tasdiqlangan son. */
function metricOf(r: WbBoardRow, period: WbPeriod) {
  return period === "week" ? r.week_gain : r.known;
}

function MeCard({ d, me, period }: { d: WbBoard; me: WbBoardRow; period: WbPeriod }) {
  const first = me.rank === 1;
  const metric = metricOf(me, period);
  let line: ReactNode;
  if (first) {
    line = <>Siz <b>1-o'rindasiz!</b> Shu holatni saqlang 🏆</>;
  } else if (me.rank === null) {
    line = period === "week"
      ? <>Shu hafta <b>1 ta</b> so'z tasdiqlasangiz — reytingga kirasiz</>
      : <>Reytingga kirish uchun <b>1 ta</b> so'z tasdiqlang</>;
  } else if (d.gap_to_next !== null) {
    line = <>Keyingi o'ringa <b>{fmtNum(d.gap_to_next)} ta so'z</b></>;
  } else {
    line = <>Mashqni davom ettiring</>;
  }
  return (
    <div className="student-panel bg-white rounded-3xl p-4 mt-4">
      <div className="flex items-baseline gap-2 mb-3">
        <p className="text-[17px] font-extrabold text-slate-900 flex-1">Sizning o'rningiz</p>
        {d.total > 0 && (
          <p className="text-[12px] text-slate-500 shrink-0">{fmtNum(d.total)} o'quvchidan</p>
        )}
      </div>
      <div className="rounded-2xl border border-slate-100 bg-slate-50/60 p-3">
        <div className="flex items-center gap-2.5">
          <span className="text-[24px] font-extrabold text-brand-600 min-w-[28px] text-center shrink-0 tabular-nums">
            {me.rank ?? "—"}
          </span>
          <Initials text={me.initials} me size={44} />
          <div className="flex-1 min-w-0">
            <p className="text-[13px] text-slate-600 leading-snug">{line}</p>
            <p className="text-[12px] text-slate-500 mt-0.5">
              {period === "week" ? (
                <>Shu hafta: <b className="text-emerald-700">+{fmtNum(metric)}</b> · jami {fmtNum(me.known)}</>
              ) : period === "history" ? (
                <>Eng yaxshi natija: <b className="text-slate-800">{fmtNum(metric)}</b></>
              ) : (
                <>
                  <b className="text-slate-800">{fmtNum(metric)}</b> ta so'z
                  {me.week_gain > 0 && <span className="text-emerald-700 font-bold"> · ▲{fmtNum(me.week_gain)}</span>}
                </>
              )}
            </p>
          </div>
          <Link to="/student/words/practice"
            className="px-3.5 min-h-[44px] inline-flex items-center rounded-xl bg-brand-600 text-white text-[13px] font-bold shrink-0">
            Mashq
          </Link>
        </div>
      </div>
    </div>
  );
}

function FirstFinishers({ list }: { list: WbFirstFinisher[] }) {
  const card = { background: JSA.card, borderColor: JSA.cardBorder };
  return (
    <div className="rounded-2xl border p-3.5 mt-4" style={card}>
      <p className="text-[15px] font-extrabold text-white flex items-center gap-2">
        <Medal size={17} className="text-amber-400" /> Birinchi bo'lib tugatganlar
      </p>
      {list.length === 0 ? (
        <p className="text-[12.5px] text-slate-400 mt-1.5 leading-snug">
          Hali hech kim daraja tugatmagan — Common 1000 ni birinchi bo'lib siz
          tugating!
        </p>
      ) : (
        <ul className="grid grid-cols-2 gap-2 mt-2.5">
          {list.map((f) => (
            <li key={f.band}
                className={`rounded-xl p-2.5 flex items-center gap-2 min-w-0 ${
                  f.is_me ? "bg-brand-600/40 ring-1 ring-sky-400" : "bg-white/5"}`}>
              <Initials text={f.initials} me={f.is_me} size={32} />
              <div className="min-w-0">
                <p className="text-[11px] font-extrabold text-amber-300 truncate">{f.label}</p>
                <p className="text-[13px] font-semibold text-white truncate">{f.is_me ? "Siz" : f.name}</p>
                {f.at && <p className="text-[10.5px] text-slate-400">{formatDate(f.at)}</p>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function BoardRow({
  r,
  period,
  scope,
  pinned = false,
}: {
  r: WbBoardRow;
  period: WbPeriod;
  scope: WbScope;
  pinned?: boolean;
}) {
  const metric = metricOf(r, period);
  // Qamrovning o'zi ko'rinib turgan ma'lumot takrorlanmaydi
  const where = [scope !== "group" ? r.group : null, scope === "school" ? r.branch : null]
    .filter(Boolean)
    .join(" · ");
  const style = r.is_me
    ? { background: "#14245E", borderColor: "#2E56E8" }
    : { background: JSA.card, borderColor: JSA.cardBorder };
  const Tag = pinned ? "div" : "li";

  return (
    <Tag
      className={`flex items-center gap-2.5 rounded-2xl border p-3 ${pinned ? "shadow-[0_8px_24px_#000a]" : ""}`}
      style={style}
      aria-current={r.is_me ? "true" : undefined}
    >
      <RankBadge rank={r.rank} />
      <Initials text={r.initials} me={r.is_me} size={40} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white truncate">{r.is_me ? "Siz" : r.name}</p>
        {where && <p className="text-[11px] text-slate-400 truncate">{where}</p>}
        {(r.cert_badge || r.label || r.flagged || r.bands_done > 0) && (
          <div className="flex flex-wrap gap-1 mt-1">
            {r.cert_badge && (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-emerald-500/15 text-emerald-300 px-1.5 py-0.5 text-[10.5px] font-bold max-w-full">
                <BadgeCheck size={11} className="shrink-0" />
                <span className="truncate">{r.cert_badge}</span>
              </span>
            )}
            {r.label && (
              <span className={`rounded-full px-1.5 py-0.5 text-[10.5px] font-bold ${
                r.label === "bitirgan" ? "bg-amber-400/15 text-amber-300" : "bg-slate-500/20 text-slate-300"}`}>
                {r.label}
              </span>
            )}
            {r.bands_done > 0 && (
              <span className="rounded-full bg-sky-500/15 text-sky-300 px-1.5 py-0.5 text-[10.5px] font-bold">
                {r.bands_done} daraja
              </span>
            )}
            {r.flagged && (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-orange-500/15 text-orange-300 px-1.5 py-0.5 text-[10.5px] font-bold">
                <Flag size={10} /> tekshirilmoqda
              </span>
            )}
          </div>
        )}
      </div>
      <div className="text-right shrink-0">
        <b className="block text-[17px] text-white leading-tight tabular-nums">
          {period === "week" ? `+${fmtNum(metric)}` : fmtNum(metric)}
        </b>
        <span className="block text-[10.5px] text-slate-400">so'z</span>
        {period === "total" && r.week_gain > 0 && (
          <span className="block text-[11px] font-bold text-emerald-400 tabular-nums">▲{fmtNum(r.week_gain)}</span>
        )}
      </div>
    </Tag>
  );
}

function RankBadge({ rank }: { rank: number | null }) {
  if (rank === 1)
    return (
      <span className="w-8 h-8 rounded-full bg-amber-400 text-white flex items-center justify-center shrink-0"
            aria-label="1-o'rin">
        <Crown size={16} fill="currentColor" />
      </span>
    );
  if (rank === 2 || rank === 3)
    return (
      <span className={`w-8 h-8 rounded-full text-[13px] font-extrabold flex items-center justify-center shrink-0 ${
        rank === 2 ? "bg-slate-300 text-slate-800" : "bg-orange-400 text-white"}`}>
        {rank}
      </span>
    );
  return (
    <span className="w-8 text-[13px] font-bold text-slate-400 text-center shrink-0 tabular-nums">
      {rank ?? "—"}
    </span>
  );
}

function Initials({ text, me = false, size }: { text: string; me?: boolean; size: number }) {
  return (
    <span
      className={`rounded-full flex items-center justify-center shrink-0 font-extrabold text-white ${
        me ? "bg-gradient-to-br from-sky-400 to-brand-600" : "bg-[#1D2F74]"}`}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.36) }}
      aria-hidden="true"
    >
      {(text || "?").slice(0, 2)}
    </span>
  );
}
