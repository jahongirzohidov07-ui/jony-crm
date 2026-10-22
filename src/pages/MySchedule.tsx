import { tab3d } from "../lib/tabs3d";
import { useEffect, useState } from "react";
import {
  CalendarClock, Info, X, ArrowRight, UserCheck, AlertTriangle,
} from "lucide-react";
import {
  api, type MyReschedules, type MySubstitutions, type SubstitutionRow,
} from "../lib/api";
import { formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  amber: "bg-amber-100 text-amber-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
};

type Tab = "move" | "cover";

/** Dars ko'chirish va o'rinbosar ustoz. */
export default function MySchedule() {
  const [tab, setTab] = useState<Tab>("move");

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <CalendarClock size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Darslarim</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Darsni ko'chirish va o'rinbosar ustoz
      </p>

      <div className="flex gap-2 mb-5 overflow-x-auto pt-0.5 pb-2 px-0.5">
        {([
          ["move", "Dars ko'chirish"],
          ["cover", "O'rinbosar"],
        ] as [Tab, string][]).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={tab3d(tab === k, "blue")}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "move" ? <MoveTab /> : <CoverTab />}
    </div>
  );
}

/* ================================================== Dars ko'chirish */
function MoveTab() {
  const [d, setD] = useState<MyReschedules | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    api
      .get<MyReschedules>("/me/reschedules")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <Quota label="Shu oyda qoldi" q={d.quota} />
        <Quota label="Kelasi oyda qoldi" q={d.quota_next} />
        <div className="bg-white border border-slate-200 rounded-xl p-3.5">
          <p className="text-xs text-slate-500 mb-1">6 oyda ishlatilgan</p>
          <p className="text-2xl font-semibold text-slate-900">
            {d.quota.used_window}
            <span className="text-sm text-slate-400"> / {d.quota.per_window}</span>
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-3.5">
          <p className="text-xs text-slate-500 mb-1">Eng ko'p surish</p>
          <p className="text-2xl font-semibold text-slate-900">
            {d.max_shift_days}
            <span className="text-sm text-slate-400"> kun</span>
          </p>
        </div>
      </div>

      <p className="text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 mb-3 flex items-start gap-2">
        <Info size={14} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
      <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 flex items-start gap-2">
        <AlertTriangle size={14} className="shrink-0 mt-0.5" />
        {d.cannot_cancel}
      </p>

      <button
        onClick={() => setAdding(true)}
        className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium mb-5"
      >
        Darsni boshqa kunga ko'chirish
      </button>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">
          Hali dars ko'chirilmagan.
        </p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <div
              key={r.id}
              className="bg-white border border-slate-200 rounded-xl p-3.5"
            >
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-sm font-medium text-slate-900">
                  {r.group}
                </span>
                <span className="text-sm text-slate-600 flex items-center gap-1.5">
                  {formatDate(r.from_date)}
                  <ArrowRight size={13} className="text-slate-400" />
                  {formatDate(r.to_date)}
                </span>
                <span
                  className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                    TONE[r.status_tone] || TONE.slate
                  }`}
                >
                  {r.status_label}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {r.reason_label}
                {r.decided_by ? ` · ${r.decided_by}` : ""}
                {r.decision_note ? ` — ${r.decision_note}` : ""}
              </p>
            </div>
          ))}
        </div>
      )}

      {adding && d && (
        <MoveForm
          data={d}
          onClose={() => setAdding(false)}
          onDone={() => {
            setAdding(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function Quota({ label, q }: { label: string; q: MyReschedules["quota"] }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p
        className={`text-2xl font-semibold ${
          q.left > 0 ? "text-emerald-600" : "text-amber-600"
        }`}
      >
        {q.left}
        <span className="text-sm text-slate-400"> / {q.per_month}</span>
      </p>
      {q.left === 0 && (
        <p className="text-xs text-amber-600 mt-0.5">tasdiq kerak bo'ladi</p>
      )}
    </div>
  );
}

function MoveForm({
  data,
  onClose,
  onDone,
}: {
  data: MyReschedules;
  onClose: () => void;
  onDone: () => void;
}) {
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([]);
  const [f, setF] = useState({
    group_id: "",
    from_date: "",
    to_date: "",
    reason: "",
    note: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<{ rows: { id: number; name: string }[] }>("/me/groups")
      .then((d) => setGroups(d.rows))
      .catch(() => {});
  }, []);

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post("/me/reschedules", {
        group_id: Number(f.group_id),
        from_date: f.from_date,
        to_date: f.to_date,
        reason: f.reason || null,
        note: f.note || null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Darsni ko'chirish</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <select
          value={f.group_id}
          onChange={(e) => setF({ ...f, group_id: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2"
        >
          <option value="">Guruhni tanlang *</option>
          {groups.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>

        <div className="grid grid-cols-2 gap-2 mb-2">
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Qaysi dars
            </label>
            <input
              type="date"
              value={f.from_date}
              onChange={(e) => setF({ ...f, from_date: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              Qaysi kunga
            </label>
            <input
              type="date"
              value={f.to_date}
              onChange={(e) => setF({ ...f, to_date: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <select
          value={f.reason}
          onChange={(e) => setF({ ...f, reason: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2"
        >
          <option value="">Sababni tanlang</option>
          {data.reasons.map((r) => (
            <option key={r.key} value={r.key}>
              {r.label}
            </option>
          ))}
        </select>

        <textarea
          value={f.note}
          onChange={(e) => setF({ ...f, note: e.target.value })}
          rows={2}
          placeholder="Izoh"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <p className="text-xs text-slate-500 mb-3">
          Kamida {data.min_notice_days} kun oldin so'ralishi kerak, ko'pi
          bilan {data.max_shift_days} kunga ko'chiriladi.
          {data.quota.teacher_auto === false
            ? " Har bir so'rov o'quv bo'limi tasdig'idan o'tadi."
            : data.quota.left === 0
            ? " Kvotangiz tugagan — so'rov tasdiqqa yuboriladi."
            : ""}
        </p>

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={save}
          disabled={busy || !f.group_id || !f.from_date || !f.to_date}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
        >
          Yuborish
        </button>
      </div>
    </div>
  );
}

/* ==================================================== O'rinbosar */
function CoverTab() {
  const [d, setD] = useState<MySubstitutions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = () => {
    api
      .get<MySubstitutions>("/me/substitutions")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  const decide = async (id: number, decision: string) => {
    setBusy(true);
    try {
      await api.post(`/me/substitutions/${id}/decide`, { decision });
      load();
    } finally {
      setBusy(false);
    }
  };

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  return (
    <div>
      <button
        onClick={() => setAdding(true)}
        className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium mb-5"
      >
        O'rniga o'tishni so'rash
      </button>

      <Section
        title="Ochiq takliflar — o'ta olasizmi?"
        rows={d.open_offers}
        empty="Hozircha ochiq taklif yo'q."
        action={(s) => (
          <button
            onClick={() => decide(s.id, "accepted")}
            disabled={busy}
            className="text-xs bg-emerald-600 text-white rounded-lg px-3 py-1.5 font-medium disabled:opacity-40"
          >
            Men o'taman
          </button>
        )}
      />

      <Section
        title="Menga taklif qilinganlar"
        rows={d.assigned_to_me}
        empty="Sizga taklif yo'q."
        action={(s) =>
          s.open ? (
            <div className="flex gap-1.5">
              <button
                onClick={() => decide(s.id, "accepted")}
                disabled={busy}
                className="text-xs bg-emerald-600 text-white rounded-lg px-3 py-1.5 font-medium"
              >
                Roziman
              </button>
              <button
                onClick={() => decide(s.id, "declined")}
                disabled={busy}
                className="text-xs border border-slate-300 text-slate-600 rounded-lg px-3 py-1.5"
              >
                Yo'q
              </button>
            </div>
          ) : null
        }
      />

      <Section
        title="Mening so'rovlarim"
        rows={d.my_requests}
        empty="Siz hali o'rinbosar so'ramagansiz."
        action={(s) =>
          s.status === "offered" || s.status === "accepted" ? (
            <button
              onClick={() => decide(s.id, "cancelled")}
              disabled={busy}
              className="text-xs border border-slate-300 text-slate-600 rounded-lg px-3 py-1.5"
            >
              Bekor qilish
            </button>
          ) : null
        }
      />

      <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
        <UserCheck size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {adding && (
        <CoverForm
          data={d}
          onClose={() => setAdding(false)}
          onDone={() => {
            setAdding(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function Section({
  title,
  rows,
  empty,
  action,
}: {
  title: string;
  rows: SubstitutionRow[];
  empty: string;
  action: (s: SubstitutionRow) => React.ReactNode;
}) {
  return (
    <div className="mb-5">
      <p className="text-sm font-medium text-slate-700 mb-2">{title}</p>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-3">{empty}</p>
      ) : (
        <div className="space-y-2">
          {rows.map((s) => (
            <div
              key={s.id}
              className="bg-white border border-slate-200 rounded-xl p-3.5 flex items-center gap-3 flex-wrap"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900">
                  {s.group} · {formatDate(s.lesson_date)}
                  {s.lesson_time ? ` ${s.lesson_time}` : ""}
                </p>
                <p className="text-xs text-slate-500">
                  {s.original_teacher}
                  {s.substitute_teacher
                    ? ` → ${s.substitute_teacher}`
                    : " · o'rinbosar izlanmoqda"}
                  {s.reason ? ` · ${s.reason_label}` : ""}
                </p>
              </div>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                  TONE[s.status_tone] || TONE.slate
                }`}
              >
                {s.status_label}
              </span>
              {action(s)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CoverForm({
  data,
  onClose,
  onDone,
}: {
  data: MySubstitutions;
  onClose: () => void;
  onDone: () => void;
}) {
  const [f, setF] = useState({
    group_id: "",
    lesson_date: "",
    reason: "",
    note: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post("/me/substitutions", {
        group_id: Number(f.group_id),
        lesson_date: f.lesson_date,
        reason: f.reason || null,
        note: f.note || null,
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">O'rinbosar so'rash</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <select
          value={f.group_id}
          onChange={(e) => setF({ ...f, group_id: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2"
        >
          <option value="">Guruhni tanlang *</option>
          {data.my_groups.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>

        <input
          type="date"
          value={f.lesson_date}
          onChange={(e) => setF({ ...f, lesson_date: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-2"
        />

        <select
          value={f.reason}
          onChange={(e) => setF({ ...f, reason: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-2"
        >
          <option value="">Sababni tanlang</option>
          {data.reasons.map((r) => (
            <option key={r.key} value={r.key}>
              {r.label}
            </option>
          ))}
        </select>

        <textarea
          value={f.note}
          onChange={(e) => setF({ ...f, note: e.target.value })}
          rows={2}
          placeholder="Izoh"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <p className="text-xs text-slate-500 mb-3">
          So'rov ochiq taklif bo'lib chiqadi — filialdagi boshqa ustozlar
          ko'radi va xohlagani oladi.
        </p>

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={save}
          disabled={busy || !f.group_id || !f.lesson_date}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
        >
          Yuborish
        </button>
      </div>
    </div>
  );
}
