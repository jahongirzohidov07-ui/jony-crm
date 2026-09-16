import { useEffect, useState } from "react";
import {
  Info, X, AlertTriangle, ChevronRight, Plus, CalendarClock,
  ClipboardList, HandCoins,
} from "lucide-react";
import { api } from "../lib/api";
import { BlacklistBadge } from "./HrBlacklist";
import { useAuth } from "../lib/AuthContext";
import { Time24Input } from "./Time24Input";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  teal: "bg-teal-100 text-teal-700",
  emerald: "bg-emerald-100 text-emerald-700",
  red: "bg-red-100 text-red-700",
  indigo: "bg-indigo-100 text-indigo-700",
  orange: "bg-orange-100 text-orange-700",
};

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * ATS kanban: har ustun — bosqich, har karta — ariza.
 *
 * Bosqich ARIZADA saqlanadi, nomzodda emas: bir odam ustozlikka rad
 * etilib administratorlikka olinishi mumkin. Muddati o'tganlar
 * qizil — nomzod javob kutib charchasa boshqa joyga ketadi.
 */
export function AtsBoard() {
  const { user } = useAuth();
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  const load = () => {
    api
      .get<Any>("/ats/pipeline")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, []);

  if (err) return <p className="text-sm text-slate-500 py-6">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <span className="px-2 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700">
          {d.open} ochiq ariza
        </span>
        <span className="px-2 py-1 rounded-lg text-xs font-medium bg-emerald-100 text-emerald-700">
          {d.hired} olindi
        </span>
        {d.overdue > 0 && (
          <span className="px-2 py-1 rounded-lg text-xs font-medium bg-red-100 text-red-700 flex items-center gap-1">
            <AlertTriangle size={11} /> {d.overdue} kechikkan
          </span>
        )}
        <span className="px-2 py-1 rounded-lg text-xs font-medium bg-indigo-100 text-indigo-700">
          {d.pool} talent pool
        </span>
        <div className="flex-1" />
        <button
          onClick={() => setAdding(true)}
          className="flex items-center gap-1 bg-brand-600 text-white rounded-lg px-3 py-1.5 text-sm font-medium"
        >
          <Plus size={14} /> Yangi ariza
        </button>
      </div>

      <div className="overflow-x-auto pb-2">
        <div className="flex gap-3 min-w-max">
          {d.columns.map((col: Any) => (
            <div key={col.key} className="w-56 shrink-0">
              <div className="flex items-center gap-1.5 mb-2">
                <span
                  className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${
                    TONE[col.tone] || TONE.slate
                  }`}
                >
                  {col.label}
                </span>
                <span className="text-xs text-slate-400">{col.count}</span>
                {col.overdue > 0 && (
                  <span className="text-xs text-red-600">
                    ({col.overdue}!)
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {col.rows.map((r: Any) => (
                  <button
                    key={r.id}
                    onClick={() => setOpen(r.id)}
                    className={`w-full text-left bg-white border rounded-lg p-2.5 hover:border-brand-400 transition ${
                      r.overdue ? "border-red-300" : "border-slate-200"
                    }`}
                  >
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {r.candidate}
                      <BlacklistBadge hit={r.blacklist} />
                    </p>
                    {/* Vakansiya ochilmagan bo'lsa ham qaysi ishga
                        kelgani ko'rinsin (2026-08-15) */}
                    <p className="text-xs text-slate-400 truncate">
                      {r.role_label || r.vacancy || "lavozim ko'rsatilmagan"}
                      {r.subject ? ` · ${r.subject}` : ""}
                    </p>
                    <p
                      className={`text-[11px] mt-1 ${
                        r.overdue ? "text-red-600 font-medium" : "text-slate-400"
                      }`}
                    >
                      {r.days_in_stage} kun
                      {r.sla_days ? ` / ${r.sla_days}` : ""}
                    </p>
                  </button>
                ))}
                {col.rows.length === 0 && (
                  <p className="text-xs text-slate-300 text-center py-3">
                    bo'sh
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <RejectedPanel d={d} onOpen={setOpen} />

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>

      {open && (
        <AppModal
          id={open}
          canApproveOffer={["founder", "finance_director"].includes(
            user?.role || ""
          )}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
      {adding && (
        <NewAppModal
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

function NewAppModal({
  data,
  onClose,
  onDone,
}: {
  data: Any;
  onClose: () => void;
  onDone: () => void;
}) {
  const [f, setF] = useState({
    full_name: "",
    phone: "",
    vacancy_id: "",
    source: "",
  });
  const [dups, setDups] = useState<Any[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const save = async (force = false, candidateId?: number) => {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<Any>("/ats/applications", {
        candidate_id: candidateId ?? null,
        full_name: candidateId ? null : f.full_name,
        phone: f.phone || null,
        vacancy_id: f.vacancy_id ? Number(f.vacancy_id) : null,
        source: f.source || null,
        force,
      });
      if (r.duplicate) {
        setDups(r.candidates);
        return;
      }
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
        className="bg-white rounded-xl p-5 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Yangi ariza</h3>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>

        <input
          value={f.full_name}
          onChange={(e) => setF({ ...f, full_name: e.target.value })}
          placeholder="Nomzod F.I.O. *"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-2"
        />
        <input
          value={f.phone}
          onChange={(e) => setF({ ...f, phone: e.target.value })}
          placeholder="Telefon"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-2"
        />
        <select
          value={f.vacancy_id}
          onChange={(e) => setF({ ...f, vacancy_id: e.target.value })}
          className="w-full border border-slate-300 rounded-lg px-2 py-2 text-sm mb-3"
        >
          <option value="">Vakansiya (ixtiyoriy)</option>
          {data.vacancies.map((v: Any) => (
            <option key={v.id} value={v.id}>
              {v.title}
            </option>
          ))}
        </select>

        {dups.length > 0 && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 mb-3">
            <p className="text-xs text-amber-800 mb-2">
              Shunday nomzod allaqachon bor — tanlang yoki baribir yangi
              oching:
            </p>
            {dups.map((c) => (
              <button
                key={c.candidate_id}
                onClick={() => save(false, c.candidate_id)}
                className="w-full text-left text-sm px-2 py-1.5 rounded-lg hover:bg-amber-100"
              >
                {c.full_name}{" "}
                <span className="text-xs text-slate-500">
                  ({c.why} mos · {c.applications} ariza)
                </span>
              </button>
            ))}
            <button
              onClick={() => save(true)}
              className="text-xs text-amber-700 underline mt-1"
            >
              Baribir yangi nomzod ochish
            </button>
          </div>
        )}

        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
        <button
          onClick={() => save()}
          disabled={busy || !f.full_name.trim()}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-40"
        >
          Ochish
        </button>
      </div>
    </div>
  );
}

/** Ariza kartasi: bosqich, tarix, suhbatlar, varaqalar, taklif. */
function AppModal({
  id,
  canApproveOffer,
  onClose,
}: {
  id: number;
  canApproveOffer: boolean;
  onClose: () => void;
}) {
  const [d, setD] = useState<Any>(null);
  const [offers, setOffers] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<"main" | "score" | "offer">("main");

  const load = () => {
    api.get<Any>(`/ats/applications/${id}`).then(setD).catch(() => {});
    api
      .get<Any>(`/ats/offers?application_id=${id}`)
      .then(setOffers)
      .catch(() => {});
  };
  useEffect(load, [id]);

  const move = async (stage: string, reason?: string, note?: string) => {
    setErr("");
    try {
      await api.post(`/ats/applications/${id}/move`, {
        stage,
        reason: reason || null,
        note: note || null,
      });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  if (!d)
    return (
      <div className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center">
        <p className="text-sm text-white">Yuklanmoqda…</p>
      </div>
    );

  const nextIdx = d.flow.indexOf(d.stage);
  const next = nextIdx >= 0 ? d.flow[nextIdx + 1] : null;
  const nextLabel = d.stages.find((s: Any) => s.key === next)?.label;

  return (
    <div
      className="fixed inset-0 bg-slate-900/40 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-5 w-full max-w-2xl max-h-[92vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900">{d.candidate}</h3>
            <BlacklistBadge hit={d.blacklist} />
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                TONE[d.stage_tone] || TONE.slate
              }`}
            >
              {d.stage_label}
            </span>
            {d.overdue && (
              <span className="px-1.5 py-0.5 rounded text-[11px] bg-red-100 text-red-700">
                {d.days_in_stage} kun kutmoqda
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-slate-400">
            <X size={18} />
          </button>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          {d.public_id} · {d.role_label || d.vacancy
            || "lavozim ko'rsatilmagan"}
          {d.subject ? ` · ${d.subject}` : ""} · {d.phone || "—"}
        </p>

        <div className="h-1.5 bg-slate-100 rounded-full mb-4 overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all"
            style={{ width: `${d.progress}%` }}
          />
        </div>

        {d.closed && (d.reject_reason_label || d.reject_note) && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-3 py-2">
            <p className="text-sm font-medium text-red-800">
              {d.stage === "withdrew" ? "O'zi voz kechdi" : "Rad etildi"} —{" "}
              {d.reject_reason_label || "sabab yozilmagan"}
            </p>
            {d.reject_note && (
              <p className="text-xs text-red-700 mt-0.5">{d.reject_note}</p>
            )}
            {d.pool && (
              <p className="text-[11px] text-red-600 mt-1">
                Talent poolda — keyingi vakansiyaga qaytarish mumkin.
              </p>
            )}
          </div>
        )}

        {!d.closed && (
          <div className="flex gap-2 mb-4 flex-wrap">
            {next && (
              <button
                onClick={() => move(next)}
                className="flex items-center gap-1 bg-brand-600 text-white rounded-lg px-3 py-1.5 text-sm font-medium"
              >
                {nextLabel} <ChevronRight size={14} />
              </button>
            )}
            <RejectButton
              onReject={(r, n) => move("rejected", r, n)}
              data={d}
            />
          </div>
        )}
        {err && <p className="text-sm text-red-600 mb-2">{err}</p>}

        <div className="flex gap-1 border-b border-slate-200 mb-4">
          {[
            { key: "main", label: "Tarix va suhbatlar" },
            { key: "score", label: "Baholash varaqasi" },
            { key: "offer", label: "Taklif" },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key as Any)}
              className={`px-3 py-2 text-sm border-b-2 -mb-px ${
                tab === t.key
                  ? "border-brand-600 text-brand-700 font-medium"
                  : "border-transparent text-slate-500"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "main" && <MainTab d={d} onChange={load} />}
        {tab === "score" && <ScoreTab appId={id} />}
        {tab === "offer" && (
          <OfferTab
            appId={id}
            offers={offers}
            canApprove={canApproveOffer}
            onChange={load}
          />
        )}
      </div>
    </div>
  );
}

function RejectButton({
  onReject,
  data,
}: {
  onReject: (reason: string, note: string) => void;
  data: Any;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  if (!open)
    return (
      <button
        onClick={() => setOpen(true)}
        className="border border-slate-300 text-slate-600 rounded-lg px-3 py-1.5 text-sm"
      >
        Rad etish
      </button>
    );
  return (
    <span className="flex items-center gap-1">
      <select
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
      >
        <option value="">Sabab…</option>
        {data.reject_reasons.map((r: Any) => (
          <option key={r.key} value={r.key}>
            {r.label}
            {r.pool ? " (poolga)" : ""}
          </option>
        ))}
      </select>
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Izoh (ixtiyoriy)"
        className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm w-44"
      />
      <button
        onClick={() => reason && onReject(reason, note)}
        disabled={!reason}
        className="bg-red-600 text-white rounded-lg px-3 py-1.5 text-sm disabled:opacity-40"
      >
        Rad
      </button>
    </span>
  );
}

/**
 * Rad etilganlar — kanbanda ko'rinmaydigan yopilgan arizalar.
 *
 * Sabab HR uchun eng qimmatli ma'lumot: "nega odam topilmayapti"
 * degan savolga aynan shu ro'yxat javob beradi. Tepada sabablar
 * kesimi, ichida esa har bir nomzod va izohi.
 */
function RejectedPanel({
  d,
  onOpen,
}: {
  d: Any;
  onOpen: (id: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const rows: Any[] = (d.rows || []).filter(
    (r: Any) => r.stage === "rejected" || r.stage === "withdrew"
  );
  if (rows.length === 0) return null;

  const by: Record<string, number> = {};
  rows.forEach((r: Any) => {
    const k = r.reject_reason_label || "Sabab yozilmagan";
    by[k] = (by[k] || 0) + 1;
  });
  const top = Object.keys(by).sort((a, b) => by[b] - by[a]);

  return (
    <div className="mt-5 bg-white border border-slate-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-3 text-left hover:bg-slate-50"
      >
        <span className="text-sm font-medium text-slate-800">
          Rad etilganlar
        </span>
        <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-red-100 text-red-700">
          {rows.length}
        </span>
        <div className="flex-1" />
        <span className="text-xs text-slate-400">
          {open ? "yopish" : "ro'yxatni ochish"}
        </span>
      </button>

      <div className="px-4 pb-3 flex flex-wrap gap-1.5">
        {top.map((label) => (
          <span
            key={label}
            className="px-2 py-0.5 rounded-lg text-[11px] bg-slate-100 text-slate-600"
          >
            {label} · {by[label]}
          </span>
        ))}
      </div>

      {open && (
        <table className="w-full text-sm border-t border-slate-100">
          <tbody className="divide-y divide-slate-100">
            {rows.map((r: Any) => (
              <tr
                key={r.id}
                onClick={() => onOpen(r.id)}
                className="hover:bg-slate-50 cursor-pointer align-top"
              >
                <td className="px-4 py-2">
                  <p className="text-slate-800">{r.candidate}</p>
                  <p className="text-xs text-slate-400">
                    {r.role_label || r.vacancy || "lavozim ko'rsatilmagan"}
                    {r.subject ? ` · ${r.subject}` : ""}
                    {r.branch ? ` · ${r.branch}` : ""}
                  </p>
                </td>
                <td className="px-3 py-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-red-100 text-red-700">
                    {r.reject_reason_label || "sabab yozilmagan"}
                  </span>
                  {r.reject_note && (
                    <p className="text-xs text-slate-500 mt-1">
                      {r.reject_note}
                    </p>
                  )}
                </td>
                <td className="px-4 py-2 text-right text-xs text-slate-400 whitespace-nowrap">
                  {r.stage === "withdrew" ? "o'zi voz kechdi" : ""}
                  {r.pool ? " · talent pool" : ""}
                  {r.closed_at ? ` · ${String(r.closed_at).slice(0, 10)}` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function MainTab({ d, onChange }: { d: Any; onChange: () => void }) {
  const [planning, setPlanning] = useState(false);
  const [f, setF] = useState({ kind: "hr", date: "", time: "" });
  const [err, setErr] = useState("");

  const plan = async () => {
    setErr("");
    try {
      await api.post("/ats/interviews", {
        application_id: d.id,
        kind: f.kind,
        date: f.date,
        time: f.time || null,
      });
      setPlanning(false);
      onChange();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <CalendarClock size={14} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Suhbatlar</p>
        {!d.closed && (
          <button
            onClick={() => setPlanning(!planning)}
            className="text-xs text-brand-600 ml-auto"
          >
            + suhbat qo'yish
          </button>
        )}
      </div>

      {planning && (
        <div className="flex gap-2 mb-2 flex-wrap items-center rounded-lg border border-slate-200 p-2">
          <select
            value={f.kind}
            onChange={(e) => setF({ ...f, kind: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
          >
            {d.interview_kinds.map((k: Any) => (
              <option key={k.key} value={k.key}>
                {k.label} ({k.minutes} daq)
              </option>
            ))}
          </select>
          <input
            type="date"
            value={f.date}
            onChange={(e) => setF({ ...f, date: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
          />
          <Time24Input
            value={f.time}
            onChange={(e) => setF({ ...f, time: e.target.value })}
            className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
          />
          <button
            onClick={plan}
            disabled={!f.date}
            className="bg-brand-600 text-white rounded-lg px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Saqlash
          </button>
          {err && <p className="text-xs text-red-600 w-full">{err}</p>}
        </div>
      )}

      {d.interviews.length === 0 ? (
        <p className="text-xs text-slate-400 mb-4">Hali suhbat yo'q.</p>
      ) : (
        <div className="space-y-1 mb-4">
          {d.interviews.map((i: Any) => (
            <div
              key={i.id}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-100 text-sm"
            >
              <span className="text-slate-700">{i.kind_label}</span>
              <span className="text-xs text-slate-400">
                {i.date_text} {i.time}
              </span>
              <span className="text-xs text-slate-400">{i.interviewer}</span>
              <span
                className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  TONE[i.status_tone] || TONE.slate
                }`}
              >
                {i.status_label}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 mb-2">
        <ClipboardList size={14} className="text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Bosqich tarixi</p>
      </div>
      <div className="space-y-1">
        {d.history.map((h: Any) => (
          <div
            key={h.id}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-50 text-xs text-slate-600"
          >
            <span>
              {h.from_label ? `${h.from_label} → ` : ""}
              <b>{h.to_label}</b>
            </span>
            {h.days != null && h.days > 0 && (
              <span className="text-slate-400">({h.days} kun)</span>
            )}
            {h.reason_label && (
              <span className="text-red-600">{h.reason_label}</span>
            )}
            <span className="ml-auto text-slate-400">{h.by}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Baholash varaqasi: mening varaqam + jamoa xulosasi. */
function ScoreTab({ appId }: { appId: number }) {
  const [d, setD] = useState<Any>(null);
  const [mine, setMine] = useState<Record<string, number>>({});
  const [rec, setRec] = useState("");
  const [strengths, setStrengths] = useState("");
  const [concerns, setConcerns] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [showQ, setShowQ] = useState(false);

  const load = () => {
    api
      .get<Any>(`/ats/scorecards/${appId}`)
      .then((x) => {
        setD(x);
        if (x.mine) {
          setMine(x.mine.scores || {});
          setRec(x.mine.recommendation || "");
          setStrengths(x.mine.strengths || "");
          setConcerns(x.mine.concerns || "");
        }
      })
      .catch(() => {});
  };
  useEffect(load, [appId]);

  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post("/ats/scorecards", {
        application_id: appId,
        scores: mine,
        recommendation: rec || null,
        strengths: strengths || null,
        concerns: concerns || null,
      });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda…</p>;

  return (
    <div>
      {d.rows.length > 0 && (
        <div className="rounded-lg border border-slate-200 p-3 mb-4">
          <p className="text-xs text-slate-500 mb-1">
            Jamoa xulosasi — {d.rows.length} varaqa
          </p>
          <p className="text-lg font-semibold text-slate-900">
            {d.avg_percent != null ? `${d.avg_percent}%` : "—"}{" "}
            <span
              className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                TONE[d.avg_tone] || TONE.slate
              }`}
            >
              {d.avg_label}
            </span>
          </p>
          <div className="mt-2 space-y-0.5">
            {d.rows.map((r: Any) => (
              <p key={r.id} className="text-xs text-slate-500">
                {r.author}: {r.percent != null ? `${r.percent}%` : "—"} ·{" "}
                <span
                  className={`px-1 rounded ${
                    TONE[r.recommendation_tone] || TONE.slate
                  }`}
                >
                  {r.recommendation_label || "tavsiyasiz"}
                </span>
              </p>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-medium text-slate-700">Mening varaqam</p>
        <button
          onClick={() => setShowQ(!showQ)}
          className="text-xs text-brand-600"
        >
          {showQ ? "savollarni yashirish" : "savollar bankisi"}
        </button>
      </div>

      {showQ && (
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 mb-3 max-h-44 overflow-y-auto">
          {d.questions.map((q: Any, i: number) => (
            <p key={i} className="text-xs text-slate-600 mb-1">
              <b>{q.label}:</b> {q.text}
            </p>
          ))}
        </div>
      )}

      {d.competency_groups.map((g: Any) => (
        <div key={g.key} className="mb-3">
          <p className="text-xs font-medium text-slate-500 mb-1.5">
            {g.label}
          </p>
          <div className="space-y-1">
            {d.competencies
              .filter((c: Any) => c.group === g.key)
              .map((c: Any) => (
                <div key={c.key} className="flex items-center gap-2">
                  <span className="text-sm text-slate-700 flex-1">
                    {c.label}
                    {c.weight >= 3 && (
                      <span className="text-slate-300"> ×{c.weight}</span>
                    )}
                  </span>
                  <div className="flex gap-0.5">
                    {[1, 2, 3, 4, 5].map((v) => (
                      <button
                        key={v}
                        title={d.score_labels[v]}
                        onClick={() => setMine({ ...mine, [c.key]: v })}
                        className={`w-7 h-7 rounded text-xs font-medium ${
                          mine[c.key] === v
                            ? "bg-brand-600 text-white"
                            : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                        }`}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}

      <div className="grid grid-cols-2 gap-2 mb-2">
        <textarea
          value={strengths}
          onChange={(e) => setStrengths(e.target.value)}
          rows={2}
          placeholder="Kuchli tomonlari"
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        />
        <textarea
          value={concerns}
          onChange={(e) => setConcerns(e.target.value)}
          rows={2}
          placeholder="Xavotirlar"
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        />
      </div>

      <div className="flex gap-2 items-center">
        <select
          value={rec}
          onChange={(e) => setRec(e.target.value)}
          className="border border-slate-300 rounded-lg px-2 py-2 text-sm flex-1"
        >
          <option value="">Yakuniy tavsiya…</option>
          {d.recommendations.map((r: Any) => (
            <option key={r.key} value={r.key}>
              {r.label}
            </option>
          ))}
        </select>
        <button
          onClick={save}
          disabled={busy}
          className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          Saqlash
        </button>
      </div>
      {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
      <p className="text-xs text-slate-400 mt-2">{d.hint}</p>
    </div>
  );
}

/** Taklif: versiyalar zanjiri va holat mashinasi. */
function OfferTab({
  appId,
  offers,
  canApprove,
  onChange,
}: {
  appId: number;
  offers: Any;
  canApprove: boolean;
  onChange: () => void;
}) {
  const [f, setF] = useState({
    position: "",
    salary: "",
    salary_note: "oyiga",
    start_date: "",
    probation_months: "2",
  });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const reload = () => onChange();

  const create = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.post("/ats/offers", {
        application_id: appId,
        position: f.position || null,
        salary: Number(f.salary),
        salary_note: f.salary_note || null,
        start_date: f.start_date || null,
        probation_months: f.probation_months
          ? Number(f.probation_months)
          : null,
      });
      reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const act = async (oid: number, action: string, note?: string) => {
    setErr("");
    try {
      await api.post(`/ats/offers/${oid}/action`, {
        action,
        note: note || null,
      });
      reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  };

  const rows = offers?.rows || [];
  const hasOpen = rows.some((r: Any) => r.open);

  return (
    <div>
      {rows.length === 0 && (
        <p className="text-xs text-slate-400 mb-3">Hali taklif yo'q.</p>
      )}

      <div className="space-y-2 mb-4">
        {rows.map((o: Any) => (
          <div
            key={o.id}
            className="rounded-lg border border-slate-200 p-3"
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-slate-400">
                {o.public_id} · v{o.version}
              </span>
              <span className="text-sm font-medium text-slate-900">
                {o.salary?.toLocaleString().replace(/,/g, " ")} so'm{" "}
                <span className="text-xs text-slate-400">
                  {o.salary_note}
                </span>
              </span>
              <span
                className={`ml-auto px-2 py-0.5 rounded text-[11px] font-medium ${
                  TONE[o.status_tone] || TONE.slate
                }`}
              >
                {o.status_label}
              </span>
            </div>
            {o.position && (
              <p className="text-xs text-slate-500 mt-1">{o.position}</p>
            )}
            {o.decline_reason && (
              <p className="text-xs text-red-600 mt-1">
                Rad sababi: {o.decline_reason}
              </p>
            )}
            <div className="flex gap-1.5 mt-2 flex-wrap">
              {o.status === "draft" && (
                <ActBtn onClick={() => act(o.id, "submit")}>
                  Tasdiqqa yuborish
                </ActBtn>
              )}
              {o.status === "approval" && canApprove && (
                <>
                  <ActBtn tone="emerald" onClick={() => act(o.id, "approve")}>
                    Tasdiqlash
                  </ActBtn>
                  <ActBtn tone="slate" onClick={() => act(o.id, "reject")}>
                    Qoralamaga qaytarish
                  </ActBtn>
                </>
              )}
              {o.status === "approval" && !canApprove && (
                <p className="text-xs text-amber-600">
                  Rahbariyat tasdig'i kutilmoqda
                </p>
              )}
              {o.status === "approved" && (
                <ActBtn tone="violet" onClick={() => act(o.id, "send")}>
                  Nomzodga yuborish
                </ActBtn>
              )}
              {o.status === "sent" && (
                <>
                  <ActBtn tone="emerald" onClick={() => act(o.id, "accept")}>
                    Qabul qildi
                  </ActBtn>
                  <ActBtn
                    tone="red"
                    onClick={() => {
                      const why = prompt("Rad sababi:");
                      if (why) act(o.id, "decline", why);
                    }}
                  >
                    Rad etdi
                  </ActBtn>
                </>
              )}
              {o.open && (
                <ActBtn tone="slate" onClick={() => act(o.id, "withdraw")}>
                  Qaytarib olish
                </ActBtn>
              )}
            </div>
          </div>
        ))}
      </div>

      {!hasOpen && (
        <div className="rounded-lg border border-dashed border-slate-300 p-3">
          <p className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-1.5">
            <HandCoins size={14} className="text-slate-400" />
            Yangi taklif
          </p>
          <div className="grid grid-cols-2 gap-2 mb-2">
            <input
              value={f.position}
              onChange={(e) => setF({ ...f, position: e.target.value })}
              placeholder="Lavozim"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
            <input
              type="number"
              value={f.salary}
              onChange={(e) => setF({ ...f, salary: e.target.value })}
              placeholder="Ish haqi (so'm) *"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
            <input
              type="date"
              value={f.start_date}
              onChange={(e) => setF({ ...f, start_date: e.target.value })}
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
            <input
              type="number"
              value={f.probation_months}
              onChange={(e) =>
                setF({ ...f, probation_months: e.target.value })
              }
              placeholder="Sinov (oy)"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={create}
            disabled={busy || !f.salary}
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
          >
            Taklif tuzish
          </button>
        </div>
      )}

      {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
      {offers?.hint && (
        <p className="text-xs text-slate-400 mt-3">{offers.hint}</p>
      )}
    </div>
  );
}

function ActBtn({
  children,
  onClick,
  tone = "brand",
}: {
  children: Any;
  onClick: () => void;
  tone?: string;
}) {
  const cls: Record<string, string> = {
    brand: "bg-brand-600 text-white",
    emerald: "bg-emerald-600 text-white",
    violet: "bg-violet-600 text-white",
    red: "bg-red-600 text-white",
    slate: "border border-slate-300 text-slate-600",
  };
  return (
    <button
      onClick={onClick}
      className={`rounded-lg px-2.5 py-1 text-xs font-medium ${
        cls[tone] || cls.brand
      }`}
    >
      {children}
    </button>
  );
}
