import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Wallet, TrendingUp, UserPlus, ChevronDown, ChevronUp, Trophy } from "lucide-react";
import { api, type AdminKpi, type AdminKpiResult } from "../lib/api";
import { formatSom } from "../lib/format";

/**
 * ADMINNING OYLIGI VA KEYINGI BONUS (2026-10-02).
 *
 * Jahongir: "Sarvar Ibragimov va boshqa adminlarni bonusi keyingisiga
 * qancha qolishi va qancha oylik olishini ko'rsatib turishi kerak va
 * ularni undashi kerak shu natijaga erishishga ... dashboardda ko'rinib
 * tursin, qayerdadir turib doim eslatib ajralib turadigan bo'lsin".
 *
 * Ikki joyda: Dashboard tepasida katta karta (AdminSalaryCard) va har
 * sahifada pastki burchakda suzib turadigan eslatma (AdminSalaryFloat).
 * Raqamlar /kpi/admins dan — Hisobotlar -> Adminlar KPI bilan bir xil.
 */
function useMyKpi(): AdminKpi | null {
  const [row, setRow] = useState<AdminKpi | null>(null);
  useEffect(() => {
    const now = new Date();
    api
      .get<AdminKpiResult>(
        `/kpi/admins?year=${now.getFullYear()}&month=${now.getMonth() + 1}`)
      .then((d) => setRow(d.rows?.[0] ?? null))
      .catch(() => setRow(null));
  }, []);
  return row;
}

function daysLeft(): number {
  const now = new Date();
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  return Math.max(1, last - now.getDate() + 1);
}

function plan(r: AdminKpi) {
  const colUp = r.next_collection_bonus != null
    ? Math.max(0, r.next_collection_bonus - r.collection_bonus) : 0;
  const newUp = r.next_new_client_bonus != null
    ? Math.max(0, r.next_new_client_bonus - r.new_client_bonus) : 0;
  return { colUp, newUp, potential: r.total + colUp + newUp };
}

