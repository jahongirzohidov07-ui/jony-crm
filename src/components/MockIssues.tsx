import { useEffect, useState } from "react";
import { AlertTriangle, Wrench } from "lucide-react";
import { api } from "../lib/api";
import { pushToast } from "../lib/toast";
import { ISSUE_STATUS, issueKindLabel } from "./MockIssueDialog";
import type { BankFocus } from "./ExamBank";

/**
 * SAVOL XATOLARI — examinerlar boshlig'ining navbati (2026-09-27).
 *
 * Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib ishlaydigan
 * bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq ustozlarga
 * ular ham experience qilib xatolarni aytadida".
 *
 * Xodimlar mockni yechib "savolda xato bor" degan xabarlar shu yerga
 * SAVOL bo'yicha yig'iladi: nechta odam aytdi, nima dedi, qanday javob
 * taklif qildi, savol xabar berilgan paytda qanday edi va hozir qanday
 * (o'zgargan bo'lsa belgisi), mock nechta daraja nusxasida turibdi va
 * xodimlar urinishlarida qaysi javob ko'p berilgan ("signal").
 *
 * "Shubhali savollar" — hech kim xabar bermagan, lekin 3+ urinishda
 * 60% dan ko'pi bir xil XATO javob bergan savollar (kalit xato bo'lishi
 * mumkin).
 *
 * Tuzatish — Test bazasida shu savolni ochadi (belgilab). Rad etish /
 * Dublikat — izoh bilan yopadi; xabar bergan xodim holatni ko'radi.
 */

type Snap = {
  q?: string | null;
  options?: string[] | null;
  answer?: unknown;
  type?: string | null;
} | null;
type Comment = {
  name?: string | null;
  text?: string | null;
  suggested?: string | null;
  given?: string | null;
  during_test?: number | boolean | null;
  kind?: string | null;
  status?: string | null;
  resolution_note?: string | null;
};
type Signal = {
  n_attempts?: number;
  wrong_pct?: number;
  top_wrong?: string | { value?: string; given?: string; text?: string; n?: number } | null;
  /** Server top_wrong ni matn qilib, sonini alohida beradi */
  top_wrong_n?: number;
  key?: string | null;
} | null;
type Group = {
  content_key: string;
  qid: string | null;
  q_n?: number | null;
  part_title?: string | null;
  skill?: string | null;
  variant?: string | null;
  n?: number;
  kinds?: string[] | Record<string, number>;
  names?: string[];
  comments?: Comment[];
  snapshot?: Snap;
  current?: Snap;
  changed?: boolean;
  copies?: number;
  template_id?: number | null;
  signal?: Signal;
  /** Shubhali savollarda signal maydonlari guruhning o'zida keladi */
  n_attempts?: number;
  wrong_pct?: number;
  top_wrong?: string | null;
  top_wrong_n?: number;
  key?: string | null;
  /** Guruhdagi xabarlar id si (server: issue_ids) */
  issue_ids?: number[];
  ids?: number[];
  id?: number;
  statuses?: Record<string, number>;
  status?: string;
  resolution_note?: string | null;
  resolved_by?: string | null;
};
type Payload = { groups?: Group[]; suspect?: Group[] } | Group[];

const LETTERS = "ABCDEFGH";

function fmtAnswer(s: Snap): string {
  if (!s) return "—";
  const a = s.answer;
  const opts = s.options || [];
  const lab = (i: number) =>
    opts[i] && opts[i] !== LETTERS[i] ? `${LETTERS[i]}) ${opts[i]}` : LETTERS[i] || String(i);
  if (s.type === "choice" && typeof a === "number") return lab(a);
  if (s.type === "multi" && Array.isArray(a)) return a.map((x) => lab(Number(x))).join(", ");
  if (s.type === "essay") return "(insho)";
  if (Array.isArray(a)) return a.join(" / ");
  if (a == null || a === "") return "—";
  return String(a);
}

