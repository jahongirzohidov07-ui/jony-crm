import { useEffect, useState } from "react";
import {
  AlertTriangle, FileText, Plane, LogOut, Info, X,
} from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  amber: "bg-amber-100 text-amber-700",
  emerald: "bg-emerald-100 text-emerald-700",
  teal: "bg-teal-100 text-teal-700",
  red: "bg-red-100 text-red-700",
};

/** HR umumiy ko'rinishi: barcha fazalarning signallari bitta ekranda. */
export function HrOverviewTab() {
  const [d, setD] = useState<Any>(null);
  useEffect(() => {
    api.get<Any>("/hr/overview").then(setD).catch(() => {});
  }, []);
  if (!d) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;

  return (
    <div>
      {d.alerts.length > 0 && (
        <div className="space-y-1.5 mb-4">
          {d.alerts.map((a: Any, i: number) => (
            <p
              key={i}
              className={`text-sm rounded-lg px-3 py-2 border flex items-center gap-2 ${
                a.tone === "red"
                  ? "bg-red-50 border-red-200 text-red-800"
                  : "bg-amber-50 border-amber-200 text-amber-800"
              }`}
            >
              <AlertTriangle size={14} className="shrink-0" />
              {a.text}
            </p>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {d.cards.map((c: Any) => (
          <div
            key={c.key}
            className="bg-white border border-slate-200 rounded-xl p-4"
          >
            <p className="text-xs text-slate-500 mb-1">{c.label}</p>
            <p className="text-2xl font-semibold text-slate-900">
              {c.value}
            </p>
          </div>
        ))}
      </div>

      {d.reject_reasons.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Rad etish sabablari — "nega odam topilmayapti"
          </p>
          {d.reject_reasons.map((r: Any) => (
            <div key={r.key} className="flex items-center gap-2 mb-1">
              <span className="text-sm text-slate-600 flex-1">
                {r.label}
              </span>
              <span className="text-sm font-medium text-slate-900">
                {r.count}
              </span>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-500 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}

/** Hujjatlar, ta'til va ketish — bitta "hayotiy sikl" tabi. */
export function HrLifecycleTab() {
  const [sub, setSub] = useState<"docs" | "leaves" | "offboard">("leaves");
  return (
    <div>
      <div className="flex gap-1.5 mb-4">
        {[
          { key: "leaves", label: "Ta'til", icon: Plane },
          { key: "docs", label: "Hujjatlar", icon: FileText },
          { key: "offboard", label: "Ketish", icon: LogOut },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setSub(t.key as Any)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${
              sub === t.key
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>
      {sub === "docs" && <DocsSub />}
      {sub === "leaves" && <LeavesSub />}
      {sub === "offboard" && <OffboardSub />}
    </div>
  );
}

function DocsSub() {
  const [d, setD] = useState<Any>(null);
  const load = () => {
    api.get<Any>("/hr/documents").then(setD).catch(() => {});
  };
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {(d.expired.length > 0 || d.expiring.length > 0) && (
        <p className="text-sm rounded-lg px-3 py-2 mb-3 bg-red-50 border border-red-200 text-red-800">
          {d.expired.length > 0 && `${d.expired.length} hujjat muddati o'tgan. `}
          {d.expiring.length > 0 &&
            `${d.expiring.length} hujjat ${d.warn_days} kun ichida tugaydi.`}
        </p>
      )}
      <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Xodim</th>
              <th className="text-left px-3 py-2.5 font-medium">Hujjat</th>
              <th className="text-left px-3 py-2.5 font-medium">Raqam</th>
              <th className="text-right px-4 py-2.5 font-medium">Muddati</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {d.rows.map((r: Any) => (
              <tr key={r.id} className={r.expired ? "bg-red-50/50" : ""}>
                <td className="px-4 py-2.5 text-slate-800">{r.user}</td>
                <td className="px-3 py-2.5 text-slate-600">{r.kind_label}</td>
                <td className="px-3 py-2.5 text-slate-500">
                  {r.number || "—"}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {r.expires_on ? (
                    <span
                      className={
                        r.expired
                          ? "text-red-600 font-medium"
                          : r.expiring
                          ? "text-amber-600 font-medium"
                          : "text-slate-500"
                      }
                    >
                      {r.expires_on}
                      {r.days_left != null && r.days_left >= 0
                        ? ` (${r.days_left} kun)`
                        : " (o'tgan)"}
                    </span>
                  ) : (
                    <span className="text-slate-300">muddatsiz</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Hujjat yo'q. Xodim kartasidan qo'shiladi.
          </p>
        )}
      </div>
    </div>
  );
}

function LeavesSub() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const load = () => {
    api.get<Any>("/hr/leaves").then(setD).catch(() => {});
  };
  useEffect(load, []);

  const decide = async (id: number, decision: string) => {
    setErr("");
    try {
      await api.post(`/hr/leaves/${id}/decide`, { decision });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {d.today.length > 0 && (
        <p className="text-sm rounded-lg px-3 py-2 mb-3 bg-sky-50 border border-sky-200 text-sky-800">
          Bugun ta'tilda: {d.today.map((x: Any) => x.user).join(", ")}
        </p>
      )}
      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
      <div className="space-y-2">
        {d.rows.map((l: Any) => (
          <div
            key={l.id}
            className="bg-white border border-slate-200 rounded-xl p-3.5"
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-slate-400">
                {l.public_id}
              </span>
              <span className="text-sm font-medium text-slate-900">
                {l.user}
              </span>
              <span className="text-xs text-slate-500">
                {l.kind_label} · {l.date_from} — {l.date_to} ({l.days} kun)
              </span>
              <span
                className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                  TONE[l.status_tone] || TONE.slate
                }`}
              >
                {l.status_label}
              </span>
            </div>
            {l.replacement && (
              <p className="text-xs text-slate-500 mt-1">
                O'rinbosar: {l.replacement}
              </p>
            )}
            {l.reason && (
              <p className="text-xs text-slate-500 mt-0.5">{l.reason}</p>
            )}
            {l.status === "pending" && d.can_approve && (
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => decide(l.id, "approved")}
                  className="bg-emerald-600 text-white rounded-lg px-3 py-1 text-xs font-medium"
                >
                  Tasdiqlash
                </button>
                <button
                  onClick={() => decide(l.id, "rejected")}
                  className="border border-slate-300 text-slate-600 rounded-lg px-3 py-1 text-xs"
                >
                  Rad etish
                </button>
              </div>
            )}
          </div>
        ))}
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Ta'til so'rovi yo'q.
          </p>
        )}
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}

function OffboardSub() {
  const [d, setD] = useState<Any>(null);
  const [open, setOpen] = useState<Any>(null);
  const load = () => {
    api.get<Any>("/hr/offboarding").then(setD).catch(() => {});
  };
  useEffect(load, []);
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {d.ours_percent != null && (
        <p className="text-sm rounded-lg px-3 py-2 mb-3 bg-slate-50 border border-slate-200 text-slate-700">
          Ketishlarning <b>{d.ours_percent}%</b> i bizga bog'liq sabablar —
          bu ustidan ishlash mumkin bo'lgan qism.
        </p>
      )}
      <div className="space-y-2">
        {d.rows.map((o: Any) => (
          <button
            key={o.id}
            onClick={() => setOpen(o)}
            className="w-full text-left bg-white border border-slate-200 rounded-xl p-3.5 hover:border-brand-400 transition"
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-slate-900">
                {o.user}
              </span>
              {o.reason_label && (
                <span
                  className={`px-1.5 py-0.5 rounded text-[11px] ${
                    o.ours
                      ? "bg-red-100 text-red-700"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {o.reason_label}
                </span>
              )}
              <span className="ml-auto text-xs text-slate-500">
                {o.done_count}/{o.total_steps} band
                {o.completed ? " · yakunlandi" : ""}
              </span>
            </div>
          </button>
        ))}
        {d.rows.length === 0 && (
          <p className="text-sm text-slate-400 py-8 text-center">
            Ketish jarayoni yo'q — yaxshi belgi.
          </p>
        )}
      </div>
      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {open && (
        <OffboardModal
          row={open}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function OffboardModal({ row, onClose }: { row: Any; onClose: () => void }) {
  const [o, setO] = useState<Any>(row);
  const [err, setErr] = useState("");

  const toggle = async (step: string, done: boolean) => {
    setErr("");
    try {
      const r = await api.post<Any>(`/hr/offboarding/${o.id}/update`, {
        step,
        done,
      });
      setO(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-900">{o.user}</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          {o.reason_label || "sabab ko'rsatilmagan"}
          {o.last_day ? ` · oxirgi kun ${o.last_day}` : ""}
        </p>

        <div className="space-y-1 mb-3">
          {o.steps.map((s: Any) => (
            <label
              key={s.key}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-100 text-sm cursor-pointer"
            >
              <input
                type="checkbox"
                checked={s.done}
                disabled={o.completed}
                onChange={(e) => toggle(s.key, e.target.checked)}
              />
              <span
                className={s.done ? "text-slate-400 line-through" : "text-slate-700"}
              >
                {s.label}
              </span>
            </label>
          ))}
        </div>

        {o.completed && (
          <p className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg p-2">
            Jarayon yakunlandi — hisob o'chirildi.
          </p>
        )}
        {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
      </div>
    </div>
  );
}
