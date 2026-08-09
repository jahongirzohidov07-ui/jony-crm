import { useEffect, useState, type ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";
import { subscribeToasts, dismissToast, type ToastMsg } from "../lib/toast";

const STYLES: Record<
  ToastMsg["kind"],
  { box: string; icon: ReactNode }
> = {
  error: {
    box: "bg-red-50 border-red-200 text-red-800",
    icon: <AlertTriangle size={18} className="text-red-500 shrink-0" />,
  },
  success: {
    box: "bg-emerald-50 border-emerald-200 text-emerald-800",
    icon: <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />,
  },
  info: {
    box: "bg-slate-50 border-slate-200 text-slate-800",
    icon: <Info size={18} className="text-slate-500 shrink-0" />,
  },
};

/** Ilova ildizida BIR MARTA joylashtiriladi (App.tsx). Har qanday
 * joydan pushToast(...) chaqirilsa, shu yerda ko'rinadi. */
export function ToastHost() {
  const [items, setItems] = useState<ToastMsg[]>([]);

  useEffect(() => subscribeToasts(setItems), []);

  if (items.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 w-full max-w-sm px-4 sm:px-0">
      {items.map((t) => {
        const s = STYLES[t.kind];
        return (
          <div
            key={t.id}
            role="alert"
            className={`flex items-start gap-2 rounded-lg border shadow-lg px-4 py-3 text-sm ${s.box}`}
          >
            {s.icon}
            <p className="flex-1 leading-snug">{t.text}</p>
            <button
              onClick={() => dismissToast(t.id)}
              className="shrink-0 opacity-60 hover:opacity-100"
              aria-label="Yopish"
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
