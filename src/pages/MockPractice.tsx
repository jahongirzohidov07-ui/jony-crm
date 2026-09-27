import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FlaskConical, Lock, Play, X, Flag as FlagIcon } from "lucide-react";
import { api } from "../lib/api";
import { pushToast } from "../lib/toast";
import { useAuth } from "../lib/AuthContext";
import { MOCK_LIMITED, MOCK_PRACTICE, can } from "../lib/roles";
import { IssueStatusBadge, issueKindLabel } from "../components/MockIssueDialog";
import {
  ExtensionProbe, ExtensionWarning, MobileBlock, StrictRules, exitFs,
  requestFs, useForeignNodes, useNoTranslate, useStrictEnv,
} from "../components/StrictExam";

/**
 * MOCK SINAB KO'RISH — xodimlar uchun (2026-09-27).
 *
 * Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib ishlaydigan
 * bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq ustozlarga
 * ular ham experience qilib xatolarni aytadida".
 *
 * Ustoz, support, examiner va rahbariyat o'quvchi yechadigan mocklarni
 * o'zi yechib ko'radi va savollardagi xatolarni examinerga aytadi.
 * Natija guruh jadvaliga, coin/XP ga TUSHMAYDI — faqat o'ziga ko'rinadi.
 * Ustozlarda har variant 30 kunda bir marta (kalitlar tarqalmasin).
 */

type Last = { score?: number; max?: number; band?: number | null; at?: string | null } | null;
type Item = {
  content_key: string;
  title?: string;
  variant?: string | null;
  skill?: string | null;
  bank?: string;
  section?: string;
  q_count?: number;
  duration?: number | null;
  has_script?: boolean;
  my_last?: Last;
  my_open?: number | null;
  locked_until?: string | null;
  open_issues?: number;
};
type Section = { section: string; items: Item[] };
type Bank = { bank: string; label: string; practice: boolean; sections: Section[] };

type Attempt = {
  id: number;
  content_key?: string;
  title?: string | null;
  skill?: string | null;
  variant?: string | null;
  status: string;
  score?: number | null;
  max?: number | null;
  max_score?: number | null;
  band?: number | null;
  cefr?: string | { level?: string } | null;
  /** /mock-practice/mine CEFR darajasini shu nomda beradi */
  cefr_level?: string | null;
  started_at?: string | null;
  created_at?: string | null;
  submitted_at?: string | null;
  issues?: { open?: number; fixed?: number; rejected?: number; duplicate?: number } | null;
};
type MyIssueRow = {
  id: number;
  content_key?: string | null;
  skill?: string | null;
  variant?: string | null;
  q_n?: number | null;
  part_title?: string | null;
  kind: string;
  comment?: string | null;
  suggested?: string | null;
  status: string;
  resolution_note?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at?: string | null;
};

const BANK_LABELS: Record<string, string> = {
  ielts: "IELTS Academic",
  cefr: "CEFR Multilevel",
  challenge25: "Reading Challenge (25 kun)",
};
const PRACTICE_BANKS = new Set(["challenge25"]);
const SEC_LABEL: Record<string, string> = {
  listening: "Listening",
  reading: "Reading",
  writing: "Writing",
  speaking: "Speaking",
};
const SEC_ORDER = ["listening", "reading", "writing", "speaking"];

function day(iso?: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("uz-UZ", {
    day: "2-digit", month: "2-digit", year: "numeric",
  });
}

function splitSkill(skill?: string | null): [string, string] {
  const s = String(skill || "");
  const i = s.indexOf("_");
  if (i < 0) return ["ielts", s || "?"];
  return [s.slice(0, i), s.slice(i + 1)];
}

/** Katalog shaklini bir xil ko'rinishga keltiradi. Server
 *  bank -> bo'lim -> variant qilib beradi; bo'lim ichida ro'yxat
 *  "items" yoki "variants" nomida kelishi, yoki butun katalog tekis
 *  ro'yxat bo'lishi mumkin — hammasi shu yerda bir xil qilinadi. */