function short(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mln`;
  if (Math.abs(n) >= 1_000) return `${Math.round(n / 1_000)} ming`;
  return String(Math.round(n));
}

function Bar({ value, mark }: { value: number; mark?: number | null }) {
  return (
    <div className="relative h-2.5 rounded-full bg-white/20 overflow-hidden">
      <div
        className="h-full rounded-full bg-white transition-[width] duration-1000 ease-out"
        style={{ width: `${Math.min(100, Math.max(2, value))}%` }}
      />
      {mark != null && mark < 100 && (
        <div className="absolute top-0 h-full w-0.5 bg-amber-300"
             style={{ left: `${mark}%` }} />
      )}
    </div>
  );
}

/** Dashboard tepasidagi katta karta. */
export function AdminSalaryCard() {
  const r = useMyKpi();
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setShown(true), 60);
    return () => clearTimeout(t);
  }, []);
  if (!r) return null;
  const { colUp, newUp, potential } = plan(r);
  const left = daysLeft();
  const perDay = r.collection_gap ? r.collection_gap / left : 0;
  const allTop = r.next_collection_percent == null && r.next_new_clients == null;
  const newPct = r.next_new_clients
    ? (r.new_clients / r.next_new_clients) * 100 : 100;

  return (
    <div className="mb-5 rounded-2xl bg-gradient-to-br from-brand-600 via-brand-700 to-indigo-700 text-white p-5 shadow-lg">
      <div className="flex flex-wrap items-start gap-4">
        <div className="flex-1 min-w-[220px]">
          <p className="flex items-center gap-1.5 text-sm text-white/80">
            <Wallet size={15} /> Shu oy oylingiz (hozirgi natija bilan)
          </p>
          <p className="text-3xl md:text-4xl font-bold tabular-nums mt-1">
            {formatSom(r.total)}
          </p>
          <p className="text-xs text-white/70 mt-1">
            Fiks {formatSom(r.fix_salary)} · Yig'im bonusi{" "}
            {formatSom(r.collection_bonus)} · Yangi mijoz bonusi{" "}
            {formatSom(r.new_client_bonus)}
          </p>
        </div>
        {!allTop && potential > r.total && (
          <div className="rounded-xl bg-white/15 px-4 py-3">
            <p className="text-xs text-white/80">Maqsadga yetsangiz</p>
            <p className="text-2xl font-bold tabular-nums text-amber-300">
              {formatSom(potential)}
            </p>
            <p className="text-xs text-white/80">
              +{formatSom(potential - r.total)} ko'proq
            </p>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-3 mt-4">
        <div className="rounded-xl bg-white/10 p-3.5">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="flex items-center gap-1.5">
              <TrendingUp size={14} /> Eski to'lovlarni yig'ish
            </span>
            <span className="font-semibold tabular-nums">{r.collection_percent}%</span>
          </div>
          <Bar value={shown ? r.collection_percent : 0} mark={r.next_collection_percent} />
          <p className="text-xs text-white/90 mt-2 leading-relaxed">
            {r.next_collection_percent != null && r.collection_gap != null ? (
              <>
                Yana <b className="text-amber-300">{formatSom(r.collection_gap)}</b> yig'ing
                — {r.next_collection_percent}% ga chiqasiz va bonusingiz{" "}
                <b>{formatSom(r.next_collection_bonus || 0)}</b> bo'ladi
                {colUp > 0 && <> (<b className="text-amber-300">+{short(colUp)}</b>)</>}.
                {perDay > 0 && <> Kuniga ~{short(perDay)} so'm yetadi.</>}
              </>
            ) : (
              <>Eng yuqori pog'onadasiz — oy oxirigacha shu foizni saqlang.</>
            )}
          </p>
        </div>

        <div className="rounded-xl bg-white/10 p-3.5">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="flex items-center gap-1.5">
              <UserPlus size={14} /> Yangi mijozlar (o'zingiz qabul qilgan)
            </span>
            <span className="font-semibold tabular-nums">
              {r.new_clients}
              {r.next_new_clients ? ` / ${r.next_new_clients}` : ""}
            </span>
          </div>
          <Bar value={shown ? newPct : 0} />
          <p className="text-xs text-white/90 mt-2 leading-relaxed">
            {r.new_clients_gap != null && r.next_new_clients != null ? (
              <>
                Yana <b className="text-amber-300">{r.new_clients_gap} ta</b> yangi
                mijoz — bonusingiz{" "}
                <b>{formatSom(r.next_new_client_bonus || 0)}</b> bo'ladi
                {newUp > 0 && <> (<b className="text-amber-300">+{short(newUp)}</b>)</>}.
              </>
            ) : (
              <>Eng yuqori pog'onadasiz — ajoyib natija!</>
            )}
          </p>
        </div>
      </div>

      <p className="flex items-center gap-1.5 text-xs text-white/80 mt-3">
        <Trophy size={13} className="text-amber-300" />
        {allTop
          ? "Barcha bonuslarni olyapsiz. Zo'r ish — shu sur'atda davom eting!"
          : `Oy tugashiga ${left} kun qoldi. Har bir qo'ng'iroq va har bir yangi mijoz oylingizni oshiradi.`}
      </p>
    </div>
  );
}

/** Har sahifada pastki burchakda doim turadigan eslatma. */
export function AdminSalaryFloat() {
  const r = useMyKpi();
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  // Dashboard'da katta karta bor — u yerda takrorlanmaydi
  if (!r || loc.pathname === "/") return null;
  const { potential } = plan(r);
  const hint = r.collection_gap != null && r.next_collection_percent != null
    ? `Yana ${short(r.collection_gap)} yig'ing → ${r.next_collection_percent}%`
    : r.new_clients_gap != null
      ? `Yana ${r.new_clients_gap} ta yangi mijoz → bonus`
      : "Barcha bonuslar sizda!";

  return (
    <div className="fixed bottom-4 right-4 z-40 max-w-[calc(100vw-2rem)]">
      {open && (
        <div className="mb-2 w-72 rounded-xl bg-white shadow-xl ring-1 ring-slate-200 p-3 text-sm">
          <p className="text-xs text-slate-500">Shu oy oylingiz</p>
          <p className="text-xl font-bold text-slate-900 tabular-nums">{formatSom(r.total)}</p>
          {potential > r.total && (
            <p className="text-xs text-emerald-700 mt-0.5">
              Maqsadga yetsangiz: <b>{formatSom(potential)}</b>
            </p>
          )}
          <ul className="mt-2 space-y-1 text-xs text-slate-600">
            <li>Yig'ish: {r.collection_percent}%
              {r.collection_gap != null && ` · yana ${formatSom(r.collection_gap)}`}</li>
            <li>Yangi mijoz: {r.new_clients} ta
              {r.new_clients_gap != null && ` · yana ${r.new_clients_gap} ta`}</li>
          </ul>
          <Link to="/" className="block mt-2 text-xs text-brand-600 hover:underline">
            Batafsil — Dashboard
          </Link>
        </div>
      )}
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-600 to-indigo-600 text-white pl-3 pr-3.5 py-2 shadow-lg ring-2 ring-white hover:brightness-110"
        title="Oylingiz va keyingi bonus"
      >
        <Wallet size={16} />
        <span className="text-sm font-semibold tabular-nums">{short(r.total)}</span>
        <span className="hidden sm:inline text-xs text-white/85 border-l border-white/30 pl-2">
          {hint}
        </span>
        {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>
    </div>
  );
}
