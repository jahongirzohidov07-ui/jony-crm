import { useEffect, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { useAuth } from "../lib/AuthContext";
import {
  EXAM_VIEW, EXAM_ACCESS, EXAM_EDIT, EXAM_ORDER_ACCEPT, can,
} from "../lib/roles";
import { BranchPicker } from "../components/BranchPicker";
import { ExamBankTab } from "../components/ExamBank";
import { ExamOrderQueueTab } from "./MyExams";
import { ExamsTab, AnalysisTab } from "./Audit";

/**
 * IMTIHONLAR — alohida bo'lim (2026-09-26).
 *
 * Jahongir: "audit bolimidagi umumiy imthonlar exam bo'limi qilib bosh
 * sahifaga qosh". Ilgari imtihonga tegishli hamma narsa Audit ichida
 * turardi va topish qiyin edi; endi Audit faqat nazorat bo'limi
 * (o'zgarishlar tarixi, oyliklar, jarima, shikoyat), imtihon ishi esa
 * shu yerda:
 *
 *   Imtihonlar        — filial bo'yicha o'tkazilgan testlar
 *   Imtihon tahlili   — natijalar kesimi
 *   Buyurtmalar       — ustozlardan kelgan imtihon so'rovlari
 *   Test bazasi       — savollar banki (mock, unit, mid, end)
 */
type Tab = "exams" | "analysis" | "orders" | "bank";

export default function ExamsHub() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("exams");
  const [branchId, setBranchId] = useState<number | null>(null);

  const showExams = can(user?.role, EXAM_VIEW);
  const showOrders = can(user?.role, EXAM_ORDER_ACCEPT);
  const showBank = can(user?.role, EXAM_ACCESS) || can(user?.role, EXAM_EDIT);

  const tabs: { key: Tab; label: string; show: boolean }[] = [
    { key: "exams", label: "Imtihonlar", show: showExams },
    { key: "analysis", label: "Imtihon tahlili", show: showExams },
    { key: "orders", label: "Buyurtmalar", show: showOrders },
    { key: "bank", label: "Test bazasi", show: showBank },
  ];
  const visible = tabs.filter((t) => t.show);
  const firstKey = visible.length ? visible[0].key : null;
  const hasTab = visible.some((t) => t.key === tab);

  useEffect(() => {
    // Ko'rinmaydigan tab tanlangan bo'lsa — birinchisiga o'tadi
    if (firstKey && !hasTab) setTab(firstKey);
  }, [firstKey, hasTab]);

  if (!visible.length) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Bu bo'lim sizga ochiq emas.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <ClipboardCheck size={20} className="text-brand-600" />
        <h1 className="text-xl font-bold text-slate-900">Imtihonlar</h1>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        O'tkazilgan testlar, natijalar tahlili, ustozlardan kelgan
        buyurtmalar va savollar bazasi.
      </p>

      <div className="flex items-end gap-4 border-b border-slate-200 mb-4">
        <div className="flex gap-1 overflow-x-auto">
          {visible.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-3 py-2 text-sm whitespace-nowrap border-b-2 -mb-px transition ${
                tab === t.key
                  ? "border-brand-600 text-brand-700 font-medium"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        {(tab === "exams" || tab === "analysis") && (
          <BranchPicker value={branchId} onChange={setBranchId} className="pb-2" />
        )}
      </div>

      {tab === "exams" && <ExamsTab branchId={branchId} />}
      {tab === "analysis" && <AnalysisTab branchId={branchId} />}
      {tab === "orders" && <ExamOrderQueueTab />}
      {tab === "bank" && <ExamBankTab canEdit={can(user?.role, EXAM_EDIT)} />}
    </div>
  );
}
