import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../lib/AuthContext";
import { api, type DashboardStats, type MyDashboard } from "../../lib/api";
import { can, CASH_ACCESS, FINANCE_ACCESS, roleLabel } from "../../lib/roles";
import { formatSom } from "../../lib/format";
import { useApp } from "./AppLayout";
import { appHref, gemFor } from "./appNav";
import { Gem, Glyph } from "./Gem";

const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul",
  "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
const DAYS = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];

/** MyPanel bilan bir xil qoida: pul bo'lsa so'm, konversiya bo'lsa %. */
export function showValue(label: string, v: number | string): string {
  if (typeof v === "string") return v;
  if (/pul|tushum|chiqim|foyda|balans|topgan|olgan|qarz|xarajat|narxi/i.test(label)) return formatSom(v);
  if (label.toLowerCase().includes("konversiya")) return `${v}%`;
  return v.toLocaleString("en-US").replace(/,/g, " ");
}

export function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "J";
}

function greet(): string {
  const h = new Date().getHours();
  if (h < 5) return "Xayrli tun";
  if (h < 12) return "Xayrli tong";
  if (h < 18) return "Xayrli kun";
  return "Xayrli kech";
}

/**
 * BOSH SAHIFA — har xodim O'Z ishini ko'radi (2026-09-27).
 * Kartalar /me/dashboard dan keladi: server rolga qarab o'zi tanlaydi
 * (panelning "Mening ishim" bloki bilan bir xil manba). Butun markaz
 * raqamlari faqat server show_general deganda chiqadi.
 */
