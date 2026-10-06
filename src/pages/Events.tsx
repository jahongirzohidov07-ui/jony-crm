import { useEffect, useMemo, useState } from "react";
import { formatPhone } from "../components/PhoneInput";
import { PartyPopper, Cake, Copy, Check, Plus, Pencil, Trash2, X, CalendarDays } from "lucide-react";
import { api } from "../lib/api";
import { MissingDatesDialog } from "../components/MissingDates";

/**
 * TADBIRLAR (2026-09-14).
 *
 * Event menejerning ish joyi: tug'ilgan kunlar o'z-o'zidan ko'rinadi
 * (o'quvchi va xodim kartasidagi sanadan), tadbirlar esa shu yerda
 * rejalashtiriladi.
 */

type BirthdayRow = {
  who: "student" | "staff";
  who_label: string;
  id: number;
  full_name: string;
  sub: string | null;
  branch: string | null;
  phone: string | null;
  date: string;
  date_label: string;
  days_left: number;
  today: boolean;
  age: number;
};

type Birthdays = {
  days: number;
  rows: BirthdayRow[];
  today: number;
  week: number;
  students: number;
  staff: number;
  missing_students: number;
  missing_staff: number;
};

type EventRow = {
  id: number;
  title: string;
  kind: string;
  kind_label: string;
  event_date: string;
  date_label: string;
  days_left: number;
  start_time: string | null;
  place: string | null;
  branch: string | null;
  audience: string | null;
  budget: number | null;
  status: string;
  status_label: string;
  responsible_id: number | null;
  responsible: string | null;
  note: string | null;
};

type EventList = {
  rows: EventRow[];
  kinds: { key: string; label: string }[];
  statuses: { key: string; label: string; tone: string }[];
  can_manage: boolean;
};

type StaffOption = { id: number; full_name: string; role_label: string };

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  emerald: "bg-emerald-100 text-emerald-700",
  rose: "bg-rose-100 text-rose-700",
};

const empty = {
  title: "", kind: "holiday", event_date: "", start_time: "", place: "",
  audience: "", budget: "", status: "planned", responsible_id: "", note: "",
};

function greeting(r: BirthdayRow): string {
  return r.who === "student"
    ? `${r.full_name}, tug'ilgan kuningiz muborak bo'lsin! Jony Academy jamoasi sizga ` +
      "bilim, sog'lik va katta yutuqlar tilaydi."
    : `${r.full_name}, tug'ilgan kuningiz muborak bo'lsin! Jony Academy jamoasi sizga ` +
      "sog'lik, tinchlik va ishingizda katta yutuqlar tilaydi.";
}

function whenText(days: number): string {
  if (days === 0) return "Bugun!";
  if (days === 1) return "Ertaga";
  if (days < 0) return `${-days} kun oldin`;
  return `${days} kundan keyin`;
}

function money(v: number | null): string {
  if (v == null) return "—";
  return `${Math.round(v).toLocaleString("ru-RU")} so'm`;
}

export default function Events() {
  const [tab, setTab] = useState<"birthdays" | "events">("birthdays");

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
          <PartyPopper size={20} />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Tadbirlar</h1>
          <p className="text-sm text-slate-500">Tug'ilgan kunlar va markaz tadbirlari</p>
        </div>
      </div>

      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1" role="tablist">
        {([["birthdays", "Tug'ilgan kunlar"], ["events", "Tadbirlar rejasi"]] as const).map(([k, lbl]) => (
          <button
            key={k}
            id={`tab-${k}`}
            role="tab"
            aria-selected={tab === k}
            onClick={() => setTab(k)}
            className={`px-4 py-1.5 text-sm rounded-md font-medium ${
              tab === k ? "bg-brand-600 text-white" : "text-slate-600 hover:text-slate-800"}`}
          >
            {lbl}
          </button>
        ))}
      </div>

      {tab === "birthdays" ? <BirthdaysTab /> : <EventsTab />}
    </div>
  );
}

