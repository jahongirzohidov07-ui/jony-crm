import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { appHref } from "./appNav";
import { Gem } from "./Gem";

type NotifItem = { icon: string; text: string; link?: string; tone: string };
const TONE_GEM: Record<string, string> = { red: "warn", amber: "bell", sky: "chat", emerald: "check" };

/** BILDIRISHNOMALAR — paneldagi qo'ng'iroqcha bilan bir xil manba (/my/alerts). */
export default function AppAlerts() {
  const [d, setD] = useState<{ items: NotifItem[]; count: number } | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<{ items: NotifItem[]; count: number }>("/my/alerts")
      .then((x) => {
        setD(x);
        try { localStorage.setItem("jonyos_alerts_seen", JSON.stringify(x.items.map((i) => i.text))); } catch { /* */ }
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Olinmadi"));
  }, []);
  return (
    <div className="jos-page">
      <div className="jos-sect" style={{ marginTop: 6 }}>
        <b style={{ fontSize: 20, fontFamily: "Unbounded, Manrope, sans-serif" }}>Bildirishnomalar</b>
      </div>
      {err && <div className="jos-note bad">{err}</div>}
      {!d && !err && [0, 1].map((i) => <div key={i} className="jos-skel" style={{ marginTop: 10 }} />)}
      {d && d.items.length === 0 && <div className="jos-empty">Yangi xabar yo'q</div>}
      {d && d.items.length > 0 && (
        <div className="jos-list">
          {d.items.map((it, i) => {
            const body = (
              <>
                <Gem name={TONE_GEM[it.tone] || "bell"} size={38} />
                <div className="m"><b style={{ whiteSpace: "normal" }}>{it.text}</b></div>
              </>
            );
            return it.link
              ? <Link key={i} to={appHref(it.link)} className="jos-it">{body}</Link>
              : <div key={i} className="jos-it">{body}</div>;
          })}
        </div>
      )}
    </div>
  );
}
