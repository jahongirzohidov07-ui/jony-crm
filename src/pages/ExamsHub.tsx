import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ClipboardCheck, Check, Hand, FlaskConical } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import {
  EXAM_VIEW, EXAM_ACCESS, EXAM_EDIT, EXAM_ORDER_ACCEPT, can,
  MOCK_PRACTICE, MOCK_ISSUE_VIEW, MOCK_ISSUE_TRIAGE,
} from "../lib/roles";
import { BranchPicker } from "../components/BranchPicker";
import { ExamBankTab, type BankFocus } from "../components/ExamBank";
import { MockIssues } from "../components/MockIssues";
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
type Tab = "exams" | "analysis" | "orders" | "bank" | "mock" | "issues";

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
function MockTab({ canTry }: { canTry: boolean }) {
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

      {/* O'ZIM SINAB KO'RAMAN (2026-09-27, Jahongir: "faqat guruhda
          emas, boshqalar ham o'zi kirib ishlaydigan bo'lsa yaxshi
          bo'lardi mock testni xodimlargayam koproq ustozlarga ular ham
          experience qilib xatolarni aytadida") */}
      {canTry && (
        <Link
          to="/mock-practice"
          className="flex items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 hover:bg-brand-100/60"
        >
          <FlaskConical size={18} className="text-brand-600 shrink-0" />
          <span className="flex-1 text-sm text-slate-700">
            <b>O'zim sinab ko'raman</b> — mockni o'quvchidek yechib ko'ring,
            savollardagi xatolarni examinerga ayting. Natija hech qayerga yozilmaydi.
          </span>
          <span className="text-sm font-medium text-brand-700">→</span>
        </Link>
      )}

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
  // ?tab=orders kabi havola to'g'ridan-to'g'ri kerakli bo'limni ochadi
  // (Jony Examiner ilovasidagi "Ko'rish" tugmasi, 2026-09-28).
  const [params] = useSearchParams();
  const TABS: Tab[] = ["exams", "analysis", "orders", "bank", "mock", "issues"];
  const want = params.get("tab") as Tab | null;
  // BUYURTMALAR BIRINCHI (2026-09-28, Jahongir: "buyurtmalarni birinchi
  // oringa qoy") — examinerning kuni kelgan so'rovlardan boshlanadi.
  // Buyurtma qabul qilmaydiganlar (filial/o'quv rahbari) Imtihonlardan.
  const [tab, setTab] = useState<Tab>(
    want && TABS.includes(want) ? want
      : can(user?.role, EXAM_ORDER_ACCEPT) ? "orders" : "exams");
  const [branchId, setBranchId] = useState<number | null>(null);

  const showExams = can(user?.role, EXAM_VIEW);
  const showOrders = can(user?.role, EXAM_ORDER_ACCEPT);
  const showBank = can(user?.role, EXAM_ACCESS) || can(user?.role, EXAM_EDIT);
  // SAVOL XATOLARI (2026-09-27): xodimlar mockni o'zi yechib yuborgan
  // "savolda xato bor" xabarlari. Soni tab yonida turadi.
  const showIssues = can(user?.role, MOCK_ISSUE_VIEW);
  const [issueCount, setIssueCount] = useState<number | null>(null);
  const [focus, setFocus] = useState<BankFocus | null>(null);
  function loadCount() {
    if (!showIssues) return;
    api
      .fresh<{ open: number }>("/mock-issues/count")
      .then((r) => setIssueCount(r?.open ?? 0))
      .catch(() => {});
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadCount, [showIssues]);

  const tabs: { key: Tab; label: string; show: boolean }[] = [
    { key: "orders", label: "Buyurtmalar", show: showOrders },
    { key: "exams", label: "Imtihonlar", show: showExams },
    { key: "analysis", label: "Imtihon tahlili", show: showExams },
    { key: "mock", label: "Mock testlar", show: showExams },
    { key: "bank", label: "Test bazasi", show: showBank },
    {
      key: "issues",
      label: issueCount != null ? `Savol xatolari (${issueCount})` : "Savol xatolari",
      show: showIssues,
    },
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
      {tab === "mock" && <MockTab canTry={can(user?.role, MOCK_PRACTICE)} />}
      {tab === "bank" && (
        <ExamBankTab
          canEdit={can(user?.role, EXAM_EDIT)}
          focus={focus}
          onFocusDone={(saved) => {
            setFocus(null);
            if (saved) loadCount();
            // Tuzatib bo'lgach navbatga qaytadi
            if (showIssues) setTab("issues");
          }}
        />
      )}
      {tab === "issues" && (
        <MockIssues
          canTriage={can(user?.role, MOCK_ISSUE_TRIAGE)}
          onChanged={loadCount}
          onFix={(f) => {
            setFocus(f);
            setTab("bank");
          }}
        />
      )}
    </div>
  );
}