function normalize(raw: unknown): Bank[] {
  const r = raw as Record<string, unknown> | unknown[] | null;
  const arr: Record<string, unknown>[] = Array.isArray(r)
    ? (r as Record<string, unknown>[])
    : ((r?.banks || r?.items || []) as Record<string, unknown>[]);
  let banks: Bank[];
  if (arr.length && !Array.isArray(arr[0].sections)) {
    // Tekis ro'yxat — o'zimiz guruhlaymiz
    const m = new Map<string, Map<string, Item[]>>();
    for (const it of arr as unknown as Item[]) {
      const [b0, s0] = splitSkill(it.skill);
      const b = it.bank || b0;
      const s = it.section || s0;
      if (!m.has(b)) m.set(b, new Map());
      const sm = m.get(b)!;
      if (!sm.has(s)) sm.set(s, []);
      sm.get(s)!.push(it);
    }
    banks = [...m.entries()].map(([bank, sm]) => ({
      bank,
      label: BANK_LABELS[bank] || bank,
      practice: PRACTICE_BANKS.has(bank),
      sections: [...sm.entries()].map(([section, items]) => ({ section, items })),
    }));
  } else {
    banks = arr.map((b) => ({
      bank: String(b.bank || ""),
      label: String(b.label || BANK_LABELS[String(b.bank)] || b.bank || ""),
      practice: b.practice != null ? !!b.practice : PRACTICE_BANKS.has(String(b.bank)),
      sections: ((b.sections || []) as Record<string, unknown>[]).map((s) => ({
        section: String(s.section || ""),
        items: ((s.items || s.variants || []) as Item[]),
      })),
    }));
  }
  for (const b of banks) {
    b.sections.sort((a, c) => {
      const x = SEC_ORDER.indexOf(a.section), y = SEC_ORDER.indexOf(c.section);
      return (x < 0 ? 9 : x) - (y < 0 ? 9 : y) || a.section.localeCompare(c.section);
    });
    for (const s of b.sections)
      s.items.sort((a, c) =>
        String(a.variant || "").localeCompare(String(c.variant || "")) ||
        a.content_key.localeCompare(c.content_key));
  }
  return banks;
}

function cefrLevel(c: Attempt["cefr"]): string | null {
  if (!c) return null;
  if (typeof c === "object") return c.level || null;
  try {
    const o = JSON.parse(c);
    return o?.level || null;
  } catch {
    return null;
  }
}

function resultText(a: { score?: number | null; max?: number | null; band?: number | null; cefr?: Attempt["cefr"] }) {
  if (a.band != null) return `Band ${a.band} · ${a.score ?? 0}/${a.max ?? 0}`;
  const lv = cefrLevel(a.cefr);
  if (lv) return `${lv} (taxminiy) · ${a.score ?? 0}/${a.max ?? 0}`;
  if (!a.max) return "tekshirilmaydi";
  return `${a.score ?? 0}/${a.max}`;
}

