import { StudentIcon } from "../../components/StudentIcon";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Check, RotateCcw, Sparkles, X } from "lucide-react";
import { api } from "../../lib/api";
import { getLang } from "../../lib/lang";
import { autoNextDelay, useAutoNext } from "../../lib/useAutoNext";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — GRAMMAR MASHG'ULOTI (2026-08-10).
 *
 * Uch tur bitta ekranda:
 *   fill  — variant tugmalari;
 *   error — gap ko'rsatiladi, XATO bo'lakni bosish kerak;
 *   order — so'z kartochkalarini bosib jumla yig'ish.
 *
 * To'g'riligini SERVER hal qiladi (/grammar/answer) — to'g'ri javob
 * mijozga oldindan kelmaydi. Har savoldan keyin izoh ko'rsatiladi —
 * bola nafaqat "xato", balki NEGA xatoligini ham ko'radi.
 */
const LEVEL_KEYS = ["a1", "a2", "b1", "b2", "c1", "c2"] as const;

/**
 * mix=true — ARALASH MASHQ (2026-09-25). Jahongir: "grammatikaga
 * aralash mashq qilish funksyiyasini qoshgin shunda aynan qaysi
 * mavzuda koproq xato qilyabdi o'ziga bilinib korinib tursin, chunki
 * bitta mavzuni ishlagan odam javob topishi osonda".
 * Savollar ochiq darajalardagi barcha mavzulardan aralash keladi,
 * mavzu nomi FAQAT javobdan keyin ko'rinadi, oxirida mavzular
 * kesimida natija chiqadi.
 */