function signalLine(sg: Signal): string | null {
  if (!sg || !sg.n_attempts) return null;
  const tw = sg.top_wrong;
  const val = tw == null ? null : typeof tw === "string" ? tw : tw.value ?? tw.given ?? tw.text ?? null;
  const cnt = tw && typeof tw === "object" ? tw.n : sg.top_wrong_n || undefined;
  const key = sg.key ? `, kalit '${sg.key}'` : "";
  if (val && cnt != null) return `${cnt}/${sg.n_attempts} xodim '${val}' dedi${key}`;
  const pct = sg.wrong_pct != null ? `${Math.round(sg.wrong_pct)}% xato` : "";
  return [
    `${sg.n_attempts} urinish`,
    pct,
    val ? `ko'p berilgan xato javob '${val}'` : "",
  ].filter(Boolean).join(" · ") + key;
}

function kindList(k: Group["kinds"]): { key: string; n?: number }[] {
  if (!k) return [];
  if (Array.isArray(k)) {
    const m = new Map<string, number>();
    for (const x of k) m.set(x, (m.get(x) || 0) + 1);
    return [...m.entries()].map(([key, n]) => ({ key, n: n > 1 ? n : undefined }));
  }
  return Object.entries(k).map(([key, n]) => ({ key, n: n > 1 ? n : undefined }));
}