export default function MockPractice() {
  const { user } = useAuth();
  const nav = useNavigate();
  const limited = can(user?.role, MOCK_LIMITED);
  const [banks, setBanks] = useState<Bank[] | null>(null);
  const [mine, setMine] = useState<Attempt[]>([]);
  const [issues, setIssues] = useState<MyIssueRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [pick, setPick] = useState<Item | null>(null);
  const [timed, setTimed] = useState(true);
  const [busy, setBusy] = useState(false);
  // MOCK — QAT'IY TARTIB (2026-09-27): telefonda boshlanmaydi, kengaytma
  // yoqilgan bo'lsa boshlanmaydi, "Boshlash" to'liq ekranga o'tkazadi
  const env = useStrictEnv();
  const mobile = env.blocked;
  const checking = !!pick && !mobile;
  const ext = useForeignNodes(checking);
  // Tarjima sahifa OCHILISHI BILAN o'chadi, faqat oyna ochilganda emas:
  // Chrome "doim tarjima qil" bilan ro'yxatni oldinroq tarjima qilib
  // qo'ysa, boshlash hech qachon ruxsat etilmasdi (2026-09-27 ko'rigi)
  useNoTranslate(true);

  useEffect(() => {
    if (!can(user?.role, MOCK_PRACTICE)) return;
    api
      .fresh<unknown>("/mock-practice/catalog")
      .then((r) => setBanks(normalize(r)))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
    api.fresh<Attempt[]>("/mock-practice/mine").then((r) => setMine(r || [])).catch(() => {});
    api.fresh<MyIssueRow[]>("/mock-issues/mine").then((r) => setIssues(r || [])).catch(() => {});
  }, [user?.role]);

  const open = useMemo(() => {
    const a = mine.find((m) => m.status === "in_progress");
    if (a) return { id: a.id, title: a.title || a.content_key || "" };
    for (const b of banks || [])
      for (const s of b.sections)
        for (const it of s.items)
          if (it.my_open) return { id: it.my_open, title: it.title || it.content_key };
    return null;
  }, [mine, banks]);

  async function start() {
    if (!pick || mobile || env.recheck()) return;
    if (ext.rescan().length || ext.seen.length) return;
    // To'liq ekran — shu bosishda, await'dan oldin (brauzer faqat
    // bosishga ruxsat beradi); ruxsat bo'lmasa test baribir boshlanadi
    requestFs();
    setBusy(true);
    try {
      const r = await api.post<{ id: number; resumed?: boolean; content_key?: string }>(
        "/mock-practice",
        { content_key: pick.content_key, timed: pick.duration ? timed : false },
      );
      // Bir vaqtda bitta urinish: boshqa test yechilayotgan bo'lsa server
      // o'shani qaytaradi — xodim nega boshqa testga tushganini bilsin.
      if (r.resumed && r.content_key && r.content_key !== pick.content_key)
        pushToast(`Avval tugallanmagan testni yakunlang: ${r.content_key}`, "info");
      nav(`/mock-practice/${r.id}`);
    } catch {
      /* xato matni toast bilan chiqadi (masalan 30 kunlik cheklov) */
      exitFs();
    } finally {
      setBusy(false);
    }
  }

  function choose(it: Item) {
    if (it.my_open) {
      // Davom etayotgan urinish — to'liq ekranda davom etadi
      if (!mobile) requestFs();
      nav(`/mock-practice/${it.my_open}`);
      return;
    }
    setTimed(true);
    setPick(it);
  }

  if (!can(user?.role, MOCK_PRACTICE))
    return <p className="text-sm text-slate-500 py-10 text-center">Bu bo'lim sizga ochiq emas.</p>;

  const nowMs = Date.now();
  const mocks = (banks || []).filter((b) => !b.practice);
  const practice = (banks || []).filter((b) => b.practice);

  const chip = (it: Item) => {
    const locked = !!it.locked_until && Date.parse(it.locked_until) > nowMs;
    const tip = [
      it.title || it.content_key,
      it.q_count ? `${it.q_count} savol` : "",
      it.my_last ? `Siz yechgansiz · ${day(it.my_last.at)} · ${resultText(it.my_last)}` : "",
      locked ? `${day(it.locked_until)} gacha yopiq` : "",
      it.open_issues ? `${it.open_issues} ta ochiq xabar` : "",
    ].filter(Boolean).join("\n");
    return (
      <button
        key={it.content_key}
        type="button"
        disabled={locked}
        title={tip}
        onClick={() => choose(it)}
        className={`relative min-w-[4.5rem] rounded-xl border px-2.5 py-1.5 text-left transition ${
          it.my_open
            ? "border-brand-500 bg-brand-50"
            : locked
              ? "border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed"
              : it.my_last
                ? "border-emerald-200 bg-emerald-50/50 hover:border-emerald-300"
                : "border-slate-200 bg-white hover:border-brand-300"
        }`}
      >
        <span className="flex items-center gap-1 text-sm font-bold text-slate-800">
          {locked && <Lock size={12} className="text-slate-400" />}
          {it.variant || "—"}
          {it.open_issues ? (
            <span className="ml-auto inline-flex items-center gap-0.5 text-[10px] font-medium text-amber-700">
              <FlagIcon size={10} /> {it.open_issues}
            </span>
          ) : null}
        </span>
        <span className="block text-[11px] text-slate-500 whitespace-nowrap">
          {it.my_open
            ? "davom etish"
            : locked
              ? `${day(it.locked_until)} gacha`
              : it.my_last
                ? `yechgansiz · ${day(it.my_last.at)}`
                : it.duration
                  ? `${it.duration} daq`
                  : "vaqtsiz"}
        </span>
      </button>
    );
  };

  const bankCard = (b: Bank, muted = false) => (
    <div key={b.bank} className={`border border-slate-200 rounded-xl overflow-hidden ${muted ? "bg-slate-50/60" : "bg-white"}`}>
      <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
        <h2 className={`font-semibold ${muted ? "text-slate-600" : "text-slate-800"}`}>{b.label}</h2>
        {muted && (
          <p className="text-xs text-slate-500 mt-0.5">
            Mock imtihon emas — faqat Reading savollari, band qo'yilmaydi.
          </p>
        )}
      </div>
      <div className="divide-y divide-slate-100">
        {b.sections.map((s) => (
          <div key={s.section} className="px-4 py-3 flex flex-col sm:flex-row sm:items-start gap-2">
            <p className="w-24 shrink-0 text-sm font-medium text-slate-700 pt-1.5">
              {SEC_LABEL[s.section] || s.section}
            </p>
            <div className="flex flex-wrap gap-1.5">{s.items.map(chip)}</div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <FlaskConical size={20} className="text-brand-600" />
          <h1 className="text-xl font-bold text-slate-900">Mock sinab ko'rish</h1>
        </div>
        <p className="text-sm text-slate-500">
          O'quvchilar yechadigan mocklarni o'zingiz yechib ko'ring va savollardagi
          xatolarni examinerga ayting. Natija hech qayerga yozilmaydi — faqat
          o'zingiz ko'rasiz.
          {limited ? " Har variantni 30 kunda bir marta yechish mumkin." : ""}
        </p>
      </div>

      {open && (
        <div className="flex items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3">
          <Play size={18} className="text-brand-600 shrink-0" />
          <p className="text-sm text-slate-700 flex-1 min-w-0">
            Tugallanmagan urinish: <b className="truncate">{open.title}</b>
          </p>
          <Link
            to={`/mock-practice/${open.id}`}
            className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium whitespace-nowrap"
          >
            Davom etish
          </Link>
        </div>
      )}

      {err ? (
        <p className="text-sm text-rose-600">{err}</p>
      ) : !banks ? (
        <p className="text-sm text-slate-400">Yuklanmoqda…</p>
      ) : !banks.length ? (
        <p className="text-sm text-slate-500">Mock testlar hali bazaga yozilmagan.</p>
      ) : (
        <>
          {mocks.map((b) => bankCard(b))}
          {practice.length > 0 && (
            <div className="pt-1 space-y-3">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                Mashq to'plamlari
              </p>
              {practice.map((b) => bankCard(b, true))}
            </div>
          )}
        </>
      )}

      <div className="border border-slate-200 rounded-xl bg-white overflow-x-auto">
        <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
          <h2 className="font-semibold text-slate-800">Mening urinishlarim</h2>
        </div>
        {mine.length === 0 ? (
          <p className="text-sm text-slate-400 px-4 py-6 text-center">Hali urinish yo'q</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-slate-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Test</th>
                <th className="text-left px-3 py-2 font-medium">Sana</th>
                <th className="text-left px-3 py-2 font-medium">Natija</th>
                <th className="text-left px-3 py-2 font-medium">Xabarlar</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {mine.map((a) => {
                const done = a.status !== "in_progress";
                const iss = a.issues || {};
                return (
                  <tr key={a.id} className="border-t border-slate-100">
                    <td className="px-4 py-2.5 text-slate-800">{a.title || a.content_key}</td>
                    <td className="px-3 py-2.5 text-slate-600 whitespace-nowrap">
                      {day(a.submitted_at || a.started_at || a.created_at)}
                    </td>
                    <td className="px-3 py-2.5 text-slate-700 whitespace-nowrap">
                      {done
                        ? resultText({
                            score: a.score, max: a.max ?? a.max_score, band: a.band,
                            cefr: a.cefr ?? (a.cefr_level ? { level: a.cefr_level } : null),
                          })
                        : <span className="text-brand-700">yechilmoqda</span>}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-600 whitespace-nowrap">
                      {iss.open ? <span className="text-amber-700 mr-2">{iss.open} ochiq</span> : null}
                      {iss.fixed ? <span className="text-emerald-700 mr-2">{iss.fixed} tuzatildi</span> : null}
                      {iss.rejected ? <span className="text-slate-500 mr-2">{iss.rejected} rad</span> : null}
                      {iss.duplicate ? <span className="text-slate-500">{iss.duplicate} dublikat</span> : null}
                      {!iss.open && !iss.fixed && !iss.rejected && !iss.duplicate ? "—" : null}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <Link to={`/mock-practice/${a.id}`} className="text-brand-600 hover:underline text-xs font-medium">
                        {done ? "Ko'rish" : "Davom etish"}
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="border border-slate-200 rounded-xl bg-white">
        <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
          <h2 className="font-semibold text-slate-800">Mening xabarlarim</h2>
        </div>
        {issues.length === 0 ? (
          <p className="text-sm text-slate-400 px-4 py-6 text-center">
            Hali xabar yubormagansiz. Test yechayotganda savol yonidagi bayroqchani bosing.
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {issues.map((i) => (
              <li key={i.id} className="px-4 py-3 text-sm">
                <div className="flex items-start gap-2 flex-wrap">
                  <span className="font-medium text-slate-800">
                    {i.content_key}
                    {i.q_n ? ` · ${i.q_n}-savol` : " · butun test"}
                  </span>
                  <span className="text-xs text-slate-500 bg-slate-100 rounded-full px-2 py-0.5">
                    {issueKindLabel(i.kind)}
                  </span>
                  <span className="ml-auto"><IssueStatusBadge status={i.status} /></span>
                </div>
                {i.comment ? <p className="text-slate-600 mt-1 whitespace-pre-line">{i.comment}</p> : null}
                {i.suggested ? (
                  <p className="text-xs text-slate-500 mt-0.5">Taklif: {i.suggested}</p>
                ) : null}
                {i.status !== "open" && (i.resolution_note || i.resolved_by) ? (
                  <p className="text-xs text-slate-500 mt-1 bg-slate-50 rounded-lg px-2 py-1">
                    {i.resolution_note || ""}
                    {i.resolved_by ? ` — ${i.resolved_by}` : ""}
                    {i.resolved_at ? `, ${day(i.resolved_at)}` : ""}
                  </p>
                ) : null}
                <p className="text-[11px] text-slate-400 mt-1">{day(i.created_at)}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {pick && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 flex items-end sm:items-center justify-center"
             onClick={() => !busy && setPick(null)}>
          <div className="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-xl p-5"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start gap-3 mb-3">
              <div className="flex-1 min-w-0">
                <h2 className="font-bold text-slate-900">{pick.title || pick.content_key}</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {pick.q_count ? `${pick.q_count} ta savol · ` : ""}
                  {pick.duration ? `${pick.duration} daqiqa` : "vaqt cheklanmagan"}
                  {pick.has_script ? " · Listening skripti brauzer ovozida o'qiladi" : ""}
                </p>
              </div>
              <button onClick={() => setPick(null)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            {pick.my_last && (
              <p className="text-xs text-slate-600 bg-slate-50 rounded-lg px-3 py-2 mb-3">
                Siz yechgansiz · {day(pick.my_last.at)} · {resultText(pick.my_last)}
              </p>
            )}
            {pick.duration ? (
              <label className="flex items-center gap-2 text-sm text-slate-700 mb-3">
                <input type="checkbox" checked={timed} onChange={(e) => setTimed(e.target.checked)} />
                Vaqt bilan (imtihondagidek, {pick.duration} daqiqa)
              </label>
            ) : null}
            {limited && (
              <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2 mb-3">
                Bu variantni 30 kunda bir marta yechish mumkin. Topshirgach, to'g'ri
                javoblar faqat xato qilgan savollaringizda ko'rinadi.
              </p>
            )}
            {mobile ? (
              <div className="rounded-xl bg-slate-50 px-3 py-4">
                <MobileBlock framed={env.framed && !env.mobile} />
              </div>
            ) : (
              <>
                <div className="space-y-2 mb-3">
                  <StrictRules staff />
                  <ExtensionWarning list={ext.seen} />
                  <ExtensionProbe />
                </div>
                <button
                  type="button"
                  disabled={busy || ext.seen.length > 0}
                  onClick={start}
                  className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold disabled:opacity-60"
                >
                  {busy ? "Boshlanmoqda..." : "Boshlash — to'liq ekranda"}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
