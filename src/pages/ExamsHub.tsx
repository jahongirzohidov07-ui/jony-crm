import { useEffect, useState } from "react";
import { ClipboardCheck, Check, Hand } from "lucide-react";
import { api } from "../lib/api";
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
type Tab = "exams" | "analysis" | "orders" | "bank" | "mock";

/** Mock bazalari: qaysi imtihon, qaysi bo'lim, natija qanday chiqadi. */
type MockSection = {
  section: string;
  variants: string[];
  levels: string[];
  questions: number;
  questions_max: number;
  paper_max: number;
  auto: boolean;
  grading: string;
};
type MockBank = {
  bank: string;
  label: string;
  /** Mock EMAS — mashq to'plami (Challenge 25): band qo'yilmaydi. */
  practice: boolean;
  sections: MockSection[];
};

const SEC_LABEL: Record<string, string> = {
  listening: "Listening",
  reading: "Reading",
  writing: "Writing",
  speaking: "Speaking",
};

/**
 * MOCK TESTLAR (2026-09-27, Jahongir: "mock testlarni imtihon
 * bo'limiga o'tkazasan IELTS va CEFR nikini").
 *
 * Bu yerda har bazaning natijasi QANDAY chiqishi ochiq yozilgan —
 * qaysi bo'lim avtomat bandga o'giriladi, qaysinisini examiner
 * qo'lda qo'yadi va nima uchun. Kamchilik yashirin qolmasin.
 */
function MockTab() {
  const [rows, setRows] = useState<MockBank[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<MockBank[]>("/mock-banks")
      .then(setRows)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (err) return <p className="text-sm text-rose-600 py-6">{err}</p>;
  if (!rows) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;
  if (!rows.length) {
    return (
      <p className="text-sm text-slate-500 py-6">
        Mock shablonlari hali bazaga yozilmagan.
      </p>
    );
  }

  const mocks = rows.filter((b) => !b.practice);
  const practice = rows.filter((b) => b.practice);

  return (
    <div className="space-y-5">
      <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
        Mockni o'tkazish uchun: guruhni oching → <b>Imtihonlar</b> →
        "Yangi test" → turi <b>Mock test</b> → test qatoridan
        <b> online link</b> oching va shu yerdagi variantlardan birini
        tanlang. Listening bo'lsa skriptni examiner ovoz chiqarib o'qiydi.
      </p>

      {mocks.map((b) => (
        <div key={b.bank} className="border border-slate-200 rounded-xl bg-white overflow-hidden">
          <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
            <h2 className="font-semibold text-slate-800">{b.label}</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Bo'lim</th>
                <th className="text-right px-3 py-2 font-medium">Variant</th>
                <th className="text-right px-3 py-2 font-medium">Savol</th>
                <th className="text-left px-4 py-2 font-medium">Natija qanday chiqadi</th>
              </tr>
            </thead>
            <tbody>
              {b.sections.map((s) => (
                <tr key={s.section} className="border-t border-slate-100 align-top">
                  <td className="px-4 py-3 font-medium text-slate-800 whitespace-nowrap">
                    {SEC_LABEL[s.section] || s.section}
                  </td>
                  <td className="px-3 py-3 text-right text-slate-600">
                    {s.variants.length}
                    <span className="text-slate-400 text-xs ml-1">
                      ({s.variants[0]}–{s.variants[s.variants.length - 1]})
                    </span>
                  </td>
                  <td className="px-3 py-3 text-right text-slate-600 whitespace-nowrap">
                    {s.questions === 0
                      ? <span className="text-slate-400">qog'ozda</span>
                      : s.questions === s.questions_max
                        ? s.questions
                        : `${s.questions}–${s.questions_max}`}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium mr-2 ${
                        s.auto
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      {s.auto ? <Check size={11} /> : <Hand size={11} />}
                      {s.auto ? "avtomat" : "examiner qo'yadi"}
                    </span>
                    <span className="text-slate-600">{s.grading}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {/* MASHQ TO'PLAMLARI — mock emas (Jahongir: "challenge 25 nima
          qilyabdi bu mock emasku shunchaki mashq edi"). Ro'yxatdan
          olib tashlanmadi, chunki ustozlar uni test qilib beradi —
          lekin mock imtihon bilan bir qatorga qo'yilmaydi. */}
      {practice.length > 0 && (
        <div className="pt-1">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">
            Mashq to'plamlari — mock imtihon emas
          </p>
          {practice.map((b) => (
            <div key={b.bank} className="border border-slate-200 rounded-xl bg-slate-50/60 overflow-hidden">
              <div className="px-4 py-2.5 border-b border-slate-200">
                <h2 className="font-semibold text-slate-600">{b.label}</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  To'liq imtihon tuzilishi emas: faqat Reading savollari.
                  Band qo'yilmaydi, xom ball va javoblar varaqasi chiqadi.
                </p>
              </div>
              <table className="w-full text-sm">
                <tbody>
                  {b.sections.map((s) => (
                    <tr key={s.section} className="border-t border-slate-100 align-top">
                      <td className="px-4 py-2.5 font-medium text-slate-700 whitespace-nowrap">
                        {SEC_LABEL[s.section] || s.section}
                      </td>
                      <td className="px-3 py-2.5 text-right text-slate-600 whitespace-nowrap">
                        {s.variants.length} to'plam
                      </td>
                      <td className="px-3 py-2.5 text-right text-slate-600 whitespace-nowrap">
                        {s.questions === s.questions_max
                          ? `${s.questions} savol`
                          : `${s.questions}–${s.questions_max} savol`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

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
    { key: "mock", label: "Mock testlar", show: showExams },
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
      {tab === "mock" && <MockTab />}
      {tab === "bank" && <ExamBankTab canEdit={can(user?.role, EXAM_EDIT)} />}
    </div>
  );
}
