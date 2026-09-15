import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { formatDate } from "../../lib/format";
import { Link } from "react-router-dom";
import { ArrowLeft, Bell, ChevronRight } from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — BILDIRISHNOMALAR.
 *
 * 2026-08-21: "bildirishnomalar.png" dizayni bo'yicha to'q temada
 * qayta terildi. Mantiq o'zgarmadi: /student/notifications, oxirgi
 * ko'rilgan vaqt localStorage'da.
 */
export default function StudentNotifications() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [filt, setFilt] = useState<"all" | "new" | "reward">("all");
  const seenBefore = localStorage.getItem("jonyos_notif_seen") || "";

  useEffect(() => {
    api
      .get<Any>("/student/notifications")
      .then((r) => {
        setD(r);
        if (r.latest) localStorage.setItem("jonyos_notif_seen", r.latest);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const items: Any[] = (d?.items || []).filter((n: Any) => {
    if (filt === "new") return seenBefore && n.date && n.date > seenBefore;
    if (filt === "reward") return n.kind === "reward";
    return true;
  });

  const today = new Date().toISOString().slice(0, 10);
  const card = { background: "#0c2258", borderColor: "#35538c" };
  const ICON: Record<string, string> = {
    payment: "/jsicons/profile-payment.png",
    reward: "/jsicons/game-reward.png",
    exam: "/jsicons/learn-exam.png",
  };

  const groups: [string, Any[]][] = [];
  for (const n of items) {
    const day = (n.date || "").slice(0, 10);
    const label = day === today ? "Bugun"
      : day && new Date(new Date(today).getTime() - 86400000)
          .toISOString().slice(0, 10) === day ? "Kecha"
      : day ? formatDate(day) : "Oldinroq";
    const g = groups.find((x) => x[0] === label);
    if (g) g[1].push(n); else groups.push([label, [n]]);
  }

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5">
        <Link to="/student"
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}>
          <ArrowLeft size={18} />
        </Link>
        <span className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
              style={card}>
          <Bell size={18} />
        </span>
        <h1 className="text-[26px] font-extrabold text-white flex-1">
          Bildirishnomalar
        </h1>
      </div>

      <div className="flex gap-2 mt-4">
        {([["all", "Barchasi"], ["new", "O'qilmagan"],
           ["reward", "Mukofotlar"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setFilt(k)}
            className={`px-4 py-2.5 rounded-full text-sm font-bold transition ${
              filt === k ? "bg-brand-600 text-white" : "text-slate-300 border"}`}
            style={filt === k ? undefined : card}>
            {l}
          </button>
        ))}
      </div>

      {err && <p className="text-sm text-red-400 mt-4">{err}</p>}

      {d && items.length === 0 && (
        <div className="rounded-2xl border p-8 text-center mt-4" style={card}>
          <Bell size={28} className="mx-auto text-slate-500 mb-2" />
          <p className="text-sm text-slate-400">Hozircha bildirishnoma yo'q</p>
        </div>
      )}

      {groups.map(([label, rows]) => (
        <div key={label}>
          <p className="text-[17px] font-extrabold text-white mt-5 mb-2">
            {label}
          </p>
          <div className="space-y-2.5">
            {rows.map((n: Any) => {
              const isNew = seenBefore && n.date && n.date > seenBefore;
              return (
                <div key={n.id}
                  className="rounded-2xl border p-3.5 flex items-center gap-3"
                  style={card}>
                  <StudentImage src={ICON[n.kind] || "/jsicons/profile-notifications.png"}
                       alt="" className="w-12 h-12 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-[15px] font-bold text-white flex items-center gap-2">
                      {isNew && (
                        <span className="w-2 h-2 rounded-full bg-brand-400 shrink-0" />
                      )}
                      <span className="truncate">{n.title}</span>
                    </p>
                    <p className="text-[13px] text-slate-400 mt-0.5 line-clamp-2">
                      {n.body}
                    </p>
                  </div>
                  {n.date && (
                    <span className="text-[12px] text-slate-500 shrink-0">
                      {(n.date || "").slice(11, 16) || formatDate(n.date)}
                    </span>
                  )}
                  <ChevronRight size={16} className="text-slate-500 shrink-0" />
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