export default function StudentGrammarPlay({ mix = false }: { mix?: boolean }) {
  const { topic } = useParams();
  const [items, setItems] = useState<Any[]>([]);
  const [idx, setIdx] = useState(0);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  // Joriy savol holati
  const [picked, setPicked] = useState<string[]>([]); // order uchun
  // MASHQ TURI (2026-08-11, Jahongir): mavzu tanlangach 4 tur
  // taklif qilinadi. null = hali tanlanmagan (tanlash ekrani).
  // Aralash mashqda tur tanlanmaydi — hamma tur aralash.
  const [kind, setKind] = useState<string | null>(mix ? "mix" : null);
  // Mashqlar soni (2026-08-21, Jahongir: "10, 20, 30, 50 tanlaydigan
  // bolsin va koproq mashq qila olsin"). null = hali tanlanmagan.
  const [cnt, setCnt] = useState<number | null>(null);
  const [kinds, setKinds] = useState<string[]>([]);
  // Aralash mashq: qaysi daraja(lar)dan — "all" yoki bitta ochiq daraja
  const [lvl, setLvl] = useState<string | null>(null);
  const [unlocked, setUnlocked] = useState<string[]>([]);
  // Aralash mashq: mavzular kesimida joriy natija
  const [perTopic, setPerTopic] = useState<Record<string, { ok: number; total: number }>>({});
  const [clozeSel, setClozeSel] = useState<Record<number, string>>({});
  const [result, setResult] = useState<Any>(null); // serverdan javob
  const [score, setScore] = useState({ ok: 0, xp: 0 });
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    // Bu mavzuda qaysi turlar borligini bilib olamiz (aralashda —
    // qaysi darajalar ochiqligini)
    api
      .get<Any>(`/student/grammar/topics?language=${getLang()}`)
      .then((r) => {
        if (mix) {
          const avail = new Set(
            ((r?.available || ["A1"]) as string[]).map((x) => x.toLowerCase()),
          );
          const open = LEVEL_KEYS.filter(
            (k) => avail.has(k) && (k === "a1" || !r?.[`${k}_locked`]),
          ).map((k) => k.toUpperCase());
          setUnlocked(open.length ? open : ["A1"]);
          return;
        }
        const all = [
          ...(r?.a1?.topics || []),
          ...(r?.a2?.topics || []),
          ...(r?.b1?.topics || []),
          ...(r?.b2?.topics || []),
          ...(r?.c1?.topics || []),
          ...(r?.c2?.topics || []),
        ];
        const t = all.find((x: Any) => x.topic === topic);
        setKinds(t?.kinds || ["fill", "error", "order"]);
      })
      .catch(() => {
        setKinds(["fill", "error", "order"]);
        setUnlocked(["A1"]);
      });
  }, [topic, mix]);

  const load = useCallback(() => {
    setErr("");
    setItems([]);
    setIdx(0);
    setResult(null);
    setPicked([]);
    setScore({ ok: 0, xp: 0 });
    setPerTopic({});
    setFinished(false);
    if (kind === null || cnt === null) return;
    if (mix && lvl === null) return;
    const url = mix
      ? `/student/grammar/mix?level=${encodeURIComponent(lvl || "all")}&count=${cnt}&language=${getLang()}`
      : `/student/grammar/round?topic=${encodeURIComponent(topic || "")}${
          kind && kind !== "mix" ? `&kind=${kind}` : ""
        }&count=${cnt}&language=${getLang()}`;
    api
      .get<Any>(url)
      .then((r) => setItems(r.items || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [topic, kind, cnt, mix, lvl]);

  useEffect(load, [load]);

  const q = items[idx];

  // Javobdan keyin o'zi keyingi savolga o'tadi (2026-08-18).
  const autoNext = useAutoNext(() => next());

  async function submit(answer: string) {
    if (!q || busy || result) return;
    setBusy(true);
    try {
      const r = await api.post<Any>("/student/grammar/answer", {
        question_id: q.id,
        answer,
        ...(mix ? { mode: "mix" } : {}),
      });
      setResult(r);
      if (r.correct)
        setScore((s) => ({ ok: s.ok + 1, xp: s.xp + (r.xp || 0) }));
      // Aralash mashq: mavzular kesimida hisob (oxirida ko'rsatiladi)
      if (mix) {
        const t = r.topic || q.topic || "—";
        setPerTopic((p) => {
          const cur = p[t] || { ok: 0, total: 0 };
          return {
            ...p,
            [t]: { ok: cur.ok + (r.correct ? 1 : 0), total: cur.total + 1 },
          };
        });
      }
      autoNext.schedule(
        autoNextDelay({
          correct: !!r.correct,
          hasAnswer: !!r.expected,
          hasExtra: !!r.explain,
        }),
      );
    } catch {
      /* toast */
    } finally {
      setBusy(false);
    }
  }

  function next() {
    autoNext.cancel();
    if (idx + 1 >= items.length) {
      setFinished(true);
      return;
    }
    setIdx(idx + 1);
    setResult(null);
    setPicked([]);
    setClozeSel({});
  }

  const remainingWords =
    q?.kind === "order"
      ? (() => {
          const left = [...(q.options || [])];
          for (const w of picked) {
            const i = left.indexOf(w);
            if (i >= 0) left.splice(i, 1);
          }
          return left;
        })()
      : [];

  // 2026-08-21: sarlavha "grammar mashq.png" dizayni bo'yicha - X
  // tugma, JONY STUDENT APP, +XP/+Coin pilllar, N/M progress.
  return (
    <>
      <div className="max-w-md mx-auto px-4 pt-5 text-white">
        <div className="flex items-center gap-2.5">
          <Link to="/student/grammar"
            className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
            style={{ background: "#0c2258", borderColor: "#35538c" }}>
            <X size={18} />
          </Link>
          <p className="text-[13px] font-extrabold tracking-wide flex-1 min-w-0">
            JONY STUDENT APP
          </p>
          <span className="inline-flex items-center gap-1 rounded-xl px-2.5 py-1.5 border text-[12px] font-bold shrink-0"
                style={{ background: "#0c2258", borderColor: "#35538c" }}>
            <StudentIcon name="xp" size={16} /> +9 XP
          </span>
          <span className="inline-flex items-center gap-1 rounded-xl px-2.5 py-1.5 border text-[12px] font-bold text-amber-300 shrink-0"
                style={{ background: "#0c2258", borderColor: "#5c4a15" }}>
            <StudentIcon name="coin" size={16} /> +5 Coin
          </span>
        </div>
        <div className="student-hero student-pattern rounded-2xl p-3 flex items-center gap-2.5 mt-3 mb-1">
          <StudentIcon name="grammar" size={44} />
          {!finished && items.length > 0 ? (
            <>
              <p className="text-[24px] font-extrabold shrink-0">
                {Math.min(idx + 1, items.length)}
                <span className="text-slate-400"> / {items.length}</span>
              </p>
              <div className="flex-1 h-2 rounded-full overflow-hidden"
                   style={{ background: "#26326B" }}>
                <div className="h-full rounded-full transition-all bg-gradient-to-r from-violet-500 to-fuchsia-400"
                     style={{ width: `${((idx + (result ? 1 : 0)) / items.length) * 100}%` }} />
              </div>
            </>
          ) : (
            <p className="text-[19px] font-extrabold truncate">
              {mix ? "Aralash mashq" : topic}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 mt-3 space-y-3 pb-8">
        {err && (
          <div className="student-panel bg-white rounded-xl border border-red-200 p-4">
            <p className="text-sm text-red-600">{err}</p>
            <button onClick={load} className="mt-2 text-sm font-medium text-violet-600">
              Qayta urinish
            </button>
          </div>
        )}

        {/* ---- YAKUN ---- */}
        {finished && (
          <div className="student-panel bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
            <Sparkles size={36} className="mx-auto text-violet-500 mb-2" />
            <p className="text-2xl font-bold text-slate-900">
              {score.ok}/{items.length}
            </p>
            <p className="text-sm text-slate-500 mt-1">
              to'g'ri javob
              {score.xp > 0 && ` · +${score.xp} XP`}
            </p>

            {/* ---- ARALASH MASHQ: MAVZULAR KESIMIDA (2026-09-25) ----
                 Ko'p xato qilingan mavzu tepada — bola aynan qayerda
                 qoqilganini ko'radi va "Takrorlash" bilan o'sha
                 mavzuga o'tadi. */}
            {mix && Object.keys(perTopic).length > 0 && (
              <div className="mt-5 text-left">
                <p className="text-sm font-semibold text-slate-800 mb-2">
                  Mavzular kesimida
                </p>
                <div className="space-y-1.5">
                  {Object.entries(perTopic)
                    .map(([t, v]) => ({
                      topic: t, ok: v.ok, total: v.total,
                      wrong: v.total - v.ok,
                      pct: v.total ? Math.round((v.ok * 100) / v.total) : 0,
                    }))
                    .sort((a, b) => b.wrong - a.wrong || a.pct - b.pct)
                    .map((row) => (
                      <div
                        key={row.topic}
                        className={`rounded-xl border px-3 py-2.5 ${
                          row.wrong > 0
                            ? "border-red-200 bg-red-50"
                            : "border-emerald-200 bg-emerald-50"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <p className="text-[13px] font-semibold text-slate-800 flex-1 min-w-0 truncate">
                            {row.topic}
                          </p>
                          <span
                            className={`text-[12px] font-bold shrink-0 ${
                              row.wrong > 0 ? "text-red-600" : "text-emerald-600"
                            }`}
                          >
                            {row.ok}/{row.total}
                            {row.wrong > 0 && ` · ${row.wrong} xato`}
                          </span>
                          {row.wrong > 0 && (
                            <Link
                              to={`/student/grammar/${encodeURIComponent(row.topic)}`}
                              className="text-[11px] font-bold text-violet-700 bg-white border border-violet-200 rounded-full px-2.5 py-1 shrink-0"
                            >
                              Takrorlash
                            </Link>
                          )}
                        </div>
                        <div className="h-1.5 rounded-full bg-white/70 mt-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              row.wrong > 0 ? "bg-red-400" : "bg-emerald-500"
                            }`}
                            style={{ width: `${row.pct}%` }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 mt-5">
              <button
                onClick={load}
                className="flex-1 py-3 rounded-xl bg-violet-600 text-white text-sm font-semibold flex items-center justify-center gap-2"
              >
                <RotateCcw size={15} />
                Yana mashq
              </button>
              <Link
                to="/student/grammar"
                className="flex-1 py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold flex items-center justify-center"
              >
                Mavzular
              </Link>
            </div>
          </div>
        )}

        {/* ---- ARALASH MASHQ: DARAJANI TANLASH (2026-09-25) ---- */}
        {mix && lvl === null && !err && (
          <div className="student-panel bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-1">
              Aralash mashq
            </p>
            <p className="text-[12px] text-slate-500 mb-3">
              Savollar bir nechta mavzudan aralash keladi, mavzu nomi
              oldindan ko'rsatilmaydi — qaysi mavzuda haqiqatan
              qoqilayotganingiz oxirida bilinadi.
            </p>
            <div className="space-y-1.5">
              <button
                onClick={() => setLvl("all")}
                className="w-full flex items-center gap-3 border border-violet-200 bg-violet-50 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
              >
                <div className="w-9 h-9 rounded-lg bg-violet-600 text-white flex items-center justify-center shrink-0 text-sm font-bold">
                  ∑
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-800">
                    Hammasi
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Ochiq darajalar: {unlocked.join(", ") || "A1"}
                  </p>
                </div>
              </button>
              {unlocked.map((L) => (
                <button
                  key={L}
                  onClick={() => setLvl(L)}
                  className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                >
                  <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center shrink-0 text-sm font-bold">
                    {L}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-800">
                      Faqat {L}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Shu darajaning barcha mavzularidan
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ---- MASHQLAR SONINI TANLASH ---- */}
        {kind !== null && cnt === null && (!mix || lvl !== null) && !err && (
          <div className="student-panel bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Nechta mashq ishlaysiz?
            </p>
            <div className="space-y-1.5">
              {[
                [10, "10 ta", "Tezkor mashq"],
                [20, "20 ta", "O'rtacha mashq"],
                [30, "30 ta", "Yaxshi mashq"],
                [50, "50 ta", "Katta mashq"],
              ].map(([n, lbl, hint]) => (
                <button
                  key={n as number}
                  onClick={() => setCnt(n as number)}
                  className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                >
                  <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center shrink-0 text-sm font-bold">
                    {n as number}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-800">{lbl}</p>
                    <p className="text-[11px] text-slate-400">{hint}</p>
                  </div>
                </button>
              ))}
              <button
                onClick={() => (mix ? setLvl(null) : setKind(null))}
                className="w-full text-center text-xs text-slate-400 pt-2"
              >
                {mix ? "← Darajaga qaytish" : "← Mashq turiga qaytish"}
              </button>
            </div>
          </div>
        )}

        {/* ---- MASHQ TURINI TANLASH ---- */}
        {!mix && kind === null && !err && (
          <div className="student-panel bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Qaysi turdagi mashqni xohlaysiz?
            </p>
            <div className="space-y-1.5">
              {[
                ["mix", "Aralash", "Har xil turdagi mashqlar"],
                ["fill", "Bo'sh joyni to'ldirish", "4 variantdan tanlang"],
                ["order", "Gaplarni tartiblash", "So'zlardan jumla tuzing"],
                ["error", "Xatoni topish", "Gapdagi xato so'zni belgilang"],
                ["cloze", "Kichik matnli test", "Dialog ichida bir nechta bo'sh joy"],
              ]
                .filter(
                  ([k]) => k === "mix" || kinds.includes(k as string),
                )
                .map(([k, lbl, hint]) => (
                  <button
                    key={k}
                    onClick={() => setKind(k as string)}
                    className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                  >
                    <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center shrink-0 text-sm font-bold">
                      {(lbl as string).charAt(0)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-800">
                        {lbl}
                      </p>
                      <p className="text-[11px] text-slate-400">{hint}</p>
                    </div>
                  </button>
                ))}
            </div>
          </div>
        )}

        {/* ---- SAVOL ---- */}
        {!finished && q && (
          <div className="student-panel bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-[11px] font-semibold text-violet-500 uppercase tracking-wide mb-2">
              {q.kind === "fill"
                ? "Bo'sh joyni to'ldiring"
                : q.kind === "error"
                  ? "Xato so'zni toping"
                  : q.kind === "cloze"
                    ? "Matnni to'ldiring"
                    : "So'zlardan jumla tuzing"}
            </p>
            <p className="text-xl font-bold text-slate-900 leading-relaxed mb-4 whitespace-pre-line">
              {q.prompt}
            </p>

            {/* CLOZE: har raqamli bo'sh joy uchun variantlar */}
            {q.kind === "cloze" && (
              <div className="space-y-3 mb-1">
                {(q.options || []).map((grp: string[], bi: number) => (
                  <div key={bi}>
                    <p className="text-[11px] text-slate-500 mb-1">
                      ({bi + 1}) uchun:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {grp.map((o) => (
                        <button
                          key={o}
                          disabled={!!result}
                          onClick={() =>
                            setClozeSel((c) => ({ ...c, [bi]: o }))
                          }
                          className={`px-3 py-2 rounded-lg border text-sm font-medium transition disabled:opacity-60 ${
                            clozeSel[bi] === o
                              ? "bg-violet-600 text-white border-transparent"
                              : "bg-white text-slate-700 border-slate-200"
                          }`}
                        >
                          {o}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                {!result && (
                  <button
                    disabled={
                      busy ||
                      Object.keys(clozeSel).length <
                        (q.options || []).length
                    }
                    onClick={() =>
                      submit(
                        (q.options || [])
                          .map((_: Any, bi: number) => clozeSel[bi] || "")
                          .join("|"),
                      )
                    }
                    className="w-full py-3 rounded-xl bg-violet-600 text-white text-sm font-semibold disabled:opacity-40"
                  >
                    Tekshirish
                  </button>
                )}
              </div>
            )}

            {/* order: yig'ilgan jumla */}
            {q.kind === "order" && (
              <div className="min-h-[52px] border-2 border-dashed border-slate-200 rounded-xl p-2 mb-3 flex flex-wrap gap-1.5">
                {picked.map((w, i) => (
                  <button
                    key={`${w}-${i}`}
                    disabled={!!result}
                    onClick={() =>
                      setPicked((p) => p.filter((_, j) => j !== i))
                    }
                    className="px-2.5 py-1.5 rounded-lg bg-violet-600 text-white text-sm font-medium disabled:opacity-70"
                  >
                    {w}
                  </button>
                ))}
                {picked.length === 0 && (
                  <span className="text-sm text-slate-300 self-center px-1">
                    So'zlarni bosing...
                  </span>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-1.5">
              {q.kind === "cloze" ? null : q.kind === "order"
                ? remainingWords.map((w: string, i: number) => (
                    <button
                      key={`${w}-${i}`}
                      disabled={!!result}
                      onClick={() => setPicked((p) => [...p, w])}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 active:scale-95 transition disabled:opacity-40"
                    >
                      {w}
                    </button>
                  ))
                : (q.options || []).map((o: string) => {
                    const isAns = result && o === result.expected;
                    const isMine = result && o === result._mine;
                    return (
                      <button
                        key={o}
                        disabled={!!result || busy}
                        onClick={() => {
                          q._mine = o;
                          submit(o).then(() =>
                            setResult((r: Any) =>
                              r ? { ...r, _mine: o } : r,
                            ),
                          );
                        }}
                        className={`w-full py-2.5 px-3 rounded-lg border text-sm font-medium text-left transition ${
                          isAns
                            ? "bg-emerald-600 text-white border-transparent"
                            : isMine
                              ? "bg-red-600 text-white border-transparent"
                              : "bg-white text-slate-700 border-slate-200 disabled:opacity-60"
                        }`}
                      >
                        {o}
                      </button>
                    );
                  })}
            </div>

            {q.kind === "order" && !result && (
              <button
                disabled={picked.length === 0 || busy}
                onClick={() => submit(picked.join(" "))}
                className="w-full mt-3 py-3 rounded-xl bg-violet-600 text-white text-sm font-semibold disabled:opacity-40"
              >
                Tekshirish
              </button>
            )}

            {/* ---- Natija + izoh ---- */}
            {result && (
              <div
                className={`mt-3 rounded-xl p-3 ${
                  result.correct ? "bg-emerald-50" : "bg-red-50"
                }`}
              >
                <p
                  className={`text-sm font-semibold flex items-center gap-1.5 ${
                    result.correct ? "text-emerald-700" : "text-red-700"
                  }`}
                >
                  {result.correct ? <Check size={15} /> : <X size={15} />}
                  {result.correct
                    ? result.first_time
                      ? "To'g'ri! +1 XP"
                      : "To'g'ri!"
                    : "Xato"}
                </p>
                {!result.correct && (
                  <p className="text-sm text-slate-700 mt-1">
                    To'g'ri javob: <b>{result.expected}</b>
                  </p>
                )}
                {result.explain && (
                  <p className="text-xs text-slate-500 mt-1">
                    {result.explain}
                  </p>
                )}
                {/* Aralash mashqda mavzu FAQAT javobdan keyin ochiladi */}
                {mix && (result.topic || q.topic) && (
                  <p className="text-xs text-slate-600 mt-1.5">
                    📌 Mavzu: <b>{result.topic || q.topic}</b>
                    {(result.level || q.level) && (
                      <span className="text-slate-400"> · {result.level || q.level}</span>
                    )}
                  </p>
                )}
                <button
                  onClick={next}
                  className="w-full mt-2.5 py-2.5 rounded-lg bg-slate-900 text-white text-sm font-semibold"
                >
                  {idx + 1 >= items.length ? "Yakunlash" : "Keyingisi"}
                  {autoNext.secsLeft > 0 ? ` (${autoNext.secsLeft})` : ""}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
