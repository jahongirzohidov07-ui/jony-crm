import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type TaskList, type TaskRow } from "../../lib/api";
import { formatDate } from "../../lib/format";

const ACTIONS = [
  { key: "in_progress", label: "Jarayonda" },
  { key: "review", label: "Tekshiruvga" },
  { key: "done", label: "Bajarildi" },
];

/**
 * VAZIFALAR — telefon uchun (2026-09-27). Faqat xodimning O'Z
 * vazifalari (serverda /tasks ning oddiy ro'yxati). Holat qoidalari
 * paneldagi bilan bir xil: muddati o'tganini yopishda kechikish
 * sababi majburiy. Tasdiqlash, yangi vazifa berish va boshqa
 * rahbar amallari — "To'liq ko'rinish" (panel sahifasi) orqali.
 */
export default function AppTasks() {
  const [data, setData] = useState<TaskList | null>(null);
  const [filter, setFilter] = useState("open");
  const [err, setErr] = useState("");

  function load() {
    api.get<TaskList>("/tasks?x=1")
      .then((d) => { setData(d); setErr(""); })
      .catch((e) => setErr(e instanceof Error ? e.message : "Vazifalar olinmadi"));
  }
  useEffect(load, []);

  const rows = (data?.rows || []).filter((r) =>
    filter === "open" ? !["done", "cancelled"].includes(r.status)
      : filter === "late" ? r.overdue && r.status !== "done"
        : r.status === filter);

  return (
    <div className="jos-page">
      <div className="jos-sect" style={{ marginTop: 6 }}>
        <b style={{ fontSize: 20, fontFamily: "Unbounded, Manrope, sans-serif" }}>Vazifalar</b>
        <Link to="/app/p/tasks">To'liq ko'rinish</Link>
      </div>
      <div className="jos-chips">
        <button className={`jos-chip ${filter === "open" ? "on" : ""}`} onClick={() => setFilter("open")}>
          Ochiq<i>{data?.open ?? ""}</i>
        </button>
        <button className={`jos-chip ${filter === "late" ? "on" : ""}`} onClick={() => setFilter("late")}>
          Kechikkan<i>{data?.overdue ?? ""}</i>
        </button>
        {(data?.statuses || []).map((s) => (
          <button key={s.key} className={`jos-chip ${filter === s.key ? "on" : ""}`} onClick={() => setFilter(s.key)}>
            {s.label}<i>{s.count}</i>
          </button>
        ))}
      </div>

      {err && <div className="jos-note bad" style={{ marginTop: 10 }}>{err}</div>}
      {!data && !err && [0, 1, 2].map((i) => <div key={i} className="jos-skel" style={{ marginTop: 10 }} />)}
      {data && rows.length === 0 && <div className="jos-empty">Bu yerda vazifa yo'q</div>}
      <div style={{ marginTop: 10 }}>
        {rows.map((t, i) => <TaskCard key={t.id} t={t} i={i} onDone={load} />)}
      </div>
    </div>
  );
}

function TaskCard({ t, i, onDone }: { t: TaskRow; i: number; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [result, setResult] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const finished = t.status === "done" || t.status === "cancelled";

  async function setStatus(status: string) {
    setErr("");
    const body: Record<string, unknown> = { status };
    if (status === "done") {
      if (t.overdue && !reason.trim() && !t.delay_reason) {
        setOpen(true);
        setErr("Muddat o'tgan — kechikish sababini yozing");
        return;
      }
      if (reason.trim()) body.delay_reason = reason.trim();
      if (result.trim()) body.result = result.trim();
    }
    setBusy(true);
    try {
      await api.put(`/tasks/${t.id}`, body);
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function toggleCheck(idx: number) {
    const list = t.checklist.map((c, k) => (k === idx ? { ...c, done: !c.done } : c));
    try {
      await api.put(`/tasks/${t.id}`, { checklist: list });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    }
  }

  return (
    <div className={`jos-task ${t.overdue && !finished ? "late" : ""} ${finished ? "done" : ""}`}
         style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}>
      <h4 onClick={() => setOpen(!open)}>{t.title}</h4>
      {t.description && (
        <p style={open ? undefined : { display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
          {t.description}
        </p>
      )}
      <div className="meta">
        <span className={`jos-pill ${finished ? "ok" : t.overdue ? "bad" : "acc"}`}>{t.status_label}</span>
        {t.deadline && (
          <span className={`jos-pill ${t.overdue && !finished ? "bad" : "mute"}`}>
            {formatDate(t.deadline)}
            {!finished && t.days_left != null && (t.overdue ? ` · ${Math.abs(t.days_left)} kun kechikdi` : ` · ${t.days_left} kun`)}
          </span>
        )}
        {t.priority_rank >= 3 && <span className="jos-pill warn">{t.priority_label}</span>}
        {t.checklist_total > 0 && <span className="jos-pill vio">{t.checklist_done}/{t.checklist_total}</span>}
      </div>
      {(t.created_by || t.watcher) && (
        <p style={{ fontSize: 11 }}>
          {t.created_by ? `Bergan: ${t.created_by}` : ""}{t.watcher ? ` · Nazoratchi: ${t.watcher}` : ""}
        </p>
      )}

      {open && t.checklist.length > 0 && (
        <div style={{ marginTop: 10 }}>
          {t.checklist.map((c, k) => (
            <label key={k} style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12.5, padding: "5px 0" }}>
              <input type="checkbox" checked={c.done} onChange={() => toggleCheck(k)} disabled={finished} />
              <span style={c.done ? { textDecoration: "line-through", opacity: .6 } : undefined}>{c.text}</span>
            </label>
          ))}
        </div>
      )}

      {!finished && open && (
        <>
          {t.overdue && !t.delay_reason && (
            <input className="jos-input" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Kechikish sababi" />
          )}
          <input className="jos-input" value={result} onChange={(e) => setResult(e.target.value)} placeholder="Natija (ixtiyoriy)" />
        </>
      )}
      {err && <div className="jos-note bad" style={{ marginTop: 8, padding: 10 }}>{err}</div>}

      {!finished && (
        <div className="acts">
          {ACTIONS.map((a) => (
            <button key={a.key} disabled={busy}
                    className={a.key === "done" ? "go" : t.stored_status === a.key ? "on" : ""}
                    onClick={() => (a.key === "done" && !open ? setOpen(true) : setStatus(a.key))}>
              {a.key === "done" && !open ? "Yakunlash…" : a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