export default function AppHome() {
  const { user } = useAuth();
  const { nav, fab } = useApp();
  const [d, setD] = useState<MyDashboard | null>(null);
  const [gen, setGen] = useState<DashboardStats | null>(null);
  const [err, setErr] = useState("");
  const [alerts, setAlerts] = useState(0);

  useEffect(() => {
    let alive = true;
    api.get<MyDashboard>("/me/dashboard")
      .then((x) => {
        if (!alive) return;
        setD(x);
        if (x.show_general) {
          api.get<DashboardStats>("/dashboard").then((g) => alive && setGen(g)).catch(() => {});
        }
      })
      .catch((e) => alive && setErr(e instanceof Error ? e.message : "Ma'lumot olinmadi"));
    api.get<{ count: number }>("/my/alerts").then((a) => alive && setAlerts(a.count || 0)).catch(() => {});
    return () => { alive = false; };
  }, []);

  const now = new Date();
  const dateStr = `${DAYS[now.getDay()]}, ${now.getDate()}-${MONTHS[now.getMonth()]}`;
  const name = user?.full_name || "";
  const first = name.split(/\s+/)[0] || name;
  const quick = nav.filter((i) => i.to !== "/").slice(0, 7);
  const money = can(user?.role, FINANCE_ACCESS) || can(user?.role, CASH_ACCESS);

  return (
    <div className="jos-page">
      <div className="jos-hello">
        <Link to="/app/profile" className="jos-ava" aria-label="Profil">{initials(name)}</Link>
        <div className="who">
          <b>{greet()}, {first}!</b>
          <small>{d?.role_label || roleLabel(user?.role || "")}{d?.branch ? ` · ${d.branch}` : ""}</small>
        </div>
        <Link to="/app/alerts" className="jos-iconbtn" aria-label="Bildirishnomalar">
          <Glyph name="bell" size={21} />
          {alerts > 0 && <span className="dot" />}
        </Link>
      </div>

      <div className="jos-hero">
        <div className="k">{dateStr}</div>
        <div className="big">
          {d ? (d.tasks.open > 0 ? `${d.tasks.open} ta ochiq vazifa` : "Vazifalar bajarilgan") : "Bugungi ish"}
        </div>
        <div className="s">
          {d && d.tasks.overdue > 0
            ? `${d.tasks.overdue} tasining muddati o'tgan — avval shularni yoping.`
            : "Kuningiz barakali o'tsin. Hammasi shu yerda, bir bosishda."}
        </div>
        <div className="row">
          {fab && (
            <Link to={fab.to} className="jos-btn w"><Glyph name={fab.gem} size={16} />{fab.label}</Link>
          )}
          <Link to="/app/tasks" className="jos-btn g"><Glyph name="task" size={16} />Vazifalar</Link>
        </div>
      </div>

      {err && <div className="jos-note bad" style={{ marginTop: 12 }}>{err}</div>}
      {!d && !err && (
        <div className="jos-stats">{[0, 1, 2, 3].map((i) => <div key={i} className="jos-skel" />)}</div>
      )}

      {d && d.cards.length > 0 && (
        <>
          <div className="jos-sect"><b>Mening ishim</b></div>
          <div className="jos-stats">
            {d.cards.map((c, i) => {
              const body = (
                <>
                  <div className="l">{c.label}</div>
                  <div className="v">{showValue(c.label, c.value)}</div>
                  {c.hint && <div className="d">{c.hint}</div>}
                </>
              );
              return c.link ? (
                <Link key={c.label} to={appHref(c.link)} className="jos-st" style={{ animationDelay: `${i * 50}ms` }}>{body}</Link>
              ) : (
                <div key={c.label} className="jos-st" style={{ animationDelay: `${i * 50}ms` }}>{body}</div>
              );
            })}
          </div>
        </>
      )}

      {d?.teacher && d.teacher.alerts.length > 0 && (
        <>
          <div className="jos-sect"><b>Diqqat talab qiladi</b><Link to="/teacher">Yo'qlama →</Link></div>
          <div className="jos-list">
            {d.teacher.alerts.slice(0, 5).map((a, i) => (
              <Link key={i} to={a.student_id ? appHref(`/students/${a.student_id}`) : "/teacher"} className="jos-it">
                <Gem name={a.tone === "red" ? "warn" : "bell"} size={38} />
                <div className="m">
                  <b>{a.student || a.group || a.label}</b>
                  <small>{a.label}{a.detail ? ` — ${a.detail}` : ""}</small>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}

      {gen && (
        <>
          <div className="jos-sect"><b>Markaz holati</b></div>
          <div className="jos-stats">
            <Link to={appHref("/students?status=active")} className="jos-st">
              <div className="l">Faol o'quvchilar</div><div className="v">{gen.active_students}</div>
              <div className="d">sinovda {gen.trial_students} · muzlatilgan {gen.frozen_students}</div>
            </Link>
            <div className="jos-st">
              <div className="l">Shu oy yangi to'lovlar</div><div className="v">{gen.month_new_payment_count}</div>
              <div className="d">jami {gen.month_payment_count} ta to'lov</div>
            </div>
            {money && (
              <div className="jos-st">
                <div className="l">Shu oy tushum</div><div className="v">{formatSom(gen.month_income)}</div>
              </div>
            )}
            <div className="jos-st">
              <div className="l">Qarzdorlar</div><div className="v">{gen.debtor_count}</div>
              {money && <div className="d">{formatSom(gen.total_debt)}</div>}
            </div>
          </div>
        </>
      )}

      {d && d.tasks.rows.length > 0 && (
        <>
          <div className="jos-sect"><b>Vazifalarim</b><Link to="/app/tasks">Hammasi ({d.tasks.open})</Link></div>
          <div className="jos-list">
            {d.tasks.rows.slice(0, 4).map((t) => (
              <Link key={t.id} to="/app/tasks" className="jos-it">
                <Gem name={t.overdue ? "fire" : "task"} size={38} />
                <div className="m">
                  <b>{t.title}</b>
                  <small>{t.deadline ? (t.overdue ? `${Math.abs(t.days_left ?? 0)} kun kechikdi` : `${t.days_left} kun qoldi`) : "muddatsiz"}</small>
                </div>
                <span className={`jos-pill ${t.overdue ? "bad" : "acc"}`}>{t.status_label}</span>
              </Link>
            ))}
          </div>
        </>
      )}

      {quick.length > 0 && (
        <>
          <div className="jos-sect"><b>Tez kirish</b><Link to="/app/menu">Barchasi</Link></div>
          <div className="jos-grid">
            {quick.map((i, k) => (
              <Link key={i.to} to={appHref(i.to)} className="jos-cell" style={{ animationDelay: `${k * 40}ms` }}>
                <Gem name={gemFor(i.to)} size={52} />
                {i.label}
              </Link>
            ))}
            <Link to="/app/menu" className="jos-cell" style={{ animationDelay: `${quick.length * 40}ms` }}>
              <Gem name="grid" size={52} />Barchasi
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
