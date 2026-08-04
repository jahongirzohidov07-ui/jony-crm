import { useState } from "react";
import { Settings as SettingsIcon, Building2, ShieldCheck } from "lucide-react";
import Branches from "./Branches";
import Permissions from "./Permissions";

/**
 * SOZLAMALAR — asoschining boshqaruv burchagi.
 * Filiallar va Ruxsatlar endi alohida menyu bandlari emas, bitta
 * joyda turadi. Kelajakda boshqa sozlamalar ham shu yerga qo'shiladi
 * (Telegram, integratsiyalar va h.k. Ruxsatlar ichida turibdi).
 */
type Tab = "branches" | "permissions";

export default function Settings() {
  const [tab, setTab] = useState<Tab>("branches");

  const tabs: { key: Tab; label: string; icon: typeof Building2 }[] = [
    { key: "branches", label: "Filiallar", icon: Building2 },
    { key: "permissions", label: "Ruxsatlar", icon: ShieldCheck },
  ];

  return (
    <div className="p-8 pb-0">
      <div className="flex items-center gap-2 mb-1">
        <SettingsIcon size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Sozlamalar</h1>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Filiallar, rollar va tizim sozlamalari — bir joyda
      </p>
      <div className="flex items-center gap-1 border-b border-slate-200">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>
      {/* Ichki sahifalar o'z p-8 padding'i bilan keladi */}
      <div className="-mx-8">
        {tab === "branches" && <Branches />}
        {tab === "permissions" && <Permissions />}
      </div>
    </div>
  );
}
