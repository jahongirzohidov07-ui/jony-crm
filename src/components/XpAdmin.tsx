import { useEffect, useState } from "react";
import {
  Pencil, X, RotateCcw, ShieldAlert, Check, Info, Plus, Zap,
} from "lucide-react";

import {
  api, type XpOverview, type XpRuleList, type XpRuleRow,
  type XpLeagueRow, type XpTransactionRow, type XpSeasonRow,
  type FraudRow, type XpAnalytics, type Student,
} from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  sky: "bg-sky-100 text-sky-700",
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  violet: "bg-violet-100 text-violet-700",
  teal: "bg-teal-100 text-teal-700",
  rose: "bg-rose-100 text-rose-700",
  orange: "bg-orange-100 text-orange-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

// ============================================================ Overview
export function XpOverviewTab() {
  const [d, setD] = useState<XpOverview | null>(null);
  useEffect(() => {
    api.get<XpOverview>("/gamification/overview").then(setD);
  }, []);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Box label="Bugun berilgan XP" value={String(d.today)} />
        <Box label="Bu hafta" value={String(d.week)} />
        <Box label="Jami XP" value={d.total.toLocaleString("ru-RU")} />
        <Box
          label="XP yig'ayotganlar"
          value={String(d.active_students)}
          hint={`o'rtacha ${d.avg_per_student} XP`}
        />
        <Box
          label="Haftada XP olganlar"
          value={`${d.weekly_active_percent}%`}
          tone={d.weekly_active_percent >= 60 ? "good" : "bad"}
        />
        <Box
          label="14 kun XP olmaganlar"
          value={String(d.silent_14d)}
          hint={d.silent_names.slice(0, 3).join(", ")}
          tone={d.silent_14d > 0 ? "bad" : "good"}
        />
        <Box
          label="Qo'lda / avtomat"
          value={`${d.manual_percent}% / ${d.auto_percent}%`}
          hint={d.top_event ? `ko'p: ${d.top_event}` : undefined}
        />
        <Box
          label="Shubhali harakat"
          value={String(d.open_alerts)}
          tone={d.open_alerts > 0 ? "bad" : "good"}
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <p className="text-sm font-medium text-slate-700 mb-3">
          Ligalar bo'yicha taqsimot
          {d.season ? ` · mavsum: ${d.season} (${d.season_participants} ishtirokchi)` : ""}
        </p>
        {d.league_distribution.length === 0 ? (
          <p className="text-sm text-slate-400">Hali ma'lumot yo'q.</p>
        ) : (
          <div className="space-y-2">
            {d.league_distribution.map((l) => {
              const max = Math.max(
                ...d.league_distribution.map((x) => x.students), 1
              );
              return (
                <div key={l.league}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-600">{l.league}</span>
                    <span className="text-slate-800">{l.students}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-brand-500"
                      style={{ width: `${(l.students / max) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================== Rules
export function XpRulesTab() {
  const [d, setD] = useState<XpRuleList | null>(null);
  const [cat, setCat] = useState("");
  const [editing, setEditing] = useState<XpRuleRow | null>(null);

  function load() {
    api.get<XpRuleList>("/gamification/rules").then(setD);
  }
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const rows = cat ? d.rows.filter((r) => r.category === cat) : d.rows;

  return (
    <div>
      <div className="flex flex-wrap gap-1 mb-4">
        <button
          onClick={() => setCat("")}
          className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
            cat === ""
              ? "bg-slate-100 border-slate-300 text-slate-700"
              : "bg-white border-slate-200 text-slate-500"
          }`}
        >
          Hammasi ({d.rows.length})
        </button>
        {d.categories.map((c) => (
          <button
            key={c.key}
            onClick={() => setCat(c.key)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
              cat === c.key
                ? "bg-slate-100 border-slate-300 text-slate-700"
                : "bg-white border-slate-200 text-slate-500"
            }`}
          >
            {c.label} ({d.rows.filter((r) => r.category === c.key).length})
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Hodisa</th>
              <th className="text-left w-28">Kategoriya</th>
              <th className="text-right w-16">XP</th>
              <th className="text-right w-16">Coin</th>
              <th className="text-center w-40">Chegara</th>
              <th className="text-center w-24">Rejim</th>
              <th className="w-16" />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.id}
                className={`border-t border-slate-100 ${
                  r.is_active ? "" : "opacity-50"
                }`}
              >
                <td className="px-4 py-2.5">
                  <p className="text-slate-800">{r.name}</p>
                  <p className="text-xs text-slate-400 font-mono">
                    {r.event_code}
                  </p>
                </td>
                <td>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs ${
                      TONE[r.tone] || TONE.slate
                    }`}
                  >
                    {r.category_label}
                  </span>
                </td>
                <td className="text-right font-medium text-slate-800">
                  {r.default_xp}
                </td>
                <td className="text-right text-slate-500">
                  {r.default_coin || "—"}
                </td>
                <td className="text-center text-xs text-slate-500">
                  {[
                    r.maximum_per_lesson && `dars ${r.maximum_per_lesson}`,
                    r.maximum_per_day && `kun ${r.maximum_per_day}`,
                    r.maximum_per_week && `hafta ${r.maximum_per_week}`,
                    r.maximum_per_month && `oy ${r.maximum_per_month}`,
                  ]
                    .filter(Boolean)
                    .join(" · ") || "—"}
                </td>
                <td className="text-center text-xs">
                  <span className="text-slate-500">
                    {r.mode === "automatic" ? "Avtomat" : "Qo'lda"}
                  </span>
                  {r.requires_approval && (
                    <span className="block text-amber-600">tasdiq</span>
                  )}
                </td>
                <td className="text-right pr-3">
                  {d.can_edit && (
                    <button
                      onClick={() => setEditing(r)}
                      className="text-slate-400 hover:text-brand-600"
                    >
                      <Pencil size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        Qoida qiymati o'zgartirilsa eski yozuvlar o'zgarmaydi — ular
        o'sha paytdagi qiymat bilan yozilgan. Ustoz bitta o'quvchiga
        haftasiga {d.teacher_week_limit} XP, bir darsda{" "}
        {d.teacher_lesson_limit} XP bera oladi. {d.approval_above} XP dan
        katta qo'lda XP tasdiqdan o'tadi.
      </p>

      {editing && (
        <RuleForm
          row={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function RuleForm({
  row,
  onClose,
  onSaved,
}: {
  row: XpRuleRow;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [f, setF] = useState({
    default_xp: String(row.default_xp ?? ""),
    default_coin: String(row.default_coin ?? ""),
    maximum_per_lesson: String(row.maximum_per_lesson ?? ""),
    maximum_per_day: String(row.maximum_per_day ?? ""),
    maximum_per_week: String(row.maximum_per_week ?? ""),
    maximum_per_month: String(row.maximum_per_month ?? ""),
  });
  const [active, setActive] = useState(row.is_active);
  const [approval, setApproval] = useState(row.requires_approval);
  const [saving, setSaving] = useState(false);
  const num = (v: string) => (v === "" ? null : Number(v));

  async function save() {
    setSaving(true);
    try {
      await api.put(`/gamification/rules/${row.id}`, {
        default_xp: num(f.default_xp),
        default_coin: num(f.default_coin),
        maximum_per_lesson: num(f.maximum_per_lesson),
        maximum_per_day: num(f.maximum_per_day),
        maximum_per_week: num(f.maximum_per_week),
        maximum_per_month: num(f.maximum_per_month),
        is_active: active,
        requires_approval: approval,
      });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  const F = ({ k, label }: { k: keyof typeof f; label: string }) => (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">
        {label}
      </label>
      <input
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        value={f[k]}
        onChange={(e) => setF({ ...f, [k]: e.target.value })}
        placeholder="—"
      />
    </div>
  );

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-semibold text-slate-900">{row.name}</h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-400 font-mono mb-4">
          {row.event_code}
        </p>

        <div className="grid grid-cols-2 gap-3">
          <F k="default_xp" label="XP" />
          <F k="default_coin" label="Coin" />
          <F k="maximum_per_lesson" label="Bir darsda ko'pi bilan" />
          <F k="maximum_per_day" label="Kuniga ko'pi bilan" />
          <F k="maximum_per_week" label="Haftasiga ko'pi bilan" />
          <F k="maximum_per_month" label="Oyiga ko'pi bilan" />
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-700 mt-3">
          <input
            type="checkbox"
            checked={active}
            onChange={(e) => setActive(e.target.checked)}
          />
          Faol (o'chirilsa XP berilmaydi, lekin qoida saqlanadi)
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700 mt-1.5">
          <input
            type="checkbox"
            checked={approval}
            onChange={(e) => setApproval(e.target.checked)}
          />
          Tasdiq talab qiladi
        </label>

        <button
          onClick={save}
          disabled={saving}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-4 disabled:opacity-60"
        >
          {saving ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </div>
    </div>
  );
}

// ============================================================= Leagues
export function XpLeaguesTab() {
  const [rows, setRows] = useState<XpLeagueRow[]>([]);
  const [canEdit, setCanEdit] = useState(false);
  const [editing, setEditing] = useState<XpLeagueRow | null>(null);
  const [msg, setMsg] = useState("");

  function load() {
    api
      .get<{ rows: XpLeagueRow[]; can_edit: boolean }>(
        "/gamification/leagues"
      )
      .then((d) => {
        setRows(d.rows);
        setCanEdit(d.can_edit);
      });
  }
  useEffect(load, []);

  return (
    <div>
      <div className="space-y-2">
        {rows.map((l) => (
          <div
            key={l.id}
            className="flex flex-wrap items-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white"
          >
            <span className="w-8 text-center text-slate-400 text-sm">
              {l.rank}
            </span>
            <span className="text-2xl w-9">{l.icon}</span>
            <div className="flex-1 min-w-[120px]">
              <p className="text-sm font-medium text-slate-800">{l.name}</p>
              <p className="text-xs text-slate-400">
                {l.minimum_xp.toLocaleString("ru-RU")}
                {l.maximum_xp
                  ? ` – ${l.maximum_xp.toLocaleString("ru-RU")}`
                  : "+"}{" "}
                XP
              </p>
            </div>
            <span className="text-sm text-amber-600 w-24 text-right">
              {l.reward_coin} coin
            </span>
            <span className="text-sm text-slate-600 w-24 text-right">
              {l.students} o'quvchi
            </span>
            {canEdit && (
              <button
                onClick={() => setEditing(l)}
                className="text-slate-400 hover:text-brand-600"
              >
                <Pencil size={14} />
              </button>
            )}
          </div>
        ))}
      </div>

      {msg && <p className="text-sm text-emerald-600 mt-3">{msg}</p>}
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        Liga umumiy XP asosida aniqlanadi va tushmaydi. Chegara
        o'zgartirilsa barcha o'quvchilar qayta hisoblanadi. Bonus coin
        ligaga birinchi marta chiqqanda beriladi.
      </p>

      {editing && (
        <LeagueForm
          row={editing}
          onClose={() => setEditing(null)}
          onSaved={(n) => {
            setEditing(null);
            if (n) setMsg(`${n} o'quvchi qayta hisoblandi`);
            load();
          }}
        />
      )}
    </div>
  );
}

function LeagueForm({
  row,
  onClose,
  onSaved,
}: {
  row: XpLeagueRow;
  onClose: () => void;
  onSaved: (recalculated: number) => void;
}) {
  const [name, setName] = useState(row.name);
  const [min, setMin] = useState(String(row.minimum_xp));
  const [max, setMax] = useState(String(row.maximum_xp ?? ""));
  const [coin, setCoin] = useState(String(row.reward_coin));
  const [icon, setIcon] = useState(row.icon ?? "");
  const [color, setColor] = useState(row.color ?? "#334155");
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      const r = await api.put<{ recalculated: number }>(
        `/gamification/leagues/${row.id}`,
        {
          name,
          minimum_xp: Number(min),
          maximum_xp: max === "" ? null : Number(max),
          reward_coin: Number(coin),
          icon,
          color,
        }
      );
      onSaved(r.recalculated);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">{row.name}</h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <Field label="Nomi" value={name} onChange={setName} />
          <div className="grid grid-cols-2 gap-3">
            <Field label="Minimum XP" value={min} onChange={setMin} />
            <Field
              label="Maximum XP (bo'sh = cheksiz)"
              value={max}
              onChange={setMax}
            />
            <Field label="Bonus coin" value={coin} onChange={setCoin} />
            <Field label="Ikonka" value={icon} onChange={setIcon} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Rang
            </label>
            <input
              type="color"
              className="w-full h-10 rounded-lg border border-slate-300"
              value={color}
              onChange={(e) => setColor(e.target.value)}
            />
          </div>
          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">
        {label}
      </label>
      <input
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

// ======================================================== Transactions
export function XpTransactionsTab() {
  const [rows, setRows] = useState<XpTransactionRow[]>([]);
  const [canReverse, setCanReverse] = useState(false);
  const [reversing, setReversing] = useState<XpTransactionRow | null>(null);

  function load() {
    api
      .get<{ rows: XpTransactionRow[]; can_reverse: boolean }>(
        "/gamification/transactions"
      )
      .then((d) => {
        setRows(d.rows);
        setCanReverse(d.can_reverse);
      });
  }
  useEffect(load, []);

  return (
    <div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Sana</th>
              <th className="text-left">O'quvchi</th>
              <th className="text-left">Hodisa</th>
              <th className="text-right w-20">XP</th>
              <th className="text-left w-24">Manba</th>
              <th className="text-left w-28">Kim berdi</th>
              <th className="w-20" />
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr
                key={t.id}
                className={`border-t border-slate-100 ${
                  t.is_reversal ? "bg-red-50/60" : ""
                }`}
              >
                <td className="px-4 py-2.5 text-slate-500 text-xs">
                  {t.date ? formatDate(t.date) : "—"}
                </td>
                <td className="text-slate-800">{t.student}</td>
                <td className="text-slate-600">
                  {t.label}
                  {t.reason && (
                    <span className="block text-xs text-slate-400">
                      {t.reason}
                    </span>
                  )}
                </td>
                <td
                  className={`text-right font-medium ${
                    t.amount < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {t.amount > 0 ? "+" : ""}
                  {t.amount}
                </td>
                <td className="text-slate-500 text-xs">{t.source_label}</td>
                <td className="text-slate-500 text-xs">{t.by}</td>
                <td className="text-right pr-3">
                  {canReverse && !t.is_reversal && (
                    <button
                      onClick={() => setReversing(t)}
                      title="Bekor qilish"
                      className="text-slate-400 hover:text-red-600"
                    >
                      <RotateCcw size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length === 0 && (
        <p className="text-sm text-slate-400 py-10 text-center">
          Hali XP berilmagan.
        </p>
      )}

      {reversing && (
        <ReverseForm
          row={reversing}
          onClose={() => setReversing(null)}
          onDone={() => {
            setReversing(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function ReverseForm({
  row,
  onClose,
  onDone,
}: {
  row: XpTransactionRow;
  onClose: () => void;
  onDone: () => void;
}) {
  const [reason, setReason] = useState("");
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!reason.trim()) {
      setErr("Sababini yozing");
      return;
    }
    setSaving(true);
    setErr("");
    try {
      await api.post(`/gamification/transactions/${row.id}/reverse`, {
        reason,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-900">XP ni bekor qilish</h2>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-600 mb-1">
          {row.student} · {row.label} · {row.amount} XP
        </p>
        <p className="text-xs text-slate-400 mb-3">
          Yozuv o'chirilmaydi — manfiy yozuv qo'shiladi, shunda tarix
          to'liq qoladi.
        </p>
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm h-24"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Masalan: Test natijasi 92 dan 75 ga tuzatildi"
        />
        {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
        <button
          onClick={save}
          disabled={saving}
          className="w-full bg-red-600 hover:bg-red-700 text-white rounded-lg py-2.5 text-sm font-medium mt-3 disabled:opacity-60"
        >
          {saving ? "Bajarilmoqda..." : "Bekor qilish"}
        </button>
      </div>
    </div>
  );
}

// ============================================================= Seasons
export function XpSeasonsTab() {
  const [d, setD] = useState<{
    rows: XpSeasonRow[];
    current?: string | null;
    hint: string;
    can_edit: boolean;
  } | null>(null);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    api.get<typeof d>("/gamification/seasons").then(setD);
  }
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  async function create() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await api.post("/gamification/seasons", { name });
      setName("");
      load();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      {d.can_edit && (
        <div className="flex gap-2 mb-4">
          <input
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Yangi mavsum nomi, masalan: Kuz 2026"
          />
          <button
            onClick={create}
            disabled={saving || !name.trim()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-50"
          >
            <Plus size={15} /> Ochish
          </button>
        </div>
      )}

      <div className="space-y-2">
        {d.rows.map((s) => (
          <div
            key={s.id}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${
              s.current
                ? "border-brand-300 bg-brand-50"
                : "border-slate-200 bg-white"
            }`}
          >
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-800">
                {s.name}
                {s.current && (
                  <span className="ml-2 text-xs text-brand-600">joriy</span>
                )}
              </p>
              <p className="text-xs text-slate-400">
                {s.start_date ? formatDate(s.start_date) : "—"}
                {s.end_date ? ` — ${formatDate(s.end_date)}` : " — davom etmoqda"}
              </p>
            </div>
          </div>
        ))}
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Hali mavsum ochilmagan. Mavsumsiz ham XP yig'iladi.
          </p>
        )}
      </div>

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>
    </div>
  );
}

// =============================================================== Fraud
export function XpFraudTab() {
  const [d, setD] = useState<{
    rows: FraudRow[];
    counts: Record<string, number>;
    statuses: { key: string; label: string }[];
  } | null>(null);
  const [status, setStatus] = useState("open");

  function load() {
    api.get<typeof d>(`/gamification/fraud?status_filter=${status}`).then(setD);
  }
  useEffect(load, [status]);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  async function review(id: number, s: string) {
    await api.post(`/gamification/fraud/${id}`, { status: s });
    load();
  }

  return (
    <div>
      <div className="flex gap-1 mb-4">
        {d.statuses.map((s) => (
          <button
            key={s.key}
            onClick={() => setStatus(s.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border ${
              status === s.key
                ? "bg-slate-100 border-slate-300 text-slate-700"
                : "bg-white border-slate-200 text-slate-500"
            }`}
          >
            {s.label} ({d.counts[s.key] || 0})
          </button>
        ))}
      </div>

      {d.rows.length === 0 ? (
        <div className="py-10 text-center">
          <Check size={22} className="text-emerald-500 mx-auto mb-2" />
          <p className="text-sm text-slate-500">
            Shubhali harakat topilmadi.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {d.rows.map((a) => (
            <div
              key={a.id}
              className="flex flex-wrap items-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white"
            >
              <ShieldAlert size={16} className="text-slate-400 shrink-0" />
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  TONE[a.tone] || TONE.slate
                }`}
              >
                {a.severity}
              </span>
              <div className="flex-1 min-w-[200px]">
                <p className="text-sm text-slate-800">{a.label}</p>
                <p className="text-xs text-slate-500">{a.description}</p>
              </div>
              <span className="text-xs text-slate-400">
                {a.date ? formatDate(a.date) : ""}
              </span>
              {a.status === "open" && (
                <div className="flex gap-1.5">
                  <button
                    onClick={() => review(a.id, "reviewed")}
                    className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-brand-300"
                  >
                    Ko'rdim
                  </button>
                  <button
                    onClick={() => review(a.id, "dismissed")}
                    className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs text-slate-500"
                  >
                    Muammo emas
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// =========================================================== Analytics
export function XpAnalyticsTab() {
  const [d, setD] = useState<XpAnalytics | null>(null);
  useEffect(() => {
    api.get<XpAnalytics>("/gamification/analytics").then(setD);
  }, []);
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const Table = ({
    title,
    rows,
  }: {
    title: string;
    rows: XpAnalytics["by_branch"];
  }) => (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm font-medium text-slate-700 mb-3">{title}</p>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-400">Ma'lumot yo'q.</p>
      ) : (
        <table className="w-full text-sm">
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-t border-slate-50">
                <td className="py-2 text-slate-800">{r.label}</td>
                <td className="py-2 text-right text-slate-500 w-24">
                  {r.students} o'quvchi
                </td>
                <td className="py-2 text-right font-medium text-slate-800 w-28">
                  {r.avg_xp.toLocaleString("ru-RU")} XP
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {d.attendance_correlation !== null &&
        d.attendance_correlation !== undefined && (
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-xs text-slate-500 mb-1">
              XP va davomat bog'liqligi
            </p>
            <p className="text-2xl font-semibold text-slate-900">
              {d.attendance_correlation}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              {d.correlation_hint}
            </p>
          </div>
        )}
      <Table title="Filiallar bo'yicha o'rtacha XP" rows={d.by_branch} />
      <Table title="Ustozlar bo'yicha o'rtacha XP" rows={d.by_teacher} />
      <Table title="Eng faol guruhlar" rows={d.by_group} />
      {d.weakest_groups.length > 0 && (
        <Table title="Eng sust guruhlar" rows={d.weakest_groups} />
      )}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <p className="text-sm font-medium text-slate-700 mb-3">
          Eng ko'p qo'lda XP berayotganlar
        </p>
        {d.manual_by_user.length === 0 ? (
          <p className="text-sm text-slate-400">Qo'lda XP berilmagan.</p>
        ) : (
          <div className="space-y-1.5">
            {d.manual_by_user.map((u) => (
              <div key={u.user} className="flex justify-between text-sm">
                <span className="text-slate-700">{u.user}</span>
                <span className="text-slate-800 font-medium">{u.xp} XP</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================== Ustoz uchun Quick XP
export function QuickXp({
  students,
  lessonId,
  onDone,
}: {
  students: Student[];
  lessonId?: number;
  onDone?: () => void;
}) {
  const [rules, setRules] = useState<XpRuleRow[]>([]);
  const [quick, setQuick] = useState<string[]>([]);
  const [picked, setPicked] = useState<number[]>([]);
  const [code, setCode] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get<XpRuleList>("/gamification/rules").then((d) => {
      setRules(d.rows);
      setQuick(d.quick);
      setCode(d.quick[0] || "");
    });
  }, []);

  const available = rules.filter((r) => quick.includes(r.event_code));
  const rule = available.find((r) => r.event_code === code);

  async function give() {
    if (!code || picked.length === 0) return;
    setBusy(true);
    setErr("");
    setResult(null);
    try {
      const r = await api.post<{
        given: { full_name: string }[];
        skipped: { full_name: string; reason: string }[];
        total_xp: number;
      }>("/gamification/award-bulk", {
        student_ids: picked,
        event_code: code,
        reason: note || undefined,
        lesson_id: lessonId,
      });
      setResult(
        `${r.given.length} o'quvchiga ${r.total_xp} XP berildi` +
          (r.skipped.length
            ? ` · ${r.skipped.length} tasiga berilmadi: ${r.skipped
                .map((s) => `${s.full_name} (${s.reason})`)
                .join("; ")}`
            : "")
      );
      setPicked([]);
      onDone?.();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <Zap size={15} className="text-amber-500" />
        <p className="text-sm font-medium text-slate-700">Tezkor XP</p>
        {rule && (
          <span className="text-xs text-slate-500">
            +{rule.default_xp} XP har biriga
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {available.map((r) => (
          <button
            key={r.event_code}
            onClick={() => setCode(r.event_code)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
              code === r.event_code
                ? "bg-brand-50 border-brand-400 text-brand-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            {r.name} +{r.default_xp}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {students.map((s) => {
          const on = picked.includes(s.id);
          return (
            <button
              key={s.id}
              onClick={() =>
                setPicked(
                  on ? picked.filter((x) => x !== s.id) : [...picked, s.id]
                )
              }
              className={`px-2.5 py-1.5 rounded-lg text-xs border transition ${
                on
                  ? "bg-emerald-50 border-emerald-400 text-emerald-700"
                  : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {on && <Check size={11} className="inline mr-1" />}
              {s.full_name}
            </button>
          );
        })}
      </div>

      <div className="flex gap-2">
        <input
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Qisqa izoh (ixtiyoriy)"
        />
        <button
          onClick={give}
          disabled={busy || picked.length === 0 || !code}
          className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-50"
        >
          {busy
            ? "..."
            : `Berish (${picked.length} ta · ${
                (rule?.default_xp || 0) * picked.length
              } XP)`}
        </button>
      </div>

      {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
      {result && <p className="text-sm text-emerald-700 mt-2">{result}</p>}
      <p className="text-xs text-slate-400 mt-2">
        XP miqdorini o'zgartirib bo'lmaydi — u qoidadan olinadi. Bir
        o'quvchiga haftalik chegara to'lsa, tizim ogohlantiradi.
      </p>
    </div>
  );
}

function Box({
  label,
  value,
  hint,
  tone = "plain",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "plain" | "good" | "bad";
}) {
  const cls = {
    plain: "bg-white border-slate-200 text-slate-900",
    good: "bg-emerald-50 border-emerald-200 text-emerald-800",
    bad: "bg-red-50 border-red-200 text-red-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5 truncate">{hint}</p>}
    </div>
  );
}