function BirthdaysTab() {
  const [d, setD] = useState<Birthdays | null>(null);
  const [days, setDays] = useState(30);
  const [who, setWho] = useState<"" | "student" | "staff">("");
  const [copied, setCopied] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  // Sanasi kiritilmaganlar (2026-10-06)
  const [missing, setMissing] = useState(false);
  const [rev, setRev] = useState(0);

  useEffect(() => {
    setErr(null);
    api.get<Birthdays>(`/events/birthdays?days=${days}`, rev > 0).then(setD).catch((e) => setErr(e.message));
  }, [days, rev]);

  const rows = useMemo(() => (d ? d.rows.filter((r) => !who || r.who === who) : []), [d, who]);

  if (err) return <p className="text-sm text-red-600">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const copy = async (r: BirthdayRow) => {
    const key = `${r.who}-${r.id}`;
    try {
      await navigator.clipboard.writeText(greeting(r));
      setCopied(key);
      setTimeout(() => setCopied(null), 1800);
    } catch {
      setCopied(null);
    }
  };

  const stats = [
    { label: "Bugun", value: d.today, cls: d.today ? "text-rose-600" : "text-slate-800" },
    { label: "7 kun ichida", value: d.week, cls: "text-slate-800" },
    { label: "O'quvchilar", value: d.students, cls: "text-slate-800" },
    { label: "Xodimlar", value: d.staff, cls: "text-slate-800" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="bg-white border border-slate-200 rounded-xl px-4 py-3">
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className={`text-2xl font-semibold tabular-nums ${s.cls}`}>{s.value}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="bd-days" className="text-sm text-slate-500">Oldindan:</label>
        <select id="bd-days" value={days} onChange={(e) => setDays(Number(e.target.value))}
          className="border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white">
          {[7, 30, 60, 90].map((n) => <option key={n} value={n}>{n} kun</option>)}
        </select>
        <label htmlFor="bd-who" className="text-sm text-slate-500 ml-2">Kimlar:</label>
        <select id="bd-who" value={who} onChange={(e) => setWho(e.target.value as "" | "student" | "staff")}
          className="border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white">
          <option value="">Hammasi</option>
          <option value="student">O'quvchilar</option>
          <option value="staff">Xodimlar</option>
        </select>
        {/* SANASI KIRITILMAGANLAR (2026-10-06, Jahongir: "bitta click bilan
            tug'ilgan kuni yoki ishga kirgan sanasi kiritilmaganlar") */}
        <button type="button" onClick={() => setMissing(true)}
          className="ml-auto inline-flex items-center gap-1.5 text-sm font-medium border border-amber-300 bg-amber-50 text-amber-800 rounded-lg px-3 py-1.5 hover:bg-amber-100">
          Sanasi kiritilmaganlar
          {(d.missing_students + d.missing_staff) > 0 && (
            <span className="rounded-full bg-amber-600 text-white text-[11px] px-1.5">{d.missing_students + d.missing_staff}</span>
          )}
        </button>
      </div>

      {(d.missing_students > 0 || d.missing_staff > 0) && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
          Tug'ilgan sanasi kiritilmagan: {d.missing_students} ta o'quvchi, {d.missing_staff} ta xodim.
          Ularning tug'ilgan kuni bu ro'yxatda chiqmaydi —{" "}
          <button type="button" onClick={() => setMissing(true)} className="underline font-medium">
            shu yerdan kiriting
          </button>.
        </p>
      )}

      {missing && (
        <MissingDatesDialog onClose={() => setMissing(false)} onChanged={() => setRev((x) => x + 1)} />
      )}

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 bg-white border border-slate-200 rounded-xl px-4 py-8 text-center">
          {days} kun ichida tug'ilgan kun yo'q.
        </p>
      ) : (
        <ul className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100">
          {rows.map((r) => {
            const key = `${r.who}-${r.id}`;
            return (
              <li key={key} className={`flex flex-wrap items-center gap-3 px-4 py-3 ${r.today ? "bg-rose-50" : ""}`}>
                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
                  r.today ? "bg-rose-100 text-rose-600" : "bg-violet-50 text-violet-600"}`}>
                  <Cake size={16} />
                </div>
                {/* Ism, lavozim/guruh, filial — telefonda ham to'liq
                    (2026-10-03, Jahongir: "faqat kun ko'rinyabdi"). Avval
                    ustun flex-1 + truncate bilan 0 kenglikka siqilardi. */}
                <div className="min-w-[200px] flex-1">
                  <p className="font-medium text-slate-800">
                    {r.full_name}{" "}
                    <span className={`ml-1 align-middle text-[10px] font-medium rounded px-1.5 py-0.5 ${
                      r.who === "staff" ? "bg-sky-50 text-sky-700" : "bg-violet-50 text-violet-700"}`}>
                      {r.who_label}
                    </span>
                  </p>
                  <p className="text-xs text-slate-600">
                    <span className="text-slate-400">{r.who === "staff" ? "Lavozimi:" : "Guruhi:"}</span>{" "}
                    {r.sub || "—"}
                  </p>
                  <p className="text-xs text-slate-600">
                    <span className="text-slate-400">{r.who === "staff" ? "Filiallari:" : "Filiali:"}</span>{" "}
                    {r.branch || "—"}
                    {r.phone ? <span className="text-slate-400"> · {formatPhone(r.phone)}</span> : null}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-semibold ${r.today ? "text-rose-600" : "text-slate-700"}`}>{whenText(r.days_left)}</p>
                  <p className="text-xs text-slate-500">{r.date_label} · {r.age} yoshga to'ladi</p>
                </div>
                <button type="button" onClick={() => copy(r)}
                  className="inline-flex items-center gap-1.5 text-xs font-medium border border-slate-200 rounded-lg px-2.5 py-1.5 hover:border-brand-400"
                  aria-label={`${r.full_name} uchun tabrik matnini nusxalash`}>
                  {copied === key ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                  {copied === key ? "Nusxalandi" : "Tabrik matni"}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function EventsTab() {
  const [d, setD] = useState<EventList | null>(null);
  const [staff, setStaff] = useState<StaffOption[]>([]);
  const [form, setForm] = useState<typeof empty | null>(null);
  const [editId, setEditId] = useState<number | null>(null);
  const [showPast, setShowPast] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = () => api.get<EventList>("/events", true).then(setD).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (d?.can_manage) api.get<StaffOption[]>("/events/staff-options").then(setStaff).catch(() => setStaff([]));
  }, [d?.can_manage]);

  if (!d) return err ? <p className="text-sm text-red-600">{err}</p> : <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const rows = d.rows.filter((r) => (showPast ? r.days_left < 0 : r.days_left >= 0));
  const statusTone = (k: string) => TONE[d.statuses.find((s) => s.key === k)?.tone || "slate"];

  const openNew = () => { setEditId(null); setForm({ ...empty }); setErr(null); };
  const openEdit = (r: EventRow) => {
    setEditId(r.id);
    setErr(null);
    setForm({
      title: r.title, kind: r.kind, event_date: r.event_date, start_time: r.start_time || "",
      place: r.place || "", audience: r.audience || "", budget: r.budget == null ? "" : String(r.budget),
      status: r.status, responsible_id: r.responsible_id ? String(r.responsible_id) : "", note: r.note || "",
    });
  };

  const save = async () => {
    if (!form) return;
    setSaving(true);
    setErr(null);
    try {
      const body = { ...form, responsible_id: form.responsible_id ? Number(form.responsible_id) : null };
      if (editId) await api.put(`/events/${editId}`, body);
      else await api.post("/events", body);
      setForm(null);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Saqlab bo'lmadi");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (r: EventRow) => {
    if (!window.confirm(`"${r.title}" tadbirini o'chirasizmi?`)) return;
    try {
      await api.delete(`/events/${r.id}`);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "O'chirib bo'lmadi");
    }
  };

  const set = (k: keyof typeof empty) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => (f ? { ...f, [k]: e.target.value } : f));
  const field = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1">
          <button type="button" id="ev-upcoming" onClick={() => setShowPast(false)}
            className={`px-3 py-1 text-sm rounded-md ${!showPast ? "bg-slate-100 font-medium text-slate-800" : "text-slate-500"}`}>Kelayotgan</button>
          <button type="button" id="ev-past" onClick={() => setShowPast(true)}
            className={`px-3 py-1 text-sm rounded-md ${showPast ? "bg-slate-100 font-medium text-slate-800" : "text-slate-500"}`}>O'tgan</button>
        </div>
        <div className="flex-1" />
        {d.can_manage && (
          <button type="button" id="ev-new" onClick={openNew}
            className="inline-flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-lg px-3 py-2">
            <Plus size={16} /> Yangi tadbir
          </button>
        )}
      </div>

      {err && !form && <p className="text-sm text-red-600">{err}</p>}

      {form && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-800">{editId ? "Tadbirni tahrirlash" : "Yangi tadbir"}</h2>
            <button type="button" onClick={() => setForm(null)} aria-label="Yopish" className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="sm:col-span-2 text-sm text-slate-600">Nomi
              <input id="ev-title" className={field} value={form.title} onChange={set("title")} placeholder="Masalan: Mustaqillik kuni bayrami" />
            </label>
            <label className="text-sm text-slate-600">Turi
              <select id="ev-kind" className={field} value={form.kind} onChange={set("kind")}>
                {d.kinds.map((k) => <option key={k.key} value={k.key}>{k.label}</option>)}
              </select>
            </label>
            <label className="text-sm text-slate-600">Holati
              <select id="ev-status" className={field} value={form.status} onChange={set("status")}>
                {d.statuses.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </label>
            <label className="text-sm text-slate-600">Sana
              <input id="ev-date" type="date" className={field} value={form.event_date} onChange={set("event_date")} />
            </label>
            <label className="text-sm text-slate-600">Boshlanish vaqti
              <input id="ev-time" type="time" className={field} value={form.start_time} onChange={set("start_time")} />
            </label>
            <label className="text-sm text-slate-600">Joyi
              <input id="ev-place" className={field} value={form.place} onChange={set("place")} placeholder="Masalan: Markaz filiali, 3-qavat zal" />
            </label>
            <label className="text-sm text-slate-600">Kimlar uchun
              <input id="ev-audience" className={field} value={form.audience} onChange={set("audience")} placeholder="Masalan: Step 1–2 o'quvchilari va ota-onalar" />
            </label>
            <label className="text-sm text-slate-600">Byudjet (so'm)
              <input id="ev-budget" type="number" min="0" className={field} value={form.budget} onChange={set("budget")} />
            </label>
            <label className="text-sm text-slate-600">Mas'ul xodim
              <select id="ev-resp" className={field} value={form.responsible_id} onChange={set("responsible_id")}>
                <option value="">— tanlanmagan —</option>
                {staff.map((s) => <option key={s.id} value={s.id}>{s.full_name} ({s.role_label})</option>)}
              </select>
            </label>
            <label className="sm:col-span-2 text-sm text-slate-600">Izoh / reja
              <textarea id="ev-note" rows={3} className={field} value={form.note} onChange={set("note")} placeholder="Dastur, kerakli narsalar, kimga nima topshirilgan" />
            </label>
          </div>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setForm(null)} className="text-sm px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Bekor qilish</button>
            <button type="button" id="ev-save" onClick={save} disabled={saving}
              className="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium disabled:opacity-60">
              {saving ? "Saqlanmoqda..." : "Saqlash"}
            </button>
          </div>
        </div>
      )}

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 bg-white border border-slate-200 rounded-xl px-4 py-8 text-center">
          {showPast ? "O'tgan tadbirlar yo'q." : "Rejalashtirilgan tadbir yo'q."}
          {!showPast && d.can_manage ? " \"Yangi tadbir\" tugmasi bilan qo'shing." : ""}
        </p>
      ) : (
        <ul className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100">
          {rows.map((r) => (
            <li key={r.id} className="px-4 py-3 flex flex-wrap items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
                <CalendarDays size={16} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-800">{r.title}</p>
                <p className="text-xs text-slate-500">
                  {r.kind_label} · {r.date_label}{r.start_time ? `, ${r.start_time}` : ""}
                  {r.place ? ` · ${r.place}` : ""}{r.branch ? ` · ${r.branch}` : ""}
                </p>
                <p className="text-xs text-slate-500">
                  Mas'ul: {r.responsible || "—"} · Byudjet: {money(r.budget)}{r.audience ? ` · ${r.audience}` : ""}
                </p>
                {r.note && <p className="text-sm text-slate-600 mt-1 whitespace-pre-line">{r.note}</p>}
              </div>
              <div className="flex flex-col items-end gap-1.5">
                <span className={`text-xs font-medium rounded-full px-2 py-0.5 ${statusTone(r.status)}`}>{r.status_label}</span>
                <span className="text-xs text-slate-500">{whenText(r.days_left)}</span>
                {d.can_manage && (
                  <div className="flex gap-1">
                    <button type="button" onClick={() => openEdit(r)} aria-label={`${r.title} — tahrirlash`}
                      className="p-1.5 rounded-md text-slate-500 hover:bg-slate-100"><Pencil size={14} /></button>
                    <button type="button" onClick={() => remove(r)} aria-label={`${r.title} — o'chirish`}
                      className="p-1.5 rounded-md text-slate-500 hover:bg-rose-50 hover:text-rose-600"><Trash2 size={14} /></button>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
