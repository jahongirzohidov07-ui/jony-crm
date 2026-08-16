import { useEffect, useState } from "react";
import { formatDate } from "../../lib/format";
import { Link } from "react-router-dom";
import { ArrowLeft, Bell, CircleDollarSign, GraduationCap, Gift } from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — BILDIRISHNOMALAR (2026-08-10).
 *
 * Jahongir: "o'ng burchakda qo'ng'iroqcha belgisida bildirishnomalar
 * kelib turadigan bo'lsin - to'lov vaqti yetgani, imtihon natijasi
 * chiqqani haqida."
 *
 * Sahifa ochilishi bilan oxirgi ko'rilgan vaqt saqlanadi - bosh
 * ekrandagi qizil nuqta shu bilan o'chadi.
 */
export default function StudentNotifications() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
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

  const items: Any[] = d?.items || [];

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/student"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Asosiy
          </Link>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <Bell size={20} />
            Bildirishnomalar
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-2 pb-8">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4 text-sm text-red-600">
            {err}
          </div>
        )}
        {d && items.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
            <Bell size={28} className="mx-auto text-slate-300 mb-2" />
            <p className="text-sm text-slate-500">
              Hozircha bildirishnoma yo'q
            </p>
          </div>
        )}
        {items.map((n: Any) => {
          const isNew = seenBefore && n.date && n.date > seenBefore;
          return (
            <div
              key={n.id}
              className={`bg-white rounded-xl shadow-sm border p-4 flex gap-3 ${
                isNew ? "border-brand-300" : "border-slate-200"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                  n.kind === "payment"
                    ? "bg-red-50 text-red-600"
                    : n.kind === "reward"
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-violet-50 text-violet-600"
                }`}
              >
                {n.kind === "payment" ? (
                  <CircleDollarSign size={19} />
                ) : n.kind === "reward" ? (
                  <Gift size={19} />
                ) : (
                  <GraduationCap size={19} />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-800">
                  {n.title}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{n.body}</p>
                {n.date && (
                  <p className="text-[11px] text-slate-400 mt-1">
                    {formatDate(n.date)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
