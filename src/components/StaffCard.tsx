import { useEffect, useState } from "react";
import {
  X, Plus, Trash2, CheckCircle2, Circle, Award, AlertTriangle,
  GraduationCap, Clock, Plane, Star, UserMinus, UserCheck,
} from "lucide-react";
import {
  api, type StaffCard as Card, type StaffEvents, type Onboarding,
} from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { useAuth } from "../lib/AuthContext";

const ICON: Record<string, typeof Award> = {
  training: GraduationCap,
  review: Star,
  late: Clock,
  absence: AlertTriangle,
  discipline: AlertTriangle,
  reward: Award,
  bonus: Award,
  vacation: Plane,
  note: Circle,
};

const TONE: Record<string, string> = {
  good: "text-emerald-600 bg-emerald-50",
  bad: "text-red-600 bg-red-50",
  neutral: "text-slate-500 bg-slate-50",
};

type Tab = "umumiy" | "tarix" | "onboarding";

/** Xodim kartasi — bir odam haqidagi hamma narsa bitta ekranda. */
export function StaffCard({
  userId,
  canEdit,
  onClose,
}: {
  userId: number;
  canEdit: boolean;
  onClose: () => void;
}) {
  const { user } = useAuth();
  const [card, setCard] = useState<Card | null>(null);
  const [tab, setTab] = useState<Tab>("umumiy");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  // Asoschi kartasi bu yerdan bo'shatilmaydi; HR esa filial
  // rahbariga tegolmaydi (server ham shuni tekshiradi).
  const canDismiss =
    canEdit &&
    !!card &&
    card.role !== "founder" &&
    !(user?.role === "hr_manager" && card.role === "branch_manager");

  async function dismiss() {
    if (!card) return;
    const reason = prompt(
      `${card.full_name} ishdan bo'shatilsinmi?\n\n` +
        "Bo'shatish sababini yozing (majburiy):"
    );
    if (reason === null) return;
    if (!reason.trim()) {
      alert("Bo'shatish sababi majburiy");
      return;
    }
    setBusy(true);
    try {
      await api.put(`/users/${userId}`, {
        is_active: false,
        exit_reason: reason.trim(),
      });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function rehire() {
    if (!card) return;
    if (!confirm(`${card.full_name} ishga qaytarilsinmi?`)) return;
    setBusy(true);
    try {
      await api.put(`/users/${userId}`, { is_active: true });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  function load() {
    setLoading(true);
    api
      .get<Card>(`/staff/${userId}/card`)
      .then(setCard)
      .catch(() => setCard(null))
      .finally(() => setLoading(false));
  }

  useEffect(load, [userId]);

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-12 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-3xl shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            <h3 className="font-semibold text-slate-900">
              {card?.full_name ?? "Xodim kartasi"}
            </h3>
            {card && (
              <p className="text-xs text-slate-500">
                {card.position}
                {card.branch ? ` · ${card.branch}` : ""}
                {card.public_id ? ` · ${card.public_id}` : ""}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {canDismiss &&
              (card!.is_active ? (
                <button
                  onClick={dismiss}
                  disabled={busy}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50"
                >
                  <UserMinus size={14} />
                  Ishdan bo'shatish
                </button>
              ) : (
                <button
                  onClick={rehire}
                  disabled={busy}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
                >
                  <UserCheck size={14} />
                  Ishga qaytarish
                </button>
              ))}
            <button onClick={onClose} className="text-slate-400">
              <X size={18} />
            </button>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-slate-400 p-8">Yuklanmoqda...</p>
        ) : !card ? (
          <p className="text-sm text-slate-500 p-8">
            Bu kartani ko'rishga ruxsatingiz yo'q.
          </p>
        ) : (
          <>
            <div className="flex gap-1 px-5 pt-3">
              {[
                { k: "umumiy", l: "Umumiy" },
                { k: "tarix", l: "Tarix" },
                { k: "onboarding", l: `Onboarding ${card.onboarding_percent}%` },
              ].map((t) => (
                <button
                  key={t.k}
                  onClick={() => setTab(t.k as Tab)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    tab === t.k
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-500 hover:bg-slate-50"
                  }`}
                >
                  {t.l}
                </button>
              ))}
            </div>

            <div className="p-5">
              {tab === "umumiy" && <Summary c={card} />}
              {tab === "tarix" && (
                <Events userId={userId} canEdit={canEdit} onDone={load} />
              )}
              {tab === "onboarding" && (
                <OnboardingList
                  userId={userId}
                  canEdit={canEdit}
                  onDone={load}
                />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3 py-1.5 border-b border-slate-50">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-sm text-slate-800 text-right">{value}</span>
    </div>
  );
}

function Summary({ c }: { c: Card }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <div>
        <p className="text-xs font-medium text-slate-700 mb-2">
          Shaxsiy ma'lumot
        </p>
        <Row label="Lavozim" value={c.position} />
        <Row label="Rol" value={c.role_label} />
        <Row label="Filial" value={c.branch || "—"} />
        <Row label="Rahbar" value={c.manager || "—"} />
        <Row
          label="Ishga kirgan"
          value={c.hired_date ? formatDate(c.hired_date) : "—"}
        />
        <Row label="Telefon" value={c.phone || "—"} />
        <Row
          label="Tug'ilgan sana"
          value={c.birth_date ? formatDate(c.birth_date) : "—"}
        />
        <Row
          label="Holati"
          value={
            c.is_active ? (
              <span className="text-emerald-600">Ishlayapti</span>
            ) : (
              <span className="text-slate-500">
                {c.exit_type_label || "Ishdan ketgan"}
              </span>
            )
          }
        />
        {!c.is_active && c.exit_reason && (
          <Row label="Ketish sababi" value={c.exit_reason} />
        )}

        <p className="text-xs font-medium text-slate-700 mt-4 mb-2">Ish haqi</p>
        {c.salary_hidden ? (
          <p className="text-xs text-slate-400 py-2">
            Maosh ma'lumoti sizga ko'rinmaydi.
          </p>
        ) : (
          <>
            <Row
              label="Fiks oylik"
              value={c.salary ? formatSom(c.salary) : "—"}
            />
            <Row
              label="Jami bonus"
              value={c.bonus_total ? formatSom(c.bonus_total) : "—"}
            />
          </>
        )}
      </div>

      <div>
        <p className="text-xs font-medium text-slate-700 mb-2">
          KPI va davomat
        </p>
        {c.groups.length > 0 && (
          <>
            <Row label="Guruhlari" value={c.groups.length} />
            <Row label="O'quvchilari" value={c.students} />
          </>
        )}
        <Row label="Ta'til kunlari" value={c.vacation_days} />
        <Row
          label="Kechikish"
          value={
            c.late_count > 0 ? (
              <span className="text-amber-600">
                {c.late_count} marta · {c.late_minutes} daqiqa
              </span>
            ) : (
              "—"
            )
          }
        />
        <Row label="Kelmagan kunlari" value={c.absences || "—"} />
        <Row label="Treninglar" value={c.trainings} />
        <Row
          label="Baholashlar"
          value={
            c.avg_review !== null && c.avg_review !== undefined
              ? `${c.reviews} ta · o'rtacha ${c.avg_review}`
              : c.reviews || "—"
          }
        />
        <Row
          label="Intizomiy holat"
          value={
            c.disciplines > 0 ? (
              <span className="text-red-600">{c.disciplines}</span>
            ) : (
              "—"
            )
          }
        />
        <Row
          label="Rag'batlantirish"
          value={
            c.rewards > 0 ? (
              <span className="text-emerald-600">{c.rewards}</span>
            ) : (
              "—"
            )
          }
        />

        {c.groups.length > 0 && (
          <>
            <p className="text-xs font-medium text-slate-700 mt-4 mb-2">
              Guruhlari
            </p>
            {c.groups.map((g) => (
              <Row key={g.id} label={g.name} value={`${g.students} o'quvchi`} />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function Events({
  userId,
  canEdit,
  onDone,
}: {
  userId: number;
  canEdit: boolean;
  onDone: () => void;
}) {
  const [data, setData] = useState<StaffEvents | null>(null);
  const [form, setForm] = useState(false);
  const [kind, setKind] = useState("note");
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [end, setEnd] = useState("");
  const [score, setScore] = useState("");
  const [amount, setAmount] = useState("");
  const [minutes, setMinutes] = useState("");

  function load() {
    api.get<StaffEvents>(`/staff/${userId}/events`).then(setData);
  }
  useEffect(load, [userId]);

  async function save() {
    if (!kind) return;
    await api.post(`/staff/${userId}/events`, {
      kind,
      title: title || null,
      date: date || null,
      end_date: end || null,
      score: score ? Number(score) : null,
      amount: amount ? Number(amount) : null,
      minutes: minutes ? Number(minutes) : null,
    });
    setForm(false);
    setTitle("");
    setScore("");
    setAmount("");
    setMinutes("");
    load();
    onDone();
  }

  if (!data) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  return (
    <div>
      {canEdit && (
        <div className="mb-4">
          {!form ? (
            <button
              onClick={() => setForm(true)}
              className="flex items-center gap-1.5 text-sm text-brand-600 hover:underline"
            >
              <Plus size={14} /> Voqea qo'shish
            </button>
          ) : (
            <div className="bg-slate-50 rounded-lg p-3 space-y-2">
              <div className="flex flex-wrap gap-2">
                <select
                  value={kind}
                  onChange={(e) => setKind(e.target.value)}
                  className="px-2 py-1.5 rounded-lg border border-slate-200 text-sm bg-white"
                >
                  {data.kinds.map((k) => (
                    <option key={k.key} value={k.key}>
                      {k.label}
                    </option>
                  ))}
                </select>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Sarlavha"
                  className="flex-1 min-w-40 px-2 py-1.5 rounded-lg border border-slate-200 text-sm"
                />
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="px-2 py-1.5 rounded-lg border border-slate-200 text-sm"
                />
                {kind === "vacation" && (
                  <input
                    type="date"
                    value={end}
                    onChange={(e) => setEnd(e.target.value)}
                    placeholder="Tugashi"
                    className="px-2 py-1.5 rounded-lg border border-slate-200 text-sm"
                  />
                )}
                {kind === "review" && (
                  <input
                    type="number"
                    step="0.5"
                    value={score}
                    onChange={(e) => setScore(e.target.value)}
                    placeholder="Ball"
                    className="w-20 px-2 py-1.5 rounded-lg border border-slate-200 text-sm"
                  />
                )}
                {kind === "bonus" && (
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="Summa"
                    className="w-28 px-2 py-1.5 rounded-lg border border-slate-200 text-sm"
                  />
                )}
                {kind === "late" && (
                  <input
                    type="number"
                    value={minutes}
                    onChange={(e) => setMinutes(e.target.value)}
                    placeholder="Daqiqa"
                    className="w-20 px-2 py-1.5 rounded-lg border border-slate-200 text-sm"
                  />
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={save}
                  className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium"
                >
                  Saqlash
                </button>
                <button
                  onClick={() => setForm(false)}
                  className="px-3 py-1.5 rounded-lg text-sm text-slate-500"
                >
                  Bekor
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {data.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-4">Voqealar yo'q.</p>
      ) : (
        <div className="space-y-1.5">
          {data.rows.map((e) => {
            const Icon = ICON[e.kind] || Circle;
            return (
              <div
                key={e.id}
                className="flex items-start gap-3 py-2 border-b border-slate-50"
              >
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                    TONE[e.tone] || TONE.neutral
                  }`}
                >
                  <Icon size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800">
                    {e.title || e.kind_label}
                    {e.score !== null && e.score !== undefined && (
                      <span className="ml-2 text-brand-700 font-medium">
                        {e.score} ball
                      </span>
                    )}
                    {e.amount ? (
                      <span className="ml-2 text-emerald-700 font-medium">
                        {formatSom(e.amount)}
                      </span>
                    ) : null}
                    {e.minutes ? (
                      <span className="ml-2 text-amber-700">
                        {e.minutes} daqiqa
                      </span>
                    ) : null}
                  </p>
                  <p className="text-xs text-slate-400">
                    {e.kind_label} · {e.date ? formatDate(e.date) : "—"}
                    {e.end_date ? ` — ${formatDate(e.end_date)}` : ""}
                    {e.by ? ` · ${e.by}` : ""}
                  </p>
                </div>
                {canEdit && (
                  <button
                    onClick={async () => {
                      await api.delete(`/staff/events/${e.id}`);
                      load();
                      onDone();
                    }}
                    className="p-1 text-slate-300 hover:text-red-600"
                  >
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function OnboardingList({
  userId,
  canEdit,
  onDone,
}: {
  userId: number;
  canEdit: boolean;
  onDone: () => void;
}) {
  const [data, setData] = useState<Onboarding | null>(null);

  function load() {
    api.get<Onboarding>(`/staff/${userId}/onboarding`).then(setData);
  }
  useEffect(load, [userId]);

  if (!data) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              data.complete ? "bg-emerald-500" : "bg-brand-500"
            }`}
            style={{ width: `${data.percent}%` }}
          />
        </div>
        <span className="text-sm font-medium text-slate-700">
          {data.done}/{data.total}
        </span>
      </div>

      {data.complete && (
        <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2 mb-3">
          Onboarding tugadi — xodim to'liq ishga kirishdi.
        </p>
      )}

      <div className="space-y-1">
        {data.rows.map((r) => (
          <button
            key={r.step}
            disabled={!canEdit}
            onClick={async () => {
              await api.post(`/staff/${userId}/onboarding`, {
                step: r.step,
                done: !r.done,
              });
              load();
              onDone();
            }}
            className={`w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-left transition ${
              canEdit ? "hover:bg-slate-50" : ""
            }`}
          >
            {r.done ? (
              <CheckCircle2
                size={16}
                className="text-emerald-500 mt-0.5 shrink-0"
              />
            ) : (
              <Circle size={16} className="text-slate-300 mt-0.5 shrink-0" />
            )}
            <div className="min-w-0">
              <p
                className={`text-sm ${
                  r.done ? "text-slate-400 line-through" : "text-slate-800"
                }`}
              >
                {r.label}
              </p>
              {r.done && r.done_by && (
                <p className="text-xs text-slate-400">
                  {r.done_by}
                  {r.done_at ? ` · ${formatDate(r.done_at)}` : ""}
                </p>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
