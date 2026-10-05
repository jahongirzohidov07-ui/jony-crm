import { useState } from "react";
import { Cake, PartyPopper, Award, X, Copy, Check, Phone } from "lucide-react";

/**
 * BILDIRISHNOMA TAFSILOTI (2026-10-05, Jahongir: "event manager va boshqa
 * bayram bildirishnomalarida kimni tug'ilgan kuni yo yubileyi ekani
 * ko'rinmayabdi, ustiga bossa batafsil ma'lumot chiqaradigan qilib ber").
 *
 * /my/alerts dagi tug'ilgan kun, yubiley va tadbir qatorlarida "detail"
 * keladi — qo'ng'iroqcha ham, JonyOS ilovasi ham shu oynani ochadi.
 */
export type AlertDetailData = {
  type: "birthday" | "anniversary" | "event";
  title: string;
  full_name: string;
  who_label: string;
  fields: [string, string][];
  phone: string | null;
  greeting: string | null;
  link: string | null;
  link_label: string | null;
};

export type NotifItem = {
  icon: string;
  text: string;
  link?: string;
  tone: string;
  detail?: AlertDetailData;
};

const ICON = { birthday: Cake, anniversary: Award, event: PartyPopper };
const TONE = {
  birthday: "bg-rose-50 text-rose-600",
  anniversary: "bg-sky-50 text-sky-600",
  event: "bg-amber-50 text-amber-600",
};

export function AlertDetailModal({ d, onClose, onOpen }: {
  d: AlertDetailData;
  onClose: () => void;
  /** Havola bosilganda (panel — navigate, ilova — appHref) */
  onOpen: (link: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const Icon = ICON[d.type] || Cake;
  const tel = (d.phone || "").replace(/[^\d+]/g, "");

  async function copy() {
    if (!d.greeting) return;
    try {
      await navigator.clipboard.writeText(d.greeting);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 z-[60] flex items-start justify-center p-4 pt-16 overflow-y-auto"
         onClick={onClose}>
      <div className="bg-white rounded-xl w-full max-w-sm shadow-xl p-5"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start gap-3 mb-4">
          <div className={`w-11 h-11 rounded-full flex items-center justify-center shrink-0 ${TONE[d.type] || TONE.birthday}`}>
            <Icon size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-500">{d.title} · {d.who_label}</p>
            <p className="font-semibold text-slate-900 leading-snug">{d.full_name}</p>
          </div>
          <button onClick={onClose} className="text-slate-400" aria-label="Yopish">
            <X size={18} />
          </button>
        </div>

        <dl className="text-sm divide-y divide-slate-100 border border-slate-100 rounded-lg">
          {d.fields.map(([k, v]) => (
            <div key={k} className="flex gap-3 px-3 py-2">
              <dt className="w-32 shrink-0 text-slate-500">{k}</dt>
              <dd className="text-slate-800 break-words min-w-0">{v}</dd>
            </div>
          ))}
        </dl>

        {d.greeting && (
          <div className="mt-4">
            <p className="text-xs text-slate-500 mb-1">Tayyor tabrik</p>
            <p className="text-sm text-slate-700 bg-slate-50 border border-slate-100 rounded-lg p-3">
              {d.greeting}
            </p>
          </div>
        )}

        <div className="flex flex-wrap gap-2 mt-4">
          {d.greeting && (
            <button onClick={copy}
                    className="inline-flex items-center gap-1.5 text-sm border border-slate-200 rounded-lg px-3 py-2 hover:bg-slate-50">
              {copied ? <Check size={15} className="text-emerald-600" /> : <Copy size={15} />}
              {copied ? "Nusxalandi" : "Tabrikni nusxalash"}
            </button>
          )}
          {tel && (
            <a href={`tel:${tel}`}
               className="inline-flex items-center gap-1.5 text-sm border border-slate-200 rounded-lg px-3 py-2 hover:bg-slate-50">
              <Phone size={15} /> Qo'ng'iroq
            </a>
          )}
          {d.link && (
            <button onClick={() => onOpen(d.link!)}
                    className="ml-auto inline-flex items-center text-sm bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-2 font-medium">
              {d.link_label || "Ochish"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