function SnapView({ s, label, tone }: { s: Snap; label: string; tone: string }) {
  if (!s) return null;
  return (
    <div className={`rounded-lg border px-3 py-2 text-xs ${tone}`}>
      <p className="font-semibold text-slate-500 uppercase text-[10px] mb-1">{label}</p>
      {s.q ? <p className="text-slate-800 whitespace-pre-line">{s.q}</p> : null}
      {s.options?.length ? (
        <ul className="mt-1 space-y-0.5">
          {s.options.map((o, i) => (
            <li key={i} className="text-slate-600">
              <b className="mr-1">{LETTERS[i]}</b>
              {o !== LETTERS[i] ? o : ""}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="mt-1">
        <span className="text-slate-500">Kalit: </span>
        <span className="font-medium text-emerald-700">{fmtAnswer(s)}</span>
      </p>
    </div>
  );
}

export function MockIssues({
  canTriage,
  onFix,
  onChanged,
}: {
  canTriage: boolean;
  onFix: (f: BankFocus) => void;
  onChanged?: () => void;
}) {
  const [status, setStatus] = useState("open");
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [suspect, setSuspect] = useState<Group[]>([]);
  const [acting, setActing] = useState<{ key: string; status: string } | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    setGroups(null);
    api
      .fresh<Payload>(`/mock-issues?status=${status}`)
      .then((r) => {
        if (Array.isArray(r)) {
          setGroups(r);
          setSuspect([]);
        } else {
          setGroups(r.groups || []);
          setSuspect(r.suspect || []);
        }
      })
      .catch(() => setGroups([]));
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [status]);

  const gkey = (g: Group) => `${g.content_key}|${g.qid ?? ""}`;
  const idsOf = (g: Group) =>
    g.issue_ids?.length ? g.issue_ids : g.ids?.length ? g.ids : g.id ? [g.id] : [];
  // Guruh holati: server har holat sonini beradi (statuses) — hammasi
  // bitta holatda bo'lsa o'sha, aks holda filtr holati.
  const statusOf = (g: Group): string | undefined => {
    if (g.status) return g.status;
    const st = Object.keys(g.statuses || {});
    return st.length === 1 ? st[0] : undefined;
  };

  async function close(g: Group, st: string) {
    const ids = idsOf(g);
    if (!ids.length) return;
    setBusy(true);
    try {
      await api.put(`/mock-issues/${ids[0]}`, { status: st, note: note.trim() || null });
      pushToast(st === "rejected" ? "Rad etildi" : "Dublikat deb yopildi", "success");
      setActing(null);
      setNote("");
      load();
      onChanged?.();
    } catch {
      /* xato toast bilan chiqadi */
    } finally {
      setBusy(false);
    }
  }

  function fix(g: Group) {
    if (!g.template_id) {
      pushToast("Bu test bazada topilmadi (o'chirilgan bo'lishi mumkin)");
      return;
    }
    onFix({
      tid: g.template_id,
      qid: g.qid,
      issueIds: idsOf(g),
      notes: (g.comments || []).map((c) => ({
        name: c.name || null,
        text: c.text || null,
        suggested: c.suggested || null,
        given: c.given || null,
      })),
    });
  }

  const card = (g: Group, isSuspect = false) => {
    const k = gkey(g);
    const names = g.names?.length
      ? g.names
      : Array.from(new Set((g.comments || []).map((c) => c.name).filter(Boolean))) as string[];
    // Shubhali savolda signal maydonlari guruhning o'zida keladi
    const sig = signalLine(g.signal || (isSuspect ? {
      n_attempts: g.n_attempts, wrong_pct: g.wrong_pct, top_wrong: g.top_wrong,
      top_wrong_n: g.top_wrong_n, key: g.key,
    } : null));
    const gStatus = statusOf(g);
    const open = !isSuspect && (gStatus ? gStatus === "open" : status === "open");
    const lastClosed = [...(g.comments || [])].reverse().find((c) => c.status && c.status !== "open");
    const resNote = g.resolution_note ?? lastClosed?.resolution_note ?? null;
    return (
      <div key={(isSuspect ? "s:" : "") + k} className={`border rounded-xl bg-white p-4 ${isSuspect ? "border-amber-200" : "border-slate-200"}`}>
        <div className="flex items-start gap-2 flex-wrap">
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-slate-900">
              {g.content_key}
              <span className="text-slate-500 font-normal">
                {g.qid ? ` · ${g.q_n ?? "?"}-savol` : " · butun test"}
                {g.part_title ? ` · ${g.part_title}` : ""}
              </span>
            </p>
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              {!isSuspect && (
                <span className="text-[11px] font-medium bg-rose-50 text-rose-700 rounded-full px-2 py-0.5">
                  {g.n ?? names.length} kishi
                </span>
              )}
              {kindList(g.kinds).map((x) => (
                <span key={x.key} className="text-[11px] bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                  {issueKindLabel(x.key)}{x.n ? ` ×${x.n}` : ""}
                </span>
              ))}
              {g.copies && g.copies > 1 ? (
                <span className="text-[11px] bg-sky-50 text-sky-700 rounded-full px-2 py-0.5"
                      title="Shu mock nechta daraja nusxasida turibdi">
                  {g.copies} nusxa
                </span>
              ) : null}
              {g.changed ? (
                <span className="text-[11px] bg-violet-50 text-violet-700 rounded-full px-2 py-0.5"
                      title="Xabar berilgandan keyin savol tahrirlangan">
                  o'zgargan
                </span>
              ) : null}
              {!isSuspect && gStatus && gStatus !== "open" && ISSUE_STATUS[gStatus] ? (
                <span className={`text-[11px] rounded-full px-2 py-0.5 ${ISSUE_STATUS[gStatus].cls}`}>
                  {ISSUE_STATUS[gStatus].label}
                </span>
              ) : null}
            </div>
          </div>
          {canTriage && (open || isSuspect) && (
            <div className="flex gap-1.5 shrink-0">
              <button
                type="button"
                onClick={() => fix(g)}
                className="inline-flex items-center gap-1 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 text-xs font-medium"
              >
                <Wrench size={13} /> Tuzatish
              </button>
              {!isSuspect && (
                <>
                  <button
                    type="button"
                    onClick={() => { setActing({ key: k, status: "rejected" }); setNote(""); }}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
                  >
                    Rad etish
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActing({ key: k, status: "duplicate" }); setNote(""); }}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
                  >
                    Dublikat
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {acting?.key === k && (
          <div className="mt-3 flex items-center gap-2 bg-slate-50 rounded-lg p-2">
            <input
              autoFocus
              className="flex-1 rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm"
              placeholder={acting.status === "rejected"
                ? "Nega rad etildi (xodimga ko'rinadi)"
                : "Qaysi xabarning dublikati"}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <button
              type="button"
              disabled={busy}
              onClick={() => close(g, acting.status)}
              className="rounded-lg bg-slate-800 text-white px-3 py-1.5 text-xs font-medium disabled:opacity-60"
            >
              {acting.status === "rejected" ? "Rad etish" : "Dublikat"}
            </button>
            <button type="button" onClick={() => setActing(null)} className="text-xs text-slate-500 px-1">
              Bekor
            </button>
          </div>
        )}

        {names.length > 0 && (
          <p className="text-xs text-slate-500 mt-2">Xabar berganlar: {names.join(", ")}</p>
        )}
        {(g.comments || []).length > 0 && (
          <ul className="mt-2 space-y-1.5">
            {(g.comments || []).map((c, i) => (
              <li key={i} className="text-sm bg-slate-50 rounded-lg px-3 py-2">
                <span className="font-medium text-slate-700">{c.name || "—"}</span>
                {c.during_test ? (
                  <span className="ml-1.5 text-[10px] text-slate-400">test paytida</span>
                ) : null}
                {c.text ? <p className="text-slate-600 whitespace-pre-line">{c.text}</p> : null}
                <p className="text-xs text-slate-500">
                  {c.given ? <>O'z javobi: <b className="text-slate-700">{c.given}</b></> : null}
                  {c.given && c.suggested ? " · " : null}
                  {c.suggested ? <>Taklif: <b className="text-emerald-700">{c.suggested}</b></> : null}
                </p>
              </li>
            ))}
          </ul>
        )}

        {sig && (
          <p className="text-xs text-amber-800 bg-amber-50 rounded-lg px-3 py-1.5 mt-2">{sig}</p>
        )}

        {(g.snapshot || g.current) && (
          <div className={`grid gap-2 mt-2 ${g.snapshot && g.current && g.changed ? "sm:grid-cols-2" : ""}`}>
            {g.changed && g.snapshot ? (
              <SnapView s={g.snapshot} label="Xabar berilgan paytda" tone="border-slate-200 bg-slate-50" />
            ) : null}
            <SnapView s={g.current || g.snapshot || null} label="Hozir bazada"
                      tone="border-slate-200 bg-white" />
          </div>
        )}

        {!open && !isSuspect && (resNote || g.resolved_by) ? (
          <p className="text-xs text-slate-500 mt-2">
            {resNote || ""}{g.resolved_by ? ` — ${g.resolved_by}` : ""}
          </p>
        ) : null}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
        Xodimlar mockni o'zi yechib ko'rganda "savolda xato bor" deb yuborgan
        xabarlar — savol bo'yicha yig'ilgan. <b>Tuzatish</b> Test bazasida shu
        savolni ochadi; saqlanganda xabar o'zi "tuzatildi" bo'ladi va xodim buni
        ko'radi.
      </p>
      <div className="flex gap-1.5 flex-wrap">
        {Object.entries(ISSUE_STATUS).map(([k, v]) => (
          <button
            key={k}
            type="button"
            onClick={() => setStatus(k)}
            className={`rounded-full border px-3 py-1 text-xs font-medium ${
              status === k
                ? "border-brand-500 bg-brand-50 text-brand-800"
                : "border-slate-200 text-slate-600 hover:border-slate-300"
            }`}
          >
            {k === "open" ? "Ochiq" : v.label}
          </button>
        ))}
      </div>

      {groups === null ? (
        <p className="text-sm text-slate-400">Yuklanmoqda…</p>
      ) : groups.length === 0 ? (
        <p className="text-sm text-slate-400 py-6 text-center">
          {status === "open" ? "Ochiq xabar yo'q" : "Bu holatda xabar yo'q"}
        </p>
      ) : (
        <div className="space-y-3">{groups.map((g) => card(g))}</div>
      )}

      {status === "open" && suspect.length > 0 && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-600" />
            <h3 className="font-semibold text-slate-800">Shubhali savollar</h3>
          </div>
          <p className="text-xs text-slate-500">
            Hech kim xabar bermagan, lekin xodimlar urinishlarida ko'pchilik bir xil
            xato javob bergan — kalitni tekshirib ko'ring.
          </p>
          {suspect.map((g) => card(g, true))}
        </div>
      )}
    </div>
  );
}
