import { useEffect, useState } from "react";
import { Coins, Plus, X, Trash2, Gift, Trophy } from "lucide-react";
import {
  api,
  type CoinBalance,
  type CoinEntry,
  type Reward,
  type Redemption,
  type ExamCoinRule,
  type Branch,
} from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { TEACHING_STAFF, FINANCE_ACCESS, can } from "../lib/roles";
import { coinSourceLabel, EXAM_KINDS } from "../lib/exams";
import { formatSom, formatDate } from "../lib/format";

type Tab = "leaderboard" | "rewards" | "rules";

const TABS: { key: Tab; label: string }[] = [
  { key: "leaderboard", label: "Reyting" },
  { key: "rewards", label: "Sovg'alar" },
  { key: "rules", label: "Coin qoidasi" },
];

const MEDALS = ["🥇", "🥈", "🥉"];

// ---------------------------------------------------------- Reyting ----
function StudentCoins({
  student,
  canAdmin,
  onClose,
  onChanged,
}: {
  student: CoinBalance;
  canAdmin: boolean;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [history, setHistory] = useState<CoinEntry[]>([]);
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  function load() {
    api
      .get<CoinEntry[]>(`/students/${student.student_id}/coins`)
      .then(setHistory);
  }
  useEffect(load, [student.student_id]);

  async function give() {
    const value = Number(amount);
    if (!value) {
      setError("Miqdorni kiriting");
      return;
    }
    try {
      await api.post(`/students/${student.student_id}/coins`, {
        amount: value,
        note: note || null,
      });
      setAmount("");
      setNote("");
      setError(null);
      load();
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  async function remove(e: CoinEntry) {
    try {
      await api.delete(`/coins/${e.id}`);
      load();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik");
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-semibold text-slate-900">{student.full_name}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-4">
          Balans:{" "}
          <span className="font-semibold text-brand-700">
            {student.balance} coin
          </span>{" "}
          · yig'gan {student.earned} · sarflagan {student.spent}
        </p>

        {canAdmin && (
          <div className="flex gap-2 mb-4">
            <input
              type="number"
              className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="+10"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <input
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Sabab (masalan: tanlov g'olibi)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <button
              onClick={give}
              className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 text-sm font-medium"
            >
              Berish
            </button>
          </div>
        )}
        {error && <p className="text-sm text-red-600 mb-2">{error}</p>}

        <div className="overflow-y-auto flex-1 -mx-2 px-2">
          {history.length === 0 && (
            <p className="text-sm text-slate-400 py-6 text-center">
              Hali coin yozuvi yo'q
            </p>
          )}
          {history.map((e) => (
            <div
              key={e.id}
              className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
            >
              <div className="min-w-0">
                <p className="text-sm text-slate-700 truncate">
                  {e.note || coinSourceLabel(e.source)}
                </p>
                <p className="text-xs text-slate-400">
                  {coinSourceLabel(e.source)} · {formatDate(e.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span
                  className={`text-sm font-semibold ${
                    e.amount >= 0 ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {e.amount > 0 ? "+" : ""}
                  {e.amount}
                </span>
                {canAdmin && e.source === "manual" && (
                  <button
                    onClick={() => remove(e)}
                    className="text-slate-300 hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LeaderboardTab({ canAdmin }: { canAdmin: boolean }) {
  const [rows, setRows] = useState<CoinBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<CoinBalance | null>(null);
  const [q, setQ] = useState("");

  function load() {
    setLoading(true);
    api
      .get<CoinBalance[]>("/coins")
      .then(setRows)
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  const filtered = rows.filter((r) =>
    r.full_name.toLowerCase().includes(q.toLowerCase())
  );
  const totalCoins = rows.reduce((a, r) => a + r.balance, 0);

  if (loading) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-3">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-64"
          placeholder="Ism bo'yicha qidirish..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <p className="text-sm text-slate-500 whitespace-nowrap">
          Aylanmadagi coin:{" "}
          <span className="font-semibold text-slate-800">{totalCoins}</span>
        </p>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Hali coin berilmagan. Baholash yoki imtihon natijasi kiritilishi bilan
          coinlar shu yerda paydo bo'ladi.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium w-16">#</th>
                <th className="text-left px-4 py-3 font-medium">Talaba</th>
                <th className="text-left px-4 py-3 font-medium">Guruh</th>
                <th className="text-right px-4 py-3 font-medium">Yig'gan</th>
                <th className="text-right px-4 py-3 font-medium">Sarflagan</th>
                <th className="text-right px-4 py-3 font-medium">Balans</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <tr
                  key={r.student_id}
                  onClick={() => setOpen(r)}
                  className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                >
                  <td className="px-4 py-3 text-slate-500">
                    {q === "" && i < 3 ? MEDALS[i] : i + 1}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {r.full_name}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{r.group || "—"}</td>
                  <td className="px-4 py-3 text-right text-slate-600">
                    {r.earned}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-500">
                    {r.spent || "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-brand-700">
                    {r.balance}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-400 mt-3">
        Coin qo'lda yig'ilmaydi: kunlik baho (1–5 ball = shuncha coin) va
        imtihon natijasi kiritilishi bilan o'zi qo'shiladi. Qatorni bosib
        tarixni ko'rasiz.
      </p>

      {open && (
        <StudentCoins
          student={open}
          canAdmin={canAdmin}
          onClose={() => setOpen(null)}
          onChanged={load}
        />
      )}
    </div>
  );
}

// --------------------------------------------------------- Sovg'alar ----
function RewardForm({
  branches,
  initial,
  onClose,
  onSaved,
}: {
  branches: Branch[];
  initial?: Reward;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editing = !!initial;
  const [name, setName] = useState(initial?.name ?? "");
  const [cost, setCost] = useState(initial ? String(initial.cost) : "");
  const [valueSom, setValueSom] = useState(
    initial?.value_som ? String(Math.round(initial.value_som)) : ""
  );
  const [stock, setStock] = useState(
    initial?.stock != null ? String(initial.stock) : ""
  );
  const [branchId, setBranchId] = useState(
    initial?.branch_id ? String(initial.branch_id) : ""
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!name.trim() || !Number(cost)) {
      setError("Nom va coin narxini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const body = {
        name: name.trim(),
        cost: Number(cost),
        value_som: valueSom ? Number(valueSom) : null,
        stock: stock === "" ? null : Number(stock),
        branch_id: branchId ? Number(branchId) : null,
      };
      if (editing) await api.put(`/rewards/${initial!.id}`, body);
      else await api.post("/rewards", body);
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">
            {editing ? "Sovg'ani tahrirlash" : "Yangi sovg'a"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              Nomi
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Masalan: Termos"
              autoFocus
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Necha coin
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Qiymati (so'm)
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={valueSom}
                onChange={(e) => setValueSom(e.target.value)}
                placeholder="ixtiyoriy"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Zaxira (dona)
              </label>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={stock}
                onChange={(e) => setStock(e.target.value)}
                placeholder="cheklanmagan"
              />
            </div>
            {branches.length > 1 && (
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">
                  Filial
                </label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  value={branchId}
                  onChange={(e) => setBranchId(e.target.value)}
                >
                  <option value="">— hamma filial —</option>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            onClick={save}
            disabled={saving}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 text-sm font-medium mt-1 disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : editing ? "Saqlash" : "Qo'shish"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RedeemModal({
  reward,
  onClose,
  onDone,
}: {
  reward: Reward;
  onClose: () => void;
  onDone: () => void;
}) {
  const [rows, setRows] = useState<CoinBalance[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<CoinBalance[]>("/coins").then(setRows);
  }, []);

  async function redeem(sid: number) {
    try {
      await api.post("/rewards/redeem", {
        student_id: sid,
        reward_id: reward.id,
      });
      onDone();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    }
  }

  const filtered = rows.filter((r) =>
    r.full_name.toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-semibold text-slate-900">{reward.name}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-3">
          {reward.cost} coin · kimga beriladi?
        </p>
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm mb-3"
          placeholder="Ism bo'yicha qidirish..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
        <div className="overflow-y-auto flex-1">
          {filtered.map((r) => {
            const enough = r.balance >= reward.cost;
            return (
              <button
                key={r.student_id}
                onClick={() => enough && redeem(r.student_id)}
                disabled={!enough}
                className={`w-full flex items-center justify-between py-2.5 px-2 rounded-lg text-left ${
                  enough ? "hover:bg-slate-50" : "opacity-40 cursor-not-allowed"
                }`}
              >
                <span className="text-sm text-slate-700">{r.full_name}</span>
                <span
                  className={`text-sm font-medium ${
                    enough ? "text-brand-700" : "text-slate-400"
                  }`}
                >
                  {r.balance} coin
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function RewardsTab({ canAdmin }: { canAdmin: boolean }) {
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [history, setHistory] = useState<Redemption[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [editing, setEditing] = useState<Reward | null>(null);
  const [redeeming, setRedeeming] = useState<Reward | null>(null);

  function load() {
    api.get<Reward[]>("/rewards").then(setRewards);
    api.get<Redemption[]>("/rewards/redemptions").then(setHistory);
  }
  useEffect(() => {
    load();
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, []);

  async function remove(r: Reward) {
    if (!confirm(`"${r.name}" o'chirilsinmi?`)) return;
    await api.delete(`/rewards/${r.id}`);
    load();
  }

  const active = rewards.filter((r) => r.active);

  return (
    <div>
      {canAdmin && (
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium mb-4"
        >
          <Plus size={16} /> Yangi sovg'a
        </button>
      )}

      {active.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          Sovg'alar ro'yxati bo'sh
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
          {active.map((r) => (
            <div
              key={r.id}
              className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-medium text-slate-800 truncate">{r.name}</p>
                  <p className="text-xs text-slate-400">
                    {r.value_som ? formatSom(r.value_som) : "—"}
                    {r.stock != null && ` · ${r.stock} dona qoldi`}
                  </p>
                </div>
                {canAdmin && (
                  <button
                    onClick={() => remove(r)}
                    className="text-slate-300 hover:text-red-500 shrink-0"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
              <p className="text-lg font-semibold text-brand-700 mt-2 flex items-center gap-1.5">
                <Coins size={16} /> {r.cost}
              </p>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => setRedeeming(r)}
                  className="flex-1 bg-brand-50 hover:bg-brand-100 text-brand-700 rounded-lg py-1.5 text-xs font-medium"
                >
                  Berish
                </button>
                {canAdmin && (
                  <button
                    onClick={() => setEditing(r)}
                    className="px-3 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg py-1.5 text-xs font-medium"
                  >
                    Tahrir
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <h3 className="font-medium text-slate-800 mb-2 flex items-center gap-2">
        <Gift size={16} className="text-slate-400" /> Berilgan sovg'alar
      </h3>
      {history.length === 0 ? (
        <p className="text-sm text-slate-400">Hali sovg'a berilmagan</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Sana</th>
                <th className="text-left px-4 py-3 font-medium">Talaba</th>
                <th className="text-left px-4 py-3 font-medium">Sovg'a</th>
                <th className="text-right px-4 py-3 font-medium">Coin</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-slate-600">
                    {formatDate(h.created_at)}
                  </td>
                  <td className="px-4 py-3 text-slate-800">
                    {h.student?.full_name || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {h.reward?.name || "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-slate-700">
                    {h.coins}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showNew && (
        <RewardForm
          branches={branches}
          onClose={() => setShowNew(false)}
          onSaved={load}
        />
      )}
      {editing && (
        <RewardForm
          branches={branches}
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
      {redeeming && (
        <RedeemModal
          reward={redeeming}
          onClose={() => setRedeeming(null)}
          onDone={load}
        />
      )}
    </div>
  );
}

// ------------------------------------------------------ Coin qoidasi ----
function RulesTab({ canAdmin }: { canAdmin: boolean }) {
  const [rules, setRules] = useState<ExamCoinRule[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<ExamCoinRule[]>("/exam-coin-rules").then(setRules);
  }, []);

  function update(i: number, patch: Partial<ExamCoinRule>) {
    setRules(rules.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
    setSaved(false);
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const clean = rules.map((r) => ({
        min_percent: Number(r.min_percent),
        coins: Number(r.coins),
        kind: r.kind || null,
      }));
      const updated = await api.put<ExamCoinRule[]>("/exam-coin-rules", clean);
      setRules(updated);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <p className="text-sm text-slate-500 mb-4">
        Imtihon natijasi shu jadval bo'yicha coinga aylanadi. O'quvchining
        foizi qaysi bosqichdan o'tsa, o'sha bosqichning coini beriladi.
      </p>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-4">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Foiz (dan)</th>
              <th className="text-left px-4 py-3 font-medium">Coin</th>
              <th className="text-left px-4 py-3 font-medium">Test turi</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  Qoida yo'q — imtihonlardan coin berilmaydi
                </td>
              </tr>
            )}
            {rules.map((r, i) => (
              <tr key={i} className="border-t border-slate-100">
                <td className="px-4 py-2">
                  <input
                    type="number"
                    disabled={!canAdmin}
                    className="w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                    value={r.min_percent}
                    onChange={(e) =>
                      update(i, { min_percent: Number(e.target.value) })
                    }
                  />
                  <span className="text-slate-400 ml-1">%</span>
                </td>
                <td className="px-4 py-2">
                  <input
                    type="number"
                    disabled={!canAdmin}
                    className="w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-50"
                    value={r.coins}
                    onChange={(e) => update(i, { coins: Number(e.target.value) })}
                  />
                </td>
                <td className="px-4 py-2">
                  <select
                    disabled={!canAdmin}
                    className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm bg-white disabled:bg-slate-50"
                    value={r.kind || ""}
                    onChange={(e) => update(i, { kind: e.target.value || null })}
                  >
                    <option value="">Hammasi</option>
                    {EXAM_KINDS.map((k) => (
                      <option key={k.key} value={k.key}>
                        {k.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-2 text-right">
                  {canAdmin && (
                    <button
                      onClick={() => {
                        setRules(rules.filter((_, idx) => idx !== i));
                        setSaved(false);
                      }}
                      className="text-slate-300 hover:text-red-500"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {canAdmin && (
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setRules([...rules, { min_percent: 50, coins: 5, kind: null }]);
              setSaved(false);
            }}
            className="flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
          >
            <Plus size={15} /> Bosqich qo'shish
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
          >
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
          {saved && <span className="text-sm text-emerald-600">Saqlandi</span>}
        </div>
      )}
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}

      <p className="text-xs text-slate-400 mt-4">
        O'zgartirish faqat bundan keyin kiritiladigan natijalarga ta'sir qiladi —
        avval berilgan coinlar o'z holicha qoladi. Mock testda IELTS band foizga
        aylantiriladi (masalan 7.0 band = 77.8%).
      </p>
    </div>
  );
}

// -------------------------------------------------------------- Page ----
export default function Gamification() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("leaderboard");

  if (!can(user?.role, TEACHING_STAFF)) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  const canAdmin = can(user?.role, FINANCE_ACCESS);

  return (
    <div className="p-8 max-w-5xl">
      <h1 className="text-xl font-semibold text-slate-900 mb-1 flex items-center gap-2">
        <Trophy size={20} className="text-brand-600" /> Coin tizimi
      </h1>
      <p className="text-sm text-slate-500 mb-5">
        Baho va imtihon natijalari coinga aylanadi, coin sovg'aga
      </p>

      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "leaderboard" && <LeaderboardTab canAdmin={canAdmin} />}
      {tab === "rewards" && <RewardsTab canAdmin={canAdmin} />}
      {tab === "rules" && <RulesTab canAdmin={canAdmin} />}
    </div>
  );
}
